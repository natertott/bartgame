# Overworld side-quests: budget research and implementation assessment

Research pass before building. Everything numeric below is **measured in the
emulator against the current build**, not estimated — the scripts are
`scratchpad/budget_curve.py` (entity + GFX load per region per difficulty)
and the audits described in each section.

---

## 1. The budgets, measured

Three separate currencies. They are not equally scarce, and the one that
binds is not the one we have been watching.

### 1.1 Entity slots — 72 game-wide

Peak live entities during combat, by region and difficulty:

| region | diff 0 | diff 4 | diff 8 | diff 12 |
|---|---|---|---|---|
| South Hyrule Field | 37 | **70** | 70 | 67 |
| North Hyrule Field | 39 | 58 | 53 | 35 |
| Castle Garden (no waves) | 11 | 11 | 11 | 11 |
| Lon Lon Ranch (no waves) | 11 | 11 | 11 | 11 |
| Trilby Highlands (no waves) | 1 | 1 | 1 | 1 |

South Hyrule Field is **already at 70 of 72** by difficulty 4. That is not a
quest budget — that is a wall. Any quest that spawns entities in SHF at
mid difficulty will fail to spawn, silently, exactly the way the pot-lottery
prize used to.

Regions not currently drawn into the chain sit at 11 or fewer, so the
headroom is wildly uneven: it depends on whether the region is hosting
waves, not on the region itself.

### 1.2 GFX slots — 44 game-wide (`MAX_GFX_SLOTS`)

This is the one we have never measured, and it is the real ceiling:

| region | diff 0 | diff 4 | diff 8 | diff 12 |
|---|---|---|---|---|
| South Hyrule Field | 18 | 19 | 30 | **44 (full)** |
| North Hyrule Field | 25 | 28 | **44 (full)** | **44 (full)** |

Both combat regions **completely exhaust the GFX table** by difficulty 8–12.
At that point there is not one slot left for a quest sprite, a fuser, a
quest enemy, or a quest item.

This also explains the open finding from the room survey — "POT_MINISH
hosts multi-enemy content, entities exist in RAM, sprites never render."
That is GFX-slot exhaustion, and it is a *general* failure mode, not a
property of that one room.

**What spends it:** distinct enemy *types*, not enemy *count*. SHF at
difficulty 12 had 56 enemies of **13 distinct types**; NHF at difficulty 12
had only 27 enemies but still hit 44/44. Roughly 2–3 slots per additional
type, on top of a ~18–25 slot baseline of terrain, player and effects.

Note the inversion in the tables: NHF at difficulty 12 shows *fewer*
entities (35) than at difficulty 4 (58). Spawning is being throttled by
exhaustion upstream — we are already over budget and losing content
without any error.

### 1.3 Flag / save storage — comfortable

- QUICKSTART's own flag window is full to offset 665; **42 offsets free**
  (666–707). Tight.
- `FLAG_BANK_11` is 192 bits and we use **32** (region wave counters), so
  **160 bits are free** there. That is the pool to spend quest state from.
- Kinstone state does **not** cost us flags at all: vanilla already has
  `gSave.kinstones` — a 19-slot bag (`types`/`amounts`), `fuserOffers[128]`,
  and a `fusedKinstones` bitfield.

Storage is a non-issue for the quest scope discussed here. Sprites are the
issue.

---

## 2. Kinstone fusions

### 2.1 What already exists (almost all of it)

The vanilla economy is intact and we are already using parts of it:

- **Bag**: `AddKinstoneToBag` accepts piece ids `0x65–0x75` (17 generic
  pieces — the colour/shape collectables). `ITEM_KINSTONE_RED/BLUE/GREEN`
  (0xfc–0xfe) are the drop forms that feed it.
- **Drop rates are already data**: `Droptable` has `kinstoneRed`,
  `kinstoneBlue`, `kinstoneGreen` weight fields, summed per drop from the
  enemy/area/modifier tables, and there is a `DROPTABLE_NO_KINSTONES`
  modifier. QUICKSTART already patches this table (we bump rupee weights
  for enemy drops) — **kinstone drop rates are a few lines in a hook that
  exists**.
- **Fusion**: `AddInteractableAsMinishFuser(entity, kinstoneId)` makes any
  entity a fuser offering a specific fusion. `GetFusionToOffer` walks the
  offer list and applies a per-fuser "fickleness" roll
  (`fuserStability <= Random() % 100` → refuse) — which is *exactly* the
  "fusion rate decreases with difficulty" knob you described, already in
  the engine's shape.
