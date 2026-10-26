"""Preview the Drain's hall as painted (art/sw_hall.py), before it is cut
into metatiles, at 3x, with optional crops.

    python3 tools/sw_preview.py OUT.png [--tick T] [--scale 3] [--crop x,y,w,h] [--grid]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'art'))
from PIL import Image  # noqa: E402

import sw_hall  # noqa: E402

args = sys.argv[1:]


def opt(name, default):
    if name in args:
        i = args.index(name)
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return default


tick = int(opt('--tick', 0))
scale = int(opt('--scale', 3))
crop = opt('--crop', None)
grid = '--grid' in args
if grid:
    args.remove('--grid')
g, o = sw_hall.paint(tick)
im = g.to_image()
im.alpha_composite(o.to_image())
if crop:
    x, y, w, h = (int(v) for v in crop.split(','))
    im = im.crop((x, y, x + w, y + h))
im = im.convert('RGB').resize((im.width * scale, im.height * scale), Image.NEAREST)
if grid:
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if (x // scale) % 16 == 0 and x % scale == 0 or (y // scale) % 16 == 0 and y % scale == 0:
                r, gg, b = px[x, y]
                px[x, y] = (min(255, r + 60), gg, b)
im.save(args[0])
print('wrote', args[0], im.size)
