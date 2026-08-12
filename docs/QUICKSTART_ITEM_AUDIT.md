# Item audit: what is actually in the game

Read off the code, not the design doc. Where this contradicts
`QUICKSTART_ITEM_TIERS.md`, this file is right and that one describes an
agreement that was never built.

Commit audited: `935b8b7`.

---

## 0. The headline

**A tier system now exists.** Sections 1-3 below describe the state this audit
originally found and are kept as the "before" record; section 6 describes what
replaced it. Where they disagree, section 6 is current.

## 1. What is obtainable, and how

38 distinct items. Grouped into your categories:

### KEY ITEMS

| item | sources |
|---|---|
| Pegasus Boots | round-1 choice, region reward |
| Roc's Cape | round-1 choice, region reward |
| Mole Mitts | round-1 choice, region reward |
| Zora's Flippers | round-1 choice **only** |
| Lantern | round-1 choice, region reward |
| Cane of Pacci | region reward **only** |
| Ocarina of Wind | region reward **only** |

Round 1 offers 3 of the 5 flipper/boots/cape/mitts/lantern rows, so two key
items are missed every run and can only come back as a region reward.
**Grip Ring and Power Bracelets are not obtainable at all.**

### REWARDS

| item | sources |
|---|---|
| Heart Piece | ? chest, wave, hunt, lottery, **every miniboss**, shop, region reward, Melari's Mine, pot quest |
| Heart Container | round-2 choice, rare site, **elite miniboss**, region reward |
| 200 Rupees | ? chest, wave, hunt, lottery, rare site |
| 100 Rupees | round-2 choice **only** |
| Red Potion (bottled) | round-2 choice **only** |
| Fairy (bottled) | shop **only** |
| Two loose fairies | the FAIRY ? room kind (heals; not an inventory item) |

**Empty bottle and blue potion are not obtainable.** A run can hold at most
two bottles, and only by taking the round-2 potion and buying the shop fairy.

### WEAPONS / TOOLS

| item | sources |
|---|---|
| Bow | ? chest, wave, hunt, lottery, shop, region reward |
| Bombs | ? chest, wave, hunt, lottery, shop, region reward |
| Boomerang | ? chest, wave, hunt, region reward |
| Gust Jar | ? chest, wave, hunt, region reward |
| Bomb Bag | ? chest, wave, hunt, shop |
| Large Quiver | ? chest, wave, hunt, shop |
| Magical Boomerang | rare site, region reward |
| Mirror Shield | rare site, region reward |
| Remote Bombs | region reward **only** |
| Red Sword (level 2) | miniboss, ~1 in 4 non-elite, **once per run** |
| Smith's Sword, Shield | boot grants |

**The Fire Rod is not obtainable** — it was agreed as an uncommon
WEAPON/TOOL last session and never added to a pool.

### SKILL UPGRADES

| item | sources |
|---|---|
| Spin Attack | round-3 choice, shop, region reward |
| Roll Attack | round-3 choice, region reward |
| Peril Beam | round-3 choice, region reward |
| Rock Breaker, Sword Beam, Dash Attack, Great Spin, Down Thrust | region reward **only** |

Five of the eight skills have exactly one source in the whole game.

### STAT UPGRADES

**None are obtainable.** Not one.

- Din's / Farore's / Nayru's Charm: `BOTTLE_CHARM_*` appear only in the
  *consumption* path (`QuickStartNoteCharm`, `CalculateDamage`). Nothing
  anywhere grants one, and the run-long stacking charm framework built last
  session is unreachable dead code today.
- Joy Butterflies (`ITEM_ARROW_BUTTERFLY`, `ITEM_DIG_BUTTERFLY`,
  `ITEM_SWIM_BUTTERFLY`): in no pool.

---

## 2. Sources, and what each one can give

