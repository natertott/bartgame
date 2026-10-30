# Final Drain integration and physical contracts

The user now requests one final sewer room built from preferred components,
with distinct side walls, a taller ladder and above-ladder arrow, correctly lit
arches, readable larger broken plumbing, and a LEFT-edge profile outlet. Five
UI studies are separate from this selected room. The shared art bible,
direction log and reference register were read before changes; no new external
art reference is claimed. These notes record implementation, not a new style
selection beyond the user's requested final Drain synthesis.

## Default and historical profiles

`BART_SEWER=9` is the ordinary build default in the Makefile and direct Python
art imports. `recipe(9)` identifies the final room and preferred NPC pair; old
profiles0–8 remain explicit alternatives. The five new UI studies are selected
independently through `BART_UI=0..5`; UI0 is the compact baseline. The selected
Step-and-cut default stays3. `HUD_HEIGHT_PIXELS=12` and `BART_UI_VARIANT` are
exported in the generated header for the UI runtime and capture checks.

## Placement-specific pictures without physical changes

`art/sewer_final_contracts.py` creates657 independent picture identities:
600ground placements and57occupied overlay placements, named
`swh_f_g_XX_YY` / `swh_f_o_XX_YY`. Original global IDs0–912 retain their
ordering; the new IDs append at913–1569. The original `reboot_contracts.json`
is unchanged. `rooms.ROOMS[0]` uses the new picture grid only in final profile9;
room dimensions30×20, all object kinds/anchors, and every empty overlay cell
remain unchanged.

`art/tiles.py` copies each original source metatile's type, quarter collision
mask, prop flag and glitter flag into its picture clone, then substitutes only
native drawing frames and intentional liquid frame timing. This preserves all
657 placements' semantics. Direct source preflight in
`integration/physical-contracts.json` checks3290 distinct source relationships;
this is a preflight, not a substitute for the independent packed-ROM audit.

The original map reused top-wall pictures on the side boundaries and reused
floor IDs inside large plumbing drawings. Independent picture names allow
side-facing walls, larger fixtures and coherent water to survive actual map
assembly. The painter `sewer_final.paint(name,phase)`, `frame_spec(layer,x,y)`,
`palette()` and `full_layers(phase)` use exactly this same placement grid.
A clone does not create a new gameplay interaction, obstacle or tile location.

## Packing and animation sharing

Final profile9's Drain tileset holds only the new room pictures; unused
historical `swh_` pictures keep global names but do not consume resident Drain
VRAM. Other profiles use their original packing predicates. Forest and mystery
packing remain unchanged.

All657 unique IDs initially reserved1066resident BG subtiles, exceeding the
GBA1024limit. `tools/build_assets.py` now shares **identical complete animation
sequences** only in final9's sewer tileset. The cache key contains all native
frames in their exact orientation, frame hold, and every quarter's palette
assignment. Reusing one frame's pixels alone is forbidden; no independent-frame
flip matching or shared timing approximation is used. Picture IDs/physical
metadata stay independent even when their entire identical animation shares
one contiguous four-subtile VRAM allocation and one runtime animation record.

The complete final native source build fits **822/1024** Drain BG subtiles,
657picture IDs,130declared animated clones sharing69distinct allocations, and
one Drain BG palette. Forest remains693subtiles/59animations/8palettes;
mystery remains114subtiles/6animations/5palettes. Animation allocation count is
asserted<=255 because the runtime field is8-bit. No art or animation frames
were simplified to force the room under budget.

## UI art boundary

The separately authored ten-pixel HUD icon function replaces only the
`huditems` sheet, preserving its frame IDs, hardware16×16canvases and original
per-frame material palette assignments. World drops, menu item illustrations,
Bloom and sword poses retain their source drawings. UI study palettes and
frame tiles are provided by their UI author/runtime owners. The tiny handrail
uses `sewer_final.rail_sprite()` in profile9 and historical rails elsewhere.

## Save compatibility and glitter

No C world, player or save struct is changed. Save version2 stores `World`,
`PlayerState` and run counters; static Drain metatile IDs are reconstructed
from the ROM and are not stored in SRAM. Existing global metatile IDs remain
stable anyway. Carried objects are persisted as `CARRY_*` kinds rather than
map IDs. No save migration is needed for appended Drain picture identities.

Ambient glitter's site generation hashes the seed, area, cell and tile
coordinates, not the metatile ID. Its eligibility/depth follows the copied
per-cell glitter/type/prop/collision flags; no RNG, emitter, phase or sparkle
sheet is changed by this integration. The independent runtime review remains
responsible for visible glitter and gameplay behavior.

## Evidence and limits

`integration-assets.log` records a complete profile9/UI0 asset build;
`integration/gen` contains its generated C/header/coverage. These are source
build/preflight artifacts, not the final frozen ROM. The parent task owns full
ROM compilation, mGBA captures, independent native-ROM decoding, actual menus,
HUD latency and user-facing publication. No claim of runtime verification is
made solely from this integration preflight.
