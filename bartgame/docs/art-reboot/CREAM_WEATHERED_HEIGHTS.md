# Weathered Curdstone: physical heights and graphical maps

Date: 2026-11-12. Profile: `BART_CREAM=12`.

The user selects Weathered Curdstone from polish #4, the carved Stone Steps /
Carved Ascent / Alternating Pins directions, and waterfall #2. They ask for
joined horizontal rock, clearly animated blue water, varied room geometry
and ten genuinely different graphical mountain maps. This pass adopts those
local material choices. The ten map layouts remain review alternatives;
none has been selected as the final map.

## Scope and native construction

Earlier Cream profiles0–11 remain separate. This work changes the profile12
Cream material composer, local physical geometry and Cream pause map. It
does not replace Bloom, enemies, the selected HUD, other regions or their
palette families. The baseline Makefile default remains separately defined;
selecting this review profile requires `BART_CREAM=12`.

Artwork is drawn directly in indexed native pixels for 16×16 gameplay cells
and the 240×160 GBA viewport. Weathered Curdstone retains its complete
finished master silhouettes and the selected Rind material banks. A native
128×48 backing joins its left/right pixel columns exactly; broad unequal beds
continue across the repeat. Short shoulder/return planes replace tall bright
bars. Discrete master masks preserve the backing around a complete picture
instead of erasing it with a rectangle.

Climb designs6/7/8 are **Stone Steps, Carved Ascent, Alternating Pins**. Their
new masks retain opaque actual treads, cut-stone recesses, pegs and endpoint
joins while revealing the real rock outside the carving. Internal dark
shadows remain material, not transparency. Two columns still form one joined
climb. These masks do not create a climb where collision has none.

**Whitewater Ribbons**, the selected waterfall #2, keeps four authored blue
phases. One-, two- and three-cell sheets have complete outside banks rather
than repeating a bordered single-cell fall. Motion and brightness must be
checked on screen, not inferred from a phase count or offscreen VRAM update.
Falls remain decoration on eligible rock and do not replace a route or gate.

## Physical room variety

`src/cream_topology.c` adds room-local support, elevation, climbs and drops
inside the existing progression graph. It retains two macrocomponents per
room, which own item-gated routes and inter-room travel. A visual platform is
therefore real supported terrain with a recorded owner and height; it is not
an illusion painted over an unchanged flat room.

| Archetype | Local composition intent |
| --- | --- |
| Open Shelf | A broad, quieter room with few extra attachments |
| Folded Stair | Successive shelves that can chain several changes of level |
| Broken Mesa | Raised interior landforms with retained exterior circulation |
| Switchback | Staggered compact shelves, climbs and changes of direction |
| High Grotto | Upper-owned platforms and rear perches using available rock |
| Narrow Spurs | Smaller attached ledges and tighter standing spaces |
| Double Ridge | More than one raised mass with useful intervening floor |
| Peak Arena | A protected boss fighting space at the actual summit cell |

Seeds select the family and measured free space determines which complete
platforms fit. Names describe a generation preference, not a promise that
every room will contain the maximum number of ledges. Baseline floor is
height0; raised local surfaces can reach heights1–6. Height7 is a routing
sentinel for the unchanged macro climb, not an extra floor. Climb drawings
may interpolate between actual endpoints for a projection, but must never
turn that sentinel into a seventh walkable terrace.

The composer reserves actual route shafts, incoming supported arrivals,
feature standing approaches and the macro gate. Local climbs connect only
same-owner floors and cannot silently link the two progression components.
Paired lateral boundary routes remain aligned. New drop takeoffs record
their real supported destination; projecting sills and connected landing
shade must follow that information. The original multiroom drop graph and
required gates are preserved. Feature/spawn placement follows final physical
platforms and available standing footprints.

These are code/design contracts requiring the final generation and live
traversal audit. The eight names alone do not prove solvability, gameplay
quality, content access or visual diversity.

## Ten map concepts in the actual pause menu

Every design renders native game pixels from the same map-data interface.
The current room can use its live synchronized topology and material state;
known noncurrent rooms use the deterministic pure core/topology preview,
including relocated core feature positions. The preview is geometry data,
not an artist-invented map or a substitute screenshot. Fine decorative rock,
all prop silhouettes and every runtime material overlay are not the purpose
of this navigational representation.

| # | Runtime name | Overview / room treatment |
| --- | --- | --- |
| 1 | Contour Folio | Survey-style geographic grid and a top-down contour plan |
| 2 | Curdstone Diorama | Isometric regional blocks and projected actual terrain |
| 3 | Geological Section | Room height stacks and a labelled north/south physical slice with its plan cutline |
| 4 | Exploded Shelves | Occupied-level stacks and separated actual elevation footprints |
| 5 | Pilgrim Ribbon | Actual macro-route constellation and a plan paired with an elevation ribbon |
| 6 | Chamber Quilt | Raised room cards, event icons and height bars; generous relief plan |
| 7 | Surveyor Blueprint | Engineering route nodes and precise top-down contour linework |
| 8 | Stained Reliquary | Pointed glass room windows; gold leading at actual top-down height boundaries |
| 9 | Cairn Locator | Large focused room plan beside a regional locator and stacked height key |
| 10 | Plan & Escarpment | Raised geographic grid; selected-room plan aligned with a ridge-height envelope |

