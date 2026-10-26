"""The Drain's two keepers, drawn by hand for the OBJ layer: the Billious
Peddler behind his counter and the Pale Gatekeeper on her rug.

Each is drawn in parts, letter drawings over a palette of their own, and
every frame is the parts put together, so a blink, a glance or a hand's
business is one part swapped. Lit from the upper left like the hall,
outlined in the darkest colour.

The Peddler is two sprites of 64x32, his head over his body, so what his
face does and what his hands do mix freely. The Gatekeeper is one of
64x64, and a wisp of flame over her orb is a sprite of its own, 16x16;
her orb's glow pulses in two palette entries. npc.c plays them.

    PEDDLER_PAL, GATEKEEPER_PAL     the palettes, 15 colours by letter
    SHEETS                          [(name, palette, w, h, {frame: rows})]
    PEDDLER_ACTS                    his business: steps of (body, face, frames)
    ORB_GLOW                        the orb's two colours through a pulse
"""

# ----------------------------------------------------------- palettes --
# 5-bit values (multiples of 8), index 1..15 in this order; 0 is clear
PEDDLER_PAL = [
    ('o', (16, 8, 24)),                                   # outline
    ('1', (40, 24, 64)), ('2', (72, 40, 104)),            # the hood's purple,
    ('3', (112, 64, 144)), ('4', (160, 112, 184)),        #   dark to light
    ('y', (128, 72, 16)), ('Y', (208, 144, 40)), ('G', (248, 216, 96)),   # gold
    ('s', (112, 88, 128)), ('S', (168, 144, 176)), ('L', (216, 200, 216)),  # skin
    ('n', (168, 80, 120)), ('N', (224, 144, 176)), ('M', (248, 200, 216)),  # nose
    ('r', (208, 48, 56)),                                 # the gems
]
GATEKEEPER_PAL = [
    ('o', (16, 8, 32)),                                   # outline
    ('1', (40, 16, 64)), ('2', (72, 32, 104)),            # robe and hat,
    ('3', (112, 56, 152)), ('4', (152, 96, 192)),         #   dark to light
    ('y', (136, 80, 24)), ('Y', (216, 160, 48)), ('G', (248, 224, 120)),  # gold
    ('k', (88, 64, 112)), ('s', (152, 136, 168)),         # her face in shadow,
    ('S', (208, 200, 216)), ('W', (248, 240, 248)),       #   her hair, pale
    ('r', (216, 40, 56)),                                 # her eyes
    ('v', (160, 64, 232)), ('V', (216, 144, 248)),        # the orb's glow
]
for _n, _p in (('peddler', PEDDLER_PAL), ('gatekeeper', GATEKEEPER_PAL)):
    assert len(_p) == 15, _n
    for _k, _c in _p:
        assert all(v % 8 == 0 for v in _c), (_n, _k)

# the orb's two glow colours, (v, V), through one pulse: npc.c steps it
ORB_GLOW = [((120, 40, 200), (184, 112, 240)), ((136, 48, 216), (200, 128, 248)),
            ((160, 64, 232), (216, 144, 248)), ((184, 88, 240), (232, 168, 248)),
            ((208, 112, 248), (240, 192, 248)), ((184, 88, 240), (232, 168, 248)),
            ((160, 64, 232), (216, 144, 248)), ((136, 48, 216), (200, 128, 248))]


# ------------------------------------------------------------- frames --
def part(text):
    """a letter drawing to rows; '.' is clear"""
    return [ln.rstrip() for ln in text.strip('\n').splitlines()]


