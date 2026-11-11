# Curated enemy restoration

The original nine production enemy IDs, names, health, selected sprites and AI remain unchanged. New IDs 9–79 correspond one-for-one to all 71 curated handoff picks (57 source IDs). IDs 80/81 restore the two giant ChuChu encounters,82 restores Big Octorok, and83 is the new Cream summit encounter using the Gleerok tool/weakpoint loop. The213 raw reference rows are provenance, not213 spawnable enemies; excluded scripted bosses are not misrepresented as generic recolored combatants.

## Source and translation rules

The authoritative roster/stat ledger is `docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md`, `src/game.c` curated arrays, and `bartgame/docs/enemy-prototypes/source_catalogue.json`. Every family's original `src/enemy/*.c` was examined for its collision and lifecycle callbacks. Source health is in the existing game's health units. Contact damage is2 units ordinarily,4 for heavy attacks; a collision-row ID is never used as a damage amount. The new world uses original handoff role bits: chaff1, heavy2, ranged4, flyer8, ambush16, fast32, slow64, thief128.

Source special health255 means a lifecycle, not128 sword hits. Bobomb arms, can be stunned/carried, and explodes; Bombarossa is a bobbing floating mine knocked into a surface. Rollobite curls, can be lifted and thrown, and resolves when plugging a pit. Wisp is dispersed by its counters and suppresses item use for 600 frames. Spark takes only a boomerang, then spawns an actual bottle-catchable fairy. Madderpillar uses a32 HP tail and armored head/body; tail damage starts a120-frame protected rage.

Mechanics retain deliberate tells and committed directions. Rope warns30 frames before its416Q8 charge (gold640); Octorok uses 30/60/60/90 walks and24–80 rest, with the golden three-shot sequence. Golden Tektite prepares6 frames and has576Q8 movement. Blue Tektite chains three hops. Spiked Beetle is shield/Pacci-flipped for 150 frames. Helmasaur and Puffstool require60 small gust contacts to strip their protection. Peahat is grounded by gust or boomerang. Lakitu loses its cloud to Pacci. Eyegore requires a front-facing open eye and3 arrow hits, or a beam. Darknut blocks the front, commits to its visible cut, and exposes its rear/recovery; forms keep12/12/20/26 HP.

Like Like captures95 frames and returns a stolen shield on defeat. Rupee Like captures60 frames and returns stolen gilt. Takkuri carries stolen currency visibly until defeated. Gibdo's fire transition replaces its wrapped form with a real Stalfos in the same actor slot and invalidates the streamed frame. Pesto can lift minish Bloom; ENEMY_50 creates three independently hit-tested decoys and captures Bloom. ENEMY_4D is the separate anchored extending/retracting ball-chain enemy, not a renamed basic pursuer. Acro Bandit builds an actual six-actor stack which collapses into individually hittable members.

Segmented enemies draw and hit-test each part at the same trail coordinates. Moldorm has4 body/tail pieces, Moldworm8, Madderpillar6 in addition to the head. Front armor and tail vulnerability are spatial rules. Flail soldiers use the actual visible orbit/extension location for damage and parrying. Elemental wizard projectiles burn, freeze, or push; warning poses precede each cast. Bomb Peahat shows a ground impact marker and drops a real explosive.

## Boss setup and explicit adaptations

The giant ChuChu's gelatin is a48-unit peel meter:1 small-gust contact,12big-gust,8 per ordinary weapon stroke. The original QuickStart weapon fallback is preserved, so a randomly drawn boss can be cleared without a mandatory jar. Its toppled core is exposed150 frames. Aggregate core health24/32 is an original-engine adaptation of the source multipart proxy lifecycle, not a claim that the source 255 is its actual health. Electric charge blocks peeling during120of180 frames and has a visible charged pose.

Big Octorok retains the source phase health sequence3,1,3,1,3,1,3,0,150 frame transitions and24 frame contact spacing. Reflected stones work; the frozen odd phases show an entirely separate frozen art strip, and a lantern/fire hit from the tail consumes that phase. The original handoff's QuickStart ordinary-weapon fallback also remains. It does not become an arbitrary health sponge.

The Cream boss uses a plated head, Pacci flip,210 frame bowed-neck ramp, an elevated back core and fire breath. Its32 HP is new-game balance. The core collider is aligned to the actual local32 × 64 art core at(16,42); the head/body never accept ordinary substitute damage. It is a scripted summit encounter with its own completion callback, separate from the existing Blight Heart.

