# Imported item and shield artwork

`art/reference_items.py` extracts the actual pixels from the supplied
`items-reference.jpg` and `shields-reference.jpg` screenshots in `art/ref/`.
It removes the opaque checkerboard, including enclosed holes and neutral
JPEG edge ringing, and preserves coloured highlights and intended glints.
Nearest-neighbour scaling retains the illustrated pixel clusters.

The 5×4 item sheet maps to the engine's existing item names. The shield
sheet supplies front, side and back views for the round wooden shield and
the green-and-gold shield. Large icons fit 32×32 frames; small items and
held shields fit 16×16 frames. Each keeps a transparent one-pixel margin.
The sword, map and astrolabe retain their existing drawings because the
new sheets do not supply replacements for them.

## Colour and rendering

Normal gameplay retains four existing OBJ palette slots, 9–12, with material
ramps for wood/metal, purple/gold, treasure, and green/wood. Each frame has a
generated palette-bank entry. These entries are used by the HUD, pickups,
planted bombs, shop, item-get, shields and Bloom's action layer.

The paused inventory has an individual 15-colour palette for each large
icon. Its eight-slot LRU cache borrows actor palette slots 0–7 while actors
are hidden. The actual world palette contents are saved and restored, so
portraits and animated keeper colours survive the menu. The world is drawn
again immediately when the menu closes. No OBJ allocation is added by
these palettes or by the extra shield design.

`art/reference_assets.py` installs the imported frames after the existing
art overrides. Bow, lantern and cape action sprites use transformed source
pixels at the existing hand/body anchors. The diagonal source arrow is
rotated for the game's cardinal projectile directions. The bomb's warning
frame recolours its imported body while retaining its shape and fuse.

## Shield variants

The wooden shield is the starting design. Both designs have large inventory
icons and three small views. Only the current small view is streamed into
the original shield tile reservation. `ITEM2_SHIELD_UPGRADE` uses bit `0x10`
in the existing ownership byte, and `player_shield_upgrade()` selects the
green-and-gold design. The save layout and version are retained.

This artwork update does not assign the upgrade to a new chest or quest.
The green-shield review sets its ownership flag explicitly to show the
supported renderer, inventory and HUD variant.

## Reproduce

```sh
source /workspace/setup/activate.sh
make -j4
python art/reference_items.py /tmp/reference-items-preview.png
python tools/reference_items_probe.py /workspace/art-review/reference-items
python tools/bloom_budget.py --out /workspace/art-review/reference-budget.json
python tools/bloom_probe.py --out /workspace/art-review/reference-bloom.json
python tools/menu_probe.py
python tools/title_probe.py --out /workspace/art-review/reference-title
```

The item probe captures real 240×160 mGBA frames. Full inventory, upgraded
shield ownership and the ten-item ground display are labelled fixtures;
tool actions use real button inputs and the Blightseeds reward is earned
by completing the generated plate trial. Exact icon pixels and palette
words are compared in actual GPU memory, including repeated page changes
and restoration after closing the menu.

[Actual mGBA review and source catalogue](../../forest-review/items-reference/README.md).
