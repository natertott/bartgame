# Additive handoff events and the Drain annex

The existing Drain, Forest, character sprites, fixed three Forest trials,
ordinary starting equipment, and boss win flow remain in place. The new
optional annex uses `AREA_HANDOFF = 4`; source event IDs are appended rather
than repurposing existing mystery-room IDs. The Drain's new annex entrance
leads to eight working service desks. A challenge desk reaches every new
site. Cream's three required tool trials use separate saved site IDs
160–162, so optional annex completions cannot complete those trials.

## Sources and adaptations

Read alongside the repository's original migration documents:

- `../../../docs/newgame/05_ITEMS_AND_ECONOMY.md`: item groups, tiers, foods, charms,
  source shops, opening draft, hub and reward rules.
- `../../../docs/newgame/06_CURRENT_GAME_DESIGN.md`: four-step adaptive chain, quests,
  current event kinds, difficulty and paused meta vision.
- `../../../docs/newgame/07_PROCGEN_DESIGN.md`: solvability, prerequisites, progress
  before gates, bounded content and replayable seeds.
- Original root `src/game.c`: `sQuickStartTiers`, `sQuickStartArchetypes`,
  `sQuickStartDifficultyTiers`, food flags and unlock registry. Later live
  source corrections take precedence over stale comments in the handoff.
- `../../../docs/QUICKSTART_HUB.md` §3.2: the three bed prices and rewards.

The independent game adapts the old overworld chain into an **optional
annex contract**. It has four reachable steps: an event, waves or a quest,
a guaranteed key-item reward in a pocket, then a boss. Four Elements mark its seals, and completion grants the Fourfold Sword. The Forest's current
three-trial progression and Heart victory remain intact. Completing the
optional contract adds a reward and score; it does not replace the real win.

The old unlock master switch was disabled by the user's earlier request
that all content remain eligible. Ordinary mode therefore keeps all annex
content and all twelve difficulty steps available. The Trophy desk offers
a separately labelled opt-in entitlement challenge. Its added item-tier,
region and difficulty caps implement the previously unbuilt meta vision;
they are an adaptation, not a claim that the old game shipped those caps.
The retired chest lottery remains retired.

## Playable services

| Desk | Actual behavior |
| --- | --- |
| Three Gifts | Three rounds, three distinct eligible choices each: key, reward/stat, skill. Adds gifts to the ordinary starting equipment. One draft per run. |
| Three Beds | 50 gilt restores 25% max health (minimum 8 HP); 200 restores 50% (minimum 16 HP) plus a common chest; 500 fully heals plus an uncommon chest. A 150-tick fade/sleep/rest sequence performs the healing; the promised chest persists beside the bed until claimed. Never awards a rare bed chest. |
| Exchange | Six rolled wares plus predictable heart-piece, seed and arrow supplies. Actual gilt deduction, prerequisite checks and sold flags. Repeated heart pieces cost 25 more each, capped at 999. Cheap-shop charm caps each price at 50. |
| Fusions | Three colors × three visibly different cut shapes. Wandering fusers also appear on clear reachable floor near Forest/Cream arrivals. Green opens a cache; blue opens a pocket cave; red opens the optional physical bridge in the traversal course. Matching halves are consumed. The first green fusion grants the Kinstone Bag, expanding matching-half capacity from 9 to 99 per color/cut. |
| Golden seals | Four distinct golden pieces: Flow, Left, Middle, Right. The Flow half opens its physical seal; all three statue halves open their seal. Both are fused from the Golden Fusion site. No generic locked door is converted into a warp. |
| Trophy | Score, wins, deaths, rank, optional entitlement mode and difficulty selection. |
| Hint | Concrete clues about paths, unmarked lantern routes and tool silhouettes. |
| Challenges | Every added event, all seven quests, endless arena, boss trial, traversal course and object course. Missing-tool cleanup/censer entries explain the prerequisite before entry. |
| Four Seals | Inspect/travel/retire a four-step optional contract. Dedicated site instances 128–131 keep optional exploration from consuming a later contract objective. Each new seal rearms only its own instance. The key-item step guarantees the displayed item instead of relying on luck. Its four completed seals award Earth/Fire/Water/Wind Elements in order. |

Colored fusions are optional soft gates. The challenge desk also provides
an ungated way to inspect the underlying events in ordinary mode. Required
Forest and Cream gates keep their own separate progression state.

## Event sites

