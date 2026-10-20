"""Generate the block puzzles (docs/QUICKSTART_BLOCK_PUZZLES.md).

Two kinds, from the user's mechanics sheet (Block_Puzzle_Mechanics.pdf):

  TEMPLATE  a fixed reference arrangement (gray rocks, never moves) beside a
            board of movable rocks; push the movable ones until they occupy
            the same cells of the board as the reference occupies of its
            frame. Cells compared, not rocks. A match pays a prize.
  MAZE      a walled grid with a chest (or, in the overworld, a door) at its
            back; movable rocks seal the passages. Push them in the right
            order until the player can stand in front of the chest.

The rules are the engine's own, measured (tools/quickstart/block_probe.py):
one push moves a rock one tile, the player must stand on the far side, a
rock never moves into a wall or another rock (no chain pushing), and rocks
cannot be pulled. The game adds three: a FIXED rock never moves, a rock
tinted for one axis moves only along it, and no rock leaves its board.

Every instance is solved here before it ships. A template's start is made
by REVERSE moves from the goal (pulls), so it is solvable by construction;
a breadth-first search then measures the fewest pushes (capped). A maze is
drawn at random and kept only if the search finds a way through. The
search walks the player over the room's real floor around the puzzle, so a
wall beside a board is accounted for.

Reads build/block_rooms.json (tools/quickstart/block_rooms.py), writes
include/quickstart/block_puzzles.h and build/block_solutions.json (each
instance's push list, for the probe).

    python3 tools/quickstart/block_puzzles.py [--check] [--seed N]
    python3 tools/quickstart/block_puzzles.py --append row:20,site:119   # new owners only
    python3 tools/quickstart/block_puzzles.py --verify-append            # ...and their check
"""
import collections
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_tables as P
import exit_lists as X

ROOMS = os.path.join(P.ROOT, 'build', 'block_rooms.json')
OUT_H = os.path.join(P.ROOT, 'include', 'quickstart', 'block_puzzles.h')
OUT_SOL = os.path.join(P.ROOT, 'build', 'block_solutions.json')

GROUND = {0, 9, 10, 12}          # act tiles of plain floor (measured over all 120 rooms)
# pit, shallow/deep water, ice, swamp, lava - and 0x08, TILE_ACT_PLAYER_WALK:
# floor that crumbles into a pit once walked on (four caves: Veil Falls'
# entrance and three Minish caves). It was counted as ground until a Veil
# Falls template's solution walked the player over it and left a hole where
# the next push had to stand.
HAZARD = {0x08, 0x0D, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x5A}
DIRS = ((0, -1), (1, 0), (0, 1), (-1, 0))   # up, right, down, left = animationState >> 1
ANY, HORIZ, VERT = 0, 1, 2
ALLOW = {ANY: (0, 1, 2, 3), HORIZ: (1, 3), VERT: (0, 2)}
KIND_TEMPLATE, KIND_MAZE = 0, 1

# Template classes: board side, movable rocks, axis-limited rocks, scramble
# length range, minimum pushes to keep.
TEMPLATE_CLASSES = [
    ('XS', 3, 3, 0, (6, 10), 5),
    ('S', 4, 4, 0, (8, 14), 7),
    ('M', 5, 5, 1, (10, 18), 9),
    ('L', 6, 7, 2, (12, 22), 11),
    ('XL', 7, 9, 3, (14, 26), 13),
]
# Maze grids (interior w, h), movable rocks, fixed interior rocks, min pushes.
# Maze grids: interior w, h, movable rocks, percent of the interior carved
# open, minimum pushes.
MAZE_CLASSES = [
    ('XS', 4, 3, 2, 70, 3),
    ('S', 5, 4, 3, 65, 5),
    ('M', 6, 5, 4, 62, 6),
]
MAX_ROCKS_SITE = 28      # entity budget in a ? room (nothing else lives there)
MAX_ROCKS_ROW = 26       # ... and in a region room, which also holds waves
FRAMES = 3               # template placements, and chest-maze placements, per room
CONTENTS = 32            # contents per placement: what a run draws from (the testbed addresses 32)
MIN_CONTENTS = 3         # fewer, and the placement is not worth its slot
MIN_DOOR_CONTENTS = 2    # a door maze is the only one in front of its door
CONTENT_TRIES = 6        # attempts per wanted content
MAZE_TRIES = 25          # ... for a maze, where most carves come out too easy
SEARCH_CAP = 60000       # BFS states before a template's minimum is called "at least the scramble"
BIG_SEARCH_CAP = 6000    # ... for the L and XL boards
WHY = collections.Counter()   # why candidates were dropped, for tuning (per process)


# ------------------------------------------------------------------ floors --

