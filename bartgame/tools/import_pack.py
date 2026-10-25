"""Import the BARTGAME GBA sprite pack into art/pack/.

    python3 tools/import_pack.py [PACK_DIR]      (default art/ref/pack)

The pack (art/ref/pack/, from the sprite pack zip) holds two kinds of
sheet:

  - exact strips: 4-bit indexed PNGs at the engine's frame size, frames
    side by side in the manifest's order. They are taken as they are,
    index for index, with the palette they carry.
  - the revised sheets: large RGBA illustrations, one figure per cell of
    a grid, drawn at four to thirteen screen pixels per art pixel. Their
    file names are crossed in the pack (hero.png holds the pickups,
    pick32.png holds the Bloom, items.png the shields, shield.png the
    folk, npc.png the small items), so each is named here by what it
    shows. A cell is found by the transparent gaps of the grid, scaled
    to the frame by area averaging (a box that is a third or more dark
    outline takes the outline, so lines and eyes stay), and quantized
    to its palette group: one outline colour and fourteen by median cut
    over every frame of the group.

The output is one indexed strip per engine sheet (art/pack/<sheet>.png,
frames in the order pack.json lists), the pack's tile and HUD strips as
they are (art/pack/tiles/, used only by the comparison build) and
pack.json with the palettes.
The build reads only art/pack/; this script needs numpy and Pillow.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PACK = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'art', 'ref', 'pack')
OUT = os.path.join(ROOT, 'art', 'pack')


# ---------------------------------------------------------------- cutting --
def runs(occ, mingap=8):
    """spans of True separated by at least mingap False"""
    out, start, gap, end = [], None, 0, 0
    for i, v in enumerate(occ):
        if v:
            if start is None:
                start = i
            gap, end = 0, i + 1
        elif start is not None:
            gap += 1
            if gap >= mingap:
                out.append((start, end))
                start = None
    if start is not None:
        out.append((start, end))
    return out


def load(rel):
    return np.array(Image.open(os.path.join(PACK, rel)).convert('RGBA')).astype(float)


def grid(src, mingap=8):
    """the cells of an illustration, row by row: (x0, y0, x1, y1), y the
    row band's extent"""
    a = src[:, :, 3] > 32
    rows = []
    for (y0, y1) in runs(a.any(axis=1), mingap):
        rows.append([(x0, y0, x1, y1) for (x0, x1) in runs(a[y0:y1].any(axis=0), mingap)])
    return rows


def tight(src, box):
    x0, y0, x1, y1 = box
    a = src[y0:y1, x0:x1, 3] > 32
    ys, xs = np.nonzero(a)
    return (x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1)


def lum(c):
    return 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]


def down(src, W, H, scale, ox, oy, dark_lum=45, dark_frac=0.30):
    """a W x H frame: target pixel (x, y) is the source box from
    (ox + x/scale, oy + y/scale), area averaged with alpha weights; a box
    that is dark_frac or more near-black takes the median of its darks"""
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


def place(src, box, W, H, scale, how='center', dx=0, dy=0):
    """a cell scaled by scale into a W x H frame. how: 'center' (the tight
    box centred), 'bottom' (centred, its foot on the last row), 'band' (the
    row band's bottom on the last row, centred on the upper body)"""
    tb = tight(src, box)
    x0, y0, x1, y1 = tb
    cw, ch = (x1 - x0) * scale, (y1 - y0) * scale
    if how == 'band':
        sub = src[box[1]:box[3], box[0]:box[2], 3] > 128
        top = sub[:int(sub.shape[0] * 0.6)]
        ys, xs = np.nonzero(top if top.any() else sub)
        cx = box[0] + xs.mean()
        ox = cx - (W / 2.0) / scale
        oy = box[3] - H / scale
    else:
        ox = x0 - ((W - cw) / 2.0) / scale
        oy = (y1 - H / scale) if how == 'bottom' else y0 - ((H - ch) / 2.0) / scale
    # sample the cell alone, so a frame wider than the cell takes nothing
    # from its neighbours
    bx0, by0, bx1, by1 = box
    return down(src[by0:by1, bx0:bx1], W, H, scale, ox - dx / scale - bx0, oy - dy / scale - by0)


