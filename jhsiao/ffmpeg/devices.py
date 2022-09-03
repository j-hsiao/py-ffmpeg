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
from __future__ import print_function
from collections import defaultdict
from functools import partial
import os
import io
import platform
import re
import subprocess as sp
import sys

class _OutInfo(object):
    """FPSes at a given size for format

    Simple heuristic for closest size.
    """
    def __init__(self, name, compressed, size, *rates, **kwargs):
        self.name = name
        self.compressed = compressed
        self.size = size
        self.rates = set(rates)
        self.kwargs = kwargs

    def __repr__(self):
        return '{},{},fps:[{}]'.format(
            self.name, self.size,
            ','.join(map(str, sorted(self.rates))))

    def options(self):
        """Return ffmpeg options for this output."""
        raise NotImplementedError

    def add(self, rate):
        """Add a rate."""
        self.rates.add(rate)
    def update(self, *rates):
        self.rates.update(rates)

    def distance(self, size):
        """Measure of distance to a given size.

        0 = exact match.
        """
        width, height = self.size
        w, h = size
        return abs(w-width) + abs(h-height)

class _Device(object):
    def __init__(self, name, idinfo=None):
        self.name = name
        self.id = idinfo
        self._data = None

    def _getdata(self):
        """Get data dict of output formats.

        {pixfmt|codec: {size: OutInfo}}
        """
        raise NotImplementedError
    def options(self):
        raise NotImplementedError

    def __iter__(self):
        for sized in self.data.values():
            for size in sized.values():
                yield size

    @property
    def data(self):
        if self._data is None:
            self._data = self._getdata()
        return self._data

    def get(self, size=None, fmt=None, compressed=None):
        """Get a combination of settings of device.

        Arguments are just guidelines. and the closest
        one will be returned.
        """
        data = self.data
        candidates = []
        sizedict = data.get(fmt)
        if sizedict is None:
            for sizedict in data.values():
                candidates.extend(sizedict.values())
        else:
            candidates.extend(sizedict.values())
        if len(candidates) == 1:
            return candidates[0]
        if compressed is not None:
            candidates = [
                item for item in candidates if item.compressed==compressed]
            if len(candidates) == 1:
                return candidates[0]
        if size is not None:
            best = float('inf')
            for cand in candidates:
                dst = cand.distance(size)
                if dst < best:
                    newcands = [cand]
                    best = dst
                elif dst == best:
                    newcands.append(cand)
            candidates = newcands
            if len(candidates) == 1:
                return candidates[0]
        # prefer highest fps
        fastest = 0
        for cand in candidates:
            fps = max(cand.rates)
            if fps > fastest:
                fastest = fps
                newcands = [cand]
            elif fps == fastest:
                newcands.append(cand)
        if len(newcands) == 1:
            return candidates[0]
        candidates = newcands
        # prefer biggest frame
        biggest = 0
        for cand in candidates:
            size = sum(cand.size)
            if size > biggest:
                biggest = size
                newcands = [cand]
            elif size == biggest:
                newcands.append(cand)
        if compressed is None:
            # prefer compressed over uncompressed
            for cand in newcands:
                if cand.compressed:
                    return cand
        return newcands[0]

class _Devices(object):
    def __init__(self):
        self.data = None
        self.refresh()

    def __iter__(self):
        """type and name."""
        for tp, devs in self.data.items():
            for dev in devs:
                yield (tp, dev)

    def __getitem__(self, idx):
        """Return items.

        If idx is str: list of devices corresponding to idx
        If idx is pair: (type, idx), index corresponding list
        If idx is int: same as pair, except type defaults to 'video'
        """
        if isinstance(idx, str):
            return self.data[idx]
        if isinstance(idx, int):
            tp = 'video'
        else:
            tp, idx = idx
        return self.data[tp][idx]

