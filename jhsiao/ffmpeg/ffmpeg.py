"""Basic ffmpeg processes."""

from collections import deque
import os
import shlex
import subprocess as sp
import io
import sys

import numpy as np

from .fmts import FormatInfo
from .eparse import FFmpegStderrParser
from ..utils.forwarder import Forwarder
from ..utils.devnull import DevNull
from ..utils.fio import SeqWriter

class Fstream(object):
    """Wrap a file-like object with pipes and threaded forwarder.

    For example, io.BytesIO can normally not be used as input/output to
    subprocess but this adds some indirection which allows it.
    """
    def __init__(self, fobj, out=True):
        """Initialize fobj.

        fobj: file object to wrap.
        out: fobj is an output, otherwise use fobj as input
        """
        self.fobj = fobj
        self.fds = r, w = os.pipe()
        if out:
            self.forwarder = Forwarder(os.fdopen(r, 'rb'), fobj).start()
            self.fd = w
        else:
            self.forwarder = Forwarder(fobj, os.fdopen(w, 'wb')).start()
            self.fd = r

    def finalize(self):
        """Close unused end so subprocess can see eof."""
        try:
            os.close(self.fd)
        except OSError:
            pass
        self.fd = None

    def fileno(self):
        return self.fd

    def join(self):
        """Wait for forwarder to finish."""
        self.forwarder.join()

    def close(self):
        """Close fobj."""
        if self.forwarder is not None:
            self.forwarder.close(True, True)
            self.forwarder = None

    def detach(self):
        """Detach fobj."""
        if self.forwarder is not None:
            if self.fd == self.fds[0]:
                self.forwarder.close(False, True)
            else:
                self.forwarder.close(True, False)
            ret = self.fobj
            self.fobj = None
            return ret

class FFmpeg(object):
    """Generalized ffmpeg command."""
    def __init__(self, commandline, istream=None, ostream=None, verbose=False, closeerr=True):
        """Initialize FFmpeg subprocess.

        commandline: The commandline to use.  Note that because stderr
            is parsed for stream info, commandline should not have
            -loglevel too low.  Be aware, if output exists, ffmpeg will
            prompt for y/n.  There is currently no mechanism to respond
            to this prompt, so use -y in the commandline if this may
            be the case.
        istream/ostream: An object usable as Popen's stdin/stdout
            argument (has a fileno() method).

            NOTE: if istream/ostream is buffered, tell() and the actual
                position might be different.  Use os.lseek to ensure
                its position.  Also, children may affect the stream
                use lseek afterwards to ensure consistent position.
                Alternatively, Fstream can work too
        verbose:
            if verbose, then stderr will be forwarded to sys.stderr
        """
        ensure_formatinfo = FormatInfo('-pix_fmts').formats, FormatInfo('-formats').formats
        if isinstance(commandline, str):
            commandline = shlex.split(commandline)
        # stdin cannot be None because then ffmpeg will eat
        # normal stdin
        stdin = sp.PIPE if istream is None else istream
        self.proc = sp.Popen(
            commandline, stdin=stdin, stdout=ostream, stderr=sp.PIPE)
        self.istream = istream if hasattr(istream, 'read') else None
        self.ostream = ostream if hasattr(ostream, 'write') else None
        self.eforward = None
        self.pre = None
        try:
            try:
                wrapped = io.TextIOWrapper(self.proc.stderr)
            except Exception:
                wrapped = self.proc.stderr
            if self.proc.stdout is not None:
                self.pre = io.BytesIO()
                f = Forwarder(self.proc.stdout, self.pre).start()
            try:
                self.einfo = FFmpegStderrParser(wrapped, verbose)
            except Exception:
                if isinstance(wrapped, io.TextIOWrapper):
                    wrapped.detach()
                raise
            finally:
                if self.proc.stdout is not None:
                    f.close(False, False)
                    self.pre.seek(0)
            self.proc.stderr = None
            if verbose:
                self.eforward = Forwarder(wrapped, sys.stderr, linebuf=True).start()
            else:
                # It seems that if stderr is closed while ffmpeg is still running
                # ffmpeg just stops writing to stderr? doesn't crash or block?
                self.eforward = Forwarder(
                    wrapped, SeqWriter(deque(maxlen=10)), linebuf=True).start()
        except Exception:
            self.proc.communicate(None if self.proc.stdin is None else b'q')
            raise

    def close(self, i=True, o=True, now=True):
        """Close the subprocess.

        i,o: close the input/output streams if given and applicable
        now: if True, communicate b'q' if applicable else None.
            This will cause ffmpeg to close now if it is reading
            from stdin.  If not now, then it'll wait until ffmpeg closes
            on its own.
        """
        if self.proc.returncode is None:
            if now and self.proc.stdin is not None:
                msg = b'q'
            else:
                msg = None
            self.proc.communicate(msg)
            if self.eforward is not None:
                self.eforward.close(True, False)
                self.eforward = None
            if i and self.istream is not None:
                try:
                    self.istream.close()
                except Exception:
                    pass
                self.istream = None
            if o and self.ostream is not None:
                try:
                    self.ostream.close()
                except Exception:
                    pass
                self.ostream = None

    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()

