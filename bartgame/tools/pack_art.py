"""Cutting the sprite pack's illustrated sheets (art/ref/pack_art/) into
game frames, for tools/import_pack.py.

An illustrated sheet is one large RGBA picture, one figure per cell of a
grid, drawn at several screen pixels per art pixel, with faint haze and
glow round the figures. The steps:

  solid()    the haze gone: alpha below 200 clear, the rest opaque
  segment()  the cells, given how many there are in each row: each row
             band and each cell is cut at the emptiest place between its
             neighbours (smoothed, so a dashed or speckled figure is not
             split), and each cell keeps its tight box and its region
  place()    a cell scaled into a frame by area averaging, sampling the
             cell's region only; a box that is mostly near-black takes the
             median of its darks, so outlines and eyes survive
  derive()   a palette group: one outline colour and fourteen by k-means
             in Lab, each colour weighing as the square root of its area,
             so small accents keep a colour of their own
  quantize() nearest palette colour in Lab

Needs numpy and Pillow."""
import numpy as np
from PIL import Image


def load(path):
    return np.array(Image.open(path).convert('RGBA')).astype(float)


def solid(im, thr=200):
    a = im.copy()
    a[:, :, 3] = np.where(a[:, :, 3] >= thr, 255.0, 0.0)
    return a


# ---------------------------------------------------------------- cells --
def _profile(mask, axis, k):
    p = mask.sum(axis=axis).astype(float)
    return np.convolve(p, np.ones(k) / k, mode='same') if k > 1 else p


def _cuts(p, n, lo, hi):
    """n-1 cut positions in p[lo:hi], emptiest first and, among equally
    empty places, nearest the middle of a gap; spaced at least half a
    cell apart"""
    if n <= 1:
        return []
    minsep = (hi - lo) / float(n) * 0.55
    occ = p > 1e-9
    dist = np.zeros(len(p))
    last = -10 ** 6
    for i in range(len(p)):
        last = i if occ[i] else last
        dist[i] = i - last
    last = 10 ** 6
    for i in range(len(p) - 1, -1, -1):
        last = i if occ[i] else last
        dist[i] = min(dist[i], last - i)
    score = p - 1e-3 * np.minimum(dist, 1000)
    chosen = []
    for i in np.argsort(score[lo:hi], kind='stable') + lo:
        if i - lo < minsep * 0.5 or hi - i < minsep * 0.5:
            continue
        if all(abs(i - c) >= minsep for c in chosen):
            chosen.append(int(i))
        if len(chosen) == n - 1:
            break
    return sorted(chosen)


def segment(src, counts, smooth=7, xcuts=None):
    """rows of cells (x0, y0, x1, y1, region) for a sheet with counts[r]
    cells in row r. xcuts: {row: {cut index: x}} to place a cut by hand
    where a figure's effect reaches into its neighbour's gap"""
    m = src[:, :, 3] > 0
    ys = np.nonzero(m.any(axis=1))[0]
    y0, y1 = ys.min(), ys.max() + 1
    yc = [y0] + _cuts(_profile(m, 1, smooth), len(counts), y0, y1) + [y1]
    rows = []
    for r, n in enumerate(counts):
        a, b = yc[r], yc[r + 1]
        band = m[a:b]
        xs = np.nonzero(band.any(axis=0))[0]
        x0, x1 = xs.min(), xs.max() + 1
        xc = [x0] + _cuts(_profile(band, 0, smooth), n, x0, x1) + [x1]
        for i, x in (xcuts or {}).get(r, {}).items():
            xc[i + 1] = x
        row = []
        for c in range(n):
            sub = band[:, xc[c]:xc[c + 1]]
            yy, xx = np.nonzero(sub)
            assert len(xx), ('empty cell', r, c)
            row.append((xc[c] + xx.min(), a + yy.min(), xc[c] + xx.max() + 1, a + yy.max() + 1, (xc[c], a, xc[c + 1], b)))
        rows.append(row)
    return rows


def flat(rows):
    return [c for r in rows for c in r]


# ---------------------------------------------------------- downscaling --
def lum(c):
    return 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]


def down(src, W, H, scale, ox, oy, dark_lum=45, dark_frac=None):
    """a W x H frame: target pixel (x, y) is the source box from
    (ox + x/scale, oy + y/scale), area averaged with alpha weights; a box
    that is dark_frac or more near-black takes the median of its darks.
    dark_frac defaults by how hard the reduction is (source pixels per
    frame pixel): 0.3 up to 6, 0.5 up to 10, 0.7 beyond, so a heavily
    reduced figure keeps its colours as well as its outline"""
    if dark_frac is None:
        k = 1.0 / scale
        dark_frac = 0.30 if k <= 6 else 0.5 if k <= 10 else 0.7
    out = np.zeros((H, W, 4))
    h, w = src.shape[:2]
    L = lum(src[:, :, :3])
    for y in range(H):
        sy0, sy1 = oy + y / scale, oy + (y + 1) / scale
        b0, b1 = max(int(np.floor(sy0)), 0), min(int(np.ceil(sy1)), h)
        if b1 <= b0:
            continue
        wy = np.clip(np.minimum(np.arange(b0, b1) + 1, sy1) - np.maximum(np.arange(b0, b1), sy0), 0, 1)
        for x in range(W):
            sx0, sx1 = ox + x / scale, ox + (x + 1) / scale
            a0, a1 = max(int(np.floor(sx0)), 0), min(int(np.ceil(sx1)), w)
            if a1 <= a0:
                continue
            wx = np.clip(np.minimum(np.arange(a0, a1) + 1, sx1) - np.maximum(np.arange(a0, a1), sx0), 0, 1)
            wgt = wy[:, None] * wx[None, :]
            blk = src[b0:b1, a0:a1]
            al = blk[:, :, 3] / 255.0 * wgt
            tot = wgt.sum()
            if tot <= 0 or al.sum() <= 0:
                continue
            out[y, x, :3] = (blk[:, :, :3] * al[:, :, None]).sum(axis=(0, 1)) / al.sum()
            out[y, x, 3] = 255.0 * al.sum() / tot
            if out[y, x, 3] < 100:
                continue
            op = blk[:, :, 3] > 128
            dk = op & (L[b0:b1, a0:a1] < dark_lum)
            if dk.sum() >= dark_frac * max(1, op.sum()):
                out[y, x, :3] = np.median(blk[dk][:, :3], axis=0)
                out[y, x, 3] = 255.0
    return out


