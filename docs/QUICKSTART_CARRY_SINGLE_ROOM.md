# The carry quest, single-room version (Oct 2026)

Status: **built** (section 10 says how it differs from this plan). The
cross-room carry quest it replaces is gone. Sections 1 to 9 are the plan
as written, with the user's answers in section 9.

The user's brief:

> Restrict it to a single room. Focus on small rooms with complex layouts:
> Minish Woods, North Hyrule Field, Veil Falls, Mount Crenel, Castor Wilds.
> Carry the object a long way in the room, corner to corner or around the
> edge, across more than one node of the reachability survey. The player
> must definitely be able to get it from A to B. The player must be able to
> throw it. What if it is thrown somewhere unreachable, into water, into the
> murk in Castor Wilds? How is that detected, where does it respawn? Spawn
> a mix of enemies: ones that pursue Link, ones that fire projectiles, and
> ones that impair movement (beetles, flaming skulls, ice and fire
> wizzrobes).

## 1. Why the old one failed, in one paragraph

The parcel was a SHOP_ITEM prop, vanilla's buy-it-in-the-shop object. A
prop cannot be thrown: put down, it goes back to its pedestal. It also does
not survive a room seam: the transition deletes loose entities and clears
the hold. The old quest bridged the seam with a save byte and a re-lift on
the far side. The probe passed that (9/9), but in play it still breaks. A
single room removes the seam. A different object adds the throw.

## 2. The object: an unbreakable pot

**Recommendation: a vanilla POT with one flag that stops it breaking.**

- Pots are lifted with R and thrown with R or A, bare-handed. No item is
  needed, and every player already knows how.
- `pot.c` is already in this mode's variant list. A pot whose type2 marks
  it as the parcel would, on landing, go back to resting and liftable
  (action 1) instead of `BreakPot`. Wall hits and a hit to Link while
  carrying end the same way: it lands, it does not break.
- It still hurts enemies when thrown, so it doubles as a weapon. That is a
  feature: the player can fight with it instead of putting it down.
- Its sprite lives in the shared object graphics, so it draws in every
  overworld tileset.