class Frame:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [['.'] * w for _ in range(h)]

    def stamp(self, rows, x0, y0):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != '.' and 0 <= x0 + i < self.w and 0 <= y0 + j < self.h:
                    self.px[y0 + j][x0 + i] = ch
        return self

    def put(self, x, y, s):
        """letters over what is there; '_' leaves a pixel, '.' clears it"""
        for i, ch in enumerate(s):
            if ch != '_' and 0 <= x + i < self.w and 0 <= y < self.h:
                self.px[y][x + i] = ch
        return self

    def rows(self, pal):
        idx = {k: '%x' % (i + 1) for i, (k, _) in enumerate(pal)}
        return [''.join('.' if ch == '.' else idx[ch] for ch in r) for r in self.px]


def build(w, h, layers, edits=()):
    f = Frame(w, h)
    for (rows, x, y) in layers:
        f.stamp(rows, x, y)
    for (x, y, s) in edits:
        f.put(x, y, s)
    return f


# ========================================================= the Peddler ==
# Drawn on a 64x64 page over his stall: x 0 is the counter's left end
# (hall x 40), y 50 its back edge (hall y 80). His head sprite is the
# page's rows 16-47, his body's rows 32-63: nothing of his body but his
# hands, his sleeves' cuffs and his coin comes below row 49, so the
# counter's top, on the ground, lies under them.
P_HEAD = part('''
.............oooooooooo...............
....oooo..ooo4444444333oo.............
..oo4443oo4444G444443333oo............
.o444333334444444444443333G32o........
o43333222344444444444443333322o.......
o4322ooo3444444444G44443333332222o....
o322o..o34444444444444333333333222o...
o32o...o3444444444444433333333G3222o..
o2o....o334444444333334444444443322o..
.o.....o33344444333333o44444444444o32o
.......oo334443333333o11111111111114o2o
.......oMoo3333333333o1sssssssssSSS1o2o
........oNNoo33G3333ooSooossSSoSSooSoo.
........onNNNoo33333oSLGGGooSSSGoSoo...
.........onNNNNo333oSLLsGosSSSMMNoo....
..........onNNNo3oooSLLLssSSSnMMMNNoo..
...........ooYoo11oSLLLLLSSSSonMMMNNNo.
............Y.Y111oSLLLLLSSSoonnMMNNNo.
.............Yo111oSSLLLSSSSoooonnMMNNo
...........o221111ooSSSoooooSo..onnMNNo
..........o1222111ooSsosLssoso..onNNo..
..........o11222111o1osSSSsso...onNNo..
.........o1112222111o1osssso.....onNo..
.........o11112222111oooooo.......oo...
''')
P_HEAD_AT = (10, 2)        # on the head sprite

# his eyes and his mouth, over the head (head sprite coordinates)
HX, HY = P_HEAD_AT
P_EYES = {
    'open': [],
    'blink': [(HX + 23, HY + 13, 'sss'), (HX + 23, HY + 14, 'ooo'), (HX + 31, HY + 13, 'o')],
    'left': [(HX + 23, HY + 13, 'oGG'), (HX + 24, HY + 14, 'GG'), (HX + 31, HY + 13, 'oG')],
    'down': [(HX + 23, HY + 13, 'GGG'), (HX + 23, HY + 14, 'oGs'), (HX + 31, HY + 13, 'G')],
    'squint': [(HX + 23, HY + 13, 'oGG'), (HX + 23, HY + 14, 'soo'), (HX + 31, HY + 13, 'o')],
}
P_MOUTHS = {
    'frown': [],
    # a greedy grin: the corners up, his teeth (one gone)
    'grin': [(HX + 21, HY + 18, 'o______o'), (HX + 22, HY + 19, 'oLLsLLo'), (HX + 22, HY + 20, 'oooooo')],
}

