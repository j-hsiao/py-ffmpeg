"""Parse ffmpeg stderr.

Return information about the streams.
"""
__all__ = ['FFmpegStderrParser']

from collections import deque
import io
import re
from itertools import chain
import sys

import numpy as np

from .holder import Holder
from .fmts import FormatInfo

class Partitions(object):
    """Iterate by partition.

    Per partition, yields an iterator to iterate over items in the
    partition.
    """
    def __init__(self, it, pred):
        """Initialize iterator.

        f: iterator source
        pred: a predicate, True if partition starter.
        """
        self.pred = pred
        self.it = it

    def __iter__(self):
        """Yield iterators over partitions.

        Iterators always consume at least 1 item.
        """
        pred = self.pred
        it = _it = iter(self.it)
        pinfo = None
        while self.it is not None:
            try:
                partition = self.Partition(it, pred, pinfo)
            except StopIteration:
                return
            yield partition
            stop = partition.stop
            if stop is None:
                return
            elif stop is partition:
                # partition not fully consumed
                pinfo = partition.stop = None
                it = _it
            else:
                pinfo, item = stop
                it = chain((item,), _it)

    class Partition(object):
        """A single partition.

        Has an attr: stop.  If stop is None, that implies the iterator
        is fully exhausted.

        May consume an item on construction to evaluate info.
        Always yields at least 1 item and continues until the next start
        of a partition.
        """
        def __init__(self, it, pred, info):
            """Initialize a single partition."""
            it = iter(it)
            if not info:
                thing = next(it)
                it = chain((thing,), it)
                info = pred(thing)
            self.it = it
            self.info = info
            self.pred = pred
            self.stop = self

        def __del__(self):
            """Break reference cycle."""
            self.stop = None

        def __iter__(self):
            pred = self.pred
            it = self.it
            yield next(it)
            for thing in it:
                result = pred(thing)
                if result:
                    self.stop = result, thing
                    return
                else:
                    yield thing
            self.stop = None

class Stream(object):
    STREAM = re.compile(
        r'\s+Stream #(?P<name>\d+:\d+)(?:\(\S+\))?: '
        r'(?P<type>\S+): (?P<info>.*)')
    is_stream = re.compile(r'\s+Stream #').match

    def __init__(self, lineOrName, tp=None, info=None):
        if info is None:
            match = self.STREAM.match(lineOrName)
            self.name = match.group('name')
            self.type = match.group('type')
            self.info = match.group('info')
        else:
            self.name = lineOrName
            self.type = tp
            self.info = info

    @staticmethod
    def parse(line):
        match = Stream.STREAM.match(line)
        name, tp, info = map(match.group, ('name', 'type', 'info'))
        if tp == 'Video':
            return VideoStream(name, tp, info)
        elif tp == 'Audio':
            return AudioStream(name, tp, info)
        else:
            return Stream(name, tp, info)

    def __str__(self):
        return '#{}: {}, {}'.format(self.name, self.type, self.info)

