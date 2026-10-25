# BARTGAME GBA Sprite Pack — FIXED, engine-sized

This is the implementation asset directory, not a montage of concept illustrations.
The `sheets/` folder contains 35 real **4-bit indexed PNG strips** at EXACT frame dimensions, palette index 0 transparent. All originally defined 32 sheets remain at their original paths, indices, and frame dimensions.

## What to load

- `sheets/`: flat horizontal strips, zero padding, frames in documented order.
- `frames/`: individually saved native-size indexed PNGs named `000_frame_name.png`, etc.
- `gba_4bpp_tiles/`: optional raw GBA 4bpp 8x8 tiled graphics, frame-major and tile-row-major within each frame. Supports hardware 1D OBJ tile mapping when used with the matching animation entries.
- `palettes/*.gba.pal`: 16 BGR555 little-endian values, 32 bytes per group; index 0 transparent.
- `manifest.json`, `frame_index.csv`, `sprite_frames.h`: authoritative machine-readable mapping.
- `validate_pack.py`: independent validation, needs Pillow.

## Corrections included

1. Original seven incorrectly assigned large illustration files **removed** from runtime paths; all engine-facing filenames now contain correctly sized indexed sheets.
2. Bloom sprite has a stalk, root feet, and leaf-arms (50 original ordered frames, including recovery and north leap). Carry pose now raises the hands above the flower head.
3. Distinct shabby round **base** shield at `shield.png`; polished tree-emblem **upgraded** shield at new `shield_upgraded.png`. New `shield_menu.png` has both menu symbols.
4. Four-faced golden diamond GILT in `items`, `pick32`, HUD, and standalone `currency32`.
5. Corrected old-man Bloom, purple-hide hooked-nose Peddler and violet wizard Gatekeeper portraits, all authored at 32x32.
6. Sister Mary Grace and Brother Mark appended to `npc` (indices 5 and 6) and `portrait` (indices 7 and 8). Original indices are unchanged.
7. HUD A/B/L/R glyphs and bomb icon drawn. Sewer-water indices adjusted to cool aquamarine tones.

## Compatibility notes

- The original engine needs no index changes for its original 32 sheets. Two appended NPCs and portraits require adding IDs if used in-game.
- Additional optional sheets (`shield_upgraded`, `shield_menu`, `currency32`) are not in the original 32-sheet spec, and need explicit game integration.
- Image width reflects a *strip*, not a supported standalone GBA sprite shape. Crop into individual frames or use raw .4bpp data.
- The tile-strip families are **palette-valid, correctly ordered first-pass art**, but the open-ended procedural terrain categories are not guaranteed to be production-quality seamless autotiles. Treat adjacency rules and level composition as an engine/design task.
- Using one palette bank per group is valid for art exports; OBJ and BG palette bank selection and VRAM residency are controlled by the GBA engine. Never load all palettes indiscriminately into one bank.
- Colors conform to 15 opaque colors per bank. The portrait bank was intentionally revised to support red petals, gold, purple, flesh, and green.
- No automatically downscaled 1000+ px illustrations are included in runtime assets. Native pixels are pixel-authored/reconstructed to satisfy the spec; some designs may still warrant a future hand-art pass.

## Typical handoff

Pass this whole ZIP to the implementing agent. Point the importer at `manifest.json`; for each entry use `png_path`, `frame_width`, `frame_height`, and `frames`, or use the corresponding `.4bpp.bin` plus `.gba.pal` resources. Run `python validate_pack.py` before compiling.
