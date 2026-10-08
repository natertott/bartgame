# QUICKSTART redesign plan: the win chain, reachability, and the next content wave

Written 2026-10-08 from the user's scoping list, checked against the current
roadmap (`docs/QUICKSTART_ROADMAP.md`), the third simulation pass
(`docs/QUICKSTART_SIM_REPORT.md`, 50,000 runs) and the code. Numbers in
this document are measured unless marked as estimates.

The user's framing, kept as the brief: "The most important thing is that
I have not been able to actually achieve a win condition in many
playthroughs, so I think something is broken there." Everything below is
ordered around that sentence first and the content wave second.

---

## 0. The one-page version

1. **The win condition is broken in measurable ways**, and three of them
   are hard failures a player cannot recover from:
   - **10% of simulated runs put the Earth Element in a region the run
     never reaches** (Royal Valley 4%, Lake Hylia 2.7%, the Wind Ruins 1%,
     Veil Falls 0.7%, the rest scattered). The element region is drawn by
     map distance from the drop, not by reach. This is the largest single
     cause of unwinnable runs and it has been there since the element hunt.
   - **2.3% of runs dealt a chain step on a ? room site whose event never
     spawns** - two site rows (Mount Crenel Center, Veil Falls Top) sit in
     region rooms, where the room monitor runs the region loop and never the
     site dispatch. Retired today (`QuickStartSiteRetired`); the build in
     this commit carries it.
   - **A chain step's completion is only as good as the kind's "I am done"
     signal**, and nothing audits that per kind and per site. The scenario
     probe proves every kind SPAWNS; nothing proves every kind FINISHES and
     sets `GF_CONTENT_SITE_DONE`. This is the most likely home of the "I did
     everything in the region and nothing advanced" report.
2. **The soft failures are the hint and the pacing.** A step is hinted by
   REGION ("A room by Veil Falls has something happening in it") while the
   region holds ten ? rooms, some of them behind prices the hint does not
   mention; a WAVE step wants N region clears with no counter shown; a
   keyed pair wants an item the player does not know they lack. The
   compass marks the room, but only a run that found the compass.
3. **Fix order:** (P0) the element draw and the completion audit, with a
   probe that plays a chain to the end on the ROM; (P1) a redesigned chain
   that names rooms, shows progress and spreads across regions; (P1) lock
   down reach (the eleven unsurveyed rows, the Wind Ruins' missing row, the
   four Mount Crenel caves, a testable MINISH); then (P2) performance,
   Hyrule Town, the puzzle and quest wave, the hub, blessings and shells;
   (P3) the castle and the dungeons.
4. **Pushback worth having:** three of the asks (Hyrule Town, the castle,
   the dungeons) widen the world before the chain works in the world we
   have, which is the roadmap's own "depth before breadth" rule. They are
   scoped below and sequenced after the chain is proven, not dropped.

---

## 1. The list, against what exists