P_MANTLE = part('''
.........o3333o...................................
........o344443o..................................
.......o34444433o..................ooooooo........
......o344444333o................oo2222222oo......
.....o3444G44333o.......oooooo..o122222222221o....
.....o344444433333o....o333333oo12222222222221o...
....o34444443333333o..o33333332222222222222221o...
....o344444333G33333oo3333333222222222222222211o..
...o3444433333333333o33333332222222222222222211o..
...o34443333333333333o3333332222222222222222111o..
..o344433333G33333333o333333222222222222222211o...
..o34433333333333333o3333332222222222222222111o...
.o3443333333333333333o33333222222222222222221111o.
.o34333333G3333333333o333332222222222222222221111o
o3433333333333333333o3333322222222222222222221111o
o3333333333333333333o3333322222222222222222221111o
''')
P_NECKLACE = part('''
.Y...........Y.
.Y...........Y.
..Y.........Y..
..GY.......YG..
...YGY...YGY...
.....rYGYr.....
....rGr.rGr....
.....r.r.r.....
.......r.......
......rGr......
.......r.......
''')
# the near arm, his sleeve down to the counter, and its hand on his coin
P_SLEEVE_L = part('''
...oooooo...
..o4LL444o..
.o4LL44443o.
.o4L444433o.
o4LL444433o.
o4L4444333o.
o4L4444333o.
o4L444o333o.
oLL44o4333o.
oLLL444332o.
.ooooooooo..
''')
P_HAND_L = {
    'rest': part('''
..ooooo...
.oLLLLLoo.
oLLLSSSSSo
oLSoSoSoSo
oSo.o.o.o.
.o........
'''),
    # lifted off the coin, the fingers spread over it as it spins
    'lift': part('''
..oooooo..
.oLLLLLLo.
oLLSSSSSSo
oSoSoSoSso
.o.o.o.o.o
'''),
    # flat on the coin, stopping it
    'slap': part('''
.ooooooooo.
oLLLLLLSSSo
oLSSSSSSSso
oSoSoSoSoSo
.o.o.o.o.o.
'''),
}
# his coin, standing on its edge, and the turns of it spinning
P_COIN = {
    9: part('''
..ooooo..
.oGGGGYo.
oGGYYYYyo
oGYGGGYyo
oGYGYyYyo
oGYYyyYyo
oYYYYYyyo
.oyyyyyo.
..ooooo..
'''),
    7: part('''
.ooooo.
oGGGYYo
oGYYYyo
oGYGYyo
oGYYYyo
oGYYyyo
oYYYYyo
oyyyyyo
.ooooo.
'''),
    5: part('''
.ooo.
oGYYo
oGYyo
oGGyo
oGYyo
oGYyo
oYYyo
oYyyo
.ooo.
'''),
    3: part('''
.o.
oGo
oYo
oYo
oYo
oYo
oyo
oyo
.o.
'''),
    -5: part('''
.ooo.
oYYyo
oYyyo
oYyyo
oGYyo
oYyyo
oYyyo
oyyyo
.ooo.
'''),
    -7: part('''
.ooooo.
oYYYyyo
oYYyyyo
oGYyyyo
oYYyyyo
oYYyyyo
oYyyyyo
oyyyyyo
.ooooo.
'''),
    -9: part('''
..ooooo..
.oYYYYyo.
oYYYyyyyo
oGYyyyyyo
oYYyyyyyo
oYYyyyyyo
oYYyyyyyo
.oyyyyyo.
..ooooo..
'''),
}
COIN_CX, COIN_Y = 19, 45       # the coin's middle and top, on the page

