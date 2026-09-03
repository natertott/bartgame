"""Measure a candidate overworld region the way a pool row needs it.

Everything a region pool row carries is a measured quantity: where the player
lands, how much open floor there is, where a reward can sit so it is visible
on arrival without landing on the player, and a scatter of enemy offsets that
are all genuinely standable. This walks a room and reports all of it, so a new
region is a survey plus a table row rather than a guess plus a bug report.

    python3 tools/quickstart/region_survey.py AREA_X ROOM_Y [entranceX entranceY]
"""
import sys, os
sys.path.insert(0, os.path.abspath('tools/quickstart'))
from emu import boot, warp, here, coll_at, room_dims, PLAYER, r16
import parse_tables as P

RC = 0x03000bf0


def flood(c, start, tw, th):
    seen, stack = {start}, [start]
    while stack:
        q = stack.pop()
        for nb in ((q[0]+1, q[1]), (q[0]-1, q[1]), (q[0], q[1]+1), (q[0], q[1]-1)):
            if (nb not in seen and 0 <= nb[0] < tw and 0 <= nb[1] < th
                    and coll_at(c, nb[0], nb[1]) == 0):
                seen.add(nb); stack.append(nb)
    return seen


def clear3(c, t, tw, th):
    return all(0 <= t[0]+dx < tw and 0 <= t[1]+dy < th and coll_at(c, t[0]+dx, t[1]+dy) == 0
               for dx in (-1, 0, 1) for dy in (-1, 0, 1))


def survey(an, rn, ex, ey, spacing=4, want=24):
    a, r = P.AREAS[an], P.ROOMS[rn]
    c = boot('tmc.gba')
    warp(c, a, r, ex, ey)
    if here(c) != (a, r):
        print('%s/%s: did not land (got %s)' % (an, rn, here(c))); return
    w, h = room_dims(c)
    tw, th = w // 16, h // 16
    px = r16(c, PLAYER + 0x2e) - r16(c, RC + 6)
    py = r16(c, PLAYER + 0x32) - r16(c, RC + 8)
    start = (px // 16, py // 16)
    if coll_at(c, *start) != 0:
        cand = [(tx, ty) for ty in range(th) for tx in range(tw) if coll_at(c, tx, ty) == 0]
        start = min(cand, key=lambda t: abs(t[0]-start[0]) + abs(t[1]-start[1]))
    comp = flood(c, start, tw, th)

    total_open = sum(1 for ty in range(th) for tx in range(tw) if coll_at(c, tx, ty) == 0)
    clear = sorted(t for t in comp if clear3(c, t, tw, th))

    print('== %s / %s' % (an, rn))
    print('   room %dx%d px  (%dx%d tiles)   open %d   arrival component %d   3x3-clear %d'
          % (w, h, tw, th, total_open, len(comp), len(clear)))
    print('   landed at px (%d,%d) = tile %s' % (px, py, start))
    if not clear:
        print('   NO clear tiles - unusable as a pool region'); del c; return

    # Reward spot: far from the arrival but inside the same component.
    reward = max(clear, key=lambda t: abs(t[0]-start[0]) + abs(t[1]-start[1]))
    print('   reward candidate  tile %s = px (%d,%d), %d tiles from arrival'
          % (reward, reward[0]*16+8, reward[1]*16+8,
             abs(reward[0]-start[0]) + abs(reward[1]-start[1])))

    # Enemy offsets: farthest-point sample of the clear set, min 4 tiles apart,
    # seeded from the arrival and the reward so nothing lands on either.
    picks, taken = [], [start, reward]
    for _ in range(want):
        best, bestd = None, -1
        for t in clear:
            d = min(abs(t[0]-u[0]) + abs(t[1]-u[1]) for u in taken)
            if d > bestd:
                best, bestd = t, d
        if best is None or bestd < spacing:
            break
        picks.append(best); taken.append(best)
    print('   %d enemy offsets, min spacing %d tiles:' % (len(picks), spacing))
    print('      ' + ', '.join('{ %d, %d }' % (t[0]*16+8, t[1]*16+8) for t in picks))
    print('   room squares (32x32 units): %d' % (len(comp) // 4))
    del c


if __name__ == '__main__':
    an, rn = sys.argv[1], sys.argv[2]
    ex = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    ey = int(sys.argv[4]) if len(sys.argv) > 4 else 120
    sp = int(sys.argv[5]) if len(sys.argv) > 5 else 4
    want = int(sys.argv[6]) if len(sys.argv) > 6 else 24
    survey(an, rn, ex, ey, sp, want)
