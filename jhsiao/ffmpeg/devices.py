"""Get video device info.

options:
    dshow
        video_size
        framerate
        video_device_number(if multiple with same name)
        pixel_format
        -c:v
            (Set to rawvideo for pixel_format)
    v4l2
        video_size
        framerate
        input_format
        pixel_format
windows systems use dshow:
    list devices:
        ffmpeg -f dshow -list_devices 1 -i dummy
    device info:
        ffmpeg -f dshow -list_options 1 -i video='name of device'
other systems use ffmpeg and v4l2-ctl
    list devices:
        os.listdir('/dev')
        v4l2-ctl --list-devices
        (+v4l2-ctl -D -d to filter out metadata-only subdevices)
    device info:
        ffmpeg -list_formats all -i /dev/video*
        v4l2-ctl --list-formats-ext -d /dev/video*
"""
from __future__ import print_function, division
__all__ = ['Devices']
from collections import defaultdict
import itertools
from functools import partial
import os
import io
import platform
import re
import subprocess as sp
import sys

from .holder import Holder

class _Setting(object):
    def __init__(self, fmt, compressed, size, rate):
        """Initialize.

        fmt: format, pixfmt if rawvideo, otherwise, codec
        compressed: bool, True or False
        size: (width,height)
        rate: float, fps
        """
        self._fmt = fmt
        self._compressed = compressed
        self._size = size
        self._rate = rate

    def __hash__(self):
        return sum(map(
            hash, (self._fmt, self._compressed, self._size, self._rate)))

    def __eq__(self, o):
        try:
            return (
                self._fmt == o._fmt and self._compressed == o._compressed
                and self._size == o._size and self._rate == o._rate)
        except AttributeError:
            return NotImplemented

    def __repr__(self):
        return '{}:{}x{}@{:.2f}fps'.format(
            self._fmt, self._size[0], self._size[1], self._rate)

    def ffargs(self):
        """Return a list of ffmpeg arguments."""
        raise NotImplementedError

    def width(self):
        return self._size[0]
    def height(self):
        return self._size[1]
    def area(self):
        return self._size[0] * self._size[1]
    def ratio(self):
        return self._size[0] / self._size[1]
    def fps(self):
        return self._rate
    def compressed(self):
        return self._compressed
    def fmt(self):
        return self._fmt


class _Device(object):
    def __init__(self, name, idinfo=None):
        self.name = name
        self.id = idinfo
        self._data = None

    SPEC = re.compile(r'(?P<prefix>[<>=-]*)(?P<property>\w+)').match
    def prefer(
        self, preferences='>fps,>area',
        size=(float('inf'), float('inf')), fps=float('inf'),
        compressed=True, fmt=''):
        """Return a list of settings.

        size: (width,height), a desired shape
        fps: float, a desired frame rate.
        options: list of possible options.
        preferences: a list of string preferences or comma delimited string.
            [<|>|=|-]name
                name:
                    width
                    height
                    area
                    ratio
                    fps
                    compressed
                    fmt
            flags:
                <: include less than or min if none smaller
                >: include greater than or max if none greater
                =: include equal to
                -: minimal absolute difference
            If there are no matches, then ignore the current filter.
            NOTE: not all flags are meaningful (eg. <> with compressed)
                and may result in weird results.
            eg.
                fps = 8
                options' fpses: [5, 5, 7, 8, 10, 25, 30]
                pref        result          comments
                <fps        5, 5, 7         fps < 8
                <=fps       5, 5, 7, 8      fps <= 8
                <=-fps      8               fps <= 8 and closest to 8
                >fps        10, 25, 30      fps > 8
                >=fps       8, 10, 25, 30   fps >= 8
                >=-fps      8               fps >= 8 and closest to 8
                -fps        8               closest to 8
                <>fps       5, 5, 7, 10, 25, 30 >8 and <8, but not =8
                <>-fps      7               !=8 and closest to 8
        """
        target = _Setting(fmt, compressed, size, fps)
        if isinstance(preferences, str):
            preferences = preferences.split(',')
        options = self.data
        for spec in preferences:
            match = self.SPEC(spec)
            prop = match.group('property')
            try:
                func = getattr(_Setting, match.group('property'))
            except AttributeError:
                raise ValueError('Unknown property: {}'.format(spec))
            lt = defaultdict(list)
            gt = defaultdict(list)
            eq = defaultdict(list)
            desired = func(target)
            for option in options:
                val = func(option)
                if val == desired:
                    eq[val].append(option)
                elif val < desired:
                    lt[val].append(option)
                else:
                    gt[val].append(option)
            prefix = match.group('prefix')
            if not prefix:
                if isinstance(desired, str):
                    prefix = '='
                else:
                    prefix = '-<>='
            if '-' in prefix and eq:
                k, options = eq.popitem()
                continue
            else:
                refined = {}
                if '=' in prefix:
                    refined.update(eq)
                for k, first, last, pick in [
                        ('<', lt, gt, min), ('>', gt, lt, max)]:
                    if k in prefix:
                        if first:
                            refined.update(first)
                        elif eq:
                            refined.update(eq)
                        else:
                            val = pick(last)
                            refined[val] = last[val]
                if not refined:
                    refined = {}
                    refined.update(lt)
                    refined.update(gt)
                    refined.update(eq)
                if '-' in prefix:
                    rrefined = defaultdict(list)
                    for k, v in refined.items():
                        rrefined[abs(desired-k)].extend(v)
                    options = rrefined[min(rrefined)]
                else:
                    options = list(
                        itertools.chain.from_iterable(refined.values()))
        return options

    def _getdata(self):
        """Get data dict of output formats.

        {pixfmt|codec: {size: OutInfo}}
        """
        raise NotImplementedError

    def ffargs(self):
        raise NotImplementedError

    def __iter__(self):
        return iter(self.data)

    @property
    def data(self):
        if self._data is None:
            self._data = self._getdata()
        return self._data

