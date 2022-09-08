__all__ = ['Retriever']
import itertools
from .lazyimport import cv2, np

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