| the ask | what exists today | the gap |
|---|---|---|
| Win chain works and is understandable | Five-step chain (EVENT/WAVE/BOSS/QUEST/ITEM), keyed pairs for four keys, Ezlo region hints, compass marker, three win carriers in the element region | Element region not reach-checked; two dead sites; no per-kind completion audit; region-level hints; no progress display; steps cluster (ranch house 24% of runs) |
| Variability of regions, paths, starts | 19 pool rows over 14 regions, 117 sites, 42 reach nodes, 628 destination rows, 50,000-run simulator with ROM parity | Drops per row (EH/WW 20% each); one key item from the hub; 68 rooms never reached by a strict run, 9 by any; four regions nearly dead (RV 7%, LH 9%, WR 1%, VF 21% entered) |
| Hyrule Town, cleared and locked, full of monsters | Stitched OUT: its four field borders are retargeted to each other (`docs/QUICKSTART_RETARGETS.md`); 35 exits from the town plaza, 29 of them house doors | A fifteenth region: borders restored, doors cancelled, vanilla content swept, enemy spots, pool row, survey block |
| Performance dips (Boomerang cave, Trilby cave, Lon Lon) | Two profiling rounds (Aug 2026) fixed field-wide lag: live-entity ceiling 28, segmented enemies censused, two per-frame sweeps latched, mixer rate; `fps_probe.py` | The three named rooms were not in those rounds. Boomerang cave holds FIVE sites at once; Trilby cave two plus a push block and a bomb wall; Lon Lon's cap may be beaten by segment chains again |
| Many more puzzles, robustly tested | Blink memory (two rooms), dojo plate puzzle, dark rooms, boomerang switches, maze doors, carry quest, "the watch" stealth, hunt, scavenger, lotteries, fairies, gauntlets, minibosses; the scenario testbed drives each kind | Few PUZZLE kinds against many combat kinds; no per-puzzle solver probe; carry quest cannot cross an area |
| Vanilla story content as quests | Lon Lon key, graveyard key, golden kinstones, nine fusion gates, shoe merchant fusions; `docs/QUICKSTART_GUIDE_FINDINGS.md` §6 assessed seven portable quests and recommended three | None of the three ported (courier, Gregal's ghost, Percy's monster lady); no dungeon content beyond two entrance rooms as ? sites |
| The rest of the vanilla map, dungeons included | Guide census of every dungeon's rooms and what gates them (§3.4): Deepwood and Cave of Flames fully payable, the rest 30-97% behind sword clones | No dungeon reach map; no per-run small-key economy; no dungeon-as-step kind |
| The hub: cramped, slow, inn unused, trophies as text | Four floors (74-184 open tiles each), three selection rounds, shop, inn rest, trophy case as text rows, wandering hint NPCs, roof wave, the hole | Floor travel is stairs; the inn is one rest; trophies have no sprites |
| Hyrule Castle / Dark Hyrule Castle | Guide notes (§3.2): entry is the Castle Garden cellar ladder (sword; the guard sneak is already cleared every frame); Dark Hyrule Castle is 70% clone-gated | Nothing built |
| More blessings/curses, recoloured sprites | 20 food/charm effects (`QUICKSTART_FOOD_*`), Link's palette tint already driven by a charm byte, kinstones already use per-type object palettes | No recolour pipeline for ground items; the effect list is flat (no tiers) |
| Seashells as 3 s invincibility | `ITEM_SHELLS` is the luck charm (rarer rewards); vanilla's `iframes` on the player entity is a frame-count immunity the engine already honours | Shells need a new role, an enemy drop weight, a visible flash and a sound |

---

## 2. Why the win condition fails, measured

### 2.1 Hard failures (the run cannot end)

**The element region ignores reach.** `QuickStartRollElementRegionOnce`
draws the element's pool row from the regions within two map hops of the
drop, then filters by the carrier (boss or wave rooms) and, since this
month, by the golden gates. It never asks whether the run can GET there.
In the third pass 10.1% of strict runs and 10.3% of rewards runs ended the
chain with the element region unreachable - and in 9% NO room of that region
was explorable. By region: Royal Valley 1,023 of 25,000 (bombs and
bracelets), Lake Hylia 639 (flippers), the Ruins 262, Veil Falls 169, and
a tail (EH 158, CG 72, TRIL 57...) that is the drop's own entrance pocket
not joining the region. The fix is one filter: draw the element among the
rows the CURRENT kit reaches (`QuickStartReachPoolOk` over the drop's
flood), and re-roll it at run start only - the same place it is rolled now.
Simulate before and after; the target is 0% unreachable at the drop and a
measured share still unreachable at step 4 only where the kit shrank (it
cannot).

**Two sites the dispatch never reaches.** Asked the ROM
(`QuickStartIsNamedRegionRoom`) for every site row: 81 (Mount Crenel
Center), 82 (Mount Crenel Entrance, already retired) and 116 (Veil Falls
Top). 81 and 116 were live and were dealt as EVENT steps in 1,141 of 50,000
runs. Retired in this commit. The general fix belongs in the invariant
checker: a site in a named region room is a FAIL.

**Completion signalling is unaudited.** An EVENT step is met when
`GF_CONTENT_SITE_DONE` is set, and that bit is set only when the kind's own
monitor returns "finished" (`QuickStartSetupEventContent`), by the fairy's
reward script, or by the memory lesson. A WAVE step is met when the
region's clear counter reaches the step's target (current count + 1 at
deal time). A BOSS step is met by a latch the boss's death sets. A QUEST
step by `QuickStartSideQuestDone`. Any of those paths can fail for one
kind in one room - a prize the player cannot pick up, a wave that counts
the whole room, a lottery whose "taken" state is never written - and the
player's experience is exactly the report: everything in the region done,
nothing advancing. What is missing is a probe that, for every site and
every kind the site can roll, drives the event to its end on the ROM and
asserts the DONE bit (and for every pool row, drives a region clear and
asserts the counter). The scenario testbed (`scenario.py site N KIND`)
already boots each one; the probe is the loop around it and the inputs
that finish each kind.

