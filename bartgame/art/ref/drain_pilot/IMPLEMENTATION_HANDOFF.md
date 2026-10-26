# BARTGAME — Drain native-art pilot (real export; engine commit `718efd8`)

## What this package actually is

A **240×160 physical-pixel**, GBA-palette-constrained **single-screen pilot composition** for the Drain, implemented as actual indexed background and OBJ artwork. It is not a high-resolution concept image or another procedural replacement for all 117 legacy entries.

The pilot is a **native-resolution pixel adaptation** of the already-approved illustrated composition. The design has been sampled at display resolution, its animated/foreground elements and actors separated, then native pixel corrections added and the result **optimized to 13 BG palettes of 15 colors each**. This is a first game-art prototype. It is **not** a claim that every 240×160 pixel has been independently hand-painted from scratch, nor that a complete new scrolling environment has been created.

## Authoritative output — use these files, not the high-res reference

| File | Contents |
| --- | --- |
| `master_240x160.png` | Exact 240×160 reference frame composited from the *exported GBA-indexed assets* |
| `assets/bg/ground_240x160.png` | Fully opaque BG2 ground, 240×160 RGBA |
| `assets/bg/overlay_240x160.png` | Transparent BG1 canopies, 240×160 RGBA |
| `assets/bg/ground_tiles/*.png` | 150 individual 16×16 BG2 logical tiles, filenames `row_col.png` |
| `assets/bg/overlay_tiles/*.png` | Only nonempty BG1 16×16 logical tiles |
| `assets/sprites/bloom_idle.png` | 32×32 GBA OBJ; green-stalk Bloom, 31-pixel-high painted form |
| `assets/sprites/peddler_idle.png` | 32×32 OBJ; source-adapted Peddler silhouette, separate from room |
| `assets/sprites/gatekeeper_idle.png` | 32×64 OBJ; source-adapted Gatekeeper silhouette, separate from room |
| `gba/drain_bg_4bpp.chr` | **Actual** packed 4bpp GBA background 8×8 characters, deduplicated |
| `gba/drain_bg2_ground.map` | 32×32 16-bit hardware screen entries, top-left 30×20 used |
| `gba/drain_bg1_overlay.map` | 32×32 16-bit hardware screen entries, top-left 30×20 used |
| `gba/drain_bg_palettes.pal` | 13×16 GBA BGR555 colors, for slots 0–12 |
| `gba/drain_obj_palettes.pal` | 16×16 OBJ BGR555 colors; banks 0–2 are populated for these pilot actors |
| `gba/obj_{actor}_4bpp.bin` | Real 4bpp 8×8 OBJ characters in 1D row-major sprite order |
| `layout.json` | Screen geometry, bank per cell, sprite placement, data filenames |
| `palettes.json` | RGB and 15-bit packed palette definitions |
| `validation.json` | Binary readback QA results |
| `source/build_pilot.py` | Fully reproducible native art and exporter code |
| `source/verify_exports.py` | **Independent hardware-byte-to-image decoder and exact pixel test** |

`source/approved_drain_composition.png` is **only the original visual reference**. Never feed that file to the ROM importer. The final 240×160 indexed art is in `assets/` and `gba/`.

## What changes in the implementation

This is a separate **pilot room ID**, e.g. `drain_art_pilot`, with its own screen-local metatile map. **It is not a drop-in replacement for the old `art/ref/pack_v3` file-key importer**, because it deliberately uses unique per-cell art across one composed 15×10 scene.

1. Add a temporary art-pilot room or standalone renderer branch; camera locked to `(0,0)`. Hide HUD/actors not part of this test. Keep the existing Drain hall untouched.
2. Load all of `gba/drain_bg_4bpp.chr` into contiguous BG 4bpp character memory accessible with screen tile IDs 0–1023. There are **659 entries including the empty character** (21,088 bytes). Both BG1 and BG2 use this shared character base.
3. Load `gba/drain_bg_palettes.pal` into BG palette slots 0–12 (416 bytes). **Preserve slots 13–15** for the existing UI/text banks.
4. Load `gba/drain_bg2_ground.map` and `gba/drain_bg1_overlay.map` into separate 32×32 screenblocks (2,048 bytes each). Example: BG char base 0 and screenblocks 16, 17 if free. Tile IDs are stored in 10 bits, palette ID in bits 12–15. No extra flips are encoded.
5. Set mode 0, BG2 priority 2, BG1 priority 1, scroll `(0,0)` on both, size 32×32. Background palette index 0 is reserved as transparency. BG2 uses opaque indices only; BG1 uses 0 off the visible canopies.
6. Import the three OBJ sprite PNGs or their included 4bpp binaries, respecting 1D OBJ mapping. Keep Bloom at the native **32×32 OBJ shape** with a 31px-tall painted form, and the Gatekeeper in a **32×64 OBJ shape**. `layout.json` holds their placement. The pilot uses OBJ palette banks 0, 1 and 2 *relative to the supplied OBJ palette block*. If these OBJ slots are already in use, relocate those palettes and update OAM attr2 accordingly; don't overwrite the existing actors' shared OBJ colors.
7. Maintain BG1 over OBJ priority 2 over BG2, as in the existing engine contract. Temporarily suppress regular world actors for screenshot comparison so they don't appear twice.
8. **Collision is not inferred from the picture.** For a first fixed-frame rendering test, use the existing controlled room geometry or a new pilot collision table. Don't mark the artwork as a completed gameplay level. The full 30×18 room, scrolling seams, NPC dialogue and water physics require a separate layout step.
9. Capture the raw mGBA 240×160 framebuffer, with the same actor placements and art; compare it with `master_240x160.png` before moving on. The provided `source/verify_exports.py` already proves the binary maps/palettes reproduce the master with no discrepancy in an independent software decoder.

### Why these assets fit the engine's reported budgets

- BG char patterns: 659/1024 (including blank); **365 free for this pilot**.
- BG palette banks: 13/13 area banks used; menu/text banks 13–15 preserved.
- OBJ banks: 3 of 14 possible, subject to live engine slot assignment.
- Both BG maps are 32×32 hardware tiles; active portion is 30×20, mapping exactly onto 240×160.
- BG2 opaque. BG1 proper alpha outside canopies. All exported sprite alpha is binary.
- The source output uses 15 visible BGR555 colors per bank, and no per-pixel alpha or bilinear filtering.

## Quality limitations and next art corrections

The image is visibly closer in arrangement and atmosphere to the approved concept than the previous procedural pack, but at 240×160 it necessarily loses minute detail from the original 1536×1024 source. This first pilot uses **native-resolution adaptation**, not a fully separately painted scene. The Peddler and Gatekeeper are cropped native sprites with polygon-based transparency masks; their outlines merit manual cleanup before production. BG2 under their silhouette and under canopy foregrounds has been inpainted, so those newly revealed backgrounds also merit manual cleanup once the characters move in the game.

A **moving** game additionally needs walk/run/talk animation, lighting behavior, joined neighboring rooms, and collision-compatible architectural edit passes. This package tests the core problem first: **can a faithful, richly composed indexed pixel scene be displayed by the real ROM without losing fidelity?** It supplies the actual art bytes with which to find out.

## Repeatable QA

From the pack root (Python + Pillow, numpy, opencv-python):

```bash
python source/build_pilot.py
python source/verify_exports.py
```

Expected exact result:

```
PASS: independently decoded BG1, BG2, OBJ and exact master RGB: 0 mismatched pixels of 38400
```

**Please return** a real ROM capture of this pilot scene (raw 240×160), and any importer/build errors. Don't redesign the art independently. Use `master_240x160.png` as the exact frame target.
