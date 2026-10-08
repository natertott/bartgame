# Status: what is built, what is not

Companion to `HANDOFF_GAME.md`. This is a **summary** of
`docs/QUICKSTART_ROADMAP.md`, which is ~4,700 lines and is the real record -
every batch entry there explains not just what changed but what was measured
and what was got wrong on the way. Read the roadmap entry for any area you
are about to touch; this file tells you which entry to look for.

Current head when this was written: **`4e07f00`** (this batch is the commit on top of it), branch
`claude/gba-fan-game-start-ptuvhn`.

---

## Built and probe-verified

**The run loop, end to end.** Hub with three selection rounds, shop, trophy
case, inn rest, wandering hint NPCs; the sky drop with per-region landing
spots and kit-aware re-rolls; a 14-region free-roam ring walked on foot; a
five-step win chain; the Earth Element hunt; win and reset.

**Combat.** Six enemy tiers covering 57 of the game's 102 enemy ids; ten
composition archetypes; per-family live caps; a size-normalised difficulty
curve over 13 steps; an Elites tier that doubles as the miniboss pool; weapon
gating for enemies a sword cannot kill; two bosses (ChuChu, Big Octorok) with
a vetted per-region allowlist.

**Content systems.** Three "? room" systems with nine event kinds; 117
content sites; quests; 14 charms/curses; the kinstone fusion economy with
travelling fusers; the map and compass; the trophy case browsing all 70
obtainable things.

**The reachability model.** A walked survey compiled into `reach.h`, a region
flood, per-room gating, and a win chain that only places requirements where
the player can already stand. Validated against the shipped ROM by
`sim_validate.py` (402/402 at last run).

**Simulation.** `sim.py` reimplements every seed-driven part of a run and can
play 100,000 of them in under two minutes; `sim_report.py` renders nine
charts and a report into `docs/sim/` and `docs/QUICKSTART_SIM_REPORT.md`.

---

## Shipped in the most recent session (read these roadmap entries first)

