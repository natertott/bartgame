"""The living wood, the blight's floors and the mystery rooms, drawn with
the terrain painter (paint.py) in hand-built palettes.

The palettes are ramps with their shadows cooler and their highlights
warmer. Groups that meet across a tile edge share exact colours: the
leaf darks are in the grass group (a verge's overhang), the grass is in
the leaf group (a crown's foot), the soil is in the water group (a
bank's lip), so a transition drawn on one tile matches the tile beside
it. The walls are darker and cooler than the floors they stand on, and
the floors are low in contrast, so what can be walked on reads at once.

apply() replaces the art of the metatiles drawn here, by name; it is
called after the tile atlases (tile_art.py)."""
import numpy as np

import paint as P

# ----------------------------------------------------------------- colours --
# One table of named colours. Tiles are drawn in them; each palette group
# is then the colours its tiles use (at most 15, checked), so a colour two
# groups share is the very same in both.
COLORS = [
    ('outline', '#0a1510'),
    ('leaf_deep', '#12261d'), ('shadow', '#1b3826'), ('leaf_md', '#255030'), ('leaf_mid', '#33683a'),
    ('leaf_lt', '#478545'), ('leaf_br', '#66a24e'), ('leaf_hl', '#93c45e'),
    ('grass_d', '#2f5a30'), ('grass_m', '#3d6e35'), ('grass_l', '#52873d'), ('grass_b', '#6ea047'), ('grass_t', '#9cc45a'),
    ('soil', '#3b2a1c'), ('trail_d', '#6b4e2e'), ('trail_m', '#8f6c3e'), ('trail_l', '#b08b52'), ('trail_h', '#d0b377'),
    ('white', '#ece6c8'), ('yellow', '#e7bb4c'), ('blue', '#8fa6e6'),
    ('bark_dk', '#2b1c12'), ('bark', '#4a3220'), ('bark_l', '#6d4b2c'), ('bark_ll', '#8f6a3e'), ('wood_cut', '#c09a62'),
    ('amber', '#d9902e'), ('glow', '#ffd877'),
    ('water_deep', '#0e2a3a'), ('water_dk', '#133d52'), ('water_md', '#1b5468'), ('water_mid', '#26707e'),
    ('water_lt', '#3b8f98'), ('ripple', '#6cc0c0'), ('foam', '#c8f0ec'),
    ('lily', '#2f6a34'), ('lily_l', '#58a04a'), ('lily_flower', '#e9e3d0'),
    ('stone_0', '#232a30'), ('stone_1', '#3a444a'), ('stone_2', '#566166'), ('stone_3', '#7a8584'), ('stone_4', '#a7b0aa'),
    ('silk', '#d6dccf'), ('gold_l', '#fff0a0'),
    ('thorn', '#b03a7a'), ('thorn_vine', '#2a1a2a'), ('berry', '#c0404a'),
    # the blight: its stains on the living grass, its earth, its leaves
    ('v_0', '#1a1222'), ('v_1', '#2a1e36'), ('v_2', '#3c2a4a'), ('v_3', '#54386a'), ('v_4', '#73508a'),
    ('mag_d', '#7a2a86'), ('mag', '#b44ac0'), ('mag_l', '#e88af0'),
    ('sick_d', '#3a4a34'), ('sick_m', '#4e5c40'), ('sick_l', '#626c4c'),
    ('cave_glow', '#4fc8c0'), ('cave_glow_l', '#b4fff2'),
    ('bt_o', '#180527'), ('bt_d', '#513461'), ('bt_m', '#732483'), ('bt_l', '#9a3b76'), ('bt_g', '#d733cc'),
    ('earth_0', '#241e2a'), ('earth_1', '#352d3a'), ('earth_2', '#463c4a'), ('earth_3', '#564b5a'),
    ('earth_4', '#6a5d6c'), ('earth_5', '#80728a'), ('earth_6', '#9a8ca2'),
    ('bl_deep', '#141024'), ('bl_dk', '#1e1838'), ('bl_md', '#2a2450'), ('bl_mid', '#383268'),
    ('bl_lt', '#4a4686'), ('bl_br', '#6260a4'), ('bl_hl', '#8a84c8'),
]
ID = {n: i + 1 for i, (n, _) in enumerate(COLORS)}
HEX = {i + 1: h for i, (_, h) in enumerate(COLORS)}


def C(*names):
    return tuple(ID[n] for n in names)


# roles, for the drawing code
G = dict(o=ID['outline'], sh=ID['shadow'], d=ID['grass_d'], m=ID['grass_m'], l=ID['grass_l'], b=ID['grass_b'],
         t=ID['grass_t'], soil=ID['soil'], td=ID['trail_d'], tm=ID['trail_m'], tl=ID['trail_l'], th=ID['trail_h'],
         white=ID['white'], yellow=ID['yellow'], blue=ID['blue'])
L = dict(o=ID['outline'], deep=ID['leaf_deep'], dk=ID['shadow'], md=ID['leaf_md'], mid=ID['leaf_mid'], lt=ID['leaf_lt'],
         br=ID['leaf_br'], hl=ID['leaf_hl'], bkd=ID['bark_dk'], bk=ID['bark'], bkl=ID['bark_l'], amber=ID['amber'],
         glow=ID['glow'], gm=ID['grass_m'], gl=ID['grass_l'])
WA = dict(o=ID['outline'], deep=ID['water_deep'], dk=ID['water_dk'], md=ID['water_md'], mid=ID['water_mid'],
          lt=ID['water_lt'], rip=ID['ripple'], foam=ID['foam'], soil=ID['soil'], bank=ID['trail_d'], pl=ID['trail_m'],
          pll=ID['trail_l'], lily=ID['lily'], lilyl=ID['lily_l'], flower=ID['lily_flower'])
S = dict(o=ID['outline'], s0=ID['stone_0'], s1=ID['stone_1'], s2=ID['stone_2'], s3=ID['stone_3'], s4=ID['stone_4'])
STONE = C('outline', 'stone_1', 'stone_2', 'stone_3', 'stone_4')
STONE_DK = C('outline', 'stone_0', 'stone_1', 'stone_2', 'stone_3')
BARK = C('outline', 'bark_dk', 'bark', 'bark_l', 'bark_ll')


# ------------------------------------------------------------------ grass --
TUFTS = [
    # a tuft is a few blades: 't' tip, 'b' bright, 'l' light, 'd' its dark root
    ['t.t', '.b.', '.d.'],
    ['.t', 'tb', 'ld'],
    ['t.', 'bt', 'dl'],
    ['.t.', 'blb', '.d.'],
]


def grass(seed, tufts=5):
    """the wood's grass: one calm mid green with a fine, even texture of
    blade shadows and lit tips, and a few tufts kept inside the tile, so
    the variants meet each other without a seam"""
    r = P.rng(seed * 101 + 7)
    img = np.full((16, 16), G['m'], np.uint8)
    # blade shadows: short dark dashes, evenly spread
    for (x, y) in P.scatter(seed * 5 + 2, 14, mind=3):
        img[y, x] = G['d']
        if r.rand() < 0.5:
            img[y, (x + 1) % 16] = G['d']
    # lit tips
    for (x, y) in P.scatter(seed * 5 + 3, 9, mind=3, avoid=img == G['d']):
        img[y, x] = G['l']
    roles = dict(t=G['b'], b=G['l'], l=G['l'], d=G['d'])
    inner = np.zeros((16, 16), bool)
    inner[1:13, 1:13] = True
    for i, (x, y) in enumerate(P.scatter(seed * 13 + 1, tufts, mind=6, avoid=~inner)):
        P.stamp(img, x, y, TUFTS[(seed + i) % len(TUFTS)], roles)
    return img


def trail(seed):
    """packed earth: warm, a lighter crown worn by feet, a few pebbles"""
    f = P.fbm(16, 16, seed + 100, ((2, 0.6), (4, 0.4)))
    img = P.levels(f, [G['td'], G['tm'], G['tl']], [0.22, 0.78], soft=0.1).astype(np.uint8)
    for (x, y) in P.scatter(seed * 7 + 3, 2, mind=7):
        P.stamp(img, x, y, ['l', 'd'], dict(l=G['th'], d=G['td']))
    return img


def grass_on(img, mask, seed):
    """grass drawn into the masked part of an image, matching grass(0)"""
    g = grass(0)
    img[mask] = g[mask]
    return img


def trail_edges():
    """the trail with the grass creeping over it on the marked sides: the
    grass's edge ragged with tufts, a dark lip under it on the trail"""
    base = trail(0)
    g = grass(0)
    masks = P.side_masks(41, lo=2, hi=5, round_r=2)
    out = {}
    for bits, m in masks.items():
        img = base.copy()
        img[m] = g[m]
        inner, outer = P.edge_ring(m)
        img[inner] = G['d']          # the grass's rim, darker
        img[outer] = G['soil']       # its shadow on the earth
        # a few blades over the line
        for (x, y) in P.scatter(bits * 11 + 7, 6, mind=3, avoid=~inner):
            if 0 <= y - 1 < 16 and not m[y - 1, x]:
                img[y - 1, x] = G['l']
        out[bits] = img
    return out


def trail_corners():
    """the trail with grass only at the marked corners: a rounded tongue
    of grass, its rim and its shadow as on the trail's edges"""
    base = trail(0)
    g = grass(0)
    out = {}
    for bits, (m, u) in P.nick_fields(43, r=4).items():
        img = base.copy()
        img[m] = g[m]
        inner, outer = P.edge_ring(m)
        img[inner] = G['d']
        img[outer] = G['soil']
        out[bits] = img
    return out


# ----------------------------------------------------------------- canopy --
LEAF_RAMP = (L['o'], L['dk'], L['md'], L['lt'], L['br'])
LEAF_RAMP2 = (L['o'], L['dk'], L['mid'], L['lt'], L['hl'])


CANOPY_A = (L['deep'], L['dk'], L['md'], L['mid'], L['lt'])
CANOPY_B = (L['deep'], L['dk'], L['mid'], L['lt'], L['br'])


def leaf_mass(seed, n=11):
    """the canopy: overlapping clumps of leaves of several sizes, lit from
    the upper left, their rims in the deepest green rather than a black
    line, on a torus so the wall is one mass with no grid in it"""
    img = np.full((16, 16), L['dk'], np.uint8)
    pts = P.scatter(seed * 3 + 11, n, mind=4)
    r = P.rng(seed * 3 + 12)
    for i, (x, y) in enumerate(sorted(pts, key=lambda q: q[1])):
        rad = 3.4 + r.rand() * 2.6
        P.clump(img, x + 0.5, y + 0.5, rad, CANOPY_A if r.rand() < 0.55 else CANOPY_B, wrap=True, rough=0.16, seed=seed * 50 + i)
    # leaves catching the light, a few
    for (x, y) in P.scatter(seed * 3 + 13, 4, mind=5, avoid=img != L['lt']):
        img[y, x] = L['br']
    return img


def canopy_face(seed=0):
    """the wall's lower edge: the leaves above, their scalloped hem, deep
    shade under it, trunks going down to the ground"""
    img = leaf_mass(seed)
    img[9:, :] = L['deep']
    r = P.rng(seed + 77)
    # trunks in the shade
    for x0 in (2, 10):
        x0 += r.randint(-1, 2)
        img[10:16, x0:x0 + 3] = L['bk']
        img[10:16, x0] = L['bkl']
        img[10:16, x0 + 2] = L['bkd']
    # the hem: clumps whose lower halves overhang the shade
    for i, x in enumerate(range(1, 17, 5)):
        P.clump(img, x + 0.5, 8.0 + (i % 2), 3.2, LEAF_RAMP2 if i % 2 else LEAF_RAMP, wrap=True, rough=0.1, seed=seed + i)
    # the ground at the foot, in shade, roots on it
    img[15, :] = P.dither(np.full((1, 16), 0.35), L['dk'], L['gm'])[0]
    img[14, :] = np.where(img[14, :] == L['deep'], L['dk'], img[14, :])
    return img


