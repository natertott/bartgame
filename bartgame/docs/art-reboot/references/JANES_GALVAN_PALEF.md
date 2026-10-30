# Reference reading notes: Richard Janes, Alain Galvan and Thomas Palef

Read on 2026-10-30 from the user's uploaded PDFs. Page references below are **PDF pages**, including the browser-print headers/footers. Read all text and inspected the rasterized pages and their illustrations; these notes paraphrase the authors rather than reproduce their tutorials. The source manifest records actual filenames, SHA256 values and page counts.

## Source 1 — Richard Janes, Introduction to Pixelart (5 PDF pages)

Original upload: `Introduction to Pixel Art • Richard Janes.pdf`.
SHA256: `65b1d596e367d6e65f17c4b96d4826b398deb9ad4783795bdbffc0f5769f3219`.

### Explicit advice and observed examples

1. **Foundations before polish (p1).** Janes presents line work, colour, dithering and shading/anti-aliasing as interdependent fundamentals. Decorative detail cannot repair broken line work or form.
2. **Consistent straight-line pixel runs (pp1–2).** Horizontal, vertical, diagonal and regular one-/two-pixel step patterns look controlled. The page2 comparison marks uneven, wavering slopes as failures. The author acknowledges that nonuniform organic shapes cannot always use these regular lines.
3. **Clean curves manually (p2).** The circle/corner panel contrasts smooth progressive run lengths with kinked corners and protruding pixels. Rough shapes are an initial stage; the artist must refine their raster outline rather than accept an unexamined primitive or sketch.
4. **Hue and saturation matter to lighting (pp2–3).** Shadows move toward cooler hues; light-catching areas toward warmer hues. The author recommends passing through lower saturation/gray when moving between opposing warm/cool hues instead of arbitrarily mixing them.
5. **Distinct value steps (p3).** The seven-shade ramp in example1 has insufficient perceptual separation. Example2 improves separation but lacks hue/saturation variation. Example3 combines separation with hue/saturation changes. The author says most sprites need no more than roughly five shades for one colour/material, not five colours for the entire sprite.
6. **Dithering is optional economy and texture (p3).** The illustrated sequence blends a hard two-tone division with a 50:50 checker, then a 25:75/75:25 transition. It is useful when another colour is unnecessary or roughness is desired, not a requirement to texture every surface.
7. **Avoid pillow shading (p4).** The comparison distinguishes a shaped edge with locally fading anti-aliasing from multiple concentric bands following the outline. Surface shading must describe the object's volume and light direction, not just its distance from the silhouette.
8. **Shape-to-palette-to-volume workflow (pp4–5).** The pot sequence starts from cleaned flat line work and a restrained palette, then places a shadow under the lip, below the rounded body and on the side away from the front-left light; highlights occupy the upper lip and left body mass. The final example selectively colours the outline.
9. **Selective outlines and final iteration (p5).** Complete absolute-black outlines are usually replaced in the pot example by dark material colours, especially beside light edges. Black remains useful for genuine deep darks or a deliberate stylistic reason. Edges stay darker than their interior; outlining and limited hand AA should preserve clarity. The author explicitly revisits and tweaks the sprite multiple times.

### GBA application

- Inspect every gold outfall crown, pipe elbow, ladder arch and frog jaw at native size for accidental single-pixel kinks. Use deliberate pixel runs; asymmetry must describe damage or organic anatomy, not raster accidents.
- Create material ramps with clearly different luminance and cool gray/blue-violet shadow versus warm cream/amber light, quantized to RGB555. Five shades per material is an upper-level simplification guideline; a 4bpp bank still has only15 visible colours shared among all its materials.
- Give the brick, crate, frog belly and wizard robe broad directional planes. Use a small local cast/contact shadow beneath a rim, hand or awning. Do not turn every brick, rag or round grate into a nested bevel.
- Replace universal near-black terrain borders with low-contrast material-dark mortar. Retain stronger dark contours around NPCs/interactive silhouettes and genuinely dark apertures. This is our scope-specific interpretation, consistent with Janes' selective-outline example; the article does not ban black universally.
- Manual internal AA may use an existing ramp colour if it improves one curve. No filtered resize, semi-transparent fringe or automatic blur: these are incompatible with our native4bpp assets and the user's GBA-first direction.
- Reserve dithering for small roughness/transition areas at an appropriate scale. Do not fill the traversable floor with checkerboards; the author's optional demonstration is not a directive to add noise.

