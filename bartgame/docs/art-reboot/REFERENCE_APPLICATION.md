# How the six PDFs change the shared art direction

R1–R6 and PDF page numbers are defined in the [reference register](REFERENCE_REGISTER.md).
The full reading notes cover individual recommendations and examples. This
matrix records their production application, including advice requiring
adaptation. Hardware limits come from the project specification, rather than
unsupported claims about another console's tutorial.

## Adopted shared rules

| Rule | Source evidence | Application to this game and the revised Drain |
| --- | --- | --- |
| G01 — Form before finish | R1 pp. 4–5; R2 pp. 3–5; R4 p. 18; R5 pp. 3–7 | Make flat native silhouettes and simple material masses first, then shade and clean edges. Texture and glitter cannot rescue an unclear frog, pipe or opening. |
| G02 — Role-scaled silhouettes | R2 pp. 3–5; R4 p. 7 embedded chart, pp. 9–14 | Exaggerate readable features and negative space at actual size. Preserve accepted GBA canvases and Bloom's scale; world sprites and portraits are separate drawings. |
| G03 — One main character hook | R2 pp. 6–8; R4 p. 7 embedded chart | The frog's jaw/eyes and the wizard's hood/flaming staff must survive silhouette and animation. Clothing supports identity instead of adding competing ornaments. |
| G04 — Palette ceiling, not quota | R2 pp. 5–6; R3 p. 2; R4 pp. 7–14; R5 pp. 2–3 | Aim for base/shadow/light per small material. Keep each 4bpp bank to fifteen visible RGB555 inks plus transparent zero; do not fill slots with indistinguishable shades. |
| G05 — Distinct, hue-shifting values | R1 pp. 2–3; R2 p. 6; R3 p. 2; R6 pp. 11, 16, 19–24 | Use cooler shadows and warmer selected highlights with clear value steps. Judge the quantized bank in grayscale and scene context. |
| G06 — Directional volume | R1 pp. 4–5; R4 p. 18; R6 pp. 15–16, 22–23 | Shade broad light-facing and shadow planes with an upper-left source and contact/cavity shadows. Replace concentric edge-following pillow bands on arches, faces, robes and crates. |
| G07 — Material-specific highlights | R3 p. 4; R6 pp. 16–18, 22–24 | Gold uses narrow strong specular groups; cloth and matte brick use broader quieter masses; wet muck has sparse attached reflections. Existing glitter remains abundant. |
| G08 — Controlled line cadence | R1 pp. 1–2; R6 pp. 7–10 | Refine curves, regular slopes and one-pixel contours in native coordinates. Deliberate chips, ragged hems and organic jaws may break regularity; accidental kinks may not. |
| G09 — Selective edge strength | R1 p. 5; R2 p. 6; R3 p. 3; R6 pp. 11–12 | Keep actors and functional silhouettes separate with hue-dark edges. Floor joints and subordinate architecture use softer material contrast instead of equal outlining everywhere. |
| G10 — Selective palette AA | R1 pp. 4–5; R3 p. 3; R4 pp. 18–19; R6 pp. 11–14 | An existing intermediate ink may improve an internal turn at 1×. Keep moving transparency edges crisp. Avoid filtered resizing, fractional-alpha fringes and indiscriminate softening. |
| G11 — Deliberate clusters and texture | R1 p. 3; R3 p. 4; R4 p. 7 embedded chart; R6 pp. 16–20 | Texture describes material. Use accumulated grease/slime and purposeful chips, rather than scattered decoration or checker patterns covering every floor tile. |
| G12 — Quiet field, clear focal objects | R2 p. 6; R4 p. 7 embedded chart; R5 pp. 2–7 | Spend detail/contrast on identifying and functional features. Drain floors stay subordinate to Bloom, the forest ladder, market frog, flame and main gold outfall. |
| G13 — Native translation | R4 p. 7 embedded chart; R5 pp. 4–6; R6 pp. 2–10 | Translate references into native silhouettes instead of shrinking high-resolution art. Simplify or exaggerate details that vanish. |
| G14 — Coherent idle motion | R2 pp. 7–8 | Keep feet planted, coordinate the small upper-body/head breath, and let cloth/flame lag. Preserve the signature silhouette and grip in every pose. |
| G15 — Family and scene review | R2 pp. 4–8; R4 p. 17; R5 pp. 6–7; R6 pp. 10–12 | Inspect full sprite families, native silhouettes and grayscale values, then actual rooms and motion. Preserve before/after evidence and critique each iteration. |
| G16 — Explicit palette correction | R3 pp. 4–6; R6 pp. 24–30 | Adjust the authored bank and recheck RGB555/readability. Do not grade a finished screenshot and treat it as implemented art. |
| G17 — Reflected light supports form | R6 pp. 19–24 | Use a small material-related reflected patch when useful, such as flame warmth on a robe. It must not become a second full outline or compete with the main light/signature. |
| G18 — Pixel-preserving presentation | R4 p. 7 embedded chart; R6 pp. 31–33 | Keep exact native files and integer nearest-neighbour review enlargements. Captions sit outside game pixels. Source assemblies, diagnostics and mGBA captures are labelled separately. |

