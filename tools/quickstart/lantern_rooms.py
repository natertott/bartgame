"""Generate the torch and cleanup ? room layouts (docs/QUICKSTART_LANTERN_GUST_EVENTS.md).

Two kinds, per ? room site, from the floors block_rooms.py captured
(build/block_rooms.json: the 100 sites alone in their room):

  TORCHES  3 to 8 unlit torch tiles (TILE_TYPE_117); light them all with
           the Lantern for the prize. Only at sites whose tileset draws a
           torch (build/lantern_sites.json, written by lantern_gust_survey.py
           --draw --json): 59 of 119. The rest (houses, tree hollows, dojos,
           Great Fairy rooms, the Minish houses, whose tilesets list the
           torch but draw nothing) are left out for now. Three
           styles: SPREAD (far apart), CLUSTER (one corner of the room) and
           HIDDEN (tucked against the room's own walls, rocks and
           furniture, far from the door).
  CLEANUP  6 to 16 pieces of debris the Gust Jar clears: spider webs
           (SPIDER_WEB, four orientations) and up to two dust clouds (the
           DUST enemy's carpet dust). Any captured site. Two styles: SCATTER
           (across the floor) and WALLS (webs hung on the room's walls,
           facing out, the way vanilla hangs them).

A torch is a solid tile, and so is a web (it stamps a one-sided blocker
tile; the generator treats it as solid from every side, which can only make
a layout harder than it plays). So every layout is proven here:

  * blocking every torch, or every web, keeps the arrival joined to the
    room's doors, the prize spot and the edge tiles, and seals no pocket
    bigger than a few tiles (block_puzzles.keeps_connected);
  * every torch has a walkable neighbour joined to the arrival, where the
    player stands to swing the Lantern at it;
  * every web can be cleared in some order: the jar takes a web only from
    the side it faces (SpiderWeb_OnGrabbed: the player's animationState >> 1
    must equal the web's type), so its STAND tile - one step against the
    facing direction - must be reachable once the webs before it are gone.
    The order is written to build/lantern_layouts.json for the probe. (The
    Lantern burns a web from any side, so it solves the room too.)

Nothing goes on a reserved tile (block_puzzles.reserved_tiles: rewards,
entrances, fuser spots, the site's content spot) or within two tiles of the
arrival.

Writes include/quickstart/lantern_rooms.h and build/lantern_layouts.json.

    python3 tools/quickstart/lantern_rooms.py [--check] [--verify] [--seed N]
"""
import collections
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_tables as P
from block_puzzles import Floor, flood, bfs_dist, keeps_connected, ROOMS, DIRS, GROUND

SITES_JSON = os.path.join(P.ROOT, 'build', 'lantern_sites.json')
OUT_H = os.path.join(P.ROOT, 'include', 'quickstart', 'lantern_rooms.h')
OUT_JSON = os.path.join(P.ROOT, 'build', 'lantern_layouts.json')

KIND_TORCHES, KIND_CLEANUP = 0, 1
SPREAD, CLUSTER, HIDDEN = 0, 1, 2          # torch styles
SCATTER, WALLS = 0, 1                      # cleanup styles
STYLE_NAMES = {KIND_TORCHES: ('spread', 'cluster', 'hidden'), KIND_CLEANUP: ('scatter', 'walls')}
CLOUD = 4                                  # a debris cell's `what`: 0-3 a web's type, 4 a dust cloud
MAX_CLOUDS = 2                             # each cloud zMallocs its own heap
TORCH_COUNTS = ((3, 4), (5, 8))            # a small and a large layout per style
DEBRIS_COUNTS = ((6, 9), (10, 16))
TRIES = 60
# Sites whose ? room never gets past its first frame, whatever it deals:
# measured by lantern_probe.py at the North Hyrule Field fairy fountain
# tree (47) and the Minish crack by the Wind Ruins (65). The site's event
# runs once, what it deals is gone the next frame, and the dispatcher never
# reaches the event again; the plain wave room spawns no enemies there
# either. A known defect, not this kind's; no layout is built there until
# it is fixed.
BROKEN_SITES = {47, 65}
# No cleanup room where the jar cannot be worked: in the barrel Minish
# house (99) the player stood on a web's stand tile goes into
# PLAYER_CLIMB (the room's act tiles read plain floor there) and the jar
# does nothing (lantern_probe.py).
NO_CLEANUP_SITES = {99}
KEEP_CLEAR = 2                             # tiles from the arrival kept empty


