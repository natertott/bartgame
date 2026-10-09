"""Where the single-room carry quest can run: start (A) and end (B) pairs,
measured from each room's live collision (docs/QUICKSTART_CARRY_SINGLE_ROOM.md).

For each candidate room (the five the user named), in a running game:

  1. The CARRY GRID: tiles with collision 0 and no hazard act tile (pit
     0x0D, deep water 0x10/0x11, swamp 0x13 - the Castor Wilds murk - and
     lava 0x5A). Bushes are solid here, which is right: Link cannot swing a
     sword with a pot over his head. Ledges are walls (a carry path never
     needs a hop).
  2. The ARRIVAL PIECES: the 4-connected parts of that grid a player can
     arrive in - under or beside the pool row's entrance, a vanilla
     transition's landing, or a survey place (its exits are the border
     crossings). Wherever the player comes in, a pair in that piece is
     walkable to A and carryable to B without cutting anything.
  3. The survey's PLACES in the room (world_reach.py rows: exits, caves,
     pockets), as tiles.
  4. PAIRS, per piece (no end within three tiles of an NPC already in the
     room; the parcel's home H three tiles from A, outside the giver's talk
     box): A and B both "roomy" (their 3x3 block in the piece,
     so the giver, the pot and the receiver stand on open floor), at least
     60% of the piece's longest walk (and 24 tiles) apart by the shortest
     carry path, which passes within 6 tiles of at least two places. Up to
     four per piece, their A's spread apart. The game takes the first pair
     whose A and B lie in the piece the player is standing in.

The in-game landing check reads the same grid: each pair is emitted with
its piece as a bitmap, so the game's "is this landing good" is one bit,
not a flood (a full-room flood costs millions of instructions - frames of
stall on every landing).

Writes include/quickstart/carry_pairs.h.

    python3 tools/quickstart/carry_pairs.py [--rom tmc-d3.gba] [--check]
"""
import os, sys
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import warp, here, press, r16, room_dims, coll_at, act_at
import scenario as S
import parse_tables as P
import world_reach as W

