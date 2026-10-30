# Playable interface and menu studies

[Actual mGBA gallery, videos and design notes](../../art-review/ui-menu-exploration/README.md)

[Download baseline and all fifteen studies](https://raw.githubusercontent.com/natertott/bartgame/ui-menu-exploration/downloads/ui-menu-studies-d113d39/baseline-and-fifteen-studies.zip) · [Checksums](SHA256SUMS.txt)

These optional native GBA ROMs use the same final Drain, forest, Bloom and Step-and-cut. Default UI0/MENU0 stays intact. Each starts as a normal game; review screenshots use disclosed inventory/map fixtures. No commercial ROM is required.

## Five skins, same existing menu layout

| Skin | Download |
| --- | --- |
| 1. Winebound Folio | [GBA ROM](style-01-winebound-folio.gba) |
| 2. Mossbound Fieldbook | [GBA ROM](style-02-mossbound-fieldbook.gba) |
| 3. Ivory Reliquary | [GBA ROM](style-03-ivory-reliquary.gba) |
| 4. Burgundy Archivist | [GBA ROM](style-04-burgundy-archivist.gba) |
| 5. Verdigris Devotional | [GBA ROM](style-05-verdigris-devotional.gba) |

## Ten menu layouts, same Winebound skin

| Layout | Download |
| --- | --- |
| 1. Loadout Workbench | [GBA ROM](layout-01-loadout-workbench.gba) |
| 2. Pocket Ledger | [GBA ROM](layout-02-pocket-ledger.gba) |
| 3. Fieldbook | [GBA ROM](layout-03-fieldbook.gba) |
| 4. Tactical Atlas | [GBA ROM](layout-04-tactical-atlas.gba) |
| 5. Toolwheel | [GBA ROM](layout-05-toolwheel.gba) |
| 6. Twin Atlas | [GBA ROM](layout-06-twin-atlas.gba) |
| 7. Expedition Dashboard | [GBA ROM](layout-07-expedition-dashboard.gba) |
| 8. Focus Cards | [GBA ROM](layout-08-focus-cards.gba) |
| 9. Barrier Index | [GBA ROM](layout-09-barrier-index.gba) |
| 10. Quick Ribbon | [GBA ROM](layout-10-quick-ribbon.gba) |

[Production baseline for comparison](00-production-baseline.gba). The ZIP contains this baseline, all fifteen options, README.txt, ROM-SHA256.txt and builds.json.

## Controls

Start opens/closes. R changes page. D-pad selects. A/B/L assign on the Items page, moving a tool between buttons under the existing rule. Key items cannot be equipped. Map A zooms, B returns to overview. The compact gameplay HUD retains the minimap and equipped-item ammunition.

## Build and evidence

Frozen game/art source `d113d398692e9b98903e5d5a944ea3cadc2d6282`. All 312 actual cases and 1,166 runtime checks pass, plus 7,523 independent preservation/encoding checks. Native screenshots and detailed provenance are in the gallery. The first full terrain atlas has an approximately 0.9 second generation cost; schematic maps are faster.

```sh
make -j4 BART_UI=6 BART_MENU=0 BUILD=build_winebound
make -j4 BART_UI=6 BART_MENU=6 BUILD=build_twin_atlas
```

[Exact per-ROM commands/source hashes](builds.json). Skins use UI6–10/MENU0; layouts use UI6/MENU1–10.
