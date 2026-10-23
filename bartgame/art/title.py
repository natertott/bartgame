"""The title screen, rendered with PIL and quantized to 16 colors.
Dark stone, a wash of blight violet rising from below, the name in a
gold gradient serif, and a scatter of gold motes."""
import os
import random

from PIL import Image, ImageDraw, ImageFont

FONTS = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
    '/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf',
]

PAL = ['#06050a', '#120c18', '#1e1428', '#2c1c3c', '#3c2450', '#1a1a22', '#2a2a36',
       '#5a3a10', '#8a5c18', '#b8882a', '#e8c04a', '#fff0a8', '#ffffff',
       '#3a4a2a', '#6a2a7a', '#9a9aae']


def nearest(pal_rgb, rgb):
    best, bi = 1 << 30, 0
    for i, p in enumerate(pal_rgb):
        d = sum((a - b) ** 2 for a, b in zip(p, rgb))
        if d < best:
            best, bi = d, i
    return bi


def render():
    rnd = random.Random(7)
    im = Image.new('RGB', (240, 160), (6, 5, 10))
    d = ImageDraw.Draw(im)
    # violet wash from the bottom, banded
    for y in range(160):
        t = max(0, (y - 70) / 90.0)
        band = [(6, 5, 10), (18, 12, 24), (30, 20, 40), (44, 28, 60), (60, 36, 80)]
        c = band[min(4, int(t * 5))]
        d.line([(0, y), (239, y)], fill=c)
    # ruined pillars
    for x in (18, 206):
        d.rectangle([x, 60, x + 16, 160], fill=(26, 26, 34))
        d.rectangle([x + 4, 60, x + 12, 160], fill=(42, 42, 54))
        d.rectangle([x - 2, 56, x + 18, 62], fill=(42, 42, 54))
    # the name
    path = next(p for p in FONTS if os.path.exists(p))
    fnt = ImageFont.truetype(path, 40)
    text = 'BARTGAME'
    bbox = d.textbbox((0, 0), text, font=fnt)
    tw = bbox[2] - bbox[0]
    tx = (240 - tw) // 2 - bbox[0]
    ty = 44
    mask = Image.new('L', (240, 160), 0)
    ImageDraw.Draw(mask).text((tx, ty), text, font=fnt, fill=255)
    # shadow
    sh = Image.new('L', (240, 160), 0)
    ImageDraw.Draw(sh).text((tx + 2, ty + 3), text, font=fnt, fill=255)
    px = im.load()
    mpx = mask.load()
    spx = sh.load()
    for y in range(160):
        for x in range(240):
            if spx[x, y] > 128:
                px[x, y] = (18, 12, 24)
    for y in range(160):
        for x in range(240):
            if mpx[x, y] > 128:
                # gold gradient: bright band near the top third
                t = (y - ty) / 48.0
                if t < 0.35:
                    px[x, y] = (255, 240, 168)
                elif t < 0.55:
                    px[x, y] = (232, 192, 74)
                elif t < 0.8:
                    px[x, y] = (184, 136, 42)
                else:
                    px[x, y] = (138, 92, 24)
    # a thin gold rule under the name
    d.line([(60, 96), (180, 96)], fill=(184, 136, 42))
    d.line([(80, 99), (160, 99)], fill=(90, 58, 16))
    # motes
    for _ in range(60):
        x, y = rnd.randrange(240), rnd.randrange(160)
        c = rnd.choice([(232, 192, 74), (255, 240, 168), (154, 154, 174)])
        px[x, y] = c
        if rnd.random() < 0.3:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < 240 and 0 <= y + dy < 160:
                    px[x + dx, y + dy] = (90, 58, 16)
    # blight tendrils at the bottom
    for i in range(12):
        x0 = 20 * i + rnd.randrange(10)
        for y in range(159, 118 - rnd.randrange(20), -1):
            xx = x0 + int(3 * ((y // 6) % 2)) + rnd.randrange(2)
            if 0 <= xx < 240:
                px[xx, y] = (58, 74, 42) if y % 9 else (154, 154, 174)
    pal_rgb = [tuple(int(c.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) for c in PAL]
    out = [[nearest(pal_rgb, px[x, y]) for x in range(240)] for y in range(160)]
    return out, PAL


if __name__ == '__main__':
    pix, pal = render()
    pal_rgb = [tuple(int(c.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) for c in pal]
    im = Image.new('RGB', (240, 160))
    p = im.load()
    for y in range(160):
        for x in range(240):
            p[x, y] = pal_rgb[pix[y][x]]
    im.resize((480, 320)).save('/tmp/title.png')
    print('wrote /tmp/title.png')
