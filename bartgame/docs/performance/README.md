# Performance diagnosis and preservation

The baseline is delivered source 11b872e9897320398fa02344cef1418733c04e9a,
ROM SHA256 1bd913bc5bf1ad81e9c1dcc7e07ebc38eac855d390a5bb613257f8fbfe128e59.
Production throughput is measured with ordinary, uninstrumented mGBA ROMs.
A separate PROFILE=1 build uses unused GBA timers 2/3 to identify CPU cost.
The final playable build has no profiler code, counters, timer setup or
per-frame profiler overhead. Native refresh is262144/4389 Hz, about 59.73 Hz;
a completed gameplay-update ratio 0.5 means about 29.86 updates per second.

## Diagnosed causes

Ordinary torch/darkness rooms recount every cell's unlit censer state each
frame. One representative room spends about 88,650 cycles on darkness/camera,
mostly this repeated scan. The same room also repeats glitter selection and
actor-bound queries in both draw passes, consumes about39,000 cycles on
animated-tile scheduling, and performs substantial sprite-depth work. Its
mean instrumented update exceeds 330,000 cycles against a 280,896-cycle native
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
  collision/movement bodies remain unchanged. Retain at least 4KB stack space
  with a linker assertion. Animated-tile scheduling uses 1,104 bytes of static
  local stack; foreground glitter uses a bounded actor-box scratch array.
- Avoid empty actor kinds in object/hand painting, unchanged HUD mapping
  uploads and duplicate numeral pixel writes. Numeral output remains exact.
- Remove 1,200 software divisions per menu redraw and hoist one immutable
  tile-kit pointer, preserving all native menu maps, preferences and controls.

## Evidence and limits

[Measured production results and actual recordings](../../../performance-review/README.md)
include 75 natural forest cells across three seeds, 24 generated interiors
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
- `tools/performance_profile.py`: timer-cycle attribution on PROFILE=1 only.
- `tools/performance_regression.py`: source/art/mechanics/native qualification.
- `tools/perf_*_equivalence.py`: focused old/new differential checks.
- `tools/performance_publish.py`: measured review, exact media and release.

[Actor](ACTOR_CULLS.md), [object](OBJECT_FILTERS.md),
[system](SYSTEM_EQUIVALENCE.md), [menu](MENU_INITIALIZATION.md),
[visibility](../PERFORMANCE_VISIBILITY.md), [effects](../PERFORMANCE_EFFECTS.md),
[scenarios](../PERFORMANCE_SCENARIOS.md) and [regression](REGRESSION.md) notes
record individual proof boundaries rather than treating check counts as FPS.

## Frozen production qualification

Source: `c09e29092e0d2ba6107659f975ed0c3ec41c3936`.
ROM: 655,332 bytes, SHA256
`59f1e54cbbbac7e8f31b4e0c4623db72fe1f2a2190c7ceee5cc6fd559c6be898`.

| Production measurement | Previous | Optimized |
| --- | ---: | ---: |
| 75 natural rooms | 12,723 /13,500 updates | 13,500 /13,500 |
| 30 sustained enemy fixtures | 4,423 /5,400 | 5,400 /5,400 |
| Warmed dark room | 90 /180 | 180 /180 |
| 146-context corpus | 24,033 /25,920 | 25,907 /25,920 |

All sustained populations retain their actual enemies, including 24-member
groups. Initial enemy types and counts match the reference. The wider corpus
retains 13 repeated-update observations; 12 occur at initial sampling
boundaries and one occurs in a mixed 16-enemy combat case. These are retained
in the published traces. Cold item/key/overview/zoom entry improves by one
to two video frames. An additional 900-frame live Heart/projectile pressure
sample reaches 899 updates versus 898 previously.

The independent committed-build qualification passes 900/900. Every authored
art file and packed native asset remains exact. All 24 matched forest renders
and 45 menu/preference renders are pixel-identical. The actual gameplay
suites pass HUD 290, progression 80, saves 6, quests 12, pockets 18 and revisits 8.
Differential algorithm tests and undefined-behavior checks also pass.

Internal RAM holds 3,948 bytes of initialized data/hot code and 22,316 bytes
of static data. The system stack retains 6,248 bytes below its 0x03007F00
start, exceeding the enforced 4KB minimum. External RAM uses 253,248 bytes,
leaving 8,896 bytes. Normal make is verified to emit the exact frozen ROM with
no profiler symbols. Both diagnostic timer builds use identical measurement
wrappers; their CPU-cycle plots are separate from production FPS evidence.
