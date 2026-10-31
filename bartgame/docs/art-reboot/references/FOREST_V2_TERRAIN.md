# Forest v2 terrain — five unselected infection studies

This local pass implements the user's new forest feedback. It supersedes the
first studies' restrained blight **for these optional profiles**, rather than
silently rewriting the shared art bible or any profile0–5 history. The requested
change is dramatic: black deadwood with glowing saturated purple/fuchsia veins,
little surviving green, much filthier anatomy, and visibly diseased grassy
footing. The healthy basic turf remains useful and readable.

`art/forest_concepts_v2_terrain.py` is new. Old painters remain unchanged. The
user-favored healthy canopy constructions1/3, healthy trees1/5, hollow/thicket
walls1/3 and cave walls1/4 are native anchors, chosen locally per option.
`forest_concepts_v2_props` owns interactive objects and the larger fallen log;
this module owns terrain, standing deadwood, canopy edges, leaf projection and
raised root spans. The selected Bloom/enemies/Heart, equipment/OBJ banks, Drain,
interface and existing glitter remain outside this authoring scope.

## Basis read

Before authoring, this pass read the root `AGENTS.md`, `ART_BIBLE.md`,
`ART_DIRECTION_LOG.md`, `REFERENCE_REGISTER.md` and the prior forest source
notes. The already recorded G01–G18 guidance remains the native discipline:
filled silhouette before detail, deliberate value groups, cool shadows and
warm selected light, material-led texture, no pillow bands, native curves,
scene/silhouette/grayscale review and exact integer enlargements. The user's
new black/purple direction is direct feedback, not attributed to a newly
accessed article. No new web reference or missing PDF figure is claimed.

Every pixel is authored on its final canvas. There is no high-resolution
image reduction, blur halo, screenshot grading or imported reference-game
pixel. Healthy anchors reuse their already native drawing vocabulary while
all sick crowns, deadwood, cankers, floor tufts, tall grass and ledges are new.

## Five directions, not five recolours

| Local / build profile | Direction | Disease construction |
| --- | --- | --- |
| **1 / 6 — Black Sap Oak** | Favored rounded oak canopy and rooted tree. | Split coal-black forks; a thick branching purple sap fracture and a wet bracket on heavy bark. |
| **2 / 7 — Violet Strangler** | Broad beech canopy and orchard-like healthy crown. | Violet constrictors turn around swollen knots and a bent trunk; cut-open half turns rather than a universal wire mesh. |
| **3 / 8 — Witchfire Weep** | Rounded living mass becomes a broken, hanging anatomy. | Long black bark sheaths and interrupted purple weeping wounds; hooked limbs and hanging charged cambium. |
| **4 / 9 — Amethyst Canker** | Beech mass and rooted oak carry broad dark plates. | Bulky ruptured abscesses and sheared charcoal collars, with purple living tissue inside irregular black wounds. |
| **5 / 10 — Royal Bruise** | Favored orchard crown and thorned branch pockets. | Black thorn forks, short arterial joins and attached violet/pink parasite pods; no free-floating loot-like motes. |

These remain alternatives. Native anatomy, wood/vein route and wound type vary,
not only the palette. The current API uses local variants1–5; integration owns
mapping those to opt-in build profiles6–10.

## Black wood, diseased ground and native glow

The `blight` BG bank uses near-black wood8, charcoal planes9–11 and very little
living green12. Violet halo5, saturated purple body6, pink-white core7,
fuchsia13 and hot pink14 describe attached wounds. The halo is an authored
2–3-ink native contour/core, not a filtered bloom. White is concentrated in
short core segments; entire branches do not become white outlines.

The first mutable source draft failed its own scene review: cropped long veins
made diagonal wire rows. A second draft replaced these with per-cell wounds,
but repetition still resembled glowing wallpaper. The final construction is a
coherent32px black-wood mass with larger irregular wounds; four world-aligned
macroquadrants and adjacency silhouettes preserve that continuity. The engine
must select `@q0`–`@q3` consistently from world coordinates. None of the rejected
mutable pilots is relabelled as final evidence.

`decay_mix` owns bald/cankered grassy floor. Desaturation, short connected soil
patches and bent dead tufts make it sick while preserving a quiet navigable
mid-value. It is neither a purple carpet nor a bright floor-vein lattice.
Strong neon stays primarily on wood, wounds and attached cankers. Disease
floor and tall grass do not pulse or blink like pickups.

## Adjacency and real depth

`paint_adjacency(parent,mask,corners,phase,variant)` accepts exposed side bits
N1/E2/S4/W8. Concave corner bits are NW1/NE2/SE4/SW8 and apply when both touching
cardinals connect but the diagonal does not. `parent@q0`–`parent@q3` select the
continuous32px canopy mass; an optional `quadrant=` keyword is equivalent.
Each8px quarter depends only on its two touching sides and its corner, enabling
whole-family tile deduplication.

