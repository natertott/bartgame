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

## A pool per room: frames and contents

The user asked for variety: a room should not deal the same puzzle run
after run. So every room holds a POOL, built offline:

- a **frame** is where a puzzle sits - the board, the template's
  reference and posts, a maze's ring walls and way in, the chest or door,
  the switch, the prize tile. These depend on the room and are slow to
  find.
- each frame carries up to 32 **contents** - a template's goal shape and
  scrambled start, or a maze's carved inner walls and its rocks. Every
  one is solved offline.

A run draws a frame and a content per site from its seed, so a room with
three frames of 32 offers 96 puzzles. Content is 2 bytes per rock for a
template and 1 per rock plus 4 for a maze, so the whole pool is a few tens
of KB of the 2 MB the ROM has free.

Generating on the GBA each run was the other road. It was not taken: a
scramble on the GBA is solvable by construction but its difficulty is
unknown, and the search that proves the fewest pushes takes seconds of
desktop CPU per puzzle. The pool keeps the floor on difficulty and lets
every puzzle be checked before it ships.

## Offline: the floors, the pool, the proof

1. `tools/quickstart/block_rooms.py` boots every candidate room once and
   captures its floor as the game sees it (collision, act tiles, NPCs,
   where the player arrives) into `build/block_rooms.json`. Candidates:
   every ? room site alone in its room, kinstone-ungated, not a Great
   Fairy (100), and every region pool row (20).
2. `tools/quickstart/block_puzzles.py` finds up to three template frames
   and three chest-maze frames per room (plus a door maze per guarded
   door in a field), fills each with up to 32 contents, and writes
   `include/quickstart/block_puzzles.h` and `build/block_solutions.json`.
   Each room has its own random stream, keyed by the seed and the room,
   and the rooms run on four processes; about 25 minutes.
3. `block_puzzles.py --verify` reads the header back, decodes every
   content the way `game.c` does, and replays its solution push by push
   under the game's rules on the room's captured floor: the player can
   reach the far side, the rock may move that way, the next tile is board
   and free, and the puzzle is solved at the last push and not before. It
   also checks the rock budget and the reserved tiles.

**Templates** are made backwards: the goal shape is laid on the board, the
rocks are pulled away from it by legal reverse moves (a pull is a push
undone; the player must be able to walk to where the pull ends), then a
breadth-first search over pushes finds the true minimum. A content is kept
only when that minimum reaches the class's floor:

| Class | Board | Rocks | Axis-bound | Min pushes |
|---|---|---|---|---|
| XS | 3x3 | 3 | 0 | 5 |
| S | 4x4 | 4 | 0 | 7 |
| M | 5x5 | 5 | 1 | 9 |
| L | 6x6 | 7 | 2 | 11 |
| XL | 7x7 | 9 | 3 | 13 (overworld only) |

The reference shape stands within about a screen of the board, framed by
four gray corner posts. The L boards never prove inside the search cap,
so their solution is the scramble undone, cut at its first match, and its
length is an upper bound.

**Mazes** carve a corridor through a grid with no open 2x2 square, wall the
ring with fixed rocks, put the chest (or the door) at the back, park the
rocks off the corridor, and search backwards to the arrangements that seal
the target. Each is proved forward; at most two per carve, for spread.

| Class | Grid | Movers | Min pushes |
|---|---|---|---|
| XS | 4x3 | 2 | 3 |
| S | 5x4 | 3 | 5 |
| M | 6x5 | 4 | 6 |

Constraints on every frame and content: rocks only on plain ground (no water, pits,
swamp, ice, lava), every door, room edge and the arrival kept reachable
whatever the rocks do, and no rock, switch or prize on a tile the mode
already uses: each pool row's entrance, reward, boss spot and landing
spots, every fuser scatter spot, every ? room site's spot. The tiles
themselves, with no margin. The first cut put a rock on Lake Hylia's
reward tile and another on a fuser spot (`invariant_check.py`); a margin
of even one tile cost most of the layouts in narrow fields like Trilby.
A ? room holds at most 28 rocks, a field 26.

## In the ROM

- **? rooms.** A site with a pool rolls BLOCKS one time in three, by a
  hash of its own (`0xB10C + site`), whatever the pickers dealt, unless
  its kind is fixed (elite, rare, miniboss). The frame is another hash of
  the run (`0xB10D + site`), the content a third (`0xB10F + site`). Extra
  is the prize's draw seed. The sim mirrors the roll (`sim.site_roll`,
  `site_roll_validate.py`).
- **The block quest.** One region row per run with a pool, avoiding
  the other givers' rows (raw bank 12 bits 682-694). Every visit deals the
  same puzzle until it is solved (its frame from the quest's roll, its
  content from the run, `0xB110`); the first solve pays a RARE draw and counts
  as the run's side quest (`QuickStartSideQuestDone`). Ezlo explains it
  once a run.
- **Door mazes.** A player arriving through the guarded door is already
  inside: the movers are not dealt, so nobody is ever walled in.
- Room flags: a ? site's window (64 + 8 per site in the room), the quest
  120-124, the reset switch 107 (`QS_SWITCH_HIT_FLAG(3)`). The maze chest
  is local flag 253, next to the chest lottery's 250-252.
- Ezlo's four lines are `gCustomStrings3` +15..+18 after the site lines.

## What the generator built

1,528 puzzles in 112 frames, in 24 ? room sites and 10 of the 20 region
rows. A room holds 3 to 135; the median is 38.

