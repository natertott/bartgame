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
- `invariant_check.py` - the Phase A1 invariant checker. Run after every
  build that touches placement data:

      python3 tools/quickstart/invariant_check.py

  Exit 0 = green (WARNs allowed), 1 = a placement invariant is broken.
  See its docstring for tiers and what each one proves.
