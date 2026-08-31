"""The overworld as a graph of PORTS, and the item bill of a route through it.

The question this answers is the user's own framing (Aug 2026): standing at
one entrance of an overworld region, what does the player need to reach
another entrance of the SAME region? Everything else - which regions a run
visits, where its win conditions sit, which key items a run must therefore
hand out - falls out of that once the graph exists.

Three tables make up the model.

  PORTS + LINKS - where a region's entrances are and what is on the other
  side. Not invented: every port below is a real WARP_TYPE_BORDER row in
  src/data/transitions.c or a real scroll seam between two rooms of
  AREA_HYRULE_FIELD, and the seams were read out of gAreaRoomHeaders
  (see derive_links() and tools/quickstart/seam_audit.py). The user's
  compass naming maps onto them exactly - "ENE" is the east edge's north
  half, which is TRANSITION_SHAPE_BORDER_EAST_NORTH.

  TRAVERSAL - for each region, from-port to to-port, what it costs. This is
  the user's own survey, entered verbatim. It is DIRECTED: the cost of
  A->B says nothing about B->A (Lon Lon's ESE->WNW wants Roc's Cape while
  WNW->ESE will take Cape, Flippers or the Pacci Cane), and some pairs are
  one-way outright (nothing in Trilby reaches its North exit).

  GATES - regions that cost an item to be IN at all, whatever route you
  take through them. Royal Valley wants the Lantern; Lake Hylia the
  Flippers; Crenel the Grip Ring; Castor Wilds the Cape or the Pegasus Boots.

Requirements are in disjunctive normal form: a set of alternative terms,
each term a set of items that must ALL be held. "Cape or Flippers" is two
one-item terms; "Bombs and Level-3 Sword and Spin" is one three-item term;
the empty term set is impossible and {frozenset()} is free. AND-ing two
requirements multiplies out and then drops any term that is a superset of
another, so a route's bill stays the shortest sets that actually work.

Usage:
    python3 tools/quickstart/overworld_paths.py            # model + examples
    python3 tools/quickstart/overworld_paths.py --check    # consistency only
    python3 tools/quickstart/overworld_paths.py --paths 20 # sample routes
"""
import itertools
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# ---------------------------------------------------------------- items ----

SWORD = 'sword'
SWORD3 = 'sword3'          # the level-3 blade
SPIN = 'spin'              # the Spin Attack skill
BOMBS = 'bombs'
FLIPPERS = 'flippers'
CAPE = 'cape'              # Roc's Cape
PACCI = 'pacci'            # Cane of Pacci
LANTERN = 'lantern'
GRIP = 'grip'              # Grip Ring
BOOTS = 'boots'            # Pegasus Boots

ITEM_ENUM = {              # for the eventual game.c port
    SWORD: 'ITEM_SMITH_SWORD', SWORD3: 'ITEM_BLUE_SWORD', SPIN: 'ITEM_SKILL_SPIN_ATTACK',
    BOMBS: 'ITEM_BOMBS', FLIPPERS: 'ITEM_FLIPPERS', CAPE: 'ITEM_ROCS_CAPE',
    PACCI: 'ITEM_PACCI_CANE', LANTERN: 'ITEM_LANTERN_OFF', GRIP: 'ITEM_GRIP_RING',
    BOOTS: 'ITEM_PEGASUS_BOOTS',
}

# Can a run actually GET each of these? Checked against sQuickStartTiers in
# src/game.c - the only thing that hands out key items - plus the starting
# kit. This is the half of the question the user flagged: "we need to make
# sure the player is able to get the key items they need for the paths we
# define", and a route whose bill names something no ? room can drop is a
# route nobody can walk.
OBTAINABLE = {
    SWORD:    (True,  'ITEM_SMITH_SWORD is in the starting kit'),
    SWORD3:   (True,  'ITEM_BLUE_SWORD drops (RARE, behind the White Sword) - added '
                      'to the tier table because this model showed the Royal Valley '
                      'route was gated behind an item no run could get'),
    SPIN:     (True,  'ITEM_SKILL_SPIN_ATTACK drops'),
    BOMBS:    (True,  'ITEM_BOMBS drops'),
    FLIPPERS: (True,  'ITEM_FLIPPERS drops'),
    CAPE:     (True,  'ITEM_ROCS_CAPE drops'),
    PACCI:    (True,  'ITEM_PACCI_CANE drops'),
    LANTERN:  (True,  'ITEM_LANTERN_OFF drops'),
    GRIP:     (True,  'ITEM_GRIP_RING drops'),
    BOOTS:    (True,  'ITEM_PEGASUS_BOOTS drops'),
}


