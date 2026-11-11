# Original-game handoff restoration audit

This records the **current additive implementation and its qualification** for the restoration requested on 2026-11-11. All 494 entries retain a historical baseline plus a separate current status, executable evidence and test scope in [features.json](features.json). Historical baseline: `3fa7774eb72e67f155f91107a772ca1fd202fc8f`. The standalone game is `bartgame/`; the outer repository contains the TMC/QUICKSTART oracle.

## Authority and scope

The authoritative transition is [00_README](../newgame/00_README.md), interpreted through [12_FROM_SCRATCH_ENGINE](../newgame/12_FROM_SCRATCH_ENGINE.md). All 13 handoff chapters, 00–12, were read. Referenced item, hub, puzzle, portal, lantern/gust, shop, simulation and source inventories were inspected. [features.json](features.json) retains file hashes, exact tier entries, every item enum value, 71 curated enemy/form entries and 213 raw enemy forms.

Current user instructions authorize additive implementation and preservation. The historical standing-rule clarification in 00 does not create a new approval barrier. Existing sprites/art, mechanics, three required Forest trials, chosen 18-update sword attack, original music, cabinet and fresh-run-after-win behavior must remain. The user explicitly replaces ordinary timed bombs with charge-and-throw impact bombs.

The nine-area architecture is a future capacity requirement. The user supplies one new area now, The Curdled Cream; seven unnamed areas cannot be invented as completed features. The existing Drain remains the authored hub, rather than recreating Nintendo Wind Tribe maps or characters.

## Source discrepancies that affect implementation

| Topic | Resolution |
| --- | --- |
| Charms | `src/game.c:4505–4534` defines 21 food bits: 20 ordinary tier items plus special Fleet. “Fourteen” in 05 and the older HANDOFF_GAME is stale. Three bottled charms are additional and stack. |
| KEY rewards | `src/game.c:6515–6522` includes KEY in QS_CAT_DROP. Older exclusion/region-wave-only wording is stale. Mandatory keys still belong before locks by construction. |
| Ammo/butterfly tiers | Newer source makes Bomb Bag, Quiver and three Butterflies COMMON; older item-tier prose says UNCOMMON. |
| Chain length | Newgame 06 and the live constant use four steps; older HANDOFF_GAME says five. Preserve current Forest trials and add the adaptive chain alongside them. |
| Wave shapes | The latest source table has plain mixed plus ten named shapes, eleven rows total. Handoff prose saying ten is stale. |
| Wallets | Wallet and Big Wallet are explicitly excluded in QUICKSTART_ITEM_TIERS §1 despite the raw vanilla enum. |
| Retired puzzles | Chest lottery is pulled from the draw; cage-and-switch was retired for a lifting bypass. Existing current chest rooms stay. |
| Health | Eight HP per heart, starting at 24 HP. The old hub note saying four HP is not the current unit. |
| Raw enemies | 71 curated picks across 57 IDs form the ordinary roster. The 213 raw rows include children and unsafe/scripted forms; they are not 213 independent bare-spawnable AIs. |
| Bosses | The documented additional boss forms are green/electric ChuChu and Big Octorok, with scripted setup. Keep the selected broken purple Heart. |
| Menu constraints | Fire Rod/Pacci exclusivity only solved an old 12-cell menu limit. An independent expanded menu may support both. |
| Research proposals | Elemental player weapons and the cucco ally summon are feasibility notes, not completed legacy features. They are identified separately. |
| Old formats | Struct offsets, LZ77, flag banks, m4a, agbcc and original script/save formats are oracles, not required implementations in the new engine. |

## What the baseline already has

The starting standalone build has selected Bloom movement, roll, cape, lift/throw, sword and shield behavior; seven usable equipped items plus key tools; a 25-room Forest with three guaranteed item trials; ten mystery kinds; six NPC roles; and nine enemies, including the recent Rope/Leever/Helmasaur adaptations. It also has the current menus/themes/maps, original music, discovery cabinet and completed-run invalidation. A related current enemy family is **not** proof that every source form or special counter is complete.

At that baseline, missing vocabulary included Gust/Pacci/Mitts/Boots/Flippers/bottles/sword arts/clones; ice/swamp/lava/moving platforms/cart/Minish puzzles; matching kinstones/fusers; tiered economy and charms; paired memory/cleanup/solver-backed boards; seven full quest forms; adaptive chain/endless role waves; meta progression; and Curdled Cream climbing.

## Ledger conventions

Each row is separately actionable. The machine ledger adds detailed requirements, citations, baseline evidence, an owner and acceptance criteria. “Partial” means related current behavior, not finished handoff coverage. Current restoration status and separate code/host/native qualification fields are populated for all 494 entries. A catalogue picture, connected mechanic, host proof and native input test remain different evidence.

| Baseline status | Count |
| --- | ---: |
| implemented_existing | 24 |
| missing | 388 |
| needs_adaptation | 1 |
| partial | 45 |
| partial_family_adaptation | 13 |
| reference_only | 21 |
| retired | 2 |

## Complete runtime and reference ledger

