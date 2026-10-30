# Character reference notes: sources 2 and 6

Read 2026-10-30. These are paraphrases of the uploaded PDFs, with PDF page
numbers rather than inferred website section positions. Recommendations below
are reference content; they do not override the user's GBA-first requirements.

## Provenance and illustration access

**Source 2:** `Pixel Art Character Design_ A Sprite That Reads at a Glance,
Silhouette First — the-pixel.art.pdf`, 10 pages,
SHA256 `5e90a8dd2d59df7ea86863647812b4b6643b62db6c195110e126270f2f936a2b`.
The article's main content runs through page 8. Pages 9–10 are recommendations
and footer material. Text was read completely. The body is visually blank in
normal PDF rasterization, but its embedded images can be extracted independently.
I inspected the five embedded main illustrations: header image p1, Wick's
silhouette/flats/shading p3, proportions p4, scale comparison p5 and idle p7.

**Source 6:** `Creating Pixel Character Art_ from Sketch to Sprite “Pixel art #1”
by Livresquare - Make better art _ CLIP STUDIO TIPS.pdf`, 37 pages,
SHA256 `3598f14d1a56f9f56a2dcee349daca86a771bab9647c72be40aa80491ecc54c5`.
Main tutorial runs through page 33; pages 34–37 contain author, comments,
recommendations and footer. All main text was read. I inspected the embedded
intro comparison p2 and four costume sketches p3. The uploaded print PDF leaves
most later example-image spaces blank: the linework, AA, shading, dithering,
lighting and posterization example images described on pp4–32 are not embedded
as main-column images. Those textual explanations are available and usable;
I do not claim to have visually inspected absent illustrations. The many image
objects in early pages include unrelated recommendation/sidebar thumbnails.

Local inspection records and embedded figures are under
`/workspace/setup/pixel-art-reference-pdfs/renders/embedded-main-manifest.json`.
Do not publish the article illustrations as new game artwork.

## Source 2: complete actionable advice

| PDF pages | Author's explicit advice | GBA application / interpretation |
| --- | --- | --- |
| 1–3 | Begin with a filled silhouette; shading cannot rescue an unrecognizable shape. | Review native 16px frog head + 32px body and 32px wizard as one flat silhouette before detail. Repeat with the NPC behind its actual counter/rug. |
| 3 | Break the outer contour with a hood tip, weapon, hair or another projection. | Frog eye lobes and webbed haunches must identify the frog; wizard hood and separated staff identify wizard. Extra contour detail should support those identities. |
| 3 | Preserve negative spaces: legs separate, and a held object should not merge into the torso. | Leave at least a native-pixel readable gap between wizard robe and staff except at grip, and between feet/haunches. Do not fill these gaps with indiscriminate outline or glow. |
| 3 | Exaggeration often works better at tiny sizes than realistic proportions. | Enlarge frog eye lobes and droopy muzzle, or wizard hood, within existing canvas. Do not enlarge the whole NPC or Bloom. |
| 4 | Choose proportions for the role: about two heads for chibi/top-down, 2.5–3 for more limb gesture, 3.5+ requires enough pixels to retain face. | Use approximately two-head world frog/wizard construction, adjusted for frog anatomy. Keep expression legible at 1×. Do not import the tall illustration's proportions into the game. |
| 4–5 | Check the actual on-screen size early; a zoomed editor image can hide failed readability. | The source atlas's large zoom is insufficient: inspect native framebuffer and actual market/wizard crop at 1×. |
| 5 | Suggested roles: platform heroes 16–32px; top-down characters fit 16×16 to16×32; large bosses/portraits can carry more detail. | These are starting points, not hardware shapes or a mandate to use64px portraits. Existing32px world and48px portrait canvases remain valid. |
| 5 | Enemies may be simpler/smaller; the player should be easy to find first. | Keep Bloom's contrast priority. NPC decoration and floor sparkle should not camouflage Bloom. User-approved glitter remains unchanged, so reduce competing static texture instead. |
| 5–6 | Once shape works, use flat material colors then shading. Each material gets base+shadow and optionally highlight. | Frog skin: three actual paint values, eyes as a separate light/dark material; apron: two or three values. Wizard cloth: three values plus shared outline. A16-entry bank is a maximum, not a reason to paint six shades on a tiny cheek. |
| 6 | Limit the whole sprite too; the example uses many materials but only a few shades per material. Historical games often use fewer total colors. | Count nontransparent inks and reuse a common dark across materials. 4bpp permits15 painted indices plus transparent0, regardless of the example's loose whole-character count. |
| 6 | Shift hue when shading. The teal example's shadow and light differ in hue as well as brightness. | Frog greens can shadow toward cooler blue/olive and light toward warm yellow-green; purple robe can shadow toward blue-violet and warm toward its flame-facing edge. Keep chosen bank roles stable. |
| 6 | Selectively soften an outline on the lit edge; full dark outlines help very small sprites, while larger sprites can use more selective outline. | World silhouettes keep a firm one-pixel separation where needed. A lit contour can use an existing dark material ink rather than a doubled black band. At48px portraits this can be more deliberate. |
| 6 | Choose one signature detail, strongest in value/saturation and in silhouette. Supporting details should stay quieter. | Frog signature is its absentminded frog face; apron/cap/coin supports it. Wizard signature is flame-tipped staff; trim, beard and cloak folds must not compete with flame. |
| 6 | An identifying feature can also communicate mechanics, as in the example's hair-color discussion. | Use this only when the game actually has a corresponding state. Do not invent cap colors implying shop stock, flame colors implying quests, or another unimplemented mechanic. |
| 7 | Check horizontal flipping and decide whether asymmetric tools stay in one hand or mirror. | Do not blindly mirror a staff or coin into a detached position. Existing wizard's staff stays on a fixed side; every pose preserves that anchor. |
| 7 | Test a cheap idle before a walk cycle; about2–4frames can sell life. | Keep the existing frame identifiers/counts but make their idle/breath states a coherent small gesture rather than unrelated pixels. |
| 7 | In the demonstrated idle, head and torso descend1px while feet stay planted. Cloth trails by1px and flame changes shape on selected frames. | Wizard breath can lower hood/shoulder mass1px while robe hem and feet stay fixed. Frog head bob must overlap the body/throat continuously. Avoid shifting the entire actor or disconnecting feet. |
| 7 | Longer holds on a relaxed key pose avoid twitchy motion; example timing is250/150/250/150ms. | This is a starter example, not a required rewrite of existing NPC timing. Preserve current timers unless runtime review finds a concrete flaw. Give secondary flame less amplitude than a whole arm gesture. |
| 8 | Final checks: silhouette, role-sized proportions, real-scale readability,2–3shades/material, one strongest signature, and reading during idle/flip. | Include flat silhouettes, three-value material block-ins, native-context views and pose/animation comparisons in the regenerated review. |
| 8 | Ask someone to identify the flat shape without explaining it. | Provide unlabeled silhouette evidence as a review aid; labels should not be the only reason a frog/wizard reads. |

