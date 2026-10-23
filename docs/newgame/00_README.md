# New game handoff: read this first

Written Oct 2026 and revised for a from-scratch engine, on branch `claude/gba-fan-game-start-ptuvhn`, for the agent
who builds the new game.

## What the new game is

The user's brief, in their words:

> A brand new game that follows the exact mechanics of this game except it
> uses its own sprites and map. A central hub, and then 9 different areas
> that are procedurally generated each time. The map itself is a puzzle
> that the player has to navigate to find certain areas/items, complete
> specific quests, etc. The key change is a procedural way of generating
> interesting maps/puzzles/layouts. Same player mechanics, movement
> mechanics, collisions, tile types, enemies, items. Re-skin the Minish Cap
> with new sprites and start from the ground up on the map itself.
> Optimized to run on Game Boy Advance for max performance: max enemies,
> events, graphics.

## What this repo is

This repo is `zeldaret/tmc`, the matching decompilation of *The Legend of
Zelda: The Minish Cap* (USA). On top of it sits **QUICKSTART**, a roguelite
mod. QUICKSTART keeps Nintendo's overworld exactly as drawn and randomizes
what happens in each room. Almost all of it lives in `src/game.c` (about
1.26 MB) behind `#ifdef QUICKSTART`.

The new game keeps TMC's rules and nothing else. The engine is new, the
map is generated, the art is new.

## The starting point: a new engine that plays like TMC

**The user's decision: the new agent builds the engine from scratch.** It
must play like TMC: the controls, player and enemy speeds, the bounce, the
roll, fire rates, knockback. And it must be built for the highest
performance the GBA allows, with a much higher ceiling than TMC for
on-screen enemies, sprites, animations and content.

**Read `12_FROM_SCRATCH_ENGINE.md` next.** It says what the new agent needs
from TMC (the feel spec, the behavior vocabulary, and TMC's measured
ceilings), what it can ignore (TMC's formats, structs, load pipeline,
scripts, sound engine and toolchain), and gives a high-performance engine
design with a cycle and memory budget.

The decomp stays useful as an **oracle**:

- readable C for every behavior to port: the player, 37 item files, 103
  enemy AIs,
- a running reference the Python harness can drive and measure,
- exact tables, extracted to `data/` by `tools/newgame/extract_feel.py`.

QUICKSTART's mode code is a **reference, not a base.** Its systems are
the design vocabulary the new game inherits: waves, ? rooms, the win
chain, quests, puzzles, the reach model and the budgets. Lift the ideas
and the tables, not the code.

## Reading order

| file | what it answers |
|---|---|
| `00_README.md` (this) | what the new game is, the starting point, the reading order |
| **`12_FROM_SCRATCH_ENGINE.md`** | **read second.** What to take from TMC and what to leave. The feel spec with exact numbers. TMC's ceilings and the engine design that beats them |
| `01_ENGINE_ARCHITECTURE.md` | reference: how TMC's engine is built (memory map, main loop, RNG, scripts, text, sound, save) |
| `02_PLAYER_AND_MOVEMENT.md` | spec: the player's states, speeds, physics, surfaces, ledges, falls, items |
| `03_WORLD_TILES_COLLISION.md` | spec: tile behaviors, collision shapes, act tiles, the area grid. Reference: TMC's formats and load pipeline |
| `04_ENTITIES_ENEMIES_OBJECTS.md` | spec: the enemy roster, the damage matrix, the object vocabulary. TMC's limits, to beat |
| `05_ITEMS_AND_ECONOMY.md` | items, the tier table, kinstones and fusers, charms, shop |
| `06_CURRENT_GAME_DESIGN.md` | QUICKSTART's run loop: hub, regions, waves, ? rooms, chain, quests, difficulty |
| `07_PROCGEN_DESIGN.md` | **the core deliverable**: how to generate areas, puzzles and gates, what QUICKSTART learned, a recommended architecture |
| `08_PERFORMANCE.md` | TMC's measured walls: CPU, entities, GFX slots, palettes, audio |
| `09_ASSETS_AND_RESKIN.md` | reference: TMC's asset formats; what new art must preserve (animation cues, hitboxes, behavior ids) |
| `10_TOOLING_AND_TESTING.md` | the emulator harness, calling ROM functions, scenario boots, probes, doctrine |
| `11_TRAPS.md` | every trap that has cost a session, in one list |
| `data/` | `enemies.csv`, `hitboxes.csv`, `collision_matrix.csv`, `player_animations.csv`: TMC's mechanics as data |