| ID | Requirement | Baseline | Owner | Source |
| --- | --- | --- | --- | --- |
| `preservation.existing_features` | Preserve every existing feature: Add systems without removing approved Forest trials, rooms, NPCs, items, UI themes, audio, discovery cabinet, difficulty or current run flow. | implemented_existing | root | Current user request and preceding approvals |
| `preservation.existing_art` | Preserve existing artwork: Keep existing art/sprite asset data unchanged; append new art only for newly added content. | implemented_existing | root | Current user request and preceding approvals |
| `preservation.win_continue` | Won runs cannot be continued: Preserve completed-run invalidation and initiate a new run after a win. | implemented_existing | root | Current user request and preceding approvals |
| `preservation.sword` | Preserve selected sword feel: Keep approved 18-update step-and-cut attack and existing readable live hit volume; do not restore obsolete 15-frame attack over it. | implemented_existing | root | Current user request and preceding approvals |
| `preservation.forest_trials` | Preserve required Forest tasks: Keep three guaranteed required Forest task rewards and barriers; optional adaptive chains cannot replace them. | implemented_existing | root | Current user request and preceding approvals |
| `player.walk` | Walking and facing: Keep fixed-point position/collision resolution, cardinal input and facing; reference walk 1.25px/frame. | implemented_existing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.roll` | Rolling: Keep roll movement, invulnerability windows, state interruptions and approved clean art. | implemented_existing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.itemget` | Item acquisition: Block ordinary control, announce and grant actual inventory; restore control after pickup. | implemented_existing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.hurt` | Damage and knockback: Apply damage, 1.5 px/frame for 8-frame knockback, 30-frame invulnerability and visible feedback without artificial hit pause. | implemented_existing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.fall_respawn` | Pit fall and safe respawn: Distinguish pits from exits, apply 2 HP fall damage and return to validated safe-ground history. | implemented_existing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.drown` | Drowning and safe respawn: Without Flippers, entering deep water drowns then returns to safe reachable ground. | implemented_existing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.jump` | Cape jump and height: Keep collision-aware forward jump, z/gravity and gap-crossing, not merely a visual hop. | implemented_existing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.lift_carry_throw` | Lifting carrying and throwing: Preserve existing bush/rock/boulder/pot pickup, carried-object layering and physical throw impacts. | implemented_existing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.talk` | Talking: Preserve NPC interaction and readable dialogue without movement leaks. | implemented_existing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.shield` | Shield use: Preserve directional block, slow movement and correct north-facing behind-body layering. | implemented_existing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.push` | Push objects: Resolve push motion and grid/world collision; reference 0.5 px/frame; support puzzle rule hook. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.pull` | Pull objects: Allow eligible generic objects to be pulled, separate from block puzzles whose rules prohibit pulling. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.sword_charge` | Sword charge: Hold to charge with readable cue; 80 frames or 40 with Fast Spin; reference movement 0.875px/frame. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.spin` | Spin attack: Charged radial attack with coherent active hitbox and reference 34-frame duration. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.thrust` | Sword thrust: Directional thrust with distinct hitbox and weapon-level damage. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.sword_beam` | Sword beam: Launch projectile at full health or with appropriate charm; sword-level eligibility and beam damage. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.bounce` | Bounce: Implement forward bounce using height physics, z=2 / forward=1. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.spring_jump` | Spring-hole jump: Pacci-activated spring hole launches z=1.625 / forward=0.46875 and reaches its declared destination. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.pegasus_dash` | Pegasus dash: 16-frame windup, 3 px/frame forward dash, wall interruption and DashAttack support. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.swim` | Swim: Flippers permit controlled movement through deep water, speed upgrade and valid bank entry/exit. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.dive` | Dive: Swimming dive input/state alters appropriate hazard interaction; visibly enters and exits dive. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.climb` | Climb: Ladders and GripRing walls enter distinct climb state, allow up/down motion, resume walking only at legal landing. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.burning` | Burning: Fire applies burn behavior/forced movement reference 3 px/frame; immunity charm suppresses it. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.lava` | Lava: Hazard surface causes burn/damage and safe recovery; protection/crossings remain item-aware. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.frozen` | Frozen: Ice attacks genuinely lock control and allow documented escape/recovery; immunity suppresses status. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.captured` | Captured and released: Capture enemies constrain control then release safely; recovery does not strand player or retain stale state. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.minish` | Small form and portals: Add shrinking/return portals with small-form collision 4×4 and small entrances; preserve normal Bloom and original art. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.clone` | Four-Sword clones: Charge and split on clone tiles, create followers/pressure coverage, cancel safely when blocked or hurt. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.parachute` | Parachute descent: Add controlled parachute state for appropriate vertical links without replacing existing falls. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.minecart` | Minecart riding: Enter cart, follow rails and exits, update layer/collision and leave at safe stops. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.sleep` | Sleeping: Inn sleep/payment/heal state and fade return to valid player state. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.conveyor` | Conveyor or wind pushing: External movement sources alter position through collision rather than teleporting. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.entrance` | Entrance and room transition state: Maintain independent semantic doorway/ladder/scroll transitions and valid arrival state. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.empty_bottle` | Bottle use: Capture eligible water/fairy or empty contents with inventory and animation changes. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `player.status_visual` | Status visual feedback: Temporary drug/aura/curse feedback has bounded duration or explicit run-long ownership and clean restoration. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md |
| `surface.dry` | Dry land: Ordinary dry traversable ground remains visually and mechanically distinct from hazards. | missing | world_objects | docs/newgame/03_WORLD_TILES_COLLISION.md |
| `surface.shallow` | Shallow water: Slow movement and splash without swimming or false dry spawn eligibility. | missing | world_objects | docs/newgame/03_WORLD_TILES_COLLISION.md |
| `surface.wade` | Wading bank: Transition consistently between ground/shallow/deep water. | missing | world_objects | docs/newgame/03_WORLD_TILES_COLLISION.md |
| `surface.ice` | Ice: Inertia/sliding with collision, not decorative recolor. | missing | world_objects | docs/newgame/03_WORLD_TILES_COLLISION.md |
| `surface.swamp` | Swamp: Sink unless moving or crossing with Boots/Cape; safe failure recovery. | missing | world_objects | docs/newgame/03_WORLD_TILES_COLLISION.md |
| `surface.dust` | Dust: Dust puff surface plus separate removable-dust object semantics. | missing | world_objects | docs/newgame/03_WORLD_TILES_COLLISION.md |
| `surface.hole` | Destination hole: Hole transition target is validated and distinct from damaging pit. | missing | world_objects | docs/newgame/03_WORLD_TILES_COLLISION.md |
| `surface.button` | Button: Standing on button presses tile/state and signals linked gate. | missing | world_objects | docs/newgame/03_WORLD_TILES_COLLISION.md |
| `surface.slope` | Slopes: Horizontal/vertical slopes apply reference 0.3125px/frame speed subtraction. | missing | world_objects | docs/newgame/03_WORLD_TILES_COLLISION.md |
| `surface.crumbling` | Crumbling floor: Contact/timeout causes floor to collapse to pit with state persistence. | missing | world_objects | docs/newgame/03_WORLD_TILES_COLLISION.md |
| `surface.ledge` | Directed ledges: Only legal downward direction permits hop; both in-room and cross-screen graph use directed edges. | missing | world_objects | docs/newgame/03_WORLD_TILES_COLLISION.md |
| `surface.bridge_layers` | Bridges and underpasses: Independent collision/elevation layers permit crossing above or below without collision leaks. | missing | world_objects | docs/newgame/03_WORLD_TILES_COLLISION.md |
| `surface.collision_shapes` | Collision shapes: Support full, partial and directional/diagonal collision footprints; visuals agree with solid mask. | missing | world_objects | docs/newgame/03_WORLD_TILES_COLLISION.md |
| `worldverb.cut` | Cut vegetation: Sword cuts grass, bushes and designated tree/sign variants; reveals only reachable drops. | missing | world_objects | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `worldverb.bomb` | Bombable objects: Bomb blast opens explicitly bombable wall/rock and persists opening. | missing | world_objects | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `worldverb.arrow` | Arrow switches: Arrows reach distant/eye switches and use proper projectile collision. | missing | world_objects | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `worldverb.boomerang` | Boomerang switches: Boomerang toggles eligible distant switch, returns to player and counters designated enemies. | missing | world_objects | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `worldverb.fire` | Fire: Lantern and Fire Rod light torches/burn eligible webs/vegetation; fire melts designated ice. | missing | world_objects | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `worldverb.gust` | Suction: Gust clears dust and webs, strips designated armor and moves eligible platform. | missing | world_objects | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `worldverb.pacci` | Flip and spring: Pacci flips eligible enemy/object and primes spring hole; supports Lakitu counter. | missing | world_objects | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `worldverb.mole` | Dig: Mitts dig soft earth and dig-wall faces, reveal buried quest content and drops. | missing | world_objects | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `worldverb.heavy` | Heavy lifting: Bracelets lift eligible heavier rocks/objects; all-size lifting when fully upgraded. | missing | world_objects | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `worldverb.rockbreaker` | Break rocks: RockBreaker skill breaks specified rocks without granting blanket damage to permanent scenery. | missing | world_objects | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `worldverb.clones` | Clone pressure puzzle: Multiple clone pads/pressure plates accept actual clone occupancy. | missing | world_objects | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `worldverb.light` | Darkness: Room lighting reflects lantern/lit torches; never unplayably black without required tool. | missing | world_objects | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `object.pot` | pot: lift and smash; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.bush` | bush: cut/lift with drop; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.giantRock` | giantRock: heavy lifting obstruction; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.pushableRock` | pushableRock: collision-aware pushing; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.pushableStatue` | pushableStatue: push and activate target; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.pushableGrave` | pushableGrave: push to reveal passage; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.pushableFurniture` | pushableFurniture: persistent movable obstacle; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.chestSpawner` | chestSpawner: stateful wooden reward chest; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.specialChest` | specialChest: stateful valuable ornate chest; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.itemOnGround` | itemOnGround: visible pickup and true grant; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.heartContainer` | heartContainer: max-health reward; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.rupee` | rupee: denomination pickup; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.fairy` | fairy: heal/capture; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.lockedDoor` | lockedDoor: consume counted small key or required state; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.metalDoor` | metalDoor: open on linked switch/fight condition; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.bossDoor` | bossDoor: require Big Key; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.lightDoor` | lightDoor: open from light condition; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.houseDoorExterior` | houseDoorExterior: visible entrance and valid return pair; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.houseDoorInterior` | houseDoorInterior: paired interior return; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.button` | button: pressable switch; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.pressurePlate` | pressurePlate: occupancy-controlled state; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.hitSwitch` | hitSwitch: weapon-hit toggle; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.eyeSwitch` | eyeSwitch: arrow target; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.lightableSwitch` | lightableSwitch: fire/light target; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.pullableLever` | pullableLever: pull activation; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.pushableLever` | pushableLever: push activation; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.bigPushableLever` | bigPushableLever: larger constrained push lever; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.hittableLever` | hittableLever: strike activation; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.lamp` | lamp: light fixture; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.flame` | flame: fire hazard/light; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.lightRay` | lightRay: directional ray/puzzle; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.litArea` | litArea: bounded illuminated region; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.trapdoor` | trapdoor: conditional floor opening; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.rotatingTrapdoor` | rotatingTrapdoor: rotating floor hazard/link; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.crackingGround` | crackingGround: timed cracking and collapse; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.floatingPlatform` | floatingPlatform: rideable water platform; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.lavaPlatform` | lavaPlatform: rideable lava crossing; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.lilypadLarge` | lilypadLarge: large water stepping platform; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.lilypadSmall` | lilypadSmall: small water stepping platform; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.minecart` | minecart: rideable rail actor; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.railtrack` | railtrack: connected route and stops; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.fan` | fan: directional fan source; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.fanWind` | fanWind: collision-aware push field; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.whirlwind` | whirlwind: vertical/air lift; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.steam` | steam: timed environmental emission; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.guruguruBar` | guruguruBar: rotating arm hazard; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.fireballChain` | fireballChain: linked rotating fire hazard; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.ladderUp` | ladderUp: climbable upward link; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.hiddenLadderDown` | hiddenLadderDown: revealed downward link; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.beanstalk` | beanstalk: vertical traversal link; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.warpPoint` | warpPoint: explicit activated portal; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.minishPortalStone` | minishPortalStone: shrinking/return portal; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.jarPortal` | jarPortal: small-form portal; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.smallIceBlock` | smallIceBlock: fire-meltable obstacle; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.bigIceBlock` | bigIceBlock: large fire-meltable obstacle; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.frozenFlower` | frozenFlower: fire-reactive frozen growth; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.barrelSpiderweb` | barrelSpiderweb: burnable/suction web barrier; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.spiderWeb` | spiderWeb: facing-aware removable web; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.removableDust` | removableDust: suction-cleanup target; has distinct added art where necessary, collision, interaction and saved resolved state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.itemForSale` | itemForSale: priced persistent run stock; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.deathFx` | deathFx: budgeted death effect; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.smoke` | smoke: budgeted smoke effect; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `object.specialFx` | specialFx: budgeted special effect; has distinct added art where necessary, collision, interaction and saved resolved state. | partial | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#objects-192-files-srcobject |
| `manager.hole_targets` | Hole destinations: Resolve destination on actual containing region/room with valid safe landing. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md |
| `manager.bomb_wall` | Bomb-wall state: Open and persist bomb wall in both rendering and collision. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md |
| `manager.torch_timeout` | Torch timeouts: Timed torches burn out until all lit latch; light level follows state. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md |
| `manager.tile_flip` | Tile-flip puzzle: Interacting flips local tiles and evaluates solver-checked target. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md |
| `manager.fight_doors` | Fight-door lifecycle: Lock on entering fight, spawn reachable enemies, unlock on actual completion. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md |
| `manager.timed_spawn` | Timed enemy spawns: Spawn scheduler respects occupancy, live caps and component. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md |
| `manager.logic` | AND and OR flags: Linked puzzle requirements combine explicit states safely. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md |
| `manager.tile_change` | Tile change observation: Changing semantic tile updates visuals, collision and trigger state together. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md |
| `manager.secret` | Hidden content reveal: Revealing valid secret creates visible content exactly once. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md |
| `manager.transform` | Transform portals: Transform/de-transform player with legal landing and collision reset. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md |
| `manager.hint` | Graph-derived hints: NPC hint reflects current reachable objective/key/route, without stale hard-coded region claims. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md |
| `manager.furniture` | Furniture coordination: Prevent pushed furniture from blocking reserved exits or invalidating mandatory puzzle. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md |
| `manager.appearing_bridge` | Appearing bridge: Puzzle state inserts/removes walkable bridge and visual art consistently. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md |
| `manager.weather` | Weather layers: Budgeted rain/cloud/steam overlays preserve gameplay readability. | missing | world_objects | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md |
| `item.SMITH_SWORD` | Smith sword: Base sword behavior; preserve current Bloom sword art. | implemented_existing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.GREEN_SWORD` | Green sword / beam charm: Preserve source dual role as weapon enum and run-long beam charm; avoid ambiguous silent substitution. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.RED_SWORD` | Red sword upgrade: Stronger next sword rung; obtained as item, no downgrade. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.BLUE_SWORD` | Blue sword upgrade: Rare upgrade requires Red Sword. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.FOURSWORD` | Four Sword: Top sword plus clone/split mechanics. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.BOMBS` | Blightseed bombs: Charge-and-throw impact bombs per current explicit request, also bombable-wall key. | needs_adaptation | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.REMOTE_BOMBS` | Remote bombs: Separate controllable detonation upgrade requiring bombs; explicit trigger distinct from ordinary impact bomb. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.BOW` | Bow: Directional arrow projectile/ammo. | implemented_existing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.LIGHT_ARROW` | Light arrow: Bow upgrade permits charge and stronger projectile; requires Bow. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.BOOMERANG` | Boomerang: Outgoing and returning projectile, switch utility and Spark counter. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.MAGIC_BOOMERANG` | Magic boomerang: Upgraded controllable/ranged return, requires Boomerang. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.SHIELD` | Shield: Directional blocking and slow stance; existing art preserved. | implemented_existing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.MIRROR_SHIELD` | Mirror shield: Upgraded reflected projectile/light behavior, not just defense flag. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.LANTERN_OFF` | Lantern: One tool with on/off state, lighting, ignition, web burning. | implemented_existing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.GUST_JAR` | Gust jar: Held suction, dust / web clearance, armor peel, released gust. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.PACCI_CANE` | Pacci cane: Flipping projectile, spring holes, Lakitu counter. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.MOLE_MITTS` | Mole mitts: Dig earth/walls, unearth buried content. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.ROCS_CAPE` | Petal cape / Roc cape: Preserve approved jumping/crossing. | implemented_existing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.PEGASUS_BOOTS` | Pegasus boots: Charge then dash and cross swamp. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.FIRE_ROD` | Fire rod: Fire projectile, ice melt, burn/light eligible targets. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.OCARINA` | Ocarina: Safe fast travel to hub/activated destinations; separate from optional summon proposal. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.GRIP_RING` | Grip ring: Climb designated walls. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.POWER_BRACELETS` | Power bracelets: Heavy lifting tiers. | implemented_existing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.FLIPPERS` | Flippers: Swim and dive. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.MAP` | Map: Preserve map item and overview/zoom exploration. | implemented_existing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.DUNGEON_MAP` | Area map: Reveal area layout without revealing unearned content indiscriminately. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.COMPASS` | Compass: Unfused fusion and objective-region guidance; current Astrolabe remains. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.BIG_KEY` | Big key: Counted/owned boss gate key. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.SMALL_KEY` | Small key: Consumed region-scoped lock currency. | implemented_existing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.BOMBBAG` | Bomb bag: Repeated upgrades to capacity type 3, only when bombs owned. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.LARGE_QUIVER` | Large quiver: Repeated capacity upgrades to type 3, only when bow owned. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.ARROW_BUTTERFLY` | Arrow butterfly: Actual arrow speed upgrade, requires Bow. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.DIG_BUTTERFLY` | Dig butterfly: Digging speed upgrade, requires Mitts. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.SWIM_BUTTERFLY` | Swim butterfly: Swimming speed upgrade, requires Flippers. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.KINSTONE_BAG` | Kinstone bag: Matching-half inventory display and fusion economy. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.BOTTLE1` | Bottle 1: One of four independent reusable bottle slots; captures/consumes contents and empty-bottle reward filtering. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.BOTTLE2` | Bottle 2: One of four independent reusable bottle slots; captures/consumes contents and empty-bottle reward filtering. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.BOTTLE3` | Bottle 3: One of four independent reusable bottle slots; captures/consumes contents and empty-bottle reward filtering. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `item.BOTTLE4` | Bottle 4: One of four independent reusable bottle slots; captures/consumes contents and empty-bottle reward filtering. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle.EMPTY` | Empty: Reusable empty bottle; capture valid contents. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle.BUTTER` | Butter: Consumable butter content. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle.MILK` | Milk: Two portions; first use becomes half-milk. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle.HALF_MILK` | Half Milk: Second milk portion empties bottle. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle.RED_POTION` | Red Potion: Potion heals and empties bottle. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle.BLUE_POTION` | Blue Potion: Potion heals and empties bottle. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle.WATER` | Water: Bottled ordinary water pours on compatible target. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle.MINERAL_WATER` | Mineral Water: Distinct mineral water source/target. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle.FAIRY` | Fairy: Captured fairy revives/heals on intended trigger. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle.PICOLYTE_RED` | Picolyte Red: Red picolyte biases corresponding drop table for duration. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle.PICOLYTE_ORANGE` | Picolyte Orange: Orange picolyte biases corresponding drop table for duration. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle.PICOLYTE_YELLOW` | Picolyte Yellow: Yellow picolyte biases corresponding drop table for duration. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle.PICOLYTE_GREEN` | Picolyte Green: Green picolyte biases corresponding drop table for duration. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle.PICOLYTE_BLUE` | Picolyte Blue: Blue picolyte biases corresponding drop table for duration. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle.PICOLYTE_WHITE` | Picolyte White: White picolyte biases corresponding drop table for duration. | missing | player_items | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle_charm.NAYRU` | Nayru's charm: Incoming damage divided by4 with minimum1. Consuming grants independent stackable run-long bit; clear only at run boundary. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle_charm.FARORE` | Farore's charm: Incoming damage divided by2, outgoing multiplied by1.5. Consuming grants independent stackable run-long bit; clear only at run boundary. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `bottle_charm.DIN` | Din's charm: Outgoing damage doubled. Consuming grants independent stackable run-long bit; clear only at run boundary. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `skill.SPIN_ATTACK` | Spin attack: Charged radial attack. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md#skills-gplayerstateskills |
| `skill.ROLL_ATTACK` | Roll attack: Attack during appropriate roll phase. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md#skills-gplayerstateskills |
| `skill.DASH_ATTACK` | Dash attack: Sword hit volume during Pegasus dash. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md#skills-gplayerstateskills |
| `skill.ROCK_BREAKER` | Rock breaker: Sword breaks rocks/pots of designated class. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md#skills-gplayerstateskills |
| `skill.SWORD_BEAM` | Sword beam: At full health, blade launches beam. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md#skills-gplayerstateskills |
| `skill.GREAT_SPIN` | Great spin: Upgraded spin; requires Spin. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md#skills-gplayerstateskills |
| `skill.DOWN_THRUST` | Down thrust: Midair downward hit; requires Cape. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md#skills-gplayerstateskills |
| `skill.PERIL_BEAM` | Peril beam: Beam at critical health. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md#skills-gplayerstateskills |
| `skill.FAST_SPIN` | Fast spin: Faster charge; requires Spin. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md#skills-gplayerstateskills |
| `skill.FAST_SPLIT` | Fast split: Faster clone creation; requires Spin / Four Sword capability. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md#skills-gplayerstateskills |
| `skill.LONG_SPIN` | Long spin: Longer spin duration; requires Spin. | missing | player_items | docs/newgame/02_PLAYER_AND_MOVEMENT.md#skills-gplayerstateskills |
| `collectible.QST_LONLON_KEY` | Qst Lonlon Key: Regional key for specific hard gate. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.QST_GRAVEYARD_KEY` | Qst Graveyard Key: Regional key for specific hard gate. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.EARTH_ELEMENT` | Earth Element: Actual goal/collectible, safely integrated with preserved Heart ending. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.FIRE_ELEMENT` | Fire Element: Collectible area goal/world token. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.WATER_ELEMENT` | Water Element: Collectible area goal/world token. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.WIND_ELEMENT` | Wind Element: Collectible area goal/world token. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.SHELLS` | Shells: Single shell grants180 frames invulnerability,4-frame blink; distinct from Shells30 charm. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.HEART_PIECE` | Heart Piece: Four pieces become one max-health container. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.HEART_CONTAINER` | Heart Container: Increase maxHP by8 and heal appropriately. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.HEART` | Heart: Heal pickup. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.FAIRY` | Fairy: Heal or capture pickup. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.RUPEE1` | Rupee ×1: Grant 1 currency/ammo, clamp to upgraded capacity and preserve denomination readability. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.RUPEE5` | Rupee ×5: Grant 5 currency/ammo, clamp to upgraded capacity and preserve denomination readability. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.RUPEE20` | Rupee ×20: Grant 20 currency/ammo, clamp to upgraded capacity and preserve denomination readability. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.RUPEE50` | Rupee ×50: Grant 50 currency/ammo, clamp to upgraded capacity and preserve denomination readability. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.RUPEE100` | Rupee ×100: Grant 100 currency/ammo, clamp to upgraded capacity and preserve denomination readability. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.RUPEE200` | Rupee ×200: Grant 200 currency/ammo, clamp to upgraded capacity and preserve denomination readability. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.BOMBS5` | Bombs ×5: Grant 5 currency/ammo, clamp to upgraded capacity and preserve denomination readability. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.BOMBS10` | Bombs ×10: Grant 10 currency/ammo, clamp to upgraded capacity and preserve denomination readability. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.BOMBS30` | Bombs ×30: Grant 30 currency/ammo, clamp to upgraded capacity and preserve denomination readability. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.ARROWS5` | Arrows ×5: Grant 5 currency/ammo, clamp to upgraded capacity and preserve denomination readability. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.ARROWS10` | Arrows ×10: Grant 10 currency/ammo, clamp to upgraded capacity and preserve denomination readability. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `collectible.ARROWS30` | Arrows ×30: Grant 30 currency/ammo, clamp to upgraded capacity and preserve denomination readability. | partial | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `food_charm.sword_knockback` | Sword Knockback: Increased outgoing sword knockback. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.walk_speed` | Walk Speed: Increased walk speed. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.steadfast` | Steadfast: No incoming knockback. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.knockback_curse` | Knockback Curse: Increased incoming knockback. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.enemy_speed_curse` | Enemy Speed Curse: Increase enemy movement speed. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.fire-rate_curse` | Fire-Rate Curse: Enemies fire more frequently. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.fire_immunity` | Fire Immunity: Suppress burning/fire status. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.ice_immunity` | Ice Immunity: Suppress frozen status. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.shock_immunity` | Shock Immunity: Suppress shock status. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.rupee_luck` | Rupee Luck: Bias rupee drops. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.kinstone_luck` | Kinstone Luck: Bias kinstone drops. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.heart_luck` | Heart Luck: Bias heart drops. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.cheap_shop` | Cheap Shop: Reduce shop prices consistently. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.rare_luck` | Rare Luck: Bias reward tier toward rare; not shell invulnerability. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.creeping_rot` | Creeping Rot: Lose1 HP every 256 frames, stop at quarter heart. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.drowned_sight` | Drowned Sight: Bounded mosaic/blur visual curse. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.ember_haze` | Ember Haze: Darken screen with readable gameplay. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.sword_edge` | Sword Edge: Add1 sword damage. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.blunt_curse` | Blunt Curse: Subtract1 sword damage, respect safe damage minimum. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.unbound_beam` | Unbound Beam: Beam at any health, requires Sword Beam. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `food_charm.fleet` | Fleet: Special golden-croissant blessing:120 frames protection on room entry. Permanent for current run; supports combined independent effect bits and clears on new run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md#charms-and-curses |
| `economy.kinstone_halves` | Matching kinstone halves: Red/blue/green families contain matching shapes; consume matching half on fusion, not arbitrary currency. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.gold_flow` | Gold flow piece: Uncommon key piece opens corresponding flow gate; only drawn while gate closed and not owned. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.gold_left` | Gold left piece: One of three distinct golden statue/gate keys, not interchangeable. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.gold_middle` | Gold middle piece: One of three distinct golden statue/gate keys, not interchangeable. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.gold_right` | Gold right piece: One of three distinct golden statue/gate keys, not interchangeable. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.fusion` | Fusion: NPC L interaction compares piece, pays it, opens corresponding door/chest/bridge for rest of run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.fuser_movement` | Travelling fusers: Fusers can appear in different regions at soft gates; hints reflect live location. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.soft_gate` | Open and fused content: Some content remains open without fusion, and fusion grind never replaces mandatory guaranteed key placement. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.tier_draw` | Tier-weighted item draw: Roll60/30/10 then uniform eligible row, respecting category, ownership, prerequisites, repeatability and capacity. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.reward_categories` | Six item categories: KEY, REWARD, WEAPON, SKILL, STAT, CHARM masks; preserve source-updated KEY eligibility for ordinary drops. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.sword_ladder` | Upgrade ladder: No downgrade/duplicate reward; Blue Sword needs Red Sword, Light Arrow needs Bow, Magic Boomerang needs Boomerang. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.capacity` | Ammo capacities: BombBag/Quiver repeated upgrades through type 3; capacity upgrades remain drawable until capped. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.stock_basic` | Permanent basic shop stock: Arrows, bombs, shields, heart pieces always-stocked, with per-run semirandom cheap prices. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.stock_roll` | Rolled shop stock: One KEY, WEAPON, SKILL, STAT slot and two REWARD slots; bought slots retire for rest of run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.price_heart` | Escalating heart-piece prices: Each purchase adds 25, cap 999; counter resets each run. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.price_tags` | Visible shop prices: Shelf/stock shows cost without mandatory shopkeeper dialogue; live gilt display remains readable. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.price_charm` | Shop discount: Cheap-shop charm applies to displayed and paid price consistently. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.heart_pieces` | Four-piece health upgrade: Track heartpieces and grant8 HP capacity for four; no loss at save/load. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.inn_50` | Comfy inn: 50 gilt heals 25% max with minimum 1 heart. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.inn_200` | Super-comfy inn: 200 gilt heals 50% max with minimum 2 hearts, COMMON reward chest. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.inn_500` | Ultra-comfy inn: 500 gilt heals full, UNCOMMON reward chest; never rare. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `economy.newrun_reset` | Economy reset: New run resets stock, sold flags, prices, fusion states, charms, temporary counters; permanent profile retained. | missing | handoff_events | docs/newgame/05_ITEMS_AND_ECONOMY.md |
| `run.authored_hub` | Authored Drain hub: Use current original sewer hub as authored base; add functions without restoring Nintendo WindTower art/layout. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `run.draft` | Three-round opening draft: Three choices each:KEY, rare REWARD / STAT, SKILL; real deterministic draw and inventory grants. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `run.safe_entry` | Loadout-safe entry: Entry/drop room must be survivable with guaranteed loadout; reroll unsafe swamp/deepwater start. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `run.roam` | Free roaming: Walk and use semantically correct doors among generated regions/rooms; map containment prevents invalid destinations. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `run.chain` | Four-step adaptive chain: Deal next EVENT/WAVE/BOSS / QUEST / ITEM only after prior complete, using current live inventory and reachability. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `run.chain_item` | Adaptive item fallback: Fallback can grant required missing item; token reach never relies exclusively on a random draw. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `run.chain_goal` | Final goal reward: Final chain reward/Element is real reachable item; additional mode coexists with approved Forest Heart victory. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `run.ocarina_home` | Home travel: Ocarina returns safely to authored hub while preserving run; current Hubcap remains. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `run.hints` | Hub wandering hints: NPCs give useful live objective/graph hints. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `run.trophy` | Catalogue and trophy case: Record actual seen/obtained discoveries and display through current retro cabinet, retaining original cabinet feature. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `run.area_architecture` | Nine-area capacity: Support independent per-area seeds/state and future nine-area design; do not invent seven unspecified regions now. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `wave.endless` | Endless escalating waves: Per-region waves continue spawning replacements until quota, then next wave with escalation. | missing | handoff_enemies | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `wave.refill` | Refill threshold: Refill when fewer than 3 own enemies stand; event pressure continues after solve until reward taken. | missing | handoff_enemies | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `wave.first_clear` | One-time clear reward: First regional clear pays exactly once; KEY eligibility not only random source of progression. | missing | handoff_enemies | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `wave.roles` | Eight role flags: CHAFF, HEAVY, RANGED, FLYER, AMBUSH, FAST, SLOW, THIEF used for encounter composition. | missing | handoff_enemies | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `wave.compositions` | Ten encounter compositions: Implement the plain mixed wave plus ten named shapes: Swarm, Menagerie, Pincer, Ambush, Crossfire, Elite Guard, Thieves, Duel, Artillery and Elite Trio. The latest source table has eleven rows; the handoff prose saying ten is stale. | missing | handoff_enemies | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `wave.themes` | Five encounter themes: FIRE, ICE, UNDEAD, BUG, AVIARY; one wave in four prefers a theme. | missing | handoff_enemies | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `wave.components` | Player-component spawns: All counted kill-quota enemies can be reached/killed with player's current items and directed terrain. | missing | handoff_enemies | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `wave.spread` | Spread and clearance: Dry farthest-point sampling with3×3 clearance and safe distance from arrivals/player. | missing | handoff_enemies | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `wave.counts` | Multi-actor costs: Madderpillar ~7 and Acro Bandit 6 consume actors as well as placement count; include projectiles/death/loot headroom. | missing | handoff_enemies | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `wave.caps` | Family live caps: Darknut 2–3, Ball and Chain 3, Madderpillar 1, Acro Bandit 2, Rupee Like 3, Like Like 3, Takkuri 3; no infinite theft grief. | missing | handoff_enemies | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `wave.refusal` | Safe encounter refusal: Insufficient tool, palette, actor, projectile or room capability causes bounded fallback, not unwinnable fight. | missing | handoff_enemies | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `event.ITEM_DROP` | Visible item prize: Actual reachable prize and persistent collection. | partial | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md#-rooms-content-sites |
| `event.MINIBOSS` | Miniboss: Elite fight only medium / large arena; actual death releases reward. | partial | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md#-rooms-content-sites |
| `event.NPC` | NPC hint/trade: A helpful character or explicit exchange, stateful completion. | partial | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md#-rooms-content-sites |
| `event.WAVES` | Fight or survive: Real quota/timer with enemy pressure, completion/reward distinct. | partial | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md#-rooms-content-sites |
| `event.POT_LOTTERY` | Pot lottery: Choose hidden prize among seeded pots; preserve lift/break semantics. | partial | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md#-rooms-content-sites |
| `event.FAIRY` | Fairy heal: Free heal/capturable fairy with valid completion. | partial | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md#-rooms-content-sites |
| `event.MEMORY` | Paired memory rooms: First room previews3 switch order, later distinct room evaluates same seeded order. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md#-rooms-content-sites |
| `event.PUZZLE` | Three switch variants: Three actual puzzle rule sets, not three skins of identical button. | partial | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md#-rooms-content-sites |
| `event.BLOCKS` | Template and maze blocks: Both solver-backed kinds and reset available. | partial | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md#-rooms-content-sites |
| `event.TORCHES` | Torch challenge: All lit simultaneously, optional darkness/timed burnout/enemy pressure; solved latch. | partial | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md#-rooms-content-sites |
| `event.CLEANUP` | Web and dust cleanup: Gust removesdust / web; lantern-alone variant has only burnable web so can complete. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md#-rooms-content-sites |
| `event.CHEST_LOTTERY` | Chest lottery: Explicitly pulled from draw in source; existing current chest rooms remain, no revival required. | retired | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md#-rooms-content-sites |
| `event.CAGE_SWITCH` | Cage-and-switch puzzle: Explicitly retired because lifting bypassed it; do not restore as requirement. | retired | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md#-rooms-content-sites |
| `portal.pair` | Portal pair: Clearing one event activates explicit portal to unreachable pocket and next chain item escape goal. | missing | handoff_events | docs/QUICKSTART_PORTAL_POCKETS.md |
| `portal.frequency` | Portal rarity: At most one pair per run, approximately one run in three. | missing | handoff_events | docs/QUICKSTART_PORTAL_POCKETS.md |
| `portal.escape` | Pocket insurance: Escape item/route guaranteed reachable; Ocarina available fallback where appropriate; death/save cannot permanently trap run. | missing | handoff_events | docs/QUICKSTART_PORTAL_POCKETS.md |
| `portal.visual` | Portal visibility and return: Activation and one-/two-way nature visible; doorway/portal uses proper transition and arrival collision. | missing | handoff_events | docs/QUICKSTART_PORTAL_POCKETS.md |
| `quest.pot` | Hidden pot prize: Prize in one seeded pot field; actual search and pickup. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `quest.hunt` | Timed hunt: 30 seconds, 7–13 enemy pack, reachable spawns, real success/failure. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `quest.scav` | Scavenger: Thief bolts OR hides in cuttable bush OR buried Mitts spot; legal predicate search with mode fallback. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `quest.stealth` | The watch: 40 second cross-watchmen challenge with sight cones and true detection/failure. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `quest.carry` | Carry pot: Unbreakable quest pot giver-to-receiver through two mixed waves; can retry after release/failure. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `quest.courier` | Courier: Deliver object between two generated regions; destination reachable with live inventory. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `quest.blocks` | Field blocks: Template/maze block puzzle in outdoor row with clear board and true reset. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `quest.stakes` | Difficulty-latched stakes: At acceptance announce and latch tier;0–3 free then rupees / hearts / charm or curse at 12. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `quest.preserve` | Current quest preservation: Keep Hermit hunt, Nun relic, Gardener torches, Stranger trade; add original quest types alongside. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `puzzle.template` | Template matching: Compare occupied cells against separate reference shape, exact no shift/rotation/reflection. | missing | world_objects | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `puzzle.maze` | Maze pushing: Clear route to chest/door in walled board. | missing | world_objects | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `puzzle.onepush` | Push legality: One cell from far side, no pull, no chain push, nothing leaves board. | missing | world_objects | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `puzzle.axis` | Axis-constrained blocks: Blue horizontal, red vertical; art/feedback agrees. | missing | world_objects | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `puzzle.goal` | Protected maze goal: Never allow block to plug mandatory maze goal. | missing | world_objects | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `puzzle.reset` | Crystal reset: Reachable crystal resets exactly board and state, allows retry. | missing | world_objects | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `puzzle.solved` | Solved lock: Solved blocks lock gold/stable and reward once. | missing | world_objects | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `puzzle.solver` | Solver-backed content: Generate by construction or select proven ROM pool, then verify actual room placement and bypass risks. | missing | world_objects | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `puzzle.reference_pool` | 1528 source puzzle records: The original 1,528 proven offline puzzles are reference data; equivalent solver-proven original boards are valid. | missing | world_objects | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `difficulty.steps` | Difficulty0–12: Persistent run difficulty step with valid0–12bounds. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `difficulty.probabilities` | Probability-based scaling: Shift tier weights and density; from step 3 every L1..Elite column positive, no hard type gates. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `difficulty.curve` | Generated tier curve: Source equivalent discrete Gaussian, Elite damping 18%, floors; no hand-edited inconsistent row sums. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `difficulty.win` | Win promotion: Win increases step bounded 12; preserve fresh-next-run behavior. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `difficulty.death` | Death demotion: Death decrements with floor 1; profile bookkeeping once per outcome. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `difficulty.density` | Separate density dial: Enemy count/cost separate from type distribution and room feasibility. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `difficulty.kinstones` | Kinstone economy pressure: Adjust fusion affordability with difficulty while keeping mandatory progression guaranteed; historical note was not tuned. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `meta.score` | Across-run score: Persistent aggregate score from actual play/outcomes with once-only accounting. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `meta.unlocks_items` | Item entitlements: Score benchmarks unlock additional optional catalogue/items, keeping starting critical progression satisfiable. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `meta.unlocks_events` | Event and quest entitlements: Expand optional event/quest vocabulary through explicit thresholds. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `meta.unlocks_regions` | Region entitlements: Explicit supported-region unlocks, never pretend future unspecified regions are implemented. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `meta.difficulty_cap` | Difficulty entitlements: Early save caps difficulty, score unlocks higher caps. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `meta.profile` | Profile continuity: Preserve cabinet discoveries, appearance settings, original music and current entitlements when migrating save/profile data. | missing | handoff_events | docs/newgame/06_CURRENT_GAME_DESIGN.md |
| `generator.seed` | Deterministic seed hierarchy: Independent run/area/room PRNG streams; tile regeneration unaffected by gameplay RNG consumption. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.mission` | Mission before space: Backward lock-and-key construction guarantees prerequisite reward before lock. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.tokens` | Unified reach tokens: Items, counted keys, switches, fusions, solved puzzles, boss flags share auditable requirement vocabulary. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.space` | Directed spatial graph: Border, door, ledge, hole, climb, one-way links explicitly directed; shared seams and collision agree. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.intraroom` | In-room token components: Mandatory gates/subregions model actual reachable tile components for loadout. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.optional` | Show locks early: Optional item-gated chests/pockets visible before tool acquisition, no forced25-room full clear. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.loop` | Loops and shortcuts: Include useful return routes and adjustable backtracking/path length. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.signature` | Signature verb: Teach area's new verb safely, test it, combine with old verbs; optionalcross-area uses. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.archetypes` | Room archetypes: Field, corridor, island, ring, cliffterrace, maze, pillarhall, arena roles with recognizable structure. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.stamps` | Semantic stamps: Feature footprints, clearance, blended shores/corners, collision separate from random decorative noise. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.connectivity` | Guard after stamps: Reject stamp invalidating required route with intended tokens. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.landings` | Reserved arrivals: Dry open2–3 tile aprons reserved before puzzles, decor, enemies. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.prizes` | Safe prizes: Dry correct-component reachable chests/rewards; no accidental water/pit/ice/swamp rewards. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.hide` | Predicate hidden placements: Query cuttable/diggable/bombable surface then ring-scan and degrade safely. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.landmark` | Landmark: Recognizable per-area setpiece gives player orientation. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.boss_arena` | Boss capability: 7×7 openness or equivalent verified fightspace and correct room capacity. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.verify_goal` | Token fixed-point proof: Goal and all mandatory keys reachable before their gates. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.verify_tiles` | Directed tile proof: Actual runtime tiles/collision permit every graph-promised route with intended capabilities. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.verify_puzzle` | In-place puzzle proof: Solve actual placed board, not only abstract template. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.verify_budget` | Resource proof: Planned actors, palettes, OAM, FX/projectiles and required art fit runtime budgets. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.retry` | Bounded retry and fallback: Finite deterministic retries then certified safe layout; no unchecked seed enters game. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.sweeps` | 100k-seed testing: Measure solvability, path length, dead ends, archetypes, budget overruns across 100,000 areas. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.twin` | Python/C equivalence: Use an independent analysis twin with identical integer arithmetic and PRNG; compare byte-for-byte against actual C output across hundreds of seeds. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.input` | Real-input traversal: Exercise every edge/verb with input and positive controls, not only RAM teleport. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.renders` | Native emulator renders: Capture actual GBA 240×160 PPU output; distinguish native emulator images from annotated mockups and asset atlases. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `generator.room_state` | Compact per-room state: Rebuild tiles deterministically on load; retain solved/reward/object state keyed byarea + room. | missing | curdled_world | docs/newgame/07_PROCGEN_DESIGN.md |
| `performance.cpu` | Cycle budget: Keep fixed-budget hot loops in ARM/IWRAM where appropriate; profile busy varied rooms with original music enabled. | missing | root | docs/newgame/08_PERFORMANCE.md |
| `performance.pools` | Bounded pools: Explicit enemies / projectiles / objects / pickups / FX capacities plus reserves; no heap churn in frame loop. | missing | root | docs/newgame/08_PERFORMANCE.md |
| `performance.collision` | Collision broad phase: Avoid all-to-all/whole-room-per-actor repeated work; preserve every collision mechanic. | missing | root | docs/newgame/08_PERFORMANCE.md |
| `performance.oam` | OAM budget: 128 hardware entries; prioritize actor / gameplay visuals, gracefully trim decorative FX. | missing | root | docs/newgame/08_PERFORMANCE.md |
| `performance.palette` | Palette discipline: 16 OBJ banks / 256 colors and BG limits; preserve enemy/NPC/item cues when combining content. | missing | root | docs/newgame/08_PERFORMANCE.md |
| `performance.stream` | Graphics residency: Respect OBJ VRAM and streaming bounds; do not undo current proven cache/transfer optimizations. | missing | root | docs/newgame/08_PERFORMANCE.md |
| `performance.audio` | Audio behavior: Keep original selected soundtrack and sound effects while measuring interrupt/stream cost. | missing | root | docs/newgame/08_PERFORMANCE.md |
| `performance.refuse` | Fast budget refusal: Preflight unsupported encounter before spawn; bounded fallback leaves run solvable. | missing | root | docs/newgame/08_PERFORMANCE.md |
| `performance.fx` | FX and loot reserve: Deaths/projectiles/pickups fit even at enemy cap; glitter current 50% reduction retained. | missing | root | docs/newgame/08_PERFORMANCE.md |
| `performance.measure` | Performance scenarios: Profile empty, multi-enemy, projectile-heavy, boss, multi-actor, event, menu, transition under current build. | missing | root | docs/newgame/08_PERFORMANCE.md |
| `art.new_only` | Append new original art: Current user forbidschangingexistingart; new tool/enemy/object/area art only. | missing | root | docs/newgame/09_ASSETS_AND_RESKIN.md |
| `art.mechanic_cues` | Mechanics readable: Art and animation communicate anticipation, activeattack, defense, damage, weakness; hitboxes separate. | missing | root | docs/newgame/09_ASSETS_AND_RESKIN.md |
| `art.frames` | Frame event cues: Per-keyframe event data drives attacks/collision/sounds consistently. | missing | root | docs/newgame/09_ASSETS_AND_RESKIN.md |
| `art.original` | Independent assets: Do not transplantNintendo sprite/map/text/musicassets; preserve selectedBloom and current art families. | missing | root | docs/newgame/09_ASSETS_AND_RESKIN.md |
| `art.coverage` | Draw every object: Every supported interactable/pickup/torch has visibleart in every admitted tileset, no invisible orb fallback. | missing | root | docs/newgame/09_ASSETS_AND_RESKIN.md |
| `art.style` | Unified design record: Apply existing GBA-first pixel/style guides, limited palettes, clean silhouettes, ground blending and glitter / filth contrast. | missing | root | docs/newgame/09_ASSETS_AND_RESKIN.md |
| `current_request.area` | The Curdled Cream: New generated 5×5 area with distinct palette, cliff / ledge / climb walls / caves; evil retains glowing purple. | missing | curdled_world | Current user request (Curdled Cream and bomb redesign) |
| `current_request.climb` | Climbing maze: Upward climb, lateral ledge walk, downward drops including 2–4 full screens; some walls deliberately unclimbable. | missing | curdled_world | Current user request (Curdled Cream and bomb redesign) |
| `current_request.caves` | Cave links: Caves connect nonadjacent ledges/rooms with safe paired destinations and directed reach accounting. | missing | curdled_world | Current user request (Curdled Cream and bomb redesign) |
| `current_request.deadends` | Meaningful dead ends: Every generated dead end contains quest / enemy / item / NPC / other content. | missing | curdled_world | Current user request (Curdled Cream and bomb redesign) |
| `current_request.boss` | Peak boss: Boss atop randomly selected top-row peak; guaranteed solvable route and fight arena. | missing | curdled_world | Current user request (Curdled Cream and bomb redesign) |
| `current_request.blight` | Depth progression: Art/content grow increasingly corrupted toward peak boss without changingexisting Forest art. | missing | curdled_world | Current user request (Curdled Cream and bomb redesign) |
| `current_request.tools` | Additional gates: Cape holes, webs, thorns and other compatible gates add maze complexity with required tools available before lock. | missing | curdled_world | Current user request (Curdled Cream and bomb redesign) |
| `current_request.proof` | Solvability proof: Verify the directed climb/drop/cave graph and actual room tiles across many seeds, using bounded retries and a certified fallback. | missing | curdled_world | Current user request (Curdled Cream and bomb redesign) |
| `current_request.bomb_charge` | Charge trajectory: While held charge caps at 1 second; tap drops below player, 0.5 second = 1.5 tiles, 1 second = 2 tiles; release throws. | missing | player_items | Current user request (Curdled Cream and bomb redesign) |
| `current_request.bomb_impact` | Impact explosion: Ordinary bombs explode on impact with ground; projectile arc, obstacle collision, bombable features and damage are coherent. | missing | player_items | Current user request (Curdled Cream and bomb redesign) |
| `reference.struct` | Struct: Entity record sizes, PlayerState offsets, MapLayer size and original memory addresses are oracle details, not independent-engine requirements. | reference_only | audit | docs/newgame/00_README.md |
| `reference.formats` | Formats: Original TMC MapLayer, LZ77, entity property lists and Transition binary layout are not required formats. | reference_only | audit | docs/newgame/00_README.md |
| `reference.toolchain` | Toolchain: Matching agbcc/C89 decompilation and original base-ROM checksums are not required for the standalone engine. | reference_only | audit | docs/newgame/00_README.md |
| `reference.scripts` | Scripts: Original script bytecode and Nintendo message banks are reference implementation details. | reference_only | audit | docs/newgame/00_README.md |
| `reference.audio` | Audio: Original m4a/MusicPlayer2000 format is not required; preserve selected original-game music and effects. | reference_only | audit | docs/newgame/00_README.md |
| `reference.save` | Save: Original gSave flag-bank addresses and the old 707-flag ceiling do not constrain new save structures. | reference_only | audit | docs/newgame/00_README.md |
| `reference.ceiling` | Ceiling: The TMC 16-slot dynamic graphics limit is an observed old-engine wall, not a new-engine hardware limit. | reference_only | audit | docs/newgame/00_README.md |
| `reference.grid` | Grid: Original 64×64-tile and multi-screen room formats are references. The current area request uses a 5×5 grid of screen rooms. | reference_only | audit | docs/newgame/00_README.md |
| `reference.rawforms` | Rawforms: The 213 raw enemy forms include children and scripted boss setup; they are not 213 independent ordinary encounters. | reference_only | audit | docs/newgame/00_README.md |
| `reference.puzzlecount` | Puzzlecount: The 1,528 original solved puzzle records are provenance; equivalent proven original boards are permitted. | reference_only | audit | docs/newgame/00_README.md |
| `reference.animations` | Animations: The 158 player animations are behavior/timing references, not permission to replace current Bloom artwork. | reference_only | audit | docs/newgame/00_README.md |
| `reference.collision_matrix` | Collision Matrix: The 5,220 nonempty original collision-matrix cells are a damage/counter oracle, not 5,220 separately requested features. | reference_only | audit | docs/newgame/00_README.md |
| `reference.futureareas` | Futureareas: The nine-area architecture does not supply names, art or mechanics for seven future unspecified areas. | reference_only | audit | docs/newgame/00_README.md |
| `reference.wallet` | Wallet: Wallet and Big Wallet are explicitly excluded by the referenced item-tier design. | reference_only | audit | docs/QUICKSTART_ITEM_TIERS.md#1-categories-and-tiers |
| `reference.chestlottery` | Chestlottery: Chest lottery and the old cage-and-switch puzzle are explicitly retired. | reference_only | audit | docs/newgame/00_README.md |
| `reference.oldbomb` | Oldbomb: The old placed-bomb 150-frame fuse is superseded by the current charge-and-throw impact request. | reference_only | audit | docs/newgame/00_README.md |
| `reference.oldsword` | Oldsword: The old 15-frame sword reference is superseded by the approved 18-update step-and-cut animation. | reference_only | audit | docs/newgame/00_README.md |
| `reference.permission` | Permission: The historical standing-rule clarification is not a permission block; the current user explicitly authorizes additive implementation. | reference_only | audit | docs/newgame/00_README.md |
| `proposal.elemental` | elemental: Elemental freeze/burn/shock player weapons are feasibility research, not completed original QUICKSTART features. Fire/ice enemy attacks and player status responses remain required. | reference_only | audit | docs/QUICKSTART_ITEM_TIERS.md#4-can-links-weapons-apply-freeze--burn--shock-to-enemies |
| `proposal.summon` | summon: An allied cucco-style swarm is research. A new original ally implementation would need a separate trigger from Ocarina fast travel. | reference_only | audit | docs/QUICKSTART_ITEM_TIERS.md#10-can-the-cucco-swarm-become-a-summon |
| `proposal.firepacci` | firepacci: Fire Rod/Pacci mutual exclusion only solved the original 12-cell menu limit. A new expanded menu may support both. | reference_only | audit | docs/QUICKSTART_ITEM_TIERS.md#8-the-fire-rod-as-a-drop---decided-uncommon-weapontool |
| `enemy.BEETLE.0` | BEETLE form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | partial_family_adaptation | handoff_enemies | src/game.c:9424 |
| `enemy.KEESE.0` | KEESE form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, FLYER, FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | partial_family_adaptation | handoff_enemies | src/game.c:9425 |
| `enemy.SMALL_PESTO.0` | SMALL_PESTO form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, FLYER, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9426 |
| `enemy.TEKTITE.0` | TEKTITE form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9427 |
| `enemy.CROW.0` | CROW form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, FLYER, FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9428 |
| `enemy.MINI_SLIME.0` | MINI_SLIME form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9429 |
| `enemy.OCTOROK.0` | OCTOROK form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, RANGED, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | partial_family_adaptation | handoff_enemies | src/game.c:9435 |
| `enemy.PEAHAT.0` | PEAHAT form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, FLYER. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9436 |
| `enemy.CHUCHU.0` | CHUCHU form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9437 |
| `enemy.ROPE.0` | ROPE form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, AMBUSH. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | partial_family_adaptation | handoff_enemies | src/game.c:9438 |
| `enemy.OCTOROK2.0` | OCTOROK2 form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, RANGED, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9453 |
| `enemy.OCTOROK.1` | OCTOROK form 1: Add original-art behavior equivalent to curated source form. Roles: RANGED, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | partial_family_adaptation | handoff_enemies | src/game.c:9454 |
| `enemy.SLIME.0` | SLIME form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | partial_family_adaptation | handoff_enemies | src/game.c:9455 |
| `enemy.STALFOS.0` | STALFOS form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9456 |
| `enemy.STALFOS.1` | STALFOS form 1: Add original-art behavior equivalent to curated source form. Roles: CHAFF, FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9457 |
| `enemy.KEATON.0` | KEATON form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9458 |
| `enemy.HELMASAUR.0` | HELMASAUR form 0: Add original-art behavior equivalent to curated source form. Roles: FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | partial_family_adaptation | handoff_enemies | src/game.c:9459 |
| `enemy.PESTO.0` | PESTO form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, FLYER, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9460 |
| `enemy.CHUCHU.2` | CHUCHU form 2: Add original-art behavior equivalent to curated source form. Roles: CHAFF, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9461 |
| `enemy.BOBOMB.0` | BOBOMB form 0: Add original-art behavior equivalent to curated source form. Roles: SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9462 |
| `enemy.BOMBAROSSA.0` | BOMBAROSSA form 0: Add original-art behavior equivalent to curated source form. Roles: RANGED, FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9463 |
| `enemy.LEEVER.0` | LEEVER form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, AMBUSH. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | partial_family_adaptation | handoff_enemies | src/game.c:9464 |
| `enemy.MULLDOZER.0` | MULLDOZER form 0: Add original-art behavior equivalent to curated source form. Roles: SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9465 |
| `enemy.TEKTITE.1` | TEKTITE form 1: Add original-art behavior equivalent to curated source form. Roles: FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9466 |
| `enemy.LEEVER.1` | LEEVER form 1: Add original-art behavior equivalent to curated source form. Roles: AMBUSH. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | partial_family_adaptation | handoff_enemies | src/game.c:9467 |
| `enemy.MOLDORM.0` | MOLDORM form 0: Add original-art behavior equivalent to curated source form. Roles: FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9476 |
| `enemy.GHINI.0` | GHINI form 0: Add original-art behavior equivalent to curated source form. Roles: FLYER, FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9477 |
| `enemy.ARMOS.0` | ARMOS form 0: Add original-art behavior equivalent to curated source form. Roles: AMBUSH, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9478 |
| `enemy.EYEGORE.0` | EYEGORE form 0: Add original-art behavior equivalent to curated source form. Roles: RANGED, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9479 |
| `enemy.MULLDOZER.1` | MULLDOZER form 1: Add original-art behavior equivalent to curated source form. Roles: SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9480 |
| `enemy.PESTO.1` | PESTO form 1: Add original-art behavior equivalent to curated source form. Roles: CHAFF, FLYER, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9481 |
| `enemy.CHUCHU.1` | CHUCHU form 1: Add original-art behavior equivalent to curated source form. Roles: CHAFF, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9482 |
| `enemy.ROCK_CHUCHU.0` | ROCK_CHUCHU form 0: Add original-art behavior equivalent to curated source form. Roles: SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9483 |
| `enemy.SPINY_CHUCHU.0` | SPINY_CHUCHU form 0: Add original-art behavior equivalent to curated source form. Roles: SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9484 |
| `enemy.SPIKED_BEETLE.0` | SPIKED_BEETLE form 0: Add original-art behavior equivalent to curated source form. Roles: AMBUSH, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9485 |
| `enemy.PUFFSTOOL.0` | PUFFSTOOL form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9486 |
| `enemy.FIREBALL_GUY.0` | FIREBALL_GUY form 0: Add original-art behavior equivalent to curated source form. Roles: RANGED. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9487 |
| `enemy.MINI_FIREBALL_GUY.0` | MINI_FIREBALL_GUY form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF, RANGED. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9488 |
| `enemy.BOMB_PEAHAT.0` | BOMB_PEAHAT form 0: Add original-art behavior equivalent to curated source form. Roles: FLYER. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9489 |
| `enemy.CLOUD_PIRANHA.0` | CLOUD_PIRANHA form 0: Add original-art behavior equivalent to curated source form. Roles: AMBUSH. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9490 |
| `enemy.SPINY_BEETLE.0` | SPINY_BEETLE form 0: Add original-art behavior equivalent to curated source form. Roles: FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9491 |
| `enemy.ENEMY_50.0` | ENEMY_50 form 0: Add original-art behavior equivalent to curated source form. Roles: FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9492 |
| `enemy.LIKE_LIKE.0` | LIKE_LIKE form 0: Add original-art behavior equivalent to curated source form. Roles: HEAVY, SLOW, THIEF. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9510 |
| `enemy.RUPEE_LIKE.0` | RUPEE_LIKE form 0: Add original-art behavior equivalent to curated source form. Roles: HEAVY, THIEF. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9511 |
| `enemy.RUPEE_LIKE.2` | RUPEE_LIKE form 2: Add original-art behavior equivalent to curated source form. Roles: HEAVY, THIEF. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9512 |
| `enemy.RUPEE_LIKE.1` | RUPEE_LIKE form 1: Add original-art behavior equivalent to curated source form. Roles: HEAVY, THIEF. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9513 |
| `enemy.TAKKURI.0` | TAKKURI form 0: Add original-art behavior equivalent to curated source form. Roles: FAST, FLYER, THIEF. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9514 |
| `enemy.GOBDO.0` | GOBDO form 0: Add original-art behavior equivalent to curated source form. Roles: HEAVY, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9515 |
| `enemy.SCISSORS_BEETLE.0` | SCISSORS_BEETLE form 0: Add original-art behavior equivalent to curated source form. Roles: HEAVY. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9516 |
| `enemy.MOLDWORM.0` | MOLDWORM form 0: Add original-art behavior equivalent to curated source form. Roles: HEAVY. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9517 |
| `enemy.ENEMY_4D.0` | ENEMY_4D form 0: Add original-art behavior equivalent to curated source form. Roles: HEAVY. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9518 |
| `enemy.BOW_MOBLIN.0` | BOW_MOBLIN form 0: Add original-art behavior equivalent to curated source form. Roles: RANGED, FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9519 |
| `enemy.SPEAR_MOBLIN.0` | SPEAR_MOBLIN form 0: Add original-art behavior equivalent to curated source form. Roles: FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9520 |
| `enemy.ACRO_BANDIT.0` | ACRO_BANDIT form 0: Add original-art behavior equivalent to curated source form. Roles: CHAFF. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9521 |
| `enemy.WIZZROBE_FIRE.0` | WIZZROBE_FIRE form 0: Add original-art behavior equivalent to curated source form. Roles: RANGED, FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9533 |
| `enemy.WIZZROBE_ICE.0` | WIZZROBE_ICE form 0: Add original-art behavior equivalent to curated source form. Roles: RANGED, FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9534 |
| `enemy.WIZZROBE_WIND.0` | WIZZROBE_WIND form 0: Add original-art behavior equivalent to curated source form. Roles: RANGED, FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9535 |
| `enemy.TEKTITE_GOLDEN.0` | TEKTITE_GOLDEN form 0: Add original-art behavior equivalent to curated source form. Roles: HEAVY, FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9536 |
| `enemy.OCTOROK_GOLDEN.0` | OCTOROK_GOLDEN form 0: Add original-art behavior equivalent to curated source form. Roles: HEAVY, RANGED, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9537 |
| `enemy.ROPE_GOLDEN.0` | ROPE_GOLDEN form 0: Add original-art behavior equivalent to curated source form. Roles: HEAVY, AMBUSH. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9538 |
| `enemy.ROLLOBITE.0` | ROLLOBITE form 0: Add original-art behavior equivalent to curated source form. Roles: FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9539 |
| `enemy.WISP.0` | WISP form 0: Add original-art behavior equivalent to curated source form. Roles: FLYER. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9540 |
| `enemy.WISP.1` | WISP form 1: Add original-art behavior equivalent to curated source form. Roles: FLYER, FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9541 |
| `enemy.SPARK.0` | SPARK form 0: Add original-art behavior equivalent to curated source form. Roles: FAST. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9545 |
| `enemy.LAKITU.0` | LAKITU form 0: Add original-art behavior equivalent to curated source form. Roles: RANGED, FLYER. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9546 |
| `enemy.DARK_NUT.0` | DARK_NUT form 0: Add original-art behavior equivalent to curated source form. Roles: HEAVY, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | partial_family_adaptation | handoff_enemies | src/game.c:9564 |
| `enemy.DARK_NUT.1` | DARK_NUT form 1: Add original-art behavior equivalent to curated source form. Roles: HEAVY, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | partial_family_adaptation | handoff_enemies | src/game.c:9565 |
| `enemy.DARK_NUT.2` | DARK_NUT form 2: Add original-art behavior equivalent to curated source form. Roles: HEAVY, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | partial_family_adaptation | handoff_enemies | src/game.c:9566 |
| `enemy.DARK_NUT.3` | DARK_NUT form 3: Add original-art behavior equivalent to curated source form. Roles: HEAVY, SLOW. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | partial_family_adaptation | handoff_enemies | src/game.c:9567 |
| `enemy.BALL_CHAIN_SOLIDER.0` | BALL_CHAIN_SOLIDER form 0: Add original-art behavior equivalent to curated source form. Roles: HEAVY. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9568 |
| `enemy.MADDERPILLAR.0` | MADDERPILLAR form 0: Add original-art behavior equivalent to curated source form. Roles: HEAVY. Initial stats and collision evidence are in enemy_inventory.curated; validate source AI, not only stats. | missing | handoff_enemies | src/game.c:9577 |
| `boss.CHUCHU_GREEN` | CHUCHU_GREEN: Green jelly boss:armoredpeel, exposed core, multiple cycles; Gust is best but other documented weapons peel; prevent jar-less softlock. | missing | handoff_enemies | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#enemies |
| `boss.CHUCHU_ELECTRIC` | CHUCHU_ELECTRIC: Electric jelly boss form with stateful charge / armor / exposure and valid arena. | missing | handoff_enemies | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#enemies |
| `boss.BIG_OCTOROK` | BIG_OCTOROK: Big Octorok multi-phase boss with proper parts / reflect / fire / ice mechanics and valid arena, rather than a bare generic enemy. | missing | handoff_enemies | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#enemies |
| `boss.HEART` | HEART: Preserve existing selected broken purple Heart boss and current ending. | implemented_existing | handoff_enemies | docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#enemies |
## Exact item inventories

