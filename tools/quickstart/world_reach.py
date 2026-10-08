"""The in-room reachability survey, as data.

WHAT THIS IS. overworld_paths.py answers "standing at one ENTRANCE of a
region, what does it take to reach another entrance". This answers the finer
question underneath it: "standing at one spot in a region, what does it take
to reach each PLACE in it" - every door, cave mouth, pocket and sub-area,
not just the borders. It is the user's walked survey of the mapexplore
build, transcribed.

HOW TO READ AN ENTRY. Every region has ONE start point, the spot the survey
was walked from. A destination's requirement is what it costs to reach that
destination FROM THAT START, and nothing else. Reaching it from a different
entrance may be cheaper, dearer, or impossible - see INCOMPLETE below.

REQUIREMENTS ARE NOT ONLY ITEMS. Half of what gates this world is world
STATE: a kinstone fusion that lays a bridge, a boulder pushed into a hole, a
maze solved, four switches thrown. Those are tokens here exactly like items
are, because the algebra does not care - a requirement is a set of facts
that must hold, and "holds the Flippers" and "boulder 1 is in its hole" are
both facts. Keeping them in the same vocabulary is what will let the sphere
filler treat "do this fusion" as a placeable step rather than a special
case.

INCOMPLETE, BY CONSTRUCTION. The user's own caveat, and it matters enough to
repeat: rooms like North Hyrule Field and Castor Wilds have several routes
into the same pocket, and a survey walked from one start point only finds
the ones that start there. Dropping the player somewhere else opens routes
this table does not know about. Treat every requirement here as an UPPER
BOUND on the cost from that start, never as proof that no cheaper way
exists.

    python3 tools/quickstart/world_reach.py           # the table
    python3 tools/quickstart/world_reach.py --check   # consistency + conflicts
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# ------------------------------------------------------------- vocabulary --
# Items. Names match overworld_paths.py where they overlap, so the two
# tables can be compared without a translation layer.
SWORD = 'sword'                # any sword at all (the Smith's)
SPIN = 'spin'
# The block push. The survey recorded it in vanilla's terms - a level-two
# sword plus the Spin Attack for Lon Lon's and Trilby's blocks, level three
# for Royal Valley's and the North Hyrule Field graveyard pocket's - because
# vanilla's duplication technique needs one clone per step up in block size,
# and the equipped sword is what decides how many clones you get.
#
# That pricing is retired. The mode reassigns the whole mechanic to the POWER
# BRACELETS, which move every size of block with no clones at all (see
# UpdatePlayerCollision's ACT_TILE_114 case). One token, one item, and the
# sword2-vs-sword3 disagreement the survey turned up stops existing - it was
# never two different obstacles, only two different block sizes.
BRACELETS = 'bracelets'
BOMBS = 'bombs'
BOW = 'bow'
FLIPPERS = 'flippers'
CAPE = 'cape'
PACCI = 'pacci'
LANTERN = 'lantern'
GRIP = 'grip'
BOOTS = 'boots'
MITTS = 'mitts'                # Mole Mitts, "dig mitts" in the survey
GUST = 'gust_jar'
MINISH = 'minish_cap'          # being able to shrink
# The Ocarina of Wind. A gate rather than a convenience in exactly one
# place: Lake Hylia's wind-crest pocket has no walkable route in at all, so
# warping to the crest IS the entrance. Testable at run time, unlike MINISH,
# so a place priced at it is offerable rather than invisible.
OCARINA = 'ocarina'
LONLON_KEY = 'lonlon_key'
GRAVEYARD_KEY = 'graveyard_key'
# The two golden-kinstone gates (Oct 2026). Each run rolls them open or
# sealed at its start (GF_GATE_SEALED_BIT in game.c): open, the way stands
# as it always did; sealed, the gate wants its golden piece(s) fused at the
# stone itself, and those pieces are key items the economy pays out
# (QUICKSTART_ITEM_GOLD_*). Testable at run time - game.c reads the gate's
# own state (rolled open, or the fusion done) into the held mask - so a
# place behind one is offerable, never invisible.
SOURCE_FLOW = 'source_flow'      # the Source of the Flow stone at cave #1's mouth, Veil Falls
STATUES = 'golden_statues'       # the three sleeping statues at Castor Wilds' south-west passage

# World state. Anything that is not carried but must have HAPPENED.
FUSION = 'fusion'                        # an unnamed kinstone fusion
STORY = 'story_flags'
MAZE = 'maze_solved'                     # Royal Valley's lost woods
# "This place exists and the survey could not find a way to it." Not a gate -
# an admission. Untestable at run time exactly like MAZE, so anything carrying
# it is invisible to the chain placer instead of being offered on a guess.
# Only the two derived regions (Minish Woods, Lake Hylia) use it; a walked
# survey of either should delete every one it replaces.
UNSURVEYED = 'unsurveyed'
SWITCHES4 = 'boomerang_switches_4'       # all four chamber switches thrown
BOULDER = lambda region, n: 'boulder:%s:%d' % (region, n)

# WHICH boulder is which, and the save flag that says it is in its hole.
#
# Every one-way boulder in the ring is a MOVEABLE_OBJECT_MANAGER entry in
# data/map/entity_headers.s (manager subtype 0x20): it creates the
# PUSHABLE_ROCK at the rock's spot, or ON the hole when its flag is already
# set, and pushableRock.c sets that flag the moment the rock settles into
# the hole (sub_0808A644). The flag is a LOCAL flag of the room's area, so
# it is wiped with everything else at run start (GameTask_Transition's
# FLAG_BANK_1.. sweep) - a new run gets its boulders back - and it can be
# read from anywhere with CheckLocalFlagByBank(GetFlagBankOffset(area), n).
# That is what makes a boulder token TESTABLE at run time (Oct 2026): the
# auto-fill that used to solve every hole on arrival is retired, the
# player pushes them, and the chain placer sees which ones are in.
#
# Numbers are the user's (survey of 2026-10-06); flag indices are the USA
# build's (the .else branch of each entity list - EU_JP's are two lower in
# Lon Lon Ranch). hole = where the rock ends up, rock = where it starts.
#   key                 area               flag  rock         hole
BOULDER_FLAGS = {
    BOULDER('LLR', 1):  ('HYRULE_FIELD', 0x7b),   # rock (488,904) hole (472,904), the south-east corner
    BOULDER('LLR', 2):  ('HYRULE_FIELD', 0x7c),   # rock (216,904) hole (232,904), by the Goron cave
    BOULDER('LLR', 3):  ('HYRULE_FIELD', 0x7a),   # rock (184,200) hole (168,200), the north field's west gate
    BOULDER('TRIL', 1): ('HYRULE_FIELD', 0x92),   # rock (344,664) hole (344,648), pushed north from the south
    BOULDER('WW-N', 1): ('HYRULE_FIELD', 0x93),   # rock (408,424) hole (424,424), pushed east toward South Field
    BOULDER('CW', 1):   ('CASTOR_WILDS', 0x15),   # rock (536,808) hole (536,792)
    BOULDER('CW', 2):   ('CASTOR_WILDS', 0x16),   # rock (696,920) hole (680,920)
    BOULDER('CW', 3):   ('CASTOR_WILDS', 0x1e),   # rock (696,328) hole (696,344)
    BOULDER('CREN', 1): ('MT_CRENEL', 0x3f),      # TOP: rock (760,88) hole (744,88)
    BOULDER('CREN', 2): ('MT_CRENEL', 0x40),      # TOP: rock (952,136) hole (712,24) - numbering ASSUMED, see the report
    BOULDER('LH', 1):   ('LAKE_HYLIA', 0x07),     # rock (40,536) hole (40,520), on the arrival shore - NOT surveyed
    BOULDER('WR', 1):   ('RUINS', 0x25),          # ENTRANCE: rock (184,488) hole (168,488) - NOT surveyed
    BOULDER('WR', 2):   ('RUINS', 0x2a),          # FORTRESS_ENTRANCE: rock (136,88) hole (120,88) - NOT surveyed
}
# Lon Lon Ranch's north field. The user: "the LLR house key is basically
# equivalent to having boulder #3 pushed in (but the reverse is not true)",
# and every north-field row says so. One token for the pair keeps a row
# that already has three alternatives from needing six: the game sets it
# when boulder 3's flag is up OR the Lon Lon Key is held.
LLR_NORTH = 'llr_north'

FREE = []                                # reachable with nothing extra

# --------------------------------------------------------------- the table --
# start:  (area, room, local x, y) - where the survey was walked from
# dests:  (area, room, local x, y, requirement, note)
#
# A requirement is a list of ALTERNATIVE terms; each term is a list of tokens
# that must ALL hold. [] means free; [[A], [B]] means A or B; [[A, B]] means
# A and B.

SURVEY = {}


def region(key, name, start, room_req=None, note=''):
    SURVEY[key] = dict(name=name, start=start, dests=[], room_req=room_req or [], note=note)


# Two different "no requirement list" cases, and collapsing them cost four
# places their gate: omitting the argument means FREE, and passing None
# means the survey looked and found NO WAY IN from its start. The old
# signature turned both into [[]] - free - so Lon Lon's Veil Falls pocket,
# Trilby's Royal Valley pocket and the two Wind Ruins armos pockets all read
# as walk-in-and-take-it, and reach.h was generated saying so.
_OMITTED = object()


def d(key, area, room, x, y, req=_OMITTED, note=''):
    SURVEY[key]['dests'].append(dict(area=area, room=room, local=(x, y),
                                     req=([[]] if req is _OMITTED else req), note=note))


# ------------------------------------------------------------- entrances --
# A survey key can be an ENTRANCE of a region rather than the region itself
# (Oct 2026). The region's own key stays the start the ring's drop lands at;
# 'LLR@E903' is the same ranch walked from where the south-east Lake Hylia
# border puts the player. Rooms are priced from each entrance separately,
# and gen_reach floods ENTRANCES, not regions, so what a room costs depends
# on where the run actually came in. ENTRANCES maps the key to its region's
# key; LINKS says which entrance a given exit row lands at.
ENTRANCES = {}


def entrance(key, of, name, start, room_req=None, note=''):
    region(key, name, start, room_req, note)
    ENTRANCES[key] = of


def copy_dests(src, dst, drop=(), add=(), skip=()):
    """Replay `src`'s rows into `dst`: `drop` tokens are removed from every
    term (a gate this entrance is already past), `add` tokens are appended
    to every term (a gate this entrance is behind), `skip` coordinates are
    left out (the entrance's own landing, or a row not re-measured)."""
    for e in SURVEY[src]['dests']:
        if (e['area'], e['room'], e['local']) in skip or (e['area'], e['room']) in skip:
            continue
        req = e['req']
        if req is not None:
            new = []
            # FREE is [] - one empty term, not no terms - or an added gate
            # would vanish from exactly the rows it matters most for.
            for term in (req or [[]]):
                t = [tok for tok in term if tok not in drop]
                for tok in add:
                    if tok not in t:
                        t.append(tok)
                k = tuple(sorted(t))
                if k not in [tuple(sorted(x)) for x in new]:
                    new.append(t)
            req = new
        SURVEY[dst]['dests'].append(dict(area=e['area'], room=e['room'], local=e['local'],
                                         req=req, note=e['note']))


# Where an exit row lands. (survey key, (area, room, x, y) of one of that
# key's rows) -> the survey key of the ENTRANCE on the far side. A row with
# a None requirement is a crossing the survey found impossible from that
# start, listed so gen_reach does not fall back to a free default for it.
# Crossings between regions that have no entry here keep the old reading:
# any node of the one region reaches the other's own start at its entry
# price.
LINKS = {}


def link(key, area, room, x, y, to):
    LINKS[(key, area, room, x, y)] = to


# ------------------------------------------------------- becoming Minish --
# What it costs to SHRINK inside each ring region.
#
# The user: "In order to reach a Minish room, there are a few requirements:
# 1) the player must have the Minish cap ... 2) there must be a tree
# stump/stone/pot nearby for the player to transform into a Minish ... There
# are other regions/rooms, though, where the tree stump/stone/portal is
# initially hidden ... hidden underneath specials trees that the player must
# ram with the Pegasus boots to reveal the stump."
#
# Requirement 1 is free: being Minish is PL_MINISH, a player STATE, and
# there is no Minish Cap in item.h to test. Requirement 2 is the whole gate,
# and it is DATA, not a judgement call. A transform point is a
# MINISH_PORTAL_MANAGER (manager subtype 3,
# src/manager/minishPortalManager.c); a TREE_HIDING_PORTAL object sitting on
# top of one is the tree, and treeHidingPortal.c only opens it on
# PLAYER_BOUNCE, which is a Pegasus Boots dash.
#
# Measured by tools/quickstart/minish_portals.py. Two earlier passes got
# this wrong and are worth remembering: looking for portal OBJECTS found
# five points in the whole ring, and widening to every portal-ish object id
# "found" Lon Lon a free MINISH_SIZED_ENTRANCE - which is a Minish-only
# DOORWAY, since it tests PL_MINISH before it fires. Somewhere to go once
# small is not a way to get small.
#
# This table reproduces all four of the user's own observations
# independently: Lon Lon free (stumps at (344,544) and (280,48) with no tree
# on them), Eastern Hills free via its South third (72,128), and North
# Hyrule Field and Hyrule Castle Garden both tree-hidden.
#
# A region is FREE if ANY of its rooms has an unhidden stump - the thirds of
# Eastern Hills and Western Wood are one walkable region across scroll
# seams, so a stump in one third serves all of it.
MINISH_PORTAL = {
    'QS_REGION_CG':   [[BOOTS]],   # (840,240), under a tree
    'QS_REGION_NHF':  [[BOOTS]],   # (808,528), under a tree
    'QS_REGION_SHF':  [[BOOTS]],   # (88,544), under a tree
    'QS_REGION_LLR':  [],          # (344,544) and (280,48) in the open
    'QS_REGION_TRIL': [],          # (56,160)
    'QS_REGION_EH':   [],          # (72,128), in the South third
    'QS_REGION_WW':   [],          # (120,128), in the South third
    'QS_REGION_CW':   [],          # (152,192)
    'QS_REGION_WR':   [],          # (56,480) and (168,48)
    'QS_REGION_MW':   [],          # (296,880) and (920,944)
    'QS_REGION_LH':   [],          # (184,496) and (296,392) in the open
    'QS_REGION_CREN': [],          # (760,216)
    # Royal Valley has NO transform point in any of its rooms. A Minish
    # destination there stays untestable - the player would have to arrive
    # already small, which nothing in the model can currently prove.
    'QS_REGION_RV':   None,
}

# ------------------------------------------------------------ entry cost --
# A region's `room_req` is what it costs to move around INSIDE the region
# once you are standing in it. That is not the same question as what it
# costs to GET IN, and for a region whose only crossing is priced on the
# NEIGHBOUR's side - as an exit row in the neighbour's own block - the entry
# cost is simply not present in this table's per-region field. gen_reach was
# reading room_req as the entry price, so those regions came out free.
#
# ENTRY states the crossing cost directly, per ring region, and gen_reach
# prefers it over room_req wherever it has a row. Only regions whose entry
# price differs from their room_req belong here; everything else is left to
# the derivation.
ENTRY = {
    # The only real way in is North Hyrule Field's WNW border
    # (link NHF WNW <-> RV E). NHF's own block prices the walk to that
    # border at bombs AND bracelets - it is reachable only through the
    # TO_GRAVEYARD pocket, which is behind a bombable wall and a lift.
    # Trilby's N port is a link on paper only: TRIL's own first row is the
    # pocket that port sits in, and it is marked "only reachable from Royal
    # Valley", so the crossing runs one way, downhill, out of the valley.
    #
    # The user, who has played it: "Royal Valley requires the power
    # bracelets to be able to reach." The survey agrees; it had simply
    # recorded the price in the neighbour's block, where the region table
    # could not see it. Royal Valley read FREE and was counted reachable in
    # 100% of 50,000 simulated runs.
    'QS_REGION_RV': [[BOMBS, BRACELETS]],
}

# --- South Hyrule Field ----------------------------------------------------
#
# RE-WALKED 2026-10-06 from three of its entrances. The old block was one
# start whose stamp was taken mid-transition; its rows are below, replaced
# where the new walk priced the same place and carried over where it did
# not (marked). The user's entrance names: "North" is the border from North
# Hyrule Field (the QUICKSTART town bridge, landing (504,16)); "NNE" is the
# scroll seam into Eastern Hills North at (997,121); "NNW" is the scroll
# seam into Western Wood North at (8,111).
region('SHF', 'South Hyrule Field', ('HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 504, 16),
       note='the north entrance, from North Hyrule Field; walked 2026-10-06')
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 504, 16, FREE, 'exit north -> HYRULE_TOWN; the start itself')
link('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 504, 16, 'HT')
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 111, [[SWORD]], 'exit NNW -> WESTERN_WOODS_NORTH (468,431), which is the dead-end side of its boulder')
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 997, 121, [[SWORD]], 'exit NNE -> EASTERN_HILLS_NORTH')
d('SHF', 'CAVES', 'SOUTH_HYRULE_FIELD_FAIRY_FOUNTAIN', 120, 120, [[BOMBS]])
d('SHF', 'CAVES', 'SOUTH_HYRULE_FIELD_RUPEE', 120, 120, [[SWORD, FUSION]])
d('SHF', 'HOUSE_INTERIORS_2', 'LINKS_HOUSE_ENTRANCE', 120, 120, FREE,
  "Link's house; the old STORY token is gone - the mode sets the flags at boot")
