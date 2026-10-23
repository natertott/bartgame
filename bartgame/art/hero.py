"""The Bloom: the hero, after the concept boards. A chibi flower-child:
a ring of orange-red petals around a round cream face with big dark
eyes and a small smile, a green hood collar over a green tunic, leaf
sleeves, a belt with a gold buckle, brown boots. 16x32, feet on the
bottom row; the head is more than half the figure.

Palette 'hero': 1 outline, 2 petal deep, 3 petal red, 4 petal orange,
5 petal light, 6 face cream, 7 face shadow, 8 tunic deep, 9 tunic green,
A tunic light, B leather dark, C leather light, D steel, E steel gleam,
F gold.
"""
import math

from px import L, Canvas, ball, compose, hflip, blank, outline, shift  # noqa: F401


# ---------------------------------------------------------- the bloom --
def bloom(face='s'):
    """The head, 16x16: eight petals around a face. face: 's' front,
    'n' the back of the bloom, 'e' a three-quarter profile."""
    c = Canvas(16, 16)
    cx, cy = 8.0, 7.5
    for k in range(8):
        ang = k * math.pi / 4 + math.pi / 8
        px, py = cx + math.cos(ang) * 4.6, cy + math.sin(ang) * 4.3
        for y in range(16):
            for x in range(16):
                dx, dy = x + 0.5 - px, y + 0.5 - py
                if dx * dx + dy * dy <= 2.7 * 2.7:
                    ddx, ddy = x + 0.5 - cx, y + 0.5 - cy
                    d = (ddx * ddx + ddy * ddy) ** 0.5
                    c.set(x, y, 5 if d > 6.3 and y < cy else 4 if d > 4.6 else 3)
    if face == 'n':
        for y in range(16):
            for x in range(16):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                if dx * dx + dy * dy <= 4.4 * 4.4:
                    c.set(x, y, 3)
        for (x, y) in ((7, 7), (8, 7), (7, 8), (8, 8)):
            c.set(x, y, 2)
    else:
        fx = cx + (2.0 if face == 'e' else 0)
        rx = 3.6 if face == 'e' else 4.4
        for y in range(16):
            for x in range(16):
                dx, dy = (x + 0.5 - fx) / rx, (y + 0.5 - cy - 0.4) / 4.4
                e = dx * dx + dy * dy
                if e <= 1.0:
                    c.set(x, y, 7 if (e > 0.62 and dx + dy > 0.35) else 6)
        if face == 's':
            for (ex, ey) in ((5, 6), (9, 6)):
                for yy in range(3):
                    c.set(ex, ey + yy, 1); c.set(ex + 1, ey + yy, 1)
                c.set(ex, ey, 0xe)
            c.set(7, 10, 1); c.set(8, 10, 1)
            c.set(6, 9, 7); c.set(9, 9, 7)
        else:
            ex, ey = 10, 6
            for yy in range(3):
                c.set(ex, ey + yy, 1); c.set(ex + 1, ey + yy, 1)
            c.set(ex, ey, 0xe)
            c.set(12, 10, 1)
            c.set(12, 7, 7)
    c.outline(1)
    return c.rows()


HEAD_S = bloom('s')
HEAD_N = bloom('n')
HEAD_E = bloom('e')