| what | roadmap entry |
|---|---|
| The performance dips: the memory-pair lookup cost 57% of every ? room frame (Boomerang cave 20 fps, Trilby's cave 30); cached, 60 everywhere in a 140-sample sweep; the fountain's ranking; Great Fairy rooms out of the memory pair | "The performance dips: one lookup, asked per site per frame" |
| P0 and P1 of the redesign: the finale drawn from live reach when the fourth trial completes; the completion audit (708 cells, 612 PASS) and the five content defects it found fixed; sites 7 and 72 retired; room-naming hints; spread and drops by region; escalation pairs; the keyed step's patience; the chain-end and win probes, and the step-roll freeze they found; seashells as three seconds of invincibility | "P0 and P1 of the redesign: the chain can end, and says where" |
| The redesign plan (`docs/QUICKSTART_REDESIGN_PLAN.md`); sites 81 and 116 retired (chain steps on them could never finish); the element lands unreachable in 10% of runs (P0.1, not yet fixed) | "The redesign plan, and two steps the chain could deal but never finish" |
| The keyed pair asks about one key per roll, round-robin from the step, one roll in ten: ITEM steps in 9% of runs (was 40%), ranch-house visits 24% (was 49%) | "The keyed pair, round-robin and one in ten" |
| The Crenel vine actually grows now (two local flags at run start); a user report, measured and fixed | "The Crenel vine was never grown" |
| The third simulation pass: 50,000 runs, a simulator checkpoint bug fixed first, the report regenerated with a third-pass narrative | "The third simulation pass" |
| The golden kinstone gates: the Source of the Flow stone and the Castor statues roll sealed or open per run; the pieces are key items and win-chain keys | "The golden kinstone gates" |
| Veil Falls integrated: pool row, 12 sites, 5 fusers, borders restored, vortex removed; the boulder survey's answers applied | "Veil Falls is the fourteenth region" |
| 50,000-run simulation study, and a second pass that corrected three of its four headline findings | "50,000 simulated runs...", "The second pass..." |
| Quest guard fix (31.7% of runs were dealt the side quest twice) | "The second pass..." |
| Bombs became a `QS_CAT_KEY` item | "The second pass..." |
| Castle Garden priced "never" and Royal Valley priced "free" - both corrected | "The second pass..." |
| Fuser cast rebuilt from rendered evidence (4 of 8 faces drew garbage) | "Faces that actually draw..." |
| Difficulty stopped gating tiers; the curve is generated now | "Faces that actually draw..." |
| GFX budget fallout: sheet costs, a room-flag collision, a starved-fuser bug | "The GFX bill for faces that actually draw" |
| Enemy ceiling priced against the GFX table instead of room area | "Lon Lon's two slots, bought properly" |
| Spawn spreads for Trilby and Lake Hylia; Eastern Hills North boss moved | "Where enemies spawn..." |
| Mount Crenel: waves keep spawning, lose their clear reward and can never be a win requirement | "Mount Crenel keeps its waves..." |
| The MINISH model - 58 dead rooms became 8 | "The MINISH model, encoded..." |
| Trilby's boss arena was clamped to the wrong pocket | "Trilby's boss arena..." |
| The feature testbed (a scenario in the save, `scenario.py`) and the carry quest | "The feature testbed and the carry quest" |
| Scenario saves (`make_sav.py`, 23 files), kit 2 = everything, upgrades/butterflies to COMMON, ammo drop weight | "Scenario saves with a full kit" |
| Switch puzzles retired; the two-room blink memory event; mixed gauntlet waves | "The switch puzzles retired" |
| The stuck-wave recentering retired; Lake Hylia and Lon Lon Ranch host no clear challenge | "The wave recentering is gone" |
| Bosses take any blade, the chuchu's walk-home freeze, 5% boss roll and a one-boss cap, roomier Lon Lon/South Field spawns, one reward per chain step, key items in every drop pool | "The Oct 2026 boss batch" |
| Enemy difficulty lags the counter by two (d5 spawns like old d3), three hearts and a bottled fairy at run start, the 100-room spawn audit, the per-kind escape hatch closed, multi-site gauntlets count their own chamber and own their seam record | "The spawn audit: void corners, multi-site gauntlets" |
| Gauntlet waves sized to the chamber: floor tiles / a per-difficulty density (16 down to 5 tiles per enemy) + 1 per wave | "Gauntlet waves sized to the chamber" |
| Boulder auto-fill retired; boulders are run-time reach bits; reach floods a graph of entrances (36 nodes); four regions re-walked per entrance; Trilby arena moved; sites 17 and 82 retired | "The boulders are the player's again" |

---

## Outstanding

### Needs the user, not an agent

- **Play a sealed golden gate.** Half the runs seal the Source of the
  Flow stone and half the Castor statues (`GF_GOLD_GATE_SEALED_BIT`).
  Nobody has found a piece in play, fused it at the stone through the
  menu, or run the statues' rock cutscene; the probe writes the fused bit
  and the passage flag instead. Say whether Ezlo's lines 212-213 read
  right and whether the piece came in time.
- **Walk Veil Falls' inferred rows.** `docs/QUICKSTART_BOULDER_SURVEY_2026-10-06.md`
  section 8: the ledge chest's chain (cave #1's upper room, its bombable
  north wall, the secret chest, the dark staircase, the block puzzle, out
  onto the ledge), the heart-piece nook's fusion, the drop plateau's own
  prices, and the lower strip. Also: say which build showed cave #1 as
  sealed - on the delivered ROM the door is open and measured so.
- **Play a drop into Veil Falls.** The landing, fuser spots and sites are
  measured; the climb was driven with the ring; nobody has played a run
  there. (Item 11 of section 4 is resolved: the user confirmed Lon Lon's
  boulder 3 for the (712,750) exit.)
- **Walk the unsurveyed landings** (report section 5): Eastern Hills North
  from the Lon Lon border, South Field's four port-model seams, Trilby from
  Crenel, Lake Hylia's shore and the Wind Ruins with their own boulders
  in place.
- **Push a boulder in play** and check the chain offers the pocket after:
  Trilby from the south (the treehouse), Lon Lon from the lake (the north
  field). The probes set the flags; nobody has pushed one.
- **Play a three-wave room in a small cave and in the Grimblade dojo at
  the new curve.** The waves are sized to the floor now (a 15x10 cave
  deals 4/5/6 at the shipped counter, the dojo 6/7/8); the density row is
  a first guess at "reasonable" and only play says whether 16 tiles per
  enemy at the bottom reads as sparse. The spawn audit measures tiles, not
  whether the fight feels right.
- **Clear one Boomerang cave chamber's gauntlet** while another chamber's
  miniboss is alive: the second wave should now come.
- **In-play confirmation that the Trilby boss now walks into the southwest.**
  The arena is measured; every behavioural probe failed on its own control.
- **A general playtest of the newly opened Minish rooms.** The MINISH model
  brought 50 rooms and 30 content sites back into the chain's reach. The gate
  sweep says all 258 policed transitions are clean, but that is a lot of
  newly exercised surface.
