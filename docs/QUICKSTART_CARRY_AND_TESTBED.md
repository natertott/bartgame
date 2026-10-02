# Two designs: the item-carry quest, and a feature testbed

Written Oct 2026 against head `c04b478`, in answer to two questions: can a
player carry a thing across screens and deliver it for a reward, and how
does one test any single feature of the mode without waiting for a run to
deal it. Both answers are built on what the ROM already does, read from
the source and measured in the emulator where it mattered. Neither is
implemented; this is the plan.

---

## 1. The item-carry quest

### 1.1 What the engine already gives us

**Carrying is one of two mechanisms, and only one of them survives a room
change at all.**

* *Lifted objects* (pots, bushes, rocks): `itemTryPickupObject.c` sets
  `gPlayerState.heldObject = 3` and the lifted thing becomes a
  `playerItemHeldObject` riding over Link's head. Throwable, breaks on
  impact, and a plain pot is not an "item" the game can name.
* *Carried props* (`SHOP_ITEM`, `src/object/itemForSale.c`): press A on
  one and `ItemForSale_Action1` runs `PausePlayer(); ResetActiveItems();
  heldObject = 4; gPlayerEntity.carriedEntity = prop;` and puts DROP on the
  R button. While carried the prop follows the player every frame
  (`ItemForSale_Action2`) and A/B/R puts it down (`sub_080819B4`). It wears
  the sprite of ANY item id, which is the point: it can be "the milk",
  "the mushroom", "the book", whatever the quest names.

The mode already uses the second mechanism as a mechanic: the Fountain of
Sacrifice (`QuickStartSacrificeMonitor`) strews props with
`QuickStartSpawnShopItem`, lets the player lift one, and reads
`carriedEntity` when they stand on the circle. So "carry a prop to a spot
and have the spot notice" exists, in one room.

**Across a room boundary, nothing survives on its own** - and that is by
engine design, not an accident:

* Every room change, seam scroll (`sub_08051D98`) or door (`sub_08051DCC`),
  runs `RecycleEntities`, which deletes every entity without
  `ENT_PERSIST`. A `SHOP_ITEM` prop has no such flag. Measured: a prop
  left loose in the ranch house's west room is gone the frame the seam
  scrolls to the east room.
* The player's own carry state is zeroed by `ResetActiveItems`
  (`playerUtils.c:395`, `heldObject = 0`), which the player's room re-init
  calls, and by `PlayerDropHeldObject` wherever vanilla's scripts and
  transitions want a free Link. `carriedEntity` would dangle at a deleted
  entity if it were not nulled with it.

So "carry across screens" cannot be done by keeping the entity. It has to
be done by **remembering what is carried and rebuilding the carry on
arrival** - which is small, because both halves already exist.

### 1.2 The design: a carry token

Three parts.

**The token.** One byte in the save: `gSave.carry_item` (the `filler38[8]`
spare at 0x38 has room; see §2.3, which wants the rest of it). 0 = hands
empty. Nonzero = the item id whose prop the player is carrying *across a
boundary right now*.