d('SHF', 'HOUSE_INTERIORS_2', 'LINKS_HOUSE_SMITH', 96, 104, FREE)
d('SHF', 'HOUSE_INTERIORS_2', 'LINKS_HOUSE_BEDROOM', 88, 40, FREE)
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 86, 574, [[SWORD, BOOTS]],
  'the Minish stump under a tree; the boots reveal it')
d('SHF', 'MINISH_HOUSE_INTERIORS', 'SOUTH_HYRULE_FIELD', 120, 120, [[SWORD, BOOTS, MINISH]])
d('SHF', 'MINISH_CAVES', 'OUTSIDE_LINKS_HOUSE', 120, 93, [[SWORD, BOOTS, MINISH, FLIPPERS]])
d('SHF', 'TREE_INTERIORS', 'SOUTH_HYRULE_FIELD_HEART_PIECE', 120, 120, [[SWORD, FUSION]])
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 772, 375, [[SWORD, FUSION]], 'kinstone gold chest')
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 708, 301, [[SWORD]], 'wind crest')
# Carried over from the old block, not re-measured on 2026-10-06.
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 264, 266, [[FLIPPERS]], 'carried over (pre-2026-10-06 start), a spot across water')
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 952, 294, [[PACCI, SWORD]], 'carried over (pre-2026-10-06 start), a cane pocket')
# The four scroll seams the walk did not price, from the port model
# (overworld_paths.py: SHF N->W costs a sword, N->E nothing). Coordinates
# are the middle of each seam band, not a stamp.
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 400, [[SWORD]], 'exit west 320-480 -> WESTERN_WOODS_CENTER; PORT MODEL, not walked')
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 584, [[SWORD]], 'exit west 480-688 -> WESTERN_WOODS_SOUTH; PORT MODEL, not walked')
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 1000, 352, FREE, 'exit east 224-480 -> EASTERN_HILLS_CENTER; PORT MODEL, not walked')
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 1000, 584, FREE, 'exit east 480-688 -> EASTERN_HILLS_SOUTH; PORT MODEL, not walked')
for _k in ('SHF',):
    link(_k, 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 504, 16, 'NHF')
    link(_k, 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 111, 'WW-N@E')
    link(_k, 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 997, 121, 'EH-N')
    link(_k, 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 400, 'WW-C')
    link(_k, 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 584, 'WW-S')
    link(_k, 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 1000, 352, 'EH-C')
    link(_k, 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 1000, 584, 'EH-S')

# From the NNE seam (Eastern Hills North). The landing pocket holds the
# heart-piece tree, the gold chest and the wind crest; a sword (bushes)
# gets out of it westward. The user's list prices the smith's room at
# "nothing" while the house entrance it is behind costs a sword - read as a
# slip, priced at the sword, and flagged for re-measurement.
entrance('SHF@NNE', 'SHF', 'South Hyrule Field (from Eastern Hills North)',
         ('HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 997, 121), note='walked 2026-10-06')
d('SHF@NNE', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 504, 16, [[SWORD]], 'exit north -> HYRULE_TOWN')
link('SHF@NNE', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 504, 16, 'HT')
d('SHF@NNE', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 111, [[SWORD]], 'exit NNW -> WESTERN_WOODS_NORTH')
d('SHF@NNE', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 997, 121, FREE, 'exit NNE -> EASTERN_HILLS_NORTH; the start itself')
d('SHF@NNE', 'CAVES', 'SOUTH_HYRULE_FIELD_FAIRY_FOUNTAIN', 120, 120, [[SWORD, BOMBS]])
d('SHF@NNE', 'HOUSE_INTERIORS_2', 'LINKS_HOUSE_ENTRANCE', 120, 120, [[SWORD]])
d('SHF@NNE', 'HOUSE_INTERIORS_2', 'LINKS_HOUSE_SMITH', 96, 104, [[SWORD]], 'the list says "nothing" behind a sword-priced entrance; taken as a slip')
d('SHF@NNE', 'HOUSE_INTERIORS_2', 'LINKS_HOUSE_BEDROOM', 88, 40, [[SWORD]])
d('SHF@NNE', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 86, 574, [[SWORD, BOOTS]], 'the Minish stump under a tree')
d('SHF@NNE', 'MINISH_HOUSE_INTERIORS', 'SOUTH_HYRULE_FIELD', 120, 120, [[SWORD, BOOTS, MINISH]])
d('SHF@NNE', 'MINISH_CAVES', 'OUTSIDE_LINKS_HOUSE', 120, 93, [[SWORD, BOOTS, MINISH, FLIPPERS]])
d('SHF@NNE', 'TREE_INTERIORS', 'SOUTH_HYRULE_FIELD_HEART_PIECE', 120, 120, [[FUSION]])
d('SHF@NNE', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 772, 375, [[FUSION]], 'kinstone gold chest')
d('SHF@NNE', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 708, 301, FREE, 'wind crest')
d('SHF@NNE', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 400, [[SWORD]], 'exit west 320-480 -> WESTERN_WOODS_CENTER; PORT MODEL')
d('SHF@NNE', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 584, [[SWORD]], 'exit west 480-688 -> WESTERN_WOODS_SOUTH; PORT MODEL')
d('SHF@NNE', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 1000, 352, FREE, 'exit east 224-480 -> EASTERN_HILLS_CENTER; PORT MODEL')
d('SHF@NNE', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 1000, 584, FREE, 'exit east 480-688 -> EASTERN_HILLS_SOUTH; PORT MODEL')

# From the NNW seam (Western Wood North's boulder side). Water gives a
# second way to Link's house for a run with the Flippers and no sword. The
# heart-piece tree's line in the list is cut off after "sword and"; priced
# as from the north entrance (sword and the fusion) and flagged.
entrance('SHF@NNW', 'SHF', 'South Hyrule Field (from Western Wood North)',
         ('HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 111), note='walked 2026-10-06')
d('SHF@NNW', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 504, 16, [[SWORD]], 'exit north -> HYRULE_TOWN')
link('SHF@NNW', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 504, 16, 'HT')
d('SHF@NNW', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 111, FREE, 'exit NNW -> WESTERN_WOODS_NORTH; the start itself (the list prices it at a sword)')
d('SHF@NNW', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 997, 121, [[SWORD]], 'exit NNE -> EASTERN_HILLS_NORTH')
d('SHF@NNW', 'CAVES', 'SOUTH_HYRULE_FIELD_FAIRY_FOUNTAIN', 120, 120, [[SWORD, BOMBS], [FLIPPERS, BOMBS]])
d('SHF@NNW', 'HOUSE_INTERIORS_2', 'LINKS_HOUSE_ENTRANCE', 120, 120, [[SWORD], [FLIPPERS]])
d('SHF@NNW', 'HOUSE_INTERIORS_2', 'LINKS_HOUSE_SMITH', 96, 104, [[SWORD], [FLIPPERS]])
d('SHF@NNW', 'HOUSE_INTERIORS_2', 'LINKS_HOUSE_BEDROOM', 88, 40, [[SWORD], [FLIPPERS]])
d('SHF@NNW', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 86, 574, [[BOOTS, SWORD], [BOOTS, FLIPPERS]], 'the Minish stump under a tree')
d('SHF@NNW', 'MINISH_HOUSE_INTERIORS', 'SOUTH_HYRULE_FIELD', 120, 120, [[BOOTS, MINISH, SWORD], [BOOTS, MINISH, FLIPPERS]])
d('SHF@NNW', 'MINISH_CAVES', 'OUTSIDE_LINKS_HOUSE', 120, 93, [[BOOTS, MINISH, FLIPPERS]])
d('SHF@NNW', 'TREE_INTERIORS', 'SOUTH_HYRULE_FIELD_HEART_PIECE', 120, 120, [[SWORD, FUSION]], 'the list is cut off after "sword and"; assumed sword and the fusion')
d('SHF@NNW', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 772, 375, [[FUSION, SWORD]], 'kinstone gold chest')
d('SHF@NNW', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 708, 301, [[SWORD]], 'wind crest')
d('SHF@NNW', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 400, [[SWORD]], 'exit west 320-480 -> WESTERN_WOODS_CENTER; PORT MODEL')
d('SHF@NNW', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 584, [[SWORD]], 'exit west 480-688 -> WESTERN_WOODS_SOUTH; PORT MODEL')
d('SHF@NNW', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 1000, 352, [[SWORD]], 'exit east 224-480 -> EASTERN_HILLS_CENTER; PORT MODEL')
d('SHF@NNW', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 1000, 584, [[SWORD]], 'exit east 480-688 -> EASTERN_HILLS_SOUTH; PORT MODEL')
for _k in ('SHF@NNE', 'SHF@NNW'):
    link(_k, 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 504, 16, 'NHF')
    link(_k, 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 111, 'WW-N@E')
    link(_k, 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 997, 121, 'EH-N')
    link(_k, 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 400, 'WW-C')
    link(_k, 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 8, 584, 'WW-S')
    link(_k, 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 1000, 352, 'EH-C')
    link(_k, 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 1000, 584, 'EH-S')

# --- Eastern Hills North ---------------------------------------------------
region('EH-N', 'Eastern Hills North', ('HYRULE_FIELD', 'EASTERN_HILLS_NORTH', -6, 428))
d('EH-N', 'HYRULE_FIELD', 'EASTERN_HILLS_NORTH', 249, 539, FREE, 'exit')
d('EH-N', 'HYRULE_FIELD', 'EASTERN_HILLS_NORTH', 463, 427, [[BOMBS]], 'exit')
d('EH-N', 'HOUSE_INTERIORS_4', 'FARM_HOUSE', -904, 136, [[BOMBS]])
d('EH-N', 'DIG_CAVES', 'EASTERN_HILLS', 56, 181, [[BOMBS, MITTS]])
d('EH-N', 'HYRULE_FIELD', 'EASTERN_HILLS_NORTH', 460, 80, [[BOMBS, PACCI]], 'exit')
d('EH-N', 'HYRULE_FIELD', 'EASTERN_HILLS_NORTH', 308, -2, [[BOMBS]], 'exit')
d('EH-N', 'HYRULE_FIELD', 'EASTERN_HILLS_NORTH', 268, 532, FREE, 'exit')
# The seam the start stands on, so the crossing into South Hyrule Field's
# NNE pocket has a row to hang its (free) price on. Lon Lon Ranch's south
# border lands at the north edge, behind the (308,-2) bombs - a landing
# this block has not been walked from; see the 2026-10-06 report.
d('EH-N', 'HYRULE_FIELD', 'EASTERN_HILLS_NORTH', 0, 428, FREE, 'exit west -> SOUTH_HYRULE_FIELD (997,121); the start itself')
link('EH-N', 'HYRULE_FIELD', 'EASTERN_HILLS_NORTH', 0, 428, 'SHF@NNE')
link('EH-N', 'HYRULE_FIELD', 'EASTERN_HILLS_NORTH', 308, -2, 'LLR')

# --- Eastern Hills Center --------------------------------------------------
region('EH-C', 'Eastern Hills Center', ('HYRULE_FIELD', 'EASTERN_HILLS_CENTER', 257, 31))
d('EH-C', 'HYRULE_FIELD', 'EASTERN_HILLS_CENTER', 169, 251, FREE, 'exit')
d('EH-C', 'HYRULE_FIELD', 'EASTERN_HILLS_CENTER', 344, 249, FREE, 'exit')
d('EH-C', 'HYRULE_FIELD', 'EASTERN_HILLS_CENTER', 0, 120, FREE, 'exit west -> SOUTH_HYRULE_FIELD; PORT MODEL (overworld_paths EH W), not walked')
link('EH-C', 'HYRULE_FIELD', 'EASTERN_HILLS_CENTER', 0, 120, 'SHF')
d('EH-C', 'CAVES', 'HILLS_KEESE_CHEST', -712, -1032, [[BOMBS]])

# --- Eastern Hills South ---------------------------------------------------
region('EH-S', 'Eastern Hills South', ('HYRULE_FIELD', 'EASTERN_HILLS_SOUTH', 330, -3))
d('EH-S', 'HYRULE_FIELD', 'EASTERN_HILLS_SOUTH', 465, 170, FREE, 'exit')
d('EH-S', 'HYRULE_FIELD', 'EASTERN_HILLS_SOUTH', 0, 100, FREE, 'exit west -> SOUTH_HYRULE_FIELD; PORT MODEL (overworld_paths EH W), not walked')
link('EH-S', 'HYRULE_FIELD', 'EASTERN_HILLS_SOUTH', 0, 100, 'SHF')
d('EH-S', 'MINISH_HOUSE_INTERIORS', 'HYRULE_FIELD_EXIT', -1032, -856, [[MINISH]])
d('EH-S', 'HYRULE_FIELD', 'EASTERN_HILLS_SOUTH', 167, 8, [[BOMBS]],
  'exit; the survey notes the reverse direction is this table plus bombs')

# --- Lon Lon Ranch ---------------------------------------------------------
#
# RE-WALKED 2026-10-06 from every entrance, with the boulders UNFILLED. The
# ranch is cut in half: boulder 3 (hole (168,200)) is the gate between the
# west corridor - the south, the Trilby and North Field entrances, Veil
# Falls - and the north field, which the ranch house also crosses when the
# Lon Lon Key is held. Boulder 3 is pushed from the north-field side, so a
# player who arrives there walks south for nothing. Boulder 1 (hole
# (472,904)) walls the south-east Lake Hylia landing off from the south;
# it is pushed from that landing only. Boulder 2 (hole (232,904)) guards
# the Goron cave and, per the user, can be pushed once boulder 1 is in by
# a player with the Minish cap. LLR_NORTH is "boulder 3 in OR the key".
#
# The user's numbering is the one used here (the previous block's 2 and 3
# are 1 and 2 now; its 1 was the house door, which is the key).
region('LLR', 'Lon Lon Ranch', ('HYRULE_FIELD', 'LON_LON_RANCH', 298, 968),
       note='the south entrance, from Eastern Hills North; walked 2026-10-06 with the boulders unfilled')
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 298, 968, FREE, 'exit south -> EASTERN_HILLS_NORTH; the start itself')
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 8, 560, [[BOMBS]], 'exit west -> HYRULE_TOWN (1000,240), from the pocket behind a bombable wall')
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 10, 163, FREE, 'exit north-west -> NORTH_HYRULE_FIELD')
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 88, 16, [[PACCI]], 'exit north -> VEIL_FALLS (88,1000), the Lon Lon strip of the falls; open since Oct 2026')
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 712, 445, [[LLR_NORTH]], 'exit east -> LAKE_HYLIA, from the north field')
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 712, 750, [[LLR_NORTH, PACCI, MINISH], [LLR_NORTH, FLIPPERS], [LLR_NORTH, CAPE]],
  "exit east -> LAKE_HYLIA's south-west corner, over water from the north field")
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 712, 903, [[BOULDER('LLR', 1)]], "exit east -> LAKE_HYLIA's south-west corner; the pocket behind boulder 1")
d('LLR', 'GORON_CAVE', 'STAIRS', 120, 120, [[FUSION, BOULDER('LLR', 2)]],
  'the fusion opens the cave; NOT a ? room any more (the user, 2026-10-06)')
d('LLR', 'GORON_CAVE', 'MAIN', 120, 632, [[FUSION, BOULDER('LLR', 2)]],
  'the first chamber; the deeper three are the kinstone-gated miniboss sites')
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 166, 54, None,
  'POCKET at tile (10,3), a gold kinstone chest. Entered from the lower strip of Veil Falls only '
  '(the VF@POCKET entrance below prices it); from inside the ranch there is no way in.')
