# 08. Performance: TMC's measured walls

The brief asks for max enemies, events and graphics. These numbers were
measured on the current ROM with the tools in `tools/quickstart/`. Read
`docs/QUICKSTART_BUDGET.md` for the full study.

**These are TMC's ceilings, the ones the new engine must beat.** The new
engine is built from scratch (`12_FROM_SCRATCH_ENGINE.md` §3 has the design
and its budget). The fixes suggested below for TMC itself are superseded
there. The measurements, and the reasons each wall exists, still hold.

## The walls, in the order you hit them

| wall | size | first symptom |
|---|---|---|
| **OBJ GFX slots** | 44 x 0x200 bytes, 4 reserved for palettes, **40 usable** | spawns fail. Enemies arrive late or not at all |
| **entities** | 72 game-wide, refused at 71 | a death cannot spawn its DEATH_FX: the enemy freezes for 255 frames and drops nothing |
| **dynamic OBJ palettes** | 9 (slots 6-14) | a sprite draws in palette 0, the player's colors. No error |
| **CPU** | about 280,896 cycles a frame | the game slows: missed VBlanks |
| OAM | 128 hardware sprites | sprites vanish |
| EWRAM | about 31 KB free | |

**For ordinary content the GFX table is the binding limit, not the CPU.**
Every wave, boss and escort combination measured held full speed,
including 46 live enemies, and a boss with a six-Wizzrobe escort. Only Acro
Bandit gangs (6 entities per placement) ever dipped, to 0.92.

## Why the GFX table runs out: swap versus fixed sheets

`src/vram.c`:

- **`LoadFixedGFX(entity, gfxIndex)`** loads a whole sheet once and shares
  it. A second entity with the same `gfxIndex` finds the loaded slot and
  bumps its reference count. N instances cost the sheet once.
- **`LoadSwapGFX(entity, count, slot)`** reserves slots **per entity**, and
  the entity streams its current animation frame into them. N instances
  cost N slots.

**Most enemies use fixed, shared sheets.** Of 213 enemy forms
(`data/enemies.csv`), 172 are fixed, 36 swap, 4 have none and 1 reuses
common art. Measured in the ROM (Oct 2026, slots each live instance points
at, with a two-kind control that showed two slots):

| kind | sheet | instances | slots held |
|---|---|---|---|
| Octorok | fixed | 1 / 6 / 8 | 1 sheet of 3 slots, every time |
| Keese | fixed | 12 | 1 sheet |
| Bow Moblin | fixed | 1 / 6 | 1 sheet of 8 slots, every time |
| Stalfos | swap | 1 / 6 | 8 / 18 slots used (+2 per instance) |
| Keaton | swap | 1 / 6 | 7 / 12 slots used (+1 per instance) |
| Darknut | swap | 1 / 4 | 8 / 14 slots used (+2 per instance) |

So the GFX cost of a wave is **the sum of its distinct fixed kinds' sheet
sizes plus a per-instance price for each swap-kind enemy**. The roster's
`cost` field is the per-kind sheet price. An earlier handoff note said
every live enemy holds its own slot, so 19 of one kind hold 19 slots. That
is true only of the swap kinds, which in QUICKSTART's roster are Stalfos,
Keaton, Gibdo, Scissors Beetle, Darknut, the Ball and Chain Soldier,
Madderpillar, Lakitu and ENEMY_4D.

The trade between the two:

| | swap (per instance) | fixed (shared) |
|---|---|---|
| VRAM per instance | the current frame only | nothing after the first |
| VRAM for the kind | one frame per instance | every frame of every animation |
| best for | big sprites with many frames, few on screen | small sprites with few frames, many on screen |

A 16x16 frame at 4bpp is 128 bytes, so one slot holds 4 frames. The
lesson for a new engine: hordes want small, shared, resident frame sets.
Streaming frames per instance is for big sprites with many frames, of
which only a few are on screen.