class VideoStream(Stream):
    """Parse a Video Stream line.

    Shape and pix_fmt are required.
    Additionally tries to parse format and fps.
    These are optional and will be None if not found.
    """
    SHAPE = re.compile(r',\s+(?P<width>[1-9]\d*)x(?P<height>[1-9]\d*)(?:,|\s|$)')
    FPS = re.compile(r'(?P<fps>\d+) (?:tbr|fps)(?:,|\s|$)')
    PIX_FMTS = None
    FORMATS = None
    NPENDIAN = {'le': '<', 'be': '>', None: ''}
    YUV = re.compile(
        r'(?P<name>[pja]?[yuv]+[pja]?[64210]{2,3}p?)'
        r'(?P<bitsize>[0-9]+)'
        r'?(?P<endian>le|be)?')

    def __init__(self, *args):
        """Initialize videostream."""
        super(VideoStream, self).__init__(*args)
        if self.type != 'Video':
            raise Exception('not a video stream')
        h = Holder()
        info = self.info
        self.shape = tuple(map(int, self.SHAPE.search(info).groups()))
        try:
            self.fps = int(self.FPS.search(info).group('fps'))
        except AttributeError:
            self.fps = None
        # Calculate these after loading
        # because they're slower
        if self.PIX_FMTS is None:
            VideoStream.PIX_FMTS = re.compile(
                '|'.join(FormatInfo('-pix_fmts')).join(
                    (r'(?:^|, )(?P<pix_fmt>', r')(?:\s?\([^)]+\))*(?:,|\s|$)')))
            VideoStream.FORMATS = re.compile(
                '|'.join(FormatInfo('-formats')).join(
                    (r'(?:^|, )(?P<format>', r')(?:\s+\([^)]+\))*(?:,|\s|$)')))
        try:
            self.format = self.FORMATS.search(info).group('format')
        except AttributeError:
            self.format = None
        self.pix_fmt = self.PIX_FMTS.search(info).group('pix_fmt')

    def bytes_per_frame(self):
        npixels = self.shape[0] * self.shape[1]
        pixbits = FormatInfo('-pix_fmts')[self.pix_fmt]['pixbits']
        framebits = npixels * pixbits
        if framebits % 8:
            raise Exception('incomplete byte per frame')
        return framebits // 8


    def framebuf(self):
        """Try to return logical frame shape and np dtype.

        If failure, then just return bytes.
        """
        pixinfo = FormatInfo('-pix_fmts')[self.pix_fmt]
        pixbits = pixinfo['pixbits']
        width, height = self.shape
        framebits = width*height*pixbits
        framebytes, extrabits = divmod(framebits, 8)
        if extrabits:
            raise Exception(
                'no info for pixel format {}'.format(self.pix_fmt))
        bitdepths = pixinfo.get('bitdepths')
        if bitdepths is None:
            return np.empty(framebytes, np.uint8), None
        pixbytes, extra_pixbits = zip(*[divmod(depth, 8) for depth in bitdepths])
        if any(extra_pixbits):
            return np.empty(framebytes, np.uint8), None
        endian = self.NPENDIAN[pixinfo.get('endian')]
        if ((self.YUV.match(self.pix_fmt.lower()) or
                self.pix_fmt.lower() in ('nv12', 'nv21'))
                and len(set(pixbytes)) == 1):
            # yuv-ish type of frame?
            nelems, extra_framebits = divmod(framebytes, pixbytes[0])
            if not extra_framebits:
                dtype = np.dtype('{}u{}'.format(endian, pixbytes[0]))
                nrows, extra_width = divmod(nelems, width)
                channels, extra_channels = divmod(nrows, height)
                if channels == 1:
                    if extra_width:
                        buf = np.empty((nrows + 3 - nrows%3, width), dtype)
                        return buf[:nrows+1], buf
                    else:
                        return np.empty((nrows, width), dtype), None
                elif extra_width or extra_channels:
                    return np.empty(framebytes, np.uint8), None
                lowered = self.pix_fmt.lower()
                if channels > 1:
                    if 'yuv' in lowered:
                        shape = (channels, height, width)
                    else:
                        shape = (height, width, channels)
                else:
                    shape = (height, width)
                return np.empty(shape, dtype), None
        elif sum(bitdepths) == pixbits:
            if len(set(pixbytes)) == 1:
                return np.empty(
                    (height, width, len(pixbytes)),
                    np.dtype('{}u{}'.format(endian, pixbytes[0]))), None
            else:
                tps = []
                for nbytes in pixbytes:
                    tps.append('{}u{}'.format(endian, nbytes))
                return np.empty(
                    (height, width), np.dtype(', '.join(tps))), None
        return np.empty(framebytes, np.uint8), None

    def __str__(self):
        return '#{}: {}, {}'.format(
            self.name, self.type,
            dict(
                shape=self.shape,
                fps=self.fps,
                format=self.format,
                pix_fmt=self.pix_fmt))

class AudioStream(Stream):
    def __init__(self, *args):
        super(AudioStream, self).__init__(*args)
        if self.type != 'Audio':
            raise Exception('not an audio stream')

