"""Parse ffmpeg streams.

Only video or audio streams supported.
"""
__all__ = ['Stream']
import re

class Stream(object):
    STREAM = re.compile(
        r'\s+Stream #(?P<name>\d+:\d+)(?:\(\S+\))?: '
        r'(?P<type>\S+): (?P<info>.*)')
    is_stream = re.compile(r'\s+Stream #').match

    def __init__(self, name, tp=None, info=None):
        self.name = name
        self.type = tp
        self.info = info

    @staticmethod
    def parse(line):
        match = Stream.STREAM.match(line)
        if not match:
            return None
        name, tp, info = map(match.group, ('name', 'type', 'info'))
        if tp == 'Video':
            return VideoStream(name, tp, info)
        elif tp == 'Audio':
            return AudioStream(name, tp, info)
        else:
            return Stream(name, tp, info)

    def __str__(self):
        return '#{}: {}, {}'.format(self.name, self.type, self.info)


parenthesized = r'\([^)]\)'
bracketed = r'\[[^]]\]'
streaminfo = re.compile(
    r'\s*[^,([]+(?:\s*{}|\s*{})*(?:,|$)'.format(
        parenthesized, bracketed))


class VideoStream(Stream):
    pass

class AudioStream(Stream):
    pass


if __name__ == '__main__':
    from ._testing import streams
    for stream in streams:
        thing = Stream.parse(stream['line'])
        if stream['type'] == 'Video':
            assert isinstance(thing, VideoStream)
        elif stream['type'] == 'Autio':
            assert isinstance(thing, AudioStream)

        print(stream['line'])
        print(thing.info)
        print(streaminfo.findall(thing.info))


    segments = [
        'rawvideo,',
        ' 1 reference frame (BGR[24] / 0x18524742),',
        ' bgr24,',
        ' 1280x720 [SAR 1:1 DAR 16:9],',
        ' q=2-31,',
        ' 200 kb/s,',
        ' 30 fps,',
        ' 30 tbn,',
        ' 30 tbc (default)'
    ]

    for seg in segments:
        print(streaminfo.search(seg))