class _Devices(object):
    """Search for devices."""
    def __init__(self):
        self.data = None
        self.refresh()

    def __iter__(self):
        """type and name."""
        for tp, devs in self.data.items():
            for dev in devs:
                yield (tp, dev)

    def __getitem__(self, key):
        """Return items.

        If key is str: It is a type.
        If key is pair: (type, index), index corresponding list
        If key is int: same as pair, except type defaults to 'video'
        """
        if isinstance(key, str):
            return self.data[key]
        if isinstance(key, int):
            tp = 'video'
        else:
            tp, key = key
        return self.data[tp][key]

if platform.system() == 'Windows':
    class Setting(_Setting):
        def ffargs(self):
            ret = [
                '-video_size', '{}x{}'.format(*self._size),
                '-framerate', '{:.2f}'.format(self._rate)]
            if self._compressed:
                ret.append('-c:v')
            else:
                ret.extend(('-c:v', 'rawvideo', '-pixel_format'))
            ret.append(self._fmt)
            return ret

    class Device(_Device):
        _CODEC = re.compile(
            r'\[dshow[^]]+\]\s+(?P<tp>vcodec|pixel_format)=(?P<fmt>\S+)'
            r'\s+min s=(?P<minsize>\d+x\d+) fps=(?P<minfps>\d+)'
            r'\s+max s=(?P<maxsize>\d+x\d+) fps=(?P<maxfps>\d+)')
        def __repr__(self):
            return '"video={}"#{}'.format(self.name, self.id)

        def _getdata(self):
            p = sp.Popen([
                'ffmpeg', '-list_options', '1', '-f', 'dshow',
                '-video_device_number', str(self.id),
                '-i', 'video='+self.name], stderr=sp.PIPE)
            try:
                f = io.TextIOWrapper(p.stderr)
            except AttributeError:
                f = p.stderr
            data = set()
            for m in filter(None, map(Device._CODEC.match, f)):
                compressed = m.group('tp') == 'vcodec'
                name = m.group('fmt')
                sizelo = tuple(map(int, m.group('minsize').split('x')))
                ratelo = float(m.group('minfps'))
                sizehi = tuple(map(int, m.group('maxsize').split('x')))
                ratehi = float(m.group('maxfps'))
                data.update((
                    Setting(name, compressed, sizelo, ratelo),
                    Setting(name, compressed, sizehi, ratehi)))
            if f is not p.stderr:
                f.detach()
            p.communicate()
            return data

        def ffargs(self, *args, **kwargs):
            """Return ffmpeg options for this device.

            args/kwargs: see prefer() to choose a setting.
            Alternatively, use "setting" kwarg to pass in
            a specifically chosen Setting.
            """
            setting = kwargs.pop('setting', None)
            if setting is None:
                setting = self.prefer(*args, **kwargs)[0]
            args = [
                '-f', 'dshow',
                '-video_device_number', str(self.id)]
            args.extend(setting.ffargs())
            args.extend(('-i', 'video='+self.name))
            return args

    class Devices(_Devices):
        _header = re.compile(r'\[dshow[^]]+\]\s+DirectShow (?P<type>video|audio) devices').match
        _match = re.compile(r'\[dshow[^]]+\]\s+"(?P<name>[^"]+)"(?:\s+\((?P<type>video|audio)\))?').match
        def refresh(self):
            p = sp.Popen(
                ['ffmpeg', '-f', 'dshow', '-list_devices', '1', '-i', 'dummy'],
                stderr=sp.PIPE)
            try:
                f = io.TextIOWrapper(p.stderr)
            except AttributeError:
                f = p.stderr
            self.data = data = defaultdict(list)
            # dshow cams may have same name, but then just use the number too
            namecounts = defaultdict(partial(defaultdict, int))
            defaulttp = None
            h = Holder()
            for line in f:
                if h(self._header(line)):
                    defaulttp = h.r.group('type')
                elif h(self._match(line)):
                    name, tp = h.r.groups()
                    if tp is None:
                        tp = defaulttp
                    if tp is None:
                        print('no tp detected for', repr(line), file=sys.stderr)
                    elif tp == 'video':
                        num = namecounts[tp][name]
                        namecounts[tp][name] += 1
                        data[tp].append(Device(name, num))
                    else:
                        # For now, only process video devices
                        pass
            if f is not p.stderr:
                f.detach()
            p.communicate()
