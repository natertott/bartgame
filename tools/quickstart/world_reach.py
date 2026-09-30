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
region('SHF', 'South Hyrule Field', ('HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', -904, -2216),
       note='the start stamp itself was taken mid-transition (see --check)')
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 893, 282, [[SWORD]])
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 1000, 120, [[SWORD]])
d('SHF', 'CAVES', 'SOUTH_HYRULE_FIELD_FAIRY_FOUNTAIN', -744, -296, [[BOMBS]])
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 264, 266, [[FLIPPERS]])
d('SHF', 'CAVES', 'SOUTH_HYRULE_FIELD_RUPEE', -152, -1032, [[FUSION]])
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 84, 111, [[SWORD]])
d('SHF', 'HOUSE_INTERIORS_2', 'LINKS_HOUSE_ENTRANCE', 120, -312, [[STORY]],
  'nothing but story flags')
d('SHF', 'HOUSE_INTERIORS_2', 'LINKS_HOUSE_BEDROOM', -1208, -392, FREE)
d('SHF', 'HOUSE_INTERIORS_2', 'LINKS_HOUSE_ENTRANCE', 244, 92, FREE)
d('SHF', 'TREE_INTERIORS', 'SOUTH_HYRULE_FIELD_HEART_PIECE', -392, 120, [[SWORD, FUSION]])
d('SHF', 'MINISH_HOUSE_INTERIORS', 'SOUTH_HYRULE_FIELD', -184, -856, [[SWORD, BOOTS, MINISH]])
d('SHF', 'MINISH_CAVES', 'OUTSIDE_LINKS_HOUSE', -1352, 184, [[SWORD, MINISH, BOOTS, FLIPPERS]])
d('SHF', 'HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 952, 294, [[PACCI, SWORD]])

# --- Eastern Hills North ---------------------------------------------------
region('EH-N', 'Eastern Hills North', ('HYRULE_FIELD', 'EASTERN_HILLS_NORTH', -6, 428))
d('EH-N', 'HYRULE_FIELD', 'EASTERN_HILLS_NORTH', 249, 539, FREE, 'exit')
d('EH-N', 'HYRULE_FIELD', 'EASTERN_HILLS_NORTH', 463, 427, [[BOMBS]], 'exit')
d('EH-N', 'HOUSE_INTERIORS_4', 'FARM_HOUSE', -904, 136, [[BOMBS]])
d('EH-N', 'DIG_CAVES', 'EASTERN_HILLS', 56, 181, [[BOMBS, MITTS]])
d('EH-N', 'HYRULE_FIELD', 'EASTERN_HILLS_NORTH', 460, 80, [[BOMBS, PACCI]], 'exit')
d('EH-N', 'HYRULE_FIELD', 'EASTERN_HILLS_NORTH', 308, -2, [[BOMBS]], 'exit')
d('EH-N', 'HYRULE_FIELD', 'EASTERN_HILLS_NORTH', 268, 532, FREE, 'exit')

# --- Eastern Hills Center --------------------------------------------------
region('EH-C', 'Eastern Hills Center', ('HYRULE_FIELD', 'EASTERN_HILLS_CENTER', 257, 31))
d('EH-C', 'HYRULE_FIELD', 'EASTERN_HILLS_CENTER', 169, 251, FREE, 'exit')
d('EH-C', 'HYRULE_FIELD', 'EASTERN_HILLS_CENTER', 344, 249, FREE, 'exit')
d('EH-C', 'CAVES', 'HILLS_KEESE_CHEST', -712, -1032, [[BOMBS]])

# --- Eastern Hills South ---------------------------------------------------
region('EH-S', 'Eastern Hills South', ('HYRULE_FIELD', 'EASTERN_HILLS_SOUTH', 330, -3))
d('EH-S', 'HYRULE_FIELD', 'EASTERN_HILLS_SOUTH', 465, 170, FREE, 'exit')
d('EH-S', 'MINISH_HOUSE_INTERIORS', 'HYRULE_FIELD_EXIT', -1032, -856, [[MINISH]])
d('EH-S', 'HYRULE_FIELD', 'EASTERN_HILLS_SOUTH', 167, 8, [[BOMBS]],
  'exit; the survey notes the reverse direction is this table plus bombs')

# --- Lon Lon Ranch ---------------------------------------------------------
region('LLR', 'Lon Lon Ranch', ('HYRULE_FIELD', 'LON_LON_RANCH', 298, 968))
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 13, 565, [[BOMBS]], 'exit')
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', -6, 157, FREE, 'exit')
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 88, 15, [[PACCI]], 'exit')
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 168, 55, None,
  'POCKET at tile (10,3), holding a kinstone chest. The mapexplore survey '
  'walked it and prices it at the Cane of Pacci - the only way in is up to '
  'Veil Falls and back down. It stays NOT REACHABLE here because this build '
  "has no Veil Falls: Lon Lon Ranch's two border rows to it and North Hyrule "
  "Field's one are compiled out under QUICKSTART (docs/QUICKSTART_RETARGETS."
  'md, the three BLOCKED rows), so the cane buys nothing. Re-price this at '
  '[[PACCI]] the day Veil Falls is opened. The coordinate was 32936,-1184 - '
  'a mid-transition stamp, not a place.')
