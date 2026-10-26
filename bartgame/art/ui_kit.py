"""The UI kit: the boxes, plates, tabs and slots of the dialogue box, the
shop, the pause menu and the HUD, drawn by hand as 8x8 tiles over the UI
palette, after the boards' navy panels in gold frames.

Tiles are letter drawings over PAL's letters. A frame is drawn from its
top-left corner, top edge and left edge; the engine flips them for the
other three sides, so every frame is the same all round.

    PAL         the UI palette: 15 colours by letter
    TILES       {name: 8 rows of 8 letters}
    TEXT        the colours the text is set in, by name
    HUD_PAL     the HUD's hearts and R's glove: their own palette
    HUD_TILES   {name: 8 rows of 8 letters} over HUD_PAL
    MAP_PAL     the pause map's colours
    OBJ_PAL     PAL as the sprites have it, the map's greens in it
    OBJ_MARKS   {name: 8 rows of 8 letters}: the marks drawn as sprites
"""

# 5-bit values (multiples of 8)
PAL = [
    ('o', (8, 8, 16)),          # 1 outline, the text's shadow
    ('1', (16, 24, 40)),        # 2 navy, deepest: wells, the map's ground
    ('2', (24, 32, 56)),        # 3 navy: the panels' fill
    ('3', (40, 48, 80)),        # 4 navy, raised: slots, rows, idle tabs
    ('4', (72, 88, 120)),       # 5 navy edge: the slots' and rows' rims
    ('y', (112, 72, 24)),       # 6 gold, dark
    ('Y', (192, 136, 48)),      # 7 gold
    ('G', (240, 200, 96)),      # 8 gold, light
    ('W', (248, 240, 192)),     # 9 gold, pale: a gleam
    ('c', (232, 224, 208)),     # A cream: the text
    ('s', (136, 144, 168)),     # B slate: dim text, an empty slot's dashes
    ('h', (248, 208, 64)),      # C the highlight: a word that matters
    ('r', (232, 80, 72)),       # D red: what a thing does
    ('p', (224, 208, 168)),     # E parchment: a speech bubble
    ('b', (64, 40, 32)),        # F brown ink, on the parchment
]
for _k, _c in PAL:
    assert all(v % 8 == 0 for v in _c), _k
INDEX = {k: i + 1 for i, (k, _) in enumerate(PAL)}
RGB = dict(PAL)
TEXT = {'cream': 'c', 'dim': 's', 'high': 'h', 'red': 'r', 'gold': 'G', 'ink': 'b', 'dark': 'o'}

TILES = {}


def t(name, art):
    rows = [r.strip() for r in art.strip('\n').splitlines()]
    assert len(rows) == 8 and all(len(r) == 8 for r in rows), (name, rows)
    TILES[name] = rows


# --------------------------------------------------------------- panel --
# A panel: navy in a double gold line, an outline round it, a stud at
# each corner.
t('panel_tl', '''
    .ooooooo
    oGGGoGGG
    oGWGoooo
    oGGGoYYY
    ooooY222
    oGoY2222
    oGoY2222
    oGoY2222
''')
t('panel_t', '''
    oooooooo
    GGGGGGGG
    oooooooo
    YYYYYYYY
    22222222
    22222222
    22222222
    22222222
''')
t('panel_l', '''
    oGoY2222
    oGoY2222
    oGoY2222
    oGoY2222
    oGoY2222
    oGoY2222
    oGoY2222
    oGoY2222
''')
t('fill', '''
    22222222
    22222222
    22222222
    22222222
    22222222
    22222222
    22222222
    22222222
''')

# the divider between a portrait and the words: the frame's double line
# run down the box, studded where it meets the top and the bottom
t('div_t', '''
    oooooooo
    GGGoGGGG
    oooGoooo
    YYYoYYYY
    222oY222
    222oG222
    222oY222
    222oG222
''')
t('div_m', '''
    222oY222
    222oG222
    222oY222
    222oG222
    222oY222
    222oG222
    222oY222
    222oG222
''')

# the name plate on the box's top edge: two tiles tall, navy raised in a
# thin gold line, its ends studded
t('plate_l_top', '''
    ..oooooo
    .oGGGGGG
    oGWYoooo
    oGYo3333
    oYo33333
    oYo33333
    oYo33333
    oYo33333
''')
t('plate_l_bot', '''
    oYo33333
    oYo33333
    oYo33333
    oYo33333
    oGYo3333
    oGWYoooo
    .oGGGGGG
    ..oooooo
''')
t('plate_m_top', '''
    oooooooo
    GGGGGGGG
    oooooooo
    33333333
    33333333
    33333333
    33333333
    33333333
''')
t('plate_m_bot', '''
    33333333
    33333333
    33333333
    33333333
    33333333
    oooooooo
    GGGGGGGG
    oooooooo
''')