## Conflicts, optional advice and intentional adaptations

| Advice in the sources | Decision and reason |
| --- | --- |
| R1 p. 3 shows checker/quarter-density dithering; R3 p. 4 favours material patterns; R6 pp. 17–20 offers several patterns. | Dithering is optional and local. It does not justify high-frequency checks across walkable ground. The resizing chart's no-dither step concerns outline repair, not a universal ban. |
| R1 favours regular lines; R6 p. 9 uses jagged changes for hair/angular forms. | Remove accidental cadence errors while retaining meaningful damage and silhouette features. Clean art need not make every broken brick a perfect rectangle. |
| R1 removes some black pot outlines; R3 permits outlined actors/objects but questions environment outlines. | Use role-dependent hue-dark contours. Preserve character/interaction edges while reducing floor/wall wire-grid contrast; neither universal black outlines nor universal outline removal is adopted. |
| R1/R4 show hand AA; R3 warns AA can obscure detail; R6 omits it in its retro example. | Use existing-ink manual AA only where native comparison proves an improvement. A crisp unsoftened contour is also valid. |
| R5 demonstrates two-color games, rectangles and a 5×5 character. | Adopt economy and readable forms, not literal replacement of this game's established scale/materials with abstract shapes. |
| R6 pp. 2–7 uses a 128×256 portrait and a downscaled tracing sketch. | Use native silhouette sketches and separately authored 48×48 portraits. The user's GBA-first requirement takes priority over that large-illustration workflow. |
| R6 pp. 13–15 permits unrestricted palettes; pp. 24–30 optionally add gradients, blurry blush and posterization. | Translate useful value/colour ideas into explicit indexed banks and native clusters. Blur, unrestricted colors and automatic posterization are not production steps for our 4bpp art. |
| R3 pp. 4–6 shows Photoshop/Gimp curves, levels and color balance. | Make equivalent deliberate palette choices in the native code. These menu examples do not require a new dependency or changes to unrelated imagery. |
| R4 compares NES/SNES/DS Mario and twelve-color Celeste. | These support constraint/readability lessons. They do not establish DMG sprite sizes, mandate four colors, or define GBA hardware limits. |
| R2 provides a sample 2–4-frame idle and example hold times. | Adopt planted-foot breathing in the existing keeper system. Preserve established act clocks and Step-and-cut combat timing rather than copying unrelated millisecond values. |
| Articles suggest software, external tutorials, palette sites and public sharing. | Record these as recommendations. Reading the PDFs does not mean external links were accessed or that every recommendation is a command/publishing instruction. |

## Concrete second-pass implementation

All five Drain directions keep their identities while their forms are
reauthored under G01–G18. Floors lose wire-grid dominance; architecture and
props gain directional planes; grease becomes accumulated material; water
uses coherent flow groups; focal metal receives selective highlights. Frog
and wizard silhouettes, material clusters and pose families are redrawn.
A concept-only added frog-body breathing frame coordinates the existing head
bob with a planted lower body while retaining original frame identifiers.

Regenerate the five complete sets, three mixed recipes, every asset/frame
atlas, native room assemblies, grayscale/silhouette diagnostics, actual mGBA
recordings and playable builds. Link visible changes to these rules and retain
the first study for before/after comparison.

Future shared direction and this pass's implementation scope are distinct:
the current redraw covers Drain studies. Forest, Bloom, HUD and existing
glitter remain protected in the ROM audit.
