"""The five NPCs, 16x32, feet on the bottom row. Palette 'folk': 1 outline,
2-4 violet deep..light, 5-6 crimson dark..bright, 7-8 green dark..bright,
9-A brown dark..light, B skin shadow, C skin, D silver, E white, F gold.
"""
from px import L

NPC = {
    # The Sage of the Drain: a silver skullcap, a river of white beard, a
    # violet robe hemmed in gold, a staff with a gold orb.
    'sage': L({' ': 3}, '''
        .............1..
        ............1f1.
        .....1111...1a1.
        ....1deed1..1a1.
        ...1dddddd1.1a1.
        ...1dcccccd11a1.
        ...1cc1cc1c11a1.
        ....1cccccc11a1.
        ....1ceeeec11a1.
        ...1eeeeeeee1a1.
        ..1eeeeeeeeee1a1
        ..1eeeeeeeeee1a1
        ..1eeedeeedee1a1
        ..13eeeeeeee31a1
        .14 3eeeeee3 41a
        .14  3eeee3  41a
        .14   eeee   41a
        .14 3 1ee1 3 41a
        .13   3  3   31a
        .13          31a
        .13          31a
        .13    fff   31a
        ..1 3  fff  3 1a
        ..1          1a.
        ..1  3    3  1a.
        ..13        31a.
        ..1ffffffffff1a.
        ..13        31a.
        ..13        31a.
        ..1222222222  1.
        ..1111111111111.
        ................
    '''),
    # The Merchant: a peaked crimson hood over a face in shadow, gold
    # eyes, a cloak clasped in gold, a purse of gilt.
    'merchant': L({' ': 6}, '''
        .......11.......
        ......1 51......
        ......1  51.....
        .....1   51.....
        .....1    51....
        ....1      51...
        ....1  11  51...
        ...1  1bb1  51..
        ...1 1bbbb1 51..
        ...1 1fb1f1 51..
        ...1 1bbbb1 51..
        ...1  1bb1  51..
        ..1   1cc1   51.
        ..1    f1    51.
        ..1          51.
        .1 5        551.
        .1  5      55 1.
        .1   5    55  1.
        .1 c 5    55c 1.
        .11c15    551c1.
        .1ff11    5 11..
        .1ff1     5  1..
        ..11      55 1..
        ...1 5    55 1..
        ...1 5    55 1..
        ...1 5    55 1..
        ...1555555555 1.
        ...1 9a1 1a9  1.
        ...19aa1 1aa9 1.
        ...1991..1991.1.
        ...1111..1111...
        ................
    '''),
    # The Hermit Knight: bald, a grey beard, dented plate gone dull, a
    # crimson sash, a rusted sword hung at his hip.
    'hermit': L({' ': 'd'}, '''
        ................
        .....111111.....
        ....1cccccc1....
        ...1ccccccccc1..
        ...1cc1cc1cc1...
        ...1cccccccc1...
        ...1cbccccbc1...
        ....1cddddc1....
        ....1dedded1....
        ...1deddddde1...
        ...1dddddddd1...
        ....1ddd1dd1....
        ..11 1dd11 11...
        .1  1 e  1  1...
        .1   1  1    1..
        1 e   1 1  1 11.
        1    2 e 2   1a1
        1 2 1     1 2191
        .11 1 2 2 1 1191
        ....1  e  1.1a91
        ....1     1.1a91
        ....1 6 6 1.1a91
        ....1 6 6 1.1a91
        ....12   21..1f1
        ....1 2 2 1..1f1
        ....1 1 1 1..1f1
        ....1 1 1 1...1.
        ....1 1 1 1.....
        ....1 1 1 1.....
        ...19 11 91.....
        ...1999 9991....
        ...1111.1111....
    '''),
    # The Weeping Nun: a white wimple, a dark habit, folded hands, a gold
    # cross, a tear on her cheek.
    'nun': L({' ': 2}, '''
        ................
        ................
        ......1111......
        ....11eeee11....
        ...1eeeeeeee1...
        ...1ee1ccc1ee1..
        ...1e1ccccc1e1..
        ...1e1c1c1c1e1..
        ...1e1cccbc1e1..
        ...1e1cccdc1e1..
        ...1e11ccc11e1..
        ...1eee111eee1..
        ...1eeeee eee1..
        ..1 eee   eee 1.
        ..1  e     e  1.
        .1    e e e    1
        .1    1eee1    1
        .1    1e e1    1
        .1   3 1e1  3  1
        .1   3  f   3  1
        .1   3 fff  3  1
        .1  3   f    3 1
        .1  3        3 1
        .1  3        3 1
        .1  3  3  3  3 1
        .1 3   3  3   31
        .1 3   3  3   31
        .1 3   3  3   31
        .1    3    3   1
        .1             1
        .11111111111111.
        ................
    '''),
    # The Blind Gardener: a green hood, a blindfold, a grey beard, a
    # brown apron, a rake in his hand and a flower in his belt.
    'gardener': L({' ': 8}, '''
        ...............1
        ......1111....1a
        .....1  771...1a
        ....1    771..1a
        ....1      1..1a
        ...1  1111  1.1a
        ...1 1cccc1 1.1a
        ...1 1eeee1 1.1a
        ...1 1cccc1 1.1a
        ...1 1cbbc1 1.1a
        ...1 1dddd1 1.1a
        ....1ddddd1..1a1
        ....1ddddd1..1a1
        ...1 1ddd1  1a1.
        ..1   1d1   1a1.
        ..1 7     7 1a1.
        .1  1aaaaa1  1a1
        .1  1a9a9a1  1a1
        .1 c1aaaaa1c 1a1
        .11c1a6fa91c11a1
        .1cc1aaaaa1cc1a1
        ..111a9aaa1111a1
        ....1aaaaa1...1a
        ....1aaaaa1..1a1
        ....1a9aa91..1a1
        ....1aaaaa1..1a1
        ....1 7 7 1..1a1
        ....1 7 7 1...1.
        ....1 7 7 1.....
        ...19 11 91.....
        ...1999 9991....
        ...1111.1111....
    '''),
}
