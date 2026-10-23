"""Dialogue portraits, 32x32, palette 'portrait': 1 outline, 2 petal deep,
3 petal red, 4 petal orange, 5 face cream, 6 face shadow, 7 green,
8 purple hide, 9 purple hide dark, A red, B red dark, C violet,
D lavender (and steel), E gold, F white.

Built from filled shapes with the painter, then hand touches: each face
is a lit oval with a shadow on the lower right, eyes with a glint, and
a dark outline round everything.
"""
import math

from px import Canvas, L, compose, blank  # noqa: F401


def disc(c, cx, cy, rx, ry, col, shade=None, shade_col=None):
    for y in range(c.h):
        for x in range(c.w):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            e = dx * dx + dy * dy
            if e <= 1.0:
                if shade and e > shade and dx + dy > 0.3:
                    c.set(x, y, shade_col)
                else:
                    c.set(x, y, col)


def cone(c, apex_x, apex_y, base_y, half_w, col, light=None):
    """a pointed hood or hat: widens from the apex to base_y"""
    for y in range(apex_y, base_y + 1):
        t = (y - apex_y) / float(max(1, base_y - apex_y))
        hw = half_w * t
        for x in range(c.w):
            if abs(x + 0.5 - apex_x) <= hw + 0.5:
                c.set(x, y, light if (light is not None and x + 0.5 - apex_x < -hw * 0.45) else col)


def eye(c, x, y, w, h, iris=1, glint=0xf):
    for yy in range(h):
        for xx in range(w):
            c.set(x + xx, y + yy, iris)
    c.set(x, y, glint)


