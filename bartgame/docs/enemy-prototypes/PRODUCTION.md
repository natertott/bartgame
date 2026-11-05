# Three enemy families in ordinary rooms — 2026-11-05

The user explicitly selects the three preceding mechanic prototypes for the
main ROM. Gilt Leech, Root Maw and Reliquary Snout are now additional normal
forest/mystery-wave candidates; the five earlier selected families and split
purple Heart retain their existing paintings and mechanics. Historical
`EN_PROTO_ROPE/LEEVER/HELMASAUR` aliases remain IDs6/7/8 for capture-tool
compatibility. Their canonical aliases are `EN_GILT_LEECH`, `EN_ROOT_MAW` and
`EN_RELIQUARY_SNOUT`.

The complete existing32-pose, native16×16 strips are retained unchanged.
Numbers and deliberate translations from Rope/red Leever/Helmasaur remain in
[the proposal](PROPOSALS.md) and [source audit](SOURCE_AUDIT.md). This pass does
not import commercial artwork or adopt a new external visual reference.

## Where they appear

Healthy bug rooms introduce the Leech's clear locked lane most often. Root Maw
is more common in the blight/dead themes. Snout appears from stage1 in those
themes, and stage2 in healthy bug rooms, so the first uncomplicated healthy
encounters do not require learning front armor immediately. Coin Toad, Quill
Moth, Bellflower, Pear Bladder and Moth Confessor remain in the appropriate
weighted distributions. Existing mystery waves use the same selector. No
extra wave or required progression event is added.

Generated monster markers already belong to the reachable room component.
New ground bodies additionally validate their complete dry footprint, keeping
any rounding-edge adjustment within8px of that marker. Snout additionally
requires an open dry cross16px in each cardinal direction, reserving physical
space for its promised flanking counter. A marker that cannot
admit that body becomes the smaller existing Coin Toad rather than a missing
or corrupt sprite. It remains sword-solvable. Room geometry is never edited.

## Timing, damage and finite burrowing

Leech retains its30-update tell,1.625px/update committed charge and36-update
recovery. Snout retains its60-update brace,3px/update locked rush,30-update
recovery and90-degree front guard. Side/rear sword and arrow hits still deal2;
a front-directed explosion is still blocked. The existing Candle remains a
terrain tool, not an invented enemy-fire counter.

Maw retains90 initially buried,24 harmless emergence,180 exposed,24 hittable
harmless retreat and240 subsequent buried updates. Its normal relocation first
uses the same twelve candidates at least40px from Bloom with a sampled dry
straight approach. A real last-wave enemy must not remain hidden forever just
because that conservative test rejects a corner. After three failed relocation
rounds, production checks deterministic cardinal sites48/32/16px away, then
uses its original validated floor anchor. Every outcome still has the complete
24-update harmless warning. A player who camps that anchor can therefore see
emergence closer than the ordinary40px exclusion and must move away. The anchor uses four dedicated free actor bytes, not `vx/vy`, which the shared
movement system overwrites. Its validity therefore survives exposed motion and
real hit recoil across later burrow cycles. The old lab retains strict40px
admission to keep its earlier mechanic experiment reproducible.

The dry-ray sampler uses an exact rational incremental walk instead of two
software divisions per sample. The actual extracted C function matches the
old signed-C formula for1,050,625 vectors across dx/dy−512..512 and91,184,129
sample coordinates, including a zero-length ray. This changes work performed,
not candidate sites, random choices, timings or collision precision.

All living new actors count toward room completion, including buried Maw.
Their state vocabulary is checked separately from the older enemy-state enum;
this is explicit hardening, not a claim that the previous exposed phase was
miscounted. Dead ordinary bodies are actually freed through the usual kill path.

## Native memory and rendering

Loading all128 native tiles for each new family beside the old roster would
waste384 OBJ tiles. Normal play instead allocates **four hardware tiles per
living new body** and streams its actual128-byte frame only when a visible
submitted pose changes. The original32-frame source strip remains in ROM.
The actor's logical/presented pose is not changed by the streamed draw index0.

A384-byte EWRAM pool reuses released four-tile slots across actor indices and
later waves. Kill releases a slot; a room reset clears the pool. Defensive
ownership validation also recovers slots if a body is retired through the
ordinary actor-free path or a disclosed developer fixture. No ever-growing
frame cache is accumulated as enemies animate or waves change.

`enemies_flush_frames()` runs immediately after the ordinary upload queue at
VBlank. This separate bounded queue cannot silently lose body changes to the
ordinary16-entry text/player/effect queue. Offscreen, hidden and hurt-blink
bodies do not request uploads. Queue entries store the owning actor index,
exact native pose and destination; no scratch pixel redraw or reduced animation
is involved. Natural room density remains capped at its existing twelve spawn
markers. The optional lab preserves its resident full-strip allocation to keep
source-sheet counterprobes meaningful.

Discovery calls `journal_note_enemy(type)` only after an actual onscreen body
submission, including the boss. Remote generation does not by itself discover
the roster. Journal persistence/UI policy belongs to the companion cabinet
implementation.

## Evidence

The [production combat harness](../../tools/enemy_production_review.py) passes
75/75 checks against the9538580-byte pre-freeze production candidate, SHA256
`341b7926b9a5f79ad35a789adf4b5c321fd3b5b149e94d648b50025740c6be98`.
Eight scenarios cover2741 actual mGBA video frames and25923 exact native
ROM-to-VRAM frame comparisons. Maximum sampled world allocation is608 tiles,
below the876-tile HUD boundary.

Actual sword inputs verify Snout front clang/rear damage and Maw buried versus
exposed damage. The second Maw cycle proves the stored anchor survives real
exposed movement and sword recoil, then guarantees its later narrow-origin
fallback. A real required two-wave trial receives a disclosed eight-Maw roster
fixture, retains those living buried actors, proceeds only after actual
full-fuse bomb kills, reuses freed streamed tiles, and awards victory after
killing its final Maw. No enemy HP, state, timers, facing or flags are assigned
by the capture harness; coordinate-only bomb target placement is explicitly
identified as a damage-interface counterprobe.

The goal-room fixture retains its real Heart and adds the other eight actual
families; all nine coexist for240/240 sampled updates. Synthetic24-Leech and
24-Snout cases produce300/300 updates each. A synchronized24-Maw emergence
produces299/300, preserving one isolated repeated video frame at the transition.
That exceeds the normal twelve-marker room cap and is recorded as a finite
performance observation, not called full cadence. The stress criterion is at
least99% throughput with no consecutive repeated frames; all strict mechanic,
frame-fidelity, allocation and progression checks remain independent. Companion
natural-room coverage is recorded by the parent release rather than inferred
from this synthetic stress case.

The parent integration records the eventual committed-source bundle and
fresh final capture provenance. Source-art pose boards remain distinct from
actual mGBA gameplay frames.

Final committed source1527dd84c92f47bf5f498cbff35cdd179cad48af reproduces that
candidate ROM exactly. The fresh final75/75 run, actual recordings and precise
299/300 synthetic-Maw observation are linked from the
[production release](../../../arcade-journal-review/README.md). The release
also binds the untouched three native study strips to the old lab ROM and
preserves every earlier production sprite payload and identifier.