d('LLR', 'MINISH_CRACKS', 'LON_LON_RANCH_NORTH', 120, 87, [[LLR_NORTH, PACCI, MINISH]])
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 427, 278, [[LLR_NORTH, PACCI, MINISH]], 'POCKET (tornado float)')
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 313, 391, [[LLR_NORTH, BOOTS]], 'the Minish stump under a tree in the north field; the boots reveal it')
d('LLR', 'MINISH_PATHS', 'LON_LON_RANCH', 121, 391, [[LLR_NORTH, BOOTS, MINISH]], 'chest')
d('LLR', 'MINISH_PATHS', 'LON_LON_RANCH', 120, 89, [[LLR_NORTH, BOOTS, MINISH]], 'heart piece')
d('LLR', 'CAVES', 'LON_LON_RANCH_WALLET', 120, 120, [[LLR_NORTH, FUSION]])
d('LLR', 'CAVES', 'LON_LON_RANCH', 168, 216, [[LLR_NORTH, BRACELETS]],
  'the stone inside wants the Power Bracelets; the cave leads up to the Tingle pocket')
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 184, 279, [[LLR_NORTH, BRACELETS]], 'POCKET out of the cave above - Tingle')
d('LLR', 'HOUSE_INTERIORS_4', 'RANCH_HOUSE_EAST', 120, 120, [[LONLON_KEY]])
d('LLR', 'HOUSE_INTERIORS_4', 'RANCH_HOUSE_WEST', 245, 90, [[MINISH], [LONLON_KEY]],
  'carried over (not in the 2026-10-06 lists); the minish route needs the room to keep its vanilla content')


def _llr_links(k):
    link(k, 'HYRULE_FIELD', 'LON_LON_RANCH', 298, 968, 'EH-N')
    link(k, 'HYRULE_FIELD', 'LON_LON_RANCH', 8, 560, 'HT')   # the town's east gate (Oct 2026: the bridge to Trilby is gone)
    link(k, 'HYRULE_FIELD', 'LON_LON_RANCH', 10, 163, 'NHF')
    link(k, 'HYRULE_FIELD', 'LON_LON_RANCH', 712, 445, 'LH')
    link(k, 'HYRULE_FIELD', 'LON_LON_RANCH', 712, 750, 'LH-SW')
    link(k, 'HYRULE_FIELD', 'LON_LON_RANCH', 712, 903, 'LH-SW')
    link(k, 'HYRULE_FIELD', 'LON_LON_RANCH', 88, 16, 'VF@LLR')


_llr_links('LLR')

# The south-east Lake Hylia landing, (712,903). Boulder 1 is pushed from
# here and from nowhere else, so the ranch costs what it costs from the
# south once that is done; the user's list for this start is the south
# list without the (712,903) row.
entrance('LLR@E903', 'LLR', 'Lon Lon Ranch (from the south-east Lake Hylia border)',
         ('HYRULE_FIELD', 'LON_LON_RANCH', 712, 903), note='walked 2026-10-06; boulder 1 is pushed from here')
copy_dests('LLR', 'LLR@E903', skip=[('HYRULE_FIELD', 'LON_LON_RANCH', (712, 903))])
d('LLR@E903', 'HYRULE_FIELD', 'LON_LON_RANCH', 712, 903, FREE, "exit east -> LAKE_HYLIA's south-west corner; the start itself")
_llr_links('LLR@E903')

# The middle Lake Hylia landing, (712,445): the north field. Nothing here
# wants boulder 3 or the key - boulder 3 is pushed from this side - and the
# south exit is free. The user's list omits the (712,903) exit; it keeps
# the south list's price (boulder 1).
entrance('LLR@E445', 'LLR', 'Lon Lon Ranch (from the middle Lake Hylia border)',
         ('HYRULE_FIELD', 'LON_LON_RANCH', 712, 445), note='walked 2026-10-06; the north field')
copy_dests('LLR', 'LLR@E445', drop=(LLR_NORTH,), skip=[('HYRULE_FIELD', 'LON_LON_RANCH', (712, 445))])
d('LLR@E445', 'HYRULE_FIELD', 'LON_LON_RANCH', 712, 445, FREE, 'exit east -> LAKE_HYLIA; the start itself')
_llr_links('LLR@E445')

# The lower Lake Hylia landing, (712,750): the user prices everything from
# here as from (712,445) "plus the Roc's Cape". From the field side the
# crossing takes the Flippers or the Pacci cane and the cap as well; the
# asymmetry is flagged in the report.
entrance('LLR@E750', 'LLR', 'Lon Lon Ranch (from the lower Lake Hylia border)',
         ('HYRULE_FIELD', 'LON_LON_RANCH', 712, 750), note='walked 2026-10-06; the cape gets off the landing')
copy_dests('LLR@E445', 'LLR@E750', add=(CAPE,), skip=[('HYRULE_FIELD', 'LON_LON_RANCH', (712, 750))])
d('LLR@E750', 'HYRULE_FIELD', 'LON_LON_RANCH', 712, 750, FREE, "exit east -> LAKE_HYLIA's south-west corner; the start itself")
_llr_links('LLR@E750')

# The west landing, (8,560), from Trilby Highlands (vanilla's Hyrule Town
# border): a pocket behind a bombable wall. "The same as starting from the
# Southern exit, except add 'and bombs' to every requirement."
entrance('LLR@W', 'LLR', 'Lon Lon Ranch (from Hyrule Town, the west pocket)',
         ('HYRULE_FIELD', 'LON_LON_RANCH', 8, 560), note='walked 2026-10-06; behind a bombable wall')
copy_dests('LLR', 'LLR@W', add=(BOMBS,), skip=[('HYRULE_FIELD', 'LON_LON_RANCH', (8, 560))])
d('LLR@W', 'HYRULE_FIELD', 'LON_LON_RANCH', 8, 560, FREE, 'exit west -> HYRULE_TOWN; the start itself')
_llr_links('LLR@W')

# The north-west landing, (10,163), from North Hyrule Field: the west
# corridor, "the same as starting from the Southern exit".
entrance('LLR@NW', 'LLR', 'Lon Lon Ranch (from North Hyrule Field)',
         ('HYRULE_FIELD', 'LON_LON_RANCH', 10, 163), note='walked 2026-10-06')
copy_dests('LLR', 'LLR@NW', skip=[('HYRULE_FIELD', 'LON_LON_RANCH', (10, 163))])
d('LLR@NW', 'HYRULE_FIELD', 'LON_LON_RANCH', 10, 163, FREE, 'exit north-west -> NORTH_HYRULE_FIELD; the start itself')
_llr_links('LLR@NW')

# The north landing, (88,16), from Veil Falls' Lon Lon strip - open since
# Oct 2026. Priced as from the south: the south list is the ranch from its
# bottom gate, and the north gate opens onto the same south half.
entrance('LLR@N', 'LLR', 'Lon Lon Ranch (from Veil Falls)',
         ('HYRULE_FIELD', 'LON_LON_RANCH', 88, 16), note='walked 2026-10-06; rows copied from the south entrance (inferred)')
copy_dests('LLR', 'LLR@N', skip=[('HYRULE_FIELD', 'LON_LON_RANCH', (88, 16))])
d('LLR@N', 'HYRULE_FIELD', 'LON_LON_RANCH', 88, 16, FREE, 'exit north -> VEIL_FALLS (88,1000); the start itself')
_llr_links('LLR@N')

# The gold-chest pocket, (176,16), from Veil Falls' lower strip. A pocket:
# the chest, and the way back north, and nothing else (the ranch's own
# (166,54) row says no way in from inside).
entrance('LLR@POCKET', 'LLR', "Lon Lon Ranch (the gold-chest pocket, from Veil Falls' lower strip)",
         ('HYRULE_FIELD', 'LON_LON_RANCH', 176, 16), note='Oct 2026; the pocket Veil Falls (176,1000) lands in')
d('LLR@POCKET', 'HYRULE_FIELD', 'LON_LON_RANCH', 166, 54, FREE, 'tile (10,3), the gold kinstone chest')
d('LLR@POCKET', 'HYRULE_FIELD', 'LON_LON_RANCH', 176, 16, FREE, 'exit north -> VEIL_FALLS (176,1000); the start itself')
link('LLR@POCKET', 'HYRULE_FIELD', 'LON_LON_RANCH', 176, 16, 'VF@POCKET')

