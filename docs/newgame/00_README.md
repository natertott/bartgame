# New game handoff: read this first

Written Oct 2026, on branch `claude/gba-fan-game-start-ptuvhn`, for the agent
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

The new game inverts that. The engine and its rules stay. The map is
generated. The art is new.

## The recommended starting point

**Fork the decomp. Keep its engine code. Replace its world data and art.**
Do not rewrite the engine from scratch.

| option | cost | what you get |
|---|---|---|
| Fork the decomp, keep the code, replace data (recommended) | low | every mechanic exactly as shipped, already proven at 60 fps |
| Rewrite an engine in C to match the mechanics | very high | years of re-deriving physics, collision and 100 enemy AIs by hand |
| Port QUICKSTART as-is and bolt on generation | medium | 1.26 MB of overworld-specific code you will mostly delete |

"Exact mechanics" is only cheap one way. Player physics, the collision
matrix, 103 enemy AIs and 192 object kinds are already C, already match the
original, and already run. What has to be new is the world data pipeline,
the generator and the art.

QUICKSTART's mode code is a **reference, not a base.** Its systems are
the design vocabulary the new game inherits: waves, ? rooms, the win
chain, quests, puzzles, the reach model and the budgets. But they are
written against fixed vanilla rooms. Lift the ideas and the tables. Lift
code only where it is room-independent.

## Reading order

| file | what it answers |
|---|---|
| `00_README.md` (this) | what the new game is, the starting point, the reading order |
| `01_ENGINE_ARCHITECTURE.md` | build, toolchain, memory map, main loop, tasks, RNG, scripts, text, sound, save |
| `02_PLAYER_AND_MOVEMENT.md` | player state machine, flags, speeds, physics, items in hand, falls, transitions |
| `03_WORLD_TILES_COLLISION.md` | map format, layers, tile types, collision bytes, act tiles, rooms, areas, exits, the load pipeline, **where a generator plugs in** |
| `04_ENTITIES_ENEMIES_OBJECTS.md` | entity struct and limits, enemy definitions, the damage matrix, the enemy roster, objects, NPCs, managers |
| `05_ITEMS_AND_ECONOMY.md` | items, the tier table, kinstones and fusers, charms, shop |
| `06_CURRENT_GAME_DESIGN.md` | QUICKSTART's run loop: hub, regions, waves, ? rooms, chain, quests, difficulty |
| `07_PROCGEN_DESIGN.md` | **the core deliverable**: how to generate areas, puzzles and gates, what QUICKSTART learned, a recommended architecture |
| `08_PERFORMANCE.md` | measured budgets: CPU, entities, GFX slots, palettes, audio; how to get "max enemies" |
| `09_ASSETS_AND_RESKIN.md` | the asset pipeline and formats; how to replace every Nintendo asset |
| `10_TOOLING_AND_TESTING.md` | the emulator harness, calling ROM functions, scenario boots, probes, doctrine |
| `11_TRAPS.md` | every trap that has cost a session, in one list |

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