class Floor:
    def __init__(self, r):
        self.r = r
        self.tw, self.th = r['tw'], r['th']
        # WALK: where the player can stand (no hazard underfoot); GROUND:
        # plain floor, where a rock may stand or be pushed.
        self.open = {(x, y) for y in range(self.th) for x in range(self.tw)
                     if r['coll'][y][x] == 0 and r['act'][y][x] not in HAZARD}
        self.reserved = reserved_tiles(r['area'], r['room'])
        # PASSABLE: no collision at all - a superset of WALK (it keeps
        # shallow water, swamp, ice, even pits), what a maze ring must seal.
        self.passable = {(x, y) for y in range(self.th) for x in range(self.tw) if r['coll'][y][x] == 0}
        self.ground = {(x, y) for (x, y) in self.open if r['act'][y][x] in GROUND} - self.reserved
        px, py = r['player']
        start = (px // 16, py // 16)
        if start not in self.open:
            start = min(self.open, key=lambda t: abs(t[0] - start[0]) + abs(t[1] - start[1]))
        self.start = start
        self.comp = flood(self.open, start)
        self.keys = self.keypoints()

    def keypoints(self):
        """Tiles that must stay connected to the arrival: room-edge tiles of
        the arrival component (borders), the room's door triggers, the
        pool row's entrance and reward, and NPCs' standing tiles."""
        keys = {self.start}
        for (x, y) in self.comp:
            if x <= 1 or y <= 1 or x >= self.tw - 2 or y >= self.th - 2:
                keys.add((x, y))
        rn = self.r['room']
        for row in X.BY_ROOM.get(rn, []):
            if row[0] == 'WARP_TYPE_AREA':
                t = (row[1] // 16, row[2] // 16)
                for d in ((0, 0),) + DIRS:
                    n = (t[0] + d[0], t[1] + d[1])
                    if n in self.comp:
                        keys.add(n)
                        break
        for k in ('entrance', 'reward'):
            if k in self.r:
                t = (self.r[k][0] // 16, self.r[k][1] // 16)
                if t in self.comp:
                    keys.add(t)
        return keys


_RESERVED = {}


def reserved_tiles(area, room):
    """Tiles of this room the mode already uses, which no rock, switch or
    prize may take: every pool row's reward, entrance, boss spot and landing
    spots, every fuser scatter spot, every ? room site's content spot. The
    tiles themselves, no margin: the drop rule's 48 px square took 179 of
    Trilby's 332 reachable tiles and every layout with them, and even one
    tile round each cost most of them. Keeping the spot free is what
    matters; Floor.keys keeps the entrance and reward connected.
    Found the hard way: a Lake Hylia maze put a rock on the region's reward
    tile and another on a fuser spot (invariant_check)."""
    key = (area, room)
    if key in _RESERVED:
        return _RESERVED[key]
    import drop_spots
    out = set()

    def mark(px, py, r):
        tx, ty = px // 16, py // 16
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                out.add((tx + dx, ty + dy))
    drops = drop_spots.drop_table()
    for i, row in enumerate(P.region_pool()):
        if (row['areaName'], row['roomName']) != key:
            continue
        mark(row['entrance'][0], row['entrance'][1], 0)
        mark(row['reward'][0], row['reward'][1], 0)
        if row['boss']:
            mark(row['boss'][0], row['boss'][1], 0)
        for x, y in (drops[i] if i < len(drops) else []):
            mark(x, y, 0)
    for f in P.fuser_spots():
        if (f['areaName'], f['roomName']) == key:
            for x, y in f['spots']:
                mark(x, y, 0)
    for an, rn, _a, _r, cx, cy, _gate in P.content_sites_full():
        if (an, rn) == key:
            mark(cx, cy, 0)
    # Where the room's doors and borders land the player, and the ring round
    # each (Oct 2026). Found in Hyrule Castle's lower hall: a maze built over
    # the ring hall's west door landing read as solved the moment it was
    # dealt (block_probe.py's reset check; the ROM's maze flood started from
    # the player stood inside it). The pool row's own entrance was the only
    # landing this knew about.
    for rows in X.BY_ROOM.values():
        for r in rows:
            if (r[6], r[7]) == key:
                mark(r[3], r[4], 1)
    _RESERVED[key] = out
    return out


def flood(cells, start):
    if start not in cells:
        return set()
    seen = {start}
    q = collections.deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in DIRS:
            n = (x + dx, y + dy)
            if n in cells and n not in seen:
                seen.add(n)
                q.append(n)
    return seen


def bfs_dist(cells, start):
    dist = {start: 0}
    q = collections.deque([start])
    while q:
        c = q.popleft()
        for dx, dy in DIRS:
            n = (c[0] + dx, c[1] + dy)
            if n in cells and n not in dist:
                dist[n] = dist[c] + 1
                q.append(n)
    return dist


def keeps_connected(floor, blocked, extra_keys=()):
    """Blocking `blocked` leaves every keypoint joined to the arrival, and
    seals off no pocket bigger than a few tiles."""
    rest = floor.comp - blocked
    if floor.start in blocked:
        return False
    main = flood(rest, floor.start)
    for k in set(floor.keys) | set(extra_keys):
        if k not in blocked and k not in main:
            return False
    return len(rest) - len(main) <= 4


def window(floor, cells, margin=4):
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    x0, x1, y0, y1 = min(xs) - margin, max(xs) + margin, min(ys) - margin, max(ys) + margin
    return {c for c in floor.comp if x0 <= c[0] <= x1 and y0 <= c[1] <= y1}


# ------------------------------------------------------------------ solver --

class Puzzle:
    """walk: tiles the player may stand on (fixed rocks already removed);
    board: tiles a movable rock may occupy; classes[i]: rock i's axis rule.

    Bitboards over a local frame with one padding column, so a flood is a
    handful of big-integer shifts rather than a per-tile walk - the search
    visits tens of thousands of states per instance."""

    def __init__(self, walk, board, classes):
        cells = set(walk) | set(board)
        self.x0 = min(c[0] for c in cells) - 1
        self.y0 = min(c[1] for c in cells) - 1
        self.W = max(c[0] for c in cells) - self.x0 + 2
        self.H = max(c[1] for c in cells) - self.y0 + 2
        self.S = self.W + 1           # row stride, with the padding column
        self.walk = self.mask(walk)
        self.board = self.mask(board)
        self.classes = tuple(classes)
        self.steps = (-self.S, 1, self.S, -1)   # up, right, down, left

    def bit(self, c):
        return (c[1] - self.y0) * self.S + (c[0] - self.x0)

    def cell(self, b):
        return (b % self.S + self.x0, b // self.S + self.y0)

    def mask(self, cells):
        m = 0
        for c in cells:
            m |= 1 << self.bit(c)
        return m

    def flood(self, start, passable):
        r = start & passable
        S = self.S
        while True:
            n = (r | (r << 1) | (r >> 1) | (r << S) | (r >> S)) & passable
            if n == r:
                return r
            r = n

    def region(self, occ, player_bit):
        return self.flood(1 << player_bit, self.walk & ~occ)

    def state(self, rocks):
        return tuple(tuple(sorted(r for r, c in zip(rocks, self.classes) if c == k)) for k in (ANY, HORIZ, VERT))

    def moves(self, rocks, occ, region):
        for i, p in enumerate(rocks):
            for d in ALLOW[self.classes[i]]:
                st = self.steps[d]
                stand, dest = p - st, p + st
                if stand >= 0 and dest >= 0 and (region >> stand) & 1 and (self.board >> dest) & 1 and not (occ >> dest) & 1:
                    yield i, d, dest

    def solve(self, rocks, player, done, cap=SEARCH_CAP):
        """Fewest pushes to a state where done(occ, region) holds: (count,
        [(x, y, dir), ...]) or (None, None) when the cap is hit or nothing
        works."""
        rocks = tuple(self.bit(r) for r in rocks)
        occ = sum(1 << r for r in rocks)
        region = self.region(occ, self.bit(player))
        if done(occ, region):
            return 0, []
        seen = {(self.state(rocks), region)}
        q = collections.deque([(rocks, occ, region, ())])
        while q:
            rocks, occ, region, path = q.popleft()
            for i, d, dest in self.moves(rocks, occ, region):
                src = rocks[i]
                nr = rocks[:i] + (dest,) + rocks[i + 1:]
                nocc = (occ & ~(1 << src)) | (1 << dest)
                nreg = self.flood(1 << src, self.walk & ~nocc)
                key = (self.state(nr), nreg)
                if key in seen:
                    continue
                npath = path + ((src, d),)
                if done(nocc, nreg):
                    return len(npath), [(self.cell(b)[0], self.cell(b)[1], dd) for b, dd in npath]
                seen.add(key)
                if len(seen) > cap:
                    return None, None
                q.append((nr, nocc, nreg, npath))
        return None, None


def scramble(puz, goal, player, n, rng):
    """Reverse moves (pulls) from the goal: rock at q, player at p = q - d
    with p - d free, pulls the rock to p and steps to p - d. Undoing that
    is a legal push, so the result is solvable by construction - provided
    the player could get to p - d in the first place, so a pull is only
    taken when p - d is reachable from the ENTRY (`player`) with the rocks
    where they end up. Without that the scramble walked the player into a
    strip of ring that a wall and two corner posts seal off, and the
    "solvable" start was not.

    Returns (start, player, pulls): `pulls` reversed and read as pushes is
    a solution, the one kept when the search cannot prove a minimum."""
    rocks = [puz.bit(g) for g in goal]
    pb = puz.bit(player)
    entry = pb
    moved = 0
    pulls = []
    for _ in range(n * 6):
        if moved >= n:
            break
        occ = sum(1 << r for r in rocks)
        region = puz.region(occ, pb)
        opts = []
        for i, q in enumerate(rocks):
            for d in ALLOW[puz.classes[i]]:
                st = puz.steps[d]
                p = q - st
                back = p - st
                if p < 0 or back < 0:
                    continue
                if (region >> p) & 1 and (puz.board >> p) & 1 and (puz.walk >> back) & 1 and not (occ >> back) & 1:
                    nocc = (occ & ~(1 << q)) | (1 << p)
                    if (puz.region(nocc, entry) >> back) & 1:
                        opts.append((i, p, back))
        if not opts:
            break
        i, p, back = rng.choice(opts)
        pulls.append((puz.cell(p), next(d for d in ALLOW[puz.classes[i]] if rocks[i] - puz.steps[d] == p)))
        rocks[i] = p
        pb = back
        moved += 1
    return tuple(puz.cell(r) for r in rocks), puz.cell(pb), pulls


def reverse_search(puz, solved, entry, sealed, cap=30000, depth_cap=40):
    """Breadth-first over REVERSE moves from a solved arrangement (the
    player at the entry). Every state reached is solvable forward. Returns
    the states, deepest first, for which sealed(occ, region) holds - the
    starts worth measuring."""
    eb = puz.bit(entry)
    rocks = tuple(puz.bit(r) for r in solved)
    occ = sum(1 << r for r in rocks)
    region = puz.region(occ, eb)
    seen = {(puz.state(rocks), region)}
    q = collections.deque([(rocks, occ, region, 0)])
    hits = []
    while q:
        rocks, occ, region, depth = q.popleft()
        if depth >= depth_cap:
            continue
        for i, qb in enumerate(rocks):
            for d in ALLOW[puz.classes[i]]:
                st = puz.steps[d]
                p = qb - st
                back = p - st
                if p < 0 or back < 0:
                    continue
                if not ((region >> p) & 1 and (puz.board >> p) & 1 and (puz.walk >> back) & 1 and not (occ >> back) & 1):
                    continue
                nocc = (occ & ~(1 << qb)) | (1 << p)
                nreg = puz.region(nocc, back)
                if not (nreg >> eb) & 1:
                    continue
                nr = rocks[:i] + (p,) + rocks[i + 1:]
                key = (puz.state(nr), nreg)
                if key in seen:
                    continue
                seen.add(key)
                if sealed(nocc, nreg):
                    hits.append((depth + 1, nr))
                if len(seen) > cap:
                    q.clear()
                    break
                q.append((nr, nocc, nreg, depth + 1))
    hits.sort(key=lambda h: -h[0])
    return [tuple(puz.cell(b) for b in h[1]) for h in hits]


# --------------------------------------------------------------- templates --

def frame_cells(ox, oy, side):
    inner = {(ox + i, oy + j) for i in range(side) for j in range(side)}
    ring = {(ox + i, oy + j) for i in range(-1, side + 1) for j in range(-1, side + 1)} - inner
    posts = {(ox - 1, oy - 1), (ox + side, oy - 1), (ox - 1, oy + side), (ox + side, oy + side)}
    return inner, ring, posts


def board_fits(floor, ox, oy, side):
    inner, ring, posts = frame_cells(ox, oy, side)
    return inner <= floor.ground and inner <= floor.comp and ring <= floor.comp and posts <= floor.ground


def ref_fits(floor, ox, oy, side):
    inner, ring, posts = frame_cells(ox, oy, side)
    return inner <= floor.ground and inner <= floor.comp and posts <= floor.ground and posts <= floor.comp


def template_layouts(floor, side, rng, limit=40):
    """(reference origin, board origin) pairs: both frames fit, they do not
    overlap (a tile of air between them), and together they fit on about
    one screen, so the player can see the pattern while pushing."""
    boards = [(x, y) for y in range(1, floor.th - side) for x in range(1, floor.tw - side)
              if board_fits(floor, x, y, side)]
    refs = [(x, y) for y in range(1, floor.th - side) for x in range(1, floor.tw - side)
            if ref_fits(floor, x, y, side)]
    cx = sum(c[0] for c in floor.comp) / len(floor.comp)
    cy = sum(c[1] for c in floor.comp) / len(floor.comp)
    boards.sort(key=lambda b: abs(b[0] + side / 2 - cx) + abs(b[1] + side / 2 - cy) + rng.random() * 4)
    out = []
    span = side + 2
    for bx, by in boards[:limit]:
        b_box = (bx - 2, by - 2, bx + side + 1, by + side + 1)   # the frame and a tile around it
        for rx, ry in refs:
            r_box = (rx - 1, ry - 1, rx + side, ry + side)
            if not (r_box[2] < b_box[0] or r_box[0] > b_box[2] or r_box[3] < b_box[1] or r_box[1] > b_box[3]):
                continue
            w = max(b_box[2], r_box[2]) - min(b_box[0], r_box[0]) + 1
            h = max(b_box[3], r_box[3]) - min(b_box[1], r_box[1]) + 1
            if (w <= max(15, 2 * span + 2) and h <= span + 2) or (h <= max(10, 2 * span + 2) and w <= span + 2):
                out.append((rx, ry, bx, by))
    rng.shuffle(out)
    out.sort(key=lambda L: abs(L[2] + side / 2 - cx) + abs(L[3] + side / 2 - cy))
    return out


def template_frames(floor, rng, max_rocks, site_owner):
    """Up to FRAMES template placements, biggest class first, at distinct
    spots, each with its pool of contents. A placement is everything that
    depends on the room - the board, the reference beside it, the posts,
    the switch, the prize tile, where the player comes in; a content is a
    goal shape and a scrambled start inside it."""
    out, used = [], []
    for cls in reversed(TEMPLATE_CLASSES):
        name, side, nrocks, nlimited, (lo, hi), minpush = cls
        if site_owner and name == 'XL':
            continue
        if 2 * nrocks + 8 > max_rocks:
            continue
        for (rx, ry, bx, by) in template_layouts(floor, side, rng)[:60]:
            if len(out) >= FRAMES:
                break
            if any(abs(bx - ux) < 2 and abs(by - uy) < 2 for ux, uy in used):
                continue
            r_in, r_ring, r_posts = frame_cells(rx, ry, side)
            b_in, b_ring, b_posts = frame_cells(bx, by, side)
            posts = r_posts | b_posts
            foot = r_in | r_posts | b_in | b_ring
            # The posts and the board here; each content checks its own
            # reference cells (the whole reference square counted blocked
            # cut the small rooms, the Grimblade dojo among them).
            blocked = posts | b_in
            if not keeps_connected(floor, blocked):
                continue
            spot = prize_spot(floor, foot, blocked, (bx + side // 2, by + side // 2))
            sw = switch_spot(floor, foot, blocked, (bx - 1, by + side))
            if spot is None or sw is None or sw == spot or not keeps_connected(floor, blocked | {sw}):
                continue
            # The player comes from the arrival: enter from the ring tile
            # nearest it, so a ring segment walled off from the room is
            # never assumed reachable.
            dist = bfs_dist(floor.comp - blocked - {sw}, floor.start)
            outside = [c for c in b_ring if c not in b_posts and c in dist]
            if not outside:
                continue
            frame = dict(kind=KIND_TEMPLATE, cls=name, board=(bx, by, side, side), ref=(rx, ry),
                         fixed=sorted(posts), prize=spot, switch=sw, target=None, door=0,
                         entry=min(outside, key=lambda c: dist[c]))
            # ... and the prize, the switch and the way in stay clear of the
            # reference square whatever its shape.
            if {spot, sw, frame['entry']} & r_in:
                continue
            contents = template_contents(floor, cls, rng, frame, foot)
            if len(contents) >= MIN_CONTENTS:
                frame['contents'] = contents
                out.append(frame)
                used.append((bx, by))
        if len(out) >= FRAMES:
            break
    return out


def first_solved(path, puz, start, gm):
    """`path` up to the first push after which the rocks fill `gm`."""
    occ = puz.mask(start)
    for n, (x, y, d) in enumerate(path):
        b = puz.bit((x, y))
        occ = (occ & ~(1 << b)) | (1 << (b + puz.steps[d]))
        if occ == gm:
            return path[:n + 1]
    return path


def template_contents(floor, cls, rng, frame, foot):
    """Up to CONTENTS distinct goals and starts for one template frame. A
    start is made by pulls from the goal, so it is solvable by
    construction; a search then proves the fewest pushes and drops the easy
    ones. Where the search hits its cap (the large boards), the scramble
    undone is the solution kept and its length an upper bound."""
    name, side, nrocks, nlimited, (lo, hi), minpush = cls
    bx, by = frame['board'][:2]
    rx, ry = frame['ref']
    posts = set(map(tuple, frame['fixed']))
    b_in = {(bx + i, by + j) for i in range(side) for j in range(side)}
    entry = tuple(frame['entry'])
    base = window(floor, foot) - posts - {tuple(frame['switch'])}
    cells = [(i, j) for i in range(side) for j in range(side)]
    out, seen = [], set()
    for _ in range(CONTENTS * CONTENT_TRIES):
        if len(out) >= CONTENTS:
            break
        goal_rel = rng.sample(cells, nrocks)
        goal = [(bx + i, by + j) for i, j in goal_rel]
        ref = {(rx + i, ry + j) for i, j in goal_rel}
        classes = [ANY] * nrocks
        for k in rng.sample(range(nrocks), nlimited):
            classes[k] = rng.choice((HORIZ, VERT))
        puz = Puzzle(base - ref, b_in, classes)
        start, _p, pulls = scramble(puz, goal, entry, rng.randint(lo, hi), rng)
        goalset = frozenset(goal)
        if sum(1 for st in start if st not in goalset) < max(2, (nrocks + 1) // 2):
            continue
        if not keeps_connected(floor, posts | b_in | ref | {tuple(frame['switch'])}):
            continue
        key = (tuple(sorted(goal)), tuple(sorted(zip(start, classes))))
        if key in seen:
            continue
        seen.add(key)
        gm = puz.mask(goal)
        # The L and XL boards never prove inside 60,000 states (all six in
        # the first build hit the cap): a smaller cap, the same outcome, a
        # tenth of the time.
        n, path = puz.solve(start, entry, lambda occ, region, gm=gm: occ == gm,
                            cap=SEARCH_CAP if nrocks <= 5 else BIG_SEARCH_CAP)
        if path is None:
            # The scramble undone - cut where it first matches: a scramble
            # can pull rocks out of the shape and back, and the game locks
            # a template the moment it matches (a Minish-path template's
            # 22-push solution matched at push 20, and push 21 was refused).
            path = first_solved([(c[0], c[1], d) for c, d in reversed(pulls)], puz, start, gm)
            if len(path) < minpush + 2:
                continue
        elif n < minpush:
            continue
        out.append(dict(move=[(s[0], s[1], c) for s, c in zip(start, classes)], goal=sorted(goal),
                        pushes=(n if n is not None else -1), solution=path))
    return out


def prize_spot(floor, foot, blocked, near):
    best = None
    # reachable with the puzzle in place, not just open floor
    main = flood(floor.comp - foot - blocked, floor.start)
    for c in main - floor.reserved:
        if not any((c[0] + dx, c[1] + dy) in foot for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            continue
        d = abs(c[0] - near[0]) + abs(c[1] - near[1])
        if best is None or d < best[0]:
            best = (d, c)
    return best[1] if best else None


def switch_spot(floor, foot, blocked, near):
    """An open tile just outside the footprint, not a keypoint, that does
    not cut anything when the switch stands on it."""
    cands = []
    # Reachable with the puzzle in place: a switch beside a maze's ring once
    # stood in a pocket the ring itself sealed (Trilby's rupee cave), and
    # nothing could strike it.
    main = flood(floor.comp - foot - blocked, floor.start)
    for c in main - floor.reserved:
        if c in floor.keys:
            continue
        if not any((c[0] + dx, c[1] + dy) in foot for dx, dy in DIRS):
            continue
        cands.append((abs(c[0] - near[0]) + abs(c[1] - near[1]), c))
    for _, c in sorted(cands):
        if keeps_connected(floor, blocked | {c}):
            return c
    return None


# ------------------------------------------------------------------- mazes --

def maze_placements(floor, cls, door=None):
    """Where a maze of this class fits: interior w x h on plain ground, its
    ring either wall or rock-able floor (`passable`, not walkability:
    shallow water, ice and swamp are walked through, and the ROM's flood,
    QuickStartBlocksMazeOpen, counts every collision-free tile as open - a
    Minish cave maze on a shallow-water edge was solved the moment it was
    dealt). `door` (x, y): an overworld door in the back border instead of
    a chest."""
    name, w, h, nmove, nfix, minpush = cls
    out = []
    for y0 in range(2, floor.th - h - 1):
        for x0 in range(2, floor.tw - w - 1):
            inner = {(x0 + i, y0 + j) for i in range(w) for j in range(h)}
            if not (inner <= floor.comp and inner <= floor.ground):
                continue
            ring = {(x0 + i, y0 + j) for i in range(-1, w + 1) for j in range(-1, h + 1)} - inner
            if any(c in floor.passable and c not in floor.ground and c != door for c in ring):
                continue
            if door is not None and not (y0 - 1 == door[1] and x0 <= door[0] < x0 + w):
                continue
            border = {c for c in ring if c in floor.comp}
            if door is not None:
                border.discard(door)
            out.append((x0, y0, inner, ring, border))
    return out


def maze_frames(floor, cls, rng, max_rocks, door=None, limit=FRAMES):
    """Up to `limit` maze placements of one class, each with its pool: the
    grid, its ring walls, the way in, the chest (or door) and the switch
    are the frame; the carved walls inside and the rocks are the content."""
    name, w, h, nmove, nfix, minpush = cls
    places = maze_placements(floor, cls, door)
    places.sort(key=lambda p: len(p[4]) + rng.random() * 2)
    out, used = [], []
    for (x0, y0, inner, ring, border) in places[:40]:
        if len(out) >= limit:
            break
        if any(abs(x0 - ux) < 2 and abs(y0 - uy) < 2 for ux, uy in used):
            continue
        if door is None:
            cx = rng.randrange(x0, x0 + w)
            chest, target = (cx, y0), (cx, y0 + 1)
        else:
            chest, target = None, (door[0], y0)
        # the way in: a border cell on the bottom, left or right whose
        # outside neighbour is in the arrival component
        gates = []
        for c in sorted(border):
            for dx, dy in DIRS:
                o = (c[0] + dx, c[1] + dy)
                i = (c[0] - dx, c[1] - dy)
                if o in floor.comp and o not in inner and o not in ring and i in inner and c[1] >= y0:
                    gates.append((c, i))
        if not gates:
            WHY['no gates'] += 1
            continue
        gate, gate_in = rng.choice(gates)
        wall = border - {gate}
        if len(wall) + nmove > max_rocks:
            continue
        chests = {chest} if chest else set()
        # the whole interior counted blocked: no carve can cut the room
        if not keeps_connected(floor, wall | chests | inner):
            WHY['cuts room'] += 1
            continue
        # The switch away from the way in: placed nearest the gate (as the
        # first build did) it often stood on the very tile in front of it,
        # and a player who walks - the probe sets the player down - could
        # not get in.
        gate_out = {(gate[0] + dx, gate[1] + dy) for dx, dy in DIRS} - inner - ring
        sw = switch_spot(floor, inner | ring, wall | chests | inner | gate_out, (x0 + w, y0 - 1))
        if sw is None:
            continue
        base = (window(floor, inner | ring, 3) | inner | {gate}) - wall - chests - {sw}
        outside = [c for c in base if c not in inner and c not in ring]
        if not outside:
            continue
        entry = min(outside, key=lambda c: abs(c[0] - gate[0]) + abs(c[1] - gate[1]))
        # The switch must not stand in the way in.
        if gate not in flood(base - inner, entry):
            WHY['switch in the way'] += 1
            continue
        frame = dict(kind=KIND_MAZE, cls=name, board=(x0, y0, w, h), ref=None, fixed=sorted(wall),
                     prize=chest if chest else door, switch=sw, target=target,
                     door=1 if door else 0, entry=entry, gate=gate, gate_in=gate_in)
        contents = maze_contents(floor, cls, rng, frame, inner, base, max_rocks)
        if len(contents) >= (MIN_DOOR_CONTENTS if door else MIN_CONTENTS):
            frame['contents'] = contents
            out.append(frame)
            used.append((x0, y0))
    return out


def maze_contents(floor, cls, rng, frame, inner, base, max_rocks):
    """Up to CONTENTS distinct carves and rock starts for one maze frame.
    Carve the open interior as a corridor grown from the way in, branching
    into pockets (where rocks can be parked and walked round) until it
    reaches the target and covers about `nfix` percent; everything not
    carved is wall. Park the rocks off the way, then search backwards for
    arrangements that seal the target, and prove each one's fewest pushes
    forward. At most two starts per carve, for spread."""
    name, w, h, nmove, nfix, minpush = cls
    chest = tuple(frame['prize']) if not frame['door'] else None
    target = tuple(frame['target'])
    gate_in = tuple(frame['gate_in'])
    entry = tuple(frame['entry'])
    wall = set(map(tuple, frame['fixed']))
    need = max(len(inner) * nfix // 100, 4)
    out, seen = [], set()
    for attempt in range(CONTENTS * MAZE_TRIES):
        if len(out) >= CONTENTS:
            break
        carved = {gate_in}
        grow_ok = False
        for _ in range(len(inner) * 8):
            c = rng.choice(sorted(carved))
            nbrs = [(c[0] + dx, c[1] + dy) for dx, dy in DIRS]
            nbrs = [nb for nb in nbrs if nb in inner and nb not in carved and nb != chest]
            if not nbrs:
                continue
            nb = rng.choice(nbrs)
            # no open 2x2 squares: a plaza gives every rock a way round
            square = any(all((nb[0] + ax, nb[1] + ay) in carved | {nb} for ax in (0, sx) for ay in (0, sy))
                         for sx in (-1, 1) for sy in (-1, 1))
            if square and rng.random() < 0.8:
                continue
            carved.add(nb)
            if target in carved and len(carved) >= need:
                grow_ok = True
                break
        if not grow_ok:
            WHY['carve'] += 1
            continue
        fixed_in = inner - carved - ({chest} if chest else set())
        if len(wall) + len(fixed_in) + nmove > max_rocks:
            WHY['too many rocks'] += 1
            continue
        walk = base - fixed_in
        board = inner - fixed_in - {target} - ({chest} if chest else set())
        spots = sorted(board - {gate_in})
        if len(spots) < nmove:
            continue
        classes = [rng.choice((ANY, ANY, HORIZ, VERT)) for _ in range(nmove)]
        puz = Puzzle(walk, board, classes)
        tb = 1 << puz.bit(target)
        # Solved arrangement: rocks parked off the way in, the target still
        # reachable; then pull them into the way.
        # Random parking, retried. (Greedy parking - a rock at a time where
        # the target stays reachable - always succeeds but tucks the rocks
        # into the pockets beside the corridor, one pull from sealing it:
        # nearly every maze it made took one or two pushes.)
        parked = None
        for _ in range(12):
            p = rng.sample(spots, nmove)
            if puz.region(puz.mask(p), puz.bit(entry)) & tb:
                parked = p
                break
        if parked is None:
            WHY['parked blocks'] += 1
            continue
        starts = reverse_search(puz, parked, entry, lambda occ, region, tb=tb: not (region & tb))
        took = 0
        for start in starts[:8]:
            if took >= 2 or len(out) >= CONTENTS:
                break
            key = (frozenset(fixed_in), tuple(sorted(zip(start, classes))))
            if key in seen:
                continue
            seen.add(key)
            n, path = puz.solve(start, entry, lambda occ, region, tb=tb: bool(region & tb), cap=SEARCH_CAP)
            if n is None or n < minpush:
                WHY['n=%s' % n] += 1
                continue
            out.append(dict(move=[(m[0], m[1], c) for m, c in zip(start, classes)],
                            walls=sorted(fixed_in), pushes=n, solution=path))
            took += 1
    return out


# ------------------------------------------------------------------ driver --

def owners(rooms):
    for key, r in sorted(rooms.items(), key=lambda kv: (kv[0].split(':')[0], int(kv[0].split(':')[1]))):
        yield key, r


def doors_of(floor):
    """Overworld doors into a ? room site: their tile and that the tile
    below is open floor (a north-wall door the maze can stand in front of)."""
    import sim
    site_rooms = {s['roomName'] for s in sim.SITES if s['gate'] == 0}
    out = []
    for row in X.BY_ROOM.get(floor.r['room'], []):
        if row[0] != 'WARP_TYPE_AREA' or row[7] not in site_rooms:
            continue
        t = (row[1] // 16, row[2] // 16)
        front = (t[0], t[1] + 1)
        if front in floor.comp:
            out.append(t)
    return out


def owner_job(job):
    """One room's frames. Its own random stream, keyed by (seed, owner), so
    the result does not depend on which process ran it or in what order."""
    seed, key, r = job
    rng = random.Random('%d:%s' % (seed, key))
    floor = Floor(r)
    site = r.get('site')
    cap = MAX_ROCKS_SITE if site is not None else MAX_ROCKS_ROW
    frames = template_frames(floor, rng, cap, site is not None)
    if r.get('row') is not None:
        for door in doors_of(floor):
            for cls in reversed(MAZE_CLASSES):
                got = maze_frames(floor, cls, rng, cap, door=door, limit=1)
                if got:
                    frames += got
                    break
    chests = []
    for cls in reversed(MAZE_CLASSES):
        if len(chests) >= FRAMES:
            break
        chests += maze_frames(floor, cls, rng, cap, limit=FRAMES - len(chests))
    frames += chests
    for f in frames:
        f.update(owner=key, area=r['area'], room=r['room'])
    return key, r['room'], frames


def tag(f):
    return ('T' if f['kind'] == KIND_TEMPLATE else ('D' if f['door'] else 'M')) + f['cls']


def generate(seed, procs=4):
    import multiprocessing
    rooms = json.load(open(ROOMS))
    jobs = [(seed, key, r) for key, r in owners(rooms)]
    out = []
    with multiprocessing.Pool(procs) as pool:
        for key, room, frames in pool.imap(owner_job, jobs):
            out += frames
            print('%-9s %-46s %s' % (key, room[5:], ' '.join('%s:%d' % (tag(f), len(f['contents'])) for f in frames) or '-'),
                  flush=True)
    return out


# ------------------------------------------------------------ the table --
#
# A frame's fixed rocks (the posts, or a maze's ring) are (x, y) pairs. A
# content is `stride` bytes: one per mover, x - bx in bits 0-2, y - by in
# bits 3-5, the class in bits 6-7; then a template's goal cells the same
# way (the reference shows them at the same offsets from rx, ry), or a
# maze's interior walls as a 32-bit mask, bit (y - by) * bw + (x - bx).

def pack(bx, by, x, y, c=0):
    assert 0 <= x - bx < 8 and 0 <= y - by < 8
    return (x - bx) | ((y - by) << 3) | (c << 6)


def records(f):
    bx, by, bw, bh = f['board']
    out = []
    for c in f['contents']:
        rec = [pack(bx, by, x, y, k) for x, y, k in c['move']]
        if f['kind'] == KIND_TEMPLATE:
            rec += [pack(bx, by, x, y) for x, y in c['goal']]
        else:
            m = 0
            for x, y in c['walls']:
                m |= 1 << ((y - by) * bw + (x - bx))
            rec += [m & 0xff, (m >> 8) & 0xff, (m >> 16) & 0xff, (m >> 24) & 0xff]
        out.append(rec)
    return out


def emit(frames):
    lines = ['// GENERATED by tools/quickstart/block_puzzles.py - do not edit.',
             '// Block puzzles: docs/QUICKSTART_BLOCK_PUZZLES.md. Room tiles, room-local.',
             '#ifndef QUICKSTART_BLOCK_PUZZLES_H', '#define QUICKSTART_BLOCK_PUZZLES_H', '']
    rows = []
    for n, f in enumerate(frames):
        recs = records(f)
        stride = len(recs[0])
        assert all(len(r) == stride for r in recs) and len(recs) <= CONTENTS
        lines.append('static const u8 sQuickStartBlockFixed%d[] = { %s };'
                     % (n, ', '.join('%d, %d' % tuple(c) for c in f['fixed'])))
        lines.append('static const u8 sQuickStartBlockContents%d[] = { %s };'
                     % (n, ', '.join(str(v) for r in recs for v in r)))
        own = f['owner']
        site = int(own.split(':')[1]) if own.startswith('site') else 0xFF
        row = int(own.split(':')[1]) if own.startswith('row') else 0xFF
        bx, by, bw, bh = f['board']
        tx, ty = f['target'] if f['target'] else (0xFF, 0xFF)
        rx, ry = f['ref'] if f['ref'] else (0xFF, 0xFF)
        pushes = [c['pushes'] for c in f['contents']]
        rows.append('    { %s, %s, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, '
                    'sQuickStartBlockFixed%d, sQuickStartBlockContents%d }, // %s %s x%d, %d-%d pushes'
                    % (f['area'], f['room'], f['kind'], f['door'], site, row, bx, by, bw, bh,
                       f['prize'][0], f['prize'][1], tx, ty, f['switch'][0], f['switch'][1], rx, ry,
                       len(f['contents'][0]['move']), len(f['fixed']), len(recs), stride, n, n,
                       own, tag(f), len(recs), min(pushes), max(pushes)))
    lines += ['', 'static const QuickStartBlockFrame sQuickStartBlockFrames[] = {'] + rows + ['};', '',
              '#endif', '']
    return '\n'.join(lines)


# ---------------------------------------------------------- verification --

def frame_space(floor, f, c):
    """(walk, board, entry, done) for content c of frame f, exactly as the
    generator built them: what the player may stand on, where a mover may
    go, where the player comes in, and the solved test."""
    bx, by, bw, bh = f['board']
    sw = tuple(f['switch'])
    fixed = set(map(tuple, f['fixed']))
    if f['kind'] == KIND_TEMPLATE:
        rx, ry = f['ref']
        side = bw
        r_in, _r_ring, r_posts = frame_cells(rx, ry, side)
        b_in, b_ring, _b_posts = frame_cells(bx, by, side)
        ref = {(rx + x - bx, ry + y - by) for x, y in c['goal']}
        walk = window(floor, r_in | r_posts | b_in | b_ring) - fixed - {sw} - ref
        goal = set(map(tuple, c['goal']))
        return walk, b_in, tuple(f['entry']), lambda puz, occ, region: occ == puz.mask(goal)
    inner = {(bx + i, by + j) for i in range(bw) for j in range(bh)}
    ring = {(bx + i, by + j) for i in range(-1, bw + 1) for j in range(-1, bh + 1)} - inner
    chests = {tuple(f['prize'])} if not f['door'] else set()
    walls = set(map(tuple, c['walls']))
    target = tuple(f['target'])
    walk = (window(floor, inner | ring, 3) | inner | {tuple(f['gate'])}) - fixed - chests - {sw} - walls
    board = inner - walls - {target} - chests
    return walk, board, tuple(f['entry']), lambda puz, occ, region: bool((region >> puz.bit(target)) & 1)


def replay(walk, board, classes, start, entry, path, done):
    """Play `path` push by push under the game's rules (player can reach
    the far side, the rock may move that way, the next tile is board and
    free). None if every push is legal and the end is solved, else why."""
    puz = Puzzle(walk, board, classes)
    rocks = [puz.bit(s) for s in start]
    occ = sum(1 << r for r in rocks)
    region = puz.region(occ, puz.bit(entry))
    if done(puz, occ, region):
        return 'solved at the start'
    for n, (x, y, d) in enumerate(path):
        b = puz.bit((x, y))
        if b not in rocks:
            return 'push %d: no rock at (%d,%d)' % (n + 1, x, y)
        i = rocks.index(b)
        if d not in ALLOW[classes[i]]:
            return 'push %d: rock (%d,%d) may not move dir %d' % (n + 1, x, y, d)
        st = puz.steps[d]
        if not (region >> (b - st)) & 1:
            return 'push %d: far side of (%d,%d) out of reach' % (n + 1, x, y)
        dest = b + st
        if not (puz.board >> dest) & 1 or (occ >> dest) & 1:
            return 'push %d: (%d,%d) cannot move dir %d' % (n + 1, x, y, d)
        rocks[i] = dest
        occ = (occ & ~(1 << b)) | (1 << dest)
        region = puz.flood(1 << b, puz.walk & ~occ)
        if n < len(path) - 1 and done(puz, occ, region):
            # the game acts on the first solved state (a template locks)
            return 'solved early, at push %d of %d' % (n + 1, len(path))
    return None if done(puz, occ, region) else 'not solved after %d pushes' % len(path)


def parse_header(text):
    arrays = {(m.group(1), int(m.group(2))): [int(v) for v in m.group(3).split(',') if v.strip()]
              for m in re.finditer(r'static const u8 sQuickStartBlock(Fixed|Contents)(\d+)\[\] = \{ ?(.*?) ?\};', text)}
    frames = []
    for m in re.finditer(r'\{ (AREA_\w+), (ROOM_\w+), ([\d, ]+), sQuickStartBlockFixed(\d+), sQuickStartBlockContents(\d+) \}', text):
        v = [int(x) for x in m.group(3).split(',') if x.strip()]
        keys = ('kind', 'door', 'site', 'row', 'bx', 'by', 'bw', 'bh', 'px', 'py', 'tx', 'ty', 'sx', 'sy',
                'rx', 'ry', 'nMove', 'nFixed', 'nContent', 'stride')
        f = dict(zip(keys, v), area=m.group(1), room=m.group(2))
        f['fixed'] = arrays[('Fixed', int(m.group(4)))]
        f['contents'] = arrays[('Contents', int(m.group(5)))]
        frames.append(f)
    return frames


def decode(h, k):
    """Content k of header frame h, the way game.c reads it."""
    rec = h['contents'][k * h['stride']:(k + 1) * h['stride']]
    n = h['nMove']
    move = [(h['bx'] + (b & 7), h['by'] + ((b >> 3) & 7), b >> 6) for b in rec[:n]]
    if h['kind'] == KIND_TEMPLATE:
        return dict(move=move, goal=sorted((h['bx'] + (b & 7), h['by'] + ((b >> 3) & 7)) for b in rec[n:]))
    m = rec[n] | (rec[n + 1] << 8) | (rec[n + 2] << 16) | (rec[n + 3] << 24)
    return dict(move=move, walls=sorted((h['bx'] + i % h['bw'], h['by'] + i // h['bw'])
                                        for i in range(h['bw'] * h['bh']) if (m >> i) & 1))


def verify(sol=OUT_SOL, appended=False):
    """The shipped table, decoded the way game.c decodes it, against the
    solutions file; every content's solution replayed under the game's
    rules on the room's captured floor; no rock, switch or prize on a
    reserved tile; and the entity budget. `appended`: only the header's
    last frames, against an --append run's own solutions file."""
    rooms = json.load(open(ROOMS))
    header = parse_header(open(OUT_H).read())
    frames = json.load(open(sol))
    if appended:
        header = header[len(header) - len(frames):]
    bad = []
    if len(header) != len(frames):
        print('header has %d frames, solutions %d' % (len(header), len(frames)))
        return 1
    total = 0
    for n, (h, f) in enumerate(zip(header, frames)):
        floor = Floor(rooms[f['owner']])
        cap = MAX_ROCKS_SITE if f['owner'].startswith('site') else MAX_ROCKS_ROW
        if h['nContent'] != len(f['contents']):
            bad.append('frame %d: %d contents in the header, %d solved' % (n, h['nContent'], len(f['contents'])))
            continue
        for spot in [tuple(f['switch']), tuple(f['prize'])] + [tuple(c) for c in f['fixed']]:
            if spot in floor.reserved and not (f['door'] and spot == tuple(f['prize'])):
                bad.append('frame %d: (%d,%d) is a reserved tile' % (n, spot[0], spot[1]))
        for k, c in enumerate(f['contents']):
            total += 1
            d = decode(h, k)
            if d['move'] != [tuple(m) for m in c['move']] or \
                    d.get('goal', d.get('walls')) != [tuple(g) for g in c.get('goal', c.get('walls'))]:
                bad.append('frame %d content %d: decodes differently' % (n, k))
                continue
            rocks = len(f['fixed']) + len(c['move']) + len(c.get('goal', c.get('walls')))
            if rocks > cap:
                bad.append('frame %d content %d: %d rocks' % (n, k, rocks))
            walk, board, entry, done = frame_space(floor, f, c)
            why = replay(walk, board, [m[2] for m in c['move']], [tuple(m[:2]) for m in c['move']],
                         entry, c['solution'], done)
            if why:
                bad.append('frame %d content %d: %s' % (n, k, why))
    print('%d contents in %d frames: %d problems' % (total, len(frames), len(bad)))
    for b in bad[:20]:
        print('  ' + b)
    return 1 if bad else 0


def append(keys, seed):
    """Generate frames for `keys` (owners not in the shipped header) only, and
    append them after its last frame, leaving every shipped frame byte for
    byte. Hyrule Castle (Oct 2026) went in this way: the captures the shipped
    header was built from are not in this checkout (build/ is not kept), and a
    fresh capture of an untouched room no longer reproduces it exactly, so a
    full regeneration would have reshuffled every room's puzzles for nothing.
    The new frames' solutions go to build/block_solutions_append.json."""
    rooms = json.load(open(ROOMS))
    old = open(OUT_H).read()
    shipped = {m.group(1) for m in re.finditer(r'// ((?:site|row):\d+) ', old)}
    clash = sorted(set(keys) & shipped)
    if clash:
        raise SystemExit('already in the header: %s' % clash)
    base = max(int(n) for n in re.findall(r'sQuickStartBlockFixed(\d+)\[\]', old)) + 1
    frames = []
    for key in keys:
        _k, room, got = owner_job((seed, key, rooms[key]))
        frames += got
        print('%-9s %-46s %s' % (key, room[5:], ' '.join('%s:%d' % (tag(f), len(f['contents'])) for f in got) or '-'))
    if not frames:
        print('no frames for %s' % keys)
        return 0
    body = emit(frames)
    arrays = [l for l in body.split('\n') if l.startswith('static const u8 ')]
    rows = [l for l in body.split('\n') if l.startswith('    { AREA_')]
    renum = lambda l: re.sub(r'(sQuickStartBlock(?:Fixed|Contents))(\d+)', lambda m: '%s%d' % (m.group(1), int(m.group(2)) + base), l)
    arrays, rows = [renum(l) for l in arrays], [renum(l) for l in rows]
    head, tail = old.split('\nstatic const QuickStartBlockFrame sQuickStartBlockFrames[] = {\n')
    table, rest = tail.split('\n};\n', 1)
    text = head + '\n' + '\n'.join(arrays) + '\n\nstatic const QuickStartBlockFrame sQuickStartBlockFrames[] = {\n' + \
        table + '\n' + '\n'.join(rows) + '\n};\n' + rest
    open(OUT_H, 'w').write(text)
    with open(os.path.join(os.path.dirname(OUT_SOL), 'block_solutions_append.json'), 'w') as f:
        json.dump(frames, f)
    print('%d frames appended at %d -> %s' % (len(frames), base, OUT_H))
    return 0


def main():
    if '--verify' in sys.argv:
        return verify()
    if '--verify-append' in sys.argv:
        return verify(os.path.join(os.path.dirname(OUT_SOL), 'block_solutions_append.json'), appended=True)
    if '--append' in sys.argv:
        return append(sys.argv[sys.argv.index('--append') + 1].split(','),
                      int(sys.argv[sys.argv.index('--seed') + 1]) if '--seed' in sys.argv else 0xB10C)
    seed = int(sys.argv[sys.argv.index('--seed') + 1]) if '--seed' in sys.argv else 0xB10C
    frames = generate(seed)
    text = emit(frames)
    if '--check' in sys.argv:
        old = open(OUT_H).read() if os.path.exists(OUT_H) else ''
        print('up to date' if old == text else 'STALE')
        return 0 if old == text else 1
    open(OUT_H, 'w').write(text)
    with open(OUT_SOL, 'w') as f:
        json.dump(frames, f)
    kinds = collections.Counter(tag(f) for f in frames)
    contents = collections.Counter()
    for f in frames:
        contents[tag(f)] += len(f['contents'])
    print('%d frames %s, %d contents %s -> %s' % (len(frames), dict(kinds), sum(contents.values()),
                                                  dict(contents), OUT_H))
    return 0


if __name__ == '__main__':
    sys.exit(main())
