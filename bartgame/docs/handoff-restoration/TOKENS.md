# Unified runtime requirements and hidden-content placement

`world_tokens.c` queries real facts without spending or inventing them. A
10-byte `WorldTokenNeed` can require original inventory bits, an appended item,
a counted number of small keys, regular/golden fusion completion, live or
latched switch bits, a solved annex puzzle, and the Forest/Cream boss outcomes.
These are conjunctions: all requested facts must be present. Empty queries are
explicitly initialized with absent-site sentinels. Gate handlers remain
responsible for consuming a key or opening/persisting a barrier after success.

The actual Cream runtime uses the same query adapter for its three mandatory
capability phases. The last capability requires both the Petal Cloak and Pacci;
Forest cloak ownership alone cannot bypass that seal. The Traversal Court's
red-fusion bridge/cache also uses a real requirement query. The mandatory graph
solver still operates on its deliberately compact three-capability state space;
it does not pretend that every optional meta fact has been incorporated into
a gigantic global solver.

Hidden scavenger content is authored into actual removable ground. The shared
finder tests cuttable/liftable vegetation, dig soil/walls or bombable cracks,
then floods the real current room from an explicit safe start and checks a dry
approach. Water, ice, lava, sinking ground and crumbling floor cannot become a
mandatory hidden-prize approach. Ring search is deterministic, bounded to eight
rings, and leaves output untouched when no valid site exists. The scavenger
quest stores the found coordinates and uses them for actual tool, tile-clear,
draw and reward behavior. It falls back to a visible chase item if placement
fails; a sprite over arbitrary empty floor is not treated as hidden content.

No persistent scratch allocation is added. Flood scratch is automatic and used
only when constructing/querying a feature. `tools/world_tokens_host.py` compiles
the actual C query/finder with production field types and explicit engine
adapters. Its2,184 checks cover all inherited Cream capability combinations,
conjoined inventory/key/fusion/switch/puzzle/boss facts, non-consumption of keys,
invalid requests, reachable/removable predicates, blocked components, hazard
rings, bounded fallback and1,000 deterministic placement samples. Native
scavenger/route input evidence remains a separate integrated test.
