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
  redraw count. The final four words are reserved.

Component and placement overflow retain the quiet forest backing; they never
write outside the fixed arrays. The telemetry describes construction, while
actual mGBA PPU/VRAM captures must independently establish what was displayed.
Source assemblies alone are not emulator evidence.
