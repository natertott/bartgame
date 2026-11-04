# Forest room composition, profile 32

The current user asks for the generated forest to feel composed: water,
crossings, paths and debris should belong to one place rather than look like
independent stamps. This pass keeps the approved twelve tree paintings and
the five-by-five progression graph, but changes the local room plan and its
decoration. The earlier large canopy and random terrace proposals are not
reintroduced. This is an implementation under review until native captures
and independent room checks have passed.

## Landscape before dressing

The existing coarse connected clearings remain the starting volume. Profile32
does not add chunk-square lakes or the extra decorative path loop. Actual
two-cell door corridors are reserved before water fitting; their centerlines
lie between the earlier chunk centerlines, so testing the chunk paths alone
could incorrectly admit a stream running along an entry corridor.

A room receives a dry glade, brook crossing, closed pond, damp root hollow,
ruined edge or Heart-arena motif. Pond candidates are unequal ellipses with at
least thirteen cells and no reserved trail through their body. A brook is one
continuous band with a restrained lazy-S bend, a narrow two- or three-cell
body and one wider bank bulge. Candidate crossings must be perpendicular to
the route and have existing dry ground beyond both ends. When no safe water
candidate fits, the room retains its dry ecological context.

Near-parallel crossings share a primary deck. Short dry-bank connections join
their approaches before any furniture is placed. Real bank cells are reserved
from bushes, logs, quest censers and furniture fallbacks. Bridge and water
geometry are checked independently after final room generation; fitting
telemetry is not accepted as a substitute for those checks.

A stream's source/outlet continues visually below the first solid forest row
through its stored display substrate. The logical border tile, type and root
collision stay solid. Thus the channel disappears beneath the wood instead
of ending in a closed rectangular water stamp, without creating an exit or
an alternate way around a progression gate.

Old one-cell ledges are omitted from this generation pass. An eventual
terrace needs a deliberate upper shelf, continuous face and lower landing;
placing several isolated cliff columns is not an acceptable height cue.

## Ecological groups and route clues

Small groups belong to a bank, forest margin or coherent ruined edge. Bank
groups combine a stone, fern and occasional flower. Root groups combine a
log/stump or bush with fallen leaves and restrained plants. Bone details
belong to a boneyard context. The central travel ground remains quieter.
Background variation selects a broad patch, then uses a separate fine hash
to leave most cells plain; nine identical tuft tiles are not stamped as a
three-by-three texture block.

The final cosmetic trail pass connects selected gates, crossings and feature
approaches to one network. It changes ordinary floor pictures, not collision,
and preserves deliberately hidden lanes. The generator's local connectivity,
mandatory mouths, NPC/chest/relic/shrine approaches and item-locked pockets
retain their explicit safety passes. No mandatory reward is moved into an
optional pocket.

Lanterns are placed after features and route artwork are known. A lamp must
frame a crossing, adjoin a visible route or sit beside a real feature or
optional item gate. Sparse off-path lamps can point toward content without a
dirt trail. They never stand in arbitrary grass merely to fill empty space.

## Native material contact

Profile32 renders shore alpha on BG1 over actual local floor on BG2. Tree
crowns do not overwrite water cells. Shared path-side and concave-corner
aliases use the same soil geometry in healthy and sick banks. Six ordinary
decoration families likewise select a material palette from the actual
substrate, including when they occur beneath props or around water.

The legacy fence/stairs IDs predate prop metadata. Their transparent artwork
is explicitly layered above the real floor. Opened seals reveal local floor
instead of leaving a second opaque dirt stamp. New aliases are visual IDs;
logical interaction and collision metadata remain the authority.

## Determinism and review data

A relic's permanent dais reserves the same placement space before and after
collection. A temporary occupancy marker remains through all generation
passes, including monster-site selection, sickness, root arches and lamps;
the spent marker is removed before drawing. This keeps layout RNG and the
remembered road/light pattern stable without showing an unclaimed reward.

All new choices derive from the run seed and room index. The world graph,
three required task/reward gates and save-layout ABI are unchanged. Historical
profiles0–31 retain their old conditional branches. Room previews save and
restore `gForestCohesionInfo`, so inspecting another room on the map cannot
change the live room's motif caption or statistics.

`gForestCohesionInfo[16]` records version, motif, actual water/deck counts,
wet components, placed ecology groups/props/accents/lamps, visible trail,
ledge cells, water-fitting attempts, off-path feature lamps, arch, stage and
cell. These are descriptive diagnostics. Native RGB555 art, true geometry,
bridge landings, item gates and player visibility require separate evidence.

References remain the already-read uploaded GBA guide and tutorial notes in
the reference register. This implementation note claims no new external
reading or commercial-game measurement.
