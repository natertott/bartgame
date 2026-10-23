# 03. World, tiles, collision, rooms, and where a generator plugs in

This is the part of the engine the new game changes most. The vanilla world
is ROM data. The new game's nine areas are generated at run time.

**How to read it for a from-scratch engine** (`12_FROM_SCRATCH_ENGINE.md`):
the tile behaviors (collision shapes, act tiles, ledges, holes, doors,
water versus land) and the area-grid rules are **spec**. The new engine
needs the same behaviors under its own format. TMC's layouts (`MapLayer`,
`RoomResInfo`, LZ77 maps, property lists) and its load pipeline are
**reference**. The last section, "where a generator plugs in", says how
TMC's own engine would take generated rooms. It shows which state a room
needs at play time, which is the checklist for the new engine's room loader.

Sources: `include/map.h`, `include/tiles.h`, `include/room.h`,
`include/area.h`, `include/transitions.h`, `src/playerUtils.c` (the loader),
`src/movement.c` (collision tests), `src/gameUtils.c` (`InitRoom`),
`src/room.c` (`LoadRoom`), `src/beanstalkSubtask.c` (`LoadMapData`),
`data/map/`.

## The tile model

```
8x8 subtile  (4bpp GBA tile, the hardware unit)
  x4  ->  16x16 tile ("metatile"): 4 subtile entries with flip and palette bits
            -> tile index 0..2047 in the room's tileset
            -> tileTypes[index]  = the tile TYPE (what it is)
                 -> gMapTileTypeToCollisionData[type] = collision byte
                 -> gMapTileTypeToActTile[type]      = act tile (behavior)
```

A room is a grid of tile indices, at most **64x64 tiles** (1024x1024 px), on
**two layers**:

| layer | struct | BG | priority | used for |
|---|---|---|---|---|
| bottom | `gMapBottom` | BG2 (0x1D02) | 2 | the ground |
| top | `gMapTop` | BG1 (0x1C01) | 1 | walls, overhangs, bridges, tree canopies |
| (HUD and text) | | BG0 (0x1F0C) | 0 | screenbase 31, charbase 3 |
| (background) | | BG3 (0x1E03) | 3 | parallax, sky, water layer |

### `MapLayer` (one per layer, 0xC004 bytes each, in EWRAM)

| offset | field | size | meaning |
|---|---|---|---|
| 0x0000 | bgSettings | ptr | the BG this layer draws to |
| 0x0004 | mapData[4096] | u16 | tile index per tile, 64-wide stride |
| 0x2004 | collisionData[4096] | u8 | collision byte per tile |
| 0x3004 | mapDataOriginal[4096] | u16 | the as-loaded map, for restoring cut bushes and similar |
| 0x5004 | tileTypes[2048] | u16 | tile index to tile type |
| 0x6004 | tileIndices[2048] | u16 | tile type to the first tile index with it (the inverse) |
| 0x7004 | subTiles[8192] | u16 | 4 subtile entries per tile index (tonc BG map format: bits 0-9 tile, 10 hflip, 11 vflip, 12-15 palette) |
| 0xB004 | actTiles[4096] | u8 | act tile per tile |

`TILE_POS(x, y) = x + (y << 6)`. `GetLayerByIndex(1 or 2)` returns the layer.

**Special tiles.** A `mapData` value of 0x4000 or more is not a tileset
index but a special tile: pots, pushable statues, boulders, ladder tops,
objects' collision footprints (0x4000-0x4096; see `include/tiles.h`
around line 1404). Their collision comes from
`gMapSpecialTileToCollisionData`. Objects use them to stamp collision
into the map: a pot sets 0x4000 under itself, a pushed rock moves its
special tile one cell.

### Tile types worth knowing (`include/tiles.h`)

The enum is mostly `TILE_TYPE_n`. The named ones:

| type | name | type | name |
|---|---|---|---|
| 0x1c | CUT_BUSH | 0x78 | PRESSURE_BUTTON |
| 0x1d | CUT_GRASS | 0x79 | PRESSURE_BUTTON_PRESSED |
| 0x1e | CUT_SIGNPOST | 0x7a / 0x7b | PRESSURE_SQUARE / pressed |
| 0x1f | CUT_TREE | 0x92 / 0x93 | STAIRS_UP / STAIRS_DOWN |
| 0x55 | ROCK | 0x176 | SIGNPOST |
| 0x73 / 0x74 | CHEST / CHEST_OPEN | 0x1d3-0x1d6 | PERMA_ROCK 1-4 |
| 0x76 / 0x77 | labeled TORCH / TORCH_LIT | 0x317 / 0x318 | RED_TILE / BLUE_TILE |