**A keyed ITEM step that cannot pay.** The pair guarantees the key as the
next reward "in an allowed region"; if the player never earns another
reward in those regions (they are far, or they stop clearing), the step
waits forever. 9% of runs carry one now. The guard is cheap: if the key is
not paid within N rewards anywhere, pay it anywhere.

### 2.2 Soft failures (the run can end, the player cannot tell how)

- **Region-level hints.** "A room by X has something happening in it"
  covers every ? room in X, including rooms priced beyond the kit (the
  chain checks the kit, the player does not know it did). Castor Wilds is
  entered in 98% of runs with a median 0% of rooms explorable: a step
  placed there reads as a lie to a player without boots or cape.
- **No progress.** Nothing says "step 2 of 5", nothing says a wave counted
  toward the step, nothing confirms the event that just finished WAS the
  step. The chain hint is one line at step start and on Select.
- **Clustering.** The ranch house hosts a requirement in 24% of runs;
  Eastern Hills and Western Wood take a third of all placements because
  they have three pool rows each. Runs feel the same.
- **Gates the hint does not mention.** Sealed golden gates, boulders, the
  Lon Lon strip's one-way ledge, Minish-only rooms: the chain never places
  behind them (the reach model is conservative), but the hint's region is
  the same word either way, so the player cannot tell "walk in" from "you
  lack the lantern".

### 2.3 Variability, measured

Strict cohort: median 41 of 181 rooms reachable after the hub and 42 by the
fourth step; rewards cohort grows to 57. 68 rooms never reached by a strict
run, 9 by any (the Ruins' three rooms - the pool row's own room has no
survey row - the Goron cave behind Lon Lon's boulder 2, two unsurveyed
Minish Woods rooms, Mount Crenel's dig cave, the falls' heart-piece nook).
12 of 117 sites never reachable, four of them Mount Crenel caves with no
survey row. Steps: EVENT 54%, WAVE 24%, QUEST 14%, BOSS 5%, ITEM 3%.
`MINISH` is the largest single untestable price: being Minish is a state,
so the model refuses every Minish room, though the player always has the
cap and the portal table (`world_reach.MINISH_PORTAL`) knows where
shrinking is free.

---

## 3. The redesigned win chain (P0-P1)

### 3.1 Principles

1. **Every step is proven, not priced.** Before a step is dealt the ROM
   must be able to answer "reachable with the kit the player holds now AND
   completable by a mechanism that sets a flag this chain reads". The first
   half exists (the reach graph); the second half is the completion audit
   (§2.1) turned into a per-kind table the dealer consults.
2. **The element follows the reach, never the map.** Drawn among reachable
   rows at run start; the three carriers keep their filters.
3. **A step names a room, and the player can always read the list.** The
   compass marker already resolves a step to a room; the hint should too
   ("the cave under Trilby's cliff", one line per site row, a data-entry
   job of ~117 lines), and Select should show all five steps with a tick
   on the finished ones. A finished step gets its own line the moment it
   completes.
4. **Spread.** No two steps in one region unless the ring has fewer than
   five reachable regions; drops drawn over regions, then rows.
5. **Growth is the chain's job again.** The sim shows growth comes only
   from region-clear luck. The keyed pair is the right shape (a key, then
   the door it opens); extend it: a step may name a KEY ITEM the next step
   needs (grip ring, then a Mount Crenel room; flippers, then a lake room),
   paid by the step before it. That is the designed escalation the first
   roadmap wanted and it makes the "entered but not explorable" regions
   playable on purpose.
6. **A stuck step heals.** If a step's target becomes impossible (a gate
   re-sealed, a region left unreachable by a kit change the player cannot
   undo - there are none today, but the dungeon work will add some), the
   monitor re-rolls that step and says so.

### 3.2 What to build, in order