def fit_scale(src, box, W, H, margin=0):
    x0, y0, x1, y1 = tight(src, box)
    return min((W - margin) / float(x1 - x0), (H - margin) / float(y1 - y0))


# --------------------------------------------------------------- palettes --
def to_lab(rgb):
    c = np.asarray(rgb, float) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.9505, 1.0, 1.089])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116.0)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def kmeans(pixels, k, power=0.5, iters=30):
    """k colours for an (N,3) RGB array: colours bucketed to 4 bits a
    channel, each bucket weighted by count**power (so a small accent keeps
    a colour of its own), weighted k-means in Lab from a farthest-point
    start. Deterministic."""
    q = (pixels.astype(int) >> 3)
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
            m = lab == j
            if m.any():
                cen[j] = (X[m] * wgt[m, None]).sum(axis=0) / wgt[m].sum()
    lab = np.argmin(((X[:, None, :] - cen[None]) ** 2).sum(axis=2), axis=1)
    out = []
    for j in range(k):
        m = lab == j
        if m.any():
            # the cluster's colour in RGB, weighted the same way
            out.append(tuple(int(round(v)) for v in (mean_rgb[m] * wgt[m, None]).sum(axis=0) / wgt[m].sum()))
    return out


def derive(frames, n=15, dark_lum=40):
    """one outline colour (the median of everything near black) and n-1 by
    weighted k-means over the rest, sorted dark to light"""
    pix = np.concatenate([f[f[:, :, 3] >= 128][:, :3] for f in frames])
    L = lum(pix)
    dark, rest = pix[L < dark_lum], pix[L >= dark_lum]
    outline = tuple(int(v) for v in np.median(dark, axis=0)) if len(dark) else (16, 12, 20)
    cols = kmeans(rest, n - 1) if len(rest) else []
    cols.sort(key=lambda c: lum(np.array(c, float)))
    return [outline] + cols


def quantize(f, pal):
    """nearest palette colour in Lab"""
    P = to_lab(np.array(pal, float))
    H, W = f.shape[:2]
    out = np.zeros((H, W), np.uint8)
    m = f[:, :, 3] >= 128
    if m.any():
        L = to_lab(f[m][:, :3])
        out[m] = np.argmin(((L[:, None, :] - P[None]) ** 2).sum(axis=2), axis=1) + 1
    return out


def indexed_to_rgba(idx, pal):
    H, W = idx.shape
    f = np.zeros((H, W, 4))
    for y in range(H):
        for x in range(W):
            if idx[y, x]:
                f[y, x, :3] = pal[idx[y, x] - 1]
                f[y, x, 3] = 255
    return f


# ----------------------------------------------------------- exact strips --
def strip(rel, w, h, names, rename=None):
    """an indexed strip from the pack: frames by name as index arrays, and
    its palette (entries 1..15)"""
    im = Image.open(os.path.join(PACK, rel))
    assert im.mode == 'P', rel
    pal = im.getpalette()[:48]
    pal = [tuple(pal[i * 3:i * 3 + 3]) for i in range(1, 16)]
    a = np.array(im)
    frames = {}
    for i, n in enumerate(names):
        frames[(rename or {}).get(n, n)] = a[:h, i * w:(i + 1) * w].astype(np.uint8)
    return frames, pal


def manifest_frames(name):
    m = json.load(open(os.path.join(PACK, 'manifest.json')))
    for s in m['sheets']:
        if s['name'] == name:
            return s['png_path'], s['frame_width'], s['frame_height'], s['frames']
    raise KeyError(name)


# ------------------------------------------------------- the revised art --
def flat(rows):
    return [c for r in rows for c in r]


