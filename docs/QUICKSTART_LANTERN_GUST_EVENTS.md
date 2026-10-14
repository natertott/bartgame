# Lantern and Gust Jar ? rooms: investigation

Two new ? room events, asked for to give the Lantern and the Gust Jar real
work (Oct 2026):

- **Torches**: light every torch in the room for the reward. Variants:
  how dark the room is, torches that go out on a timer, enemies, and where
  the torches stand.
- **Cleanup**: fill the room with debris the Gust Jar clears, plus enemies,
  and the player cleans the room for the reward.

In both, enemy waves never end: a kill is replaced after a while.

This is the research phase. Every engine fact below was measured in the ROM,
by `tools/quickstart/lantern_gust_spike.py` (12/12) and
`tools/quickstart/lantern_gust_survey.py` (all 119 sites). Nothing is built
yet; the plan and the open questions are at the end.

## What the engine gives us

### Torches are tiles, and vanilla already has timed torches

| fact | evidence |
|---|---|
| An unlit torch is `TILE_TYPE_117`, a lit one `TILE_TYPE_118`. `tiles.h` labels 118/119 "TORCH/TORCH_LIT", one off: 119 is a raised floor button (`button.c`). | `flameManager.c`, `lightLevelSetManager.c`; spike TORCH |
| The Lantern lights a torch tile by itself: swing it at tile 117 and the tile becomes 118. No manager is needed for the lighting. | spike TORCH |
| A lit torch can be put out by setting it back to 117. | spike OUT |
| Vanilla's timed torch is `LIGHT_LEVEL_SET_MANAGER` type 3: once its tile reads 118 it raises the room's light, counts `field_0x36 * 60` frames, then puffs (`CreateDeathFxAt`), restores the unlit tile and lowers the light, unless an "all lit" flag latches it on. Type 2 is the permanent torch. | `lightLevelSetManager.c` |
| The Lon Lon Ranch secret cave is the vanilla model: a dark room (`tile_entity type=0x9`), two of those managers on two torches, a flag manager, a chest. | `entity_headers.s` |
| A tile only shows after `SetTileType`, `SetTile` and a visible-tiles refresh, and only on a layer whose tileset carries it (0xFFFF means absent). `QuickStartPaintChestTile` already does exactly this for chests. | game.c; spike |
| Placed torches need a tileset that has torch art. **72 of 119 sites do**: caves (19), Minish caves (14), Crenel caves (12), Veil Falls caves (9), Goron caves (5), Castor caves (5), and a few more. The other 47 cannot draw one: tree interiors, houses, dojos, Minish houses, Great Fairy rooms. | survey |

### Darkness is a single dial

| fact | evidence |
|---|---|
| `sub_0805BB00(level, 1)` darkens the room; the dark wave rooms already use it. 0x100 is daylight, 0x80 vanilla's dim (Percy's house), 0x00 pitch black. | game.c; spike DARK |
| With the Lantern lit, dim shows the room behind a circle of light; pitch black shows nothing outside the circle. | screenshots |
| `ChangeLightLevel(n)` adds light, clamped 0-0x100. Vanilla gives each lit torch a share, so a black room brightens as the torches go up: measured 0x00 to 0x40 for one torch's share. | spike DARK+TORCH |

### Debris the Gust Jar clears

| debris | portable? | jar | lantern | notes |
|---|---|---|---|---|
| `SPIDER_WEB` (projectile 0x15) | **yes**, own sprite sheet | clears it (85 frames held) | burns it | Four orientations; the jar takes a web only from the side it faces. It stamps a one-sided obstacle tile ("Object Top"), so it blocks from its facing side only: walked into from behind, the player passed. |
| `DUST` cloud (enemy 0x53, type 0) | **yes**, own sprite | clears it (107 frames) | - | Hyrule Town's carpet dust: one entity, many hitboxes, sheds pieces as it is pulled. Deletes itself while the town flag `MACHI_MACHIHOKORI` is set, so a room must clear it first. No contact damage, does not block. It is an ENEMY kind: wave counts and caps must not count it. |
| Mount Crenel's dust (`REMOVABLE_DUST` type 0) | no | - | - | Sits on that tileset's own dust tiles (387, 1018-1025), which only 3 sites carry, all outdoors. Dust tiles slow the player (`SurfaceAction_Dust`); they do not hurt. |
| `REMOVABLE_DUST` type 1 | no | not taken | - | Draws magenta outside Crenel: its form loads no sheet of its own. |
| `DUST` type 1 (piece) | no | - | - | Deletes itself on its first frame. |