args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else 'tmc-d3.gba'
OUT = os.path.join(P.ROOT, 'include/quickstart/carry_pairs.h')
SAVE = 0x02002a40
MSG = 0x02000050
HAZ = (0x0D, 0x10, 0x11, 0x13, 0x5A)
# (label, area, room, the pool row's entrance - sQuickStartRegionPool)
ROOMS = [
    ('NHF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 504, 456),
    ('MW', 'MINISH_WOODS', 'MAIN', 8, 424),
    ('VF', 'VEIL_FALLS', 'MAIN', 296, 500),
    ('CREN-BASE', 'MT_CRENEL', 'ENTRANCE', 1000, 424),
    ('CW', 'CASTOR_WILDS', 'MAIN', 968, 312),
]
MIN_FRACTION = 0.6
NODE_REACH = 6
MAX_PAIRS = 4
MIN_LENGTH = 24   # tiles of carry, whatever the piece's size
A_SPREAD = 8


def dismiss(c, limit=600):
    quiet = 0
    for _ in range(limit):
        if c.memory.u8[MSG] == 0:
            c.run_frame(); quiet += 1
            if quiet >= 30:
                return
            continue
        press(c, c.KEY_A, 3, 17); quiet = 0


def grid(c):
    w, h = room_dims(c)
    tw, th = min(w // 16, 64), min(h // 16, 64)
    g = [[coll_at(c, x, y) == 0 and act_at(c, x, y) not in HAZ for x in range(tw)] for y in range(th)]
    return tw, th, g


def components(tw, th, g):
    comp = [[-1] * tw for _ in range(th)]
    sizes = []
    for y in range(th):
        for x in range(tw):
            if g[y][x] and comp[y][x] < 0:
                n = len(sizes); comp[y][x] = n; q = deque([(x, y)]); k = 0
                while q:
                    a, b = q.popleft(); k += 1
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        u, v = a + dx, b + dy
                        if 0 <= u < tw and 0 <= v < th and g[v][u] and comp[v][u] < 0:
                            comp[v][u] = n; q.append((u, v))
                sizes.append(k)
    return comp, sizes


def bfs(tw, th, inside, src):
    dist = {src: 0}; par = {src: None}; q = deque([src])
    while q:
        a, b = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            t = (a + dx, b + dy)
            if t not in dist and inside(t):
                dist[t] = dist[(a, b)] + 1; par[t] = (a, b); q.append(t)
    return dist, par


def nearest(tw, th, inside, x, y):
    best = None
    for v in range(th):
        for u in range(tw):
            if inside((u, v)):
                d = abs(u * 16 + 8 - x) + abs(v * 16 + 8 - y)
                if best is None or d < best[0]:
                    best = (d, (u, v))
    return best[1] if best else None


def survey_places(area, room, tw, th):
    out = []
    for key, reg in W.SURVEY.items():
        for e in reg['dests']:
            if e['area'] == area and e['room'] == room and e['local'][0] is not None:
                x, y = e['local']
                if 0 <= x < tw * 16 + 16 and 0 <= y < th * 16 + 16:
                    t = (min(max(x // 16, 0), tw - 1), min(max(y // 16, 0), th - 1))
                    if t not in out:
                        out.append(t)
    return out


def arrivals(area, room, ex, ey, places):
    """Where a player can come into the room: the pool row's entrance, the
    vanilla transitions that land here, and the survey's places (its exits
    are the border crossings, which keep the coordinate they crossed at)."""
    import dungeon_reach as D
    lists, _ = D.parse_transitions()
    pts = [(ex, ey)]
    for rows in lists.values():
        for r in rows:
            if r['area'] == 'AREA_' + area and r['room'] == 'ROOM_%s_%s' % (area, room):
                pts.append((r['ex'], r['ey']))
    pts += [(p[0] * 16 + 8, p[1] * 16 + 8) for p in places]
    return pts


def npc_tiles(c):
    """The room's own NPCs. Not the mode's quest givers (all ZELDA-skinned):
    they move from run to run, and their regions are rolled apart from the
    carry quest's (QuickStartCarryRollOnce)."""
    import re
    from emu import entities, KIND_NPC, ROOM_CONTROLS
    zelda = {m.group(2): int(m.group(1), 16) for m in
             re.finditer(r'/\*0x([0-9a-f]+)\*/\s*(\w+),', open(os.path.join(P.ROOT, 'include/npc.h')).read())}['ZELDA']
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    return [((e[4] - ox) >> 4, (e[5] - oy) >> 4) for e in entities(c, KIND_NPC) if e[2] != zelda]


def home_for(a, roomy_set, du_b):
    """Where the parcel waits: a roomy tile three tiles from the giver in a
    line or one off it - outside the giver's oversized talk box (40x40), or R
    by the pot talks instead of lifting (measured) - the one nearest B."""
    best = None
    for dx, dy in ((3, 0), (-3, 0), (0, 3), (0, -3), (3, 1), (3, -1), (-3, 1), (-3, -1),
                   (1, 3), (-1, 3), (1, -3), (-1, -3)):
        h = (a[0] + dx, a[1] + dy)
        if h in roomy_set and h in du_b:
            if best is None or du_b[h] < du_b[best]:
                best = h
    return best


def room_pairs(c, label, area, room, ex, ey):
    tw, th, g = grid(c)
    npcs = npc_tiles(c)
    comp, sizes = components(tw, th, g)
    if not sizes:
        return tw, th, [], {}
    places = survey_places(area, room, tw, th)
    # the pieces a player can arrive in: the piece under (or beside, within
    # three tiles of) each arrival point
    pieces = set()
    for x, y in arrivals(area, room, ex, ey, places):
        tx, ty = min(max(x // 16, 0), tw - 1), min(max(y // 16, 0), th - 1)
        best = None
        for v in range(max(ty - 3, 0), min(ty + 4, th)):
            for u in range(max(tx - 3, 0), min(tx + 4, tw)):
                if g[v][u]:
                    d = max(abs(u - tx), abs(v - ty))
                    if best is None or d < best[0]:
                        best = (d, comp[v][u])
        if best is not None:
            pieces.add(best[1])
    pairs = []
    info = dict(open=sum(sizes), pieces=len(pieces), places=len(places), main=0, diameter=0, roomy=0)
    for piece in sorted(pieces, key=lambda i: -sizes[i]):
        inside = lambda t, piece=piece: 0 <= t[0] < tw and 0 <= t[1] < th and comp[t[1]][t[0]] == piece
        seed = next(t for t in ((x, y) for y in range(th) for x in range(tw)) if inside(t))
        d0, _ = bfs(tw, th, inside, seed)
        u = max(d0, key=d0.get)
        du, _ = bfs(tw, th, inside, u)
        diameter = max(du.values())
        if diameter < MIN_LENGTH:
            continue
        roomy = [t for t in du if all(inside((t[0] + dx, t[1] + dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                 and 2 <= t[0] < tw - 2 and 2 <= t[1] < th - 2
                 and all(max(abs(t[0] - n[0]), abs(t[1] - n[1])) > 3 for n in npcs)]
        roomy_set = set(roomy)
        info['main'] = max(info['main'], sizes[piece]); info['diameter'] = max(info['diameter'], diameter)
        info['roomy'] += len(roomy)
        mine = []
        for a in sorted(roomy, key=lambda t: -du[t]):        # the far ends first
            if any(abs(a[0] - p[0][0]) + abs(a[1] - p[0][1]) < A_SPREAD for p in mine):
                continue
            da, par = bfs(tw, th, inside, a)
            cands = [b for b in roomy if da.get(b, 0) >= max(MIN_FRACTION * diameter, MIN_LENGTH)]
            for b in sorted(cands, key=lambda t: -da[t]):
                if any(abs(b[0] - p[1][0]) + abs(b[1] - p[1][1]) < A_SPREAD for p in mine):
                    continue   # one end per spot: variety between runs
                path = []
                t = b
                while t is not None:
                    path.append(t); t = par[t]
                touched = {p for p in places if any(max(abs(p[0] - q[0]), abs(p[1] - q[1])) <= NODE_REACH for q in path)}
                if len(touched) >= 2:
                    db, _ = bfs(tw, th, inside, b)
                    h = home_for(a, roomy_set, db)
                    if h is None:
                        break
                    mine.append((a, b, db[h], len(touched), path[::-1], h, set(du)))
                    break
            if len(mine) >= MAX_PAIRS:
                break
        pairs += mine
    return tw, th, pairs, info


def main():
    c = S.boot(ROM, 0, seed=6, frames=300)
    c.memory.u8[SAVE + 0x3C] = 0x51
    dismiss(c)
    rows = []
    paths = {}
    for label, an, rn, ex, ey in ROOMS:
        area, room = P.AREAS['AREA_' + an], P.ROOMS['ROOM_%s_%s' % (an, rn)]
        warp(c, area, room, ex, ey, frames=300); dismiss(c)
        if here(c) != (area, room):
            print('%-10s did not land (%s)' % (label, here(c)))
            continue
        tw, th, pairs, info = room_pairs(c, label, an, rn, ex, ey)
        print('%-10s %dx%d  open %d  arrival pieces %d  biggest %d  longest walk %d  places %d  pairs %d' %
              (label, tw, th, info.get('open', 0), info.get('pieces', 0), info.get('main', 0), info.get('diameter', 0),
               info.get('places', 0), len(pairs)))
        for a, b, d, n, path, h, tiles in pairs:
            print('    A %s (pot %s) -> B %s  carry %d tiles, %d places' % (a, h, b, d, n))
            rows.append((an, rn, label, a, b, d, h, tiles))
            paths[(label, a, b)] = path
    if '--check' in args:
        return rows, paths
    with open(OUT, 'w') as f:
        f.write('// Generated by tools/quickstart/carry_pairs.py - do not edit by hand.\n')
        f.write('// The single-room carry quest\'s start (A) and end (B) tiles. Both on open\n')
        f.write('// floor with a 3x3 clear block, in one piece of the room a player can\n')
        f.write('// arrive in, joined by a carry path (no hazards, no ledge hops, no bushes)\n')
        f.write('// of at least 60% of that piece\'s longest walk and 24 tiles, passing\n')
        f.write('// within 6 tiles of two survey places.\n')
        f.write('//\n')
        f.write('// Each pair carries its PIECE: one bit per tile (64 per row, the layout of\n')
        f.write('// QUICKSTART_REACH_GET) of the carry grid\'s piece holding A and B. A parcel\n')
        f.write('// coming down on a tile outside it is lost; inside it, it lies there.\n')
        pieces = []
        for i, (an, rn, label, a, b, d, h, tiles) in enumerate(rows):
            bits = bytearray(512)
            for x, y in tiles:
                k = (y << 6) | x
                bits[k >> 3] |= 1 << (k & 7)
            pieces.append(bits)
            f.write('static const u8 sQuickStartCarryPiece%d[512] = {\n' % i)
            for j in range(0, 512, 16):
                f.write('    ' + ', '.join('0x%02x' % v for v in bits[j:j + 16]) + ',\n')
            f.write('};\n')
        f.write('// The parcel waits at H, three tiles from the giver (outside the talk box).\n')
        f.write('// { area, room, ax, ay, hx, hy, bx, by, carry length H to B in tiles, piece }\n')
        f.write('static const QuickStartCarryPair sQuickStartCarryPairs[] = {\n')
        for i, (an, rn, label, a, b, d, h, tiles) in enumerate(rows):
            f.write('    { AREA_%s, ROOM_%s_%s, %d, %d, %d, %d, %d, %d, %d, sQuickStartCarryPiece%d }, // %s\n' %
                    (an, an, rn, a[0], a[1], h[0], h[1], b[0], b[1], min(d, 255), i, label))
        f.write('};\n')
    print('wrote', OUT, len(rows), 'pairs')
    return rows, paths


if __name__ == '__main__':
    main()
