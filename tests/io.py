from jhsiao.ffmpeg.eparse.io import IO
data = [
    dict(
        line="Input #0, matroska,webm, from '/home/andy/Videos/asdf.mkv':\n",
        type='In',
        name='/home/andy/Videos/asdf.mkv',
        num=0,
    ),
    dict(
        line="Output #0, rawvideo, to 'pipe:':\n",
        type='Out',
        name='pipe:',
        num=0,
    ),
    dict(
        line="Input #0, matroska,webm, from '2020-11-08 11-10-12.mkv':\n",
        type='In',
        name='2020-11-08 11-10-12.mkv',
        num=0,
    ),
    dict(line="Output #0, rawvideo, to 'nul':\n",
        type='Out',
        name='nul',
        num=0,
    ),
    dict(line="Input #0, matroska,webm, from 'hipsway.mkv':\n",
        type='In',
        name='hipsway.mkv',
        num=0,
    ),
    dict(line="Input #1, matroska,webm, from 'keyboard.mkv':\n",
        type='In',
        name='keyboard.mkv',
        num=1,
    ),
    dict(line="Output #0, matroska, to 'o1.mkv':\n",
        type='Out',
        name='o1.mkv',
        num=0,
    ),
    dict(line="Output #1, matroska, to 'o2.mkv':\n",
        type='Out',
        name='o2.mkv',
        num=1,
    ),
    dict(line="Input #0, matroska,webm, from 'out.mkv':\r\n",
        type='In',
        name='out.mkv',
        num=0,
    ),
    dict(line="Output #0, rawvideo, to 'pipe:':\r\n",
        type='Out',
        name='pipe:',
        num=0,
    ),
]
def test_io():
    for d in data:
        m = IO.inp.match(d['line'])
        if not m:
            m = IO.out.match(d['line'])
        print(d['line'])
        assert bool(m)
        assert m.group('type') == d['type']
        assert m.group('name') == d['name']
        assert int(m.group('num')) == d['num']

