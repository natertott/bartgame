# QUICKSTART Roadmap

> **New to this project? Read `docs/HANDOFF.md` first.** It and its three
> companions (`HANDOFF_GAME.md`, `HANDOFF_STATUS.md`, `HANDOFF_ISSUES.md`)
> summarise the game, the current state, the known traps and the working
> constraints. This roadmap is the authoritative long-form record - the
> handoff tells you which entry of it to read.


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
shop, quests, fourteen charms/curses, the map and compass, the hub inn's
rest, the hub trophy case browsing all 70 obtainable things, and a
six-tier enemy roster driving composition-built waves are live and
probe-verified; what follows is what is NOT yet built.

**Tooling note:** `emu.py`'s `snap()` now works against both mgba python
builds. The pip wheel (0.10.2) exposes `Image.save_png(file)` where a
source build exposes `to_pil()`, and every screenshot probe was failing on
the wheel until the helper learned both.

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
2. **Make the meta loop visible** - largely DONE now. The MAP and COMPASS
   (F10) shipped, so a run can be read off the pause screen, and the
   trophy case shipped, so the player can browse all 70 things this mode
   can give them and read what each one does. What is left is the
   entitlement half: while `QUICKSTART_UNLOCKS_ENABLED` is 0 the case
   shows what has been FOUND, not what has been unlocked.
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

### 2.0 The Fountain of Sacrifice (SHIPPED Aug 2026)

**Built as designed below, plus per-run rotation.** What shipped: the
graveyard Great Fairy chamber skips its site dispatch and runs the
sacrifice instead. A Zelda-sprite host at the fountain edge explains the
deal (custom strings 229-233). Eight items are strewn as liftable
`SHOP_ITEM` props on fixed pedestal spots; WHICH eight rotates per run -
the top 8 of the player's eligible inventory ranked by an avalanche hash
of (run_seed, item id), so two runs with near-identical seeds still get
different spreads (a plain xor hash measurably did not rotate - the
multiply-xorshift-multiply mix is load-bearing). Eligibility excludes all
swords, bottles, quest keys, and the Earth Element. Carrying a prop into
the summoning-circle box consumes it: inventory slot zeroed (equipped
slots included), the ItemForSale teardown mirrored, and the tier-scaled
return resolved on the spot - commons roll punish/nothing/common,
uncommons small-punish/uncommon/rare, rares always pay and can pay
double. Props the player puts down (outside the circle) respawn on their
pedestals via the same maintain loop the shop uses.

The original research record, kept for the design rationale:

The user's pitch: in a Great Fairy fountain room, the player's items lie
strewn across the floor; a sprite asks for a sacrifice; the player picks
one up and gives it to the fountain, loses it, and receives a tier-scaled
return - commons risk punishment or nothing, uncommons break even or
better, rares only ever pay out (up to two rares).

**Every part of it maps onto machinery this mode already ships, verified
by probe:**

- *Items strewn as carryable props*: `SHOP_ITEM` (ItemForSale) renders
  ANY item id as a liftable pedestal prop - the run's own shop spawns
  them dynamically (`QuickStartSpawnShopItem`) and the player lifts and
  carries them in play every day. Probed: three arbitrary item ids
  spawned and rendered as props inside the graveyard fairy chamber
  (scratchpad sacrifice_strew.png). Strewing the inventory = enumerate
  owned eligible items, spawn one prop each.
- *"Throw it into the fountain"*: ItemForSale has no throw arc (its drop
  snaps it home - sub_080819B4), so v1 should trigger on CARRY-INTO-THE
  -POOL-BOX: while `gPlayerEntity.carriedEntity` is one of our props and
  the player stands in the fountain-edge box, pressing the drop button
  consumes it - splash FX + SFX_WATER_SPLASH, delete prop, done. Reads
  as tossing it in, needs zero new engine mechanics. (A true pot-style
  throw arc means a new carry class or patching ItemForSale's drop path
  - possible, not worth v1.)
- *Losing the item*: SetInventoryValue(item, 0) - the F1c handicap
  system already strips and restores whole kits including button slots,
  so removal incl. the equipped-item edge is proven code.
- *Tier of the offering*: sQuickStartTiers carries every item's
  COMMON/UNCOMMON/RARE band - direct lookup, the same table the
  boomerang-shadowing check reads.
