# Mechanisms placed in the generated regions

The regional planner assigns these features to ordinary Forest and Curdled
Cream nodes. Generated entrances lead to themed, single-purpose puzzle rooms;
small field mechanisms and traversal routes are also stamped into the outdoor
rooms themselves. The old multi-station courts remain compatibility code,
not the normal game's route to this content.

The normal geometry owns its doors, landings, required tools and boss paths.
A field stamp is admitted only on a reserved component. Hazards and blocking
material stay inside its footprint, with an ordinary dry perimeter so an old
route can pass around the optional feature. Each builder checks the final
room with the production regional route validator. A rejected stamp restores
the footprint's ground, overlay and visual underlay and resets its controller.
Qualification verifies the actual builder succeeded, not just that the
planner found a rectangle.

## Twelve regional mechanism puzzles

Horizontal mirroring and seeded ferry type vary the layouts. Each room keeps
its permanent southern return and places a golden reward mark beyond its own
mechanism. Several rooms also contain persistent optional side caches. The
whole set covers the42 existing mechanism families across seeds; the generator
does not paste the old four workshops into every cave.

| Pattern | Physical puzzle and useful objects |
| --- | --- |
| Store room | Push a statue onto a pressure plate. The metal door stays open while a block or copy holds the plate; a brief visit by Bloom does not latch it. Graves, furniture and pullable rocks share its movement vocabulary. |
| Sealed vaults | A Big Key vault, a light seal and a guardian seal occupy separate enclosures. The key is physically supplied before its optional door when absent. The guardian vault holds the main reward. |
| Ferry | A broad moving platform carries Bloom across a pit, lava or water channel to the far bank. Its old footprint carries the body before its position changes, preventing edge riders being left behind. |
| Breathing mine | A whirlwind crosses a short pit while fans, steam, rotating bars and fire chains create timing hazards. |
| Buried garden | Reveal a loose stair, water a beanstalk and turn the weather vane to release a three-part northern seal. |
| Linked pockets | Visible paired stairs/holes and violet pads join separated pockets; timed and rotating trapdoors occupy the lower route. |
| Missing bridge | A handle on the near bank writes a real three-tile-wide bridge over the gap. Its position follows the mirrored room, rather than a hardcoded court coordinate. |
| Key crypt | Pull, push and heavy handles release the central seal. Farm/Grave keys guard optional side enclosures. Four Sword staging plates permit the copy alternative to strength. |
| Mirror shrine | A Mirror Shield reflects the emitter into a receiver on the gate's front face. The actual receiver opens the physical northern seal. |
| Echo roots | Three real copy footprints hold the plates and latch the gate. A jar portal and a four-pixel gap lead to a separate small-form cache. |
| Tool crypt | Actual Pacci, arrow and sword/thrown-object contacts turn three seals. Suction provides a clod to launch; springs, dig soil, dash stone and a water sprout add optional tool routes. A visible arrow pickup prevents an owned Bow with zero ammunition stranding the puzzle. |
| Frozen store | Fire or mineral water melts the great ice, flame frees the flower, and flame or suction removes the barrel's silk. Their three states release the northern seal. |

`handoff_objects_can_solve` supplies the chain's capability check. A puzzle
requiring a bottle, strength/copies, Mirror Shield, Four Sword, Pacci/Bow or
fire/mineral water is not selected as a live chain objective before those
capabilities exist. Optional item-gated content may still be seen early.
The mineral-water check uses actual bottle contents, not a stale inventory
history bit. Small outdoor variants have their own capability predicate.

## Outdoor mechanisms and red fusion

The four compact field families are a pressure-cache, a frozen-flower/web
cache, a thirsty root and a Pacci-flipped pot. Their reward mark responds to
actual object state. Standing on a pressure plate and leaving it does not
substitute for retained weight.

A red fuser's five-by-five feature contains a three-by-three pool, a dry
center island and a missing southern approach. The matching fusion writes the
walkable bridge. Its reward requires Bloom's feet on the island tile, not just
interaction range from the bank. The outer dry ring preserves the room's old
connections. The original island floor is retained, including its regional
material and blight stage.

Field admission accepts noninteractive floor flecks and the three explicit
Cream mould overlays, whose prop-priority ink does not mean an obstacle.
Admitted dressing is cleared only inside the reserved feature. Solid tiles,
special surfaces and interactive props remain vetoes. This distinction fixed
a native failure where otherwise valid Forest and Cream rectangles silently
failed the stricter builders.

## Regional traversal routes