## Native art and bounded runtime

`art/handoff_enemies.py` appends74 enemy sheets plus one common12-frame parts sheet:2,540 native frames. `art/cream_actors.py` owns the separate32 × 64summit boss. Each strip starts with 8 poses×4facings:idle,walk1,walk2,tell,attack,recover,hurt,buried. Five sheets append a second32 frames for permanent bare states or Big Octorok ice. Ordinary bodies are16 × 16; larger humanoids/columns are32 × 32. Palette banks are the unchanged existing blight/fx banks. Purple accents and selective ivory/gold highlight identify hostile living forms; silhouettes and damage tells carry the main meaning. No source game pixels were copied and no high-resolution image was scaled down.

New actor art is streamed one current frame, not a full sheet. Shared parts cost 48 hardware tiles. Four24-sample trail histories cost 400bytes. Enemy projectile count is bounded12. Family/live-cost checks run at admission; multipart entities are priced5/9/7 for Moldorm/Moldworm/Madderpillar and6 for Acro Bandit. New required-counter families are admitted only with appropriate owned tools, and Rollobite also requires a pit. Teleports are bounded and checked against walkable collision geometry. Existing forest encounter selection is preserved.

Source art inspection: `/workspace/setup/handoff-enemies/bestiary-source.png` and its manifest. These are source previews, not emulator evidence. Root integration supplies actual ROM verification; a clean host syntax check has passed for the module. Mechanical test results are recorded separately when run; this document does not claim unperformed native-run verification.

## Complete curated coverage

Speed is sourceQ8.8,256=1 pixel/frame. Family notes in `gLegacyEnemyDefs` and the dispatch/collision code specify the actual mechanic rather than treating shared source names as implementation proof.

