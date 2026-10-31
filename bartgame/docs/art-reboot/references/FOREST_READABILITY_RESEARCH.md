# Forest readability: native game evidence and original adaptations

Read and inspected on 2026-10-31 UTC for the five optional forest concepts.
The current user brief is the direct authority: retain recognizable forest,
green grass and brown earth even in deep blight; communicate corruption mainly
through ecology, structure and local accents; keep the playable field quiet;
and clearly distinguish permanent boundaries from temporary interactions.
These requirements are not attributed to Nintendo or an external article.

The six previously read tutorial PDFs and G01–G18 remain the common art basis.
This follow-up adds fresh primary-source study. It does not introduce another
art pack or import any reference pixels into the game.

## What was actually examined

Two repositories were fetched at pinned revisions through the configured
network proxy:

- Pokémon Emerald, `pret/pokeemerald` revision
  `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881`.
- The Minish Cap, `zeldaret/tmc` revision
  `6fb6dfb4a7efbe24d0fd1dda5097af6131faacde`.

The Emerald general native tile PNG, its metatiles/attributes and six primary
palettes were decoded. The 48×44-cell Petalburg Woods layout was reconstructed
using its actual General/Rustboro tilesets, all thirteen loaded source palettes,
map entries, tile indices, palette-bank indices and flip bits. Relevant source
code confirms two groups of four 8×8 tiles per 16×16 metatile. This is a static
**source reconstruction**, not a real emulator screenshot: there are no actors,
live tile animations, darkness effects or gameplay assertions in that image.
Palette channels were reduced explicitly to their upper five bits for the
RGB555 inspection image. The source renderer does not establish another game's
live OAM priorities or the complete appearance of an animated water surface.

The native source contacts, reconstruction code, complete fetch/hashes manifest
and measurements remain outside the production repository at
`/workspace/setup/forest-concepts/research/`. They are research aids, not BARTGAME
assets or falsely labelled game captures. Only this original analysis and its
upstream citations belong in the project documentation.

Emerald's cuttable tree, breakable rock and pushable boulder source PNGs were
also viewed in their original indexed preview palettes, at native and integer
zoom sizes. Their 16×16 frame dimensions were cross-checked against the object
graphics declarations. Their source preview colors are not claimed to be the
live OBJ palettes in every map. Minish Cap's bush and pot implementations were
read for object identity, collision, removal, carrying and terrain response;
commercial Minish Cap forest graphics are not present in that clean project,
and no exact Minish Cap forest pixel measurements are claimed.

## Visual and measured findings

| Inspected source | Evidence | Original BARTGAME adaptation |
| --- | --- | --- |
| Emerald Petalburg Woods native terrain | A small repeated tree vocabulary forms connected boundaries around broad grassy clearings. The same crown construction remains recognizable throughout the source layout. | Limit each concept to a coordinated tree/shrub family. Change leaf mass, branch structure and canopy edge direction rather than mixing unrelated trees in one room. |
| General grass metatile `001` | The static source reconstruction uses three colors; 220/256 pixels (85.94%) share one base ink. Sparse small clusters provide texture. | Keep a dominant, quiet walkable field. Retain green/brown material identity through all blight stages. Do not copy its visible dotted repeat or treat 85.94% as a universal quota. |
| Tall grass metatile `00D` | Four colors and denser repeated blade silhouettes; its dominant color occupies 89/256 pixels (34.77%). Its source behavior is explicitly tall grass, unlike ordinary grass. | Dense texture should mean a deliberate region or object, not fill every walkable tile. Decorative blades must not resemble cuttable bushes, drops or traps. BARTGAME does not acquire Pokémon encounter rules. |
| General tree-to-grass transition cells | Distinct edge pieces combine the same leaf shape with surrounding grass. Petalburg's forest walls read as massed vegetation rather than a vertical stone wall repeated around every side. | Share transition inks and consistent edge clusters. Show raised crown overhang, lower contact shadow and identifiable trunks; keep direction-specific north/side/near edges. |
| Cave entrance cells `09F`/`0A7` | The source opening has a dark recessed void and a visible stone frame; the bottom cell has an entrance/warp behavior. In the static diagnostic its mean luma is 66.78 versus grass's 173.50, using the recorded `(54R+183G+19B)/256` metric. | Give hollow/cave/thicket entrances a large dark aperture, legible framing and a clean approach. Surface decoration must not fill the aperture. These sample values are comparative diagnostics, not fixed game palette targets. |
| Cuttable tree first pose | A distinct 16×16 entity, with 15×15 nonzero-index bounds, a compact rounded crown and a small visible trunk. Four source frames change its silhouette during cutting. | A functional bush/tree is one self-contained connected object, separated from the background canopy by contour, contact shadow and a different shape scale. Keep it recognizable during lift, carry, throw or cut. |
| Breakable rock first pose | A 16×16 entity with 14×14 nonzero-index bounds and a conspicuous branching fissure. The four-frame source sheet uses five colors overall. | Bombable blocks get a deep branching crack, exposed pale fracture planes and a bounded, removable silhouette. Ordinary environment rocks must not casually reuse that fissure. |
| Pushable boulder | A whole 16×16 faceted body using five colors, without the breakable rock's branching fissure. | Heavy liftables and bombable obstacles differ in structure, not merely color or glitter intensity. No false fracture should promise an unsupported bomb interaction. |