| Kind and class | Frames | Puzzles | Pushes to solve |
|---|---|---|---|
| Template XS | 16 | 212 | 5-7 |
| Template S | 12 | 234 | 7-10 |
| Template M | 1 | 22 | 9-12 |
| Template L | 5 | 160 | up to 22, unproven |
| Maze XS, chest | 53 | 767 | 3-4 |
| Maze S, chest | 16 | 72 | 5-6 |
| Maze M, chest | 2 | 7 | 6 |
| Maze XS, door | 5 | 44 | 3 |
| Maze S, door | 2 | 10 | 5-6 |

| Field row | Frames | Puzzles |
|---|---|---|
| North Hyrule Field | 12 | 135 |
| Western Woods north | 7 | 128 |
| Lon Lon Ranch | 6 | 96 |
| South Hyrule Field | 6 | 66 |
| Hyrule Town | 5 | 46 |
| Royal Valley | 3 | 41 |
| Wind Ruins north | 2 | 36 |
| Western Woods | 1 | 32 |
| Trilby Highlands | 2 | 14 |
| Castle Garden | 1 | 8 |

The draw is uniform over every puzzle a room holds, not frame first. The
chance that two runs deal the same puzzle in a room is about one over its
count: median 2.8%, worst 33% (a site with three). Drawing the frame
first made it 14% at the median, because a door maze with two contents got
the same share as a template with 32.

In a run a site with a pool deals BLOCKS one time in three: 6.3% of all
site rolls, about 7.5 of a run's 119 sites (`sim.site_roll`, 2,000 seeds).

Fewer rooms than the first build (31 sites, 11 rows). The difference is
correctness: seven sites' only layouts had a switch the player could not
reach (below), and Minish Woods' mazes lost theirs the same way.

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
  bits of extra; a site can own six frames. Now the frame is bits 5-7 and
  the content bits 0-4.
- **A switch nobody could reach.** The first build put a maze's reset
  switch on the open tile nearest its way in: often the very tile in
  front of it, and once (Trilby's rupee cave) in a pocket the maze's own
  ring walls sealed. The first probe never noticed - it sets the player
  down rather than walking. The switch now goes to the far corner, never
  in front of the way in, and the switch and the prize must both be
  reachable with the puzzle in place.
- **Solved too early.** A large template's solution is its scramble
  undone, and a scramble can pull rocks out of the shape and back. The
  game locks a template at its first match, so a solution that passed
  through the shape halfway had its next push refused. Solutions are cut
  at the first match, and `--verify` rejects any that solve before their
  last push (it found 12 in the build before the fix).
- **Greedy parking.** Parking a maze's rocks one at a time where the chest
  stays reachable always succeeds, but it tucks them beside the corridor,
  one pull from sealing it: nearly every maze took one or two pushes.
  Random parking, retried, is back.

## Verifying

`block_puzzles.py --verify` is the proof for the whole pool: every content
decoded from the header as the game decodes it, every solution replayed
under the game's rules on the captured floor, solved at its last push and
not before. On the shipped pool: 1,528 of 1,528, 0 problems.

`tools/quickstart/block_probe.py` plays puzzles in the ROM through the
testbed (SITE kind BLOCKS, the frame in extra bits 5-7 and the content in
bits 0-4; or QUEST BLOCKS, frame + 1 in `scenario_c` and content + 1 in
`scenario_d`). It checks the dealt rocks against the table, plays the
solver's pushes, and requires the ROM's own SOLVED flag, the prize and the
DONE (or WON) state. `--contents N` plays the first content of every frame
and N - 1 seeded draws; 0 plays them all (about 75 minutes). The player is
set down behind each rock; the solver proved the walk. `--rules` adds the
refusals (fixed, axis, board edge) and the reset switch.

Last run, on the delivered ROM, two contents of every frame (224
puzzles): 224 solved, with the prize taken and DONE or WON set; every
reset put every rock back; fixed rocks refused 223 times, axis-bound
rocks a cross-axis push 28 times, pushes off the board 212 times. The
one reset that first failed (South Hyrule Field, a wave spoiling the
swing) passed on a retry, and alone four times in four.

`tools/quickstart/block_runpick.py` checks the run's own draw, nothing
forced: for every site that can deal BLOCKS it finds a seed whose roll
does, predicts the frame and content from the seed, boots that seed into
the room and compares the rocks. 23 of 23 dealt as predicted.

Harness traps the probe works round: an Ezlo line arriving a few seconds
after landing freezes the player (settle first, retry a refused push); a
field's waves knock the player off a push (health and invulnerability
frames pinned); a one-tile corridor's corner slide walks a teleported
player off the line (pin the cross axis while pushing, never both); the
boot's START can open the pause menu (close it); the test kit sometimes
puts the sword on A.

    python3 tools/quickstart/block_rooms.py              # once per floor change
    python3 tools/quickstart/block_puzzles.py            # ~25 min; --check to compare with the header
    python3 tools/quickstart/block_puzzles.py --verify   # every content, decoded and replayed
    make quickstart-d3
    python3 tools/quickstart/block_probe.py --rules      # two contents per frame

## Testbed

    python3 tools/quickstart/scenario.py site 27 BLOCKS 36     # site 27: frame 1 (bits 5-7), content 4 (bits 0-4)
    python3 tools/quickstart/scenario.py quest BLOCKS SHF 2 5  # the block quest in South Hyrule Field: frame 2, content 5
