"""The Drain's props, drawn by hand: letter drawings over the painter's
colours (sw_paint.py). Lit from the upper left, outlined in the darkest
grey, a gleam where the light catches.
"""
from sw_paint import sprite

# a teal chest bound in brass, a lock at its heart
CHEST = sprite({'o': 'g0', 'T': 'a5', 't': 'a4', 'd': 'a3', 'D': 'a2',
                'G': 'b5', 'g': 'b4', 'q': 'b3', 'k': 'g1', 'x': 'x'}, '''
...oooooooooo...
..oTTTTTTTTTto..
.oTTtttttttttdo.
oTtttttttttttddo
oGgGgggggggggqqo
otttttooottttdDo
oTttttoGxotttdDo
ogggggoGgoggqqqo
oTttttooooottdDo
oTtttttttttttdDo
oqqqqqqqqqqqqqqo
.oooooooooooooo.
''')

# a barrel: staves lit on the left, two iron hoops
BARREL = sprite({'o': 'g0', '1': 'd1', '2': 'd2', '3': 'd3', '4': 'd4',
                 'i': 'g3', 'I': 'g4', 'j': 'g2'}, '''
..oooooooo..
.o44433322o.
o4433332221o
o3333322211o
oIIIijjjjj1o
o4333322211o
o4333322211o
o4333322211o
oIIIijjjjj1o
o3333322211o
.o33322211o.
..oooooooo..
''')

def crate(w=14, h=14):
    """a crate: a frame of planks lit on the top and the left, a cross
    brace inside, a nail at each corner"""
    out = [[None] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1):
                c = 'g0'
            elif y == 1 or x == 1:
                c = 'd4'
            elif y == h - 2 or x == w - 2:
                c = 'd2'
            elif y == 2 or x == 2:
                c = 'd3'
            else:
                # the brace: two diagonals, lit on their upper edge
                u, v = x - 3, y - 3
                n = w - 6
                on1 = abs(u - v * (n - 1) / max(1, h - 7)) < 0.9
                on2 = abs((n - 1 - u) - v * (n - 1) / max(1, h - 7)) < 0.9
                if on1 or on2:
                    c = 'd4'
                elif abs(u - v * (n - 1) / max(1, h - 7) - 1) < 0.9 or abs((n - 1 - u) - v * (n - 1) / max(1, h - 7) + 1) < 0.9:
                    c = 'd2'
                else:
                    c = 'd3'
            out[y][x] = c
    for (x, y) in ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)):
        out[y][x] = 'g4'
    return out


CRATE = crate()
CRATE_S = crate(12, 11)


# a skull, grinning
SKULL = sprite({'o': 'g0', 'w': 'x', 'k': 'k2', 's': 'g5', 'h': 'g1'}, '''
..ooooo..
.owwwkko.
owwwwkkso
owhhwhhso
owhhwhhso
.okwhwkso
..okkkso.
..oksksoo
...ooooo.
''')

# potions: a round flask and a tall bottle, corked
FLASK_TEAL = sprite({'o': 'g0', 'c': 'd3', 'C': 'd4', 'L': 'a6', 'l': 'a5', 'd': 'a3', 'x': 'x', 'g': 'g5'}, '''
..oCo..
..oco..
.ogggo.
oxLlllo
oLllldo
olllddo
.oddoo.
..ooo..
''')
FLASK_PURPLE = sprite({'o': 'g0', 'c': 'd3', 'C': 'd3', 'L': 'p4', 'l': 'p3', 'd': 'p2', 'x': 'p4', 'g': 'g5'}, '''
..oCo..
..oco..
.ogggo.
oxLlllo
oLllldo
olllddo
.oddoo.
..ooo..
''')

# a heap of coins
COINS = sprite({'o': 'g0', 'G': 'b5', 'g': 'b4', 'q': 'b3'}, '''
....oooo....
...oGGGgo...
..ooggqqoo..
.oGGGoGGGgo.
oGgqqoggqqqo
oooooooooooo
''')
FLASK_RED = sprite({'o': 'g0', 'c': 'd3', 'C': 'd4', 'L': 'r4', 'l': 'r3', 'd': 'r2', 'x': 'b5', 'g': 'b4'}, '''
..oCo..
..oco..
.ogggo.
oxLlllo
oLllldo
olllddo
.oddoo.
..ooo..
''')

# a candle: wax, a wick, a flame in two frames
CANDLE = sprite({'o': 'g0', 'w': 'x', 'k': 'k2', 's': 'g5'}, '''
.ooo.
owwko
owkko
owkko
owkko
owkso
ooooo
''')
FLAMES = [sprite({'y': 'y1', 'Y': 'y2', 'x': 'x'}, '''
..y..
.yYy.
.YxY.
..Y..
'''), sprite({'y': 'y1', 'Y': 'y2', 'x': 'x'}, '''
..y..
..Yy.
.yxY.
..Y..
'''), sprite({'y': 'y1', 'Y': 'y2', 'x': 'x'}, '''
.....
.yY..
.YxY.
..Y..
''')]

# the crow on the Gatekeeper's crates
CROW = sprite({'o': 'g0', 'b': 'g1', 'B': 'g2', 'h': 'g3', 'e': 'y2', 'k': 'b3'}, '''
...ooo.....
..obBho....
.obbeboo...
okkbbbBBo..
.oobbbbBBo.
...obbbbbBo
...obbbbbbo
....obbbbo.
.....okko..
....okook..
''')
