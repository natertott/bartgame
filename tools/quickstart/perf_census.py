"""The performance census (Oct 2026, the redesign's P2 section 4): the
three rooms the user named as slow - the Boomerang cave, Trilby's
push-block cave and Lon Lon Ranch - measured with the real frame rate
(fps_probe's gMain.ticks method: the game loop ticks once per frame it
finishes, so 60 * ticks / frames is the true rate) and a census of what is
alive while it runs: entities by kind, the busiest ids, the GFX slots in
use, and the peak.

Each ? room site in those rooms is booted through the testbed with every
kind forced, at difficulty 3 and 5; Lon Lon is booted as its region row.
The player stands still at the landing (nothing is killed: the lag the
user saw is with the room full).

    python3 tools/quickstart/perf_census.py [--rom tmc-d3.gba] [--frames 600] [--quick]
"""
import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import here, GENT, STRIDE, MAX_ENT
import scenario as S
import parse_tables as P
args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else 'tmc-d3.gba'
FRAMES = int(args[args.index('--frames') + 1]) if '--frames' in args else 600
GMAIN_TICKS = 0x03001000 + 0x0C
GFXBASE, MAX_GFX = 0x02024490, 44
KIND = {1: 'PLAYER', 3: 'ENEMY', 4: 'PROJ', 6: 'OBJECT', 7: 'NPC', 8: 'INTERACT', 9: 'MANAGER'}
objs = {v: k for k, v in P._enum(open(os.path.join(P.ROOT, 'include/object.h')).read()).items()}
enems = {v: k for k, v in P._enum(open(os.path.join(P.ROOT, 'include/enemy.h')).read()).items()}

def ticks(c):
    return c.memory.u8[GMAIN_TICKS] | (c.memory.u8[GMAIN_TICKS + 1] << 8)

def gfx_used(c):
    return sum(1 for i in range(MAX_GFX) if (c.memory.u8[GFXBASE + 4 + i * 12] & 0x0F) not in (0, 1, 2))

def census(c):
    kinds = collections.Counter(); ids = collections.Counter()
    for i in range(MAX_ENT):
        b = GENT + i * STRIDE
        k = c.memory.u8[b + 8]
        if k == 0:
            continue
        kinds[KIND.get(k, str(k))] += 1
        ident = c.memory.u8[b + 9]
        name = (enems.get(ident, ident) if k == 3 else objs.get(ident, ident) if k == 6 else ident)
        ids['%s:%s' % (KIND.get(k, k), name)] += 1
    return kinds, ids

def measure(c, frames=FRAMES):
    t0 = ticks(c); hist = []; worst = 60.0
    peak = (0, None, None); gpeak = 0
    for f in range(frames):
        c.run_frame()
        hist.append(ticks(c))
        if len(hist) > 30:
            rate = 60.0 * ((hist[-1] - hist[-31]) & 0xffff) / 30
            worst = min(worst, rate)
        if f % 15 == 0:
            kinds, ids = census(c)
            n = sum(kinds.values())
            if n > peak[0]:
                peak = (n, kinds, ids)
            gpeak = max(gpeak, gfx_used(c))
    avg = 60.0 * ((ticks(c) - t0) & 0xffff) / frames
    return avg, worst, peak, gpeak

def row(label, diff, c):
    avg, worst, (n, kinds, ids), g = measure(c)
    top = ', '.join('%s %d' % (k, v) for k, v in ids.most_common(5)) if ids else ''
    ks = ' '.join('%s %d' % (k, v) for k, v in sorted(kinds.items())) if kinds else ''
    print('%-44s d%-2d fps %5.1f worst %5.1f  ents %3d gfx %2d | %s | %s' % (label, diff, avg, worst, n, g, ks, top), flush=True)
    return avg, worst, n

def sweep():
    """--all: every site (its own roll) and every region row, 300 frames
    each, at difficulty 5. The memory-pair cost lived in every ? room, not
    only the three the user named; this is the check that none is left."""
    out = []
    sites = P.content_sites()
    for i, s in enumerate(sites):
        c = S.boot(ROM, S.KINDS['SITE'], i, S.EVENTS.index('WAVES'), 0, kit=2, diff=5, frames=240)
        if here(c)[:2] != (s[2], s[3]):
            continue
        avg, worst, (n, k, ids), g = measure(c, 300)
        out.append(('site %d %s' % (i, s[1][5:]), avg, worst, n))
        print('%-50s fps %5.1f worst %5.1f ents %d' % out[-1], flush=True)
    for r, p in enumerate(P.region_pool()):
        c = S.boot(ROM, S.KINDS['REGION'], r, 0, kit=2, diff=5, frames=240)
        avg, worst, (n, k, ids), g = measure(c, 300)
        out.append(('row %d %s' % (r, p['roomName'][5:]), avg, worst, n))
        print('%-50s fps %5.1f worst %5.1f ents %d' % out[-1], flush=True)
    slow = [o for o in out if o[2] < 55]
    print('\nSLOW: %d of %d' % (len(slow), len(out)))
    for o in slow:
        print('  %-50s avg %.1f worst %.1f ents %d' % o)

def main():
    if '--all' in args:
        return sweep()
    out = []
    sites = P.content_sites()
    targets = [i for i, s in enumerate(sites) if s[1] in ('ROOM_CAVES_BOOMERANG', 'ROOM_CAVES_TRILBY_HIGHLANDS')]
    kinds = ['WAVES', 'MINIBOSS', 'NPC', 'ITEM_DROP', 'CHEST_LOTTERY', 'FAIRY']
    if '--quick' in args:
        kinds = ['WAVES', 'MINIBOSS']
    for diff in (3, 5):
        for i in targets:
            for k in kinds:
                c = S.boot(ROM, S.KINDS['SITE'], i, S.EVENTS.index(k), 0, kit=2, diff=diff, frames=240)
                if here(c)[:2] != (sites[i][2], sites[i][3]):
                    print('site %d %s did not land' % (i, k)); continue
                out.append(('site %d %s %s' % (i, sites[i][1][5:], k), diff) + row('site %d %s %s' % (i, sites[i][1][5:], k), diff, c))
        # the plain room, every site rolling its own kind from the seed
        for rn in ('ROOM_CAVES_BOOMERANG', 'ROOM_CAVES_TRILBY_HIGHLANDS'):
            i = [j for j in targets if sites[j][1] == rn][0]
            for sd in (1, 2, 3):
                c = S.boot(ROM, S.KINDS['SITE'], i, S.EVENTS.index('ITEM_DROP'), 0, kit=2, diff=diff, seed=sd, frames=240)
                out.append(('%s seed %d (own rolls)' % (rn[5:], sd), diff) + row('%s seed %d (own rolls)' % (rn[5:], sd), diff, c))
        pool = P.region_pool()
        for r, p in enumerate(pool):
            if p['roomName'] != 'ROOM_HYRULE_FIELD_LON_LON_RANCH':
                continue
            for sd in (1, 2, 3):
                c = S.boot(ROM, S.KINDS['REGION'], r, 0, kit=2, diff=diff, seed=sd, frames=240)
                out.append(('LON_LON_RANCH row %d seed %d' % (r, sd), diff) + row('LON_LON_RANCH row %d seed %d' % (r, sd), diff, c))
    slow = [o for o in out if o[3] < 55]
    print('\nSLOW (worst 30-frame window under 55 fps): %d of %d samples' % (len(slow), len(out)))
    for o in slow:
        print('  %-50s d%d avg %.1f worst %.1f ents %d' % o)

if __name__ == '__main__':
    main()
