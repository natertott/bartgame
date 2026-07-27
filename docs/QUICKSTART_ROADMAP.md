# QUICKSTART Long-Term Roadmap

This document captures the long-term design for the QUICKSTART roguelite mode:
where it's going, the architectural decisions already validated in the engine,
and the order we're building the rest of it in. It's meant to be read and
revised over many sessions - update it as decisions change.

## 1. The vision, restated

A run looks like:

1. **Spawn room** (Castor Darknut Main) - item-choice sequence, 3 waves of
   enemies, chest reward. Difficulty tier 1. *(exists today)*
2. **Hub room** (Melari's Mine) - shop + inn-style rest point, no combat.
   Difficulty tier 1. *(exists today, no "inn/rest" feature yet)*
3-7. **Four overworld regions**, drawn at random from a pool of seven and
   played in random order. Each region: enemies scale up per its position in
   the run, a full-clear item reward, then a boss fight, then one of the four
   Elements. Difficulty rises with region position (region 1 harder than the
   hub, region 4 hardest of all).
8. **Win**: once all four Elements are collected, the run ends, a score is
   shown, that score feeds a persistent meta-progression currency, and the
   game loops back to a new run at a higher base difficulty.

Over many runs, accumulated score unlocks: more of the seven regions
appearing in the random pool, more items available to find, and buffs -
making later runs both harder (base difficulty climbs every win, exactly as
today) and *more random* (bigger pools to draw from).

## 2. What's already validated and implemented

### 2.1 Region area/room IDs (verified against `include/roomid.h`/`area.h`)

All seven named regions already exist as real, playable rooms in the base
game - no new map content needed, only QUICKSTART logic:

| Region | Area | Room | Status |
|---|---|---|---|
| Hyrule Castle Gardens | `AREA_CASTLE_GARDEN` | `ROOM_CASTLE_GARDEN_MAIN` | **Done** |
| Lon Lon Ranch | `AREA_HYRULE_FIELD` | `ROOM_HYRULE_FIELD_LON_LON_RANCH` | **Done** |
| Castor Wilds | `AREA_CASTOR_WILDS` | `ROOM_CASTOR_WILDS_MAIN` | Not started |
| Eastern Hills | `AREA_HYRULE_FIELD` | `ROOM_HYRULE_FIELD_EASTERN_HILLS_CENTER`\* | Not started |
| Trilby Highlands | `AREA_HYRULE_FIELD` | `ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS` | Not started |
| North Hyrule Field | `AREA_HYRULE_FIELD` | `ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD` | Not started |
| South Hyrule Field | `AREA_HYRULE_FIELD` | `ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD` | Not started (MAPEXPLORE spawn point, camera bug already fixed here) |

\* Eastern Hills is actually 3 linked screens in vanilla
(`..._EASTERN_HILLS_SOUTH/CENTER/NORTH`). v1 treats only CENTER as "the
region," same footprint as every other single-room region below - folding
in the other two screens as a bigger, multi-room region is a plausible
future upgrade, not a v1 requirement.

### 2.2 Persistent storage model (implemented, tested)

The key open question was *where does progress live so it survives what*.
Verified by reading `src/fileselect.c`/`src/save.c`:

- `ResetSaveFile()` does `MemClear(save, sizeof(SaveFile))` - a **full wipe**
  of every field, including all global flags, whenever a save slot is deleted
  or a new file is started on it.
- `DoSoftReset()` (the win-loop's own reset, used today for the
  difficulty counter) does **not** touch `gSave` at all - it's explicitly
  preserved in EWRAM, and `WriteSaveFile()` is called right before it to
  persist to EEPROM too.

Decision: **meta-progression (score, XP, unlocks) lives in `gSave`, the same
struct the existing difficulty counter (`GF_DIFFICULTY_BIT`) already uses.**
It survives the win-loop (the actual "get better, then go again" cycle this
whole mode is built around) but resets if the player deletes the save file
and starts fresh - consistent with how difficulty already behaves, and it
required zero new EEPROM address plumbing (see below) rather than reverse-
engineering a second save slot outside the per-file wipe boundary.

**Storage budget**: `SaveFile` (`include/save.h`) is 0x4B4 bytes; its EEPROM
slot is 0x500 - already ~76 bytes of headroom, on top of ~86 bytes of
pre-existing `fillerNN[]` padding fields inside the struct. New fields were
added by repurposing filler bytes exactly (same total size per block), so
the struct's total size and every other field's offset is unchanged for
non-QUICKSTART builds (each new field is `#ifdef QUICKSTART` / `#else
fillerNN[]` / `#endif`) - zero risk to real-game save compatibility.

Fields added (all `#ifdef QUICKSTART`, all reset to 0 in `GameTask_Transition`
*except* the two marked persistent):

- `run_frames` (u32) - frames elapsed this run, real-time clock for the
  score's time bonus.
- `enemies_killed` (u32, pre-existing field, now reset per-run under
  QUICKSTART instead of accumulating for the whole save file's lifetime)
- `miniboss_kills` (u32)
- `boss_kills` (u32) - wired up, always 0 today (no region has a boss yet)
- `meta_xp` (u32, **persistent**) - lifetime accumulated score
- `runs_completed` (u32, **persistent**) - lifetime win count

### 2.3 Scoring (implemented, tested end-to-end in emulator)

`QuickStartComputeScore()` (`src/game.c`, right before `QuickStartCheckWinCondition`):

```
score = enemies_killed*10 + miniboss_kills*100 + boss_kills*500
      + (500 if run_frames <= 10 in-game minutes)
      + (200 if rupees >= 200)
      + (50 per heart gained beyond the starting 3)
      + (20 per distinct item owned)
```

All thresholds are `#define`d placeholders at the top of the function,
explicitly meant to be retuned once real playthrough data exists - not a
final balance pass.

Wired into `QuickStartCheckWinCondition` as a **second** message shown after
the existing "Difficulty increased" message is dismissed ("Run score:
`<N>`"), using the same `\x06\x01`/`gMessage.rupees` numeric-substitution
mechanism the difficulty message already proven to use. `meta_xp` and
`runs_completed` are updated at the moment this message is composed, so
they're saved by the same `WriteSaveFile()` call already at the end of the
win sequence.

**Verified in-emulator** (`scratchpad/score_test1.py` this session): poked
known values for every input, confirmed the displayed score and `meta_xp`
matched the formula exactly, confirmed `meta_xp`/`runs_completed` survived
`DoSoftReset` while `enemies_killed`/`miniboss_kills`/`run_frames` correctly
reset to 0 for the next run.

### 2.4 Miniboss kill tracking (implemented)

The one existing miniboss (`LADDER_KIND_MINIBOSS`, a `DARK_NUT` in a ? room -
`QuickStartSetupLadderRoomContent`, `src/game.c`) now increments
`gSave.miniboss_kills` at the exact point the code already detects "no
matching enemy left in the room => it died" - tied to the same
`SetRoomFlag(2)` success path that drops its reward, so it can't double-count
even on a retry frame.

## 3. Not yet designed in code - open architecture questions

### 3.1 Region system generalization

Today, Castle Garden and Lon Lon Ranch are each hand-written: their own
enemy-offset grids, their own "spawn enemies once"/"spawn reward once"
functions, their own containment logic, called individually from
`QuickStartRoomMonitor`. Adding 5 more regions by copy-pasting that pattern
5 more times is how this file already got to ~3000 lines: not recommended.

**Plan**: introduce one `QuickStartRegion` table (area, room, enemy offset
grid + count, room-square count for density, reward item pool, boss id,
"cleared" global-flag bit) and one generic set of functions
(`QuickStartSpawnRegionEnemiesOnce`, `QuickStartSpawnRegionRewardOnce`,
`QuickStartSpawnRegionBossOnce`, `QuickStartCheckRegionCleared`) that take a
`QuickStartRegion*` and do what the Castle Garden/Lon Lon-specific versions
do today. Castle Garden and Lon Lon Ranch become the first two rows in that
table (a refactor, not a behavior change - existing behavior must be
reverified after, not just assumed preserved). The other five regions become
new rows plus per-region emulator work to find each room's walkable bounds
and a good enemy-offset grid (the same kind of survey already done for
Castle Garden/Melari's Mine/Lon Lon Ranch - see the `sQuickStart*EnemyOffsets`
tables and their "confirmed empirically" comments).

Region-quirk logic that doesn't fit the generic shape (Lon Lon Ranch's boulder
puzzle, its Goron NPC removal) stays as small region-specific hooks the table
row can optionally point to, same pattern `QuickStartRoomMonitor` already uses
for one-off cases.

### 3.2 Region selection & difficulty-by-position

Once 7 regions exist in the table: at run start (or hub-room entry), pick 4
distinct regions at random and shuffle their order. Map region position to a
difficulty tier feeding `QuickStartPickEnemy`'s existing tier system (already
data-driven 0-12): e.g. region 1 -> tier N, region 2 -> tier N+X, etc., where
the overall base difficulty (`QuickStartGetDifficulty()`, already persistent
across wins) shifts the whole curve up each time the player wins. Exact
tier-per-position mapping is a balance question best settled after real
playtests of the 2-region version, not guessed now.

The chosen order needs to persist for the whole run (survives room
transitions, does not survive `DoSoftReset`) - same idiom as everything else
in this section: a `gSave`-backed field (or a handful of global flags/bits),
reset in `GameTask_Transition`'s existing per-run reset block.

### 3.3 Per-region boss + Element reward

**Open research question, not yet answered**: which enemy IDs can actually
serve as a standalone "boss" the way `DARK_NUT` already does for the ? room
miniboss? Real dungeon bosses in this engine overwhelmingly need scripted
arenas, cutscene triggers, or dungeon-specific room properties - the exact
reason the regular enemy roster (`sQuickStartLevel1..5`) deliberately excluded
anything beyond a bare `CreateEnemy(id, form)` call. This needs the same kind
of one-by-one "does it crash, does it just sit there, does it work" audit
already done for the regular roster, run against the real dungeon boss list,
*before* committing to which bosses are usable.

Fallback if few/no real bosses turn out to be standalone-spawnable: an
"elite" encounter built from the existing roster instead of a new actor - a
single higher-tier enemy with boosted stats/a `EM_FLAG`-style marker, or a
small multi-enemy gauntlet - functionally a "boss" for scoring/reward
purposes (counts toward `boss_kills`, drops an Element) without needing a
new actor to work. This should be a fully acceptable fallback if the real-boss
audit comes back thin, not a last resort.

### 3.4 Expanded "?" room types

Currently: heart piece Darknut miniboss, +/- rupee NPC, random item chest,
friendly NPC (Zelda). Planned additions:

- **More miniboss types**: same audit as 3.3 (which enemies work as a
  standalone `CreateEnemy` fight), feeding a generalized version of
  `LADDER_KIND_MINIBOSS` that picks from a small roster instead of always
  `DARK_NUT`, each with its own reward.
- **Restricted item pools per room kind**: today's chest pulls from
  `sQuickStartLadderRewardPool` (6 items) unconditionally. This becomes
  several named pools (e.g. "combat reward," "utility item," "quality of
  life") and each ? room kind picks from the pool that fits its theme/
  difficulty, rather than one pool for everything.
- **Puzzle rooms**: a new `LADDER_KIND_PUZZLE`. Needs a concrete puzzle
  mechanic decision - candidates: a pushable-block/switch room (engine
  already has block-pushing and switch objects used elsewhere in the real
  game, likely reusable), a "hit N crystal switches in the right state"
  room, or a timed dash-through room using the same trigger-box technique
  `QuickStartProcessLinks` already uses for the ? room return trip. Needs a
  prototype + a playtest before committing to one - this is the single
  most "needs a human to say whether it's actually fun/solvable" item in
  the whole roadmap.

### 3.5 Score-gated unlock tiers

Bit storage is cheap and already reserved: `gSave.flags` is 512 bytes (4096
bits); the named `Flag` enum only reaches bit 0x65 in bank 0, and this
session's difficulty counter claimed up to bit 177 - `GF_UNLOCK_BASE = 178`
onward in bank 0 is confirmed free and is the reserved range for every
unlock bit this section needs (region unlocks, item unlocks, buff unlocks -
comfortably under the ~78 remaining bits in bank 0 for a first cut; if that
turns out to be too tight, the next bank up needs its own real-flag
occupancy audit before claiming it, the same way bank 0 already was this
session). **Specific bit assignments are deliberately not hardcoded yet** -
they depend on the final region/item lists in 3.1/3.6, which aren't locked
in. What's locked in is the mechanism (a threshold table keyed on
`gSave.meta_xp`, checked the same way `QuickStartGetDifficultyTier` already
turns a scalar into a tier) and the reserved bit range.

Open question for the user: roughly how many wins should it take to unlock
the full 7-region pool and the full item pool? This sets the actual
XP-per-threshold numbers once the score formula's real output range is
known from playtesting (right now the formula in 2.3 produces ~1000-2000
per run in a synthetic test - real full-run values from a human playthrough
are needed before picking thresholds that feel like real progression rather
than unlocking everything after 2 wins or nothing after 20).

### 3.6 First-playthrough vs. unlockable items, and delivery mechanism

Needs a concrete list from the user (or a first proposal for the user to
edit) split into three buckets:

1. **Always available from run 1** (today's entire starter/bonus/skill
   choice pools plus the 9-item shop catalog - already curated this
   session).
2. **Unlocked by `meta_xp` tier**, then folded into an existing delivery
   path - the roadmap doesn't need a new delivery mechanism, just gating
   which of these three existing pools a newly-unlocked item is added to:
   - the starter/bonus/skill choice pools (`sQuickStartStarterItems` etc.)
   - the shop catalog (`sQuickStartShopCatalog`)
   - the ? room reward pools (3.4's restricted pools)
3. **Prerequisite-gated items** (3.7) - conceptually a 4th bucket, but
   mechanically just an extra filter applied to bucket 2's pools.

### 3.7 Item prerequisites and area-gating

Two distinct mechanisms, same underlying shape (a small lookup table
consulted before a reward pool is rolled):

- **Item-requires-item** (Roc's Cape -> Roc's Cape Scroll): a table mapping
  item -> required prerequisite item (or none). Every reward-selection site
  (ladder rewards, region-clear rewards, shop restock) filters its candidate
  list against `GetInventoryValue(prereq) != 0` before rolling.
- **Region-requires-item** (Castor Wilds needs Pegasus Boots or Roc's Cape
  to traverse): a table mapping region -> a short list of "acceptable
  traversal items." When the random region order (3.2) is generated, for
  any selected region with a requirement the player doesn't already own one
  of: inject one of the acceptable items into an earlier reward pool (e.g.
  the region immediately before it, or the hub shop) so it's guaranteed
  obtainable before arrival - not merely likely.

Needs a concrete prerequisite list from the user before this can be more
than a mechanism - which items gate which other items, and which regions
need which traversal item, are content decisions, not engineering ones.

## 4. Implementation order

Roughly in dependency order - each phase should get its own build+commit,
not one giant patch:

1. **~~Storage + scoring foundation~~** - done this session (2.2-2.4).
2. **Region system generalization** (3.1) - refactor Castle Garden/Lon Lon
   Ranch onto the generic table, reverify both still behave identically.
   Highest-leverage single piece of work: every region added after this is
   a data row, not a few hundred new lines.
3. **Boss audit** (3.3) - spend a focused session just finding out which
   enemy IDs can stand in as a boss, before designing anything further
   around them.
4. **Add the 5 remaining regions** (3.1's table + per-region emulator
   surveys), one at a time, each independently verified in the emulator
   before moving to the next - this is the single largest chunk of routine
   work in the whole roadmap.
5. **Region selection + difficulty-by-position** (3.2), once >2 regions
   exist to actually select among.
6. **Score-gated unlocks** (3.5) - mechanism first (generic threshold
   table), specific thresholds once real playtest score data exists.
7. **Item pool split + prerequisites** (3.6, 3.7) - needs the user's
   concrete item lists.
8. **Expanded ? room types** (3.4) - can happen in parallel with 4-7 once
   the boss audit (3) is done, since new miniboss kinds reuse its findings.
9. **Puzzle rooms** (3.4's last bullet) - explicitly saved for last: it's
   the one feature that most needs a working prototype in front of a human
   before more engineering effort goes in.

## 5. Testing strategy

### 5.1 What's reliably automatable in the emulator (mgba Python bindings)

- **Any pure state/math change**: score formula, unlock threshold math,
  difficulty tier weighting, drop-table odds, item price bounds - poke the
  relevant `gSave`/`gRoomVars` memory directly to known values, run a few
  frames, read back the result. This is how 2.3/2.4 were verified this
  session and is by far the most reliable technique available - it doesn't
  depend on scripted combat succeeding.
- **Room transitions, spawn positions, containment boxes**: walk-and-check
  via scripted input, screenshot comparison. Proven reliable all session
  (camera fix, shop NPC placement, ladder room setup).
- **Persistence across `DoSoftReset`**: proven reliable this session
  (2.2-2.4) - poke pre-state, drive the win sequence via memory pokes,
  mash through the reboot (`DoSoftReset` re-runs the *entire* boot/title
  sequence - the same ~200-iteration A+START mash a cold boot needs, not a
  short passive wait; this cost real debugging time this session and is
  worth remembering for every future win-condition test).
- **Text display correctness**: screenshot + read.

### 5.2 What's historically NOT reliable to automate (established this
### session, still true)

- **Scripted bot combat** (mashing attack near enemies to force kills): this
  session's own drop-rate verification attempts all failed for this reason -
  enemies didn't reliably take damage or die from a naive input script, and
  writing `health = 0` directly doesn't trigger real death/loot logic (it
  silently resets). Anything whose verification *requires* an enemy to
  actually die via real combat (not a memory poke standing in for "it died")
  should be treated as **needs a human playtest**, not re-attempted with a
  slightly different bot script. This applies directly to:
  - Whether a new boss encounter is actually beatable/well-tuned.
  - Whether enemy density at a new difficulty tier feels fair, not just
    "spawns without crashing."
  - Puzzle room solvability/intuitiveness - inherently a "does a human find
    this fun and clear" question, no memory poke substitutes for it.
- **Overall pacing across a full run** (does difficulty escalation feel
  right region-to-region, does a full run take a reasonable amount of time) -
  needs a human playing start to finish, ideally more than once as content
  is added.
- **Subjective balance calls** in general: exact score thresholds, exact
  drop-rate numbers, exact enemy density curves. Code review + the automated
  checks above confirm the mechanism *works as coded*; only playtesting
  confirms it *feels right*. This mirrors exactly how this session already
  handled the enemy drop-rate change (implemented and code-reviewed, but not
  statistically re-verified, once bot combat proved unreliable) - not a new
  problem, a known and accepted limitation of this testing setup.

### 5.3 Suggested per-phase split

| Phase | Automatable now | Needs your playtest |
|---|---|---|
| Region generalization refactor | Yes - identical behavior to today, verify via existing screenshot/memory-poke tests | Spot-check it still *feels* like the same two regions |
| Boss audit | Partially - crash/no-crash and "does it move/attack at all" per candidate | Whether any candidate is actually a fun/fair fight |
| New regions (enemy spawns, containment, reward) | Yes - same techniques as Castle Garden/Lon Lon Ranch | Difficulty/density feel once real combat is involved |
| Region selection + difficulty curve | Yes - the selection/shuffle logic and tier math | Whether the curve across 4 regions feels right |
| Unlock thresholds | Yes - mechanism and math | Whether unlock *pacing* (wins-to-unlock) feels right |
| Puzzle rooms | Only "does it not crash" | Nearly everything else |

## 6. Open questions for the user

1. Roughly how many wins should it take to unlock the full region/item pool?
   (Needed to convert the score formula's real output into unlock
   thresholds - see 3.5.)
2. Concrete first-playthrough item list vs. unlockable item list (3.6) -
   this roadmap can propose a first cut, but the split is fundamentally a
   content decision.
3. Concrete item-prerequisite and region-traversal-requirement lists (3.7) -
   the Roc's Cape Scroll and Castor Wilds/Pegasus Boots examples given are
   understood as illustrative; the full list needs to come from the user.
4. Preferred puzzle mechanic (3.4) - pushable blocks, switches, timed dash,
   something else - to prototype first.
