"""BARTGAME metatiles: 16x16 tiles with a behavior type and collision.

Art is rows of 16 hex digits. Ground is drawn by hand from small tuft
and pebble marks placed where they read well; the canopy walls are leaf
masses built from overlapping lit blobs that wrap at the tile edge so
they tile without a seam; landmarks are drawn.

Palette 'forest': 1 outline, 2-6 grass deep..bright, 7-9 soil, A-C blight
                  violet, D-E rot, F pale gleam.
Palette 'wood':   1 outline, 2-6 leaf deepest..bright, 7-A bark, B-C thorn,
                  D mist, E blight black, F gold.
Palette 'stone':  1 outline, 2-6 stone, 7-A water, B-D gold, E moss, F wood.
Palette 'sewer':  1 outline, 2-6 wet stone, 7-9 slime, A-C black water,
                  D rust, E-F flame.
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
# Grass: a mid green with tufts, lit from the upper left. The marks are
# tiny so the ground stays calm under the sprites.
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

# Blight: a violet stain creeping over the grass, with a bright rim and
# a black-violet heart; the second variant grows rot mushrooms.
BLIGHT_PATCH = A('''
    ...aa....
    .aabbaa..
    aabbcbbaa
    abbcbcbba
    aabbbbbaa
    .aabbaa..
    ...aa....
''')
BLIGHT_SMALL = A('''
    .aa.
    abba
    abca
    .aa.
''')
VEIN = A('''
    a...
    .a..
    .a..
    ..a.
    ..aa
''')
MUSHROOM = A('''
    .ee.
    eeee
    dddd
    .dd.
''')
mt('moss_blight', 'forest', 'FLOOR', marks(GRASS, [
    (BLIGHT_PATCH, 1, 1), (BLIGHT_SMALL, 10, 9), (VEIN, 9, 2), (TUFT['e'], 13, 5),
    (TUFT['b'], 2, 11), (TUFT['a'], 6, 11), (TUFT['c'], 14, 14)]))
mt('moss_blight2', 'forest', 'FLOOR', marks(GRASS, [
    (BLIGHT_PATCH, 7, 7), (MUSHROOM, 2, 3), (MUSHROOM, 11, 1), (VEIN, 3, 8),
    (TUFT['a'], 1, 12), (TUFT['e'], 6, 1), (TUFT['c'], 14, 12)]))

# Flowers: pale gold and violet blooms, white hearts.
FLOWER_GOLD = A('''
    .f.
    f9f
    .f.
''')
FLOWER_VIOLET = A('''
    .c.
    caf
    .c.
''')
mt('moss_flowers', 'forest', 'FLOOR', marks(GRASS, [
    (FLOWER_GOLD, 2, 2), (FLOWER_VIOLET, 11, 4), (FLOWER_GOLD, 7, 9), (FLOWER_VIOLET, 1, 11),
    (TUFT['a'], 6, 2), (TUFT['b'], 13, 10), (TUFT['e'], 4, 7), (TUFT['c'], 12, 13),
    (FLOWER_GOLD, 13, 0)]))

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

# A pool of blight: violet liquid with a dark rim; the glints drift.
_pool = marks(0xb, [(A('aa'), 3, 3), (A('a'), 11, 9), (A('aa'), 6, 12), (A('a'), 13, 2)])
_pool = compose(_pool, A('''
    aaaaaaaaaaaaaaaa
    a..............a
    a..............a
    a..............a
    a..............a
    a..............a
    a..............a
    a..............a
    a..............a
    a..............a
    a..............a
    a..............a
    a..............a
    a..............a
    a..............a
    aaaaaaaaaaaaaaaa
'''))
_glint1 = A('''
    ................
    ................
    ....c...........
    ...cfc.......c..
    ....c.......cfc.
    .............c..
    ................
    ................
    ........c.......
    .......cfc......
    ........c.......
    ................
    ..c.............
    .cfc............
    ..c.............
    ................
''')
_glint2 = A('''
    ................
    ................
    ................
    ................
    ....c...........
    ...cfc.......c..
    ....c.......cfc.
    .............c..
    ................
    ................
    ................
    ........c.......
    .......cfc......
    ..c.....c.......
    .cfc............
    ..c.............
''')
mt('blight_pool', 'forest', 'HURT', frames=[compose(_pool, _glint1), compose(_pool, _glint2)], anim_speed=16)


# ---------------------------------------------------------- the canopy --
# Leaf masses: overlapping round blobs, each with a deep shadow ring, a
# mid body, a lit crescent and a bright tip. Drawn top to bottom so the
# lower blobs overlap the upper, wrapping at the edge so the tile seams.
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

# The wall's face, under the top canopy: a hanging leaf fringe, trunks in
# shadow, and the ground shadow the wall throws on the grass.
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
# grass showing between the scallops (leaf light reads as grass).
_crown = leaf_mass([(2, 6, 3.4), (8, 5, 3.8), (14, 6, 3.4), (5, 11, 3.6), (11, 12, 3.6), (0, 14, 2.6)],
                   [(LEAF_TIP, 4, 8), (LEAF_TIP2, 12, 9), (LEAF_TIP, 9, 13)], base=0xd)
_crown = compose(_crown, A('''
    dddddddddddddddd
    dddddddddddddddd
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
# a dark outline where the mass meets the grass
_crown_g = Canvas.from_rows(_crown)
for y in range(16):
    for x in range(16):
        if _crown_g.get(x, y) == 0xd and y < 9:
            # grass pixel: outline below it if a leaf pixel follows
            if _crown_g.get(x, y + 1) in (2, 4, 6):
                _crown_g.set(x, y + 1, 1)
mt('canopy_n', 'wood', 'SOLID', _crown_g.rows())


# A free-standing tree: a 32-wide crown over a trunk, 2x3 metatiles.
# The top four are overlay tiles (the hero walks behind them); the
# trunk pair is ground, solid in its upper half.
def tree_art():
    c = Canvas(32, 48)
    crown = [(16, 10, 9.5), (8, 9, 6.5), (24, 9, 6.5), (6, 16, 6.0), (26, 16, 6.0),
             (12, 21, 6.2), (20, 21, 6.2), (16, 25, 5.0)]
    for cx, cy, r in sorted(crown, key=lambda p: p[1]):
        blob(c, cx, cy, r, (2, 4, 5, 6), wrap=False)
    # trunk
    c.rect(13, 28, 18, 44, 8)
    c.vline(13, 28, 44, 7)
    c.vline(14, 30, 44, 9)
    c.vline(18, 28, 44, 7)
    c.vline(17, 30, 44, 8)
    # roots
    c.hline(11, 13, 44, 8); c.hline(18, 20, 44, 8)
    c.hline(10, 12, 45, 7); c.hline(19, 21, 45, 7)
    c.rect(13, 45, 18, 45, 7)
    # shadow on the ground around the trunk (leaf deep over grass-light)
    c.outline(1)
    return c.rows()


_tree = tree_art()


def slice16(rs, tx, ty):
    return [r[tx * 16:tx * 16 + 16] for r in rs[ty * 16:ty * 16 + 16]]


mt('tree_top_nw', 'wood', 'FLOOR', slice16(_tree, 0, 0))
mt('tree_top_ne', 'wood', 'FLOOR', slice16(_tree, 1, 0))
mt('tree_mid_w', 'wood', 'FLOOR', slice16(_tree, 0, 1))
mt('tree_mid_e', 'wood', 'FLOOR', slice16(_tree, 1, 1))
# the trunk tiles stand on grass, so they take the forest palette, whose
# soil browns serve as bark
_grass_w = marks(GRASS, [(TUFT['a'], 1, 2), (TUFT['e'], 3, 9), (TUFT['c'], 1, 13), (TUFT['b'], 9, 14)])
_grass_e = marks(GRASS, [(TUFT['b'], 11, 3), (TUFT['a'], 12, 8), (TUFT['e'], 7, 14), (TUFT['c'], 14, 13)])
mt('tree_trunk_w', 'forest', 'SOLID', compose(_grass_w, slice16(_tree, 0, 2)), coll=3)
mt('tree_trunk_e', 'forest', 'SOLID', compose(_grass_e, slice16(_tree, 1, 2)), coll=3)

# ------------------------------------------------------------- stones --
# A boulder on moss: blue-grey, lit from the upper left, a gleam on the
# crown, dark under its belly.
mt('rock', 'stone', 'SOLID', L({'o': 1, 'm': 0xe}, '''
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

# A broken pillar: a pale fluted column, moss at its foot.
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

# A ruined wall: tumbled blocks, mortar lines, moss in the cracks.
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

# Thorns: a bramble of dark vines on the grass, blight-violet barbs.
mt('thorn', 'forest', 'THORN', compose(marks(GRASS, [(TUFT['b'], 0, 14), (TUFT['c'], 14, 0)]), A('''
    ................
    ..1.......1.....
    .121..c..121.c..
    .12111c1112111c.
    ..1221c22211221.
    ...122221121b1..
    .c..1222221221..
    .1c..1222221....
    .121..12222c1...
    ..121.1221221...
    ..b1211211.121..
    ...1221.11..121.
    ..11221..c...1..
    ..1.1221.1c.....
    ....1.121.1.....
    ......1.........
''')))

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

# Water: deep blue with lit wave bands and foam crests; two frames.
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

# Pits: a dark hole with a lip of soil on the near edge.
mt('pit', 'forest', 'PIT', A('''
    4444444444444444
    4544444454444444
    3333333333333333
    1111111111111111
    7777717777717777
    7177777177777717
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
mt('pit_inner', 'forest', 'PIT', flat(0))

# Ledges: a step of raised ground ending in a cliff of soil.
mt('ledge_s', 'forest', 'LEDGE_S', A('''
    4444444444444444
    4544444445444444
    4344444443444444
    4444454444445444
    4444434444443444
    6666666666666666
    1111111111111111
    9999999999999999
    8988898888988988
    8888888888888888
    7888788887888878
    7877778877777877
    7777777777777777
    1711117111171117
    1111111111111111
    2222222222222222
'''))
mt('ledge_n', 'forest', 'LEDGE_N', A('''
    1111111111111111
    1711117111171117
    7777777777777777
    7877778877777877
    7888788887888878
    8888888888888888
    8988898888988988
    9999999999999999
    1111111111111111
    6666666666666666
    4444434444443444
    4444454444445444
    4344444443444444
    4544444445444444
    4444444444444444
    4444444444444444
'''))

# ---------------------------------------------------------------- gates --
# A cracked stone slab in the wall: the bombs' door.
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

# A pale web across a dark way: the lamp's door.
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

# A locked door: iron-banded oak, a gold lock, a stone frame.
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

# A censer on a stone pedestal; lit, it carries a gold flame.
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

# Chests: oak with gold bands and a gold lock; open, the lid stands up
# and the inside glows.
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

# Bones in the grass.
mt('bones', 'forest', 'FLOOR', marks(GRASS, [
    (A('''
        ff...ff
        .fffff.
        ff...ff
    '''), 1, 2),
    (A('''
        f9.
        .f9
        ..f9
        ...f9
    '''), 9, 3),
    (A('''
        .ff.
        f99f
        f11f
        .ff.
    '''), 10, 9),
    (TUFT['a'], 6, 7), (TUFT['e'], 13, 14), (TUFT['c'], 0, 14), (TUFT['b'], 3, 11)]))

# Gold motes twinkling on the ground (an overlay).
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
mt('sparkle', 'stone', 'FLOOR', frames=_sp, anim_speed=14)

# The relic's altar: a round stone dais on moss.
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

# A flat paving stone, moss in its chips.
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

# Steps down into the dark.
mt('stairs_down', 'stone', 'STAIRS', A('''
    1111111111111111
    1666666666666661
    1555555555555551
    1111111111111111
    1555555555555551
    1444444444444441
    1111111111111111
    1444444444444441
    1333333333333331
    1111111111111111
    1333333333333331
    1222222222222221
    1111111111111111
    1222222222222221
    1111111111111111
    1111111111111111
'''))


# =============================================================== sewer ===
# Flagstones: big slabs with dark mortar, a light edge on top and left,
# wet shine in a few places.
def flagstones(seed, slabs):
    """slabs: list of (x0, y0, x1, y1, tone) rectangles; mortar between."""
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
    return c.rows()


mt('sw_floor0', 'sewer', 'FLOOR', flagstones(1, [(0, 0, 7, 6, 4), (9, 0, 15, 8, 4), (0, 8, 5, 15, 4), (7, 10, 15, 15, 4)]))
mt('sw_floor1', 'sewer', 'FLOOR', flagstones(2, [(0, 0, 9, 4, 4), (11, 0, 15, 6, 3), (0, 6, 6, 12, 4), (8, 6, 15, 12, 4), (0, 14, 15, 15, 3)]))
mt('sw_floor2', 'sewer', 'FLOOR', flagstones(3, [(0, 0, 5, 9, 3), (7, 0, 15, 5, 4), (7, 7, 12, 15, 4), (14, 7, 15, 15, 4), (0, 11, 5, 15, 4)]))
mt('sw_floor_slime', 'sewer', 'SLOW', compose(
    flagstones(1, [(0, 0, 7, 6, 4), (9, 0, 15, 8, 4), (0, 8, 5, 15, 4), (7, 10, 15, 15, 4)]), A('''
    ................
    .....1777.......
    ...177888771....
    ..17888998871...
    .178889999887...
    .1788899988871..
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

# The wall face: wet bricks in running bond, a mossy drip or two.
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

# Black water: a slow glint moves across it.
_sw1 = A('''
    aaaaaaaaaaaaaaaa
    abbbaaaaaaabbbaa
    aacbbaaaaaaacbaa
    aaaaaaaaaaaaaaaa
    aaaaaaaaaaaaaaaa
    aaaaaabbbaaaaaaa
    aaaaaaacbbaaaaaa
    aaaaaaaaaaaaaaaa
    aaaaaaaaaaaaaaaa
    abbbaaaaaaaabbba
    aacbaaaaaaaaacba
    aaaaaaaaaaaaaaaa
    aaaaaaaaaaaaaaaa
    aaaaaabbbbaaaaaa
    aaaaaaaacbaaaaaa
    aaaaaaaaaaaaaaaa
''')
_sw2 = A('''
    aaaaaaaaaaaaaaaa
    aaabbbaaaaaaabbb
    aaaacbbaaaaaaacb
    aaaaaaaaaaaaaaaa
    aaaaaaaaaaaaaaaa
    aaaaaaaabbbaaaaa
    aaaaaaaaacbbaaaa
    aaaaaaaaaaaaaaaa
    aaaaaaaaaaaaaaaa
    aaabbbaaaaaaaabb
    aaaacbaaaaaaaaac
    aaaaaaaaaaaaaaaa
    aaaaaaaaaaaaaaaa
    aaaaaaaabbbbaaaa
    aaaaaaaaaacbaaaa
    aaaaaaaaaaaaaaaa
''')
mt('sw_water', 'sewer', 'WATER', frames=[_sw1, _sw2], anim_speed=20)

# The channel's edge: floor, then a stone lip, then the drop to the water.
mt('sw_water_edge_n', 'sewer', 'FLOOR', compose(
    flagstones(4, [(0, 0, 6, 7, 4), (8, 0, 15, 7, 4)]), A('''
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
    aaaaaaaaaaaaaaaa
    aaaaaaaaaaaaaaaa
''')))

# An iron grate over the channel: bars both ways, black water beneath.
mt('sw_grate', 'sewer', 'FLOOR', A('''
    5444444444444445
    4511511511511514
    41aa1aa1aa1aa114
    41aa1aa1aa1aa114
    4511511511511514
    41aa1aa1aa1aa114
    41aa1aa1aa1aa114
    4511511511511514
    41aa1aa1aa1aa114
    41aa1aa1aa1aa114
    4511511511511514
    41aa1aa1aa1aa114
    41aa1aa1aa1aa114
    4511511511511514
    4111111111111114
    3333333333333333
'''))

# A rusted pipe mouth in the wall, dripping.
mt('sw_pipe', 'sewer', 'SOLID', compose(_bricks, A('''
    ................
    ................
    ..111111111111..
    .1dddddddddddd1.
    .1d5ddddddddd51.
    .1dd11111111dd1.
    .1d1aaaaaaaa1d1.
    .1d1aaaaaaaa1d1.
    .1d1aaaaaaaa1d1.
    .1dd11111111dd1.
    .1dddddddddddd1.
    ..111111111111..
    ......1b1.......
    ......1b1.......
    .......b........
    ................
''')))

# A ladder up into the dark.
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

# The drain hole: a round dark mouth in the wall, a stone ring.
mt('sw_hole', 'sewer', 'EXIT', compose(_bricks, A('''
    ................
    ....11111111....
    ..115666655511..
    .1566111111551.
    .156111111115541
    .15111aaaa111541
    .1511aaaaaaa1541
    .1511aaaaaaa1541
    .1511aaaaaaa1541
    .1511aaaaaaa1541
    .15111aaaaa11441
    .145111111114431
    .14441111144431.
    ..11444444431...
    ....11111111....
    ................
''')))

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

# An archway: the dark under the vault, the keystone above.
mt('sw_arch', 'sewer', 'SOLID', A('''
    2222222222222222
    2555553255555532
    2544443254444432
    2544443254444432
    2333332233333322
    5532555553255555
    4432544443254444
    4432544443254444
    3322333332233333
    2555553255555532
    2544111111114432
    2541aaaaaaaa1432
    233aaaaaaaaaa322
    55aaaaaaaaaaaa55
    44aaaaaaaaaaaa44
    33aaaaaaaaaaaa33
'''), coll=12)

# The merchant's counter: a plank top on a stone base, gold coin on it.
mt('sw_counter', 'sewer', 'SOLID', A('''
    ................
    ................
    1111111111111111
    1dddddddddddddd1
    1d5ddddddddddd51
    1dddddddddddddd1
    1111111111111111
    1dddddddddddddd1
    1d1111111111111d
    1d14444444444d1d
    1d14555555554d1d
    1d14333333334d1d
    1d14444444444d1d
    1d11111111111d1d
    1dddddddddddddd1
    1111111111111111
'''))

# Rubble: fallen blocks on the floor.
mt('sw_rubble', 'sewer', 'SOLID', compose(
    flagstones(5, [(0, 0, 7, 6, 4), (9, 0, 15, 8, 4), (0, 8, 5, 15, 4), (7, 10, 15, 15, 4)]), A('''
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
