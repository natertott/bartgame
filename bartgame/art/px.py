"""Pixel helpers for BARTGAME's art.

Art is rows of hex digits, one per pixel ('.' is transparent). To keep
the drawings readable they are written with letter legends and turned
into hex here. The helpers add outlines, flip, shift and compose rows,
and a small Canvas draws procedural textures with the same discipline:
flat fills, one-pixel outlines, three tones and a gleam.
"""


def L(legend, s):
    """A multi-line letter drawing to hex rows. legend: {char: index}.
    '.' stays transparent; blank lines and indentation are ignored."""
    out = []
    for ln in s.strip('\n').splitlines():
        ln = ln.strip()
        if not ln:
            continue
        row = []
        for ch in ln:
            if ch == '.':
                row.append('.')
            elif ch == ' ' and ' ' not in legend:
                row.append(' ')  # left for a later replace; the builder reads it as clear
            elif ch in legend:
                v = legend[ch]
                row.append('%x' % v if isinstance(v, int) else v)
            elif ch in '0123456789abcdef':
                row.append(ch)
            else:
                raise ValueError('unknown pixel %r in %r' % (ch, ln))
        out.append(''.join(row))
    return out


def grid(rows):
    return [[-1 if ch == '.' else int(ch, 16) for ch in r] for r in rows]


def rows(g):
    return [''.join('.' if c < 0 else '%x' % c for c in r) for r in g]


def blank(w, h):
    return ['.' * w] * h


def hflip(rs):
    return [r[::-1] for r in rs]


def vflip(rs):
    return rs[::-1]


def pad(rs, w, h, dx=0, dy=0):
    """Fit rows into a w x h frame, placed at (dx, dy)."""
    out = blank(w, h)
    return compose(out, rs, dx, dy)


def shift(rs, dx, dy):
    w, h = len(rs[0]), len(rs)
    return compose(blank(w, h), rs, dx, dy)


def compose(base, top, dx=0, dy=0):
    """Draw top over base at (dx, dy); '.' in top shows base."""
    g = [list(r) for r in base]
    bw, bh = len(base[0]), len(base)
    for y, r in enumerate(top):
        yy = y + dy
        if yy < 0 or yy >= bh:
            continue
        for x, ch in enumerate(r):
            xx = x + dx
            if ch == '.' or xx < 0 or xx >= bw:
                continue
            g[yy][xx] = ch
    return [''.join(r) for r in g]


def stack(*layers):
    """compose several same-size layers, first at the bottom"""
    out = layers[0]
    for l in layers[1:]:
        out = compose(out, l)
    return out


def outline(rs, col, diagonal=False, only=None):
    """Add a one-pixel outline of color col around every opaque pixel,
    on transparent pixels only. only: a set of (x, y) to restrict to."""
    g = grid(rs)
    h, w = len(g), len(g[0])
    c = col if isinstance(col, int) else int(col, 16)
    add = set()
    n4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    n8 = n4 + ((1, 1), (-1, -1), (1, -1), (-1, 1))
    for y in range(h):
        for x in range(w):
            if g[y][x] < 0:
                continue
            for dx, dy in (n8 if diagonal else n4):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and g[yy][xx] < 0:
                    add.add((xx, yy))
    for (x, y) in add:
        if only is None or (x, y) in only:
            g[y][x] = c
    return rows(g)


def remap(rs, mapping):
    """Replace hex digits: mapping {from_char: to_char}."""
    return [''.join(mapping.get(ch, ch) for ch in r) for r in rs]


def opaque(rs, fill):
    """Fill transparent pixels with a color (for ground tiles)."""
    f = fill if isinstance(fill, str) else '%x' % fill
    return [r.replace('.', f) for r in rs]


def mirror_lr(rs):
    """Left half drawn, right half mirrored: symmetrical sprites."""
    w = len(rs[0])
    half = w // 2
    return [r[:half] + r[:half][::-1] for r in rs]


class Canvas:
    """A w x h grid of palette indices; -1 is transparent."""

    def __init__(self, w, h, fill=-1):
        self.w, self.h = w, h
        self.g = [[fill] * w for _ in range(h)]

    @classmethod
    def from_rows(cls, rs):
        c = cls(len(rs[0]), len(rs))
        c.g = grid(rs)
        return c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.g[y][x]
        return -1

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def hline(self, x0, x1, y, c):
        for x in range(x0, x1 + 1):
            self.set(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(y0, y1 + 1):
            self.set(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c):
        """A filled ellipse; cx, cy may be half-integers (x.5) for even widths."""
        for y in range(self.h):
            for x in range(self.w):
                dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                if dx * dx + dy * dy <= 1.0:
                    self.set(x, y, c)

    def blit(self, rs, dx=0, dy=0):
        for y, r in enumerate(rs):
            for x, ch in enumerate(r):
                if ch != '.':
                    self.set(x + dx, y + dy, int(ch, 16))

    def replace(self, a, b):
        for y in range(self.h):
            for x in range(self.w):
                if self.g[y][x] == a:
                    self.g[y][x] = b

    def outline(self, c, diagonal=False):
        self.g = grid(outline(rows(self.g), c, diagonal))

    def rows(self):
        return rows(self.g)

    def wrap_set(self, x, y, c):
        """set with toroidal wrap: seamless tiles"""
        self.g[y % self.h][x % self.w] = c

    def wrap_blit(self, rs, dx, dy):
        for y, r in enumerate(rs):
            for x, ch in enumerate(r):
                if ch != '.':
                    self.wrap_set(x + dx, y + dy, int(ch, 16))


def ball(c, cx, cy, rx, ry, tones, gleam=True):
    """A lit sphere on canvas c: tones = (deep, dark, mid, light, bright).
    Light from the upper left; a deep rim at the lower right."""
    deep, dark, mid, light, bright = tones
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            e = dx * dx + dy * dy
            if e > 1.0:
                continue
            t = (dx + dy) / 2.0
            if gleam and t < -0.5 and e < 0.5:
                col = bright
            elif t < -0.2 and e < 0.85:
                col = light
            elif t > 0.5 and e > 0.55:
                col = deep
            elif t > 0.18 or (e > 0.8 and t > 0):
                col = dark
            else:
                col = mid
            c.set(x, y, col)
