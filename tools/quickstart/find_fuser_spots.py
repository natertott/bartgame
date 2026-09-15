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
from emu import boot, warp, here, room_dims, coll_at, poison_here

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
    # The overworld expansion. Kinstones 0x2E (EH Center) and 0x24 (WW South)
    # are real world events here too but are BEANSTALKS, deliberately not
    # fused in this mode (the climb leaves the ring and containment cancels
    # it), so neither room hosts a fuser at all.
    ('ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH', [0x16, 0x55]),
    ('ROOM_HYRULE_FIELD_WESTERN_WOODS_CENTER', [0x3D]),
    ('ROOM_HYRULE_FIELD_WESTERN_WOODS_NORTH', [0x11, 0x21, 0x3A, 0x48, 0x4C]),
]

# How many scatter spots to propose per region. Has to be at least as many as
# the region has fusers (North Hyrule Field has six), with enough spare that
# the per-run rotation actually moves them somewhere different.
SPOTS_PER_REGION = 10
# Minimum separation, in tiles, between any two spots and between a spot and
# anything already placed. Big enough that two fusers never read as a pair.
MIN_SPACING = 6


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
    """Propose a well-spread set of fuser spots per region.

    The fusers used to stand next to the gate they open, which made them easy
    to read but put every one of them in the same corner of the map as its
    door. These are scattered instead: farthest-point sampling over the
    reachable open tiles, so the set covers the whole walkable map rather than
    clustering, with the region entrance and reward spot seeded as already-
    taken so nothing lands on top of them.
    """
    gates = gate_positions()
    regions = {r['roomName']: r for r in P.region_pool()}
    print('static const QuickStartFuserSpots sQuickStartFuserSpots[] = {')
    problems = []
    for room_name, kids in GATES:
        r = regions[room_name]
        c = boot(ROM)
        poison_here(c)
        warp(c, r['area'], r['room'], r['entrance'][0], r['entrance'][1])
        if here(c) != (r['area'], r['room']):
            problems.append('%s: did not land' % room_name)
            continue
        W, H = room_dims(c)
        tw, th = W // 16, H // 16
        grid = [[coll_at(c, tx, ty) for tx in range(tw)] for ty in range(th)]
        seed = (r['entrance'][0] // 16, r['entrance'][1] // 16)
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
        # A fuser needs open ground on every side so the player can walk up
        # and face it from any direction.
        cands = [t for t in sorted(reach)
                 if all(open_((t[0] + dx, t[1] + dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
        # Seeded as taken: the arrival point, the reward drop, and every gate
        # this region owns - a fuser standing on a staircase reads as a bug.
        taken = [(r['entrance'][0] // 16, r['entrance'][1] // 16),
                 (r['reward'][0] // 16, r['reward'][1] // 16)]
        taken += [(gates[k][0] // 16, gates[k][1] // 16) for k in kids]
        picked = []
        for _ in range(SPOTS_PER_REGION):
            best, bestd = None, -1
            for t in cands:
                if t in picked:
                    continue
                d = min(max(abs(t[0] - o[0]), abs(t[1] - o[1])) for o in taken + picked)
                if d > bestd:
                    best, bestd = t, d
            if best is None or bestd < MIN_SPACING:
                problems.append('%s: only %d spots at least %d tiles apart'
                                % (room_name, len(picked), MIN_SPACING))
                break
            picked.append(best)
        print('    // %s - room %dx%d, %d reachable tiles, %d candidate spots'
              % (room_name, W, H, len(reach), len(cands)))
        print('    { %s, %s,' % (r['areaName'], room_name))
        print('      { ' + ', '.join('{ %d, %d }' % (t[0] * 16 + 8, t[1] * 16 + 8) for t in picked) + ' } },')
    print('};')
    if problems:
        print('\nPROBLEMS:')
        for p in problems:
            print('  ' + p)


if __name__ == '__main__':
    main()
