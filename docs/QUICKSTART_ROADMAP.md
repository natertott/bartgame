# QUICKSTART Roadmap

Rewritten against the code as it actually stands. The previous version of
this document described an architecture the code left behind ~30 commits
ago - most of what runs today (the vanilla-door "? room" model, the 2-door
pool, the relocated shop, the gated-zone table) was not in it at all.

## 1. The vision (as agreed, in full)

A roguelite inside the vanilla Minish Cap world. Each run: an item-selection
phase, then out into the overworld to explore, power up, and collect the
run's required objectives; heavy randomization around a small mandatory
spine; LOTS of optional ? events.

**The meta loop is the game.** Early save-file: limited item variety,
limited regions, limited ? event kinds, capped difficulty - room to learn
the vocabulary. Aggregated score across runs crosses benchmarks that
unlock: new items, new powerups, new ? event kinds, new quests, new
regions. Wins raise difficulty AND lengthen the run: the region chain grows
from 2 toward the cap of 5 total (the start region plus up to 4 element
regions, each holding its own element the player must find inside it).

**Kinstones are the key economy.** Enemies drop kinstone pieces; fusing at
a gated door opens a new ? room for the rest of the run. Every region also
keeps a set of always-open doors so some ? events are reachable no matter
what. The economy tightens as difficulty rises: abundant drops early,
grind-worthy scarcity later.

**The overworld keeps its vanilla layout**; the randomization lives behind
the doors - which room a door leads to (the 2-door pool model, now on
sound footing) and what happens inside it (the event kinds). Same map every
run, different world behind it.

## 2. Guiding principle for this phase

**Depth before breadth.** The pool stays at its current five overworld
regions until a full playthrough is smooth and bug-free. Every problem
solved between now and then should be solved with a *general mechanism*,
not a per-room special case, so that adding regions later is mostly data
entry.

The systems that already work this way, and are the model to follow:

- `sQuickStartRoomContentSites` - a table row per room, not code per room.
- `sQuickStartGatedZones` - a table of item-gated boxes, consulted by one
  generic position filter, usable by anything that places something.
- `QuickStartRegion` - a table row per region, driven by generic chain code.
  One rule the table cannot express and nothing checks: a region's exit box
  must lie **inside** the room's own pixel bounds, and off the outermost
  pixel row so it beats the real border transition. Lon Lon Ranch's sat past
  the bottom edge of a 720x960 room for as long as the chain has existed.
- `QsCheckRoomFlag`/`QsSetRoomFlag` - one private flag window, so no room's
  vanilla logic can collide with ours.

Every per-room special case still in the file (`QuickStartClearNorthFieldScrub`,
`QuickStartLonLonRanchQuirkHook`, the Melari East/Southeast bespoke
dispatchers) is a candidate for folding into a table as the same need
appears a second time.

## 3. Current architecture

### 3.1 Run flow

```
Wind Tribe Tower F3   item choice, 3 rounds (key item / rare reward / skill)
        |             then the phase machine parks at 10 - no combat here
        | stairs down (vanilla, F3 -> F2 -> F1 -> Entrance)
        v
Tower Entrance        walk out the front door (its solid tiles are cleared)
        |
   Cloud Tops         the wind crest, and the pit in front of it
        | pit fall, redirected by QuickStartProcessHubHoleLink
        v
   DROP REGION        one of the 11 pool rooms, drawn per run; the same
        |             every fall within a run. From here the player WALKS
        |             the seven-region ring freely (sec 3.2)
        v
   any region         endless escalating waves everywhere; each region's
        |             wave-0 clear drops its one-time reward - except the
        |             run's drawn ELEMENT REGION, whose wave-0 clear drops
        v             the EARTH ELEMENT ("it's SOMEWHERE - go find it")
      win: difficulty +1, score -> meta_xp, save, soft reset
```

The hub is Home of the Wind Tribe - see `docs/QUICKSTART_HUB.md` for the
survey, the build order and what is still to do (shop on Floor 1, roof wave,
inn on Floor 2, wind crest data).

**Castor Darknut and Melari's Mine are retired.** Castor Darknut's waves,
heart-piece chest and links are deleted outright. Melari's Mine keeps all its
own content (reward, enemies, three side rooms, the Southwest content site)
but is off the route and off `QuickStartAreaContained`'s list - which is what
walls Castle Garden's south border, since that border still points at the mine
from when the mine was the hub. The area comes back when the region pool
grows.

**Every per-run draw is rolled unconditionally** from `QuickStartRoomMonitor`
(region chain, ladders, doors, 2-door, river bridge, cave, Melari rooms,
shop), each latched by its own `GF_*_RANDOMIZED` flag - they used to hang off
the old hub room's dispatch, which stopped being safe when that room left the
route.

### 3.2 Regions

**The overworld is a seven-region ring now** (the overworld expansion):
Castle Garden, North Hyrule Field, Lon Lon Ranch, Eastern Hills (3 rooms),
South Hyrule Field, Western Wood (3 rooms), and Trilby Highlands circle the
missing Hyrule Town. Travel between them is free and vanilla-shaped - every
seam and border between two ring rooms works exactly as vanilla built it.
Two synthetic "town bridge" borders stitch the gap the town leaves (NHF
south <-> SHF north; LLR west <-> Trilby east), each landing at the exact
coordinates vanilla's own town exits delivered a through-traveler to.
Every border OUT of the ring (Veil Falls, Lake Hylia, Minish Woods, Castor
Wilds, Royal Valley, Mt Crenel) is compiled away under QUICKSTART - walking
that edge just stops. The old per-run warp boxes between regions
(`QuickStartProcessRegionChainLinks`) are retired.

Ring facts a maintainer needs (all emulator-verified, `tools/quickstart/ring.py`):
- SHF's east seam opens into Eastern Hills **North**, not South - the south
  rooms' west edges are vanilla walls. SHF's west edge is fully walled too:
  Western Wood is entered from Trilby, through WW-North.
- The ring's walking order: CG - NHF - (bridge) - SHF - EH-N - {EH-C - EH-S}
  - LLR - (bridge) - Trilby - WW-N - WW-C - WW-S.
- Containment collapsed to one rule: any transition between two ring rooms
  passes (`QuickStartIsRingCrossing`); pockets/? rooms keep their own
  allowances; everything else cancels as a safety net behind the data-level
  blocks.

`sQuickStartRegionPool` - **11 rows now**: Castle Garden, Lon Lon Ranch,
South Hyrule Field, North Hyrule Field, Trilby Highlands, plus the
overworld expansion's six - Eastern Hills South/Center/North and Western
Wood South/Center/North. Each row carries its entrance, its (retired)
"onward" exit box, an enemy-offset grid, room size/enemy cap, a reward
spot, and an optional quirk hook. The six new rows were surveyed with the
same live-collision flood as the original three field regions (offsets
farthest-point sampled over open 3x3 neighbourhoods; act tile 0x9 - plain
grass - verified on every reward spot); Eastern Hills North's grid uses
only its main walkable component, not the small SHF-seam pocket.

Their six real doors are content sites now (the farm house, the Eastern
Hills cave, the Western Wood heart-piece tree, Percy's house, and the two
Minish houses - the last two pulled OUT of the drawn small-room pool so a
walk-in room is never also a teleport target).

**Kinstone fusers are live in the new regions too.** The audit found nine
vanilla fusions whose world events land in EH/WW rooms; seven are wired
as fusers (EH-North: KINSTONE_16 and the golden-enemy KINSTONE_55;
WW-Center: KINSTONE_3D; WW-North: KINSTONE_11/21/3A/48/4C - the ring's
densest fusion room). The two BEANSTALK fusions (KINSTONE_2E in
EH-Center, KINSTONE_24 in WW-South) are deliberately NOT offered: a
beanstalk's payoff is climbing out of the ring to the cloud rooms, which
containment cancels, and a fusion that grows an unusable ladder reads as
a bug. Scatter spots for the three hosting rooms were generated with the
region's enemy grid, gates, entrance and reward spot seeded as taken, so
a fuser can never stand on a wave spawn point or the reward drop.
With this, the new regions are at full feature parity with the original
five.

**The ordered chain is retired.** The run is a free-roam hunt now, per the
user: "the Earth Element is SOMEWHERE. Go find it." Every pool region is
live every run - endless escalating waves, a one-time reward on the first
wave clear, quests - and ONE region drops the Earth Element in place of
its normal reward. Entering that region fires the Ezlo "the Earth Element
is here!" hint (`GF_REGION_FINAL_HINT_SHOWN`, kept from the chain era);
the run's intro hint fires in whichever region is entered first.

**Where the pit drops you, and where the element hides**
(`QuickStartRollElementRegionOnce`, both latched per run): the hub's Cloud
Tops pit lands in a DROP REGION drawn uniformly over the 11 pool rooms
(`GF_DROP_REGION_BIT` 467-470, rolled-latch 466) - the same room on every
fall within a run, rerolled between runs
(`QuickStartProcessHubHoleLink` reads it). The element region is then
drawn by rejection so it lies within TWO named regions of the drop, where
"named region" collapses the 11 pool rooms to the seven ring names
(`QuickStartRingRegionOfPoolIndex`) and distance is counted on the ring's
adjacency map (`sQuickStartRingAdjacency`: map edges plus the two town
bridges, so NHF touches LLR and Trilby). The user's worked example, which
the tables reproduce exactly: land in Castle Garden and the element can be
in CG (0 away), NHF (1), or LLR / SHF / Trilby (2) - never EH or WW (3).
Verified over 8 seeds (`tools/quickstart/freeroam.py` plus a pit-fall
probe): drop varies, every element draw is within distance 2, every pit
fall lands in the drawn room.

Consequences: the two REGION unlock rules (Lon Lon at 1 win, Trilby at 2)
are retired - a freely walkable region cannot be locked - and so is the
Zora Flippers force-Trilby-last routing. Per-region state is keyed by POOL
INDEX in the QS window now (`GF_REGION_WAVE_BIT` 362-457,
`GF_REGION_REWARD_STATE_BIT` 338-361, element draw 332-336, quest/hunt
host region 458-465, all sized for 12 regions); the old bank-11 wave
counters (142-173) and chain flags (208-228) are free.

Within a region: wave 0 is a plain tiered group; every wave after it has a
20% chance of being a solo Chuchu Boss instead - but ONLY in Castle Garden,
North Hyrule Field and South Hyrule Field (`QuickStartRegionAllowsBoss`).
The small rooms cannot host the boss (it locked the game up scrolling into
Eastern Hills South), and the rest of the ring is paused-not-vetted, so
it's an allowlist: a region gets bosses when someone has watched one work
there. The roll's `Random()` consume is unconditional so the RNG stream
does not depend on where the player is standing. Wave count persists per
slot across leaving and returning (`FLAG_BANK_11`). The boss is beatable without
the Gust Jar - conventional weapons peel the jelly as well as the gust stream
does (`sub_08027AA4`, chuchuBoss.c) - which is what lets the Gust Jar be an
ordinary drop rather than a boot grant.

### 3.3 "? rooms" - three distinct systems

