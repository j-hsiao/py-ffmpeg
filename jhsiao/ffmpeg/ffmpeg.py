"""Basic ffmpeg processes."""
import io
from collections import deque
import subprocess as sp
import sys

import numpy as np

from jhsiao.ioutils.seqwriter import SeqWriter
from jhsiao.ioutils.forwarder import Forwarder, Wrapper
from jhsiao.ioutils.fdwrap import FDWrap

from .info import PixFmts
from .its import RewindIt
from .eparse import FFmpegEParser
from .retrieve import FrameRetriever


class FFmpegProc(object):
    """A ffmpeg process."""
    def __init__(self, command, istream=None, ostream=None, verbose=False):
        """Initialize an FFmpeg process.

        command: list of str
            The ffmpeg command.  stderr is parsed for stream info so
            -loglevel should not be too low.  If outputs exist, ffmpeg
            will prompt for y/n to overwrite.  However, there is no way
            to pass the response so ffmpeg will fail.  Add -y to the
            command to overwrite existing output files.
        istream: None or file-like object.
            The object to use as ffmpeg stdin.
        ostream: None or file-like object.
            The object to use as ffmpeg stdout.
        verbose: bool
            Print lines when parsing stderr
        """
        if istream is None:
            istream = sp.PIPE
        self.istream = istream
        self.ostream = ostream
        self.proc = sp.Popen(
            command, stdin=istream,
            stdout=ostream, stderr=sp.PIPE)
        if sys.version_info.major > 2:
            stderr = io.TextIOWrapper(self.proc.stderr)
        else:
            stderr = self.proc.stderr
        self.proc.stderr = None

        #unblock stdout while trying to parse stderr
        if self.proc.stdout is not None:
            stdof = Forwarder(
                self.proc.stdout, io.BytesIO(), False, False)
        it = RewindIt(stderr)
        self.streaminfo = FFmpegEParser(it, verbose)
        if self.proc.stdout is not None:
            stdof.stop()
            stdof.join()
            self.pre = stdof.streams[1]
            self.pre.seek(0)
            self._readinto = self._readinto_pre
        else:
            self._readinto = None
        self.eforward = Forwarder(
            stderr, SeqWriter(deque(it.history, maxlen=5)), True, False)

    def _readinto_pre(self, buf):
        amt = self.pre.readinto(buf)
        if amt < len(buf):
            ret = amt + self.proc.stdout.readinto(memoryview(buf)[amt:])
            self._readinto = self.proc.stdout.readinto
            return ret
        else:
            return amt

    def close(self):
        """Close proc and stop stderr forwarding.

        Note that this does not close the given istream/ostream.
        Note that if istream was given, this will wait until eof on the
        istream end.  This means it may hang if the istream is never
        closed or has no eof.
        """
        if self.proc is None:
            return
        if self.proc.stdin is not None:
            self.proc.communicate(b'qqqq')
        else:
            self.proc.communicate()
        self.eforward.stop()
        self.eforward = None
        self.proc = None

    release = close

    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()
    def __del__(self):
        self.close()


