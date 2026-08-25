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
  class - present by the hundreds in every ring region
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
- **Hide-and-seek stealth quest (F2). RESEARCH ANSWERED: YES, it
  transplants** - and to exactly the entity kind the fake would have
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
  Still open: *watch the eyes* (blink sequence, wrong order resets, F1c
  stake at high difficulty - the stake helper now exists), *the burning
  wick* (HELD until key-item logic - fire-gated by design), *overworld
  switch links* (a plate in one ring region opens a grate in another;
  ambitious, gives the compass something to point at).
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
  cleared room, three are marginal, none fit a live diff-12 wave. The
  #125 "simultaneous dual kill softlocks" blocker DID NOT REPRODUCE when
  re-tested (see the #125 entry in Known bugs) - the remaining gate is a
  positive: script a real kill of an engaged boss so the dual-engaged
  case can be measured before combos ship. Escort-roster combos ship as
  a per-boss field once measured (blue chuchu + ice wizzrobes is the
  thematic shortlist head).
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
  re-run ring.py + the checker. The adjacency map and distance-2 element
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
     ring room's transitions to anywhere unblessed, and Royal Valley is not
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
  2. `game.c`: a `sQuickStartRegionPool` row, a `QS_RING_*` enum entry, its
     adjacency edges (NHF and Trilby), and the pool-index mapping.
  3. ~~Containment decisions~~ **PARTLY DONE.** Four of Main's five vanilla
     doors are content sites now (user's call): **Dampe's house**, the
     **Great Fairy**, and the **two graves**. Each is a clean pocket with a
     border straight back to Main, all four checker-verified. The **Royal
     Crypt stays blocked**, also per the user - no site row, so containment
     keeps its door shut. Gina's grave is worth knowing about: its exit
     list carries a SECOND border, to Castle Garden Main, and Castle Garden
     is a ring room, so the pocket rule lets that through - the room is a
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
  the eighth named region (`QS_RING_RV`), adjacent to North Hyrule Field
  and Trilby. North Hyrule Field's `WEST_NORTH` border is open, which is
  the only way in. `QuickStartIsRingRegionRoom` names it, so the temporary
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
  each ring region's own `WARP_TYPE_AREA` doors transitively (never back
  out through a ring room, or every pocket ends up owned by everything),
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
  Lon Key. One content site has no owner at all (Melari's Mine's south-west
  room hangs off Melari's Mine, which is not in the ring), and an unowned
  room refuses every gated key - the right answer for a room with no way
  back to the overworld.
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
  `minish_sweep.py` walks every exit the eleven ring rooms have, filters
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
    ring.py, the checker), not a room wiring. It is the natural next
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
  with one border back to the ring room its hole is in, so blessing them
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
  **What to put there** (not built - the user's question, answered with a
  recommendation): the cleared patch is a known, per-fusion coordinate, so
  it is a natural reward spot. Cheapest worthwhile version is the Tingle
  payout's exact shape - poll `CheckKinstoneFused`, pay once per fusion via
  a paid-bit, drop through `QuickStartSpawnRewardEntity` at the revealed
  patch - with an UNCOMMON-tier draw rather than Tingle's heart container.
  The step up in ambition is to make it a challenge: deal a small guarded
  pack at the patch (the satellite spawner already does exactly this in one
  call) and let the drop land when it clears, which turns each brush fusion
  into a miniature ? event without needing a room behind it.

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

11. **Ids come from the build, never from a regex over the header.** A hand
    parse of `include/item.h` returned 52 and 57 for the two overworld
    keys; `build/USA/enum_include/item.inc`, which is what the ROM was
    compiled against, says 55 and 60. A parser that silently drops the rows
    it did not anticipate makes every id after them wrong by however many
    it dropped - and the failure is invisible, because asking a gating
    function about the wrong item still gets a perfectly plausible answer
    back. It made `QuickStartKeyRegionAllowed` look permanently permissive
    when it was in fact answering about items that are not gated at all.
    `parse_tables.ITEMS` reads the generated `.inc`; use it.