1. **Content sites** (`sQuickStartRoomContentSites`, 27 rows) - the primary
   model. A real vanilla room, entered through its own real vanilla door,
   with a randomized event placed inside it. Rooms can hold several events
   (the Boomerang chamber holds five, one per entrance).
2. **2-door pool** (7 small + 13 large rooms) - rooms reached through a
   synthetic connector that puts the same room behind both of two doors.
   Fed by Lon Lon Ranch's cave mouth, North Hyrule Field's river bridge, and
   North Hyrule Field's cave mouth, each with its own independent draw.
3. **Drawn-door slots** - the original mechanism (once literal ladders in
   Castle Garden, which is where the retired `LADDER_*` naming came from),
   now down to Castle Garden's northwest door, which redirects to a drawn
   single-door room. Named `QuickStartSlot*` / `GF_SLOT_*` since the
   cleanup pass; the entrance table and its trigger are deleted.

All three converge on `QuickStartSetupEventContent`, which places one of
**seven kinds** (`QS_EVENT_*`): item drop, miniboss, NPC, 3-wave gauntlet,
pot lottery, chest lottery, fairy room. Note the item-drop kind places a
GROUND_ITEM, not a chest - it was called "chest" for a long time and never
was one. A content site names which set it may roll:
`QUICKSTART_KINDS_SMALL` (chest/NPC/both lotteries) for cramped tree hollows
and cave nooks, `QUICKSTART_KINDS_LARGE` (miniboss/waves/fairy) for rooms
with floor space, and `QUICKSTART_KINDS_ANY` for rooms big and clear enough
to host anything. A room being large was never a reason to stop it rolling a
pot lottery; it was only ever a reason to stop a cramped one rolling a
miniboss, which is what ANY exists to say.

Three of the sites are **Minish-gated**: the cave at (376,216) and the tiny
door at (72,456) in South Hyrule Field, and Castle Garden's northeast wall
hole. Every region has a vanilla Minish portal hidden under a tree stump,
and the stump only opens on a Pegasus Boots dash into the tree (vanilla's
own PLAYER_BOUNCE reveal - the old force-reveal is gone per the user's
call), so Minish content is what a boots run buys, the same way Trilby
Highlands is what a Flippers run buys.

Every one of these rooms is swept on entry: vanilla enemies, NPCs, and
payout-shaped objects (ground items, both chest kinds, heart containers,
fairies) are deleted, so the event *is* the room's reward rather than a
bonus on top of vanilla's.

### 3.3b Every run was the same run

`gRand` is set to the literal `0x1234567` in `AgbMain` (`src/main.c`) and never
touched again, and `DoSoftReset` - how a won run starts the next one - goes
back through `AgbMain`. Every per-run draw compounds it: they are all rolled
unconditionally from `QuickStartRoomMonitor`, which first runs on frame ONE,
before the player has pressed anything, so `QuickStartStirRandom` (one extra
`Random()` per input frame) has had nothing to stir.

Result: same region chain, same shop, same prices, same "? room" contents,
every single run. Reported by the user as "the same items every time" in the
shop; the shop was just where it showed.

`GameTask_Transition` now reseeds per run from a persistent 6-bit counter
(flag bits 178-183, in the gap between `GF_DIFFICULTY_BIT` and the 184-201
clear loop) plus the previous run's length and kill counts, then stirs. The
counter is committed with a `WriteSaveFile` at run start, without which it
does not survive: `gSave` lives in EWRAM but `InitSaveData` reloads it from
SRAM on every boot. Verified across four consecutive soft resets: four
different `gRand` values and four different shop stock lists.

The first run on a brand-new save is still fixed - nothing has happened yet to
vary it - which is fine.

### 3.3c The hub's three selection rounds

Floor 3 offers three items, three times. Each round now **draws from the tier
table** (`QuickStartSpawnChoiceRow`), where all three used to be hardcoded
arrays:

| Round | Categories | Tiers | Pool size on a fresh run |
|---|---|---|---|
| 1 | `QS_CAT_KEY` | any | 8 |
| 2 | `QS_CAT_REWARD \| QS_CAT_STAT` | rare only | 6 |
| 3 | `QS_CAT_SKILL` | rare excluded | 6 |

Round 1's array had listed **5 of the table's 9** key items, so the Cane of
Pacci, the Grip Ring and the Power Bracelets could never open a run; the 9th,
the Ocarina of Wind, is granted at boot and so is filtered out by
`QuickStartTierEntryUsable` like any other item already owned. Rounds 2 and 3
were not randomized at all - the same heart container / 100 rupees / red
potion and the same three skills, every run.

All four bottled entries in round 2's band (the fairy and the three charms)
need an empty bottle, which the boot grant already provides
(`gSave.stats.bottles[0] = 0x20`), so the full 6 are live from the first run.
`QuickStartSpawnChoiceRow` still widens to every tier of the same categories
if a band cannot fill three slots, but nothing reaches that path today.

**How a round detects the choice changed with it.** The old check scanned the
inventory for the three items it had offered; nothing persists which three are
drawn now, and the pickup is not uniformly observable anyway (a rupee goes to
the wallet, a charm into a bottle). Detection is now "an item left the row" -
`QuickStartChoiceRowRemaining` counts ground items at the three row
coordinates. That fires several frames EARLIER than the old check, on the
frame the vanilla item-get cutscene starts rather than when `GiveItem` runs, so
the next phase additionally waits on `QuickStartItemGetCutsceneRunning`;
without it, tearing the row down and reloading the room would cancel the
pickup the player just made.

`tools/quickstart/hub_rounds.py` is the regression probe: per seed it prints
each round's drawn set and then, on a fresh boot per item, walks onto that item
and checks the round actually advanced.

### 3.4 The shop

**Floor 1 of the hub**, one flight up from the tower entrance - walked to,
not drawn. **Eight** shelf slots in two rows across the upper hall, the
permanent four nearest the player at y=120 and the run's four one-off wares
behind them at y=88, with a walkway between at y=104 and the merchant at its
east end.

| slot | stock | price |
|---|---|---|
| 0 | recovery heart | rolled per run in [1, 100] |
| 1 | ten arrows *(needs the Bow)* | rolled per run in [1, 100] |
| 2 | ten bombs *(needs Bombs)* | rolled per run in [1, 100] |
| 3 | heart piece | **50, +25 per purchase this run** |
| 4 | one KEY ITEM | rolled per run in [1, 500] |
| 5 | one WEAPON/TOOL | rolled per run in [1, 500] |
| 6 | one REWARD | rolled per run in [1, 500] |
| 7 | one SKILL **or** STAT upgrade | rolled per run in [1, 500] |

Slots 0-3 are **permanent and repeatable** - buy them as often as the rupees
last. Slots 4-7 are drawn once per run from `sQuickStartShopPool` (37 rows,
every tier) and can be bought **once each**; the slot then stands empty for
the rest of the run, tracked by `GF_SHOP_SLOT_SOLD_BIT` because several of
them are repeatable items that a usability test alone would happily restock.

The draw is by rejection so nothing appears twice, and eligibility is
`QuickStartTierEntryUsable` - the same test every other draw uses. That test
is re-applied at *display* time too, which is what makes the shelf tidy
itself in both directions: buy the Pegasus Boots elsewhere and the slot goes
bare, and buy the Bow at slot 5 and the arrows at slot 1 stock themselves.

Prices are **absolute amounts** now, not the old `(4 + roll) / 8` scale on the
vanilla table. A multiplier cannot hit a stated range, and half this shelf
(the recovery heart, the butterflies, the charms) has a vanilla price of zero
to scale in the first place.

The pool stays separate from `sQuickStartTiers`, but for a narrower reason
than before: an item is only sellable with a confirm-purchase message id in
`gItemMetaData`, and 17 of these have none. Rather than write 17 QUICKSTART
overrides into that table, `GetSaleItemConfirmMessageID` (`src/itemUtils.c`)
now falls back to one generic line for anything `QuickStartGetShopPrice` is
pricing. What the pool table is still *for* is leaving out what the shop
should not sell: rupees (paying rupees for rupees), the heart piece (its own
slot), and the boot-granted Ocarina.

Every spot is emulator-verified liftable (`invariant_check.py`'s `hub` tier
presses R and reads `gPlayerState.heldObject`, rather than reasoning from the
collision map - which is what made the previous layout take four attempts;
re-spacing the eight evenly was tried and that tier caught one of the new
offsets spawning stock that would not lift). `tools/quickstart/shop.py` prints
the run's stock and prices and can drive a real purchase end to end.

It used to be a "? room": first in the Grimblade dojo behind a fixed link,
then in Stockwell's store reached by redirecting one of eight candidate
overworld doors drawn per run. That retired two standing problems with it -
the drawn door's own "? room" event was displaced for that run, and three of
the nine catalog spots sat on a shelf in a sealed Minish-only pocket.

### 3.4a Getting back to the hub: the Ocarina of Wind

Granted at boot, and it goes to exactly one place: the wind crest outside the
Home of the Wind Tribe (`gUnk_08128024` row 2, Cloud Tops at (488,424), which
is where the WINDCREST object stands). The crest-picking map is skipped -
`Subtask_FastTravel_0` jumps straight to state 4 under QUICKSTART, the state
vanilla reaches after a confirmed pick, so the ocarina animation, the bird
that carries the player off, the fade and the arrival bird are all vanilla and
all still play.

No tier-table change was needed: `QuickStartTierEntryUsable` already refuses
non-repeatable items the player owns, so a granted ocarina stops being
drawable on its own.

### 3.4b The hub's roof

Optional content, one flight above the item selection. One wave at the run's
difficulty + 2, from 14 hand-placed offsets inside the roof's measured
reachable component; clearing it drops a REWARD-category item, RARE one time
in four and UNCOMMON otherwise. The reward drops ONCE per run: any revisit
that finds the spot empty in state 1 promotes straight to "done" (the old
re-drop arm could not tell "left it behind" from "grabbed it on the way
out", which paid a second copy - the state-1 comment in
`QuickStartRoofMonitor` has the full story). Leaving mid-fight and
returning still gives a fresh wave. The roof's vanilla `BIG_VORTEX` (the
Palace of Winds warp) is deleted on entry by `QuickStartClearHubRoom` -
the roof leads nowhere but back down the stairs.

### 3.5 Win condition

The run's element region drops the Earth Element at its reward spot once
wave 0 is clear. Picking it up runs: vanilla's item-get message, then "You win!
Difficulty increased", then "Run score", then `WriteSaveFile` and
`DoSoftReset`.

Robustness measures now in place:
- The Element's despawn timer is refreshed every frame, and the win check
  runs every frame, not only while the room is clear.
- The win message waits for vanilla's own get-message to start *and* finish.
- `QuickStartRescueStuckFinalWave` pulls any survivor to the reward spot if
  the Element-gating wave is still alive after 90 seconds, so an enemy the
  player cannot reach can no longer end a run.

### 3.6 Reachability and gating

`sQuickStartGatedZones` - boxes in room-local coordinates, each with a
required item (or "never"). Nothing gets placed inside a box whose item the
player lacks. Populated from the user's own hand-walked coordinates; the
emulator walk-flood harness (`scratchpad/reach_audit.py`) is a cross-check,
not the source of truth.