# --- North Hyrule Field ----------------------------------------------------
# Every row carries the start's own bushes: a sword. Recorded once here
# rather than repeated, exactly as the survey states it.
region('NHF', 'North Hyrule Field', ('HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 1013, 638),
       room_req=[[SWORD]], note='the start is behind bushes - every row costs a sword')
d('NHF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 9, 607, [[CAPE], [FLIPPERS]], 'exit')
d('NHF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 498, 795, FREE, 'exit')
d('NHF', 'TREE_INTERIORS', 'BOOMERANG_SOUTHWEST', -1672, 120, [[FUSION]])
d('NHF', 'CAVES', 'BOOMERANG', 72, 248, [[FUSION]], 'POCKET, one of the four switches')
d('NHF', 'TREE_INTERIORS', 'BOOMERANG_SOUTHEAST', -1928, 120, [[FUSION]])
d('NHF', 'CAVES', 'BOOMERANG', 264, 248, [[FUSION]], 'POCKET, one of the four switches')
d('NHF', 'TREE_INTERIORS', 'BOOMERANG_NORTHEAST', -1416, 120, [[FUSION]])
d('NHF', 'CAVES', 'BOOMERANG', 264, 136, [[FUSION]], 'POCKET, one of the four switches')
d('NHF', 'TREE_INTERIORS', 'BOOMERANG_NORTHWEST', -1160, 120, [[FUSION]])
d('NHF', 'CAVES', 'BOOMERANG', 72, 136, [[FUSION]], 'POCKET, one of the four switches')
d('NHF', 'CAVES', 'BOOMERANG', 168, 216, [[SWITCHES4]], 'the central pocket')
d('NHF', 'TREE_INTERIORS', 'NORTH_HYRULE_FIELD_FAIRY_FOUNTAIN', None, None, [[FUSION]])
d('NHF', 'CAVES', 'NORTH_HYRULE_FIELD_FAIRY_FOUNTAIN', -376, -1432, [[FUSION]],
  'the same fusion as the tree above')
# The east edge, MEASURED (Oct 2026, scratchpad vf_borders.py): borders keep
# the GLOBAL coordinate, so the north half of this edge - the bomb pocket at
# (999,112) - is the Veil Falls crossing (it lands in the falls' North Field
# corridor at (8,639)), and the start itself, (1013,638), is the Lon Lon
# crossing (it lands at the ranch's (10,163)). The old link had the two the
# other way round.
d('NHF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 999, 112, [[BOMBS]], 'exit east, the bomb pocket -> VEIL_FALLS (8,639)')
link('NHF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 999, 112, 'VF@NHF')
link('NHF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 9, 607, 'TRIL')
link('NHF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 498, 795, 'HT')   # the town's north gate (Oct 2026)
d('NHF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 1013, 638, FREE, 'exit east -> LON_LON_RANCH (10,163); the start itself')
link('NHF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 1013, 638, 'LLR@NW')

# North Hyrule Field from Veil Falls: the falls' corridor lands in the bomb
# pocket at (1000,111), and the field's own row prices that pocket at the
# bombs from the start, so the pocket is priced at the bombs the other way
# too. The user confirmed it (second pass, 2026-10-07): leaving the pocket
# takes the bombs.
entrance('NHF@VF', 'NHF', 'North Hyrule Field (from Veil Falls, the east bomb pocket)',
         ('HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 1000, 111), room_req=[[SWORD]],
         note='Oct 2026; measured landing, rows copied from the start with the bombs added; the user confirmed the bombs (second pass)')
copy_dests('NHF', 'NHF@VF', add=(BOMBS,), skip=[('HYRULE_FIELD', 'NORTH_HYRULE_FIELD', (999, 112))])
d('NHF@VF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 999, 112, FREE, 'exit east -> VEIL_FALLS (8,639); the start itself')
link('NHF@VF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 999, 112, 'VF@NHF')
link('NHF@VF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 1013, 638, 'LLR@NW')
link('NHF@VF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 9, 607, 'TRIL')
link('NHF@VF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 498, 795, 'HT')
d('NHF', 'MINISH_CRACKS', 'EAST_HYRULE_CASTLE', -936, 48, [[MINISH, BOOTS]])
d('NHF', 'CAVES', 'TO_GRAVEYARD', -104, 216, [[BOMBS]])
d('NHF', 'CAVES', 'HEART_PIECE_HALLWAY', -1000, -1000, [[BOMBS]])
d('NHF', 'DOJOS', 'TO_GREATBLADE', -392, -56, [[FUSION, FLIPPERS]])
d('NHF', 'DOJOS', 'GREATBLADE', 120, 200, [[FUSION, FLIPPERS]])
d('NHF', 'CAVES', 'TO_GRAVEYARD', 59, 110, [[BOMBS, BRACELETS]], 'POCKET')
d('NHF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 5, 93, [[BOMBS, BRACELETS]],
  'exit, reachable ONLY through the TO_GRAVEYARD pocket above')
link('NHF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 5, 93, 'RV')

# --- Hyrule Castle Garden --------------------------------------------------
# NOT WALKED. Derived from transitions.c (link CG S <-> NHF N is a plain
# WARP_TYPE_BORDER row, no gate on either side) and from the five content
# sites the mode already places in the garden, every one of which is a
# Minish room. The user, who has played it: "Hyrule Castle Garden is always
# guaranteed to be reachable - it directly connects to NHF with no item
# requirement to pass between the two."
#
# Before this block existed the garden had NO survey entry, and gen_reach
# prices a region with no entry at "never". So the one region of the ring
# that costs nothing to walk into was the one region the chain believed it
# could never reach: measured over 50,000 simulated runs, Castle Garden was
# counted reachable in 7% of them - exactly the share of runs that DROP
# there, since the drop region is admitted unconditionally.
#
# SUPPLEMENTED from the vanilla walkthrough (docs/QUICKSTART_GUIDE_FINDINGS.md),
# Oct 2026. Three things the derived block had wrong or missing, each checked
# against the ROM's own data before it was changed:
#   * The two fountain rooms are NOT behind the Minish holes. Vanilla drains
#     each fountain with a kinstone fusion (shared fusions #78/#79 in the
#     guide); the world events are KINSTONE_18 / KINSTONE_35, type 5 "remove
#     water / open path", at (776,72) and (232,72) - the two fountain doors -
#     and both fusers are live in this mode's Castle Garden fuser table
#     (tools/quickstart/kinstone_audit.py). So the price is the fusion.
#   * Grimblade's dojo was missing entirely - the ladder is under bushes in
#     the garden's south-east corner (door at (936,388), bush object at
#     (936,376) in entity_headers.s). A sword is the whole cost. It is content
#     site 16, which the simulation listed as never reachable.
#   * The hedge-maze ladder in the north-west corner leads through
#     HYRULE_CASTLE_CELLAR into the castle's lower hall. Vanilla also makes
#     the player sneak past guards to reach it; this mode clears GUARD_1
#     every frame (QuickStartClearCastleGuards), so the bushes are the cost.
region('CG', 'Hyrule Castle Garden', ('CASTLE_GARDEN', 'MAIN', 504, 480),
       note='derived from the exit list and the site table, not walked; '
            'supplemented from the vanilla guide')
d('CG', 'CASTLE_GARDEN', 'MAIN', 504, 36, FREE, 'exit, south to North Hyrule Field')
d('CG', 'CASTLE_GARDEN_MINISH_HOLES', '0', 136, 104, [[MINISH]])
d('CG', 'CASTLE_GARDEN_MINISH_HOLES', '1', 136, 104, [[MINISH]])
d('CG', 'MINISH_CRACKS', 'HYRULE_CASTLE_GARDEN', 152, 104, [[MINISH]])
#   * The user, having played it: each drained fountain opens TWO ways in,
#     "one is reachable as a full sized link, one is reachable only as
#     Minish Link". Both are behind the drain, so the full-size door is the
#     price and the Minish door is the second term, recorded so nobody
#     re-measures it.
d('CG', 'GARDEN_FOUNTAINS', 'EAST', 120, 80, [[FUSION], [FUSION, MINISH]],
  'the north-east fountain, drained by a kinstone fusion (KINSTONE_18); a '
  'heart piece in vanilla. Two doors once drained: one full-size, one Minish')
d('CG', 'GARDEN_FOUNTAINS', 'WEST', 120, 80, [[FUSION], [FUSION, MINISH]],
  'the north-west fountain, drained by a kinstone fusion (KINSTONE_35); a '
  'fairy fountain in vanilla. Two doors once drained: one full-size, one Minish')
d('CG', 'DOJOS', 'TO_GRIMBLADE', 120, 104, [[SWORD]],
  'ladder under the bushes in the south-east corner; guide: "slash the '
  'bushes there to reveal a ladder leading down"')
d('CG', 'DOJOS', 'GRIMBLADE', 120, 88, [[SWORD]],
  "Grimblade's dojo, through the room above; dark until its torches are lit "
  'in vanilla, which a ? room does not care about')
d('CG', 'HYRULE_CASTLE_CELLAR', '0', 104, 392, [[SWORD]],
  'ladder under the bushes in the north-west hedge alcove; the tunnel lets '
  "out in the castle's lower hall (HYRULE_CASTLE/3). Not a content site - "
  'recorded because it is the way INTO Hyrule Castle')

# --- Royal Valley ----------------------------------------------------------
region('RV', 'Royal Valley', ('ROYAL_VALLEY', 'MAIN', -536, 416),
       note='the only real entrance')
d('RV', 'ROYAL_VALLEY', 'MAIN', 118, 1000, FREE, 'exit')
link('RV', 'ROYAL_VALLEY', 'MAIN', 118, 1000, 'TRIL@N')
d('RV', 'GREAT_FAIRIES', 'GRAVEYARD', 120, 120, [[BOMBS]],
  "the Great Dragonfly Fairy's cave, content site. Added from the vanilla "
  'guide (Oct 2026): "climb down ... see the lonely posts? Place a bomb '
  'between them to blow up an entry" - right at the valley entrance, before '
  'the maze, so bombs are the whole cost from this start')
d('RV', 'ROYAL_VALLEY', 'FOREST_MAZE', -248, -3240, FREE,
  'free to reach; the LANTERN is what solves it. NOTE from the guide: the '
  'maze is a FIXED sequence (up, left, left, up, right, up; south exits it '
  'at once) and the lantern only lets you read the signs that say so - a '
  'player who knows the path walks it dark. See the findings doc for the '
  'design lever this hands Royal Valley.')
# THE MAZE IS FREE (Oct 2026). These rows used to carry LANTERN + MAZE, and
# MAZE was untestable, so everything past the Lost Woods was invisible to the
# chain. The vanilla guide retired both: the maze is a fixed sequence of
# turns (this mode randomises it per run and re-aims vanilla's own signs to
# read it out), and the lantern never opened anything - it lit the sign. For
# a player with no lantern Ezlo now speaks each step on each pass
# (QuickStartMazeMonitor), so the route is knowable with nothing at all. The
# user approved retiring the token; the walk that confirms the dark maze is
# steerable blind is still owed.
d('RV', 'ROYAL_VALLEY', 'MAIN', -888, 440, FREE, 'north of the maze')
d('RV', 'HOUSE_INTERIORS_2', 'DAMPE', -376, -312, FREE)
d('RV', 'ROYAL_VALLEY', 'MAIN', 244, 331, [[GRAVEYARD_KEY]],
  'the gate to the upper pocket - everything above it inherits this')
d('RV', 'ROYAL_VALLEY_GRAVES', 'HEART_PIECE', 120, 120, [[GRAVEYARD_KEY]])
d('RV', 'ROYAL_VALLEY_GRAVES', 'GINA', -168, 280, [[GRAVEYARD_KEY]])
d('RV', 'ROYAL_VALLEY', 'CRYPT', None, None,
  [[GRAVEYARD_KEY, BRACELETS]], 'the royal crypt')

# --- Trilby Highlands ------------------------------------------------------
#
# RE-WALKED 2026-10-06 from four entrances with the boulder UNFILLED. The
# boulder (rock (344,664), hole (344,648)) is pushed north, from the south
# side only, and walls the south-west off from the rest: Percy's treehouse,
# the rupee and fairy-fountain caves, the Keese chest cave, the near half
# of the two-ladder cave and the seam into Western Wood North are "boulder
# in OR the Power Bracelets" from every entrance but the south, where they
# are free and the push is how you leave. The old block was walked with the
# hole auto-filled, which is why it priced the same places free.
region('TRIL', 'Trilby Highlands', ('HYRULE_FIELD', 'TRILBY_HIGHLANDS', 470, 129),
       note='the north-east entrance, from North Hyrule Field; walked 2026-10-06 with the boulder unfilled')
_TB = BOULDER('TRIL', 1)
d('TRIL', 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 470, 129, FREE, 'exit east (north half) -> NORTH_HYRULE_FIELD; the start itself')
d('TRIL', 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 472, 560, FREE, 'exit east (south half) -> HYRULE_TOWN (8,240), the town gate (Oct 2026)')
d('TRIL', 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 8, 414, FREE, 'exit west -> MT_CRENEL/ENTRANCE, Mount Crenel Base')
d('TRIL', 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 363, 953, [[_TB], [BRACELETS]], 'exit south -> WESTERN_WOODS_NORTH; in the boulder pocket')
d('TRIL', 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 32880, -1184, None, 'POCKET at the Royal Valley landing, only reachable from Royal Valley; the valley is inaccessible from here')
d('TRIL', 'TREE_INTERIORS', 'PERCYS_TREEHOUSE', 120, 120, [[_TB], [BRACELETS]], 'in the boulder pocket')
d('TRIL', 'CAVES', 'TRILBY_RUPEE', 120, 120, [[FUSION, _TB], [FUSION, BRACELETS]], 'in the boulder pocket')
d('TRIL', 'CAVES', 'TRILBY_KEESE_CHEST', 120, 120, [[BOMBS, _TB], [BOMBS, BRACELETS]], 'in the boulder pocket')
d('TRIL', 'CAVES', 'TRILBY_FAIRY_FOUNTAIN', 120, 120, [[BOMBS, _TB], [BOMBS, BRACELETS]], 'in the boulder pocket')
d('TRIL', 'CAVES', 'TRILBY_HIGHLANDS', 56, 56, [[_TB], [BRACELETS]],
  "the two-ladder cave's pocket half, tile (3,3): through its pocket door, or from the far half with the bracelets")
d('TRIL', 'CAVES', 'TRILBY_HIGHLANDS', 296, 56, FREE, "the two-ladder cave's near half, tile (18,3)")
d('TRIL', 'CAVES', 'BOTTLE_BUSINESS_SCRUB', 25, 90, [[BOMBS]], 'THE bombable wall off the near half of the two-ladder cave; not a ? room')
d('TRIL', 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 280, 455, FREE, 'kinstone gold chest')
d('TRIL', 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 393, 71, [[FUSION]], 'gold kinstone chest')
d('TRIL', 'DIG_CAVES', 'TRILBY_HIGHLANDS', 88, 184, [[MITTS]], 'dig cave entrance 1, from the field door at (136,148)')
d('TRIL', 'DIG_CAVES', 'TRILBY_HIGHLANDS', 71, 70, [[MITTS]], 'gold chest from entrance 1')
d('TRIL', 'DIG_CAVES', 'TRILBY_HIGHLANDS', 299, 103, [[MITTS]], 'gold chest from entrance 1')
d('TRIL', 'DIG_CAVES', 'TRILBY_HIGHLANDS', 136, 104, [[MITTS]], 'the ladder up to the Tingle pocket')
d('TRIL', 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 183, 135, [[MITTS]], 'POCKET: the Tingle fusion, up the ladder from the dig cave')
d('TRIL', 'MINISH_HOUSE_INTERIORS', 'NEXT_TO_KNUCKLE', 120, 120, [[MITTS, MINISH]])
d('TRIL', 'DIG_CAVES', 'TRILBY_HIGHLANDS', 264, 215, [[FUSION, MITTS, FLIPPERS], [FUSION, MITTS, CAPE]],
  'dig cave entrance 2: a fusion lays land in front of the dig spot at (264,249), then the Flippers or the cape reach it')
d('TRIL', 'DIG_CAVES', 'TRILBY_HIGHLANDS', 231, 183, [[FUSION, MITTS, FLIPPERS], [FUSION, MITTS, CAPE]], 'gold chest from entrance 2')
d('TRIL', 'DIG_CAVES', 'TRILBY_HIGHLANDS', 424, 106, [[FUSION, MITTS, FLIPPERS], [FUSION, MITTS, CAPE]], 'the ladder down to the fiery cave, from entrance 2')
d('TRIL', 'CAVES', 'TRILBY_MITTS_FAIRY_FOUNTAIN', 184, 40, [[FUSION, MITTS, FLIPPERS], [FUSION, MITTS, CAPE]])


def _tril_links(k):
    link(k, 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 470, 129, 'NHF')
    link(k, 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 472, 560, 'HT')   # the town's west gate (Oct 2026)
    link(k, 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 8, 414, 'CREN-BASE')
    link(k, 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 363, 953, 'WW-N')
    link(k, 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 32880, -1184, 'RV')


_tril_links('TRIL')

# The south seam, from Western Wood North: the boulder pocket itself. The
# push is free from here, so the whole region is.
entrance('TRIL@S', 'TRIL', 'Trilby Highlands (from Western Wood North)',
         ('HYRULE_FIELD', 'TRILBY_HIGHLANDS', 363, 953), note='walked 2026-10-06; the boulder is pushed from here')
copy_dests('TRIL', 'TRIL@S', drop=(_TB,), skip=[('HYRULE_FIELD', 'TRILBY_HIGHLANDS', (363, 953))])
d('TRIL@S', 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 363, 953, FREE, 'exit south -> WESTERN_WOODS_NORTH; the start itself')
_tril_links('TRIL@S')

# The east landing (472,560), from Lon Lon Ranch's bombable pocket. Same
# as the north-east.
entrance('TRIL@E', 'TRIL', 'Trilby Highlands (from Hyrule Town)',
         ('HYRULE_FIELD', 'TRILBY_HIGHLANDS', 472, 560), note='walked 2026-10-06')
copy_dests('TRIL', 'TRIL@E')
_tril_links('TRIL@E')

# The Royal Valley landing: a pocket that drops into the main body one
# way. Same prices as the north-east once down.
entrance('TRIL@N', 'TRIL', 'Trilby Highlands (from Royal Valley)',
         ('HYRULE_FIELD', 'TRILBY_HIGHLANDS', 40, 16), note='walked 2026-10-06; a one-way drop out of the landing pocket')
copy_dests('TRIL', 'TRIL@N', skip=[('HYRULE_FIELD', 'TRILBY_HIGHLANDS', (32880, -1184))])
_tril_links('TRIL@N')

# --- Western Wood North ----------------------------------------------------
#
# RE-WALKED 2026-10-06 from all four entrances with the boulder UNFILLED.
# The boulder (rock (408,424), hole (424,424)) sits right in front of the
# seam from South Hyrule Field and is pushed east, from inside: from the
# west, north and south entrances the region is one open walk and that
# seam costs nothing (you push it); from South Hyrule Field the landing is
# a vestibule from which EVERYTHING is "blocked by boulder" - the token,
# which is only ever set from the far side.
region('WW-N', 'Western Wood North', ('HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 343, 0),
       note='the north entrance, from Trilby Highlands; walked 2026-10-06 with the boulder unfilled')
_WB = BOULDER('WW-N', 1)
d('WW-N', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 343, 0, FREE, 'exit north -> TRILBY_HIGHLANDS (363,953); the start itself')
d('WW-N', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 6, 97, FREE, 'exit west -> CASTOR_WILDS')
d('WW-N', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 284, 636, FREE, 'exit south -> WESTERN_WOODS_CENTER')
d('WW-N', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 33, 633, [[FUSION]], "exit south -> WESTERN_WOODS_CENTER's Percy pocket; the fusion lays the way")
d('WW-N', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 468, 431, FREE, 'exit east -> SOUTH_HYRULE_FIELD (8,111); the boulder is in front of it and is pushed from here')
d('WW-N', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 199, 74, [[FUSION, MITTS]], 'kinstone dig site; the fusion clears the branch, the mitts dig the prize')
d('WW-N', 'TREE_INTERIORS', 'WESTERN_WOODS_HEART_PIECE', 120, 120, [[FUSION]])
d('WW-N', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 235, 263, [[FUSION]], 'POCKET: kinstone gold chest')
# Carried over from the old block, not re-measured on 2026-10-06.
d('WW-N', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 416, 648, [[FUSION]],
  'carried over: POCKET entered from Western Wood Center, with a second fusion-only pocket inside it')
d('WW-N', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', -848, -1656, [[FUSION]], 'carried over: POCKET (mid-transition stamp)')


def _wwn_links(k):
    link(k, 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 343, 0, 'TRIL@S')
    link(k, 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 6, 97, 'CW')
    link(k, 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 284, 636, 'WW-C')
    link(k, 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 33, 633, 'WW-C')
    link(k, 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 468, 431, 'SHF@NNW')


_wwn_links('WW-N')

entrance('WW-N@W', 'WW-N', 'Western Wood North (from Castor Wilds)',
         ('HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 6, 97), note='walked 2026-10-06')
copy_dests('WW-N', 'WW-N@W', skip=[('HYRULE_FIELD', 'WESTERN_WOODS_NORTH', (6, 97))])
d('WW-N@W', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 6, 97, FREE, 'exit west -> CASTOR_WILDS; the start itself')
_wwn_links('WW-N@W')

entrance('WW-N@S', 'WW-N', 'Western Wood North (from Western Wood Center)',
         ('HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 284, 636), note='walked 2026-10-06')
copy_dests('WW-N', 'WW-N@S', skip=[('HYRULE_FIELD', 'WESTERN_WOODS_NORTH', (284, 636))])
d('WW-N@S', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 284, 636, FREE, 'exit south -> WESTERN_WOODS_CENTER; the start itself')
_wwn_links('WW-N@S')

# The vestibule behind the boulder, where the seam from South Hyrule Field
# lands. Every row is the boulder token: nothing here is walkable until it
# has been pushed from the far side, earlier in the run.
entrance('WW-N@E', 'WW-N', 'Western Wood North (from South Hyrule Field, behind the boulder)',
         ('HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 468, 431), note='walked 2026-10-06; a vestibule - everything is blocked by the boulder')
copy_dests('WW-N', 'WW-N@E', add=(_WB,), skip=[('HYRULE_FIELD', 'WESTERN_WOODS_NORTH', (468, 431))])
d('WW-N@E', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 468, 431, FREE, 'exit east -> SOUTH_HYRULE_FIELD; the start itself')
_wwn_links('WW-N@E')

# --- Western Wood Center ---------------------------------------------------
region('WW-C', 'Western Wood Center', ('HYRULE_FIELD', 'WESTERN_WOODS_CENTER', 277, -2))
d('WW-C', 'HYRULE_FIELD', 'WESTERN_WOODS_CENTER', 48, -3, [[FUSION]],
  'POCKET, gated by the same fusion that opens WW-N (48,633)')
d('WW-C', 'HOUSE_INTERIORS_2', 'PERCY', 120, -88, [[FUSION]], 'inside that pocket')
d('WW-C', 'HYRULE_FIELD', 'WESTERN_WOODS_CENTER', 414, 15, FREE, 'exit')
d('WW-C', 'HYRULE_FIELD', 'WESTERN_WOODS_CENTER', 277, 0, FREE, 'exit north -> WESTERN_WOODS_NORTH (284,636); the start itself')
link('WW-C', 'HYRULE_FIELD', 'WESTERN_WOODS_CENTER', 277, 0, 'WW-N@S')
d('WW-C', 'HYRULE_FIELD', 'WESTERN_WOODS_CENTER', 414, 158, FREE, 'exit')
d('WW-C', 'HYRULE_FIELD', 'WESTERN_WOODS_CENTER', 307, 154, FREE, 'exit')

# --- Western Wood South ----------------------------------------------------
region('WW-S', 'Western Wood South', ('HYRULE_FIELD', 'WESTERN_WOODS_SOUTH', 307, -2))
d('WW-S', 'HYRULE_FIELD', 'WESTERN_WOODS_SOUTH', 421, 12, FREE, 'exit')
d('WW-S', 'MINISH_HOUSE_INTERIORS', 'HYRULE_FIELD_SOUTHWEST', 104, -856, [[MINISH]])

# --- Castor Wilds ----------------------------------------------------------
# The whole region costs cape-or-boots to be in at all; every row below is on
# top of that, which is what room_req means.
region('CW', 'Castor Wilds', ('CASTOR_WILDS', 'MAIN', 1000, 33329),
       room_req=[[CAPE], [BOOTS]], note='swamp crossing is the price of entry')
d('CW', 'CASTOR_WILDS', 'MAIN', 741, 515, FREE, 'a small pocket of land')
d('CW', 'CASTOR_WILDS', 'MAIN', 537, 798, FREE, 'BOULDER 1')
d('CW', 'CASTOR_WILDS', 'MAIN', 682, 926, [[FLIPPERS]], 'BOULDER 2')
d('CW', 'CASTOR_WILDS', 'MAIN', 697, 344, FREE, 'BOULDER 3')
d('CW', 'CASTOR_CAVES', 'SOUTH', 120, 152,
  [[FLIPPERS, SWORD], [BOULDER('CW', 1), BOW, MINISH, SWORD],
   [BOULDER('CW', 1), BOULDER('CW', 2), SWORD]],
  'three routes: neither boulder in, boulder 1 only, or both')
d('CW', 'CASTOR_WILDS', 'MAIN', 39, 952, [[BOULDER('CW', 1), STATUES], [BOULDER('CW', 2), STATUES]],
  'exit to the southern pocket, and south over the border into the Wind Ruins; the three statues at tiles '
  '(1-3,58-59) stand aside only once all three are fused, or the run rolled their gate open')
# The Ruins hang off this one crossing: the link prices it at the row above
# instead of the ring adjacency's default (the Ruins' own swamp kit).
link('CW', 'CASTOR_WILDS', 'MAIN', 39, 952, 'WR')
d('CW', 'CASTOR_CAVES', 'NORTH', 296, 120, FREE, 'right-hand pocket of a two-entrance room')
d('CW', 'CASTOR_CAVES', 'HEART_PIECE', 120, 120, [[FLIPPERS]])
d('CW', 'DOJOS', 'TO_SCARBLADE', -648, -56, [[FLIPPERS, FUSION]])
d('CW', 'DOJOS', 'SCARBLADE', 120, 200, [[FLIPPERS, FUSION]])
d('CW', 'CASTOR_WILDS_DIG_CAVE', '0', 776, 404, [[MITTS]])
d('CW', 'DOJOS', 'SWIFTBLADE_I', -904, 136,
  [[BOULDER('CW', 1)], [FLIPPERS, SWORD], [MINISH, SWORD]])
d('CW', 'MINISH_CRACKS', 'CASTOR_WILDS_NORTH', -136, -120, [[MINISH, FUSION]],
  'the fusion unlocks a lily pad that ferries the player to the entrance')
d('CW', 'MINISH_PATHS', 'BOW', -232, 728, [[MINISH, FLIPPERS], [MINISH, GUST]],
  'a long water hallway - only aquatic or flying content belongs here')
d('CW', 'MINISH_CRACKS', 'CASTOR_WILDS_NEXT_TO_BOW', -1160, -120, [[MINISH, FUSION]],
  'behind MINISH_PATHS/BOW; the fusion is UNCONFIRMED in the survey')
d('CW', 'MINISH_CRACKS', 'CASTOR_WILDS_BOW', -1384, 48, [[MINISH, FUSION]],
  'same as the room above; fusion UNCONFIRMED')
d('CW', 'MINISH_CRACKS', 'CASTOR_WILDS_WEST', -392, -120, [[MINISH, FUSION]], 'lily-pad fusion')
d('CW', 'MINISH_CAVES', 'SOUTHEAST_WATER_1', -296, 232, [[FUSION, FLIPPERS]],
  'the same lily pad as CASTOR_WILDS_WEST')
d('CW', 'MINISH_CAVES', '2', 117, 280, [[FUSION, FLIPPERS]], 'the other half of that cave')
d('CW', 'MINISH_CRACKS', 'CASTOR_WILDS_MIDDLE', -648, -120, [[MINISH, FUSION, FUSION]],
  'the lily-pad fusion AND a second fusion for a second lily pad')
d('CW', 'CASTOR_CAVES', 'DARKNUT', -376, -216, FREE)
d('CW', 'CASTOR_DARKNUT', 'HALL', 392, -168, FREE)
d('CW', 'CASTOR_DARKNUT', 'MAIN', 134, 216, FREE)

# --- Wind Ruins ------------------------------------------------------------
region('WR', 'Wind Ruins', ('RUINS', 'ENTRANCE', 32812, -2624),
       room_req=[[CAPE], [BOOTS]],
       note='only reachable through Castor Wilds, so it inherits the swamp price')
# The region's own start room (Oct 2026, the redesign's P1.5): the pool
# landing (game.c's region pool row for the Ruins) and the room the Castor
# Wilds crossing arrives in. A start is free by definition - the player is
# standing in it - but the room test (QuickStartReachTestRoom) prices a
# room by its survey row, and this one had none, so a ? site or a wave in
# the entrance room read "never". The row says what the start says.
d('WR', 'RUINS', 'ENTRANCE', 216, 456, FREE, 'the region start itself')
d('WR', 'CASTOR_CAVES', 'WIND_RUINS', -328, 8, [[BOMBS]])
d('WR', 'MINISH_CRACKS', 'RUINS_ENTRANCE', -1640, 40, [[MINISH]])
d('WR', 'MINISH_CRACKS', 'RUINS_TEKTITE', -904, -120, [[MINISH]])
d('WR', 'MINISH_CAVES', 'RUINS', -392, 184, [[MINISH]])
d('WR', 'RUINS', 'BELOW_FORTRESS_ENTRANCE', 347, 39, None,
  'POCKET with two chests, behind a vanilla gate that opens when some armos '
  'are killed - a candidate to re-appropriate as a ? event')
d('WR', 'RUINS', 'FORTRESS_ENTRANCE', None, None, None,
  'vanilla blocks this pocket behind another kill-the-enemies event - same '
  're-appropriation candidate')


# --- Hyrule Town -----------------------------------------------------------
#
# The fifteenth region (Oct 2026, the redesign's P2): the square, with every
# door shut by containment, so the town is ONE room and its four gates. Not
# walked by the user: measured instead (tools/quickstart/town_survey.py) -
# the floor floods to a single 2,331-tile component from all four gates'
# landings (vanilla's own coordinates) and from the drop, with no ledge,
# water or wall between them, so every exit is free from the start. The
# landings on the far side are the field nodes that already had those
# coordinates: South Hyrule Field's north start (504,16), North Hyrule
# Field's south gate (498,795), Lon Lon's west pocket (8,560, LLR@W) and
# Trilby's east landing (472,560, TRIL@E).
region('HT', 'Hyrule Town', ('HYRULE_TOWN', 'MAIN', 520, 664),
       note='measured, not walked: one component from every gate (town_survey.py)')
d('HT', 'HYRULE_TOWN', 'MAIN', 520, 664, FREE, 'the drop, a little south of the square; the start itself')
d('HT', 'HYRULE_TOWN', 'MAIN', 504, 24, FREE, 'exit north -> NORTH_HYRULE_FIELD (504,792)')
d('HT', 'HYRULE_TOWN', 'MAIN', 504, 952, FREE, 'exit south -> SOUTH_HYRULE_FIELD (504,16)')
d('HT', 'HYRULE_TOWN', 'MAIN', 8, 240, FREE, 'exit west -> TRILBY_HIGHLANDS (472,560)')
d('HT', 'HYRULE_TOWN', 'MAIN', 1000, 240, FREE, 'exit east -> LON_LON_RANCH (8,560), the west pocket')
link('HT', 'HYRULE_TOWN', 'MAIN', 504, 24, 'NHF')
link('HT', 'HYRULE_TOWN', 'MAIN', 504, 952, 'SHF')
link('HT', 'HYRULE_TOWN', 'MAIN', 8, 240, 'TRIL@E')
link('HT', 'HYRULE_TOWN', 'MAIN', 1000, 240, 'LLR@W')


# --- Mt Crenel -------------------------------------------------------------
#
# READ THE DIRECTION OF TRAVEL BEFORE READING THE ROWS. Every other region
# here was surveyed from the spot the player ARRIVES at. Mt Crenel was
# surveyed from a waypoint deep inside it - the Cavern of Flames entrance -
# and walked DOWNHILL, while a player coming from Trilby Highlands arrives at
# the bottom and climbs UP. So these requirements are the cost of the
# survey's route, which is the reverse of the player's, and the uphill price
# simply is not in the data. The user said as much: "there are a lot of
# one-way gates going from this starting point to this exit; going the other
# way, the requirements list might look different."
#
# Two things follow, and both err toward offering the chain placer LESS.
#
# The REGION price is grip + bombs. Not because the survey says so - it says
# nothing about getting in - but because those are the two most expensive
# things it shows anywhere on the stretch between the mountain's entrance and
# the rest of it, and pricing the way IN at the worst thing on the way OUT is
# the conservative reading. If the real climb is cheaper, the cost is
# variety, not a stranded run.
#
# The one-way CANE gate the survey describes is NOT priced into the rows
# below it, and that is deliberate rather than an oversight: the lower half
# has its own way out of the mountain entirely (MT_CRENEL/ENTRANCE), so a
# player who drops through the gate without the cane is not stranded - they
# just cannot climb back UP without it. Content in the lower half is safe;
# what a run cannot do is bounce between the two halves.
region('CREN', 'Mt Crenel', ('MT_CRENEL', 'CAVERN_OF_FLAMES_ENTRANCE', 101, 271),
       room_req=[[GRIP, BOMBS]],
       note='surveyed downhill from inside; the player arrives uphill')

# The upper half, above the one-way cane gate.
d('CREN', 'CAVE_OF_FLAMES', 'ENTRANCE', 136, 168, FREE)
d('CREN', 'MELARIS_MINE', 'MAIN', 159, 290, [[MINISH]])
d('CREN', 'CRENEL_MINISH_PATHS', 'MELARI', 120, 154, [[MINISH]])
# The mine's three side rooms. NOT separately walked - these are the mine's
# own three vanilla WARP_TYPE_AREA doors (gExitList_MelarisMine_Main[2..4]),
# each landing at the arrival the row itself names, so they cost exactly
# what the mine costs and nothing more. Rows matter here because
# QuickStartReachRoomOk refuses a room with no row at all, and the
# south-west one is a content site: without these it could never host a
# gated placement no matter what the player was carrying.
d('CREN', 'MINISH_HOUSE_INTERIORS', 'MELARI_MINES_SOUTHWEST', 120, 40, [[MINISH]])
d('CREN', 'MINISH_HOUSE_INTERIORS', 'MELARI_MINES_SOUTHEAST', 120, 40, [[MINISH]])
d('CREN', 'MINISH_HOUSE_INTERIORS', 'MELARI_MINES_EAST', 36, 86, [[MINISH]])
d('CREN', 'CRENEL_CAVES', 'EXIT_TO_MINES', 184, 152, [[MINISH]])
d('CREN', 'CRENEL_CAVES', 'PILLAR_CAVE', 56, 78, [[MINISH]])
d('CREN', 'MT_CRENEL', 'CAVERN_OF_FLAMES_ENTRANCE', 472, 200, [[MINISH]])
d('CREN', 'CRENEL_CAVES', 'BRIDGE_SWITCH', 72, 456, [[MINISH]])
d('CREN', 'CRENEL_CAVES', 'BLOCK_PUSHING', 568, 200, [[MINISH]])
d('CREN', 'MT_CRENEL', 'CAVERN_OF_FLAMES_ENTRANCE', 520, 40, [[MINISH, CAPE], [MINISH, PACCI]])
d('CREN', 'CRENEL_CAVES', 'BLOCK_PUSHING', 88, 440, [[MINISH, CAPE], [MINISH, PACCI]],
  'one-way: enterable from the far side, exitable only the way you came')

# Past the one-way cane gate. Free to fall into from above; the cane is what
# it costs to climb back, and the mountain's own entrance is the way out.
d('CREN', 'CRENEL_CAVES', 'GRIP_RING', 120, 120, [[BOMBS]])
d('CREN', 'CRENEL_CAVES', 'TO_GRAYBLADE', 120, 240, [[GRIP]])
d('CREN', 'DOJOS', 'GRAYBLADE', 120, 160, [[GRIP, BRACELETS]],
  'the block push - priced at the bracelets like every other one')
d('CREN', 'MT_CRENEL', 'CENTER', 504, 120, FREE)
d('CREN', 'MT_CRENEL', 'WALL_CLIMB', 160, 377, [[GRIP]], 'by the fusion-revealed chest')
d('CREN', 'GREAT_FAIRIES', 'CRENEL', 120, 120, [[GRIP, BOMBS]],
  "the Great Mayfly Fairy's cave, content site. Added from the vanilla guide "
  '(Oct 2026): half-way up Crenel Wall, "get on the right-side ledge, and '
  'bomb the wall at its end" - so the climb plus a bomb')
d('CREN', 'MT_CRENEL', 'TOP', 240, 151, [[GRIP]])
d('CREN', 'MT_CRENEL', 'WALL_CLIMB', 104, 121, [[GRIP]])
d('CREN', 'CRENEL_CAVES', 'HERMIT', 120, 120, [[GRIP]])
d('CREN', 'CRENEL_DIG_CAVE', '0', 56, 325, [[GRIP, MITTS]])
d('CREN', 'MT_CRENEL', 'TOP', 553, 72, [[GRIP]])
d('CREN', 'CRENEL_MINISH_PATHS', 'RAIN', 34, 70, [[GRIP, MINISH]])
# The boulder-hole puzzle: with hole 2 filled this is grip alone, without it
# grip plus a portal. Both terms recorded; the boulder token has no run-time
# test, so in practice the placer sees only the minish term and passes.
d('CREN', 'MT_CRENEL', 'TOP', 904, 64, [[GRIP, MINISH], [GRIP, BOULDER('CREN', 2)]],
  'by the transformation stone')
d('CREN', 'CRENEL_CAVES', 'BLOCK_PUSHING', 424, 40, [[MINISH, GRIP]])
d('CREN', 'MT_CRENEL', 'CAVERN_OF_FLAMES_ENTRANCE', 296, 40, [[GRIP, MINISH]])
d('CREN', 'MT_CRENEL', 'ENTRANCE', 861, 54, [[GRIP]])
d('CREN', 'CRENEL_CAVES', 'LADDER_TO_SPRING_WATER', 120, 136, [[GRIP, BOMBS]])
d('CREN', 'MT_CRENEL', 'ENTRANCE', 730, 309, [[GRIP, BOMBS]])
d('CREN', 'CRENEL_MINISH_PATHS', 'SPRING_WATER', 128, 792, [[GRIP, BOMBS, MINISH]])
d('CREN', 'CRENEL_CAVES', 'HINT_SCRUB', 120, 120, [[GRIP, BOMBS]])
d('CREN', 'MT_CRENEL', 'ENTRANCE', 994, 416, [[GRIP]], 'exit, back down to Trilby')

# --- Minish Woods and Lake Hylia -------------------------------------------
#
# NOT WALKED. Every block above this one is the user walking the mapexplore
# build and writing down what each place cost. These two are DERIVED, and the
# difference matters enough to say before the rows: the destinations are the
# rooms' own vanilla exit lists (src/data/transitions.c, so the coordinates
# and the room names are exact), and the requirements come from flooding the
# live collision grid out of the running game from the tile the player really
# arrives on - tools/quickstart/door_reach.py, which is what produced the
# numbers quoted below.
#
# A flood sees GEOMETRY, not gates. It can prove a door is walkable with
# nothing at all; it cannot tell a wall from a wall-with-a-bomb-crack. So the
# rows split in two:
#
#   * doors the flood REACHES are recorded FREE, which is a fact about the
#     room and is safe to hand the chain placer;
#   * doors it does not reach carry UNSURVEYED, an untestable token exactly
#     like MINISH or MAZE. The placer can never satisfy it, so those places
#     are invisible rather than wrongly offered. That is the same
#     conservative direction the Mt Crenel block argues for, taken further
#     because there is even less to go on.
#
# Replace these blocks with a walked survey when one exists. Until then the
# two regions are honest about being thin: a walkable arena, their border
# home, one reachable door each, and everything else marked unknown.
#
# MINISH WOODS. 63x63 tiles, 1195 open, THIRTY-TWO components. The west-edge
# arrival lands in a 277-tile band across the middle of the room, and that
# band touches the west edge and nothing else - not the north edge (the Lake
# Hylia border), not the south, not the east. The stump mazes, the tree
# hollows and the Minish cracks are all separate components. Letting the
# sword cut shrubs adds ten tiles and changes nothing.
region('MW', 'Minish Woods', ('MINISH_WOODS', 'MAIN', 8, 424),
       note="the user's walked survey, Sep 2026, from the west-central seam")
# WALKED. This block was flood-derived guesswork until the user walked it;
# almost everything below is a real measurement now, and the shape of the
# region turned out to be quite unlike what the flood suggested.
#
# THE ONE THING TO KNOW ABOUT MINISH WOODS: most of it is not reachable from
# the seam at all. It is reachable through MINISH VILLAGE, which is reachable
# through a Minish path, which wants the Minish Cap and (probably) the
# Flippers. Everything below marked "via the village" inherits that, which is
# why a region that looks like open woodland prices most of its contents at
# two key items.
#
# A NOTE ON THE START. The user described the west-central seam as the one
# "shared by Lon Lon Ranch". The ROM disagrees and so does a walk: Minish
# Woods' west border rows go to EASTERN_HILLS_NORTH (north half) and
# EASTERN_HILLS_SOUTH (south half), and tools/quickstart/region_walk.py has
# driven EH-North -> MW and MW -> EH-North for real. Lon Lon Ranch is flush
# against the woods' NORTH edge with no border row at all (see "Flush on the
# map, no crossing" in docs/QUICKSTART_TRAVERSAL_AUDIT.md). Treated as a slip
# of the pen about which neighbour, not about which seam - the coordinates
# match the west-central one exactly - but it is worth confirming, because if
# there really is a Lon Lon crossing here the region graph gains an edge.
d('MW', 'HYRULE_FIELD', 'EASTERN_HILLS_NORTH', 456, 429, FREE,
  'exit; the border the player arrives through, walked both ways')
d('MW', 'HYRULE_FIELD', 'EASTERN_HILLS_SOUTH', 456, 160, FREE, 'exit')

# --- free from the seam ---------------------------------------------------
d('MW', 'MINISH_WOODS', 'MAIN', 200, 374, FREE,
  'golden kinstone chest, tile (12,23) - reaching it costs nothing')
d('MW', 'MINISH_WOODS', 'MAIN', 410, 699, FREE, 'heart piece, tile (25,43)')
d('MW', 'TREE_INTERIORS', 'MINISH_WOODS_BUSINESS_SCRUB', 120, 120, [[FUSION]],
  "the business scrub's tree, tile (7,7). Was FREE with a flag on it - the "
  "survey said 'kinstone fusion maybe?' and a collision flood reached the "
  "door with nothing. The flood was wrong about the gate, not the geometry: "
  "the vanilla guide opens this tree with Fusion #13 (the Castor Wilds "
  "business scrub), KINSTONE_27's world event fires at (528,456), which is "
  "this door, and this mode clears gSave.kinstones at boot and pre-fuses "
  "only the three Castor statues - so the tree starts CLOSED every run. "
  "Priced at the fusion; KINSTONE_27 has a live fuser in Minish Woods.")
d('MW', 'CAVES', 'KINSTONE_BUSINESS_SCRUB', 121, 122, [[FUSION]],
  'connected to the tree above, behind the same fusion')

# --- one item each --------------------------------------------------------
d('MW', 'LAKE_WOODS_CAVE', 'MAIN', 600, 767, [[MITTS]],
  'tile (37,47); this part of the cave holds two golden chests')
link('MW', 'LAKE_WOODS_CAVE', 'MAIN', 600, 767, 'LH-LADDER')
d('MW', 'MINISH_CRACKS', 'MINISH_WOODS_SOUTH', 120, 56, [[MINISH]], 'tile (7,3)')
d('MW', 'MINISH_WOODS', 'MAIN', 907, 599, [[FUSION]],
  'golden fusion chest, tile (56,37) - the fusion is the whole cost')
d('MW', 'MINISH_WOODS', 'MAIN', 667, 743, [[FUSION]],
  'golden fusion chest, tile (41,46) - the fusion is the whole cost')

# --- the Minish Village route ---------------------------------------------
# The Flippers used to ride on every row here as the survey's own
# uncertainty: "there are some leaves that can transport you across the
# water if you don't have zoras flippers, but I'm not sure if they're gated
# by a story flag event or not". Answered, Oct 2026, from two directions.
# The vanilla guide rides the leaves to the village at the very start of the
# game with no items at all (Heart Piece #2 comes before the first dungeon);
# and the leaves are LILYPAD_SMALL objects authored unconditionally into
# MINISH_PATHS/ToMinishVillage's entity list (data/map/entity_headers.s) whose
# only gate is `gPlayerState.flags & PL_MINISH` (src/object/lilypadSmall.c)
# - no story flag anywhere. The crossing costs being Minish and nothing else.
# CONFIRMED IN PLAY by the user (Oct 2026): "the leaves will carry you
# without needing zoras flippers or anything else, they only require you to
# be in Minish form."
d('MW', 'MINISH_PATHS', 'MINISH_VILLAGE', 136, 776, [[MINISH]],
  'tile (8,48), the way in; the leaves are the crossing, and they are free')
d('MW', 'MINISH_PATHS', 'MINISH_VILLAGE', 106, 519, [[MINISH]],
  'a kinstone fusion event on that path, tile (6,32)')
d('MW', 'MINISH_VILLAGE', 'MAIN', 520, 992, [[MINISH]],
  'tile (32,62); the village proper')
d('MW', 'MINISH_HOUSE_INTERIORS', 'FESTARI', 257, 79, [[MINISH]],
  "tile (16,4); the village's third door. The survey adds a story gate here "
  '- Festari has to have moved out of the doorway - and the mode pays it at '
  'boot (M_PRIEST_MOVE, with the rest of the village story), for the same '
  "reason the Crenel bean is pre-grown: it is a chore a run cannot do. So "
  'the token is gone rather than unpriced.')
d('MW', 'MINISH_WOODS', 'MAIN', 424, 840, [[MINISH]],
  'tile (26,52); the third village entrance, reached through the village')
d('MW', 'MINISH_WOODS', 'MAIN', 297, 704, [[MINISH]],
  'the wind crest, tile (18,44) - via the village')
d('MW', 'MINISH_WOODS', 'MAIN', 84, 679, [[MINISH]],
  'golden kinstone chest, tile (5,42) - via the village')
d('MW', 'MINISH_HOUSE_INTERIORS', 'MINISH_WOODS_BOMB', 120, 120, [[MINISH]],
  'via the village')
d('MW', 'DEEPWOOD_SHRINE_ENTRY', 'MAIN', 120, 232, [[MINISH]],
  'tile (7,14); the giant stump')
# The three southwest cave mouths are ONE linked room with three entrances.
# Left cave: a long ice path to a heart piece. Centre: a chest, half water.
# Right: a chest. The user wants all three wired as ? rooms carefully, which
# is a content job rather than a reachability one - recorded here so the
# reachability half is not measured twice.
d('MW', 'MINISH_CAVES', 'MINISH_WOODS_SOUTHWEST', 88, 280, [[MINISH]],
  'west mouth - via the village; the long ice path to a heart piece')
d('MW', 'MINISH_CAVES', 'MINISH_WOODS_SOUTHWEST', 312, 280, [[MINISH]],
  'centre mouth, tile (19,17) - via the village; a chest, and half water')
d('MW', 'MINISH_CAVES', 'MINISH_WOODS_SOUTHWEST', 536, 280, [[MINISH]],
  'east mouth, tile (33,17) - via the village; a chest')

# --- the Pacci pocket, which is not entered from Minish Woods at all -------
# The Great Fairy and the tree hollow above her sit in a pocket whose only
# way in is Eastern Hills North's own exit at (472,72), and reaching THAT
# inside Eastern Hills needs the Cane of Pacci. So the cane is the price of
# everything in here, even though nothing in Minish Woods asks for it.
d('MW', 'TREE_INTERIORS', 'MINISH_WOODS_GREAT_FAIRY', 120, 120, [[PACCI]],
  "entered from Eastern Hills North's Pacci ledge, not from the woods. The "
  'survey believed the tree itself was fusion-gated as well; the vanilla '
  'guide walks in with the cane alone (Big Wallet #2, no fusion named) and '
  'no kinstone world event lands on this door (kinstone_audit.py), so the '
  'fusion term is dropped')
d('MW', 'GREAT_FAIRIES', 'MINISH_WOODS', 120, 120, [[PACCI]],
  'the fairy below that tree - same pocket, same cane')

# --- still unmeasured -----------------------------------------------------
d('MW', 'BEANSTALKS', 'EASTERN_HILLS', 120, 136, [[FUSION, UNSURVEYED]],
  'the beanstalk a kinstone fusion grows - not in the walked survey')
d('MW', 'TREE_INTERIORS', 'WITCH_HUT', 120, 136, [[UNSURVEYED]])
d('MW', 'MINISH_CAVES', 'MINISH_WOODS_NORTH_1', 120, 264, [[MINISH, UNSURVEYED]])
d('MW', 'LAKE_HYLIA', 'MAIN', 0, 952, [[UNSURVEYED]],
  'exit on paper - the north border - and still nothing has walked it')

# LAKE HYLIA. 48x60 tiles, 662 open, and most of that open ground is WATER.
# The west-edge arrival from Lon Lon Ranch lands on a 165-tile north-west
# shore, which again touches only the west edge. The start below is (40,440)
# rather than the border's own (8,328): that tile reads collision 0x0f, the
# cuttable-shrub class, so nothing can stand on it. Same component. Stockwell's lake house is
# the one door on it. Everything else - the mayor's cabin, the Waveblade
# tree, Librari, the Lake Woods cave - is across the lake, which is what the
# region's Flippers price in QuickStartRegionNeedsSwampKit is about.
region('LH', 'Lake Hylia', ('LAKE_HYLIA', 'MAIN', 40, 440),
       note='derived from the exit list + a collision flood, not walked')
# The three lake/ranch crossings, per the user (2026-10-06, second pass):
# ranch (712,443)/(712,762)/(712,908) <-> lake (8,443)/(8,746)/(8,905). This
# block's row used to say (712,328), a coordinate no crossing has; it is the
# middle one, the north-field landing.
d('LH', 'HYRULE_FIELD', 'LON_LON_RANCH', 712, 445, FREE,
  'exit; the border the player arrives through, walkable both ways')
link('LH', 'HYRULE_FIELD', 'LON_LON_RANCH', 712, 445, 'LLR@E445')
# The wind crest is the Ocarina's warp target; the pocket around it has no
# walkable way in (LH-CREST), so this is the edge into it.
d('LH', 'LAKE_HYLIA', 'MAIN', 168, 440, [[OCARINA]], 'the wind crest: the Ocarina warp is the way into its pocket')
link('LH', 'LAKE_HYLIA', 'MAIN', 168, 440, 'LH-CREST')
d('LH', 'HOUSE_INTERIORS_2', 'STOCKWELL_LAKE_HOUSE', 120, 120, FREE,
  'the one door the arrival shore reaches - 67 tiles of walk, no gate')
# Everything the arrival shore cannot reach has MOVED, not been deleted: the
# walked survey found that Lake Hylia is four disconnected places, and each
# of the rooms that used to sit here carrying UNSURVEYED now sits in the
# block that can actually get to it.
#
#   the mayor's cabin, the Waveblade tree and dojo, the Minish caves and
#   cracks, the dig caves, the Temple of Droplets   -> LH-LADDER
#   Librari and the Ocarina house                   -> LH-CREST
#   the Minish Woods border                         -> LH-SW
#
# LAKE_WOODS_CAVE/MAIN is the one that changes direction rather than price:
# it is not somewhere you go from this shore, it is the LADDER you arrive
# through, and the MW block owns that row.
d('LH', 'LAKE_WOODS_CAVE', 'MAIN', 584, 424, None,
  'the Lake Woods ladder is an ENTRANCE to the lake, not a destination from '
  'this shore - see the LH-LADDER block, which starts where it lets out')
d('LH', 'MINISH_WOODS', 'MAIN', 0, 16, None,
  "the south border is in the isolated south-west corner, not in this "
  'shore\'s component - see LH-SW')


# --- Minish Village --------------------------------------------------------
#
# WALKED, Sep 2026, from the village's SOUTH entrance. Its own map rather
# than a handful of rows inside Minish Woods: the village is fourteen doors
# and two rooms, and hanging all of that off the MW start would have said
# nothing about what is reachable once you are actually inside it.
#
# The whole place is Minish-sized, so the Minish Cap is the price of being
# here at all - that is the region requirement below, not a token on every
# row. The Flippers USED to ride along with it, as the MW survey's own
# uncertainty about the floating leaves on the path in. The leaves are free
# (see the Minish Village route in the MW block: the vanilla guide rides them
# with no items, and the lilypad object tests only PL_MINISH), so the region
# costs exactly what being small costs.
#
# "No blockers except for various story flags/events" is the survey's verdict
# on every door not named below. The mode pays the village's story at boot
# (M_PRIEST_TALK, M_PRIEST_MOVE, M_ELDER_TALK1ST, M_ELDER_TALK2ND,
# MORI_00_KOBITO, KOBITO_MORI_1ST and the rest, in GameTask_Transition), for
# the same reason the Crenel bean is pre-grown: a run cannot do a chore that
# needs a story it is not playing. So those doors are FREE here rather than
# carrying an unpayable STORY token.
region('MV', 'Minish Village', ('MINISH_VILLAGE', 'MAIN', 520, 934),
       room_req=[[MINISH]],
       note="the user's walked survey, from the village's south entrance")
d('MV', 'MINISH_VILLAGE', 'SIDE_HOUSE_AREA', 115, 115, FREE,
  'tile (7,7); a HEART CONTAINER, and it costs nothing once you are in the '
  'village. Reached across the seam the two village rooms share - there is '
  'no transition row between them.')
d('MV', 'MINISH_HOUSE_INTERIORS', 'SIDE_AREA', 128, 120, [[FLIPPERS]],
  'tile (8,7); the one door inside the village with a real gate on it')
# The rest of the village's doors, from its own exit list. All FREE per the
# survey; listed individually rather than summarised so the chain placer can
# use them and so a later measurement has somewhere to land.
d('MV', 'MINISH_HOUSE_INTERIORS', 'GENTARI_MAIN', 120, 120, FREE)
d('MV', 'MINISH_HOUSE_INTERIORS', 'GENTARI_EXIT', 104, 80, FREE)
d('MV', 'MINISH_HOUSE_INTERIORS', 'RED', 128, 120, FREE)
d('MV', 'MINISH_HOUSE_INTERIORS', 'GREEN', 128, 120, FREE)
d('MV', 'MINISH_HOUSE_INTERIORS', 'BLUE', 128, 120, FREE)
d('MV', 'MINISH_HOUSE_INTERIORS', 'SHOE_MINISH', 120, 120, FREE)
d('MV', 'MINISH_HOUSE_INTERIORS', 'POT_MINISH', 120, 200, FREE)
d('MV', 'MINISH_HOUSE_INTERIORS', 'BARREL_MINISH', 120, 320, FREE)
d('MV', 'MINISH_HOUSE_INTERIORS', 'FESTARI', 232, 184, FREE,
  'Festari has to have moved out of the doorway; the mode sets M_PRIEST_MOVE '
  'at boot, so the story gate is already paid')
d('MV', 'MINISH_PATHS', 'MINISH_VILLAGE', 120, 24, FREE, 'exit, back to the path')
d('MV', 'MINISH_WOODS', 'MAIN', 456, 824, FREE, 'exit, north-west')
d('MV', 'MINISH_WOODS', 'MAIN', 424, 840, FREE, 'exit, west-north')

# --- Lake Hylia: the wind-crest pocket -------------------------------------
#
# WALKED. A patch of ground with a wind crest, a tree stump and two Minish
# rooms on it, and NO walkable route in from anywhere: the only way to stand
# here is to play the Ocarina and warp to the crest at (168,440), tile
# (10,27). That makes the Ocarina the entrance rather than a shortcut, which
# is why it is the region requirement.
#
# It is also the one gate in this whole table the game can actually TEST and
# that the survey did not already have a token for - ITEM_OCARINA is real
# inventory, unlike MINISH or MAZE - so everything in here is offerable to
# the chain placer instead of invisible to it.
region('LH-CREST', 'Lake Hylia (wind-crest pocket)', ('LAKE_HYLIA', 'MAIN', 168, 440),
       room_req=[[OCARINA]],
       note='no walkable route in at all; the Ocarina warp IS the entrance')
d('LH-CREST', 'MINISH_HOUSE_INTERIORS', 'LAKE_HYLIA_OCARINA', 120, 120, FREE,
  'tile (7,7); nothing beyond getting to the crest')
d('LH-CREST', 'MINISH_CAVES', 'LAKE_HYLIA_LIBRARI', 72, 104, [[MINISH, FUSION]],
  'tile (4,6); the cave mouth is revealed by a kinstone fusion')
d('LH-CREST', 'MINISH_HOUSE_INTERIORS', 'LIBRARI', 120, 120,
  [[MINISH, FUSION, FLIPPERS], [MINISH, FUSION, CAPE]],
  'tile (7,7); through the fusion-revealed cave, whose crossing takes the '
  'Flippers or the cape - so this is the crest, the cap, the fusion and one '
  'of those two')

# --- Lake Hylia: the isolated south-west corner ----------------------------
#
# WALKED. A corner of Lake Hylia with three ways out of the region and no
# way into the rest of it. Nothing in here is gated; the corner is simply
# somewhere you arrive from a neighbour rather than from the lake.
region('LH-SW', 'Lake Hylia (south-west corner)', ('LAKE_HYLIA', 'MAIN', 8, 757),
       note='cut off from the rest of Lake Hylia; entered from MW or LLR')
d('LH-SW', 'LAKE_HYLIA', 'MAIN', 188, 952, FREE,
  'exit, tile (11,59) -> MINISH_WOODS/MAIN (428,16)')
d('LH-SW', 'LAKE_HYLIA', 'MAIN', 8, 907, FREE,
  'exit, tile (0,56) -> HYRULE_FIELD/LON_LON_RANCH (712,907)')
d('LH-SW', 'LAKE_HYLIA', 'MAIN', 8, 757, FREE,
  'exit, the start itself -> HYRULE_FIELD/LON_LON_RANCH (712,757), the lower landing that wants the cape')
link('LH-SW', 'LAKE_HYLIA', 'MAIN', 8, 907, 'LLR@E903')
link('LH-SW', 'LAKE_HYLIA', 'MAIN', 8, 757, 'LLR@E750')

# --- Lake Hylia: the ladder pocket, which is most of the lake --------------
#
# WALKED, and it replaces almost everything the flood guessed. The start is
# where the Lake Woods cave ladder from MINISH_WOODS lets the player out -
# LAKE_HYLIA/MAIN (328,856), tile (20,53) - and from there the lake opens up
# in three price bands: free on the near shore, the Flippers or the cape to
# cross, and the cape plus the Mole Mitts for the whole dig-cave system.
#
# The dig caves are worth naming: HYLIA_DIG_CAVES/1 alone holds SEVEN golden
# chests and its own exit into a Lon Lon Ranch pocket with a heart piece in
# it. That is the densest single room in the survey and all of it sits
# behind the same two items.
region('LH-LADDER', 'Lake Hylia (from the Lake Woods ladder)',
       ('LAKE_HYLIA', 'MAIN', 328, 856),
       note="the user's walked survey; entered from MINISH_WOODS via "
            'LAKE_WOODS_CAVE/MAIN')
# --- the near shore -------------------------------------------------------
d('LH-LADDER', 'HOUSE_INTERIORS_4', 'MAYOR_LAKE_CABIN', 120, 160, FREE,
  'tile (7,10); assuming the door is unlocked')
d('LH-LADDER', 'MINISH_PATHS', 'LAKE_HYLIA', 120, 24, [[MINISH, BOOTS]],
  'tile (7,1)')
d('LH-LADDER', 'HOUSE_INTERIORS_4', 'MAYOR_LAKE_CABIN', 184, 72, [[MINISH, BOOTS]],
  "tile (11,4); the cabin's second way in, a Minish door")
# --- across the water -----------------------------------------------------
d('LH-LADDER', 'LAKE_HYLIA', 'MAIN', 423, 791, [[FLIPPERS]],
  'tile (26,49); a HEART PIECE')
d('LH-LADDER', 'HOUSE_INTERIORS_2', 'STOCKWELL_LAKE_HOUSE', 120, 120, [[FLIPPERS]],
  'tile (7,7)')
d('LH-LADDER', 'LAKE_HYLIA', 'MAIN', 8, 445, [[FLIPPERS]],
  'exit, tile (0,27) -> Lon Lon Ranch')
link('LH-LADDER', 'LAKE_HYLIA', 'MAIN', 8, 445, 'LLR@E445')
d('LH-LADDER', 'TREE_INTERIORS', 'WAVEBLADE', 120, 120, [[FLIPPERS], [CAPE]],
  "tile (7,7); the dojo's atrium, NOT content of its own - the survey also "
  'suspects a kinstone fusion here, unconfirmed, so this is an upper bound '
  'on the crossing and a lower bound on the total')
d('LH-LADDER', 'DOJOS', 'WAVEBLADE', 120, 152, [[FLIPPERS], [CAPE]],
  'tile (7,9); through the atrium above, same unconfirmed fusion')
d('LH-LADDER', 'HYLIA_DIG_CAVES', '0', 136, 135, [[FLIPPERS, MITTS], [CAPE, MITTS]],
  'tile (8,8)')
# --- the cape half of the lake -------------------------------------------
d('LH-LADDER', 'LAKE_HYLIA', 'MAIN', 530, 242, [[CAPE]],
  'tile (33,15); a HEART PIECE')
d('LH-LADDER', 'HYLIA_DIG_CAVES', '1', 744, 247, [[CAPE, MITTS]], 'tile (46,15)')
d('LH-LADDER', 'HYLIA_DIG_CAVES', '1', 776, 136, [[CAPE, MITTS]], 'tile (48,8)')
d('LH-LADDER', 'LAKE_HYLIA', 'BEANSTALK', 904, 72, [[CAPE, MITTS]], 'tile (56,4)')
d('LH-LADDER', 'LAKE_HYLIA', 'BEANSTALK', 520, 120, [[CAPE, MITTS]], 'tile (32,7)')
d('LH-LADDER', 'HYLIA_DIG_CAVES', '1', 923, 198, [[CAPE, MITTS]],
  'tile (57,12); GOLDEN CHEST')
d('LH-LADDER', 'HYLIA_DIG_CAVES', '1', 215, 102, [[CAPE, MITTS]],
  'tile (13,6); GOLDEN CHEST')
d('LH-LADDER', 'HYLIA_DIG_CAVES', '1', 442, 102, [[CAPE, MITTS]],
  'tile (27,6); GOLDEN CHEST')
d('LH-LADDER', 'HYLIA_DIG_CAVES', '1', 843, 54, [[CAPE, MITTS]],
  'tile (52,3); GOLDEN CHEST')
d('LH-LADDER', 'HYLIA_DIG_CAVES', '1', 664, 359, [[CAPE, MITTS]],
  'tile (41,22); GOLDEN CHEST')
d('LH-LADDER', 'HYLIA_DIG_CAVES', '1', 536, 359, [[CAPE, MITTS]],
  'tile (33,22); GOLDEN CHEST')
d('LH-LADDER', 'HYLIA_DIG_CAVES', '1', 520, 311, [[CAPE, MITTS]],
  'tile (32,19); GOLDEN CHEST')
d('LH-LADDER', 'HYLIA_DIG_CAVES', '1', 136, 263, [[CAPE, MITTS]],
  'tile (8,16); the dig system\'s own exit, out into a Lon Lon Ranch pocket '
  'at LON_LON_RANCH (568,104)')
d('LH-LADDER', 'HYRULE_FIELD', 'LON_LON_RANCH', 537, 127, [[CAPE, MITTS]],
  'tile (33,7); a HEART PIECE, in the Lon Lon pocket the dig caves open into '
  '- priced from HERE, which is the only route the survey found to it')
# --- the Minish layer, which wants boots and water as well ----------------
d('LH-LADDER', 'MINISH_CRACKS', 'LAKE_HYLIA_EAST', 152, 48,
  [[BOOTS, MINISH, FLIPPERS]], 'tile (9,3)')
d('LH-LADDER', 'MINISH_CAVES', 'LAKE_HYLIA_NORTH', 392, 424,
  [[BOOTS, MINISH, FLIPPERS]], 'tile (24,26)')
d('LH-LADDER', 'LAKE_HYLIA', 'MAIN', 536, 936, [[BOOTS, MINISH, FLIPPERS]],
  'exit, tile (33,58) - a Minish hole out to MINISH_WOODS/MAIN (776,40)')
d('LH-LADDER', 'MINISH_CAVES', 'MINISH_WOODS_NORTH_1', 120, 264,
  [[BOOTS, MINISH, FLIPPERS]],
  'reached from the Minish Woods pocket the hole above lets out in, not from '
  'the woods proper')
d('LH-LADDER', 'TEMPLE_OF_DROPLETS', 'ENTRANCE', 264, 200,
  [[BOOTS, MINISH, FLIPPERS], [BOOTS, MINISH, CAPE]], 'tile (16,12)')


# --- Mount Crenel's Base ---------------------------------------------------
#
# WALKED, from the one entrance - the border up from Trilby Highlands. The
# CREN block above walked the same mountain DOWNHILL from the Cavern of
# Flames forecourt with the Grip Ring already in hand, which is a completely
# different set of prices; this is the uphill story, and it is the one a run
# actually lives, because Trilby is where the ring puts the player.
#
# THE WHOLE BASE IS BEHIND BOMBS. One cave is free of them and everything
# else is not. A collision flood from the Trilby arrival agrees and is worth
# recording, because it explains a number this project has been puzzled by:
# the arrival component is 52 tiles of the room's 467 open ones, and not ONE
# of the coordinates below is inside it. A flood sees geometry, not gates, so
# a bomb wall reads as a wall - "52 tiles from the border arrival but 198
# from the survey's own coordinate" (docs/QUICKSTART_TRAVERSAL_AUDIT.md) was
# never two different measurements of the same thing. It was the bombs.
#
# THE BEAN ERRAND IS NOT PRICED HERE, AND THAT IS DELIBERATE. The survey's
# own framing is that a BOTTLE is a prerequisite for everything past the
# hint-scrub cave, because the vine has to be watered, and that certain beans
# want the green miner's water from CRENEL_MINISH_PATHS/SPRING_WATER on top
# of that. All true of vanilla and of the mapexplore build this was walked
# in. It is not true here: the run start sets WATERBEAN_OUT and WATERBEAN_PUT
# (global) and, since 2026-10-07, Mount Crenel's local flags YAMA_04_00 and
# YAMA_04_01 - the two sprouts' "has grown" flags - so each CrenelBeanSprout
# lays its vine at init and deletes itself (crenel_vine_probe.py: the base
# climbs into Center, Center climbs down onto the floor). The earlier
# reading, "both sprouts sitting in action 4, their grown state", was wrong:
# action 4 is the seed in its hole waiting for the water, and the vine above
# it was solid wall until the user climbed down onto it. Same treatment, and
# the same reasoning, as the FESTARI row in Minish Woods: the gate is open
# before the run starts, so charging a route for it would price something no
# run can do anything about either way.
#
# If the pre-grow is ever removed, every row below gains the bottle and the
# vine row gains the green water with it.
region('CREN-BASE', "Mount Crenel's Base", ('MT_CRENEL', 'ENTRANCE', 994, 416),
       note='walked uphill from the Trilby border; the CREN block above is '
            'the same mountain walked downhill with the Grip Ring')
d('CREN-BASE', 'CRENEL_CAVES', 'HINT_SCRUB', 120, 93, [[BOMBS]],
  'tile (7,5); the only thing in the base that is not behind the bean')
d('CREN-BASE', 'CRENEL_CAVES', 'LADDER_TO_SPRING_WATER', 120, 136, [[BOMBS]],
  'tile (7,8)')
d('CREN-BASE', 'MT_CRENEL', 'ENTRANCE', 728, 312, [[BOMBS]],
  'tile (45,19); the ledge the player has to reach for the green water')
d('CREN-BASE', 'CRENEL_MINISH_PATHS', 'SPRING_WATER', 128, 792, [[BOMBS, MINISH]],
  'tile (8,49); where the green miner\'s water comes from. Vanilla needs it '
  'for the beans; this build has already grown them.')
d('CREN-BASE', 'CRENEL_CAVES', 'MUSHROOM_KEESE', 184, 312, [[BOMBS]], 'tile (11,19)')
d('CREN-BASE', 'CRENEL_CAVES', 'HELMASAUR_HALLWAY', 104, 40, [[BOMBS]], 'tile (6,2)')
d('CREN-BASE', 'MT_CRENEL', 'ENTRANCE', 408, 232, [[BOMBS]], 'tile (25,14)')
d('CREN-BASE', 'MT_CRENEL', 'ENTRANCE', 123, 103, [[BOMBS, MINISH]],
  'tile (7,6); a GOLDEN CHEST')
d('CREN-BASE', 'MINISH_CAVES', 'BEAN_PESTO', 152, 424, [[BOMBS, GUST, MINISH]],
  'tile (9,26); holds a chest. The user wants it filled with tough enemies '
  'rather than drawn as a general-purpose ? room - a content job, recorded '
  'here so the reachability half is not measured twice.')
d('CREN-BASE', 'CRENEL_MINISH_PATHS', 'BEAN', 128, 792, [[BOMBS, GUST, MINISH]],
  'tile (8,49)')
d('CREN-BASE', 'CRENEL_CAVES', 'BOMB_BUSINESS_SCRUB', 120, 120, FREE,
  'the survey stamped this one at (-1336,-1912), which is a mid-transition '
  'reading rather than a place; the coordinate here is the door\'s own '
  'vanilla arrival. Free either way.')
d('CREN-BASE', 'MT_CRENEL', 'CENTER', 280, 376, [[BOMBS, GUST, MINISH]],
  'tile (17,23); up the vine at ENTRANCE (280,12), tile (17,0). In vanilla '
  'this also wants the green bean planted and watered with the miner\'s '
  'water - pre-paid here, see the block comment.')
# --- the alternative that skips all of it ---------------------------------
# The user: "if the player has the grip ring then they can skip all of the
# above routes". The wall is real in the tile data - act tile 0x50, a climb
# surface, in a seven-tile band at tx 50-56, ty 0-2, which is pixels 800-912
# across the top of the Entrance screen and lands exactly where the survey
# says it does.
d('CREN-BASE', 'MT_CRENEL', 'CENTER', 856, 274, [[GRIP]],
  'tile (53,17); the climb near the base entrance, which skips the bombs, '
  'the bean and the Minish layer entirely')
link('CREN-BASE', 'MT_CRENEL', 'CENTER', 856, 274, 'CREN')


# --- Veil Falls ------------------------------------------------------------
#
# Walked by the user 2026-10-06 from both of its borders. Two pockets that
# no walk joins: pocket 1 is the Lon Lon strip at the falls' south-west
# corner (the ranch's north gate lands there), pocket 2 is everything else,
# entered from North Hyrule Field's east border through a corridor to cave
# #1 at the foot of the big falls.
#
# CAVE #1 is the Source of the Flow's cave. In vanilla a stone face (NPC4E,
# type 11) seals it until the player fuses KINSTONE_SOURCE_FLOW with it -
# the gold piece King Gustaf's ghost hands over in the Royal Crypt
# (script_KingGustav.inc, GiveKinstone 0x6d). Since Oct 2026 the stone is a
# GATE the run rolls (SOURCE_FLOW above): open, the NPC is deleted at its
# init (npc4E.c) and the door was measured OPEN - walking north from
# (56,560) enters VEIL_FALLS_CAVES/ENTRANCE in 80 frames; sealed, the stone
# stands and the piece is a key item (QUICKSTART_ITEM_GOLD_FLOW) the
# economy pays out in the neighbouring regions. The cave is dark, and the
# user prices the dark at the Lantern.
#
# Beyond cave #1 the falls are a Grip Ring climb: the big waterfall (tiles
# 17-27, rows 18-28, collision 0x2b over act tile 0x50) climbs from the
# plateau to the top plateau - measured, a player with the ring climbs
# from (344,470) to (344,214) - and the Top screen is reached the same way.
# The water is the Flippers. The dig cave is the Mitts.
#
# The DROP lands on the plateau at the foot of the big falls, (296,500),
# which the walk reaches "through cave #1". So the region key VF is that
# plateau: its rows are the user's North Field rows with cave #1's cost
# taken off everything that is not the cave itself (INFERRED from the
# walk, not walked), the two borders carry the user's lists verbatim.

region('VF', 'Veil Falls', ('VEIL_FALLS', 'MAIN', 296, 500),
       note='the drop plateau at the foot of the big falls, tile (18,31); rows inferred from the North Field walk')
d('VF', 'VEIL_FALLS_CAVES', 'ENTRANCE', 56, 120, [[LANTERN]], 'cave #1, dark')
d('VF', 'VEIL_FALLS_CAVES', 'EXIT', 79, 66, [[LANTERN]], "cave #1's upper room, dark")
d('VF', 'VEIL_FALLS', 'MAIN', 8, 639, [[LANTERN, SOURCE_FLOW]], 'exit west -> NORTH_HYRULE_FIELD (1000,111), the bomb pocket, down through cave #1 and out past the stone')
d('VF', 'VEIL_FALLS', 'MAIN', 216, 472, FREE, 'tile (13,29), where cave #1 opens onto this plateau')
d('VF', 'VEIL_FALLS', 'MAIN', 358, 199, [[GRIP, FUSION]], 'gold chest, tile (22,12), on the top plateau; KINSTONE_61 lays it')
d('VF', 'VEIL_FALLS', 'MAIN', 248, 254, [[GRIP]], 'the wind crest, tile (15,15)')
d('VF', 'VEIL_FALLS_CAVES', 'HALLWAY_1F', 184, 120, [[GRIP]])
d('VF', 'VEIL_FALLS_CAVES', 'HALLWAY_SECRET_ROOM', 106, 90, [[GRIP]], "behind the 1F hallway's bombable wall in vanilla (SUIGEN_DOUKUTU_01_BW00); the user prices it at the grip alone")
d('VF', 'VEIL_FALLS', 'MAIN', 200, 88, [[GRIP]], 'tile (12,5)')
d('VF', 'VEIL_FALLS_CAVES', 'HALLWAY_2F', 56, 120, [[GRIP]])
d('VF', 'VEIL_FALLS', 'MAIN', 344, 56, [[GRIP]], 'tile (21,3)')
d('VF', 'VEIL_FALLS_TOP', '0', 430, 153, [[GRIP]], 'exit north -> the ledge above the falls, tile (26,9)')
d('VF', 'VEIL_FALLS_CAVES', 'HALLWAY_RUPEE_PATH', 152, 40, [[GRIP]])
d('VF', 'VEIL_FALLS', 'MAIN', 168, 216, [[GRIP]], 'tile (10,13)')
d('VF', 'VEIL_FALLS_CAVES', 'HALLWAY_HEART_PIECE', 120, 42, [[GRIP, FLIPPERS, FUSION]],
  'the nook behind the small upper-left waterfall; the user: grip and flippers, and (second pass) the fusion too. '
  'KINSTONE_13 (world event type 9, marker at the nook\'s door (56,40)) is what reveals it')
d('VF', 'VEIL_FALLS', 'MAIN', 154, 611, [[FLIPPERS]], 'heart piece, tile (9,38), in the pool below the plateau')
d('VF', 'VEIL_FALLS_DIG_CAVE', '0', 232, 625, [[FUSION, MITTS, FLIPPERS]], 'dig-cave entrance 2, tile (14,39); KINSTONE_1F lays the land in front')
d('VF', 'VEIL_FALLS_DIG_CAVE', '0', 227, 299, [[FUSION, MITTS, FLIPPERS]], 'heart piece, tile (14,18), from entrance 2')
d('VF', 'VEIL_FALLS_DIG_CAVE', '0', 443, 86, [[FUSION, MITTS, FLIPPERS]], 'gold chest, tile (27,5), from entrance 2')
# Not in the user's lists, and asked about: the gold chest on the ledge by
# the falls, VEIL_FALLS/MAIN (200,360), tile (12,22). The data says it is the
# block-puzzle cave's doorstep - that cave's south border lands on the ledge
# at (216,344), tile (13,21), and the ledge's door at (13,19-20) leads back
# in. Into the chain: cave #1's upper room has a bombable north wall
# (SUIGEN_DOUKUTU_04_BW00, "wall to secret area blown open"), its room
# rectangle abuts the SECRET_CHEST room's (same area, a scroll seam), and
# from there a door to the dark SECRET_STAIRCASE and a door to the block
# puzzle. Measured: the ledge is NOT reached by stepping off the waterfall
# climb (the climb holds the player on the falls). Priced at the bombs and
# the lantern; UNWALKED.
d('VF', 'VEIL_FALLS_CAVES', 'SECRET_CHEST', 152, 72, [[LANTERN, BOMBS]], "through cave #1's bombable wall; a 50-shell chest. INFERRED")
d('VF', 'VEIL_FALLS_CAVES', 'HALLWAY_SECRET_STAIRCASE', 88, 72, [[LANTERN, BOMBS]], 'dark; INFERRED')
d('VF', 'VEIL_FALLS_CAVES', 'HALLWAY_BLOCK_PUZZLE', 152, 280, [[LANTERN, BOMBS, BRACELETS]], 'the block puzzle; the user: the Power Bracelets move the blocks. Route INFERRED')
d('VF', 'VEIL_FALLS', 'MAIN', 200, 360, [[LANTERN, BOMBS, BRACELETS]], "the ledge chest, tile (12,22), out of the block puzzle's south door; the bracelets are the puzzle before it. Route INFERRED")
# The Lon Lon side is the other pocket: nothing here walks to it.
link('VF', 'VEIL_FALLS', 'MAIN', 8, 639, 'NHF@VF')
link('VF', 'VEIL_FALLS_TOP', '0', 430, 153, 'VF')

# Pocket 2 from its border: the user's North Field list, verbatim, with
# "cave #1" as the Lantern (the user: "this cave is dark, so it requires
# the lantern") and the drop plateau added as a destination.
entrance('VF@NHF', 'VF', 'Veil Falls (from North Hyrule Field)', ('VEIL_FALLS', 'MAIN', 8, 639),
         note='walked 2026-10-06; the corridor to cave #1. Every row past the corridor also carries SOURCE_FLOW: the stone at the cave mouth (Oct 2026)')
d('VF@NHF', 'VEIL_FALLS', 'MAIN', 8, 639, FREE, 'exit west -> NORTH_HYRULE_FIELD (1000,111), the bomb pocket; the start itself')
d('VF@NHF', 'VEIL_FALLS_CAVES', 'ENTRANCE', 56, 120, [[SOURCE_FLOW, LANTERN]], 'cave #1, dark, and the stone at its mouth must be gone (the gate rolled open, or its golden piece fused)')
d('VF@NHF', 'VEIL_FALLS_CAVES', 'EXIT', 79, 66, [[SOURCE_FLOW, LANTERN]], 'through cave #1')
d('VF@NHF', 'VEIL_FALLS', 'MAIN', 216, 472, [[SOURCE_FLOW, LANTERN]], 'tile (13,29): must go through cave #1')
d('VF@NHF', 'VEIL_FALLS', 'MAIN', 296, 500, [[SOURCE_FLOW, LANTERN]], 'the drop plateau, tile (18,31): through cave #1 (added)')
d('VF@NHF', 'VEIL_FALLS', 'MAIN', 358, 199, [[SOURCE_FLOW, LANTERN, GRIP, FUSION]], 'gold chest, tile (22,12)')
d('VF@NHF', 'VEIL_FALLS', 'MAIN', 248, 254, [[SOURCE_FLOW, LANTERN, GRIP]], 'wind crest, tile (15,15)')
d('VF@NHF', 'VEIL_FALLS_CAVES', 'HALLWAY_1F', 184, 120, [[SOURCE_FLOW, LANTERN, GRIP]])
d('VF@NHF', 'VEIL_FALLS_CAVES', 'HALLWAY_SECRET_ROOM', 106, 90, [[SOURCE_FLOW, LANTERN, GRIP]])
d('VF@NHF', 'VEIL_FALLS', 'MAIN', 200, 88, [[SOURCE_FLOW, LANTERN, GRIP]], 'tile (12,5)')
d('VF@NHF', 'VEIL_FALLS_CAVES', 'HALLWAY_2F', 56, 120, [[SOURCE_FLOW, LANTERN, GRIP]])
d('VF@NHF', 'VEIL_FALLS', 'MAIN', 344, 56, [[SOURCE_FLOW, LANTERN, GRIP]], 'tile (21,3)')
d('VF@NHF', 'VEIL_FALLS_TOP', '0', 430, 153, [[SOURCE_FLOW, LANTERN, GRIP]], 'tile (26,9)')
d('VF@NHF', 'VEIL_FALLS_CAVES', 'HALLWAY_RUPEE_PATH', 152, 40, [[SOURCE_FLOW, LANTERN, GRIP]])
d('VF@NHF', 'VEIL_FALLS', 'MAIN', 168, 216, [[SOURCE_FLOW, LANTERN, GRIP]], 'tile (10,13)')
d('VF@NHF', 'VEIL_FALLS_CAVES', 'HALLWAY_HEART_PIECE', 120, 42, [[SOURCE_FLOW, LANTERN, GRIP, FLIPPERS, FUSION]], 'the user: cave #1, grip and flippers, and the fusion (confirmed, second pass): the KINSTONE_13 reveal')
d('VF@NHF', 'VEIL_FALLS', 'MAIN', 154, 611, [[SOURCE_FLOW, LANTERN, FLIPPERS]], 'heart piece, tile (9,38): the user prices it at the flippers; the lantern is the cave on the way (added)')
d('VF@NHF', 'VEIL_FALLS_DIG_CAVE', '0', 232, 625, [[SOURCE_FLOW, LANTERN, FUSION, MITTS, FLIPPERS]], 'dig-cave entrance 2')
d('VF@NHF', 'VEIL_FALLS_DIG_CAVE', '0', 227, 299, [[SOURCE_FLOW, LANTERN, FUSION, MITTS, FLIPPERS]], 'heart piece from entrance 2')
d('VF@NHF', 'VEIL_FALLS_DIG_CAVE', '0', 443, 86, [[SOURCE_FLOW, LANTERN, FUSION, MITTS, FLIPPERS]], 'gold chest from entrance 2')
d('VF@NHF', 'VEIL_FALLS_CAVES', 'SECRET_CHEST', 152, 72, [[SOURCE_FLOW, LANTERN, BOMBS]], 'INFERRED, see the VF block')
d('VF@NHF', 'VEIL_FALLS_CAVES', 'HALLWAY_SECRET_STAIRCASE', 88, 72, [[SOURCE_FLOW, LANTERN, BOMBS]], 'INFERRED')
d('VF@NHF', 'VEIL_FALLS_CAVES', 'HALLWAY_BLOCK_PUZZLE', 152, 280, [[SOURCE_FLOW, LANTERN, BOMBS, BRACELETS]], 'the bracelets for the blocks (the user); route INFERRED')
d('VF@NHF', 'VEIL_FALLS', 'MAIN', 200, 360, [[SOURCE_FLOW, LANTERN, BOMBS, BRACELETS]], 'the ledge chest; the bracelets are the puzzle before it; route INFERRED')
link('VF@NHF', 'VEIL_FALLS', 'MAIN', 8, 639, 'NHF@VF')
link('VF@NHF', 'VEIL_FALLS_TOP', '0', 430, 153, 'VF')

# Pocket 1: the Lon Lon strip. The user's list from the ranch's north gate,
# verbatim. The exit at (176,1000) is a one-way ledge down onto the lower
# strip (collision 0x17 at tiles (10,54)-(10,56)), which is the VF@POCKET
# entrance below; nothing walks back up.
entrance('VF@LLR', 'VF', 'Veil Falls (from Lon Lon Ranch, the Lon Lon strip)', ('VEIL_FALLS', 'MAIN', 88, 1000),
         note='walked 2026-10-06; pocket 1, cut off from the rest of the falls')
d('VF@LLR', 'VEIL_FALLS', 'MAIN', 88, 1000, FREE, 'exit south -> LON_LON_RANCH (88,16); the start itself')
d('VF@LLR', 'VEIL_FALLS', 'MAIN', 176, 1000, FREE, "exit south -> LON_LON_RANCH's gold-chest pocket (176,16), down the ledge")
d('VF@LLR', 'DOJOS', 'TO_SPLITBLADE', 120, 55, [[FUSION, FLIPPERS]], 'the Splitblade dojo\'s ante room; KINSTONE_1D opens the archway')
d('VF@LLR', 'DOJOS', 'SPLITBLADE', 120, 167, [[FUSION, FLIPPERS]], 'the Splitblade dojo')
d('VF@LLR', 'VEIL_FALLS', 'MAIN', 409, 953, FREE, 'heart piece, tile (25,59)')
d('VF@LLR', 'VEIL_FALLS_DIG_CAVE', '0', 424, 583, [[FLIPPERS, MITTS]], 'dig-cave entrance 1, tile (26,36)')
d('VF@LLR', 'VEIL_FALLS_DIG_CAVE', '0', 281, 534, [[FLIPPERS, MITTS]], 'gold chest, tile (17,33), from entrance 1')
d('VF@LLR', 'VEIL_FALLS_DIG_CAVE', '0', 267, 534, [[FLIPPERS, MITTS]], 'gold chest, tile (16,33), from entrance 1')
link('VF@LLR', 'VEIL_FALLS', 'MAIN', 88, 1000, 'LLR@N')
link('VF@LLR', 'VEIL_FALLS', 'MAIN', 176, 1000, 'LLR@POCKET')

# The lower strip, from the ranch's gold-chest pocket: the Lon Lon list
# minus the way back up to (88,1000). INFERRED from the walk (the user's
# list was taken from (88,1000) and the ledge is one-way).
entrance('VF@POCKET', 'VF', "Veil Falls (the lower strip, from Lon Lon's gold-chest pocket)", ('VEIL_FALLS', 'MAIN', 176, 1000),
         note='Oct 2026; below the one-way ledge. Rows copied from VF@LLR without the (88,1000) exit')
copy_dests('VF@LLR', 'VF@POCKET', skip=[('VEIL_FALLS', 'MAIN', (88, 1000))])
link('VF@POCKET', 'VEIL_FALLS', 'MAIN', 176, 1000, 'LLR@POCKET')

# ------------------------------------------------------------------ checks --
def _fmt(req):
    if req is None:
        return 'NOT REACHABLE from this start'
    if not req or req == [[]]:
        return '-'
    return ' / '.join(' + '.join(t) for t in req) or '-'


def dump():
    for key in SURVEY:
        r = SURVEY[key]
        a, room, x, y = r['start']
        print('\n=== %-22s start %s / %s (%d,%d)%s' %
              (r['name'], a, room, x, y,
               ('   ROOM REQ ' + _fmt(r['room_req'])) if r['room_req'] else ''))
        if r['note']:
            print('    (%s)' % r['note'])
        for e in r['dests']:
            loc = ('(%s,%s)' % e['local']) if e['local'][0] is not None else '(-)'
            print('    %-24s %-34s %-12s %s' %
                  ('%s/%s' % (e['area'], e['room']), _fmt(e['req']), loc, e['note']))


def check():
    """Consistency of the survey against the ROM's own exit table and against
    the port model in overworld_paths.py."""
    import exit_lists as EX
    import overworld_paths as OP
    problems, notes = [], []

    # 1. Every destination room named must be a room the ROM actually has, and
    #    a cross-room destination should be an exit this room really owns.
    for key, r in SURVEY.items():
        sa, sr, _, _ = r['start']
        src_room = 'ROOM_%s_%s' % (sa, sr) if not sr.startswith(sa) else 'ROOM_' + sr
        rows = EX.BY_ROOM.get(src_room, [])
        dests = {(row[6], row[7]) for row in rows}
        for e in r['dests']:
            if e['area'] == sa and e['room'] == sr:
                continue  # a spot inside the same room
            want = ('AREA_%s' % e['area'], 'ROOM_%s_%s' % (e['area'], e['room']))
            if want[1] not in EX.OWNER and want[1] not in EX.BY_ROOM:
                notes.append('%s: %s/%s is not a room name transitions.c knows'
                             % (key, e['area'], e['room']))
            elif want not in dests:
                notes.append('%s: %s/%s is not a direct exit of the start room '
                             '(fine if it is two doors deep)' % (key, e['area'], e['room']))

    # 2. Coordinates that cannot be a settled reading. The overlay computes
    #    local = world - origin, and mid-transition the origin still belongs to
    #    the room being left, so these come out negative or enormous.
    for key, r in SURVEY.items():
        for e in [dict(local=r['start'][2:], area=r['start'][0], room=r['start'][1],
                       note='the start stamp')] + r['dests']:
            x, y = e['local']
            if x is None:
                continue
            if x < 0 or y < 0 or x > 2000 or y > 2000:
                problems.append('%s: %s/%s (%d,%d) is outside any room - taken '
                                'mid-transition, so the coordinate is unusable '
                                '(the room NAME is still good)'
                                % (key, e['area'], e['room'], x, y))

    # 3. Conflicts with the port model, where both speak about the same thing.
    conflicts = []
    #    3a. Region gates.
    for key, r in SURVEY.items():
        op_key = {'CW': 'CW', 'RV': 'RV', 'WR': 'WR'}.get(key)
        if op_key and op_key in OP.GATES:
            survey = set(frozenset(t) for t in r['room_req']) if r['room_req'] else None
            model = OP.GATES[op_key]
            if survey is not None and survey != set(model):
                conflicts.append('%s room requirement %s vs overworld_paths GATES %s'
                                 % (key, _fmt(r['room_req']), OP.show(model)))
            if survey is None and model:
                conflicts.append('%s has no room requirement in the survey but '
                                 'overworld_paths gates it on %s' % (key, OP.show(model)))
    #    3b. RESOLVED, and the check kept as a regression guard. The survey
    #        priced the same "push a block" obstacle at a level-two sword in
    #        Lon Lon and Trilby and a level-three sword in Royal Valley and
    #        the North Hyrule Field graveyard pocket. Neither reading was
    #        wrong about the map - vanilla really does charge more for a
    #        bigger block, because block size is clone count and clone count
    #        is sword level. The mode moved the whole mechanic onto the Power
    #        Bracelets, so every block is one item now. If a sword level ever
    #        reappears as a block price, this catches it.
    swordy = sorted({k for k, r in SURVEY.items() for e in r['dests']
                     if e['req'] and any(any(t.startswith('sword') and t != SWORD
                                             for t in term)
                                         for term in e['req'])})
    if swordy:
        conflicts.append('a sword level is being used as a block-push price again, in '
                         '%s - the Power Bracelets own that gate now' % swordy)
    #    3c. The two models have to agree on North Hyrule Field's WNW border,
    #        because the survey found only ONE way out that way - through the
    #        graveyard pocket at (5,93) - and overworld_paths prices that
    #        border independently. This used to be a by-hand cross-check
    #        printed every run because the two sides were written in
    #        different currencies; with the block push down to one item they
    #        are directly comparable, so it only speaks up when they differ.
    op_nhf = OP.TRAVERSAL.get(('NHF', 'N', 'WNW'))
    if op_nhf:
        survey_nhf = _fmt([[BOMBS, BRACELETS]])
        if OP.show(op_nhf) != survey_nhf:
            conflicts.append('overworld_paths prices NHF N->WNW at %s but the survey\'s '
                             'only route out that way (5,93) costs %s'
                             % (OP.show(op_nhf), survey_nhf))

    print('=== survey: %d regions, %d destinations' %
          (len(SURVEY), sum(len(r['dests']) for r in SURVEY.values())))
    print('\n--- coordinates that need re-taking (%d) ---' % len(problems))
    for p in problems:
        print('  ' + p)
    print('\n--- conflicts and cross-checks (%d) ---' % len(conflicts))
    for c in conflicts:
        print('  ' + c)
    print('\n--- notes (%d) ---' % len(notes))
    for n in notes[:40]:
        print('  ' + n)
    if len(notes) > 40:
        print('  ... and %d more' % (len(notes) - 40))


if __name__ == '__main__':
    if '--check' in sys.argv:
        check()
    else:
        dump()