| # | item | size | depends on | proof |
|---|---|---|---|---|
| P0.1 | Element region drawn from reachable rows | S | - | sim: 0% unreachable at drop; `scenario_probe` |
| P0.2 | Retire sites 81/116 (done); invariant FAIL for a site in a region room | S | - | `invariant_check --static-only` |
| P0.3 | **Completion audit probe**: for each site x kind and each pool row, finish the event on the ROM and assert DONE / the wave counter | L | scenario testbed | a table of 117 x kinds, every cell PASS |
| P0.4 | Keyed step pays anywhere after N unpaid rewards | S | - | sim + `scenario.py chain` |
| P1.1 | Room-naming hint lines (one per site row) and a Select screen listing the five steps with ticks | M | - | `memory_probe`-style textbox checks |
| P1.2 | Spread rule (one step per region) and drops by region then row | S | - | sim: ranch-house share, EH/WW share |
| P1.3 | Key-item steps that unlock the NEXT step's region (the escalation) | M | P0.3 | sim: growth of strict cohort > flat |
| P1.4 | Chain-end probe: boot 200 seeds, drive every step to completion with scripted inputs, reach the element, win | L | P0.3, P1.1 | 200/200 wins or a named cause per failure |
| P1.5 | Reach lock-down (see §4) | M + walks | user walks | `sim_validate` 402/402, never-reached list shrinks |

### 3.3 Reach lock-down (P1.5)

Data gaps the sim names, each a row or a walk:

- `RUINS/ENTRANCE` has no survey row though it is the Ruins' pool landing;
  `BELOW_FORTRESS_ENTRANCE` and `FORTRESS_ENTRANCE` are priced "never".
  The Ruins' entrance stamp (32812, -2624) is mid-transition. One walk.
- Four Mount Crenel cave sites with no row (fairy fountain, chuchu pot
  chest, spiny chu puzzle, water heart piece). One walk, probably a half
  hour on the upper mountain with the grip.
- The eleven rows marked INFERRED or UNWALKED in the Veil Falls and Lon
  Lon blocks (listed in `docs/QUICKSTART_BOULDER_SURVEY_2026-10-06.md` §8).
- **Make MINISH testable.** The player always has the cap; what varies is
  a free portal in the region. `MINISH_PORTAL` already prices that per
  region ([] free, [[BOOTS]] tree-hidden, None for Royal Valley). Fold it
  into the held mask: MINISH held in any region whose portal price the kit
  pays. This is the single change that moves the most rooms (the second
  pass measured 58 Minish rooms dead; the MINISH model cut that to 8 for
  pricing but the held mask still never sets the bit).
- Boulders in play: the model never pushes one. Add a cohort that pushes
  the boulders the kit allows (bracelets for the ones that need them) so
  the sim stops reporting the Goron cave and the Castor passage as dead.
- Entered-but-not-explorable regions: Castor Wilds' free border makes it
  "open" to the chain while the swamp is not. The dealer should use
  room-level reach (it does for EVENT) for WAVE and BOSS too: a wave must be
  placed in a region where the player can stand on open ground beyond the
  entrance, which the entered-vs-explored measure already computes.

---

## 4. Performance (P2, measured first)

History: the Aug 2026 rounds found the field-wide lag was total live
entities past ~45 (segmented enemies multiplying after the placement cap)
plus two per-frame sweeps of ours, and the mixer; `fps_probe.py` reads the
true frame rate from RAM. The three rooms the user names were not in those
measurements and each has a plausible mechanism:

- **Boomerang cave:** five ? sites in one room (four trees and the
  staircase), each with its own event and enemies, plus four boomerang
  switches with their tile rewrites, plus the vanilla room's own entities.
  A multi-site room can deal five events' spawns at once; the live ceiling
  is per deal, not per room.
- **Trilby cave (push block, bomb wall):** two sites, the push block's
  per-frame tile logic, the bomb wall's flag checks, and a chamber small
  enough that a gauntlet wave sized "4/5/6 at the shipped counter" crowds
  one screen.
- **Lon Lon Ranch overloaded:** the segment-chain multiplication again
  (moldworms, moldorms), or the region wave plus a boss arena plus the
  carry/stealth givers in one room.

Plan: (1) extend `fps_probe.py` with an entity census per kind and per
source (QuickStart vs vanilla) and run it in the three rooms at difficulty
3 and 5 with each site kind forced through the testbed; (2) whatever the
census names: a per-ROOM live ceiling across all sites, segmented kinds
barred from rooms under N open tiles, a second-site activation gate (the
next chamber's event spawns when the player is within a screen of it, not
on room entry), and the audio-light build's mixer settings if the mixer
shows again; (3) a frame-time table before/after in the roadmap. Size: M.
Depends on nothing; can run in parallel with P0.

