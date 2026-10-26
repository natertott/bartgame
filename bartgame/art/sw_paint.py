"""The Drain's painter: a canvas of named colours and the drawing tools the
hall is painted with (art/sw_hall.py).

Every colour is a name in COLORS, on the GBA's 5-bit grid, so what is
painted is what the hardware shows. Ramps order a material's colours
dark to light, so light and shadow are a step along the ramp, never a
new colour. The hall is painted at native resolution, a pixel at a time,
in clusters and clean edges.
"""
import math

# ------------------------------------------------------------- colours --
# 5-bit values (multiples of 8): what is painted is what the screen shows
COLORS = {
    # one grey for every stone and the iron, hue-shifted: blue in the
    # dark (the walls, the mortar, the iron), warmer in the light (the
    # floor, the dressed stone of arches and copings)
    'g0': (8, 8, 16), 'g1': (24, 32, 40), 'g2': (40, 48, 64), 'g3': (64, 72, 80),
    'g4': (88, 96, 96), 'g5': (120, 128, 120), 'g6': (160, 160, 144), 'g7': (208, 200, 176),
    # one white: foam, a flame's heart, a sparkle, a gleam
    'x': (248, 248, 232),
    # moss
    'm1': (32, 72, 32), 'm2': (56, 104, 40), 'm3': (104, 152, 48),
    # brass and copper: pipes, caps, rods, frames, gold
    'b1': (80, 48, 16), 'b2': (128, 80, 24), 'b3': (176, 112, 32), 'b4': (216, 152, 48), 'b5': (248, 200, 96),
    # water (its teal also dyes a banner)
    'a1': (8, 40, 56), 'a2': (8, 64, 80), 'a3': (16, 96, 104), 'a4': (24, 128, 128),
    'a5': (40, 168, 152), 'a6': (80, 208, 184), 'a7': (160, 240, 224),
    # wood
    'd1': (64, 32, 16), 'd2': (96, 56, 24), 'd3': (136, 88, 40), 'd4': (176, 120, 64),
    # the Peddler's red
    'r1': (96, 24, 24), 'r2': (144, 32, 32), 'r3': (192, 56, 40), 'r4': (232, 104, 64),
    # the Gatekeeper's purple
    'p1': (56, 24, 80), 'p2': (88, 40, 112), 'p3': (128, 64, 152), 'p4': (168, 104, 192),
    # flame
    'y1': (248, 168, 48), 'y2': (248, 224, 120),
    # bone, a pink bloom
    'k2': (200, 184, 152), 'lp': (232, 128, 160),
}
for _n, _c in COLORS.items():
    assert all(v % 8 == 0 for v in _c), _n

