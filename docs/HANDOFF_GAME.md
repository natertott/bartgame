# The game: what QUICKSTART is

A handoff document. Start here, then `HANDOFF_STATUS.md` for what is built,
`HANDOFF_ISSUES.md` for what is broken, and `HANDOFF.md` for how to work in
this repo without repeating mistakes that have already been paid for.

---

## One paragraph

QUICKSTART is a **roguelite built inside a decompiled GBA *Legend of Zelda:
The Minish Cap***. The vanilla overworld is kept exactly as Nintendo drew it;
the randomization lives behind the doors and in what happens in each room.
Every run: pick three items in a hub, fall out of the sky into a random
overworld region, fight escalating waves, and chase a five-step chain of
requirements that ends in the Earth Element. Same map every run, different
world behind it.

It is a **mod, not a fork**: essentially all of it lives in `src/game.c`
behind `#ifdef QUICKSTART`, on top of the untouched decomp.

---

## The run loop

1. **Hub.** A room in the Wind Tribe tower. Three selection rounds - a key
   item, a rare reward or stat, a skill - each offering three choices drawn
   from the tier table. Also a shop, a trophy case, an inn, and wandering
   NPCs who give hints.
2. **The drop.** The player leaves through a pit in the Cloud Tops and falls
   into one of 18 **region-pool rows** spread over 13 **ring regions**. The
   drop region is rolled, then re-rolled if the player lacks the kit that
   region needs to survive (boots/cape for the swamp, flippers for the lake).
   Each region has several surveyed landing spots.
3. **Free roam.** The ring is walked, not warped. Every region runs endless
   escalating waves, pays a one-time reward on its first wave clear, and can
   host quests and "? rooms".
4. **The win chain.** Five requirements, dealt **one at a time** - each is
   rolled only when the previous one completes, so the placer sees the
   player's live inventory. Kinds: `EVENT` (clear a ? room), `WAVE` (clear a
   region's next wave), `BOSS` (kill a region's boss), `QUEST` (finish the
   run's side quest), and `ITEM` as a fallback.
5. **The Earth Element** drops in one rolled region when that region's
   *carrier* condition is met (wave, boss or quest). Grab it and the run ends.

## The economy

- **Kinstones are the key economy.** Enemies drop pieces; fusing with an NPC
  at a gated door opens a new ? room for the rest of the run. Some doors are
  always open so content stays reachable without fusions.
- **The tier table** (`sQuickStartTiers`) is the one item source. A draw rolls
  a tier 60/30/10 and then picks uniformly among usable entries. Categories
  are a **bitmask**: `KEY`, `REWARD`, `WEAPON`, `SKILL`, `STAT`, `CHARM`.
  `QS_CAT_DROP` is everything but KEY; `QS_CAT_ALL` includes it.
- **The region clear reward is the only draw that can pay a KEY item**, which
  makes it the mechanism by which a run's reachable world actually grows.
  (The `ITEM` chain step was designed for that job and never fires - see
  `HANDOFF_STATUS.md`.)
- Fourteen charms/curses, half of them traps, are repurposed vanilla food
  items with run-long effects.

## Difficulty

`sQuickStartDifficultyTiers` has one row per difficulty step 0-12, six
columns (enemy levels 1-5 plus an Elites tier) that must sum to 100, plus a
density. **Difficulty moves the odds, it never gates content**: from step 3
up every column is non-zero. The table is generated - edit
`tools/quickstart/tier_curve.py` and re-emit, never hand-type it.

The Elite column is deliberately tiny at every step because four of its six
entries are Darknut forms; it is effectively the Darknut dial. Live caps
(`sQuickStartLiveCaps`) bound each family independently.

**We ship difficulty 3 only.** `make quickstart-d3`.

## The reachability model

The most load-bearing subsystem, and the one most likely to bite you.

- **The survey** (`tools/quickstart/world_reach.py`) is hand-transcribed from
  the user walking the world in a MAPEXPLORE build. It is the source of
  truth. Each region block has a start point and a list of destinations, each
  priced in **tokens** (items and world facts alike: `bombs`, `grip`,
  `minish_cap`, `maze_solved`, `fusion`...).
- **`gen_reach.py` compiles it** to `include/quickstart/reach.h`. That header
  is GENERATED - never hand-edit it.
- At run time `QuickStartReachableRegions` floods the ring adjacency admitting
  a region when its **entry price** is paid, and `QuickStartReachRoomOk` asks
  whether a specific room is enterable given the loadout.
- **The chain only ever places a requirement somewhere the player can already
  stand**, using the loadout held at the moment it is placed. That is the one
  rule the whole subsystem exists to serve.

Two structural traps, both of which have already caused real bugs:

- **A region's `room_req` is the cost of moving around INSIDE it, not the
  cost of getting in.** Where the entry price is recorded as an exit row in a
  *neighbour's* block, it is invisible to the region table. `world_reach.ENTRY`
  now states crossings directly for the regions where those differ.
- **"Can enter" is not "can explore."** `QuickStartReachPoolOk` only asks
  whether the player can be inside a region, and that is also the test the
  chain uses to place a wave or a boss. Mount Crenel is free to walk into and
  its interior wants the Grip Ring.

## The long-term vision

From the roadmap's own statement of direction, still current:

- **The meta loop is the game.** An early save file has limited items,
  regions, event kinds and capped difficulty - room to learn the vocabulary.
  Score aggregated *across* runs crosses benchmarks that unlock new items,
  powerups, event kinds, quests and regions. Wins raise difficulty and deepen
  the run.
- **The kinstone economy tightens as difficulty rises** - abundant early,
  grind-worthy later.
- **The overworld keeps its vanilla layout.** Randomization lives behind the
  doors.
- **Depth before breadth.** The ring does not grow until a full playthrough
  is smooth. Every fix is a general mechanism, never a per-room special case.
- **Content breadth is data entry.** The tables, checkers and budget docs
  exist so new events, quests and regions are rows plus a survey. Spend
  breadth effort only through that machinery.
- **Measurement before allowlists.** Nothing spawns anywhere it has not been
  watched working; nothing is tuned without a probe.

The single biggest unbuilt piece of the vision is the **entitlement half of
the meta loop**: `QUICKSTART_UNLOCKS_ENABLED` is 0, so the trophy case shows
what a run has FOUND rather than what the save file has UNLOCKED. Everything
needed to make unlocks real - the catalog, the score, the trophy case UI -
already exists.
