# Reference-led NPC redesign, second Drain pass

Scope: `art/sewer_concepts_npcs.py` only. All five remain exploratory local
Drain treatments, not five incompatible rendering styles. Native anchors,
canvases and first fourteen body IDs remain stable. This file records the
art decisions for incorporation into the parent's shared direction log.

## Actual sources read

Read the complete three research-note files, source2 main article text, and
viewed source2's extracted silhouette/flats/shading, proportion, native-scale
and idle illustrations (PDF pp3,4,5,7). Viewed source6's available introductory
finished/sketch comparison p2 and costume/shape variations p3. Its later
illustrations are absent from this uploaded print; their explicit text is
recorded in the source notes and was not substituted with imagined examples.

The implementation also applies the page-specific guidance recorded from
Janes/source1, Alain/source3, Adafruit/source4 and Palef/source5. No commercial
example pixels or source tutorial images are copied into game art.

## Decisions and rationale

| Change | Source evidence | Native implementation |
| --- | --- | --- |
| Redesign from masses, not from the old ellipse/ring decorations. | Source2 pp3–4; source4 p18 and p7 embedded MiniBoss chart; source5 pp3–7. | Five new hand-authored16×16 head masks, five proportion-specific body masses, five hood/robe plane sets and separately drawn48×48 portraits. The wide/squat/narrow/low-toad/compact-capped silhouettes differ before colour. |
| Concentrate identity in one strong visual feature. | Source2 p6; source4 p7 embedded MiniBoss chart. | Frog eye lobes/muzzle carry the character; apron pockets, metal pins, multiple buttons and tiny border embroidery are removed or reduced. Wizard's flame-staff remains brightest, with cloth/beard/trim subordinate. |
| Keep negative spaces and readable contours. | Source2 p3; source1 pp1–2; source6 pp7–10. | Eye lobes break the frog silhouette, haunches/legs join planted webbed feet, and the wizard's staff stands apart from the robe except at its connected grip. Stepped head masks replace generic nested ellipses. Ragged contours describe cloth tears rather than loose flecks. |
| Use two or three purposeful tones per painted material. | Source2 pp5–6; source1 pp2–3; source3 p2; source4 pp7–9; source5 pp2–3. | Green forehead/cheek/haunch uses indices2/3/4; separate cream throat uses5/6, eyes7+1. Apron uses9/10/11; cloak uses2/3/4. Palette bank remains16entries including transparent0, with unused role slots permitted rather than painted as a quota. |
| Describe volume under upper-left light, avoiding pillow rings. | Source1 pp4–5; source6 pp15–16,22–24. | One broad lit forehead/near haunch and far-side skin shadow; one broad lit hood/near shoulder and a darker draping plane per silhouette. Cloth highlights are broader and quieter than narrow metal/flame highlights. Internal hand/neck/robe overlaps receive restrained occlusion instead of bright edge bands. |
| Hue shifts and value separation happen in source palettes. | Source1 pp2–3; source3 pp2,4–6; source2 p6. | Cool green/blue-violet shadows, warm green/cream or violet lights; every returned palette isRGB555. No screenshot colour grading, blur, semitransparent edge or automatic high-resolution reduction. |
| Idle articulates the connected upper body with fixed feet. | Source2 p7 illustration and text. | New `breathe` body frame is appended after the fourteen existing IDs. Torso/throat/shoulders/hands compress1px to match headY6→7; bottom rows29–31 are naturally exact `rest` pixels for every style. Wizard hood/near shoulder shift1px while staff, hem and feet remain fixed. Existing action timers are not changed by this painter. |
| Flame is a small coherent animation, not detached glitter. | Source2 pp6–7; source6 pp22–24. | Four newly drawn8×8 connected flame phases with five local tongue shapes. Shaft top remains(26,8), flame origin(23,1), and each base touches that stem. Emissive13/14 never paint any robe frame. |
| Preserve readable expression when isolated details vanish. | Source2 pp4–5; source6 p10; source4 p7 embedded MiniBoss chart. | Large eye white/pupil groups and jaw direction replace tiny nostrils/cheek ornament; sleepy eyes still have separate lobes rather than a full-width bar. Wizard face stays shadowed, so no implausible tiny facial anatomy is forced into the hood. |
| Redraw portraits as native busts of the same characters. | Source2 pp4–6; source6 pp2–3,10. | Independent48px silhouettes preserve the same eye spacing, jaw, cap, hood and staff. Portraits add controlled planes, not an enlarged screenshot or a reduced128×256 illustration. |

## Five shape plans

1. Crown: broad round frog jaw and heavy near haunch, plain worn apron; short
   hunched pilgrim with a compact bent cowl and one broad draping fold.
2. Crooked: the broadest asymmetric frog paunch and uneven eye heights; a
   sideways floppy hood and rounded shoulder/sleeve.
3. Moonlit: narrower dozy frog with distinct lid/eye lobes and quiet coat; a
   round shroud and long cool shadow plane, little trim.
4. Reliquary: the lowest broad toad jaw and haunches; a few large ragged cloth
   cuts and broad offset hood, without noisy warts or floating thread pixels.
5. Royal: compact frog with a small legible porter cap and quiet button coat;
   tall pointed cowl with one restrained gold seam, not a ring of jewelry.

## Deliberate adaptations and exclusions

The sources do not mandate every software operation or every example size.
Source6's128×256 traced/downscaled sketch, optional blurred gradients and
posterization are not used: the user's GBA-first requirement takes priority.
Source1's optional dithering and selectiveAA and source3's readability cautions
are reconciled through cleaner pixel runs/material clusters; no blanket
checkerboard or fuzzy external AA is needed on these tiny moving sprites.
Source4 does not supply a mandatory four-colour DMG rule; GBA limits come from
this project's independent hardware specification. Source2's example idle
hold times are a starting example, not a request to replace game clocks.

## Review artifacts and checks

- `npc-concepts.png`: 1× and4× native characters plus independent2× portraits.
- `silhouettes-and-values.png`: filled silhouettes and three-value reductions.
- `idle-study-1.gif` .. `idle-study-5.gif`: labelled source-pose studies;
  ordinary in-game timing and rendering must be judged in the parent's mGBA
  recordings, not inferred from these presentation loops.
- `before-after-characters.png`: matched first-pass and revised source poses.
- `native-review.json`: legal canvases, palette values, unchanged foot rows,
  connected flames, source-change coverage and per-material usage.

All150 world frames (five×(5heads+15bodies+6wizards+4flames)) and ten portraits
are legal indexed drawings. All first-pass world-frame and portrait geometry
has changed. All four flame phases have five distinct style geometries. The
bottom three body rows are identical for rest/breathe in every style. These
are source/structure observations; the parent retains runtime OAM, context,
frame-schedule, VRAM budget and actual idle checks.

Remaining tradeoff: extremely small world faces cannot carry the portrait's
expression detail. The torso/haunch variations matter more in a full source
view than behind the actual counter; the larger eyes, mouth and shoulder mass
are therefore the primary native gameplay cue. No unexplained extra trim is
added to compensate for counter occlusion.