# ---------------------------------------------------------------- slots --
# An item's slot in the pause grid: raised navy, rounded, a cool rim; the
# chosen one's rim gold and studded; an empty one only dashes.
t('slot_tl', '''
    ..oooooo
    .o444444
    o4433333
    o4333333
    o4333333
    o4333333
    o4333333
    o4333333
''')
t('slot_t', '''
    oooooooo
    44444444
    33333333
    33333333
    33333333
    33333333
    33333333
    33333333
''')
t('slot_l', '''
    o4333333
    o4333333
    o4333333
    o4333333
    o4333333
    o4333333
    o4333333
    o4333333
''')
t('slot_fill', '''
    33333333
    33333333
    33333333
    33333333
    33333333
    33333333
    33333333
    33333333
''')
t('sel_tl', '''
    .GGGoooo
    GWGGGGGG
    GGYy3333
    GGy33333
    oG333333
    oG333333
    oG333333
    oG333333
''')
t('sel_t', '''
    oooooooo
    GGGGGGGG
    yyyyyyyy
    33333333
    33333333
    33333333
    33333333
    33333333
''')
t('sel_l', '''
    oGy33333
    oGy33333
    oGy33333
    oGy33333
    oGy33333
    oGy33333
    oGy33333
    oGy33333
''')
t('empty_tl', '''
    ........
    ..ss.ss.
    .s......
    .s......
    ........
    .s......
    .s......
    ........
''')
t('empty_t', '''
    ........
    ss.ss.ss
    ........
    ........
    ........
    ........
    ........
    ........
''')
t('empty_l', '''
    ........
    .s......
    .s......
    ........
    .s......
    .s......
    ........
    .s......
''')

# ----------------------------------------------------------------- tabs --
# The pause pages' tabs: two tiles tall; the open page's gold, the others
# navy in a cool rim. Their ends are the left ones turned.
t('tab_l_top', '''
    ..oooooo
    .o444444
    o4433333
    o4333333
    o4333333
    o4333333
    o4333333
    o4333333
''')
t('tab_l_bot', '''
    o4333333
    o4333333
    o4333333
    o4333333
    o4333333
    o4433333
    .o444444
    ..oooooo
''')
t('tab_m_top', '''
    oooooooo
    44444444
    33333333
    33333333
    33333333
    33333333
    33333333
    33333333
''')
t('tab_m_bot', '''
    33333333
    33333333
    33333333
    33333333
    33333333
    33333333
    44444444
    oooooooo
''')
t('tabon_l_top', '''
    ..oooooo
    .oWWWWWW
    oWGGGGGG
    oWGGGGGG
    oGGGGGGG
    oGGGGGGG
    oGGGGGGG
    oGGGGGGG
''')
t('tabon_l_bot', '''
    oGGGGGGG
    oGGGGGGG
    oYGGGGGG
    oYGGGGGG
    oYGGGGGG
    oyYYYYYY
    .oyyyyyy
    ..oooooo
''')
t('tabon_m_top', '''
    oooooooo
    WWWWWWWW
    GGGGGGGG
    GGGGGGGG
    GGGGGGGG
    GGGGGGGG
    GGGGGGGG
    GGGGGGGG
''')
t('tabon_m_bot', '''
    GGGGGGGG
    GGGGGGGG
    GGGGGGGG
    GGGGGGGG
    GGGGGGGG
    YYYYYYYY
    yyyyyyyy
    oooooooo
''')

