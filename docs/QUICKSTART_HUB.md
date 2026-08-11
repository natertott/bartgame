# The hub: Home of the Wind Tribe

Scope and build plan for the structural change that replaces Castor Darknut
Hall as the run's start and pulls the shop out of the "? room" pool.

**Status: scoped, not implemented.** Every coordinate below is measured off
the live ROM, not read from a map dump - the survey is in §2 and is the part
that makes the build cheap. Implementation order is §6.

---

## 1. What the hub is

Six rooms, one vertical stack plus its exterior. Vanilla's tower is a clean
`WARP_TYPE_AREA` staircase chain, so the floors already connect the way the
design needs and no transition rewiring is required for movement inside it.

| room | id | role |
|---|---|---|
| Cloud Tops (exterior) | `AREA_CLOUD_TOPS` / `ROOM_CLOUD_TOPS_CLOUD_TOPS` | wind crest + the hole out to the overworld |
| Tower Entrance | 48 / 0 | ground floor, arrival from outside |
| Floor 1 | 48 / 1 | **the shop** |
| Floor 2 | 48 / 2 | **the inn** |
| Floor 3 | 48 / 3 | **spawn + item selection** |
| Roof | 49 / 0 | **enemy wave + reward** |

Vanilla stair links, confirmed in `gExitLists_WindTribeTower`: Entrance <-> F1
<-> F2 <-> F3 <-> Roof, and Entrance's south border goes to Cloud Tops. The
player walks the whole hub without a single custom transition.

---

## 2. Survey (measured, `tools/quickstart/emu.py`)

All four tower floors are **240x336 (15x21 tiles)**; the roof is **240x416
(15x26)**. `.` = fully open, `o` = partial/special, `#` = solid.

### Floor 3 - spawn and item selection (108 open tiles, the largest)

```
###############   rows 0-1
#####.....#..##   2
##...........##   3
##...........##   4      <- the open hall: rows 3-7, tx 2-12
##...........##   5
##...........##   6
##...........##   7
###o###########   8-12   <- stairs down, tx 3
##...##########   13-14
##...........##   15-17
##o.........o##   18-19
###############   20
```

Arrival is the stair head at the top of the lower block. The item row goes in
rows 3-7, which is 11 tiles wide and clear - more room than Castor Darknut
Main had, so the existing three-slot layout drops straight in.

### Floor 2 - the inn (74 open tiles)

```
###############   0-2
####.##.##.####   3      <- THREE ALCOVES at tx 4, 7, 10: the three beds
####.##.##.####   4
##...........##   5
##.....o###o.##   6      <- the two 'o' at tx 7 and tx 11: the chests
##.....o###o.##   7
###o###########   8-12
##...##########   13-14
##...........##   15-17
##o...ooo...o##   18
###############   19-20
```

This is the room the design describes exactly: three separate bed alcoves in
a row, with chest-shaped objects between them. The three bed tiles are
**(4,3), (7,3), (10,3)** in tiles = **(72,56), (120,56), (168,56)** in pixels.

### Floor 1 - the shop (95 open tiles)

```
###############   0-1
#####.##.##..##   2
####..##.##..##   3
####..oo.##..##   4
##...........##   5      <- main floor, rows 5-7
##...........##   6
##...........##   7
###o###########   8-12
##...##########   13-14
##...........##   15-17
##......oo...##   18
###############   19-20
```

Nine catalog items fit comfortably in rows 5-7 (11 tiles wide) plus the
row-15-17 block. **Unlike the current shop room, every candidate tile here is
in one connected floor** - the alcove-unreachability problem that has bitten
the shop twice cannot recur.

### Roof - the wave (184 open tiles, much the biggest)

```
...............   0-1
.....#####.....   2
....#######....   3
....##o.o##....   4
oooo##...##oooo   5
######...######   6
######ooo######   7-9
#o.oo#...#oo.o#   10
#.............#   11-13   <- south arena, 13 wide
#.....#########   14-19
#.............#   20-21
#ooo.......ooo#   22
####.......####   23-24
###############   25
```

Two arenas: rows 11-13 (13 tiles wide) and rows 20-24. Plenty for a wave, and
the existing open-tile placer will find the ground on its own.

### Entrance and Cloud Tops

Entrance (92 open tiles) is a pass-through. **Cloud Tops is not yet
surveyed** - it is the one measurement still outstanding, needed for the wind
crest and hole positions. See §5.

---

## 3. Mechanics to build

### 3.1 Item selection (Floor 3)

Move, not rebuild. `QuickStartUpdateItemChoice` already runs the three rounds
against `QUICKSTART_AREA`/`QUICKSTART_ROOM` build defines; pointing those at
48/3 relocates the whole phase. The Zelda sign NPC
(`script_QuickStartChooseOne`) and the Ezlo "your item picks your path" hint
(custom string 5) come along unchanged.

### 3.2 The inn (Floor 2)

| bed | price | heal | chests |
|---|---|---|---|
| comfy | 50 | 25% of max, min 1 heart | empty |
| super comfy | 200 | 50% of max, min 2 hearts | COMMON rewards |
| ultra comfy | 500 | full | UNCOMMON rewards |

Never rare, per the design.

Reuse, in order of preference:
- **Payment + dialogue**: the merchant's own flow
  (`script_QuickStartMerchant`, `ScriptCommand_SaleItemConfirmMessage` /
  `CheckShopItemPrice` / `BuyShopItem`) already does "confirm a price, take
  the rupees, refuse politely if short". Three beds = three interactables
  with three prices.
