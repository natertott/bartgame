"""Which of a room's own exit-list doors are reachable from the border arrival?

world_reach.py is a WALKED survey - the user walking the mapexplore build and
writing down what each place cost. Two regions (Minish Woods, Lake Hylia) were
brought in without one, so their rows are derived instead: this reads the
room's real exit list out of transitions.c, floods the live collision grid
from the tile the player actually arrives on, and reports for each door
whether it is in that component, how far it is, and what stands between.

That is strictly less than a walk - it sees geometry, not gates. A door the
flood cannot reach might be opened by a bomb, a fusion or a shrink; a door it
CAN reach is genuinely walkable with nothing at all, which is the half that
matters for not stranding a run.

    python3 tools/quickstart/door_reach.py AREA_MINISH_WOODS ROOM_MINISH_WOODS_MAIN 8 424
"""
import sys, os, re
sys.path.insert(0, os.path.abspath('tools/quickstart'))
from emu import boot, warp, here, coll_at, room_dims, PLAYER, r16
import parse_tables as P

RC = 0x03000bf0
TILETYPES = 0x02025eb0 + 0x5004
SRC = 'src/data/transitions.c'


def type_at(c, tx, ty, tw):
    return r16(c, TILETYPES + 2 * (ty * tw + tx))


def is_bush(c, tx, ty, tw):
    """The ROM's own QuickStartTileIsBush: tile types 427-431 are the
    cuttable-shrub class. A bush JOINS two components for a player with a
    sword - they cut through - but nothing may stand on one."""
    return 427 <= type_at(c, tx, ty, tw) <= 431


def exits_for(listname):
    """Every AREA-warp row of one exit list: (doorX, doorY, destArea, destRoom)."""
    txt = open(SRC).read()
    m = re.search(r'const Transition %s\[\] = \{(.*?)\n\};' % listname, txt, re.S)
    if not m:
        raise SystemExit('no exit list named %s' % listname)
    body = ' '.join(m.group(1).split())
    out = []
    for row in re.findall(r'\{(.*?)\}', body):
        f = [x.strip() for x in row.split(',')]
        if f[0] != 'WARP_TYPE_AREA':
            continue
        out.append((int(f[1], 0), int(f[2], 0), f[6], f[7]))
    return out


def flood(c, start, tw, th, bushes=False):
    seen, dist, stack = {start}, {start: 0}, [start]
    while stack:
        q = stack.pop()
        for nb in ((q[0]+1, q[1]), (q[0]-1, q[1]), (q[0], q[1]+1), (q[0], q[1]-1)):
            if nb in seen or not (0 <= nb[0] < tw and 0 <= nb[1] < th):
                continue
            if coll_at(c, nb[0], nb[1]) != 0 and not (bushes and is_bush(c, nb[0], nb[1], tw)):
                continue
            seen.add(nb); dist[nb] = dist[q] + 1; stack.append(nb)
    return seen, dist


def main(an, rn, ex, ey, listname):
    a, r = P.AREAS[an], P.ROOMS[rn]
    c = boot('tmc.gba')
    warp(c, a, r, ex, ey)
    if here(c) != (a, r):
        raise SystemExit('%s/%s: did not land (got %s)' % (an, rn, here(c)))
    w, h = room_dims(c)
    tw, th = w // 16, h // 16
    px = r16(c, PLAYER + 0x2e) - r16(c, RC + 6)
    py = r16(c, PLAYER + 0x32) - r16(c, RC + 8)
    start = (px // 16, py // 16)
    if coll_at(c, *start) != 0:
        cand = [(tx, ty) for ty in range(th) for tx in range(tw) if coll_at(c, tx, ty) == 0]
        start = min(cand, key=lambda t: abs(t[0]-start[0]) + abs(t[1]-start[1]))
    comp, dist = flood(c, start, tw, th)
    bcomp, bdist = flood(c, start, tw, th, bushes=True)
    total = sum(1 for ty in range(th) for tx in range(tw) if coll_at(c, tx, ty) == 0)
    print('== %s / %s  %dx%d px (%dx%d tiles)  arrival tile %s'
          % (an, rn, w, h, tw, th, start))
    print('   open %d   strict arrival component %d   bush-permeable %d'
          % (total, len(comp), len(bcomp)))
    for dx, dy, da, dr in exits_for(listname):
        t = (dx // 16, dy // 16)
        near = lambda dd: min([dd[(t[0] + ox, t[1] + oy)]
                               for ox in (-1, 0, 1) for oy in (-1, 0, 1)
                               if (t[0] + ox, t[1] + oy) in dd] or [None])
        strict, bushy = near(dist), near(bdist)
        if strict is not None:
            verdict = 'WALKABLE d=%d' % strict
        elif bushy is not None:
            verdict = 'through bushes d=%d (needs a sword)' % bushy
        else:
            verdict = 'not reachable on foot'
        print('   door px(%4d,%4d) tile%-9s -> %-28s %-38s %s'
              % (dx, dy, str(t), da, dr, verdict))
    del c


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5])
