# Integration validation

Game/art source: `fd7465d87f3dfcec33152254d49b3df629debf26`.
Playable ROM SHA256: `977f38406e3f5cf12e7108e3840356d305d364bd665bc0d9ef578ec8f5937e78`.

| Evidence | Result | Details |
| --- | --- | --- |
| Real mGBA room/camera/movement capture | 140/140 | [Captured views and proof](../actual/capture.json); three rooms,27 native camera frames,504 walk frames |
| Independent packed art, room geometry and capture verification | 1915/1915 | [Audit](audit.json), [host statistics](host/report.json), [host log](host/run.log) |
| Actual mGBA menu, cache, region and progression checks | 78/78 | [Runtime report](runtime/report.json); all three required tasks and item gates |
| Literal image/media/ZIP/link verification | 209/209 | [Publication QA](publication-qa.json) |
| Historical build preservation | 31/31 | [Profiles0–30](legacy-preservation.json), [all32 builds](builds.json) |
| Ordinary default build | Exact selected ROM | [No-override make result](default-build.json) |

The independent host corpus executes the actual C room generator and collision
code using frozen native ROM metadata. Its512 seeds cover12,800 rooms,
86,699 required approaches,7,258 item pockets,108,800 inventory/boundary
checks,6,807,405 unique tree-base ownership checks, opened-state/real-feet
routes, deterministic rebuilds and800 preview/cache cases. Hardware submission
is suppressed in the host harness; these are logic tests, not emulator images.

All twelve source paintings, anchors, palette entries and source-alpha masks
match the frozen ROM. The comparison also protects1532 non-tree forest
metatiles,36 complete OBJ sheets,19 UI/palette payloads and other regions'
resolved tilesets. Forest residency is646/768 BG tiles and11/12 world banks.

The actual runtime harness uses disclosed positioning/enemy-isolation fixtures.
Trial completion, rewards, item use, input, room transitions and menus run real
game code. Its combat fixture selects an attackable enemy instead of waiting
indefinitely on an obstructed first enemy; it never grants trial rewards or
modifies enemy health. Runtime screenshots are untouched240×160 framebuffers.

Full-room images are literal registered mosaics, with a fixed native clock and
HUD hidden by the review camera. Individual native views and declared crops
remain available. Ambient glitter can differ across viewport overlaps; it is
not painted over. Actual minimum visible Bloom pixels are90/94/95 across the
three clips (504 native frames total). There are1/1/0 missed logic intervals, bounded by the
[pinned historical control](../actual/timing-baseline.json); there is no
frame-perfect performance claim. [Optimization timing](fast-alpha-timing.json)
retains the matched diagnostic conditions.

The finite review accepts local upper-crown clipping near protected features
and conservative full-cell forest barrier bands around visibly narrow roots.
See the [independent critique](../../../bartgame/docs/art-reboot/references/FOREST_TREES_INTEGRATION_REVIEW.md).

[Native build header](frozen/v31/assets.h) · [Linker map](frozen/v31/bartgame.map) ·
[Build/input hashes](frozen/v31/freeze.json) · [Asset coverage](frozen/v31/coverage.json) ·
[Review gallery](../README.md)
