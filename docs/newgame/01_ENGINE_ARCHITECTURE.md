# 01. Engine architecture

The engine is the Minish Cap decomp. Everything here is vanilla unless it
says QUICKSTART.

**Reference, not design.** The new engine is built from scratch
(`12_FROM_SCRATCH_ENGINE.md`). Use this document to find your way around
TMC's code while porting behavior and while using TMC as the measuring
oracle. Two parts carry over as rules: generate from a run seed with your
own PRNG, never a shared gameplay RNG (the RNG section), and keep a run
state block for generated rooms (the save section).

## Build and toolchain

| piece | what it is |
|---|---|
| `agbcc` | the original GCC 2.95-era compiler Nintendo used. All C in `src/` builds with it. It is C89 |
| `arm-none-eabi-as/ld` | assembler and linker. `linker.ld` places every section |
| `tools/bin/asset_processor` | extracts assets from `baserom.gba`, converts them and builds them back (see `09_ASSETS_AND_RESKIN.md`) |
| `tools/bin/gbagfx` | PNG to 4bpp/8bpp, palettes, LZ77 |
| `tools/bin/preproc`, `scaninc` | string and include preprocessing |
| `tools/bin/mid2agb`, `aif2pcm` | music and sample conversion for m4a |
| `tools/bin/tmc_strings` | text banks (`translations/*.json` to `USA.bin`) |
| `tools/bin/gbafix` | header checksum |

```
make tools                 # once
make                       # vanilla USA, must match tmc.sha1
make quickstart-d3         # the current mod's shipped build: tmc.gba and tmc-d3.gba
make custom                # CUSTOM=1: build assets from the converted files rather than the baserom
```

`make custom` is the route for a re-skin: it runs `asset_processor build`
on edited assets. See `09_ASSETS_AND_RESKIN.md`.

**C89 under agbcc.** Declarations before statements. `-Werror`. No
`__umodsi3` or `__udivsi3` in this libgcc: an unsigned `%` or `/` by a
runtime divisor fails at **link**, not compile. Use signed values,
`(s32)(x & 0x7fff) % (s32)n`, or a subtract loop. A zero-extended byte
counts as "known non-negative", so even `(s32)some_u8 % n` can turn
unsigned. This has broken the build twice, both times when a table grew
past a power of two.

**A new mod build needs a variant guard.** Objects whose source has
`#ifdef QUICKSTART` do not depend on the flag, so make reuses one built for
another variant. The Makefile's `VARIANT_OBJS` list deletes them before
every variant build. The new game should be its own tree, not a flag, so
this goes away. If you do add flags, keep the list.

## Memory map (measured from `build/USA/tmc.map` and `tmc.elf`)

| region | range | size | use |
|---|---|---|---|
| BIOS | 0x00000000 | 16 KB | SWI calls: `LZ77UnCompVram`, `CpuSet`, `Div` |
| EWRAM | 0x02000000-0x0203FFFF | 256 KB | 16-bit bus, 2 wait states. Maps, save, buffers, music |
| IWRAM | 0x03000000-0x03007FFF | 32 KB | 32-bit, 0 wait. Entities, OAM controls, ARM hot code, the m4a mixer |
| I/O | 0x04000000 | | registers |
| palette | 0x05000000 | 1 KB | BG 256 colors, OBJ 256 colors |
| VRAM | 0x06000000 | 96 KB | BG 64 KB, OBJ 32 KB at 0x06010000 |
| OAM | 0x07000000 | 1 KB | 128 sprites |
| ROM | 0x08000000 | 16 MB | code and data. The current build uses about 14.1 MB, mostly Nintendo assets |

Key RAM symbols:

| symbol | address | notes |
|---|---|---|
| `gSave` | 0x02002a40 | the save file in RAM. QUICKSTART uses 0x22-0x4F and flag banks 11-12 |
| `gMapTop` | 0x0200b650 | MapLayer, 0xC004 bytes (top layer, BG1) |
| `gMapBottom` | 0x02025eb0 | MapLayer, 0xC004 bytes (bottom layer, BG2) |
| `gBG1Buffer` | 0x02021f30 | tilemap staging for BG1 |
| `gGFXSlots` | 0x02024490 | the 44 OBJ GFX slot records |
| `gMPlayTracks` | 0x02036bc0 | music player state |
| `gEndOfEwram` | 0x02038560 | end of static EWRAM use. **About 31 KB of EWRAM is free above it** |
| `gOAMControls` | 0x03000000 | OAM shadow plus sprite draw state |
| `gPlayerEntity` | 0x03001160 | the player, 0x88 bytes |
| `gEntities` | 0x030015a0 | the entity pool |

