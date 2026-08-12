# QUICKSTART tooling

- `emu.py` - minimal mgba harness (boot/warp/memory peek+poke/Qs flag set).
- `parse_tables.py` - parses the placement-bearing tables out of src/game.c
  and src/data/transitions.c so checks always run against the real source.
- `measure_budget.py` - overworld budget probe: peak entity slots (of 72)
  and GFX slots (of 44) per region per difficulty. The GFX table is the
  binding constraint above difficulty 8; run this before adding anything
  that spawns a new sprite. See docs/QUICKSTART_QUEST_RESEARCH.md.
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
- `invariant_check.py` - the Phase A1 invariant checker. Run after every
  build that touches placement data:

      python3 tools/quickstart/invariant_check.py

  Exit 0 = green (WARNs allowed), 1 = a placement invariant is broken.
  See its docstring for tiers and what each one proves.
