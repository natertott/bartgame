"""Sampling the style boards: a sprite or a tile is cut from a board,
scaled to its GBA size, keyed from the board's backdrop and quantized to
a palette of fifteen colours derived from the boards themselves. The
boards live in art/ref/. Everything here is deterministic."""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
_boards = {}


def board(name):
    if name not in _boards:
        _boards[name] = Image.open(os.path.join(HERE, 'ref', 'board_%s.jpg' % name)).convert('RGB')
    return _boards[name]


def hexcol(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def dist2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def keyed(im, bg, thresh):
    """RGBA: alpha 0 where the pixel is near the backdrop colour"""
    out = Image.new('RGBA', im.size)
    src = im.load()
    dst = out.load()
    t2 = thresh * thresh
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            p = src[x, y]
            near = any(dist2(p, b) < t2 for b in bg) if bg else False
            dst[x, y] = (p[0], p[1], p[2], 0 if near else 255)
    return out


def derive(samples, n=15, bgs=(), thresh=28, spread=False):
    """a palette of n colours (median cut) over the opaque pixels of the
    given (board, box) crops. spread: cut 2n and keep the n farthest
    apart, so a sprite's few bright colours survive its many darks."""
    pix = []
    for name, box in samples:
        # every crop weighs the same, whatever its size
        im = board(name).crop(box).resize((64, 64), Image.LANCZOS)
        k = keyed(im, bgs, thresh).load()
        for y in range(im.size[1]):
            for x in range(im.size[0]):
                p = k[x, y]
                if p[3]:
                    pix.append(p[:3])
    strip = Image.new('RGB', (len(pix), 1))
    strip.putdata(pix)
    m = n * 2 if spread else n
    q = strip.quantize(colors=m, method=Image.MEDIANCUT)
    pal = q.getpalette()[:m * 3]
    cols = [tuple(pal[i:i + 3]) for i in range(0, m * 3, 3)]
    if spread:
        counts = sorted(q.getcolors(), reverse=True)
        order = [cols[idx] for _, idx in counts]
        keep = [order[0]]
        while len(keep) < n and len(keep) < len(order):
            best = max((c for c in order if c not in keep), key=lambda c: min(dist2(c, k) for k in keep))
            keep.append(best)
        cols = keep
    cols.sort(key=lambda c: c[0] * 3 + c[1] * 6 + c[2])
    return cols


def cut(name, box, w, h, palette, bgs=(), thresh=28, outline=None, floor_alpha=128):
    """rows of hex digits: the crop scaled to w x h, keyed, nearest colour
    in the palette (index 1..15; 0 clear). outline: an index drawn round
    the opaque pixels, outside them."""
    im = board(name).crop(box)
    rgba = keyed(im, bgs, thresh).resize((w, h), Image.LANCZOS)
    px = rgba.load()
    grid = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            if p[3] < floor_alpha:
                continue
            best, bd = 1, 1 << 30
            for i, c in enumerate(palette):
                d = dist2(p, c)
                if d < bd:
                    bd = d
                    best = i + 1
            grid[y][x] = best
    if outline is not None:
        for y in range(h):
            for x in range(w):
                if grid[y][x]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] and grid[ny][nx] != outline:
                        grid[y][x] = outline
                        break
    return [''.join('%x' % v if v else '.' for v in row) for row in grid]


def opaque(rows, fill):
    return [r.replace('.', '%x' % fill) for r in rows]


def seamless(im):
    """blend an RGB image with itself shifted by half, weighted toward the
    edges, so the tile wraps"""
    w, h = im.size
    src = im.load()
    out = Image.new('RGB', (w, h))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            a = src[x, y]
            b = src[(x + w // 2) % w, (y + h // 2) % h]
            wx = abs(x + 0.5 - w / 2.0) / (w / 2.0)
            wy = abs(y + 0.5 - h / 2.0) / (h / 2.0)
            t = max(0.0, (max(wx, wy) - 0.66) / 0.34) ** 2 * 0.5
            dst[x, y] = tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))
    return out


def quantize_rows(rgba, palette, floor_alpha=128, outline=None):
    w, h = rgba.size
    px = rgba.load()
    grid = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            if len(p) > 3 and p[3] < floor_alpha:
                continue
            best, bd = 1, 1 << 30
            for i, c in enumerate(palette):
                d = dist2(p, c)
                if d < bd:
                    bd = d
                    best = i + 1
            grid[y][x] = best
    if outline is not None:
        for y in range(h):
            for x in range(w):
                if grid[y][x]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] and grid[ny][nx] != outline:
                        grid[y][x] = outline
                        break
    return [''.join('%x' % v if v else '.' for v in row) for row in grid]


def tile(name, box, w, h, palette, wrap=True):
    """an opaque tile: the crop scaled, made seamless, quantized"""
    im = board(name).crop(box).resize((w, h), Image.LANCZOS)
    if wrap:
        im = seamless(im)
    return quantize_rows(im.convert('RGBA'), palette)


def fit(name, box, W, H, palette, bgs, thresh=40, height=None, width=None, outline=1, bottom=True, shift=(0, 0)):
    """a sprite: the crop keyed and trimmed to its opaque bounds, scaled to
    the given height (or width), set on a clear W x H canvas, centred and
    on the bottom row (or centred vertically)"""
    im = board(name).crop(box)
    rgba = keyed(im, bgs, thresh)
    bb = rgba.getbbox()
    if bb is None:
        return ['.' * W] * H
    rgba = rgba.crop(bb)
    bw, bh = rgba.size
    if height is not None:
        sw, sh = max(1, int(round(bw * height / float(bh)))), height
        if sw > W:
            sw, sh = W, max(1, int(round(bh * W / float(bw))))
    else:
        sw, sh = width, max(1, int(round(bh * width / float(bw))))
        if sh > H:
            sw, sh = max(1, int(round(bw * H / float(bh)))), H
    small = rgba.resize((sw, sh), Image.LANCZOS)
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ox = (W - sw) // 2 + shift[0]
    oy = (H - sh if bottom else (H - sh) // 2) + shift[1]
    canvas.paste(small, (ox, oy), small)
    return quantize_rows(canvas, palette, outline=outline)
