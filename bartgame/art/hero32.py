"""The Bloom at 32x32, from the style boards: the sheet's idle, walk and
direction frames and the big drawing, with the rest of the states made
from them: a leg bob for the front and back walks, the curled ball of
the roll in the boards' colours, arms raised for the load, the sinking
frames for water and holes."""
import math

import style as ST
from px import Canvas, ball, hflip, blank, compose

SRC = ST.HERO_SRC
PAL = ST.PAL_HERO


def nearest(rgb):
    best, bd = 1, 1 << 30
    for i, c in enumerate(PAL):
        d = sum((rgb[k] - c[k]) ** 2 for k in range(3))
        if d < bd:
            bd = d
            best = i + 1
    return best


# the colours the procedural pieces want, as the board palette has them
C_OUT, C_GREEN_D, C_GREEN, C_GREEN_L = 1, nearest((28, 74, 40)), nearest((46, 128, 64)), nearest((88, 184, 88))
C_RED, C_ORANGE, C_ORANGE_L, C_CREAM, C_BOOT = nearest((240, 72, 40)), nearest((255, 128, 48)), nearest((255, 176, 72)), nearest((255, 248, 232)), nearest((90, 52, 24))


def bob(rows, side):
    """one leg lifted: the lower rows of that half moved up a pixel"""
    out = [list(r) for r in rows]
    h = len(rows)
    lo = h - 7
    x0, x1 = (0, 16) if side == 0 else (16, 32)
    for y in range(lo, h):
        for x in range(x0, x1):
            out[y - 1][x] = rows[y][x] if rows[y][x] != '.' else out[y - 1][x]
    for x in range(x0, x1):
        out[h - 1][x] = '.'
    return [''.join(r) for r in out]


def shift_down(rows, dy):
    return (['.' * len(rows[0])] * dy + rows)[:len(rows)]


def shift_up(rows, dy):
    return (rows + ['.' * len(rows[0])] * dy)[dy:]


def arms_up(rows):
    """arms straight up from the shoulders, in the tunic's green"""
    out = [list(r) for r in rows]
    h = len(rows)
    for y in range(h - 24, h - 14):
        for x in (9, 10, 21, 22):
            if 0 <= y < h:
                out[y][x] = '%x' % C_GREEN
    for x in (9, 10, 21, 22):
        out[h - 25][x] = '%x' % C_CREAM
    for y in range(h - 25, h - 14):
        for x in (8, 11, 20, 23):
            if out[y][x] == '.':
                out[y][x] = '1'
    return [''.join(r) for r in out]


def roll_ball(ang):
    c = Canvas(32, 32)
    ball(c, 16, 20, 11, 11, (C_GREEN_D, C_GREEN_D, C_GREEN, C_GREEN_L, C_GREEN_L))
    a = math.radians(ang)
    fx, fy = 16 + math.sin(a) * 5.4, 20 - math.cos(a) * 5.4
    for y in range(32):
        for x in range(32):
            dx, dy = x + 0.5 - 16, y + 0.5 - 20
            d = (dx * dx + dy * dy) ** 0.5
            if d > 11.3:
                continue
            pa = math.atan2(dx, -dy)
            diff = (pa - a + math.pi) % (2 * math.pi) - math.pi
            if abs(diff) < 1.0 and d > 3.5:
                c.set(x, y, C_ORANGE_L if d > 9.5 else C_ORANGE if d > 7.3 else C_RED)
            back = (pa - a) % (2 * math.pi) - math.pi
            if abs(back) < 0.45 and 7 < d < 10.4:
                c.set(x, y, C_BOOT)
            if (x + 0.5 - fx) ** 2 + (y + 0.5 - fy) ** 2 <= 3.0 * 3.0:
                c.set(x, y, C_CREAM)
    c.outline(1)
    return c.rows()


IDLE_S, IDLE_N, IDLE_E = SRC['idle_s2'], SRC['dir_n'], SRC['dir_e']
FRAMES = {
    'idle_s': IDLE_S, 'walk_s1': bob(IDLE_S, 0), 'walk_s2': bob(IDLE_S, 1),
    'idle_n': IDLE_N, 'walk_n1': bob(IDLE_N, 0), 'walk_n2': bob(IDLE_N, 1),
    'idle_e': IDLE_E, 'walk_e1': SRC['walk_s1'], 'walk_e2': SRC['walk_s3'],
    'atk_s': IDLE_S, 'atk_n': IDLE_N, 'atk_e': IDLE_E,
    'atk_s1': IDLE_S, 'atk_n1': IDLE_N, 'atk_e1': IDLE_E,
    'atk_s3': IDLE_S, 'atk_n3': IDLE_N, 'atk_e3': IDLE_E,
    'roll_1': shift_down(IDLE_S, 3),
    'roll_2': roll_ball(0), 'roll_3': roll_ball(90), 'roll_4': roll_ball(180), 'roll_5': roll_ball(270),
    'roll_6': shift_down(IDLE_S, 4), 'roll_7': shift_down(IDLE_S, 2),
    'hurt_s': IDLE_S, 'hurt_n': IDLE_N, 'hurt_e': IDLE_E,
    'jump_s': shift_up(IDLE_S, 2), 'jump_n': shift_up(IDLE_N, 2), 'jump_e': shift_up(IDLE_E, 2),
    'itemget': arms_up(SRC['idle_s']),
    'carry_s': arms_up(IDLE_S), 'carry_s1': arms_up(bob(IDLE_S, 0)), 'carry_s2': arms_up(bob(IDLE_S, 1)),
    'carry_n': arms_up(IDLE_N), 'carry_n1': arms_up(bob(IDLE_N, 0)), 'carry_n2': arms_up(bob(IDLE_N, 1)),
    'carry_e': arms_up(IDLE_E), 'carry_e1': arms_up(SRC['walk_s1']), 'carry_e2': arms_up(SRC['walk_s3']),
    'drown_1': shift_down(IDLE_S, 6), 'drown_2': shift_down(IDLE_S, 14), 'drown_3': shift_down(IDLE_S, 22),
    'fall_1': shift_down(IDLE_S, 6), 'fall_2': shift_down(IDLE_S, 14), 'fall_3': shift_down(IDLE_S, 22),
    'guard_n': IDLE_N, 'guard_e': IDLE_E, 'guard_s': IDLE_S,
    'big': SRC['idle_s'],
}
