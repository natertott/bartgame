# Exact actor-canvas rejection before terrain depth

The current actor painter first rejects hidden/hurt-blinking bodies, derives
the canvas origin, calculates terrain/tree depth and only then asks
`draw_sprite()` to reject a canvas outside240×160. Multiple enemies outside
the camera therefore trigger depth queries that can never produce OAM.

`actor_draw()` now applies the **same** `draw_sprite()` canvas predicate before
the pure depth calculation. It reads the sheet dimensions rather than the
smaller physical silhouette or padded actor dimensions. Touching the far
outside edge is rejected; one visible native pixel is retained. Hidden/blink
rules, animation presentation metadata, canvas origin, priority for submitted
actors, OAM order and capacity are unchanged. There is no AI culling, altered
enemy population, deferred update, RNG call or gameplay clock change.

The same pure queries are also skipped if all128 hardware OAM entries are
already occupied: the original allocator cannot submit an entry then either.
Production forest profiles11 and later explicitly implement
`player_recoil_priority()` as an identity. The generic body painter therefore
omits that external call in those profiles, while preserving it for6–10 where
the narrow recoil exception is real.

The Confessor's blade has its own rejection using its final independently
calculated16×16 canvas. Culling a body must not hide a blade which reaches
into the screen. The original north-facing body/blade ordering and conditional
vertical flip remain intact.

`tools/perf_actor_equivalence.py` extracts the actual baseline and candidate
C functions and compiles them against the unchanged OAM writer and the native
36-sheet descriptor metadata. A deterministic pure depth stub supplies equal
verdicts for equal arguments. All Actor bytes and all128 OAM entries must match.

The first differential run passes513,184 cases, covering every native canvas
at exact viewport edges, randomized actors/cameras, hidden/iframe states, full
OAM and both blade states/four directions. It contains846 submitted blades
whose owning body is outside view. The candidate avoids232,279 body and63,224
blade depth calls in this synthetic corpus. These counts describe equivalent
work avoided, **not** a frame-rate or typical-room performance claim.

Actual frame timing, real forest depth, gameplay and native framebuffer
equivalence are qualified separately by the parent performance review. This
change does not alter art, collision, attacks, resource use or room generation.
