# Independent Cream source/art review

Status: exploratory studies; no style adoption. Read `AGENTS.md`, the shared
art bible, direction log/reference register and Cream art/room contract. No
new external visual reference is claimed. The user brief and existing native
construction/interaction rules are the basis of this review.

The preserved production baseline is candidate4, ROM SHA256
`0dd8554384b53e618140f8c61590fc7e6a7ff0888f296ece034a95f357b34fdd`.
Its Cream bank uses 344/1024 BG subtiles and 10/12 resident palette banks:
eight Cream material banks plus two shared handoff banks. There are142 Cream
metatile IDs and seven resident animation descriptors, including shared art.
The game's 126 sprite sheets already occupy all 16 OBJ palette banks. Existing
Cream sprite canvases are 32×32 and 32×64; the cave composition is 32×48 and the
chest composition 32×32. Palette headroom is tighter than BG tile headroom.

The original material weakness is shallow, repeated horizontal stripes with
similar pale borders on raised rims and committed drops. A convincing drawing
needs a quiet walkable plane, a projecting lip, a darker vertical face and an
attached contact shadow. Climb shafts require a regular artificial handhold
cadence, unlike ordinary rock. Gate silhouettes must retain branching stone
fractures, connected pale fibres, a single lock and visible used/lit states.

## Source comparison at native size

Inspected the artists' native assemblies and larger integer inspections.
These are source drawings, not emulator screenshots.

| Study | Visible construction | Strongest distinction | Remaining concern |
| --- | --- | --- | --- |
| Karst | Rounded ivory shelves, grouped pores, dark undercuts, brass staples | Natural porous/calcite mass, broad solid rim teeth | Repetition can form long bands; complementary cliff halves require matching placement |
| Basilica | Recessed pointed bays, buttresses, cornices and pointed portal | Architectural silhouette and negative space | Repeating dark bays can suggest entrances; paired halves must form complete bays in actual rooms |
| Moldglass | Green angular plates over dark cavities, attached bright facets | Most distinct mineral palette and faceted surface | Deep-stage veins and repeated faceting are busy; inspect enemies and small interactables against them |
| Quarry | Broad dressed ochre strata, rectangular cut portal, metal fixtures | Restrained large planes and regular cut-stone construction | Closest to the original horizontal mountain vocabulary; carved doorway is less organic |
| Rind | Unequal oyster fans, dark wet undersides, rooted mold and short threads | Organic shelves with closed cap contours and mold structure | Closest to Karst in horizontal material rhythm; repeated small fans can resemble masonry at 1× |

All five preserve pale, relatively quiet walking ground through corruption.
Corruption changes drawn plate/shelf matter, cavities and attached seams, not
only bank hues. The shared physical footprint, doorway scale and interaction
language intentionally make them related studies within one game.

An independent API sweep called 149 native drawings per module. Every output
was mode P, index 0–15 and the required native canvas, with eight 16-ink RGB555
banks. Across all 10 study pairs, each measured family has different canonical
geometry after removing arbitrary ink numbering. Full per-family counts are
in `painter-api-check.json`. This excludes a palette-only explanation; it
does not establish that every altered pixel improves the art.

## Placement correction required before relying on source compositions

The legacy room painter chooses cliff variant 1 using
`(((x/3+y/2)&7)==0)`, leaving most panels variant 0 in patches. Karst and
Basilica deliberately cut complementary halves from 32×16 masters. Their source
assemblies pair 0/1; legacy rooms will repeat the left half and occasionally
insert the right. This breaks the intended complete shelves/bays. Root was
notified before freeze and agreed to implement optional paired-column
selection for styles 1/2 with the same existing IDs and unchanged
type/collision metadata. The default profile must retain its previous selection.

Depth in these studies is painted volume. Unchanged collision/type/prop arrays
do not create new heights, walkable upper decks or underpasses. Real mGBA
captures must establish climb/ledge readability, clear approaches, visible
moving characters, stage contrast and actual return-door presentation. Source
assemblies and static pixel comparisons cannot establish those properties.

## Verification tool

`tools/cream_art_study_audit.py` accepts `--baseline`, repeated
`--bundle LABEL=PATH` and `--out`, plus optional exact `--pin LABEL=SHA256`.
It does not build. It pins the baseline above, decodes native 4bpp BG/OBJ data,
applies quarter flips/palettes, compares complete source animation frames,
checks native budgets and preserves all existing identifiers, physics/props,
glitter, non-Cream BG paintings, all OBJ sheets, title/HUD/font/palettes and
resolved original music descriptors/complete PCM. Native assemblies generated
by the tool are explicitly marked as ROM-decoded source assemblies.

