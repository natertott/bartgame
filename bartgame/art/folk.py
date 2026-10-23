"""The five NPCs, 16x32, feet on the bottom row. Palette 'folk': 1 outline,
2-3 purple hide dark..light, 4-5 pale skin shadow..light, 6-7 red
dark..bright, 8-A violet dark..light, B gold, C gold dark, D white,
E brown, F green.
"""
from px import L

NPC = {
    # The Pale Gatekeeper: a tall violet hat with a gold band, a long
    # pale face and nose, white hair, a violet robe hemmed in gold, a
    # staff crowned with a violet-glowing orb.
    'sage': L({' ': 9}, '''
        .......1.....1a1
        ......181....1a1
        ......181....1e1
        .....1 81....1e1
        .....1 81....1e1
        ....1  881...1e1
        ....1  881...1e1
        ...1   8881..1e1
        ...1bbbbbb1..1e1
        .11        11 e1
        1            1e1
        .1111dd1dd1111e1
        ....1d5551d1.1e1
        ...1d1555551.1e1
        ...1d1515151.1e1
        ...1d1555541.1e1
        ...1d15 5541.1e1
        ....1d1554 1.1e1
        .....1 44 1..1e1
        ....1      1.1e1
        ...1 8    8 1 e1
        ...1 8    8 11e1
        ...1 b    b 15e1
        ...1 8    8 15e1
        ..1   8  8   1e1
        ..1          1e1
        ..1bbbbbbbbbb1e1
        ..1          1e1
        ..18        81e1
        ..18888888888 e1
        ..1111111111111.
        ................
    '''),
    # The Billious Peddler: hunched under a red hood, purple hide, a
    # hooked nose, gold eyes, a gold medallion, his pack behind him.
    'merchant': L({' ': 7}, '''
        ......11........
        .....1  1.......
        .....1  1.......
        ....1    1......
        ....1    1.11...
        ...1      1ee1..
        ...1  11  1eee1.
        ..1  1331 1eee1.
        ..1 13bb31 1ee1.
        ..1 1b1b3 1 1e1.
        ..1 133331 11e1.
        ..1 12133 1  e1.
        ..1  1 21 1  e1.
        .1    11    1e1.
        .1          1e1.
        .1  6    6  1e1.
        .1 6      6 1e1.
        .1 6  bb  6 1e1.
        .1 61 bb 16 1e1.
        .1 6  bb  6 111.
        .1 6      6 1...
        .1 6      6 1...
        .1 6      6 1...
        .13 6    6 31...
        .13        31...
        .13 6    6 31...
        .13        31...
        .1 6666666  1...
        .1  ee11ee  1...
        .1  ee1 ee  1...
        .1  11. 11  1...
        .1111...1111....
    '''),
    # The Hermit Knight: bald, a white beard, plate gone to rust, a
    # crimson sash, a rusted sword at his hip.
    'hermit': L({' ': 'e'}, '''
        ................
        .....111111.....
        ....15555551....
        ...1555555555 1.
        ...1551551551...
        ...15555555 1...
        ...1545555451...
        ....15dddd51....
        ....1d1dd1d1....
        ...1dddddddd1...
        ...1dddddddd1...
        ....1ddd1dd1....
        ..11 1dd11 11...
        .1  1 b  1  1...
        .1   1  1    1..
        1 c   1 1  1 11.
        1    8 c 8   1c1
        1 8 1     1 8161
        .11 1 8 8 1 1161
        ....1  c  1.1c61
        ....1     1.1c61
        ....1 7 7 1.1c61
        ....1 7 7 1.1c61
        ....18   81..1b1
        ....1 8 8 1..1b1
        ....1 1 1 1..1b1
        ....1 1 1 1...1.
        ....1 1 1 1.....
        ....1 1 1 1.....
        ...1c 11 c1.....
        ...1ccc ccc1....
        ...1111.1111....
    '''),
    # The Weeping Nun: a white wimple, a dark habit, folded hands, a gold
    # cross, a tear on her cheek.
    'nun': L({' ': 8}, '''
        ................
        ................
        ......1111......
        ....11dddd11....
        ...1dddddddd1...
        ...1dd15551dd1..
        ...1d1555551d1..
        ...1d1515151d1..
        ...1d15554 1d1..
        ...1d1555d51d1..
        ...1d11555 1d1..
        ...1ddd111ddd1..
        ...1ddddd ddd1..
        ..1 ddd   ddd 1.
        ..1  d     d  1.
        .1    d d d    1
        .1    1ddd1    1
        .1    1d d1    1
        .1   9 1d1  9  1
        .1   9  b   9  1
        .1   9 bbb  9  1
        .1  9   b    9 1
        .1  9        9 1
        .1  9        9 1
        .1  9  9  9  9 1
        .1 9   9  9   91
        .1 9   9  9   91
        .1 9   9  9   91
        .1    9    9   1
        .1             1
        .11111111111111.
        ................
    '''),
    # The Blind Gardener: a green hood, a blindfold, a grey beard, a
    # brown apron, a rake in his hand and a flower in his belt.
    'gardener': L({' ': 'f'}, '''
        ...............1
        ......1111....1e
        .....1  ee1...1e
        ....1    ee1..1e
        ....1      1..1e
        ...1  1111  1.1e
        ...1 155551 1.1e
        ...1 1dddd1 1.1e
        ...1 155551 1.1e
        ...1 154451 1.1e
        ...1 1dddd1 1.1e
        ....1ddddd1..1e1
        ....1ddddd1..1e1
        ...1 1ddd1  1e1.
        ..1   1d1   1e1.
        ..1 e     e 1e1.
        .1  1eeeee1  1e1
        .1  1ecece1  1e1
        .1 51eeeee15 1e1
        .11515e7be1511e1
        .1551eeeee155 e1
        ..111ecee11111e1
        ....1eeeee1...1e
        ....1eeeee1..1e1
        ....1ecee c1.1e1
        ....1eeeee1..1e1
        ....1 e e 1..1e1
        ....1 e e 1...1.
        ....1 e e 1.....
        ...1c 11 c1.....
        ...1ccc ccc1....
        ...1111.1111....
    '''),
}