def line(c, x0, y0, x1, y1, col):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        c.set(x0 + (x1 - x0) * i // n, y0 + (y1 - y0) * i // n, col)


# ---------------------------------------------------------------- hero --
def hero_portrait(surprised=False):
    c = Canvas(32, 32)
    cx, cy = 16.0, 15.0
    for k in range(8):
        ang = k * math.pi / 4 + math.pi / 8
        px, py = cx + math.cos(ang) * 9.6, cy + math.sin(ang) * 9.0
        for y in range(32):
            for x in range(32):
                dx, dy = x + 0.5 - px, y + 0.5 - py
                if dx * dx + dy * dy <= 5.8 * 5.8:
                    ddx, ddy = x + 0.5 - cx, y + 0.5 - cy
                    d = (ddx * ddx + ddy * ddy) ** 0.5
                    c.set(x, y, 4 if (d > 12.5 and y < cy + 2) else 3 if d > 9.5 else 2)
    # the collar below
    for y in range(26, 32):
        for x in range(32):
            if abs(x + 0.5 - cx) <= 6 + (y - 26) * 1.2:
                c.set(x, y, 7)
    disc(c, cx, cy + 0.5, 8.8, 8.8, 5, 0.62, 6)
    if surprised:
        eye(c, 10, 11, 4, 5); eye(c, 18, 11, 4, 5)
        disc(c, 16, 21, 2.2, 2.6, 1)
        disc(c, 16, 21.5, 1.2, 1.5, 0xb)
    else:
        eye(c, 10, 12, 3, 4); eye(c, 19, 12, 3, 4)
        for (x, y) in ((13, 20), (14, 21), (15, 21), (16, 21), (17, 21), (18, 20)):
            c.set(x, y, 1)
        c.set(11, 18, 6); c.set(21, 18, 6)
    c.outline(1)
    return c.rows()


# ------------------------------------------------------------- peddler --
def peddler_portrait():
    c = Canvas(32, 32)
    cone(c, 16, 0, 31, 15, 0xa, 0xb)
    # the hood's dark inside around the face
    disc(c, 16, 18, 10, 11, 0xb)
    disc(c, 16, 18, 8, 9, 8, 0.6, 9)
    # the great nose
    for (x, y) in ((17, 17), (18, 17), (18, 18), (19, 18), (19, 19), (20, 19), (20, 20), (21, 20), (21, 21), (20, 21), (19, 21), (18, 20)):
        c.set(x, y, 8)
    for (x, y) in ((19, 20), (20, 21), (21, 22)):
        c.set(x, y, 9)
    line(c, 17, 16, 22, 22, 1)
    c.set(22, 22, 1); c.set(21, 23, 1)
    # yellow eyes, a frown
    eye(c, 10, 14, 3, 2, 0xe, 0xf); c.set(12, 15, 1)
    eye(c, 18, 14, 3, 2, 0xe, 0xf); c.set(19, 15, 1)
    line(c, 9, 12, 13, 13, 1); line(c, 17, 13, 21, 12, 1)
    for (x, y) in ((11, 24), (12, 23), (13, 23), (14, 23), (15, 23), (16, 23), (17, 24)):
        c.set(x, y, 1)
    # an earring
    c.set(8, 20, 0xe); c.set(8, 21, 0xe); c.set(7, 21, 0xe)
    c.outline(1)
    return c.rows()


# ---------------------------------------------------------- gatekeeper --
def gatekeeper_portrait():
    c = Canvas(32, 32)
    cone(c, 15, 0, 14, 9, 0xc, 0xd)
    disc(c, 16, 15, 14, 3, 0xc)
    for x in range(3, 29):
        c.set(x, 14, 0xd)
    for x in range(7, 24):
        c.set(x, 13, 0xe)
    disc(c, 16, 23, 7, 8.5, 5, 0.6, 6)
    # hair falling at the sides
    for y in range(17, 31):
        for x in (8, 9, 22, 23):
            if c.get(x, y) < 0 or c.get(x, y) == 5:
                c.set(x, y, 0xd)
    # the long nose
    line(c, 17, 21, 20, 27, 5)
    line(c, 18, 21, 21, 27, 6)
    line(c, 19, 22, 22, 28, 1)
    c.set(21, 28, 1); c.set(20, 28, 1)
    # eyes under heavy lids
    eye(c, 12, 20, 2, 2); eye(c, 19, 20, 2, 2)
    line(c, 11, 19, 14, 19, 1); line(c, 18, 19, 21, 19, 1)
    c.set(13, 24, 1); c.set(14, 25, 1); c.set(15, 25, 1); c.set(16, 25, 1)
    # the collar
    for y in range(29, 32):
        for x in range(6 + (y - 29), 26 - (y - 29)):
            c.set(x, y, 0xc)
    c.set(16, 30, 0xe); c.set(15, 30, 0xe)
    c.outline(1)
    return c.rows()


# -------------------------------------------------------------- hermit --
def hermit_portrait():
    c = Canvas(32, 32)
    disc(c, 16, 13, 9, 9.5, 5, 0.6, 6)
    # the beard
    for y in range(19, 32):
        hw = 9 - (y - 19) * 0.35
        for x in range(32):
            if abs(x + 0.5 - 16) <= hw:
                c.set(x, y, 0xf if (x + y) % 3 else 0xd)
    for y in range(19, 23):
        for x in range(12, 21):
            if abs(x - 16) < 3 and y < 21:
                c.set(x, y, 5)
    # tired eyes, a scar
    eye(c, 11, 11, 3, 2); eye(c, 18, 11, 3, 2)
    line(c, 10, 14, 13, 14, 6); line(c, 18, 14, 21, 14, 6)
    line(c, 20, 6, 23, 10, 0xb)
    line(c, 14, 18, 18, 18, 1)
    # a steel gorget
    for y in range(28, 32):
        for x in range(4, 28):
            c.set(x, y, 0xd)
    for x in range(4, 28, 3):
        c.set(x, 29, 1)
    c.outline(1)
    return c.rows()


# ----------------------------------------------------------------- nun --
def nun_portrait():
    c = Canvas(32, 32)
    disc(c, 16, 16, 12, 13.5, 0xf, 0.7, 0xd)
    for y in range(26, 32):
        for x in range(32):
            if abs(x + 0.5 - 16) <= 13:
                c.set(x, y, 0xc)
    disc(c, 16, 17, 7, 8.5, 5, 0.6, 6)
    # eyes closed, a tear
    line(c, 11, 16, 13, 16, 1); line(c, 19, 16, 21, 16, 1)
    c.set(10, 15, 1); c.set(14, 15, 1); c.set(18, 15, 1); c.set(22, 15, 1)
    c.set(20, 18, 0xd); c.set(20, 19, 0xd); c.set(20, 20, 0xf)
    line(c, 14, 22, 18, 22, 1)
    c.set(16, 29, 0xe); c.set(15, 29, 0xe); c.set(17, 29, 0xe); c.set(16, 28, 0xe); c.set(16, 30, 0xe)
    c.outline(1)
    return c.rows()


# ------------------------------------------------------------ gardener --
def gardener_portrait():
    c = Canvas(32, 32)
    disc(c, 16, 12, 12.5, 12, 7, 0.55, 1)
    disc(c, 16, 17, 7.5, 8, 5, 0.6, 6)
    # the blindfold
    for y in range(14, 18):
        for x in range(7, 26):
            c.set(x, y, 0xf if y != 17 else 0xd)
    # the beard
    for y in range(21, 31):
        hw = 7 - (y - 21) * 0.3
        for x in range(32):
            if abs(x + 0.5 - 16) <= hw:
                c.set(x, y, 0xd if (x + y) % 3 else 0xf)
    line(c, 13, 20, 19, 20, 1)
    c.set(16, 19, 6)
    c.outline(1)
    return c.rows()


PORTRAITS = {
    'hero': hero_portrait(),
    'hero_surprised': hero_portrait(True),
    'peddler': peddler_portrait(),
    'gatekeeper': gatekeeper_portrait(),
    'hermit': hermit_portrait(),
    'nun': nun_portrait(),
    'gardener': gardener_portrait(),
}
