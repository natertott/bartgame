# 04. Entities, enemies, objects, NPCs, managers

All vanilla engine. The enemy roster and caps are QUICKSTART's and carry
over as data.

Sources: `include/entity.h`, `src/entity.c`, `include/enemy.h`,
`src/enemy.c`, `src/enemyUtils.c`, `include/definitions.h`,
`src/objectDefinitions.c`, `include/collision.h`, `src/collision.c`, and
`src/enemy/`, `src/object/`, `src/npc/`, `src/manager/`,
`src/projectile/`, `src/playerItem/`.

## The entity record (`Entity`, 0x88 bytes)

| offset | field | notes |
|---|---|---|
| 0x00 | prev, next | intrusive list links |
| 0x08 | kind | PLAYER 1, ENEMY 3, PROJECTILE 4, OBJECT 6, NPC 7, PLAYER_ITEM 8, MANAGER 9 |
| 0x09 | id | which enemy, object or NPC |
| 0x0a | type | form or variant (color, size) |
| 0x0b | type2 | |
| 0x0c | action | the state machine index |
| 0x0d | subAction | |
| 0x0e | timer | |
| 0x0f | subtimer | |
| 0x10 | flags | DID_INIT 0x1, SCRIPTED 0x2, DELETED 0x10, PERSIST 0x20, COLLIDE 0x80 |
| 0x14 | animationState | 0/2/4/6 = N/E/S/W |
| 0x15 | direction | 0-31. 0x80 not moving. 0xFF none |
| 0x20 | zVelocity | Q16.16 |
| 0x24 | speed | Q8.8 |
| 0x2c, 0x30, 0x34 | x, y, z | Q16.16 world pixels |
| 0x38 | collisionLayer | 1 bottom, 2 top, 3 both |
| 0x3d | iframes | |
| 0x3f | hitType | row in the collision matrix |
| 0x40 | hurtType | column |
| 0x41 | contactFlags | who hit me, with what (`COL_*` ids) |
| 0x44 | damage | |
| 0x45 | health | |
| 0x48 | hitbox | `Hitbox*` |
| 0x50 | parent | |
| 0x54 | child | |
| 0x68-0x87 | generic fields | per-kind use, via typed structs that extend `Entity` |

Enemies extend it (`Enemy`): `enemyFlags` (boss and so on), `homeX/Y` and
`rangeX/Y` for patrol leashes.

## Limits that shape everything

| limit | value | what happens at it |
|---|---|---|
| entities game-wide | 72 (`GetEmptyEntity` refuses at 71) | spawns silently fail |
| managers | 32 more, a separate pool, 64 bytes each | do not count against 72 |
| aux player entities | 7 | |
| GFX slots | 44, 0x200 bytes each | **the real wall.** See `08_PERFORMANCE.md` |
| dynamic OBJ palettes | 9 (6-14) | a failed load silently falls back to palette 0, so a sprite draws in the player's colors |
| hardware sprites | 128 OAM entries | `CopyOAM` stops at the limit |

A deleted entity's slot frees only at frame end. Delete-then-create in
one frame comes back empty in a busy room. To free a slot this frame, set
`ENT_DELETED` on a linked entity: `GetEmptyEntity`'s last pass evicts it.

## Entity lists and update

`gEntityLists[9]`. Kind maps to list through `{8,1,8,4,5,8,6,7,2,6}`.
`ram_UpdateEntities` (ARM, in IWRAM) walks every list each frame, then the
managers. An entity's update is `Actions[super->action](this)`. Enemies go
through `EnemyUpdate` with handler slots: 0 tick, 1 collision, 2
knockback, 3 death, 4 confused, 5 grabbed.

`CreateEnemy(id, form)`, `CreateObject(id, type, type2)`,
`CreateNPC(id, ...)`, `CreateProjectile*`, `CreateFx`, `CreateManager`. A
room's entity lists call these at load.

