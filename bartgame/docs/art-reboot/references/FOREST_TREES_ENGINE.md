# Approved repeated trees in generated rooms

The user's approval of the twelve native pieces in `art/forest_tree_study.py`
authorizes their production integration. This pass preserves those exact
32×32 and16×32 source pixels, shared RGB555 palette, two forms and three
structural states. The already-read GBA field guide, especially pp.6–11,
supplies the local contact, collision, depth and native contract checks. No
new article or reference image is claimed.

## Geometry and collision

Profile31 plans trees after ordinary room generation. It never changes the
layout RNG, ground/overlay logical IDs, event positions or collision masks.
Every solid forest/canopy base cell has exactly one tree owner. Adjacent equal
base cells usually receive a32px broad drawing; narrow16px drawings fit single
cells and break up rows. A stateless seed/cell/position hash selects form and
healthy/sick/dead state. Healthy rooms strongly favor healthy trees; middle
rooms mix all states; deep rooms favor sick and dead while retaining green.
The healthy/sick/dead hash thresholds are 86/14/0, 55/40/5, 30/50/20 and
18/42/40 percent for stages 0, 1, 2 and 3 respectively. These are probabilities,
not a forced quota in each room.

The old large drawings are fully retired from the profile31 renderer. A
standard32×48 logical group becomes one compact broad tree over its existing
two-cell root row. A48×64 great tree becomes a compact narrow tree at its
single solid center root; its old floor root wings and three-row crown vanish.
Small dead trees likewise use one compact native picture. Old overlays and
floor props never remain as stray tree parts.

Production forest stands retain the original full16px-deep base bands, one or
two cells wide. Free-standing trees retain the original shallower collision
quarters, normally only the lower8px. These conservative base footprints are
not per-pixel alpha and differ from the earlier grove's diagnostic16×8 roots.
Keeping the original forest bands is deliberate: sparse bare trees must not
open an alternate way around a key gate, item pocket, bridge or room exit.
Dead branches reveal actual local floor between roots, while that forest
stand remains an impassable dense stand. This is the remaining conservative
collision/art tradeoff to review in future generator work.

## Native layers and sorting

BG2 carries real stored/adjacent/stage-appropriate floor at priority3. Exact
upper16px tree halves occupy BG1 at priority1; exact lower16px halves occupy
BG3 at priority2. Tree roots can repeat every16px vertically. A tree's upper
half therefore overlaps the previous row's lower half through hardware alpha,
without erasing the neighboring pixels or compositing new source tiles.
Reserved events, entrances, bridges and other authored overlays keep their
pixels and approaches. Exterior index zero always reveals the true floor.
At protected features, an upper band can be hidden to preserve the feature.
Broad pictures never straddle two cells with different protection decisions;
a narrow form fits that boundary instead. Some shortened tree silhouettes
remain beside protected openings. They are disclosed as an engine clearance
tradeoff rather than represented as complete unobstructed source pictures.

The BG3 world map uses screenblocks12–15. Its space is reserved by a hard
768-subtile forest atlas limit; UI charblock2, BG0 and existing BG1/BG2 maps
retain their slots. Trees consume no OBJ slots. Actor sorting uses the source
y=30 ground anchor and a small spatial root-owner lookup. Bloom's existing
native visibility guard queries actual foreground pixels, preserving partial
readability beneath foliage. Background shadows remain below the trees.
The first walking pilot exposed false priority3 sorting behind unrelated BG1
ground foliage. A tree's transparent bounding corner must not demote an actor
behind every lower world plane. Priority3 now requires actual source alpha in
the actor's intersection with a near tree's lower half. Exact32-bit source
alpha rows make this a few row-mask tests, avoiding an expensive per-pixel
VRAM scan. Nearby broad-owner cells are deduplicated in the spatial lookup.
The native visibility guard also admits priority3 and combines existing
general canopy coverage with actual source-owned BG1/BG3 pixels before
copying the unchanged lower-body fragment. Blank tile zero is not an occluder
merely because its map entry contains palette bits. No pose, action clock or
collision behavior changes in these corrections.

`room_render` reuses the same live planted scene and reconstructs all three
world maps. Its cache key is seed, cell and room dimensions; actual room loads
reset it through `tiles_load`. Cutting a bush does not change a neighboring
tree's form when a menu closes. Local interactive redraws reapply cached tree
entries. Map previews suppress room rendering and never modify the live tree
scene. Menus temporarily return
BG3 to screenblock22; room return reconstructs world maps. Leaving the forest
disables and restores the ordinary hidden/menu BG3 configuration.

## Review ABI

`ForestTree` is an8-byte record: signed world canvas x/y, frame, flags and two
original collision nibbles. Width, form, state and anchors come from packed
source metadata. `gForestTreeRoots` maps each physical base cell to a one-based
owner. `gForestTreeStats` records counts, stage, clipping and redraws.
`forest_trees_plan()` performs no hardware write or Room mutation, allowing
host geometry checks against actual generation and collision. Host callers
which directly generate a new test room without `tiles_load` must explicitly
call `forest_trees_reset()` before asking for a fresh plan. Captures also
retain literal native maps, source atlas/palette and last actual scroll writes;
the write-only GBA scroll registers are not falsely treated as readable state.

The initial healthy whole-room mGBA pilot confirms the production density and
true grass contact. Independent geometry/runtime/capture reports supply the
final finite-case results; this note does not replace those reports or claim
universal coverage.
