__all__ = ['Retriever']
import itertools

def _findcode(names):
    """Lazy import cv2 and numpy."""
    if not names:
        return
    try:
        for name in names:
            code = getattr(cv2, 'COLOR_'+name, None)
            if code is not None:
                return code
        else:
            raise ValueError('cv2 is missing names {}'.format(names))
    except (NameError, UnboundLocalError):
        import cv2 as ocv2
        import numpy
        g = globals()
        g['cv2'] = ocv2
        g['np'] = numpy
        return _findcode(names)
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
        'yvyu422': 'yuyv422',
        'uyvy422': 'yuyv422',
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
            self._cache[codename] = self.retrieve = getattr(
                self, funcname)(code)


    @staticmethod
    def yuv444p(code):
        cvt = cv2.cvtColor
        moveaxis = np.moveaxis
        def _yuv444p(data):
            """ffpmeg YUV444 is CHW format, opencv needs HWC."""
            return cvt(moveaxis(data, 0, 2), code)
        return _yuv444p

    @staticmethod
    def yuv422p(code):
        """ffmpeg yuv422p is semi-chw.  Need to fix ordering for cv2."""
        cvt = cv2.cvtColor
        moveaxis = np.moveaxis
        stack = np.stack
        def _yuv422p(data):
            tmp = moveaxis(
                data[1].reshape(2, -1), 0, 1)
            return cvt(stack(
                (data[0], tmp.reshape(data.shape[1:])), axis=2), code)
        return _yuv422p

    @staticmethod
    def yuyv422(code):
        """Interleaved."""
        cvt = cv2.cvtColor
        def _yuyv422(data):
            return cvt(data, code)
        return _yuyv422


    @staticmethod
    def yuv420p(code):
        cvt = cv2.cvtColor
        def _yuv420p(data):
            return cvt(data, code)
        return _yuv420p


    @staticmethod
    def bgr24():
        def _bgr24(data):
            return data

    @staticmethod
    def rgb24():
        def _rgb24(data):
            return data[...,::-1]
        return _rgb24

if __name__ == '__main__':
    import numpy as np
    import cv2
    import argparse
    from jhsiao.ffmpeg import ffmpeg
    p = argparse.ArgumentParser()
    p.add_argument('vid', help='path to vid to grab a frame')
    p.add_argument('-v', '--verbose', action='store_true')
    p.add_argument('pixfmt', nargs='?', default='yuv420p', help='pixel format')
    args = p.parse_args()

    with ffmpeg.FFmpegReader(
            'ffmpeg -i "{}" -f rawvideo -pix_fmt {} -'.format(
                args.vid, args.pixfmt),
            verbose=args.verbose) as reader:
        succ, data = reader.grab()
        r = Retriever(args.pixfmt)
        cv2.imshow('frame', r.retrieve(data))
        cv2.waitKey(0)
        succ, data = reader.grab()
