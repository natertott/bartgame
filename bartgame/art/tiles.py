"""BARTGAME metatiles: 16x16 tiles with a behavior type and collision.

Art is rows of 16 hex digits. Ground is drawn by hand from small tuft
and pebble marks placed where they read well; the canopy walls are leaf
masses built from overlapping lit blobs that wrap at the tile edge so
they tile without a seam; landmarks are drawn.

Palette 'forest': 1 outline, 2-6 grass deep..bright, 7-9 path, A blue,
                  B pink, C cream, D blight violet, E magenta, F gold.
Palette 'wood':   1 outline, 2-6 leaf deepest..bright, 7-A bark, B-D
                  lantern amber, E grass, F thorn magenta.
Palette 'stone':  1 outline, 2-6 stone, 7-A water deep..foam, B-D gold,
                  E moss, F wood.
Palette 'blight': 1 outline, 2-7 blight deepest..pink, 8-A dead bark,
                  B crystal light, C-D grass, E gold, F white.
Palette 'sewer':  1 outline, 2-6 wet stone, 7-8 moss, 9-C teal water
                  deep..foam, D rust, E-F candle.
Palette 'props':  1 outline, 2-4 wood, 5 stone mid, 6-7 bone, 8-9 teal
                  cloth, A-B red cloth, C gold, D-E rug violet, F amber.
"""
import random

from px import L, Canvas, compose, outline, hflip, vflip, opaque, remap, blank, ball  # noqa: F401

TYPES = ['FLOOR', 'SOLID', 'PIT', 'WATER', 'LEDGE_N', 'LEDGE_E', 'LEDGE_S', 'LEDGE_W',
         'THORN', 'CRACK', 'WEB', 'DOOR', 'DOOR_OPEN', 'TORCH', 'TORCH_LIT', 'SLOW', 'HURT',
         'EXIT', 'CHEST', 'CHEST_OPEN', 'SWITCH', 'STAIRS', 'LIFT1', 'LIFT2', 'MYST', 'FRONT']

SOLID_TYPES = {'SOLID', 'THORN', 'CRACK', 'WEB', 'DOOR', 'TORCH', 'TORCH_LIT', 'CHEST', 'CHEST_OPEN',
               'LIFT1', 'LIFT2', 'LEDGE_N', 'LEDGE_E', 'LEDGE_S', 'LEDGE_W'}


def default_coll(t):
    return 15 if t in SOLID_TYPES else 0


def A(s):
    """Multi-line string to rows, ignoring blank lines and indentation."""
    return [ln.strip() for ln in s.strip('\n').splitlines() if ln.strip()]


def overlay(base_rows, top_rows):
    """Draw top_rows over base_rows where top is not '.'."""
    return compose(base_rows, top_rows)


METATILES = []


def mt(name, pal, type_, art=None, frames=None, coll=None, anim_speed=8):
    d = {'name': name, 'pal': pal, 'type': type_}
    if frames:
        d['frames'] = frames
    else:
        d['art'] = art
    if coll is not None:
        d['coll'] = coll
    if anim_speed:
        d['anim_speed'] = anim_speed
    METATILES.append(d)


def flat(c, w=16, h=16):
    return [('%x' % c) * w] * h


def turf(seed, base=4, dark=3, light=5, n_dark=7, n_light=4, w=16, h=16):
    """Ground with texture: the body tone, short dark dashes where blades
    or grains overlap, single lit tips. Deterministic from the seed."""
    rnd = random.Random(seed)
    c = Canvas(w, h, base)
    for _ in range(n_dark):
        x, y = rnd.randrange(w), rnd.randrange(h)
        c.wrap_set(x, y, dark)
        c.wrap_set(x + 1, y, dark)
    for _ in range(n_light):
        c.wrap_set(rnd.randrange(w), rnd.randrange(h), light)
    return c.rows()


def marks(base, placements, w=16, h=16):
    """A tile with small drawings placed on it (wrapping). Grass and soil
    bases get a texture first, seeded by where the marks go."""
    seed = sum((x + 1) * 31 + (y + 1) * 7 for art, x, y in placements)
    if base == 4:
        c = Canvas.from_rows(turf(seed, 4, 3, 5, 6, 8, w, h))
    elif base == 8:
        c = Canvas.from_rows(turf(seed, 8, 7, 9, 5, 5, w, h))
    else:
        c = Canvas(w, h, base)
    for art, x, y in placements:
        c.wrap_blit(art, x, y)
    return c.rows()


# ============================================================== forest ===
# Grass: a mid green with tufts, lit from the upper left.
TUFT = {
    'a': A('''
        .5.
        53.
        .3.
    '''),
    'b': A('''
        5.
        .3
    '''),
    'c': A('''
        6
        5
    '''),
    'd': A('''
        .6.
        65.
        .3.
    '''),
    'e': A('''
        3.
        .2
    '''),
    'f': A('''
        .5
        3.
    '''),
}

GRASS = 4
mt('moss0', 'forest', 'FLOOR', marks(GRASS, [
    (TUFT['a'], 1, 1), (TUFT['b'], 9, 2), (TUFT['c'], 13, 0), (TUFT['a'], 11, 6),
    (TUFT['e'], 4, 7), (TUFT['b'], 6, 10), (TUFT['d'], 1, 12), (TUFT['a'], 9, 12),
    (TUFT['c'], 14, 10), (TUFT['e'], 12, 15), (TUFT['f'], 5, 4)]))
mt('moss1', 'forest', 'FLOOR', marks(GRASS, [
    (TUFT['b'], 2, 2), (TUFT['a'], 7, 0), (TUFT['e'], 13, 3), (TUFT['d'], 10, 8),
    (TUFT['c'], 3, 8), (TUFT['a'], 5, 13), (TUFT['f'], 14, 13), (TUFT['b'], 0, 6),
    (TUFT['e'], 8, 5), (TUFT['c'], 12, 11)]))
mt('moss2', 'forest', 'FLOOR', marks(GRASS, [
    (TUFT['a'], 3, 4), (TUFT['c'], 8, 1), (TUFT['b'], 12, 6), (TUFT['e'], 1, 9),
    (TUFT['d'], 7, 10), (TUFT['f'], 13, 12), (TUFT['b'], 4, 14), (TUFT['e'], 10, 14),
    (TUFT['c'], 0, 1), (TUFT['f'], 15, 2)]))

# Blight: a violet stain with a magenta glow; the second variant grows
# blue glowing mushrooms.
BLIGHT_PATCH = A('''
    ...dd....
    .ddeedd..
    ddeeeeedd
    deeeeeedd
    ddeeeeed.
    .ddeedd..
    ...dd....
''')
BLIGHT_SMALL = A('''
    .dd.
    deed
    deed
    .dd.
''')
VEIN = A('''
    d...
    .d..
    .d..
    ..d.
    ..dd
''')
MUSHROOM = A('''
    .aa.
    acaa
    .11.
    .11.
''')
mt('moss_blight', 'forest', 'FLOOR', marks(GRASS, [
    (BLIGHT_PATCH, 1, 1), (BLIGHT_SMALL, 10, 9), (VEIN, 9, 2), (TUFT['e'], 13, 5),
    (TUFT['b'], 2, 11), (TUFT['a'], 6, 11), (TUFT['c'], 14, 14)]))
mt('moss_blight2', 'forest', 'FLOOR', marks(GRASS, [
    (BLIGHT_SMALL, 8, 8), (MUSHROOM, 2, 3), (MUSHROOM, 11, 1), (VEIN, 3, 8),
    (TUFT['a'], 1, 12), (TUFT['e'], 6, 1), (TUFT['c'], 14, 12), (MUSHROOM, 12, 11)]))

# Flowers: blue, pink and cream blooms with pale hearts.
FLOWER_BLUE = A('''
    .a.
    aca
    .a.
''')
FLOWER_PINK = A('''
    .b.
    bcb
    .b.
''')
FLOWER_CREAM = A('''
    .c.
    cfc
    .c.
''')
FLOWER_GOLD = A('''
    .f.
    fcf
    .f.
''')
mt('moss_flowers2', 'forest', 'FLOOR', marks(GRASS, [
    (FLOWER_GOLD, 3, 3), (FLOWER_CREAM, 11, 2), (FLOWER_GOLD, 8, 9), (FLOWER_PINK, 2, 12),
    (TUFT['a'], 13, 7), (TUFT['e'], 6, 6), (TUFT['c'], 13, 13), (FLOWER_CREAM, 10, 13)]))
mt('moss_flowers', 'forest', 'FLOOR', marks(GRASS, [
    (FLOWER_BLUE, 2, 2), (FLOWER_PINK, 11, 4), (FLOWER_CREAM, 7, 9), (FLOWER_BLUE, 1, 11),
    (TUFT['a'], 6, 2), (TUFT['b'], 13, 10), (TUFT['e'], 4, 7), (TUFT['c'], 12, 13),
    (FLOWER_PINK, 13, 0)]))

# Tall grass: bright blades in a clump.
mt('tall_grass', 'forest', 'FLOOR', compose(marks(GRASS, [(TUFT['b'], 13, 1), (TUFT['e'], 1, 14)]), A('''
    ................
    ......6.........
    ...6..5..6......
    ...5.65..5.6....
    .6.5.55.65.5....
    .5.55.5.5..5.6..
    .5.5.55.5.65.5..
    .55.5.5.55.5.5..
    .5.5.5.5.5.5.5..
    .35.5.5.5.5.53..
    .3.35.35.5.3.3..
    .3.3.3.3.33.3...
    ..3.3.3.3.3.3...
    ...3.2.3.3.2....
    .....2...2......
    ................
''')))

# Grass in the shadow of a wall or a cliff: deep green over the top two
# thirds, a ragged edge where the light returns.
_shade_top = A('''
    3333333333333333
    3323333333323333
    3333333333333333
    2333333233333332
    3333333333333333
    3333233333333333
    3333333333323333
    3233333333333333
    3333333323333333
    3333333333333333
    3343333343333433
    3433343334333343
    4344434444344434
    ................
    ................
    ................
''')
mt('moss_shade', 'forest', 'FLOOR', compose(marks(GRASS, [(TUFT['e'], 2, 13), (TUFT['b'], 9, 13), (TUFT['f'], 13, 14),
                                                          (TUFT['c'], 5, 14)]), _shade_top))

# Soil: a warm trodden path with pebbles and a few dark footmarks.
PEBBLE = A('''
    .9.
    971
''')
PEBBLE2 = A('''
    99
    71
''')
DARK = A('''
    77
    .7
''')
SOIL = 8
mt('path', 'forest', 'FLOOR', marks(SOIL, [
    (PEBBLE, 2, 2), (DARK, 9, 1), (PEBBLE2, 12, 5), (DARK, 4, 7), (PEBBLE, 7, 10),
    (DARK, 13, 11), (PEBBLE2, 1, 13), (DARK, 10, 14), (A('9'), 6, 5), (A('9'), 14, 2),
    (A('7'), 0, 9)]))

# The path's north end: grass above, a scalloped dark lip, soil below.
mt('path_edge_n', 'forest', 'FLOOR', compose(marks(SOIL, [
    (PEBBLE, 3, 9), (DARK, 10, 11), (PEBBLE2, 13, 13), (DARK, 6, 14)]), A('''
    4444444444444444
    4454444444544444
    4434444444344444
    4444444444444444
    3344433344433344
    1133311133311133
    7711777711177771
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
''')))

# A pool of blight: violet with a dark rim; magenta glints drift.
_pool = marks(0xd, [(A('11'), 3, 3), (A('1'), 11, 9), (A('11'), 6, 12), (A('1'), 13, 2)])
_pool = compose(_pool, A('''
    1111111111111111
    1..............1
    1..............1
    1..............1
    1..............1
    1..............1
    1..............1
    1..............1
    1..............1
    1..............1
    1..............1
    1..............1
    1..............1
    1..............1
    1..............1
    1111111111111111
'''))
_glint1 = A('''
    ................
    ................
    ....e...........
    ...efe.......e..
    ....e.......efe.
    .............e..
    ................
    ................
    ........e.......
    .......efe......
    ........e.......
    ................
    ..e.............
    .efe............
    ..e.............
    ................
''')
_glint2 = A('''
    ................
    ................
    ................
    ................
    ....e...........
    ...efe.......e..
    ....e.......efe.
    .............e..
    ................
    ................
    ................
    ........e.......
    .......efe......
    ..e.....e.......
    .efe............
    ..e.............
''')
mt('blight_pool', 'forest', 'HURT', frames=[compose(_pool, _glint1), compose(_pool, _glint2)], anim_speed=16)


# ---------------------------------------------------------- the canopy --
def blob(c, cx, cy, r, tones=(2, 4, 5, 6), wrap=True):
    deep, mid, light, bright = tones

    def put(x, y, col):
        if wrap:
            c.wrap_set(x, y, col)
        else:
            c.set(x, y, col)

    def disc(ox, oy, rad, col):
        for y in range(int(cy - rad - 1), int(cy + rad + 2)):
            for x in range(int(cx - rad - 1), int(cx + rad + 2)):
                dx, dy = x + 0.5 - (cx + ox), y + 0.5 - (cy + oy)
                if dx * dx + dy * dy <= rad * rad:
                    put(x, y, col)

    disc(0.9, 0.9, r + 0.4, deep)
    disc(0, 0, r, mid)
    disc(-0.9, -0.9, r - 1.2, light)
    if r >= 3:
        disc(-1.3, -1.3, max(0.8, r - 2.4), bright)


LEAF_TIP = A('''
    6.
    .3
''')
LEAF_TIP2 = A('''
    .6
    3.
''')


def leaf_mass(positions, tips=(), w=16, h=16, base=2, tones=(2, 4, 5, 6)):
    c = Canvas(w, h, base)
    for cx, cy, r in sorted(positions, key=lambda p: p[1]):
        blob(c, cx, cy, r, tones)
    for art, x, y in tips:
        c.wrap_blit(art, x, y)
    return c.rows()


CANOPY_A = [(3, 2, 3.6), (11, 1, 2.8), (7, 6, 3.8), (14, 7, 3.0), (2, 10, 3.2), (9, 12, 3.8), (15, 14, 2.4)]
CANOPY_B = [(9, 2, 3.6), (1, 4, 2.8), (14, 5, 3.2), (5, 9, 3.8), (12, 11, 3.0), (1, 14, 2.6), (8, 15, 3.0)]
TIPS_A = [(LEAF_TIP, 5, 4), (LEAF_TIP2, 13, 3), (LEAF_TIP, 0, 7), (LEAF_TIP2, 10, 9), (LEAF_TIP, 6, 14)]
TIPS_B = [(LEAF_TIP2, 4, 1), (LEAF_TIP, 11, 7), (LEAF_TIP2, 2, 8), (LEAF_TIP, 14, 13), (LEAF_TIP2, 7, 12)]
mt('canopy', 'wood', 'SOLID', leaf_mass(CANOPY_A, TIPS_A))
mt('canopy2', 'wood', 'SOLID', leaf_mass(CANOPY_B, TIPS_B))

# Fireflies in the leaves: two frames, the lights trade places.
def glint(rows, pts):
    c = Canvas.from_rows(rows)
    for x, y in pts:
        c.wrap_set(x, y, 0xd)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c.wrap_set(x + dx, y + dy, 0xc)
    return c.rows()


mt('canopy_glint', 'wood', 'SOLID', frames=[glint(leaf_mass(CANOPY_A, TIPS_A), [(3, 4), (12, 9)]),
                                             glint(leaf_mass(CANOPY_A, TIPS_A), [(8, 13), (13, 3)])], anim_speed=28)

# A lantern hung in the canopy: amber light on the leaves around it.
_lant_base = leaf_mass(CANOPY_B, TIPS_B)
_lantern = A('''
    ................
    .......1........
    .......1........
    ......111.......
    .....1bcb1......
    .....1cdc1......
    .....1cdc1......
    .....1bcb1......
    ......1b1.......
    .......1........
    ................
    ................
    ................
    ................
    ................
    ................
''')
_glow1 = A('''
    ................
    ................
    ................
    ................
    ....c.....c.....
    ................
    ...c.......c....
    ................
    ....c.....c.....
    ......c.c.......
    ................
    ................
    ................
    ................
    ................
    ................
''')
_glow2 = A('''
    ................
    ................
    ................
    ....c.....c.....
    ................
    ...c.......c....
    ................
    ................
    ...c.......c....
    ................
    .....c...c......
    ................
    ................
    ................
    ................
    ................
''')
mt('canopy_lantern', 'wood', 'SOLID', frames=[compose(compose(_lant_base, _glow1), _lantern),
                                                compose(compose(_lant_base, _glow2), _lantern)], anim_speed=10)

# A darker, sicker canopy for the deep rooms, magenta at the tips.
BLIGHT_TIP = A('''
    f.
    .2
''')
mt('canopy_blight', 'wood', 'SOLID', leaf_mass(CANOPY_A, [(BLIGHT_TIP, 5, 4), (BLIGHT_TIP, 13, 3), (BLIGHT_TIP, 0, 7),
                                                           (BLIGHT_TIP, 10, 9), (BLIGHT_TIP, 6, 14)], tones=(1, 2, 3, 4)))

# The wall's face, under the top canopy: a hanging leaf fringe, thick
# dark trunks, and the shadow the wall throws on the ground.
_face = A('''
    2222222222222222
    3233322332233322
    2322232222322232
    1211121121121112
    1988718711887187
    1988718711887187
    1988712211887187
    1988718711887187
    1988718711887187
    1988718711882287
    1988718711887187
    1988718711887187
    9888788711888187
    1111111111111111
    1111111111111111
    2111121111112111
''')
mt('canopy_s', 'wood', 'SOLID', _face)

