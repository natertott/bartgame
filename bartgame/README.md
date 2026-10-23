# BARTGAME

A Game Boy Advance game built from scratch: a new engine that plays like
*The Minish Cap*, a hero who is half man and half plant, a sewer for a
home, and a blighted wood above it that is a different maze every time.

Loosely after Boorman's *Excalibur*, Bataille's sun and rot, *Slay the
Spire*'s runs and *Zelda*'s rooms. Dark, grungy, medieval, with gold in it.

## The demo

- **The Drain.** You wake in a sewer hall: a waterfall into a basin, a
  channel with a grate bridge, the great round drain, candles and
  banners. The Pale Gatekeeper on her rug explains; the Billious Peddler
  under his red awning sells Healing Petals and Blightseeds for gilt. The
  drain hole in the north wall leads up into the wood; the arch in the
  wood's first glade leads back down.
- **The Blighted Wood.** A 5x5 maze of rooms, generated from a seed rolled
  on the title screen: a growing tree that mostly runs in corridors and
  branches a third of the time, so about half the rooms lie off the way
  to the Heart. Every room is a glade, a grove, a ruin, a pond, a thicket
  or a boneyard, full of monsters. Three key gates stand on the way to
  the Heart: a cracked wall, a pale web, a chasm. Their keys, the
  Blightseed Bombs, the Grail Lamp and the Petal Cloak, wait in chests
  that are always reachable before the gate they open. Locked doors on
  the side branches want small keys; the keys sit in rooms that need no
  key, and no lock ever stands between you and a key item, a key chest or
  the Heart. Dead ends hold chests, shrines and three kinds of quest
  giver.
- **The Blight Heart.** At the deepest glade. Cut it out, take the Grail.

## The look

Grime and glamour, after the concept boards: a chibi flower-child hero
with a round cream face in a ring of orange petals, a green hood and
tunic; the Billious Peddler, purple-hided under a red hood; the Pale
Gatekeeper in a tall violet hat. A forest falling into sickness: a
canopy that goes from blue-black to lit green, dark olive turf with
bright tips, warm soil trails, deep navy water with foam that drifts,
amber lanterns hung in the trees, white and gold stars on the ground,
fireflies; rocks in three shapes sunk in moss and soil on a palette of
their own; and the rot, by depth: stained grass split by glowing cracks
at the second stage, then purple to the walls, pitted, veined with
light, under a mist, with dead black trees clawing up and walls of
old stone lit violet from below, a crystal set in some. Every material has its own 16-color palette and a
dark hue outline, three tones and a gleam, light from the upper left.
The ground is textured turf with hand-placed tufts, flowers and
pebbles; the canopy walls are leaf masses of lit blobs that wrap at the
tile edge, with lanterns and fireflies in the leaves; water has a dark
bank and a drifting foam fringe wherever ground touches it; every
sprite is drawn pixel by pixel with letter legends in `art/*.py`; the
font is a hand-drawn 5x7. `tools/preview.py` renders any sheet or tile
to PNG at 4x.

**The wood's rooms.** Every forest room is 32x24 tiles carved out of
solid canopy: a corridor in from each door, three to five clearings,
and winding paths between them whose width wanders from three tiles to
a squeeze of one, with a soil trail down the middle. A clearing can be
a lake round an island, and a path that meets water runs straight over
it on planks; a river may wander across the room, bridged where the
paths cross it; a dry room may rise, its upper part behind a cliff of
ledges you can drop from, with one ramp back up, and water pours off
the cliff in one or two places into a churned pool below. Trees stand in the
big clearings, bushes and stones narrow the paths without ever closing
them, and a hoard is sometimes dug into the wall behind a bush or a
boulder. Fireflies drift over the living rooms. Set pieces span tiles,
painted whole and sliced: two great trees of 3x4 (one with a hollow in
its trunk, one lopsided with a lantern on its low branch) and roots
over three tiles of turf, two 2x3 trees (one with a lantern hung in
it) and the blight's 2x3 dead tree, a rock wedged in a stump's roots
(2x2), a flower meadow of 3x3
round a flat stone, clover and fairy rings of 2x2, a great boulder of
2x2, a hollow log of 2x1, a lily raft of 2x2 on open water; cliffs end
in capped stones, lakes have rounded corners and banks on every side
the ground touches. No generic boundary is a hard line: grass that
meets water ends in a shore of soil, sand and reeds; grass that meets
the canopy has a verge of shadow and fallen leaves under a wall,
undergrowth against its sides and ferns above a crown; a trail has
grass creeping over its edges; the canopy shows its trunks at the
water's edge. Each is one tile per combination of sides, chosen by the
generator from the tiles around it.

## The interface

