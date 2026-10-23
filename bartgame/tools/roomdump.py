"""Render the room currently loaded in the emulator from RAM, using the art
sources, so a tile can be named by looking at it. Also prints the grid of
metatile names.

    import roomdump; roomdump.render(c, 'out.png')
    python3 tools/roomdump.py CELL OUT.png     boots and walks into the forest,
                                               teleports to the cell by index
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'art'))
from PIL import Image  # noqa: E402

import probe as P  # noqa: E402
import palettes  # noqa: E402
import tiles  # noqa: E402

BG = {n: c for n, c in palettes.BG_PALETTES}


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def render(c, out, scale=2):
    R = P.sym('gRoom')
    w, h = P.r8(c, R), P.r8(c, R + 1)
    im = Image.new('RGB', (w * 16 * scale, h * 16 * scale), (0, 0, 0))
    px = im.load()
    names = []
    for layer in (0, 1):
        base = R + 2 + layer * 2048
        for y in range(h):
            row = []
            for x in range(w):
                v = P.r16(c, base + (y * 32 + x) * 2) & 0xFFFF
                if v == 0xFFFF:
                    row.append('--')
                    continue
                m = tiles.METATILES[v]
                if layer == 0:
                    row.append(m['name'][:10])
                art = m.get('art') or m['frames'][0]
                pal = BG[m['pal']]
                for yy, r in enumerate(art):
                    for xx, ch in enumerate(r):
                        if ch in '. ' or (layer == 1 and ch == '0'):
                            continue
                        col = rgb(pal[int(ch, 16)])
                        for dy in range(scale):
                            for dx in range(scale):
                                px[(x * 16 + xx) * scale + dx, (y * 16 + yy) * scale + dy] = col
            if layer == 0:
                names.append(row)
    im.save(out)
    return names


if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else '/tmp/room.png'
    c = P.boot()
    P.run(c, 40)
    P.enter_forest(c)
    names = render(c, out)
    for row in names:
        print(' '.join('%-10s' % n for n in row))
    print('wrote', out)