| source | draws from | notes |
|---|---|---|
| Boot grant | fixed | Smith's Sword, Shield, Wallet, Kinstone Bag, Lon Lon key |
| Round 1 (key item) | `sQuickStartKeyItems` (5) | 3 offered, 1 taken |
| Round 2 (bonus) | `sQuickStartBonusItems` (3) | 3 offered, 1 taken |
| Round 3 (skill) | `sQuickStartSkillItems` (3) | 3 offered, 1 taken |
| Shop | `sQuickStartShopCatalog` (9) | all 9 always stocked; prices re-rolled per run |
| ? chest | ladder pool (8) | uniform |
| ? wave gauntlet | ladder pool (8) | uniform, paid after wave 3 |
| ? pot / chest lottery | ladder pool, **first 4 only** | see the defect in §4 |
| ? miniboss | fixed | Heart Piece; Heart Container if elite; Red Sword on a 1-in-4 side roll |
| ? fairy room | — | two loose fairies, no item |
| ? rare site | rare pool (4) | the Boomerang chamber staircase, 1 site |
| Region clear reward | garden pool (23) | filtered to items not already owned |
| Hunt quest | ladder pool (8), or rare pool if handicap | one per run |
| Pot quest | fixed | Heart Piece |
| Melari's Mine | fixed | Heart Piece |
| Win | fixed | Earth Element |
| **Enemy drops** | droptables | **rupees, hearts, kinstone pieces, bomb/arrow refills only — never equipment** |

Kinstone fusions open doors and reveal staircases; they do not pay items.

---

## 3. The real distribution

30 content sites per save. Each is classed by room size and rolls a kind once
per run. Three kinds are meta-progression locked (pot lottery at 500 meta_xp,
chest lottery at 1500, fairy at 1 win), and a locked roll **falls back to
CHEST** — which is why a fresh save is so chest-heavy.

Site classes: 20 SMALL, 6 ANY, 2 LARGE, 1 ELITE, 1 RARE.

### Fresh save (0 wins, 0 meta_xp)

| kind | sites/run | % of sites |
|---|---|---|
| CHEST | 18.4 | 61.4% |
| NPC | 5.9 | 19.5% |
| MINIBOSS | 2.5 | 8.4% |
| WAVES | 2.2 | 7.3% |
| RARE chest | 1.0 | 3.3% |

Expected item drops per run from ? sites:

| item | expected count |
|---|---|
| Heart Piece | 5.10 |
| 200 Rupees | 2.83 |
| Bow / Bombs / Boomerang / Gust Jar / Bomb Bag / Large Quiver | 2.58 **each** |
| Magical Boomerang / Mirror Shield / Heart Container | 0.25 each |

### Fully unlocked (2+ wins, 1500+ meta_xp)

| kind | sites/run | % of sites |
|---|---|---|
| CHEST | 5.9 | 19.5% |
| NPC | 5.9 | 19.5% |
| POT_LOTTERY | 5.9 | 19.5% |
| CHEST_LOTTERY | 5.9 | 19.5% |
| MINIBOSS | 2.5 | 8.4% |
| WAVES | 1.5 | 5.1% |
| FAIRY | 1.5 | 5.1% |
| RARE chest | 1.0 | 3.3% |

| item | expected count |
|---|---|
| Heart Piece | 6.38 |
| 200 Rupees | 4.10 |
| Bow / Bombs | 3.85 each |
| Boomerang / Gust Jar / Bomb Bag / Large Quiver | 0.92 each |
| Magical Boomerang / Mirror Shield / Heart Container | 0.25 each |

**Read that carefully.** Every item in a pool is equally likely, so "rarity"
today is entirely an artefact of *which pool an item is in and how big that
pool is* — a Mirror Shield is rare because only one site draws from the
4-entry rare pool, not because anything marked it rare. And unlocking the
lotteries makes the Boomerang, Gust Jar, Bomb Bag and Quiver **2.8× rarer**,
because lotteries can only reach the first four pool entries.

---

## 4. Defect found during this audit - FIXED

`QuickStartPickLotteryExtra` and `QuickStartPickPotRoomExtra` packed the prize
index as `prizeIndex << 2`, and every reader unpacked it as `(extra >> 2) & 3`
— a **2-bit** field. That was correct while the pool had 4 entries. Growing it
to 8 in `935b8b7` made the writer emit 3 bits into a 2-bit slot:

- **Chest lottery:** prize indices 4-7 folded onto 0-3, so lotteries could
  never award the Boomerang, Gust Jar, Bomb Bag or Large Quiver.