**Trap: the torch labels are one off.** Measured in the ROM, an unlit torch
is type 117 (0x75) and a lit one 118 (0x76). 119 (0x77) is a floor
button. The swung Lantern turns 117 into 118 by itself.
(`docs/QUICKSTART_LANTERN_GUST_EVENTS.md`)

**A tile type is behavior, not art.** The same type can draw differently
in every tileset. That is what makes a re-skin cheap: keep the type
numbers, replace the subtile art. And it is what makes a generator
possible: it can place **types** and let a per-area tileset pick the
indices.

## Collision bytes (`collisionData`, `src/movement.c` `IsTileCollision`)

| value | meaning |
|---|---|
| 0x00 | open |
| 0x01-0x0F | a 2x2 quadrant mask: bit 3 NW, bit 2 NE, bit 1 SW, bit 0 SE (8x8 quarters of the 16x16 tile). 0x0F is fully solid |
| 0x10-0xFE | shape functions: half and three-eighths fills, diagonals (`TileCollisionFunction0-9`) |
| 0xFF | special: solid for most movers, a shape for some |

The answer also depends on the **mover's `collisionType`**. Each mover
passes one, and lookup tables in `IsTileCollision` decide per type whether
a value is solid. That is how flyers cross water, why collisionType 4
treats open tiles as solid (it stays on special terrain), and how the
Minish fits through quarter gaps.

Collision is **derived** at load (`sub_0807BBE4`, `src/playerUtils.c` line
3653). For each tile: index below 0x4000 gives
`gMapTileTypeToCollisionData[tileTypes[index]]`, otherwise
`gMapSpecialTileToCollisionData`. Then `CreateCollisionDataBorderAroundRoom`
writes 0xFF on the column and row just past the room's width and height,
so nothing walks off a room except through an exit.

## Act tiles (`actTiles`)

Behavior per tile, filled at load from the tile type by
`FillActTileForLayer`. The player's surface comes from it (see
`02_PLAYER_AND_MOVEMENT.md`). Items and objects test it too.

| act | meaning | act | meaning |
|---|---|---|---|
| 0x00 | cut (sword) | 0x28, 0x29 | door: area transitions fire here |
| 0x01 | rock breaker | 0x2a-0x2d, 0x40-0x43, 0x4c-0x4f | ledges, by direction |
| 0x02 | boomerang | 0x2e | bombable wall |
| 0x03 | bomb | 0x3d | Minish portal |
| 0x04 | arrow | 0x3e | removable dust |
| 0x05 | gust | 0x3f | stairs, auto ladder |
| 0x06 | lift | 0x50 | climb wall (Grip Ring) |
| 0x07 | fire | 0x53 | ladder |
| 0x08 | crumbling floor (becomes 0x0d once walked on) | 0x56 | Mole Mitts wall dig (a solid face, collision 0x0f-0x16) |
| 0x09 | enemy walk | 0x57 | clone tile |
| 0x0a | Pacci | 0x5a | lava |
| 0x0c | sword beam | 0x65-0x6f | minecart rails |
| 0x0d | pit. Also the soft earth the Mole Mitts dig (`TILE_ACT_DIG` in the scavenger survey) | 0x72 | block push |
| 0x0e | water edge slope | 0x74 | edge |
| 0x0f | shallow water | 0xf0 | hole |
| 0x10 | deep water | 0xf1 | ladder top (door transition) |
| 0x12 | ice | | |
| 0x13 | swamp | | |
| 0x16 | dust | | |
| 0x19 | hole | | |
| 0x1b, 0x1d | button | | |
| 0x1f, 0x20 | Minish door front/back | | |
| 0x26, 0x27 | slopes | | |

**Walkable collision is not land.** Water and swamp are open collision.
A spawn point, a chest or a landing must also reject act tiles 0x0d, 0x0e,
0x0f, 0x10, 0x12 and 0x13. QUICKSTART once placed enemies in the middle of
Lake Hylia this way.

## Rooms and areas

An **area** is a set of rooms sharing a tileset family, a music track and a
flag bank. Rooms of one area share **one pixel grid**: each room has a
`map_x`/`map_y` origin in it, and borders between them scroll rather than
fade.

