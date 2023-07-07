blocks = [
    dict(
        block=(
            b"Input #0, matroska,webm, from '/home/andy/Videos/asdf.mkv':\n"
            b"  Metadata:\n"
            b"    COMPATIBLE_BRANDS: isomiso2avc1mp41\n"
            b"    MAJOR_BRAND     : isom\n"
            b"    MINOR_VERSION   : 512\n"
            b"    ENCODER         : Lavf56.40.101\n"
            b"  Duration: 00:00:58.20, start: 0.000000, bitrate: 969 kb/s\n"
            b"    Stream #0:0(eng): Video: h264 (High), yuv420p, 1280x540 [SAR 1:1 DAR 64:27], 15 fps, 15 tbr, 1k tbn, 30 tbc (default)\n"
            b"    Metadata:\n"
            b"      LANGUAGE        : eng\n"
            b"      HANDLER_NAME    : VideoHandler\n"
            b"      ENCODER         : Lavc56.60.100 libx264\n"
            b"      DURATION        : 00:00:58.200000000\n"
            b"Output #0, rawvideo, to 'pipe:':\n"
            b"  Metadata:\n"
            b"    COMPATIBLE_BRANDS: isomiso2avc1mp41\n"
            b"    MAJOR_BRAND     : isom\n"
            b"    MINOR_VERSION   : 512\n"
            b"    encoder         : Lavf56.40.101\n"
            b"    Stream #0:0(eng): Video: rawvideo (BGR[24] / 0x18524742), bgr24, 1280x540 [SAR 1:1 DAR 64:27], q=2-31, 200 kb/s, 15 fps, 15 tbn, 15 tbc (default)\n"
            b"    Metadata:\n"
            b"      LANGUAGE        : eng\n"
            b"      HANDLER_NAME    : VideoHandler\n"
            b"      DURATION        : 00:00:58.200000000\n"
            b"      encoder         : Lavc56.60.100 rawvideo\n"
            b"Stream mapping:\n"
            b"  Stream #0:0 -> #0:0 (h264 (native) -> rawvideo (native))\n"),
        ins={
            0: [
                dict(
                    type='video',
                    name='0:0',
                    codec='h264',
                    pix_fmt='yuv420p',
                    width=1280,
                    height=540,
                    fps=15),
            ],
        },
        outs={
            0: [
                dict(
                    type='video',
                    name='0:0',
                    codec='rawvideo',
                    pix_fmt='bgr24',
                    width=1280,
                    height=540,
                    fps=15),
            ],
        },
    ),
    dict(
        block=(
            b"Input #0, matroska,webm, from '2020-11-08 11-10-12.mkv':\n"
            b"  Metadata:\n"
            b"    ENCODER         : Lavf58.29.100\n"
            b"  Duration: 00:00:06.30, start: 0.000000, bitrate: 2620 kb/s\n"
            b"    Stream #0:0: Video: h264 (High), yuv420p(progressive), 452x800, 30 fps, 30 tbr, 1k tbn, 60 tbc (default)\n"
            b"    Metadata:\n"
            b"      DURATION        : 00:00:06.300000000\n"
            b"    Stream #0:1: Audio: aac (LC), 44100 Hz, stereo, fltp (default)\n"
            b"    Metadata:\n"
            b"      title           : simple_aac\n"
            b"      DURATION        : 00:00:06.200000000\n"
            b"File 'nul' already exists. Overwrite? [y/N] y\n"
            b"Stream mapping:\n"
            b"  Stream #0:0 -> #0:0 (h264 (native) -> rawvideo (native))\n"
            b"Press [q] to stop, [?] for help\n"
            b"Output #0, rawvideo, to 'nul':\n"
            b"  Metadata:\n"
            b"    encoder         : Lavf58.44.100\n"
            b"    Stream #0:0: Video: rawvideo (BGR[24] / 0x18524742), bgr24, 452x800, q=2-31, 260352 kb/s, 30 fps, 30 tbn, 30 tbc (default)\n"
            b"    Metadata:\n"
            b"      DURATION        : 00:00:06.300000000\n"
            b"      encoder         : Lavc58.90.100 rawvideo\n"
            b"frame=  189 fps=0.0 q=-0.0 Lsize=  200222kB time=00:00:06.30 bitrate=260352.0kbits/s dup=1 drop=0 speed=33.6x\n"
            b"video:200222kB audio:0kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.000000%\n"),
    ),
    dict(
        block=(
            b"Input #0, matroska,webm, from 'hipsway.mkv':\n"
            b"  Metadata:\n"
            b"    ENCODER         : Lavf58.29.100\n"
            b"  Duration: 00:00:24.03, start: 0.000000, bitrate: 2626 kb/s\n"
            b"    Stream #0:0: Video: h264 (High), yuv420p(progressive), 500x850, 30 fps, 30 tbr, 1k tbn, 60 tbc (default)\n"
            b"    Metadata:\n"
            b"      DURATION        : 00:00:24.033000000\n"
            b"    Stream #0:1: Audio: aac (LC), 44100 Hz, stereo, fltp (default)\n"
            b"    Metadata:\n"
            b"      title           : simple_aac\n"
            b"      DURATION        : 00:00:23.917000000\n"
            b"Input #1, matroska,webm, from 'keyboard.mkv':\n"
            b"  Metadata:\n"
            b"    ENCODER         : Lavf58.29.100\n"
            b"  Duration: 00:00:25.83, start: 0.000000, bitrate: 2650 kb/s\n"
            b"    Stream #1:0: Video: h264 (High), yuv420p(progressive), 848x480, 30 fps, 30 tbr, 1k tbn, 60 tbc (default)\n"
            b"    Metadata:\n"
            b"      DURATION        : 00:00:25.833000000\n"
            b"    Stream #1:1: Audio: aac (LC), 44100 Hz, stereo, fltp (default)\n"
            b"    Metadata:\n"
            b"      title           : simple_aac\n"
            b"      DURATION        : 00:00:25.728000000\n"
            b"Stream mapping:\n"
            b"  Stream #0:0 -> #0:0 (h264 (native) -> h264 (libx264))\n"
            b"  Stream #1:1 -> #0:1 (aac (native) -> vorbis (libvorbis))\n"
            b"  Stream #0:1 -> #1:0 (aac (native) -> vorbis (libvorbis))\n"
            b"  Stream #1:0 -> #1:1 (h264 (native) -> h264 (libx264))\n"
            b"Press [q] to stop, [?] for help\n"
            b"[libx264 @ 000001e99d0950c0] using cpu capabilities: MMX2 SSE2Fast SSSE3 SSE4.2 AVX FMA3 BMI2 AVX2\n"
            b"[libx264 @ 000001e99d0950c0] profile High, level 3.1, 4:2:0, 8-bit\n"
            b"[libx264 @ 000001e99d0950c0] 264 - core 160 - H.264/MPEG-4 AVC codec - Copyleft 2003-2020 - http://www.videolan.org/x264.html - options: cabac=1 ref=3 deblock=1:0:0 analyse=0x3:0x113 me=hex subme=7 psy=1 psy_rd=1.00:0.00 mixed_ref=1 me_range=16 chroma_me=1 trellis=1 8x8dct=1 cqm=0 deadzone=21,11 fast_pskip=1 chroma_qp_offset=-2 threads=12 lookahead_threads=2 sliced_threads=0 nr=0 decimate=1 interlaced=0 bluray_compat=0 constrained_intra=0 bframes=3 b_pyramid=2 b_adapt=1 b_bias=0 direct=1 weightb=1 open_gop=0 weightp=2 keyint=250 keyint_min=25 scenecut=40 intra_refresh=0 rc_lookahead=40 rc=crf mbtree=1 crf=23.0 qcomp=0.60 qpmin=0 qpmax=69 qpstep=4 ip_ratio=1.40 aq=1:1.00\n"
            b"Output #0, matroska, to 'o1.mkv':\n"
            b"  Metadata:\n"
            b"    encoder         : Lavf58.44.100\n"
            b"    Stream #0:0: Video: h264 (libx264) (H264 / 0x34363248), yuv420p(progressive), 500x850, q=-1--1, 30 fps, 1k tbn, 30 tbc (default)\n"
            b"    Metadata:\n"
            b"      DURATION        : 00:00:24.033000000\n"
            b"      encoder         : Lavc58.90.100 libx264\n"
            b"    Side data:\n"
            b"      cpb: bitrate max/min/avg: 0/0/0 buffer size: 0 vbv_delay: N/A\n"
            b"    Stream #0:1: Audio: vorbis (libvorbis) (oV[0][0] / 0x566F), 44100 Hz, stereo, fltp (default)\n"
            b"    Metadata:\n"
            b"      title           : simple_aac\n"
            b"      DURATION        : 00:00:25.728000000\n"
            b"      encoder         : Lavc58.90.100 libvorbis\n"
            b"[libx264 @ 000001e99d09a080] using cpu capabilities: MMX2 SSE2Fast SSSE3 SSE4.2 AVX FMA3 BMI2 AVX2\n"
            b"[libx264 @ 000001e99d09a080] profile High, level 3.1, 4:2:0, 8-bit\n"
            b"[libx264 @ 000001e99d09a080] 264 - core 160 - H.264/MPEG-4 AVC codec - Copyleft 2003-2020 - http://www.videolan.org/x264.html - options: cabac=1 ref=3 deblock=1:0:0 analyse=0x3:0x113 me=hex subme=7 psy=1 psy_rd=1.00:0.00 mixed_ref=1 me_range=16 chroma_me=1 trellis=1 8x8dct=1 cqm=0 deadzone=21,11 fast_pskip=1 chroma_qp_offset=-2 threads=12 lookahead_threads=2 sliced_threads=0 nr=0 decimate=1 interlaced=0 bluray_compat=0 constrained_intra=0 bframes=3 b_pyramid=2 b_adapt=1 b_bias=0 direct=1 weightb=1 open_gop=0 weightp=2 keyint=250 keyint_min=25 scenecut=40 intra_refresh=0 rc_lookahead=40 rc=crf mbtree=1 crf=23.0 qcomp=0.60 qpmin=0 qpmax=69 qpstep=4 ip_ratio=1.40 aq=1:1.00\n"
            b"Output #1, matroska, to 'o2.mkv':\n"
            b"  Metadata:\n"
            b"    encoder         : Lavf58.44.100\n"
            b"    Stream #1:0: Audio: vorbis (libvorbis) (oV[0][0] / 0x566F), 44100 Hz, stereo, fltp (default)\n"
            b"    Metadata:\n"
            b"      title           : simple_aac\n"
            b"      DURATION        : 00:00:23.917000000\n"
            b"      encoder         : Lavc58.90.100 libvorbis\n"
            b"    Stream #1:1: Video: h264 (libx264) (H264 / 0x34363248), yuv420p, 848x480, q=-1--1, 30 fps, 1k tbn, 30 tbc (default)\n"
            b"    Metadata:\n"
            b"      DURATION        : 00:00:25.833000000\n"
            b"      encoder         : Lavc58.90.100 libx264\n"
            b"    Side data:\n"
            b"      cpb: bitrate max/min/avg: 0/0/0 buffer size: 0 vbv_delay: N/A\n"),
    ),
    dict(
        block=(
            b'ffmpeg version git-2020-06-04-7f81785 Copyright (c) 2000-2020 the FFmpeg developers\r\n'
            b'  built with gcc 9.3.1 (GCC) 20200523\r\n'
            b'  configuration: --enable-gpl --enable-version3 --enable-sdl2 --enable-fontconfig --enable-gnutls --enable-iconv --enable-libass --enable-libdav1d --enable-libbluray --enable-libfreetype --enable-libmp3lame --enable-libopencore-amrnb --enable-libopencore-amrwb --enable-libopenjpeg --enable-libopus --enable-libshine --enable-libsnappy --enable-libsoxr --enable-libsrt --enable-libtheora --enable-libtwolame --enable-libvpx --enable-libwavpack --enable-libwebp --enable-libx264 --enable-libx265 --enable-libxml2 --enable-libzimg --enable-lzma --enable-zlib --enable-gmp --enable-libvidstab --enable-libvmaf --enable-libvorbis --enable-libvo-amrwbenc --enable-libmysofa --enable-libspeex --enable-libxvid --enable-libaom --disable-w32threads --enable-libmfx --enable-ffnvcodec --enable-cuda-llvm --enable-cuvid --enable-d3d11va --enable-nvenc --enable-nvdec --enable-dxva2 --enable-avisynth --enable-libopenmpt --enable-amf\r\n'
            b'  libavutil      56. 49.100 / 56. 49.100\r\n'
            b'  libavcodec     58. 90.100 / 58. 90.100\r\n'
            b'  libavformat    58. 44.100 / 58. 44.100\r\n'
            b'  libavdevice    58.  9.103 / 58.  9.103\r\n'
            b'  libavfilter     7. 84.100 /  7. 84.100\r\n'
            b'  libswscale      5.  6.101 /  5.  6.101\r\n'
            b'  libswresample   3.  6.100 /  3.  6.100\r\n'
            b'  libpostproc    55.  6.100 / 55.  6.100\r\n'
            b"Input #0, matroska,webm, from 'out.mkv':\r\n"
            b'  Metadata:\r\n'
            b'    ENCODER         : Lavf58.44.100\r\n'
            b'  Duration: 00:00:05.00, start: 0.000000, bitrate: 4 kb/s\r\n'
            b'    Stream #0:0: Video: h264 (High 4:4:4 Predictive), yuv444p(progressive), 500x500, 2 fps, 2 tbr, 1k tbn, 4 tbc (default)\r\n'
            b'    Metadata:\r\n'
            b'      ENCODER         : Lavc58.90.100 libx264\r\n'
            b'      DURATION        : 00:00:05.000000000\r\n'
            b'Stream mapping:\r\n'
            b'  Stream #0:0 -> #0:0 (h264 (native) -> rawvideo (native))\r\n'
            b'Press [q] to stop, [?] for help\r\n'
            b'frame=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \rframe=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \rframe=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \rframe=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \rframe=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \rframe=    0 fps=0.0 q=0.0 size=       0kB time=-577014:32:22.77 bitrate=  -0.0kbits/s speed=N/A    \r'
            b"Output #0, rawvideo, to 'pipe:':\r\n"
            b'  Metadata:\r\n'
            b'    encoder         : Lavf58.44.100\r\n'
            b'    Stream #0:0: Video: rawvideo (BGR[24] / 0x18524742), bgr24, 500x500, q=2-31, 12000 kb/s, 2 fps, 2 tbn, 2 tbc (default)\r\n'
            b'    Metadata:\r\n'
            b'      DURATION        : 00:00:05.000000000\r\n'
            b'      encoder         : Lavc58.90.100 rawvideo\r\n'),
    ),
]

