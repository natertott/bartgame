# 10. Tooling and testing

QUICKSTART's tooling is about 150 Python scripts in `tools/quickstart/`
that drive the real ROM in mGBA (`tools/quickstart/README.md` is the
inventory). It is the project's biggest asset and its biggest source of
false findings. Copy the core library into the new game on day one.

## The core library

| module | what it gives you |
|---|---|
| `emu.py` | boot a ROM in mGBA's Python bindings, `run_frame`, `press`, `warp(c, area, room, x, y)`, `here(c)` (area and room), `entities(c, kind, id)`, `coll_at`, `act_at`, `room_dims`, `r16`/`w16`, `snap` (PNG screenshot), `poison_here` |
| `callrom.py` | **call a function inside the running ROM and read r0.** Parks the target in r3, executes `bx r3`, clears IME for the call. Static functions resolve from `nm build/USA/src/game.o` plus the `.text` base read from the current map file. One question per boot: the call clobbers the context |
| `parse_tables.py` | the game's own tables parsed from source and the build's generated enums (`build/USA/enum_include/*.inc`): areas, rooms, items, pool, sites, fusers, tiers |
| `scenario.py` | the **testbed**: writes 8 bytes into the save so the next boot skips the hub, grants a kit, pins the difficulty and lands in one room with one feature dealt. No rebuild |
| `chain_audit.py` | `dismiss(c)`: clears message boxes so a probe can keep walking |

Key addresses the probes use (`emu.py`):

| symbol | address |
|---|---|
| room controls | 0x03000bf0 |
| player | 0x03001160 |
| entities | 0x030015a0, stride 0x88, 72 of them |
| bottom collision | 0x02025eb0 + 0x2004 |
| save flags | 0x02002a40 + 0x25C |

## The probe shape

Every probe in the repo has the same form (see `castle_probe.py`,
`well_probe.py`):

```python
res = []
def check(name, ok, detail=''):
    res.append(bool(ok))
    print('%s %-52s %s' % ('PASS' if ok else 'FAIL', name, detail))

c = S.boot(ROM, S.KINDS['ROOM'], a=area, b=room, c=x // 16, d=y // 16, kit=2, frames=300)
...walk, warp, call, read...
check('WALKS: entrance hall -> ring hall', got == want, 'from %s to %s' % (start, got))
print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
```

Named checks, a detail string with the measured values, and a RESULT line
with a count. A probe walks with real input (`set_keys`, then run frames
until the room changes) rather than writing positions, wherever the
question is about movement. "Is this door reachable" is answered by
walking through it.

## What to build for the new game

| tool | job |
|---|---|
| a scenario boot | boot straight into (seed, area, room) with a kit. The first thing to build |
| `gen_dump.py` | call the ROM generator for a seed and dump the graph and both layers' tiles |
| `gen_twin.py` | the Python twin of the generator (`07_PROCGEN_DESIGN.md` §5) |
| `gen_equiv.py` | the ROM against the twin, byte for byte, over hundreds of seeds |
| `gen_sweep.py` | 100,000 seeds in the twin: solvability, lengths, budgets, archetype mix |
| `area_shot.py` | a PNG of a whole generated area (extend `room_shot.py`, which stitches screenshots of a room) |
| `walk_graph.py` | walk every edge of a generated area in the ROM, both directions, with real input |
| `gfx_floor.py`, `cpu_probe.py`, `pc_profile.py` | the budgets, per area theme |
| an invariant sweep | the broad regression run after anything non-trivial |

## Generated files

QUICKSTART keeps two generated artefacts, each with a `--check` mode:

| generated | generator |
|---|---|
| `include/quickstart/reach.h` | `gen_reach.py` from `world_reach.py` |
| `sQuickStartDifficultyTiers` | `tier_curve.py` |

**Never hand-edit a generated table.** Give the new game the same rule
for stamp libraries, puzzle pools and tier tables.

**Trap: `build/` is not kept**, so a generator that reads build output
cannot run from a clean checkout. Make generators read sources.

## Doctrine (from `docs/QUICKSTART_ROADMAP.md` §5 and `docs/HANDOFF.md`)

Each rule was written after a specific failure.

1. **Tables are the game.** The invariant checker validates the tables.
   Run it after every build that touches placement data.
2. **Runtime self-correction stays on** (snap to open ground, rescue
   failsafes), so a bad row degrades instead of breaking.
3. **Measured docs are the source of truth for placement.** Guessed
   coordinates do not go into tables.
4. **Humans test feel, machines test truth.** Probes verify state and
   transitions. Seeded playtests judge fairness and fun.
5. **The hard limits keep plans honest**: 72 entities, the GFX table is
   the wall, new logic over existing assets is cheap while new graphics,
   maps and AI are expensive.
6. **Borrowed objects are only as portable as their art.**
7. **A collision flood cannot see a ledge.**
8. **A probe that finds nothing has proven nothing until a control says
   otherwise.** Point the same probe at a case known to work. If the
   control fails too, the finding is about the probe. Positives stand
   alone. Only negatives need the control. *The highest-value rule in the
   project. It has caught at least six false findings.*
9. **Fix the vanilla mechanism. Do not replace it.**
10. **You can ask the ROM directly.** `callrom.py`. Re-implementing a rule
    in Python tests the copy, not the game.
11. **A probe that forces state can go stale silently.** Encodings change
    underneath it and it keeps returning plausible answers.
    `scenario_probe.py`'s carry check still hosts the carry quest in a room
    that no longer has a carry pair, so it fails on every build.
12. **Ids come from the build, never from a regex over the header.**
13. **A table's comment can be wrong about geography.**
14. **When a fix makes a checker pass, ask whether it was passing for the
    right reason before.** Lon Lon Ranch's GFX floor passed for years only
    because its fuser face was broken and loaded no sheet.

## Harness traps

- **mGBA's bindings refuse to write r15.** `callrom.py` works around it.
- **Teleporting the player onto a hole lets `RespawnPlayer` answer
  first.** Set position and action in the same frame (`well_probe.py`
  `fall_in`).
- **Seeds shift wave draws**, and a probe that assumes 60 fps breaks when
  a heavy kind is drawn. Pin what the probe does not test.
- **A build can be a hybrid**: objects whose source changes with a
  variant flag are reused across variants unless deleted
  (`VARIANT_OBJS`). One shipping ROM once carried the testkit's `game.o`.
- **`invariant_check.py` takes about 30 minutes.** Redirect it to a file
  and run it in the background.
- **Keep a baseline.** Run the sweeps before your first change and keep the
  output. Several "regressions" were conditions that predated the change.

## Working with the user

From `docs/HANDOFF.md`: the user is a strong reviewer, and when they pushed
back they were right. They overturned three of four headline findings in
one report, from having played the game. **Prefer another measurement to
another question.** Ask only when the answer changes what gets built: a
design trade-off, a mechanic change, a risk to completability. The user
said "Try again" to an agent that asked them to settle a contradiction the
agent could have measured. Two more measurement passes found the real
mechanism.

They prefer shell tooling (`cat`, `sed`, `grep`, heredocs) over dedicated
file tools where either works.
