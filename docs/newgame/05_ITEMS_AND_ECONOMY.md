# 05. Items and economy

The item list is vanilla. The tiers, categories, charms and the kinstone
economy are QUICKSTART's. They carry over as design.

Sources: `include/item.h`, `src/itemMetaData.c`, `src/item/`,
`src/game.c` (`sQuickStartTiers` around line 6620, the charm and food
masks around line 4505), `include/kinstone.h`,
`docs/QUICKSTART_ITEM_TIERS.md`, `docs/QUICKSTART_SHOP_PRICE_TAGS.md`.

## The vanilla item ids (`include/item.h`)

Equipment: Smith's, Green, Red, Blue and Four Swords; Bombs and Remote
Bombs; Bow and Light Arrow; Boomerang and Magic Boomerang; Shield and
Mirror Shield; Lantern; Gust Jar; Cane of Pacci; Mole Mitts; Roc's Cape;
Pegasus Boots; Fire Rod; Ocarina; four Bottles and their contents (butter,
milk, potions, water, fairy, picolyte).

Passive: Grip Ring, Power Bracelets, Flippers, Map, Compass, Big Key.

Skills, granted as items: Spin, Roll, Dash, Rock Breaker, Sword Beam,
Great Spin, Down Thrust, Peril Beam, plus the Fast Spin, Fast Split and
Long Spin upgrades.

Quest items: dog food, the Lon Lon key, mushroom, three books, the
graveyard key, Tingle trophy, Carlov medal. Elements: Earth, Fire, Water,
Wind. Shells, rupees, hearts, kinstones.

Inventory in the save is 2 bits per item (`gSave` +0xF2): 0 none, 1 have,
2 have and seen. `GetInventoryValue` and `SetInventoryValue` read and
write it.

## Item roles in a gated world

The new game is a lock-and-key puzzle, so classify every item by what it
**opens**. This is QUICKSTART's KEY category, and the reach tokens in
`07_PROCGEN_DESIGN.md` use the same names.

| item | opens | world feature |
|---|---|---|
| Sword | bushes, grass, switches | act 0x00 cut |
| Bombs | bombable walls and rocks | act 0x2e, act 0x03 |
| Bow | far switches, eye switches | act 0x04 |
| Boomerang | far switches. **The only answer to Spark** | act 0x02 |
| Lantern | dark rooms, torches, webs | act 0x07, tile type 117 |
| Gust Jar | dust, webs, some platforms | act 0x05, 0x16, 0x3e |
| Cane of Pacci | spring holes, flipping. **The only answer to Lakitu** | act 0x0a, special tile 0x4020 |
| Mole Mitts | soft earth, dig-through wall faces | act 0x0d (soft earth), 0x56 (wall face) |
| Roc's Cape | pits and gaps, swamp | act 0x0d, 0x13 |
| Pegasus Boots | swamp, dash walls | act 0x13 |
| Grip Ring | climb walls | act 0x50 |
| Power Bracelets | heavy blocks, all sizes in QUICKSTART | act 0x72 |
| Flippers | deep water | act 0x10 |
| Fire Rod | ice blocks, torches | |
| Ocarina | warp home | |
| Rock Breaker skill | rocks | act 0x01 |

## QUICKSTART's tier table (`sQuickStartTiers`)

The one source of every random item. Each row is
`{item, category mask, tier, requirement, repeatable}`. A draw rolls a
tier **60/30/10** (common, uncommon, rare), then picks uniformly among the
usable rows. A requirement filters rows: the Blue Sword wants the Red,
the Large Quiver wants the Bow, potions want an empty bottle.
`repeatable` rows (rupees, hearts, refills) may drop again when owned.

Category bitmask: `KEY`, `REWARD`, `WEAPON`, `SKILL`, `STAT`, `CHARM`.
`QS_CAT_DROP` is everything but KEY. `QS_CAT_ALL` includes KEY.

| tier | rewards | weapons and tools | skills |
|---|---|---|---|
| common | 50 rupees, heart piece, blue potion, bottle | Bow, Bombs, Boomerang, Bomb Bag, Large Quiver | Spin, Rock Breaker, Roll |
| uncommon | 100 rupees, red potion | Remote Bombs, Gust Jar, Fire Rod, Red Sword, a bottle | Dash, Peril Beam, Sword Beam |
| rare | 200 rupees, heart container, fairy | Blue Sword, Magic Boomerang, Mirror Shield, Light Arrow | Down Thrust, Great Spin, Fast Spin, Fast Split, Long Spin |

STAT rows are the butterflies (arrow, dig and swim upgrades).

KEY items are the movement and access verbs: Mole Mitts, Cane of Pacci,
Lantern, Pegasus Boots, Roc's Cape, Grip Ring, Power Bracelets,
Flippers, Bombs. **In QUICKSTART, only the region clear reward can pay a
KEY item**, and that is how a run's reachable world grows. The `ITEM`
chain step meant to do it never fired in 500,000 simulated rolls. The
lesson for procgen is below.

## Charms and curses

Fourteen run-long effects, half of them traps, carried as repurposed
vanilla food and orb items (`QUICKSTART_FOOD_*`):

| good | bad |
|---|---|
| sword knockback, walk speed, steadfast (no knockback taken) | curse: knockback taken |
| immune to fire, to ice, to shock | curse: enemy speed |
| drops more rupees, kinstones or hearts | curse: fire rate |
| cheap shop, rare luck | curse: rot (slow poison, Green Orb) |
| sword edge (+1 damage) | curse: blur (mosaic, Blue Orb) |
| beam from any health | curse: dim (dark screen, Red Orb) |
| fleet | curse: blunt (-1 damage) |

Plus the three vanilla bottle charms: Nayru (damage taken / 4), Farore
(taken / 2 and dealt x 1.5), Din (dealt x 2). **Trap: the three orbs have no
ground sprite**, so a dropped orb lies on the floor undrawn.

## Kinstones and fusion (`include/kinstone.h`)

Vanilla: kinstone halves drop from enemies, grass and chests. Fusing a
matching half with an NPC (L button, `PLAYER_08070E9C`, the fusion
subtask) triggers a world event: a chest appears, a bridge forms, a door
opens. `FuseInfo gFuseInfo` tracks the fusion state machine
(`FUSION_STATE_0-6`).

QUICKSTART: kinstones are the key economy. Enemies drop pieces.
**Fusers** (NPCs wearing borrowed faces) travel between regions and stand
at gated doors. A fusion opens a new ? room for the rest of the run. Some
doors are always open so content stays reachable without fusions. The
design note "the kinstone economy tightens as difficulty rises" was never
tuned.

Fusion is a good procgen lever: a **soft gate** that costs grind, not a
specific item. A generator can place one where a hard gate would make the
graph too linear.

## The shop, hearts and rupees

The hub shop (`docs/QUICKSTART_SHOP_PRICE_TAGS.md`) sells a key-item slot
plus tier draws, at prices the cheap-shop charm cuts. `ITEM_FOR_SALE`
objects carry the stock. Rupees come from drops, chests and lotteries.
Heart pieces combine four to a container.

## The hub's selection rounds

At run start: three rounds of three choices each, drawn from the tier
table. Round one is a key item, round two a rare reward or a stat, round
three a skill. This is the run's opening loadout, and it decides which
part of the world is open first. The new game's generator must read the
chosen loadout before it places the first gates, or it must place gates
that every possible opening can pass.
