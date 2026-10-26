# BARTGAME engine contract for the artist

Written for the artist agent's "Art-to-Engine Fidelity Recovery Plan". It answers what that plan lists as not yet known, gives the engine's contract as data, and supplies fixed golden scenes captured from the real engine with the tools to compare against them. Everything here is read from the game's source and built tables, or captured from the running ROM. None of it is estimated.

The data files named below sit beside this document in the handoff zip. In the repository they are in `docs/engine_contract/`, and the tools are in `bartgame/tools/`. The engine commit they describe is `engine_commit` in `engine_asset_contract.json`.

## 1. The finding: the renderer draws the pack exactly

We rendered three fixed scenes two ways and compared them pixel for pixel:

1. **The engine.** The ROM ran in mGBA, and the raw 240x160 framebuffer was saved with the HUD and sprites switched off, so only BG2 (ground) and BG1 (overlay) show.
2. **An independent compositor** (`tools/compose_frame.py`). It draws the same cells straight from the art pack V3's PNG files. It uses none of the game's import, tile or palette code. The colours go through BGR555 exactly as the hardware does.

| Scene | Camera (px) | Pixels that differ | Worst channel difference |
|---|---|---|---|
| drain | 0, 0 | 0 of 38,400 | 0 |
| living | 48, 48 | 0 of 38,400 | 0 |
| blighted | 64, 160 | 0 of 38,400 | 0 |

The test was at tolerance 0. This means:

- tile order, flips, palette banks, layer priority, scroll, animation phase and transparency are all correct;
- there is no filtering;
- what the game shows is the pack's pixels, unchanged.

So the gap the plan describes is in the art as delivered, as the plan suspected. It is not in the engine. A better master drawn to this contract will reach the screen as drawn.

The evidence is in `scenes/<scene>/`:

- `engine_capture_bg_240x160.png`
- `compose_bg_240x160.png`
- `diff_bg.png` (all grey means no mismatch)
- `report_bg.json`

## 2. Answers to "what is not yet known"

| Question | Answer |
|---|---|
| Platform target | A real Game Boy Advance ROM: ARM7TDMI, Thumb code, built with arm-none-eabi gcc. It is tested in mGBA 0.10.3. It has not yet been tried on hardware. It is not a web reimplementation. |
| Game source | Repository `natertott/bartgame`, game under `bartgame/`. The user can grant access. The files that matter to art are listed in section 7. |
| Current importer | `bartgame/art/env_pack.py`. It reads `art/ref/pack_v3/manifest.json` and `assets/<group>/<key>.png` under the tile spec v1 keys (section 3). Checks are listed in section 4. |
| Screenshot of the same room from the identical exported tiles | `scenes/*/engine_capture_*.png` and `scenes/*/compose_bg_240x160.png`, compared in section 1. |
| Raw framebuffer | Every capture is mGBA's 240x160 video buffer as rendered. There is no scaling, shader or CSS. |

## 3. The three tile specs, and which one is current

The PDF the plan used is **v2**. The pack V3 was drawn for **v1**. The game now lays **v3**.

| Version | Commit | Entries | Tiles | What it is |
|---|---|---|---|---|
| v1 | 4297bb8 | 117 | 328 | The first tile spec. The pack V3 was drawn for it, and the importer reads its keys. |
| v2 | 0477e1d | 99 | 423 | The painted-drafts spec: the 41-page PDF. It is superseded. |
| v3 | current | 103 | 293 | What the game lays today, every entry drawn from the pack V3. |

`key_migration.json` lists every key in every version: its file path, size, shape, frames, layer and the metatiles it draws, plus what the importer reads today. The three cases the plan names resolve like this:

- **`blight_growth/blight_tree.png`** is the v2 path. In v2 the blighted tree came from an earlier atlas, which used group `blight_growth`. In v1 and v3 the path is `wood_blight/blight_tree.png`, 32x48 (2 by 3 tiles). That is the file the game reads.
- **`wood_ground/trail_corner.png`** existed in v2 only, as a painted draft. The pack has no corner nicks, so the game no longer lays them. It is listed as a wanted addition (section 6).
- **`drain_props/d_crate.png`** is the v3 name for the crate. Its art is tile 1 of v1's `drain_props/d_props.png`, and the importer reads it from there.

The v1 keys stay the importer's file names, so a redraw of any of the 117 files is a drop-in. If the next pack moves to v3 names, tell us. We will switch the importer to the v3 keys and fail the build on any missing one.

## 4. The engine contract