class FFmpegReader(FFmpegProc):
    """Read from a ffmpeg process."""
    def __init__(self, commandline, istream=None, wrap=True, verbose=False):
        """Initialize.

        commandline: list of str: ffmpeg commandline.
            This should output to pipe.
        istream: file-like object or None
            If given, this will be used as ffmpeg stdin.
            Usually the commandline will read from pipe in this case.
        wrap: bool
            Wrap istream with an fd.  This defaults to True which is
            the safe choice.  istream may be buffered and unseekable
            in which case data may have been consumed from the fd.
            Directly passing the fd may result in errors.  If you are
            sure that the istream position is correct, you can set
            this to False to improve performance.  Note however, that
            setting wrap to False also means that the resulting process
            will open that file descriptor directly.  There is no way
            for the current process to close it and end the ffmpeg
            process prematurely.
        verbose: bool
            Verbose ffmpeg stderr parsing.
        """
        if istream is not None and wrap:
            with FDWrap(istream, 'rb') as f:
                super(FFmpegReader, self).__init__(
                    commandline, f, sp.PIPE, verbose)
            self._terminate = False
        else:
            self._terminate = True
            super(FFmpegReader, self).__init__(
                commandline, istream, sp.PIPE, verbose)
        candidate = None
        for o in self.streaminfo.outs.values():
            if not o.is_pipe():
                continue
            for name, stream in o.items():
                if stream.type == 'Video':
                    if candidate is None:
                        candidate = stream
                    else:
                        raise ValueError('Expect only 1 output video stream to pipe')
        if candidate is None:
            raise ValueError('No pipe output to read from.')
        if candidate.codec != 'rawvideo':
            raise ValueError('Only rawvideo codec is supported.')
        self.fps = candidate.fps
        self.width = candidate.width
        self.height = candidate.height
        self.codec = candidate.codec
        try:
            self.pix_fmt = PixFmts()[candidate.pix_fmt]
            self.retriever = FrameRetriever(
                self.pix_fmt, self.width, self.height)
            self.retrieve = self.retriever.cvt
            self.rawbuf = self.retriever.rawbuf
        except Exception:
            self.close()
            raise

    def grab(self):
        """Read frame data into buffer."""
        amt = self._readinto(self.rawbuf.ravel())
        return amt == self.rawbuf.nbytes

    def retrieve(self, out=None):
        """Parse the grabbed data into a BGR frame."""
        return self.retrieve(out)

    def read(self, out=None):
        """Read a frame. grab() and retrieve().
        """
        if self.grab():
            return self.retrieve(out)
        return False, None

    def close(self):
        """Close the process.

        Terminate process as well if istream was a file-like object
        and not wrapped.
        """
        if self.istream != sp.PIPE:
            self.istream.close()
            if self._terminate:
                self.proc.terminate()
        super(FFmpegReader, self).close()


class FFmpegWriter(FFmpegProc):
    """Write frames to an ffmpeg process."""
    def __init__(self, commandline, ostream=None, wrap=True, verbose=False):
        """Initialize.

        commandline: list of str
            The ffmpeg commandline to run.
        ostream: None or file-like object
            The subprocess output will be written to this object.
            If wrap is False, then `ostream.fileno()` must return a
            valid file number to be used in `subprocess.Popen`.
        wrap: bool
            Wrap the ostream with FDWrap to allow writing to ostream
            even if it is not a real file.
        verbose: bool
            stderr parsing verbosity.
        """
        if ostream is not None and wrap:
            with FDWrap(ostream, 'wb') as f:
                super(FFmpegWriter, self).__init__(
                    commandline, sp.PIPE, f, verbose)
        else:
            super(FFmpegWriter, self).__init__(
                commandline, sp.PIPE, ostream, verbose)

    def write(self, frame):
        self.proc.stdin.write(frame)

class FFmpegDelayedWriter(object):
    """Delay the actual process creation until first frame.

    This does not require knowledge of frame shape until first write.
    """
    pass

















