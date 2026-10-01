# Status: what is built, what is not

Companion to `HANDOFF_GAME.md`. This is a **summary** of
`docs/QUICKSTART_ROADMAP.md`, which is ~4,700 lines and is the real record -
every batch entry there explains not just what changed but what was measured
and what was got wrong on the way. Read the roadmap entry for any area you
are about to touch; this file tells you which entry to look for.

Current head when this was written: **`61bf9d3`**, branch
`claude/gba-fan-game-start-ptuvhn`.

---

## Built and probe-verified

**The run loop, end to end.** Hub with three selection rounds, shop, trophy
case, inn rest, wandering hint NPCs; the sky drop with per-region landing
spots and kit-aware re-rolls; a 13-region free-roam ring walked on foot; a
five-step win chain; the Earth Element hunt; win and reset.

**Combat.** Six enemy tiers covering 57 of the game's 102 enemy ids; ten
composition archetypes; per-family live caps; a size-normalised difficulty
curve over 13 steps; an Elites tier that doubles as the miniboss pool; weapon
gating for enemies a sword cannot kill; two bosses (ChuChu, Big Octorok) with
a vetted per-region allowlist.

**Content systems.** Three "? room" systems with nine event kinds; 105
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

---

## Outstanding

### Needs the user, not an agent

- **In-play confirmation that the Trilby boss now walks into the southwest.**
  The arena is measured; every behavioural probe failed on its own control.
- **A general playtest of the newly opened Minish rooms.** The MINISH model
  brought 50 rooms and 30 content sites back into the chain's reach. The gate
  sweep says all 258 policed transitions are clean, but that is a lot of
  newly exercised surface.
- **Ride the leaves to Minish Village without the Flippers, in the shipped
  d3 ROM.** The vanilla walkthrough and `lilypadSmall.c` both say the crossing
  is free, so the survey dropped the Flippers from fourteen Minish Woods rows
  and the village's own price (Oct 2026). If the leaves do not carry a Minish
  player in this build, a chain step in the village is a stranded run.
  `docs/QUICKSTART_GUIDE_FINDINGS.md` §1.1.
- **Seven more guide-derived survey corrections await a walk each** -
  findings doc §1.2 lists the walk for every one.

### Design decisions waiting on a call

- **The `ITEM` chain step never fires.** 0 times in 500,000 requirement
  rolls. It is the chain's only *guaranteed* item grant; everything the
  region clear pays is a 64-way draw that might be a bottle. Either force one
  into the chain or accept that growth runs through the loot table and retire
  the branch.
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

### Known-stale tooling

`plates_check.py` and `los_check.py` both carry headers saying which of their
legs no longer measure anything. Do not trust them without reading those
headers first.

---

## Where the authoritative records live

| file | what it is |
|---|---|
| `docs/QUICKSTART_ROADMAP.md` | The real history. Sections: 1 vision, 2 outstanding features, 3 known bugs, 4 vanilla behaviours, 5 everything else (**the numbered doctrine list lives here**). |
| `docs/QUICKSTART_SIM_REPORT.md` | The simulation study and its corrections. |
| `docs/QUICKSTART_GUIDE_FINDINGS.md` | The vanilla walkthrough read against the survey: applied and proposed reach corrections, the Veil Falls / castle / dungeon maps, mechanics to re-purpose, the quest-porting assessment. |
| `docs/QUICKSTART_TRAVERSAL_AUDIT.md`, `docs/quickstart_traversal.json` | What the world graph does and does not know. |
| `docs/QUICKSTART_RETARGETS.md` | Door retargeting table. |
| `tools/quickstart/README.md` | The probe inventory. |
