"""The items at 32x32, drawn 24 pixels wide: the pickups on the ground
(pick32) and the treasures and tools (icon32) for the pause menu and
the item-get. Palette 'fx': 1 outline, 2-4 red dark..bright, 5-7 gold
dark..bright, 8 white, 9-B violet dark..light, C-E grey dark..light,
F blue glow."""
import math

from px import Canvas, ball, blank
from portraits import disc, line


def canvas():
    return Canvas(32, 32)


def done(c):
    c.outline(1)
    return c.rows()


def heart_shape(c, cx, cy, r, tones, top=None):
    """a plump heart: two lobes and a point, lit from the upper left"""
    deep, mid, light, gleam = tones
    lx, rx = cx - r * 0.55, cx + r * 0.55
    for y in range(c.h):
        for x in range(c.w):
            px, py = x + 0.5, y + 0.5
            in_l = (px - lx) ** 2 + (py - cy) ** 2 <= (r * 0.62) ** 2
            in_r = (px - rx) ** 2 + (py - cy) ** 2 <= (r * 0.62) ** 2
            tip = cy + r * 1.05
            in_t = py >= cy and py <= tip and abs(px - cx) <= (tip - py) * (r * 1.15) / (tip - cy)
            if in_l or in_r or in_t:
                if top is not None and py > top:
                    continue
                shade = (px - cx) + (py - cy) * 0.8
                c.set(x, y, deep if shade > r * 0.5 else light if shade < -r * 0.5 else mid)
    c.set(int(lx - 1), int(cy - r * 0.35), gleam); c.set(int(lx), int(cy - r * 0.35), gleam); c.set(int(lx - 1), int(cy - r * 0.35) + 1, gleam)


def heart():
    c = canvas()
    heart_shape(c, 16, 14, 9, (2, 3, 4, 8))
    return done(c)


