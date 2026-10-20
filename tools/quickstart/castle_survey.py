"""Hyrule Castle, measured for its region (Oct 2026): per castle room, the
walkable floor from each arrival the room has (vanilla's own landing
coordinates, src/data/transitions.c, and the seams measured by walking),
whether the arrivals share a component, a farthest-point spread of enemy
spots over it with 3x3 clearance (spawn_spread's rules), and the most open
tile, for the boss spot and the reward spot.

The castle's flag doors (LOCKED_DOOR type 0, waiting on flag 0, which
nothing sets) are opened by the region's quirk hook in the game; here the
probe bypass leaves them shut, so a door tile reads solid and never joins
two components on its own.

    python3 tools/quickstart/castle_survey.py [--rom tmc-d3.gba] [--emit]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenario as S
import parse_tables as P
from emu import warp, here, poison_here, coll_at, act_at, room_dims
import spawn_spread as SP

args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else os.path.join(P.ROOT, 'tmc-d3.gba')
HC = P.AREAS['AREA_HYRULE_CASTLE']
# room -> (C table name, how many spots, {arrival name: (x, y)})
ROOMS = {
    0: ('sQuickStartCastleHallEnemyOffsets', 20, {
        'from the garden gate': (0xd8, 0x208),
        'from the ring hall (seam)': (216, 43),
        'from the lower hall door': (0x48, 0xe8),
    }),
    1: ('sQuickStartCastleRingEnemyOffsets', 22, {
        'from the entrance hall (seam)': (248, 487),
        'from the throne room (seam)': (248, 43),
        'from the lower hall, west door': (0x58, 0x38),
        'from the lower hall, east door': (0x198, 0x38),
    }),
    3: ('sQuickStartCastleLowerEnemyOffsets', 24, {
        'from the cellar (west border)': (0x52, 0x29c),
        'from the entrance hall door': (0x88, 0x288),
        'from the ring hall, west door': (0x68, 0x28),
        'from the ring hall, east door': (0x1c8, 0x28),
    }),
}


def survey(c, room, name, want, arrivals):
    poison_here(c)
    x0, y0 = list(arrivals.values())[0]
    warp(c, HC, room, x0, y0, frames=400)
    assert here(c) == (HC, room), here(c)
    W, H = room_dims(c)
    tw, th = W // 16, H // 16
    g = [[coll_at(c, x, y) for x in range(tw)] for y in range(th)]
    acts = [[act_at(c, x, y) for x in range(tw)] for y in range(th)]
    print('room %d: %dx%d px, %dx%d tiles' % (room, W, H, tw, th))
    comps = {}
    for an, (x, y) in arrivals.items():
        sx, sy = min(max(x // 16, 0), tw - 1), min(max(y // 16, 0), th - 1)
        if g[sy][sx] == SP.SOLID:
            sx, sy = min((abs(a - sx) + abs(b - sy), a, b) for b in range(th) for a in range(tw)
                         if g[b][a] != SP.SOLID)[1:]
        comp = SP.flood(g, (sx, sy), tw, th)
        comps[an] = frozenset(comp)
        land = sum(1 for t in comp if acts[t[1]][t[0]] not in SP.BAD_ACT)
        print('  %-32s tile %s: component %d tiles, %d land' % (an, (sx, sy), len(comp), land))
    groups = {}
    for an, comp in comps.items():
        groups.setdefault(comp, []).append(an)
    print('  %d component(s) among the arrivals' % len(groups))
    union = set().union(*comps.values())
    spots = SP.propose(g, union, tw, th, [], want, acts)
    print('  proposed %d spots, %.0f%% of land covered' % (len(spots), SP.covered(union, spots, acts)))

    def openness(t):
        return sum(1 for dy in range(-3, 4) for dx in range(-3, 4)
                   if (t[0] + dx, t[1] + dy) in union and acts[t[1] + dy][t[0] + dx] not in SP.BAD_ACT)
    best = max(union, key=lambda t: (openness(t), -abs(t[0] - tw // 2) - abs(t[1] - th // 2)))
    print('  most open tile', best, 'px', (best[0] * 16 + 8, best[1] * 16 + 8), 'open', openness(best), 'of 49')
    if '--emit' in args:
        print('static const s16 %s[][2] = {' % name)
        for i in range(0, len(spots), 6):
            print('    ' + ' '.join('{ %d, %d },' % p for p in spots[i:i + 6]))
        print('};')
        print('// %d tiles, %d 32x32 squares' % (len(union), len(union) // 4))
    return union


def main():
    c = S.boot(ROM, 0, seed=5, frames=300)
    c.memory.u8[0x02002a40 + 0x3C] = 0x51   # the probe bypass: containment lets the warps through
    for room, (name, want, arrivals) in ROOMS.items():
        survey(c, room, name, want, arrivals)


if __name__ == '__main__':
    main()
