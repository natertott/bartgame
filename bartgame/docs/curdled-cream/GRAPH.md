# The Curdled Cream: a directed terrace puzzle

The generated area has25 rooms on a5×5 map. Each room has two physical
components: a LOWER terrace and an UPPER terrace separated by a cliff.
The graph therefore has50 nodes, not25 room-center placeholders. Room art
must preserve this separation and implement the precise ports it receives.
The Blighted Forest's `World`, art and generator are untouched.

## Traversal vocabulary

- WALK joins equal terraces in horizontally adjacent cells.
- CLIMB ascends a local climbable face, or joins an upper terrace to the
  lower terrace in the cell directly above. A missing edge means a genuinely
  unscalable wall, not an invisible transition trigger.
- DROP reverses a local/one-row ascent as a one-way jump. A LONG_DROP edge
  instead joins an upper terrace to a lower terrace two, three or four
  complete map rows below, in the same column. Its landing component is
  explicit. These are not ordinary bidirectional maze corridors.
- CAVE pairs join separated cell/components. The required cave replaces a
  broken surface route; the old surface segments become content branches.
  A second cave pair, available after all capabilities, makes a long descent
  revisitable. Each component has at most one cave mouth.

North is up. Entry is on a seeded bottom-row lower terrace. The boss always
occupies a seeded top-row upper terrace, with a dedicated broad arena in the
room builder. All five top-row peak columns occur. Geometry and content
placement own the physical fighting floor and approach clearances.

## Mission and construction

1. Build a seeded tree over the50-component cliff grid using only local,
   lateral and adjacent-row connections.
2. Cut an entry-to-peak connection and reconnect its sides with a real
   multi-row downward jump. Its return cave initially requires all tools.
3. Graft a nonlocal cave onto the directed mission route, cutting the old
   surface route so the cave is meaningful. It cannot bypass the long jump.
4. Three route cuts divide the graph into four capability stages. The long
   descent is one cut and occurs before the last capability, preventing its
   late cave from bypassing the first required jump. Every edge crossing a
   stage boundary receives the corresponding capability requirements.
5. Put each mission reward inside its own earlier reachable stage. Prefer a
   short branch/detour rather than an on-route handout. All dead ends receive
   a chest, cache, healing, NPC, mission or boss purpose beyond an empty floor.
6. Check the actual directed graph/capability state space. Retry at most24
   candidate constructions; after that copy a solved ROM certificate and run
   the same validator. There is no unbounded fallback generation loop.

The capability bits are Bombs, Lamp, and Cape **plus Pacci**. The runtime maps
actual ownership to these bits; a Forest cape alone does not satisfy the last
proof. A player already carrying a tool may use it normally. Mission sites
still carry their content and grant missing capabilities. `cream_collect_tokens`
is the solver's abstraction of *completing* a reachable task, not permission to
award a prize merely because the player entered its room. The game should call
`cream_reward_bit(node)` only when that site's actual objective is completed.

## Solver guarantee

The400 possible states are `(terrace node, capability mask)`. Forward search
starts from each of the eight possible inherited inventories, collecting a
mission's reward when its prior capability requirements are satisfied.
Reverse search from the peak with all capabilities marks winning states.
Every reachable state must also be winning: an allowed one-way descent or cave
cannot strand the player away from a required missing capability. With full
capabilities, all50 physical components must be reachable.

`cream_solution()` returns a shortest legal capability-acquiring witness. Its
node list includes revisits, so required distance includes real detours and
backtracking. It returns the required output length; callers must supply that
many bytes before using the output. The generator admits18–52 crossing routes
in the current sweep, requiring9–22 distinct rooms, so a win never requires
visiting all25 cells.

This proves the graph, not a separate picture of the graph. The room builder
must flood its actual collision tiles from each landing to its promised
ports, cave fronts, climb stripes and mission sites, with the matching tools.
Enemy spawns counted by a room-clear objective must remain on the player's
current terrace component. A graph test alone cannot establish these physical
contracts or substitute for real mGBA traversal.

## Storage and API

