# Regular forest material pass

The regular forest uses the same small leaf clusters, cool shadows,
warm wood and restrained ground contrast as the atlas-guided blight.
Healthy areas retain green and teal foliage, sunlit tips and living turf;
violet earth and luminous corruption remain visually distinct.

`art/ref/board_forest.jpg` guides the material treatment. This pass is
authored at native resolution in `art/healthy_reference.py`, rather than
presenting the concept illustration as a game screenshot.

## Assets and integration

The final healthy override runs after the existing forest painters and
the blight-reference pass. It refines continuous canopy, oak, birch and
fir sprites, trunks and roots, grass, dirt, pond banks, water reflections,
ferns and litter. Six existing material palettes retain their semantic
slot order: foliage colours stay foliage colours, bark stays bark, and
water stays water. The main grass colours match the retained decay-edge
palette so that healthy and blighted turf can meet naturally.

Shared woodland materials follow the update wherever the forest uses
them, including rivers and bridges in deep rooms and natural surfaces in
forest interiors. The imported blight-specific canopy, earth, masonry,
trees, crystals, fissures, pits and pools are retained. The Drain, item
icons, Bloom, enemy sheets and opening screen are outside this pass.

Metatile IDs, physical types, collision masks, prop flags, animation frame
counts and timing are retained. No room-generation or progression code
changes are needed. The existing terrain underlay and transparent prop
renderer continue to place roots, rocks, litter and growths over their
actual floor.

## Build and inspect

From the custom game's `bartgame` directory with the ARM toolchain and
mGBA Python environment active:

```sh
make -j4
python tools/healthy_review.py /tmp/healthy-new --seed 6
```

For matched comparisons, freeze the old ROM, linker map and generated
`assets.h` before building the new artwork. The capture tool can load
those through `--rom`, `--map` and `--assets-header`, and `--match` reuses
the old standing positions. `--changed-materials` takes an exact material
list and checks that control-frame changes stay within their actual
visible terrain cells.

Native PNGs are unmodified 240×160 mGBA framebuffers. The fixture navigates
real generated rooms, heals Bloom, clears enemies and ambient firefly
actors, settles the camera and synchronizes the animation clock. GIFs
sample actual frames and enlarge 2× without smoothing; they may reduce
colours to the GIF palette limit.

## Verification

`tools/healthy_scope_probe.py` decodes the actual packed ROM artwork,
including palette banks, quadrant flips, transparency and every animation
frame. An explicit list permits regular woodland material changes.
Blight-specific art is always compared, and Drain tiles, sprite sheets,
item palette data and the title bitmap must remain exact. The tool also
checks every metatile's ID, type, collision and prop flag.

`tools/surface_compare.py` compares 75 generated rooms against the frozen
ROM. The surface, critical-path and optional-mystery probes check that
the new art retains prop layering, interactions and progression.

The [published mGBA gallery](../../forest-review/healthy-reference/README.md)
contains matched native captures, animation, the final ROM hash and
validation reports.
