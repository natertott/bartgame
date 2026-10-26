# BARTGAME

A Game Boy Advance game built from scratch: a new engine that plays like
*The Minish Cap*, a hero who is half man and half plant, a sewer for a
home, and a blighted wood above it that is a different maze every time.

Loosely after Boorman's *Excalibur*, Bataille's sun and rot, *Slay the
Spire*'s runs and *Zelda*'s rooms. Dark, grungy, medieval, with gold in it.

## The demo

- **The Drain.** You wake in a sewer hall: a waterfall into a basin, a
  channel with a grate bridge, the great round drain, lanterns and
  banners, and nothing lying about on its slabs. The Pale Gatekeeper on her rug explains; the Billious Peddler
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
- **The mystery rooms.** Two rooms in five have a mouth in a wall: a
  cave's dark arch, a hollow in the trunks, a gap in the brambles. Walk
  in. Behind it is a cave, the hollow of a tree or a thicket of brush,
  small, medium or large, holding one event: six pots, one with a
  prize; a chest; a stranger who sells a piece of heart for ten gilt;
  a spring that fills the hearts; waves of monsters, or a survive-the-
  clock, or a knight captain, behind a way out that shuts until it is
  won; stone plates to step on; censers to light; boulders to lift.
  Every won fight or solved room leaves a chest: ten gilt in a small
  room, a piece of heart in a medium one, a small key and twenty gilt
  in a large one. The small rooms deal the quiet kinds and the
  gauntlets; the captain, the plates, the censers and the boulders need
  the floor of a medium or large room.

## The look

Grime and glamour, after the concept boards: a chibi flower-child hero
with a round cream face in a ring of orange petals, a green hood and
tunic; the Billious Peddler, purple-hided under a red hood; the Pale
Gatekeeper in a tall violet hat. A forest falling into sickness: a
canopy that goes from blue-black to lit green, dark olive turf with
bright tips, warm soil trails, deep navy water with foam that drifts,
amber lanterns hung in the trees, white and gold stars on the ground,
fireflies; rocks in three shapes sunk in moss and soil on a palette of
their own; and the rot, by depth: a stain in the grass here and there,
then patches of stained ground in the sick rooms, then whole rooms gone
over: a dark violet floor pitted and veined with magenta light, a sick
canopy, walls of blighted stone, under a mist, with crystals, snags,
pools and the blighted tree. Every material has its own 16-color palette and a
dark hue outline, three tones and a gleam, light from the upper left.
The ground is textured turf with hand-placed tufts, flowers and
pebbles; the canopy walls are leaf masses of lit blobs that wrap at the
tile edge, with lanterns and fireflies in the leaves; water has a dark
bank and a drifting foam fringe wherever ground touches it; every
sprite is drawn pixel by pixel with letter legends in `art/*.py`; the
font is a hand-drawn 5x7. `tools/preview.py` renders any sheet or tile
to PNG at 4x.

**The sprite pack.** Every sprite comes from the BARTGAME GBA sprite
pack, kept as delivered: `art/ref/pack/` holds the fixed, engine-sized
sheets and `art/ref/pack_art/` the eight illustrated sheets that came
after (the Bloom, the folk, the hub's two, the portraits, the small
items, the pickups, the 32px icons, the shields). `tools/import_pack.py`
imports both into `art/pack/`: one 4-bit indexed strip per sheet and
`pack.json` with the frame names and palettes, which is all the build
reads. The exact strips go in index for index with the palette they
carry. The illustrations are cut by `tools/pack_art.py`: the haze round
each figure keyed off, the cells cut given how many each row holds,
each cell area-averaged down to its frame (a box that is mostly dark
keeps its darks, so outlines and eyes survive), and each palette group
derived by weighted k-means in Lab so small accents keep a colour.
They replace the hero, the folk, the hub's two, the portraits, the
items, the pickups, the icons and the shield, and take five more OBJ
palette slots (gear, items, pick, icons, folk32), fourteen in all. The
importer's docstrings name which cell went to which frame and the
choices where the art has no exact pose.

The Bloom is 64x32 now, centred on her flower head, so a swing's arc
fits beside her. Her frames carry the sword she swings and the leaf
she guards with, so the engine no longer draws a blade or shield over
her; the sword's hit box is unchanged. A lifted load is drawn over her
where her carry frames hold their barrel, at the chest or across her
back facing north. The prize held up is the engine's icon; the coin
the art drew there is taken out. Small folk stream the one frame they
show into a cache of eight. The engine's frame order still follows the
hand-drawn sheets the pack replaced, so code that counts frames keeps
working; frames the pack appends (Sister Mary Grace and Brother Mark on
the folk and portrait sheets) come after, and its extra sheets (the
upgraded shield, the shield menu symbols, the standalone gilt diamond)
are imported but not yet used. Only the speaker's face is resident (16
OBJ tiles) and the portrait slot is loaded with the speaker's palette.
The HUD tiles are the pack's too, quantized into the HUD palette the
text inks depend on, with its 8x8 slot squares opened out to the
engine's 16x16 slots and its arrow turned to point down. The CPU-drawn
mini-map writes through `ui_ink[]` into the pack's ui palette.

