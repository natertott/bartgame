# Forest visibility without per-pixel re-querying

The 2026-11-04 performance pass keeps the approved tree paintings, live BG
maps, sorting rules and Bloom's partial-visibility guard unchanged. No actor
is hidden, no silhouette is simplified, and no tree/root collision changes.

The previous guard examined each nonzero lower-body pixel independently.
Each examination could repeat forest activation/bounds tests, owner-map
identity, BG screenblock addressing, hardware flips and VRAM nibble decoding.
It also reread the same source-palette classification per selected pixel.

`forest_trees_opaque_row` now reads each intersecting native8px tile row once,
collapses its eight4bpp nibbles into an eight-bit opacity mask, applies the
same hardware flips and returns a32px world-space span. It still requires
the expected tree entry to equal the actual live map entry. Priority3 adds
the existing lower/root plane. `room_canopy_opaque_row` unions the same
legacy foliage fallback; architecture remains excluded as before. These
queries allocate no persistent RAM and cache no map or alpha decisions.

Bloom's guard aligns the span with its mirrored/unmirrored source pose and
intersects four packed words per native row. Every retained nibble remains
the original hero ink. Opaque/colored diagnostics and queued body/guard
uploads retain their previous meanings. The source-palette16-ink classifier
is evaluated once per guard, rather than once per retained pixel. The
redundant second upper-tree bounding query is skipped only where the first
query has already proved it false; priority3 still tests the root plane.

The remaining actor-depth query runs as a small ARM routine in IWRAM
(`forest_depth_iwram.c`). A128-byte row-occupancy index accompanies the
existing planted owner map, updated in the same reset/add operations. It
skips rows that contain no candidate owners before reading slower EWRAM.
Every surviving owner still uses the same bounds, feet/height comparison and
authored root-alpha rows. Once root ink proves the actor behind a tree, the
function returns priority3 immediately: that result dominated all later
front flags in the original side-effect-free query too.

Generic prop depth also uses three conservative32-word indexes for visual
overhead, visual water and possible logical prop/plate contributors. Their
384 bytes plus small revision/dimension keys are rebuilt lazily after a
room mutation or preview restoration. Overhead/water classifications are
exact; prop candidates deliberately include all legacy trees and chests
regardless of readiness, overlay ownership or region. The original predicates
still decide each surviving prop's result. The original C-truncated body
bounds and their different width/height caps remain unchanged. Chest
readiness and area changes cannot create a candidate missing from the index.

`tools/perf_visibility_equivalence.py` reads the complete original guard
function from baseline commit11b872e9897320398fa02344cef1418733c04e9a.
Its host VRAM fixture checks240,000 row queries against7,680,000 original
scalar pixel queries and38,552 complete guard cases. It varies live entry
matches/mismatches, both flips, sparse/opaque VRAM inks, borders, inactive
trees, legacy foliage, both tree priorities, all133 native hero poses and
all16 source palette classifications, as well as fall/hidden/flicker and
invalid-frame exits. Mask bytes, all guard diagnostics, readiness and queue
arguments match exactly. A further240,000 varying native depth/bounds cases
compare the complete original priority function with the optimized ARM-source
routine and row index. The same corpus also passes with the host undefined-
behavior sanitizer enabled. Another240,000 complete generic prop-priority
comparisons exercise20,360 logical/visual/preview-restoration mutations,
including stale visual overlays beside changed logical tiles, and toggle
chest readiness and region without invalidating the conservative index.
Host query equivalence is separate from real mGBA
cycle measurements and does not itself claim an FPS improvement.

The parent performance report records the final linked-ROM measurements,
actual native scene comparisons, source identity and remaining worst cases.
