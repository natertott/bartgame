"""The Drain's hall, painted whole at native resolution and cut into
metatiles (see sw_paint.py for the tools and colours).

The hall is 30x20 metatiles. Its rows, top to bottom:

    0-3    the back wall: brick, brass pipes, the barred arch the falls
           pour from, the drain hole up to the wood, banners, lanterns
    4-8    the upper floor: the Peddler's stall, the basin under the
           falls, the Gatekeeper's corner
    9      the channel's near bank, railed
    10-11  the channel
    12     its far bank, railed
    13-16  the lower floor: the great drain, where a run begins
    17     the floor's front edge, railed, its face dropping to the water
    18-19  the water below, pipes pouring into it

It is painted as two layers, ground (under the sprites) and overlay
(over them), at every tick of the animation clock, then cut into 16x16
cells (sw_cut.py): identical cells share a metatile, and the colours are
packed into the area's 13 palettes.
"""
import math

from sw_paint import Canvas, Path, tube, sprite, shift, rnd, dither, ellipse_px

W, H = 30, 20
PW, PH = W * 16, H * 16
WALL_Y1 = 64            # the back wall's foot; the floor begins
NB_COPE = 154           # the near bank's coping (6 px)
NB_FACE = 160           # its face, dropping into the channel (7 px)
CH_W0, CH_W1 = 167, 192  # the channel's water
SB_COPE = 192           # the far bank's coping
FE_COPE = 272           # the lower floor's front edge
FE_FACE = 278           # its face (10 px)
BW_Y0 = 288             # the water below
SIDE = 16               # the side walls
CX = PW // 2            # the hall's middle: the falls, the bridge, the drain

# the clock: a tick is 4 frames; everything loops in 24 ticks
TICKS = 24


# ---------------------------------------------------------- flagstones --
def _ashlar(pw, ph, heights, wmin, wmax, salt):
    """courses of stones on a pw x ph torus: rects (x, y, w, h)"""
    stones = []
    y = 0
    for ci, h in enumerate(heights):
        widths = []
        k = 0
        while sum(widths) < pw:
            widths.append(int(wmin + rnd(ci, k, salt) * (wmax - wmin + 1)))
            k += 1
        widths[-1] -= sum(widths) - pw
        if widths[-1] < wmin:
            widths[-2] += widths[-1]
            widths.pop()
        x = int(rnd(ci, 99, salt) * pw)
        for wdt in widths:
            stones.append((x % pw, y, wdt, h))
            x += wdt
        y += h
    assert y == ph
    return stones


def _random_ashlar(pw, ph, ux, uy, wmin, wmax, p_double, salt):
    """random paving on a pw x ph torus, course by course: stones of wmin to
    wmax units of ux wide, one course of uy tall or now and then two, laid
    so that no gap narrower than wmin is ever left"""
    cols, rows = pw // ux, ph // uy
    pre = [set() for _ in range(rows)]   # units a stone from the course above holds
    stones = []
    for j in range(rows):
        held = pre[j]
        start = min(held) if held else 0
        runs = []
        i = 0
        while i < cols:
            if (start + i) % cols in held:
                i += 1
                continue
            k = i
            while k < cols and (start + k) % cols not in held:
                k += 1
            runs.append(((start + i) % cols, k - i))
            i = k
        for (u0, L) in runs:
            assert L >= wmin, ('a gap too narrow for a stone', j, L)
            x = 0
            n = 0
            while x < L:
                left = L - x
                if left <= wmax and (left < 2 * wmin or rnd(j, u0 + n, salt + 5) < 0.3):
                    w = left
                else:
                    hi = min(wmax, left - wmin)
                    w = wmin + int(rnd(j * 31 + n, u0, salt) * (hi - wmin + 1))
                ux0 = (u0 + x) % cols
                h = 1
                if j + 1 < rows and rnd(j, ux0, salt + 9) < p_double:
                    span = {(ux0 + a) % cols for a in range(w)}
                    if not (span & pre[j + 1]) and _gaps_ok(pre[j + 1] | span, cols, wmin):
                        pre[j + 1] |= span
                        h = 2
                stones.append((ux0 * ux, j * uy, w * ux, h * uy))
                x += w
                n += 1
    return stones


def _gaps_ok(held, cols, wmin):
    """every free run of a course left by held units is wide enough"""
    if not held:
        return True
    start = min(held)
    i = 0
    while i < cols:
        if (start + i) % cols in held:
            i += 1
            continue
        k = i
        while k < cols and (start + k) % cols not in held:
            k += 1
        if k - i < wmin:
            return False
        i = k
    return True


class Stones:
    """a periodic field of stones: which stone is at a pixel, and where in it"""

    def __init__(self, pw, ph, rects):
        self.pw, self.ph = pw, ph
        self.rects = rects
        self.at = [[None] * pw for _ in range(ph)]
        for i, (x0, y0, w, h) in enumerate(rects):
            for yy in range(y0, y0 + h):
                for xx in range(x0, x0 + w):
                    self.at[yy % ph][xx % pw] = (i, xx - x0, yy - y0)
        assert all(all(c is not None for c in row) for row in self.at)

    def info(self, x, y):
        i, u, v = self.at[y % self.ph][x % self.pw]
        _, _, w, h = self.rects[i]
        return i, u, v, w, h


# the floor: 96 x 80, courses of 10, stones 12 to 28 wide, a slab of two
# courses now and then; the wall: courses of 8, bricks 14 to 20
FLOOR = Stones(96, 80, _random_ashlar(96, 80, 4, 10, 3, 7, 0.28, 7))
BRICK = Stones(48, 64, _ashlar(48, 64, [8] * 8, 13, 19, 21))


def _blotch(i, u, v, w, h, salt):
    """a soft worn patch in a stone, clear of its edges"""
    cx = 2 + rnd(i, 1, salt) * max(1, w - 6)
    cy = 2 + rnd(i, 2, salt) * max(1, h - 5)
    rx = 1.6 + rnd(i, 3, salt) * 2.2
    ry = 1.0 + rnd(i, 4, salt) * 1.0
    dx, dy = (u + 0.5 - cx) / rx, (v + 0.5 - cy) / ry
    return dx * dx + dy * dy <= 1.0


