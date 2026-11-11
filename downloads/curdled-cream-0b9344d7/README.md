# Curdled Cream release

- [Download ROM](https://raw.githubusercontent.com/natertott/bartgame/handoff-restoration-curdled-cream/downloads/curdled-cream-0b9344d7/bartgame-0b9344d7.gba)
- [Download ROM ZIP](https://raw.githubusercontent.com/natertott/bartgame/handoff-restoration-curdled-cream/downloads/curdled-cream-0b9344d7/bartgame-0b9344d7.zip)
- [Download frozen build and native evidence ZIP](https://raw.githubusercontent.com/natertott/bartgame/handoff-restoration-curdled-cream/downloads/curdled-cream-0b9344d7/native-evidence.zip)
- [Actual emulator gallery, controls and feature audit](../../curdled-cream-review/README.md)
- [SHA256 checksums](SHA256SUMS)
- [Full evidence manifest](evidence-manifest.json)

Source commit: `0b9344d781e65e304d245bd9ae4aecdbc7056837`.

For an earlier save, copy its `.sav` beside the downloaded ROM as
`bartgame-0b9344d7.sav`; mGBA associates SRAM with the ROM's filename.

ROM SHA256:
`b348cf4d628aee1abb9b71d8885a9f04094332c5252490ff2dd8f8e7cd0bf1b8`.

Normal production flags: `PROFILE=0`, `ENEMY_LAB=0`, selected `BART_SWING=3`,
`BART_FOREST=32`, `BART_HUD=1`. The standalone game needs no commercial ROM.
Build from the `bartgame/` subdirectory using `make -j4`, with
`arm-none-eabi-gcc`/binutils, Python/Pillow and `tools/bin/gbafix` on the expected
paths. The exact compiler invocation and build log are in the evidence ZIP.

The evidence archive contains the exact ROM/ELF/linker map/generated asset
header and source identity, all release-native reports and their untouched
PNG/GIF/audio outputs, separately labelled C host reports, old-art preservation
results and the matched baseline performance report. Private SRAM, save states
and duplicate fixture ROMs are excluded. `manifest.json` hashes every included
file; the adjacent manifest is the same data. A source commit pins game code;
the later publication commit adds documentation, final harnesses and artifacts.
