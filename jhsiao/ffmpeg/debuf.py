"""Use threading to continually grab frames.

Frames are generally buffered which may result in higher latency since
older frames are kept in the buffer.
"""
import time
import threading
from .lazyimport import cv2

class Debuffer(object):
    def __init__(self, capture, slowgrab=0.01, resync=10):
        self.resync = resync
        self.cap = capture
        self.cond = threading.Condition()
        self.slow = slowgrab
        self._updated = False
        self._running = True
        self.t = threading.Thread(target=self._grabloop)
        self.t.start()

    def _guess_fps(self):
        cap = self.cap
        try:
            return cap.stream.fps
        except AttributeError:
            try:
                fps = cap.get(cv2.CAP_PROP_FPS)
            except Exception:
                pass
            else:
                if fps > 0:
                    return fps
        return None

    def _grabloop(self):
        """Try to minimize time with lock held."""
        resync = self.resync
        cap = self.cap
        cond = self.cond
        slow = self.slow
        sleep = time.sleep
        tm = time.time
        def grab():
            """Grab a frame.

            Return begintime, endtime, and okay.
            """
            with cond:
                cond.notify()
                if not self._running:
                    return None, None, False
                begin = tm()
                self._updated = cap.grab()
                end = tm()
                if not self._updated:
                    self._running = False
                return begin, end, self._updated
        fps = self._guess_fps()
        # Remove prebuffered frames, assume fps < 100.
        okay = True
        grabtime = 0
        while grabtime < slow and okay:
            begin, end, okay = grab()
            grabtime = end-begin
        if not okay:
            return
        if fps is None:
            begin = end
            _, end, okay = grab()
            period = end-begin
            fps = 1/period
        else:
            period = 1/fps
        totalgrabs = 0
        anchor = end
        while okay:
            begin, end, okay = grab()
            totalgrabs += 1
            totaltime = end-anchor
            if end-begin > slow:
                fps = totalgrabs / totaltime
                anchor = end
                period = 1/fps
                print('resynced', fps)
                totalgrabs = 0
                sleep(period)
            else:
                expectedgrabs = int(totaltime*fps)
                if totaltime < resync and 0 <= expectedgrabs - totalgrabs <= 2:
                    sleep(period)

    def ready(self):
        return self._updated or not self._running

    def read(self, frame=None):
        cond = self.cond
        with cond:
            if (self._updated or not self._running
                or cond.wait_for(self.ready)):
                if self._updated:
                    s, f = self.cap.retrieve(frame)
                    self._updated = False
                    return s, f
                else:
                    return False, None

    def close(self):
        self.detach().close()

    def detach(self):
        if self.t is not None:
            with self.cond:
                self._running = False
            self.t.join()
            self.t = None
        cap = self.cap
        self.cap = None
        return cap

if __name__ == '__main__':
    import argparse
    from jhsiao.ffmpeg.ffmpeg import FFmpegReader
    p = argparse.ArgumentParser()
    p.add_argument('vid', help='vid to play')
    p.add_argument('-v', '--verbose', action='store_true')
    args = p.parse_args()
    cap = FFmpegReader(
        ['ffmpeg', '-re', '-i', args.vid, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'],
        verbose=args.verbose)

    ncap = Debuffer(cap)

    s, f = ncap.read()
    while s:
        cv2.imshow('f', f)
        s, f = ncap.read()
        switch = cv2.waitKey(1)
        if switch == ord('q'):
            s = False
    ncap.close()
