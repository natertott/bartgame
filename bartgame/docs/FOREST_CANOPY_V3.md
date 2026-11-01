# Leafy canopy studies

The current review accepts grey dead grass and rejects the second pass's
healthy and blighted canopy forms. These eight optional studies begin with
recognizable leafy crowns, forked trunks and broad horizontal boughs, then
apply different kinds of infection. They keep living green leaf groups at
every depth, aiming for roughly twenty percent across deep canopy masses.

| Review option | Build profile | Infection treatment |
| --- | ---: | --- |
| 1. Veinbound Oak | 11 | Branching purple veins follow leaf and branch structure. |
| 2. Patchblight Beech | 12 | Necrotic patches interrupt the leaf planes. |
| 3. Spore Drift | 13 | Local dithered spore clusters and attached purple light. |
| 4. Bracketwood | 14 | Shelf fungi grow from lateral boughs. |
| 5. Violet Leaf Mosaic | 15 | Diseased violet leaves sit among surviving green. |
| 6. Black Sap Bough | 16 | Wet dark sap follows forks and short drips. |
| 7. Silkbound Crown | 17 | Parasitic silk connects portions of the crown. |
| 8. Canker Bloom | 18 | Ragged luminous cankers flower on intact tree forms. |

The non-canopy environment uses forest profile6 as fixed context: accepted
grey ground, water, props, characters and portraits retain its artwork. The
maze generator is unchanged, including the pending lantern-placement work.
Bloom's native artwork, action timing and physics stay intact, as do selected
enemies/Heart, equipment, interfaces, Drain architecture and existing glitter.
Earlier profiles0–10 and the production default0 remain available.

Overhead foliage may cover Bloom's upper body but must preserve a recognizable
part of his current silhouette. A conditional foreground fragment uses only
existing pixels from his current body frame; it keeps the lower portion
readable while branches retain real occlusion. It adds no new player poses or
rectangular opening in the scenery. Intentional hurt blinking and the existing
fall/death disappearance retain their meanings. Source diagrams alone do not
prove this behavior; actual mGBA movement is required for review.

Build a study with, for example:

```sh
make -j4 BART_FOREST=11 BUILD=build-canopy-01 TARGET=canopy-01
make -j4 BART_FOREST=18 BUILD=build-canopy-08 TARGET=canopy-08
make -j4  # ordinary forest0 remains the default
```

All art is authored at native GBA sizes and RGB555 limits. One additional
BG-only canopy bank supplies infected leaf planes and living greens without
recoloring the accepted ground or other materials. Approximately twenty
percent green is a mass-composition guide, not a per-tile quota. Large crowns,
isolated cells, connected bands and concave joins need separate inspection.

[Terrain authoring](art-reboot/references/FOREST_V3_TERRAIN.md) ·
[Depth implementation](art-reboot/references/FOREST_V3_DEPTH.md) ·
[Shared art bible](art-reboot/ART_BIBLE.md) ·
[Decision log](art-reboot/ART_DIRECTION_LOG.md)

The final gallery will separate native source assemblies, naturally generated
mGBA contexts and explicitly constructed renderer diagnostics. The eight
infection treatments remain unselected alternatives.