**The environment art pack.** Every background tile of the wood, the
mystery rooms and the Drain is the environment art pack V3's, kept as
delivered in `art/ref/pack_v3/` (its assets, manifest, palettes,
previews and handoff; not its build scripts or reference boards). It
was drawn for the first tile spec: 117 entries, one PNG each, in twelve
palette groups of fifteen colours. `art/env_pack.py` lays them over the
metatiles last, in both builds, index for index: every pixel is one of
its group's colours exactly and every ground tile is opaque, both
checked, so the tiles are the pack's to the pixel. A PNG's tiles run
left to right (variants, a family of fifteen in the order 1..15, a
piece row by row) and its animation frames are further rows below,
with the pack's frame times. What the game lays that the first spec
had no entry for takes a pack tile's art: a mystery room's crown is its
wall and its floor's edges its floor. The hall lays the pack's single
waterfall, grate and counter tiles repeated and its one-tile arch. The
blighted rooms are built from the pack's blight set: its floor, now and
then pitted, its vein for the trail, the sick canopy and the blight
walls, with no edge tiles, since the pack draws its edges in the living
grass only; what the pack draws on grass (stones, bones, flowers) is
not scattered there. The sick rooms get patches of the stained ground,
never a strip one tile wide. The blighted tree is 2x3, as the pack draws
it, and the fairy's spring lies on the overlay. The pack's Drain marks
and clutter are imported but not laid: the hall stays plain.
`docs/BARTGAME_TILE_SPEC.md` (written by `tools/tile_spec/`) lists every
tile laid, marks the pack's, and lists the pieces the pack lacks.

**Before the pack.** The tile atlases (`art/ref/tile_art/`, imported by
`tools/import_tiles.py` into `art/tile_art/tiles.json` and laid by
`art/tile_art.py`) and the painted wood (`art/wood_art.py`, with the
terrain painter `art/paint.py`: tiling value noise, a Bayer dither, lit
clumps, edge bands local to each quarter tile) still run first; the pack
covers all they draw, so they only matter for a tile the pack does not.
`tools/roomgrids.py` dumps many rooms as grids of tile names from the
ROM and renders them from the art in seconds, for judging art across
many real rooms.

**The palettes by area.** The hardware's sixteen BG palettes are shared
out by area: each tileset (the wood, the Drain, the mystery rooms) loads
up to thirteen groups of its own into slots 0 to 12 when the area is
entered, and the pause menu's planks, the gold text and the text and
HUD keep slots 13 to 15.

**The style boards.** The other tiles come from four reference boards in
`art/ref/`: the sprite sheets, the Drain, the blighted wood, and the UI
board. `art/sample.py` cuts them: a crop is scaled to its GBA size,
keyed from the sheet's grey, and quantized to a palette of fifteen
colours derived from the boards themselves (median cut over the crops
a palette serves, each crop weighing the same). `art/style.py` names
every crop: grass, path, canopy, flowers, bushes, tufts, stumps, logs,
two oaks at 32x48 cut into crown quarters masked round an ellipse and a
trunk, water, lilies, falls, bridges, ledges, the well, rocks; the
blight's ground, veins, crystals, dead trees, walls, the door, the
arch, the pool, the pillar; the Drain's floors, walls, water, falls,
pipes, grates, the drain, lanterns, banners, ladders, posts, and the
stall's props. `art/tiles_style.py` puts them into the metatiles by
name; every metatile and HUD tile still drawn by hand is remapped,
colour by nearest colour, into the board palettes (`palettes.REMAP_BG`).
The HUD and the boxes are drawn in the UI board's colours.

**The comparison build.** `make pack-tiles` builds
`bartgame_packtiles.gba` with the sprite pack's own tile sheets instead
(`art/pack_tiles.py`, switched on by `BART_TILES=pack`).
The pack calls them representative families: the area palettes become
the pack's, a pack tile goes on each metatile it names, the pack's
foam-rimmed water on the engine's banked water (the turf beside it is
plain grass, as the pack draws the rim on the water side), path edges
are built from its four one-sided edges, and everything else is
remapped into the pack's colours.

