# BARTGAME

A Game Boy Advance game built from scratch: a new engine that plays like
*The Minish Cap*, a hero who is half man and half plant, a sewer for a
home, and a blighted wood above it that is a different maze every time.

Loosely after Boorman's *Excalibur*, Bataille's sun and rot, *Slay the
Spire*'s runs and *Zelda*'s rooms. Dark, grungy, medieval, with gold in it.

## The demo

- **The Drain.** You wake in a sewer. The Sage of the Drain explains, the
  Merchant sells heart potions and blightseeds for gilt. The hole in the
  north wall leads up into the wood; the stairs in the wood's first glade
  lead back down.
- **The Blighted Wood.** A 5x5 maze of rooms, generated from a seed rolled
  on the title screen. Every room is a glade, a grove, a ruin, a pond, a
  thicket or a boneyard, full of monsters. Three key gates stand on the
  way to the Heart: a cracked wall, a pale web, a chasm. Their keys, the
  Blightseed Bombs, the Grail Lamp and the Petal Cloak, wait in chests
  that are always reachable before the gate they open. Locked doors on
  the side branches want small keys; the keys sit in rooms that need no
  key. Dead ends hold chests, shrines and three kinds of quest giver.
- **The Blight Heart.** At the deepest glade. Cut it out, take the Grail.

## Controls

| key | action |
|---|---|
| D-pad | walk (1.25 px per frame, like Link) |
| A | sword swing; talk to someone you face; open a chest from below |
| B | the chosen item: set a bomb, swing the lamp, leap with the cloak |
| L | choose the next item |
| R | roll (24 frames, invulnerable for the first 18) |
| Start | the map of the wood |

Walk into a locked door with a key to open it. Push into a ledge for a
moment to drop off it. Pits and water cost a quarter heart and put you
back on the last safe ground.

## Building

```
make            # bartgame.gba, from src/ and the art in art/*.py
make clean
```

Needs `arm-none-eabi-gcc` (any modern one; the code is C, Thumb in ROM),
Python 3 with Pillow (the art pipeline renders the font and the title
with PIL), and `../tools/bin/gbafix` from the decomp's tools for the
header checksum.

## Layout

```
src/            the engine and the game
  crt0.s        boot, IRQ dispatch
  gba.ld        linker script: ROM, IWRAM (.iwram, .bss), EWRAM
  gba.h         registers, types, fixed point
  video.c       VBlank, OAM shadow, palettes, fades
  room.c        the loaded room: two metatile layers, an 8x8 solidity
                grid, BG map rendering, camera, animated tiles
  actor.c       the actor pool, tile collision with corner assist,
                hit boxes, OBJ VRAM sheets
  player.c      Bart: walk, roll, sword, knockback, falls, jumps
  items.c       B and L, keys in doors, thorns under the sword
  react.c       what tiles do when struck, burned, blown up, unlocked
  world.c       the maze: spanning tree, staged gates, key placement
  roomgen.c     a room from a cell: border, doors, features, flood check
  enemy.c       rot beetle, spore bat, blight spitter, gloom slime,
                thorn knight (ports of TMC's AIs and numbers)
  boss.c        the Blight Heart
  objects.c     projectiles, pickups, effects, bombs
  npc.c         the sage, the merchant, the hermit, the nun, the gardener
  text.c        BG0 text, the message box, menus, the HUD
  sound.c       PSG sound effects and a three-track tracker
  game.c        states: title, play, transitions, map, win
art/            pixel art as hex-digit rows: palettes, tiles, sprites,
                HUD tiles, the hub room, the PIL-rendered font and title
tools/
  build_assets.py   art -> build/gen/assets.c with deduplicated tiles
  preview.py        render art to PNG
  probe.py          mGBA harness: boot, keys, RAM by symbol, screenshots
  roomdump.py       render the loaded room from RAM
  critical_path.py  walks the key chain to the Grail: the regression test
  quest_probe.py    the three quests
  perf_probe.py     monsters against the frame
```

## How it is built for speed

- Thumb code in ROM, hot data in IWRAM, the room's maps in EWRAM. No
  libc, no mixer: sound is the four PSG channels.
- Rooms render once into 64x64 BG maps; the camera just scrolls. Tile
  changes rewrite four map entries.
- One actor pool of 96 with per-kind fields; monsters of a kind share one
  sprite sheet loaded at room entry; the hero streams one frame.
- Collision is an 8x8 cell grid derived from tile types at load.

## Testing

Every probe drives the real ROM in mGBA and reads RAM by linker symbol:

```
python3 tools/critical_path.py --boss     # title to win screen, 18 checks
python3 tools/quest_probe.py --seed 0x28c
python3 tools/perf_probe.py
```