# --------------------------------------------------------------- bodies --
# South, standing: 14 rows (18..31)
BODY_S = L({}, '''
    ....1a9999a1....
    ...1a999999a1...
    .1aa1a9999a1aa1.
    .1991a9999a1991.
    .19919999991991.
    .16619999991661.
    .1111bbfbbb1111.
    .....199991.....
    .....1899981....
    ....1881.1881...
    ....1cc1.1cc1...
    ....1bb1.1bb1...
    ...1bbb1.1bbb1..
    ...1111..1111...
''')
BODY_S_W1 = L({}, '''
    ....1a9999a1....
    ...1a999999a1...
    .1aa1a9999a1aa1.
    .1991a9999a1991.
    .19919999991991.
    .16619999991661.
    .1111bbfbbb1111.
    .....199991.....
    .....1899981....
    ....1881.1881...
    ....1cc1.1cc1...
    ....1bb1.1bb1...
    ...1bbb1.1111...
    ...1111.........
''')
BODY_S_W2 = L({}, '''
    ....1a9999a1....
    ...1a999999a1...
    .1aa1a9999a1aa1.
    .1991a9999a1991.
    .19919999991991.
    .16619999991661.
    .1111bbfbbb1111.
    .....199991.....
    .....1899981....
    ....1881.1881...
    ....1cc1.1cc1...
    ....1bb1.1bb1...
    ....1111.1bbb1..
    .........1111...
''')
# the swing: the sword hand drops forward and low
BODY_S_ATK = L({}, '''
    ....1a9999a1....
    ...1a999999a1...
    .1aa1a9999a1a1..
    .1991a9999a1aa1.
    .19919999991991.
    .16619999991991.
    .1111bbfbbb1661.
    .....199991111..
    .....1899981....
    ....1881.1881...
    ....1cc1.1cc1...
    ....1bb1.1bb1...
    ...1bbb1.1bbb1..
    ...1111..1111...
''')
# the wind-up: the sword hand raised high at the right; the follow-through:
# the arm swung across the body, low
BODY_S_ATK1 = L({}, '''
    ....1a9999a11661
    ...1a999999a1aa1
    .1aa1a9999a1aa1.
    .1991a9999a1991.
    .19919999991111.
    .16619999991....
    .1111bbfbbb1....
    .....199991.....
    .....1899981....
    ....1881.1881...
    ....1cc1.1cc1...
    ....1bb1.1bb1...
    ...1bbb1.1bbb1..
    ...1111..1111...
''')
BODY_S_ATK3 = L({}, '''
    ....1a9999a1....
    ...1a999999a1...
    .1aa1a9999a1aa1.
    .1991a9999a1991.
    .19919999991991.
    .16619aa9991991.
    .1111166bbb1111.
    .....199991.....
    .....1899981....
    ....1881.1881...
    ....1cc1.1cc1...
    ....1bb1.1bb1...
    ...1bbb1.1bbb1..
    ...1111..1111...
''')
# hurt: arms flung up
BODY_S_HURT = L({}, '''
    .11.1a9999a1.11.
    1661a999999a1661
    1991.a9999a.1991
    .11.19999991.11.
    ....19999991....
    ....19999991....
    ....1bbfbbb1....
    .....199991.....
    .....1899981....
    ....1881.1881...
    ....1cc1.1cc1...
    ....1bb1.1bb1...
    ...1bbb1.1bbb1..
    ...1111..1111...
''')
# the leap: arms out, boots tucked up
BODY_S_JUMP = L({}, '''
    .11.1a9999a1.11.
    1661a999999a1661
    1991.a9999a.1991
    .11.19999991.11.
    ....19999991....
    ....19999991....
    ....1bbfbbb1....
    .....199991.....
    .....1899981....
    ....1cc1.1cc1...
    ...1bbb1.1bbb1..
    ...1111..1111...
    ................
    ................
''')
BODY_N = [r.replace('f', 'b') for r in BODY_S]
BODY_N_W1 = [r.replace('f', 'b') for r in BODY_S_W1]
BODY_N_W2 = [r.replace('f', 'b') for r in BODY_S_W2]
BODY_N_ATK = [r.replace('f', 'b') for r in BODY_S_ATK]
BODY_N_ATK1 = [r.replace('f', 'b') for r in BODY_S_ATK1]
BODY_N_ATK3 = [r.replace('f', 'b') for r in BODY_S_ATK3]
BODY_N_HURT = [r.replace('f', 'b') for r in BODY_S_HURT]
BODY_N_JUMP = [r.replace('f', 'b') for r in BODY_S_JUMP]

