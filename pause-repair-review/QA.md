# Pause display regression: actual mGBA evidence

Both runs use the real mGBA core and frozen ROM/source bundles. The screenshot
files are native 240×160 output; `-3x.png` files use nearest-neighbour enlargement.
No artwork was reconstructed for these screenshots.

| Run | Source | ROM SHA-256 | Result |
| --- | --- | --- | --- |
| Before | `48a39a9a1c0dc3fe1a0eb4fa563219eab0d104f6` | `98d1dce7d1fa78d64a537688d44872b78e9a012585584081820a23edb2f9842e` | Both reported bugs reproduced |
| Fixed | `9080b7e1d32e1b344722fcd6f89acefe1e621160` | `9b3c24cf17088a335c7efeaf2d49aacb627abb43569987a050decf910f6a5f5f` | 30/30 focused checks pass |

## Inventory acquisition and first pause

Seed 1, real opening draft selections `(1,0,0)`, awards Mole Mitts (19),
Heart Container (98), and Peril Beam (79) through normal gameplay. The tool
does not assign inventory, health, completion flags, rewards, palettes, or
video output. It confirms owned-item visibility independently by reading
hardware OAM and comparing the actual OBJ pixels and palette to the frozen
ROM's corresponding item frame.

Before: the newly earned Mitts are absent from the first pause; the later
Satchel workaround displays them. The two newly earned passive items are
also absent from the initial Keys screen.

Fixed: the Mitts appear on the first START, have initial selection, and real
A, B, and L inputs equip them. Both new passives display on the Keys page.
Cycling pages and reopening the pause menu retain item visibility.

Images: `fixed/inventory/first-pause.png`, `fixed/inventory/new-passives.png`, and
`before/inventory/later-satchel-workaround.png` relative to this gallery.

## Atlas graphics lifetime

The run opens the actual Cream overview and zoom, moves to Satchel, and
closes the menu. Before: charblock 2's blank, HUD hearts, and native UI kit
are all overwritten, and the world retains repeated gold glyph artifacts.
Fixed: every one of those bytes matches the pinned ROM; all 5,504 borrowed
icon/HUD OBJ bytes and all 512 live OBJ palette bytes restore exactly. No
subsequent queued upload corrupts them again.

The test also compares all 32,768 world-ground character bytes, masking only
the documented native animation destinations. Static ground characters above
the 600-character menu range remain intact. Exact native BG2 composites and
read-only snapshots of actors, room/topology, inventory, and progression stay
unchanged during pause. It returns through the actual Cream and Forest ladders
and repeats Forest map/inventory checks; Sewer resident HUD/UI also survives.

Images: `fixed/graphics/atlas-zoom.png`, `fixed/graphics/satchel-after-atlas.png`,
`fixed/graphics/returned-to-world.png`, and `fixed/graphics/forest/after.png`.
The baseline world example is cell0; the fixed example uses the surveyed
most-loaded cell18. They demonstrate the same menu round trip in different rooms.

## Scope and reproduction

The fixed run surveys all 25 ordinarily generated Cream rooms of seed 1,
then exercises the largest native OBJ allocation scene. Its world OBJ heap
is 438/876 tiles, with no allocation failures. Opening pause adds no heap
allocation. This does not claim an artificially exhausted heap or an exhaustive
all-seed test. Ordinary room-load and hero-navigation fixtures are disclosed
in the input trace; actual gameplay spawns and rewards are left intact.
Native inventory pagination with more than seven owned items was not forced
by assigning inventory; the separate host catalogue tests cover that case.

```sh
source /workspace/setup/activate.sh
python3 tools/pause_inventory_capture.py --bundle /workspace/setup/cream-selected/frozen --out /workspace/setup/pause-repair/baseline --baseline
python3 tools/pause_inventory_capture.py --bundle /workspace/setup/pause-repair/frozen-r1 --out /workspace/setup/pause-repair/fixed-r1 --survey
```

Machine-readable assertions, fingerprints, native resource snapshots, and
input traces are in each run's `report.json` and section folders.
