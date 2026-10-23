# 07. Procedural generation: design, lessons, and a recommended architecture

This is the new work. Nothing here exists yet as code. What exists is
QUICKSTART's experience with three related problems:

- deciding where things can go given what the player holds (the reach
  model),
- generating puzzles that are always solvable (block puzzles),
- placing content in rooms nobody authored for it (spawn sampling,
  predicates, surveys).

Each of these taught specific lessons, and they are written into the
design below.

## 1. Goals, as constraints

| goal | constraint it puts on the generator |
|---|---|
| "the map itself is a puzzle" | the area is a **lock-and-key graph**, not a maze of corridors. Getting somewhere must need thought or an item |
| nine areas, generated each run | deterministic from a seed, fast enough to run during a fade |
| same mechanics as Minish Cap | gates are vanilla verbs: bombable walls, dark rooms, deep water, climb walls, ledges, blocks, switches, keys, fusions |
| find areas and items, complete quests | goals are graph nodes. Quests and ? rooms are node decorations |
| max performance on GBA | rooms are built from stamps and tile types into the existing `MapLayer` arrays. No second map copy. Generation is O(tiles) |
| always completable | **solvable by construction, then verified**. Never ship a seed that was not checked |

## 2. The vocabulary: tokens

Take this straight from `tools/quickstart/world_reach.py`. **A requirement
is a set of facts that must hold**, and items and world state are both
facts:

```
sword  bombs  bow  boomerang  lantern  gust  pacci  mitts  cape  boots
grip  bracelets  flippers  firerod  rockbreaker  spin
key:<area>:<n>     a small key, counted
switch:<id>        a switch thrown somewhere else
fusion:<id>        a kinstone fusion done
solved:<id>        a puzzle solved
boss:<area>        the area's boss down
```

"Holds the Flippers" and "boulder 1 is in its hole" are the same kind of
fact. Keeping them in one vocabulary is what lets a single filler place
"solve this maze" as a step, not as a special case.

**Edges carry requirements. Nodes carry rewards.** A room is reachable
when some path to it has every edge's requirement satisfied by the tokens
collected before it.

## 3. The architecture

```
run_seed
  └── hub (authored)
  └── area_seed[i] = hash(run_seed, i)       i = 0..8
         │
         ├── A. mission graph   which goals, keys and locks, in what order
         ├── B. space graph     rooms on the area grid, edges = borders and doors
         ├── C. room layouts    tiles from stamps and rules, per room
         ├── D. placement       chests, puzzles, spawns, landings, NPCs
         └── E. verification   flood with tokens, puzzle solvers, budgets
                 └── fail → reseed (bounded), else fallback layout
```

Generate the **graph** for all nine areas at run start. It is small:
tens of bytes per room. Generate **room tiles** on room load from the
room's own seed. Never store full maps.

### A. The mission graph (per area)