# The top edge of the lower wall: the lit crown of the leaf mass with
# grass showing between the scallops.
_crown = leaf_mass([(2, 6, 3.4), (8, 5, 3.8), (14, 6, 3.4), (5, 11, 3.6), (11, 12, 3.6), (0, 14, 2.6)],
                   [(LEAF_TIP, 4, 8), (LEAF_TIP2, 12, 9), (LEAF_TIP, 9, 13)], base=0xe)
_crown = compose(_crown, A('''
    eeeeeeeeeeeeeeee
    eeeeeeeeeeeeeeee
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
'''))
_crown_g = Canvas.from_rows(_crown)
for y in range(16):
    for x in range(16):
        if _crown_g.get(x, y) == 0xe and y < 9:
            if _crown_g.get(x, y + 1) in (2, 4, 6):
                _crown_g.set(x, y + 1, 1)
mt('canopy_n', 'wood', 'SOLID', _crown_g.rows())


# A free-standing tree: a 32-wide crown over a trunk, 2x3 metatiles.
def tree_art():
    c = Canvas(32, 48)
    crown = [(16, 10, 9.5), (8, 9, 6.5), (24, 9, 6.5), (6, 16, 6.0), (26, 16, 6.0),
             (12, 21, 6.2), (20, 21, 6.2), (16, 25, 5.0)]
    for cx, cy, r in sorted(crown, key=lambda p: p[1]):
        blob(c, cx, cy, r, (2, 4, 5, 6), wrap=False)
    c.rect(13, 28, 18, 44, 8)
    c.vline(13, 28, 44, 7)
    c.vline(14, 30, 44, 9)
    c.vline(18, 28, 44, 7)
    c.vline(17, 30, 44, 8)
    c.hline(11, 13, 44, 8); c.hline(18, 20, 44, 8)
    c.hline(10, 12, 45, 7); c.hline(19, 21, 45, 7)
    c.rect(13, 45, 18, 45, 7)
    c.outline(1)
    return c.rows()


_tree = tree_art()


def slice16(rs, tx, ty):
    return [r[tx * 16:tx * 16 + 16] for r in rs[ty * 16:ty * 16 + 16]]


mt('tree_top_nw', 'wood', 'FLOOR', slice16(_tree, 0, 0))
mt('tree_top_ne', 'wood', 'FLOOR', slice16(_tree, 1, 0))
mt('tree_mid_w', 'wood', 'FLOOR', slice16(_tree, 0, 1))
mt('tree_mid_e', 'wood', 'FLOOR', slice16(_tree, 1, 1))
_grass_w = marks(GRASS, [(TUFT['a'], 1, 2), (TUFT['e'], 3, 9), (TUFT['c'], 1, 13), (TUFT['b'], 9, 14)])
_grass_e = marks(GRASS, [(TUFT['b'], 11, 3), (TUFT['a'], 12, 8), (TUFT['e'], 7, 14), (TUFT['c'], 14, 13)])
mt('tree_trunk_w', 'forest', 'SOLID', compose(_grass_w, slice16(_tree, 0, 2)), coll=3)
mt('tree_trunk_e', 'forest', 'SOLID', compose(_grass_e, slice16(_tree, 1, 2)), coll=3)

# A lantern on a post, lit: amber light on the grass.
_post = L({'g': 0xe}, '''
    gggggg1111gggggg
    ggggg1bccb1ggggg
    ggggg1cddc1ggggg
    ggggg1cddc1ggggg
    ggggg1bccb1ggggg
    gggggg1991ggggg1
    ggggggg17gggg1g1
    ggggggg18ggggg1g
    ggggggg18gggggg1
    ggggggg18gggggg1
    ggggggg18gggggg1
    ggggggg18ggggggg
    gggggg1981ggggg1
    ggggg198881ggggg
    ggggg111111ggggg
    gggggggggggggggg
''')
_post = [r.replace('1', 'e', 0) for r in _post]
_postglow1 = A('''
    ................
    ................
    ....c......c....
    ................
    ...c........c...
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
''')
_postglow2 = A('''
    ................
    ...c........c...
    ................
    ..c..........c..
    ................
    ....c......c....
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
''')
mt('lantern_post', 'wood', 'SOLID', frames=[compose(_post, _postglow1), compose(_post, _postglow2)], coll=3, anim_speed=10)

# A wooden fence: two rails on posts, on grass.
mt('fence', 'wood', 'SOLID', L({'g': 0xe}, '''
    gggggggggggggggg
    gggggggggggggggg
    g1991gggggg1991g
    g1a81gggggg1a81g
    g1a8111111111a81
    g1a8aaaaaaaaaa81
    g1a8888888888881
    g1a8111111111a81
    g1a81gggggg1a81g
    g1a8111111111a81
    g1a8aaaaaaaaaa81
    g1a8888888888881
    g1a8111111111a81
    g1781gggggg1781g
    g1111gggggg1111g
    gggggggggggggggg
'''))

# A fallen log, rings at the cut end.
mt('log', 'wood', 'SOLID', L({'g': 0xe}, '''
    gggggggggggggggg
    gggggggggggggggg
    gggggggggggggggg
    g11111111111111g
    1aaaaaaaaaaa9a91
    1a99999999999891
    1998889988898891
    1988888888888781
    1987777877778871
    1877777777777771
    .1777777777777 1
    g11111111111111g
    gggggggggggggggg
    gggggggggggggggg
    gggggggggggggggg
    gggggggggggggggg
'''))
METATILES[-1]['art'] = [r.replace(' ', '7').replace('.', 'e') for r in METATILES[-1]['art']]

# A plank bridge over water, railings at the sides.
mt('bridge', 'wood', 'FLOOR', A('''
    1111111111111111
    9aaaaaaaaaaaaaa9
    1888888888888881
    1999999999999991
    1aaaaaaaaaaaaaa1
    1888888888888881
    1111111111111111
    1999999999999991
    1aaaaaaaaaaaaaa1
    1888888888888881
    1111111111111111
    1999999999999991
    1aaaaaaaaaaaaaa1
    1888888888888881
    9aaaaaaaaaaaaaa9
    1111111111111111
'''))
# The same planks for a way that runs north-south: the rails at the sides.
mt('bridge_v', 'wood', 'FLOOR', [''.join(r[i] for r in METATILES[-1]['art']) for i in range(16)])

# Thorns: a bramble of dark vines, magenta barbs, on the grass.
mt('thorn', 'wood', 'THORN', L({'g': 0xe}, '''
    gggggggggggggggg
    gg1ggggggg1ggggg
    g181ggfgg181gfgg
    g18111f111811fg.
    gg1771f77711771g
    ggg17777711718gg
    gfgg17777717771g
    g1fgg1777771gggg
    g181gg17777f1ggg
    gg181g1771771ggg
    ggf1711711g171gg
    ggg1771g11gg171g
    gg11771ggfggg1gg
    gg1g1771g1fggggg
    gggg1g171g1ggggg
    gggggg1ggggggggg
'''))
METATILES[-1]['art'] = [r.replace('.', 'e') for r in METATILES[-1]['art']]

# A stump: rings on the cut top, bark down the sides, on the grass.
mt('stump', 'forest', 'SOLID', compose(marks(GRASS, [(TUFT['a'], 0, 12), (TUFT['c'], 14, 1)]), A('''
    ................
    .....111111.....
    ...11999999911..
    ..1998888889991.
    .19989999998991.
    .19898999989891.
    .19898988989891.
    .19898999989891.
    .19989888889991.
    .19999999999991.
    .17877878787871.
    .18877878788781.
    .17777877877771.
    ..177778777771..
    ...1111111111...
    ................
''')))

# A bush: a round leafy thing with berries, lifted with R or cut.
mt('bush', 'wood', 'LIFT1', L({'g': 0xe}, '''
    gggggggggggggggg
    gggggg1111gggggg
    gggg1155551ggggg
    ggg1556f65551ggg
    gg15565555f5541g
    gg1554444544441g
    g155f44444f44431
    g154444f44444431
    g15444444444f331
    g1444f444f433331
    g1434444433333 1
    gg1333433333321g
    gg1233333322221g
    ggg11222222211gg
    gggg1111111 1ggg
    gggggggggggggggg
'''))
METATILES[-1]['art'] = [r.replace(' ', '1') for r in METATILES[-1]['art']]

# A small stone, light enough to lift.
mt('rock_small', 'stone', 'LIFT1', L({'m': 0xe}, '''
    mmmmmmmmmmmmmmmm
    mmmmmmmmmmmmmmmm
    mmmmmmmmmmmmmmmm
    mmmmmm1111mmmmmm
    mmmm11556611mmmm
    mmm1556655441mmm
    mm15565554433 1m
    mm1555544443331m
    mm1444444433321m
    mm1444443333221m
    mmm13333322211mm
    mmmm11111111mmmm
    mmmmmmmmmmmmmmmm
    mmmmmmmmmmmmmmmm
    mmmmmmmmmmmmmmmm
    mmmmmmmmmmmmmmmm
'''))
METATILES[-1]['art'] = [r.replace(' ', '3') for r in METATILES[-1]['art']]

# A boulder: dark, cracked, only the gauntlet moves it.
mt('boulder', 'stone', 'LIFT2', L({'m': 0xe}, '''
    mmmmmmmmmmmmmmmm
    mmmmm111111mmmmm
    mmm1144555411mmm
    mm144455544331mm
    m14455544433321m
    m1455444143332 1
    m1444441443332 1
    m1444414444332 1
    m1333144433322 1
    m1333314333222 1
    m1222333322221 1
    mm12222222211 1m
    mm11122221111mmm
    mmmm11111111mmmm
    mmmmmmmmmmmmmmmm
    mmmmmmmmmmmmmmmm
'''))
METATILES[-1]['art'] = [r.replace(' ', '1') for r in METATILES[-1]['art']]

# ------------------------------------------------------------- stones --
mt('rock', 'stone', 'SOLID', L({'m': 0xe}, '''
    mmmmmmmmmmmmmmmm
    mmmmm1111111mmmm
    mmm1155566511mmm
    mm155665554441mm
    m15666555544431m
    m1566555544433m1
    m1555554444333m1
    m1455544444333m1
    m1444444433332m1
    m1344443333322m1
    m1333333332221m1
    mm1333322222111m
    mm11322222111mmm
    mmm111111111mmmm
    mmmmm1111mmmmmmm
    mmmmmmmmmmmmmmmm
'''))

mt('pillar', 'stone', 'SOLID', L({'m': 0xe}, '''
    eeeeeeeeeeeeeeee
    eee1111111111eee
    ee155566665531ee
    ee143444444431ee
    eee1545645441eee
    eee1545645431eee
    eee1545645431eee
    eee1545645431eee
    eee1e45645431eee
    eee1545e45431eee
    eee1545645431eee
    ee155556655431ee
    e15555666554421e
    e14444444443321e
    ee111111111111ee
    eeeeeeeeeeeeeeee
'''))

mt('ruin_wall', 'stone', 'SOLID', A('''
    eeee11111111eeee
    e111455555541eee
    1556444444431e1e
    1444444444431151
    1333444444331441
    1111111111111331
    1455541455554411
    1444431444444431
    1444431e44444431
    1333321444333331
    1111111111111111
    1455554414555441
    1444444314444431
    1444444e14e44431
    1333333311333321
    1111111111111111
'''))

# A stone statue: a seated hare with a glowing gem, the shrine's keeper.
mt('statue', 'stone', 'SOLID', L({'m': 0xe}, '''
    mmmmm1mm1mmmmmmm
    mmmm151151mmmmmm
    mmmm154154mmmmmm
    mmmm1545541mmmmm
    mmmm15555541mmmm
    mmm1544144431mmm
    mmm15444444431mm
    mmm1544449a431mm
    mmm154444a44431m
    mmm1544444444431
    mmmm1544444443 1
    mmmm15444444331m
    mmmm1443333321mm
    mmm1555555554 1m
    mmm1444444443 1m
    mmmm1111111111mm
'''), coll=3)
METATILES[-1]['art'] = [r.replace(' ', '3') for r in METATILES[-1]['art']]

# Water: deep blue with lit wave bands and foam sparkles; two frames.
_w1 = A('''
    8888898888889888
    7888899888889988
    7788889888a89888
    7788888888888888
    8888888888888888
    8898888898888889
    8998888a988888a9
    8988888898888898
    8888888888888888
    8888888888888888
    8889888888988888
    8a99888889988888
    8899888888988888
    7888888888888888
    7788888888888888
    7788888888888888
''')
_w2 = A('''
    7888889888888988
    7788889988888898
    7788888988a88888
    8888888888888888
    8888888888888888
    8888898888889888
    8888a98888889988
    8888898888889a88
    8888888888888888
    8888888888888888
    8898888888898888
    8998888888a98888
    8898888888998888
    7888888888888888
    7788888888888888
    7788888888888888
''')
mt('water', 'stone', 'WATER', frames=[_w1, _w2], anim_speed=20)


# Water against ground: a dark bank and a fringe of foam on each side the
# ground lies, one tile per combination (N=1, E=2, S=4, W=8), the foam
# drifting between the frames.
def banked(frame, mask, phase):
    c = Canvas.from_rows(frame)

    def foam(i):
        return ((i + phase) % 6) < 2

    if mask & 1:
        for x in range(16):
            c.set(x, 0, 1)
            c.set(x, 1, 0xa if foam(x) else 7)
    if mask & 4:
        for x in range(16):
            c.set(x, 15, 1)
            c.set(x, 14, 0xa if foam(x + 3) else 8)
    if mask & 8:
        for y in range(16):
            c.set(0, y, 1)
            c.set(1, y, 0xa if foam(y) else 7)
    if mask & 2:
        for y in range(16):
            c.set(15, y, 1)
            c.set(14, y, 0xa if foam(y + 3) else 8)
    return c.rows()


for _m in range(1, 16):
    mt('water_%x' % _m, 'stone', 'WATER', frames=[banked(_w1, _m, 0), banked(_w2, _m, 2)], anim_speed=20)

# A lily pad on the water, a pale gold bud on it.
_lily = A('''
    ................
    ................
    ................
    ....11111.......
    ...1eeeeee1.....
    ..1eeeeeee e1...
    ..1ee1ddeeee1...
    ..1ee1cdeeee1...
    ..1eeee1eee1....
    ...1eeeeee1.....
    ....111111......
    ................
    ................
    ................
    ................
    ................
''')
_lily = [r.replace(' ', 'e') for r in _lily]
mt('water_lily', 'stone', 'WATER', frames=[compose(_w1, _lily), compose(_w2, _lily)], anim_speed=20)

# Pits: a dark hole with a stone lip on the near edge.
mt('pit', 'stone', 'PIT', A('''
    eeeeeeeeeeeeeeee
    eeeeeeeeeeeeeeee
    1111111111111111
    4544454444544454
    3333333333333333
    2222122222122222
    1111111111111111
    0000000000000000
    0000000000000000
    0000000000000000
    0000000000000000
    0000000000000000
    0000000000000000
    0000000000000000
    0000000000000000
    0000000000000000
'''))
mt('pit_inner', 'stone', 'PIT', flat(0))

# Ledges: grass ends in a cliff of stone blocks.
mt('ledge_s', 'stone', 'LEDGE_S', A('''
    eeeeeeeeeeeeeeee
    eeeeeeeeeeeeeeee
    eeeeeeeeeeeeeeee
    eeeeeeeeeeeeeeee
    6666666666666666
    1111111111111111
    5555515555551555
    4444414444441444
    4444414444441444
    1111111111111111
    4451444444144444
    4451444444144444
    3331333333133333
    1111111111111111
    2222222222222222
    1111111111111111
'''))
mt('ledge_n', 'stone', 'LEDGE_N', A('''
    1111111111111111
    2222222222222222
    1111111111111111
    3331333333133333
    4451444444144444
    4451444444144444
    1111111111111111
    4444414444441444
    5555515555551555
    1111111111111111
    6666666666666666
    eeeeeeeeeeeeeeee
    eeeeeeeeeeeeeeee
    eeeeeeeeeeeeeeee
    eeeeeeeeeeeeeeee
    eeeeeeeeeeeeeeee
'''))

# ---------------------------------------------------------------- gates --
mt('crack', 'stone', 'CRACK', A('''
    1111111111111111
    1555555555555551
    1544444441444441
    1544444411444441
    1544444414444441
    1544444144444441
    1544441444444441
    1544441144444441
    1544444144444441
    1544444411444441
    1544444441444441
    1544444441444441
    1544444414444441
    1544444414444441
    1333333133333331
    1111111111111111
'''))
mt('web', 'stone', 'WEB', A('''
    2122222222222212
    1612222222222161
    2161222222221612
    2216122222216122
    2221612222161222
    2222161221612222
    2222216116122222
    2266666666666622
    2222216116122222
    2222161221612222
    2221612222161222
    2216122222216122
    2161222a22221612
    1612222222222161
    2122222222222212
    2222222222222222
'''))
mt('door_locked', 'stone', 'DOOR', A('''
    1111111111111111
    1455555555555541
    1411111111111141
    141ffbffbffbf141
    141fbb4b4bbbf141
    141ff5fff5fff141
    141fbbfbfbbbf141
    141ffbffbffbf141
    141fbbfcdcbbf141
    141ff5fdcdff5141
    141fbbfbcbbbf141
    141ffbffbffbf141
    141fbbfbfbbbf141
    141ffbffbffbf141
    1411111111111141
    1111111111111111
'''))
mt('door_open', 'stone', 'DOOR_OPEN', A('''
    1111111111111111
    1455555555555541
    1411111111111141
    1412222222222141
    1412111111112141
    1412111111112141
    1412111111112141
    1412111111112141
    1412111111112141
    1412111111112141
    1412111111112141
    1412111111112141
    1412111111112141
    1412222222222141
    1411111111111141
    1111111111111111
'''))

