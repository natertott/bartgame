"""Render art to PNG so it can be looked at before it goes in the ROM.

    python3 tools/preview.py tiles OUT.png        every metatile, 4x
    python3 tools/preview.py sheet NAME OUT.png   one sprite sheet, 4x
    python3 tools/preview.py room NAME OUT.png    a hand-authored room, 2x
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'art'))
from PIL import Image  # noqa: E402

import palettes  # noqa: E402
import tiles  # noqa: E402
import sprites  # noqa: E402
import rooms  # noqa: E402

BG = {n: c for n, c in palettes.BG_PALETTES}
OBJ = {n: c for n, c in palettes.OBJ_PALETTES}


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def paint(im, x0, y0, rows, pal, scale):
    px = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in '. 0':
                continue
            c = rgb(pal[int(ch, 16)])
            for dy in range(scale):
                for dx in range(scale):
                    px[x0 + x * scale + dx, y0 + y * scale + dy] = c


def main():
    what = sys.argv[1]
    if what == 'tiles':
        out = sys.argv[2]
        n = len(tiles.METATILES)
        cols = 12
        rows_n = (n + cols - 1) // cols
        s = 4
        im = Image.new('RGB', (cols * 18 * s, rows_n * 18 * s), (60, 20, 60))
        for i, m in enumerate(tiles.METATILES):
            art = m.get('art') or m['frames'][0]
            paint(im, (i % cols) * 18 * s + s, (i // cols) * 18 * s + s, art, BG[m['pal']], s)
        im.save(out)
        print('\n'.join('%3d %s' % (i, m['name']) for i, m in enumerate(tiles.METATILES)))
    elif what == 'sheet':
        name, out = sys.argv[2], sys.argv[3]
        sh = next(s for s in sprites.SHEETS if s['name'] == name)
        s = 4
        names = list(sh['frames'])
        im = Image.new('RGB', (len(names) * (sh['w'] + 2) * s, (sh['h'] + 2) * s), (60, 20, 60))
        for i, fn in enumerate(names):
            paint(im, i * (sh['w'] + 2) * s + s, s, sh['frames'][fn], OBJ[sh['pal']], s)
        im.save(out)
        print(' '.join(names))
    elif what == 'room':
        name, out = sys.argv[2], sys.argv[3]
        r = next(x for x in rooms.ROOMS if x['name'] == name)
        mts = {m['name']: m for m in tiles.METATILES}
        s = 2
        im = Image.new('RGB', (r['w'] * 16 * s, r['h'] * 16 * s), (0, 0, 0))
        for layer in (r['ground'], r['overlay']):
            if not layer:
                continue
            for y, row in enumerate(layer):
                for x in range(r['w']):
                    mn = rooms.LEGEND[row[x * 2:x * 2 + 2]]
                    if mn is None:
                        continue
                    m = mts[mn]
                    art = m.get('art') or m['frames'][0]
                    paint(im, x * 16 * s, y * 16 * s, art, BG[m['pal']], s)
        im.save(out)


if __name__ == '__main__':
    main()
