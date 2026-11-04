# Performance regression qualification

`tools/performance_regression.py` qualifies code changes against the delivered
HUD build, source `11b872e9897320398fa02344cef1418733c04e9a`, ROM SHA256
`1bd913bc5bf1ad81e9c1dcc7e07ebc38eac855d390a5bb613257f8fbfe128e59`.
This complements the natural-enemy/stress workload survey and the focused
host differential tests. It does not substitute screenshots for timing data.

The scope audit compares every retained authored art/metadata file, unchanged
mechanics source, logical behavior regions of enemy/player/actor code, all
generated numeric contracts, every nonpointer linked native asset payload,
all36 resolved sprite-sheet descriptors/pixels, and all three complete
region tile/palette/map/animation sets. Pointer tables are compared through
their resolved data because code relocation necessarily moves addresses.
A production build must not contain cycle-profiler data symbols.

The one permitted declaration/body-prefix normalization removes only the
literal `IWRAM_CODE ` placement token, from both sides. This allows unchanged
hot routines and their declarations to reside in fast memory; every remaining
source byte in these logical regions must still match the baseline. No
arithmetic, collision, control-flow or animation changes are normalized away.
The object-renderer kind filters have their own differential test; all object,
projectile, effect and pickup logic before `objects_draw_hand` must remain
exact, including the release-overlap helper and RNG behavior.
Room generation is compared byte-for-byte after removing only the explicit
`react.h` include and restored-room cache invalidation line following preview
restoration. The menu comparison reverses only the two separately tested pure
presentation rewrites: an invariant kit-pointer hoist and the equivalent600-entry
row/column map loop. Every other menu and generator source byte remains exact;
no navigation, assignment, maze, RNG, event or reward behavior is exempted.

Actual mGBA regression uses the existing HUD review and forest runtime suites,
plus save migration/round trips, the forest quests, all three item pockets and
relic revisits. The original CLI probes are run in separate processes with
only their default ROM/map paths redirected to the immutable tested bundle.
Navigation, inventory and enemy-isolation fixtures are preserved and disclosed
by those tools. Four censers are lit through real candle inputs before the
Gardener reward is tested, exercising the new lazy torch count and invalidation.

An additional actual native image comparison uses four real generated rooms:
healthy, mixed, pond and deep woods, each at three cameras and two fixed clocks.
The existing review-camera hook freezes simulation/clock and suppresses HUD;
nonplayer actors are removed and Bloom stands at the same selected real safe
floor position. A camera containing no playable floor keeps him on real floor
outside that view. No VRAM, palette, framebuffer, terrain or collision bytes
are injected. These24 matched camera images compare literal240×160 RGB
framebuffers. Native partial-canopy visibility is exercised in this corpus.
The source/host tests cover broader geometry and pose combinations; the small
native corpus is not a claim that every possible scene was visually compared.

Faster code allows more normal AI updates at equal video age. Therefore live
combat clips from the workload survey are presented as matched workloads,
not as expected identical images of enemies at equal wall-clock times. The
fixed-clock/native and host differential tests establish visual equivalence
without hiding that difference in the normal simulation.

Before accepting the optimized build, the same probe wrapper was run on the
unmodified baseline: HUD290/290, forest runtime80/80, save6/6, quests12/12,
pockets18/18 and relic revisit8/8 passed. The optimized private pilot's24
native views match exactly; final frozen-source reports provide the final
qualification and hashes. Numerical scope success alone does not prove smooth
or attractive gameplay; the separate real workload and native reviews remain
required.
