"""Where a region's enemies CAN spawn, against where they DO.

The user, on three regions: Trilby has "a large swath of walkable land in
the southwest corner where no enemies spawn"; Lake Hylia and Mount Crenel
have "basically all enemies spawn near the room entrance/exit and nowhere
else. This makes the rooms very boring."

So this measures the room rather than guessing at it: flood the walkable
collision from the spot the player actually arrives at, report how much of
that component the CURRENT offset table covers, and propose a spread that
covers the rest. Farthest-point sampling, so the proposal fills the biggest
holes first and the early rows stay useful if the table is later trimmed.

A spot is only offered if it has 3x3 clearance and sits at least MIN_APART
pixels from every spot already chosen - a spawn box overlapping a wall drops
its enemy into geometry, and two spawns on top of each other waste a slot
the GFX table is now charging for (QuickStartRoomEnemyCeiling).

ONLY THE ARRIVAL COMPONENT IS PROPOSED. Other components are reported but
never filled: a region's wave-clear counts every enemy in the room, so one
enemy stranded across water or up a climb wall is a region that can never be
cleared. Islands need their reachability established first (component_map.py
walks ledges) and then a deliberate decision.

    python3 tools/quickstart/spawn_spread.py                 # the three
    python3 tools/quickstart/spawn_spread.py TRILBY --emit   # C rows
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, here, poison_here, coll_at, room_dims, act_at
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
SOLID = 0x0f
MIN_APART = 56          # pixels between proposed spots
COVER_R = 96            # a tile counts as covered if a spot is within this
CLEAR = 1               # tiles of clearance required around a spot

# Act tiles a land enemy must not be dealt onto (src/data/mapActTileToSurfaceType.c):
# 0x0d PIT, 0x0e ground->water slope, 0x0f SHALLOW_WATER, 0x10 WATER,
# 0x12 ICE, 0x13 SWAMP. Collision alone does not catch these - Lake Hylia's
# water is walkable collision, so a flood happily proposes the middle of the
# lake, and Castor Wilds' swamp is the same trap in the other direction.
BAD_ACT = {0x0d, 0x0e, 0x0f, 0x10, 0x12, 0x13}
TARGET_SPOTS = 34       # what a well-served region looks like (Eastern Hills North)

TARGETS = {
    'TRILBY': ('ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS', 'sQuickStartTrilbyEnemyOffsets'),
    'LAKEHYLIA': ('ROOM_LAKE_HYLIA_MAIN', 'sQuickStartLakeHyliaEnemyOffsets'),
    'CRENEL': ('ROOM_MT_CRENEL_ENTRANCE', 'sQuickStartMtCrenelEnemyOffsets'),
    'EHN': ('ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH', 'sQuickStartEasternHillsNorthEnemyOffsets'),
}


def current_offsets(table):
    src = open(os.path.join(P.ROOT, 'src/game.c')).read()
    i = src.index('%s[][2] = {' % table)
    body = src[i:src.index('\n};', i)]
    return [(int(a), int(b)) for a, b in
            re.findall(r'\{\s*(\d+)\s*,\s*(\d+)\s*\}', body)]


def flood(g, start, tw, th, seen=None):
    comp = {start}
    q = collections.deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if (n not in comp and 0 <= n[0] < tw and 0 <= n[1] < th
                    and g[n[1]][n[0]] != SOLID):
                comp.add(n)
                q.append(n)
    return comp


def grid_and_components(c, entrance):
    W, H = room_dims(c)
    tw, th = W // 16, H // 16
    g = [[coll_at(c, x, y) for x in range(tw)] for y in range(th)]
    seed = (entrance[0] // 16, entrance[1] // 16)
    if not (0 <= seed[0] < tw and 0 <= seed[1] < th) or g[seed[1]][seed[0]] == SOLID:
        seed = min((abs(x - seed[0]) + abs(y - seed[1]), x, y)
                   for y in range(th) for x in range(tw) if g[y][x] != SOLID)[1:]
    comp = flood(g, seed, tw, th)
    others, seen = [], set(comp)
    for y in range(th):
        for x in range(tw):
            if g[y][x] == SOLID or (x, y) in seen:
                continue
            blob = flood(g, (x, y), tw, th)
            seen |= blob
            others.append(blob)
    return g, comp, sorted(others, key=len, reverse=True), tw, th


def clear_at(g, x, y, tw, th, acts=None):
    for dy in range(-CLEAR, CLEAR + 1):
        for dx in range(-CLEAR, CLEAR + 1):
            a, b = x + dx, y + dy
            if not (0 <= a < tw and 0 <= b < th) or g[b][a] == SOLID:
                return False
            if acts is not None and acts[b][a] in BAD_ACT:
                return False
    return True


def covered(comp, spots, acts=None):
    """Coverage of the LAND in a component. Counting water in the
    denominator makes Lake Hylia look worse than it is and makes any fix
    look impossible: two thirds of its arrival component is lake, which no
    land enemy may stand on."""
    land = [t for t in comp if acts is None or acts[t[1]][t[0]] not in BAD_ACT]
    if not spots or not land:
        return 0.0
    n = 0
    for tx, ty in land:
        px, py = tx * 16 + 8, ty * 16 + 8
        if any((px - sx) ** 2 + (py - sy) ** 2 <= COVER_R ** 2 for sx, sy in spots):
            n += 1
    return n / len(land) * 100


def propose(g, comp, tw, th, keep, want, acts=None):
    """Farthest-point sampling over the component, seeded with `keep`."""
    cands = [(x * 16 + 8, y * 16 + 8) for (x, y) in sorted(comp)
             if clear_at(g, x, y, tw, th, acts)]
    chosen = list(keep)
    out = []
    while len(out) < want and cands:
        best, bestd = None, -1
        for p in cands:
            d = min(((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) for q in chosen) if chosen else 1 << 30
            if d > bestd:
                best, bestd = p, d
        if bestd < MIN_APART ** 2:
            break
        chosen.append(best)
        out.append(best)
        cands.remove(best)
    return out


def run(key, emit):
    room_name, table = TARGETS[key]
    row = next(r for r in P.region_pool() if r['roomName'] == room_name)
    cur = current_offsets(table)
    c = boot(ROM, seed=None)
    poison_here(c)
    warp(c, row['area'], row['room'], row['entrance'][0], row['entrance'][1])
    if here(c) != (row['area'], row['room']):
        print('%s: did not land' % key)
        return
    g, comp, others, tw, th = grid_and_components(c, row['entrance'])
    acts = [[act_at(c, x, y) for x in range(tw)] for y in range(th)]
    del c
    total = len(comp) + sum(len(o) for o in others)
    print('\n=== %s (%s), room %dx%d tiles ===' % (key, room_name[5:], tw, th))
    landn = sum(1 for t in comp if acts[t[1]][t[0]] not in BAD_ACT)
    print('  arrival component %d walkable tiles of %d, of which %d are LAND'
          % (len(comp), total, landn))
    big = [o for o in others if len(o) >= 20]
    if big:
        print('  other components >=20 tiles (NOT filled, reachability unproven): %s'
              % ', '.join(str(len(o)) for o in big[:6]))
    inside = [p for p in cur if (p[0] // 16, p[1] // 16) in comp]
    print('  current: %d spots, %d in the arrival component, %.0f%% of its land covered'
          % (len(cur), len(inside), covered(comp, inside, acts)))
    target = TARGET_SPOTS
    for a in sys.argv:
        if a.startswith('--target='):
            target = int(a.split('=')[1])
    add = propose(g, comp, tw, th, inside, max(0, target - len(inside)), acts)
    allspots = inside + add
    print('  proposed: +%d -> %d spots, %.0f%% of land covered'
          % (len(add), len(allspots), covered(comp, allspots, acts)))
    if emit:
        print('\nstatic const s16 %s[][2] = {' % table)
        for i in range(0, len(allspots), 4):
            print('    ' + ' '.join('{ %d, %d },' % p for p in allspots[i:i + 4]))
        print('};')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    for key in (args or ['TRILBY', 'LAKEHYLIA', 'CRENEL']):
        if '--map' in sys.argv:
            coverage_map(key.upper())
        else:
            run(key.upper(), '--emit' in sys.argv)
    return 0




def coverage_map(key):
    """ASCII map of the arrival component: '#' solid, '.' covered,
    'o' walkable but UNCOVERED, '*' a current spawn spot. Column/row
    labels are TILE indices, so a bare patch can be read straight off."""
    room_name, table = TARGETS[key]
    row = next(r for r in P.region_pool() if r['roomName'] == room_name)
    cur = current_offsets(table)
    c = boot(ROM, seed=None)
    poison_here(c)
    warp(c, row['area'], row['room'], row['entrance'][0], row['entrance'][1])
    g, comp, others, tw, th = grid_and_components(c, row['entrance'])
    del c
    spots = [p for p in cur if (p[0] // 16, p[1] // 16) in comp]
    spott = {(p[0] // 16, p[1] // 16) for p in spots}
    print('\n%s coverage map (%d spots, tile grid %dx%d)' % (key, len(spots), tw, th))
    print('     ' + ''.join(str(x // 10 % 10) for x in range(tw)))
    print('     ' + ''.join(str(x % 10) for x in range(tw)))
    for y in range(th):
        line = []
        for x in range(tw):
            if (x, y) in spott:
                line.append('*')
            elif (x, y) not in comp:
                line.append('#' if g[y][x] == SOLID else '~')
            else:
                px, py = x * 16 + 8, y * 16 + 8
                ok = any((px - sx) ** 2 + (py - sy) ** 2 <= COVER_R ** 2 for sx, sy in spots)
                line.append('.' if ok else 'o')
        print('%3d  %s' % (y, ''.join(line)))
    print('  # solid   ~ other component   . covered   o UNCOVERED   * spawn spot')


if __name__ == '__main__':
    sys.exit(main())
