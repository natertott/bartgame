# Drain services and the second wall ladder

This is a local implementation note for the user's request to put the restored
features into the ordinary game, and to replace the Cream arch with another
wall ladder matching the Forest exit. It does not adopt a new shared palette
or change existing character/terrain paintings.

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

## Ordinary hub services

`hub_services.c` supplies five compact physical fixtures/people in the Drain.
It calls the same actual economy and service routines used by the restored
systems; it does not expose a list of challenge rooms or teleport the player
to a selected event. Generated-region events are handled independently.

| Fixture | World feet / standing front | Action |
| --- | --- | --- |
| Wares assistant, beside the existing market | `(120,110)` / `(120,126)` | A: extended rolled wares. The Billious Peddler's original shop remains available. |
| Stone broker | `(152,238)` / `(152,254)` | A: locate the actual colored fusers and gold seal chambers in the regions. Matching and its physical consequence happen there. |
| Trail guide | `(304,238)` / `(304,254)` | A: inspect the current regional objective. R: a concrete local hint. |
| Patched cot | `(352,238)` / `(352,254)` | A: choose a paid rest. |
| Trophy cup | `(416,238)` / `(416,254)` | A: record, optional entitlements and difficulty. |
| Promised bedside chest | `(384,238)` / `(384,254)` | A: collect the actual pending inn reward. Present only when a paid stay has earned it. |

The source hub's three price/reward levels remain in the inn menu. One physical
cot presents those three choices in the compact Drain instead of duplicating
three beds across the existing walking field. This is an explicit local
adaptation, not a claim that the source Wind Tribe tower geometry was rebuilt.
The three-round opening gift draft is initiated by ordinary new-run flow;
it does not require an optional room-selection desk.

The assistant, matcher and guide reuse the existing Cream folk drawings and
their original material bank at the same world scale. A narrow cot and one
unmistakable gilt cup are appended as frames 12/13 after the family's original
twelve frames. The old 51 Cream actor/door frames and all prior sheet IDs stay
unchanged. The cup explicitly uses the existing gold/FX bank; the cot keeps
the quiet stone/wood bank and an exposed ivory pillow. No palette is replaced.

All physical services reserve a short feet-level collider and a clear standing
front. Their two draw passes use the same feet-based OAM ordering as the
existing NPCs and cabinet. Six single-frame allocations are made on entry;
no frame allocation or upload occurs while drawing the service fixtures.

## Qualification

`tools/hub_services_review.py` compiles and executes the actual service module
against explicit room, renderer and service spies. Its 1,419 checks include:

- Exact source-ladder metatile reuse and untouched cells outside its stamp.
- Old actor-sheet/frame IDs and pixels retained as an exact prefix; native
  canvases and 4bpp ink limits for every frame in the affected family.
- Busy-state/facing/range filtering for the physical service inputs and hint.
- Correct conditional bedside claim and one draw per fixture across depth passes.
- Dry player-feet routes from the ordinary spawn to all service fronts, the
  cabinet, both ladder approaches and the Cream return. This uses the selected
  authored metatile collision/hazard metadata, the real cabinet footprint and
  the service module's actual dynamic colliders.

Report: `/workspace/setup/regional-drain/host/report.json`. The pure source
atlas is `/workspace/setup/regional-drain/source/actors-source.png`.
These host/source results do not establish actual PPU appearance, native input
or GBA performance. The integrated native review must walk from the real Drain
spawn, complete the opening draft through its actual UI, exercise the services
and both ladders, preserve original Peddler/wizard interactions, and inspect
the new ladder beside the wizard with the real camera settled.


## Final regional native qualification

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