def place(src, cell, W, H, scale, how='bottom', anchor_x=None, base_y=None, dy=0, region=None):
    """a cell into a W x H frame at scale. how: 'bottom' (base_y, by
    default the tight box's foot, on the last row) or 'center'. anchor_x:
    the source x on the frame's middle (default the tight box's middle).
    Only the cell's region (or region) is sampled."""
    x0, y0, x1, y1, reg = cell
    rx0, ry0, rx1, ry1 = region or reg
    cx = anchor_x if anchor_x is not None else (x0 + x1) / 2.0
    ox = cx - (W / 2.0) / scale
    if how == 'center':
        oy = (y0 + y1) / 2.0 - (H / 2.0) / scale
    else:
        oy = (base_y if base_y is not None else y1) - H / scale
    return down(src[ry0:ry1, rx0:rx1], W, H, scale, ox - rx0, oy - dy / scale - ry0)


def fit(src, cell, W, H, margin=1, how='center'):
    """a cell scaled to fill the frame"""
    x0, y0, x1, y1, _ = cell
    return place(src, cell, W, H, min((W - margin) / float(x1 - x0), (H - margin) / float(y1 - y0)), how)


def head_x(src, cell, frac=0.45):
    """the middle of the upper part of a figure: what a standing figure is
    centred on, so an outflung arm or sword does not shift it"""
    x0, y0, x1, y1, _ = cell
    m = src[y0:y1, x0:x1, 3] > 0
    top = m[:max(1, int(m.shape[0] * frac))]
    ys, xs = np.nonzero(top if top.any() else m)
    return x0 + xs.mean()


def hflip(f):
    return f[:, ::-1].copy()


def raised(f, n):
    g = np.zeros_like(f)
    g[:-n] = f[n:]
    return g


# --------------------------------------------------------------- colour --
def to_lab(rgb):
    c = np.asarray(rgb, float) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.9505, 1.0, 1.089])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116.0)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def kmeans(pixels, k, power=0.5, iters=30):
    """k colours for an (N,3) RGB array: buckets of 5 bits a channel, each
    weighted by count**power, weighted k-means in Lab from a farthest-point
    start. Deterministic."""
    q = pixels.astype(int) >> 3
    key = q[:, 0] * 1024 + q[:, 1] * 32 + q[:, 2]
    uk, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    mean_rgb = np.zeros((len(uk), 3))
    np.add.at(mean_rgb, inv, pixels.astype(float))
    mean_rgb /= cnt[:, None]
    X = to_lab(mean_rgb)
    wgt = cnt.astype(float) ** power
    k = min(k, len(uk))
    cen = [X[np.argmax(wgt)]]
    for _ in range(k - 1):
        d = np.min([((X - c) ** 2).sum(axis=1) for c in cen], axis=0) * wgt
        cen.append(X[np.argmax(d)])
    cen = np.array(cen)
    for _ in range(iters):
        lab = np.argmin(((X[:, None, :] - cen[None]) ** 2).sum(axis=2), axis=1)
        for j in range(k):
            sel = lab == j
            if sel.any():
                cen[j] = (X[sel] * wgt[sel, None]).sum(axis=0) / wgt[sel].sum()
    lab = np.argmin(((X[:, None, :] - cen[None]) ** 2).sum(axis=2), axis=1)
    out = []
    for j in range(k):
        sel = lab == j
        if sel.any():
            out.append(tuple(int(round(v)) for v in (mean_rgb[sel] * wgt[sel, None]).sum(axis=0) / wgt[sel].sum()))
    return out


def derive(frames, n=15, dark_lum=40):
    pix = np.concatenate([f[f[:, :, 3] >= 128][:, :3] for f in frames])
    L = lum(pix)
    dark, rest = pix[L < dark_lum], pix[L >= dark_lum]
    outline = tuple(int(v) for v in np.median(dark, axis=0)) if len(dark) else (16, 12, 20)
    cols = kmeans(rest, n - 1) if len(rest) else []
    cols.sort(key=lambda c: lum(np.array(c, float)))
    return [outline] + cols


def quantize(f, pal):
    P = to_lab(np.array(pal, float))
    out = np.zeros(f.shape[:2], np.uint8)
    m = f[:, :, 3] >= 128
    if m.any():
        L = to_lab(f[m][:, :3])
        out[m] = np.argmin(((L[:, None, :] - P[None]) ** 2).sum(axis=2), axis=1) + 1
    return out


def indexed_to_rgba(idx, pal):
    f = np.zeros(idx.shape + (4,))
    for y in range(idx.shape[0]):
        for x in range(idx.shape[1]):
            if idx[y, x]:
                f[y, x, :3] = pal[idx[y, x] - 1]
                f[y, x, 3] = 255
    return f
