"""Generate the C reachability table from the walked survey.

world_reach.py is the single source of truth for "what does it cost to reach
this place"; this turns it into a table game.c can consult at run time, so the
win chain can only ever place a step somewhere the player can actually get to.

    python3 tools/quickstart/gen_reach.py          # write include/quickstart/reach.h
    python3 tools/quickstart/gen_reach.py --check  # fail if the file is stale

THE GRAPH (Oct 2026). Every survey key is a NODE: a region's own start (where
the ring's drop lands), or one of its ENTRANCES (world_reach.ENTRANCES - the
same region priced from where a particular border puts the player). Rooms
hang off nodes: a destination row is (node, room, cost from that node).
Nodes are joined by EDGES: a LINKS row says which node an exit row lands at
and the exit row's cost prices the edge; sibling entrances of one region are
joined by the row each has at the other's landing spot; and every ring
adjacency the survey does not spell out keeps the old reading - any node of
the one region reaches the other's own start at that region's entry price.
The game floods this graph from the drop's node with what the player holds,
and a room is offerable when some reached node has a satisfied row for it.
That is what lets Lon Lon Ranch cost one thing from its south border and
another from the lake, and what keeps a wave out of Trilby's boulder pocket
until the boulder is in.

WHAT SURVIVES THE TRIP. Requirements are DNF - a list of alternative terms,
each a set of tokens that must all hold - and that maps onto a u32 bitmask per
term with no loss. What does NOT survive is any token the game cannot TEST at
run time: being Minish is a state rather than an item (but see expand_minish),
and "the maze is solved" / "four switches are thrown" have no save-flag this
file can point at. Those tokens are emitted anyway, and simply never appear in
the held-mask the game builds, so any term containing one is permanently
false. A destination that needs one is invisible to the chain placer rather
than wrongly offered to it - the conservative direction, because the cost of
being wrong is an unwinnable run.

BOULDERS ARE TESTABLE NOW. "boulder X is in its hole" is a local save flag the
rock itself sets (world_reach.BOULDER_FLAGS), so each boulder the survey names
gets its own bit and game.c reads the flag. LLR_NORTH is the one derived bit:
boulder 3 OR the Lon Lon key.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import world_reach as W
import parse_tables as P

SKIPPED = []
WARN = []

# NOT include/*.h: GBA.mk globs that directory and runs every header
# through pycparser to harvest enums for the assembler, and this one is
# full of u16/u32 tables pycparser has no types for. A subdirectory is
# outside the (non-recursive) glob and still resolves under -iquote.
OUT = os.path.join(ROOT, 'include', 'quickstart', 'reach.h')

# token -> (C name, the inventory item that proves it, or None for "cannot be
# tested at run time"). Order fixes the bit numbers.
TOKENS = [
    ('sword',           'QS_REACH_SWORD',      'ITEM_SMITH_SWORD'),
    ('spin',            'QS_REACH_SPIN',       'ITEM_SKILL_SPIN_ATTACK'),
    ('bracelets',       'QS_REACH_BRACELETS',  'ITEM_POWER_BRACELETS'),
    ('bombs',           'QS_REACH_BOMBS',      'ITEM_BOMBS'),
    ('bow',             'QS_REACH_BOW',        'ITEM_BOW'),
    ('flippers',        'QS_REACH_FLIPPERS',   'ITEM_FLIPPERS'),
    ('cape',            'QS_REACH_CAPE',       'ITEM_ROCS_CAPE'),
    ('pacci',           'QS_REACH_PACCI',      'ITEM_PACCI_CANE'),
    ('lantern',         'QS_REACH_LANTERN',    'ITEM_LANTERN_OFF'),
    ('grip',            'QS_REACH_GRIP',       'ITEM_GRIP_RING'),
    ('boots',           'QS_REACH_BOOTS',      'ITEM_PEGASUS_BOOTS'),
    ('mitts',           'QS_REACH_MITTS',      'ITEM_MOLE_MITTS'),
    ('gust_jar',        'QS_REACH_GUST',       'ITEM_GUST_JAR'),
    ('ocarina',         'QS_REACH_OCARINA',    'ITEM_OCARINA'),
    ('lonlon_key',      'QS_REACH_LONLON_KEY', 'ITEM_QST_LONLON_KEY'),
    ('graveyard_key',   'QS_REACH_GRAVE_KEY',  'ITEM_QST_GRAVEYARD_KEY'),
    # Not an item, but the game keeps a count it can read.
    ('fusion',          'QS_REACH_FUSION',     None),
    # Untestable at run time - see the module docstring. Emitted so the table
    # stays a faithful copy of the survey; never set in the held mask.
    ('minish_cap',      'QS_REACH_MINISH',     None),
    ('story_flags',     'QS_REACH_STORY',      None),
    ('maze_solved',     'QS_REACH_MAZE',       None),
    ('boomerang_switches_4', 'QS_REACH_SWITCHES4', None),
    # Minish Woods / Lake Hylia only: "the derived survey could not find a
    # route here". Untestable on purpose - see world_reach.py's UNSURVEYED.
    ('unsurveyed',      'QS_REACH_UNSURVEYED', None),
    # Derived: boulder 3 of Lon Lon Ranch in its hole, OR the Lon Lon Key.
    (W.LLR_NORTH,       'QS_REACH_LLR_NORTH',  None),
    # Derived too (Oct 2026): a golden-kinstone gate the run rolled open,
    # OR its fusion done - game.c reads the gate's own state
    # (QuickStartGoldGatePassable) into the held mask.
    (W.SOURCE_FLOW,     'QS_REACH_SOURCE_FLOW', None),
    (W.STATUES,         'QS_REACH_STATUES',    None),
]
DERIVED = {W.LLR_NORTH, W.SOURCE_FLOW, W.STATUES}
BIT = {name: i for i, (name, _, _) in enumerate(TOKENS)}
BOULDER_BASE = len(TOKENS)

# survey region key -> the QS_REGION_* the game knows it by. Three of the
# survey's regions are thirds of one named region (Eastern Hills, Western
# Wood); the ring does not subdivide them and neither does travel.
RING = {
    'SHF': 'QS_REGION_SHF', 'EH-N': 'QS_REGION_EH', 'EH-C': 'QS_REGION_EH',
    'EH-S': 'QS_REGION_EH', 'LLR': 'QS_REGION_LLR', 'NHF': 'QS_REGION_NHF',
    'CG': 'QS_REGION_CG',
    'RV': 'QS_REGION_RV', 'TRIL': 'QS_REGION_TRIL', 'WW-N': 'QS_REGION_WW',
    'WW-C': 'QS_REGION_WW', 'WW-S': 'QS_REGION_WW', 'CW': 'QS_REGION_CW',
    'WR': 'QS_REGION_WR', 'CREN': 'QS_REGION_CREN',
    'MW': 'QS_REGION_MW', 'LH': 'QS_REGION_LH', 'VF': 'QS_REGION_VF',
    # Sub-starts. Lake Hylia is not one place: the border shore, the
    # wind-crest pocket, the isolated south-west corner and the ladder
    # pocket are four disconnected components with four different entrances,
    # and the survey walked them separately. Minish Village hangs off Minish
    # Woods and is its own map. Same treatment Eastern Hills and Western
    # Wood already get - several survey keys, one region the ring knows.
    'LH-CREST': 'QS_REGION_LH', 'LH-SW': 'QS_REGION_LH', 'LH-LADDER': 'QS_REGION_LH',
    'MV': 'QS_REGION_MW', 'CREN-BASE': 'QS_REGION_CREN',
}
RINGS = ['QS_REGION_CG', 'QS_REGION_NHF', 'QS_REGION_SHF', 'QS_REGION_EH',
         'QS_REGION_LLR', 'QS_REGION_TRIL', 'QS_REGION_WW', 'QS_REGION_RV',
         'QS_REGION_CW', 'QS_REGION_WR', 'QS_REGION_CREN', 'QS_REGION_MW',
         'QS_REGION_LH', 'QS_REGION_VF']

# Keys that are joined to the rest of their region ONLY by an explicit link:
# the three Lake Hylia pockets the walk found disconnected, and Mount
# Crenel's upper half, which is a climb (CREN-BASE -> CREN, the grip) and not
# a free stroll from the base. Everything else that shares a ring is stitched
# free, which is the ring's own reading.
ISOLATED = {'LH-CREST', 'LH-SW', 'LH-LADDER', 'CREN'}
# ...and the three lake pockets lead nowhere else in their ring either: the
# crest and the corner are cut off from the shore, and the ladder pocket's
# own rows price everything it can reach. Mount Crenel's upper half is not
# here because dropping back to the base IS free (a one-way ledge).
NO_WAY_OUT = {'LH-CREST', 'LH-SW', 'LH-LADDER'}
SNAP = 48   # pixels: how close a row must be to a sibling's landing to price the walk to it

MINISH = W.MINISH      # the survey's own token name, not a second spelling
BOOTS = W.BOOTS

NODES = list(W.SURVEY.keys())
NODE_ID = {k: i for i, k in enumerate(NODES)}
BASE_OF = {k: W.ENTRANCES.get(k, k) for k in NODES}
RING_OF = {k: RING[BASE_OF[k]] for k in NODES}


def and_dnf(a, b):
    """AND two DNFs; None (impossible) absorbs; supersets are dropped."""
    if a is None or b is None:
        return None
    terms = []
    for ta in (a or [[]]):
        for tb in (b or [[]]):
            t = list(ta)
            for tok in tb:
                if tok not in t:
                    t.append(tok)
            terms.append(t)
    out = []
    for t in terms:
        if any(set(o) < set(t) for o in terms):
            continue
        if sorted(t) not in [sorted(o) for o in out]:
            out.append(t)
    return out


def expand_minish(req, ring):
    """Replace the `minish_cap` token with what shrinking COSTS in `ring`.

    The token used to be a flat untestable bit, so every route priced at
    "be Minish" was permanently false and 42 rooms were invisible to the
    chain. It is really two things: the ability, which is free (PL_MINISH is
    a state, not an item), and a transform point within reach, which is what
    actually varies. world_reach.MINISH_PORTAL prices the second per region,
    measured from the room entity lists by minish_portals.py.

      free region   -> drop the token; whatever else the term wanted stands
      boots region  -> the token becomes `boots`
      no portal     -> keep it untestable, so the row stays unreachable

    Conservative in the one direction that matters: a region with no known
    transform point keeps its rows shut rather than opening them on a guess.
    """
    if not req:
        return req
    price = getattr(W, 'MINISH_PORTAL', {}).get(ring, None)
    out = []
    for term in req:
        if MINISH not in term:
            out.append(term)
            continue
        if price is None:
            out.append(term)          # untestable, unchanged
            continue
        rest = [t for t in term if t != MINISH]
        if not price:                 # free: the stump costs nothing
            out.append(rest)
        else:
            for extra in price:       # e.g. [[BOOTS]]
                merged = list(rest)
                for tok in extra:
                    if tok not in merged:
                        merged.append(tok)
                out.append(merged)
    seen, uniq = set(), []
    for t in out:
        k = tuple(sorted(t))
        if k not in seen:
            seen.add(k)
            uniq.append(t)
    return uniq


# Boulders that some row actually names get a bit; the rest of BOULDER_FLAGS
# is documentation until a survey prices something on them.
def referenced_boulders():
    used = []
    for k, r in W.SURVEY.items():
        for e in r['dests']:
            for term in (e['req'] or []):
                for tok in term:
                    if tok.startswith('boulder:') and tok not in used:
                        used.append(tok)
        for term in (r['room_req'] or []):
            for tok in term:
                if tok.startswith('boulder:') and tok not in used:
                    used.append(tok)
    return [b for b in W.BOULDER_FLAGS if b in used], [b for b in used if b not in W.BOULDER_FLAGS]


BOULDERS, UNFLAGGED = referenced_boulders()
BOULDER_BIT = {b: BOULDER_BASE + i for i, b in enumerate(BOULDERS)}


def cname_of_boulder(tok):
    return 'QS_REACH_BOULDER_' + tok[len('boulder:'):].replace(':', '_').replace('-', '_')


def term_mask(term, where):
    m = 0
    for t in term:
        if t.startswith('boulder:'):
            if t not in BOULDER_BIT:
                raise SystemExit('%s: %s has no flag in world_reach.BOULDER_FLAGS' % (where, t))
            m |= 1 << BOULDER_BIT[t]
        else:
            m |= 1 << BIT[t]
    return m


def req_masks(req, where):
    """DNF -> masks. 0 means 'free'; an empty list means 'never'."""
    if req is None:
        return []
    if not req:
        return [0]
    return sorted({term_mask(t, where) for t in req})


def node_req(key):
    """What every row of this key costs on top of itself: the key's room_req,
    folded into its rows and its outgoing edges alike."""
    return W.SURVEY[key]['room_req'] or []


def adjacency():
    """sQuickStartRegionAdjacency from game.c, as {ring: set(ring)}."""
    src = P.GAME
    i = src.find('static const u16 sQuickStartRegionAdjacency[QS_REGION_COUNT] = {')
    body = src[i:src.find('\n};', i)]
    marks = [(m.start(), m.group(1)) for m in re.finditer(r'/\* (\w+)\s*\*/', body)
             if 'QS_REGION_' + m.group(1) in RINGS]
    out = {}
    for n, (pos, name) in enumerate(marks):
        end = marks[n + 1][0] if n + 1 < len(marks) else len(body)
        out['QS_REGION_' + name] = {'QS_REGION_' + r for r in re.findall(r'1 << QS_REGION_(\w+)', body[pos:end])}
    if len(out) != len(RINGS):
        raise SystemExit('adjacency parse failed: %r' % sorted(out))
    return out


def find_row(key, area, room, x, y, snap=0):
    best = None
    for e in W.SURVEY[key]['dests']:
        if e['area'] != area or e['room'] != room or e['local'][0] is None:
            continue
        dx, dy = abs(e['local'][0] - x), abs(e['local'][1] - y)
        if dx <= snap and dy <= snap and (best is None or dx + dy < best[0]):
            best = (dx + dy, e)
    return best[1] if best else None


def build_graph():
    """-> (dests, edges, pool_node). dests: (node key, area, room, DNF);
    edges: (from key, to key, DNF, why). DNFs are already Minish-expanded."""
    dests = []
    for k in NODES:
        for e in W.SURVEY[k]['dests']:
            req = expand_minish(and_dnf(node_req(k), e['req']), RING_OF[k])
            dests.append((k, e['area'], e['room'], req, '%s %s/%s' % (k, e['area'], e['room'])))

    edges = []
    have = set()      # (from key, to key)
    covered = set()   # (from ring, to ring) spelled out by a link

    def add(frm, to, req, why):
        # Two exits of one node can land at the same far node (Lon Lon's
        # (712,750) and (712,903) both reach Lake Hylia's south-west corner):
        # the edge is the OR of their prices, never just the first.
        if (frm, to) in have:
            for n, (f, t, r, w) in enumerate(edges):
                if f == frm and t == to:
                    if r is None:
                        edges[n] = (f, t, req, why)
                    elif req is not None:
                        merged = list(r)
                        for term in req:
                            if sorted(term) not in [sorted(x) for x in merged]:
                                merged.append(term)
                        merged = [t2 for t2 in merged if not any(set(o) < set(t2) for o in merged)]
                        edges[n] = (f, t, merged, w + ' | ' + why)
                    break
            return
        have.add((frm, to))
        edges.append((frm, to, req, why))

    # 1. the links: an exit row, and the node it lands at
    for (k, area, room, x, y), to in W.LINKS.items():
        row = find_row(k, area, room, x, y)
        covered.add((RING_OF[k], RING_OF[to]))
        if row is None:
            WARN.append('link %s (%s/%s %d,%d) -> %s has no row; no edge' % (k, area, room, x, y, to))
            continue
        if row['req'] is None:
            have.add((k, to))   # spelled out as impossible: no default either
            continue
        req = expand_minish(and_dnf(node_req(k), row['req']), RING_OF[k])
        add(k, to, req, 'link: %s row (%d,%d)' % (k, x, y))

    # 2. sibling entrances of one region: the row each has at the other's spot
    for k in NODES:
        for k2 in NODES:
            if k2 == k or BASE_OF[k2] != BASE_OF[k]:
                continue
            sa, sr, sx, sy = W.SURVEY[k2]['start']
            row = find_row(k, sa, sr, sx, sy, SNAP)
            if row is None or row['req'] is None:
                continue
            req = expand_minish(and_dnf(node_req(k), row['req']), RING_OF[k])
            add(k, k2, req, 'walk from %s to the %s landing' % (k, k2))

    # 3. the thirds and the base/upper halves: one ring, stitched free unless isolated
    for k in NODES:
        for k2 in NODES:
            if k2 == k or RING_OF[k2] != RING_OF[k] or BASE_OF[k] == BASE_OF[k2]:
                continue
            if k in W.ENTRANCES or k2 in W.ENTRANCES or k2 in ISOLATED or k in NO_WAY_OUT:
                continue
            req = expand_minish(and_dnf([], node_req(k2)), RING_OF[k2])
            add(k, k2, req, 'same ring region (%s)' % RING_OF[k])

    # 4. every ring adjacency the links do not spell out: the old reading
    adj = adjacency()
    for ra in RINGS:
        # RINGS order, not set order: the header must come out byte-identical
        # from one process to the next or --check cries wolf.
        for rb in sorted(adj.get(ra, ()), key=RINGS.index):
            if (ra, rb) in covered:
                continue
            for k in NODES:
                if RING_OF[k] != ra or k in NO_WAY_OUT:
                    continue
                for k2 in NODES:
                    if RING_OF[k2] != rb or k2 in W.ENTRANCES or k2 in ISOLATED:
                        continue
                    entry = W.ENTRY.get(rb)
                    req = entry if entry is not None else node_req(k2)
                    req = expand_minish(and_dnf([], req), rb)
                    add(k, k2, req, 'ring adjacency %s -> %s (entry price)' % (ra, rb))

    # the drop: a pool row lands at the base node whose start is in its room
    pool_node = []
    for row in P.region_pool():
        ring = None
        for key, r in RING.items():
            pass
        cands = [k for k in NODES if k not in W.ENTRANCES and k not in ISOLATED
                 and W.SURVEY[k]['start'][0] == row['areaName'][5:]
                 and W.SURVEY[k]['start'][1] == row['roomName'][5 + len(row['areaName'][5:]) + 1:]]
        if not cands:
            cands = [k for k in NODES if k not in W.ENTRANCES and k not in ISOLATED
                     and RING_OF[k] == 'QS_REGION_' + _ring_of_pool(row)]
        if not cands:
            raise SystemExit('no node for pool row %s' % row['roomName'])
        ex, ey = row['entrance']
        cands.sort(key=lambda k: abs(W.SURVEY[k]['start'][2] - ex) + abs(W.SURVEY[k]['start'][3] - ey))
        pool_node.append(cands[0])
    return dests, edges, pool_node


def _ring_of_pool(row):
    src = P.GAME
    i = src.find('static const u8 byPool[] = {')
    names = re.findall(r'QS_REGION_(\w+)', src[i:src.find('};', i)])
    rows = P.region_pool()
    return names[rows.index(row)]


def build():
    dests, edges, pool_node = build_graph()
    terms = 1
    for (_, _, _, req, where) in dests:
        if req:
            terms = max(terms, len(req_masks(req, where)))
    for (_, _, req, why) in edges:
        if req:
            terms = max(terms, len(req_masks(req, why)))

    L = []
    A = L.append
    A('// GENERATED by tools/quickstart/gen_reach.py from world_reach.py.')
    A('// Do not edit by hand - edit the survey and regenerate. `gen_reach.py')
    A('// --check` fails the build\'s own conscience if this drifts.')
    A('#ifndef QUICKSTART_REACH_H')
    A('#define QUICKSTART_REACH_H')
    A('')
    A('// One bit per fact a route can require. The first group are items and')
    A('// are tested with GetInventoryValue; QS_REACH_FUSION reads the run\'s')
    A('// fusion count; the untestable group has NO run-time test, is never set')
    A('// in the held mask, and so permanently fails any term containing it;')
    A('// QS_REACH_LLR_NORTH is derived (boulder 3 OR the Lon Lon key); the two')
    A('// golden-kinstone gates are derived (rolled open this run OR fused); and')
    A('// each boulder bit reads the rock\'s own "settled in the hole" save flag.')
    A('// That is deliberate: an unreachable step is an unwinnable run, so the')
    A('// table errs toward offering the chain placer less, never more.')
    for i, (tok, cname, item) in enumerate(TOKENS):
        note = ('  // %s' % item) if item else ('  // derived' if tok in DERIVED else '  // no run-time test')
        A('#define %-28s (1u << %2d)%s' % (cname, i, note))
    for b in BOULDERS:
        area, flag = W.BOULDER_FLAGS[b]
        A('#define %-28s (1u << %2d)  // %s: AREA_%s local flag 0x%02x' % (cname_of_boulder(b), BOULDER_BIT[b], b, area, flag))
    A('')
    A('// The items behind the first block of bits, in bit order. game.c')
    A('// walks this to build the held mask, so the two cannot drift: add a')
    A('// token to TOKENS and both the bit and its item appear here together.')
    A('static const u16 sQuickStartReachItems[] = {')
    items = [item for _, _, item in TOKENS if item]
    for n in range(0, len(items), 3):
        A('    ' + ' '.join('%s,' % it for it in items[n:n + 3]))
    A('};')
    A('#define QS_REACH_ITEM_BITS %d' % len(items))
    A('#define QS_REACH_TERMS %d' % terms)
    A('')
    A('// The boulders, in bit order from QS_REACH_BOULDER_BASE: the area whose')
    A('// local flag bank holds the rock\'s flag, and the flag. Read with')
    A('// CheckLocalFlagByBank(GetFlagBankOffset(area), flag).')
    A('typedef struct {')
    A('    u8 area;')
    A('    u8 flag;')
    A('} QuickStartReachBoulder;')
    A('')
    A('#define QS_REACH_BOULDER_BASE %d' % BOULDER_BASE)
    # The derived bit's own flag: boulder 3 is not named by any row (every
    # row says LLR_NORTH), so it gets no bit of its own, and game.c reads
    # the flag directly to compute the derived one.
    n_area, n_flag = W.BOULDER_FLAGS[W.BOULDER('LLR', 3)]
    A('#define QS_REACH_LLR_NORTH_AREA AREA_%s  // boulder:LLR:3' % n_area)
    A('#define QS_REACH_LLR_NORTH_FLAG 0x%02x' % n_flag)
    A('#define QS_REACH_BOULDER_BITS %d' % len(BOULDERS))
    A('static const QuickStartReachBoulder sQuickStartReachBoulders[] = {')
    for b in BOULDERS:
        area, flag = W.BOULDER_FLAGS[b]
        A('    { AREA_%s, 0x%02x }, // %s' % (area, flag, b))
    A('};')
    A('')
    A('// The nodes: every start the survey was walked from, each inside a ring')
    A('// region. A region\'s own start (where the drop lands) and each of its')
    A('// surveyed entrances are separate nodes.')
    A('typedef struct {')
    A('    u8 region;   // QS_REGION_*')
    A('    u8 area;')
    A('    u8 room;')
    A('    u8 entrance; // 1 = an entrance of its region rather than the drop start')
    A('} QuickStartReachNode;')
    A('')
    A('#define QS_REACH_NODES %d' % len(NODES))
    A('static const QuickStartReachNode sQuickStartReachNodes[QS_REACH_NODES] = {')
    for k in NODES:
        sa, sr, sx, sy = W.SURVEY[k]['start']
        A('    /* %2d %-10s */ { %s, AREA_%s, ROOM_%s_%s, %d },' % (
            NODE_ID[k], k, RING_OF[k], sa, sa, sr, 1 if k in W.ENTRANCES else 0))
    A('};')
    A('')
    A('// Which node each region pool row\'s landing is: the drop starts here.')
    A('static const u8 sQuickStartReachPoolNode[] = {')
    for i, k in enumerate(pool_node):
        A('    %2d, // pool %2d -> %s' % (NODE_ID[k], i, k))
    A('};')
    A('')
    A('// The edges: from node to node, at the price of the exit row that lands')
    A('// there. Alternatives in req; 0 = free, ~0u = unused slot.')
    A('typedef struct {')
    A('    u8 from;')
    A('    u8 to;')
    A('    u32 req[%d];' % terms)
    A('} QuickStartReachEdge;')
    A('')
    A('static const QuickStartReachEdge sQuickStartReachEdges[] = {')
    for (frm, to, req, why) in edges:
        masks = req_masks(req, why) + [None] * terms
        cells = ['%#010xu' % m if m else ('0' if m == 0 else '~0u') for m in masks[:terms]]
        A('    { %2d, %2d, { %s } }, // %s -> %s: %s' % (NODE_ID[frm], NODE_ID[to], ', '.join(cells), frm, to, why))
    A('};')
    A('')
    A('typedef struct {')
    A('    u8 node;')
    A('    u8 area;')
    A('    u8 room;')
    A('    u8 pad;')
    A('    u32 req[%d]; // alternatives; 0 = free, ~0u = never' % terms)
    A('} QuickStartReachDest;')
    A('')
    A('// Every place the survey walked to, as (node, area, room) plus what it')
    A('// cost to get there FROM THAT NODE. A room can appear many times - two')
    A('// nodes can both reach it, one node by two routes - and it counts as')
    A('// reachable if ANY row whose node the flood reached is satisfied.')
    A('static const QuickStartReachDest sQuickStartReachDests[] = {')
    for (k, ea, er, req, where) in dests:
        area, room = 'AREA_' + ea, 'ROOM_%s_%s' % (ea, er)
        if area not in P.AREAS or room not in P.ROOMS:
            SKIPPED.append(where)
            continue
        masks = req_masks(req, where) + [None] * terms
        cells = ['%#010xu' % m if m else ('0' if m == 0 else '~0u') for m in masks[:terms]]
        A('    { %2d, %s, %s, 0, { %s } },' % (NODE_ID[k], area, room, ', '.join(cells)))
    A('};')
    A('')
    A('#endif // QUICKSTART_REACH_H')
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    text = build()
    if '--check' in sys.argv:
        cur = open(OUT).read() if os.path.exists(OUT) else ''
        if cur != text:
            print('STALE: %s does not match world_reach.py - rerun gen_reach.py' % OUT)
            sys.exit(1)
        print('%s is up to date (%d destinations)' % (OUT, text.count('    { ')))
    else:
        open(OUT, 'w').write(text)
        print('wrote %s (%d nodes, %d edges, %d destination rows)' % (
            OUT, text.count('*/ {'), text.count('} }, //'), text.count(', 0, {')))
        for w in WARN:
            print('  warning: ' + w)
        for w in SKIPPED:
            print('  skipped (room name is not an enum member): %s' % w)
        if UNFLAGGED:
            print('  boulders named by rows with no flag: %s' % UNFLAGGED)
