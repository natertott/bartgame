# 12. A from-scratch engine: what to take from TMC, and what to leave

**The decision (from the user):** the new agent builds the engine from the
ground up. It must **play like TMC**: the controls, the player's and
enemies' speeds, the bounce, the roll, fire rates, knockback, the feel.
And it must be built for **the highest performance the GBA allows**, with
a much higher ceiling than TMC for on-screen enemies, sprites,
animations and content.

This document supersedes the "fork the decomp" recommendation that docs
00-11 were first written around. Read it first.

## 1. What the new agent needs to know about TMC

Only three things. Everything else about TMC's engine can be ignored.

| need | why | where |
|---|---|---|
| **1. The feel spec**: every number and timing the player can feel | "plays like TMC" is only true if these match frame for frame | §2 here, `data/*.csv`, `02_PLAYER_AND_MOVEMENT.md` |
| **2. The behavior vocabulary**: what each tile behavior, item verb and enemy does | the game design and the generator speak this language (ledges, pits, water, bombable walls, the Lantern lighting torches) | `02`, `03` (act tiles), `04`, `05` |
| **3. TMC's ceilings**: where its engine runs out, measured | so the new engine does not inherit them | §3 here, `08_PERFORMANCE.md` |

**Not needed**: TMC's struct layouts and offsets, its data formats
(tilesets, LZ77 room maps, sprite frame and OAM lists), its room
property lists and load pipeline, the script bytecode, the m4a sound
engine, the save layout, the decomp's toolchain (agbcc) and its traps.
Those parts of docs 01, 03 and 09 describe *how TMC does it*. They are
reference for reading TMC's source while porting behavior, never a design
to copy.

**The decomp is still the most valuable thing in this repo for the new
agent**, as an oracle:

- **Readable C for every behavior.** `src/player.c`, `src/playerUtils.c`,
  `src/item/*.c`, `src/playerItem/*.c`, `src/enemy/*.c` (103 AIs). Port the
  logic, not the code structure.
- **A running reference.** The mGBA harness in `tools/quickstart/` plays the
  real game. Anything not written down can be measured
  (`tools/newgame/feel_trace.py`).
- **Exact tables, extracted** (`tools/newgame/extract_feel.py`, below).

## 2. The feel spec

### Units

| quantity | unit |
|---|---|
| time | frames at 59.73 Hz. All timings below are frames |
| position | pixels. TMC keeps Q16.16 |
| speed | Q8.8 px per frame (256 = 1 px/frame) |
| z (height) | Q16.16, negative is up |
| direction | 32 steps, N = 0, E = 8, S = 16, W = 24. Movement uses a 256-entry sine table indexed `dir * 8` |
| health | 8 per heart. A new file has 24 (3 hearts). Damage 2 is a quarter heart |

### Player movement (`src/player.c`, measured where marked)

| what | value |
|---|---|
| walk | 1.25 px/f |
| walk while charging the sword | 0.875 |
| walk with the shield up | 0.75 |
| walk with the Gust Jar | 0.5 |
| push and pull a block | 0.5 |
| burning | 3.0 |
| slope penalty | -0.3125 |
| Pegasus dash | 3.0 (Minish 2.5), after a 16-frame wind-up |
| walk animation | 10 keyframes of 3 frames, a 30-frame cycle |
| hitbox | 12x12 box (half-extents 6), centered 3 px above the feet. Minish 4x4 |
| ledge jump | walk into a ledge edge for more than 5 frames (at once when dashing), both front corners on ledge tiles |
| jump forward speed | 1.0 |

### The roll (`PlayerRollInit`/`PlayerRollUpdate`, `ANIM_ROLL`)

25 frames, 11 keyframes (durations 1 3 2 1 5 4 2 2 2 3, then hold). Speed is
driven by the animation's flag cues, not a timer:

| animation phase (flag low bits) | speed |
|---|---|
| 0 | 2.0 |
| 1 | +0.125 each frame |
| 2 | 3.0 |
| 3 | 0 |

The player cannot be hurt by ordinary hits while flag bit 0x10 is set
(early frames). Items become usable again when bit 0x40 is set (the tail).
A hit taken during the roll ends it.

