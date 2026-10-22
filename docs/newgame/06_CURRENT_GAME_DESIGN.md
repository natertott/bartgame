# 06. The current game's design (QUICKSTART)

What the current game plays like, system by system. The new game keeps
this design vocabulary and moves it onto generated areas. Each section ends
with what carries over.

Deeper records: `docs/HANDOFF_GAME.md`, `docs/HANDOFF_STATUS.md`, and the
roadmap entries they point to.

## The run loop

1. **Hub.** A stack of rooms in the Wind Tribe tower
   (`docs/QUICKSTART_HUB.md`). Floor 3 is the spawn and the three item
   selection rounds. Floor 2 is the inn (pay to rest). Floor 1 is the shop.
   The roof runs a wave with a reward. The exterior has the wind crest and
   the pit out. A trophy case shows what runs have found. Wandering NPCs
   give hints. Vanilla's staircase transitions link the floors, so the hub
   needed no custom doors.
2. **The drop.** The player falls through a pit in the Cloud Tops into a
   random **region pool row**: 23 rows over 16 regions. The drop region
   re-rolls if the loadout cannot survive it: boots or cape for the swamp,
   flippers for the lake. Each row has several surveyed landing spots.
3. **Free roam.** Regions connect on foot through vanilla borders and
   doors. **Containment** cancels any transition into a room that is not
   in a region or blessed as a pocket interior.
4. **The win chain.** `QUICKSTART_CHAIN_STEPS` (now 4) requirements, dealt
   one at a time. Each is rolled only when the last completes, so the
   placer sees the live inventory. Kinds: `EVENT` (finish a ? room),
   `WAVE` (clear a region's next wave), `BOSS`, `QUEST` (the run's side
   quest), and `ITEM` as a fallback. The last step pays the Earth Element.
   Grab it and the run ends.
5. **The Ocarina** flies home to the hub at any time.

**Carries over**: hub, then drop, then roam, then a chain of N steps,
then the goal item. In the new game the nine generated areas replace the
ring of regions.

## Regions, rows and containment

A **region** is a set of vanilla rooms treated as one place. A **pool
row** is a room in it that can host waves, quests and landings. Tables
per region in `src/game.c`: adjacency (`sQuickStartRegionAdjacency`),
pool rows and `byPool`, drop spots, wave and boss allowlists
(`QuickStartRegionAllowsWave/Boss`), `QuickStartRegionOfRoom`,
containment lists, quirk hooks (per-region code that deletes vanilla
content on sight), hint banks, and the reach survey.

**The checklist for adding one region runs to about 20 tables.** Adding
Hyrule Castle took three commits. That cost is the clearest argument for
generation: in the new game each of these tables must be **output by the
generator**, not authored.

| QUICKSTART table | what the generator must emit instead |
|---|---|
| adjacency | the area's room graph |
| pool rows, drop spots | rooms flagged for waves and landings, with surveyed spots |
| wave and boss allowlists | per-room capability flags from its size and open floor |
| containment and blessing | nothing: a generated area has no rooms outside itself |
| quirk hooks | nothing: no vanilla content to delete |
| hint banks | generated hint text from the graph |
| reach survey | the lock-and-key graph itself |

## Waves

Every region runs **endless escalating waves**. A wave deals a
composition from the difficulty row (`04_ENTITIES_ENEMIES_OBJECTS.md`):
level odds, then kinds by role and theme, then a count from density, all
inside the GFX and entity budgets. Killed enemies are replaced until the
wave quota is met. The first clear of a region pays a one-time reward,
which is the only draw that can pay a KEY item. The castle's waves pay
nothing, by the user's request.

Spawn spots come from `spawn_spread.py`: farthest-point sampling over the
room's walkable, dry land with 3x3 clearance, over every component the
arrivals can reach. **`QuickStartRegionWaveCleared` counts every enemy in
the room**, so an enemy stranded across water or up a climb wall makes a
wave impossible to clear. Spawn only on the player's component.

Ten composition archetypes (swarm, artillery, ambush and so on) ask for
roles, not kinds.

**Carries over**: composition by roles and costs, budgets, spawn sampling
and the component rule. The generator knows the components, so it can
emit spawn spots directly.

## ? rooms (content sites)

122 **content sites**: rooms behind doors where an event is dealt.
Kinds (`QS_EVENT_*`, `src/game.c` around line 11238):

| # | kind | what happens |
|---|---|---|
| 0 | ITEM_DROP | a prize on the floor |
| 1 | MINIBOSS | an Elite fight. Medium and large rooms only |
| 2 | NPC | a character with a hint or a trade |
| 3 | WAVES | a fight, or survive N seconds |
| 4 | POT_LOTTERY | pick a pot |
| 5 | CHEST_LOTTERY | pick a chest. Pulled from the draw |
| 6 | FAIRY | a free heal |
| 7 | MEMORY | two rooms: one shows three switches blinking in a seeded order, another elsewhere pays when they are struck in that order |
| 8 | PUZZLE | a one-room switch puzzle, three variants |
| 9 | BLOCKS | a block puzzle: template or maze (below) |
| 10 | TORCHES | light every torch with the Lantern. The room may be dark, torches may burn out, enemies keep coming |
| 11 | CLEANUP | clear webs and dust with the Gust Jar, or burn webs with the Lantern |

