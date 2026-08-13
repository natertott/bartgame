# QUICKSTART vanilla inventory: everything reusable, graded

The F8 catalog. Content planning should draw from this table, not from
memory. Sources: `src/enemy/`, `src/npc/`, `src/object/`, the item and
area tables, and the QUICKSTART rosters as shipped. Grades are honest
about their basis: rows marked (m) are measured or already running in the
mode; everything else is assessed from source and needs the usual
budget/arena checks before shipping (the Electric Chuchu - one spawn
experiment, three latent bugs - is the calibration case for what
"assessed" hides).

**Grades**
- **A** - in use in the mode today
- **B** - drop-in candidate: standalone AI, overworld-viable, no arena
- **C** - needs an audit first: terrain/projectile/VRAM questions
- **D** - heavy: arena-, macro- or cutscene-bound; its own project
- **X** - excluded on principle or pointless here

## 1. Enemies

The wave rosters draw levels 1-5; minibosses draw level 5 + DARK_NUT
forms; the boss roll spawns CHUCHU_BOSS (both forms).

| Enemy (id) | Grade | Notes |
|---|---|---|
| OCTOROK (0) r/b | A (m) | levels 1/2 |
| CHUCHU (1) g/r/b | A (m) | levels 1/2/3 |
| LEEVER (2) r/b | A (m) | levels 1/2 |
| PEAHAT (3) | A (m) | level 2 |
| ROLLOBITE (4) | A (m) | level 3 |
| DARK_NUT (5) x4 forms | A (m) | level 4 + miniboss roster |
| HANGING_SEED (6) | X | prop-like, tree-bound |
| BEETLE (7) | A (m) | level 1; the F1 swarm's bodies |
| KEESE (8) | A (m) | level 1 |
| DOOR_MIMIC (9) | C | door prop-enemy; placement is everything |
| ROCK_CHUCHU (10) | A (m) | level 3 |
| SPINY_CHUCHU (11) | B | sibling of shipped chuchus |
| CUCCO_CHICK_AGGR (12) | B | the revenge-swarm chick; comedy option |
| MOLDORM (13) | A (m) | level 2 |
| ENEMY_E (14) | X | unknown/unnamed |
| MOLDWORM (15) | A (m) | level 4 |
| SLUGGULA (16) | A (m) | level 2 |
| PESTO (17) r/b | A (m) | levels 2/3 |
| PUFFSTOOL (18) | A (m) | level 3; 8-slot sheet - budget hog (m) |
| CHUCHU_BOSS (19) g/b | A (m) | the region boss, both forms; death machinery single-family only (m) |
| LIKE_LIKE (20) | A (m) | level 1 |
| SPEAR_MOBLIN (21) | A (m) | level 3; 8-slot sheet (m) |
| BUSINESS_SCRUB (22) | C | projectile-deflect duel; also a merchant hook |
| RUPEE_LIKE (23) g/r/b | A (m) | levels 2/3/4 |
| MADDERPILLAR (24) | C | cave enemy; check overworld tiles |
| WATER_DROP (25) | X | dungeon drip |
| WALL_MASTER (26/35) | C | grab-warp AI - could feed F1c stakes (warp-out punishment) |
| BOMB_PEAHAT (27) | B (m) | measured cheap as a boss escort (budget doc) |
| SPARK (28) | A (m) | level 3; F1 swarm; measured-cheap escort |
| CHASER (29) | C | rolling hazard; lane-bound |
| SPIKED_BEETLE (30) | A (m) | level 3 |
| SENSOR/BLADE_TRAP (31/47), TORCH_TRAP (73) | C | room hazards, not wave enemies - future trap-room kind |
| HELMASAUR (32) | A (m) | level 2 |
| FALLING_BOULDER (33) | C | hazard rain - a wave modifier candidate |
| BOBOMB (34) | A (m) | level 1 |
| GLEEROK (36) | D | arena boss: neck/lava/tiles |
| VAATI_* (37,74,75,79,81,82,84,90,95) | X | endgame cutscene machinery |
| TEKTITE (38) r/b | A (m) | levels 2/3 |
| WIZZROBE_WIND (39) | B | only ICE/FIRE shipped; same family |
| WIZZROBE_FIRE/ICE (40/41) | A (m) | level 5; F1 swarm; projectile sheets load ungated (m) |
| ARMOS (42) | C | statue-activation; placement-keyed |
| EYEGORE (43) | C | arrow-gated fight - a bow-check duel room |
| ROPE (44) | A (m) | level 1 |
| SMALL_PESTO (45) | B | swarm filler |
| ACRO_BANDIT (46) | A (m) | level 1; GANG - capped at 2 placements, the one measured CPU hazard |
| KEATON (48) | A (m) | level 3; the scavenger thief |
| CROW (49) | A (m) | level 1 |
| MULLDOZER (50) r/b | A (m) | levels 2/3 |
| BOMBAROSSA (51) | A (m) | level 2 |
| WISP (52) r/b | A (m) | level 3/4 |
| SPINY_BEETLE (53) | A (m) | level 4 |
| MAZAAL_* (54,55,56,68) | D | multi-entity macro boss; wants its own room |
| OCTOROK_BOSS (57) | D | the lantern-gated ice boss; damage audit + arena |
| FLYING_POT (58) | B | ambush prop-enemy; pairs with the pot quest |
| GOBDO (59) | A (m) | level 4 |
| GOLDEN OCTOROK/TEKTITE/ROPE (60/61/62) | B | the golden-enemy fusion (KINSTONE_55 is wired!) - rare-spawn payoff waiting to exist |
| CLOUD_PIRANHA (63) | C | cloud-terrain; hub-top only |
| SCISSORS_BEETLE (64) | A (m) | level 4 |
| CUCCO_AGGR (65) | B | the full revenge swarm; F1c stake or comedy event |
| STALFOS (66) r/b | A (m) | level 3 |
| FLYING_SKULL (67) | B | thrown-skull hazard |
| TAKKURI (69) | A (m) | level 4; also the THIEF bird - F1c rupee-stealer candidate |
| BOW_MOBLIN (70) | A (m) | level 2; 8-slot sheet (m) |
| LAKITU (71) + CLOUD (72) | A (m) | level 4 |
| GHINI (78) | A (m) | level 3 |
| BALL_CHAIN_SOLIDER (76) | A (m) | level 5 |
| GIBDO | C | mummy; sheet cost unknown |
| SLIME/MINI_SLIME (86/87) | B | splitting slime - gauntlet flavor |
| FIREBALL_GUY/MINI (88/89) | C | fire variant of slime; check projectiles |
| GYORG_* (92-99) | D | flying multi-part finale boss |
| DUST (83), CURTAIN (94), TREE_ITEM (101), ENEMY_4D/50/64/66 | X | props/unknowns |

