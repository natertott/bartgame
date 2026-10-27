# Blighted Forest atlas pass

The blighted terrain uses the supplied atlas's blue-violet foliage, mossy
stone, purple earth, luminous fissures, pools, crystals and twisted trees.
`art/ref/tile_art/blight.webp` is the higher-resolution original of the same
atlas; `art/ref/blight-reference.jpg` preserves the supplied screenshot.
The atlas's example room is a visual reference, not a replacement map.

## Asset pipeline

`art/blight_reference_source.py` extracts native 16×16 materials and the
32×48 tree, with transparent silhouettes for growths and props.
`art/blight_reference.py` applies the final blight materials after the
existing forest painter. Source colours are reduced to the GBA's 4bpp
material palettes and RGB555 display; large source illustrations cannot
retain every detail at this size.

The existing grass-transition masks are retained around patches of decay.
Tree branches, roots, crystals and mist use the terrain underneath them;
their source backgrounds are not painted into rectangular prop tiles.
The healthy shared stump retains its original rendered pixels. A separate
blighted stump is selected in transitional and deep rooms.

Cosmetic metatiles are appended after the established IDs. The blighted
pit keeps the original pit's hole type and collision mask; the blighted
stump keeps the original stump's type and mask. Eight quiet fissure
variants break up the former repeated trail glyph. Six solid tree parts
frame at most two clearing edges in each deep room, replacing complete
2×3 blocks of existing solid canopy and masonry. They add no blocked
ground and never cover an event overlay. The final `roomgen_build` skin
pass selects these after generation, spawn placement and map marks,
without consuming layout RNG. Walkable cracked earth
remains a floor, and glowing pools retain their existing harmful surface
behaviour. No new route, reward, combat or progression rules are introduced.

## Reproduce and inspect

From the game directory, with the configured ARM toolchain and mGBA Python
environment active:

```sh
make -j4
python art/blight_reference_source.py /tmp/blight-source.png
python tools/blight_review.py /tmp/blight-new --seed 6
```

For matched comparisons, retain the old ROM, linker map and generated
`assets.h`, then capture both builds with the same navigation fixture:

```sh
python tools/blight_review.py /tmp/blight-old \
  --rom /path/to/old.gba --map /path/to/old.map \
  --assets-header /path/to/old-assets.h --seed 6
python tools/blight_review.py /tmp/blight-new \
  --match /tmp/blight-old/capture.json
```

PNG files are unmodified 240×160 mGBA framebuffers. The fixture navigates
the actual generated rooms, clears enemies and ambient firefly actors,
heals Bloom and settles the camera. It synchronizes the animation clock,
then runs 64 video frames
before capture. It does not replace terrain or paint a screenshot.
GIFs sample 96 actual video frames at every other frame and enlarge 2×
without smoothing. GIFs use a shared reduced palette if necessary; PNGs
preserve the original framebuffer colours.

## Scope and gameplay verification

`tools/blight_scope_probe.py` decodes the real ROM's 4bpp tiles, quadrant
flips and RGB555 palettes. It compares every animation frame of retained
forest, Drain and mystery-room artwork, all sprite sheets, item palette tables and the
opening bitmap against the prior build. This avoids treating changed
palette-bank or tile indices as visual changes.

`tools/surface_compare.py` compares the actual generated tile contracts,
solidity grids and spawn records in 75 rooms against the prior ROM.
`tools/surface_probe.py` checks transparent props and terrain blending;
`tools/critical_path.py --boss` exercises all three progression items and
the Heart. The optional mystery-room probe is also retained.

The published gallery includes the final ROM hash, reports, matched
captures from two seeds and exact healthy-forest and Drain controls:
[actual mGBA review](../../forest-review/blight-reference/README.md).