def canopy_crown(seed=1):
    """the wall's upper edge: the ground above, the lit tops of the clumps"""
    img = leaf_mass(seed)
    top = np.zeros((16, 16), bool)
    top[:6, :] = True
    img[top] = L['gm']
    img[0:2, :] = P.dither(np.full((2, 16), 0.25), L['gm'], L['gl'])
    for i, x in enumerate(range(2, 18, 5)):
        P.clump(img, x + 0.5, 7.2 - (i % 2), 3.4, LEAF_RAMP2, wrap=True, rough=0.1, seed=seed * 9 + i)
    return img


def canopy_glint():
    a = leaf_mass(0)
    b = a.copy()
    for (x, y) in ((4, 5), (11, 10)):
        if b[y, x] in (L['lt'], L['br'], L['mid']):
            b[y, x] = L['hl']
            b[y - 1, x] = L['br']
    return [a, b]


def canopy_lantern():
    """a small lantern hung in the leaves; its glow flickers"""
    base = leaf_mass(1)
    frames = []
    for k in range(2):
        img = base.copy()
        img[2:6, 7] = L['bkd']                      # its chain
        img[6:11, 6:10] = L['bkd']                  # the cage
        img[7:10, 7:9] = L['glow'] if k == 0 else L['amber']
        img[6, 6] = img[6, 9] = img[10, 6] = img[10, 9] = L['o']
        img[11, 7:9] = L['bkd']
        for (x, y) in ((5, 8), (10, 8), (7, 5), (8, 12)):
            if k == 0:
                img[y, x] = L['amber']
        frames.append(img)
    return frames


# ------------------------------------------------------------------ verges --
def verges():
    """grass beside the canopy: shade and leaf litter under a wall to the
    north; to the east or west the leaves hang over it in small clumps; a
    wall to the south (its crown) has a few dark ferns at its foot"""
    base = grass(0)
    fields = P.band_fields(45, lo=2, hi=5, r=2)
    out = {}
    leaf = (G['o'], G['sh'], G['d'], G['d'], G['m'])
    for bits, (m, u) in fields.items():
        img = base.copy()
        # shade, deepest at the wall
        sh = np.clip(1.0 - u, 0, 1)
        shade = P.dither(sh * 1.4, G['m'], G['d'])
        img = np.where(m, shade, img)
        img = np.where(m & (u < 0.4), P.dither(np.clip(0.4 - u, 0, 1) * 3, G['d'], G['sh']), img)
        # the leaves hanging over from the east and west
        for side, ex in ((2, 16.0), (8, 0.0)):
            if bits & side:
                for i, y in enumerate((2, 8, 13)):
                    P.clump(img, ex, y + 0.5, 2.6 + (i % 2) * 0.6, leaf, wrap=False, rough=0.15, seed=side * 10 + i)
        if bits & 1:
            for i, x in enumerate((3, 11)):
                P.clump(img, x + 0.5, -0.6, 2.2, leaf, wrap=False, rough=0.15, seed=30 + i)
        out[bits] = img
    return out


def verge_corners():
    base = grass(0)
    out = {}
    leaf = (G['o'], G['sh'], G['d'], G['d'], G['m'])
    for bits, (m, u) in P.nick_fields(47, r=5).items():
        img = base.copy()
        img = np.where(m, P.dither(np.clip(1 - u, 0, 1) * 1.4, G['m'], G['d']), img)
        for b, (cx, cy) in ((1, (0, 0)), (2, (16, 0)), (4, (16, 16)), (8, (0, 16))):
            if bits & b:
                P.clump(img, cx, cy, 2.8, leaf, wrap=False, rough=0.15, seed=b)
        out[bits] = img
    return out


# ------------------------------------------------------------------- water --
def water(seed, frame):
    """open water: deep and calm, a few short ripples of light that drift
    between the two frames"""
    f = P.fbm(16, 16, 300 + seed, ((2, 0.6), (4, 0.4)))
    img = P.levels(f, [WA['dk'], WA['md']], [0.45], soft=0.12).astype(np.uint8)
    for i, (x, y) in enumerate(P.scatter(400 + seed, 5, mind=5)):
        x = (x + frame * 2) % 16
        n = 2 + (i % 2)
        for k in range(n):
            img[y, (x + k) % 16] = WA['lt'] if k in (0, n - 1) else WA['rip']
    return img


def water_banks():
    """water with a bank on the marked sides: a broken line of foam at the
    bank, dark water in the bank's shade, then the open water"""
    fields = P.band_fields(49, lo=3, hi=5, r=2)
    out = {}
    for bits, (m, u) in fields.items():
        frames = []
        for fr in range(2):
            img = water(0, fr)
            img = np.where(m & (u < 1.0), P.dither(np.clip(1.0 - u, 0, 1) * 1.6, WA['md'], WA['dk']), img)
            img = np.where(m & (u < 0.5), WA['deep'], img)
            # a light rim at the bank, a few flecks of foam on it
            rim = m & (u < 0.2)
            fz = P.dither(np.full((16, 16), 0.22), WA['lt'], WA['foam'], ox=fr * 2)
            img = np.where(rim, fz, img)
            frames.append(img)
        out[bits] = frames
    return out


def water_nicks():
    out = {}
    for bits, (m, u) in P.nick_fields(51, r=5).items():
        frames = []
        for fr in range(2):
            img = water(0, fr)
            img = np.where(m, P.dither(np.clip(1.0 - u, 0, 1) * 1.6, WA['md'], WA['dk']), img)
            img = np.where(m & (u < 0.5), WA['deep'], img)
            img = np.where(m & (u < 0.2), P.dither(np.full((16, 16), 0.22), WA['lt'], WA['foam'], ox=fr * 2), img)
            frames.append(img)
        out[bits] = frames
    return out


def lily_pad(img, cx, cy, r, flower=True):
    pad = (WA['o'], WA['lily'], WA['lily'], WA['lilyl'], WA['lilyl'])
    m = P.clump(img, cx, cy, r, pad, ry=r * 0.8)
    # the notch
    img[int(cy), int(cx):int(cx + r)] = WA['lily']
    if flower:
        img[int(cy) - 1, int(cx) - 1] = WA['flower']
        img[int(cy) - 1, int(cx)] = WA['foam']
    return m


def water_lily():
    frames = []
    for fr in range(2):
        img = water(1, fr)
        lily_pad(img, 8.0, 8.5 + fr * 0.0, 4.2)
        frames.append(img)
    return frames