**This pattern is everywhere in TMC: timing lives in animation keyframes.**
The code reads `entity->frame` flag bits set by the current keyframe: hit
windows, speed phases, spawn moments, "animation done" (0x80). So **the new
engine's animation system must carry per-keyframe flag bytes**, and the
player's animation timings must be copied exactly.
`data/player_animations.csv` has all 158 player animations: durations and
cues.

### Gravity and arcs (`GravityUpdate`, asm)

```
z -= zVelocity;            // z negative = up
if (z >= 0) { z = 0; zVelocity = 0; landed; }
else zVelocity -= gravity;
```

| what | zVelocity | gravity | result |
|---|---|---|---|
| default gravity | | 0.125 px/f² (`Q_8_8(32)` in Q16.16) | |
| Roc's Cape jump | 2.0 | 0.125 | about 33 frames airborne, apex about 17 px |
| bounce off a wall | 2.0, forward 1.0 | 0.125 | |
| jump out of a hole | 1.625, forward 0.46875 | 0.125 | |
| other player arcs | 1.0, 1.5, 2.5, 3.5625, 4.5625 by state | some states use gravity / 4 or x 2 | see `src/player.c` |

### Taking damage (`gCollisionMtx`, player body = hurtType 0)

| what | value |
|---|---|
| knockback from a typical enemy contact | 1.5 px/f for 8 frames |
| invulnerability after a hit | 30 frames |
| fire contact | 4 damage, 1.5 px/f for 12 frames, 30 iframes, sets the player burning |
| a fall into a pit | 2 damage, respawn on the last safe tile |
| the hit pause | none. `gMain.pauseFrames` exists, but nothing outside `main.c` sets it |

### Sword and items

| what | value | source |
|---|---|---|
| sword swing | `ANIM_SWORD`: 12 keyframes, 15 frames. Each cue's low 4 bits pick where the blade touches tiles that frame (`gUnk_08129072`), bit 0x20 plays the swing sound, bit 0x40 fires a beam | `data/player_animations.csv`, `playerItemSword.c` |
| sword hit on an enemy | the enemy is knocked back 1.5 px/f for 12 frames, 12 iframes | matrix row for the enemy, column 13 |
| sword damage | by the sword's hurtType, against an Octorok: 0x0d (swinging) 2, 0x08/0x09/0x0a (charged, by sword) 4/6/8, 0x0b/0x0c (thrusts) 4/6 | matrix row 25, columns 8-13 |
| spin charge | 80 frames to charge (40 with Fast Spin) | `src/item/itemSword.c` |
| spin attack | 34 frames | `ANIM_SPINATTACK` |
| arrow | 3.0 px/f (the 0x0e arrow, the Light Arrow, 4.0) | `playerItemBow.c` |
| boomerang | 2.0 px/f for 30 frames out (Magic 2.5 for 60), then returns with a speed ramp | `playerItemBoomerang.c` |
| bomb fuse | 150 frames placed (60 and 15 for other bomb types), then an 80-frame flash | `playerItemBomb.c` |
| sword beam | 3.5 px/f | `playerItemSwordBeam.c` |
| Fire Rod shot | 4.0 px/f | `playerItemFireRodProjectile.c` |
| Pacci shot | 2.0 px/f | `playerItemPacciCaneProjectile.c` |
| throw | `ANIM_THROW` 16 frames | |

### Enemies

`data/enemies.csv` has all 213 enemy forms: health, speed, contact damage
type, hitbox, collision mask, and whether the sheet is shared. A sample:

| enemy | health | speed (px/f) |
|---|---|---|
| Octorok (red) | 2 | 0.375 |
| Keese | 2 | 1.0 |
| Crow | 2 | 1.25 |
| ChuChu (green) | 4 | 0.125 |
| Bow Moblin | 8 | 1.0 |
| Darknut forms 0-3 | 12 / 12 / 20 / 26 | 0.375 |

**AI timing (fire rates, wind-ups, patrols) is decision logic, not a
constant.** Port each AI from `src/enemy/<name>.c`. For example, the
Octorok (`src/enemy/octorok.c`):

