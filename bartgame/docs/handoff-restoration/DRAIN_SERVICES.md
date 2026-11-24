# Drain services and the second wall ladder

The Drain is the starting hub and the return point for the Forest and the
Curdled Cream. Both regions use the same native wall ladder design.

## Ladder

The selected Forest ladder is the native BG construction painted by
`art/sewer_final.py:_ladder`: a 48px-wide brass-framed recess, seven clear
rungs and a filled arrow above them. `hub_services_build` repeats the same
three-by-five metatile stamp from cells 8–10/rows 0–4 at cells 18–20/rows 0–4.
The Cream ladder is centered at world x312, with its painted foot at y71.
The shared return anchor is `(312,94)`, south of the automatic crossing.

Repeating the actual metatile IDs preserves their exact RGB555 pixels,
animation, palette and collision vocabulary. It needs no extra BG bank or
new ladder drawing. The ordinary game no longer draws the Cream arch over
the wall. The historical arch frames remain in the asset family so previous
sheet/frame IDs and older evidence stay interpretable.

The new location lies between the cistern and the wizard. Storage, the arcade
cabinet, bridge, banks, existing Forest ladder and original NPC anchors are
not moved. The lower edge of the new ladder meets the existing carpet/floor;
the old logical wall is opened only within the authorized exit stamp. The
game state must route the copied `TT_EXIT` cells to Cream, including when a
shield keeps Bloom facing another direction.

## Current hub

Face north at the Billious Peddler's counter and press A to shop. Press Select
at the counter to trade a matching card. Speak to the Wizard for the three
Forest trials. Press A at the Trophy Case to see discoveries and use Start
there for optional challenge mode or run difficulty.

Starting gifts still appear during a new run. Each region handles its own
traders, quests and seals. Continue grants a pending reward from an older
paid stay directly. The old service coordinates are ordinary room terrain.

## Historical regional native qualification

Runtime source `51880a55e6ecf86728f3a0923e5547e7bdeed5a0`, ROM SHA256
`0dd8554384b53e618140f8c61590fc7e6a7ff0888f296ece034a95f357b34fdd`.
The [physical hub review](../../../regional-handoff-review/validation/hub/report.json)
passes43/43 checks through ordinary walking and real service/ladders inputs.
The [original Drain review](../../../regional-handoff-review/validation/preservation-drain/report.json)
passes11/11 for the existing frog market, wizard and cabinet, including its
item/enemy pages and proper return. Both reviews use private erased SRAM and
an explicit deterministic title seed; they do not assign hero position, health,
inventory, camera, terrain or outcomes. The earlier source/host review above
retains its own scope; actual mGBA images and traces are in the linked review.
