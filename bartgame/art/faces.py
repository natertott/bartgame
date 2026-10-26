"""The dialogue box's faces: busts of 48x48 drawn by hand for each who
speaks, after their sprites in the game, lit from the upper left like
everything else and outlined in their darkest colour. Each has fifteen
colours of its own (the keepers' are their sprites' own palettes), loaded
into the portrait slot with the speaker.

A face is painted in parts: shapes filled through a shading rule (a ramp
of letters by how a pixel faces the light), then the features set by
hand as letter drawings, then the outline drawn round what is there.

    FACES       [(name, palette, rows)]: 48 rows of 48 letters, '.' clear
    PAL_*       the palettes, 15 colours by letter
"""
import math

import sw_folk as SF

W = H = 48
LIGHT = (-0.6, -0.8)  # from the upper left


class Face:
    def __init__(self, pal):
        self.pal = pal
        self.keys = {k for k, _ in pal}
        self.px = [['.'] * W for _ in range(H)]

    def put(self, x, y, k):
        if 0 <= x < W and 0 <= y < H and k != ' ':
            assert k == '.' or k in self.keys, k
            self.px[y][x] = k

    def get(self, x, y):
        return self.px[y][x] if 0 <= x < W and 0 <= y < H else '.'

    def ellipse(self, cx, cy, rx, ry, shade, rot=0.0):
        """fill an ellipse; shade(u, v, d, x, y) gives the letter, (u, v)
        the pixel in the ellipse's own frame (-1..1), d its distance out"""
        c, s = math.cos(rot), math.sin(rot)
        r = int(max(rx, ry)) + 2
        for y in range(int(cy) - r, int(cy) + r + 1):
            for x in range(int(cx) - r, int(cx) + r + 1):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                u = (dx * c + dy * s) / rx
                v = (-dx * s + dy * c) / ry
                d = math.hypot(u, v)
                if d <= 1.0:
                    k = shade(u, v, d, x, y)
                    if k:
                        self.put(x, y, k)

    def poly(self, pts, shade):
        """fill a polygon by the even-odd rule at pixel centres"""
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            yc = y + 0.5
            xs = []
            for i in range(len(pts)):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
                if (y0 <= yc < y1) or (y1 <= yc < y0):
                    xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(math.ceil(a - 0.5)), int(math.floor(b - 0.5)) + 1):
                    k = shade(x, y)
                    if k:
                        self.put(x, y, k)

    def line(self, x0, y0, x1, y1, k):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n):
            t = i / max(1, n - 1)
            self.put(int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)), k)

    def stamp(self, x, y, art):
        """a letter drawing set at (x, y); spaces leave what is there"""
        for j, row in enumerate(art.strip('\n').split('\n')):
            row = row.rstrip()
            pad = len(row) - len(row.lstrip(' '))
            for i, k in enumerate(row):
                if i >= pad and k != ' ':
                    self.put(x + i, y + j, k)

    def outline(self, k='o', keep=()):
        """the darkest colour round everything drawn: every clear pixel
        beside a drawn one, unless that one is of keep"""
        out = []
        for y in range(H):
            for x in range(W):
                if self.px[y][x] != '.':
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = self.get(x + dx, y + dy)
                    if n != '.' and n != k and n not in keep:
                        out.append((x, y))
                        break
        for x, y in out:
            self.px[y][x] = k

    def edge(self, inside, k, outside=None):
        """a line where a region of inside's letters meets anything else:
        drawn on the region's own edge pixels"""
        hit = []
        for y in range(H):
            for x in range(W):
                if self.px[y][x] not in inside:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = self.get(x + dx, y + dy)
                    if n not in inside and n != '.' and (outside is None or n in outside):
                        hit.append((x, y))
                        break
        for x, y in hit:
            self.px[y][x] = k

    def rows(self):
        return [''.join(r) for r in self.px]


def lit(u, v):
    """how much a point of a dome faces the light, -1..1"""
    z = math.sqrt(max(0.0, 1 - u * u - v * v))
    return (u * LIGHT[0] + v * LIGHT[1]) * 0.8 + z * 0.4 - 0.2


def ramp(letters, t):
    """a letter of a ramp, dark to light, for t in 0..1"""
    t = min(0.999, max(0.0, t))
    return letters[int(t * len(letters))]


