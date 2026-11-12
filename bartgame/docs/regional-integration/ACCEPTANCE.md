# Regional handoff integration acceptance

This is the acceptance contract for moving the Challenge Annex's working
systems into the ordinary Drain, Blighted Forest and Curdled Cream. It records
what must be demonstrated; it is **not a completion report**. Historical Annex
tests remain valid for their old scenes and ROM hashes, but do not establish
regional deployment.

The controlling sources are [chapter 06](../../../docs/newgame/06_CURRENT_GAME_DESIGN.md),
[chapter 07](../../../docs/newgame/07_PROCGEN_DESIGN.md), the
[item/economy chapter](../../../docs/newgame/05_ITEMS_AND_ECONOMY.md), and
[hub services](../../../docs/QUICKSTART_HUB.md). The current user specifically
requests integration in both playable regions and a Cream **wall ladder**
matching the Forest ladder. Existing Forest trials, boss wins, artwork outside
that authorized entrance change, and previously available mechanics remain.

## Evidence rules

- Source connectivity, an offline plan, a successful host simulation, a native
  picture, and a completed native interaction are different qualifications.
  Every promoted requirement states its actual scope.
- Host coverage executes the production C planner/geometry/state functions.
  A handwritten mock of expected placements cannot prove the generator works.
- Every native report names the frozen source commit, ROM SHA256, harness
  SHA256, seed, fixtures and input sequence. Screenshots are untouched 240×160
  emulator framebuffers. Composite room views are labelled separately.
- At least the Drain ladder/service approach and representative regional
  doorway/NPC approaches use actual movement from their ordinary arrival,
  without position or camera assignments. Broad isolated interaction tests may
  disclose navigation/loadout fixtures, but cannot substitute for these natural
  approach tests. No completion, reward, enemy HP/state, terrain or pixel writes
  may be used to manufacture success.
- Old publication evidence retains its original hash. A new ROM may use old
  evidence as a regression baseline, never as a relabelled native pass.

## Deployment matrix

| ID | Source requirement | Acceptance in the ordinary game | Proof required |
| --- | --- | --- | --- |
| `opening_loadout_flow` |05:130–137;06:12–18 | A new run offers three rounds of three choices before regional exploration. Key, reward/stat and skill rounds grant the selected items once. Continue/re-entry cannot reroll or duplicate them. The chosen loadout cannot invalidate the required area routes. | Real opening inputs plus inventory deltas; cold Continue; generation across opening capability masks. |
| `drain_services` |06:12–18; hub§3.2–3.3 | Shop, three bed offers, trophy/difficulty, hints and fusion information are reachable from physical Drain interactions. Existing Peddler and wizard behavior remains available. No Challenge-selection menu is needed to obtain normal run services. | Natural walking to service anchors; payment/refusal/heal/reward checks; exit and original NPC regressions. |
| `cream_wall_ladder` | Current user request | The Cream entrance depicts a continuous wall ladder in the selected Forest-ladder style, with a clear ascent cue. Its actual interaction follows the pictured ladder. Walking into it and A on its usable approach work; returning does not immediately re-enter. | Native approach/return clips; body/collision/art anchor checks; original Forest ladder still works. |
| `regional_event_placement` |06:90–118;07§D/E | Item, elite, stranger, waves/survival, pots, fairy, memory, floor switches, both block puzzles, torches and cleanup are placed as reachable generated nodes or ordinary cave interiors in both regions across seeds. Entering them uses a real regional doorway/feature and returns to its actual origin. Retired chest lottery and cage puzzle stay retired. | Production-plan family coverage, actual-room component/front checks, representative native entries in both regions and event completion inputs. |
| `paired_events` |06:99–115 | Learn and Recall have distinct regional locations and a shared saved sequence. Portal trial and pocket form a bounded pair; a visible physical access changes after the trial/fusion and the pocket always has a valid exit. Optional visits cannot pre-complete a later chain objective accidentally. | Pair-map/solver checks; real Learn→Recall and trial→pocket travel; save/reload and return controls. |
| `regional_quest_placement` |06:122–143 | The seven quest forms are offered by regional NPC/content sites, with actual origin/receiver coordinates and region/cell identities. Quest type coverage rotates across seeds rather than dumping all types into a menu. Existing Hermit/Nun/Gardener/Stranger content remains. | Plan coverage for all seven; native giver/start and success for each; negative and persistence controls scoped per form. |
| `quest_courier` |06:132;07 token/reach rules | A real giver in Forest can direct delivery to Cream, or vice versa. The destination is reachable with the live run's inventory/world facts. Delivery is not an Annex-to-field shortcut or a menu warp. The active errand survives ordinary room/area changes and cold Continue. | Live origin/destination state, actual regional transfer and receiver interaction; once-only reward and save proof. |
| `quest_stakes` |06:135–143 | Difficulty stakes are announced and latched at quest start. Time limits, capture/stealth, cargo through two waves, hidden-property lookup and block solutions remain physical mechanics after deployment. Leaving a room does not falsely fail a cross-room quest or silently complete it. | Relevant success/failure paths and timers; stakes cannot increase mid-quest; cancellation/escape controls. |
| `regional_waves_and_chain` |06:24–35,61–82 | Both regions host escalating, quota-driven waves on the player's current reachable component. Replacements respect live-count, actor and graphics budgets. First regional clear pays once; claiming it does not stop later waves. A wave can never count an unreachable foe on another Cream shelf or beyond water. | Component/spawn host sweeps; actual multi-wave run and first-prize/re-entry checks; live budget/frame traces. |
| `live_chain_targets` |06:24–35,184–190 | Each of four objectives is selected only after its predecessor, using current inventory and actual reach facts. EVENT/WAVE/BOSS/QUEST/ITEM objectives refer to real generated nodes/items and are explained with useful regional directions. No objective-travel menu teleports the player. | Independent target reach assertions for varied live masks; actual four-objective completion path; original Forest trial anti-bypass controls. |
| `regional_fusion_consequences` |05:104–121;07 token vocabulary | Matching colored/golden halves cause persistent regional consequences: a real cache, cave access, seal or useful crossing changes in the generated world. Generic locked doors remain their own type. Some content stays available without fusion; no mandatory route depends on random half drops. | Before/after actual physical geometry/content; half consumption; revisit/cold Continue; optional-access reach proof. |
| `regional_mechanism_placement` |03 world vocabulary;07§C–E | Mechanism families are reachable as coherent generated field features or themed regional interiors. Their purpose is a route, obstacle, interaction or reward, rather than a renamed fixed demonstration court. All implemented families remain naturally eligible across tested seeds. | Production family/footprint coverage; original approach/exit reservations; native representative tool/switch/key/push/Minish/clone interactions. |
| `regional_traversal` |02 movement;03 layers;07 directed edges | Minecart rails connect valid stops; an upper/lower bridge supplies usable distinct routes; parachute descent has an actual safe lower landing in Cream. Traversal does not overlap a mandatory arrival, sever an old route or create an invisible collision plane. | Actual component/landing checks; natural boarding/dismount/over/under/descent clips; unsupported water and supported deck controls. |
| `persistence_and_maps` |07 token vocabulary/verification;09 saves | Planned sites, completed states, regional wave progression, fusion facts, active quest and chain targets survive the intended room/re-entry/save boundaries. Maps and hints identify actual features and their real room coordinates. Old saves remain readable; victory still retires a won run. | Site-ID nonoverlap checks; visit/revisit/cold Continue; real map/zoom and existing save/victory regression. |
| `preservation_and_resources` | Current user preservation;07§E;08 performance | Additions preserve the three required Forest trials, Cream graph/traversal/boss, chosen ordinary sword, original music, other existing art and old interaction semantics. Added actors/NPC faces/objects fit budgets with no sustained enemy-room slowdown. | Old/new asset comparison, earned Forest/Cream routes, music/modal boundaries and representative worst-case native frame/resource traces. |