## Definitions (how an id becomes a sprite and a hitbox)

`EnemyDefinition` (`include/definitions.h`), indexed by enemy id in
`gEnemyDefinitions` (`src/enemy.c` line 51). A `MULTI_FORM` row points at
per-form sub-tables.

| field | meaning |
|---|---|
| gfx | sheet id and gfx type (fixed sheet vs swap) |
| paletteIndex | OBJ palette group |
| ptr.hitbox | hitbox |
| spriteIndex | `gSpritePtrs[]` entry: animations plus frames |
| spriteFlags | priority, collision on, draw mode, shadow |
| health | the one honest difficulty scalar |
| speed | Q8.8 |
| damageType | a **type id**, not hearts. The victim's handler decides what it means |
| collisionMask | |

`ObjectDefinition` (`src/objectDefinitions.c`) does the same for objects:
gfx and gfx type, palette, sprite index, priority, draw mode, shadow, or a
pointer to a per-type table.

**Re-skinning an enemy** means replacing the sheet its `gfx` names and the
palette `paletteIndex` names. Keep the frame layout and the animation
tables (see `09_ASSETS_AND_RESKIN.md`), and the AI, hitbox and
collision stay correct untouched.

## Damage and the collision matrix

`CollisionMain` tests overlapping hitboxes. A hit looks up
`gCollisionMtx[hitType * 34 + hurtType]` (173 rows by 34 columns of
`ColSettings`: knockback, iframes, damage, confusion, flags). Then a
handler runs. `CollisionDefault` knocks back at 16 times the setting. The
shield blocks hits from the facing direction.

`CalculateDamage` (`src/collision.c` line 248):

- Enemy hits player: `damage = tgt->damage`, divided by 4 with Nayru's
  charm and by 2 with Farore's, minimum 1, then `ModHealth(-damage)`.
- Player hits enemy: the item's damage, with QUICKSTART's charm
  multipliers (Farore times 1.5, Din times 2).

Contact ids (`include/collision.h`): `COL_LANTERN` 0x07, `COL_SMALL_GUST`
0x13, `COL_BOOMERANG` 0x14, `COL_ARROW` 0x15, `COL_BIG_GUST` 0x1b,
`COL_PACCI` 0x1d, `COL_SWORD_BEAM` 0x21. Some enemies die only to one:
**Spark only to the boomerang (0x14), Lakitu only to the Cane of Pacci
(0x1d).** Found by reading their collision handlers.

## Enemies

103 source files, ids 0x00-0x66. The full list is `src/enemy/`. The
roster QUICKSTART actually spawns, as `{id, form, roles, cost in GFX
slots, required item, theme}` (`src/game.c` around line 9420):

| level | enemies (form) | cost range |
|---|---|---|
| 1 | Beetle, Keese, Small Pesto, Tektite (red), Crow, Mini Slime, Octorok (red), Peahat, ChuChu (green), Rope | 1-4 |
| 2 | Octorok2, Octorok (blue), Slime, Stalfos (red, blue), Keaton, Helmasaur, Pesto (red), ChuChu (blue), Bob-omb, Bombarossa, Leever (red, blue), Mulldozer (red), Tektite (blue) | 1-4 |
| 3 | Moldorm, Ghini, Armos, Eyegore, Mulldozer (blue), Pesto (blue), ChuChu (red), Rock ChuChu, Spiny ChuChu, Spiked Beetle, Puffstool, Fireball Guy, Mini Fireball Guy, Bomb Peahat, Cloud Piranha, Spiny Beetle, ENEMY_50 | 2-8 |
| 4 | Like Like, Rupee Like (green, red, blue), Takkuri, Gibdo, Scissors Beetle, Moldworm, ENEMY_4D, Bow Moblin, Spear Moblin, Acro Bandit | 1-8 |
| 5 | Wizzrobe (fire, ice, wind), Golden Tektite, Golden Octorok, Golden Rope, Rollobite, Wisp (red, blue), Spark (needs Boomerang), Lakitu (needs Cane) | 1-6 |
| Elite | Darknut forms 0-3 (form 2 is 20 hp, form 3 is 26 hp), Ball and Chain Soldier, Madderpillar | 1-5 |