# ------------------------------------------------------------ the Bloom --
PAL_BLOOM = [
    ('o', (32, 16, 16)),        # outline
    ('r', (136, 32, 32)),       # petal, deep: between the petals
    ('R', (216, 64, 48)),       # petal
    ('O', (248, 112, 56)),      # petal, lit
    ('P', (248, 168, 96)),      # petal, its gleam
    ('c', (200, 144, 104)),     # face, in shadow
    ('C', (240, 208, 152)),     # face
    ('W', (248, 240, 216)),     # face, its gleam; the eyes' light
    ('k', (40, 24, 32)),        # the eyes
    ('p', (232, 120, 112)),     # blush
    ('d', (40, 72, 24)),        # green, deep
    ('g', (88, 128, 32)),       # green
    ('G', (152, 184, 56)),      # green, lit
    ('b', (104, 64, 32)),       # bark brown
    ('y', (232, 176, 56)),      # the buckle's gold
]


def bloom_surprised():
    f = Face(PAL_BLOOM)
    cx, cy = 24, 21
    # the body: a green tunic, shoulders at the foot, a leaf at the left
    f.ellipse(24, 52, 17, 14, lambda u, v, d, x, y: ramp('dgG', 0.45 + lit(u, v) * 0.6) if d < 0.93 else 'd')
    f.ellipse(8, 41, 7, 4, lambda u, v, d, x, y: 'd' if d > 0.85 or abs(v) < 0.12 else ('G' if v < 0 else 'g'), rot=-0.6)
    f.ellipse(41, 42, 6, 3.5, lambda u, v, d, x, y: 'g' if d < 0.8 else 'd', rot=0.5)
    # the petals, seven, back to front
    def petal(ang, dist, rx, ry):
        a = math.radians(ang)
        px, py = cx + math.cos(a) * dist, cy + math.sin(a) * dist

        def sh(u, v, d, x, y):
            # u runs out from the face, v across
            if d > 0.84:
                return 'r'
            if u < -0.55:
                return 'r'
            t = lit(u * math.cos(a) - v * math.sin(a), u * math.sin(a) + v * math.cos(a))
            if t > 0.55 and d < 0.62:
                return 'P'
            if t < -0.15 or d > 0.72:
                return 'R'
            return 'O'
        f.ellipse(px, py, rx, ry, sh, rot=a)
    for ang in (-90, -138, -42, 180, 0, 132, 48):
        petal(ang, 15.5 if ang in (-90,) else 15, 8.6, 7.4)
    # the face: cream, its gleam high at the left, shade at the lower right
    def face(u, v, d, x, y):
        t = lit(u, v)
        if d > 0.9:
            return 'c' if t < 0.4 else 'C'
        if t > 0.75 and d < 0.7:
            return 'W'
        return 'C' if t > -0.25 else 'c'
    f.ellipse(cx, cy, 10.5, 10, face)
    f.edge(set('cCW'), 'o', outside=set('rROP'))
    # surprised: round eyes with their light, the mouth an o, the cheeks hot
    f.stamp(cx - 6, cy - 4, '''
 kk
kWkk
kkkk
kkkk
 kk
''')
    f.stamp(cx + 2, cy - 4, '''
 kk
kWkk
kkkk
kkkk
 kk
''')
    f.stamp(cx - 9, cy + 3, 'pp')
    f.stamp(cx + 7, cy + 3, 'pp')
    f.stamp(cx - 2, cy + 4, '''
 rr
r kr
 rr
''')
    f.put(cx - 1, cy + 5, 'k')
    f.put(cx, cy + 5, 'k')
    # the tunic's collar and its buckle
    f.stamp(18, 39, '''
dgGGGggggGGGd
 dgggggggggd
''')
    f.stamp(22, 43, '''
oyyyo
oybyo
oyyyo
''')
    f.outline('o')
    return f.rows()


# ----------------------------------------------------------- the Peddler --
# his sprite's own palette: the starred purple hood, lilac skin, the long
# pink nose, the gold of his chain and the red of its gem
PAL_PEDDLER = SF.PEDDLER_PAL