- **Gates**: `WriteBit(&gSave.kinstones.fusedKinstones, id)` opens the gate;
  `roomInit.c` skips loading the blocking entity/tiles when fused.

### 2.2 The nine gates already in our regions

This is the important discovery. Nine **real vanilla kinstone-gated
entrances** already sit in the regions we use, and we currently **pre-fuse
all of them at boot** as a stopgap (`game.c`, the `WriteBit` block):

| region | gate ids | what they open |
|---|---|---|
| Lon Lon Ranch | `0x29` | Goron wall crack → the cave |
| South Hyrule Field | `0x32`, `0x58` | Heart Piece tree, Rupee cave |
| North Hyrule Field | `0x59`, `0x40`, `0x4d`, `0x5a`, `0x2d` | 4 Boomerang trees, Fairy Fountain tree |
| Trilby Highlands | `0x3f` | Rupee cave |

So the feature is not "build a kinstone system" — it is **stop pre-fusing
these nine, and place a fuser in the same region instead**. Your constraint
("fusion sites always in the same overworld map as the doors they unlock")
is satisfied by construction, because these gates and their rooms are
already co-located.

Castle Garden has none, so it would need either a synthetic gate or to be
left as the un-gated region.

### 2.3 Proposed shape

- **A `QuickStartKinstoneGate` table**: `{region, gateKinstoneId, fuserX,
  fuserY, requiredPieceId}` — one row per gate, same table-driven model as
  every other system here. The fuser spot goes through the same measured /
  `QuickStartFindOpenTileNear`-snapped placement as everything else, and
  the invariant checker gets a tier asserting each fuser spot is open,
  reachable, and in the same room as its gate.
- **Per-run reset**: clear the nine `fusedKinstones` bits at boot instead of
  setting them. Costs no new flags.
- **Drop rate**: extend the existing `#ifdef QUICKSTART` block in
  `itemUtils.c` with kinstone weights scaled by
  `QuickStartGetDifficulty()` — high early, decaying later, exactly as you
  described.
- **Guaranteeing "some but not all"**: the honest way to hit that target is
  a **floor plus a decaying rate**, not rate alone. A pure random rate can
  always roll zero. Suggestion: first N kills in a region drop a guaranteed
  piece (the floor), everything after that rolls the difficulty-scaled
  rate. That gives "always enough for some doors, grind for all of them"
  deterministically rather than hopefully.
- **Fusion refusal**: our own roll, difficulty-scaled, mirroring vanilla's
  fickleness — so a fuser may need a second or third approach at high
  difficulty.

### 2.4 Cost

- Flags: ~0 (vanilla storage).
- Entities: **1 per unfused gate present in the region**. NHF has five
  gates — five fusers at once, in the region that hits 44/44 GFX by
  difficulty 8.
- GFX: **0 if the fuser reuses a sprite already resident in that region**
  (a vanilla animal/NPC already loaded), **2–3 slots if it is a new
  sprite**. With five fusers in NHF this is the difference between free
  and impossible. Strong recommendation: **fusers reuse an already-loaded
  sprite**, at least until the type-cap work below lands.

---

## 3. Enemy-hunt quest

Spawn-on-activation, harder than the current tier, fixed type and count.

- **Mechanism**: reuse `QuickStartSpawnEnemiesOnOpenTiles` (already
  ground-aware, spaced, ENT_PERSIST-tagged) plus the existing
  `QuickStartEnemyIsOurs` ownership test for kill tracking. The wave-room
  kind already does nearly all of this; a hunt is that logic with a
  fixed roster and a region-scale placement area instead of a room-scale one.
- **"Harder than normal"**: the roster already has tiers
  (`sQuickStartLevel1..5`). A hunt at `min(difficulty + 2, 12)` reuses the
  existing tier machinery with no new enemy data.
- **Flags**: ~4 bits (active / count killed / done) in `FLAG_BANK_11`.
- **Entities**: 3–5.
- **GFX: the blocker.** If the hunt enemy is a type *already spawned in
  that region this run*, cost ≈ 0. If it is a new type, 2–3 slots — and at
  difficulty ≥8 there are none. Since "harder than the current tier"
  implies a type the normal waves are *not* using, this quest structurally
  conflicts with the GFX budget at high difficulty.
- **Mitigation** (recommended): while a hunt is active, **reserve a type
  slot** — reduce the region density spawner's type roster by one. Keeps
  the total constant instead of overflowing.

## 4. Item-finding quest