Roles (bitmask): CHAFF 0x01 (dies fast, safe in numbers), HEAVY 0x02
(armored, rationed), RANGED 0x04, FLYER 0x08 (ignores ground), AMBUSH 0x10
(hides, burrows), FAST 0x20 (speed 256 or more), SLOW 0x40 (speed 96 or
less), THIEF 0x80 (takes items or rupees).

Themes: FIRE, ICE, UNDEAD, BUG, AVIARY. One wave in four rolls a theme and
prefers entries carrying it.

**Left out of the roster, with reasons**: the Gyorg child, Sluggula, Wall
Master, ENEMY_64, and every boss part (Vaati, Mazaal, Gyorg, Gleerok,
Octorok Boss, ChuChu Boss pieces). They need scripted setup, a room
property or a dungeon entrance, or they crash on a bare `CreateEnemy`.
A new game that wants them must supply that setup.

**Multi-entity enemies**: a Madderpillar is about 7 live entities. An
Acro Bandit placement bursts into 6. Price them in entities, not
placements.

**Bosses QUICKSTART uses**: the ChuChu boss (green and electric forms)
and the Big Octorok. Each has a vetted arena allowlist, because a boss
needs open floor and its parts need GFX slots. Two bosses fit in a
cleared room. None fit on top of a live high-difficulty wave.

### Live caps (`sQuickStartLiveCaps`)

Per family, independent of difficulty: Darknut 2 to 3, Ball and Chain 3,
Madderpillar 1 (one chain), Acro Bandit 2, Rupee Like 3, Like Like 3,
Takkuri 3, with Wizzrobes generous by design. A theft cap exists because
"losing a shield twice is a story, five times is the run."

### The difficulty table (`sQuickStartDifficultyTiers`, generated)

Columns are the chance of each level. Density is the enemy count dial.

| step | L1 | L2 | L3 | L4 | L5 | Elite | density |
|---|---|---|---|---|---|---|---|
| 0 | 100 | 0 | 0 | 0 | 0 | 0 | 25 |
| 1 | 75 | 25 | 0 | 0 | 0 | 0 | 22 |
| 2 | 50 | 45 | 5 | 0 | 0 | 0 | 17 |
| 3 | 25 | 40 | 26 | 6 | 2 | 1 | 13 |
| 6 | 9 | 27 | 35 | 22 | 6 | 1 | 10 |
| 9 | 3 | 13 | 29 | 33 | 21 | 1 | 8 |
| 12 | 1 | 7 | 19 | 34 | 35 | 4 | 6 |

The user's rule: **"difficulty should not be about what tiers or types of
enemies are possible, but rather the chance that various tiers spawn."**
From step 3 up, no column is zero. `tools/quickstart/tier_curve.py`
generates it: a discrete gaussian whose peak walks from level 1 to level
4, with the Elite column damped to 18% and a per-column floor. Never
hand-edit the table.

## Objects (192 files, `src/object/`)

Interactive world pieces. The ones a generated world will lean on:

