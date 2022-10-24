from jhsiao.ffmpeg.devices import Devices
import argparse

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-s', '--size', help='WidthxHeight', default='1920x1080')
    p.add_argument('-r', '--rate', help='fps', type=float, default=30)
    p.add_argument('-c', '--compressed', help='compressed?', action='store_true')
    p.add_argument('-f', '--format', help='format', default='h264')
    p.add_argument('filter', nargs='?', help='filter for preferences')
    args = p.parse_args()

    devs = Devices()
    curtype = None
    for tp, dev in devs:
        if tp != curtype:
            curtype = tp
            print(tp)
        print('  ', dev, sep='')
        if args.filter:
            it = dev.prefer(
                args.filter, size=tuple(map(int, args.size.split('x'))),
                fps=args.rate, compressed=args.compressed,
                fmt=args.format)
        else:
            it = dev
        for setting in it:
            print('    ', ' '.join(dev.ffargs(setting=setting)), sep='')
