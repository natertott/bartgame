# Drain archive cabinet: native art decisions

2026-11-05 · implemented source asset; actual room qualification follows integration

The direct brief adds a retro game cabinet to the Drain. Interacting with it
opens the discovered-item/enemy collection. This extends the existing room's
material language rather than introducing a separate arcade sprite pack.
The canonical art bible, direction log and reference register were read before
authoring. This pass uses their already-recorded native-size, silhouette,
lighting, contact, material-cluster and interaction rules. No new website,
commercial artwork, generated high-resolution image or unread PDF is claimed.

## Native construction

`art/arcade_cabinet.py` is the source. `build_sheet()` and `SHEET` supply:

- Sheet `arcade`, valid32×64 vertical GBA OBJ canvas.
- Frames `idle` and `glow`, each32 hardware8×8 tiles;64 tiles for the whole strip.
- Existing `PAL_OBJ_FX` bank, the unchanged `reboot_core.PALETTES['gold']`.
- Literal4bpp pixel-index row strings. Index0 stays transparent.

The complete painted extent, including the contact shadow, is27×45 pixels,
from native coordinate(3,19) to(29,63) inclusive. Most of the upper64px canvas
is hardware padding, not part of the cabinet. A recommended contact anchor is
(16,62), with a shallow physical base near(4,50)–(27,62). Integration must
place its actual base and unobstructed front on reachable dry floor; the full
32×64 hardware rectangle must not become collision.

## Readability and shared materials

The machine has an overhanging marquee, recessed teal monitor, inward waist,
projecting control deck, one connected red joystick and two separated buttons.
These are arcade-cabinet identity details at native scale. The marquee uses
hand-authored3×5 `PLAY` lettering; the monitor contains a tiny open book to
suggest the catalogue function. Broad masses come before scratches.

Wine-brown housing shares the Drain's tarnished brass/ivory edges. The CRT uses
the bank's two existing teal inks. The narrow right return is darker than the
front; upper-left edges receive the short highlight. No new palette slot or
full-body glow is required. Damp grime stays attached to lower seams and the
base. The exterior is transparent, so real gray-brick floor shows around the
silhouette and rounded contact shadow.

Only9 screen pixels change between the two frames. The housing, joystick,
controls, shadow and short static material glint do not flicker. A slow screen
pulse, such as64 video frames per pose, suits the quieter glitter brief; it
must not restore the former ambient sparkle density. The cabinet's screen
activity is separate from ambient glitter selection.

## Source inspection and evidence

Running the module exports native transparent PNGs, a1×/3× nearest-neighbor
inspection sheet and a palette/size/hash manifest. These are **source art
assemblies, not emulator renders**. Current private export location:
`/workspace/setup/arcade-release/cabinet-source/`.

Source checks confirm two32×64 frames, indices0–15, RGB555-compatible existing
inks, stable64-tile storage and9 changed pixels contained in the monitor.
The final room capture must separately verify physical placement, front
approach, sprite layering against Bloom, HUD clearance, and return from the
journal without a changed palette or corrupted room graphics.
