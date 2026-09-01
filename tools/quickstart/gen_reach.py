"""Generate the C reachability table from the walked survey.

world_reach.py is the single source of truth for "what does it cost to reach
this place"; this turns it into a table game.c can consult at run time, so the
win chain can only ever place a step somewhere the player can actually get to.

    python3 tools/quickstart/gen_reach.py          # write include/quickstart_reach.h
    python3 tools/quickstart/gen_reach.py --check  # fail if the file is stale

WHAT SURVIVES THE TRIP. Requirements are DNF - a list of alternative terms,
each a set of tokens that must all hold - and that maps onto a u32 bitmask per
term with no loss. What does NOT survive is any token the game cannot TEST at
run time: being Minish is a state rather than an item, and "the maze is
solved" / "four switches are thrown" / "a boulder is in its hole" have no
save-flag this file can point at. Those tokens are emitted anyway, and simply
never appear in the held-mask the game builds, so any term containing one is
permanently false. A destination that needs one is invisible to the chain
placer rather than wrongly offered to it - the conservative direction, because
the cost of being wrong is an unwinnable run.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import world_reach as W
import parse_tables as P

SKIPPED = []

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
]
BOULDER = ('QS_REACH_BOULDER', 'a boulder pushed into a hole in this region')
BIT = {name: i for i, (name, _, _) in enumerate(TOKENS)}
BOULDER_BIT = len(TOKENS)

# survey region key -> the QS_RING_* the game knows it by. Three of the
# survey's regions are thirds of one ring region (Eastern Hills, Western
# Wood); the ring does not subdivide them and neither does travel.
RING = {
    'SHF': 'QS_RING_SHF', 'EH-N': 'QS_RING_EH', 'EH-C': 'QS_RING_EH',
    'EH-S': 'QS_RING_EH', 'LLR': 'QS_RING_LLR', 'NHF': 'QS_RING_NHF',
    'RV': 'QS_RING_RV', 'TRIL': 'QS_RING_TRIL', 'WW-N': 'QS_RING_WW',
    'WW-C': 'QS_RING_WW', 'WW-S': 'QS_RING_WW', 'CW': 'QS_RING_CW',
    'WR': 'QS_RING_WR', 'CREN': 'QS_RING_CREN',
}
RINGS = ['QS_RING_CG', 'QS_RING_NHF', 'QS_RING_SHF', 'QS_RING_EH',
         'QS_RING_LLR', 'QS_RING_TRIL', 'QS_RING_WW', 'QS_RING_RV',
         'QS_RING_CW', 'QS_RING_WR', 'QS_RING_CREN']

MAX_TERMS = 3   # the widest requirement in the survey (Lon Lon's east exit:
                # flippers, or the cape, or Minish plus the Pacci Cane)


def term_mask(term):
    m = 0
    for t in term:
        if t.startswith('boulder:'):
            m |= 1 << BOULDER_BIT
        else:
            m |= 1 << BIT[t]
    return m


def req_masks(req, where):
    """DNF -> up to MAX_TERMS masks. 0 means 'free'; an empty list means
    'never'. A requirement with more alternatives than fit is an error rather
    than a silent truncation - truncating would make a place look HARDER than
    it is, which strands runs."""
    if not req:
        return [0]
    terms = sorted({term_mask(t) for t in req})
    if len(terms) > MAX_TERMS:
        raise SystemExit('%s has %d alternative terms, MAX_TERMS is %d'
                         % (where, len(terms), MAX_TERMS))
    return terms


def build():
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
    A('// fusion count; everything after it has NO run-time test, is never set')
    A('// in the held mask, and so permanently fails any term containing it.')
    A('// That is deliberate: an unreachable step is an unwinnable run, so the')
    A('// table errs toward offering the chain placer less, never more.')
    for i, (tok, cname, item) in enumerate(TOKENS):
        note = ('  // %s' % item) if item else '  // no run-time test'
        A('#define %-22s (1u << %2d)%s' % (cname, i, note))
    A('#define %-22s (1u << %2d)  // %s' % (BOULDER[0], BOULDER_BIT, BOULDER[1]))
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
    A('#define QS_REACH_TERMS %d' % MAX_TERMS)
    A('')
    A('typedef struct {')
    A('    u8 region;   // QS_RING_*')
    A('    u8 area;')
    A('    u8 room;')
    A('    u32 req[%d]; // alternatives; 0 = free, ~0u = never' % MAX_TERMS)
    A('} QuickStartReachDest;')
    A('')

    # Region entry requirements, indexed by QS_RING_*.
    A('// What it costs to be inside a region AT ALL, straight from the')
    A('// survey\'s own per-region room_req. A ring region with no survey')
    A('// entry (Hyrule Castle Garden) gets "never": the survey never walked')
    A('// it, so nothing in it can be proven reachable.')
    A('static const u32 sQuickStartReachRegion[][%d] = {' % MAX_TERMS)
    ring_req = {}
    for key, r in W.SURVEY.items():
        masks = req_masks(r['room_req'], 'region ' + key)
        ring = RING[key]
        # Two survey regions sharing a ring: the ring is enterable if EITHER is.
        if ring in ring_req:
            ring_req[ring] = sorted(set(ring_req[ring]) | set(masks))
            if len(ring_req[ring]) > MAX_TERMS:
                raise SystemExit('%s merged past MAX_TERMS' % ring)
        else:
            ring_req[ring] = masks
    for ring in RINGS:
        masks = ring_req.get(ring)
        if masks is None:
            cells = ['~0u'] * MAX_TERMS
            note = 'never - not surveyed'
        else:
            cells = ['%#010xu' % m if m else '0' for m in masks]
            cells += ['~0u'] * (MAX_TERMS - len(cells))
            note = 'free' if masks == [0] else 'gated'
        A('    /* %-14s */ { %s },  // %s' % (ring, ', '.join(cells), note))
    A('};')
    A('')

    rows = []
    for key, r in W.SURVEY.items():
        for e in r['dests']:
            where = '%s %s/%s' % (key, e['area'], e['room'])
            area, room = 'AREA_' + e['area'], 'ROOM_%s_%s' % (e['area'], e['room'])
            # The survey records places by the name the mapexplore overlay
            # printed, and a couple of those are not enum members - the
            # Royal Valley crypt and one Castor Wilds dig cave are rooms the
            # game reaches without transitions.c naming them. Dropped rather
            # than guessed at: a row the compiler cannot resolve stops the
            # build, and a row pointed at the WRONG room would place a step
            # somewhere the player is not.
            if area not in P.AREAS or room not in P.ROOMS:
                SKIPPED.append(where)
                continue
            masks = req_masks(e['req'], where)
            masks = list(masks) + [None] * (MAX_TERMS - len(masks))
            rows.append((RING[key], area, room, masks, where))
    A('// Every place the survey walked to, as (region, area, room) plus what')
    A('// it cost to get there FROM THAT REGION\'S START. A room can appear')
    A('// more than once - two regions can both reach it, and one region can')
    A('// reach one room by two routes - and it counts as reachable if ANY of')
    A('// its rows is satisfied.')
    A('static const QuickStartReachDest sQuickStartReachDests[] = {')
    for ring, area, room, masks, where in rows:
        cells = ['%#010xu' % m if m else ('0' if m == 0 else '~0u') for m in masks]
        A('    { %s, %s, %s, { %s } },' % (ring, area, room, ', '.join(cells)))
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
        print('%s is up to date (%d destinations)' % (OUT, text.count('{ QS_RING_')))
    else:
        open(OUT, 'w').write(text)
        print('wrote %s (%d destination rows)' % (OUT, text.count('{ QS_RING_')))
        for w in SKIPPED:
            print('  skipped (room name is not an enum member): %s' % w)