class FFmpegReader(FFmpeg):
    """Read video.

    commandline should output to pipe with rawvideo format
    Try to return the corresponding pixfmt specified by the commandline.
    Failure if unsupported pixel format.
    Expect 1 output video stream to pipe:
    """
    def __init__(
        self, commandline, istream=None, verbose=False, closeerr=True):
        """Same args as FFmpeg.

        ostream is sp.PIPE.
        """
        super(FFmpegReader, self).__init__(
            commandline, istream, sp.PIPE, verbose)
        readcandidates = [
            out for out in self.einfo.outs
            if out.name == 'pipe:' and out.format == 'rawvideo']
        if len(readcandidates) != 1:
            self.close()
            raise Exception(
                'Ambiguous output candidates, expect 1, got: {}'.format(
                    [out.name for out in readcandidates]))
        out = readcandidates[0]
        streamcandidates = [
            stream for stream in out.streams.values()
            if stream.type == 'Video']
        if len(streamcandidates) != 1:
            self.close()
            raise Exception(
                'Ambiguous video stream candidates, expect 1, got: {}'.format(
                    [stream.name for stream in streamcandidates]))
        self.stream = streamcandidates[0]
        try:
            self.shape, self.dtype = self.stream.frameinfo()
        except Exception:
            self.close()
            raise

    def read(self, buf=None):
        """Expect buf to be contiguous if given."""
        if buf is None:
            buf = np.empty(self.shape, self.dtype)
        if self.pre is None:
            return self.proc.stdout.readinto(buf) == buf.nbytes, buf
        else:
            amt = self.pre.readinto(buf)
            if amt != buf.nbytes:
                self.pre = None
                return (
                    (self.proc.stdout.readinto(buf.ravel()[amt:])+amt) == buf.nbytes,
                    buf)
            else:
                return True, buf

    def close(self, i=True, now=True):
        super(FFmpegReader, self).close(i, True, now)