class IO(object):
    """Input/output."""
    io = re.compile(
        r"(?=Input #\d+, \S+, from '.*':$|Output #\d+, \S+, to '.*':)"
        r"(?P<type>In|Out)put #(?P<number>\d+), (?P<format>\S*), "
        r"(?:from|to) '(?P<name>.*)':\s*$")

    def __init__(self, lines):
        """Initialize an Input/Output from ffmpeg stderr lines.

        lines: a list of lines corresponding to input/output
        """
        it = iter(lines)
        match = self.io.match(next(it))
        self.type = match.group('type')
        self.number = match.group('number')
        self.format = match.group('format')
        self.name = match.group('name')
        self.streams = {}
        for partition in Partitions(it, Stream.is_stream):
            streamit = iter(partition)
            if partition.info:
                stream = Stream.parse(next(streamit))
                self.streams[stream.name] = stream
            deque(streamit, maxlen=0)

class StreamMap(object):
    """Stream mapping."""
    MAPPING = re.compile(
        r'\s+Stream #(?P<istream>\d+:\d+).*'
        r'-> #(?P<ostream>\d+:\d+)'
        r' \((?P<iformat>\S+).*\s+->\s+(?P<oformat>\S+).*\)')
    def __init__(self, lines):
        it = iter(lines)
        header = next(it)
        self.mappings = []
        self.i2o = {}
        for line in it:
            match = self.MAPPING.match(line)
            self.i2o[match.group('istream')] = match.group('ostream')
            self.mappings.append(
                tuple(map(
                    match.groupdict().__getitem__,
                    ('istream', 'ostream', 'iformat', 'oformat'))))
    def __iter__(self):
        return iter(self.mappings)

class FFmpegStderrParser(object):
    pat = re.compile(r'(?P<tp>Output |Input |Stream mapping)|(?P<other>\S+)')
    def __init__(self, err, verbose=False):
        self.ins = []
        self.outs = []
        self.istreams = {}
        self.ostreams = {}
        self.streammap = None
        for partition in Partitions(err, self.pat.match):
            info = partition.info
            if verbose:
                partition = list(partition)
                print(''.join(partition), file=sys.stderr, end='')
            if not info or info.group('other'):
                continue
            tp = info.group('tp')
            if tp == 'Stream mapping':
                self.streammap = StreamMap(partition)
                if self._done():
                    return
            else:
                ioput = IO(partition)
                if ioput.type == 'In':
                    self.ins.append(ioput)
                    self.istreams.update(ioput.streams)
                else:
                    self.outs.append(ioput)
                    self.ostreams.update(ioput.streams)
                    if self._done():
                        return
    def _done(self):
        ostreams = set(self.ostreams)
        return (
            self.streammap is not None
            and set(self.streammap.i2o.values()) == ostreams)


# VIDEO = 'Video'
# AUDIO = 'Audio'
# 
# INDENTED = re.compile(r'^\s+')
# FF_INPUT = re.compile(r"^Input #(?P<num>\d+).* from '(?P<name>.*)':")
# FF_OUTPUT = re.compile(r"^Output #(?P<num>\d+).* to '(?P<name>.*)':")
# 
# FF_STREAMMAP_ENTRY = re.compile(
#     r'^\s+Stream #(?P<inum>\d+):(?P<istream>\d+).+->.+'
#     r'#(?P<onum>\d+):(?P<ostream>\d+)')
# 
# FF_STREAM = re.compile(
#     r'^\s+Stream #(?P<num>\d+):(?P<stream>\d+)(?:\([\w\s]*\))*: (?P<type>\w+): '
#     r'(?P<info>.*)$')
# FF_PIXFMT_INFO, FF_PIXFMT = FF_PIXFMTS()
# FF_VSTREAM_INFO = re.compile(
#     ''.join((
#     r'(?P<format>\w+[^,]*).*, ',
#     FF_PIXFMT.pattern,
#     r'.*',
#     FF_SHAPE.pattern,
#     r'[^,]*,?',
#     r'(?P<remain>.*)$'
# )))


