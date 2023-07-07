from jhsiao.ffmpeg.eparse.stream import Stream, VideoStream, AudioStream
streams = [
    dict(
        line="    Stream #0:0(eng): Video: h264 (High), yuv420p, 1280x540 [SAR 1:1 DAR 64:27], 15 fps, 15 tbr, 1k tbn, 30 tbc (default)",
        type='Video',
        name='0:0',
        codec='h264',
        pix_fmt='yuv420p',
        width=1280,
        height=540,
        fps=15,
    ),
    dict(
        line="    Stream #0:0: Video: rawvideo (YUY2 / 0x32595559), yuyv422, 1280x720, 147456 kb/s, 10 fps, 10 tbr, 1000k tbn, 1000k tbc",
        type='Video',
        codec='rawvideo',
        pix_fmt='yuyv422',
        width=1280,
        height=720,
        fps=10,
    ),
    dict(
        line="    Stream #0:0: Video: mjpeg, yuvj420p(pc, bt470bg/unknown/unknown), 440x293 [SAR 1:1 DAR 440:293], 25 tbr, 25 tbn, 25 tbc",
        type='Video',
        codec='mjpeg',
        pix_fmt='yuvj420p',
        width=440,
        height=293,
        fps=25,
    ),
    dict(
        line="    Stream #0:0: Video: mjpeg, gray(bt470bg/unknown/unknown), 250x250 [SAR 1:1 DAR 1:1], 25 tbr, 25 tbn, 25 tbc",
        type='Video',
        codec='mjpeg',
        pix_fmt='gray',
        width=250,
        height=250,
        fps=25,
    ),
    dict(
        line="    Stream #0:0(eng): Video: h264 (High), yuv420p, 1280x540 [SAR 1:1 DAR 64:27], 15 fps, 15 tbr, 1k tbn, 30 tbc (default)",
        type='Video',
        codec='h264',
        pix_fmt='yuv420p',
        width=1280,
        height=540,
        fps=15,
    ),
    dict(
        line="    Stream #0:0(eng): Video: rawvideo (BGR[24] / 0x18524742), bgr24, 1280x540 [SAR 1:1 DAR 64:27], q=2-31, 200 kb/s, 15 fps, 15 tbn, 15 tbc (default)",
        type='Video',
        codec='rawvideo',
        pix_fmt='bgr24',
        width=1280,
        height=540,
        fps=15,
    ),
    dict(
        line="    Stream #0:0: Video: h264 (High), yuv420p(progressive), 452x800, 30 fps, 30 tbr, 1k tbn, 60 tbc (default)",
        type='Video',
        codec='h264',
        pix_fmt='yuv420p',
        width=452,
        height=800,
        fps=30,
    ),
    dict(
        line="    Stream #0:1: Audio: aac (LC), 44100 Hz, stereo, fltp (default)",
        type='Audio',
        codec='aac',
    ),
    dict(
        line="    Stream #0:0: Video: rawvideo (BGR[24] / 0x18524742), bgr24, 452x800, q=2-31, 260352 kb/s, 30 fps, 30 tbn, 30 tbc (default)",
        type='Video',
        codec='rawvideo',
        pix_fmt='bgr24',
        width=452,
        height=800,
        fps=30,
    ),
    dict(
        line="    Stream #0:0: Video: h264 (High), yuv420p(progressive), 500x850, 30 fps, 30 tbr, 1k tbn, 60 tbc (default)",
        type='Video',
        codec='h264',
        pix_fmt='yuv420p',
        width=500,
        height=850,
        fps=30,
    ),
    dict(
        line="    Stream #0:1: Audio: aac (LC), 44100 Hz, stereo, fltp (default)",
        type='Audio',
        codec='aac',
    ),
    dict(
        line="    Stream #1:0: Video: h264 (High), yuv420p(progressive), 848x480, 30 fps, 30 tbr, 1k tbn, 60 tbc (default)",
        type='Video',
        codec='h264',
        pix_fmt='yuv420p',
        width=848,
        height=480,
        fps=30,
    ),
    dict(
        line="    Stream #1:1: Audio: aac (LC), 44100 Hz, stereo, fltp (default)",
        type='Audio',
        codec='aac',
    ),
    dict(
        line="    Stream #1:0: Video: h264 (High), yuv420p(progressive), 848x480",
        type='Video',
        codec='h264',
        pix_fmt='yuv420p',
        width=848,
        height=480,
        fps=None
    ),
    dict(
        line="    Stream #0:0: Video: h264 (libx264) (H264 / 0x34363248), yuv420p(progressive), 500x850, q=-1--1, 30 fps, 1k tbn, 30 tbc (default)",
        type='Video',
        codec='h264',
        pix_fmt='yuv420p',
        width=500,
        height=850,
        fps=30,
    ),
    dict(
        line="    Stream #0:0: Video: rawvideo (BGR[24] / 0x18524742), bgr24, 500x500, q=2-31, 12000 kb/s, 2 fps, 2 tbn, 2 tbc (default)",
        type='Video',
        codec='rawvideo',
        pix_fmt='bgr24',
        width=500,
        height=500,
        fps=2,
    ),
    dict(
        line="    Stream #0:0: Video: rawvideo, 1 reference frame (BGR[24] / 0x18524742), bgr24, 1280x720 [SAR 1:1 DAR 16:9], q=2-31, 200 kb/s, 30 fps, 30 tbn, 30 tbc (default)",
        type='Video',
        codec='rawvideo',
        pix_fmt='bgr24',
        width=1280,
        height=720,
        fps=30,
    )
]

def test_stream():
    for stream in streams:
        thing = Stream.parse(stream['line'])
        if stream['type'] == 'Video':
            assert isinstance(thing, VideoStream)
            for attr in 'codec pix_fmt width height fps'.split():
                v1 = getattr(thing, attr)
                v2 = stream[attr]
                assert v1 == v2
        elif stream['type'] == 'Audio':
            assert isinstance(thing, AudioStream)
