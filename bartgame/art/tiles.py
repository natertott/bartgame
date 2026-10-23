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

from px import L, Canvas, compose, outline, hflip, vflip, opaque, remap, blank  # noqa: F401

TYPES = ['FLOOR', 'SOLID', 'PIT', 'WATER', 'LEDGE_N', 'LEDGE_E', 'LEDGE_S', 'LEDGE_W',
         'THORN', 'CRACK', 'WEB', 'DOOR', 'DOOR_OPEN', 'TORCH', 'TORCH_LIT', 'SLOW', 'HURT',
         'EXIT', 'CHEST', 'CHEST_OPEN', 'SWITCH', 'STAIRS']

SOLID_TYPES = {'SOLID', 'THORN', 'CRACK', 'WEB', 'DOOR', 'TORCH', 'TORCH_LIT', 'CHEST', 'CHEST_OPEN'}


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


def marks(base, placements, w=16, h=16):
    """A flat tile with small drawings placed on it (wrapping)."""
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
