# Item tiers, sources, and status effects

Design notes for the item system: the categorization written down, answers to
the two feasibility questions, and the engineering constraints that will shape
the build.

Built so far: §6 (run-long charms) and §7 (starting loadout). §8-10 are
research answers, not implementations.

---

## 1. Categories and tiers

### KEY ITEMS
Mole Mitts, Cane of Pacci, Lantern, Pegasus Boots, Roc's Cape, Grip Ring /
Power Bracelets, Zora's Flippers.

No tier split: each is a movement or access verb, and the run either has it or
does not.

**Two sources, for now:** the opening item-selection rounds (round one is
drawn from this category) and the shop's key-item slot. More sources - side
quests, new ? room types - come later, and they are blocked on the overworld
region progression system, which first needs a map of which items are required
to traverse which regions. That map does not exist yet and is the real
prerequisite here.

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

Sword upgrades are WEAPON/TOOL items, not a category of their own, and keep
every source: the shop, ? room rewards, item drops, and the miniboss reward
that already grants the Red Sword.

### SKILL UPGRADES
| | |
|---|---|
| Common | Spin attack, rock/pot break, roll attack |
| Uncommon | Dash attack, peril beam, sword beam |
| Rare | Down thrust (requires Roc's Cape), great spin (requires spin attack) |

### STAT UPGRADES
| | |
|---|---|
| Common | *(none - deliberately empty)* |
| Uncommon | Joy Butterflies (arrow, dig, swim) |
| Rare | Din's Charm, Farore's Charm, Nayru's Charm |

Charms are permanent for the run - see §6.

### EXCLUDED
Wallet, Big Wallet.

---

## 2. Where things come from

| Source | Eligible categories |
|---|---|
| Shop, always stocked | Arrows, bombs, shields, heart pieces |
| Shop, one rolled slot each | KEY ITEM, WEAPON/TOOL, SKILL UPGRADE, STAT UPGRADE, REWARD x2 |
| ? rooms | Any category except KEY ITEMS |
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
- Buying a rolled slot retires it **for the rest of that run**. A new run
  starts with a full shop again.

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

### Answered

1. **Sold-out slots are per-run.** A new run restocks the shop completely.
2. **Key items: opening selection + shop only, for now.** More sources wait on
   the region progression system and its item-to-region requirement map.
3. **Sword upgrades stay WEAPON/TOOL** and keep all their sources, miniboss
   reward included.
4. **? room rewards draw from every category except key items.**
5. **STAT UPGRADES: no common tier.** Butterflies uncommon, charms rare.

### Suggested build order

1. The tier tables and the weighted roll (pure data, no new mechanics).
2. Shop restructure: always-stocked four, six rolled slots, sold-out latches,
   escalating heart-piece price. Storage in `FLAG_BANK_11`.
3. ? room drops draw from the same tables, key items excluded.
4. Quest-item effects on the charm and picolyte frameworks - three or four to
   start, one of each shape (buff, curse, find-rate, immunity).
5. Elemental weapons via the knockback-stun version, if 4 lands well.

Step 4's foundation is already in - see §6.

---

## 6. Run-long charms - DONE

Priced and built, because the cost turned out to be small.

| Piece | Cost |
|---|---|
| Stop them expiring | One `#ifndef QUICKSTART` around the tick in `interrupts.c`. The timer is simply never decremented, which also keeps it above the `0xb4` threshold `GetPlayerPalette` uses to blink the tint when a charm is about to lapse. |
| Clear them per run | Two lines in `GameTask_Transition`, alongside rupees and health. Charms live in `gSave.stats`, which persists across runs, so with nothing expiring them the run boundary has to. |
| Hold more than one | `gSave.stats.charm` is a single byte, so vanilla's second charm replaces the first - correct for a 60-second drink, wrong for a rare permanent pickup. Ownership moved to three bits in `FLAG_BANK_11` (40-42), and `CalculateDamage` reads that mask instead. ~20 lines, all `#ifdef`-guarded. |
| Grant path | Free. `BOTTLE_CHARM_NAYRU/FARORE/DIN` are values in the same enum as `ITEM_BOTTLE_*`, so a charm is granted by filling a bottle exactly like the "fairy in a bottle" reward already on the list. The player drinks it to activate. |
| Palette | Free. `gSave.stats.charm` is still set to the most recent charm purely so `GetPlayerPalette` keeps tinting Link. |

Verified in the emulator: bits clear at boot; drinking Din sets its bit and
the vanilla byte; after 1200 frames the timer still reads 3600 where vanilla
would read 2400; drinking Nayru afterwards leaves Din's bit set.

**Balance note.** Charms now stack, and the multipliers were written for a
one-at-a-time drink. Nayru and Farore together divide incoming damage by 8;
Din and Farore together triple outgoing. That is a large swing for a mode
whose difficulty is a wave counter. It is deliberate - they are the rarest
tier - but if the late game starts feeling trivial, these multipliers are the
first number to reach for, ahead of enemy health or wave size.

---

## 7. Starting loadout - DONE

**Sword and shield only.** The Bow, its arrows, Bombs, the Fire Rod and the
Light Arrow are no longer granted at boot, `equippedExtra[0]` (the L slot)
starts empty, and `arrowCount`/`bombCount` start at zero. Verified at boot:
owned items are Smith's Sword, Shield, Gust Jar; A = shield, B = sword,
L = nothing, 0 arrows, 0 bombs.

**The Gust Jar is a deliberate exception and needs a decision.** It is the
only thing that can damage `CHUCHU_BOSS` - Castle Garden's boss, whose core is
vulnerable to being sucked in and slammed, not to sword hits, exactly as in
its vanilla Deepwood Shrine fight. Taking it away makes Castle Garden
unwinnable. Three ways out, none of them free:

1. Leave it free, as now. Cheapest, but "sword and shield only" is not quite
   true.
2. Give the boss a second answer - make its core take sword damage. Changes a
   vanilla fight.
3. Guarantee a Gust Jar before Castle Garden can come up in the chain. Most
   in keeping with the design, most work, and it needs the region progression
   system that key items are already waiting on.

## 8. The Fire Rod as a drop

Easy, and the slot problem is our own, not vanilla's.

`itemMetaData.c` gives `ITEM_FIRE_ROD` `MENU_SLOT_CANE`. Vanilla ships it with
menuSlot `0x63` - the "not on the grid" sentinel, the same one `ITEM_NONE`
uses - because the rod is unreachable content there. We gave it the cane's
cell earlier in this project *because* the Cane of Pacci was never granted, so
there was no collision to worry about. Now there would be.

The item grid has twelve cells (`MENU_SLOT_SWORD` through `MENU_SLOT_BOW`) and
all twelve are spoken for by items in the tier lists, so there is no free cell
to give the rod and the menu art is a fixed 4x3 box. **The fix is not a new
cell - it is making the two mutually exclusive in the roll:** if the run
already holds one, the other cannot be drawn. One condition in the draw, and
the player never sees the seam.

Would it break anything else? No. The rod is already a fully working item in
this build - `src/item/itemFireRod.c` drives it and
`playerItemFireRodProjectile.c` is a complete projectile - it has simply been
a boot grant rather than a find. It is a ranged damage option, which is the
same role as the Bow, so it slots into WEAPON/TOOL without disturbing balance.
The one thing to watch is that its projectile lights braziers and burns
bushes, so it can substitute for the Lantern in a couple of places - a bonus
rather than a problem, but worth knowing before the Lantern's key-item value
is priced.

## 9. Can the Ocarina warp to arbitrary locations?

**Yes, and it is pure data.** This is the cheapest of everything discussed.

The eight windcrest destinations are `gUnk_08128024[]` in
`src/menu/kinstoneMenu.c` - and they are **ordinary `Transition` rows**, the
same struct every exit list in `transitions.c` uses:

```c
{ 1, 0, 0, 0x2c8, 0x128, 0, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD, 1, 12, 4, 0 },
```

The fast-travel subtask reads that array for both the map markers
(`sub_080A6EE0`) and the warp itself - on confirm it calls
`sub_080A71F4(&gUnk_08128024[choice])`, which is a thin wrapper over
`DoExitTransition`. Availability is `gSave.windcrests` bits 24-31, one per
row, and the MAPEXPLORE branch already sets `windcrests |= 0xFF000000` to
unlock all eight.

So: rewrite eight rows with our own area/room/x/y, set the eight bits, done.
No engine work. Natural uses - warp to the region's entrance, to the shop, to
the hub. The map-marker screen positions itself from
`gAreaRoomHeaders[area][room].map_x/map_y`, so markers land correctly for any
destination without extra work.

Two caveats. `CreateBird` gates the whole thing on `AreaAllowsWarp()`, so the
rooms it can be used *from* need checking. And eight is the table size the
menu is drawn for - more destinations than that is a real change, fewer is
free.

## 10. Can the cucco swarm become a summon?

**Feasible, medium effort, and the honest cost is in the last mile.**

What exists: `CUCCO_AGGR` is a complete enemy (`src/enemy/cuccoAggr.c`, 396
lines). `gCuccoAggrSpawnPoints[]` is a ring of 24 offsets around the screen
border - the swarm flies in from off-screen. `cuccoMinigame.c` already spawns
them in bulk with `CreateEnemy(CUCCO_AGGR, ...)`. So "call in a swarm from
off-screen" is a solved problem we can call directly.

What does not exist: they attack **Link**. Their homing is two
`GetFacingDirection(&gPlayerEntity.base, super)` calls, and they are `ENEMY`
kind, so `CalculateDamage` routes their damage to the player. Enemy-to-enemy
collision is not wired in this engine.

- Retargeting the **movement** is easy: swap the player pointer for a
  nearest-enemy pointer. We already sweep `gEntities` every frame in the room
  monitor, so "nearest enemy to Link" is a small helper.
- Making them **hurt** enemies is the real work, and the answer is not to
  fight the collision system: let the cuccos be the visual, and apply the
  damage ourselves from the monitor - each frame, for each summoned cucco,
  damage and knock back enemies within a radius. Fully controllable, no
  engine surgery.

Rough shape: a summon manager in game.c that spawns N cuccos at the ring
offsets, retargets their homing each frame, applies proximity damage,
despawns after ~600 frames, and gates re-use on a cooldown. The cooldown wants
a frame stamp rather than flags - `gSave.run_frames` already exists for this
mode, and `final_wave_frame` is precedent for adding another `u32` beside it.

Two constraints. The swarm needs a sprite sheet, and the gfx reserve is four
slots with a hard floor of two - North Hyrule Field sits at three free at high
difficulty, so the summon must respect `QuickStartGfxBudgetForSpawn` and
probably scale its count down. And **the Ocarina cannot be both a warp and a
summon** - one button, one behaviour. If both are wanted, one of them needs a
different trigger.
