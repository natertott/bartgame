# QUICKSTART tooling

- `emu.py` - minimal mgba harness (boot/warp/memory peek+poke/Qs flag set).
- `parse_tables.py` - parses the placement-bearing tables out of src/game.c
  and src/data/transitions.c so checks always run against the real source.
- `measure_budget.py` - overworld budget probe: peak entity slots (of 72)
  and GFX slots (of 44) per region per difficulty. The GFX table is the
  binding constraint above difficulty 8; run this before adding anything
  that spawns a new sprite. `--combo id:form:count+...` stages a boss +
  escort roster through the in-game measurement mailbox
  (QuickStartMeasureMailbox, game.c: 12 bytes at 0x0203FF00 that spawn
  raw CreateEnemy calls past every cap) and prices it. Findings live in
  docs/QUICKSTART_BUDGET.md.
- `gfx_trace.py` - per-frame GFX slot table tracer: sheet loads and
  lifetimes, refcount-0-to-freed reaper latency, zero-free windows. The
  tool that shows WHY a spawn burst failed, where measure_budget only
  shows THAT the table peaked.
- `cpu_probe.py` - CPU cost per staged scenario, measured two ways: the
  lag ratio (game main-loop frames per video frame - cycle-accurate,
  1.000 = full speed, this is the reading to trust) and host wallclock
  per frame (proxy; only comparable within one run on an idle host). Run
  it alone. Reproduces the uncapped acro pile the F9 cap prevents.
- `kinstone_audit.py` - which vanilla Kinstone fusions actually change a
  room this mode visits. Reads `gKinstoneWorldEvents[]` and `gWorldEvents[]`
  out of the built ROM and intersects them with the region pool, the ? room
  sites and the 2-door pool, reporting each fusion's world-event type, the
  gate it opens, and which droppable piece id matches its shape. Re-run it
  after adding a region or a ? room - a new room can drag in gates the
  fuser table does not know about.
- `guide_reach.py` - reachability for the places the ring never visits
  (Veil Falls, Hyrule Castle and the Sanctuary, Dark Hyrule Castle, the
  Cloud Tops, all six dungeons and the Royal Crypt), transcribed from the
  vanilla walkthrough in `world_reach.py`'s vocabulary plus `KEYS(n)`,
  `BIG_KEY` and `CLONES(n)`. Feeds nothing. `--check` validates every room
  name against `roomid.h`; `--adjacency AREA` reads `room_headers.s` for
  rooms that share an edge (dungeon rooms have no transition rows);
  `--summary` is the finding - how much of each dungeon sits behind the
  sword-level clone puzzles this mode cannot pay. Static; no emulator.
  `docs/QUICKSTART_GUIDE_FINDINGS.md` is the write-up.
- `wave_reentry.py` - regression test for the walk-out-and-back exploit on
  3-wave ? rooms (Oct 2026): finds the run's first WAVES site through the
  ROM's own `QuickStartContentSiteRoll`, enters, warps out to Castle Garden
  and back four times, and reads the seam-gauntlet record and the floor.
  PASS is wave 0 every time and no item. Before the fix it printed the
  user's report verbatim: wave 0, 1, 2, reward.
- `find_fuser_spots.py` - proposes `sQuickStartFusers` rows. Boots each
  region with its gates still shut, floods the walkable graph from the
  region entrance, and picks the closest fully-open tile to each gate that
  has open ground on every side. Prints C table rows; the checker
  re-verifies whatever ends up in the source.
- `seed.py` - the Phase A3 fixed-seed playtest switch. Every run records
  its RNG seed in `gSave.run_seed`, so a reported bug is reproducible from
  the player's save file alone (`seed.py show --sav tmc.sav`); pinning makes
  the next run replay that seed exactly (`seed.py pin 0xDEADBEEF`, self-test
  with `seed.py check`). `emu.boot(rom, seed=N)` and
  `invariant_check.py --seed N` both go through it. Note what it exposes: a
  harness boot has no save behind it and therefore always derives the SAME
  seed, so an unpinned checker run only ever tests one run's worth of drawn
  content.
