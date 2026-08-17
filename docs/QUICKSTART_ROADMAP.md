# QUICKSTART Roadmap

Streamlined for the forward-direction reassessment (Aug 2026). This
document is forward-looking only: it holds the vision, the outstanding
work, and the open problems. Everything already shipped - the completed
feature log, the architecture reference, the resolved-bug writeups - is
stashed verbatim in `docs/QUICKSTART_ARCHIVE.md` (code comments citing
"roadmap sec N" refer to the numbering there). Measured room data lives in
`docs/QUICKSTART_ROOM_SURVEY.md`, budgets in `docs/QUICKSTART_BUDGET.md`,
the reusable-content catalog in `docs/QUICKSTART_VANILLA_INVENTORY.md`.

## 1. Vision and direction

**The game.** A roguelite inside the vanilla Minish Cap world. Each run:
an item-selection phase in the hub, then out into the overworld to
explore, power up, and find the run's objective; heavy randomization
around a small mandatory spine; lots of optional ? events.

**The meta loop is the game.** Early save-file: limited item variety,
limited regions, limited ? event kinds, capped difficulty - room to learn
the vocabulary. Aggregated score across runs crosses benchmarks that
unlock new items, powerups, event kinds, quests, and regions. Wins raise
difficulty and deepen the run.

**Kinstones are the key economy.** Enemies drop pieces; fusing at a gated
door opens a new ? room for the rest of the run. Always-open doors keep
some events reachable regardless. The economy tightens as difficulty
rises: abundant early, grind-worthy later.

**The overworld keeps its vanilla layout**; the randomization lives
behind the doors - which room a door leads to and what happens inside it.
Same map every run, different world behind it.

**Where the build stands, in one line:** the run loop (hub, free-roam
seven-region ring, endless waves, bosses, Earth Element hunt, win/reset),
the kinstone economy, three ? room systems with nine event kinds, the
shop, quests, thirteen charms/curses, the map and compass, the hub inn's
rest, and a six-tier enemy roster driving composition-built waves are live
and probe-verified; what follows is what is NOT yet built.

**Shipped since the last roadmap pass (Aug 2026), for orientation:** F10's
MAP and COMPASS; the hub inn's REST half; D2's persistent living-enemy
count; the switch-puzzle repair (placement off the doorway, and the
sprite-less lever replaced with a real crystal switch); the difficulty
rework (size-normalized escalation, per-family live caps, a GFX sheet
budget in place of the kind cap, ten composition archetypes, a retuned
curve); and the roster expansion to six tiers - 57 of the game's 102 enemy
ids, an Elites tier that doubles as the miniboss pool, and weapon gating
for enemies a sword cannot kill. The reasoning behind the last two lives
in the Wave Composition Study artifact.

**High-level goals for the next phase, in priority terms:**

1. **Make the win condition worthy of the meta loop** - win-condition
   variety (F7) is the single biggest missing piece of the vision, and it
   is blocked on the key-item reachability logic, which is therefore the
   most important unstarted design work in the project.
2. **Make the meta loop visible** - the player still cannot see the
   unlock progression the whole design hangs on (unlocks viewer). The
   navigation half of this goal is done: the MAP and COMPASS (F10)
   shipped, so a run can now be read off the pause screen.
3. **Content breadth as data entry** - the tables, checker, and budget
   docs exist precisely so new events, quests, and regions are rows plus
   surveys. Spend breadth effort only through that machinery.
4. **Depth before breadth stays the rule.** The ring stays at seven
   regions until a full playthrough is smooth. Every fix is a general
   mechanism, not a per-room special case.
5. **Measurement before allowlists.** Nothing spawns somewhere it has not
   been watched working; nothing is tuned without a probe.

## 2. Outstanding features

Ordered roughly by how much of the vision each unblocks.

### 2.1 Win-condition variety (F7) - PAUSED, and its prerequisite

