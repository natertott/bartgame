# 02. Player and movement

All vanilla. **This is the spec the new engine reproduces**: every speed,
state, surface and edge case here is what "plays like TMC" means. Struct
offsets and function names are only there to find the code to port.
`12_FROM_SCRATCH_ENGINE.md` §2 adds the timings (roll phases, arcs,
knockback, item speeds), and `data/player_animations.csv` the animation
cues that drive them.

Source: `src/player.c` (the state machine), `src/playerUtils.c` (surfaces,
respawn, ledges, the room tileset loader), `src/item/*.c` (item use),
`src/playerItem/*.c` (the entities items spawn), `include/player.h`.

## The player entity

`gPlayerEntity` (0x03001160) is a `PlayerEntity`: a normal `Entity` (0x88
bytes, see `04_ENTITIES_ENEMIES_OBJECTS.md`) of kind PLAYER (1). Its state
beyond the entity is `gPlayerState` (`PlayerState`, `include/player.h`).

`gPlayerState` fields that matter most:

| offset | field | use |
|---|---|---|
| 0x02 | jump_status | 0x81 on a ledge jump |
| 0x05 | heldObject | lifting or carrying |
| 0x0d | direction | input direction this frame |
| 0x12 / 0x13 | floor_type, floor_type_last | the `SurfaceType` under the player |
| 0x16 / 0x18 | startPosX/Y | room entry point |
| 0x1b | sword_state | charge, spin, beam |
| 0x1c | gustJarState | `PL_JAR_*` |
| 0x1e | dash_state | Pegasus Boots |
| 0x26 | swim_state | 0x80 diving |
| 0x30 | flags | `PL_*` (below) |
| 0x3c | killed | non-zero when dead |
| 0x40 | path_memory[16] | the last safe tiles. Respawn after a fall or drowning picks from here |
| 0x80 | speed_modifier | |
| 0x90 | playerInput | held and new input bits |
| 0xac | skills | `SKILL_*` bitfield |

## The state machine (`gPlayerEntity.base.action`)

| # | action | # | action |
|---|---|---|---|
| 0 | INIT | 16 | PULL |
| 1 | NORMAL | 17 | LAVA |
| 2 | DUMMY | 18 | WARP |
| 3 | FALL | 19 | (0x08072454) |
| 4 | JUMP | 20 | DROWN |
| 5 | PUSH | 21 | USEPORTAL |
| 6 | BOUNCE | 22 | TALKEZLO |
| 7 | (kinstone fusion start, L) | 23 | ROOMTRANSITION |
| 8 | ITEMGET | 24 | ROLL |
| 9 | MINISH | 25 | (0x080728AC) wait for scroll, respawn |
| 10 | MINISHDIE | 26 | INHOLE |
| 11 | (0x08071DB8) | 27 | (0x08072C9C) |
| 12 | EMPTYBOTTLE | 28 | SLEEP |
| 13 | FROZEN | 29 | CLIMB |
| 14 | (0x0807204C) | 30 | USEENTRANCE |
| 15 | ROOM_EXIT | 31 | PARACHUTE |

`PLAYER_NORMAL` is where walking, attacking, item use and surface handling
happen. Every other state is a scripted interlude that returns to NORMAL.

### Player flags (`gPlayerState.flags`)

| flag | value | flag | value |
|---|---|---|---|
| PL_BUSY | 0x1 | PL_PIT_IS_EXIT | 0x8000 |
| PL_DROWNING | 0x4 | PL_GYORG_FIGHT | 0x20000 |
| PL_NO_CAP | 0x8 | PL_ROLLING | 0x40000 |
| PL_CAPTURED | 0x10 | PL_MOLDWORM_CAPTURED | 0x80000 |
| PL_USE_PORTAL | 0x20 | PL_IN_HOLE | 0x100000 |
| PL_HIDDEN | 0x40 | PL_MOLDWORM_RELEASED | 0x200000 |
| PL_MINISH | 0x80 | PL_CLONING | 0x400000 |
| PL_DISABLE_ITEMS | 0x100 | PL_USE_LANTERN | 0x800000 |
| PL_FALLING | 0x200 | PL_PARACHUTE | 0x1000000 |
| PL_BURNING | 0x400 | PL_CONVEYOR_PUSHED | 0x2000000 |
| PL_FROZEN | 0x800 | PL_ENTER_MINECART | 0x4000000 |
| PL_IN_MINECART | 0x1000 | PL_SWORD_THRUST | 0x8000000 |
| PL_DRUGGED | 0x4000 | PL_USE_OCARINA | 0x10000000 |
| | | PL_CLIMBING | 0x20000000 |

