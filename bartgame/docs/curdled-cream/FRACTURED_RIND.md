# Fractured Rind: optional Cream synthesis6

Status: exploratory local synthesis from the user's latest review, not an
adopted default. Build with `make -C bartgame BART_CREAM=6`; production0 and
studies1–5 remain selectable. The
[review gallery](../../../cream-depth-review/README.md) distinguishes source
drawings, frozen registered room surveys and ordinary live mGBA footage.

## User direction and material choices

The user selected study2's visual contrast and arch idea, study3/5's wall
textures, and particularly study5's colors. They rejected repetitive small
motifs, unclear blocked/drop borders and missing landing depth. This pass
retains study5's exact eight RGB555 banks and quiet pale ground. It combines
broader mineral planes, irregular grime seams, uneven strata and occasional
large closed architectural reliefs. The actual cave uses study2's pointed
construction in study5's palette roles, with an uneven broken crown.

Healthy stone has mostly dormant stress seams. Sour stone loses chips and
develops wider bruised cracks. Deep stone exposes branching violet cores and
small attached glints. The same underlying masses remain recognizable;
corruption changes the stone's structure as well as its color. Ground remains
subordinate to actors, interactables and navigation.

## Compose after generating the room

`art/cream_depth_walls.py` authors seven unequal native compositions:

| Family | Native size | Purpose |
| --- | --- | --- |
| Two shelf/fold faces |64×32 | Large unequal overhangs, broad lit planes and damp seams. |
| Two fractured spans |96×32 | Long connected stress fractures and asymmetric ribs. |
| One blind arch |64×48 | Closed rock relief, with a legible continuous backing. |
| Two compact remnants |32×32 | Narrow leftover rock that cannot fit a full span. |

These are drawings at their final coordinates, cut into16×16 cells after
composition. They are not enlarged tiny tiles or downsampled illustrations.
The quieter filler supports the large forms without adding a small repeated
arch, crack or fan to every cell.

`src/cream_visuals.c` measures actual unused midface after semantic routes and
room content have been drawn. A full panel must fit the measured rectangle;
it is not clipped around a cave, waterfall, climb strip, gate or prop. The
deterministic seeded choice mixes unequal96/64px spans and compact32px
remnants according to available space, leaves quiet breaks, and permits at most one complete blind arch in
a room when space allows. A blind arch is decorative sealed stone. Only real
entrances receive the open cave mouth and accessible approach.

This refines picture placement rather than regenerating the maze. Each
replacement is rejected unless its terrain type, collision and property flags
match the existing cell. Physical room geometry, directed route graph,
climbing behavior, enemy/content placement and gate requirements remain under
their existing authorities. The optional compositor is not a per-frame effect;
the room receives its wall composition during construction and its edge/cue
refresh after a gate changes.

## Edges, height and destination shading

`art/cream_depth_edges.py` separates raised blocked mass from the low open drop
sill. Neighbor-aware side returns join the blocked span; actual drop intervals
have endcaps. An open takeoff should not have a second impassable-looking curb
directly beneath it. Regular pale climb grips retain their exclusive meaning.

A dark seam at the bottom of the vertical face and a shallow textured floor
toe give the wall contact with its own ground. These structural shadows are
distinct from a drop's destination patch. Incoming directed drop edges use
`cream_room_arrival()` to obtain the actual target feet, including cross-room
and multi-screen routes. The original floor shading is a48×32 native master
split into six cells, with most visible shade concentrated near the top and a
broken shallow lower boundary. Quiet floor marks survive through it; no black
pit contour, bright target center or arrow is added.

The destination patch is applied only to compatible plain floor and path.
Path-specific drawings retain the pressed path grain beneath the shade;
hazards, gates and objects keep their own drawings. Routes behind clearable gates keep
their destination cue inactive until clearing. A cape-only gap can retain its
destination cue because acquiring the cape does not erase the physical pit.
Read-only cache telemetry records the arrival and painted portions so native testing can
compare the advertised landing with the real transition. It is not a second
source of gameplay coordinates.