These alternatives change geometry, projection and information hierarchy,
not only frame or palette. Readable chest, folk, healing heart, broken boss
heart, cave, mission, climb, drop, mechanism and player symbols share native
pixel vocabulary. A capability obstruction uses a barred mark; it must not
advertise a small key for a Bomb/Lamp/Cape requirement.

### Controls

From the Cream pause map:

| Input | Action |
| --- | --- |
| D-pad in overview | Select a room in the 5×5 geographic grid |
| L | Next map concept |
| Select | Previous map concept |
| A in overview | Zoom the selected room |
| B in zoom | Return to overview with the same selected room |
| B in overview | Return from the map |
| R | Open the item page |
| Start | Close the pause menu |

Item-page A/B/L equipment bindings retain their existing context. Map cycling
does not change a run’s terrain, inventory or progression.

### Truth, fog and diagram limitations

- **Knowledge is existing game state.** A visited room or owned Map can make
  geometry known under the current policy. Unknown rooms do not expose their
  real floor plan, content coordinates or route endpoints. Current player
  position and selected-room cursor remain separate.
- **Content is stateful.** Collected chests/caches, spent heals, earned mission
  rewards and a defeated boss follow progress rather than remaining fake
  outstanding objectives. Core and regional markers use actual coordinates.
- **Links are real graph edges.** The overview may combine a room’s two
  macrocomponents for a compact diagram, but a pictured line must originate
  in an actual route. Directional drops and cave folds are not generic
  bidirectional adjacency. Known endpoints are required.
- **A section is a slice.** Geological Section selects and marks a real
  north/south cut column. It cannot show every event or lateral route outside
  that slice. Use its inset plan or another map to interpret off-slice space.
- **An exploded view separates elevation for reading.** Diagram gaps between
  floors are neither pits nor climbable passages. Actual footprints remain
  level-specific; higher planes do not establish connectivity by overlap.
- **A profile is a summary.** Plan & Escarpment’s RIDGE PROFILE uses the
  maximum actual walkable height in each room column. This envelope is not a
  continuous side-view route. Overview stacks and ribbons likewise summarize
  real height ranges, not a guaranteed sequence of steps.
- **A projection can hide detail.** Isometric overlap, small overview cards,
  clustered 9px markers and shared high-level shades have native-resolution
  limits. Numeric height keys, cutlines, plan context and zoom are part of
  interpretation. A plus/multiple-content mark means inspect the room view.

Pure preview and drawing must leave the live room maps, topology, world
graph, progress, actors and player unchanged. Closing or changing map pages
must restore borrowed graphics memory, palettes and the existing UI. Those
invariants need both source inspection and actual state comparisons.

## Source and rationale

This is original art and layout guided by the user’s current choices and the
already-read [tutorial application matrix](REFERENCE_APPLICATION.md),
[GBA menu source study](references/GBA_MENU_RESEARCH.md) and
[viewed Mount Crenel note](../curdled-cream/CRENEL_REFERENCE.md). Material
clusters, quiet playable fields, controlled edges and truthful shadows guide
the room; stable focus, zoom continuity and layered knowledge guide the map.
No new external research, review quotation, source-game animation measurement
or imported commercial pixels are claimed.

Principal sources are `art/cream_dynamic_art.py`, `art/cream_studies.py`,
the profile12 asset dispatcher, `src/cream_topology.*`, `src/cream_room.c`,
`src/cream_runtime.c`, `src/cream_map_concepts.*`,
`src/cream_map_forms_a.c`, `src/cream_map_forms_b.c` and the existing menu
restoration/input hooks. Profile-specific audit and capture tools accompany
the implementation. This documentation does not report their results before
the final source is frozen.

## Pending final verification

At this documentation handoff, **final source commit, ROM hash, final asset
budgets, generation counts and independent runtime results are pending**.
Earlier profile7–11 evidence is historical and cannot qualify profile12.
Host source mockups are labelled synthetic fixtures; they are not mGBA runs.

The final record should bind one source/build to:

1. Native palette/character budgets and protected-region comparisons.
2. Seeded room/graph audits for real support, same-owner local climbs,
   required gates, paired lateral routes, useful dead ends, content approaches
   and protected summit space, with finite scope reported.
3. Ordinary mGBA climbing and local/multiroom drops across varied rooms;
   visible animated one-, two- and three-cell blue falls; joined wall art and
   correct ledge/landing shading at native size.
4. All ten actual-game overview/zoom pairs, early fog state, complete map
   input navigation and unchanged live-state snapshots across previews.
5. Menu/room restoration, positive player health, timing/performance checks
   appropriate to the added room construction and honest remaining risks.

Registered whole-room surveys, a single live 240×160 viewport, movement clips
and source sheets must retain distinct labels and pinned provenance.