The sheet kind is the `gfx` field of `EnemyDefinition`: 0x8000 common art,
0x4000 swap (slot count in bits 4-11), otherwise a fixed sheet index into
`gFixedTypeGfxData` (`LoadEnemySprite`, `src/enemyUtils.c`).

**The reaper is slow.** A sheet nobody uses anymore sat at reference count
0 for a **median 663 frames** (11 seconds) before it was freed. Vanilla
compacts only when slots run out, and QUICKSTART's reserve reaper runs one
frame in 64. So a freed sheet is not free capacity for ~10 seconds, and
spawn gates read stale counts. Loading happens in the spawn burst, which
is where failures live.

**Slots in status 3 (`GFX_SLOT_FOLLOWER`) look free and are not.** They are
the tails of multi-slot sheets.

**NPCs cost sheets too.** Every distinct NPC id is a sheet, and some cost
two (`LoadExtraSpriteData`). Lon Lon Ranch topped out at 4 reclaimable
slots. Keep the cast small.

## Entities

72 entities cover everything: player, items, effects, props, enemies,
projectiles, drops.

- A death is **two entities for a moment** (the enemy plus its
  DEATH_FX).
- **Projectiles count**, and the live-enemy count does not see them.
  Twelve Pestos with twelve dirt balls hit 71 of 72.
- **Floor drops** live 600 frames each. QUICKSTART caps them at 8
  (`FLOOR_DROP_CAP`).
- Multi-entity enemies: a Madderpillar is about 7, an Acro Bandit
  placement 6.
- QUICKSTART keeps a reserve of 16 (`QUICKSTART_ENTITY_RESERVE`) and evicts
  on the death path.

To fit more enemies: cap projectiles per kind, shorten drop lifetimes,
pool effects, and **price enemies in entities** the way the roster prices
them in slots.

## Palettes

Nine dynamic OBJ palettes (6-14). Each enemy kind and color form needs one.
A failed load falls back to palette 0 silently. An entity created this
frame has not loaded its palette yet, so the free count reads high in a
burst (`QuickStartFreeObjPalettes` counts those as pending).

For the re-skin: **design enemies to share palettes.** Give each area theme
2-3 enemy palettes and draw every enemy in that area from them. Then nine
slots are plenty.

## CPU: where the frame goes

Profiled on North Hyrule Field (`pc_profile.py`, a PC sampler that
attributes each sample to its source object):

| share | what | cuttable? |
|---|---|---|
| **40%** | m4a mixer (IWRAM) | only by the audio settings below |
| 6.6% | `src/game.o` (the mode) | some. The hot spots are flag reads |
| 6.4% | `src/movement.o` | no: entity movement |
| 4.5% | `src/playerUtils.o` | no: the player |
| 3.7% | `src/entity.o` | no: list housekeeping |
| 3.4% | `src/ui.o` | only by dropping HUD elements |
| 3.1% | engine IWRAM code plus interrupts | no |
| 3.0% | `GravityUpdate` (asm) | scales with entity count |
| 2.6% | m4a ROM half | with the audio settings |
| ~4% | enemy AI | scales with enemy count |

### Audio is the biggest dial

The mixer rate is a compile-time constant in `m4aSoundInit`
(`SOUND_MODE_FREQ_15768` in vanilla). Cost scales with rate, because m4a
mixes rate/60 samples per channel per frame.

| mixer rate | instructions per frame | vs vanilla |
|---|---|---|
| 15,768 Hz (vanilla) | 74,792 | |
| 13,379 Hz | 71,160 | -4.9% |
| 10,512 Hz | 66,101 | -11.6% |
| 7,884 Hz | 61,291 | -18.1% |

Whole builds, North Hyrule Field walking:

| build | instructions per frame | worst frame |
|---|---|---|
| before the optimisation pass | 81,240 | 138,056 |
| default after it | 64,205 (-21%) | 85,200 |
| `audiolight`: 4 channels, no reverb, 13,379 Hz | 52,936 (-35%) | 65,800 |
| `audiomin`: the same at 7,884 Hz | 42,224 (-48%) | 51,632 |

