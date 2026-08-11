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
Wind Tribe Tower F3   item choice, 3 rounds (key item / bonus / skill)
        |             then the phase machine parks at 10 - no combat here
        | stairs down (vanilla, F3 -> F2 -> F1 -> Entrance)
        v
Tower Entrance        walk out the front door (its solid tiles are cleared)
        |
   Cloud Tops         the wind crest, and the pit in front of it
        | pit fall, redirected by QuickStartProcessHubHoleLink
        v
   region slot 0      endless escalating waves; wave 0's clear drops the
        |             region's one-time reward
        | region exit box
        v
   region slot 1      same, except its wave-0 clear drops the EARTH ELEMENT
        |
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

`sQuickStartRegionPool` - 5 rows: Castle Garden, Lon Lon Ranch, South
Hyrule Field, North Hyrule Field, Trilby Highlands. Each row carries its
entrance, its "onward" exit box, an enemy-offset grid, room size/enemy cap,
a reward pool + reward spot, and an optional quirk hook.

`QuickStartRegionChainLength()` is **2 + 1 per win, capped at 4** (B2). The
chain draws that many distinct UNLOCKED rows at random, in random order,
once per run (B1: Lon Lon Ranch joins at 1 win, Trilby Highlands at 2).
Owning Zora Flippers (with Trilby unlocked) forces Trilby into the last
slot; otherwise it is excluded from the draw entirely (its only surveyed
approach is across a canal).

Within a region: wave 0 is a plain tiered group; every wave after it has a
20% chance of being a solo Chuchu Boss instead. Wave count persists per slot
across leaving and returning (`FLAG_BANK_11`). The boss is beatable without
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

### 3.4 The shop

**Floor 1 of the hub**, one flight up from the tower entrance - walked to,
not drawn. Nine-item catalog in two rows across the upper hall (y=88 and
y=120) with a walkway between them at y=104, and the merchant at its east
end. Every spot is emulator-verified liftable (`invariant_check.py`'s `hub`
tier presses R and reads `gPlayerState.heldObject`, rather than reasoning
from the collision map - which is what made the previous layout take four
attempts). Prices randomized per run, bought by carrying an item to the
merchant (vanilla's own `BuyShopItem` path).

It used to be a "? room": first in the Grimblade dojo behind a fixed link,
then in Stockwell's store reached by redirecting one of eight candidate
overworld doors drawn per run. That retired two standing problems with it -
the drawn door's own "? room" event was displaced for that run, and three of
the nine catalog spots sat on a shelf in a sealed Minish-only pocket.

### 3.5 Win condition

The chain's last slot drops the Earth Element at its reward spot once wave 0
is clear. Picking it up runs: vanilla's item-get message, then "You win!
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

- Global flags: bank 12 from offset 700, `QsCheckFlag`/`QsSetFlag`. Bits
  101-652 are cleared per run; `GF_DIFFICULTY_BIT` (174-177) deliberately is
  not. Layout above the low block: content sites 266-616 (27 x 13 bits),
  bridge 617, shop 618-650, Melari's two latches 651-652, ceiling 707.
  **Raising the site count moves everything above it.** Getting that wrong is
  silent: at 25 sites the smithy's block began at exactly 578, which was the
  bridge flag, so throwing the bridge lever also gave the smithy an all-zero
  roll and entering the smithy joined the bridge.
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
- **A3. Deterministic playtest switch**: a debug toggle that pins the RNG
  seed so a reported bug's run can be reproduced exactly.

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
- **B3. Per-region elements.** Each chain slot's region holds its own
  element; collecting it is what un-gates that region's onward exit. Win =
  the final region's element. (Today only the last slot drops an element
  and exits are ungated.) Element theming per region is a content decision
  - see Decisions.
- **B4. Unlocks viewer** (research task #52) so the player can see the
  progression the whole design hangs on.

### Phase C - The kinstone economy

- **C1. DONE.** Vanilla's death-drop roll (`CreateRandomItemDrop`,
  itemUtils.c). Note the sentinel: a `Droptable` field of **-999** means
  "never", and `SumDropProbabilities2` clamps negatives to zero, so an
  additive weight bump can never escape it - kinstone weights are
  *assigned*, not added.
- **C2. DONE.** Difficulty-scaled piece weights:
  `126 - difficulty * 7`, floored at 42, on red/blue/green alike. Cut 30%
  from the original 180/-10/60 after play-testing: collecting every piece a
  run needed was no real challenge, which is the opposite of what the economy
  is for.
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
- *Medium (one new mechanism each)*: kill-quota bounties per region
  (kill counters exist; needs a quest NPC handout); carry-item-to-NPC
  quests (the shop's carry-to-merchant flow, pointed across rooms);
  Great Fairy fountain gamble (GREAT_FAIRIES rooms + script reuse);
  Mole Mitts dig rooms (DIG_CAVES areas exist and are surveyed
  candidates); Minish-layer ? rooms beyond SHF's two.
- *Hard (new AI or heavy scripting - defer)*: escort/herding events,
  bespoke new enemy behaviours, fully new scripted questlines.

### Phase E - World breadth

Regions 6-7 (Eastern Hills needs its sub-room survey; Castor Wilds), the
Minish layer as a parallel network, pool capacity already modeled. Adding a
region = region-table row + survey + invariant-checker pass, which by then
is routine.

## 5. Known open bugs and loose ends

Full per-room measurements (walkability grids, components, entity headroom,
special tiles, vanilla contents) live in `docs/QUICKSTART_ROOM_SURVEY.md`.

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
- **Hyrule Castle Cellar's content site never fires.** Forcing its kind and
  entering the room produces nothing at all. Its configured content spot is
  `y=376` in a room only 192 tall - outside its own room, the same class of
  error as Lon Lon's old exit box - which suggests it has never worked. The
  generator ignores content offsets now, so it should start working the
  moment the site actually dispatches; why it doesn't is unchased.
- Trilby Highlands: one enemy offset, `(120,24)`, sits in an isolated
  north-west pocket. Not gated - the user paused Trilby zone-gating pending
  their own walk.
- Lon Lon Ranch: the top-middle pocket the user described has no walked box
  yet, so it is still unfenced.
- `POT_MINISH` does not render multi-enemy content (long-standing).
- Gentari's Room / Gentari's Main adjacency conflict (long-standing).
- Lon Lon Ranch's second gated cave (the wallet sinkhole) is unwired.
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
