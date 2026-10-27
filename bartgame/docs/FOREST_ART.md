# Forest art direction

The reference is `art/ref/board_forest.jpg`: blue-green foliage, olive turf,
warm earth, deep blue water, gilded details and violet corruption. The
visual progression preserves the game's generated stages: living wood,
stained grass, sick patches, then bruised violet earth and ruined masonry.
Gold, pale petals and luminous wounds are small accents against dark matter.

`art/forest_art.py` is the final forest/interior art pass after `env_pack`.
It uses the existing terrain painter's edge families and object silhouettes,
new native-resolution foliage, trees, dead trees, crystals, earth, masonry
and room-event props, with a forest-specific set of material palettes.
It deliberately excludes every `sw_` and `swh_` tile. The hero, item art,
Drain keepers, HUD, menus and title retain their original art and palettes.

`art/forest_sprites.py` draws the rot scarab, spore moth, sediment slime,
predatory lily, tarnished knight and rooted reliquary Heart. It preserves
all sheet dimensions, animation names and facing/frame ordering. Only the
enemy palette groups (`bugs`, `blight`, `iron`) change.

The extra canopy and blight-floor variants are applied at the end of
`roomgen_build`. Their choice comes from coordinate hashes, after all
placement and spawn decisions, so the original RNG stream is preserved.
The replacements have identical tile types and quarter collision masks.

## Build and review

From this directory:

```sh
source /workspace/setup/activate.sh
make -j4
python tools/forest_review.py /workspace/art-review/current --seed 0xB4A7
python tools/wood_probe.py
python tools/myst_probe.py
python tools/critical_path.py --seed 0xB4A7 --boss
```

The review tool boots the actual ROM in mGBA and captures native 240x160
framebuffers. Debug room transitions inspect all 25 procedurally generated
cells and one naturally generated mystery of each available style. It
records the seed, ROM SHA256, cell/stage, and hashes of runtime collision
and spawn contracts in `capture.json`. No screenshot terrain or actors are
composited outside the game. Screenshots remain generated review outputs.

For a baseline comparison, pass `--rom PATH --map PATH` with a matched
original ROM and linker map. Compare per-cell `geometry_sha256` values and
`drain_control.png` pixels. On seed `0xB4A7`, all 25 collision/spawn contracts
and every Drain control pixel matched the pre-change build.

The asset builder enforces the hardware budgets: at most 1024 8x8 terrain
subtiles and 12 material palettes per area, 15 opaque colours per palette,
and unchanged sprite bounds. Do not replace these constraints with larger
preview-only artwork.
