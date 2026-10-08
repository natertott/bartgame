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

- **A ROM call that never returns is a freeze, not a hang.** `callrom.call_keep`
  stops after 500,000 instructions and raises; the chain-end probe hit that
  on `QuickStartChainRollStep(1)` and it was real: the roll cost seconds of
  GBA time (the memory-pair test asked per site). Measure with a bigger
  `budget=` before calling anything an infinite loop; `gSave.run_frames`
  frozen across `run_frame` calls is the in-game symptom.
- **`emu.warp` is a transition, and the containments cancel it** when the
  current room is a region room and the target is not a region crossing
  (Castle Garden to anywhere, measured). A plain run whose `scenario_d`
  byte is 0x51 is exempt (`QuickStartProbeWarpsFree`); the chain-end and
  win probes set it right after boot. A warp out of some interiors
  straight to a field room is refused too; hop through a field room.
- **The probe's player dies.** Three hearts, waves respawning around a
  kill-everything cheat: the early chain-end runs ended on the title
  screen (`here()` = (0, 0), action 0). Keep the health byte full and the
  seashell clock running (`chain_end_probe.heal`).
- **`pkill -f <pattern>` kills your own shell** when the pattern appears
  in the command line that runs it (the whole Bash call is one command
  line). Use a bracket in the pattern, `pkill -f "chain_end_prob[e]"`.
- **Game symbols vanish while `make` runs.** `callrom.game_sym` reads
  `build/USA/src/game.o`, which is rewritten mid-build; every ROM-calling
  probe started during a build dies with a KeyError. Wait for the build.
- **Static functions can be inlined away.** `QuickStartRegionGetWaveCount`
  has no symbol at -O2; ask `QuickStartChainStepMet` instead.

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
- **`call_keep` between the frames of a wave still being dealt loses the
  rest of the wave.** A mixed wave lands its kinds on consecutive frames;
  calling into the ROM on the first of them (to flood from the player's
  tile) meant the second kind never arrived and no later wave did either.
  Record what you need (the player's tile) and make the call after the
  run - room geometry does not change.
- **A pool row's own room never runs the site loop.** The room monitor
  runs the region monitor for a named region room and the content-site
  dispatch for everything else, so a site row keyed to a pool row's room
  (Mount Crenel's entrance was one) is a row that never happens. Check
  `QuickStartIsNamedRegionRoom` before adding a site to a region room.
- **Changing the eligible-site set moves every seeded pick.** Retiring
  site 17 moved the memory event's lesson onto site 82 and the memory
  probe failed 3 of 9 on a room that had nothing to do with the change.
  Expect seed-keyed probes to land somewhere new after any site change.
  Retiring site 82 then moved the recital onto site 99, the barrel house,
  where the boot puts the player next to the sprite: a dismiss() that
  pressed A six times blind TALKED to the sprite on the sixth press and
  every object in the room froze behind its textbox (a forged switch hit
  sat unconsumed for 40 frames). `memory_probe.py` now presses only while
  the player's action byte reads message (0x16) or talking (0x7), and the
  blink watch starts from the sequence's own first switch. Never dismiss
  by count. The second form of the same trap, found on Veil Falls: a
  region's first arrival stacks two or three Ezlo hints (the run intro,
  the chain's region line, the element's), each of which only takes A once
  it has finished typing, so twelve blind presses still leave one open.
  Both probes now press A only while `gMessage.state` reads 7 (waiting)
  and stop after thirty quiet frames.
- **The hint banks are addressed by region number, and the number is
  not free.** `gCustomStrings2` lays the region lines at 0-12, the
  compass bank at 13 and the pair bank at 26 + ring*5; inserting a region
  line at 13 shifts every literal index after it (and game.c has dozens).
  A new region goes LAST in `QS_REGION_*` and takes its lines from the
  table's end through `QuickStartRegionHintLine` / `QuickStartPairHintLine`.
- **The extension slots for pool rows 12+ live in 105 bits of scraps.**
  Fourteen bits per slot now; a twentieth pool row (eight slots, 112 bits)
  does not fit without finding another run - `invariant_check.py`'s flag
  audit says what is free.
- **A site table row count is a define.** `sQuickStartRoomContentSites` is
  declared `[QUICKSTART_CONTENT_SITE_COUNT]`; append rows AND bump the
  count, or the build fails on the initializer.
- **`traversal_audit.py` writes nothing without `--md --json`.** Run it
  bare and the docs stay stale while the exit code says 0.
- **`gen_reach.py --check` must be byte-stable across processes.** A set
  iterated for output order made it cry STALE every other run; iterate
  `RINGS` order.
- **`call_keep(QuickStartMarkReachableTiles)` can reset the game.** In
  Trilby Highlands (site 13) a flood call at frame 200 sent the game to
  room (0,0) on the very next frame, with every flag reading zero; in the
  Boomerang cave the same call was harmless. A probe that floods BEFORE it
  kills and waits measures a title screen and reports "the wave never
  came". Flood last, or flood in Python off the collision map
  (`emu.coll_at`, as `multisite2.py` in the scratchpad did).
- **Zeroing an enemy's kind byte is the kill the wave counter believes**;
  a health write leaves some kinds standing. `spawn_audit.py` does this
  between waves.
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
- **A tile flood cannot classify pockets.** Both the ROM's
  `QuickStartMarkReachableTiles` and a 4-neighbour collision flood call
  half of South Hyrule Field unreachable from its landing - one-way ledges
  are walls to a flood. "Not connected to the landing" is not
  "unreachable"; do not retire spawn offsets or regions on that number.
- **Warps out of Castle Garden do not land while Ezlo's hint is on
  screen** - dismiss (A) before the warp, or boot per region with the
  testbed's REGION scenario instead of warping between regions.
- **Writing health 0 does not clear every enemy kind.** The wave-mix probe
  zeroed +0x45 on a gauntlet wave and the same five slots were still there
  900 frames later; zeroing the KIND byte (+0x08) drops the entity from the
  table and the room reads clear. Use the kind byte when the point is "make
  the wave gone", health only when the death path itself is under test.
- **`emu.press` takes `c.KEY_A`**, not the string `'A'`.
- **Entity coordinates**: integer x is at **0x2e** and integer y at **0x32**.
  0x30 and 0x34 are the LOW halves. Writing those moves nothing and reads
  back what you wrote, so the mistake is self-consistent and silent.
- **mgba cannot attach a save file here.** Both `core.autoload_save()`
  and `core.load_save(vfile)` segfault within the first hundred frames of
  the boot, after writing only the EEPROM header. Anything that needs the
  game to READ save state goes through EWRAM instead (`seed.boot_pinned`,
  `scenario.boot` hammer the bytes on every title frame); anything that
  needs a real `.sav` is a user test.
- **`DeleteEntity` through `callrom.call_keep` never returns** on a
  `SHOP_ITEM` (budget exhausted). Shove the entity off screen (write its
  x at 0x2e) or leave the room; a seam deletes every non-persistent entity.
- **`CreateObject` through `call_keep` does not take** - the entity list
  shows nothing afterwards. Spawn through the game's own monitors (set the
  state they read and run frames).
