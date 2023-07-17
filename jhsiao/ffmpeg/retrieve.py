__all__ = ['Retriever', 'frameinfo']
import itertools
from .lazyimport import cv2, np

class FrameRetriever(object):
    """Retrieve frame"""
    CODENAMES = {
        'yuv420p': (
            'YUV2BGR_I420', 'YUV2BGR_IYUV',
            'YUV420P2RGB', 'YUV420p2RGB', 'YUV2RGB_YV12'),
        'nv12': ('YUV2BGR_NV12',),
        'nv21': ('YUV2BGR_NV21', 'YUV420SP2BGR', 'YUV420sp2BGR'),
        'yuv422p': ('YUV2BGR_YUNV', 'YUV2BGR_YUY2', 'YUV2BGR_YUYV'),
        'uyvy422': ('YUV2BGR_UYNV', 'YUV2BGR_UYVY', 'YUV2BGR_Y422'),
        'yvyu422': ('YUV2BGR_YVYU',),
        'yuv444p': ('YUV2BGR',)
    }

    def __init__(self, pix_fmt, width , height):
        """Initialize retriever

        pix_fmt: The pixel format dict from `info.PixFmts`
        """
        self.rawbuf = np.empty(
            *self.frameinfo(pix_fmt, width, height))
        try:
            self.cvt = getattr(self, '_' + pix_fmt['name'])
        except AttributeError:
            raise ValueError('Unsupported pixel format conversion: {}'.format(
                pix_fmt['name']))

    def _bgr24(self, out=None):
        if out is None:
            return True, self.rawbuf
        else:
            out[...] = self.rawbuf
            return True, out

    def _rgb24(self, out=None):
        if out is None:
            return True, self.rawbuf[...,::-1].copy()
        else:
            out[...] = self.rawbuf[...,::-1]
            return True, out

    def _yuv444p(self, out=None):
        return True, cv2.cvtColor(
            self.rawbuf.transpose(1,2,0), cv2.COLOR_YUV2BGR, out)
    _yuvj444p = _yuv444p

    def _yuv420p(self, out=None):
        return True, cv2.cvtColor(self.rawbuf, cv2.COLOR_YUV2BGR_I420, out)
    _yuvj420p = _yuv420p

    def _nv12(self, out=None):
        return True, cv2.cvtColor(self.rawbuf, cv2.COLOR_YUV2BGR_NV12)

    def _nv21(self, out=None):
        return True, cv2.cvtColor(self.rawbuf, cv2.COLOR_YUV2BGR_NV21)

    def _yuv422p(self, out=None):
        tmpbuf = np.stack(
            (self.rawbuf[0], self.rawbuf[1].reshape(2, -1).T.reshape(self.rawbuf.shape[1:])),
            axis=2)
        return True, cv2.cvtColor(tmpbuf, cv2.COLOR_YUV2BGR_YUYV)

    def _yuyv422(self, out=None):
        return True, cv2.cvtColor(self.rawbuf, cv2.COLOR_YUV2BGR_YUYV)

    def _uyvy422(self, out=None):
        return True, cv2.cvtColor(self.rawbuf, cv2.COLOR_YUV2BGR_UYNV)

    def _yvyu422(self, out=None):
        return True, cv2.cvtColor(self.rawbuf, cv2.COLOR_YUV2BGR_YVYU)


    @staticmethod
    def frameinfo(pix_fmt, width, height):
        """Return numpy array buffer to hold a frame of pix_fmt."""
        name = pix_fmt['name']
        if name in ('bgr24', 'rgb24'):
            return (height, width, 3), np.uint8
        if name in ('yuv444p', 'yuvj444p'):
            return (3, height, width), np.uint8
        if name == 'yuv422p':
            return (2, height, width), np.uint8
        if name in ('yuyv422', 'uyvy422', 'yvyu422'):
            return (height, width, 2), np.uint8
        if name in ('yuv420p', 'nv12', 'yuvj420p'):
            return (int(height * 1.5), width), np.uint8


        dtypes = {
            8: np.uint8,
            16: np.uint16,
            32: np.uint32,
            64: np.uint64,
        }
        bppx = pix_fmt['fields']['BITS_PER_PIXEL']
        nchan = pix_fmt['fields']['NB_COMPONENTS']
        if bppx % nchan == 0:
            if pix_fmt['name'] == 'yuv444p':
                shape = (nchan, height, width)
            else:
                shape = (height, width, nchan)
            tp = dtypes.get(bppx / nchan)
            if tp is not None:
                return shape, tp
        totalbits = bppx * height * width
        if height % 2 == 0:
            shape = (height + height//2, width)
            npix = shape[0] * shape[1]
            if totalbits % npix == 0:
                tp = dtypes.get(totalbits // npix)
                if tp is not None:
                    return shape, tp
        if nchan == 3 and bppx == 16:
            if 'bayer' in pix_fmt['name']:
                pass
            else:
                return (2, height, width), np.uint8
        if totalbits % 8 == 0:
            return totalbits // 8, np.uint8
        raise ValueError(
            'Unsupported Pixel format {} with shape {}x{}'.format(
                pix_fmt['name'], width, height))

def _findcode(names):
    """Lazy import cv2 and numpy and find conversion code."""
    if not names:
        return
    for name in names:
        code = getattr(cv2, 'COLOR_'+name, None)
        if code is not None:
            return code
    else:
        raise ValueError('cv2 is missing names {}'.format(names))
class Retriever(object):
    """
    """
    # general observations:
    # yuv = planar
    # yuyv = interleaved
    CODENAMES = {
        'yuv420p': (
            'YUV2BGR_I420', 'YUV2BGR_IYUV',
            'YUV420P2RGB', 'YUV420p2RGB', 'YUV2RGB_YV12'),
        'nv12': ('YUV2BGR_NV12',),
        'nv21': ('YUV2BGR_NV21', 'YUV420SP2BGR', 'YUV420sp2BGR'),
        'yuv422p': ('YUV2BGR_YUNV', 'YUV2BGR_YUY2', 'YUV2BGR_YUYV'),
        'uyvy422': ('YUV2BGR_UYNV', 'YUV2BGR_UYVY', 'YUV2BGR_Y422'),
        'yvyu422': ('YUV2BGR_YVYU',),
        'yuv444p': ('YUV2BGR',)
    }
    SAMECODE = {
        'yuvj420p': 'yuv420p',
        'yuyv422': 'yuv422p',
        'yuvj444p': 'yuv444p'
    }
    SAMEFUNC = {
        'yuyv422': 'yuv420p',
        'yvyu422': 'yuv420p',
        'uyvy422': 'yuv420p',
        'yuvj420p': 'yuv420p',
        'nv12': 'yuv420p',
        'nv21': 'yuv420p',
        'yuvj444p': 'yuv444p'
    }
    _cache = {}
    def __init__(self, fmt):
        codename = self.SAMECODE.get(fmt, fmt)
        funcname = self.SAMEFUNC.get(fmt, fmt)
        try:
            self.retrieve = self._cache[codename]
        except KeyError:
            names = self.CODENAMES.get(codename)
            code = _findcode(names)
            creator = getattr(self, funcname, None)
            if creator is None:
                self._cache[codename] = self.retrieve = None
            else:
                self._cache[codename] = self.retrieve = creator(code)


    @staticmethod
    def yuv444p(code):
        """Channels first, channels same size."""
        cvt = cv2.cvtColor
        moveaxis = np.moveaxis
        def _yuv444p(data, frame=None):
            """ffpmeg YUV444 is CHW format, opencv needs HWC."""
            return cvt(moveaxis(data, 0, 2), code, frame)
        return _yuv444p

    @staticmethod
    def yuv422p(code):
        """ffmpeg yuv422p is semi-chw.  Need to fix ordering for cv2."""
        cvt = cv2.cvtColor
        moveaxis = np.moveaxis
        stack = np.stack
        def _yuv422p(data, frame=None):
            tmp = moveaxis(
                data[1].reshape(2, -1), 0, 1)
            return cvt(stack(
                (data[0], tmp.reshape(data.shape[1:])), axis=2), code, frame)
        return _yuv422p

    @staticmethod
    def yuv420p(code):
        cvt = cv2.cvtColor
        def _yuv420p(data, frame=None):
            return cvt(data, code, frame)
        return _yuv420p

    @staticmethod
    def rgb24(code):
        def _rgb24(data, frame=None):
            rev = data[...,::-1]
            if frame is None:
                return rev.copy()
            else:
                frame[...] = rev
                return frame
        return _rgb24



if __name__ == '__main__':
    import numpy as np
    import cv2
    import argparse
    from jhsiao.ffmpeg import ffmpeg
    def showbuf(buf):
        if buf.ndim == 2:
            scale = 800 / buf.shape[0]
            cv2.imshow('raw', cv2.resize(buf, (0,0), fx=scale, fy=scale))
            return
        elif buf.ndim == 3:
            channels = min(buf.shape)
            if channels <= 4:
                show = np.moveaxis(buf, buf.shape.index(channels), 0)
                for i in range(channels):
                    cv2.imshow(str(i), show[i])
                return
        print('unknown shape', buf.shape)

    p = argparse.ArgumentParser()
    p.add_argument('vid', help='path to vid to grab a frame', nargs='?')
    p.add_argument('-f', help='full ffmpeg command', nargs='...')
    p.add_argument('-v', '--verbose', action='store_true')
    p.add_argument('-p', '--pixfmt', default='yuv420p', help='pixel format')
    args = p.parse_args()
    if args.f:
        command = args.f
    else:
        command = 'ffmpeg -i "{}" -f rawvideo -pix_fmt {} -'.format(
            args.vid, args.pixfmt)
    with ffmpeg.FFmpegReader(command, verbose=args.verbose) as reader:
        data = reader.dbuf
        print('cap shape:', reader.shape)
        print('read shape:', reader.buf.shape)
        print('decode shape:', reader.dbuf.shape)
        running = 1
        while running:
            if reader.grab():
                r = Retriever(args.pixfmt)
                if r.retrieve:
                    s, f = r.retrieve(data)
                    print('output shape', f.shape)
                    if s:
                        cv2.imshow('frame', f)
                    else:
                        print('retrieve failed')
                        showbuf(data)
                else:
                    cv2.imshow('frame', data)
            else:
                print('grab failed')
                showbuf(data)
                r = Retriever(args.pixfmt)
                if r.retrieve:
                    s, f = r.retrieve(data)
                    if s:
                        cv2.imshow('retrieve bad grab', f)
                        print(f.shape)
            if cv2.waitKey(0) & 0xFF == ord('q'):
                running = 0