| structure | where | what |
|---|---|---|
| `RoomHeader {map_x, map_y, pixel_width, pixel_height, tileSet_id}` | `gAreaRoomHeaders[area][room]`, ROM | room placement and size |
| `AreaHeader {flags, location, flag_bank, queueBgm}` | `gAreaMetadata[area]`, ROM (`src/data/areaMetadata.c`) | `AR_IS_OVERWORLD`, `AR_HAS_KEYS`, `AR_IS_DUNGEON`, `AR_HAS_MAP` and so on |
| `RoomResInfo` (0x20 bytes) | `gArea.roomResInfos[64]`, **RAM** | per-room pointers: tileSet, map, tiles, bg_anim, exits, properties, size and origin |
| `Area gArea` | RAM, 0x894 bytes | the current area: room infos, BGM, onEnter/onExit hooks |
| `RoomControls gRoomControls` | RAM | area, room, origin, scroll, width, height, camera target, `reload_flags` |
| `RoomVars gRoomVars` | RAM, 0xCC bytes | per-visit state: `flags[52]`, light level, `properties[8]`, `graphicsGroups[4]`, puzzle entity pointers |

`MAX_ROOMS` is 64 per area.

### What a room's `properties` hold (`data/map/entity_headers.s`)

`properties[0..7]`, the room's "property list":

| slot | contents |
|---|---|
| 0 | entity list (objects, NPCs) |
| 1 | entity list (more) |
| 2 | enemy list |
| 3 | tile entities (chests, signs, bombable walls, Ezlo hints, darkness) |
| 4 | a condition callback (`sub_unk3`) |
| 5 | the on-load state change callback (`sub_StateChange`) |
| 6, 7 | additional data |

An **entity list** is an array of `EntityData` packets (16 bytes:
`kind, flags, id, type, type2, xPos, yPos, spritePtr`) ending with kind
0xFF. `LoadRoom` (`src/room.c` line 183) spawns lists 1 and 0, then the
enemy list, then the tile entities. Coordinates are room-local pixels.

### Exits (`include/transitions.h`)

`Transition` rows in a list ended by `warp_type == 0xFFFF`:

```
u16 warp_type   BORDER (0), AREA (1), BORDER2, AREA2
u16 startX, startY      the box (AREA) or edge span (BORDER), room-local px
u16 endX, endY          where the player lands in the target room
u8  shape               AREA: 12x12, 12x28, 28x12, 44x12 box; BORDER: which edge(s)
u8  area, room, layer   the target
u8  transition_type     NORMAL, DROP_IN, STAIR_EXIT, HOP_IN, FLY_IN ...
u8  facing_direction    0-4
u16 transitionSFX
```

`CheckRoomExit` tests them every frame. A door is an AREA box over act
tile 0x28 or 0x29. Vanilla exit lists live in `gExitLists[area][room]`
(`src/data/transitions.c`, ROM). **Trap: a landing coordinate inside a
puzzle board or on a solid tile breaks the room.** QUICKSTART dealt puzzles
whose boards covered a door's landing. They read as solved the moment the
player arrived. Keep every landing, plus a few tiles of approach, out of
anything generated.

### Holes

`gHoleTransitions` (`src/manager/holeManager.c`): rows of a tile box plus a
target area, room and position. Stepping into the box sets
`PL_PIT_IS_EXIT` and calls `DoHoleTransition`. A generated pit that leads
somewhere is a row here. A pit that leads nowhere is just act 0x0d and
costs a respawn plus 2 damage.

## The load pipeline

On a room change (`GameMain_ChangeRoom` and `InitRoom`):

1. **`InitRoom` / `InitAllRoomResInfo`** (`src/gameUtils.c` around line
   504) fill `gArea.roomResInfos[room]` from ROM:
   `exits = gExitLists[area][room]`,
   `properties = gAreaTable[area][room]`, and tileSet, map and tiles from
   `gAreaTileSets`, `gAreaRoomMaps` and `gAreaTiles`.
2. **`LoadRoomTileSet`** (`src/playerUtils.c` line 3883): fills
   `tileTypes` with 0xFFFF, loads the tileset (subtile art to VRAM, the
   `subTiles` table and `tileTypes`) through `LoadMapData` if it changed,
   loads palettes, starts BG animations, then builds `tileIndices`.
3. **`LoadRoomGfx`** (line 3931):
   - clears the top map and collision,
   - `LoadMapData(map)`: decompresses the room's map (LZ77) into
     `mapData` packed at room width,
   - `sub_0807C8B0`: re-strides it to 64 wide,
   - copies `mapData` to `mapDataOriginal`,
   - `sub_0807BBE4`: derives `collisionData` from the tile types,
   - `CreateCollisionDataBorderAroundRoom`,
   - `FillActTileForLayer` on both layers,
   - `RenderMapLayerToSubTileMap`: expands both layers into
     `gMapDataBottomSpecial`/`TopSpecial` (subtile maps the scroller
     copies to VRAM),
   - sets BG control and DISPCNT. **This step switches on the area id**
     (Minish houses, interiors and the default). Your areas need their
     own entry, or a per-area metadata field instead.