The JSON retains every row instead of flattening items with multiple categories/tiers. These source values determine eligibility; an item name or icon alone is not content.

| Table | Count |
| --- | ---: |
| Original item enum records, including excluded/sentinel records | 122 |
| `sQuickStartTiers` rows | 77 |
| Run-long food effects | 21 |
| Bottled stackable run charms | 3 |

| Bit | Source carrier | Run-long effect |
| ---: | --- | --- |
| 0 | `BRIOCHE` | sword knockback: Increased outgoing sword knockback. |
| 1 | `CROISSANT` | walk speed: Increased walk speed. |
| 2 | `CAKE` | steadfast: No incoming knockback. |
| 3 | `PIE` | knockback curse: Increased incoming knockback. |
| 4 | `QST_DOGFOOD` | enemy speed curse: Increase enemy movement speed. |
| 5 | `QST_MUSHROOM` | fire-rate curse: Enemies fire more frequently. |
| 6 | `QST_BOOK1` | fire immunity: Suppress burning/fire status. |
| 7 | `QST_BOOK2` | ice immunity: Suppress frozen status. |
| 8 | `QST_BOOK3` | shock immunity: Suppress shock status. |
| 9 | `QST_TINGLE_TROPHY` | rupee luck: Bias rupee drops. |
| 10 | `JABBERNUT` | kinstone luck: Bias kinstone drops. |
| 11 | `QST_CARLOV_MEDAL` | heart luck: Bias heart drops. |
| 12 | `QST_BROKEN_SWORD` | cheap shop: Reduce shop prices consistently. |
| 13 | `SHELLS30` | rare luck: Bias reward tier toward rare; not shell invulnerability. |
| 14 | `ORB_GREEN` | creeping rot: Lose1 HP every 256 frames, stop at quarter heart. |
| 15 | `ORB_BLUE` | drowned sight: Bounded mosaic/blur visual curse. |
| 16 | `ORB_RED` | ember haze: Darken screen with readable gameplay. |
| 17 | `QST_SWORD` | sword edge: Add1 sword damage. |
| 18 | `UNUSED_SWORD` | blunt curse: Subtract1 sword damage, respect safe damage minimum. |
| 19 | `GREEN_SWORD` | unbound beam: Beam at any health, requires Sword Beam. |
| 20 | `FLEET` | fleet: Special golden-croissant blessing:120 frames protection on room entry. |