- `hub_rounds.py` - the hub's three selection rounds, per seed:

      python3 tools/quickstart/hub_rounds.py 0xDEADBEEF

  Prints each round's drawn set (checking the three are distinct and come
  from the band that round is supposed to draw from) and then, on a fresh
  boot per item so one pickup cannot mask another, walks onto that item and
  reports whether the round advanced. Worth re-running after anything that
  touches the tier table or the row-teardown path: rounds are detected by an
  item leaving the row, which fires on the frame the item-get cutscene
  starts, so a mistimed teardown shows up here as a STUCK round.
- `shop.py` - what the hub shop is stocking this run, and for how much:

      python3 tools/quickstart/shop.py --arm 0xDEADBEEF
      python3 tools/quickstart/shop.py --buy 3 0xDEADBEEF

  Prints all eight slots with their rolled prices, read straight out of the
  flag bank. `--arm` grants the Bow and Bombs first so the two ammo slots
  stock (they are correctly bare without the weapons). `--buy <slot>` drives
  a real purchase end to end - lift, carry, confirm, pay - and re-reports, so
  the heart piece's price ramp and a one-off slot retiring itself are both
  observable rather than argued from the source.
- `region_crossings.py` - the seven-region overworld ring's connectivity test. Walks
  all 20 region crossings (vanilla seams, the CG<->NHF border/door pair, and
  the two "town bridge" borders that replace the missing Hyrule Town) in
  both directions, and pushes on the 9 blocked outside edges (Veil Falls,
  Lake Hylia, Minish Woods, Castor Wilds, Royal Valley, Mt Crenel) to
  confirm they hold. Run after anything that touches transitions.c, the
  containment functions, or ring-room collision:

      python3 tools/quickstart/region_crossings.py [seed]
- `freeroam.py` - the free-roam hunt's structure, per seed: which region
  drew the Earth Element, that a non-element region's first wave clear pays
  a normal reward at its reward spot, and that the element region's clear
  runs the whole win end to end (the element drops at the wave centre where
  the probe's player stands, so it is auto-collected and the win sequence -
  score, save, soft reset - completes; `gSave.runs_completed` ticking up is
  the assertion):

      python3 tools/quickstart/freeroam.py 0xDEADBEEF
- `invariant_check.py` - the Phase A1 invariant checker. Run after every
  build that touches placement data:

      python3 tools/quickstart/invariant_check.py

  Exit 0 = green (WARNs allowed), 1 = a placement invariant is broken.
  See its docstring for tiers and what each one proves.
- `spawn_audit.py` - where the ? room gauntlet actually puts its enemies.
  Boots every eligible content site (SMALL/LARGE/ANY, no kinstone gate)
  through the testbed with WAVES forced, steps one frame at a time so each
  body is recorded on the frame it appears, kills the wave and waits for
  the next, three waves per room. Every body is checked against the game's
  own flood from the player's tile, a second flood from the content spot,
  the open set and the room rectangle's rim; flagged rooms get an ASCII
  map and a screenshot in `--out DIR`. It cannot tell a neighbour
  chamber's event from a spill in the three multi-site rooms, and the RIM
  tag is advisory (Minish paths walk their top row):

      python3 tools/quickstart/spawn_audit.py --rom tmc-d3.gba --out /tmp/audit [--sites 4,13]
- `boulder_probe.py` - the one-way boulders in the ROM: no auto-fill (the
  Trilby rock stays at its spot; with its flag set the manager puts it in
  the hole), the held mask's boulder and north-field bits, Percy's
  treehouse through `QuickStartReachTestRoom`, and a collision-flood
  partition of Lon Lon Ranch and Trilby from every surveyed landing with
  each boulder out and in. The partition is collision only - blind to
  ledges - so read it beside the walked survey, not instead of it:

      python3 tools/quickstart/boulder_probe.py --rom tmc-d3.gba