# East: in profile, the near arm in front
BODY_E = L({}, '''
    .....1a999a1....
    ....1a99999a1...
    ....1999999a1...
    ....19999991aa1.
    ....19999991991.
    ....19999991661.
    ....1bbbfbb1111.
    .....199991.....
    .....1899981....
    .....1881881....
    .....1cc1cc1....
    .....1bb1bb1....
    ....1bbb1bbb1...
    ....1111.1111...
''')
BODY_E_W1 = L({}, '''
    .....1a999a1....
    ....1a99999a1...
    ....1999999a1...
    ....19999991aa1.
    ....19999991991.
    ....19999991661.
    ....1bbbfbb1111.
    .....199991.....
    .....1899981....
    .....1881.1881..
    .....1cc1.1cc1..
    .....1bb1.1bb1..
    ....1bbb1.1bbb1.
    ....1111..1111..
''')
BODY_E_W2 = L({}, '''
    .....1a999a1....
    ....1a99999a1...
    ....1999999a1...
    ....19999991aa1.
    ....19999991991.
    ....19999991661.
    ....1bbbfbb1111.
    .....199991.....
    .....1899981....
    .....188881.....
    .....1cccc1.....
    .....1bb1bb1....
    ....1bbb11bb1...
    ....1111.1111...
''')
BODY_E_ATK = L({}, '''
    .....1a999a1....
    ....1a99999a1...
    ....1999999a1...
    ....19999991aaa1
    ....199999919991
    ....199999916661
    ....1bbbfbb11111
    .....199991.....
    .....1899981....
    .....1881881....
    .....1cc1cc1....
    .....1bb1bb1....
    ....1bbb1bbb1...
    ....1111.1111...
''')
# facing east the blade comes down over the head: the hand starts high
BODY_E_ATK1 = L({}, '''
    .....1a999a1.11.
    ....1a99999a1661
    ....1999999a1aa1
    ....19999991aa1.
    ....19999991991.
    ....19999991111.
    ....1bbbfbb1....
    .....199991.....
    .....1899981....
    .....1881881....
    .....1cc1cc1....
    .....1bb1bb1....
    ....1bbb1bbb1...
    ....1111.1111...
''')
BODY_E_ATK3 = L({}, '''
    .....1a999a1....
    ....1a99999a1...
    ....1999999a1...
    ....19999991....
    ....19999991aa1.
    ....199999911aa1
    ....1bbbfbb11661
    .....199991.....
    .....1899981....
    .....1881881....
    .....1cc1cc1....
    .....1bb1bb1....
    ....1bbb1bbb1...
    ....1111.1111...
''')
BODY_E_HURT = L({}, '''
    .11..1a999a1....
    1661.1a9999a11..
    1991.1999999a1..
    .11.1999999 1aa1
    ....19999991991.
    ....19999991661.
    ....1bbbfbb1111.
    .....199991.....
    .....1899981....
    .....1881.1881..
    .....1cc1.1cc1..
    .....1bb1.1bb1..
    ....1bbb1.1bbb1.
    ....1111..1111..
''')
BODY_E_HURT = [r.replace(' ', '9') for r in BODY_E_HURT]
BODY_E_JUMP = L({}, '''
    .11..1a999a1....
    1661.1a9999a11..
    1991.1999999a1..
    .11.19999991aa1.
    ....19999991991.
    ....19999991661.
    ....1bbbfbb1111.
    .....199991.....
    .....1899981....
    .....1cc1cc1....
    ....1bbb1bbb1...
    ....1111.1111...
    ................
    ................
''')


def frame(head, body, head_dy=4):
    """the head over the body in a 32-row frame; the body's last row is
    the frame's last row, the head overlaps its first row"""
    out = blank(16, 32)
    out = compose(out, body, 0, 32 - len(body))
    out = compose(out, head, 0, head_dy)
    return out


# the item held up: arms straight over the bloom
ITEMGET_ARMS = L({}, '''
    ...11......11...
    ..1661....1661..
    ..1aa1....1aa1..
    ..1991....1991..
    ..1991....1991..
    ..1991....1991..
    ..1991....1991..
    ...11......11...
''')


def itemget():
    out = frame(HEAD_S, BODY_S, 8)
    return compose(out, ITEMGET_ARMS, 0, 6)