def obtainable_term(term):
    return all(OBTAINABLE.get(i, (False, ''))[0] for i in term)


def walkable(dnf):
    """Is there at least one way through that a run can actually equip?"""
    return any(obtainable_term(t) for t in dnf)


# ------------------------------------------------------ requirement algebra --

FREE = frozenset({frozenset()})
IMPOSSIBLE = frozenset()


def req(*terms):
    """A requirement from alternative terms, e.g. req([CAPE], [FLIPPERS])."""
    if not terms:
        return FREE
    return minimize(frozenset(frozenset(t) for t in terms))


def minimize(dnf):
    """Drop any term that another term is a subset of - it can never be the
    cheapest way through, and leaving it in makes bills look worse than they
    are."""
    out = []
    for t in sorted(dnf, key=len):
        if not any(o <= t for o in out):
            out.append(t)
    return frozenset(out)


def both(a, b):
    """AND: every way through a, combined with every way through b."""
    if not a or not b:
        return IMPOSSIBLE
    return minimize(frozenset(x | y for x in a for y in b))


def either(a, b):
    """OR: either requirement will do."""
    return minimize(a | b)


def satisfied(dnf, held):
    return any(t <= set(held) for t in dnf)


def show(dnf):
    if dnf is IMPOSSIBLE or not dnf:
        return 'IMPOSSIBLE'
    terms = sorted((' + '.join(sorted(t)) if t else '-') for t in dnf)
    return ' / '.join(terms)


# ------------------------------------------------------------- the regions --
# Ports use the user's compass naming. The single letters are edge middles;
# three-letter names are edge-then-half, so ENE is the east edge's north half
# and SWS is the south edge's west half - the same convention
# TRANSITION_SHAPE_BORDER_EAST_NORTH etc. already use.

REGIONS = {
    'CG':   dict(name='Hyrule Castle Garden', ports=['S']),
    'NHF':  dict(name='North Hyrule Field',   ports=['N', 'S', 'ENE', 'ESE', 'WSW', 'WNW']),
    'SHF':  dict(name='South Hyrule Field',   ports=['N', 'E', 'W']),
    'TRIL': dict(name='Trilby Highlands',     ports=['N', 'W', 'S', 'ENE', 'ESE']),
    'LLR':  dict(name='Lon Lon Ranch',        ports=['N', 'WNW', 'WSW', 'ESE', 'SWS']),
    'EH':   dict(name='Eastern Hills',        ports=['N', 'W', 'ENE', 'ESE', 'S']),
    'WW':   dict(name='Western Wood',         ports=['N', 'E', 'W']),
    # Not in the pool yet. Listed so the gates and the links that reach them
    # are already stated - adding one to the run is then a pool edit, not a
    # graph edit.
    # Royal Valley is a one-way valve, and the room's own geometry is why.
    # Measured (royal_valley_survey.py): Main is 30x63 tiles holding THREE
    # separate walkable components. North Hyrule Field's border lands in a
    # 42-tile pocket (tx 19-29, ty 36-40); the graveyard proper is 242 tiles
    # (tx 4-28, ty 43-62) with Trilby's border in it; and a 262-tile top
    # part (tx 2-26, ty 23-40) reachable ONLY by solving the Lost Woods
    # maze. The pocket drops into the graveyard over a one-tile neck at
    # tx 20, ty 41-42 whose collision reads 0x29 - a ledge, downhill only.
    # Solving the maze reaches the top part, which does NOT contain the
    # North Hyrule Field border, so it is not a way back out either. Hence
    # E->S free, S->E impossible: exactly the user's survey, for reasons
    # the room can show you.
    'RV':   dict(name='Royal Valley',   ports=['E', 'S']),
    'VF':   dict(name='Veil Falls',     ports=['S', 'WSW'], pooled=False),
    'LH':   dict(name='Lake Hylia',     ports=['W'],        pooled=False),
    'CREN': dict(name='Mt Crenel',      ports=['E'],        pooled=False),
    # Castor Wilds joined the pool (the western spur): in from Western
    # Wood North's west border (its E port), out south-west to the Wind
    # Ruins - that passage's sleeping-statue fusions are pre-fused at run
    # start, so the SWS exit costs nothing beyond the area's own gate.
    # In-region traversal E<->SWS crosses the swamp, which is what the
    # region gate (cape-or-boots) already prices.
    'CW':   dict(name='Castor Wilds',   ports=['E', 'SWS']),
    # The Wind Ruins: one way in (the Castor Wilds border at its north end).
    # Its six rooms are ring members; the entrance strip and the armos
    # field below the fortress are pool regions, the rest are corridors.
    'WR':   dict(name='Wind Ruins',     ports=['N']),
}

