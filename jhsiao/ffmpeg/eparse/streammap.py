__all__ = ['StreamMap']
import itertools
import re

class StreamMap(object):
    pattern = re.compile(
        r'\s+Stream #(?P<iname>\d+:\d+).*\s+->\s+#(?P<oname>\d+:\d+)')

    def __init__(self, mappings):
        self.mappings = mappings

    @staticmethod
    def parse(block):
        """Parse a Stream mapping block."""
        if not block[0].rstrip().endswith('Stream mapping:'):
            return None
        mappings = list(filter(None, [
            StreamMap.pattern.match(line)
            for line in itertools.islice(block, 1, None)]))
        return StreamMap(
            [(m.group('iname'), m.group('oname')) for m in mappings])


    def __iter__(self):
        return iter(self.mappings)

    def __len__(self):
        return len(self.mappings)

    def __getitem__(self, idx):
        return self.mappings[idx]

    def __repr__(self):
        chunks = ['Stream mapping:']
        chunks.extend(
            ['\n\t#{} -> #{}'.format(*t) for t in self.mappings])
        return ''.join(chunks)