| New ID | Source enemy / form | Tier | HP | Speed | Source AI |
|---:|---|---|---|---:|---|
| 9 | `BEETLE` 0 | 1 | 1 | 256 | `src/enemy/beetle.c` |
| 10 | `KEESE` 0 | 1 | 2 | 256 | `src/enemy/keese.c` |
| 11 | `SMALL_PESTO` 0 | 1 | 1 | 64 | `src/enemy/smallPesto.c` |
| 12 | `TEKTITE` 0 | 1 | 3 | 256 | `src/enemy/tektite.c` |
| 13 | `CROW` 0 | 1 | 2 | 320 | `src/enemy/crow.c` |
| 14 | `MINI_SLIME` 0 | 1 | 1 | 128 | `src/enemy/miniSlime.c` |
| 15 | `OCTOROK` 0 | 1 | 2 | 96 | `src/enemy/octorok.c` |
| 16 | `PEAHAT` 0 | 1 | 4 | 128 | `src/enemy/peahat.c` |
| 17 | `CHUCHU` 0 | 1 | 4 | 32 | `src/enemy/chuchu.c` |
| 18 | `ROPE` 0 | 1 | 4 | 128 | `src/enemy/rope.c` |
| 19 | `OCTOROK2` 0 | 2 | 2 | 96 | `src/enemy/octorok2.c` |
| 20 | `OCTOROK` 1 | 2 | 3 | 96 | `src/enemy/octorok.c` |
| 21 | `SLIME` 0 | 2 | 2 | 64 | `src/enemy/slime.c` |
| 22 | `STALFOS` 0 | 2 | 4 | 224 | `src/enemy/stalfos.c` |
| 23 | `STALFOS` 1 | 2 | 4 | 224 | `src/enemy/stalfos.c` |
| 24 | `KEATON` 0 | 2 | 4 | 256 | `src/enemy/keaton.c` |
| 25 | `HELMASAUR` 0 | 2 | 4 | 256 | `src/enemy/helmasaur.c` |
| 26 | `PESTO` 0 | 2 | 4 | 64 | `src/enemy/pesto.c` |
| 27 | `CHUCHU` 2 | 2 | 4 | 32 | `src/enemy/chuchu.c` |
| 28 | `BOBOMB` 0 | 2 | lifecycle | 128 | `src/enemy/bobomb.c` |
| 29 | `BOMBAROSSA` 0 | 2 | lifecycle | 256 | `src/enemy/bombarossa.c` |
| 30 | `LEEVER` 0 | 2 | 6 | 128 | `src/enemy/leever.c` |
| 31 | `MULLDOZER` 0 | 2 | 6 | 96 | `src/enemy/mulldozer.c` |
| 32 | `TEKTITE` 1 | 2 | 6 | 320 | `src/enemy/tektite.c` |
| 33 | `LEEVER` 1 | 2 | 8 | 128 | `src/enemy/leever.c` |
| 34 | `MOLDORM` 0 | 3 | 10 | 384 | `src/enemy/moldorm.c` |
| 35 | `GHINI` 0 | 3 | 9 | 256 | `src/enemy/ghini.c` |
| 36 | `ARMOS` 0 | 3 | 10 | 160 | `src/enemy/armos.c` |
| 37 | `EYEGORE` 0 | 3 | 3 | 256 | `src/enemy/eyegore.c` |
| 38 | `MULLDOZER` 1 | 3 | 8 | 96 | `src/enemy/mulldozer.c` |
| 39 | `PESTO` 1 | 3 | 4 | 64 | `src/enemy/pesto.c` |
| 40 | `CHUCHU` 1 | 3 | 4 | 32 | `src/enemy/chuchu.c` |
| 41 | `ROCK_CHUCHU` 0 | 3 | 4 | 64 | `src/enemy/rockChuchu.c` |
| 42 | `SPINY_CHUCHU` 0 | 3 | 4 | 32 | `src/enemy/spinyChuchu.c` |
| 43 | `SPIKED_BEETLE` 0 | 3 | 4 | 96 | `src/enemy/spikedBeetle.c` |
| 44 | `PUFFSTOOL` 0 | 3 | 1 | 64 | `src/enemy/puffstool.c` |
| 45 | `FIREBALL_GUY` 0 | 3 | 4 | 64 | `src/enemy/fireballGuy.c` |
| 46 | `MINI_FIREBALL_GUY` 0 | 3 | 1 | 64 | `src/enemy/miniFireballGuy.c` |
| 47 | `BOMB_PEAHAT` 0 | 3 | 4 | 192 | `src/enemy/bombPeahat.c` |
| 48 | `CLOUD_PIRANHA` 0 | 3 | 4 | 256 | `src/enemy/cloudPiranha.c` |
| 49 | `SPINY_BEETLE` 0 | 3 | 4 | 352 | `src/enemy/spinyBeetle.c` |
| 50 | `ENEMY_50` 0 | 3 | 9 | 256 | `src/enemy/enemy50.c` |
| 51 | `LIKE_LIKE` 0 | 4 | 20 | 64 | `src/enemy/likeLike.c` |
| 52 | `RUPEE_LIKE` 0 | 4 | 16 | 96 | `src/enemy/rupeeLike.c` |
| 53 | `RUPEE_LIKE` 2 | 4 | 16 | 96 | `src/enemy/rupeeLike.c` |
| 54 | `RUPEE_LIKE` 1 | 4 | 16 | 96 | `src/enemy/rupeeLike.c` |
| 55 | `TAKKURI` 0 | 4 | 4 | 320 | `src/enemy/takkuri.c` |
| 56 | `GOBDO` 0 | 4 | 20 | 96 | `src/enemy/gibdo.c` |
| 57 | `SCISSORS_BEETLE` 0 | 4 | 20 | 128 | `src/enemy/scissorsBeetle.c` |
| 58 | `MOLDWORM` 0 | 4 | 20 | 128 | `src/enemy/moldworm.c` |
| 59 | `ENEMY_4D` 0 | 4 | 16 | 128 | `src/enemy/enemy4D.c` |
| 60 | `BOW_MOBLIN` 0 | 4 | 8 | 256 | `src/enemy/bowMoblin.c` |
| 61 | `SPEAR_MOBLIN` 0 | 4 | 8 | 256 | `src/enemy/spearMoblin.c` |
| 62 | `ACRO_BANDIT` 0 | 4 | 1 | 128 | `src/enemy/acroBandit.c` |
| 63 | `WIZZROBE_FIRE` 0 | 5 | 8 | 192 | `src/enemy/wizzrobeFire.c` |
| 64 | `WIZZROBE_ICE` 0 | 5 | 8 | 192 | `src/enemy/wizzrobeIce.c` |
| 65 | `WIZZROBE_WIND` 0 | 5 | 8 | 192 | `src/enemy/wizzrobeWind.c` |
| 66 | `TEKTITE_GOLDEN` 0 | 5 | 64 | 576 | `src/enemy/tektiteGolden.c` |
| 67 | `OCTOROK_GOLDEN` 0 | 5 | 64 | 96 | `src/enemy/octorokGolden.c` |
| 68 | `ROPE_GOLDEN` 0 | 5 | 64 | 128 | `src/enemy/ropeGolden.c` |
| 69 | `ROLLOBITE` 0 | 5 | lifecycle | 256 | `src/enemy/rollobite.c` |
| 70 | `WISP` 0 | 5 | lifecycle | 128 | `src/enemy/wisp.c` |
| 71 | `WISP` 1 | 5 | lifecycle | 384 | `src/enemy/wisp.c` |
| 72 | `SPARK` 0 | 5 | lifecycle | 256 | `src/enemy/spark.c` |
| 73 | `LAKITU` 0 | 5 | 6 | 128 | `src/enemy/lakitu.c` |
| 74 | `DARK_NUT` 0 | Elite | 12 | 96 | `src/enemy/darkNut.c` |
| 75 | `DARK_NUT` 1 | Elite | 12 | 96 | `src/enemy/darkNut.c` |
| 76 | `DARK_NUT` 2 | Elite | 20 | 96 | `src/enemy/darkNut.c` |
| 77 | `DARK_NUT` 3 | Elite | 26 | 96 | `src/enemy/darkNut.c` |
| 78 | `BALL_CHAIN_SOLIDER` 0 | Elite | 16 | 128 | `src/enemy/ballChainSoldier.c` |
| 79 | `MADDERPILLAR` 0 | Elite | 32 tail; 255 proxy source | 224 | `src/enemy/madderpillar.c` |