- **Play the two keys.** Find the Lon Lon Key, open the ranch house by either
  door and cross it; find the graveyard key, come through the maze and talk
  to Dampe at the gate. Every leg is measured in the emulator
  (`docs/QUICKSTART_ROADMAP.md`, "The two door keys"), none has been watched
  in play, and the keyed chain pair hangs a win step on them.
- **Bomb the Crenel fairy's wall and answer her honestly, in play.** The
  orchestrator that runs her script is kept now (it used to be deleted with
  every other cutscene orchestrator) and the payout function drops a RARE
  item in the emulator, but nobody has watched the whole vanilla question
  land in this build. Same for the Minish Woods fairy and her rupees.
- **Seven more guide-derived survey corrections await a walk each** -
  findings doc §1.2 lists the walk for every one.
- **Try `scenario.py` on a real save.** Start the game once so the
  emulator writes `tmc-d3.sav`, then `python3 tools/quickstart/scenario.py
  room AREA_ROYAL_VALLEY ROOM_ROYAL_VALLEY_MAIN 18 53 --sav tmc-d3.sav` and
  boot. Landing in Royal Valley proves the slot write and its checksum; the
  game calling the file corrupt means the arithmetic transcribed from
  `src/save.c` is wrong (the harness's mgba cannot attach a save to check
  it). `clear` afterwards - a scenario persists until cleared.
- **Load one scenario save.** `make_sav.py`'s layout is transcribed from
  `src/save.c` and self-verifies under `scenario.py show`, but no save it
  wrote has been loaded by the game (the harness's mgba cannot attach
  one). If file 1 shows up and starts in Castle Garden with the Big
  Octorok, every other file will too; if the file select is empty, try
  `--plain`, and if that fails too the checksum arithmetic is the suspect.
- **Play the blink memory pair.** Both rooms are measured end to end with
  forged strikes; what nobody has watched is the feel - whether a 48-frame
  blink with a dark beat reads as an order at a glance, whether the three
  switches sit where the player expects, and whether the sprite's lines
  land. `scenario.py site N MEMORY 0` (lesson) / `site N MEMORY 1`
  (recital) puts either room under test, in any site.
- **Watch for a wave that never clears in Castle Garden, Royal Valley,
  Castor Wilds, the Wind Ruins or Minish Woods.** The pull-to-centre
  failsafe is gone everywhere, and only Lake Hylia and Lon Lon Ranch were
  taken off the clear-challenge list; those five were neither on the
  user's safe list nor measurable (see the roadmap entry). A surviving
  enemy nobody can reach in one of them now stalls that region's reward
  and any chain WAVE step placed there. One line in
  `QuickStartRegionAllowsWave` retires the region.
- **Fight each boss with whatever sword a run gives you.** The any-blade
  fix is measured with the Four Sword from the test kit; the Smith's Sword
  was the one case that always worked. The chuchu's walk-home freeze is
  fixed by a timeout that has not been watched in play - if a chuchu ever
  stands still for longer than two seconds without hopping, that is the
  thing to report, with the room.
- **Play the carry quest.** `scenario.py quest CARRY CG --kit test` puts
  its giver in Castle Garden with the parcel in North Hyrule Field. Every
  leg is measured (`carry_probe.py`, 9/9) but the feel of carrying through
  a wave - the hit that drops it at your feet, the walk back for it - has
  not been watched.

- **The GFX budget tier fails for Lon Lon Ranch and North Hyrule Field**
  on the Veil Falls build: 1 and 0 free GFX slots at difficulty 4 against
  the floor of 2. Every seeded roll moved when the pool grew to nineteen
  rows, so this is one seed's population, not a Veil Falls change - but
  `QuickStartEnforceGfxReserve` is supposed to hold the floor whatever the
  roll, and here it did not. Nobody has looked at which sheets fill the
  table on that seed.
- **The spawn audit tags one tile in two Veil Falls rooms as solid.** The
  Top screen's (14,4) is floor by every map (collision 0, act 0) and its
  open top row is tagged RIM: the audit's known noise. The 1F hallway's
  (11,4) is collision 0 but act 0x10, WATER - one body of each of three
  waves was dealt into the hallway's pool. The gauntlet placer treats
  water as open; whether a land enemy dealt there can act is unmeasured.

### Design decisions waiting on a call

- **The redesign plan's open decisions** (`docs/QUICKSTART_REDESIGN_PLAN.md`
  §11): which six puzzle kinds first, dungeons as regions or as steps, the
  hub's shape. P0 of that plan (the element draw from reach, the completion
  audit probe, the keyed step's fallback payout) needs no decision and is
  the next work.

