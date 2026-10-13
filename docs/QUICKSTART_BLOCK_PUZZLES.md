# Block puzzles

Oct 2026. The user's mechanics sheet (Block_Puzzle_Mechanics.pdf) describes
two push-block puzzles, both built here:

- **Template.** A gray reference shape stands apart. The brown rocks must
  be pushed into the same shape on the board next to it. Occupied cells are
  compared, not which rock is where; no rotation, reflection or shift. A
  match pays a prize on the tile beside the board.
- **Maze.** Rocks stand in a walled grid between the player and a chest
  (in a ? room or a field) or a door (in a field). Pushing them clear opens
  the way. The chest holds the prize; the door is its own reward.

Both are ? room kinds (`QS_EVENT_BLOCKS`, value 9) and one overworld quest
(the block quest, one region row per run).

## The rules, and where each is enforced

| Sheet rule | Where |
|---|---|
| A push moves a rock one tile | vanilla `PUSHABLE_ROCK` (`pushableRock.c`) |
| The player must stand on the far side | vanilla push code (`beanstalkSubtask.c`, `SPECIAL_TILE_27`) |
| No push into a wall or another rock | vanilla (`sub_0801A2B0`) |
| No pulling | vanilla: R does nothing to a rock |
| No chain pushing | vanilla: a rock behind a rock is a wall |
| Some rocks move only one way | `QuickStartBlockPushAllowed`, blue = side to side, red = up and down |
| Nothing leaves the board | `QuickStartBlockPushAllowed` (the board rectangle) |
| A maze rock never plugs the chest or its approach | `QuickStartBlockPushAllowed` |
| Feedback on a match | a solve sound, the matched rocks turn gold and lock |
| Undo / reset | a crystal switch beside the board puts every rock back |
| Never a second reward | the prize is a room flag per visit, the site DONE bit or the quest's WON state for good |

The hook in `beanstalkSubtask.c` is one call under `#ifdef QUICKSTART`,
made after vanilla has accepted the push and before it starts. A rock that
is not ours (a vanilla boulder) is always allowed.

One-way rocks (down only, right only) from the sheet are not built. The
two-axis classes cover the sheet's examples and read clearly in two
colours; a one-way rock would need an arrow sprite.

## Colours

The rock's own palette differs by area (pink in Castle Garden), so every
rock is recoloured from it, one palette slot per colour
(`QuickStartBlockTint`, the same slot scheme as the pastry tiers):

| Rock | Colour |
|---|---|
| Movable, any direction | brown |
| Movable, side to side only | blue |
| Movable, up and down only | red |
| Fixed (the reference, the frame posts, maze walls) | gray |
| Part of a matched template | gold |

## Offline: the floors, the layouts, the solutions

Every layout is generated and solved before the build. Nothing is searched
on the GBA.

1. `tools/quickstart/block_rooms.py` boots every candidate room once and
   captures its floor as the game sees it (collision, act tiles, NPCs,
   where the player arrives) into `build/block_rooms.json`. Candidates:
   every ? room site alone in its room, kinstone-ungated, not a Great
   Fairy (100), and every region pool row (20).
2. `tools/quickstart/block_puzzles.py` builds up to three templates and
   three mazes per room and writes `include/quickstart/block_puzzles.h`
   and `build/block_solutions.json` (the push list for each).

**Templates** are made backwards: the goal shape is laid on the board, the
rocks are pulled away from it by legal reverse moves (a pull is a push
undone; the player must be able to walk to where the pull ends), then a
breadth-first search over pushes finds the true minimum. A layout is kept
only when that minimum reaches the class's floor. Classes:

| Class | Board | Rocks | Axis-bound | Min pushes |
|---|---|---|---|---|
| XS | 3x3 | 3 | 0 | 5 |
| S | 4x4 | 4 | 0 | 7 |
| M | 5x5 | 5 | 1 | 9 |
| L | 6x6 | 7 | 2 | 11 |
| XL | 7x7 | 9 | 3 | 13 (overworld only) |

The reference shape stands within about a screen of the board, framed by
four gray corner posts. No M or XL template fits anywhere in this build
(the generator tries the biggest class first and falls back).

**Mazes** carve a corridor through a grid with no open 2x2 square, wall the
ring with fixed rocks, put the chest (or the door) at the back, and search
backwards from rocks parked clear of the path to the states where the
target is sealed. The deepest one under the class's rock cap is kept.

| Class | Grid | Movers | Min pushes |
|---|---|---|---|
| XS | 4x3 | 2 | 3 |
| S | 5x4 | 3 | 5 |
| M | 6x5 | 4 | 6 |

Constraints on every layout: rocks only on plain ground (no water, pits,
swamp, ice, lava), every door, room edge and the arrival kept reachable
whatever the rocks do, and no rock, switch or prize on a tile the mode
already uses: each pool row's entrance, reward, boss spot and landing
spots, every fuser scatter spot, every ? room site's spot. The tiles
themselves, with no margin. The first cut put a rock on Lake Hylia's
reward tile and another on a fuser spot (`invariant_check.py`); a margin
of even one tile cost most of the layouts in narrow fields like Trilby.
A ? room holds at most 28 rocks, a field 26.