## Source 3 — Alain Galvan, Pixel Art Design for Game Development (6 PDF pages)

Original upload: `Pixel Art Design for Game Development.pdf`.
SHA256: `7d419630c02c4af9f7c79baf9aa6973af06c8917bbb1acad37b84771ab7c59e8`.

### Explicit advice and observed examples

1. **Use constraints deliberately (pp1–2).** Historical resolution, colour and RAM limits create pixel art's character. Pixel art is designed pixel by pixel; every pixel matters. Modern unlimited RGB does not remove the usefulness of limits.
2. **Hue-shifting palette around a midtone (p2).** Build highlights/shadows around an average colour rather than a purely linear brightness ramp. Purple/teal shadows and yellow/white speculars are offered as useful relationships. The small blue creature illustrates a coloured material ramp; the article recommends at most15 visible colours plus transparency per sprite.
3. **Communicative silhouette, including action (p2).** The dark dragon/creature silhouette must convey its character/action before internal rendering. Paint within a controlled silhouette; do not rely on interior ornament to make a weak shape intelligible.
4. **Masks protect established shape (p3).** The yellow creature paint screenshot demonstrates preserving silhouette while painting. Photoshop's layer-mask menu is an example workflow, not a requirement to use that software.
5. **Balance AA and readability (p3).** Small sprites cannot carry unlimited intricate detail. More AA generally reduces crisp detail readability. Outlines can help characters and objects, while heavily outlining environments may be inappropriate. This is a balance, not a blanket ban on all AA or all outlines.
6. **Material-pattern shading over mechanical dither (pp3–4).** The large watery Perfect Chaos drawing uses flowing/swirling surface structure rather than a uniform checkerboard; the author describes blending through patterns and careful edge/shape control. The example is much larger and more detailed than our16px tiles, so its visual density is not a target for each tile.
7. **Revisit colour globally (pp4–5).** Curves and levels adjust contrast/midtones, colour balance adjusts overall shadow/highlight relationships, and exact colour replacement revises a palette. Illustrated Photoshop/Gimp panels show correction tools applied to an existing sprite. They are means of reaching better value/colour relationships, not an instruction to introduce unbounded final colours.
8. **Count final colours (p6).** A colour-analysis tool verifies the number of inks after revisions. The page also lists further resources, not additional read-and-adopt instructions.

### GBA application

- Every study should have a readable flat/silhouette blockout before adding cracks, trims and sparkles: arched inlet, continuous handrail with a bridge gap, ladder, frog eyes/jaw/haunches, wizard hood/staff.
- Keep primary shapes strong and contours crisp on moving subjects. Let architecture and terrain use different edge strengths: the floor should not compete with the frog or forest ladder.
- Represent sewage as coherent elongated flow bands/eddies anchored to the current and banks, not independent bright dash confetti; simplify the watery-monster example's structural idea to tiny native clusters.
- Do palette correction on the existing16-entry role bank, then quantize/check RGB555 and contrast. Hardware palettes replace Photoshop curves as the production mechanism; do not apply destructive post-render grading to whole screenshots.
- The article's Game Boy/NES historical limits are illustrative and do not supersede actual GBA hardware or this engine's budgets. Retain our engine-specific1024BG-subtile and legalOBJ-shape checks.

## Source 5 — Thomas Palef, Tips to Make Pixel Art for Your Games (9 PDF pages)

