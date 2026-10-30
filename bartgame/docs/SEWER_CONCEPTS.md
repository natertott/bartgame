# Drain art concepts for selection

The current [third-pass gallery](../../art-review/sewer-concepts-v3/README.md)
responds to the user's component-by-component feedback on the second pass.
Its five new treatments keep exploring the preferred #1 frog and #5 wizard;
neither actor is fixed across all five rooms. Floors, damaged walls, water,
ladder markers, stalls and storage are reconsidered together. The shared
[direction log](art-reboot/ART_DIRECTION_LOG.md) records the feedback and review. Game/art source `22b0af6` passes all 22,125
packed/runtime checks, with 88 fresh mGBA cases and eight playable study ROMs.

The [reference-led second pass](art-reboot/REFERENCE_APPLICATION.md) reauthors
all five sets from the six uploaded PDFs. The shared [art bible](art-reboot/ART_BIBLE.md),
[decision log](art-reboot/ART_DIRECTION_LOG.md) and [source register](art-reboot/REFERENCE_REGISTER.md)
record the reasoning continuously. The published first study remains the
before reference; new source/value/silhouette comparisons and actual-run
captures are generated rather than relabelling old media.

[Open the regenerated second-pass gallery](../../art-review/sewer-concepts-v2/README.md)
for every option, native before/after comparisons, actual mGBA recordings and
eight playable builds. The game/art source is `476d1ed`; all 21,971 static and
runtime checks pass. The normal released room remains unchanged during selection.

These are native-GBA comparison builds, not a selected replacement for the
released room. `BART_SEWER=0` keeps the current Step-and-cut release intact.
The [review gallery](../../art-review/sewer-concepts/README.md) provides full
room assemblies, real mGBA views, complete inventories and five alternatives
for each Drain-specific asset.

## Fixed construction

The Drain remains 30×20 cells, 480×320 pixels. Metatiles remain 16×16; hardware
tiles remain 8×8. Ground, foreground, collisions, type/prop flags, animated
frame counts/speeds and the four object anchors keep their existing contracts.
The bridge, market, stream, ladder, wizard and spawn keep their positions.
Bloom uses the selected Step-and-cut animation unchanged. Existing glitter
drawings, emitter rules, placement metadata and viewport budget remain intact.

All new pixels start on these native canvases. Sixteen indexed inks per
hardware bank use RGB555 colours. Enlarged review images use nearest-neighbour
scaling. A 480×320 source room assembly displays the scrolling map at once;
the actual GBA screen is 240×160 and shows part of that map.

## Five material and character directions

| Option | Direction | Design emphasis |
| --- | --- | --- |
| 1 | Ashlar & Amber | Broad running-bond gray brick, worn brass and the closest preferred actor anchors. |
| 2 | Crooked Brickwork | Unequal old brick courses, patched market canvas and lopsided characters. |
| 3 | Floodworn Flags | Long worn setts, narrow pouring water and a timber-canopied market. |
| 4 | Crumbling Vault | Chipped flags, decayed masonry, ragged cloth and broken-lip water. |
| 5 | Silted Cloister | Denser herringbone paving, worn orderly brass and compact pointed-cowl wizard. |

These are shape/material studies, not five palette swaps. The material banks
share index roles so components can be mixed without exceeding GBA limits.
Each has an absentminded cartoon frog Peddler, a market and wares, an old
purple-robed wizard, a shadowed hood and a staff-top flame. The Peddler uses
short, concrete phrases; shop prices, stock and ownership rules stay stable.

Recipes 1–5 use one direction throughout. Recipes 6–8 mix floor, masonry,
water, metal, bridge, market, sanctum, props, Peddler and wizard choices.
The exact combinations live in `art/sewer_concepts.py` and the gallery.
Choose an option per component when giving feedback, rather than needing
to select one entire room unchanged.

## Complete scope

The active room has 350 ground IDs plus 20 foreground IDs, placed 657 times.
Their 623 native frame drawings include 38 animated tile IDs. The keeper
sheets retain 29 original world animation frames, plus two 48×48 portraits.
The second pass appends a fifteenth Peddler body pose, `breathe`, making
30 world keeper frames. It coordinates the existing one-pixel head bob with
upper-body compression while leaving the bottom three foot rows unchanged.
The original action-frame IDs and live streamed body allocation remain stable.
The review separately inventories 80 unused named sewer catalogue tiles.

A new 16×8 decorative rail sprite joins the north-bank posts. It uses two
resident OBJ tiles and the existing gold palette, with a clear opening at
the bridge. Keeping this handrail in a separate foreground layer avoids
repeating it across walkable floor cells that share background tile IDs.
It changes neither the room's physical layout nor its glitter surfaces.

Repeated IDs remain reusable material panels: arbitrary crops from a large
fixture would repeat its corners elsewhere in the room. Only declared
animated metatiles move in gameplay. Foreground silhouettes and transparent
apertures must continue to agree with the room's collision and depth rules.

The shared HUD, menus, merchandise icons, font and conditional item effects
belong to the common game art. They are listed in the inventory for context.
The concept comparison focuses on Drain world materials, fixtures, keepers
and their matching portraits.

## Reproduce

```sh
# Current released room and selected Step-and-cut sword.
make -j4

# One complete Drain concept.
make -j4 BART_SEWER=3 BUILD=build_sewer3

# A mixed recipe.
make -j4 BART_SEWER=6 BUILD=build_sewer6
```

Freeze the ROM, map, generated header and coverage report together before
capturing. `tools/sewer_concept_review.py` records real mGBA views and
`tools/sewer_concept_gallery.py` assembles source art comparisons. Each
presentation identifies its source, timing and any capture fixtures.
`tools/sewer_concept_audit.py` independently decodes the frozen ROM pixels and
verifies the unchanged assets and room contracts against the default build.
