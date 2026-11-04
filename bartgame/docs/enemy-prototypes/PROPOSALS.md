# New enemy prototypes: filth, gilt and readable combat

2026-11-04 · review proposal, not an adopted replacement bestiary

The first three candidates add **a committed straight charge, an announced
burrowing ambush, and armor that rewards flanking**. These mechanics add new
combat decisions without requiring a new item or replacing the five selected
forest enemies. Their optional combat lab passes110/110 actual mGBA checks
across14 controlled scenarios. Ordinary procedural room rosters retain Coin
Toad, Quill Moth, Trumpet Bellflower, Pear Bladder and Moth Confessor. The boss
remains the purple heart broken down its middle. Names and prototype art below
are provisional.

The distinction matters: **source facts** describe the previous Zelda Fan Game;
**prototype tuning** describes this independent BARTGAME implementation;
**later proposals** are unimplemented ideas for review. A polished illustration
is not evidence of a working attack, counter, or vulnerability.

## What the old design actually supplies

The starting point is the carried-over
[enemy/object specification](../../../docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#enemies),
its [live curated arrays](../../../src/game.c), and the source behavior/collision
code. The curated roster contains **71 enemy/form picks across six buckets**,
not 213 independent monsters. The raw table includes color forms, children of
segmented creatures and scripted boss parts. [SOURCE_AUDIT.md](SOURCE_AUDIT.md)
records the exact roster, source links, damage interpretation and unavailable
item dependencies; [source_catalogue.json](source_catalogue.json) retains
machine-readable provenance. Historical names below identify mechanics to
study, rather than final names or artwork to copy.

Use the current game's units when evaluating a prototype:

| Current rule | Value or behavior |
| --- | --- |
| Player heart | 8 HP; contact damage 2 removes a quarter heart. Enemy HP is not measured in player hearts. |
| Normal sword / arrow | 2 enemy HP per accepted hit, before any later modifiers. |
| Blightseed explosion | 8 enemy HP; the existing explosion can also hurt Bloom for 4 HP. Directional armor still checks the incoming direction. |
| Thrown object | Pot/bush 2; rock/boulder 4, using the current object system. |
| Candle/lantern | Burns supported terrain and lights features. **It currently deals no enemy damage.** A fire counter needs a real combat hook before being advertised. |
| Shield / cape | The shield can block applicable frontal contact. Cape avoidance follows the existing height/collision rules; it is not a promise of invulnerability against everything. |

In the original data, `damage_type` is a collision-matrix row ID, not the amount
of damage. Likewise, Bob-omb's 255 HP is part of a special lifecycle, not a
request for 128 sword hits. These shortcuts would produce misleading tuning.

## Optional pilot: controls, isolation and current evidence

The implementation is isolated by `BART_ENEMY_LAB=1` in the
[Makefile](../../Makefile). The normal default is `0`; its generated roster
never selects these three IDs. The native state machines live in
[enemy_prototypes.c](../../src/enemy_prototypes.c) and the provisional sheets in
[enemy_prototypes.py](../../art/enemy_prototypes.py). This report was reconciled
against that code, not merely the initial brief. **The frozen lab passes110/110 actual mGBA checks across14 controlled
scenarios. These are mechanic studies, not production-ready encounters.**
The [review gallery](../../../enemy-prototype-review/README.md) provides actual
recordings, the source commit, playable builds and validation limits.

In the optional ROM:

| Control / setup | What actually happens |
| --- | --- |
| Title New Game: **A or Start** | Enters the real generated forest and opens the lab introduction. Dismiss the introduction before cycling encounters. |
| **Select** during live play | Cycles **Gilt Leech → Root Maw → Reliquary Snout → all three → Gilt Leech**. Each selection clears the active actor set and respawns that fixture on valid floor. It does not regenerate the room's tiles. |
| **B / L / A** initially | Sword / shield / blightseeds. Hold L for the shield under the existing rules. |
| **Start** | Opens the real inventory. Move to an owned tool; A/B/L equips it to that button. R changes pages; Start closes the menu. |
| Granted review loadout | 80 HP (ten hearts), 20 blightseeds, 50 arrows; sword, shield, candle, cape, gauntlet and bow are available. Switching cases refills the loadout. These are disclosed test fixtures, not earned run rewards. |
| Run-save guard | Lab `save_exists`/`save_load` return false; run-save write and erase return without touching the record. It does not import or persist the granted progression. Independent title appearance preferences still have their ordinary separate settings record; this is not a claim that all SRAM writes are disabled. |

Actor clearing isolates the fight, so the optional encounter replaces the
room's ordinary enemies, NPCs and loose objects; it does not substitute a fake
background or redraw procedural terrain. Tool use can still alter supported
room tiles. The fixture floor search is setup work and must be excluded from
steady-state combat performance measurements.

The [native review harness](../../tools/enemy_prototype_review.py) runs
separately from the game. It drives real inputs and AI but discloses navigation,
inventory, healing and coordinate-only positioning fixtures. Those controlled
counterprobes can establish damage/state rules; they are not evidence of an
unassisted complete run. Source sprite boards are design material. Only actual
emulator frames and their trace records may be labeled gameplay evidence.

## First playable review set

All three small bodies are designed initially for one native **16×16** sprite,
using the current game's lighting, foot baseline and palette conventions. Their
states must remain legible at native 240×160 resolution. Telegraphs are physical
poses and ground disturbances; their readability must not depend on glitter.
Times below are AI updates at the normal approximately 60 Hz rate. The existing
12-update hit-knockback phase pauses these state timers; menus and dialogue
also pause live combat. An interrupted phase therefore need not last the same
number of uninterrupted video frames.

### 1. Gilt Leech — Rope's committed charge

A squat black-green leech with a blunt, gilt mouth. Its broad, low body folds
horizontally when it spots Bloom; the mouth points along the exact attack lane.
The tail stretches during the charge, then bunches into an exhausted heap.
This is a charge silhouette, rather than another small creature endlessly
following the player.

**Play:** bait the alignment, step sideways, and punish the recovery. The leech
locks its direction before advancing; it does not secretly steer into a dodge.
The windup must be as visible facing north as it is facing south. A wall ends
the pass cleanly instead of letting the body vibrate against scenery.

| Prototype parameter | First-pass setting |
| --- | --- |
| HP / body contact | 4 / 2; two ordinary sword hits. |
| Patrol | 0.5 px/update. |
| Acquisition | Cardinal alignment within 8 px; distance 20–112 px, with a dry collision-clear lane sampled every 8 px. |
| Windup | 30 updates, compressed body and visible facing. |
| Charge | 1.625 px/update; direction locked; at most 36 updates or until obstructed. |
| Recovery | 36 updates; body visibly slack, ordinary damage still accepted. |

**Source versus adaptation:** Rope's source supplies HP 4, base speed 0.5,
30-update preparation and 1.625 charge. The explicit acquisition distance,
maximum pass length and generous recovery are prototype choices. Sword,
arrows, bombs and thrown objects work in visible states under the normal
rules. No special item is required.

### 2. Root Maw — Leever's visible ambush cycle

A diseased root bulb opens into a pale, toothlike wooden rosette. While buried,
its small disturbed-earth mound is recognizable as a creature: a moving slit
and displaced grass distinguish it from a hole, switch, chest or collectible.
On emergence, the mound rises, the rosette unfolds and the body becomes solid.
Grey grass and a little purple sap communicate sickness without turning the
whole floor into a hazard-colored field.

**Play:** notice the mound, give it room to surface, and attack the exposed
creature. Emerging is announced before it can hurt Bloom. The retreat retains
a brief punish window. Buried phases are temporary, not deletion: a clear-room
challenge must continue tracking the living enemy until it actually dies.

| Prototype parameter | First-pass setting |
| --- | --- |
| HP / body contact | 6 / 2; three ordinary sword hits. |
| Emergence site | Dry clear footprint, at least 40 px from Bloom, outside reserved features; a direct dry route from Bloom is sampled at steps no larger than 4 px. |
| Initial buried wait | 90 updates in the demonstration. |
| Emergence | 24 updates; visible, harmless and not yet hittable. |
| Exposed phase | 180 updates; 0.5 px/update approach; can hit and be hit. |
| Retreat | 24 updates; can be hit, cannot inflict contact damage. |
| Subsequent buried cooldown | 240 updates; harmless and unhittable. |

**Source versus adaptation:** red Leever supplies HP 6, the 180-update active
life and 240-update buried cooldown. Its original collision is enabled by an
animation cue, and motion varies with animation. Fixed 24-update transitions,
a visible mound, explicit safe radius and constant exposed approach speed are
new readability choices. Site selection tests at most twelve nearby candidates
before its current-position fallback. If neither is safe it remains buried and
retries after 30 updates; it does not force an unsafe emergence. The route
check is conservative straight-line sampling, not a full connected-component
flood fill, so a reachable site around a corner can still be rejected. A finite
buried state is not yet a proof that every obstructed generated room will
produce an emergence; that admission test remains necessary. Blue Leever's
shorter active phase and extra speed are not silently folded into this first
prototype.

### 3. Reliquary Snout — Helmasaur's directional armor

A low, snuffling creature carries a battered brass faceplate, like a tiny
ambulatory reliquary. The front has a single broad, bright plane and a blunt
snout; the native pilot uses a contrasting soft **red** rear against the gold
front. This is a provisional material choice using the existing effects bank.
Feet and hindquarters remain visible. The protected area must read from its shape,
including when the creature faces north; a floating glint alone cannot explain
where the player should strike.

**Play:** let the creature brace, dodge its committed rush, and strike the
exposed side or rear. A blocked frontal strike produces the existing
visible/audible clang while preserving HP; it does not yet play a dedicated body-recoil pose. An accepted
strike uses the hurt pose and ordinary hit feedback. Facing stays committed
through the rush and recovery, so a flank does not vanish through an instant turn.

| Prototype parameter | First-pass setting |
| --- | --- |
| HP / body contact | 4 / 2; two accepted ordinary sword hits. |
| Approach | 1 px/update in 24-update steps. |
| Brace | 60 updates; feet plant and headplate lowers. |
| Committed rush | 3 px/update, locked facing; at most 30 updates or until a wall. |
| Recovery | 30 updates, facing still locked. |
| Armor | Incoming direction within ±4 of the 32-direction front (a 90-degree arc) blocks direct hits in visible states; other directions accept ordinary damage. |
| Armor removal | Not implemented; no promised candle, bomb or Gust Jar removal. |

**Source versus adaptation:** Helmasaur supplies HP 4, base speed 1,
60-update brace and 3 px/update charge, plus directional armor. The source's
accepted rear-angle region is narrower than this prototype's side/rear opening.
The deliberately kinder 90-degree frontal guard and simplified approach are
new tuning. Source helmet removal uses Gust Jar, which this game's inventory
does not contain. The lab preserves flanking without inventing that item.
A rear/side bomb can deal the normal 8 HP; a front-directed hit is blocked under
the current directional check. The hit interface supplies damage and incoming
direction, not an attack-kind tag: armor currently applies the same guard to
sword, arrow, thrown object and explosion. Explosions do not strip the helmet.
Normal 12-update enemy invulnerability still suppresses repeated accepted hits.

### What each current tool does in this review set

| Tool | Gilt Leech | Root Maw | Reliquary Snout |
| --- | --- | --- | --- |
| Sword / arrow | Normal 2 HP on a valid hit. | Normal 2 HP while exposed or retreating; buried/emerging cannot be hit. | Normal 2 HP from sides/rear; front blocked. |
| Blightseed | Normal 8 HP on a valid explosion hit. | Valid exposed/retreating hit only. | Normal 8 HP from sides/rear under the existing incoming-direction guard; no helmet strip. |
| Thrown object | Existing 2/4 HP rules. | Valid exposed/retreating hit only. | Existing 2/4 HP from an accepted direction. |
| Shield | Ordinary applicable front-contact block; no automatic stun promised. | Ordinary applicable front-contact block while active. | Ordinary applicable front-contact block; does not flip or remove armor. |
| Cape | Existing leap/collision avoidance; helps cross the committed lane. | Can help move away from the announced emergence. | Can help evade the rush and reach a flank. |
| Candle | No enemy damage. | No enemy damage. | No enemy damage or helmet removal. |

These rules are deliberately sword-solvable. A room must never require a
finite ammunition supply to kill its final enemy or award a progression key.

## Broader roster: sixteen families worth exploring

Everything in this table beyond the three lab candidates is a **proposal**.
Suggested HP/contact values are starting points in current-game units, not a
claim that the source behaved identically. Final encounter tuning follows
playtests with the selected step-and-cut sword. None of these names or visual
concepts supersedes an already approved enemy appearance.

| Priority / source family | Provisional BARTGAME design | Distinct movement, attack and readable counter | Proposed HP / contact; integration need |
| --- | --- | --- | --- |
| Now · Rope | **Gilt Leech** | Compress, lock a straight lane, charge, recover. Side-step and punish; windup advertises the actual direction. | **4 / 2**; lab candidate above. |
| Now · red Leever | **Root Maw** | Visible mound unfolds into an exposed root mouth; finite buried cycle. Give emergence space, then strike. | **6 / 2**; lab candidate above. |
| Now · Helmasaur | **Reliquary Snout** | Brass front blocks; locked rush exposes sides/rear. Physical plate and soft body show the rule. | **4 / 2**; lab candidate above; no Gust Jar replacement. |
| Next · Spiked Beetle | **Briar Tick** | Narrow spiny body charges; a successful shield reversal exposes a pale belly. Upright sword clangs, flipped sword hurts. | **4 / 2**; implement shield-to-flip callback first. Keep a visible 150-update belly window and last-60 wobble as the initial source-based brief. Gate optional encounters by shield availability. |
| Next · Stalfos | **Marrow Fencer** | Thin bark-and-bone duelist leans away from a threatened swing, then commits to a short counterstep. Its retreat is physical and finite, not arbitrary invulnerability. | **4 / 2**; attack-reactive sidestep and counter are proposed tuning; do not replace existing heavy enemy. |
| Next · Crow | **Funeral Jackdaw** | Crooked perch silhouette lifts, readies, then sweeps through a clear lane. Ground shadow shows altitude; sword can hit when the real hitbox permits it. | **2 / 2**; source 16-update lift, 24 ready and 1.75 curved swoop are useful first timings. Needs intentional perches. Different from Quill Moth's sustained hunting. |
| Next · Bob-omb | **Fever Cask** | A leaking little cask staggers on root feet. First hit lights an obvious fuse; a second changes handling. Armed body, fuse and blast radius must have distinct cues. | **Lifecycle, not 255 ordinary HP**; walking contact **2**, proposed blast **4**. Carry/throw, ally damage and fuse handling need a separate safety pass. No surprise detonation on pickup. |
| Later · Puffstool | **Censer Puff** | A walking fungal censer swells before releasing one small, short-lived spore patch. Coating and exposed stalk read as different materials. | Proposed **4 / 2**. Source coating uses Gust Jar; a sword-accessible timed opening and optional candle stripping would be **new adaptations**, requiring real hooks. Never require the absent tool. |
| Later · Eyegore | **Pilgrim Eye** | A kneeling wooden pilgrim wakes one luminous eye, braces, then advances in straight steps. Only the open-eye pose accepts the intended precision hit. | Proposed **6 / 4**; source has special arrow/sword handlers. Use a sword-accessible opening, with arrows improving reach; do not claim original arrow-only behavior. |
| Later · Armos | **Root Saint** | A mossy shrine statue gives a slow crack-and-step wake-up, then advances with heavy, discrete footfalls. Open joints show recovery. | Proposed **10 / 4**; obvious wake tell and safe first encounter. Its base silhouette must distinguish sleeping enemy from a usable relic. |
| Later · Keaton | **Ragged Page** | An impertinent leaf-and-rag attendant feints sideways, then lunges along its facing. A missed lunge leaves the page tangled in its own hem. | Proposed **4 / 2**; finite commitment/recovery, sword-solvable. Distinct from the leech through one visible feint, not constant evasive running. |
| Later · Wizzrobe | **Lamenting Wick** | A hunched candle spirit folds into its snuffer, reappears with a visible wick and only then sends a narrow lane shot. | Proposed **8 / 4**, projectile **2**; one shot at a time in the first forest. Fire/ice/wind cousins belong in later-region briefs; teleport cannot appear on Bloom or beyond a required gate. |
| Later · Rupee Like / Like Like | **Velvet Purse** | A suspicious purse breathes before opening into a grabbing mouth. It imitates gilt imperfectly, with a tiny moving seam the attentive player can spot. | Proposed **8 / 2**; any stolen gilt is bounded and recoverable. Never steal keys, quest rewards or permanently remove equipment. Needs an explicit escape/recovery interaction. |
| Later · Gibdo (`GOBDO`) | **Candle Widow** | A wrapped, soot-stained figure lurches slowly; burning wraps reveals the faster Marrow Fencer underneath. The collapsing wrapper is a transformation, not an unexplained death. | Proposed **8 / 4** before transformation; sword remains a slower fallback. Source lantern contact really transforms Gibdo to Stalfos, but the current lamp needs an enemy-reaction hook. |
| Later · Moldorm | **Gilt Centipede** | A short chain of blackened seed husks turns broadly around the room; a pale rear segment marks the intended weak point. | Proposed shared **10 / 4**; tail-only vulnerability is a new choice. Budget every body segment and follow shared history; defer until ordinary single-body enemies are measured. |
| Later · Tektite | **Vesper Hopper** | A water-strider-like seed insect folds low, then makes a long, committed hop. A compact ground shadow makes the destination readable. | Source-derived HP **3 red / 6 blue**, contact **2**; exact leap and arrow interaction require implementation review. Lower priority because Pear Bladder already supplies hopping pressure. |

The same family need not occupy all nine future regions. Give each area a
small local cast and introduce one new rule at a time. Historical tier buckets
can inform weighted rarity and combinations; they must not become a rule that
all interesting mechanics disappear at low difficulty. Multi-form recolors do
not count as sixteen new behaviors.

The rest of the source roster stays recorded in the audit rather than being
silently discarded. Octorok, Keese/Pesto and ordinary slime variants overlap
existing shooter, flyer and hopper roles; study their decisions before adding
another lookalike encounter. Moblin/Darknut/ball-and-chain branches deserve a
later weapon-range and elite-budget pass. Segmented Madderpillar and Acro
Bandit groups follow only after whole-group costs are measured. Script-bound
boss parts and the documented unsafe bare-spawn exclusions are not candidates
for routine room generation. This is a prioritized prototype queue, not a
commitment to populate the first forest with the entire old roster.

## Art direction for the eventual sprite pass

Apply the existing [art bible](../art-reboot/ART_BIBLE.md) and
[reference application rules](../art-reboot/REFERENCE_APPLICATION.md), rather
than inventing another separate style:

- Draw at native sprite resolution and RGB555/palette limits. Start small
  bodies at 16×16; justify a padded 32×32 sprite for a tall or elite silhouette.
  Match the actual collision footprint and common foot baseline.
- Use broad, readable pixel clusters and horizontal body structure. One clear
  contour, one light-facing plane and one material accent do more work than
  scattered tiny highlights. The default floor remains quieter than actors.
- Filth belongs to the body: soft rot, black wood, torn cloth, swollen sap.
  Glory belongs to a deliberate focal point: a brass plate, wick, eye or gilt
  mouth. Match the current shared glitter density; do not undo its reduction
  by giving every new enemy a private particle cloud.
- Show preparation, commitment, impact/hurt, recovery and death as different
  body poses. A still body with one moving accessory will not sell weight.
  Complete directional silhouettes before adding ornament. North-facing
  counters and weapon coverage deserve their own review.
- A contact shadow must reflect real altitude and footing. A telegraph must
  correspond to a real delayed attack. Exposed flesh and protected armor must
  coincide with the collision rule, including the directional boundary.
- Enemy tells must not resemble arrows pointing to an exit, pickup sparkles,
  minimap symbols, lantern trails or item-gate icons. Glitter is an accent;
  timing and safety cannot depend on noticing a sparkle.

## Procedural encounters and performance admission

The lab is for testing a rule in isolation, then in mixed fights. It is not a
reason to add every family to all procedural rooms immediately.

1. **Place combat on navigable ground.** Use the player-reachable dry component
   and validate approaches, not just an empty tile. Reserve door arrivals,
   bridge chokepoints, ladders, chests, NPC interactions and required item-gate
   approaches. Choose Leever emergence outside those reserved cells and away
   from Bloom; the player can still deliberately step onto the announced mound
   during its warning. A buried living actor still counts toward room completion.
2. **Introduce combinations deliberately.** Start with one new enemy. Pair a
   leech with a stationary shooter only after its dodge lane is readable.
   Avoid a first encounter with armor blocking the only safe route while a
   burrower emerges behind Bloom. Two or three complementary families per
   room are more legible than an arbitrary sample of the whole bestiary.
3. **Preserve progression.** Required encounters must be solvable with current
   permanent capabilities and an empty ammunition pouch. Do not hide a last
   enemy behind an unopened item barrier. Spark/boomerang and Lakitu/Pacci
   dependencies are deferred because those tools are absent. Shield-only
   reversal encounters remain optional until the shield is guaranteed.
4. **Price the complete actor.** One Moldorm placement includes its segments;
   an Acro Bandit-like group includes every member. The old engine's dynamic
   graphics-slot `cost` is not the standalone engine's CPU, OAM or tile cost.
   Treat those as separate budgets, including projectiles and temporary art.
5. **Keep the update cheap without degrading behavior.** Use fixed-point state
   timers, bounded collision queries, shared art/palettes and one body sprite
   for the initial small prototypes. Reuse body poses for tells when possible.
   Avoid per-enemy room scans and separate actors for decorative wisps. Do not
   obtain speed by skipping combat updates, hiding enemies or reducing the
   player's established animation and mechanics.
6. **Measure new combinations.** Existing performance improvements do not
   certify a new AI family. Exercise small and high-density mixed rooms on
   healthy/blighted terrain, with water, lighting, arrows, bombs and item use.
   Record cycles/frame and missed frames from actual GBA execution; separately
   inspect armor-angle, wall, terrain-transition and clear-room correctness.
   Current lab support is evidence of a prototype, not a claim that every
   sixteen-family combination already holds the frame budget.

## What to judge in the first review

- **Gilt Leech:** does the body make the locked lane and start time obvious,
  and is a perpendicular dodge rewarded consistently?
- **Root Maw:** can the mound be recognized on both healthy and blighted grass,
  without being mistaken for a hole or treasure? Does emergence give enough
  notice, and is the exposed interval worth pursuing?
- **Reliquary Snout:** can front protection and the accepted side/rear region
  be predicted in all four directions? Does recovery allow a satisfying flank
  with the selected sword, rather than a fight against rapid enemy turning?

Review the rule, timing and counter first. The three native lab sprites are
mechanics placeholders; a selected creature can then receive its full
walk/prepare/attack/hurt/recover/death suite using the unified art direction.
