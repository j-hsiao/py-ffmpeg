import argparse

import cv2

from jhsiao.ffmpeg.ffmpeg import FFmpegReader


def test_reader():
    p = argparse.ArgumentParser()
    p.add_argument('fname', help='input fname')
    p.add_argument('-pix_fmt', help='pixel format to use', default='bgr24')
    args = p.parse_args()

    command = [
        'ffmpeg', '-i', args.fname,
        '-f', 'rawvideo', '-pix_fmt', args.pix_fmt, '-']
    with FFmpegReader(command) as reader:
        print(reader.rawbuf.shape)
        s, f = reader.read()
        while s:
            cv2.imshow('f', cv2.resize(f, (0,0), fx=.5, fy=.5))
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            s, f = reader.read()


if __name__ == '__main__':
    test_reader()
