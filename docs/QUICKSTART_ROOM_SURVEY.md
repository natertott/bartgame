# QUICKSTART ? room survey

Measured in the emulator (collision + act tiles + live entities read out of
RAM per room), not inferred from source. One record per room used by any of
the three ? room systems, the shop, and the Minish rooms.

## How to read a room entry

- **Grid legend**: `.` open floor reachable from the surveyed entrance, `o`
  open floor NOT reached from that entrance (another component - reached by
  a different door, a staircase, or not at all), `+` a partial tile (some
  quadrants solid - shelf fronts, doorway lips; standable against, not
  placeable ON), `#` solid.
- **Components** are 4-connected regions of fully-open tiles. IMPORTANT
  CAVEAT: stairs/ladders/ramps carry special collision values (0x61, 0x63,
  0xf1...) that this model treats as walls, so two components joined by a
  staircase appear separate here. Rooms where that is known to matter are
  flagged in their notes.
- **Reco spot** is the measured recommendation for centred content: the
  reachable tile nearest the entrance component's centre of mass, preferring
  tiles with all four neighbours open. This is what "centered, when centre
  makes sense" resolves to numerically; the placement code can already snap
  to it (`QuickStartFindOpenTileNear`).
- **Free slots** is 72 (`MAX_ENTITIES`, the whole game's budget) minus the
  entities live on entry. This is the real "how much can we spawn here"
  budget - see the budget section below for why this, not VRAM, is usually
  the binding constraint.

## Event dynamics (all rooms, from the code)

The seven kinds all run through `QuickStartSetupEventContent`, called every
frame the player is in the room. Common shape:

- **Spawn-once latch**: room flag `base+0` marks "content spawned this
  visit". Room flags reset on every room load, so leaving and re-entering
  re-runs the spawn - EXCEPT that the persistent `GF_CONTENT_SITE_DONE` (a
  save-flag) latches "reward collected", and once set the room spawns
  nothing ever again this run.
- **Chest / lottery / pot / miniboss / waves reward**: the payout is a
  GROUND_ITEM. `QuickStartGroundItemAt/OfForm` refreshes its despawn timer
  every frame and distinguishes "picked up" (item gone while room stayed
  loaded -> set DONE) from "room unloaded before pickup" (respawn next
  visit).
- **Miniboss**: spawns 1 enemy (3-6 for Wizzrobes) via the ground-aware
  placer; alive-test is ENT_PERSIST-based so a vanishing Wizzrobe still
  counts; reward drops at the content spot when all are dead.
- **Waves**: 3 waves, one enemy TYPE per wave (bounded gfx load by
  construction), count scales with difficulty, capped at 12 per wave;
  reward after wave 3. Wave index lives in room flags -> leaving mid-fight
  resets to wave 0 (documented behaviour, not a bug - the DONE latch only
  sets on pickup).
- **Pot room**: layout derives from the site's stored extra byte + room
  identity (not live RNG), so re-entry rebuilds the identical layout;
  target capped by open floor, `MAX_POTS` 44, trap cap 12, and (new) real
  entity headroom so the prize always exists. In shared rooms the fill is
  clipped to the owning site's nearest-site region.
- **NPC**: one Zelda NPC, friendly or 100-rupee script by extra bit. Reads
  as "vanilla flavour" to players - the known perception issue from the
  SHF feedback round; kind weight already reduced via KINDS_ANY.
- **Fairy**: pure reward, no win condition, no DONE latch on touch.

## Door mechanics (all rooms, from the code + this survey)

- **Content-site rooms**: entered by their own real vanilla door
  (WARP_TYPE_AREA or BORDER row in transitions.c); the return leg is the
  same row's vanilla partner. Transitions are the engine's own - seamless.
- **2-door pool rooms**: both door rows are tagged (`QUICKSTART_2DOOR_TAG_A/_B`
  in endX/endY); the engine's own matching identifies which door fired, exit
  side keys the overworld return, and arrival is placed at the matching
  door's own spot then snapped to ground. See QUICKSTART_2DOOR_MAP.md.
- **Ladder-pool room (Castle Garden NW)**: the ladder's destination is
  rewritten per run by `QuickStartProcessDoorRedirects`. Anything else that
  targets the same vanilla destination is rewritten too - this is why the
  Hyrule Castle Cellar content site is SHADOWED (see its entry).

## The budget: entities first, VRAM second

`MAX_ENTITIES` is 72 for the whole game - player, items, FX, projectiles
included. That is the binding constraint in practice, and it is measured
per room below. On VRAM/gfx-slots: no direct measurement exists in this
harness. What is known empirically:

- Pots share one graphic: 40+ pots is fine anywhere (measured repeatedly).
- One enemy TYPE at a time (the wave rule) bounds gfx pressure by design.
- The one confirmed VRAM-class failure is POT_MINISH hosting MULTI-enemy
  content (entities exist in RAM, sprites never render). Its distinctive
  tile reskin plausibly eats the budget. Rule of thumb until measured
  properly: rooms with heavy background animation/reskins should not host
  multi-enemy kinds; everything in the current pools except POT_MINISH
  (already excluded) has hosted its kinds without a rendering failure.

## What gets turned off, what stays

On entry every ? room is swept once per visit
(`QuickStartClearVanillaRoomContent`): ENEMY-kind and NPC-kind entities and
payout-shaped objects (ground items, both chest kinds, heart containers,
fairies) are deleted. Props (pots, furniture, acorns, signs) stay unless
the room is on the `clearObjects` list (arena rooms). Tile-level state -
bombable walls, smashed tiles, opened chests' local flags, revealed portals
- is per-area LOCAL flags, and since the world-reset change every run wipes
those: walls re-seal, portals re-hide (and stay hidden until their vanilla
uncover step - grass cut for hidden ladders, boots dash for stumps), chests
re-arm. Kinstone
gates will behave the same way when re-enabled.

---

## Room-by-room

### AREA_CAVES / ROOM_CAVES_NORTH_HYRULE_FIELD_FAIRY_FOUNTAIN  `[site]`

- size 240x160, open 64 tiles (reachable from entrance: 64, partial: 2), free entity slots on entry: **69**
- components (sizes): [64]
- reco content spot: (120,72)
- table content spots: (120,96)
- on entry: OBJ:SPECIAL_CHEST(t250)@(104,96), OBJ:SPECIAL_CHEST(t251)@(120,96), OBJ:SPECIAL_CHEST(t252)@(136,96)

```
###############
###############
##...........##
##...........##
##...........##
##...........##
###.........###
##...........##
#######+#######
#######+#######
```

### AREA_TREE_INTERIORS / ROOM_TREE_INTERIORS_SOUTH_HYRULE_FIELD_HEART_PIECE  `[site]`

- size 240x160, open 42 tiles (reachable from entrance: 42, partial: 10), free entity slots on entry: **70**
- components (sizes): [42]
- reco content spot: (120,72)
- table content spots: (120,96)
- on entry: OBJ:ARCHWAY(t6)@(120,152), OBJ:GROUND_ITEM(t101)@(120,96)

```
###############
###############
####+.....+####
###+.......+###
###.........###
###.........###
###+.......+###
####+.....+####
#######+#######
#######+#######
```

### AREA_CAVES / ROOM_CAVES_SOUTH_HYRULE_FIELD_FAIRY_FOUNTAIN  `[site]`

- size 240x160, open 70 tiles (reachable from entrance: 46, partial: 16), free entity slots on entry: **71**
- components (sizes): [46, 12, 12]
- reco content spot: (120,72)
- table content spots: (120,96)
- on entry: OBJ:GROUND_ITEM(t101)@(120,96)

```
oo+#########+oo
o+###########+o
o##.........##o
o##+.......+##o
o##.........##o
o##.+.....+.##o
o##+#.....#+##o
o##.........##o
o+#####+#####+o
oo+####+####+oo
```

### AREA_CAVES / ROOM_CAVES_SOUTH_HYRULE_FIELD_RUPEE  `[site]`

- size 240x160, open 62 tiles (reachable from entrance: 62, partial: 6), free entity slots on entry: **71**
- components (sizes): [62]
- reco content spot: (120,72)
- table content spots: (120,96)
- on entry: OBJ:GROUND_ITEM(t101)@(120,96)

```
###############
###############
##...........##
##+.........+##
##...........##
##...........##
##+.........+##
##...........##
#######+#######
#######+#######
```

### AREA_CAVES / ROOM_CAVES_BOOMERANG  `[site]`

- size 336x336, open 177 tiles (reachable from entrance: 40, partial: 33), free entity slots on entry: **28**
- components (sizes): [41, 40, 40, 39, 4, 4, 4, 3, 1, 1]
- reco content spot: (72,88)
- table content spots: (72,78), (266,58), (72,285), (263,206), (170,158)
- special tiles: stair63 at [[168, 184], [72, 216], [264, 216]]
- on entry: OBJ:LADDER_UP(t1)@(72,124), OBJ:LADDER_UP(t1)@(264,124), OBJ:LADDER_UP(t1)@(72,236), OBJ:LADDER_UP(t1)@(264,236), OBJ:BUTTON(t0)@(104,57), OBJ:BUTTON(t0)@(232,57), OBJ:BUTTON(t0)@(104,281), OBJ:BUTTON(t0)@(232,281), OBJ:SPECIAL_CHEST(t250)@(56,78), OBJ:SPECIAL_CHEST(t251)@(72,78), OBJ:SPECIAL_CHEST(t252)@(88,78), NPC:PARALLAX_ROOM_VIEW(t0)@(266,58), OBJ:SPECIAL_CHEST(t250)@(247,206), OBJ:SPECIAL_CHEST(t251)@(263,206) (+30 more)

```
##########o##########
##########o##########
###...#.##o##o#ooo###
##......##o##oooooo##
##......#####oooooo##
##......#####oooooo##
##.....#######ooooo##
##..+..#++#++#oo+oo##
##.....#+++o+#+oooo##
##....+#++oo+#ooooo##
########o++o+########
##oooo+#++o+o#ooooo##
##oooo+#++++o#ooooo##
##ooooo#++++o#ooooo##
##oo+oo#######oo+oo##
##oooooo#####oooooo##
##oooo#o#####o#oooo##
###ooooo##o##ooooo###
##oooooo##o##oooooo##
##########o##########
##########o##########
```

### AREA_TREE_INTERIORS / ROOM_TREE_INTERIORS_PERCYS_TREEHOUSE  `[site]`

- size 240x160, open 27 tiles (reachable from entrance: 27, partial: 14), free entity slots on entry: **67**
- components (sizes): [27]
- reco content spot: (120,104)
- table content spots: (120,96)
- on entry: OBJ:FURNITURE(t0)@(120,40), OBJ:ARCHWAY(t6)@(120,152), OBJ:SPECIAL_CHEST(t250)@(104,96), OBJ:SPECIAL_CHEST(t251)@(120,96), OBJ:SPECIAL_CHEST(t252)@(136,96)

```
###############
###############
####+#####+####
###+.+###+.+###
###..+###+..###
###.........###
###+.......+###
####+.....+####
#######+#######
#######+#######
```

### AREA_CAVES / ROOM_CAVES_TRILBY_KEESE_CHEST  `[site]`

- size 240x160, open 75 tiles (reachable from entrance: 57, partial: 22), free entity slots on entry: **69**
- components (sizes): [57, 6, 6, 3, 3]
- reco content spot: (104,88)
- table content spots: (120,96)
- on entry: OBJ:SPECIAL_CHEST(t250)@(104,96), OBJ:SPECIAL_CHEST(t251)@(120,96), OBJ:SPECIAL_CHEST(t252)@(136,96)

```
ooo+#######+ooo
oo+#########+oo
o+#+.......+#+o
+#+.........+#+
##.....#.....##
##...........##
##...........##
+#+.........+#+
o+#####+#####+o
oo+####+####+oo
```

### AREA_CAVES / ROOM_CAVES_TRILBY_RUPEE  `[site]`

- size 240x160, open 62 tiles (reachable from entrance: 62, partial: 6), free entity slots on entry: **69**
- components (sizes): [62]
- reco content spot: (120,72)
- table content spots: (120,96)
- on entry: OBJ:SPECIAL_CHEST(t250)@(104,96), OBJ:SPECIAL_CHEST(t251)@(120,96), OBJ:SPECIAL_CHEST(t252)@(136,96)

```
###############
###############
##.+.......+.##
##...........##
##...........##
##...........##
##...........##
##.+......+..##
#######+#######
#######+#######
```

### AREA_CAVES / ROOM_CAVES_TRILBY_FAIRY_FOUNTAIN  `[site]`

- size 240x160, open 41 tiles (reachable from entrance: 41, partial: 27), free entity slots on entry: **69**
- components (sizes): [41]
- reco content spot: (120,104)
- table content spots: (120,96)
- on entry: OBJ:SPECIAL_CHEST(t250)@(104,96), OBJ:SPECIAL_CHEST(t251)@(120,96), OBJ:SPECIAL_CHEST(t252)@(136,96)

```
#######+#######
#######+#######
##..+++++++..##
##..+++++++..##
##..+++++++..##
##.+.......+.##
##.#.......#.##
##...........##
#######+#######
#######+#######
```

### AREA_HYRULE_CASTLE_CELLAR / ROOM_HYRULE_CASTLE_CELLAR_0  `[site]`

**SHADOWED**: warping or walking to this room lands in area/room (37, 0) because the Castle Garden NW ladder redirect rewrites every transition that targets it. Its content-site row is dead while that redirect exists. Decision needed: exempt this destination from the redirect, or retire the site row (renumbering hazard: rows above it shift, and the flag layout with them).

### AREA_DOJOS / ROOM_DOJOS_GRIMBLADE  `[site]`

- size 240x192, open 86 tiles (reachable from entrance: 86, partial: 2), free entity slots on entry: **68**
- components (sizes): [86]
- reco content spot: (120,104)
- table content spots: (120,136)
- on entry: OBJ:SPECIAL_FX(t7)@(162,189), OBJ:SPECIAL_FX(t7)@(85,153), OBJ:FAIRY(t96)@(87,149), OBJ:FAIRY(t96)@(161,189)

```
###############
###############
###.........###
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
#######+#######
#######+#######
```

### AREA_GORON_CAVE / ROOM_GORON_CAVE_STAIRS  `[site]`

- size 240x160, open 80 tiles (reachable from entrance: 28, partial: 25), free entity slots on entry: **69**
- components (sizes): [28, 26, 26]
- reco content spot: (120,88)
- table content spots: (120,96)
- special tiles: door40 at [[120, 56]]
- on entry: OBJ:SPECIAL_CHEST(t250)@(104,96), OBJ:SPECIAL_CHEST(t251)@(120,96), OBJ:SPECIAL_CHEST(t252)@(136,96)

```
oooo+#####+oooo
ooo+#######+ooo
oo+#+.+++.+#+oo
oo###.+#+..##oo
oo##..+.+..##oo
oo##.......##oo
oo##......###oo
oo+#+.....+#+oo
ooo+###+###+ooo
oooo+##+##+oooo
```

### AREA_GORON_CAVE / ROOM_GORON_CAVE_MAIN  `[site]`

- size 240x720, open 326 tiles (reachable from entrance: 36, partial: 51), free entity slots on entry: **66**
- components (sizes): [68, 63, 63, 42, 36, 27, 12, 12, 3]
- reco content spot: (120,616)
- table content spots: (120,608)
- special tiles: door40 at [[120, 648]]
- on entry: OBJ:EZLO_CAP(t0)@(120,632), OBJ:CAMERA_TARGET(t0)@(-256,0), ENEMY:46(t0)@(120,616), ENEMY:46(t0)@(120,568), ENEMY:46(t0)@(40,536), ENEMY:46(t0)@(200,536)

```
ooo#########ooo
ooo#########ooo
ooo###+#+###ooo
ooo##ooooo##ooo
#####ooooo#####
######ooo######
##+++++o+++++##
##+++++o+++++##
##+++++o+++++##
##ooooooooooo##
###############
###############
###############
##ooooooooooo##
##ooooooooooo##
##ooooooooooo##
##ooooo#ooooo##
##ooooooooooo##
####ooooooo####
####ooooooo####
oo###########oo
oo###########oo
oo###########oo
oo##ooooooo##oo
oo##ooooooo##oo
oo##+ooooo+##oo
oo##ooooooo##oo
oo##ooooooo##oo
oo####ooo####oo
oo####ooo####oo
oooo##ooo##oooo
oooo#######oooo
oooo#######oooo
oooo#######oooo
oooo##...##oooo
oo####...####oo
oo####...####oo
oo##.......##oo
oo##.......##oo
oo##..+.+..##oo
oo##..+#+..##oo
oo##..+++..##oo
oo+#++ooo++#+oo
ooo+#######+ooo
oooo+#####+oooo
```

### AREA_HOUSE_INTERIORS_2 / ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_ENTRANCE  `[site]`

- size 240x160, open 46 tiles (reachable from entrance: 46, partial: 14), free entity slots on entry: **66**
- components (sizes): [46]
- reco content spot: (104,104)
- table content spots: (120,96)
- special tiles: door40 at [[88, 24]]
- on entry: OBJ:FURNITURE(t3)@(148,40), OBJ:FURNITURE(t6)@(168,40), OBJ:ARCHWAY(t0)@(120,152), OBJ:ARCHWAY(t1)@(232,88), OBJ:ARCHWAY(t1)@(88,8), OBJ:GROUND_ITEM(t101)@(120,96)

```
###############
###############
####....+######
##....++##+..##
##....++##+.+##
##..........+++
##..........+##
##...........##
#######+#######
#######+#######
```

### AREA_HOUSE_INTERIORS_2 / ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_SMITH  `[site]`

- size 240x160, open 43 tiles (reachable from entrance: 43, partial: 12), free entity slots on entry: **71**
- components (sizes): [43]
- reco content spot: (120,88)
- table content spots: (120,104)
- special tiles: bombwall at [[88, 136]]
- on entry: OBJ:GROUND_ITEM(t101)@(120,104)

```
###############
###############
##+..##########
##+..........##
##+..........##
+++......##..##
##+......+#####
##.......++++##
###############
###############
```

### AREA_HOUSE_INTERIORS_2 / ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_BEDROOM  `[site]`

- size 240x160, open 41 tiles (reachable from entrance: 41, partial: 8), free entity slots on entry: **68**
- components (sizes): [41]
- reco content spot: (120,88)
- table content spots: (88,64)
- special tiles: door40 at [[88, 24]]
- on entry: OBJ:ARCHWAY(t1)@(88,8), OBJ:SPECIAL_CHEST(t250)@(72,64), OBJ:SPECIAL_CHEST(t251)@(88,64), OBJ:SPECIAL_CHEST(t252)@(104,64)

```
###############
###############
##......##.####
##......##.####
##.#....++.++##
#####+.......##
#####+.....++##
##.........####
###############
###############
```

### AREA_CAVES / ROOM_CAVES_HEART_PIECE_HALLWAY  `[site]`

- size 240x240, open 145 tiles (reachable from entrance: 25, partial: 9), free entity slots on entry: **69**
- components (sizes): [60, 60, 25]
- reco content spot: (120,136)
- table content spots: (120,176)
- special tiles: door40 at [[120, 56]]
- on entry: OBJ:SPECIAL_CHEST(t250)@(104,176), OBJ:SPECIAL_CHEST(t251)@(120,176), OBJ:SPECIAL_CHEST(t252)@(136,176)

```
oooo#######oooo
oooo#######oooo
oooo##+++##oooo
oooo##+#+##oooo
oooo##+.+##oooo
oooo##...##oooo
oooo##...##oooo
oooo##...##oooo
oooo##...##oooo
oooo##...##oooo
oooo##...##oooo
oooo##...##oooo
oooo##...##oooo
oooo###+###oooo
oooo###+###oooo
```

### AREA_HOUSE_INTERIORS_4 / ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_WEST  `[site]`

- size 240x160, open 24 tiles (reachable from entrance: 24, partial: 28), free entity slots on entry: **69**
- components (sizes): [24]
- reco content spot: (120,88)
- table content spots: (104,96)
- special tiles: portal61 at [[40, 88], [56, 88], [40, 104], [56, 104]]
- on entry: OBJ:SPECIAL_CHEST(t250)@(88,96), OBJ:SPECIAL_CHEST(t251)@(104,96), OBJ:SPECIAL_CHEST(t252)@(120,96)

```
#######+++#####
###############
####.#####+####
####.##..++####
##++.++...+####
##++......+++++
##++......+####
##...+++.++####
######+########
######+########
```

### AREA_HOUSE_INTERIORS_4 / ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_EAST  `[site]`

- size 240x160, open 43 tiles (reachable from entrance: 43, partial: 16), free entity slots on entry: **71**
- components (sizes): [43]
- reco content spot: (104,88)
- table content spots: (120,96)
- on entry: OBJ:GROUND_ITEM(t101)@(120,96)

```
###############
###############
####..#########
##.....##....##
##+..........##
+++.....+++++##
##+..........##
##+...+++....##
#######+#######
#######+#######
```

### AREA_CAVES / ROOM_CAVES_LON_LON_RANCH  `[site]`

- size 240x256, open 123 tiles (reachable from entrance: 61, partial: 4), free entity slots on entry: **68**
- components (sizes): [61, 42, 20]
- reco content spot: (120,72)
- table content spots: (120,88)
- special tiles: bombwall at [[216, 104]]
- on entry: OBJ:LADDER_UP(t0)@(56,28), OBJ:SPECIAL_CHEST(t250)@(104,88), OBJ:SPECIAL_CHEST(t251)@(120,88), OBJ:SPECIAL_CHEST(t252)@(136,88)

```
###+###########
###+###########
##...........##
##...........##
##........##.##
##......#....##
##...........##
##........##.##
###############
#########oooo##
ooooooo##oooo##
ooooooo##oooo##
ooooooo##oooo##
ooooooo##oooo##
ooooooo###+####
ooooooo###+####
```

### AREA_MINISH_HOUSE_INTERIORS / ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHWEST  `[site]`

- size 240x160, open 25 tiles (reachable from entrance: 25, partial: 14), free entity slots on entry: **67**
- components (sizes): [25]
- reco content spot: (136,72)
- table content spots: (152,83)
- on entry: OBJ:MINISH_SIZED_ARCHWAY(t12)@(120,16), OBJ:MINISH_LIGHT(t1)@(84,128), OBJ:SPECIAL_CHEST(t250)@(136,83), OBJ:SPECIAL_CHEST(t251)@(152,83), OBJ:SPECIAL_CHEST(t252)@(168,83)

```
#######+#######
#######+#######
######+.+.++###
#####+.....+###
######+....+###
###+.......+###
###+.......+###
###############
###############
###############
```

### AREA_MINISH_CAVES / ROOM_MINISH_CAVES_OUTSIDE_LINKS_HOUSE  `[site]`

- size 240x240, open 20 tiles (reachable from entrance: 20, partial: 64), free entity slots on entry: **71**
- components (sizes): [20]
- reco content spot: (120,72)
- table content spots: (120,80)
- on entry: OBJ:GROUND_ITEM(t101)@(120,80)

```
###############
###############
###############
###++.....++###
###++.....++###
###++.....++###
###++.....++###
###+++++++++###
###+++++++++###
###+++++++++###
###+++++++++###
###+++++++++###
#######+#######
#######+#######
#######+#######
```

### AREA_MINISH_HOUSE_INTERIORS / ROOM_MINISH_HOUSE_INTERIORS_SOUTH_HYRULE_FIELD  `[site]`

- size 240x160, open 18 tiles (reachable from entrance: 18, partial: 15), free entity slots on entry: **68**
- components (sizes): [18]
- reco content spot: (136,88)
- table content spots: (120,80)
- on entry: OBJ:MINISH_SIZED_ARCHWAY(t0)@(120,144), OBJ:SPECIAL_CHEST(t250)@(104,80), OBJ:SPECIAL_CHEST(t251)@(120,80), OBJ:SPECIAL_CHEST(t252)@(136,80)

```
###############
###############
#####++########
#####++++######
#####+.....####
####++.....####
####+.....+####
#####+...+#####
#######+#######
#######+#######
```

### AREA_CASTOR_CAVES / ROOM_CASTOR_CAVES_DARKNUT  `[pool]`

- size 240x160, open 80 tiles (reachable from entrance: 34, partial: 16), free entity slots on entry: **68**
- components (sizes): [34, 23, 23]
- reco content spot: (104,104)
- special tiles: door40 at [[104, 24]]
- on entry: OBJ:POT(t0)@(120,75), OBJ:POT(t0)@(136,91), OBJ:POT(t93)@(136,75), OBJ:POT(t0)@(120,91)

```
oooo+########oo
ooo+#########oo
oo+#+....+.##oo
oo##.......##oo
oo##...++..##oo
oo##...++..##oo
oo##.......##oo
oo##.+....+#+oo
oo######+##+ooo
oo######+#+oooo
```

### AREA_CRENEL_CAVES / ROOM_CRENEL_CAVES_BRIDGE_SWITCH  `[pool]`

- size 240x496, open 241 tiles (reachable from entrance: 52, partial: 39), free entity slots on entry: **66**
- components (sizes): [76, 52, 52, 40, 18, 3]
- reco content spot: (136,136)
- special tiles: door40 at [[56, 40]]
- on entry: OBJ:POT(t93)@(168,59), OBJ:POT(t0)@(184,59), OBJ:POT(t93)@(200,59), OBJ:POT(t0)@(40,299), OBJ:POT(t86)@(56,299), OBJ:LIGHTABLE_SWITCH(t1)@(184,280)

```
ooooooooooooooo
#######o#######
#######o#######
##...##o##+++##
##...#####ooo##
##...##########
+#+..........##
o+#+.........##
oo+#+........##
ooo+###+.....##
oooo+###+....##
ooooooo+#+...##
oooooooo##...##
oooooooo##+.+##
oooooooo##+++##
oooooooo##+++##
######oo##ooo##
######o+#+o#o##
##++####+oooo##
##oo###+ooooo##
##ooooooooooo##
##oooooooooo+#+
##oooo#oooo+#+o
##oooooooo+#+oo
##o#ooo####+ooo
##ooooo###+oooo
##ooo#o##oooooo
##ooooo##oooooo
##ooooo##oooooo
####+####oooooo
####+####oooooo
```

### AREA_CRENEL_CAVES / ROOM_CRENEL_CAVES_CHUCHU_POT_CHEST  `[pool]`

- size 240x176, open 72 tiles (reachable from entrance: 10, partial: 23), free entity slots on entry: **63**
- components (sizes): [33, 25, 10, 3, 1]
- reco content spot: (120,104)
- special tiles: door40 at [[56, 40]]
- on entry: OBJ:POT(t0)@(88,75), OBJ:POT(t0)@(104,75), OBJ:POT(t0)@(152,75), OBJ:POT(t0)@(72,91), OBJ:POT(t0)@(168,91), OBJ:POT(t0)@(88,123), OBJ:POT(t0)@(104,123), OBJ:POT(t0)@(136,123), OBJ:POT(t0)@(152,123)

```
ooooooooooooooo
##########+oooo
###########+ooo
##oooooooo+#+oo
###oo++##+o+#+o
##oo+.....+o+#+
##oo#.....#oo##
##ooo++#++ooo##
+#+oooooooooo##
o+#########+###
oo+########+###
```

### AREA_CRENEL_CAVES / ROOM_CRENEL_CAVES_HELMASAUR_HALLWAY  `[pool]`

- size 560x160, open 177 tiles (reachable from entrance: 133, partial: 46), free entity slots on entry: **62**
- components (sizes): [133, 14, 12, 6, 6, 6]
- reco content spot: (280,88)
- special tiles: door40 at [[104, 24]]
- on entry: OBJ:POT(t0)@(40,75), OBJ:POT(t0)@(40,91), OBJ:POT(t0)@(200,107), OBJ:POT(t0)@(216,107), OBJ:POT(t0)@(232,107), OBJ:POT(t0)@(376,59), OBJ:POT(t0)@(392,59), OBJ:POT(t0)@(408,59), OBJ:POT(t0)@(520,75), OBJ:POT(t0)@(520,91)

```
ooo+######+ooooooo+############+ooo
oo+########+ooooo+##############+oo
o+#+......+#######+............+#+o
+#+........+#####+.....+++......+#+
##+.............................+##
##+.............................+##
+#+.........+++....+######+......##
o+#+..............+########+.....##
oo+################+oooooo+####+###
ooo+##############+oooooooo+###+###
```

### AREA_CRENEL_CAVES / ROOM_CRENEL_CAVES_LADDER_TO_SPRING_WATER  `[pool]`

- size 240x160, open 60 tiles (reachable from entrance: 60, partial: 4), free entity slots on entry: **71**
- components (sizes): [60]
- reco content spot: (136,72)
- on entry: OBJ:LADDER_UP(t0)@(120,28)

```
#######+#######
#######+#######
##...........##
##...#.......##
###..........##
##.....#....###
##........#..##
##...#.......##
#######+#######
#######+#######
```

### AREA_VEIL_FALLS_CAVES / ROOM_VEIL_FALLS_CAVES_EXIT  `[pool]`

- size 240x160, open 74 tiles (reachable from entrance: 34, partial: 9), free entity slots on entry: **66**
- components (sizes): [34, 20, 20]
- reco content spot: (88,104)
- special tiles: door40 at [[88, 24]]; bombwall at [[152, 24]]
- on entry: OBJ:POT(t93)@(104,75), OBJ:POT(t0)@(120,75), OBJ:POT(t0)@(136,75), OBJ:POT(t0)@(104,91), OBJ:POT(t0)@(120,91), OBJ:POT(t93)@(136,91)

```
oo###+#######oo
oo###########oo
oo##....#.###oo
oo##.......##oo
oo##..+++..##oo
oo##..+++..##oo
oo##.......##oo
oo##.......##oo
oo#######+###oo
oo#######+###oo
```

### AREA_VEIL_FALLS_CAVES / ROOM_VEIL_FALLS_CAVES_HALLWAY_SECRET_STAIRCASE  `[pool]`

- size 240x160, open 90 tiles (reachable from entrance: 28, partial: 0), free entity slots on entry: **71**
- components (sizes): [62, 28]
- reco content spot: (120,104)
- special tiles: door40 at [[88, 56], [152, 56]]
- on entry: NPC:PARALLAX_ROOM_VIEW(t0)@(100,120)

```
ooooooooooooooo
ooooooooooooooo
oo###########oo
oo###########oo
oo##.......##oo
oo##.......##oo
oo##.......##oo
oo##.......##oo
oo###########oo
oo###########oo
```

### AREA_CRENEL_MINISH_PATHS / ROOM_CRENEL_MINISH_PATHS_MELARI  `[pool]`

- size 800x192, open 384 tiles (reachable from entrance: 384, partial: 2), free entity slots on entry: **71**
- components (sizes): [384]
- reco content spot: (408,104)
- on entry: OBJ:ARCHWAY(t18)@(120,184)

```
##################################################
##################################################
##................................................
##................................................
##................................................
##................................................
##................................................
##................................................
##................................................
##................................................
#######+##########################################
#######+##########################################
```

### AREA_CRENEL_MINISH_PATHS / ROOM_CRENEL_MINISH_PATHS_RAIN  `[pool]`

- size 800x192, open 400 tiles (reachable from entrance: 400, partial: 0), free entity slots on entry: **66**
- components (sizes): [400]
- reco content spot: (408,104)
- on entry: ENEMY:25(t0)@(122,140), ENEMY:25(t0)@(202,90), ENEMY:25(t0)@(214,89), ENEMY:25(t0)@(-2,66), OBJ:WATER_DROP_OBJECT(t0)@(122,140), OBJ:WATER_DROP_OBJECT(t0)@(214,89)

```
##################################################
##################################################
..................................................
..................................................
..................................................
..................................................
..................................................
..................................................
..................................................
..................................................
##################################################
##################################################
```

### AREA_MINISH_PATHS / ROOM_MINISH_PATHS_MINISH_VILLAGE  `[pool]`

- size 240x800, open 498 tiles (reachable from entrance: 498, partial: 14), free entity slots on entry: **57**
- components (sizes): [498]
- reco content spot: (120,408)
- on entry: OBJ:HUGE_ACORN(t2)@(80,112), OBJ:HUGE_ACORN(t0)@(144,352), OBJ:HUGE_ACORN(t3)@(160,560), OBJ:HUGE_ACORN(t1)@(96,672), OBJ:GIANT_LEAF(t1)@(104,264), OBJ:GIANT_LEAF(t0)@(120,440), OBJ:GIANT_LEAF(t1)@(168,760), OBJ:HUGE_ACORN(t255)@(80,112), OBJ:HUGE_ACORN(t255)@(80,113), OBJ:HUGE_ACORN(t255)@(80,112), OBJ:HUGE_ACORN(t255)@(144,352), OBJ:HUGE_ACORN(t255)@(160,560), OBJ:HUGE_ACORN(t255)@(160,561), OBJ:HUGE_ACORN(t255)@(160,560) (+1 more)

```
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
##.+###.#+...##
##.####......##
##.+##+......##
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
##.....+###..##
##.....####..##
##.....+##+..##
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
##...+#.###+.##
##......####.##
##......+##+.##
##...........##
##...........##
##...........##
##...........##
##..###+.....##
##..####.....##
##..+##+.....##
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
```

### AREA_VEIL_FALLS_CAVES / ROOM_VEIL_FALLS_CAVES_HALLWAY_RUPEE_PATH  `[pool]`

- size 240x320, open 115 tiles (reachable from entrance: 75, partial: 71), free entity slots on entry: **57**
- components (sizes): [75, 40]
- reco content spot: (120,184)
- special tiles: door40 at [[152, 24]]
- on entry: OBJ:GROUND_ITEM(t84)@(184,56), OBJ:GROUND_ITEM(t84)@(168,72), OBJ:GROUND_ITEM(t86)@(184,72), OBJ:GROUND_ITEM(t84)@(200,72), OBJ:GROUND_ITEM(t84)@(184,88), OBJ:GROUND_ITEM(t84)@(88,152), OBJ:GROUND_ITEM(t84)@(72,168), OBJ:GROUND_ITEM(t84)@(104,168), OBJ:GROUND_ITEM(t84)@(88,184), OBJ:GROUND_ITEM(t84)@(88,72), OBJ:GROUND_ITEM(t84)@(104,72), OBJ:GROUND_ITEM(t85)@(168,152), OBJ:GROUND_ITEM(t85)@(184,152), OBJ:GROUND_ITEM(t86)@(88,264) (+1 more)

```
oo#############
oo#############
oo##++++.....##
oo##+++++....##
oo##+++++....##
oo##+++++....##
oo##++++.....##
oo##.....++++##
oo##....+++++##
oo##....+++++##
oo##....+++++##
oo##.....++++##
oo##.........##
oo##++++.....##
oo##+++++....##
oo##+++++....##
oo##+++++....##
oo##++++.....##
oo#########+###
oo#########+###
```

### AREA_HOUSE_INTERIORS_1 / ROOM_HOUSE_INTERIORS_1_INN_EAST_2F  `[pool]`

- size 240x448, open 147 tiles (reachable from entrance: 94, partial: 28), free entity slots on entry: **63**
- components (sizes): [94, 53]
- reco content spot: (120,152)
- special tiles: door40 at [[184, 376]]
- on entry: OBJ:ARCHWAY(t5)@(8,72), OBJ:ARCHWAY(t5)@(120,264), OBJ:ARCHWAY(t30)@(120,280), OBJ:ARCHWAY(t5)@(120,296), OBJ:ARCHWAY(t4)@(72,440), OBJ:POT(t0)@(200,91), OBJ:POT(t0)@(40,235), OBJ:POT(t92)@(200,235), OBJ:HOUSE_DOOR_INT(t0)@(72,424)

```
###############
###############
##..###########
##+.###########
+++.###########
##+.........+##
##...........##
##...........##
##...........##
##.......#...##
##......###..##
##.....#####.##
##......###..##
##.......#...##
##+...+++...+##
#######+#######
#######+#######
#######+#######
#######+#######
#######+#######
##oooo+++oooo##
##ooooooooooo##
##oooooooo+o+##
##oooooooo+#+##
##oooooooo+++##
###ooooooooo###
####+##########
####+##########
```

### AREA_HOUSE_INTERIORS_1 / ROOM_HOUSE_INTERIORS_1_LIBRARY_1F  `[pool]`

- size 352x256, open 160 tiles (reachable from entrance: 130, partial: 12), free entity slots on entry: **56**
- components (sizes): [130, 30]
- reco content spot: (200,104)
- special tiles: door40 at [[104, 24]]
- on entry: OBJ:FURNITURE(t0)@(56,40), OBJ:FURNITURE(t0)@(152,40), OBJ:FURNITURE(t0)@(56,104), OBJ:FURNITURE(t0)@(152,104), OBJ:FURNITURE(t60)@(176,152), OBJ:FURNITURE(t2)@(288,104), OBJ:MASK(t0)@(208,8), OBJ:MASK(t1)@(240,8), OBJ:MASK(t0)@(272,8), OBJ:MASK(t1)@(304,8), OBJ:PAPER(t0)@(276,104), OBJ:PAPER(t0)@(300,104), OBJ:ARCHWAY(t4)@(232,248), OBJ:ARCHWAY(t5)@(104,8) (+2 more)

```
######################
######################
#####...###.........##
##..................##
##..................##
##..................##
#####...###.....######
##..................##
#########.......++++##
#############...######
#########+++#...#+++##
oooooo#######...######
oooooo###...........##
oooooo###...........##
oooooo########+#######
oooooo########+#######
```

### AREA_HOUSE_INTERIORS_1 / ROOM_HOUSE_INTERIORS_1_LIBRARY_2F  `[pool]`

- size 240x176, open 48 tiles (reachable from entrance: 48, partial: 5), free entity slots on entry: **63**
- components (sizes): [48]
- reco content spot: (120,88)
- special tiles: door40 at [[120, 24]]
- on entry: OBJ:FURNITURE(t0)@(168,40), OBJ:FURNITURE(t0)@(72,104), OBJ:FURNITURE(t0)@(168,104), OBJ:ARCHWAY(t4)@(120,168), OBJ:ARCHWAY(t5)@(120,8), OBJ:MINISH_SIZED_ENTRANCE(t0)@(72,144), NPC:RUPEE_OBJECT(t2)@(56,64), OBJ:FURNITURE(t37)@(72,40), OBJ:CAMERA_TARGET(t0)@(-544,0)

```
###############
###############
######...######
###.........###
###.........###
###.........###
######...######
###.........###
###...+++...###
#######+#######
#######+#######
```

### AREA_HOUSE_INTERIORS_1 / ROOM_HOUSE_INTERIORS_1_SCHOOL_WEST  `[pool]`

- size 240x240, open 106 tiles (reachable from entrance: 106, partial: 18), free entity slots on entry: **62**
- components (sizes): [106]
- reco content spot: (120,136)
- on entry: OBJ:ARCHWAY(t4)@(120,232), OBJ:ARCHWAY(t5)@(232,88), OBJ:POT(t0)@(56,43), OBJ:POT(t0)@(40,43), OBJ:POT(t0)@(40,59), OBJ:POT(t0)@(200,43), OBJ:POT(t0)@(184,43), OBJ:POT(t0)@(200,59), OBJ:OBJECT_BLOCKING_STAIRS(t0)@(120,72), NPC:FILE_SCREEN_OBJECTS(t1)@(120,120)

```
###############
###############
##++.......++##
##+...+++...+##
##....+#+....##
##....+++....++
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
##...........##
#######+#######
#######+#######
```

### AREA_MINISH_HOUSE_INTERIORS / ROOM_MINISH_HOUSE_INTERIORS_FESTARI  `[pool]`

- size 464x256, open 160 tiles (reachable from entrance: 160, partial: 34), free entity slots on entry: **68**
- components (sizes): [160]
- reco content spot: (232,136)
- on entry: OBJ:MINISH_SIZED_ARCHWAY(t5)@(232,224), OBJ:MINISH_SIZED_ARCHWAY(t6)@(232,32), NPC:SHOP_ITEM(t0)@(248,72), OBJ:CAMERA_TARGET(t0)@(-112,-320)

```
##############+##############
##############+##############
#####+..+#####+#####+..+#####
####+....+####+####+....+####
####......+#.....#+......####
####.....................####
####+.....##.....##.....+####
#####+....##.....##....+#####
#####+.................+#####
####+.....##.....##.....+####
####......##.....##......####
####.....................####
####+....+####+####+....+####
#####+..+#####+#####+..+#####
##############+##############
##############+##############
```

### AREA_DARK_HYRULE_CASTLE / ROOM_DARK_HYRULE_CASTLE_3F_TRIPLE_DARKNUT  `[pool]`

- size 336x256, open 208 tiles (reachable from entrance: 146, partial: 13), free entity slots on entry: **62**
- components (sizes): [146, 31, 31]
- reco content spot: (168,136)
- on entry: OBJ:FAIRY(t96)@(94,83), OBJ:LOCKED_DOOR(t0)@(168,40), OBJ:POT(t95)@(56,59), OBJ:POT(t95)@(280,59), OBJ:POT(t95)@(56,203), OBJ:POT(t95)@(280,203), OBJ:FAIRY(t96)@(98,76), OBJ:SPECIAL_FX(t7)@(93,79), OBJ:SPECIAL_FX(t7)@(98,82), OBJ:SPECIAL_FX(t7)@(98,76)

```
ooooooooo###ooooooooo
o###################o
o###################o
o##+.............+##o
o##...............##o
o##...............##o
o##...............##o
o##...............##o
o##...............##o
o##...............##o
o##...............##o
o##...............##o
o##+.............+##o
o########+++########o
o########+++########o
oooooooo#+++#oooooooo
```

### AREA_DARK_HYRULE_CASTLE_BRIDGE / ROOM_DARK_HYRULE_CASTLE_BRIDGE_MAIN  `[pool]`

- size 272x320, open 57 tiles (reachable from entrance: 45, partial: 129), free entity slots on entry: **71**
- components (sizes): [45, 6, 6]
- reco content spot: (136,152)
- special tiles: door40 at [[136, 24]]
- on entry: NPC:PARALLAX_ROOM_VIEW(t0)@(120,104)

```
#################
#################
##++++#...#++++##
##++++#...#++++##
##++++#...#++++##
##++++#...#++++##
##++++#...#++++##
##++++#...#++++##
##++++#...#++++##
##++++#...#++++##
##++++#...#++++##
##++++#...#++++##
##++++#...#++++##
##++++#...#++++##
##++++#...#++++##
##++++#...#++++##
##++++#...#++++##
#######+++#######
#######+++#######
oooooo#+++#oooooo
```

### AREA_SANCTUARY_ENTRANCE / ROOM_SANCTUARY_ENTRANCE_MAIN  `[pool]`

- size 272x432, open 220 tiles (reachable from entrance: 220, partial: 4), free entity slots on entry: **71**
- components (sizes): [220]
- reco content spot: (136,216)
- special tiles: door40 at [[136, 56]]
- on entry: OBJ:MINISH_VILLAGE_OBJECT(t1)@(136,64)

```
#################
#################
#################
########+########
##.............##
##.............##
##.............##
##.##.......##.##
##.##.......##.##
##.............##
##.##.......##.##
##.##.......##.##
##.............##
####.........####
####.........####
##.............##
##.##.......##.##
##.##.......##.##
##.............##
##.............##
##.##.......##.##
##.##.......##.##
##.............##
##.............##
########+########
########+########
########+########
```

### AREA_NULL_61 / ROOM_NULL_61_0  `[pool]`

- size 240x240, open 10 tiles (reachable from entrance: 10, partial: 131), free entity slots on entry: **72**
- components (sizes): [10]
- reco content spot: (120,168)
- special tiles: door40 at [[120, 88]]

```
###############
###############
###############
###############
###############
###+++#.#+++#++
###++++.+++++++
+++++++.+++++++
+++++++.+++++++
+++++++.+++++++
+++++++.+++++++
+++++++.+++++++
+++++++.+++++++
+++++++.+++++++
+++++++.+++++++
```

### AREA_HOUSE_INTERIORS_3 / ROOM_HOUSE_INTERIORS_3_STOCKWELL_SHOP  `[shop]`

- size 240x208, open 54 tiles (reachable from entrance: 31, partial: 20), free entity slots on entry: **62**
- components (sizes): [31, 15, 8]
- reco content spot: (104,136)
- special tiles: portal61 at [[184, 72], [200, 72], [184, 88], [200, 88]]
- on entry: OBJ:SHOP_ITEM(t108)@(40,120), OBJ:SHOP_ITEM(t110)@(56,120), OBJ:SHOP_ITEM(t13)@(72,120), OBJ:SHOP_ITEM(t100)@(168,120), OBJ:SHOP_ITEM(t102)@(56,152), NPC:PARALLAX_ROOM_VIEW(t0)@(192,168), OBJ:SHOP_ITEM(t99)@(136,120), OBJ:SHOP_ITEM(t40)@(152,120), OBJ:SHOP_ITEM(t101)@(40,152), OBJ:SHOP_ITEM(t72)@(72,152)

```
ooooooooooooooo
###############
##########+####
##########+####
##########o++##
##.....#ooo++##
##.....#oooo+##
##++++.#++++###
######.########
##...........##
##....+++....##
#######+#######
#######+#######
```

### AREA_MINISH_HOUSE_INTERIORS / ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_EAST  `[melari]`

- size 352x160, open 49 tiles (reachable from entrance: 46, partial: 33), free entity slots on entry: **67**
- components (sizes): [46, 2, 1]
- reco content spot: (136,88)
- on entry: OBJ:MINISH_SIZED_ARCHWAY(t14)@(16,80), OBJ:MINISH_LIGHT(t3)@(88,104), OBJ:MINISH_LIGHT(t3)@(184,104), OBJ:MINISH_LIGHT(t3)@(304,48), NPC:PARALLAX_ROOM_VIEW(t0)@(136,80)

```
######################
######################
###+##################
##+.++++++++++++++####
++............+++o+###
++...........+###+oo##
##++.#.....#.+###.++##
###+..............+###
######################
######################
```

### AREA_MINISH_HOUSE_INTERIORS / ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHEAST  `[melari]`

- size 240x160, open 26 tiles (reachable from entrance: 21, partial: 17), free entity slots on entry: **69**
- components (sizes): [21, 5]
- reco content spot: (152,72)
- on entry: OBJ:MINISH_SIZED_ARCHWAY(t13)@(120,16), OBJ:MINISH_LIGHT(t2)@(72,32), OBJ:GROUND_ITEM(t99)@(152,83)

```
#######+#######
#######+#######
###+#.+.+######
##+.......#####
##..+##+...+###
##+.+###...+###
###+o+++...+###
####oooo#######
###############
###############
```

## Findings and decisions needed

1. **Hyrule Castle Cellar site is shadowed** by the NW-ladder redirect (see
   its entry). Decide: exempt or retire.
2. **ROOM_NULL_61_0 retired from the large pool** (fixed this pass): 10
   open tiles in an area named NULL cannot host large-pool kinds.
3. **Pot prize could fail to spawn in crowded rooms** (fixed this pass):
   target now capped by live entity headroom; verified in the Boomerang
   chamber (28 free slots -> prize present).
4. **Content spots now self-correct** (fixed this pass): any kind's spot
   snaps to open ground centrally, so future table rows can't silently
   break chest/NPC/fairy kinds.
5. **Stairs split components in this model** - Goron Cave Main (5 comps),
   Heart Piece Hallway, Veil Falls staircases and others carry special
   collision (0x61/0x63/0xf1) that this survey counts as walls, so floors
   joined by a staircase read as separate components. Trust the flagged
   notes over raw component counts in those rooms.
5b. **The shop's right shelf is the vanilla MINISH shelf** - RESOLVED.
   The survey found 4 Minish-portal act tiles (0x3d) at (184-200, 72-88)
   inside the 8-tile right alcove; the in-game check confirmed the alcove
   is its own component with no normal-size route, so the three catalog
   items sitting on its shelf at y=120 could not be picked up. Measured
   fix: the shelf's FRONT row at y=136 sits directly above the lower
   room's floor at y=152, which is ordinary reachable ground, and the lift
   fires from there. All nine catalog items are now on the three shelves
   the user marked, each verified liftable in the emulator (park a real
   SHOP_ITEM, stand on the adjacent floor, press R, assert
   gPlayerState.heldObject == 4).
6. **Boomerang chamber is the busiest room in the game**: 44 entities on
   entry, 28 free slots, five events. It works, but it is the room to test
   first after any change that spawns more.
7. **Ranch House West contains 4 Minish-portal tiles** and the two
   MINISH_SIZED_ENTRANCE doors outside lead here - the "unwired Minish
   connection" in Lon Lon Ranch. Wiring decision needed: those doors need
   the Minish shrink to be usable at all.
8. **Multi-floor pool rooms** (Inn East 2F, Library 1F, Bridge Switch,
   Chuchu Pot Chest, Helmasaur Hallway...) have significant floor outside
   the entrance component. Events anchor on the player, so content lands on
   the entered floor - fine - but reward pools should avoid placing the
   payout across a stair boundary; the reco spots listed here are all in
   the entrance component.


## North Hyrule Field's through-cave (ROOM_CAVES_TO_GRAVEYARD)

Corrected finding. This file and two comment blocks in transitions.c used to
say this cave "reaches Royal Valley and so escapes the run", and treated both
ends of it as things to neutralize. Its exit list says otherwise:

    (0x38,0x38)  -> North Hyrule Field (0x88,0xd8)
    (0x118,0x38) -> North Hyrule Field (0x118,0xd8)
    (0x138,0x98) -> ROOM_CAVES_HEART_PIECE_HALLWAY (0x78,0x48)
    border south -> North Hyrule Field (0x108,0x148)

Three mouths back into the same field and one door into the Heart Piece
Hallway, whose own only other exit is that same field. The two caves are a
closed pocket and always were, so there was never anything to contain.

It is reached by its own vanilla mouth now (the synthetic teleport box at
local (264,304), six pixels short of the real mouth at (264,312), is gone),
hosts a ? event through the old connector's kind/extra roll, and is blessed
past containment by name in QuickStartIsPocketInteriorRoom. The hallway's
onward door is vanilla again.

Verified: walking into the field mouth lands in the cave (368x240) with its
event live; walking up through the hallway's onward door lands in the cave.
The cave-side door back into the hallway reads act tile 0x28 (armed) with a
staircase tile arrangement around it - confirmed in data, not yet walked,
because the scripted harness cannot land on a staircase tile the way a
player does.