The optional `--allow-cream-return` exception permits only Creamdoors return
frame 2 to change; the other two door frames, sheet descriptor, frame IDs and
existing iron OBJ bank remain exact. Root explicitly authorized this narrow
exception. The baseline self-comparison passed 975/975, including source-file
snapshot stability. Final frozen-study results remain pending root's serial
builds.

## Semantic findings before the final freeze

The first source pass incorrectly pictured a keyhole on several capability
wards. Those wards require gifts, not a small key. Root identified this
meaning mismatch and chose three luminous sigils within each study's existing
gate frame. The change must also appear on cave-ward lower tiles.

The independent follow-up found index-zero corners on Moldglass, Quarry and
Rind pressure-switch ground tiles: 73, 38 and 44 pixels respectively. Unlike
alpha props, these plates are ordinary FLOOR metatiles. Root was notified that
opaque subdued backing avoids apparent holes. Quarry/Rind unlit lamp art also
retained a flame or bright window; a true off state should differ clearly from
the TORCH_LIT state. Natural Cream generation currently places lit lamps, but
the resident unlit family still needs trustworthy semantics.

`native-first-three.json` records the superseded initial ae30ba11 freeze and
passes 2953/2953 checks. `native-default.json` separately proves its style 0
binary equals the preserved production ROM. These earlier files do not
qualify the later semantic corrections; final evidence will name the later
source pin and exact ROMs explicitly.

Final source 4966dab4 resolves these findings through the optional study
dispatcher: three luminous gift sigils replace each keyhole, zero-valued plate
corners receive a complete stone plinth, unlit Moldglass/Quarry/Rind lamps have
dark interiors or no flame, and the dominant Rind floor loses its repeated
bright corner block. The underlying artist source files remain separate study
ingredients; the dispatcher-normalized `cream_terrain.METATILES` is the actual
source compared to the final ROMs. Default profile 0 bypasses these wrappers.

## Final frozen native audit

Final `style-0-r2` through `style-5-r2`, pinned to source 4966dab4, pass
**5983/5983** independent checks in `native-audit.json`. The report records
each complete ROM SHA256, map/header hashes, source-file hashes and exact
source-commit comparisons. Default 0's ROM is byte-identical to candidate4.

| Direction | Cream BG subtiles /1024 | Palette banks /12 | Verified Cream frames |
| --- | ---: | ---: | ---: |
| Original | 344 | 10 | 148 |
| Karst | 400 | 10 | 148 |
| Basilica | 381 | 10 | 148 |
| Moldglass | 400 | 10 | 148 |
| Quarry | 375 | 10 | 148 |
| Rind | 408 | 10 | 148 |

Each bundle's 142 Cream metatiles/148 frames independently match the actual
dispatcher-normalized indexed source, including all moving water/fall phases.
Every metatile ID, collision/type/prop/glitter byte, original frame/sheet ID,
non-Cream painting and protected sprite remains exact. The only changed OBJ
frame is the authorized Cream return doorway; its source pixels match, its
padding/canvas remains legal, and the original iron bank stays untouched.
Fonts, HUD, title, timing arrays, original music PCM and resolved song records
also remain exact.

For all 10 pairs among the five directions, every one of the 142 metatile
drawings has a different canonical index geometry and internal colour-boundary
pattern after ink renumbering. The 15 comparisons including Original are in
the report. This establishes broad family redrawing beyond palette swaps.
Opaque floor/cliff/climb silhouettes intentionally retain their full-cell
footprints; their differences are internal planes, cavities and surface
clusters. Collision/elevation geometry is unchanged. Difference counts do not
rate beauty, depth readability or successful movement.

`final-semantic-checks.json` independently confirms both switch states have
zero transparent pixels in all five final ROMs. Lit/unlit lamp drawings now
change 12–18 pixels; the count describes distinct frames, while the dark
interior/flame removal supplies their meaning. ROM-decoded atlases are native
source assemblies and retain that label; the separate mGBA review owns actual
room, motion and interaction evidence.

Executed audit script SHA256:
`b711cf40f7916bbc305f091b3094c035d7866a6fb98b235ee93f8bef3769966c`.
Independent native decoder helper SHA256:
`d975c773dfa1ba641169b30fa42128b2a6671d1f1f90ce3fb99b16c4a06d76c5`.
