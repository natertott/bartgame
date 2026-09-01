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
LONLON_KEY = 'lonlon_key'
GRAVEYARD_KEY = 'graveyard_key'

# World state. Anything that is not carried but must have HAPPENED.
FUSION = 'fusion'                        # an unnamed kinstone fusion
STORY = 'story_flags'
MAZE = 'maze_solved'                     # Royal Valley's lost woods
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


def d(key, area, room, x, y, req=None, note=''):
    SURVEY[key]['dests'].append(dict(area=area, room=room, local=(x, y),
                                     req=(req if req is not None else [[]]), note=note))


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
d('LLR', 'HYRULE_FIELD', 'LON_LON_RANCH', 32936, -1184, None,
  'POCKET, unreachable from this room at all - only from its Veil Falls side. '
  'Holds a fusion-rewarded chest.')
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
