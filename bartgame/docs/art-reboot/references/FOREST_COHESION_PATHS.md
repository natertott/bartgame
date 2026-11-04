# Visible forest wear, profile32

`forest_paths_refine(cell,path)` runs after required event positions are known,
before local sickness and route lights. Its floor graph reads actual native
metatile type/collision and overlays. A compact heap prefers existing wear,
then joins each selected entrance, crossing bank or feature approach to the
already chosen network. The search stops at the existing network instead of
painting every old coarse-plan cycle. Bridge approaches remain functional;
some optional features and reclaimed lanes intentionally lack a dirt clue.

Unused PATH/PEDGE cells become calm grass or stage-appropriate sick floor.
Transparent props no longer reveal a discarded dirt rectangle underneath.
Selected ordinary zero-collision FLOOR pictures become PATH; relics, switches,
barriers, slow grass, portable objects, bridge decks and event logic retain
their semantic IDs and physical masks. No world edge, wall or item gate is
opened. These are visible wear edits, not new passable corridors.

The generator's actual PATH cells and MID scratch flags are updated together.
Detailed paused-room previews run the same native generation, while the older
coarse overview remains a passability chart rather than an exact dirt drawing.
The module keeps only generation scratch in EWRAM (about8.4KB); there is no
per-frame path search or persistent road cache. Same-room menu redraws reuse
the existing Room and planted-tree cache. Deterministic room reconstruction
uses the same seed, anchors, heap tie order and costs without consuming RNG.

The module is omitted entirely from historical0–31 linker input lists. Native
old/new views, item-gate/approach audits and menu/preview checks must qualify
its actual behavior. No external reference beyond the existing art direction
and the user's direct room-cohesion feedback is claimed.