if platform.system() == 'Windows':
    class OutInfo(_OutInfo):
        def options(self, fps=30):
            ret = ['-video_size', '{}x{}'.format(*self.size), '-framerate']
            lo = min(self.rates)
            hi = max(self.rates)
            ret.append('{:.2f}'.format(max(min(fps, hi), lo)))
            if self.compressed:
                ret.append('-c:v')
            else:
                ret.extend(('-c:v', 'rawvideo', '-pixel_format'))
            ret.append(self.name)


    class Device(_Device):
        _CODEC = re.compile(
            r'\[dshow[^]]+\]\s+(?P<tp>vcodec|pixel_format)=(?P<fmt>\S+)'
            r'\s+min s=(?P<minsize>\d+x\d+) fps=(?P<minfps>\d+)'
            r'\s+max s=(?P<maxsize>\d+x\d+) fps=(?P<maxfps>\d+)')
        def __repr__(self):
            return '"video={}"#{}'.format(self.name, self.id)

        def _getdata(self):
            p = sp.Popen(
                ['ffmpeg', '-list_options', '1']+self.options(),
                stderr=sp.PIPE)
            try:
                f = io.TextIOWrapper(p.stderr)
            except AttributeError:
                f = p.stderr
            data = defaultdict(dict)
            for m in filter(None, map(Device._CODEC.match, f)):
                compressed = m.group('tp') == 'vcodec'
                name = m.group('fmt')
                sizelo = tuple(map(int, m.group('minsize').split('x')))
                ratelo = float(m.group('minfps'))
                sizehi = tuple(map(int, m.group('maxsize').split('x')))
                ratehi = float(m.group('maxfps'))
                infos = data[name]
                info = infos.get(sizelo)
                if info is None:
                    info = infos[sizelo] = OutInfo(name, compressed, sizelo, ratelo)
                if compressed != info.compressed:
                    print(
                        'warning, compression does not match for format {}'.format(name),
                        file=sys.stderr)
                if sizelo == sizehi:
                    info.update(ratelo, ratehi)
                else:
                    info.add(ratelo)
                    info = infos.get(sizehi)
                    if info is None:
                        info = infos[sizelo] = OutInfo(name, compressed, sizelo, ratelo)
                    if compressed != info.compressed:
                        print(
                            'warning, compression does not match for format {}'.format(name),
                            file=sys.stderr)
                    info.add(ratehi)
            if f is not p.stderr:
                f.detach()
            p.communicate()
            return data

        def options(self):
            """Return ffmpeg options for this device."""
            return [
                '-f', 'dshow',
                '-video_device_number', str(self.id),
                '-i', 'video='+self.name]

    class Devices(_Devices):
        _match = re.compile(r'\[dshow[^]]+\]\s+"(?P<name>[^"]+)"(?: \((?P<type>video|audio)\))?').match
        _header = re.compile(r'\[dshow[^]]+\]\s+DirectShow (?P<type>video|audio) devices').match
        def refresh(self):
            p = sp.Popen(
                ['ffmpeg', '-f', 'dshow', '-list_devices', '1', '-i', 'dummy'],
                stderr=sp.PIPE)
            try:
                f = io.TextIOWrapper(p.stderr)
            except AttributeError:
                f = p.stderr
            self.data = data = defaultdict(list)
            namecounts = defaultdict(partial(defaultdict, int))
            defaulttp = None
            for line in f:
                h = Devices._header(line)
                if h:
                    defaulttp = h.group('type')
                else:
                    m = Devices._match(line)
                    if m:
                        name, tp = m.groups()
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
    from .holder import Holder
    class OutInfo(_OutInfo):
        def options(self, fps=30):
            """Note: v4l2 seems to force one of the innate framerates.

            In testing, it seems to round down, but I would prefer
            rounding up, and then using -r as output to adjust it to
            the desired fps.
            """
            ret = ['-video_size', '{}x{}'.format(*self.size), '-framerate']
            if fps not in self.rates:
                rates = [(fps-r, r) for r in self.rates if fps > r]
                if rates:
                    fps = min(rates)[1]
                else:
                    fps = max(self.rates)
            ret.append('{:.2f}'.format(fps))
            if self.compressed:
                ret.append('-input_format')
            else:
                ret.extend(('-input_format', 'rawvideo', '-pixel_format'))
            ret.append(self.name)

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
            info v4l2-ctl only gives names incompatible as ffmpeg
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
            compressed = None
            it = iter(f)
            data = defaultdict(dict)
            lastinfo = None
            for line in it:
                if h(self._v4l2ctl_header.match(line)):
                    name = h.r.group('name')
                    compressed = bool(h.r.group('compressed'))
                    if ffinfo[name]['compressed'] != compressed:
                        print('warning, compressed does not match for', name, file=sys.stderr)
                    name = ffinfo[name]['name']
                elif h(self._v4l2ctl_size.match(line)):
                    size = tuple(map(int, h.r.group('size').split('x')))
                    lastinfo = data[name][size] = OutInfo(name, compressed, size)
                elif h(self._v4l2ctl_rate.match(line)):
                    lastinfo.add(float(h.r.group('fps')))
            if f is not p.stdout:
                f.detach()
            p.communicate()
            return data

        def _get_ffinfo(self):
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
                    name=ffname, compressed=compressed, sizes=sizes)
            if f is not p.stderr:
                f.detach()
            p.communicate()
            return ffinfo

        def options(self):
            return ['-f', 'v4l2', '-i', self.name]
        def __repr__(self):
            return self.name

    class Devices(_Devices):
        # Only video devices for now.
        _osdevice = re.compile(r'(?P<type>\D+)(?P<num>\d+)')
        _v4l2ctl_header = re.compile(r'(?P<indent>\s*)(?P<name>.+\s+)\((?P<bus>.*)\):')
        _v4l2ctl_device = re.compile(r'\s+/dev/(?P<type>\D+)(?P<num>\d+)')
        def refresh(self):
            """Refresh data."""
            osdata = self._get_os_devices()
            v4l2data = self._get_v4l2ctl_devices()
            vids = {d['path']: d for d in v4l2data['video']}
            for extrapath in set(osdata['video']).difference(vids):
                data[extrapath] = dict(
                    name='""', bus='', path=extrapath)
            for p in list(vids):
                if not self._isvid(p):
                    del vids[p]
            self.data = data = defaultdict(list)
            self.data['video'] = [
                Device(d['path'], (d['name'], d['bus'])) for d in vids.values()
            ]

        def _get_os_devices(self):
            data = defaultdict(set)
            for m in filter(None, map(Devices._osdevice.match, os.listdir('/dev'))):
                tp, num = m.groups()
                if tp == 'video':
                    data[tp].add(os.path.join('/dev', m.string))
            return data

        def _get_v4l2ctl_devices(self):
            p = sp.Popen(['v4l2-ctl', '--list-devices'], stdout=sp.PIPE)
            try:
                f = io.TextIOWrapper(p.stdout)
            except AttributeError:
                f = p.stdout
            h = Holder()
            data = defaultdict(list)
            for line in f:
                if h(Devices._v4l2ctl_header.match(line)):
                    indent, name, bus = h.r.groups()
                elif h(Devices._v4l2ctl_device.match(line)):
                    tp, num = h.r.groups()
                    data[tp].append(dict(name=name, bus=bus, path=line.strip()))
            if f is not p.stdout:
                f.detach()
            p.communicate()
            return data

        def _isvid(self, path):
            p = sp.Popen(['v4l2-ctl', '-D', '-d', path], stdout=sp.PIPE)
            try:
                f = io.TextIOWrapper(p.stdout)
            except AttributeError:
                f = p.stdout
            for line in f:
                stripped = line.lstrip()
                if stripped.startswith('Device Caps'):
                    indent = line[:len(line) - len(stripped)]
                    pat = re.compile(indent + r'\s+(?P<cap>.*)')
                    caps = set()
                    for match in filter(None, map(pat.match, f)):
                        caps.add(match.group('cap'))
                    return 'Video Capture' in caps
            return False

if __name__ == '__main__':
    devs = Devices()
    for tp, dev in devs:
        print('type:', tp, '| device:', dev)
        print(dev.get(size=(1920,1080)))