4. **`LoadRoom`** spawns the property lists' entities.
5. The scroller (`UpdateScrollVram`) streams `gMapData*Special` into the
   BG buffers as the camera moves.

`MapDataDefinition {src, dest, size}` chains (bit 31 of `src` means
another follows; bit 31 of `size` means LZ77). `src` is **an offset from
`gMapData` in ROM, not a pointer**. A `dest` of NULL means "load palette
group `src`".

## Where a generator plugs in

Every piece of state the room uses at play time is already in RAM:
`mapData`, `collisionData`, `actTiles`, `gArea.roomResInfos`,
`gRoomVars.properties`. Only the **sources** are ROM. So:

| piece | vanilla source | for a generated room |
|---|---|---|
| room size and origin | `gAreaRoomHeaders` | write `RoomResInfo.pixel_width/height/map_x/map_y` |
| tileset | `gAreaTileSets` (ROM chain) | keep. One authored tileset per area theme, loaded the vanilla way |
| map | `gAreaRoomMaps` (LZ77 in ROM) | **replace step 3's `LoadMapData(map)`** with the generator writing `mapData` for both layers directly, already at 64 stride. Skip `sub_0807C8B0` |
| collision | derived | keep: `sub_0807BBE4` derives it from what you wrote. Write overrides after it if needed |
| act tiles | derived | keep: `FillActTileForLayer` |
| exits | `gExitLists` (ROM) | point `RoomResInfo.exits` at a RAM `Transition[]` the generator fills, ended by 0xFFFF |
| entities | `gAreaTable` property lists (ROM) | point `properties` at RAM arrays of `EntityData`, ended by kind 0xFF |
| holes | `gHoleTransitions` (ROM) | a RAM table, and a one-line change in the hole manager to read it |
| area metadata | `gAreaMetadata` | keep 10 authored rows (hub plus 9 areas) |

The cleanest shape:

1. Reserve **10 area ids**: one hub and nine generated. Author the hub as
   ordinary data. Each generated area gets an authored **tileset** (art
   plus a type table), music, and a theme.
2. At run start (or on entering an area), the generator runs from
   `hash(run_seed, area_index)`. It produces a **room graph** (rooms,
   sizes, connections, locks, keys) and stores it compactly in EWRAM,
   about 31 KB free. Do not store full tile maps for every room. Store
   the graph plus a per-room seed, and **regenerate the tile map on room
   load**. Generation must be deterministic and fast: a few frames during
   the fade.
3. A `GeneratedRoomLoad(area, room)` hook replaces `LoadMapData(map)` in
   `LoadRoomGfx`. It writes both layers' `mapData` from the room seed and
   the graph. Then collision, act tiles and rendering run unchanged.
4. Exits and entity lists come from the graph into RAM arrays, and the
   `RoomResInfo` points at them.
5. Per-room persistent state (chest opened, door unlocked, puzzle
   solved) lives in a run state block in `gSave`, indexed by
   (area, generated room). Room flags in `gRoomVars.flags` clear on every
   load and only suit per-visit state.

### Area-grid rules the generator must respect

- **Rooms of one area share one pixel grid.** A BORDER exit scrolls to
  the neighbour without a fade only when the two rooms touch in that grid.
  So lay rooms out on a grid in area space first, then give each its
  `map_x`/`map_y`. Two rooms joined by a BORDER must share the edge span
  exactly. QUICKSTART's seam audits (`seam_audit.py`) exist because the
  vanilla seams are not always where the comments said.
- A room's size is a multiple of 16 px and at most 1024x1024. The screen
  is 240x160 (15x10 tiles), so a room smaller than one screen will not
  scroll. A room near 64x64 tiles costs the full 0xC004 bytes per layer
  either way.
- `CreateCollisionDataBorderAroundRoom` makes the edge solid. Every way
  out must be a `Transition`.
- Doors: an AREA box over act 0x28 or 0x29, with a landing in the target
  room that is open, dry land, and outside every generated feature.
- **Ledges are one-way edges.** Record them as directed edges in the
  graph. A flood fill over collision cannot see them.
- **Every hole needs a valid target**, or it must be a plain pit.

### Tilesets for generated rooms

The generator works best placing **tile types and small authored
stamps**, not raw indices. Per area theme, author:

- a tileset (subtile art, palettes, the `tileTypes` table),
- a **stamp library**: wall segments, corners, cliffs with ledges, door
  frames, water edges, tree clumps, torches, chests on pedestals, each
  a small grid of tile indices on both layers with a footprint mask,
- the auto-tile rules for joins (cliff edge and corner pieces, water
  shorelines).

Then a room is: carve walkable space, place stamps on the footprint,
auto-tile the borders, then place entities. See `07_PROCGEN_DESIGN.md`.
