# The hub: Home of the Wind Tribe

Scope and build plan for the structural change that replaces Castor Darknut
Hall as the run's start and pulls the shop out of the "? room" pool.

**Status: steps 1-5 of §6 are built and verified.** The run spawns on Floor
3, walks down and out, and drops through the pit in Cloud Tops into its first
overworld region past the shop on Floor 1; Castor Darknut and Melari's Mine
are off the route, and the roof runs its wave. Steps 6-8 (inn, wind crest,
content sites) are still to do. Every
coordinate below is measured off the live ROM, not read from a map dump - the
survey is in §2 and is the part that makes the build cheap.

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

### 3.3 The shop (Floor 1) - BUILT

Gone: `sQuickStartShopDoors`, `QuickStartShopGetDoor`, the `GF_SHOP_DOOR_BIT`
draw, the redirect in `QuickStartProcessDoorRedirects`, and
`QuickStartFixupShopReturn`. Kept verbatim: `sQuickStartShopCatalog`, the
per-run price roll, the merchant NPC and `script_QuickStartMerchant`.

**This retired two open bugs at once** - the unreachable right-shelf alcove
(roadmap §5) and the shop's dependency on a drawn door.

Layout, measured: Floor 1 is two blocks joined by the stair column at tile
column 3, and they really are one connected component (walked it: (56,112)
down to (56,302), and (56,216) back up to (56,87)). The catalog goes in the
UPPER hall, rows 5-7 -

```
y=88    five items    (row 5)
y=104   the walkway   (row 6), merchant at its east end (192,104)
y=120   four items    (row 7)
```

- because the lower block is where the traffic is: arriving from the Entrance
lands at (184,248) and from Floor 2 at (136,248), and stock strewn across the
arrival tiles is exactly the complaint the Stockwell layout drew.

**No obstacle sweep here.** The Stockwell room's blanket "delete every OBJECT
that isn't a SHOP_ITEM" would have taken Floor 1's two `ARCHWAY` objects with
it, and those sit on the stair doors at (136,216) and (184,216) - the room's
only way in or out. `QuickStartClearHubRoom` already handles the floor's
enemies and NPCs while sparing the ZELDA-kind merchant, which is all that is
needed.

### 3.4 The roof wave - BUILT

One wave at `QuickStartGetDifficulty() + 2` (clamped to 12), cleared-detection
via `QuickStartCountRoomEnemies`, and on clear a
`QuickStartDrawAtTier(seed, QS_CAT_REWARD, tier)` that is RARE one time in
four and UNCOMMON otherwise.

**Hand-placed offsets, not the open-tile spawner.** Flooding the roof from the
arrival spot (184,328) gives a 121-tile component spanning rows 10-24: a north
band (rows 11-13, columns 1-13), a west corridor (rows 14-19, columns 1-5),
and a south arena (rows 20-24). Rows 0-5 - the tower's peak and its two wings
- are open tiles that are **not** in that component.
`QuickStartSpawnEnemiesOnOpenTiles` rings outward over any open tile within 40
rings, so it would put part of every wave up there, where the player cannot
follow and the fight can never be cleared. `sQuickStartRoofEnemyOffsets` is 14
interior tiles of the component instead, each with all four neighbours open
and none within a tile of the arrival.

The roof is also **exempt from `QuickStartClearHubRoom`'s enemy sweep** - that
runs every frame on every hub room and would delete the wave on the frame it
appeared. Its NPC half still runs. Safe because a live entity dump of the roof
found no vanilla enemies, only objects.

Density: the arena is 30 of the 32x32 squares the density formula counts in,
and the code passes 60. That is tuning, stated as such - at the honest 30 the
wave is two enemies at difficulty 2 and six at 12, which is not worth climbing
for; at 60 it runs 4 to 10.

**The reward's draw seed is stored** (`GF_ROOF_SEED_BIT`, six bits). The
reward has a re-drop arm - state "cleared" with nothing on the floor means the
player left and came back - and rolling fresh there turned the roof into a
slot machine: the same cleared roof handed over ITEM_RUPEE100 and then
ITEM_BOTTLE_RED_POTION on consecutive visits. Rolling once and replaying the
seed fixes which item that roof gives.

Leaving mid-fight and returning gives a *fresh wave*, by keeping the
"spawned this visit" latch in room flags: the fight is one visit's work rather
than something to whittle down over several trips.

### 3.5 The hole to the overworld - BUILT

Destination is chain slot 0, which is already fixed for the whole run (the
chain is drawn once per run, `GF_REGION_CHAIN_*`), so nothing extra is stored.

**A position box on the hole does not work, and this is the interesting part.**
The first build put a box at (440-540, 552-600), measured off a survey of
"special" tiles at rows 34-36. Those are not the pit. The pit's real geometry
is in `holeManager.c`'s own `gHoleTransitions` table - the row
`{ 0x01, 0x08, 0x01, 0x01, ..., 0x1d, 0x1d, 0x03, 0x03 }` is tiles (29,29)
3x3, i.e. pixels **(464,464)-(512,512)**, a good 40px north of where the box
was. The player fell through the real pit before ever reaching the trigger,
landed on the vanilla cloud level, and the feature looked simply absent.

