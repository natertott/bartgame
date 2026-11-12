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
deterministic seeded choice tries larger96/64px spans before compact32px
remnants, leaves quiet breaks, and permits at most one complete blind arch in
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

The destination patch is applied only to compatible plain floor, leaving
paths, hazards, gates and objects intact. Routes behind clearable gates keep
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

The study adds native environment drawings and the optional compositor. It
reuses the selected study5 utility/object families, with the new pointed cave;
it is not a redraw of all actors or all shared handoff objects. Bloom,
enemies, NPCs, menus/HUD, original music and other regions retain their current
art. No high-resolution generated image, filtered scaling or screenshot color
grading becomes a game asset.

TBD — final source commit, build-option identity, ROM SHA256, palette/subtile
budget, audit counts, room/seed coverage and protected-art/default comparison.

TBD — links to final healthy/sour/deep registered mosaics, before/after pair,
ordinary live climb/short-drop/multi-screen clips, exact fixtures/input
disclosures, per-file media manifest and independent runtime critique. The
frozen room survey demonstrates renderer composition; live footage and
arrival checks establish movement/cue agreement. Neither finite evidence set
proves every possible procedural seed.