`engine_asset_contract.json` holds the full contract as data. It has the platform and display facts, each area's budgets and banks, every metatile, and every pack entry the importer reads. In short:

**Display**
- Mode 0 with four tiled backgrounds, 4bpp (16-index banks, index 0 transparent), and OBJ 1D mapping.
- BG0 is text, HUD and dialogue (priority 0).
- BG1 is the room overlay (priority 1, drawn over sprites): tree crowns, sparkles, mist, and the mystery rooms' pots, plates, chests and spring.
- BG2 is the room ground (priority 2, opaque).
- BG3 is the pause menu's plank backdrop.
- Sprites are OBJ priority 2: over the ground, under the overlay. A few effects use priority 1.
- There is no alpha blending in rooms. Fades use brightness only.

**Tiles**
- A logical cell is 16x16: four 8x8 hardware pieces (TL, TR, BL, BR).
- The importer gives all four pieces of a metatile one palette bank. The hardware allows a bank per 8x8 piece. If a hand-drawn master needs that, it is a small importer change, so ask for it.
- Identical 8x8 pieces are stored once, also when one is the other flipped horizontally, vertically or both.
- Animated metatiles are not deduplicated.
- Animation: a metatile with N frames swaps all four pieces every D/60 s, so the frame shown is (frame counter // D) % N. Every copy in a room animates in step.
- Collision is per 8x8 quarter. The metatile's type decides what a solid quarter does: wall, water, pit, thorn, lift and so on.

**Palettes**
- BG and OBJ palettes are separate.
- Each area loads up to 13 BG banks of its own into slots 0..12.
- Slots 13 (menu), 14 (gold text) and 15 (text and HUD) are fixed.
- The sprites use 14 OBJ banks.

**Rooms**

| Area | Rooms | Size in 16x16 cells |
|---|---|---|
| Wood | generated from a seed, 25 a run, camera scrolls | 32x24 |
| Mystery rooms | generated | 12x9, 18x12 or 24x16 |
| Drain | one hand-laid hall (`art/rooms.py`) | 30x18 |

Generated rooms repeat tiles everywhere, so wood art must be tiles that repeat. The Drain is laid by hand, so its art can be unique per cell, within the piece budget below.

**Budgets (as built with the pack V3)**

| Area | 8x8 pieces used | Pieces free | BG banks used | Banks free |
|---|---|---|---|---|
| Wood | 873 of 1,023 | 150 | 6 of 13 | 7 |
| Mystery rooms | 129 of 1,023 | 894 | 5 of 13 | 8 |
| Drain | 298 of 1,023 | 725 | 4 of 13 | 9 |

The Drain's 725 free pieces would hold a fully unique 240x160 pilot frame: 150 cells, 600 pieces at most.

**The importer's checks (the build fails on any)**
- Every v1 key has exactly one asset, and no asset is unknown.
- Size is columns x 16 by rows x 16 x frames.
- Every opaque pixel is exactly one of its group's 15 colours. There is no partial alpha.
- Ground tiles are fully opaque. Transparency is allowed only in overlay entries and tree crown rows.
- Each group has one 16-colour palette across all its files.
- It does not check resemblance to any reference. The scene comparison in section 5 does that.

**Tiles the game lays that no pack file draws**
- A mystery room's crown (the bottom wall seen from the room) takes its wall art.
- Its floor beside the walls takes its floor art.
- These are listed as `"kind": "derived"` in the contract.
- Tiles the game holds but no longer lays take a plain pack tile (`"spare"`).

## 5. Golden scenes and the comparison loop

*The Drain has since been redrawn from scratch (`art/sw_hall.py`, Oct 2026). The `drain` scene and `drain_hall.json` below describe the hall before it; the living and blighted scenes still hold.*

`scenes/` has three fixed scenes. All use the pinned seed 0xB4A7, so every room and camera is reproducible. Each scene folder contains:

| File | What it is |
|---|---|
| `engine_capture_240x160.png` | The whole frame: HUD, ground, overlay and sprites, as a player sees it. |
| `engine_capture_bg_240x160.png` | The room only: BG2 and BG1. This is the target for a master's room layers. |
| `engine_capture_ground_240x160.png` | BG2 alone. |
| `layout.json` | Exactly what is on screen (see below). |
| `compose_bg_240x160.png`, `diff_bg.png`, `report_bg.json` | The check from section 1. |

`layout.json` gives:

- the camera and the frame counter;
- every visible 16x16 cell, ground and overlay, with its metatile, pack file and tile, the animation frame on screen, its palette group and bank, its type and its collision per quarter;
- the hardware 8x8 screen entries of BG2 and BG1, read from VRAM;
- the 16 BG banks, read from palette RAM;
- the visible sprites, read from OAM.

`drain_hall.json` is the whole 30x18 hall: ground and overlay cell by cell, and its objects (spawn, exit, the two NPCs).

**The pilot.** The plan picks the Drain, and so do we: camera (0, 0), the hall's top-left 15x10 cells. It shows the Peddler's stall, banners, lanterns, the drain hole, the waterfall into its basin and the top of the channel. The Bloom stands at (120, 104) in room pixels; the Peddler is at cell (4, 4). To deliver a master for it:

1. **The scene.** Draw it for this camera and layout. If you want a different composition, send a `layout.json` in this schema with the cells you want, and we will lay the hall to match. Collision must keep each cell's type: the walls, the water and the stall stay where they are.
2. **The layers.** Send `master_240x160.png` (flattened, for approval). Also send its room layers:
   - `ground_240x160.png`: opaque, BG2;
   - `overlay_240x160.png`: transparent where empty, BG1, drawn over sprites;
   - optionally `sprites_ref_240x160.png`, for reference only. Sprites come from the sprite pipeline.
3. **The palettes.** Send `palettes.json`: the BG banks, at most 13 for the area, 15 colours each. Also give the bank of each 16x16 cell, or of each 8x8 piece if you want per-piece banks.
4. **Our side.**
   - We slice the layers into the hall's cells. Each cell becomes its own metatile if its pixels are unique; repeats share one.
   - We build, capture the same camera with `tools/golden_capture.py`, and run `python3 tools/compare_frames.py master_bg_240x160.png engine_capture_bg_240x160.png --tolerance 8 --output diff.png --report report.json`.
   - A pass means every pixel is within 8 per channel, which covers BGR555. Mismatches are reported per 16x16 cell.

For the wood, a master must be built from tiles that repeat, because rooms are generated. The living and blighted scenes show the tiles as the generator lays them.

## 6. What the pack V3 lacks, and how it looks in the engine

**Not in the pack, wanted.** Each needs a small engine change, made on delivery:

- a blighted canopy crown;
- edge tiles for the blight floor against the vein, water and walls;
- corner nicks (15 each) for the trail and the verges;
- the chest, censers, mystery mouths, thorns and cliff drawn on blight floor;
- soft edges for the stained ground;
- banks on every side of the Drain's pools.

**As delivered, visible in the scenes.** These are faithful to the files:

- Objects on grass sit on squares darker than plain grass: rocks, boulders, censers, chests, flagstones and tree trunks.
- The three grass variants differ in tone, so the grid shows.
- The blight floor tiles show their edges.
- Water banks and bridges are a bright cream that outshines the floor.
- In blighted rooms, the chest, censers, mouths, thorns and cliffs stand on grass.

## 7. The files that matter to art

| Path (under `bartgame/`) | What it does |
|---|---|
| `art/env_pack.py` | The importer: v1 key to metatiles, slicing, exact indexing, the checks |
| `art/ref/pack_v3/` | The pack V3 as delivered |
| `art/tiles.py` | Every metatile: name, type, collision; the art pipeline's order |
| `tools/build_assets.py` | Tilesets per area, 8x8 dedupe with flips, banks per area, animation tables |
| `src/room.c` | Loading a tileset and its banks, animating tiles, drawing the room into BG1 and BG2 |
| `src/video.c` | Display mode, BG layers and priorities |
| `src/roomgen.c` | How the wood's rooms lay tiles |
| `src/myst.c` | How the mystery rooms lay tiles |
| `art/rooms.py` | The Drain hall's layout |
| `tools/golden_capture.py` | The fixed scenes, captured from the ROM |
| `tools/compose_frame.py` | The independent compositor |
| `tools/compare_frames.py` | The frame comparison |
| `tools/engine_contract.py` | Writes `engine_asset_contract.json` and `key_migration.json` |

To regenerate everything from the repo:

```
cd bartgame && make
python3 tools/engine_contract.py OUT
python3 tools/golden_capture.py OUT/scenes
python3 tools/compose_frame.py OUT/scenes/drain/layout.json art/ref/pack_v3 OUT/scenes/drain/compose_bg_240x160.png
python3 tools/compare_frames.py OUT/scenes/drain/compose_bg_240x160.png OUT/scenes/drain/engine_capture_bg_240x160.png --tolerance 0 --output diff.png
```