The three traversal families use the same portable controller in generated
caves and compact outdoor footprints. Field caches and interior caches have
separate saved claim bits.

- **Minecart:** connected rails join two dry stations across visible water.
  Suspended rail drawings retain WATER semantics; the mounted cart supplies
  support. A requests dismount at the next station, and regional stops select
  a genuinely dry adjacent landing. Reaching the far station wakes its cache.
- **Over/under bridge:** the end ramps enter the upper collision plane and
  its rails contain the rider. A perpendicular dry bank remains below it.
  Crossing from one ramp to the other wakes the upper cache; walking beneath
  the span provides a separate lower-bank cache.
- **Parachute shelf:** a marked upper edge launches an actual controlled
  descent over a cliff face to its dry lower shelf. Left/right steers, Up
  slows, Down accelerates and A folds the silk. Reaching the landing wakes
  its cache. The optional stamp's outer path remains available for return.

Small field stamps do not pretend to add unverified graph edges between
Cream terraces. Their cliff and landing are local to a reserved safe feature;
the existing regional climbing/drop graph remains authoritative.

## Verification scope

`tools/regional_mechanisms_host.py` compiles the actual production C with
explicit room/input/inventory fixtures and undefined-behavior/bounds checking.
The current pass has 23,487 checks: 15,105 object checks and 8,382 mobility checks.
It covers 64 seeds across 12 puzzles, all 42 object families, 384 field traversal
builds in both area contexts, protected dry perimeters, real state counters,
pressure retention, red-fusion floor changes, mounted water support, safe
stops, both bridge planes, controlled descent and once-only rewards.
Every traversal template also checks the ordinary unassisted south arrival
and return feet boxes. The cart's channel stops north of that bank; it cannot
require Flippers simply to enter or leave its chamber.

The previous 1,511 traversal and 277 mechanism checks still pass. These host
checks do not establish rendering, normal door access or unassisted gameplay.
`tools/regional_mechanisms_native.py` separately surveys actual generated
regional doors and exercises the controllers in the normal ROM. It compiles
private-record offsets with the ARM compiler against the exact pinned source,
rather than hand-maintaining offsets. Its report discloses navigation/loadout
and player-protection fixtures; it never writes completion, fusion, terrain,
enemy state or video data. Native qualification is recorded with the final
integrated ROM identity after the run succeeds.

The final C4 native qualification has 167 passing checks across five groups
(114 main, 20 field, 5 lily-ferry, 5 lava-ferry and 23 Cream-field checks).
Every substantive check starts from a fresh seeded core and requires an
active game with positive player health; the input driver stops on depleted
health. All 159 substantive checks passed, and every recorded input interval
kept positive health. Earlier diagnostic runs whose long survey depleted
health are invalidated and excluded from this qualification.

The native evidence covers all 42 families' ordinary regional access and
exact sprite uploads; the physical reaction checks cover representative
push, pressure, Cape/Minish refusal, copy formation, Mirror Shield, bottle,
weather, sword, arrow, Pacci and fire interactions. It also covers actual
outdoor cart/upper-bridge/underpass/parachute routes and their separate
once-only caches, the matching red half and physical island crossing, and
a parachute landing specifically in a Cream field. All three traversal
interiors remain dry for 120 real frames without Flippers, and actual
southward walking returns to each parent. This does not claim a native test
of every specialized reaction merely because its sprite was instantiated.

Qualification identity: source `51880a55e6ecf86728f3a0923e5547e7bdeed5a0`,
ROM SHA256 `0dd8554384b53e618140f8c61590fc7e6a7ff0888f296ece034a95f357b34fdd`,
harness SHA256 `1de971a45ff5ab0cff27ba111ba6d40d6a92bb5ef97b11916de0685c0b34adbe`.
Native PNGs remain unedited 240×160 frames. GIFs are diagnostic encodings;
stepped navigation can play slowly, so input/frame traces establish timing.

The final workspace proof is
`/workspace/setup/regional-integration/mechanisms-live-c4/manifest.json`, with
`main`, `fields`, `lily`, `lava` and `cream` report groups. The published
[main report](../../../regional-handoff-review/validation/mechanisms/report.json),
[field report](../../../regional-handoff-review/validation/mechanisms-fields/report.json)
and [Cream report](../../../regional-handoff-review/validation/mechanisms-cream/report.json)
contain the corresponding traces. The manifest lists 111 raw native media
files, including positive-health replacements for the invalidated diagnostic
run. Gilt is explicitly decreased to 0 before isolated cache accounting; no
player HP or completion/fusion/claim flags are assigned.
