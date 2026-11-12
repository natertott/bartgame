# Fractured Rind: optional Cream study 6

This exploratory local synthesis follows the user's preference for study 2's
contrast/arches, study 3/5's wall textures and especially study 5's colors.
Build with `make -C bartgame BART_CREAM=6`. Production 0 and studies 1–5 remain
selectable; this pass does not adopt a new default.

The [gallery](../../../cream-depth-review/README.md) separates source drawings,
frozen registered room mosaics and ordinary live mGBA footage.

## Materials and composition

Study 5's exact eight RGB555 environment banks and quiet pale ground remain.
Broad mineral planes, unequal overhangs, irregular grime seams and fractured
strata replace the repeated little fans. The actual cave uses study 2's pointed
construction in study 5's palette roles, with a damaged asymmetric crown.

Healthy stone carries dormant stress seams. Sour stone loses chips and gains
wider bruised cracks. Deep stone exposes branching violet cores with small
attached glints. The same masses remain recognizable while corruption changes
both material structure and palette. Floors remain quieter than actors,
interactables and useful contact points.

`art/cream_depth_walls.py` authors native paintings at final pixel coordinates:

| Family | Native size | Role |
| --- | --- | --- |
| Two shelf/fold faces | 64×32 | Unequal overhangs and broad lit planes. |
| Two fractured spans | 96×32 | Connected stress fractures and asymmetric ribs. |
| One blind arch | 64×48 | Closed architectural relief with solid rock backing. |
| Two compact remnants | 32×32 | Detail for genuinely narrow remaining wall. |
| Continuous backing | 128×48 | Quiet strata/grime beneath and between panels. |

The pictures are cut into 16×16 cells after drawing. They are not enlarged
tiny tiles or downsampled illustrations. Backing phase remains continuous
across the room face, so quiet areas do not expose a grid of small scallops.

## Fit art to actual generated wall

`src/cream_visuals.c` measures unused midface after semantic routes and room
content have been drawn. A complete panel must fit its measured footprint;
it cannot clip around a cave, waterfall, climb shaft, gate or prop. Seeded
staggered anchors mix unequal forms, prevent an identical panel immediately
meeting itself, and cap foreground panel coverage at three quarters of the
available face. At most one complete blind arch appears when space permits.
Its closed stone backing distinguishes it from a real open cave and approach.

This changes picture composition, not the maze. Substitutions must preserve
terrain type, collision, property and glitter metadata. Existing code remains
authoritative for geometry, directed routes, climbing, enemies/content and
requirements. The wall composition runs during room construction; edge and
landing refresh runs when a gate changes, not every frame.

## Ledge borders and truthful destination shade

`art/cream_depth_edges.py` distinguishes raised blocked rock from a low open
sill. Neighbor-aware returns join the blocked rim; actual drop intervals have
endcaps and no second impassable-looking curb directly below. Regular pale
grips remain exclusive to real climbable shafts.

The cliff toe and immediate textured floor shade describe wall contact. A
separate landing patch marks actual incoming directed drops. Coordinates come
from `cream_room_arrival()`, including cross-room and multi-screen routes; the
picture cache is not a second source of gameplay destinations.

The 48×32 landing master has a shallow asymmetric shadow, retained floor grain
and a broken lower edge. It has no black pit outline, bright target or arrow.
Compatible plain floor and paths receive their matching shaded drawings;
path-specific variants retain the pressed route grain. Hazards, gates and
objects keep their own drawings. Clearable gates suppress their route's
active destination cue until opened; cape-only gaps may retain it because the
physical pit remains after acquiring the cape. Read-only telemetry records the
real target and painted portions for native arrival comparisons.

The [Mount Crenel reference note](CRENEL_REFERENCE.md) records actually viewed
source URLs/digests and access limits. Its plane hierarchy and raised rim/low
sill distinction inform the original art. Destination shading is the user's
requested enhancement; no Nintendo pixels become game assets.

## Independent final visual review

