"""The pause menu's backdrop: one great plank of rotted wood, 240x160,
its grain running the width of the screen (periodic every 40 pixels,
so the tiles repeat along a row), knots, a long crack, patches of rot
ringed with mould, grime in the corners, and mushrooms growing from
the rot. Palette 'menu': 1 ink, 2 parchment, 3 parchment dark, 6 moss,
7 dark green, A tan, C blight purple, D plank dark, E plank, F plank
light. Emitted as deduplicated 8x8 tiles and a 30x20 map."""
import math
import random

from px import Canvas, ball

W, H = 240, 160
PERIOD = 32


def grain():
    c = Canvas(W, H, 0xE)
    rnd = random.Random(7)
    # streaks: each a wavy line across the whole width, period PERIOD
    y = 1.0
    while y < H:
        tone = 0xD if rnd.random() < 0.6 else 0xF
        thick = 1 if rnd.random() < 0.75 else 2
        amp = rnd.uniform(0.6, 1.8)
        phase = rnd.uniform(0, 2 * math.pi)
        for x in range(W):
            yy = y + amp * math.sin(2 * math.pi * x / PERIOD + phase) + 0.4 * math.sin(4 * math.pi * x / PERIOD + phase * 2)
            iy = int(yy)
            for k in range(thick):
                if 0 <= iy + k < H:
                    c.set(x, iy + k, tone)
        y += rnd.uniform(3.0, 6.5)
    # the plank's bevelled edges top and bottom
    for x in range(W):
        c.set(x, 0, 1); c.set(x, 1, 0xF); c.set(x, H - 2, 0xD); c.set(x, H - 1, 1)
    return c


def knot(c, cx, cy, rx, ry):
    for y in range(int(cy - ry - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            e = dx * dx + dy * dy
            if e <= 1.0:
                ring = int(e * 4) & 1
                c.set(x, y, 0xD if ring else 0xE)
                if e < 0.12:
                    c.set(x, y, 1)
            elif e <= 1.5:
                c.set(x, y, 0xD if ((x + y) & 1) else c.get(x, y))


def rot(c, cx, cy, rx, ry, seed):
    """a patch of rot: dark, soft-edged, mould at its rim, purple spots"""
    rnd = random.Random(seed)
    lobes = [(cx + rnd.uniform(-rx * 0.5, rx * 0.5), cy + rnd.uniform(-ry * 0.5, ry * 0.5), rnd.uniform(rx * 0.5, rx), rnd.uniform(ry * 0.5, ry)) for _ in range(4)]
    for y in range(int(cy - ry * 1.6), int(cy + ry * 1.6) + 1):
        for x in range(int(cx - rx * 1.6), int(cx + rx * 1.6) + 1):
            best = 9.0
            for (lx, ly, lrx, lry) in lobes:
                dx, dy = (x + 0.5 - lx) / lrx, (y + 0.5 - ly) / lry
                best = min(best, dx * dx + dy * dy)
            if best <= 0.5:
                c.set(x, y, 1)
            elif best <= 0.85:
                c.set(x, y, 0xD if ((x * 3 + y) & 3) else 7)
            elif best <= 1.15:
                c.set(x, y, 7 if ((x + y) & 1) else 6)
            elif best <= 1.4 and rnd.random() < 0.3:
                c.set(x, y, 6)
    for _ in range(6):
        x, y = int(cx + rnd.uniform(-rx, rx)), int(cy + rnd.uniform(-ry, ry))
        c.set(x, y, 0xC); c.set(x + 1, y, 0xC)


def mushroom(c, x, y, r):
    """a cap of tan with pale spots on a pale stem, rooted in the rot"""
    c.vline(x, y, y + r + 1, 3); c.vline(x + 1, y, y + r + 1, 2)
    ball(c, x + 1, y - 1, r + 1, r * 0.7 + 1, (0xA, 0xA, 0xA, 2, 2), gleam=False)
    c.set(x, y - 2, 2); c.set(x + 2, y - 1, 2)
    for yy in range(int(y - r * 0.7 - 2), y + 1):
        for xx in range(int(x - r), int(x + r + 3)):
            if c.get(xx, yy) in (0xA, 2):
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if c.get(xx + dx, yy + dy) not in (0xA, 2, 1, 3):
                        c.set(xx + dx, yy + dy, 1)


def crack(c, pts):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            x, y = x0 + (x1 - x0) * i // n, y0 + (y1 - y0) * i // n
            c.set(x, y, 1)
            if c.get(x + 1, y) not in (1,):
                c.set(x + 1, y, 0xD)


def grime(c, cx, cy, rx, ry, seed):
    rnd = random.Random(seed)
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            e = dx * dx + dy * dy
            if e <= 1.0 and rnd.random() < (1.0 - e) * 0.8 and c.get(x, y) in (0xE, 0xF):
                c.set(x, y, 0xD)


def build():
    c = grain()
    knot(c, 212, 44, 7, 5)
    rot(c, 30, 26, 13, 7, 3)
    rot(c, 204, 132, 15, 8, 5)
    crack(c, [(150, 2), (158, 18), (155, 36), (163, 56)])
    grime(c, 232, 8, 14, 10, 12)
    grime(c, 6, 152, 12, 9, 11)
    mushroom(c, 24, 22, 3)
    mushroom(c, 36, 28, 2)
    mushroom(c, 208, 126, 3)
    mushroom(c, 198, 134, 2)
    return c.rows()


ROWS = build()


def tiles_and_map():
    """deduplicated tiles (lists of 64 indices) and the 30x20 map of tile ids"""
    tiles, index, m = [], {}, []
    for ty in range(H // 8):
        for tx in range(W // 8):
            key = tuple(int(ROWS[ty * 8 + y][tx * 8 + x], 16) for y in range(8) for x in range(8))
            if key not in index:
                index[key] = len(tiles)
                tiles.append(key)
            m.append(index[key])
    return tiles, m


if __name__ == '__main__':
    t, m = tiles_and_map()
    print(len(t), 'unique tiles')
