# Known issues, recurring traps, and broken probes

Companion to `HANDOFF_GAME.md` and `HANDOFF_STATUS.md`. Section 3 of
`docs/QUICKSTART_ROADMAP.md` is the long-form record; this is the short list
you want in your head before you start.

---

## 1. Broken or untrustworthy probes

**These have failed on their own controls. A result from one of them is not
evidence until you fix the probe.**

| probe | state |
|---|---|
| `boss_region.py` | Reports `engaged NEVER` for Trilby - **and reports the identical line when rebuilt at the previous commit**, so it is the harness, not a regression. It still correctly reports the family composing with five pieces. Its own docstring warns that an open textbox freezes the boss's stage machine; that is the first place to look. **This is the tool the boss allowlist depends on.** |
| `plates_check.py` | The deal leg works; the WALK legs do not. It pins the player's coordinates every frame instead of walking them, and after one long pinned stand the next plate's collision never fires. Labelled in its own header. |
| `los_check.py` | Both legs read "not spotted", control included, so it says nothing about the mechanism. Labelled in its own header. |
| `component_map.py` | Correct but very slow - it walks the player off every boundary tile of every component. Timed out at 600s on Trilby. Budget for it or narrow the room. |

**Three one-off probes written in the last session and discarded**, recorded
so nobody re-invents them:

- Reading `gArea.portal_mode` after warping the player onto a Minish stump:
  returned 0 everywhere *including the negative control*. Struct offsets are
  the likely fault (`include/area.h` has unannotated padding).
- Borrowing a live enemy and rewriting its `id` to `CHUCHU_BOSS` to test the
  boss clamp: the entity does not survive being re-identified.
- Spawning a boss via `QuickStartCreateWaveBoss` with `call_keep` and then
  running frames: the boss does not persist. `callrom` is documented as one
  question per boot, and this is what that costs.

## 2. Harness mechanics that will waste your time

- **`invariant_check.py` takes ~30 minutes** and, if you pipe it through
  `tail`, you see nothing until it finishes and lose the detail. **Redirect
  to a file** (`> /tmp/.../inv.txt 2>&1`) and grep it afterwards.
- **Python buffers stdout to a file**, so a long probe shows nothing until it
  exits. Do not read an empty output file as "it produced nothing".
- **A region intro hint holds a textbox** over the screen and keeps
  `PL_BUSY`. Screenshot probes photograph the textbox and wave probes measure
  a paused game. Press A several times after warping.
- **`pkill -f <something>` can match your own shell** and kill the command
  you are in the middle of. It killed a heredoc before it wrote its file.
- **`callrom.call` is one question per boot - it clobbers the game
  context.** Running frames after it measures garbage: the first dark-room
  probe called `sub_0805BB00` this way, saw `lightLevel` change and the screen
  not, and nearly reported the engine call broken. `call_keep` restores the
  context; use it whenever the game has to keep playing afterwards.
- **An Ezlo line may be open when you warp into a region.** A forced
  `InitItemGetSequence` fired into `PLAYER_TALKEZLO` did nothing and left the
  player stuck with the textbox closed. Dismiss the line (slow A presses,
  wait for action 1 and `gMessage.state` 0) before handing the player
  anything; the game code's own guard is `QuickStartPlayerCanBeHandedItem`.
- **`gEntities` scans do not see aux player entities.** The item-get pair
  (`LINK_HOLDING_ITEM`, `LINK_ANIMATION`) lives in `gAuxPlayerEntities`;
  `entities()` and `QuickStartItemGetCutsceneRunning` both read 0 while the
  pose is on screen. Read the player's action (8 = `PLAYER_ITEMGET`) and
  `gMessage.state` instead.
- **A warp onto a solid tile leaves the player unable to move for the rest
  of that run** - every later `w16` placement reads back fine and the
  player still never walks. Warp onto open ground (`coll_at` == 0) and
  place from there.
- **The Castle Garden -> Royal Valley warp does not land** (`here()` reads
  the poisoned room byte). Trilby -> Royal Valley does.
- **Vanilla Dampe registers as a talk target only after he has been off
  screen once** (`script_DampeOuside` loops on an on-screen check first), so
  a warp beside him is never answered. Land at the maze exit, then walk or
  place.
- **`emu.press` takes `c.KEY_A`**, not the string `'A'`.
- **Entity coordinates**: integer x is at **0x2e** and integer y at **0x32**.
  0x30 and 0x34 are the LOW halves. Writing those moves nothing and reads
  back what you wrote, so the mistake is self-consistent and silent.

