__all__ = ['IO']
import re

from .stream import Stream
from .blockiter import BlockIter

class IO(object):
    inp = re.compile(
        r"(?P<type>In)put #(?P<num>\d+), \S+, from '(?P<name>.*)':\r?\n?$")
    out = re.compile(
        r"(?P<type>Out)put #(?P<num>\d+), \S+, to '(?P<name>.*)':\r?\n?$")

    def __init__(self, type, num, name):
        self.type = type
        self.num = num
        self.name = name

    def is_pipe(self):
        return self.name == 'pipe:'

    def parse_streams(self, preit):
        self.streams = list(
            filter(None, map(Stream.parse, BlockIter(preit))))

    @staticmethod
    def parse(preit):
        for line in preit:
            m = IO.inp.match(line)
            if not m:
                m = IO.out.match(line)
            if not m:
                preit.push(line)
                return None
            else:
                return IO(
                    m.group('type'), int(m.group('num')),
                    m.group('name'))
