"""A terrain painter: tiles drawn in palette indices on numpy arrays.

Everything that repeats is drawn on a torus (coordinates wrap), so a tile
meets copies of itself without a seam. The pieces:

  vnoise()     value noise that repeats every w x h pixels
  dither()     a field turned into two indices by a 4x4 Bayer matrix, so
               a gradient between two colours is a pattern, not a line
  stamp()      a small drawing of roles ('d' dark, 'm' mid, 'l' light,
               'h' highlight, 'o' outline) put down with wrapping
  scatter()    positions spread apart, deterministic, wrapping
  clump()      a round lit clump (a leaf mass, a bush, a stone)
  outline()    a ring of one index round a mask
  side_masks() the fifteen bands of an edge family: one fixed wavy band
  corner_masks()  per side and per corner, so a band meets its neighbour's,
               and each 8x8 quarter depends only on the two sides (or the
               one corner) that touch it, which lets the build share them
  rows()       an index array as the rows of hex digits tiles.py uses

Needs numpy."""
import numpy as np

B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 + 1 / 32.0
SIDES = [(1, 'N'), (2, 'E'), (4, 'S'), (8, 'W')]


def rng(seed):
    return np.random.RandomState(seed & 0x7fffffff)


def vnoise(w, h, cx, cy, seed):
    """value noise in [0, 1] on a w x h torus, with cx by cy lattice cells"""
    r = rng(seed)
    g = r.rand(cy, cx)
    ys = (np.arange(h) + 0.5) * cy / float(h)
    xs = (np.arange(w) + 0.5) * cx / float(w)
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
    fy = ys - y0; fx = xs - x0
    sy = fy * fy * (3 - 2 * fy); sx = fx * fx * (3 - 2 * fx)
    a = g[y0[:, None] % cy, x0[None, :] % cx]
    b = g[y0[:, None] % cy, (x0[None, :] + 1) % cx]
    c = g[(y0[:, None] + 1) % cy, x0[None, :] % cx]
    d = g[(y0[:, None] + 1) % cy, (x0[None, :] + 1) % cx]
    top = a + (b - a) * sx[None, :]
    bot = c + (d - c) * sx[None, :]
    return top + (bot - top) * sy[:, None]