## Satchel and directed Cream atlas

`gear_menu.c/h` adds a separate possession grid and a map of the Cream's fifty traversal components. Existing three pause pages remain available. The Satchel uses the selected UI frame theme, one native 16 × 16 icon per owned possession and the existing A/B/L assignment convention. Twelve current icons borrow only the reserved HUD icon region; the world HUD invalidates and restores them on return. It never loads the complete item sprite sheet into OBJ memory.

The atlas shows twenty-five room rectangles split into upper and lower shelves, with distinct C/F/H/D/T/G/B event marks and full words beside the selected room. Directed arrows and a route list distinguish walking, climbing, dropping and cave links, including destinations on other rows. Press A for a room preview derived from the same profiles, routes and content spots as the live room. Preview generation does not mutate the active room, collision, actors, graphics, or persistent state. Unvisited rooms remain uncharted until a map is owned. A blinking player marker uses the actual position in the current room.

BG0 allocation is bounded at 327 tiles within the existing 328-tile text pool; icon uploads are twelve 128-byte frames. The menu explicitly owns BG3's 32 × 32 map and character block while open, then restores the previous configuration. Entering from the older full-screen menu first restores that menu's borrowed world character memory and input hook. This state handoff was checked after an actual mGBA capture exposed incorrect inherited character-bank selection; final native screenshots are recorded by the root integration report.

## Verification and final mechanic corrections

A native mGBA review of frozen integration3 passed all 21 Satchel/atlas checks: entry from the original pause, exact native icon bytes, additional-sword assignment, page navigation, overview/zoom, bounded BG0 canvases, unchanged room terrain/collision, return to the original menu and world, restoration of BG3 and HUD icons, and direct access from the Cream map tab. Unedited screenshots and the disclosed inventory/navigation fixtures are in `/workspace/setup/curdled-cream/gear-ui-native3/`. The menu also now queues short button presses during a redraw in VBlank; the next frozen integration repeats that acceptance check with the queue enabled.

The real enemy-module host harness passed 547,662 assertions under AddressSanitizer and UndefinedBehaviorSanitizer (inherited fixed-point shift idioms excluded). It exercises all 75 added forms for 1,800 ticks, the weapon/facing/phase matrix, armor removal and matching art, capture/escape, multipart weak points, original boss phase counts, natural Rollobite pit trajectories and native frame bounds. Deterministic host geometry and player-status stubs are explicitly not emulator proof. Harness and results: `/workspace/setup/handoff-enemies-syntax/`.

