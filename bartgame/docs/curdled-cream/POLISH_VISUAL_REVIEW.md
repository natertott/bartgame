# Cream polish: final visual review and evidence scope

Five optional refinements of Cream 6, profiles 7–11, address the user's request
for finished wall textures without apparent cropping, shadows reaching the
wall beneath projecting ledges, cleaner ladder iterations, and brighter blue
waterfalls with 1/2/3 tile widths. These remain local review alternatives.

Game/art source: `687e6c0e999a8df70ef2f7db55f36b9200ddde30`.
[Gallery and downloads](../../../cream-polish-review/README.md).

## Native art and the apparent cropping

The prior opaque panel rectangle could erase the coherent backing, while
forms drawn through a panel boundary looked sawn off. Complete native masters
now finish their important contours/cracks inside the canvas. Explicit masks
keep the entire rock body and internal shade opaque; only the exterior
reveals the actual background. A palette-colored rectangle is not a mask.

Native BG2 composition combines each mask with its true backing. The whole
panel must fit both the available physical wall and the hardware character
budget before placement; a rejected candidate leaves the backing intact.
It does not draw a partial rock and then run out of room. Independent native
checks compare the actual rendered RGB555 pixels with the alpha union.

The common floor/cliff/prop palette remains Rind's material vocabulary. A
separate RGB555 blue-water bank makes liquid distinct from stone and violet
rot. All game drawings begin at final indexed size: 16px cells, full 32px ladder
segments,16/32/48px water widths and32/64/96/128px wall constructions. Inspection
copies use nearest-neighbor enlargement; no downsampled illustration supplies
pixels. Seven unequal masters and a continuous 128×48 backing compose each wall.

| Review option / profile | Wall | Climb design | Water family | Static BG subtiles |
| --- | --- | --- | --- | --- |
| 1 / 7 | Pearlstone Folds | 01 Ashwood Rails | Azure Curtain | 852 |
| 2 / 8 | Faulted Chalk | 04 Ivory Iron | Whitewater Ribbons | 879 |
| 3 / 9 | Ribbed Karst | 07 Stone Staples | Glassfall | 866 |
| 4 / 10 | Weathered Curdstone | 11 Hemp Loops | Split Silk | 894 |
| 5 / 11 | Velvet Travertine | 13 Bolted Timber | Cerulean Cascade | 892 |

Each uses 10 area banks, with up to 128 reserved runtime composition characters
within the 1024-subtile limit. Palette roles, light direction and quiet ground
connect the five treatments. Healthy/sour/deep states retain material identity;
selected bruised fissures develop attached violet cores instead of washing the
whole walking field purple.

## Ladders, projecting edges and shade

The old 16px grip picture repeated across a 32px physical strip produced four
upright rails and busy pegs. Fifteen new source constructions each draw one
full 32px fixture, then install distinct left/right halves. Horizontal treads
communicate climbing; surrounding geological strata do not acquire that
regular narrow cadence. Top sockets join the wall, and floor-bank feet avoid
a dark shaft rectangle pasted onto walking ground.

The chosen five include quiet timber, slim iron, stone staples, shallow rope
loops and cuffed timber. All share the same existing climb mechanic; they do
not create new climbable routes. The source Alternating Pins silhouette is
less explicit than full treads. Hemp Loops supplies the most visibly different
step shape. Source assemblies alone do not establish moving hand/foot contact.

An actual drop has a low broad sill and projecting vertical underside. The
front face agrees with the legal takeoff instead of inventing a new walkable
platform. Permanent rims remain visibly raised and obstructed. The cast shade
joins the real wall base to supported landing ground, preserves existing
floor/path grain and feathers its sides/termination through native clusters.
The gameplay arrival helper remains authoritative, including distant rooms.
A long-drop destination cue does not imply that several screens below are
visible before jumping.

## Water widths and motion

Each fall is one complete 16/32/48px composition. Interior cells are joined blue
water, with wet rock only at the outside contacts. Downward-moving pale streaks,
a crown and a lower foam contact communicate liquid. Width placement fits
eligible rock without covering climbs, gates, features or arrival footprints;
collision is not changed to make a wider decorative waterfall fit.

