# Imported title artwork

The opening screen uses the supplied screenshot at
`art/ref/title-reference.jpg`. `art/title.py` imports the complete image,
resizes it to 240×160 with LANCZOS, and converts the result to RGB555.
The border, lettering, characters, moon, castle, forest and drains all come
from that source image. The artwork is not redrawn or cropped.

The resulting bitmap contains 2,070 colours and occupies 76,800 bytes.
`tools/build_assets.py` stores it as `title_bitmap` in ROM. The source image
is an explicit Makefile dependency, so replacing it rebuilds the asset.
Run `python art/title.py /tmp/title-preview.png` for a native preview,
nearest-neighbour enlargement, and source/conversion hashes.

The title uses GBA Mode 3 to retain the image's shading. During the title:

- BG2 displays the direct-colour bitmap with an identity transform.
- Prompt and save-choice text use high OBJ tiles, outside bitmap memory.
- Hardware brightness handles fades for both the bitmap and text.
- Background map uploads and tile animation stay off to protect the image.

New Game and Continue restore Mode 0, world tiles, UI graphics, fonts and
palettes. Returning from the win screen can enter the bitmap title again.
The subtitle is already in the source artwork, so the former generated
subtitle is removed. The small prompt and save choices sit near the water
to keep the main lettering and source subtitle visible.

## Reproduce the review

```sh
source /workspace/setup/activate.sh
make -j4
python tools/title_probe.py --out /workspace/art-review/title
python tools/menu_probe.py
python tools/bloom_probe.py --out /workspace/art-review/title-bloom.json
```

The title probe checks all 38,400 RGB555 words in actual VRAM, compares
the full unobscured mGBA framebuffer with the imported bitmap, exercises
fresh starts and saved choices, and returns through the real win path.
PNG captures are unmodified native 240×160 framebuffers.

[Actual mGBA review](../../forest-review/title-reference/README.md).