Actually inspected candidate 3, source `9747a925`, under
`/workspace/setup/cream-depth/native-r3`: all three study 6 full-room mosaics,
matched study 5 sour mosaic, and sampled 240×160 frames from the ordinary
local-drop, one-row-drop and sour-climb GIFs. Also inspected the native source
atlases, 3× continuous backing and earned four-row destination frame. This is
direct visual review of those
images and sampled motion poses, not a claim to have watched every captured
frame or completed an unassisted playthrough.

The broader quiet planes and staggered panel groups remove the conspicuous
16px filler scallops and regular ivory-seam cadence. The room reads as pale
walking ground separated by continuous vertical rock. The blind arch reads
as sealed relief beside the stronger negative space of actual cave mouths.
Landings retain ground texture under the real actor, reducing the isolated
atlas's puddle ambiguity. The one-row clip visibly includes a partially black
room-loading transition; it is not omitted from the timing qualification.

The finite kit still repeats recognizable panel shapes. Pale overhangs can
look shelf-like while Bloom falls past them, although they are not physical
intermediate platforms. Violet is controlled rather than covering the ground,
so deep corruption remains relatively restrained. These are visual tradeoffs
for review, not evidence of a collision defect or universal seed coverage.

## Exact build, scope and evidence

Source: `9747a92526fe9162d93a1ed46b8a6b8292841bb4`.
ROM SHA256: `2b8559c3cac89f483d3a34d48aa6eb5144a4fc2b3b7b265808b800672216a1b1`.
The optional study uses 861/1024 BG subtiles and 10/12 area banks.

The asset/geometry audit passes 5221/5221 checks: 375 appended metatiles and
523 source frames match their original native drawings; 64 seeds cover 1600
layouts in closed/open states for 3200 builds. It verifies 3582 exact incoming
anchors, 3516 active feet with shade, 66 suppressed closed cues, 3200 idempotent
refreshes and 40 real unlocks with unchanged physical contracts. Matched
rooms/climbs pass 61 checks, physical comparisons 38, isolated drops 26 and
the earned four-row drop four. Production 0 is byte-exact to the published
control, SHA256 `0dd8554384b53e618140f8c61590fc7e6a7ff0888f296ece034a95f357b34fdd`.

New native drawings and the optional compositor extend the study 5 utility/
object kit, with the pointed cave. Bloom, enemies, NPCs, menus/HUD, original
music and other regions retain their current art. This is not a redraw of all
actors or every shared handoff object. No filtered scaling or screenshot color
grading supplies game pixels.

Final reports: [asset/geometry audit](../../../cream-depth-review/validation/native-audit.json),
[native capture/physical comparison](../../../cream-depth-review/validation/native-capture.json),
[matched rooms/climbs](../../../cream-depth-review/validation/matched-capture.json),
[isolated drops](../../../cream-depth-review/validation/isolated-drops.json),
[earned long drop](../../../cream-depth-review/validation/earned-long.json),
[visual/loading review](../../../cream-depth-review/validation/VISUAL_REVIEW.md),
and [capture fixtures/limits](../../../cream-depth-review/validation/CAPTURE_NOTES.md).

Matched cases use seed 0xB4A7 and generated Cream seed 4030825150, with fresh
private cores for each frozen renderer survey and each ordinary live case.
Ordinary load requests and actor navigation/facing are disclosed fixtures.
Health, inventory/equipment, enemies, gates, progression, terrain, palette,
VRAM, framebuffer and player action/height are not assigned in those matched
and isolated cores. The earned four-row proof uses the established progression
harness, which discloses standing/height normalization at navigation waypoints.
It traverses cells 3→8→13→18→23 and lands supported at the real shadow anchor
(448,286). Its fixture scope differs from the matched art survey.

Composition adds room-loading frames: the tested one-row drop takes 70
physical frames versus the control's 64, six extra VBlanks (about 0.10s).
Its 46 fall simulation ticks remain unchanged, as do the local fall's 32 ticks
and matched climb input counts of 135/119/151. No composition runs in the
active frame loop. Frozen room mosaics demonstrate composition, while ordinary input and arrival checks
establish motion/cue agreement. These finite samples cannot establish every
visual join in all procedural seeds.