### Skills (`gPlayerState.skills`)

SPIN_ATTACK 1, ROLL_ATTACK 2, DASH_ATTACK 4, ROCK_BREAKER 8, SWORD_BEAM
0x10, GREAT_SPIN 0x20, DOWN_THRUST 0x40, PERIL_BEAM 0x80, FOURSWORD 0x100,
FAST_SPIN 0x200, FAST_SPLIT 0x400, LONG_SPIN 0x800.

## Speeds and physics (`src/player.c` lines 35-56)

All speeds are Q8.8 pixels per frame at 60 fps.

| constant | value | px/s |
|---|---|---|
| kWalkSpeed | 1.25 | 75 |
| kWalkSpeedRolling | 2.0 | 120 |
| kWalkSpeedGustJar | 0.5 | 30 |
| kWalkSpeedShield | 0.75 | 45 |
| kWalkSpeedSwordCharge | 0.875 | 52.5 |
| kWalkSpeedBurning | 3.0 | 180 |
| kWalkSpeedSlopeSubtractor | 0.3125 | |
| kJumpSpeedForward | 1.0 | |
| kJumpSpeedHoleForward | 0.46875 | |
| kJumpSpeedHoleZ | 1.625 (Q16.16) | |
| kBounceSpeedForward | 1.0 | |
| kBounceSpeedZ | 2.0 (Q16.16) | |
| kPushSpeed, kPullSpeed | 0.5 | |
| kGravityRate | Q8.8(32) | |
| kFallDamage | 2 quarter-hearts | |

**Movement pipeline.** `ProcessMovement*` (`src/movement.c`) calls
`CalculateEntityTileCollisions` and then `ProcessMovementInternal(e,
speed, dir, collisionType)`. It steps along `gSineTable[dir * 8]` and
resolves the result against the collision bytes of the current
`collisionLayer` (see `03_WORLD_TILES_COLLISION.md`). `GravityUpdate` (asm)
integrates z. Each mover passes its own `collisionType`, which is how a
flyer ignores water and a Minish-sized player fits through gaps.

**Layers.** `collisionLayer` is 1 (bottom) or 2 (top), and 3 means both.
Stairs and some act tiles switch layer (`UpdateCollisionLayer`,
`ResolveCollisionLayer`). Bridges over walkways are two-layer maps.

## Surfaces

Every frame in NORMAL, the act tile under the player maps to a
`SurfaceType` (`src/data/mapActTileToSurfaceType.c`). The surface's
`SurfaceAction_*` runs (`src/playerUtils.c` around line 760).

| act tile | surface | effect |
|---|---|---|
| 0x0d | PIT | fall (PLAYER_FALL) |
| 0x0f | SHALLOW_WATER | splash, slows |
| 0x0e | SLOPE_GNDWATER | wade-in edge |
| 0x10 | WATER | swim with Flippers, else drown and respawn |
| 0x12 | ICE | slide |
| 0x13 (swamp) | SWAMP | sink unless moving. Boots or Cape cross it |
| 0x16 | DUST | dust cloud |
| 0x19, 0xf0 | HOLE | falls into a hole transition (below) |
| 0x1b, 0x1d | BUTTON | press |
| 0x26, 0x27 | SLOPE V/H | slow on slopes |
| 0x28, 0x29 | DOOR | door transitions fire here |
| 0x30-0x33 | SURFACE_22 | unnamed in the decomp. Verify in the ROM before using |
| 0x5a | SURFACE_1C (lava) | lava splash, burn |
| 0x53, 0xf1 | LADDER / AUTO_LADDER | climb, switch layer |
| 0x50 | CLIMB_WALL | Grip Ring climbing |
| 0x74 | EDGE | |
| 0x08 | (crumbling floor) | turns into a pit once walked on |

## Ledges (one-way jumps)

`sub_08079550` (`src/playerUtils.c` around line 2026) starts a ledge
jump. The player must be walking straight in their facing direction. Both
tiles at the front corners of the hitbox must carry a **ledge act tile
valid for that direction** (`gUnk_0811C1E8`). Then, after more than 5
frames of pushing (at once when dashing), the player goes to PLAYER_JUMP.
Collision is off for the arc.

| facing | jump act tiles (decimal) |
|---|---|
| north | 43, 65, 78, 76 |
| east | 44, 66, 76, 77 |
| south | 42, 64, 79, 77 |
| west | 45, 67, 78, 79 |

76-79 are corners, valid from two directions. The table's value is the
landing `animationState + 1`. The decomp's `mapActTileToSurfaceType.c`
maps 42-45 and 64-75 to surfaces it names `SurfaceAction_Conveyer*`
(SURFACE_D, E, F and 0x10). Those names are the decomp's guesses. The
same tiles are the ledge set, so check what they do in the ROM before
building conveyors from them.

