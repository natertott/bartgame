"""A room's walkable components, and the LEDGES that join them.

Written because a collision flood gets this wrong, and got it wrong twice
in one session. A flood follows fully-open tiles, so it finds a room's
components correctly; it cannot see a LEDGE, because the tile you hop from
reads as ordinary floor and the tiles you hop over read as solid wall.
Both times the flood reported a sealed pocket and both times the player
could simply walk off the edge:

  Royal Valley  a one-tile neck at tx 20 whose collision reads 0x29.
  Trilby        the pocket Royal Valley's border lands in, which drops
                into the region's 334-tile main body from tx 14-16.

So this floods AND THEN walks the player off every boundary tile of every
component, in the direction that leaves it, and reports where they
actually end up. A landing inside another component is a real link. Ledges
are one-way by nature, so the map it prints is DIRECTED - finding
[0] -> [1] says nothing about getting back.

Usage:  python3 tools/quickstart/component_map.py AREA ROOM [X Y]
        X,Y is a spot to warp to; some rooms need a specific one.
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, here, coll_at, room_dims, r16, ROOM_CONTROLS, PLAYER

ROM = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tmc.gba'))
DIRS = (('DOWN', 0, 1), ('UP', 0, -1), ('LEFT', -1, 0), ('RIGHT', 1, 0))


def components(grid, tw, th):
    seen = set()
    out = []
    for ty in range(th):
        for tx in range(tw):
            if grid[ty][tx] != 0 or (tx, ty) in seen:
                continue
            comp = {(tx, ty)}
            q = collections.deque([(tx, ty)])
            while q:
                t = q.popleft()
                for _, dx, dy in DIRS:
                    n = (t[0] + dx, t[1] + dy)
                    if n not in comp and 0 <= n[0] < tw and 0 <= n[1] < th and grid[n[1]][n[0]] == 0:
                        comp.add(n)
                        q.append(n)
            seen |= comp
            out.append(comp)
    out.sort(key=len, reverse=True)
    return out


def boundary(comp, direction):
    _, dx, dy = direction
    return sorted(t for t in comp if (t[0] + dx, t[1] + dy) not in comp)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    area, room = int(sys.argv[1]), int(sys.argv[2])
    spot = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (120, 120)
    minsize = 8

    c = boot(ROM)
    c.memory.u8[ROOM_CONTROLS + 5] = 0xff
    warp(c, area, room, spot[0], spot[1])
    if here(c) != (area, room):
        print(f'did not land ({here(c)})')
        return 1
    for _ in range(120):
        c.run_frame()
    W, H = room_dims(c)
    tw, th = W // 16, H // 16
    grid = [[coll_at(c, tx, ty) for tx in range(tw)] for ty in range(th)]
    comps = components(grid, tw, th)
    del c

    big = [cp for cp in comps if len(cp) >= minsize]
    print(f'area {area} room {room}: {tw}x{th} tiles, {len(comps)} components '
          f'({len(big)} of {minsize} tiles or more)')
    index = {}
    for i, cp in enumerate(big):
        xs = [t[0] for t in cp]
        ys = [t[1] for t in cp]
        print(f'  [{i}] {len(cp):>4} tiles  tx {min(xs)}-{max(xs)}  ty {min(ys)}-{max(ys)}')
        for t in cp:
            index[t] = i

    print('\nwalking each component off its own edges - a landing inside another '
          'component is a ledge:')
    found = collections.OrderedDict()
    for i, cp in enumerate(big):
        for d in DIRS:
            for t in boundary(cp, d):
                cc = boot(ROM)
                cc.memory.u8[ROOM_CONTROLS + 5] = 0xff
                warp(cc, area, room, t[0] * 16 + 8, t[1] * 16 + 8)
                if here(cc) != (area, room):
                    del cc
                    continue
                for _ in range(30):
                    cc.run_frame()
                k = getattr(cc, 'KEY_' + d[0])
                cc.set_keys(k)
                for _ in range(120):
                    cc.run_frame()
                    if here(cc) != (area, room):
                        break
                cc.clear_keys(k)
                for _ in range(45):
                    cc.run_frame()
                left = here(cc) != (area, room)
                ox, oy = r16(cc, ROOM_CONTROLS + 6), r16(cc, ROOM_CONTROLS + 8)
                end = ((r16(cc, PLAYER + 0x2e) - ox) // 16, (r16(cc, PLAYER + 0x32) - oy) // 16)
                del cc
                if left:
                    continue
                j = index.get(end)
                if j is not None and j != i:
                    found.setdefault((i, j, d[0]), []).append((t, end))
    if not found:
        print('  none - every component here really is sealed')
    for (i, j, d), pairs in found.items():
        tiles = ', '.join(str(p[0]) for p in pairs[:6])
        print(f'  [{i}] -> [{j}] walking {d} from {len(pairs)} tile(s): {tiles}'
              f'{" ..." if len(pairs) > 6 else ""}  landing near {pairs[0][1]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