## In the ROM

- **? rooms.** A site with instances rolls BLOCKS one time in three, by a
  hash of its own (`0xB10C + site`), whatever the pickers dealt, unless
  its kind is fixed (elite, rare, miniboss). Which instance: another hash
  (`0xB10D + site`). Extra is the prize's draw seed. The sim mirrors all
  of it (`sim.site_roll`, `site_roll_validate.py`).
- **The block quest.** One region row per run with instances, avoiding
  the other givers' rows (raw bank 12 bits 682-694). Every visit deals the
  puzzle until it is solved; the first solve pays a RARE draw and counts
  as the run's side quest (`QuickStartSideQuestDone`). Ezlo explains it
  once a run.
- **Door mazes.** A player arriving through the guarded door is already
  inside: the movers are not dealt, so nobody is ever walled in.
- Room flags: a ? site's window (64 + 8 per site in the room), the quest
  120-124, the reset switch 107 (`QS_SWITCH_HIT_FLAG(3)`). The maze chest
  is local flag 253, next to the chest lottery's 250-252.
- Ezlo's four lines are `gCustomStrings3` +15..+18 after the site lines.

## What the generator built

162 instances: 31 ? room sites (of 100 candidates) and 11 of the 20 region
rows.

| Kind and class | Instances | Pushes to solve |
|---|---|---|
| Template XS | 24 | 5-7 |
| Template S | 15 | 7-9 |
| Template L | 6 | 12-22 |
| Maze XS, chest | 90 | 3-4 |
| Maze S, chest | 16 | 5-6 |
| Maze M, chest | 4 | 6-7 |
| Maze XS, door | 6 | 3 |
| Maze S, door | 1 | 5 |

The large templates are in the two big Minish path rooms (sites 50 and
80). Their minimum was not proved inside the search cap, so the count is
the length of the scramble undone, an upper bound. In the fields the
templates are XS and S and the mazes guard doors in North Hyrule Field
and the Western Woods. Nine rows have nothing: the floor near the arrival
is too broken up (Eastern Hills, the Western Woods' south and centre,
Castor Wilds, the Ruins' entrance, Crenel, Veil Falls) or wet (Lake
Hylia).

In a run a site with instances deals BLOCKS one time in three: 8.2% of all
site rolls, about 10 of a run's 119 sites (`sim.site_roll`, 3,000 seeds).

## Traps found on the way

- **Rocks on the mode's own spots.** The first cut put a rock on Lake
  Hylia's reward tile and one on a fuser spot. Now reserved (above).
- **Walkable water.** A Minish cave maze sat on a shallow-water edge the
  generator thought was a wall; the ROM's flood walked round the rocks and
  called it solved on the first frame. Maze rings now seal every
  collision-free tile.
- **Crumbling floor.** Act tile 0x08 (`TILE_ACT_PLAYER_WALK`) turns into a
  pit once walked on. In the Veil Falls cave entrance a template's
  solution walked the player over it and left a hole where the next push
  had to stand. It is a hazard now.
- **Same-frame respawn.** A deleted entity's slot frees at the end of the
  frame, so the reset switch's delete-then-spawn came back with no movers
  in busy fields. The movers are now owed and dealt on a later frame, all
  or none, retried until they fit (`QS_BLOCK_DEAL_FLAG`). The first deal
  goes the same way.
- **Overflowing ordinal.** The testbed's instance number first rode in two
  bits of extra; a site can own six instances.

## Verifying

`tools/quickstart/block_probe.py` boots every instance through the testbed
(SITE kind BLOCKS with the ordinal in extra bits 5-7, or QUEST BLOCKS with
`scenario_c` = ordinal + 1), checks the dealt rocks against the table,
plays the solver's push list, and requires the ROM's own SOLVED flag, the
prize and the DONE (or WON) state. The player is set down behind each rock
rather than walked there; the solver proved the walk. `--rules` adds the
refusals (fixed, axis, board edge) and the reset switch on every instance
where each applies.

Last run, on the delivered ROM: 162 of 162 solved, with the prize taken and
DONE or WON set. Every reset put every rock back (162), fixed rocks
refused 161 times, axis-bound rocks refused a cross-axis push 26 times,
and pushes off the board were refused 153 times.

Harness traps the probe works round: an Ezlo line arriving a few seconds
after landing freezes the player (settle first, retry a refused push); a
field's waves knock the player off a push (health and invulnerability
frames pinned); a one-tile corridor's corner slide walks a teleported
player off the line (pin the cross axis while pushing, never both); the
boot's START can open the pause menu (close it); the test kit sometimes
puts the sword on A.

    python3 tools/quickstart/block_rooms.py          # once per floor change
    python3 tools/quickstart/block_puzzles.py        # ~30 min; --check to verify the header
    make quickstart-d3
    python3 tools/quickstart/block_probe.py --rules

## Testbed

    python3 tools/quickstart/scenario.py site 27 BLOCKS 32    # site 27, its second instance (extra 32 = ordinal 1)
    python3 tools/quickstart/scenario.py quest BLOCKS SHF 2    # the block quest in South Hyrule Field, its second instance