## Complete family coverage

The event set is based on the active source vocabulary, not the retired table
rows. It includes the existing additional survival, portal/pocket, golden-seal,
traversal and mechanism adaptations where they have playable implementations.
The placement report must enumerate which region, seed, room, component,
physical access and prerequisite exposes each family. Seeing the enum in a
plan is insufficient when the room could not reserve an actual footprint.

The quest coverage set is POT, HUNT, SCAVENGER, STEALTH, CARRY, COURIER and BLOCKS.
The mechanism coverage set is the production module's implemented family
registry, including its specialized tool/counter and traversal objects. The
report must retain that registry/version so a future added family cannot be
silently omitted by a stale hardcoded count.

Coverage across seeds is intentional. A single run must be coherent, bounded
and completable; it need not contain every optional family or require visiting
all 25 rooms. Rare or tool-gated content may remain visible before the tool is
owned, provided its approach/return is safe and mandatory progression does not
depend on an unbounded random reward.

## Solvability and compatibility decisions to record

The verification must include original world facts, not just equipment bits.
The original Forest's three trial completions remain required even when a
draft/shop grants their tools. Optional new features may reserve side pockets
and interior accesses; they must not erase an old mouth, gate, arrival, chest,
NPC or the only route to one.

The handoff's original final chain ended a run. The current game already has
approved Forest and Cream boss victories, and the user requires preserving
those features. The adopted compatibility rule is an **additional regional
Earth Element victory path** after the four real objectives. The original
Heart and Cream boss victories stay available. Tests must establish all three
outcomes and their completed-run reset, rather than silently replacing a boss
win or relabelling an optional Annex contract as the historical run loop.

The extra ending also preserves the original area progression: an actual set
of three Forest trial completions, or all three Cream trial rewards, is
required before the final seal is eligible. The closing objective must be a
genuine regional boss or late elite. Four early optional wave clears cannot
substitute for the original trials. Native tests must observe the physical
Earth Element pickup before victory and include the early-chain refusal.

Likewise, ordinary mode must not acquire accidental entitlement locks. If an
existing optional entitlement mode remains, its restrictions and reach solver
must agree and explain a blocked access rather than leave an inert feature.

## Qualification status

This remains the criteria document. Final results and their precise limits
are in [VERIFICATION.md](VERIFICATION.md), its [machine evidence index](verification.json)
and the [current audit](../../../docs/handoff-restoration/AUDIT.md#current-regional-integration-2026-11-12).
The final source `51880a55e6ecf86728f3a0923e5547e7bdeed5a0` closes the six named
deployment gaps. The five formerly `partial_integration` rows now have scoped
native sample qualification. Other per-feature native obligations and all
historical baseline/ROM identities remain distinct.
