# Layouts 6–10: native menu design intent

Status: exploratory interaction/layout studies, not production selection.
All concepts target 240×160 native pixels, the same UI6 skin and current game
state. No map contents, room links or future quest state are invented. Every
layout retains item assignment, a key-item page, overview and chamber detail.
The common runtime provides source icons, text, navigation and known-map data.

## 6 — Twin Atlas

The map page shows the regional overview and the selected chamber together.
The player marker and selected-room marker are distinct, and moving selection
changes chamber detail without losing the overview position. The pack page
uses a lean vertical item rail and a spacious selected-tool information field.

Benefit: supports backtracking and item-gated return trips without repeatedly
opening/closing zoom. Tradeoff: two maps sacrifice individual map resolution;
full chamber inspection remains a deliberate zoom mode rather than pretending
that tiny overview pixels are complete room details.

## 7 — Expedition Dashboard

Equipment and factual run state have their own upper/right field; the pack
uses compact icons and a large selected-item card. The map page pairs a useful
regional map with an equipment/known-state column.

Benefit: quick checks of held tools, currency and explored state before a long
branch. Tradeoff: individual descriptions are shorter than a full field guide.
The interface must never imply that visiting every room is required.

## 8 — Focus Cards

One selected item is the hero: native 32px art, its real name, a clear action
line and generous description. A compact peer rail provides immediate access
to the other owned tools. Key items receive the same hierarchy.

Benefit: new players can understand a tool before assigning it; current
selection remains stable when details or map views change. Tradeoff: scanning
the whole pack is slower than a list. D-pad order is explicit, cyclic and fixed.

## 9 — Tool Index

Selection emphasizes the gameplay verb: cut, guard, blast, burn, leap, shoot
or return. The normal item name and original description remain visible for
the selected tool; verb headings do not replace identity. The map uses known
room/landmark information rather than revealing unvisited barriers.

Benefit: connects the player's equipment to the game's interaction vocabulary.
Tradeoff: role labels need to stay short at native size; this is an index, not
a promise that the currently selected room contains a matching obstacle.

## 10 — Quick Ribbon

Seven owned-tool positions form one direct horizontal ribbon with a generous
information field below. Selection and button assignment take one repeated
left/right gesture; no secondary confirmation tree is introduced. The map
retains large overview/chamber space with a slim text rail.

Benefit: quickest comparison and reassignment for experienced players.
Tradeoff: a long ribbon is less scalable than a paginated list if future areas
add many tools. Prototype capacity matches the current seven tool families;
any future overflow needs paging rather than shrinking icons below readability.

## Controls and research relationship

D-pad navigates owned choices; A/B/L assign their real item slots; Start closes;
R turns pages; B returns from map zoom. L remains an item-assignment button.
Any study-specific control change must be explicitly labelled by the common runtime. Empty inventory, partial ownership
and full current inventory must all remain usable without phantom items.

The research agent has independently verified persistent bag/list positions
and cursor-centered map zoom in public GBA source. These observations support
stable selection, anchored detail and distinct player/inspection markers. Exact
pinned citations will be linked from the shared research note; this concept
note does not claim new external source inspection on its own.

## Source geometry review

`src/menu_layouts_b.c` defines five independent native arrangements. ARM
syntax checking passes. Ten native wireframes (item/map pages) and a coordinate
ledger are under `layouts/`; these are deliberately labelled source planning
assemblies, not game screenshots. Every panel rectangle is hardware-tile aligned
and inside the 240×160 viewport with header/footer reserved. Icon positions
fit their native16px or32px canvases without resampling. Actual text wrapping,
selection and map truthfulness remain common-renderer responsibilities and
need mGBA review before these studies can be called readable or complete.

The Twin Atlas uses separate item-preview geometry so its useful full map page
does not shrink to the pack inset's dimensions. Focus Cards uses a32px selected
illustration and sixteen-pixel peer icons; Quick Ribbon uses all seven full-size
32px illustrations. The Barrier Index's short verbs accompany, rather than
replace, the selected real name/description. Dashboard's narrower detail column
intentionally trades long prose for immediate loadout/status visibility.