`QuickStartProcessHubHoleLink` catches the fall instead of the position:
`DoHoleTransition` sets `gRoomTransition.transitioningOut` and fills
`player_status` exactly the way a real door does, so the same
rewrite-the-destination idiom `QuickStartProcessDoorRedirects` uses works, and
works for *every* pit in the room rather than one hand-measured rectangle.
Cloud Tops' only non-pit exit is the tower door (area 48), so "a transition
out of here heading to another Cloud Tops room" is an exact description of a
pit fall. The drop animation is left as the hole manager set it up, so the
player really does fall out of the sky into the region.

**Lesson for the rest of this build: when vanilla already has a table for a
thing, read the table.** A tile survey is a guess about what the table says.

### 3.6 The wind crest

`gSave.windcrests` bit for Cloud Tops, set at run start next to the other
boot grants. The eight fast-travel destinations are ordinary `Transition`
rows in `gUnk_08128024` (`src/menu/kinstoneMenu.c`) - see
`QUICKSTART_ITEM_TIERS.md` §9, which already researched this. Making the hub
one of the eight is data.

---

## 4. What gets retired

- **Castor Darknut Main and Hall - DONE.** Gone: the three Main waves
  (`QuickStartSpawnEnemies`/`Wave2`/`Wave3` and the 35-spot offset table they
  shared), Hall's ambient Octoroks, `QuickStartSpawnHallReward`'s heart piece,
  phases 6-9 of the item-choice machine, both `sQuickStartLinks` rows into and
  out of Hall, and `AREA_CASTOR_DARKNUT` from `QuickStartAreaContained`.
- **Melari's Mine - ROUTING DONE, CONTENT KEPT.** `QuickStartSkipMelarisMine`
  and the Door B region-chain box are gone; the mine's own content
  (`QuickStartClearMelarisMineObstacles`, its reward, its enemies, the three
  side rooms and their dispatchers, the Southwest content site) is kept whole
  per the user, dormant until the area comes back.

  The load-bearing detail: **Castle Garden's south border still points at
  Melari's Mine** (`transitions.c`), from when the mine was the hub. With the
  skip deleted that row would have stranded the player; with the skip still in
  place it was a free warp straight to region slot 0. Dropping
  `AREA_MELARIS_MINE` from `QuickStartAreaContained` turns it into a wall
  instead - contained Castle Garden may not leave for a non-contained area, so
  `QuickStartEnforceContainment` cancels it and the player just stops at the
  edge, no fade, no bounce. The row is deliberately *not* reverted to vanilla's
  North Hyrule Field, which containment would sometimes allow (whenever this
  save's chain puts NHF at slot 0 or right after Castle Garden) - that would
  make the edge a wall on some runs and a shortcut on others.
- **The shop's door-draw machinery**, as above - still to do (step 4).

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

1. ~~**Move the spawn.**~~ DONE. Build defines point at 48/3, item row in the
   measured hall, three rounds confirmed. Needed two follow-ups found in play:
   the vanilla Wind Tribe NPCs stand in doorways (`QuickStartClearHubRoom`
   sweeps enemies and non-ZELDA NPCs every frame), and the tower's front door
   is walled by solid tiles on rows 19-20 that the same function clears once.
2. ~~**Wire the hole.**~~ DONE - see §3.5, including why the first attempt
   silently did nothing.
3. ~~**Retire Castor Darknut and the Melari skip.**~~ DONE - see §4.
4. ~~**Move the shop to Floor 1.**~~ DONE - see §3.3. Covered by a new
   `hub` tier in `invariant_check.py`: 10 boots that check every catalog prop
   spawns on its table spot and actually lifts (press R, read
   `gPlayerState.heldObject`) rather than trusting the collision map.
5. ~~**The roof wave and its reward.**~~ DONE - see §3.4. Covered by the
   `hub` invariant tier, which floods the component and fails if any enemy
   lands outside it.
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


---

## 8. Measured facts worth not re-deriving

- **The tower stairs work, in both directions, on every floor.** A probe that
  warped onto Floor 3's stair tiles and found nothing firing looked for a
  while like the spawn floor was a dead end. It is not: Floor 3 is
  `QUICKSTART_ROOM`, so the arrival Ezlo hint is on screen, and an open
  message box blocks all player input. Dismiss it first. Walked end to end
  afterwards: Floor 3 -> Floor 2 -> Floor 1 -> Entrance -> Cloud Tops -> the
  pit -> the run's first region.
- **The stair doors' trigger tiles are (136,232) and (184,232)** on every
  floor, approached from the lower block by holding toward the archway from
  around y=250. The `ARCHWAY` objects at (136,216)/(184,216) sit on them.
- **Floor 1 arrivals**: (184,248) coming up from the Entrance, (136,248)
  coming down from Floor 2.
- **On every tower floor the WEST archway (136,232) goes up and the EAST one
  (184,232) goes down.** On Floor 3 the west archway is the way onto the roof.
- **The roof is not convex.** Its north band is reached from the arrival only
  through the west corridor at columns 1-5; walking straight north from the
  arrival hits a wall at row 19. Anything that has to cross the roof needs a
  route, not a heading.
- The exit-list names in `transitions.c` are off by one against the room they
  serve (`gExitList_WindTribeTower_Floor2` is Floor 1's list, and so on).
  Read `gExitLists_WindTribeTower` rather than the names.
