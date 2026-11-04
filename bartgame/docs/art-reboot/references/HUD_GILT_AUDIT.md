# Gleaming HUD: independent scope and budget review

`tools/hud_gilt_audit.py` checks the linked ROM independently of the source
gallery. Numerical success establishes native fidelity, scope and allocation;
it does not establish attractive art or smooth gameplay. Actual mGBA scene,
input, animation and cadence evidence belongs to `tools/hud_gilt_review.py`.

The baseline is the previously delivered forest-room-cohesion ROM, SHA256
`5fcf4cba1c6ab3a5af4575a5a05a49d9813457a02b4f5d16a7e3abc05e41566e`,
published at commit `e3e65be4d7ab98426e31a4bfab9dac02e17299f6`.
The baseline is retained unchanged, rather than regenerated from a new painter.

## What is independently compared

- A fresh explicit `BART_HUD=0` build must reproduce every byte of the previous
  ROM. A copied old ROM without the current configuration header is insufficient.
- Clean subprocesses load the selected profiles with HUD0/HUD1 separately,
  preventing cached Python painters from contaminating comparisons.
- The four allowed changed families are `items`, `pick32`, `icon32` and
  `huditems`. Their identifiers, ordering, canvas dimensions, physical sheet
  descriptors and per-frame material assignments remain exact.
- Every linked item frame is decoded from hardware 4bpp OBJ tile order and
  compared pixel by pixel with the direct native source. The separate exact
  inventory tile stream must match the redrawn menu sheet too.
- Each nonempty source frame has one eight-connected silhouette. This catches
  stray fragments and disconnected handles; it does not demand rectangular
  silhouettes or eliminate useful negative space inside an object.
- World items keep a maximum14px painted extent on16px canvases. The equipped
  item variants use larger13–16px native silhouettes than the old9–10px icons.
  Menu illustrations remain independently authored32px images.
- All remaining source/linked object sheets, all area terrain tiles/maps/
  animations, existing material and UI palettes, title/font/menu payloads,
  tree pictures and combat geometry tables remain exact. Pointer-table bytes
  are excluded from raw equality because ROM addresses move; their resolved
  assets and physical descriptors are compared instead.
- Gameplay source files match the baseline. Only the HUD implementation,
  its header and the OBJ-reservation comment may change in `src/`.
- The final frozen ROM hash and every recorded build input match both the
  current files and their bytes at the committed source revision. Private
  `--allow-pilot` output is explicitly unqualified and cannot replace this check.

## Hardware allocations and limits

The script reads actual linker sizes for IWRAM/EWRAM, verifies area BG tile
and palette limits, and checks that a32px padded minimap fits the reserved
last16 OBJ tiles at1008–1023. It also reports the remaining BG0 text pool below
screenblocks22/23. Positive capacity alone does not prove dialogue allocation;
real unnamed/named dialogue, shop, item/map pages and returns are exercised by
the emulator review.

The gold frame is painted24px square, with a20px room grid. Its transparent
padding is a hardware allocation detail, not permission to fill a32px corner.
The enlarged pods are local20px-high panels. Real decoded HUD alpha checks
must retain the open top-center world view and keep counts separate from the
equipped-item identity. Button illumination, the room pulse and the border
gleam have separate meanings and require motion review.

## Visual and timing review

The initial item critique identified a thin glove/hood treatment; the painter
broadened the gauntlet palm and cloak material groups. An inventory-lantern
handle gap was connected before final source freezing. These are original
native edits applying the recorded silhouette/material guidance, not imported
commercial pixels or newly claimed reference research.

The first runtime pilot exposed a substantial cadence regression from repeated
HUD painting. That pilot is private diagnostic evidence and is not qualified
for release. Final acceptance requires a new build, actual VBlank/logic-age
samples and a fresh scene/input review after optimization. Neither a passing
asset audit nor an attractive screenshot overrides a timing failure.