---

## 5. Hyrule Town as the fifteenth region (P2)

Scope as asked: no ? rooms, every house locked, the plaza full of
monsters. Work items, all with precedent in the Veil Falls integration:

1. Restore the four border transitions (`transitions.c` retargets listed
   in `docs/QUICKSTART_RETARGETS.md`) under QUICKSTART, and un-retarget
   Stockwell's shop door or leave the shop stitched out (recommend: leave
   it out; the hub has a shop).
2. Cancel the 29 house doors and the underground/cave/tree exits in
   containment (the existing cancelled-door mechanism), so the town is one
   plaza. Keep the Minish house door cancelled too.
3. Sweep vanilla content at room load: NPCs (the town's cast is large and
   scripted), cuccos, the sign posts and shop stalls that script
   interactions - `QuickStartClearVanillaRoomContent` plus a town quirk
   hook, the pattern Eastern Hills and Veil Falls Top use.
4. Enemy spot table sampled over the plaza (`spawn_spread.py`), a pool row
   (drop target) with reward and drop spots, waves allowed, boss allowlist
   decided by arena size (the plaza is large; a boss probably fits).
5. Region enum, adjacency (NHF, SHF, LLR, TRIL - the four borders), a
   survey block (the plaza is flat; a short walk settles it), hint lines
   (region line + five pair lines), owners table, sim tables.
6. GFX budget check: the town's tileset is heavy; the spawn audit's GFX
   tier will say how many enemy sheets fit.

Size: M. Depends on P0 only in the sense that a new region should not go
in before the chain is proven; mechanically it is independent.

---

## 6. Puzzles and quests (P2, the content wave)

### 6.1 Puzzle kinds to add, with how each is tested

Each puzzle is a ? room kind with a SOLVED flag the chain reads, a
testbed scenario that boots it, and a solver probe that finishes it with
scripted inputs. That trio is the "robust test" the user asked for; the
blink memory room is the template (lesson/recital, solved flag, a wave on a
wrong answer, `memory_probe.py` 9/9).