_censer = L({'m': 0xe}, '''
    mmmmmmmmmmmmmmmm
    mmmmmmmmmmmmmmmm
    mmmmmmmmmmmmmmmm
    mmmmmmmmmmmmmmmm
    mmmmm111111mmmmm
    mmmm15666531mmmm
    mmmm14555431mmmm
    mmmmm143331mmmmm
    mmmmmm1431mmmmmm
    mmmmmm1431mmmmmm
    mmmmmm1431mmmmmm
    mmmmm155431mmmmm
    mmmm15555431mmmm
    mmmm14444331mmmm
    mmmm11111111mmmm
    mmmmmmmmmmmmmmmm
''')
_flame1 = A('''
    ................
    ......cc........
    .....cddc.......
    .....cddc.......
    ....cddddc......
    .....1dd1.......
''')
_flame2 = A('''
    .......c........
    ......cdc.......
    .....cddc.......
    ....cdddcc......
    .....cddc.......
    .....1dd1.......
''')
mt('torch', 'stone', 'TORCH', _censer, coll=3)
mt('torch_lit', 'stone', 'TORCH_LIT', frames=[compose(_censer, _flame1), compose(_censer, _flame2)], coll=3, anim_speed=6)

mt('chest', 'stone', 'CHEST', L({'m': 0xe}, '''
    mmmmmmmmmmmmmmmm
    mmmmmmmmmmmmmmmm
    mmm1111111111mmm
    mm1cddcffcddc1mm
    m1cdcfffffcdcc1m
    m1ccfffffffbcc1m
    m1ffffffffffbb1m
    m1111111111111mm
    m1ccffdcdffbcc1m
    m1ccffcdcffbcc1m
    m1ffffbbbfffbb1m
    m1ffffffffffbb1m
    m1ccbbbbbbbbcc1m
    m1cbbbbbbbbbbb1m
    mm111111111111mm
    mmmmmmmmmmmmmmmm
'''))
mt('chest_open', 'stone', 'CHEST_OPEN', L({'m': 0xe}, '''
    mmm1111111111mmm
    mm1cdccffccdc1mm
    m1cdcbbbbbbcdc1m
    m1ccbbbbbbbbcc1m
    m1cbbbbbbbbbbc1m
    m1111111111111mm
    m1dddddddddddd1m
    m1ddddddddddddd1
    m1ccffdddffbcc1m
    m1ccffdddffbcc1m
    m1ffffbbbfffbb1m
    m1ffffffffffbb1m
    m1ccbbbbbbbbcc1m
    m1cbbbbbbbbbbb1m
    mm111111111111mm
    mmmmmmmmmmmmmmmm
'''))

mt('bones', 'forest', 'FLOOR', marks(GRASS, [
    (A('''
        cc...cc
        .ccccc.
        cc...cc
    '''), 1, 2),
    (A('''
        c9.
        .c9
        ..c9
        ...c9
    '''), 9, 3),
    (A('''
        .cc.
        c99c
        c11c
        .cc.
    '''), 10, 9),
    (TUFT['a'], 6, 7), (TUFT['e'], 13, 14), (TUFT['c'], 0, 14), (TUFT['b'], 3, 11)]))

_sp = [A('''
    ................
    ................
    ....d...........
    ...dfd..........
    ....d.......c...
    ................
    ................
    ................
    ..........c.....
    .........cdc....
    ..........c.....
    ................
    ...c............
    ................
    ................
    ................
'''), A('''
    ................
    ................
    ....c...........
    ................
    ............d...
    ...........dfd..
    ............d...
    ................
    ................
    ..........d.....
    ................
    ................
    ..dc............
    ..cd............
    ................
    ................
'''), A('''
    ................
    ................
    ................
    ....c...........
    ................
    ............c...
    ................
    ................
    ..........d.....
    .........dfd....
    ..........d.....
    ................
    ...d............
    ..dfd...........
    ...d............
    ................
''')]
_sp = [[r.replace('f', 'd') for r in fr] for fr in _sp]
mt('sparkle', 'stone', 'FLOOR', frames=_sp, anim_speed=14)

mt('relic', 'stone', 'FLOOR', L({'m': 0xe}, '''
    mmmmmmmmmmmmmmmm
    mmmmm111111mmmmm
    mmm1155555511mmm
    mm155555444441mm
    m15555444444431m
    m15554444444331m
    m15544444443331m
    m15444444333321m
    m14444433333221m
    m14443333322221m
    mm143333222221mm
    mmm1133322211mmm
    mmmmm111111mmmmm
    mmmmmmmmmmmmmmmm
    mmmmmmmmmmmmmmmm
    mmmmmmmmmmmmmmmm
'''))
mt('mossy_stone', 'stone', 'FLOOR', L({'m': 0xe}, '''
    mmmmmmmmmmmmmmmm
    mm11111111111mmm
    m1555555555541mm
    m154444444444e1m
    m15444444444441m
    m1e444444444431m
    m15444444444431m
    m154444444e4431m
    m15444444444331m
    m14443333333321m
    mm1333333333211m
    mmm111111111mmmm
    mmmmmmmmmmmmmmmm
    mmmmmmmmmmmmmmmm
    mmmmmmmmmmmmmmmm
    mmmmmmmmmmmmmmmm
'''))
mt('black', 'forest', 'SOLID', flat(1))

# A stone arch with steps going down into the dark.
mt('stairs_down', 'stone', 'STAIRS', A('''
    1111111111111111
    1455555555555541
    1544444444444451
    1541111111111451
    1541555555551451
    1541444444441451
    1541111111111451
    1541444444441451
    1541333333331451
    1541111111111451
    1541333333331451
    1541222222221451
    1541111111111451
    1541222222221451
    1441111111111441
    1111111111111111
'''))

# ============================================================== blight ===
# The deep rooms: purple ground split by glowing cracks, crystal
# clusters, dead trees that still glow at the root.
BL_CRACK = A('''
    2....
    .2...
    .2...
    ..2..
    ..22.
''')
BL_GLOW = A('''
    .6.
    676
    .6.
''')
BL_PATCH = A('''
    .44.
    4554
    4554
    .44.
''')
BL = 3
STAIN = A('''
    ...333....
    .33344333.
    3344455433
    3344555443
    .334444433
    ..3333333.
''')
STAIN2 = A('''
    ..333..
    .34443.
    3345543
    .34443.
    ..333..
''')
GTUFT = A('''
    .d
    c.
''')
# the deep rooms' grass, stained and cracked
mt('blight_ground0', 'blight', 'FLOOR', marks(0xd, [
    (STAIN, 1, 1), (GTUFT, 12, 2), (GTUFT, 4, 11), (GTUFT, 11, 9), (A('2'), 8, 13), (A('6'), 4, 3)]))
mt('blight_ground1', 'blight', 'FLOOR', marks(0xd, [
    (STAIN2, 8, 8), (GTUFT, 13, 5), (GTUFT, 1, 13), (GTUFT, 3, 3), (A('2'), 12, 1), (A('6'), 10, 10)]))
# stained grass split by a glowing crack
_bg2 = marks(0xd, [(STAIN, 6, 7), (STAIN2, 1, 1), (GTUFT, 13, 3), (GTUFT, 2, 13), (A('2'), 11, 13)])
_gv1 = A('''
    ................
    ...........2....
    ..........26....
    ..........6.....
    .........76.....
    .........6......
    ........26......
    ........6.......
    .......26.......
    .......6........
    ......67........
    ......6.........
    .....2..........
    ................
    ................
    ................
''')
_gv2 = A('''
    ................
    ...........2....
    ..........27....
    ..........7.....
    .........67.....
    .........7......
    ........27......
    ........6.......
    .......26.......
    .......7........
    ......76........
    ......7.........
    .....2..........
    ................
    ................
    ................
''')
mt('blight_ground2', 'blight', 'FLOOR', frames=[compose(_bg2, _gv1), compose(_bg2, _gv2)], anim_speed=12)
# the arena's floor: purple through and through
mt('blight_floor', 'blight', 'FLOOR', marks(BL, [
    (BL_CRACK, 2, 1), (BL_PATCH, 9, 3), (A('2'), 13, 8), (BL_CRACK, 11, 9), (BL_PATCH, 2, 10),
    (A('5'), 6, 7), (A('2'), 7, 14), (A('5'), 14, 14)]))
_bv = marks(BL, [(BL_PATCH, 1, 1), (A('2'), 12, 3), (BL_PATCH, 10, 11), (A('5'), 4, 13)])
_vein1 = A('''
    ................
    ................
    .........6......
    ........676.....
    .......6.6......
    ......6.........
    ......6.........
    .....6..........
    ....676.........
    .....6..........
    ..............6.
    ................
    ................
    ................
    ................
    ................
''')
_vein2 = A('''
    ................
    ................
    .........7......
    ........767.....
    .......7.6......
    ......6.........
    ......7.........
    .....6..........
    ....767.........
    .....7..........
    ..............7.
    ................
    ................
    ................
    ................
    ................
''')
mt('blight_vein', 'blight', 'FLOOR', frames=[compose(_bv, _vein1), compose(_bv, _vein2)], anim_speed=12)

mt('blight_crystal', 'blight', 'SOLID', L({'g': 3}, '''
    gggggggg1ggggggg
    ggggggg1b1gggggg
    ggg1ggg1b71ggggg
    gg1b1g1bb71ggggg
    gg1b51g1b71g1ggg
    g1bb51g1b71g1b1g
    g1b551g1b71g1b51
    g15541g1b71g1551
    g1b55411b7111541
    g15544155b71b541
    g1544415b75155 1
    g1444415575144 1
    gg1441154451441g
    gg1111115411111g
    gggg2g2111g2gggg
    gggggggggggggggg
'''))
METATILES[-1]['art'] = [r.replace(' ', '1') for r in METATILES[-1]['art']]

mt('dead_tree', 'blight', 'SOLID', L({'g': 3}, '''
    gg1ggggggggg1ggg
    g1a1ggg1ggg1a1gg
    g1a1gg1a1g1a91gg
    gg1a11a91g1a1ggg
    ggg1aa91gg1a1ggg
    gggg1a91gg191ggg
    ggggg1a91g191ggg
    gggggg1a9191gggg
    ggggggg1a91ggggg
    ggggggg1a81ggggg
    gggggg1a981ggggg
    gggggg1a981ggggg
    ggggg1aa9881gggg
    gg6g1a999888 16g
    g6g1111111111g6g
    ggg6ggg6gg6ggggg
'''), coll=3)
METATILES[-1]['art'] = [r.replace(' ', '1') for r in METATILES[-1]['art']]

# ========================================================== set pieces ===
# Things that span several tiles, painted whole and sliced: a great tree
# of 3x4, a flower meadow of 3x3, clover and mushroom rings of 2x2, a
# great boulder of 2x2, a hollow log of 2x1, a lily raft of 2x2 on the
# water, the ends of a cliff, the corners of a lake.
import math


def piece(name, pal, types, rows, w, h, coll=None, frames=None):
    """A w x h metatile painting sliced row-major into name_0..; types is
    one type for all tiles or one per tile. frames: a list of whole
    paintings for an animated piece."""
    for i in range(w * h):
        tx, ty = i % w, i // w
        t = types[i] if isinstance(types, (list, tuple)) else types
        if frames:
            mt('%s_%d' % (name, i), pal, t, frames=[slice16(f, tx, ty) for f in frames], coll=coll, anim_speed=20)
        else:
            mt('%s_%d' % (name, i), pal, t, slice16(rows, tx, ty), coll=coll)


# The great tree: a crown of lit leaf masses 48 wide, a thick trunk with a
# hollow, roots that spread over three tiles of turf. The crown rides the
# overlay layer over whatever is behind it; the roots are ground.
def great_tree_art():
    c = Canvas(48, 64)
    crown = [(24, 9, 8.5), (12, 14, 9.5), (36, 14, 9.5), (24, 17, 13.0), (7, 25, 7.0), (41, 25, 7.0),
             (15, 31, 9.0), (33, 31, 9.0), (24, 35, 8.5), (24, 42, 5.5)]
    for cx, cy, r in sorted(crown, key=lambda q: q[1]):
        blob(c, cx, cy, r, (2, 4, 5, 6), wrap=False)
    # the trunk
    c.rect(19, 40, 28, 60, 8)
    c.vline(19, 40, 60, 7)
    c.vline(20, 43, 59, 9)
    c.vline(28, 40, 60, 7)
    c.vline(27, 42, 60, 8)
    c.vline(23, 46, 56, 9)
    c.vline(25, 44, 52, 7)
    # a hollow, dark, with a lit lip
    c.ellipse(24, 51, 2.5, 3.5, 1)
    c.set(22, 48, 0xa)
    c.set(23, 48, 0xa)
    # the roots
    c.hline(9, 18, 58, 8); c.hline(5, 13, 59, 7); c.hline(11, 18, 59, 9); c.hline(7, 11, 60, 8)
    c.hline(29, 38, 58, 8); c.hline(34, 42, 59, 7); c.hline(29, 36, 59, 9); c.hline(36, 40, 60, 8)
    c.hline(19, 28, 61, 7)
    c.hline(14, 19, 57, 9); c.hline(28, 33, 57, 9)
    c.outline(1)
    return c.rows()


