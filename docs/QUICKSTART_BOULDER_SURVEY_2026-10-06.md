# The boulder survey of 2026-10-06: what went in, what disagrees, what to re-measure

The user re-walked Western Wood North, Trilby Highlands, South Hyrule Field
and Lon Lon Ranch from every entrance with the one-way boulders left in
place, and asked for the measurements to go into the reachability graph,
for every conflict with earlier measurements or inferences to be found, and
for every internal inconsistency, typo or ambiguity to be flagged for
re-measurement. This is that record. The data itself is in
`tools/quickstart/world_reach.py` (the four region blocks and their
`entrance()` blocks); the generated graph is `include/quickstart/reach.h`;
the per-entrance tables are appended to each region in
`docs/QUICKSTART_TRAVERSAL_AUDIT.md`.

## 1. What changed in the model

- **The boulders are the player's again.** `QuickStartFillBoulderHoles`,
  which drove every pushable rock in a region room into its hole the moment
  the room settled, is retired. Nothing touches the rocks.
- **Each boulder is a run-time fact.** The rock that settles in a hole sets a
  local flag of its area (`pushableRock.c`); the run start wipes every
  area's local flags; so "boulder X is in" is readable from anywhere and
  means "this run pushed it". Every boulder a survey row names is a
  `QS_REACH_BOULDER_*` bit of the held mask (`world_reach.BOULDER_FLAGS`
  lists the flags, decoded from the `MOVEABLE_OBJECT_MANAGER` entries in
  `data/map/entity_headers.s`). `QS_REACH_LLR_NORTH` is derived: boulder 3
  of Lon Lon Ranch OR the Lon Lon Key, the equivalence the user stated.
- **Reach is per entrance, not per region.** A survey key can now be an
  entrance of a region (`LLR@E903` is the ranch priced from the south-east
  lake landing). The game floods a graph whose nodes are these starts and
  whose edges are the priced exits, each landing at the far side's node
  (`world_reach.LINKS`), from the node the run dropped at. A room is
  offerable to the win chain when some reached node has a satisfied row
  for it. Regions without entrance surveys keep the old reading (any node
  of a neighbour reaches their own start at the old entry price).
- **Goron Cave's stair room is no longer a ? room** (`QuickStartSiteRetired`;
  the row stays so site indexes do not shift).

## 2. The boulders, as the ROM has them

| survey name | rock | hole | pushed from | USA flag | surveyed |
|---|---|---|---|---|---|
| boulder:LLR:1 | (488,904) | (472,904) | the south-east lake landing only | HYRULE_FIELD 0x7b | yes |
| boulder:LLR:2 | (216,904) | (232,904) | "once 1 is in, with the Minish cap" | HYRULE_FIELD 0x7c | yes |
| boulder:LLR:3 | (184,200) | (168,200) | the north field | HYRULE_FIELD 0x7a | yes |
| boulder:TRIL:1 | (344,664) | (344,648) | the south | HYRULE_FIELD 0x92 | yes |
| boulder:WW-N:1 | (408,424) | (424,424) | inside, toward South Field | HYRULE_FIELD 0x93 | yes |
| boulder:CW:1 | (536,808) | (536,792) | - | CASTOR_WILDS 0x15 | older survey |
| boulder:CW:2 | (696,920) | (680,920) | - | CASTOR_WILDS 0x16 | older survey |
| boulder:CW:3 | (696,328) | (696,344) | - | CASTOR_WILDS 0x1e | named, never priced |
| boulder:CREN:1 | TOP (760,88) | (744,88) | - | MT_CRENEL 0x3f | not named |
| boulder:CREN:2 | TOP (952,136) | (712,24) | - | MT_CRENEL 0x40 | older survey; **numbering assumed** |
| boulder:LH:1 | (40,536) | (40,520) | - | LAKE_HYLIA 0x07 | **never surveyed** |
| boulder:WR:1 | ENTRANCE (184,488) | (168,488) | - | RUINS 0x25 | **never surveyed** |
| boulder:WR:2 | FORTRESS_ENTRANCE (136,88) | (120,88) | - | RUINS 0x2a | **never surveyed** |

