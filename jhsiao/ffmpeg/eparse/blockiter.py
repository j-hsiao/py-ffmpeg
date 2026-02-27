__all__ = ['BlockIter']
import re

indented = re.compile('^\s+')

class BlockIter(object):
    """Iterate on lines and following indented lines."""
    def __init__(self, it):
        """Initialize a block iter.

        it: RewindIt
            RewindIt iterating over lines of text.
        """
        self.it = it

    def __iter__(self):
        it = self.it
        for line in it:
            yield line
            for line in it:
                if indented.match(line):
                    yield line
                else:
                    it.rewind(1)
                    return

if __name__ == '__main__':
    import io
    from jhsiao.ffmpeg.its import RewindIt
    data = io.StringIO('hello world\n\tgoodbye\n\tworld\nnextblock\n')
    pre = RewindIt(data)
    block = list(BlockIter(pre))
    assert len(block) == 3
    assert block == ['hello world\n', '\tgoodbye\n', '\tworld\n']
    block = list(BlockIter(pre))
    assert len(block) == 1
    assert block == ['nextblock\n']
    block = list(BlockIter(pre))
    assert len(block) == 0
    assert block == []
