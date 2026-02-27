__all__ = ['IO']
import itertools
import re

from .stream import Stream
from .blockiter import BlockIter

class IO(object):
    TYPE_IN = 'In'
    TYPE_OUT = 'Out'
    patterns = (
        re.compile(
            r"(?:.*\r|^)(?P<type>In)put #(?P<num>\d+), \S+, from '(?P<name>.*)':\r?\n?$"),
        re.compile(
            r"(?:.*\r|^)(?P<type>Out)put #(?P<num>\d+), \S+, to '(?P<name>.*)':\r?\n?$"),
    )

    def __init__(self, type, num, name, streams):
        self.type = type
        self.num = int(num)
        self.name = name
        self.streams = {s.name: s for s in streams}

    def is_pipe(self):
        return self.name == 'pipe:'

    def __iter__(self):
        return iter(self.streams)

    def items(self):
        return self.streams.items()

    def __getitem__(self, key):
        """Get stream by name(str) or index(int).

        The name includes the IO num and is what appears in the
        stream mapping block.  An index will be joined to the IO num
        with ':' and the result used as the stream name.
        """
        if isinstance(key, int):
            key = ':'.join((str(self.num), str(key)))
        return self.streams[key]

    def __len__(self):
        return len(self.streams)

    def __repr__(self):
        chunks = ["{}put #{} '{}'".format(self.type, self.num, self.name)]
        chunks.extend([str(self[i]) for i in range(len(self))])
        return '\n\t'.join(chunks)

    @staticmethod
    def parse(block):
        """Parse an Input/Output block.

        block: sequence of str
            Constituent lines of the block. non-empty
        """
        for p in IO.patterns:
            m = p.match(block[0])
            if m:
                break
        else:
            return None
        streams = list(filter(
            None, map(Stream.parse, itertools.islice(block, 1, None))))
        return IO(
            m.group('type'), m.group('num'), m.group('name'),
            streams)