def peddler():
    f = Face(PAL_PEDDLER)
    # the robe's shoulders and the collar of the hood falling on them
    f.ellipse(22, 55, 24, 17, lambda u, v, d, x, y: ramp('1234', 0.35 + lit(u, v) * 0.55))

    # the hood: a great dome over the head, its tip curled back to the left
    def hood(u, v, d, x, y):
        t = lit(u, v)
        if d > 0.9:
            return '1' if t < 0.2 else '2'
        return ramp('1234', 0.42 + t * 0.6)
    f.ellipse(19, 19, 16.5, 16, hood)
    f.poly([(7, 9), (2, 2), (4, 1), (9, 3), (14, 6)], lambda x, y: '3' if y < 4 else '2')
    f.put(2, 2, '4')
    f.put(3, 1, '4')
    # the ear, long and pink, hanging below the hood at the back
    f.poly([(13, 26), (5, 36), (7, 37), (16, 30)], lambda x, y: 'N' if x > 9 else 'n')
    f.line(12, 28, 7, 35, 'M')

    # the hood's opening: the face in its shadow, turned to the right
    def face(u, v, d, x, y):
        t = lit(u, v)
        if v < -0.5 or u < -0.6:
            return 's'
        return ramp('sSL', 0.45 + t * 0.7)
    f.ellipse(30, 23, 9, 10.5, face)
    # the hood's rim over the brow and down the back of the face
    f.poly([(19, 9), (35, 10), (39, 14), (34, 13), (28, 14), (24, 17), (22, 26), (20, 33), (17, 24)],
           lambda x, y: '1' if y > 13 or x < 22 else '2')
    # the nose: long, hooked, drooping to the right, lit along its ridge
    f.poly([(34, 18), (38, 18), (42, 22), (45, 28), (46, 33), (44, 35), (42, 32), (40, 27), (36, 24)],
           lambda x, y: 'n' if (x - 36) * 0.9 > (y - 18) * 1.1 + 1 else 'N')
    f.line(35, 18, 38, 18, 'M')
    f.line(39, 19, 42, 22, 'M')
    f.line(43, 24, 44, 28, 'M')
    # the eye: gold, its pupil, under a heavy lid; the grin with a tooth
    f.stamp(29, 15, '''
ooooo
 oGGoGo
 oGGoGo
  oooo
''')
    f.stamp(27, 14, 'o')
    f.stamp(30, 28, '''
oo
 ooooo
  oLLo
''')
    f.stamp(30, 32, '''
SSss
 sss
''')
    f.put(28, 23, 'L')
    # the stars on the hood
    for x, y in ((8, 12), (14, 6), (21, 4), (27, 7), (6, 21), (11, 17), (14, 24), (4, 14), (18, 13)):
        f.put(x, y, 'G')
    # the chain and its gem
    f.line(10, 38, 22, 44, 'Y')
    f.line(36, 38, 26, 44, 'Y')
    for x, y in ((12, 39), (16, 41), (20, 43), (34, 39), (30, 41)):
        f.put(x, y, 'G')
    f.stamp(21, 43, '''
 oyyo
oYGGYo
oYrrYo
oyrryo
 oyyo
''')
    f.outline('o')
    return f.rows()


# -------------------------------------------------------- the Gatekeeper --
# her sprite's own palette: the purple hat and robe, the gold, her pale
# face and white hair, her red eyes, the orb's violet glow
PAL_GATEKEEPER = SF.GATEKEEPER_PAL


