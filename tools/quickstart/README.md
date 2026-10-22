# QUICKSTART tooling

The new game built on this engine has its own handoff set in
`docs/newgame/`. `10_TOOLING_AND_TESTING.md` there says which of these
tools to carry over and what to build for generated areas.

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
- `castle_probe.py` - Hyrule Castle as a region: its three pool rows deal
  and replace waves and pay nothing for a clear, the guards are swept,
  every crossing is walked with containment live (the gate, the seams, the
  flag doors, the courtyard, the cellar and its ladder), the sanctuary door
  is refused, the three ? rooms, and every quest kind in every wave room.
  39/39.
- `castle_survey.py` - each castle wave room's floor from every arrival,
  one component or not, and a spread of enemy spots (`--emit`).
- `room_shot.py` - one picture of a whole room, stitched from screenshots,
  with tile numbers on the edges.
- `well_probe.py` - Hyrule Town's well and the underground: the fall lands
  in the well room, its ladder and passage, the main room's ladder to the
  chimney roof and back, a door out of the region cancelled. 7/7.
- `block_puzzles.py --append OWNERS` - boards for new rooms only, the shipped
  frames untouched (`--verify-append` replays them).
- `win_probe.py` - the finale alone: the trials forced done, the
  Element drawn, the carrier driven in the Element's row (waves, the boss,
  or the quest flag), the Element taken, the run reset with the score.
  6/6 seeds over WAVE, BOSS and QUEST carriers.
- `shell_probe.py` - seashells as three seconds of invincibility: the clock
  on the pickup and its countdown, `CalculateDamage` keeping the health
  while it runs, and the luck charm living on `ITEM_SHELLS30`. 3/3.
- `perf_census.py` - the frame rate (gMain.ticks, the worst 30-frame
  window) and a census of what is alive, in the three rooms the user named
  with every kind forced at difficulty 3 and 5; `--all` sweeps every site
  and every region row.
- `pc_profile.py` - where the CPU goes: the program counter sampled every
  N instructions over F frames, attributed to game.c statics and map
  globals. `SITE <site> <KIND>` or `REGION <row>`.
- `town_survey.py` - Hyrule Town's plaza for the fifteenth region: the
  floor from each border arrival, the enemy spot spread, the most open tile.
- `town_probe.py` - Hyrule Town as a region: landing, the cast swept, the
  waves and the first clear's reward, pause, its own hint lines, every
  door refused, the four gates walked both ways with containment live, and
  a boss composed in the square. 18/18.
- `puzzle_probe.py` - the switch puzzles (ECHO, LIGHTS, RACE) solved by a
  script that reads the room like a player: it watches the echo's show,
  searches the lights' strikes, races at walking pace; then the prize and
  DONE. `--all` sweeps every site the game deems eligible
  (`QuickStartSitePuzzleOk`, less retired sites and the seed's memory pair).
- `inn_probe.py` - the inn's blessing table: three pastries, one gold, take
  one and the rest go, once a run; the dungeon key bag empty at the start.
- `courier_probe.py` - the courier quest by talking: offer, hurry, the
  receiver in the neighbouring region, delivery pays and closes the side
  quest, nothing twice. NPCs are told apart by the script they run.
- `gregal_probe.py` - Gregal's ghost: his scene on the shop floor, the real
  Gust Jar's contact, the spirit tracked until it yields, the thanks and
  its draw once, gone afterwards.
- `dungeon_reach.py` - the dungeon reach map: every room of the dungeons
  and the castle landed in and flooded into walkable parts, with the edges,
  exits and key/boss doors each part touches. Writes
  `docs/QUICKSTART_DUNGEON_REACH.md` and `docs/dungeon_reach.json`.
- `hub_probe.py` - the hub's two warp pads (asleep during the draft, then
  F3 to the shop and the shop to the tower door).
- `carry_pairs.py` - the single-room carry quest's pairs: floods each
  candidate room's live collision into the carry grid, finds the arrival
  pieces, picks long A-B pairs past two survey places, writes
  `include/quickstart/carry_pairs.h` with each pair's piece bitmap.
- `carry_room_probe.py` - plays every carry pair by key presses (accept,
  lift, both waves, carry, deliver); `--throws` checks a swamp loss, a kept
  throw and the dry-ground rule.
- `carry_measure.py` - the engine facts behind the carry quest: room sizes
  and hazards, lifting, walking and throwing a vanilla pot.
- `trophy_probe.py` - the trophy case: each found row draws its item's
  sprite in the figurine pane (read from OAM), a locked row draws none, the
  Rusted Blade draws in its rust palette, and the charm rows carry their
  own names. Screenshots of a few rows.
- `blessing_probe.py` - the pastry tiers: curses spawn as green blessings,
  gold one in four, the tinted palette slots (and their release), each
  tier's effect through `GiveItem`, the gold croissant's room-entry grace,
  and a gold cake taken off the floor. Saves `blessing_tiers.png` to
  `--out`, and forges a full palette table to prove an untintable green
  pastry turns back into its curse. 14/14.
- `sword_variant_probe.py` - every row of `sQuickStartSwordVariants`: the
  HUD button's icon in the variant's tint, the swing's blade entity in its
  tinted palette, and the pause menu's button and grid entries. 3/3 per row.
- `shf_probe.py` - a field under load, frame by frame: the entity table
  (gEntCount of 72), GFX slots, OBJ palettes (and frames with all nine
  dynamic ones held), OAM, the true frame rate, deaths that never got their
  DEATH_FX (the frozen-enemy symptom), NPCs drawn in palette 0 (a failed
  load) and sprites drawn from a stale GFX slot. Kills one enemy every
  `--every` frames (`--all`: every enemy at once); `--no-collect` leaves
  the drops on the floor. `--row` picks the region (2 = South Hyrule Field,
  19 = Hyrule Town).