Original upload: `Tips to Make Pixel Art for Your Games _ by Thomas Palef _ Medium.pdf`.
SHA256: `7e3eb5b95882a0a701caad36974f6e90e118e3b78541a21c6297f395bf3fce1a`.

### Explicit advice and observed examples

1. **Simplify the palette (pp2–3).** Selecting a small, coherent set reduces the risk of one incompatible colour. The space-shooter example uses white silhouettes on dark blue, proving readable shapes can carry the game with only two colours.
2. **Begin with basic geometric forms (pp3–4).** The platformer example uses simple rectangular actors, hazards and terrain. Its point is an inexpensive coherent design, not a requirement that every game become abstract rectangles.
3. **Use small native resolution to focus decisions (pp4–5).** The adventure image and enlarged five-by-five character reduce decisions to very few pixels. The game scene keeps the river, bridge, character and ground readable through large simple masses. This does not instruct us to reduce Bloom to5×5 or build a high-resolution image first.
4. **Iterate instead of expecting a perfect first attempt (pp6–7).** The princess progression changes facial separation, hand/body shape and dress silhouette across several passes, then displays the final pixel grid. Most improvement is structural simplification/refinement, not piling on tiny detail.
5. **Match resolution to the intended style (p6) and simplify deliberately (p7).** If the tiny treatment is unsuitable, the author permits higher resolution. In this game, the user's GBA-first constraint sets the maximum; refine inside our accepted native footprints rather than changing the display or re-enlarging Bloom.
6. **Editorial/context limits (p1, pp8–9).** Page1 links a later improved article and shows a decorative forest header; the supplied PDF is the article actually read here. Pages8–9 are author/footer content. No animation timing, outline-thickness law, precise palette size or shading algorithm is supplied by this article.

### GBA application

- Use few deliberate material masses inside each tile and NPC. Do not use all15 ink slots merely because they exist.
- Reduce needless interior seams, buttons, floor cracks, repeated trim and decorative single pixels. Strong frog eyes/jaw, hood silhouette and arch/ladder structure should remain understandable before accent colour.
- Keep the room's playable floor quiet enough for Bloom, wares and glitter to read. This is our environment-specific application of the article's simplification examples, not a quoted quantitative floor-contrast rule.
- Preserve old/new sheets and native room crops to show the actual iterative improvement. Compare at1× and in room context, not only huge isolated illustrations.

## Joint interpretation and apparent conflicts

- **AA:** Janes demonstrates careful selective AA (pp4–5); Galvan warns that AA can reduce readability (p3). Adopt controlled existing-ink, internal/material-edge AA only when a native comparison proves it helps. Keep external transparency edges crisp, use no filtering, and prioritize silhouette.
- **Dither:** Janes' checker/quarter-density samples (p3) explain an optional colour-economy technique; Galvan (p4) prefers patterns that describe material. Apply sparse directionally/material-informed transitions at a large enough scale. Neither requires checkerboard noise across all tiny terrain.
- **Outlines:** Janes' pot loses some black outlining (p5); Galvan explicitly allows strong object/character outlines while questioning environment outlines (p3). Share a hue-dark contour vocabulary with different edge strength by gameplay role, rather than forcing one black border on everything or removing all actor separation.
- **Complexity/resolution:** Galvan's large watery creature demonstrates material structure, while Palef's tiny scenes demonstrate economy. Borrow the structure and economy; do not copy the large image's surface density into16px tiles or the5×5 example's literal footprint into established sprites.
- **Software commands:** Photoshop/Gimp menus and post-processing operations are examples of workflows. In our Python/native tile pipeline, achieve equivalent palette/shape control through indexed source art and explicit palette edits. Documents do not authorize arbitrary shell commands or unrelated edits.
- **No animation timing evidence:** These three PDFs do not teach anticipation/recovery frame counts, sword collision or physics. Preserve the user-selected Step-and-cut clock and borrow only action-readability/silhouette principles for local NPC poses.

