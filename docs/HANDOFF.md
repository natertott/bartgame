# Handoff: read this first

Written Sep 2026 at commit `61bf9d3` for the agent taking over this work.

| file | what it answers |
|---|---|
| **`HANDOFF.md`** (this) | How to work here. Constraints, build, tooling, doctrine. |
| **`HANDOFF_GAME.md`** | What the game is, how it plays, the long-term vision. |
| **`HANDOFF_STATUS.md`** | What is built, what is outstanding, which roadmap entry to read. |
| **`HANDOFF_ISSUES.md`** | Known bugs, recurring traps, and which probes are lying to you. |

The authoritative record is `docs/QUICKSTART_ROADMAP.md` (~4,700 lines). It
is written as narrative batch entries that explain what was measured and what
was got *wrong* on the way, which is usually the more useful half. **Before
touching an area, read its roadmap entry.** These four files tell you which
entry to look for; they do not replace it.

---

## Standing instructions from the user

These are durable. Treat them as still in force unless the user says
otherwise.

- **Deliver the difficulty-3 ROM only.** `make quickstart-d3`. Do not hand
  over other difficulty builds.
- **Only vanilla door mechanics.** *"We should ONLY have vanilla door
  mechanics, no more of this teleporting/warping stuff."* When a door will
  not fire, the fix is the byte stopping it - an act tile, a collision value
  - never a trigger box layered on top. A position box that fires near a door
  is not a door: it takes the room away from the player.
- **Work on branch `claude/gba-fan-game-start-ptuvhn`.** Never push to
  another branch without explicit permission. Do not open a pull request
  unless asked.
- **Update the roadmap as features ship.** Every batch gets an entry, and the
  entry should record what was measured and what went wrong, not just what
  changed.
- **Commit trailers** are configured per session - check the session's own
  instructions rather than copying old ones.
- The user prefers work done through shell tooling (`cat`, `sed`, `grep`,
  heredocs) over dedicated file tools where either would do.

## Working agreement that has actually mattered

The user is a strong reviewer and **has been right every time they pushed
back.** In the last session they overturned three of four headline findings
in a research report, corrected two region entry prices, and corrected the
Minish portal model - each time from having played the game. When a
measurement contradicts them, the measurement is the thing to re-examine
first.

They said **"Try again"** once, to an agent that came back asking them to
confirm a contradiction instead of digging further. That was the right
correction: the contradiction was the agent's, and two more measurement
passes found the real mechanism. **Prefer another measurement over another
question.**

Do ask when the answer genuinely changes what gets built - a design
trade-off, a mechanic change, a risk to run-completability. Do not ask to
resolve something a probe can settle.

---

## Build

```
make quickstart-d3          # the shipped build; writes tmc.gba AND tmc-d3.gba
```

Roughly 3-6 minutes clean. The mod lives almost entirely in **`src/game.c`**
(~1.26 MB) behind `#ifdef QUICKSTART`, on top of an untouched decomp.

**Generated files - never hand-edit:**

| generated | generator | check |
|---|---|---|
| `include/quickstart/reach.h` | `tools/quickstart/gen_reach.py` from `world_reach.py` | `gen_reach.py --check` |
| `sQuickStartDifficultyTiers` in `game.c` | `tools/quickstart/tier_curve.py` | `tier_curve.py --check` |

Toolchain constraints are in `HANDOFF_ISSUES.md` §3. The one that costs the
most time: **no unsigned `%` by a runtime divisor** - it fails at link, not
compile, with `undefined reference to '__umodsi3'`.

---

## The tooling

`tools/quickstart/` holds ~60 Python probes that drive the real ROM in mGBA.
This is the project's biggest asset and its biggest source of false findings.
`tools/quickstart/README.md` is the inventory.

**The core library:**

- `emu.py` - boot, warp, press, here, entities, `coll_at`, `act_at`,
  `room_dims`, `r16`/`w16`, `snap` (PNG screenshot).
- `callrom.py` - **call a function inside the running ROM and read r0.**
  This beats re-implementing a rule in Python, which only ever tests the
  copy. Static functions come from `nm build/USA/src/game.o` plus the `.text`
  base. One question per boot.
- `parse_tables.py` - the game's own tables (areas, rooms, kinstones, content
  sites, region pool, fusers, tiers), parsed from source and the build's
  generated enums.

**The checkers you should run before claiming a change is done:**