def bloom():
    """the hero, 32x32, from the Bloom illustration (pick32.png in the
    pack): 55 cells for 50 frames. The cells are chosen by pose; five are
    spares (a second front idle, two more balls, a second item pose, a
    front carry). The roll uncurls on the cell it curls on; there is no
    back view of the leap, so jump_n is the back idle raised a pixel."""
    src = load('sheets/objects/pick32.png')
    cells = flat(grid(src))
    assert len(cells) == 55, len(cells)
    x0, y0, x1, y1 = tight(src, cells[0])
    scale = 31.0 / (y1 - y0)
    pick = {
        'idle_s': 0, 'idle_n': 1, 'idle_e': 2,
        'walk_s1': 3, 'walk_s2': 8, 'walk_n1': 5, 'walk_n2': 6, 'walk_e1': 4, 'walk_e2': 10,
        # the swing: wind-up, blow, follow-through, by the sides the
        # engine sweeps the blade through
        'atk_s1': 7, 'atk_s': 16, 'atk_s3': 12,
        'atk_n1': 9, 'atk_n': 14, 'atk_n3': 17,
        'atk_e1': 13, 'atk_e': 18, 'atk_e3': 15,
        'roll_1': 19, 'roll_2': 20, 'roll_3': 21, 'roll_4': 22, 'roll_5': 23, 'roll_6': 26, 'roll_7': 19,
        'hurt_s': 27, 'hurt_n': 28, 'hurt_e': 29,
        'jump_s': 30, 'jump_e': 31,
        'itemget': 33,
        'carry_s': 35, 'carry_n': 36, 'carry_e': 37, 'carry_s1': 38, 'carry_s2': 39,
        'carry_n1': 40, 'carry_n2': 42, 'carry_e1': 43, 'carry_e2': 45,
        'drown_1': 46, 'drown_2': 47, 'drown_3': 48,
        'fall_1': 49, 'fall_2': 50, 'fall_3': 51,
        'guard_s': 52, 'guard_n': 53, 'guard_e': 54,
    }
    out = {k: place(src, cells[i], 32, 32, scale, 'band') for k, i in pick.items()}
    out['jump_n'] = place(src, cells[1], 32, 32, scale, 'band', dy=-1)
    return out


def shields():
    """the Bark Shield, 16x16: the plain round shield (front, edge, back),
    the first row of items.png; the green upgraded shield on the second
    row has no place in the game yet"""
    src = load('sheets/objects/items.png')
    row = grid(src)[0]
    scale = fit_scale(src, row[0], 16, 16, 1)
    return {n: place(src, c, 16, 16, scale, 'center') for n, c in zip(['front', 'side', 'back'], row)}


def pickups():
    """the ground pickups, 32x32, from hero.png: two rows of five at one
    scale, resting on the bottom row"""
    src = load('sheets/characters/hero.png')
    cells = flat(grid(src))
    names = ['heart', 'gilt', 'bomb_pickup', 'gilt_big', 'key', 'relic', 'grail', 'arrow1', 'arrow5', 'arrow10']
    assert len(cells) == len(names)
    scale = min(fit_scale(src, c, 32, 32, 2) for c in cells)
    scale = min(scale, 26.0 / (tight(src, cells[0])[2] - tight(src, cells[0])[0]))
    return {n: place(src, c, 32, 32, scale, 'bottom') for n, c in zip(names, cells)}


def icons():
    """the treasures, 32x32, from icon32.png: 'none' is the empty first
    cell"""
    src = load('sheets/objects/icon32.png')
    cells = flat(grid(src))
    names = ['bombs', 'lamp', 'cloak', 'key', 'heart_piece', 'heart_container', 'gilt_big', 'relic',
             'gauntlet', 'bow', 'hubcap', 'map', 'astrolabe', 'sword', 'shield']
    assert len(cells) == len(names)
    scale = min(fit_scale(src, c, 32, 32, 3) for c in cells)
    out = {'none': np.zeros((32, 32, 4))}
    out.update({n: place(src, c, 32, 32, scale, 'center') for n, c in zip(names, cells)})
    return out


def items16():
    """the small items, 16x16, from npc.png: each fitted to the slot"""
    src = load('sheets/characters/npc.png')
    cells = flat(grid(src))
    names = ['bombs', 'lamp', 'cloak', 'key', 'heart_piece', 'heart_container', 'gilt_big', 'relic', 'heart',
             'gilt', 'bomb_pickup', 'spark', 'grail', 'gauntlet', 'bow', 'arrow1', 'arrow5', 'arrow10', 'hubcap']
    assert len(cells) == len(names)
    out = {'none': np.zeros((16, 16, 4))}
    for n, c in zip(names, cells):
        out[n] = place(src, c, 16, 16, fit_scale(src, c, 16, 16, 1), 'center')
    return out


