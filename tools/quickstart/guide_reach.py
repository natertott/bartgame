"""Reachability for the places the ring never visits, read off the vanilla
walkthrough instead of walked.

WHAT THIS IS, AND IS NOT. world_reach.py is the user's walked survey of the
ring regions, and it is the source of truth for reach.h. This file is a
different thing: a first map of VEIL FALLS, HYRULE CASTLE (with the Elemental
Sanctuary and Dark Hyrule Castle), the CLOUD TOPS and all SIX DUNGEONS plus
the Royal Crypt, transcribed from Banjo2553's 100% walkthrough of the vanilla
game (the user uploaded it, Oct 2026) and cross-checked against three things
the ROM states outright:

    * the room names and ids       - include/roomid.h
    * the room-to-room doors       - src/data/transitions.c
    * the room rectangles          - data/map/room_headers.s, so that rooms a
                                     door table does not connect (dungeon
                                     rooms adjoin by shared edges and door
                                     TILES, not transition rows) can still be
                                     checked for adjacency with --adjacency
    * the Minish transform points  - data/map/entity_headers.s managers

Nothing here feeds reach.h. None of these areas is a ring region, and a
guide is an upper bound on knowledge, not a measurement: it tells you what
the vanilla route NEEDED, in vanilla, with vanilla's story state. Where this
mode has already changed the price (block pushes are the Power Bracelets,
story flags are pre-paid at boot, guards are swept) the note says so. Walk
anything here before wiring content to it.

THE ONE THING THESE AREAS HAVE IN COMMON. Every dungeon from the third on is
built around the SWORD-LEVEL CLONE mechanic - stand on glowing tiles, charge,
split into two/three/four Links to hold switches, push large blocks and
deflect cannonballs. The CLONES(n) token below marks every such gate. This
mode has no element forging and no sword levels, so CLONES(n) is UNPAYABLE
here today; the Power Bracelets stand in for the block pushes only. That
single fact decides how much of each dungeon a run could ever see, and the
per-area summaries at the bottom count it.

    python3 tools/quickstart/guide_reach.py            # the table
    python3 tools/quickstart/guide_reach.py --check    # names vs roomid.h/transitions.c
    python3 tools/quickstart/guide_reach.py --adjacency DEEPWOOD_SHRINE
    python3 tools/quickstart/guide_reach.py --summary  # per-area gate census
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import world_reach as W
from world_reach import (SWORD, SPIN, BRACELETS, BOMBS, BOW, FLIPPERS, CAPE, PACCI,
                         LANTERN, GRIP, BOOTS, MITTS, GUST, MINISH, OCARINA, FUSION,
                         FREE)

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

# ------------------------------------------------------------- vocabulary --
# Tokens the ring survey never needed. Same algebra as world_reach: a
# requirement is a list of alternative terms, a term is a list of tokens that
# must all hold.
SHIELD = 'shield'                 # any shield; the Smith's sword's companion
BOOMERANG = 'boomerang'
BIG_KEY = 'big_key'               # this dungeon's big key, found inside it


def KEYS(n):
    """The n-th locked door of this dungeon: n small keys must have been
    collected, which the guide's own route guarantees by the time it arrives.
    A token rather than a count because a run that enters mid-dungeon will
    not have them."""
    return 'small_keys:%d' % n


def CLONES(n):
    """A sword-level clone puzzle: split into n Links on glowing tiles.
    Vanilla pays it with the White Sword (2 elements -> 2, 3 -> 3) and the
    Four Sword (4). UNPAYABLE in QUICKSTART, which has no sword levels; the
    Power Bracelets cover the large-block pushes only, never the switches."""
    return 'clones:%d' % n


UNPAYABLE = {CLONES(2), CLONES(3), CLONES(4)}

GUIDE = {}


def area(key, name, start, room_req=None, note=''):
    GUIDE[key] = dict(name=name, start=start, dests=[], room_req=room_req or [], note=note)


def d(key, area_, room, req=FREE, note=''):
    GUIDE[key]['dests'].append(dict(area=area_, room=room, req=req, note=note))


# ================================================================ VEIL FALLS
#
# One big room (VEIL_FALLS/MAIN, 480x1008) with ten cave rooms, a dig cave, a
# top screen and the whirlwind to the Cloud Tops. Vanilla reaches it twice
# over: early for a heart piece, late for the climb to the sky. The ring
# does not visit it at all - the three border rows into it are compiled out
# under QUICKSTART (docs/QUICKSTART_RETARGETS.md, the three BLOCKED rows) -
# so this is the map for the day it opens.
#
# TWO SEPARATE ARRIVALS, and the guide routes back through North Hyrule Field
# between them rather than walking across, so until walked they are treated
# as two components joined only by water.
area('VF-S', 'Veil Falls (south strip, from Lon Lon Ranch)',
     ('VEIL_FALLS', 'MAIN', 456, 1000),
     note='entered from the Lon Lon Ranch Pacci ledge; LLR prices the ledge at '
          'the Cane of Pacci. Guide: "Use the Cane of Pacci on the hole and jump '
          'in to spring up to a ledge."')
d('VF-S', 'VEIL_FALLS', 'MAIN', FREE,
  'HEART PIECE #10, "just sitting there by the water" - no item at all once here')
d('VF-S', 'HYRULE_FIELD', 'LON_LON_RANCH', FREE,
  'exit, the second border row down to the Lon Lon pocket at (168,55) that the '
  "LLR survey prices NOT REACHABLE - this is its only way in. Vanilla's shared "
  'fusion #85 drops a chest there (KINSTONE_60, (168,40))')

area('VF-W', 'Veil Falls (west ledge, from North Hyrule Field)',
     ('VEIL_FALLS', 'MAIN', 8, 1000),
     note="entered from North Hyrule Field's north-east border; free from NHF")
d('VF-W', 'VEIL_FALLS', 'MAIN', [[FLIPPERS]],
  'HEART PIECE #32: "climb down and into the water, and just swim to the Piece '
  'of Heart"')
d('VF-W', 'DOJOS', 'TO_SPLITBLADE', [[FUSION, FLIPPERS]],
  "Splitblade's waterfall dojo. Opened by Grimblade's fusion (#27, Castle "
  'Garden), entered from the water: "jump into the water. Enter the waterfall"')
d('VF-W', 'DOJOS', 'SPLITBLADE', [[FUSION, FLIPPERS]], 'through the atrium above')
d('VF-W', 'VEIL_FALLS_DIG_CAVE', '0', [[FLIPPERS, MITTS]],
  'the lower dig spot: "swim right to the piece of land there. Dig through the '
  'grey wall" - a Blue Chuchu and two chests (50 shells, 50 rupees)')
d('VF-W', 'VEIL_FALLS_CAVES', 'ENTRANCE', [[FUSION]],
  'the gold-wall door at (56,482). The fuser is the NPC "Source of the Flow" '
  '(npc 0x4e at (56,509)) and the piece is KINSTONE_SOURCE_FLOW, which vanilla '
  "hands over in the Royal Crypt - so in this mode the fusion is only payable "
  'if a fuser offers it. Dark inside; the lantern is a convenience, not a gate')
d('VF-W', 'VEIL_FALLS_CAVES', 'EXIT', [[FUSION]],
  'upstairs from the entrance cave; Wisps (curse your sword - Gust Jar or '
  'Boomerang kills them, or walk round)')
d('VF-W', 'VEIL_FALLS', 'MAIN', [[FUSION]],
  'back outside at (216,450), the middle ledge; a Rock Chuchu lives here')
# Everything from here is also reachable by WARPING to the wind crest the
# player reveals on the plateau - the Ocarina IS an entrance, exactly as it
# is for Lake Hylia's crest pocket in the walked survey.
d('VF-W', 'VEIL_FALLS', 'MAIN', [[FUSION, GRIP], [OCARINA]],
  'the plateau with the wind crest: "avoid the Rock Chuchu and simply climb up '
  'the wall here. At the top, investigate the gravestone to reveal a wind '
  'crest". The climb is read as a Grip Ring wall from the word "climb"; the '
  'act tile has NOT been checked. A Golden Tektite spawns here after fusion #53')
d('VF-W', 'VEIL_FALLS_CAVES', 'HALLWAY_1F', [[FUSION, GRIP], [OCARINA]],
  'the cave on the plateau, doors at (280,66) and (200,116)')
d('VF-W', 'VEIL_FALLS_CAVES', 'HALLWAY_SECRET_ROOM', [[FUSION, GRIP, BOMBS], [OCARINA, BOMBS]],
  '"bomb the suspicious wall nearby and open the chest inside for 50 Mysterious '
  'Shells". No transition row - the wall is a bomb tile inside HALLWAY_1F')
d('VF-W', 'VEIL_FALLS_CAVES', 'HALLWAY_RUPEE_PATH', [[FUSION, GRIP], [OCARINA]],
  '"downstairs, a semi-flooded room with a bunch of Rupees, that leads you out '
  'to seemingly nowhere" - its south border lets out on the ledge at (168,194)')
d('VF-W', 'VEIL_FALLS_DIG_CAVE', '0', [[FUSION, GRIP, FUSION, MITTS], [OCARINA, FUSION, MITTS]],
  'the UPPER dig spot, off the Rupee Path ledge: fusion #72 (the lakeside '
  'Minish in Minish Village) "makes a platform appear at Veil Falls so you can '
  'access a dig spot" - HEART PIECE #43 and 50 shells. Same room id as the '
  'lower dig spot; whether it is one room with two mouths is unwalked')
d('VF-W', 'VEIL_FALLS_CAVES', 'HALLWAY_2F', [[FUSION, GRIP], [OCARINA]],
  '"going upstairs and exiting the left door" - a 100 rupee chest; both its '
  'border exits land back on the plateau at (168,34) and (344,34)')
d('VF-W', 'VEIL_FALLS_CAVES', 'HALLWAY_BLOCK_PUZZLE', [[FUSION, GRIP, BRACELETS], [OCARINA, BRACELETS]],
  'door at (216,322); a block puzzle, which this mode prices at the Power '
  'Bracelets like every other one. Leads on to the two secret rooms below')
d('VF-W', 'VEIL_FALLS_CAVES', 'HALLWAY_SECRET_STAIRCASE', [[FUSION, GRIP, BRACELETS], [OCARINA, BRACELETS]],
  'through the block puzzle; holds a Ghini')
d('VF-W', 'VEIL_FALLS_CAVES', 'SECRET_CHEST', [[FUSION, GRIP, BRACELETS], [OCARINA, BRACELETS]],
  'through the secret staircase')
d('VF-W', 'VEIL_FALLS_CAVES', 'HALLWAY_HEART_PIECE', [[FUSION, FLIPPERS]],
  'the TOPMOST waterfall, door at (56,40): fusion #54 (Gale, Cloud Tops) opens '
  'it; "drop off the west side, swim north, and enter the waterfall\'s opening" '
  '- HEART PIECE #40')
d('VF-W', 'VEIL_FALLS_TOP', '0', [[FUSION, GRIP], [OCARINA, GRIP]],
  '"exit out the right. Climb up to the top" - a second climb from the '
  "plateau. Biggoron sleeps behind the mountain (six BIG_GORON npcs authored "
  'into this one screen); fusion #48 wakes him, and the Mirror Shield trade is '
  'post-credits only in vanilla. The ladder and the giant whirlwind to the '
  'Cloud Tops are here')
d('VF-W', 'CLOUD_TOPS', 'CLOUD_TOPS', [[FUSION, GRIP], [OCARINA, GRIP]],
  'the whirlwind. Not a transition row - a scripted object. In this mode the '
  'Cloud Tops are the HUB side of the sky, so this is the one place the ring '
  'and the hub would touch on foot')


# ========================================================== HYRULE CASTLE
#
# The castle proper is five small rooms around one big hall. Vanilla locks
# every side room behind the story ("all other entryways are closed off by
# locked doors") and the main gate behind guards; this mode clears GUARD_1
# every frame (QuickStartClearCastleGuards), so the gate is a door.
area('HC', 'Hyrule Castle', ('HYRULE_CASTLE', '0', 0, 0),
     note='entered from the Castle Garden main door (CG (504,40)); in vanilla '
          'the garden guards turn you away until the story lets you in')
d('HC', 'HYRULE_CASTLE', '0', FREE,
  'the entrance hall; two GUARD_1 npcs at the inner door in vanilla, swept here')
d('HC', 'HYRULE_CASTLE', '3', FREE,
  'the lower hall, "look for a staircase to go down. There\'s one at the '
  'entrance room, up the left ladder" - door at (72,216) in room 0. The west '
  'border of this hall is the cellar tunnel from the garden hedge maze')
d('HC', 'HYRULE_CASTLE', '1', FREE,
  'the throne room, up either staircase from the lower hall (doors at (104,24) '
  'and (456,24) in room 3)')
d('HC', 'HYRULE_CASTLE', '2', [[W.STORY]],
  "Link's sick-bed room - the game resumes here after the festival. No exit "
  'row; adjoins the throne room by a door tile. Story-locked in vanilla')
d('HC', 'HYRULE_CASTLE', '4', [[W.STORY]],
  'a castle maid (MAID_1 npc). No exit row; story-locked in vanilla')
d('HC', 'HYRULE_CASTLE', '5', [[W.STORY]], 'no exit row; story-locked in vanilla')
d('HC', 'HYRULE_CASTLE_CELLAR', '1', FREE,
  'the tunnel from the garden: CELLAR_0 (ladder under bushes, garden NW alcove) '
  '-> CELLAR_1 -> this hall\'s west border. Priced from the garden side in '
  'world_reach.py at a sword')
d('HC', 'SANCTUARY_ENTRANCE', 'MAIN', FREE,
  '"a doorway with light coming out ... a little garden", door at (280,456) in '
  'the lower hall')
d('HC', 'SANCTUARY', 'HALL', FREE,
  'the glowing doorway. Vanilla opens it "once every 100 years" - a story flag, '
  'not an item')
d('HC', 'SANCTUARY', 'MAIN', FREE,
  'the pedestal room: place the sword, the elements infuse it. The clone tiles '
  'here are the tutorial for CLONES(2); the door back out needs one clone on '
  'a switch (CLONES(2)) in vanilla. Three NPC_UNK_4E "prevent player leaving" '
  'scripts guard the room')
d('HC', 'SANCTUARY', 'STAINED_GLASS', FREE,
  'the windows that play the backstory; opens after the Four Sword in vanilla')

# Dark Hyrule Castle REPLACES Hyrule Castle behind the same garden door once
# the Four Sword is forged (DHC's 1F_ENTRANCE exits to CASTLE_GARDEN/MAIN at
# (408,544), the same door). The whole dungeon is the Four Sword's dungeon:
# every cannon hall, every four-switch room and the curse-breaking beam are
# CLONES(4).
area('DHC', 'Dark Hyrule Castle', ('DARK_HYRULE_CASTLE', '1F_ENTRANCE', 0, 0),
     note='the final dungeon; swapped in for Hyrule Castle by story. Nearly '
          'everything past the first floor is a Four Sword puzzle')
d('DHC', 'DARK_HYRULE_CASTLE', '1F_ENTRANCE', FREE, 'pots and two fairies to the south')
d('DHC', 'DARK_HYRULE_CASTLE', 'B1_MAP', FREE,
  '"head west, climb, and kill the Moblin there. Head north ... fire bars ... '
  'downstairs"; doors at (264,216) and (552,216)')
d('DHC', 'DARK_HYRULE_CASTLE', 'B1_TO_PRISON_FIREBAR', FREE, 'the fire-bar hall')
d('DHC', 'DARK_HYRULE_CASTLE', 'B1_TO_PRISON', FREE)
d('DHC', 'DARK_HYRULE_CASTLE', 'B2_TO_PRISON', FREE)
d('DHC', 'DARK_HYRULE_CASTLE', 'B2_PRISON', FREE,
  'King Daltus in a cell, cursed; Minister Potho in the other. A transform '
  'stump stands here (136,56)')
d('DHC', 'DARK_HYRULE_CASTLE', 'B1_BOMB_WALL', [[BOMBS]],
  '"bomb the east wall. Inside, shrink using the pedestal" - stump at (72,72)')
d('DHC', 'DARK_HYRULE_CASTLE', 'B2_DROPDOWN', [[BOMBS, MINISH]],
  '"exit, go south, and drop down" as Minish, then back north into the prison '
  'through the Minish hole')
d('DHC', 'DARK_HYRULE_CASTLE', 'B2_PRISON', [[BOMBS, MINISH, CLONES(4)]],
  'the switch opens both cells; curing the king is "a charged sword beam" - the '
  'Four Sword, so CLONES(4). He gives SMALL KEY 1')
d('DHC', 'DARK_HYRULE_CASTLE', 'B1_MAP', [[KEYS(1)]],
  '"open the south locked door, the other one\'s a Mimic" - Moldorms, then the '
  'DUNGEON MAP. The dungeon can be left from here')
d('DHC', 'DARK_HYRULE_CASTLE', 'B1_CANNONS', [[CLONES(4)]],
  'cannonballs deflected by a line of clones; Floormasters; the blue/red tile '
  'walk; clone switches -> SMALL KEY 2')
d('DHC', 'DARK_HYRULE_CASTLE', 'B1_KEATONS', [[KEYS(2), CLONES(4)]],
  'through the B1 east locked door and a second cannon square; "a bunch of blue '
  'Keatons. Kill them all. Once they\'re gone, bomb around the southwest corner"')
d('DHC', 'DARK_HYRULE_CASTLE', 'B1_BEFORE_THRONE', [[KEYS(2), CLONES(4), BOMBS]],
  'Winders, then upstairs')
d('DHC', 'DARK_HYRULE_CASTLE', '1F_THRONE_ROOM', [[KEYS(2), CLONES(4), BOMBS]],
  'a Red Darknut; "push it aside to find a staircase" - the throne, which this '
  'mode would price at the Bracelets')
d('DHC', 'DARK_HYRULE_CASTLE', '1F_COMPASS', [[KEYS(2), CLONES(4), BOMBS]], 'the COMPASS, east of the throne')
d('DHC', 'DARK_HYRULE_CASTLE', 'B1_BELOW_THRONE', [[KEYS(2), CLONES(4), BOMBS, BRACELETS, LANTERN]],
  'under the throne: "this dark hall past Gibdos and Keese" - the lantern is '
  'how the guide walks it')
d('DHC', 'DARK_HYRULE_CASTLE_OUTSIDE', 'NORTHEAST', [[KEYS(2), CLONES(4), BOMBS, BRACELETS]],
  'out onto the battlements via the 1F/2F tower stairs; whirlwinds, a Bow '
  'Moblin, cannons. Gliding is free (Ezlo), no cape needed')
d('DHC', 'DARK_HYRULE_CASTLE_OUTSIDE', 'EAST', [[KEYS(2), CLONES(4), BOMBS, BRACELETS]],
  'a doorway with a clone block push (CLONES(4) in vanilla, Bracelets here)')
d('DHC', 'DARK_HYRULE_CASTLE_OUTSIDE', 'SOUTHEAST', [[KEYS(2), CLONES(4), BOMBS, BRACELETS]],
  'the south-east tower - "you can enter the tower, but you can\'t do anything '
  'to it" yet')
d('DHC', 'DARK_HYRULE_CASTLE_OUTSIDE', 'SOUTH', [[KEYS(2), CLONES(4), BOMBS, BRACELETS]],
  '"hit the switch from across the gap to create a bridge" (Boomerang or Bow), '
  'then the 2F entrance')
d('DHC', 'DARK_HYRULE_CASTLE', '2F_ENTRANCE', [[KEYS(2), CLONES(4), BOMBS, BRACELETS]],
  'four switches slashed at once by four clones -> the big door; two Ball and '
  'Chain Soldiers -> red portal; side doors open')
d('DHC', 'DARK_HYRULE_CASTLE', '2F_LEFT', [[KEYS(2), CLONES(4), BOMBS, BRACELETS, GUST]],
  'the platform to the grated floor; "grab a Bob-omb with the Gust Jar, then spit '
  'it out at the blocks"')
d('DHC', 'DARK_HYRULE_CASTLE', '2F_SPARKS', [[KEYS(2), CLONES(4), BOMBS, BRACELETS, GUST]],
  'a line of Sparks (free fairies with the Boomerang); north is the Black Knight')
d('DHC', 'DARK_HYRULE_CASTLE', '2F_BOSS_KEY', [[KEYS(6), CLONES(4), BOMBS, BRACELETS, GUST, BOW, LANTERN]],
  'four lock blocks, four keys from the four corners of 2F: Stalfos + two Wall '
  'Masters + shoot the eyes (BOW); two Darknuts + light the torches fast '
  '(LANTERN) + Ghinis; a Red Darknut + a clone spin on the switches (CLONES(4)); '
  'two Darknuts + the second tile puzzle + Ghinis + the tower. Then "split into '
  'four, and push aside the block. Open the large chest for the Big Key!"')
d('DHC', 'DARK_HYRULE_CASTLE', '2F_BOSS_DOOR', [[BIG_KEY, KEYS(6), CLONES(4), BOMBS, BRACELETS, GUST, BOW, LANTERN]],
  'the big door; Vaati is mid-ceremony, three bell chimes on the clock')
d('DHC', 'DARK_HYRULE_CASTLE_BRIDGE', 'MAIN', [[BIG_KEY, KEYS(6), CLONES(4), BOMBS, BRACELETS, GUST, BOW, LANTERN]])
d('DHC', 'DARK_HYRULE_CASTLE', '3F_KEATON_HALL_TO_VAATI', [[BIG_KEY, KEYS(6), CLONES(4), BOMBS, BRACELETS, GUST, BOW, LANTERN]],
  'a Ball and Chain Soldier, Keatons, clone switches')
d('DHC', 'DARK_HYRULE_CASTLE', '3F_TRIPLE_DARKNUT', [[BIG_KEY, KEYS(6), CLONES(4), BOMBS, BRACELETS, GUST, BOW, LANTERN]],
  'three Darknuts, then Vaati Reborn is fought here')
d('DHC', 'VAATIS_ARMS', 'FIRST', [[BIG_KEY, KEYS(6), CLONES(4), BOMBS, BRACELETS, GUST, BOW, LANTERN, PACCI, MINISH]],
  "Vaati's Wrath: the Cane of Pacci detaches an arm, a pedestal shrinks you, "
  'you go inside it. Two stumps authored into VAATI_3 (176,40)')
d('DHC', 'VAATIS_ARMS', 'SECOND', [[BIG_KEY, KEYS(6), CLONES(4), BOMBS, BRACELETS, GUST, BOW, LANTERN, PACCI, MINISH]],
  'the second arm is dark inside - the lantern again')


# ============================================================= CLOUD TOPS
#
# Three rooms stacked on one 1008x1008 footprint: the top layer, the middles
# and the bottoms. Holes drop you a layer, red whirlwinds lift you one.
# Clouds are dug with the Mole Mitts; five gold pieces are fused into
# "Mysterious Clouds" to start five windmills, which summon the whirlwind up
# to the Wind Tribe tower - this mode's HUB.
area('CT', 'Cloud Tops', ('CLOUD_TOPS', 'CLOUD_TOPS', 0, 0),
     note='entered by the Veil Falls whirlwind; in this mode the hub tower is '
          'entered from the top layer and the run DROPS out through a pit here')
d('CT', 'CLOUD_TOPS', 'CLOUD_TOPS', FREE,
  'the top layer; Hailey (fusion #53) and Gale (#54) stand at the arrival')
d('CT', 'CLOUD_TOPS', 'CLOUD_MIDDLES', FREE, 'drop through any hole; red whirlwinds come back up')
d('CT', 'CLOUD_TOPS', 'CLOUD_BOTTOMS', FREE, 'drop again')
d('CT', 'CLOUD_TOPS', 'CLOUD_TOPS', [[MITTS]],
  'every chest and most loose pieces are under diggable cloud: "dig through the '
  'clouds a bit to access the chest here"')
d('CT', 'CLOUD_TOPS', 'CLOUD_MIDDLES', [[GUST], [BOW]],
  'two Lakitus block two paths: "Use the Gust Jar to suck away its cloud" (or '
  'arrows - the enemy list says the Bow kills them)')
d('CT', 'CLOUD_TOPS', 'CLOUD_MIDDLES', [[SWORD]],
  'two gold pieces are released by killing Cloud Piranhas: "kill the Cloud '
  'Piranhas and a bit of the cloud will disperse, revealing a golden Kinstone"')
d('CT', 'WIND_TRIBE_TOWER', 'ENTRANCE', [[FUSION, FUSION, FUSION, FUSION, FUSION, MITTS]],
  'five Mysterious Cloud fusions (KINSTONE_MYSTERIOUS_CLOUD_*) with five gold '
  'pieces (three in cloud-covered chests, two from piranhas) start the '
  'windmills; "a giant whirlwind makes its appearance". The tower is this '
  "mode's hub, so in QUICKSTART this edge runs the other way: the hub is where "
  'you start and the Cloud Tops pit is where you leave')
d('CT', 'WIND_TRIBE_TOWER', 'FLOOR_1', FREE, 'Gregal (Light Arrow if you saved him) and Caprice (fusion #55)')
d('CT', 'WIND_TRIBE_TOWER', 'FLOOR_2', FREE, 'Flurris (fusions #56, #57)')
d('CT', 'WIND_TRIBE_TOWER', 'FLOOR_3', FREE, 'Siroc (fusions #58, #59) opens the way to the Palace')
d('CT', 'WIND_TRIBE_TOWER_ROOF', '0', FREE,
  'the roof whirlwind to the Palace of Winds. THE HUB ROOF: the Palace is one '
  'whirlwind from where every run begins')


# ======================================================== DEEPWOOD SHRINE
#
# The first dungeon, and the only one with NO clone puzzle. Entirely
# Minish-sized; entered through the giant stump in Minish Woods (which the
# walked MW survey now prices at the Minish Cap alone). Its item is the Gust
# Jar, which this mode grants at spawn, so a run arrives here already holding
# the dungeon's own key item.
area('DWS', 'Deepwood Shrine', ('DEEPWOOD_SHRINE', 'ENTRANCE', 0, 0),
     room_req=[[MINISH]],
     note='Minish-sized throughout; the Gust Jar is its dungeon item and this '
          "mode's starting kit. Four small keys, a big key, no clones")
d('DWS', 'DEEPWOOD_SHRINE_ENTRY', 'MAIN', FREE, 'the forecourt; HEART PIECE #1 lies in front of it')
d('DWS', 'DEEPWOOD_SHRINE', 'ENTRANCE', FREE,
  '"push aside the front statue to enter the next room". Two web-covered '
  'staircases (GUST) lead up to a 20-rupee chest and to the boss door')
d('DWS', 'DEEPWOOD_SHRINE', 'TORCHES', [[SWORD]],
  'Sluggulas; "step on the floor switches to light the torches, making a chest '
  'appear" - SMALL KEY 1')
d('DWS', 'DEEPWOOD_SHRINE', 'LEVER', [[KEYS(1)]],
  '"grab the handle in the wall with R. Pull it far enough and a bridge will '
  'appear"; the first mushroom fling')
d('DWS', 'DEEPWOOD_SHRINE', 'BARREL', [[KEYS(1)]],
  'the hub room: vines burnt by two torch switches (one needs a statue pushed '
  'onto it), then the rotating barrel - INSIDE_BARREL - is the door to four '
  'rooms')
d('DWS', 'DEEPWOOD_SHRINE', 'INSIDE_BARREL', [[KEYS(1)]], 'walk inside it to turn it')
d('DWS', 'DEEPWOOD_SHRINE', 'MAP', [[KEYS(1)]],
  'west of the barrel: a Mulldozer, the long mushroom fling, the DUNGEON MAP')
d('DWS', 'DEEPWOOD_SHRINE', 'POT_BRIDGE', [[KEYS(1)]],
  'a Pesto; "push it [the pot] east, until it\'s on top of the switch. A bridge forms"')
d('DWS', 'DEEPWOOD_SHRINE', 'DOUBLE_STATUE', [[KEYS(1)]],
  'two statues on two switches, one pulled into the alcove - SMALL KEY 2')
d('DWS', 'DEEPWOOD_SHRINE', 'PILLARS', [[KEYS(2)]],
  'the upper-right barrel exit and a locked door; mushroom north, island switch, '
  'bridge, fling')
d('DWS', 'DEEPWOOD_SHRINE', 'MULLDOZER', [[KEYS(2)]],
  'ceiling Sluggulas, a statue onto a switch, then "Kill the Mulldozers to get a '
  'SMALL KEY" - key 3')
d('DWS', 'DEEPWOOD_SHRINE', 'BUTTON', [[KEYS(3)]],
  'up the small ladder: Puffstools and "the floor switch to open a door to the '
  'barrel room"')
d('DWS', 'DEEPWOOD_SHRINE', 'MADDERPILLAR', [[KEYS(3)]],
  'west through the locked door: the Madderpillar (nose, then tail) -> the GUST '
  'JAR. Webbing to the south hides HEART PIECE #3')
d('DWS', 'DEEPWOOD_SHRINE', 'BLUE_PORTAL', [[KEYS(3), GUST]],
  'north of the barrel, "the room filled with dust and Puffstools": suck the '
  'dust off three switches -> a blue portal and two 10-shell chests. HEART PIECE '
  '#4 is on its ledge, reached by the matching portal at the entrance')
d('DWS', 'DEEPWOOD_SHRINE', 'LILY_PAD_WEST', [[KEYS(3), GUST]],
  'fall through the web-covered hole in the barrel: lilypad steering with the '
  'Gust Jar, pots onto switches')
d('DWS', 'DEEPWOOD_SHRINE', 'LILY_PAD_EAST', [[KEYS(3), GUST]],
  'the far end of the water: pot on switch -> SMALL KEY 4')
d('DWS', 'DEEPWOOD_SHRINE', 'COMPASS', [[KEYS(3), GUST]],
  '"push the right block up and the left block left. Open the big chest for the '
  'dungeon\'s Compass"; its door pairs with STAIRS_TO_B1')
d('DWS', 'DEEPWOOD_SHRINE', 'STAIRS_TO_B1', [[KEYS(3), GUST]])
d('DWS', 'DEEPWOOD_SHRINE', 'BOSS_KEY', [[KEYS(4), GUST]],
  'north through the last locked door: a chain of mushrooms pulled by the Gust '
  'Jar -> the BIG KEY, and a red portal back to the entrance')
d('DWS', 'DEEPWOOD_SHRINE', 'BOSS_DOOR', [[GUST]],
  'up the entrance\'s second staircase, mushrooms across -> the big door')
d('DWS', 'DEEPWOOD_SHRINE_BOSS', 'MAIN', [[GUST, BIG_KEY]],
  'Big Green ChuChu: suck the goo from its base, slash it when it falls. The '
  'EARTH ELEMENT - this mode\'s own win item')


# ========================================================= CAVE OF FLAMES
#
# Entered from Mt Crenel's Cavern of Flames forecourt (the CREN survey's own
# start). Normal-sized with four Minish stumps inside; its item is the Cane
# of Pacci, found half-way, after which everything is "flip it". No clones.
area('COF', 'Cave of Flames', ('CAVE_OF_FLAMES', 'ENTRANCE', 0, 0),
     note='bombs early (or a lured Bob-omb), the Cane of Pacci half-way, two '
          'small keys, four stumps, no clones. The Gust Jar is handy throughout '
          'but the guide names a sword alternative every time')
d('COF', 'CAVE_OF_FLAMES', 'ENTRANCE', FREE)
d('COF', 'CAVE_OF_FLAMES', 'NORTH_ENTRANCE', FREE, '"north leads nowhere"')
d('COF', 'CAVE_OF_FLAMES', 'BOB_OMB_WALL', [[BOMBS]],
  '"Avoid the Bob-ombs or use them to blast away the north wall" - the enemy '
  'can pay this one for you')
d('COF', 'CAVE_OF_FLAMES', 'COMPASS', [[BOMBS, SHIELD], [BOMBS, PACCI]],
  'Spiked Beetles must be flipped ("run into your shield" or the cane) and '
  'killed before the COMPASS chest appears')
d('COF', 'CAVE_OF_FLAMES', 'MAIN_CART', [[BOMBS]],
  'west past a Rupee Like, downstairs, the first minecart; "You will go FLYING '
  'into a new room"')
d('COF', 'CAVE_OF_FLAMES', 'CART_WEST', [[BOMBS]], 'where the cart stops')
d('COF', 'CAVE_OF_FLAMES', 'HELMASAUR_FIGHT', [[BOMBS]],
  'a second Bob-omb wall; "kill all the Helmasaurs and a pedestal will appear" '
  '- stump (120,136)')
d('COF', 'CAVE_OF_FLAMES', 'MINISH_LAVA_ROOM', [[BOMBS, MINISH]],
  'through the north-east Minish hole and south: pedestal (248,168), slash the '
  'fires, the DUNGEON MAP; crumbling rock platforms over lava; a kinstone chest '
  'and a switch')
d('COF', 'CAVE_OF_FLAMES', 'ROLLOBITE_LAVA_ROOM', [[BOMBS, MINISH]],
  'Rollobites into the holes -> 50 rupees; a whirlwind glide; "push the chest on '
  'the pedestal to the left, into the hole" -> SMALL KEY 1')
d('COF', 'CAVE_OF_FLAMES', 'CART_TO_SPINY_CHU', [[BOMBS, MINISH, KEYS(1)]],
  'the locked door, the lever that switches the track, the second ride')
d('COF', 'CAVE_OF_FLAMES', 'a', [[BOMBS, MINISH, KEYS(1)]],
  'HEART PIECE #8: "walk along the minecart track to the other side. Bomb the '
  'wall and head in". Room letter is a guess from the names left unnamed')
d('COF', 'CAVE_OF_FLAMES', 'SPINY_CHU', [[BOMBS, MINISH, KEYS(1)]],
  '"drop down to fight eight Spiny ChuChus" -> the CANE OF PACCI')
d('COF', 'CAVE_OF_FLAMES', 'AFTER_CANE', [[BOMBS, MINISH, KEYS(1), PACCI]],
  'flip the rock, fire the cane into the hole, jump: "Link will get flung to a '
  'high ledge!" - switch, door, blue portal')
d('COF', 'CAVE_OF_FLAMES', 'MINISH_SPIKES', [[BOMBS, MINISH, KEYS(2), PACCI]],
  'flip the minecart (PACCI) for SMALL KEY 2, then the locked door and '
  'downstairs: two stumps (584,152),(72,72), Traps and Chasers')
d('COF', 'CAVE_OF_FLAMES', 'TOMPAS_DOOM', [[BOMBS, MINISH, KEYS(2), PACCI]],
  'the lava platform crossing - flip the spiked platforms before boarding; the '
  'name is the decomp\'s own and the match to the guide is a guess')
d('COF', 'CAVE_OF_FLAMES', 'BOSSKEY_PATH1', [[BOMBS, MINISH, KEYS(2), PACCI]],
  'whirlwinds and cane holes over the big lava room; a 100-rupee chest, a '
  'kinstone chest')
d('COF', 'CAVE_OF_FLAMES', 'BOSSKEY_PATH2', [[BOMBS, MINISH, KEYS(2), PACCI]],
  '"glide north over to the large chest on the ledge. Open it to get the Big Key!"')
d('COF', 'CAVE_OF_FLAMES', 'BOSS_DOOR', [[BOMBS, MINISH, KEYS(2), PACCI]],
  'red portal back to the start; "flipping the rock platform that comes along" '
  'reaches the door')
d('COF', 'CAVE_OF_FLAMES', 'BEFORE_GLEEROK', [[BOMBS, MINISH, KEYS(2), PACCI, BIG_KEY]],
  'the supply room: pots with fairies')
d('COF', 'CAVE_OF_FLAMES_BOSS', '0', [[BOMBS, MINISH, KEYS(2), PACCI, BIG_KEY]],
  "Gleerok: the cane flips its shell, walk its neck, slash the jewel. FIRE ELEMENT")


# ======================================================= FORTRESS OF WINDS
#
# The third dungeon and the first built on clones: three CLONES(2) puzzles
# stand between the entrance hall and two of the four small keys, and the
# Bow (found in Castor Wilds, not here) opens the first locked route. Its own
# item, the Mole Mitts, comes late. Eight Minish stumps, more than any other
# area in the game.
area('FOW', 'Fortress of Winds', ('OUTER_FORTRESS_OF_WINDS', 'ENTRANCE_HALL', 0, 0),
     note='entered from the Wind Ruins\' fortress forecourt, which the WR survey '
          'prices NOT REACHABLE (behind a kill-all-armos event). The Bow is a '
          'prerequisite, the Mole Mitts are the prize, and CLONES(2) gates two '
          'of the four keys')
d('FOW', 'OUTER_FORTRESS_OF_WINDS', 'ENTRANCE_HALL', FREE, 'four doorways and the heart-piece door')
d('FOW', 'FORTRESS_OF_WINDS', 'EAST_STAIRS_1F', FREE, '"the second right doorway. It should lead to a room that has a Minish hole"')
d('FOW', 'FORTRESS_OF_WINDS', 'EAST_STAIRS_2F', FREE,
  'a Spark (Boomerang -> fairy), a Stalfos, two levers -> two kinstone chests')
d('FOW', 'OUTER_FORTRESS_OF_WINDS', '2F', FREE, 'the 2F walkway; dirt walls everywhere (MITTS later)')
d('FOW', 'OUTER_FORTRESS_OF_WINDS', '3F', FREE)
d('FOW', 'FORTRESS_OF_WINDS', 'EAST_KEY_LEVER', [[CLONES(2)]],
  'two switches by a door that "won\'t stay down"; skulls and an Armos on '
  'glowing tiles; split to hold both. Then a pedestal (two stumps: (392,104), '
  '(56,280)), climb INTO the remaining Armos to switch it on, destroy it, pull '
  'the lever: SMALL KEY 1 drops to 1F')
d('FOW', 'FORTRESS_OF_WINDS', 'HEART_PIECE', [[CLONES(2), MINISH]],
  'HEART PIECE #16: shrink on 3F, drop through the hole to 1F, "head east '
  'through the hole, then un-shrink"; leave by pushing a block. Stump (184,72)')
d('FOW', 'FORTRESS_OF_WINDS', 'WEST_STAIRS_1F', FREE, 'the leftmost door')
d('FOW', 'FORTRESS_OF_WINDS', 'WEST_STAIRS_2F', [[BOW]],
  '"an odd mark on the west wall. Line up with it and shoot an arrow at it, and '
  'the door will open"; Stalfos, Rupee Likes, a ladder')
d('FOW', 'FORTRESS_OF_WINDS', 'PIT_PLATFORMS', [[BOW]],
  'moving platforms; "quickly shoot arrows into each of the eyes on the north '
  'wall to open the door"')
d('FOW', 'FORTRESS_OF_WINDS', 'DOUBLE_EYEGORE', [[BOW, CLONES(2)]],
  'split onto the switches, destroy the two Eyegores -> the COMPASS')
d('FOW', 'FORTRESS_OF_WINDS', 'WEST_KEY_LEVER', [[BOW, CLONES(2)]],
  'the east eyes from the rightmost platform; Ropes, skulls, a three-stage '
  'clone block puzzle, the lever: SMALL KEY 2 drops to 1F')
d('FOW', 'FORTRESS_OF_WINDS', 'CENTER_STAIRS_1F', FREE, 'the middle door')
d('FOW', 'FORTRESS_OF_WINDS', 'MAIN_2F', [[BOW]],
  'Stalfos and Eyegores, two locked doors, and up the stairs the DUNGEON MAP. '
  'The Eyegores only die to arrows')
d('FOW', 'FORTRESS_OF_WINDS', 'ARROW_EYE_BRIDGE', [[BOW, KEYS(1)]],
  'the left locked door: a moving platform, then "shoot the eyes on the west '
  'wall while being on the lookout for the Wallmaster" -> a bridge')
d('FOW', 'FORTRESS_OF_WINDS', 'DARKNUT_ROOM', [[BOW, KEYS(1)]],
  'both doors shut, a Darknut (shield his swing, hit his side); blue portal; '
  'green Traps to a switch')
d('FOW', 'FORTRESS_OF_WINDS', 'ENTRANCE_MOLE_MITTS', [[BOW, KEYS(1), BOMBS]],
  '"a couple of skulls with a space between them. Place a bomb there" -> the '
  'MOLE MITTS, and 100 rupees behind dirt')
d('FOW', 'OUTER_FORTRESS_OF_WINDS', 'MOLE_MITTS', [[BOW, KEYS(1), BOMBS]])
d('FOW', 'FORTRESS_OF_WINDS', 'ROTATING_SPIKE_TRAPS', [[BOW, KEYS(2)]],
  'the right locked door: a receding bridge on a lever, Floormasters '
  '(Boomerang-stun or one arrow), a pedestal appears; rolling spiked logs')
d('FOW', 'FORTRESS_OF_WINDS', 'PILLAR_CLONE_BUTTONS', [[BOW, KEYS(2), CLONES(2)]],
  'two statues and four switches: statues on two, clones on the other two -> '
  'SMALL KEY 3')
d('FOW', 'FORTRESS_OF_WINDS', 'MINISH_HOLE', [[BOW, KEYS(3), CLONES(2), MINISH]],
  'through the third locked door as Minish, between the logs, into a small hole')
d('FOW', 'OUTER_FORTRESS_OF_WINDS', 'SMALL_KEY', [[BOW, KEYS(3), CLONES(2), MINISH, MITTS]],
  '"get yourself back to normal size, and step on the switch to make a SMALL KEY '
  'appear. Dig through the dirt over to it" - key 4. Stump (40,72)')
d('FOW', 'FORTRESS_OF_WINDS', 'WALLMASTER_MINISH_PORTAL', [[BOW, KEYS(3), CLONES(2), MINISH, MITTS]],
  'stump (136,104); the room between the spike traps and the boss-key stair')
d('FOW', 'FORTRESS_OF_WINDS', 'BOSS_KEY', [[BOW, KEYS(4), CLONES(2), MINISH, MITTS]],
  'dig to the ladder past Moldorms, "open the locked door and drop down the '
  'right hole. Open the large chest for the Big Key!"')
d('FOW', 'FORTRESS_OF_WINDS', 'WIZZROBE', [[MITTS]],
  'the 1F dirt room\'s hidden doorway: two Wizzrobes -> 80 shells. Free of the '
  'dungeon\'s route; only the mitts')
d('FOW', 'FORTRESS_OF_WINDS', 'STALFOS', [[MITTS]], 'the 2F dirt rooms and their kinstone chests')
d('FOW', 'FORTRESS_OF_WINDS', 'BEFORE_MAZAAL', [[BOW, MITTS]],
  'south of the map room: "dig out the statue and push it onto the floor switch", '
  'a ladder, dig to the doorway; push the odd block -> red portal')
d('FOW', 'FORTRESS_OF_WINDS', 'MAZAAL', [[BOW, MITTS, BIG_KEY, MINISH]],
  'the supply room, then Mazaal: arrows into the palms, shrink at a pedestal '
  '(stumps (56,56),(312,56)), walk into the head, dig for the glowing pillar')
d('FOW', 'INNER_MAZAAL', 'MAIN', [[BOW, MITTS, BIG_KEY, MINISH]], 'inside the head')
d('FOW', 'FORTRESS_OF_WINDS_TOP', 'MAIN', [[BOW, MITTS, BIG_KEY, MINISH]],
  'the tablet of the Wind Tribe; Zeffa drops the OCARINA OF WIND. No element here')


# ======================================================= TEMPLE OF DROPLETS
#
# Minish-sized, ice and water. Unusually the BIG KEY is the first thing
# found; the dungeon is then two halves of a sunlight puzzle whose levers are
# CLONES(2). The Flippers (from the library, not here) are needed almost at
# once; the Flame Lantern is the prize, two-thirds in.
area('TOD', 'Temple of Droplets', ('TEMPLE_OF_DROPLETS', 'ENTRANCE', 0, 0),
     room_req=[[MINISH]],
     note='entered by shrinking on the stump on Lake Hylia\'s ice island '
          '(LH-LADDER prices it at boots + Minish + Flippers/cape). Minish-sized '
          'throughout. Flippers early, CLONES(2) on both sunlight levers and four '
          'block puzzles, the lantern as the prize')
d('TOD', 'TEMPLE_OF_DROPLETS', 'ENTRANCE', FREE)
d('TOD', 'TEMPLE_OF_DROPLETS', 'ELEMENT', FREE,
  'the central hall: the boss door south, the element frozen in a block of ice '
  'with a frozen Octorok beside it')
d('TOD', 'TEMPLE_OF_DROPLETS', 'NORTH_SPLIT_ROOM', FREE,
  '"possessed pots ... torches in the middle of the room that shoot fireballs"; '
  'name matched from position, not certain')
d('TOD', 'TEMPLE_OF_DROPLETS', 'NORTHWEST_STAIRS', FREE,
  'downstairs: "push the handle and the ceiling will open up" - sunlight')
d('TOD', 'TEMPLE_OF_DROPLETS', 'WEST_HOLE', FREE,
  'fall down the hole: an ice block with SMALL KEY 1 inside, pushed into the sun')
d('TOD', 'TEMPLE_OF_DROPLETS', 'BOSS_KEY', [[KEYS(1)]],
  'the locked door and three ice blocks: "push the remaining block left, up, left, '
  'down, left, up, right. The ice will melt, and you can pick up the Big Key!"')
d('TOD', 'TEMPLE_OF_DROPLETS', 'WEST_WATERFALL_SOUTHWEST', [[BIG_KEY]],
  'through the big door and the hall\'s south-west doorway: the DUNGEON MAP down '
  'a rupee tunnel')
d('TOD', 'TEMPLE_OF_DROPLETS', 'WATERFALL_NORTHWEST', [[BIG_KEY, FLIPPERS, GUST]],
  '"Get in the water, dive when the spiked log comes rolling ... use the Gust Jar '
  'on the mushroom to get across, and step on the switch"')
d('TOD', 'TEMPLE_OF_DROPLETS', 'SPIKE_BAR_FLIPPER_ROOM', [[BIG_KEY, FLIPPERS]],
  'swim down the waterfall, dive under the log, the switch; the blocks "forming '
  'the shape of a pot" - dive inside for SMALL KEY 2')
d('TOD', 'TEMPLE_OF_DROPLETS', 'LILYPAD_B2_WEST', [[BIG_KEY, FLIPPERS, KEYS(2), GUST]],
  'climb by the waterfall, unlock the door, the lilypad released by a switch '
  'and steered with the Gust Jar')
d('TOD', 'TEMPLE_OF_DROPLETS', 'ICE_MADDERPILLAR', [[BIG_KEY, FLIPPERS, KEYS(2), GUST]],
  'east on the lilypad: a Madderpillar -> the COMPASS behind it')
d('TOD', 'TEMPLE_OF_DROPLETS', 'COMPASS', [[BIG_KEY, FLIPPERS, KEYS(2), GUST]])
d('TOD', 'TEMPLE_OF_DROPLETS', 'LILYPAD_ICE_BLOCKS', [[BIG_KEY, FLIPPERS, KEYS(2), GUST]],
  'north on the lilypad: the ice-block switch puzzle ("push it down, right, down, '
  'left, and north") and a 50-rupee chest')
d('TOD', 'TEMPLE_OF_DROPLETS', 'STAIRS_TO_SCISSORS_MINIBOSS', [[BIG_KEY, FLIPPERS, KEYS(2), GUST]],
  '"it\'s pitch-black in here, so be careful" - walkable dark, the lantern not '
  'yet owned')
d('TOD', 'TEMPLE_OF_DROPLETS', 'SCISSORS_MINIBOSS', [[BIG_KEY, FLIPPERS, KEYS(2), GUST]],
  'three Scissors Beetles -> a blue portal')
d('TOD', 'TEMPLE_OF_DROPLETS', 'BLOCK_CLONE_ICE_BRIDGE', [[BIG_KEY, FLIPPERS, KEYS(2), GUST, CLONES(2)]],
  'the FIRST giant lever: "can\'t be moved by just one" - sunlight melts the '
  'small ice block and opens the east half')
d('TOD', 'TEMPLE_OF_DROPLETS', 'ICE_CORNER', [[BIG_KEY, FLIPPERS, KEYS(2), GUST, CLONES(2)]],
  'the south-east doorway of the hall: kinstone chests, Pestos, a line of green '
  'Traps')
d('TOD', 'TEMPLE_OF_DROPLETS', 'HOLE_TO_BLUE_CHU_KEY', [[BIG_KEY, FLIPPERS, KEYS(2), GUST, CLONES(2)]],
  'two floors of levers opening and closing the ceiling to melt a frozen chest: '
  'SMALL KEY 3')
d('TOD', 'TEMPLE_OF_DROPLETS', 'BLUE_CHU_KEY_LEVER', [[BIG_KEY, FLIPPERS, KEYS(2), GUST, CLONES(2)]])
d('TOD', 'TEMPLE_OF_DROPLETS', 'BLUE_CHU_KEY', [[BIG_KEY, FLIPPERS, KEYS(2), GUST, CLONES(2)]])
d('TOD', 'TEMPLE_OF_DROPLETS', 'TO_BLUE_CHU', [[BIG_KEY, FLIPPERS, KEYS(3), GUST, CLONES(2)]],
  'the locked door; a lever lets the light in and "blue goo drops in"')
d('TOD', 'TEMPLE_OF_DROPLETS', 'BLUE_CHU', [[BIG_KEY, FLIPPERS, KEYS(3), GUST, CLONES(2)]],
  'Big Blue ChuChu, electric - wait it out, suck the base, slash. The FLAME '
  'LANTERN. This mode already fields a Blue ChuChu boss elsewhere')
d('TOD', 'TEMPLE_OF_DROPLETS', 'DARK_SCISSOR_BEETLES', [[BIG_KEY, FLIPPERS, KEYS(3), GUST, CLONES(2), LANTERN]],
  'melt the ice, downstairs for 100 rupees, "Light your torch and keep it out as '
  'you fight three Scissors Beetles"')
d('TOD', 'TEMPLE_OF_DROPLETS', 'DARK_MAZE', [[BIG_KEY, FLIPPERS, KEYS(3), GUST, CLONES(2), LANTERN]],
  'torches unblock paths; kinstone chests; a cracked wall')
d('TOD', 'TEMPLE_OF_DROPLETS', 'MULLDOZER_KEY', [[BIG_KEY, FLIPPERS, KEYS(3), GUST, CLONES(2), LANTERN, BOMBS]],
  '"Bomb it and head inside. Fight off all the Mulldozers to get a SMALL KEY" - key 4')
d('TOD', 'TEMPLE_OF_DROPLETS', 'BLOCK_CLONE_PUZZLE', [[BIG_KEY, FLIPPERS, KEYS(4), GUST, CLONES(2), LANTERN, BOMBS]],
  'past the Winders and the icy path: four re-splits to push four blocks')
d('TOD', 'TEMPLE_OF_DROPLETS', 'BLOCK_CLONE_BUTTON_PUZZLE', [[BIG_KEY, FLIPPERS, KEYS(4), GUST, CLONES(2), LANTERN, BOMBS]],
  'two ice blocks, then clones on the remaining switches open the door')
d('TOD', 'TEMPLE_OF_DROPLETS', 'MULLDOZERS_FIRE_BARS', [[BIG_KEY, FLIPPERS, KEYS(4), GUST, CLONES(2), LANTERN, BOMBS]],
  'Mulldozers, melt the ice, a clone block push')
d('TOD', 'TEMPLE_OF_DROPLETS', '9_LANTERNS', [[BIG_KEY, FLIPPERS, KEYS(4), GUST, CLONES(2), LANTERN, BOMBS]],
  '"very simple: light all the torches to open the door"')
d('TOD', 'TEMPLE_OF_DROPLETS', 'FLAMEBAR_BLOCK_PUZZLE', [[BIG_KEY, FLIPPERS, KEYS(4), GUST, CLONES(2), LANTERN, BOMBS]],
  'swim under spiked logs, Scissors Beetles; Pestos, pots and a switch -> red '
  'portal. Name matched from position')
d('TOD', 'TEMPLE_OF_DROPLETS', 'BEFORE_TWIN_MADDERPILLARS', [[BIG_KEY, FLIPPERS, KEYS(4), GUST, CLONES(2), LANTERN, BOMBS]],
  '"bomb the north wall as the tiles made out as an arrow clearly point to"')
d('TOD', 'TEMPLE_OF_DROPLETS', 'TWIN_MADDERPILLARS', [[BIG_KEY, FLIPPERS, KEYS(4), GUST, CLONES(2), LANTERN, BOMBS]],
  'burn the webbing, two Madderpillars at once')
d('TOD', 'TEMPLE_OF_DROPLETS', 'AFTER_TWIN_MADDERPILLARS', [[BIG_KEY, FLIPPERS, KEYS(4), GUST, CLONES(2), LANTERN, BOMBS]],
  'the ice bridge, upstairs, Mulldozers, back to the hall\'s SECOND giant lever '
  '(CLONES(2)) - the ice melts and the Octorok swallows the element')
d('TOD', 'TEMPLE_OF_DROPLETS', 'BIG_OCTO', [[BIG_KEY, FLIPPERS, KEYS(4), GUST, CLONES(2), LANTERN, BOMBS, SHIELD, BOOTS]],
  'Big Octorok: shield its rocks back, dash (BOOTS) behind it and light its '
  'flower (LANTERN). WATER ELEMENT. This mode already implements this boss')


# ============================================================ ROYAL CRYPT
#
# A mini-dungeon under the Royal Valley graveyard. Opened by CLONES(3) on
# three switches in vanilla (the RV survey prices the giant gravestone push
# at the Bracelets); inside, two of three keys are CLONES(3) puzzles and the
# torch room needs the lantern. Everything a Four-Sword-less run cannot do.
area('CRYPT', 'Royal Crypt', ('ROYAL_CRYPT', 'ENTRANCE', 0, 0),
     note='the RV survey\'s CRYPT row prices the way in at lantern + maze + '
          'graveyard key + bracelets. Inside: three keys, two behind CLONES(3), '
          'and a mandatory lantern')
d('CRYPT', 'ROYAL_CRYPT', 'ENTRANCE', FREE)
d('CRYPT', 'ROYAL_CRYPT', 'GIBDO', FREE,
  'two Gibdos, "one is holding a SMALL KEY and the other holds bombs". The '
  'lantern burns their wrappings into Stalfos but a sword does the job')
d('CRYPT', 'ROYAL_CRYPT', 'MUSHROOM_PIT', [[KEYS(1)]],
  'the mushroom fling and three locked doors, two of them Door Mimics: the '
  'middle one')
d('CRYPT', 'ROYAL_CRYPT', 'KEY_BLOCK', [[KEYS(1), CLONES(3)]],
  'east: clones on switches -> SMALL KEY 2; west: three clones riding platforms '
  'past blocks -> SMALL KEY 3; two key blocks')
d('CRYPT', 'ROYAL_CRYPT', 'WATER_ROPE', [[KEYS(3), CLONES(3)]], 'Ropes')
d('CRYPT', 'ROYAL_CRYPT', '5', [[KEYS(3), CLONES(3), LANTERN]],
  '"light all the torches with the Flame Lantern to make a couple of Gibdo '
  'appear" - the torches then shoot fireballs. Room number is a guess')
d('CRYPT', 'ROYAL_CRYPT', '0', [[KEYS(3), CLONES(3), LANTERN]],
  'the Triforce stone; Gustaf gives KINSTONE_SOURCE_FLOW, the gold piece that '
  'opens Veil Falls. Room number is a guess')


# ========================================================= PALACE OF WINDS
#
# The sky dungeon, one whirlwind above this mode's hub roof. Roc's Cape is
# its item and is needed within a few rooms of finding it; CLONES(3) is
# everywhere - six puzzles on the main route and the boss itself. Six small
# keys, the most of any dungeon.
area('POW', 'Palace of Winds', ('PALACE_OF_WINDS', 'ENTRANCE_ROOM', 0, 0),
     note='from the Wind Tribe tower roof - the hub. Roc\'s Cape early and then '
          'everywhere; CLONES(3) on the main route six times and on the boss; '
          'the Bow, the Cane, bombs and the lantern all called for')
d('POW', 'PALACE_OF_WINDS', 'ENTRANCE_ROOM', FREE,
  'switch-raised bridges, Peahats; "throw the Boomerang at an angle to hit the '
  'switch" - Boomerang or Bow for the ranged switches')
d('POW', 'PALACE_OF_WINDS', 'BRIDGE_SWITCHES_CLONE_BLOCK', [[CLONES(3)]],
  'skulls hide glowing tiles; "split into three. Cross the bridge and push aside '
  'the large block" (Bracelets for the block here)')
d('POW', 'PALACE_OF_WINDS', 'PLATFORM_RIDE_BOMBAROSSAS', [[CLONES(3)]], 'the moving platform, blocks and Bombarossas')
d('POW', 'PALACE_OF_WINDS', 'FIRE_BAR_GRATES', [[CLONES(3)]], 'grated floor, Winders, Bob-ombs')
d('POW', 'PALACE_OF_WINDS', 'ROC_CAPE', [[CLONES(3), BOMBS], [CLONES(3), BOW], [CLONES(3), BOOMERANG]],
  'a far switch, then "Hit the switch, then place a bomb by it and cross the '
  'bridge before it goes off"; twelve Wizzrobes in three waves -> ROC\'S CAPE')
d('POW', 'PALACE_OF_WINDS', 'GRATES_TO_3F', [[CLONES(3), CAPE]],
  '"jump in place there to get below the grating" - the cape opens the grate '
  'panels and the cloud stacks between floors')
d('POW', 'PALACE_OF_WINDS', 'SPINY_FIGHT', [[CLONES(3), CAPE, PACCI]],
  '2F: a block puzzle, clones slashing four switches at once, Spiked Beetles '
  'flipped with the cane')
d('POW', 'PALACE_OF_WINDS', 'TO_FAN_BRIDGE', [[CLONES(3), CAPE, PACCI]],
  'fans, a hole to hide in, "fill the hole with the Cane\'s magic, then use it to '
  'jump to the ledge above"')
d('POW', 'PALACE_OF_WINDS', 'GRATE_PLATFORM_RIDE', [[CLONES(3), CAPE, PACCI]], 'panels and platforms')
d('POW', 'PALACE_OF_WINDS', 'PLATFORM_CLONE_RIDE', [[CLONES(3), CAPE, PACCI]],
  '3F: "split yourself into three, wait for the platform to come, and get on it"')
d('POW', 'PALACE_OF_WINDS', 'POT_PUSH', [[CLONES(3), CAPE, PACCI, MINISH]],
  'three clones slash three switches -> a pedestal (stump (392,72)); the Minish '
  'pot maze, nine pots in order')
d('POW', 'PALACE_OF_WINDS', 'KEY_ARROW_BUTTON', [[CLONES(3), CAPE, PACCI, MINISH, BOW], [CLONES(3), CAPE, PACCI, MINISH, BOOMERANG]],
  'back to size, "hit the switch from afar to make the door open up and a SMALL '
  'KEY to drop" - key 1')
d('POW', 'PALACE_OF_WINDS', 'PIT_CORNER_AFTER_KEY', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(1)]], 'the rolling log and the locked door')
d('POW', 'PALACE_OF_WINDS', 'CLOUD_JUMPS', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(1)]], 'up the cloud stack')
d('POW', 'PALACE_OF_WINDS', 'FAN_BRIDGE', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(1)]],
  '4F: the fan bridge ("memorize it"), a block mess, a fan-assisted jump')
d('POW', 'PALACE_OF_WINDS', 'CRACKED_FLOOR_LAKITU', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(1)]],
  'platforms past Lakitus, Bow Moblins, a kinstone chest, the last stack to the top')
d('POW', 'PALACE_OF_WINDS', 'BALL_AND_CHAIN_SOLDIERS', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(1)]],
  'top floor: two Ball and Chain Soldiers -> SMALL KEY 2')
d('POW', 'PALACE_OF_WINDS', 'BEFORE_BALL_AND_CHAIN_SOLDIERS', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(1)]])
d('POW', 'PALACE_OF_WINDS', 'FOUR_BUTTON_STALFOS', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(2)]],
  '"leave at least one [pot] ... push it onto one of the switches. Now split into '
  'three adjacent to the remaining switches"')
d('POW', 'PALACE_OF_WINDS', 'MOBLIN_AND_WIZZROBE_FIGHT', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(2)]],
  'a fan switch, a fan jump south, Moblins and Ice Wizzrobes (one lantern hit '
  'each, if you have it)')
d('POW', 'PALACE_OF_WINDS', 'FAN_AND_KEY_TO_BOSS_KEY', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(2), BOW]],
  '"attack the Stalfos with your Bow, jump across"; a fan switch, a fan jump, a '
  'chest: SMALL KEY 3')
d('POW', 'PALACE_OF_WINDS', 'BOSS_KEY', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(3), BOW]],
  'blocks, the locked door, "open the large chest for the Big Key"')
d('POW', 'PALACE_OF_WINDS', 'HOLE_TO_DARKNUT', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(3), BOW, BIG_KEY]],
  'the giant door south; "jump down where the tiles point to" - back to 1F')
d('POW', 'PALACE_OF_WINDS', 'DARKNUT_MINIBOSS', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(3), BOW, BIG_KEY]],
  'a Red Darknut; blue portal; a bridge forms')
d('POW', 'PALACE_OF_WINDS', 'BRIDGE_AFTER_DARKNUT', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(3), BOW, BIG_KEY]])
d('POW', 'PALACE_OF_WINDS', 'DARK_COMPASS_HALL', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(3), BOW, BIG_KEY, LANTERN]],
  '"Take out your Flame Lantern, as it\'s dark in here"; the COMPASS on a ledge')
d('POW', 'PALACE_OF_WINDS', 'CORNER_TO_MAP', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(3), BOW, BIG_KEY, LANTERN]],
  'upstairs; north then east: "drop down the center hole. Open the chest for a '
  'SMALL KEY" - key 4. Stump (184,120)')
d('POW', 'PALACE_OF_WINDS', 'PEAHAT_SWITCH', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(3), BOW, BIG_KEY, LANTERN]],
  'the south doorway: Peahats, clones to four switches')
d('POW', 'PALACE_OF_WINDS', 'TO_PEAHAT_SWITCH', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(3), BOW, BIG_KEY, LANTERN]])
d('POW', 'PALACE_OF_WINDS', 'SPIKE_BAR_SMALL_KEY', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(4), BOW, BIG_KEY, LANTERN]],
  '"Jump over the rolling logs, climb up and open the chest for a SMALL KEY" - key 5')
d('POW', 'PALACE_OF_WINDS', 'WHIRLWIND_BOMBAROSSA', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(5), BOW, BIG_KEY, LANTERN]],
  'the locked door, whirlwinds to the north-east ledge between Bombarossas')
d('POW', 'PALACE_OF_WINDS', 'SHORTCUT_DOOR_BUTTONS', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(5), BOW, BIG_KEY, LANTERN, SPIN]],
  '"use a spin attack to hit both switches, opening the door here that will act '
  'as a shortcut"')
d('POW', 'PALACE_OF_WINDS', 'KINSTONE_WIZZROBE_FIGHT', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(5), BOW, BIG_KEY, LANTERN]],
  'Wizzrobes -> a kinstone chest')
d('POW', 'PALACE_OF_WINDS', 'MAP', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(5), BOW, BIG_KEY, LANTERN]],
  '"fight off all the Fire Wizzrobes and a large chest will appear ... the '
  'Dungeon Map"')
d('POW', 'PALACE_OF_WINDS', 'FLOORMASTER_LEVER', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(5), BOW, BIG_KEY, LANTERN]],
  'Floor Masters from a distance, a lever')
d('POW', 'PALACE_OF_WINDS', 'STALFOS_FIREBAR_HOLE', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(5), BOW, BIG_KEY, LANTERN]],
  'shoot a Bombarossa by the cracked blocks; Gibdos and Stalfos; light the '
  'torches -> red portal')
d('POW', 'PALACE_OF_WINDS', 'HEART_PIECE_BRIDGE', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(5), BOW, BIG_KEY, LANTERN]],
  '"push the blocks off, jump across the gap, and enter the door. Follow the path '
  'to get a Piece of Heart!" - #33')
d('POW', 'PALACE_OF_WINDS', 'GIBDO_STAIRS', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(5), BOW, BIG_KEY, LANTERN, BOMBS]],
  'a boomerang switch -> 200 rupees; the locked door; "kill the Gibdos and bomb '
  'the cracked wall"')
d('POW', 'PALACE_OF_WINDS', 'BOMB_WALL_INSIDE', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(5), BOW, BIG_KEY, LANTERN, BOMBS]],
  'Stalfos and Fire Wizzrobes; "bomb the north side of the west wall until you '
  'uncover a hole"')
d('POW', 'PALACE_OF_WINDS', 'BOMB_WALL_OUTSIDE', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(5), BOW, BIG_KEY, LANTERN, BOMBS]])
d('POW', 'PALACE_OF_WINDS', 'TO_BOMBAROSSA_PATH', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(5), BOW, BIG_KEY, LANTERN, BOMBS]])
d('POW', 'PALACE_OF_WINDS', 'BOMBAROSSA_PATH', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(5), BOW, BIG_KEY, LANTERN, BOMBS]],
  'thread the Bombarossas without setting one off; blocks; a chest: SMALL KEY 6')
d('POW', 'PALACE_OF_WINDS', 'BLOCK_MAZE_TO_BOSS_DOOR', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(6), BOW, BIG_KEY, LANTERN, BOMBS]],
  'cracked floors drop you to the locked door; spikes to jump, a kinstone chest, '
  'the one-path maze, the cloud stacks')
d('POW', 'PALACE_OF_WINDS', 'GYORG_BOSS_DOOR', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(6), BOW, BIG_KEY, LANTERN, BOMBS]])
d('POW', 'PALACE_OF_WINDS', 'GYORG_TORNADO', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(6), BOW, BIG_KEY, LANTERN, BOMBS]])
d('POW', 'PALACE_OF_WINDS_BOSS', '0', [[CLONES(3), CAPE, PACCI, MINISH, KEYS(6), BOW, BIG_KEY, LANTERN, BOMBS]],
  'Gyorg Pair, fought on their backs: jump (CAPE) between them, split (CLONES(3)) '
  'to hit the open eyes together. WIND ELEMENT')


# ------------------------------------------------------------------ checks --
def _fmt(req):
    if req is None:
        return 'NOT REACHABLE'
    if not req or req == [[]]:
        return '-'
    return ' / '.join(' + '.join(t) for t in req)


def roomid_names():
    """Every ROOM_* and AREA_* name in include/roomid.h, from the source the
    build compiles."""
    txt = open(os.path.join(ROOT, 'include', 'roomid.h')).read()
    rooms = set(re.findall(r'\b(ROOM_\w+)', txt))
    areas = set(re.findall(r'// (AREA_\w+)', txt))
    return rooms, areas


def room_rects(area_name):
    """Room rectangles of one area from data/map/room_headers.s, in pixels:
    (index, x, y, w, h). x,y are stored in 16-px map units."""
    txt = open(os.path.join(ROOT, 'data', 'map', 'room_headers.s')).read()
    m = re.search(r'gAreaRoomHeaders_%s:: @ \w+\n((?:\troom_header .*\n)+)' % area_name, txt)
    if not m:
        return []
    out = []
    for i, row in enumerate(re.findall(r'room_header (\S+), (\S+), (\S+), (\S+), (\d+)', m.group(1))):
        x, y, w, h = (int(v, 0) for v in row[:4])
        out.append((i, x * 16, y * 16, w, h))
    return out


def adjacency(area_name):
    """Pairs of rooms in one area whose rectangles share an edge. Dungeon rooms
    adjoin by door TILES rather than transition rows, so this is the only
    static view of which rooms can be neighbours. Sharing an edge does not
    prove a door; not sharing one proves there is none."""
    rects = [r for r in room_rects(area_name) if r[3] and r[4]]
    pairs = []
    for i, (a, ax, ay, aw, ah) in enumerate(rects):
        for b, bx, by, bw, bh in rects[i + 1:]:
            horiz = (ax + aw == bx or bx + bw == ax) and (ay < by + bh and by < ay + ah)
            vert = (ay + ah == by or by + bh == ay) and (ax < bx + bw and bx < ax + aw)
            if horiz or vert:
                pairs.append((a, b))
    return pairs


def room_enum(area_name):
    """ROOM_* names of one area, in enum order, from include/roomid.h."""
    txt = open(os.path.join(ROOT, 'include', 'roomid.h')).read()
    m = re.search(r'// AREA_%s\n((?:    ROOM_\w+(?: = \d+)?,\n)+)' % area_name, txt)
    return re.findall(r'(ROOM_\w+)', m.group(1)) if m else []


def check():
    rooms, areas = roomid_names()
    problems = 0
    for key, r in GUIDE.items():
        for e in [dict(area=r['start'][0], room=r['start'][1])] + r['dests']:
            an = 'AREA_' + e['area']
            rn = 'ROOM_%s_%s' % (e['area'], e['room'])
            if an not in areas:
                print('PROBLEM %s: %s is not an area roomid.h knows' % (key, an))
                problems += 1
            elif rn not in rooms:
                print('PROBLEM %s: %s is not a room roomid.h knows' % (key, rn))
                problems += 1
    for key, r in GUIDE.items():
        for e in r['dests']:
            for term in (e['req'] or []):
                for tok in term:
                    if tok in UNPAYABLE:
                        pass
    print('%d areas, %d rows, %d naming problems' %
          (len(GUIDE), sum(len(r['dests']) for r in GUIDE.values()), problems))
    return 1 if problems else 0


def summary():
    """Per area: how many rows a QUICKSTART run could ever pay, given that
    CLONES(n) has no price here."""
    print('%-28s %5s %9s %9s  %s' % ('area', 'rows', 'payable', 'clones', 'clone puzzles are the gate on'))
    for key, r in GUIDE.items():
        rows = r['dests']
        cloned = [e for e in rows if e['req'] and all(any(t in UNPAYABLE for t in term) for term in e['req'])]
        print('%-28s %5d %9d %9d  %s' % (key, len(rows), len(rows) - len(cloned), len(cloned),
                                          '%d%% of the area' % (100 * len(cloned) // max(1, len(rows)))))


def dump():
    for key, r in GUIDE.items():
        a, room = r['start'][:2]
        print('\n=== %-34s start %s/%s%s' % (r['name'], a, room,
              ('   ROOM REQ ' + _fmt(r['room_req'])) if r['room_req'] else ''))
        if r['note']:
            print('    (%s)' % r['note'])
        for e in r['dests']:
            print('    %-46s %s' % ('%s/%s' % (e['area'], e['room']), _fmt(e['req'])))
            if e['note']:
                print('        %s' % e['note'])


if __name__ == '__main__':
    if '--check' in sys.argv:
        sys.exit(check())
    if '--summary' in sys.argv:
        summary()
    elif '--adjacency' in sys.argv:
        an = sys.argv[sys.argv.index('--adjacency') + 1]
        names = room_enum(an)
        for a, b in adjacency(''.join(w.capitalize() for w in an.split('_'))):
            print('%-48s <-> %s' % (names[a] if a < len(names) else a, names[b] if b < len(names) else b))
    else:
        dump()
