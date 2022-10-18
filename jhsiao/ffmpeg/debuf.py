"""Use threading to continually grab frames.

Frames are generally buffered which may result in higher latency since
older frames are kept in the buffer.
"""
from __future__ import print_function
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
        self, cap, resync=(10, 3), samplesize=5, error=0.10,
        delaythresh=0.5):
        """Initialize a Debuffer object.

        cap: The video reader.  It should support grab and retrieve.
        resync: float or tuple.  Resync period in seconds and number of
            resyncs before forced buffer-clearing.  Resyncing entails
            comparing current fps to calculated fps.  If the relative
            difference is greater than error, clear resample the fps.
            If a tuple, the second value indicates that every Nth
            resync is forced to resample fps even if the effective
            grabrate matches the calculated fps to within error.  If the
            force period is omitted, no resyncs will be forced.
        error: float:0-1  If the grab-rate differs from the sampled fps
            by more than error(relative error), fps is resampled.  This
            can happen if the initially sampled fps was too high, for
            example, if there were buffered frames.  If the fps could be
            parsed (cv2.VideoCapture.get() or
            .ffmpeg.FFmpegReader.stream.fps, then fps will be sampled
            until it is within error of the parsed fps.  This effectively
            clears any buffered frames.
        delaythresh: float: 0-1  If a grab takes longer than delaythresh
            of the frame period, then the grab is considered slow, which
            would happen on empty buffers.  To reduce the time with the
            lock held, wait a bit more.
        """
        self.cap = cap
        self.cond = threading.Condition()
        self._updated = False
        self._running = True

        if isinstance(resync, (int, float)):
            resync = (resync, float('inf'))
        elif len(resync) < 2:
            resync = (resync[0], float('inf'))
        self.resync = resync
        self.samplesize = samplesize
        self.error = error
        self.delaythresh = delaythresh
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
        target = self.samplesize
        while 1:
            for i in range(self.samplesize):
                if not grab(cond, cap):
                    return False, None, None
            finish = time.time()
            elapsed = finish - start
            if elapsed:
                return True, self.samplesize / (finish - start), finish
            else:
                start = finish

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
            fps = parsedfps
            okay, end = self._clear_buffer(cond, cap, time.time(), parsedfps)
        else:
            okay = grab(cond, cap)
            if not okay:
                return
            okay, fps, end = self._sample_fps(cond, cap, time.time())
        if not okay:
            return
        anchor = end
        check = end + self.resync[0]
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
                if (abs((effectivefps / fps)-1) > self.error
                        or resyncs>=self.resync[1]):
                    if parsedfps is not None:
                        okay, end = self._clear_buffer(cond, cap, end, parsedfps)
                    else:
                        okay, fps, end = self._sample_fps(cond, cap, end)
                        period = 1/fps
                    if not okay:
                        return
                    target = end+period
                    resyncs = 0
                else:
                    gaverage = gtotal/total
                total = gtotal = 0
                check = end+self.resync[0]
                anchor = end
            if target>end:
                time.sleep(target-end)
            else:
                if gtime > period*self.delaythresh:
                    time.sleep(period)
                    target = time.time()
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
        """Stop thread and close capture."""
        cap = self.detach()
        closer = getattr(cap, 'close', getattr(cap, 'release', None))
        if closer is not None:
            closer()

    def release(self):
        """mimic opencv interface."""
        self.close()

    def __del__(self):
        self.close()

    def detach(self):
        """Stop thread but keep original capture open."""
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
    p.add_argument(
        '--raw', help='run with the raw capture', action='store_true')
    p.add_argument('-f', help='ffmpegreader commandline', nargs='...')
    p.add_argument('-c', help='cv2 identifier', default='0')
    p.add_argument('-v', '--verbose', action='store_true')
    p.add_argument(
        '-w', '--wait', help='wait time for waitkey', type=int, default=10)

    d = p.add_argument_group('debuffer')
    d.add_argument(
        '-r', '--resync', help='resync period',
        default=[10], type=float, nargs='*')
    d.add_argument(
        '-s', '--samplesize', help='fps sampling size', default=10, type=int)
    d.add_argument(
        '-e', '--error', help='error for resampling', default=0.1, type=float)
    d.add_argument(
        '-d', '--delaythresh',
        help='% of frame period threshold to delay frame grabbing',
        type=float, default=0.5)

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
        cap = Debuffer(
            cap, args.resync, args.samplesize, args.error, args.delaythresh)

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
            grabtime += time.time()-now
            switch = cv2.waitKey(args.wait) & 0xFF
            if switch == ord('q'):
                s = False
            elif switch == ord(' '):
                print('average readtime:', grabtime/nframes)
                print('overall fps', nframes / (time.time()-start))
                grabtime = nframes = 0
                start = time.time()
    finally:
        getattr(cap, 'close', getattr(cap, 'release', None))()
