__all__ = ['FFmpegEParser']
import sys

from ..preit import PreIt
from .blockiter import BlockIter
from .io import IO
from .streammap import StreamMap

class FFmpegEParser(object):
    """Parse ffmpeg stderr for info on streams."""
    def __init__(self, lines, verbose=False):
        it = PreIt(lines)
        self.streammap = None
        self.ins = {}
        self.outs = {}
        istreams = set()
        ostreams = set()
        itargets = set()
        otargets = set()
        while (self.streammap is None or
                not (istreams.issuperset(itargets)
                    and ostreams.issuperset(otargets))):

            block = list(BlockIter(it))
            if verbose:
                sys.stderr.writelines(block)
            io = IO.parse(block)
            if io:
                if io.type == io.TYPE_IN:
                    self.ins[io.num] = io
                    istreams.update(io)
                else:
                    self.outs[io.num] = io
                    ostreams.update(io)
            else:
                mp = StreamMap.parse(block)
                if mp:
                    self.streammap = mp
                    itargets.update([i for i,o in mp])
                    otargets.update([o for i, o in mp])