**Stash on the way out.** The mode already watches every transition the
frame it fires (`gRoomTransition.transitioningOut`, the same hook the door
redirects and containment use). Add one more watcher: if
`gPlayerState.heldObject == 4` and `carriedEntity` is a `SHOP_ITEM` that
belongs to the quest (its `type` is the quest's item), write
`carry_item = type` and let the engine delete the prop as it always does.
A prop that is NOT the quest's (a shop purchase, a fountain offering) is
left alone, so nothing else changes.

**Rebuild on arrival.** On the first settled frame in the new room
(`QuickStartRoomSettled`, the test every dispatcher uses), if
`carry_item != 0`: spawn the prop at the player's feet with
`QuickStartSpawnShopItem`, then run exactly the five lines
`ItemForSale_Action1` runs on a lift - `PausePlayer()`,
`ResetActiveItems()`, `heldObject = 4`, `carriedEntity = prop`,
`gHUD.rActionPlayerState = R_ACTION_DROP` - and clear the token. The
player arrives already holding it, which is what "carrying across the
screen" should look like. Seam and door are the same case; the stash/
rebuild pair does not care which path deleted the prop.

**What a walk feels like.** While `heldObject` is set the sword, items,
roll and shield are off (`playerUtils.c` gates all of them on it), so a
carry through a region is a run past its enemies with no way to fight -
the quest's actual difficulty, for free. Two rules to add deliberately:
a hit drops it (watch `gPlayerEntity.base.iframes` go nonzero while
carrying: null the carry and leave the prop on the floor where the player
stands, so it can be picked back up), and shrinking drops it (vanilla
already does; the Minish hole into the ranch house is a legitimate
shortcut only for an empty-handed player).

### 1.3 The quest shape

Same skeleton as the three quests that exist (hunt, scavenger, stealth -
`QuickStartRandomizeQuestOnce` picks a kind and a host region and the
monitor for that kind runs in the host):

1. **The giver** stands in the host region on a surveyed spot - a
   ZELDA-faced or cast-faced talkable NPC, the way the fountain's asking
   sprite is made. Talk: "Bring me the X from <region>." Region, not room,
   same rule as the chain hints.
2. **The prop** is placed in an *adjacent* region (`sQuickStartRegionAdjacency`
   - the fuser scatter already walks it) at one of that region's reward
   spots, by the region monitor, idempotent by position. It sits there
   until lifted. Adjacent, so the carry is one or two screens of enemies,
   not a tour.
3. **Delivery** is the fountain's test moved to the giver: carrying the
   quest prop within the giver's interact box resolves the quest -
   delete the prop, clear the carry, pay the reward through
   `InitItemGetSequence` (forced, the way chain rewards are now), set
   `GF_QUEST_DONE` so the chain's QUEST step sees it.
4. **Failure** is the carry rules above: dropped by a hit, it lies where it
   fell; walk off the screen without it and it is deleted like any loose
   prop - and respawned at its origin spot by the placing monitor, since
   the quest is not done. No softlock, and no need for a timer.

**Chain and economy.** The quest kind goes into the existing QUEST roll; a
chain QUEST step already means "finish the run's quest", so it hangs a win
step on a carry with no new chain kind. Reward from the quest table like
the others. Hints: one Ezlo line for the giver, one for the compass.

### 1.4 Costs and risks

* **GFX:** the prop is one `SHOP_ITEM` on an item sheet the room may or
  may not already hold (one slot), and the giver is one NPC face (shared
  with the room's fusers when it wears the cast face). Same budget as a
  fuser plus a strewn offering, which the fountain room already pays.
* **Entity:** one, plus the one the rebuild makes for a frame.
* **Save:** one byte.
* **The one thing to measure first:** whether the vanilla seam and door
  transitions *fire* while `heldObject == 4`. The probe that tried to walk
  out of the ranch house carrying a prop did not leave the room; the
  harness has been wrong about that room's doorways twice today, so it is
  not evidence either way. If carrying really does block the border walk,
  the stash has to run on the frame the border would have fired - the
  containment hook sees that frame - and release the player for the walk.
  This is a one-probe question and decides nothing about the design, only
  where the stash line sits.
* **Vanilla fixtures to keep clear of:** shop rooms set
  `gRoomVars.shopItemType`, and `sub_080819B4` keeps a prop alive instead
  of deleting it when that is set; the quest prop must never be dropped
  inside the hub shop. Trivial to guard (the hub is already excluded from
  every monitor).

---

## 2. A feature testbed

### 2.1 What exists today, and why it is not enough

| lever | what it isolates | its limit |
|---|---|---|
| `make quickstart-testkit` | the kit (sword, bombs, spin) | nothing else |
| `make quickstart-d3` | the difficulty floor | one number |
| `make mapexplore` | walking the world | no mode content at all |
| `seed.py pin` | a whole run, replayed | you still have to walk to the thing |
| `emu.py` + `callrom.py` | any room, any function | Python only - not something to play |

Everything a run deals is a pure function of `gSave.run_seed` and a small
amount of save state: a ? room's kind is `QuickStartContentSiteRoll(seed,
site)`, the drop region is `QuickStartRollElementRegionOnce`, the quest is
`QuickStartRandomizeQuestOnce`, a region boss is a 10% roll in
`QuickStartSpawnRegionWave` (or forced by the BOSS carrier), the chain is
`QuickStartChainRollStep`. That is the good news: every one of those is a
single function with a single place to put an override.

### 2.2 The design: a scenario in the save file

**A scenario is four bytes of save state** that the run-start code reads
before it does anything else. Proposed layout in `filler38`:

```
/*0x38*/ u8 scenario_kind;   // 0 = none (a normal run); else QS_SCN_*
/*0x39*/ u8 scenario_a;      // meaning per kind (see below)
/*0x3a*/ u8 scenario_b;
/*0x3b*/ u8 scenario_c;
/*0x3c*/ u8 scenario_kit;    // 0 = hub picks as normal; 1 = the test kit; 2 = everything
/*0x3d*/ u8 scenario_diff;   // 0 = the build's floor; else this difficulty
/*0x3e*/ u8 carry_item;      // §1
/*0x3f*/ u8 spare;
```

Kinds, each naming the override it needs and the room it lands the player
in:

| kind | a | b | c | lands in | override |
|---|---|---|---|---|---|
| `SITE` | site index | event kind | extra | the site's room, at its arrival | `QuickStartContentSiteRoll` returns (b, c) for site a |
| `BOSS` | pool row | boss form | - | the region's drop spot | `QuickStartSpawnRegionWave` deals the boss on wave 0 |
| `QUEST` | quest kind | pool row | - | the host region | `QuickStartRandomizeQuestOnce` takes (a, b) |
| `CHAIN` | kind | where | detail | the drop region | step 0 pre-dealt as (a, b, c) |
| `REGION` | pool row | wave count | - | the region | plain arrival, waves from b |
| `FUSER` | spot room | face id | - | that room | the cast draw returns b |
| `ROOM` | area | room | - | (a, b) at vanilla arrival | nothing - for charms, keys, doors |

**At run start** (`GameTask_Transition`, the QUICKSTART branch - the one
at line ~1353, not the MAPEXPLORE one after it), with a scenario set: the
hub is marked finished (`QuickStartHubSetPhase(10)`), the kit is granted
per `scenario_kit` (the TESTKIT block already knows how), the difficulty
written per `scenario_diff`, the drop region rolled to the scenario's
region and `GF_ELEMENT_REGION_ROLLED` set, and `player_status` pointed at
the landing room instead of the hub. The player boots into the thing.

**The override points** are each one `if`: the four functions in §2.1 ask
`QuickStartScenario(kind)` first and take the forced values when it
answers. Every other system - waves, fusers, drops, containment - runs
unmodified, which is what makes the test honest: it is the real feature
in the real room with everything else live, only the dice are loaded.

**Persistence:** the scenario stays set until cleared, so soft reset
replays the same test; the reset path that bumps the run counter leaves it
alone. Clearing it is the same tool that set it.

### 2.3 Setting a scenario: two front doors

**From outside, with a tool - the one to build first.** `seed.py` already
writes a pin and a seed into a `.sav` file by offset; `scenario.py` does the
same for the eight bytes:

```
python3 tools/quickstart/scenario.py site  ROOM_CAVES_BOOMERANG WAVES 5
python3 tools/quickstart/scenario.py boss  ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS OCTOROK
python3 tools/quickstart/scenario.py quest STEALTH ROOM_HYRULE_FIELD_LON_LON_RANCH
python3 tools/quickstart/scenario.py chain EVENT 27 --kit test --diff 8
python3 tools/quickstart/scenario.py room  AREA_ROYAL_VALLEY ROOM_ROYAL_VALLEY_MAIN
python3 tools/quickstart/scenario.py clear
python3 tools/quickstart/scenario.py list      # every site, kind, region, quest, face by name
```

It resolves names through `parse_tables.py` (which already knows the site
table, the pool, the kinds), writes `tmc.sav`, and prints what it wrote.
Load the ROM with that save on the emulator or the cart and the run boots
into the scenario. No rebuild - the three-to-six-minute build is the thing
this avoids. `list` is the catalogue: the whole surface of the game,
enumerated, which is also the checklist for "every little thing".

**From inside, with a console - the second step.** A ZELDA-faced "test
console" NPC in the hub spawn room, built only under a `QUICKSTART_TESTBED`
define so the shipped game never shows it. The text engine can print a
number into a line (`\x06\x01` reads `gMessage.rupees`; the difficulty HUD
and the scav score use it already), so the console can say "Scenario kind
[1] a [27] b [3] c [5]" and the Select-with-nobody-near idiom that opens
the chain hint can be reused for "next field / next value": each talk
advances one field, L and R move the value, and leaving the hub through
the hole launches it. The whole picker is one script and one custom
string. It is worse than the tool for choosing among 105 sites by number,
which is why the tool comes first and the console second - but it is what
makes a test possible on a cart with nothing but a cable.

### 2.4 What this buys the harness

Every existing probe sets up its state by hand - warp, write flags, call
a function. With the scenario in the save, a probe becomes "write eight
bytes, boot, play": `invariant_check.py` can run a per-site matrix (every
site x every kind it can deal, 105 x 8) against the real spawn path
instead of calling the spawner directly, and a failing scenario is
reproducible by anyone with the same eight bytes. The `scenario.py`
catalogue doubles as the list of what the matrix covers.

### 2.5 Cost and order of work

1. The save fields and the run-start branch (hub skip, kit, difficulty,
   landing). Small; everything else hangs off it. Measure: boot with a
   `ROOM` scenario, land in the room.
2. `scenario.py` with `list` and `room`. The catalogue is worth having on
   its own.
3. The four override `if`s, one kind at a time, each with a probe that
   boots the scenario and reads the result (the site kind from the roll,
   the boss entity in the room, the quest flags, the chain step).
4. The in-hub console, last, behind `QUICKSTART_TESTBED`.

Nothing here touches the shipped game's behaviour when `scenario_kind` is
0, which it is on every save the game has ever written.