## 3. Language and toolchain traps (agbcc, C89)

- **No unsigned `%` by a runtime divisor.** agbcc emits `__umodsi3` and the
  runtime library does not have one, so it fails at LINK time, not compile.
  Mask the value and use signed modulo: `(s32)(x & 0x7fff) % (s32)n`. This
  has bitten twice - both times when a table grew off a power-of-two size.
- **Declarations before statements**, `-Werror`, no `//`-only surprises.
- **No new mutable statics in `game.o`.** Per-room state goes in the
  `QsSetRoomFlag` window; per-run state goes in `gSave`'s QUICKSTART range.
- **Room flag numbers are scattered across 24,000 lines.** `grep "_FLAG [0-9]"`
  before claiming one. Reusing 46 (`QUICKSTART_REMAINDERS_SWEPT_FLAG`)
  silently disabled a wave sweep and corrupted an hour of measurements.
- **Ids come from the build, never a regex over the header.**
  `build/USA/enum_include/*.inc` is what the ROM was compiled against;
  `parse_tables.ITEMS` reads it.

## 4. Hard engine limits

- **72 entities game-wide.**
- **44 GFX sheet slots, and this is the real wall, not RAM.** Every live
  enemy holds its own slot (they arrive through `LoadSwapGFX`, not a shared
  sheet), so nineteen enemies of a *single kind* hold nineteen slots. Every
  distinct NPC id costs a sheet, and some NPCs cost two because they call
  `LoadExtraSpriteData`. `QUICKSTART_GFX_HARD_FLOOR` is 2 and
  `QuickStartRoomEnemyCeiling` now prices against the table rather than room
  area. **Lon Lon Ranch tops out at 4 reclaimable slots** - it is the tightest
  room in the game and any new per-room sheet will show up there first.
  `tools/quickstart/gfx_floor.py` measures one room in a minute.
- Slots in status 3 (`GFX_SLOT_FOLLOWER`) look free and are not - they are
  the tails of multi-slot sheets.

## 5. World-model traps

- **A collision flood cannot see a ledge.** It finds components correctly
  then lies about how they connect. `component_map.py` walks the player off
  every boundary tile instead. Two wrong "sealed pocket" calls came from this.
- **Walkable collision is not land.** Lake Hylia's water is walkable
  collision - a flood happily proposes the middle of the lake. Castor Wilds'
  swamp is the same trap inverted. The **act tile** tells them apart
  (`src/data/mapActTileToSurfaceType.c`); reject 0x0d/0x0e/0x0f/0x10/0x12/0x13
  for anything that must stand on dry ground.
- **"The southwest pocket" is a lie told twice.** Both the Trilby enemy spawn
  table and the Trilby boss arena had comments calling tiles (2,36)-(10,44)
  "the southwest pocket". It is the MID-WEST pocket; the actual southwest
  corner is tiles (1,49)-(13,58). Two separate bugs, same wrong name. Be
  suspicious of positional names in comments and check them against a map.
- **`QuickStartRegionWaveCleared` counts every enemy in the ROOM**, not in
  the player's component. One enemy stranded across water or up a climb wall
  is a region that can never be cleared. This is why Mount Crenel's spawn
  area was not expanded.
- **Transform points are managers, not objects.** `MINISH_PORTAL_MANAGER`
  (manager subtype 3). Two scans that looked only at `object` lines got the
  Minish model wrong in opposite directions before this landed.

## 6. Live gameplay issues, unresolved

- **Trilby boss reaching the southwest** - fixed in code, never witnessed.
- **8 rooms / 18 content sites never reachable** in any simulated run.
- **Royal Valley at 7% reachable, 0.2% of requirements** - honest pricing,
  but effectively dead content.
- **The `ITEM` chain step is dead code in practice** - 0 of 500,000 rolls.
- Three pre-existing `invariant_check` WARNs, unchanged for many sessions:
  Castle Garden's entrance and reward sit on special tile 0x5f; North Hyrule
  Field's and Trilby's exit boxes are clipped by the room edge.

## 7. The one rule that would have caught most of the above

**A probe that finds nothing has proven nothing until a control says
otherwise.** Before reporting that something does not work, point the same
probe at a case known to work. If the control fails too, the finding is about
the probe. A positive result stands on its own; only negatives need the
control.

This is doctrine 8 in the roadmap, it was written after two false findings in
one session, and it has since caught at least four more - including three in
the last session alone.