# the roll: the bloom ducks, curls into a ball of leaf and petal that
# tumbles forward (the petal crown and the face turn round it, the boots
# tucked opposite), lands in a squash and comes up
def roll_ball(ang):
    """the curled bloom, the crown turned to ang degrees: 0 up, 90 to
    the right, so a run of 0, 90, 180, 270 rolls clockwise (east)"""
    c = Canvas(16, 16)
    ball(c, 8, 8.5, 7, 7, (8, 8, 9, 0xa, 0xa))
    a = math.radians(ang)
    fx, fy = 8 + math.sin(a) * 3.4, 8.5 - math.cos(a) * 3.4
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5 - 8, y + 0.5 - 8.5
            d = (dx * dx + dy * dy) ** 0.5
            if d > 7.3:
                continue
            pa = math.atan2(dx, -dy)
            diff = (pa - a + math.pi) % (2 * math.pi) - math.pi
            if abs(diff) < 1.0 and d > 2.2:
                c.set(x, y, 5 if d > 6.1 else 4 if d > 4.7 else 3)
            back = (pa - a) % (2 * math.pi) - math.pi
            if abs(back) < 0.45 and 4.4 < d < 6.6:
                c.set(x, y, 0xb)
            if (x + 0.5 - fx) ** 2 + (y + 0.5 - fy) ** 2 <= 1.9 * 1.9:
                c.set(x, y, 6)
    c.outline(1)
    return c.rows()


ROLL_1 = compose(compose(blank(16, 32), BODY_S_JUMP, 0, 18), HEAD_S, 0, 10)
ROLL_BALLS = [compose(blank(16, 32), roll_ball(ang), 0, 16) for ang in (0, 90, 180, 270)]
ROLL_6 = compose(compose(blank(16, 32), BODY_S_JUMP, 0, 18), HEAD_S, 0, 11)
ROLL_7 = compose(compose(blank(16, 32), BODY_S, 0, 18), HEAD_S, 0, 8)

FRAMES = {
    'idle_s': frame(HEAD_S, BODY_S),
    'walk_s1': frame(HEAD_S, BODY_S_W1),
    'walk_s2': frame(HEAD_S, BODY_S_W2),
    'idle_n': frame(HEAD_N, BODY_N),
    'walk_n1': frame(HEAD_N, BODY_N_W1),
    'walk_n2': frame(HEAD_N, BODY_N_W2),
    'idle_e': frame(HEAD_E, BODY_E),
    'walk_e1': frame(HEAD_E, BODY_E_W1),
    'walk_e2': frame(HEAD_E, BODY_E_W2),
    'atk_s': frame(HEAD_S, BODY_S_ATK),
    'atk_n': frame(HEAD_N, BODY_N_ATK),
    'atk_e': frame(HEAD_E, BODY_E_ATK),
    # the blade swings from the hero's left to his right facing south (the
    # back view the other way), so the south poses are mirrored
    'atk_s1': frame(HEAD_S, hflip(BODY_S_ATK1), 3),
    'atk_n1': frame(HEAD_N, BODY_N_ATK1, 3),
    'atk_e1': frame(HEAD_E, BODY_E_ATK1, 3),
    'atk_s3': frame(HEAD_S, hflip(BODY_S_ATK3), 5),
    'atk_n3': frame(HEAD_N, BODY_N_ATK3, 5),
    'atk_e3': frame(HEAD_E, BODY_E_ATK3, 5),
    'roll_1': ROLL_1,
    'roll_2': ROLL_BALLS[0],
    'roll_3': ROLL_BALLS[1],
    'roll_4': ROLL_BALLS[2],
    'roll_5': ROLL_BALLS[3],
    'roll_6': ROLL_6,
    'roll_7': ROLL_7,
    'hurt_s': frame(HEAD_S, BODY_S_HURT),
    'hurt_n': frame(HEAD_N, BODY_N_HURT),
    'hurt_e': frame(HEAD_E, BODY_E_HURT),
    'jump_s': frame(HEAD_S, BODY_S_JUMP, 2),
    'jump_n': frame(HEAD_N, BODY_N_JUMP, 2),
    'jump_e': frame(HEAD_E, BODY_E_JUMP, 2),
    'itemget': itemget(),
}

# Going under. Into water: the bloom flails, the petals go under, rings
# spread. Into a hole: the bloom shrinks away into the dark.
def ring(w, y, h=3):
    c = Canvas(16, 32)
    for yy in range(32):
        for xx in range(16):
            dx, dy = (xx + 0.5 - 8) / (w / 2.0), (yy + 0.5 - y) / (h / 2.0)
            e = dx * dx + dy * dy
            if 0.55 <= e <= 1.0:
                c.set(xx, yy, 0xe)
    return c.rows()