# Regions that cost an item to be inside AT ALL, on any route through them.
GATES = {
    # RETIRED: 'RV': req([LANTERN]). The walked survey
    # (tools/quickstart/world_reach.py) disagreed with this row and the
    # survey is right: you can stand in Royal Valley's entrance, and walk
    # its E->S crossing, with no Lantern at all. What the Lantern actually
    # gates is the LOST WOODS MAZE and everything past it - the graveyard,
    # Dampe's house, the upper pocket - none of which is a port, so none of
    # it belongs in a port-level gate. Those costs live per-destination in
    # world_reach.py, where they can also carry the maze-solved and
    # graveyard-key facts that come with them.
    'LH':   req([FLIPPERS]),
    'CREN': req([GRIP]),
    'CW':   req([CAPE], [BOOTS]),
}

# ------------------------------------------------------------ the traversal --
# The user's survey, verbatim. Key is (region, fromPort, toPort).
# Anything absent is UNKNOWN, not free - see check() below, which lists the
# holes rather than silently treating them as walkable.

TRAVERSAL = {}


def t(region, frm, to, *terms):
    TRAVERSAL[(region, frm, to)] = req(*terms) if terms else FREE


def impossible(region, frm, to):
    TRAVERSAL[(region, frm, to)] = IMPOSSIBLE


# --- Hyrule Castle Garden --------------------------------------------------
# One port, so nothing to cross. ("south entrance, no requirements".)

# --- North Hyrule Field ----------------------------------------------------
t('NHF', 'N', 'ENE', [BOMBS])
t('NHF', 'N', 'S')
t('NHF', 'N', 'ESE', [SWORD])
t('NHF', 'N', 'WSW', [FLIPPERS], [CAPE])
t('NHF', 'N', 'WNW', [BOMBS, SWORD3, SPIN])

t('NHF', 'WNW', 'WSW')
t('NHF', 'WNW', 'N')
t('NHF', 'WNW', 'S')
t('NHF', 'WNW', 'ENE', [BOMBS])
t('NHF', 'WNW', 'ESE', [SWORD])

t('NHF', 'ESE', 'S', [SWORD])
t('NHF', 'ESE', 'WSW', [SWORD, CAPE], [SWORD, FLIPPERS])
t('NHF', 'ESE', 'WNW', [BOMBS, SWORD3, SPIN])
t('NHF', 'ESE', 'N', [SWORD])
t('NHF', 'ESE', 'ENE', [SWORD, BOMBS])

t('NHF', 'ENE', 'N', [BOMBS])
t('NHF', 'ENE', 'WNW', [BOMBS, SWORD3, SPIN])
t('NHF', 'ENE', 'WSW', [BOMBS, FLIPPERS], [BOMBS, CAPE])
t('NHF', 'ENE', 'S', [BOMBS])
t('NHF', 'ENE', 'ESE', [BOMBS, SWORD])

t('NHF', 'S', 'WSW', [CAPE], [FLIPPERS])
t('NHF', 'S', 'WNW', [BOMBS, SWORD3, SPIN])
t('NHF', 'S', 'N')
t('NHF', 'S', 'ENE', [BOMBS])
t('NHF', 'S', 'ESE', [SWORD])

