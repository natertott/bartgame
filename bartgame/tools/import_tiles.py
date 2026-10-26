"""Import the illustrated tile atlases into art/tile_art/.

    python3 tools/import_tiles.py [PREVIEW_DIR]

Sources, kept as delivered in art/ref/tile_art/:
  drain.webp    the Drain: floors, walls, water, the stall and its clutter
  blight.webp   the blight of the wood: its canopy, walls, grounds, pools,
                crystals and trees, and the wood's sparkles and mist

Each atlas draws a tile in a framed cell about four times its game size.
A cell's box is given roughly below and snapped to its frame line; the
art inside the frame is cut and reduced by area averaging, a box that is
mostly near-black keeping its darks (tools/pack_art.py). What a cell is:

  tile     the cell is the tile: squeezed to 16x16 (or the piece's size)
  object   a thing on a dark ground: the ground keyed away from the
           cell's edges, the thing fitted to the tile, bottom-aligned,
           and laid on a floor tile cut here
  overlay  the same, left transparent, for the overlay layer
  tree     the blighted tree: fitted to 48x64, its top three rows on the
           overlay and its roots laid on the blight floor

Palette groups are derived from what they hold (an outline and fourteen
colours by weighted k-means in Lab) and every tile is quantized to its
group. The output, which art/tiles_style.py reads:
  art/tile_art/tiles.json   the groups' colours and every tile's rows
With a PREVIEW_DIR, each tile is also written there as a PNG at 4x.
Needs numpy and Pillow.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pack_art as PA  # noqa: E402

ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'art', 'ref', 'tile_art')
OUT = os.path.join(ROOT, 'art', 'tile_art')


def load(name):
    return np.array(Image.open(os.path.join(SRC, name + '.webp')).convert('RGBA')).astype(float)


# ---------------------------------------------------------------- cells --
def frame_mask(a):
    mx = a[:, :, :3].max(axis=2)
    mn = a[:, :, :3].min(axis=2)
    return (mx - mn <= 20) & (mx >= 80) & (mx <= 170)


def snap(m, box, reach=8, inset=4):
    """the art inside a cell's frame: each edge of the rough box moved to
    the strongest frame line within reach, then inset past the line"""
    x0, y0, x1, y1 = box
    H, W = m.shape

    def best(cands, score, n):
        sc = [(score(c), c) for c in cands]
        s, c = max(sc)
        return c if s >= 0.35 * n else None

    ys = slice(y0 + 6, y1 - 6)
    xs = slice(x0 + 6, x1 - 6)
    L = best(range(max(0, x0 - reach), x0 + reach + 1), lambda x: m[ys, x].sum(), y1 - y0 - 12)
    R = best(range(x1 - 1 - reach, min(W, x1 + reach)), lambda x: m[ys, x].sum(), y1 - y0 - 12)
    T = best(range(max(0, y0 - reach), y0 + reach + 1), lambda y: m[y, xs].sum(), x1 - x0 - 12)
    B = best(range(y1 - 1 - reach, min(H, y1 + reach)), lambda y: m[y, xs].sum(), x1 - x0 - 12)
    return (x0 if L is None else L + inset, y0 if T is None else T + inset,
            x1 if R is None else R + 1 - inset, y1 if B is None else B + 1 - inset)


CRISP = True


def reduce(src, W, H, crisp=None, accent=False, dark_frac=None):
    """src (an RGBA crop) to W x H, separately in x and y: by area average,
    or (crisp) by the median of its middle tones. A mostly dark box keeps
    its darks; with accent, a strong bright accent that covers enough of a
    box keeps its colour (veins of light, glints, flames)"""
    crisp = CRISP if crisp is None else crisp
    h, w = src.shape[:2]
    out = np.zeros((H, W, 4))
    L = PA.lum(src[:, :, :3])
    sx, sy = w / float(W), h / float(H)
    k = max(sx, sy)
    if dark_frac is None:
        dark_frac = 0.30 if k <= 6 else 0.5 if k <= 10 else 0.7
    for y in range(H):
        a0, a1 = y * sy, (y + 1) * sy
        b0, b1 = int(np.floor(a0)), min(int(np.ceil(a1)), h)
        wy = np.clip(np.minimum(np.arange(b0, b1) + 1, a1) - np.maximum(np.arange(b0, b1), a0), 0, 1)
        for x in range(W):
            c0, c1 = x * sx, (x + 1) * sx
            d0, d1 = int(np.floor(c0)), min(int(np.ceil(c1)), w)
            wx = np.clip(np.minimum(np.arange(d0, d1) + 1, c1) - np.maximum(np.arange(d0, d1), c0), 0, 1)
            wgt = wy[:, None] * wx[None, :]
            blk = src[b0:b1, d0:d1]
            al = blk[:, :, 3] / 255.0 * wgt
            if al.sum() <= 0:
                continue
            out[y, x, :3] = (blk[:, :, :3] * al[:, :, None]).sum(axis=(0, 1)) / al.sum()
            out[y, x, 3] = 255.0 * al.sum() / wgt.sum()
            if out[y, x, 3] < 100:
                continue
            op = blk[:, :, 3] > 128
            if not op.any():
                continue
            bl = L[b0:b1, d0:d1]
            dk = op & (bl < 45)
            # a bright, strong accent (a vein of light, a glint) that covers
            # enough of the box keeps its colour
            rgb = blk[:, :, :3]
            chroma = rgb.max(axis=2) - rgb.min(axis=2)
            m = bl[op].mean()
            ac = op & (bl > m + 35) & ((chroma > 70) | (bl > 170))
            if accent and ac.sum() >= 0.18 * op.sum():
                out[y, x, :3] = np.median(rgb[ac], axis=0)
                out[y, x, 3] = 255.0
            elif dk.sum() >= dark_frac * op.sum():
                out[y, x, :3] = np.median(rgb[dk], axis=0)
                out[y, x, 3] = 255.0
            elif crisp:
                # the middle tones' median, not their mean, so two
                # materials in one box are not blended into a third
                mid = op & ~dk
                out[y, x, :3] = np.median(rgb[mid], axis=0)
    return out


def key(crop, tol=30):
    """the dark ground of a cell made transparent: flood from the edges
    over colours near the edges' own"""
    c = crop.copy()
    edge = np.concatenate([c[0, :, :3], c[-1, :, :3], c[:, 0, :3], c[:, -1, :3]])
    # the ground is the darker half of the edge: a thing may touch it
    el = PA.lum(edge)
    bg = np.median(edge[el <= np.percentile(el, 50)], axis=0)
    near = np.sqrt(((c[:, :, :3] - bg) ** 2).sum(axis=2)) < tol
    reg = np.zeros(near.shape, bool)
    reg[0, :] = near[0, :]; reg[-1, :] = near[-1, :]; reg[:, 0] = near[:, 0]; reg[:, -1] = near[:, -1]
    while True:
        g = reg.copy()
        g[1:, :] |= reg[:-1, :]; g[:-1, :] |= reg[1:, :]; g[:, 1:] |= reg[:, :-1]; g[:, :-1] |= reg[:, 1:]
        g &= near
        if (g == reg).all():
            break
        reg = g
    c[reg, 3] = 0
    return c