**The wood's rooms.** Every forest room is 32x24 tiles, planned as a
grid of 3x3-tile chunks (ten by seven over the carvable part) drawn
from a bank of pieces: forest, open ground, paths of one, two or three
tiles' width, water, plank bridges, cliffs and their ramps. The plan is
laid in strokes that span chunks: a landing inside each door, three or
four clearings (rectangles of open chunks, rounded off by the trees, a
lake in the heart of a wide one), winding chunk paths from the doors to
the clearings and between them that open into pockets of glade here and
there, then a river meandering across the room, bridged where a path
crosses it, or a cliff along one row of chunks with ledges you can drop
from and a ramp wherever a path runs down through it, and water pouring
off the cliff into a churned pool. Every stroke chooses its pieces to
meet, so water, ledges and paths are shapes and never a scatter of
single tiles. What stands on the open ground is laid by the chunk as a
designed piece: a tree, a ring of bushes, a fall of rocks, a ruined
wall between its pillars, a colonnade, a hedge of thorns, two dead
trees and their bones, a cluster of crystals, a lantern among flowers,
a meadow, a clover patch, a hollow log by its stump, a great boulder, a
tree on its rock, a fairy ring, a pool; only what reads alone on a tile
is still scattered alone: bushes, rocks, posts, stumps, logs, pillars,
flowers and grass. Nothing closes a way, and a hoard is sometimes dug
into the wall behind a bush or a boulder. Fireflies drift over the
living rooms. Set pieces span tiles,
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
- **Pause (Start).** Three pages on one great plank of rotted wood,
  its grain the width of the screen, a knot, a crack, patches of rot
  with mould and mushrooms. R turns the pages, Start closes. ITEMS:
  the HUD's hearts, purse and buttons along the top, then everything
  you own that a button can hold in carved wells, four to a row, the
  rows scrolling when they outgrow the page; the item under the cursor
  is named and described in a bold hand (what it is, what it does, how
  it is used), and A, B or L puts it on that button. KEY ITEMS: the
  pieces of heart lit by count and the hearts grown, then the worn and
  carried things: small keys, the Root Gauntlet, the Relic, the Map,
  the Astrolabe. THE WOOD: the map drawn from the rooms themselves at
  a pixel a tile, visited cells as they are laid out and the rest
  parchment, a cursor walking the cells with the cell's name below; A
  looks closer at six pixels a tile. The marks: a door into a mystery
  until it is won, a quest giver until the quest is paid, a chest until
  opened, a shrine until used, the Nun's relic from her asking to its
  taking, and the Bloom. There is no legend; the marks speak for
  themselves. Nothing is saved from here.
- **The Map and the Astrolabe.** Two chests of the wood hold them. The
  Map draws every cell, seen or not. The Astrolabe adds the chests, the
  Heart and the barriers between rooms (cracked walls, webs, locked
  doors, chasms, thorns), on the overview as dots at the cell edges and
  in the close look at the doors themselves.
- **Items.** The things on the ground and in the menu are drawn at 24
  pixels in 32-pixel sprites: hearts, coins, a purse, seeds, keys, arrows
  in ones, fives and quivers, the relic, the Grail; the tools and
  treasures likewise, and the found thing is held up at that size. The
  HUD's slots keep the small icons.
- **Boxes.** Every message, shop and banner sits in a carved wood frame.
- **The save file.** The game saves itself, to SRAM, when the Heart is
  cut and when the Bloom dies: the wood as generated and as you have
  changed it, the map's marks, everything you carry and the counts. The
  title offers CONTINUE and NEW GAME; a continued run wakes in the drain.

## Controls

| key | action |
|---|---|
| D-pad | walk (1.25 px per frame, like Link) |
| A | what A holds (empty to begin with); talk to someone you face. The Thorn Bow, from a chest near the start, looses an arrow the way you face; the Drain Cap, in the pack from the start, opens a mouth under you that takes you home to the drain |
| B | what B holds: the sword to begin with; or set a bomb, swing the lamp, leap with the cloak |
| L | what L holds: the Bark Shield to begin with. Hold it and the Bloom guards: slower, facing fixed, bites and seeds from the front are turned |
| R | roll while walking (24 frames, invulnerable for the first 18); standing still, lift the bush, small stone or pot you face, held over your head with both arms up; throw what you carry. A sword swing while carrying drops the load at your feet |
| Start | the pause menu: items, key items, the map |