Native mGBA execution additionally proves the actual held-shield flip, Gust helmet/cap removal, Pacci cloud removal, boomerang Spark kill, lantern Gibdo transition, Slime division, Madderpillar tail damage/rage and giant ChuChu peel/core flow. The room traversal review completed the Cream peak encounter after earning all three real rewards: Pacci struck the visible head, Bloom climbed its bowed ramp to height 16, and sixteen actual two-damage sword hits defeated the 32 HP core and entered the win state. No boss health/state, reward, completion or player-health assignment supplied that result. Report and unedited footage: `/workspace/setup/curdled-cream/runtime-review3/peak-combat.json` and `peak-core-combat.gif`.

A source review also corrected capture damage rather than leaving grabs harmless: Ghini and its mirage counterpart bite for 4, Gibdo has four 8-unit squeezes, a minish Pesto captive takes 2 periodically, Moldworm's natural tail release deals 16, and a shieldless LikeLike timeout deals 1. These callbacks use the existing damage pipeline, including charms, food, bottled fairies and death, while preserving an alive captive's held pose. Early escape stops damage and prevents shield theft. Peahat's natural 60-frame grounded rest keeps a sword-only early wave solvable; its 150-frame tool counter remains stronger. Rejected-hit particles and sounds are throttled to one per six ticks without changing guard or damage timing.

## Native art and registered raised contact

`art/handoff_enemies.py` adds74 enemy sheets and a12-frame parts sheet,
containing2,540 native indexed frames. Ordinary creatures use16×16 hardware
canvases; humanoids and the three added legacy bosses use32×32. The peak's
separate32×64 painting is owned by `art/cream_actors.py`. Existing approved
sprites and all sixteen existing OBJ palettes remain protected. The new
paintings use the existing blight bank, with the existing gold/FX bank for
rare golden forms. Family silhouettes describe actual motion: jointed hopping
legs, propellers, hinged jaws, swelling jelly, planted armor and drawn weapons.
Permanent cap/helmet/cloud/rock removal has a separate32-pose strip, so ordinary
recovery never falsely advertises exposed flesh. Big Octorok has an explicit
frozen strip. Source atlases are labelled source art, separately from mGBA.

Native painter validation passes123,899 canvas, order, coordinate and4bpp ink
checks. Independent ROM decoding matches all2,540 authored frames exactly.
Actual emulator presentation compares each queued source frame with the next
VBlank's uploaded payload, including4/16/32-tile bodies. It does not compare a
newly queued frame with the previous frame's still-resident graphics.

The peak's bowed neck/back is a real temporary16px support plane. The player
queries its exposed physical footprint before gravity and before deriving a
sword box. Standing and attacking retain z16 and zero vertical velocity;
descending jumps land onto that plane and ordinary gravity resumes when
leaving it. The boss AI never changes the player's height after collision has
already captured a sword box. Jump takeoff also starts at the supporting
surface, preserving the original0.5px takeoff in every ordinary room. The
painted plated head has its own Pacci box and matching fire-breath origin;
ordinary body contact cannot impersonate a head hit.

A150-assertion sanitized host regression extracts the actual player update,
jump, attack and sword-bound functions with the actual selected18-frame
Step-and-cut tables. It verifies identical collision/display boxes before and
after boss AI, stable support through the full swing and idle, platform jump
launch/landing, walk-off gravity, normal-floor takeoff and support retirement.
Integration4 additionally records native attack frames at z16/zvel0 and exact
blade/source-box agreement. The small subsequent jump-takeoff correction is
identified separately until its next native build is reviewed.

Integration4 native review passes264 checks, including all admitted forms,
actual equipped-tool counters, capture damage, escape/theft, an actual curled
Rollobite R-lift/R-throw into an existing generated hole, and three biomes.
The pitless annex correctly excludes Rollobite; its separate Forest pit case
supplies that environment.74 admitted forms retain13,320/13,320 sampled
updates. Six600-frame new-roster stress cases retain3,600/3,600 updates;
separate cost26 tests admit12 real heavy actors including a complete
Madderpillar and three flail guards in Forest/Cream/annex, retaining another
1,800/1,800 updates. Their19 checks include exact streamed frames and bounded
OBJ/OAM use. Peak observed world allocation is760 of876 reserved-world tiles;
peak observed OAM is58 of128. These are disclosed samples and fixtures, not a
universal frame-rate claim. The native Satchel/atlas repeat passes27 checks,
including two-frame presses during redraw, eventual input-queue drain,
assignment, zoom, and terrain/BG3/HUD restoration.