| Site | Interaction and completion |
| --- | --- |
| Item cache | Interact with the cache; receive an eligible source-tier reward. |
| Champion | Defeat a real appended Darknut. Failed spawn allocation cannot award an empty-room win. |
| Stranger | Ten gilt buys a piece of heart, once. |
| Waves | Three quota waves with role casts; complete, then collect the chest. Refill while fewer than three live until its prize is claimed. |
| Hidden pot | Six actual liftable/breakable pots; one seeded pot reveals the prize. |
| Fairy well | Two real fairy pickups and an interactable healing well. |
| Memory pair | Learn and Recall rooms share a saved seeded plate sequence. Learn shows it repeatedly at predictable 60-tick beats; Recall requires entering plates in that order. An error resets input, never seals the exit. |
| Floor plates | Seeded all-plates, neighboring-toggle, or ordered timed-sequence variants. |
| Block template | Match the adjacent 5×5 reference using three one-cell push blocks. |
| Block maze | Shift axis-marked blocks to open the route to the far seal. |
| Censers | Three visible fixtures respond to actual lantern/flame hit boxes. |
| Cleanup | Fire removes silk; Gust removes dust. Lantern alone gets silk only; Gust alone gets dust only. Neither tool means the desk explains the prerequisite. |
| Survival | Twenty-second live encounter, then a chest. |
| Endless arena | Continues quota waves until the player leaves, including after its first chest is claimed. Wave five grants the special Fleet food. It never continues behind a game victory overlay. |
| Portal/pocket | A visible arch requests the new pocket interior. An escape tool is supplied **before entry** when absent. Its south return always works. |
| Boss trial | Real Giant ChuChu or Big Octorok with the appended enemy agent's ordinary-weapon fallback. Broad 28×19 dry fighting space. |
| Golden fusion | Two physical seals and an interior prize; the distinct golden halves open them. |
| Traversal course | Minecart, rail, controllable parachute descent, actual upper/lower bridge collision and a red-fusion island crossing. Implemented by `handoff_mobility.c`. |
| Object workshop | Four directly selectable mechanism courses (sites 28–31) dispatch through `handoff_objects.c`, including furniture/statues/graves, multiple doors and levers, platforms, hazards and traversal objects. |

Every ordinary site can be exited to the south. Existing quest rooms are
not repopulated by these annex wave routines. A completed annex challenge
stops spawning after its chest is claimed; only the explicitly endless
arena continues.

## Seven quests and announced stakes

Pot: find one of six pots. Hunt: defeat a seeded quota of 7–13 enemies within
30 seconds, with bounded live refills. Scavenger: catch a moving glint, cut
its leaf pile, or use the actual Mitts dig rectangle on soft earth; the
buried mode is not selected without Mitts. Stealth: pass rotating watchers'
visible gaze markers and physical cover to the far seal within 40 seconds.
Carry: Bloom really lifts and carries a pot, can throw/drop it, must recover
it and clear two ambushes before delivering it. The marked cargo remains
recoverable when thrown into an unsafe spot. Courier: carry a parcel to a
reachable wandering recipient at the Forest entry; a Compass marks the
recipient. Blocks: solve one of the certified template/axis mazes.

The quest latches its difficulty and announces its entire failure stake
before its timer starts. Changing difficulty afterwards cannot change that
stake. Leaving an active non-courier quest or dying forfeits it; courier
travel is expected.

| Latched difficulty | Failure stake |
| --- | --- |
| 0–3 | Free |
| 4–7 | Up to 50 gilt |
| 8–11 | Up to 100 gilt; half current HP when above one heart |
| 12 | Up to 200 gilt; half HP; one good food charm removed, or a minor curse if none exists |

## Items, food and modifiers

The 77 source tier rows retain source categories, 60/30/10 reward bands,
requirements and non-repeatable ownership. Bag/quiver and all three
butterflies use the later **common** source correction. Map and Compass are
rare tool rewards. KEY is eligible in ordinary source reward drops despite
an obsolete comment to the contrary. Four golden halves use separate
virtual IDs and flags, never collide with legacy inventory IDs.

All twenty normal food bits and special Fleet exist. Foods affect sword
knockback, speed, steadfastness, incoming knockback, enemy speed/fire
cadence, fire/ice/shock wards, gilt/kinstone/heart drops, shop prices, rare
luck, creeping rot, drowned sight, ember haze, edge/blunt damage and
any-health beams. Fleet grants 120 ticks of safety on room entry. One loose
shell grants 180 ticks. Nayru/Farore/Din stack their source incoming and
outgoing factors; zero incoming damage remains zero. Bottle charms apply
on drinking, not on acquiring a filled vessel. Picolytes use an explicit
added 30-second drop bias, preserving the individual bottle vocabulary.

Modifier queries are called by the parent integration and item/enemy
modules. Persistent inventory ownership is owned exclusively by
`legacy_items.c`; event rewards call its real grant path. The event module
never duplicates equipment state or writes SRAM itself.

## Waves, difficulty and meta

The thirteen integer tier rows exactly match the latest Gaussian-derived
source table. Difficulty changes tier probabilities rather than silently
banning upper tiers. The source's ten ordinary composition archetypes plus
its later Elite Trio use their actual minimum difficulty, role slots,
relative shares, count scale and forced tier. A cast is rolled once per
wave; up to five freshly selected species share a composition. One in four
casts prefers a common Fire/Ice/Undead/Bug/Aviary flavor. Live family caps,
killability prerequisites, dry-floor spawn checks, distance from Bloom and
a bounded cost budget apply before real enemy creation. Theme/role fallback
is bounded so an unavailable role cannot stall a room.

