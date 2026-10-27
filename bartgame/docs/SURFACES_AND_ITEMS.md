# Surface blending and clean item art

This revision addresses two independent readability problems in the generated
forest and the interface. [The review gallery](../../forest-review/polish/README.md)
contains matched native mGBA views and the new item art in the running game.

## Keep the floor separate from the prop

Previously a rock, trunk, chest, or patch of bones was an opaque ground tile
with a grass/rot background baked into its material palette. Placing it on a
different floor produced a rectangular island; even matching grass could
shift colour through another material's quantized palette.

`metatile_prop` now identifies transparent prop art. `Room.underlay`, appended
after the original Room fields, retains the floor the prop covers. BG2 draws
that exact floor and BG1 draws the transparent material. Logical ground IDs,
types, collision quarters and seeded spawn decisions remain authoritative.
Meaningful overlays, such as tree crowns and event furniture, retain their
priority; incidental sparkle/mist does not replace a material prop.

Lifting/cutting exposes the stored floor. Open chests and lit censers retain
their substrate. Mixed blight paints the floor underneath props and selects
side **and diagonal corner** transitions, with a wider grass/sick/bruise
fringe. The underlay costs 2 KB of working RAM; it is not serialized into saves.

Material draw ordering also distinguishes standing in front of a solid prop
from standing behind it, and ground-level debris must not cover character
faces. The surface probe inspects both terrain VRAM and sprite priorities.

## Plain item silhouettes

`art/clean_items.py` supplies the active art after the imported sprite pack.
The inventory, HUD, pickups, item-get, resident sword/shield and arrow sheets
use consistent simple silhouettes and restrained material colours. No icon
contains a decorative frame or halo. Existing UI panels, hero animation art
and enemy art are retained.

All 55 affected frames keep their original names, order and dimensions.
The existing gear/items/pick/icons palette slots are reused, and projectile
arrows map to the existing effects palette. No extra OBJ palette is needed.

## Reproduce the review

```sh
source /workspace/setup/activate.sh
make -j4
python tools/surface_probe.py
python tools/items_review.py /workspace/art-review/items
python tools/generation_review.py /workspace/art-review/forest --seed 0xB4A7
python tools/menu_probe.py
python tools/wood_probe.py
python tools/myst_probe.py
```

For a matched older build, `items_review.py` accepts `--rom` and `--map`.
`surface_compare.py --before-rom ROM --before-map MAP --out report.json`
compares actual logical tile contracts, solidity grids and spawn records
across three seeds. Render colours and cosmetic floor overlays are excluded
from the physical comparison.

Item UI review uses a full-inventory render fixture. Its item-get view earns
Blightseeds by completing the generated plate trial and opening the reward
chest. The separately labelled icon catalogue is a source-asset preview;
the HUD, menu and item-get pictures are actual 240×160 mGBA framebuffers.
