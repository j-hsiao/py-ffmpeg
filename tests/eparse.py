from jhsiao.ffmpeg.eparse import FFmpegEParser
import io

blocks = [
    dict(
        block=(
            "Input #0, matroska,webm, from '/home/andy/Videos/asdf.mkv':\n"
            "  Metadata:\n"
            "    COMPATIBLE_BRANDS: isomiso2avc1mp41\n"
            "    MAJOR_BRAND     : isom\n"
            "    MINOR_VERSION   : 512\n"
            "    ENCODER         : Lavf56.40.101\n"
            "  Duration: 00:00:58.20, start: 0.000000, bitrate: 969 kb/s\n"
            "    Stream #0:0(eng): Video: h264 (High), yuv420p, 1280x540 [SAR 1:1 DAR 64:27], 15 fps, 15 tbr, 1k tbn, 30 tbc (default)\n"
            "    Metadata:\n"
            "      LANGUAGE        : eng\n"
            "      HANDLER_NAME    : VideoHandler\n"
            "      ENCODER         : Lavc56.60.100 libx264\n"
            "      DURATION        : 00:00:58.200000000\n"
            "Output #0, rawvideo, to 'pipe:':\n"
            "  Metadata:\n"
            "    COMPATIBLE_BRANDS: isomiso2avc1mp41\n"
            "    MAJOR_BRAND     : isom\n"
            "    MINOR_VERSION   : 512\n"
            "    encoder         : Lavf56.40.101\n"
            "    Stream #0:0(eng): Video: rawvideo (BGR[24] / 0x18524742), bgr24, 1280x540 [SAR 1:1 DAR 64:27], q=2-31, 200 kb/s, 15 fps, 15 tbn, 15 tbc (default)\n"
            "    Metadata:\n"
            "      LANGUAGE        : eng\n"
            "      HANDLER_NAME    : VideoHandler\n"
            "      DURATION        : 00:00:58.200000000\n"
            "      encoder         : Lavc56.60.100 rawvideo\n"
            "Stream mapping:\n"
            "  Stream #0:0 -> #0:0 (h264 (native) -> rawvideo (native))\n"),
        ins={
            0: {
                '0:0': dict(
                    type='Video',
                    codec='h264',
                    pix_fmt='yuv420p',
                    width=1280,
                    height=540,
                    fps=15),
            },
        },
        outs={
            0: {
                '0:0': dict(
                    type='Video',
                    codec='rawvideo',
                    pix_fmt='bgr24',
                    width=1280,
                    height=540,
                    fps=15),
            },
        },
        map=[('0:0', '0:0')]
    ),
    dict(
        block=(
            "Input #0, matroska,webm, from '2020-11-08 11-10-12.mkv':\n"
            "  Metadata:\n"
            "    ENCODER         : Lavf58.29.100\n"
            "  Duration: 00:00:06.30, start: 0.000000, bitrate: 2620 kb/s\n"
            "    Stream #0:0: Video: h264 (High), yuv420p(progressive), 452x800, 30 fps, 30 tbr, 1k tbn, 60 tbc (default)\n"
            "    Metadata:\n"
            "      DURATION        : 00:00:06.300000000\n"
            "    Stream #0:1: Audio: aac (LC), 44100 Hz, stereo, fltp (default)\n"
            "    Metadata:\n"
            "      title           : simple_aac\n"
            "      DURATION        : 00:00:06.200000000\n"
            "File 'nul' already exists. Overwrite? [y/N] y\n"
            "Stream mapping:\n"
            "  Stream #0:0 -> #0:0 (h264 (native) -> rawvideo (native))\n"
            "Press [q] to stop, [?] for help\n"
            "Output #0, rawvideo, to 'nul':\n"
            "  Metadata:\n"
            "    encoder         : Lavf58.44.100\n"
            "    Stream #0:0: Video: rawvideo (BGR[24] / 0x18524742), bgr24, 452x800, q=2-31, 260352 kb/s, 30 fps, 30 tbn, 30 tbc (default)\n"
            "    Metadata:\n"
            "      DURATION        : 00:00:06.300000000\n"
            "      encoder         : Lavc58.90.100 rawvideo\n"
            "frame=  189 fps=0.0 q=-0.0 Lsize=  200222kB time=00:00:06.30 bitrate=260352.0kbits/s dup=1 drop=0 speed=33.6x\n"
            "video:200222kB audio:0kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.000000%\n"),
        ins={
            0: {
                '0:0': dict(
                    type='Video',
                    codec='h264',
                    pix_fmt='yuv420p',
                    width=452,
                    height=800,
                    fps=30),
                '0:1': dict(type='Audio'),
            },
        },
        outs={
            0: {
                '0:0': dict(
                    type='Video',
                    codec='rawvideo',
                    pix_fmt='bgr24',
                    width=452,
                    height=800,
                    fps=30
                ),
            },
        },
        map=[('0:0', '0:0')]
    ),
    dict(
        block=(
            "Input #0, matroska,webm, from 'hipsway.mkv':\n"
            "  Metadata:\n"
            "    ENCODER         : Lavf58.29.100\n"
            "  Duration: 00:00:24.03, start: 0.000000, bitrate: 2626 kb/s\n"
            "    Stream #0:0: Video: h264 (High), yuv420p(progressive), 500x850, 30 fps, 30 tbr, 1k tbn, 60 tbc (default)\n"
            "    Metadata:\n"
            "      DURATION        : 00:00:24.033000000\n"
            "    Stream #0:1: Audio: aac (LC), 44100 Hz, stereo, fltp (default)\n"
            "    Metadata:\n"
            "      title           : simple_aac\n"
            "      DURATION        : 00:00:23.917000000\n"
            "Input #1, matroska,webm, from 'keyboard.mkv':\n"
            "  Metadata:\n"
            "    ENCODER         : Lavf58.29.100\n"
            "  Duration: 00:00:25.83, start: 0.000000, bitrate: 2650 kb/s\n"
            "    Stream #1:0: Video: h264 (High), yuv420p(progressive), 848x480, 30 fps, 30 tbr, 1k tbn, 60 tbc (default)\n"
            "    Metadata:\n"
            "      DURATION        : 00:00:25.833000000\n"
            "    Stream #1:1: Audio: aac (LC), 44100 Hz, stereo, fltp (default)\n"
            "    Metadata:\n"
            "      title           : simple_aac\n"
            "      DURATION        : 00:00:25.728000000\n"
            "Stream mapping:\n"
            "  Stream #0:0 -> #0:0 (h264 (native) -> h264 (libx264))\n"
            "  Stream #1:1 -> #0:1 (aac (native) -> vorbis (libvorbis))\n"
            "  Stream #0:1 -> #1:0 (aac (native) -> vorbis (libvorbis))\n"
            "  Stream #1:0 -> #1:1 (h264 (native) -> h264 (libx264))\n"
            "Press [q] to stop, [?] for help\n"
            "[libx264 @ 000001e99d0950c0] using cpu capabilities: MMX2 SSE2Fast SSSE3 SSE4.2 AVX FMA3 BMI2 AVX2\n"
            "[libx264 @ 000001e99d0950c0] profile High, level 3.1, 4:2:0, 8-bit\n"
            "[libx264 @ 000001e99d0950c0] 264 - core 160 - H.264/MPEG-4 AVC codec - Copyleft 2003-2020 - http://www.videolan.org/x264.html - options: cabac=1 ref=3 deblock=1:0:0 analyse=0x3:0x113 me=hex subme=7 psy=1 psy_rd=1.00:0.00 mixed_ref=1 me_range=16 chroma_me=1 trellis=1 8x8dct=1 cqm=0 deadzone=21,11 fast_pskip=1 chroma_qp_offset=-2 threads=12 lookahead_threads=2 sliced_threads=0 nr=0 decimate=1 interlaced=0 bluray_compat=0 constrained_intra=0 bframes=3 b_pyramid=2 b_adapt=1 b_bias=0 direct=1 weightb=1 open_gop=0 weightp=2 keyint=250 keyint_min=25 scenecut=40 intra_refresh=0 rc_lookahead=40 rc=crf mbtree=1 crf=23.0 qcomp=0.60 qpmin=0 qpmax=69 qpstep=4 ip_ratio=1.40 aq=1:1.00\n"
            "Output #0, matroska, to 'o1.mkv':\n"
            "  Metadata:\n"
            "    encoder         : Lavf58.44.100\n"
            "    Stream #0:0: Video: h264 (libx264) (H264 / 0x34363248), yuv420p(progressive), 500x850, q=-1--1, 30 fps, 1k tbn, 30 tbc (default)\n"
            "    Metadata:\n"
            "      DURATION        : 00:00:24.033000000\n"
            "      encoder         : Lavc58.90.100 libx264\n"
            "    Side data:\n"
            "      cpb: bitrate max/min/avg: 0/0/0 buffer size: 0 vbv_delay: N/A\n"
            "    Stream #0:1: Audio: vorbis (libvorbis) (oV[0][0] / 0x566F), 44100 Hz, stereo, fltp (default)\n"
            "    Metadata:\n"
            "      title           : simple_aac\n"
            "      DURATION        : 00:00:25.728000000\n"
            "      encoder         : Lavc58.90.100 libvorbis\n"
            "[libx264 @ 000001e99d09a080] using cpu capabilities: MMX2 SSE2Fast SSSE3 SSE4.2 AVX FMA3 BMI2 AVX2\n"
            "[libx264 @ 000001e99d09a080] profile High, level 3.1, 4:2:0, 8-bit\n"
            "[libx264 @ 000001e99d09a080] 264 - core 160 - H.264/MPEG-4 AVC codec - Copyleft 2003-2020 - http://www.videolan.org/x264.html - options: cabac=1 ref=3 deblock=1:0:0 analyse=0x3:0x113 me=hex subme=7 psy=1 psy_rd=1.00:0.00 mixed_ref=1 me_range=16 chroma_me=1 trellis=1 8x8dct=1 cqm=0 deadzone=21,11 fast_pskip=1 chroma_qp_offset=-2 threads=12 lookahead_threads=2 sliced_threads=0 nr=0 decimate=1 interlaced=0 bluray_compat=0 constrained_intra=0 bframes=3 b_pyramid=2 b_adapt=1 b_bias=0 direct=1 weightb=1 open_gop=0 weightp=2 keyint=250 keyint_min=25 scenecut=40 intra_refresh=0 rc_lookahead=40 rc=crf mbtree=1 crf=23.0 qcomp=0.60 qpmin=0 qpmax=69 qpstep=4 ip_ratio=1.40 aq=1:1.00\n"
            "Output #1, matroska, to 'o2.mkv':\n"
            "  Metadata:\n"
            "    encoder         : Lavf58.44.100\n"
            "    Stream #1:0: Audio: vorbis (libvorbis) (oV[0][0] / 0x566F), 44100 Hz, stereo, fltp (default)\n"
            "    Metadata:\n"
            "      title           : simple_aac\n"
            "      DURATION        : 00:00:23.917000000\n"
            "      encoder         : Lavc58.90.100 libvorbis\n"
            "    Stream #1:1: Video: h264 (libx264) (H264 / 0x34363248), yuv420p, 848x480, q=-1--1, 30 fps, 1k tbn, 30 tbc (default)\n"
            "    Metadata:\n"
            "      DURATION        : 00:00:25.833000000\n"
            "      encoder         : Lavc58.90.100 libx264\n"
            "    Side data:\n"
            "      cpb: bitrate max/min/avg: 0/0/0 buffer size: 0 vbv_delay: N/A\n"),
        ins={
            0: {
                '0:0': dict(
                    type='Video',
                    codec='h264',
                    pix_fmt='yuv420p',
                    width=500,
                    height=850,
                    fps=30),
                '0:1': dict(type='Audio'),
            },
            1: {
                '1:0': dict(
                    type='Video',
                    codec='h264',
                    pix_fmt='yuv420p',
                    width=848,
                    height=480,
                    fps=30),
                '1:1': dict(type='Audio')
            }
        },
        outs={
            0: {
                '0:0': dict(
                    type='Video',
                    codec='h264',
                    pix_fmt='yuv420p',
                    width=500,
                    height=850,
                    fps=30),
                '0:1': dict(type='Audio')
            },
            1: {
                '1:0': dict(type='Audio'),
                '1:1': dict(
                    type='Video',
                    codec='h264',
                    pix_fmt='yuv420p',
                    width=848,
                    height=480,
                    fps=30),
            },
        },
        map=[('0:0', '0:0'), ('1:1', '0:1'), ('0:1', '1:0'), ('1:0', '1:1')]
    ),
    dict(
        block=(
            'ffmpeg version git-2020-06-04-7f81785 Copyright (c) 2000-2020 the FFmpeg developers\r\n'
            '  built with gcc 9.3.1 (GCC) 20200523\r\n'
            '  configuration: --enable-gpl --enable-version3 --enable-sdl2 --enable-fontconfig --enable-gnutls --enable-iconv --enable-libass --enable-libdav1d --enable-libbluray --enable-libfreetype --enable-libmp3lame --enable-libopencore-amrnb --enable-libopencore-amrwb --enable-libopenjpeg --enable-libopus --enable-libshine --enable-libsnappy --enable-libsoxr --enable-libsrt --enable-libtheora --enable-libtwolame --enable-libvpx --enable-libwavpack --enable-libwebp --enable-libx264 --enable-libx265 --enable-libxml2 --enable-libzimg --enable-lzma --enable-zlib --enable-gmp --enable-libvidstab --enable-libvmaf --enable-libvorbis --enable-libvo-amrwbenc --enable-libmysofa --enable-libspeex --enable-libxvid --enable-libaom --disable-w32threads --enable-libmfx --enable-ffnvcodec --enable-cuda-llvm --enable-cuvid --enable-d3d11va --enable-nvenc --enable-nvdec --enable-dxva2 --enable-avisynth --enable-libopenmpt --enable-amf\r\n'
            '  libavutil      56. 49.100 / 56. 49.100\r\n'
            '  libavcodec     58. 90.100 / 58. 90.100\r\n'
            '  libavformat    58. 44.100 / 58. 44.100\r\n'
            '  libavdevice    58.  9.103 / 58.  9.103\r\n'
            '  libavfilter     7. 84.100 /  7. 84.100\r\n'
            '  libswscale      5.  6.101 /  5.  6.101\r\n'
            '  libswresample   3.  6.100 /  3.  6.100\r\n'
            '  libpostproc    55.  6.100 / 55.  6.100\r\n'
            "Input #0, matroska,webm, from 'out.mkv':\r\n"
            '  Metadata:\r\n'
            '    ENCODER         : Lavf58.44.100\r\n'
            '  Duration: 00:00:05.00, start: 0.000000, bitrate: 4 kb/s\r\n'
            '    Stream #0:0: Video: h264 (High 4:4:4 Predictive), yuv444p(progressive), 500x500, 2 fps, 2 tbr, 1k tbn, 4 tbc (default)\r\n'
            '    Metadata:\r\n'
            '      ENCODER         : Lavc58.90.100 libx264\r\n'
            '      DURATION        : 00:00:05.000000000\r\n'
            'Stream mapping:\r\n'
            '  Stream #0:0 -> #0:0 (h264 (native) -> rawvideo (native))\r\n'
            'Press [q] to stop, [?] for help\r\n'
            'frame=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \rframe=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \rframe=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \rframe=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \rframe=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \rframe=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \r'
            "Output #0, rawvideo, to 'pipe:':\r\n"
            '  Metadata:\r\n'
            '    encoder         : Lavf58.44.100\r\n'
            '    Stream #0:0: Video: rawvideo (BGR[24] / 0x18524742), bgr24, 500x500, q=2-31, 12000 kb/s, 2 fps, 2 tbn, 2 tbc (default)\r\n'
            '    Metadata:\r\n'
            '      DURATION        : 00:00:05.000000000\r\n'
            '      encoder         : Lavc58.90.100 rawvideo\r\n'),
        ins={
            0: {
                '0:0': dict(
                    type='Video',
                    codec='h264',
                    pix_fmt='yuv444p',
                    width=500,
                    height=500,
                    fps=2),
            },
        },
        outs={
            0: {
                '0:0': dict(
                    type='Video',
                    codec='rawvideo',
                    pix_fmt='bgr24',
                    width=500,
                    height=500,
                    fps=2),
            }
        },
        map=[('0:0', '0:0')]
    ),
]


