"""The title screen, painted with PIL in the title palette's own colors
and quantized back to 16. A night sky over the blighted wood: stars, the
Grail burning gold above the canopy with rays about it, violet mist on
the ground, the name in bevelled gold serif with a dark shadow, motes."""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

FONTS = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
    '/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf',
]

PAL = ['#080810',   # 0 night, backdrop
       '#180c28',   # 1 violet deepest
       '#2c1c48',   # 2 violet
       '#4a2c68',   # 3 violet mist
       '#0c2418',   # 4 leaf deepest
       '#184830',   # 5 leaf dark
       '#2a7048',   # 6 leaf mid
       '#584010',   # 7 gold dark
       '#a07020',   # 8 gold
       '#e0b030',   # 9 gold mid
       '#fff0a0',   # A gold bright
       '#ffffff',   # B white
       '#ff8030',   # C petal orange
       '#c02038',   # D crimson
       '#6c4880',   # E violet light
       '#101810']   # F outline


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


C = [rgb(p) for p in PAL]


def nearest(pal_rgb, col):
    best, bi = 1 << 30, 0
    for i, p in enumerate(pal_rgb):
        d = sum((a - b) ** 2 for a, b in zip(p, col))
        if d < best:
            best, bi = d, i
    return bi


def render():
    rnd = random.Random(11)
    im = Image.new('RGB', (240, 160), C[0])
    d = ImageDraw.Draw(im)
    px = im.load()
    # the sky: night above, violet toward the horizon, in bands
    bands = [C[0], C[1], C[2], C[3]]
    edges = [0.4, 0.68, 0.88, 2.0]
    for y in range(0, 112):
        t = y / 112.0
        k = next(i for i, e in enumerate(edges) if t < e)
        col = bands[k]
        # a checker of the next band through the last rows of each band
        nxt = bands[min(3, k + 1)]
        e0 = edges[k - 1] if k else 0.0
        frac = (t - e0) / (edges[k] - e0) if edges[k] < 2 else 0
        for x in range(240):
            px[x, y] = nxt if (frac > 0.78 and (x + y) % 2 == 0) or (frac > 0.9 and (x + y) % 2 == 1 and x % 3 == 0) else col
    # stars
    for _ in range(70):
        x, y = rnd.randrange(240), rnd.randrange(0, 90)
        px[x, y] = C[0xb] if rnd.random() < 0.7 else C[0xe]
    for (x, y) in ((30, 18), (200, 12), (70, 40), (170, 48), (120, 8), (220, 60)):
        px[x, y] = C[0xb]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            px[x + dx, y + dy] = C[0xe]
    # rays from the Grail, dashed
    gx, gy = 120, 46
    for k in range(16):
        ang = k * math.pi / 8 + 0.1
        for r in range(22, 78):
            if (r // 4) % 2:
                continue
            x, y = int(gx + math.cos(ang) * r), int(gy + math.sin(ang) * r * 0.8)
            if 0 <= x < 240 and 0 <= y < 104:
                px[x, y] = C[7] if r > 56 else C[8]
    # the glow
    for r, col in ((26, C[2]), (20, C[3]), (14, C[0xe])):
        d.ellipse([gx - r, gy - r * 0.8, gx + r, gy + r * 0.8], fill=col)
    # the Grail
    d.polygon([(gx - 12, gy - 14), (gx + 12, gy - 14), (gx + 6, gy), (gx + 2, gy + 4), (gx - 2, gy + 4), (gx - 6, gy)], fill=C[9])
    d.polygon([(gx - 12, gy - 14), (gx - 4, gy - 14), (gx - 3, gy - 2), (gx - 6, gy)], fill=C[0xa])
    d.polygon([(gx + 6, gy - 14), (gx + 12, gy - 14), (gx + 6, gy), (gx + 3, gy)], fill=C[8])
    d.rectangle([gx - 2, gy + 4, gx + 1, gy + 12], fill=C[9])
    d.line([(gx - 2, gy + 4), (gx - 2, gy + 12)], fill=C[0xa])
    d.line([(gx + 1, gy + 4), (gx + 1, gy + 12)], fill=C[8])
    d.polygon([(gx - 9, gy + 16), (gx + 9, gy + 16), (gx + 2, gy + 12), (gx - 2, gy + 12)], fill=C[9])
    d.line([(gx - 9, gy + 16), (gx + 9, gy + 16)], fill=C[7])
    d.line([(gx - 12, gy - 14), (gx + 12, gy - 14)], fill=C[0xa])
    d.line([(gx - 12, gy - 13), (gx + 12, gy - 13)], fill=C[7])
    # the gem
    d.rectangle([gx - 1, gy - 9, gx, gy - 7], fill=C[0xd])
    px[gx - 1, gy - 9] = C[0xb]
    # the outline of the Grail
    for y in range(gy - 16, gy + 18):
        for x in range(gx - 14, gx + 14):
            if px[x, y] in (C[9], C[0xa], C[8], C[0xd], C[0xb]):
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if px[x + dx, y + dy] in (C[9], C[0xa], C[8]):
                    px[x, y] = C[7]
                    break
    # the wood: a line of dark canopy blobs along the horizon, trunks under
    for i in range(-1, 14):
        cx = i * 19 + rnd.randrange(6)
        r = 12 + rnd.randrange(6)
        cy = 110 + rnd.randrange(6)
        d.ellipse([cx - r - 1, cy - r, cx + r + 1, cy + r], fill=C[4])
        d.ellipse([cx - r + 2, cy - r + 2, cx + r - 3, cy + r - 4], fill=C[5])
        d.ellipse([cx - r + 4, cy - r + 4, cx + r - 7, cy + r - 9], fill=C[6])
    d.rectangle([0, 118, 239, 132], fill=C[4])
    for i in range(14):
        x = i * 18 + rnd.randrange(8)
        d.rectangle([x, 120, x + 3, 136], fill=C[1])
        d.line([(x + 3, 120), (x + 3, 136)], fill=C[0])
    # the mist and ground
    for y in range(132, 160):
        t = (y - 132) / 28.0
        col = C[3] if t < 0.25 else C[2] if t < 0.6 else C[1]
        d.line([(0, y), (239, y)], fill=col)
    for _ in range(40):
        x, y = rnd.randrange(240), rnd.randrange(126, 158)
        px[x, y] = C[0xe]
    # blight vines in the lower corners
    for (x0, dirn) in ((4, 1), (235, -1)):
        x, y = x0, 158
        for i in range(44):
            px[max(0, min(239, x)), y] = C[0xe] if i % 5 else C[0xb]
            y -= 1
            x += dirn if (i // 3) % 2 else 0
            if i % 9 == 4:
                px[max(0, min(239, x + dirn * 2)), y + 1] = C[0xd]
    # the name
    path = next(p for p in FONTS if os.path.exists(p))
    fnt = ImageFont.truetype(path, 28)
    text = 'BARTGAME'
    bbox = d.textbbox((0, 0), text, font=fnt)
    tw = bbox[2] - bbox[0]
    tx = (240 - tw) // 2 - bbox[0]
    ty = 78
    mask = Image.new('L', (240, 160), 0)
    ImageDraw.Draw(mask).text((tx, ty), text, font=fnt, fill=255)
    mpx = mask.load()
    ink = [[mpx[x, y] > 110 for x in range(240)] for y in range(160)]
    # the shadow, then the outline, then the gold bevel
    for y in range(160):
        for x in range(240):
            if y >= 3 and x >= 2 and ink[y - 3][x - 2]:
                px[x, y] = C[1]
    for y in range(1, 159):
        for x in range(1, 239):
            if ink[y][x]:
                continue
            if ink[y - 1][x] or ink[y + 1][x] or ink[y][x - 1] or ink[y][x + 1]:
                px[x, y] = C[0xf]
    top = min(y for y in range(160) if any(ink[y]))
    bot = max(y for y in range(160) if any(ink[y]))
    for y in range(160):
        for x in range(240):
            if not ink[y][x]:
                continue
            t = (y - top) / float(bot - top)
            if not ink[y - 1][x]:
                col = C[0xb]           # the lit top edge
            elif t < 0.3:
                col = C[0xa]
            elif t < 0.55:
                col = C[9]
            elif t < 0.8:
                col = C[8]
            else:
                col = C[7]
            if ink[y + 1][x] is False and t > 0.5:
                col = C[7]
            px[x, y] = col
    # motes
    for _ in range(50):
        x, y = rnd.randrange(240), rnd.randrange(60, 150)
        if px[x, y] in (C[0], C[1], C[2], C[3], C[4], C[5]):
            px[x, y] = rnd.choice([C[9], C[0xa], C[0xb]])
    # two blooms flank the name: the hero's own flower
    for bx in (18, 222):
        by = 96
        for k in range(8):
            ang = k * math.pi / 4 + math.pi / 8
            cxp, cyp = bx + math.cos(ang) * 6.5, by + math.sin(ang) * 6.0
            for y in range(by - 12, by + 13):
                for x in range(bx - 12, bx + 13):
                    dx, dy = x + 0.5 - cxp, y + 0.5 - cyp
                    if dx * dx + dy * dy <= 3.8 * 3.8:
                        ddx, ddy = x + 0.5 - bx, y + 0.5 - by
                        d = (ddx * ddx + ddy * ddy) ** 0.5
                        px[x, y] = C[0xc] if d > 6.5 else C[0xd]
        for y in range(by - 6, by + 7):
            for x in range(bx - 6, bx + 7):
                dx, dy = (x + 0.5 - bx) / 6.0, (y + 0.5 - by) / 6.0
                if dx * dx + dy * dy <= 1.0:
                    px[x, y] = C[0xb] if dx + dy < 0.9 else C[0xa]
        for (ex, ey) in ((bx - 3, by - 2), (bx + 1, by - 2)):
            for yy in range(3):
                px[ex, ey + yy] = C[0xf]; px[ex + 1, ey + yy] = C[0xf]
            px[ex, ey] = C[0xb]
        px[bx - 1, by + 3] = C[0xf]; px[bx, by + 3] = C[0xf]
        # an outline round the bloom
        for y in range(by - 13, by + 14):
            for x in range(bx - 13, bx + 14):
                if px[x, y] in (C[0xc], C[0xd], C[0xb], C[0xa], C[0xf]):
                    continue
                for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if px[x + ddx, y + ddy] in (C[0xc], C[0xd]):
                        px[x, y] = C[0xf]
                        break
    # a gold filigree frame round the screen, knots at the corners
    for i in range(240):
        for yy in (3, 156):
            px[i, yy] = C[8]
        for yy in (4, 155):
            px[i, yy] = C[7]
    for j in range(160):
        for xx in (3, 236):
            px[xx, j] = C[8]
        for xx in (4, 235):
            px[xx, j] = C[7]
    for (kx, ky) in ((3, 3), (236, 3), (3, 156), (236, 156)):
        for ddx in range(-3, 4):
            for ddy in range(-3, 4):
                if abs(ddx) + abs(ddy) <= 3 and 0 <= kx + ddx < 240 and 0 <= ky + ddy < 160:
                    px[kx + ddx, ky + ddy] = C[0xa] if abs(ddx) + abs(ddy) < 2 else C[8]
    out = [[nearest(C, px[x, y]) for x in range(240)] for y in range(160)]
    return out, PAL


if __name__ == '__main__':
    pix, pal = render()
    im = Image.new('RGB', (240, 160))
    p = im.load()
    for y in range(160):
        for x in range(240):
            p[x, y] = C[pix[y][x]]
    im.resize((480, 320)).save('/tmp/title.png')
    print('wrote /tmp/title.png')