The run's only win carrier is a region's wave clear. Wanted: the Element
can also hang on a boss, a quest, or a ? room. **Paused (user's call)
until the key-item reachability logic exists**: no event may carry the
win until the run can guarantee the player can reach it with the kit they
can actually obtain.

- **The prerequisite - key-item reachability logic.** Which items gate
  which content, and how a run proves "this goal is reachable" before
  hanging the Element on it. This is design work, not code, and it also
  unblocks the held switch puzzle (burning wick) and gated quest
  variants. Nothing else on this list moves the vision as much.
- **Banked design from the paused attempt** (reverted cleanly): a per-run
  2-bit carrier draw (wave/boss/quest/? room), each carrier restricting
  the element-region draw to regions where it can pay out; boss carrier
  forces the boss wave until beaten with a self-healing counter gate;
  quest carrier puts the Element in the pot quest's hidden pot; a global
  Element despawn refresh; per-carrier Ezlo final-hint variants. Every
  carrier must clear two bars: a "cannot stall the run" argument and a
  "provably reachable" argument.

### 2.2 The meta layer's missing surfaces

- **The unlock system is currently SWITCHED OFF** (user's call, Aug 2026:
  "all items/rooms/features should be available random options at all
  levels"). `QUICKSTART_UNLOCKS_ENABLED` is 0, so `QuickStartIsUnlocked`
  returns TRUE for everything; the rules table, the score and win counters
  and every call site are untouched, so turning it back on is one line.
  Note what this means for the vision: the meta loop's *content* gating is
  gone, and only the difficulty counter still varies with wins. Both items
  below are therefore paused rather than dropped.
- **Unlocks viewer (B4 / #52).** PAUSED with the system itself - there is
  nothing to view while everything is unlocked. Cheap path when it
  returns: a hub NPC that speaks `sQuickStartUnlockRules` as dialogue.
- **Unlock benchmark values.** PAUSED. The thresholds were always
  placeholder and were never tuned against real play (Decision 2), which
  is part of why switching the system off costs so little today.

### 2.3 Quests

- **Scavenger hunt's other two hide modes (F1).** Carrier mode (the
  Keaton chase) shipped; buried (Mole Mitts) and under-bush modes remain.
  Both need per-region tile surveys (diggable spots, cuttable bushes)
  before they can be drawn safely; the quest's mode field and state
  machine are ready. The dig research is shared with the Mole Mitts dig
  rooms below - do them together.
- **Difficulty-scaled failure stakes (F1c).** Failing a quest should
  start to HURT as difficulty climbs: rupees at mid, health/buff at high,
  item loss at top tiers. One shared `QuickStartApplyFailureStake()`
  serving every timed-or-conditioned goal. Two rules carried from the
  curse work: stakes are announced in the offer text, and the failure
  text says what was taken. The scavenger hunt's FAILED branch is the
  pilot site.
- **Hide-and-seek stealth quest (F2).** Research-first: does vanilla's
  guard line-of-sight AI transplant outside its scripted rooms? If yes,
  guards on patrol rows from a table gate a prize; if no, fake it with
  ZELDA-kind patrol NPCs and our own cone check. Park the research
  question early; schedule the build only once answered.

### 2.4 Events and puzzles

- **Switch puzzles 3-6** (pilot order agreed with the user; 1 and 2
  shipped): *hold everything down* (pressure plates + thrown weights),
  *watch the eyes* (blink sequence, wrong order resets, F1c stake at high
  difficulty), *the burning wick* (HELD until key-item logic - fire-gated
  by design), *overworld switch links* (a plate in one ring region opens
  a grate in another; ambitious, gives the compass something to point at).
- **Phase D cheap events** (one mechanism each, all proven parts): switch
  rooms, bombable-wall treasure, pot-room variants, boss-rush,
  survive-N-seconds. Recommendation stands: survive-N-seconds first -
  smallest diff, reuses the hunt timer + wave spawner verbatim (Decision 4
  picks the pilot). One constraint any switch-driven event inherits:
  build it on LIGHTABLE_SWITCH, never HITTABLE_LEVER - the lever has no
  sprite at all and paints its art as room tiles, so it only renders in
  dungeon tilesets (see doctrine 6).
- **Phase D medium events**: kill-quota bounties (counters exist; needs a
  giver NPC), carry-item-to-NPC (open question: do held objects survive a
  room transition? if not, keep giver and receiver in one region), Great
  Fairy fountain gamble, Mole Mitts dig rooms, more Minish-layer sites.

### 2.4b Wave composition - what is left after the Aug 2026 rework

The escalation clock, per-kind live caps, the sheet budget, the archetype
builder and the retuned curve all shipped together; the study behind them
is the Wave Composition Study artifact. What it identified and did NOT
build:

- **Themed draws.** Occasionally pick a theme (fire, ice, undead, bug,
  aviary) and prefer roster entries carrying it, so a wave sometimes reads
  as a designed encounter rather than a mix. Needs a theme tag per row;
  the roles bitmask already has room beside it. The roster now has the
  material for it: a fire theme could field Fireball Guy, its mini
  variant, the fire Wizzrobe and Bombarossa.
- **Weapon-gated enemies are a mechanic worth using on purpose.** Spark
  (boomerang) and Lakitu (Cane of Pacci) currently only appear once the
  player holds their answer, which keeps waves clearable. The same field
  could gate a whole encounter behind a tool as a reward for having found
  it - but note the reverse risk: it makes those enemies invisible on runs
  that never draw the item, so it is a rationing tool, not a difficulty one.
- **Grow the Elite roster.** Seven entries, four of them Darknut forms.
  Wall Master would fit thematically if its warp destination were ever
  defined for our rooms, and Octorok Boss could serve if the entity cost
  of its macro were acceptable in a cleared room.
- **Elite points.** The study proposed a per-difficulty allowance pricing
  heavies against each other (Darknut 3, Wizzrobe 2, ...). Shipped instead
  as per-family live caps, which covers the reported problem more simply.
  Revisit only if heavies need to trade off against EACH OTHER rather than
  each having its own ceiling.
- **Per-region sheet budgets.** `QUICKSTART_WAVE_SHEET_BUDGET` is one
  global number (12). The tightest rooms at difficulty 12 have less
  headroom than the roomy ones, so a per-region override is the obvious
  next tuning knob if the budget ever proves too generous somewhere.
- **Archetype tuning by measurement.** Weights were chosen by judgement,
  not measured play. Once a full run is played at the new curve, revisit
  which shapes appear too often or too rarely.

### 2.5 Bosses

- **Multi-boss and boss+wave combos (F6).** Measured: two bosses fit a
  cleared room, three are marginal, none fit a live diff-12 wave. Blocked
  on **family-scoping the boss death machinery (#125)** - a simultaneous
  dual kill currently softlocks (one-family-per-room assumptions in the
  staged death and the death sweeps). Escort-roster combos ship as a
  per-boss field once measured (blue chuchu + ice wizzrobes is the
  thematic shortlist head).
- **New boss forms.** Octorok Boss is the next-cheapest per the vanilla
  inventory's boss ladder. Gleerok/Mazaal/Big Octorok each need a damage
  audit, an arena audit (Mazaal is a multi-entity macro and wants a
  dedicated room), and a budget measurement. None are "just spawn it" -
  the blue chuchu, the cheapest case, surfaced three latent bugs.
- **Boss spawns for the paused regions.** The allowlist is
  vetted-regions-only (CG, NHF, SHF, Trilby's pocket arena). Path per
  region: measure with the F6 harness, watch one full fight in the
  emulator, then add the row. EH-North and Lon Lon Ranch are the
  plausible next candidates; the small seam-scroll rooms stay boss-free.
- **Boss cadence sanity check.** The deferred-spawn fix made the 10% roll
  real for the first time; mid-region bosses were previously ~never.
  After some play, reassess whether 10% + deferral FEELS right (Decision 6).

### 2.6 Economy and items

- **Kinstone drop curve (C4).** Both rate cuts so far are flat
  placeholders. The probe to build: play N seeds' worth of waves with the
  real droptable, count pieces by shape, measure stall risk (every gate
  shape maps to exactly one piece id, so a run can in principle stall on
  one unlucky shape). Then set the curve so expected pieces cover ~60-70%
  of a region's gates per run. Kinstone specificity model is Decision 3.
- **Sword upgrades in the pools - the level-2 sword is IN** (uncommon
  weapons/tools, per the user, Aug 2026). Equipment has no ground-item
  form, so it reaches the player through `QuickStartSpawnRewardEntity`'s
  direct-grant path (GiveItem + message) instead of as something lying on
  the floor; `QuickStartItemNeedsDirectGrant` is the one place to add the
  Green/Blue/Four Sword when they are wanted too. Only the main item-drop
  site is wired through that helper so far - the other reward spawn sites
  still call `CreateObject(GROUND_ITEM, ...)` directly and would pay
  nothing if they ever drew a no-floor-form item. Routing the rest through
  the helper is the tidy-up.
- **Last unused charm idea (F4).** Rare-reward-chance-up is the only
  item from the original wish list not implemented (boss-chance-up was
  deliberately rejected). Framework is ready; one bit, one read.
- **Chest item control - choose and change what any chest holds (per the
  user, a feature to implement; research DONE).** Every chest kind is
  controllable. Small chests (SPECIAL_CHEST): contents come from the
  per-room `gSmallChests` RAM table (8 rows: tile, item, subtype,
  opened-flag) - inject a row and spawn the chest, which is exactly what
  the shipped chest lottery already does; a vanilla small chest's
  contents can be overwritten by rewriting its row after room load. Big
  chests (CHEST_SPAWNER, including every kinstone-fusion-revealed
  chest): the open handler (`sub_08084074`, chestSpawner.c) resolves the
  item from a BIG_CHEST tile-entity row in ROM room data matched by
  local flag - one QUICKSTART override table consulted there puts any
  fusion chest's contents under our control, and spawning a fresh
  always-open big chest is CHEST_SPAWNER type 4 plus an override row.
  The build: the override table + hook, an injection/overwrite helper
  the reward systems can call (tier-table draws included, so a chest can
  hold a rolled prize), and one probe check that CreateItemEntity-granted
  equipment (swords) survives the chest path. First clients once built:
  the fusion chests' payouts, the inn's two reward chests, and the
  chest-lottery prize finally living IN its chest.

### 2.7 The hub

- **The inn's two chests (Floor 2).** The REST half shipped (Aug 2026):
  three beds at 50/200/500 rupees healing 25%/50%/100% (min 1 heart / 2
  hearts / full), a two-step R interaction that quotes the price first.
  What remains is the chest half of the spec - the two chest props
  between the alcoves holding a COMMON and an UNCOMMON reward - which
  now rides the answered chest research above (inject two `gSmallChests`
  rows + spawn two SPECIAL_CHESTs, the chest lottery's own proven
  recipe).
- **Hint pool drawn per run (F5).** Six fixed hint spots today; wanted: a
  pool much larger than the spot count, drawn per run without
  replacement, so every run teaches something. Content should lean on
  what tests keep proving players miss: quest rules, the kinstone
  economy, charm gambles, the distance-2 element rule.

### 2.8 World structure

- **2-door pool door rewiring.** All 40 doors (20 rooms x 2) still
  retarget to one destination and one landing spot, so B->A travel is
  impossible and entry teleports to mid-room. Surveyed and planned in
  `docs/QUICKSTART_2DOOR_MAP.md`; the remaining work is mechanical
  retargeting plus a checker tier that walks both directions of every
  pair. An afternoon of data entry that removes a player-visible wart.
- **Regions beyond the ring (E).** Castor Wilds / Royal Valley each mean:
  un-block a border, extend the ring-room test, survey, add fusers,
  re-run ring.py + the checker. The adjacency map and distance-2 element
  rule absorb new regions as one enum row plus edges. Routine now - a
  breadth call, not an engineering risk.
- **The Minish layer as a parallel network (#102).** Blocked behind #103
  (transform rendering + the NHF vine, in Bugs below). After that, Minish
  rooms are ordinary content sites.
- **Difficulty option research (#51).** An options-menu entry writing a
  save field is small; the real question is design: does difficulty still
  auto-escalate on wins if the player can also set it? (Decision 5.)

## 3. Known bugs and issues

Open defects and unexplained reports, roughly by player impact.

- **Item-drop ? rooms "never pay" (user report, PARTLY EXPLAINED).** The
  reward audit (Aug 2026) found and fixed the draw bug behind the related
  "never seen a pastry" report: the pick index was `seed / 10` on a 6-bit
  seed, so it only ever spanned 0..6 and no tier could reach past its
  seventh usable entry. That made all 13 charms, and the late rare
  entries, unreachable for every seed in every room. Now spread across the
  whole list. Whether it also explains "never pay" is untested - the items
  themselves demonstrably spawn AND grant (a 34-item sweep confirmed every
  reward, charm included, spawns as a floor item and is collectable), so
  what remains is the live-play question: walk in through the real door and
  watch the item's entity lifetime, plus one playtest asking whether a
  floor heart piece simply doesn't read as a payout. Cheap insurance
  regardless: give item-drop sites the sparkle effect the hub's selection
  items use.
- **Boss death machinery is not family-scoped (#125).** Two bosses dying
  simultaneously softlocks. Latent today (one boss at a time), but it is
  the hard blocker for F6 multi-boss and a real crash risk if any future
  content double-spawns.
- **Some Minish holes/entrances don't work (#103, narrowed - user, Aug
  2026).** The transform RENDERING works fine now and the Minish world is
  broadly incorporated; what remains is that not every hole/entrance
  functions. The user is collecting a list of the non-working entrances
  and will report them; fix them as they land, then the Minish-layer
  survey (#102) can finish.
- **Trilby's NW enemy offset (120,24) sits in an isolated pocket**; **Lon
  Lon Ranch's top-middle pocket is unfenced** (no walked gating box yet -
  the user paused zone-gating pending their own walk). Both are data
  fixes waiting on the same harness.
- **The reachability harness (#81) is slow and crashes mgba** after
  enough reboots (worked around by process chunking, still slow). It
  gates the two items above; batch the fix with the next budget-harness
  work.
- **Enemies still outside the roster.** The Aug 2026 expansion probed and
  admitted 16 new kinds, taking the tiers from 41 to 57 of the game's 102
  enemy ids. What is still out, and why: the Vaati/Mazaal/Gleerok/Gyorg
  macros and Octorok Boss (multi-entity set pieces - Octorok Boss probed
  at 10+ entities per placement and is lantern-only), Wall Master (warps
  the player to a dungeon entrance our rooms do not define), the trap and
  furniture kinds, and Flying Skull (health 255 with no death arm found in
  its handler - excluded until someone can show what kills it). Anything
  admitted from here should clear the same two gates: the spawn probe
  (`enemy_spawn_probe.py` pattern) and the killability read.
- **First run on a brand-new save is fixed** (nothing has happened yet to
  vary the seed). Accepted as fine; noted so nobody rediscovers it as a
  bug.

## 4. Vanilla behaviors not yet addressed

Vanilla machinery that still pokes through the mode, needing a decision
or a sweep.

- **Scripted vanilla populations can still appear outside Eastern
  Hills.** Story/kinstone flags a run sets can conjure vanilla NPCs at
  their scripted spots (the EH farm crew walling the stairs was this;
  those three rooms now sweep per-frame). The same class could surface in
  any other ring room - Western Wood and SHF have story spawns too.
  Consider generalizing the EH sweep to every ring region (it already
  spares our ZELDA-kind NPCs) rather than waiting for the next report.
- **Vanilla ground pickups survive in ring regions.** Lon Lon Ranch still
  ships its NE heart piece and a red rupee from vanilla room data (found
  during the four-fix verification). Free loot outside the mode's reward
  economy - decide: sweep them, or accept them as flavor.
- **Lon Lon Ranch's Minish geography is half-wired.** The ranch house's
  two MINISH_SIZED_ENTRANCE doors lead into rooms that are already
  content sites (a second route in, harmless). But the central "long
  hallway" the player expects after shrinking has NO entrance object in
  the room data - where vanilla puts it is still unfound - and the old
  "check Lon Lon's extra link" note (#49) folds into this same survey.
- **Inactive Minish hole, NHF's east edge.** Does nothing when
  approached. Likely an unwired MINISH_SIZED_ENTRANCE or a portal whose
  destination was never containment-blessed; fold into the #102 survey
  once #103 unblocks it.
- **The beanstalk fusions stay excluded** (KINSTONE_2E, KINSTONE_24).
  Their payoff is climbing out of the ring to cloud rooms containment
  cancels; a fusion that grows an unusable ladder reads as a bug. Only
  revisit if cloud rooms ever become content (a new pocket type).
- **The shadowed cellar renders dark** (a checker WARN since the first
  full run). Vanilla's lighting, our content. Decide: exempt it, light
  it, or retire the site (Decision 7).

## 5. Everything else

**Open content decisions** (calls for the user, not engineering):

1. Element theming - which element belongs to which region, and does the
   start region carry one? (Feeds F7's carrier design.)
2. Unlock benchmark values - tune from real playthrough scores.
3. Kinstone specificity - exact-piece vs color-tier matching, and
   pieces-per-region counts. (Feeds the C4 curve probe.)
4. Which Phase D cheap event to prototype first (recommendation:
   survive-N-seconds).
5. Difficulty option semantics - if the player can set difficulty, does
   it still auto-escalate on wins?
6. Boss cadence - after play, does 10% + deferred spawn feel right?
7. The shadowed cellar - exempt, relight, or retire.

**Suggested sequencing** (respects: vision-critical design first,
research that unblocks before the work it unblocks, measurement before
allowlists):

1. **The key-item reachability logic** - pure design work, unblocks F7
   (the vision's biggest gap) and two held puzzle/quest variants.
2. **Unlocks-viewer NPC** - the meta loop's last invisible surface now
   that F10 has shipped; small, independent, and cheap as dialogue.
3. **#125 family-scoping + the F6 measurement pass** - turns the boss
   roster from "one chuchu" into a system; also retires a crash risk.
4. **F1's remaining hide modes + dig-room research** (shared survey),
   then **F1c stakes** piloted on the chase.
5. **F7 itself**, once 1 and 4 give it carriers worth drawing.
6. Structural debts on their own clock: 2-door rewiring (any afternoon),
   the inn (waits on its chest probe), C4 curve (waits on its probe),
   Minish layer (waits on #103).

**Testing doctrine** (unchanged, condensed):

1. Tables are the game; the invariant checker validates the tables -
   run it after every build that touches placement data.
2. Runtime self-correction (snap-to-open-ground, rescue failsafes) stays
   on as the second line, so a bad row degrades instead of breaking.
3. Measured docs are the source of truth for placement; guessed
   coordinates don't go into tables.
4. Humans test feel, machines test truth - emulator probes verify state
   and transitions; seeded playtests judge fairness and fun.
5. The decomp's hard limits keep plans honest: 72 entities game-wide,
   the GFX sheet table is the wall (not RAM), no new .bss/.data in
   game.o, new logic over existing assets is cheap while new
   graphics/maps/AI are expensive - which is why the whole plan leans on
   recombination.
6. **Borrowed vanilla objects are only as portable as their art.** An
   object that paints its visual into the room's TILEMAP works only in
   tilesets that carry those tiles; one that carries an entity SPRITE
   renders anywhere. This has now bitten twice - the invisible painted
   shutter, then the lever that drew as garbage in every overworld ? room
   - so before reusing a vanilla object outside its home rooms, check
   which of the two it is.