# a button's badge: its letter on a rounded slate key
t('badge_a', '''
    .oooooo.
    osssssso
    ossccsso
    oscsscso
    osccccso
    oscsscso
    osssssso
    .oooooo.
''')
t('badge_b', '''
    .oooooo.
    osssssso
    oscccsso
    oscsscso
    oscccsso
    oscsscso
    oscccsso
    .oooooo.
''')
t('badge_l', '''
    .oooooo.
    osssssso
    oscsssso
    oscsssso
    oscsssso
    oscsssso
    osccccso
    .oooooo.
''')
t('badge_r', '''
    .oooooo.
    osssssso
    oscccsso
    oscsscso
    oscccsso
    oscscsso
    oscsscso
    .oooooo.
''')
# ------------------------------------------------------------ the shop --
# A ware's row: raised navy, three tiles tall; the chosen one's rim gold
t('row_tl', '''
    ..oooooo
    .o444444
    o4433333
    o4333333
    o4333333
    o4333333
    o4333333
    o4333333
''')
t('row_t', '''
    oooooooo
    44444444
    33333333
    33333333
    33333333
    33333333
    33333333
    33333333
''')
t('row_l', '''
    o4333333
    o4333333
    o4333333
    o4333333
    o4333333
    o4333333
    o4333333
    o4333333
''')
t('srow_tl', '''
    ..oooooo
    .oGGGGGG
    oGWyyyyy
    oGy33333
    oGy33333
    oGy33333
    oGy33333
    oGy33333
''')
t('srow_t', '''
    oooooooo
    GGGGGGGG
    yyyyyyyy
    33333333
    33333333
    33333333
    33333333
    33333333
''')
t('srow_l', '''
    oGy33333
    oGy33333
    oGy33333
    oGy33333
    oGy33333
    oGy33333
    oGy33333
    oGy33333
''')
# the speech bubble: parchment in brown ink, its tail toward the speaker
t('bub_tl', '''
    ...ooooo
    ..oppppp
    .opppppp
    oppppppp
    oppppppp
    oppppppp
    oppppppp
    oppppppp
''')
t('bub_t', '''
    oooooooo
    pppppppp
    pppppppp
    pppppppp
    pppppppp
    pppppppp
    pppppppp
    pppppppp
''')
t('bub_l', '''
    oppppppp
    oppppppp
    oppppppp
    oppppppp
    oppppppp
    oppppppp
    oppppppp
    oppppppp
''')
t('bub_fill', '''
    pppppppp
    pppppppp
    pppppppp
    pppppppp
    pppppppp
    pppppppp
    pppppppp
    pppppppp
''')
# the tail, in the column left of the bubble, pointing at the speaker;
# the bubble's edge beside it is the join, open where the tail meets it
t('bub_tail', '''
    .......o
    .....oop
    ...ooppp
    .ooppppp
    oppppppp
    .ooopppp
    ....oooo
    ........
''')
t('bub_join', '''
    pppppppp
    pppppppp
    pppppppp
    pppppppp
    pppppppp
    pppppppp
    oppppppp
    oppppppp
''')
# a gilt coin, for prices and the purse
t('coin', '''
    ........
    ..oooo..
    .oGGYYo.
    oGWGYYyo
    oGGYYyyo
    oYYYyyyo
    .oyyyyo.
    ..oooo..
''')
# a short rule under a heading
t('rule', '''
    22222222
    22222222
    22222222
    yyyyyyyy
    YYYYYYYY
    22222222
    22222222
    22222222
''')
t('rule_end', '''
    22222222
    22222222
    22222222
    yyyyyyy2
    YYYYYYoo
    22222222
    22222222
    22222222
''')

# ----------------------------------------------------------- the HUD --
# The HUD's panels float over the world: the same double gold line as
# the boxes', set two pixels in from the tile's edge so a margin of the
# world shows round each panel, then two of navy before what it holds.
t('hud_tl', '''
    ........
    ........
    ...ooooo
    ..oGGGGG
    ..oGoooo
    ..oGoYYY
    ..oGoY22
    ..oGoY22
''')
t('hud_t', '''
    ........
    ........
    oooooooo
    GGGGGGGG
    oooooooo
    YYYYYYYY
    22222222
    22222222
''')
t('hud_l', '''
    ..oGoY22
    ..oGoY22
    ..oGoY22
    ..oGoY22
    ..oGoY22
    ..oGoY22
    ..oGoY22
    ..oGoY22
''')
# a gold key, for the keys on the purse's line
t('key', '''
    ........
    .ooo....
    oGWYo...
    oYoYoooo
    oYYYYYYo
    .ooo.YoY
    .....o.o
    ........
''')

# The hearts and R's hand sit on the HUD's panel in a palette of their
# own (BG slot 15, 'hud'): the panels' navies, then the hearts' reds and
# the hand's cream. Every pixel is set, the navy where nothing is drawn,
# so no room shows through between them.
HUD_PAL = [
    ('o', (8, 8, 16)),          # 1 outline
    ('2', (24, 32, 56)),        # 2 navy: the panel's fill, as the kit's
    ('3', (40, 48, 80)),        # 3 navy, raised: an empty heart
    ('4', (72, 88, 120)),       # 4 navy edge: an empty heart's gleam
    ('R', (136, 24, 40)),       # 5 heart, dark
    ('r', (216, 48, 56)),       # 6 heart red
    ('q', (248, 120, 112)),     # 7 heart, lit
    ('W', (248, 240, 192)),     # 8 a gleam
    ('c', (232, 224, 208)),     # 9 cream: the hand
    ('s', (136, 144, 168)),     # A slate: the hand's shade
]
for _k, _c in HUD_PAL:
    assert all(v % 8 == 0 for v in _c), _k
