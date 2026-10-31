# Selected interfaces and enemy comparison ROMs

[Full actual/source gallery, controls and animation comparisons](../../art-review/appearance-enemy-studies/README.md)

[Download the selected-interface game](https://raw.githubusercontent.com/natertott/bartgame/appearance-enemy-studies/downloads/appearance-enemy-5eedc6d/00-selected-ui-existing-enemies.gba) · [Download all eleven ROMs](https://raw.githubusercontent.com/natertott/bartgame/appearance-enemy-studies/downloads/appearance-enemy-5eedc6d/selected-ui-and-ten-enemy-studies.zip) · [Checksums](SHA256SUMS.txt)

The normal game includes title Options, the selected Winebound HUD, Workbench items/keys and the schematic event map. Menu/dialogue frame construction and palette can be mixed independently and survive reset/New Game/Continue. Existing enemy artwork stays in this build while the sixty proposed forms are reviewed.

The ten optional ROMs each pair the same alternative number across all six current enemy behaviors. You can choose different numbers for different enemy families in the final design. Each is the full game with those native artwork/presentation changes. They share the same AI rules, damage, hitboxes and progression.

| Build | Download | Actual recordings |
| --- | --- | --- |
| Selected interfaces, current enemies | [GBA](00-selected-ui-existing-enemies.gba) | [Browse](../../art-review/appearance-enemy-studies/actual/enemies/v0/README.md) |
| Enemy alternatives 1 | [GBA](enemy-study-01.gba) | [Browse](../../art-review/appearance-enemy-studies/actual/enemies/v1/README.md) |
| Enemy alternatives 2 | [GBA](enemy-study-02.gba) | [Browse](../../art-review/appearance-enemy-studies/actual/enemies/v2/README.md) |
| Enemy alternatives 3 | [GBA](enemy-study-03.gba) | [Browse](../../art-review/appearance-enemy-studies/actual/enemies/v3/README.md) |
| Enemy alternatives 4 | [GBA](enemy-study-04.gba) | [Browse](../../art-review/appearance-enemy-studies/actual/enemies/v4/README.md) |
| Enemy alternatives 5 | [GBA](enemy-study-05.gba) | [Browse](../../art-review/appearance-enemy-studies/actual/enemies/v5/README.md) |
| Enemy alternatives 6 | [GBA](enemy-study-06.gba) | [Browse](../../art-review/appearance-enemy-studies/actual/enemies/v6/README.md) |
| Enemy alternatives 7 | [GBA](enemy-study-07.gba) | [Browse](../../art-review/appearance-enemy-studies/actual/enemies/v7/README.md) |
| Enemy alternatives 8 | [GBA](enemy-study-08.gba) | [Browse](../../art-review/appearance-enemy-studies/actual/enemies/v8/README.md) |
| Enemy alternatives 9 | [GBA](enemy-study-09.gba) | [Browse](../../art-review/appearance-enemy-studies/actual/enemies/v9/README.md) |
| Enemy alternatives 10 | [GBA](enemy-study-10.gba) | [Browse](../../art-review/appearance-enemy-studies/actual/enemies/v10/README.md) |

The ZIP contains all eleven ROMs, README.txt, ROM-SHA256.txt and builds.json. No commercial ROM is required. Open a .gba in mGBA.

## Controls

Title Options: Up/Down selects Style or Colors; Left/Right cycles; A/B/Start returns. Gameplay: Start opens/closes inventory, R changes page, D-pad selects, A/B/L assigns a carried tool. Map: A zooms, B returns to overview; D-pad browses. Minimap and relevant equipped ammunition remain on the compact HUD.

## Provenance

Frozen game/art source: `5eedc6dae94d8c1ea21c55b8668435bcf0be884d`. [Exact build commands and source hashes](builds.json) · [ROM SHA256](ROM-SHA256.txt).

```sh
make -j4
make -j4 BART_ENEMY=1 BUILD=build_enemy_1
```

The normal defaults are BART_SEWER=9, BART_SWING=3, BART_UI=6, BART_MENU=1, BART_ENEMY=0. Settings are changed inside the game; a separate build is not needed for the nine frame/color combinations. Enemy studies remain explicit profiles1–10.