## Enemy admission and behavior

The [existing source audit](../../bartgame/docs/enemy-prototypes/SOURCE_AUDIT.md) and [catalogue](../../bartgame/docs/enemy-prototypes/source_catalogue.json) preserve original stats and initial collision cells. That catalogue snapshot predates this restoration baseline; hashes in the JSON distinguish provenance. Required roster counts are L1=10, L2=15, L3=17, L4=12, L5=11 and Elite=6. Each curated form has its own ledger ID and a full source entry in the JSON. Of 71 curated picks, 69 have distinct raw CSV rows; Rupee Like forms 1 and 2 reuse the form-0 initial definition.

New original art must depict the attack telegraph, active phase, recovery and weakness. Generic AI with different HP does not restore enemy behavior. Spark needs Boomerang and Lakitu needs Pacci, so admission checks must ensure tool availability or an optional encounter with a safe exit. Bob-omb's 255 HP is a lifecycle sentinel, not 128 sword hits. Armored front/rear, burrowing, hopping, electric/freeze/fire, capture/theft, multi-actor tails, exposure and reflection need actual state paths.

Unsafe raw forms such as boss children, Gyorg child, Sluggula, Wall Master and ENEMY_64 need setup if the independent game admits them. They remain reference inventory rather than claimed finished ordinary encounters. Documented green/electric ChuChu and Big Octorok need genuine fight setup and arena validation.

