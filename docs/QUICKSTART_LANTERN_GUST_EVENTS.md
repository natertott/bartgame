# Lantern and Gust Jar ? rooms

Two ? room kinds, asked for to give the Lantern and the Gust Jar real work
(Oct 2026). Built, and played layout by layout in the ROM.

- **Torches** (`QS_EVENT_TORCHES`, 10): unlit torches stand round the room.
  Light them all with the Lantern and the prize drops. The room may be
  dark, the torches may burn out, and enemies keep coming.
- **Cleanup** (`QS_EVENT_CLEANUP`, 11): spider webs and dust clouds fill the
  room. Clear them all with the Gust Jar, or burn the webs with the
  Lantern, and the prize drops. Enemies keep coming.

## The user's answers

| question | answer | what was built |
|---|---|---|
| Deal only once the item is owned? | "These should show up anyway as a reason to go find it. We can incorporate these into our win chain as well." | Dealt whatever the player holds. Half the win chain's EVENT steps that land on a site with a layout force one of the two kinds there. |
| May the Lantern burn webs? | "Keep this as a feature: the lantern can also solve the gust jar rooms." | Vanilla's web burns, unchanged. Without the Gust Jar no dust cloud is dealt, so a Lantern alone can finish any cleanup room. |
| Which Mount Crenel debris hurts? | The white patches at Crenel's base the jar clears to reveal the Minish portal. | That is `REMOVABLE_DUST` type 0. Measured: Link standing in the patch took no damage. It only exists on that tileset's dust tiles (3 outdoor sites), so it is not used. |
| The sites with no torch art? | "Leave those 47 rooms out for now, but keep a note." | Left out. The count grew to 60 once the screen was checked (below). |
| Endless waves? | "Continue even after the win", refill when fewer than three are alive. | As asked: refills whenever fewer than three of ours stand, until the prize is taken. |

## Engine facts (measured)

### Torches

| fact | evidence |
|---|---|
| An unlit torch is `TILE_TYPE_117`, a lit one 118. `tiles.h` labels them one off (119 is a floor button). The swung Lantern turns 117 into 118 by itself. | `lantern_gust_spike.py` TORCH |
| Vanilla's torch manager, `LIGHT_LEVEL_SET_MANAGER`, does the rest. Type 2 adds its share of light when lit. Type 3 burns `field_0x36` seconds, then puffs, restores the floor and takes its light back, unless the room's "all lit" flag latches it. One manager per torch is spawned by the room. | `lightLevelSetManager.c`; Lon Lon Ranch's secret cave |
| **A tile changed from the ? room code never reached the screen in a room that does not scroll.** `QuickStartUpdate` runs after the frame's `UpdateScrollVram` has copied the maps into the BG buffers, and `WaitForNextFrame` then uploads the stale buffers and clears the flag. Measured: the torch's subtiles were in `gMapDataBottomSpecial` and absent from `gBG1Buffer`. The painter now calls `UpdateScrollVram` at once, as `Scroll2Sub0` does. The chest painter had the same flaw and got the same fix. | `lantern_probe.py` DEALT UNSEEN check |
| Listing the torch's tile is not drawing it. The Minish houses list it and their character data there is blank. `lantern_gust_survey.py --draw` paints a torch on the floor at every site and compares the screen: **59 of 119 draw one.** | survey |
| Darkness is one dial: `sub_0805BB00(level, 1)`, 0x100 day, 0x80 vanilla's dim, 0 black. Each lit torch adds `(0x100 - level) / count`. | probe: light 0x0 rose to 0xff with every torch lit |

### Debris

| fact | evidence |
|---|---|
| `SPIDER_WEB` (projectile 0x15) draws anywhere. The jar latches it only from the side it faces (`animationState >> 1 == type`), and the web comes away only as the player is pulled back. **A web whose stand tile backs onto a wall or another web is grabbed and never comes off;** with one free tile behind it is hit and miss, so the generator wants two. The Lantern burns a web from any side. | probe traces |
| The web's stand tile must be plain floor. On a ladder the player is in `PLAYER_CLIMB` and the jar does nothing (a Minish house). | probe trace |
| The `DUST` cloud (enemy 0x53, type 0, Hyrule Town's carpet dust) is cleared in 107 frames, **but only with the player 23 to 36 px straight below its centre**. At 16 px or 44 px it never came. It deletes itself while the town flag `MACHI_MACHIHOKORI` is set, so the room clears that flag before each cloud. It neither blocks nor hurts. | probe: distance sweep |
| A dust cloud is an ENEMY entity. `QuickStartEnemyIsOurs` now never counts `DUST`, so waves, caps and the GFX trim leave it alone. | game.c |
| The Deepwood Shrine's entrance hangs webs of its own. The room counts only the webs it dealt (their flag word is `QS_LANTERN_NO_FLAG`, 0xC000, which `CheckFlags` reads as clear and `SetFlag` ignores). | probe |

### Hazard enemies

What each roster enemy does to the player was measured, not read off the
roster's colour themes (`hazard_probe.py`: three of each round a player in
the quiet dojo, 600 frames, standing and swinging).

