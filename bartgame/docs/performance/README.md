# Performance diagnosis and preservation

The baseline is delivered source11b872e9897320398fa02344cef1418733c04e9a,
ROM SHA2561bd913bc5bf1ad81e9c1dcc7e07ebc38eac855d390a5bb613257f8fbfe128e59.
Production throughput is measured with ordinary, uninstrumented mGBA ROMs.
A separate PROFILE1 build uses unused GBA timers2/3 to identify CPU cost.
The final playable build has no profiler code, counters, timer setup or
per-frame profiler overhead. Native refresh is262144/4389Hz, about59.73Hz;
a completed gameplay-update ratio0.5 means about29.86 updates per second.

## Diagnosed causes

Ordinary torch/darkness rooms recount every cell's unlit censer state each
frame. One representative room spends about88,650 cycles on darkness/camera,
mostly this repeated scan. The same room also repeats glitter selection and
actor-bound queries in both draw passes, consumes about39,000 cycles on
animated-tile scheduling, and performs substantial sprite-depth work. Its
mean instrumented update exceeds330,000 cycles against a280,896-cycle native
frame budget. Six to eight natural enemies can therefore tip a room into
half-speed gameplay; the enemy AI itself is a much smaller part of that case.

The changes avoid equivalent work rather than reducing content:

- Cache unlit-censer counts, invalidating every room mutation and restored
  preview. Darkness and quest conditions retain their exact counts.
- Share exact animation quotients among descriptors with the same speed,
  retaining both volatile clock reads and every ordered DMA/palette result.
- Cache glitter's ordered viewport/material selection by camera and room
  revision; retain live phases, foreground actor tests, caps and draw order.
- Reject only bodies or independent blades that the existing painter cannot
  submit, plus full OAM; continue all offscreen AI and simulation updates.
- Replace repeated opacity reads with packed equivalent row masks. Preserve
  Bloom's original body pixels, palette classification and visibility guard.
- Use conservative row indexes for trees, overhead, water and possible props;
  original depth predicates still make every visible decision.
- Place small measured drawing/collision routines in fast internal RAM. Their
  collision/movement bodies remain unchanged. Retain at least4KB stack space
  with a linker assertion. Animated-tile scheduling uses1,104 bytes of static
  local stack; foreground glitter uses a bounded actor-box scratch array.
- Avoid empty actor kinds in object/hand painting, unchanged HUD mapping
  uploads and duplicate numeral pixel writes. Numeral output remains exact.
- Remove1,200 software divisions per menu redraw and hoist one immutable
  tile-kit pointer, preserving all native menu maps, preferences and controls.

## Evidence and limits

[Measured production results and actual recordings](../../../performance-review/README.md)
include75 natural forest cells across three seeds,24 generated interiors
covering all three styles and ten mystery kinds, combat/action/UI contexts,
30 additional sustained synthetic swarms, and a separately warmed dark room.
Natural rosters are retained. Synthetic populations are explicitly labelled,
with actual initial/end counts recorded. Player health/inventory/navigation
fixtures do not alter enemy HP, AI, room artwork, terrain or frame clocks.
Faster builds advance more gameplay over equal video time, so matching
inputs is not a claim of identical combat outcomes at equal video ages.

Differential host tests compare actual old/new routines, ordered painter
calls, OAM bytes, packed opacity, DMA uploads, palette writes, cache mutations
and all numerical glyphs. Native comparisons cover tree/water/glitter/Bloom
views and all nine menu-style/color combinations. Actual gameplay checks
exercise required trials, bombs/cape/candle, Heart entry, four censers, item
pockets, relic revisits, saves, menus, shop and dialogue. Every authored art
file and resolved native asset payload remains unchanged.

These tests cover finite rooms, actions and populations. Isolated entry,
equipment and combat-boundary repeats remain visible in raw traces; there
is no universal unlimited-enemy or frame-perfect guarantee. Cold map/zoom
pages still generate real room previews. No enemy, mechanic, animation rate,
glitter, detail level or rendering feature is removed to obtain the gain.

## Reproducing the investigation

Normal `make` produces the uninstrumented game. `make PROFILE=1` is a
development-only cycle-accounting build. Rebuild with `make PROFILE=0` before
shipping. The profile stamp recompiles the C objects when switching modes.

- `tools/performance_scenarios.py`: native gameplay/frame workload survey.
- `tools/performance_profile.py`: timer-cycle attribution on PROFILE1 only.
- `tools/performance_regression.py`: source/art/mechanics/native qualification.
- `tools/perf_*_equivalence.py`: focused old/new differential checks.
- `tools/performance_publish.py`: measured review, exact media and release.

[Actor](ACTOR_CULLS.md), [object](OBJECT_FILTERS.md),
[system](SYSTEM_EQUIVALENCE.md), [menu](MENU_INITIALIZATION.md),
[visibility](../PERFORMANCE_VISIBILITY.md), [effects](../PERFORMANCE_EFFECTS.md),
[scenarios](../PERFORMANCE_SCENARIOS.md) and [regression](REGRESSION.md) notes
record individual proof boundaries rather than treating check counts as FPS.