Measured bounds exclude palette index zero; dimensions above are painted extents,
not hitbox measurements. The two rock sources use the same small color count:
the different silhouette and material construction carry their interaction
meaning. The source forest is a measured example, not proof that every GBA game
uses its exact tree sizes, ground texture or palette arrangement.

## Mechanics and layering evidence

- Emerald's [metatile renderer, lines 226–307](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/field_camera.c#L226)
  selects primary/secondary metatile records and explicitly places bottom/top
  groups into split, covered or normal background layers. Art must be tested
  with actual depth, rather than assuming every tall tree image can simply sit
  in front of Bloom. BARTGAME keeps its own renderer and collision contracts.
- [Field-map getters, lines 326–354](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/fieldmap.c#L326)
  distinguish collision, metatile identity, behavior and layer type. A painting's
  dark pixels alone do not establish solidity or accessible space.
- [Player collision, lines 693–758](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/field_player_avatar.c#L693)
  treats ledge jumps and pushable boulders separately from ordinary collision;
  surfing additionally considers elevation. BARTGAME ledges therefore need a
  readable drop face/direction; ordinary path edging must not mimic that face.
- [Water/bridge behavior, lines 773–818](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/metatile_behavior.c#L773)
  distinguishes bridges over water and their edge cases. The source comments
  explicitly say bridge portions outside water use normal behavior. Separate
  [shallow-flowing water, lines 879–888](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/metatile_behavior.c#L879)
  and [surfable water, lines 280–286](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/metatile_behavior.c#L280)
  definitions show why decorative liquid should not promise unsupported access.
  BARTGAME's forest water should have continuous banks, coherent ripple groups
  and believable bridge landings. A harmful pool, pit and safe path need
  different material signatures even if all are dark.
- [Cut setup, lines 142–153](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/fldeff_cut.c#L142)
  checks the specific cuttable-tree graphics ID. [Rock Smash setup, lines
  119–139](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/fldeff_rocksmash.c#L119)
  checks the breakable-rock graphics ID. These confirm a distinct authored
  visual vocabulary for tool targets; they do not prove a particular designer's
  intent or prescribe identical objects for BARTGAME.
- Minish Cap's [bush, lines 50–119](https://github.com/zeldaret/tmc/blob/6fb6dfb4a7efbe24d0fd1dda5097af6131faacde/src/object/bush.c#L50)
  caches the underlying tile, installs a blocker and restores the old tile when
  removed. It has explicit hitbox geometry and separate state handlers. A
  temporary bush should read as an object on the ground, not a torn fragment of
  the permanent boundary. The `6,6` hitbox initializer is not its painted size.
- Minish Cap's [pot, lines 112–190](https://github.com/zeldaret/tmc/blob/6fb6dfb4a7efbe24d0fd1dda5097af6131faacde/src/object/pot.c#L112)
  restores its ground tile, registers carrying and distinguishes water splash,
  falling and lava responses. Its [break handler, lines 305–317](https://github.com/zeldaret/tmc/blob/6fb6dfb4a7efbe24d0fd1dda5097af6131faacde/src/object/pot.c#L305)
  creates shatter effects then removes the object. BARTGAME liftables should
  retain one silhouette/material through standing, lifting, carrying and
  throwing; fragments belong to the break event rather than normal idle art.

## Rules for all five forest alternatives

1. **Forest identity comes before blight.** Recognizable leaves, trunks, grass,
   soil and shrubs survive every stage. A color change alone is insufficient:
   expose dead branches, climbing parasites, sparse pale fungus, wet bark or
   bruised blossom groups on the existing family. Keep green/brown continuity.
2. **Use three visual roles.** Quiet mid-value, low-contrast walkable ground;
   darker raised, connected permanent vegetation/rock; bounded, readable objects
   with stronger contour/contact shadow and selective light accents. Do not give
   every floor fleck an object-like black outline or gold sparkle.
3. **Concentrate detail.** Preserve clear approaches and usable combat space.
   Attach filth and glitter to identifiable surfaces; place bright blight on
   roots, canopy wounds, petals, pool margins or meaningful objects, not a purple
   blanket that erases the field. Reuse a small family of leaf/flower clusters.
4. **Tool meanings survive style changes.** Branching fracture = bomb target;
   connected pale silk/dry tangled brush = candle target; a genuinely recessed
   void with visible banks = jump crossing; single clear lock/keyhole = key gate;
   broad raised/depressed face = switch. Do not put these marks on permanent
   fixtures or unrelated ornament.
5. **Entry points are functional silhouettes.** Dark opening taller than Bloom,
   readable top/side material frame, threshold and unobstructed approach. Avoid
   hiding a doorway with crown foliage or elaborate symmetrical decorations.
6. **Water belongs to a feature.** Continuous bank, coherent moving ripples,
   deeper interior and a clear near lip. Bridges span actual water/pits and meet
   usable ground; holes use near-black depth without water glints. The forest's
   cleaner water can retain teal/blue rather than inherit sewer murk.
7. **A held prop is the same prop.** Check grounded and lifted bushes/rocks/pots,
   chest closed/open tiers and plate up/down states together. Preserve existing
   physics, paint anchors and legal hardware canvases.
8. **One system, five original expressions.** Vary crown silhouettes, leaf-cluster
   rhythm, bark structure, parasite placement and material highlights, while
   sharing interaction semantics and quiet-ground hierarchy. These remain
   optional studies until the user selects one. Selected enemies, Bloom, HUD,
   item icons and Drain artwork are comparison context, not new enemy proposals.
9. **Judge real scenes.** Review native color, grayscale, complete groups and
   live animation on healthy, mixed and deep-blight backgrounds. Verify grass/
   dirt joins, tree feet, water banks, occlusion and interactables in actual mGBA
   views. Label source assemblies separately from actual captures.

These are original adaptations consistent with G01/G02/G05/G06/G09/G11/G12/G15/
G18, the adopted Drain interaction vocabulary and the current user brief. No
review rating, developer quotation or inferred exact Minish Cap tile size is
presented as evidence.

## Pinning and selected content hashes

The local `pinned-fetches.json` records every fetched URL, status, byte count
and SHA256. Representative byte identities are listed here so the analysis can
be checked without committing another game's assets.

| Upstream file (at the pinned revision above) | SHA256 |
| --- | --- |
| `pret/pokeemerald/data/tilesets/primary/general/tiles.png` | `365ba5482e7564763e614a0009900d1c317790dcd9f7a06c4ab74c363a3ba2f5` |
| `pret/pokeemerald/data/tilesets/primary/general/metatiles.bin` | `17974b0ba1bb9d105d5ba255c69a3b80d8484a26ea0b8ff22c6c6567c6c22910` |
| `pret/pokeemerald/data/tilesets/primary/general/metatile_attributes.bin` | `06c9548a6c70d133b6d47638090f5d36f3fec92aace3d90deca758a4404cfa9b` |
| `pret/pokeemerald/data/layouts/PetalburgWoods/map.bin` | `053fc2e64d7065edaf0bfaa4b7504fef15ad808dc458f8b937cb3a2604495442` |
| `pret/pokeemerald/graphics/object_events/pics/misc/cuttable_tree.png` | `7777b5b630cb9a430d1313e6d9603a6e2e4829c5954f08dc1f11b4a0a4f5eac1` |
| `pret/pokeemerald/graphics/object_events/pics/misc/breakable_rock.png` | `accf417ec0b1958af56e2964eda5dadd1ba97a52def6bbf6057d11f4a02be316` |
| `pret/pokeemerald/graphics/object_events/pics/misc/pushable_boulder.png` | `9ff11e929fbc9c221dd5228e342be51a04b19591b7248ad12aa698e60221e663` |
| `zeldaret/tmc/src/object/bush.c` | `9187cabaa865761eeb51cafbb476ddb7a6471d704532ae2a85402fa078623bdf` |
| `zeldaret/tmc/src/object/pot.c` | `39b9ce0207a29c39f73c6158bc1dea1e180100cc75c0d3e07b9bda7646a7906d` |

Source graphics declarations: [cuttable tree](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/data/object_events/object_event_graphics_info.h#L1559),
[breakable rock](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/data/object_events/object_event_graphics_info.h#L1635),
[pushable boulder](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/data/object_events/object_event_graphics_info.h#L1654).
The [layout record](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/data/layouts/layouts.json#L1344)
identifies Petalburg Woods dimensions and its General/Rustboro pair; the
[renderer header](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/include/fieldmap.h#L4)
records its tile/metatile counts. Failed guessed paths for a separate
`petalburg_woods` tileset and alternate object filenames were not used as
sources. Source metadata established the correct actual paths before analysis.
