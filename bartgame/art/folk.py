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


# ------------------------------------------------- the hub's two, large --
# The Pale Gatekeeper and the Billious Peddler at 32x32, built with the
# painter and touched by hand: more of them to see, and a second frame
# each (a blink; the orb pulses, the hands rub). Feet on the bottom row.
from px import Canvas  # noqa: E402
from portraits import disc, cone, line  # noqa: E402


def big_sage(blink=False):
    c = Canvas(32, 32)
    # the staff: a dark shaft, a gold collar, the orb in violet glass
    c.vline(27, 6, 31, 0xe)
    c.set(27, 8, 0xc); c.set(27, 9, 0xb)
    disc(c, 27.5, 4.5, 3.0, 3.0, 9)
    disc(c, 27.5, 4.5, 2.0, 2.0, 0xa)
    c.set(26, 3, 0xd); c.set(27, 3, 0xd); c.set(26, 4, 0xd)
    if blink:
        for (x, y) in ((27, 0), (23, 4), (31, 4), (27, 8), (24, 1), (30, 1), (24, 7), (30, 7)):
            c.set(x, y, 0xa)
    # the robe: a long violet bell hemmed in gold, folds in the dark tone
    cone(c, 12.5, 13, 30, 9, 9, 0xa)
    for x in range(4, 22):
        c.set(x, 29, 0xb); c.set(x, 30, 0xc if x % 3 else 0xb)
    c.hline(3, 22, 31, 1)
    c.set(3, 29, 1); c.set(22, 29, 1)
    for (x, y0) in ((7, 22), (18, 22), (12, 24)):
        c.vline(x, y0, 28, 8)
    # the sleeves fall wide; pale hands folded at the waist, gold cuffs
    c.rect(5, 20, 9, 24, 9); c.rect(16, 20, 20, 24, 9)
    c.rect(6, 24, 9, 24, 0xb); c.rect(16, 24, 19, 24, 0xb)
    c.rect(9, 24, 16, 26, 5)
    c.hline(9, 16, 26, 4); c.set(12, 25, 4); c.set(13, 25, 4)
    # a gold clasp at the throat
    c.set(12, 19, 0xb); c.set(13, 19, 0xb); c.set(12, 20, 0xc); c.set(13, 20, 0xc)
    # white hair falling at the sides, long
    for x in (5, 6, 7):
        c.vline(x, 13, 22 + (x - 5), 0xd)
    for x in (18, 19, 20):
        c.vline(x, 13, 24 - (x - 18), 0xd)
    c.vline(5, 13, 20, 0xd); c.set(6, 23, 0xd); c.set(19, 23, 0xd)
    # the long pale face, the nose down its middle, a thin mouth
    disc(c, 12.5, 16.5, 4.5, 5.5, 5, 0.6, 4)
    c.vline(13, 15, 19, 4); c.set(13, 20, 4); c.set(14, 20, 4)
    c.vline(14, 16, 19, 1); c.set(15, 20, 1); c.set(14, 21, 1)
    c.set(12, 15, 4)
    c.hline(11, 14, 22, 1)
    c.hline(9, 11, 14, 4); c.hline(15, 17, 14, 4)
    if blink:
        c.set(10, 16, 1); c.set(11, 16, 1); c.set(15, 16, 1); c.set(16, 16, 1)
    else:
        c.rect(10, 15, 11, 16, 1); c.rect(15, 15, 16, 16, 1)
        c.set(10, 15, 0xa); c.set(15, 15, 0xa)
    # the tall hat: a violet cone with a gold band, a dark brim over the brow
    cone(c, 12.5, 0, 10, 8, 9, 0xa)
    c.hline(5, 20, 9, 0xb); c.hline(5, 20, 10, 0xc)
    c.hline(4, 21, 11, 8); c.hline(3, 22, 12, 8)
    c.set(12, 2, 0xa); c.set(11, 4, 0xa)
    c.outline(1)
    return c.rows()


