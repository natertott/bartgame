"""8x8 BG tiles for the HUD and the text box frame, palette 'hud':
1 cream ink, 2 dark brown shadow, 3 red, 4 bright red, 5 dark red,
6-8 gold ramp, 9 gray, A dark slate, B pale blue, C violet, D light
violet, E near-black, F slate."""
from tiles import A

TILES = {}


def t(name, art):
    TILES[name] = A(art)


t('heart_full', '''
    .33..33.
    3443344.
    34444443
    34444443
    .344443.
    ..3443..
    ...33...
    ........
''')
t('heart_half', '''
    .33..55.
    3443555.
    34445555
    34445555
    .344555.
    ..3455..
    ...35...
    ........
''')
t('heart_empty', '''
    .55..55.
    5ee55ee.
    5eeeeee5
    5eeeeee5
    .5eeee5.
    ..5ee5..
    ...55...
    ........
''')
t('gilt', '''
    ...66...
    ..6776..
    .677876.
    .678876.
    .677876.
    ..6776..
    ...66...
    ........
''')
t('key', '''
    .666....
    6..6....
    6..6666.
    6..6.6.6
    .666.6..
    ........
    ........
    ........
''')
t('bomb', '''
    ....7...
    ...e6...
    ..eee...
    .eeeee..
    .eeFee..
    .eeeee..
    ..eee...
    ........
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
    .67777777
    ..666666
    ........
    ........
'''.replace('.67777777', '.6777777'))
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
    .1111...
    ..111...
    ...1....
    ........
    ........
    ........
''')
t('item_box', '''
    99999999
    9aaaaaa9
    9aaaaaa9
    9aaaaaa9
    9aaaaaa9
    9aaaaaa9
    9aaaaaa9
    99999999
''')
t('lamp', '''
    ...77...
    ..7887..
    ..7887..
    ...66...
    ...22...
    ..2222..
    ...22...
    ........
''')
t('cloak', '''
    ...33...
    ..3443..
    .344443.
    .344443.
    3444c443
    34cc4c43
    .3c4443.
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
    9f8888f9
    9f8888f9
    9f8888f9
    9f8888f9
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
    9f3333f9
    9f3443f9
    9f3443f9
    9f3333f9
    9ffffff9
    99999999
''')