def test_eparse():
    for d in blocks:
        print('------------------------------')
        thing = FFmpegEParser(io.StringIO(''.join(d['block'])), True)
        print('====')
        ins = {}
        outs = {}
        for i in thing.ins.values():
            idata = {}
            for stream in i.streams.values():
                if stream.type == 'Video':
                    idata[stream.name] = dict(
                        type=stream.type,
                        codec=stream.codec,
                        pix_fmt=stream.pix_fmt,
                        width=stream.width,
                        height=stream.height,
                        fps=stream.fps)
                else:
                    idata[stream.name] = dict(type=stream.type)
            ins[i.num] = idata
        for o in thing.outs.values():
            odata = {}
            for stream in o.streams.values():
                if stream.type == 'Video':
                    odata[stream.name] = dict(
                        type=stream.type,
                        codec=stream.codec,
                        pix_fmt=stream.pix_fmt,
                        width=stream.width,
                        height=stream.height,
                        fps=stream.fps)
                else:
                    odata[stream.name] = dict(type=stream.type)
            outs[o.num] = odata

        for i in thing.ins.values():
            print(i)
        for o in thing.outs.values():
            print(o)
        print(thing.streammap)

        assert ins == d['ins']
        assert outs == d['outs']
        assert set(list(thing.streammap)) == set(d['map'])