IWRAM static use runs to about 0x03006960, plus the stack below 0x03007F00.
The free EWRAM matters for the new game. A generated area needs a RAM
exit list, a RAM entity list and generator scratch (see
`03_WORLD_TILES_COLLISION.md`). 31 KB is enough for that if the generator
writes straight into the existing `MapLayer` arrays rather than building a
second copy.

## Boot and the main loop (`src/main.c`)

`AgbMain`:

1. `InitOverlays`, `InitSound`, `InitDMA`, `InitSaveData`, `InitSaveHeader`,
   `InitVBlankDMA`, `InitFade`. Copy the BG palette, `MessageInitialize`,
   `ResetPalettes`.
2. `gRand = 0x1234567`. `SetTask(TASK_TITLE)`.
3. Every frame: `ReadKeyInput`, the soft-reset check, optional pause
   frames, `gMain.ticks++`, `sTaskHandlers[gMain.task]()`, `MessageMain`,
   `FadeMain`, `AudioMain`, then `WaitForNextFrame` (VBlank wait plus DMA
   uploads of the staged BG buffers, OAM and palettes).

Tasks (`gMain.task`): `TASK_TITLE`, `TASK_FILE_SELECT`, `TASK_GAME`,
`TASK_GAMEOVER`, `TASK_STAFFROLL`, `TASK_DEBUG`.

The game task (`src/game.c`, `GameTask`) has states Transition, Init,
Main and Exit. Main has substates: `InitRoom`, `ChangeRoom`, `Update`,
`ChangeArea`, `MinishPortal`, `BarrelUpdate`, `Subtask` (menus, pause and
the kinstone screen run as subtasks).

### One gameplay frame (`GameMain_Update`)

The order matters. Several bugs came from code that ran in the wrong slot.

1. `UpdateTimerCallbacks`. `PausePlayer` if a message box is up.
2. `FlushSprites`, then **`UpdateEntities`** (players, enemies, objects,
   NPCs, items, then managers), then `UpdateDoorTransition`, then
   **`CollisionMain`** (entity against entity, through `gCollisionMtx`).
3. `UpdateScroll`, `UpdateBgAnimations`, **`UpdateScrollVram`** (copies
   the visible map into the BG staging buffers).
4. `DrawUI`, `UpdateManagers`.
5. QUICKSTART's monitors (`QuickStartUpdate` and friends).
6. `DrawUIElements`, `UpdateCarriedObject`, `DrawEntities`.
7. `CheckRoomExit` (borders and door boxes), `CheckGameOver`, `CopyOAM`.
8. Handle `gRoomControls.reload_flags`.

**Trap.** A tile edited after step 3 does not reach the screen in a room
that is not scrolling. `WaitForNextFrame` uploads the stale buffer and
clears the dirty flag. Raise `gUpdateVisibleTiles` and call
`UpdateScrollVram()` yourself after the edit. A generator that edits tiles
live (opening a wall, lighting a torch) must do this.

`ram_UpdateEntities` is ARM code copied into IWRAM. It runs two passes,
entities then managers. Each entity's update is `Actions[super->action](this)`.

## RNG

`Random()` (`asm/src/code_08000E44.s`):

```
gRand = ror(gRand * 3, 13);   // gRand += gRand << 1, then rotate right 13
return gRand >> 1;
```

One global stream. Everything that rolls advances it: enemy AI, drops,
particles. **It is not a seed you can replay.** QUICKSTART keeps a
separate per-run seed (`gSave` QUICKSTART range, `run_seed`) and hashes
it for every draw that must be reproducible (`QuickStartChainHash`). The
new game must do the same: generate every area from a run seed plus the
area index with its own hash or PRNG, never from `gRand`. Then the Python
simulator can replay the exact world (see `07_PROCGEN_DESIGN.md`).

## Fixed-point conventions