Alternative considered: the **cucco** (Anju's minigame bird). It is carried
and thrown natively and flutters down instead of breaking, but it is an NPC
with its own movement, so it wanders when put down. It would make a good
second skin later.

## 3. Detecting a bad landing, and where it comes back

The engine already sorts landings. `GetTileHazardType` (asm, used by
`pot.c` when a thrown pot lands) returns:

| value | tile | vanilla effect |
|---|---|---|
| 1 | pit (act tile 0x0D) | falls |
| 2 | deep water (0x10, 0x11) | splash, sinks |
| 3 | lava (0x5A) | burns |
| 4 | swamp (0x13) | **sinks in the murk: Castor Wilds' swamp is this** |

That covers water and the murk without new detection. The harder case is
dry ground the player cannot reach, like a cliff top or a fenced pocket.
For that, each quest room gets a **carry map** computed offline (section 4).
It is a bitmap of the tiles that are reachable on foot from A **while
carrying**, and from which B is reachable the same way.

**The rule, checked every time the parcel comes to rest:**

1. If it rests on a hazard (1 to 4), play vanilla's splash, fall or sink
   effect.
2. If it rests on a tile outside the carry map, do the same.
3. In either case the parcel reappears at its **last good rest spot**: the
   tile it was last lifted from. A small sparkle and SFX mark the return,
   and Ezlo says "It's back where you picked it up" once per run.
4. A landing inside the carry map is simply where it now lies.

The last good rest spot is stored in run-cleared bits (two bytes, tile
x/y). A careless throw costs the distance since the last lift, never the
whole trip. The alternative is a full reset to A. That is harsher, and it
is your call (question 1).

If the player **leaves the room**, the parcel stays at its last good rest
spot (or at its landing, if that was good) and is there on return. Nothing
crosses a seam.

## 4. Guaranteeing A to B: the carry map and the pair table

"Definitely reachable" has to mean reachable **while carrying**, which is a
stricter mobility than the reach survey's. While holding a pot, Link
cannot swim, climb, use the cape, shrink, dig or dash. Before trusting any
of this I would measure in the emulator which of these hold:

- Can Link hop **down** a ledge while carrying? Vanilla Zelda usually
  allows it. If so, ledges are one-way edges in the carry map.
- Does shallow water slow him or drop the pot?
- Can he go up or down stairs within a room while carrying?

Then a new tool (`carry_map.py`) builds, for each candidate room:

1. Live collision, flooded tile by tile with the measured carry rules
   (ledges one-way, no water, no ladders, no Minish passages), starting
   from each walkable tile. The probe already floods live collision for
   the dungeon reach map, so this reuses that code.
2. **Candidate pairs (A, B):** both on open floor, B reachable from A
   while carrying. The carry path must be at least about 60% of the
   room's longest walk ("corner to corner or around the edge"), and it
   must cross at least two survey places of `world_reach.py` (e.g. from
   the Western Wood's south shelf to its north pocket). It must also avoid
   places that need an item the player may not have. Each pair carries the
   item requirements of the places its path crosses.
3. A table emitted into game.c: per pair, the room, A, B and the
   requirement mask, with the room's carry-map bitmap. That is about 300
   bytes for a 64x64-tile room, less for smaller rooms.

**At run time**, the quest picks a pair whose requirements the player's kit
meets at the moment they accept it. That is the same "pick against the
real kit" rule the old quest used for its region choice.

**Proof, not trust:** a probe (`carry_room_probe.py`) plays every pair in
the table. It lifts the parcel at A and walks Link along the planned path
with real key presses, parcel overhead, hopping the ledges. It delivers at
B. Then it throws the parcel into each hazard kind the room has, and onto
one unreachable dry tile if the room has one, and checks the parcel comes
back to its last rest spot. A pair the probe cannot finish is dropped from
the table.

## 5. Rooms

The five regions you named, each as its field room or rooms:

| region | why it suits | hazards to cover |
|---|---|---|
| Minish Woods | narrow paths, one-way ledges, water channels | deep water |
| North Hyrule Field | long perimeter, ledge terraces, pockets | ledges only |
| Veil Falls | stacked shelves, a long climb | deep water, pits |
| Mount Crenel | ledges and drops everywhere | pits, cliffs |
| Castor Wilds | swamp everywhere, few dry routes | **the murk** (hazard 4) |

The table decides which pairs exist. A room where no pair passes the
probe simply offers none.

## 6. The quest's shape

- **Giver at A**, standing beside the parcel: "Carry this to my friend
  across the way." A **receiver at B** in another skin. Both reuse the
  courier's talking machinery.
- Delivery happens by standing near the receiver with the parcel in hand
  (the old proximity test), or by setting it down within a tile of them.
- The payout is the same as now: a RARE draw at B's feet. It counts as the
  run's side quest for the win chain's QUEST step.
- One quest per run, in one of the five regions, rolled like the other
  givers so they keep separate regions.

## 7. Enemies

They spawn when the player **first lifts** the parcel: a fixed budget
spread along the path's middle stretch, never within four tiles of A or B.
They stay until killed, and a second, smaller wave spawns at the halfway
point. Each wave mixes three roles:

| role | candidates already in the mode | note |
|---|---|---|
| pursue Link | `sQuickStartPursuers`: red and blue Stalfos, Spear Moblin, Helmasaur, Ghini, the coloured Keatons, blue Chuchu | the survive-room list, soak-tested |
| fire projectiles | Octorok, Bow Moblin (arrows), Fire, Ice and Wind Wizzrobes, Bombarossa, Fireball Guy | the tier tables' `QS_R_RANGED` picks |
| impair movement | Beetle (latches on), Ice Wizzrobe (freezes), Fire Wizzrobe (sets Link running), Like Like (grabs), Spark (circles the walls) | a hit while carrying drops the parcel, which then lands under the section 3 rule |

**Flaming skulls, a question.** The only skull enemy is the Flying Skull.
The Fireball Guy, a bouncing flame, is the other candidate.
`pursuer_soak.py` found it inert as a standalone enemy, but that measured
the lying-bone form (type 0). Its type 1 rises and dives at Link when he
comes within three tiles, which fits an ambush along the path. If you meant
a different enemy, tell me which room it appears in (question 3).

The budget scales with difficulty, like the waves. It also goes through
`QuickStartGfxBudgetForSpawn`, because Veil Falls and Castor Wilds are
already the busiest rooms in the performance census.

## 8. Order of work

1. Measure the carry rules (ledge hop, shallow water, stairs, hit-drop)
   and the pot's landing paths. One probe, about a session.
2. The unbreakable parcel pot, with the landing rule and the respawn.
   Probe it with throws into each hazard.
3. `carry_map.py` and the pair table, rooms one at a time, starting with
   North Hyrule Field (one room, no swamp).
4. Giver, receiver, payout, side-quest credit. Retire the old cross-room
   parcel code.
5. Enemy waves. Then play-test, then the other rooms.

## 9. Questions for the user, answered

1. A lost parcel comes back to **where it was last picked up**.
2. Unreachable dry ground **counts as lost**, with water, pits, lava and
   the murk.
3. "Flaming skulls" meant the **red and blue Wisps**; use the **Flying
   Skull** too.
4. A **giver at the start and a receiver at the end**.

## 10. As built (Oct 2026)

What changed between the plan and the ROM, and what was measured on the
way (`carry_measure.py`, `carry_pairs.py`, `carry_room_probe.py`).

**The parcel.** A vanilla pot, `CreateObject(POT, 0xFF, 0x50)`: type2 0x50
marks it. `pot.c` hands it to game.c at the three places a pot's carry or
flight ends: the lift (`sub_08082510`, which records where it was lifted
from and, the first time, starts the quest's first wave), the landing
(`sub_0808259C`) and `BreakPot`. Every way a flight ends reaches one of
the last two: a throw, a drop when Link is hit, a hazard tile
(`playerItemHeldObject.c` ends them all with the pot's sub-action 3).
`QuickStartParcelLanded` stands a fresh parcel where it landed or back at
the lift spot, and the old one is deleted.

**Good ground is a bitmap, not a flood.** The plan had the landing check
flood the room live from B. A full-room flood measured **1.3 million
instructions** in North Hyrule Field, 4.7 frames of stall on every
landing. Instead `carry_pairs.h` carries each pair's PIECE, one bit per
tile: the carry grid's piece holding A and B (open tiles, no hazard act
tiles, bushes and ledges as walls). A landing in it stays; outside it, or
on a hazard, it is lost. A pot stopped by a wall comes down on the wall's
part-solid edge tile, so the open tile beside it counts. And it never
comes back on Link's own tile, which a pot dropped mid-lift would (its
solid marker tile would shut around him).

**Where pairs come from.** Not one big component per room: in these
rooms the carry grid falls into many pieces (Veil Falls' biggest is 97
tiles, Castor Wilds' 277 once the swamp is out). Pairs are made per
ARRIVAL PIECE: the piece under a vanilla transition's landing, the pool
row's entrance, or a survey place (its exits are the border crossings).
The game picks, once per run on the first settled frame in the room, the
first pair whose piece holds the player's tile. Wherever they came in,
they can walk to A and carry to B without cutting a bush.

| room | pairs | carry length (tiles) |
|---|---|---|
| North Hyrule Field | 1 | 65 |
| Minish Woods | 1 | 32 |
| Mount Crenel's base | 2 | 41-42 |
| Castor Wilds | 3 | 28-35 |
| Veil Falls | 0 | no piece has a 24-tile walk |

Veil Falls has no pair. Its ledges cut it into pieces too short to carry
across. Ledge hops while carrying would join them; that was not measured
here.

**The parcel's home is three tiles from the giver.** Beside the giver, R
at the pot talked instead of lifting: the giver's talk box
(`QuickStartMakeNpcTalkable`) is an oversized 40x40, and talk beats lift.
So each pair names a home tile H, three tiles off, and the generator
keeps A, H and B clear of the room's own NPCs.

**Measured engine facts.** A pot must stand on a tile centre (x = 16n+8):
its solid marker tile and its lift hitbox only line up there. Walking on
into a pot shoves it a tile (16 px). R mid-lift (`heldObject` 3, not yet
4) drops the pot at Link's feet. `gPlayerEntity.carriedEntity` is the
held-object player item, and the pot is its `child`. Deep water and pits
already count as solid in the collision map; the swamp does not (672 of
Castor Wilds' 1927 open tiles), which is why the hazard act tiles are
filtered out of the grid.

**Dry ground out of reach.** No room offers a throw onto unreachable dry
ground: a thrown pot is stopped by cliff faces, and no pit or channel
beside a carry piece has dry ground just beyond it (searched in all four
rooms). The rule is in and tested on the game's own code: the probe puts
the held parcel on open ground outside the piece and calls
`QuickStartParcelLanded`, which sends it back to the lift spot.

**Enemies.** First wave on the first lift, at a third of the way from A
to B: 3 + difficulty/3. Second wave when the carried parcel is half-way
(Manhattan) to B, at three quarters of the way: 2 + difficulty/4. Roles
in turn: a pursuer (`sQuickStartPursuers`), a shooter (Octorok red or
blue, Bow Moblin, Wind Wizzrobe), a movement-impairer (Beetle, Ice or
Fire Wizzrobe, red or blue Wisp, Flying Skull type 1). The first
impairer of each wave is always a Wisp or a Flying Skull, the user's
named three.