`CreamWorld` is1392 bytes in EWRAM. It holds50 degrees, at most six four-byte
edges per component, stage/content arrays,25 corruption values and compact
route metrics. It consumes no global gameplay RNG and stores no complete tile
maps. Corruption is0 fresh,1 sick,2 deep; entry is0 and the peak is2.
Room images regenerate from the area seed; persistent visited/claimed/cleared
flags belong to the game's save extension, rather than this generated graph.

`cream_generate(seed)` and `cream_generate_certified(seed)` return validation
success. `cream_edge(node,index)` exposes the exact target, verb, capability
mask and LONG_DROP/LATE_SHORTCUT/MISSION_GATE flags. `cream_node`, `cream_cell`
and `cream_terrace` convert addresses without inventing room-center landings.
The maximum generation attempt count is24; the certificate is ROM data in
`cream_world_fallback.inc` and is independently exercised by the host tests.

## Measured host evidence

`tools/cream_graph_review.py` compiles the actual C generator and validator.
The100,000-seed final host run passes all checks, including byte determinism,
all five peak columns, all three multi-room drop spans and zero lost states.
The first1,000 graphs are also reconstructed and solved independently in Python
for all inherited inventories. The fixed certificate is independently checked
at six explicit seeds. No normal candidate fell back in this sweep; maximum
observed attempts were22 of24. The certificate remains a tested control rather
than an assumed unreachable code path.

Measured required crossings:18–52, mean33.84207. Required rooms:9–22,
mean18.27462. Sampled solutions contain8–23 climb edges. The sample's long-drop
span counts are89,190 two-row,10,205 three-row and605 four-row routes.
These are host measurements; actual ROM/room comparisons and native traversal
are separate release evidence.

```sh
source /workspace/setup/activate.sh
python3 tools/cream_graph_review.py \
  --out /path/to/cream-graph-review --seeds 100000 --independent 1000
```


## Final content and physical qualification

A dead end with a chest no longer advertises a second loose cache using the
same persistence/physical footprint. The fixed ROM certificate and validator
apply the same rule. This changes no RNG draw, graph route, objective or peak.

`tools/cream_room_batch_review.py` exercises100000complete actual-C roomsets
with the established8px collision adapter. The host caches each seed's25built
rooms only to avoid repeated builder/FFI overhead. It checks both dry terrace
components, every promised trigger/target landing, enemy spawn and content
front. The earlier256-seed independent Python geometry review additionally
checks preview purity and native gate restoration/persistence. Native mGBA
progression separately proves one full seeded route and the peak fight; it is
not labeled an unassisted playthrough or universal native proof.

## Independent generator equivalence

`tools/cream_world_twin.py` independently generates the same graph in Python.
It uses explicit unsigned 32-bit xorshift and mixing arithmetic, preserves
candidate/rejection and reservoir order, and serializes the record manually.
Expected generation never calls C or reads/parses its output or source. Its
capability validator independently enumerates canonical states and reverse
edges instead of reproducing C's incoming-node/mask-inversion algorithm.

The final comparison passes **1,000 generated seeds and six explicit certified
fallbacks**, comparing all **1,392 bytes** per record: **1,400,352 bytes** total.
This includes every edge slot, content/stage/corruption field, route metric,
attempt/fallback flag and zero padding byte. Seeds include 0, 1, `0xffffffff`,
the first-attempt zero-shape control, small sequential values and deterministic
full-width pseudorandom values. All five peak columns and all three long-drop
spans occur. No natural fallback occurs in these 1,000 cases, so the six
explicit fallback controls are reported separately.

The fixed certificate is reconstructed independently using its original
shape seed `0x4ce2a547` with content seed 0, followed by the requested run seed
and certified flags. The Python tool copies no graph literal from C. The
comparison adapter compiles the unchanged production C and reads its observed
record only after the Python expected record is complete. Before/after source
hashes prove that this verification does not change the runtime generator.

```sh
python3 tools/cream_world_twin.py \
  --out /path/to/cream-python-twin --seeds 1000
```

The result is host equivalence for these cases, not an exhaustive proof over
all 32-bit seeds or a substitute for the separately recorded native input tests.