| quantity | format |
|---|---|
| entity x, y, z | Q16.16 (`x.HALF.HI` is the pixel) |
| speed | Q8.8 px per frame (0x100 = 1 px/frame) |
| zVelocity | Q16.16 |
| direction | 0-31, N=0, E=8, S=0x10, W=0x18. Bit 0x80 means "not moving". 0xFF means none |
| animationState | 0, 2, 4, 6 = N, E, S, W |
| tile position | `TILE_POS(x, y) = x + (y << 6)`, tile coordinates in a 64-wide grid |

`gSineTable` drives `LinearMoveUpdate`: `dir * 8` indexes a 256-entry sine.

## Scripts (`include/script.h`, `data/scripts/`)

NPCs, cutscenes and many objects run **scripts**: u16 bytecode
interpreted by `ExecuteScript`. A `ScriptExecutionContext` holds the
instruction pointer, a wait counter, an int variable, a condition, and
x/y for movement commands. `gActiveScriptInfo.syncFlags` synchronises
scripts on different entities. `StartCutscene(entity, script)` attaches
one. `StartPlayerScript` drives the player through one.

Scripts are assembled from `data/scripts/**/*.inc` with macros in
`asm/macros/scripts.inc`. QUICKSTART writes custom scripts there too.

For a generated world, keep scripts for NPC dialogue and set-piece
behavior. Drive placement and state from C. A script cannot know where a
generated room put things unless C writes it into the context.

## Text

`TEXT_INDEX(category, index) = (category << 8) | index`. Vanilla banks
are compiled from `translations/USA.json` into `translations/USA.bin` by
`tmc_strings`. QUICKSTART added three C-side banks resolved in `text.c`:
`TEXT_CUSTOM` (0xFE), `TEXT_CUSTOM2` (0xFF) and `TEXT_CUSTOM3` (0xFD). Each
is a `gCustomStrings*[256]` array in `game.c`, and 256 is a hard ceiling per
bank.

For a new game, rewrite the text banks in `translations/*.json` and drop
the custom-bank hack. Use the vanilla pipeline with your own strings. The
message box renders on BG0 with a font in BG0's charblock.

**Generated text.** A hint like "the key is in the room north of the
lake" needs runtime string building. The message system supports
substitution (`SetMessageValueIndex`: rupees and fields 0x14-0x1C). For
anything richer, write a small string builder into a RAM buffer and point
a custom bank entry at it.

## Sound (m4a / MusicPlayer2000)

Nintendo's standard `m4a` engine (`src/gba/m4a.c`, IWRAM mixer).
`BGM_*` and `SFX_*` ids are in `include/sound.h` (447 SFX).
`SoundReq(id)` plays one.

**The mixer is the single biggest CPU cost in the game: 37-40% of a
frame.** Its cost scales with the sample rate, which is a compile-time
constant in `m4aSoundInit`. See `08_PERFORMANCE.md` for the measured
trade-offs. A "max enemies" game should decide the audio budget first.

## Save (`include/save.h`)

`SaveFile gSave` is mirrored to an 8 KB EEPROM in three slots (0x500
bytes each, two copies with checksums, `gSaveFileEEPROMAddresses`).
Layout highlights:

| offset | field |
|---|---|
| +0x22-0x4F | QUICKSTART: chain arrays, scenario bytes, `run_frames`, `run_seed` |
| +0xA8 | stats: health at +0xAA, max health and so on |
| +0xC0 | rupees |
| +0xF2 | inventory (2 bits per item: 0 none, 1 have, 2 have and seen) |
| +0x25C | global flags. Bank 11 at +0x9C0 and bank 12 at +0xA80 are QUICKSTART's |

Room-local state lives in `gRoomVars.flags[52]` (cleared on every room
load) and per-area flag banks in `gSave` (`AreaHeader.flag_bank`).

**For a roguelite with generated areas, a room flag cannot be a fixed bit
number in a fixed area bank.** Room ids are not stable across runs.
QUICKSTART solved this with a window of save bits it maps per run
(`QS_WINDOW` origin 700, `QS_BIT0` 3388) and `QsSetRoomFlag`. The new game
should define its own **run state block** from the start: per-area
generated-room state (chest opened, door unlocked, puzzle solved) indexed
by generated room number. Size it for 10 areas times the max rooms per
area.