- **Drops are per pool row, not per region**: Eastern Hills and Western
  Wood take 20% of drops each. Draw a region first, then one of its rows,
  if "any region, evenly" is the intent.
- **The Wind Ruins' pool row lands in a room the reach model has no row
  for** (`RUINS/ENTRANCE`), and its other two rooms are priced "never",
  so the chain can never place anything in the Ruins' own rooms. The
  Ruins want a walk (their entrance stamp is mid-transition too).
- **Four Mount Crenel cave sites have no survey row** (fairy fountain,
  chuchu pot chest, spiny chu puzzle, water heart piece) and so can never
  host a requirement.

- **The `ITEM` chain step** fires as the first half of the keyed pair: find
  a key (one of four since the golden gates), then clear what it locks. The
  user settled the odds after the third simulation pass: one key per roll,
  round-robin from the step, one roll in ten (`QUICKSTART_CHAIN_PAIR_MOD`).
  See the roadmap entry "The keyed pair, round-robin" for the measured
  rates.
- **Royal Valley is near-dead content.** With its real entry price (bombs AND
  Power Bracelets) it is reachable in 7% of runs and hosts 0.2% of
  requirements. A whole region with a graveyard, a maze and a dojo that most
  runs never see. The lever is the toll or a second route in. **A cheaper
  lever surfaced from the vanilla guide:** the forest maze is a fixed
  six-move path and the lantern only reads the signs - retire the untestable
  `MAZE` token and have Ezlo speak the path (findings doc §1.2).
- **Port vanilla quests as a fifth quest sibling?** Assessed in
  `docs/QUICKSTART_GUIDE_FINDINGS.md` §6: eleven port cleanly (the courier
  family is seven of them), six need surgery, the rest are Hyrule Town. Two
  blockers to decide first: the mode has spent most `ITEM_QST_*` ids as
  charms, and `QuickStartIsOurNpc` deletes every non-ZELDA face. Recommended
  first three: the courier, Gregal's ghost, Percy's Monster Lady.
- **Make `FUSION` a testable token.** Eighteen survey rows and 41 live fusers,
  and the placer can satisfy none of them because `QS_REACH_FUSION` has no
  run-time test - yet `gSave.kinstones.fusedKinstones` records every open
  gate. Findings doc §1.3.
- **8 rooms and 18 content sites are still never reachable.** Down from 58
  and 48. Worth a pass to see which are genuine and which are survey gaps.
- **Mount Crenel's spawn area is a 69-tile entrance strip** of an 831-tile
  room. The rest is reached only by leaving through a cave and coming back
  out. Expanding it needs either per-cave kit gating on the extra spots, or
  scoping the wave-clear test to the player's own component. Less urgent now
  that Crenel waves pay nothing.

### Straightforward work, not started

- **P2 and P3 of the redesign** (`docs/QUICKSTART_REDESIGN_PLAN.md` §11,
  sized there): the performance census in the Boomerang cave, Trilby's
  push-stone cave and Lon Lon; Hyrule Town as a locked monster plaza;
  blessing tiers with recoloured sprites; the six puzzle kinds with solver
  probes; the three quest ports; the hub (travel, inn, trophy sprites);
  the dungeon reach probe, per-run small keys, Deepwood and the Cave of
  Flames as regions, the castle. P0, P1 and the seashells are shipped.
- **The chain-end probe's own limits** (`chain_end_probe.py`): an ITEM
  step is paid by the first clear of a region the probe can warp to; the
  warp from an interior straight to a field room is refused; and on seed 2
  a prompt the probe answers with A quits the run to the title at its
  second step (a screenshot showed the title; which prompt it was is the
  next thing to find - `dismiss` already backs out of Ezlo's talk state
  with B). Two of five seeds run to the finale; `win_probe.py` covers the
  finale itself 6/6.
- **The Boomerang chamber's fairy and NPC cells** (`chain_audit.py`: sites
  4, 6, 8 FAIRY and 5, 6, 8 NPC, plus Trilby's site 14 NPC) still read FAIL
  or LEFT. The game side is believed right (site 5's item-drop fallback
  completes when the player stands on the spot, measured by hand); the
  audit's driver cannot reach a fairy that wanders over the chamber's
  pits or stand below a spot at a ladder's top. A driver that climbs the
  ladders, or a walk by the user, settles it.
- **The step roll costs about 10 frames** (`QuickStartChainEventOk` walks
  the 629 reach rows per site). It no longer freezes the game for seconds
  - the memory-pair test is asked only for reachable sites now - but a
  per-site index into `sQuickStartReachDests` would make it free.

