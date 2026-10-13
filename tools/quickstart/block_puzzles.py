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
"""
import collections
import json
import os
import random
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
PER_OWNER = 3            # instances per owner per kind
SEARCH_CAP = 60000
WHY = collections.Counter()   # why candidates were dropped, for tuning       # BFS states before a template's minimum is called "at least the scramble"


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


def make_template(floor, cls, rng, max_rocks):
    name, side, nrocks, nlimited, (lo, hi), minpush = cls
    if 2 * nrocks + 8 > max_rocks:
        return None
    for (rx, ry, bx, by) in template_layouts(floor, side, rng)[:60]:
        r_in, r_ring, r_posts = frame_cells(rx, ry, side)
        b_in, b_ring, b_posts = frame_cells(bx, by, side)
        foot = r_in | r_posts | b_in | b_ring
        best = None
        for attempt in range(10):
            goal_rel = rng.sample([(i, j) for i in range(side) for j in range(side)], nrocks)
            goal = [(bx + i, by + j) for i, j in goal_rel]
            ref = [(rx + i, ry + j) for i, j in goal_rel]
            fixed = set(ref) | r_posts | b_posts
            # The reference cells and the posts block for good, the board
            # cells may: none of that may cut the room.
            if not keeps_connected(floor, fixed | b_in):
                break
            walk = window(floor, foot) - fixed
            classes = [ANY] * nrocks
            for k in rng.sample(range(nrocks), nlimited):
                classes[k] = rng.choice((HORIZ, VERT))
            puz = Puzzle(walk, b_in, classes)
            outside = [c for c in b_ring if c not in b_posts and c in walk]
            if not outside:
                break
            # The player comes from the arrival: enter the search from the
            # ring tile nearest it, so a ring segment walled off from the
            # room is never assumed reachable.
            dist = bfs_dist(floor.comp - fixed - b_in, floor.start)
            outside = [c for c in outside if c in dist]
            if not outside:
                break
            near_entry = min(outside, key=lambda c: dist[c])
            goalset = frozenset(goal)
            for _ in range(4):
                start, _p, pulls = scramble(puz, goal, near_entry, rng.randint(lo, hi), rng)
                if sum(1 for st in start if st not in goalset) < max(2, (nrocks + 1) // 2):
                    continue
                entry = near_entry
                gm = puz.mask(goal)
                n, path = puz.solve(start, entry, lambda occ, region, gm=gm: occ == gm)
                if path is None:
                    # No minimum proved inside the cap: the scramble undone.
                    path = [(c[0], c[1], d) for c, d in reversed(pulls)]
                score = n if n is not None else hi
                if best is None or score > best[0]:
                    best = (score, n, path, start, classes, goal, fixed)
            if best and best[0] >= minpush + 2:
                break
        if best is None or best[0] < minpush:
            continue
        score, n, path, start, classes, goal, fixed = best
        spot = prize_spot(floor, foot, fixed | b_in, (bx + side // 2, by + side // 2))
        sw = switch_spot(floor, foot, fixed | b_in, (bx - 1, by + side))
        if spot is None or sw is None or sw == spot:
            continue
        if not keeps_connected(floor, fixed | b_in | {sw}):
            continue
        return dict(kind=KIND_TEMPLATE, cls=name, board=(bx, by, side, side), ref=(rx, ry),
                    move=[(st[0], st[1], c) for st, c in zip(start, classes)],
                    fixed=sorted(fixed), goal=sorted(goal), prize=spot, switch=sw,
                    target=None, door=0, pushes=(n if n is not None else -1),
                    bound=score, solution=path)
    return None


def prize_spot(floor, foot, blocked, near):
    best = None
    for c in floor.comp - foot - blocked - floor.reserved:
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
    for c in floor.comp - foot - blocked - floor.reserved:
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

def make_maze(floor, cls, rng, max_rocks, door=None):
    """A maze: interior w x h, a border ring (rock where the floor is open,
    nothing where it is wall), one entrance gap, a chest at the back with
    the target cell in front of it, fixed and movable rocks inside.

    `door` (x, y): an overworld door the maze guards instead of a chest -
    the door tile sits in the back border and the target is in front of it."""
    name, w, h, nmove, nfix, minpush = cls
    placements = []
    for y0 in range(2, floor.th - h - 1):
        for x0 in range(2, floor.tw - w - 1):
            inner = {(x0 + i, y0 + j) for i in range(w) for j in range(h)}
            if not (inner <= floor.comp and inner <= floor.ground):
                continue
            ring = {(x0 + i, y0 + j) for i in range(-1, w + 1) for j in range(-1, h + 1)} - inner
            # a ring cell is either wall (nothing to place) or floor a rock
            # can stand on. "Wall" is collision, not walkability: shallow
            # water, ice and swamp are walked through, and the ROM's own
            # flood (QuickStartBlocksMazeOpen) counts every collision-free
            # tile as open. A Minish cave maze sat on a shallow-water edge
            # and was solved the moment it was dealt.
            if any(c in floor.passable and c not in floor.ground and c != door for c in ring):
                continue
            if door is not None:
                # the door in the top border, its front tile the target
                dx, dy = door
                if not (y0 - 1 == dy and x0 <= dx < x0 + w):
                    continue
                target, chest = (dx, y0), None
            else:
                target = None
                chest = None
            rocks = {c for c in ring if c in floor.comp}
            if door is not None:
                rocks.discard(door)
            placements.append((x0, y0, inner, ring, rocks, target, chest))
    if not placements:
        return None
    placements.sort(key=lambda p: len(p[4]) + rng.random() * 2)
    for (x0, y0, inner, ring, border, target, chest) in placements[:30]:
        if door is None:
            cxs = list(range(x0, x0 + w))
            rng.shuffle(cxs)
            for cx in cxs:
                chest, target = (cx, y0), (cx, y0 + 1)
                break
        # entrance: a border cell on the bottom/left/right side whose outside
        # neighbour is in the arrival component
        gates = []
        for c in border:
            for dx, dy in DIRS:
                o = (c[0] + dx, c[1] + dy)
                i = (c[0] - dx, c[1] - dy)
                if o in floor.comp and o not in inner and o not in ring and i in inner and c[1] >= y0:
                    gates.append(c)
        if not gates:
            WHY['no gates'] += 1
            continue
        best = None
        for attempt in range(25):
            gate = rng.choice(gates)
            wall = set(border) - {gate}
            if len(wall) + nmove > max_rocks:
                break
            # Interior walls: a random handful that leave the open interior
            # in one piece with the gate and the target in it.
            gate_in = next(((gate[0] - dx, gate[1] - dy) for dx, dy in DIRS
                            if (gate[0] - dx, gate[1] - dy) in inner), None)
            if gate_in is None:
                WHY['no gate_in'] += 1
                continue
            # Carve the open interior as a corridor grown from the way in,
            # branching into a few pockets (where rocks can be parked and
            # walked round), until it reaches the target and covers about
            # `nfix` percent of the interior. Everything not carved is wall.
            carved = {gate_in}
            need = max(len(inner) * nfix // 100, 4)
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
            fixed = wall | fixed_in
            if len(fixed) + nmove > max_rocks:
                WHY['too many rocks'] += 1
                continue
            blocked = fixed | ({chest} if chest else set())
            if not keeps_connected(floor, blocked | inner):
                WHY['cuts room'] += 1
                continue
            walk = (window(floor, inner | ring, 3) | inner | {gate}) - blocked
            board = inner - fixed_in - {target} - ({chest} if chest else set())
            outside = [c for c in walk if c not in inner and c not in ring]
            if not outside:
                continue
            entry = min(outside, key=lambda c: abs(c[0] - gate[0]) + abs(c[1] - gate[1]))
            # Solved arrangement: rocks parked on interior cells off the way
            # in, the target still reachable. Then pull them into the way.
            for park_try in range(12):
                classes = [rng.choice((ANY, ANY, HORIZ, VERT)) for _ in range(nmove)]
                spots = sorted(board - {gate_in})
                if len(spots) < nmove:
                    break
                parked = rng.sample(spots, nmove)
                puz = Puzzle(walk, board, classes)
                occ = puz.mask(parked)
                tb = 1 << puz.bit(target)
                if not puz.region(occ, puz.bit(entry)) & tb:
                    WHY['parked blocks'] += 1
                    continue
                starts = reverse_search(puz, parked, entry, lambda occ, region, tb=tb: not (region & tb))
                if not starts:
                    WHY['never sealed'] += 1
                    continue
                found = None
                for start in starts[:6]:
                    n, path = puz.solve(start, entry, lambda occ, region, tb=tb: bool(region & tb), cap=SEARCH_CAP)
                    if n is not None and (found is None or n > found[0]):
                        found = (n, path, start)
                if found is None or found[0] < minpush or (best is not None and found[0] <= best[0]):
                    WHY['n=%s' % (found and found[0])] += 1
                    continue
                n, path, start = found
                sw = switch_spot(floor, inner | ring, blocked, gate)
                if sw is None:
                    continue
                best = (n, dict(kind=KIND_MAZE, cls=name, board=(x0, y0, w, h),
                                move=[(m[0], m[1], c) for m, c in zip(start, classes)],
                                fixed=sorted(fixed), goal=[], prize=chest if chest else door,
                                switch=sw, target=target, door=1 if door else 0,
                                pushes=n, bound=n, solution=path))
            if best is not None and best[0] >= minpush + 3:
                break
        if best is not None:
            return best[1]
    return None


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


def generate(seed):
    rooms = json.load(open(ROOMS))
    rng = random.Random(seed)
    out = []
    for key, r in owners(rooms):
        floor = Floor(r)
        site = r.get('site')
        row = r.get('row')
        cap = MAX_ROCKS_SITE if site is not None else MAX_ROCKS_ROW
        made = []
        for cls in reversed(TEMPLATE_CLASSES):
            if site is not None and cls[0] in ('XL',):
                continue
            for k in range(PER_OWNER):
                inst = make_template(floor, cls, rng, cap)
                if inst:
                    made.append(inst)
            if sum(1 for m in made if m['kind'] == KIND_TEMPLATE) >= PER_OWNER:
                break
        mazes = 0
        if row is not None:
            for door in doors_of(floor):
                for cls in reversed(MAZE_CLASSES):
                    inst = make_maze(floor, cls, rng, cap, door=door)
                    if inst:
                        made.append(inst)
                        mazes += 1
                        break
        for cls in reversed(MAZE_CLASSES):
            for k in range(PER_OWNER):
                if mazes >= PER_OWNER:
                    break
                inst = make_maze(floor, cls, rng, cap)
                if inst:
                    made.append(inst)
                    mazes += 1
        for m in made:
            m.update(owner=key, area=r['area'], room=r['room'])
        out += made
        print('%-9s %-46s %s' % (key, r['room'][5:], ' '.join('%s%s%s' % ('T' if m['kind'] == 0 else ('D' if m['door'] else 'M'), m['cls'], m['pushes']) for m in made) or '-'))
    return out


def emit(insts):
    lines = ['// GENERATED by tools/quickstart/block_puzzles.py - do not edit.',
             '// Block puzzles: docs/QUICKSTART_BLOCK_PUZZLES.md. Room tiles, room-local.',
             '#ifndef QUICKSTART_BLOCK_PUZZLES_H', '#define QUICKSTART_BLOCK_PUZZLES_H', '']
    data, rows = [], []
    for n, m in enumerate(insts):
        cells = []
        for x, y, c in m['move']:
            cells += [x, y, c]
        for x, y in m['fixed']:
            cells += [x, y]
        for x, y in m['goal']:
            cells += [x, y]
        data.append('static const u8 sQuickStartBlockCells%d[] = { %s };' % (n, ', '.join(str(v) for v in cells)))
        own = m['owner']
        site = int(own.split(':')[1]) if own.startswith('site') else 0xFF
        row = int(own.split(':')[1]) if own.startswith('row') else 0xFF
        bx, by, bw, bh = m['board']
        tx, ty = m['target'] if m['target'] else (0xFF, 0xFF)
        rows.append('    { %s, %s, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, sQuickStartBlockCells%d }, // %s %s%s %d'
                    % (m['area'], m['room'], m['kind'], m['door'], site, row, bx, by, bw, bh,
                       m['prize'][0], m['prize'][1], tx, ty, m['switch'][0], m['switch'][1],
                       len(m['move']), len(m['fixed']), len(m['goal']), n,
                       own, 'T' if m['kind'] == 0 else 'M', m['cls'], m['pushes']))
    lines += data
    lines += ['', 'static const QuickStartBlockPuzzle sQuickStartBlockPuzzles[] = {'] + rows + ['};', '',
              '#endif', '']
    return '\n'.join(lines)


def main():
    seed = int(sys.argv[sys.argv.index('--seed') + 1]) if '--seed' in sys.argv else 0xB10C
    insts = generate(seed)
    text = emit(insts)
    if '--check' in sys.argv:
        old = open(OUT_H).read() if os.path.exists(OUT_H) else ''
        print('up to date' if old == text else 'STALE')
        return 0 if old == text else 1
    open(OUT_H, 'w').write(text)
    with open(OUT_SOL, 'w') as f:
        json.dump(insts, f)
    kinds = collections.Counter(('T' if m['kind'] == 0 else ('D' if m['door'] else 'M')) + m['cls'] for m in insts)
    print('%d instances %s -> %s' % (len(insts), dict(kinds), OUT_H))
    return 0


if __name__ == '__main__':
    sys.exit(main())