## Completion gate

A feature needs every applicable path: obtainable/enterable through play, actual mechanic, visible art, correct damage/weakness/collision, success/failure/reset/reward, save/reload, new-run reset and resource admission. A registry, flavor text, enum, static stat or menu entry does not meet this gate.

Validate seed proofs against the actual C generator. Check real room tiles and directed links, exercise input transitions, capture native 240×160 mGBA output, measure busy rooms with original music, and preserve existing art checksums. The baseline audit itself performed no build or runtime tests. The current qualification below records the subsequent implementation and measured tests.

## Current implementation and final qualification

Final source: `0b9344d781e65e304d245bd9ae4aecdbc7056837`.
Final ROM SHA-256: `b348cf4d628aee1abb9b71d8885a9f04094332c5252490ff2dd8f8e7cd0bf1b8`.
The baseline columns above remain historical. Each machine ledger row has a
separate current `restoration_status`, executable source references and scoped
`qualification` fields. A catalogue image, connected mechanic, host proof and
native input test remain different evidence.

Current additions include the independent 25-room Curdled Cream directed
climbing/drop/cave puzzle, all 71 curated enemy forms plus scripted boss
adaptations, actual handoff tools, skills, bottles, forms and surfaces, seven
quests, the optional four-seal contract, all four Elements, economy, charms,
fusions, meta persistence and 1,528 certified push boards. The authored Drain,
approved Forest progression, ordinary sword feel, original music and existing
artwork remain. The cabinet lists 139 meaningful items and 84 enemies while
retaining 146 stable raw item identifiers.