def floor_px(x, y):
    """the flagstone floor's colour at a hall pixel"""
    i, u, v, w, h = FLOOR.info(x, y)
    if u == w - 1 or v == h - 1:
        j = FLOOR.info(x + 1, y + 1)[0]
        return 'g0' if (u == w - 1 and v == h - 1) or j != FLOOR.info(x + 1, y)[0] else 'g1'
    base = 'g3'
    # a crack across a few stones: a dark jagged line from the top edge
    # most of the way down, lit along its left
    if rnd(i, 50, 51) < 0.09 and w > 10 and h > 8:
        x0 = 3 + int(rnd(i, 52, 53) * (w - 8))
        lean = 1 if rnd(i, 54, 55) < 0.5 else -1
        for k in range(h - 3):
            cx = x0 + lean * ((k + 1) // 3) + (1 if (k % 5 == 3) else 0)
            if (u, v) == (cx, k):
                return 'g1'
            if (u, v) == (cx - 1, k) and k % 3 == 1:
                return 'g4'
    if u == w - 2 and v == h - 2:
        return 'g1'
    if u == 0 and v == 0 and rnd(i, 9, 39) < 0.3:
        return 'g1'
    if v == 0 and u < w - 2:
        return shift(base, 1)
    if u == 0 and v < (h - 1) * 0.6:
        return shift(base, 1)
    if v == h - 2:
        return shift(base, -1)
    if u == w - 2 and v > h * 0.45:
        return shift(base, -1)
    if _blotch(i, u, v, w, h, 40) and rnd(i, 5, 41) < 0.65:
        return shift(base, 1)
    for k in range(1 + int(rnd(i, 2, 33) * 2)):
        px, py = 2 + int(rnd(i, 10 + k, 34) * (w - 5)), 2 + int(rnd(i, 20 + k, 35) * (h - 5))
        if (u, v) == (px, py) or ((u, v) == (px + 1, py) and rnd(i, 30 + k, 36) < 0.5):
            return shift(base, -1)
    return base


def _mossy_joint(x, y):
    """is this joint pixel grown over: a few joints of the pattern, by
    stone, thick where two joints meet"""
    i, u, v, w, h = FLOOR.info(x, y)
    # the joint belongs to the stone to its left or above
    return rnd(i, 70, 71) < 0.22


def moss_px(x, y, base):
    """the floor with the pattern's own moss: in the grown joints, the
    mortar is moss, and a pixel or two creeps onto the stone beside"""
    i, u, v, w, h = FLOOR.info(x, y)
    if (u == w - 1 or v == h - 1) and _mossy_joint(x, y):
        k = rnd(x % 96, y % 80, 72)
        return 'm1' if k < 0.45 else ('m2' if k < 0.85 else 'm3')
    # creeping onto the stone: next to a grown joint, now and then
    for (dx, dy) in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        j, uu, vv, ww, hh = FLOOR.info(x + dx, y + dy)
        if (uu == ww - 1 or vv == hh - 1) and j != i and _mossy_joint(x + dx, y + dy):
            if rnd(x % 96, y % 80, 73) < 0.3:
                return 'm2' if rnd(x % 96, y % 80, 74) < 0.6 else 'm1'
    return base


def brick_px(x, y):
    """the back wall's brick at a hall pixel"""
    i, u, v, w, h = BRICK.info(x, y)
    if u == w - 1 or v == h - 1:
        return 'g0' if (u == w - 1 and v == h - 1) or rnd(x % 48, y % 64, 41) < 0.25 else 'g1'
    r = rnd(i, 0, 42)
    base = 'g2' if r < 0.72 else ('g1' if r < 0.86 else 'g3')
    if v == 0 and u < w - 2:
        return shift(base, 1)
    if v == h - 2:
        return shift(base, -1)
    if u == 0 and v < h - 3 and rnd(i, 1, 43) < 0.6:
        return shift(base, 1)
    if rnd(i, 2, 44) < 0.55:
        px, py = 2 + int(rnd(i, 3, 45) * (w - 5)), 2 + int(rnd(i, 4, 46) * 3)
        if (u, v) in ((px, py), (px + 1, py)):
            return shift(base, -1)
    return base


def ring(period, wmin, wmax, salt):
    """block widths round a ring of the period: (start, width) pairs"""
    widths = []
    k = 0
    while sum(widths) < period:
        widths.append(wmin + int(rnd(k, 0, salt) * (wmax - wmin + 1)))
        k += 1
    widths[-1] -= sum(widths) - period
    if widths[-1] < wmin:
        widths[-2] += widths[-1]
        widths.pop()
    out, x = [], 0
    for w in widths:
        out.append((x, w))
        x += w
    return out


def ring_at(blocks, period, x):
    """the block a pixel falls in: (index, offset, width)"""
    xx = x % period
    for i, (x0, w) in enumerate(blocks):
        if x0 <= xx < x0 + w:
            return i, xx - x0, w
    raise AssertionError(x)


# ------------------------------------------------------------ the bones --
def paint_floor(g):
    for y in range(WALL_Y1, PH):
        for x in range(PW):
            g.px[y][x] = moss_px(x, y, floor_px(x, y))


def paint_back_wall(g):
    for y in range(WALL_Y1):
        for x in range(PW):
            c = brick_px(x, y)
            if y < 10:
                c = shift(c, -1)    # the vault: darker toward the top
            if y < 3:
                c = shift(c, -1)
            g.px[y][x] = c
    # a plinth course: big dressed blocks, a lit top edge
    y0 = WALL_Y1 - 7
    blocks = ring(96, 22, 34, 51)
    for yy in range(y0, WALL_Y1):
        for xx in range(PW):
            k, u, wdt = ring_at(blocks, 96, xx)
            v = yy - y0
            if u == wdt - 1:
                c = 'g0'
            elif v == 0:
                c = 'g4'
            elif v == 1:
                c = 'g3'
            elif v == 6:
                c = 'g1'
            else:
                c = 'g3' if rnd(xx % 96, yy, 52) > 0.08 else 'g2'
            g.px[yy][xx] = c
    # the wall's foot throws a shadow on the floor
    for x in range(PW):
        g.px[WALL_Y1][x] = 'g0'
        g.px[WALL_Y1 + 1][x] = 'g1'
        if not dither(x, WALL_Y1 + 2, 0.5):
            g.px[WALL_Y1 + 2][x] = shift(g.px[WALL_Y1 + 2][x], -1)


def coping(g, y0, x0, x1, salt, period=96):
    """a bank's edge: a course of long dressed stones, lit along the top"""
    blocks = ring(period, 20, 34, salt)
    for yy in range(y0, y0 + 6):
        for xx in range(x0, x1):
            k, u, wdt = ring_at(blocks, period, xx)
            chip = int(rnd(k, 1, salt) * (wdt - 6)) + 3
            v = yy - y0
            if u == wdt - 1:
                c = 'g1'
            elif v == 0:
                c = 'g6' if 0 < u < wdt - 2 else 'g5'
            elif v == 1:
                c = 'g5'
            elif v == 5:
                c = 'g3'
            elif v == 4:
                c = 'g3' if u >= wdt - 3 else 'g4'
            else:
                c = 'g4'
            if v == 0 and u in (chip, chip + 1):
                c = 'g4'
            g.px[yy][xx] = c


def bank_face(g, y0, h, x0, x1, salt, period=32):
    """a bank's face, dropping into the water: wet dark blocks"""
    blocks = ring(period, 10, 18, salt)
    for yy in range(y0, y0 + h):
        for xx in range(x0, x1):
            k, u, wdt = ring_at(blocks, period, xx)
            v = yy - y0
            if u == wdt - 1 or v == h - 1:
                c = 'g0'
            elif v == 0:
                c = 'g3'
            elif u == 0:
                c = 'g3' if v < h - 3 else 'g2'
            else:
                c = 'g2' if rnd(xx % period, yy, salt + 1) > 0.12 else 'g1'
            g.px[yy][xx] = c


def paint_banks(g):
    coping(g, NB_COPE, 0, PW, 61)
    bank_face(g, NB_FACE, 7, 0, PW, 62)
    coping(g, SB_COPE, 0, PW, 63)
    coping(g, FE_COPE, 0, PW, 64)
    bank_face(g, FE_FACE, 10, 0, PW, 65)


def side_wall_px(x, y, inner):
    """a side wall's top, seen from above: big dark blocks, a lit lip"""
    d = (SIDE - 1 - x) if inner == 1 else (x - (PW - SIDE))
    if d == 0:
        return 'g4'
    if d == 1:
        return 'g3'
    return shift(brick_px(x + 7, y + 3), -1)


def paint_side_walls(g):
    """the side walls: the left drawn, the right its mirror (so the
    hardware's flips draw both from the one set of pieces)"""
    x0, inner = 0, 1
    for y in range(PH):
        for i in range(SIDE):
            g.px[y][x0 + i] = side_wall_px(x0 + i, y, inner)
    # the culverts the channel and the pool run through
    for (y0, y1) in ((NB_FACE, CH_W1), (FE_FACE, PH)):
        for y in range(y0 - 6, y1):
            for i in range(SIDE):
                d = SIDE - 1 - i
                if y < y0:
                    g.px[y][i] = 'g4' if y == y0 - 6 else ('g5' if y == y0 - 5 else 'g3')
                elif d < 2:
                    g.px[y][i] = 'g1'
                else:
                    g.px[y][i] = 'g0' if rnd(i, y, 66) > 0.12 else 'a1'
    # a brass pipe down each side wall, riveted to it, broken by the
    # culverts' arches
    for (y0, y1) in ((-6, NB_FACE - 6), (SB_COPE + 6, FE_FACE - 6)):
        pipe(g, [(7, y0), (7, y1 + 2)], 8, 4)
        for y in range(y0 + 20, y1 - 4, 32):
            collar(g, 7, y, 8)
        for (yy) in (y1 - 3, y1 - 2, y1 - 1, y1):
            for x in range(1, 14):
                g.put(x, yy, 'b4' if yy == y1 - 3 else ('b3' if yy < y1 else 'b1'))
        g.put(1, y1 - 3, 'b5')
    for y in range(PH):
        for i in range(SIDE):
            g.px[y][PW - 1 - i] = g.px[y][i]
    # the shadow each throws on the floor
    for sx in (SIDE, PW - SIDE - 1):
        for y in range(WALL_Y1, PH):
            c = g.px[y][sx]
            if c and c[0] == 'g':
                g.px[y][sx] = shift(c, -1)


# ---------------------------------------------------------------- pipes --
BRASS = ['b1', 'b2', 'b3', 'b4', 'b5']


def pipe(g, pts, width=10, r=7):
    tube(g, Path(pts, r), width, 'b', 'g0', BRASS)


def collar(g, x, y, width, vertical=True):
    """a band round a pipe: wider than it, riveted"""
    if vertical:
        x0 = x - width // 2 - 1
        for yy in range(y, y + 3):
            for xx in range(x0, x0 + width + 2):
                u = xx - x0
                if u in (0, width + 1):
                    c = 'g0'
                elif yy == y:
                    c = 'b5' if u < width * 0.5 else 'b4'
                elif yy == y + 2:
                    c = 'b1'
                else:
                    c = 'b3' if u < width * 0.6 else 'b2'
                g.put(xx, yy, c)
        g.put(x0 + 2, y + 1, 'x')
        g.put(x0 + width - 1, y + 1, 'b4')
    else:
        y0 = y - width // 2 - 1
        for xx in range(x, x + 3):
            for yy in range(y0, y0 + width + 2):
                u = yy - y0
                if u in (0, width + 1):
                    c = 'g0'
                elif xx == x:
                    c = 'b5' if u < width * 0.5 else 'b4'
                elif xx == x + 2:
                    c = 'b1'
                else:
                    c = 'b3' if u < width * 0.6 else 'b2'
                g.put(xx, yy, c)
        g.put(x + 1, y0 + 2, 'x')


def paint_pipes(g):
    # the left run: down from the vault behind the stall, along the wall
    # over the drain hole, down to the floor beside it
    pipe(g, [(30, -6), (30, 14), (126, 14), (126, 66)], 10, 8)
    collar(g, 30, 2, 10)
    collar(g, 70, 14, 10, vertical=False)
    collar(g, 126, 30, 10)
    collar(g, 126, 50, 10)
    # a thin feeder beside it, turning into the wall
    pipe(g, [(104, -6), (104, 6), (114, 6)], 6, 4)
    # the right run: down out of the vault, along the wall's top over the
    # Gatekeeper's corner, back up; a valve wheel on it
    pipe(g, [(PW - 58, -6), (PW - 58, 12), (PW - 172, 12), (PW - 172, -6)], 10, 8)
    collar(g, PW - 58, 0, 10)
    collar(g, PW - 172, 0, 10)
    collar(g, PW - 136, 12, 10, vertical=False)
    valve(g, PW - 100, 12)
    # a great pipe down the far right, into the floor
    pipe(g, [(PW - 40, -6), (PW - 40, 66)], 12, 8)
    collar(g, PW - 40, 22, 12)
    collar(g, PW - 40, 46, 12)
    # where the pipes go into the floor, a brass flange bolted down
    flange(g, 126, 10)
    flange(g, PW - 40, 12)


def flange(g, cx, width):
    """a brass flange where a pipe meets the floor, lit on its left"""
    x0 = cx - width // 2 - 2
    for x in range(x0, x0 + width + 4):
        u = x - x0
        g.put(x, WALL_Y1 - 1, 'b5' if u < (width + 4) // 2 else 'b4')
        g.put(x, WALL_Y1, 'b3' if u < (width + 4) // 2 else 'b2')
        g.put(x, WALL_Y1 + 1, 'b1')
        g.put(x, WALL_Y1 + 2, 'g0')
    g.put(x0, WALL_Y1 - 1, 'g0')
    g.put(x0 + width + 3, WALL_Y1 - 1, 'g0')
    g.put(x0 + 1, WALL_Y1, 'x')


def valve(g, cx, cy):
    """an iron hand wheel on a pipe: a rim, four spokes, a brass hub"""
    for (x, y) in ellipse_px(cx + 0.5, cy + 0.5, 6, 6):
        dx, dy = x + 0.5 - (cx + 0.5), y + 0.5 - (cy + 0.5)
        r = math.hypot(dx, dy)
        if r > 4.2:
            g.put(x, y, 'g1' if r > 5.3 else ('g5' if dx + dy < 0 else 'g3'))
        elif abs(dx) < 1 or abs(dy) < 1:
            g.put(x, y, 'g4')
    g.put(cx, cy, 'b5')
    g.put(cx - 4, cy - 3, 'g6')


# ----------------------------------------------------------- the falls --
ARCH_CY = 42            # the arch's centre: its spring line
ARCH_R0, ARCH_R1 = 20, 29  # the opening's radius and the ring's


def paint_arch(g):
    """the barred arch the falls pour from: a ring of voussoirs over two
    jambs, a dark culvert behind, a portcullis across its top"""
    for y in range(ARCH_CY - ARCH_R0, WALL_Y1):
        for x in range(CX - ARCH_R0, CX + ARCH_R0):
            dx = x + 0.5 - CX
            if y < ARCH_CY and math.hypot(dx, y + 0.5 - ARCH_CY) > ARCH_R0:
                continue
            g.px[y][x] = 'g0' if y < ARCH_CY - 4 or abs(dx) > 15 else 'a1'
    joints = [math.radians(a) for a in (154, 128, 104, 76, 52, 26)]
    for y in range(ARCH_CY - ARCH_R1, ARCH_CY + 1):
        for x in range(CX - ARCH_R1, CX + ARCH_R1):
            dx, dy = x + 0.5 - CX, y + 0.5 - ARCH_CY
            r = math.hypot(dx, dy)
            if not (ARCH_R0 <= r < ARCH_R1):
                continue
            ang = math.atan2(-dy, dx) % (2 * math.pi)
            if ang > math.pi:
                continue
            if any(abs(ang - j) * r < 0.7 for j in joints):
                g.px[y][x] = 'g0'
                continue
            if r >= ARCH_R1 - 1:
                c = 'g0'
            elif r < ARCH_R0 + 1:
                c = 'g3'
            else:
                lit = (-dx * 0.6 - dy * 0.8) / r
                c = 'g6' if (r < ARCH_R0 + 2.2 and lit > 0.3) else ('g5' if lit > 0.15 else ('g4' if lit > -0.4 else 'g3'))
                if abs(ang - math.pi / 2) < 0.2 and r > ARCH_R0 + 1.5:
                    c = 'g6' if r < ARCH_R1 - 2 else 'g5'
            g.px[y][x] = c
    # the jambs below the spring line: dressed blocks on each side
    jw = ARCH_R1 - ARCH_R0
    for side in (-1, 1):
        x0 = CX - ARCH_R1 if side == -1 else CX + ARCH_R0
        for y in range(ARCH_CY, WALL_Y1):
            for x in range(x0, x0 + jw):
                u, v = x - x0, (y - ARCH_CY) % 8
                if v == 7 or (side == -1 and u == 0) or (side == 1 and u == jw - 1):
                    c = 'g0'
                elif side == -1 and u == jw - 1:
                    c = 'g3'
                elif side == 1 and u == 0:
                    c = 'g1'
                elif v == 0:
                    c = 'g5'
                else:
                    c = 'g4' if side == -1 else 'g3'
                g.px[y][x] = c
    # the portcullis: bars across the opening's crown
    for y in range(ARCH_CY - ARCH_R0, ARCH_CY - 3):
        for bx in range(CX - 17, CX + 18, 6):
            if math.hypot(bx + 0.5 - CX, y + 0.5 - ARCH_CY) > ARCH_R0 - 0.5:
                continue
            g.put(bx, y, 'g4')
            g.put(bx + 1, y, 'g1')
    for yb in (ARCH_CY - 14, ARCH_CY - 4):
        for x in range(CX - ARCH_R0, CX + ARCH_R0):
            if math.hypot(x + 0.5 - CX, yb + 0.5 - ARCH_CY) <= ARCH_R0 - 0.5:
                g.put(x, yb, 'g4' if (x - CX) % 6 else 'g5')
                g.put(x, yb + 1, 'g1')


FALL_X0, FALL_X1 = CX - 14, CX + 14     # the sheet of water
FALL_Y0 = ARCH_CY - 3                    # it pours over the culvert's lip
BASIN_Y1 = 104                           # the basin's front rim
BASIN_RX = 34                            # its half width


def basin_inside(x, y):
    """the basin's water: the wall at its back, a rounded front"""
    if y < WALL_Y1:
        return False
    dx = (x + 0.5 - CX) / (BASIN_RX - 5)
    dy = (y + 0.5 - WALL_Y1) / (BASIN_Y1 - 6 - WALL_Y1)
    return dx * dx + dy ** 4 <= 1.0


def basin_rim(x, y):
    if y < WALL_Y1:
        return False
    dx = (x + 0.5 - CX) / BASIN_RX
    dy = (y + 0.5 - WALL_Y1) / (BASIN_Y1 - WALL_Y1)
    return dx * dx + dy ** 4 <= 1.0


def paint_basin_rim(g):
    """the basin's rim: dressed stone round the water, its face below"""
    for y in range(WALL_Y1, BASIN_Y1 + 1):
        for x in range(CX - BASIN_RX - 1, CX + BASIN_RX + 1):
            if not basin_rim(x, y) or basin_inside(x, y):
                continue
            if not basin_rim(x, y + 1):
                c = 'g1'
            elif not basin_rim(x, y + 4):
                c = 'g2' if not basin_rim(x, y + 2) else 'g3'
            elif basin_inside(x, y - 1) or basin_inside(x + 1, y) or basin_inside(x - 1, y):
                c = 'g6'
            else:
                c = 'g4' if rnd(x, y, 71) > 0.1 else 'g5'
            g.px[y][x] = c
    for ang in (0.55, 0.95, 1.35, 1.79, 2.19, 2.59):
        _rim_joint(g, ang)
    # the shadow the rim throws on the floor below it
    for x in range(CX - BASIN_RX, CX + BASIN_RX):
        for y in range(WALL_Y1, BASIN_Y1 + 4):
            if basin_rim(x, y) and not basin_rim(x, y + 1):
                for d in (1, 2):
                    c = g.get(x, y + d)
                    if c and c[0] == 'g' and (d == 1 or not dither(x, y + d, 0.5)):
                        g.put(x, y + d, shift(c, -1))
                break


def _rim_joint(g, ang):
    """a joint across the rim at an angle round its front"""
    for t in range(0, 12):
        f = t / 11.0
        x = CX - math.cos(ang) * (BASIN_RX - 5 + f * 6)
        y = WALL_Y1 + math.sin(ang) * ((BASIN_Y1 - 6 - WALL_Y1) + f * 6) * 0.98
        xi, yi = int(x), int(y)
        if basin_rim(xi, yi) and not basin_inside(xi, yi):
            g.px[yi][xi] = 'g0'


def paint_falls(g, t):
    """the sheet of water: streaks pouring down, a bright lip, the churn"""
    wdt = FALL_X1 - FALL_X0
    for y in range(FALL_Y0, WALL_Y1 + 8):
        for x in range(FALL_X0, FALL_X1):
            u = x - FALL_X0
            if y > WALL_Y1 - 4 and u in (0, wdt - 1):
                continue
            edge = u in (0, wdt - 1)
            ph = int(rnd(u, 0, 81) * 16)
            k = (y - 4 * t - ph) % 16
            if y == FALL_Y0:
                c = 'a7' if not edge else 'a5'
            elif y == FALL_Y0 + 1:
                c = 'a6' if not edge else 'a4'
            elif edge:
                c = 'a3' if k > 2 else 'a4'
            elif k < 2:
                c = 'x' if (rnd(u, 1, 82) < 0.5 and k == 0) else 'a7'
            elif k < 5:
                c = 'a6'
            elif u in (1, wdt - 2):
                c = 'a4'
            else:
                c = 'a5'
            g.px[y][x] = c


def paint_basin(g, t):
    """the basin's water: churned white where the falls strike, rings
    spreading from it, calmer and darker toward the rim"""
    for y in range(WALL_Y1, BASIN_Y1):
        for x in range(CX - BASIN_RX, CX + BASIN_RX):
            if not basin_inside(x, y):
                continue
            dx, dy = (x + 0.5 - CX), (y + 0.5 - (WALL_Y1 + 6)) * 1.9
            r = math.hypot(dx, dy)
            # the rings spread out to 24 px and fade; beyond, the water lies still
            ring = (r - 2.0 * (t % 12)) % 12
            churn = r < 15 and y < WALL_Y1 + 12
            if churn:
                n = rnd(x // 2, y // 2, 90 + t % 4)
                c = 'x' if n < 0.28 else ('a7' if n < 0.62 else 'a6')
            elif ring < 1.2 and r < 15:
                c = 'a6' if r < 11 else 'a5'
            elif ring < 2.2 and r < 15:
                c = 'a2'
            else:
                c = 'a4' if r < 22 else 'a3'
            if not churn and (not basin_inside(x, y - 2) or not basin_inside(x - 2, y) or not basin_inside(x + 2, y)):
                c = 'a2'
            g.px[y][x] = c


# ------------------------------------------------------------ the hole --
HOLE_X = 9 * 16 + 8     # the drain hole's middle (the exit cell is 9, 2)
HOLE_HW = 7
HOLE_TOP = 22


def paint_hole(g, o):
    """the drain hole up to the wood: an arched mouth in the wall, a
    ladder climbing into the dark, a green glimmer far above"""
    cy = HOLE_TOP + HOLE_HW
    for y in range(HOLE_TOP - 3, WALL_Y1):
        for x in range(HOLE_X - HOLE_HW - 3, HOLE_X + HOLE_HW + 3):
            dx = x + 0.5 - HOLE_X
            r = math.hypot(dx, y + 0.5 - cy) if y < cy else abs(dx)
            if r < HOLE_HW:
                if y < HOLE_TOP + 4 and abs(dx) < 4:
                    c = 'm2' if dither(x, y, 0.45) else 'm1'
                elif y < HOLE_TOP + 8:
                    c = 'g2' if dither(x, y, 0.3) else 'g0'
                else:
                    c = 'g0'
                g.px[y][x] = c
            elif r < HOLE_HW + 3:
                lit = (-dx - ((y - cy) if y < cy else 0)) > 0
                c = 'g5' if (r < HOLE_HW + 1 and lit) else ('g4' if lit else 'g3')
                if r >= HOLE_HW + 2:
                    c = 'g0'
                g.px[y][x] = c
    for y in range(HOLE_TOP + 2, WALL_Y1):
        for rx in (HOLE_X - 4, HOLE_X + 3):
            g.put(rx, y, 'g2')
        if (y - HOLE_TOP) % 5 == 0:
            for x in range(HOLE_X - 4, HOLE_X + 4):
                g.put(x, y, 'g4')
            g.put(HOLE_X - 3, y, 'g5')
    for x in range(HOLE_X - HOLE_HW, HOLE_X + HOLE_HW):
        g.px[WALL_Y1][x] = 'g1'
    # vines hang from the arch: the wood grows down into the drain
    for (vx, length) in ((HOLE_X - 8, 9), (HOLE_X - 5, 5), (HOLE_X + 6, 7), (HOLE_X + 9, 11), (HOLE_X + 2, 3)):
        top = HOLE_TOP - 2 + (0 if abs(vx - HOLE_X) < 7 else 4)
        for k in range(length):
            x = vx + (1 if (k // 3) % 2 else 0)
            g.put(x, top + k, 'm2' if k % 3 else 'm3')
            if k % 4 == 2:
                g.put(x + (1 if vx < HOLE_X else -1), top + k, 'm1')
        g.put(vx, top + length, 'm1')
    # the arch's crown rides the overlay: the hero in the mouth is inside it
    for y in range(HOLE_TOP - 3, HOLE_TOP + 14):
        for x in range(HOLE_X - HOLE_HW - 3, HOLE_X + HOLE_HW + 3):
            dx = x + 0.5 - HOLE_X
            r = math.hypot(dx, y + 0.5 - cy) if y < cy else abs(dx)
            if HOLE_HW <= r < HOLE_HW + 3 or (r < HOLE_HW and y < HOLE_TOP + 6):
                o.put(x, y, g.px[y][x])


# -------------------------------------------------------------- banners --
SUN = sprite({'g': 'b5', 'G': 'b3', 'h': 'x'}, '''
..g.g.g..
...ggg...
g.gGhGg.g
.gGhhhGg.
.ghhGhhg.
.gGhhhGg.
g.gGGGg.g
...ggg...
..g.g.g..
''')
MOON = sprite({'g': 'b5', 'G': 'b3', 'h': 'b5'}, '''
...ggg...
..gGG....
.gGG.....
.gG...h..
gGG......
.gG......
.gGG...h.
..gGGg...
...ggg...
''')


def banner(g, x0, y0, cloth, emblem):
    """a banner on a brass rod: cloth with a gold border, a swallowtail,
    folds lit from the left, an emblem at its heart"""
    w, h = 16, 36
    c0, c1, c2, c3 = cloth
    for x in range(x0 - 3, x0 + w + 3):
        g.put(x, y0 - 2, 'b5')
        g.put(x, y0 - 1, 'b3')
    for fx in (x0 - 4, x0 + w + 3):
        g.put(fx, y0 - 3, 'b5')
        g.put(fx, y0 - 2, 'b4')
        g.put(fx, y0 - 1, 'b3')

    def notch(x, y):
        return h - 1 - y < 6 and abs(x - (w - 1) / 2.0) < (6 - (h - 1 - y)) * 0.75

    for y in range(h):
        for x in range(w):
            if notch(x, y):
                continue
            if x in (0, w - 1) or y == 0 or y == h - 1:
                c = c0
            elif y == 2:
                c = 'b4'
            else:
                fold = (x - 2) % 6
                c = c3 if fold == 0 else (c1 if fold in (4, 5) else c2)
                if y > h - 9 and fold in (3, 4):
                    c = c1
            g.put(x0 + x, y0 + y, c)
    # the gold hem along the swallowtail
    for y in range(h - 7, h):
        for x in range(1, w - 1):
            if not notch(x, y) and (y + 1 >= h or notch(x, y + 1)):
                g.put(x0 + x, y0 + y, 'b4')
    g.blit(emblem, x0 + (w - 9) // 2 + 1, y0 + 10)


def paint_banners(g):
    banner(g, 11 * 16, 14, ('g1', 'a2', 'a3', 'a4'), SUN)
    banner(g, 18 * 16, 14, ('g0', 'p2', 'p3', 'p4'), MOON)


# ------------------------------------------------------------- lanterns --
def lantern_static(g, cx, top, bottom):
    """a lantern hung on a chain: a brass cap and foot, a cage of bars
    (four brass tones, so a lantern's cell keeps to one palette)"""
    for y in range(top, bottom):
        if (y - top) % 4 < 2:
            g.put(cx, y, 'g4')
        else:
            g.put(cx - 1, y, 'g0')
            g.put(cx + 1, y, 'g0')
    y = bottom
    for dx in range(-2, 3):
        g.put(cx + dx, y, 'b4' if dx < 1 else 'b3')
    for dx in range(-5, 6):
        g.put(cx + dx, y + 1, 'b4' if dx < -1 else ('b3' if dx < 3 else 'b2'))
        g.put(cx + dx, y + 2, 'b2' if abs(dx) < 5 else 'b1')
    for yy in range(y + 3, y + 13):
        g.put(cx - 5, yy, 'b3')
        g.put(cx + 5, yy, 'b1')
        g.put(cx, yy, 'b2')
    for dx in range(-5, 6):
        g.put(cx + dx, y + 13, 'b4' if dx < 0 else 'b2')
    for dx in range(-3, 4):
        g.put(cx + dx, y + 14, 'b3' if dx < 1 else 'b1')
    g.put(cx, y + 15, 'b2')


def lantern_glass(g, cx, top_cap, t):
    """the flame behind the glass: three tones that flicker"""
    y0 = top_cap + 3
    f = (t // 2) % 3
    for yy in range(y0, y0 + 10):
        for dx in (-4, -3, -2, -1, 1, 2, 3, 4):
            v = yy - y0
            if abs(dx) < 3 and 2 <= v <= 7:
                c = 'x' if (f != 2 or v > 3) else 'y2'
            else:
                c = 'y2' if (v < 3 or abs(dx) == 3) else 'y1'
                if f == 1 and abs(dx) == 4 and v > 6:
                    c = 'y1'
            g.put(cx + dx, yy, c)


def glow(g, cx, cy, r):
    """a lantern's light on the wall round it: each colour a step up its
    ramp (no higher than its fourth), fading out in an ordered dither"""
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            d = math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * 1.1) / r
            if d > 1:
                continue
            c = g.get(x, y)
            if c is None or c[0] != 'g' or c in ('g4', 'g5', 'g6', 'g7'):
                continue
            level = 1 - d
            if level > 0.55 or dither(x, y, level / 0.55):
                g.put(x, y, shift(c, 1))


LANTERNS = [(12 * 16 + 8, 18), (17 * 16 + 8, 18)]


def paint_lanterns_static(g):
    for (cx, bottom) in LANTERNS:
        glow(g, cx, bottom + 8, 15)
        lantern_static(g, cx, 0, bottom)


def paint_lanterns(g, t):
    for (cx, bottom) in LANTERNS:
        lantern_glass(g, cx, bottom, t)


# ---------------------------------------------------------------- water --
WAVE_P = 32
# the crests: (row from the water's top, start, length) round a 32 px ring
WAVES = [(5, 3, 7), (5, 20, 4), (8, 14, 6), (11, 25, 5), (11, 7, 4), (14, 17, 7), (17, 2, 6),
         (17, 22, 4), (20, 11, 7), (23, 26, 5), (23, 6, 4), (26, 15, 6), (29, 1, 7), (32, 19, 6)]
SPARKS = [(7, 12, 0), (12, 27, 3), (18, 5, 5), (24, 18, 2), (30, 29, 6)]


def water_px(x, y, t, top, bottom):
    """open water: a teal body, darker under the bank, crests drifting
    with the flow, a sparkle now and then"""
    v = y - top
    depth = bottom - top
    if v < 2:
        return 'a1'
    if v < 4:
        return 'a2'
    if v == depth - 1:
        return 'a2'
    phase = (t // 3) % 8
    xx = (x - 4 * phase) % WAVE_P
    for (wv, x0, ln) in WAVES:
        if v == wv:
            k = (xx - x0) % WAVE_P
            if k < ln:
                if k == 1:
                    return 'a6'
                return 'a4' if k in (0, ln - 1) else 'a5'
        elif v == wv + 1:
            k = (xx - x0) % WAVE_P
            if 1 <= k < ln - 1:
                return 'a2'
    for (sv, sx, sp) in SPARKS:
        if sv > depth - 16:
            continue
        if v == sv and xx == sx and (phase - sp) % 8 < 2:
            return 'x' if (phase - sp) % 8 == 0 else 'a7'
    return 'a3'


def paint_water(g, t):
    for y in range(CH_W0, CH_W1):
        for x in range(SIDE, PW - SIDE):
            g.px[y][x] = water_px(x, y, t, CH_W0, CH_W1)
    for y in range(BW_Y0, PH):
        for x in range(SIDE, PW - SIDE):
            c = water_px(x, y, t, BW_Y0, PH + 6)
            # deeper toward the room's edge: a step darker in its last rows
            if y >= PH - 6:
                c = shift(c, -1) if c not in ('x', 'a7') else 'a5'
            g.px[y][x] = c


# ------------------------------------------------------------- railings --
BRIDGE_X0, BRIDGE_X1 = CX - 16, CX + 16


def post(c, x0, base, h=16):
    """a slate post with a brass cap and band, standing on its foot"""
    top = base - h
    # the foot: a little plinth
    for x in range(x0 - 1, x0 + 7):
        c.put(x, base, 'g3' if x < x0 + 4 else 'g2')
        c.put(x, base + 1, 'g1')
    # the shaft, lit on its left
    for y in range(top + 3, base):
        for i, col in enumerate(('g0', 'g4', 'g3', 'g3', 'g2', 'g0')):
            c.put(x0 + i, y, col)
    # a brass band near the foot
    for i, col in enumerate(('g0', 'b4', 'b3', 'b3', 'b1', 'g0')):
        c.put(x0 + i, base - 4, col)
    # the cap: a lit brass dome
    cap = sprite({'o': 'g0', '1': 'b1', '3': 'b3', '4': 'b4', '5': 'b5', 'x': 'x'}, '''
.oooooo.
o45433o.
o5x4331o
o443311o
.o3311o.
''')
    c.blit(cap, x0 - 1, top - 1)


def rail(c, x0, x1, y):
    """a brass rail between posts: lit on top, dark below"""
    for x in range(x0, x1):
        c.put(x, y, 'b5' if x % 32 in (3, 4, 19) else 'b4')
        c.put(x, y + 1, 'b3')
        c.put(x, y + 2, 'b1')


def railing(c, xs, base, rail_y, gaps=()):
    """posts at xs on a coping, a rail between each two, none over a gap"""
    for a, b in zip(xs, xs[1:]):
        if any(a < g1 and b > g0 for (g0, g1) in gaps):
            continue
        rail(c, a + 6, b, rail_y)
    for x in xs:
        post(c, x, base)


def rail_posts(x0, x1, step=32, first=8):
    return [x for x in range(x0 + first, x1, step)]


def paint_railings(under, over, o):
    """the three railed edges: the near bank, the far bank, the front"""
    gaps = [(BRIDGE_X0, BRIDGE_X1)]
    xs = [x for x in rail_posts(SIDE, PW - SIDE) if not (BRIDGE_X0 - 6 < x < BRIDGE_X1)]
    xs = sorted(set(xs + [BRIDGE_X0 - 8, BRIDGE_X1 + 2]))
    # the near bank: the hero walks behind it, so its tops ride the overlay
    tmp = Canvas(PW, PH)
    railing(tmp, xs, NB_COPE + 2, NB_COPE - 9, gaps)
    for y in range(PH):
        for x in range(PW):
            col = tmp.px[y][x]
            if col is not None:
                (o if y < NB_COPE - 10 else under).put(x, y, col)
    # the far bank: its posts stand over the channel's water
    railing(over, xs, SB_COPE + 2, SB_COPE - 9, gaps)
    # the lower floor's front edge: the hero walks behind it
    tmp = Canvas(PW, PH)
    railing(tmp, rail_posts(SIDE, PW - SIDE), FE_COPE + 2, FE_COPE - 9)
    for y in range(PH):
        for x in range(PW):
            col = tmp.px[y][x]
            if col is not None:
                (o if y < FE_COPE else under).put(x, y, col)


def paint_bridge(g, over):
    """an iron grate bridge over the channel: two girders, cross bars,
    the dark water glinting between them"""
    for y in range(NB_FACE - 6, SB_COPE + 6):
        for x in range(BRIDGE_X0, BRIDGE_X1):
            u = x - BRIDGE_X0
            w = BRIDGE_X1 - BRIDGE_X0
            on_water = NB_FACE <= y < SB_COPE
            if u in (0, w - 1):
                col = 'g0'
            elif u in (1, 2):
                col = 'g5' if u == 1 else 'g4'
            elif u in (w - 3, w - 2):
                col = 'g3' if u == w - 3 else 'g2'
            else:
                k = (y - NB_FACE) % 4
                col = 'g5' if k == 0 else ('g4' if k == 1 else ('g3' if k == 2 else ('a2' if on_water else 'g1')))
            (over if on_water else g).put(x, y, col)
    # the bridge's ends: a lip of dressed stone on each bank
    for y in (NB_COPE - 1, SB_COPE + 6):
        for x in range(BRIDGE_X0 - 1, BRIDGE_X1 + 1):
            g.put(x, y, 'g5' if y < SB_COPE else 'g2')
    # its side rails: brass along both edges over the water, a post at
    # each end
    for y in range(NB_FACE - 4, SB_COPE + 2):
        for (x, cols) in ((BRIDGE_X0 + 1, ('b4', 'b3')), (BRIDGE_X1 - 3, ('b3', 'b1'))):
            (over if NB_FACE <= y < SB_COPE else g).put(x, y, cols[0])
            (over if NB_FACE <= y < SB_COPE else g).put(x + 1, y, cols[1])
    for (x, y) in ((BRIDGE_X0 + 1, NB_FACE - 6), (BRIDGE_X1 - 3, NB_FACE - 6), (BRIDGE_X0 + 1, SB_COPE + 1), (BRIDGE_X1 - 3, SB_COPE + 1)):
        for (dx, dy, col) in ((0, 0, 'b5'), (1, 0, 'b4'), (0, 1, 'b4'), (1, 1, 'b2'), (0, 2, 'g0'), (1, 2, 'g0')):
            g.put(x + dx, y + dy, col)


# ------------------------------------------------------------- the drain --
DRAIN_Y = 234


def paint_drain(g):
    """the great drain: a ring of ten dressed blocks round a barred dark,
    water glinting far down. Each block is lit by where it faces."""
    rx1, ry1 = 26.0, 17.0       # the ring's outside
    k0 = 0.62                   # its inside, as a part of the outside
    n = 10
    for y in range(DRAIN_Y - 18, DRAIN_Y + 19):
        for x in range(CX - 27, CX + 27):
            u, v = (x + 0.5 - CX) / rx1, (y + 0.5 - DRAIN_Y) / ry1
            rho = math.hypot(u, v)
            if rho > 1:
                continue
            if rho <= k0:
                # the hole: a dark lip, bars, the dark between
                if rho > k0 - 0.07:
                    col = 'g1'
                elif (x - CX) % 4 == 0:
                    col = 'g4' if v < -0.15 else 'g3'
                elif (x - CX) % 4 == 1:
                    col = 'g1'
                elif abs(v) < 0.04:
                    col = 'g2'
                elif v > 0.25 and abs(u) < 0.32 and (x + y) % 3 == 0:
                    col = 'a2'
                else:
                    col = 'g0'
                g.px[y][x] = col
                continue
            ang = math.atan2(v, u) % (2 * math.pi)
            sector = int(ang / (2 * math.pi / n))
            mid = (sector + 0.5) * (2 * math.pi / n)
            # the joint: within half a pixel of a sector line
            edge = min(ang - sector * (2 * math.pi / n), (sector + 1) * (2 * math.pi / n) - ang)
            if edge * rho * rx1 < 0.75:
                col = 'g1'
            elif rho > 0.94:
                col = 'g2' if v > 0 else 'g3'
            elif rho < k0 + 0.07:
                col = 'g5' if v > 0 else 'g3'   # the hole's lit far rim
            else:
                face = -math.cos(mid) * 0.6 - math.sin(mid) * 0.8   # faces the light
                col = 'g6' if face > 0.55 else ('g5' if face > 0.0 else ('g4' if face > -0.6 else 'g3'))
                if face > 0.55 and rho > 0.85:
                    col = 'g5'
            g.px[y][x] = col
    # the ring sits a little proud: a shadow under its lower rim
    for x in range(CX - 24, CX + 24):
        for y in range(DRAIN_Y + 10, DRAIN_Y + 20):
            u, v = (x + 0.5 - CX) / rx1, (y + 0.5 - DRAIN_Y) / ry1
            if math.hypot(u, v) > 1:
                c = g.get(x, y)
                if c and c[0] == 'g':
                    g.put(x, y, shift(c, -1))
                break


def small_grate(g, cx, cy):
    """a round floor grate: a lit rim, three bars over the dark"""
    rx, ry = 9, 6
    for y in range(cy - ry - 1, cy + ry + 1):
        for x in range(cx - rx - 1, cx + rx + 1):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = (dx / rx) ** 2 + (dy / ry) ** 2
            if r > 1:
                continue
            ri = (dx / (rx - 2)) ** 2 + (dy / (ry - 2)) ** 2
            if ri > 1:
                col = 'g5' if (dy > 0 or dx > 3) and r > 0.6 else ('g2' if dy < 0 else 'g4')
                if dy > 1.5 and r > 0.75:
                    col = 'g5'
                if dy < -1 and r > 0.7:
                    col = 'g2'
            elif (x - cx) % 4 == 2:
                col = 'g4' if dy < 0 else 'g3'
            elif (x - cx) % 4 == 3:
                col = 'g1'
            else:
                col = 'g0'
            g.px[y][x] = col


def paint_grates(g):
    small_grate(g, CX - 104, DRAIN_Y - 2)
    small_grate(g, CX + 104, DRAIN_Y - 2)
    small_grate(g, CX - 152, 120)
    small_grate(g, CX + 152, 120)


# ------------------------------------------------------- the front face --
SPOUTS = [CX - 120, CX + 120]


def paint_spouts_static(g):
    """brass pipe ends jutting from the front face"""
    for sx in SPOUTS:
        for (x, y) in ellipse_px(sx + 0.5, FE_FACE + 4.5, 5, 4):
            dx, dy = x + 0.5 - (sx + 0.5), y + 0.5 - (FE_FACE + 4.5)
            r = (dx / 5) ** 2 + (dy / 4) ** 2
            if r > 0.5:
                g.put(x, y, 'b5' if dx + dy < -1 else ('b3' if dx + dy < 2 else 'b1'))
            else:
                g.put(x, y, 'g0')
        g.put(sx - 3, FE_FACE + 2, 'x')


def paint_spouts(g, t):
    """water pouring from each spout into the pool, a splash below"""
    for sx in SPOUTS:
        y0 = FE_FACE + 6
        for y in range(y0, BW_Y0 + 3):
            for dx in range(-2, 3):
                k = (y - 4 * t - dx * 3) % 8
                col = 'x' if k < 2 else ('a6' if abs(dx) < 2 else 'a5')
                if y >= BW_Y0 and abs(dx) == 2:
                    continue
                g.put(sx + dx, y, col)
        # the splash: foam that boils, a ring that spreads, all within the
        # spout's own cell
        for (x, y) in ellipse_px(sx + 0.5, BW_Y0 + 4.5, 5, 3):
            n = rnd(x, y, 130 + t % 4)
            if n < 0.4:
                g.put(x, y, 'x' if n < 0.15 else 'a6')
        r = 4 + (t % 4) * 1
        for k in range(40):
            ang = k * math.pi / 20
            x = int(sx + math.cos(ang) * r)
            y = int(BW_Y0 + 6 + math.sin(ang) * r * 0.4)
            if y > BW_Y0 + 1:
                g.put(x, y, 'a5')


def paint_ladder(over):
    """an iron ladder down the front face into the pool"""
    x0 = 66
    for y in range(FE_COPE - 2, BW_Y0 + 10):
        over.put(x0, y, 'g5')
        over.put(x0 + 1, y, 'g3')
        over.put(x0 + 9, y, 'g5')
        over.put(x0 + 10, y, 'g3')
        if (y - FE_COPE) % 5 == 0:
            for x in range(x0 + 2, x0 + 9):
                over.put(x, y, 'g6' if x < x0 + 5 else 'g5')
                over.put(x, y + 1, 'g1')


# ------------------------------------------------------------ shadows --
def shadow(g, cx, cy, rx, ry=None):
    """a contact shadow: the ground under a thing a step darker"""
    ry = ry or max(1.5, rx / 2.5)
    for (x, y) in ellipse_px(cx + 0.5, cy + 0.5, rx, ry):
        c = g.get(x, y)
        if c and c[0] == 'g' and c != 'g0':
            g.put(x, y, shift(c, -1))


# ------------------------------------------------------- the Peddler --
import sw_props as SP  # noqa: E402

PEDDLER = (4 * 16 + 8, 5 * 16 + 14)     # where the game stands him
GATEKEEPER = (21 * 16 + 8, 5 * 16 + 14)
STALL_X0, STALL_X1 = 24, 120
COUNTER_X0, COUNTER_X1, COUNTER_Y0, COUNTER_Y1 = 40, 104, 80, 101


def awning(g, x0, x1, y0, y1, cloth, trim):
    """a cloth awning off the wall: a batten, the cloth sloping toward
    us in lit and shaded folds, a scalloped valance with a gold hem"""
    c1, c2, c3, c4 = cloth
    # the batten it hangs from
    for x in range(x0 - 2, x1 + 2):
        g.put(x, y0 - 2, 'd3')
        g.put(x, y0 - 1, 'd1')
    for y in range(y0, y1):
        for x in range(x0, x1):
            v = (y - y0) / float(y1 - y0)
            fold = (x - x0) % 12
            # the folds catch the light on their left, darken to their right
            col = c4 if fold in (0, 1) and v > 0.25 else (c2 if fold in (8, 9, 10, 11) else c3)
            if v < 0.2:
                col = c2 if fold < 8 else c1    # under the batten, in its shade
            g.put(x, y, col)
    # the valance: scallops of eight under a gold hem, each a round lobe
    # lit on its left, darker to its right, outlined along its edge
    for x in range(x0 - 1, x1 + 1):
        g.put(x, y1, trim[1])
        g.put(x, y1 + 1, trim[0])
        k = (x - x0) % 8
        depth = [2, 4, 5, 6, 6, 5, 4, 2][k]
        for d in range(depth):
            if d == depth - 1 or k == 0:
                col = c1
            else:
                col = c4 if k in (1, 2) and d < depth - 2 else (c3 if k in (1, 2, 3, 4) else c2)
            g.put(x, y1 + 2 + d, col)
        if k == 4:
            g.put(x, y1 + 2 + depth, trim[1])
    for x in (x0 - 1, x1):
        for y in range(y0, y1 + 2):
            g.put(x, y, 'g0')


def pole(g, x, y0, y1):
    """a wooden pole, lit on the left"""
    for y in range(y0, y1):
        g.put(x, y, 'd4')
        g.put(x + 1, y, 'd3')
        g.put(x + 2, y, 'd1')


def counter(o, x0, x1, y0, y1):
    """the Peddler's counter, on the overlay so he stands behind it: a
    wooden top, red cloth draped down its front, a gold diamond on it"""
    top = y0 + 6
    for y in range(y0, y1):
        for x in range(x0, x1):
            u = x - x0
            if y == y0:
                col = 'g0'
            elif y < top:
                # the top: planks running along, lit at the front edge
                col = 'd4' if y == top - 1 else ('d3' if (y - y0) % 2 else 'd2')
                if u in (0, x1 - x0 - 1):
                    col = 'g0'
            elif y == y1 - 1:
                col = 'g0'
            else:
                # the cloth: folds every eight, a fringe of gold at its hem
                fold = u % 8
                col = 'r4' if fold == 1 else ('r2' if fold in (6, 7) else 'r3')
                if y >= y1 - 3:
                    col = 'b4' if (u % 2 == 0) else 'b3'
                if u in (0, x1 - x0 - 1):
                    col = 'g0'
            o.put(x, y, col)
    # the gold diamond on the cloth
    cx, cy = (x0 + x1) // 2, top + (y1 - top) // 2 - 1
    for dy in range(-4, 5):
        w = 4 - abs(dy)
        for dx in range(-w, w + 1):
            ring = abs(dx) + abs(dy)
            o.put(cx + dx, cy + dy, 'b5' if ring == 4 else ('r1' if ring == 3 else ('b4' if ring < 2 else 'r2')))


def paint_stall(g, o):
    """the Peddler's stall: an awning off the wall on two poles, his
    counter, his wares, a chest and a barrel at its ends"""
    # the shade the awning throws on the floor under it
    for y in range(WALL_Y1 + 3, COUNTER_Y0 + 2):
        for x in range(STALL_X0, STALL_X1):
            c = g.get(x, y)
            if c and c[0] == 'g':
                g.put(x, y, shift(c, -1))
    awning(g, STALL_X0 + 3, STALL_X1 - 3, 34, 52, ('r1', 'r2', 'r3', 'r4'), ('b3', 'b5'))
    pole(g, STALL_X0 + 2, 56, COUNTER_Y1 + 1)
    pole(g, STALL_X1 - 5, 56, COUNTER_Y1 + 1)
    counter(o, COUNTER_X0, COUNTER_X1, COUNTER_Y0, COUNTER_Y1)
    o.blit(SP.COINS, COUNTER_X0 + 8, COUNTER_Y0 - 3)
    o.blit(SP.FLASK_RED, COUNTER_X1 - 16, COUNTER_Y0 - 5)
    # at its ends: the chest and a barrel with a skull on it
    shadow(g, 26, COUNTER_Y1, 8)
    shadow(g, STALL_X1 - 5, COUNTER_Y1, 6)
    g.blit(SP.CHEST, 17, COUNTER_Y1 - 12)
    g.blit(SP.BARREL, STALL_X1 - 12, COUNTER_Y1 - 12)
    g.blit(SP.SKULL, STALL_X1 - 10, COUNTER_Y1 - 20)


# --------------------------------------------------- the Gatekeeper --
RUG_X0, RUG_X1, RUG_Y0, RUG_Y1 = 312, 376, 80, 116


def rug(g, x0, x1, y0, y1):
    """the Gatekeeper's rug: purple, a gold border, a crescent at its
    heart, stars at its corners, a fringe at its ends"""
    for y in range(y0, y1):
        for x in range(x0, x1):
            u, v = x - x0, y - y0
            w, h = x1 - x0, y1 - y0
            if u in (0, w - 1) or v in (0, h - 1):
                col = 'p1'
            elif u in (2, w - 3) or v in (2, h - 3):
                col = 'b4'
            elif u in (1, w - 2) or v in (1, h - 2):
                col = 'p2'
            else:
                col = 'p3' if ((u + v) // 2) % 5 else 'p2'
            g.put(x, y, col)
        # the fringe
    for y in (y0 - 1, y1):
        for x in range(x0 + 1, x1 - 1, 2):
            g.put(x, y, 'b3')
    moon = sprite({'g': 'b5', 'G': 'b4'}, '''
..ggg..
.gG....
gG.....
gG.....
gG.....
.gG....
..ggg..
''')
    g.blit(moon, (x0 + x1) // 2 - 3, (y0 + y1) // 2 - 3)
    for (sx, sy) in ((x0 + 7, y0 + 7), (x1 - 8, y0 + 7), (x0 + 7, y1 - 8), (x1 - 8, y1 - 8)):
        g.put(sx, sy, 'b5')
        g.put(sx - 1, sy, 'b4')
        g.put(sx + 1, sy, 'b4')
        g.put(sx, sy - 1, 'b4')
        g.put(sx, sy + 1, 'b4')


def bookshelf(g, x0, y0, w=30, h=36):
    """a bookshelf against the wall: two shelves of books"""
    books = ['r2', 'a3', 'p2', 'b4', 'd3', 'a3', 'p2', 'r2']
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            u, v = x - x0, y - y0
            if u in (0, w - 1) or v in (0, h - 1):
                col = 'g0'
            elif u in (1, w - 2) or v in (1, h - 13, h - 25):
                col = 'd3' if u == 1 or v in (1,) else 'd2'
                if v in (h - 13, h - 25):
                    col = 'd4'
            elif v == h - 2:
                col = 'd1'
            else:
                shelf = 0 if v < h - 25 else (1 if v < h - 13 else 2)
                if shelf == 0:
                    col = 'd1'
                else:
                    k = (u - 2) // 3
                    tall = 9 if (k * 7 + shelf) % 3 else 7
                    top = (h - 13 if shelf == 1 else h - 1) - tall
                    if v < top - (0 if shelf == 2 else 0) or v >= (h - 13 if shelf == 1 else h - 1):
                        col = 'd1'
                    else:
                        col = books[(k * 3 + shelf * 5) % len(books)]
                        if (u - 2) % 3 == 2:
                            col = 'g0'
                        elif v == top:
                            col = {'r2': 'r3', 'a3': 'a4', 'p2': 'p3', 'd3': 'd4'}.get(col, col)
            g.put(x, y, col)


def candles(g, x, y, t, n=3):
    """a stand of candles, their flames flickering out of step"""
    for k in range(n):
        cx = x + k * 6
        h = (3, 0, 2)[k % 3]
        g.blit(SP.CANDLE, cx, y + h)
        if t is not None:
            f = SP.FLAMES[(t // 2 + k) % 3]
            g.blit(f, cx, y + h - 4)


def paint_corner(g, o):
    """the Gatekeeper's corner: a purple canopy off the wall over him,
    candles at its feet, his books, his rug, crates stacked high and a
    crow on them, a skull and a flask by the banner"""
    for y in range(WALL_Y1 + 3, RUG_Y0):
        for x in range(RUG_X0 + 6, RUG_X1 - 6):
            c = g.get(x, y)
            if c and c[0] == 'g':
                g.put(x, y, shift(c, -1))
    awning(g, RUG_X0 + 10, RUG_X1 - 10, 30, 42, ('p1', 'p2', 'p3', 'p4'), ('b4', 'b5'))
    bookshelf(g, 372, 30, 28, 42)
    rug(g, RUG_X0, RUG_X1, RUG_Y0, RUG_Y1)
    g.blit(SP.SKULL, 298, 66)
    shadow(g, 302, 75, 5)
    g.blit(SP.FLASK_PURPLE, 313, 66)
    shadow(g, 316, 74, 3)
    # crates stacked against the wall, the crow on the top one
    shadow(g, 424, 88, 18, 3)
    g.blit(SP.CRATE, 402, 74)
    g.blit(SP.CRATE, 416, 74)
    g.blit(SP.CRATE_S, 410, 63)
    g.blit(SP.CROW, 412, 54)
    g.blit(SP.BARREL, 431, 76)


def paint_corner_anim(g, t):
    candles(g, RUG_X0 + 12, 61, t)
    candles(g, RUG_X1 - 28, 61, t)


# --------------------------------------------------------- lily pads --
LILIES = [(170, 171, False), (196, 306, True), (330, 302, False)]


def lily(g, cx, cy, bloom):
    """a lily pad on the water: a disc with a notch, lit on its upper
    left, a dark rim, a shadow on the water below it; a pink bloom"""
    rx, ry = 6, 3.5
    for (x, y) in ellipse_px(cx + 0.5, cy + 1.5, rx, ry):
        g.put(x, y, 'a1')               # its shadow on the water
    for (x, y) in ellipse_px(cx + 0.5, cy + 0.5, rx, ry):
        dx, dy = x + 0.5 - (cx + 0.5), y + 0.5 - (cy + 0.5)
        # the notch: a wedge to its right
        if dx > 0 and abs(dy) < dx * 0.35:
            continue
        r = (dx / rx) ** 2 + (dy / ry) ** 2
        if r > 0.7 and (dx + dy > 0):
            col = 'm1'
        elif dx + dy * 1.4 < -2.5:
            col = 'm3'
        else:
            col = 'm2'
        g.put(x, y, col)
    if bloom:
        for (dx, dy, col) in ((-1, -1, 'lp'), (0, -2, 'lp'), (1, -1, 'lp'), (0, -1, 'x'), (-1, 0, 'lp'), (1, 0, 'lp')):
            g.put(cx - 2 + dx, cy + dy, col)


def paint_lilies(g):
    for (x, y, b) in LILIES:
        lily(g, x, y, b)


# ----------------------------------------------------------- puddles --
PUDDLES = [(100, 238, 7), (378, 124, 6), (300, 250, 5)]


def paint_puddles(g):
    """standing water in the floor's low places: the stone round it wet
    and dark, the water darker still, a streak of reflected light"""
    for (cx, cy, r) in PUDDLES:
        wet = set(ellipse_px(cx + 0.5, cy + 0.5, r + 2, r * 0.45 + 1.5))
        pool = set(ellipse_px(cx + 0.5, cy + 0.5, r, r * 0.45))
        for (x, y) in wet - pool:
            c = g.get(x, y)
            if c and c[0] == 'g' and c != 'g0':
                g.put(x, y, shift(c, -1))
        for (x, y) in pool:
            edge = (x, y - 1) not in pool or (x - 1, y) not in pool or (x + 1, y) not in pool
            col = 'g1' if ((x, y + 1) not in pool) else ('a2' if not edge else 'a2')
            # the streak: the room's light caught across its upper middle
            if (x, y - 1) in pool and (x, y - 2) not in pool and abs(x - cx) < r * 0.5:
                col = 'a3'
            g.put(x, y, col)


# ------------------------------------------------- the lower floor's corners --
def paint_lower_corners(g):
    """crates and barrels against the side walls of the lower floor"""
    shadow(g, 34, 254, 16, 3)
    g.blit(SP.CRATE, 18, 240)
    g.blit(SP.BARREL, 33, 242)
    shadow(g, 446, 254, 14, 3)
    g.blit(SP.BARREL, 432, 242)
    g.blit(SP.BARREL, 446, 242)


# ---------------------------------------------------------- the painting --
_STATIC = None


def paint_static():
    """everything that does not move, once: (ground under, ground over, overlay)"""
    g = Canvas(PW, PH)
    over = Canvas(PW, PH)
    o = Canvas(PW, PH)
    paint_floor(g)
    paint_back_wall(g)
    paint_banks(g)
    paint_pipes(g)
    paint_arch(g)
    paint_basin_rim(g)
    paint_hole(g, o)
    paint_banners(g)
    paint_lanterns_static(g)
    paint_drain(g)
    paint_grates(g)
    paint_bridge(g, over)
    paint_spouts_static(g)
    paint_railings(g, over, o)
    paint_ladder(over)
    paint_stall(g, o)
    paint_corner(g, o)
    paint_puddles(g)
    paint_lower_corners(g)
    paint_side_walls(g)
    return g, over, o


def paint(t=0):
    """the hall at animation tick t: (ground, overlay)"""
    global _STATIC
    if _STATIC is None:
        _STATIC = paint_static()
    g0, over, o = _STATIC
    g = g0.copy()
    paint_water(g, t)
    paint_falls(g, t)
    paint_basin(g, t)
    paint_lanterns(g, t)
    paint_spouts(g, t)
    paint_corner_anim(g, t)
    paint_lilies(g)
    for y in range(PH):
        row = over.px[y]
        for x in range(PW):
            if row[x] is not None:
                g.px[y][x] = row[x]
    return g, o.copy()
