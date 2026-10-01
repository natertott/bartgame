# What the vanilla walkthrough tells us

Findings from reading Banjo2553's 100% walkthrough of *The Minish Cap* (the
user's upload, Oct 2026; 8,730 lines: the full route, a spoiler-free route,
44 heart pieces, 94 kinstone fusions, every item, 136 figurines, every enemy
and boss) against this mode's own tables and the ROM's data. Six questions
were asked of it:

1. Supplement the reachability survey. -> §1, applied and proposed.
2. Map Veil Falls, Hyrule Castle and every dungeon from the guide. -> §3,
   `tools/quickstart/guide_reach.py`.
3. Vanilla mechanics worth re-purposing. -> §4.
4. Anything else relevant. -> §5.
5. Can vanilla quests be ported, which, what would it look like, what does
   it cost, what breaks. -> §6, the long answer.

A rule this document keeps: **the guide is an upper bound on knowledge, not a
measurement.** It records what the vanilla route needed in vanilla's story
state. Every change it motivated to the shipped survey landed on a row the
survey itself had flagged as uncertain or derived, and every one was checked
against ROM data before it was made. Everything else it suggests is listed as
a proposal with the walk that would settle it.

---

## 1. The reachability survey

### 1.1 Applied (committed to `world_reach.py`, regenerated into `reach.h`)

