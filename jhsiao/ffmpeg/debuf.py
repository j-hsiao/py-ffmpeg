"""Use threading to continually grab frames.

Frames are generally buffered which may result in higher latency since
older frames are kept in the buffer.
"""
import time
import threading
from .lazyimport import cv2

class Debuffer(object):
    """Debuffer opens a thread to continually grab frames.

    The ideal state to maintain is 1 buffered frame.  However, there is
    no access to the buffer.  As a result, the best you can do is use
    the time required to grab a frame as indication of whether the
    buffer is empty or not.  Furthermore, from testing, grabbing at
    exactly the frame rate consistently results in an effective
    grabbing speed lower than the framerate which causes the buffer to
    build up.  However, note that grabtime can also be influenced by
    the reader trying to acquire the lock.

    The grabbing keeps the buffer empty so frames are up-to-date.
    It aims to grab at fps rate and uses sleep to minimize
    lock-time.
    """
    def __init__(
        self, cap, resync=10, samplesize=5, error=0.10, force=10):
        """Initialize a Debuffer object.

        cap: The video reader.  It should support grab and retrieve.
        resync: Resync period in seconds.  If the detected fps differs
            from the calculated one (maybe one of the calculations was
            inaccurate or some other issue), then re-clear buffer and
            or recalculate the fps.  If the current fps is still similar
            to the last calculated fps, do nothing.
        force: Every forceth resync will be forced (buffer forcibly
            recleared). force <= 0 means never force
        error: If effective fps differs from sampled fps by more than
            error, 
        """
        self.cap = cap
        self.cond = threading.Condition()
        self._updated = False
        self._running = True

        self.resync = resync
        self.samplesize = samplesize
        self.error = error
        self.force = float('inf') if force<=0 else force
        self.t = threading.Thread(target=self._grabloop)
        self.t.start()

    def _parse_fps(self):
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

    def _grab(self, cond, cap):
        """Grab a frame and return okay."""
        with cond:
            cond.notify()
            if not self._running:
                return False
            ret = self._updated = cap.grab()
            return ret

    def _sample_fps(self, cond, cap, start):
        """Grab frames as fast as possible to calculate fps."""
        # clear buffer before sampling
        grab = self._grab
        for i in range(self.samplesize):
            if not grab(cond, cap):
                return False, None, None
        finish = time.time()
        return True, self.samplesize / (finish - start), finish

    def _clear_buffer(self, cond, cap, start, fps):
        """Clear buffer by sampling until sampled fps == fps."""
        okay, sampledfps, end = self._sample_fps(cond, cap, start)
        while okay and abs((sampledfps/fps)-1) > self.error:
            okay, sampledfps, end = self._sample_fps(cond, cap, end)
        return okay, end

    def _grabloop(self):
        """Ensure _running is cleared on exit."""
        try:
            self.__grabloop()
        finally:
            with self.cond:
                self._running = False

    def __grabloop(self):
        """Try to minimize time with lock held.

        Occasionally sample fps via max-rate grabbing.
        """
        cond = self.cond
        cap = self.cap
        grab = self._grab
        parsedfps = self._parse_fps()
        if parsedfps is not None:
            print('parsed fps:', parsedfps)
            fps = parsedfps
            okay, end = self._clear_buffer(cond, cap, time.time(), parsedfps)
        else:
            okay, fps, end = self._sample_fps(cond, cap, start)
            print('initial fps:', fps)
        if not okay:
            return
        anchor = end
        check = end + self.resync
        period = 1/fps
        total = 0
        resyncs = 0
        gtotal = 0
        gstart = time.time()
        okay = grab(cond, cap)
        target = time.time() + period
        while okay:
            end = time.time()
            gtime = end-gstart
            gtotal += gtime
            total += 1
            if end > check:
                resyncs += 1
                effectivefps = total / (end-anchor)
                print('effective fps:', effectivefps)
                if abs((effectivefps / fps)-1) > self.error or resyncs>=self.force:
                    print('recalibrate')
                    if parsedfps is not None:
                        okay, end = self._clear_buffer(cond, cap, end, parsedfps)
                    else:
                        okay, fps, end = self._sample_fps(cond, cap, start)
                        period = 1/fps
                        print('new sampled fps:', fps)
                    if not okay:
                        return
                    target = end+period
                    resyncs = 0
                else:
                    gaverage = gtotal/total
                    print('avg grab duration:', gaverage)
                gtotal = 0
                check = end+self.resync
                anchor = end
                total = 0
            if target>end:
                time.sleep(target-end)
            else:
                if gtime > period*0.5:
                    print('target before now but buffer is empty')
                    target = time.time()
                else:
                    print('behind schedule')
            target += period
            gstart = time.time()
            okay = grab(cond, cap)

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
        cap = self.detach()
        closer = getattr(cap, 'close', getattr(cap, 'release', None))
        if closer is not None:
            closer()

    def __del__(self):
        self.close()

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
    p = argparse.ArgumentParser()
    p.add_argument('--raw', help='run with the raw capture', action='store_true')
    p.add_argument('-f', help='ffmpegreader commandline', nargs='...')
    p.add_argument('-c', help='cv2 identifier', default='0')
    p.add_argument('-v', '--verbose', action='store_true')
    p.add_argument('-w', '--wait', help='wait time for waitkey', type=int, default=10)

    d = p.add_argument_group('debuffer')
    d.add_argument('-r', '--resync', help='resync period', default=10, type=float)
    d.add_argument('-s', '--samplesize', help='fps sampling size', default=10, type=int)
    d.add_argument('-e', '--error', help='error for resampling', default=0.1, type=float)
    d.add_argument('--force', type=int, help='force nth resync', default=10)

    args = p.parse_args()

    if args.f:
        from jhsiao.ffmpeg.ffmpeg import FFmpegReader
        cap = FFmpegReader(args.f, verbose=args.verbose)
    else:
        import ast
        cap = cv2.VideoCapture()
        try:
            args.c = ast.literal_eval(args.c)
        except ValueError:
            pass
        cap.open(args.c)

    if not args.raw:
        cap = Debuffer(cap, args.resync, args.samplesize, args.error, args.force)

    start = time.time()
    nframes = 0
    grabtime = 0
    try:
        s, f = cap.read()
        while s:
            nframes += 1
            cv2.imshow('f', f)
            now = time.time()
            s, f = cap.read()
            grabtime = grabtime + 0.05 * ((time.time()-now) - grabtime)
            switch = cv2.waitKey(args.wait) & 0xFF
            if switch == ord('q'):
                s = False
            elif switch == ord(' '):
                print('average readtime:', grabtime)
                print('overall fps', nframes / (time.time()-start))
    finally:
        getattr(cap, 'close', getattr(cap, 'release', None))()
