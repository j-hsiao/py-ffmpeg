import re

indented = re.compile('^\s+')

class BlockIter(object):
    """Iterate on lines and following indented blocks."""
    def __init__(self, preit):
        """Initialize a block iter.

        preit: PreIt
            PreIt iterating over lines of text.
        """
        self.preit = preit

    def __iter__(self):
        preit = self.preit
        for line in preit:
            lines = [line]
            for line in preit:
                if indented.match(line):
                    lines.append(line)
                else:
                    preit.push(line)
                    break
            yield lines

if __name__ == '__main__':
    import io
    from jhsiao.ffmpeg.preit import PreIt
    data = io.StringIO('hello world\n\tgoodbye\n\tworld\nnextblock\n')
    blocks = list(BlockIter(PreIt(data)))
    assert len(blocks) == 2
    assert len(blocks[0]) == 3
    assert len(blocks[1]) == 1
    for block in blocks:
        print('------------------------------')
        for line in block:
            print(line.rstrip())