t('NHF', 'WSW', 'WNW', [CAPE, BOMBS, SWORD3, SPIN], [FLIPPERS, BOMBS, SWORD3, SPIN])
t('NHF', 'WSW', 'N', [CAPE], [FLIPPERS, BOMBS])
t('NHF', 'WSW', 'S', [CAPE], [FLIPPERS, BOMBS])
t('NHF', 'WSW', 'ENE', [CAPE, BOMBS], [FLIPPERS, BOMBS])
t('NHF', 'WSW', 'ESE', [CAPE], [FLIPPERS, BOMBS])

# --- South Hyrule Field ----------------------------------------------------
t('SHF', 'N', 'E')
t('SHF', 'N', 'W', [SWORD])
t('SHF', 'E', 'W', [SWORD])
t('SHF', 'E', 'N')
t('SHF', 'W', 'E', [SWORD])
t('SHF', 'W', 'N', [SWORD])

# --- Castor Wilds ----------------------------------------------------------
# One crossing: the swamp between the north-east dry bank (E, the Western
# Wood border) and the south-west passage to the Ruins. The region gate
# (cape-or-boots) is the price; the crossing itself adds nothing.
t('CW', 'E', 'SWS')
t('CW', 'SWS', 'E')

# --- Eastern Hills / Western Wood -----------------------------------------
t('EH', 'N', 'W', [BOMBS])
t('EH', 'W', 'N', [BOMBS])
# The top section's two east exits (the user's Aug 21 survey). ENE is a
# ledge pocket: everything flows OUT of it freely (drop down), and the only
# way back UP is flipping yourself with the Cane of Pacci - plus the bombs
# the west/south routes already needed to reach the top section at all.
# ENE and ESE are documented but UNLINKED until whatever lies beyond them
# joins the ring (Minish Woods is blocked), same standing as Castor Wilds'
# SWS; S is the blocked Minish Woods border on the south section.
t('EH', 'ENE', 'ESE')
t('EH', 'ENE', 'N')
t('EH', 'ENE', 'W', [BOMBS])
t('EH', 'ENE', 'S', [BOMBS])
t('EH', 'ESE', 'ENE', [PACCI])
t('EH', 'N', 'ENE', [PACCI])
t('EH', 'W', 'ENE', [BOMBS, PACCI])
t('EH', 'S', 'ENE', [BOMBS, PACCI])
t('WW', 'N', 'E')
t('WW', 'E', 'N')

# --- Royal Valley ----------------------------------------------------------
# A one-way valve: you come in from North Hyrule Field at E and you leave to
# Trilby at S, and there is no way back up. The Lantern is the area's own
# gate (GATES below), so the crossing itself asks for nothing on top of it.
t('RV', 'E', 'S')
impossible('RV', 'S', 'E')

# --- Castle Garden ---------------------------------------------------------
# "Castle Garden requires nothing to traverse" - so if it ever grows a
# second port, every pair between them is free. One port today.

# --- Trilby Highlands ------------------------------------------------------
for a in ('ENE', 'ESE', 'W', 'S'):
    for b in ('ENE', 'ESE', 'W', 'S'):
        if a != b:
            t('TRIL', a, b)
    impossible('TRIL', a, 'N')
# Arriving from Royal Valley puts the player on a LEDGE, not in the region
# proper: the border lands them at Trilby y=16, in a 48-tile pocket
# (tx 4-16, ty 0-4) that a collision flood reads as a component of its own.
# It is not sealed. Walking off its south edge at tx 14, 15 or 16 drops the
# player to ty 9, inside Trilby's 334-tile main body - measured by walking
# it, after a flood said otherwise and the user corrected me. A flood
# cannot see a ledge: the tile you hop from reads as ordinary floor and the
# tiles you hop over read as solid wall. tools/quickstart/component_map.py
# exists now to catch exactly this.
#
# So these four are free, as the user's survey said all along. The drop is
# one-way, which is why nothing in Trilby reaches N (the rows above).
for b in ('W', 'S', 'ENE', 'ESE'):
    t('TRIL', 'N', b)

# --- Lon Lon Ranch ---------------------------------------------------------
t('LLR', 'WNW', 'WSW', [BOMBS])
t('LLR', 'WNW', 'SWS')
t('LLR', 'WNW', 'ESE', [CAPE], [FLIPPERS], [PACCI])
t('LLR', 'WNW', 'N', [PACCI])