# the far arm, and its hand flat on the counter, a finger tapping
P_SLEEVE_R = part('''
..oooooo..
.o443332o.
o4443332o.
o4433322o.
o433322o..
o433o222o.
o43o32222o
o4333222o.
o333222o..
ooooooo...
''')
P_HAND_R = {
    'rest': part('''
.ooooooo...
oLLLLLSSo..
oLSLSLSSso.
oSoSoSoSso.
.o.o.o.oo..
'''),
    # drumming: two fingers up, then the other two
    'tap': part('''
.ooooooo...
oLLLLLSSo..
oLSLSLSSso.
oooSoooSso.
...o...oo..
'''),
    'tap2': part('''
.ooooooo...
oLLLLLSSo..
oLSLSLSSso.
oSoooSooso.
.o...o..o..
'''),
}
# both hands brought together over the counter, rubbing
P_SLEEVE_L_RUB = part('''
...oooooo....
..o4LL444o...
.o4LL44443o..
.o4L444433o..
o4LL4444333o.
o4L44444333o.
.o4L4444333o.
.o4LL444433o.
..o4LL44433oo
..oLLL444333o
...oooooooo..
''')
P_SLEEVE_R_RUB = part('''
....oooooo
...o443332o
..o4433322o
..o433322o.
.o433322o..
.o43322o...
o433222o...
o432222o...
o33222o....
oooooo.....
''')
P_HANDS_RUB = [part('''
..ooooo.ooooo..
.oLLLLLoLLLSSo.
oLLSSSSoSSSSSso
oLSoSoSoSoSoSso
.o.o.o.o.o.o.o.
'''), part('''
..ooooooooooo..
.oLLLLLoLLLSSo.
oLLSSSSoSSSSSso
oSoSoSoSoSoSoSo
.o.o.o.o.o.o.o.
''')]


def peddler_head(eyes='open', mouth='frown'):
    return build(64, 32, [(P_HEAD,) + P_HEAD_AT], P_EYES[eyes] + P_MOUTHS[mouth])