- **Pot lottery:** the spilled bit landed in the winner field (bits 4-7), so
  the prize roll perturbed *which pot* held the prize. Self-consistent, so
  invisible in play, but the two fields were no longer independent.

**Fixed by widening the prize field to 3 bits and re-packing.** The chest
lottery had bits 5-7 free and simply uses them. The pot lottery was fully
packed, so its winner field gave up one bit — 16 buckets down to 8. That field
is not a slot index but a position along the far half of the fill order, and
that half is only ~10-22 pots deep, so four bits were finer than the thing
being addressed; eight buckets still land the prize somewhere different nearly
every time.

New layout, with the mask derived from the pool size so the two cannot drift
apart again:

| field | chest lottery | pot lottery |
|---|---|---|
| bits 0-1 | winning chest (0-2) | density preset (0-2) |
| bits 2-4 | prize index (0-7) | prize index (0-7) |
| bits 5-7 | unused | winner bucket (0-7) |

Verified by exhaustively round-tripping all 216 pot-lottery and 24
chest-lottery combinations, and by checking the derived winner index stays in
range for pot counts of 10/20/30/44. The invariant checker now asserts the
prize field is derived from the pool size, does not overlap the winner field,
and fits in the 8 stored bits.

**The §3 tables were measured before this fix.** The kind distribution is
unchanged; the item expectations under "fully unlocked" are now:

| item | before fix | after fix |
|---|---|---|
| Heart Piece | 6.38 | 4.91 |
| 200 Rupees | 4.10 | 2.64 |
| Bow / Bombs | 3.85 each | 2.39 each |
| Boomerang / Gust Jar / Bomb Bag / Large Quiver | 0.92 each | 2.39 each |
| Magical Boomerang / Mirror Shield / Heart Container | 0.25 each | 0.25 each |

The fresh-save numbers are untouched — no lottery can roll on a fresh save,
so nothing there ever read the truncated field. The distortion the audit
called out is gone: every ladder-pool item is now equally likely, and
unlocking the lotteries no longer makes four of the eight rarer.

---

## 5. Gaps against the agreed design, ranked

1. **No tier system at all.** Everything below follows from this.
2. **No stat upgrades exist.** Charms and butterflies are both unreachable;
   the charm code is live but nothing can trigger it.
3. **The Fire Rod is unobtainable** despite being agreed as an uncommon drop.
4. **Bottles are nearly unobtainable** — max two per run, no empty bottle, no
   blue potion. This is also what blocks charms, since a charm is a bottle
   fill.
5. **Grip Ring and Power Bracelets** are agreed key items with no source.
6. **Bow of Light and the Green/Blue/Four Sword** have no source; the only
   sword upgrade is the Red Sword, once, at 1-in-4 off a miniboss.
7. **Five of eight skills have exactly one source** (region reward), so a
   short chain simply cannot see them.
8. **Enemies never drop equipment** — only rupees, hearts and kinstones.
9. **A fresh save is 61% chests**, because three of the seven kinds are
   meta-locked and every locked roll degrades to CHEST.

---

## 6. What changed after the audit

The audit's findings were implemented. `sQuickStartTiers` is now the single
source of every drop, replacing the three flat pools.

### The curve

**60 / 30 / 10** common / uncommon / rare, expressed as buckets out of ten
(`QS_TIER_BUCKETS`). Buckets rather than percentages because the stored draw
seed is only six bits: the first attempt used `seed % 100 < 60`, which made
rare literally unreachable, since a seed of 0-63 never lands in the 90-99
band. Quantised against 64 seeds the realised split is **62.5 / 28.1 / 9.4**.
The checker asserts every tier stays reachable.

### The table

| category | common | uncommon | rare |
|---|---|---|---|
| REWARDS | 50 rupees, heart piece, blue potion, empty bottle | 100 rupees, red potion | 200 rupees, heart container, bottled fairy |
| WEAPONS / TOOLS | Bow, Bombs, Boomerang | bomb bag, large quiver, remote bombs, bottle, Gust Jar, **Fire Rod** | Magical Boomerang, Mirror Shield |
| SKILL UPGRADES | spin attack, rock breaker, roll attack | dash attack, peril beam, sword beam | down thrust, great spin |
| STAT UPGRADES | *(none, by design)* | **arrow / dig / swim butterfly** | **Nayru's / Farore's / Din's Charm** |
| KEY ITEMS | *(none)* | boots, cape, mitts, flippers, lantern, ocarina | Cane of Pacci, grip ring, power bracelets |

