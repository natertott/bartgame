# Five Curdled Cream environment studies

These are **unselected alternatives**, made for the user's request for a less
flat, more detailed mountain region. `BART_CREAM=0` retains the production art;
`BART_CREAM=1..5` selects a complete native environment study. This is not a
selection of a new default.

| Number | Direction | Material and depth | Navigation vocabulary |
| --- | --- | --- | --- |
| 1 | Curdstone Karst | Rounded ivory travertine/curd shelves, grouped erosion cups, brine stains and dark undercuts. | Recessed brass staples; rooted calcite rim versus open drop notch. |
| 2 | Brine Basilica | Chipped limestone cornices, pointed recessed bays, ruined buttresses and narrow gilt details. | Regular gilt grips separate from architectural ribs; a clear parapet silhouette and dark doorway. |
| 3 | Moldglass Crags | Olive/teal mineral plates, asymmetric facets, damp cavities and violet fractures. | Pale paired handholds in a dark cut shaft; angular permanent rims and bright temporary seals. |
| 4 | Gilt Quarry | Broad dressed curdstone blocks, chisel cuts, ochre/ivory planes, cool shadow courses and bronze fixtures. | Deliberate grip cadence and strong shelf faces; obvious wooden/brass chest, fracture and lock. |
| 5 | Black Rind Terraces | Unequal oyster-fungus shelves, wet black backing, living green seams and purple rotten cavities. | Pale repeated pegs distinguish the climb from irregular fans; blocked caps versus an open edge. |

All five redraw the142 existing Cream metatiles: floor/path variants,
cliff faces and side returns, climb caps/shafts/feet, solid rims/drop notches,
caves, temporary barriers, holes, mold, water/falls, lamps, shrines, switches,
trial markers, supplies, wards and chest states. Fresh/sour/deep states change
both material details and palette; the walking surface stays quieter than the
walls and interactables. Violet remains the corruption/danger ink. Gold and
ivory identify useful contact points.

Every painter starts at its final indexed resolution:16×16 cells,32×48 cave
compositions and32×32 chests. Eight sixteen-color RGB555 BG banks are used.
No high-resolution illustration, filtered scaling, photographic texture or
post-processed emulator image supplies game pixels. Source atlases and source
assemblies remain distinct from native emulator captures.

The Cream return portal uses the selected native cave silhouette with clear
steps and the established down arrow, mapped directly into the unchanged iron
OBJ palette and padded to32×64. Only that Cream-only frame changes. Bloom,
climbing animation, NPCs, enemies, HUD, title, other regions and all other sprite
frames remain. All identifiers, collision/type/prop/glitter metadata, animation
frame counts and speeds remain unchanged.

## Art and placement must agree

Karst and Basilica draw paired32-pixel cliff masters. The original renderer's
rare second variant would repeat the left half and break those forms. Study
builds install their halves with `x&1`; Quarry also alternates its compatible
cut faces. Moldglass and Rind stagger their standalone variants. The exact
same solid type and collision remain under both pictures. Default0 retains
the original variant choice.

The actual upper cliff lip is drawn with `rim`, so depth cannot depend on a
`cliff_top` tile that the room immediately replaces. Rim, middle face and
base all carry the volume. The larger cave is one native composition cut into
its existing six cells. Transparent prop corners show the true floor instead
of an unrelated rectangular backing.

Existing procedural routes, lantern locations, cliff profiles, features and
directed climbing/drop/cave connections are retained for comparison. These
studies do not add incidental ladders or mark ordinary walls as climbable.
A bright grip shaft must correspond to an actual `TT_CLIMB` strip; an open
notch must correspond to the actual drop takeoff.

## Review and limits

Compare the styles on matched seeded rooms before choosing one. Inspect at
native scale, in grayscale and while climbing, especially a pale body against
bright limestone and a dark body against deep recesses. The palette's brightest
clusters belong to contact points and selected glints; detail on the floor is
subordinate to actors and hazards.

Karst and Rind share a horizontal organic rhythm, while Basilica is the most
architectural and Moldglass the most faceted. Quarry deliberately uses broader,
quieter wall masses. The first native review should judge whether each one's
repetition and feature contrast remain clear on the complete generated room,
not only on a source strip. An attractive atlas is not a native gameplay pass.

The [shared art bible](../art-reboot/ART_BIBLE.md) and its tutorial application
rules G01–G18 remain authoritative. This study uses those already recorded
sources and the user's Mount Crenel traversal annotation; it does not claim new
external research or import another game's art.

Review artifacts and exact build/capture identities will be linked from the
repository's Cream art gallery after the native runs finish.
