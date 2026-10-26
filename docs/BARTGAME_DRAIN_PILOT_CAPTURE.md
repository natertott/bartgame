# BARTGAME Drain pilot: the ROM capture

The reply to `BARTGAME_DRAIN_NATIVE_240x160_GBA_PILOT` (built on engine commit `718efd8`). The pack is kept as delivered in `bartgame/art/ref/drain_pilot/`. Its two source reference PNGs are left out.

## 1. The result

The real ROM draws the pilot exactly.

- Every byte the hardware holds matches the delivered files: the characters, both maps, the BG banks, the OBJ banks, the OBJ tiles and the OAM placements.
- The raw mGBA frame matches `master_240x160.png` to within 1 step of 255 on every pixel.
- Once both sides expand colour the same way, 0 of 38,400 pixels differ.

| Comparison (raw mGBA 240x160) | Tolerance | Pixels that differ | Worst channel difference |
|---|---|---|---|
| Full frame vs `master_240x160.png` as delivered | 0 | 16,674 | 1 |
| Full frame vs `master_240x160.png` as delivered | 1 | 0 | 1 |
| Full frame vs `master_240x160.png` as delivered | 8 | 0 | 1 |
| Full frame vs the master in mGBA's colour expansion | 0 | 0 | 0 |
| BG2 and BG1 vs ground + overlay PNGs, mGBA expansion | 0 | 0 | 0 |
| BG2 vs `ground_240x160.png`, mGBA expansion | 0 | 0 | 0 |

**Why 16,674 pixels differ by 1.** The art is not the cause, and the importer is not the cause. It comes from how a 5-bit channel is shown as 8 bits.

- `verify_exports.py` expands a channel c to `round(c*255/31)`.
- mGBA expands it to `(c<<3)|(c>>2)`.
- The two differ by 1 at c = 3, 7, 24 and 28, for example 25 against 24 at c = 3.

Build the master with mGBA's expansion and the full frame matches it at tolerance 0. Or compare at tolerance 1.

## 2. Importer and build errors

There were none.

- `tools/build_assets.py` takes the pilot byte for byte and stops the build if any check fails:
  - the character file is 659 x 32 bytes;
  - each map is 2,048 bytes, every entry's piece is below 659, its bank is below 13, and no flip bits are set;
  - the BG palette file is 416 bytes and the OBJ palette file 512;
  - each OBJ file is its sprite's tile count x 32 bytes.
- `source/verify_exports.py` passes: "0 mismatched pixels of 38400".
- `source/build_pilot.py` needs OpenCV, which was not installed here. With `opencv-python-headless` 5.0.0.93 it ran in a copy of the pack and rewrote every delivered file byte for byte. `verify_exports.py` then passed on the rebuild.

## 3. How the ROM shows it

`make pilot` builds `bartgame_drainpilot.gba`. It boots straight into the pilot. Start fades to the title, and Select on the title comes back. The main ROM does not have the pilot. The existing Drain hall is untouched.

| What | Where |
|---|---|
| BG characters, 659 with the blank | VRAM 0x06000000, charblock 0, running into charblock 1 |
| BG2 ground map | screenblock 28, priority 2 |
| BG1 overlay map | screenblock 24, priority 1 |
| Map size and scroll | 32x32 while shown (the game's maps are 64x64), scroll (0,0) |
| BG banks | slots 0-12 from `drain_bg_palettes.pal`; 13-15 kept (menu, gold, text) |
| DISPCNT | 0x1640: mode 0, OBJ 1D, BG1, BG2, OBJ; no HUD |
| OBJ tiles | Bloom at OBJ tile 72, Peddler at 88, Gatekeeper at 104 |
| OAM | Bloom 32x32 at (104,65), Peddler 32x32 at (23,48), Gatekeeper 32x64 at (187,48), all priority 2 |

**OBJ palettes were moved.** The game's own colours hold OBJ banks 0-13. The pilot's banks 0, 1 and 2 are loaded into banks 13, 14 and 15, and OAM attr2 is set to match.

- Banks 14 and 15 are free.
- Bank 13 holds the 32x32 folk, whose Peddler and Gatekeeper this scene draws on its own.
- Leaving the pilot puts bank 13 back.

The handoff's example screenblocks 16 and 17 are not free in this engine: they hold the font and HUD characters (charblock 2). So the pilot uses the game's own screenblocks 24 and 28.

No world actors, HUD or collision are present. The pilot is a fixed frame, not a level.

## 4. The capture files

They are in `docs/engine_contract/pilot/`. `tools/pilot_capture.py` writes them all.

| File | What it is |
|---|---|
| `engine_capture_240x160.png` | The raw mGBA frame: BG1, BG2 and OBJ |
| `engine_capture_bg_240x160.png` | BG2 and BG1 only |
| `engine_capture_ground_240x160.png` | BG2 only |
| `master_hw_240x160.png` | The master in mGBA's colour expansion |
| `bg_hw_240x160.png`, `ground_hw_240x160.png` | The pack's layers in mGBA's colour expansion |
| `diff_*.png`, `compare_*.json` | Each comparison in the table above, with mismatches per 16x16 cell |
| `readback.json` | Every hardware check: VRAM, palette RAM, OAM, registers, scroll, fade |
| `sheet_3x.png` | The master, the capture and the diff, at 3x |
| `engine_capture_again_240x160.png` | The pilot again, after Start to the title and Select back. It is identical. |
| `after_pilot_hall_240x160.png` | A run begun after the pilot: the game's own hall, with its VRAM back |

Run it again with `cd bartgame && make pilot && python3 tools/pilot_capture.py OUTDIR`.

## 5. What a whole hall in this style would need

These are budget facts for the next step. They are not changes to this pilot.

- The hall is 30x18 cells and scrolls. Drawn unique like this, it would need up to 2,160 pieces. The BG has 1,023, shared by BG1 and BG2.
- The pilot uses 659 for one screen, so a scrolling hall needs repeated cells.
- The game has 2 free OBJ banks. The Bloom's in-game colours are bank 0 and the folk's are bank 13. Pilot actors in a playable room would have to use those banks or replace them.