def big_merchant(alt=False):
    c = Canvas(32, 32)
    # the pack behind him: a brown bundle, straps, bottles poking out
    c.rect(19, 10, 29, 25, 0xe)
    c.hline(19, 29, 10, 0xc); c.vline(24, 10, 25, 1); c.hline(19, 29, 17, 1)
    c.rect(21, 6, 22, 9, 0xf); c.set(21, 5, 0xc); c.set(22, 5, 0xc)
    c.rect(25, 7, 26, 9, 0xd); c.set(25, 6, 0xc); c.set(26, 6, 0xc)
    c.set(28, 8, 0xb); c.set(28, 9, 0xb); c.set(27, 9, 0xc)
    # the hooded cloak: red, hunched, a dark right side, patches
    cone(c, 12.5, 0, 30, 12, 7)
    disc(c, 12.5, 7.5, 7.5, 7.5, 7)
    for y in range(4, 31):
        for x in range(32):
            if c.get(x, y) == 7 and x + 0.5 - 12.5 > (y - 1) * 12 / 29.0 * 0.45:
                c.set(x, y, 6)
    c.rect(4, 23, 6, 25, 0xf); c.set(4, 23, 1); c.set(6, 25, 1)
    c.rect(16, 26, 18, 28, 9); c.set(18, 26, 1); c.set(16, 28, 1)
    c.hline(2, 23, 30, 6)
    for x in (3, 7, 12, 17, 21):
        c.set(x, 30, 1)
    c.hline(1, 24, 31, 1)
    # the hood's dark hollow, the purple face in it
    disc(c, 12.5, 13, 7, 7.5, 1)
    disc(c, 12.5, 14, 5, 5.5, 3, 0.6, 2)
    # a great hooked nose, warts on it
    for (x, y) in ((13, 13), (14, 13), (14, 14), (15, 14), (15, 15), (16, 15), (16, 16), (17, 16), (17, 17), (17, 18), (16, 18), (15, 17), (14, 16), (14, 15)):
        c.set(x, y, 3)
    for (x, y) in ((16, 17), (16, 18), (15, 16)):
        c.set(x, y, 2)
    line(c, 13, 12, 18, 17, 1); c.set(18, 18, 1); c.set(17, 19, 1)
    c.set(15, 13, 2); c.set(17, 15, 2)
    # gold eyes under the hood, a grin of teeth
    if alt:
        c.hline(9, 10, 13, 0xb); c.hline(14, 15, 12, 0xb)
    else:
        c.rect(9, 12, 10, 13, 0xb); c.set(10, 13, 1)
        c.rect(14, 11, 15, 12, 0xb); c.set(15, 12, 1)
    for i, x in enumerate(range(8, 15)):
        c.set(x, 19, 0xd if i % 2 == 0 else 1)
    c.hline(8, 15, 20, 1)
    # the medallion on its chain
    line(c, 9, 21, 12, 23, 0xc); line(c, 16, 21, 13, 23, 0xc)
    disc(c, 12.5, 24.5, 2.5, 2.5, 0xb); c.set(12, 24, 0xd); c.set(13, 25, 0xc); c.set(12, 25, 0xc)
    # the hands rubbing before him, a ring on each
    hx = 1 if alt else 0
    c.rect(7 + hx, 26, 11 + hx, 28, 3); c.rect(14 - hx, 26, 18 - hx, 28, 3)
    c.hline(7 + hx, 11 + hx, 28, 2); c.hline(14 - hx, 18 - hx, 28, 2)
    c.set(9 + hx, 26, 0xb); c.set(16 - hx, 26, 0xb)
    c.vline(12 + hx, 26, 28, 1); c.vline(13 - hx, 26, 28, 1)
    c.outline(1)
    return c.rows()


BIG = {
    'sage_1': big_sage(),
    'sage_2': big_sage(True),
    'merchant_1': big_merchant(),
    'merchant_2': big_merchant(True),
}