- **The sleep fade**: vanilla's own inn is worth reading first
  (Hyrule Town). If its script is not reusable, `TRANSITION_FADE_BLACK_SLOW`
  plus a re-entry of the same room gives the same read for far less risk -
  the exact technique `QuickStartReloadRoomAfterFusion` already uses.
- **Healing**: `ModHealth(+n)`. Max health is `gSave.stats.maxHealth`; a
  heart is 4 units in this engine (see the ITEM_HEART_CONTAINER comment in
  game.c), so "25%, min 1 heart" is `max(maxHealth / 4, 4)`.
- **Chest contents**: `QuickStartDrawAtTier(seed, QS_CAT_REWARD, tier)` -
  the tier system already takes a forced tier and a category mask, so this
  is one call, no new pool.

**Open question for the build**: the two chest objects are vanilla
`SPECIAL_CHEST` / `CHEST_SPAWNER` entities, and those resolve their contents
from room-authored tile data we do not have - the same wall
`QuickStartSpawnHallReward` hit when it wanted a literal chest. Most likely
answer is to sweep them and place ground items on the same tiles, which is
what every other reward in this mode does. Decide by measuring, not by
guessing.

### 3.3 The shop (Floor 1)

The shop stops being a "? room". Delete `sQuickStartShopDoors` and the
per-run door draw (`QuickStartShopRandomizeOnce` and its redirect); keep
`sQuickStartShopCatalog`, the per-run price roll, the merchant NPC and
`script_QuickStartMerchant` verbatim. Only the placement table changes: nine
new offsets inside Floor 1's connected floor.

**This retires two open bugs at once** - the unreachable right-shelf alcove
(roadmap §5) and the shop's dependency on a drawn door.

### 3.4 The roof wave

`QuickStartSpawnWave(contentX, contentY, wave, difficulty)` with difficulty
one tier above the run's own, cleared-detection via
`QuickStartCountRoomEnemies`, and on clear a
`QuickStartDrawAtTier(..., QS_CAT_REWARD, ...)` split between UNCOMMON and
RARE. All four pieces exist; this is assembly.

### 3.5 The hole to the overworld

Behaviourally identical to what `QuickStartSkipMelarisMine` already does -
warp to chain slot 0 - so the mechanism is proven. Two differences:
- It fires from a position box on the hole rather than on room entry.
- **The destination is fixed for the whole run.** That is already true: the
  region chain is drawn once per run (`GF_REGION_CHAIN_*`), so slot 0 does
  not move. Nothing extra to store.

### 3.6 The wind crest

`gSave.windcrests` bit for Cloud Tops, set at run start next to the other
boot grants. The eight fast-travel destinations are ordinary `Transition`
rows in `gUnk_08128024` (`src/menu/kinstoneMenu.c`) - see
`QUICKSTART_ITEM_TIERS.md` §9, which already researched this. Making the hub
one of the eight is data.

---

## 4. What gets retired

- **Castor Darknut Main and Hall.** Main is the current item-selection room,
  Hall the one-wave gate after it. Both stop being visited once
  `QUICKSTART_AREA`/`QUICKSTART_ROOM` point at the tower. The Hall's wave is
  not worth preserving - the roof wave replaces it and is optional.
- **Melari's Mine.** Already bypassed by `QuickStartSkipMelarisMine`; the
  skip and the room's own content can go. Per the user this area comes back
  when the region pool grows, so **delete the routing, keep the room tables**
  (`QuickStartSetupMelariEastRoomContent` and friends) rather than ripping
  them out.
- **The shop's door-draw machinery**, as above.

---

## 5. Still to measure before writing code

1. **Cloud Tops collision map and entity list** - needed for the wind crest
   and hole positions, and to know how much vanilla content is out there.
2. **What vanilla content actually sits in the five tower rooms.** The
   entity scan in the survey pass returned values that are not entity kinds,
   so it was not trustworthy and is not reported above. `QuickStartClear
   VanillaRoomContent` sweeps generically, so this is unlikely to be work -
   but it should be *seen*, not assumed, before calling the rooms clear.
3. **Whether Floor 2's two chest objects can be filled**, per §3.2.
4. **Vanilla's Hyrule Town inn script**, to judge reuse versus a plain fade.

---

## 6. Build order

Each step is separately verifiable and leaves the game playable.

1. **Move the spawn.** Point the build defines at 48/3, relocate the item row
   to the measured hall, confirm the three rounds still run. *This alone is a
   shippable change and the riskiest one - do it first and alone.*
2. **Wire the hole.** Position box in Cloud Tops -> chain slot 0. The run is
   then fully playable through the new hub.
3. **Retire Castor Darknut and the Melari skip.**
4. **Move the shop to Floor 1.**
5. **The roof wave and its reward.**
6. **The inn.** Last because it is the only genuinely new mechanic and the
   only one with an unresolved question (the chests).
7. **Wind crest**, which is data once the rest works.
8. Content sites for the hub rooms if wanted later - the tower floors are
   good candidates once they are cleared.

---

## 7. Risks

- **The spawn move is the one change that can brick a run.** Everything else
  degrades; a broken spawn is unplayable. Verify in the emulator before
  moving on, and keep the Castor Darknut defines in a comment so the revert
  is one line.
- **Containment.** `QuickStartEnforceContainment` and friends currently
  assume the run starts at Castor Darknut and passes through Melari's Mine.
  Every one of those checks needs re-reading against the new flow, or the
  player will be bounced out of their own hub.
- **The hub is six rooms of new surface** in a mode whose recurring failure
  is hand-placed coordinates. Every table row added here should get an
  invariant-checker tier before it is trusted.
