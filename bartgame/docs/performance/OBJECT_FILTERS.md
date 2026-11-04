# Reject unrelated actor kinds before object-composite checks

The three object-paint passes formerly visited all95 non-player actor slots
and called the released-load overlap predicate before checking whether their
kind could ever paint. Empty slots, enemy bodies and NPCs cannot pass that
predicate or the later object-paint conditions.

`objects_draw()` now first accepts only projectiles, pickups, effects and
objects. Each near/far `objects_draw_hand()` pass first accepts only objects,
projectiles and effects. The original release-overlap, hand validity, bomb
handoff, gated-hoard, hurt/hidden, art selection and layer predicates remain
unchanged after those filters. No update, movement, lifecycle, collision,
timer, enemy count, RNG or object allocation code changes.

`tools/perf_objects_equivalence.py` compiles the actual baseline/candidate
painters and release-overlap helpers against the unchanged renderer, native
sheet descriptors and a pure deterministic depth stub. It compares the full
ordered painter-call trace, all128 OAM entries, all64 bytes of every actor,
player state, world and game state. Both hand passes and the ordinary object
pass run in their original order.

The differential test passes107,704 cases, including8,192 randomized
96-actor pools and34,950 initially full OAM pools. It exercises bombs at
timer2 values0–8, all four release sides, player arrows and their ownership
bit, flames, thrown loads, gated/opened hoards, hidden/blinking actors and
Bloom's falling/death/hidden hand-composite conditions. Ordered604,195
painter calls and39,687 submitted OAM entries remain identical. It avoids
29,922,703 redundant release-overlap calls in this synthetic corpus; that
work count is not a typical-room speed claim.

The renderer/depth stub deliberately holds those independent systems fixed.
Actual depth, sprites, combat, native framebuffers and cycle improvement are
qualified by the parent real-mGBA performance suite.