A directed graph of what the player must do: get the key, open the door,
light the room, push the block, beat the guardian, take the prize.
Build it **backwards from the goal** ("lock and key" grammar, as in
Dormans' mission/space split and in randomizer forward-fill):

1. Start with `ENTRY -> GOAL`.
2. Pick a lock type allowed by this area's theme and the tokens the player
   is guaranteed to hold on entry. Insert `LOCK` before `GOAL` and a `KEY`
   somewhere before `LOCK`.
3. Recurse into the segment between `ENTRY` and `KEY`: maybe that key is
   itself behind a lock.
4. Add **optional branches**: side rewards behind locks the player cannot
   pass yet ("these should show up anyway as a reason to go find it").
5. Add **cycles**: a shortcut back to the entry that opens from the far
   side (a one-way door, a ledge, a block pushed from behind). Cycles
   are what make a map feel designed rather than a tree.

Each area has a **signature verb** taught there (a dark area teaches the
Lantern, a lake area the Flippers). The area's own key item should be
found early in it and used against its locks. The verb then gates
**optional** content in other areas. That is how nine areas become one
puzzle.

**QUICKSTART's hardest lesson applies here.** Its key items were meant to
arrive through a random `ITEM` chain step. That step **fired 0 times in
500,000 simulated rolls**, so the reachable world never grew. **Key items
must be placed by the generator as part of the mission graph**, in a
reachable spot, before any lock that needs them. Never leave progression
to a random draw.

### B. The space graph (rooms on the area grid)

Lay the mission onto rooms:

- An area is a grid of **cells**, one screen each (15x10 tiles, 240x160
  px). A room is a rectangle of 1x1 to 4x4 cells. That keeps every room
  within the 64x64 tile limit and lets neighbours join on shared edges.
- Mission nodes go into rooms. A lock becomes an **edge** between two rooms
  (a door, a bombable wall, a water channel), or a **feature inside a
  room** that splits it into components (a ledge, a gap, a block wall).
- Edges become `Transition`s. Rooms that touch in the grid join with a
  `WARP_TYPE_BORDER` across the shared span, which scrolls without a fade.
  Rooms that do not touch use doors (an AREA box over act 0x28 or 0x29,
  with a landing).
- **Record every one-way link as a directed edge**: a ledge, a hole, a
  one-way door. A flood fill over collision cannot see a ledge.
  QUICKSTART made two false "sealed pocket" calls this way.

A useful shape: **a hub-and-spoke area with one loop**. The entry is
central. Three or four spokes each end in a lock. One spoke holds the
area's key item. Its use opens the others. One spoke loops back.

### C. Room layout

Per room, from `room_seed = hash(area_seed, room_index)`:

1. **Frame**: the solid border, with gaps where edges exit. Edge
   positions are fixed by the space graph, so a neighbour's layout never
   needs to be known.
2. **Archetype**: pick a layout family for the room's role and theme:
   open field, corridor, island, ring, cliff terrace, maze, pillar hall,
   arena. Each archetype is a small rule set, not a picture.
3. **Carve**: lay floor where the archetype says, then **place stamps**
   (authored tile clusters: cliff runs with ledge tiles, water pools with
   shores, tree clumps, rock fields, ruins). Stamps are drawn from the
   area theme's library, with a footprint mask for collision and
   clearance.
4. **Join**: auto-tile the seams (cliff corners, shore edges, wall
   corners) from neighbour rules.
5. **Connectivity guard**: after every stamp, check that every required
   entry still reaches every required feature **with the tokens that edge
   is meant to require**. A stamp that cuts a path it should not is
   rejected and redrawn.
6. **Decorate**: grass, flowers, pots and bushes as filler. Bushes and
   grass are free cover. They are also soft gates (sword), and they hide
   things.

Write tile **types** through the theme's tileset `tileIndices`
(type to index). Then the vanilla pipeline derives collision and act tiles,
and the art can change without touching the generator.

### D. Placement

| placement | rule | lesson behind it |
|---|---|---|
| landings (every door's arrival point) | open dry land, plus a clear apron of 2-3 tiles, reserved before anything else is placed | puzzles over door landings read as solved on arrival |
| chests and prizes | on the component the mission graph says. Dry land, act not in {0x0d, 0x0e, 0x0f, 0x10, 0x12, 0x13} | walkable collision is not land: enemies were placed in a lake |
| enemy spawn spots | farthest-point sampling with 3x3 clearance over the **player's component** (`tools/quickstart/spawn_spread.py`) | a wave counts every enemy in the room. One stranded enemy means a wave that can never clear |
| puzzle boards | a rectangle of open floor with a clear margin, away from landings, on one component | |
| hidden things | ask the room for a tile with a property (cuttable shrub, soft earth act 0x0d, bombable 0x2e) and ring-scan from a spot | QUICKSTART's hide modes work in every region with no table, by predicate |
| torches | only where the tileset draws torch art | 60 of 119 sites listed the tile and drew nothing |
| NPCs | count every distinct face as a GFX sheet | |
| boss arenas | the most open tile by a 7x7 openness score | `castle_survey.py` |

### E. Verification

Every generated area runs these checks before the player can enter it:

1. **Token flood**: starting from ENTRY with the guaranteed tokens, flood
   the directed room graph, collecting rewards, until nothing changes.
   The GOAL must be reached. Every KEY must be reachable before its LOCK.
2. **In-room components**: per room, flood the tile grid (with ledge
   tiles as directed edges and water, pits and lava as blocked unless the
   tokens allow) from each entry. Check that each entry reaches the
   features the graph promises.
3. **Puzzles**: each placed puzzle is solved by its solver in place,
   against the room's actual tiles.
4. **Budgets**: per room, the planned live enemies plus NPC faces plus
   objects fit the GFX and entity budgets of `08_PERFORMANCE.md`.
5. **Failure**: reseed the room (or the area) up to N times. After that,
   fall back to a hand-authored "always valid" layout for that room role.
   Never let an unverified layout reach the player.

## 4. Puzzles: on device or pre-solved?

QUICKSTART's block puzzles were generated **offline** in Python with a
breadth-first solver, and 1,528 proven puzzles ship as data. Per puzzle
type, choose:

| approach | when |
|---|---|
| pre-solved pool in ROM, picked by seed, fitted to a footprint | search-heavy puzzles (block pushing, sliding, Sokoban-like). The solver is too slow for a fade |
| generate on device by construction | puzzles solvable by design: torch counts, switch orders (MEMORY), key and lock, dark-room routes |
| generate on device, then verify with a small solver | small state spaces: a 4-switch lights-out, a 3x3 tile flip |

ROM is cheap. The current build uses about 14.1 MB of 16 MB, almost all
of it Nintendo art and data the new game replaces. A pool of thousands of puzzles at a few dozen bytes each
costs little.

## 5. A Python twin, from day one

QUICKSTART's best tooling decision was `sim.py`: a Python re-implementation
of every seed-driven rule, fast enough to run 100,000 runs in two minutes,
and **validated against the ROM** by calling the ROM's own functions
(`sim_validate.py`, 402 of 402 cases).

For the new game, write the generator **twice from one spec**: in C for
the ROM and in Python for analysis. Use the same PRNG and the same
integer math (no floats, signed modulo as agbcc does it). Then:

- **Seed sweeps**: generate 100,000 areas in Python. Measure solvability,
  path length, how many locks, dead-end rate, how often each room
  archetype appears, budget overruns.
- **Equivalence**: boot the ROM in the emulator, call the C generator for
  a seed (`callrom.py`), dump the RAM graph and tiles, and diff them
  byte for byte against the Python twin. Run it over a few hundred seeds
  in CI.
- **Renders**: draw any seed's area as a PNG from Python, and from the
  ROM with `room_shot.py` (it stitches screenshots of a whole room).

**Doctrine 10: you can ask the ROM directly.** A Python copy of a rule only
tests the copy, until it is validated against the ROM.

## 6. Making it interesting, not just valid

Valid is the floor. These are the levers QUICKSTART found the user cares
about, plus standard ones for this genre:

- **Show the lock before the key.** A chest across water, a cracked wall,
  a dark doorway. The player should see a reason to come back.
- **One new verb per area**, taught in a safe room, then tested, then
  combined with an older verb.
- **Loops and shortcuts.** After the hard part, a one-way door or ledge
  back to the entry.
- **Landmarks.** One authored set piece stamp per area (a giant tree, a
  ruined tower) that the space graph places centrally, so players can
  orient themselves.
- **Escalating rooms.** Difficulty along the mission path: early rooms
  are chaff, rooms near the goal draw from higher levels. Per-room
  difficulty is the column-weight table, not new content.
- **Secrets by predicate.** A bombable wall with a crack stamp, a dig spot
  with a tell, a bush hiding a stair. Generated from the same predicate
  QUICKSTART uses for hiding.
- **Hints from the graph.** "The key lies north of the lake" is a walk
  over the graph. Build hint strings at run time into a RAM text buffer
  (`01_ENGINE_ARCHITECTURE.md`, text).
- **Map and compass.** Vanilla has both (`ITEM_MAP`, `ITEM_COMPASS`). The
  map screen needs a generated room layout. Plan for it with the space
  graph.

## 7. Traps that will reappear in generated worlds

Each of these cost QUICKSTART a session or more. Full list in `11_TRAPS.md`.

| trap | the generator's defence |
|---|---|
| a flood fill cannot see a ledge | ledges are directed edges in the room graph and in the in-room flood |
| walkable collision is not land | test the act tile, not the collision byte, for anything that stands |
| "can enter" is not "can explore" | the reach check asks for the feature's own component, not the room |
| a region's inner cost is not its entry price | price edges, not rooms |
| content over a door landing | reserve landings first |
| a wave counts the whole room | spawn only on the player's component |
| a hole whose transition is cancelled freezes the player invisible | every hole has a valid target, checked at generation |
| a locked door waiting on a flag nothing sets never opens | every lock's flag is set by a placed key or switch, checked by the flood |
| a tileset lists a type and draws nothing | test the screen in a probe, once per theme |
| a tile edit after `UpdateScrollVram` does not show | call `UpdateScrollVram` after live edits |
| comments lie about geography | name positions by coordinates, never "the southwest pocket" |
| a probe that forces state goes stale | regenerate probes' expectations from the twin, never hand-type them |

## 8. Memory and time budgets for generation

These were sized against TMC's memory map. The new engine owns its own
map (`12_FROM_SCRATCH_ENGINE.md` §3), and will have more EWRAM free
than TMC's 31 KB. The per-room and per-area sizes still hold.

| resource | budget | note |
|---|---|---|
| EWRAM free | about 31 KB above `gEndOfEwram` (0x02038560) | the graph for 9 areas, the current room's RAM exit list and entity lists, generator scratch |
| per room in the graph | aim for 16-32 bytes | size, grid position, edges (direction, kind, requirement id), role, seed, state bits |
| per area | 16-48 rooms | 48 rooms at 32 bytes is 1.5 KB. Nine areas is under 14 KB |
| tile maps | none stored | regenerated from the room seed into `gMapBottom`/`gMapTop` on load |
| room state | bits in `gSave`, per area per room | survives saves. Room flags in `gRoomVars` clear on every load |
| time | a room build within one fade, about 16-30 frames | about 280k cycles a frame. A 64x64 two-layer room is 8,192 tile writes plus stamp logic. Put the inner loops in IWRAM as ARM if needed |

A sketch of the stored room record:

```c
typedef struct {
    u8  cellX, cellY;        // position on the area grid, in screens
    u8  cellsW, cellsH;      // size in screens (1..4)
    u8  role;                // ENTRY, KEY, LOCK, GOAL, OPTIONAL, LOOP, CONTENT
    u8  archetype;           // layout family
    u8  content;             // ? room kind / quest / puzzle id, 0 none
    u8  edgeCount;
    u32 seed;                // room_seed
    struct { u8 dir, offset, kind, target; u16 req; } edges[4]; // req indexes a token set
} GenRoom;                   // 32 bytes with 4 edges
```

## 9. Suggested build order

1. **One authored room, loaded by the new engine's room loader** from
   the in-RAM form the generator will produce: tiles, exits, entity list.
   (Had TMC's engine been kept, this was a `GeneratedRoomLoad` hook in
   `LoadRoomGfx`. See `03_WORLD_TILES_COLLISION.md`.)
2. **One generated room**, from a seed, with a frame and exits only.
   Render it with `room_shot.py`.
3. **An area of 4 rooms** with borders and one door. Walk it in the
   emulator with a probe.
4. **The Python twin** of steps 2-3, and the equivalence probe.
5. **The mission graph** with one lock type (a small key), verified by the
   token flood over 100,000 seeds.
6. **Stamps and archetypes** for one theme. Budget probe per archetype.
7. **More lock types**, one verb at a time, each with its verifier.
8. **Waves and content** on generated rooms: spawn sampling, ? room kinds.
9. **Nine themes, the hub, the chain across areas.**

Measure at every step with a control. A probe that finds nothing has
proven nothing until it passes on a case known to work.