Mount Crenel's viewed map helps establish plane hierarchy and the raised-rim
versus low-sill distinction. The destination cue is the user's requested
enhancement. The [reference note](CRENEL_REFERENCE.md) records exact inspected
URLs, image/crop digests, blocked sources, and observations versus inference.
No Nintendo pixels supply these original game paintings.

## Independent source-art critique

Actually viewed before final room qualification:
`/workspace/setup/cream-depth/source/source-atlas-3x.png` and
`/workspace/setup/cream-depth/edges/edge-source-4x.png`, with source drawings
enlarged by nearest neighbor. These observations are not claims about footage
that has not yet been examined.

- Unequal broad masses, longer fractures and one complete sealed arch are a
  substantial compositional improvement over the previous per-cell fans.
  Crack failure progresses across a recognizable material form. Solid/open
  edges differ in height and silhouette without relying on tiny arrows.
- Pale horizontal caps inside a wall can look like extra small walkable
  shelves. In the room, vertical face, contact and lack of an approach must
  keep these as material overhangs rather than promising a new platform.
- The closed arch has a solid backing and seated rock, but can still attract
  a player's attention as an entrance. Compare it beside actual caves at1×.
  Keep the real opening's negative space and approach stronger.
- Violet lighting is controlled rather than covering the ground. It may be
  less intense than the user's imagined deep corruption; judge connected
  glow against the whole dark face rather than brightening every crack.
- The revised landing master has a shallow asymmetric silhouette and floor
  grain. Its isolated atlas still cannot establish contact: a displaced dark
  shape could read as a puddle or separate slab. Native arrival and local
  cliff context are decisive, especially for distant drops.

## Qualification and protected scope

### Initial actual-renderer review

Viewed initial source `ed3e1480` under
`/workspace/setup/cream-depth/native`: all three style6 registered full-room
mosaics, matched study5 sour mosaic, and sampled 240×160 frames from the local
drop, one-row drop and sour-climb live GIFs. The mosaics are frozen camera
surveys; the sampled frames come from advancing ordinary input clips. This
review does not claim to establish the unviewed timing of every frame or an
unassisted playthrough.

The new wall masses are much calmer than study5's dense repeated little fans;
more of the room reads as walking field versus continuous vertical rock. The
complete blind arch reads as sealed relief beside the actual dark cave mouth.
Visible landing patches sit beneath the real actor at the sampled arrivals
and retain ground texture, reducing the isolated source-atlas puddle concern.

However, the initial placement still repeats the ivory near-vertical seam and
oval caps of `fracture_rib` at regular intervals along the upper band. The deep
veins make that recurrence especially visible. Larger art alone did not solve
the compositional rhythm: the planner needs mixed priorities and staggered
anchors rather than always fitting the same long span first. That revision is
pending a fresh source/build/capture, so these initial pictures and checks are
not substituted for final evidence.

The pale material overhangs also remain perceptually shelf-like while Bloom
falls past them. They are not physical intermediate platforms; actual final
arrival patches and the clear main terrace planes must carry that distinction.
This remains an honest visual tradeoff rather than a collision defect claimed
from still images.

### Final build inputs still required

The study adds native environment drawings and the optional compositor. It
reuses the selected study5 utility/object families, with the new pointed cave;
it is not a redraw of all actors or all shared handoff objects. Bloom,
enemies, NPCs, menus/HUD, original music and other regions retain their current
art. No high-resolution generated image, filtered scaling or screenshot color
grading becomes a game asset.

Before publication, fill these from the final frozen build:

- Source commit, build-option identity, ROM SHA256 and published download.
- Palette/subtile budget, asset audit, room/seed coverage and protected-art/
  production0/previous-study comparisons.
- Final healthy/sour/deep registered mosaics and matched before/after pair.
- Ordinary live climb, short-drop and multi-screen clips, with exact fixtures
  and input disclosures, plus final arrival/cue checks.
- Per-file media manifest and critique of the corrected planner in the final
  actual-renderer images.

The frozen room survey demonstrates renderer composition; live footage and
arrival checks establish movement/cue agreement. Neither finite evidence set
proves every possible procedural seed.