- *The returns*: QuickStartDrawAtTier for prizes (two rares = two calls,
  dropped at the player's feet like everything now); the F1c stake
  machinery already implements the punishments (rupee loss, heart loss,
  charm loss); heart-container loss is a stats.maxHealth write.
- *The asking sprite*: the proven talkable-NPC + TEXT_CUSTOM strings
  (merchant/sign machinery), not a live GREAT_FAIRY object (unverified
  AI).

**The two real constraints found:**

1. *GFX budget*: each unique strewn item costs a sprite sheet; a full
   20-item inventory will not fit the 44-slot table. Strew a curated
   draw of at most ~8-10 eligible items per visit (fairy rooms are
   otherwise empty, so that fits comfortably), or rotate per visit.
2. *Curation*: never strew the sword (an endless-wave run without one
   can brick), active quest keys, or the Earth Element. An ELIGIBLE
   predicate over the tier table's categories covers this.

**Suggested placement**: upgrade the existing QS_EVENT_FAIRY site kind -
the site-kind field is full at 8, and the plain two-heal-fairies payout
is the weakest event in the vocabulary; the fountain-sacrifice is a
strict upgrade for the same bit, and its extra byte can roll
"plain fairies vs sacrifice" per site if both should coexist.

### 2.1 Win-condition variety (F7) - SHIPPED (Aug 2026), carriers live

**The banked design is built.** Every run rolls a WIN CARRIER alongside
the element region - an even three-way draw from the run seed through the
avalanche mix (measured first with Random() % 3: over 18 pinned
sequential seeds it returned only {WAVE, QUEST}, alternating with seed
parity, and BOSS never landed once - the fountain's near-identical-seeds
lesson, again):

- **WAVE** - the classic, byte-for-byte: clear the element region's
  first wave and the Element drops at the reward spot.
- **BOSS** - the element region's wave loop deals a Chuchu Boss from its
  very first wave and keeps dealing one until it falls; the kill latches
  a per-run bit, feeds `gSave.boss_kills` (the score formula's feeder at
  last), fires the "It is freed!" hint, and the Element appears. The
  element-REGION draw is restricted at roll time to the boss allowlist
  (with an any-candidate pre-check so the roll can never spin on an empty
  distance-2 intersection - unsatisfiable falls back to WAVE). Beaten
  detection is a sighting-then-absence latch (room flag 45 + the corpse
  filter), guarded against quest population swaps.
- **QUEST** - the run's pot quest is forced to host in the element region
  and completing it (unfailable - the pot hunt has no clock) frees the
  Element. The completion hint tells the player where to look, because
  unlike a wave clear they may be far from the reward spot.

The final-region Ezlo hint names the actual trigger per carrier (strings
12/234/235). Both non-wave unlocks persist for the run once earned; the
boss deal self-heals through the existing owed/deferral machinery and
re-deals on every fresh visit until beaten. Both roadmap bars hold:
no carrier can stall the run, and every carrier's payout spot is the
region's own verified reward spot.

**What this deliberately does NOT yet include**: the ? room carrier (the
fourth of the banked design - it needs a per-site reachability argument
the key-item runtime will eventually provide), and the full route-bill
runtime (roll a route per run, price its kit) - the reachability MODEL
below stands ready for both.

The original prerequisite record:

- **The prerequisite - key-item reachability logic. THE MODEL NOW EXISTS**
  (user survey, Aug 2026), in `tools/quickstart/overworld_paths.py`. The
  user's framing is what unlocked it: *standing at one entrance of an
  overworld region, what does the player need to reach another entrance of
  the same region?* Everything else - which regions a run visits, where
  its win conditions sit, which key items it must therefore hand out -
  falls out of that.
  **Three tables.** PORTS+LINKS: where each region's entrances are and what
  is on the other side. Not invented - every port is a real
  `WARP_TYPE_BORDER` row in transitions.c or a real scroll seam between
  two AREA_HYRULE_FIELD rooms read out of `gAreaRoomHeaders`, and the
  user's compass naming lands on them exactly (their "ENE" is
  `TRANSITION_SHAPE_BORDER_EAST_NORTH`). All 19 ports of the four
  surveyed regions matched a real edge, with nothing left over.
  TRAVERSAL: the user's survey, entered verbatim, and DIRECTED - Lon Lon's
  ESE->WNW wants Roc's Cape while WNW->ESE takes Cape, Flippers or the
  Pacci Cane, and nothing in Trilby reaches its North exit at all.
  GATES: regions that cost an item to stand in whatever route you take
  (Royal Valley/Lantern, Lake Hylia/Flippers, Crenel/Grip Ring, Castor
  Wilds/Cape or Ladder).
  **Requirements are disjunctive normal form** - alternative terms, each a
  set of items all of which are needed. AND-ing multiplies out and drops
  superset terms, so a route's bill comes out as the shortest kits that
  actually work. A generated route reports its bill directly: three
  regions from Castle Garden costs nothing, or a sword, or Cape/Flippers,
  or bombs+sword; five regions converges on bombs+sword+Cape/Flippers.
  **What it found, and what shipped because of it.** The model showed that
  five NHF traversals - between them every route to the WNW port, which is
  the only door to Royal Valley - were priced in a level-3 blade the
  weapon ladder never reached: the tier table stopped at
  `ITEM_RED_SWORD`. Nothing about either table looks wrong on its own;
  side by side, a region falls off the map. **The Tempered Sword
  (`ITEM_BLUE_SWORD`) is now a RARE drop gated behind the White Sword**
  (`QS_REQ_RED_SWORD`), so the ladder can only be climbed upward - the run
  cannot deal the third rung first and then equip a downgrade over it.
  Every traversal in the survey is now walkable with a kit a run can
  assemble.
  Adding it meant a catalog row, and the catalog's name and description
  strings are indexed arithmetically off `gCustomStrings`, so the fourteen
  non-catalog strings above them moved up by two. The three sites that
  refer to those by literal number (the Tingle payout, `sQuickStartHintPool`,
  and the wind-crest sign script) moved with them, and all seven moved
  strings were read back out of the built ROM to confirm they resolve to
  the right text.
  **The survey is now complete but for two pairs** (EH `W->N`, WW `E->N`),
  after the user filled in NHF's WSW row, all of SHF, and one crossing each
  for Eastern Hills and Western Wood. Castle Garden costs nothing to
  cross; Castor Wilds is gated on Cape or Pegasus Boots (not a Ladder -
  that is not an item) and its SWS exit is open now that its Kinstone gate
  is being removed, though nothing yet records what lies on the other side
  of it.
  What is left to build once the table is complete: the runtime half - roll
  a route per run from the run seed, distribute the win conditions along
  it, and refuse to place one behind a bill the run cannot fill.
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
- ~~Unlocks viewer (B4 / #52)~~ **SHIPPED, as Carlov's trophy case** (the
  user's call, Aug 2026: repurpose the vanilla trophy case so the player
  can browse everything they have unlocked, with a description of what
  each thing DOES). What went in:
  - **A 70-row catalog** (`sQuickStartCatalog`, game.c) covering
    everything this mode can hand the player: the Earth Element, the
    ordinary pickups (hearts, three rupee sizes, bomb and arrow refills,
    Kinstone pieces, fairies), the nine reward-tier rewards, fifteen
    weapons and tools, nine key items, all eight sword skills, six stat
    upgrades, and all fourteen charms and curses. Grouped by category,
    because the vanilla list has no headings of its own and grouping IS
    the structure the player sees.
  - **A discovery ledger in `gSave.figurines`** - vanilla's 288-bit
    figurine bitset, which this mode never used (no Carlov, no lotto,
    `figurineCount` never leaves 0). That choice is what made the re-skin
    small: the menu's own ownership test is `ReadBit(gSave.figurines,
    idx)` and needed no change at all. On persistence, now PROVEN through
    a power cycle (`tools/quickstart/ledger_cycle.py`): set a ledger bit,
    call the game's own WriteSaveFile, hard-reset the core (EWRAM wiped,
    EEPROM kept), walk the boot flow again - the bit comes back, a
    neighbor byte stays 0, and the bit is verifiably absent between the
    reset and the reload, so it came from EEPROM rather than surviving
    RAM. The case can honestly be described as a permanent record, with
    the ordinary save-semantics caveat: a discovery reaches EEPROM at the
    NEXT save write (run start and the win path both call WriteSaveFile),
    so powering off mid-run loses discoveries made since the last one.
    No code path in the tree clears the array - the run wipe covers
    `gSave.inventory`, `gSave.kinstones` and named flag ranges only.
  - **Marking at the one chokepoint** - `GiveItem`, via the existing
    `QuickStartNoteFoodItem` hook, so ground pickups, chest payouts, hub
    selections and scripted gives all record themselves. The three bottle
    charms are marked separately in `QuickStartNoteCharm`, because a
    charm arrives as a filled BOTTLE and the id GiveItem sees is a
    bottle.
  - **The case itself is the vanilla object**, FIGURINE_DEVICE type 0,
    standing on Floor 3 at tile (3,3) - the west end of the spawn room's
    hall, clear of the sign, the item row and the arrival spot. It keeps
    its own "Check" prompt and its own MenuFadeIn(7, 0xff); only its
    SHOP07_TANA story gating had to be bypassed.
  - **Deferred: the picture pane.** It draws `gFigurines[idx]`, per-
    figurine art, which for an item catalog would show an arbitrary
    figurine per row - worse than nothing, so it is suppressed under
    QUICKSTART. The obvious follow-up is the item's own inventory icon
    (`DrawDirect` + `gSpriteAnimations_322`, as the pause menu does), but
    that sheet is not among the ones this screen loads and half the
    catalog - hearts, rupees, refills, skills - has no inventory icon at
    all.
  - **One real bug found and fixed on the way**: the case registers in
    the SHARED interaction candidate list once at init, because Carlov's
    back room has nothing else competing for a slot. The hub's spawn room
    does, and once the case lost its slot it was dead for the visit -
    checkable-looking and permanently silent. Measured: it opened on a
    clean boot and never again after a single ground-item pickup in the
    same room. It now re-arms whenever it finds itself off the list.
  - Note for whoever adds a catalog row: the name block, the description
    block and the table are three parallel lists indexed arithmetically.
    A compile-time check catches the pair running past the 256-entry
    `gCustomStrings` ceiling (the catalog uses 61-200 of it), but nothing
    can catch them falling out of order.
  - Still true: with `QUICKSTART_UNLOCKS_ENABLED` at 0 the case shows
    DISCOVERY, not entitlement - a row lights when the player has held
    the thing, which is what a trophy case has always meant. If the
    unlock system comes back, a second dimension (locked/unlocked vs
    found/not-found) is a design question to answer then.
- **Unlock benchmark values.** PAUSED. The thresholds were always
  placeholder and were never tuned against real play (Decision 2), which
  is part of why switching the system off costs so little today.

### 2.3 Quests

- ~~Scavenger hunt's other two hide modes (F1)~~ **SHIPPED, both.** The
  thief no longer always bolts from the giver: a third of hunts hide it
  under a BUSH (cut it out) and a third BURY it in soft earth (Mole
  Mitts), decided when the giver spawns in the host room - the roll
  happens wherever the player first walks, so the host's tiles are only
  scannable then. Hidden hunts start the clock with NOTHING released:
  35 seconds (vs the chase's 25) covering the search, the region's own
  wave still up ("searching under fire" is the mode's texture), and the
  pack - thief AND swarm - bursts out of the hide tile the moment it
  transforms. Never found = the same FAILED branch, F1c stake included.
  **The survey work turned into predicates, not tables.** A
  slash-everything diff over North Hyrule Field
  (solid-before/open-after is what separates a bush from trampled grass)
  identified tile types 427-431 (collision 0x0f) as THE cuttable-shrub
  class - present by the hundreds in every named region
  (`tools/quickstart/hide_survey.py`) - and diggable ground is simply
  `actTiles == TILE_ACT_DIG (0xd)`, which exists ONLY in the three
  Eastern Hills rooms, so buried is rare by geography on top of its Mole
  Mitts gate. The runtime picker ring-scans from the quest's own drawn
  spot for the nearest qualifying tile and degrades mode by mode down to
  the carrier chase, so no region needed a hand-built table and a region
  with no bushes simply never offers one.
  **Detection is the predicate itself**: the monitor re-tests the
  recorded tile each frame, and "no longer a bush / no longer diggable"
  IS the find - no new event plumbing, and a room reload correctly
  regrows an unfound hiding place. Verified end to end in the emulator
  (`tools/quickstart/hide_check.py`): bush mode rolls, hides at a real
  bush tile, Begin arms the search clock with no Keaton out,
  transforming the tile releases thief-plus-swarm there, the kill wins
  and pays, and the timeout control fails with the stake path; the
  buried leg does the same in Eastern Hills off a real 0xd tile with
  Mole Mitts granted. The sword's power to transform exactly these tile
  types is the diff probe's own already-proven half.
- ~~Quest clocks are too generous~~ **SHIPPED** (the user, Aug 2026: "the
  quests need to be more difficult in general"). The Keaton chase went
  60s -> 25s ("about half or less"); the hunt quest went 45s -> 30s AND
  4-8 enemies -> 7-13, which takes it from ~7 seconds per kill to ~2.3 at
  the top of the curve. Both offer texts quote the new number, and the
  pack ceiling is still inside the entity budget because the pack is one
  kind and the placer already stops at the GFX reserve. What is NOT tuned
  is what happens on a LOSS - that is F1c below, and it is the half that
  makes a tight clock mean something.
- ~~Difficulty-scaled failure stakes (F1c)~~ **SHIPPED**, on both timed
  quests at once (they share the clock, the mark bit and now the stake).
  The ladder: difficulty 0-3 free, 4-7 costs 50 rupees, 8-11 costs 100
  rupees and half your current hearts, 12 costs 200 rupees, half your
  hearts, and one held food charm - or, with no charm to take, a run-long
  curse goes on instead. Both announced rules hold: the giver scripts
  branch on `QuickStartStakeIs*` and show the tier's own stake line after
  the offer (strings 217-219), and `QuickStartApplyFailureStake()`
  returns the failure string for the strongest thing it actually took
  (220-223), so a broke player is never told they lost rupees they never
  had. The tier is LATCHED at quest start (the freed 75-76 hunt-slot
  bits) so a stake can't grow after it was announced. Taking a charm is
  the top tier's item loss on purpose: charms can never strand a run the
  way traversal items could, and the cleared inventory bit puts the charm
  back in the draw pool. Health never goes below two hearts, and a player
  at two hearts or less is spared the health hit entirely. Verified by
  calling the shipped functions in the ROM at all four tiers plus both
  edge cases (charmless tier 3 -> curse; low-health tier 2 -> spared) -
  six for six. The cage puzzle's timeout is the natural next caller.
  One build trap found: this libgcc has no `__umodsi3`, so an unsigned
  modulo is a LINK error - mask to 15 bits and use signed `%`.
- ~~Hide-and-seek stealth quest (F2)~~ **SHIPPED, as "the watch".** A
  giver posts a line of watchmen across their region and asks the player to
  reach their partner on the far side without being seen. 40 seconds; get
  there and the partner pays a RARE draw at the player's feet; get caught
  in a cone, or run out of clock, and the shared F1c stake applies. It is
  the fourth quest sibling and the first that is not a fight - the region's
  own wave is suspended for the duration (`QuickStartQuestSwapActive`),
  because sneaking past sentries while a wave chases you is a fight with
  extra steps.

  **The watchmen do not walk, they TURN**, and that is a deliberate
  departure from the brief below. Sweeping sentries beat patrolling ones on
  three counts, and the third decided it: a facing is *readable* on a GBA
  screen where a moving cone is not; a stationary sentry cannot walk into a
  wall, off a ledge or into an arena's one-tile neck, none of which the
  region offset tables were surveyed to guarantee; and a sweep needs **no
  per-entity state at all**. game.o gets no .data/.bss, so there is nowhere
  to keep a patrol cursor - but a facing that is a pure function of the
  frame counter and the sentry's own fixed tile needs no storage, and is
  therefore exactly reload-safe: leave the region and come back and every
  sentry resumes the facing it would have had, because nothing was stored
  to go stale. Identity is position, like the fusers and the other two
  givers.

  Everything - giver, watchmen, partner - is the ZELDA npc kind, so the
  whole quest costs **one gfx sheet**. State is bank 11 offsets 143-156,
  the run the extension slots gave back when they moved into the QUICKSTART
  window, and the host is a plain five-bit field because the block was
  allocated after the pool passed sixteen rows.

  Verified end to end in the emulator
  (`tools/quickstart/stealth_check.py`), four legs: the giver spawns in the
  drawn host region; Begin places the line and the partner with a live
  `GUARD_LINE_OF_SIGHT` emitter parented to each watchman; the sentries
  sweep through all four facings over 420 frames; and both endings fire -
  standing in a cone flips the quest FAILED, standing with the partner
  flips it WON. The research record that made it cheap:

- **F2 research. ANSWERED: YES, it transplants** - and to exactly the entity kind the fake would have
  used. Vanilla's guard sight is not AI in the guard at all: it is a
  self-contained projectile pair (`GUARD_LINE_OF_SIGHT`, projectile 12).
  An invisible emitter rides its parent's position and, while the parent
  is on screen, fires a short-lived invisible ray every 4 ticks in the
  parent's `knockbackDirection` (with a small angular jitter); rays die
  on wall tiles - real occlusion - and a ray touching the player writes
  `parent->type = 0xff`. That byte IS the "spotted!" signal; everything
  else in the vanilla sneak rooms is scripted response.
  Verified live (`tools/quickstart/los_check.py`): attached to a plain
  ZELDA npc - the same kind every quest giver already is - in an
  ordinary room, the player is spotted standing in the facing line and
  NOT spotted standing behind, and the effective sight range brackets
  between 60 and 70px (call it four tiles), which is vanilla's own
  close-quarters sneaking feel. Two wiring notes for the build: the
  parent must have a real `collisionLayer` (offset 0x38 - probes that
  write 0x1d are setting gustJarTolerance and measuring nothing), and
  the emitter needs `parent` plus `subtimer=60` set at spawn, exactly as
  guard.c does. The build is now: patrol rows from a table (walk the
  NPC, keep knockbackDirection = walk direction), the emitter attached,
  and the quest monitor polling the patroller's type byte for 0xff.

### 2.4 Events and puzzles

- ~~The switch puzzle's window is trivial, and switches spawn under the
  cage pots~~ **SHIPPED** (both halves of a user report, Aug 2026). The
  window is no longer a flat 8-seconds-falling-to-4: it is priced in
  TILES OF TRAVEL from the switch that was pulled to the cage, measured
  against Link's real walking speed (1.20 px/frame, ~14 frames per tile -
  `walkspeed.py`), times a per-tile allowance that tightens from 22
  frames at difficulty 0 to 15 at difficulty 12. Measured over 24 forced
  deals: slack runs 1.55x-1.91x a straight walk at difficulty 0 and
  1.05x-1.30x at difficulty 12, where the old window was 3-8x whatever
  the deal happened to require. The decoy variant, which used to open the
  cage permanently on a correct guess, now runs the same clock at DOUBLE
  length - its pull is one-shot, so a lapse there cannot be re-pulled.
  The placement half: switches are dealt at least 5 tiles from the cage
  (relaxing to a hard floor of 2 in rooms too cramped for it), the cage
  ring now refuses to spawn a pot on a switch tile, and the switch search
  clamps to the outer-3 door band rather than the cage's 5.5-tile margin -
  that margin is sized for a 3x3 ring and was collapsing every small cave
  onto the 2-tile floor. Same 24 deals: zero buried switches.
- **Switch puzzles 3-6** (pilot order agreed with the user; 1 and 2
  shipped): ~~*hold everything down*~~ **#3 SHIPPED as the LINGER
  PLATES**, the third deal of the switch site's per-visit roll (an even
  three-way now: gate / decoy / plates). Two pressure plates, one dealt
  ahead of the player and one across the cage; both must be down AT
  ONCE, and a plate stays down 300 frames (tightening 12/difficulty
  step) after the player steps off - the linger IS the clock, and the
  sprint between the plates crosses the prize. One honest deviation from
  the sketch: "thrown weights" died on contact with vanilla - a thrown
  pot SHATTERS, and the only vanilla plate-weights are pushable statues,
  which can wedge irreversibly in a dealt room - so the simultaneity
  pressure moved into the linger instead, and nothing in the puzzle can
  soft-lock (a short deal in a cramped room degrades the same way every
  cage does: trap pots are liftable). Built as a type2-gated variant
  inside vanilla's own pressurePlate.c - type2 = linger>>4, vanilla
  plates (type2 0) untouched - with the same room-flag plumbing the
  switches use (bits 104-105). Verified end to end in the emulator
  (tools/quickstart/plates_check.py): the deal renders (PRESSURE_PLATE
  is a real entity sprite - doctrine 6 satisfied, screenshot taken),
  stepping on presses, both-down opens the cage, and the control run
  that waits out the linger finds the cage still shut. Two probe traps
  reconfirmed on the way: an open textbox makes PlayerCanBeMoved()
  false, so IsCollidingPlayer refuses a player standing squarely ON the
  plate - dismiss hints before measuring; and in a SMALL room the
  mirrored anchor clamps onto the first one, dealing the plates adjacent
  (trivial but survivable - larger rooms spread them).
  ~~*watch the eyes*~~ **#4 SHIPPED as the BLINK SEQUENCE**, the fourth
  deal of the site's per-visit roll (now an even four-way). Three switches
  blink one after another; repeat the order to open the cage; a wrong press
  darkens everything and starts over, and at difficulty 8+ it also costs
  the F1c stake, once per visit.

  **The display and the input share one channel, and that is the whole
  design.** A LIGHTABLE_SWITCH's frameIndex is mirrored from its flag every
  frame (`sub_0809EABC`, called from Action1), so writing the flag from C
  *lights the switch* - the blink comes free, with no new object and no new
  sprite, which matters because doctrine 6 says a fixture that is not a
  real entity sprite will not render in overworld tilesets. But the
  player's hit toggles that same flag. So the loop is split and only one
  side owns the flags at a time: 192 frames of SHOW (three 48-frame blinks
  plus a dark beat) where the game writes them and progress is pinned at
  zero, then 432 frames of INPUT where the player does.

  The clock is `gRoomTransition.frameCount`, which free-runs and is never
  reset, so the sequence **loops forever** rather than playing once. That
  is deliberate and it is also forced: there is nowhere to store a "the
  show started at frame N" timestamp - game.o gets no .data/.bss and the
  site's own eight-flag window is full - and a looping show is kinder
  anyway. Running out of the input window mid-sequence resets progress,
  which is the pressure.

  Two pieces of storage came from noticing something was already there.
  The **variant** is two bits, not two booleans: `flagBase + 1` (decoy) and
  `flagBase + 7` (plates) had a fourth combination that was simply never
  dealt, so a fourth puzzle needed no new room flag. The **puzzle's own
  state** (drawn permutation, progress, stake-taken) went to room flags
  108-113, above the four switch/plate toggle bits - `gRoomVars.flags` has
  416 bits against an origin of 256, so that is free room rather than a
  squeeze. A room that cannot hold three switches degrades to the
  single-switch gate, the same way the linger plates already do.

  Still open: *the burning wick* (HELD until key-item logic - fire-gated by
  design), *overworld switch links* (a plate in one named region opens a
  grate in another; ambitious, gives the compass something to point at).
- **Phase D cheap events** - ~~survive-N-seconds~~ **SHIPPED** as the
  pilot, exactly as recommended (smallest diff, reuses the wave spawner
  and the quests' HUD clock). It shares QS_EVENT_WAVES' kind value the way
  the two switch puzzles share QS_EVENT_GATE's: one combat-room visit in
  three deals "stand your ground" instead of the 3-wave gauntlet, decided
  per visit (the room state is per-visit anyway). The clock is 20s + 1s
  per difficulty point - it scales UP because the pressure does: the
  spawner re-runs whenever the room thins below three live enemies, capped
  by the same global 28-enemy budget as everything else. Win = the clock,
  not the body count; the survivors scatter and the prize drops from the
  same QS_CAT_DROP pool a chest pays. Three sharp edges handled: the
  variant is never dealt while a timed quest owns the shared clock; a
  seam crossing (Grimblade) resumes the live attempt rather than
  re-flipping it; and an abandoned attempt's clock is swept by the ring
  monitor the moment the player is seen back in a region room (one
  documented cosmetic leak: warping straight home freezes the HUD clock
  until the next region visit). Verified in the emulator end to end: deal
  rate, ticking, enemy spawns, the win branch clearing the room and
  dropping the prize, and the abandon sweep.
  Still open from the same list: switch rooms, bombable-wall treasure,
  pot-room variants, boss-rush. One constraint any switch-driven event
  inherits: build it on LIGHTABLE_SWITCH, never HITTABLE_LEVER - the
  lever has no sprite at all and paints its art as room tiles, so it only
  renders in dungeon tilesets (see doctrine 6).
- ~~Tingle's kinstone events~~ **SHIPPED** (the user, Aug 2026: "Tingle
  should be there and the player can fuse Kinstones with them. If they
  fuse correctly, they should receive a heart container"). Built on the
  fuser machinery rather than as a new system - a Tingle is a fuser with
  a different sprite and our own payout, so it scatters over the same
  per-region spot list, uses the same script and hitbox, and retires the
  same way once fused. Standing in Trilby Highlands, so the region that
  gained a dig-cave event also gained a reason to walk it.
  - **Which fusion is the design.** KINSTONE_2A, whose vanilla world
    event adds another Goron to the line in Goron Cave's main chamber -
    a content-site room whose vanilla occupants are swept every frame.
    The fusion's own payload is therefore inert here, which is what a
    fusion should be when the reward is ours to give. This mode listed
    2A as an ordinary fuser once and dropped it for being pointless;
    pointless is the property being reused.
  - The sprite is the real `TINGLE_SIBLINGS`, whose definition carries
    four forms each with a genuine entity sprite. `StartCutscene` sets
    ENT_SCRIPTED, which routes its update down the same scripted branch
    the ZELDA fusers take, so none of its vanilla talking logic gets a
    say.
  - Verified: Tingle stands at Trilby local (40,584); forcing the fusion
    latches the payout bit and drops a Heart Container at (40,612).
  - Open, if more Tingles are wanted: only four `GF_TINGLE_PAID_BIT`
    slots exist, and each new one needs a fusion whose vanilla payload is
    equally inert - that search is the work, not the wiring.
- **Mole Mitts dig caves as ? event sites - the first one SHIPPED, and
  the recipe for the rest** (the user, Aug 2026: "convert this mole mitts
  cave to a ? event... a general way of implementing ? events in mole
  mitt caves as we add more overworld regions"). A dig cave turns out to
  need no new machinery at all: it is an ordinary content-site row. What
  it needs is two measurements, and both have to be taken rather than
  read off the map data:
  1. **The reachable interior, flooded from the arrival tile.**
     `AREA_DIG_CAVES` is a single 480x960 map shared by four rooms, so a
     raw collision dump spans rooms the player cannot walk to and will
     happily suggest a content spot in a different room. Trilby's flooded
     to 27 tiles, tx 7-18 by ty 3-8 against a room origin of (0,640) - a
     winding corridor with ZERO tiles of full 3x3 elbow room, which is
     what makes it a KINDS_SMALL site: a pot cage or a wave has nowhere
     to stand. Expect most dig caves to come out this cramped.
  2. **Whether its overworld mouth sits in a one-way pocket**, because if
     it does, the cave's exit is also the region's descent (see the
     Trilby ladder entry in Known bugs).
  Shipped row: `{ AREA_DIG_CAVES, ROOM_DIG_CAVES_TRILBY_HIGHLANDS,
  QUICKSTART_KINDS_SMALL, 184, 104 }`, checker-verified ("landed, spots
  OK, 1 chest spawn verified"). `tools/quickstart/digcave_survey.py` is
  the survey - re-run it per cave rather than guessing.
  One trap worth carrying: the first spot tried was the cave's far end,
  which a "put it as deep as possible" rule picks - and the invariant
  checker rejected it, correctly, because a wall segment separates it
  from the entrance's own run and only a side passage joins them. In a
  27-tile corridor "deep" is three tiles. Take the spot from the run the
  arrival opens into, and let the checker have the last word.
- **Phase D medium events**: kill-quota bounties (counters exist; needs a
  giver NPC), carry-item-to-NPC (open question: do held objects survive a
  room transition? if not, keep giver and receiver in one region), Great
  Fairy fountain gamble, Mole Mitts dig rooms, more Minish-layer sites.

### 2.4b Wave composition - what is left after the Aug 2026 rework

The escalation clock, per-kind live caps, the sheet budget, the archetype
builder and the retuned curve all shipped together; the study behind them
is the Wave Composition Study artifact. What it identified and did NOT
build:

**FRAME RATE (Aug 2026, user report: "the game is slowing down
significantly on certain enemy waves... specifically in the very large
areas, like North/South Hyrule field", with drops "into the single
frames-per-second" on an iPhone 15). FIXED, and the number that fixes it
is measured.**

The measurement needs no instrumentation. `main.c`'s loop does
`gMain.ticks++`, runs the frame, then waits for VBlank; when the work
overruns, that wait lands on the VBlank *after* next, so ticks advances
once per two hardware frames. `60 * ticks / frames` is therefore the real
frame rate, read out of RAM - `tools/quickstart/fps_probe.py`. Control for
the method: a room load, which certainly overruns, reads 54.8fps with 26
stalled frames of 300.

North Hyrule Field, difficulty 12, live enemy count *held fixed* for the
window, player walking so the room scrolls:

| enemies | entities | avg fps | worst 30-frame window |
|--------:|---------:|--------:|----------------------:|
| 16 | 33 | 60.0 | 60.0 |
| 24 | 41 | 60.0 | 60.0 |
| 28 | 45 | 60.0 | 60.0 |
| 32 | 49 | 59.4 | 54.0 |
| 36 | 53 | 57.2 | 44.0 |
| 40 | 57 | 54.6 | 34.0 |
| 44 | 61 | 52.0 | 30.0 |
| 50 | 67 | 52.0 | 30.0 |

Three findings, in order of usefulness:

1. **The knee is between 28 and 32 enemies**, and past 44 it pins at 30fps
   because the frame has simply doubled. `QUICKSTART_MAX_LIVE_ENEMIES` is
   28 - a GLOBAL ceiling, because the frame budget belongs to the console
   rather than to any room, and it counts what is already alive rather
   than just this wave's own head count (waves overlap; two capped waves
   stacked are an uncapped room).
2. **Scrolling is the other half of it.** At 50 enemies standing still the
   room can still hold 60fps; walking - the tile-buffer rebuild and BG DMA
   a scrolling room does every frame - is what pushes the same wave over.
   That is exactly why the report named the large areas: small rooms do
   not scroll, so enemy work has the whole frame to itself.
3. **It was one room's problem.** North Hyrule Field is the biggest in the
   ring (775 squares against South Hyrule Field's 651) and the only region
   whose waves actually reached the old cap of 50; South Hyrule Field tops
   out at 29 by itself and Lon Lon at 30, which is why those two measured
   clean and this one did not. VARIETY turned out not to matter at all -
   the 50-enemy waves were fifty of ONE kind (a swarm archetype at 150%),
   and cost the same per body as mixed waves of the same size.

After: every region holds 60.0fps walking and 60.0 walking diagonally,
room-locked, at difficulty 12. Two rooms (Lon Lon, Western Woods North)
sit at 59.6-59.7 with three or four stalled frames in 600 - visible only
to the counter.

A method note worth keeping: the first "after" run showed Castle Garden at
10fps and Lon Lon holding 48 enemies, which looked like the fix failing.
Both were the player walking out of the room mid-sample - a room load, not
a frame cost. Frame-rate samples have to assert the room did not change.

- ~~Themed draws~~ **SHIPPED.** One wave in four rolls a theme (fire,
  ice, undead, bug, aviary) and every archetype slot prefers roster
  entries tagged with it - on-theme-and-on-role first, then on-theme,
  then the old role/any ladder - so the cast reads as a designed
  encounter while the shape still owns the structure. Thirty rows are
  tagged; the tags are honest where the bestiary is (bugs, birds, ghosts
  and bones, things on fire) and visual where it is not (the ICE set
  beyond the ice Wizzrobe is the blue/cold cast, because a wave of blue
  things led by an ice mage reads as an ice encounter, which is a
  theme's whole job). A preference, never a guarantee: a tier with
  nothing on-theme degrades to the ordinary draw, so a theme can never
  starve a wave or smuggle in power. The `theme` field trails the struct
  so only tagged rows spell it. Verified by calling the shipped
  QuickStartDrawRole from the emulator (callrom grew stack-argument
  support for it): 40 of 40 themed draws returned on-theme entries at a
  tier where the theme exists on every level; the theme-0 control drew
  the ordinary mix.
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
- ~~Per-region sheet budgets~~ **SHIPPED**, with Castle Garden as its
  first and so far only row (8 sheets against the global 12). The table
  is `sQuickStartRegionSheetBudgets`; adding a region is one row. Re-run
  the checker's `--gfx` tier after any roster or archetype change - that
  tier is what caught this, and it is the cheapest of the three emulator
  tiers to run on its own.
- **Archetype tuning by measurement.** Weights were chosen by judgement,
  not measured play. Once a full run is played at the new curve, revisit
  which shapes appear too often or too rarely.

### 2.5 Bosses

- **Multi-boss and boss+wave combos (F6).** Measured: two bosses fit a
  cleared room, three are marginal, none fit a live diff-12 wave.
  **THE GATE IS OPEN, and it immediately found something.**
  `tools/quickstart/boss_kill.py` engages a family for real and kills it.
  The dual-engaged case measures CLEAN in two of the three allowlisted
  rooms - Castle Garden and Eastern Hills North: two families, both at
  intro stage 9 and out of subAction 0, both zeroed on the same frame,
  both fully gone, player still responsive, same room. No softlock, so
  #125 stays not-reproduced against ENGAGED bosses now, not just idle ones.

  **Lon Lon Ranch does NOT pass the dual case**, and the failure is
  specific: with one family it engages at frame 1027 and dies clean like
  everywhere else, but with two, the second family never finishes its
  intro (measured to 5000 frames: stages [7, 2], subActions [0, 3] - one
  live, one parked in the intro dispatcher). The two Helpers are distinct
  (0x020364f0 and 0x02036530), so it is NOT a shared-scratch collision;
  the likely suspect is the +/-48px dual placement around that region's
  reward spot. **Multi-boss must not ship for Lon Lon until that is
  understood** - and the room-by-room split is the reason the gate was
  worth opening rather than assuming.

  Escort-roster combos ship as a per-boss field once measured (blue
  chuchu + ice wizzrobes is the thematic shortlist head).

  **The recorded diagnosis of why the harness could not do this was
  wrong, and the truth is much simpler.** The note said the engaged fight
  ignores sword taps at 1 hp because "the peel wants real contact windows
  the dumb driver doesn't hit". Measured: the family had never engaged at
  all. Its intro is a nine-stage machine on the body's `Helper` (unk_03),
  and stages 1 and 2 are gated on the PLAYER'S action byte -
  `sub_08026328` waits for `action != PLAYER_ROOMTRANSITION`,
  `sub_08026358` for `action != PLAYER_ROOM_EXIT`. A warped-in player sits
  in PLAYER_ROOMTRANSITION (action 22) and never leaves on its own, so the
  intro parked at stage 1 *for as long as anyone watched* - 1500 frames -
  and every piece stayed at action 1 / subAction 0. subAction 0 is the
  intro dispatcher and is the one subAction that never calls the peel
  handler, so no sword tap could ever have registered. The old driver was
  hitting an inert stack.

  The fix is one line of driver: **walk**. Give the player ordinary
  movement input and action 22 drops to 1, the intro runs 1 -> 3 -> 5 -> 9,
  and the fight engages at ~frame 1027.

  This also revises trap #1 from the region-vetting entry below. An
  undismissed textbox does freeze the stage machine, but pressing A was
  only ever fixing this by accident - it nudges the player out of the
  transition action. The general rule is the useful one: **the boss intro
  will not start until the player is in a normal action state**, and
  warping alone never puts them there.

  What is real in that harness and what is not, because a probe that blurs
  it is worthless: the engagement is real (the shipped intro machine,
  driven by ordinary input); the peel is real (contacts written the way
  the collision system writes them, with the shipped `sub_08027AA4` doing
  everything downstream, and iframes respected so a contact counts once
  per swing); the FINAL BLOW is `health := 0`, because the collision
  system rather than the receiving entity subtracts health, so a forged
  contact cannot do it. Everything after the zero is the shipped death
  path, which is what the dual question is about.

  One race worth knowing: a peel in flight writes
  `super->child->health = 0xff`, so a single zero landing on the wrong
  frame is undone and the family walks away immortal - killing after a
  300-frame peel worked while killing after 1200 frames left all five
  pieces standing. The driver re-zeros for half a second to cover it.

  And one near-miss worth recording as doctrine: the first run of the
  responsiveness check reported the player FROZEN after the kill, which
  would have been a softlock finding. A no-boss control in the same room
  refused three of the same four directions - the spot is simply hemmed
  in. **Test all four directions and pass on any**; a one-direction
  movement check invents softlocks.
- **New boss forms.** Octorok Boss is the next-cheapest per the vanilla
  inventory's boss ladder. Gleerok/Mazaal/Big Octorok each need a damage
  audit, an arena audit (Mazaal is a multi-entity macro and wants a
  dedicated room), and a budget measurement. None are "just spawn it" -
  the blue chuchu, the cheapest case, surfaced three latent bugs.
- ~~Boss spawns for the paused regions~~ **Lon Lon Ranch and Eastern
  Hills North ADDED** (the two named candidates), vetted with
  `tools/quickstart/boss_region.py` to PARITY with Castle Garden - the
  control everyone has watched work in real play. Per room: the family
  composes at the reward spot, the intro finishes and the fight engages
  at the same frame count as the control, a mid-intro seam scroll
  neither locks the game nor strands the player (both directions), and
  the mid-fight screenshot shows the boss actually fighting in the room.
  The small seam-scroll rooms (EH South 480x208, EH Center 480x256) stay
  boss-free; EH North is 480x544.
  **Three traps the harness ate so the next vetting doesn't:** (1) an
  undismissed textbox freezes the boss's whole stage machine while the
  player can still walk - a probe that never presses A measures a paused
  game, and the "boss" it sees is an invisible, inert, sword-carvable
  stack that looks exactly like "this room can't host it". (2) Standing
  inside the boss gets the player swallowed, and out here the swallow's
  spit-out has no arena respawn - measured, it dumped the player at
  world (0,0) in a DIFFERENT room. Real players fight from sword range,
  so the driver does too - but this is a real vanilla-mechanism edge
  worth its own look someday. (3) A fence between the entrance and a
  seam reads as a lockup to a blind march - pick crossing columns from
  the collision map.
  **Bar not yet met by the harness anywhere, control included:** killing
  an ENGAGED boss by script. The engaged fight ignores plain sword taps
  at 1 hp (the peel wants real contact windows the dumb driver doesn't
  hit); Castle Garden fails this leg identically, so it measures the
  harness, not the rooms.
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
  weapons/tools, per the user, Aug 2026), and every reward spawner now
  goes through the shared `QuickStartSpawnRewardEntity` /
  `QuickStartRewardDelivered` pair. The Green/Blue/Four Sword are one row
  each in `QuickStartItemNeedsDirectGrant` whenever they are wanted.
  Correction worth carrying: this file long asserted that equipment has no
  ground-item form and that `CreateObject(GROUND_ITEM, ITEM_RED_SWORD)`
  never creates an entity. A clean-room probe disproved it - the entity is
  created and the sword sprite renders on the floor. The swords stay on
  the grant path anyway, because that is already how the miniboss payout
  delivers one and because GiveItem is the unambiguous way to make an
  equipment upgrade apply.
- ~~Last unused charm idea (F4)~~ **SHIPPED.** Rare-reward-chance-up is
  the Mysterious Shells (`ITEM_SHELLS`), a vanilla collectible this mode
  never used. It re-cuts the tier roll from 60/30/10 to 40/40/20 - rare
  loot doubles - and is one read in `QuickStartDrawItem`, exactly as
  predicted. That closes the original F4 wish list; boss-chance-up stays
  deliberately rejected. Note for the next charm: the food flag block had
  to move (496-508 was about to collide with the D2 alive counts) and now
  lives at 581+, and the announcement strings are no longer contiguous -
  the fourteenth uses string 59 because 46 is the inn's first bed offer.
- **Carlov's lotto machine as a shell sink - A FEATURE TO BUILD (the
  user's call, Aug 2026; research DONE, see below).** Yes, and the gamble
  curve underneath it is good enough to keep as-is.

  **Read this first: the Mysterious Shells are currently doing another
  job.** The luck charm IS `ITEM_SHELLS` - this mode carries all fourteen
  charms and curses on vanilla item ids that had no other role, and the
  shells were the fourteenth (`QuickStartNoteFoodItem`, `case
  ITEM_SHELLS: n = 13`). Vanilla's `GiveItem` still runs that item's own
  metadata action afterwards (`case 0x0e` -> `ModShells`), so **every
  luck-charm pickup silently banks one shell** - measured: shells 0 -> 1,
  charm bit 0 -> 1, figurineCount untouched. Harmless while nothing reads
  the counter; it becomes a design question the moment the machine
  exists, because one shell per charm pickup is far too slow to feed a
  gamble. Decide at build time: either shells get a real drop row of
  their own and the charm moves to some other unused item id, or the
  charm stays the coin and the machine's prices are set to that scarcity.

  What the machine is
  (`src/object/figurineDevice.c`, 828 lines):
  - `FIGURINE_DEVICE`, object id 34, **gfx 81 / sprite 183** - it carries
    a real entity sprite, so unlike the lever it renders in any tileset
    (doctrine 6). It also stamps `SPECIAL_TILE_34` across its three base
    tiles for collision, which is engine-special, not tileset art. It
    costs one GFX sheet slot wherever it stands.
  - **The bet IS the odds, one for one.** Base success chance is
    `100 * (unclaimed / available)` (`sub_0808826C`), and each extra
    shell wagered adds one percentage point
    (`newChance = prevChance + shellDifference`), capped at 100 and at
    the player's purse. UP/DOWN adjust the bet, R jumps by ten. A floor
    (15/12/9/6%) keeps a nearly-complete collection from being hopeless.
    That is a ready-made "spend a currency, buy your own odds" gamble -
    it needs no design work, only a new prize pool.
  - **The draw itself is one function**, `FigurineDevice_Draw`: it rolls
    `Random() % 100 < chance`, then walks the bit array for the first
    unowned (win) or owned (dud) index. A QUICKSTART branch there that
    calls `QuickStartDrawItem` and the shared reward helpers is the whole
    repurposing job. The state machine around it (bet prompt, pull,
    reveal, Carlov's lines) is untouched.
  - **The shells economy already exists in this mode.** The luck charm is
    `ITEM_SHELLS`, and its metadata action (`case 0x0e`, itemUtils.c)
    runs `ModShells` - so every luck-charm pickup is also banking one
    shell today, invisibly. Worth deciding deliberately: either the
    machine is the reason shells accumulate (then shells want their own
    drop row, not just the charm), or the charm keeps being the only
    source and the machine is a rare treat.
  - The two real costs: the reveal expects a FIGURINE index to display a
    figurine sprite, so either the prize shows a borrowed figurine
    picture or the reveal is replaced with an Ezlo line; and the machine
    is gated by `SHOP07_TANA` / `SHOP07_COMPLETE` local flags plus
    `gSave.available_figurines`, all of which a QUICKSTART placement has
    to set or bypass.
  Recommended home if built: the hub, beside the shop - a shell sink
  belongs where the player already spends.
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

- **The inn (Floor 2).** Rest is an INNKEEPER now, not three beds you had
  to stand on (the user, Aug 2026: "walking up to the beds and 'talking'
  to them is not intuitive"). It is vanilla's own inn, moved: Hyrule
  Town's Happy Hearth is run by Emma through `script_Emma`, one textbox
  offering three rooms at three prices with the choice returning through
  a JumpTable - all of which is reused, along with the TEXT_HAPPY_HEARTH
  dialogue. Ours are the prices (50/200/500, pushed in with
  SetMessageValue so the numbers shown are the ones charged) and what
  renting does: vanilla's branches walk the player off to a rented
  bedroom, ours heal 25%/50%/100% on the spot and play the sleep fade.
  The old alcove R-press is deleted.
  - **The keeper is a ZELDA-kind NPC, not the Emma sprite**, and that is
    a measured retreat. Emma was tried first and never answered: her own
    update calls `InitScriptForNPC` on action 0, which re-points her at
    the script her ROOM DATA names - and an NPC built with CreateNPC was
    placed by no room data, so the script `StartCutscene` had just
    attached went with it. Forcing her past that branch did not help.
    What the user asked to reuse is the inn, not the innkeeper's face.
    Giving her Emma's sprite is a follow-up for whoever works out what
    else her action-0 branch wants.
  - `MessageNoOverlap`, not vanilla's `MessageFromTarget`: the latter
    wants message-target state a room-data NPC has.
  - **Verified:** the keeper stands at Floor 2 local (120,104) and
    talking to her opens TEXT_HAPPY_HEARTH message 0x01 (textIndex
    0x4501) - the Happy Hearth greeting, rendered. **NOT verified:** the
    three-way choice, the charge and the heal, because no probe in this
    harness can advance a textbox - a control test on the known-good
    wind-crest signpost showed its box sitting in state 0x04 through
    eight A taps exactly like the innkeeper's. Every earlier NPC probe in
    this project only ever proved a box OPENS. The branch structure is
    copied from vanilla's working script and the three rest functions are
    linked (an undefined Call target would fail the link), but the rent
    path wants a playtest before it is trusted with the player's rupees.
    If it misbehaves, the user's own fallback - three sprites at the ends
    of the beds - is a smaller change than this one was.
  - Still open: the chest half of the spec - the two chest props between
    the alcoves holding a COMMON and an UNCOMMON reward - which rides the
    answered chest research above.
- ~~A permanent ocarina reminder outside the tower~~ **SHIPPED** (the
  user, Aug 2026). A seventh wanderer stands on the Cloud Tops at
  (488,440), one tile south of the wind crest itself at (488,424), so it
  is on the path anyone walking up to warp home already takes. It rides
  the hint table for the spawner and sweep-immunity that come with it,
  but its script names its own string rather than drawing from the pool -
  this line has to be said EVERY run, because it is the only place the
  game states out loud that a trip into the ring is not one-way.
  Verified: it stands there and speaks string 214 (textIndex 0xfed6).
  A probe note worth keeping: `AREA_CLOUD_TOPS` is 8, and a warp that
  misses lands in area 7 without complaining. Two earlier passes of this
  survey read `here() == (7,0)`, carried on regardless, and produced both
  a collision map of the wrong room and a confident "the signpost did not
  spawn". Assert the room before trusting anything measured in it.
- ~~Hint pool drawn per run (F5)~~ **SHIPPED.** Eighteen hints, six
  wanderers, dealt fresh each run: strings 20-25 (the original six) plus
  twelve new ones written against what the mode does NOW - the trophy
  case, Tingle, the dig caves, the switch-puzzle clock, one-attempt
  quests, charms-vs-curses - none of which existed when the first six
  were authored.
  - **Without replacement, without a shuffle or any storage.** Walking
    the pool with a fixed stride from a per-run base visits distinct
    entries as long as stride and pool size are coprime; 18 and 5 are, so
    six spots always draw six different hints. A compile-time check
    enforces that for whoever grows the pool - at 20 hints the stride
    would start repeating and the build stops instead.
  - The base comes from `gSave.run_seed`, not a rolled flag: already
    per-run, already saved, already what every other per-run draw derives
    from. A3's seed pin therefore reproduces the hint deal too.
  - The six scripts no longer name a string. They `Call
    QuickStartHubHintPick` (which works out which spot it is speaking for
    from the NPC's own position and sets `intVariable`) then
    `MessageNoOverlapVar` - the same pair vanilla uses for its own
    table-driven dialogue, and the reason the pool can live in game.c
    next to the spot table instead of being baked into six .inc files.
  - Verified end to end: seed 0x22 predicts string 212 for spot 0, and
    talking to that wanderer in the tower entrance resolves textIndex
    0xfed4 - TEXT_CUSTOM 212 - and renders it.

### 2.8 World structure

- ~~2-door pool door rewiring~~ **MOOT - the pool system is RETIRED**
  (user's call, Aug 2026: "we should be setting all entrances/exits/rooms
  as vanilla rooms now... retire that system ENTIRELY. Connections should
  now only be their vanilla connections, or they should be blocked
  entrances entirely"). Nothing draws a room from a pool any more, so
  there are no synthetic door pairs left to rewire and
  `docs/QUICKSTART_2DOOR_MAP.md` is history rather than a work plan.
  What that turned off, and what replaced it:
  - **North Hyrule Field's river crossing** (the two-way connector the
    user named). Off. Its west bank is inert ground now; its east bank
    turns out to have a REAL vanilla cave entrance behind it, which now
    fires normally into `AREA_CAVES` - verified, the room renders and has
    its ladder back.
  - **Castle Garden's northwest ladder** - BLOCKED, per the user. It was
    the last place the 1-door pool was still used for its original
    purpose; its vanilla destination is the Great Fairy cellar, which
    opens into Hyrule Castle, so blocking beat both alternatives.
  - **The shop's connection stays** (user's explicit call), and so does
    the hub hole. Neither is a ? room pool draw.
  - The pool tables, the room lists and the bank-position survey data are
    kept in-tree behind `QUICKSTART_POOL_CONNECTORS_ENABLED` rather than
    deleted: the coordinates are hand-walked ground truth, and a real
    river crossing would want exactly those two spots.
- **Regions beyond the ring (E).** Castor Wilds / Royal Valley each mean:
  un-block a border, extend the ring-room test, survey, add fusers,
  re-run region_crossings.py + the checker. The adjacency map and distance-2 element
  rule absorb new regions as one enum row plus edges. Routine now - a
  breadth call, not an engineering risk.
- ~~ROYAL VALLEY: surveyed and ready to wire~~ **IN THE POOL** (user, Aug
  2026). The ring is eight regions now. It is a one-way valve - in from
  North Hyrule Field at E, out to Trilby at S, no way back - and the
  room's own geometry is why.
  **Three components, not one** (`tools/quickstart/royal_valley_survey.py`).
  Main is 30x63 tiles holding three separate walkable spaces: the 42-tile
  pocket where NHF's `WEST_NORTH` border lands (tx 19-29, ty 36-40); the
  242-tile graveyard with Trilby's border in it (tx 4-28, ty 43-62); and a
  262-tile top part (tx 2-26, ty 23-40). The pocket drops into the
  graveyard over a ONE-TILE neck at tx 20, ty 41-42 whose collision reads
  0x29 rather than open floor - a ledge, downhill only. The top part is
  reachable only by solving the Lost Woods maze, and it does NOT contain
  the NHF border, so it is not a way back either. That is the user's
  "E to S free, S to E impossible", derived from the map rather than
  asserted.
  **The row, ready to paste**: the graveyard is the component on the
  route, so content belongs there - `roomSquares` 242, `maxEnemies` 18
  (242/13, the survey formula), 28 spawn spots with full 3x3 clearance at
  least three tiles apart, all listed by the survey. The top part would
  support 262/20 and 26 spots if it is ever wanted as bonus space behind
  the maze.
  **What wiring it needs, in order.**
  1. `transitions.c`: un-block North Hyrule Field's `WEST_NORTH` row (it is
     `#ifndef QUICKSTART` today). Royal Valley's OWN borders are unguarded
     already, so the ways out work the moment the player is inside.
     **Trilby's north row is open now**, per the user, and it had to be:
     that crossing was one-way in the worst possible direction. Royal
     Valley's row into Trilby lands the player at y=16 inside a **48-tile
     pocket** (tx 4-16, ty 0-4) that is a walkable component of its own -
     Trilby has 24 separate components and this one touches none of the
     other 23. Leaving Royal Valley was therefore a trap, not a shortcut.
     Opening the row needed a second thing as well: containment cancels a
     region room's transitions to anywhere unblessed, and Royal Valley is not
     in the pool yet, so `QuickStartIsPocketInteriorRoom` names it
     explicitly for now. That naming retires the day the region joins the
     pool. Both directions walked end to end.
     **Where it lands is a LEDGE, and that is fine** - corrected by the
     user after a collision flood said otherwise. The row puts the player
     at Trilby's y=16 in a 48-tile pocket at the top of the map that reads
     as a sealed component; walking off its south edge at tx 14, 15 or 16
     drops them to ty 9, inside the region's 334-tile main body. So Royal
     Valley connects to the Trilby region properly: drop in, walk back
     north to return.
  2. `game.c`: a `sQuickStartRegionPool` row, a `QS_REGION_*` enum entry, its
     adjacency edges (NHF and Trilby), and the pool-index mapping.
  3. ~~Containment decisions~~ **PARTLY DONE.** Four of Main's five vanilla
     doors are content sites now (user's call): **Dampe's house**, the
     **Great Fairy**, and the **two graves**. Each is a clean pocket with a
     border straight back to Main, all four checker-verified. The **Royal
     Crypt stays blocked**, also per the user - no site row, so containment
     keeps its door shut. Gina's grave is worth knowing about: its exit
     list carries a SECOND border, to Castle Garden Main, and Castle Garden
     is a region room, so the pocket rule lets that through - the room is a
     real shortcut out of Royal Valley rather than a dead end.
     Still open: **the Lost Woods maze**. Both its doors are unblessed, so
     the puzzle is scenery until someone decides otherwise.
  4. **The Lantern gate needs somewhere to live.** The route model treats
     it as the area's entry cost; nothing in the game enforces it yet, and
     a run that walks in without one wants checking before this ships.
  **What it buys**: Royal Valley turns up in 71 of 300 four-region routes
  and carries the heaviest bill in the graph - bombs + Lantern + Spin +
  the level-3 blade. That whole class of route was impossible before the
  Tempered Sword went in the pool this same session.
  **As shipped**: pool row 12 of a state block sized for exactly 12,
  `roomSquares` 242 and `maxEnemies` 18 over the graveyard component,
  entrance (296,856) and reward (184,904), 28 surveyed spawn spots. It is
  the eighth named region (`QS_REGION_RV`), adjacent to North Hyrule Field
  and Trilby. North Hyrule Field's `WEST_NORTH` border is open, which is
  the only way in. `QuickStartIsNamedRegionRoom` names it, so the temporary
  pocket-interior exception added for the Trilby seam is retired.
  Measured after wiring: mixed waves of 9-11 enemies at difficulty 0
  through 12, a steady 60fps walking, at least 12 free GFX slots at every
  difficulty, and the checker green.
  **Still open, and now live rather than theoretical**: the region is
  DARK - screenshotted, it paints the Lantern's small-radius overlay - and
  nothing gates the pool draw on holding a Lantern. A run drawn here
  without one plays in the dark. That is the first concrete thing the
  key-item reachability work has to decide.
  **The upper valley was empty, and is not any more** (user report). Royal
  Valley Main is FOUR separate walkable spaces, not the three the first
  survey found: 366 tiles north of the graveyard gate, 262 in the middle
  behind the Lost Woods maze, the 242-tile graveyard, and the 42-tile
  arrival pocket. Every spawn spot was in the graveyard, so the north was
  unpopulated by construction. It has 27 spots now, filtered by a gated
  zone (`sQuickStartGatedZones`) asking for the Graveyard Key - so nothing
  spawns behind the gate until the player can open it, and no wave becomes
  unclearable. The middle stays empty deliberately: the maze doors are
  still cancelled by containment, so anything placed there would be an
  enemy nobody can reach.
- **OVERWORLD KEYS ARE A HUNT NOW** (user, Aug 2026: "I want to restore the
  vanilla behavior of these keys and make it a goal for the player in our
  game to hunt down these keys").
  The Lon Lon Key used to be handed out at boot for a door that did not
  check it, while `QuickStartUnlockRanchHouseDoors` forced both ranch house
  doors open unconditionally. Both halves are gone: the key is a drop, the
  doors stay on vanilla's own script until the run finds one, and the two
  ranch house ? rooms are behind it again. The Graveyard Key gates Royal
  Valley's northern 366 tiles the same way.
  **Where a key may drop is the whole design.** The user's rule - "the key
  must not drop inside the region where it's needed... it could
  accidentally be placed somewhere inaccessible, for example as part of a ?
  room that is behind the door the key unlocks" - is enforced by
  `sQuickStartKeyRegions`, which names the REGIONS each key may appear in:
  the Lon Lon Key in North Hyrule Field, Trilby and Eastern Hills; the
  Graveyard Key in North Hyrule Field, Trilby and Royal Valley itself.
  Royal Valley is on its own list deliberately and safely - every spot
  outside the gate is in the valley's lower half, the gated zone keeps
  placements out of the north until the key is already held, and an owned
  key never draws again.
  **? rooms are wired in** (user: "now wire the ? rooms into the key drop
  regions too"), which closes the third of the user's three drop sources.
  A pocket interior is its own room, so a rule written against
  `gRoomControls` stopped applying the moment the player walked through a
  door - a cave hanging off Lon Lon Ranch looked like nowhere in
  particular. `sQuickStartRoomOwners` is that missing map: 49 pocket rooms,
  each with the region-bit mask of whatever region's door leads into it.
  It is DERIVED, not hand-listed - `tools/quickstart/room_owner.py` walks
  each named region's own `WARP_TYPE_AREA` doors transitively (never back
  out through a region room, or every pocket ends up owned by everything),
  its Minish holes via the SpecialWarpManager property chain, its
  `sQuickStartLinks` boxes, and the two scroll seams that carry no row
  anywhere. The walk partitions cleanly: no pocket in the pool comes out
  reachable from two regions.
  **Owning a region is not sufficient.** A pocket can be inside an allowed
  region and still sit behind that key's own gate, which is the exact
  accident the rule exists to prevent. Royal Valley Main is four
  disconnected pieces, and of its four ? rooms only the Great Fairy is in
  the lower half the player can walk out of - both graves are behind the
  graveyard gate and Dampe's house is behind the Lost Woods maze - so all
  three carry `sealedBy`. The ranch house halves carry it against the Lon
  Lon Key. (Melari's Mine's south-west room used to be the one content site
  with no owner at all, because the mine hung off nothing; the mine is a
  Mount Crenel pocket again and the room is owned by CREN.)
  **Verified against the ROM, not against a model.**
  `tools/quickstart/key_regions.py` warps into 17 rooms and calls the
  shipped `QuickStartKeyRegionAllowed` directly, expected answer per case,
  plus an ungated item each time so a room that refuses everything cannot
  pass as a room that correctly refuses keys. Earlier: the boot inventory
  no longer carries the Lon Lon Key, and the gated zone provably controls
  where enemies spawn (zone asking for an item the player always holds, 6
  of 11 enemies north of the gate; asking for the key, none). The doors
  themselves still want a playtest.
- **A test build exists for walking gated routes**: `make
  quickstart-testkit` starts the player holding the Blue Sword, bombs and
  the Spin Attack - the kit North Hyrule Field's WNW border asks for, and
  so the only way to reach Royal Valley on foot without first winning
  those items. Off in every normal build (`QUICKSTART_TESTKIT`).
  Deliberately NOT the Four Sword: holding it makes `sub_080AF284`
  (movement.c, from Castle Garden's state change) replace Castle Garden's
  entire exit list, which would take the region's borders with it.
- **The Minish layer as a parallel network (#102) - the SURVEY IS DONE and
  its findings are wired** (the user, Aug 2026: sweep every Minish hole,
  room and treehouse in the ring and add the unwired ones as ? rooms).
  `minish_sweep.py` walks every exit the eleven region rooms have, filters
  to the Minish-layer areas and cross-references
  `sQuickStartRoomContentSites`. Result: 26 Minish-layer exits, and only
  six destinations with nothing in them.
  - **Five are now content sites**: North Hyrule Field's four Boomerang
    tree hollows (each behind its own kinstone fusion, each with a ladder
    down to a Boomerang chamber quadrant that was ALREADY a site) and its
    fairy-fountain tree. All five are 240x160 hollows with 27-37
    reachable tiles and not one tile of full 3x3 clearance, so they are
    KINDS_SMALL and their spots ask only for a plus-shape. Checker-
    verified, all five: "landed, spots OK, 1 chest spawn verified".
  - **The tree ladders are real ladders again.** Each hollow's ladder down
    into the chamber used to be a position box on the floor in front of it,
    so the player never climbed anything - they walked near the ladder and
    the room changed under them (the user, Aug 2026: "we want the player to
    actually descend the ladder, like in vanilla"). The vanilla row was
    always right; the collision under the ladder art reads 0x0c, which
    stopped the player at y=95, the last pixel of the tile and six outside
    the door's own +-6 rect at y=84. Right tile, wrong pixel. Opening that
    one tile's collision alongside its actTile (`SetCollisionData`, which
    touches neither art nor tile type) lets the vanilla door fire, with the
    tile's own type still feeding `gRoomTransition.stairs_idx` so the climb
    plays. All four verified: walk up, descend; arrive back, stand still,
    walk out south. The boxes are gone.
  - **The Boomerang trees were the risk, and it is checked, not assumed.**
    Their ladders are what reach a chamber this mode already fills, so a
    site that swept their contents would strand four existing sites plus
    a RARE drop. `QuickStartClearVanillaRoomContent` deletes enemies,
    NPCs and a six-object whitelist; the only object standing in these
    rooms is an ARCHWAY (id 79), which is not on it.
  - **The fairy-fountain tree DOES cost something**, and the trade is
    deliberate: FAIRY and GREAT_FAIRY *are* on that whitelist, so wiring
    it deletes the vanilla Great Fairy and replaces a fixed free heal
    with a drawn event (the mode's own FAIRY kind can still roll there).
    Revisit if free heals turn out to matter more than variety.
  - **The sixth is `AREA_MINISH_WOODS`, deliberately left out.** It is
    not a room but a whole area behind a BORDER exit from Eastern Hills
    South and North - opening it is the "regions beyond the ring"
    decision below, with everything that entails (survey, fusers,
    region_crossings.py, the checker), not a room wiring. It is the natural next
    region if the ring grows.
  - What remains of #102 is the part still blocked behind #103: the
    holes and entrances the user is collecting that do not fire at all.
    Those are not missing SITES - they are missing transitions, and the
    sweep above cannot see them because a door that never fires has no
    exit row to find.
- **Difficulty option research (#51).** An options-menu entry writing a
  save field is small; the real question is design: does difficulty still
  auto-escalate on wins if the player can also set it? (Decision 5.)

## 3. Known bugs and issues

Open defects and unexplained reports, roughly by player impact.

### Gauntlet waves sized to the chamber (Oct 2026)

The user, right after the spawn audit: "Size the gauntlet waves to the
chamber too. We want to go by enemy density per available square,
scaling with difficulty. At very high difficulties we might have an
enemy every 5 squares, while at lower difficulties it could be every 9
squares or every 16 squares."

`QuickStartSpawnWave` now asks `QuickStartChamberTileCount` for the floor
it has: the placer's own flood (player-seeded when it holds the content
spot, anchor-seeded otherwise), restricted to the owning site's share of
a multi-site room. The wave is that floor divided by
`sQuickStartWaveTilesPerEnemy[enemy difficulty]`, plus one body per wave,
never fewer than two, still capped at the room's twelve. The row:

| enemy difficulty | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tiles per enemy | 16 | 15 | 14 | 12 | 11 | 10 | 9 | 8 | 7 | 7 | 6 | 5 | 5 |

Enemy difficulty is the counter less two, so the shipped counter of 3 is
row 1 and the user's "difficulty 5" is row 3. The old flat 4 + d/2 + 2
per wave survives only for a wave whose seeds find no floor at all.

Measured on the shipped ROM with `spawn_audit.py --diff 3` and `--diff
12` (bodies on the frame they appear; at the top of the curve the count
includes the extra entities a multi-body kind brings, so a capped wave of
12 placements can read 15-18):

| room | at counter 3 | at counter 12 |
|---|---|---|
| South Field rupee cave (15x10) | 4/5/6 | 12-cap every wave |
| Grimblade dojo | 5/6/7 | 12-cap every wave |
| Castor Darknut hall (17x13) | 7/8/9 | 12-cap every wave |
| Minish cave north of Lake Hylia | 6/7/8 | 12-cap, 16 on the third |
| Castor Darknut cave, Grip Ring | 2/3/4 | 7/5/5 (the floor fills) |
| Heart Piece hallway (3 wide) | 2/2/3 | 5/3/3 (the floor fills) |
| Lake Woods ladder landing | 2/2/2 | 3/5/2 |

The Boomerang cave and Trilby Highlands still deal waves 1 and 2 into
the killed chamber with the neighbour's enemies standing (now 3 and 2
bodies a wave at the shipped counter, their chambers being 41 and 27
tiles).

The survive variant draws its top-ups through the same sizing, and so do
the memory room's wrong-answer wave and the seam gauntlet.


### The spawn audit: void corners, multi-site gauntlets, a softer curve, three hearts (Oct 2026)

The user, on the shipped build: "The current difficulty on tmc-3d feels
very high. I would say this should be difficulty 5 in terms of the enemies
spawning"; runs should start with three hearts, "one bottle with a fairy
inside, and one empty bottle"; and "some of the ? rooms have enemies that
are spawning into the very corner of the room, usually the upper-right
corner... affecting the winability of certain ? events like three wave
clear rooms. Do an audit on all of the eligible ? rooms."

**The curve.** `QuickStartEnemyDifficulty()` is the run's counter minus
two, floored at zero, and it is what every enemy roster and head count
reads now: the tier table (`QuickStartPickEnemy` / `PickPursuer`), the
live caps, the region escalation base, the gauntlet, survive, hunt, scav,
stealth, dig, roof, memory and challenge counts, the miniboss coven size.
The counter itself - HUD, drop weights, stake tiers, dark-room and fickle
odds, the increment on a win - is untouched, so a save's number still
means what it did. Measured: a pinned counter of 5 answers enemy
difficulty 3, 3 answers 1, 12 answers 10.

**Three hearts, two bottles.** `maxHealth` 24 at run start; bottle 1
holds a fairy, bottle 2 is empty (the empty one is what keeps the rare
band's bottled rewards drawable). Measured from the save after a boot:
health 24/24, bottles [fairy, empty].

**The audit** is `tools/quickstart/spawn_audit.py`: every SMALL/LARGE/ANY
site without a kinstone gate (100 of the 105), booted through the testbed
with the WAVES event forced and a full kit, stepped one frame at a time so
each enemy is recorded on the frame it appears, then killed wave by wave
for three waves. Each body is checked against the game's own flood from
the player's tile, a second flood from the content spot, the open set, and
the room rectangle's rim. First run: 1,872 bodies, 196 flagged, 24 rooms.
Of those, the Great Fairy rooms deal no site event by design, two Crenel
rooms held the seed's quest giver instead of a wave (other seeds deal
waves), Mount Crenel's count is the region's own ambient waves, three
Minish rooms are rim-flagged walkable water or path tiles, and the
Boomerang cave's "void" is its other four chambers. What was left were
two real defects.

**Defect 1: mixed waves opened the escape hatch per kind.** The placer's
fourth pass drops the reachability rule so a wave never places nobody;
it opens when a CALL placed nothing, and a mixed wave is two or three
calls. In a small chamber the first kind filled the floor, the last kind
found no tile at one-tile separation, and the hatch put it on the open
tiles outside the walls - the top rows of the cave's rectangle, both
upper corners of Grip Ring's, the left rim of the Castor Darknut cave,
both void columns beside the Heart Piece hallway, the ladder corridor in
the Lake Woods cave. Always the third wave, always the overflow kind.
That is the user's corner. Now `QuickStartSpawnEnemiesOnOpenTilesEx`
takes `allowHatch`, and `QuickStartSpawnWave` passes it only while the
wave is still empty: a short third wave in a cramped room, never a body
over the wall. And when the player's seed fails outright (a doorway with
four wall neighbours - the Minish water cave south of Lake Hylia, every
wave) the placer floods from the content spot before it gives up on
reachability at all.

**Defect 2: a gauntlet in a multi-site room counted the whole room.**
`QuickStartCountRoomEnemies` is every enemy of ours anywhere; the Boomerang
cave has five sites in four sealed chambers, Trilby Highlands two, Goron
Cave's main room four. Kill a chamber's first wave and the second never
came while a neighbour's miniboss stood - a wave room the player cannot
finish from inside it. `QuickStartCountSiteEnemies` applies the miniboss
kind's own ownership rule (`QuickStartTileBelongsToSite`, nearest site
wins) to the gauntlet's headcount, the survive top-up and the re-entry
sync, and the wave itself is now placed as its site's so it cannot land
in the chamber next door.

**Defect 3: two gauntlets in one room shared the seam record.** The
seam-gauntlet record (FLAG_BANK_11 43-58, the state that survives
Grimblade's scroll seam) was keyed to the ROOM. Whenever two sites in the
Boomerang cave or Trilby Highlands both rolled the gauntlet - the fixed
testbed seed does exactly that - they read each other's state: A cleared
its wave and wrote "wave 1, not spawned", B dealt wave 1 on top of its
own wave 0, A read B's "spawned" and cleared again. A never got a second
wave. Measured with a pure-Python chamber flood and a chamber-only kill
(no ROM call before the kill - see HANDOFF_ISSUES): on the pre-fix ROM
Trilby Highlands' west chamber never received wave 1 while the east
chamber held 8; on the fixed ROM both rooms deal waves 1 and 2 into the
killed chamber within five frames with the neighbour's five enemies still
standing. The record carries a 7-bit site tag now (bits 124-130, the gap
between the inn chests and the Western Wood brush), and
`QuickStartGauntletIsHere(site)` / `Remember(wave, spawned, site)` take
the site.

**Measured after the fixes** (same audit, same rooms): the Heart Piece
hallway deals 3/3/3 instead of 3/7/9 with the overflow in the void, Grip
Ring 5/5/5, Exit to Mines 4/4/4, the Castor Darknut cave 5/5/5, the Lake
Woods ladder landing 2/2/2 - every body on the player's floor, zero
flagged in those rooms. The full pass on the shipped ROM: 1,898 bodies
over 100 rooms, and the only tiles off the player's floor are the three
multi-site rooms' neighbour chambers and Mount Crenel's ambient region
waves; the rest of what flags is the rim tag on walkable Minish path and
beanstalk tiles, and the five rooms that deal no wave by design.

**Not changed, worth knowing.** The rim flag is advisory: Minish path
rooms genuinely walk their top row. (Wave sizes were still the flat 4 +
difficulty/2 + 2 per wave when this shipped; the entry above this one
sizes them to the chamber.)


### Scenario saves with a full kit; the upgrades that never showed; ammo drops (Oct 2026)

The user: "build me a few scenario files" for every boss, the carry quest
and as many ? room trials as reasonable, every one with "a full kit, full
hearts, all items and powerups"; the bomb bag, quiver and joy butterflies
"have never shown up"; and enemies should drop arrows and bombs "much more
often".

**Kit 2 is everything now.** `QuickStartGrantEverythingKit` walks the tier
table and grants every weapon, key item, skill and butterfly (the charms
and curses stay out - they are status effects), takes the stronger half of
each exclusive pair (bombs, magic boomerang), and sets 40 hearts, a full
wallet with 999 rupees, bag and quiver level 3 with 99 each, and red
potions in two bottles - MAPEXPLORE's ceiling. Measured: a BOSS scenario
booted with kit 2 reports every listed item owned.

**`tools/quickstart/make_sav.py`** builds a complete `.sav` around a
scenario with no save to start from: it boots the ROM once, takes the
game's own freshly started SaveFile and SaveHeader out of EWRAM, writes
the scenario in, and lays the image out as `src/save.c` does (signature,
header, file 0 with 'MCZ3' statuses and CalculateChecksum, the other
slots INIT), stored 8-byte-reversed as mGBA keeps this game's EEPROM.
Twenty-three saves ship as a zip: the three bosses (and a green chuchu in
Trilby), the five quests, every ? room kind at the ranch house's ANY site
including the rare drop, the elite miniboss, both NPC moods, the stripped
gauntlet and both memory rooms, and a plain North Field landing. The
memory rooms needed one more line: a SITE scenario dealing kind 7 now puts
the named site in the named role, so the sprite there answers for the
room it stands in. `scenario.py show` reads every file back with its
checksums verifying; what has NOT been done is loading one in the game,
because the harness's mgba cannot attach a save - the README says to try
`--plain` if the file select comes up empty.

**The missing upgrades.** `ITEM_BOMBBAG`, `ITEM_LARGE_QUIVER` and the three
butterflies sat in the forty-row UNCOMMON tier behind a prerequisite: each
was 1-in-40 of a 30% band, under one draw in a hundred, and only once its
weapon was held. All five are COMMON now (prerequisites kept), fifteen
rows at 60%.

**Ammo.** The QUICKSTART drop block added 650 points of rupees to every
enemy's table and nothing to bombs or arrows, which the vanilla rows weigh
in single digits. Each gets 200 the moment its weapon is held.


### The switch puzzles retired; the two-room blink memory event; mixed waves (Oct 2026)

The user: the switch-puzzle ? rooms were "completely broken" - the cage's
pots could be lifted and thrown, the layouts were awkward, the switches did
not work and no enemies came for a wrong switch - so they are retired
outright and the blink puzzle rebuilt across TWO linked rooms; and the
three-wave room should mix its enemies.

**Retired.** `QS_EVENT_GATE` and all four of its variants (closing gate,
decoy switches, linger plates, blink sequence) are gone from the dispatch
and the kind pickers; the sixteenths they took in the ANY picker went to
the pot lottery, the chest lottery and the NPC, and the LARGE picker's one
share to a gauntlet. The puzzle helpers the new event reuses (the switch
spawner, the inboard clamp, the switch-spot finder, the permutation table)
stay; the cage, timer and plate helpers are dead code pending a sweep.

**The blink memory event (`QS_EVENT_MEMORY`, value 7).** Two sites per
run, a pure function of the run seed over the sites that may host anything
(`QuickStartMemorySite`): a LESSON, where three switches north of a Zelda
sprite light one at a time in a seed-drawn order, forever, and a hit changes
nothing but the click (the room rewrites the flags every frame); and a
RECITAL elsewhere - never the same room - where the sprite asks for the
order back. The right three strikes drop a prize a tile south of the
sprite; a wrong one darkens everything, resets, and deals a real wave.

What the win chain sees: both are ordinary EVENT candidates. The lesson is
DONE the moment its sprite has been talked to (the script's own Call), and
alone among sites keeps its content after DONE so the blink stays
watchable; the recital is a candidate only while the lesson's room is also
in reach, and can be brute-forced regardless (six orders, a wave each), so
a step on it is never a wall. Its DONE is the prize taken. The testbed's
SITE scenario deals it as kind 7 with the role in extra bit 0.

Measured (`tools/quickstart/memory_probe.py`, 9/9): distinct rooms;
three switches and a sprite in each; the lesson blinks in the seed's order
and ignores a strike; the lesson latches DONE and keeps its content on a
second visit; a wrong first strike in the recital spawns enemies and
resets; the right order drops the prize and taking it latches DONE. One
trap for anyone probing it: the three switches are NOT left-to-right in
flag order once the spot finder nudges one past its neighbour - read each
switch's own flag id (entity +0x86).

**Mixed waves.** `QuickStartSpawnWave` draws two roster entries for the
first wave and three for later ones and splits the head count between
them (the first draw keeps the remainder; the fallback ring keeps the
first draw). Independent draws, so a wave can still come up all one kind,
just rarely. Measured in the ranch house's gauntlet: wave 0 {48:2, 63:3},
wave 1 {63:2, 20:1, 88:4}, wave 2 {2:3, 89:6}. The same spawner serves
the survive room's pursuers and the recital's punishment wave.


### The wave recentering is gone; Lake Hylia and Lon Lon host no clear challenge (Oct 2026)

The user: "all the enemies in certain areas (like SHF, NHF) will spawn to
a central location after a fixed amount of time. This feature is left over
from previous builds... We need to remove this feature, if it's safe."
Safe for certain in NHF, SHF, EH, WW and Trilby; Lon Lon Ranch has a pocket
reachable only from Veil Falls and Lake Hylia two separate pockets, and
rather than keep the pull there, "don't allow wave clear challenges in
these regions with isolated pockets, the way we are currently doing for
Crenel Heights."

**Done exactly that.** `QuickStartRescueStuckFinalWave` - ninety seconds
of an uncleared wave, then every survivor to the reward spot - is retired
everywhere, both call sites (the per-region loop and the WAVE carrier's
element gate). `QuickStartRegionAllowsWave` now refuses Lake Hylia and Lon
Lon Ranch alongside Mount Crenel's Base: waves still spawn there as
scenery, but there is no clear reward, no chain WAVE step and no WAVE win
carrier in either. The simulator reads that list from the C and follows.

**What a flood cannot tell you.** Two floods were tried to classify every
region's spawn offsets as reachable or pocketed from the landing - the
ROM's own `QuickStartMarkReachableTiles` and a plain collision flood - and
they agree with each other and disagree with the user: both call 25 of
South Hyrule Field's 48 offsets isolated, in a field that is walkable end
to end. One-way ledges are walls to a flood, so "not 4-connected to the
landing" is not "unreachable", and the measurement was set aside; the
region list above is the user's knowledge, not the tool's. Castle Garden,
Royal Valley, Castor Wilds, the Wind Ruins and Minish Woods keep their
clear challenges with no pull behind them - Royal Valley, Castor Wilds and
both Ruins rooms measured zero offsets outside the landing's component or
a gated zone, Castle Garden and Minish Woods did not measure cleanly, and
none of the five was on the user's safe list. If a wave in one of those
ever will not go to zero, that region joins the refusal list; the cost is
one line.


### The Oct 2026 boss batch: any blade, no freeze, fewer, roomier, one reward, keys everywhere

The user: bosses "often not working and happening too often"; the chuchus
and the Big Octorok "sometimes don't take damage from a regular sword hit,
sometimes they do"; the chuchu "gets stuck and frozen and the player has
to leave the room and come back"; the spawns in South Hyrule Field and
Lon Lon Ranch are cramped; a wave-clear chain step pays two key items;
and key items should come from ? rooms and quests too. Every item measured
with the new testbed (`scenario.py boss ROW FORM`) and a free-roam driver.

**Which sword you held decided whether the boss could be hurt.** The
chuchu's peel handler (`sub_08027AA4`) and the Octorok's weapon hook each
listed contact source 4 ("sword") and 16 ("dash sword"). A sword's contact
source is the ITEM's hurtType: the Smith's Sword is 4, the White Sword 5,
the Four Sword 6, a spin attack 0x18-0x1a by blade, a thrust 0xb/0xc, a
charged swing 8-0xa or 0xd. Measured (`chuchu_contact.py`): a Four Sword
swing sets `contactFlags 0x86` on the body - CONTACT_NOW | 6 - and the peel
counter did not move once in 4000 frames of swinging, while the body's
iframes went to -16 on every swing. The earlier "fix" that opened the dead
phases was measured by forging contacts with source 4, which is why it
passed. Both bosses now take ANY player weapon: every source below 0x40
except 0 and the small gust.

**The freeze is the walk home.** After a peel-and-rearmour the body enters
subAction 10, which slides the family sideways to the exact x it spawned
at (`Helper.unk_0e`) and does nothing else until `x == home`. Deepwood's
floor is flat; a field is not, and the first free-roam run sat in that
state for 3586 frames, then 752 more. Ninety frames of not arriving now
makes wherever it stands the new home (the spare `Helper.unk_0d` counts).

**Fewer bosses.** The wave roll is 5% (was 10); the chain deals at most one
BOSS step, none when the win carrier is already BOSS, and only in every
other run (a per-run coin off the chain hash), so a run owes one boss at
most and the roll is the only extra. Simulated over 3000 strict runs: a
required boss in 55% of runs (the carrier's third plus the coin's
half of the rest), against four runs in five before the coin and up to
several per run before the cap. The simulator mirrors all three rules.

**Roomier spawns.** `QuickStartRegion` grew `bossX/bossY`; the Trilby
special case became a row. Measured from the collision map (scratchpad
`open_space.py`: the largest all-open square inside the arrival component
and outside every gated zone): Lon Lon's reward spot had a clearance of
ZERO tiles, South Field's two. Lon Lon's boss stands at (312, 792) and
South Field's at (488, 408), both clearance three; both compose there
(`boss_spots.py`).

**One reward per chain step.** The chain no longer pays its own key item
on top of the step's content; a WAVE step is the region clear's draw and
nothing more. The next step is still rolled against what the player holds,
so placement is unchanged; what changed is the pace of the kit.

**Keys everywhere.** `QS_CAT_DROP` includes `QS_CAT_KEY`, so ? rooms,
quests, gauntlets, the roof and the fairies can all pay a key item at the
tier the table gives it.

**Measured after, free-roam with the Four Sword only, on the testbed's
BOSS scenario in Castle Garden (`tools/quickstart/boss_fight.py`, which
teleports the player beside the body when stuck so what it measures is the
damage path): the green chuchu's whole family dead at frame 4648 (445
swings), the blue's at 7028 (775), the Big Octorok's at 1963 (256) - no
stall anywhere outside vanilla's ~1300-frame entrance. Before the batch
the same driver logged 1281 swings on the blue chuchu with the peel
counter at 0 and 12000 frames on the Octorok without landing a blow, and
the green chuchu spent 3586 of its frames in the walk-home state.

**Tooling:** `parse_tables.region_pool` learned the two new row fields (the
chain probe and the catalogue both read the pool, and three rows had
vanished from it). `chain_probe.py` runs to progress 4 again - the old
ROM's item-get payout had stopped its forced steps from ever advancing -
but its own Python reach model predates the MINISH model and calls two
Minish-house sites unreachable that the ROM (and sim_validate, 402/402)
place inside reach; listed under known-stale tooling.


### The feature testbed and the carry quest (Oct 2026)

The user: "I need a mode where I can test individual features of our game
in an isolated way... every little thing in our game that could come up",
and "a sprite in one part of the map could instruct the player to go fetch
an item from another map region and carry it back to them". Both built as
designed in `docs/QUICKSTART_CARRY_AND_TESTBED.md`, which now carries the
as-built notes and the usage.

**The testbed.** Eight bytes in the save (`SaveFile.scenario_*`, the old
`filler38`) name a scenario; `QuickStartScenarioRunStart` reads them once
at run start and the four dealers consult them when they roll. Kinds:
SITE (a site deals a named event), BOSS (a row deals a named boss form on
every wave), QUEST (a named quest hosted in a named row - pot, hunt, scav,
stealth, carry), CHAIN (step 0 dealt verbatim), REGION (arrive with waves
banked), FUSER (a spot room wears a named face), ROOM (any room, any
tile). A scenario skips the hub, hands out a kit (none / the test kit /
that plus every traversal item), pins the difficulty, pre-rolls the pit's
drop region to the landing's region and lands the player there.
`tools/quickstart/scenario.py` writes the bytes into a `.sav` (or, for
the harness, into EWRAM on boot) and `list`s the catalogue.
`scenario_probe.py` boots every kind: 15/15, with a no-scenario control
landing in the hub. Kind 0 - every save ever written - changes nothing.

**The carry quest.** A fourth quest giver (Zelda-faced, own region, own
bank-11 bits 156-173) asks for a parcel - one of five vanilla trading
props as a `SHOP_ITEM` - lying on the reward spot of a region next door
(adjacency table, preferring a region the kit can reach, chosen at accept
time). Lifting is vanilla's; the seam is bridged by one save byte: stash
on `transitioningOut`, respawn at the feet on the far side and lift it
again through vanilla's own interaction path (the player forced into the
talk state with the lift queued; the prop's init clears `interactType`,
so the lift waits one frame for it; the queued action is then returned to
normal by hand because no shop textbox will do it). While held, the
prop's pedestal is kept under the player, so a hit, a shrink or a fall
drops it at the feet via `sub_080819B4`'s own put-back. Left behind, it
goes home. Delivery is a proximity test at the giver or the script's
first `Call`, pays a RARE draw at the feet, and counts as the run's side
quest (`QuickStartSideQuestDone`: pot OR carry) for the chain's QUEST
step and carrier. `carry_probe.py` plays it end to end: 9/9.

**Measured.** Borders fire while carrying; a forced drop lands within a
tile; the rebuilt hold takes ~100 frames after a seam; all five parcels
draw; a parcel carried into the hub or a fairy's room goes home instead.
**Not measured:** the `.sav` slot write - the harness's mgba crashes with
any save attached (both `autoload_save` and `load_save`), so the checksum
arithmetic is transcribed from `src/save.c` and awaits a real save. The
in-hub console (design doc sec 2.3) is not built.
`invariant_check.py`: 0 failures once its flag ledger learned that
`GF_CARRY_*` is bank 11 (the first full run reported 18 collisions that
were all that one missing line); sim_validate 402/402.


### The two door keys, run vanilla's way, and the keyed chain step (Oct 2026)

The user: the ranch house's back door was open, its front door locked on a
key, and walking from the back room into the front one left Link "walking
continuously while the player is locked out of any controls"; the graveyard
key opened nothing. Both doors should be locked until their key, the keys
should be rewards that turn up somewhere every run, and finding a key then
clearing what it locks should be an option in the win chain. "Research how
this happens in vanilla so that we can properly emulate it."

**What vanilla does.** The ranch house is one global flag, `INLOCK` ("gave
the key to Talon"): clear, the front door is a script-driven `HOUSE_DOOR_EXT`
(`script_LonLonRanchDoor`, waiting on the flag) and the west room loads two
`HOUSE_DOOR_INT` blockers with timer 1, which `HouseDoorInterior_Action1`
reads as never pushable - one across the doorway to the east room, one
inside the front door; set, the script jiggles the door open and hands it
to the plain walk-up type (`sub_0808692C`), and the blockers are not loaded.
The back door was never locked: the north field is reached THROUGH the
house. The graveyard key is a three-state item - 1 Dampe handed it over, 2
Dampe opened the gate (`script_DampeOuside`: value 2 + `sub_0806BEFC`
retiles it) - and Royal Valley's room init loads the closed gate, its
tiles, and Dampe beside it whenever the value is not 2, plus the Takkuri
theft (crows, key-on-the-tree) unless `HAKA_KEY_LOST`/`HAKA_KEY_FOUND` say
that chapter is over.

**The bug, reproduced.** In through the open back door, west through the
doorway, and the seam scroll walks the player into the west room's blocker
at (184,88): `PLAYER_ROOMTRANSITION` pushing on a door that cannot open from
that side. The earlier fix had stripped `ENT_SCRIPTED` off the front door
when the key was held and never touched the blockers, so even a key-holder
could not cross the house.

**What shipped.**
* `INLOCK` follows the key: `QuickStartRanchHouseMonitor` sets it the frame
  the run holds the Lon Lon Key. In the ranch it then takes every scripted
  door (the front door is type2 3, script-driven with no `ENT_SCRIPTED` bit
  at all) off its script the way `sub_0808692C` does - the script itself
  never gets there, because its jiggle waits four times on a sync flag only
  Talon's cutscene sets. Without the key it hands the back door the same
  script, which holds it shut. A door still in action 0 keeps its own init:
  converting a freshly spawned door straight to action 1 left it invisible
  and unpushable (measured). Inside the house with the flag set the
  blockers are deleted, as a load with the flag set would never have made
  them; `QuickStartFixupRoomFixtures` no longer makes those two pushable,
  so a Minish player through the hole gets the west room and nothing past
  it. Survey: `RANCH_HOUSE_EAST` is `LONLON_KEY` now (was boulder or
  Minish). Measured on the shipped ROM: no key, both doors hold the player
  at y 651; key first or key later, either door enters its room, and the
  interior crosses both ways (west room arrival 104,120 -> east room
  25,90 -> west room 183,90, action 1 throughout).
* The graveyard needed one line of state and no code: the run reset sets
  `HAKA_KEY_LOST` and `HAKA_KEY_FOUND` (and clears `INLOCK`), and vanilla's
  own Dampe - who was standing by the gate all along with his script parked
  on `CheckGlobalFlag HAKA_KEY_LOST` - does the rest. Measured: talk to him
  holding the key (value 1), value 2, the gate tiles change and the player
  walks through (local y 400 -> 263). The gated zone behind the gate now
  opens at value 2, not at "held". A ZELDA-faced gatekeeper of our own was
  built first and found standing on top of him; it went. One trap on the way:
  the first draft of the run-reset lines was anchored after
  `SetGlobalFlag(KAKERA_COMPLETE)`, which exists only in the
  `#elif defined(MAPEXPLORE)` branch of `GameTask_Transition` - a
  frame-by-frame trace of the flag bits is what found it.
* **The keyed chain pair** (`QuickStartChainRollKeyedPair`): one roll in six
  while a step is left for the far side of the lock deals an ITEM step for
  one of the two keys and, in the same roll, an EVENT step at a content
  site that key seals (`sQuickStartRoomOwners.sealedBy`: the ranch house's
  two rooms, the graveyard's two), priced against the reach mask WITH the
  key - the one time a sealed site can be dealt before the run holds its
  key. The ITEM kind was the chain's dead branch (0 of 500,000 rolls); it
  is honest now because while the step is current `QuickStartDrawItem` pays
  that key out of the very next reward drawn in one of its own regions
  (`sQuickStartKeyRegions` - a ? room, a clear, a quest, a fairy), and the
  pair is only dealt when those regions overlap what the run can reach.
  Ezlo's line for the step names the key and the regions (strings 195-196,
  compass or not). `QuickStartChainRollStep` returns how many steps it dealt
  and the monitor rolls only what is new. `sim.py` mirrors it (`SEALED`,
  `CHAIN_KEYS`); 10,000 runs put a keyed pair in 39% of runs, 96% of them
  the ranch key - the graveyard pair wants Royal Valley reachable at roll
  time, which it rarely is. Measured on the ROM: 8 of 24 seeds deal
  `ITEM(55) -> EVENT(site 26/27)` with `chain_rolled` 2, and with the pair
  current the draw returns the key in North Hyrule Field (mask 0x2, allowed)
  and the normal item in Castle Garden (allowed 0).

Harness notes from the way there, for `docs/HANDOFF_ISSUES.md`: a warp onto
a solid tile leaves the player unable to move for the rest of the run; the
Castle Garden -> Royal Valley warp does not land (Trilby -> Royal Valley
does); vanilla Dampe only registers as a talk target after he has been off
screen once, so a warp beside him never gets an answer.

### The shoe merchant's fusions, and Mount Crenel populated (Oct 2026)

Two more from the user, the morning after the five.

**Rem could not fuse.** "The player can speak to the sprite, which causes it
to play its default vanilla dialogue, and then the player is frozen in
place." Rem is one of the seven fuser faces, and his NPC handler is the one
whose type-0 init does more than the others': `sub_0806A3D8` (src/npc/rem.c)
calls `StartCutscene(super, &script_Rem)` unconditionally, over the
`script_QuickStartFuser` the spawner had just given him, and `script_Rem`'s
first line registers him as a TALK target. The other six faces init through
`InitScriptForNPC`, which leaves the script pointer alone - which is why
they were fine and he was not. Measured in Trilby with the default run seed
(whose face there is Rem): seven Rem fusers, all `INTERACTION_TALK` with
kinstone 0, none `FUSE`. The fix is a question the handler can ask:
`QuickStartNpcIsOurs(Entity*)` answers from the interaction table, where
every NPC the mode places is registered with game.c's own static hitbox and
no vanilla NPC can be. Rem's init parks ours in action 5 (`nullsub_503`)
and returns; the type-0 update loop still runs `ExecuteScriptForEntity`
every frame, which is all the fuser script needs. After: the same seven
stand in action 5, five of them `FUSE` and two `TALK` with kinstone 0 - the
fickle roll from the batch before, not Rem's script. The function is there
for the next face whose handler does the same thing.

**Crenel's enemies were confined to the ledge.** By design, as the earlier
entry "Where enemies spawn ... the Mount Crenel problem" records: its ten
spots covered the 69-tile arrival component only, because a body on a
component the player cannot reach is a region that can never be cleared.
That premise expired when the mountain's clear rewards, boss and WAVE steps
were all withdrawn (`QuickStartRegionAllowsWave`/`AllowsBoss`); nothing on
Crenel counts the room to zero any more, and the user asked twice. So the
table now covers every land component the room has - the ledge's ten, 14 on
the mountain proper (402 tiles), 7 on the middle shelf (244), one each in
the two pockets the cave network lands in (47, 29): 33 spots, 92% of 777
land tiles within 96px of one, sampled the same way as Trilby's
(`spawn_spread.py`'s sampler run over the union of components). Room squares
go 52 -> 400, half the land, Trilby's ratio. Measured from the Trilby
arrival at d3: 22 enemies, 7 on the ledge, 12 on the mountain, 2 on the
shelf, 1 in a pocket, none on a solid tile. The known consequence is in the
table's comment: a wave with survivors out of reach never reads as cleared,
so a visit deals one wave; the next comes with the next entry. The "two
answers" measurement that was left open (52 vs 198 tiles) is moot - the
flood is over the whole room now.

### Five reported bugs, measured and fixed (Oct 2026)

The user's list, in their order, with what the emulator said before and
after. Every one of these was reproduced before it was touched (doctrine 8),
and two of them turned out to be something other than what the report
assumed.

**1. The starting skill: no dialogue, and the Zelda sprite vanishes.** Two
bugs under one report. The dialogue: a skill taken off the hub floor runs
vanilla's own item-get pair (`CreateItemEntity`'s `LINK_ANIMATION` +
`LINK_HOLDING_ITEM`), which reaches its textbox about ten frames after the
pick - and phase 5 ended with a `RELOAD_ALL` three frames after the pick,
which recycled the pair before it spoke. Measured both ways: with the reload,
`gMessage` never opens and the player's action never leaves `PLAYER_NORMAL`;
without it, "You learned the secret Spin Attack fighting technique!" prints
and closes on A. The reload was the combat room's clean slate and had no job
left, so it is gone. (An explicit `InitItemGetSequence` was tried first and
produced the line twice - the vanilla pair was never broken, only killed.)
The sprite: the "Choose one of these items!" sign is a ZELDA NPC that
`QuickStartDeleteGroundItemsAndSigns` tore down with every row, and only the
phases that spawned a next row put it back - so it vanished after the FIRST
pick, not the third; the user noticed it at the third. It is respawned by
every phase now, and after the last pick it stays with a goodbye line
(`script_QuickStartChosen`, custom string 194). Found along the way:
`QuickStartItemGetCutsceneRunning` has never once returned TRUE - both halves
of the pair are aux player entities, invisible to a `gEntities` scan - so
every phase has advanced two frames after its pick since the hub was built.
Left as it is, documented at the function: the rounds are proven with it
answering FALSE.

**2. Walk out of a wave room and back in, three times, and the reward
drops.** Reproduced exactly (`scratchpad/wave_reentry.py`: enter, warp out
to Castle Garden, re-enter - wave 0, 1, 2, reward, no kills). The seam-
gauntlet record (`GF_SEAM_GAUNTLET_*`, FLAG_BANK_11) survives the room on
purpose, because a seam scroll wipes the room flags mid-fight; but a door is
not a seam. Leaving through one deletes the wave, and the next visit found a
live record whose wave had "no enemies left" - so it cleared, advanced and
dealt the next one. The tell is the enemies: across a seam they persist
(`ENT_PERSIST`; the leash hauls them back), so a record - or a survive clock
- with NONE of ours alive on its first frame in the room is a fight that was
walked out on. `QuickStartSetupWaveRoomContent` reconciles once per visit
(`QUICKSTART_WAVE_ROOM_SYNCED_FLAG`, flagBase+7, the window's last bit):
forget the record, clear `GF_SURVIVE_LIVE` and the clock. After: four
re-entries, wave 0 every time, no item. The survive variant was caught in
the same measurement (every other re-entry rolled it) and resets the same
way.

**3. Tingle's fusion: too many boxes.** Tingle's, then Ezlo's, then the
container's. Ezlo's (`CreateEzloHint` of custom string 203) is cut from
`QuickStartTinglePayout`; the string stays in the table unreferenced.

**4. A chain step's reward can be lost.** The step completed wherever the
last enemy died, Ezlo's hint for the NEXT step played, the item dropped at
the player's feet, and a player who had already walked off left a KEY item
on a floor the room load wiped - with the next step already priced against
owning it. The user's two options were "force it on the player or make it
persistent"; forced is what shipped, and it is vanilla's own hand-over:
`QuickStartChainMonitor` now runs `InitItemGetSequence` (the routine every
swordsman's `GivePlayerItem` runs) - Link holds it up, the item-get line
plays, `GiveItem` lands it, nothing touches the floor. Direct-grant
equipment (swords, keys) keeps its direct grant. Both the payout and
`QuickStartChainHintOnce` wait on one test, `QuickStartPlayerCanBeHandedItem`
(normal action, not busy, not swimming, no queued action, no textbox, no door
firing), which is what puts the hint AFTER the item instead of before.
Measured in Castle Garden: the sequence from our frame context gives the
pose, the text, the item (Bow 0 -> 1) and the player back in 219 frames. One
caveat from the measurement: fired while Ezlo was mid-sentence it did
nothing and left the player stuck - exactly the window the guard refuses.

**5. The Crenel Base boss, squeezed in by the entrance.** Removed, not moved,
and the user leaned that way: the region's arrival component is the 52-tile
ledge, the reward spot the boss spawns at is ten tiles along it, and every
larger space on the mountain is behind the bombable wall or the climb.
`QuickStartRegionAllowsBoss` says no for `ROOM_MT_CRENEL_ENTRANCE`, which the
BOSS carrier, the chain's BOSS step and the wave loop's 10% roll all already
consult - the same way the mountain's wave rewards were withdrawn earlier.
`boss_arena.py` still lists the room as a candidate; it is a parity tool,
not an allowlist.

### Vanilla mechanics re-purposed, and the maze doors walked (Oct 2026)

The user's go-ahead on `docs/QUICKSTART_GUIDE_FINDINGS.md` §4 (everything
but the four shops and Simon's gauntlet) and on the Royal Valley maze
proposal, plus two corrections of theirs: the leaves to Minish Village need
Minish form and nothing else (confirmed in play), and a drained Castle Garden
fountain opens TWO entrances - one for full-size Link and one only a Minish
Link fits through. The survey rows carry both terms now.

Reading the ROM before writing anything: five of the eleven mechanics were
already live (the golden trio in the Elites tier, the three Joy Butterflies as
STAT rows, the thieving crows, cross-region fuser scatter, the item-reactive
enemies) and the Ocarina-as-entrance rule was already the wind-crest
treatment. What shipped new, with its measurement:

* **The maze costs knowledge, not kit.** The route was already a per-run
  function of the seed and the signs already read it out, so the Lantern was
  never the gate. Six rows lost `LANTERN + MAZE` (the valley north of the
  maze and Dampe's house are FREE; the graveyard side costs the key alone;
  the crypt the key and the Bracelets), the gated-zone row asks for the key
  alone, and `QuickStartMazeMonitor` has Ezlo speak each pass's direction
  (custom strings 190-192) to a player with no Lantern. The doors were walked
  in the shipped ROM, since a comment in the zone table claimed containment
  cancelled them: the south door at (120,808) goes in, the maze's south border
  comes out. (The first walk stood the player in the trees at (120,700) and
  went nowhere; the collision dump found the path, which is what a failed
  control is for.) The comment was wrong and is corrected.
* **Fickle fusers, and shared offers.** `QuickStartSpawnRegionFusers` rolls
  each room's second and later fusers against 4% per difficulty point from
  difficulty 2 (0% at 1, 48% at 12 - `QuickStartFuserFickleChance`); a
  fickle one is a talk-only NPC with vanilla's "not in the mood" shrug
  (string 189). The room's first fuser always fuses, so no room goes dark.
  The offers are also permuted per room per run (a keyed Fisher-Yates over
  the room's unfused ids), so the same spot pays different fusions across
  runs - vanilla's shared-fusion shape without its pool bookkeeping.
  Measured with `callrom`: the roll lands 13.2% at d3 and 44.0% at d12 over
  400 draws each; across all 18 regions the ZELDA-faced fuser census goes
  36 fuse / 12 talk at d3 to 30 / 18 at d12. (The first census, filtered on
  the ZELDA id, found nothing - fusers wear cast faces. The interaction
  table's candidate type is the honest reading: 2 fuses, 1 talks.)
* **Dark wave rooms.** 5% per difficulty point (15% at d3, 60% at d12),
  rolled once per visit with the room's variant and applied every settled
  frame (`QuickStartDarkRoomRoll`/`Apply`, room flags 48/49). The engine's
  own darkness: `sub_0805BB00(0x80, 1)`, the Lantern widens the circle, the
  room loads light again. Measured: mean screen brightness 148.5 -> 86.0 on
  apply, unchanged on a control call with the flag clear, idempotent on a
  second call. (The first measurement showed no change at all and was the
  harness - `callrom.call` clobbers the game context; `call_keep` is the one
  that lets frames run afterwards.)
* **The Great Fairies' honesty tests.** The Minish Woods and Crenel fairy
  rooms keep their vanilla fairy and orchestrator (site dispatch skips them),
  the vanilla scripts ask their questions, and the reward branch under
  `QUICKSTART` is ours: a RARE draw at the player's feet
  (`QuickStartFairyHonestyReward`), her thanks (string 193), the vanilla
  fade-out, and the site's DONE bit. Their `IZUMI_*` flags are cleared at run
  start. **The measurement that mattered:** the entity scan found both rooms
  holding the fairy and NO orchestrator - `cutsceneOrchestrator.c` deletes
  every orchestrator under `QUICKSTART`, a Castor Darknut-era sweep. It now
  excepts these two rooms (the graveyard keeps its Fountain of Sacrifice).
  After: both rooms hold both objects, and the payout function drops an item
  when called in the Crenel room. Not yet watched end to end in play; on the
  handoff list.

### The vanilla walkthrough, read against the survey

The user uploaded Banjo2553's 100% walkthrough of the vanilla game (8,730
lines) and asked four things of it: supplement the reachability survey, map
Veil Falls / Hyrule Castle / every dungeon from the guide alone, list the
vanilla mechanics worth re-purposing, and assess whether vanilla's quests can
be ported into the run. The long answer is **`docs/QUICKSTART_GUIDE_FINDINGS.md`**;
this entry records what changed in the build and the two things learned
about method.

**Seven survey rows changed, and every one of them sat on a row the survey
had already marked uncertain or derived.** That was the rule for touching the
walked data with a secondary source: the guide could tie-break a doubt the
survey had recorded, never overturn a measurement, and each change had to be
confirmed in the ROM's own data first.

* **The leaves to Minish Village are free.** The MW block carried the
  Flippers on fourteen rows as "not sure if they're gated by a story flag".
  The guide rides them to the village before the first dungeon with no items;
  `MINISH_PATHS/ToMinishVillage` authors the `LILYPAD_SMALL` objects
  unconditionally and `lilypadSmall.c` tests only `PL_MINISH`. Fourteen rows
  and Minish Village's own room requirement lost the Flippers; since the
  woods have open stumps, `gen_reach` prices the whole village route FREE now.
  The largest single reach change since the MINISH model. **Wants one walk in
  the shipped ROM** - shrink at the MW stump, ride to the village without the
  Flippers - because a wrong answer here strands a chain step.
* **The Minish Woods scrub tree was FREE on a gated door.** The flood that
  priced it reached the door; the door is opened by Fusion #13 and the mode
  clears every fusion bit at boot. Now `FUSION`. The dangerous direction, and
  the kind of error a collision flood cannot see (doctrine 7 again).
* **Castle Garden's fountains are drained by fusions, not entered through
  Minish holes** - world events `KINSTONE_18`/`_35` "remove water" at the two
  doors, both fusers live in CG. Grimblade's dojo (site 16, "never
  reachable") and the castle-cellar ladder were missing outright; both are
  bushes and a sword. The Great Fairy caves in Royal Valley and on Crenel
  Wall - content sites - had no rows; `BOMBS` and `GRIP + BOMBS`.
* The Great Fairy tree in Minish Woods lost a `FUSION` term the survey only
  "believed" was there; no world event lands on that door.

`reach.h` moved by 41 lines, all accounted for. `world_reach.py --check` and
`gen_reach.py --check` are clean; `sim_validate.py` and `invariant_check.py`
were run against the rebuilt difficulty-3 ROM (results recorded in the commit
that follows this entry).

**Seven more corrections are PROPOSED and not applied**, each with the walk
that would settle it (findings doc §1.2). The one worth saying here: **the
Royal Valley maze is a fixed six-move path** (up, left, left, up, right, up)
and the lantern only reads the signs that say so. `MAZE` is knowledge, not
kit. Retiring the token and having Ezlo speak the path is the cheapest change
available against "Royal Valley is dead content".

**The non-ring areas are mapped in `tools/quickstart/guide_reach.py`** - 11
areas, 231 rows, same vocabulary as the survey plus `KEYS(n)`, `BIG_KEY` and
`CLONES(n)`, validated against `roomid.h` (0 naming problems), with a
room-rectangle adjacency reader because dungeon rooms adjoin by door tiles
and have no transition rows. It feeds nothing; it is the map for the day Veil
Falls or a dungeon is opened. Its `--summary` is the finding: **every dungeon
from the third on is built on the sword-level clone**, which this mode cannot
pay - Palace of Winds 97% clone-gated, Dark Hyrule Castle 70%, the Crypt 57%,
the Temple 55%, the Fortress 30%; Deepwood Shrine and the Cave of Flames 0%.
Only the first two dungeons could ever be run end to end with this mode's
items.

**Quest porting: yes, as a fifth sibling of the four quests that already
ship, not as a new system.** The findings doc §6 has the full table -
eleven vanilla quests port cleanly (the courier family is seven of them),
six need geometry surgery, the rest are Hyrule Town or warps. Two
incompatibilities found by reading rather than guessing: the mode has
already spent `ITEM_QST_DOGFOOD`, `_MUSHROOM`, `_BOOK1-3`, `_TINGLE_TROPHY`,
`_CARLOV_MEDAL` and `_BROKEN_SWORD` as charms and curses, so a courier
cannot carry them; and `QuickStartIsOurNpc` deletes any face that is not
ZELDA or the room's fuser, which is every vanilla quest NPC. Sheet costs
were measured by grepping `LoadExtraSpriteData`: Smith, Percy, Talon,
Melari, Syrup and the Hurdy-Gurdy Man are two-sheet faces; Potho, Gregal,
the Moblin Lady, Dampe, Stockwell, Rem, Anju and the rest are one.

**Method, two notes.** First: the vanilla guide is a *third* source on the
world, after the walked survey and the ROM's data, and it is good at a thing
neither of the others is - it says what the player was *carrying* when a
place was reached, which is the price. Second: it could only be trusted
where it could be checked. Every row it changed was confirmed against a
world-event table, an entity list or an object's source before the survey
moved, and the seven rows it could not be checked on are proposals.

### Trilby's boss arena was the wrong pocket

The user: "the bosses are blocked from going all the way down to this part
of the room", of the southwest corner.

They were describing `QuickStartTrilbyQuirkHook`'s clamp, and it is the SAME
naming mix-up the enemy spawn table had. The box was x 32-160, y 576-704 -
tiles (2,36) to (10,44) - and every comment around it calls that "the
enclosed southwest pocket". Measured, it is the MID-WEST pocket. The room's
actual southwest corner is tiles (1,49) to (13,58), a separate body of land
below it, and the clamp was teleporting the boss back out of it every frame.

**The new box is tiles (1,36) to (11,58)**, chosen by measuring four
candidates against the room's own collision rather than by drawing a bigger
rectangle:

    current    x 2-10  y 36-44   78% walkable
    extended A x 1-13  y 36-58   71%
    extended B x 1-11  y 36-58   79%   <- chosen
    extended C x 1-10  y 36-52   88%, but stops short of rows 53-58

B is three times the area at the same density as the old box. The two halves
join along the west edge, which is continuously open from row 36 to row 58,
so the boss walks between them instead of being teleported.

**The clamp now lands on open ground.** Neither box is a clean rectangle -
the OLD one already contained 18 non-walkable tiles and 10 bad boundary
tiles, so it could park a boss inside rock, and tripling the area would only
have made that more likely. After clamping, the hook snaps to the nearest
open tile (`QuickStartFindOpenTileNear`, radius 3) and leaves the boss alone
if nothing is open nearby. That fixes a pre-existing hazard, not just the
one this change would have introduced.

**What is NOT verified, stated plainly.** Three behavioural probes were
written and all three are discarded under the usual rule, because each one
failed identically on its own control:

* borrowing a live enemy and rewriting its id to CHUCHU_BOSS - the entity
  does not survive being re-identified;
* spawning one through `QuickStartCreateWaveBoss` with `call_keep` - same;
* `boss_region.py`, the purpose-built vetting tool, reports "engaged NEVER"
  for Trilby. Rebuilding at the PREVIOUS commit and re-running gives the
  identical line, so that is the harness or a pre-existing condition and not
  a regression from this change. It does report the family composing with
  five pieces in both builds, so the boss still spawns.

So this batch has a measured arena and no in-play confirmation that the boss
now walks into the southwest. The arithmetic and the collision are checked;
the behaviour is for the user to see. `boss_region.py`'s lost engagement
detection is worth its own look - its docstring warns that an open textbox
freezes the boss's stage machine, which is exactly the kind of thing that
drifts.

### The MINISH model, encoded: 58 dead rooms become 8

The first pass at this measured the wrong thing twice and came back asking
the user to confirm a contradiction. They said "Try again." They were right
to: the contradiction was mine, not theirs, and the third measurement
reproduces all four of their own observations independently.

**What the first two passes got wrong.**

* Pass one looked for portal OBJECTS - `JAR_PORTAL`, `MINISH_PORTAL_STONE`,
  `TREE_HIDING_PORTAL` - and concluded the whole ring has five transform
  points, all boots-gated. That contradicted the user on Lon Lon and Eastern
  Hills South.
* Pass two widened to every portal-ish id in `object.inc` and "found" Lon Lon
  a free `MINISH_SIZED_ENTRANCE`. Reading `minishSizedEntrance.c` killed
  that: it tests `gPlayerState.flags & PL_MINISH` before it will fire, so it
  is a Minish-only DOORWAY. Somewhere to go once small is not a way to get
  small.
* The transform point is **not an object at all**. It is
  `MINISH_PORTAL_MANAGER`, manager subtype 3
  (`src/manager/minishPortalManager.c`), which sets `gArea.portal_mode` when
  the player stands in its proximity box. Its `type` field is the `PT_*`
  kind. Both earlier scans read only `object` lines, so they could not have
  seen one.

**The rule, now that the mechanism is right.** A region can shrink if it has
a portal manager with no `TREE_HIDING_PORTAL` sitting on top of it; if every
manager has a tree on it, the price is the Pegasus Boots, because
`treeHidingPortal.c` only opens on `PLAYER_BOUNCE` - a boots dash. Measured
per region by `tools/quickstart/minish_portals.py`:

    FREE   LLR, TRIL, EH, WW, CW, WR, MW, LH, CREN
    BOOTS  CG, NHF, SHF
    NONE   RV

All four of the user's statements check out against that table without being
fitted to it: Lon Lon free (two bare stumps, at (344,544) and (280,48)),
Eastern Hills free through its South third at (72,128), and North Hyrule
Field and Castle Garden both tree-hidden.

**How it is encoded.** `world_reach.MINISH_PORTAL` prices the shrink per ring
region and `gen_reach.expand_minish` substitutes it wherever a survey row
asked for `minish_cap`: a free region drops the token, a boots region turns
it into `boots`, and a region with no portal keeps the untestable bit so its
rows stay shut. Conservative in the one direction that matters - Royal
Valley is not opened on a guess.

**Measured over 50,000 simulated runs**, and the reach model still agrees
with the shipped ROM 402 of 402:

    rooms never reachable      58 of 159  ->   8 of 159
    ? room sites never reached 48 of 105  ->  18 of 105
    reachable rooms, strict    median 38  ->  median 55
    reachable rooms, rewards   median 66  ->  median 72

The untestable `MINISH` bit is now referenced by exactly one line in
reach.h - its own `#define`. Every destination row has been expanded to real
items.

**One live probe is discarded rather than reported as evidence.** A test that
warped the player onto each stump and read `gArea.portal_mode` returned zero
everywhere, including in the negative control, so by the usual rule it says
nothing about the mechanism - wrong struct offsets, most likely. The static
entity-list read stands on its own, and it is corroborated by four
independent observations from someone who has played the rooms.

### The MINISH model, step one: where you can actually shrink

The user answered the open question from the simulation report - yes, MINISH
should be modelled - and described the shape: "In order to reach a Minish
room ... 1) the player must have the Minish cap ... 2) there must be a tree
stump/stone/pot nearby for the player to transform into a Minish ... There
are other regions/rooms, though, where the tree stump/stone/portal is
initially hidden. Sometimes they require another item to reveal ... These
stumps are hidden underneath specials trees that the player must ram with the
Pegasus boots."

**Requirement 1 is free and requirement 2 is the whole gate.** Being Minish
is `PL_MINISH`, a player STATE, not an inventory item - there is no Minish
Cap in `item.h` to test. So what the reach model has been calling `minish_cap`
is really "can this player reach a transform point from here".

**The game ships the distinction as three object types**, so the price is
readable rather than a judgement call: `MINISH_PORTAL_STONE` (116) and
`JAR_PORTAL` (56) stand in the open; `TREE_HIDING_PORTAL` (156) is hidden
until rammed. `treeHidingPortal.c` confirms the ram: its trigger tests
`gPlayerEntity.base.action == PLAYER_BOUNCE`, which is a Pegasus Boots dash,
and `TreeHidingPortal_Init` deletes the tree outright once its flag is set.

`tools/quickstart/minish_portals.py` reads them out of
`data/map/entity_headers.s`, and an emulator scan of the live entity list in
all eighteen region rooms agrees with it exactly.

**What the ring actually has.** Five transform points, every one of them a
tree, every one of them unrevealed at boot (action 0):

    CASTLE_GARDEN_MAIN, HYRULE_FIELD_SOUTH_HYRULE_FIELD,
    HYRULE_FIELD_LON_LON_RANCH, HYRULE_FIELD_NORTH_HYRULE_FIELD,
    LAKE_HYLIA_MAIN

The other thirteen region rooms have none - including Castor Wilds, which
has SEVEN Minish holes and no way to become Minish in the room, and Minish
Woods, which has four.

**Widening the scan to every room in the game is what makes sense of that.**
42 rooms carry a transform point and 37 are free - but the free ones are
`JAR_PORTAL`s inside houses (House Interiors 1-4, Hyrule Town) and
`MINISH_PORTAL_STONE`s in late dungeons (Fortress of Winds, Palace of Winds,
Vaati 3). The overworld's only transform points are those five trees.

**Which gives the model its real shape**, and it is nicer than the flat token
it replaces: a Minish destination costs *the cheapest way to reach any
transform point that connects to it*. The survey already prices reaching
every room, so a jar portal inside the farm house costs whatever the farm
house costs - `[[BOMBS]]` from Eastern Hills North, per that block's own row.
The token stops being a magic bit and becomes ordinary composition.

**Two things the measurement contradicts, and they are recorded rather than
resolved.** The user named Lon Lon Ranch's stump as one "given freely", and
said "the player can reach the Minish room in Eastern Hills South with ONLY
the Minish cap". Measured, Lon Lon's portal is a TREE_HIDING_PORTAL at
(312,352) - boots - and Eastern Hills South has no transform point at all in
any of its rooms. The likely reconciliation is the house jar portals (the
ranch house and the farm house both have one), which would make the access
free-once-inside but priced at whatever the door costs. Confirmed before
encoding, because a wrong price here makes rooms look reachable that are
not - the failure direction the whole conservative-token policy exists to
avoid.

### Mount Crenel keeps its waves and loses its wave rewards

The decision on the previous entry's open question. The user: "disable wave
clear rewards for Mount Crenel entirely. Items should not drop when the
player kills all enemies, and a WAVE CLEAR for any of the Crenel sites
should never be a win requirement."

`QuickStartRegionAllowsWave` is the twin of `QuickStartRegionAllowsBoss`, and
three places now ask it:

* `QuickStartSpawnRegionRewardOnce` pays no clear reward there. The guard
  sits AFTER the element branch on purpose - the Earth Element may still be
  placed in Mount Crenel under a BOSS or QUEST carrier, and neither of those
  depends on emptying the room.
* `QuickStartChainWaveOk` keeps WAVE requirements off it, the same shape as
  the boss allowlist and for the same reason: a requirement a region cannot
  host is a step that can never be finished.
* `QuickStartRollElementRegionOnce` will not put a WAVE-carrier element
  there. That needed a second pre-check as well: the existing comment called
  a wave "the classic fallback, which every room hosts by construction", and
  that stopped being true the moment one room stopped hosting one. Without
  it the element loop could spin forever on a distance-2 mask whose only
  member is the mountain.

Waves still SPAWN on Crenel. The mountain is not meant to be empty and
fighting in it is fine; what is withdrawn is everything that depends on
counting the room to zero.

**Measured in the ROM, with controls.** Forcing a clear in each region and
reading `gSave.reward_drop_x/y` - which only `QuickStartSpawnRegionRewardItem`
writes: Mount Crenel stays (0,0) after a clear, Trilby pays at (360,360),
Lake Hylia at (40,440). The controls are the point: a probe that reports "no
payout" everywhere proves nothing.

Simulated over 4,000 runs with `sim.py` taught the same rule: **0** WAVE
steps placed in Mount Crenel out of 9,956, and **0** WAVE-carrier elements
there, while BOSS (239) and QUEST (115) carriers still use it.

### Where enemies spawn: Trilby, Lake Hylia, and the Mount Crenel problem

Three user reports about spawn coverage, two fixed and one that turns out to
be a design decision rather than a bug.

`tools/quickstart/spawn_spread.py` is the tool: flood the room's collision
from the tile the player actually arrives at, farthest-point sample the LAND
in that component, and report coverage before and after. `--map` prints an
ASCII coverage map with tile indices, which is what located the bare ground
in seconds instead of by eye.

**Land, not "walkable".** Lake Hylia's water is walkable COLLISION, so a
flood alone happily proposes the middle of the lake. Its arrival component
is 1586 tiles and only 617 are land. The act tile is what tells them apart
(`mapActTileToSurfaceType.c`), and the proposer rejects pit, slope, ice,
swamp and both water tiles. Castor Wilds' swamp is the same trap in the
other direction, already known from the drop-site work.

* **Trilby Highlands**: 28 spots covering 66% of its 923 land tiles. The
  bare block was tiles (1,48)-(13,58) - the southwest corner the user named.
  Worth noting the existing rows labelled "the southwest pocket" are a
  DIFFERENT pocket up at rows 35-43, which is why the area read as served.
  48 spots now, **100%**.
* **Lake Hylia**: 16 spots, all inside x 24-296 y 104-456 of a 48x60 room,
  covering 35% of the land. 39 spots now, **93%**. The proposer runs out of
  legal candidates before 48 - that is the lake, not a bug.
* **Eastern Hills North boss spot**: moved from (264,264) to **(128,272)**.
  Measured rather than eyeballed: the largest square of clear, non-water,
  in-component tiles in the room is TEN tiles on a side, spanning x 3-12 by
  y 12-21, and (128,272) is its centre. The old spot was tile (16,16) inside
  a six-tile block on the far side of the dividing wall - and not the field
  the farmhouse looks out on, whose door the survey puts at y 136, directly
  above the new square.

**Mount Crenel cannot be expanded the same way, and the reason is worth
recording.** Its arrival component is **69 tiles of the room's 831**. The
other components - 402, 244, 47 and 29 tiles - are the mountain proper, and
the current ten spots already cover 100% of the strip the player arrives in.

The room holds 21 climb-wall act tiles and none of them bridges two
components. What DOES reach the mountain is the cave network: twelve
transitions land inside this room at scattered coordinates - (312,328) from
CRENEL_CAVES_MUSHROOM_KEESE, (408,232) from HELMASAUR_HALLWAY, (184,424)
from BOMB_BUSINESS_SCRUB, (728,408) from LADDER_TO_SPRING_WATER, and so on.
So a player reaches those components by LEAVING THE ROOM and coming back out
somewhere else, and most of those caves are priced at bombs or the Grip Ring.

That matters because `QuickStartRegionWaveCleared` returns FALSE while ANY
enemy is in the room. One enemy dealt onto the mountain is a region that can
never be cleared for a player without the cave's key - which blocks the
chain step, the region reward, and possibly the run. So the spots were NOT
expanded, and the decision goes to the user: gate the extra spots on the kit
that opens the matching cave, or scope the wave-clear test to the player's
own component. Either is a real mechanic change, not a table edit.

**GFX cost checked.** Spreading spawns across more of a room loads more
sheets. Trilby falls from 15 free slots to 3 and Lake Hylia from 20 to 11;
every region room is still above `QUICKSTART_GFX_HARD_FLOOR`, and the
GFX-aware enemy ceiling from the previous batch is what keeps it that way.

### Lon Lon's two slots, bought properly

The face batch left Lon Lon Ranch one slot under the GFX floor, and the
choice was to live with it or find out where the room's slots actually go.
The user picked finding out. It was the right call: the answer was not the
faces at all.

**Dumping all 44 slots settled the question in one run.** `GfxSlot` carries
`slotCount` and `referenceCount` (include/vram.h), so a dump attributes
every slot to its owner:

* 4 slots pinned by the system (referenceCount 128).
* 8 in status 3, `GFX_SLOT_FOLLOWER` - and these are NOT free, they are the
  tails of multi-slot sheets. Slot 5 has `slotCount` 4 and owns 6, 7 and 8;
  slot 13 has 3 and owns 14 and 15. The accounting is honest and
  `QuickStartReclaimableGfxSlots` is right to exclude them.
* ~10 for the room's own content.
* 2 for the fuser face, shared by all eight fusers (referenceCount 8).
* **19 for 19 enemies, one slot each.**

That last line is the finding. Enemies arrive through `LoadSwapGFX`, not a
shared sheet, so nineteen enemies of a SINGLE kind held nineteen of the
forty-four slots. The per-room `sQuickStartRegionSheetBudgets` lever does not
bind here at all, because it limits distinct KINDS and the cost is per
ENTITY.

**So the ceiling was wrong, not the cast.** `QuickStartRoomEnemyCeiling` was
`14 + roomSquares / 50`, capped at 28. Lon Lon is a big room, so its area
earned it 28; its sprite table can afford about 21 once the room's content
and one face are paid for. The wave took 23 and left 1.

The ceiling now also asks what the table can still spend - what the wave
already holds, plus what is reclaimable, less the hard floor and the sheets
a face still has to buy - with a floor of `QUICKSTART_ENEMY_CEILING_MIN` so a
wave can never be starved into never clearing.

Measured after: Lon Lon goes from 0 free slots to **4**, double the floor,
and its wave peaks at 19 enemies instead of 23. Every other region room is
unchanged and in double digits; the new term only binds where the table is
actually tight. That is the whole point of pricing against the resource
instead of against room area.

### The GFX bill for faces that actually draw

The face batch above broke `invariant_check.py`'s GFX floor in two rooms, and
chasing it down was worth more than the fix.

**North Hyrule Field: two sheets, not one.** Five of the twelve faces call
`LoadExtraSpriteData` and so cost a SECOND sprite sheet - KID (the user's own
"working well" example), CASTLE_MAID, TALON, MUTOH and GORMAN. NHF fell from
7 free slots to 1. The cast is seven now, six of them single-sheet, KID kept
because the user named it: ZELDA, POSTMAN, WHEATON, PITA, REM, ANJU, KID.
TALON and MALON are also out for a second reason - they are Lon Lon Ranch's
own vanilla residents, and `QuickStartIsOurNpc` spares any scripted NPC
wearing the room's drawn face, so drawing Malon in Lon Lon would have spared
the vanilla Malon from the region sweep.

**The tutorial ramp is hand-tuned for a reason.** Generating steps 0-2 from
the same gaussian widened step 0 from `{ 100, 0, 0, 0, 0, 0 }` to
`{ 58, 36, 6, 0, 0, 0 }` - three levels of enemy kinds instead of one, each
kind its own sheet. Those three rows are fixed data again; the brief starts
at difficulty 3 and step 3 is unchanged at 65/26/9.

**Two wrong turns, both instructive.**

* A room flag was claimed for a "wear the plain face" latch without checking
  the number. 46 is already `QUICKSTART_REMAINDERS_SWEPT_FLAG`, so setting it
  made Lon Lon skip `QuickStartResetOtherWaveRemainders` - a wave bug wearing
  a GFX bug's clothes, and it corrupted an hour of measurements. The defines
  are scattered through 24,000 lines; grep `_FLAG [0-9]` before claiming one.
* The plain-face idea was wrong anyway. `git show`-ing the pre-commit build
  and reading the live NPC ids showed Lon Lon used to wear STURGEON - one of
  the four BROKEN faces - and had 2 free slots. The old faces were cheap
  because they were broken: a face whose sheet never loads costs nothing.
  Lon Lon's "pass" was an artifact of the bug the user reported.

**What actually fixed it: wait for the room to finish loading.** The fuser
set was placed the frame the room settled, while the loader still held the
previous room's sheets. Deferring until the room can pay for the face and
still hold `QUICKSTART_GFX_HARD_FLOOR` removed the dip everywhere except Lon
Lon. The first attempt gated on `QuickStartGfxBudgetForNewKind` (more than 4
free) and STARVED Lon Lon, whose ceiling is exactly 4 - eight fusions with no
sprite, forever, because a retry that can never succeed is a deletion. Caught
by counting NPCs after the change rather than trusting the GFX number.

**What is left, and it is a real trade-off, not an oversight.** Lon Lon Ranch
tops out at 4 reclaimable slots and a working face costs 3, so it dips to 1
against a floor of 2 for about a second on entry, then settles at 4. The room
cannot host a face that renders AND keep the floor. The floor exists so a
boss spawn can find sixteen slots; Lon Lon never has sixteen and defers
either way, so the practical cost of the dip is likely nil - but that is a
judgement about the guard, so it is recorded here rather than fixed by
quietly lowering it.

`tools/quickstart/gfx_floor.py` is the tool this produced: the invariant
check's own GFX measurement for one room at one difficulty, so a change can
be iterated in a minute instead of the twenty-five the full sweep takes.

### Faces that actually draw, and a difficulty curve that gates nothing

Two user reports, both about variety, both fixed by measuring instead of
reading tables.

**Four of the eight fuser faces were drawing garbage.** The user: "The 'Kid'
and 'Postman' sprites are working well. The other two are having
visual/GFX glitches." Measured: TPWNSPERSON, BEEDLE, BROCCO and STURGEON are
all broken; ZELDA, KID, POSTMAN and MAID are all fine.

Nothing in the tables predicted which. A broken face is placed, carries a
sprite index, and passes every check `hub_variety.py` makes - it just
renders as scrambled tiles, because its sheet is not in the room's loaded
gfx group and the OAM indexes into whatever is. The first cast was picked by
reading the NPC enum for "ordinary standing townsfolk", which is exactly the
kind of table-reading this project keeps getting caught by.

`tools/quickstart/fuser_faces.py` is the fix for that. It forces each cast
slot by SEARCHING A RUN SEED rather than patching - `QuickStartFuserCastId`
is `(((run_seed >> 3) + roomIndex * 5) & 0x7fff) % count`, so for a fixed
room a seed exists for every slot and the shipped path runs unmodified - then
brings the face to the camera and saves a PNG. Thirty-six candidates were
drawn that way.

The cast is now twelve faces, every one of them looked at:

    ZELDA, KID, POSTMAN, MAID, TALON, MALON,
    MUTOH, GORMAN, WHEATON, PITA, REM, ANJU

Three that render correctly are still excluded, because they bring their own
furniture: Stockwell arrives behind his shop counter, the hurdy-gurdy man
with his organ cart. Both look absurd standing in a field.

One trap on the way: growing the cast from 8 to anything else broke the
link with `undefined reference to '__umodsi3'`. `QuickStartFuserCastId` used
an unsigned `%` by `ARRAY_COUNT`, which agbcc turns into a mask only when
the count is a power of two. Signed modulo on the masked value, the same
shape `QuickStartRegionDropSpot` already uses.

**Difficulty was gating content, not weighting it.** The user: "The
difficulty scaling should not be about what tiers or types of enemies are
possible, but rather the chance that various tiers spawn. At difficulty
three, the majority of enemies should be sampled from the lower tiers, but
we should still be seeing enemies from the higher tiers on occasion."

The old table read `{ 30, 50, 20, 0, 0, 0 }` at difficulty 3. Levels 4 and 5
and the Elites were not rare at the shipped difficulty, they were
IMPOSSIBLE - a hard unlock gate wearing a weighted die's clothes. A player at
the baseline could finish a run having met 42 of the roster's 71 entries and
never learn the other 29 exist.

The curve is generated now, by `tools/quickstart/tier_curve.py`: a discrete
gaussian over the six columns whose peak walks from level 1 at step 0 to
level 4 at step 12, with the Elite column damped to 18% of its natural
weight and a per-column FLOOR. The floor is the part that answers the brief -
a gaussian alone puts 0.4% in level 5 at step 3, and integer rounding turns
that back into the same gate. From step 3 up, no column is ever zero.

Difficulty 3 now deals 65% from levels 1-2, 26% level 3, and 9% from levels
4, 5 and the Elites together.

The Elite column stays tiny at every step, and that is not timidity: four of
its six entries are Darknut forms, so it IS the Darknut dial, and the pile
of five Darknuts the user reported is what the wave rework exists to
prevent. At step 12 it is 4%. Level 5 climbs much higher (35% at the top)
because it holds no Darknut any more - it is Wizzrobes, the golden variants
and the Wisps, eleven entries wide. That is the one number this batch
changed most from the old table's "level 5 tops out at 7%", and the reason
that cap existed no longer applies.

Density is untouched: the user asked about WHICH enemies spawn, not how
many, and that column is tuned against the entity budget.

**Both changes are measured, not asserted.** `tier_curve.py --check`
compares the table in game.c against the generator and asserts the sums, the
floors and that the mean level never falls as difficulty rises.
`tools/quickstart/tier_mix.py` goes further and measures the ROM: it walks
into region rooms, lets the wave spawn, and maps every live enemy back to
its roster level. Over 1,216 live enemies at difficulty 3 across ten rooms
and six seeds it reports L1 30.2%, L2 30.2%, L3 28.1%, L4 9.8%, L5 1.6%,
Elite 0.2%.

Worth noting that the measured mix is NOT the table's own numbers - L1 runs
higher and L2 lower than the weights say. That is the archetype composition
builder and the live caps reshaping waves after the level is rolled, which is
working as designed. The table sets the draw; it does not set the outcome.
The number that matters is that the top three columns are 11.6% of spawns
where they used to be exactly 0.

### The second pass: three of four findings were wrong, and a reader caught them

The 50,000-run report went out with four headline findings. The user read it
and pushed back on three of them, and was right on all three. This entry is
the correction, the fixes it produced, and a re-run at 100,000.

**What was asked for, and shipped.**

* **The quest guard is fixed.** `QuickStartChainCountCandidates` now asks
  `!QuickStartChainAlreadyUsed(step, QS_CHAIN_QUEST, (u8)QuickStartQuestSlot())`,
  matching what `QuickStartChainStore` actually writes. The duplicate-quest
  rate goes 31.7% -> 0.
* **Bombs join `QS_CAT_KEY`.** The row is `QS_CAT_WEAPON | QS_CAT_KEY`, so
  bombs stay a weapon for the shop and the "? room" drop pool and are a key
  item everywhere reach is decided: hub round 1 can offer them and a chain
  ITEM step can grant them. `cat` was already a mask at every call site but
  two - `QuickStartChainPickItem` used `==` and `!=`; both are mask tests
  now. Fourteen bomb-priced rooms come back into the chain's reach,
  including the whole of Mount Crenel's base.

**Correction 1: the reachable world DOES grow.** The user: "If the player
clears a wave or a boss, then they are granted an item. Wouldn't that expand
the reachability for the run?" Yes. `QuickStartSpawnRegionRewardItem` draws
`QuickStartDrawItem(Random() & 0x3f, QS_CAT_ALL)` and `QS_CAT_ALL` includes
key items, so a region clear is the one draw in the mode that can hand one
over - and every WAVE and BOSS step is a region clear. The chain rolls one
step at a time off the live inventory (`QuickStartChainRollStep` is called
from the previous step's completion), so the placer sees those grants.

The first report's `found` cohort was a hand-wave - "one unheld key item per
completed step" - and its `strict` cohort was defined to pick nothing up. Of
course strict was flat; that was a tautology dressed as a finding. The
`rewards` cohort now models the real draw: six bits of seed, 64 equiprobable
outcomes, the real 60/30/10 tier curve, the real `QuickStartTierEntryUsable`
tests including the two region-gated quest keys. Measured: a run goes
**39.6 reachable rooms after the hub to 54.2 by the fourth requirement**.

The ITEM step is still never dealt - 0 in 500,000 requirement rolls - and
that is still worth a decision, because it is the only GUARANTEED grant in
the chain while everything a region clear pays is a draw that might be a
bottle. But it is not load-bearing for growth, which is what the first pass
claimed.

**Correction 2: two region entry prices were wrong, and the cause is
structural.** The user: "Hyrule Castle Garden is always guaranteed to be
reachable - it directly connects to NHF with no item requirement... On the
other hand, Royal Valley requires the power bracelets to be able to reach."
Both correct, and the evidence for both was already in our own tables.

`gen_reach` built `sQuickStartReachRegion` from each survey region's
`room_req`. That field is the cost of moving around INSIDE a region once you
are standing in it - it is not the cost of the crossing. For a region whose
entry price is recorded as an exit row in its NEIGHBOUR's block, the price
was simply never read.

* **Castle Garden had no survey block at all**, so it fell through to
  "never". The one region of the ring that costs nothing to walk into was
  the one region the chain believed it could never reach: 7% of runs,
  which is exactly the share that DROP there. It has a block now (derived
  from transitions.c and the site table, not walked - marked as such), and
  it is reachable in 100% of runs and hosts 5.3% of requirements.
* **Royal Valley was priced FREE** and counted reachable in 100% of runs.
  Its only way in is North Hyrule Field's WNW border, and NHF's own block
  prices the walk to that border at `[[BOMBS, BRACELETS]]` - it is behind
  the TO_GRAVEYARD pocket. Trilby's N port is a link on paper only: TRIL's
  first row is that pocket, marked "only reachable from Royal Valley", so
  the crossing runs one way, out of the valley.

The fix is `world_reach.ENTRY`, a small explicit table of crossing prices
that `gen_reach` prefers over the `room_req` derivation. The report prints
every region's entry price for audit, because that is how these two were
caught.

**A consequence worth a decision: Royal Valley is now nearly dead content.**
Reachable in 7% of runs, hosting 0.2% of requirements. That is the honest
number rather than a bug, but a whole region - graveyard, maze, dojo - is
now something most runs never see. The lever is the toll.

**Correction 3: "reachable" was measuring the wrong thing.** The user: "We
are not simply concerned with whether the player can walk into the entrance
of a region but whether or not they can explore the rooms in that region."
`QuickStartReachPoolOk` asks only whether the player can be INSIDE a region,
and that is also the test the chain uses to decide where a WAVE or BOSS step
may go. Mount Crenel is free to enter and everything past the entrance wants
the Grip Ring, so a region-count metric scored the mountain as wide open.

Every checkpoint now records reachable rooms PER REGION, and the report
carries an "entered is not explored" chart and table. Mount Crenel: enterable
in 100% of runs, median 10% of its rooms actually reachable.

Two honest caveats on that measure, both stated in the report. The
denominator is every room the survey attributes to the region, and a large
share of those are Minish rooms the model can never count, so a low
explorable share is partly about the region and partly about the `MINISH`
token - North Hyrule Field's 8% is mostly the second kind. And the placement
semantics are NOT changed: a wave spawns around the player, so an entrance
strip is arguably fine for one; a boss spawns at the region's fixed reward
spot, so for a boss it matters. That is left as a decision rather than
taken unilaterally.

**What the corrected sweep says.** 100,000 runs (50,000 per cohort) in 1m43s
- the first version's per-region loop re-scanned all 273 destination rows per
room and took 25 minutes for half the sample; indexing the table by room
made it 60x faster with the same answers (`sim_validate.py`: 402/402 against
the ROM). Dead rooms fall from 69 of 154 to **58 of 159**, and `MINISH` is
now 47 of those 58 - the one remaining decision that would move the number.
Run variety is healthy: 61,950 distinct requirement-region sequences, the
most common at 0.01%.

**The doctrine.** Every one of the three errors was a faithful simulation of
what the code does, reported as something it does not mean. The model was
right and the interpretation was wrong, which is the failure mode a
validator cannot catch - `sim_validate.py` agreed with the ROM at every
stage, including while the report was saying the world never grows. What
caught it was a reader who knew the world. So the report now prints its
inputs - the full entry-price table above all - for exactly that kind of
audit, and keeps its own wrong answers on the page under "What the first
pass got wrong" instead of quietly overwriting them.

### 50,000 simulated runs: four things the model says out loud

A full-run simulator now exists. `tools/quickstart/sim.py` reimplements the
parts of the mode that are driven by `gSave.run_seed` and nothing else - the
three hub selection rounds, the drop-region roll and its kit redraw, the
carrier and element-region rolls, the quest slot, and all five iterations of
`QuickStartChainRollStep` - and measures reachability at the five checkpoints
the user asked for: after the item selection and after each of the first four
requirements. `tools/quickstart/sim_validate.py` calls the ROM's own
`QuickStartReachRoomOk` through `callrom` on random (loadout, room) pairs and
the model agrees **302 of 302**, so what follows is the shipped gate's answer,
not a Python approximation of it.

Two cohorts, run 25,000 each. `strict` holds only the three hub picks plus
whatever the chain's own ITEM steps hand over - exactly the placer's view, and
a floor. `found` adds one unheld key item per completed step plus the fusion
bit, standing in for drops picked up on the way - a ceiling. Where they
disagree, the gap IS the finding.

Full write-up and nine charts: `docs/QUICKSTART_SIM_REPORT.md`, `docs/sim/`.
The 70 MB run dump is not committed; `sim.py` regenerates it in about seven
minutes.

**1. The ITEM fallback never fires.** Across 250,000 requirement rolls, the
chain dealt ITEM **zero times**. There is always at least one placed
candidate for one of the other four kinds, so the branch the code calls "the
guaranteed floor and the reason the chain can never wedge" has never once
been taken. It is not wrong - it is unreachable.

**2. Therefore the reachable world does not grow.** This is a direct
consequence of (1), and it is the most important number here.
`QuickStartChainPickItem`'s own comment says an ITEM step exists so that
"finishing the step GROWS the sphere, which is what lets the next step be
placed further out than this one was". With no ITEM steps, no chain step ever
grants a key item, and clearing a WAVE, BOSS, EVENT or QUEST grants nothing
the reach model can see. In the strict cohort the reachable-room count is
**identical at all five checkpoints** - 39.5 rooms, 10.46 regions, start to
finish. The intended escalation is not happening; a run is exactly as large
at the Earth Element as it was walking out of the hub. (The `found` cohort
grows 39.5 -> 66.8, which says the growth that does happen comes from loot
the placer cannot count on, not from the chain.)

**3. 31.7% of runs are dealt the side quest twice.** 15,827 of 50,000. There
is one quest per run, so the second copy is already satisfied when it lands
and the run silently loses a step. The cause is a two-line mismatch: the
guard asks `!QuickStartChainAlreadyUsed(step, QS_CHAIN_QUEST, 0)` but the
store writes `gSave.chain_where[step] = (u8)QuickStartQuestSlot()`, so the
guard only matches when the slot happens to be 0 - 1 case in 18. The
simulation confirms the reading exactly: of the 15,827 duplicate runs,
**zero** had slot 0. The comment above the guard reads "One quest per run",
so the intent is not in question.

**4. 69 of 154 rooms and 58 of 105 ? room sites are never counted
reachable.** Read this one carefully, because the obvious reading is wrong:
these rooms are not sealed in the world, and a player can walk into most of
them. What is true is that `QuickStartReachRoomOk` never returns TRUE for
them under any loadout a run can assemble, so the chain can never place a
requirement there and the mode believes they are out of reach. Two causes
account for 56 of the 69:

* **`MINISH` has no run-time test (42 rooms).** Being Minish is a state, not
  an inventory item, so `QuickStartHeldReachMask` can never set the bit and
  every term containing it is permanently false. That was a deliberate
  conservative choice; this is the first measurement of what it costs.
* **Bombs are not a `QS_CAT_KEY` item (14 rooms).** Neither a round-1 hub
  offer nor a chain ITEM step can ever hand them over, so every bomb-priced
  room is outside the chain's reach. Mount Crenel's base - freshly surveyed,
  blessed and wired up - is the clearest casualty: its entire cave network is
  priced at bombs, so none of it can host a requirement.

The rest: 3 MAZE, 3 BOULDER-ish, 2 UNSURVEYED, 2 with no survey row at all
(`CASTLE_GARDEN/MAIN`, `RUINS/ENTRANCE`), 2 priced `never` outright.

**What the distribution looks like where it does work.** Host regions are led
by Trilby 13.6%, Lake Hylia 13.6% and Eastern Hills 12.7%; the tail is Castor
Wilds 1.3%, Wind Ruins 1.1%, Castle Garden 0.4%. Twelve open-field rooms host
about 6.5% of all requirements each, and twelve ? room sites carry roughly
8.6% each - those are the staleness watchlist. Run-to-run variety in the large
is fine: 38,037 distinct requirement-region sequences across 50,000 runs, the
most common accounting for 0.06%.

Two systems key off the live RNG stream rather than the run seed, so no
seed-driven model can name what a particular run gets; the report gives the
distribution the tables deal instead. ? room kinds in sixteenths: SMALL is
7 WAVES / 3 NPC / 3 POT_LOTTERY / 1 FAIRY, LARGE is 7/6 MINIBOSS/2 GATE/1,
ANY is 4/5/2/1/3/1. Enemy rosters by tier: 10/15/17/12/11 distinct kinds for
levels 1-5, so a difficulty-3 run has roughly forty in play.

Nothing here is fixed yet - this entry is the measurement. (1)+(2) are one
design question (should the chain grant key items, and if the ITEM branch is
meant to be the mechanism, why is it never picked), (3) is a one-line fix,
and (4) is two policy calls: whether bombs join `QS_CAT_KEY`, and whether
`MINISH` becomes testable.

### The 09/28 survey: Minish Woods, walked

The user walked Minish Woods from the west-central seam and sent the
measurements. The region's block in `world_reach.py` was flood-derived
guesswork; it is a real survey now - 27 destinations against the old 11, and
only four still carrying `unsurveyed`. Minish Woods goes from 77% of its
traversal matrix unmeasured to **31%**, which makes it the best-measured
region in the game.

**The shape of the region is not what the flood suggested.** Most of Minish
Woods is not reachable from the seam at all: it is reachable through MINISH
VILLAGE, which is reachable through a Minish path, which wants the Minish Cap
and (probably) the Flippers. Nine destinations inherit that, which is why a
region that looks like open woodland prices most of its contents at two key
items.

Three things the survey changed beyond the table:

* **The Minish Village story is pre-cleared at boot** - entrance scene seen,
  Gentari talked to twice, and Festari moved out of his doorway. The survey
  named that last one as a gate; the mode pays it for the same reason the
  Crenel bean is pre-grown, so the FESTARI row carries no story token.
* **Ezlo's two Minish-portal lectures are marked as already heard**
  (`MORI_00_KOBITO`, `MORI_ENTRANCE_1ST`) - the user's "Ezlo scene that plays
  out whenever Link approaches the tree stump". The portals themselves are
  untouched: the survey routes half the woods through one.
* **A note on the start.** The user described the west-central seam as the
  one "shared by Lon Lon Ranch". The ROM says Eastern Hills - the west border
  rows go to EH North and EH South - and `region_walk.py` has driven both
  directions for real. Lon Lon is flush against the woods' NORTH edge with no
  border row at all. Treated as a slip about which neighbour rather than
  which seam, since the coordinates match the west-central one exactly, but
  worth confirming: if there is a Lon Lon crossing there, the region graph
  gains an edge.

**Minish Village is walkable in `mapexplore` now.** The user could not get in
from the south and described horse carts across the road. The carts are real
(FURNITURE objects at local (500,872) and (540,872)) and deleting all three
of the room's FURNITURE entities changes nothing: their collision is baked
into the room's TILEMAP - the same thing the smithy's "big invisible
barriers" turned out to be. Flooded from the south arrival the pocket was 31
tiles of a 1009-tile room, sealed by two solid rows at ty 54-55.
`MapExploreOpenMinishVillage` opens those rows by collision only, leaving the
art, so the carts are still drawn and simply walked through. After: the same
arrival reaches **952 of 1023** tiles. MAPEXPLORE only - the run still meets
the real wall, and enters the village by the Minish path the survey measured.

**Still unmeasured in the woods:** the Witch's Hut, the north Minish cave,
the fusion beanstalk, and the north border into Lake Hylia. Also flagged: the
business scrub's tree is recorded FREE because the collision flood reaches
it, but KINSTONE_27's world event fires at exactly that door, so it may be
fusion-revealed and the row wrong.

### Four asks: faces, landings, wanderers, and a shelf in the doorway

**The fusers wear eight faces now, not one.** `sQuickStartFuserCast` -
Zelda, a townsperson, a kid, the postman, Beedle, Brocco, Sturgeon, a maid -
and a room draws one per run. ONE PER ROOM rather than one per fuser, and
that is the GFX budget talking rather than taste: every NPC id costs a
sheet, and four faces in a room would cost four in a mode that already
defers boss spawns waiting for sixteen slots. A room-wide draw keeps the
cost at the single sheet the Zelda-only rule had. Nothing in the cast is a
story actor, a swept animal, or an id the mode already means something by.

That broke the sweeps, which is worth naming because the fix is not the
obvious one. `QuickStartClearEasternHillsNpcs` deleted every NPC whose id
was not ZELDA - exact while every QUICKSTART NPC was a Zelda, and fatal to a
fuser the moment it was not. Widening it to the whole cast by id alone would
also have spared a VANILLA townsperson wearing the drawn face, so
`QuickStartIsOurNpc` asks for the scripted bit as well: `StartCutscene` sets
`ENT_SCRIPTED` on everything this file makes talkable or fusable, and a
vanilla NPC standing in a field is not scripted.

Measured, not assumed: `tools/quickstart/hub_variety.py` walks all twelve
fuser rooms and reports which face each drew and whether the NPCs standing
there carry a sprite index. All eight faces turn up, every one renders.

**Two to four landings per region, one drawn per run**, from
`sQuickStartRegionDropSpots` - 65 across the eighteen regions, found by
`drop_spots.py --multi`. The first row of each is the landing the region
always used, so a run can still come out where it did; the rest are spread
as far apart as the floor allows, which is what turns one trajectory into
several.

Every spot is in the SAME connected component as that original landing, and
that is a safety property rather than a limit of the search. The far side of
a bombable wall - the example the request gives - is the more interesting
version and also the one that can end a run before it starts: a player who
draws no bombs and lands on the wrong side has no way out unless that pocket
carries a border of its own. That needs a per-component exit analysis, and
until it exists the cross-component drop stays out.

The clear square follows the drawn landing rather than the pool row's fixed
entrance - otherwise the protected ground and the ground the player falls
onto would be different tiles three runs in four. `drop_spots.py` had to
learn the same thing: it audited the fixed entrance and immediately reported
four regions with an enemy on a landing they were not going to use. It reads
the live run seed and audits what the run actually draws now. All 18 pass.

**The hub's wanderers move and turn.** Four placements each, drawn per run,
every coordinate checked against the live collision map. Most are
deliberately not 3x3 clear - standing against a wall is the thing being
asked for, and a spot with three tiles of air around it is the middle of the
floor - and each carries a facing that puts its back to whatever it stands
against. The wind-crest signpost does not wander: all four of its variants
are the same tile, because it is a landmark. Verified across pinned seeds:
the arrangement changes with the seed and reproduces exactly for the same
one.

The hint pool went from 18 lines to 31. These are the first pool entries in
BANK 2 - bank one is closed at its 256-line ceiling - so the pool became a
table of full `TEXT_INDEX` values rather than bare indices. Two compile-time
asserts did real work here: the pool deals without replacement by walking
with a stride of 5, so a pool of 30 would have dealt one line to two
wanderers, and `QuickStartHintPoolDealsDistinct` refused to build it. Thirty
one it is.

**The shop's heart is out of the doorway**, and finding out why it was there
took reading tile data. The passage into the upper hall is a STAIRCASE:
column tx 3 of rows 8-12 carries act tile 0x29 with collision 0x27, and its
top landing is tile (3,7). The heart sat at (64,120), tile (4,7) - the very
next tile east. The catalog moves two tiles east, which clears tiles 2-4 on
all three rows, and translating the block rather than re-spacing it keeps
the geometry every one of those eight spots was verified in.

The merchant had to move too, and THAT is the part the checker taught us.
Shifting the catalog east put a shelf beside the shopkeeper and the lift
test failed on it - as it had once before, at (176,120). One cause explains
both: `QuickStartMakeNpcTalkable` gives every sign and shopkeeper a
deliberately oversized 40x40 interact box, and a shelf inside it answers R
with dialogue instead of lifting. Both failures were one tile away in one
axis; the six that passed were two clear. So the rule is a spacing rule, the
merchant stands in the north-WEST corner now, and the catalog runs east of
them. Every item lifts.

**A correction to the last batch's write-up.** The claim that
`gPlayerState.floor_type` sticks once the player is in swamp was made with a
probe that wrote the player's position to entity offsets 0x30 and 0x34 -
which are y's LOW half and z's LOW half, not x and y. The integer halves are
0x2e and 0x32 (x is a Q16.16 SplitWord at 0x2c). That probe never moved the
player at all, so it could not have shown what it claimed. Re-run with the
right offsets, the finding HOLDS - 204 sampled positions across Castor Wilds
all read SURFACE_SWAMP while the act tiles say 105 of them are dry ground -
so `drop_spots.py` reading act tiles instead is still the right call. It was
the evidence that was wrong, not the conclusion. The shipped tool never used
the bad offsets.

### Mount Crenel's Base, walked uphill

The user walked the base from its one entrance - the border up from Trilby
Highlands. The existing `CREN` block walked the same mountain DOWNHILL from
the Cavern of Flames forecourt with the Grip Ring already in hand, which is
a different set of prices; this is the uphill story, and it is the one a run
actually lives, because Trilby is where the ring puts the player. New survey
key `CREN-BASE`; reach.h 240 -> 253 rows.

**The whole base is behind bombs**, and that answers a question this project
has been carrying. A collision flood from the Trilby arrival finds a
52-tile component in a room with 467 open tiles, and not one of the survey's
coordinates is inside it. "52 tiles from the border arrival but 198 from the
survey's own coordinate" (`docs/QUICKSTART_TRAVERSAL_AUDIT.md`) was never two
measurements of the same thing - a flood reads a bomb wall as a wall.

**The bean errand is not priced, and that is deliberate.** The survey's
framing is that a BOTTLE gates everything past the hint-scrub cave, because
the vine has to be watered, and that certain beans want the green miner's
water from `CRENEL_MINISH_PATHS/SPRING_WATER` as well. True of vanilla and of
mapexplore. Not true here: `GameTask_Transition` sets `WATERBEAN_OUT` and
`WATERBEAN_PUT` at boot, and both `CrenelBeanSprout` entities in
`MT_CRENEL/ENTRANCE` were measured sitting in **action 4** - their grown
state, climbable tile already laid - in the shipped difficulty-3 ROM. Same
treatment and same reasoning as the FESTARI row: the gate is open before the
run starts, so charging a route for it prices something no run can affect. If
the pre-grow is ever removed, every row gains the bottle and the vine row
gains the green water with it.

**The Grip Ring alternative is real in the tile data.** The user's note that
the ring skips the whole base checks out: act tile 0x50, a climb surface, in
a seven-tile band at tx 50-56, ty 0-2 - pixels 800-912 across the top of the
Entrance screen, landing exactly where the survey says (`MT_CRENEL/CENTER`
at 856,274).

**Five more cancelled caves, now blessed.** `survey_gate.py` found six of
`MT_CRENEL/ENTRANCE`'s nine doors refused, and the base is where a run
ARRIVES on the mountain, so this was most of the region's ground floor: the
ladder to the spring water, the Helmasaur hallway, the bomb-scrub cave, Bean
Pesto's Minish cave, and the rupee fairy fountain the same exit list turned
up alongside them. Every one is a dead end back to `MT_CRENEL/ENTRANCE`.
All nine of that room's exits are open now.

Not done, recorded rather than guessed: the user wants `MINISH_CAVES/BEAN_PESTO`
filled with tough enemies rather than drawn as a general-purpose ? room. It
is not a content site today, so nothing has to be removed first - it needs
its own placement, the way Melari's Mine has one.

**And then the last three, on the user's say-so.** Trilby's dig cave was the
third "open at the far end, shut at the mouth" of this batch - the fairy
fountain behind it was already a site, so only Trilby's own door into the
cave was broken, and the walked survey has that cave as the ONLY way into a
Trilby pocket holding a tingle event and a Minish house. Blessed per room
rather than per area, because AREA_DIG_CAVES is one 480x960 map shared by
four rooms and blessing the area would bless three the player cannot reach.

The Minish Woods business-scrub tree was the survey's one TRAP: Tree
Interiors is a contained area, so both of its exits were policed and both
failed - the kinstone cave because it was not blessed, the border back to the
woods because walking OUT of a pocket needs the pocket itself blessed.
Nothing could reach it, so nothing was ever stuck, but it was one open door
from being a real trap. The cave behind it went with it.

That does not settle the fusion question on that door. The flood reaches it
with nothing while KINSTONE_27's world event fires at exactly (528,456), and
the survey records FREE as the cheaper of two readings. Blessing is policy;
whatever gates the door in the world is untouched.

`survey_gate.py` now reports NOTHING CANCELLED across 249 policed
transitions in 152 rooms.

### Minish Village and Lake Hylia, walked

The user walked the mapexplore build again and measured Minish Village and
three separate pieces of Lake Hylia. Transcribed into `world_reach.py`; the
reach table goes from 195 destination rows to 240.

**Lake Hylia is four places, not one.** That is the finding that reshaped the
block. The survey walked it from four different entrances and they do not
connect: the Lon Lon shore (the old `LH` start), a wind-crest pocket with no
walkable route in at all, an isolated south-west corner that only touches
Minish Woods and Lon Lon Ranch, and the big ladder pocket where the Lake
Woods cave lets out - which is most of the lake. Four survey keys now, the
same treatment Eastern Hills and Western Wood already get, all mapping to
`QS_REGION_LH`. Every row that used to sit on the Lon Lon shore carrying
`UNSURVEYED` has MOVED to the block that can actually reach it.

**A new token, `OCARINA`.** The wind-crest pocket has no route in: playing
the Ocarina and warping to the crest IS the entrance. It is also the only
new gate in the table the game can genuinely test - `ITEM_OCARINA` is real
inventory, unlike `MINISH` or `MAZE` - so everything in that pocket is
offerable to the chain placer rather than invisible to it.

**The dig caves are the densest room in the survey.** `HYLIA_DIG_CAVES/1`
holds seven golden chests and its own hole out into a Lon Lon Ranch pocket
with a heart piece in it, all behind Roc's Cape plus the Mole Mitts. None of
it was reachable.

**Minish Village is its own map**, fourteen doors and two rooms, walked from
the south entrance. Everything in it is free once you are inside except the
side house, which wants the Flippers; the heart container in
`SIDE_HOUSE_AREA` costs nothing. The story flags the survey notes are
already paid at boot.

**And most of it was cancelled.** `tools/quickstart/survey_gate.py` is the
new standing check: for every room the survey names, it finds the rooms
whose exit lists lead into it and asks the shipped containment functions
from the real door, from both sides. A room is a TRAP only if every one of
its own exits is cancelled. Nine rooms were blessed as a result -

  * Minish Village's path, the village and its side-house area. The village
    is the route to most of Minish Woods, so this was the most load-bearing
    cancelled pocket in the game. `MINISH_VILLAGE/SIDE_HOUSE_AREA` is the
    one that would have trapped a player: its only door leads into a
    CONTAINED area, so walking back out is policed.
  * Lake Hylia's Minish path, its east crack, the Librari cave (whose house
    on the far side was already blessed - the route was open at both ends
    and shut in the middle), both dig caves, and `LAKE_HYLIA/BEANSTALK`,
    which despite the name is not a climb to the clouds: its only three
    doors go into `HYLIA_DIG_CAVES/1`.

The Temple of Droplets stays shut. It is a dungeon, and that is a decision
about what this mode contains rather than an oversight.

**Getting the probe right took two tries, and the first one lied.** Asking
"from this region's survey start, can I reach X" is the wrong question for
anything two doors deep - there is no transition between them at all, and a
cancelled answer to an imaginary door is noise. That version reported
Melari's Mine's side rooms as traps by asking whether they could return to a
Mount Crenel room they have never had a door to. Walking the exit table
instead is what makes the answer mean something.

**Also from this pass.** The Waveblade TREE is no longer a content site -
per the user it is the dojo's atrium and nothing else, so putting an event
in it made two ? rooms out of one place; it stays blessed as a pocket, since
Lake Hylia is policed and it is the room the lake's door opens into.
Knuckle, the fourth Tingle sibling, is back at his Lake Hylia stump
(325,279) - he was excluded on the grounds that the lake was outside the
ring, which stopped being true some time ago. And Lon Lon Ranch's kinstone
pocket at tile (10,3) is now correctly described: mapexplore prices it at
the Cane of Pacci via Veil Falls, and it stays NOT REACHABLE here because
this build compiles the Veil Falls borders out.

Still cancelled, all pre-existing and none from this survey: Trilby's dig
cave, Mount Crenel's ladder to the spring water, and the Minish Woods
business-scrub tree with the kinstone cave behind it.

### Where a run lands, and when a region pays

**Nothing this mode places may sit on a region's landing square.**
`tools/quickstart/drop_spots.py` measured what was waiting at the eighteen
coordinates the Cloud Tops pit drops a run onto: fourteen had one of that
region's own enemy offsets within three tiles, four had one on the EXACT
pixel (South Hyrule Field, North Hyrule Field, Trilby Highlands, Royal
Valley), and eight cost the player health while they stood still after
landing. `QuickStartOnRegionDropSpot` is the rule, checked inside
`QuickStartPositionAllowed` so it governs the quest pots and the
hunt/scavenger/stealth givers drawn off the same table as well as the waves.
It costs 21 of the pool's 616 offsets - 3.4%, never more than three in one
region - and it cannot be undone by a later edit to an offset table, which
moving eighteen coordinates by hand could. After it: 0 of 18 landings have
anything of ours in the square, and none loses health. (One vanilla Wind
Ruins enemy stands about twenty pixels from the below-fortress landing. This
mode neither places nor moves it.)

**Castor Wilds landed in the swamp**, and that one was a coordinate, not a
rule: (984,264) is act tile 0x13. Moved 51px to (968,312), the nearest dry
tile with four dry neighbours.

Finding it needed the right oracle. `gPlayerState.floor_type` looks like the
answer and is not - once the player is standing in swamp it stops tracking,
so teleporting around the room and reading it back said all 1933 open tiles
in Castor Wilds were swamp, and all 72 of its enemy offsets with them, which
would have meant the region had no dry ground at all. Reading the ACT TILE
out of `gActTilePtrs` and mapping it through the ROM's own
`gMapActTileToSurfaceType` says 1039 of those tiles are ordinary ground.
`emu.act_at()` is that read, for anything that needs it next.

**A region no longer pays its clear reward on arrival.** The reward state
machine has three states, and state 1 - "dropped, not yet confirmed
collected" - had an unconditional payout at the bottom of it. On a re-entry
the room load wipes room flag 1, and the item that was on the floor was
wiped with the room, so the "still lying there?" scan misses and the next
thing that happens is a fresh reward at the player's feet before they have
taken a step. State 1 is easy to be left in: the promotion to 2 only happens
if the player is still in the room when the item leaves the floor, so
walking out through a ? room, a cave or a fusion reload first leaves the
region paying again on every arrival for the rest of the run. The single
shared `gSave.reward_drop_x/y` - one pair for eighteen regions - makes the
scan miss more often rather than causing it. The re-drop now requires
`QuickStartRegionWaveCleared()`, the same bar the first payout has always
had; flag 0 is wiped by the room load too, so that is false on arrival by
construction, and the endless wave loop means the reward is never lost.

Two things this batch did NOT find, said plainly. The settled-room guard in
`QuickStartRegionMonitor` still holds: eleven walk-ins across borders and
scroll seams, with a wave up behind the player, paid nothing on arrival on
the current build - and nothing on the pre-fix build either, so that path is
not where the report comes from. And `QuickStartSpawnRegionWave` used to
return TRUE for a deal that placed zero enemies, arming flag 0 on an empty
room; that is a real defect (a phantom clear, plus an inflated wave counter)
and it is fixed by returning the placement count, but it was measured NOT to
happen on arrival in any of the eighteen regions, so it is hardening rather
than the fix. `tools/quickstart/region_arrival.py --armed` is the standing
check that no region reads as a cleared wave while the player is arriving.

One residual, not fixed: `gSave.reward_drop_x/y` is still one pair for all
eighteen regions, so a stale coordinate that happens to have an unrelated
ground item on it can set room flag 1 and promote a region to "collected"
that never paid. Narrow, and no longer able to cause a payout; closing it
properly means recording the owning slot in the save.

### Melari's Mine, live: the mountain's Minish holes were all cancelled

The mine's route was never missing from the data. Every row on it - the
holes, the paths room's south border, the mine's three side-room doors and
their three borders back - was already vanilla. What stopped it was policy.

`tools/quickstart/minish_holes.py`, run over `AREA_MT_CRENEL`, finds six
holes. The Cavern of Flames forecourt has three (two into
`CRENEL_MINISH_PATHS/MELARI`, one straight down into `MELARIS_MINE/MAIN`);
the Entrance screen has three more (`CRENEL_MINISH_PATHS/BEAN`,
`CRENEL_MINISH_PATHS/SPRING_WATER`, `MINISH_CRACKS/MT_CRENEL`). Both
mountain rooms are named region rooms, so
`QuickStartEnforceFieldRegionContainment` polices them, and only
SPRING_WATER was blessed - it is a content site. The other four landed in
rooms nothing had named and were cancelled the frame they fired, which from
the player's side is the "fall in and land nowhere" the ring's own holes
showed before they were blessed. `QuickStartIsPocketInteriorRoom` now names
the mine, the three Crenel Minish path rooms and the Mt Crenel crack. Every
one is a dead end whose exits run back into the mountain or deeper into the
same pocket, so nothing here opens a way out of the run.

Blessing the mine fixes the other direction too, and that one could have
trapped a player: the mine's three side rooms live in
`AREA_MINISH_HOUSE_INTERIORS`, a CONTAINED area, so walking back out of them
is checked - and passes only because "the destination is a pocket interior"
is now true of the mine.

**Verified against the ROM.** `tools/quickstart/melari_gate.py` stages each
transition the way vanilla's door and border code does and runs all three
containment functions: 17 checks, 13 that must pass and 4 controls that must
still be refused. Note what is NOT a control - a side room leaving for
another side room is allowed by construction, because
`QuickStartEnforceContainment`'s last line only cancels when the destination
is outside the contained set. The controls leave the contained area for a
Crenel cave with no site row. A live census in the mine finds 28 enemies and
no NPCs (the wave and the clear both running), and the two bespoke side
rooms roll their content - the east room came up NPC, the south-east a
chest.

**Three warp boxes retired.** `sQuickStartLinks` carried a trigger box for
each of the mine's three side-room doors, sitting on that door's own
coordinates and leading to the same room - a box layered on a door, which
the standing rule forbids. Not cosmetic either: the boxes landed the player
at (0x78,0x64) while the doors land at each room's vanilla arrival, so
whichever won the race decided where the player came out. The doors are
unopposed now and the round trip is vanilla end to end.

**A generator bug came out with it.** `room_owner.py` looked a ring room's
area up in `sQuickStartRegionPool`, which names only ONE room per region, so
four of Mount Crenel's five rooms resolved to nothing and their Minish holes
were never walked - and two of those four are how the mine is entered. Fixed
by resolving the area from the room name; the owner table goes from 136
pocket rooms to 142, and Melari's Mine's south-west room - the last content
site with no owner - is owned by CREN.

**Reach rows for the three side rooms**, at `[[MINISH]]`, the same price as
the mine. `QuickStartReachRoomOk` refuses a room with no row at all, so
without these the south-west room could never host a gated placement no
matter what the player was carrying.

**Castle Garden's south border was already vanilla** and is not in
`docs/QUICKSTART_RETARGETS.md`. Three comments in `game.c` still said it
pointed at the mine, left over from the hub era; they are corrected.

### The 09/28 batch: the last of the pool, and a door that would not let go

**Melari's Mine is back on vanilla too**, which takes RETARGETED to 5 and
empties the category of leftovers entirely - all five that remain are the
missing-Hyrule-Town stitching. That door had been pointed at Castor Darknut
Hall to stop it racing a custom `sQuickStartLinks` box covering the same
spot; both Castor Darknut Hall <-> Melari's Mine link rows were retired from
that table a while ago, so there was nothing left to race. Nothing is
orphaned: Darknut Hall's real way in is `gExitList_CastorCaves_Darknut`
inside Castor Wilds, which the walked survey uses and which is untouched.

**The single-door "? room" pool's retargets are gone.** Twenty-one exit
lists still sent their only door to Castle Garden Main - three dojos, three
tree hollows, ten Minish house interiors, Gina's grave, the Veil Falls
heart-piece cave and the Minish Woods Great Fairy. They are all vanilla
again, which took RETARGETED from 27 to 6 (`docs/QUICKSTART_RETARGETS.md`).
The six left are the four town-bridge borders, Stockwell's shop and Melari's
Mine's custom-link alignment - all deliberate.

Two of those restorations matter beyond tidiness. The Great Fairy's door and
the tree hollow above her are a PAIR, and the user's walked survey reaches
them only through Eastern Hills North's Pacci-cane ledge - so retargeting the
fairy severed the one pocket in Minish Woods with a measured way in. And ten
Minish Village houses all exiting to Castle Garden made a village the survey
routes a large part of Minish Woods THROUGH into somewhere a route cannot
pass.

One restoration is knowingly odd: `MinishHouseInteriors_HyruleTown` exits
into Hyrule Town, which the mode's overworld does not contain. The room is a
Minish hole in that same town, so nothing in a run can reach it to use the
door; left vanilla rather than special-cased.

**The Ezlo-hint door loop.** The user's report: walk out of the Trilby
Highlands tree, "Something sleeps here" plays the instant the field loads,
the door pulls the player back inside because they are still standing on it,
and it repeats forever. Two features that are each fine alone - vanilla
takes a player who lingers on a door, and the element region announces
itself on entry - and the hint's freeze is what closes the loop. The hint is
room-flag gated, so it fires on EVERY entry, including the entry the door
itself causes.

`QuickStartPlayerOnExitTrigger` now suppresses every room-entry hint while
the player stands on one of the room's own exits, and does NOT set the
latch, so the line is postponed rather than lost.
`tools/quickstart/door_hint_loop.py` measures it, and two things about that
probe are worth keeping: `emu.warp()` runs 300 frames of its own, so a
player who arrives at the reward spot and is moved to the door afterwards
has already heard the hint; and the player must be PINNED on the door,
because left alone the engine takes them through it, they come back out
elsewhere, and the hint fires there quite correctly. An earlier version of
the probe did neither and reported a working fix as broken twice.

### The 09/25 integration batch, part two: content, and where it can go

Fourteen new ? rooms, all in the three expansion regions, all in pockets
those regions already owned and simply had no row for. Content sites per
region now read CREN 16, NHF 14, CW 12, LLR 11, **MW 9**, SHF 8, TRIL 8,
**LH 8** - which is the shape the user asked for, against the 4/5/8 the
three started at.

Every spot is proposed by `tools/quickstart/site_candidates.py` rather than
chosen by eye: it boots the ROM, lands the player on the room's REAL arrival
(the `endX, endY` of the transition row that points into it - for a
WARP_TYPE_AREA row that pair is the landing inside the destination, which is
why Eastern Hills North's farm-house door reads (64,72) -> (120,136)),
floods the walkable grid from there, and takes the open tile farthest from
the arrival. Farthest, because landing ON the content spot collects the
reward on the spawn frame. The kind comes from the room's own measured
floor: 50+ open tiles ANY, 25-49 LARGE, under that SMALL.

Two Lake Hylia rooms are deliberately still out - its two Minish cracks are
entered through holes rather than doors, so no transition row points into
them and the proposer has no arrival to stand on.

**Open measurement (closed Oct 2026 - the spawn table covers every component now, see "The shoe merchant's fusions, and Mount Crenel populated"): Mount Crenel's entrance has two different answers.**
Flooded from the Trilby border arrival it is 52 tiles (which is what
`QUICKSTART_MTCRENEL_ROOM_SQUARES` and the region's ten enemy offsets are
built on); flooded from the survey's own coordinate,
`tools/quickstart/crenel_spots.py` reports 198. Both cannot be the
component a player arriving from Trilby stands in. Until that is settled the
enemy grid stays at the conservative reading, because the expensive way to
be wrong here is the one the user already reported once - enemies spawning
behind a wall.

### The 09/25 integration batch: the expansion regions join the rules

"Ring" is retired as a word. The regions are regions: `QS_REGION_*`,
`sQuickStartRegionAdjacency`, `QuickStartRegionOfRoom`,
`QuickStartRegionsWithinTwo`, and `tools/quickstart/ring.py` is now
`region_crossings.py`. Nothing about the graph changed - only what it is
called.

**Twenty-two ? rooms belonged to no region at all.** Minish Woods, Lake
Hylia and the mountain had no rows in `sQuickStartRoomOwners`, and an
unowned room reports region mask 0 - which `QuickStartKeyRegionOk` reads as
a REFUSAL. Every gated key was silently barred from those rooms.
`room_owner.py` now knows the three regions (and two more scroll seams it
could not derive: Grayblade's dojo above its ante room, and the Darknut
arena beside its hall), and the regenerated table covers 80 rooms instead of
64. (Melari's Mine's south-west room was left unowned in this batch and is
owned by CREN as of the mine's reinstatement below.)

**All three can host bosses now**, vetted to parity with Castle Garden by
the new `tools/quickstart/boss_arena.py`: family composes, intro finishes on
the control's own frame (1027), the peel handler runs for the same 1184
frames, the family dies, the player is still in the room. An earlier pass
read all three as "never engaged" and it was the harness: the driver walks
the player in a straight line, and in a region whose arrival component
touches a border that walks out of the room before the intro finishes. The
CONTROL failed the same way, which is the only reason the reading was
caught.

**The kinstone economy reached none of them.** Minish Woods, Lake Hylia and
Mount Crenel had zero fusers between them. Worse, checking the existing
table against the ROM's own `gKinstoneWorldEvents -> gWorldEvents` chain
(`kinstone_audit.py`) showed four of Castor Wilds' five fusions do not fire
in Castor Wilds at all - KINSTONE_40's event is in North Hyrule Field,
KINSTONE_58's in South Hyrule Field, and KINSTONE_44's and KINSTONE_56's in
MINISH WOODS - and 40 and 58 were ALREADY listed against those rooms, so
the table held two rows for one fusion. The duplicates are gone, 44 and 56
moved to the woods where their chests are, and the three regions now hold
eight fusions between them. Mount Crenel also gained the fuser-spot row it
never had.

**Two stack overflows, both found by growing the tables.**
`QuickStartFuserPlacements` sized `counts` and `cands` at a literal 9 - the
spot table's row count on the day it was written, which Minish Woods and
Lake Hylia had already taken to eleven, so every run's placement pass wrote
two bytes past the end of a stack array. `QuickStartSpawnRegionFusers` had
the same shape with `hostRoom[34]`/`hostSpot[34]` against a table that is
now 41 rows, and that one was VISIBLE: the invariant checker reported four
fusers that should have been standing somewhere and were not. Both are now
sized by a stated ceiling with a compile-time assert holding the real table
under it.

### The 09/25 boss batch: the chuchu's dead window, and a second boss

**The chuchu was hittable only in four of its twelve phases.** The user's
report was "green and blue are sometimes resistant, sometimes susceptible",
and the colour turned out to have nothing to do with it - both forms measure
identically. `sub_08027AA4`, the handler that lets a weapon peel the jelly,
is not called from the tick; it is called by hand from the subAction
handlers for 1, 2, 3 and 5 and from nowhere else. Whether a swing counted
depended on which animation the boss happened to be playing.

Measured with `tools/quickstart/chuchu_windows.py`, delivering a contact on
every clear-iframe frame: **subAction 11 - the re-armour after a core hit -
took 52 frames of contacts and advanced the peel counter zero times.** The
tick now calls the peel itself whenever the body's hitType is 0x7D (the
armoured jelly) and the running handler is not one of the four that already
do. After: the same probe records 40 advances in subAction 11, and the whole
fight moves several times faster because no phase is dead any more.

**The Big Octorok is in.** It is the mode's second boss, drawn 50/50 against
the chuchu in the wave loop's boss deal. Getting it there took four separate
findings, all measured with `tools/quickstart/octorok_boss.py`:

1. *Nothing can hurt it.* Not the sword, not an arrow, not anything, in any
   phase. The only thing in `octorokBoss.c` that takes health off the body
   is the Burning sequence, and the only way into Burning is touching the
   FROZEN tail with contact source 7 - the Lantern, and nothing else.
   `COLLISION_ON` is called in exactly one place, and that place runs after
   the boss has already been hurt once. A run without a Lantern would meet a
   wave it could never clear. The family now reads weapon contacts on ANY
   piece and takes a health off the body, which drops it into the shipped
   OnDeath -> Hit chain that advances the phase.
2. *The hit was landing on the wrong entity.* Forged contacts on the body
   advanced the fight perfectly while a real sword did nothing: the body
   carries no hitbox of its own, so a swing touches a leg, the mouth or the
   tail. Reading only the body made a boss a probe could kill and a player
   could not.
3. *The intro is a cutscene that cannot run here.* It hides the player,
   teleports them to a fixed offset above the boss, takes the camera,
   disables the pause menu and then waits on them walking 30 units into an
   arena that does not exist. QUICKSTART skips it: Init goes straight to
   ACTION1.
4. *The phase change was a softlock.* `Hit_SubAction1` only counts its timer
   down once the boss has walked to a HARDCODED screen position - the middle
   of the Temple of Droplets. In an overworld room that spot can be inside a
   wall, so the timer never reached zero, the phase never completed, and the
   player stayed frozen. The timer now runs regardless; the boss still walks
   toward the spot, it just no longer waits to arrive.

Also generalised: every `id == CHUCHU_BOSS` exemption in game.c - the GFX
reserve trimmer, the enemy census, the Trilby pocket clamp, the charm that
speeds enemies up - now asks `QuickStartIsBossId`, so the next boss cannot
inherit half of them.

Measured after: a plain sword standing beside the Big Octorok takes its body
from 3 health to 2 in 300 frames, and the full eight-phase fight runs to the
death sequence with the family gone at frame 1759.

**Still open:** the harness cannot chase an eleven-piece boss around an
overworld room well enough to kill it free-roaming - it lands almost nothing
while the family wanders. That is a driving problem, not a game one (the
same driver kills an ordinary Octorok in 300 frames), but it means the
free-roam kill is unverified and the fight's real-play pacing is unmeasured.

### The 09/25 traversability audit: what the world graph does and does not know

The user asked for the inventory before the graph: every entrance, exit,
seam and room in every overworld region, and a matrix saying, for each
ordered pair, whether anyone has ever measured the walk from one to the
other. `tools/quickstart/traversal_audit.py` generates it from the
repository - `transitions.c` for doors, `gAreaRoomHeaders` for scroll
seams, `world_reach.py` for the walked survey, `overworld_paths.py` for
the port model, `region_walk.py` for the emulator legs - into
`docs/QUICKSTART_TRAVERSAL_AUDIT.md` and `docs/quickstart_traversal.json`.

The headline number: **17 regions, 416 places, 13,886 ordered pairs, and
8,981 of them (65%) with no measurement and no inference at all.** 170
places have never been priced from anywhere.

Four things the audit found that were not visible before it existed.

**`d()` conflated "free" with "no way in".** `world_reach.py`'s row
builder replaced a `None` requirement with `[[]]`, so the four rows written
to say *the survey looked and found no route* - Lon Lon's Veil Falls
pocket, Trilby's Royal Valley pocket, and the two Wind Ruins armos pockets
- were compiled into `reach.h` as FREE. The placer was being told it could
drop a step in a pocket nobody can walk into. Fixed with a sentinel
default, and `gen_reach.req_masks` now emits "never" for `None`.

**Abutment is not a seam.** The first draft read any two room rectangles
that touch as a scroll seam and invented about a dozen crossings, including
a Wind Ruins / Western Wood border. The engine scroll-walks only between
rooms of the SAME area; across areas the only crossing is a
`WARP_TYPE_BORDER` row. The audit now reports cross-area abutment
separately, as *Flush on the map, no crossing* - 38 places where the world
map looks joined and is not, each one a border we could add or a wall a
player will walk into expecting a path.

**A door is priced by the room behind it, but only when it is the only
door.** The survey records what it cost to END UP somewhere, never where
the door was. Where exactly one door leads to a priced room, the room's
price is also the door's; where several do, the survey cannot say which one
it used and the audit leaves those doors unmeasured rather than guessing.
That one rule moved coverage from 79% unmeasured to 65%.

**Where the holes are.** Wind Ruins (93% unmeasured) and Mount Crenel
(77%) are the worst, and both for the same reason: they are several rooms
joined by internal scroll seams that no survey has walked. Hyrule Castle
Garden has never been surveyed at all. Minish Woods and Lake Hylia are
better covered but their coverage is FLOOD-derived, and 27 of their places
are priced only in `unsurveyed` - a token with no run-time test, so the
placer can never satisfy it and never offers those places.

### The 09/21 batch: the three regions are actually reachable now

The 09/17 entry below claims Minish Woods and Lake Hylia were opened. They
were not, and the way that went wrong is the most useful thing in this
entry.

`QuickStartRegionOfRoom` learned both regions and containment stopped
cancelling the crossing - that part was real, and `seam_gate.py` measured
it honestly. What `seam_gate.py` cannot see is whether a crossing EXISTS:
it stages the transition itself, by writing `area_next`, `room_next` and
`transitioningOut`, then runs the containment functions over it. The
borders had been deleted from `src/data/transitions.c` outright, under
`#ifndef QUICKSTART`, each with a comment saying the region was "outside
the ring". So the gate was opened on a door that was not there, the probe
happily confirmed the policy, and the player stayed exactly as stuck.

**Doctrine: a gate probe measures the policy, never the route.** The
question "can the player get there" is only ever answered by walking.
`tools/quickstart/region_walk.py` does that now - eight legs, in and back
out of all three regions.

Restored, and walked: Eastern Hills North and South into Minish Woods, Lon
Lon Ranch into Lake Hylia, Trilby Highlands into Mount Crenel. Veil Falls'
two north borders stay deleted on purpose - that region has no pool row,
no sites and no survey.

A second thing the walk taught, which cost the first run of the probe
three of its four legs: **an overworld border is open only in bands.**
Sweeping Eastern Hills North's east edge in 64px steps, y=40 and y=104
cross, y=168 through y=360 do not, y=424 crosses again. The rest is cliff.
"Held RIGHT and nothing happened" is evidence about terrain, not about the
transition table, and every coordinate in the probe is now a measured
crossing rather than a guess.

**Mount Crenel is a full region now**, not just a set of ? rooms. It was
the odd case: its sites were blessed as pocket destinations, so the
mountain's interiors were reachable in policy while the mountain itself
had no restored way in, no ring membership and no containment once you
were on it. It now has all five of its rooms in the ring (they are joined
by the area's own scroll seams, so naming only the arrival room would have
policed one screen and left the rest open to the Cavern of Flames), and a
pool row: entrance (1000,424), which is where the restored border actually
deposits the player, and reward (872,408), ten tiles along the same
flooded component. Ten spawn points, not the usual sixteen - the arrival
ledge is 52 tiles of the room's 467 open ones, the rest of the mountain
being behind the climb, which is exactly what `reach.h` already prices at
BOMBS plus the GRIP RING.

Added while growing both: a compile-time check that
`QuickStartRegionOfPoolIndex`'s `byPool` array is the same length as
the pool. The index is taken modulo the POOL's size and read out of
`byPool`, so a mismatch reads off the end and a region answers to the
wrong ring - and nothing enforced it until these two had to grow together.

### The 09/17 batch: two regions opened, and the item pools widened

- **Minish Woods and Lake Hylia are in the run.** Both had pool rows,
  reach-table entries and content sites already; the entire seal was one
  missing case in `QuickStartRegionOfRoom`, because containment only
  passes a transition when BOTH ends are region rooms. Measured before and
  after with `tools/quickstart/seam_gate.py`: before, the three ways in
  were cancelled and every way OUT of both regions was allowed (the Minish
  caves, the Great Fairy tree, the Lake Woods cave); after, the ways in are
  open and the ways out are policed. Doctrine: **a region can be fully
  built and still be unreachable** - pool row, reach entry and site table
  all present is not the same as a door the mode will let you walk through.
  Second doctrine, from choosing the controls: the Witch Hut, Librari and
  Mount Crenel's entrance all looked like obvious "should be sealed"
  destinations and all three are correctly ALLOWED, because each is a
  content site and a site's door is blessed wherever it lives.
  Mount Crenel stays out of the ring on the user's instruction (its base is
  unmapped). Worth recording that its ? rooms are already reachable from
  Trilby as pocket sites - what Crenel lacks is a pool row, not a door.
- **Bottled items stopped evaporating.** `GiveItem` case 4 scanned all four
  bottle slots for one holding 0x20 and returned if it found none - and an
  UNOWNED slot holds 0, not 0x20, so a player with one full bottle failed
  the scan and the pickup was destroyed in silence. Now: spend an empty
  bottle, else grant a NEW bottle with the item in it, else (four full)
  overwrite slot 0.
- **Bombs grant the Bomb Bag.** Vanilla's order is bag first, ITEM_BOMBS
  only later as the "switch back from Remote Bombs" option, so a mode that
  draws ITEM_BOMBS from a pool left the player with no bag and spent the
  next bag draw granting what it should have expanded. Measured: bombs then
  three bags walks 10 -> 30 -> 50 -> 99 and caps.
- **Light Arrow and the last three sword arts** joined the draw, behind the
  Bow and the Spin Attack respectively. The risk that needed measuring was
  the pause menu - the Lantern's two ids hang its slot-fill loop and the
  bow's two share a slot - and with both owned the menu runs.
- **The last six unused ids became charms and curses**: Creeping Rot (a
  slow poison held back by rupees and kinstones), Drowned Sight (mosaic),
  Ember Haze (a dimmed screen), Duelist's Edge (+1 sword damage), Rusted
  Blade (-1), and the Whetstone (the sword beam stops requiring full
  health). `tools/quickstart/charm_batch3.py` measures all of it, 26
  checks.

Four things that batch taught, all of them the same shape - the thing that
looked verified was not:

1. **A free-flag scan that only reads macros is not a free-flag scan.** The
   six new charms were first put at 101-106 on the strength of a script
   that parsed every `GF_*` define and found a 20-wide gap. 101-173 is the
   ladder pool's block, allocated by a run-start clear LOOP that no macro
   describes. The symptom was not a crash: giving one charm lit five mask
   bits, and the poison curse drained health in the control run too. They
   now live at 94-99, the spare tail the content-site block gave back when
   it collapsed to one bit per site - and `invariant_check.py` confirms it.
   Anything allocated here must be checked against the clear loops and
   `QuickStartExtSlotFlag`'s four borrowed runs, not just the macros.
2. **Write-only registers read back as garbage.** `REG_MOSAIC` and
   `REG_BLDY` both returned 0x30b8 - the same open-bus value - so a probe
   that "read" them was verifying nothing, twice. Visual effects are
   measured on the frame buffer now.
3. **A screenshot catches what a register read cannot.** The blur worked
   perfectly and made every line of dialogue in the run unreadable, because
   the world and the text share BG0. Dropping BG0 from the mosaic set just
   removed the blur from the world. The fix - blur everything, stand down
   while a message is up - is only findable by looking at the picture.
4. **Mind what a `default: return` is standing in front of.** Creeping
   Rot's antidote was added after the charm switch in
   `QuickStartNoteFoodItem`; that switch ends in `default: return`, and a
   rupee is not a charm, so the antidote was unreachable for every item
   that could have triggered it. It measured as "the curse has no
   antidote".

**Retracted: the "Grimblade dojo health drain" was not a defect.** The
measurement was real - a parked player lost two health units over 600
frames at one spot and fourteen at another - but the cause is that the
dojo is a live ? room and the probe walked into its wave. Forcing the
site DONE and repeating both spots: zero enemies, 16/16 health over the
same window, at both. The four bodies were ROPEs, a legitimate roster row
(`QS_R_CHAFF | QS_R_AMBUSH`), doing exactly what an ambusher should do to
somebody standing still. The fourteen-unit spot is simply the one inside
the spawn cluster.

Doctrine, because this is the second time it has cost a probe: **a content
site room is a COMBAT room until its DONE bit says otherwise.** Parking a
player in one and measuring anything about their health, position or state
measures the wave, not the thing under test. `emu.poison_here` does not
help here - it only stops `here()` being confused by a stale room byte.
`qs_site_set(c, <site>, 1)` is what makes a room quiet, and any probe that
needs a still player belongs in a region room or a site that has been
silenced. (The first time was the pursuer soak, where a BOW_MOBLIN killed
the player at row 8 and the remaining sixteen rows were measured against a
frozen game.)

### The 09/16 playthrough batch (all five shipped)

Five notes from a playthrough of the difficulty-3 build.

- **Survive rooms drew wanderers.** "Stand your ground!" is the one event
  where an enemy declining to engage costs the player nothing, so the wave
  now re-rolls the difficulty pick against `sQuickStartPursuers` and only
  falls back to a flat draw from that list after eight misses. Three kinds
  the user named are deliberately absent, and the reason is measured rather
  than argued - `tools/quickstart/pursuer_soak.py` spawns every row 64px
  from a pinned, invulnerable player in the dojo: FLYING_POT runs its whole
  action chain and deletes itself after ~47 frames, FLYING_SKULL and LAKITU
  sit in action 1 forever and move 3px and 0px in 900 frames. All three
  need a spawner parent. Doctrine: **the roster soak's "alive at 600" is
  not the same question as "dangerous"** - LAKITU passed admission and is
  still inert, and on a clock a harmless enemy is worse than none because
  it holds a slot.
- **Enemies spawning behind walls the player cannot pass** (Goron ? cave in
  LLR, the bombable-wall cave in EH centre). The cause is that **"open"
  includes the VOID**: the tiles outside a room's walls carry collision 0
  exactly like its floor does, so Goron Cave's stairs room measures 67 open
  tiles of which 9 are the actual chamber. Placement is now restricted to
  the player's own connected component, reusing the pot fill's flood.
  Three things were needed to make that work:
  * Seed from the player AND his four neighbours. The arrival tile is very
    often a doorway, which reads as solid - in the Grimblade dojo a
    single-tile seed found nothing, so the rule switched itself off in one
    of the busiest ? rooms there is.
  * Bound the ring walk by the reachable set's own extent
    (`QuickStartReachMaxRing`). Without it the first three passes ground
    through ~6,500 cells each to place nothing. Measured, Goron main, 8
    enemies: **4,548,667 instructions before, 303,984 after** - sixteen
    frames of dead air at the moment a wave drops, down to one.
  * Ignore the set when the ANCHOR is not in it, and open the no-reach
    escape hatch only when reachable ground produced NOTHING. A collision
    flood cannot see a ledge, and it cannot see a diggable wall either -
    Dig Caves' Trilby room keeps its site behind one, and the invariant
    checker caught that as a regression before it shipped.
  `tools/quickstart/spawn_reach.py` is the probe, with the dojo as its
  control: 86 open tiles, 86 reachable, 8 of 8 placements on reachable
  ground, so the two Goron rooms' 290 and 58 unreachable tiles mean
  something.
- **Select with nothing to fuse now names the next step.** Select became
  the Kinstone Fusion button in this build, which is why
  `CanDispEzloMessage` is a stub - it used to be how you asked Ezlo where
  to go. `QuickStartSelectHintMonitor` takes the other half of the press,
  testing for a fuser exactly the way `sub_080782C0` does so the two can
  neither both fire nor both decline. A third hint bank (65 lines,
  generated by macro rather than authored) says region AND kind in one box,
  which neither of the existing banks could.
- **Link's House smithy keeps its furniture.** Clearing it bought no floor
  space at all: the collision lives in the room's tilemap, not on the
  entity, so sweeping the objects took the sprites and left the barriers -
  the "big invisible barriers all over the room" in the report. Doctrine:
  **deleting a furniture entity does not delete what it stands on.**
- **Minibosses re-centring.** Both spawn sites now latch a room flag the
  first time the player comes within 96px and only hold the enemy on its
  content spot before that. **Untested in-game**: the probe written for it
  could not produce an elite spawn on any scanned seed, and a green-but-
  blind fixture is worse than none, so it was deleted rather than shipped.

Open, found while verifying the above and measured identical on the
previous build, so not a regression from it: **North Hyrule Field breaches
the GFX reserve floor at difficulty 12** - 1 free slot against a floor of
2. `invariant_check.py` reports it.

### The 08/21 playtest batch (all fixed, with the doctrine each fix bought)

The user's deaths-up-to-difficulty-4 playtest surfaced eight bugs and four
feature asks; every one shipped in this pass. What each fix taught, kept
here because the lessons outlive the bugs:

- **Enemies dying on room entry with item drops (major) - three compounding
  causes.** (1) The GFX trimmer and spawn budget gated on strictly-FREE
  slots, which a settled room pins at ZERO forever (slots end up referenced
  or UNLOADED, never FREE), so the trimmer deleted one enemy every 64
  frames without ever satisfying its own stop condition. Both now count
  RECLAIMABLE slots (FREE + UNLOADED + STATUS2 - what the loader can
  actually claim). Doctrine: **reclaimable is the budget; strict-free of a
  settled room is always zero and gating on it means gating forever.**
  (2) SLUGGULA left the roster: form 0 is a ceiling-hanger that
  self-replaces with a new entity (reads as death + spawn churn), a raw
  form 1 batch self-deletes. (3) GYORG_CHILD left the roster: a boss
  escort that despawns 27 frames in without a living parent. Doctrine:
  **roster admission now requires surviving raw EXISTENCE, not merely
  spawning** - `tools/quickstart/roster_soak.py` raw-spawns every roster
  row in the quiet dojo and demands 600 frames of life; all 49 surviving
  rows pass.
- **Quest end cleared the wave and paid the region prize.** The
  wave-cleared headcount ran during a quest's population swap and read the
  empty frames around quest start/end as a legitimate clear. Two guards:
  wave-clear returns FALSE while a quest swap is active, and quest end
  latches room flag 10 which the wave loop consumes on the NEXT frame -
  because DeleteEntity effects settle a frame late and a same-frame
  emptiness check races (measured: false clear at f61 after a FAILED at
  f60).
- **Boss-spawn item drop / prizes dropping automatically after many
  waves** - both downstream of the above two: the trimmer bleed could
  empty a room (= credited clear + reward + boss roll in the same
  instant), and the churn kinds' self-deaths rolled kill drops. A 25-clear
  soak on the fixed build (2 boss spawns included) shows zero spurious
  drops. One legitimate coincidence remains by design: a first-clear
  region reward can land on the same clear that rolls a boss.
- **Performance drops** - not reproducible on the fixed build: every ring
  region plus Castle Garden and Lon Lon Ranch holds a locked 60.0 fps
  (average AND worst 30-frame window, 900-frame samples) at difficulties
  0/4/8/12, up to 40 live enemies. The constant delete/respawn churn the
  trimmer bug caused was almost certainly the felt cost. SUPERSEDED: the
  drops persisted and the real cause is segmented kinds blowing the live
  ceiling - see "The large-area slowdowns" section below.
- **Minish door lockout (ranch house west).** The 2-door obstacle sweep
  deleted every OBJECT in the room - including the MINISH_SIZED_ENTRANCE
  that is the room's only way back out (no pot inside to un-shrink with).
  The sweep now exempts MINISH_SIZED_ENTRANCE and MINISH_SIZED_ARCHWAY.
  Doctrine: **a Minish-sized entrance is a DOOR, not furniture; no object
  sweep may take one.**
- **Magical Boomerang downgrade.** Upgrades now shadow their base item out
  of the tier pool (`QuickStartTierEntryUsable`): holding the Magical
  Boomerang removes the plain Boomerang from the draw, holding the Blue
  Sword removes the Red.
- **Eastern Hills model corrected** (overworld_paths.py): the top section
  has BOTH an ENE and an ESE exit; the surveyed matrix is ENE->ESE/N free,
  ENE->W/S bombs, ESE->ENE and N->ENE Cane of Pacci, W->ENE and S->ENE
  bombs + Cane. ENE/ESE/S remain unlinked ports (same standing as Castor
  Wilds SWS).
- **Deku scrub restored** in North Hyrule Field as a shop: the prologue
  cull now replaces BUSINESS_SCRUB_PROLOGUE with a real BUSINESS_SCRUB at
  its spot, carrying one of three new QUICKSTART sales rows (heart 10 /
  10 bombs 30 / 30 arrows 30), re-rolled per room entry, start-revealed
  (no shield duel gates the shop). The hearts offer is custom string 228,
  which chains via the vanilla mechanism (`\x07` jump) into the shared
  "Sure / No, thanks" prompt - **the choice markup in that chained prompt
  is what arms a purchase**; an offer text that never reaches it can never
  sell. The scrub is kind ENEMY, so one predicate
  (`QuickStartEntityIsShopScrub`) exempts it from the wave-cleared scan,
  the alive counter, the trimmer's victim pick, and the scav quest's
  swap/pack-marking. The prologue's orphaned scene prop and its carved-
  open hedge tiles (placeholder glyphs outside the cutscene) are cleaned
  with the same RestorePrevTileEntity repair the scene's own resolution
  uses.
- **Trilby's hidden pool** (behind the dig cave's bombable wall - vanilla's
  Mitts Great Fairy fountain) is content site 59, with TRIL ownership.
  Appended at the site table's END so no existing site's flag-block index
  moves; 2 of the 61-slot ceiling remain.
- **Switch prize puzzle retuned**: per-tile slack 18-difficulty (was 22),
  ~1.3x a straight walk at difficulty 0 and ~1.07x from 3 up - and every
  pull that opens the window drops a pressure pack around the cage
  (beetles + Bobombs, 2+1 at diff 0 to 4+3 at 12), guarded by live-count
  so pull-spam cannot flood but a killed pack re-arms.
- **Vanilla small chests restocked from our economy.** Small chests are
  TILE entities (gSmallChests, loot in the entry's `_2`), invisible to
  every object sweep. `QuickStartRestockSmallChests` (room monitor,
  unconditional) swaps each freshly-registered entry's item for a 60/30/10
  drop draw, marked in the unused `_7` byte; chest visuals/persistence
  stay vanilla, lottery injections are skipped by their reserved flags.
  Surveyed live: Castle Garden ships two, Western Wood South one.

Probe doctrine banked along the way: gate_probe-style switch flips write
the switch entity's frameIndex (+0x1e); BEETLE is enemy id 7 (not 5) and
BOBOMB 0x22 - filter ids from enemy.h, not memory; and a transient
HP->0-for-one-frame on STALFOS is its collapse mechanic, not a death.

### The second playtest batch (all shipped)

- **Tingle siblings at their vanilla stumps.** Three now, not one, each
  at his sibling's own vanilla entity placement: Tingle in SHF
  (0x3b8,0x118), Ankle in LLR (0xb8,0x108), David Jr. in Trilby
  (0xb8,0x78); Knuckle's stump is Lake Hylia, outside the ring. Fusions
  KINSTONE_2A/2B/2C (one red-piece family, as vanilla); each pays a
  heart container at the player's feet. They no longer draw from the
  fuser scatter or consume its slots. NOTE: three heart containers per
  run is richer than the old one - retune the payout if it plays too
  generous.
- **Tingle fusions skip the world-event cutscene.** KinstoneMenu_Type2
  consults game.c's exported QuickStartKinstoneIsTingle and closes the
  menu like a fusion with no event, so a tingle fusion cuts straight to
  the item drop instead of panning to the Goron Cave. Goron unlocks
  stay on the ZELDA fusers (25/26/2F walls + 29 entrance), untouched.
- **Region clear rewards drop at the player's feet**, snapped to open
  ground, with the true landing spot recorded in gSave.reward_drop_x/y
  (carved from filler22) for the exact-coordinate confirm scan. The boss
  spawn and the Earth Element keep the fixed reward spot - setpieces.
- **The Lost Woods maze is per-run random.** Route = pure function of
  gSave.run_seed, five steps from {Up,Right,Left} (Down = the give-up
  border, never drawn); vanilla's fixed alternate route compiled out.
  The sign system tells the truth for free: sign text is bound to tile
  POSITION (Up@0x49, Right@0x14b, Left@0x18c, sign tile type 374), so
  the progress painter stamps the position whose word IS the current
  step. Each pass's Ghini is swept and replaced by one level 4/5 roster
  draw. Walked end to end: wrong step resets, five correct solve, the
  north border delivers to RV-middle at (0x78,0x278).
- **Probe doctrine:** ROOM_HYRULE_FIELD_LON_LON_RANCH is room FIVE, not
  2 - a warp to (3,2) lands in a different Hyrule Field room that
  happily settles and spawns waves, which cost half a day chasing
  'missing fusers'; AREA_ROYAL_VALLEY is 9. Take room ids from
  parse_tables, never from memory. The maze's progress lives in
  gArea's bitfield byte at +0xd (unk_0c_1 = bits 1-3, unk_0c_4 = bits
  4-7), and gRoomVars (QS room flags included) is wiped on EVERY
  scroll-load - which is what makes a room flag a per-pass latch in
  scroll-looping rooms.

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
  floor heart piece simply doesn't read as a payout. **The cheap insurance
  has shipped**: every reward this mode places now twinkles
  (`QuickStartSparkleRewards`, vanilla's own `CreateSparkleFx` on a
  staggered cycle, scoped to ENT_PERSIST items so vanilla room pickups stay
  quiet). If the report was ever "I did not notice it", that is answered;
  if it persists, the remaining cause is entity lifetime and the next step
  is the live-play watch.
- ~~Castle Garden runs out of GFX sheets at difficulty 4~~ **FIXED.** It
  arrived with the wave rework (six-kind waves and a 12-sheet budget
  replaced a hard 3-kind cap that used to keep this room comfortable) and
  was confirmed pre-existing by building the previous commit and getting
  the identical failure. Traced before it was fixed: at difficulty 4 the
  free-slot count sat at ZERO for frames 0-58 while the room loaded its
  own furniture alongside the wave, then settled at exactly 2 - which is
  `QUICKSTART_GFX_HARD_FLOOR` itself, i.e. no headroom at all, while
  every other region ran 8 to 31 free. The fix is the per-region sheet
  budget the composition study named: Castle Garden's wave now spends 8
  sheets instead of 12. Free never drops below the floor now, and the
  checker's GFX tier passes all eleven regions.
  Two things worth keeping from the diagnosis: the GFX slot struct is 12
  bytes with a state nibble at +4 (a slot is used when that nibble is not
  0/1/2), and reading it any other way produces numbers that look healthy
  and are wrong - a first pass at stride 8 reported 23 free slots where
  the checker correctly saw 0. And a short sheet budget costs VARIETY,
  not difficulty: density and the caps are untouched, so the same number
  of enemies spawn from fewer sheets.
- **Boss death machinery family-scoping (#125) - the claimed softlock
  DOES NOT REPRODUCE on the current build.** The claim ("a simultaneous
  dual kill softlocks") predates the compaction that ate its analysis, so
  it was re-tested from scratch: two full families spawned side by side,
  every piece weakened to 1 hp, both killed through the real damage
  pipeline within the same quarter-second - all ten pieces tear down,
  nothing lingers, the player stays mobile, and the wave loop resumes
  (it rolled a fresh legitimate boss two rooms later). What that run
  does NOT cover: a dual kill of two ENGAGED bosses, because scripting a
  real kill of even one engaged boss is still unsolved (see the
  boss_region entry). Until that exists, #125 is DOWNGRADED from "hard
  blocker" to "needs a reproducing case": no fix will be written against
  a failure nobody can produce. The audit of the QUICKSTART-side sweeps
  found them already family-safe by construction (they match on id, not
  on a singleton, and the one Helper block is per-family heap).
- ~~Some Minish holes/entrances don't work (#103)~~ **FIXED, root cause
  found** (user, Aug 2026, pointing at the hole on North Hyrule Field's
  east side: "a hole in the ground that Link falls through as mini link...
  the Minish room that is not working").
  **A Minish hole is not a door and has no Transition row**, which is why
  every exit-table sweep this project has run - the #102 Minish sweep
  included - walked past all ten of them. It is room-property data driven
  by `SpecialWarpManager`: the room's entity list carries
  `manager subtype=0x6, paramA=N`, property N is a list of
  `exit_region_raw` boxes, each box names an `exitIndex` into the room's
  own property table where an `exit_raw` gives the destination, and the
  manager fires `DoExitTransition` when a Minish-sized player stands in
  the box. `tools/quickstart/minish_holes.py` walks that chain and prints
  every hole in the ring with where it goes.
  **The holes were never broken - all ten fire.** Seven landed in rooms
  this mode had not blessed, and
  `QuickStartEnforceFieldRegionContainment` cancelled the transition the
  same frame it started. Falling in and landing nowhere is exactly what an
  unblessed destination looks like from the player's side. Castle Garden's
  three holes were already content sites, which is precisely why its holes
  always worked and nobody else's did.
  **Five are now content sites** - NHF east (`MINISH_CRACKS_EAST_HYRULE_CASTLE`,
  the user's), NHF west (`DOJOS_TO_GREATBLADE`), Lon Lon's Minish path and
  its north crack, and Trilby's Knuckle house. Each is a dead-end pocket
  with one border back to the region room its hole is in, so blessing them
  opens no route out of the run; all five are checker-verified "landed,
  spots OK, 1 chest spawn verified". The two beanstalk climbs stay out for
  the same reason the beanstalk fusions do - they leave the ring.
  **Proven, not assumed:** NHF's west hole and Eastern Hills Center's
  beanstalk hole have identical bitfields and fire by the same manager. In
  the same build, the one whose destination is now a site drops the player
  through; the one that is still unblessed is cancelled and leaves them
  standing in the field.
- ~~Trilby Highlands' northwest ladder is a one-way trap~~ **FIXED**
  (user report, Aug 2026). Measured first: Trilby's northwest holds a
  raised pocket at tiles tx 2-12, ty 7-12, and a collision flood puts it
  in a component of its own - 44 tiles against the main room's 334, with
  nothing joining them. Walking every direction from inside kept the
  player inside. The Mole Mitts dig cave's mouth is IN that pocket, and
  vanilla's cave exit landed at (0x88,0x78), back in the pocket - so the
  cave was not a way out, it was the pocket's only furniture. The cave is
  now the descent: its overworld exit lands at (0x98,0x268), a spot
  vanilla itself uses for this region's other cave exit, so it is proven
  walkable and in the main body. Verified: walking out of the cave now
  puts the player at local (152,616), clear of the pocket.
  **The general shape, for the regions still to come:** leave the climb
  alone and make the pocket's cave the way back down. One retargeted
  transition row per region, no new machinery.
- **Trilby's NW enemy offset (120,24) sits in an isolated pocket**; **Lon
  Lon Ranch's top-middle pocket is unfenced** (no walked gating box yet -
  the user paused zone-gating pending their own walk). Both are data
  fixes waiting on the same harness.
- **The reachability harness (#81) is slow and crashes mgba** after
  enough reboots (worked around by process chunking, still slow). It
  gates the two items above; batch the fix with the next budget-harness
  work.
- ~~A Gyorg boss was in the Elite pool~~ **REMOVED** (user, Aug 2026:
  "this enemy is usually larger than the room and it really breaks the
  mechanics"). It was `ENEMY_64` - the enemy enum puts it at 0x64,
  directly after `GYORG_FEMALE_MOUTH`, and its handler calls into
  gyorgMale's, so it is a Gyorg boss part drawn at boss scale. It probed
  as a legal 36hp spawn, which is how it got in; that probe measured
  whether it spawns and dies, not whether it FITS. Its live-cap row went
  with it. The lesson generalizes to the rest of the roster: admission
  needs a size gate as well as a spawn gate.
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
- ~~Croissant charm launches Link through walls when rolling~~ **FIXED**
  (user report, Aug 2026: "when the player rolls the sprite jumps forward
  many frames, sometimes clipping the player through tiles and out of
  frame"). The walk-speed charm bumped `gPlayerEntity.base.speed` in place
  every frame inside UpdatePlayerMovement, trusting that the walk state
  re-derives speed each frame first - but PlayerRollUpdate only re-derives
  on frames 0-3 of its animation cycle and calls UpdatePlayerMovement
  every frame, so during a roll the bump compounded 1.5x per frame,
  overflowed the Q8.8 s16 speed, and the resulting hundreds-of-px steps
  tunneled through collision. Now boost-move-restore: the 1.5x applies
  around the position integration only and the field is restored after,
  so it cannot compound in ANY player state. Verified live: the walk boost
  still measures exactly 1.5x with no residue in the speed field, and
  twelve consecutive integrations at roll speed leave it byte-identical
  (the old code made that 130x and an overflow). Doctrine: **a per-frame
  multiplicative buff must never persist into the field it scales** -
  "some state re-derives this" is an alibi that holds exactly until the
  one state that doesn't.

### The large-area slowdowns: reproduced, diagnosed, and FIXED (Aug 2026)

The user's report: big framerate drops in NHF, SHF and Lon Lon persisted
after the enemy cap was dropped, "indicating that it wasn't the enemy
count OR variety." Reproduced under cycle-accurate timing (the tick-skip
metric reads the game's true hardware frame rate), so it is NOT the
user's emulator. The bisect - one variable at a time, difficulty 12 -
acquitted every suspect but one:

- **QS room monitors, ground-item litter, area size: innocent.** Empty
  NHF holds a locked 60.0. 24 ground items on the floor: 60.0. The same
  24 enemies in NHF and in a tiny cave: 60.0 both. (The earlier battery's
  "litter drags fps" reading was confounded - it ran on top of a
  leftover wave.)
- **Raw headcount below the ceiling: innocent.** 28 keese, 38 keese,
  even 48 keese standing still: 60.0 flat. Twelve of ANY single roster
  kind: 60.0.
- **Total live entities past ~45, plus scrolling/combat: guilty.** The
  real NHF entry wave at difficulty 12 measured 41 live enemies - 59.9
  standing still (borderline), 54.5 avg / 38 worst while fighting, and
  43.5 at 51 / ~31 at 55. The skip cadence at the floor is exactly the
  alternating-frame "halved fps" the user sees.

**Why 41 live enemies exist under a 28 ceiling:** the frame-budget cap
(`QUICKSTART_MAX_LIVE_ENEMIES` 28, set in the previous performance round)
clamps the wave's PLACEMENT count against what is alive at deal time -
but a placement is not an entity. Probed one-by-one, five roster kinds
multiply after the clamp: **MOLDWORM x9, MADDERPILLAR x7 (already
live-capped to 2), MOLDORM x4, ENEMY_50 x4, BOMB_PEAHAT x2, RUPEE_LIKE
x2** - they are segmented chains (or spawn a partner), every segment a
full enemy entity the frame must update, collide and draw. Censused at
NHF entry, difficulty 12: the wave dealt 16 placements (8 red chuchu + 8
moldorm) and the moldorms alone became 32 entities - 40 live, 143% of
the ceiling. Once over, the next deal's headroom is zero so the room
HOVERS above the cap until enough segments die; and each 1-placement
top-up can itself be a x4/x9 draw. That is also why dropping the cap
changed nothing: the cap held perfectly - in placements.

**The fix SHIPPED** (the turn after the diagnosis): every spawner now
charges each placement its measured entity cost against the room's live
budget (`QuickStartKindEntityCost`: moldworm 9, madderpillar 7, acro gang
6, moldorm 4, enemy_50 4, bomb peahat 2, rupee like 2, everything else 1).
The wave dealer swaps an unaffordable kind for a loaded kind that fits -
the same redirect shape the live caps use - and the single-kind placer
divides its count by the kind's cost (floored at one placement so miniboss
and Lost Woods set pieces can never wedge their rooms). Verified on the
same seed that produced the 41-entity NHF entry: the identical
moldorm-heavy draw now lands at exactly 28 entities, and the sword-mash
measurement went from 54.5 avg / 38 worst to 60.0 / 58.0.

Alongside it, the per-region maxEnemies hand caps are RETIRED for a
size-scaled ceiling (`QuickStartRoomEnemyCeiling`: 14 + squares/50, capped
at the hardware 28) - the user's brief: the largest continuous areas carry
the most enemies, the small rooms still read busy. NHF gets the full 28,
SHF/Lon Lon 27, WW North 26, the mid rooms 18-23, and the smallest shelves
15-16 where the old hand caps starved them at 5-9 (measured post-fix:
Ruins entrance 8 entities vs its old cap of 5, WW Center 11 vs 9). Two
constraints still bound small-room fights: the difficulty-sloped GFX spawn
cap (16 placements at difficulty 8+, a sprite-table property) and each
room's verified-spot pool.

**The spot-survey round then grew the eight skimpy pools** (+61 spots:
EHS 9->16, EHC 15->26, EHN 20->34, WW South 14->20, WW Center 11->22,
WW North 24->38, Ruins entrance 4->5, Ruins below 12->17). Method worth
keeping: flood from the region entrance over open ground PLUS tiles the
ROM's own `QuickStartTileIsBush` confirms as the cuttable class (bushes
join components - the player cuts through - but no spot stands on one);
every candidate needs a strictly-open 3x3 and a TRUE from the shipped
`QuickStartTileHasElbowRoom`, called in the running game. The
bush-verified flood reproduces the recorded room surveys (EHS 258 tiles
vs 265 recorded), and the shrub bridge is NOT trusted outside the Hyrule
Field tileset - the Ruins rooms got a strict open-ground flood, which is
why their hauls are small: the Ruins entrance genuinely has 12 elbow-room
tiles, and its floor, not its ceiling, is the limit. Measured after: EHN
and WW Center enter at exactly their ceilings (23 and 16) at 60fps.

The survey also flushed a second budget race the small ceilings made
visible: the Ruins quirk hook deletes its vanilla armos garrison in the
same monitor pass the first wave deals, DeleteEntity corpses keep their
kind byte until next frame's cleanup, and the garrison-counting budget
dealt a 2-enemy wave into what was about to be an empty room.
`QuickStartCountRegionEnemies` now skips corpses by the engine's own
deleted test (prev < 0). Measured after: Ruins-below entry went 2 -> 7
visible entities with 12 of its 16-entity budget charged (an Acro gang
rides coiled as ONE entity until it bursts, and bomb peahats pair) - the
budget is honest even when the room looks sparser than it is. The Ruins
entrance still varies with the archetype roll: a lone-heavy shape deals
one strong body on some seeds, a fuller shape deals its five spots.

Measurement doctrine that made this findable:
`scratchpad/multiplicity.py`'s spawn-ONE-and-count is the admission gate
any future roster row should clear; the old entrance-spot fps probe
passed the broken build because it sampled rooms whose draw happened not
to include a multiplier.

### The Castor Wilds batch (Aug 2026, all shipped)

Five user reports off the first Castor Wilds playthroughs, all fixed in
one pass:

- **The statue passage stayed blocked despite the pre-fused kinstones.**
  The fused bits alone are not the passage: the statue NPC stamps the
  bottom-left tiles (1,58)-(3,59) solid whenever `HIKYOU_00_SEKIZOU` is
  unset (castorWildsStatue.c), and vanilla only sets that flag at the end
  of the rock cutscene the three fusions trigger - which pre-fused bits
  skip. Run start now sets the flag the cutscene would have
  (`SetLocalFlagByBank(GetFlagBankOffset(AREA_CASTOR_WILDS), ...)`).
  Verified: all six passage tiles read open, statues stand in their
  stepped-aside pose, art intact.
- **The Wind Tribe tower's front door rendered as a black box.** The old
  fix stamped `TILE_TYPE_0` over the doorway - the painted-tile trap,
  again (type 0 has no art in that tileset). The block was never ours to
  carve: `sub_StateChange_WindTribeTower_Entrance` stamps SPECIAL_TILE_114
  over the doorway whenever the `WARP_EVENT_END` story flag is unset. Run
  start sets the flag; the room draws itself open. Verified: walked out
  the front door to Cloud Tops in 60 frames, doorway art vanilla.
  Doctrine, third strike and now law: **when a vanilla room hides or
  shows tiles, find the flag its StateChange keys on - never repaint.**
- **Nine unwired doors and holes are ? rooms now.** Castor Wilds' five
  Minish holes (the Bow path with both its holes, three cracks), the
  Scarblade dojo hole, Swiftblade I's grave dojo, the Minish water cave
  off the south-east door, and the Wind Ruins entrance crack. The site
  table was FULL at its 61-site flag ceiling, so these are the first
  EXTENSION sites: site indices 61+ route their 13 bits through free
  window runs (208+, 496+, 617+, 658+) plus the head of bank 11's retired
  wave-counter range (QsCheckSiteFlag/QsSetSiteFlag; capacity 9, all
  inside existing run wipes, flags tier green at 1487 claimed bits).
  Spots surveyed per room with origin correction - DOJOS and MINISH_CAVES
  share multi-room pixel grids, and a flood keyed on room-local arrival
  coordinates reads walls there (the survey now floods from the player's
  settled tile).
- **Castor Wilds has kinstone fusers now** (user: none spawned there at
  all). Five fusions, every payload inside the region: KINSTONE_56/57/58
  are the hole-reveal fusions for the region's own Minish cracks - fusing
  IS how those new ? rooms open - plus KINSTONE_40 (west-edge pocket) and
  KINSTONE_44 (the Scarblade hole, whose world event also pays the Fast
  Spin scroll). All shapes 16-18, pieces the droptable mints. Nine
  scatter spots drawn from the region's verified enemy-offset grid.
  Verified: five fusers stand on scatter spots at region entry.

### The Castor Wilds / Wind Ruins second batch (Aug 2026, shipped)

- **Castor Wilds spawned everything in one corner.** The first survey took
  the north-east dry bank for the whole region: 28 spots in a corner of a
  63x60 room, `roomSquares` 244. Re-flooded whole, the Wilds are 1933 open
  tiles in 33 components - two of them the map: the arrival's northern
  landmass (644 tiles) and the southern one (1078), with nothing joining
  them on foot. The grid is **72 spots** now (the spawner's own index
  ceiling, so nothing is truncated): 46 across the north, 26 across the
  south, `roomSquares` 483. Measured with gear: waves span local y 71-942
  across both islands; without, they stay north.
- **The sludge crossing is boots OR cape.** `QuickStartGatedZone` grew a
  trailing `altItem`, so one zone can name two keys - the south landmass
  is gated on Pegasus Boots or Roc's Cape rather than whichever one the run
  happened to draw. (Trailing field, so every existing row is untouched.)
- **The last two Castor cave doors are ? rooms**: the Darknut hall (the
  user named it) and the south cave, surveyed room-local at 34 and 67
  tiles. Extension capacity went 9 -> 11 sites by widening the bank-11
  routing run and extending that bank's run-start wipe to 173 (174 is the
  seed pin and stays).
- **The Wind Ruins' sub-areas are populated.** Like Eastern Hills and the
  Western Wood, the Ruins are one area cut into six seam-joined rooms, but
  only two are pool regions and the pool is at its 16-row 4-bit ceiling.
  So satellites: a small table of (area, room, offsets, squares) that
  fills a seam neighbour once per visit off the same tiered group spawner,
  with no reward, quest or wave state of its own - the hub roof's shape.
  Beanstalk, Tektites, Ladder-to-Tektites and the Fortress approach all
  deal 2-5 enemies now where they used to be empty.
- **The inn's chests were free loot.** The blanket small-chest restock was
  filling all three, so the player could walk upstairs and open them
  without renting a bed. The restock skips the inn now; the chests are
  sealed at run start through the same local flags `SpecialChest` reads to
  delete itself; and paying deals exactly one - 50 rupees a COMMON, 200 an
  UNCOMMON, 500 a RARE - re-arming on the next purchase since beds repeat.
- **Still open from this batch**: `ROOM_DIG_CAVES_1` and `_2` (the
  suspected dirt-filled caves) read zero open tiles on a cold warp, so
  either they need their entrance's own load path or they are unused
  rooms. They want a walked check from the overworld mouth before being
  wired, exactly like the Trilby dig cave got.

### Hub polish + the Western Wood brush fusions (Aug 2026)

- **The wind-crest sign was in the doorway's line.** The tower door sits at
  Cloud Tops local x 488 and the drop hole is straight south of it, so the
  sign at (488,440) was standing in the path every run took after the item
  draft. Moved to (552,456) - still beside the crest, off the axis, and on
  a tile with full elbow room (the first candidate, (568,456), was open but
  pinched, which the shipped predicate caught).
- **Three vanilla chests removed** (user report): the hub shop's, the two
  behind the spawn room's display case - which also stole the case's own A
  press, since a chest registers as an interactable and won that contest -
  and the forge chest in Link's house. Sealed at run start through the same
  local flags `SpecialChest` reads to delete itself, the mechanism the inn
  chests already use. The bedroom's three lottery chests are ours and stay.
- **The Western Wood brush fusions reveal ground, by design** (research
  answer). Those fusions are `WORLD_EVENT_TYPE_6`, and its handler
  (`sub_08018AB4`, kinstone.c) does exactly one thing: while the fusion is
  UNDONE it stamps a 4x3 patch of brush art over the spot, bottom layer and
  top. Fusing does not add anything - it stops the stamp, so the map's own
  ground shows through and the patch becomes passable. There is no entity
  load, no transition, no dig tile and no chest anywhere in the event data,
  which is why nothing is behind them: in vanilla the payoff is the SHORTCUT
  itself, not a treasure, and nothing needs digging up.
  **What went on them: BOTH, rolled per run** (the user's call). Each of
  the two brush patches pays out once, in one of two moods decided by an
  avalanche hash of (run_seed, kinstone id) - so the two can differ inside
  a run and both differ across runs, with nothing stored:
  - *reward* - a common-or-uncommon draw lying in the clearing.
  - *challenge* - an UNCOMMON draw with a pack of this difficulty's own
    enemies ringed around it (3 + difficulty/4). The prize is placed WITH
    the guards rather than behind them, so there is no clear-detection to
    get wrong and nothing is lost by leaving mid-fight: come back and the
    pack re-deals around a prize still lying there.
  Built on the Tingle payout's exact shape (poll `CheckKinstoneFused`, pay
  once per patch via a bank-11 paid bit, deliver through
  `QuickStartRewardDelivered`), with its own Ezlo line per mood (strings
  237/238). Verified across pinned seeds: reward/reward, challenge/
  challenge and a split run all pay at the right patch coordinates with
  guards only in challenge mode. One honest degradation: the guard pack
  goes through the same entity-cost budget as everything else, so in a room
  already carrying a full difficulty-12 wave the guards may not fit - the
  prize still lands, the clearing is just quiet.

### ? event variety: the roll was fair, the TABLE was not (Aug 2026)

User report: "a noticeable lack of variety in ? events... I think I only
received pot rewards for every room I entered." Measured before changing
anything - forcing every site's roll across pinned seeds and reading the
dealt kind back out of its flags - and the pickers themselves were clean:
the small pool's four kinds came out near-even, the engine's own
`Random() % 4` is well distributed (checked against the real generator,
`gRand = ror(gRand * 3, 13)`), and no kind was starved by the unlock
fallback. The bias was structural:

- **57 of 72 sites were `QUICKSTART_KINDS_SMALL`**, and SMALL's pool is
  the four quiet kinds only. Miniboss, gauntlet, gate puzzle and fairy
  rooms live in the LARGE/ANY pools, which ten sites had between them - so
  a run realistically never met one.
- **Three of the small pool's four kinds are "collect a prize out of a
  container"** (item drop, pot lottery, chest lottery), so even a fair
  roll produced the same texture three visits in four.

Two fixes, both measured:

1. **Reclassified by measured floor space.** Every site room was flooded
   from its own content spot and its tiles with full 3x3 clearance
   counted; the eleven SMALL rooms with 20 or more went to `KINDS_ANY`
   (Swiftblade's dojo alone has 52). Cramped rooms stay SMALL. ANY sites:
   7 -> 18.
2. **FAIRY joined the small pool**, weighted 1/9 against 2/9 for each of
   the four originals - it needs almost no floor and is the one small-room
   kind that is not a prize to pick up. A flat fifth measured at 17% of
   all sites, which is more free healing than the economy wants; 1/9 lands
   it at 11%.

Measured after, same method, 288 site rolls over four seeds: pot 22%, NPC
19%, item drop 16%, chest 15%, fairy 11%, miniboss 10%, gate 4%, waves 4%.
**Container-prize share 70% -> 53%; combat/puzzle/fairy 14% -> 28%; all
eight kinds now appear in every seed.**

### The combat rebalance: rare fairies, no free prizes, gauntlets everywhere (Aug 2026)

The follow-up to the variety pass above, and the user's spec verbatim:
"bias fairy rooms down - these should be considered rare events...
completely eliminate rooms that just drop a prize immediately, except for
the central boomerang room in NHF... increase the amount of combat style
rooms (waves, mini bosses, survive n seconds)... we can add in the 'wave'
and 'survive N seconds' type to the small rooms, but we shouldn't put mini
bosses in those rooms. Don't use Ravens for wave or survive N seconds type
spawns."

Five changes, all in the three kind pickers plus the wave spawner:

1. **`QS_EVENT_ITEM_DROP` is out of every draw.** It survives at exactly
   one site - the Boomerang chamber's central staircase
   (`QUICKSTART_KINDS_RARE`), which is gated behind four kinstone fusions
   and pays a RARE item for them. Earning a free prize is fine; tripping
   over one is not. The unlock fallbacks mattered as much as the draws
   here: all three pickers used to degrade a locked kind to the item drop,
   which would have quietly reinstated it for any save that had not earned
   the lotteries yet. Small now splits its fallback between NPC and the
   gauntlet; ANY and LARGE fall back to the gauntlet.
2. **The gauntlet joins the small pool** at 6/16, which brings the survive
   clock (one combat visit in three, decided per visit) and the
   stripped-kit handicap (one gauntlet in four, extra bit 6) into cramped
   rooms with it - one kind added, three textures gained. The MINIBOSS
   deliberately stays out of SMALL: a set-piece body needs room to circle.
   That inverts what the size gate is for - it used to separate combat
   from quiet content, and now it holds back only the miniboss and the
   gate puzzle, the two kinds that genuinely need floor.
3. **ANY went to half combat** (4/16 waves + 4/16 miniboss) and gave the
   gate puzzle 3/16; those eighteen sites are the only ones with floor for
   a set-piece fight and they were spending a third of their draws on a
   dropped prize or a fairy. LARGE is 13/16 combat.
4. **FAIRY is 1/16 in every pool** (it was 1/9 in small, 1/4 in large),
   measured at 4.5% of all sites - the user's "rare event".
5. **No Ravens in a gauntlet or on a survive clock.** A CROW flies a wide
   erratic circuit and will not commit to the player, so a wave of them is
   dead air against the clock and a stalemate in a cramped room.
   `QuickStartSpawnWave` re-rolls up to four times rather than
   substituting outright, so the wave still gets a difficulty-appropriate
   draw; only a run of rolls that all land on the bird falls back to a
   beetle.

One safety net came with #2: a wave that places nobody reads as instantly
cleared, and three of those in a row hand the reward over for free. That
was theoretical while gauntlets lived in roomy sites; with cramped rooms
rolling them, `QuickStartSpawnWave` now puts one body on the content spot
itself if the ring placer comes back empty.

**Measured after, 201 site rolls over six pinned seeds** (each seed walked
into every site room, kind read back out of its own flags):

| kind | share | | kind | share |
|---|---|---|---|---|
| waves | 26.9% | | pot lottery | 11.9% |
| NPC | 17.9% | | chest lottery | 11.4% |
| miniboss | 16.9% | | gate | 7.5% |
| | | | fairy | 4.5% |
| | | | item drop | 3.0% |

Combat is **43.8%** of all sites, up from 14%. Every one of the six item
drops is the RARE boomerang site - the kind appears nowhere else. No SMALL
site rolled a miniboss in any seed. 11 of the 54 gauntlets (20%) carry the
stripped-kit handicap.

Two side checks, both on the same build. Forcing eight of the tightest
SMALL rooms to `QS_EVENT_WAVES` and watching each for eight seconds: all
eight spawn a four-body wave and hold it, so the cramped-room gauntlet is
a real fight rather than a walkover. And across 92 sampled wave-room
visits at difficulties 0 and 8, a Raven appeared exactly zero times
(average 4.6 bodies per wave).

One fix fell out of the rebalance. The invariant checker's "a 2-door
room's entrance must be open floor" rule started failing on
`ROOM_VEIL_FALLS_CAVES_EXIT`: with the new weights that room drew the pot
lottery on the default seed, and the field reached the arrival tile - a
pot the player has to break before they can leave by the door they came
in. The pot layout anchors on wherever the player is standing when the
room settles, which is not always that doorway, so the arrival tile is now
denied in the reachability set the two fill passes share
(`QuickStartPotRoomKeepClear`). Denying rather than deleting matters: the
counting pass and the spawning pass have to see the same field, or the
winner index lands on a pot that never spawned and the room is
unwinnable.

### Travelling fusions, and fuser sprites that actually move (Aug 2026)

Two things, both from play. "The Zelda sprites always spawn into the exact
same positions and it gets a bit boring", and a new mechanic: "when the
player fuses kinstones with a Zelda sprite, the place it unlocks can be up
to 1 world region away... sprites in EH can unlock things in Lon Lon Ranch,
NHF sprites can unlock things in Trilby Highlands".

**Why the positions never moved.** The old rule was
`slot = (indexInRegion * 4 + a 4-bit run roll + roomIndex * 2) % 9`. Four
and nine are coprime, so no two fusers in a room ever collided - but the
whole expression is one fixed order with a per-run STARTING POINT. North
Hyrule Field's six fusers took the same six spots in the same sequence
every run, rotated. Sixteen rolls, nine rotations, one arrangement.

It is a real permutation now: a seed-derived STEP through the nine spots
(always coprime with nine, so still injective) plus a seed-derived offset.
54 distinct layouts per room instead of 9 rotations of one.

**How a fusion travels.** A fusion's payload is vanilla world-event data
and fires where `gWorldEvents` says it does, so what moves is the SPRITE:
the sprite offering the Trilby fusion may be standing in North Hyrule
Field. Candidate hosts are the fusion's own room plus every fuser room
whose named region is adjacent on the map graph - the same
`sQuickStartRegionAdjacency` the element's hiding place already uses - so a
fusion can still turn up exactly where it always did.

Three rules keep it from breaking a run:

- **Castor Wilds exports only.** Its region is a swamp crossed with the
  Pegasus Boots or Roc's Cape, so a Western Wood fusion hosted there would
  be unreachable until the player finds one. Fusions homed in the Wilds may
  travel out; nothing travels in.
- **Nine per room, the spot count.** A fusion that would be the tenth falls
  back to its home room, then to any room with space. 34 fusions, 81 spots.
- **One ordered pass.** The whole assignment is resolved in a single pass
  over the table with a live count per room, which is what makes the answer
  identical no matter which room the player is standing in when it is
  asked. Anything less than that and a fusion could exist in two rooms, or
  neither.

Measured over three pinned seeds: all 34 fusers standing in every seed, and
the spread moves a long way run to run - North Hyrule Field hosted 8, then
3, then 3; South Hyrule Field 3, 5, 6; Trilby 4, 5, 7; Castor Wilds 4, 2, 2
(never more than the 5 it homes, as designed). Spot indices differ per seed
in every room.

The invariant checker's fuser tier moved with it: a room's population is a
per-run draw now, so "as many occupied spots as fusers homed here" is no
longer the invariant. Every spot room is walked (not just the ones that
home a fuser), every spot is still verified reachable and open, and the
count check is global - all 34 fusions standing somewhere, exactly once.

### The Pacci drop: Castor Wilds and the Wind Ruins need swamp kit (Aug 2026)

User report: taking the Cane of Pacci in the hub's gift round and being
dropped into Castor Wilds and the Wind Ruins, which are islands in a swamp
that needs the Pegasus Boots or Roc's Cape to cross. A player dropped there
with neither can neither explore the region nor leave it.

The check could not live in the draw. The drop region is rolled on frame
one, well before the gift round has happened, so nothing about the player's
kit is known yet. It lives at the FALL instead
(`QuickStartDropRegionIndexUsable`), which is the first moment it is - and
the correction is latched back into the drop bits rather than recomputed,
so "every fall within a run lands in the same place" still holds after the
player finds a pair of boots halfway through.

Measured, forcing the drop to each of the three swamp rows: with no kit all
three redirect (to North Hyrule Field on the test seed), and the control
row is untouched; with the Pegasus Boots written into the inventory, Castor
Wilds and the Ruins Entrance both land where they were drawn.

### ? room spawns keep clear of the door (Aug 2026)

"For certain ? rooms, especially the smaller ones, we need to make sure
that enemies spawn sufficiently away from the door entrance... sometimes
during waves an enemy will spawn under them. The ball-and-chain enemy also
poses a problem... they can hit the player immediately on entrance causing
an auto-death."

The placer's ring search starts at the content spot, which in a cramped
room is where the player is standing when the room settles. Two radii now,
because reach differs: two tiles for everything, four for the
BALL_CHAIN_SOLIDER, whose swing covers the ring around it. The wider one is
enforced only while the placer is still being picky - a third relax pass
drops a long-reach kind back to the ordinary two rather than spawning
nothing, which would hand the room's reward over uncontested. The
empty-wave fallback added last week was rewritten for the same reason: it
used to drop a body on the content spot, which is exactly the ambush this
rule exists to prevent, and now walks out to the first open tile that
clears the player.

Measured in the eight tightest rooms that host a gauntlet: the closest
spawn to the player is 3 tiles in seven of them and 5 in the eighth, with
3-4 bodies landing in each.

### The large-area lag, profiled properly (Aug 2026)

Reported again from two devices - an iPhone 15 running Delta and a 2025
MacBook Air running mGBA - with the same signature both times: entering
North or South Hyrule Field makes the gameplay lag, while **the FPS readout
stays at 60 and the music stays in time**. Earlier rounds moved enemy
counts, enemy variety and the RAM/VRAM caps and none of it helped, which is
what finally made it clear that the question was wrong: the frame rate was
never the problem.

**What that signature actually means.** The LCD refreshes at 60Hz no matter
what the CPU is doing, and the sound driver is fed from the VBlank
interrupt, so both keep perfect time even when the game itself is late.
What can be late is the main loop: it does a frame's work, then waits for
the next VBlank. If the work overruns the frame's 280,896 cycles, the wait
returns a vblank LATER than it should and the game updates once per two
refreshes. An emulator reports 60 FPS throughout; the music never stutters;
the game moves in lurches. That is the report, exactly.

**A profiler, finally.** mgba's Python bindings can single-step, and they
step about 1.4 million instructions a second, which is fast enough to
profile a real frame. `prof2` steps the CPU, samples the PC every 8
instructions, resolves each sample against `nm tmc.elf` (every local static,
not just the linker map's exported symbols - the first pass attributed a
quarter of the file to `GameTask` because the statics after it had no
entries), and brackets frames on `gRoomTransition.frameCount`, which
GameTask bumps once per main-loop pass. Bracketing on the BIOS halt does
not work: every interrupt enters the BIOS, so the halt is not a frame
boundary.

Two things that do NOT work and are worth writing down. Counting samples
inside the BIOS to measure idle time gives nonsense, because mgba collapses
the whole VBlankIntrWait halt into a single step - the first run of this
reported "99% busy" everywhere, including in an empty room. And the
logic-frame-rate check (frameCount increments per 600 video frames) reads
100% in every region room in this harness, standing still or walking, at
difficulty 0 and 12 - so the overrun is not reproducible here, only the
load that causes it.

**What one frame costs.** Instructions per frame, North Hyrule Field:

| | before | after |
|---|---|---|
| standing still | 60,210 | 52,621 |
| walking (average) | 85,896 | 75,175 |
| walking (worst frame) | **140,960** | **90,536** |
| QuickStart* share, walking | 17.3% | 9.5% |
| QuickStart* share, standing | 24.4% | 13.2% |

THUMB code fetched from ROM averages around three cycles an instruction, so
a 141,000-instruction frame is roughly 420,000 cycles against a budget of
280,896. **Those frames could not fit**, and a frame that does not fit is
the lurch. The average frame fit; the peaks did not.

**Where it goes.** Of the frame as it stands: about 40% is the M4A sound
mixer (the `SoundMainRAM` copy in IWRAM at 0x030042e8-0x0300432c - vanilla,
untouched, and confirmed running vanilla's own settings: 8 channels,
frequency index 5, `maxLines` 0), about 10-13% is ours, and the rest is the
engine's own entity, collision and drawing work over the 17-29 enemies a
region wave puts on the field.

**Two suspicions ruled out with measurements.** The GamePak wait states are
already optimal - `REG_WAITCNT` reads 0x4314 at runtime, which is WS0 3/1
with the prefetch buffer ON, so the ROM is not being read slowly. And the
sound engine is configured exactly as vanilla configures it, so nothing we
re-appropriated made the mixer more expensive.

**The fix: a frame-phase scheduler.** `QuickStartRoomMonitor` was calling
about fifty of our monitors on every single frame. Most are not per-frame
work by nature - they are idempotent sweeps that fix up world state, and
several walk the whole 72-entity table to do it. The worst single one,
`QuickStartSpawnRegionFusers`, walked the entity table once per fuser in
the room (six times in North Hyrule Field) every frame, to answer a
question that only changes when a room loads or a fusion completes.

`QuickStartPhase(slot)` is true on one frame in eight, and callers pass
distinct slots so the work spreads across the cycle instead of bunching:

| slot | what runs there |
|---|---|
| 0 | placed-item timer refresh (the timer it writes is 600 frames long) |
| 1 | the nine latched one-shot per-run draws |
| 2 | room-fixture fixups, reward sparkles |
| 3 | chest restock, Boomerang chamber, ranch-house doors |
| 4 | boulder-hole settling |
| 6 | region fusers; the stuck-wave rescue |
| 7 | the Tingle and brush fusion payouts |

Plus the region monitor's alive-count bookkeeping, which was a full entity
sweep and an 8-bit flag read every frame and is 3.3% of a region frame on
its own; nothing reads the stored remainder until the player leaves the
room, and the update is a min-update, so a later sample can only be more
correct.

What is deliberately NOT staggered: anything that has to observe a single
frame to be correct (containment, door redirects, the handicap monitor, the
food effects, the HUD, the region monitor itself, every ? room's own
content dispatch), and the two global safety valves. The GFX reserve was
staggered in the first attempt and the invariant checker caught it
immediately - free slots dipped to zero between enforcements in two
regions - so it went back to every frame, which it can afford: it never
appeared in the profile at all.

**Where the remaining headroom is**, in order of size:

1. **The 40% audio mixer.** Vanilla's, and the biggest single item in the
   frame. `maxLines` is 0 (unlimited); setting it would cap the mixer's
   share at the cost of audio quality under load. Worth an experiment.
2. **Enemy count.** After audio, the engine's per-entity work over 17-29
   enemies is the frame. The room ceiling is 28; every enemy removed is
   real cycles back. This is the lever previous rounds pulled, and it does
   work - it just was not the whole story.
3. **Our remaining ~10%**, now mostly flag reads (`ReadBit` and
   `CheckLocalFlagByBank` together are still ~4% of the frame, and we are
   the dominant caller). Batching them would mean reading whole flag BYTES
   instead of calling a function per bit.

**Two open checker results, both pre-existing.** With the default seed the
GFX-reserve tier reports North Hyrule Field dipping to 1 free slot (the
floor is 2) for a few frames at difficulty 4; seeds 2, 3 and 7 are clean on
that tier. On seed 7 the rooms tier reports the forced chest in
ROOM_CASTOR_CAVES_DARKNUT not appearing - the ROM built from the previous
commit fails that one identically, so it is not from this batch. This check has been
marginal in that room for a while - the ROM shipped before this batch fails
the same check on seed 1 - and the batch changed the RNG stream (one
`Random()` call retired with the fuser scatter roll, and the per-run draws
moved to a phase slot), which moved which seeds land on a three-sheet wave.
It is a dip in RAW free slots; the game's own spawn gate is on RECLAIMABLE
slots, which stayed above its floor, and the fuser change is not the cause
(measured: four fuser sprites in the room, all sharing one sheet). Worth
tightening the wave's own sheet budget by one next time this area is open.

### Can we turn the sound mixer off? Measured (Aug 2026)

Asked directly after the profiling round: the mixer is 40%+ of the frame -
would switching it off hand that back? **No, and the honest number is 26%.**
Every row below is the same room, the same walk, the same profiler, with
one thing changed in m4a's live `SoundInfo`:

| | instr/frame | vs shipped |
|---|---|---|
| as shipped (8 channels, reverb 40) | 68,390 | — |
| reverb off | 65,719 | −3.9% |
| 8 → 6 direct-sound channels | 67,149 | −1.8% |
| 8 → 4 direct-sound channels | 61,005 | **−10.8%** |
| reverb off + 4 channels | 58,056 | **−15.1%** |
| direct sound OFF entirely | 50,464 | **−26.2%** |

The gap between "the profiler says 43% is in the mixer" and "silencing it
gives 26% back" is the DMA and interrupt path, which runs whatever the
channels are doing. Silencing direct sound also means no music and no
sound effects, which is not a shipping option.

Two things that do NOT work: the mixer FREQUENCY field is only read when
m4a initialises, so writing it live changes nothing (measured: 0.0%); and a
song change re-runs m4a's setup and puts vanilla's reverb back (measured:
40 in the hub, 30 in North Hyrule Field on the stock build), so anything we
set has to be re-asserted rather than set once.

**Shipped as a knob, not a change.** `make quickstart-audiolight` builds
with four channels and no reverb; the default build is untouched and
byte-identical with the knob in the tree (verified by md5). On that build,
North Hyrule Field walking goes 66,821 → 58,618 instructions per frame and
the worst frame 148,416 → 92,040. The cost is audible: fewer simultaneous
sounds, so a new effect cuts an older one off sooner, and no reverb tail.
Whether that trade is worth it is a listening decision on real hardware.

### The dojo switch puzzle: two plates in one tile, and no penalty (Aug 2026)

Photographed in play: the two linger plates spawned on top of each other,
and the puzzle read as "press one, nothing happens; press the other, take
the prize."

**Why they stacked.** `QuickStartLeverAtTile` - the "is a fixture already
here" test the spot search runs - only ever matched `LIGHTABLE_SWITCH`.
Pressure plates were invisible to it, so plate two's search happily
returned the tile plate one was standing on. The mirrored anchor was
supposed to throw plate two across the room, but the mirror is CLAMPED back
inboard, and in a room as small as a dojo the clamp puts it straight back
where it started.

Three fixes: the occupancy test sees plates now; plate two is searched with
plate one as a second point to keep its distance from (six tiles, walked
down to three); and a room that cannot hold both a walk apart falls back to
the single-switch gate instead of dealing ONE plate - which was not a hard
puzzle but an unsolvable one, since both bits can never be up. Measured
across five site rooms and two seeds: every plate deal is now 6-8 tiles
apart (average 7.2), and the one room too small for the variant
(ROOM_DOJOS_TO_SCARBLADE) now deals the gate instead.

**And the wrong answer costs something.** Per the user: "something bad
should happen if you press the wrong switch - enemies spawn, you lose a
heart, you lose some rupees." The decoy variant deals three switches as
prize / trap / dud, and the dud used to be *exactly nothing* - the switch's
own click - which is what made a three-way gamble read as "press them until
one works". Now:

- **dud**: a rupee toll, `20 + difficulty * 5`, never more than the player
  is carrying, with its own line so the player knows what just happened;
- **trap**: still rings the player in primed pots, and now calls in the
  beetle-and-Bobomb pack as well. Being ringed in was easy to miss - a
  trap-pot cage is liftable, and players walked out of it without noticing
  they had sprung anything. A pack landing on them cannot be missed.

The linger plates got the same treatment from the other side: with one
plate down and the other still up, the run between them is contested by the
same pack, on the same live-count guard, so stepping on and off cannot
flood the room.

### Round two on frame time: the mixer's sample rate, and two latches (Aug 2026)

Asked what else was on the table after the first pass. Three things were,
and together they take a North Hyrule Field frame from 81,240 instructions
to 42,224 at the far end.

**A finer profiler first.** The sampler now attributes every sample to the
SOURCE OBJECT it came from (linker-map section ranges) as well as the
function, and it separates m4a's IWRAM mixer buffer
(0x0300404c-0x030043cf) from the engine's other IWRAM-resident code. That
turned "45% is in IWRAM somewhere" into "37.75% is the mixer, 3.7% is the
engine's IWRAM code and the interrupt handlers".

**1. Two per-frame sweeps that only needed to run once per room visit.**
Both were ours, and both were near the top of the profile:

- `QuickStartResetOtherWaveRemainders` asked all fifteen regions for an
  8-bit counter, every frame - and every one of those bits is a routed
  flag read. `QuickStartRegionGetAliveCount` + `QuickStartSlotBitCheck` +
  `ReadBit` were ~4.5% of the frame between them, almost all of it this one
  caller. Once per visit is not an approximation: the sweep clears every
  region EXCEPT the one the player is in, and while they are standing in
  it nothing can write another region's counter.
- `QuickStartFuserPlacements` (new last round) walked the whole fuser table
  with a nine-row room lookup per row, every frame, to answer a question
  that only changes when a room loads or a fusion completes - and both of
  those wipe the room flags, so the latch is exactly as fresh as the
  question. Latched only on a COMPLETE pass, so a spawn refused for want of
  a gfx slot retries next frame.

Plus the region quirk hooks (the delete-vanilla-content-on-sight sweeps -
North Hyrule Field's prologue scrub was 1.6% by itself) now run one frame
in four. Nothing races them: the content they remove is placed at room load
and sits there until something deletes it.

Result: **`src/game.o` went from 20.5% of the frame to 6.8%**, and the whole
frame from 81,240 to 64,205 instructions (-21%), worst frame 138,056 to
85,200 (-38%).

**2. The mixer's SAMPLE RATE is a compile-time constant.** `m4aSoundInit`
calls `m4aSoundMode(... SOUND_MODE_FREQ_15768 ...)`, and mixing cost scales
with it directly - m4a mixes rate/60 samples per channel per frame.
Measured, same room and walk, one build each:

| mixer rate | instr/frame | vs vanilla |
|---|---|---|
| 15,768 Hz (vanilla) | 74,792 | — |
| 13,379 Hz | 71,160 | −4.9% |
| 10,512 Hz | 66,101 | −11.6% |
| 7,884 Hz | 61,291 | **−18.1%** |

It stacks with the channel and reverb trims from the previous round,
because they scale different parts of the same loop.

**3. Two audio builds, and the numbers for both.** North Hyrule Field and
South Hyrule Field, walking, against the ROM from before any of this work:

| build | NHF instr/frame | NHF worst | SHF instr/frame |
|---|---|---|---|
| before this work | 81,240 | 138,056 | 65,083 |
| default now | 64,205 (−21%) | 85,200 | 55,054 (−15%) |
| `quickstart-audiolight` | 52,936 (−35%) | 65,800 | 48,528 (−25%) |
| `quickstart-audiomin` | 42,224 (**−48%**) | 51,632 | 44,246 (−32%) |

`audiolight` is 4 channels, no reverb, 13,379Hz; `audiomin` is the same at
7,884Hz. At audiomin the worst North Hyrule Field frame is about 155,000
cycles of a 280,896-cycle budget - roughly half - where before this work the
worst frame did not fit at all. Both are audible trades and neither is the
default.

**A build-system trap worth knowing.** Neither `game.o` nor `m4a.o` depends
on the flags that select a variant, so `make` will happily reuse an object
built with different ones - which is how a "vanilla audio" measurement came
back showing the mixer at half cost (it still had the 7,884Hz `m4a.o` in
the build tree). Every quickstart target now deletes both objects before
building, so the variants cannot cross-contaminate.

**What is left, in order of size.** For a North Hyrule Field frame as it
now stands:

| | share | cuttable? |
|---|---|---|
| m4a mixer (IWRAM) | 40% | only by the audio knobs above - it is vanilla's |
| `src/movement.o` | 6.4% | no - entity movement |
| `src/game.o` | 6.6% | some; the remaining hot spots are flag reads |
| `src/playerUtils.o` | 4.5% | no - the player |
| `src/entity.o` | 3.7% | no - list housekeeping |
| `src/ui.o` | 3.4% | only by dropping HUD elements the player sees |
| engine IWRAM + IRQ | 3.1% | no |
| `GravityUpdate` (asm) | 3.0% | per entity per frame - scales with enemy count |
| m4a ROM half | 2.6% | with the audio knobs |
| enemy AI (`asm/src/enemy.o` + per-enemy) | ~4% | scales with enemy count |

Two honest observations from that table. **Enemy count is still the second
lever after audio** - gravity, movement, collision and AI are all per-entity
per-frame, and the room ceiling is 28. And the NPC script VM (~1.5%) scales
with the number of fuser sprites in a room, which cross-region hosting can
now push to nine; capping that lower would be a small, cheap win if it is
ever wanted.

### Mapping the world: a requirements model for every square (Aug 2026)

The design question behind win-condition chains, in the user's words: "we
need a way of mapping out the vanilla world and all the requirements needed
to reach every square of the game, and we need to do it robustly." What
follows is the plan, the measurement that says it is tractable, and what
already exists.

**Walkthroughs are the wrong source.** A 100% walkthrough describes
vanilla's intended ORDER - get the Flippers, then go to Lake Hylia - which
is one valid route, not the set of constraints. It cannot tell you what is
reachable without an item, it says nothing about the rooms this mode has
re-wired, and it cannot be checked. The ROM has strictly better data: it is
exact, offline, and already half-parsed by the tools here.

**The measurement that makes it tractable.** The scaling worry is "every
square" - tens of thousands of them. But a requirement is a property of the
KIND of square, not the square. Measured this round (`tileclass.py`): the
fifteen region rooms hold about 24,000 tiles and **397 distinct
(collisionData, tileType, actTile) classes** between them, of which 68 are
plain floor and 329 are everything else. That is a 60:1 reduction, and it
gets better, not worse, with more rooms - a new room in a tileset already
surveyed adds almost no new classes. **The measurement burden is a few
hundred things once, not tens of thousands of things ever.**

**Three layers.**

1. **The room graph.** Nodes are rooms, edges are exits. Already built:
   `exit_lists.py` parses every room's exit list out of transitions.c as
   the BUILD sees it, resolving the QUICKSTART #ifdefs so it reports the
   doors that exist in the ROM we ship rather than vanilla's.
2. **Intra-room reachability.** For one room: a flood over the collision
   grid where passability is a function of (tile class, items held) rather
   than a fixed test. Output: which of the room's exits reach which, and at
   what cost. This is the piece that does not exist yet.
3. **The world graph.** Compose the two. A node is (room, entrance); an
   edge is (room, entranceA) -> (room, exitB) carrying layer 2's
   requirement, then (room, exitB) -> (destRoom, arrival) free from layer 1.

**Where requirements come from, in order of trust.**

- **Tile class** (the bulk): the table above, filled once per class.
- **Objects**: locked doors, bombable walls, cracked floors, dig spots.
  These are entities, not tiles, so they come from the room's object list,
  and each object type maps to a requirement.
- **Fusions**: `gKinstoneWorldEvents` -> `gWorldEvents` already gives which
  fusion changes which room at which coordinates - `find_fuser_spots.py`
  reads it today.

**How the class table gets filled: differential measurement, not
judgement.** For each class, one experiment: stand the player next to a
tile of that class holding item set S, walk into it, and see whether they
end up standing on it. Every piece of that already works - granting items
by writing `gSave.inventory` directly was proven this month on the swamp-kit
drop gate, and the flood and warp helpers are the checker's own. The answer
is a property of the class, so one measurement transfers to every tile of
that class in the game.

**The verification loop is the "robustly" part.** The model is trusted only
where the emulator agrees with it. For a sample of (room, entrance, exit,
item set) the harness walks it and confirms; a disagreement means a class
is misclassified, and the tile that disagreed names which one. That is the
same discipline the invariant checker already applies to sites and fusers,
pointed at reachability.

**Then chains are winnable BY CONSTRUCTION, not by checking.** This is the
important design point, and it is what answers "makes sure the player can
win every time". Do not generate a chain and then verify it - generate it
forward, in spheres:

- Sphere 0 is everything reachable with the starting kit.
- The chain's first step is placed somewhere in sphere 0. Its reward joins
  the item set.
- Sphere 1 is everything reachable with that larger set. The second step
  goes there. Repeat.

A chain built this way cannot be unwinnable, because no step was ever
placed anywhere the player could not already stand. This is the standard
randomizer guarantee (assumed fill / sphere logic) and it removes the need
for a solver that can fail.

**Meta-events fall out for free.** "Do fusion X, in region Y, which needs
item Z" is one goal node whose requirement is the AND of the fusion's own
requirement and the region's reachability. The DNF algebra for that already
exists in `overworld_paths.py` - alternative terms, AND multiplies out, OR
unions, and minimize() drops any term another term is a subset of, so a
route's bill stays the shortest sets that actually work.

**A worked example, measured this round.** `ROOM_DIG_CAVES_TRILBY_HIGHLANDS`
is 30x60 and holds SEVEN walkable components. The entrance lands in a
27-tile corridor; the main body is 1,170 tiles (1,036 with full 3x3
clearance). A pure collision flood says the body is unreachable from the
door. It is not - it is behind the MOLE MITTS, and the diggable wall
between them is a tile class the flood does not know about. One room
contains the whole problem and the whole solution.

**Staging.**

1. ~~The class census.~~ Done - 397 classes, `tileclass.py`.
2. The class -> requirement table, by differential measurement. Start with
   the ~30 classes that cover most of the map's area.
3. `reach.py`: the permission flood, per room, per item set, emitting
   exit-to-exit DNFs.
4. The object layer (bombable, locked, dig, fusion-revealed).
5. The world graph and the sphere filler.
6. Port the finished graph into game.c as static data. The game needs the
   answer, not the tooling.

**What the harness can measure today**: the room graph, collision grids,
tile classes, component structure, arbitrary item grants, and whether a
given spot is reachable from a given entrance. **What needs building**: the
class-to-requirement table and the permission flood. Everything in stage 3
onward is composition of things that already work.

### The site block has hit its ceiling (Aug 2026)

Adding the 73rd content site needed thirteen more flag bits and there were
almost none left. An audit (the invariant checker's own macro expansion,
reused as a free-space report) says the QUICKSTART window is **689 of its
704 offsets full**, and the only free runs left anywhere that a run-start
wipe actually clears are window 94-100 (7 bits) and bank-11 133-141 (9).
The 73rd site is built out of exactly those two scraps.

A first attempt widened extension run B into window 509-521 instead, and
the flag tier rejected it within one run - `GF_REGION_ALIVE_BIT` is already
there. Worth recording as a win for the checker: a silent overlap there
would have corrupted region state in a way that would have been very hard
to trace back.

**There is no 74th site.** Before the table grows again the site block wants
a real storage redesign - a packed array in gSave (13 bits x N read and
written as bytes) rather than one engine flag per bit. That would also cut
the flag-read cost the profiler keeps finding, since a byte read replaces
thirteen routed bit reads.

### The first reachability survey, encoded and cross-checked (Aug 2026)

The user walked the mapexplore build and produced a per-region reachability
survey: for each region, one start point, and what it costs to reach every
door, cave mouth, pocket and sub-area from there. It is now
`tools/quickstart/world_reach.py` - **13 regions, 129 destinations** - and
`--check` runs it against the ROM's exit table and against the port model in
`overworld_paths.py`.

**Requirements stopped being only items, and that is the important part.**
Half of what gates this world is world STATE: a fusion that lays a bridge, a
boulder pushed into a hole, a maze solved, four switches thrown. Those are
tokens in the same vocabulary as items now, because the algebra does not
care - "holds the Flippers" and "boulder 1 is in its hole" are both just
facts that must hold. That is what will let the sphere filler treat *do this
fusion* as a placeable chain step rather than a special case.

**What the cross-check found.**

1. **69 of the 129 coordinates are unusable, and it is the overlay's
   fault.** Local coordinates are world position minus
   `gRoomControls.origin`, and for several frames around a transition the
   position is already the new room's while the origin still belongs to the
   old one - which comes out as a large negative or a number in the tens of
   thousands. Every reading taken while walking through a door landed in
   that window. The room NAMES are all good, so no requirement is lost; only
   the pixel coordinates need re-taking. **Fixed**: the overlay now computes
   a `settled` test (local inside the room rect), holds the room-change
   stamp until it passes, and prints `** MID-TRANSITION **` rather than a
   number that means nothing.
2. ~~**A real conflict: the block-pushing skill is priced two ways.** The
   survey says *level-2 sword + spin* for the pushable blocks in Lon Lon
   Ranch and Trilby Highlands, and *level-3 sword + spin* for the Royal
   Valley crypt and the North Hyrule Field graveyard pocket.~~ RESOLVED, and
   neither reading was wrong: vanilla charges one clone per step up in block
   size, and clone count is sword level, so the survey was seeing two block
   sizes rather than two obstacles. The mode moves the whole mechanic onto
   the Power Bracelets - see "The Power Bracelets move every block now".
3. **Royal Valley's lantern gate is stated differently by the two tables.**
   `overworld_paths.GATES` gates the whole region on the Lantern; the survey
   has no region requirement and instead puts the Lantern on the individual
   destinations past the maze. The survey looks more accurate - you can
   stand in Royal Valley's entrance without a Lantern - so the GATES row
   probably wants to become a per-destination cost.
4. Two room names the survey uses are not in transitions.c:
   `ROYAL_VALLEY/CRYPT` and `CASTOR_WILDS_DIG_CAVE/0`. Both are probably
   real places under other names.
5. 27 destinations are not direct exits of their start room - expected, and
   worth keeping: they are the two-doors-deep entries, which is exactly the
   composition the world graph is for.

**The survey is an upper bound, not a proof.** The user's own caveat, worth
repeating because it shapes how the filler must use this: a survey walked
from ONE start point only finds the routes that start there. North Hyrule
Field and Castor Wilds both have several ways into the same pocket, and
dropping the player somewhere else opens routes this table does not know
about. Every requirement here is the cost from that start - never evidence
that no cheaper way exists.

### Content the survey says we should gate (Aug 2026)

Places where the mode currently spawns content without checking whether the
player can be there, or where vanilla has a mechanism worth taking over:

* ~~**Lon Lon Ranch's tornado pocket** (396,253) needs the Minish Cap and
  the Pacci Cane; **the Tingle pocket** (184,298) needs the block push.~~
  SHIPPED - both are zone rows now, measured exactly; see below.
* ~~**Castor Wilds' `MINISH_PATHS/BOW`** is a long water hallway crossed
  with the Flippers or the Gust Jar - only aquatic or flying enemies belong
  in it.~~ SHIPPED - substituted at the placer; see below.
* ~~**`HOUSE_INTERIORS_4/RANCH_HOUSE_WEST`** is reachable as Minish *only
  if the room keeps its vanilla content* - our sweep must not clear it.~~
  SHIPPED - off the obstacle-sweep list; see below.
* **Wind Ruins has two vanilla kill-the-enemies gates** (the two-chest
  pocket below the fortress entrance, and the fortress approach). Both are
  ready-made ? events - the gate mechanism is already there and already
  keyed to clearing a room.
* **Two pockets are unreachable from their own room**: Lon Lon Ranch's
  fusion-chest pocket (only from Veil Falls) and Trilby's north pocket (only
  from Royal Valley). Neither should ever be picked as a content site for a
  run that cannot enter from the far side.

### The survey's gates, enforced (Aug 2026)

Four of the items above are now code, plus the Royal Valley correction the
survey forced.

**Royal Valley is not Lantern-gated as a region.** The route model priced
the whole area at a Lantern because the room is dark, and the pool row said
so in a comment. The walked survey disagrees: you can stand in the entrance
and walk the E->S crossing with no Lantern at all. What the Lantern actually
gates is the Lost Woods maze and everything past it - the graveyard, Dampe's
house, the upper pocket - none of which is a *port*, so none of it belonged
in a port-level gate. `GATES['RV']` is retired (with the reasoning left in
place of the row) and the cost moved to where it is true: the north
component's zone row now asks for the Graveyard Key **and** the Lantern.
The maze-solved fact is not an inventory item and cannot be asked for at
placement time, but the Lantern is the gate *on* the maze, so requiring it
covers the same ground.

**Zone rows can now express an AND.** `QuickStartPositionAllowed` answers on
the first row containing the point, so two overlapping rows cannot mean
"both" - the second is never consulted. The gated-zone struct grew a
trailing `alsoItem`, making the whole requirement
`(requiredItem OR altItem) AND alsoItem`. Lon Lon's Tingle pocket is what
needed it (level-two sword *and* Spin Attack for the block push, at the
time - that row is a single item now that the Power Bracelets own the block
gate); Royal Valley's graveyard still uses it.

**Lon Lon Ranch's two pockets are measured, not estimated.** Flooding the
room's collision: the tornado pocket is a 46-tile component (tx 22-38 /
ty 13-21 = px x 352-623, y 208-351), the Tingle pocket 23 tiles (tx 10-14 /
ty 16-23 = px x 160-239, y 256-383). **Zero** tiles of the 460-tile main
body fall inside either box, so the rectangles are exact rather than
approximate - a rare luxury for a zone row.

One honest limitation on the tornado row: it gates on the Pacci Cane only.
There is no `ITEM_MINISH_*` at all - being Minish is a *state* - and even if
there were, this filter runs when the room's content is placed, with the
player at the door at full size, so a "are you Minish right now" test would
answer about the wrong moment. A run holding the cane with no route to a
portal can still have content placed there. That is a much smaller hole than
the one it closes; if it turns out to matter in play, the fix is
`requiredItem 0` ("never"), not a cleverer test.

**`MINISH_PATHS/BOW` only accepts things that fly.** A walking enemy dealt
into that water hallway is either standing on liquid or stuck on the thin
bank - and for a wave room, a gauntlet that cannot be cleared. The
substitution happens at the *placer*
(`QuickStartSpawnEnemiesOnOpenTiles`), not at the roster draw, so every path
that puts a body in a room goes through it - waves, minibosses, quest packs,
the pot room's own filler - while the roster stays untouched everywhere
else. Already-airborne kinds pass through unchanged; anything else is
re-rolled into KEESE / SMALL_PESTO / PEAHAT / PESTO / GHINI / WISP. CROW is
left out for the same reason waves never draw it, TAKKURI because a thief
over water can carry a stolen shield somewhere unreachable, and LAKITU
because its roster row needs the Pacci Cane.

**`RANCH_HOUSE_WEST` keeps its furniture.** It was on the obstacle-sweep
list, and OBJECT-kind is exactly what its second, Minish-sized entrance is
made of - so clearing the clutter deleted the entrance with it. It comes off
the list; `RANCH_HOUSE_EAST` stays, because its second way in is a separate
minish door rather than furniture in the room. Keeping the objects costs a
little floor space. Clearing them cost a route, and a route is the scarcer
thing.

### The GFX-budget tier measures something the reserve does not promise

Worth writing down, because this batch tripped it and it is not a bug in
this batch.

`QuickStartEnforceGfxReserve` stops trimming when **reclaimable** slots
reach the reserve. The checker's gfx tier counts **strict-free** slots
(state nibble not in 0/1/2) and fails under 2. Those are different
quantities, so the reserve can be perfectly satisfied while the tier reads
zero.

Measured across seeds, both before and after this batch: North Hyrule Field
at difficulty 4 reads 0 free on seed `0x11111111` on **both** ROMs,
identically, and passes on `0x22222222` and `0x33333333`. Lon Lon Ranch
read 0 on the derived default seed after this batch and 4 before it - but
5, 5, 7 before and 12, 11, 13 after on the three pinned seeds, i.e. *better*
on every seed that was checked both ways. Filtering spots changes how many
`Random()` calls the shuffle makes, which shifts the whole downstream
stream; the room lands on a different set of sheets, and sometimes that set
is unluckier.

So: a single-seed gfx failure is a seed report, not a regression. Diagnose
it by running the tier on the same seed against the previous ROM before
believing it. The underlying weakness - the reserve not defending the
metric the tier measures - is real and still open.

**Confirmed again, Sep 2026, by the Minish Woods / Lake Hylia batch**, and
this time the comparison was run rather than reasoned about. Lon Lon Ranch
failed at 0 free on the derived seed after that batch, so the previous ROM
(`e3da734`) was rebuilt and pointed at the same tier on the same seed: it
reads **0 free too, identically**. Not a regression. The rest of the
comparison went the other way - the old ROM had four gfx failures on that
seed and the new one has one, with North Hyrule Field going from 1 free to
5 - and on pinned seed `0x11111111` Lon Lon passes outright while North
Hyrule Field reproduces its own long-standing 1-free reading. Rebuilding
the previous ROM costs two `make` runs and settles the question in one
measurement; do that rather than sweeping more seeds.

### The Power Bracelets move every block now (Aug 2026)

The survey turned up the same "push a block" obstacle priced two different
ways - a level-two sword in Lon Lon and Trilby, a level-three sword in Royal
Valley and the North Hyrule Field graveyard pocket - and the answer turned
out to be that **both readings were right about vanilla**, which is why the
model had to change rather than the map.

**How vanilla actually works.** The block's size comes back from
`sub_0801A570` in the top nibble of the tile position. In
`UpdatePlayerCollision`'s `ACT_TILE_114` case that becomes `tmp2`, which is
simultaneously the `PUSHED_BLOCK` type (2x2 -> 1, 3x3 -> 2, 4x4 -> 3) and the
number of **extra pushers** demanded: one clone per step up in size. The only
way to get clones is the duplication technique - charge the Spin Attack,
stand on a glowing clone tile, split into as many Links as the equipped sword
allows (`SurfaceAction_CloneTile`: Smith's and Green none, Red one, Blue two,
Four Sword three). So a bigger block is literally a bigger sword, and the
survey was reading two block sizes, not two obstacles.

**Why that could not stay.** It priced overworld pockets in whatever sword a
run happened to draw - a fact about its luck, not a choice it made - and it
needs a scroll AND a sword AND a glowing tile within reach of the block,
which not every one of these blocks has.

**What replaces it.** The Power Bracelets are now the whole gate: hold them
and any size of block moves, with no clones at all. One item, the same one at
every block on the map. The change is three lines around the clone count, and
it **skips** the count rather than faking clones - nothing downstream reads
`gPlayerClones` (the `PUSHED_BLOCK` object moves itself and repaints the
tiles under it; the player just plays the push animation), so a spoofed clone
would be a sprite to feed and delete for no gain. Skipping also drops the
read through `gPlayerClones[0]`, which is a NULL dereference any time a
cloneless Link leans on one of these - harmless on hardware, since address
0x6c is BIOS, but not worth keeping.

**Measured, both directions**, on four real blocks (scratchpad
`block_probe.py`, which finds each block as a connected component of act tile
114 and shoves the player against the middle of all four edges):

| room | block | with bracelets | without |
|---|---|---|---|
| `CAVES/LON_LON_RANCH` | 2x2 | moves | does not move |
| `CAVES/TRILBY_HIGHLANDS` | 2x2 | moves | does not move |
| `CAVES/TO_GRAVEYARD` | 3x3 | moves | does not move |
| `ROYAL_VALLEY_GRAVES/HEART_PIECE` | 3x3 | moves | does not move |

The 3x3 rows are the ones that matter: that is the size vanilla charges two
clones for, so the bypass is not just working at the cheapest block. Each one
moves from a single side because the others are walled in - that is the map,
not the mechanic.

**Fallout.** `world_reach.py` and `overworld_paths.py` both retire their
sword/spin tokens for a single `BRACELETS`; the Lon Lon Tingle-pocket zone
row in `game.c` drops its sword+spin AND for one item; the conflict check
that reported the sword2-vs-sword3 disagreement is now a regression guard
that fires if a sword level is ever used as a block price again; and the NHF
WNW cross-check, which used to print every run because the two models were
written in different currencies, now compares them directly and stays quiet
when they agree. `world_reach.py --check` reports **zero** conflicts.

One knock-on worth noting: `beanstalkSubtask.c` joins `VARIANT_OBJS`. It is
the file that owns `UpdatePlayerCollision`, so it now compiles differently
per variant, and the stale-object trap that has bitten this project three
times applies to it like any other.

**And a fourth version of that same trap, caught here.** Every variant target
builds the same file - `tmc.gba` - because GBA.mk's ROM name comes from
`GAME_VERSION` and nothing else. The per-variant names (`tmc-testkit.gba`,
`tmc-d3.gba`, ...) were copies made by hand *after* the build, which means a
round of "build all six" left five of them untouched and shipped whatever was
last copied into them. That happened; the previous batch's five non-default
ROMs were stale. Each target now ends with its own `cp`, so the copy is part
of building rather than something to remember, and `ls -la tmc*.gba` shows six
distinct timestamps and six distinct md5s when the set is genuinely fresh.

### The win is a five-step chain now (Aug 2026)

The Earth Element used to be one condition away: clear a wave, or beat a
boss, or finish the pot quest, in one rolled region. It is five now, and the
fifth is that carrier - so the old machinery is the last link rather than
the whole chain.

**Rolled one at a time, and that is the entire design.** Step n+1 does not
exist until step n is finished. Its roll is made against the loadout the
player is holding at that moment, so it can be placed inside the sphere they
have actually opened. This is the spheres idea run forwards: sphere 0 is what
the starting kit reaches; a step placed inside the current sphere is
reachable by construction; finishing it pays a key item, which grows the
sphere; the next step goes inside the grown one. Nothing has to be proved
winnable afterwards, because at no point was anything placed anywhere the
player could not already stand. Rolling all five up front cannot give that -
it would have to guess which items the run will find, and a wrong guess is a
run that cannot be finished.

**The five kinds**, each of them something the mode was already able to
observe, which is the constraint that shaped the list — a step whose
completion cannot be detected is a dead run:

| kind | the task | how it is seen |
|---|---|---|
| `ITEM` | be holding a particular item | `GetInventoryValue` |
| `EVENT` | finish the ? room event at one content site | `GF_CONTENT_SITE_DONE` |
| `WAVE` | clear waves in one region until its counter hits a target | the per-region wave counter |
| `BOSS` | put a boss down in one region | a watcher modelled on the carrier's |
| `QUEST` | finish the run's side quest | `GF_QUEST_DONE` |

A kinstone-gated ? room is an `EVENT` like any other, not a kind of its own -
which is what was asked for. The gate is respected at ROLL time instead: a
gated site is only offered once its fusion is already done, because a site
whose wall has not been punched open is a place the player cannot stand.

`ITEM` is the guaranteed floor and the reason the chain can never wedge:
"be holding X" needs no reachable room at all, only that the economy can
still hand X over, and the economy runs wherever the player already is.

**Where reachability comes from.** `tools/quickstart/gen_reach.py` compiles
the walked survey into `include/quickstart/reach.h` - 128 destination rows
and a per-region entry price, each a DNF of token bitmasks. The game builds
a "held" mask from the inventory plus the run's fusion count, floods the ring
adjacency from the drop region admitting a neighbour only when its entry
price is paid, and then asks whether the candidate's own row is satisfied.

Two things about that table are deliberate and worth keeping deliberate.
Tokens with no run-time test - being Minish, the maze solved, four switches
thrown, a boulder in its hole - are emitted but **never set** in the held
mask, so any route needing one is permanently invisible to the placer. And
the flood starts from `QuickStartDropRegionIndexUsable`, not the raw rolled
drop: a raw roll can land on Castor Wilds or the Wind Ruins, which a run
without boots or cape cannot be inside at all. Reading the raw bits instead
put four of six probe seeds' first step inside the Wind Ruins - correctly,
for a drop that was never going to happen.

**Telling the player, without telling them everything.** Ezlo names the
REGION and nothing else (`gCustomStrings` 241-250, one per named region) - a
region rather than a room because 842 rooms do not fit in a 256-slot string
table, and because "somewhere in Trilby Highlands" is a hint while a room
name is an instruction. The COMPASS changes both surfaces at once: Ezlo's
line becomes one that says what the task IS (251-255, one per kind), and the
map screen gains a second marker, exact to the room. So a compass holder gets
the what and the where; everyone else gets a region and their own legs.

That fills `gCustomStrings` to 256 of 256. There is no 257th - text.c
indexes it with a u8 - so the next line that needs a slot needs a second
text category (`TEXT_CUSTOM` is 0xfe; 0xff is unused), and there is now a
compile-time guard that says so instead of silently aliasing string 0.

**State** lives in `gSave.chain_*` (save.h), in filler the mode had not
claimed - the flag banks are full. `chain_rolled` counts steps dealt,
`chain_progress` steps finished, `chain_hinted` carries one hint bit per step
plus the current step's own observation latch. All of it is zeroed per run:
a stale `chain_rolled` would make the monitor think step 0 was dealt already
and go hunting a target chosen against last run's loadout, in last run's
ring, from last run's drop point.

**Measured, on the ROM, both directions** (`tools/quickstart/chain_probe.py`,
which recomputes reachability in Python from the same survey and complains if
the game disagrees):

* six seeds, every step the game dealt was independently confirmed reachable
  — **0 problems**;
* two seeds ran all four pre-steps to completion with the rewards landing and
  the next step rolling each time;
* a `BOSS` step advances on the kill and not before (progress 0 → 1 across a
  boss family that was alive for 180 frames first);
* the Earth Element **did not appear** in the element region on 3/3 seeds
  while the pre-steps were unfinished, and appeared once they were forced
  done on the two seeds whose carrier the crude test could satisfy (the
  third's carrier is QUEST, which the test never completes);
* Ezlo's hint fires on 6/6 seeds, and names the right thing: string 243
  (South Hyrule Field) for a boss step in South Hyrule Field, 246 (Trilby)
  for an event in Percy's treehouse - and with the compass held the same
  seeds instead get 254 (boss) and 252 (event).

`gen_reach.py --check` is now part of the invariant checker's static tier, so
editing the survey without regenerating the header fails loudly rather than
leaving the game placing steps by yesterday's map.

**What is not wired.** The `ITEM` step is satisfiable from the normal economy
and nothing bounds how long that takes - the mode hands out key items
constantly, but a specific one is a draw, not a promise. Biasing the reward
draw toward the wanted item while an `ITEM` step is live is the obvious next
move and it is one hook (`QuickStartDrawItem`) away.

### Mt Crenel, and the site block's ceiling coming down (Aug 2026)

Adding the mountain meant removing a wall first: the content-site table was
exactly full at 73, and the comment on it said so - "the next site after this
cannot be added by finding more bits, because there are not any."

**The redesign turned out to be a deletion.** A site stored thirteen bits: a
"randomized" latch, a 3-bit KIND and an 8-bit EXTRA (the kind's parameter),
plus DONE. Twelve of those thirteen were recording a dice roll - rolled once
with `Random()` on first entry and kept so the room would look the same on
the way back. But the run already has a seed that never changes and the site
already has an index, so the same answer can be **computed** from those two
whenever it is asked for. `QuickStartContentSiteRoll` borrows vanilla's whole
RNG state (`gRand`, one word), seeds it from an avalanche of
`(run_seed, site)`, runs the *unchanged* roll, and puts the state back. Six
lines, and every kind picker stayed untouched - the alternative was rewriting
five of them to take an RNG argument.

What is left is DONE, one bit, at raw offset `ORIGIN + site`. The ceiling
moved from **73 sites to 793**, the extension router and its six borrowed
scrap runs are gone, and bank 11 is untangled - the extension's own comment
claimed 121-141 was free while the inn chests had been sitting at 121-123 the
whole time.

**Mt Crenel is 30 surveyed destinations and 11 new ? rooms.** The survey is
in `world_reach.py` as region `CREN`, and it needed a caveat none of the
others did, in the user's own words: *"there are a lot of one-way gates going
from this starting point to this exit; going the other way, the requirements
list might look different."* Every other region was walked from where the
player arrives. Crenel was walked **downhill** from a waypoint inside the
mountain, while a player from Trilby arrives at the bottom and climbs **up**,
so the rows are the cost of the reverse of the player's route and the uphill
price is simply not in the data.

Two consequences, both erring toward offering the placer less:

* the **region** is priced at grip + bombs. Not because the survey says so -
  it says nothing about getting in - but because those are the two most
  expensive things it shows anywhere between the mountain's entrance and the
  rest of it. Pricing the way in at the worst thing on the way out is the
  conservative reading; if the real climb is cheaper the cost is variety, not
  a stranded run.
* the one-way **cane gate** is deliberately NOT priced into the rows below
  it. The lower half has its own way out of the mountain entirely
  (`MT_CRENEL/ENTRANCE`), so a player who drops through without the cane is
  not stranded - they just cannot climb back up. What a run cannot do is
  bounce between the halves.

`QS_REGION_CREN` joins the ring as a spur off Trilby's west border. It is a
ring member but **not** a pool row: nothing drops the player there and no
region wave loop runs in it, so Crenel hosts EVENT steps and nothing else.

**Every spot is measured, not chosen.** `tools/quickstart/crenel_spots.py`
warps in at the survey's own coordinate, floods the collision from where the
player lands, and returns the tile nearest that component's centre of mass
among those with eight-way clearance and at least four tiles between them and
the arrival - four because the spawner's door keep-clear is two, and four for
a ball-and-chain. That measurement is also why **five** rooms the survey
names are not sites: Crenel's pillar cave and dig cave are 5 and 9 tiles of
standing room, and Mt Crenel's Top, Wall Climb and Cavern of Flames approach
are ledge mazes with no 3x3-clear tile in the arrival component at all. An
event with no room to happen in is worse than no event.

**Measured, on the ROM.** With the grip ring and bombs in hand, Mt Crenel
joins the sphere on 8/8 probe seeds and the chain placed **six** steps inside
it across those seeds - every one independently confirmed reachable by
`chain_probe.py`, which recomputes the sphere in Python from the same survey.
Without those two items Crenel never appears, which is the same check run
from the other side.

That verification also caught a drift the moment it was introduced: the
probe's hand-copied region adjacency had never heard of Crenel, so it called
six correct placements unreachable. It now asserts its region set against the
generator's and that the adjacency is symmetric, so a missing region is loud
rather than a wrong verdict.

**A second text bank.** `gCustomStrings` hit its hard 256-entry ceiling with
the win chain's hint banks, and Crenel needs an eleventh region line.
`TEXT_CUSTOM2` (0xff, the last free category) adds a second 256-entry table;
the hint banks moved into it, freeing 241-255 in the first. New strings go in
bank two from now on.

**The test kit carries the Four Sword now**, plus the grip ring, the power
bracelets, the spin attack and the lantern (and keeps its bombs, because
Crenel's entry price is grip AND bombs). The Four Sword was refused for a
long time and for a real reason: holding it makes `sub_080AF284` replace
Castle Garden's ENTIRE exit list with its late-game version, which would take
the mode's own pool doors with it. Both of vanilla's Four-Sword exit swaps are
suppressed under QUICKSTART now, which costs nothing - the layouts they point
at are content this mode never reaches - and that is what makes the top of
the sword ladder safe to hand out.

### Minish Woods and Lake Hylia, and the pool index that ran out of bits (Sep 2026)

The user: *"begin incorporating the Minish Woods and Lake Hylia as part of
our overworld regions included. Please fully convert these rooms and bring
them into the main game mechanics."* Two new pool regions, taking the pool
from fifteen rows to seventeen - and seventeen is where a lot of quiet
arithmetic stopped working.

**Seventeen rows do not fit in four bits.** Five separate fields in `game.c`
store a POOL INDEX: which region hides the Earth Element, which hosts the pot
quest, which hosts the scavenger hunt's giver, which hosts its target, and
which one the hub's pit drops the player into. Every one of them was four
bits wide, which encodes 0-15 and was correct right up to the sixteenth row.
Row 16 (Lake Hylia) would have wrapped every one of them silently to 0 -
Castle Garden - so a run that drew the lake would have found the Element in
the garden and never known why. The four-bit bases stay where they are and
each grew a fifth bit in the 208-212 run (`GF_POOL_HI_*`), read and written
only through `QuickStartReadPoolIdx` / `QuickStartWritePoolIdx` so the two
halves cannot drift apart. A compile-time check now caps the pool at 32 rows.

**Seventeen rows also exposed a live flag collision.** Pool rows past the
twelfth keep their wave/alive/reward state in `QuickStartExtSlotFlag`, which
was laid into three runs of `FLAG_BANK_11` its own comment described as free.
They were not. An audit of every bank-11 allocation found **seventeen**
colliding offsets: Castor Wilds' alive counter shared 60-71 with the
stripped-kit handicap's area/room snapshot, its top alive bits shared 121-122
with the inn's chest-armed flags, and the Wind Ruins' wave counter shared
131-132 with the Western Wood brush payouts. Paying for a bed really did move
a region's enemy count, and taking the handicap really did scribble on Castor
Wilds. The whole block moves into four free runs of the QUICKSTART window
(617-655, 658-689, 496-508, 213-228), all inside the 202-703 run wipe, so an
extension slot resets per run with no clear loop of its own.

**The reason it was invisible is that it was a function.** The invariant
checker's flag tier parses every `#define GF_*` out of `game.c`, expands it
over its declared range and asserts no bit is claimed twice - and
`QuickStartExtSlotFlag` is a function, so it was never in the ledger at all.
The tier now re-derives the function's run table from its own source and
registers it as an ordinary block, under the same collision, bank-bounds and
run-wipe checks as everything else. If the function is rewritten into a shape
the parse cannot follow, that is a FAIL rather than a silent skip.

**Both regions were DERIVED, not walked, and the tables say so.** Every other
region in `world_reach.py` is the user walking the mapexplore build. These two
are the rooms' own vanilla exit lists (exact coordinates, exact room names)
plus a collision flood run from the tile the player really arrives on -
`tools/quickstart/door_reach.py`, new this pass. A flood sees geometry, not
gates: it can prove a door is walkable with nothing at all, but it cannot tell
a wall from a wall with a bomb crack in it. So the rows split. Doors the flood
reaches are recorded FREE, which is a fact about the room. Doors it does not
reach carry a new token, `UNSURVEYED` - untestable at run time exactly like
`MINISH` or `MAZE`, so the chain placer can never satisfy it and those places
are invisible rather than wrongly offered. Replace the blocks when a walked
survey exists; until then the two regions are honest about being thin.

**They are spurs, not a loop.** Both rooms have a border into the other -
Minish Woods' north edge into the lake, the lake's south edge back - and the
first draft of the region adjacency wrote that edge in and called the pair the
overworld's first closed circuit. The flood says otherwise, and the flood
wins: Minish Woods' arrival component is **277 of its 1195 open tiles** and
touches the west edge and nothing else; Lake Hylia's is **165 of 662** and
likewise only the west. Each room's other thirty-odd components are tree
hollows, Minish cracks and, in the lake's case, the far shore. So the walkable
graph is EH <-> MW and LLR <-> LH, two dead ends, and the MW-LH edge stays out
of `sQuickStartRegionAdjacency` because writing it in would tell the chain's
flood a kitless player can walk a circuit they cannot.

**Lake Hylia generalised the swamp gate.** Castor Wilds and the Wind Ruins had
a two-region special case: dropped in without the Pegasus Boots or Roc's Cape,
the player can neither explore nor leave. The lake is the same shape of
problem in a different liquid - 165 tiles of shore around water only the
Flippers cross - so the special case became a small table
(`sQuickStartRegionKitRules`) of ring, item, alternative item. A drop into a
row whose kit the player does not hold is re-drawn, latched, exactly as
before.

Everything else is the ordinary pool-row work, all of it measured in the
running game: 22 and 16 enemy offsets, entrances at the real border arrival
points, rewards flood-verified in the same component, nine fuser spots each
(farthest-point sampled with entrance and reward seeded as taken - the
spacing relaxes to 80px in the woods and 48 on the shore, because a cul-de-sac
shore strip has no room for six-tile spacing), two Ezlo region hint lines
inserted at the `QS_REGION_MW` / `QS_REGION_LH` positions, and **nine new ? rooms**
in the pockets behind the two regions' doors.

Six of the fifteen doors are deliberately absent from the site table. Five
rooms - the business scrub and Great Fairy trees, the Waveblade tree, the
Minish Woods north crack and the Lake Woods cave - have no 3x3-clear tile
anywhere in their arrival component, and the Minish Woods bomb house has
twelve tiles with its only clear spot one tile from the door. An event with no
room to happen in is worse than no event, and one that spawns on the doorstep
is worse still. The nine that remain are there even though most sit behind
gates the game cannot test, for the same reason the Castor Wilds cave rows
are: the content sweep empties every room it enters, and a real vanilla door
that opens onto an emptied room is a bug whether or not the chain ever points
at it.

`chain_probe.py` reports 0 problems across six seeds, one of which (0x44444444)
drops into Minish Woods and completes all four pre-steps from there.

### The Earth Element was promised before the chain was run (Sep 2026)

The user: *"if the player enters the room where the earth element is located
Ezlo says 'The Earth element is here!' and the player can immediately get to
the earth element without having to go through the other quest events,
essentially making them completely optional."*

**The drop was already gated; the PROMISE was not.** Asked directly of the
shipped code in a running ROM - `QuickStartWinCarrierMet` called at chain
progress 0,1,2,3,4,5 - the answer is 0,0,0,0,0,0: the carrier refuses below
four completed steps and does not turn true at four either (it still wants
its own condition). Every way a step could be pre-satisfied is already shut,
and that was checked one at a time rather than assumed: ITEM steps only pick
items the player does NOT hold, EVENT steps skip sites already marked done,
WAVE steps store a TARGET of "this region's count plus one" so waves cleared
before the step was dealt do not count, and QUEST refuses a quest already
finished. The chain cannot cascade.

What leaked was `QuickStartShowRegionFinalHintOnce`, which fired on first
entry to the element region with no chain check at all and announced the
Element by name. That is the whole reported experience: being told the
Element is *here*, in the room it really is in, reads as "go get it", and
everything else on the list reads as optional busywork. The player was told
the truth about the place and a lie about the timing.

Two changes:

* **the hint waits for the chain.** Before the pre-steps are done, an early
  arrival gets a different line - it still names the place, which is fair
  and useful, but promises nothing. That one uses a per-VISIT room flag
  rather than a run-long one on purpose: someone who wanders back through
  mid-chain should be reminded, not left wondering what they missed.
* **the spawner refuses on its own account.** The gate lived only in the
  caller, and the caller asks `WinCarrierMet() || QsCheckRoomFlag(43)` -
  that second clause exists so the Element's despawn timer keeps being
  refreshed after the carrier's condition goes stale, and it is a way past
  the first. Nothing sets flag 43 early today (measured), but one gate in
  front of the run's whole objective is one too few, so
  `QuickStartSpawnWinKeyOnce` now checks the pre-steps itself. It is the
  only place the item is ever created, so it holds regardless of caller or
  flag.

`tools/quickstart/element_gate.py` is the regression test, four legs: the
carrier's answer across the whole progress range; the spawner called
directly at progress 0 **with flag 43 forced set** (0 elements); the spawner
at progress 4 (1 element - a gate that never opens is worse than one that
never closes); and a clean early visit to the element region (no Element in
the room, early line shown).

## 4. Vanilla behaviors not yet addressed

Vanilla machinery that still pokes through the mode, needing a decision
or a sweep.

- **Scripted vanilla populations can still appear outside Eastern
  Hills.** Story/kinstone flags a run sets can conjure vanilla NPCs at
  their scripted spots (the EH farm crew walling the stairs was this;
  those three rooms now sweep per-frame). The same class could surface in
  any other region room - Western Wood and SHF have story spawns too.
  Consider generalizing the EH sweep to every named region (it already
  spares our ZELDA-kind NPCs) rather than waiting for the next report.
- **Vanilla ground pickups survive in named regions.** Lon Lon Ranch still
  ships its NE heart piece and a red rupee from vanilla room data (found
  during the four-fix verification). Free loot outside the mode's reward
  economy - decide: sweep them, or accept them as flavor.
- **Lon Lon Ranch's Minish geography is half-wired.** The ranch house's
  two MINISH_SIZED_ENTRANCE doors lead into rooms that are already
  content sites (a second route in, harmless). But the central "long
  hallway" the player expects after shrinking has NO entrance object in
  the room data - where vanilla puts it is still unfound - and the old
  "check Lon Lon's extra link" note (#49) folds into this same survey.
- ~~Inactive Minish hole, NHF's east edge~~ **FIXED.** The second guess
  was the right one: a destination that was never containment-blessed.
  `MINISH_CRACKS_EAST_HYRULE_CASTLE` is a content site now. See #103.
- **The beanstalk fusions stay excluded** (KINSTONE_2E, KINSTONE_24).
  Their payoff is climbing out of the ring to cloud rooms containment
  cancels; a fusion that grows an unusable ladder reads as a bug. Only
  revisit if cloud rooms ever become content (a new pocket type).
- **The shadowed cellar renders dark** (a checker WARN since the first
  full run). Vanilla's lighting, our content. Decide: exempt it, light
  it, or retire the site (Decision 7).

## 5. Everything else

**Build targets.** `make quickstart` and `make quickstart-testkit` are the
two shipping ROMs. `make quickstart-d3` and `make quickstart-testkit-d3`
are the same two builds with `QUICKSTART_START_DIFFICULTY=3` - every run
starts at difficulty 3 instead of 0, for playtesting the middle of the
curve without having to win up to it. It is a FLOOR, not a pin: the
counter is still the mode's real meta-progression number, so a win moves
it on to 4 and a save that has already climbed past 3 keeps its progress.
Any value works (`make quickstart QUICKSTART_START_DIFFICULTY=7`); at the
default of 0 the knob compiles out entirely - verified by the shipping
ROM's md5 being byte-identical before and after the knob was added.


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
2. **Trilby's one-way ladder** - a run-ending trap, and the only bug on
   this list that costs the player their whole run rather than degrading.
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
7. **A collision flood cannot see a ledge.** It follows fully-open tiles,
   so it finds a room's components correctly and then lies about how they
   connect: the tile you hop from reads as ordinary floor, and the tiles
   you hop over read as solid wall. This produced two wrong "sealed
   pocket" calls in one session - Royal Valley's neck at tx 20 (collision
   0x29) and Trilby's Royal Valley arrival, which the user had to correct.
   `tools/quickstart/component_map.py` is the fix: it floods, then WALKS
   the player off every boundary tile of every component and reports where
   they land. Run on Trilby it found seven links between components,
   including two-way ones between the main body and the 85-tile southern
   component that no survey had recorded. Ledges are one-way by nature, so
   its map is directed.
8. **A probe that finds nothing has proven nothing until a control says
   otherwise.** Aug 2026, twice in one session: a walk probe reported
   twenty-two ring doors "dead" and a memory-forced Minish probe reported
   every Minish hole "dead". Both were the harness. Warping the player in
   and holding a direction is not how the engine sees someone who walked
   to a door, and setting the PL_MINISH bit is not the same as being
   Minish. The first one shipped as twenty-one teleport boxes on doors
   that had been working the whole time, and had to be reverted whole.
   The rule that would have caught it costs one extra run: **before
   reporting that something does not work, point the same probe at a case
   known to work.** If the control fails too, the finding is about the
   probe. A positive result (it fired, it spawned, it landed) still
   stands on its own - only negatives need the control.
9. **Fix the vanilla mechanism; do not replace it.** The user's standing
   call, Aug 2026: "we should ONLY have vanilla door mechanics, no more of
   this teleporting/warping stuff". A position box that fires near a door
   is not a door - it takes the room away from the player instead of
   letting them walk through it, and it cannot play the animation the tile
   was drawn for. When a vanilla door will not fire, the fix is the byte
   that is stopping it (an actTile, a collision value), not a trigger box
   layered on top.

10. **You can ask the ROM directly.** `tools/quickstart/callrom.py` calls a
    function inside the running game and reads r0 - warp into whatever
    state the question is about, hand the CPU an address, get the shipped
    answer. That beats re-implementing a rule in Python and checking the
    re-implementation, which only ever tests the copy. Two details make it
    work: mgba's binding refuses to write r15, so PC is set by having
    `ARMRunFake` execute a `bx r3` (in ARM encoding, not Thumb - after a
    warp the CPU is usually parked in the BIOS IRQ wait), and IME has to be
    cleared or an interrupt carries the CPU off with your LR. Static
    functions are absent from `tmc.map`; their addresses come from
    `arm-none-eabi-nm build/USA/src/game.o` plus the `.text` base. The call
    clobbers the context it hijacks, so it is one question per boot.

11. **A probe that forces state can go stale silently.** Sep 2026: the
    blink-sequence puzzle's first probe reported "the blink does not
    blink", and every part of that was the harness. Three faults, each
    worth knowing on its own:
    * The probe stamped a site's KIND into the flag block, the way
      `plates_check.py` still does. That encoding is GONE - a site is one
      DONE bit now and its kind is computed from `(run_seed, site)`
      (`QuickStartContentSiteRoll`), so poking `gRand` cannot move it.
      Pin the RUN SEED with `boot(rom, seed=...)` and then ask the ROM
      which sites that seed makes gate sites (`callrom` on the roll
      function) - guessing a site's kind is no longer possible.
    * It spawned the player ON the site's content spot, so the caged prize
      was picked up on frame one, `QuickStartSetupContentSite` returned
      TRUE, and the site went DONE before the puzzle ever ran. A ? room
      probe must land somewhere that is NOT the content spot.
    * It read the failure as a bug in the C. Doctrine 8 is what caught it:
      the control run showed the site DONE bit already set, which no
      amount of staring at the puzzle's own code would have explained.
    `plates_check.py`, `roster_soak.py` and `los_check.py` were all still
    using the retired encoding; all three are ported. Two of them turned
    out to have drifted further than that, and both are now labelled in
    their own headers rather than left to mislead:
    * **`plates_check.py`**: the deal leg works again, the WALK legs do
      not. Measured both orders - the FIRST plate the probe visits presses
      and the SECOND never does, whichever it is - so the failure follows
      the order, not the plate, which makes it the harness. It pins the
      player's coordinates every frame instead of walking them, and after
      one long pinned stand the next plate's collision never fires. Same
      family as the textbox trap already recorded there.
    * **`los_check.py`**: both legs now read "not spotted", the control
      included, so by doctrine 8 it says nothing about the mechanism. The
      question it asked is answered by shipped code anyway -
      `stealth_check.py` walks the same LOS pair end to end in a real
      region. Confirmed the drift is not from the site-index port: it
      fails identically with the original line.

12. **Ids come from the build, never from a regex over the header.** A hand
    parse of `include/item.h` returned 52 and 57 for the two overworld
    keys; `build/USA/enum_include/item.inc`, which is what the ROM was
    compiled against, says 55 and 60. A parser that silently drops the rows
    it did not anticipate makes every id after them wrong by however many
    it dropped - and the failure is invisible, because asking a gating
    function about the wrong item still gets a perfectly plausible answer
    back. It made `QuickStartKeyRegionAllowed` look permanently permissive
    when it was in fact answering about items that are not gated at all.
    `parse_tables.ITEMS` reads the generated `.inc`; use it.