### Source 2 illustration observations

- **p3:** Wick's filled pale silhouette already separates his hanging lantern
  from his torso and leaves gaps between boots. His hood tip projects far
  enough to survive reduction. Flat colors preserve that same outline; the
  shaded third panel adds a few clustered teal highlights rather than fine
  equipment texture. This supports silhouette before surface decoration.
- **p4:** The shortest build allocates a large fraction of its height to the
  head and has compact legs; the tallest loses facial area. The variants change
  structural proportion, not just color or trim.
- **p5:** The smallest sprite retains a teal hood, orange scarf and separated
  light lantern. Fine eyes disappear before those masses. The lesson for our
  16px head is to preserve the frog's eye *lobes and muzzle shape*, not a tiny
  nostril/cheek ornament.
- **p7:** Four poses keep the boot bottoms on a common baseline. Upper masses
  shift only a pixel, and the lantern's flame changes without moving its stem.
  This is directly relevant to the existing fixed staff/flame anchor.

## Source 6: complete actionable advice and applicable limits

| PDF pages | Author's explicit advice | GBA application / interpretation |
| --- | --- | --- |
| 2 | The tutorial concerns detailed128×256 tall character sprites, often for dialogue/visual novels. Small sprites are more stylized and easier to animate. | Its lighting/line principles apply; its size and detail density do not set our world scale. Existing world32px / portrait48px remain native. |
| 2–3 | Multi-page art files help track character variants. | Keep consistent indexed source frames/atlases and documented anchors; there is no need to adopt Clip Studio EX or another editor. |
| 3 | Sketch multiple design/clothing ideas in a comfortable style before pixel work. | Explore multiple silhouettes as *native-size* flat thumbnails. The user explicitly rejects HD-first downscaling, so freeform ideation must not become the production source. |
| 3–4 | Decide the intended style before production: linework versus lineless, dithered versus clustered shadows, palette/era. Match the style to the design. | Each option needs an explicit compact shape/material plan, while sharing the game's perspective, scale, cluster discipline and interaction grammar. Avoid selecting arbitrary pixel treatments per asset. |
| 4–7 | Import sketch into the small target canvas; hard-edge interpolation makes pixels visible for tracing. | Do not use this literal high-resolution-sketch reduction workflow because it conflicts with the user's native-GBA-first directive. Use the general lesson of planning on the final canvas and hard-edge inspection. |
| 7–8 | For the demonstrated1px-line approach, keep consistent line width and regular diagonal stepping; accidental thickness changes and jaggies hurt flow. | Audit frog eye contours, round jaws, wizard hood diagonals and staff grips. Clean corner overlaps rather than retaining a2px blob where primitives intersect. |
| 9 | Deliberate jaggies/blocky corners may express hair parts or angular shape. | Ragged Pilgrim's torn hem or Rotten Reliquary's cracks may intentionally break a contour, but each break should describe a real material/shape. Do not treat random damage pixels as style. |
| 10 | Depart from the sketch when small sleeves or expressions become lost; enlarge or reinterpret details for the pixel image. | Give frog jaw/eyelid gestures usable pixel area and broad robe sleeves; simplify the mouth rather than trying to preserve a high-detail expression. |
| 11 | Establish shadow/light boundaries during line work and choose hue-shifted line colors compatible with them. | Plan a single lit shoulder/hood plane and a broad far-side shadow before adding folds. The darkest contour should support volume, not ring every internal patch. |
| 11–12 | Manual pixel-art AA uses small intermediate-color transitions. The author chose not to use it in the retro example. Zoom out regularly to check contour/shape language. | Manual AA is optional, not universally required or banned. If used in a48px portrait, choose existing legal opaque inks sparingly inside curves. Never use filtered/alpha-soft outer edges or add uncontrolled colors. At16px usually choose cleaner stepping instead. |
| 13–15 | Consider the desired palette; there is no universal art color limit. Disable automatic AA/area scaling in fill tools to prevent color spill. | Our hardware *does* impose a strict bank limit, so use15 painted entries maximum and no semitransparent fill artifacts. Material economy is additionally a style choice. |
| 15–16 | Shade based on light direction and object form, not dark rings following every border: avoid pillow shading. The author uses upper-left light and two shadow colors. | Frog forehead/jaw/haunch should read as lit masses with cast/occlusion shadows. Do not give every ellipse a concentric highlight ring. Robe folds should describe planes and drape. |
| 16 | About1–3shadow colors usually avoid muddy tiny forms. | On our very small sprites prefer one shadow + base + one optional light for a material. This adapts the broader tall-sprite range to32px. |
| 16–18 | Shading patterns communicate roughness or smoothness; dithering with lines/checkers/other patterns can soften transitions and imply texture. Pattern density controls the apparent color blend. | No blanket checkerboard skin/cloth. Use small controlled texture only where it conveys rough cloth, sludge or worn metal at1×. Distinct material clusters often serve16px assets better than dithering. |
| 18–20 | Optional shadow-edge color rims can suggest subsurface scattering or stylization; their brightness can soften or strengthen contrast. Dither can soften shadow edges. | A warm green light edge on frog skin, or restrained violet/amber reflection on robe, can be chosen deliberately. Do not outline every shadow in a bright rim, which would restore pillow shading and noisy edges. |
| 21 | Small variations within shadow/light can add depth; changing the base can clarify existing shadows. | Compare material masses in grayscale. Fix the large base-to-shadow separation before adding another swatch. Avoid subtle near-duplicate shades that consume a bank without improving1× readability. |
| 22–23 | Highlights follow form and reflectivity. Metal/silk can have brighter, tighter highlights than stone/flax. Do not simply light all corners. | Reserve tight gold and flame highlights for brass/staff/emissive material. Frog skin can have one small wet patch; cloth uses wider subdued planes. Gold trim should not light every seam. |
| 23–24 | Reflected light picks up neighboring/light-source color; stylized colored reflections can unify a design. | The flame-facing staff grip/hood may receive a very small warm reflection, and the far robe shadow may lean cool. Shared environmental hue can connect NPC and sewer without recoloring the entire character to the background. |
| 24–27 | Optional modern gradient/blend layers and a soft blush can add lighting, then a controlled extra shadow/light pass restores structure. The author expressly allows skipping this. | Skip blur, unrestricted gradients and blend-layer finishing in production. Author the intended light separation directly in RGB555 indexed clusters. A larger illustration's optional finishing is not a native-GBA requirement. |
| 27–30 | Posterization reduces color range; different level/opacity settings create different looks. | Do not depend on automatic posterization to rescue an HD image or enforce15painted inks. Our palette is authored from the beginning; use its general principle of deliberate color economy and inspect resulting clusters directly. |
| 31–33 | Export PNG and enlarge with hard edges for online presentation to avoid blurry website scaling. | Keep exact native PNGs and integer nearest-neighbour review copies. A1000px social-media canvas is presentation, not a game source. |
| 33 | This is one workflow among many, not a universal compulsory process. | Record which ideas were adopted, translated or omitted; do not claim all software operations were required. |