- **Pressing A while carrying a shop prop DROPS it.** A probe's
  "dismiss the textbox" A-presses after a seam put the carry quest's parcel
  on the floor every time and looked like a rebuild failure. Check
  `gMessage.state & 0x7f` before pressing anything.
- **A lift only registers after walking INTO the prop.** Placing the
  player a tile away and pressing R does nothing; hold UP into it for ~16
  frames first, then R (the interaction box has to overlap).

- **Forged contacts prove the handler, not the weapon.** Writing
  `contactFlags = CONTACT_NOW | 4` on a boss piece showed the chuchu's peel
  working in every phase - and a real Four Sword swing arrives as source
  6, which that handler ignored. When a probe forges an input, also record
  what the real input looks like once (`chuchu_contact.py` does), or the
  probe will pass for a blade nobody is holding.
- **Enemy pieces are not updated while the player stands in a textbox**,
  and the boss driver's first 1400 frames were Ezlo's hints. Dismiss text
  before timing anything.
- **A free-roam driver cannot path around a boss family.** Pushing toward
  the nearest piece parks the player against a leg for thousands of
  frames (the Octorok logged 0 swings in 12000). `boss_stall.py` teleports
  beside the body when stuck for 40 frames; that measures the damage
  path, not pathfinding, and says so.
- **mgba's register binding takes int32_t.** `callrom` used to assign
  `v & 0xFFFFFFFF` straight into `cpu.gprs[i]`; the day the reach mask
  grew a bit-31 token, `sim_validate` died with an OverflowError. Registers
  go in through `_s32()` now and results come back masked unsigned.
- **A probe that hardcodes a reach bit is wrong the day a token is
  inserted.** `boulder_probe.py` had `1 << 25` for Trilby's boulder; the
  golden-gate tokens moved every boulder up two. Read `sim.TOKEN_BITS`.
- **A bitmask is only as good as the thing it indexes.** `sim.snapshot`
  took the REGION mask and asked `reach_room_ok`, which indexes NODES,
  about it; every room count came out as ~10 and nobody noticed until a
  report said 161 of 181 rooms were never reached. When a function's
  argument changes meaning (entrance model: regions became nodes), grep
  every caller for what it passes, not just whether it compiles.
- **"Action 4" is not a state name.** The Crenel sprout's action 4 was
  read as "grown" and recorded that way in two documents; it is the seed
  waiting for water. Read the handler before naming a state, and measure
  the thing the state is supposed to produce (here: a climb tile), not the
  state number.
- **A probe that presses a direction through a textbox measures the
  textbox.** The Crenel vine's first probe reported the player stuck at
  the vine top; it was Ezlo's region line. Use the state-aware dismiss
  (`memory_probe.py`, `veilfalls_probe.py`, `crenel_vine_probe.py`) after
  every room change, including scroll seams.
- **`KinstoneSave` has `fuserOffers[128]` between `fuserProgress` and
  `fusedKinstones`.** The fused bitfield is at +0x12D, not +0xAD; a write
  at the wrong offset is silent and `CheckKinstoneFused` keeps saying no.

## 3. Language and toolchain traps (agbcc, C89)

- **A zero-extended byte is "known non-negative" to agbcc, and a signed
  `%` on it becomes `__umodsi3`** - which this libgcc lacks, so the LINK
  fails, not the compile. `(s32)gSave.some_u8 % QUICKSTART_REGION_POOL_SIZE`
  does it; `(s32)Random() % n` does not (sign unknown). Reduce a byte with a
  subtract loop (`QuickStartScenarioRow`) or mask through a u32 call result.
- **An entity's own init can undo what you wrote on its spawn frame.**
  `ItemForSale_Init` -> `AddInteractableObject` clears `interactType`; a
  lift written the frame the prop is created is gone before its Action1
  reads it. Wait for `action == 1`, then write.

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