t('LLR', 'WSW', 'WNW', [BOMBS])
t('LLR', 'WSW', 'N', [BOMBS, PACCI])
t('LLR', 'WSW', 'SWS', [BOMBS])
t('LLR', 'WSW', 'ESE', [BOMBS, CAPE], [BOMBS, FLIPPERS], [BOMBS, PACCI])

t('LLR', 'N', 'WNW')
t('LLR', 'N', 'WSW', [BOMBS])
t('LLR', 'N', 'SWS')
t('LLR', 'N', 'ESE', [CAPE], [FLIPPERS], [PACCI])

# --- The TRUE ESE, and two east ports this model does not have yet --------
#
# User, Aug 2026: "There is a connection in LLR that I forgot about. It is
# the true ESE." Their survey of it, verbatim:
#
#     ESE -> SWS               nothing
#     ESE -> W                 bombs
#     ESE -> WNW               nothing
#     ESE -> NWN               cane of pacci
#     ESE -> upper middle E    nothing (except the boulder-in-hole)
#     ESE -> middle E          rocs cape or zoras flippers or cane of pacci
#
# The first four map onto ports this model already has - W is WSW and NWN
# is N - and they REPLACE the old ESE rows wholesale. The old rows were
# written for a different connection and every one of them was dearer
# (ESE->WNW wanted the Cape; it is free from the true ESE).
#
# The last two name ports that do not exist here: Lon Lon Ranch's east side
# apparently has THREE connections - this ESE plus an "upper middle E" and a
# "middle E" - where the model has one. They cannot be added from the survey
# alone, because a port is only half a fact: the other half is what is on
# the other side of it, and nothing here says which region or room those two
# reach. Recorded, not invented. See the roadmap's world-reachability
# section - this is exactly the kind of hole the reachability extractor is
# meant to close by measurement rather than by asking.
t('LLR', 'ESE', 'SWS')
t('LLR', 'ESE', 'WSW', [BOMBS])
t('LLR', 'ESE', 'WNW')
t('LLR', 'ESE', 'N', [PACCI])
# PENDING (need the destinations before they can be ports):
#   t('LLR', 'ESE', 'E_UPPER_MIDDLE')                        # free
#   t('LLR', 'ESE', 'E_MIDDLE', [CAPE], [FLIPPERS], [PACCI])

t('LLR', 'SWS', 'WSW', [BOMBS])
t('LLR', 'SWS', 'WNW')
t('LLR', 'SWS', 'N', [PACCI])
t('LLR', 'SWS', 'ESE', [CAPE], [FLIPPERS], [PACCI])

# ----------------------------------------------------------------- links ----
# (region, port) -> (region, port). Each entry's provenance is recorded so a
# reader can tell a measured edge from an assumed one; there are no assumed
# ones today.

LINKS = {}
LINK_WHY = {}


def link(a, ap, b, bp, why):
    LINKS[(a, ap)] = (b, bp)
    LINKS[(b, bp)] = (a, ap)
    LINK_WHY[frozenset({(a, ap), (b, bp)})] = why


BORDER = 'WARP_TYPE_BORDER row in transitions.c'
SEAM = 'scroll seam, from gAreaRoomHeaders room rectangles'

link('CG', 'S', 'NHF', 'N', BORDER)
link('NHF', 'S', 'SHF', 'N', BORDER + ' (the QUICKSTART town bridge)')
link('NHF', 'ESE', 'LLR', 'WNW', SEAM)
link('NHF', 'WSW', 'TRIL', 'ENE', SEAM)
link('NHF', 'ENE', 'VF', 'WSW', BORDER)
link('NHF', 'WNW', 'RV', 'E', BORDER)
link('LLR', 'ESE', 'LH', 'W', BORDER)
link('LLR', 'N', 'VF', 'S', BORDER)
link('LLR', 'WSW', 'TRIL', 'ESE', BORDER + ' (QUICKSTART; vanilla is the town gate)')
link('LLR', 'SWS', 'EH', 'N', SEAM)
link('TRIL', 'N', 'RV', 'S', BORDER)
link('TRIL', 'W', 'CREN', 'E', BORDER)
link('TRIL', 'S', 'WW', 'N', SEAM)
link('SHF', 'E', 'EH', 'W', SEAM)
link('SHF', 'W', 'WW', 'E', SEAM)
link('WW', 'W', 'CW', 'E', BORDER + ' (restored under QUICKSTART with the expansion)')
link('CW', 'SWS', 'WR', 'N', BORDER)


