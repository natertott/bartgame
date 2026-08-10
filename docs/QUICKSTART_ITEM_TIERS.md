# Item tiers, sources, and status effects

Design notes for the item system. Nothing here is implemented yet - this is
the categorization written down, plus answers to the two feasibility
questions, plus the engineering constraints that will shape the build.

---

## 1. Categories and tiers

### KEY ITEMS
Mole Mitts, Cane of Pacci, Lantern, Pegasus Boots, Roc's Cape, Grip Ring /
Power Bracelets, Zora's Flippers.

No tier split given, and they probably do not want one: each is a movement or
access verb, and the run either has it or does not. Seven items, one shop slot
per run, no ? room source - see the open question in §5.

### REWARDS
| | |
|---|---|
| Common | 50 rupees, heart piece, blue potion, empty bottle |
| Uncommon | 100 rupees, two fairies, red potion |
| Rare | 200 rupees, full heart container, fairy in a bottle |

### WEAPONS / TOOLS
| | |
|---|---|
| Common | Bow, bombs, boomerang |
| Uncommon | Big bomb bag, big quiver, remote bombs, bottle, gust jar |
| Rare | Magical boomerang, mirror shield, bow of light, sword upgrade |

### SKILL UPGRADES
| | |
|---|---|
| Common | Spin attack, rock/pot break, roll attack |
| Uncommon | Dash attack, peril beam, sword beam |
| Rare | Down thrust (requires Roc's Cape), great spin (requires spin attack) |

### STAT UPGRADES
Din's Charm, Farore's Charm, Nayru's Charm, the three Joy Butterflies.
**Needs a tier split** - six items with no common/uncommon/rare assigned.
Suggestion below in §5.

### EXCLUDED
Wallet, Big Wallet.

---

## 2. Where things come from

| Source | Eligible categories |
|---|---|
| Shop, always stocked | Arrows, bombs, shields, heart pieces |
| Shop, one rolled slot each | KEY ITEM, WEAPON/TOOL, SKILL UPGRADE, STAT UPGRADE, REWARD x2 |
| ? rooms | Everything except KEY ITEMS |
| Pot-breaking overworld quest | REWARDS only |
| Later side quests | To be decided per quest |

Shop rules:

- Arrows, bombs and shields are cheap relative to everything else, with a
  fresh semi-random price each run - the mechanism already exists
  (`GF_SHOP_PRICE_BIT`, rolled once per run in `QuickStartRandomizeShopOnce`).
- Heart pieces start cheap and rise **+25 rupees per purchase**, capped at
  999. Needs a per-run purchase counter (§4).
- The six rolled slots draw from their category by tier weight: common often,
  uncommon less, rare rarely.
- Buying a rolled slot retires it - that slot stays empty afterwards.

---

## 3. Can vanilla's unused items carry our own effects?

**Yes, and better than expected: three separate buff frameworks already exist,
already persist in the save, and already have visual feedback.** None of this
needs inventing.

### 3a. The charm framework - combat multipliers

`gSave.stats.charm` + `charmTimer`, set from a bottle
(`playerItemBottle.c`, 3600 frames = 60s), ticked down in `interrupts.c`, and
consumed in **`CalculateDamage` (collision.c)**:

| Charm | Effect |
|---|---|
| Nayru | incoming damage / 4 |
| Farore | incoming damage / 2, outgoing player-item damage x 1.5 |
| Din | outgoing player-item damage x 2 |

`GetPlayerPalette` (playerUtils.c) tints Link per charm, so a new charm value
gets a colour for free.

This is exactly the "book grants a stat boost / book acts as a curse" idea,
already wired. A curse is a multiplier below 1 in the same switch - the
function is four lines of arithmetic and takes new cases trivially.

### 3b. The picolyte framework - drop-table modifiers

`gSave.stats.picolyteType` + `picolyteTimer` (900 frames = 15s). In
`itemUtils.c` the type indexes `gEnemyDroptables[type + 6]` and that row is
**summed into every enemy's drop roll**.

This is literally "increases the chance of finding rare items". A quest item
that sets a picolyte-like type for a long duration - or permanently for the
run - biases hearts, rupees or kinstones without touching a single drop site.
Note the sentinel trap we already hit once: `-999` means "never" and negatives
clamp to zero, so modifiers must be *assigned* over it, not added.

### 3c. The effect framework - aura + player-flag

`gSave.stats.effect` + `effectTimer`, set by wisps (`enemy/wisp.c`, 600
frames). While non-zero it forces `PL_DRUGGED` on the player and spawns
`FX_RED_AURA - 1 + effect` every 64 frames. A ready-made channel for a
timed debuff with a visible aura.

### 3d. Speed

There is no speed stat, but there does not need to be. Movement speed is a
plain value assigned per state, and vanilla already branches on an item:

```c
if (GetInventoryValue(ITEM_SWIM_BUTTERFLY) == 1) speed = 0x100; else speed = 0xc0;
```

Walking is `0xa0`. A walk-speed buff is the same shape of edit in
`playerUtils.c`. Cheap and safe.

### 3e. Immunity to status

`PL_BURNING` and `PL_FROZEN` are bits in `gPlayerState.flags`. Suppressing
them for an item is a guard where they are set. Straightforward.

**Verdict:** every effect suggested - speed, attack, defence, rare-find rate,
status immunity - maps onto something that already exists. The work is
choosing numbers and writing the item-to-effect table, not building
machinery. The one real cost is that most of these are *timed* in vanilla;
run-long versions need our own storage (§4).

---

## 4. Can Link's weapons apply freeze / burn / shock to enemies?

**Not as a switch, and the honest answer is more interesting than yes or no.**

What vanilla actually has:

- **A damage-source channel, not an element system.** The attacker sets
  `hitType`; the receiver reads `contactFlags & 0x7f` and switches on it.
  Every enemy hand-codes which sources it reacts to - `bobomb.c` has cases for
  `0xe/0x14/0x15/0x16`, `businessScrub.c` tests `hitType == 1 &&
  (contactFlags & 0x7f) == 0x42`. There is no shared "this hit was cold" bit.
- **Freezing is not a status at all.** It is bespoke objects -
  `object/frozenOctorok.c`, `object/frozenFlower.c` - placed by the room. An
  enemy is not frozen; a frozen-thing entity exists instead.
- **Burning is a player state** (`PL_BURNING`) plus per-object flammability.
  Enemies do not carry it.
- `EntityDisabled` is the only central "stop updating" path and it is driven
  by global cutscene priority, so it cannot suspend one enemy.

So a real per-enemy freeze means adding status storage to the enemy struct
and teaching every enemy in the roster to honour it. That is a feature, not a
tweak, and I would want it prototyped on one enemy before it goes in a plan.

**But there is a cheap 90% version that works today.** Enemies already honour
`knockbackDuration` centrally - it is what makes them reel and stop acting
after a hit. An "ice arrow" that sets `knockbackDuration` to ~120 frames
instead of ~4, plus a palette swap via `ChangeObjPalette`, reads as a freeze,
needs no new state, and works on every enemy that already supports knockback.
Same trick gives a "shock" (short repeated stun) and a "burn" (damage over
time by re-applying damage on a timer from our own monitor).

Recommendation: build the cheap version first as an elemental-arrow or
elemental-sword modifier, play it, and only invest in true per-enemy status if
the stun version feels hollow.

---

## 5. Engineering constraints and open questions

### Flag space - the binding constraint

The QUICKSTART flag window (`FLAG_BANK_12` + origin 700) is nearly full:
offsets run to 703 with a ceiling of **707**. Four left.

A rough count for the item system: six rolled shop slots at ~6 bits each
(36), six sold-out latches (6), a heart-piece purchase counter (6) - about 48
flags. It does not fit, and no amount of shuffling makes it fit.

**It does not need to.** `FLAG_BANK_11` is 192 bits, of which we use bits
0-31 for the region wave counters and 32-39 for quest state. **Bits 40-191 are
free** - 152 bits, three times what the item system needs. The item system
should live there from the start rather than squeezing into bank 12. There
are also six flags deliberately held in reserve at 255-260
(`GF_CAVE_POOL_BIT`, `GF_CAVE_ROOM_BIT`) if a bank-12 slot is ever wanted.

### Questions before I build anything

1. **"That slot is not filled for the rest of the game"** - the rest of the
   *run*, or permanently across runs? Permanent means a veteran save has a
   near-empty shop, which I doubt is the intent. I will assume per-run unless
   told otherwise.
2. **Key items have exactly one source** - the shop's one key-item slot. Seven
   key items, one slot, and buying it empties the slot. So a run gets at most
   one key item, only if the player can afford it. Deliberate? It makes key
   items feel enormous, but it also means a run can be locked out of a
   movement verb entirely by price.
3. **Sword upgrade appears twice.** It is listed as a WEAPON/TOOL rare, but
   the Red Sword is already a rare miniboss reward. Keep both sources, or make
   the shop the only one?
4. **STAT UPGRADES need a tier split.** Suggestion: charms common (they are
   timed and consumable in feel), butterflies uncommon (permanent but narrow),
   leaving rare empty - or promote one charm to rare and make it run-long.
5. **How long do effects last?** Vanilla charms are 60 seconds. For a
   roguelite, run-long is more interesting than a 60-second window, but that
   is a different feel and a different storage cost.

### Suggested build order

1. The tier tables and the weighted roll (pure data, no new mechanics).
2. Shop restructure: always-stocked four, six rolled slots, sold-out latches,
   escalating heart-piece price. Storage in `FLAG_BANK_11`.
3. ? room drops draw from the same tables, key items excluded.
4. Quest-item effects on the charm and picolyte frameworks - three or four to
   start, one of each shape (buff, curse, find-rate, immunity).
5. Elemental weapons via the knockback-stun version, if 4 lands well.
