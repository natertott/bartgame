"""Royal Valley Main, measured for a region-pool row.

Royal Valley is not one walkable space, which is the whole reason to
measure it before wiring it in. It is three, and how they join is what
makes the region a one-way valve:

  NORTH-EAST POCKET   where North Hyrule Field's WEST_NORTH border lands.
  SOUTH               the graveyard proper, and the border out to Trilby.
  TOP                 reached only by solving the Lost Woods maze.

The pocket drops into the south over a one-tile neck at tx 20, ty 41-42,
whose collision reads 0x29 rather than open floor - a ledge, passable
downhill only. That is the shape the user's survey describes from the
outside: E to S costs nothing, S to E is impossible. The way back up is
the maze (ROOM_ROYAL_VALLEY_FOREST_MAZE), whose success exit lands at
(120, 632) in the top part and whose failure exit drops the player back at
(120, 824) in the south.

Run from tools/quickstart. Prints the flood of each component, spawn spots
with full 3x3 clearance spread at least three tiles apart, and what
vanilla leaves standing.
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import (boot, warp, here, coll_at, room_dims, r16, ROOM_CONTROLS, PLAYER,
                 entities, KIND_OBJECT, KIND_NPC)

ROM = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tmc.gba'))
AREA, ROOM = 9, 0

# label, the pixel spot to flood from, and where that spot comes from
STARTS = [
    ('north-east pocket', (0x1d8, 0x260), "North Hyrule Field's WEST_NORTH border lands here"),
    ('south (graveyard)', (0x78, 0x3e0), "Trilby's NORTH_WEST border lands at y=1000"),
    ('top (past the maze)', (0x78, 0x278), "the maze's success exit, per roomInit.c's MAZE_CLEAR check"),
]


def grid_of(c):
    W, H = room_dims(c)
    tw, th = W // 16, H // 16
    return [[coll_at(c, tx, ty) for tx in range(tw)] for ty in range(th)], tw, th


def flood(grid, tw, th, seed):
    reach = {seed}
    q = collections.deque([seed])
    while q:
        t = q.popleft()
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (t[0] + d[0], t[1] + d[1])
            if n not in reach and 0 <= n[0] < tw and 0 <= n[1] < th and grid[n[1]][n[0]] == 0:
                reach.add(n)
                q.append(n)
    return reach


def spots(reach):
    full = sorted(t for t in reach
                  if all((t[0] + dx, t[1] + dy) in reach for dx in (-1, 0, 1) for dy in (-1, 0, 1)))
    picked = []
    for t in full:
        if all(abs(t[0] - p[0]) + abs(t[1] - p[1]) >= 3 for p in picked):
            picked.append(t)
    return full, picked


def main():
    comps = {}
    for label, start, why in STARTS:
        c = boot(ROM)
        c.memory.u8[ROOM_CONTROLS + 5] = 0xff
        warp(c, AREA, ROOM, start[0], start[1])
        if here(c) != (AREA, ROOM):
            print(f'{label}: did not land ({here(c)})')
            continue
        for _ in range(150):
            c.run_frame()
        grid, tw, th = grid_of(c)
        ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
        px, py = r16(c, PLAYER + 0x2e) - ox, r16(c, PLAYER + 0x32) - oy
        seed = (px // 16, py // 16)
        if grid[seed[1]][seed[0]] != 0:
            seed = min(((abs(x - seed[0]) + abs(y - seed[1]), x, y)
                        for y in range(th) for x in range(tw) if grid[y][x] == 0))[1:]
        reach = flood(grid, tw, th, seed)
        comps[label] = reach
        xs = [t[0] for t in reach]
        ys = [t[1] for t in reach]
        full, picked = spots(reach)
        print(f'\n== {label} ==   ({why})')
        print(f'  landed local ({px},{py}) = tile {seed} in a {tw}x{th}-tile room')
        print(f'  {len(reach)} tiles, tx {min(xs)}-{max(xs)}, ty {min(ys)}-{max(ys)}')
        print(f'  {len(full)} with full 3x3 clearance, {len(picked)} of those >=3 tiles apart')
        print(f'  roomSquares {len(reach)}, maxEnemies ~ {len(reach)//13}')
        if len(picked) >= 6:
            for i in range(0, len(picked), 6):
                print('    ' + ' '.join('{ %3d, %3d },' % (t[0]*16+8, t[1]*16+8) for t in picked[i:i+6]))
        if label.startswith('south'):
            objs = collections.Counter(e[2] for e in entities(c, KIND_OBJECT))
            npcs = collections.Counter(e[2] for e in entities(c, KIND_NPC))
            print(f'  vanilla objects {dict(objs)} (113 = PUSHABLE_GRAVE), NPCs {dict(npcs)}')
        del c
    ls = list(comps)
    for i in range(len(ls)):
        for j in range(i + 1, len(ls)):
            n = len(comps[ls[i]] & comps[ls[j]])
            print(f'\noverlap {ls[i]} / {ls[j]}: {n} tiles' + ('' if n else '  - separate components'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