else:
    class Setting(_Setting):
        def ffargs(self, *args, **kwargs):
            """Note: v4l2 seems to force one of the innate framerates.

            In testing, it seems to round down, but I would prefer
            rounding up, and then using -r as output to adjust it to
            the desired fps.
            """
            ret = [
                '-video_size', '{}x{}'.format(*self._size),
                '-framerate', '{:.2f}'.format(self._rate)]
            if self._compressed:
                ret.append('-input_format')
            else:
                ret.extend(('-input_format', 'rawvideo', '-pixel_format'))
            ret.append(self._fmt)
            return ret

    class Device(_Device):
        _ffformat = re.compile(
            r'\[[^]]+\]\s+(?P<compressed>Compressed|Raw)\s*'
            r':\s+(?P<fmt>\S+)\s+:'
            r'\s+(?P<name>.*)\s+:\s+'
            r'(?P<sizes>.*)'
        )

        _v4l2ctl_header = re.compile(
            r"\s+\[\d+\]: '[^']+' \((?P<name>[^,]+)(?P<compressed>(?:, compressed)?)\)")
        _v4l2ctl_size = re.compile(r'\s+Size: \D+(?P<size>\d+x\d+)')
        _v4l2ctl_rate = re.compile(r'\s+Interval: .*\((?P<fps>\d+(?:\.\d+)?) fps\)')
        def __repr__(self):
            return self.name + '@'.join(self.id)

        def _getdata(self):
            """Get info.

            ffmpeg list_formats gives proper ffmpeg names, but no fps
            info.  v4l2-ctl only gives names incompatible as ffmpeg
            arguments, but also gives fps info.
            """
            ffinfo = self._get_ffinfo()
            p = sp.Popen(
                ['v4l2-ctl', '--list-formats-ext', '-d', self.name],
                stdout=sp.PIPE)
            try:
                f = io.TextIOWrapper(p.stdout)
            except AttributeError:
                f = p.stdout
            h = Holder()
            name = None
            ffname = None
            compressed = None
            size = None
            sizes = None
            it = iter(f)
            data = []
            added = set()
            for line in it:
                if h(self._v4l2ctl_header.match(line)):
                    name = h.r.group('name')
                    compressed = bool(h.r.group('compressed'))
                    if ffinfo[name]['compressed'] != compressed:
                        print(
                            'warning, compressed does not match for', name,
                            file=sys.stderr)
                    ffname = ffinfo[name]['fmt']
                    sizes = ffinfo[name]['sizes']
                    size = None
                elif h(self._v4l2ctl_size.match(line)):
                    size = tuple(map(int, h.r.group('size').split('x')))
                    if sizes is None:
                        print(
                            'warning, ffmpeg sizes were nor parsed.',
                            file=sys.stderr)
                    elif size not in sizes:
                        print(
                            'Warning:', size, 'not in', sizes, file=sys.stderr)

                elif h(self._v4l2ctl_rate.match(line)):
                    if size is None:
                        print(
                            'Warning, size was None, but expect sizes'
                            ' before fps.  FPS was',
                            h.r.group('fps'), file=sys.stderr)
                    else:
                        setting = Setting(
                            ffname, compressed, size, float(h.r.group('fps')))
                        if setting not in added:
                            added.add(setting)
                            data.append(setting)
                        else:
                            print(
                                'Warning, repeated setting', setting,
                                file=sys.stderr)
            if f is not p.stdout:
                f.detach()
            p.communicate()
            return data

        def _get_ffinfo(self):
            """Return ffmpeg info.

            {
                'full format name': {
                    fmt: 'ffmpeg fmt',
                    sizes=[(width,height),...],
                    compressed=True/False
                },...
            }
            """
            p = sp.Popen(
                ['ffmpeg', '-list_formats', 'all', '-i', self.name],
                stderr=sp.PIPE)
            try:
                f = io.TextIOWrapper(p.stderr)
            except AttributeError:
                f = p.stderr
            ffinfo = {}
            for m in filter(None, map(self._ffformat.match, f)):
                compressed = m.group('compressed') == 'Compressed'
                ffname = m.group('fmt')
                name = m.group('name')
                sizes = [
                    tuple(map(int, s.split('x')))
                    for s in m.group('sizes').strip().split()]
                ffinfo[name] = dict(
                    fmt=ffname, compressed=compressed, sizes=sizes)
            if f is not p.stderr:
                f.detach()
            p.communicate()
            return ffinfo

        def ffargs(self, *args, **kwargs):
            setting = kwargs.pop('setting', None)
            if setting is None:
                setting = self.prefer(*args, **kwargs)[0]
            args = ['-f', 'v4l2']
            args.extend(setting.ffargs())
            args.extend(('-i', self.name))
            return args

        def __repr__(self):
            return self.name

    class Devices(_Devices):
        # Only video devices for now.
        _osdevice = re.compile(r'(?P<type>\D+)(?P<num>\d+)')
        _v4l2ctl_header = re.compile(r'(?P<indent>\s*)(?P<name>.+\s+)\((?P<bus>.*)\):')
        _v4l2ctl_device = re.compile(r'\s+/dev/(?P<type>\D+)(?P<num>\d+)')
        def refresh(self):
            """Refresh data."""
            osdata = self.get_os_devices()
            v4l2data = self.get_v4l2ctl_devices()
            vids = {d['path']: d for d in v4l2data['video']}
            for extrapath in set(osdata['video']).difference(vids):
                vids[extrapath] = dict(name='""', bus='', path=extrapath)
            for p in list(vids):
                if not self.isvid(p):
                    del vids[p]
            self.data = data = defaultdict(list)
            self.data['video'] = [
                Device(d['path'], (d['name'], d['bus'])) for d in vids.values()
            ]

        @classmethod
        def get_os_devices(cls):
            data = defaultdict(set)
            for m in filter(None, map(cls._osdevice.match, os.listdir('/dev'))):
                tp, num = m.groups()
                if tp == 'video':
                    data[tp].add(os.path.join('/dev', m.string))
            return data

        @classmethod
        def get_v4l2ctl_devices(cls):
            """Return dict of info.

            {
                tp:
                    [{path: path, name=name, bus=bus}]
            """
            p = sp.Popen(['v4l2-ctl', '--list-devices'], stdout=sp.PIPE)
            try:
                f = io.TextIOWrapper(p.stdout)
            except AttributeError:
                f = p.stdout
            h = Holder()
            data = defaultdict(list)
            for line in f:
                if h(cls._v4l2ctl_header.match(line)):
                    indent, name, bus = h.r.groups()
                elif h(cls._v4l2ctl_device.match(line)):
                    tp, num = h.r.groups()
                    data[tp].append(dict(name=name, bus=bus, path=line.strip()))
            if f is not p.stdout:
                f.detach()
            p.communicate()
            return data

        @staticmethod
        def isvid(path):
            """Check if path is actually a video capture.

            Sometimes webcams give 2 video devices, 1 for 'Video Capture'
            and one for 'Metadata Capture'.  You can only read video from
            the 'Video Capture' ones.
            """
            p = sp.Popen(['v4l2-ctl', '-D', '-d', path], stdout=sp.PIPE)
            try:
                f = io.TextIOWrapper(p.stdout)
            except AttributeError:
                f = p.stdout
            it = iter(f)
            caps = set()
            for line in it:
                stripped = line.lstrip()
                if stripped.startswith('Device Caps'):
                    indent = line[:len(line) - len(stripped)]
                    pat = re.compile(indent + r'\s+(?P<cap>.*\S)\s*')
                    for match in filter(None, map(pat.match, it)):
                        caps.add(match.group('cap'))
                    break
            if p.stdout is not f:
                f.detach()
            p.communicate()
            return 'Video Capture' in caps