All fifteen ordinary width clips show visible water in the actual viewport.
The camera reaches its ordinary settled position, without a review-camera or
clock assignment: the recorded waits are16/16/68 frames for widths 1/2/3. Some
long falls' crowns lie partly above the moving camera/HUD; these clips prove
visible width and flow, not an uncropped whole waterfall. Full room surveys
and source assemblies supply the complementary whole-shape view.

## What was actually inspected

Final files under `/workspace/setup/cream-polish/native-r2/` were viewed:

- All 15 healthy/sour/deep registered mosaics, profiles 7–11, at
  `style-N/matched/polish/{stage}/registered-renderer/full-room.png`.
- Sampled first/middle/last ordinary sour-climb and local-drop GIF frames for
  all five profiles, retaining their full unpainted240×160 frame. Private
  contact sheets label these as sampled real clips, not another game render.
- All 15 ordinary waterfall width PNGs. Profile7's1/2/3wide GIFs were additionally
  sampled across four animation phases; highlights and normal enemies advance
  while Bloom remains supported on dry ground.
- Fifteen healthy and deep ladder source sheets, the five-family water source
  atlas, and the original native wall/mask source assemblies.

In these views the wall groups reveal their continuous backing through
irregular contours, without the previous rectangular erasure or abruptly
sliced pale detail. Whole native masses are visibly different among the five
kits. Ribbed Karst has the strongest horizontal bedding read; Weathered
Curdstone is more deliberately planar; Velvet Travertine softens the folds.
The stone-backed relief remains closed beside the real dark cave mouths.

Paired ladders remain readable during climbing, and Bloom stays visible from
standing foot through upper exit. The projecting drop lip has a clearer edge;
sampled real falls end on the wall-connected grey shade. Revised feathering
reduces the initially boxed shadow edges without turning them into black pits
or outlined puddles. Water is distinctly blue, and width changes remain clear
without a separate rock border between every16px stream cell.

Remaining visual tradeoffs are deliberate finite-kit reuse, broad pale wall
strata that may attract attention like small shelves, and restrained attached
violet light. The main terraces, marked drops and actual grips remain the
traversable structures. Mask fidelity and collision preservation do not by
themselves establish artistic quality or every possible procedural join.

## Qualification and preservation

Independent audits pass **32,796 checks**: profile 7 has 6,560; profiles 8–11 have
6,559 each. The five suites include 16,000 closed/open room builds over 64 seeds
per style (64 × 25 rooms × 2 states × 5 styles), source/native pixel and mask checks,
hardware budgets, physical terrain/routes/features, connected destination
shade, and protected art. Exact native RGB555 alpha unions pass in all 15
matched room views. Real menu open/close cache checks pass in profiles 7/11.

All five provide three real climbs with 135/119/151 input frames, plus local
and one-row drops on supported shade. All 15 generated widths 1/2/3 waterfalls
are visible and animate. Profile7 also has the earned four-room drop proof.
Default 0 and the previous Cream 6 rebuild byte-for-byte to their published
ROMs; see the [preservation record](../../../cream-polish-review/validation/preservation.json).

The tested local drop remains 32 physical/32 simulation ticks. The one-row
cases take 74 physical frames in profiles 7–10 and 75 in profile 11, versus 64
in the production control; all retain 46 simulation ticks. That is about
0.17–0.18 seconds more room-loading time in these samples, not slower fall physics.
Composition is prepared during room construction; map writes reuse cached
entries. These finite cases are not a broad active-gameplay performance study.

Registered 512×384 room mosaics freeze simulation and hide HUD to inspect nine
literal native camera crops. Ordinary clips use separate fresh cores, normal
HUD and advancing simulation. Explicit seed, hero navigation/facing and normal
room-load requests select review cases. Health, inventory, enemies, gates,
terrain, VRAM and video results are not assigned in those isolated cores. The
earned long-drop harness separately discloses standing/height normalization at
navigation waypoints while rewards/tools/gates/falls are real input outcomes.
These are instrumented comparisons, not unassisted playthroughs.

[Capture methods and exact fixtures](../../../cream-polish-review/validation/CAPTURE_NOTES.md)
· [Per-build reports](../../../cream-polish-review/README.md#evidence-and-limits)
· [Shared art direction](../art-reboot/ART_BIBLE.md)
· [Viewed Mount Crenel reference](CRENEL_REFERENCE.md)
