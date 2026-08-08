# QUICKSTART tooling

- `emu.py` - minimal mgba harness (boot/warp/memory peek+poke/Qs flag set).
- `parse_tables.py` - parses the placement-bearing tables out of src/game.c
  and src/data/transitions.c so checks always run against the real source.
- `invariant_check.py` - the Phase A1 invariant checker. Run after every
  build that touches placement data:

      python3 tools/quickstart/invariant_check.py

  Exit 0 = green (WARNs allowed), 1 = a placement invariant is broken.
  See its docstring for tiers and what each one proves.