### 3.7 Storage

- Bank 12 is effectively QUICKSTART's whole address space: `gAreaMetadata`
  gives `LOCAL_BANK_12` only to the eight Royal Crypt areas, which this mode
  never enters. Its 1408 bits are laid out as:

  | raw offset | what |
  |---|---|
  | 0 | unusable - `SetLocalFlagByBank` is `if (flag != 0)`, so vanilla reserves offset 0 in every bank |
  | 1-793 | the room-keyed content sites, 13 bits each, room for **61**. `QsCheckSiteFlag`/`QsSetSiteFlag` |
  | 794-800 | spare |
  | 801-1407 | the QUICKSTART window, i.e. `QsCheckFlag` offsets 101-707 |

  Offsets 101-703 in the window are cleared per run, plus the whole site
  block; `GF_DIFFICULTY_BIT` (174-177) deliberately is not. Adding a content
  site is now **one table row and nothing else** - the block grows downward
  into its own reserved space instead of shoving the bridge/shop/Melari
  flags along in front of it, and a compile-time assertion stops the build
  if it ever reaches the window. Raw 1-585 is space reclaimed from
  `GF_DOOR_*`, 15 synthetic door entrances retired long ago whose 286 bits
  were never given back - that dead block is why the site table was stuck at
  30 and a 31st was impossible.

  Getting this wrong used to be silent: at 25 sites the smithy's block began
  at exactly 578, which was the bridge flag, so throwing the bridge lever
  also gave the smithy an all-zero roll and entering the smithy joined the
  bridge. The checker's `flags` tier now expands every `GF_*` define over its
  declared parameter range and asserts no bit is claimed twice, nothing sits
  at offset 0, nothing overruns its bank, and every per-run bit is actually
  covered by a run-start clear loop. It found two live bugs the moment it
  was written: chain slot 0's wave counter was based at bank-11 offset 0 (so
  it could only ever hold even wave numbers), and the pot quest's block was
  never cleared between runs (so it was pinned to its first-ever roll, and
  vanished for good once completed).
- Room flags: `gRoomVars.flags` from offset **256**, `QsCheckRoomFlag` and
  friends. This window exists because vanilla uses the low bits and *does*
  clear them out from under us - the cause of the Triple Darknut room
  spawning content once per frame until the entity table saturated.
- **Per-area local flags are wiped every run.** `gSave.flags` is one
  4096-bit array split into banks: bank 0 is the global flags (story
  progress, the entrances this mode forces open) and survives; everything
  from `FLAG_BANK_1` up to QUICKSTART's own block is per-area state, and
  that is where the world records bombed walls, smashed tiles, opened
  chests, revealed portals and kinstone fusions. Vanilla wants those
  permanent; a roguelite does not, so `GameTask_Transition` clears the whole
  range. A wall the last run blew open is whole again.
- `gSave`: `run_frames`, `final_wave_frame`, `enemies_killed`,
  `miniboss_kills`, `boss_kills` (per run); `meta_xp`, `runs_completed`
  (persistent).

## 4. The plan: five phases, each shippable

Reconciled with the full vision. Ordering principle: build the RAILS that
make polish cheap first, then the META LAYER that is the vision's spine,
then spend everything else on content breadth - because once the rails and
the meta layer exist, content is data entry into unlock-gated tables, which
is exactly the "universal method" being asked for.

What the vision needs that already exists (verified, not hoped):
- Item selection phase: built (Wind Tribe Tower Floor 3, 3 rounds).
- Region chain: built; length is one constant, and the flag layout already
  reserves per-slot state for 4 slots ("just a bigger CHAIN_LENGTH", per
  the layout comment at GF_REGION_CHAIN_*).
- Persistent score: `meta_xp` and `runs_completed` accumulate in the save
  and survive the soft reset. Benchmarks have storage waiting.
- Difficulty counter: built, feeds enemy tiers.
- ? events: 7 kinds, 3 delivery systems, 46 rooms measured
  (QUICKSTART_ROOM_SURVEY.md).
- World reset per run: built (local-flag wipe) - bombable walls, portals
  and future kinstone fusions all re-arm by construction.
- Both-direction 2-door doors: built (tag mechanism, QUICKSTART_2DOOR_MAP.md).

### Phase A - Rails (short; do before anything else)

The recurring failure class this project has actually had is hand-placed
data being wrong (exit boxes, content spots, entrances, shelf items - six
systems). The cure each time was measuring at runtime. Phase A turns that
cure into a standing tool instead of a per-incident scramble.

- **A1. The invariant checker.** DONE - `tools/quickstart/invariant_check.py`
  (see `tools/quickstart/README.md`). Three tiers: static (door tags, pool
  size constants), regions (entrance/reward/exit-box geometry, 5 boots),
  rooms (~45 boots: landing, spot openness/segment membership, forced
  chest spawns). Multi-site rooms are held to one-distinct-segment-per-site.
  Full run green: 0 FAIL, 4 WARN (Castle Garden path tiles, two edge-
  clipped exit boxes, the shadowed cellar). Run it after every build that
  touches placement data; it is the regression gate.
- **A2. Burn down the survey's open findings.** Shop right-shelf Minish
  check: DONE (finding 5b - the alcove really is Minish-only, and the fix
  was the shelf's front row, reachable from the lower room; all nine items
  verified liftable). Still open: the cellar shadowing decision and the Lon
  Lon Minish doors.
- **A3. Deterministic playtest switch.** DONE - `gSave.run_seed` (the old
  `filler4c`, save.h) plus `GF_SEED_PINNED` (bank 11 offset 174, outside
  every run-start wipe, for the same reason the difficulty counter is) and
  `tools/quickstart/seed.py`.

  The seed is RECORDED on every run whether or not anyone armed anything,
  which is the half that makes a player's report reproducible: the value is
  in their .sav, and `seed.py show --sav` reads it without booting. Setting
  the pin makes the next run reuse that value verbatim instead of deriving a
  fresh one; one field does both jobs. `seed.py check` is the self-test -
  same seed reproduces the run (shop stock AND fuser scatter identical), a
  different seed changes it.

  The pin never has to reach SRAM. Within one boot the order is: AgbMain
  sets gRand, InitSaveData loads gSave from SRAM, then GameTask_Transition
  reads the pin - so EWRAM between those two points is enough, and a soft
  reset would actively destroy it (the reset reloads gSave from SRAM). The
  harness therefore rewrites pin+seed on every frame of the title sequence
  rather than guessing which frame the load lands on.

  The finding that came with it, and it narrows what every green checker run
  has ever meant: **a harness boot has no .sav behind it, so it always
  derives the SAME seed.** The emulator tiers have only ever exercised one
  run's worth of drawn content. `invariant_check.py --seed N` fixes that -
  it is how a seed-dependent placement bug (a shop draw in an awkward spot, a
  fuser scatter that lands badly) gets found rather than waited for.

### Phase B - The meta layer (the vision's spine)