def raft():
    frames = []
    for fr in range(2):
        img = np.concatenate([np.concatenate([water(2, fr), water(3, fr)], axis=1),
                              np.concatenate([water(4, fr), water(5, fr)], axis=1)], axis=0)
        for (x, y, r, fl) in ((10, 11, 6.0, True), (22, 9, 5.0, False), (12, 23, 5.2, False), (23, 22, 6.2, True), (17, 16, 4.0, False)):
            lily_pad(img, x + 0.5, y + 0.5, r, fl)
        frames.append(img)
    return [[P.slice16(f, i % 2, i // 2) for f in frames] for i in range(4)]


def waterfall():
    """water falling: streaks of light pouring down, three frames scrolling
    a third of a tile each, so it loops"""
    base = np.full((16, 16), WA['mid'], np.uint8)
    r = P.rng(55)
    for x in range(16):
        if r.rand() < 0.35:
            base[:, x] = WA['md']
    streak = np.zeros((16, 16), np.uint8)
    for x in range(0, 16, 2):
        y0 = r.randint(16)
        ln = 4 + r.randint(6)
        for k in range(ln):
            streak[(y0 + k) % 16, (x + r.randint(2)) % 16] = WA['rip'] if k < ln - 1 else WA['foam']
    frames = []
    for fr in range(3):
        img = base.copy()
        sh = np.roll(streak, fr * 5, axis=0)
        img = np.where(sh > 0, sh, img)
        frames.append(img)
    return frames


def foam():
    frames = []
    for fr in range(2):
        img = water(6, fr)
        f = P.fbm(16, 16, 610 + fr, ((4, 0.6), (8, 0.4)))
        yy = np.arange(16)[:, None] / 16.0
        dens = np.clip(1.1 - yy * 1.1 + (f - 0.5) * 0.6, 0, 1)
        img = np.where(dens > 0.55, P.dither(dens, WA['rip'], WA['foam'], ox=fr), np.where(dens > 0.3, WA['lt'], img))
        frames.append(img)
    return frames


def bridge(vertical=False):
    """plank boards across the water, a rail along each side, the water
    showing past the rails"""
    img = np.full((16, 16), WA['md'], np.uint8)
    img[0:2, :] = P.dither(np.full((2, 16), 0.5), WA['dk'], WA['md'])
    img[15, :] = WA['deep']
    img[2, :] = WA['o']
    img[3, :] = WA['pll']
    img[4, :] = WA['soil']
    for x in range(16):
        col = WA['pl'] if (x // 4) % 2 == 0 else WA['bank']
        img[5:12, x] = col
        if x % 4 == 0:
            img[5:12, x] = WA['pll'] if (x // 4) % 2 == 0 else WA['pl']
        if x % 4 == 3:
            img[5:12, x] = WA['soil']
    img[12, :] = WA['soil']
    img[13, :] = WA['pll']
    img[14, :] = WA['o']
    for x in (1, 9):
        img[7, x] = WA['soil']
        img[10, x + 2] = WA['soil']
    return img.T.copy() if vertical else img


# ------------------------------------------------------------------ shores --
def shores():
    """grass beside water on the marked sides: grass to a strip of sand,
    a line of dark wet soil at the water, a few reeds"""
    base = grass(0)
    out = {}
    for bits, (m, u) in P.band_fields(49, lo=3, hi=5, r=2).items():
        img = base.copy()
        img = np.where(m & (u < 1.0), P.dither(np.clip(1.15 - u, 0, 1) * 1.5, G['l'], G['th']), img)
        img = np.where(m & (u < 0.62), P.dither(np.full((16, 16), 0.45), G['th'], G['tl']), img)
        img = np.where(m & (u < 0.3), G['soil'], img)
        out[bits] = img
    return out


def shore_corners():
    base = grass(0)
    out = {}
    for bits, (m, u) in P.nick_fields(51, r=5).items():
        img = base.copy()
        img = np.where(m, P.dither(np.clip(1.15 - u, 0, 1) * 1.5, G['l'], G['th']), img)
        img = np.where(m & (u < 0.62), P.dither(np.full((16, 16), 0.45), G['th'], G['tl']), img)
        img = np.where(m & (u < 0.3), G['soil'], img)
        out[bits] = img
    return out


# ------------------------------------------------------- the grass's accents --
def flowers(seed, col, n=5):
    img = grass(0).copy()
    for (x, y) in P.scatter(seed, n, mind=4, avoid=~P.disc(16, 16, 8, 8, 6.5)):
        P.stamp(img, x - 1, y - 1, ['.c.', 'cyc', '.d.'], dict(c=col, y=G['yellow'] if col != G['yellow'] else G['white'], d=G['d']))
    return img


def tall_grass():
    img = grass(0).copy()
    blades = ['t.t.t', 'btbtb', 'lblbl', 'dldld', '.ddd.']
    P.stamp(img, 2, 6, blades, dict(t=G['t'], b=G['b'], l=G['l'], d=G['d']))
    P.stamp(img, 8, 3, blades, dict(t=G['t'], b=G['b'], l=G['l'], d=G['d']))
    P.stamp(img, 7, 9, ['t.t', 'btb', 'ldl', '.d.'], dict(t=G['t'], b=G['b'], l=G['l'], d=G['d']))
    return img


def bones():
    img = grass(0).copy()
    # a skull half sunk, a rib, a long bone: the bone white, its shade
    P.stamp(img, 3, 5, ['.ww.', 'wwww', 'wkwk', '.ww.'], dict(w=G['white'], k=G['sh']))
    P.stamp(img, 9, 9, ['w....', '.www.', '....w'], dict(w=G['white']))
    P.stamp(img, 9, 10, ['.....', '.ddd.'], dict(d=G['d']))
    P.stamp(img, 3, 9, ['....', '.dd.'], dict(d=G['d']))
    return img


def meadow():
    """a patch of taller grass and flowers, 48x48, fading out into the
    plain grass at its edge"""
    img = np.concatenate([np.concatenate([grass(i)] * 3, axis=1) for i in range(3)], axis=0)
    yy, xx = np.mgrid[0:48, 0:48]
    f = P.fbm(48, 48, 700, ((3, 0.6), (6, 0.4)))
    d = np.sqrt((xx - 23.5) ** 2 + (yy - 23.5) ** 2) / 22.0 + (f - 0.5) * 0.35
    inside = d < 1.0
    img = np.where(inside, P.dither(np.clip((1.0 - d) * 2.0, 0, 1), G['m'], G['l']), img)
    r = P.rng(701)
    for (x, y) in P.scatter(702, 26, 48, 48, mind=5, avoid=~inside):
        P.stamp(img, x - 1, y - 1, ['t.t', 'btb', '.d.'], dict(t=G['t'], b=G['b'], d=G['d']), wrap=False)
    for (x, y) in P.scatter(703, 12, 48, 48, mind=7, avoid=~(d < 0.8)):
        col = (G['white'], G['yellow'], G['blue'])[r.randint(3)]
        P.stamp(img, x - 1, y - 1, ['.c.', 'cyc', '.d.'], dict(c=col, y=G['yellow'] if col != G['yellow'] else G['white'], d=G['d']), wrap=False)
    return [P.slice16(img, i % 3, i // 3) for i in range(9)]


def clover():
    img = np.concatenate([np.concatenate([grass(0), grass(1)], axis=1), np.concatenate([grass(2), grass(0)], axis=1)], axis=0)
    f = P.fbm(32, 32, 720, ((3, 0.6), (6, 0.4)))
    yy, xx = np.mgrid[0:32, 0:32]
    d = np.sqrt((xx - 15.5) ** 2 + (yy - 15.5) ** 2) / 13.0 + (f - 0.5) * 0.4
    for (x, y) in P.scatter(721, 30, 32, 32, mind=3, avoid=~(d < 1.0)):
        P.stamp(img, x - 1, y - 1, ['.b.', 'blb', '.d.'], dict(b=G['b'], l=G['t'], d=G['d']), wrap=False)
    for (x, y) in P.scatter(722, 4, 32, 32, mind=8, avoid=~(d < 0.7)):
        img[y, x] = G['white']
    return [P.slice16(img, i % 2, i // 2) for i in range(4)]


def fairy_ring():
    img = np.concatenate([np.concatenate([grass(1), grass(0)], axis=1), np.concatenate([grass(0), grass(2)], axis=1)], axis=0)
    for k in range(11):
        a = k / 11.0 * 6.283 + 0.3
        x, y = 15.5 + 10.5 * np.cos(a), 15.5 + 9.0 * np.sin(a)
        P.stamp(img, int(x) - 1, int(y) - 1, ['wcw', '.d.'], dict(w=G['white'], c=G['yellow'], d=G['sh']), wrap=False)
    return [P.slice16(img, i % 2, i // 2) for i in range(4)]


# ----------------------------------------------------------- things on grass --
def foot_shadow(img, cx, cy, rx, ry):
    m = P.disc(img.shape[1], img.shape[0], cx, cy, rx, ry)
    img[m & (img != G['o'])] = np.where(P.B4[np.arange(img.shape[0])[:, None] % 4, np.arange(img.shape[1])[None, :] % 4] > 0.35, G['sh'], G['d'])[m & (img != G['o'])]


def moss_cap(img, body, cy, depth=2.5, seed=0):
    """moss over the top of a stone"""
    h, w = img.shape
    yy = np.arange(h)[:, None] * np.ones((1, w))
    f = P.fbm(w, h, 800 + seed, ((4, 1.0),))
    cap = body & (yy < cy + (f - 0.5) * 3 - depth)
    img[cap] = np.where(f[cap] > 0.5, G['l'], G['d'])


def bush():
    img = grass(0).copy()
    foot_shadow(img, 9.5, 13.0, 6.5, 2.6)
    ramp = C('outline', 'shadow', 'leaf_mid', 'leaf_lt', 'leaf_br')
    ramp2 = C('outline', 'leaf_md', 'leaf_lt', 'leaf_br', 'leaf_hl')
    P.clump(img, 8.0, 9.0, 6.0, ramp, rough=0.08, seed=1)
    P.clump(img, 5.5, 7.0, 3.3, ramp2, rough=0.1, seed=2)
    P.clump(img, 10.8, 6.5, 3.1, ramp2, rough=0.1, seed=3)
    P.clump(img, 8.5, 10.5, 2.8, ramp, rough=0.1, seed=4)
    for (x, y) in ((5, 10), (11, 9), (8, 5)):
        img[y, x] = ID['amber']
        img[y - 1, x] = ID['glow']
    return img


def stone(cx, cy, rx, ry, ramp=STONE, seed=0, moss=True, base=None):
    img = grass(0).copy() if base is None else base
    foot_shadow(img, cx + 1.5, cy + ry * 0.7, rx * 1.05, ry * 0.55)
    body = P.clump(img, cx, cy, rx, ramp, ry=ry, rough=0.05, seed=seed)
    if moss:
        moss_cap(img, body & (img != ramp[0]), cy, depth=ry * 0.45, seed=seed)
    return img


def rock_small():
    return stone(8.0, 10.0, 4.3, 3.6, seed=1)


def boulder():
    img = stone(8.0, 8.6, 6.6, 6.0, ramp=STONE_DK, seed=2)
    # a crack
    for (x, y) in ((7, 6), (8, 7), (8, 8), (9, 9), (9, 10), (10, 11)):
        img[y, x] = S['o']
    img[7, 6] = S['s3']
    return img


def rock():
    img = stone(8.0, 9.5, 5.6, 4.8, seed=3)
    for x in (3, 6, 10, 13):
        P.stamp(img, x - 1, 12, ['t.t', '.b.'], dict(t=G['b'], b=G['l']), wrap=False)
    return img


def rock2():
    img = grass(0).copy()
    body = P.clump(img, 8.0, 10.5, 6.6, STONE, ry=3.6, rough=0.04, seed=5)
    moss_cap(img, body & (img != S['o']), 10.5, depth=1.0, seed=5)
    for x in range(2, 15, 3):
        P.stamp(img, x - 1, 12, ['t.t', '.b.'], dict(t=G['b'], b=G['l']), wrap=False)
    return img


def rock3():
    img = stone(8.0, 11.0, 5.6, 3.8, seed=6, moss=False)
    body = P.clump(img, 7.5, 6.2, 3.6, STONE, ry=3.0, rough=0.05, seed=7)
    moss_cap(img, body & (img != S['o']), 6.2, depth=1.0, seed=7)
    img[8:10, 4:12] = np.where(img[8:10, 4:12] == S['s2'], G['d'], img[8:10, 4:12])
    return img


def gboulder():
    img = np.concatenate([np.concatenate([grass(0), grass(1)], axis=1), np.concatenate([grass(2), grass(0)], axis=1)], axis=0)
    foot_shadow(img, 18.0, 27.0, 13.0, 4.5)
    body = P.clump(img, 16.0, 17.0, 13.2, STONE, ry=11.5, rough=0.04, seed=9)
    moss_cap(img, body & (img != S['o']), 17.0, depth=5.0, seed=9)
    for (x, y) in ((11, 18), (19, 21), (14, 24), (22, 15)):
        img[y, x] = S['s4']
        img[y, x + 1] = ID['yellow']
    # a sapling in a crack
    img[4:9, 21] = ID['bark']
    P.clump(img, 21.5, 4.0, 2.6, C('outline', 'grass_d', 'grass_l', 'grass_b', 'grass_b'), seed=10)
    return [P.slice16(img, i % 2, i // 2) for i in range(4)]


def treerock():
    img = np.concatenate([np.concatenate([grass(1), grass(0)], axis=1), np.concatenate([grass(0), grass(2)], axis=1)], axis=0)
    foot_shadow(img, 17.5, 27.0, 12.0, 4.0)
    P.clump(img, 16.0, 19.0, 8.5, STONE, ry=7.5, rough=0.04, seed=11)
    # the stump on top of it, its roots wrapping the stone
    P.clump(img, 16.0, 9.0, 7.0, C('outline', 'bark', 'bark', 'bark_l', 'bark_l'), ry=4.0, seed=12)
    P.clump(img, 16.0, 7.6, 5.6, C('outline', 'bark_l', 'bark_l', 'bark_l', 'bark_l'), ry=2.6, seed=13)
    img[7, 13:19] = ID['bark']
    for k, x in enumerate((7, 10, 22, 25)):
        for y in range(10, 25):
            xx = int(x + (k - 1.5) * (y - 10) * 0.18)
            if 0 <= xx < 32 and img[y, xx] != G['m']:
                img[y, xx] = ID['bark_l']
                img[y, xx + 1 if xx + 1 < 32 else xx] = ID['bark']
    return [P.slice16(img, i % 2, i // 2) for i in range(4)]


def stump():
    img = grass(0).copy()
    foot_shadow(img, 9.5, 13.0, 6.0, 2.2)
    img[7:13, 3:13] = ID['bark']
    img[7:13, 3] = ID['bark_l']
    img[7:13, 4] = ID['bark_ll']
    img[7:13, 11:13] = ID['bark_dk']
    for x in range(5, 11, 2):
        img[8:12, x] = ID['bark_l']
    P.outline(img, P.disc(16, 16, 8, 9.5, 5.2, 3.6) | (np.add.outer(np.arange(16), 0 * np.arange(16)) >= 7) & (np.arange(16)[None, :] >= 3) & (np.arange(16)[None, :] <= 12) & (np.arange(16)[:, None] <= 12), G['o'])
    P.clump(img, 8.0, 7.0, 5.0, C('outline', 'bark_ll', 'wood_cut', 'wood_cut', 'wood_cut'), ry=2.6, seed=3)
    img[7, 6:10] = ID['bark_ll']
    img[6, 7:9] = ID['bark_ll']
    # roots
    for (x, y) in ((2, 12), (13, 12), (6, 13), (10, 13)):
        img[y, x] = ID['bark_l']
    return img


def log():
    img = grass(0).copy()
    foot_shadow(img, 9.0, 12.5, 7.0, 2.0)
    body = np.zeros((16, 16), bool)
    body[6:12, 2:13] = True
    img[body] = ID['bark']
    img[6, 2:13] = ID['bark_ll']
    img[7, 2:13] = ID['bark_l']
    img[11, 2:13] = ID['bark_dk']
    for x in (4, 8, 11):
        img[8:10, x] = ID['bark_dk']
    P.outline(img, body, G['o'])
    P.clump(img, 12.8, 9.0, 2.4, C('outline', 'bark_ll', 'wood_cut', 'wood_cut', 'wood_cut'), ry=3.2, seed=4)
    img[9, 12:14] = ID['bark_ll']
    return img


def hollow_log():
    img = np.concatenate([grass(0), grass(1)], axis=1)
    foot_shadow(img, 17.0, 13.0, 14.0, 2.2)
    body = np.zeros((16, 32), bool)
    body[4:12, 3:28] = True
    img[body] = ID['bark']
    img[4, 3:28] = ID['bark_ll']
    img[5, 3:28] = ID['bark_l']
    img[11, 3:28] = ID['bark_dk']
    for x in range(6, 27, 5):
        img[7:10, x] = ID['bark_dk']
    # moss along its back
    for x in range(5, 26, 2):
        img[4, x] = G['l'] if x % 4 else G['d']
    P.outline(img, body, G['o'])
    P.clump(img, 3.5, 8.0, 2.4, C('outline', 'bark_ll', 'wood_cut', 'wood_cut', 'wood_cut'), ry=3.6, seed=5)
    P.clump(img, 27.5, 8.0, 2.6, C('outline', 'bark_dk', 'outline', 'outline', 'bark_dk'), ry=3.8, seed=6)
    return [img[:, :16], img[:, 16:]]


def pillar():
    img = grass(0).copy()
    foot_shadow(img, 10.0, 14.0, 5.5, 1.8)
    img[2:14, 5:11] = S['s2']
    img[2:14, 5] = S['s3']
    img[2:14, 6] = S['s4']
    img[2:14, 10] = S['s1']
    for y in (5, 9):
        img[y, 5:11] = S['s1']
    img[12:15, 4:12] = S['s2']
    img[12, 4:12] = S['s3']
    img[14, 4:12] = S['s1']
    # the broken top
    for (x, y) in ((5, 2), (6, 1), (7, 2), (8, 3), (9, 2), (10, 3)):
        img[y, x] = S['s3']
        img[0:y, x] = img[0:y, x]
    m = np.zeros((16, 16), bool)
    m[1:15, 4:12] = True
    m[1, 4] = m[1, 11] = False
    m[0:12, 4] = False
    m[0:12, 11] = False
    m[2:14, 5:11] = True
    m[12:15, 4:12] = True
    P.outline(img, m & (img != G['m']) & (img != G['d']) & (img != G['l']) & (img != G['b']), G['o'])
    img[2:4, 6:9] = np.where(img[2:4, 6:9] == S['s4'], G['l'], img[2:4, 6:9])
    return img


def ruin_wall():
    img = grass(0).copy()
    foot_shadow(img, 8.0, 14.0, 9.0, 1.6)
    wall = np.zeros((16, 16), bool)
    wall[4:14, :] = True
    img[wall] = S['s2']
    for y in (4, 8, 11):
        img[y, :] = S['s1'] if y != 4 else S['s3']
    for y0, y1, off in ((5, 8, 0), (9, 11, 3), (12, 14, 1)):
        for x in range(off, 16, 6):
            img[y0:y1, x] = S['s1']
            if x + 1 < 16:
                img[y0:y1, x + 1] = S['s3'] if y0 != 12 else S['s2']
    img[13, :] = S['s1']
    # a broken top, with moss
    for x in range(16):
        top = 4 - (1 if x in (3, 4, 9, 13) else 0) + (1 if x in (6, 7) else 0)
        img[4:top, x] = G['m']
        if 0 <= top < 16:
            img[top, x] = G['l'] if x % 3 else G['d']
            if top - 1 >= 0:
                img[top - 1, x] = G['o']
    return img


def statue():
    """the shrine's keeper: a seated stone hare with a gem at its breast"""
    img = grass(0).copy()
    foot_shadow(img, 9.5, 14.5, 6.5, 1.6)
    img[12:15, 3:13] = S['s2']
    img[12, 3:13] = S['s3']
    img[14, 3:13] = S['s1']
    P.outline(img, np.pad(np.ones((3, 10), bool), ((12, 1), (3, 3))), G['o'])
    P.clump(img, 8.0, 9.0, 4.4, STONE, ry=3.6, seed=20)
    P.clump(img, 8.0, 4.8, 2.9, STONE, ry=2.5, seed=21)
    P.clump(img, 6.6, 1.6, 0.9, STONE, ry=2.0, seed=22)
    P.clump(img, 9.4, 1.6, 0.9, STONE, ry=2.0, seed=23)
    img[5, 7] = S['o']
    img[5, 9] = S['o']
    img[9, 8] = ID['gold_l']
    img[10, 8] = ID['yellow']
    return img


def lantern_post():
    frames = []
    for k in range(2):
        img = grass(0).copy()
        foot_shadow(img, 9.0, 14.5, 3.5, 1.2)
        img[3:15, 6:8] = ID['bark']
        img[3:15, 6] = ID['bark_l']
        img[3, 6:12] = ID['bark']
        img[2, 6:12] = ID['bark_l']
        P.outline(img, np.pad(np.ones((12, 2), bool), ((3, 1), (6, 8))) | np.pad(np.ones((2, 6), bool), ((2, 12), (6, 4))), G['o'])
        img[4, 10] = ID['bark_dk']
        cage = np.zeros((16, 16), bool)
        cage[5:10, 9:12] = True
        img[cage] = ID['bark_dk']
        img[6:9, 10] = ID['glow'] if k == 0 else ID['amber']
        img[7, 9:12] = np.where(img[7, 9:12] == ID['bark_dk'], ID['amber'], img[7, 9:12])
        P.outline(img, cage, G['o'])
        if k == 0:
            for (x, y) in ((8, 7), (13, 7), (10, 11)):
                if img[y, x] in (G['m'], G['d'], G['l'], G['b']):
                    img[y, x] = ID['amber']
        frames.append(img)
    return frames


def thorns():
    """a bramble: dark vines looping across the tile on the torus, barbs
    of magenta, the grass under it shaded"""
    img = grass(0).copy()
    img = np.where(P.fbm(16, 16, 850, ((4, 1.0),)) > 0.45, G['d'], img).astype(np.uint8)
    for k, (y0, amp, ph) in enumerate(((3, 2.0, 0.0), (8, 2.5, 2.0), (13, 2.0, 4.0))):
        for x in range(16):
            y = int(round(y0 + amp * np.sin(x / 16.0 * 6.283 + ph))) % 16
            img[y, x] = ID['thorn_vine']
            img[(y + 1) % 16, x] = G['o']
            if (x + k * 3) % 5 == 0:
                img[(y - 1) % 16, x] = ID['thorn']
                img[(y - 2) % 16, x] = ID['thorn_vine']
    return img


def cliff(end=None):
    """a cliff to jump down going south: a grassy brow, a face of mossy
    stone blocks, a foot of dark soil"""
    img = grass(0).copy()
    face = np.zeros((16, 16), bool)
    face[4:14, :] = True
    img[face] = S['s2']
    for y in (4, 8, 11):
        img[y, :] = S['s1']
    for y0, y1, off in ((5, 8, 0), (9, 11, 4), (12, 14, 2)):
        for x in range(off, 16, 8):
            img[y0:y1, x] = S['s1']
            if x + 1 < 16:
                img[y0:y1, x + 1] = S['s3']
    img[5, :] = np.where(img[5, :] == S['s2'], S['s3'], img[5, :])
    # the brow: grass over the edge, moss hanging down
    img[3, :] = G['l']
    img[4, :] = G['o']
    r = P.rng(870)
    for x in range(16):
        if r.rand() < 0.4:
            n = 1 + r.randint(3)
            img[5:5 + n, x] = np.where(r.rand() < 0.5, G['d'], G['l'])
    img[14, :] = G['o']
    img[15, :] = P.dither(np.full((1, 16), 0.5), G['sh'], G['d'])[0]
    if end:
        yy, xx = np.mgrid[0:16, 0:16]
        cx = 16.0 if end == 'w' else 0.0
        cut = np.abs(xx + 0.5 - cx) > 12.0
        g = grass(1)
        img[cut] = g[cut]
        edge = (np.abs(np.abs(xx + 0.5 - cx) - 12.0) < 0.7) & (yy >= 3) & (yy <= 14)
        img[edge] = G['o']
    return img


def mossy_stone():
    img = grass(0).copy()
    m = P.disc(16, 16, 8, 8.5, 6.4, 5.2)
    img[m] = S['s3']
    f = P.fbm(16, 16, 880, ((4, 1.0),))
    img[m & (f < 0.4)] = S['s2']
    img[m & (f > 0.72)] = G['l']
    P.outline(img, m, S['s1'])
    img[3, 6:11] = np.where(img[3, 6:11] == S['s1'], S['s4'], img[3, 6:11])
    return img


def chest(open_=False):
    img = grass(0).copy()
    foot_shadow(img, 9.5, 14.0, 6.5, 1.8)
    box = np.zeros((16, 16), bool)
    box[6:14, 2:14] = True
    img[box] = ID['bark_l']
    img[9:14, 2:14] = ID['bark']
    img[6:9, 2:14] = ID['bark_l'] if not open_ else ID['outline']
    for x in (2, 13):
        img[6:14, x] = ID['yellow']
    img[9, 2:14] = ID['yellow']
    if not open_:
        img[9:11, 7:9] = ID['gold_l']
        img[10, 7] = G['o']
    else:
        img[4:7, 3:13] = ID['bark_l']
        img[4, 3:13] = ID['yellow']
        img[7, 6:10] = ID['yellow']
    P.outline(img, box | (np.pad(np.ones((3, 10), bool), ((4, 9), (3, 3))) if open_ else box), G['o'])
    return img


def censer(lit, frame=0):
    img = grass(0).copy()
    foot_shadow(img, 9.0, 14.5, 4.5, 1.4)
    img[9:15, 6:10] = S['s2']
    img[9:15, 6] = S['s3']
    img[9:15, 9] = S['s1']
    P.clump(img, 8.0, 7.6, 5.0, STONE, ry=2.6, seed=30)
    img[6:8, 5:11] = S['s0']
    img[6, 5:11] = S['o']
    P.outline(img, np.pad(np.ones((6, 4), bool), ((9, 1), (6, 6))), G['o'])
    if lit:
        fl = [['..g..', '.gyg.', 'gyGyg', '.gyg.'], ['.g...', '..gg.', '.gyGg', 'gyyg.']][frame]
        P.stamp(img, 6, 2, fl, dict(g=ID['yellow'], y=ID['gold_l'], G=ID['gold_l']), wrap=False)
    return img


# ------------------------------------------------------------- the gates --
GS = dict(o=ID['outline'], sh=ID['shadow'], s0=ID['stone_0'], s1=ID['stone_1'], s2=ID['stone_2'], s3=ID['stone_3'],
          s4=ID['stone_4'], silk=ID['silk'], td=ID['trail_d'], tm=ID['trail_m'], tl=ID['trail_l'], w=ID['bark'], wl=ID['bark_l'], gold=ID['yellow'])


def blocks(img, x0, x1, y0, y1, seed=0):
    img[y0:y1, x0:x1] = GS['s2']
    for y in range(y0, y1, 4):
        img[y, x0:x1] = GS['s1']
        if y + 1 < y1:
            img[y + 1, x0:x1] = GS['s3']
        off = ((y - y0) // 4 * 3 + seed) % 6
        for x in range(x0 + off, x1, 6):
            img[y:min(y + 4, y1), x] = GS['s1']


def crack():
    img = np.full((16, 16), GS['sh'], np.uint8)
    blocks(img, 0, 16, 0, 16, seed=1)
    for (x, y) in ((7, 1), (8, 2), (8, 3), (7, 4), (8, 5), (9, 6), (9, 7), (8, 8), (8, 9), (9, 10), (10, 11), (9, 12), (9, 13), (8, 14), (8, 15)):
        img[y, x] = GS['o']
        img[y, x + 1] = GS['s0']
    img[6, 10] = GS['o']
    img[10, 7] = GS['o']
    return img


def web():
    img = np.full((16, 16), GS['o'], np.uint8)
    img = np.where(P.fbm(16, 16, 900, ((4, 1.0),)) > 0.5, GS['sh'], img).astype(np.uint8)
    cx, cy = 8.0, 7.5
    for a in np.linspace(0, 6.283, 9)[:-1]:
        for t in np.linspace(0, 11, 30):
            x, y = int(cx + np.cos(a) * t), int(cy + np.sin(a) * t)
            if 0 <= x < 16 and 0 <= y < 16:
                img[y, x] = GS['s4']
    for rad in (3.0, 5.5, 8.0):
        for a in np.linspace(0, 6.283, 40):
            x, y = int(cx + np.cos(a) * rad), int(cy + np.sin(a) * rad * 0.9)
            if 0 <= x < 16 and 0 <= y < 16:
                img[y, x] = GS['silk']
    return img


def door(open_):
    img = np.full((16, 16), GS['sh'], np.uint8)
    # posts of stone at the sides, a lintel above
    blocks(img, 0, 3, 0, 16)
    blocks(img, 13, 16, 0, 16, seed=2)
    blocks(img, 0, 16, 0, 3, seed=1)
    img[0:16, 3] = GS['o']
    img[0:16, 12] = GS['o']
    img[3, 3:13] = GS['o']
    if open_:
        f = P.fbm(16, 16, 910, ((2, 0.6), (4, 0.4)))
        img[4:16, 4:12] = P.levels(f[4:16, 4:12], [GS['td'], GS['tm'], GS['tl']], [0.3, 0.75], soft=0.1)
        img[4, 4:12] = GS['o']
        img[5, 4:12] = GS['td']
    else:
        img[4:16, 4:12] = GS['wl']
        for x in (5, 8, 11):
            img[4:16, x] = GS['w']
        for y in (6, 12):
            img[y, 4:12] = GS['s1']
        img[9, 7:9] = GS['gold']
        img[10, 7] = GS['o']
    return img


def stairs():
    img = np.full((16, 16), GS['o'], np.uint8)
    blocks(img, 0, 3, 0, 16)
    blocks(img, 13, 16, 0, 16, seed=2)
    blocks(img, 0, 16, 0, 3, seed=1)
    for k, y in enumerate(range(4, 16, 3)):
        col = (GS['s3'], GS['s2'], GS['s1'], GS['s0'])[k]
        img[y, 3:13] = col
        img[y + 1, 3:13] = GS['s0'] if k < 3 else GS['o']
    img[0:16, 3] = GS['o']
    img[0:16, 12] = GS['o']
    return img


def pit():
    img = np.full((16, 16), GS['o'], np.uint8)
    img[0:3, :] = GS['s3']
    img[0, :] = GS['s4']
    img[2, :] = GS['s1']
    img[3, :] = GS['s0']
    for x in range(0, 16, 5):
        img[0:3, x] = GS['s1']
    img[4:8, :] = np.where(P.B4[np.arange(4)[:, None] % 4, np.arange(16)[None, :] % 4] > 0.6, GS['s0'], GS['o'])
    return img


# ---------------------------------------------------------------- trees --
def crown(w, h, blobs, ramp_a, ramp_b, seed, trunk=None):
    """a tree's crown on the overlay: lit clumps on a transparent ground;
    trunk (x0, x1, y0) draws the trunk's top behind the leaves, down to
    the crown's last row, so it meets the trunk tiles below"""
    img = np.zeros((h, w), np.uint8)
    if trunk:
        x0, x1, y0 = trunk
        img[y0:h, x0:x1] = ID['bark']
        img[y0:h, x0] = ID['bark_l']
        img[y0:h, x0 + 1] = ID['bark_l']
        img[y0:h, x1 - 1] = ID['outline']
        img[y0:h, x0 - 1] = ID['outline']
        img[y0:h, x1] = ID['outline']
    r = P.rng(seed)
    for i, (x, y, rad) in enumerate(sorted(blobs, key=lambda q: q[1])):
        P.clump(img, x, y, rad, ramp_a if i % 2 else ramp_b, rough=0.12, seed=seed * 10 + i)
    return img


TREE_A = C('outline', 'shadow', 'leaf_mid', 'leaf_lt', 'leaf_br')
TREE_B = C('outline', 'leaf_md', 'leaf_lt', 'leaf_br', 'leaf_hl')


def trunk_tiles(w, x0, x1, roots, seed):
    """the bottom row of a tree: its trunk on the grass, roots spreading"""
    img = np.concatenate([grass(i % 3) for i in range(w // 16)], axis=1)
    foot_shadow(img, (x0 + x1) / 2.0 + 2, 12.0, (x1 - x0) * 0.9, 3.0)
    img[0:12, x0:x1] = ID['bark']
    img[0:12, x0] = ID['bark_l']
    img[0:12, x0 + 1] = ID['bark_ll']
    img[0:12, x1 - 1] = ID['bark_dk']
    for x in range(x0 + 2, x1 - 1, 3):
        img[2:10, x] = ID['bark_dk']
    for (rx, ry, dx) in roots:
        for k in range(5):
            xx, yy = int(rx + dx * k), int(ry + k * 0.6)
            if 0 <= xx < w and 0 <= yy < 16:
                img[yy, xx] = ID['bark']
                if yy + 1 < 16:
                    img[yy + 1, xx] = ID['bark_dk']
    m = np.zeros((16, w), bool)
    m[0:12, x0:x1] = True
    P.outline(img, m, G['o'])
    return img


def oak(lantern=False):
    blobs = [(16, 10, 8.0), (9, 15, 6.0), (23, 15, 6.0), (16, 19, 7.0), (12, 7, 5.0), (21, 8, 5.0), (16, 24, 5.0)]
    if lantern:
        blobs = [(15, 10, 8.0), (8, 16, 6.5), (24, 14, 6.0), (17, 20, 7.0), (11, 6, 4.5), (22, 7, 5.0)]
    cr = crown(32, 32, blobs, TREE_A, TREE_B, 31 if not lantern else 32, trunk=(12, 20, 20))
    if lantern:
        cr[20:25, 9:12] = ID['bark']
        cr[21:24, 10] = ID['glow']
        cr[19, 10] = ID['outline']
    tr = trunk_tiles(32, 12, 20, [(12, 10, -0.8), (19, 10, 0.8)], 33)
    return [P.slice16(cr, 0, 0), P.slice16(cr, 1, 0), P.slice16(cr, 0, 1), P.slice16(cr, 1, 1), tr[:, :16], tr[:, 16:]]


def great_tree(second=False):
    if not second:
        blobs = [(24, 10, 9.5), (12, 15, 9.0), (36, 15, 9.0), (24, 20, 11.0), (7, 26, 7.0), (41, 26, 7.0),
                 (15, 32, 8.0), (33, 32, 8.0), (24, 36, 8.0)]
    else:
        blobs = [(22, 9, 9.0), (10, 17, 8.5), (35, 13, 9.5), (22, 21, 11.5), (6, 28, 6.5), (40, 25, 7.5),
                 (14, 33, 8.5), (32, 33, 8.0), (23, 38, 7.0)]
    cr = crown(48, 48, blobs, TREE_A, TREE_B, 41 if not second else 42, trunk=(19, 29, 36))
    if second:
        cr[36:41, 9:12] = ID['bark']
        cr[37:40, 10] = ID['glow']
    tr = trunk_tiles(48, 19, 29, [(19, 11, -1.2), (28, 11, 1.2), (22, 13, -0.4), (25, 13, 0.5)], 43)
    # the hollow in the trunk
    tr[3:8, 22:26] = ID['bark_dk']
    tr[4:7, 23:25] = G['o']
    return [P.slice16(cr, i % 3, i // 3) for i in range(9)] + [tr[:, 0:16], tr[:, 16:32], tr[:, 32:48]]


# --------------------------------------------------------------- mouths --
MO = dict(o=ID['outline'], deep=ID['leaf_deep'], dk=ID['shadow'], bk=ID['bark'], bkl=ID['bark_l'], bkd=ID['bark_dk'],
          s1=ID['stone_1'], s2=ID['stone_2'], s3=ID['stone_3'])


def mouth(kind):
    """a way into a mystery room, set into the canopy's face"""
    img = canopy_face(0)
    yy, xx = np.mgrid[0:16, 0:16]
    hole = ((xx + 0.5 - 8) / 5.0) ** 2 + ((yy + 0.5 - 15.5) / 9.5) ** 2 <= 1.0
    rim = ((xx + 0.5 - 8) / 6.4) ** 2 + ((yy + 0.5 - 15.5) / 11.0) ** 2 <= 1.0
    if kind == 'cave':
        f = P.fbm(16, 16, 950, ((4, 1.0),))
        img[rim & ~hole] = np.where(f[rim & ~hole] > 0.5, MO['s3'], MO['s2'])
        img[rim & ~hole & (yy > 12)] = MO['s1']
    elif kind == 'hollow':
        img[rim & ~hole] = MO['bk']
        img[rim & ~hole & (xx < 6)] = MO['bkl']
    else:
        f = P.fbm(16, 16, 951, ((4, 1.0),))
        img[rim & ~hole] = np.where(f[rim & ~hole] > 0.5, ID['leaf_md'], ID['shadow'])
    img[hole] = MO['o']
    P.outline(img, rim, MO['o'])
    return img


# -------------------------------------------------------------- the blight --
# A blighted room is a living room in other colours: BLIGHT maps each of
# the wood's colours to its blighted twin, and the room loads its groups
# so mapped. Grass turns to a violet-grey earth, the trail to ash, the
# leaves to indigo, bark to dead grey, water to murk, the lanterns' and
# the flowers' light to the blight's magenta. So a blighted room has
# every edge and transition of a living one, and reads the same: floor
# low and calm, walls darker and clumped.
BLIGHT = {
    'outline': '#120c18',
    'leaf_deep': '#141024', 'shadow': '#1e1838', 'leaf_md': '#2a2450', 'leaf_mid': '#363064',
    'leaf_lt': '#46407e', 'leaf_br': '#5a5494', 'leaf_hl': '#7a72b2',
    'grass_d': '#463c4a', 'grass_m': '#564b5a', 'grass_l': '#6a5d6c', 'grass_b': '#6a5d6c', 'grass_t': '#80728a',
    'soil': '#352d3a', 'trail_d': '#62566a', 'trail_m': '#7a6e7e', 'trail_l': '#908496', 'trail_h': '#aa9eae',
    'white': '#b4a6bc', 'yellow': '#b44ac0', 'blue': '#73508a',
    'bark_dk': '#1e1820', 'bark': '#3a3238', 'bark_l': '#564c52', 'bark_ll': '#72686c', 'wood_cut': '#948a88',
    'amber': '#b44ac0', 'glow': '#e88af0',
    'water_deep': '#14202a', 'water_dk': '#1a2c38', 'water_md': '#223c48', 'water_mid': '#2c4e5a',
    'water_lt': '#3e646c', 'ripple': '#6a9698', 'foam': '#b4d4d0',
    'lily': '#3a3048', 'lily_l': '#5a4a6c', 'lily_flower': '#e88af0',
    'stone_0': '#22202a', 'stone_1': '#38374a', 'stone_2': '#535466', 'stone_3': '#747486', 'stone_4': '#9e9cae',
    'berry': '#b44ac0',
    # the stains' sick greens, gone over to earth
    'sick_d': '#463c4a', 'sick_m': '#564b5a', 'sick_l': '#6a5d6c',
}
# the same earth, for the rot drawn into a living room
EARTH = dict(d=ID['earth_2'], m=ID['earth_3'], l=ID['earth_4'], b=ID['earth_4'], t=ID['earth_5'])
SICK = dict(d=ID['sick_d'], m=ID['sick_m'], l=ID['sick_l'], b=ID['sick_l'], t=ID['grass_b'])
assert all(BLIGHT[k] == HEX[EARTH[r]] for k, r in (('grass_d', 'd'), ('grass_m', 'm'), ('grass_l', 'l')))
BT = dict(o=ID['bt_o'], d=ID['bt_d'], m=ID['bt_m'], l=ID['bt_l'], g=ID['bt_g'], md=ID['mag_d'], mg=ID['mag'], ml=ID['mag_l'])


def stain(seed, cover, glow=False):
    """the living grass with the blight in it: violet blotches, soft at
    their edges, over the same grass, so a stained tile meets a clean one
    without a seam"""
    img = grass(seed % 3).copy()
    f = P.fbm(16, 16, 1000 + seed, ((2, 0.5), (4, 0.5)))
    # keep the blotches off the tile's rim, so neighbours meet in clean grass
    yy, xx = np.mgrid[0:16, 0:16]
    rim = np.minimum(np.minimum(xx, 15 - xx), np.minimum(yy, 15 - yy))
    fade = np.clip(rim / 3.0, 0, 1)
    d = (f - (1.0 - cover)) * 2.2 * fade
    img = np.where(d > 0.0, P.dither(np.clip(d * 2.5, 0, 1), ID['sick_m'], ID['sick_d']), img)
    img = np.where(d > 0.25, P.dither(np.clip((d - 0.25) * 3, 0, 1), ID['v_3'], ID['v_2']), img)
    img = np.where(d > 0.5, ID['v_1'], img)
    if glow:
        for (x, y) in P.scatter(1100 + seed, 3, mind=4, avoid=~(d > 0.4)):
            img[y, x] = ID['mag']
    return img


# the rot's edge: how far the grass reaches in, D at every corner so
# that sides and corners of neighbouring tiles meet at the same depth,
# wavering between
ROT_D = 5.5


def rot_wave(seed):
    t = np.arange(16) + 0.5
    f = P.vnoise(16, 1, 4, 1, seed)[0] - 0.5
    return ROT_D + 8.0 * f * np.sin(np.pi * t / 16.0)


def blocked(sides):
    """the corners a marked side already covers"""
    return (1 if sides & 9 else 0) | (2 if sides & 3 else 0) | (4 if sides & 6 else 0) | (8 if sides & 12 else 0)


def rot_combos():
    """every (sides, corners) a tile of rot can meet grass on: the sides
    where grass lies beside it (1 N, 2 E, 4 S, 8 W), and the corners
    (1 NW, 2 NE, 4 SE, 8 SW) where it lies only diagonally"""
    return [(sd, cn) for sd in range(16) for cn in range(16) if not cn & blocked(sd)]


def rot(sides, corners):
    """the blight's bare earth in a living room: the very grass, its every
    blade, gone over to earth; where grass lies beside it the colour
    comes back through the sick greens, dithered over a few pixels, so
    the rot fades into the grass rather than meeting it at a line"""
    g = grass(0)
    yy, xx = np.mgrid[0:16, 0:16]
    W = {s: rot_wave(1700 + s) for s in (1, 2, 4, 8)}
    dist = {1: (yy + 0.5) / W[1][xx], 4: (15.5 - yy) / W[4][xx], 8: (xx + 0.5) / W[8][yy], 2: (15.5 - xx) / W[2][yy]}
    terms = [dist[s] for s in (1, 2, 4, 8) if sides & s]
    for b, (cx, cy) in ((1, (0, 0)), (2, (16, 0)), (4, (16, 16)), (8, (0, 16))):
        if corners & b:
            terms.append(np.sqrt((xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2) / ROT_D)
    if terms:
        k = 0.12
        u = -k * np.log(sum(np.exp(-t / k) for t in terms))
        u = np.maximum(u, 0)
    else:
        u = np.full((16, 16), 9.0)
    j = (P.B4[yy % 4, xx % 4] - 0.5) * 0.32
    lev = np.where(u + j < 0.42, 0, np.where(u + j < 0.78, 1, 2))
    out = g.copy()
    for role in ('d', 'm', 'l', 'b', 't'):
        on = g == G[role]
        out[on & (lev == 1)] = SICK[role]
        out[on & (lev == 2)] = EARTH[role]
    return out


def crystal():
    """a cluster of the blight's crystals, grown up out of the grass"""
    img = grass(0).copy()
    foot_shadow(img, 8.5, 13.5, 6.0, 2.2)
    shards = [(8, 13, 3.2, 11), (4, 14, 2.2, 6), (12, 14, 2.4, 7)]
    yy, xx = np.mgrid[0:16, 0:16].astype(float)
    for (cx, by, hw, h) in sorted(shards, key=lambda q: -q[3]):
        t = np.clip((by - yy) / h, 0, 1)
        half = hw * (1 - t ** 1.6)
        body = (yy <= by) & (yy >= by - h) & (np.abs(xx + 0.5 - cx) <= half + 0.01)
        lit = body & (xx + 0.5 < cx)
        img[body] = BT['md']
        img[lit] = BT['mg']
        img[body & (np.abs(xx + 0.5 - cx + 0.6) < 0.6)] = BT['ml']
        P.outline(img, body, BT['o'])
    img[2, 7] = BT['ml']
    return img


def dead_tree():
    """a snag the blight has stripped: a crooked trunk, two bare limbs,
    a knot of its light"""
    img = grass(0).copy()
    foot_shadow(img, 8.5, 14.0, 5.5, 1.8)
    m = np.zeros((16, 16), bool)
    for y in range(4, 15):
        x0 = 7 + (1 if y < 8 else 0) - (1 if y > 12 else 0)
        x1 = 9 + (1 if y < 8 else 0) + (1 if y > 12 else 0)
        m[y, x0:x1 + 1] = True
    for (x, y) in ((6, 7), (5, 6), (4, 5), (4, 4), (3, 3), (11, 6), (12, 5), (12, 4), (13, 3), (13, 2), (9, 3), (9, 2), (10, 1), (5, 4)):
        m[y, x] = True
    img[m] = BT['d']
    lit = m & ~np.roll(m, -1, axis=1)
    img[m & np.roll(m, 1, axis=1) & ~np.roll(m, -1, axis=1)] = BT['m']
    img[11, 8] = BT['g']
    img[10, 8] = BT['l']
    P.outline(img, m, BT['o'])
    return img


# where the blighted tree's crown (the atlas's, btree_6..8) ends on its
# last row: its trunk comes down from there. apply() checks it.
BTREE_FOOT = [c == '#' for c in '.......##.#....#' '..##############' '###.######......']


def btree_roots(above):
    """the foot of the blighted tree under its crown: the trunk carried
    down from the crown's last row, flaring into roots on the grass"""
    img = np.concatenate([grass(i) for i in (1, 0, 2)], axis=1)
    foot_shadow(img, 25.0, 9.5, 15.0, 3.2)
    cols = [x for x in range(48) if above[x]]
    x0, x1 = min(cols), max(cols)
    m = np.zeros((16, 48), bool)
    for y in range(0, 10):
        f = y / 9.0
        a = int(round(x0 + (18 - x0) * min(1, f * 1.6)))
        b = int(round(x1 + (33 - x1) * min(1, f * 1.6)))
        m[y, a:b + 1] = True
    for (sx, dx) in ((19, -1), (23, -1), (28, 1), (32, 1)):
        x = sx
        for y in range(8, 13):
            m[y, x] = True
            m[y, x + dx] = True
            x += dx
    img[m] = BT['d']
    img[m & ~np.roll(m, -1, axis=1)] = BT['m']
    for (x, y) in ((22, 3), (27, 5), (25, 1)):
        img[y, x] = BT['l']
    img[4, 25] = BT['g']
    P.outline(img, m, BT['o'])
    img[0, :][m[0, :]] = BT['d']
    return [img[:, 0:16], img[:, 16:32], img[:, 32:48]]


def blight_pool():
    """a pool of the blight's light: plainly a hazard, a dark rim, a
    glowing body, slow rings"""
    frames = []
    for fr in range(2):
        img = grass(0).copy()
        body = P.disc(16, 16, 8, 8.5, 6.4, 5.4)
        rim = P.disc(16, 16, 8, 8.5, 7.4, 6.4) & ~body
        img[rim] = BT['o']
        f = P.fbm(16, 16, 1500 + fr, ((2, 0.5), (4, 0.5)))
        img[body] = np.where(f[body] > 0.5, BT['mg'], BT['md'])
        ring = P.disc(16, 16, 8, 8.5, 3.0 + fr * 1.5, 2.4 + fr * 1.2) & ~P.disc(16, 16, 8, 8.5, 2.0 + fr * 1.5, 1.5 + fr * 1.2)
        img[ring & body] = BT['ml']
        frames.append(img)
    return frames


def blight_mist():
    """a few motes of violet over the blighted rooms"""
    frames = []
    for fr in range(2):
        img = np.zeros((16, 16), np.uint8)
        for k, (x, y) in enumerate(P.scatter(1600 + fr, 4, mind=6)):
            img[y, x] = ID['v_4'] if k % 2 else ID['mag']
            if k == 0:
                img[y, (x + 1) % 16] = ID['v_3']
        frames.append(img)
    return frames


def sparkles():
    """the wood's sparkles on the overlay: a gold glint, white stars"""
    gold = []
    for k in range(3):
        img = np.zeros((16, 16), np.uint8)
        arm = (1, 2, 1)[k]
        cx, cy = 8, 8
        img[cy, cx] = ID['gold_l']
        for d in range(1, arm + 1):
            for (dx, dy) in ((d, 0), (-d, 0), (0, d), (0, -d)):
                img[cy + dy, cx + dx] = ID['yellow'] if d == arm else ID['gold_l']
        if k == 1:
            img[5, 11] = ID['yellow']
        gold.append(img)
    white = []
    for k in range(2):
        img = np.zeros((16, 16), np.uint8)
        for (cx, cy, big) in ((5, 6, k == 0), (11, 11, k == 1)):
            img[cy, cx] = ID['silk']
            if big:
                for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    img[cy + dy, cx + dx] = ID['stone_4']
        white.append(img)
    return gold, white


# -------------------------------------------------------- the mystery rooms --
# A mystery room is a box: a wall all round, its face along the top, its
# crown along the bottom, the floor between. The floor is shaded toward
# every wall and the wall's lumps hang over its edge, as the canopy's do
# over the wood's verges, so the box has no hard line in it. The floor
# is calm and lighter than the lumped, darker walls. The thicket is the
# wood itself, its grass, canopy and verges, so the censers and boulders
# its events stand on grass meet it without a seam.
MYST = ('cave', 'hollow', 'thicket')


def lumps(seed, ramp_a, ramp_b, base, n=11, rmin=3.4, rspan=2.4, rough=0.12):
    """a wall of lumps on the torus, as the canopy's leaves are"""
    img = np.full((16, 16), base, np.uint8)
    pts = P.scatter(seed * 3 + 11, n, mind=4)
    r = P.rng(seed * 3 + 12)
    for i, (x, y) in enumerate(sorted(pts, key=lambda q: q[1])):
        P.clump(img, x + 0.5, y + 0.5, rmin + r.rand() * rspan, ramp_a if r.rand() < 0.55 else ramp_b, wrap=True, rough=rough, seed=seed * 50 + i)
    return img


def speckle(seed, base, dark, lit, n_dark=10, n_lit=6, pairs=0.5):
    """a calm floor: one tone, short dark dashes, a few lit grains"""
    r = P.rng(seed * 101 + 9)
    img = np.full((16, 16), base, np.uint8)
    for (x, y) in P.scatter(seed * 5 + 4, n_dark, mind=3):
        img[y, x] = dark
        if r.rand() < pairs:
            img[y, (x + 1) % 16] = dark
    for (x, y) in P.scatter(seed * 5 + 5, n_lit, mind=3, avoid=img == dark):
        img[y, x] = lit
    return img


CV = dict(o=ID['outline'], s0=ID['stone_0'], s1=ID['stone_1'], s2=ID['stone_2'], s3=ID['stone_3'], s4=ID['stone_4'],
          wd=ID['water_md'], wl=ID['water_lt'], rip=ID['ripple'], foam=ID['foam'], md=ID['leaf_md'], mid=ID['leaf_mid'],
          g=ID['cave_glow'], gl=ID['cave_glow_l'])
HW = dict(o=ID['outline'], k0=ID['bark_dk'], k1=ID['bark'], k2=ID['bark_l'], k3=ID['bark_ll'], cut=ID['wood_cut'],
          soil=ID['soil'], f0=ID['trail_d'], f1=ID['trail_m'], f2=ID['trail_l'], amber=ID['amber'], glow=ID['glow'],
          wd=ID['water_md'], wl=ID['water_lt'], rip=ID['ripple'])


def myst_floor(style, seed):
    if style == 'cave':
        img = speckle(seed, CV['s2'], CV['s1'], CV['s3'])
        for (x, y) in P.scatter(seed * 7 + 1, 2, mind=7):
            P.stamp(img, x, y, ['ll', 'dd'], dict(l=CV['s3'], d=CV['s1']))
        return img
    if style == 'hollow':
        img = speckle(seed, HW['f0'], HW['soil'], HW['f1'], n_dark=9, n_lit=7)
        for (x, y) in P.scatter(seed * 7 + 2, 3, mind=6, avoid=img != HW['f0']):
            img[y, x] = HW['cut']
            img[y, (x + 1) % 16] = HW['k2']
        return img
    return grass(seed % 3)


def myst_floor1(style):
    if style == 'cave':
        # a puddle that catches the light
        img = myst_floor('cave', 3).copy()
        body = P.disc(16, 16, 8.5, 9.0, 3.6, 1.9)
        img[body] = CV['wd']
        img[body & ~np.roll(body, 1, axis=0)] = CV['s1']
        img[9, 7:9] = CV['wl']
        img[8, 10] = CV['rip']
        return img
    if style == 'hollow':
        # a knuckle of root through the floor
        img = myst_floor('hollow', 3).copy()
        m = P.disc(16, 16, 8.0, 9.0, 3.8, 1.5)
        img[m] = HW['k1']
        img[m & ~np.roll(m, 1, axis=0)] = HW['k2']
        img[m & ~np.roll(m, -1, axis=0)] = HW['k0']
        P.outline(img, m, HW['soil'])
        return img
    return grass(1)


def myst_ramps(style):
    if style == 'cave':
        return (C('outline', 'stone_0', 'stone_1', 'stone_2', 'stone_3'), C('outline', 'stone_0', 'stone_1', 'stone_2', 'stone_2'), CV['s0'])
    if style == 'hollow':
        return (C('outline', 'bark_dk', 'bark', 'bark_l', 'bark_ll'), C('outline', 'bark_dk', 'bark', 'bark', 'bark_l'), HW['k0'])
    return (CANOPY_A, CANOPY_B, L['dk'])


def myst_wall(style, seed=0):
    a, b, base = myst_ramps(style)
    if style == 'thicket':
        return leaf_mass(2 + seed)
    return lumps(60 + seed * 7 + (style == 'hollow') * 3, a, b, base, rough=0.07 if style == 'cave' else 0.12)


def myst_face(style):
    """the top wall seen from the room: its lumps, then its face going down
    to the floor, darkest at the foot"""
    if style == 'thicket':
        return canopy_face(1)
    a, b, base = myst_ramps(style)
    img = myst_wall(style).copy()
    yy, xx = np.mgrid[0:16, 0:16]
    if style == 'cave':
        face = np.full((16, 16), CV['s1'], np.uint8)
        f = P.fbm(16, 16, 960, ((4, 0.5), (8, 0.5)))
        face = np.where(f > 0.55, CV['s2'], face).astype(np.uint8)
        for y0, off in ((9, 0), (12, 5)):
            face[y0, :] = CV['s0']
            for x in range(off, 16, 7):
                face[y0 - 2:y0, x % 16] = CV['s0']
        face[14:, :] = CV['s0']
        face[15, :] = P.dither(np.full((1, 16), 0.5), CV['s0'], CV['s1'])[0]
        img[6:, :] = face[6:, :]
        for i, x in enumerate(range(1, 17, 5)):
            P.clump(img, x + 0.5, 5.5 + (i % 2), 3.0, a if i % 2 else b, wrap=True, rough=0.07, seed=970 + i)
        for x in (3, 9, 13):
            img[7:9 + (x % 3), x] = CV['md']
            img[7, x] = CV['mid']
    else:
        face = np.full((16, 16), HW['k1'], np.uint8)
        for x in range(16):
            if x % 4 == 1:
                face[:, x] = HW['k0']
            elif x % 4 == 3:
                face[:, x] = HW['k2']
        f = P.fbm(16, 16, 961, ((2, 0.6), (4, 0.4)))
        face = np.where((f > 0.62) & (face == HW['k1']), HW['k2'], face).astype(np.uint8)
        face[14:, :] = HW['k0']
        face[15, :] = P.dither(np.full((1, 16), 0.5), HW['k0'], HW['soil'])[0]
        img[6:, :] = face[6:, :]
        for i, x in enumerate(range(1, 17, 5)):
            P.clump(img, x + 0.5, 5.5 + (i % 2), 3.0, a if i % 2 else b, wrap=True, rough=0.12, seed=980 + i)
    return img


def myst_crown(style):
    """the bottom wall seen from the room: the floor, then the lit tops of
    its lumps"""
    if style == 'thicket':
        return canopy_crown(2)
    a, b, base = myst_ramps(style)
    img = myst_wall(style, 1).copy()
    fl = myst_floor(style, 0)
    img[:6, :] = fl[:6, :]
    dk = CV['s1'] if style == 'cave' else HW['soil']
    img[3:6, :] = np.where(P.dither(np.tile(np.linspace(0.2, 0.8, 3)[:, None], (1, 16)), 0, 1) == 1, dk, img[3:6, :])
    for i, x in enumerate(range(2, 18, 5)):
        P.clump(img, x + 0.5, 7.2 - (i % 2), 3.3, a, wrap=True, rough=0.07 if style == 'cave' else 0.12, seed=990 + i)
    return img


def myst_edges(style):
    """the floor beside the walls: shade deepening to the wall, and the
    wall's lumps hanging over at the sides"""
    if style == 'thicket':
        return verges()
    a, b, base = myst_ramps(style)
    fl = myst_floor(style, 0)
    lo, hi = (CV['s2'], CV['s1']) if style == 'cave' else (HW['f0'], HW['soil'])
    deep = CV['s0'] if style == 'cave' else HW['k0']
    out = {}
    for bits, (m, u) in P.band_fields(65 if style == 'cave' else 66, lo=2, hi=5, r=2).items():
        img = fl.copy()
        img = np.where(m, P.dither(np.clip(1.0 - u, 0, 1) * 1.3, lo, hi), img)
        img = np.where(m & (u < 0.35), P.dither(np.clip(0.35 - u, 0, 1) * 3, hi, deep), img)
        for side, ex in ((2, 16.0), (8, 0.0)):
            if bits & side:
                for i, y in enumerate((2, 8, 13)):
                    P.clump(img, ex, y + 0.5, 2.5 + (i % 2) * 0.6, b, wrap=False, rough=0.1, seed=side * 10 + i + 400)
        out[bits] = img
    return out


def myst_prop(style):
    """a solid thing on the floor: a stalagmite, a burl of root, a thorn bush"""
    if style == 'thicket':
        return thorns()
    img = myst_floor(style, 5).copy()
    a, b, base = myst_ramps(style)
    yy, xx = np.mgrid[0:16, 0:16].astype(float)
    if style == 'cave':
        sh = P.disc(16, 16, 9.0, 13.6, 5.5, 1.8)
        img[sh] = CV['s1']
        t = np.clip((14.0 - yy) / 12.0, 0, 1)
        half = 4.2 * (1 - t) ** 0.9 + 0.4
        body = (yy <= 14) & (yy >= 2) & (np.abs(xx + 0.5 - 8) <= half)
        img[body] = CV['s2']
        img[body & (xx + 0.5 < 8 - half * 0.2)] = CV['s3']
        img[body & (xx + 0.5 > 8 + half * 0.45)] = CV['s1']
        img[body & (np.abs(xx + 0.5 - 6.8) < 0.6) & (yy > 6)] = CV['s4']
        for y in (6, 10):
            img[y, :][body[y, :]] = np.where(img[y, :][body[y, :]] == CV['s3'], CV['s2'], CV['s1'])
        P.outline(img, body, CV['o'])
        return img
    sh = P.disc(16, 16, 9.0, 13.2, 6.5, 2.2)
    img[sh] = HW['soil']
    body = P.clump(img, 8.0, 9.0, 5.6, a, ry=4.6, rough=0.1, seed=7)
    top = P.disc(16, 16, 7.5, 7.2, 3.4, 2.0) & body
    img[top] = HW['cut']
    img[P.disc(16, 16, 7.5, 7.2, 2.0, 1.1) & top] = HW['k3']
    img[7, 7] = HW['k1']
    return img


def myst_glow(style):
    """a floor accent that gives its light: pale caps in the cave, amber
    fungus in the hollow, glowing flowers in the thicket"""
    if style == 'thicket':
        return flowers(9, G['yellow'], n=4)
    img = myst_floor(style, 6).copy()
    if style == 'cave':
        cap, lit, stem = CV['g'], CV['gl'], CV['s4']
    else:
        cap, lit, stem = HW['amber'], HW['glow'], HW['cut']
    for (x, y, big) in ((6, 9, True), (10, 11, False), (4, 12, False)):
        img[y + 1:y + 3, x] = stem
        if big:
            P.stamp(img, x - 2, y - 1, ['.ccc.', 'ccLcc', '.ddd.'], dict(c=cap, L=lit, d=stem), wrap=False)
        else:
            P.stamp(img, x - 1, y - 1, ['cLc', '.d.'], dict(c=cap, L=lit, d=stem), wrap=False)
    for (x, y) in ((12, 5), (3, 7), (13, 9)):
        img[y, x] = lit if style == 'cave' else cap
    return img


def myst_exit(style):
    """the way out, in the bottom wall: the floor going down into dark"""
    fl = trail(0) if style == 'thicket' else myst_floor(style, 7)
    img = fl.copy()
    dk1, dk2 = (G['soil'], G['o']) if style == 'thicket' else ((CV['s1'], CV['s0']) if style == 'cave' else (HW['soil'], HW['k0']))
    for y in range(6, 16):
        t = (y - 6) / 9.0
        row = P.dither(np.full((1, 16), min(1, t * 1.6)), 0, 1)[0]
        img[y, :] = np.where(row == 1, dk1, img[y, :])
        if t > 0.5:
            row2 = P.dither(np.full((1, 16), (t - 0.5) * 2), 0, 1)[0]
            img[y, :] = np.where(row2 == 1, dk2, img[y, :])
    return img


def myst_spring(style):
    """the fairy's spring: a round pool in a ring of stones, its light
    turning"""
    frames = []
    for k in range(2):
        if style == 'thicket':
            img = grass(0).copy()
            rim_c, d, l, rip = ID['stone_2'], ID['water_md'], ID['water_lt'], ID['ripple']
            o = G['o']
        elif style == 'cave':
            img = myst_floor('cave', 8).copy()
            rim_c, d, l, rip, o = CV['s3'], CV['wd'], CV['wl'], CV['rip'], CV['o']
        else:
            img = myst_floor('hollow', 8).copy()
            rim_c, d, l, rip, o = HW['k2'], HW['wd'], HW['wl'], HW['rip'], HW['o']
        rim = P.disc(16, 16, 8, 8.5, 7.2, 6.6)
        body = P.disc(16, 16, 8, 8.5, 5.6, 5.0)
        img[rim] = rim_c
        img[body] = d
        img[P.disc(16, 16, 7, 7.5, 3.6, 2.8) & body] = l
        for i, (x, y) in enumerate(((5, 7), (10, 6), (8, 11), (11, 10))):
            if (i + k) % 2 == 0:
                img[y, x] = rip
        P.outline(img, rim, o)
        frames.append(img)
    return frames


def myst_tiles(T):
    for st in MYST:
        grp = 'myst_%s' % st
        if st == 'thicket':
            T['thicket_wall'] = ('wood_leaf', [myst_wall(st)], None)
            T['thicket_face'] = ('wood_leaf', [myst_face(st)], None)
            T['thicket_crown'] = ('wood_leaf', [myst_crown(st)], None)
            for k in ('floor0', 'floor_switch', 'floor_chest'):
                T['thicket_%s' % k] = ('wood_grass', [myst_floor(st, 0)], None)
            for k in ('floor1', 'floor_lift'):
                T['thicket_%s' % k] = ('wood_grass', [myst_floor1(st)], None)
            for bits, img in myst_edges(st).items():
                T['thicket_edge_%x' % bits] = ('wood_grass', [img], None)
            T['thicket_prop'] = ('wood_bark', [myst_prop(st)], None)
            T['thicket_glow'] = ('wood_grass', [myst_glow(st)], None)
            T['thicket_exit'] = ('wood_grass', [myst_exit(st)], None)
            T['thicket_spring'] = ('wood_rot', myst_spring(st), 12)
            continue
        T['%s_wall' % st] = (grp, [myst_wall(st)], None)
        T['%s_face' % st] = (grp, [myst_face(st)], None)
        T['%s_crown' % st] = (grp, [myst_crown(st)], None)
        for k in ('floor0', 'floor_switch', 'floor_chest'):
            T['%s_%s' % (st, k)] = (grp, [myst_floor(st, 0)], None)
        for k in ('floor1', 'floor_lift'):
            T['%s_%s' % (st, k)] = (grp, [myst_floor1(st)], None)
        for bits, img in myst_edges(st).items():
            T['%s_edge_%x' % (st, bits)] = (grp, [img], None)
        T['%s_prop' % st] = (grp, [myst_prop(st)], None)
        T['%s_glow' % st] = (grp, [myst_glow(st)], None)
        T['%s_exit' % st] = (grp, [myst_exit(st)], None)
        T['%s_spring' % st] = (grp, myst_spring(st), 12)


# --------------------------------------------------------------- the list --
def tiles():
    """{metatile name: (group, [frames], anim speed)}"""
    T = {}
    T['moss0'] = ('wood_grass', [grass(0)], None)
    T['moss1'] = ('wood_grass', [grass(1)], None)
    T['moss2'] = ('wood_grass', [grass(2)], None)
    T['path'] = ('wood_grass', [trail(0)], None)
    for bits, img in trail_edges().items():
        T['pedge_%x' % bits] = ('wood_grass', [img], None)
    T['canopy'] = ('wood_leaf', [leaf_mass(0)], None)
    T['canopy2'] = ('wood_leaf', [leaf_mass(1)], None)
    T['canopy_glint'] = ('wood_leaf', canopy_glint(), 28)
    T['canopy_lantern'] = ('wood_leaf', canopy_lantern(), 10)
    T['canopy_s'] = ('wood_leaf', [canopy_face(0)], None)
    T['canopy_n'] = ('wood_leaf', [canopy_crown(0)], None)
    for bits, img in verges().items():
        T['verge_%x' % bits] = ('wood_grass', [img], None)
    T['water'] = ('wood_water', [water(0, 0), water(0, 1)], 20)
    for bits, frs in water_banks().items():
        T['water_%x' % bits] = ('wood_water', frs, 20)
    for bits, frs in water_nicks().items():
        T['water_c%x' % bits] = ('wood_water', frs, 20)
    T['water_lily'] = ('wood_water', water_lily(), 20)
    for i, frs in enumerate(raft()):
        T['raft_%d' % i] = ('wood_water', frs, 20)
    T['waterfall'] = ('wood_water', waterfall(), 6)
    T['water_foam'] = ('wood_water', foam(), 10)
    for bits, img in shores().items():
        T['shore_%x' % bits] = ('wood_grass', [img], None)
    for bits, img in shore_corners().items():
        T['shore_c%x' % bits] = ('wood_grass', [img], None)
    for bits, img in trail_corners().items():
        T['pedge_c%x' % bits] = ('wood_grass', [img], None)
    for bits, img in verge_corners().items():
        T['verge_c%x' % bits] = ('wood_grass', [img], None)
    T['bridge'] = ('wood_water', [bridge(False)], None)
    T['bridge_v'] = ('wood_water', [bridge(True)], None)
    # the grass's accents and set pieces
    T['moss_flowers'] = ('wood_grass', [flowers(5, G['white'])], None)
    T['moss_flowers2'] = ('wood_grass', [flowers(6, G['blue'])], None)
    T['tall_grass'] = ('wood_grass', [tall_grass()], None)
    T['bones'] = ('wood_grass', [bones()], None)
    for i, t in enumerate(meadow()):
        T['meadow_%d' % i] = ('wood_grass', [t], None)
    for i, t in enumerate(clover()):
        T['clover_%d' % i] = ('wood_grass', [t], None)
    for i, t in enumerate(fairy_ring()):
        T['shroomring_%d' % i] = ('wood_grass', [t], None)
    # things on the grass
    T['bush'] = ('wood_tree', [bush()], None)
    T['rock_small'] = ('wood_stone', [rock_small()], None)
    T['boulder'] = ('wood_stone', [boulder()], None)
    T['rock'] = ('wood_stone', [rock()], None)
    T['rock2'] = ('wood_stone', [rock2()], None)
    T['rock3'] = ('wood_stone', [rock3()], None)
    for i, t in enumerate(gboulder()):
        T['gboulder_%d' % i] = ('wood_stone', [t], None)
    for i, t in enumerate(treerock()):
        T['treerock_%d' % i] = ('wood_stone', [t], None)
    T['stump'] = ('wood_bark', [stump()], None)
    T['log'] = ('wood_bark', [log()], None)
    for i, t in enumerate(hollow_log()):
        T['hlog_%d' % i] = ('wood_bark', [t], None)
    T['pillar'] = ('wood_stone', [pillar()], None)
    T['ruin_wall'] = ('wood_stone', [ruin_wall()], None)
    T['statue'] = ('wood_stone', [statue()], None)
    T['lantern_post'] = ('wood_bark', lantern_post(), 10)
    T['thorn'] = ('wood_bark', [thorns()], None)
    T['mossy_stone'] = ('wood_stone', [mossy_stone()], None)
    T['chest'] = ('wood_stone', [chest(False)], None)
    T['chest_open'] = ('wood_stone', [chest(True)], None)
    T['torch'] = ('wood_stone', [censer(False)], None)
    T['torch_lit'] = ('wood_stone', [censer(True, 0), censer(True, 1)], 6)
    # cliffs, crossings, gates
    T['ledge_s'] = ('wood_stone', [cliff()], None)
    T['ledge_s_w'] = ('wood_stone', [cliff('w')], None)
    T['ledge_s_e'] = ('wood_stone', [cliff('e')], None)
    T['crack'] = ('wood_gate', [crack()], None)
    T['web'] = ('wood_gate', [web()], None)
    T['door_locked'] = ('wood_gate', [door(False)], None)
    T['door_open'] = ('wood_gate', [door(True)], None)
    T['stairs_down'] = ('wood_gate', [stairs()], None)
    T['pit'] = ('wood_gate', [pit()], None)
    # trees: crowns on the overlay, trunks on the ground
    for name, parts in (('tree', oak(False)), ('tree2', oak(True))):
        names = ['tree_top_nw', 'tree_top_ne', 'tree_mid_w', 'tree_mid_e', 'tree_trunk_w', 'tree_trunk_e'] if name == 'tree' else ['tree2_%d' % i for i in range(6)]
        for i, (n, t) in enumerate(zip(names, parts)):
            T[n] = ('wood_tree' if i < 4 else 'wood_bark', [t], None)
    for name, parts in (('gtree', great_tree(False)), ('gtree2', great_tree(True))):
        for i, t in enumerate(parts):
            T['%s_%d' % (name, i)] = ('wood_tree' if i < 9 else 'wood_bark', [t], None)
    for kind in ('cave', 'hollow', 'thicket'):
        T['mouth_%s' % kind] = ('wood_mouth', [mouth(kind)], None)
    # the blight: stains on the living grass, the rot's bare earth and
    # its edges, its crystals, snags, pools and mist, the foot of its tree
    T['moss_blight'] = ('wood_sick', [stain(3, 0.25)], None)
    T['moss_blight2'] = ('wood_sick', [stain(4, 0.3, glow=True)], None)
    T['blight_ground0'] = ('wood_sick', [stain(5, 0.4)], None)
    T['blight_ground1'] = ('wood_sick', [stain(6, 0.45)], None)
    T['blight_ground2'] = ('wood_sick', [stain(7, 0.7, glow=True), stain(7, 0.7, glow=False)], 24)
    for sd, cn in rot_combos():
        T['rot_%x%x' % (sd, cn)] = ('wood_rot', [rot(sd, cn)], None)
    T['blight_crystal'] = ('wood_blight', [crystal()], None)
    T['dead_tree'] = ('wood_blight', [dead_tree()], None)
    T['blight_pool'] = ('wood_blight', blight_pool(), 16)
    T['blight_mist'] = ('wood_sick', blight_mist(), 16)
    for i, t in enumerate(btree_roots(BTREE_FOOT)):
        T['btree_%d' % (9 + i)] = ('wood_blight', [t], None)
    # what a blighted room drew of its own before it was a living room in
    # the blight's colours: kept, as the living art, so nothing differs
    T['blight_floor'] = ('wood_rot', [rot(0, 0)], None)
    T['blight_floor2'] = ('wood_rot', [rot(0, 0)], None)
    T['blight_vein'] = ('wood_grass', [trail(0)], None)
    T['canopy_blight'] = ('wood_leaf', [leaf_mass(0)], None)
    T['canopy_blight2'] = ('wood_leaf', [leaf_mass(1)], None)
    for n in ('blight_wall', 'blight_wall2', 'blight_wall_lit'):
        T[n] = ('wood_leaf', [canopy_face(0)], None)
    myst_tiles(T)
    gold, white = sparkles()
    T['sparkle'] = ('wood_gate', gold, 14)
    T['sparkle_white'] = ('wood_gate', white, 16)
    # what is never placed, kept in the wood's palettes
    for n in ('moss_shade', 'path_edge_n', 'fence', 'relic'):
        T[n] = ('wood_grass', [grass(0)], None)
    T['pit_inner'] = ('wood_gate', [np.full((16, 16), GS['o'], np.uint8)], None)
    T['ledge_n'] = ('wood_stone', [cliff()], None)
    T['black'] = ('wood_grass', [np.full((16, 16), G['o'], np.uint8)], None)
    return T


_CACHE = {}


def build():
    """the tiles drawn here and the palette groups they make"""
    if 'T' in _CACHE:
        return _CACHE['T'], _CACHE['G']
    T = tiles()
    used = {}
    for name, (g, frames, _) in T.items():
        u = used.setdefault(g, set())
        for f in frames:
            u |= set(int(v) for v in np.unique(f) if v)
    groups = {}
    for g, u in used.items():
        assert len(u) <= 15, (g, len(u), sorted(COLORS[i - 1][0] for i in u))
        # dark to light, so a palette reads as a ramp
        order = sorted(u, key=lambda i: (lambda h: 0.299 * int(h[1:3], 16) + 0.587 * int(h[3:5], 16) + 0.114 * int(h[5:7], 16))(HEX[i]))
        groups[g] = order
    _CACHE['T'], _CACHE['G'] = T, groups
    return T, groups


def group(name):
    _, groups = build()
    return ['#000000'] + [HEX[i] for i in groups[name]] + ['#000000'] * (15 - len(groups[name]))


def group_blight(name):
    """a group's palette with each colour turned to its blighted twin"""
    _, groups = build()
    cols = [BLIGHT.get(COLORS[i - 1][0], HEX[i]) for i in groups[name]]
    return ['#000000'] + cols + ['#000000'] * (15 - len(cols))


def group_names():
    return sorted(build()[1])


def rows_in(img, order):
    lut = {c: k + 1 for k, c in enumerate(order)}
    return [''.join('%x' % (lut[int(v)] if v else 0) for v in r) for r in img]


def apply(metatiles):
    T, groups = build()
    names = {m['name'] for m in metatiles}
    by = {m['name']: m for m in metatiles}
    foot = ''.join(''.join('.' if ch in '. 0' else '#' for ch in (by['btree_%d' % i].get('frames') or [by['btree_%d' % i]['art']])[0][15]) for i in (6, 7, 8))
    assert [c == '#' for c in foot] == BTREE_FOOT, ('the blighted tree\'s crown changed; its foot is drawn to', foot)
    assert set(T) <= names, sorted(set(T) - names)
    for m in metatiles:
        t = T.get(m['name'])
        if not t:
            continue
        g, frames, speed = t
        m['pal'] = g
        if len(frames) > 1:
            m['frames'] = [rows_in(f, groups[g]) for f in frames]
            m.pop('art', None)
            m['anim_speed'] = speed or 20
        else:
            m['art'] = rows_in(frames[0], groups[g])
            m.pop('frames', None)
