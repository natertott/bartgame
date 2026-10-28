# UI, title and portrait plan

This is a production plan, not an implemented redesign. The direction and
shared native palette must be selected from the first mockup critique before
these assets are drawn.

## What exists

The current interface is one of the more coherent parts of the game. Its
three pause pages, item descriptions, button assignment language, shop rows,
portrait/name/dialogue arrangement and five-by-five map are worth retaining.
The mixed visual language comes principally from the oversized world sprites
and the imported bitmap, rather than a need to reinvent those information
structures.

| Asset | Current contract | Producer and consumers |
| --- | --- | --- |
| UI kit | 51 named 8×8 BG tiles; named semantic palette indices | `art/ui_kit.py`; `ui.c`, `text.c`, `menu.c`, `game.c` |
| HUD tiles | Four 8×8 tiles: full/half/empty heart and lifting hand | `ui_kit.HUD_TILES`; `text.c` |
| UI sprite marks | Six 8×8 frames: next, pick, cursor corner, A/B/L badges | `ui_kit.OBJ_MARKS`; `sprites.py`, HUD, shop, map, title menu |
| Proportional face | 97 glyphs, nine rows each; one-pixel interglyph gap and three-pixel space | `art/ui_font.py`; generated `vwf_w`/`vwf_bits`, `src/vwf.c` |
| Map markers | Fourteen 16×16 marks; twelve 8×8 dots; one 32×32 cursor with 32×24 painted outline | `marks.py` frame contracts, currently replaced by imported pack; `menu.c` |
| Dialogue portraits | Six 48×48 drawings padded to 64×64 OBJ: Bloom, Peddler, Gatekeeper, Hermit, Nun, Gardener | `faces.FACES`; generated `pal_face`, streamed `SHEET_FACE`; `text.c` and `npc.c` |
| Title bitmap | 240×160 Mode 3; 76,800 bytes of RGB555 | `art/title.py`, `build_assets.py`, `game.c` |
| Title prompts | 64×32 OBJ text canvas; Press Start at y140, saved-game choices at y120 | `game.c`, VWF, UI palette |
| Minimap | 32×32 procedural OBJ; five-by-five grid with 4px cells | `text.c:minimap_render`, UI semantic inks |
| Full map | Procedural overview and zoom, with terrain/visited/selection states | `menu.c:map_ink`, UI map palette and marker sprites |

The present title producer explicitly resizes a JPEG with Lanczos and stores
about 2,070 RGB555 colours. It is legal GBA Mode 3 output but does not meet the
new native-authored pixel-art requirement. It should be replaced completely.

## Proposed visual rules

Use the selected `reboot_core` palette and cluster grammar. The UI has a quiet,
near-black panel interior, cream main text, antique brass frame and a brighter
ivory-gold selection. The same outline, brass and ivory colours should appear
on world treasure, character metal and title ornaments. Red remains damage or
cost; dim text remains legible rather than disappearing into the panel.

Redraw all kit assets at 8×8. Keep the named tiles, frame IDs, mirrored corner
contracts and palette meaning. Reduce the visual weight of doubled decorative
rules where they consume space; put a single clear silhouette around the panel
and one bright edge around the selected item. A thumbnail-sized sparkle or
cut-gem corner may identify selection, but must not resemble a world pickup.

Retain nine-row proportional text and current advances wherever possible.
Hand redraw the face to match the new cluster style, with open counters on
`a`, `e`, `B`, `8` and a clear distinction between `I`, `l` and `1`. Whole words
must be evaluated at native size, including coloured keywords, counts and
multiline wrapping. Do not change a correct punctuation dot merely to force
a hash difference; the requirement is a coherent reviewed typeface, not
arbitrary damage to universal pixel primitives.

Portraits are illustrations rather than world-scale figures. Draw six new busts
at native 48×48, each inside the existing padded 64×64 hardware canvas. Use a
consistent upper-left light, two-pixel material clusters, the world character's
recognizable costume and facial landmarks, and common framing. A portrait
must represent the redesigned NPC rather than inheriting an old unrelated
face. Keep 15 visible colours per portrait; the existing streamer can load
its palette when the speaker changes. Do not replace portraits with enlarged
world sprites.

The title should be composed directly on a 240×160 integer-pixel canvas from
at most 48 chosen RGB555 colours. Keep the game name and Drain subtitle,
a clear dark area for prompts, and a recognizable grail/flower motif. The
contrast is glorious bright metal above wet, decaying stone and roots. Provide
many native cross-shaped twinkles and a few larger stepped flares, not
resampled photographic bloom. Prompt rows at y120 and y140 must remain clear
in both new-game and Continue states. Menu choices are real game text rather
than baked lettering inside the bitmap.

## HUD scale decision

The current HUD is 32px high because its three equipment slots display the
32×32 inventory illustrations directly. Its map is also a full 32×32 OBJ.
Reducing only its frame or palette would not reduce the true obstruction.

A 24px HUD is feasible with these explicit changes:

- Add a dedicated 16×16 HUD equipment sheet or cache, drawn at native size.
  Keep 32×32 illustrations for pause, shop and item-get screens.
- Keep A/B/L labels, counts, hearts, currency, keys and R's lifting cue. Use
  8px badges and 7px figures; do not overlay a count onto an unreadable icon.
- Paint the minimap in 24×24 of its 32×32 hardware canvas, with 3px cells and
  breathing room. Its 16-tile reservation can remain unchanged initially.
- Make the panel three BG tiles high, but draw equipment as 16px hardware
  sprites; retain enough spacing between slots to distinguish assignments.
- Verify the world below y24 is free of HUD pixels, including icon alpha,
  number outlines, badge corners and OBJ-window duplicates in dark rooms.

A 20px visual band is possible inside a 24px tile row allocation, but should
be judged from the first native mockups. The HUD cannot simply squeeze seven
32px menu illustrations down by generic image resampling. A dedicated native
16px depiction is part of the shared item family.

## Ownership and integration boundaries

After direction selection, UI production should own new native kit/font/title/
portrait producers and their palette registrations. The engine agent should
own `src/text.c` if compact HUD geometry is selected. Avoid concurrent changes
to that file. Root owns the shared art direction and final screen review.

The item artist should own the item designs at three sizes: 10–14px world,
16px HUD and 24–28px inventory/item-get. Shared silhouettes must remain
recognizable at each size. The UI artist should supply frames and spacing,
not independently redraw the item into another style.

Map markers need redesigned symbols consistent with the world affordances:
chest, doorway, web, fracture, key lock, pit, thorn, person and healing. Shape
and placement convey meaning; colour reinforces it. The overview dots should
not all be interchangeable discs if they represent different gameplay states.

## Required review screens

Review native frames for the title before/after Start, saved-game title menu,
HUD with maximum hearts/three equipped items/bombs/arrows/three-digit purse,
all three pause pages, both map zoom levels, item assignment changes, shop
selection and insufficient funds, plain text, named dialogue with each of the
six portraits, multiple pages, item-get, death/return, and the win screen.

Validate actual OAM/VRAM and palette restoration after closing menus and
shops. The seven-icon cache must still accommodate every simultaneously
drawn pause icon, including the selected description. Text canvas budgets,
wrapping and HUD reservations must remain within their existing pools.