#from collections import deque
#import os
#import shlex
#import subprocess as sp
#import io
#import sys
#
#import numpy as np
#
#from .fmts import FormatInfo
#from .eparse import FFmpegStderrParser
#from ..utils.forwarder import Forwarder
#from ..utils.devnull import DevNull
#from ..utils.fio import SeqWriter
#from .retrieve import Retriever
#
#class Fstream(object):
#    """Wrap a file-like object with pipes and threaded forwarder.
#
#    For example, io.BytesIO can normally not be used as input/output to
#    subprocess but this adds some indirection which allows it.
#    """
#    def __init__(self, fobj, out=True):
#        """Initialize fobj.
#
#        fobj: file object to wrap.
#        out: fobj is an output, otherwise use fobj as input
#        """
#        self.fobj = fobj
#        self.fds = r, w = os.pipe()
#        if out:
#            self.forwarder = Forwarder(os.fdopen(r, 'rb'), fobj).start()
#            self.fd = w
#        else:
#            self.forwarder = Forwarder(fobj, os.fdopen(w, 'wb')).start()
#            self.fd = r
#
#    def finalize(self):
#        """Close unused end so subprocess can see eof."""
#        try:
#            os.close(self.fd)
#        except OSError:
#            pass
#        self.fd = None
#
#    def fileno(self):
#        return self.fd
#
#    def join(self):
#        """Wait for forwarder to finish."""
#        self.forwarder.join()
#
#    def close(self):
#        """Close fobj."""
#        if self.forwarder is not None:
#            self.forwarder.close(True, True)
#            self.forwarder = None
#
#    def detach(self):
#        """Detach fobj."""
#        if self.forwarder is not None:
#            if self.fd == self.fds[0]:
#                self.forwarder.close(False, True)
#            else:
#                self.forwarder.close(True, False)
#            ret = self.fobj
#            self.fobj = None
#            return ret
#
#class FFmpeg(object):
#    """Generalized ffmpeg command."""
#    def __init__(self, commandline, istream=None, ostream=None, verbose=False):
#        """Initialize FFmpeg subprocess.
#
#        commandline: The commandline to use.  Note that because stderr
#            is parsed for stream info, commandline should not have
#            -loglevel too low.  Be aware, if output exists, ffmpeg will
#            prompt for y/n.  There is currently no mechanism to respond
#            to this prompt, so use -y in the commandline if this may
#            be the case.
#        istream/ostream: An object usable as Popen's stdin/stdout
#            argument (has a fileno() method).
#
#            NOTE: if istream/ostream is buffered, tell() and the actual
#                position might be different.  Use os.lseek to ensure
#                its position.  Also, children may affect the stream
#                use lseek afterwards to ensure consistent position.
#                Alternatively, Fstream can work too
#        verbose:
#            if verbose, then stderr will be forwarded to sys.stderr
#        """
#        ensure_formatinfo = FormatInfo('-pix_fmts').formats, FormatInfo('-formats').formats
#        if isinstance(commandline, str):
#            commandline = shlex.split(commandline)
#        # stdin cannot be None because then ffmpeg will eat
#        # normal stdin
#        stdin = sp.PIPE if istream is None else istream
#        self.proc = sp.Popen(
#            commandline, stdin=stdin, stdout=ostream, stderr=sp.PIPE)
#        self.istream = istream if hasattr(istream, 'read') else None
#        self.ostream = ostream if hasattr(ostream, 'write') else None
#        self.eforward = None
#        self.pre = None
#        try:
#            try:
#                wrapped = io.TextIOWrapper(self.proc.stderr)
#            except Exception:
#                wrapped = self.proc.stderr
#            if self.proc.stdout is not None:
#                self.pre = io.BytesIO()
#                f = Forwarder(self.proc.stdout, self.pre).start()
#            try:
#                self.einfo = FFmpegStderrParser(wrapped, verbose)
#            except Exception:
#                if isinstance(wrapped, io.TextIOWrapper):
#                    wrapped.detach()
#                raise
#            finally:
#                if self.proc.stdout is not None:
#                    f.close(False, False)
#                    self.pre.seek(0)
#            self.proc.stderr = None
#            if verbose:
#                self.eforward = Forwarder(wrapped, sys.stderr, linebuf=True).start()
#            else:
#                # It seems that if stderr is closed while ffmpeg is still running
#                # ffmpeg just stops writing to stderr? doesn't crash or block?
#                self.eforward = Forwarder(
#                    wrapped, SeqWriter(deque(maxlen=10)), linebuf=True).start()
#        except Exception:
#            self.proc.communicate(None if self.proc.stdin is None else b'q')
#            raise
#
#    def close(self, i=True, o=True, now=True):
#        """Close the subprocess.
#
#        i,o: close the input/output streams if given and applicable
#        now: if True, communicate b'q' if applicable else None.
#            This will cause ffmpeg to close now if it is reading
#            from stdin.  If not now, then it'll wait until ffmpeg closes
#            on its own.
#        """
#        if self.proc.returncode is None:
#            if now and self.proc.stdin is not None:
#                msg = b'q'
#            else:
#                msg = None
#            self.proc.communicate(msg)
#            if self.eforward is not None:
#                self.eforward.close(True, False)
#                self.eforward = None
#            if i and self.istream is not None:
#                try:
#                    self.istream.close()
#                except Exception:
#                    pass
#                self.istream = None
#            if o and self.ostream is not None:
#                try:
#                    self.ostream.close()
#                except Exception:
#                    pass
#                self.ostream = None
#    def release(self):
#        """Mimic opencv interface."""
#        self.close()
#
#    def __enter__(self):
#        return self
#    def __exit__(self, *args):
#        self.close()
#    def __del__(self):
#        self.close()
#
#
#class FFmpegReader(FFmpeg):
#    """Read video.
#
#    commandline should output to pipe with rawvideo format
#    Try to return the corresponding pixfmt specified by the commandline.
#    Failure if unsupported pixel format.
#    Expect 1 output video stream to pipe:
#    """
#    def __init__(
#        self, commandline, istream=None, verbose=False, closeerr=True):
#        """Same args as FFmpeg.
#
#        ostream is sp.PIPE.
#        """
#        super(FFmpegReader, self).__init__(
#            commandline, istream, sp.PIPE, verbose)
#        readcandidates = [
#            out for out in self.einfo.outs
#            if out.name == 'pipe:' and out.format == 'rawvideo']
#        if len(readcandidates) > 1:
#            self.close()
#            raise Exception(
#                'Ambiguous output candidates, expect 1, got: {}'.format(
#                    [out.name for out in readcandidates]))
#        elif len(readcandidates) == 0:
#            self.close()
#            raise Exception('No outputs for reading.')
#        out = readcandidates[0]
#        streamcandidates = [
#            stream for stream in out.streams.values()
#            if stream.type == 'Video']
#        if len(streamcandidates) > 1:
#            self.close()
#            raise Exception(
#                'Ambiguous video stream candidates, expect 1, got: {}'.format(
#                    [stream.name for stream in streamcandidates]))
#        elif len(streamcandidates) == 0:
#            self.close()
#            raise Exception('No streams in output.')
#        self.stream = streamcandidates[0]
#        self.shape = self.stream.shape
#        try:
#            buf, dbuf = self.stream.framebuf()
#        except Exception:
#            self.close()
#            raise
#        self.buf = buf
#        self.dbuf = dbuf = buf if dbuf is None else dbuf
#        retrievefunc = Retriever(self.stream.pix_fmt).retrieve
#        pre = [self.pre]
#        readinto = self.proc.stdout.readinto
#        nbytes = buf.nbytes
#        def grab(buff=None):
#            """Grab data for a single frame.  Return True if success.
#
#            buff: for internal use.
#            """
#            if buff is None:
#                buff = buf
#            if pre:
#                amt = pre[0].readinto(buff)
#                if amt != nbytes:
#                    del pre[:]
#                    return readinto(buff.ravel()[amt:])+amt == nbytes
#                else:
#                    return True
#            else:
#                return readinto(buff) == nbytes
#        if retrievefunc is None:
#            def retrieve(frame=None):
#                if frame is None:
#                    return True, buf.copy()
#                else:
#                    try:
#                        frame[...] = buf
#                    except ValueError:
#                        return True, buf.copy()
#                    else:
#                        return True, frame
#            def read(frame=None):
#                if frame is None or frame.nbytes != buf.nbytes:
#                    frame = np.empty(buf.shape, buf.dtype)
#                return grab(frame), frame
#        else:
#            width, height = self.shape
#            def retrieve(frame=None):
#                try:
#                    return True, retrievefunc(dbuf, frame)[:height, :width]
#                except Exception:
#                    return False, None
#            def read(frame=None):
#                if grab():
#                    try:
#                        return True, retrievefunc(dbuf, frame)[:height, :width]
#                    except Exception:
#                        pass
#                return False, None
#        self.grab = grab
#        self.read = read
#        self.retrieve = retrieve
#
#    def grab(self):
#        """Grab data for a single frame."""
#        pass
#
#    def retrieve(self, data):
#        """Parse data into an image."""
#        pass
#
#    def read(self, frame=None):
#        if self.grab():
#            return self.retrieve(frame)
#
#    def close(self, i=True, now=True):
#        super(FFmpegReader, self).close(i, True, now)
#
#class FFmpegWriter(FFmpeg):
#    """Write video.
#
#    commandline should read from pipe in raw video format.
#    Writing video specifies framesize so no stderr parsing is necessary.
#    In fact, in testing, stderr is only available for parsing after
#    writing a certain amount of data to ffmpeg so it's impossible to
#    parse stderr to check the first input data anyways.
#    """
#    def __init__(self, commandline, ostream=None, verbose=False):
#        """Expect commandline to read from pipe:
#
#        Data provided to write() should match the input format/pix_fmt etc
#        of the commandline.  ostream should be provided if commandline
#        indicates output to stdout.
#        """
#        if verbose:
#            self.proc = sp.Popen(commandline, stdin=sp.PIPE, stdout=ostream)
#            self._err = None
#        else:
#            self.proc = sp.Popen(
#                commandline, stdin=sp.PIPE, stdout=ostream, stderr=sp.PIPE)
#            self._err = Forwarder(
#                self.proc.stderr, SeqWriter(deque(maxlen=10)), linebuf=True).start()
#        self.ostream = ostream if hasattr(ostream, 'close') else None
#
#    def write(self, frame):
#        """Write a frame of data to ffmpeg."""
#        # contiguous array seems to write faster
#        self.proc.stdin.write(np.ascontiguousarray(frame))
#
#    def error(self):
#        """Return any error info."""
#        if self._err is None:
#            # opened in verbose mode, all info is on stderr
#            return None
#        return b''.join(self._err.orig[1].data)
#
#    def __enter__(self):
#        return self
#    def __exit__(self, *args):
#        self.close()
#    def close(self, o=True):
#        ret = None
#        if self.proc.returncode is None:
#            try:
#                self.proc.stdin.close()
#            except OSError:
#                pass
#            self.proc.wait()
#            if o and self.ostream is not None:
#                try:
#                    self.ostream.close()
#                except Exception:
#                    pass
#                self.ostream = None
#            if self._err is not None and self.proc.returncode:
#                self._err.close(True, False)
#                ret = b''.join(self._err.orig[1].data).decode()
#                self._err.orig[1].close()
#                self._err = None
#            elif self._err is not None:
#                self._err.close()
#                self._err = None
#        return ret
#
#
#if __name__ == '__main__':
#    import argparse
#    p = argparse.ArgumentParser()
#    p.add_argument('-c', '--command', nargs='...', help='ffmpeg commandline')
#    p.add_argument('-r', '--reader', nargs='...', help='ffmpeg reading commandline')
#    p.add_argument('-w', '--writer', nargs='...', help='ffmpeg writing commandline')
#    p.add_argument('-v', '--verbose', action='store_true', help='verbose stderr')
#    args = p.parse_args()
#
#    if args.command is not None:
#        ff = FFmpeg(args.command, verbose=args.verbose)
#        print('\n\ninstantiated ff!\n\n')
#        print('number of inputs', len(ff.einfo.ins))
#        for stream in ff.einfo.istreams.values():
#            print(' ', stream.name, stream.type)
#            if stream.type == 'Video':
#                print('    fps', stream.fps)
#                print('    pixfmt', stream.pix_fmt)
#                print('    shape', stream.shape)
#                print('    bytes/frame', stream.bytes_per_frame())
#        print('number of outputs', len(ff.einfo.outs))
#        for stream in ff.einfo.ostreams.values():
#            print(' ', stream.name, stream.type)
#            if stream.type == 'Video':
#                print('    fps', stream.fps)
#                print('    pixfmt', stream.pix_fmt)
#                print('    shape', stream.shape)
#                print('    bytes/frame', stream.bytes_per_frame())
#        ff.close()
#    elif args.reader is not None:
#        import cv2
#        reader = FFmpegReader(args.reader, verbose=args.verbose)
#        print('created reader')
#        try:
#            success, thing = reader.read()
#            fps = reader.stream.fps
#            while success:
#                if reader.stream.pix_fmt == 'yuv420p':
#                    thing = cv2.cvtColor(thing, cv2.COLOR_YUV2BGR_I420)
#                cv2.imshow('thing', thing)
#                success, thing = reader.read()
#                success = success and cv2.waitKey(1) != ord('q')
#            reader.close()
#
#            # cap = cv2.VideoCapture(0)
#            # success, thing = cap.read()
#            # while success:
#                # cv2.imshow('thing', thing)
#                # success, thing = cap.read()
#                # success = success and cv2.waitKey(1) != ord('q')
#            # cap.release()
#        finally:
#            reader.close()
#    elif args.writer is not None:
#        command = args.writer
#        width, height = map(
#            int, args.writer[args.writer.index('-s')+1].split('x'))
#        framebuf = np.zeros((height, width, 3), np.uint8)
#        writer = FFmpegWriter(args.writer, verbose=args.verbose)
#        for i in range(width):
#            print(i, end='\r')
#            framebuf[:,i] = np.random.randint(0, 256, (height,3), np.uint8)
#            writer.write(framebuf)
#            framebuf[:,i] = 0
#        print('done')
#        writer.close()
#        print('closed')