## Specific critique of the first Drain studies (our assessment)

Viewed `art-review/sewer-concepts/source/room-overview.png` and `characters.png`.

- The common repeated mortar/brick outlines and highlighted horizontal courses often make floor, walls and bank faces equally insistent. The eye reads a graph-like room texture instead of a hierarchy of solid architecture, quiet travel plane and focal objects.
- Gold outfalls, rectangular crates and floor grates are often predominantly outlined/banded forms rather than clearly shaded volumes. Several rings have near-uniform bright perimeter weight; use directional light and a darker side plane instead of concentric bright bands.
- Roughness/filth is conveyed by small repeated motif clusters over a regular floor. Larger low-contrast stain masses attached to pipes, floor seams and water contact can feel like accumulated material instead of sprinkled symbols.
- Frog and wizard silhouettes are recognisable, but changes in outfit colour/trim still carry too much variation. Strengthen the primary eye/jaw/haunch and hood/shoulder/hem masses while keeping the established anchors and canvases.
- Every fifth-floor brick need not advertise itself. Focal gold/glitter must retain headroom over the scene's ordinary lit stone; preserve the existing surface glitter as requested.

## Application to all five revised styles (design proposals, not source assertions)

1. **Crown of Sludge:** simplify floors into broad cool-gray flag masses with understated mortar. Make the ceremonial outfall a real thick arch with broad light-facing blocks and a recessed cool cavity; reserve hot cream at a few upper-left metal glints. Larger accumulation stains below plumbing, not uniform crack density. Frog: round belly and a clear wide jaw under tall separated eyes; wizard: hunch expressed by shoulder/hood silhouette and one directional robe fold.
2. **Crooked Brassworks:** keep rounded geometry but remove heavy outlines around every cobble. Use chunky clear crooked pipes/bridge planks with controlled pixel-run curves and short contact shadows. Frog: the widest readable potbelly/haunch mass and asymmetrical sleepy eyes; avoid filling it with apron lines. Wizard: one exaggerated floppy hood curve, not several tiny bend pixels.
3. **Moonlit Cistern:** retain cool gray/teal atmosphere with separated value planes rather than many similar grays. Keep the water dark and broad, with long sparse current groups and restrained ripples. Warm brass should punctuate ladder/outfall, not trace every masonry seam. Frog: thin sleepy silhouette with clear lid/eye contrast; wizard: quiet rounded hood plus one clear staff/flame profile.
4. **Rotten Reliquary:** achieve filth with big attached low-contrast grease/lichen masses, jagged structural breaks and limited roughness rather than dense checker/crack marks. Keep a legible quiet path and a handful of clean glorious metal faces above it. Frog: low broad toad jaw/haunches and two readable eyes; wizard: broad frayed hem built from a few intentional tears, not disconnected pixels.
5. **Royal Drains:** simplify gilded details into confident bands and clearly shaded thick fittings. Reduce the all-over border/cross/star density so golden sacred/functional fixtures remain the focus; existing engine glitter supplies excess sparkle. Frog: compact capped silhouette with fewer uniform buttons/lines; wizard: tall hood and a few gold-trim cues that do not flatten the robe volume.

## Suggested review criteria (our synthesis)

- A flat silhouette or two-/three-value blockout conveys each NPC, the ladder, bridge and outfall before texture.
- Room-native comparisons show distinct foreground objects and a quieter traversable plane, without extra blur or expanded sprites.
- All hard curves have intentional run rhythms and no unexplained kinks; chipped/organic edges have coherent masses.
- Values remain distinct afterRGB555 quantization; material ramps hue-shift rather than merely moving up gray brightness.
- Upper-left diffuse lighting shapes volume; contact and cavity shadows stay in plausible locations. Glitter is a separate local specular exception.
- Colour count, tile/OBJ limits and current anchors are preserved after palette correction.
- Compare each pass with the previous art in the same native room and camera position, including moving water and NPC animation, then record what was changed and why in the common direction log.
