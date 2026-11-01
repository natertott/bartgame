# Room-shaped canopy composition studies

Status: exploratory profiles 19–28. These replace the rejected repeated-canopy
studies for review; they do not select a production art direction. The user's
latest instruction supersedes the earlier fixed 3×3 composition rule.

The semantic room is generated first. `canopy_scene.c` reads its actual forest
mass, including healthy, diseased and connector cells, then labels connected
components. It fits native drawings into the available unclaimed rectangles.
Small isolated pieces and broad stands therefore use different authored
drawings, rather than enlargements of the same tile. A 96×64 drawing occupies
six by four logical cells but is designed as one tree group. The eight-pixel
hardware tiles are only storage and transfer units.

The nine native roles are 16×16 small growth, 32×32 clump, 48×48 tree, 64×64
grove, 96×64 hero stand, 64×16 overhanging branch, 32×16 roots, 96×32 narrow
border and 16×64 column. A broad component receives a hero where it fits,
followed by unequal supporting groups. Placement prefers edges exposed to
walkable space, particularly the south face where the native trunks are
visible. The fit search has no global chunk grid or source-cell parity rule.
Small fragments retain quiet organic backing if a larger drawing cannot fit.
The long branch has a separately packed solid-backed picture for thin blocked
components. Its projected version retains transparent space around the limb;
the blocked version has a quiet dense understory so it does not advertise
walkable floor inside collision. Both have the same native 64×16 anatomy.

The selected style has one immutable atlas. At the first linked style-1 pilot,
the complete forest atlas occupies 911 of the GBA's 1024 eight-pixel tiles and
11 of the 12 area palette banks, before the backed-branch addition. Those are
measured pilot figures, not a
guarantee for every later art revision. The engine does not stream character
tiles, rasterize a full-room pixel image or allocate a framebuffer. It stores
the final BG1 map entries for the room, leaving the existing world planes and
OBJ rendering in place. Native source alpha defines the drawn contour; the
planner guarantees semantic footprint fit, not arbitrary pixel-mask clipping.
Actual isolated and concave borders still require visual review.

The room's logical ground, overlays, stored substrates, collision, maze and
world RNG are unchanged. Portal frames, rewards, speakers, quest torches and
their approaches are excluded from the composition. Only deep interior
forest cells receive the quiet opaque underbrush ground plane; boundary
alpha reveals the local floor. A few broad branches may project into clear
floor next to a continuous forest edge. Their cells retain walkable physics.
Rendered vegetation ownership markers let the existing exact-pixel Bloom
visibility guard inspect the real resident BG1 pixels, including these
projected branches. This pass does not change Bloom frames or action timing.

Planning happens at room render, with a cache keyed by seed, cell, dimensions
and the actual eligible forest mask. Returning from a menu reuses the scene
when that mask is unchanged. Ordinary item edits redraw only touched cells
and their neighbors and reapply their stored scene entries. Palette animation
changes one dedicated canopy bank after the existing forest pulse; healthy
through deep stages share geometry and retain living-green accents.

Fit tests use 32 available-row bitmasks, with a chosen footprint clearing its
bits in at most four rows. Cached open-floor row and column masks provide exact
edge-exposure counts through a 64-entry lookup table. The native drawings span
at most six cells horizontally and four vertically; larger future roles would
require extending that lookup policy. Candidate searches retain ascending
order within each component's inclusive bounds, preserving the previous
placement decisions and hash tie breaks. The hot fit search, count table and
small masks occupy 1,280 additional bytes of IWRAM. The local inlined score
hash retains the shared `hash32` expression; it never advances gameplay RNG.

The measured final pilot uses EWRAM through `0x02039514` (234,772 bytes) and
IWRAM through `0x03005ab4`, leaving 9,292 bytes before the system stack's initial
address. These are linked allocation bounds, not measured worst-case stack
usage. No extra scene atlas, framebuffer or streamed character cache was added.

On the measured mGBA seed-6/cell-4 transition, the original adaptive planner
took 108 video/VBlank frames, the bitmask version 54, and the final IWRAM
version 47; preserved base6 took 28. All observed transitions executed two
mainloop updates. Final loading is about 0.79 seconds versus base6's 0.47,
an extra 0.32 seconds in this case. This is a known room-entry cost, distinct
from recorded gameplay cadence and not a bound for every generated room.
Coarse internal timing for the final case was 1 frame for mask/copy, 12 for
component fitting and 3 for projection/application, 16 total inside the
adaptive build. All five reviewed natural rooms retained byte-identical
8,192-byte BG1 and BG2 maps, visual owner arrays, placement records and masks
between the original and optimized planners. Independent checks compared
736,212 fits and exposure counts against per-cell definitions and one million
actual C hash results against the shared hash. Reports are
`audit/planner-bitmask-equivalence.json`, `audit/local-score-hash-equivalence.json`
and `audit/planner-iwram-runtime.json` in the review workspace.

Read-only telemetry in `canopy_scene.h` makes the choice reviewable:

- `gAdaptiveCanopyMask`: 32×32 bytes; 1 solid forest, 2 projected branch.
- `gAdaptiveCanopyComponent`: 32×32 component IDs.
- `gAdaptiveCanopyComponents`: 12-byte records containing ID, area, inclusive
  bounds, placement count and painted cell count.
- `gAdaptiveCanopyPlacements`: 8-byte records containing component ID, role,
  x/y/w/h in 16-pixel cells and flags; the drawing is never scaled or flipped.
- `gAdaptiveCanopyStats`: 16 words; version, component count, recorded count,
  placement count, eligible cells, painted solid cells, projected cells,
  greatest native width/height in pixels, stage, overflow flags and cached
  redraw count. Words 12–15 contain coarse room-entry VBlank counts for
  mask/copy, component fitting, projection/application and total. Interrupt
  timing can round phase boundaries; these words do not drive gameplay.

Component and placement overflow retain the quiet forest backing; they never
write outside the fixed arrays. The telemetry describes construction, while
actual mGBA PPU/VRAM captures must independently establish what was displayed.
Source assemblies alone are not emulator evidence.

Historical profiles 0–18 omit `canopy_scene.c` from the Makefile's linker input
list. Preprocessor guards alone were insufficient: even an empty extra object
reordered GNU ld's ARM/Thumb division veneers. Restoring the original input
list restored all 19 historical ROM hashes exactly. This is a binary
preservation rule, not an art-selection change.