def coin(cx, cy, r):
    c = canvas()
    ball(c, cx, cy, r, r, (5, 5, 6, 7, 8))
    for y in range(c.h):
        for x in range(c.w):
            d = ((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2) ** 0.5
            if r - 2.2 < d <= r - 1.2:
                c.set(x, y, 5)
    # a four-petal mark
    for (dx, dy) in ((0, -3), (0, 3), (-3, 0), (3, 0)):
        disc(c, cx + dx, cy + dy, 1.8, 1.8, 5)
    disc(c, cx, cy, 1.3, 1.3, 7)
    return c


def gilt():
    return done(coin(16, 17, 9.5))


def pouch():
    c = canvas()
    # a violet purse tied with gold, coins spilling
    for y in range(8, 27):
        hw = 4 + (y - 8) * 0.55 if y < 22 else 11.5 - (y - 22) * 1.2
        for x in range(32):
            if abs(x + 0.5 - 16) <= hw:
                c.set(x, y, 0xA if (x + 0.5 - 16) < -hw * 0.3 else 9 if (x + 0.5 - 16) > hw * 0.5 else 0xA)
    for x in range(11, 22):
        c.set(x, 11, 6); c.set(x, 12, 5)
    c.set(10, 10, 6); c.set(22, 10, 6); c.set(9, 8, 6); c.set(23, 8, 6)
    for y in range(13, 24):
        c.set(16 + (y & 1), y, 9)
    for (x, y) in ((6, 24), (25, 25), (8, 27), (23, 27)):
        disc(c, x, y, 2.5, 2.0, 6); c.set(x - 1, y - 1, 7)
    return done(c)


def seed(fuse_len):
    c = canvas()
    ball(c, 16, 18, 9.5, 9, (9, 9, 0xA, 0xB, 8))
    for y in range(9, 28):
        c.set(16, y, 9)
    c.set(15, 9, 9); c.set(17, 9, 9)
    x, y = 16, 8
    for i in range(fuse_len):
        c.set(x + i, y - i, 0xD if i % 2 else 0xE)
    sx, sy = x + fuse_len, y - fuse_len
    for (dx, dy) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        c.set(sx + dx, sy + dy, 7)
    c.set(sx, sy, 8)
    return done(c)


def key():
    c = canvas()
    disc(c, 16, 9, 5.5, 5, 6, 0.55, 5)
    disc(c, 16, 9, 2.2, 2.2, 1)
    c.rect(15, 13, 17, 27, 6); c.vline(17, 13, 27, 5); c.vline(15, 13, 27, 7)
    c.rect(18, 22, 21, 23, 6); c.rect(18, 25, 20, 26, 6); c.set(21, 23, 5); c.set(20, 26, 5)
    c.set(14, 9, 7); c.set(13, 8, 7)
    return done(c)


def arrow_on(c, x0, y0, x1, y1):
    line(c, x0, y0, x1, y1, 0xD)
    line(c, x0 + 1, y0, x1 + 1, y1, 0xC)
    # the head: a few pixels past the point
    c.set(x1, y1, 8); c.set(x1 - 1, y1, 8); c.set(x1, y1 + 1, 8); c.set(x1 - 2, y1, 0xE); c.set(x1, y1 + 2, 0xE); c.set(x1 - 1, y1 + 1, 8)
    # the fletching
    for k in range(3):
        c.set(x0 + k, y0 - 1 - k, 3); c.set(x0 + 1 + k, y0 + 1 - k, 2); c.set(x0 + k, y0 - 2 - k, 3)


def arrow1():
    c = canvas()
    arrow_on(c, 6, 26, 25, 7)
    return done(c)


def arrow5():
    c = canvas()
    for i in range(3):
        arrow_on(c, 4 + i * 4, 26, 21 + i * 4, 9)
    for k in range(10):
        c.set(10 + k, 20 - k * 0 + (k // 3), 6)
        c.set(10 + k, 21 + (k // 3), 5)
    return done(c)


def quiver():
    c = canvas()
    c.rect(9, 10, 22, 27, 5)
    c.rect(10, 11, 21, 26, 6)
    c.hline(9, 22, 10, 7); c.vline(9, 10, 27, 7)
    c.hline(9, 22, 17, 5); c.hline(9, 22, 18, 7)
    for i, x in enumerate((11, 14, 17, 20)):
        top = 3 + (i % 2) * 2
        c.vline(x, top, 10, 0xD); c.vline(x + 1, top, 10, 0xC)
        c.set(x, top - 1, 8); c.set(x + 1, top - 1, 8); c.set(x, top - 2, 8)
    return done(c)


def gem():
    c = canvas()
    # a lozenge of violet glass with a blue light, in a gold setting
    for y in range(4, 24):
        hw = (y - 4) * 0.9 if y < 12 else (23 - y) * 0.75
        for x in range(32):
            dx = x + 0.5 - 16
            if abs(dx) <= hw:
                c.set(x, y, 0xB if dx < -hw * 0.3 and y < 12 else 0xF if abs(dx) < 1.5 and 9 <= y <= 14 else 9 if dx > hw * 0.4 else 0xA)
    c.rect(10, 24, 21, 25, 6); c.rect(12, 26, 19, 27, 5); c.set(10, 24, 7); c.set(11, 24, 7)
    c.set(13, 7, 8); c.set(12, 8, 8)
    return done(c)


def chalice(flame=False, glow=True):
    c = canvas()
    # the cup
    for y in range(7, 17):
        hw = 8.5 - (y - 7) * 0.65
        for x in range(32):
            dx = x + 0.5 - 16
            if abs(dx) <= hw:
                c.set(x, y, 7 if dx < -hw * 0.45 else 5 if dx > hw * 0.45 else 6)
    c.hline(8, 23, 7, 7); c.hline(8, 23, 8, 5)
    if glow:
        for x in range(11, 21):
            c.set(x, 9, 0xF)
    c.rect(15, 17, 16, 22, 6); c.vline(16, 17, 22, 5)
    c.rect(11, 23, 20, 24, 6); c.rect(9, 25, 22, 26, 5); c.hline(9, 22, 25, 7)
    if flame:
        pts = [(16, 2), (15, 3), (16, 3), (17, 3), (14, 4), (15, 4), (16, 4), (17, 4), (18, 4), (14, 5), (15, 5), (16, 5), (17, 5), (18, 5), (15, 6), (16, 6), (17, 6)]
        for (x, y) in pts:
            c.set(x, y, 3)
        for (x, y) in ((16, 4), (16, 5), (15, 5), (16, 6)):
            c.set(x, y, 7)
        c.set(16, 5, 8)
        for (x, y) in ((14, 4), (18, 4), (15, 3)):
            c.set(x, y, 4)
    return done(c)


def cloak():
    c = canvas()
    # a cape of petals: shoulders, a flare, a scalloped hem
    for y in range(6, 27):
        hw = 5 + (y - 6) * 0.4 if y < 22 else 11.5
        for x in range(32):
            dx = x + 0.5 - 16
            if abs(dx) <= hw:
                scallop = (y >= 23) and ((int(x + 1) // 4) % 2 == 0) and y >= 25
                if scallop:
                    continue
                c.set(x, y, 4 if dx < -hw * 0.45 else 2 if dx > hw * 0.5 else 3)
    c.rect(13, 6, 18, 8, 6); c.set(13, 6, 7); c.set(14, 6, 7)
    for y in range(9, 24):
        c.set(16, y, 2)
    c.set(9, 12, 4); c.set(8, 15, 4)
    return done(c)


def heart_piece():
    c = canvas()
    heart_shape(c, 16, 14, 9, (0xC, 0xC, 0xD, 0xD))
    # the found quarter: the upper left
    d = canvas()
    heart_shape(d, 16, 14, 9, (2, 3, 4, 8))
    for y in range(32):
        for x in range(32):
            if x < 16 and y < 14 and d.get(x, y) >= 0:
                c.set(x, y, d.get(x, y))
    c.vline(16, 5, 14, 1); c.hline(7, 16, 14, 1)
    return done(c)


def heart_container():
    c = canvas()
    disc(c, 16, 16, 12.5, 12.5, 6)
    disc(c, 16, 16, 10.5, 10.5, 5)
    for k in range(12):
        a = k * math.pi / 6
        c.set(int(16 + math.cos(a) * 11.5), int(16 + math.sin(a) * 11.5), 7)
    heart_shape(c, 16, 15, 8, (2, 3, 4, 8))
    return done(c)


def gauntlet():
    c = canvas()
    c.rect(9, 12, 22, 24, 0xD)
    for x in (10, 13, 16, 19):
        c.rect(x, 4, x + 2, 12, 0xD); c.vline(x + 2, 4, 12, 0xC); c.set(x, 4, 0xE)
    c.rect(5, 14, 8, 20, 0xD); c.vline(5, 14, 20, 0xE)
    c.rect(9, 25, 22, 27, 0xC)
    for x in (11, 14, 17, 20):
        c.set(x, 13, 6); c.set(x + 1, 13, 7); c.set(x, 14, 5)
    for (x, y) in ((12, 18), (17, 20), (14, 22), (19, 16)):
        c.set(x, y, 0xC); c.set(x + 1, y + 1, 0xC)
    c.hline(10, 21, 12, 0xC)
    return done(c)


def bow():
    c = canvas()
    for y in range(3, 29):
        t = (y - 16) / 13.0
        x = 9 + (1 - t * t) * 7
        c.set(int(x), y, 6); c.set(int(x) + 1, y, 5); c.set(int(x) - 1, y, 7)
        c.set(9, y, 0xD)
    c.set(9, 3, 1); c.set(9, 28, 1)
    line(c, 10, 15, 27, 15, 0xD); line(c, 10, 16, 26, 16, 0xC)
    c.set(27, 15, 8); c.set(28, 15, 8); c.set(26, 14, 8); c.set(26, 16, 8)
    for k in range(3):
        c.set(10 + k, 13 - k, 3); c.set(10 + k, 18 + k, 3)
    return done(c)


def hubcap():
    c = canvas()
    ball(c, 16, 16, 11.5, 11.5, (0xC, 0xC, 0xD, 0xE, 0xE))
    for y in range(32):
        for x in range(32):
            d = ((x + 0.5 - 16) ** 2 + (y + 0.5 - 16) ** 2) ** 0.5
            if 8.2 < d <= 9.0 and (x + y) % 2 == 0:
                c.set(x, y, 1)
            if 4.4 < d <= 5.2 and (x + y) % 2 == 1:
                c.set(x, y, 1)
    for k in range(8):
        a = k * math.pi / 4
        c.set(int(16 + math.cos(a) * 6.5), int(16 + math.sin(a) * 6.5), 1)
    c.set(10, 8, 0xB); c.set(9, 9, 0xB); c.set(11, 7, 0xB)
    return done(c)


def map_scroll():
    c = canvas()
    c.rect(6, 6, 25, 25, 7)
    c.rect(6, 6, 25, 7, 6); c.rect(6, 24, 25, 25, 6); c.vline(6, 6, 25, 6); c.vline(25, 6, 25, 5)
    c.rect(4, 5, 6, 26, 6); c.rect(25, 5, 27, 26, 6); c.vline(4, 5, 26, 7); c.vline(27, 5, 26, 5)
    for k in range(6):
        c.hline(9, 22, 9 + k * 2.6 if False else 9 + int(k * 2.6), 5)
        c.vline(9 + int(k * 2.6), 9, 22, 5)
    c.set(14, 14, 3); c.set(15, 15, 3); c.set(14, 15, 3); c.set(15, 14, 3)
    return done(c)


def astrolabe():
    c = canvas()
    disc(c, 16, 17, 11, 11, 6)
    disc(c, 16, 17, 9, 9, 0)
    disc(c, 16, 17, 6.5, 6.5, 5)
    disc(c, 16, 17, 4.5, 4.5, 0)
    for k in range(12):
        a = k * math.pi / 6
        c.set(int(16 + math.cos(a) * 10), int(17 + math.sin(a) * 10), 7)
    line(c, 8, 25, 24, 9, 5); line(c, 9, 25, 25, 9, 7)
    c.rect(15, 3, 17, 6, 6); c.set(16, 2, 7); c.set(14, 4, 6); c.set(18, 4, 6)
    for (x, y) in ((16, 15), (16, 19), (14, 17), (18, 17), (16, 17)):
        c.set(x, y, 8)
    c.set(16, 17, 0xF)
    return done(c)


def sword():
    c = canvas()
    for y in range(3, 20):
        c.set(15, y, 8); c.set(16, y, 0xE); c.set(17, y, 0xD)
    c.set(16, 2, 8)
    c.rect(11, 20, 21, 21, 6); c.hline(11, 21, 20, 7); c.set(11, 21, 5); c.set(21, 21, 5)
    c.rect(15, 22, 17, 26, 0xC); c.vline(15, 22, 26, 0xD)
    c.rect(14, 27, 18, 28, 6); c.set(14, 27, 7)
    return done(c)


def shield():
    c = canvas()
    disc(c, 16, 16, 9.5, 12, 6)
    disc(c, 16, 16, 8, 10.5, 5)
    for x in (12, 16, 20):
        c.vline(x, 7, 25, 6)
    for y in (9, 16, 23):
        c.hline(9, 23, y, 7)
    for (x, y) in ((11, 9), (21, 9), (11, 23), (21, 23), (16, 16)):
        c.set(x, y, 7); c.set(x + 1, y, 6)
    return done(c)


PICK32 = {
    'heart': heart(),
    'gilt': gilt(),
    'bomb_pickup': seed(4),
    'gilt_big': pouch(),
    'key': key(),
    'relic': gem(),
    'grail': chalice(flame=False, glow=True),
    'arrow1': arrow1(),
    'arrow5': arrow5(),
    'arrow10': quiver(),
}
ICON32 = {
    'none': blank(32, 32),
    'bombs': seed(7),
    'lamp': chalice(flame=True, glow=False),
    'cloak': cloak(),
    'key': key(),
    'heart_piece': heart_piece(),
    'heart_container': heart_container(),
    'gilt_big': pouch(),
    'relic': gem(),
    'gauntlet': gauntlet(),
    'bow': bow(),
    'hubcap': hubcap(),
    'map': map_scroll(),
    'astrolabe': astrolabe(),
    'sword': sword(),
    'shield': shield(),
}