def gatekeeper():
    f = Face(PAL_GATEKEEPER)
    # the staff at the right, its orb burning over her shoulder
    f.line(41, 15, 41, 47, 'Y')
    f.line(42, 15, 42, 47, 'y')
    for y in (22, 30, 38, 46):
        f.put(41, y, 'G')
    f.stamp(39, 13, '''
oYYYo
 oYo
''')

    def orb(u, v, d, x, y):
        if d < 0.35 and u < 0.1 and v < 0.1:
            return 'W'
        return 'V' if lit(u, v) > 0.15 else 'v'
    f.ellipse(41.5, 9.5, 4.6, 4.6, orb)
    # the robe's shoulders, a gold hem along the collar
    f.ellipse(21, 54, 21, 15, lambda u, v, d, x, y: ramp('1234', 0.3 + lit(u, v) * 0.6))
    f.line(10, 42, 21, 47, 'Y')
    f.line(32, 42, 22, 47, 'Y')
    # her hair, long and white, falling past her face to the shoulders
    f.poly([(9, 22), (35, 22), (37, 34), (34, 45), (29, 46), (28, 30), (16, 30), (14, 46), (8, 44), (6, 32)],
           lambda x, y: 'W' if (x < 12 and y < 36) else ('S' if x < 30 else 's'))
    for x0 in (9, 12, 31, 34):
        f.line(x0, 26, x0 - 1, 44, 's')

    # the face, pale and long, the brim's shadow across the brow, the jaw
    # narrowing to a sharp chin
    def face(x, y):
        if y < 26:
            return 'k'
        if x < 20:
            return 'S'
        if x > 25 or y > 35:
            return 'k' if (x > 26 or y > 36) else 's'
        return 's'
    f.poly([(15, 23), (29, 23), (29, 32), (26, 37), (23, 39), (21, 39), (18, 37), (15, 32)], face)
    # the face's edge against her hair
    for (x0, y0, x1, y1) in ((14, 24, 14, 32), (14, 32, 18, 38), (18, 38, 21, 40), (30, 24, 30, 32),
                             (30, 32, 27, 37), (27, 37, 23, 40)):
        f.line(x0, y0, x1, y1, 'k')
    f.line(16, 33, 19, 37, 's')
    # the eyes, red in dark sockets; the long nose; the thin mouth
    f.stamp(16, 27, '''
kkrrk kkrrk
 kkk   kkk
''')
    f.put(18, 27, 'W')
    f.line(22, 28, 22, 33, 'W')
    f.line(23, 29, 23, 34, 'k')
    f.put(21, 34, 'k')
    f.stamp(19, 36, 'okkko')
    # the hat: its crown rising to a tip bent to the right, a gold band
    def crown(x, y):
        t = (x - 22) / 14.0 + (y - 18) / 30.0
        return ramp('4321', 0.35 + t * 0.7)
    f.poly([(9, 19), (35, 19), (30, 11), (29, 5), (31, 2), (36, 0), (33, 0), (27, 2), (23, 7), (17, 13)], crown)
    f.poly([(9, 16), (35, 16), (35, 19), (9, 19)], lambda x, y: 'G' if y == 16 else ('Y' if y == 17 else 'y'))
    # the brim, wide and dipping at the front
    def brim(u, v, d, x, y):
        if v > 0.35:
            return '1'
        return '3' if u < -0.2 else '2'
    f.ellipse(22, 21, 21, 3.6, brim)
    # stars on the crown
    for x, y in ((20, 13), (27, 9), (24, 4)):
        f.put(x, y, 'G')
    f.outline('o')
    return f.rows()


# ------------------------------------------------------ the Hermit Knight --
PAL_HERMIT = [
    ('o', (24, 16, 16)),        # outline
    ('k', (160, 104, 88)),      # skin, in shadow
    ('s', (216, 160, 128)),     # skin
    ('S', (240, 208, 168)),     # skin, lit
    ('w', (144, 136, 128)),     # beard, in shadow
    ('W', (208, 200, 184)),     # beard
    ('H', (240, 236, 224)),     # beard, lit
    ('e', (48, 32, 24)),        # the eyes, the mouth
    ('a', (56, 48, 48)),        # armour, dark
    ('A', (96, 88, 88)),        # armour
    ('B', (152, 144, 136)),     # armour, lit
    ('u', (136, 72, 32)),       # rust
    ('U', (192, 112, 48)),      # rust, lit
    ('m', (72, 96, 40)),        # moss
    ('M', (120, 144, 56)),      # moss, lit
]


