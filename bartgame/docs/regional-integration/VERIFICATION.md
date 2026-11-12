# Regional integration verification

Runtime source: `51880a55e6ecf86728f3a0923e5547e7bdeed5a0`.
ROM SHA-256:
`0dd8554384b53e618140f8c61590fc7e6a7ff0888f296ece034a95f357b34fdd`.

The [acceptance contract](ACCEPTANCE.md) separates source connectivity,
production-C geometry, native access, actual mechanic completion and
preservation. The [review bundle](../../../regional-handoff-review/README.md)
contains the corresponding raw reports and actual mGBA images. Earlier
candidate and Annex results retain their original identities; they are not
relabelled as tests of this ROM.

For repository readability, large `report.json` files are compact summaries.
Their adjacent `report.json.gz` files decode to the exact original JSON hashes
recorded in `verification.json`; the full originals also remain in the native
evidence ZIP. PNG/GIF captures are copied unchanged.

## Ordinary access and display

| Final native review | Result | Scope |
| --- | ---: | --- |
| [Opening](../../../regional-handoff-review/validation/opening/report.json) | 18/18 | Three real choice rounds on three seeds; distinct offers, retained original gear, no idle reroll. |
| [Drain services and ladders](../../../regional-handoff-review/validation/hub/report.json) | 43/43 | Actual walking from the opening over the Drain bridge to its services and both wall ladders; payment, promised chest, hint, optional preference guard, ordinary toggle and return. |
| [Forest exploration](../../../regional-handoff-review/validation/access/report.json) | 12/12 | Actual Drain/Forest travel and dry walking to a generated entrance; map zoom at its real tile; A and walking entry; ordinary exit without bounce. |
| [Interior arrival safety](../../../regional-handoff-review/validation/arrivals/report.json) | 195/195 | 32 generated classes: 17 unsealed event families, 12 mechanism patterns and three traversal patterns. Ordinary loadout without Flippers, real A entry, 60 standing frames, Down exit and physical origin. |
| [Field graphics resources](../../../regional-handoff-review/validation/resources/report.json) | 210/210 | 42 Forest/Cream scenes over four seeds; allocated door storage and actual hardware OAM; no native allocation failure. |
| [Original-art preservation](../../../regional-handoff-review/validation/art/report.json) | 2,593/2,593 | Original sheet IDs, hardware geometry, palette and every original frame byte remain exact; two CreamFolk frames append. |

The opening, hub and Forest exploration reviews have only fresh private SRAM
and deterministic title-seed fixtures. They never assign hero position, health,
inventory, camera, progression or pixels. The wider interior/resource surveys
explicitly use hero navigation and ordinary room-load fixtures. They do not
claim natural exploration of every sampled room. Door input waits for genuine
hurt recovery instead of forcing a standing state.

The resource survey's maximum is 608 of 876 world OBJ tiles and 19 OAM
entries. The camera moves through its normal update; the review waits for
the pictured door to enter OAM. These are sampled field budgets, not an
assertion about every possible actor/clone/effect combination. The separate
performance review supplies the broader busy-room measurements.

The Forest art check protects all 530 original physical tiles referenced by
old mappings or animations. Exactly 17 explicitly named, formerly all-zero
`LH_MOB_*` mapping slots receive new regional transport art. No existing
visible metatile is exempted. Other old tileset, palette, title and sprite
contracts remain protected. The Cream wall ladder copies the original Forest
ladder stamp; the Drain's existing props and NPC positions remain.

## Production generation and independent reach

The [placement sweep](../../../regional-handoff-review/validation/placement/report.json)
executes actual Forest/Cream generators and the actual post-placement
object, fusion and mobility builders against native metatile metadata.
Across 1,024 seeds it checks:

- 102,400 closed/open room states and 94,208 generated door fronts.
- 12,288 required NPC fronts and all 711,476 requested original enemy
  spawns, with retained populations, distinct dry feet and unchanged old routes.
- 33,324 accepted physical field stamps, with a dry perimeter, confined
  changes and preserved original spawn feet. A separate actual-feet flood
  includes real object and mobility collision, alongside the production route
  validator.
- All 310 Blocks quest boards, all 2,048 red-fusion footprints, and all three
  field traversal patterns. Every sampled quest giver is initially reachable
  without tools or counted keys. Six quest kinds rotate between both regions;
  the larger Blocks board remains a verified Forest clearing.
- 47,104 live Forest map previews and discovered-anchor checks after opened
  gates and revisits. All 155 first Blocks-plan probes preserve exact live
  Room bytes, spots and captured reservations compared with a warm plan.

The declared host collision adapter is the existing coarse eight-pixel Room
grid. Fine-mask callbacks are no-ops in this adapter; their native restoration
and precise collision have separate tests. Unused controller/render functions
are removed by linker section collection, while the actual field builders,
their state and collision functions remain. No substitute geometry builder or
handwritten room generator is used.

The [independent reach review](../../../regional-handoff-review/validation/reach/report.json)
solves exported primitive production graphs in Python. It compares 393,216
exact Forest/Cream reach-mask pairs and 614,400 per-site wrappers over the same
1,024 seeds. Its expected masks never call the production reach query. It
varies all eight tool combinations, Pacci ownership, counted keys, four
original-trial fact states and opened gate bits. Forest uses weighted key
paths; Cream uses directed terrace nodes and the Cape-and-Pacci conjunction.

These are finite seed/property samples. They do not establish an exhaustive
32-bit seed proof or 102,400 native playthroughs.

## Mechanic completion and persistence

The six named deployment gaps are closed in the [current ledger](../../../docs/handoff-restoration/features.json).
The event, quest, chain, fusion and mechanism owners retain their exact scopes
in [event notes](../handoff-restoration/EVENTS.md),
[regional mechanism notes](../handoff-restoration/REGIONAL_MECHANISMS.md) and
[map/checkpoint notes](MAP_SAVE.md). In particular, genuine regional quest and
chain tests do not assign inventory, enemy HP/state, completion, gates, terrain
or video. Broad mechanism-tool tests use separately disclosed owned-equipment,
standing and immunity fixtures; they do not substitute for genuine earned-run
and input-only approach controls above.

The final mechanism replacement totals 167 checks from fresh cores. All 159
substantive checks require actual `GS_PLAY` and HP above zero; minimum observed
HP is 22. It covers actual representative controls, all three field routes,
a Cream parachute landing, once-only caches and a real red-fusion crossing.
Its broad all-42-family coverage means native instance/art/access coverage;
specialized reactions beyond the current action set remain source/host scope.
The earlier zero-HP run was invalidated and supplies no final qualification.

The additional Earth ending requires four real objectives, all three earned
trials in one original region, a real late guardian fight and the physical
Earth pickup. The existing Heart and Cream peak victories remain separate.
Won-run retirement, published-save migration, active quest/chain continuity,
actual map anchors and original music are independently reported in the review
bundle. The historical 494-row handoff ledger retains its per-feature native
limits; this report does not turn every code-connected row into an exhaustive
native pass.
