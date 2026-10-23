"""8x8 BG tiles for the HUD and the text box frame, palette 'hud':
1 cream ink, 2 ink shadow, 3 heart red, 4 heart bright, 5 heart dark,
6 gold dark, 7 gold mid, 8 gold bright, 9 grey, A frame dark, B pale
blue, C violet, D light violet, E box fill, F slate."""
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
    9ff88ff9
    9f8888f9
    9f8888f9
    9ff88ff9
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
    9f3ff3f9
    9f3443f9
    9ff33ff9
    9fff3ff9
    9ffffff9
    99999999
''')