- `crenel_vine_probe.py` - Mount Crenel's bean vine (Oct 2026): no sprout
  entity left in Entrance (a grown sprout lays its vine and deletes
  itself), the two tiles above the bean are climb tiles over a walkable
  foot, a player below the vine climbs into Center, and a player walking
  down from Center crosses the seam and reaches the Entrance floor:

      python3 tools/quickstart/crenel_vine_probe.py --rom tmc-d3.gba
- `veilfalls_probe.py` - Veil Falls, the fourteenth region, and the two
  golden-kinstone gates (Oct 2026). Pinned seeds are booted until both
  gates have been seen sealed and open; with the Source of the Flow gate
  open cave #1's door opens from the North Field corridor and no stone
  stands; sealed, the stone stands, the cave stays shut, `SOURCE_FLOW` is
  not in the held mask and the piece is wanted, a drop forced onto the
  falls' pool row is re-drawn, and writing the fusion makes the stone go and
  the cave open; `QuickStartSpawnRewardEntity` lays the piece as a kinstone;
  the Castor Wilds passage is walkable with `STATUES` held on the open roll,
  solid and not held on the sealed one (the set key pays its first piece),
  and the passage flag the rock cutscene sets opens it. Then the region
  itself: the Top screen's whirlwind is gone, the big falls climb with the
  Grip Ring and not without, the pool row's entrance, reward and fuser spots
  share one walkable piece, every site spot is on its door's arrival piece,
  `QuickStartReachTestRoom` from the falls' pool row prices the cave at the
  lantern, the top plateau at the grip and the Lon Lon strip as never, and
  the seven border crossings land where the rows say:

      python3 tools/quickstart/veilfalls_probe.py --rom tmc-d3.gba


- `finale_probe.py` - the finale is drawn from LIVE reach when the fourth
  trial completes (Oct 2026, the redesign's P0.1), not at the hub's exit by
  map distance: forces the four pre-steps on two seeds, lands in the drop
  row, and reads back the element row, the carrier bits and that the row's
  region is inside `QuickStartReachableRegions(held)` at that moment; the
  compass marker before and after. 7/7.
- `chain_audit.py` - the completion audit (P0.3): every ? room site x every
  kind the testbed can force, driven to its end with a player's inputs (or
  a probe's cheat: health 0 for a wave, a teleport INSIDE the room after the
  walk failed, reported as such) and the site's DONE bit read back - the bit
  a chain EVENT step waits on. Results per cell: PASS, FAIL, LEFT (the
  landing walked out of the room), NOSPAWN, MEMORY, GATED, VANILLA,
  UNDRIVEN. `--sites A:B` shards it, `--only 4:WAVES,85:CHEST_LOTTERY`
  re-runs cells, `--regions` checks the wave counter per pool row. It found
  the fairy kind that never completed, the chest rows over walls, the
  moved chest row that forgot itself, the landings on exit stairs, the
  second Zelda that never spawns, and the Cave of Flames entrance's layer.
- `chain_end_probe.py` - the chain-end probe (P1.4): can a RUN be won? Boots
  a plain run per seed with the real starting kit, drives every dealt step
  with the audit's inputs and a warp for the travel between rooms, reads the
  finale the ROM drew, drives the carrier and picks up the Element. A seed
  ends WIN or FAIL at a named step; forced steps (the quests, the undriven
  kinds) are listed per seed. `--seeds A:B`, `--verbose`. A win is a RESET
  (the score lands in `gSave.meta_xp` and the next run starts), which is
  how both this and `win_probe.py` read it.
- `win_probe.py` - the finale alone: the four trials forced done, the
  Element drawn, the carrier driven in the Element's row (waves, the boss,
  or the quest flag), the Element taken, the run reset with the score.
  6/6 seeds over WAVE, BOSS and QUEST carriers.
- `shell_probe.py` - seashells as three seconds of invincibility: the clock
  on the pickup and its countdown, `CalculateDamage` keeping the health
  while it runs, and the luck charm living on `ITEM_SHELLS30`. 3/3.