assert dict(HUD_PAL)['2'] == RGB['2']
HUD_INDEX = {k: i + 1 for i, (k, _) in enumerate(HUD_PAL)}
HUD_TILES = {}


def ht(name, art):
    rows = [r.strip() for r in art.strip('\n').split('\n')]
    assert len(rows) == 8 and all(len(r) == 8 and set(r) <= set(HUD_INDEX) for r in rows), name
    HUD_TILES[name] = rows


ht('heart_full', '''
    2oo2oo22
    oWqoqro2
    oqrrrro2
    orrrrRo2
    2orrRo22
    22oRo222
    222o2222
    22222222
''')
ht('heart_half', '''
    2oo2oo22
    oWqo33o2
    oqrr33o2
    orrr33o2
    2orr3o22
    22oro222
    222o2222
    22222222
''')
ht('heart_empty', '''
    2oo2oo22
    o43o33o2
    o33333o2
    o33333o2
    2o333o22
    22o3o222
    222o2222
    22222222
''')
# R lifts and throws: an open glove
ht('hand', '''
    22o2o2o2
    2ocococo
    2ocococo
    oococcco
    occcccco
    2occccso
    22occso2
    222ooo22
''')

# ----------------------------------------------------------- the map --
# The map's own colours (a palette of their own, the menu's second):
# the ground is the panel's deepest navy with a faint grid, the ways are
# green with a lit rim, water blue, the blight violet.
MAP_PAL = [
    ('o', (8, 8, 16)),          # 1 outline
    ('n', (16, 24, 40)),        # 2 the ground, navy
    ('N', (24, 40, 64)),        # 3 the grid on it
    ('k', (24, 56, 40)),        # 4 green, deepest: a way's edge in shadow
    ('g', (56, 120, 64)),       # 5 green: a way
    ('G', (104, 176, 96)),      # 6 green, lit: a way's rim
    ('L', (168, 216, 128)),     # 7 green, pale: a path worn in it
    ('w', (40, 96, 168)),       # 8 water
    ('W', (96, 160, 216)),      # 9 water, lit
    ('b', (104, 80, 48)),       # A a ledge, a bridge's planks
    ('v', (120, 56, 168)),      # B the blight
    ('V', (176, 120, 216)),     # C the blight, lit: its rim, its veins
    ('U', (56, 64, 96)),        # D the dotted edge of a cell not yet seen
    ('y', (240, 200, 96)),      # E gold: the cell the cursor is on
    ('c', (232, 224, 208)),     # F cream
]
for _k, _c in MAP_PAL:
    assert all(v % 8 == 0 for v in _c), _k
MAP_INDEX = {k: i + 1 for i, (k, _) in enumerate(MAP_PAL)}
MAP_RGB = dict(MAP_PAL)

# The kit's palette as the sprites have it (OBJ slot 'uikit'): the same
# letters, but the parchment and its ink, which no sprite draws, are the
# map's greens, for the HUD's mini-map.
OBJ_PAL = [(k, MAP_RGB['g'] if k == 'p' else MAP_RGB['G'] if k == 'b' else c) for k, c in PAL]

# ---------------------------------------------------------- sprites --
# Marks drawn as sprites over the boxes, in the kit's palette (OBJ slot
# 'uikit'): the box's "more" arrow, the shop's pointer, the map cursor's
# corner, and the buttons' badges over the HUD's icons, 8x8 each
OBJ_MARKS = {
    'next': [
        '........',
        'oooooooo',
        'oGGGGGYo',
        '.oGGGYo.',
        '..oGYo..',
        '...oo...',
        '........',
        '........',
    ],
    'pick': [
        '.oo.....',
        '.oGo....',
        '.oGGo...',
        '.oGGYo..',
        '.oGYo...',
        '.oYo....',
        '.oo.....',
        '........',
    ],
    # a corner of the map's cell cursor; the other three are it turned
    'corner': [
        'ooooo...',
        'oGGGo...',
        'oGooo...',
        'oGo.....',
        'ooo.....',
        '........',
        '........',
        '........',
    ],
}


# the badges are the kit's own, as sprites so they sit over the icons
for _b in ('badge_a', 'badge_b', 'badge_l'):
    OBJ_MARKS[_b] = TILES[_b]


def obj_rows(rows):
    """a mark's rows as the sprite build wants them: hex digits, '.' clear"""
    return [''.join('.' if ch == '.' else '%x' % INDEX[ch] for ch in r) for r in rows]
