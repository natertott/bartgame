# Repeated trees: procedural integration review

Status: implementation review in progress. The user approved the twelve-tree
kit and requested implementation plus complete room renders. This supersedes
the earlier diagnostic-only scope in `TREE_GUIDE_APPLICATION.md`; the approved
paintings remain unchanged. Numerical results and final visual observations
will be recorded here after the frozen build and real mGBA captures exist.

## Source and interpretation

The twelve approved drawings are produced by `art/forest_tree_study.py`:
two broad 32×32 forms and two narrow 16×32 forms, each healthy, sick and dead.
All share one native RGB555 bank, transparent index zero and ground anchor
`(width/2, 30)`. Their source canvas is not a floor-colored rectangle.

The source guide is the user's fourteen-page `GBA_Sprite_Art_Guide.pdf`, SHA256
`bc5400b675d76d7088f9b59f6a11feb04292c5c01ed34ce7cedece84b33fb4e1`.
Its advice is documented with page references in `TREE_GUIDE_APPLICATION.md`:
connected value masses before texture (pp.5,12), local contact over the actual
floor (pp.6,10), structural state changes beyond hue (p.7), separate visible
bounds and collision (p.8), and ground contact sorting (p.9). These are design
references, not instructions in the attachment that override the user's task.
No new commercial-game measurements or external play testing are claimed.

## Engineering decision and tradeoff

The integration preserves the maze's generated forest boundary rather than
clearing all formerly solid forest into an open field. Each retained logical
forest base is dressed by a repeated tree: a broad tree consumes two adjacent
16px base cells and a narrow tree consumes one. The lower sixteen source rows
are on a separate world layer, with the upper sixteen rows on the foreground
layer. Both are exact portions of the approved painting; neither is stretched.

Dense boundary trees preserve the full original base cells: 32×16 for a broad
tree and 16×16 for a narrow tree. Authored standalone trees retain their
original per-quarter root masks, often only the lower 8px, while their former
upper picture cells become real floor. This is deliberately wider than the
compact roots of the earlier grove diagnostic. It preserves continuous forest
walls around item-gated pockets and the room perimeter. It is not pixel-perfect
root collision, nor is the entire 32px image height solid. Transparent gaps
beside a trunk can therefore be non-walkable; this needs visual inspection and
honest disclosure. Native fidelity alone does not establish that this
footprint feels clear in motion.

Unconditionally clearing the old mask would create a different serious bug:
optional bomb/candle/cape pockets rely on their solid flanks and back wall, and
the room boundary must remain a cutset around each progression gate. A sparse
decorative grove over the old full-height collision would instead conceal
large invisible walls. The integration is reviewed against both risks.

## Independent evidence required

`tools/forest_trees_audit.py` independently decodes native 4bpp tile entries and
hardware flips from the frozen ROM, compares all twelve drawings and their
shared palette with the approved painter, and compares resolved Drain,
mystery-room, Bloom, equipment, bestiary and interface art with profile30.
Pointers may relocate; their resolved art payloads must remain exact.

The spatial corpus executes the actual C room generator, room collision code
and tree implementation using metadata read from that same ROM. Only video
submission is suppressed. It checks all 25 rooms across a spread of seeds,
required fixture and enemy approaches, all eight progression-item combinations
at room boundary cutsets, correct/wrong-item access to optional pockets,
deterministic rebuilds, and a smaller corpus using Bloom's implemented 10×8
feet box. The latter also regenerates rooms after perimeter gates and optional
pockets have been opened. These are host logic checks, not screenshots or
mGBA playthroughs. World/progression and room-generation source are compared
with the previous build; unchanged maze code does not warrant repeating its
older enormous graph-only corpus.

Real mGBA evidence must retain untouched 240×160 viewports. A full 512×384 room
image is a camera mosaic, explicitly labelled as such. Each output rectangle
must be copied exactly from a declared native viewport crop, with complete
coverage, no filtered resizing, and no copied/repositioned HUD or actor. A
normal HUD view and ordinary movement/overlap evidence remain separate from
the world-only camera capture. Animation time and viewport culling can make
seams differ; any such limitation must be stated rather than repainted.

## Visual observations

The healthy, mixed and deep pilot rooms and all three normal HUD viewports
were independently inspected at native size. Repeated raised leafy crowns
read as a coherent forest; mixed/deep rooms keep recognizable damaged forks,
some surviving crowns and attached violet rather than opaque purple backing.
Actual grass shows through the negative space around the trees. Bloom's red
petals remain easy to find, and floors, paths, water and gold interactions
keep their existing hierarchy.

Dead-tree regions reveal more floor between the compact roots while the
forest boundary remains physically solid. In these rooms the gaps occur
inside a dense, continuous forest mass; they are not open clearings that lead
to an invisible wall. This is still a readability tradeoff for later play
feedback. A few upper half-cells are omitted near protected fixtures and
their approaches: 11 healthy, 9 mixed and 6 deep in the pilot scenes. That can
make a local tree read as a stump, but keeps the portal/chest/NPC approach
visible. It is recorded rather than passed off as an unmodified full-tree
stamp in every location.

The camera mosaic holds world actor positions. It does not reproduce one
instantaneous 512×384 hardware display. Ambient glitter has viewport culling
and per-view limits, so some overlap pixels legitimately differ; the capture
manifest reports them and the audit does not smooth them away.

## Results

Pending the integrated frozen build, spatial corpus and visual review.