- `lantern_gust_survey.py` - every ? room site's tileset: does it list a
  torch (tile types 117 unlit, 118 lit, on either layer) and Mount
  Crenel's dust tiles. 72 of 119 list one. `--draw` paints a torch and
  compares the screen: 59 draw it (the Minish houses list it and draw
  nothing). `--json build/lantern_sites.json` feeds `lantern_rooms.py`.
- `lantern_rooms.py` - generates the torch and cleanup ? room layouts per
  site into `include/quickstart/lantern_rooms.h`, each proven (no torch or
  web walls the room off, every torch has a lighting tile, the webs clear
  in an order from the side the jar takes them, every cloud can be
  approached from below). `--verify` re-proves the shipped table; `--check`
  says whether it is stale.
- `lantern_probe.py` - plays every layout in the ROM: dealt and on screen,
  every torch lit with the Lantern or every web and cloud cleared with the
  jar (`--lantern`: webs burnt), won, waves still standing after the win,
  prize taken, site DONE. `--kind`, `--sites A-B`, `--max N`, `--diff`,
  `--snap DIR`.
- `portal_pockets.py` - the reach graph's pockets, for the portal ? room
  research: every node the mainland cannot walk to with the boot kit, what
  walking in costs, what walking back out costs (TRAP when it needs an
  item, "ocarina only" when no item does), and the region rows and ? room
  sites reachable inside. `--json OUT`.
- `portal_rooms.py` - generates `include/quickstart/portals.h`: the portal
  pockets (landing, one-way or two-way, escape items, what counts as
  inside) and, per ? room site, the tile its portal stands on (captured
  floor, clear of the room's objects from `build/portal_census.json`, no
  Minish rooms). `--check` compares.
- `portal_probe.py` - plays the portal pairs in the ROM: each pocket end to
  end (dealt, asleep, A's fight, lit, ride, paid inside, back, walk out and
  the Ocarina home), the patience rule, `--sweep` every portal A site,
  `--census` the rooms' objects and Minish size for the generator.
- `ruins_statue_probe.py` - the Wind Ruins' tektite statue: a run dropped
  in the Armos room walks out to the Ruins Entrance (the statue removed for
  it), a control with the drop recorded as the Entrance stops at the
  statue, and an Entrance drop keeps the vanilla fight.
- `site_force_probe.py` - a step that forces a ? room's kind (a portal
  pair) dealt while the player stands in that room: the room keeps this
  visit's kind and pays nothing early; out and back in, the force applies.
- `difficulty_probe.py` - the difficulty counter: a new save starts at the
  build's difficulty, each death steps it down to a floor of 1, Continue
  keeps the demoted value, and the seed never lowers a save.
- `hazard_probe.py` - what each roster enemy does to the player: status
  flags (captured, burning, frozen, held), the slowest walking speed, hits
  and their types. Three of each round a player in the quiet dojo;
  `--swing` makes the player strike. Built the torch and cleanup rooms'
  hazard list.
- `lantern_gust_spike.py` - the engine primitives the lantern and gust-jar
  rooms would be built from, played in a cave site: a torch tile set and
  lit by the swung Lantern, put out again, the room darkened dim and black,
  a torch's light share, a spider web pulled by the jar and burnt by the
  lantern, Hyrule Town's dust cloud pulled by the jar. 12/12.
- `sim_study.py` - the simulation study: plays hundreds of thousands of
  runs per cohort over four processes and writes
  `docs/QUICKSTART_SIM_STUDY.md` and `docs/sim_study/`: rooms reachable and
  visited, chain shapes, where each requirement sits, items by source, ?
  room kinds, drop-region islands. `--census` adds `room_census.py`'s diff.
- `site_roll_validate.py` - asks the ROM's `QuickStartContentSiteRoll` for
  every site over a set of seeds and compares with `sim.site_roll`.
- `room_census.py` - every room the region rooms lead to (doors, links,
  Minish holes, scroll seams), with `--gate` asking the ROM's containment
  at each policed door; diffs against the survey, the sites and the pool.
  `--json` writes the rows `sim_study.py --census` reads.
- `chain_roll_validate.py` - asks the ROM's `QuickStartChainRollStep` to
  deal steps for random seeds, drop rows, loadouts and step indices, and
  compares each with `sim.roll_step`: the keyed pair, the escalation and its
  rare-region seek, the spread rule and the rare-region weights.
- `block_rooms.py` - captures the floor of every room a block puzzle may
  use (the 100 lone ? room sites and the 20 pool rows) into
  `build/block_rooms.json`: collision, act tiles, NPCs and the arrival.
- `block_puzzles.py` - the block puzzles' pool
  (`docs/QUICKSTART_BLOCK_PUZZLES.md`): per room up to three template
  frames and three maze frames (plus a door maze per guarded door), each
  with up to 32 contents, every one proved solvable with a floor on its
  push count, clear of every spot the mode already uses. Four processes,
  about 25 minutes. Writes `include/quickstart/block_puzzles.h` and
  `build/block_solutions.json`. `--verify` decodes the header the way
  game.c does and replays every content's solution under the game's
  rules; `--check` compares a fresh run with the header.
- `block_probe.py` - plays block puzzles in the ROM from the solver's
  push list: the dealt rocks, each push, the ROM's own SOLVED flag, the
  prize and the site's DONE (or the quest's WON). `--contents N` per frame
  (default 2, 0 for all), `--rules` adds the refusals (fixed, axis-bound,
  board edge) and the reset switch.
- `block_runpick.py` - the run's own block puzzle draw, nothing forced:
  per site, a seed whose roll deals BLOCKS, the frame and content it
  should draw, and the rocks the room actually deals. 23/23.
