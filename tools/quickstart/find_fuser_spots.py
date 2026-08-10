"""Propose a stand-in-front-of spot for every Kinstone fuser.

A fuser has to be reachable while its own gate is still SHUT, so this boots
the real ROM (which now un-fuses those gates per run), walks into each
region, floods the walkable graph from the region entrance, and then picks
the nearest reachable tile to the gate it opens.

Prints the rows to paste into sQuickStartFusers in src/game.c. The invariant
checker re-verifies whatever ends up there, so this is a proposal tool - the
constants in the source stay the source of truth.
"""
import collections
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_tables as P
from emu import boot, warp, here, room_dims, coll_at

ROOT = P.ROOT
ROM = os.path.join(ROOT, 'tmc.gba')
MAP = open(os.path.join(ROOT, 'build/USA/tmc.map')).read()
ROMB = open(ROM, 'rb').read()

# Kinstone -> region, in the order the fuser table should read.
GATES = [
    ('ROOM_CASTLE_GARDEN_MAIN', [0x18, 0x35]),
    ('ROOM_HYRULE_FIELD_LON_LON_RANCH', [0x1E, 0x29, 0x60]),
    ('ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD', [0x40, 0x4D, 0x59, 0x5A, 0x2D, 0x5F]),
    ('ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD', [0x32, 0x58, 0x53]),
    ('ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS', [0x3F, 0x22, 0x52, 0x5E]),
]

# How far from its own gate a fuser is allowed to end up. Close enough that
# the player reads the two as connected, far enough that the search has room
# to get around the obstacle the gate itself puts there.
MAX_TILES = 9
# Keep fusers off the tile the gate occupies and its immediate ring, so the
# sprite never overlaps the staircase/stump art the fusion draws.
MIN_TILES = 2


def sym(name):
    for line in MAP.split('\n'):
        parts = line.split()
        if len(parts) == 2 and parts[1] == name and parts[0].startswith('0x'):
            return int(parts[0], 16) - 0x08000000
    raise KeyError(name)


def gate_positions():
    kwe, we = sym('gKinstoneWorldEvents'), sym('gWorldEvents')
    out = {}
    for kid in range(1, 101):
        weid = ROMB[kwe + kid * 8 + 4]
        if ROMB[kwe + kid * 8 + 3] != 8 or weid == 0:
            continue
        off = we + weid * 20
        x, y = struct.unpack('<2H', ROMB[off + 8:off + 12])
        out[kid] = (x, y)
    return out


def main():
    gates = gate_positions()
    regions = {r['roomName']: r for r in P.region_pool()}
    print('static const QuickStartFuser sQuickStartFusers[] = {')
    problems = []
    for room_name, kids in GATES:
        r = regions[room_name]
        c = boot(ROM)
        c.memory.u8[0x03000bf0 + 4] = 0
        warp(c, r['area'], r['room'], r['entrance'][0], r['entrance'][1])
        if here(c) != (r['area'], r['room']):
            problems.append('%s: did not land' % room_name)
            continue
        W, H = room_dims(c)
        tw, th = W // 16, H // 16
        grid = [[coll_at(c, tx, ty) for tx in range(tw)] for ty in range(th)]
        seed = (r['entrance'][0] // 16, r['entrance'][1] // 16)
        # Walkable = fully open. Special tiles (stairs, garden paths) are
        # standable but a fuser on one reads as misplaced, so they are only
        # used to traverse, never to land on.
        walk = lambda t: 0 <= t[0] < tw and 0 <= t[1] < th and grid[t[1]][t[0]] != 0x0f
        open_ = lambda t: 0 <= t[0] < tw and 0 <= t[1] < th and grid[t[1]][t[0]] == 0
        if not walk(seed):
            best = min(((abs(x - seed[0]) + abs(y - seed[1]), x, y)
                        for y in range(th) for x in range(tw) if grid[y][x] == 0), default=None)
            seed = (best[1], best[2])
        reach = {seed}
        q = collections.deque([seed])
        while q:
            t = q.popleft()
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (t[0] + d[0], t[1] + d[1])
                if n not in reach and walk(n):
                    reach.add(n)
                    q.append(n)
        print('    // %s - room %dx%d, %d reachable tiles from the entrance'
              % (room_name, W, H, len(reach)))
        taken = []
        for kid in kids:
            gx, gy = gates[kid]
            gt = (gx // 16, gy // 16)
            cands = []
            for t in reach:
                if not open_(t):
                    continue
                d = max(abs(t[0] - gt[0]), abs(t[1] - gt[1]))
                if d < MIN_TILES or d > MAX_TILES:
                    continue
                # Spread fusers apart so two gates in one corner do not put
                # two sprites on the same tile.
                if any(max(abs(t[0] - o[0]), abs(t[1] - o[1])) < 3 for o in taken):
                    continue
                # Prefer a spot with open ground all around it: the player
                # has to be able to walk up and face it from any side.
                room = sum(1 for dx in (-1, 0, 1) for dy in (-1, 0, 1) if open_((t[0] + dx, t[1] + dy)))
                cands.append((-room, d, t))
            if not cands:
                problems.append('%s KINSTONE_%02X: no reachable spot within %d tiles of (%d,%d)'
                                % (room_name, kid, MAX_TILES, gx, gy))
                continue
            cands.sort()
            t = cands[0][2]
            taken.append(t)
            px, py = t[0] * 16 + 8, t[1] * 16 + 8
            print('    { %-28s %-38s KINSTONE_%02X, %4d, %4d },'
                  % (r['areaName'] + ',', room_name + ',', kid, px, py))
    print('};')
    if problems:
        print('\nPROBLEMS:')
        for p in problems:
            print('  ' + p)


if __name__ == '__main__':
    main()