### Source 6 available illustration observations

- **p2 intro comparison:** The finished tall woman has visibly simplified pixel
  contour and broad color/shadow blocks relative to the soft sketch; light
  blue/teal reflected edges tie coat, hair and bag together. The example has
  far more pixel area and color freedom than a32px game NPC.
- **p3 four sketches:** Outfit variations change coat cut, sleeve shape, stance
  and large light/dark distribution, not merely hue. For our five studies,
  changing apron color alone is insufficient differentiation.
- Later linework, AA, pillow-shading, dither, reflection and posterization
  diagram spaces are blank in the supplied file; only their textual lessons
  are verified here. Do not reproduce imagined diagram details in citations.

## Critique of the first Drain NPC sets

Inspected `art/sewer_concepts_npcs.py` and the published first-pass
`art-review/sewer-concepts/source/characters.png`.

1. **The silhouettes are readable but too similar between options.** Frogs1,
   2 and5 mostly share a wide ellipse, raised eyes and central apron; wizard
   bodies share nearly the same triangular drape and interior folds. The
   source2 p4 and source6 p3 examples support varying large proportion/shape.
2. **Tiny materials use too many concentric values.** The frog palette defines
   six skin shades, and head shapes layer outline/inner ellipse/highlight arc/
   chin ellipse/light chin line. The effect is more contour-following than a
   single lit form. Source2 pp5–6 and source6 pp15–16 call for fewer purposeful
   material values and form-based lighting.
