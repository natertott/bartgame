# QUICKSTART Roadmap

Rewritten against the code as it actually stands. The previous version of
this document described an architecture the code left behind ~30 commits
ago - most of what runs today (the vanilla-door "? room" model, the 2-door
pool, the relocated shop, the gated-zone table) was not in it at all.

## 1. The vision

A roguelite mode built inside the vanilla game: a short run through a
handful of overworld regions, randomized every time, ending when the player
takes the Earth Element. Wins raise a persistent difficulty counter and feed
a meta-progression score. The vanilla world is the content - rooms, doors,
enemies and props are reused rather than authored - so most work here is
about *selecting* and *repurposing* what is already there, safely.

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
Castor Darknut Main   item choice, 3 rounds (key item / bonus / skill)
        |
Castor Darknut Hall   one enemy wave
        |
   [Melari's Mine]    BYPASSED - QuickStartSkipMelarisMine warps the player
        |             straight on to chain slot 0 on arrival
        v
   region slot 0      endless escalating waves; wave 0's clear drops the
        |             region's one-time reward
        | region exit box
        v
   region slot 1      same, except its wave-0 clear drops the EARTH ELEMENT
        |
      win: difficulty +1, score -> meta_xp, save, soft reset
```

Melari's Mine is skipped for playtest speed (the user's call - the overworld
is what is under test). The room, its reward, its enemies and its two ? rooms
are all still built; deleting `QuickStartSkipMelarisMine` restores the hub.

Because the hub is no longer guaranteed to be visited, **every per-run draw
is rolled unconditionally** from `QuickStartRoomMonitor` (region chain,
ladders, doors, 2-door, river bridge, cave, Melari rooms, shop), each latched
by its own `GF_*_RANDOMIZED` flag.

### 3.2 Regions

`sQuickStartRegionPool` - 5 rows: Castle Garden, Lon Lon Ranch, South
Hyrule Field, North Hyrule Field, Trilby Highlands. Each row carries its
entrance, its "onward" exit box, an enemy-offset grid, room size/enemy cap,
a reward pool + reward spot, and an optional quirk hook.

`QUICKSTART_REGION_CHAIN_LENGTH` is **2**. The chain draws that many
distinct rows at random, in random order, once per run. Owning Zora Flippers
forces Trilby Highlands into the last slot; not owning them excludes it from
the draw entirely (its only surveyed approach is across a canal).

Within a region: wave 0 is a plain tiered group; every wave after it has a
20% chance of being a solo Chuchu Boss instead. Wave count persists per slot
across leaving and returning (`FLAG_BANK_11`).

### 3.3 "? rooms" - three distinct systems

1. **Content sites** (`sQuickStartRoomContentSites`, 27 rows) - the primary
   model. A real vanilla room, entered through its own real vanilla door,
   with a randomized event placed inside it. Rooms can hold several events
   (the Boomerang chamber holds five, one per entrance).
2. **2-door pool** (7 small + 13 large rooms) - rooms reached through a
   synthetic connector that puts the same room behind both of two doors.
   Fed by Lon Lon Ranch's cave mouth, North Hyrule Field's river bridge, and
   North Hyrule Field's cave mouth, each with its own independent draw.
3. **Ladder pool** - the original mechanism, now down to Castle Garden's
   northwest ladder, which redirects to a drawn single-door room.

All three converge on `QuickStartSetupEventContent`, which places one of
**seven kinds**: chest, miniboss, NPC, 3-wave gauntlet, pot lottery, chest
lottery, fairy room. A content site names which set it may roll:
`QUICKSTART_KINDS_SMALL` (chest/NPC/both lotteries) for cramped tree hollows
and cave nooks, `QUICKSTART_KINDS_LARGE` (miniboss/waves/fairy) for rooms
with floor space, and `QUICKSTART_KINDS_ANY` for rooms big and clear enough
to host anything. A room being large was never a reason to stop it rolling a
pot lottery; it was only ever a reason to stop a cramped one rolling a
miniboss, which is what ANY exists to say.

Two of the sites are **Minish-gated**: the cave at (376,216) and the tiny
door at (72,456), both in South Hyrule Field, both reachable only by
shrinking. Every region has a vanilla Minish portal, and
`QuickStartRevealHiddenLadders` uncovers the four that ship hidden under a
stump - vanilla wants the player to roll into it, an unmarked secret with no
hint, and this mode has no Ezlo hints.

Every one of these rooms is swept on entry: vanilla enemies, NPCs, and
payout-shaped objects (ground items, both chest kinds, heart containers,
fairies) are deleted, so the event *is* the room's reward rather than a
bonus on top of vanilla's.

### 3.4 The shop

Its own room (Stockwell's), reached by redirecting one of eight candidate
overworld doors, drawn per run. Nine-item catalog on the floor in front of
the shelving, prices randomized per run, bought by carrying an item to the
merchant (vanilla's own `BuyShopItem` path).

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
- `gSave`: `run_frames`, `final_wave_frame`, `enemies_killed`,
  `miniboss_kills`, `boss_kills` (per run); `meta_xp`, `runs_completed`
  (persistent).

## 4. Priorities

Ordered as agreed. Nothing below the line gets started until everything
above it is smooth.

### Now

**P1. Puzzle rooms and ? rooms.** The largest slice of run-to-run variety,
and the thing a playthrough spends most of its time in.
- A real puzzle kind beyond the two lotteries. Candidates the engine
  already supports: pushable blocks onto switches, hit-all-crystals, a timed
  dash. Needs one prototype in front of a human before more is built.
- Per-kind reward pools - today every kind draws from the same 4-item
  `sQuickStartLadderRewardPool`.
- More miniboss types; the roster audit only ever confirmed `DARK_NUT` and
  `CHUCHU_BOSS`.
- Fold the remaining bespoke room dispatchers (Melari East/Southeast) into
  the content-site table.
- Content-site coverage pass: several rows are for rooms that are currently
  unreachable and are kept only against a future fix.

**P2. Kinstone-fusion door gating.** Today every gated entrance in the pool
is force-fused at boot - a stopgap that silently pre-solves them. The real
feature: pieces drop from enemies/pots, lightweight fusion-partner sprites
sit in each region, walking up with a matching piece clears one door
permanently. Use a QUICKSTART-owned flag/check rather than vanilla's
100-partner machinery. Open: pieces per region, 1:1 vs many-to-one, drop
weighting, whether partners are visible before a piece is held.

**P3. Win conditions - establish and test.** The mechanism is fixed and
verified end to end in the emulator; what is missing is *coverage*. Every
spawn and item-selection path should be walked, not just the ones that
happened to come up. Concretely: finish the reachability survey for Castle
Garden, Lon Lon Ranch and North Hyrule Field (the three the harness could
not measure), and confirm each region is winnable as the last slot.

**P4. The bridge switch.** DONE - `QuickStartUpdateSwitchBridges`. North
Hyrule Field's `HITTABLE_LEVER` at local (56,456) toggles room flag 100
(vanilla's own, deliberately read raw rather than through our private
window); throwing it fills the three-tile gap in the river bridge at local
(160-207, 592-623), and a Qs global flag keeps it filled for the rest of the
run across leaving and returning.

The reusable part is **how** the gap is filled: copy the tile from an intact
neighbour rather than naming a tile. `GetTileTypeAtTilePos` on a plank two
tiles away, `SetTileType` onto each gap tile. A tile lifted from the same
room is by construction from that room's own tileset, so graphics, collision
and act tile all stay consistent and nothing is hardcoded - which is what
went wrong when the Boomerang chamber was given literal `TILE_TYPE_*`
constants from another area's tileset. Note `SetTile(index)` is NOT
sufficient: it updates `mapData` and the collision/act maps (measured: the
gap moved from index 465-467/collision 48 to the donor's 23/collision 0) but
nothing redraws the on-screen BG buffer, so the player walks across water
that still looks like water. `SetTileType` is the path vanilla itself uses
for a visible change.

### Next

**P5. Difficulty by chain position.** Map slot index to a tier offset on top
of the persistent difficulty counter. Cheap once the curve is decided;
the curve itself needs playtest data.

**P6. Item pools and prerequisites.** Split the one reward pool into named
pools per room kind and per difficulty; add an item-requires-item table
consulted before any reward roll; give the other four key items real,
surveyed paths the way Flippers/Trilby already has one.

### After that

**P7. Expand the overworld pool.** Eastern Hills (3 sub-rooms, needs its own
survey) and Castor Wilds, taking the pool to 7, then raise
`QUICKSTART_REGION_CHAIN_LENGTH` from 2 to 4.

**P8. Score-gated unlocks.** `meta_xp` and `runs_completed` already
accumulate and survive the reset. Needs a threshold table and a reserved
unlock-bit range, plus real score data from human playthroughs to pick
thresholds.

## 5. Known open bugs and loose ends

- Lon Lon Ranch's two `MINISH_SIZED_ENTRANCE` objects at (316,632) and
  (436,632) are the ranch house's west and east Minish doors (the user's
  own identification). They lead into rooms that are already content sites,
  so they are a second route in rather than new ? rooms.
- No Minish-sized entrance exists anywhere else in Lon Lon Ranch's room
  data - the central "long hallway" the player expects after shrinking there
  has no entrance object in this room. Where vanilla puts that entrance is
  still unfound.
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

## 6. Testing

**Reliable to automate**: state/math changes via memory pokes; room
transitions and spawn positions via scripted walks; standability and
4-direction walkability of any specific coordinate; entity dumps for "what
is actually in this room"; persistence across `DoSoftReset`.

**Not reliable to automate**: anything requiring an enemy to die from real
combat; whether an encounter is fair; whether a puzzle is solvable or fun;
pacing across a full run. These need a human playtest and should be handed
over as such rather than approximated with a bot script.

**A note on ground truth**: where the user has hand-walked coordinates, those
win over anything the harness reports. The harness has been wrong often
enough - and the walked boxes right often enough - that this is the standing
order, not a preference.

## 7. Open questions

1. Which puzzle mechanic to prototype first?
2. Kinstone gating shape: how many partners per region, and should they be
   visible before the player holds a matching piece?
3. Item prerequisite and per-kind reward pool lists (content decisions).
4. Unlock pacing - roughly how many wins to open the full pool.