The Mount Crenel debris "that hurts the player if they touch it" is not one of
these: none of the dust measured here deals damage. See the open questions.

### Enemies and endless waves

- The survive room already runs endless pressure. The wave spawner is re-run
  whenever the room thins below three live enemies, under the global enemy
  ceiling and the entity, GFX and palette reserves. Both events can use that
  engine as it is.
- Enemy picks with a theme already work this way: the survive room's
  `QuickStartPickPursuer` re-rolls the difficulty-scaled pick against an
  allowlist (`sQuickStartPursuers`, 21 entries), so the curve still applies.
  A "hazard" allowlist built the same way covers the request's four groups:
  - **Slows the player**: grabbers and holders such as Rupee Like.
  - **Status effects**: fire (Fire Wizzrobe, Fireball Guy), ice (Ice
    Wizzrobe), electric (ChuChu forms, Spark).
  - **Targets the player**: the existing pursuer list.
  - **Rare elite**: the Elites table, rationed to one.
- The roster's fire and ice "themes" are colour sets, not effects. Which
  status each candidate actually inflicts on the player has to be measured
  (frozen, burning, shocked, held) before the list is final.
- Budget: a web is one entity, and a DUST cloud one entity with a heap. A
  room of 12 webs and 8 live enemies sits well inside the entity reserve.

## Proposed design

### Torches (`QS_EVENT_TORCHES`)

| axis | values |
|---|---|
| darkness | lit, dim (0x80), black (0x00); each lit torch adds `0x100 / count` light, so the room brightens as you work |
| torch count | 3 to 8, by room size and difficulty |
| layout | spread, clustered, or hidden: in corners, behind the room's own rocks and pillars, off the line of sight from the door |
| timer | none, or each torch burns N seconds then puffs out (vanilla type 3); difficulty shortens N; "all lit at once" latches them on and pays |
| enemies | none, or endless hazard waves; one elite now and then at high difficulty |

Layouts are generated offline per site from the floors `block_rooms.py`
already captures (`build/block_rooms.json`), proven reachable, as the block
puzzles are: a pool per site, a draw per run. Torches are solid tiles, so the
generator keeps every torch's lighting tile and the reward reachable.

### Cleanup (`QS_EVENT_CLEANUP`)

| axis | values |
|---|---|
| debris | webs (four orientations) and dust clouds, mixed |
| amount | 6 to 16 pieces, by room size and difficulty |
| layout | across the floor, walling corridors with webs whose blocking side faces the approach, guarding the reward |
| enemies | endless hazard waves, same pool |

Also generated offline per site, with a clearing order proven: every web
reachable on its facing side once the webs before it are gone. Both kinds of
debris draw in any tileset, so all 119 sites are candidates.

## Plan

1. **Generator** (`tools/quickstart/lantern_rooms.py`, a sibling of
   `block_puzzles.py`): torch layouts and debris layouts per site, with
   `--verify`.
2. **Runtime** in game.c: the two kinds, torch painting through the chest
   painter, timers and light shares, debris spawning, the win checks, the
   hazard allowlist on the survive spawner, and Ezlo's lines.
3. **Probes** that solve each layout by playing: light every torch with the
   lantern, clear every piece with the jar.
4. **Simulator mirror** of the kind roll, and the docs.

## Open questions for the user

1. **Item gating.** Deal these rooms only once the player owns the Lantern or
   the Gust Jar, or deal them anyway as a reason to go and find it?
2. **Webs and the lantern.** In vanilla the lantern burns webs too. Keep that,
   or make the cleanup rooms jar-only?
3. **The Mount Crenel debris that hurts.** Neither the Crenel dust nor the
   town's dust cloud does damage. Which one did you mean?
4. **The 47 sites with no torch art** (houses, trees, dojos). Leave them out
   of the torch room, or build an object stand-in for a torch?
5. **Endless waves.** Confirm they stop the moment the goal is done, and that
   the survive room's pressure, a refill below three live enemies, is the
   right feel.
