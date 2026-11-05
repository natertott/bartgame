# Memory cabinet interface

The Drain cabinet opens a collection journal, using the current Winebound
Folio, Mossbound Fieldbook or Ivory Reliquary construction and independently
selected colors. This extends the existing selected interface; it introduces
no imported artwork, new font or unrelated visual style.

The index shows six entries at a time, with a broad native selection plate.
Items and enemies have separate remembered cursors. Discovered names and the
actual final-size item/enemy drawings appear on the right. An unseen entry is
`???`: its name, description, health, image and palette are never requested
by the presentation path. Found/total counts are shown on both category tabs.

A opens a full notes page: a native picture has its own frame while readable
proportional text fills a separate panel. Enemy health and contact damage are
explicitly HP, with `One heart = 8 HP` displayed beneath. Item and enemy notes
come from the shared journal data, not a duplicated interface-specific list.
The index may shorten a long row label; the full entry name and notes fit the
larger detail panel. Unknown detail pages remain generic and contain no stats.

Controls:

- Up/Down move one entry; holding the D-pad repeats after a short delay.
- Left/Right jump six entries in the index, or one entry in full notes.
- L or R changes category and returns to the index.
- A opens notes. B returns to the index, then leaves the cabinet.
- Start leaves from either page.

The modal uses `GS_ARCADE`, pausing world actors, collisions, attacks and the
run timer while the normal main loop continues music. It does not clear actors,
change discovery state, heal Bloom or change equipment. The parent interaction
owns the physical cabinet and its accessible front.

## Native memory and restoration

The backdrop uses the existing selected UI kit in BG3 charblock3. The Drain's
room maps are rebuilt on exit; display mode, BG3 control and scroll, animation
enable and blend registers are restored. BG0 returns through its existing HUD
invalidation/rebuild path. No world sprite allocation is performed.

One preview frame is streamed into reserved face tiles944–975, at most32 OBJ
tiles /1,024 bytes. The prior contents are saved and restored. Portrait palette6
is temporarily borrowed and restored separately (32 bytes). Item illustrations
use their exact authored frame pixels/palettes; pickup and enemy pictures use
their original native sheets and material banks. No resizing or screenshot
painting is used. The largest native Heart view fits the32-tile reserve.

The index consumes317 of the328 available pooled BG0 text tiles; the notes
page consumes291. Preview upload plus five text canvases fit within the existing
16-entry VRAM queue. The art dimensions and text planes are separate; a body
cannot obscure its own name or notes.

`arcade.h` exposes read-only page, absolute cursor, scroll top, detail mode,
seen state and preview sheet/frame/tile-count diagnostics for actual mGBA
qualification. Source inspection establishes intended layout and memory
contracts; final screenshots, input checks and restoration tests must come
from the production ROM. The parent release records that qualification.

## Native catalogue inspection

`tools/arcade_ui_review.py` runs all33 full-note entries under all nine
shape/color combinations through the real cabinet and ordinary UI controls.
Its valid private serialized discovery records are catalogue-coverage fixtures,
not evidence that a player earned all discoveries. It never assigns a UI
cursor, terrain, palette, VRAM, OAM, framebuffer or enemy state. Each preview
is checked against its native ROM frame and palette, its hardware position
against its separate picture frame, and the world allocation/restoration
contracts against actual emulator memory. Actual native font advances also
establish that every current description fits within three136px lines.

The initial private pilot passes654 checks for297 full-note frames, nine
preference combinations, native previews and restored borrowed resources.
The item/enemy sheets and nine-style contact sheet were visually inspected:
no name/stat/description clipping or body/text overlap appeared. The known
pilot Healing Petal material-bank mistake belongs to journal metadata and
is corrected separately; the final review adds an independent per-frame
palette-table check for pickups. Final release evidence must use the rebuilt
ROM and current capture-tool hash rather than relabeling this pilot.
