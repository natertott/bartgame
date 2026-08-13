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
- `ring.py` - the seven-region overworld ring's connectivity test. Walks
  all 20 region crossings (vanilla seams, the CG<->NHF border/door pair, and
  the two "town bridge" borders that replace the missing Hyrule Town) in
  both directions, and pushes on the 9 blocked outside edges (Veil Falls,
  Lake Hylia, Minish Woods, Castor Wilds, Royal Valley, Mt Crenel) to
  confirm they hold. Run after anything that touches transitions.c, the
  containment functions, or ring-room collision:

      python3 tools/quickstart/ring.py [seed]
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
