# Forest studies, second pass

The user's detailed review calls for much stronger disease: blackened wood,
bright purple living veins, filthy growth and sparse surviving green. Healthy
grass/dirt and favored canopy/tree constructions remain anchors. New native
art, topology-aware joins and foreground projection are reviewed together.
These alternatives are unselected; ordinary builds still select forest0.

| Review option | Build profile | Direction |
| --- | ---: | --- |
| 1 | 6 | Black Sap Oak |
| 2 | 7 | Violet Strangler |
| 3 | 8 | Witchfire Weep |
| 4 | 9 | Amethyst Canker |
| 5 | 10 | Royal Bruise |

## What changes

- Sick grass, completely new infected/dead tree anatomy and charcoal canopy
  masses with attached native purple/pink glow. Healthy anchors draw from
  preferred canopy1/3 and trees1/5; interiors use the preferred constructions.
- Ten wooden chest designs, two per option, with real hinged open states;
  five simple pressure buttons, five different web constructions, infected
  thorns and a large unmistakable single keyhole.
- Taller shrine/relic markers and two-cell logs with real placement clearance.
- Fifteen forest character forms, five per existing Hermit/Nun/Gardener role,
  with matching native48px portraits and compact world silhouettes.
- Forty-seven water/canopy adjacency cases, rounded isolated cells, transparent
  floor joins, canopy overhangs, a real root underpass, clearer ledge faces,
  and correct common floor restoration after barrier removal.

Bloom, chosen enemies/Heart, equipment/pickup art, the Drain and selected
interfaces remain context. Native OBJ banks and existing glitter stay intact.
The second pass changes some conditional room rendering/generation behavior,
not merely pixels: see [topology contracts](FOREST_TOPOLOGY.md). It does not
claim a fully walkable two-level bridge system.

## Build

```sh
make -j4 BART_FOREST=6 BUILD=build-forest-v2-1 TARGET=forest-v2-1
make -j4 BART_FOREST=7 BUILD=build-forest-v2-2 TARGET=forest-v2-2
make -j4 BART_FOREST=8 BUILD=build-forest-v2-3 TARGET=forest-v2-3
make -j4 BART_FOREST=9 BUILD=build-forest-v2-4 TARGET=forest-v2-4
make -j4 BART_FOREST=10 BUILD=build-forest-v2-5 TARGET=forest-v2-5
make -j4  # production forest0 remains the default
```

Prior explicit profiles1–5 remain available. Current controls, run saves and
appearance preferences retain their established meaning. The two wooden forms
share loot value; selection changes their drawing without consuming RNG.

## Design record and evidence

- [Terrain and authored glow](art-reboot/references/FOREST_V2_TERRAIN.md).
- [Props, chest range and markers](art-reboot/references/FOREST_V2_PROPS.md).
- [Fifteen characters and portraits](art-reboot/references/FOREST_V2_FOLK.md).
- [Renderer/generation integration](art-reboot/references/FOREST_V2_ENGINE.md).
- [Living art direction](art-reboot/ART_BIBLE.md) and [decision log](art-reboot/ART_DIRECTION_LOG.md).
- [Second-pass review](../../art-review/forest-concepts-v2/README.md).

Source atlases and layered assemblies are labelled separately from actual
mGBA recordings. Natural generated rooms and deliberately constructed renderer
diagnostics also have separate labels. Exact native PNGs are authoritative;
source review holds do not pretend to reproduce gameplay timing. Final frozen
builds, runtime results and host-generation evidence accompany the gallery.
