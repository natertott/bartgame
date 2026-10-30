# Menu layout studies 1–5: native planning and tradeoffs

Exploratory proposals for the user's ten-layout request. The common art bible,
reference register and direction log were read. All geometry begins at the
240×160 GBA screen; text keeps the existing native font, icons use existing
32px menu art or separately authored small native glyphs. No filtered shrink
or imported game graphics is part of these designs. Game-specific research
is being collected separately; no new source is claimed as read here.

The palette/skin comparison is separate from the layout comparison. These
five layouts will use the same proposed dark skin so position, information
hierarchy and navigation can be judged without changing materials each time.

## 1 — Loadout workbench

Bring A/B/L assignments into a prominent top workbench. The pack grid sits
below, with a larger selected-item pane alongside it. Equipment and pack
are adjacent: selecting and assigning a tool creates a visible relationship
rather than requiring the player to inspect a narrow secondary strip.

Keys reuse the pack area but replace assignment information with heart-piece,
key and tool ownership information. Map pages keep a known-room map beside
loadout or selected-room context. It supports deliberate preparation before
returning to a previously blocked room. Tradeoff: the pack has less area than
a pure inventory; native spacing must avoid overlapping 32px item drawings.

## 2 — Provision ledger

A compact vertical list shows the icon, actual item name and relevant current
ammunition side by side. A selected-item information pane and use description occupy
the right. This emphasizes recognition through words and quantities, useful
when a new player has not learned the game's seven silhouettes.

The key list can show pieces/keys as actual values. A schematic region map
and selected-room ledger emphasize connections and known barriers over tile
texture. Tradeoff: the list is less spatially memorable than a fixed grid,
and a detailed map belongs in the zoom view rather than in every small node.

## 3 — Fieldbook spread

Two facing pages divide a quick index from selected-item information. A
central page gutter and page-role labels make the inventory feel like an annotated
travel record. The right page spends pixels on use descriptions and equipped
status, while the left provides the selectable native icon/index.

Overview and zoom can be treated as two related page roles; the current room
and region context must stay visible when enlarging the chamber. Tradeoff:
book margins consume area, so ornament must remain at edges and the native
font must not be reduced to fit extra prose.

## 4 — Tactical atlas

Prioritize the player's maze/navigation problem rather than inventory
collection. A map occupies most of the page; a compact tool index and
selected-use/readiness panel sit alongside. It is intended to help the player
notice that a previously found barrier can now be approached with the chosen
item. Any hint must use known/visited and Map/Astrolabe visibility rules.

The map page should distinguish a broad region view from chamber detail,
ideally keeping the selected region cell visible during zoom. Tradeoff:
smaller tool drawings carry less information than the full menu illustrations;
selected text and current ammunition must compensate.

## 5 — Tool rosette

Seven tools occupy a directional ring, with a concise selected-item summary
in the center and A/B/L assignments at the side. D-pad movement uses actual
spatial neighbors; the design does not pretend the GBA has an analog stick.
It tests whether a small fixed tool set is faster to learn through position
and direction than through row/column counting.

Key items use a related reduced ring. Map pages keep a north-up graph/compass
rather than rotating the maze. Tradeoff: a ring is less familiar and requires
careful nearest-neighbor navigation. Every item must be reachable without
wrapping into an unexpected opposite node, and no icon may overlap the central
summary. If that cannot be established at native size, geometry wins over the
metaphor and the ring must be simplified.

## Shared usability rules

- Item pages show A/B/L assignment explicitly. B is an assignment button in
  the current game and cannot simultaneously be advertised as cancel there.
- R changes page and Start closes. B may return from map zoom to overview.
- Keep selection stable across page/zoom transitions where supported.
- Empty/unknown information must stay meaningfully empty. Do not invent
  future quests, statistics, destinations or room knowledge for a pretty card.
- Unknown gate information stays hidden unless existing discovery/item rules
  permit it. An optional map style must not remove exploration from the maze.
- Check source geometry, then real ROM rendering, all seven equipment items,
  all key items, map bounds, assignment controls and closed-menu restoration.

## Implemented recipe data and source evidence

`src/menu_layouts_a.c` now provides five pure `MenuLayout` recipes. The shared
runtime owns truthful state, native text, source icons, map generation and
controls; these data do not change prices, item powers, discovery or gameplay.

| Layout | Item representation | Selected-information area | Map representation |
| --- | --- | --- | --- |
| 1 Loadout Workbench | Seven32px sources in a4×2 drawer grid below the assignment bar. | Right88×80 pane; actual status above. | Terrain overview and chamber in a144×104 area with a72px information rail. |
| 2 Pocket Ledger | Seven16px sources in a16px-pitch list with names/counts. | Right88×64 pane, then assignment and status rows. | Graph overview;128×104 map with a wider88px ledger. |
| 3 Fieldbook | Two columns of16px index glyphs, with a central page gutter. | Facing104×88 reading pane and lower progress row. | Parchment treatment;136×104 region with80px information rail. |
| 4 Tactical Atlas |16px vertical tool index beside a live discovered-map preview. | Wide184×40 lower card; assignments in a right-hand column. | Independent144×64 pack preview; full160×104 route map/chamber and56px info rail. |
| 5 Toolwheel | Seven fixed canonical32px nodes around a central summary. |72×40 center plus a vertical assignment strip. | Familiar north-up graph and chamber, preserving spatial map conventions. |

The Toolwheel deliberately keeps canonical tool positions as inventory grows;
unowned nodes remain empty without revealing an icon/name, and navigation
skips them. The other list/grid choices may compact owned items for efficiency.
Canonical selection memory is handled by the shared runtime, not duplicated
per-layout state. Equipment rectangles are wide or tall so the renderer can
choose horizontal or vertical assignment arrangements consistently.

The research agent's pinned primary-source notes were read in
`docs/art-reboot/references/GBA_MENU_RESEARCH.md`. Emerald's fixed list/detail
reading locations and saved per-pocket index/scroll state support the ledger
and stable reading panes. Fire Emblem8's seven16px list rows support the compact
named ledger without manufacturing a scroll list for only seven tools. The
Minish Cap's explicit neighbor table for a nonuniform inventory supports
predictable D-pad graph navigation and direct assignment. These facts justify
constraints and information hierarchy; the workbench/book/atlas/ring compositions
are original BARTGAME proposals, not claims that the reference games used these
exact layouts. No source graphics or Nintendo code is imported.

Local geometry proof under`layouts/a-geometry-check.json` checks all35 icon
positions,8px-aligned rectangles, screen/body bounds and absence of item/panel
intersection. The diagrams are labelled source geometry and are not emulator
screenshots. Their flat colors are diagnostic region colors, not proposed
production art. ARM compilation and diff checks pass. Real native rendering
and interaction review remains required after the common runtime is built.