- **B1. Unlock registry.** DONE - `sQuickStartUnlockRules` +
  `QuickStartIsUnlocked()` in game.c, thresholds on meta_xp (pot lottery
  500, chest lottery 1500) and runs_completed (fairy 1, Lon Lon Ranch 1,
  Trilby Highlands 2). Consulted by the kind pick functions (locked draws
  degrade to CHEST/WAVES) and the region chain draw (locked pool rows
  rejected; Trilby's Flippers-forced-last path also requires its unlock).
  New content still ships as a table row plus a rule row. Shop catalog and
  reward pools stay ungated for now - add rows there when there's content
  worth gating.
- **B2. Chain length scales with wins.** DONE - `QuickStartRegionChainLength()`
  = 2 + 1 per win, capped at `QUICKSTART_REGION_CHAIN_MAX` (4). Verified
  in the emulator at 0/1/2 wins: slot distinctness, locked-region
  exclusion, and Trilby forced last only with Flippers + unlock. The 5th
  region ("start + 4, each with its own element") waits on B3's per-region
  elements.
- **B3. Per-region elements.** RESHAPED by the free-roam rework: there is
  no chain and no gated onward exits anymore, so "each slot's element
  un-gates its exit" no longer describes anything. What survives of the
  idea is *element variety* - more than one element per run, or different
  elements as different event payouts - which now lives in F7
  (win-condition variety). Element theming per region remains a content
  decision - see Decisions.
- **B4. Unlocks viewer** (research task #52) so the player can see the
  progression the whole design hangs on.

### Phase C - The kinstone economy

- **C1. DONE.** Vanilla's death-drop roll (`CreateRandomItemDrop`,
  itemUtils.c). Note the sentinel: a `Droptable` field of **-999** means
  "never", and `SumDropProbabilities2` clamps negatives to zero, so an
  additive weight bump can never escape it - kinstone weights are
  *assigned*, not added.
- **C2. DONE.** Difficulty-scaled piece weights:
  `63 - difficulty * 4`, floored at 21, on red/blue/green alike. Two cuts
  from the original 180/-10/60 after play-testing: 30% off (126/-7/42)
  because collecting every piece a run needed was no real challenge, then
  halved again after the overworld expansion - seven regions' worth of
  waves made the right fusions too easy to hit. The proper drop-curve
  analysis is still future work; both cuts are flat.
- **C3. DONE.** Not a new table after all - the gates already exist. Vanilla
  wires 91 fusions to world events (staircases drawn over water, tree
  canopies, cracked walls, treasure chests); 29 of them fire in a room this
  mode visits, and `tools/quickstart/kinstone_audit.py` derives that list
  from the ROM rather than a survey. 18 that open a gate or place a chest
  have a fuser placed in the same overworld map (`sQuickStartFusers`,
  positions proposed by `find_fuser_spots.py`, verified by the checker's
  fusers tier). The fuser reuses `AddInteractableObject` with our own
  kinstone id, bypassing vanilla's ROM-table-driven `GetFusionToOffer`
  entirely; `script_QuickStartFuser` drives the fuse state machine.
  `gSave.kinstones` is wiped per run, so gates re-lock and the bag empties.
  Castle Garden's two fountain chambers became content sites in the same
  change - they are what its two staircase fusions now open.

  One wrinkle worth remembering: vanilla applies a fusion's world event to
  the LIVE room only on room load (`sub_080186EC`, room.c). The cutscene
  runs against an auxiliary copy, so the player watched a staircase appear
  and came back to a room that still did not have one - it only landed the
  next time they walked in. Re-applying the event by hand does not cover the
  whole class either: a type 4 or type 7 gate is "shut" because tiles were
  PAINTED OVER the room at load time, and nothing in vanilla erases them.
  `QuickStartReloadRoomAfterFusion` re-enters the room once instead, latched
  on a 7-bit "already reloaded for this fusion" id
  (`GF_FUSION_RELOADED_ID_BIT`) so it fires exactly once, and gated on the
  player having control back so it cannot interleave with the cutscene.

  The world-event cutscene is kept - it pans to the door and shows it open,
  which is the payoff - but the local map hint vanilla chases it with is
  skipped (`Subtask_WorldEvent_End`, QUICKSTART branch). In a mode whose
  whole map is five rooms the player already knows, a second full-screen
  interruption saying where on the map that door was is just a pause.

  Fusers do not stand next to their gates. Each region has nine scatter
  spots (`sQuickStartFuserSpots`), farthest-point sampled over its reachable
  open tiles by `find_fuser_spots.py` with the entrance, the reward drop and
  every gate seeded as taken, so the set covers the whole walkable map and no
  two spots are within six tiles. A single 4-bit per-run roll
  (`GF_FUSER_SCATTER_BIT`) plus a step of 4 through the list of 9 - coprime,
  so no two fusers in a region can collide - places all eighteen without
  storing eighteen positions.
- **C4. The curve**: piece specificity by difficulty tier. Drop rate is
  done (C2); what is left is which shapes are obtainable when. Today every
  gate's shape maps to exactly one droppable piece id (0x6E-0x75), so a run
  can in principle stall on one unlucky shape - measure before tuning.

### Phase D - Content breadth (all unlock-gated, all data entry once B1 lands)

New events assembled from proven vanilla parts, cheapest first:

- *Cheap (mechanisms already proven in this codebase)*: lever-opens-path
  rooms (HittableLever + the bridge's donor-tile fill); bombable-wall
  treasure rooms (walls reset every run now); pot-room variants (timed
  prize, gauntlet-then-lottery); boss-rush rooms (sequential roster
  minibosses); survive-N-seconds wave rooms.

  **Switch-puzzle room designs (sketched with the user, Aug 2026)** -
  new QS_EVENT_SWITCH_* kinds in the existing content framework; state
  in room flags, reward through the standard once-latch, objects at
  surveyed spots with their own checker tier. The rule the F7 pause
  taught applies from day one: general-pool rooms must be solvable with
  sword+shield alone; gated variants wait for the key-item logic and
  then become drawn-only-when-guaranteed. In pilot order:
  1. *The closing gate* - **DONE (Aug 2026).** `QS_EVENT_GATE` (kind 7,
     filling the site table's 3-bit kind field) in the LARGE pool at 25%
     and ANY at 12.5%. The prize (standard tier draw) sits at the site's
     content spot behind a 3x3 ring of eight primed trap pots; a
     HittableLever spawns near the room entrance; Ezlo says "Strike the
     lever, then RUN for the prize!". Any lever flip opens the cage and
     arms a 10-bit QS-window countdown (`GF_GATE_TIMER_BIT` 486-495) of
     480 − difficulty×20 frames (floor 240); at zero the cage re-closes
     around whatever the player didn't grab. Two pivots worth
     remembering: (a) the original tile-painted shutter had working
     collision but was *invisible* in interior rooms - wall art lives on
     a different BG layer than the sampled tile type - so the cage
     became trap-pot entities, which carry their own sprites and render
     everywhere (and, being liftable at a price, can never jail the
     player); (b) a pot stamps SPECIAL_TILE_0 collision over its tile at
     init and only restores the saved original through its own
     lift/break paths, so the gate's open path must `SetTile` the saved
     index (entity offset 0x70) back before `DeleteEntity`, or the ring
     tiles stay phantom-solid and the re-close finds no room to spawn.
     Probe-verified end to end: cage 8/8 on arrival, lever strike arms
     the clock and opens the ring, prize collectable, lapse re-closes.
  2. *The decoy lever* - **DONE (Aug 2026), revised per the user: NO
     eye-switch tell - a total gamble.** Three identical levers dealt
     prize/trap/dud blind. Shares `QS_EVENT_GATE` with the closing gate
     (the 3-bit kind field is full) via a per-visit coin flip stored in
     room flag +1; re-entering may deal the other puzzle, which suits a
     gamble room since all state rebuilds per visit anyway. The deal is
     one of the six permutations, stamped lever-by-lever into entity
     `type2` (hittableLever.c never touches it; bit 0x80 marks a
     resolved pull so re-flipping a spent lever is inert) - entity
     storage because the site's room-flag window had only 3 free bits,
     not enough for a permutation plus per-lever state. Prize lever:
     cage opens permanently, no countdown. Trap lever: the cage
     machinery aimed at the *player* - a ring of primed trap pots
     around their feet (lift one and eat the blast, or hope for a
     gap), with the menu-error sting. Dud: the lever's own clack and
     nothing else. Probe-verified all four resolutions plus the
     closing-gate regression (coin flip left puzzle #1 intact).
  3. *Hold everything down* - 2-3 pressure plates depressed at once:
     player on one, thrown/pushed weights on the rest; the room holds
     exactly enough pots, and one plate is throw-only across a gap.
  4. *Watch the eyes* - eye switches blink a sequence; hit them in
     order (sword adjacency keeps it kit-free); wrong order resets, and
     at high difficulty an F1c stake bites.
  5. *The burning wick* (HELD until key-item logic) - light all torches
     before the first burns out; fire-gated, and deliberately the first
     client of the "drawn only when the kit is guaranteed" rule.
  6. *Overworld switch links* (ambitious) - a plate in one ring region
     opens a grate in another, reusing the proven NHF bridge machinery;
     the free-roam ring becomes the puzzle box, and the compass gets
     something to point at.
- *Medium (one new mechanism each)*: kill-quota bounties per region
  (kill counters exist; needs a quest NPC handout); carry-item-to-NPC
  quests (the shop's carry-to-merchant flow, pointed across rooms);
  Great Fairy fountain gamble (GREAT_FAIRIES rooms + script reuse);
  Mole Mitts dig rooms (DIG_CAVES areas exist and are surveyed
  candidates); Minish-layer ? rooms beyond SHF's two.
- *Hard (new AI or heavy scripting - defer)*: escort/herding events,
  bespoke new enemy behaviours, fully new scripted questlines.

### Phase D1 - Overworld fixes the user reported, still open

Done: the boomerang-cave ladder flag, the stuck-wave rescue, and Lon Lon's
shallow-water staircase (below). These are not:

**DONE - Lon Lon Ranch's shallow-water cave.** The Kinstone fusion revealed the
staircase, the player walked down, and the cave's only exit put them in Castle
Garden - which is what "leads nowhere, just warps back to the overworld" was.
The exit had been retargeted at Castle Garden Main, the shared landing spot of
the old "? room" pool, but the room was never added to that pool, so the
retarget was all cost and no benefit. Exit back on vanilla, and the room is a
content site now.

That site REPLACES the Hyrule Castle Cellar one rather than being a 31st. The
comment on `QUICKSTART_CONTENT_SITE_COUNT` claims a site of headroom; that was
true when written, before `GF_FUSION_RELOADED_ID_BIT` and
`GF_FUSER_SCATTER_ROLLED` took 692-703 against a ceiling of 707. The cellar
slot was dead twice over - unreachable behind the Castle Garden northwest
ladder's redirect, and its content spot was `y=376` in a room 192 tall - so
reclaiming its 13 bits closes two open bugs and costs nothing.

- **DONE - Lon Lon Ranch: the Goron cave's kinstone progression.** Four
  stages, verified, and reachable in play.

  The room is a 240x720 vertical shaft that vanilla cuts into chambers with
  `sub_StateChange_GoronCave_Main`: five kinstone fusions, only THREE of
  which paint a wall open. Measured reachable tiles per state: 36, +51
  (KINSTONE_25), +0 (2A), +89 (26), +0 (2B), +60 (2F). So the room supports
  four sealed chambers, not the eight stages first sketched - 2A and 2B buy
  no floor. Per the user's call the chain is four stages, strictly one per
  chamber: a free `?` roll, then three minibosses paying COMMON, UNCOMMON
  and RARE off the shared tier table. Each row is gated on the fusion that
  opens its own chamber (new `gateKinstone` field), and the payout comes
  from a new `rewardTier` field.

  The three wall fusions are offered by fusers in Lon Lon Ranch - in vanilla
  the wall-punching Gorons offer them, but they are NPCs and every content
  site room sweeps its vanilla NPCs, so nothing in this mode offered them
  and the chain could not be advanced at all. KINSTONE_2A and 2B were
  briefly listed alongside them and have been dropped: neither opens a wall,
  the Gorons they add are swept anyway, so in play they were fusions that
  did nothing while each consumed a scatter spot. The ranch is at 6 of its 9
  spots now rather than 8, which matters because KINSTONE_29 alone decides
  whether the cave opens at all. Measured across four real runs: 3 distinct
  layouts, six non-colliding spots every time.

  Two real bugs surfaced in the shared miniboss code, both invisible until a
  room held more than one miniboss site, and both fixed with the Voronoi
  tile-ownership test the pot lottery already used:
  - the "is my miniboss dead" headcount counted every enemy in the room, so
    no stage paid out until every stage's fight was over, and then all four
    paid at once;
  - the leash that parks a not-yet-engaged miniboss on its spawn spot ran
    against every enemy in the room, so each frame all four sites yanked all
    four fights to their own spot in turn. Last writer won and the whole
    cave's minibosses ended up stacked on one tile. Measured frame by frame:
    they spawn correctly at four distinct anchors and are collapsed onto one
    the very next frame.

  **Enterable - and the earlier "unreachable" verdict here was wrong twice
  over, both times because of the measurement, not the game.**

  The real blocker was the overworld gate, and the user found it in play:
  "there is still an invisible barrier where the Goron stood".
  `sub_StateChange_HyruleField_LonLonRanch` paints two blocking tiles over
  the cave mouth AND spawns the wall-punching Goron in front of them, both
  only while KINSTONE_29 is unfused - one gate, lifted by one fusion. This
  mode deleted the Goron NPC but could not delete the tiles, so the barrier
  stayed with nothing standing in front of it. That deletion was a leftover:
  it made sense while the mode also fused KINSTONE_29 at boot, and that
  boot-time fuse was removed when KINSTONE_29 became a real fuser in C3.
  Only the deletion and four stale comments survived it. The Goron stays
  now, and fusing KINSTONE_29 at its fuser opens the cave with the vanilla
  punch-through cutscene.

  The second error was the stairs room's inner door, reported here as
  sitting on a solid tile and never firing. It fires - the trigger is at the
  FOOT of the staircase fixture, and standing anywhere in (112-128, 72-80)
  opens the main chamber at once. Two bad probes hid it: walking up the
  middle column stalls at y=101, which is where this room's own content site
  drops its reward, and the pickup's message box blocks all input (the trap
  this project has now been caught by three times); walking up a side column
  instead overshoots to the top row and passes above the trigger.

  Verified end to end with real input: ranch -> fuse KINSTONE_29 -> cave
  stairs -> main chamber. No position box needed.

  The reported symptom - "the west door does not fire" - was ours, not
  vanilla's. All three are driven by the same mechanism: `SpecialWarpManager`
  (manager subtype 6, room property 8) walks the garden's three exit regions
  every frame and calls `DoExitTransition` for whichever one a MINISH-sized
  player is standing in. The three regions are symmetric in the room data.
  What differed was containment: `QuickStartEnforceContainment` cancels any
  transition leaving Castle Garden unless the destination is a pocket
  interior, and the pocket interior set IS the content-site table. The east
  hole was in the table, so it opened; the other two were cancelled on the
  frame they fired, which in play is indistinguishable from a dead door.
  Wiring content and opening the door are the same act here.

  Measured before/after against two builds: east OPEN / west CANCELLED /
  crack CANCELLED, then all three OPEN.

  Kinds: east stays ELITE (guaranteed level-5 miniboss, heart container).
  West is ANY - identical 80-tile footprint, but a second guaranteed
  miniboss in one region reads as a farm. The crack is SMALL: 31 reachable
  tiles in three narrow passages, the smallest hosting room in the game. All
  seven kinds were driven in both rooms; the pot lottery fits 23 pots in the
  crack, since it already scales its fill to the open-tile count.

  No vanilla chest needed sweeping in the end - the generic
  `QuickStartClearVanillaRoomContent` pass every site room runs already
  covers chests, and the only vanilla occupant left anywhere in the three was
  the crack's Minish NPC, which it deletes. The crack's four FURNITURE props
  are scenery and deliberately stay.

### Phase D2 - Queued, in the user's own priority order

Named work, deferred deliberately rather than not yet thought about:

- **The hub's inn (Floor 2).** `docs/QUICKSTART_HUB.md` §3.2 and §6 step 6.
  Three beds at 50 / 200 / 500 rupees healing 25% / 50% / 100% (minimum 1 / 2
  hearts / full), and the chests between them holding nothing / a COMMON
  REWARD / an UNCOMMON REWARD, never rare. Paused at the user's request in
  favour of overworld fixes; it is the only genuinely new mechanic left in the
  hub, and the only one with an open question (whether Floor 2's
  `SPECIAL_CHEST` objects can be filled, or whether the contents have to be
  ground items on the same tiles like every other reward in this mode).
- **Persistent living-enemy count.** Today a wave is re-spawned whole every
  time the region room loads, so killing 10 of 20, stepping into a "? room"
  and stepping back out puts all 20 back. That makes leaving mid-wave a
  punishment and effectively forbids using a "? room" during a fight. What is
  wanted: the count of enemies *still alive* survives leaving the area, and
  only resets to the wave maximum when a wave is actually wiped. Storage
  exists for it (the region chain already keeps a per-slot wave counter in
  FLAG_BANK_11); the work is in the spawner, which currently keys off "is the
  room empty" rather than off a remembered count.
- **More hints, drawn per run.** Superseded by F5 below, which carries the
  current thinking.

### Phase E - World breadth

Largely landed: Eastern Hills and Western Wood joined the pool with the
overworld expansion (six new rows, surveys, fusers, quests - see 3.2), so
"adding a region = table row + survey + checker pass" is now demonstrated
routine. What remains under this heading: regions beyond the ring (Castor
Wilds, Royal Valley - both currently blocked borders, so adding one means
un-blocking an edge and extending containment), and the Minish layer as a
parallel network (tasks #102/#103 - the transform rendering bug blocks it).

### Phase F - Expansion topics (user, Aug 2026)

Each entry carries its own speculated implementation path; the cross-item
sequencing lives in section 8.

- **F1. Overworld quests v2: the timed scavenger hunt. CARRIER MODE
  SHIPPED** - the Keaton chase (`QuickStartScav*`, game.c;
  `script_QuickStartScav.inc`). One giver NPC per run in a drawn region
  (never the hunt quest's own - the two share the HUD clock and the enemy
  mark bit, and guard each other's RUNNING state). Talking to it despawns
  the region's wave and releases a Keaton thief at the region's REWARD
  spot - across the map, so the chase crosses the region - plus a
  slow-you-down swarm around the giver (beetles for bodies, sparks for a
  positioning tax, ice wizzrobes for ranged pressure: instance-heavy,
  kind-light, the measured-cheap shape). Kill the Keaton inside 60
  seconds and a RARE prize drops at the giver's spot; run out and the
  pack scatters - one attempt per run. Leaving the region mid-chase
  pauses the clock and re-releases the pack on return (room flag 7 tells
  a reload apart from a kill). All three endings emulator-verified
  through the real NPC conversation. One lesson for every future spawner:
  a just-created enemy's health is 0 until its own init tick, so
  completion counters must count by mark, never by health.

  Still open from the F1 brief - the other two hide modes: buried
  (Mole Mitts) and under-bush items. Both need per-region tile surveys
  (diggable spots, cuttable bushes) before they can be drawn safely;
  the quest's mode field and state machine are ready for them.

  *Path:* this is the third sibling of two quests that already exist and
  prove every mechanism needed. The pot quest (`GF_QUEST_*`,
  `QuickStartSpawnQuestPots`) proves per-run host-region draw + hidden-index
  draw + "prize appears at a drawn spot"; the hunt quest (`GF_HUNT_*`,
  `QuickStartHuntMonitor`) proves a giver NPC, a 45-second frame timer
  (`QUICKSTART_HUNT_FRAMES`), a live enemy-group swap mid-room, and win/lose
  states in 2 bits. New pieces, in order of risk: (a) *buried* items - find
  vanilla's dig-spot mechanism (Mole Mitts digs fire a tile action; survey
  which act tiles in ring rooms are diggable, or paint our own the way the
  bridge's donor-tile fill paints tiles); (b) *under-bush* items - hook the
  grass-cut drop path (`CreateRandomItemDrop` is already ours in
  itemUtils.c; a per-run drawn tile in the host region overrides the roll
  with the quest item when cut); (c) *carrier enemy* - spawn one swarm
  member with a mark, hook its death the way wave-clear detection already
  watches enemy counts, drop the item where it died. The swarm itself is
  `QuickStartSpawnEnemyGroupAtDifficulty` with a bespoke roster table
  instead of the tier table, sized by the GFX heuristics (few DISTINCT
  kinds, many instances - instance count is nearly free, each new kind
  costs sheet slots). Despawn/restore of the normal wave is the hunt's
  existing swap. Drop-location scoping is the survey + checker pattern:
  buried/bush spots become table rows the invariant checker walks.

- **F1b. DONE (first pass) - quest dialogue quality bar.** The user's
  finding: current quest text is not enough for an inexperienced player to
  know what to do. The pass rewrote every line that failed that bar: the
  hunt offer now names the task and the 45-second limit, the handicap
  offer says the kit comes back, the loss line says the run's one attempt
  is spent; the pot quest - which had NO intro at all, pots just appeared -
  got a give line (custom string 26, latched once per run on
  `GF_REGION_QUEST_HINT`); and four chain-era lines that had become false
  under free-roam were corrected (the selection greeting's "your item
  picks your path", the intro hint, the region-clear hint - which now
  teaches "the Element is NOT here", the only useful fact that moment
  has - and hub hint 21's "final area"). Rule going forward: a quest ships
  with give/win/lose/reminder lines, and a playtester who has never seen
  the code reads them cold.

- **F1c. Difficulty-scaled failure stakes (user, Aug 2026).** Today,
  failing a quest costs only the missed reward. Wanted: as the run's
  difficulty climbs, failure starts to HURT - lose the Keaton and maybe
  you lose health, or an item is taken, or a previously acquired buff, or
  rupees. Explicitly cross-feature: the same stakes system should serve
  every timed-or-conditioned goal - the scavenger chase, the hunt, the
  wave gauntlet, the future stealth quest's spotted-out, and whatever F7
  hangs an element on.

  *Path:* one shared `QuickStartApplyFailureStake()` called from every
  quest's FAILED transition, rolling a punishment from a menu whose every
  entry already has working machinery: rupees (`ModRupees` - the trap
  ladder NPC already takes 100), health (the stat write every probe
  uses), a charm/buff (clear a `QUICKSTART_CHARM_BIT` - and later an F4
  status bit), an item (the handicap system already knows how to take
  and track items; a stake is the same take without the give-back).
  Scale by `QuickStartGetDifficulty()`: nothing at low difficulty (the
  learning runs stay kind), rupees at mid, health/buff at high, item
  loss reserved for the top tiers. Two design rules carried over from
  the curse work and F1b: the stakes are ANNOUNCED in the offer text at
  the difficulties where they apply ("fail me and I take something" -
  the player chose the gamble), and the failure text SAYS what was
  taken, never leaves it to be discovered. The scavenger hunt's FAILED
  branch is the natural pilot site.

- **F2. Hide-and-seek (stealth) quest.** Borrow vanilla's
  dodge-the-guards mechanic: cross a space without entering guard line of
  sight; spotted = warped back to the start. Our version bounds it with a
  timer or a fixed number of tries.

  *Path:* research-first. Vanilla's implementation lives with the Hyrule
  Castle sneak sequence - find the guard entity's LOS check and its
  "spotted" handler (the warp-back is a scripted transition we would
  retarget at our own start tile). Two open questions decide feasibility:
  whether the guard AI runs outside its scripted vanilla room (precedent
  says yes - most entities run anywhere if spawned with the right sheet
  loaded), and whether LOS reads room-specific data. If the vanilla AI
  transplants, the quest is: pick a host room (interior ? rooms are better
  than open overworld - LOS in a 1008-wide field is meaningless), place
  guards on patrol rows from a table, gate a prize behind the far side.
  If it does not transplant, fake it: ZELDA-kind NPCs on patrol paths +
  a cone check in our own monitor (we already run per-frame monitors), and
  our own warp-back. Either way the fail budget (tries/timer) is 2-3 bits
  of QS-window state next to the other quests'.

- **F3. More vanilla bosses; DONE for the Electric (blue) Chuchu.** The
  boss roll now flips a fair coin per spawn: CHUCHU_BOSS type 0 (green)
  or type 4 (blue/electric). What the experiment actually found, since
  the type mechanics were subtler than the theory:
  - The spawn type is a FORM, and the init consumes it: the base captures
    it into `type2` (0 green / 4 blue - the one reliable runtime marker;
    probes must read type2, not type, which ends up role-only) and the
    EnemyDefinition rows 0-3 vs 4-8 carry the two palette families.
  - The blue intro is Temple-of-Droplets STAGE machinery, not fight
    logic - it seizes the camera, waits on a player room-transition that
    never comes, and paints an arena tile at a hardcoded position. In an
    open region the pieces sat invisible at the spawn point forever.
    QUICKSTART routes both forms through the green intro; type2 keeps
    palettes, particles and moveset blue.
  - Two aftermath bugs bit BOTH forms and were latent in every boss kill
    to date: the invisible hitbox proxy (the type-8 spawn) is never felled
    by the core's death (vanilla's arena transition wiped it), leaving an
    immortal invisible enemy that blocked the wave loop - and once dead it
    ran ChuchuBoss_OnDeath (whose first act is PausePlayer) every frame
    forever, freezing the player for the rest of the run. The core's
    death completion now fells every family piece, and a dead piece with
    no living family deletes itself.
  Verified end to end (blue_chuchu_probe2): both forms spawn, assemble
  visibly (screenshots), die, the next wave arrives, and control returns.
  The electric contact damage rides the blue moveset unchanged; the
  sub_08027AA4 weapon-peel widening keys on contact flags, not form, so
  it covers both.

  Bosses beyond that (Gleerok, Mazaal, Big Octorok) each need: a damage
  audit, an arena audit (Mazaal is a multi-entity macro - MAZAAL_MACRO 55
  - and almost certainly wants a dedicated room, not an open field), and
  a budget measurement. Treat each as its own task; none are "just spawn
  it" - the blue chuchu, the CHEAPEST possible case, still surfaced three
  latent bugs.

- **F4. Charms and curses on the unused quest items.** Assign our own
  run-long status effects to vanilla's unused quest items (the books, the
  pies, the medals...). Receiving one announces its effect in dialogue and
  applies it for the rest of the run. Candidate effects the user named:
  player walk speed up/down, enemy speed up/down, enemy projectile rate
  up, elemental immunities (fire/ice/shock), drop-rate shifts, cheap-shop,
  rare-reward chance up, boss-spawn chance up/down.

  *Path:* the bottled charms (Nayru/Farore/Din) are the working precedent
  for every piece of this: granted through the tier table, latched into a
  per-run mask (`QUICKSTART_CHARM_BIT` -> `QuickStartCharmMask()`), read
  at the point of effect (`CalculateDamage`), suspended/restored around
  vanilla's own charm machinery. Generalize: one `QuickStartStatusMask()`
  over a block of QS-window bits (474-655 are free - 471 became the pot
  quest's give-line latch, 472-473 the roof fairy pots; ~16 effects fit
  easily), items enter the reward/? tier tables as ordinary rows with a
  new QS_CAT or reuse of QS_CAT_STAT, and the pickup path fires a custom
  text (the item-get message hook already exists for the win sequence).
  Each effect is then one read at one point, and the points all exist:
  walk speed (the Pegasus Boots / swiftness path sets player speed),
  enemy speed/projectile rate (enemy update reads per-kind constants - a
  global multiplier needs a shim at CreateEnemy or in the shared enemy
  tick), immunities (CalculateDamage, same as charms), drop rates
  (itemUtils.c QUICKSTART block already modifies the droptable), shop
  prices (the per-run price roll), boss chance
  (QUICKSTART_REGION_BOSS_WAVE_CHANCE becomes a function). Curses ride
  the same mask; the only design rule is that a curse must come attached
  to something the player chose to take (a cursed shop bargain, a cursed
  quest reward) so it reads as a gamble, not a gotcha. Start with the
  four cheapest reads (immunities, drop rate, shop, boss chance), ship,
  then do the speed family which needs the enemy-tick shim.

- **F5. More hub hints, drawn per run.** (Supersedes the D2 entry.) The
  hint table (`sQuickStartHubHints`) is six fixed rows, one per spot.
  Wanted: a pool much larger than the spot count, drawn per run, so every
  run teaches something. *Path:* exactly the shop-stock shape: keep the
  six spots, grow the script pool (each hint is a script pointing at a
  custom text - writing more is data entry), and add a per-run draw
  (6 draws without replacement from N; a few QS-window bits per spot,
  or re-derive from the run seed the way fuser scatter does with zero
  storage). The hint CONTENT should lean on what tests keep proving
  players miss: the quests' rules, the kinstone economy, charm/curse
  gambles, the distance-2 element rule.

- **F6. Boss + wave combinations (research).** What can run alongside a
  boss within 72 entities / 44 GFX slots, and which combos are fun?
  Candidates named: Electric Chuchu + fire/ice wizzrobes; BOMB_PEAHAT
  (27) raining bombs during any boss; sparks orbiting the arena. *Path:*
  this is measurement first, opinion second. Extend
  `tools/quickstart/measure_budget.py` to spawn boss + roster
  combinations at difficulty 8-12 and report peak entity and GFX use, the
  same way the WW-N failure was diagnosed. The cost model to verify: a
  boss is a multi-entity macro (green chuchu = core + 3 jelly + helper),
  each DISTINCT enemy kind costs sheet slots, instances are cheap.
  Combos that share sheets with the boss (more chuchus during a chuchu
  boss) will measure cheapest; wizzrobes carry projectile sheets that
  load ungated (the WW-N lesson), so wizzrobe combos need headroom. The
  interesting-first shortlist to measure: blue chuchu + ice wizzrobes
  (thematic, shared palette family), any boss + 2 bomb peahats (indirect
  pressure that doesn't crowd the melee), any boss + sparks (pure
  positioning tax, sparks are cheap singles). Ship as: a per-boss
  "escort roster" field in the boss roll, gated by measured budget.
  Multi-boss (user question): measured - two bosses fit a CLEARED room
  comfortably, three are marginal, none fit on a live diff-12 wave
  (QUICKSTART_BUDGET.md finding 3). Blocked on family-scoping the boss
  death machinery first: a simultaneous dual kill currently softlocks,
  because the staged death cutscene and the QUICKSTART death sweeps
  assume one family per room.

- **F7. Win-condition variety: PAUSED (user, Aug 2026) - the KEY ITEM
  reachability logic comes first.** The stopping reason, in the user's
  own terms: some ? rooms are still unreachable to the player at the
  current moment, and no event may carry the win until the run can
  GUARANTEE the player is able to reach it. The wave clears are (almost)
  always guaranteed to work - so they stay the sole carrier until then.
  The prerequisite is its own piece of design work: the key-item logic -
  which items gate which content, and how a run proves "this goal is
  reachable with the kit this player can actually obtain" before hanging
  the element on it.

  Design banked from the paused implementation attempt (reverted cleanly,
  nothing shipped), for whenever this resumes:
  - a per-run 2-bit CARRIER draw (wave / boss / quest / ? room) rolled
    with the element region, each carrier restricting the element draw to
    regions where it can pay out (boss -> the CG/NHF/SHF allowlist -
    every ring's within-two set was checked to contain one; ? room -> a
    hand-curated table of UNGATED walk-in sites, one per ring, with Lon
    Lon Ranch excluded because all its interiors are gated);
  - BOSS carrier: every post-0 wave in the element region is the forced
    boss until beaten; the drop gate is the wave counter reaching 2, so
    a boss that fails to spawn still counts up and the run self-heals;
  - QUEST carrier: the pot quest forced to the element region with the
    Element in the hidden pot - no fail state, pots respawn per visit
    until the Element is in hand;
  - a global per-frame Element ground-item despawn refresh, so the item
    survives wherever a carrier drops it (pot, interior, field);
  - per-carrier Ezlo final-hint variants, so "it's here!" never lies
    about HOW ("a BOSS guards it" / "hides in a pot" / "behind a door").
  Every carrier resumed later must clear the same bar the pause names:
  a "cannot stall the run" argument (the way
  QuickStartRescueStuckFinalWave covers waves) AND a "provably reachable
  with the guaranteed kit" argument from the key-item logic.

- **F8. The full vanilla sweep + the budget audit.** Two standing research
  deliverables: (a) a catalog of ALL vanilla content re-purposable for
  this mode - enemies, NPCs, scripts, minigames, rooms, objects, items,
  cutscene machinery - so content planning draws from an inventory
  instead of memory; (b) a RAM/VRAM/GFX/entity budget analysis.

  **(b)'s measurement half is DONE - see `docs/QUICKSTART_BUDGET.md`**
  for the tools (the measurement mailbox in game.c, measure_budget.py's
  combo mode, gfx_trace.py, cpu_probe.py's lag ratio) and the first
  measured findings: the tightest rooms sit at 5-7 free GFX slots at
  difficulty 12; waves chain themselves and accumulate sheets past the
  per-wave kind cap; a boss+wizzrobe escort on a live diff-12 wave fills
  the table to 0 and the boss fails to spawn; the reaper frees a dead
  sheet after a median 11 SECONDS; and CPU never lags for normal
  content - only gang AIs (the acro class) ever moved the ratio.
  **(a) and the EWRAM audit are DONE too - see
  `docs/QUICKSTART_VANILLA_INVENTORY.md`**: every enemy graded with its
  roster status (A in-use / B drop-in / C needs-audit / D arena-bound /
  X excluded), the NPC/object/item/area/system toolboxes, the boss
  ladder (Octorok Boss is the next-cheapest after the chuchus), and the
  EWRAM map. EWRAM headlines: ~31 KB simply free at the top,
  gDungeonMap is 28 KB of dead state that is ALSO the pause-map's own
  buffer (so F10 repurposes it rather than reclaiming it), and RAM is
  not the scarce resource - the GFX table remains the wall. The
  cheapest unexploited content per the grades: the golden-enemy trio
  (KINSTONE_55 is wired with no payoff today), the switch-puzzle object
  vocabulary, FLYING_POT ambushes, CUCCO_AGGR as an F1c stake, and
  WIZZROBE_WIND completing the wizzrobe family. With this F8 is
  complete.

- **F10. The MAP and COMPASS items (user, Aug 2026).** Two findable
  items, listed under rare WEAPONS/TOOLS in the tier table. Today the
  player has NO overworld map at all - the START screen's map feature is
  not even active in this mode. The MAP item activates it, showing ONLY
  the regions visited so far this run. The COMPASS re-appropriates
  vanilla's unclaimed-fusion-treasure map icon, inverted: it marks every
  kinstone fusion NOT yet fused, and the icon clears when the player
  enters the unlocked room / claims the reward. The compass also marks
  WHICH REGION holds the Earth Element - the region only, never the spot,
  so it sharpens the hunt without ending it.

  *Path, in dependency order:*
  1. *Research spike first* - why the START-screen map is inactive here
     (story-flag gating? the pause menu screen set?), how vanilla decides
     map visibility per area (there is per-area visited state in the
     save), and where vanilla's fusion-treasure icons come from (the
     gKinstoneWorldEvents -> gWorldEvents chain the kinstone audit
     already reads has the coordinates; the icon renderer is what needs
     finding). The pause menu is vanilla UI code this mode has touched
     only lightly (the L-slot work) - budget the spike accordingly.
  2. *Items*: vanilla's dungeon MAP and COMPASS item ids already exist
     with icons and pickup plumbing - repurpose them rather than minting
     new ids, and add them as rare WEAPON/TOOL tier rows (the unlock
     registry can gate them later if wanted).
  3. *MAP half*: a per-run visited-regions bitfield (11 bits, QS window
     486+, set where the intro-hint path already detects first entry) and
     a pause-map draw filter: no item = screen stays inactive; item =
     visited regions drawn, unvisited masked.
  4. *COMPASS half*: draw icons at each unfused fuser's host-region map
     position (sQuickStartFusers x kinstone-fused state, all readable),
     clear per the user's rule (room entered / reward claimed - the
     fusion-reload latch and site-claimed flags already know); plus a
     region-level marker over QuickStartElementRegionIndex()'s region.
  5. Checker tier: every icon's map position lands inside its region's
     rectangle; map masks exactly the unvisited set.

- **F9. DONE - cap simultaneous Acro-Bandits.** The user's report: 3-4 on
  screen visibly tanks the frame rate. Confirmed mechanism: ACRO_BANDIT
  (46) is a GANG - the placed leader bursts into FIVE more of itself when
  its pop-up animation finishes (acroBandits.c, Type0Action5), so each
  placement is eventually six live entities of a heavy per-frame AI, and
  the slowdown is CPU, not GFX. The cap
  (`QuickStartAcroBanditCapReached`): a placement is allowed only while
  fewer than 2 acros are live, checked at all three of our spawn edges -
  the multi-kind group spawner substitutes a kind the wave already loaded
  (or skips), the single-kind open-tile placer stops, and the two
  single-pick callers (3-wave rooms, the hunt pack) trade a capped pick
  for a beetle so an empty spawn can't read as an instant clear. Vanilla's
  own follower spawns are untouched - capping a gang mid-burst would leave
  a half-formed formation. The same guard pattern belongs on any future
  gang/macro kind that reaches the tier table.

## 5. Known open bugs and loose ends

Full per-room measurements (walkability grids, components, entity headroom,
special tiles, vanilla contents) live in `docs/QUICKSTART_ROOM_SURVEY.md`.

- **DONE - switch-puzzle cage walled the dojo shut + phantom prize in the
  ante room (user-reported, Aug 2026).** Two independent defects, both
  reproduced via the real ante-room -> seam -> dojo path:
  1. The dojo site's content spot (0x78,0x88) sat two tiles from the seam
     mouth, so the gate's 3x3 pot cage walled the room's only entrance
     (measured: 0px of progress). Fixed three ways: the spot moved to the
     arena center (0x78,0x58); `QuickStartGateClose` refuses cage tiles in
     the room's outer THREE rows/columns (doors and their approach
     corridors live there - in a room too cramped for clearance the cage
     comes out with a gap, the safe failure); and both variants' levers
     (solid, collidable fixtures) now spawn from an anchor clamped 3 tiles
     inboard (`QuickStartClampInboard`) with the same outer-band rejection,
     because the decoy deal had put its middle lever on the seam
     corridor's own column - the same lockout by other means.
  2. The phantom prize: mid-scroll through the dojo seam there are frames
     where `gRoomControls.room` already names the dojo while the origin
     still points at the ante screen (they flip mid-frame), and the
     content-site dispatcher ran in that window - every room-local
     coordinate wrong - re-dropping the prize INTO the ante room, partial
     pot cage and all, free to take without touching the lever.
     `QuickStartSetupContentSite` now refuses to run unless the room is
     settled (`reload_flags == 0 && scrollAction == 1`, measured as the
     settled state in every room class). Two adjacent holes closed with
     it: the prize carries ENT_PERSIST and scroll-seam re-entries don't
     clear it while per-visit room flags do reset, so both the gate and
     the plain item-drop inits now ADOPT an item already sitting on the
     spot instead of stacking a duplicate.
  Probe-verified end to end: entry never blocked (player crosses the
  lever row's open flank into the arena), a mid-puzzle round trip to the
  ante room yields zero items there and exactly one prize total, re-entry
  keeps one prize and a full cage, and the gate cycle (strike, open,
  take) works at the new center spot.

- **DONE - boss "started spawning", camera swung between the spawn and the
  player, black screen + freeze crossing back toward Trilby
  (user-reported, Aug 2026, save file attached).** Root cause, reproduced
  end to end in the emulator: `QuickStartEnforceGfxReserve` (the GFX
  trimmer) had no boss exclusion, and the boss - spawned at the region
  reward spot, far from wherever the player walked in - is exactly the
  FARTHEST enemy that trimmer hunts. Whenever the boss family (measured
  cost: 14 GFX slots) plus a live fill pushed free slots below the
  reserve with more than 10 enemies alive, the trimmer ate the family one
  piece per 64-frame pass (measured 5 -> 0 in 320 frames), mid-intro.
  A bare-deleted intro core strands `gRoomControls.camera_target` on a
  cleared entity slot reading position (0,0): the camera chases recycled
  slots and the void, at the intro's scrollSpeed of 1 - the swinging and
  the black screen. Four fixes, each independently verified:
  1. The trimmer refuses live boss pieces and the current camera target
     (setpieces are not density fill).
  2. The boss roll is gated on free-or-evictable GFX slots >= 16
     (`QUICKSTART_BOSS_SPAWN_MIN_GFX`; family costs 14) so a room that
     cannot afford a full 5-piece family deals a normal wave instead -
     partial families were the other latent failure (orphan pieces
     dereferencing dangling parent/child pointers).
  3. `QuickStartRescueDanglingCamera` in the room monitor: a camera
     following a cleared entity slot is handed back to the player at
     scroll speed 4. Armor for every seizure in the game, not just this
     one.
  4. The boss intro/death stopped being a CUTSCENE under QUICKSTART
     (chuchuBoss.c): no camera grab (the vanilla grab pans at 1 px/frame
     - ~900 frames each way across North Hyrule Field), no per-frame
     PausePlayer (~21 measured seconds of frozen player), no pause-menu
     lock; the spawn flash, particles, fall, shake and boss theme all
     stay, and the proxy's death-watch gained an orphan guard. Probes:
     full family under the gate, zero camera-not-player frames, player
     mobile through the intro, trimmer under pressure eats fill (12 -> 5
     beetles) while the boss keeps 5/5 pieces, clean death, clean seam
     exits mid-intro and mid-fight.

- **CORRECTED: item-drop "? rooms" are NOT empty.** An earlier entry here
  claimed 23 of 26 content-site rooms held no ground item. That was wrong,
  and the cause was the measuring tool, not the game: the probe read the
  entity `kind` field at offset +0 when it lives at **+8** (`id` is at +9,
  not +1). Reading +0 returns a field whose values are all multiples of 8, so
  the scan looked plausible, matched nothing anywhere, and reported every
  room as empty. `tools/quickstart/probe_content_rooms.py` with the correct
  offsets reports **26 OK / 0 EMPTY** - every item-drop site places its item.
  The invariant checker's own rooms tier had been saying so all along
  ("1 chest spawn(s) verified"); that contradiction should have been chased
  instead of explained away. `emu.entities()` now wraps the offsets so no
  probe has to know them.

  Two changes were made while chasing the phantom. Both stand on their own,
  but neither was fixing what it was said to be fixing:
  - Placed rewards are now covered by the ground-item timer refresh. The gap
    was real - `QuickStartRefreshItemTimers` was only ever called for the
    hub's item rows - but items evidently survived long enough regardless.
  - A vanished item no longer counts as a collected one unless the player is
    near where it was. Defensive and cheap; not a bug that was firing.

  **The user's report is still unexplained**: they have never seen an
  item-drop "? room" pay out. Since the items demonstrably spawn, the next
  thing to check is live play rather than a warp-in - and note the kind was
  called "chest" until the cleanup pass while only ever placing a ground
  item, so part of the report may be that a heart piece on the floor does not
  read as "a treasure chest room".

- **TODO: add the sword upgrades to the reward/item pools.** Only the Red
  Sword is reachable today, and only as a miniboss payout via `GiveItem` -
  `CreateObject(GROUND_ITEM, ITEM_RED_SWORD)` never creates an entity,
  because equipment has no ground-item form in vanilla. So putting sword
  upgrades in the tier table needs a grant path that is not a floor item:
  either a scripted pickup like the skill scrolls use, or a small "pedestal"
  NPC that hands the sword over on interaction. Applies to the Green, Blue
  and Four Sword as well as the Red.

- Lon Lon Ranch's two `MINISH_SIZED_ENTRANCE` objects at (316,632) and
  (436,632) are the ranch house's west and east Minish doors (the user's
  own identification). They lead into rooms that are already content sites,
  so they are a second route in rather than new ? rooms.
- No Minish-sized entrance exists anywhere else in Lon Lon Ranch's room
  data - the central "long hallway" the player expects after shrinking there
  has no entrance object in this room. Where vanilla puts that entrance is
  still unfound.
- **The 2-door pool's door transitions are wrong in both directions.** All
  40 doors (20 rooms x 2) are retargeted to one destination and one landing
  spot, so leaving by either door returns the player to the same overworld
  side and B -> A is impossible; entry teleports them to the middle of the
  room rather than to the matching door. Surveyed and planned in
  `docs/QUICKSTART_2DOOR_MAP.md`; the rewiring itself is not implemented.
- Trilby Highlands: one enemy offset, `(120,24)`, sits in an isolated
  north-west pocket. Not gated - the user paused Trilby zone-gating pending
  their own walk.
- Lon Lon Ranch: the top-middle pocket the user described has no walked box
  yet, so it is still unfenced.
- **DONE - roof pot fairies respawned every visit (user-reported).** One
  life each per run now: room flags record "this visit saw the pot
  standing", a later absence latches `GF_FAIRY_POT_BIT` (QS window
  472-473), and every later visit's respawn is deleted on sight
  (`QuickStartRoofFairyPotsOnce`). The two plain pots beside them stay
  vanilla. Verified: take the left pot, leave, return - it stays gone,
  the other three respawn.
- **DONE - ? room exits warped to the Castle Garden cellar ladder
  (user-reported).** Two stacked causes, both fixed:
  (1) three rooms promoted to walk-in content sites in the overworld
  expansion - the two Minish houses (EH-S, WW-S doors) and the Western
  Wood heart-piece tree - still carried their pool-era exit retargets to
  Castle Garden's shared ladder landing in transitions.c; restored to
  their vanilla exits (same treatment as the SouthHyruleField precedent).
  (2) underneath, `QuickStartIsPocketOverworldRoom` was still the
  pre-expansion five-room list, so a correctly-targeted exit into an
  EH/WW room would have been CANCELLED by containment - invisible while
  the retargets pointed at Castle Garden, surfaced the moment they were
  fixed. It now accepts every ring room. Verified: all three rooms exit
  to their real fields (EH-S / WW-S / WW-N).
- **Acro-Bandit slowdown (user-reported).** 3-4 on screen visibly slows
  the game. Suspected cause: each ACRO_BANDIT placement is a 5-entity gang
  (acroBandits.c spawns leader + four), so a few draws of the kind is 15+
  live heavy AIs - a CPU wall, not a GFX one, and other gang/macro kinds
  likely share it. Fix sketch and verification plan: Phase F9.
- **Inactive Minish hole, North Hyrule Field's very eastern edge
  (user-reported).** A small Minish hole there does nothing. Likely the
  same family as the Minish-layer blockers (tasks #102/#103 - transform
  rendering, portal wiring); check whether it is an unwired
  MINISH_SIZED_ENTRANCE like Lon Lon's ranch-house pair or a portal whose
  destination was never containment-blessed. Fold into the #102 survey.
- `POT_MINISH` does not render multi-enemy content (long-standing).
- Gentari's Room / Gentari's Main adjacency conflict (long-standing).
- Castle Garden Main's East and West Fountains are gated entrances not yet
  in any pool.
- The reachability harness crashes mgba after enough reboots; it now
  chunks its work across processes to survive that, but it is slow.

## 6. Testing doctrine (how we get polish without hand-engineering)

1. **Tables are the game; the checker validates the tables.** Every
   placement-bearing row (sites, exits, doors, spots, shop, kinstone doors)
   gets machine-checked per build (Phase A1). The six coordinate bugs this
   project has already paid for would all have been caught by it.
2. **Runtime self-correction stays on** (snap-to-open-ground everywhere) as
   the second line, so a bad row degrades instead of breaking.
3. **Measured docs are the source of truth for placement**:
   QUICKSTART_ROOM_SURVEY.md (rooms), QUICKSTART_2DOOR_MAP.md (doors).
   Guessed coordinates don't go into tables anymore.
4. **Humans test feel, machines test truth.** Emulator verifies state,
   spawns, transitions, persistence; playtests (with the A3 fixed seed)
   judge fairness, fun, pacing. Neither substitutes for the other.
5. **The decomp's hard limits, so plans stay honest**: 72 entities
   game-wide (measured per room in the survey); no new .bss/.data in
   game.o; VRAM/gfx-slots not directly measurable in the harness (one
   known failure class: POT_MINISH multi-enemy); new graphics/maps/AI are
   expensive, new LOGIC over existing assets is cheap - which is why the
   whole plan leans on recombination.

## 7. Decisions needed (content calls, not engineering)

1. Element theming: which element belongs to which region, and does the
   start region carry one?
2. Unlock benchmark values (first pass can be placeholder and tuned from
   real playthrough scores).
3. Kinstone specificity model: exact-piece matching vs. color-tier
   matching, and pieces-per-region counts.
4. Cellar site: exempt from the NW-ladder redirect, or retire.
5. Shop right shelf: Minish-only shelf (lean in) or move the trio.
6. Which Phase D cheap events to prototype first (one in front of a human
   before building more).

## 8. Implementation paths for the whole open backlog (speculative)

Phase F entries carry their own paths inline; this section covers
everything ELSE still open, then proposes one sequencing across all of it.
"Speculative" means: grounded in code that exists, but nothing here has
been prototyped unless it says so.

### 8.1 The standing backlog, item by item

- **B4 / task #52 - unlocks viewer.** The pause menu and the figurine
  gallery both prove full-screen owned UIs are possible, but a new screen
  is the expensive road. Cheap road: an NPC in the hub (ZELDA-kind, like
  every other QUICKSTART NPC) that speaks the unlock table -
  `sQuickStartUnlockRules` is data, so a script that walks it and prints
  "LOCKED (needs N wins)" / "UNLOCKED" lines into a custom text is pure
  data-to-dialogue. Ship the NPC first; only build a real screen if the
  dialogue version reads badly in playtests.
- **C4 - the kinstone drop curve** (user: "curve analysis later"). Two
  measurable questions: (1) pieces-per-run at current weights - instrument
  a probe that plays N seeds' worth of waves with the real droptable and
  counts kinstone drops by shape; (2) stall risk - which gates' shapes
  can fail to drop in a plausible run length. Then set the curve so the
  EXPECTED pieces cover ~60-70% of a region's gates per run (scarcity with
  agency). The flat halvings so far are placeholders for exactly this
  probe.
- **Phase D cheap events** (lever rooms, bombable-wall treasure, pot-room
  variants, boss-rush, survive-N-seconds). All five are one-mechanism
  recombinations; the decision needed is which ONE to prototype first
  (Decision 6). Recommendation: survive-N-seconds - it reuses the hunt's
  timer + the wave spawner verbatim, so it is the smallest diff, and it
  doubles as the template for F1's timed structure.
- **Phase D medium events** (kill-quota bounty, carry-to-NPC, Great Fairy
  gamble, dig rooms, more Minish sites). Kill-quota: kill counters exist
  (`miniboss_kills` etc.) - needs only a giver NPC + threshold + payout.
  Carry-to-NPC: the shop's lift-carry-confirm flow is the donor; the open
  question is carrying across a room transition (vanilla drops held
  objects on transition - if so, keep giver and receiver in one region).
  Dig rooms and F1's buried items share the Mole Mitts research - do them
  together. Great Fairy: rooms exist, script reuse was scoped in #25.
- **D2 - the inn.** Fully specced in QUICKSTART_HUB.md; the one unknown is
  whether Floor 2's SPECIAL_CHEST objects can be given contents. Probe
  that first in the harness (spawn one, set its item field, open it); if
  it fights back, ground items on the beds' tiles do the job with zero
  new mechanisms - the shop already sells items lying on furniture.
- **Research (user, Aug 2026): can we control chest contents game-wide?**
  Can vanilla chests be given OUR items - both the chests already sitting
  in rooms this mode visits and chests we might place ourselves? What is
  known so far: a CHEST object's item comes from its room-data entity
  definition (kind/id/type plus an item parameter), and the ? room
  item-drop kind deliberately places GROUND_ITEMs instead because that
  path was proven first; the inn's SPECIAL_CHEST question above is one
  sub-case. The research task: read the chest object's open handler to
  find where the item id and the "already opened" flag live, then probe
  (a) overwriting a vanilla chest's item parameter at room load, (b)
  spawning a fresh CHEST with a chosen item, (c) what GiveItem-only
  equipment (swords - see the pedestal note) does when a chest tries to
  hold it. If (a)/(b) work, chests become a delivery option for every
  reward system in the mode - and the chest-lottery's prize could
  finally live IN its chest.
- **D2 - persistent living-enemy count.** The spawner keys off "room has
  no enemies" today. Path: on wave spawn, write the spawned count into
  the region's wave-state byte neighborhood (bank 11 has free ranges);
  decrement on enemy death (the wave-clear watcher already counts
  deaths); on room re-entry spawn only the REMEMBERED remainder, placed
  by the same grid draw. The subtlety is what "remainder" means for a
  wave whose roster was random: store the count only and redraw kinds -
  close enough, and infinitely cheaper than storing the roster.
- **E - regions beyond the ring.** Castor Wilds / Royal Valley each mean:
  un-block a border in transitions.c, extend `QuickStartIsRingRegionRoom`,
  survey (grid + reward + entrance), add fusers, re-run ring.py + checker.
  The ring adjacency map (`sQuickStartRingAdjacency`) and the distance-2
  element rule absorb new named regions by adding one enum row and its
  edges. No new mechanism anywhere - this is the "routine by now" path E
  was always meant to be.
- **E - the Minish layer** (tasks #102, #103). Blocked behind #103 (the
  transform rendering bug and the NHF vine) - fix that first or every
  Minish site stays theoretical. After it: Minish rooms are content sites
  like any other; the survey tool already reads their collision.
- **Sword upgrades in the pools** (section 5 TODO). Equipment has no
  ground-item form, so the grant path must be scripted. Cheapest shape:
  the skill-scroll pickup script pattern, or a pedestal NPC
  (ZELDA-kind, AddInteractableObject like the fusers) whose interaction
  runs GiveItem + a custom text. The pedestal doubles as F4's charm/curse
  delivery for items that also lack ground forms - build it once, use it
  twice.
- **The 2-door pool's door rewiring** (section 5). Surveyed and planned in
  QUICKSTART_2DOOR_MAP.md; the work is mechanical retargeting of 40 exit
  rows to per-door destinations + landings, then a checker tier that
  walks A->B and B->A for every pair. No design questions left - this is
  an afternoon of data entry plus verification, and it removes a
  standing player-visible wart.
- **Item-drop ? rooms "never pay" (user report, unexplained).** Items
  demonstrably spawn (26/26 in the probe). Next step is live-play shaped:
  a probe that walks in through the real door (not a warp), waits, and
  watches the item's entity lifetime; plus one playtest asking whether a
  floor heart-piece simply doesn't read as a payout (the kind was called
  "chest" forever and never was one). Cheap insurance regardless: give
  item-drop sites the sparkle effect the hub's selection items use.
