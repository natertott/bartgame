# Regional maps and compatible checkpoints

The selected Forest map keeps its existing frame, palette, terrain drawing
and original symbol IDs. New native seven-pixel symbols identify field waves,
fusions, mechanism sites and the current regional seal. Room cards keep each
symbol in its own slot; a plus sign indicates additional types when a narrow
historical layout cannot fit them. The selected room's legend lists its actual
types, and A opens their detailed chart.

Cream's directed atlas adds quest, wave, fusion, mechanism, cache and objective
marks. A two-column legend fits the existing text-tile budget. Nearby features
receive separate symbols with short tethers to their true tile anchors. The
normal world does not consume the map's read-only position telemetry.

The Satchel's R shortcut resolves the current region, including generated
interiors: Forest opens the selected Forest map and Cream opens the shelf
atlas. Existing Start/pause maps and equipment assignments remain available.

## Real positions and discovery

The region planner records only anchors that were actually placed on loaded
geometry. The new checkpoint stores its fifty ten-byte discovery records.
Detailed maps do not place an undiscovered feature at an invented room center.
A regional seal may identify an unvisited room while its terrain and exact
feature position remain uncharted. Once found, the chart marks the saved tile
coordinate. Map/Astrolabe and ordinary visit permissions still govern terrain.

This follows the existing art bible's semantic map vocabulary and explicit
anchor rule. No existing sprite or terrain pixels were repainted. New map
symbols use the existing native UI inks; map-only buffers live in EWRAM.

## Save extension version 3

The original base-v1/v2 Forest checkpoint, the `HandoffState` layout and the
independent cross-run profile retain their formats. Extension v3 appends the
500-byte discovered-position array and run-start quest-region choice to the
published extension-v2 prefix. The record is 1,908 bytes and remains within each
existing 4,096-byte slot. The region choice is latched once, so a mid-run change
to entitlement mode or score cannot move a quest giver between regions.

An older v2 record is checked at its original 1,404-byte length and original
checksum position. The existing EWRAM staging buffer reads the old prefix;
there is no additional 1.4KB stack record. Its inventory, regions, completed
events, food and profile facts survive. Newly added position records start
unknown, and the event module migrates the old optional Annex contract into a
real regional chain without taking away already earned items or Elements.
An active legacy quest whose giver lived only in the Annex is retired without
calling the loss/forfeit path; its paid stake and existing inventory remain.
This avoids carrying an unreachable giver or a false regional completion into
the continued run.

New active chain targets use real regional field/interior site IDs 32–127.
Wave and quest targets must be fields; invalid enum values, target ranges,
quest destination coordinates, map coordinates and marker flag bits reject
the extension safely. Runtime objective selection rechecks the regenerated
world and live capabilities after the record is restored.

## Qualification

`tools/run_extension_host_review.py` compiles the actual serialization C with
the production types and explicit runtime initialization stubs. It tests
published-v2 migration, v3 round trips, isolated profile precedence, interrupted
write prefixes, generation wrap, invalid action fields and protected SRAM.
The initialization stub does not prove the real regional chain's selection
logic; that requires the native regional integration review.

The final candidate is source `51880a55e6ecf86728f3a0923e5547e7bdeed5a0`,
ROM SHA-256
`0dd8554384b53e618140f8c61590fc7e6a7ff0888f296ece034a95f357b34fdd`.
Its actual 1,908-byte extension is qualified by these independent reviews:

| Review | Passed | Report directory under `/workspace/setup/regional-integration/` |
| --- | ---: | --- |
| Actual serializer, production branch | 2,609 functional + 48,640 protected-byte checks | `save-host-candidate4` |
| Serializer lab write protection | 5 | `save-host-candidate4` |
| Native Forest save/cold Continue + published `2bc08eca` migration | 37/37 | `save-native-candidate4` |
| Native Forest save/cold Continue + published `0b9344` migration | 37/37 | `save-native-candidate4-original` |
| Both regions, generated interiors, map anchors and scene preservation | 64/64 | `maps-candidate4` |
| Pending original trials, both charts and another cold checkpoint | 14/14 | `maps-pending-candidate4` |
| Cream courier, entitlement guard, delivery and cold region latch | 18/18 | `maps-cold-cream-candidate4` |

The native save review accepts an actual Forest quest, opens its map, returns
through the original stairs and saves using the physical Drain Trophy. A new
core retains the entire `HandoffState`, earned draft inventory, all 500 discovery
bytes and the latched quest region without repeating the opening draft. Both
published ROMs create their own genuine extension-v2 checkpoint through the old
contract desk, courier quest and Trophy. The final ROM retains those saves'
inventory, journal knowledge, profile and appearance settings, retires the
unreachable Annex quest and selects a real regional chain target.

Map checks exercise actual doors, overview/zoom controls and exits. They verify
the semantic icons and objective tethers against actual discovered tile
coordinates. Paused previews preserve the complete room, both region worlds,
base and regional spots, hero, both handoff runtimes, saved handoff facts and
discovery records. Arrival foot probes and inventory checks explicitly verify
dry entry without Flippers; the earlier cart-channel drowning loop now has a
dry southern bank and passes its actual entrance/exit regression.

The pending-trial review consumes the exact genuine checkpoint from the final
native journey after its first three objectives, with all original trials
unearned. Neither chart invents an objective tile while the final seal is
waiting, and a further Trophy save/cold Continue retains step 3/state 0.

The Cream review follows the actual ladder and admitted graph to a courier,
accepts the parcel and verifies the Trophy's explanatory refusal to enable a
restriction that would strand that task. A real checkpoint preserves the active
quest, all handoff facts and anchors. After real delivery, the Trophy permits
the preference change; another cold Continue retains the same Cream giver
plan and run-start region.

No quest, inventory, completion, terrain, enemy, camera or pixel writes are
used. Private SRAM/title seed and hero navigation coordinates are disclosed
fixtures. Isolated map cases request the ordinary regional fade/load path;
the Cream and pending-chain reviews use actual regional travel. Captures are
unmodified 240×160 mGBA output, after native canvas upload. These tests qualify
map/save integration; the separate regional journey and mechanism reviews
qualify puzzle progression.