| Current qualification | Rows |
| --- | ---: |
| `baseline_preserved_qualified` | 23 |
| `native_sample_qualified` | 181 |
| `code_connected_pending_native` | 247 |
| `host_logic_qualified_pending_native` | 10 |
| `retired_exempt` | 2 |
| `host_geometry_qualified_pending_native` | 9 |
| `host_equivalence_qualified` | 1 |
| `reference_exempt` | 21 |


Exact final-ROM evidence:

- **32/32 mobility/profile controls**: cart riding and stopping, B/L equipment
  ownership, steerable parachute, both bridge planes, dry deck with and without
  Flippers, bow use above confirmed underlying water, actual lower-water dive
  and unsupported drowning, red-fusion bridge/cache, genuine hazard death,
  save and cold Continue of progress, discoveries and preferences.
- **227/227 catalogue checks**: every visible item and enemy identifier maps to
  the exact native preview pixels/palette; actor and terrain freeze, then
  return to the live Drain. Complete knowledge is an explicit private UI
  fixture, rather than an earned memory claim. Sentinel defenses and actual
  tail/aggregate boss statistics have truthful labels.
- **59/59 full-route and 28/28 each long-drop controls**: all three actual trial
  rewards, Bomb/Lamp/Cape+Pacci gates, cave transfer and a real peak win;
  separate three- and four-row falls show intervening generated terrain.
  Native art review passes 65 checks. These tests disclose hero navigation and
  facing fixtures; they do not assign rewards, enemy HP/state, completion,
  gates, terrain or video output.
