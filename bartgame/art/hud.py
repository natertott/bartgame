"""8x8 BG tiles for the HUD, the item slots, the text box frame and the
map, palette 'hud': 1 cream ink, 2 ink shadow, 3 heart red, 4 heart
bright, 5 heart dark, 6 gold dark, 7 gold mid, 8 gold bright, 9 grey,
A frame fill, B blue, C blue dark, D violet, E box fill, F slate."""
from tiles import A

TILES = {}


def t(name, art):
    TILES[name] = A(art)


t('heart_full', '''
    .55..55.
    54435445
    54333335
    53333335
    .533335.
    ..5335..
    ...55...
    ........
''')
t('heart_half', '''
    .55..55.
    54435ee5
    54335ee5
    53335ee5
    .5335e5.
    ..5355..
    ...55...
    ........
''')
t('heart_empty', '''
    .55..55.
    5ee55ee5
    5eeeeee5
    5eeeeee5
    .5eeee5.
    ..5ee5..
    ...55...
    ........
''')
t('gilt', '''
    ..2222..
    .267762.
    26788762
    26787762
    26777762
    .267762.
    ..2222..
    ........
''')
t('key', '''
    ..222...
    .27772..
    .27872..
    ..272...
    ..27722.
    ..272...
    ..27722.
    ...22...
''')
t('bomb', '''
    .....28.
    ....2...
    ..2222..
    .2cddd2.
    2cddddd2
    2ccdddd2
    .2cccc2.
    ..2222..
''')
# the item slots: a gold frame round a dark well, dim or lit
t('slot_tl', '''
    .6666666
    66aaaaaa
    6aaaaaaa
    6aaaaaaa
    6aaaaaaa
    6aaaaaaa
    6aaaaaaa
    6aaaaaaa
''')
t('slot_tr', '''
    6666666.
    aaaaaa66
    aaaaaaa6
    aaaaaaa6
    aaaaaaa6
    aaaaaaa6
    aaaaaaa6
    aaaaaaa6
''')
t('slot_bl', '''
    6aaaaaaa
    6aaaaaaa
    6aaaaaaa
    6aaaaaaa
    6aaaaaaa
    6aaaaaaa
    66aaaaaa
    .6666666
''')
t('slot_br', '''
    aaaaaaa6
    aaaaaaa6
    aaaaaaa6
    aaaaaaa6
    aaaaaaa6
    aaaaaaa6
    aaaaaa66
    6666666.
''')
t('slot_lit_tl', '''
    .8888888
    88777777
    87aaaaaa
    87aaaaaa
    87aaaaaa
    87aaaaaa
    87aaaaaa
    87aaaaaa
''')
t('slot_lit_tr', '''
    8888888.
    77777788
    aaaaaa78
    aaaaaa78
    aaaaaa78
    aaaaaa78
    aaaaaa78
    aaaaaa78
''')
t('slot_lit_bl', '''
    87aaaaaa
    87aaaaaa
    87aaaaaa
    87aaaaaa
    87aaaaaa
    87aaaaaa
    88777777
    .8888888
''')
t('slot_lit_br', '''
    aaaaaa78
    aaaaaa78
    aaaaaa78
    aaaaaa78
    aaaaaa78
    aaaaaa78
    77777788
    8888888.
''')
t('btn_l', '''
    .666666.
    6aaaaaa6
    6a1aaaa6
    6a1aaaa6
    6a1aaaa6
    6a111aa6
    6aaaaaa6
    .666666.
''')
t('btn_a', '''
    .666666.
    6aaaaaa6
    6aa11aa6
    6a1aa1a6
    6a1111a6
    6a1aa1a6
    6aaaaaa6
    .666666.
''')
t('btn_b', '''
    .666666.
    6aaaaaa6
    6a111aa6
    6a1aa1a6
    6a111aa6
    6a1aa1a6
    6a111aa6
    .666666.
''')
t('hand', '''
    ..1.1.1.
    .11111..
    .1111.1.
    .11111..
    1.1111..
    .111.11.
    ..1..1..
    ........
''')
t('btn_r', '''
    .666666.
    6aaaaaa6
    6a111aa6
    6a1a1aa6
    6a111aa6
    6a1a1aa6
    6aaaaaa6
    .666666.
''')
t('box_tl', '''
    ........
    ........
    ..666666
    .6777777
    .67eeeee
    .67eeeee
    .67eeeee
    .67eeeee
''')
t('box_t', '''
    ........
    ........
    66666666
    77777777
    eeeeeeee
    eeeeeeee
    eeeeeeee
    eeeeeeee
''')
t('box_l', '''
    .67eeeee
    .67eeeee
    .67eeeee
    .67eeeee
    .67eeeee
    .67eeeee
    .67eeeee
    .67eeeee
''')
t('box_fill', '''
    eeeeeeee
    eeeeeeee
    eeeeeeee
    eeeeeeee
    eeeeeeee
    eeeeeeee
    eeeeeeee
    eeeeeeee
''')
t('box_bl', '''
    .67eeeee
    .67eeeee
    .67eeeee
    .67eeeee
    .6777777
    ..666666
    ........
    ........
''')
t('box_b', '''
    eeeeeeee
    eeeeeeee
    eeeeeeee
    eeeeeeee
    77777777
    66666666
    ........
    ........
''')
t('arrow', '''
    ........
    ........
    .11111..
    ..111...
    ...1....
    ........
    ........
    ........
''')
t('item_box', '''
    11111119
    1aaaaaa9
    1aaaaaa9
    1aaaaaa9
    1aaaaaa9
    1aaaaaa9
    1aaaaaa9
    99999999
''')
t('lamp', '''
    ...8....
    ..878...
    .27772..
    .26662..
    ..262...
    ..262...
    .27772..
    .22222..
''')
t('cloak', '''
    ...22...
    ..2442..
    .243342.
    .233332.
    23333332
    23332332
    .222222.
    ........
''')
t('cursor', '''
    ........
    .8......
    .88.....
    .888....
    .8888...
    .888....
    .88.....
    .8......
''')
t('map_cell', '''
    99999999
    9ffffff9
    9ffffff9
    9ffffff9
    9ffffff9
    9ffffff9
    9ffffff9
    99999999
''')
t('map_here', '''
    99999999
    9ffffff9
    9ff33ff9
    9f3443f9
    9f3333f9
    9ff33ff9
    9ffffff9
    99999999
''')
t('map_unknown', '''
    ........
    ........
    ........
    ........
    ........
    ........
    ........
    ........
''')
t('map_goal', '''
    99999999
    9ffffff9
    9f7ff7f9
    9f7887f9
    9ff77ff9
    9fff7ff9
    9ffffff9
    99999999
''')
t('rule', '''
    ........
    ........
    ........
    66666666
    77777777
    ........
    ........
    ........
''')

# Tiles that sit inside a box keep nothing transparent: the fill shows
# where the drawing does not, so no scene shows through a cursor, a rule,
# the hand, an unknown map cell, a coin or the corners of a slot.
for _n in ('rule', 'cursor', 'arrow', 'map_unknown', 'hand', 'gilt', 'item_box',
           'slot_tl', 'slot_tr', 'slot_bl', 'slot_br', 'slot_lit_tl', 'slot_lit_tr', 'slot_lit_bl', 'slot_lit_br',
           'btn_l', 'btn_a', 'btn_b', 'btn_r'):
    TILES[_n] = [r.replace('.', 'e') for r in TILES[_n]]