**Boss ladder** (each is its own project, per F3's lesson):
CHUCHU_BOSS both forms A(m) → next cheapest is probably OCTOROK_BOSS
(single entity + object partner) → GLEEROK (arena tiles) → MAZAAL (full
macro) → GYORG (flying multi-part). All need: damage audit, arena audit,
budget measurement, death-path audit *outside their vanilla arenas* -
the chuchu needed all four and it was the easy one.

## 2. NPCs

Every mode room sweeps vanilla NPCs; QUICKSTART NPCs are ZELDA-kind with
custom scripts (givers, fusers, hints, merchant). Reusable machinery:

| NPC / system | Grade | Notes |
|---|---|---|
| ZELDA as generic interactable | A (m) | every giver/fuser/hint |
| stockwell shop machinery | A (m) | the hub shop's carry-to-buy flow |
| greatFairy | A (m) | fairy-room content kind |
| bladeBrothers (dojo masters) | B | skill-teaching NPCs - the sword-skill grant path (pairs with the pedestal idea) |
| guard / guardWithSpear | C | THE F2 stealth quest's line-of-sight AI - research spike target |
| syrup / picolyteBottle | B | potion-brewing flavor for a shop variant |
| dampe / ghostBrothers / gina | B | graveyard flavor; Gina already hosts a ? room |
| malon/talon/epona/cow/cucco | B | ranch ambience; cuccoMinigame object exists too |
| carlov/figurine gallery | X | save-file metagame; EWRAM/asset heavy; retired by design |
| postman/mailbox | X | story mail; could someday deliver run summaries (whimsy, not plan) |
| tingleSiblings | X | fusion menu alternates; our fusers replace them |

## 3. Objects (the prop toolbox)

| Object | Grade | Notes |
|---|---|---|
| POT / pot contents | A (m) | quests, lotteries, fairy pots |
| GROUND_ITEM | A (m) | every reward in the mode |
| HITTABLE/PUSHABLE LEVER, EYE/LIGHTABLE SWITCH, PRESSURE_PLATE | B | the whole switch-puzzle vocabulary, unused so far - Phase D's lever rooms |
| CHEST (+ chestSpawner) | C | the user's chest-contents research question - probe first |
| LOCKED_DOOR + graveyardKey | B | a real key-and-lock pair - THE key-item logic's natural test asset |
| MINECART (+ door) | C | ride system; lane data per room |
| BEANSTALK | X (m) | climbs out of the ring; containment cancels it (deliberate) |
| BIG_VORTEX | A (m) | deleted on the roof; usable as a placed warp elsewhere if ever wanted |
| fan/fanWind, guruguruBar | C | wind pushers - movement puzzle flavor |
| pushableRock/Statue/Grave | B | block puzzles; grave pairs with Royal Valley if ever un-blocked |
| jarPortal, minishPortalStone | A (m) | the Minish shrink path (works; #103 rendering bug pending) |
| cuccoMinigame | C | a timed minigame host - quest-kind candidate |
| frozen* (flower/octorok/waterElement) | D | Temple of Droplets ice system |
| kinstoneSpark, fusionMenuNPC | A (m) | the fusion economy |

## 4. Items

| Item family | Grade | Notes |
|---|---|---|
| Weapons/tools in tier table | A (m) | bow, bombs, boomerangs, jar, cane, rods, boots, mitts, cape, flippers... |
| Charms (Nayru/Farore/Din) | A (m) | run-long; the F4 template |
| Skill scrolls | A (m) | selection rounds + drops |
| Books, pies, medals, unused quest items | B | F4's charm/curse bodies - ids exist, icons exist |
| Dungeon MAP / COMPASS ids | B | F10's items - icons and pickup plumbing free |
| Small/big keys | B | dungeon-only in vanilla; the key-item logic may want them for gated content |
| Bottles + contents | A (m) | in tier table |
| Picolyte | C | timed-buff potion system - F4-adjacent, unbuilt |

## 5. Areas and rooms (beyond the ring)

| Area | Grade | Notes |
|---|---|---|
| The six dungeons (Deepwood, CoF, Fortress, Droplets, Palace, DHC) | D | whole unused worlds - the far-future "dungeon dive" event class; each brings its boss and its gimmick system |
| Dig caves (6 areas) | B | Mole Mitts rooms - F1's buried mode + Phase D dig rooms |
| Great Fairy rooms | A (m) | fairy kind |
| Minish Village / Minish paths | C | blocked on #103 |
| Cloud Tops | A (m) | the hub pit room; more of it is unused |
| Hyrule Town | X | the ring's deliberate hole; un-blocking it is a design decision, not a task |
| Castor Wilds / Royal Valley / Veil Falls / Crenel / Lake Hylia / Minish Woods | C | Phase E expansion stock - each needs the full region treatment (survey, fusers, checker) |

## 6. Systems and machinery

| System | Grade | Notes |
|---|---|---|
| Kinstone fusion + world events | A (m) | 18 fusers live |
| Ocarina warp | A (m) | return-to-hub |
| Ezlo hints / custom text | A (m) | gCustomStrings, 34 lines |
| HUD key-slot clock | A (m) | shared by hunt + scavenger |
| Pause-menu map screens | C | F10's spike target; gDungeonMap machinery below |
| Guard line-of-sight | C | F2's spike target |
| Weather/palette effects (rain, dark rooms, light rays) | C | mood modifiers for event rooms; lantern pairs with dark rooms |
| Cutscene orchestrator | D | powerful, expensive to drive |

## 7. EWRAM audit (closes the budget doc's open item)

From the linker map, blocks ≥1KB (89 layout symbols total; last symbol
`gEndOfEwram` at 0x02038560, EWRAM ends 0x0203FFFF):

    0x020000c0 gUnk_020000C0        3,072 B
    0x02000d00 gTextGfxBuffer       3,328 B
    0x02001a40 gBG3Buffer           4,096 B
    0x02002a40 gSave                1,216 B
    0x02002f00 gMapDataTopSpecial  16,384 B
    0x02006f00 gUnk_02006F00       16,384 B
    0x0200b650 gMapTop             49,156 B
    0x02017ba0 gUnk_02017BA0        4,864 B
    0x02018ee0 gUnk_02018EE0        4,096 B
    0x02019ee0 gMapDataBottomSpecial 4,096 B
    0x0201aee0 gDungeonMap         28,672 B   <- DEAD under QUICKSTART
    0x02021f30 gBG1Buffer           2,048 B
    0x02022830 gUnk_02022830        6,144 B
    0x020246b0 gUnk_020246B0        6,144 B
    0x02025eb0 gMapBottom          49,168 B
    0x02031ec0 gNPCData             4,096 B   <- mostly dead (vanilla NPC talk/figurine state)
    0x02033a90 gArea                2,152 B
    0x020344b0/4cb0 gBG2/BG0Buffer  2,048 B each
    0x02036570 gScriptExecutionContextArray 1,152 B
    0x02036bc0 gMPlayTracks         6,560 B

  Headlines:
  - **~31 KB of EWRAM is simply free** above gEndOfEwram (0x02038560 to
    0x0203FFFF) - the measurement mailbox already lives there.
  - **gDungeonMap is 28 KB of dead state** in a mode with no dungeons -
    AND it is exactly the buffer the pause-map draws from, which makes it
    the natural home for F10's overworld map rather than a reclamation
    target. Repurpose beats reclaim here.
  - gNPCData (4 KB) is mostly vanilla NPC bookkeeping for NPCs this mode
    sweeps; usable as scratch if anything ever needs per-run bulk state -
    but flags-in-gSave remains the discipline for anything that must
    persist.
  - RAM is NOT the scarce resource. The GFX slot table and the entity
    table remain the walls that matter (budget doc findings 1-5).

## Where to start when content is wanted

Cheapest real wins by grade-B density: the golden-enemy trio (a wired
fusion with no payoff today), the switch-puzzle object vocabulary
(Phase D's lever rooms), FLYING_POT ambushes in pot-heavy rooms,
CUCCO_AGGR as an F1c stake, and WIZZROBE_WIND to round out the wizzrobe
family. The boss ladder starts at OCTOROK_BOSS when F6 resumes.