- **267/267 enemy action checks and 74 appended roster samples**: each sampled
  entry actually runs 180 updates, totaling 13,320 updates and physical frames.
  Targeted tool, capture, armor, lifecycle and stress tests have narrower
  per-feature scopes. Independent native asset decoding checks 2,540 source
  frames. This qualifies observed current-port behavior and rendering,
  rather than complete original-AI equivalence or every possible counter.
- **95 item/object/form/mechanism checks** and **27 gear-interface checks**:
  real tools and reachable course mechanisms, possession navigation/equipping,
  room atlas/zoom, rapid input, native icons and return to unchanged terrain.
  Loadout, navigation and unrelated-actor isolation fixtures are disclosed.
- **Event/service suites** pass 14 service, 28 quest, 22 adaptive-contract and
  19 meta power-cycle checks. They exercise the draft, 50-gilt inn, source boards,
  memory, all seven quest success paths, a real four-seal contract and profile
  continuity. Per-row entries preserve untested failure paths, alternate beds,
  fusion details and unlock thresholds as code-connected scopes.
- **Original-game regression**: 21 Forest, 53 victory/save, 69 music and eight
  integration-guard checks pass. Original-art preservation passes 2,232 checks
  across all 40 original sheets and existing tile/palette/identifier contracts.
- **Resources**: 146 scenarios, 127 checks and 26,160 video frames, including
  75 natural Forest rooms, stress rosters, interiors, actions and menus;
  29 native boundary checks also pass. This is representative workload
  coverage, rather than every possible new-area actor combination.