**This is the most important movement fact for procgen.** A ledge is a
one-way edge in the room graph. A flood fill over collision cannot see
it, because the ledge tile is solid from below and passable from above
only as a jump. A generator that places ledges must record them as
**directed edges**. QUICKSTART lost two sessions to "sealed pocket"
findings that were really ledges (`tools/quickstart/component_map.py`
walks the player off every boundary tile to find them).

## Falling, holes and respawn

- **A plain pit** (act 0x0d): PLAYER_FALL, then `RespawnPlayer` at a
  `path_memory` tile, then `kFallDamage`.
- **An exit pit**: `PL_PIT_IS_EXIT` set. The fall changes room instead of
  respawning.
- **Hole transitions** (`src/manager/holeManager.c`, `gHoleTransitions`
  rows): a box of tiles that sets `PL_PIT_IS_EXIT` and calls
  `DoHoleTransition` to a target area, room and position. The well in
  Hyrule Town is one.
- **Trap.** If anything cancels a hole's room transition after the fall
  starts, the player stays in PLAYER_FALL, undrawn, forever. QUICKSTART's
  containment did exactly this (the inn and well freeze). Every
  generated hole needs a valid target, or no hole at all.

## Room transitions as the player sees them

- **Borders**: walking off a room edge. `CheckRoomExit` finds the
  `WARP_TYPE_BORDER` transition whose edge and span match, and the camera
  scrolls if the next room is in the same area.
- **Doors and stairs**: the player stands on act tile 0x28 or 0x29 inside
  a `WARP_TYPE_AREA` transition box. The game fades and loads the target.
  `PLAYER_USEENTRANCE` and `ROOM_EXIT` animate it.
- **The rule the user set for the current game**: only vanilla door
  mechanics. A door is the act tile plus a transition row. Never a
  position trigger.

## Items in hand

Equipped items run through `src/item/item*.c` (button handling and player
animation) and spawn `PLAYER_ITEM` entities (`src/playerItem/*.c`, kind 8)
that carry the hitbox.

| item | file | what it does to the world |
|---|---|---|
| Sword | itemSword.c, playerItemSword.c | cuts grass and bushes (act cut), hits enemies. Charge gives a spin. Skills add beam, roll, dash and the rest |
| Shield | itemShield.c | blocks from the facing direction, reflects some shots |
| Bombs | itemBomb.c, playerItemBomb.c | break bombable walls (act 0x2e), stun, damage |
| Remote Bombs | same | detonate on command |
| Bow / Light Arrow | itemBow.c | arrows hit switches, eyes, enemies |
| Boomerang / Magic | itemBoomerang.c | stuns, fetches items, hits switches. Required to hurt Spark |
| Lantern | itemLantern.c | lights torches (tile type 117 to 118), burns webs, lights dark rooms |
| Gust Jar | itemGustJar.c | sucks dust and webs, pulls enemies, launches held objects |
| Cane of Pacci | itemPacciCane.c | flips enemies and pots, launches from holes. Required to hurt Lakitu |
| Mole Mitts | itemMoleMitts.c | dig soft earth (act 0x0d) and wall faces (act 0x56) |
| Roc's Cape | itemRocsCape.c | jump over pits and water |
| Pegasus Boots | itemPegasusBoots.c | dash, cross swamp, break some walls with a dash |
| Fire Rod | itemFireRod.c | fireballs |
| Ocarina | itemOcarina.c | warp. QUICKSTART uses it to fly home to the hub |
| Bottles | itemJarEmpty.c | catch fairies, potions |
| Grip Ring | (passive) | climb walls (act 0x50) |
| Power Bracelets | (passive) | push and lift heavy blocks. QUICKSTART gives them every block size, no clones |
| Flippers | (passive) | swim (act 0x10) |

Input: A and B are the two item buttons. R is context (lift, push, roll). L
is the kinstone fusion. QUICKSTART added a third item slot on L (input
bit 0x2000).

## The Minish form

The cap's shrink is a full second movement mode: `PL_MINISH`,
`PLAYER_MINISH`, Minish-scale collision types, Minish doors (act 31 and 32)
and portals (`MINISH_PORTAL_MANAGER`, manager subtype 3, act 0x3d). Minish
rooms are their own areas. Keep it or cut it, but decide up front. It
doubles the number of room scales a generator must reason about.
QUICKSTART's portal ? rooms (`docs/QUICKSTART_PORTAL_POCKETS.md`) used
Minish portals as one-way gates.