Wins raise difficulty by one to 12; deaths lower it with a floor of one.
Cross-run score and win counters never reset with run inventory. Optional
entitlement mode exposes common items immediately, uncommon items at 500
score/one win, rare items at 1500/two wins; key tools remain exempt so a
trial cannot be made insoluble. The optional Cream access entitlement is
500 score/one win. Pots use 500 score and fairies one win, preserving the
source's surviving unlock rules. The added optional difficulty cap is
`min(12, 3 + 2*wins + score/1500)`. Ordinary mode bypasses every such gate.

## Puzzle proof and validation

`tools/handoff_puzzle_pool.py` reproducibly emits 1,528 distinct native
5×5 boards: 96 template bases and 95 maze bases, each with eight D4
orientations. Template minimums use a feasible witness matching the exact
assignment-distance lower bound; axis maze minimums use push-state BFS with
canonical reachable-player components. Pushes require approaching the far
side, obey the colored axis, cannot chain or pull, and never plug entry or
exit. The separate Reset crystal and Select restore the certified board.
The ring and blocks use the actual feet collider, and the board disables
cape bypass while inside its boundary. Scavenger hiding uses the shared
`world_hidden_find` predicate against a real cuttable/diggable surface with a
dry reachable approach, rather than selecting an arbitrary empty tile.

Validation run on 2026-11-11:

- Generator: 1,000 seeded picks for each board family, **2,000 passes**;
  certified minima 1–12 pushes.
- Actual C host harness: **10,678 checks**, including all 1,528 witnesses,
  2,000 deliberately corrupt boards rejected, 1,000 distinct draft sets,
  10,000 eligible reward draws, food/charm arithmetic, announced stake
  behavior, optional entitlement gates/caps, 16-bit golden contract rewards, and fresh contract instances after prior exploration.
- ARM Thumb private compilation with `-Wall -Wextra -Werror` passed.
- `HandoffState` is 1,240 bytes; transient event/menu/loose-half state is
  about 182 bytes. Puzzle art/data stay in ROM. Parent owns final full-ROM
  build, extension-save verification and real mGBA captures.

Commands:

```sh
python3 tools/handoff_puzzle_pool.py --out src/handoff_puzzles.inc --report /tmp/handoff-puzzles.json
python3 tools/handoff_events_host.py --report /tmp/handoff-events-host.json
```

These host checks verify game logic and proof data; they are not emulator
renders or evidence of visual polish. Parent mGBA evidence must be labelled
separately from the source atlas.

A frozen integration-3 mGBA run also exercised the actual Drain entrance,
three-round draft, paid inn sleep, template and axis pushes, learned/recall
sequence including a repeated plate, and a neighboring-toggle puzzle.
Further real inputs completed the buried Scavenger task, a continuous
Stealth route, a Courier delivery in the real Forest entry, Hunt's actual
8-enemy quota, and Carry's two live ambushes plus pot delivery. No enemy,
health or completion state was written by these probes. Player position
and facing were navigation fixtures; the Mitts were actually drafted.
That review caught an overlay-only pot whose logical ground was not
liftable, a row/plate-height mismatch in the menu, and the need to stop
post-completion refills in Cream's required trial sites. These have source
fixes, all verified in the final integration-5 build. The reproducible
`tools/handoff_events_native.py` copies a ROM into a private test bundle,
derives current extension offsets from C, and performs native interactions,
including every pot lift/throw required to find the seeded pot.

Final integration-5 mGBA evidence (SHA-256
`c9a9d9e619a8d04ad61537bf2c7c79fa1a29e091cd74ebd39619cf25343205e5`):
services **14/14**, all seven quests **28/28**, the complete four-seal
contract **22/22**, and actual preference-save/reset/Continue **19/19**.
The contract completes a fresh board after its ordinary counterpart was
already cleared, fights the real wave and boss, grants its displayed item,
and awards all four Elements and Fourfold Sword. Preference changes restore
both the profile and matching completed run flags after reset.

```sh
python3 tools/handoff_events_native.py --out /tmp/handoff-services
python3 tools/handoff_events_native.py --out /tmp/handoff-quests --suite quests
python3 tools/handoff_events_native.py --out /tmp/handoff-contract --suite contract
python3 tools/handoff_events_native.py --out /tmp/handoff-meta --suite meta
```


## Original added art and shared style

`art/handoff_events.py` adds native 16×16, 4bpp props using the existing FX
material bank. It introduces **31** small frames, without repainting any
existing art: service desk/fuser, gold seal, portal, cache gleam, free and
axis-marked blocks, floor goal/reset crystal, silk/dust, lit/unlit censer,
four watcher directions, parcel/pot/recipient, nine distinct colored shaped
kinstone halves and a cuttable leaf pile. Menu rows use the native 16-pixel plate height with four visible rows and scrolling, so a selected border cannot strike through its neighbor. The source cave floor, wall,
spring and chest art are reused exactly.

Local additions follow the shared art bible: one dark silhouette contour,
short horizontal clusters, top-left gold highlights, clear warm interactable
contrast, and teal/wine horizontal/vertical block marks. Distinct kin-half
cutouts communicate **shape as well as color**. No new global palette,
Bloom body animation, background floor, forest tree, old object or existing
HUD is changed by this module. New course artwork has its own module notes.