The Rot Gauntlet from the second lock's chest lifts boulders too. A
thrown thing flies two and a half pixels a frame, breaks on the ground,
a wall or a monster (two hearts of damage for a bush or a pot, four for
a stone) and may leave a heart or a coin. The sword cuts bushes, gathers
any heart or coin its swing reaches, turns a spitter's seed back the
way you face (yours now, it hurts what it meets) and lands on a thorn
knight from any side. Bombs break bushes, stones and pots. Arrows, two
hearts of damage and stopped by walls, come twenty with the bow, in
ones, fives and tens from the dead, and ten for ten gilt from the
Peddler. Walk into a chest from below to open it.
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
  myst.c        the mystery rooms: cave, hollow, thicket; ten event kinds
  enemy.c       rot beetle, spore bat, blight spitter, gloom slime,
                thorn knight (ports of TMC's AIs and numbers)
  boss.c        the Blight Heart
  objects.c     projectiles, pickups, effects, bombs
  npc.c         the sage, the merchant, the hermit, the nun, the gardener
  menu.c        the pause menu: items, key items, the drawn map
  save.c        the save file in SRAM
  text.c        BG0 text, the message box with portraits, the shop,
                the HUD, the mini-map
  sound.c       PSG sound effects and a three-track tracker
  game.c        states: title, play, transitions, map, win
art/            pixel art as rows of letters mapped to palette indices
  palettes.py   the 16-color palettes: BG from the boards over the drawn
                ones, OBJ from the sprite pack, the remap tables
  ref/          the four style boards; ref/pack/ the sprite pack's exact
                sheets and ref/pack_art/ its illustrated sheets, as delivered;
                ref/tile_art/ the Drain's and the blight's tile atlases;
                ref/pack_v3/ the environment art pack V3
  pack/         the sprite pack imported: a strip per sheet, pack.json
  pack.py       reads art/pack/ for the build
  pack_tiles.py the pack's HUD tiles; its tiles, for `make pack-tiles`
  tile_art/     the tile atlases imported: tiles.json, the groups and tiles
  tile_art.py   lays the atlases' tiles over the metatiles, in both builds
  sample.py     cutting a board: key, scale, derive a palette, quantize
  style.py      every tile crop by name, and the palettes derived from them
  tiles_style.py the sampled tiles into the metatiles; the rest remapped
  px.py         the painter: legends, outlines, flips, compose, a canvas
                with lit blobs and shaded balls for round things
  paint.py      the terrain painter: tiling noise, dither, lit clumps,
                edge bands and nicks local to each quarter tile
  wood_art.py   the living wood, the blight and the mystery rooms, painted
                before the pack came (it covers them all now)
  env_pack.py   the environment art pack V3, laid over all, index for index
  tiles.py      metatiles: grass, blight, paths, canopy walls, trees,
                stones, water, gates, chests, the sewer set
  hero.py       the drawn Bloom, kept for the engine's frame order
  monsters.py   beetle, bat, slime, spitter, knight, its sword, the boss
  items.py      pickups, key items, effects, projectiles
  folk.py       the five NPCs
  portraits.py  the dialogue portraits, 32x32
  sprites.py    the sheet list: the pack's sheets in the engine's frame order
  hud.py        hearts, icons, item slots, the text box frame, the map
  font.py       the 5x7 font
  title.py      the title screen, painted with PIL in 16 colors
  rooms.py      the hub room: the Drain
tools/
  build_assets.py   art -> build/gen/assets.c with deduplicated tiles
  import_pack.py    the sprite pack (art/ref/pack/, art/ref/pack_art/) -> art/pack/
  pack_art.py       cutting the illustrated sheets: cells, downscaling, palettes
  import_tiles.py   the tile atlases (art/ref/tile_art/) -> art/tile_art/
  tile_spec/        the tile spec for the artist: entries, renders, the doc
  roomgrids.py      many rooms dumped from the ROM as tile names, rendered from the art
  preview.py        render art to PNG
  probe.py          mGBA harness: boot, keys, RAM by symbol, screenshots
  roomdump.py       render the loaded room from RAM
  critical_path.py  walks the key chain to the Grail: the regression test
  quest_probe.py    the three quests
  perf_probe.py     monsters against the frame
```

## The tile budget

A background map entry has ten bits for its tile, so the ground and
overlay layers can address 1,024 subtiles of 8x8 between them. The
build therefore makes three tilesets, one per area, each deduplicated
on its own (flips reused): the forest, the sewer and the mystery rooms.
A metatile keeps one global id; each set carries its own map entries
for it, blank where the set does not hold it. `tiles_load` copies the
area's set into the charblocks when the area changes. The build prints
each set's count.

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
python3 tools/myst_probe.py               # every mystery kind forced, played to its reward
python3 tools/wood_probe.py               # the bow, the Drain Cap, the sword's gathering and deflecting, open knights
python3 tools/menu_probe.py               # the three pause pages, the grid, the map's zoom, save and continue
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