DROWN_1 = compose(compose(compose(blank(16, 32), ring(14, 27, 5)), HEAD_S, 0, 12), ITEMGET_ARMS, 0, 14)
DROWN_2 = compose(compose(blank(16, 32), ring(12, 28, 4)), [r if i < 7 else '.' * 16 for i, r in enumerate(HEAD_S)], 0, 21)
DROWN_3 = compose(ring(14, 28, 5), ring(6, 28, 2))


def shrink(rows, k):
    """every k-th pixel of a frame, the first opaque of each block"""
    h, w = len(rows), len(rows[0])
    out = []
    for y in range(0, h, k):
        line = ''
        for x in range(0, w, k):
            ch = '.'
            for dy in range(k):
                for dx in range(k):
                    if y + dy < h and x + dx < w and rows[y + dy][x + dx] != '.':
                        ch = rows[y + dy][x + dx]
                        break
                if ch != '.':
                    break
            line += ch
        out.append(line)
    return out


_whole = frame(HEAD_S, BODY_S_HURT)
FALL_1 = compose(blank(16, 32), [r for r in frame(HEAD_S, BODY_S_HURT)], 0, 4)
FALL_2 = compose(blank(16, 32), shrink(_whole, 2), 4, 16)
FALL_3 = compose(blank(16, 32), shrink(_whole, 4), 6, 24)

FRAMES.update({
    'drown_1': DROWN_1, 'drown_2': DROWN_2, 'drown_3': DROWN_3,
    'fall_1': FALL_1, 'fall_2': FALL_2, 'fall_3': FALL_3,
    # the guard: hunched a little behind the shield
    'guard_s': frame(HEAD_S, BODY_S, 5),
    'guard_n': frame(HEAD_N, BODY_N, 5),
    'guard_e': frame(HEAD_E, BODY_E, 5),
})


# The Bark Shield: wooden planks bound in brass, a steel boss. Seen from
# the front, the side, and behind (its back, when the bloom faces away).
def shield_front():
    c = Canvas(16, 16)
    c.ellipse(7.5, 8, 6.5, 7, 0xf)
    c.ellipse(7.5, 8, 5.2, 5.7, 0xc)
    for x in (4, 8, 12):
        c.vline(x, 3, 13, 0xb)
    c.ellipse(7.5, 8, 2.0, 2.0, 0xd)
    c.set(7, 7, 0xe)
    for y in range(16):
        for x in range(16):
            if c.get(x, y) == 0xc and (x + 0.5 - 7.5) + (y + 0.5 - 8) > 6:
                c.set(x, y, 0xb)
    c.outline(1)
    return c.rows()


def shield_side():
    c = Canvas(16, 16)
    c.ellipse(8, 8, 2.8, 7, 0xf)
    c.ellipse(8, 8, 1.6, 5.6, 0xc)
    c.vline(8, 4, 12, 0xb)
    c.set(8, 8, 0xd)
    c.outline(1)
    return c.rows()


def shield_back():
    c = Canvas(16, 16)
    c.ellipse(7.5, 9, 6.5, 2.4, 0xf)
    c.ellipse(7.5, 9, 5.2, 1.4, 0xb)
    c.outline(1)
    return c.rows()


SHIELD = {'front': shield_front(), 'side': shield_side(), 'back': shield_back()}

# The sword: a bright blade, a gold cross guard. Pointing S, E and SE.
SWORD = {
    'blade_s': L({}, '''
        ......1f1.......
        .....1fff1......
        ......1f1.......
        .....1ede1......
        .....1ede1......
        .....1ede1......
        .....1ede1......
        .....1ede1......
        .....1ede1......
        .....1ede1......
        .....1ede1......
        .....1ede1......
        ......1e1.......
        ......1e1.......
        .......1........
        ................
    '''),
    'blade_e': L({' ': 1}, '''
        ................
        ................
        ................
        ................
        ................
        ..1.............
        .1f11111111111..
        1fffeeeeeeeeee1.
        .1f1ddddddddde1.
        ..1.111111111 1.
        ................
        ................
        ................
        ................
        ................
        ................
    '''),
    'blade_se': L({}, '''
        ................
        ................
        ..1.............
        .1f1............
        ..1f11..........
        ...1ed1.........
        ....1ed1........
        .....1ed1.......
        ......1ed1......
        .......1ed1.....
        ........1ed1....
        .........1ed1...
        ..........1e1...
        ...........11...
        ................
        ................
    '''),
}
