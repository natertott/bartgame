# Selected interface and persistent appearance options

Status: adopted in response to the user's 2026-10-31 selection. The gameplay
HUD is **#1 Winebound Folio** (`BART_UI=6`), the item/key menu uses **#1 Loadout
Workbench**, and the map uses **#2 Pocket Ledger's** connection diagram. The
map changes are recorded separately by their renderer owner.

The title now exposes **New Game** and **Options** without a run save, and
**Continue**, **New Game**, **Options** when a valid run exists. Its 64×32
native text sprite fits three readable rows without growing into the resident
UI-mark allocation or covering additional title art.

## Independent frame structure and colors

Options contains two controls:

- **Style:** Winebound Folio, Mossbound Fieldbook, Ivory Reliquary.
- **Colors:** Wine / gilt, Moss / brass, Ivory / slate.

Up/Down selects the row; Left/Right wraps its three values. A, B or Start
finishes and saves. Changing either row immediately redraws the actual native
kit and a dialogue sample; selecting a structure does not reset its color.
All nine combinations are supported. One shared choice styles the item/key/
map frames, dialogue, reward/shop fields and their continuation/selection
marks consistently. The actual HUD and corner minimap retain their separate
selected Winebound geometry and palettes.

These are the previously authored native structures and semantic palette
recipes, now selectable at runtime. Their sources are the user's direct
selection and [UI remix notes](UI_REMIX.md); no new external article or missing
PDF illustration is claimed as inspected. The shared GBA-first art rules,
semantic contrast roles and references remain in force. No automatic regional
palette switching is introduced.

All three kits have the same 51 semantic tile identifiers, authored at 8×8
with 4bpp pixels. Three six-frame 8×8 marker sets follow the existing
next/pick/corner/A/B/L frame order. They are stored in ROM and only the chosen
kit/marks are resident. The three 16-entry palettes are exact RGB555 colors.
The Options text uses 318 of the 328 available full-page BG0 canvas tiles;
frames occupy the existing BG3 kit rather than consuming that text pool.

## Integration API and restoration

`src/appearance.c/.h` owns the selected shape/color and persistence.
`ui_current_tiles()` and `ui_current_marks()` return the selected ROM native
data. `appearance_style()` / `appearance_palette()` are independent indices
0–2; `appearance_revision()` is available to cache owners. The menu refreshes
its native kit cache when opened rather than retaining an earlier shape.

`text_init()`, native text-kit compositing and `ui_backdrop_open()` use the
current kit. The room palette initialization reapplies the active appearance,
so entering an area does not reset it. `appearance_apply()` loads menu BG
bank 13 and only neutral paper/ink entries in map BG bank 12. Terrain and
landmark meanings stay fixed. Continuation/selection pointers use their own
UI OBJ bank 8, keeping HUD/minimap OBJ bank 15 fixed. The inventory temporarily
borrows actor palettes and restores this selected pointer palette on close.
The startup reload after preferences are read gives the saved title picker
its matching shape immediately.

## SRAM compatibility

The run's `SaveFile`, accepted versions 1/2, checksum, migration and erase
logic are unchanged. Preferences use a separate twelve-byte versioned,
checksummed record at SRAM offset `0x7F00`, inside the final reserved 256 bytes
of ordinary 32KB SRAM. Shape and color are range-checked; a missing, damaged
or unknown record falls back to Winebound/Wine. The validity byte is written
last. Changing options never serializes, replaces or erases the run.

New Game, Continue, death/run save and legacy migration retain the independent
preference bytes. `save_erase()` still clears only the original run header.
A compile-time `SaveFitsBeforeAppearance` guard prevents a future expanded
run record from silently growing into the reserved preference region.

## Actual review evidence

`tools/appearance_review.py` drives the real title controls; it never writes
the selected preference, menu cursor, canvas, palette or pose variables.
Fixtures are disclosed: initial blank/corrupt SRAM, the deterministic seed,
inventory/resources and safe NPC standing positions. The separate serialized
legacy-save check uses the existing independent `save_probe` fixtures.

The final appearance **pilot** passes **280/280 checks over 56 native mGBA
captures**, including all nine Options, item, opening-dialogue, named-wizard,
shop and HUD views, plus both title states. Actual checks confirm:

- Preview VRAM matches the selected native ROM kit and marker set.
- The item page's actual rendered corner uses that selected kit.
- Menu/pointer palettes follow the selected colors.
- Fixed Winebound HUD paint, HUD palette, minimap tiles and minimap palette
  match exactly across all nine combinations.
- A/B finish Options, normal two-frame taps cycle choices, actual reset loads
  them, and New Game/Continue keep them.
- Preferences leave a valid run record byte-identical; a normal v2 death/save
  leaves preferences byte-identical; bad preference checksums fall back safely.

The separate legacy-save regression passes **6/6**: v1 trial migration,
unrelated inventory/world preservation, v2 round trip, unclaimed rewards and
corrupt run-checksum rejection. These are compatibility/behavior evidence,
not an aesthetic score.

Actual nine-way Options/items/dialogue/shop/HUD boards were personally viewed
at native size. Body type, selected rows, prices, punctuation, continuation
marks and all three palette pairings remain readable. Board labels sit outside
the unchanged 240×160 frames; no gameplay image is recolored or resampled.

Pilot evidence lives under `/workspace/setup/appearance-enemy-studies/`:
`appearance-pilot-review/appearance-review.json`, its `nine-*.png` boards,
`appearance-title-pilot.png` and `appearance-legacy-save.log`. These mutable
pilot paths must not be presented as final source-freeze evidence. The parent
publishes a fresh run against the committed final ROM and records that final
provenance separately.

Remaining design choice: the appearance applies jointly to menus/dialogue,
with independent colors; separate per-screen or per-region preferences are
not additional controls in this requested pass.