A "? room" draws `QS_CAT_DROP` — everything except KEY. A region clear reward
draws `QS_CAT_ALL`, because that is where the Cane, the Ocarina and the key
items the opening selection did not offer have always come from.

The hub's three selection rounds draw from this table too, superseding §2's
`sQuickStartKeyItems` / `sQuickStartBonusItems` / `sQuickStartSkillItems` rows
— those arrays are gone. Each round takes a slice, and unlike a "? room" it
picks a *band* rather than rolling the 60/30/10 curve:

| round | categories | tiers | pool on a fresh run |
|---|---|---|---|
| 1 | KEY | any | 8 (all 9, less the boot-granted Ocarina) |
| 2 | REWARDS + STAT UPGRADES | rare only | 6 |
| 3 | SKILL UPGRADES | rare excluded | 6 |

Round 1's array had held 5 of the 9 KEY entries, so the Cane, the grip ring
and the power bracelets could not open a run; rounds 2 and 3 were fixed
triples with no randomness at all.

### Prerequisites

Checked at draw time, not roll time, so a prize decided on the first visit
still resolves correctly on a later one:

| requirement | applies to |
|---|---|
| owns Bow | large quiver, arrow butterfly |
| owns Bombs | bomb bag, remote bombs |
| owns Boomerang | Magical Boomerang |
| owns Mole Mitts / Flippers | dig / swim butterfly |
| owns Spin Attack / Roc's Cape | Great Spin / Down Thrust |
| has an **empty bottle** | all potions, bottled fairy, all three charms |
| has a **free bottle slot** | a new empty bottle |
| does **not** own the Cane of Pacci | Fire Rod |
| does **not** own the Fire Rod | Cane of Pacci |

Non-repeatable entries also drop out once owned. Rupees, hearts, bottle fills
and the two capacity upgrades are repeatable.

### The four gaps, closed

1. **Tiers** — implemented, as above.
2. **Stat upgrades** — butterflies need only the item they upgrade (their
   effect is read straight off the inventory bit by `itemBow.c`,
   `itemMoleMitts.c` and `playerUtils.c`, so no new code). Charms arrive
   bottled and become permanent when drunk, which finally makes the run-long
   stacking charm framework reachable instead of dead code.
3. **Fire Rod** — uncommon WEAPON/TOOL, mutually exclusive with the Cane of
   Pacci because `itemMetaData.c` gives both `MENU_SLOT_CANE` and the 4x3 item
   grid has no free cell. Whichever the run finds first locks the other out.
4. **Bottles** — an empty bottle is a common REWARD and an uncommon
   WEAPON/TOOL, gated on having a free slot. Bottles were the hidden blocker
   on charms.

### Still not obtainable, deliberately

- `ITEM_RED_SWORD` — `CreateObject(GROUND_ITEM, ITEM_RED_SWORD)` never makes an
  entity, so it stays a `GiveItem`-only miniboss payout.
- `ITEM_LIGHT_ARROW` (Bow of Light) — same risk, unverified as a floor item.
- Green / Blue / Four Sword — no drop path.
- Two loose fairies — that is the FAIRY room kind, not an item.

### Lotteries are separate on purpose

`sQuickStartLotteryPrizes` is a fixed 8-entry table (5 common / 2 uncommon /
1 rare) with no prerequisites and no already-owned filter. A lottery decides
its prize on the first visit and must recognise that exact item on the floor
later (`QuickStartGroundItemOfForm`), so its draw has to be a pure function of
the stored seed — a tier draw filters on current inventory and could answer
differently the second time, leaving the room permanently unsolved.

### Not verified in play

The table, the curve and the prerequisite logic are verified statically and by
the invariant checker. **No drop has been watched landing in the emulator** —
in particular the charm route (bottle -> drink -> permanent) and the
Fire Rod / Cane exclusion are reasoned, not observed.