| tool | what it proves | cost |
|---|---|---|
| `invariant_check.py` | The broad regression sweep. Run it for anything non-trivial. | ~30 min; redirect to a file |
| `survey_gate.py` | Walks the exit table and asks the containment gate from real doors, both directions. Catches rooms with no way in and one-way traps. | ~25 min |
| `sim_validate.py` | The Python reach model against the ROM's own `QuickStartReachRoomOk`. | ~5 min |
| `gfx_floor.py` | Free GFX slots per room per difficulty. **Run this after anything that adds a sprite or spreads spawns.** | ~1 min/room |
| `tier_curve.py --check` | The difficulty table matches its generator. | instant |
| `gen_reach.py --check` | `reach.h` matches the survey. | instant |

**Analysis tools worth knowing:** `sim.py` (100k runs in ~2 min),
`sim_report.py`, `spawn_spread.py` (spawn coverage, `--map` prints an ASCII
coverage map), `minish_portals.py`, `guide_reach.py` (Veil Falls, the
castle, the Cloud Tops and every dungeon mapped from the vanilla
walkthrough - feeds nothing, `--summary` shows how clone-gated each dungeon
is; see `docs/QUICKSTART_GUIDE_FINDINGS.md`), `component_map.py` (ledge-aware
components - slow), `tier_mix.py` (what levels actually spawn),
`fuser_faces.py` (renders each NPC face to PNG), `drop_spots.py`,
`boss_region.py` / `boss_arena.py` (**currently drifted** - see
`HANDOFF_ISSUES.md`).

---

## Doctrine

Twelve numbered rules live in section 5 of the roadmap, each written after a
specific failure. The ones that recur most:

**8. A probe that finds nothing has proven nothing until a control says
otherwise.** Point the same probe at a case known to work. If the control
fails too, the finding is about the probe. Positives stand alone; only
negatives need the control. *This is the single highest-value rule in the
project and it has caught at least six false findings.*

**10. You can ask the ROM directly.** `callrom.py`. Re-implementing a rule in
Python and checking the re-implementation tests the copy, not the game.

**9. Fix the vanilla mechanism; do not replace it.**

**7. A collision flood cannot see a ledge.** It finds components correctly
and then lies about how they connect.

**6. Borrowed vanilla objects are only as portable as their art.** An object
that paints into the room's TILEMAP works only in tilesets carrying those
tiles; one that carries an entity SPRITE renders anywhere.

**11. A probe that forces state can go stale silently.** Encodings change
underneath probes and they keep returning plausible answers.

**12. Ids come from the build, never from a regex over the header.**

Two more worth adding from the most recent session:

**13. A table's comment can be wrong about geography.** "The southwest
pocket" named the mid-west pocket in two independent places and caused two
separate bugs. Check positional names against a map.

**14. When a fix makes a checker pass, ask whether the checker was passing
for the right reason before.** Lon Lon Ranch's GFX floor passed for years
only because its fuser face was *broken* and loaded no sheet. Fixing the face
"caused" a failure that was really a pre-existing condition being exposed.

---

## Orientation: the files that matter

```
src/game.c                          the mod, ~1.26 MB, all of it
include/quickstart/reach.h          GENERATED reachability tables
tools/quickstart/world_reach.py     the walked survey - source of truth
tools/quickstart/gen_reach.py       compiles the survey to reach.h
tools/quickstart/tier_curve.py      generates the difficulty table
docs/QUICKSTART_ROADMAP.md          the real history (read the relevant entry)
docs/QUICKSTART_SIM_REPORT.md       the simulation study
docs/sim/                           its charts
```

Key functions to know by name, all in `src/game.c`:

- `QuickStartChainRollStep` / `QuickStartChainStore` - the win chain placer.
- `QuickStartReachableRegions` / `QuickStartReachRoomOk` / `QuickStartReachPoolOk`
  - the reach model. Note the third only asks "can the player be inside this
  region", which is not the same as "can they explore it".
- `QuickStartRegionAllowsBoss` / `QuickStartRegionAllowsWave` - per-region
  content allowlists.
- `QuickStartIsPocketInteriorRoom` - the "blessing" table. A room must be
  blessed or the containment sweep cancels transitions into it, which looks
  from the player's side like falling into a hole and landing nowhere.
- `QuickStartRoomEnemyCeiling` - now prices against the GFX table.
- `QuickStartSpawnRegionRewardOnce` - the region clear reward, and the only
  path that can hand over a key item.

---

## If you do only one thing before your first change

Run `invariant_check.py` and `gfx_floor.py --all` on the current build and
keep the output. They are your baseline. Several "regressions" in this
project's history were pre-existing conditions that nobody had a baseline
for, and one of them cost most of a session.