At `audiomin` the worst frame uses about 155,000 of 280,896 cycles, about
half. **Decide the audio budget first.** Fewer channels, no reverb and a
lower rate buy more CPU than any game-logic optimisation. Composing
music for 4-5 channels at 10-13 kHz is the cheapest path to big enemy
counts.

### Code habits that cost real time

QUICKSTART cut its own share from 20.5% to 6.8% of the frame by:

- **Never sweeping per frame what changes per room.** A per-frame sweep
  of 15 regions' flag bits was 4.5% of the frame. A per-frame fuser
  table walk was another chunk. Both became once per room visit, latched.
- **Throttling hooks that clean up after load** to one frame in four.
- **Making a failed spawn cheap.** An empty wave deal retries every
  frame by design. A palette rule that refused every kind made each
  frame pay a full deal: Hyrule Town fell to 15 fps with nothing on screen.
  Refuse up front.

For the new game:

- Put hot per-entity loops in IWRAM as ARM code, as vanilla does for
  `ram_UpdateEntities`, `GetTileAtEntityPos` and the collision helpers
  (`linker.ld`, "ARM functions copied to IWRAM").
- Keep enemy AI on its own timers. Many vanilla AIs already think every
  N frames.
- Generation runs inside fades, never during play.
- Flags are bit reads through routing code. Cache what you read every frame.

## Graphics headroom

| resource | vanilla use | notes |
|---|---|---|
| BG layers | 4: HUD, top, bottom, background | all used. Generated rooms keep the same layout |
| BG VRAM | 64 KB | tileset art per area theme, streamed at room load |
| OBJ VRAM | 32 KB, GFX slots from 0x06012800 | the first 10 KB hold the player, items and HUD sprites |
| BG palettes | 16 x 16 colors | per tileset |
| OBJ palettes | 16 x 16, 0-5 fixed, 6-14 dynamic | |
| affine sprites | used by bosses and effects | expensive in OAM matrices |
| blending and windows | darkness (`lightType`), fades | the torch rooms use the window for light |

**Darkness costs nothing extra.** It is a window plus a level dial.

## The measurement tools

| tool | measures |
|---|---|
| `cpu_probe.py` | lag ratio: game frames per video frame |
| `pc_profile.py` | where the frame goes, by function and object |
| `fps_probe.py`, `perf_census.py` | frame rate per room and cast |
| `gfx_trace.py` | every GFX slot over time |
| `gfx_floor.py` | free slots per room per difficulty, about a minute a room |
| `measure_budget.py` | the whole sweep |
| `shf_probe.py` | entities and palettes under a kill stream |
| `roster_soak.py`, `pursuer_soak.py` | long soaks of one kind |

A measurement mailbox at 0x0203FF00 lets the ROM publish counters the
probes read.

**Run `gfx_floor.py` after anything that adds a sprite or spreads
spawns.** A baseline before your first change has saved sessions: several
"regressions" were pre-existing conditions nobody had a baseline for.

## A target budget, if TMC's engine were kept

Superseded by `12_FROM_SCRATCH_ENGINE.md` §3 for the new engine. Kept as
the measured envelope of TMC itself:

| budget | value |
|---|---|
| audio | 5 channels, no reverb, 13,379 Hz (`audiolight`-like) |
| enemy kinds per room | 3-4, few swap-sheet instances |
| live enemies | 24-32 chaff on fixed sheets, plus 2-4 heavies |
| entity reserve | 16 |
| projectiles | capped per kind |
| floor drops | 8 |
| OBJ palettes | 2-3 per theme for enemies, 2 for NPCs |
| GFX reserve | 4 slots |
| NPC faces per room | 2 |

Prove each with a soak probe before it goes in the tables.
