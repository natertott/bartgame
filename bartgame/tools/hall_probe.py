"""The Drain's hall, played in the ROM.

  WALK     from the spawn the hero walks, on his own feet, to the drain
           hole's mouth, to the Peddler's counter and to the Gatekeeper
  SHOP     facing the Peddler over his counter, A opens his wares
  FRONT    in front of the counter the hero is drawn over it (OAM
           priority 1); out on the floor, under the overlay (2)
  TALK     facing the Gatekeeper, A opens her words
  EXIT     up the drain hole: the wood
  RETURN   back down it: the hero stands in the hole's mouth, on floor
  SAFE     no ground the hero can reach lets him fall

    python3 tools/hall_probe.py
"""
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import probe as P  # noqa: E402
import critical_path as CP  # noqa: E402
import lift_probe as LP  # noqa: E402

S = os.environ.get('SNAPDIR', '/tmp')
res = []


def check(name, ok, detail=''):
    res.append(bool(ok))
    print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail))


def solid_grid(c):
    R = P.sym('gRoom')
    w, h = P.r8(c, R), P.r8(c, R + 1)
    base = R + 2 + 2048 + 2048
    return w, h, [[P.r8(c, base + y * 64 + x) for x in range(64)] for y in range(64)]


def free(sol, w, h, x, y):
    """the hero's feet box at (x, y) clear of solid ground (actor.c HB_HERO_FEET)"""
    x0, y0, x1, y1 = x - 6, y - 12, x + 5, y - 1
    if x0 < 0 or y0 < 0 or x1 >= w * 16 or y1 >= h * 16:
        return False
    return all(not sol[yy][xx] for yy in range(y0 >> 3, (y1 >> 3) + 1) for xx in range(x0 >> 3, (x1 >> 3) + 1))


def path(c, start, goal, step=2):
    """a walk from start to within a step of goal over free feet boxes"""
    w, h, sol = solid_grid(c)
    sx, sy = start
    gx, gy = goal
    q = deque([(sx, sy)])
    prev = {(sx, sy): None}
    while q:
        x, y = q.popleft()
        if abs(x - gx) <= step and abs(y - gy) <= step:
            out = [(x, y)]
            while prev[out[-1]] is not None:
                out.append(prev[out[-1]])
            return out[::-1]
        for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step)):
            n = (x + dx, y + dy)
            if n not in prev and free(sol, w, h, n[0], n[1]):
                prev[n] = (x, y)
                q.append(n)
    return None


def corners(pts):
    """the points where a walk turns"""
    out = [pts[0]]
    for a, b, cc in zip(pts, pts[1:], pts[2:]):
        if (b[0] - a[0], b[1] - a[1]) != (cc[0] - b[0], cc[1] - b[1]):
            out.append(b)
    out.append(pts[-1])
    return out


def walk(c, pts, frames=900):
    """steer the hero along a walk, one axis at a time, by the D-pad"""
    way = corners(pts)[1:]
    for (wx, wy) in way:
        for _ in range(frames):
            x, y = P.player_pos(c)
            if abs(x - wx) <= 1 and abs(y - wy) <= 1:
                break
            if abs(x - wx) > 1:
                P.hold(c, 'RIGHT' if wx > x else 'LEFT', 1)
            else:
                P.hold(c, 'DOWN' if wy > y else 'UP', 1)
        else:
            return False
    c.set_keys()
    P.run(c, 4)
    return True


def hero_prio(c):
    """the OAM priority of the hero's sprite (drawn first, slot 0)"""
    return (P.r16(c, 0x07000000 + 4) >> 10) & 3


def main():
    c = P.boot(seed=0xB4A7)
    P.run(c, 40)
    CP.dismiss(c)
    spawn = P.player_pos(c)
    ex, ey = P.hall_exit(c)
    mouth = (ex * 16 + 8, (ey + 1) * 16 + 12)
    peddler = (4 * 16 + 8, 7 * 16 + 6)
    gatekeeper = (21 * 16 + 8, 7 * 16 + 4)
    w, h, sol = solid_grid(c)
    for name, goal in (('the drain hole', mouth), ("the Peddler's counter", peddler), ('the Gatekeeper', gatekeeper)):
        CP.teleport(c, *spawn)
        p = path(c, spawn, goal)
        ok = p is not None and walk(c, p)
        check('WALK: from the spawn to %s' % name, ok, 'at %s, %d steps' % (P.player_pos(c), len(p) if p else -1))
        if name == "the Peddler's counter":
            P.hold(c, 'UP', 6)
            prio_front = hero_prio(c)
            P.press(c, 'A', 2, 30)
            count = P.r8(c, LP.ssym('sShopCount'))
            check('SHOP: the Peddler shows his wares over the counter', count > 0, 'wares %d' % count)
            P.snap(c, os.path.join(S, 'hall_shop.png'))
            for _ in range(3):
                P.press(c, 'B', 2, 20)
            CP.dismiss(c)
            P.run(c, 30)
            check('FRONT: in front of the counter, drawn over it', prio_front == 1, 'priority %d' % prio_front)
        if name == 'the Gatekeeper':
            before = P.r8(c, P.sym('gTbActive'))
            P.hold(c, 'UP', 6)
            P.press(c, 'A', 2, 30)
            tb = P.r8(c, P.sym('gTbActive')) and not before
            check('TALK: the Gatekeeper speaks', tb, 'box %d' % tb)
            P.snap(c, os.path.join(S, 'hall_gatekeeper.png'))
            CP.dismiss(c)
    CP.teleport(c, *spawn)
    P.run(c, 4)
    check('FRONT: out on the floor, under the overlay', hero_prio(c) == 2, 'priority %d' % hero_prio(c))
    # SAFE: every cell the hero can stand in is plain ground
    types = P.sym('metatile_type')
    R = P.sym('gRoom')
    hdr = open(os.path.join(P.ROOT, 'build', 'gen', 'assets.h')).read()
    tt = {n: int(hdr.split('#define TT_%s ' % n)[1].split()[0]) for n in ('PIT', 'WATER')}
    bad = []
    for cy in range(h):
        for cx in range(w):
            if free(sol, w, h, cx * 16 + 8, cy * 16 + 14):
                mt = P.r16(c, R + 2 + (cy * 32 + cx) * 2) & 0xFFFF
                if P.r8(c, types + mt) in tt.values():
                    bad.append((cx, cy))
    check('SAFE: nothing to fall into where the hero stands', not bad, 'cells %s' % bad[:6])
    # EXIT and RETURN
    CP.teleport(c, *mouth)
    P.hold(c, 'UP', 60)
    P.run(c, 40)
    check('EXIT: up the drain hole into the wood', CP.area(c) == 1, 'area %d' % CP.area(c))
    return_pos = (ex * 16 + 8, ey * 16 + 16 + 14)
    check('RETURN: the hole\'s mouth is floor to stand on', free(sol, w, h, *return_pos), 'at %s' % (return_pos,))
    print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
    return 0 if all(res) else 1


if __name__ == '__main__':
    sys.exit(main())