## Existing docs worth reading next

These are the current game's own records. They are longer, narrative and
specific to QUICKSTART. Use them when a section here points at them.

| file | why |
|---|---|
| `docs/HANDOFF.md` | how this repo is worked: build, tooling, doctrine |
| `docs/HANDOFF_GAME.md` | what QUICKSTART is |
| `docs/HANDOFF_ISSUES.md` | hard engine limits and traps, §3-§5 |
| `docs/QUICKSTART_BUDGET.md` | the full GFX, palette and CPU budget study |
| `docs/QUICKSTART_BLOCK_PUZZLES.md` | a generator plus solver that produced 1,528 proven puzzles |
| `docs/QUICKSTART_LANTERN_GUST_EVENTS.md` | torches, darkness, webs and dust, measured |
| `docs/QUICKSTART_PORTAL_POCKETS.md` | pockets, one-way gates and escape items |
| `docs/QUICKSTART_HUB.md` | the hub, built from a vanilla staircase tower |
| `docs/QUICKSTART_ITEM_TIERS.md` | item categories and tiers |
| `docs/QUICKSTART_SIM_STUDY.md` | 100k-run simulation of reachability |
| `docs/QUICKSTART_ROADMAP.md` | 7,400 lines of history. §5 holds the doctrine |
| `tools/quickstart/README.md` | the inventory of about 150 probe scripts |

## Standing rules carried over from the user

These come from the current project. Ask the user before assuming any of
them still hold for the new game.

- **Only vanilla door mechanics.** No trigger boxes that teleport. When a
  door will not fire, fix the byte that stops it: the act tile or the
  collision value.
- **Measure with controls.** A probe that finds nothing has proven nothing
  until the same probe passes on a case known to work.
- **Fix the vanilla mechanism; do not replace it.**
- **Every fix is a general mechanism, never a per-room special case.** This
  matters even more for procgen. A special case cannot exist in a room that
  was never authored.
- **The roadmap records what was measured and what went wrong**, not only
  what changed.
- The user is a strong reviewer, and when they pushed back they were right.
  When a measurement contradicts what they saw in play, re-examine the
  measurement first.

## Glossary

| term | meaning |
|---|---|
| tile / metatile | 16x16 px map cell, made of four 8x8 subtiles |
| subtile | 8x8 px GBA hardware tile, 4bpp |
| tile index | entry in the room's tileset, 0-2047. 0x4000+ marks a special tile |
| tile type | what a tile *is* (bush, grass, torch). Indexes the collision and act tile LUTs |
| collision byte | per-tile solidity: 0 open, 0x01-0x0F quadrant mask, 0x10+ shape, 0xFF special |
| act tile | per-tile behavior: water, pit, ladder, door, ice and so on |
| area / room | an area holds rooms on one shared pixel grid. A room is at most 64x64 tiles |
| exit list | per-room table of `Transition`s: borders and door boxes |
| GFX slot | 0x200-byte OBJ VRAM block. 44 exist and they are the real enemy limit |
| manager | invisible logic entity, kind 9, from a separate pool of 32 |
| region | QUICKSTART's unit of world: one or more rooms with waves and content |
| ? room | a content site where QUICKSTART deals an event |
| chain | QUICKSTART's win condition: N requirements dealt one at a time |
| reach token | a fact the player needs to get somewhere: an item, or world state like `maze_solved` |
