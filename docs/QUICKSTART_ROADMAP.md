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

### 2.1 Win-condition variety (F7) - PAUSED, and its prerequisite

The run's only win carrier is a region's wave clear. Wanted: the Element
can also hang on a boss, a quest, or a ? room. **Paused (user's call)
until the key-item reachability logic exists**: no event may carry the
win until the run can guarantee the player can reach it with the kit they
can actually obtain.

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

- **Scavenger hunt's other two hide modes (F1).** Carrier mode (the
  Keaton chase) shipped; buried (Mole Mitts) and under-bush modes remain.
  Both need per-region tile surveys (diggable spots, cuttable bushes)
  before they can be drawn safely; the quest's mode field and state
  machine are ready. The dig research is shared with the Mole Mitts dig
  rooms below - do them together.
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
- **Hide-and-seek stealth quest (F2).** Research-first: does vanilla's
  guard line-of-sight AI transplant outside its scripted rooms? If yes,
  guards on patrol rows from a table gate a prize; if no, fake it with
  ZELDA-kind patrol NPCs and our own cone check. Park the research
  question early; schedule the build only once answered.

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
  shipped): *hold everything down* (pressure plates + thrown weights),
  *watch the eyes* (blink sequence, wrong order resets, F1c stake at high
  difficulty), *the burning wick* (HELD until key-item logic - fire-gated
  by design), *overworld switch links* (a plate in one ring region opens
  a grate in another; ambitious, gives the compass something to point at).
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
- **Boss death machinery is not family-scoped (#125).** Two bosses dying
  simultaneously softlocks. Latent today (one boss at a time), but it is
  the hard blocker for F6 multi-boss and a real crash risk if any future
  content double-spawns.
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