- **POT_MINISH multi-enemy rendering (#17)** - the known VRAM failure
  class. Fold into F8's sheet-slot lifetime tracer; it is the same
  investigation, and #17 is its best-documented reproducer.
- **Gentari adjacency (#19), Trilby NW pocket, Lon Lon top-middle
  pocket** - all three are survey/data fixes waiting on the reachability
  harness (#81) being pleasant to run. #81's mgba-crash workaround
  (process chunking) is done but slow; F8's budget work will touch the
  same harness, so batch them.
- **Boss spawns for the paused regions.** The allowlist is explicitly
  "vetted regions only". Path per region: measure (F6's extended
  measure_budget.py) -> watch one full boss fight there in the harness
  (spawn, fight envelope, death, payout) -> add the room to
  `QuickStartRegionAllowsBoss`. EH-N and LLR are the plausible next
  candidates (large rooms); the EH-S/EH-C seam scrollers likely stay
  boss-free forever, and that is fine.
- **The excluded beanstalk fusions.** Only worth revisiting if cloud rooms
  ever become content; the path would be a containment exception plus a
  return transition, i.e. a new pocket type. Default: leave excluded.
- **Research #51 (difficulty option)** - an options-menu entry writing a
  save field the difficulty getter reads is small; the design question
  (does difficulty still auto-escalate on wins?) is the real content.
  **#53 (hint sprites)** - effectively DONE (the hub hint NPCs); close it
  in favour of F5.

### 8.2 One suggested sequencing

Orderings below try to respect: user-visible wins early, research that
unblocks other work before the work, measurement before allowlists.

1. **F9 Acro-Bandit cap** + the item-drop sparkle - both small, both
   user-visible polish on things already reported.
2. **F1b dialogue pass** over the EXISTING quests (pot hunt, timed hunt) -
   writing only, immediate clarity payoff, and it builds the text
   patterns F1/F2/F7 will reuse.
3. **F3 Electric Chuchu** - one harness experiment away from knowing its
   cost; if the type-variant theory holds it ships in days and refreshes
   the boss roster cheaply.
4. **F5 hint pool + per-run draw** - small, and its content immediately
   teaches the mechanics the deeper features depend on players knowing.
5. **F8 budget audit first half** (the measurement extensions: sheet
   tracer, frame-time probe, boss-combo harness) - this UNBLOCKS F6
   (combos), the boss-region vetting, #17, and honest sizing of F1's
   swarms. Do it before the content that needs its numbers.
6. **F1 timed scavenger hunt** (with the dig research shared with the
   Mole Mitts rooms), then **F7 win-condition variety** - F7 wants F1
   in place so "quest pays the element" has a quest worth paying.
7. **F4 charms/curses**, cheapest four effects first (immunity, drop
   rate, shop, boss chance), then the speed family.
8. **F6 boss+wave combos** and boss-region expansion, now data-driven.
9. **F2 stealth quest** after its vanilla-LOS research spike - park it
   early as a one-day research question ("does guard AI transplant?"),
   schedule the build only once answered.
10. **F8 second half** (the vanilla inventory doc) as background work -
    it has no dependencies and improves every future content decision;
    slot it into gaps.
11. The standing structural debts on their own clock: 2-door rewiring
    (mechanical, any time), persistent enemy count (real design win),
    the inn (waits on its chest probe), C4 curve (waits on its probe),
    Minish layer (waits on #103).

The through-line: measurement tooling (F8/F9/F6 harness work) is the
next real rail. Nearly everything else on this list either needs its
numbers or ships faster once they exist - which is the same lesson Phase
A taught with placement data.