def folk():
    """the folk, from shield.png: the Gatekeeper, the Peddler, the Hermit
    Knight, the Weeping Nun; then the Gardener (Sister Mary Grace and
    Brother Mark follow, not yet in the game). 32x32, all at one scale,
    feet on the last row"""
    src = load('sheets/characters/shield.png')
    rows = grid(src)
    cells = flat(rows)
    assert len(cells) == 7, len(cells)
    scale = min(31.0 / (tight(src, c)[3] - tight(src, c)[1]) for c in cells)
    names = ['sage', 'merchant', 'hermit', 'nun', 'gardener']
    return {n: place(src, c, 32, 32, scale, 'bottom') for n, c in zip(names, cells)}


def portraits():
    """the dialogue faces, 32x32, from portrait.png: a 3x3 grid in the
    spec's order (the last two, Sister Mary Grace and Brother Mark, are
    not yet in the game). Each keeps a palette of its own."""
    src = load('sheets/characters/portrait.png')
    h, w = src.shape[:2]
    bands = runs((src[:, :, 3] > 32).any(axis=1), 8)
    names = ['hero', 'hero_surprised', 'peddler', 'gatekeeper', 'hermit', 'nun', 'gardener']
    out = {}
    for i, n in enumerate(names):
        y0, y1 = bands[i // 3]
        box = (w * (i % 3) // 3, y0, w * (i % 3 + 1) // 3, y1)
        out[n] = place(src, box, 32, 32, fit_scale(src, box, 32, 32, 0), 'bottom')
    return out


def brighten(f, pal, region, pick):
    """a blink frame: the pixels in region whose colour pick() accepts,
    lifted toward white"""
    g = f.copy()
    x0, y0, x1, y1 = region
    for y in range(y0, y1):
        for x in range(x0, x1):
            if g[y, x, 3] >= 128 and pick(g[y, x, :3]):
                g[y, x, :3] = g[y, x, :3] * 0.45 + 255 * 0.55
    return g


def violet(c):
    r, g, b = c
    return b > 90 and r > 60 and g < 0.7 * min(r, b)


def golden(c):
    r, g, b = c
    return r > 150 and g > 100 and b < 0.6 * g


# -------------------------------------------------------------- the pack --
def main():
    sheets, groups, extra = {}, {}, {}

    def put(sheet, group, w, h, frames):
        sheets[sheet] = {'group': group, 'w': w, 'h': h, 'frames': frames}

    # the revised art, quantized by group
    rgba = {
        'hero': ('hero', 32, 32, bloom()),
        'shield': ('gear', 16, 16, shields()),
        'pick32': ('pick', 32, 32, pickups()),
        'icon32': ('icons', 32, 32, icons()),
        'items': ('items', 16, 16, items16()),
        'npc': ('folk', 32, 32, folk()),
    }
    fk = rgba['npc'][3]
    # the hub's two drawn large: the same figures, a palette of their own,
    # and a blink each (her orb flares, his lantern flickers)
    big = {'sage_1': fk['sage'], 'merchant_1': fk['merchant']}
    big['sage_2'] = brighten(fk['sage'], None, (0, 4, 8, 17), violet)
    big['merchant_2'] = brighten(fk['merchant'], None, (16, 4, 32, 26), golden)
    rgba['folk32'] = ('folk32', 32, 32, {k: big[k] for k in ['sage_1', 'sage_2', 'merchant_1', 'merchant_2']})

    # the sword is an exact strip in the pack's hero colours; it joins the
    # shield's group
    path, w, h, names = manifest_frames('sword')
    sw, swpal = strip(path, w, h, names)
    rgba['sword'] = ('gear', 16, 16, {k: indexed_to_rgba(v, swpal) for k, v in sw.items()})

    by_group = {}
    for sheet, (group, w, h, frames) in rgba.items():
        by_group.setdefault(group, []).extend(frames.values())
    for group, frames in by_group.items():
        groups[group] = derive(frames)
    for sheet, (group, w, h, frames) in rgba.items():
        put(sheet, group, w, h, {k: quantize(v, groups[group]) for k, v in frames.items()})

    # the portraits: a palette each
    por = portraits()
    ppal = {k: derive([v]) for k, v in por.items()}
    put('portrait', 'portrait', 32, 32, {k: quantize(v, ppal[k]) for k, v in por.items()})
    groups['portrait'] = ppal['hero']
    extra['portrait_palettes'] = {k: ['#%02x%02x%02x' % c for c in v] for k, v in ppal.items()}

    # the exact strips, as they are
    exact = {
        'fx': ['fx', 'proj', 'arrow', 'mouth'],
        'bugs': ['beetle', 'bat', 'slime'],
        'blight': ['spitter', 'boss'],
        'iron': ['knight', 'ksword'],
        'lift': ['lift'],
        'ui': ['marks', 'dots', 'cursor'],
    }
    knight = {'walk1_s': 'walk_s1', 'walk2_s': 'walk_s2', 'walk1_n': 'walk_n1', 'walk2_n': 'walk_n2',
              'walk1_e': 'walk_e1', 'walk2_e': 'walk_e2'}
    for group, names_ in exact.items():
        gp = None
        for sheet in names_:
            path, w, h, names = manifest_frames(sheet)
            frames, pal = strip(path, w, h, names, knight if sheet == 'knight' else None)
            if gp is None:
                gp = pal
            elif pal != gp:
                # a sheet of the group with other colours: nearest colour
                frames = {k: quantize(indexed_to_rgba(v, pal), gp) for k, v in frames.items()}
            put(sheet, group, w, h, frames)
        groups[group] = gp

    # the tile sheets and the HUD, for the comparison build that uses
    # them (art/pack_tiles.py): copied as they are, with their palettes
    tiles = {}
    for name in ['forest', 'wood', 'stone', 'cliff', 'blight', 'sewer', 'props', 'hud']:
        path, w, h, names = manifest_frames(name)
        frames, pal = strip(path, w, h, names)
        tiles[name] = {'w': w, 'h': h, 'frames': names,
                       'palette': ['#%02x%02x%02x' % tuple(c) for c in pal]}
        os.makedirs(os.path.join(OUT, 'tiles'), exist_ok=True)
        a = np.zeros((h, w * len(names)), np.uint8)
        for i, n in enumerate(names):
            a[:, i * w:(i + 1) * w] = frames[n]
        im = Image.fromarray(a, 'P')
        pl = [255, 0, 255] + [v for c in pal for v in c]
        im.putpalette(pl + [0] * (768 - len(pl)))
        im.save(os.path.join(OUT, 'tiles', name + '.png'), transparency=0)
    extra['tiles'] = tiles

    # write
    os.makedirs(OUT, exist_ok=True)
    meta = {'groups': {g: ['#%02x%02x%02x' % tuple(c) for c in p] for g, p in groups.items()}, 'sheets': {}}
    meta.update(extra)
    for sheet, s in sheets.items():
        names = list(s['frames'])
        w, h = s['w'], s['h']
        a = np.zeros((h, w * len(names)), np.uint8)
        for i, n in enumerate(names):
            a[:, i * w:(i + 1) * w] = s['frames'][n]
        im = Image.fromarray(a, 'P')
        pal = [255, 0, 255] + [v for c in groups[s['group']] for v in c]
        im.putpalette(pal + [0] * (768 - len(pal)))
        im.save(os.path.join(OUT, sheet + '.png'), transparency=0)
        meta['sheets'][sheet] = {'group': s['group'], 'w': w, 'h': h, 'frames': names}
    json.dump(meta, open(os.path.join(OUT, 'pack.json'), 'w'), indent=1, sort_keys=True)
    print('art/pack: %d sheets, %d groups' % (len(sheets), len(groups)))


if __name__ == '__main__':
    main()