def hermit():
    f = Face(PAL_HERMIT)

    # the armour's shoulders, rusted at the rims, moss on the left one
    def plate(u, v, d, x, y):
        if d > 0.86:
            return 'u' if lit(u, v) < 0.2 else 'U'
        return ramp('aAB', 0.35 + lit(u, v) * 0.7)
    f.ellipse(8, 44, 11, 9, plate)
    f.ellipse(38, 44, 11, 9, plate)
    f.ellipse(23, 50, 15, 10, lambda u, v, d, x, y: ramp('aA', 0.4 + lit(u, v) * 0.6))
    for x, y in ((3, 39), (5, 38), (7, 37), (2, 41), (9, 37), (4, 40)):
        f.put(x, y, 'm')
    for x, y in ((4, 38), (6, 37), (8, 36)):
        f.put(x, y, 'M')
    for x, y in ((35, 39), (40, 37), (44, 40)):
        f.put(x, y, 'U')

    # the head: bald, lit high on the left, the ears out at the sides
    def head(u, v, d, x, y):
        t = lit(u, v)
        if t > 0.7 and d < 0.6:
            return 'S'
        return ramp('ksS', 0.4 + t * 0.7)
    f.ellipse(9.5, 19, 2.5, 3.5, lambda u, v, d, x, y: 'k' if u > 0.2 else 's')
    f.ellipse(34.5, 19, 2.5, 3.5, lambda u, v, d, x, y: 'k')
    f.ellipse(22, 16, 12, 13, head)

    # the beard: long and white, from the cheeks to the foot, in strands
    def beard(x, y):
        t = (x - 22) / 12.0
        k = 'H' if t < -0.45 else ('W' if t < 0.35 else 'w')
        if (x + y // 3) % 5 == 0 and y > 26:
            k = 'w' if k != 'w' else 'W'
        return k
    f.poly([(11, 20), (33, 20), (34, 28), (31, 38), (27, 46), (24, 48), (19, 48), (15, 44), (11, 34), (10, 26)], beard)
    # the face above it: cheeks, the nose, the eyes deep under the brows
    f.poly([(14, 17), (30, 17), (30, 23), (27, 26), (17, 26), (14, 23)],
           lambda x, y: 'S' if x < 18 else ('s' if x < 27 else 'k'))
    f.stamp(13, 14, '''
 HHHWw      wWWW
HWWWWww    wwWWWw
''')
    f.stamp(16, 17, '''
 oek      keo
  k        k
''')
    f.put(17, 17, 'H')
    f.put(27, 17, 'H')
    f.stamp(20, 19, '''
 sSs
 sSSs
ksSSsk
 kkkk
''')
    # the moustache over the mouth, falling into the beard
    f.stamp(16, 25, '''
 wWHHHHWWw
wWWw  wWWw
WWw    wWW
''')
    f.stamp(21, 27, 'ekke')
    # lines on the pate
    f.line(17, 9, 21, 8, 'k')
    f.line(19, 11, 24, 10, 's')
    f.outline('o')
    return f.rows()


# ------------------------------------------------------- the Weeping Nun --
PAL_NUN = [
    ('o', (24, 16, 32)),        # outline
    ('1', (40, 32, 56)),        # the veil, dark
    ('2', (64, 56, 88)),        # the veil
    ('3', (96, 88, 128)),       # the veil, lit
    ('w', (176, 168, 168)),     # the wimple, in shadow
    ('W', (224, 216, 208)),     # the wimple
    ('H', (248, 248, 240)),     # the wimple, lit
    ('k', (184, 136, 112)),     # skin, in shadow
    ('s', (224, 184, 152)),     # skin
    ('S', (248, 216, 184)),     # skin, lit
    ('e', (72, 40, 40)),        # the lashes
    ('t', (136, 192, 232)),     # a tear
    ('p', (192, 104, 96)),      # the lips
    ('y', (160, 104, 32)),      # gold, dark
    ('Y', (232, 184, 72)),      # gold
]


def nun():
    f = Face(PAL_NUN)
    # the veil: dark, over the head and falling wide to the shoulders
    def veil(x, y):
        t = (x - 24) / 18.0 + (y - 20) / 40.0
        return ramp('321', 0.3 + t * 0.7)
    f.poly([(15, 2), (33, 2), (40, 8), (43, 22), (46, 47), (2, 47), (5, 22), (8, 8)], veil)
    f.line(9, 9, 6, 22, '3')
    f.line(6, 23, 4, 40, '3')

    # the wimple: white, round the face and down over the breast
    def wimple(u, v, d, x, y):
        t = lit(u, v)
        return 'H' if t > 0.45 else ('W' if t > -0.3 else 'w')
    f.ellipse(24, 21, 12.5, 14, wimple)
    f.poly([(12, 28), (36, 28), (39, 47), (9, 47)], lambda x, y: 'W' if x < 21 else ('w' if x > 30 else 'W'))
    f.line(13, 30, 11, 46, 'H')
    # the band over the brow, a gold cross set in it
    f.poly([(14, 8), (34, 8), (35, 11), (13, 11)], lambda x, y: 'w' if y == 11 else 'W')
    f.stamp(23, 7, '''
 Y
YYY
 y
''')

    # the face, bowed a little, the eyes shut and wet
    def face(u, v, d, x, y):
        t = lit(u, v)
        return 'S' if t > 0.35 else ('s' if t > -0.35 else 'k')
    f.ellipse(24, 22, 8, 9.5, face)
    f.stamp(18, 20, '''
 eee    eee
e  e    e  e
''')
    f.stamp(19, 22, 't')
    f.stamp(19, 24, 't')
    f.put(20, 23, 't')
    f.stamp(23, 22, '''
 k
 sk
''')
    f.stamp(22, 27, 'kppk')
    # her hands, pressed together before her
    def hands(x, y):
        return 'S' if x < 24 else ('s' if x < 26 else 'k')
    f.poly([(23, 31), (26, 31), (28, 38), (29, 47), (19, 47), (20, 38)], hands)
    f.line(24, 32, 24, 46, 'k')
    f.line(20, 41, 28, 41, 's')
    f.outline('o')
    return f.rows()


# ---------------------------------------------------- the Blind Gardener --
PAL_GARDENER = [
    ('o', (24, 24, 16)),        # outline
    ('1', (40, 64, 24)),        # the hood, dark
    ('2', (72, 104, 40)),       # the hood
    ('3', (120, 152, 56)),      # the hood, lit
    ('k', (152, 96, 64)),       # skin, in shadow
    ('s', (208, 152, 112)),     # skin
    ('S', (240, 192, 152)),     # skin, lit
    ('w', (160, 152, 144)),     # beard, in shadow
    ('W', (224, 216, 200)),     # beard
    ('e', (168, 192, 208)),     # the eyes, milky
    ('b', (104, 64, 32)),       # the staff
    ('B', (160, 104, 56)),      # the staff, lit
    ('f', (224, 96, 128)),      # a flower
    ('F', (248, 184, 200)),     # a flower, lit
    ('y', (240, 200, 72)),      # its heart
]


def gardener():
    f = Face(PAL_GARDENER)
    # his staff at the right, a knot of root at its head
    f.line(41, 10, 41, 47, 'b')
    f.line(42, 10, 42, 47, 'B')
    f.stamp(38, 5, '''
 bBBb
bBbbBb
 bBBb
  bb
''')

    # the cloak's shoulders and the hood: green, pointed, falling wide
    def cloth(x, y):
        t = (x - 22) / 18.0 + (y - 20) / 40.0
        return ramp('321', 0.3 + t * 0.75)
    f.poly([(19, 1), (26, 3), (33, 9), (37, 20), (40, 34), (45, 47), (1, 47), (5, 34), (8, 18), (13, 7)], cloth)
    f.line(12, 8, 7, 20, '3')
    f.line(7, 21, 4, 34, '3')
    # its folds, and the shadow inside its mouth round the face
    f.line(30, 26, 36, 46, '1')
    f.line(12, 30, 9, 46, '2')
    f.line(18, 34, 16, 46, '1')
    f.ellipse(23, 22, 11, 12.5, lambda u, v, d, x, y: '1')

    # the face in the hood's mouth: weathered, the eyes milky and blind
    def face(u, v, d, x, y):
        t = lit(u, v)
        return 'S' if t > 0.35 else ('s' if t > -0.35 else 'k')
    f.ellipse(23, 21, 8.5, 9, face)
    f.poly([(13, 13), (33, 13), (31, 16), (15, 16)], lambda x, y: '1')
    f.stamp(16, 16, '''
WWWw   wWWW
 kek   kek
''')
    f.put(17, 17, 'e')
    f.put(18, 17, 'W')
    f.put(26, 17, 'e')
    f.put(27, 17, 'W')
    f.stamp(21, 18, '''
 sS
 sSs
ksSsk
''')

    # the beard: white, round and short, the moustache over it
    def beard(u, v, d, x, y):
        t = lit(u, v)
        k = 'W' if t > -0.2 else 'w'
        if (x * 3 + y) % 7 == 0:
            k = 'w'
        return k
    f.ellipse(23, 31, 9.5, 7.5, beard)
    f.stamp(17, 23, '''
 wWWWwWWWw
wWw     wWw
''')
    f.stamp(21, 25, 'kook')
    # a flower and its leaves tucked into the hood, another at the breast
    f.stamp(9, 8, '''
  ff
 fFFf
fFyyFf
 fFFf  33
  ff  3
''')
    # a vine of leaves over the hood
    for x, y, k in ((14, 5, '3'), (16, 4, '2'), (6, 16, '3'), (5, 18, '2'), (4, 24, '3'), (6, 26, '2'),
                    (34, 14, '3'), (36, 18, '2'), (37, 24, '3')):
        f.put(x, y, k)
        f.put(x + 1, y, '1')
    f.stamp(30, 37, '''
 ff
fFyf
 ff
''')
    f.outline('o')
    return f.rows()


FACES = [
    ('bloom_surprised', PAL_BLOOM, bloom_surprised()),
    ('peddler', PAL_PEDDLER, peddler()),
    ('gatekeeper', PAL_GATEKEEPER, gatekeeper()),
    ('hermit', PAL_HERMIT, hermit()),
    ('nun', PAL_NUN, nun()),
    ('gardener', PAL_GARDENER, gardener()),
]
