# Regional content planning and placement

The Forest and Curdled Cream keep their existing mission graphs, required
trials, entrances and bosses. `regional_content.c` deals the restored content
onto ordinary rooms, with actual physical entrances and field interaction
anchors. Runtime event dispatch and mechanism stamping are separate modules.

## Seed plan and stable site identities

The two regions contain 50 field sites, IDs 32–81. Each region's 23 rooms other
than entry and boss receive one optional interior site: IDs 82–127. Existing
site IDs, base save layouts and the original Forest mystery-room packing are
not reused. A seed-based permutation distributes 18 event classes, 12 mechanism
patterns, 3 traversal patterns and 13 extra basic events across those 46 rooms.
The unique Learn/Recall pair is in separate rooms.

One side quest is selected from all seven kinds per run. Six kinds rotate
between the Forest and Cream across seeds. Cream givers use an entry-reachable
lower terrace with no capability requirement; the initial area choice is
latched in the extension save so later entitlement changes cannot move it.
Forest givers use an immutable entry flood without tool, small-key or earned
trial assumptions. A stage-zero label alone is insufficient: an unopened
small-key door can still divide that stage.

The block quest remains in the Forest. Broad glades and arenas are preferred,
but an actual base-room build must admit its 7×7 board, giver, entrance and
cache together before that room is selected. Failed candidates are skipped.
The transactional probe uses the existing preview room buffer, canonical
initial room flags and fresh discovery, and restores the live room, spots,
RNG, marks, fine collision masks, path masks and regional reservations. It
does not render or alter a required room feature. Green and
blue fusers live in the Forest, red in Cream. Blue's generated entrance is a
real secret-pocket door; changing its event assignment swaps the previous
decoration elsewhere rather than dropping a mechanism or memory opportunity.
Each region also has an escalating field-wave host. Field roles are exclusive,
so quest, wave, fusion and mechanism completions cannot alias one save bit.
Forest wave hosts exclude original item trials and the Hunt, Fetch and Torch
givers; an optional endless wave cannot prevent those original quests.

One third of seeds have a portal trial with a separate pocket. Its ordinary
outer hatch stays sealed until that actual trial is completed. The other
seeds use Survival in that slot. The blue fusion pocket remains a separate
feature requiring its matching fusion, so neither route bypasses the other.

## Actual geometry and stable map markers

Room-load placement uses one fixed canonical dry component. Cream's planned
terrace is explicit; arrival direction cannot move a feature to another shelf.
NPCs, entrances, future chain caches and optional mechanism footprints stay
clear of original landmarks, their interaction fronts, ledge lips and actual
directed arrivals. Compact nonblocking hatches provide a fallback when a
large arch does not fit. Only admitted coordinates enter the 500-byte discovery
array used by regional maps and the extension save. Previously discovered
anchors are preferred on revisits.

`regional_content_get` is deterministic planning. `regional_content_marks`
returns room-level planned labels while its output structure contains only
actual discovered coordinates. It does not invent unvisited zoom-map anchors.
Claimed fusers and completed quest marks are filtered using real saved facts.

## Coherent optional clearings

A field board uses a 7×7 footprint: the certified 5×5 puzzle plus a permanent dry
walking ring. Compact traversal features use 6×5; the red fusion's island uses
5×5. Large optional footprints are reserved before small incidental markers.
When plain space is insufficient, a bounded clearing may remove only ordinary
grass and canopy from the current connected field. It preserves existing
landmarks, gates, hazards, ledges and item pockets. A candidate touching any
previously disconnected dry component is rejected, including diagonal contact.
Existing floor and road artwork is retained; new grass uses the same native
area floor family. Forest tree ownership is rebuilt after clearing.

Mechanisms keep an outer dry ring. After stamping, the route validator checks
that every originally reachable tile outside the optional footprints still
belongs to the component, along with actual new door/NPC/cache approaches.
The stamp owner must reject or roll back a feature if this check fails.
Rejected stamps also remove the corresponding live and discovered mechanism
marker; a planned rectangle alone cannot claim a visible completed feature.
Original enemy spots are retained when safe; replacements keep their original
terrace, avoid all added reservations and prefer 3×3 dry standing clearance.

Objective selection computes both regional reach masks once per pass. Forest
reach uses unopened-key costs and real earned trial facts; Cream uses directed
edges, the live token mask and the plan's exact terrace. This avoids dozens
of repeated graph searches while a contract chooses its next objective.

The regional plan itself is not evidence of visible or usable content. Host
placement sweeps and real mGBA field/interior interactions qualify the final
implementation separately.
