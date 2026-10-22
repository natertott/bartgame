# 09. Assets, formats and the re-skin

The brief: same mechanics, **its own sprites and map**. This document says
where every asset lives, what format it is in, and what a re-skin must
keep identical so the code still works.

## Where assets come from today

The decomp repo contains **no game assets**. `make` runs
`tools/bin/asset_processor`:

```
asset_processor extract USA build/USA/assets   # cut every asset out of baserom.gba
asset_processor convert USA build/USA/assets   # binary to editable (PNG, .s, .bin)
asset_processor build   USA build/USA/assets   # editable back to binary  (make custom / CUSTOM=1)
```

The manifests in `assets/*.json` list every asset with its ROM offset,
size and type:

| manifest | types and counts |
|---|---|
| `assets/gfx.json` | 1,308 gfx, 2,856 palettes |
| `assets/map.json` | 95 tilesets plus 95 tileset type tables, 217 subtile sets, 1,148 tile maps, 30 collision maps, 219 dungeon maps |
| `assets/assets.json` | 2,903 animations, 138 sprite frame tables, 119 gfx, 2 frame OBJ lists |
| `assets/samples.json` | 272 sound samples (AIF) |
| `assets/sounds.json` | 513 songs (MIDI) |
| `translations/*.json` | text banks for each language |

After a build, `build/USA/assets/` holds 1,638 PNGs, 1,609 `.4bpp` files,
2,856 `.gbapal` palettes, the map binaries and the animation `.s` files.

**For the new game, the goal is a repo whose assets are all its own**, built
with `asset_processor build` (or plain `gbagfx` rules in the Makefile)
from files in the repo, with no `baserom.gba` at all. Until then,
`make custom` builds from the converted tree, so a replaced PNG goes in
without touching the ROM image.

**A note for the user, not legal advice.** Everything extracted from the
baserom is Nintendo's: art, maps, music, samples, text and the font. The
decompiled code is a reconstruction of Nintendo's code. A game that
replaces every asset still runs that code. Whether and how it can be
distributed is the user's decision to make.

## Formats

| asset | format | tool |
|---|---|---|
| tiles | 4bpp, 8x8 per tile, 32 bytes, often LZ77 (`.4bpp.lz`) | `gbagfx` PNG to 4bpp and back |
| palettes | 16 colors of BGR555, 32 bytes (`.gbapal`) | `gbagfx` from `.pal` or a PNG's palette |
| BG tileset | subtile art (`gAreaTileSet_<Area>_<n>_<k>.4bpp.lz`) plus the metatile table (4 u16 subtile entries per tile: tile number, flip bits, palette) plus the type table (`gAreaTileSetTypes_*`, a u16 tile type per tile index) | |
| room map | u16 tile indices per layer, packed at room width, LZ77 (`gAreaRoomMap_<Area>_<Room>_bottom/top.bin.lz`) | |
| collision map | optional per-room override of derived collision | |
| sprite gfx | 4bpp tiles in `gGlobalGfxAndPalettes`, named by gfx index | |
| sprite frames | `SpriteFrame {numTiles, firstTileIndex}` per frame (`gSpriteFrames_<n>.s`) | |
| frame OBJ lists | per frame, the OAM pieces: offset, shape, size, flip (`gFrameObjLists`) | |
| animations | per animation, keyframes `{frame_index, duration, flags}`, ended by a keyframe with bit 0x80 (`gSpriteAnimations_<n>_<k>.s`) | |
| sprite table | `gSpritePtrs[]`: `{animations, frames, ptr}` per sprite index | |
| music | m4a songs from MIDI (`mid2agb`) | |
| samples | AIF to PCM (`aif2pcm`) | |
| text | JSON to `USA.bin` (`tmc_strings`) | |

### How a sprite draws

```
EnemyDefinition / ObjectDefinition
   gfx           -> the 4bpp sheet (fixed: whole sheet; swap: streamed per frame)
   spriteIndex   -> gSpritePtrs[i] = { animations, frames, ... }
   paletteIndex  -> OBJ palette group
entity->animIndex + frame timer
   -> animations[animIndex] keyframes -> frame_index
   -> frames[frame_index] = which tiles of the sheet
   -> gFrameObjLists[sprite][frame] = how those tiles lay out as OAM pieces
```

**What a re-skin must keep**, per sprite:

- **the animation table**: the same animation ids, because AI code calls
  `InitAnimationForceUpdate(this, n)` with literal numbers. Keyframe counts
  and durations may change, but timing changes how attacks feel, and some
  AIs wait on an animation's end flag;
- **the frame OBJ layout**, or rebuild it to match new art: an OAM piece
  list per frame;
- **the hitbox**, which lives in the definition, not the art. New art should
  match the old silhouette's footprint, or update the hitbox too;
- **the number of directions**: 4-direction sprites use animationState
  0/2/4/6, and some use flips for east and west.

**Re-art for performance at the same time** (`08_PERFORMANCE.md`): small
frame counts for chaff enemies, so they fit fixed shared sheets.

### How a tile draws

```
room mapData[tilePos] = tile index
   -> subTiles[index*4 .. +3] = four 8x8 subtile entries (tile, hflip, vflip, palette)
   -> tileTypes[index]        = tile type -> collision byte and act tile
```

**What a re-skin must keep**: the **tile type** of every tile that has
behavior. A bush must still be type 0x1c, a torch 117, a chest 0x73. The art
and the tile index can be anything. Types with no behavior (plain floor,
wall faces) are free.

**Build each area theme's tileset from scratch**, as a list of
`{tile type, 4 subtiles, palette}` plus the stamps the generator places
(`07_PROCGEN_DESIGN.md`). A tileset holds up to 2,048 tile indices per
layer. A theme needs a few hundred.

**Trap: tile art must exist for every type the generator uses.** Vanilla
Minish houses list the torch type with blank art. Probe each theme's
tileset once by drawing every type it claims (`lantern_gust_survey.py
--draw` is the pattern).

## The order to replace things

1. **The player.** One sprite with many animations (walk, attack, every
   item use, swim, climb, fall, Minish). The largest single job. Do it
   first, because every test shows it.
2. **One area theme's tileset** plus its stamp library, so the generator has
   something to draw.
3. **Chaff enemies** (level 1 and 2), re-arted with small frame counts.
4. **Common objects**: pots, bushes, chests, doors, switches, torches,
   rocks, rupees, hearts.
5. **The HUD and font**: hearts, rupee digits, item icons, message box.
   The HUD digits live at BG0 tile 0xF0. An earlier bug overwrote BG0's
   screenbase 31 with digit art.
6. **Remaining enemies, NPCs, effects**.
7. **Music and sound**, written for the audio budget you chose.
8. **Text**, all of it new.

## Re-skin checklist per enemy

- [ ] new sheet drawn to the old frame list, or frames and OBJ lists rebuilt
- [ ] the same animation ids
- [ ] palette shares a theme palette
- [ ] fixed or swap decided, and the GFX cost re-measured with `gfx_trace.py`
- [ ] hitbox still matches the silhouette
- [ ] its death effect and drops still spawn (`shf_probe.py` pattern)
