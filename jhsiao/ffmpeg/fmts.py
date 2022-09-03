"""ffmpeg format info
"""
__all__ = ['FormatInfo']
import re
import io
import subprocess as sp

from ..utils.devnull import DevNull as nul
from .holder import Holder


class PixFmtGuesser(object):
    """Guess bits for each component.

    Some ffmpegs don't provide this field when called with -pix_fmts.
    """
    ENDIAN = re.compile(r'(?P<prefix>.*[^\d])(?P<num>\d+)(?P<endian>[lb]e)$')
    ENDNUM = re.compile(r'(?P<prefix>.*[^\d])(?P<num>\d+)$')

    YUV = set('yuvajp4210')
    BGR = set('bgra0p')
    @classmethod
    def update(cls, name, parsed, info):
        h = Holder()
        if info:
            parsed['bitdepths'] = tuple(map(int, info[0].split('-')))
            if h(cls.ENDIAN.match(name)):
                parsed['endian'] = h.r.group('endian')
            return
        components = parsed['components']
        pixbits = parsed['pixbits']
        if h(cls.ENDIAN.match(name)):
            snum, endian, prefix = map(h.r.group, ('num', 'endian', 'prefix'))
            num = int(snum)
            parsed['endian'] = endian
            if (
                    prefix.startswith('bayer')
                    and components == 3 and num and not num%4):
                fourth = num//4
                parsed['bitdepths'] = (fourth, num//2, fourth)
            elif num == pixbits and num and not num%components:
                parsed['bitdepths'] = (num//components,) * components
            elif prefix == 'nv' and num and not num%2:
                parsed['bitdepths'] = (num//2,)*components
            elif prefix == 'p' or prefix == 'y':
                parsed['bitdepths'] = (num%100,)*components
            elif num < 100:
                parsed['bitdepths'] = (num,)*components
            elif len(snum) == components:
                parsed['bitdepths'] = tuple(map(int, snum))
        elif h(cls.ENDNUM.match(name)):
            prefix, snum = map(h.r.group, ('prefix', 'num'))
            num = int(snum)
            if (
                    prefix.startswith('bayer')
                    and components == 3 and num and not num%4):
                fourth = num//4
                parsed['bitdepths'] = (fourth, num//2, fourth)
            elif cls.BGR.issuperset(prefix) and num and not num%components:
                parsed['bitdepths'] = (num//components,)*components
            elif (
                    cls.YUV.issuperset(prefix)
                    or prefix in ('nv', 'pal', 'ya')
                    or (cls.BGR.issuperset(prefix) and num == 0)):
                parsed['bitdepths'] = (8,)*components
        else:
            if (
                    cls.BGR.issuperset(name)
                    or name=='gray'
                    or cls.YUV.issuperset(name)):
                parsed['bitdepths'] = (8,)*components

class FormatInfo(object):
    __cache = {}
    def __init__(self, flag):
        """Initialize format info.

        flag: The flag to pass to ffmpeg to list formats.
            This is generally -pix_fmts or -formats.
        """
        self.flag = flag
        self.infoparser = getattr(self, 'parse_{}'.format(flag.strip('-')))
        self._formats, self.flags = FormatInfo.__cache.setdefault(
            flag, ({}, {}))

    @property
    def formats(self):
        """Get the actual info."""
        if self._formats:
            return self._formats
        p = sp.Popen(
            ['ffmpeg', self.flag], stderr=nul(), stdin=nul(), stdout=sp.PIPE)
        h = Holder()
        f = io.TextIOWrapper(p.stdout)
        try:
            pattern, flags = self.parse_flags(f)
            self.flags.update(flags)
            for line in f:
                line = line.rstrip()
                match = pattern.match(line)
                try:
                    info = dict(flags=match.group('flags'))
                except AttributeError:
                    print(pattern.pattern)
                    print('bad line:', repr(line))
                else:
                    name = match.group('name')
                    self.infoparser(name, info, match.group('info'))
                    self._formats[name] = info
        finally:
            f.detach()
            p.communicate()
        return self._formats

    def __len__(self):
        return len(self.formats)

    def __contains__(self, thing):
        return thing in self.formats

    def __iter__(self):
        return iter(self.formats)

    def __getitem__(self, k):
        return self.formats[k]

    spaces=re.compile(r'\s+')
    flagdesc = re.compile('(?P<flags>[.A-Z]+) = (?P<description>.*)')
    @classmethod
    def parse_pix_fmts(cls, name, parsed, info):
        info = cls.spaces.split(info)
        parsed.update(
            zip(('components', 'pixbits'), map(int, info[:2])))
        PixFmtGuesser.update(name, parsed, info[2:])
        return parsed

    @staticmethod
    def parse_formats(name, parsed, info):
        parsed['info'] = info
        return parsed

    @classmethod
    def parse_flags(cls, f):
        """Parse the header flag definition info."""
        h = Holder()
        flags = {}
        order = []
        for line in f:
            line = line.strip()
            if h(cls.flagdesc.match(line)):
                match = h.r
                if not order:
                    order = [None] * len(match.group('flags'))
                flag = match.group('flags').strip('.')
                pos = match.group('flags').index(flag)
                order[pos] = flag
                flags[flag] = dict(position=pos, description=match.group('description'))
            elif line == '-'*len(order):
                break
        chunks = [r'\s*(?P<flags>']
        chunks.extend(map('[{}. ]'.format, order))
        chunks.append(r')\s+(?P<name>[\w,]+)\s+(?P<info>.*)$')
        return re.compile(''.join(chunks)), flags

if __name__ == '__main__':
    pixfmts = (
        'Pixel formats:\n'
        'I.... = Supported Input  format for conversion\n'
        '.O... = Supported Output format for conversion\n'
        '..H.. = Hardware accelerated format\n'
        '...P. = Paletted format\n'
        '....B = Bitstream format\n'
        'FLAGS NAME            NB_COMPONENTS BITS_PER_PIXEL BIT_DEPTHS\n'
        '-----\n'
        'IO... yuv420p                3             12      8-8-8\n'
        'IO... yuyv422                3             16      8-8-8\n')
    formats = (
        'File formats:\n'
        ' D. = Demuxing supported\n'
        ' .E = Muxing supported\n'
        ' --\n'
        ' D  3dostr          3DO STR\n'
        '  E 3g2             3GP2 (3GPP2 file format)\n'
        '  E 3gp             3GP (3GPP file format)\n'
        ' D  4xm             4X Technologies\n'
        '  E a64             a64 - video for Commodore 64\n'
        ' D  aa              Audible AA format files\n')

    print(len(FormatInfo('-pix_fmts')))
    print(FormatInfo('-pix_fmts').flags)

    print(len(FormatInfo('-formats')))
    print(FormatInfo('-formats').flags)

    print('h264', FormatInfo('-formats')['h264'])
    print('bgra', FormatInfo('-pix_fmts')['bgra'])