def derive_links():
    """Re-derive the seam links from the ROM, so the table above stays honest.

    Returns a list of (roomA, edge, roomB) for the ring's rooms."""
    import seam_audit as S
    NAMES = {0: 'WW-S', 1: 'SHF', 2: 'EH-S', 3: 'EH-C', 4: 'EH-N',
             5: 'LLR', 6: 'NHF', 7: 'TRIL', 8: 'WW-N', 9: 'WW-C'}
    out = []
    rects = S.room_rects(3)
    for r, (x, y, w, h) in sorted(rects.items()):
        if r not in NAMES:
            continue
        for o, (ox, oy, ow, oh) in sorted(rects.items()):
            if o == r or o not in NAMES:
                continue
            if x + w == ox and oy < y + h and y < oy + oh:
                span = (max(y, oy), min(y + h, oy + oh))
                out.append((NAMES[r], 'east', NAMES[o], span, (y, y + h)))
            if y + h == oy and ox < x + w and x < ox + ow:
                span = (max(x, ox), min(x + w, ox + ow))
                out.append((NAMES[r], 'south', NAMES[o], span, (x, x + w)))
    return out


# ------------------------------------------------------------- the routing --

def cross(region, frm, to):
    """What it costs to get from one port of a region to another."""
    if frm == to:
        return FREE
    return TRAVERSAL.get((region, frm, to))


def exits_from(region, port):
    """Every (exitPort, cost, nextRegion, nextPort) leaving `region` after
    arriving at `port`, skipping the impossible and the unsurveyed.

    Leaving by the port you came in through is included, and costs nothing -
    the player is already standing on it. That is the only way out of a
    one-port region like Castle Garden, and it is why such a region can only
    ever be a route's first or last stop: any other position would make the
    next hop a backtrack, which generate() refuses."""
    out = []
    for p in REGIONS[region]['ports']:
        c = FREE if p == port else cross(region, port, p)
        if not c:                     # None = unsurveyed, IMPOSSIBLE = one-way
            continue
        nxt = LINKS.get((region, p))
        if nxt is None:
            continue
        out.append((p, c, nxt[0], nxt[1]))
    return out


def generate(seed, stops=3, start=('CG', 'S'), pooled_only=True, tries=400):
    """A route of `stops` regions, and the bill to walk it.

    Returns (hops, bill) where each hop is a dict, or None if the seed could
    not produce one. Backtracking into the region just left is refused, so a
    route reads as a journey rather than a pace."""
    rng = random.Random(seed)
    for _ in range(tries):
        region, port = start
        hops = []
        bill = GATES.get(region, FREE)
        prev = None
        ok = True
        for _step in range(stops):
            cand = [e for e in exits_from(region, port)
                    if e[2] != prev and (not pooled_only or REGIONS[e[2]].get('pooled', True))]
            if not cand:
                ok = False
                break
            exit_port, cost, nxt_region, nxt_port = rng.choice(cand)
            gate = GATES.get(nxt_region, FREE)
            step_bill = both(both(bill, cost), gate)
            if not step_bill:
                ok = False
                break
            bill = step_bill
            hops.append(dict(region=region, enter=port, exit=exit_port, cost=cost,
                             to=nxt_region, to_port=nxt_port))
            prev, region, port = region, nxt_region, nxt_port
        if ok and hops:
            hops.append(dict(region=region, enter=port, exit=None, cost=FREE,
                             to=None, to_port=None))
            return hops, bill
    return None


def describe(hops, bill):
    lines = []
    for h in hops:
        if h['exit'] is None:
            lines.append(f"  arrive {REGIONS[h['region']]['name']} at {h['enter']}  <- win condition here")
        else:
            lines.append(f"  {REGIONS[h['region']]['name']} {h['enter']} -> {h['exit']}"
                         f"  [{show(h['cost'])}]  then {REGIONS[h['to']]['name']} {h['to_port']}")
    lines.append(f"  BILL: {show(bill)}")
    return '\n'.join(lines)


# ------------------------------------------------------------- consistency --

