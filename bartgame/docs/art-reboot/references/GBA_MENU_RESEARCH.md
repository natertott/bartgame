# GBA menus: primary-source research for the new layout studies

Research date: 2026-10-30. Status: source-backed observations and exploratory
BARTGAME adaptations. This document does not select a final menu or palette.
The user's request is to explore five new style combinations and ten genuinely
different menu layouts, including equipment, information, overview and zoom.

## Evidence and limits

The games studied are *The Legend of Zelda: The Minish Cap*, *Pokémon Emerald*,
*Pokémon FireRed*, *Fire Emblem: The Sacred Stones*, and *Metroid Fusion*.
They provide relevant GBA action/adventure, RPG and map/navigation interfaces.
Their public decompilation sources were fetched at exact revisions; the
specific handlers, tables and windows below were inspected. These sources
support implementation and layout facts, not claims that reviewers endorsed
a particular feature or that the original developers published UI design rules.

This environment permits GitHub/raw source access but its enforced proxy
returns 403 for the attempted Metacritic and Nintendo Life review pages.
Therefore this pass does **not** invent scores, quote inaccessible reviews or
claim to have read reception text. The titles are established GBA reference
points; the detailed evidence here is their actual menu behavior. No commercial
ROM was downloaded or run, no Nintendo graphics were imported, and no Nintendo
code is copied into BARTGAME. Source observations are paraphrased into original
native layouts and input rules. No tutorial images or missing PDF figures are
newly claimed as inspected.

| Repository | Frozen revision | Inspected files |
| --- | --- | --- |
| `pret/pokeemerald` | `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881` | `src/item_menu.c`, `src/region_map.c` |
| `pret/pokefirered` | `ce6406d8c2eaf46d543c8a2606de0c3cb1951982` | `src/item_menu.c`, `src/region_map.c` |
| `zeldaret/tmc` | `6fb6dfb4a7efbe24d0fd1dda5097af6131faacde` | `src/menu/pauseMenu.c`, `include/menu.h` |
| `FireEmblemUniverse/fireemblem8u` | `04d1edb163d14bd10777a065697e1a9f17be65f2` | `src/prep_itemlist.c`, `src/uimenu.c` |
| `metroidret/mf` | `1ab064aceaef8954fdfb5441d44f4537600a12ea` | `src/menus/pause_screen.c`, `src/menus/pause_screen_map.c` |

Additional neighboring files were downloaded for context; the claims below
name the actual inspected sections. Local research manifests record URLs,
SHA256 file hashes, successes and failures. Review-access failures are
separately recorded. These are reproducible research records, not production
assets. Links below use pinned commits rather than movable branches.

## What the games actually do

### Pokémon Emerald: keep the reading locations stable