d('LLR', 'MINISH_CRACKS', 'LON_LON_RANCH_NORTH', 120, 56, [[PACCI, MINISH]])
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 396, 253, [[MINISH, PACCI]],
  'POCKET (tornado float). Only spawn content here when these are held.')
d('LLR', 'MINISH_PATHS', 'LON_LON_RANCH', -864, 728, [[BOOTS, MINISH]])
d('LLR', 'CAVES', 'LON_LON_RANCH', 86, 81, [[BRACELETS]],
  'the main part is behind a pushable block')
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 184, 298, [[BRACELETS]],
  'POCKET out of the cave above - where Tingle sits. Gate content on this.')
d('LLR', 'CAVES', 'LON_LON_RANCH_WALLET', 120, -1032, [[FUSION]])
d('LLR', 'HOUSE_INTERIORS_4', 'RANCH_HOUSE_WEST', 245, 90, [[MINISH], [LONLON_KEY]],
  'the minish route needs the room to keep its vanilla content')
d('LLR', 'HOUSE_INTERIORS_4', 'RANCH_HOUSE_EAST', -632, 120, [[BOULDER('LLR', 1)], [MINISH]],
  'free once the boulder is in; there is also a separate minish door')
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 710, 753,
  [[FLIPPERS], [CAPE], [MINISH, PACCI]], 'exit')
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 707, 907, [[BOULDER('LLR', 2)]])
d('LLR', 'GORON_CAVE', 'STAIRS', 120, 120, [[BOULDER('LLR', 3)], [MINISH]])

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
d('NHF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 999, 112, [[BOMBS]], 'exit')
d('NHF', 'MINISH_CRACKS', 'EAST_HYRULE_CASTLE', -936, 48, [[MINISH, BOOTS]])
d('NHF', 'CAVES', 'TO_GRAVEYARD', -104, 216, [[BOMBS]])
d('NHF', 'CAVES', 'HEART_PIECE_HALLWAY', -1000, -1000, [[BOMBS]])
d('NHF', 'DOJOS', 'TO_GREATBLADE', -392, -56, [[FUSION, FLIPPERS]])
d('NHF', 'DOJOS', 'GREATBLADE', 120, 200, [[FUSION, FLIPPERS]])
d('NHF', 'CAVES', 'TO_GRAVEYARD', 59, 110, [[BOMBS, BRACELETS]], 'POCKET')
d('NHF', 'HYRULE_FIELD', 'NORTH_HYRULE_FIELD', 5, 93, [[BOMBS, BRACELETS]],
  'exit, reachable ONLY through the TO_GRAVEYARD pocket above')

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
region('CG', 'Hyrule Castle Garden', ('CASTLE_GARDEN', 'MAIN', 504, 480),
       note='derived from the exit list and the site table, not walked')
d('CG', 'CASTLE_GARDEN', 'MAIN', 504, 36, FREE, 'exit, south to North Hyrule Field')
d('CG', 'CASTLE_GARDEN_MINISH_HOLES', '0', 136, 104, [[MINISH]])
d('CG', 'CASTLE_GARDEN_MINISH_HOLES', '1', 136, 104, [[MINISH]])
d('CG', 'MINISH_CRACKS', 'HYRULE_CASTLE_GARDEN', 152, 104, [[MINISH]])
d('CG', 'GARDEN_FOUNTAINS', 'EAST', 120, 80, [[MINISH]],
  'reached through the minish holes above')
d('CG', 'GARDEN_FOUNTAINS', 'WEST', 120, 80, [[MINISH]],
  'reached through the minish holes above')

# --- Royal Valley ----------------------------------------------------------
region('RV', 'Royal Valley', ('ROYAL_VALLEY', 'MAIN', -536, 416),
       note='the only real entrance')
d('RV', 'ROYAL_VALLEY', 'MAIN', 118, 1000, FREE, 'exit')
d('RV', 'ROYAL_VALLEY', 'FOREST_MAZE', -248, -3240, FREE,
  'free to reach; the LANTERN is what solves it')
d('RV', 'ROYAL_VALLEY', 'MAIN', -888, 440, [[LANTERN, MAZE]])
d('RV', 'HOUSE_INTERIORS_2', 'DAMPE', -376, -312, [[LANTERN, MAZE]])
d('RV', 'ROYAL_VALLEY', 'MAIN', 244, 331, [[LANTERN, MAZE, GRAVEYARD_KEY]],
  'the gate to the upper pocket - everything above it inherits this')
d('RV', 'ROYAL_VALLEY_GRAVES', 'HEART_PIECE', 120, 120, [[LANTERN, MAZE, GRAVEYARD_KEY]])
d('RV', 'ROYAL_VALLEY_GRAVES', 'GINA', -168, 280, [[LANTERN, MAZE, GRAVEYARD_KEY]])
d('RV', 'ROYAL_VALLEY', 'CRYPT', None, None,
  [[LANTERN, MAZE, GRAVEYARD_KEY, BRACELETS]], 'the royal crypt')

# --- Trilby Highlands ------------------------------------------------------
region('TRIL', 'Trilby Highlands', ('HYRULE_FIELD', 'TRILBY_HIGHLANDS', 465, 124),
       note='the entrance that connects to North Hyrule Field')
d('TRIL', 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 32880, -1184, None,
  'POCKET, only reachable from Royal Valley')
d('TRIL', 'DIG_CAVES', 'TRILBY_HIGHLANDS', 264, 229, [[FUSION, FLIPPERS, MITTS]],
  'the fusion lays the land in front of the mouth')
d('TRIL', 'CAVES', 'TRILBY_MITTS_FAIRY_FOUNTAIN', -1496, -360, [[FUSION, FLIPPERS, MITTS]])
d('TRIL', 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 16, 415, FREE, 'exit')
d('TRIL', 'DIG_CAVES', 'TRILBY_HIGHLANDS', 88, 229, [[MITTS]])
d('TRIL', 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', -872, -1080, [[MITTS]],
  'POCKET with a tingle event and a minish house, only via the dig cave')
d('TRIL', 'MINISH_HOUSE_INTERIORS', 'NEXT_TO_KNUCKLE', -472, -856, [[MITTS, MINISH]])
d('TRIL', 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 470, 560, FREE, 'exit')
d('TRIL', 'CAVES', 'TRILBY_HIGHLANDS', -824, -600, FREE, 'the two-ladder cave, near side')
d('TRIL', 'CAVES', 'BOTTLE_BUSINESS_SCRUB', -6, 95, [[BOMBS]],
  'THE bombable wall off the two-ladder cave')
d('TRIL', 'CAVES', 'TRILBY_HIGHLANDS', -1064, -600, [[BRACELETS]],
  'the other pocket of the two-ladder cave, from its far side')
d('TRIL', 'CAVES', 'TRILBY_KEESE_CHEST', -152, -296,
  [[BOMBS, BOULDER('TRIL', 1)], [BOMBS, BRACELETS]])
d('TRIL', 'CAVES', 'TRILBY_RUPEE', -440, -1032, [[FUSION]], 'in the boulder pocket')
d('TRIL', 'TREE_INTERIORS', 'PERCYS_TREEHOUSE', -136, 120, FREE, 'in the boulder pocket')
d('TRIL', 'CAVES', 'TRILBY_FAIRY_FOUNTAIN', -472, -296, [[BOMBS]], 'in the boulder pocket')
d('TRIL', 'HYRULE_FIELD', 'TRILBY_HIGHLANDS', 343, 953, FREE, 'in the boulder pocket')

# --- Western Wood North ----------------------------------------------------
region('WW-N', 'Western Wood North', ('HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 343, -3))
d('WW-N', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 467, 430, [[BOULDER('WW-N', 1)]],
  'exit; free from THIS start (push the boulder), but blocked outright for '
  'anyone entering through it')
d('WW-N', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 232, 263, [[FUSION]], 'POCKET')
d('WW-N', 'TREE_INTERIORS', 'WESTERN_WOODS_HEART_PIECE', 120, -56, [[FUSION]])
d('WW-N', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', -848, -1656, [[FUSION]], 'POCKET')
d('WW-N', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 6, 97, FREE, 'exit')
d('WW-N', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 48, 633, [[FUSION]], 'exit')
d('WW-N', 'HYRULE_FIELD', 'WESTERN_WOODS_NORTH', 416, 648, [[FUSION]],
  'POCKET entered from Western Wood Center, with a second fusion-only pocket inside it')

# --- Western Wood Center ---------------------------------------------------
region('WW-C', 'Western Wood Center', ('HYRULE_FIELD', 'WESTERN_WOODS_CENTER', 277, -2))
d('WW-C', 'HYRULE_FIELD', 'WESTERN_WOODS_CENTER', 48, -3, [[FUSION]],
  'POCKET, gated by the same fusion that opens WW-N (48,633)')
d('WW-C', 'HOUSE_INTERIORS_2', 'PERCY', 120, -88, [[FUSION]], 'inside that pocket')
d('WW-C', 'HYRULE_FIELD', 'WESTERN_WOODS_CENTER', 414, 15, FREE, 'exit')
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
d('CW', 'CASTOR_WILDS', 'MAIN', 39, 952, [[BOULDER('CW', 1)], [BOULDER('CW', 2)]],
  'exit to the southern pocket')
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
d('MW', 'TREE_INTERIORS', 'MINISH_WOODS_BUSINESS_SCRUB', 120, 120, FREE,
  "the business scrub's tree, tile (7,7). The survey says 'kinstone fusion "
  "maybe?' and the ROM half agrees - KINSTONE_27's world event fires at "
  "(528,456), which is this door - but the collision flood reaches it with "
  "nothing. Recorded FREE, the cheaper of the two readings, and flagged: if "
  "the door really is fusion-revealed this row is wrong and wants a fusion.")
d('MW', 'CAVES', 'KINSTONE_BUSINESS_SCRUB', 121, 122, FREE,
  'connected to the tree above, and carries the same fusion question')

# --- one item each --------------------------------------------------------
d('MW', 'LAKE_WOODS_CAVE', 'MAIN', 600, 767, [[MITTS]],
  'tile (37,47); this part of the cave holds two golden chests')
d('MW', 'MINISH_CRACKS', 'MINISH_WOODS_SOUTH', 120, 56, [[MINISH]], 'tile (7,3)')
d('MW', 'MINISH_WOODS', 'MAIN', 907, 599, [[FUSION]],
  'golden fusion chest, tile (56,37) - the fusion is the whole cost')
d('MW', 'MINISH_WOODS', 'MAIN', 667, 743, [[FUSION]],
  'golden fusion chest, tile (41,46) - the fusion is the whole cost')

# --- the Minish Village route ---------------------------------------------
# The Flippers here are the survey's own uncertainty, kept as a cost rather
# than dropped: "there are some leaves that can transport you across the
# water if you don't have zoras flippers, but I'm not sure if they're gated
# by a story flag event or not". Pricing the crossing at the Flippers is the
# expensive reading; if the leaves turn out to be free, every row below gets
# cheaper and a lot of Minish Woods opens up earlier.
d('MW', 'MINISH_PATHS', 'MINISH_VILLAGE', 136, 776, [[MINISH, FLIPPERS]],
  'tile (8,48), the way in; the leaves may be a cheaper crossing - unmeasured')
d('MW', 'MINISH_PATHS', 'MINISH_VILLAGE', 106, 519, [[MINISH, FLIPPERS]],
  'a kinstone fusion event on that path, tile (6,32)')
d('MW', 'MINISH_VILLAGE', 'MAIN', 520, 992, [[MINISH, FLIPPERS]],
  'tile (32,62); the village proper')
d('MW', 'MINISH_HOUSE_INTERIORS', 'FESTARI', 257, 79, [[MINISH, FLIPPERS]],
  "tile (16,4); the village's third door. The survey adds a story gate here "
  '- Festari has to have moved out of the doorway - and the mode pays it at '
  'boot (M_PRIEST_MOVE, with the rest of the village story), for the same '
  "reason the Crenel bean is pre-grown: it is a chore a run cannot do. So "
  'the token is gone rather than unpriced.')
d('MW', 'MINISH_WOODS', 'MAIN', 424, 840, [[MINISH, FLIPPERS]],
  'tile (26,52); the third village entrance, reached through the village')
d('MW', 'MINISH_WOODS', 'MAIN', 297, 704, [[MINISH, FLIPPERS]],
  'the wind crest, tile (18,44) - via the village')
d('MW', 'MINISH_WOODS', 'MAIN', 84, 679, [[MINISH, FLIPPERS]],
  'golden kinstone chest, tile (5,42) - via the village')
d('MW', 'MINISH_HOUSE_INTERIORS', 'MINISH_WOODS_BOMB', 120, 120, [[MINISH, FLIPPERS]],
  'via the village')
d('MW', 'DEEPWOOD_SHRINE_ENTRY', 'MAIN', 120, 232, [[MINISH, FLIPPERS]],
  'tile (7,14); the giant stump')
# The three southwest cave mouths are ONE linked room with three entrances.
# Left cave: a long ice path to a heart piece. Centre: a chest, half water.
# Right: a chest. The user wants all three wired as ? rooms carefully, which
# is a content job rather than a reachability one - recorded here so the
# reachability half is not measured twice.
d('MW', 'MINISH_CAVES', 'MINISH_WOODS_SOUTHWEST', 88, 280, [[MINISH, FLIPPERS]],
  'west mouth - via the village; the long ice path to a heart piece')
d('MW', 'MINISH_CAVES', 'MINISH_WOODS_SOUTHWEST', 312, 280, [[MINISH, FLIPPERS]],
  'centre mouth, tile (19,17) - via the village; a chest, and half water')
d('MW', 'MINISH_CAVES', 'MINISH_WOODS_SOUTHWEST', 536, 280, [[MINISH, FLIPPERS]],
  'east mouth, tile (33,17) - via the village; a chest')

# --- the Pacci pocket, which is not entered from Minish Woods at all -------
# The Great Fairy and the tree hollow above her sit in a pocket whose only
# way in is Eastern Hills North's own exit at (472,72), and reaching THAT
# inside Eastern Hills needs the Cane of Pacci. So the cane is the price of
# everything in here, even though nothing in Minish Woods asks for it.
d('MW', 'TREE_INTERIORS', 'MINISH_WOODS_GREAT_FAIRY', 120, 120, [[PACCI, FUSION]],
  "entered from Eastern Hills North's Pacci ledge, not from the woods; the "
  'survey believes the tree itself is fusion-gated as well')
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
d('LH', 'HYRULE_FIELD', 'LON_LON_RANCH', 712, 328, FREE,
  'exit; the border the player arrives through, walkable both ways')
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
# row. The Flippers ride along with it because the only measured way in is
# the Minish path from Minish Woods, which the MW block prices at
# [[MINISH, FLIPPERS]] (and whose Flippers term is that survey's own
# uncertainty about the floating leaves - if the leaves turn out to be free,
# this whole region gets cheaper with it).
#
# "No blockers except for various story flags/events" is the survey's verdict
# on every door not named below. The mode pays the village's story at boot
# (M_PRIEST_TALK, M_PRIEST_MOVE, M_ELDER_TALK1ST, M_ELDER_TALK2ND,
# MORI_00_KOBITO, KOBITO_MORI_1ST and the rest, in GameTask_Transition), for
# the same reason the Crenel bean is pre-grown: a run cannot do a chore that
# needs a story it is not playing. So those doors are FREE here rather than
# carrying an unpayable STORY token.
region('MV', 'Minish Village', ('MINISH_VILLAGE', 'MAIN', 520, 934),
       room_req=[[MINISH, FLIPPERS]],
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
# in. It is not true here: GameTask_Transition sets WATERBEAN_OUT and
# WATERBEAN_PUT at boot, and both CrenelBeanSprout entities in
# MT_CRENEL/ENTRANCE were measured sitting in action 4 - their grown state,
# climbable tile already laid - in the shipped difficulty-3 ROM. Same
# treatment, and the same reasoning, as the FESTARI row in Minish Woods: the
# gate is open before the run starts, so charging a route for it would price
# something no run can do anything about either way.
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