def fit(obj, W, H, margin=0, how='bottom', accent=False):
    """a keyed thing, cropped to what it shows, scaled to fit W x H"""
    ys, xs = np.nonzero(obj[:, :, 3] > 0)
    o = obj[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = o.shape[:2]
    s = min((W - margin) / float(w), (H - margin) / float(h))
    tw, th = max(1, int(round(w * s))), max(1, int(round(h * s)))
    r = reduce(o, tw, th, accent=accent, dark_frac=0.55)
    out = np.zeros((H, W, 4))
    ox = (W - tw) // 2
    oy = H - th if how == 'bottom' else (H - th) // 2
    out[oy:oy + th, ox:ox + tw] = r
    return out


def outlined(f, col=(10, 4, 16)):
    """a one-pixel dark line round what is drawn, so a dark thing stands
    off a dark ground"""
    g = f.copy()
    on = g[:, :, 3] >= 128
    near = np.zeros_like(on)
    near[1:, :] |= on[:-1, :]; near[:-1, :] |= on[1:, :]; near[:, 1:] |= on[:, :-1]; near[:, :-1] |= on[:, 1:]
    ring = near & ~on
    g[ring, :3] = col
    g[ring, 3] = 255.0
    return g


def over(base, top):
    """top over an opaque base"""
    a = (top[:, :, 3:4] >= 128)
    out = base.copy()
    out[:, :, :3] = np.where(a, top[:, :, :3], base[:, :, :3])
    return out


def opaque(f):
    g = f.copy()
    g[:, :, 3] = 255.0
    return g


def dither(f, lo=0.45, hi=0.8):
    """a haze for the overlay, by how far it is lit above the darkest of
    it: the thin parts on a checker, the dense parts whole, the rest clear"""
    g = f.copy()
    L = PA.lum(g[:, :, :3])
    on = g[:, :, 3] > 0
    if not on.any():
        return g
    l0, l1 = np.percentile(L[on], 5), L[on].max()
    d = np.clip((L - l0) / max(1.0, l1 - l0), 0, 1)
    yy, xx = np.mgrid[0:g.shape[0], 0:g.shape[1]]
    keep = on & ((d >= hi) | ((d >= lo) & ((xx + yy) % 2 == 0)))
    g[:, :, 3] = np.where(keep, 255.0, 0.0)
    return g


def glow_only(f, thr):
    """a glint without its soft halo: only the bright core kept"""
    g = f.copy()
    g[:, :, 3] = np.where((g[:, :, 3] > 0) & (PA.lum(g[:, :, :3]) >= thr), 255.0, 0.0)
    return g


def cracks(f, lum=95, chroma=80):
    """the bright, strong lines of a tile alone, the rest clear"""
    g = f.copy()
    rgb = g[:, :, :3]
    c = rgb.max(axis=2) - rgb.min(axis=2)
    g[:, :, 3] = np.where((PA.lum(rgb) >= lum) & (c >= chroma), 255.0, 0.0)
    return g


def split(box, cols, rows=1, inset=4):
    """a box cut into cols x rows cells, each inset past the lines between them"""
    x0, y0, x1, y1 = box
    w, h = (x1 - x0) / float(cols), (y1 - y0) / float(rows)
    return [(int(round(x0 + c * w)) + inset, int(round(y0 + r * h)) + inset, int(round(x0 + (c + 1) * w)) - inset, int(round(y0 + (r + 1) * h)) - inset)
            for r in range(rows) for c in range(cols)]


# ---------------------------------------------------------- the atlases --
def trim(a, m, box, most=6):
    """edge lines of the box that are the frame, not the art: almost all
    near-black or frame grey, taken off, up to most on a side"""
    x0, y0, x1, y1 = box
    L = PA.lum(a[:, :, :3])

    def framey(sl):
        return ((L[sl] < 30) | m[sl]).mean() >= 0.7

    for _ in range(most):
        if framey((slice(y0, y1), x0)):
            x0 += 1
    for _ in range(most):
        if framey((slice(y0, y1), x1 - 1)):
            x1 -= 1
    for _ in range(most):
        if framey((y0, slice(x0, x1))):
            y0 += 1
    for _ in range(most):
        if framey((y1 - 1, slice(x0, x1))):
            y1 -= 1
    return x0, y0, x1, y1


def seamless(f, k=4):
    """a texture made to repeat: each edge band blended toward the band
    across the tile from it, so the left edge meets the right and the top
    the bottom"""
    g = f.copy()
    H, W = g.shape[:2]
    for i in range(k):
        t = 0.5 * (1 - i / float(k))
        l, r = g[:, i].copy(), g[:, W - 1 - i].copy()
        g[:, i] = (1 - t) * l + t * r
        g[:, W - 1 - i] = (1 - t) * r + t * l
    for i in range(k):
        t = 0.5 * (1 - i / float(k))
        u, d = g[i].copy(), g[H - 1 - i].copy()
        g[i] = (1 - t) * u + t * d
        g[H - 1 - i] = (1 - t) * d + t * u
    return g


class Atlas:
    def __init__(self, name):
        self.a = load(name)
        self.m = frame_mask(self.a)

    def cell(self, box, snap_it=True):
        b = snap(self.m, box) if snap_it else box
        if snap_it:
            b = trim(self.a, self.m, b)
        x0, y0, x1, y1 = b
        return self.a[y0:y1, x0:x1]

    def tile(self, box, W=16, H=16, snap_it=True, accent=False):
        return opaque(reduce(self.cell(box, snap_it), W, H, accent=accent))

    def thing(self, box, W=16, H=16, margin=1, tol=30, snap_it=True, how='bottom', min_lum=0, accent=True):
        """min_lum: what is darker is ground too (a glow drawn on black)"""
        k = key(self.cell(box, snap_it), tol)
        if min_lum:
            k[PA.lum(k[:, :, :3]) < min_lum, 3] = 0
        return fit(k, W, H, margin, how, accent)


def pieces(f, cols, rows):
    return [f[r * 16:(r + 1) * 16, c * 16:(c + 1) * 16] for r in range(rows) for c in range(cols)]


def drain():
    A = Atlas('drain')
    T = {}   # metatile -> (group, [frames])

    def put(name, group, frames, speed=None):
        T[name] = (group, frames, speed)

    floor = [A.tile(b) for b in ((26, 101, 94, 170), (100, 101, 172, 170), (173, 101, 240, 171))]
    for n, f in zip(('sw_floor0', 'sw_floor1', 'sw_floor2'), floor):
        put(n, 'drain_stone', [f])
    for n, b in (('sw_floor_grime', (259, 102, 327, 171)), ('sw_floor_grime2', (328, 102, 396, 171)),
                 ('sw_floor_crack', (418, 102, 486, 171)), ('sw_floor_crack2', (487, 102, 555, 171)),
                 ('sw_floor_moss', (572, 102, 637, 171)), ('sw_floor_moss2', (642, 102, 708, 171)),
                 ('sw_floor_bones', (190, 224, 257, 285))):
        put(n, 'drain_stone', [A.tile(b)])
    put('sw_floor_puddle', 'drain_water', [A.tile(b) for b in ((26, 223, 91, 283), (92, 223, 156, 283))], 24)
    put('sw_floor_shroom', 'drain_stone', [A.tile(b, accent=True) for b in ((291, 226, 349, 285), (353, 226, 410, 285))], 16)
    # the drips fall on the wet slabs
    drips = [A.thing(b, margin=0, tol=24, how='center', min_lum=40) for b in ((444, 226, 498, 285), (501, 226, 555, 285), (560, 226, 616, 285), (622, 226, 684, 286))]
    put('sw_floor_drip', 'drain_stone', [over(floor[0], d) for d in drips], 9)

    # the walls
    put('sw_wall_top', 'drain_stone', [A.tile((27, 378, 97, 446))])
    put('sw_wall_top_moss', 'drain_stone', [A.tile((104, 378, 172, 446))])
    wall = A.tile((201, 379, 274, 448))
    put('sw_wall', 'drain_stone', [wall])
    for n, b in (('sw_wall_slime', (303, 379, 367, 448)), ('sw_wall_crack', (376, 379, 440, 448)), ('sw_wall_moss', (445, 379, 511, 448)),
                 ('sw_wall_chain', (519, 379, 582, 448)), ('sw_wall_tally', (589, 379, 653, 448)), ('sw_wall_skull', (660, 379, 722, 448)),
                 ('sw_wall_rust', (731, 379, 792, 448))):
        put(n, 'drain_stone', [A.tile(b)])
    wdrips = [A.thing(b, margin=0, tol=24, how='center', min_lum=40) for b in ((27, 499, 79, 561), (80, 499, 131, 561), (132, 500, 183, 562))]
    put('sw_wall_drip', 'drain_stone', [over(wall, d) for d in wdrips], 9)
    webs = [A.thing(b, margin=0, tol=24, how='center', min_lum=45) for b in ((205, 500, 264, 562), (270, 499, 330, 562))]
    put('sw_wall_web', 'drain_stone', [over(wall, webs[0])])
    put('sw_wall_web_r', 'drain_stone', [over(wall, webs[1])])
    put('sw_wall_fungus', 'glints', [A.tile(b, accent=True) for b in ((355, 499, 413, 563), (419, 499, 478, 563))], 14)
    put('sw_wall_window', 'drain_stone', [A.tile(b, accent=True) for b in ((499, 499, 563, 563), (574, 499, 644, 563))], 22)
    put('sw_pipe', 'drain_props', [A.tile((671, 498, 750, 565))])
    put('sw_pipe_h', 'drain_props', [A.tile((757, 498, 845, 565))])
    # the teal banner keeps the water's teals and brass; the red, the stall's reds
    put('sw_banner_teal', 'drain_water', [over(wall, A.thing((39, 614, 107, 699), tol=26))])
    put('sw_banner_red', 'drain_props', [over(wall, A.thing((115, 614, 182, 699), tol=26))])
    put('sw_lantern', 'drain_props', [A.tile(b, accent=True) for b in ((208, 614, 259, 699), (263, 614, 314, 699))], 10)
    put('sw_torch_lit', 'drain_props', [A.tile(b, accent=True) for b in ((338, 614, 391, 699), (397, 614, 453, 699))], 6)
    put('sw_hole', 'drain_stone', [A.tile((479, 614, 558, 699))])
    arch = A.tile((583, 614, 728, 699), 32, 16)
    put('sw_arch', 'drain_stone', [pieces(arch, 2, 1)[0]])
    put('sw_arch_r', 'drain_stone', [pieces(arch, 2, 1)[1]])

    # the water
    put('sw_water', 'drain_water', [seamless(A.tile(b)) for b in ((744, 103, 808, 161), (811, 103, 876, 161))], 20)
    put('sw_water_scum', 'drain_water', [A.tile(b) for b in ((902, 105, 952, 163), (953, 105, 1004, 163))], 20)
    put('sw_water_glint', 'drain_water', [A.tile(b, accent=True) for b in ((1014, 105, 1064, 162), (1065, 105, 1116, 162))], 16)
    put('sw_lilypad', 'drain_water', [A.tile(b) for b in ((1127, 105, 1179, 162), (1177, 105, 1228, 162))], 20)
    water0 = T['sw_water'][1][0]
    bubbles = [A.thing(b, margin=2, tol=24, how='center') for b in ((1241, 106, 1285, 161), (1286, 106, 1334, 161), (1335, 106, 1382, 161), (1384, 106, 1429, 161))]
    put('sw_water_bubble', 'drain_water', [over(water0, b) for b in bubbles], 8)
    put('sw_water_edge_n', 'drain_stone', [A.tile((752, 214, 831, 280))])
    put('sw_water_edge_n_moss', 'drain_stone', [A.tile((834, 214, 907, 280))])
    put('sw_water_edge_s', 'drain_stone', [A.tile((935, 215, 1010, 281))])
    put('sw_water_edge_s_moss', 'drain_stone', [A.tile((1018, 215, 1094, 281))])
    grate = A.tile((1116, 211, 1283, 284), 32, 16)
    put('sw_grate', 'drain_water', [pieces(grate, 2, 1)[0]])
    put('sw_grate_r', 'drain_water', [pieces(grate, 2, 1)[1]])
    put('sw_ladder_down', 'drain_water', [A.tile((1310, 211, 1413, 285))])
    falls = [A.tile(b, 48, 32, snap_it=False) for b in ((1035, 327, 1227, 447), (1035, 455, 1227, 576))]
    for i in range(6):
        put('sw_fall_%d' % i, 'drain_water', [pieces(f, 3, 2)[i] for f in falls], 6)

    # the stall, the rug, the drain and the clutter
    drain_ = A.tile((29, 787, 195, 925), 32, 32)
    for i, n in enumerate(('sw_drain_nw', 'sw_drain_ne', 'sw_drain_sw', 'sw_drain_se')):
        put(n, 'drain_stone', [pieces(drain_, 2, 2)[i]])
    rug = A.tile((218, 787, 379, 925), 32, 32)
    for i, n in enumerate(('sw_rug_nw', 'sw_rug_ne', 'sw_rug_sw', 'sw_rug_se')):
        put(n, 'drain_props', [pieces(rug, 2, 2)[i]])
    awn = over(np.concatenate([floor[1], floor[1]], axis=1), A.thing((409, 787, 638, 860), 32, 16, margin=0))
    put('sw_awning_l', 'drain_props', [pieces(awn, 2, 1)[0]])
    put('sw_awning_r', 'drain_props', [pieces(awn, 2, 1)[1]])
    cnt = over(np.concatenate([floor[1], floor[1]], axis=1), A.thing((665, 787, 828, 895), 32, 16, margin=0))
    put('sw_counter', 'drain_props', [pieces(cnt, 2, 1)[0]])
    put('sw_counter_r', 'drain_props', [pieces(cnt, 2, 1)[1]])
    for n, b in (('sw_barrel', (28, 962, 78, 1016)), ('sw_crate', (82, 962, 132, 1016)), ('sw_skull', (137, 962, 187, 1016)),
                 ('sw_gold', (194, 962, 253, 1016)), ('sw_rubble', (260, 962, 325, 1016)), ('sw_pot', (340, 967, 389, 1021))):
        put(n, 'drain_props', [over(floor[0], A.thing(b, tol=26))])
    put('sw_candles', 'drain_props', [over(floor[0], A.thing(b, tol=26)) for b in ((404, 943, 461, 1016), (472, 943, 529, 1016))], 7)

    # glints: three kinds, the lower row of each group its three frames
    for n, b, sp in (('sw_glint', (546, 941, 646, 1016), 12), ('sw_glint2', (662, 941, 741, 1016), 14), ('sw_glint3', (753, 941, 834, 1016), 18)):
        cells = split(b, 3, 2)[3:]
        put(n, 'glints', [glow_only(A.thing(c, margin=5, tol=70, snap_it=False, how='center'), 70) for c in cells], sp)
    return T


def blight():
    A = Atlas('blight')
    T = {}

    def put(name, group, frames, speed=None):
        T[name] = (group, frames, speed)

    put('canopy_blight', 'blight_canopy', [A.tile((47, 133, 141, 226), accent=True)])
    put('canopy_blight2', 'blight_canopy', [A.tile(b, accent=True) for b in ((209, 133, 303, 226), (322, 133, 416, 226))], 18)
    put('blight_wall', 'blight_growth', [A.tile((479, 133, 573, 226))])
    put('blight_wall2', 'blight_growth', [A.tile((590, 133, 684, 226))])
    put('blight_wall_lit', 'blight_growth', [A.tile(b, accent=True) for b in ((750, 133, 844, 226), (863, 133, 956, 226))], 16)
    g = [A.tile(b) for b in ((35, 330, 127, 422), (144, 330, 236, 422))]
    put('blight_ground0', 'blight_ground', [g[0]])
    put('blight_ground1', 'blight_ground', [g[1]])
    put('blight_ground2', 'blight_ground', [A.tile(b, accent=True) for b in ((269, 330, 361, 422), (379, 330, 471, 422))], 12)
    fl = A.tile((510, 330, 616, 422))
    put('blight_floor', 'blight_floor', [fl])
    put('blight_floor2', 'blight_floor', [A.tile(b, accent=True) for b in ((656, 330, 762, 422), (776, 330, 872, 422))], 20)
    # the vein is the blighted rooms' trail, laid wide: only its bright
    # cracks, over the plain rot, so it glows without drowning the room
    veins = [A.tile(b, accent=True) for b in ((910, 330, 1006, 422), (1030, 330, 1126, 422))]
    put('blight_vein', 'blight_floor', [over(fl, cracks(v)) for v in veins], 12)
    put('blight_pool', 'blight_floor', [A.tile(b, accent=True) for b in ((1180, 330, 1276, 422), (1303, 330, 1399, 422))], 16)
    put('blight_crystal', 'blight_growth', [over(fl, outlined(A.thing((36, 536, 121, 622), tol=26, margin=2)))])
    put('dead_tree', 'blight_growth', [over(fl, outlined(A.thing((132, 535, 270, 662), tol=26, snap_it=False, margin=2)))])
    tree = outlined(A.thing((537, 470, 742, 707), 48, 64, margin=2, tol=26, snap_it=False))
    ps = pieces(tree, 3, 4)
    for i in range(9):
        put('btree_%d' % i, 'blight_growth', [ps[i]])
    for i in range(9, 12):
        put('btree_%d' % i, 'blight_growth', [over(fl, ps[i])])
    put('blight_mist', 'blight_floor', [dither(A.thing(b, margin=0, tol=16, how='center')) for b in ((800, 536, 872, 611), (883, 536, 956, 611))], 16)
    put('sparkle', 'glints', [glow_only(A.thing(b, margin=2, tol=20, how='center'), 100) for b in ((988, 536, 1061, 611), (1072, 536, 1145, 611), (1167, 536, 1240, 611))], 14)
    put('sparkle_white', 'glints', [glow_only(A.thing(b, margin=2, tol=20, how='center'), 100) for b in ((1270, 536, 1341, 611), (1345, 536, 1415, 611))], 16)
    return T


# ---------------------------------------------------------------- write --
def quantize(f, pal, wl=2.0):
    """nearest palette colour in Lab, lightness weighing double: a tile
    keeps its values (a black pit stays the darkest colour) before hues"""
    P = PA.to_lab(np.array(pal, float))
    out = np.zeros(f.shape[:2], np.uint8)
    m = f[:, :, 3] >= 128
    if m.any():
        L = PA.to_lab(f[m][:, :3])
        d = ((L[:, None, :] - P[None]) ** 2) * np.array([wl * wl, 1.0, 1.0])
        out[m] = np.argmin(d.sum(axis=2), axis=1) + 1
    return out


def rows_of(idx):
    return [''.join('%x' % v for v in r) for r in idx]


def main():
    T = {}
    T.update(drain())
    T.update(blight())
    groups = {}
    for name, (g, frames, _) in T.items():
        groups.setdefault(g, []).extend(frames)
    pals = {g: PA.derive(fr, 15) for g, fr in groups.items()}
    out = {'palettes': {g: ['#%02x%02x%02x' % tuple(c) for c in p] for g, p in sorted(pals.items())}, 'tiles': {}}
    prev = sys.argv[1] if len(sys.argv) > 1 else None
    if prev:
        os.makedirs(prev, exist_ok=True)
    for name, (g, frames, speed) in sorted(T.items()):
        idx = [quantize(f, pals[g]) for f in frames]
        d = {'pal': g, 'frames': [rows_of(i) for i in idx]}
        if speed and len(frames) > 1:
            d['anim_speed'] = speed
        out['tiles'][name] = d
        if prev:
            strip = np.concatenate([PA.indexed_to_rgba(i, pals[g]) for i in idx], axis=1)
            Image.fromarray(strip.astype(np.uint8), 'RGBA').resize((strip.shape[1] * 4, 64), Image.NEAREST).save(os.path.join(prev, name + '.png'))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'tiles.json'), 'w') as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print('art/tile_art: %d tiles in %d palette groups' % (len(T), len(pals)))


if __name__ == '__main__':
    main()
