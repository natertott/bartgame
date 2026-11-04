# Cold menu/map diagnosis and exact initialization savings

The broad native measurements distinguish paused-menu work from an active
room falling below its frame budget. Cold item/key/map redraws and the first
detailed chart can span several video frames. The existing VBlank input latch
retains taps while this synchronous work completes. This pass does not skip
chart geometry, trim text, simplify frames or change that control model.

Two avoidable costs were found directly in the selected Thumb build:

- `ms_draw()` initialized600 visible BG3 map entries using both `i/30` and
  `i%30`. Its generated loop called `__aeabi_idiv` and `__aeabi_idivmod` once
  each per tile:1,200 software divisions on every redraw. A20×30 row/column
  loop writes exactly the same entries in the same order without division.
  The original1,024-entry clearing pass remains, including the unused cells.
- `ms_cache_kit()` called `ui_current_tiles()` inside all four flips,51 tiles
  and eight rows. Appearance changes only on the main thread outside this
  cache build. Hoisting its immutable source pointer removes1,631 repeated
  lookups per cold build. Existing warm/cold invalidation behavior is retained.

No persistent RAM is added. `tools/perf_menu_equivalence.py` compiles the
actual old/new initialization fragments and native cache functions. Across
all16 palette banks it compares every1,024 map value and25,984 ordered writes.
All four flips, opacity masks and glyph bit masks match for all three linked
frame styles in both cold and warm-cache cases.

The detailed chart's first view still runs the existing full procedural room
preview to retain real paths, approaches and exact feature positions. The
existing per-run mask/event caches prevent duplicate generation on later
views. Replacing that with asynchronous work would be a larger flow change;
no such behavior change is introduced here. Real native menu screenshots,
styles/colors, restoration and cold/warm costs are qualified separately in
the mGBA comparison suite.