Find a key/quest item hidden under a bush, or dropped by a specific enemy.

This is the **cheapest** of the three and the best first build:

- **Under a bush**: vanilla grass/bush objects already populate the
  regions; a "this specific bush holds the item" flag plus a drop on
  destruction. No new sprite for the bush.
- **Dropped by an enemy**: hang it off the existing per-enemy drop path we
  already hook.
- **The item itself**: a `GROUND_ITEM`, whose sprite sheet is already
  resident (every ? room reward uses it). **GFX cost ≈ 0.**
- **Entities**: 1–2. **Flags**: ~3 bits.
- One caveat learned the hard way this week: **equipment has no ground-item
  form** (`CreateObject(GROUND_ITEM, ITEM_RED_SWORD)` silently creates
  nothing). A quest item must be a real item id with a ground form, or be
  granted via `GiveItem` with a message.

## 5. Other quest mechanisms worth testing — puzzle-leaning

Ranked by cost, cheapest first. The first four add **no new sprites at
all**, which is what makes them viable at high difficulty:

1. **Timed traversal** — reach a marked spot within N seconds. Pure logic,
   zero entities, zero GFX. Cheapest possible quest; also the best vehicle
   for testing the quest *framework* before spending sprites on content.
2. **Switch/bridge puzzle** — we already built a switch-driven bridge in
   North Hyrule Field. Generalise it: "throw the 3 switches in this
   region." Reuses existing objects; near-zero GFX.
3. **Gust Jar clearing** — the Gust Jar is granted at spawn, and vanilla
   has dust piles/webs. "Clear the 3 dust piles." Only free if those
   objects are already resident in the region — needs one measurement.
4. **Fetch-and-carry** — lift a pot/object and carry it to an NPC. Reuses
   the exact lift/carry path we just verified in the shop. Zero new
   sprites if both ends already exist.
5. **Torch lighting** — light N torches; ties naturally to the Lantern key
   item, so the quest becomes a *reason* to pick it, strengthening the
   item-choice phase. Costs a torch sprite if not already resident.
6. **Minish-scale errand** — shrink, enter a hole, retrieve something. All
   machinery exists (portals, Minish rooms, the boots gate). Costs the
   shrink route rather than sprites; naturally gated behind Pegasus Boots,
   consistent with the elite Minish room.
7. **Dig site (Mole Mitts)** — vanilla dirt tiles exist (Lon Lon's cave
   uses one). Same "quest as a reason to choose an item" benefit.
8. **Escort/follow** — an NPC that must survive. Honestly assessed:
   expensive, fiddly, AI-dependent, and the highest bug risk of the set. I
   would not build this until the framework is proven.

The pattern worth noting: options 5–7 each make a *key item choice*
meaningful, which is currently the weakest part of the run (four of the
five key items have no surveyed gate anywhere in the pool). Quests are the
cheapest way to give those items a purpose.

---

## 6. The recommendation

**The GFX ceiling should be fixed before quests are built, not after.**

At difficulty ≥8 the overworld is already over budget and silently losing
content. Adding quests on top of that will produce invisible sprites and
non-spawning enemies that look like random bugs and cost days to diagnose —
we have already paid that price once with POT_MINISH.

Suggested order:

1. **Measure and cap enemy type variety.** The region density spawner rolls
   a type per enemy independently, which is how SHF reaches 13 distinct
   types. Cap distinct types per region (6 is a reasonable first trial) and
   re-measure the curve. Expected to free a large block of GFX; the number
   should be measured, not assumed.
2. **Add a GFX-slot tier to the invariant checker** — assert free slots
   remain at each difficulty in each region, so exhaustion becomes a build
   failure instead of a play-test mystery.
3. **Build the item-finding quest first** (cheapest, near-zero GFX) to
   prove the quest framework, flags, and reset behaviour.
4. **Then kinstone fusions** — the highest-value feature, mostly already
   built in vanilla, and the one that turns nine pre-solved stopgap gates
   back into real content.
5. **Then the enemy hunt**, once the type-slot reservation exists to pay
   for it.

### Decisions I need from you

- **Castle Garden has no vanilla kinstone gate.** Leave it un-gated, or
  give it a synthetic gate?
- **Fuser sprite**: reuse an already-resident sprite (free, less
  distinctive) or a dedicated one (2–3 GFX slots, only affordable at low
  difficulty or after the type cap)?
- **Type cap**: is reduced enemy variety at high difficulty an acceptable
  trade for quest headroom? It is currently variety-vs-quests, and the
  budget cannot pay for both.