- **`MINISH_CAVES/BEAN_PESTO`** should be filled with tough enemies rather
  than used as a general-purpose ? room. The user asked for this a while ago;
  it is recorded and never actioned.
- **Cross-component drop sites** - dropping the player on either side of a
  bombable wall to vary the route. Needs a per-component exit analysis first
  so a bomb-less run is never stranded.
- **`boss_region.py`'s engagement detection has drifted** - see
  `HANDOFF_ISSUES.md`. It is the tool the boss allowlist depends on, so it
  should be repaired before any new region is vetted for bosses.
- **The entitlement half of the meta loop.** `QUICKSTART_UNLOCKS_ENABLED` is
  0. The catalog, the score and the trophy case all exist; what is missing is
  gating content on cross-run benchmarks.
- **Sweep the dead switch-puzzle helpers** (`QuickStartGateReadTimer`,
  `GateWriteTimer`, `GateRingPots`, `GateClose`, `GateOpen`,
  `GatePlateSpot`, `GateWindowFor`, `SpawnPuzzlePlate`, the decoy role
  byte) - unreferenced since the gate site was retired; agbcc does not
  warn on them.
- **The testbed's in-hub console** (`docs/QUICKSTART_CARRY_AND_TESTBED.md`
  sec 2.3, second door): a ZELDA-faced picker behind a `QUICKSTART_TESTBED`
  define, for scenarios on a cart with no cable. The save bytes and every
  override already exist; the console is only a script that writes them.

### Known-stale tooling

- **`boss_region.py` / `boss_arena.py` do not list Veil Falls** and need
  not: the region hosts no boss (`QuickStartRegionAllowsBoss`). If that
  changes, the plateau is 68 tiles and the Top screen 114.

- **Collision floods are blind to ledges and one-way drops**, and the
  boulder probe's Lon Lon partition shows it: the E445 landing reaches
  nothing but its own border, where the walk reaches the whole north
  field. Read `boulder_probe.py`'s tables as "what collision alone
  allows", never as the walk.
- **`chain_probe.py` still reads the old region-mask API** (its own
  `reachable_regions`); the ROM's flood is per node now
  (`QuickStartReachTestRoom` / `QuickStartReachTestRegions`). Oct 2026: its
  hand-copied adjacency gained Veil Falls and its pool list is read from
  the simulator, but it dies at `G.RING['SHF@NNE']` - it indexes the
  survey by region and the survey is keyed by entrance now. Rewriting its
  reach half on `sim.reachable_nodes` is the fix; until then
  `sim_validate.py` is the reach check and `scenario_probe.py` the chain
  check.
- **`spawn_audit.py` cannot tell a neighbour chamber's event from a
  spill** in the three multi-site rooms (Boomerang cave, Trilby Highlands,
  Goron Cave main), and counts Mount Crenel's ambient region waves as the
  site's. Its VOID tag there is noise; read the per-room map it writes.
- **`chain_probe.py`'s reach model predates the MINISH model.** It runs
  again (the chain's payout removal unblocked its forced steps) but calls
  Minish-house sites "UNREACHABLE" that the ROM places inside reach;
  `sim_validate.py` (402/402) is the authoritative reach check. Its
  verdicts on EVENT steps at sites 29 and 37 are noise until it learns
  the MINISH tokens.

`plates_check.py` and `los_check.py` both carry headers saying which of their
legs no longer measure anything. Do not trust them without reading those
headers first.

---

## Where the authoritative records live

| file | what it is |
|---|---|
| `docs/QUICKSTART_ROADMAP.md` | The real history. Sections: 1 vision, 2 outstanding features, 3 known bugs, 4 vanilla behaviours, 5 everything else (**the numbered doctrine list lives here**). |
| `docs/QUICKSTART_SIM_REPORT.md` | The simulation study and its corrections. |
| `docs/QUICKSTART_CARRY_AND_TESTBED.md` | Two designs, not yet built: the item-carry quest (carry token + rebuild on arrival) and the scenario-in-the-save feature testbed. |
| `docs/QUICKSTART_GUIDE_FINDINGS.md` | The vanilla walkthrough read against the survey: applied and proposed reach corrections, the Veil Falls / castle / dungeon maps, mechanics to re-purpose, the quest-porting assessment. |
| `docs/QUICKSTART_TRAVERSAL_AUDIT.md`, `docs/quickstart_traversal.json` | What the world graph does and does not know. |
| `docs/QUICKSTART_RETARGETS.md` | Door retargeting table. |
| `tools/quickstart/README.md` | The probe inventory. |
