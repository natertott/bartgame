# Adaptive forest canopy: native art authoring

Status: ten review directions, not a selected production style. The previous
fixed crown studies are not a source for these drawings. This note records the
new art contract; actual room and emulator evidence must be reviewed alongside
the source sheets.

The room shape comes first. The composer identifies the connected blocked
forest, finds space inside it, and chooses a composition that fits. A large
region should contain a large tree with connected woody anatomy and unequal
crown masses. An isolated fragment gets a sapling, broken stem or root with its
own small drawing. It must not get a cropped hero tree or an enlarged small
crown. The 16-pixel gameplay grid remains; it no longer dictates the visual
scale of every tree.

## Native drawing contract

All pieces start on their final indexed canvas. No high-resolution source is
downsampled, and no small crown is resized to produce another role. The atlas
uses 8×8 hardware cells, with the following placement extents in 16-pixel cells:

| Role | Native pixels | Placement cells | Purpose |
| --- | --- | --- | --- |
| small | 16×16 | 1×1 | isolated sapling, stem or stump |
| clump | 32×32 | 2×2 | compact growth with visible wood |
| tree | 48×48 | 3×3 | medium tree anatomy |
| grove | 64×64 | 4×4 | connected larger stand |
| hero | 96×64 | 6×4 | large, unequal trunk/fork/crown composition |
| branch | 64×16 | 4×1 | horizontal projected limb; transparent ground below |
| roots | 32×16 | 2×1 | small root/understory attachment |
| border | 96×32 | 6×2 | purpose-drawn shallow connected bough system |
| column | 16×64 | 1×4 | narrow attached stem and foliage |

These nine rectangles total 304 raw 8×8 cells before transparent and flip
deduplication. Final residency is verified by the asset packer; this raw count
is not a claim about the complete game's atlas usage.

The previously authored tree obstacles keep their 32×48 and 48×64 footprints.
They receive new drawings through `authored_tree`, rooted at the bottom centre.
Their backgrounds remain transparent. They are separate from full blocked
canopy rectangles and do not silently change a root obstacle's physical size.

## Ten structural directions

| # | Direction | Primary tree form |
| --- | --- | --- |
| 1 | Ancient Oak Vault | stout crooked bole, unequal long lateral forks |
| 2 | Crooked Willow | leaning bole, broad arc, short attached drooping sprays |
| 3 | Buttress Beech | broad flared roots, upright bole and bark ribs |
| 4 | Woven Bower | two unequal crossing woody stems with distinct forks |
| 5 | Fungal Cathedral | low leaning bole, unequal attached shelf growths |
| 6 | Fallen Crown | fallen trunk and large branching root/fork structure |
| 7 | Lightning Cleft Oak | deeply divided dominant trunk |
| 8 | Pale Birch Congregation | unequal pale stems arranged as a stand |
| 9 | Black Cedar Cathedral | dark conifer form with horizontal branch tiers |
| 10 | Sorrow Arch Elm | swept, curved trunk with long lateral canopy |

Violet infection follows the wood and attached growth. It should reveal the
tree's construction rather than replace it with an independent neon symbol.
The major bole and limbs are thicker and quieter than the twigs. Pointed leaf
fans and unequal crown planes break a continuous scalloped roof. A stronger
warm plane on the new wood inks was added after source critique because the
glowing vein initially read before its supporting limb.

Fungal Cathedral was redrawn after its first source sheet: adding caps to the
oak did not provide enough structural distinction. The current drawing has a
low diagonal, stepped bole and separate native layouts for its small, medium,
large and authored-tree roles.

## Depth and material

One new 16-ink RGB555 bank, `canopy_adaptive`, serves the new geometry. It has
transparent ink 0; outline 1; wood 2–4; changing leaves/underbrush 5–7; surviving
greens 8–10; wound/glitter 11–14; and fungal/pale bark 15. Existing non-canopy
palettes, including the accepted gray diseased ground, remain separate.

Four depth rows change the material of the same anatomy. Healthy leaf inks
become desaturated and then dead plum; bark/dew marks become violet wounds.
The surviving green inks remain green. Four pulse rows change only 11–14.
This avoids doubling the native geometry atlas just to represent disease.

The user's roughly 80/20 diseased/living direction applies across a stand, not
as a quota inside every small fragment. Do not add one equal green oval to
every cell. The ten current hero source drawings have approximately 12–24%
surviving-green pixels among their leaf/underbrush inks; that measurement is a
source diagnostic, not a whole-room vegetation or screen-color claim.

## Depth, alpha and blocked-space honesty

Blocked canopy pieces have a continuous, quiet understory inside their full
placement rectangles. Large empty-looking ground holes inside an impassable
rectangle would teach the wrong collision rule. Small organic outer alpha
margins are retained. The room composer must respect the actual component's
boundary silhouette so this backing cannot repaint a rounded boundary as a
hard square. Quiet backing is not a second layer of bright repeated leaf icons.

Projected branches have transparent surroundings and may extend over clear
walkable ground. They must not completely hide Bloom. Authored trees likewise
have normal transparent surroundings. A drawn alpha bound, a placement extent
and a gameplay collider are different things and must be checked together.

## Source and room review

Native source sheets show anatomy, materials and exact sizes. A nearest-neighbour
inspection enlargement is labelled as an enlargement, and never presented as a
new asset. Source assemblies are labelled source assemblies. Actual generated
placement, collision coverage, healthy/deep room composition and emulator
captures remain separate evidence. The first source critique accepted the new
trunk/fork hierarchy and unequal-size assembly as suitable for the actual-room
gate; it did not approve a final game-wide style.

The first actual profile 19 room review confirmed that the large native forks,
trunks and unequal scales survive at 240×160. It exposed a separate contact
problem: residual tiles formed a bright repeating wave, and the quiet backing
made roots and the bottom of large patches look like rectangular planter boxes.
The focused correction keeps the tree anatomy, removes that wave and the
automatic paired green pads, and gives blocked backing unequal shallow native
contact notches with sparse low-contrast tufts. Boundary aliases likewise use
unequal two-to-four-pixel contacts while preserving their convex/concave cases.
The second actual-room pass must assess this correction before final review.

Thin solid forest arms use `blocked_branch`: a separate 64×16 native map with
the same long limb and quiet organic backing. The ordinary branch remains
transparent for projection over walkable floor. This extra packed map does
not change the nine-role selection contract or turn a projection into a wall.

The module is `art/forest_canopy_adaptive.py`; styles 6–10 delegate native drawing
to `art/forest_canopy_adaptive_b.py`. The public boundary is `prefab`,
`prefab_specs`, `authored_tree`, `quiet_fill`, `blocked_branch`, `stage_palette`, and
`pulse_palettes`. A dimension/index check covers 90 prefab drawings and 40
authored-tree variants. This check does not substitute for watching the room
in mGBA.