| region / room | was | now | why the guide won |
|---|---|---|---|
| **MW: the Minish Village route** (path, village, Festari, wind crest, gold chest, bomb Minish house, Deepwood forecourt, three SW cave mouths) and **MV room requirement** | `MINISH + FLIPPERS` | `MINISH` | The survey carried the Flippers as its own doubt ("leaves ... not sure if gated by a story flag"). The guide rides the leaves to the village at the very start of the game with no items (Heart Piece #2 comes before dungeon one). The leaves are `LILYPAD_SMALL` objects authored unconditionally into `MINISH_PATHS/ToMinishVillage` and `lilypadSmall.c` tests only `PL_MINISH`. No flag exists. |
| **MW: Business Scrub tree** + its cave | `FREE` (flagged) | `FUSION` | Survey: "kinstone fusion maybe?", flood reached it. Guide: Fusion #13 opens it. `KINSTONE_27`'s world event fires at (528,456), this door, and the mode `MemClear`s kinstones at boot and pre-fuses only the three Castor statues - the tree starts closed every run. A live fuser for KINSTONE_27 stands in Minish Woods. **This was a FREE row on a gated door - the dangerous direction.** |
| **MW: Great Fairy tree** | `PACCI + FUSION` | `PACCI` | Survey "believes the tree itself is fusion-gated as well". Guide takes Big Wallet #2 with the cane alone, no fusion; `kinstone_audit.py` has no world event on that door. |
| **CG: both fountain rooms** | `MINISH` ("through the minish holes") | `FUSION` | Vanilla drains each fountain with a shared fusion (#78/#79). World events `KINSTONE_18`/`KINSTONE_35`, type 5 "remove water", sit at (776,72)/(232,72) - the two fountain doors - and both fusers are live in the mode's Castle Garden fuser table. The Minish holes were never the way in. |
| **CG: Grimblade's dojo** (two rooms) | missing | `SWORD` | Site 16, listed never-reachable by the simulation. Guide: "slash the bushes ... ladder leading down" in the SE corner; door (936,388), bush object (936,376). |
| **CG: castle cellar ladder** | missing | `SWORD` | The hedge-maze tunnel into the castle's lower hall. Vanilla also wants a guard sneak; the mode clears `GUARD_1` every frame. Recorded because it is the way *into* Hyrule Castle. |
| **RV: Great Dragonfly Fairy** | missing | `BOMBS` | Content site. Guide: "the lonely posts? Place a bomb between them" - right at the valley entrance, before the maze. |
| **CREN: Great Mayfly Fairy** | missing | `GRIP + BOMBS` | Content site. Guide: half-way up Crenel Wall, "the right-side ledge, and bomb the wall at its end". |

`reach.h` changed by 41 lines, all accounted for by these rows. The region
table's Minish Woods entry lost its Flippers alternative. `gen_reach.py
--check` and `world_reach.py --check` are clean (the 68 "coordinates to
re-take" are the pre-existing mid-transition stamps).

**What these buy.** Minish Village and the whole "via the village" half of
Minish Woods were priced at two key items; they now cost one that this mode
hands every run (the cap), and because the woods have open stumps, the model
prices them FREE. Fourteen rows, including the Deepwood Shrine forecourt and
the three south-west cave mouths. Site 16 becomes placeable. Two fairy
fountains gain honest prices.

**What they risk.** If the leaves do *not* carry a Minish player in this
build, a chain step placed in the village is a stranded run. Two independent
sources say they do (the vanilla route, the object's own code) and the user
rode them in the mapexplore build. It still wants one walk in the shipped d3
ROM: shrink at the MW stump, ride to the village with no Flippers.

### 1.2 Proposed, not applied (each needs a walk)

| where | survey says | guide says | the walk |
|---|---|---|---|
| LLR -> Lake Hylia east crossing (710,753) | `FLIPPERS / CAPE / MINISH+PACCI` | cane to the ledge, then whirlwinds straight across; the stump detour is a side-trip for a kinstone chest | Cane only, no shrinking: does the glide reach LH? If yes, add `[PACCI]`. |
| LH-CREST: Librari's house | `MINISH+FUSION+FLIPPERS` or `+CAPE` | "diving into the holes to let the spiked logs pass" - ducking, not swimming; no water named | Is there water on the Minish road to Librari? If not, drop the water term. |
| LH: Waveblade's tree | "suspects a kinstone fusion here, unconfirmed" | reached by swimming and stairs, no fusion; no world event on the door | Confirm and delete the suspicion from the note. |
| CW: south-west corner (Swiftblade I, gold cave) | `BOULDER1 / FLIPPERS+SWORD / MINISH+SWORD` | the vanilla land route passes two Eyegores that only the Bow destroys | Does the boulder route pass an Eyegore in this build? If so the term wants `BOW`. |
| RV: the forest maze | `LANTERN + MAZE`, both untestable | the maze is a FIXED path - up, left, left, up, right, up (south exits at once); the lantern only lets you read the signs that say so | Walk it dark. If it goes, `MAZE` is knowledge, not kit: retire the token (always true) and have Ezlo speak the sequence on entry. **This is the lever on "Royal Valley is dead content" (7% reachable, 0.2% of requirements).** |
| RV: the graveyard key | `GRAVEYARD_KEY`, untestable | Dampe gives it, a Takkuri steals it, you ram its tree with the Pegasus Boots | If the key route is ever made live it costs `BOOTS` in vanilla. |
| LLR: the Veil Falls pocket (168,55) | `NOT REACHABLE` | reached only by going up to Veil Falls and back down; fusion #85's chest (KINSTONE_60) sits there | Re-price at `PACCI` the day Veil Falls opens, as the row already says. |

### 1.3 A structural note the guide makes unavoidable

Eighteen of the survey's rows are priced at `FUSION`, and `QS_REACH_FUSION`
is "no run-time test" - the placer can never satisfy it, so every one of
those rooms is invisible to the chain even though **41 fusers are live** in
the ring and `gSave.kinstones.fusedKinstones` records exactly which gate is
open. The data to make the token testable per gate already exists (the fuser
table carries the kinstone id; the world-event table carries the door). That
would turn "do this fusion" into a placeable chain step, which is what the
survey's own header asked for when it chose to keep world facts and items in
one vocabulary. Not done here; recorded because the two fountain rooms and
the scrub tree just joined the list.

---

## 2. The Minish transform points, counted

`data/map/entity_headers.s` authors **44 transform points** game-wide
(`MINISH_PORTAL_MANAGER`, manager subtype 3; `tools/quickstart/minish_portals.py`
reads them). Six are hidden under a `TREE_HIDING_PORTAL` and need the
Pegasus Boots - Castle Garden (840,240), South Hyrule Field (88,544), North
Hyrule Field (808,528), Lon Lon Ranch's cow pen (312,368), Lake Hylia's
south-east (680,736), and nothing else. Every one matches a "tree that
sparkles when you get close" in the guide. The ring survey's `MINISH_PORTAL`
table agrees with the census on every region.

The dungeons: Cave of Flames 4 stumps, Fortress of Winds 8, Palace of Winds
2, Dark Hyrule Castle 2, Vaati's arena 2. Deepwood Shrine and the Temple of
Droplets have none because they are Minish-sized throughout - you shrink
*outside* (the Minish Woods giant stump; the Lake Hylia ice island) and stay
small. The Royal Crypt has none and needs none.

---

## 3. Veil Falls, Hyrule Castle, the Cloud Tops and the dungeons

All of it is in **`tools/quickstart/guide_reach.py`**: 11 areas, 231 rows in
`world_reach.py`'s own `region()`/`d()` vocabulary plus `KEYS(n)`, `BIG_KEY`,
`SHIELD`, `BOOMERANG` and `CLONES(n)`. `--check` validates every room name
against `include/roomid.h` (0 problems); `--adjacency AREA` prints which
rooms share an edge from `data/map/room_headers.s`, because dungeon rooms
connect by door tiles, not transition rows, and that is the only static view
of their neighbours; `--summary` prints the gate census below. **Nothing in
it feeds `reach.h`** - none of these is a ring region.

### 3.1 Veil Falls

One 480x1008 room, ten caves, a dig cave, a top screen. Two arrivals that the
guide treats as separate (it routes back through North Hyrule Field between
them), joined at most by water:

- **South strip** (from Lon Lon Ranch's Pacci ledge, LLR's own `PACCI`
  price): Heart Piece #10 free; the second border row down into the Lon Lon
  pocket the survey marks unreachable.
- **West ledge** (free from NHF's north-east border): Heart Piece #32 in the
  water (`FLIPPERS`); Splitblade's waterfall dojo (`FUSION #27 + FLIPPERS`);
  the lower dig spot (`FLIPPERS + MITTS`); and the gold-wall door
  (`KINSTONE_SOURCE_FLOW`, the piece Gustaf gives in the Crypt) into the
  caves, up to the middle ledge, a climb to the **wind-crest plateau**, a
  second climb to the top screen (Biggoron; the whirlwind to the Cloud Tops).
  The plateau is also an **Ocarina destination**, so the whole upper half
  reads `FUSION + GRIP` *or* `OCARINA` - the same shape as Lake Hylia's crest
  pocket. Both climbs are inferred Grip walls from the word "climb"; the act
  tiles were not checked.
- Caves: a bomb wall to a shell chest; a flooded rupee hall whose far door
  lands on the ledge for the **upper dig spot** (fusion #72, Heart Piece
  #43); a 100-rupee cave; a block puzzle (Bracelets here) to two secret
  rooms; the topmost waterfall (fusion #54, Heart Piece #40, swum to).

Vanilla also wires three Veil Falls prizes to fusions in *other* regions -
Grimblade (CG) opens the dojo, Gale and Hailey (Cloud Tops) open the top
waterfall and spawn a Golden Tektite, Caprice (tower) drops a chest - which
is the cross-region fusion pattern the kinstone economy was designed around.

### 3.2 Hyrule Castle, the Sanctuary, Dark Hyrule Castle

Five small rooms around one hall. The garden's main door, the castle's
entrance hall, a ladder down to the lower hall, two stairs up to the throne
room, the courtyard to the Elemental Sanctuary (hall, pedestal room, stained
glass), and the cellar tunnel in from the hedge maze. The side rooms (Link's
sick-bed, the maid's room, two more) have no transition rows and are
story-locked in vanilla. **The castle is free to walk** once the guards are
gone, and the mode already sweeps them.

Dark Hyrule Castle replaces it behind the same door after the Four Sword.
Thirty rows mapped; 21 of them are behind `CLONES(4)` - cannon halls
deflected by a line of four, four-switch rooms, the curse-breaking beam that
frees the king. See the census.

### 3.3 Cloud Tops

Three rooms on one footprint (top, middles, bottoms): drop through holes,
ride red whirlwinds up. Clouds are dug with the Mole Mitts; two Lakitus
block paths (Gust Jar or Bow); five gold pieces (three in dug-out chests,
two from killing Cloud Piranhas) fused into five Mysterious Clouds start the
windmills that summon the whirlwind to the **Wind Tribe tower - this mode's
hub.** The Palace of Winds is one whirlwind off the hub's own roof.

### 3.4 The dungeons, and the one fact that decides them

```
area                          rows   payable    clones   gated by clone puzzles
Deepwood Shrine                 21        21         0     0%
Cave of Flames                  20        20         0     0%
Fortress of Winds               30        21         9    30%
Temple of Droplets              34        15        19    55%
Royal Crypt                      7         3         4    57%
Dark Hyrule Castle              30         9        21    70%
Palace of Winds                 46         1        45    97%
```

Every dungeon from the third on is built on the **sword-level clone**: stand
on glowing tiles, charge, split into two, three or four Links to hold
switches, ride platforms, deflect cannonballs, move the big levers. This
mode has no element forging and no sword levels. The Power Bracelets stand
in for the *large-block pushes* only; nothing stands in for the switches.
So:

- **Deepwood Shrine** is fully payable: Minish (free in MW), a sword, four
  small keys, the Gust Jar (which this mode grants at spawn), the big key.
  Its boss is the mode's own win item.
- **Cave of Flames** is fully payable: bombs (or a lured Bob-omb), two keys,
  the Cane of Pacci half-way (a key item already in the pool), four stumps.
- **Fortress of Winds**: the Bow before anything, the Mole Mitts as the
  prize; two of four keys and the heart piece behind `CLONES(2)`. The boss
  needs the Bow, Mitts and shrinking.
- **Temple of Droplets**: Minish-sized; the **big key is the first thing
  found**; Flippers almost at once; both sunlight levers and four block
  puzzles are `CLONES(2)`; the Flame Lantern is the prize two-thirds in. The
  mode already fields its boss.
- **Royal Crypt**: a mini-dungeon; two of three keys are `CLONES(3)`; the
  torch room needs the lantern.
- **Palace of Winds**: Roc's Cape early then everywhere; `CLONES(3)` six
  times on the spine and on the boss; six small keys.
- **Dark Hyrule Castle**: the Four Sword's dungeon.

A dungeon room used as a ? room does not care about any of this - the mode
already uses `DEEPWOOD_SHRINE/ENTRANCE` and `CAVE_OF_FLAMES/ENTRANCE` as
sites. What the census governs is **dungeon-as-run-content**: only the first
two could be run end to end with this mode's items, and even they want a
small-key economy the mode does not have (keys are per-dungeon inventory in
vanilla and would need per-run reset).

---

## 4. Vanilla mechanics worth re-purposing

Ranked by how much already exists in the ROM and how little it costs in the
currency that binds (sprite sheets).

1. **Golden enemies** (`OCTOROK_GOLDEN`, `TEKTITE_GOLDEN`, `ROPE_GOLDEN`;
   ids 0x3c-0x3e). Vanilla spawns one per fusion as a bounty worth 100-200
   rupees, "many times stronger", in a named region. They are a ready-made
   **elite hunt target** and a ready-made **Elites-tier member**, with a
   vanilla reason to exist. Cost: one enemy sheet each, same as any enemy.
2. **Joy Butterflies** - three passive upgrades (dig faster, shoot faster,
   swim faster), each a butterfly to catch in a region. Three cheap `STAT`
   rows for the tier table with a vanilla pickup animation, and a "catch it"
   event that is zero new design.
3. **Takkuri theft.** A red crow that steals from you on contact - rupees in
   general, and in vanilla *the graveyard key*, which it then carries to a
   tree you must ram. That is a **curse event** and a **fetch-back quest** in
   one enemy (`TAKKURI`, 0x45).
4. **Kinstone fickleness and shared fusions.** `GetFusionToOffer` already
   rolls `fuserStability` against `Random() % 100` and refuses; shared
   fusions are a pool any of ~45 fusers can pay out once. Both are the
   "economy tightens with difficulty" knob and the "many fusers, few
   outcomes" shape the vision describes, and both are in the engine.
5. **Fusions that change *another* region.** Dampe's second fusion opens a
   hole in the Wind Ruins; Grimblade's opens Veil Falls; the five Mysterious
   Walls across five dig caves summon five Gorons to one Lon Lon tunnel.
   Cross-region cause and effect is the vanilla kinstone grammar; the mode's
   fusers today open the door beside them.
6. **The Great Fairies' honesty tests.** Three self-contained rooms, each a
   quiz whose "right" answer is honesty, each paying a capacity upgrade. All
   three are content sites already; two gained prices today.
7. **Stockwell's growing stock, Beedle's Picolyte, the inn's room prize,
   Borlov's double-or-nothing.** Four shop/gamble shapes with scripts and UI
   in the ROM: stock that expands with progress; bottle buffs that bias drop
   tables for a minute (hearts / rupees / kinstones / fairies / ammo - five
   of them map one-to-one onto charms); pay more for a better prize; bet and
   re-bet. The hub shop and inn exist; these are their vanilla vocabulary.
8. **Simon's Simulations** - "fight monsters without any danger ... if you
   dispatch a monster nicely enough, you may get a prize", 10 rupees a go, a
   chest at the end. It is the wave room with a ticket price.
9. **Wind crests + Ocarina.** Nine crests (Minish Woods, Castor Wilds, Lake
   Hylia, Mt Crenel, Veil Falls, Cloud Tops, Hyrule Town, two more revealed
   by gravestones). The mode already treats the Ocarina as an *entrance* for
   Lake Hylia's crest pocket; Veil Falls' plateau is the same shape.
10. **Dark rooms.** Veil Falls' caves, the Temple's maze, the Palace's
    compass hall, Grimblade's dojo, Percy's house: vanilla uses darkness as
    a *soft* gate - walkable blind, readable lit. A lantern-flavoured ? room
    kind costs nothing.
11. **Sparks -> fairies with the Boomerang; Gibdos -> Stalfos with the
    lantern; Lakitu clouds eaten by the Gust Jar; Peahats pulled down; Like
    Likes eating the shield; Wisps cursing the sword.** Item-vs-enemy
    interactions the roster already has ids for, and reasons to pick an
    item.

Explicitly **not** worth re-purposing: the Stranger's portal (fusion #29) - a
warp, which the user's door rule forbids; the Elemental Sanctuary's sword
forging - it is the clone mechanic's on-switch; Biggoron's Mirror Shield - a
six-entity NPC that is post-credits-only in vanilla.

---

## 5. Other things the guide settles

- **Hyrule Town is where most of vanilla's side content lives** - the cucco
  game, the library, the shoemaker, three shops, the inn, the school, the
  oracles, Simon, Borlov, the carpenters, two Minish roads, 115 scripts. The
  mode references `AREA_HYRULE_TOWN` once, in a comment. Any plan that leans
  on town quests leans on a region the mode does not have.
- **Vanilla's "kill every enemy to open the way" gates** sit exactly where
  the survey has dead pockets: the Wind Ruins' two armos events, the
  Fortress forecourt. The survey already names them as re-appropriation
  candidates; the guide confirms they are the only way in.
- **Heart-piece spots are pre-verified reward spots.** 44 of them, each a
  walkable tile the designers chose for a pickup, in rooms the mode uses.
- **Enemy ids the roster lacks that the guide places in the overworld:**
  Golden trio, Takkuri/Crow, Ghini (RV), Rock ChuChu (VF), Leevers (WR,
  VF), Cloud Piranha and Lakitu (sky), Wisp (VF caves), Bow Moblin.
- **Vanilla story flags the mode pre-pays at boot are the right call** in
  every case the guide describes: Festari's doorway, the Crenel beans, the
  Castor statues. The guide's route spends hours on exactly those chores.
- **Minish-only doorways** (`MINISH_SIZED_ENTRANCE`) and transform points
  are different objects, which the previous session established; the guide
  never once conflates them either - every "shrink" names a stump, rock or
  overturned pot.
- **The lost-woods sign trick** is the only maze in the game and its answer
  is six moves long.

---

## 6. Porting vanilla quests: the assessment

### 6.1 Is it possible?

**Yes, and the mode is already doing a version of it.** The quest system
shipped four kinds (the pot hunt, the enemy hunt, the scavenger hunt in
three hide modes, the stealth "watch") and every one is built the way a
ported vanilla quest would be: a giver NPC with a `data/scripts/quickstart/
script_QuickStart*.inc` that `Call`s C helpers, text in `gCustomStrings`
(176 strings, `TEXT_CUSTOM` and a second bank `TEXT_CUSTOM2`), state in
`FLAG_BANK_11`, reward through the mode's own draw. The research in
`docs/QUICKSTART_QUEST_RESEARCH.md` already proved the one scary
transplant - vanilla's guard line-of-sight projectile pair moved onto a plain
NPC and worked ("ANSWERED: YES, it transplants").

What vanilla gives us on top: **87 NPC source files**, **~420 scripts**
organised by area, **11 quest-item ids** (`ITEM_QST_*`), per-NPC text banks,
and quest state in global/local flags the engine already saves. A vanilla
quest is three things - an NPC entity with its C file, a script that drives
dialogue and checks, and flags/items that carry state - and all three are
data this mode can place. The reward is always a single `GivePlayerItem` /
`InitItemGetSequence` line in the script, which is where our draw goes
instead.

### 6.2 Which quests qualify

Verdicts are about **portability to a ring region**, not about fun.

**Port cleanly - self-contained, NPC + script + check, no town geometry**

| vanilla quest | mechanism | needs | notes |
|---|---|---|---|
| Smith's sword -> Minister Potho | carry `ITEM_QST_SWORD` from giver to receiver | two NPCs | The user's own example. Generalises to **the courier quest**: vanilla has seven of them (sword, broken sword to Melari, mushroom to Rem, dog food to Fifi, three books, graveyard key, ranch key). One framework, seven skins. |
| Gregal's ghost | Gust Jar sucks the ghost off a bedridden man; `gregal.c` spawns the ghost itself | one NPC, `GUST` | A reason to hold the Gust Jar. Vanilla's reward is 100 shells now and the Light Arrow later - a **deferred second reward** shape worth keeping. |
| Percy and the Monster Lady | light two torches in a dark house with the lantern; the "old woman" is a Moblin | one NPC (`MOBLIN_LADY`, 18 lines of C, two scripts), `LANTERN` | A reason to hold the lantern; a house interior is a one-door ? room. |
| The Great Fairies (x3) | answer honestly, get an upgrade | rooms already sites | Effectively ported: swap the reward line. |
| Business Scrubs | deflect the nut, then shop | rooms already sites | Same. |
| Golden enemy bounties | a fusion spawns one elite in a region; kill it | one enemy sheet | Is the shipped **hunt quest** with a vanilla target. |
| Joy Butterfly | catch a butterfly in a region | one small sprite | Zero design; pays a `STAT`. |
| Melari reforges the sword | deliver, go away, come back later | one NPC | Courier + **delayed pickup**, a shape the chain's "one step at a time" structure handles naturally. |
| Picolyte research | bring the Minish a bottled item | one Minish NPC (MV room exists) | Courier with a bottle; unlocks shop stock. |
| Jabber Nut fetch | push a crate, take the nut, return | MV rooms exist | Courier inside Minish Village. |
| Mysterious Walls -> Goron tunnel | fuse at five walls in five dig caves; a cave opens | wall fusers are objects, ~0 sheets | A **multi-fusion meta-quest**; the Goron cave is five content sites already. |

**Port with surgery - mechanism is fine, geometry or partner is town-bound**

| vanilla quest | what binds it | the surgery |
|---|---|---|
| Anju's cuccos | `cuccoMinigame.c` hard-codes the cage at origin+(0x360,0x350) and teleports the player to (0x340,0x378); prize tiers are global flags | parameterise the cage, pick an enclosure per region, reset the tier flags per run. Cuccos cost a sheet; chicks another. |
| Stockwell's dog food | the bottle is in town rafters; the bowl is in his Lake Hylia house (a site) | keep the delivery half only: giver hands the bottle, Fifi's bowl receives. **Blocked** - see 6.5. |
| Lon Lon Ranch key | find the key in the ranch house as Minish, hand it to Talon | already partly live (task #10 removed the boot-granted key); Talon is swept as a resident. |
| Hagen's library book | the lakeside cabin leg (hidden stump, lilypad + Gust Jar, push the cabinet) is in LH; the return is to the town library | replace the receiver with our NPC. |
| Dampe's key and the Takkuri | key, theft, tree, gate - all in RV; needs Boots | the gate object and the Takkuri are RV-specific; works only there. |
| Wake-Up Mushroom | Syrup's hut (MW, unsurveyed) to Rem (town) | replace Rem with our NPC; `rem.c` is 495 lines you do not need. |

**Do not port - or not as a quest**

| vanilla quest | why not |
|---|---|
| Library books 1 and 2, Simon's, Borlov's, the oracles' housing, the carpenters' house, the Stranger's portal, the school, the inn | Hyrule Town geometry end to end, or a warp (the portal), or a shop shape rather than a quest. |
| Biggoron's shield | six NPC entities on one screen, post-credits only, Veil Falls only, and it takes the player's shield. |
| The Zelda escort | `zeldaFollower.c` exists (211 lines), but the research already ranked escort as the highest-risk shape; the follower AI assumes the festival route. |
| Librari's trial, the Sanctuary infusion, the Ocarina tablet | story set pieces with cutscene orchestrators. |
| Tingle brothers -> Magical Boomerang | already in the survey as the four-switch pocket; it is a world mechanic, not a quest. |

### 6.3 What incorporating it looks like

The shipped quest framework already has the shape; a ported quest is a fifth
sibling, not a new system.

1. **A quest table row**: `{ kind, giverNpcId, giverFace, receiverNpcId,
   questItem, needsItemMask, rewardCategory, hostRegionRule }`. Kinds:
   COURIER, CLEANSE (Gregal), ILLUMINATE (Percy), CATCH (butterfly),
   BOUNTY (golden enemy - the hunt with a fixed target).
2. **Two cloned scripts** per kind under `data/scripts/quickstart/` - the
   vanilla script with its text indexes swapped to `TEXT_CUSTOM`/`CUSTOM2`
   and its `GivePlayerItem` replaced by `Call QuickStartQuestComplete`,
   exactly as `script_QuickStartHunt.inc` does today. Vanilla's own lines
   are reusable where they are story-neutral (Gregal's thanks, the Moblin's
   "don't tell anybody"), which saves custom strings.
3. **The NPC entity**: `CreateNPC(id, form, 0)` on a surveyed spot, with
   `QuickStartIsOurNpc` taught to recognise it (today "ours" means `ZELDA`
   or the room's fuser face; a quest NPC with its own face is deleted by the
   per-frame sweep the next frame).
4. **State**: `FLAG_BANK_11`, ~6 bits per live quest (rolled, host, stage,
   done) - the research measured 150+ free. Quest *items* use the
   `ITEM_QST_*` inventory values vanilla already has (`GetInventoryValue`
   0/1/2 encodes "not yet / carrying / delivered" in `dampe.c` and `dog.c`),
   cleared per run alongside the other QUICKSTART save fields.
5. **Roll**: one or two vanilla quests per run, drawn at run start into
   regions whose `QuickStartReachRoomOk` passes for both ends, with the
   receiver placed one region away so the courier is a *walk*. The chain's
   `QUEST` kind already points at "the run's side quest"; it becomes "one of
   the run's side quests".
6. **Reward**: `QuickStartDrawItem` at the receiver's feet, the F1c stake on
   failure where a clock applies, same as the siblings.

### 6.4 What it costs

Measured numbers from the project's own research, not estimates:

- **GFX sheets are the binding currency.** 44 slots; each live enemy holds
  one; a drawing NPC face costs **1 sheet, or 2 if its C file calls
  `LoadExtraSpriteData`**. Of the candidate quest NPCs: **Potho, Gregal,
  Moblin Lady, Dampe, Stockwell, Rem, Malon, Goron, Gina, Librari, Dr Left,
  Hagen, Gustaf, Festari, Gentari, Anju and the Cucco load one sheet; Smith,
  Percy, Talon, Melari, Syrup and the Hurdy-Gurdy Man load two.** A
  two-NPC courier with single-sheet faces is 2 sheets; the measured cost of
  one quest in the tightest wave region was 3 slots of margin (NHF, 6 -> 3)
  and Lon Lon Ranch tops out at **4 reclaimable slots**, so one ported quest
  per region at a time is the ceiling, and Lon Lon cannot host a two-face
  one at all. **Every candidate face must be rendered before use** - four of
  the eight original fuser faces drew garbage and nothing in the tables
  predicted which (`fuser_faces.py` is the probe; it currently forces only
  the fuser cast and wants a one-line extension).
- **Entities**: 2-4 per quest (giver, receiver, item, ghost). South Hyrule
  Field sits at 70 of 72 by difficulty 4, so a quest hosted there at
  difficulty 3 is already on the edge; the enemy ceiling now prices against
  the GFX table and would need to price against the entity count too.
- **Flags**: ~6 bits per quest in bank 11; comfortable.
- **Text**: `gCustomStrings` is at 176 entries with index 240 the highest in
  bank one; bank two exists. A courier skin is ~4 lines. Comfortable.
- **Code**: the four siblings cost ~120 lines of C each plus a script; a
  courier framework is the same order, then each skin is a table row and a
  text block. The expensive one is the cucco game (coordinate surgery in
  `cuccoMinigame.c`).
- **Build**: no new `.data/.bss` in `game.o` is allowed, which is why the
  watchmen "turn rather than walk" - any quest NPC movement has to be a pure
  function of frame and position, or stationary. Couriers stand still.

### 6.5 Concerns and incompatibilities

- **The quest-item ids are already spent.** The mode repurposed
  `ITEM_QST_DOGFOOD` and `ITEM_QST_MUSHROOM` as curses and `ITEM_QST_BOOK1-3`,
  `TINGLE_TROPHY`, `CARLOV_MEDAL` and `BROKEN_SWORD` as charms. A courier
  that hands the player "a bottle of dog food" would hand them the
  enemies-faster curse. Only `ITEM_QST_SWORD`, `LONLON_KEY` and
  `GRAVEYARD_KEY` are still quest items, and the last two are `QS_CAT_KEY`
  draws. **The courier needs its own carried-item representation** (a bank
  11 "carrying" bit and a sprite), or the charm ids move.
- **Vanilla scripts test story flags the mode pre-sets at boot.** `percy.c`
  branches on `URO_POEMN_TALK`, `dampe.c` on `DANPEI_TALK1ST`; a cloned
  script inherits those branches. Each port needs its flag reads audited and
  its flags cleared per run - vanilla flag banks persist across the mode's
  runs unless reset.
- **The sweep.** `QuickStartClearEasternHillsNpcs`-style sweeps delete any
  NPC that is not `ZELDA` or the room's fuser face, every frame. Vanilla
  residents who are also quest actors (Talon, Malon, Smith in his own house)
  are deleted on sight today; `QuickStartIsOurNpc` is a one-function fix,
  but note the recorded trap: the fuser cast dropped Talon and Malon
  *because* sparing the face would spare the vanilla residents too.
- **Fusion-outcome collisions.** Vanilla quests that fire through
  `fusedKinstones` (Eenie -> the Goron, the oracles -> butterflies) share the
  bit array the mode clears at boot and uses for its own gates. A ported
  fusion quest must claim ids the mode's 41 live fusers do not.
- **Hyrule Town.** Thirteen of the ~26 vanilla quests touch it; bringing the
  town in is a region project (one 1008x960 room with ~115 scripts and ~40
  NPC faces, which is the GFX wall in one screen), not a quest project.
- **The vanilla door rule** excludes the Stranger's portal and anything
  that teleports; Wallmasters/Floormasters that "send you back to the
  start" are vanilla hazards and fine.
- **Minigame objects hard-code rooms** (`cuccoMinigame.c`'s cage). Any
  object with `gRoomControls.origin_x + literal` in it needs a table.
- **Reward dialogue is vanilla's**. Story-neutral lines reuse; everything
  else is custom text, and the mode's rule is that every line the player
  reads must be ours or verbatim-correct (the "Now, when you're..." fragment
  was a real bug).
- **Doctrine 8 applies with force.** Anju's script `Call`s
  `CuccoMinigame_Init` through the script system's condition register; a
  port that "works" in a probe with no control is not evidence. The hunt,
  scav and watch each shipped with an end-to-end emulator check and a
  failing control; so should each port.

### 6.6 Recommendation

Three ports, in this order, each a week's work at the pace the siblings set:

1. **The courier** - Smith's sword to the Minister as the first skin, with
   its own carried-item bit. It generalises to seven vanilla quests, it
   exercises the two-NPC / two-region shape the chain has never placed, and
   both faces (Smith 2 sheets, Potho 1) are measurable first. If Smith's
   second sheet is a problem, the Postman or Anju - already-verified
   single-sheet faces in the fuser cast - can be the giver.
2. **Gregal's ghost** - one NPC, one item (the Gust Jar the run already
   holds), vanilla's own ghost entity does the work, vanilla's thanks line
   is reusable, and the deferred second reward is a chain-friendly shape.
3. **Percy's Monster Lady** - the lantern's first reason to exist in the
   pool, an 18-line NPC, a house interior.

And one non-port that the guide makes urgent: **retire `MAZE` as a token
and speak the six-move path**, because it is the cheapest change in this
document and it is the one that brings Royal Valley back.