_gtree = great_tree_art()
for _i in range(9):
    mt('gtree_%d' % _i, 'wood', 'FLOOR', slice16(_gtree, _i % 3, _i // 3))
_root_w = marks(GRASS, [(TUFT['a'], 1, 2), (TUFT['e'], 2, 12), (TUFT['c'], 12, 1)])
_root_e = marks(GRASS, [(TUFT['b'], 12, 3), (TUFT['a'], 2, 13), (TUFT['f'], 13, 12)])
_root_c = marks(GRASS, [(TUFT['e'], 1, 1), (TUFT['c'], 14, 2)])
mt('gtree_9', 'forest', 'FLOOR', compose(_root_w, slice16(_gtree, 0, 3)))
mt('gtree_10', 'forest', 'SOLID', compose(_root_c, slice16(_gtree, 1, 3)), coll=3)
mt('gtree_11', 'forest', 'FLOOR', compose(_root_e, slice16(_gtree, 2, 3)))


# A flower meadow: 48x48 of turf, blossoms thickest at the heart round a
# flat mossy stone, thinning to the rim so it blends into the grass.
def meadow_art(seed):
    rnd = random.Random(seed)
    c = Canvas.from_rows(turf(seed, 4, 3, 5, 26, 16, 48, 48))
    flowers = [FLOWER_BLUE, FLOWER_PINK, FLOWER_CREAM, FLOWER_GOLD]
    for i in range(40):
        ang = rnd.random() * 2 * math.pi
        rad = (rnd.random() ** 0.55) * 21
        x, y = int(24 + rad * math.cos(ang)), int(24 + rad * math.sin(ang))
        if abs(x - 24) < 7 and abs(y - 25) < 4:
            continue
        c.blit(flowers[i % 4], x - 1, y - 1)
    for i in range(16):
        c.blit(TUFT['abcdef'[i % 6]], rnd.randrange(45), rnd.randrange(45))
    c.ellipse(24.5, 26, 6.5, 3.5, 7)
    c.ellipse(24, 25.5, 6, 3, 8)
    c.ellipse(23, 24.5, 4, 1.8, 9)
    c.set(22, 24, 0xc)
    c.set(21, 24, 0xc)
    return c.rows()


piece('meadow', 'forest', 'FLOOR', meadow_art(7), 3, 3)

# Clover: dark three-leaved clumps on the turf, a cream gleam on the lucky one.
CLOVER = A('''
    .3.3.
    33233
    .333.
    ..2..
''')


def clover_art(seed):
    rnd = random.Random(seed)
    c = Canvas.from_rows(turf(seed, 4, 3, 5, 10, 6, 32, 32))
    for i in range(14):
        c.wrap_blit(CLOVER, rnd.randrange(32), rnd.randrange(32))
    c.set(13, 14, 0xc)
    c.set(21, 23, 0xc)
    return c.rows()


piece('clover', 'forest', 'FLOOR', clover_art(3), 2, 2)


# A fairy ring: glowing mushrooms in a circle round a violet stain.
def shroomring_art():
    c = Canvas.from_rows(turf(11, 4, 3, 5, 10, 4, 32, 32))
    c.ellipse(16, 16.5, 6, 4, 0xd)
    c.ellipse(15.5, 16, 4, 2.5, 0xe)
    c.ellipse(15, 15.5, 2, 1, 0xd)
    for k in range(8):
        ang = k * math.pi / 4 + 0.3
        x, y = int(16 + 11 * math.cos(ang)), int(16 + 9 * math.sin(ang))
        c.blit(MUSHROOM, x - 2, y - 2)
    return c.rows()


piece('shroomring', 'forest', 'FLOOR', shroomring_art(), 2, 2)


# A great boulder: a lit stone two tiles across, moss on its crown, a
# crack down its face, a shadow under it.
def gboulder_art():
    c = Canvas(32, 32)
    ball(c, 16, 15, 13.5, 11.5, (2, 3, 4, 5, 6))
    c.ellipse(11, 6.5, 5, 2.2, 0xe)
    c.ellipse(20, 5.5, 3, 1.4, 0xe)
    for i, (x, y) in enumerate(((18, 10), (18, 11), (19, 12), (19, 13), (20, 14), (20, 15), (21, 16), (21, 17), (22, 18))):
        c.set(x, y, 1)
        if i % 3 == 0:
            c.set(x + 1, y, 2)
    c.hline(5, 27, 27, 2)
    c.outline(1)
    return opaque(c.rows(), 'e')


piece('gboulder', 'stone', 'SOLID', gboulder_art(), 2, 2)


# A hollow log two tiles long: rings at the cut end, a dark hollow at the
# other, moss on its back.
def hlog_art():
    c = Canvas(32, 16)
    c.rect(3, 4, 29, 12, 8)
    c.hline(4, 28, 4, 0xa)
    c.hline(4, 28, 5, 9)
    c.hline(4, 28, 11, 7)
    c.hline(4, 28, 12, 7)
    for x in (9, 14, 20, 25):
        c.set(x, 7, 7)
        c.set(x + 1, 8, 7)
    c.ellipse(5.5, 8.5, 3, 4.5, 9)
    c.ellipse(5.5, 8.5, 2, 3.5, 1)
    c.ellipse(27.5, 8.5, 3, 4.5, 9)
    c.ellipse(27.5, 8.5, 2, 3.5, 8)
    c.ellipse(27.5, 8.5, 1, 2, 9)
    c.ellipse(14, 4.5, 4, 1.2, 0x5)
    c.ellipse(22, 4.5, 2.5, 1, 0x5)
    c.outline(1)
    return opaque(c.rows(), 'e')


piece('hlog', 'wood', 'SOLID', hlog_art(), 2, 1)


# A lily raft: broad pads on open water, a gold lotus on the largest.
def raft_art(frame):
    c = Canvas(32, 32)
    for ty in range(2):
        for tx in range(2):
            c.blit(frame, tx * 16, ty * 16)
    for cx, cy, r in ((11, 12, 6.5), (23, 20, 5.5), (8, 24, 4.0), (24, 8, 3.5)):
        c.ellipse(cx, cy, r + 0.6, r * 0.8 + 0.6, 1)
        c.ellipse(cx, cy, r, r * 0.8, 0xe)
        c.set(int(cx + r * 0.6), int(cy - r * 0.5), 1)
        c.set(int(cx + r * 0.7), int(cy - r * 0.3), 1)
    c.blit(A('''
        .d.d.
        dcdcd
        .ddd.
        ..c..
    '''), 9, 9)
    return c.rows()


piece('raft', 'stone', 'WATER', None, 2, 2, frames=[raft_art(_w1), raft_art(_w2)])

# The ends of a cliff: the stone face stops and the grass wraps round.
_ledge_rows = next(m for m in METATILES if m['name'] == 'ledge_s')['art']
_cap_w = []
for _y, _r in enumerate(_ledge_rows):
    if _y < 4:
        _cap_w.append(_r)
    else:
        _cap_w.append('eee' + ('1' if _y < 15 else 'e') + _r[4:])
mt('ledge_s_w', 'stone', 'LEDGE_S', _cap_w)
mt('ledge_s_e', 'stone', 'LEDGE_S', hflip(_cap_w))


# Open water with ground at a corner: a nick of bank and foam there.
def nicked(frame, dmask, phase):
    c = Canvas.from_rows(frame)

    def nick(x0, y0, sx, sy):
        c.set(x0, y0, 1)
        c.set(x0 + sx, y0, 1)
        c.set(x0, y0 + sy, 1)
        c.set(x0 + sx, y0 + sy, 0xa if phase == 0 else 7)
        c.set(x0 + 2 * sx, y0, 7)
        c.set(x0, y0 + 2 * sy, 7)

    if dmask & 1:
        nick(0, 0, 1, 1)
    if dmask & 2:
        nick(15, 0, -1, 1)
    if dmask & 4:
        nick(15, 15, -1, -1)
    if dmask & 8:
        nick(0, 15, 1, -1)
    return c.rows()


for _m in range(1, 16):
    mt('water_c%x' % _m, 'stone', 'WATER', frames=[nicked(_w1, _m, 0), nicked(_w2, _m, 1)], anim_speed=20)

# ====================================================== the sickness ===
# After the forest board again: the ground darker and the lights
# brighter; rocks sunk in moss and soil on a palette of their own, in
# several shapes; trees in several shapes, lanterns hung in them; the
# blight glowing, with its own dead trees and a mist.
def remt(name, pal, type_, art=None, frames=None, coll=None, anim_speed=8):
    """replace a metatile in place, keeping its id"""
    for i, m in enumerate(METATILES):
        if m['name'] == name:
            d = {'name': name, 'pal': pal, 'type': type_}
            if frames:
                d['frames'] = frames
            else:
                d['art'] = art
            if coll is not None:
                d['coll'] = coll
            if anim_speed:
                d['anim_speed'] = anim_speed
            METATILES[i] = d
            return
    raise KeyError(name)


# Palette 'cliff': 1 outline, 2-6 stone deep..bright, 7-9 moss dark..light,
# A-B soil dark..light, C cream, D lichen violet, E grass mid, F grass
# bright. Turf on it: grass with moss-dark dashes and bright tips.
def cturf(seed, w=16, h=16):
    return turf(seed, 0xe, 7, 0xf, 6, 5, w, h)


def rock_on(ground, draw, w=16, h=16):
    """draw(c) paints a rock on a transparent canvas; it is outlined and
    laid on the ground rows, with a soil shadow under it first."""
    g = Canvas.from_rows(ground)
    c = Canvas(w, h)
    draw(c)
    c.outline(1)
    return compose(g.rows(), c.rows())


def soil_ring(g, cx, cy, rx, ry):
    g.ellipse(cx, cy, rx, ry, 0xa)
    g.ellipse(cx, cy - 0.5, rx - 1, ry - 1, 0xb)


# a mossy stone sunk in the soil, tufts over its foot
def _rock(c):
    ball(c, 8, 8.5, 6.5, 5.5, (2, 3, 4, 5, 6))
    c.ellipse(6, 4.5, 3.5, 1.5, 8)
    c.ellipse(5.5, 4, 2, 0.8, 9)
    c.set(12, 7, 0xd)
    c.set(3, 10, 0xd)


_g = Canvas.from_rows(cturf(21)); soil_ring(_g, 8, 11, 8, 4.5)
_r = rock_on(_g.rows(), _rock)
_r = compose(_r, A('''
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ..f.........f...
    .f9........f9...
    ................
    ................
    ................
'''))
remt('rock', 'cliff', 'SOLID', _r)


# a flat stone buried to its shoulders, grass growing over its edge
def _rock2(c):
    c.ellipse(8, 9.5, 7, 3.6, 3)
    c.ellipse(7.5, 9, 6.5, 3, 4)
    c.ellipse(6.5, 8, 4.5, 1.8, 5)
    c.ellipse(5.5, 7.5, 2, 0.8, 6)
    c.set(10, 10, 2)
    c.set(11, 10, 2)


_g = Canvas.from_rows(cturf(22)); soil_ring(_g, 8, 11.5, 8, 3)
_r = rock_on(_g.rows(), _rock2)
_r = compose(_r, A('''
    ................
    ................
    ................
    ................
    ................
    ..............f.
    .............f9.
    ................
    ................
    ................
    ................
    ...f.......f....
    ..f9......f9e...
    ................
    ................
    ................
'''))
mt('rock2', 'cliff', 'SOLID', _r)


# two stones stacked, moss between them, lichen on the top one
def _rock3(c):
    ball(c, 8, 11, 6.5, 3.8, (2, 3, 4, 5, 6))
    ball(c, 7.5, 5.5, 4.5, 3.5, (2, 3, 4, 5, 6))
    c.ellipse(8, 8.5, 4.5, 1, 8)
    c.set(6, 3, 0xd)
    c.set(9, 4, 0xd)
    c.set(5, 5, 0xd)


_g = Canvas.from_rows(cturf(23)); soil_ring(_g, 8, 13, 7.5, 2.8)
mt('rock3', 'cliff', 'SOLID', rock_on(_g.rows(), _rock3))


# the small stone, light enough to lift, a cap of moss
def _rock_small(c):
    ball(c, 8, 9, 4.5, 3.8, (2, 3, 4, 5, 6))
    c.ellipse(7, 6.5, 2.5, 1, 8)
    c.set(6, 6, 9)


_g = Canvas.from_rows(cturf(24)); soil_ring(_g, 8, 11.5, 5.5, 2.5)
remt('rock_small', 'cliff', 'LIFT1', rock_on(_g.rows(), _rock_small))


# the boulder: dark, cracked, mossy; only the gauntlet moves it
def _boulder(c):
    ball(c, 8, 8, 7, 6.5, (2, 3, 4, 5, 6))
    for x, y in ((9, 4), (9, 5), (10, 6), (10, 7), (11, 8), (11, 9), (12, 10)):
        c.set(x, y, 1)
    c.ellipse(5.5, 3.5, 3, 1.4, 8)
    c.set(4, 3, 9)
    c.set(3, 9, 0xd)
    c.set(12, 5, 0xd)


_g = Canvas.from_rows(cturf(25)); soil_ring(_g, 8, 12, 8, 3.5)
remt('boulder', 'cliff', 'LIFT2', rock_on(_g.rows(), _boulder))


# the great boulder again: moss on its crown, lichen, a sapling rooted in a crack
def _gboulder(c):
    ball(c, 16, 15.5, 13.5, 11.5, (2, 3, 4, 5, 6))
    c.ellipse(11, 7, 6, 2.6, 8)
    c.ellipse(10, 6.5, 4, 1.4, 9)
    c.ellipse(21, 6, 3, 1.4, 8)
    for i, (x, y) in enumerate(((18, 10), (18, 11), (19, 12), (19, 13), (20, 14), (20, 15), (21, 16), (21, 17), (22, 18))):
        c.set(x, y, 1)
        if i % 3 == 0:
            c.set(x + 1, y, 2)
    for x, y in ((6, 12), (7, 16), (25, 12), (24, 19), (14, 22)):
        c.set(x, y, 0xd)
    # the sapling
    c.vline(23, 1, 6, 0xb)
    c.set(23, 0, 9)
    c.set(22, 2, 9); c.set(21, 2, 8); c.set(24, 3, 9); c.set(25, 3, 8); c.set(22, 4, 9)


_g = Canvas.from_rows(cturf(26, 32, 32)); soil_ring(_g, 16, 25, 15, 5)
_rows = rock_on(_g.rows(), _gboulder, 32, 32)
for _i in range(4):
    remt('gboulder_%d' % _i, 'cliff', 'SOLID', slice16(_rows, _i % 2, _i // 2))


# a rock wedged in the roots of a stump: roots of soil-brown wrap a stone
def _treerock(c):
    ball(c, 13, 17, 8.5, 7, (2, 3, 4, 5, 6))
    c.ellipse(10, 11.5, 4, 1.6, 8)
    # the stump
    c.rect(18, 2, 28, 14, 0xb)
    c.vline(18, 2, 14, 0xa); c.vline(19, 3, 14, 0xa)
    c.vline(27, 2, 14, 0xa)
    c.ellipse(23, 2.5, 5, 1.8, 0xb); c.ellipse(23, 2.5, 3.5, 1.1, 0xc); c.ellipse(23, 2.5, 2, 0.6, 0xb)
    # roots over the stone
    for x0, y0, x1, y1 in ((20, 14, 12, 20), (22, 14, 17, 22), (26, 14, 29, 24)):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for k in range(n + 1):
            x = x0 + (x1 - x0) * k // n
            y = y0 + (y1 - y0) * k // n
            c.set(x, y, 0xb); c.set(x + 1, y, 0xb); c.set(x, y + 1, 0xa)
    c.set(5, 14, 0xd); c.set(8, 21, 0xd)


_g = Canvas.from_rows(cturf(27, 32, 32)); soil_ring(_g, 15, 25, 14, 5)
_rows = rock_on(_g.rows(), _treerock, 32, 32)
piece('treerock', 'cliff', 'SOLID', _rows, 2, 2)


# cliffs on the cliff palette: a mossy brow, blocks of stone hung with
# moss, a foot of soil
_cliff = A('''
    eeeeeeeeeeeeeeee
    eeeeeeeeeeeeeeee
    eeeeeeeeeeeeeeee
    eeeeeeeeeeeeeeee
    9999999999999999
    1111111111111111
    5555515555551555
    4484414444441484
    4444414448441444
    1111111111111111
    4451444444144444
    4451448444144884
    3331333333133333
    1111111111111111
    aaaaaaaaaaaaaaaa
    bbabbbbbabbbbbba
''')
_cliff = compose(cturf(28), _cliff)
remt('ledge_s', 'cliff', 'LEDGE_S', _cliff)
_cap_w = []
for _y, _r in enumerate(_cliff):
    if _y < 4:
        _cap_w.append(_r)
    else:
        _cap_w.append(cturf(28)[_y][:3] + ('1' if _y < 14 else 'a') + _r[4:])
remt('ledge_s_w', 'cliff', 'LEDGE_S', _cap_w)
remt('ledge_s_e', 'cliff', 'LEDGE_S', hflip(_cap_w))
remt('ledge_n', 'cliff', 'LEDGE_N', vflip(_cliff))
remt('pit', 'cliff', 'PIT', compose(cturf(29), A('''
    ................
    ................
    1111111111111111
    4544454444544454
    3333333333333333
    2222122222122222
    1111111111111111
    0000000000000000
    0000000000000000
    0000000000000000
    0000000000000000
    0000000000000000
    0000000000000000
    0000000000000000
    0000000000000000
    0000000000000000
''')))


# ---------------------------------------------------------------- trees --
def tree_piece(name, rows, crown_pal, ground_pal, ground_w, ground_e, coll=3):
    """a 2x3 tree: crown on the overlay (4 tiles), trunks solid on the ground"""
    for i in range(4):
        mt('%s_%d' % (name, i), crown_pal, 'FLOOR', slice16(rows, i % 2, i // 2))
    mt('%s_4' % name, ground_pal, 'SOLID', compose(ground_w, slice16(rows, 0, 2)), coll=coll)
    mt('%s_5' % name, ground_pal, 'SOLID', compose(ground_e, slice16(rows, 1, 2)), coll=coll)


LANTERN_SMALL = A('''
    .1.
    111
    1c1
    1d1
    1b1
    .1.
''')


def hang_lantern(rows, x, y):
    c = Canvas.from_rows(rows)
    c.blit(LANTERN_SMALL, x, y)
    for dx, dy in ((-2, 2), (4, 2), (-1, 6), (3, 6), (1, -2), (-3, 4), (5, 4)):
        if c.get(x + 1 + dx, y + 3 + dy) in (2, 3, 4):
            c.set(x + 1 + dx, y + 3 + dy, 0xc)
    return c.rows()


# the tree with a lantern hung in its crown
tree_piece('tree2', hang_lantern(_tree, 22, 18), 'wood', 'forest',
           marks(GRASS, [(TUFT['a'], 1, 2), (TUFT['e'], 3, 9), (TUFT['c'], 1, 13), (TUFT['b'], 9, 14)]),
           marks(GRASS, [(TUFT['b'], 11, 3), (TUFT['a'], 12, 8), (TUFT['e'], 7, 14), (TUFT['c'], 14, 13)]))


# a second great tree: lopsided, a lantern on its low branch, a knot
def great_tree2_art():
    c = Canvas(48, 64)
    crown = [(20, 8, 7.5), (32, 12, 9.0), (10, 16, 8.5), (26, 20, 12.0), (40, 24, 6.5), (6, 27, 6.0),
             (18, 31, 9.0), (34, 32, 8.0), (26, 38, 7.0), (12, 38, 5.0)]
    for cx, cy, r in sorted(crown, key=lambda q: q[1]):
        blob(c, cx, cy, r, (2, 4, 5, 6), wrap=False)
    c.rect(21, 42, 29, 60, 8)
    c.vline(21, 42, 60, 7); c.vline(22, 45, 59, 9)
    c.vline(29, 42, 60, 7); c.vline(28, 44, 60, 8)
    c.vline(25, 47, 57, 9)
    # the low branch to the left, and the lantern under it
    c.hline(8, 21, 44, 8); c.hline(6, 20, 45, 7); c.hline(10, 20, 43, 9)
    c.ellipse(26, 53, 2, 1.5, 7); c.set(26, 53, 1)
    c.hline(10, 20, 58, 8); c.hline(6, 15, 59, 7); c.hline(12, 20, 59, 9)
    c.hline(30, 40, 58, 8); c.hline(35, 43, 59, 7); c.hline(30, 37, 59, 9)
    c.hline(21, 29, 61, 7)
    c.hline(16, 21, 57, 9); c.hline(29, 34, 57, 9)
    c.outline(1)
    return hang_lantern(c.rows(), 10, 46)


_gtree2 = great_tree2_art()
for _i in range(9):
    mt('gtree2_%d' % _i, 'wood', 'FLOOR', slice16(_gtree2, _i % 3, _i // 3))
mt('gtree2_9', 'forest', 'FLOOR', compose(_root_w, slice16(_gtree2, 0, 3)))
mt('gtree2_10', 'forest', 'SOLID', compose(_root_c, slice16(_gtree2, 1, 3)), coll=3)
mt('gtree2_11', 'forest', 'FLOOR', compose(_root_e, slice16(_gtree2, 2, 3)))


_bground = marks(BL, [(BL_PATCH, 2, 10), (A('2'), 13, 8), (A('5'), 6, 14)])
_bground2 = marks(BL, [(BL_PATCH, 9, 11), (A('2'), 3, 9), (A('5'), 12, 13)])
# the blighted tree, 2x3 like the oaks: its crown on the overlay, its
# trunks solid at the foot (its art is the environment pack's). The
# atlas drew it 3x4 (btree_6..11 are what is left of that, not laid).
for _i in range(4):
    mt('btree_%d' % _i, 'blight', 'FLOOR', flat(0))
mt('btree_4', 'blight', 'SOLID', _bground, coll=3)
mt('btree_5', 'blight', 'SOLID', _bground2, coll=3)
for _i in range(6, 9):
    mt('btree_%d' % _i, 'blight', 'FLOOR', flat(0))
mt('btree_9', 'blight', 'FLOOR', _bground)
mt('btree_10', 'blight', 'FLOOR', _bground2)
mt('btree_11', 'blight', 'FLOOR', _bground)

# ---------------------------------------------------------------- blight --
# the deep rooms' floor: dark purple, pits of black, a few short seams of
# light that pulse
_bf2 = marks(3, [(A('22'), 3, 2), (A('2'), 4, 3), (A('222'), 10, 9), (A('22'), 11, 10), (A('2'), 13, 4), (A('2'), 6, 13),
                 (A('4'), 8, 6), (A('4'), 14, 14), (A('4'), 1, 8), (A('22'), 8, 14)])
_bcr1 = A('''
    ................
    ................
    ................
    ................
    ......6.........
    .......6........
    ................
    ................
    ................
    ................
    ............6...
    ...........6....
    ................
    ................
    ..6.............
    ................
''')
_bcr2 = [r.replace('6', '7') for r in _bcr1]
mt('blight_floor2', 'blight', 'FLOOR', frames=[compose(_bf2, _bcr1), compose(_bf2, _bcr2)], anim_speed=20)

# a mist that drifts over the deep rooms: sparse motes on the overlay
_mist1 = A('''
    ................
    ..5.......6.....
    ................
    ......5.........
    ..............5.
    ....6...........
    ................
    .........5......
    .5..............
    ..........6.....
    ......5.........
    ................
    ............5...
    ...6............
    ................
    .........5......
''')
_mist2 = A('''
    ................
    ...5.......6....
    ................
    .......5........
    ..............6.
    ....5...........
    ................
    ..........5.....
    ..5.............
    ...........6....
    .......5........
    ................
    .............5..
    ....6...........
    ................
    ..........5.....
''')
mt('blight_mist', 'blight', 'FLOOR', frames=[_mist1, _mist2], anim_speed=16)

# a sicker canopy: the leaves veined with light
_cb2 = leaf_mass(CANOPY_B, [(BLIGHT_TIP, 4, 1), (BLIGHT_TIP, 11, 7), (BLIGHT_TIP, 2, 8), (BLIGHT_TIP, 14, 13)], tones=(1, 2, 3, 4))
_cbv1 = A('''
    ................
    ......6.........
    .....6..........
    .....6....6.....
    ....67...6......
    ....6....6......
    ............6...
    ...........67...
    ...........6....
    ..6.............
    ..6.............
    .67.............
    .6........6.....
    .........6......
    .........6......
    ................
''')
_cbv2 = [r.replace('7', '6').replace('6', '7', 1) for r in _cbv1]
mt('canopy_blight2', 'wood', 'SOLID', frames=[compose(_cb2, _cbv1), compose(_cb2, _cbv2)], anim_speed=18)

# white sparkles on the ground, four-point stars that wink
_sw1 = A('''
    ................
    ....c...........
    ...ccc..........
    ..ccfcc.........
    ...ccc..........
    ....c...........
    ................
    ................
    ................
    ............c...
    ...........ccc..
    ............c...
    ................
    ................
    ......c.........
    ................
''')
_sw2 = A('''
    ................
    ................
    ....c...........
    ...ccc..........
    ....c...........
    ................
    ................
    ................
    ...........c....
    ..........ccc...
    .........ccfcc..
    ..........ccc...
    ...........c....
    ................
    ................
    ......c.........
''')
mt('sparkle_white', 'forest', 'FLOOR', frames=[_sw1, _sw2], anim_speed=16)

# ----------------------------------------------------- falls and walls --
# A waterfall off a cliff: the lip foams, streaks of lit water pour down
# the face, three frames scrolling.
def waterfall_frame(k):
    c = Canvas(16, 16, 8)
    for x in range(16):
        c.set(x, 0, 0xa)
        c.set(x, 1, 9 if (x + k) % 3 else 0xa)
    for x in (1, 4, 7, 10, 13):
        for y in range(2, 16):
            c.set(x, y, 9)
            if (y + k * 2) % 6 == 0:
                c.set(x, y, 0xa)
                c.set(x + 1, y, 0xa)
            elif (y + k * 2) % 6 == 3:
                c.set(x + 1, y, 9)
    for x in (3, 9, 15):
        for y in range(2, 16):
            if (y + k * 2 + 2) % 5 == 0:
                c.set(x, y, 7)
    return c.rows()


mt('waterfall', 'stone', 'WATER', frames=[waterfall_frame(0), waterfall_frame(1), waterfall_frame(2)], anim_speed=6)


# the pool a fall lands in: water churned white
def foam_frame(frame, k):
    c = Canvas.from_rows(frame)
    for x in range(16):
        for y in range(0, 6):
            if ((x * 5 + y * 3 + k * 4) % 7) < 2 and y < 4 - (x % 3):
                c.set(x, y, 0xa)
            elif ((x * 3 + y * 5 + k) % 9) == 0:
                c.set(x, y, 9)
    return c.rows()


mt('water_foam', 'stone', 'WATER', frames=[foam_frame(_w1, 0), foam_frame(_w2, 1)], anim_speed=10)


# The deep rooms' walls: old stone blocks, violet light climbing them
# from the ground, a crystal set in the lit ones.
def blight_wall_art(seed, lit=False, k=0):
    rnd = random.Random(seed)
    c = Canvas(16, 16, 8)
    for row in range(4):
        y0 = row * 4
        off = 0 if row % 2 == 0 else 4
        for bx in range(-1, 3):
            x0 = bx * 8 + off
            for y in range(y0 + 1, y0 + 4):
                for x in range(x0 + 1, x0 + 8):
                    if 0 <= x < 16:
                        c.set(x, y, 9)
            for x in range(x0 + 1, x0 + 7):
                if 0 <= x < 16:
                    c.set(x, y0 + 1, 0xa)
            if 0 <= x0 + 1 < 16:
                c.set(x0 + 1, y0 + 2, 0xa)
    # the glow from below
    for y in range(10, 16):
        for x in range(16):
            v = c.get(x, y)
            p = (y - 9) * 2 + rnd.randrange(3)
            if v == 9 and p > 6:
                c.set(x, y, 5 if p > 9 else 4)
            elif v == 0xa and p > 8:
                c.set(x, y, 6 if p > 11 else 5)
            elif v == 8 and p > 10:
                c.set(x, y, 4)
    if lit:
        c.blit(A('''
            ..1..
            .1b1.
            1b771
            1b6b1
            .161.
            ..1..
        '''), 6, 5)
        for x, y in ((4, 6), (12, 7), (5, 11), (11, 11), (8, 3)):
            c.set(x, y, 6 if (x + k) % 2 else 5)
    c.hline(0, 15, 0, 1)
    return c.rows()


mt('blight_wall', 'blight', 'SOLID', blight_wall_art(5))
mt('blight_wall2', 'blight', 'SOLID', blight_wall_art(9))
mt('blight_wall_lit', 'blight', 'SOLID', frames=[blight_wall_art(5, True, 0), blight_wall_art(5, True, 1)], anim_speed=16)

# ===================================================== the transitions ===
# No generic boundary is a hard line. Ground that meets water gets a
# shore: a dark soil lip, a strip of sand, reeds dipping in; ground that
# meets the canopy gets a verge: shadow and fallen leaves under a wall,
# undergrowth against its sides, ferns above a crown; a soil trail gets
# ragged grass creeping over its edge. One tile per combination of
# sides (N=1 E=2 S=4 W=8), all on one turf so their untouched quarters
# share subtiles.
TURF_EDGE = turf(50)


def edged(base, mask, painters):
    c = Canvas.from_rows(base)
    for bit, paint in painters:
        if mask & bit:
            paint(c)
    return c.rows()


def mirror_x(paint):
    """a painter for the opposite side: paint on a flipped canvas"""
    def p(c):
        f = Canvas.from_rows(hflip(c.rows()))
        paint(f)
        g = hflip(f.rows())
        for y in range(16):
            for x in range(16):
                c.set(x, y, int(g[y][x], 16))
    return p


def mirror_y(paint):
    def p(c):
        f = Canvas.from_rows(vflip(c.rows()))
        paint(f)
        g = vflip(f.rows())
        for y in range(16):
            for x in range(16):
                c.set(x, y, int(g[y][x], 16))
    return p


# --- the shore: water on that side
def shore_n(c):
    for x in range(16):
        c.set(x, 0, 9)
        c.set(x, 1, 9 if (x * 3) % 4 else 8)
        c.set(x, 2, 7)
        c.set(x, 3, 3 if (x * 5) % 3 else 7)
    for x in (2, 6, 11, 14):
        c.set(x, 0, 5); c.set(x, 1, 5); c.set(x, 2, 5)
        c.set(x + 1, 0, 6)


def shore_e(c):
    for y in range(16):
        c.set(15, y, 9)
        c.set(14, y, 9 if (y * 3) % 4 else 8)
        c.set(13, y, 7)
        c.set(12, y, 3 if (y * 5) % 3 else 7)
    for y in (1, 5, 9, 13):
        c.set(15, y, 5); c.set(14, y, 5); c.set(13, y, 5)
        c.set(15, y + 1, 6)


shore_s = mirror_y(shore_n)
shore_w = mirror_x(shore_e)
SHORE = [(1, shore_n), (2, shore_e), (4, shore_s), (8, shore_w)]
for _m in range(1, 16):
    mt('shore_%x' % _m, 'forest', 'FLOOR', edged(TURF_EDGE, _m, SHORE))


# water at a corner only: a nick of soil and sand
def nick(cx, cy, sx, sy):
    def p(c):
        c.set(cx, cy, 9); c.set(cx + sx, cy, 9); c.set(cx, cy + sy, 9); c.set(cx + sx, cy + sy, 8)
        c.set(cx + 2 * sx, cy, 7); c.set(cx, cy + 2 * sy, 7); c.set(cx + 2 * sx, cy + sy, 7); c.set(cx + sx, cy + 2 * sy, 7)
        c.set(cx + 3 * sx, cy, 3); c.set(cx, cy + 3 * sy, 3)
    return p


NICKS = [(1, nick(0, 0, 1, 1)), (2, nick(15, 0, -1, 1)), (4, nick(15, 15, -1, -1)), (8, nick(0, 15, 1, -1))]
for _m in range(1, 16):
    mt('shore_c%x' % _m, 'forest', 'FLOOR', edged(TURF_EDGE, _m, NICKS))


# --- the verge: the canopy on that side
def verge_n(c):
    """the wall's shadow and the leaves it drops"""
    for y in range(7):
        for x in range(16):
            v = c.get(x, y)
            if y < 5 or (x * 7 + y) % 3:
                if v in (4, 5, 6):
                    c.set(x, y, 3)
                elif v == 3:
                    c.set(x, y, 2)
    for x, y in ((3, 2), (9, 1), (13, 3), (6, 4)):
        c.set(x, y, 7)
        c.set(x + 1, y, 8)


def verge_e(c):
    """undergrowth against the trunks: a dark strip, leaf tips"""
    for y in range(16):
        c.set(15, y, 1)
        c.set(14, y, 2)
        c.set(13, y, 3 if (y * 5) % 4 else 2)
    for y in (2, 7, 12):
        c.set(12, y, 5); c.set(11, y + 1, 5); c.set(13, y - 1, 6)


def verge_s(c):
    """ferns above the crown below"""
    for x in range(16):
        c.set(x, 15, 2)
        c.set(x, 14, 2 if (x * 3) % 5 else 3)
    for x in (1, 4, 7, 10, 13):
        c.set(x, 13, 5); c.set(x, 12, 6 if x % 2 else 5); c.set(x + 1, 13, 5); c.set(x + 1, 11, 5)


verge_w = mirror_x(verge_e)
VERGE = [(1, verge_n), (2, verge_e), (4, verge_s), (8, verge_w)]
for _m in range(1, 16):
    mt('verge_%x' % _m, 'forest', 'FLOOR', edged(TURF_EDGE, _m, VERGE))


# --- the trail's edge: grass creeping over the soil on that side
PATH_EDGE = next(m for m in METATILES if m['name'] == 'path')['art']


def pedge_n(c):
    for x in range(16):
        d = 1 + ((x * 7) % 3)
        for y in range(d):
            c.set(x, y, 4 if (x + y) % 3 else 5)
        c.set(x, d, 3)


def pedge_e(c):
    for y in range(16):
        d = 1 + ((y * 7) % 3)
        for k in range(d):
            c.set(15 - k, y, 4 if (y + k) % 3 else 5)
        c.set(15 - d, y, 3)


pedge_s = mirror_y(pedge_n)
pedge_w = mirror_x(pedge_e)
PEDGE = [(1, pedge_n), (2, pedge_e), (4, pedge_s), (8, pedge_w)]
for _m in range(1, 16):
    mt('pedge_%x' % _m, 'forest', 'FLOOR', edged(PATH_EDGE, _m, PEDGE))

# ====================================================== mystery rooms ===
# Behind a mouth in the forest's walls: a damp cave (the cliff palette),
# the hollow of a tree, a thicket of brush (the wood palette). Each has a
# wall mass, a wall face, two floors, a solid thing, a glowing thing, its
# way out, and floors that carry a type under an overlay: a switch, a
# pot, a chest, drawn on the overlay so one drawing serves all three.
def mystery(name, pal, wall, face, floor0, floor1, prop, glow, exit_):
    mt('%s_wall' % name, pal, 'SOLID', wall)
    mt('%s_face' % name, pal, 'SOLID', face)
    mt('%s_floor0' % name, pal, 'FLOOR', floor0)
    mt('%s_floor1' % name, pal, 'FLOOR', floor1)
    mt('%s_prop' % name, pal, 'SOLID', prop)
    mt('%s_glow' % name, pal, 'FLOOR', glow)
    mt('%s_exit' % name, pal, 'MYST', exit_)
    mt('%s_floor_switch' % name, pal, 'SWITCH', floor0)
    mt('%s_floor_lift' % name, pal, 'LIFT1', floor1)
    mt('%s_floor_chest' % name, pal, 'CHEST', floor0)


# --- the cave: lumps of wet rock, a block face dripping moss, a floor of
#     stone with puddles that catch the light, stalagmites, pale fungus
def rock_mass(seed):
    rnd = random.Random(seed)
    c = Canvas(16, 16, 2)
    pts = [(rnd.randrange(16), rnd.randrange(16), 2.2 + rnd.random() * 2) for _ in range(7)]
    for cx, cy, r in sorted(pts, key=lambda q: q[1]):
        blob(c, cx, cy, r, (2, 3, 4, 5))
    for _ in range(5):
        c.wrap_set(rnd.randrange(16), rnd.randrange(16), 1)
    return c.rows()


def cave_face():
    c = Canvas(16, 16, 3)
    for row in range(3):
        y0 = row * 5
        off = 0 if row % 2 == 0 else 4
        for bx in range(-1, 3):
            x0 = bx * 8 + off
            for y in range(y0 + 1, y0 + 5):
                for x in range(x0 + 1, x0 + 8):
                    if 0 <= x < 16 and y < 15:
                        c.set(x, y, 4)
            for x in range(x0 + 1, x0 + 7):
                if 0 <= x < 16 and y0 + 1 < 15:
                    c.set(x, y0 + 1, 5)
    c.hline(0, 15, 0, 1)
    c.hline(0, 15, 15, 0xa)
    for x, y in ((3, 1), (3, 2), (3, 3), (11, 6), (11, 7), (7, 11), (7, 12), (7, 13)):
        c.set(x, y, 8)
    c.set(3, 4, 9); c.set(11, 8, 9); c.set(7, 14, 9)
    return c.rows()


def cave_floor(seed, puddle):
    c = Canvas.from_rows(turf(seed, 3, 2, 4, 6, 5))
    if puddle:
        c.ellipse(9, 10, 4, 2.2, 2)
        c.ellipse(9, 10, 3, 1.4, 1)
        c.set(8, 9, 0xc); c.set(7, 10, 5)
    for x, y in ((2, 3), (13, 6), (4, 13)):
        c.set(x, y, 7)
    return c.rows()


def cave_prop():
    c = Canvas(16, 16)
    for y in range(2, 15):
        w = 1 + (y - 2) * 5 // 13
        c.hline(8 - w, 8 + w, y, 4)
        c.set(8 - w, y, 3)
        c.set(8 + w, y, 5)
    c.set(8, 2, 6); c.set(7, 4, 6)
    c.outline(1)
    return compose(cave_floor(31, False), c.rows())


def cave_glow():
    c = Canvas.from_rows(cave_floor(32, False))
    for cx, cy, r in ((5, 9, 2.5), (10, 7, 2.0), (12, 11, 1.5)):
        c.ellipse(cx, cy, r, r * 0.6, 0xd)
        c.ellipse(cx, cy - 0.5, r * 0.5, 0.5, 0xc)
        c.vline(int(cx), int(cy), int(cy) + 2, 0xc)
    return c.rows()


def arch(base_rows, inner):
    """a doorway in a wall: the base with a dark arch cut, lit at the foot"""
    c = Canvas.from_rows(base_rows)
    for y in range(16):
        for x in range(16):
            dx, dy = (x + 0.5 - 8) / 6.0, (y + 0.5 - 9) / 8.0
            if dy > 0:
                dy = 0
            if dx * dx + dy * dy <= 1.0 and y < 16:
                c.set(x, y, inner)
    for x in range(3, 13):
        c.set(x, 15, 0xe)
    c.outline(1)
    return c.rows()


mystery('cave', 'cliff', rock_mass(3), cave_face(), cave_floor(21, False), cave_floor(22, True), cave_prop(), cave_glow(),
        arch(rock_mass(3), 1))


# --- the hollow: bark grain, the rings of the heartwood as a face, a floor
#     of chips and root, a knot, a shelf of amber fungus
def bark_mass(seed):
    rnd = random.Random(seed)
    c = Canvas(16, 16, 8)
    for x in range(16):
        tone = 7 if x % 5 == 0 else 9 if x % 5 == 2 else 8
        for y in range(16):
            c.set(x, y, tone if (y + x) % 7 else 7)
    for _ in range(2):
        cx, cy = rnd.randrange(16), rnd.randrange(16)
        for r, t in ((2.6, 7), (1.8, 9), (0.9, 7)):
            for y in range(16):
                for xx in range(16):
                    dx, dy = ((xx - cx + 8) % 16 - 8), ((y - cy + 8) % 16 - 8)
                    if dx * dx / (r * r * 1.4) + dy * dy / (r * r) <= 1:
                        c.set(xx, y, t)
    return c.rows()


def hollow_face():
    c = Canvas(16, 16, 8)
    for y in range(16):
        for x in range(16):
            d = ((x - 8) ** 2 / 2.2 + (y + 6) ** 2 / 9) ** 0.5
            c.set(x, y, (9, 0xa, 8, 7)[int(d) % 4])
    c.hline(0, 15, 0, 1)
    c.hline(0, 15, 15, 7)
    c.hline(0, 15, 14, 7)
    return c.rows()


def hollow_floor(seed, root):
    c = Canvas.from_rows(turf(seed, 8, 7, 9, 7, 5))
    if root:
        for x in range(16):
            y = 10 + int(2.5 * math.sin(x / 2.5))
            c.set(x, y, 9); c.set(x, y + 1, 7)
    for x, y in ((3, 3), (12, 5), (6, 13)):
        c.set(x, y, 0xa)
    return c.rows()


def hollow_prop():
    c = Canvas(16, 16)
    ball(c, 8, 9, 6, 5, (7, 7, 8, 9, 0xa))
    c.ellipse(7, 7, 2.5, 1.5, 7)
    c.ellipse(7, 7, 1.2, 0.7, 9)
    c.outline(1)
    return compose(hollow_floor(41, False), c.rows())


def hollow_glow():
    c = Canvas.from_rows(hollow_floor(42, False))
    for cx, cy, r in ((5, 8, 3.0), (11, 11, 2.5)):
        c.ellipse(cx, cy, r, r * 0.5, 0xb)
        c.ellipse(cx, cy - 0.5, r * 0.8, r * 0.3, 0xc)
        c.set(int(cx), int(cy) - 1, 0xd)
    return c.rows()


mystery('hollow', 'wood', bark_mass(5), hollow_face(), hollow_floor(43, False), hollow_floor(44, True), hollow_prop(), hollow_glow(),
        arch(bark_mass(5), 1))


# --- the thicket: a bramble mass barbed with magenta, a face of stems and
#     leaves, a floor of turf under leaf litter, a stump, berries that glow
def bramble_mass(seed):
    rows = leaf_mass(CANOPY_B if seed % 2 else CANOPY_A, [], tones=(2, 3, 4, 5))
    c = Canvas.from_rows(rows)
    rnd = random.Random(seed)
    for _ in range(6):
        x, y = rnd.randrange(16), rnd.randrange(16)
        c.wrap_set(x, y, 1); c.wrap_set(x + 1, y + 1, 1); c.wrap_set(x + 2, y, 0xf)
    return c.rows()


def thicket_face():
    c = Canvas(16, 16, 3)
    for x in (1, 4, 7, 10, 13):
        c.vline(x, 2, 15, 8)
        c.vline(x + 1, 3, 15, 7)
    for x, y in ((2, 4), (5, 7), (8, 3), (11, 9), (14, 5), (3, 11), (9, 12), (12, 2)):
        c.set(x, y, 5); c.set(x + 1, y, 4); c.set(x, y + 1, 4)
    for x, y in ((6, 5), (12, 11), (0, 9)):
        c.set(x, y, 0xf)
    c.hline(0, 15, 0, 2)
    c.hline(0, 15, 1, 2)
    c.hline(0, 15, 15, 1)
    return c.rows()


def thicket_floor(seed, litter):
    c = Canvas.from_rows(turf(seed, 4, 3, 5, 6, 6))
    rnd = random.Random(seed)
    for _ in range(10 if litter else 5):
        x, y = rnd.randrange(16), rnd.randrange(16)
        c.wrap_set(x, y, 8); c.wrap_set(x + 1, y, 9 if rnd.random() < 0.5 else 7)
    return c.rows()


def thicket_prop():
    c = Canvas(16, 16)
    c.rect(4, 6, 11, 13, 8)
    c.vline(4, 6, 13, 7); c.vline(11, 6, 13, 9)
    c.ellipse(7.5, 5.5, 4.5, 2.3, 9); c.ellipse(7.5, 5.5, 3, 1.5, 0xa); c.ellipse(7.5, 5.5, 1.5, 0.7, 9)
    c.outline(1)
    return compose(thicket_floor(51, False), c.rows())


def thicket_glow():
    c = Canvas.from_rows(thicket_floor(52, False))
    for x, y in ((3, 4), (6, 9), (10, 5), (12, 11), (8, 13)):
        c.set(x, y, 3); c.set(x + 1, y, 3); c.set(x, y + 1, 3)
        c.set(x + 1, y + 1, 0xf); c.set(x + 2, y, 0xd)
    return c.rows()


mystery('thicket', 'wood', bramble_mass(7), thicket_face(), thicket_floor(53, True), thicket_floor(54, False), thicket_prop(), thicket_glow(),
        arch(bramble_mass(7), 1))

# --- the mouths in the forest's walls: in the trunk face's place
_mouth_rock = Canvas.from_rows(_face)
for _y in range(16):
    for _x in range(16):
        if _mouth_rock.get(_x, _y) in (7, 8, 9):
            _mouth_rock.set(_x, _y, 4)
mt('mouth_cave', 'cliff', 'MYST', arch([r.replace('1', '1') for r in _mouth_rock.rows()], 1))
mt('mouth_hollow', 'wood', 'MYST', arch(_face, 1))
_mouth_thicket = Canvas.from_rows(_face)
for _y in range(16):
    for _x in range(16):
        if _mouth_thicket.get(_x, _y) in (7, 8, 9):
            _mouth_thicket.set(_x, _y, 3 if (_x + _y) % 3 else 4)
mt('mouth_thicket', 'wood', 'MYST', arch(_mouth_thicket.rows(), 1))

# --- things on the overlay, one drawing for every style
mt('myst_switch', 'cliff', 'FLOOR', L({}, '''
    ................
    ................
    ................
    .....111111.....
    ....16655551....
    ...1655554441...
    ...1555544431...
    ...1544444331...
    ...1444433321...
    ....14333221....
    .....111111.....
    ................
    ................
    ................
    ................
    ................
'''))
mt('myst_switch_down', 'cliff', 'FLOOR', L({}, '''
    ................
    ................
    ................
    ................
    ................
    .....111111.....
    ....14433331....
    ...1433333221...
    ...1333322221...
    ....12222211....
    .....111111.....
    ................
    ................
    ................
    ................
    ................
'''))
mt('myst_pot', 'cliff', 'FLOOR', L({}, '''
    ................
    ................
    ....11111111....
    ...1bccbbbcb1...
    ....1bbbbbb1....
    ...1bccbbbbb1...
    ..1bbbbbbbbbb1..
    .1bcbbbbbbbaab1.
    .1bbbbbbbbbaab1.
    .1bbbbbbbbbaa1..
    .1abbbbbbbaaa1..
    ..1aabbbbaaa1...
    ...1aaaaaaa1....
    ....1111111.....
    ................
    ................
'''))
_chest_rows = next(m for m in METATILES if m['name'] == 'chest')['art']
_chest_open_rows = next(m for m in METATILES if m['name'] == 'chest_open')['art']
mt('myst_chest', 'stone', 'FLOOR', [r.replace('e', '.') for r in _chest_rows])
mt('myst_chest_open', 'stone', 'FLOOR', [r.replace('e', '.') for r in _chest_open_rows])

# a spring: water that glows, the fairy's gift
_spring1 = Canvas.from_rows(_w1); _spring2 = Canvas.from_rows(_w2)
for _c, _k in ((_spring1, 0), (_spring2, 1)):
    for _y in range(16):
        for _x in range(16):
            if _x in (0, 15) or _y in (0, 15):
                _c.set(_x, _y, 1)
    for _x, _y in ((4, 4), (11, 6), (7, 10), (12, 12), (3, 12)):
        _c.set((_x + _k) % 16, _y, 0xd)
        _c.set((_x + _k + 1) % 16, _y, 0xa)
mt('myst_spring', 'stone', 'FLOOR', frames=[_spring1.rows(), _spring2.rows()], anim_speed=12)

# =============================================================== sewer ===
def flagstones(seed, slabs, moss=()):
    """slabs: (x0, y0, x1, y1, tone); mortar between; moss: (x, y) spots."""
    c = Canvas(16, 16, 2)
    for x0, y0, x1, y1, tone in slabs:
        c.rect(x0, y0, x1, y1, tone)
        c.hline(x0, x1, y0, min(6, tone + 1))
        c.vline(x0, y0, y1, min(6, tone + 1))
        c.hline(x0 + 1, x1, y1, max(2, tone - 1))
        c.vline(x1, y0 + 1, y1, max(2, tone - 1))
    rnd = random.Random(seed)
    for _ in range(3):
        x, y = rnd.randrange(16), rnd.randrange(16)
        if c.get(x, y) == 4:
            c.set(x, y, 3)
    for (x, y) in moss:
        c.set(x, y, 7); c.set(x + 1, y, 8); c.set(x, y + 1, 8)
    return c.rows()


SLABS0 = [(0, 0, 7, 6, 4), (9, 0, 15, 8, 4), (0, 8, 5, 15, 4), (7, 10, 15, 15, 4)]
mt('sw_floor0', 'sewer', 'FLOOR', flagstones(1, SLABS0, [(8, 7)]))
mt('sw_floor1', 'sewer', 'FLOOR', flagstones(2, [(0, 0, 9, 4, 4), (11, 0, 15, 6, 3), (0, 6, 6, 12, 4), (8, 6, 15, 12, 4), (0, 14, 15, 15, 3)], [(7, 13)]))
mt('sw_floor2', 'sewer', 'FLOOR', flagstones(3, [(0, 0, 5, 9, 3), (7, 0, 15, 5, 4), (7, 7, 12, 15, 4), (14, 7, 15, 15, 4), (0, 11, 5, 15, 4)], [(6, 10), (13, 6)]))
mt('sw_floor_slime', 'sewer', 'SLOW', compose(flagstones(1, SLABS0), A('''
    ................
    .....1777.......
    ...177888771....
    ..17888888871...
    .178888878887...
    .1788888888871..
    .17888888888871.
    ..178888888871..
    ...1778888771...
    .....1777771....
    .......111......
    ................
    ................
    ................
    ................
    ................
''')))

# The wall face: wet bricks, moss drips, glints of water.
_bricks = A('''
    1111111111111111
    1444442144444421
    1433332143333321
    1433632143333321
    1222221122222211
    4421444443214444
    3321433333213333
    3321433333213633
    2211222222112222
    1444442144444421
    1433332143333321
    1433332143336321
    1222221122222211
    4421444443214444
    3621433333213333
    2211222222112222
''')
mt('sw_wall', 'sewer', 'SOLID', _bricks)
mt('sw_wall_top', 'sewer', 'SOLID', A('''
    6666666666666666
    5555555555555555
    4444444444444444
    3333333333333333
    2322232222322223
    2232222322232232
    2222322223222222
    3222232222322322
    2322222322223222
    2223222222322222
    2222223222222232
    3222322223222222
    2232222322232222
    2222222232222322
    3222322222322222
    2222222222222222
'''))
mt('sw_wall_slime', 'sewer', 'SOLID', compose(_bricks, A('''
    ......7777......
    .....178887.....
    .....17888871...
    ......178871....
    ......17887.....
    ......17887.....
    .......1787.....
    .......1787.....
    .......178......
    .......178......
    .......17.......
    ........7.......
    ........7.......
    ................
    ................
    ................
''')))

# Teal water: a glow in it, ripples and foam that drift.
_sw1 = A('''
    9999999999999999
    9aaa99999999aaa9
    99bba9999999ba99
    9999999999999999
    9999999999999999
    999999aaa9999999
    9999999cba999999
    9999999999999999
    9999999999999999
    9aaa9999999aaaa9
    99ba999999999ba9
    9999999999999999
    9999999999999999
    999999aaaa999999
    99999999cb999999
    9999999999999999
''')
_sw2 = A('''
    9999999999999999
    999aaa9999999aaa
    9999bba9999999ba
    9999999999999999
    9999999999999999
    99999999aaa99999
    999999999cba9999
    9999999999999999
    9999999999999999
    999aaa99999999aa
    9999ba9999999999
    9999999999999999
    9999999999999999
    99999999aaaa9999
    9999999999cb9999
    9999999999999999
''')
mt('sw_water', 'sewer', 'WATER', frames=[_sw1, _sw2], anim_speed=20)
_swlily = A('''
    ................
    ................
    ....11111.......
    ...1888888 1....
    ..18888888 81...
    ..188178888 1...
    ..18817888881...
    ..188888188 1...
    ...18888881.....
    ....111111......
    ................
    ................
    ................
    ................
    ................
    ................
''')
_swlily = [r.replace(' ', '8') for r in _swlily]
mt('sw_lilypad', 'sewer', 'WATER', frames=[compose(_sw1, _swlily), compose(_sw2, _swlily)], anim_speed=20)

# A waterfall pouring down the wall into the channel.
_wf1 = A('''
    9ab9ba9b9ab9ba9b
    9ab9ba9b9ab9ba9b
    9ab9ba9b9ab9ba9b
    9ab9ba9b9ab9ba9b
    9ab9ba9b9ab9ba9b
    9ab9ba9b9ab9ba9b
    9ab9ba9b9ab9ba9b
    9ab9ba9b9ab9ba9b
    9ab9ba9b9ab9ba9b
    9ab9ba9b9ab9ba9b
    9ab9ba9b9ab9ba9b
    9ab9ba9b9ab9ba9b
    9ac9ba9b9ab9ca9b
    9bcbbcbbbbcbbcbb
    bccbbcbcbccbbccb
    cbbccbbcbcbbcbcc
''')
_wf2 = A('''
    b9ab9ba9b9ab9ba9
    b9ab9ba9b9ab9ba9
    b9ab9ba9b9ab9ba9
    b9ab9ba9b9ab9ba9
    b9ab9ba9b9ab9ba9
    b9ab9ba9b9ab9ba9
    b9ab9ba9b9ab9ba9
    b9ab9ba9b9ab9ba9
    b9ab9ba9b9ab9ba9
    b9ab9ba9b9ab9ba9
    b9ab9ba9b9ab9ba9
    b9ab9ba9b9ab9ba9
    b9ac9ba9b9ab9ca9
    bbcbbcbbbcbbbcbb
    cbbcbccbbccbcbbc
    bccbcbbcbcbccbcb
''')
mt('sw_waterfall', 'sewer', 'SOLID', frames=[_wf1, _wf2], anim_speed=4)

# The channel's banks.
mt('sw_water_edge_n', 'sewer', 'FLOOR', compose(flagstones(4, [(0, 0, 6, 7, 4), (8, 0, 15, 7, 4)]), A('''
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    6666666666666666
    5555555555555555
    4444444444444444
    3333333333333333
    2222222222222222
    1111111111111111
    9999999999999999
    9999999999999999
''')))
mt('sw_water_edge_s', 'sewer', 'FLOOR', compose(flagstones(6, [(0, 12, 6, 15, 4), (8, 12, 15, 15, 4)]), A('''
    9999999999999999
    9aaa99999999aaa9
    99ba9999999999a9
    9999999999999999
    9999999999999999
    9999999aaa999999
    99999999ba999999
    9999999999999999
    1111111111111111
    3333333333333333
    5555555555555555
    4444444444444444
    ................
    ................
    ................
    ................
''')))

# An iron grate over the channel: bars both ways, black water beneath.
mt('sw_grate', 'sewer', 'FLOOR', A('''
    5444444444444445
    4511511511511514
    4199199199199114
    4199199199199114
    4511511511511514
    4199199199199114
    4199199199199114
    4511511511511514
    4199199199199114
    4199199199199114
    4511511511511514
    4199199199199114
    4199199199199114
    4511511511511514
    4111111111111114
    3333333333333333
'''))


# The great drain: a round grate two tiles across.
def drain():
    c = Canvas(32, 32, 4)
    base = flagstones(7, [(0, 0, 15, 15, 4)])
    for ty in range(2):
        for tx in range(2):
            c.blit(base, tx * 16, ty * 16)
    # the stone ring
    for y in range(32):
        for x in range(32):
            dx, dy = x + 0.5 - 16, y + 0.5 - 16
            d = (dx * dx + dy * dy) ** 0.5
            if d <= 14.5:
                c.set(x, y, 9)   # water below
            if 11.5 < d <= 14.5:
                c.set(x, y, 5 if dx + dy < 0 else 3)
            if 13.5 < d <= 14.5 or 11.5 < d <= 12.5:
                c.set(x, y, 1)
    # the bars
    for i in range(-10, 11, 4):
        for t in range(-12, 13):
            if (i * i + t * t) ** 0.5 <= 11.5:
                c.set(16 + i, 16 + t, 2)
                c.set(16 + t, 16 + i, 2)
    for y in range(4, 28):
        for x in range(4, 28):
            dx, dy = x + 0.5 - 16, y + 0.5 - 16
            if (dx * dx + dy * dy) ** 0.5 <= 11.5 and c.get(x, y) == 9 and (x + y) % 5 == 0:
                c.set(x, y, 0xa)
    return c.rows()


_drain = drain()
mt('sw_drain_nw', 'sewer', 'FLOOR', slice16(_drain, 0, 0))
mt('sw_drain_ne', 'sewer', 'FLOOR', slice16(_drain, 1, 0))
mt('sw_drain_sw', 'sewer', 'FLOOR', slice16(_drain, 0, 1))
mt('sw_drain_se', 'sewer', 'FLOOR', slice16(_drain, 1, 1))

# Pipes: a rusted mouth in the wall, and a copper run along it.
mt('sw_pipe', 'sewer', 'SOLID', compose(_bricks, A('''
    ................
    ................
    ..111111111111..
    .1dddddddddddd1.
    .1d5ddddddddd51.
    .1dd11111111dd1.
    .1d19999999a1d1.
    .1d19999999a1d1.
    .1d1aaaaaaaa1d1.
    .1dd11111111dd1.
    .1dddddddddddd1.
    ..111111111111..
    ......1b1.......
    ......1b1.......
    .......b........
    ................
''')))
mt('sw_pipe_h', 'sewer', 'SOLID', compose(_bricks, A('''
    ................
    ................
    ................
    ................
    1111111111111111
    5555555555555555
    dddddddddd1ddddd
    dddddddd1d5d1ddd
    dddddddd1555 1dd
    dddddddd1d5d1ddd
    dddddddddd1ddddd
    1111111111111111
    ................
    ................
    ................
    ................
''')))
METATILES[-1]['art'] = [r.replace(' ', '5') for r in METATILES[-1]['art']]

mt('sw_ladder', 'sewer', 'EXIT', compose(_bricks, A('''
    ................
    ...1dd1..1dd1...
    ...1dd1dd1dd1...
    ...1dd1111dd1...
    ...1dd1..1dd1...
    ...1dd1dd1dd1...
    ...1dd1111dd1...
    ...1dd1..1dd1...
    ...1dd1dd1dd1...
    ...1dd1111dd1...
    ...1dd1..1dd1...
    ...1dd1dd1dd1...
    ...1dd1111dd1...
    ...1dd1..1dd1...
    ...1dd1..1dd1...
    ...1111..1111...
''')))
# a ladder down into the water, from the floor
mt('sw_ladder_down', 'sewer', 'FLOOR', compose(_sw1, A('''
    5444444444444445
    4111111111111114
    41dd1......1dd14
    41dd1dddddd1dd14
    41dd1111111ddd14
    41dd1......1dd14
    41dd1dddddd1dd14
    41dd1111111ddd14
    41dd1......1dd14
    41dd1dddddd1dd14
    41dd1111111ddd14
    .1dd1......1dd1.
    .1dd1dddddd1dd1.
    .1dd1111111ddd1.
    .1dd1......1dd1.
    .1111......1111.
''')))
mt('sw_hole', 'sewer', 'EXIT', compose(_bricks, A('''
    ................
    ....11111111....
    ..115666655511..
    .1566111111551.
    .156111111115541
    .15111999911 541
    .1511999999915 1
    .15119999999154
    .1511999999915 1
    .15119999999154
    .15111999991 441
    .145111111114431
    .14441111144431.
    ..11444444431...
    ....11111111....
    ................
''')))
METATILES[-1]['art'] = [r.replace(' ', '1') for r in METATILES[-1]['art']]

# A wall sconce burning.
_sconce = compose(_bricks, A('''
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ......1dd1......
    .....1dddd1.....
    ......1dd1......
    ......1dd1......
    ......1dd1......
    .....1dddd1.....
    ....1dddddd1....
    .....111111.....
    ................
'''))
_sf1 = A('''
    ................
    .......e........
    ......efe.......
    .....effe.......
    .....effee......
    ......efe.......
    ......1e1.......
''')
_sf2 = A('''
    ................
    ................
    ......ee........
    .....effe.......
    ....eeffe.......
    .....efe........
    ......1e1.......
''')
mt('sw_torch_lit', 'sewer', 'TORCH_LIT', frames=[compose(_sconce, _sf1), compose(_sconce, _sf2)], coll=3, anim_speed=6)

# A cluster of candles on the floor, three flames.
_cand = compose(flagstones(1, SLABS0), A('''
    ................
    ................
    ................
    ................
    ................
    ......1.........
    ....1161..1.....
    ...16661.161....
    ...16651166 1...
    ..1166511665 1..
    ..16661166651...
    ..1665116651....
    ..1665 16651....
    ..11111111111...
    ..1222222222 1..
    ...111111111....
'''))
_cand = [r.replace(' ', '6') for r in _cand]
_cf1 = A('''
    ................
    ................
    ......e.........
    .....efe...e....
    ....1efe1.efe...
    ....1ee1.1efe1..
''')
_cf2 = A('''
    ................
    ......e.........
    .....efe...e....
    .....efe..efe...
    ....1ee1.1efe1..
    .....11..1ee1...
''')
mt('sw_candles', 'sewer', 'SOLID', frames=[compose(_cand, _cf1), compose(_cand, _cf2)], anim_speed=7)

# A hanging lantern on the wall, chained.
_lan = compose(_bricks, A('''
    .......1........
    .......1........
    .......1........
    ......111.......
    .....1ddd1......
    ....1deeed1.....
    ....1deffd1.....
    ....1deffd1.....
    ....1deeed1.....
    ....1ddddd1.....
    .....1ddd1......
    ......111.......
    ................
    ................
    ................
    ................
'''))
_lg1 = A('''
    ................
    ................
    ................
    ................
    ...e.......e....
    ................
    ..e.........e...
    ................
    ...e.......e....
''')
_lg2 = A('''
    ................
    ................
    ................
    ...e.......e....
    ................
    ..e.........e...
    ................
    ..e.........e...
    ................
''')
mt('sw_lantern', 'sewer', 'SOLID', frames=[compose(_lan, _lg1), compose(_lan, _lg2)], anim_speed=10)

# Banners on the wall: teal and rust, a gold sigil on each.
mt('sw_banner_teal', 'sewer', 'SOLID', compose(_bricks, A('''
    ................
    ..111111111111..
    ..1aaaaaaaaaa1..
    ..1a9aaaaaa9a1..
    ..1aa9aaaa9aa1..
    ..1aaa9ee9aaa1..
    ..1aaaefffaaa1..
    ..1aa9effeaaa1..
    ..1aaa9ee9aaa1..
    ..1aa9aaaa9aa1..
    ..1a9aaaaaa9a1..
    ..1aaaaaaaaaa1..
    ..19aaaaaaaa91..
    ..19a9aaaa9a91..
    ...11911911 1...
    ................
''')))
METATILES[-1]['art'] = [r.replace(' ', '1') for r in METATILES[-1]['art']]
mt('sw_banner_red', 'sewer', 'SOLID', compose(_bricks, A('''
    ................
    ..111111111111..
    ..1dddddddddd1..
    ..1d1dddddd1d1..
    ..1dd1dddd1dd1..
    ..1ddd1ee1ddd1..
    ..1dddefffddd1..
    ..1ddd1effddd1..
    ..1ddd1ee1ddd1..
    ..1dd1dddd1dd1..
    ..1d1dddddd1d1..
    ..1dddddddddd1..
    ..11dddddddd11..
    ..11d1dddd1d11..
    ...11111111 1...
    ................
''')))
METATILES[-1]['art'] = [r.replace(' ', '1') for r in METATILES[-1]['art']]

mt('sw_arch', 'sewer', 'SOLID', A('''
    1111111111111111
    1444442144444421
    1433332143333321
    1433332143333321
    1222221122222211
    4421444443214444
    3321433333213333
    3321433333213333
    2211222222112222
    1444442144444421
    1433111111114321
    1431999999991321
    1119999999999111
    4499999999999944
    3399999999999933
    2299999999999922
'''), coll=12)

mt('sw_rubble', 'sewer', 'SOLID', compose(flagstones(5, SLABS0), A('''
    ................
    ......11111.....
    .....1566651....
    ....15644441....
    ...1156444431...
    ..15661133311...
    .156644115666511
    .154444415444431
    .144444415444431
    .133333315433331
    .111111115333321
    ..15555561111111
    ..1444444415661.
    ..1333333314431.
    ..1111111111111.
    ................
''')))

# ------------------------------------------------------------- props --
# Props stand on flagstones drawn in the props palette: body 5, lit
# edges F, mortar 1.
def prop_floor(seed, slabs):
    c = Canvas(16, 16, 1)
    for x0, y0, x1, y1 in slabs:
        c.rect(x0, y0, x1, y1, 5)
        c.hline(x0, x1, y0, 0xf)
        c.vline(x0, y0, y1, 0xf)
    return c.rows()


PFLOOR = prop_floor(1, [(0, 0, 7, 6), (9, 0, 15, 8), (0, 8, 5, 15), (7, 10, 15, 15)])


def on_floor(rows):
    return compose(PFLOOR, [r.replace('g', '.') for r in rows])


# The merchant's counter: planks on a stone base, gold coins on it.
mt('sw_counter', 'props', 'SOLID', on_floor(A('''
    gggggggggggggggg
    gggggggggggggggg
    1111111111111111
    1444444444444441
    143333c33333c341
    1433333333333341
    1222222222222221
    1444444444444441
    1431111111111341
    1431555555551341
    1431566666651341
    1431533333351341
    1431555555551341
    1431111111111341
    1222222222222221
    1111111111111111
''')))

# The peddler's stall: a red striped awning, gold fringe, two halves.
_awn = A('''
    gggggggggggggggg
    ggggggg111111111
    gggggg1bbaabbaab
    ggggg1bbaabbaabb
    gggg1bbaabbaabba
    ggg1bbaabbaabbaa
    gg1bbaabbaabbaab
    g1bbaabbaabbaabb
    g1cccccccccccccc
    g1c1c1c1c1c1c1c1
    g1cgcgcgcgcgcgcg
    g1gggggggggggggg
    g1gggggggggggggg
    g1gggggggggggggg
    g1gggggggggggggg
    g1gggggggggggggg
''')
mt('sw_awning_l', 'props', 'SOLID', on_floor(_awn))
mt('sw_awning_r', 'props', 'SOLID', on_floor(hflip(_awn)))

# The gatekeeper's rug: a violet circle with gold runes, two tiles across.
def rug():
    c = Canvas(32, 32, 5)
    for ty in range(2):
        for tx in range(2):
            c.blit(PFLOOR, tx * 16, ty * 16)
    for y in range(32):
        for x in range(32):
            dx, dy = x + 0.5 - 16, y + 0.5 - 16
            d = (dx * dx + dy * dy) ** 0.5
            if d <= 15:
                c.set(x, y, 0xe if d > 12.5 else 0xd)
            if 14 < d <= 15 or 11.5 < d <= 12.5:
                c.set(x, y, 1)
            if 13 < d <= 13.8 and (x + y) % 2 == 0:
                c.set(x, y, 0xc)
    runes = [(16, 8), (16, 24), (8, 16), (24, 16), (11, 11), (21, 11), (11, 21), (21, 21)]
    for (rx, ry) in runes:
        c.set(rx, ry, 0xc); c.set(rx - 1, ry, 0xc); c.set(rx + 1, ry, 0xc); c.set(rx, ry - 1, 0xc); c.set(rx, ry + 1, 0xc)
    c.set(16, 16, 0xf); c.set(15, 16, 0xc); c.set(17, 16, 0xc); c.set(16, 15, 0xc); c.set(16, 17, 0xc)
    return c.rows()


_rug = rug()
mt('sw_rug_nw', 'props', 'FLOOR', slice16(_rug, 0, 0))
mt('sw_rug_ne', 'props', 'FLOOR', slice16(_rug, 1, 0))
mt('sw_rug_sw', 'props', 'FLOOR', slice16(_rug, 0, 1))
mt('sw_rug_se', 'props', 'FLOOR', slice16(_rug, 1, 1))

mt('sw_barrel', 'props', 'SOLID', on_floor(L({'g': 'g'}, '''
    gggggggggggggggg
    ggggg111111ggggg
    ggg1143333411ggg
    gg11555555521gg
    gg14433333421gg
    gg14444433421gg
    gg14444433421gg
    gg15555555521gg
    gg14444433421gg
    gg14444433421gg
    gg14433333421gg
    gg15555555521gg
    gg14433333421gg
    ggg1143333411ggg
    ggggg111111ggggg
    gggggggggggggggg
''')))
mt('sw_crate', 'props', 'SOLID', on_floor(L({'g': 'g'}, '''
    gggggggggggggggg
    gg111111111111gg
    gg144444444441gg
    gg143333333331gg
    gg143122222331gg
    gg143122222331gg
    gg141333333131gg
    gg141222222231gg
    gg143122222331gg
    gg143122222331gg
    gg141333333131gg
    gg141222222231gg
    gg143333333331gg
    gg122222222221gg
    gg111111111111gg
    gggggggggggggggg
''')))
mt('sw_skull', 'props', 'FLOOR', on_floor(L({'g': 'g'}, '''
    gggggggggggggggg
    gggggggggggggggg
    gggg1111111ggggg
    ggg166666661gggg
    gg16666666661ggg
    gg16617661761ggg
    gg16611661161ggg
    gg176666666661gg
    gg17661666617ggg
    ggg1771111771ggg
    gggg1766771gggg6
    ggggg11111ggg166
    gggggggggggg1667
    gggg11gggggg1771
    ggg1661gggg1771g
    gggg11gggggg11gg
''')))
# A clay pot, lifted or smashed.
mt('sw_pot', 'props', 'LIFT1', on_floor(L({'g': 'g'}, '''
    gggggggggggggggg
    gggggggggggggggg
    gggggg1111gggggg
    ggggg144441ggggg
    ggggg122221ggggg
    gggg14444441gggg
    ggg1443333441ggg
    gg14433333334 1g
    gg14433333332 1g
    gg14333333332 1g
    gg13333333322 1g
    gg13332222222 1g
    ggg122222222 1gg
    gggg11111111 ggg
    gggggggggggggggg
    gggggggggggggggg
''')))
METATILES[-1]['art'] = [r.replace(' ', '1') for r in METATILES[-1]['art']]
mt('sw_gold', 'props', 'FLOOR', on_floor(L({'g': 'g'}, '''
    gggggggggggggggg
    gggggggggggggggg
    gggggggggggggggg
    gggggggggggggggg
    gggggggggggggggg
    ggggggg11ggggggg
    gggggg1fc1gg11gg
    ggg11g1cc1g1fc1g
    gg1fc11111g1cc1g
    gg1cc1fc1gg1111g
    gg11111cc1ggg11g
    gg1fcc1111gg1fc1
    gg1cccc1fcc11cc1
    gg11111ccccc1111
    ggggg111111111gg
    gggggggggggggggg
''')))


# ----------------------------------------------------- grime and glint --
# More of the drain: stained and cracked slabs, puddles, moss in the
# mortar, bones, fungus that glows, drips off the vault, chains and rust
# and webs on the bricks, a barred window, a skull in a niche, scum and
# bubbles on the channel; and glints, an overlay of winking stars that
# can lie over anything wet.
def stain(rows, seed, n=3, r=3.4, tone=2, edge=3):
    """dark blots soaked into the slabs, a spatter of dots around"""
    c = Canvas.from_rows(rows)
    rnd = random.Random(seed)
    for _ in range(n):
        cx, cy = rnd.uniform(3, 13), rnd.uniform(3, 13)
        rx, ry = rnd.uniform(r * 0.6, r), rnd.uniform(r * 0.5, r * 0.9)
        for y in range(16):
            for x in range(16):
                dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                e = dx * dx + dy * dy
                if e <= 1.0 and c.get(x, y) in (3, 4, 5, 6):
                    c.set(x, y, tone if e < 0.55 else edge)
    for _ in range(5):
        x, y = rnd.randrange(16), rnd.randrange(16)
        if c.get(x, y) in (4, 5):
            c.set(x, y, edge)
    return c.rows()


def crack(rows, pts):
    """a dark crack along the points, chipped on its right side"""
    c = Canvas.from_rows(rows)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            x, y = x0 + (x1 - x0) * i // n, y0 + (y1 - y0) * i // n
            c.set(x, y, 1)
            if c.get(x + 1, y) in (4, 5, 6):
                c.set(x + 1, y, 2)
    return c.rows()


def mossy(rows, seed, n=4):
    """moss grown along the mortar, lit tips"""
    c = Canvas.from_rows(rows)
    rnd = random.Random(seed)
    for _ in range(n):
        cx, cy = rnd.randrange(16), rnd.randrange(16)
        for y in range(cy - 3, cy + 4):
            for x in range(cx - 3, cx + 4):
                if c.get(x, y) == 2 and (x - cx) ** 2 + (y - cy) ** 2 <= 10:
                    c.set(x, y, 7)
    for y in range(16):
        for x in range(16):
            if c.get(x, y) == 7 and c.get(x, y - 1) != 7 and (x * 7 + y * 3) % 4 == 0:
                c.set(x, y, 8)
    return c.rows()


SLABS1 = [(0, 0, 9, 4, 4), (11, 0, 15, 6, 3), (0, 6, 6, 12, 4), (8, 6, 15, 12, 4), (0, 14, 15, 15, 3)]
mt('sw_floor_grime', 'sewer', 'FLOOR', stain(flagstones(7, SLABS0), 11))
mt('sw_floor_grime2', 'sewer', 'FLOOR', stain(flagstones(8, SLABS1), 12, n=2, r=4.2))
mt('sw_floor_crack', 'sewer', 'FLOOR', crack(stain(flagstones(9, SLABS0), 13, n=1), [(2, 0), (5, 4), (4, 8), (8, 11), (9, 15)]))
mt('sw_floor_crack2', 'sewer', 'FLOOR', crack(flagstones(10, SLABS1), [(15, 2), (10, 5), (11, 9), (6, 12), (5, 15)]))
mt('sw_floor_moss', 'sewer', 'FLOOR', mossy(flagstones(11, SLABS0), 21))
mt('sw_floor_moss2', 'sewer', 'FLOOR', mossy(stain(flagstones(12, SLABS1), 22, n=1), 23, n=5))


# A puddle in a worn slab: teal, a lit band, glints that drift.
def puddle(glints):
    c = Canvas.from_rows(stain(flagstones(13, SLABS0), 14, n=1))
    for y in range(16):
        for x in range(16):
            dx, dy = (x + 0.5 - 8) / 6.2, (y + 0.5 - 9) / 4.2
            e = dx * dx + dy * dy
            if e <= 1.0:
                c.set(x, y, 0xa if (e > 0.45 and dx + dy < -0.2) else 9)
            elif e <= 1.4:
                c.set(x, y, 3)
    for (x, y) in glints:
        c.set(x, y, 0xc); c.set(x - 1, y, 0xb); c.set(x + 1, y, 0xb)
    return c.rows()


mt('sw_floor_puddle', 'sewer', 'FLOOR', frames=[puddle([(6, 8), (11, 11)]), puddle([(7, 9), (10, 10)])], anim_speed=24)

# Bones on the slabs: a rib, a long bone, a jaw.
mt('sw_floor_bones', 'sewer', 'FLOOR', compose(stain(flagstones(14, SLABS0), 15, n=1), A('''
    ................
    ................
    ..11............
    .1661.......11..
    ..1611.....1651.
    ...1661....151..
    ....1661...11...
    .....1651.......
    ......1661.111..
    .......161661...
    ........1511....
    .........1......
    ...111......11..
    ..16651....1651.
    ...111......11..
    ................
''')))

# Fungus on the floor, teal and glowing: the glow breathes.
_shroom = A('''
    ................
    ................
    ................
    .......11.......
    ......1bb1......
    .....1bcbb1.....
    .....1bbbb1.....
    ..11..1551..11..
    .1bb1.1551.1bb1.
    .1bcb1155.1bcb1.
    ..1551.11..1551.
    ..1551.....1551.
    ...11.......11..
    ................
    ................
    ................
''')
_shroom = [r.replace('.', '.') for r in _shroom]
_sg1 = A('''
    ................
    ................
    ................
    ................
    ....a......a....
    ................
    ................
    ................
    ................
    ...........a....
    ................
    ....a...........
    ................
    .....a....a.....
    ................
    ................
''')
_sg2 = A('''
    ................
    ................
    ................
    ....a...........
    ...........a....
    ..a.............
    ............a...
    ................
    ................
    ................
    ....a......a....
    ................
    ................
    ......a..a......
    ...a........a...
    ................
''')
_shroom2 = [r.replace('c', 'b') for r in _shroom]
_shroom2 = compose(_shroom2, A('''
    ................
    ................
    ................
    ................
    ........c.......
    ................
    ................
    ................
    ................
    ..c.........c...
'''))
mt('sw_floor_shroom', 'sewer', 'FLOOR', frames=[compose(compose(flagstones(15, SLABS1), _sg1), _shroom),
                                                compose(compose(flagstones(15, SLABS1), _sg2), _shroom2)], anim_speed=16)

# A drip from the vault lands in a wet patch: a drop, a ring, a wider ring.
_wet = stain(flagstones(16, SLABS0), 17, n=1, r=4.5, tone=3, edge=3)
_ring1 = A('''
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ........c.......
    .......bcb......
    ........b.......
''')
_ring2 = A('''
    ................
    ................
    ................
    ................
    ................
    ................
    .......aaa......
    .....aa...aa....
    .....a..c..a....
    .....aa...aa....
    .......aaa......
''')
_ring3 = A('''
    ................
    ................
    ................
    ................
    .....aaaaaa.....
    ...aa......aa...
    ..a..........a..
    ..a....bb....a..
    ..a....bb....a..
    ..a..........a..
    ...aa......aa...
    .....aaaaaa.....
''')
mt('sw_floor_drip', 'sewer', 'FLOOR', frames=[compose(_wet, _ring1), compose(_wet, _ring2), compose(_wet, _ring3), _wet], anim_speed=9)

# --- the bricks: cracked, mossed, chained, dripping, webbed, rusted
mt('sw_wall_crack', 'sewer', 'SOLID', compose(_bricks, A('''
    .......1........
    .......1........
    ........1.......
    ........1.......
    .......12.......
    2222...12.......
    2222....1.......
    2222....12......
    .........1......
    .........1......
    ........12......
    ........1.......
    .......12.......
    .......1........
    .......1........
    ........1.......
''')))
mt('sw_wall_moss', 'sewer', 'SOLID', compose(_bricks, A('''
    7777777777777777
    7887778877787887
    7777877778777777
    1777177771777177
    .177.177.177.17.
    .17..17...17..7.
    ..7...7....7....
    ..7........7....
    ...7............
    ................
    ................
    ................
    ................
    ................
    ................
    ................
''')))
mt('sw_wall_chain', 'sewer', 'SOLID', compose(_bricks, A('''
    ......1111......
    .....156651.....
    .....15..51.....
    .....15..41.....
    .....144441.....
    ......1111......
    ......1541......
    .....15..41.....
    .....15..41.....
    ......1541......
    ......1541......
    .....15..41.....
    .....15..41.....
    ......1441......
    ......1dd1......
    .......dd.......
''')))
_streak = compose(_bricks, A('''
    ........3.......
    ........2.......
    ........2.......
    ........2.......
    ........2.......
    ........2.......
    ........2.......
    ........2.......
    ........2.......
    ........2.......
    ........2.......
    ........2.......
    ........2.......
    ........2.......
    ........2.......
    ........2.......
'''))


def drop(y):
    rs = ['................'] * 16
    rs[y] = '........b.......'
    rs[y + 1] = '.......cbb......'
    rs[y + 2] = '........b.......'
    return rs


mt('sw_wall_drip', 'sewer', 'SOLID', frames=[compose(_streak, drop(1)), compose(_streak, drop(6)), compose(_streak, drop(11)),
                                             compose(_streak, A('''
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ......c.c.......
    .......c........
'''))], anim_speed=7)


def web():
    """a cobweb in the top-left corner: spokes and three arcs, dusty"""
    c = Canvas(16, 16)
    for r in (3.5, 6.5, 9.5):
        for y in range(16):
            for x in range(16):
                d = ((x + 0.5) ** 2 + (y + 0.5) ** 2) ** 0.5
                if abs(d - r) < 0.5 and (x + y) % 2 == 0:
                    c.set(x, y, 5)
    for k in range(5):
        ang = k * math.pi / 8
        for i in range(11):
            c.set(int(math.cos(ang) * i), int(math.sin(ang) * i), 6 if i % 3 else 5)
    c.set(5, 4, 1); c.set(6, 4, 1); c.set(5, 5, 1); c.set(6, 5, 1)
    return c.rows()


mt('sw_wall_web', 'sewer', 'SOLID', compose(_bricks, web()))
mt('sw_wall_web_r', 'sewer', 'SOLID', compose(_bricks, hflip(web())))
_fung = A('''
    ................
    ................
    ....1111........
    ...1bbbb1.......
    ..1bccbbb1......
    ..1aaaaaa1......
    ...111111.......
    .........111....
    ........1bbb1...
    .......1bccbb1..
    .......1aaaaa1..
    ........11111...
    ..111...........
    .1bbb1..........
    .1aaa1..........
    ..111...........
''')
_fung2 = compose([r.replace('c', 'b') for r in _fung], A('''
    ................
    ................
    ................
    ....c...........
    ................
    ................
    ................
    ................
    ..........c.....
    ................
    ................
    ................
    ................
    ..c.............
'''))
_fglow1 = A('''
    ................
    ..........a.....
    ..a.............
    ................
    ................
    ................
    ......a.........
    ................
    ................
    ...............a
    ................
    ................
    ......a.........
    ................
    ................
    ....a...........
''')
_fglow2 = A('''
    ................
    ................
    ...........a....
    .a..............
    ................
    ..........a.....
    ................
    ................
    ......a.........
    ................
    ..............a.
    ................
    ................
    ......a.........
    ................
    ................
''')
mt('sw_wall_fungus', 'sewer', 'SOLID', frames=[compose(compose(_bricks, _fglow1), _fung), compose(compose(_bricks, _fglow2), _fung2)], anim_speed=14)
mt('sw_wall_tally', 'sewer', 'SOLID', compose(_bricks, A('''
    ................
    ................
    ..2.2.2.2.......
    ..1.1.1.1.......
    ..1.1.1.1.2.....
    ..1.1.1211.......
    ..1.12.1.1......
    ..121.1.1.......
    ................
    ..........2.2.2.
    ..........1.1.1.
    ..........1.1.1.
    ..........1.1.1.
    ....33333.......
    ...3322233......
    ..332222233.....
''')))
_win = A('''
    ................
    ................
    ...1111111111...
    ..1a9a9a9a9a91..
    ..199999999991..
    ..1a1999a1999a1.
    ..191999919991..
    ..1a1999a1999a1.
    ..191999919991..
    ..1a1999a1999a1.
    ..199999999991..
    ..1555555555551.
    ...4444444444...
    ................
    ................
    ................
''')
_win1 = [r.replace('a', '9') for r in _win]
_win1 = compose(_win1, A('''
    ................
    ................
    ................
    ................
    ....a....a......
    ................
    ........a.......
    ................
    .....a......a...
'''))
_win2 = compose([r.replace('a', '9') for r in _win], A('''
    ................
    ................
    ................
    ................
    ......a.........
    ...........a....
    ................
    ....a...........
    ................
    .........a......
'''))
mt('sw_wall_window', 'sewer', 'SOLID', frames=[compose(_bricks, _win1), compose(_bricks, _win2)], anim_speed=22)
mt('sw_wall_skull', 'sewer', 'SOLID', compose(_bricks, A('''
    ................
    ................
    ...1111111111...
    ..122222222221..
    ..121166666121..
    ..126666666621..
    ..126616661621..
    ..126611661621..
    ..122666666221..
    ..122566665221..
    ..122156651221..
    ..122215512221..
    ..155555555551..
    ..1fef555fee51..
    ...1ee1111ee1...
    ....11....11....
''')))
mt('sw_wall_rust', 'sewer', 'SOLID', compose(_bricks, A('''
    ................
    ..111111111111..
    ..1dddddddddd1..
    ..11dddddddd11..
    ..1ddddd3ddd21..
    ..1dddd33dd221..
    ..1ddd3ddd2221..
    ..1dddddd22221..
    ..11ddd2222211..
    ..111111111111..
    ...d..d...d.d...
    ...d..d...d.d...
    ......d...d.....
    ......d.........
    ................
    ................
''')))
_top = METATILES[[m['name'] for m in METATILES].index('sw_wall_top')]['art']
mt('sw_wall_top_moss', 'sewer', 'SOLID', compose(_top, A('''
    ................
    ....87..........
    ...7777.....87..
    ...........777..
    ................
    ..........7.....
    .87......777....
    .777............
    ................
    ......87........
    .....777........
    ................
    ...........7....
    ..87......777...
    .7777...........
    ................
''')))

# --- the channel: scum, bubbles, glints; mossed banks
_scum = A('''
    ................
    ................
    ....7777........
    ...778877777....
    ..77777777777...
    ...777a7777.....
    ..........7.....
    ................
    ................
    ..........7777..
    .........778877.
    ........7777777.
    .........7777...
    ................
    ..7.............
    ................
''')
mt('sw_water_scum', 'sewer', 'WATER', frames=[compose(_sw1, _scum), compose(_sw2, _scum)], anim_speed=20)


def bubble(y, pop=False):
    rs = ['................'] * 16
    if pop:
        rs[y] = '......c...c.....'
        rs[y + 1] = '.......c.c......'
        rs[y + 2] = '......c...c.....'
    else:
        rs[y] = '.......bb.......'
        rs[y + 1] = '......b..b......'
        rs[y + 2] = '......bc.b......'
        rs[y + 3] = '.......bb.......'
    return rs


mt('sw_water_bubble', 'sewer', 'WATER', frames=[compose(_sw1, bubble(11)), compose(_sw1, bubble(7)), compose(_sw2, bubble(3)), compose(_sw2, bubble(2, True))], anim_speed=8)


def star(rs, x, y, big=True):
    c = Canvas.from_rows(rs)
    c.set(x, y, 0xf if big else 0xc)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        c.set(x + dx, y + dy, 0xc)
    if big:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            c.set(x + dx, y + dy, 0xc)
    return c.rows()


mt('sw_water_glint', 'sewer', 'WATER', frames=[star(star(_sw1, 4, 5), 12, 11, False), star(star(_sw2, 4, 5, False), 12, 11)], anim_speed=16)
_edge_n = METATILES[[m['name'] for m in METATILES].index('sw_water_edge_n')]['art']
_edge_s = METATILES[[m['name'] for m in METATILES].index('sw_water_edge_s')]['art']
mt('sw_water_edge_n_moss', 'sewer', 'FLOOR', compose(_edge_n, A('''
    ................
    ................
    ................
    ................
    ................
    ....87..........
    ...777.....87...
    ..77777...7777..
    .7777777.777777.
    ..7.77.7..7.77..
    ..7..7....7..7..
    .....7.......7..
    ................
    ................
    ................
    ................
''')))
mt('sw_water_edge_s_moss', 'sewer', 'FLOOR', compose(_edge_s, A('''
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ....77....87....
    ...7877..7777...
    ...77777.7777...
    ..777.7...7.7...
    ..7...7.....7...
    ......7.........
''')))

# --- glints: an overlay of winking stars, transparent round them
_blank16 = ['................'] * 16
_gl = [star(star(_blank16, 4, 4), 11, 10, False),
       star(star(_blank16, 4, 4, False), 11, 10),
       star(_blank16, 11, 10, False)]
mt('sw_glint', 'sewer', 'FLOOR', frames=_gl, anim_speed=12)
_gl2 = [star(star(_blank16, 12, 3, False), 3, 12),
        star(_blank16, 12, 3),
        star(star(_blank16, 12, 3, False), 3, 12, False)]
mt('sw_glint2', 'sewer', 'FLOOR', frames=_gl2, anim_speed=14)
_gl3 = [star(_blank16, 8, 7, False), star(_blank16, 8, 7), ['................'] * 16]
mt('sw_glint3', 'sewer', 'FLOOR', frames=_gl3, anim_speed=18)


# The Drain's pieces the tile atlas draws wider than the hand-drawn set:
# the arch and the grate two tiles wide, the counter two wide (laid
# twice), the waterfall three by two. Their art is the atlas's.
mt('sw_arch_r', 'sewer', 'SOLID', flat(1), coll=12)
mt('sw_grate_r', 'sewer', 'FLOOR', flat(1))
mt('sw_counter_r', 'props', 'SOLID', flat(1))
for _i in range(6):
    mt('sw_fall_%d' % _i, 'sewer', 'SOLID', frames=[flat(1), flat(1)], anim_speed=6)

# The trail's and the verges' corner nicks: grass (or the canopy) at a
# corner only. Their art is the painter's (wood_art.py).
for _m in range(1, 16):
    mt('pedge_c%x' % _m, 'forest', 'FLOOR', flat(4))
for _m in range(1, 16):
    mt('verge_c%x' % _m, 'forest', 'FLOOR', flat(4))

# The rot: the blight's bare earth in a living room, one tile for each way
# grass can lie around it, sides and corners (wood_art.rot_combos)
def _rot_combos():
    bl = lambda sd: (1 if sd & 9 else 0) | (2 if sd & 3 else 0) | (4 if sd & 6 else 0) | (8 if sd & 12 else 0)
    return [(sd, cn) for sd in range(16) for cn in range(16) if not cn & bl(sd)]


for _s, _c in _rot_combos():
    mt('rot_%x%x' % (_s, _c), 'forest', 'FLOOR', flat(4))

# the mystery rooms' crowns (their bottom wall seen from the room), the
# floor's edges against the walls (1 N, 2 E, 4 S, 8 W) and their springs,
# drawn in wood_art
for _st in ('cave', 'hollow', 'thicket'):
    mt('%s_crown' % _st, 'stone', 'SOLID', flat(1))
    for _m in range(1, 16):
        mt('%s_edge_%x' % (_st, _m), 'stone', 'FLOOR', flat(1))
    mt('%s_spring' % _st, 'stone', 'FLOOR', flat(1))

# the style boards' tiles replace what they cover, and the rest is
# remapped into the boards' palettes (tiles_style.py)
import tiles_style  # noqa: E402
tiles_style.apply(METATILES)

# the comparison build puts the sprite pack's own tiles in instead
import palettes as _pl  # noqa: E402
if _pl.PACK_TILES:
    import pack_tiles  # noqa: E402
    pack_tiles.apply(METATILES)

# the illustrated tile atlases over both (tile_art.py)
import tile_art  # noqa: E402
tile_art.apply(METATILES)

# the living wood, the blight's floors and the mystery rooms drawn with
# the terrain painter (wood_art.py), over both
import wood_art  # noqa: E402
wood_art.apply(METATILES)

# the environment art pack, V3, over all (env_pack.py)
import env_pack  # noqa: E402
env_pack.apply(METATILES)

# Additional visual variants share exactly the original collision contracts.
for _i in range(8):
    mt('forest_rot%d' % _i, 'forest', 'FLOOR', flat(4))
for _i in range(6):
    mt('forest_canopy%d' % _i, 'wood', 'SOLID', flat(1))

# Species share the oak's upper-half trunk collision and overlay crown.
for _species in ('birch', 'fir', 'sicktree'):
    for _i in range(6):
        mt('%s_%d' % (_species,_i), 'wood', 'SOLID' if _i>=4 else 'FLOOR',
           flat(0 if _i<4 else 4), coll=3 if _i>=4 else 0)
for _name,_type in (('leaf_litter','FLOOR'),('fern_patch','FLOOR'),('sick_bones','FLOOR'),
                    ('sick_stump','SOLID'),('sick_rock','SOLID')):
    mt(_name,'forest',_type,flat(4))

# The forest's final native-resolution art; keep the Drain's tiles intact.
import forest_art  # noqa: E402
forest_art.apply(METATILES, dict(_pl.BG_PALETTES))

# the Drain's hall, painted whole and cut into cells of its own (sw_drain.py)
import sw_drain  # noqa: E402
METATILES.extend(sw_drain.METATILES)

# Atlas-guided corruption after all earlier forest painters. Existing ids
# remain stable; the visual pit clone is appended after every original tile.
import blight_reference
blight_reference.apply(METATILES, dict(_pl.BG_PALETTES))

# Living woodland materials after the blight source; imported decay stays exact.
import healthy_reference
healthy_reference.apply(METATILES, dict(_pl.BG_PALETTES))

# Ground interactions keep their physical contracts but read at native scale.
import interactive_tiles
interactive_tiles.apply(METATILES, dict(_pl.BG_PALETTES))