Host qualification includes 100,000 actual-C capability graphs and 100,000
complete physical roomsets. The latter covers 2.5 million rooms, 9.9 million
route triggers and target landings each, 22,899,209 spawn checks, 3,376,541
content fronts and 100,000 dry reachable hub-return fronts, with zero failures.
The graph occupies 1,392 bytes and has bounded attempts plus a checked fixed
certificate. Python independently solves 1,000 C graphs with all eight
inherited capability masks.

The independent Python generator twin also matches **every byte** of the
actual C record for **1,000 generated seeds and six explicit fixed-certificate
controls**: **1,400,352 bytes** including padding and unused edge slots. It
implements explicit unsigned 32-bit arithmetic and PRNG behavior, ordered
construction and rejection, and manual serialization. Expected generation
never calls C or parses C output/source. The fixed certificate is independently
reconstructed from its original shape seed with content seed zero. Boundary
and full-width seeds are covered; no natural fallback occurs in these cases,
so explicit certificate controls are separately identified. This closes
`generator.twin`; it is an engineering equivalence result, rather than an
exhaustive 32-bit seed or native gameplay proof.

Actual-C host suites also pass 1,951 production and 1,868 LAB journal checks
with 97,600 protected-byte checks; 1,479 extension-v2 checks with 48,640 protected
bytes; 2,184 common-token/hidden-placement checks; 1,511 transport controls;
and **16,067 fine-mask collision checks**. The extension preserves the original
base save layouts and uses independent versioned records. Reports retain
source/build hashes and explicit adapters/fixtures.

No named runtime implementation gap remains in the current ledger. Many rows
remain `code_connected_pending_native`: their implementation and reachable
caller are present, while the entire per-feature acceptance matrix has not
been independently exercised in mGBA. Native evidence is representative; it
does not claim an unassisted run, every keyframe on every background, every
possible encounter combination or 100,000 native playthroughs.

Reference distinctions remain explicit: raw child/cinematic forms and old ROM
formats are provenance, retired chest lottery/cage-switch are not reintroduced,
research proposals are not silently made requirements, and seven unnamed future
regions are not invented as completed content. Forest and Cream state remain
independent; the nine-region architecture provides future capacity.

[Module implementation notes](../../bartgame/docs/handoff-restoration/JOURNAL.md)
and each machine row retain precise current sources, source exceptions and
separate host/native evidence. Verification artifacts are copied into the
published review bundle; workspace report paths identify their original runs.