| object | use |
|---|---|
| pot, bush, giantRock, pushableRock, pushableStatue, pushableGrave, pushableFurniture | liftable, cuttable, pushable. Each stamps a special tile under itself |
| chestSpawner, specialChest, itemOnGround, heartContainer, rupee, fairy | rewards |
| lockedDoor, metalDoor, bossDoor, lightDoor, houseDoorExterior/Interior | doors. **A LOCKED_DOOR of type 0 waits on flag 0, which nothing sets. It never opens** |
| button, pressurePlate, hitSwitch, eyeSwitch, lightableSwitch, pullableLever, pushableLever, bigPushableLever, hittableLever | switches |
| lamp, flame, lightRay, litArea | light and darkness |
| trapdoor, rotatingTrapdoor, crackingGround | floor hazards |
| floatingPlatform, lavaPlatform, lilypadLarge/Small, minecart, railtrack | moving floors |
| fan, fanWind, whirlwind, steam | pushers |
| guruguruBar, fireballChain | rotating hazards |
| ladderUp, hiddenLadderDown, beanstalk | vertical links |
| warpPoint, minishPortalStone, jarPortal | warps and portals |
| smallIceBlock, bigIceBlock, frozenFlower | fire-rod puzzles |
| barrelSpiderweb, spiderWeb (projectile), removableDust (projectile) | Gust Jar targets |
| itemForSale | shop stock |
| deathFx, smoke, specialFx | effects. **A death borrows a slot for its DEATH_FX** |

**Doctrine: borrowed objects are only as portable as their art.** An
object that paints its look into the room's tilemap (a torch, a switch
drawn as tiles) works only in tilesets carrying those tiles. One that
carries its own sprite renders anywhere. For a re-skin, sort every object
you keep into "sprite" or "tilemap" and re-art accordingly.

## NPCs (87 files, `src/npc/`)

Script-driven characters. Each distinct NPC id costs a GFX sheet, and
some cost two (`LoadExtraSpriteData`). QUICKSTART reuses a few faces (the
`FACES` list in `scenario.py`: Zelda, Postman, Wheaton, Pita, Rem, Anju,
Kid) as quest givers and travelling kinstone fusers. It **sweeps every
vanilla NPC** out of a wave room, testing "is this ours" by a scripted
flag plus the Zelda id. That test once swept the fusers too, because
`QuickStartIsOurNpc(-1)` matched anything.

For a new game: author a small cast. Give each role (quest giver, fuser,
shopkeeper, hint) an NPC id with a re-skinned sheet. Keep the count low,
because every face is a sheet.

## Managers (57 files, `src/manager/`)

Invisible logic, kind 9, in their own pool. The ones that matter:

| manager | use |
|---|---|
| holeManager | hole transitions (`gHoleTransitions`) |
| bombableWallManager | bombable walls (act 0x2e) |
| lightManager, lightLevelSetManager | darkness and torches. Type 2 adds light when lit. Type 3 burns out after `field_0x36` seconds |
| tilePuzzleManager | tile-flip puzzles |
| fightManager | locked-room fights: close doors, spawn, open on clear |
| entitySpawnManager, delayedEntityLoadManager | timed spawns |
| flagAndOperatorManager | flag logic: AND/OR of flags sets a flag |
| secretManager, tileChangeObserveManager, destructibleTileObserveManager | react to tile changes |
| minishPortalManager | Minish portals (subtype 3) |
| ezloHintManager | context hints |
| regionTriggerManager | position triggers (do not use them for doors) |
| moveableObjectManager, pushableFurnitureManager | push mechanics |
| bridgeManager | bridges that appear |
| weatherChangeManager, rainfallManager, cloudOverlayManager, steamOverlayManager | ambience overlays |

**Transform points are managers, not objects.** Two scans that looked
only at objects got the Minish model wrong.

`fightManager` plus `flagAndOperatorManager` plus doors plus switches are
the vanilla toolkit for **lock-and-key rooms**. A generator should
compose them, not invent new ones.

## Projectiles (37 files) and player items (37 files)

Projectiles are kind 4: arrows, rocks, fire, ice, Moblin spears, Darknut
slashes, webs and dust. **They hold entity and GFX slots that the
live-enemy count never sees.** Pesto's dirt ball and the Spear Moblin's
spear both caused slot starvation. Player items are kind 8, one per
active item: sword, bomb, boomerang, arrows, gust, lantern, held object,
shield, beams.