def fbm(w, h, seed, octaves=((2, 0.55), (4, 0.3), (8, 0.15))):
    f = np.zeros((h, w))
    for i, (n, amp) in enumerate(octaves):
        f += amp * vnoise(w, h, n, max(1, n * h // w), seed * 31 + i)
    return f / sum(a for _, a in octaves)


def dither(field, lo_idx, hi_idx, ox=0, oy=0):
    """hi where the field (0..1) beats the Bayer threshold, else lo"""
    h, w = field.shape
    t = B4[(np.arange(h)[:, None] + oy) % 4, (np.arange(w)[None, :] + ox) % 4]
    return np.where(field > t, hi_idx, lo_idx)


def levels(field, idxs, cuts, soft=0.06):
    """a field banded into indices at the cuts, each step dithered over
    a soft width so no band edge is a line"""
    h, w = field.shape
    t = B4[np.arange(h)[:, None] % 4, np.arange(w)[None, :] % 4]
    out = np.full((h, w), idxs[0], np.uint8)
    for c, i in zip(cuts, idxs[1:]):
        out = np.where(field + (t - 0.5) * soft * 2 > c, i, out)
    return out


def scatter(seed, n, w=16, h=16, mind=4, tries=400, avoid=None):
    """n points spread at least mind apart on the torus"""
    r = rng(seed)
    pts = []
    for _ in range(tries):
        if len(pts) >= n:
            break
        x, y = int(r.randint(w)), int(r.randint(h))
        if avoid is not None and avoid[y % h, x % w]:
            continue
        ok = True
        for (px, py) in pts:
            dx = min(abs(px - x), w - abs(px - x))
            dy = min(abs(py - y), h - abs(py - y))
            if dx * dx + dy * dy < mind * mind:
                ok = False
                break
        if ok:
            pts.append((x, y))
    return pts


def stamp(img, x, y, art, roles, wrap=True, mask=None):
    """put down a small drawing: art rows of role letters, '.' clear;
    roles maps letters to indices; (x, y) is the drawing's top left"""
    h, w = img.shape
    for dy, row in enumerate(art):
        for dx, ch in enumerate(row):
            if ch == '.' or ch not in roles:
                continue
            X, Y = x + dx, y + dy
            if wrap:
                X %= w; Y %= h
            elif not (0 <= X < w and 0 <= Y < h):
                continue
            if mask is not None and not mask[Y, X]:
                continue
            img[Y, X] = roles[ch]


def disc(w, h, cx, cy, rx, ry=None, wrap=False):
    ry = rx if ry is None else ry
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    dx = xx + 0.5 - cx
    dy = yy + 0.5 - cy
    if wrap:
        dx = (dx + w / 2.0) % w - w / 2.0
        dy = (dy + h / 2.0) % h - h / 2.0
    return (dx / rx) ** 2 + (dy / ry) ** 2 <= 1.0


def clump(img, cx, cy, r, ramp, wrap=False, rough=None, seed=0, light=(-0.45, -0.55), ry=None):
    """a round lit thing: ramp is (outline, dark, mid, light, highlight);
    lit from the upper left, an outline round it, a dark rim at the lower
    right. rough jitters the rim so leaves read as leaves."""
    h, w = img.shape
    ry = r if ry is None else ry
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    dx = xx + 0.5 - cx
    dy = yy + 0.5 - cy
    if wrap:
        dx = (dx + w / 2.0) % w - w / 2.0
        dy = (dy + h / 2.0) % h - h / 2.0
    d = np.sqrt((dx / r) ** 2 + (dy / ry) ** 2)
    if rough:
        ang = np.arctan2(dy, dx)
        rr = rng(seed)
        k = rr.randint(5, 9)
        ph = rr.rand() * 6.28
        d = d * (1 + rough * np.sin(ang * k + ph))
    body = d <= 1.0
    rim = (d > 1.0) & (d <= 1.0 + 1.2 / max(r, 1))
    lit = (dx * light[0] + dy * light[1]) / max(r, 1)  # high toward the light
    o, dk, md, lt, hl = ramp
    shade = np.where(lit > 0.55, hl, np.where(lit > 0.1, lt, np.where(lit > -0.45, md, dk)))
    # the darkest rim on the far side
    shade = np.where((d > 0.72) & (lit < -0.2), dk, shade)
    img[rim] = o
    img[body] = shade[body]
    return body | rim


def outline(img, mask, idx, diag=False):
    """idx round mask (outside it)"""
    m = mask
    n = np.zeros_like(m)
    n[1:, :] |= m[:-1, :]; n[:-1, :] |= m[1:, :]; n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]
    if diag:
        n[1:, 1:] |= m[:-1, :-1]; n[:-1, :-1] |= m[1:, 1:]; n[1:, :-1] |= m[:-1, 1:]; n[:-1, 1:] |= m[1:, :-1]
    ring = n & ~m
    img[ring] = idx
    return ring


def shift(a, dx, dy):
    return np.roll(np.roll(a, dy, axis=0), dx, axis=1)


# ------------------------------------------------------------ edge bands --
def profile(seed, lo, hi, n=16):
    """a band's depth along a side: lo..hi, smooth, periodic over n, and
    the same at both ends, so a run of tiles carries one wavy line"""
    f = vnoise(n, 1, 4, 1, seed)[0]
    d = np.round(lo + (hi - lo) * f).astype(int)
    return d


def side_masks(seed, lo=3, hi=6, round_r=3):
    """{bits: mask} for bits 1..15 (1 N, 2 E, 4 S, 8 W): the band along
    each marked side, its depth one fixed profile per side, and the corner
    where two marked sides meet rounded off"""
    P = {s: profile(seed * 7 + i, lo, hi) for i, (s, _) in enumerate(SIDES)}
    yy, xx = np.mgrid[0:16, 0:16]
    band = {
        1: yy < P[1][xx],
        4: (15 - yy) < P[4][xx],
        8: xx < P[8][yy],
        2: (15 - xx) < P[2][yy],
    }
    out = {}
    for bits in range(1, 16):
        m = np.zeros((16, 16), bool)
        for s in (1, 2, 4, 8):
            if bits & s:
                m |= band[s]
        # round the inner corner of the remaining ground where two bands meet
        for a, b, cx, cy in ((1, 8, 0, 0), (1, 2, 15, 0), (4, 8, 0, 15), (4, 2, 15, 15)):
            if bits & a and bits & b:
                da = P[a][cx if a in (1, 4) else cy]
                db = P[b][cy if b in (8, 2) else cx]
                ex = db + round_r if cx == 0 else 15 - db - round_r
                ey = da + round_r if cy == 0 else 15 - da - round_r
                sx = 1 if cx == 0 else -1
                sy = 1 if cy == 0 else -1
                corner = ((xx - ex) * sx < 0) & ((yy - ey) * sy < 0) & (((xx - ex) ** 2 + (yy - ey) ** 2) > round_r * round_r)
                m |= corner
        out[bits] = m
    return out


def corner_masks(seed, r=5):
    """{bits: mask} for bits 1..15 (1 NW, 2 NE, 4 SE, 8 SW): a rounded nick
    at each marked corner"""
    yy, xx = np.mgrid[0:16, 0:16].astype(float)
    rr = rng(seed)
    nick = {}
    for bit, (cx, cy) in ((1, (0, 0)), (2, (16, 0)), (4, (16, 16)), (8, (0, 16))):
        rad = r + rr.randint(-1, 2)
        nick[bit] = ((xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2) < rad * rad
    out = {}
    for bits in range(1, 16):
        m = np.zeros((16, 16), bool)
        for b in (1, 2, 4, 8):
            if bits & b:
                m |= nick[b]
        out[bits] = m
    return out


def band_fields(seed, lo=3, hi=6, r=2):
    """{bits: (mask, u)} for bits 1..15 (1 N, 2 E, 4 S, 8 W): the band
    along each marked side and u, 0 at the tile edge rising to 1 at the
    band's inner line (beyond 1 outside it), so a band can be drawn in
    layers (a lip, foam, shadow). Each side's depth is one fixed profile;
    where two marked sides meet, the corner of the rest is rounded with a
    fillet that stays inside its quarter."""
    P = {s: profile(seed * 7 + i, lo, hi) for i, (s, _) in enumerate(SIDES)}
    yy, xx = np.mgrid[0:16, 0:16]
    dist = {1: yy + 0.5, 4: 15.5 - yy, 8: xx + 0.5, 2: 15.5 - xx}
    along = {1: xx, 4: xx, 8: yy, 2: yy}
    us = {s: dist[s] / P[s][along[s]] for s in (1, 2, 4, 8)}
    out = {}
    for bits in range(1, 16):
        u = np.full((16, 16), 9.0)
        for s in (1, 2, 4, 8):
            if bits & s:
                u = np.minimum(u, us[s])
        for a, b, cx, cy in ((1, 8, 0, 0), (1, 2, 15, 0), (4, 8, 0, 15), (4, 2, 15, 15)):
            if bits & a and bits & b:
                da = P[a][cx]
                db = P[b][cy]
                ex = db + r - 0.5 if cx == 0 else 15.5 - db - r
                ey = da + r - 0.5 if cy == 0 else 15.5 - da - r
                sx = 1 if cx == 0 else -1
                sy = 1 if cy == 0 else -1
                reg = ((xx + 0.5 - ex) * sx < 0) & ((yy + 0.5 - ey) * sy < 0)
                d = np.sqrt((xx + 0.5 - ex) ** 2 + (yy + 0.5 - ey) ** 2)
                fill = reg & (d > r)
                u = np.where(fill, np.minimum(u, 1.0 - 0.5 * np.clip(d - r, 0, r) / r), u)
        out[bits] = (u < 1.0, u)
    return out


def nick_fields(seed, r=5):
    """{bits: (mask, u)} for bits 1..15 (1 NW, 2 NE, 4 SE, 8 SW): a
    rounded nick at each marked corner, u its distance over its radius"""
    yy, xx = np.mgrid[0:16, 0:16].astype(float)
    rr = rng(seed)
    us = {}
    for bit, (cx, cy) in ((1, (0, 0)), (2, (16, 0)), (4, (16, 16)), (8, (0, 16))):
        rad = r + rr.randint(-1, 2)
        us[bit] = np.sqrt((xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2) / rad
    out = {}
    for bits in range(1, 16):
        u = np.full((16, 16), 9.0)
        for b in (1, 2, 4, 8):
            if bits & b:
                u = np.minimum(u, us[b])
        out[bits] = (u < 1.0, u)
    return out


def edge_ring(mask):
    """(inner, outer): the band's pixels touching the rest, and the rest's
    pixels touching the band (4-neighbours, inside the tile)"""
    m = mask
    n = np.zeros_like(m)
    n[1:, :] |= m[:-1, :]; n[:-1, :] |= m[1:, :]; n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]
    o = ~m
    k = np.zeros_like(o)
    k[1:, :] |= o[:-1, :]; k[:-1, :] |= o[1:, :]; k[:, 1:] |= o[:, :-1]; k[:, :-1] |= o[:, 1:]
    return m & k, n & ~m


# ------------------------------------------------------------------ out --
def rows(img):
    return [''.join('%x' % int(v) for v in r) for r in img]


def slice16(img, tx, ty):
    return img[ty * 16:(ty + 1) * 16, tx * 16:(tx + 1) * 16]
