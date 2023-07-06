"""Parse ffmpeg streams.

Only video or audio streams supported.
"""
__all__ = ['Stream', 'VideoStream', 'AudioStream']
import re

from ..info import Codecs, PixFmts


class Stream(object):
    """A basica stream class.

    Subclasses should have attrs list: tuple of attrname to pattern.
    """

    streaminfo = re.compile(
        r'\s*[^,([]+(?:\s*\([^)]+\)|\s*\[[^]]+\])*(?:,|$)')
    stream = re.compile(
        r'\s+Stream #(?P<name>\d+:\d+)(?:\(\S+\))?: '
        r'(?P<type>\S+): (?P<info>.*)')

    attrs = []

    def __init__(self, name, tp, info):
        """Initialize a stream.

        name: str
            Name of the stream.
        tp: str
            Type of the stream.
        info: list of str
            List of fields of info for the stream.
        """
        self.name = name
        self.type = tp
        self.info = info
        it = iter(info)
        # not sure if order is actually fixed relatively, but it seems
        # that way from all the different ffmpeg versions i've tested.
        for attr, pat in self.attrs:
            for item in it:
                m = pat.match(item)
                if m:
                    setattr(self, attr, m.group(attr))
                    break
            else:
                setattr(self, attr, None)

    @staticmethod
    def parse(line):
        match = Stream.stream.match(line)
        if not match:
            return None
        name, tp, info = map(match.group, ('name', 'type', 'info'))
        info = Stream.streaminfo.findall(info)
        if tp == 'Video':
            return VideoStream(name, tp, info)
        elif tp == 'Audio':
            return AudioStream(name, tp, info)
        else:
            return Stream(name, tp, info)

    def __repr__(self):
        return '{} Stream #{}: {}'.format(self.type, self.name, self.info)



class VideoStream(Stream):
    attrs = [
        ('codec', re.compile(r'\s*(?P<codec>{})'.format('|'.join(Codecs())))),
        ('pix_fmt', re.compile(r'\s*(?P<pix_fmt>{})'.format('|'.join(PixFmts())))),
        ('shape', re.compile(r'\s*(?P<shape>\d+x\d+)')),
        ('fps', re.compile(r'\s*(?P<fps>\d+) (?:fps|tbr)')),
    ]

    def __init__(self, *args):
        super(VideoStream, self).__init__(*args)
        self.width, self.height = map(int, self.shape.split('x'))
        if self.fps is not None:
            self.fps = int(self.fps)

    def __repr__(self):
        return 'Video Stream #{}: {}, {}, {}x{}, {}'.format(
            self.name,
            self.codec,
            self.pix_fmt,
            self.width,
            self.height,
            self.fps)



class AudioStream(Stream):
    pass


if __name__ == '__main__':
    from ._testing import streams
    for stream in streams:
        thing = Stream.parse(stream['line'])
        if stream['type'] == 'Video':
            assert isinstance(thing, VideoStream)
            for attr in 'codec pix_fmt width height fps'.split():
                v1 = getattr(thing, attr)
                v2 = stream[attr]
                assert v1 == v2
        elif stream['type'] == 'Audio':
            assert isinstance(thing, AudioStream)
