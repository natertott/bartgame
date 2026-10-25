"""Render the current art of every tile spec entry, and check that the
entries cover every tile the game places.

    cd bartgame && python3 tools/tile_spec/render.py OUTDIR
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, 'art')
from PIL import Image  # noqa: E402

import palettes  # noqa: E402
import tiles  # noqa: E402
import rooms  # noqa: E402
import spec_data as D  # noqa: E402

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
MT = {m['name']: m for m in tiles.METATILES}
PAL = {n: c for n, c in palettes.BG_PALETTES}
BACKDROP = PAL['forest'][0]
OVERLAY = set(['sparkle', 'sparkle_white', 'blight_mist', 'myst_switch', 'myst_switch_down', 'myst_pot',
               'myst_chest', 'myst_chest_open', 'myst_spring', 'sw_glint', 'sw_glint2', 'sw_glint3',
               'tree_top_nw', 'tree_top_ne', 'tree_mid_w', 'tree_mid_e'] +
              ['tree2_%d' % i for i in range(4)] + ['btree_%d' % i for i in range(4)] +
              ['gtree_%d' % i for i in range(9)] + ['gtree2_%d' % i for i in range(9)])


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def frames_of(name):
    m = MT[name]
    return m.get('frames') or [m['art']]


def tile_img(name, f):
    fr = frames_of(name)
    rows = fr[min(f, len(fr) - 1)]
    pal = PAL[MT[name]['pal']]
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in '. 0':
                if name not in OVERLAY:
                    px[x, y] = rgb(BACKDROP) + (255,)
                continue
            px[x, y] = rgb(pal[int(ch, 16)]) + (255,)
    return im


def checker(w, h, s=4):
    im = Image.new('RGBA', (w, h), (205, 196, 210, 255))
    px = im.load()
    for y in range(h):
        for x in range(w):
            if ((x // s) + (y // s)) % 2:
                px[x, y] = (232, 226, 236, 255)
    return im


def grid(e):
    sh = e['shape']
    m = e['mts']
    if sh[0] == 'piece':
        c, r = sh[1], sh[2]
        return [m[i * c:(i + 1) * c] for i in range(r)]
    return [m]


def render(e, scale=3, gap=2):
    g = grid(e)
    nf = max(len(frames_of(n)) for n in e['mts'])
    cols, rows = len(g[0]), len(g)
    # a family or a set of variants gets a hairline gap between tiles; a piece is whole
    tg = gap if e['shape'][0] in ('vars', 'fam') else 0
    W = cols * 16 + (cols - 1) * tg
    H = rows * 16
    fg = 4
    sheet = Image.new('RGBA', (W, nf * H + (nf - 1) * fg), (0, 0, 0, 0))
    for f in range(nf):
        y0 = f * (H + fg)
        sheet.alpha_composite(checker(W, H), (0, y0))
        for r, line in enumerate(g):
            for c, n in enumerate(line):
                sheet.alpha_composite(tile_img(n, f), (c * (16 + tg), y0 + r * 16))
    return sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST), nf


def area_sections():
    return [('wood', D.WOOD), ('myst', D.MYST), ('drain', D.DRAIN)]


# ---------------------------------------------------------------- render
seen = {}
for area, secs in area_sections():
    for title, intro, entries in secs:
        for e in entries:
            for n in e['mts']:
                assert n in MT, ('no metatile', n)
                assert n not in seen, ('twice', n, seen.get(n), e['key'])
                seen[n] = e['key']
            im, nf = render(e)
            e['current_frames'] = nf
            im.save(os.path.join(OUT, e['key'] + '.png'))

# --------------------------------------------------------------- coverage
names = [m['name'] for m in tiles.METATILES]
mt_names = {n: i for i, n in enumerate(names)}
hub = set()
for r in rooms.ROOMS:
    for layer in ('ground', 'overlay'):
        if r.get(layer):
            hub |= set(names[i] for i in rooms.expand(r[layer], r['w'], r['h'], mt_names) if i != 0xFFFF)
NEVER = {'moss_shade', 'relic', 'fence', 'pit_inner', 'ledge_n', 'path_edge_n', 'sw_floor_slime', 'sw_ladder', 'black'}
# floors that carry a switch, a pot or a chest reuse the plain floor's drawing
ALIAS = {'%s_floor_%s' % (st, k) for st in ('cave', 'hollow', 'thicket') for k in ('switch', 'lift', 'chest')}
placed = set()
for n in names:
    if n.startswith('sw_'):
        if n in hub:
            placed.add(n)
    elif n not in NEVER and n not in ALIAS:
        placed.add(n)
missing = sorted(placed - set(seen))
extra = sorted(set(seen) - placed)
print('entries cover %d tiles; placed %d; missing %s; extra %s' % (len(seen), len(placed), missing, extra))
assert not missing and not extra