def check():
    problems = []
    notes = []
    for (region, frm, to), _ in sorted(TRAVERSAL.items()):
        if frm not in REGIONS[region]['ports']:
            problems.append(f'{region}: traversal from unknown port {frm}')
        if to not in REGIONS[region]['ports']:
            problems.append(f'{region}: traversal to unknown port {to}')
    for rid, r in REGIONS.items():
        for p in r['ports']:
            if (rid, p) not in LINKS:
                problems.append(f'{rid}.{p} has no link - nothing on the other side')
    for rid, r in REGIONS.items():
        if not r.get('pooled', True):
            continue
        for a, b in itertools.permutations(r['ports'], 2):
            if (rid, a, b) not in TRAVERSAL:
                notes.append(f'{rid}: {a} -> {b} not surveyed')
    for key, (b, bp) in sorted(LINKS.items()):
        if LINKS.get((b, bp)) != key:
            problems.append(f'link {key} -> {b}.{bp} is not mutual')
    return problems, notes


def main():
    args = sys.argv[1:]
    print('=== regions ===')
    for rid, r in REGIONS.items():
        gate = f'  GATE {show(GATES[rid])}' if rid in GATES else ''
        pooled = '' if r.get('pooled', True) else '  (not in the pool yet)'
        print(f'  {rid:<5} {r["name"]:<22} ports {",".join(r["ports"]):<28}{gate}{pooled}')

    print('\n=== links (both directions) ===')
    seen = set()
    for (a, ap), (b, bp) in sorted(LINKS.items()):
        k = frozenset({(a, ap), (b, bp)})
        if k in seen:
            continue
        seen.add(k)
        print(f'  {a}.{ap:<4} <-> {b}.{bp:<4}   {LINK_WHY[k]}')

    print('\n=== seam geometry, re-derived from the ROM ===')
    try:
        for a, edge, b, span, full in derive_links():
            half = 'whole edge'
            if span != full:
                mid = (full[0] + full[1]) / 2.0
                centre = (span[0] + span[1]) / 2.0
                low, high = ('north', 'south') if edge == 'east' else ('west', 'east')
                half = f'{low} end' if centre < mid else f'{high} end'
            print(f'  {a:<5} {edge:<5} edge -> {b:<5} ({half})')
    except Exception as exc:
        print('  (could not read the ROM:', exc, ')')

    problems, notes = check()
    print(f'\n=== consistency: {len(problems)} problem(s), {len(notes)} unsurveyed pair(s) ===')
    for p in problems:
        print('  PROBLEM', p)
    for n in notes:
        print('  todo   ', n)

    print('\n=== can a run get these? ===')
    for k in sorted(OBTAINABLE):
        ok, why = OBTAINABLE[k]
        print(f'  {k:<9} {"yes" if ok else "NO ":<4} {why}')

    print('\n=== ports gated behind something no run can obtain ===')
    dead = 0
    for (region, frm, to), dnf in sorted(TRAVERSAL.items()):
        if dnf and not walkable(dnf):
            print(f'  {region}.{frm} -> {region}.{to}  needs {show(dnf)}')
            dead += 1
    print(f'  {dead} traversal(s) currently impossible for reasons other than geography')

    if '--stats' in args:
        n = int(args[args.index('--stats') + 1])
        import collections
        bills = collections.Counter()
        demand = collections.Counter()
        bad = 0
        for s_ in range(n):
            got = generate(s_, stops=3)
            if not got:
                bad += 1
                continue
            _hops, bill = got
            bills[show(bill)] += 1
            if not walkable(bill):
                bad += 1
            for term in bill:
                for it in term:
                    demand[it] += 1
        print(f'\n=== {n} routes sampled ===')
        for b, c in bills.most_common():
            print(f'  {c:>4}x  {b}')
        print(f'  routes with no obtainable way through: {bad}')
        print('  item demand (times an item appears in some winning term):')
        for it, c in demand.most_common():
            print(f'    {it:<9} {c}')

    n = 6
    if '--paths' in args:
        n = int(args[args.index('--paths') + 1])
    print(f'\n=== {n} generated routes (3 regions, starting Castle Garden south) ===')
    for s in range(n):
        got = generate(s, stops=3)
        print(f'\nseed {s}:')
        print(describe(*got) if got else '  no route')


if __name__ == '__main__':
    main()
