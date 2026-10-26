"""Cut the painted hall (sw_hall.py) into metatiles for the build.

Each 16x16 cell of the ground and the overlay is read at every tick of
the animation clock. A cell that never changes is one frame; one that
does is stored with the fewest frames and the slowest speed that show
it exactly. Identical cells share a metatile. Each 8x8 quarter of a
cell takes one of the hand-set palettes (TEMPLATES), as the hardware
allows a palette per 8x8 piece; a quarter that fits none gives its
stray colours to the nearest ones of the template it is closest to,
and every such pixel is reported (REDUCED).

    sw_cut.cut(paint, ticks, types) -> metatiles, palettes, the two grids
"""
from sw_paint import COLORS

CELL = 16
MAX_PALS = 13
FRAME_TICK = 4          # frames per tick of the hall's clock


def _cell(cv, cx, cy):
    return tuple(tuple(cv.px[cy * CELL + j][cx * CELL:cx * CELL + CELL]) for j in range(CELL))


def _compress(frames, ticks):
    """the fewest frames and the slowest speed that replay a cell's ticks
    exactly: (frames, speed in game frames)"""
    if all(f == frames[0] for f in frames):
        return [frames[0]], 0
    for k in sorted({d for d in range(1, ticks + 1) if ticks % d == 0}, reverse=True):
        # the cell only changes on ticks that are multiples of k
        if all(frames[t] == frames[t - t % k] for t in range(ticks)):
            seq = [frames[i * k] for i in range(ticks // k)]
            n = len(seq)
            for p in range(1, n + 1):
                if n % p == 0 and all(seq[i] == seq[i % p] for i in range(n)):
                    return seq[:p], k * FRAME_TICK
    raise AssertionError('unreachable')


def _colors(frames):
    s = set()
    for f in frames:
        for row in f:
            s.update(c for c in row if c is not None)
    return s


# The hall's palettes, set by hand like a GBA artist's: each one a
# material and what it is painted against. Every 8x8 piece of the hall
# is drawn from one of them.
TEMPLATES = [
    # bricks, brass pipes and lanterns, posts on the coping
    ('wall', 'g0 g1 g2 g3 g4 g5 g6 b1 b2 b3 b4 b5 x y1 y2'),
    # dressed stone and water: the arch, the falls, the basin, the channel
    ('water', 'g0 g1 g2 g3 g4 g5 g6 a1 a2 a3 a4 a5 a6 a7 x'),
    # the floor, its moss, puddles and grates
    ('floor', 'g0 g1 g2 g3 g4 g5 g6 g7 m1 m2 m3 a2 a3 b3 b4'),
    # the far bank's railing stood over the water; the spouts pouring
    ('railwater', 'g0 g1 g2 g3 g4 a2 a3 a4 a5 a6 b1 b3 b4 b5 x'),
    # the Peddler's red: awning, counter, poles, coins
    ('red', 'g0 g1 g2 g3 d2 r1 r2 r3 r4 b3 b4 b5 d1 d3 d4'),
    # the Gatekeeper's purple: canopy, rug, banner
    ('purple', 'g0 g1 g2 g3 g4 g5 p1 p2 p3 p4 b3 b4 b5 d1 d3'),
    # teal and brass: the banner, the chest, a flask
    ('teal', 'g0 g1 g2 g3 g4 g5 a2 a3 a4 a5 b3 b4 b5 x d1'),
    # wood and bone: crates, barrels, a skull, the crow
    ('wood', 'g0 g1 g2 g3 g4 g5 d1 d2 d3 d4 b3 b4 k2 x y2'),
    # candles and flames on the floor and the wall
    ('flame', 'g0 g1 g2 g3 g4 g5 k2 x y1 y2 b2 b3 b4 d1 d3'),
    # books on their shelves
    ('books', 'g0 g1 g2 g3 d1 d2 d3 d4 r2 r3 a3 a4 p2 p3 b4'),
    # lily pads on the water, a pink bloom on one
    ('lily', 'g0 a1 a2 a3 a4 a5 a6 a7 x m1 m2 m3 lp'),
]
TEMPLATE_SETS = [(n, set(c.split())) for n, c in TEMPLATES]
for _n, _c in TEMPLATE_SETS:
    assert len(_c) <= 15, (_n, len(_c))


def fit(colors):
    """the template a set of colours fits, or the nearest one and the
    colours it must give up: (index, remap)"""
    for i, (n, t) in enumerate(TEMPLATE_SETS):
        if colors <= t:
            return i, {}
    best = None
    for i, (n, t) in enumerate(TEMPLATE_SETS):
        miss = colors - t
        remap = {c: min(t, key=lambda d: _dist(c, d)) for c in miss}
        err = sum(_dist(c, remap[c]) for c in miss)
        if best is None or err < best[0]:
            best = (err, i, remap)
    return best[1], best[2]


REDUCED = []


def _dist(a, b):
    ra, ga, ba = COLORS[a]
    rb, gb, bb = COLORS[b]
    return (ra - rb) ** 2 * 3 + (ga - gb) ** 2 * 4 + (ba - bb) ** 2 * 2


def _lum(name):
    r, g, b = COLORS[name]
    return 0.3 * r + 0.59 * g + 0.11 * b


QUARTERS = ((0, 0), (8, 0), (0, 8), (8, 8))


def cut(paint, ticks, types, prefix='swh_', pal_prefix='sw_pal'):
    """paint(t) -> (ground, overlay) canvases; types(cx, cy) -> (type, coll).
    Each 8x8 quarter of a cell takes a palette of its own, as the
    hardware allows: the quarters' colours are what is packed."""
    g0, _ = paint(0)
    W, H = g0.w // CELL, g0.h // CELL
    layers = [[], []]
    for t in range(ticks):
        g, o = paint(t)
        layers[0].append(g)
        layers[1].append(o)
    cells = []   # (layer, cx, cy, frames, speed)
    for li in (0, 1):
        for cy in range(H):
            for cx in range(W):
                fr = [_cell(layers[li][t], cx, cy) for t in range(ticks)]
                seq, speed = _compress(fr, ticks)
                if li == 1 and all(c is None for f in seq for row in f for c in row):
                    continue
                if li == 0:
                    assert all(c is not None for f in seq for row in f for c in row), ('a hole in the ground at', cx, cy)
                cells.append((li, cx, cy, seq, speed))
    REDUCED.clear()
    # each quarter takes the template its colours fit; one that fits none
    # gives its strays to the nearest template's colours (reported)
    where = []
    for k, (li, cx, cy, seq, speed) in enumerate(cells):
        seq = [list(list(r) for r in f) for f in seq]
        for q in range(4):
            x0, y0 = QUARTERS[q]
            cols = set()
            for f in seq:
                for row in f[y0:y0 + 8]:
                    cols.update(c for c in row[x0:x0 + 8] if c is not None)
            ti, remap = fit(cols)
            if remap:
                n = 0
                for f in seq:
                    for row in f[y0:y0 + 8]:
                        for x in range(x0, x0 + 8):
                            if row[x] in remap:
                                row[x] = remap[row[x]]
                                n += 1
                REDUCED.append(((li, cx * CELL + x0, cy * CELL + y0), TEMPLATE_SETS[ti][0], remap, n))
            where.append(ti)
        cells[k] = (li, cx, cy, [tuple(tuple(r) for r in f) for f in seq], speed)
    used = sorted(set(where))
    assert len(used) <= MAX_PALS, ('%d palettes needed' % len(used))
    where = [used.index(w) for w in where]
    pals = [TEMPLATE_SETS[u][1] for u in used]
    pal_lists = [sorted(p, key=_lum) for p in pals]
    pal_index = [{c: i + 1 for i, c in enumerate(pl)} for pl in pal_lists]
    palettes = []
    for k, pl in enumerate(pal_lists):
        hexes = ['#%02x%02x%02x' % COLORS[pl[0]]] + ['#%02x%02x%02x' % COLORS[c] for c in pl]
        hexes += ['#000000'] * (16 - len(hexes))
        palettes.append(('%s_%s' % (pal_prefix, TEMPLATE_SETS[used[k]][0]), hexes))
    metatiles = []
    seen = {}
    grids = [[[None] * W for _ in range(H)], [[None] * W for _ in range(H)]]
    for k, (li, cx, cy, seq, speed) in enumerate(cells):
        qp = [where[4 * k + q] for q in range(4)]
        rows = []
        for f in seq:
            fr = []
            for y in range(CELL):
                line = ''
                for x in range(CELL):
                    c = f[y][x]
                    q = (1 if x >= 8 else 0) + (2 if y >= 8 else 0)
                    line += '%x' % (0 if c is None else pal_index[qp[q]][c])
                fr.append(line)
            rows.append(tuple(fr))
        rows = tuple(rows)
        if li == 0:
            ty, coll = types(cx, cy)
        else:
            ty, coll = 'FLOOR', 0
        key = (tuple(qp), rows, ty, coll, speed)
        if key not in seen:
            name = '%s%03d' % (prefix, len(metatiles))
            d = {'name': name, 'pal': palettes[qp[0]][0], 'qpals': [palettes[p][0] for p in qp],
                 'type': ty, 'coll': coll}
            if len(rows) > 1:
                d['frames'] = [list(r) for r in rows]
                d['anim_speed'] = speed
            else:
                d['art'] = list(rows[0])
            metatiles.append(d)
            seen[key] = name
        grids[li][cy][cx] = seen[key]
    return {'metatiles': metatiles, 'palettes': palettes, 'ground': grids[0], 'overlay': grids[1],
            'cells': cells, 'w': W, 'h': H, 'quarter_palettes': where}


def pieces(metatiles):
    """how many 8x8 pieces the build will need: static ones deduplicated
    with flips, animated ones four each"""
    seen = set()
    n = 1  # the blank
    seen.add(tuple(['0' * 8] * 8))
    for m in metatiles:
        if 'frames' in m:
            n += 4
            continue
        rows = m['art']
        for (x0, y0) in ((0, 0), (8, 0), (0, 8), (8, 8)):
            q = tuple(r[x0:x0 + 8] for r in rows[y0:y0 + 8])
            forms = {q, tuple(r[::-1] for r in q), q[::-1], tuple(r[::-1] for r in q[::-1])}
            if not (forms & seen):
                seen.add(q)
                n += 1
    return n