RAMPS = {
    'g': ['g0', 'g1', 'g2', 'g3', 'g4', 'g5', 'g6', 'g7'],
    'm': ['g1', 'm1', 'm2', 'm3'],
    'b': ['g0', 'b1', 'b2', 'b3', 'b4', 'b5', 'x'],
    'a': ['g0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'x'],
    'd': ['g0', 'd1', 'd2', 'd3', 'd4'],
    'r': ['g0', 'r1', 'r2', 'r3', 'r4'],
    'p': ['g0', 'p1', 'p2', 'p3', 'p4'],
    'y': ['y1', 'y2', 'x'],
}
RAMP_OF = {}
for _r, _names in RAMPS.items():
    for _i, _n in enumerate(_names):
        RAMP_OF.setdefault(_n, (_r, _i))
# the shared colours shift along the grey
for _n in ('g0', 'g1'):
    RAMP_OF[_n] = ('g', RAMPS['g'].index(_n))


def shift(name, d):
    """the colour d steps lighter (or darker) along its own ramp"""
    if name is None or d == 0 or name not in RAMP_OF:
        return name
    r, i = RAMP_OF[name]
    ramp = RAMPS[r]
    return ramp[max(0, min(len(ramp) - 1, i + d))]


def rnd(x, y, salt=0):
    """a fixed pseudo-random number in [0, 1) for a pixel"""
    h = (x * 374761393 + y * 668265263 + salt * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFF) / float(0x1000000)


BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dither(x, y, level):
    """true where an ordered dither of level (0..1) is on"""
    return (BAYER4[y & 3][x & 3] + 0.5) / 16.0 < level


# -------------------------------------------------------------- canvas --
class Canvas:
    """a grid of colour names; None is clear"""

    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.px = [[fill] * w for _ in range(h)]

    def copy(self):
        c = Canvas(self.w, self.h)
        c.px = [row[:] for row in self.px]
        return c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return None

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.px[y][x] = c

    def clear(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = None

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, c)

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def shift(self, x, y, d):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = shift(self.px[y][x], d)

    def blit(self, spr, x, y, flip=False):
        for j, row in enumerate(spr):
            for i, c in enumerate(row[::-1] if flip else row):
                if c is not None:
                    self.put(x + i, y + j, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for (x, y) in ellipse_px(cx, cy, rx, ry):
            self.put(x, y, c)

    def to_image(self):
        from PIL import Image
        im = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        p = im.load()
        for y in range(self.h):
            row = self.px[y]
            for x in range(self.w):
                c = row[x]
                if c is not None:
                    r, g, b = COLORS[c]
                    p[x, y] = (r | r >> 5, g | g >> 5, b | b >> 5, 255)
        return im


def ellipse_px(cx, cy, rx, ry):
    """the pixels inside an ellipse centred on (cx, cy), half-pixel exact"""
    out = []
    for y in range(int(math.floor(cy - ry)), int(math.ceil(cy + ry)) + 1):
        for x in range(int(math.floor(cx - rx)), int(math.ceil(cx + rx)) + 1):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if dx * dx + dy * dy <= 1.0:
                out.append((x, y))
    return out


def sprite(legend, text):
    """a letter drawing to rows of colour names; '.' is clear"""
    out = []
    for ln in text.strip('\n').splitlines():
        ln = ln.strip()
        if not ln:
            continue
        out.append([None if ch == '.' else legend[ch] for ch in ln])
    w = max(len(r) for r in out)
    assert all(len(r) == w for r in out), ('ragged sprite', [len(r) for r in out])
    return out


def flip(spr):
    return [row[::-1] for row in spr]


# --------------------------------------------------------------- tubes --
# Pipes, posts, barrels and rails are tubes: shaded by the surface normal
# against one light from the upper left and in front, then stepped onto
# the material's ramp, so every bend and cap is lit the same way.
LIGHT = (-0.55, -0.62, 0.56)
_ll = math.sqrt(sum(v * v for v in LIGHT))
LIGHT = tuple(v / _ll for v in LIGHT)


def lit(nx, ny, nz):
    """diffuse light on a unit normal, 0..1, with a little ambient"""
    d = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
    return 0.18 + 0.82 * max(0.0, d)


def tone(ramp, level, steps=None):
    """a light level 0..1 to a colour of the ramp (skipping its outline)"""
    names = RAMPS[ramp] if steps is None else steps
    i = int(level * (len(names) - 0.001))
    return names[max(0, min(len(names) - 1, i))]


class Path:
    """a tube's centre line: straight runs joined by quarter bends of radius r"""

    def __init__(self, pts, r=6):
        self.pts = pts
        self.r = r
        self.parts = []  # ('seg', a, b) or ('arc', centre, radius, a0, a1)
        n = len(pts)
        starts = [pts[0]]
        ends = []
        for i in range(1, n - 1):
            p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
            d1 = _unit(p1[0] - p0[0], p1[1] - p0[1])
            d2 = _unit(p2[0] - p1[0], p2[1] - p1[1])
            a = (p1[0] - d1[0] * r, p1[1] - d1[1] * r)
            b = (p1[0] + d2[0] * r, p1[1] + d2[1] * r)
            ends.append(a)
            starts.append(b)
            # the bend's centre is r from both runs
            cx, cy = a[0] + d2[0] * r, a[1] + d2[1] * r
            self.parts.append(('arc', (cx, cy), r, a, b))
        ends.append(pts[-1])
        for s, e in zip(starts, ends):
            self.parts.append(('seg', s, e))

    def nearest(self, x, y):
        """distance to the line, the across vector there, and where along it"""
        best = None
        for p in self.parts:
            if p[0] == 'seg':
                (ax, ay), (bx, by) = p[1], p[2]
                dx, dy = bx - ax, by - ay
                L2 = dx * dx + dy * dy or 1e-9
                t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
                qx, qy = ax + t * dx, ay + t * dy
                d = math.hypot(x - qx, y - qy)
                tx, ty = _unit(dx, dy)
                across = (-ty, tx)
            else:
                (cx, cy), r, a, b = p[1], p[2], p[3], p[4]
                vx, vy = x - cx, y - cy
                L = math.hypot(vx, vy) or 1e-9
                ux, uy = vx / L, vy / L
                # only the quarter between a and b
                ua = _unit(a[0] - cx, a[1] - cy)
                ubv = _unit(b[0] - cx, b[1] - cy)
                if (ux * ua[0] + uy * ua[1]) < -1e-6 or (ux * ubv[0] + uy * ubv[1]) < -1e-6:
                    continue
                qx, qy = cx + ux * r, cy + uy * r
                d = abs(L - r)
                across = (ux, uy)
            if best is None or d < best[0]:
                best = (d, (x - qx, y - qy), across)
        return best


def _unit(x, y):
    L = math.hypot(x, y) or 1e-9
    return (x / L, y / L)


def tube(cv, path, width, ramp='b', outline='b0', steps=None, mask=None):
    """paint a tube of the given width along a Path"""
    hw = width / 2.0
    xs = [p[0] for p in path.pts]
    ys = [p[1] for p in path.pts]
    for y in range(int(min(ys) - hw - 2), int(max(ys) + hw + 2)):
        for x in range(int(min(xs) - hw - 2), int(max(xs) + hw + 2)):
            n = path.nearest(x + 0.5, y + 0.5)
            if n is None:
                continue
            d, (ox, oy), (ax, ay) = n
            if d > hw:
                continue
            if mask and not mask(x, y):
                continue
            s = (ox * ax + oy * ay) / hw  # -1..1 across the tube
            s = max(-1.0, min(1.0, s))
            if hw - d < 1.0:
                cv.put(x, y, outline)
                continue
            nz = math.sqrt(max(0.0, 1 - s * s))
            cv.put(x, y, tone(ramp, lit(ax * s, ay * s, nz), steps))


def cylinder_x(cv, x0, y0, w, h, ramp, outline, steps=None):
    """an upright cylinder seen from the front: shaded across x"""
    for x in range(x0, x0 + w):
        s = ((x + 0.5 - x0) / w) * 2 - 1
        nz = math.sqrt(max(0.0, 1 - s * s))
        c = tone(ramp, lit(s, 0, nz), steps)
        for y in range(y0, y0 + h):
            cv.put(x, y, outline if x in (x0, x0 + w - 1) else c)


def cylinder_y(cv, x0, y0, w, h, ramp, outline, steps=None):
    """a lying cylinder seen from above: shaded across y"""
    for y in range(y0, y0 + h):
        s = ((y + 0.5 - y0) / h) * 2 - 1
        nz = math.sqrt(max(0.0, 1 - s * s))
        c = tone(ramp, lit(0, s, nz), steps)
        for x in range(x0, x0 + w):
            cv.put(x, y, outline if y in (y0, y0 + h - 1) else c)


def dome(cv, cx, cy, rx, ry, ramp, outline, steps=None):
    """a lit dome or ball"""
    for (x, y) in ellipse_px(cx, cy, rx, ry):
        dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        r2 = dx * dx + dy * dy
        if r2 > 0.72 and _edge(x, y, cx, cy, rx, ry):
            cv.put(x, y, outline)
            continue
        nz = math.sqrt(max(0.0, 1 - min(1.0, r2)))
        cv.put(x, y, tone(ramp, lit(dx, dy, nz), steps))


def _edge(x, y, cx, cy, rx, ry):
    """is this pixel on the rim of the ellipse (a neighbour outside it)"""
    for (ex, ey) in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        dx, dy = (ex + 0.5 - cx) / rx, (ey + 0.5 - cy) / ry
        if dx * dx + dy * dy > 1.0:
            return True
    return False
