# Five forest environment studies

These alternatives respond to the user's forest-first brief. Healthy, mixed
and deep forest keep green grass and warm dirt. Blight comes chiefly from
leaf loss, broken limbs, parasitic vines and local flowers/fungi. Ground
texture stays quiet, with dark raised canopies, banked water, recessed pits,
strong interaction silhouettes and a limited kit of repeated vegetation.

| Profile | Direction | Local construction |
| --- | --- | --- |
| 0 | Current production | Preserves the selected-enemy release. |
| 1 | Fern & Oak | Rounded broad crowns, ferns and warm timber. |
| 2 | Silver Willow | Drooping crowns, pale lichen and light trim. |
| 3 | Copper Beech | Broad leaves, warm copper/bark and clustered growth. |
| 4 | Velvet Cedar | Layered conifer fans, cool shade and tarnished fittings. |
| 5 | Pale Orchard | Knotted fruit-tree forms and pale parasitic growth. |

The five alternatives remain **unselected**. Bloom, selected enemies and Heart,
equipment/pickups, interface, Drain architecture/keepers and glitter keep their
established source pixels and behavior. Optional studies also redraw shared
portable objects, large chests and entrances so their world/carry/open states
remain coherent; those object drawings are shared across areas in a study ROM.
No generator layout, room shape, item rule, collision or AI change is intended.

## Build a comparison

```sh
make -j4 BART_FOREST=1 BUILD=build-forest-1 TARGET=forest-study-1
make -j4 BART_FOREST=2 BUILD=build-forest-2 TARGET=forest-study-2
make -j4 BART_FOREST=3 BUILD=build-forest-3 TARGET=forest-study-3
make -j4 BART_FOREST=4 BUILD=build-forest-4 TARGET=forest-study-4
make -j4 BART_FOREST=5 BUILD=build-forest-5 TARGET=forest-study-5
make -j4  # production forest, selected enemies, Drain, interfaces and sword
```

Native art uses indexed 16×16 metatiles and legal OBJ canvases. BG-only palette
aliases preserve ground/carried prop colors without changing shared OBJ banks.
Types, collision, prop flags, glitter attachment and animation clocks stay
stable. Existing saves and controls remain compatible.

## Evidence and design record

- [Complete asset inventory](art-reboot/references/FOREST_ASSET_INVENTORY.md).
- [Fresh primary-game readability research](art-reboot/references/FOREST_READABILITY_RESEARCH.md).
- [Terrain construction](art-reboot/references/FOREST_TERRAIN_CONCEPTS.md).
- [Interactive objects](art-reboot/references/FOREST_PROP_CONCEPTS.md).
- [Forest folk and matching portraits](art-reboot/references/FOREST_FOLK_CONCEPTS.md).
- [Shared art bible](art-reboot/ART_BIBLE.md) and [direction log](art-reboot/ART_DIRECTION_LOG.md).
- [Review gallery](../../art-review/forest-concepts/README.md).

Source atlases/catalogs and actual mGBA views are labelled separately. The
review uses matching naturally generated layouts and discloses seed, player,
equipment, health and camera fixtures. Fixed source inspection holds do not
represent AI or damage timing. Native PNGs are the authoritative pixel view;
integer enlargement is only for inspection.