- **HUD.** Hearts, the purse and the keys at the top left; three gold
  slots for A, B and L with what each button holds, lit when it holds
  something, the bomb count under the slot that holds the bombs; the R
  hand that lifts; a parchment mini-map of the wood at the top right,
  red where you stand, gold at the Heart.
- **Dialogue.** A speaker's name in gold and a 32x32 portrait beside the
  words. A advances, B hurries the typing.
- **The shop.** A list with icons and prices, a description of the item
  under the cursor, your gilt in the corner. A buys, B leaves.
- **Pause (Start).** Two pages, R turns them. ITEMS: the three buttons
  with what they hold, the row of everything you own; walk it with the
  d-pad and press A, B or L to put the item on that button (the worn
  things, the gauntlet and the relic, only show). THE WOOD: the map with
  its legend, how the three quests stand, your gilt, keys and kills.

## Controls

| key | action |
|---|---|
| D-pad | walk (1.25 px per frame, like Link) |
| A | what A holds (empty to begin with); talk to someone you face |
| B | what B holds: the sword to begin with; or set a bomb, swing the lamp, leap with the cloak |
| L | what L holds: the Bark Shield to begin with. Hold it and the Bloom guards: slower, facing fixed, bites and seeds from the front are turned |
| R | roll while walking (24 frames, invulnerable for the first 18); standing still, lift the bush, small stone or pot you face; throw what you carry |
| Start | the pause menu: the items, then the map |

The Rot Gauntlet from the second lock's chest lifts boulders too. A
thrown thing flies two and a half pixels a frame, breaks on the ground,
a wall or a monster (two hearts of damage for a bush or a pot, four for
a stone) and may leave a heart or a coin. The sword cuts bushes; bombs
break bushes, stones and pots. Walk into a chest from below to open it.
Walk into a locked door with a key to open it. Push into a ledge for a
moment to drop off it. The moment your feet cross into water you go
under where you stand, petals last, rings spreading; into a hole, you
shrink away into the dark. Either costs a quarter heart and puts you
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
  player.c      the Bloom: walk, roll, sword, knockback, falls, jumps
  items.c       B and L, keys in doors, thorns under the sword
  react.c       what tiles do when struck, burned, blown up, unlocked
  world.c       the maze: spanning tree, staged gates, key placement
  roomgen.c     a room from a cell: border, doors, features, flood check
  enemy.c       rot beetle, spore bat, blight spitter, gloom slime,
                thorn knight (ports of TMC's AIs and numbers)
  boss.c        the Blight Heart
  objects.c     projectiles, pickups, effects, bombs
  npc.c         the sage, the merchant, the hermit, the nun, the gardener
  text.c        BG0 text, the message box with portraits, the shop,
                the HUD, the mini-map
  sound.c       PSG sound effects and a three-track tracker
  game.c        states: title, play, transitions, map, win
art/            pixel art as rows of letters mapped to palette indices
  palettes.py   the 16-color palettes, BG and OBJ
  px.py         the painter: legends, outlines, flips, compose, a canvas
                with lit blobs and shaded balls for round things
  tiles.py      metatiles: grass, blight, paths, canopy walls, trees,
                stones, water, gates, chests, the sewer set
  hero.py       the Bloom: 22 frames and the sword
  monsters.py   beetle, bat, slime, spitter, knight, its sword, the boss
  items.py      pickups, key items, effects, projectiles
  folk.py       the five NPCs
  portraits.py  the dialogue portraits, 32x32
  sprites.py    the sheet list, in the engine's frame order
  hud.py        hearts, icons, item slots, the text box frame, the map
  font.py       the 5x7 font
  title.py      the title screen, painted with PIL in 16 colors
  rooms.py      the hub room: the Drain
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
python3 tools/critical_path.py --seed 0x1234 --boss
python3 tools/quest_probe.py --seed 0x28c
python3 tools/lift_probe.py               # roll, lift, throw, boulder, pause menu
python3 tools/guard_probe.py              # the loadout, the water's edge, a hole, the shield
python3 tools/perf_probe.py
python3 tools/roomshots.py out/           # every room of a seed rendered from RAM, and a sheet
```

The delivered ROM passed the critical path on three seeds (0xB4A7,
0x1234, 0x7777), the quests on 0x28c, 0x1234 and 0x3, the hands probe
14/14, and 64 beetles at full speed. The maze generator is also compiled for the host and checked over
twenty thousand seeds without an emulator:

```
make verify-world    # every key item, key chest and the goal reachable
                     # in order, without a lock; all three quests present
```

`build/host/dump.c` prints one seed's maze, `build/host/stats.c` the
averages (path length, side rooms, dead ends, locks, chests).
