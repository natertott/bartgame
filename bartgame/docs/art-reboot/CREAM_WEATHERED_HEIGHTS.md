# Weathered Curdstone: physical heights and graphical maps

Date: 2026-11-12. Profile: `BART_CREAM=12`.

The user selects Weathered Curdstone from polish #4, the carved Stone Steps /
Carved Ascent / Alternating Pins directions, and waterfall #2. They ask for
joined horizontal rock, clearly animated blue water, varied room geometry
and ten genuinely different graphical mountain maps. The initial pass adopts
those local material choices; the subsequent selection below adopts one map.

## Adopted pause map

The user subsequently selected **Contour Folio (#1) with Exploded Shelves
(#4) icons**. This is now the standard Cream map: #1's grid, inset and contour
zoom; #4's colored native event groups, two icons per room and extra-content
pips; and its climb/drop/cave legend. The room zoom already used those shared
colored markers. The title now names the region.

Normal builds enable profile12. The ten alternatives below describe the
historical review round. Current controls are D-pad to select, A to zoom,
B to return, R for items, Select for the standard menu and Start to resume.
L leaves the chosen map style unchanged.

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

## Final qualification

Frozen source: `f4b917f7964941d488c4d20fce073f3f58b950bc`. ROM SHA-256:
`a2e98b9551213c5335e826c59642fea5c03a4998746a811d5a9d464a96e24f86`.
The [actual gallery](../../../cream-heights-review/README.md) and its
[aggregate qualification](../../../cream-heights-review/validation/qualification.json)
record the exact finite test scope.

- 7,193 source/native checks pass. Cream uses 861 static native characters,
  163 available blended characters, ten palette banks and 6,356 free EWRAM bytes.
  Optional wall painting leaves 16 blend slots for later structural joins.
- 3,200 actual-C builds across 64 seeds pass content, support, ownership, gate,
  arrival, local-drop and refresh checks. All eight room families occur.
- Eight whole-room surveys, 20 charted native pause screens, fresh fog and
  actual menu/Forest-cache restoration pass. All map views share the same
  actual selected-room data and preserve gameplay state.
- Ordinary input clips verify carved climbs, local jumps, two- and four-screen
  drops. Four actual waterfall phases remain visible in each of three widths.
- A full earned run passes all three trial gifts, real barriers and Pacci,
  mounting and sword boss combat, then checks fresh-run reset.
- The 25-room timing comparison retains 1.000 updates per hardware frame in
  both builds. Room-load p95 changes 50→57 frames, including fades. Charted
  map redraws take 9–29 frames, initial 17; uncached Map-item reveals were
  not included in that timing sample.
- Production0 and prior Weathered10 rebuild byte for byte. The workspace
  remains restored to0; the review download explicitly enables12.

The last native review fixes preserve a truthful height key: shaft sentinel7
is never a floor. Shafts interpolate actual endpoints, and exploded diagrams
exclude shaft-only intermediate planes. A small dark native outline keeps
parchment text readable. Height summaries are recorded from actual loaded
rooms; paused style and zoom changes reuse one immutable selected-room plan.
Seed changes invalidate those summaries. Borrowed Forest caches invalidate
and recompute correctly after the Cream atlas closes.

Registered whole-room surveys assemble exact cropped renderer-camera frames.
Ordinary clips and menu screenshots use normal mGBA frames with disclosed seed,
loader and hero-navigation fixtures; game rewards, gate states and combat
outcomes are earned by real inputs. The gallery keeps these evidence types
and their limitations explicit.
