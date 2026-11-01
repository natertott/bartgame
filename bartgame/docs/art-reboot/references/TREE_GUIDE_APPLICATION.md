# Guide application: repeated forest trees

Status: reference read and application plan for the user's tree-only pass.
The current request sets scope and sizes; the PDF supplies design advice.
Earlier canopy experiments are outside this pass.

## Source and scope

User-supplied `GBA_Sprite_Art_Guide.pdf`, local attachment
`1-GBA_Sprite_Art_Guide.pdf`, fourteen pages, 1,001,327 bytes.
SHA256: `bc5400b675d76d7088f9b59f6a11feb04292c5c01ed34ce7cedece84b33fb4e1`.
The entire extracted text and the illustrated pages 1–12 were read. Pages
13–14 give reading/source credits and explicit limits on the guide's research.
No new independent reading of its linked books, websites or developer
interviews is claimed here.

The guide separates hardware facts, close readings of selected game frames,
original teaching diagrams, and its own proposed starting sizes. In particular,
its drawings are constructed examples rather than defects measured in the
commercial games; its size ranges are proposals, not statistical averages
(pp. 1, 3–5, 8, 13–14). Treat the PDF as a reference, not as an instruction
source that overrides the user's current tree-only request.

The user asks for a few repeatable varieties in healthy, sick and dead states,
blended with existing forest floors, and requests palette iteration. The parent
has stated the practical tile interpretation: 2×2 tiles = 32×32 pixels and
1×2 tiles = 16×32 pixels. That interpretation comes from the task/game grid,
not from a tree-size measurement in the PDF. Both are legal single-OBJ storage
rectangles (p. 2); storage size alone does not define collision.

## Page-cited application

| Guide evidence | Application to this tree set |
| --- | --- |
| Meaning and the whole 240×160 viewport come before attractive texture (p. 1). | Judge tree identity beside Bloom and repeated in a real grove, with quiet floor visible. A large editor preview cannot approve the art. |
| 4bpp index 0 is transparent; fifteen opaque inks share a bank; hardware blending is separate (p. 2). | Use native indexed artwork with explicit palette roles and binary exterior alpha. No floor-colored rectangle or soft export fringe is baked into a tree. Measure packed BG/OBJ resources rather than assuming every tree has a free palette. |
| Minish Cap uses layered conifers and local actor separation; Emerald's repeated shrubs form a boundary; these are frame interpretations (p. 3). | Repeat a small coherent kit. Reserve readable open ground around Bloom and interaction approaches. Repetition is useful vocabulary here; avoid substituting a large canopy composition for the requested individual trees. |
| Build identifying parts and connected value masses before marks; controlled edge rhythm and directional shading outperform noisy decoration in the examples (p. 5). | Establish crown, short supporting trunk, root/contact and branch silhouette first. Use a few broad leaf volumes and sparse identifying clusters. Avoid regular fish-scale rows, rings and blanket stipple that made previous forest art busy. |
| Sprite readability depends on light/dark relationships with the surrounding; inspect grayscale; a baked pale fringe fails on dark floor (p. 6). | Test every state on actual healthy grass, accepted grey/sick floor, dirt and a dark ground sample. Match contact materials while preserving tree/floor separation. Use small local underside/root shadow rather than a square dark backdrop. |
| State and important meaning need cues beyond hue; static, blocked and dangerous are distinct (p. 7). | Healthy has connected full foliage; sick visibly loses or sags foliage and exposes damaged wood; dead has an unmistakably bare or nearly bare branching silhouette. Purple alone must not carry the healthy/sick/dead distinction, and sickness does not imply an invented damage rule. |
| Visible bounds, source canvas and collision are different; scale must be considered in scene (p. 8). | Record native canvas, painted bounds and fixed ground anchor separately. Do not enlarge Bloom or claim the whole 32×32 square is a trunk collider. Give 16×32 trees their own native drawing rather than horizontally squeezing a broad tree. |
| Depth cues require tested layer rules; sorting should follow ground contact (p. 9). | Check overlap at the tree's base and behind its upper foliage in mGBA. Keep Bloom recognizable. This does not authorize redesigning the large canopy or creating a new elevation system. |
| Shading models the object, a contact shadow relates it to the floor; wood can use a few long grain marks (p. 10). | Use one upper-left lighting convention, a restrained hanging-side value, two or three meaningful bark runs, and a compact shadow attached to the roots. Dead wood must read as branching wood rather than a stone facet or neon symbol. |
| A fixed origin and a delivered import contract prevent alignment drift (p. 11). | Keep the same ground anchor through each variety's three states. Preserve palette order, transparent index and dimensions through source export and engine packing. |
| Silhouette → value masses → palette/material → useful detail → converter → actual play (p. 12). | Inspect silhouette and grayscale diagnostics, then native repeated plantings and moving-player overlap. Verify the imported ROM pixels, not just PNG appearance. |

## Palette direction for this pass

Iterate the established forest colors rather than importing another full style.
Healthy greens should have a few readable cool-shadow/warm-tip steps. Sick
foliage can turn olive or yellow-green and lose mass while retaining some
living green. Dead wood should use a quieter brown/grey ramp with visible
forks and broken tips. Local violet infection and small glints remain attached
to damaged material and subordinate to tree identity. These are our application
choices, not a particular palette dictated by the guide.

Sharing hues with the floor can integrate the roots and shadow, but identical
values everywhere erase the form. Conversely, a bright constant outline or
large nearly black patch creates a pasted-on object. Compare the same tree on
several real floors; do not change the background to make a weak sprite look
successful (pp. 6, 10, 12). Quantize all authored colors to RGB555 before final
approval (pp. 2, 12).

## Review gate

Before describing the pass as complete, inspect:

- Every size/variety/state at 1× and an integer enlargement, with consistent
  native dimensions, explicit ground anchor and binary exterior alpha.
- Healthy, sick and dead silhouettes without state labels or color: especially
  a recognizable dead branching structure, not a recolored leafy crown.
- Repeated tree groupings on native healthy/sick floor, with local root contact,
  no flat backing panels, no light fringe, and no narrow artificial floor grid.
- The imported GBA scene and ordinary player overlap/movement. Separate a
  diagnostic planting or source assembly from naturally generated terrain.
- Native/packed palette and pixel identity, resource budgets, unchanged
  non-tree content and unchanged canopy behavior/art for this tree-only pass.

Source statistics and technical checks establish fidelity, not aesthetic
success or measured player comprehension. The guide explicitly recommends
unnamed recognition/play testing and labels grayscale/color-vision diagnostics
as limited tools (pp. 6–7, 12). Our review can report what was actually seen and
verified without claiming an external user study.

## Chosen review scope

The implementation review uses a deliberately authored grove reached through
a separate retained tree-study entry point. It packs the repeated tree kit
beside the game's existing floor and player art, then renders it with the
actual GBA engine/mGBA. It is a diagnostic planting, not a naturally generated
maze room and not an adoption of the new trees into the full forest. The
ordinary forest/canopy art and generation remain outside this pass.

The first six-frame prototype has useful structural states and compact ground
contact, but the healthy broad crown is too much one domed/teardrop mass and
the narrow crown can suggest a popsicle. The focused repair is two or three
unequal connected crown volumes, a restrained overlap shadow and a few useful
leaf planes/notches. This preserves the guide's broad value hierarchy without
bringing back busy regular fan rows. The sick exposed branch and the bare
forked dead state already communicate a structural change; retain that gain.