def peddler_body(left='rest', coin=9, right='rest', rub=None):
    """his body sprite: the page's rows 32-63"""
    oy = -32
    layers = [(P_MANTLE, 2, 34 + oy), (P_NECKLACE, 29, 38 + oy)]
    if rub is None:
        layers.append((P_SLEEVE_R, 41, 40 + oy))
        layers.append((P_SLEEVE_L, 9, 37 + oy))
        c = P_COIN[coin]
        layers.append((c, COIN_CX - len(c[0]) // 2, COIN_Y + oy))
        hx, hy = {'rest': (13, 44), 'lift': (13, 41), 'slap': (14, 45)}[left]
        layers.append((P_HAND_L[left], hx, hy + oy))
        layers.append((P_HAND_R[right], 42, 49 + oy))
    else:
        c = P_COIN[9]
        layers.append((c, COIN_CX - 4, COIN_Y + oy))
        layers.append((P_SLEEVE_R_RUB, 36, 40 + oy))
        layers.append((P_SLEEVE_L_RUB, 14, 37 + oy))
        layers.append((P_HANDS_RUB[rub], 25, 46 + oy))
    return build(64, 32, layers)


PEDDLER_HEAD = {
    'open': peddler_head(),
    'blink': peddler_head('blink'),
    'left': peddler_head('left'),
    'down': peddler_head('down'),
    'grin': peddler_head('squint', 'grin'),
}
PEDDLER_BODY = {
    'rest': peddler_body(),
    'tap': peddler_body(right='tap'),
    'tap2': peddler_body(right='tap2'),
    'lift': peddler_body('lift'),
    'spin9': peddler_body('lift', 9),
    'spin7': peddler_body('lift', 7),
    'spin5': peddler_body('lift', 5),
    'spin3': peddler_body('lift', 3),
    'spin5b': peddler_body('lift', -5),
    'spin7b': peddler_body('lift', -7),
    'spin9b': peddler_body('lift', -9),
    'slap': peddler_body('slap'),
    'rub0': peddler_body(rub=0),
    'rub1': peddler_body(rub=1),
}


# ===================================================== the Gatekeeper ==
# Drawn on a 64x64 page: x 32 is where she stands (hall x 344), y 63 her
# feet (hall y 93), on her rug.
G_HAT = part('''
..................ooooo........
................oo44443oo......
...............o444433322oo....
..............o44433332222o....
..............o4433oo22222o....
.............o4433o..o2222o....
.............o4433o...o221o....
............o44332o....o1o.....
............o4G3322o....o......
...........o4443322o...........
...........o444332G2o..........
..........o44443322222o........
..........o444G33322222o.......
.........o4444333322222o.......
.........o44443333222222o......
........oyYYGYYYYYYyyyyyyo.....
........oyYYYYYYYYYYyyyyyo.....
....oooo44444433333322222oooo..
..oo444444444443333333332222oo.
.o4444444443333333333333322221o
..oo11111111111111111111111oo..
....ooooooooooooooooooooooo....
''')
G_FACE = part('''
..oksSkkkkkkkkksko..
.oksSSkkkkkkkkkkSsko
.oksSSkrrkkkkrrkSsko
.oksSSkkkkkSkkkkSsko
.oksSsskssSWskssSsko
.oksSSssssSWssssSsko
.oksSSssssSWSssssSko
.oksSSsssSWWSssssSko
.oksSSsssSWWSksssSko
.oksSSssskSSkkssSsko
.oksSSoskkoooksosSko
..oksSSosssssssoSsko
..oksSo.ossssso.Ssko
..oksso..okkko..sko.
...oksSo........sko.
...oksso.........ko.
....okso.........o..
.....oo.............
''')
G_ROBE = part('''
.......oooooooooooo.......
......o222222211111o......
.....o22222222111111o.....
.....o222222Y21111111o....
....o222222YGY1111111o....
....o2222222YY1111111o....
....o2222222Y21111111o....
....o2322222Y21111111o....
...o23222222Y211111111o...
...o23222222Y211111111o...
...o32222222Y211111111o...
...o32222222Y2111111111o..
..o232222222Y2111111111o..
..o322222122Y21111111111o.
..o322Y21222Y211111Y1111o.
..o32YGY1222Y21111Y11111o.
.o2322Y12222Y21111Y111111o
.o3222212222Y211111Y11111o
.o3222122Y22Y211y11111111o
o33222122222Y2111111111111o
oYGYYYYYYYYYYYYYYYYYYYYyyyo
oyyyyyyyyyyyyyyyyyyyyyyyyyo
.o11oooooooooooooooooo11o..
..oo..................oo...
''')
G_SLEEVE_L = part('''
.....ooo....
....o233o...
...o23332o..
..o233322o..
..o233221o..
.o2332221o..
.o2332211o..
o23322211o..
o2332221o...
o33222211oo.
o3222221111o
oGYYY22111o.
.oyyYYYYYo..
..ooooooo...
''')
G_SLEEVE_R = part('''
...ooo......
..o1111o....
..o11111o...
..o111111o..
..o1111111o.
...o111111o.
...o1111111o
...o11111111o
..o111111111o
..o1111111111o
..o11111111yyo
...oyYYyyyyyo.
....ooooooo...
''')
G_STAFF = part('\n'.join(['.oYo.', 'oGYyo', 'oYyyo', '.oYo.'] + ['.oGo.', '.oYo.', '.oyo.'] * 12 + ['.ooo.']))
G_ORB = part('''
..ooooo..
.ovVVVvo.
ovVWWVvvo
ovWWWVvvo
ovVWVVvvo
ovVVVvv2o
.ovvvv2o.
..oYoYo..
...oYo...
''')
G_HAND_L = part('''
.ooo.
oSWSo
oWSso
oSsso
.ooo.
''')
G_HAND_R = part('''
.oooo
oSWSo
oSSso
.ooo.
''')
# her free hand raised, palm up, a light kindled over it
G_HAND_L_UP = part('''
..V..
.vWv.
..v..
.ooo.
oSWSo
oWSso
.ooo.
''')


def gatekeeper(blink=False, breath=0, hand='down'):
    up = breath
    layers = [(G_ROBE, 19, 39), (G_SLEEVE_R, 34, 39), (G_STAFF, 41, 22), (G_ORB, 39, 14),
              (G_HAND_R, 40, 44), (G_FACE, 21, 29 + up), (G_SLEEVE_L, 17, 39)]
    if hand == 'down':
        layers.append((G_HAND_L, 25, 43))
    else:
        layers.append((G_HAND_L_UP, 25, 37))
    layers.append((G_HAT, 15, 8 + up))
    edits = []
    if blink:
        edits = [(21 + 7, 29 + up + 2, 'kk'), (21 + 13, 29 + up + 2, 'kk')]
    return build(64, 64, layers, edits)


GATEKEEPER = {
    'idle': gatekeeper(),
    'blink': gatekeeper(blink=True),
    'breath': gatekeeper(breath=1),
    'breath_blink': gatekeeper(blink=True, breath=1),
    'kindle': gatekeeper(hand='up'),
    'kindle_blink': gatekeeper(blink=True, hand='up'),
}

# the wisp of flame over her orb, curling as it burns
WISP = {
    'w0': build(16, 16, [(part('''
........V.......
.......vV.......
.......vVv......
........vV......
.......vVv......
......vVv.......
......vVv.......
.......vVv......
........vVv.....
.......vVWv.....
......vVWWVv....
'''), 0, 5)]),
    'w1': build(16, 16, [(part('''
.......V........
.......Vv.......
......vVv.......
......vV........
.......vVv......
........vVv.....
........vVv.....
.......vVv......
......vVv.......
......vVWv......
.....vVWWVv.....
'''), 0, 5)]),
    'w2': build(16, 16, [(part('''
.........V......
........vV......
.......vVv......
......vVv.......
......vV........
......vVv.......
.......vVv......
........vVv.....
.......vVv......
......vVWVv.....
.....vVWWVv.....
'''), 0, 5)]),
    'w3': build(16, 16, [(part('''
................
......V.........
......vV........
.......vVv......
........vVv.....
........vVv.....
.......vVv......
......vVv.......
......vVVv......
......vVWVv.....
.....vVWWWVv....
'''), 0, 5)]),
}
WISP_AT = (35, 0)    # its top left on her page, over the orb

# ------------------------------------------------------------ scripts --
# What the Peddler does between customers, as steps of (body frame, face,
# frames to hold) that npc.c plays one after another, an idle between:
# he spins his coin and slaps it flat, rubs his hands, drums his fingers.
# His blinks, his breath and a glance at the hero ride over them; the
# Gatekeeper's breath, blinks and kindled light are npc.c's own.
SPIN_TURN = [9, 7, 5, 3, -5, -7, -9, -7, -5, 3, 5, 7]


def _spin():
    steps = [('lift', 'down', 10)]
    for hold in (2, 2, 3, 4):          # four turns, slowing
        for w in SPIN_TURN:
            steps.append(('spin%d%s' % (abs(w), 'b' if w < 0 else ''), 'down', hold))
    return steps + [('slap', 'down', 14), ('slap', 'grin', 30)]


PEDDLER_ACTS = [
    _spin(),
    [('rub0', 'grin', 5), ('rub1', 'grin', 5)] * 8,
    [('tap', 'open', 5), ('tap2', 'open', 5)] * 6,
]
for _act in PEDDLER_ACTS:
    for (_b, _f, _t) in _act:
        assert _b in PEDDLER_BODY and _f in PEDDLER_HEAD and 0 < _t < 256, (_b, _f, _t)

SHEETS = [
    ('peddler_head', 'peddler', 64, 32, {k: f.rows(PEDDLER_PAL) for k, f in PEDDLER_HEAD.items()}),
    ('peddler_body', 'peddler', 64, 32, {k: f.rows(PEDDLER_PAL) for k, f in PEDDLER_BODY.items()}),
    ('gatekeeper', 'gatekeeper', 64, 64, {k: f.rows(GATEKEEPER_PAL) for k, f in GATEKEEPER.items()}),
    ('wisp', 'gatekeeper', 16, 16, {k: f.rows(GATEKEEPER_PAL) for k, f in WISP.items()}),
]