Canopy silhouettes return **transparent0 outside the raised mass**, not an
opaque green rectangle. The engine owns the real floor underneath, preserving
grass, dirt or water at the edge. A small opaque contact shadow describes the
near side. Fully SOLID `forest_blight_tree0`–`5` wallskins retain dense visible
wood backing: exposing a floor-looking void across their blocked footprint
would be a collision lie. Ordinary FLOOR crowns and placed root components
instead retain transparency outside their actual branch/root anatomy. The six
retired `btree_6`–`11` floor contracts remain opaque sick turf.

`fringe(parent,mask,variant)` uses **touching** canopy bits N1/E2/S4/W8. Its true
transparent foreground canvas projects at most2px in central north columns4–11,
with6–7px hanging tips at the outer flanks,3–4px at the sides, and only a tiny
southern contact rim. Real roll inspection found that a full6px central fringe
could combine with the opaque base canopy to hide the entire low rolling body.
The central2px header and transparent lower lane correct that coverage without
removing the partial walk-under edge effect. It can partly occlude Bloom's head and
brush while leaving the central route and feet readable. It never fills the
floor in its transparent areas. Existing meaningful interactive overlays win;
engine integration owns BG1 priority and actual foreground behavior.

`arch_group(variant)` is a native transparent32×16 raised woody root span.
It has an upper root surface, interwoven lower root and contact ends, with
walkable floor beneath. Its upper surface is scenery, **not** a second
walkable level or a claim of multi-level physics. Engine rendering determines
true walk-under ordering; the source image alone does not prove it.

Ledges have a grassy raised lip, a material-dark vertical face, broken stone
seams and a separate lower contact shadow. A one-pixel line cannot substitute
for visible height. Pits remain recessed, dark cavities, not raised ledges.

## Rounded isolated pools and water compatibility

Named outer/corner water tiles and all47 mixed topology cases call the same
water painter. The all-four-exposed case is one rounded native pool with a
single continuous bank, rather than four compounded border strips or a cross.
Lily and foam isolated cases share that pond body. The complete exterior is
transparent0: isolated pond render aliases belong on BG1 over the actual or
inferred local BG2 ground. Using healthy grass ink11 in those corners produced
a false16px green rectangle on dirt and sick grass; the source three-floor
inspection caught and corrected that before freezing. Interior bank/body and
lily/foam pixels are unchanged by the correction. Other water and waterfall
construction preserves the favored earlier treatment. Coherent river bridge
placement and topology belong to the engine, not a painted screenshot.

## Real palette breathing, not source-only motion

`pulse_palettes(variant)` returns four authored16-ink RGB555 states of the
**BG blight bank only**. `PULSE_INDICES` explicitly lists permitted changing
inks5/6/7/13/14. All grass, bark, stone, OBJ, UI, Drain and protected glitter
colours remain invariant. `palette(bank,variant)` is state0 exactly.

The engine applies these states only while playing v2 forest/mystery areas
and restores the correct palettes after menus and area transitions. This gives
real glow to static one-frame trees without pretending that inspection-only
extra image phases animate at runtime. Already animated canopy/wound surfaces
may additionally use their retained native local phase changes. Source pulse
GIFs hold frames for inspection; their180ms review holds are not engine timing.
Static-tree geometry remains phase0 in those source scene pulse GIFs.

## API and review evidence

The module exposes `RECIPES`, `BANKS`, `supports`, `paint`, `palette`,
`paint_adjacency`, `fringe`, `arch_group`, `pulse_palettes` and `PULSE_INDICES`.
BG bank names stay `ground`, `foliage`, `water`, `stone`, `blight`, `decay_mix`,
`rot_water`; no new bank is requested and no global `R.PALETTES` is mutated.
Protected carried-object aliases remain integration-owned.

Native source evidence is generated in
`/workspace/setup/forest-concepts-v2/terrain/`: paired living/deep240×160 source
assemblies,3× nearest-neighbour views, grayscale values, native standing-tree
anatomy and exact-colour source pulse GIFs. These are **source assemblies**,
not actual mGBA frames. Packed BG budgets, real palette restoration/foreground
ordering, isolated-water topology and protected-history comparisons must be
verified by the parent integration and independent actual-ROM audit.

Direct authoring checks cover all469 owned terrain phase instances in each of
five variants, valid16×16 indexed canvases, RGB555 banks, unchanged material
inks across all four pulse states, mixed side/corner API cases, transparent
fringes and native32×16 arch shapes. No build, commit or push is performed by
this terrain authoring task.