3. **Body shading is not sufficiently specific to silhouette.** Five wizard
   coat outlines differ, but the inner polygons are reused. Rebuild the light
   and shadow planes for each hood, shoulder posture and robe drape.
4. **Small trim competes with identity.** Apron pockets, pins, isolated gold
   points and robe hems consume contrast. Source2 p6 suggests preserving one
   strongest signature, with other decoration quieter. Keep the frog face and
   wizard flame as the strongest cues.
5. **Some contour detail describes the drawing tool, not the material.** Generic
   ellipses and line intersections create uneven outer thickness. Source6
   pp7–10 supports hand-cleaning curves and deliberately angular/ragged accents.
6. **The existing staff/flame anchor is good and must remain stable.** Its
   separation from the body follows source2 p3. Retain body-relative flame
   origin(23,1), staff top near(26,8), legal8px flame and palette13/14 emissive
   reservation. Improve the robe/hand pose around it rather than relocating it.
7. **Use actual counter/context as the final readability test.** Most frog
   lower-body detail is occluded by the counter. An improved face silhouette,
   gaze and upper shoulder shape will matter more than a new hidden apron seam.
8. **Idle should articulate upper masses, not disconnect them.** Head/body
   overlap needs a small safety margin throughout the existing one-pixel head
   bob. Wizard hood/torso can shift against planted hem/feet. Current six pose
   IDs and fourteen body IDs can be reauthored without treating the reference's
   example timing as an instruction to change the game clocks.

## Proposed five-way NPC direction, explicitly our interpretation

| Concept | Frog emphasis | Wizard emphasis | Shared-rule evidence |
| --- | --- | --- | --- |
| Crown of Sludge | Broad, heavy jaw and widely separated eye lobes; single simple worn apron mass. | Bowed shoulder, compact bent hood and broad fold; fire stays brightest. | Source2 pp3–6; source6 pp15–16,22–24. |
| Crooked Brassworks | Squat belly with clearly uneven eyelids/eyes and a lopsided shoulder gesture. | Floppy hood tip projecting sideways, rounded sleeve; readable gap to staff. | Source2 pp3–4; source6 pp8–10. |
| Moonlit Cistern | Narrower sleepy face, broad single eyelid planes, fewer tiny mouth/nostril pixels. | Rounded hood and long quiet cool shadow plane; only a small warm flame reflection. | Source2 pp4–6; source6 pp21–24. |
| Rotten Reliquary | Low broad toad jaw and squat haunches; a few connected rough-skin clusters. | Ragged asymmetrical hood/hem, intentionally broken contour but simple continuous drape. | Source2 p3; source6 pp9,16–18. |
| Royal Drains | Compact upright frog with a cap large enough to read in silhouette; tidy quiet coat. | Angular tall hood, restrained trim and explicit plane changes rather than jewelry pixels. | Source2 pp3,6; source6 pp7–10,22–23. |

All five should still belong to the same game: same foot baseline and anchors,
same three-quarter viewing convention, same outline discipline, same material
budget and hierarchy. Their distinction must survive a black silhouette and
the actual native background, not depend on each using another rendering style.
