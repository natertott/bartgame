"""An independent compositor: draw a scene's room straight from the art pack's
PNG files and a layout.json (tools/golden_capture.py), with none of the
game's import, tile or palette code, so its output can be held against the
engine's capture of the same scene.

    python3 tools/compose_frame.py LAYOUT.json PACKDIR OUT.png [--ground-only]

PACKDIR is the pack as delivered (art/ref/pack_v3). Each cell takes its
pack file's tile at the layout's frame; ground first, the overlay over it
(transparent where the PNG is), scrolled by the layout's camera. Colours
are brought to the hardware's 5 bits a channel and back the way mGBA
shows them, so an exact match is possible.
"""
import json
import os
import sys

from PIL import Image

layout = json.load(open(sys.argv[1]))
PACK = sys.argv[2]
OUT = sys.argv[3]
ground_only = '--ground-only' in sys.argv
manifest = {a['key']: a for a in json.load(open(os.path.join(PACK, 'manifest.json')))['assets']}


def hw(p):
    """8-bit RGB through BGR555, as the GBA stores it and mGBA shows it"""
    return tuple(((v >> 3) << 3) | ((v >> 3) >> 2) for v in p[:3])


def cols_rows(a, key):
    fw, fh = a['frame_width'], a['frame_height']
    return fw // 16, fh // 16


_img = {}


def tile(cell):
    """the cell's 16x16 RGBA from its pack file, at the frame shown"""
    key = cell['pack_key']
    a = manifest[key]
    if key not in _img:
        _img[key] = Image.open(os.path.join(PACK, cell['pack_file'])).convert('RGBA')
    im = _img[key]
    cols, rows = cols_rows(a, key)
    t = cell['tile']
    c, r = t % cols, t // cols
    f = cell['frame_shown'] % a['frame_count']
    return im.crop((c * 16, f * a['frame_height'] + r * 16, c * 16 + 16, f * a['frame_height'] + r * 16 + 16))


cx, cy = layout['camera_px']
out = Image.new('RGB', (240, 160), (0, 0, 0))
px = out.load()
missing = set()
for layer in ('ground', 'overlay'):
    if ground_only and layer == 'overlay':
        continue
    for cell in layout['cells']:
        cl = cell[layer]
        if not cl:
            continue
        if not cl['pack_key']:
            missing.add(cl['metatile'])
            continue
        t = tile(cl).load()
        for y in range(16):
            for x in range(16):
                sx, sy = cell['x'] * 16 + x - cx, cell['y'] * 16 + y - cy
                if not (0 <= sx < 240 and 0 <= sy < 160):
                    continue
                p = t[x, y]
                if p[3] == 0:
                    continue
                px[sx, sy] = hw(p)
out.save(OUT)
print('composed %s from %d cells%s' % (OUT, len(layout['cells']), ('; no pack art for ' + ', '.join(sorted(missing))) if missing else ''))