Retired: the cage-and-switch puzzle. Its pots could simply be lifted, and
it was broken or awkward in most rooms. **Lesson: every puzzle needs a
solver-checked layout in its actual room, and no bypass through vanilla
mechanics** (lifting, jumping, bombing).

**Portal pockets** (`docs/QUICKSTART_PORTAL_POCKETS.md`): a chain pair
where clearing a ? room wakes a portal into an unreachable pocket. The
next step is an ITEM met by holding any of the pocket's escape items.
One pair at most per run, in about one run in three.

**Carries over**: the event vocabulary. In a generated area, a "? room"
is any room node the generator marks for content, and every kind becomes
a node decoration the generator can place and verify.

## Quests

One side quest per run, hosted in a region row
(`scenario.py` `QUESTS`):

| quest | what the player does |
|---|---|
| POT | find the prize hidden in one of a field of pots |
| HUNT | kill a pack against a clock (30 s, 7-13 enemies) |
| SCAV | catch a thief who bolts, or find it hidden under a bush or buried (Mole Mitts) |
| STEALTH | "the watch": cross a line of watchmen without entering a sight cone, 40 s |
| CARRY | carry an unbreakable pot from giver to receiver through two mixed waves |
| COURIER | a ported vanilla errand: deliver between two regions |
| BLOCKS | a block puzzle in a field row |

**Failure stakes scale with difficulty**: free at 0-3, then rupees, then
hearts, then a charm or a curse at 12. The tier is latched at quest start
so it cannot grow after it was announced.

Hide spots are found by **predicate**, not table: "a cuttable-shrub tile
type" and "act tile dig". The runtime ring-scans from the quest's spot
and degrades mode by mode. **This is the right pattern for procgen**:
content asks the room for a tile with a property, so it works in a room
that was never authored.

## Puzzles

**Block puzzles** (`docs/QUICKSTART_BLOCK_PUZZLES.md`). Two kinds, from the
user's mechanics sheet:

- **Template**: a gray reference shape stands apart. Push the brown rocks
  into the same shape on the board. Cells are compared, not which rock is
  where. No rotation, reflection or shift.
- **Maze**: rocks stand in a walled grid between the player and a chest or
  door. Push them clear.

Rules: one tile per push, from the far side, no pulling, no chain pushing,
nothing leaves the board, some rocks move one axis only (blue side to side,
red up and down), a maze rock never plugs the goal. A crystal switch
resets the board. A match locks the rocks gold. **1,528 proven puzzles**:
an offline generator plus a breadth-first solver, so every puzzle shipped
has a known solution and a known minimum push count. The rule hook is
one function (`QuickStartBlockPushAllowed`) called from vanilla's push code.

**Torches and darkness**: unlit torch type 117 becomes 118 when swung at
with the Lantern. Light is one dial, `sub_0805BB00(level, 1)`: 0x100 day,
0x80 vanilla's dim, 0 black. Each lit torch adds `(0x100 - level) / count`.
**Only 59 of 119 sites draw a torch**, because a tileset can list the tile
type and have blank art for it. Test the screen, not the tables.

**Webs and dust**: the Gust Jar pulls a web away only while the player is
pulled back from it, and dust only from 23-36 px straight below.

**Carries over**: the generator-plus-solver pattern, the rule hooks and
the measured mechanics. In the new game, the generator runs **on the
device** or ships a pre-solved pool, and every placement is checked by
the same solver.

## Difficulty

Steps 0-12. The table moves the odds, never the content
(`04_ENTITIES_ENEMIES_OBJECTS.md`). A win promotes one step. A death
demotes one, with a floor of 1. QUICKSTART ships only difficulty 3
(`make quickstart-d3`).

## The reach model (the load-bearing part)

Covered in depth in `07_PROCGEN_DESIGN.md`. In short:
`world_reach.py` is the hand-walked survey of where each item lets the
player go. `gen_reach.py` compiles it to `include/quickstart/reach.h`.
At run time a flood over region adjacency admits a region when its entry
price is paid. **The chain only places a requirement where the player can
already stand.** `sim.py` replays 100,000 runs to show what is reachable.

## The meta loop (unbuilt)

The vision: an early save has limited items, regions, event kinds and a
capped difficulty. Score across runs unlocks more. `QUICKSTART_UNLOCKS_ENABLED`
is 0. The catalog, score and trophy case exist. The entitlement half does
not.

## What the user has asked for, in their words

- "These should show up anyway as a reason to go find it." (Item-gated
  rooms appear before the player holds the item.)
- "Keep this as a feature: the lantern can also solve the gust jar rooms."
- "The difficulty scaling should not be about what tiers or types of
  enemies are possible, but rather the chance that various tiers spawn."
- "We should ONLY have vanilla door mechanics, no more of this
  teleporting/warping stuff."
- Endless waves: "continue even after the win", refill when fewer than
  three are alive.
- "The quests need to be more difficult in general."
