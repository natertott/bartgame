# Repeated trees: procedural integration review

Status: adopted and independently reviewed in profile 31, the production
default. The user approved the twelve-tree kit and requested implementation
plus complete room renders. This supersedes the earlier diagnostic-only scope
in `TREE_GUIDE_APPLICATION.md`; the approved paintings remain unchanged.

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

The healthy, mixed and deep final rooms and all three normal HUD viewports
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
their approaches: 11 healthy, 9 mixed and 6 deep in the final scenes. That can
make a local tree read as a stump, but keeps the portal/chest/NPC approach
visible. It is recorded rather than passed off as an unmodified full-tree
stamp in every location.

The camera mosaic holds world actor positions. It does not reproduce one
instantaneous 512×384 hardware display. Ambient glitter has viewport culling
and per-view limits, so some overlap pixels legitimately differ; the capture
manifest reports them and the audit does not smooth them away.

## Results

Frozen game/art source: `fd7465d87f3dfcec33152254d49b3df629debf26`.
Production profile 31 ROM SHA256:
`977f38406e3f5cf12e7108e3840356d305d364bd665bc0d9ef578ec8f5937e78`.
The final independent audit passed **1,915/1,915** checks using held helper
SHA256 `901aad854d1dd8b18e2849d8233a8afd644a97a3626ac78beb9aa0ed84f770e8`.
The final capture helper separately passed 140/140 checks.

| Evidence | Result |
| --- | --- |
| Approved tree drawings | All 12 native index images, exact shared RGB555 palette, dimensions, ground anchors and state/variety descriptors preserved. All 384 new fast depth-sorting alpha rows match the source bit for bit. |
| Resource use | 646 resident BG tiles of 768 available with the extra layer; 11 world palette banks of 12. |
| Unrelated art | 1,532 non-tree forest metatiles preserve every resolved RGB555/transparent pixel and animation timing; 36 complete OBJ sheets, 19 interface/palette payloads, pre-existing global BG palettes except the adopted tree bank, and both other world tilesets stay exact. |
| Generation corpus | 512 seeds, each with all 25 rooms: 12,800 generated rooms. World/progression and room-generation source match profile 30. |
| Root/route checks | 6,807,405 base-cell ownership checks, 86,699 required approaches, 7,258 item-pocket cases and 108,800 boundary checks across the eight item combinations; zero failures. |
| Lifecycle checks | 12,800 deterministic rebuilds; 800 paused-map previews and 800 live bush-clear/redraw cache checks preserve resident trees. |
| Actual feet clearance | 1,600 room-state cases using Bloom's 10×8 feet box: 800 rooms before and after gates/pockets open. |
| Native render provenance | Three 512×384 camera mosaics, each from nine untouched 240×160 mGBA viewports. Every pixel has exactly one declared source crop; no interpolation, repainted seam, copied HUD or repositioned actor. |
| Movement | All 504 native walk frames independently match ROM Bloom poses, exact guard subsets, palette and paired scanout; minimum visible current-body pixels 90/94/95 in healthy/mixed/deep. Worst-overlap native frames were also inspected visually. |

The observed healthy/mixed/deep walks contain 1/1/0 intervals without a logic
update. These counts match the pinned profile 29 control for the same selected
rooms, standing positions and 168-frame directional sequences. The comparison
file is held by SHA256
`1ef84e4fc5df0cc32c74ce7e46852bc88818a6122006a7410432b64600405ce3`.
All native video frames remain in the evidence; none were dropped to make
motion appear smoother. The MP4s are viewing copies at approximately 59.73Hz;
sampled GIFs have inspection holds and do not reproduce original timing.
Different art and navigation phases limit this finite performance comparison.
It does not establish frame-perfect performance or universal gameplay safety.

The camera-overlap comparison reports 63/100/17 differing pixels in the three
rooms, associated with native viewport-dependent ambient glitter. The mosaics
retain literal crops; those differences are neither averaged nor erased.
These technical checks and the reviewed rooms establish import fidelity and
the tested geometry/visibility contracts. They are not an exhaustive playthrough,
an external player-recognition study or a claim that every future forest
generation is aesthetically successful.

Reviewable evidence:

- [Actual room gallery and playable build](../../../../art-review/forest-trees-integrated/README.md).
- [Final independent audit](../../../../art-review/forest-trees-integrated/validation/audit.json)
  and [actual C host corpus report](../../../../art-review/forest-trees-integrated/validation/host/report.json).
- [Capture manifest and native camera/scanout data](../../../../art-review/forest-trees-integrated/actual/capture.json).
- [Historical build byte-preservation](../../../../art-review/forest-trees-integrated/validation/legacy-preservation.json).