- walks for 30, 60, 60 or 90 frames (random), at 0.375 px/f,
- pauses for 24-80 frames (`(Random() & 0x38) + 24`),
- at the end of a walk, if it faces the player (4-way), it spits with
  probability 3/4 (form 0),
- its rock flies at 2.5 px/f.

Measured with `feel_trace.py` against a standing player: 10 shots in 3
minutes, at least 98 frames apart, median 320. That is the number a port
must reproduce. A constant "fires every N frames" would feel wrong.

### The collision matrix (`data/collision_matrix.csv`)

TMC resolves every hit through one table: row = the enemy-side entity's
`hitType`, column = the player-side entity's `hurtType` (body 0, each
sword swing, arrows, bombs...). Each of the 5,220 non-empty cells gives
knockback speed, iframes, knockback duration, damage and confusion for
**both** sides, or names a special handler (shield block, reflect, burn,
freeze, grab). Copy the table as data. It is the most compact form of
TMC's combat feel there is.

### Verifying feel

1. **Same inputs, same trajectory.** Record an input sequence. Play it in
   TMC under mGBA (the harness can feed keys frame by frame) and in the new
   engine. Compare the player's position every frame. With the constants
   above and the same sine table, walking, rolling, jumping and knockback
   should match to the pixel.
2. **Per-enemy traces.** `feel_trace.py ID` against the ported AI's own
   trace: speeds, action durations, shot intervals.
3. **The user plays both.** Doctrine 4: machines test truth, humans test
   feel.

## 3. TMC's ceilings, and what a high-performance engine does instead

Measured on TMC (see `08_PERFORMANCE.md` for the method and tables).

| wall in TMC | measured | the new engine |
|---|---|---|
| **72 entities** game-wide, one 0x88-byte generic struct, everything counts (effects, drops, projectiles) | 71 of 72 in a busy field | per-kind pools with their own capacities (actors, projectiles, particles, pickups). Particles never take an actor slot |
| **44 OBJ GFX slots of 512 B**, allocated at runtime | slots freed a median 663 frames late | VRAM laid out per room at load: every kind's frames resident, so nothing allocates during play |
| **fixed sheets shared per kind; swap sheets cost slots per instance** | 6 Octoroks = 1 sheet; 6 Stalfos = 6x2 slots (measured) | all horde enemies use shared resident frames. Streamed frames only for the player and a few bosses |
| multi-piece sprite frames (7-12 tiles each, several OAM pieces) | | horde enemies as **one 16x16 OBJ** per frame. Bigger enemies as 32x32 |
| **128 OAM entries** (hardware) | | the hard ceiling for sprites on screen. Budget them: 1 per horde enemy, a few per big enemy. Rotate overflow (flicker) by priority. HBlank OAM multiplexing can exceed 128, at real complexity cost |
| sprite pixels per scanline (hardware: about 1,210 OBJ cycles per line, 954 with H-Blank Interval Free) | | about 75 non-affine 16-px-wide sprites can share one scanline. Avoid affine sprites for hordes (they cost about twice as much, plus 10 per sprite) |
| **9 dynamic OBJ palettes**, a failed load is silent | | palettes assigned per room at load: 16 OBJ palettes, fixed for the room |
| **m4a mixer: 37-40% of the CPU** | 15,768 Hz vanilla. -18% CPU at 7,884 Hz | a light mixer: 4-5 PCM channels at 10-13 kHz plus the 4 PSG channels (almost free). Target 10% or less |
| most code is **Thumb running from ROM** (16-bit bus, WAITCNT 3/1 with prefetch) | only a few routines are ARM in IWRAM | the per-actor loops (move, tile collide, animate, build OAM) as ARM in IWRAM. Everything else Thumb in ROM |
| generic per-entity dispatch: `Actions[action](this)` through pointers, every entity every frame | | the same state-machine model, but AI "think" staggered (each actor thinks every 2-4 frames, round robin) while movement integrates every frame |
| entity vs entity: a 16-entry player-side list x every collidable, AABB plus z test, then the matrix | cheap already | keep the asymmetric design (only player-side vs enemy-side pairs) and add a coarse grid when actor counts grow |
| tile collision: per-pixel shape functions per mover type | | 1 byte per metatile, 4 corner probes, shapes as small bitmasks |
| maps: two 64x64 layers in EWRAM, about 48 KB each, plus 32 KB subtile maps each, all rendered at load | | generate per room into a compact metatile map, stream rows and columns into the BG maps as the camera moves |
| agbcc (GCC 2.95, C89), chosen to match Nintendo's binary | | modern `arm-none-eabi-gcc` (devkitARM), `-O2`, ARM for IWRAM code, Thumb for ROM code. The `__umodsi3` trap goes away |

