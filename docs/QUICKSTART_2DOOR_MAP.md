# The 2-door "? room" pool: door map and rewiring plan

## The bug

A vanilla overworld region has two doors, A and B, that connect through
some interior. Walk in at A, cross the interior, come out at B. Walk in at
B, come out at A. The 2-door pool is supposed to substitute a random room
with its own two doors, A' and B', preserving that: A leads to A', B leads
to B', and leaving by either returns you to the matching overworld side.

What happens instead:

- Entering at A teleports the player into the MIDDLE of the pool room, not
  to A'.
- Leaving by either A' or B' returns them to overworld door B.
- Travelling B -> A is therefore impossible.

## Why - measured, not guessed

Every one of the 40 doors in the pool (20 rooms, 2 each) has been
retargeted in `transitions.c` to the *same destination and the same landing
spot*: `AREA_HYRULE_FIELD / ROOM_HYRULE_FIELD_LON_LON_RANCH` at
`(184, 312)`. The survey below is the proof - the right-hand column is
identical on all 40 rows.

On top of that, `QuickStartFixupCaveConnectorReturn` overrides
`start_pos_x/y` to a single hard-coded `(232, 476)` whenever the player
leaves a pool room, and the entry side (`QuickStartProcessCaveConnectorLink`)
warps them to a per-room `entranceX/entranceY` that is the unmeasured
constant `(100,100)` for 18 of the 20 rooms.

So the destination carries no information about which door was used, in
either direction. This is an artifact of the older design where the player
was warped into every room rather than walking through real doors, exactly
as suspected.

## What the fix needs

Both ends have to become side-aware.

**Room side.** Each pool room's own exit list already carries what is
needed, and it can be read at runtime from the loaded room rather than
duplicated into a table: for a `WARP_TYPE_AREA` door, `startX/startY` is
the door's position inside the room; the landing spot for arriving through
that door is open ground next to it (`QuickStartFindOpenTileNear` already
does that snap). Index 0 becomes side A', index 1 side B'.

**Overworld side.** The connector needs to record which of its two
overworld doors the player entered by, and the room's exit needs to consult
that plus which door they left by:

    entered A, left A'  ->  overworld A
    entered A, left B'  ->  overworld B
    entered B, left B'  ->  overworld B
    entered B, left A'  ->  overworld A

i.e. the destination depends only on WHICH DOOR THEY LEFT BY, not on how
they came in - which is what makes it seamless in both directions and is
simpler than tracking entry at all.

**Identifying which door they left by** is the one part that is not
uniform. Doors come in two shapes:

- `WARP_TYPE_AREA` - has a real position, so comparing the player's
  position against `startX/startY` identifies it.
- `WARP_TYPE_BORDER` - `startX/startY` are both 0 and the room edge is
  encoded in the `shape` field instead. Comparing positions cannot
  distinguish these; the edge has to be derived from `shape` and matched
  against which edge the player walked off.

Four rooms have BOTH doors as borders and so need the shape-based path:
Crenel Caves / Ladder To Spring Water, Crenel Minish Paths / Melari,
Crenel Minish Paths / Rain, and Minish Paths / Minish Village.

## Status

Implemented. Doors are tagged in the data and the engine's own matching
identifies them, so both shapes work through one path.

**How to add a room to the pool later.** Two steps, no code:
1. Add the room to `sQuickStart2DoorSmallRoomPool` / `LargeRoomPool`.
2. In `transitions.c`, give its first door row `endX`/`endY` of
   `0x3fe` and its second `0x3fd` (`QUICKSTART_2DOOR_TAG_A`/`_B`).

Everything else derives itself: `QuickStart2DoorExitSide` reads the tag the
fired transition planted in `player_status.start_pos_x`, and
`QuickStart2DoorDoorSpot` reads the room's own live exit list to find where
to stand the player on arrival - `startX/startY` for an AREA door, the edge
named by `shape` for a BORDER one - then snaps that onto open ground.

**Adding a new overworld connector** needs its two side positions and two
return spots, the same shape the river bridge already has
(`QUICKSTART_RIVER_SIDE_A_*` / `_B_*`), plus a call to
`QuickStart2DoorExitSide()` in its return fixup.

Verified in Dark Hyrule Castle's bridge room, which has one door of each
shape: leaving by the AREA door lands at North Hyrule Field (320,238),
leaving by the BORDER door lands at (120,278) - different sides, from the
same room, which is what was impossible before.

## The survey

All 20 pool rooms, read out of `transitions.c` (QUICKSTART branch).
`at (x,y)` is the door's trigger position inside the room; the landing is
where that door currently sends the player.