| enemy | effect | dealt from enemy difficulty |
|---|---|---|
| Beetle | clings on: the player walks at speed_modifier -240 | 0 |
| ChuChu form 2 (blue) | its charge hurts a sword that strikes it (untyped hits only while swinging) | 1 |
| Ghini | grabs and holds (CAPTURED) | 2 |
| Like Like | swallows (CAPTURED) | 3 |
| Fire Wizzrobe | sets the player alight (BURNING) | 4 |
| Ice Wizzrobe | freezes the player solid (FROZEN) | 5 |

Left out: `ENEMY_50` and the Moldworm also capture, but one placement is a
dozen or more entities; Spark shocks but keeps to the walls and dies only
to the boomerang.

## How it is built

### Layouts (`tools/quickstart/lantern_rooms.py`)

Generated offline per site from the floors `block_rooms.py` captured (the
sites alone in their room), proven, written to
`include/quickstart/lantern_rooms.h`. `--verify` re-proves the shipped
table.

| kind | sites | layouts | styles |
|---|---|---|---|
| Torches | 45 | 234 | spread, cluster, hidden (against the room's own walls and furniture, far from the door) |
| Cleanup | 75 | 232 | scatter (webs and up to two clouds), walls (webs hung on the walls, facing in) |

The proofs:

- Torches and webs are solid. Blocking every one keeps the arrival joined
  to the doors, the prize spot and the edges, and seals no pocket bigger
  than four tiles.
- Every torch has a plain-floor neighbour joined to the arrival.
- The webs clear in some order: each web's stand tile and the two tiles
  behind it are plain floor (ground act tiles, so no ladder) reachable
  once the webs before it are gone. With only one free tile behind, the
  web came away or not depending on where in the tile the player stood.
- Every cloud has open ground all round and the two plain-floor tiles
  below it reachable.
- Nothing stands on a reserved tile or within two tiles of the arrival.

### Runtime (`src/game.c`, `QuickStartSetupLanternContent`)

- **Roll.** At a site with layouts of the kind, over the open kinds (ANY,
  LARGE, SMALL), by hashes of their own: torches one roll in six, else
  cleanup one in six. Simulated over 300 seeds the pair takes 16.2% of ?
  room rolls (torches 6.2%, cleanup 10.0%). `extra` is the prize's draw
  seed.
- **Layout.** Drawn from the run seed over the site's layouts; below enemy
  difficulty 4 only the smaller ones.
- **Torch variant**, from the run seed and the difficulty:
  - darkness 0x100, 0xC0, 0x80, 0x40 or 0, darker as the difficulty
    climbs, never darker than 0x80 without a Lantern;
  - timed torches one room in four, two from enemy difficulty 6, three
    from 12; each burns `10 + 2 * count - difficulty / 2` seconds, at
    least 8. Lighting them all at once latches them on.
- **Waves.** Refill whenever fewer than three of ours stand, half hazards
  and half pursuers, through the win and until the prize is taken. From
  enemy difficulty 5 one refill in eight brings a Darknut or a Ball and
  Chain soldier when none is standing.
- **Fallback.** On the frame after the deal, a room where no torch tile
  came out or not one piece of debris was created deals the item drop
  instead, as the NPC and fairy kinds already do.
- **Win chain.** `QuickStartChainStore` gives an EVENT step's
  `chain_detail` 0x80 + the kind (`QuickStartChainEventForce`) for half the
  steps whose site has a layout. The site roll deals that kind while the
  step stands. Measured: a CHAIN scenario with detail 0x8a dealt torches at
  its site, 0x8b webs, 0 the site's own roll.
- **Ezlo** says one of three lines as the room deals: torches, torches that
  burn out, and the cleanup.

### Left out, and why

- **Torch rooms at 74 sites.** 60 cannot draw a torch: houses, tree
  hollows, dojos, Great Fairy rooms, the Minish houses, the dark Veil Falls
  stair. The rest have no captured floor (they share their room with other
  sites, like the Boomerang cave) or no layout fits.
- **Cleanup at 44 sites.** The same shared-room rule, rooms too small for
  six pieces, and the barrel Minish house (site 99), where the player on a
  web's stand tile goes into `PLAYER_CLIMB` and the jar does nothing.
- **Two broken sites: the North Hyrule Field fairy fountain tree (47) and
  the Minish crack by the Wind Ruins (65).** Their ? room runs one frame
  and stops, whatever it deals: the plain wave room spawns no enemies there
  either. A known defect logged in the roadmap; no layout is built there
  until it is fixed (`BROKEN_SITES`).

## Testing

| tool | what | result |
|---|---|---|
| `lantern_rooms.py --verify` | every shipped layout re-proven | 466 layouts, 0 problems |
| `lantern_probe.py` | every layout played in the ROM: dealt, seen, solved, won, waves after the win, prize taken, site DONE | 466/466 |
| `lantern_gust_survey.py --draw` | which sites draw a torch | 59 of 119 |
| `hazard_probe.py` | what each roster enemy does to the player | table above |
| `lantern_gust_spike.py` | the engine primitives | 12/12 |
| `site_roll_validate.py` | the simulator deals the ROM's roll | 833/833 |