def walled(floor, t):
    """How many of the 8 neighbours are not open floor: a tile against the
    room's walls, rocks or furniture scores high."""
    x, y = t
    return sum(1 for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy) and (x + dx, y + dy) not in floor.open)


def candidates(floor):
    """Ground tiles a torch or a piece of debris may take."""
    sx, sy = floor.start
    spot = spot_tile(floor)
    out = []
    for t in floor.comp & floor.ground:
        if abs(t[0] - sx) + abs(t[1] - sy) <= KEEP_CLEAR or t in floor.keys or t == spot:
            continue
        if abs(t[0] - spot[0]) <= 1 and abs(t[1] - spot[1]) <= 1:
            continue          # the prize drops here; keep a ring round it free
        out.append(t)
    return sorted(out)


def standable(floor, t):
    """Plain floor the player can stand on and use an item from. Open but
    not ground is a ladder or the like: measured in a Minish house, a web's
    stand tile on the ladder put the player in PLAYER_CLIMB, where the jar
    does nothing."""
    x, y = t
    return t in floor.open and floor.r['act'][y][x] in GROUND


def spot_tile(floor):
    return (floor.r['spot'][0] // 16, floor.r['spot'][1] // 16)


def spot_keys(floor):
    """The prize spot as a keypoint, when the arrival reaches it at all (in
    two Minish caves it sits across water the capture counts as hazard)."""
    return [spot_tile(floor)] if spot_tile(floor) in floor.comp else []


def torch_ok(floor, torches):
    blocked = set(torches)
    if not keeps_connected(floor, blocked, extra_keys=spot_keys(floor)):
        return False
    main = flood(floor.comp - blocked, floor.start)
    return all(any((t[0] + dx, t[1] + dy) in main and standable(floor, (t[0] + dx, t[1] + dy)) for dx, dy in DIRS)
               for t in torches)


def pick_spread(cands, n, rng, dist_ok):
    first = rng.choice(cands)
    got = [first]
    while len(got) < n:
        best = max(cands, key=lambda c: (min(abs(c[0] - g[0]) + abs(c[1] - g[1]) for g in got), rng.random()))
        if best in got:
            return None
        got.append(best)
    return got


def pick_cluster(cands, n, rng):
    centre = rng.choice(cands)
    near = sorted(cands, key=lambda c: (abs(c[0] - centre[0]) + abs(c[1] - centre[1]), rng.random()))
    got = []
    for c in near:
        # not shoulder to shoulder: every torch keeps its own lighting tile
        if all(abs(c[0] - g[0]) + abs(c[1] - g[1]) >= 2 for g in got):
            got.append(c)
        if len(got) == n:
            return got
    return None


def pick_hidden(floor, cands, n, rng):
    dist = bfs_dist(floor.comp, floor.start)
    far = max(dist.values()) or 1
    scored = sorted(cands, key=lambda c: -(walled(floor, c) * 4 + 6 * dist.get(c, 0) / far + rng.random() * 3))
    got = []
    for c in scored:
        if walled(floor, c) < 3:
            continue
        if all(abs(c[0] - g[0]) + abs(c[1] - g[1]) >= 3 for g in got):
            got.append(c)
        if len(got) == n:
            return got
    return None


def torch_layouts(floor, rng):
    cands = candidates(floor)
    room = len(floor.comp)
    out = []
    for style in (SPREAD, CLUSTER, HIDDEN):
        for lo, hi in TORCH_COUNTS:
            hi = min(hi, max(lo, room // 14))
            for _ in range(TRIES):
                n = rng.randint(lo, hi)
                if len(cands) < n * 2:
                    break
                if style == SPREAD:
                    got = pick_spread(cands, n, rng, None)
                elif style == CLUSTER:
                    got = pick_cluster(cands, n, rng)
                else:
                    got = pick_hidden(floor, cands, n, rng)
                if got and torch_ok(floor, got) and not any(sorted(got) == o['cells'] for o in out):
                    out.append(dict(kind=KIND_TORCHES, style=style, cells=sorted(got),
                                    what=[0] * len(got)))
                    break
    return out


def stand_of(w, d):
    """Where the player stands to gust web w of type d: one step back from
    the way they face (type 0 is gusted facing up, from below)."""
    return (w[0] - DIRS[d][0], w[1] - DIRS[d][1])


def pull_of(w, d):
    """The two tiles behind the stand tile. The jar only latches the web;
    the player tears it off by being pulled back (SpiderWeb_SubAction0
    walks them away a few pixels a frame), so these must be free too.
    Measured: a web whose stand tile backed onto a wall or another web was
    grabbed, held and never came away, and with one free tile it came away
    or not depending on where in the stand tile the player stood (the
    Veil Falls rupee hall). Two make it forgiving."""
    return [(w[0] - k * DIRS[d][0], w[1] - k * DIRS[d][1]) for k in (2, 3)]


def clear_order(floor, webs):
    """A clearing order for the webs (dict tile -> type), or None. Greedy
    is exact here: clearing a web only ever opens floor."""
    left = dict(webs)
    order = []
    while left:
        reach = flood(floor.comp - set(left), floor.start)
        ready = [w for w, d in sorted(left.items())
                 if stand_of(w, d) in reach and standable(floor, stand_of(w, d))
                 and all(p in reach and standable(floor, p) for p in pull_of(w, d))]
        if not ready:
            return None
        for w in ready:
            order.append(w)
            del left[w]
    return order


def web_types(floor, t, rng, wall_first):
    """Orientations web t may take: its stand tile must be open floor. With
    wall_first, the ones with a wall behind the web come first (it hangs on
    the wall and faces into the room)."""
    out = []
    for d in range(4):
        s = stand_of(t, d)
        if not standable(floor, s) or not all(standable(floor, p) for p in pull_of(t, d)):
            continue
        behind = (t[0] + DIRS[d][0], t[1] + DIRS[d][1])
        out.append((0 if (wall_first and behind not in floor.open) else 1, rng.random(), d))
    return [d for _, _, d in sorted(out)]


def cloud_approach(c):
    """The tiles a dust cloud is gusted from: the jar takes it with the
    player 23 to 36 px straight below its centre (measured; at 16 px or
    44 px it never came), so the probe stands at 28 px, in the second
    tile down, and walks there through the first."""
    return [(c[0], c[1] + 1), (c[0], c[1] + 2)]


def debris_layouts(floor, rng):
    cands = candidates(floor)
    reach_all = flood(floor.comp, floor.start)
    room = len(floor.comp)
    out = []
    for style in (SCATTER, WALLS):
        for lo, hi in DEBRIS_COUNTS:
            hi = min(hi, max(lo, room // 8))
            for _ in range(TRIES):
                n = rng.randint(lo, hi)
                if len(cands) < n * 2:
                    break
                pool = list(cands)
                if style == WALLS:
                    pool = [c for c in pool if walled(floor, c) >= 2]
                rng.shuffle(pool)
                clouds = []
                if style == SCATTER:
                    for c in pool:
                        if len(clouds) >= min(MAX_CLOUDS, rng.randint(0, MAX_CLOUDS)):
                            break
                        # a cloud spreads over its neighbours: open ground all
                        # round, and the two tiles below it walkable from the
                        # door (the jar takes it from 23 to 36 px below)
                        if walled(floor, c) == 0 and all(abs(c[0] - g[0]) + abs(c[1] - g[1]) >= 4 for g in clouds) \
                                and all(a in reach_all and standable(floor, a) for a in cloud_approach(c)):
                            clouds.append(c)
                webs = {}
                for c in pool:
                    if len(webs) + len(clouds) >= n:
                        break
                    if c in clouds or any(abs(c[0] - g[0]) <= 1 and abs(c[1] - g[1]) <= 1 for g in clouds) \
                            or any(c in cloud_approach(g) for g in clouds):
                        continue
                    if any(abs(c[0] - w[0]) + abs(c[1] - w[1]) < 2 for w in webs):
                        continue
                    types = web_types(floor, c, rng, style == WALLS)
                    if types:
                        webs[c] = types[0]
                if len(webs) + len(clouds) < lo:
                    continue
                if not keeps_connected(floor, set(webs), extra_keys=spot_keys(floor)):
                    continue
                order = clear_order(floor, webs)
                if order is None:
                    continue
                cells = sorted(list(webs) + clouds)
                what = [webs[c] if c in webs else CLOUD for c in cells]
                if any(cells == o['cells'] for o in out):
                    continue
                out.append(dict(kind=KIND_CLEANUP, style=style, cells=cells, what=what,
                                order=[list(w) for w in order]))
                break
    return out


def generate(seed):
    rooms = json.load(open(ROOMS))
    # Listed in the tileset AND seen on screen (lantern_gust_survey.py
    # --draw): the Minish houses list the torch's tile and draw nothing.
    torch_sites = {r['site'] for r in json.load(open(SITES_JSON))
                   if r['bottom']['torch'] and r['bottom']['lit'] and r.get('draws')}
    layouts = []
    for key in sorted((k for k in rooms if k.startswith('site:')), key=lambda k: int(k.split(':')[1])):
        site = int(key.split(':')[1])
        if site in BROKEN_SITES:
            continue
        floor = Floor(rooms[key])
        rng = random.Random('%d:%s' % (seed, key))
        got = []
        if site in torch_sites:
            got += torch_layouts(floor, rng)
        if site not in NO_CLEANUP_SITES:
            got += debris_layouts(floor, rng)
        for g in got:
            g['site'] = site
            g['room'] = rooms[key]['room']
        layouts += got
    return layouts


def emit(layouts):
    lines = ['// GENERATED by tools/quickstart/lantern_rooms.py - do not edit.',
             '// Torch and cleanup ? rooms: docs/QUICKSTART_LANTERN_GUST_EVENTS.md.',
             '// Cells are room tiles, room-local: x, y, what (a web\'s type 0-3, 4 a dust',
             '// cloud; 0 for a torch).',
             '#ifndef QUICKSTART_LANTERN_ROOMS_H', '#define QUICKSTART_LANTERN_ROOMS_H', '']
    rows = []
    for n, l in enumerate(layouts):
        cells = ', '.join('%d, %d, %d' % (c[0], c[1], w) for c, w in zip(l['cells'], l['what']))
        lines.append('static const u8 sQuickStartLanternCells%d[] = { %s };' % (n, cells))
        rows.append('    { %d, %d, %d, %d, sQuickStartLanternCells%d }, // %s %s'
                    % (l['site'], l['kind'], l['style'], len(l['cells']), n,
                       l['room'].replace('ROOM_', ''), STYLE_NAMES[l['kind']][l['style']]))
    lines += ['', 'static const QuickStartLanternLayout sQuickStartLanternLayouts[] = {'] + rows + ['};', '',
              '#endif', '']
    return '\n'.join(lines)


def parse_header(text):
    cells = {int(m.group(1)): [int(v) for v in m.group(2).split(',') if v.strip()]
             for m in re.finditer(r'static const u8 sQuickStartLanternCells(\d+)\[\] = \{ ?(.*?) ?\};', text)}
    out = []
    for m in re.finditer(r'\{ (\d+), (\d+), (\d+), (\d+), sQuickStartLanternCells(\d+) \}', text):
        site, kind, style, count, n = (int(m.group(i)) for i in range(1, 6))
        raw = cells[n]
        out.append(dict(site=site, kind=kind, style=style, count=count,
                        cells=[(raw[i], raw[i + 1]) for i in range(0, len(raw), 3)],
                        what=[raw[i + 2] for i in range(0, len(raw), 3)]))
    return out


def verify():
    """The shipped table, decoded as game.c reads it, against the layouts
    file, and every layout re-proven on its room's floor."""
    rooms = json.load(open(ROOMS))
    header = parse_header(open(OUT_H).read())
    layouts = json.load(open(OUT_JSON))
    bad = []
    if len(header) != len(layouts):
        print('header has %d layouts, the json %d' % (len(header), len(layouts)))
        return 1
    for n, (h, l) in enumerate(zip(header, layouts)):
        floor = Floor(rooms['site:%d' % h['site']])
        cells = [tuple(c) for c in l['cells']]
        if h['cells'] != cells or h['what'] != l['what'] or h['count'] != len(cells) or h['kind'] != l['kind']:
            bad.append('layout %d: decodes differently' % n)
            continue
        for c in cells:
            if c in floor.reserved or c not in floor.ground or c == floor.start:
                bad.append('layout %d: (%d,%d) is not free ground' % (n, c[0], c[1]))
        if h['kind'] == KIND_TORCHES:
            if not torch_ok(floor, cells):
                bad.append('layout %d: a torch walls the room or cannot be lit' % n)
        else:
            webs = {c: w for c, w in zip(cells, h['what']) if w != CLOUD}
            if sum(1 for w in h['what'] if w == CLOUD) > MAX_CLOUDS:
                bad.append('layout %d: too many clouds' % n)
            if not keeps_connected(floor, set(webs), extra_keys=spot_keys(floor)):
                bad.append('layout %d: the webs wall the room' % n)
            if clear_order(floor, webs) is None:
                bad.append('layout %d: no clearing order' % n)
            reach_all = flood(floor.comp, floor.start)
            for c, w in zip(cells, h['what']):
                if w == CLOUD and any(a not in reach_all or a in webs or not standable(floor, a)
                                      for a in cloud_approach(c)):
                    bad.append('layout %d: cloud (%d,%d) cannot be approached from below' % (n, c[0], c[1]))
    kinds = collections.Counter(('torches', 'cleanup')[h['kind']] for h in header)
    sites = {k: len({h['site'] for h in header if h['kind'] == i}) for i, k in enumerate(('torches', 'cleanup'))}
    print('%d layouts %s over sites %s: %d problems' % (len(header), dict(kinds), sites, len(bad)))
    for b in bad[:20]:
        print('  ' + b)
    return 1 if bad else 0


def main():
    if '--verify' in sys.argv:
        return verify()
    seed = int(sys.argv[sys.argv.index('--seed') + 1]) if '--seed' in sys.argv else 0x7012C
    layouts = generate(seed)
    text = emit(layouts)
    if '--check' in sys.argv:
        old = open(OUT_H).read() if os.path.exists(OUT_H) else ''
        print('up to date' if old == text else 'STALE')
        return 0 if old == text else 1
    open(OUT_H, 'w').write(text)
    with open(OUT_JSON, 'w') as f:
        json.dump(layouts, f)
    kinds = collections.Counter((('torches', 'cleanup')[l['kind']], STYLE_NAMES[l['kind']][l['style']]) for l in layouts)
    print('%d layouts %s -> %s' % (len(layouts), dict(kinds), OUT_H))
    return 0


if __name__ == '__main__':
    sys.exit(main())