if __name__ == '__main__':
    import traceback
    streams = [
        "    Stream #0:0(eng): Video: h264 (High), yuv420p, 1280x540 [SAR 1:1 DAR 64:27], 15 fps, 15 tbr, 1k tbn, 30 tbc (default)",
        "    Stream #0:0: Video: rawvideo (YUY2 / 0x32595559), yuyv422, 1280x720, 147456 kb/s, 10 fps, 10 tbr, 1000k tbn, 1000k tbc",
        "    Stream #0:0: Video: mjpeg, yuvj420p(pc, bt470bg/unknown/unknown), 440x293 [SAR 1:1 DAR 440:293], 25 tbr, 25 tbn, 25 tbc",
        "    Stream #0:0: Video: mjpeg, gray(bt470bg/unknown/unknown), 250x250 [SAR 1:1 DAR 1:1], 25 tbr, 25 tbn, 25 tbc",
        "    Stream #0:0(eng): Video: h264 (High), yuv420p, 1280x540 [SAR 1:1 DAR 64:27], 15 fps, 15 tbr, 1k tbn, 30 tbc (default)",
        "    Stream #0:0(eng): Video: rawvideo (BGR[24] / 0x18524742), bgr24, 1280x540 [SAR 1:1 DAR 64:27], q=2-31, 200 kb/s, 15 fps, 15 tbn, 15 tbc (default)",
        "    Stream #0:0: Video: h264 (High), yuv420p(progressive), 452x800, 30 fps, 30 tbr, 1k tbn, 60 tbc (default)",
        "    Stream #0:1: Audio: aac (LC), 44100 Hz, stereo, fltp (default)",
        "    Stream #0:0: Video: rawvideo (BGR[24] / 0x18524742), bgr24, 452x800, q=2-31, 260352 kb/s, 30 fps, 30 tbn, 30 tbc (default)",
        "    Stream #0:0: Video: h264 (High), yuv420p(progressive), 500x850, 30 fps, 30 tbr, 1k tbn, 60 tbc (default)",
        "    Stream #0:1: Audio: aac (LC), 44100 Hz, stereo, fltp (default)",
        "    Stream #1:0: Video: h264 (High), yuv420p(progressive), 848x480, 30 fps, 30 tbr, 1k tbn, 60 tbc (default)",
        "    Stream #1:1: Audio: aac (LC), 44100 Hz, stereo, fltp (default)",
        "    Stream #1:0: Video: h264 (High), yuv420p(progressive), 848x480",
        "    Stream #0:0: Video: h264 (libx264) (H264 / 0x34363248), yuv420p(progressive), 500x850, q=-1--1, 30 fps, 1k tbn, 30 tbc (default)",
        "    Stream #0:0: Video: rawvideo (BGR[24] / 0x18524742), bgr24, 500x500, q=2-31, 12000 kb/s, 2 fps, 2 tbn, 2 tbc (default)",
        "    Stream #0:0: Video: rawvideo, 1 reference frame (BGR[24] / 0x18524742), bgr24, 1280x720 [SAR 1:1 DAR 16:9], q=2-31, 200 kb/s, 30 fps, 30 tbn, 30 tbc (default)"
    ]
    streaminfo = [
        ('h264', 'yuv420p', 1280, 540, 15),
        ('rawvideo', 'yuyv422', 1280, 720, 10),
        ('mjpeg', 'yuvj420p', 440,293, 25),
        ('mjpeg', 'gray', 250,250, 25),
        ('h264', 'yuv420p', 1280,540, 15),
        ('rawvideo', 'bgr24', 1280, 540, 15),
        ('h264', 'yuv420p', 452, 800, 30),
        ('rawvideo', 'bgr24', 452, 800, 30),
        ('h264', 'yuv420p', 500, 850, 30),
        ('h264', 'yuv420p', 848, 480, 30),
        ('h264', 'yuv420p', 848, 480, None),
        ('h264', 'yuv420p', 500, 850, 30),
        ('rawvideo', 'bgr24', 500, 500, 2),
        ('rawvideo', 'bgr24', 1280, 720, 30)
    ]
    vstreams = iter(streaminfo)
    for streamdata in streams:
        try:
            s = Stream.parse(streamdata)
        except Exception:
            traceback.print_exc()
            print(streamdata)
            raise
        if s.type == 'Audio':
            if 'Audio: ' not in streamdata:
                print('got audio but not correct?')
                print(streamdata)
            else:
                print('ok')
        elif s.type == 'Video':
            expected = next(vstreams)
            result = (s.format, s.pix_fmt, s.shape[0], s.shape[1], s.fps)
            if result != expected:
                print(streamdata)
                print('expected')
                print(expected)
                print('but got')
                print(result)
            else:
                print('ok')
        else:
            print('Unexpected stream type:', s.type)
            print(repr(streamdata))

    sample_stderrs = [
        (
            b"Input #0, matroska,webm, from '/home/andy/Videos/asdf.mkv':\n"
            b"  Metadata:\n"
            b"    COMPATIBLE_BRANDS: isomiso2avc1mp41\n"
            b"    MAJOR_BRAND     : isom\n"
            b"    MINOR_VERSION   : 512\n"
            b"    ENCODER         : Lavf56.40.101\n"
            b"  Duration: 00:00:58.20, start: 0.000000, bitrate: 969 kb/s\n"
            b"    Stream #0:0(eng): Video: h264 (High), yuv420p, 1280x540 [SAR 1:1 DAR 64:27], 15 fps, 15 tbr, 1k tbn, 30 tbc (default)\n"
            b"    Metadata:\n"
            b"      LANGUAGE        : eng\n"
            b"      HANDLER_NAME    : VideoHandler\n"
            b"      ENCODER         : Lavc56.60.100 libx264\n"
            b"      DURATION        : 00:00:58.200000000\n"
            b"Output #0, rawvideo, to 'pipe:':\n"
            b"  Metadata:\n"
            b"    COMPATIBLE_BRANDS: isomiso2avc1mp41\n"
            b"    MAJOR_BRAND     : isom\n"
            b"    MINOR_VERSION   : 512\n"
            b"    encoder         : Lavf56.40.101\n"
            b"    Stream #0:0(eng): Video: rawvideo (BGR[24] / 0x18524742), bgr24, 1280x540 [SAR 1:1 DAR 64:27], q=2-31, 200 kb/s, 15 fps, 15 tbn, 15 tbc (default)\n"
            b"    Metadata:\n"
            b"      LANGUAGE        : eng\n"
            b"      HANDLER_NAME    : VideoHandler\n"
            b"      DURATION        : 00:00:58.200000000\n"
            b"      encoder         : Lavc56.60.100 rawvideo\n"
            b"Stream mapping:\n"
            b"  Stream #0:0 -> #0:0 (h264 (native) -> rawvideo (native))\n"),
        (
            b"Input #0, matroska,webm, from '2020-11-08 11-10-12.mkv':\n"
            b"  Metadata:\n"
            b"    ENCODER         : Lavf58.29.100\n"
            b"  Duration: 00:00:06.30, start: 0.000000, bitrate: 2620 kb/s\n"
            b"    Stream #0:0: Video: h264 (High), yuv420p(progressive), 452x800, 30 fps, 30 tbr, 1k tbn, 60 tbc (default)\n"
            b"    Metadata:\n"
            b"      DURATION        : 00:00:06.300000000\n"
            b"    Stream #0:1: Audio: aac (LC), 44100 Hz, stereo, fltp (default)\n"
            b"    Metadata:\n"
            b"      title           : simple_aac\n"
            b"      DURATION        : 00:00:06.200000000\n"
            b"File 'nul' already exists. Overwrite? [y/N] y\n"
            b"Stream mapping:\n"
            b"  Stream #0:0 -> #0:0 (h264 (native) -> rawvideo (native))\n"
            b"Press [q] to stop, [?] for help\n"
            b"Output #0, rawvideo, to 'nul':\n"
            b"  Metadata:\n"
            b"    encoder         : Lavf58.44.100\n"
            b"    Stream #0:0: Video: rawvideo (BGR[24] / 0x18524742), bgr24, 452x800, q=2-31, 260352 kb/s, 30 fps, 30 tbn, 30 tbc (default)\n"
            b"    Metadata:\n"
            b"      DURATION        : 00:00:06.300000000\n"
            b"      encoder         : Lavc58.90.100 rawvideo\n"
            b"frame=  189 fps=0.0 q=-0.0 Lsize=  200222kB time=00:00:06.30 bitrate=260352.0kbits/s dup=1 drop=0 speed=33.6x\n"
            b"video:200222kB audio:0kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.000000%\n"),
        (
            b"Input #0, matroska,webm, from 'hipsway.mkv':\n"
            b"  Metadata:\n"
            b"    ENCODER         : Lavf58.29.100\n"
            b"  Duration: 00:00:24.03, start: 0.000000, bitrate: 2626 kb/s\n"
            b"    Stream #0:0: Video: h264 (High), yuv420p(progressive), 500x850, 30 fps, 30 tbr, 1k tbn, 60 tbc (default)\n"
            b"    Metadata:\n"
            b"      DURATION        : 00:00:24.033000000\n"
            b"    Stream #0:1: Audio: aac (LC), 44100 Hz, stereo, fltp (default)\n"
            b"    Metadata:\n"
            b"      title           : simple_aac\n"
            b"      DURATION        : 00:00:23.917000000\n"
            b"Input #1, matroska,webm, from 'keyboard.mkv':\n"
            b"  Metadata:\n"
            b"    ENCODER         : Lavf58.29.100\n"
            b"  Duration: 00:00:25.83, start: 0.000000, bitrate: 2650 kb/s\n"
            b"    Stream #1:0: Video: h264 (High), yuv420p(progressive), 848x480, 30 fps, 30 tbr, 1k tbn, 60 tbc (default)\n"
            b"    Metadata:\n"
            b"      DURATION        : 00:00:25.833000000\n"
            b"    Stream #1:1: Audio: aac (LC), 44100 Hz, stereo, fltp (default)\n"
            b"    Metadata:\n"
            b"      title           : simple_aac\n"
            b"      DURATION        : 00:00:25.728000000\n"
            b"Stream mapping:\n"
            b"  Stream #0:0 -> #0:0 (h264 (native) -> h264 (libx264))\n"
            b"  Stream #1:1 -> #0:1 (aac (native) -> vorbis (libvorbis))\n"
            b"  Stream #0:1 -> #1:0 (aac (native) -> vorbis (libvorbis))\n"
            b"  Stream #1:0 -> #1:1 (h264 (native) -> h264 (libx264))\n"
            b"Press [q] to stop, [?] for help\n"
            b"[libx264 @ 000001e99d0950c0] using cpu capabilities: MMX2 SSE2Fast SSSE3 SSE4.2 AVX FMA3 BMI2 AVX2\n"
            b"[libx264 @ 000001e99d0950c0] profile High, level 3.1, 4:2:0, 8-bit\n"
            b"[libx264 @ 000001e99d0950c0] 264 - core 160 - H.264/MPEG-4 AVC codec - Copyleft 2003-2020 - http://www.videolan.org/x264.html - options: cabac=1 ref=3 deblock=1:0:0 analyse=0x3:0x113 me=hex subme=7 psy=1 psy_rd=1.00:0.00 mixed_ref=1 me_range=16 chroma_me=1 trellis=1 8x8dct=1 cqm=0 deadzone=21,11 fast_pskip=1 chroma_qp_offset=-2 threads=12 lookahead_threads=2 sliced_threads=0 nr=0 decimate=1 interlaced=0 bluray_compat=0 constrained_intra=0 bframes=3 b_pyramid=2 b_adapt=1 b_bias=0 direct=1 weightb=1 open_gop=0 weightp=2 keyint=250 keyint_min=25 scenecut=40 intra_refresh=0 rc_lookahead=40 rc=crf mbtree=1 crf=23.0 qcomp=0.60 qpmin=0 qpmax=69 qpstep=4 ip_ratio=1.40 aq=1:1.00\n"
            b"Output #0, matroska, to 'o1.mkv':\n"
            b"  Metadata:\n"
            b"    encoder         : Lavf58.44.100\n"
            b"    Stream #0:0: Video: h264 (libx264) (H264 / 0x34363248), yuv420p(progressive), 500x850, q=-1--1, 30 fps, 1k tbn, 30 tbc (default)\n"
            b"    Metadata:\n"
            b"      DURATION        : 00:00:24.033000000\n"
            b"      encoder         : Lavc58.90.100 libx264\n"
            b"    Side data:\n"
            b"      cpb: bitrate max/min/avg: 0/0/0 buffer size: 0 vbv_delay: N/A\n"
            b"    Stream #0:1: Audio: vorbis (libvorbis) (oV[0][0] / 0x566F), 44100 Hz, stereo, fltp (default)\n"
            b"    Metadata:\n"
            b"      title           : simple_aac\n"
            b"      DURATION        : 00:00:25.728000000\n"
            b"      encoder         : Lavc58.90.100 libvorbis\n"
            b"[libx264 @ 000001e99d09a080] using cpu capabilities: MMX2 SSE2Fast SSSE3 SSE4.2 AVX FMA3 BMI2 AVX2\n"
            b"[libx264 @ 000001e99d09a080] profile High, level 3.1, 4:2:0, 8-bit\n"
            b"[libx264 @ 000001e99d09a080] 264 - core 160 - H.264/MPEG-4 AVC codec - Copyleft 2003-2020 - http://www.videolan.org/x264.html - options: cabac=1 ref=3 deblock=1:0:0 analyse=0x3:0x113 me=hex subme=7 psy=1 psy_rd=1.00:0.00 mixed_ref=1 me_range=16 chroma_me=1 trellis=1 8x8dct=1 cqm=0 deadzone=21,11 fast_pskip=1 chroma_qp_offset=-2 threads=12 lookahead_threads=2 sliced_threads=0 nr=0 decimate=1 interlaced=0 bluray_compat=0 constrained_intra=0 bframes=3 b_pyramid=2 b_adapt=1 b_bias=0 direct=1 weightb=1 open_gop=0 weightp=2 keyint=250 keyint_min=25 scenecut=40 intra_refresh=0 rc_lookahead=40 rc=crf mbtree=1 crf=23.0 qcomp=0.60 qpmin=0 qpmax=69 qpstep=4 ip_ratio=1.40 aq=1:1.00\n"
            b"Output #1, matroska, to 'o2.mkv':\n"
            b"  Metadata:\n"
            b"    encoder         : Lavf58.44.100\n"
            b"    Stream #1:0: Audio: vorbis (libvorbis) (oV[0][0] / 0x566F), 44100 Hz, stereo, fltp (default)\n"
            b"    Metadata:\n"
            b"      title           : simple_aac\n"
            b"      DURATION        : 00:00:23.917000000\n"
            b"      encoder         : Lavc58.90.100 libvorbis\n"
            b"    Stream #1:1: Video: h264 (libx264) (H264 / 0x34363248), yuv420p, 848x480, q=-1--1, 30 fps, 1k tbn, 30 tbc (default)\n"
            b"    Metadata:\n"
            b"      DURATION        : 00:00:25.833000000\n"
            b"      encoder         : Lavc58.90.100 libx264\n"
            b"    Side data:\n"
            b"      cpb: bitrate max/min/avg: 0/0/0 buffer size: 0 vbv_delay: N/A\n"),
        (
            b'ffmpeg version git-2020-06-04-7f81785 Copyright (c) 2000-2020 the FFmpeg developers\r\n'
            b'  built with gcc 9.3.1 (GCC) 20200523\r\n'
            b'  configuration: --enable-gpl --enable-version3 --enable-sdl2 --enable-fontconfig --enable-gnutls --enable-iconv --enable-libass --enable-libdav1d --enable-libbluray --enable-libfreetype --enable-libmp3lame --enable-libopencore-amrnb --enable-libopencore-amrwb --enable-libopenjpeg --enable-libopus --enable-libshine --enable-libsnappy --enable-libsoxr --enable-libsrt --enable-libtheora --enable-libtwolame --enable-libvpx --enable-libwavpack --enable-libwebp --enable-libx264 --enable-libx265 --enable-libxml2 --enable-libzimg --enable-lzma --enable-zlib --enable-gmp --enable-libvidstab --enable-libvmaf --enable-libvorbis --enable-libvo-amrwbenc --enable-libmysofa --enable-libspeex --enable-libxvid --enable-libaom --disable-w32threads --enable-libmfx --enable-ffnvcodec --enable-cuda-llvm --enable-cuvid --enable-d3d11va --enable-nvenc --enable-nvdec --enable-dxva2 --enable-avisynth --enable-libopenmpt --enable-amf\r\n'
            b'  libavutil      56. 49.100 / 56. 49.100\r\n'
            b'  libavcodec     58. 90.100 / 58. 90.100\r\n'
            b'  libavformat    58. 44.100 / 58. 44.100\r\n'
            b'  libavdevice    58.  9.103 / 58.  9.103\r\n'
            b'  libavfilter     7. 84.100 /  7. 84.100\r\n'
            b'  libswscale      5.  6.101 /  5.  6.101\r\n'
            b'  libswresample   3.  6.100 /  3.  6.100\r\n'
            b'  libpostproc    55.  6.100 / 55.  6.100\r\n'
            b"Input #0, matroska,webm, from 'out.mkv':\r\n"
            b'  Metadata:\r\n'
            b'    ENCODER         : Lavf58.44.100\r\n'
            b'  Duration: 00:00:05.00, start: 0.000000, bitrate: 4 kb/s\r\n'
            b'    Stream #0:0: Video: h264 (High 4:4:4 Predictive), yuv444p(progressive), 500x500, 2 fps, 2 tbr, 1k tbn, 4 tbc (default)\r\n'
            b'    Metadata:\r\n'
            b'      ENCODER         : Lavc58.90.100 libx264\r\n'
            b'      DURATION        : 00:00:05.000000000\r\n'
            b'Stream mapping:\r\n'
            b'  Stream #0:0 -> #0:0 (h264 (native) -> rawvideo (native))\r\n'
            b'Press [q] to stop, [?] for help\r\n'
            b'frame=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \rframe=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \rframe=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \rframe=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \rframe=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \rframe=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \r'
            b"Output #0, rawvideo, to 'pipe:':\r\n"
            b'  Metadata:\r\n'
            b'    encoder         : Lavf58.44.100\r\n'
            b'    Stream #0:0: Video: rawvideo (BGR[24] / 0x18524742), bgr24, 500x500, q=2-31, 12000 kb/s, 2 fps, 2 tbn, 2 tbc (default)\r\n'
            b'    Metadata:\r\n'
            b'      DURATION        : 00:00:05.000000000\r\n'
            b'      encoder         : Lavc58.90.100 rawvideo\r\n')
    ]
    for i, data in enumerate(sample_stderrs):
        print('sample', i)
        with io.TextIOWrapper(io.BytesIO(data)) as f:
            parser = FFmpegStderrParser(f, verbose=True)
            print('number of inputs', len(parser.ins))
            for inp in parser.ins:
                print(inp.name)
                print('  number of streams:', len(inp.streams))
                for stream in inp.streams.values():
                    if stream.type == 'Video':
                        print('    Video Stream')
                        print('   ', stream)
                        npixels = stream.shape[0] * stream.shape[1]
                        pixinfo = FormatInfo('-pix_fmts')[stream.pix_fmt]
                        print('    bits per pixel:', pixinfo['pixbits'])
                        print('    bytes per pixel:', pixinfo['pixbits']/8)
                        print('    number of pixels', npixels)
                        print('    frame bytes:', pixinfo['pixbits']/8 * npixels)
                        print('    from method:', stream.bytes_per_frame())
                    else:
                        print('    other stream')
                        print('   ', stream)
            print('number of outputs', len(parser.outs))
            for out in parser.outs:
                print(out.name)
                print('  number of streams:', len(out.streams))
                for stream in out.streams.values():
                    if stream.type == 'Video':
                        print('    Video Stream')
                        print('   ', stream)
                        npixels = stream.shape[0] * stream.shape[1]
                        pixinfo = FormatInfo('-pix_fmts')[stream.pix_fmt]
                        print('    bits per pixel:', pixinfo['pixbits'])
                        print('    bytes per pixel:', pixinfo['pixbits']/8)
                        print('    number of pixels', npixels)
                        print('    frame bytes:', pixinfo['pixbits']/8 * npixels)
                        print('    from method:', stream.bytes_per_frame())
                    else:
                        print('    other stream')
                        print('   ', stream)

            for mapping in parser.streammap.mappings:
                print('mapping {} to {} ({}->{})'.format(*mapping))
                print(parser.istreams[mapping[0]])
                print('to')
                print(parser.ostreams[mapping[1]])
