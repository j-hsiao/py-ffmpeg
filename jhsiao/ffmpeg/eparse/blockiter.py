__all__ = ['BlockIter']
import re

indented = re.compile('^\s+')

class BlockIter(object):
    """Iterate on lines and following indented lines."""
    def __init__(self, preit):
        """Initialize a block iter.

        preit: PreIt
            PreIt iterating over lines of text.
        """
        self.preit = preit

    def __iter__(self):
        preit = self.preit
        for line in preit:
            yield line
            for line in preit:
                if indented.match(line):
                    yield line
                else:
                    preit.push(line)
                    return

if __name__ == '__main__':
    import io
    from jhsiao.ffmpeg.preit import PreIt
    data = io.StringIO('hello world\n\tgoodbye\n\tworld\nnextblock\n')
    pre = PreIt(data)
    block = list(BlockIter(pre))
    assert len(block) == 3
    assert block == ['hello world\n', '\tgoodbye\n', '\tworld\n']
    block = list(BlockIter(pre))
    assert len(block) == 1
    assert block == ['nextblock\n']
    block = list(BlockIter(pre))
    assert len(block) == 0
    assert block == []