### A budget to design against

The GBA gives 280,896 cycles a frame. This is a planning estimate, to be
replaced by measurements once a prototype runs:

| share | budget | for |
|---|---|---|
| audio | 10% (28k cycles) | the light mixer above |
| scroll, BG streaming, DMA setup | 5% | |
| the player | 5% | |
| HUD, logic, generation hooks | 10% | |
| **actors** | about 65% (180k cycles) | at roughly 1,000-1,500 cycles per actor per frame for move, tile collision, animation and OAM build in IWRAM ARM, **about 120-180 actors** |
| headroom | 5% | |

At those counts **the OAM limit (128) binds before the CPU**. So design the
content for it: horde enemies 1 OBJ each, projectiles 1 OBJ (8x8),
particles drawn as shared 8x8 OBJs with a strict cap, or on a BG layer.
For comparison, TMC's measured ceiling was about 46 live enemies, set by its
entity table and GFX slots, not its CPU.

### IWRAM plan (32 KB)

| use | size |
|---|---|
| stack | 2 KB |
| actor hot fields as arrays (x, y, z, vx, vy, vz, state, timer, anim, flags) for 192 actors | about 8 KB |
| hot code (ARM): actor update, tile collision, OAM build, collision grid | 8-12 KB |
| audio mixer buffers and code | 4-6 KB |
| OAM shadow (128 x 8 B) plus affine | 1 KB |
| spare | 3-9 KB |

Cold actor data (AI-specific fields, pointers) lives in EWRAM.

## 4. How the rest of the handoff set reads now

| doc | read it as |
|---|---|
| `02_PLAYER_AND_MOVEMENT.md` | **spec**: the behaviors to reproduce. Ignore its struct offsets |
| `03_WORLD_TILES_COLLISION.md` | **spec** for the tile behaviors (collision shapes, act tiles, ledges, holes, doors) and the area-grid rules. Its load pipeline and "where a generator plugs in" sections describe TMC, and apply only as an example |
| `04_ENTITIES_ENEMIES_OBJECTS.md` | **spec** for the enemy roster, the matrix and the object vocabulary. TMC's limits there are what to beat |
| `05_ITEMS_AND_ECONOMY.md`, `06_CURRENT_GAME_DESIGN.md`, `07_PROCGEN_DESIGN.md` | **design**, engine-neutral. In 07, step 1 of the build order becomes "build the engine's room loader from generated data" |
| `08_PERFORMANCE.md` | **TMC's measured walls**. The fixes it suggests for TMC are superseded by §3 here |
| `01_ENGINE_ARCHITECTURE.md`, `09_ASSETS_AND_RESKIN.md` | **reference** for reading TMC's code. Not a design |
| `10_TOOLING_AND_TESTING.md`, `11_TRAPS.md` | the harness drives TMC as the oracle. The doctrine applies to the new engine unchanged. The toolchain traps apply only to TMC's build |

## 5. Tools added for this

| tool | what it does |
|---|---|
| `tools/newgame/extract_feel.py` | writes `docs/newgame/data/`: `enemies.csv` (213 forms), `hitboxes.csv` (131), `collision_matrix.csv` (5,220 cells), `player_animations.csv` (158). Reads `src/enemy.c` and `src/data/hitbox.c`, and reads the matrix and the animations from the vanilla ROM (`baserom.gba`) |
| `tools/newgame/feel_trace.py ID [FORM] [--at DX,DY] [--frames N] [--csv OUT]` | spawns one enemy beside the standing player in the real game and records it frame by frame: position, speed, action, timer, animation, and every projectile fired with frame gaps |
