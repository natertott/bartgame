# 11. Traps

Every trap here cost the current project real time. They are grouped by
where they will bite the new game. The source doc is named where there is
more detail.

The new engine is built from scratch (`12_FROM_SCRATCH_ENGINE.md`). The
toolchain and engine traps below are TMC's. They matter when reading,
building or measuring TMC as the oracle. The world, generation and probe
traps apply to the new game directly.

## Toolchain (agbcc, C89)

| trap | defence |
|---|---|
| no `__umodsi3` or `__udivsi3`: an unsigned `%` or `/` by a runtime divisor fails at **link** | signed math: `(s32)(x & 0x7fff) % (s32)n`, or a subtract loop |
| a zero-extended byte counts as non-negative, so `(s32)some_u8 % n` turns unsigned | mask through a u32 call result, or loop |
| declarations must come before statements. `-Werror` | |
| objects whose source has `#ifdef VARIANT` are reused across variant builds, which makes hybrid ROMs | delete them before every variant build (`VARIANT_OBJS`), or have no variant flags |
| `build/` is not kept, so generators that read it are not reproducible | generators read sources |
| ids parsed by regex from headers drift from what was compiled | read `build/USA/enum_include/*.inc` |
| a table row a regex fails to parse silently shifts every later id (the first `extract_feel.py` run named row 0x46 Bow Moblin with Lakitu Cloud's values) | make every parser hold a row's place and fail loudly on one it cannot read |
| room flag numbers scattered over 24,000 lines: reusing one silently broke a sweep | one header that allocates every flag |
| `save.h`'s offset comments are wrong from `figurines` on | trust `offsetof`, not comments |

## Engine

| trap | defence |
|---|---|
| 72 entities, refused at 71, and a deleted slot frees only at frame end | create on a later frame, or set `ENT_DELETED` on a linked entity so `GetEmptyEntity` evicts it now |
| a death with no free entity freezes the enemy for 255 frames with no drop | keep an entity reserve (16) |
| projectiles and floor drops hold entities and slots the enemy count never sees | cap them per kind |
| 44 GFX slots. Fixed sheets are shared per kind, swap sheets cost slots per instance (measured: 6 Stalfos hold 6x the slots, 6 Octoroks one sheet) | price waves by distinct kinds plus swap instances (`08_PERFORMANCE.md`) |
| a freed sheet stays reserved for a median 663 frames | spawn gates must not trust free counts during a burst |
| `GFX_SLOT_FOLLOWER` slots look free and are not | count them as used |
| 9 dynamic OBJ palettes. A failed load silently uses palette 0 | count pending loads. Share palettes by theme |
| an empty spawn deal retries every frame | make refusals cheap, and refuse up front |
| a tile edited after `UpdateScrollVram` does not show in a still room | raise `gUpdateVisibleTiles` and call `UpdateScrollVram()` |
| an entity's own init can undo what you wrote on its spawn frame (`ItemForSale_Init` clears `interactType`) | wait for `action == 1`, then write |
| act tile 0x08 crumbles into a pit once walked on | never treat it as ground |
| a tileset can list a tile type and draw nothing for it | probe the screen per theme |
| tile type labels in `tiles.h` are one off around the torches: unlit is 117, lit 118, and 119 is a button | measured in the ROM |
| the Gust Jar only frees a web while pulling back, and dust only from 23-36 px straight below | place targets with that approach space |
| item sprites (sprite 322) carry an absolute palette. Setting `entity->palette` does nothing | read the OAM entry, not RAM |
| a talkable NPC's 40x40 box wins over any lift inside it | keep liftables out of talk boxes |
| a pot off its tile centre cannot be lifted | spawn on tile centres |
| the kinstone menu loads its art over OBJ tiles 0x40-0x2CF | harmless: `RestoreGameTask` re-uploads slots |
| a ROM call that takes seconds looks like a freeze | measure with a larger budget before calling it a hang |

## World and generation

| trap | defence |
|---|---|
| **a collision flood cannot see a ledge** | ledges are directed edges. `component_map.py` walks off every boundary tile |
| **walkable collision is not land**: water and swamp are open | reject act 0x0d, 0x0e, 0x0f, 0x10, 0x12, 0x13 for anything that stands |
| "can enter" is not "can explore" | reach checks ask for a feature's component |
| a region's inner cost is not its entry price | price edges, not rooms |
| a wave counts every enemy in the room | spawn only on the player's component |
| puzzles over a door landing read as solved on arrival | reserve landings and their approach first |
| a hole whose transition is cancelled leaves the player invisible in PLAYER_FALL forever | every hole has a valid target |
| a LOCKED_DOOR of type 0 waits on flag 0, which nothing sets | every lock is tied to a placed key or switch, and the flood checks it |
| containment that cancels a transition looks like a hole to nowhere | in a generated area every room belongs to the area, so there is nothing to contain |
| "the southwest pocket" was the mid-west pocket, in two places, causing two bugs | name places by coordinates |
| transform points are managers, not objects | scan managers too |
| borrowed objects that paint into the tilemap only work in tilesets that carry those tiles | prefer sprite objects |
| a vanilla puzzle could be bypassed by lifting its pots | every puzzle is solved, and its bypasses tested, in place |
| QUICKSTART's random `ITEM` chain step never fired, so the world never grew | place key items deliberately in the mission graph |

## Probes and the harness

| trap | defence |
|---|---|
| **a negative result with no control** | point the same probe at a known-working case. Doctrine 8 |
| `EnemyCreateProjectile` does not set the projectile's parent | find a shooter's shots by appearance in an otherwise empty room, not by parent |
| an enemy that "never fires" may just not be facing the player: the Octorok spits only at the end of a walk, facing the player | trace long, with the enemy in the player's line (`feel_trace.py --at`) |
| a probe that forces state goes stale when encodings change | regenerate its expectations from the twin |
| a Python copy of a rule tests the copy | call the ROM (`callrom.py`) |
| `callrom.call_keep` can fail or segfault in a crowded room | one question per boot. Use a quiet seed |
| teleporting onto a hole lets `RespawnPlayer` act first | set position and action in the same frame |
| a probe's start can leave the pause menu open | dismiss menus before reading the room |
| the test kit does not always put the sword on B | set the button explicitly |
| `pkill -f` or `pgrep -f` on a script name matches your own shell | match on something only the target carries |
| seeds shift wave draws, so a probe that assumes 60 fps breaks | pin what the probe does not test |
| a checker passing for the wrong reason (a broken face loaded no sheet) | when a fix turns a check red, look at why it was green |
| no baseline: pre-existing conditions read as regressions | run the sweeps before your first change and keep the output |