The user's coordinates for Lon Lon's three ((472,906), (232,906), (168,202))
are the HOLE positions, which is the right thing to have stamped. The
numbering here is the user's; the previous survey called today's 1 and 2
its 2 and 3, and its 1 was the ranch house's east door.

## 3. Conflicts with earlier measurements and inferences

Each of these was resolved in favour of the new walk unless marked.

1. **Trilby's boulder pocket was priced free.** Percy's treehouse, the
   rupee and fairy-fountain caves and the seam into Western Wood North were
   all "free" from the North Field entrance in the old block. That walk was
   done with the auto-fill on; the new walk prices them at "boulder in OR
   the Power Bracelets", which the old Keese-chest row already did. Not a
   measurement error - the old rows measured a filled hole.
2. **Lon Lon's Goron cave.** Old: `boulder 3 (= today's 2) OR Minish`, no
   fusion. New: `fusion AND boulder 2`, no Minish route. Two differences:
   the fusion was missing before (vanilla's Goron cave is opened by a
   fusion, so the new reading is the plausible one), and the Minish
   alternative is gone. **Re-measure: is there a Minish-sized way into the
   Goron cave that skips boulder 2?** The old row thought so.
3. **South Field's rupee cave.** Old: `fusion`. New, from the north
   entrance: `sword AND fusion`. The old start was a mid-transition stamp
   whose entrance nobody could name; the new reading stands.
4. **Link's house.** Old: `story_flags` (an untestable token, so the house
   was invisible to the chain). New: nothing. The mode sets the flags at
   boot; the old token was a leftover.
5. **Western Wood North's south seam.** The audit said the seam into
   Western Wood Center costs a fusion, from the old row at (416,648). The
   new walk prices the seam at (284,636) free and keeps a fusion-only
   pocket at (33,633). Both are true of different spots on the same edge;
   the old row is carried over as the pocket it is.
6. **Lake Hylia's side of the ranch border.** The lake's derived block
   lands on Lon Lon at (712,328); the walked ranch exits are at y 445, 750
   and 903. The 328 row is linked to the E445 landing as the nearest.
   **Re-measure: walk from the lake's arrival shore to the ranch border and
   confirm it meets the north field (E445) and not a cliff.**
7. **Lon Lon's free Minish stumps.** `MINISH_PORTAL` prices Lon Lon's
   Minish token free on the strength of unhidden stumps at (344,544) and
   (280,48). The new walk prices the Minish paths at the Pegasus Boots
   (the tree-hidden stump at (313,391)) from every entrance. Not a
   contradiction if the open stumps cannot walk, as Minish, to the paths'
   door at (480,372) - but **confirm which stump you used for the Minish
   paths, and whether (344,544) is in the south half at all.**
8. **The ranch house's west room** is not in any of the new lists. The old
   row (`Minish OR the key`) is carried over unchanged.

### 3b. What a collision flood says about the same rooms

`tools/quickstart/boulder_probe.py` floods Lon Lon Ranch and Trilby
Highlands from each landing over the collision map (pit tiles excluded,
boulders placed by the ROM for each flag combination). A flood is blind
to ledges, one-way drops, Minish doors and fusion walls, so it can only
confirm walls, never open ways. Where it agrees with the walk nothing is
said; the four places it does not are below.

1. **The ranch cave's lower door (232,436) sits in the south half.** With
   no boulder in, the flood from the south, north-west and E903-plus-
   boulder-1 landings all reach the door; the walk prices the cave at
   "boulder 3 or the key, and the Power Bracelets". If the door really is
   walkable from the south, the gate on the cave (and on the Tingle pocket
   above it) is the bracelet stone alone and boulder 3 drops out of both
   rows. **Re-measure: from the south entrance, no boulders, walk to the
   cave door at (232,436).**
2. **The E445 landing is a cliff in collision.** With no flags the middle
   lake landing reaches nothing but its own exit; with boulder 3 in it
   joins the south half. That is the walk's reading (the north field is
   LLR_NORTH) and means the ledges off the north field are one-way drops
   the flood cannot cross, which the lists never state. Worth one line in
   the survey: which drop joins the north field to the south.
3. **Trilby's boulder pocket is a ledge, not a hole.** With the Trilby
   boulder in its hole, the flood still cannot enter the pocket (Percy's
   treehouse, the two caves, the Western Wood seam): the tile south of the
   filled hole has collision 41, a ledge. So the walk's "boulder in OR the
   bracelets" is a drop the player takes, not a floor the boulder makes,
   and the pocket is one-way from the main field. Consistent with the
   lists; recorded so nobody tries to flood-verify it again.
4. **The first flood disagreed and was wrong.** Counting the empty holes as
   floor put the E903 landing in the south half with no boulder, against
   the walk's "boulder 1 walls it". Holes are act 25 and the player falls
   in; with pits excluded the landing is a pocket until boulder 1 is in,
   exactly as walked. Kept here because the roadmap briefly carried the
   wrong reading.

Also found by the probes, not by the walk: **Mount Crenel's entrance (site
82) never dispatched** as a ? room, because it is the Crenel pool row's
own room and a pool room runs its region monitor instead of the site
loop. It is retired alongside the Goron stairs; a lesson stored there
would never have fired.

## 4. Internal inconsistencies, typos and ambiguities in the new lists

These are the ones to re-measure or restate; the model took the reading
noted in brackets.

1. **Boulder 1, who pushes it.** The notes say "Boulder #1 can only be
   pushed in from the South Eastern entrance to Lake Hylia", and the south
   entrance's list opens with "The player can push in Boulder #1 from this
   entrance", then prices the (712,903) exit at "boulder #1 must be pushed
   in". The first line of the south list contradicts the other two. [Taken
   as: pushed from the E903 landing only. If the south side CAN push it,
   say so and the E903 exit becomes free from the south.]
2. **Boulder 2 needs the Minish cap.** "If boulder #1 has been pushed in
   and the player has the Minish cap, then they can push in boulder #2."
   Why the cap? [Recorded as stated; the model only ever reads the flag, so
   nothing hangs on it, but the reason belongs in the survey.]
3. **The lower lake landing (712,750) is asymmetric.** From the north field
   the crossing takes the cape, the Flippers, or the cane and the cap;
   from the landing back in, "add Roc's Cape to every requirement" - only
   the cape. [Recorded as stated.] **Is the landing a ledge you drop off,
   so the Flippers do not get you back up? Please confirm.**
4. **South Field from the NNE entrance: Link's smithy.** The house
   entrance costs a sword, the smithy's room behind it "nothing". [Priced
   at the sword.]
5. **South Field from the NNW entrance: the heart-piece tree** line is cut
   off after "sword and". [Priced at sword and the fusion, as from the north.]
6. **South Field from the NNW entrance: the NNW exit** is priced at a sword
   although it is the start itself. [Free.]
7. **South Field: the rupee cave** is priced only from the north entrance
   and missing from the NNE and NNW lists. [Only the north row exists.]
8. **Lon Lon from E445 and E750: the (712,903) exit** is missing. [Kept at
   the south list's price, boulder 1.]
9. **Trilby from the south: the near half of the two-ladder cave (296,56)**
   is described but not priced. [Free, as from the north-east.]
10. **"Exit to Hyrule Town."** Lon Lon's (8,560) and Trilby's (472,560) are
    the same border, Hyrule Town having been stitched out of this build
    (docs/QUICKSTART_RETARGETS.md). [Linked to each other.]
11. **"Boulder must be pushed in"** without a number, on the south list's
    (712,750) row. [Boulder 3, as the E903 list says.]
12. **The Veil Falls entrance** is surveyed as a start, and this build has
    no way into Veil Falls. [Recorded; nothing links to it.]
13. **Dig cave entrance 2's Flippers-or-cape.** The fusion lays land in
    front of the dig spot; the list still wants the Flippers or the cape
    to stand on it. [Recorded as stated.] Worth one sentence on what the
    water is for.

## 5. What the entrance model still cannot see

Landings nobody has walked from, so the game lands the player at the
region's old start there (the previous, optimistic reading). In order of
how much the win chain leans on them:

1. **Eastern Hills North from the Lon Lon border** (its north edge). The
   only row at that edge, (308,-2), costs bombs FROM THE WEST, so the
   landing is a pocket the old survey never stood in.
2. **South Hyrule Field from Western Wood Center, Western Wood South,
   Eastern Hills Center and Eastern Hills South** - four seams priced from
   the port model only.
3. **Trilby Highlands from Mount Crenel Base** (the west border).
4. **Lake Hylia's arrival shore** with its own boulder (40,536) in place:
   the derived block was flooded with the hole filled.
5. **The Wind Ruins' two boulders**, same reason.

## 6. What the measurements changed for the player

- Trilby's south-west is a real pocket now: a run without the bracelets
  that enters from the north cannot reach Percy's treehouse, the rupee and
  fairy caves or Western Wood North through it until something pushes the
  boulder from the south. The win chain will not place a step there until
  it is in; a wave in Trilby stays on the player's side of it (the region
  spawner filters offsets by the player's flood). The boss arena, which
  was in that pocket, moves - see the roadmap entry.
- Lon Lon Ranch's north field is behind boulder 3 or the key from the
  south, west and North Field entrances, and open from the two upper lake
  landings; the south-east landing is a vestibule until boulder 1 is in.
- Western Wood North's South Field seam is a dead end from the South Field
  side until the boulder is pushed from inside.

## 7. The user's answers (second pass), and what moved

Every item in sections 3 and 4 has an answer now; the model reads as
follows.

- **No Minish route skips boulder 2.** Confirmed; the row stands.
- **The three lake crossings** are ranch (712,443) / (712,762) / (712,908)
  to lake (8,443) / (8,746) / (8,905). The lake block's (712,328) row was
  a coordinate no crossing has; it is the middle crossing and now reads
  (712,445) with its link to the E445 landing.
- **The Minish paths** are reached from the Pegasus Boots stump only; the
  two open stumps are cut off from them. Confirmed; `MINISH_PORTAL`'s free
  Minish token for the ranch prices being small, the paths' own rows carry
  the boots.
- **The ranch cave's lower door** needs boulder 3 or the key. Confirmed;
  the collision flood's reading in section 3b is the flood being blind to
  a ledge, and is withdrawn.
- **Boulder 1** is pushed from the south-east lake entrance only; the cap
  on boulder 2 is for the tornado hop onto the ledge above the Goron
  cave; the lower lake landing is a ledge the Flippers cannot climb from
  the south; the (712,903) exit from E445 and E750 is boulder 1; the
  South Field tree is sword and fusion; every room in the South Field
  house costs the sword; the near half of the two-ladder cave is free;
  the dig-cave water is what the fusion lays land over. All recorded as
  stated; none moved a row.
- **"Trilby has only one boulder, and it should have been referenced as
  boulder #1."** Item 11 was about Lon Lon's (712,750) row, which says
  "Boulder must be pushed in" with no number; the model keeps boulder 3
  there (the E903 list names it). If that row meant something else, say
  which.

## 8. Veil Falls, walked 2026-10-06 and integrated

The falls are the fourteenth region: a pool row (the drop lands on the
plateau at the foot of the big falls), twelve content sites, five fusers,
eighteen enemy spots over every piece of land, waves as scenery only
(like Lake Hylia: the pieces are joined by a Grip Ring climb, water and a
one-way ledge, so nothing counts the room to zero), no boss. The survey
is `world_reach.py`'s `VF`, `VF@NHF`, `VF@LLR` and `VF@POCKET` blocks and
Lon Lon's new `LLR@POCKET`; the roadmap entry has the rest.

**Cave #1's door.** In vanilla the Source of the Flow - a stone face, NPC
4E type 11, standing at the cave mouth (56,509) - seals it until the
player fuses `KINSTONE_SOURCE_FLOW` with the stone itself. The matching
gold piece is the one King Gustaf's ghost gives in the Royal Crypt
(`script_KingGustav.inc`, `GiveKinstone 0x6d`), which this build has no
way to. The stone is deleted at its init under QUICKSTART (`npc4E.c`),
and the door was MEASURED open on the delivered ROM: a player walked north
from (56,560) is inside VEIL_FALLS_CAVES/ENTRANCE eighty frames later
(`tools/quickstart/veilfalls_probe.py`, DOOR). If you saw a "special
door" there, say which build; on this one there is nothing in the way.
The cave is dark, and the lantern is what the rows charge for it.

**The gold chest on the ledge.** It is the one chest VEIL_FALLS/MAIN
carries in its tile data, at (200,360), tile (12,22), on the ledge beside
the big falls at rows 21-24. Everything about the ledge is in the exit
lists: the block-puzzle cave's south border lands on it at (216,344), and
the ledge's own door at (13,19-20) leads back into that cave. So the
ledge is the block-puzzle cave's doorstep. Into the cave from the other
side: cave #1's upper room (EXIT) has a bombable north wall - flag
`SUIGEN_DOUKUTU_04_BW00`, "wall to secret area blown open" - and its
rectangle abuts the SECRET_CHEST room's on the caves' pixel grid (a
scroll seam), from where a door leads to the dark SECRET_STAIRCASE and
another to the BLOCK_PUZZLE; solve the blocks, walk out the south door,
and the chest is on your left. Measured on the way: stepping off the
waterfall climb onto the ledge does NOT work (the climb holds the player
on the falls). The four rooms are priced at the lantern and the bombs
and marked INFERRED; **walk them**: cave #1's upper room, bomb the north
wall, through to the block puzzle and out onto the ledge.

**The whirlwind on the Top screen** carried a player straight into the
Cloud Tops (measured), which this mode does not include. It is removed
(`bigVortex.c`); "Tornado up to the sky" is no longer a destination.

**North Hyrule Field's east edge was linked backwards.** Walked on the
delivered ROM (scratchpad `vf_borders.py`, six crossings): a border keeps
the GLOBAL coordinate, so the north half of the field's east edge - the
bomb pocket your field rows price at (999,112) - is the Veil Falls
crossing, landing in the falls' corridor at (8,639); and the field's
start itself, (1013,638), is the Lon Lon crossing, landing at the
ranch's (10,163). The survey had the two links the other way round.
Fixed, and the field gained an entrance `NHF@VF` for the player who comes
DOWN from the falls: they land in the bomb pocket, so every row from
there carries the bombs on top of the field's price. INFERRED from the
field's own row for the pocket; **walk it**: from the falls' corridor
into North Hyrule Field, and say what it takes to leave the pocket.
All six border crossings - the ranch's two north halves both ways, the
field's east both ways - were walked and land where the rows say.

**Inferred rows to re-measure**, besides the ledge chain:

- The drop plateau's own rows (`VF`) are your North Field rows with
  "cave #1" taken off everything past the cave, because a drop lands past
  it. From the plateau: the North Field exit and the cave's two rooms cost
  the lantern, the top plateau and the upper caves the grip, the pool the
  flippers.
- The heart-piece nook behind the small upper-left waterfall carries a
  FUSION on top of your "grip and flippers": `KINSTONE_13`'s world event
  (type 9, the waterfall-cave reveal) has its marker at that nook's door
  (56,40). **Does the nook open without it?**
- The lower strip (`VF@POCKET`, where the ranch's gold-chest pocket lands
  at (176,1000)) is your Lon Lon list without the way back up to
  (88,1000): the ledge at tiles (10,54)-(10,56) is one-way down.
- Lon Lon's north gate landing (`LLR@N`) is priced as from the south gate.

**Kinstone events in the falls**, all five placed as fusers on the drop
plateau: 1D (the Splitblade dojo's archway, your "kinstone fusion event"),
61 (the gold chest on the top plateau), 4A (the golden enemy up there),
1F (the land in front of dig-cave entrance 2), 13 (the heart-piece nook).
KINSTONE_E, the Biggoron fusion on the Top screen, is left out: its event
is the Mirror Shield cutscene, and the vanilla Gorons are swept off that
screen instead.