```
== AREA_CASTOR_CAVES / ROOM_CASTOR_CAVES_DARKNUT
   gExitList_CastorCaves_Darknut [QUICKSTART]
     door 0: WARP_TYPE_AREA   at ( 104,  24) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_CRENEL_CAVES / ROOM_CRENEL_CAVES_BRIDGE_SWITCH
   gExitList_CrenelCaves_BridgeSwitch [QUICKSTART]
     door 0: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_AREA   at (  56,  40) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_CRENEL_CAVES / ROOM_CRENEL_CAVES_CHUCHU_POT_CHEST
   gExitList_CrenelCaves_ChuchuPotChest [QUICKSTART]
     door 0: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_AREA   at (  56,  40) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_CRENEL_CAVES / ROOM_CRENEL_CAVES_HELMASAUR_HALLWAY
   gExitList_CrenelCaves_HelmasaurHallway [QUICKSTART]
     door 0: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_AREA   at ( 104,  24) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_CRENEL_CAVES / ROOM_CRENEL_CAVES_LADDER_TO_SPRING_WATER
   gExitList_CrenelCaves_LadderToSpringWater [QUICKSTART]
     door 0: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_VEIL_FALLS_CAVES / ROOM_VEIL_FALLS_CAVES_EXIT
   gExitList_VeilFallsCaves_Exit [QUICKSTART]
     door 0: WARP_TYPE_AREA   at (  88,  24) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_VEIL_FALLS_CAVES / ROOM_VEIL_FALLS_CAVES_HALLWAY_SECRET_STAIRCASE
   gExitList_VeilFallsCaves_SecretStaircases [QUICKSTART]
     door 0: WARP_TYPE_AREA   at (  88,  56) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_AREA   at ( 152,  56) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_CRENEL_MINISH_PATHS / ROOM_CRENEL_MINISH_PATHS_MELARI
   gExitList_CrenelMinishPaths_MelarisMine [QUICKSTART]
     door 0: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_CRENEL_MINISH_PATHS / ROOM_CRENEL_MINISH_PATHS_RAIN
   gExitList_CrenelMinishPaths_Rainfall [QUICKSTART]
     door 0: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_MINISH_PATHS / ROOM_MINISH_PATHS_MINISH_VILLAGE
   gExitList_MinishPaths_ToMinishVillage [QUICKSTART]
     door 0: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_VEIL_FALLS_CAVES / ROOM_VEIL_FALLS_CAVES_HALLWAY_RUPEE_PATH
   gExitList_VeilFallsCaves_RupeePath [QUICKSTART]
     door 0: WARP_TYPE_AREA   at ( 152,  24) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_HOUSE_INTERIORS_1 / ROOM_HOUSE_INTERIORS_1_INN_EAST_2F
   gExitList_HouseInteriors1_InnEast2F [QUICKSTART]
     door 0: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_AREA   at ( 184, 376) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_HOUSE_INTERIORS_1 / ROOM_HOUSE_INTERIORS_1_LIBRARY_1F
   gExitList_HouseInteriors1_Library1F [QUICKSTART]
     door 0: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_AREA   at ( 104,  24) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_HOUSE_INTERIORS_1 / ROOM_HOUSE_INTERIORS_1_LIBRARY_2F
   gExitList_HouseInteriors1_Library2F [QUICKSTART]
     door 0: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_AREA   at ( 120,  24) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_HOUSE_INTERIORS_1 / ROOM_HOUSE_INTERIORS_1_SCHOOL_WEST
   gExitList_HouseInteriors1_SchoolWest [QUICKSTART]
     door 0: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_AREA   at ( 120,  72) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_MINISH_HOUSE_INTERIORS / ROOM_MINISH_HOUSE_INTERIORS_FESTARI
   gExitList_MinishHouseInteriors_Festari [QUICKSTART]
     door 0: WARP_TYPE_AREA   at ( 232, 232) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_AREA   at ( 232,  24) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_DARK_HYRULE_CASTLE / ROOM_DARK_HYRULE_CASTLE_3F_TRIPLE_DARKNUT
   gExitList_DarkHyruleCastle_3FTripleDarknut [QUICKSTART]
     door 0: WARP_TYPE_AREA   at ( 168,  40) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_DARK_HYRULE_CASTLE_BRIDGE / ROOM_DARK_HYRULE_CASTLE_BRIDGE_MAIN
   gExitList_DarkHyruleCastleBridge_Main [QUICKSTART]
     door 0: WARP_TYPE_AREA   at ( 136,  24) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_SANCTUARY_ENTRANCE / ROOM_SANCTUARY_ENTRANCE_MAIN
   gExitList_SanctuaryEntrance_Main [QUICKSTART]
     door 0: WARP_TYPE_AREA   at ( 136,  56) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)

== AREA_NULL_61 / ROOM_NULL_61_0
   gExitList_61_0 [QUICKSTART]
     door 0: WARP_TYPE_AREA   at ( 120,  88) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
     door 1: WARP_TYPE_BORDER at (   0,   0) -> AREA_HYRULE_FIELD/ROOM_HYRULE_FIELD_LON_LON_RANCH landing ( 184, 312)
```