class FFmpegWriter(FFmpeg):
    """Write video.

    commandline should read from pipe in raw video format.
    Writing video specifies framesize so no stderr parsing is necessary.
    In fact, in testing, stderr is only available for parsing after
    writing a certain amount of data to ffmpeg so it's impossible to
    parse stderr to check the first input data anyways.
    """
    def __init__(self, commandline, ostream=None, verbose=False):
        """Expect commandline to read from pipe:

        Data provided to write() should match the input format/pix_fmt etc
        of the commandline.  ostream should be provided if commandline
        indicates output to stdout.
        """
        if verbose:
            self.proc = sp.Popen(commandline, stdin=sp.PIPE, stdout=ostream)
            self._err = None
        else:
            self.proc = sp.Popen(
                commandline, stdin=sp.PIPE, stdout=ostream, stderr=sp.PIPE)
            self._err = Forwarder(
                self.proc.stderr, SeqWriter(deque(maxlen=10)), linebuf=True).start()
        self.ostream = ostream if hasattr(ostream, 'close') else None

    def write(self, frame):
        """Write a frame of data to ffmpeg."""
        # contiguous array seems to write faster
        self.proc.stdin.write(np.ascontiguousarray(frame))

    def error(self):
        """Return any error info."""
        if self._err is None:
            # opened in verbose mode, all info is on stderr
            return None
        return b''.join(self._err.orig[1].data)

    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()
    def close(self, o=True):
        ret = None
        if self.proc.returncode is None:
            try:
                self.proc.stdin.close()
            except OSError:
                pass
            self.proc.wait()
            if o and self.ostream is not None:
                try:
                    self.ostream.close()
                except Exception:
                    pass
                self.ostream = None
            if self._err is not None and self.proc.returncode:
                self._err.close(True, False)
                ret = b''.join(self._err.orig[1].data).decode()
                self._err.orig[1].close()
                self._err = None
            else:
                self._err.close()
                self._err = None
        return ret


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('-c', '--command', nargs='...', help='ffmpeg commandline')
    p.add_argument('-r', '--reader', nargs='...', help='ffmpeg reading commandline')
    p.add_argument('-w', '--writer', nargs='...', help='ffmpeg writing commandline')
    p.add_argument('-v', '--verbose', action='store_true', help='verbose stderr')
    args = p.parse_args()

    if args.command is not None:
        ff = FFmpeg(args.command, verbose=args.verbose)
        print('\n\ninstantiated ff!\n\n')
        print('number of inputs', len(ff.einfo.ins))
        for stream in ff.einfo.istreams.values():
            print(' ', stream.name, stream.type)
            if stream.type == 'Video':
                print('    fps', stream.fps)
                print('    pixfmt', stream.pix_fmt)
                print('    shape', stream.shape)
                print('    bytes/frame', stream.bytes_per_frame())
        print('number of outputs', len(ff.einfo.outs))
        for stream in ff.einfo.ostreams.values():
            print(' ', stream.name, stream.type)
            if stream.type == 'Video':
                print('    fps', stream.fps)
                print('    pixfmt', stream.pix_fmt)
                print('    shape', stream.shape)
                print('    bytes/frame', stream.bytes_per_frame())
        ff.close()
    elif args.reader is not None:
        import cv2
        reader = FFmpegReader(args.reader, verbose=args.verbose)
        print('created reader')
        try:
            success, thing = reader.read()
            fps = reader.stream.fps
            while success:
                if reader.stream.pix_fmt == 'yuv420p':
                    thing = cv2.cvtColor(thing, cv2.COLOR_YUV2BGR_I420)
                cv2.imshow('thing', thing)
                success, thing = reader.read()
                success = success and cv2.waitKey(1) != ord('q')
            reader.close()

            # cap = cv2.VideoCapture(0)
            # success, thing = cap.read()
            # while success:
                # cv2.imshow('thing', thing)
                # success, thing = cap.read()
                # success = success and cv2.waitKey(1) != ord('q')
            # cap.release()
        finally:
            reader.close()
    elif args.writer is not None:
        command = args.writer
        width, height = map(
            int, args.writer[args.writer.index('-s')+1].split('x'))
        framebuf = np.zeros((height, width, 3), np.uint8)
        writer = FFmpegWriter(args.writer, verbose=args.verbose)
        for i in range(width):
            print(i, end='\r')
            framebuf[:,i] = np.random.randint(0, 256, (height,3), np.uint8)
            writer.write(framebuf)
            framebuf[:,i] = 0
        print('done')
        writer.close()
        print('closed')
