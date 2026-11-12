# Native source drawings

These are original indexed game drawings and inspection atlases, not emulator captures. 16×16 metatiles use sixteen-color RGB555 banks; large illustrations are drawn directly at32×32,64×32,96×32,64×48 and128×48 before literal splitting. Enlarged sheets use nearest neighbor only.

`native-source-atlas.png` shows the seven complete native wall masters at each corruptionstage. `backing-source-native.png` shows the continuous quiet128×48 rock. `edge-source-native.png` shows raised/open rims, side returns, wall/floor toes and landing shade. `terrain-source.png` covers the142 existing Cream tile roles in the selected treatment. `source-inventory.json` and `manifest.json` retain names, contracts and exact palettes. New appendix contains375 visual-only Cream metatiles; all earlier IDs are retained.

Reproduce with BART_CREAM=6 and art/cream_depth_assets.write_review(), art/cream_terrain.write_review(). No Nintendo pixels are included. See the viewed reference note for art principles and source limits.
