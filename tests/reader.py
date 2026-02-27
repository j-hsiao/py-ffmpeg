import argparse
import io

import cv2

from jhsiao.ffmpeg.ffmpeg import FFmpegReader, FFmpegWriter
from jhsiao.ffmpeg.info import Codecs


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
        if s:
            shape = '{}x{}'.format(*f.shape[1::-1])
            cmd = [
                'ffmpeg', '-s', shape, '-pix_fmt', 'bgr24', '-f', 'rawvideo', '-i', '-',
                '-c:v', Codecs()['h264'].get('encoders', ['libx264'])[0],
                '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-f', 'matroska', '-']
            with FFmpegWriter(cmd, io.BytesIO()) as writer:
                while s:
                    try:
                        writer.write(f)
                    except Exception:
                        print(writer.error())
                        raise
                    cv2.imshow('f', cv2.resize(f, (0,0), fx=.5, fy=.5))
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    s, f = reader.read()
            raw = writer.ostream.detach()

    command = [
        'ffmpeg', '-i', '-',
        '-f', 'rawvideo', '-pix_fmt', args.pix_fmt, '-']
    raw.seek(0)
    with FFmpegReader(command, raw) as reader:
        s, f = reader.read()
        while s:
            cv2.imshow('f', cv2.resize(f, (0,0), fx=.5, fy=.5))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            s, f = reader.read()


if __name__ == '__main__':
    test_reader()
