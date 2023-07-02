"""Parse information from ffmpeg listings.

ffmpeg -codecs
ffmpeg -pix_fmts
ffmpeg -formats
"""

# example ffmpeg outputs:
#Codecs:
# D..... = Decoding supported
# .E.... = Encoding supported
# ..V... = Video codec
# ..A... = Audio codec
# ..S... = Subtitle codec
# ...I.. = Intra frame-only codec
# ....L. = Lossy compression
# .....S = Lossless compression
# -------
# D.VI.S 012v                 Uncompressed 4:2:2 10-bit
# D.V.L. 4xm                  4X Movie
# D.VI.S 8bps                 QuickTime 8BPS video
# .EVIL. a64_multi            Multicolor charset for Commodore 64 (encoders: a64multi )
# .EVIL. a64_multi5           Multicolor charset for Commodore 64, extended with 5th color (colram) (encoders: a64multi5 )
# D.V..S aasc                 Autodesk RLE
# D.V.L. agm                  Amuse Graphics Movie
# D.VIL. aic                  Apple Intermediate Codec
# DEVI.S alias_pix            Alias/Wavefront PIX image
# DEVIL. amv                  AMV Video
#
#
#
#Pixel formats:
#I.... = Supported Input  format for conversion
#.O... = Supported Output format for conversion
#..H.. = Hardware accelerated format
#...P. = Paletted format
#....B = Bitstream format
#FLAGS NAME            NB_COMPONENTS BITS_PER_PIXEL
#-----
#IO... yuv420p                3            12
#IO... yuyv422                3            16
#
#
#
#File formats:
# D. = Demuxing supported
# .E = Muxing supported
# --
# D  3dostr          3DO STR
#  E 3g2             3GP2 (3GPP2 file format)
#  E 3gp             3GP (3GPP file format)
# D  4xm             4X Technologies
#  E a64             a64 - video for Commodore 64
# D  aa              Audible AA format files
#

import re
import subprocess as sp

from .preit import PreIt


class Header(object):
    pattern = re.compile(r'(?P<indent>\s*)(?P<flags>[A-Z. ]+) = (?P<desc>.*)')
    def __init__(self, it):
        """Initialize a header.

        it: PreIt
            Iterator over lines.
        """
        headers = []
        for line in it:
            match = self.pattern.match(line)
            if match:
                headers.append(match.groupdict())
            else:
                it.pre.append(line)
                break
        indents = set([d['indent'] for d in headers])
        self.indent = min(indents, key=len)
        if len(indents) > 1:
            for h in headers:
                h['flags'] = h['indent'][len(self.indent):] + h['flags']
        for h in headers:
            if len(h['flags']) != len(headers[0]['flags']):
                raise ValueError(
                    'mismatched flag lengths: {} vs {}'.format(
                        repr(h['flags']), repr(headers[0]['flags'])))

        for h in headers:
            del h['indent']
            idx = None
            for i, char in enumerate(h['flags']):
                if char not in '. ':
                    if idx is None:
                        idx = i
                    else:
                        raise ValueError('bad flags {}'.format(h['flags']))
            if idx is None:
                raise ValueError('bad flags {}'.format(h['flags']))
            h['idx'] = idx + len(self.indent)
            h['char'] = h['flags'][idx]
        self.headers = headers

        p = [self.indent, '(?P<flags>']
        for h in self.headers:
            p.append('[ .{}]'.format(h['char']))

        p.append(r')\s+(?P<name>\S+)\s+(?P<desc>.*)')
        self.isline = re.compile(''.join(p))
        # TODO: iterate on lines until only indent----

    def __repr__(self):
        lines = ['headers:']
        for h in self.headers:
            lines.append(
                ''.join(
                    (self.indent, h['flags'], ' = ', h['desc'],
                    ' (', str(h['idx']), ')')))
        return '\n'.join(lines)




class Info(object):

    def __init__(self, flag):
        p = sp.Popen(['ffmpeg', flag], stderr=sp.STDOUT, stdout=sp.PIPE)
        stdo, _ = p.communicate()
        self.it = PreIt(stdo.decode('utf-8').splitlines())

        self.headers = self._get_header()

    def _get_header(self):
        it = self.it
        for line in it:
            if Header.pattern.match(line):
                return Header(it.push(line))

    def __getitem__(self, name):
        pass



if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('flag', default='-pix_fmts', nargs='?')
    print(Info(p.parse_args().flag.strip()).headers)
