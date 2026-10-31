# Adopted Workbench and annotated room map

Status: adopted implementation with passing actual mGBA pilot review. The
parent will repeat this checker against the final immutable release freeze.
The user's 2026-10-31 selections are the direct source: item menu1, map menu2,
a fixed Winebound HUD and runtime selectable frame/color choices. Shared art
bible, direction log, reference register and the prior pinned GBA menu research
were read. This pass claims no newly accessed article or Nintendo asset.

## Adopted composition

Items and Key Items retain Loadout Workbench1: seven native 32px illustrations,
persistent A/B/L assignments, selected functional help and truthful resources.
The map independently adopts Pocket Ledger2's north-up connection diagram,
expanded from 128×104 to 160×112 so each room can hold readable contents. The
selected chamber uses the same 160×112 map region beside a 56px legend.
Frame style and palette come from runtime appearance settings. Each menu open
recaches the current native kit and resets page backgrounds, so a prior theme
cannot leak through cached pixels. No full-screen image is downscaled.

## Semantic marks, not center stacks

Nine native 7px symbols serve the overview, zoom and legend: You arrow, arched
Door, Task exclamation, Chest, healing heart, Heart H, Folk F, Relic diamond,
and barred Gate. The player marker is gold, event symbols pale, each with a
one-pixel dark contour over the map. Map art and marker meanings remain stable
when interface colors change. H is the moving boss; the heart silhouette is a
healing shrine. In the overview, distinct known event types occupy separate
9px slots INSIDE each room rectangle. You receives its own slot rather than
being overpainted on a chest or person. Current game role exclusivity limits
ordinary cards to three event types plus You, fitting two rows of two symbols.

In zoom, x+1/y+1 saved marks become tile-center anchors at the room's true
coordinates. Unvisited charted Astrolabe finds use a pure metadata preview;
no estimated center position is invented. Gates use actual roomgen_gate_tiles.
The Heart uses its actual live actor position in the current room, otherwise
its deterministic arena spawn. The player uses actual world coordinates.
Close neighboring features receive a short leader line from their true anchor
to a separated marker; outlines remain inside the map viewport.

## Knowledge and completion

Visited entrances, unfinished tasks/Folk and unused healing shrines remain
known from saved room marks. Astrolabe ownership adds chest/Heart/barrier
knowledge; Map ownership charts terrain. The active relic quest retains its
existing revelation rule. Completed trials/quests, opened chests, used shrines
and a cleared Heart stop advertising unfinished business. Unknown terrain is
never fetched merely because a cursor points at it. Ordinary NPCs are Folk,
not Tasks; Key Item trial rooms no longer advertise a phantom forest chest,
because their reward exists inside the trial.

## Review interface and limits

Read-only gMenuMapEvents reports exactly the nine semantic bits displayed in
each overview card. gMenuMapMarkers reports each zoom icon's source anchor,
displayed callout position and native room tile. The game never consumes those
reports, and a capture harness must never write them to fabricate a screen.

Controls remain Start close/open, R page, D-pad item/room navigation, A/B/L
assignment on Items, A map zoom and B overview. Zoom now advertises D-pad room
browsing. Native ARM syntax checks pass for the active MENU1 path. The actual mGBA
pilot now passes 198/198 checks across 34 captures: all 25 normally generated
rooms are loaded to harvest authentic positions, then navigated by two-frame
button taps in the adopted map. Every visible event agrees with actual room
tiles; adjacent icons stay separate and bounded. A cold fresh-core Map +
Astrolabe preview reproduces an unvisited chest's real position. Completion,
fog and Map-without-Astrolabe states preserve their separate meanings. Unknown
zoom fetches no terrain and displays no fabricated locations. Preview browsing
preserves live World, Room, RoomSpots, PlayerState and gameplay RNG. Closing
restores static world VRAM, legal animation allocations and palettes.

The healing shrine is genuine seed 2 / cell 8, not an inserted mark. The
six-panel native comparison shows Door, Task/NPC, Chest, Heart, Relic and Shrine.
The appearance owner independently inspected that board and the native overview:
no symbol, label, palette or overlap blocker was found. Ordinary forest NPCs
currently all have tasks, so the Folk F registry/legend is present without
inventing a non-task actor simply to exercise it. Cold pilot graph draw takes
12 IRQ frames; sampled complete room zooms take 6–20. These measurements are
samples, not a worst-case guarantee for every seed.

Tool: tools/adopted_map_review.py, invoked with --frozen and --out. It never
writes any gMenuStudy or map presentation report. Mutable pilot evidence lives
under /workspace/setup/appearance-enemy-studies/map-native-review; final immutable
capture/publication remains owned by the parent. The appearance owner's
separate all-nine style/palette suite covers interface changes; this map pass
uses the fixed Winebound default for consistent comparisons.
