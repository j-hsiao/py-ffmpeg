"""Simple FFmpeg commandline helpers.

If you want more complicated commandlines, just write them yourself.
"""

def read(fname, pix_fmt='bgr24', extra={}):
    """Basic FFmpeg read command.

    Automatically fills output to be:
        -f rawvideo -pix_fmt pix_fmt -
    This is generally most useful to read frames into python.

    extra: additional arguments for input.
        a - will be prepended to the keys if they do not start with
        a -.  If value is None, the flag should take no arguments.
        Otherwise, the value will be used as argument to the flag.
    example:
        read('myfile.mp4', extra=dict(re=None))
        will become the commandline:
            ffmpeg -re -i myfile.mp4 -f rawvideo -pix_fmt bgr24 -
    """
    command = ['ffmpeg']
    for k, v in extra.items():
        if k.startswith('-'):
            command.append(k)
        else:
            command.append('-'+k)
        if v is not None:
            command.append(str(v))
    command.extend(('-i', fname))
    command.extend(('-f', 'rawvideo', '-pix_fmt', pix_fmt, '-'))
    return command

def write(
    fname, size, pix_fmt='bgr24', fps=None, extra={}):
    """Basic ffmpeg write command.

    Generally, this means writing frames to the ffmpeg subprocess.
    The ffmpeg input will default to rawvideo reading from pipe.

    fname: name of output file to write to.
    size: size of video frames for input. tuple: (width,height)
    codec: Name of format or specific encoder.  FFmpeg seems to choose
        the first listed codec in `ffmpeg -codecs` if given a format.
    pix_fmt: Input pixel format.
    fps: the fps to use, if None, then -use_wallclock_as_timestamps.
    extra: extra arguments for output.
    """
    command = ['ffpmeg', '-pix_fmt', pix_fmt, '-f', 'rawvideo']
    if fps is None:
        command.append('-use_wallclock_as_timestamps')
    else:
        command.extend(('-framerate', str(fps), '-r', str(fps)))
    command.extend(('-s', str(size[0]), str(size[1])))
    command.extend(('-pix_fmt', pix_fmt))
    command.extend(('-i', '-'))

    for k, v in extra.items():
        if k.startswith('-'):
            command.append(k)
        else:
            command.append('-'+k)
        if v is not None:
            command.append(str(v))
    command.append(fname)
    return command

if __name__ == '__main__':
    print(read('myfile.mkv'))
    print(write('something.mkv', (500,500)))