| kind | mechanism (vanilla pieces) | solver probe |
|---|---|---|
| Push-stone to plates | `PUSHABLE_ROCK` / block objects onto pressure plates (the dojo plate puzzle already exists); 2-4 blocks, one-way pushes make it a puzzle | path-plan the pushes from collision, press |
| Torch order | lightable torches (lantern) in a sequence shown by a hint sprite; wrong order relights all | light in order |
| Boomerang switches as a puzzle | the Boomerang cave's four switches, dealt as "throw in the shown order" | throw sequence |
| Dig for the key | Mole Mitts rooms: N dig spots, one holds the door's trigger; hints by sound/sparkle | dig all |
| Statue drag | Power Bracelets large blocks onto floor eyes (Fortress-style, without clones) | push sequence |
| Lantern dark maze | dark rooms exist; add moving sentries | path |
| Stealth v2 ("the watch" improved) | sentries with cones (vanilla guards' sight logic), a safe route that changes per seed, a bell on detection, no wave spam | path along the safe route |
| Carry within one area | keep the parcel inside one region's rooms (same area, no area change); the seam rebuild already works within an area and fails across areas, so restrict the giver/target pairs to same-area rooms | carry and deliver |
| Delivery (courier) | the GUIDE §6.6 port: an item from NPC A to NPC B two regions apart, with its own carried-item bit (not a held object) | talk, walk, talk |
| Escort / fetch-the-ghost | Gregal's ghost (Gust Jar) | one interaction |
| Kinstone chain | fuse at A to open B where the piece for C is | fuse, walk |

Target: six new puzzle kinds in the first wave, each with a probe, before
any dungeon work. Size: L (two to three kinds a week at the pace the memory
room set).

### 6.2 Vanilla story content as quests

From `docs/QUICKSTART_GUIDE_FINDINGS.md` §6, in order: the courier (Smith's
sword to the Minister as the first skin; generalises to seven vanilla
deliveries), Gregal's ghost, Percy's monster lady. Each is a QUEST kind the
chain already knows how to deal and complete. Dungeon-flavoured quests
(§7) come after the dungeons have a reach map.

---

## 7. The rest of the map: castle and dungeons (P3)

**What the census says.** Deepwood Shrine and the Cave of Flames are
payable end to end with the mode's items; the Fortress 70%, the Temple of
Droplets 45%, the Royal Crypt 43%, Dark Hyrule Castle 30%, the Palace of
Winds 3% - the rest is sword-clone puzzles the mode has no mechanism for.
Hyrule Castle proper is entered from the Castle Garden cellar ladder with a
sword; Dark Hyrule Castle replaces it after the Four Sword.

**Dungeon reach map.** A probe can get most of it: flood each dungeon room's
collision from each door, read the door list and the key/boss doors from
the map data, and emit per-room rows priced at `KEY(n)`, `BIG_KEY`, the
item each puzzle wants, and `CLONES(n)` (untestable, like MAZE). What a
probe cannot see is which puzzle actually blocks a door - that is the
user's walk, room by room, as with the overworld.

**Per-run small keys.** Vanilla keys are per-dungeon inventory in the save;
the run start must wipe them and the dungeon's door flags, like local
flags. One line per dungeon in the run reset; the invariant checker learns
the flag ranges.

**How dungeons enter the game**, three ways, cheapest first:
1. Dungeon rooms as ? room sites (two already are).
2. A dungeon as a QUEST or EVENT step: "find the big key" (a chest the
   chain places) or "defeat the dungeon's boss" (the boss arena and a
   latch, the pattern the overworld bosses use).
3. A dungeon as a region: Deepwood and the Cave of Flames only, as a drop
   target with its own pool row, waves and sites. The castle as a region
   is the same shape with the Castle Garden ladder as its border.

Dark Hyrule Castle and the Palace of Winds stay ? room sites and boss
arenas; nothing else in them is payable.

---

## 8. The hub (P2)

The survey (`docs/QUICKSTART_HUB.md`) measured 74-184 open tiles per floor
and stairs between floors. Proposals, each a measured change:

- **Travel:** a warp pad per floor (vanilla warp points exist; the roof
  already has the wind crest) so the shop, inn and selection are one step
  apart; or collapse to two floors - selection and services - with the
  roof wave as the third.
- **Room:** the tower's floors are what they are; the real fix for
  "cramped" is fewer things per floor (the selection round's three items
  on one floor, the shop's four slots on another, the inn and trophy case
  together). Measure the walk time between the three selection rounds
  before and after.
- **Inn:** rest is one heal at a price. Make it the place where the
  run's blessings are chosen (one of three baked goods, see §9) and where
  the previous run's trophies pay a one-time bonus; then it is visited
  every run.
- **Trophy case with sprites:** the catalog has 70 rows; a page of 8-12
  pedestals with the item's ground sprite on each is a GFX-slot question
  (44 slots game-wide, measured in `docs/QUICKSTART_QUEST_RESEARCH.md`
  §1.2), answered by the budget probe before the case is redrawn.

---

## 9. Blessings and curses (P2)

**Recolouring is feasible.** Object sprites draw through an object
palette slot (`objPalette` in the sprite settings; the kinstone's own
table picks a palette per piece), and Link's charm tint already loads a
modified palette from a charm byte. A recoloured brioche is a copy of the
item's 16-colour palette with its browns shifted to greens or golds, loaded
into one of the reserved object palette slots when the item spawns, and
the item's `type2` saying which. Cost: palette slots are a shared budget
(four reserved for palettes, measured Aug 2026); one slot per tier in use
at a time is affordable, a slot per item is not. Probe: spawn each tier,
screenshot, compare palettes.

**Tiers:** brown = blessing, green = curse, gold = greater blessing, on the
same sprite; the pickup line names the tier. The food block has 20 effect
bits; the save has room for a tier byte per effect.

**New effects worth testing** (each one a flag and a hook, like the
twenty): double rupees but half hearts; enemies drop bombs/arrows (exists:
make tiers); invincibility on room entry for 2 s; sword beam always but
knockback doubled (curse pair); magnet for drops; slow enemies / fast
enemies; one free fairy per region; the compass points at the next step
(a blessing that IS the hint fix for one run); dark rooms lit; waves one
enemy smaller; prices halved / doubled; a curse that re-seals one golden
gate; a blessing that pushes one boulder for you.

---

## 10. Seashells as invincibility (P2, small)

- Vanilla's player entity carries `iframes`, a frame count during which
  damage is refused and the hurt-blink runs (`hurtBlinkSpeed`). Picking up
  a shell sets `iframes = 180` (3 s), plays a sound, and tints Link through
  the same palette path the charm tint uses (cycle three palettes every
  four frames for the Mario feel), restoring the tint when the count ends.
- Enemies drop shells: a weight in the drop table next to hearts and
  rupees, rarer than hearts; the shell count the engine keeps is left at 0
  so the pickup never counts as a collectible.
- `ITEM_SHELLS` is the luck charm today (charm 14). Move the luck charm to
  another unused sprite so the shell is unambiguous.
- Probe: spawn a shell, pick it up, take a hit, assert health unchanged
  for 180 frames and reduced at 181.

---

## 11. Order of work, with sizes

| phase | items | why here |
|---|---|---|
| **P0 (this week)** | element draw from reach (S); dead-site invariant (S, the two sites are retired); completion audit probe (L); keyed step pays anywhere (S) | the three hard failures; every later feature is measured against a chain that can end |
| **P1** | chain redesign: room hints and the step list (M); spread and drops by region (S); key-item escalation steps (M); chain-end probe over 200 seeds (L); reach lock-down (M + walks) | the soft failures and variability; the chain-end probe is the acceptance test for everything after |
| **P2a** | performance census and fixes in the three rooms (M) | independent, user-visible, parallel to P1 |
| **P2b** | Hyrule Town region (M); six puzzle kinds with solvers (L); the three quest ports (M); shells (S); blessing tiers and recolours (M); hub travel, inn, trophy sprites (M) | content wave, each item a data row plus a probe, in the order the chain-end probe can absorb them |
| **P3** | dungeon reach probe and walks (L); per-run keys (S); Deepwood and Cave of Flames as regions (L); castle entry (M); the rest as sites and arenas (S) | breadth, after depth |

Sizes: S under a day, M two to four days, L a week or more, at the pace
the roadmap's shipped batches set.

### What is needed from the user

- Walks: the Wind Ruins from Castor Wilds; Mount Crenel's four upper caves;
  the eleven inferred Veil Falls / Lon Lon rows; Hyrule Town's plaza once
  it is open; each dungeon's puzzle gates once the probe has the doors.
- Play: a sealed golden gate end to end; a run whose hint names a room (P1)
  with the step list open, to say whether it reads right.
- Decisions: the puzzle kinds to build first (§6.1 proposes six); whether
  dungeons become regions or stay steps (§7); the hub's shape (§8).

---

## 12. Feedback on the plan

- **Agree with the diagnosis, and the measurements sharpen it.** The chain
  fails for reasons that are not the player's: a tenth of runs cannot be
  won at all, a fortieth were dealt a step that cannot fire, and the rest
  of the confusion is a hint that names a region when the game knows the
  room. Fixing the first two is days, not weeks, and the third is data
  entry.
- **Build the proof before the redesign.** The chain-end probe (P1.4) is
  the thing this project has never had: a machine that plays a run to the
  win. With it, every change to the chain, every new puzzle and every new
  region has one acceptance test. Without it the redesign will be judged
  the way the current chain was - by a player who could not win and could
  not say why. It should be the first large item built.
- **Keep "depth before breadth".** Hyrule Town, the castle and the
  dungeons are good additions and they will each add new ways for the
  chain to be wrong. Sequence them after the probe exists so each arrives
  with its own measured proof. Hyrule Town as a monster plaza is the
  cheapest of the three and the only one worth doing before the chain is
  redesigned, because it adds a region with nothing to break.
- **Make MINISH testable.** Of all the reach changes, this one is a few
  lines and moves the most rooms. The model's conservatism here costs
  more variability than any other single decision.
- **The carry quest within one area is the right call.** Cross-area
  carries need a rebuild on every area load that the engine resists; the
  seam rebuild already works within an area. Same-area giver/target pairs
  keep the quest and drop the failure.
- **Seashells: 3 s is right, the drop rate is the risk.** Shells that drop
  as often as hearts make waves trivial; weight them rarer than hearts and
  bar them from boss arenas, or the boss batch's balance work is undone.
- **Blessing tiers beat more flat effects.** Three tiers on the existing
  twenty gives sixty outcomes for the price of a palette slot and a tier
  byte; new effects can follow once the tiers are visible.
- **One suggestion the list does not have:** a run summary at the end
  (steps, regions, items, time), because the meta loop's score needs it
  and because it is how the player learns what the chain asked for. It is
  cheap once the step list (P1.1) exists.
