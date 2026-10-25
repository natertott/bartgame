# BARTGAME — GBA sprite pack (first complete asset pass)

**Sprite sheets:** 32. **Individual engine frames:** 462.

## Original palette art direction

Filth beneath splendor: blackened iron and bruised earth; polished gold flashes; vivid orange-red flower; oceanic teal against midnight forest; supernatural acid-violet blight. Inspired by the high-contrast heraldry and magical light of *Excalibur* (1981). This is original pixel art, not a copy of Nintendo's or any film asset.

## Folders

- `sheets/characters`, `sheets/monsters`, `sheets/objects`, `sheets/effects`, `sheets/map`: exactly sized horizontal animation strips in required frame order, no gaps.
- `sheets/tiles`: 16x16 BG tile strips including named adjacency, cliff, cave, vegetation and sewer tile sets.
- `sheets/ui/hud.png`: 8x8 tile strip.
- `palettes/*.gba.pal`: raw little-endian GBA BGR555 arrays with 16 entries, transparent index zero. Text RGB888 palette companion files.
- `frame_index.csv`: per-frame bounding boxes and frame names (indices are zero-based).
- `manifest.json`: dimensions, palette groups, counts and order.
- `sprite_frames.h`: frame indices for easy C / C++ engine integration.
- `previews`: enlarged nearest-neighbor **previews only**, not game assets.
- `reference_only`: non-runtime concept art for further polishing.

## Hardware constraints

All master sprite sheets are **4-bit paletted PNGs** containing at most 16 indices (index 0 transparent, 15 opaque). No antialiasing or fractional alpha. Frames are the exact dimensions in the supplied specification. The transparent index in these PNGs is 0. Sprite sheets are laid out *horizontally*, ordered by index, including north/south/east and no unneeded west frames. Indexing follows spec even when certain animations have very small motion differences.

BG tiles use dedicated area palettes (15 opaque colors each). Because GBA **hardware cannot directly load PNG**, convert these indexed master PNGs to tile and palette assets using your existing build system or tools like grit. The .gba.pal files are already BGR555 palette data. Beware: a 16x16 or 32x32 object consists of 8x8 hardware tiles; BG atlas-to-map assembly is the engine's responsibility.

**Honest limitation:** This is a coherent programmatically rendered, pixel-native first pass of every listed sheet, not a hand-refined commercial-quality final sprite set. Some environment categories with open-ended requirements receive representative families; procedural edge blending and autotile pairing will require play-testing. The references contain higher-detail mood boards and are *not* engine-ready.
