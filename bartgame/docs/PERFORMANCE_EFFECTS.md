# Effects and HUD performance diagnosis

2026-11-04. This pass preserves the selected native art, glitter coverage,
item/counter shapes, layers and all gameplay clocks. Source baseline is
`11b872e9897320398fa02344cef1418733c04e9a`, the delivered gilt-HUD build.
Representative measured CPU costs belong to the main performance report;
the host comparisons below establish algorithm equivalence separately.

## Surface glitter

The original renderer scans the shuffled room-wide list twice per world
render, once before the actors and once after them. Each pass repeatedly
queries live room material. Every active foreground glint can scan all96
actor slots and calculate the same actor silhouettes again. Natural crowded
room profiling identified both passes as a substantial frame cost.

The optimized selector retains the exact first24 surviving viewport/material
sites, in the original shuffled order. A96-byte index/material cache uses
camera coordinates and the room mutation revision as its key. Opening,
destroying or rendering room material advances that revision. Room/reset
always invalidates the cached site list, including resets at the same video
frame. Phase and actor/OAM conditions remain live on every draw; no glitter
site, active phase, budget or sparkle frame is removed.

The foreground helper lazily prepares visual rectangles only when an active
foreground glint needs them. It keeps full32-bit bounds/feet and discards
only rectangles that cannot intersect the exact eligible inner viewport.
Every retained rectangle has the original width, height, Z and foot-depth
tests. The bounded96×20-byte scratch array uses1,920 bytes of transient IWRAM
stack and is released before Bloom's separate visibility-mask preparation.
No actor state or world RNG is written. The generated glitter frame count
also replaces two software divisions of an immutable sheet descriptor.

## HUD mapping and quantities

The HUD's90 screen-map entries are stable while its tile pixels animate.
Previously `hud_bar` cleared/remapped the top three rows and marked the
entire2KB BG0 shadow map dirty on every gameplay update. The new installed
mapping flag is invalidated by every public shadow-map mutation/borrow route
(`clear`, `put`/`fill`, raw-map borrowing, canvas/show) and by HUD invalidation.
The HUD restores its entries once after such a change. Ordinary animation
still updates the existing tile pixels and OAM at the same times.

Quantity updates previously painted a nine-pixel outline around every set
glyph pixel, with repeated function calls and overdraw. The same literal3×5
glyph table now forms seven coverage rows. One-bit rows are expanded into
native4bpp masks and merged into at most four destination words per row.
The outline, type ink, one-pixel spacing, coordinates, clipping and existing
five-digit truncation remain exact; surrounding cached pixels are preserved.

The historical HUD0 rendering branch is not edited by these HUD changes.

## Equivalence evidence

`tools/perf_effects_equivalence.py` compiles the actual baseline/current C
sources for the host and supplies deterministic room/actor/render fixtures.
It compares full glitter draw-call streams and counters, not just totals.
The tests include camera motion/holds, all phases, room mutation revisions,
random actor kinds/flags/visual sizes/Z, OAM pressure and repeated same-frame
complete renders. HUD tests exercise mutation, borrowing and restoration;
numbers begin over random4bpp backgrounds so unchanged pixels are checked.

Current results:

- 65,536 glitter fixtures;106,666 identical calls, ordering, frames, palettes,
 coordinates, priorities, caps and counters. Repeated visual-size queries
 fall from1,511,437 to541,764 in this corpus.
- 50,000 HUD map fixtures, each comparing all1,024 shadow entries; avoidable
 map uploads fall from50,000 to5,185 under deliberately frequent UI mutation.
- 138,048 quantity fixtures: every16-bit gilt value, all byte ammunition
 values at the three actual slots, hardware-word alignments, clipping and
 the original five-digit behavior on larger unsigned inputs. All720 packed
 canvas words agree in every case.

These are focused algorithm tests. They do not claim that host operation
counts equal GBA CPU cycles or replace actual crowded-room, combat, HUD,
dialogue/menu-restoration and native-frame review.