[Bag source](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/item_menu.c#L393)
defines an item-list window at tile `(14,2)`, size `15×16` tiles: pixel
`(112,16)`, `120×128`. Its description window sits at tile `(0,13)`, size
`14×6`: pixel `(0,104)`, `112×48`. These are measured source declarations,
not guessed from an enlarged screenshot. At 240×160, two deliberate reading
locations are more useful than fitting the maximum number of framed objects.

The [state structure and input/list callbacks](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/item_menu.c#L115)
maintain separate cursor and scroll positions per pocket. Opening a pocket
passes its saved positions into the list; cursor movement changes its icon
and description. `PrintItemDescription` clears/repaints the same description
window. `CloseItemMessage` restores the list positions after an action.
`BagMenu_ItemPrintCallback` right-aligns relevant quantities, suppresses them
for important/key items, and can show the registered-item mark instead.
Context action sets differ among ordinary items, key items, balls, TMs and
berries. Scroll and pocket-switch arrow pairs are explicit affordances.

**Our adaptation:** a fixed useful-description region, position memory per
page/category, relevant counts instead of universal numeric clutter, and a
stable action footer. A large selected icon earns space only when it clarifies
use or identity. BARTGAME has seven usable items, not a Pokémon-sized bag;
a long scrolling list is an option to compare, not an automatic improvement.

### Pokémon FireRed: the same concepts can have another visual arrangement

[Bag implementation](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/item_menu.c#L634)
builds a list from the active pocket, computes the visible item count and
preserves cursor/items-above positions per pocket. Its cursor callback replaces
the selected-item icon; the description print is separate. Quantities and
registered-item marks depend on item importance. Field, party and battle
contexts offer different valid actions rather than every possible command.

[Region-map implementation](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/region_map.c#L595)
has an explicit map-type permission table and separate normal/dungeon
map-section lookups, cursor state and location descriptions. Those are useful
examples of context-sensitive maps; they are not evidence that BARTGAME should
reveal secret rooms or copy FireRed's particular region artwork.

**Our adaptation:** preserve the same controls, selected object and vocabulary
while testing a ledger, book or workbench presentation. Show only actions the
current item actually supports. An item can have an identity, current quantity,
assignment state and barrier use without filling its page with redundant stats.

### The Minish Cap: equipment is a spatial graph with visible assignment

[Item-slot table and handler](https://github.com/zeldaret/tmc/blob/6fb6dfb4a7efbe24d0fd1dda5097af6131faacde/src/menu/pauseMenu.c#L337)
store each slot's explicit up/down/left/right neighbor and x/y position. For
example the sword/shield column is at x66, y51/y75; other main columns are
x102,138,174. Bottom bottles and the save location are not forced into the
same rectangular spacing. Directional navigation follows the table, which
makes nonuniform arrangements predictable on a D-pad.

The A/B handler calls equipment assignment for the selected item and updates
its description; the drawing code places equipped indicators back on item
locations. [Page navigation](https://github.com/zeldaret/tmc/blob/6fb6dfb4a7efbe24d0fd1dda5097af6131faacde/src/menu/pauseMenu.c#L107)
separately handles L/R and prevents access to unavailable map pages based on
ownership. The source also stores page/cursor state; the partly unnamed
fields are not interpreted as more detailed behavior than their code shows.

**Our adaptation:** give every prototype explicit spatial neighbors, especially
a wheel, ribbon or uneven card layout. Keep the assignment badges next to the
items and the A/B/L loadout visible when equipping. BARTGAME already assigns A/B/L directly on its item page; Start closes and
R changes page. B returns from map zoom only. Preserve those contextual bindings
and show them clearly rather than inventing a global B=Back convention. The
reference supports visible direct assignment; its exact foreign bindings are
not copied blindly.
No slot coordinates or artwork are reproduced in our final layouts.

### Fire Emblem: The Sacred Stones: help can be a layer, not a new destination

[Preparation item list](https://github.com/FireEmblemUniverse/fireemblem8u/blob/04d1edb163d14bd10777a065697e1a9f17be65f2/src/prep_itemlist.c#L22)
stores a current page plus per-page index and vertical offset. Its scrollbar
configuration uses seven visible rows; row positions advance by 16 pixels.
It displays an owner/supply field and highlights the current category.

The [R-help handler](https://github.com/FireEmblemUniverse/fireemblem8u/blob/04d1edb163d14bd10777a065697e1a9f17be65f2/src/prep_itemlist.c#L498)
opens item help at the selected row without losing selection; R or B closes
the help layer. A and B retain context-specific confirm/cancel roles. The
[general menu help](https://github.com/FireEmblemUniverse/fireemblem8u/blob/04d1edb163d14bd10777a065697e1a9f17be65f2/src/uimenu.c#L552)
also anchors a help box to the selected item and can update help as focus changes.

**Our adaptation:** contextual barrier/tool descriptions and focused cards can
stay attached to a selection. Clear page/focus indicators and a scrolling cue
matter more than showing every statistic at once. Owner fields are meaningful
for FE's party inventory; BARTGAME is a single-character game, so replace that
field with equipped slot, ammo or known use rather than inventing a party.

### Metroid Fusion: a map is several truth layers

[Pause-map input](https://github.com/metroidret/mf/blob/1ab064aceaef8954fdfb5441d44f4537600a12ea/src/menus/pause_screen_map.c#L31)
computes directional scrolling availability from useful map bounds, moves the
view only when allowed, supports L/R map transitions and A objective information.
The source defines distinct arrow/target/player markers. The
[pause handler](https://github.com/metroidret/mf/blob/1ab064aceaef8954fdfb5441d44f4537600a12ea/src/menus/pause_screen.c#L804)
keeps map, status, navigation information and close actions as distinct states.

[Visited-map rendering](https://github.com/metroidret/mf/blob/1ab064aceaef8954fdfb5441d44f4537600a12ea/src/menus/pause_screen_map.c#L143)
separates downloaded-map state, visited bits, hidden flags and collected-item
updates. Having a downloaded map does not mean a tile has been visited or that
hidden content should be exposed. View bounds derive from the meaningful
nonblank map area; arrows indicate where more map exists.

**Our adaptation:** distinguish the player's current room, the room under the
menu cursor, known geometry, explored state and discovered markers. The zoom
must refer to the overview's selected room. An overview should explain the
maze; a zoom should explain local banks, walls, pits and entrances. Both should
keep orientation and a clear legend. Do not print a completion percentage or
"loot left" statistic unless the actual game state supports that claim.

### Emerald's overview/zoom: preserve location when changing scale

[Region-map initialization](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/region_map.c#L508)
selects normal/zoom input handlers, initializes from the player's actual map
location, and stores player-icon position independently from the cursor.
Zoom initialization centers its scroll around cursor coordinates instead of
resetting to a corner; [zoomed movement](https://github.com/pret/pokeemerald/blob/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881/src/region_map.c#L775)
updates the section name and position as the view moves.

**Our adaptation:** changing scale is a continuity operation. Keep current and
selected rooms separately marked. B returns from zoom to the same overview
focus. A selected-room name and a compact legend prevent a handsome atlas
from becoming harder to use than a simple grid.

## Ten exploratory layouts and the question each asks

These are original BARTGAME concepts, not assertions that the referenced games
used these exact layouts. Shared controls and truthful map/item state remain
invariants. Native 240×160 geometry and the existing font require tradeoffs.

| Study | Main question / useful change | Research basis | Tradeoff to inspect |
| --- | --- | --- | --- |
| 1 Loadout Workbench | Can the player compare A/B/L and pack contents without opening another panel? Make assignment relationships persistent. | Minish Cap equipped markers + spatial graph. | Equipment can consume too much room otherwise available for descriptions. |
| 2 Pocket Ledger | Can item names, relevant quantities and a stable detail panel beat a grid for recognition? | Emerald/FireRed lists, fixed descriptions and quantity rules. | More directional steps; seven items should not require unnecessary scrolling. |
| 3 Fieldbook | Can separate equipment/key/map pages feel coherent while keeping page focus and readable text? | Pocket memory and page navigation. | Book decoration and a central seam must not reduce actual readable width. |
| 4 Tactical Atlas | Can the player choose a tool while keeping the route visible? | Map/status separation and context-sensitive actions. | Tiny icons need labels; map must not imply a route or gate that is not known. |
| 5 Toolwheel | Can seven spatial positions reduce switching effort while remaining D-pad predictable? | Minish Cap's explicit neighbor graph; wheel is our experiment. | Uneven distances and icon-only ambiguity; keep a stable selected name/action line. |
| 6 Twin Atlas | Can overview and chamber detail stay visible together, preserving orientation? | Emerald zoom continuity and independent player/cursor markers. | Both maps become smaller; label which cell is enlarged and keep symbols readable. |
| 7 Expedition Dashboard | Can equipment, useful resources and known progress support preparing a run? | FE contextual information + Metroid's layered truth. | Do not invent quest percentages, unexplored loot counts or predictive path advice. |
| 8 Focus Cards | Can one generous item card improve understanding of barrier uses and resource cost? | FE anchored help + Pokémon's fixed selected-item detail. | Lower simultaneous item count; retain nearby choices and position memory. |
| 9 Barrier Index | Can categories such as blast/burn/leap help a player remember what a tool opens? | Context action sets and layered map knowledge. | Must not reveal unknown barriers; acquired tools and known room facts only. |
| 10 Quick Ribbon | Can a low-complexity one-row selector make repeated assignment fast? | Persistent list focus and stable action hints. | Horizontal movement may require more presses; selected name and map context must remain. |

## BARTGAME facts the prototypes must respect

The current menu/source already gives useful information. Blightseeds open
cracked walls; the Grail Lamp burns webs/thorns and lights censers; the Petal
Cloak crosses pits; the Root Gauntlet lifts boulders using R. The Drain Cap
**returns the player home**; it is not a boomerang or ranged weapon. The Map
reveals chamber geometry; the Astrolabe reveals additional chest/Heart/barrier
marks. Respect those ownership/discovery distinctions and the existing
`known()` logic. Descriptions should remain factual as well as evocative.

Good comparisons include both a well-equipped state and an early-run state:
unknown/unowned items, zero seeds/arrows, no Map/Astrolabe, visited versus
unvisited room, and switching overview/zoom repeatedly. Direct A/B/L equipment assignment, Start-close and the map-specific B-back
behavior must remain predictable. A more creative layout earns its extra
ornament or navigation step by improving a concrete player task.

## Palette independence and future regions

The user likes structures2/4/5 and explicitly asks to combine them with
palettes1/4/5. Treat structure, reading hierarchy and color roles separately.
This is not a request to auto-select a different skin for each area now.
Future regional palettes may change material hue while preserving body-text,
selected-text, disabled-state, current-room and selected-room contrast meanings.
Never encode a barrier's meaning or selection solely by hue. Repeat native
contrast checks on the dark wine, green ledger and ivory palettes and on
actual bright/dark gameplay backgrounds.

## Review evidence and adoption

Research establishes a source-backed set of design questions, not a winning
menu. The parent task generates native working studies, captures actual mGBA
screens and checks their input/state behavior. That evidence and user feedback
select the useful layout. Maintain the original final Drain, Bloom, world
art and compact HUD/minimap/ammo requirements while changing pause-menu studies.

Local source records: `research/pins.json`, `source-register.json`,
`review-access.json` and downloaded pinned C files under the task work root.
The final publication should retain a compact machine-readable manifest of
successful source URLs/revisions/hashes. Inaccessible reviews remain marked
unread; they do not silently become evidence in later notes.
