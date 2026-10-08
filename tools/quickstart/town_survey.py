"""Hyrule Town's plaza, measured for the fifteenth region (Oct 2026, the
redesign's P2 section 5): the walkable floor from each of the four border
arrivals (vanilla's own landing coordinates for the North Field, South
Field, Lon Lon and Trilby borders), whether they are one component, the
house doors that open off it, and a farthest-point spread of enemy spots
over the land with 3x3 clearance (spawn_spread's rules).

    python3 tools/quickstart/town_survey.py [--rom tmc-d3.gba] [--emit]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenario as S
import parse_tables as P
from emu import warp, here, poison_here, coll_at, act_at, room_dims
import spawn_spread as SP
args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else 'tmc-d3.gba'
AT, RT = P.AREAS['AREA_HYRULE_TOWN'], P.ROOMS['ROOM_HYRULE_TOWN_MAIN']
# vanilla's landing coordinates for the four borders (src/data/transitions.c,
# the #else rows of the field exit lists)
ARRIVALS = {'from SHF (south)': (0x1f8, 0x3b8), 'from NHF (north)': (0x1f8, 0x18),
            'from LLR (east)': (0x3e8, 0xf0), 'from TRIL (west)': (0x8, 0xf0)}

def main():
    c = S.boot(ROM, 0, seed=5, frames=300)
    c.memory.u8[0x02002a40 + 0x3C] = 0x51
    poison_here(c); warp(c, AT, RT, 0x1f8, 0x3a0, frames=400)
    assert here(c) == (AT, RT), here(c)
    W, H = room_dims(c); tw, th = W // 16, H // 16
    g = [[coll_at(c, x, y) for x in range(tw)] for y in range(th)]
    acts = [[act_at(c, x, y) for x in range(tw)] for y in range(th)]
    print('room %dx%d px, %dx%d tiles' % (W, H, tw, th))
    comps = {}
    for name, (x, y) in ARRIVALS.items():
        sx, sy = min(max(x // 16, 0), tw - 1), min(max(y // 16, 0), th - 1)
        if g[sy][sx] == SP.SOLID:
            sx, sy = min((abs(a - sx) + abs(b - sy), a, b) for b in range(th) for a in range(tw) if g[b][a] != SP.SOLID)[1:]
        comp = SP.flood(g, (sx, sy), tw, th)
        comps[name] = comp
        land = sum(1 for t in comp if acts[t[1]][t[0]] not in SP.BAD_ACT)
        print('  %-18s lands tile %s: component %d tiles, %d land' % (name, (sx, sy), len(comp), land))
    first = list(comps.values())[0]
    same = all(c2 == first for c2 in comps.values())
    print('  all four arrivals in ONE component:', same)
    union = set().union(*comps.values())
    spots = SP.propose(g, union, tw, th, [], 34, acts)
    print('  proposed %d spots, %.0f%% of land covered' % (len(spots), SP.covered(union, spots, acts)))
    # the most open tile: the most clear tiles within 3 tiles, for the boss and the reward
    def openness(t):
        return sum(1 for dy in range(-3, 4) for dx in range(-3, 4)
                   if (t[0] + dx, t[1] + dy) in union and acts[t[1] + dy][t[0] + dx] not in SP.BAD_ACT)
    best = max(union, key=lambda t: (openness(t), -abs(t[0] - tw // 2) - abs(t[1] - th // 2)))
    print('  most open tile', best, 'px', (best[0] * 16 + 8, best[1] * 16 + 8), 'open', openness(best), 'of 49')
    if '--emit' in args:
        print('\nstatic const s16 sQuickStartHyruleTownEnemyOffsets[][2] = {')
        for i in range(0, len(spots), 6):
            print('    ' + ' '.join('{ %d, %d },' % p for p in spots[i:i + 6]))
        print('};')
        print('#define QUICKSTART_HYRULETOWN_ROOM_SQUARES %d' % (len(union) // 9))

if __name__ == '__main__':
    main()
