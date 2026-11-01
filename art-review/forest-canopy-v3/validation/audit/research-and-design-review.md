# Independent canopy design review: source basis and current brief

This is an original analysis of the current user feedback, existing source notes,
and images actually inspected. It does not claim a new web article or missing
PDF illustration was accessed. Final actual-game critique is separate.

## Sources actually consulted in this pass

- `docs/art-reboot/ART_BIBLE.md`, `REFERENCE_REGISTER.md`,
  `REFERENCE_APPLICATION.md`, the final forest-v2 and lantern decision entries.
- `references/JANES_GALVAN_PALEF.md`,
  `references/CHARACTER_DESIGN_LIVRESQUARE.md`, and
  `references/FOREST_READABILITY_RESEARCH.md`.
- The published `art-review/forest-concepts-v2/healthy-mixed-deep-actual.png`:
  real native mGBA panels, not source mockups.
- The previously pinned Emerald Petalburg Woods source reconstruction at
  `/workspace/setup/forest-concepts/research/emerald-petalburgwoods-terrain-source.png`.
  Its revision, source URLs and methodology are recorded in the forest research
  notes. This reconstruction is static source evidence, not a live emulator run.
- Three mutable native source previews from the new canopy artist under
  `forest-canopy-v3/art/first-native-canopies-source.png`, `second-...` and
  `third-...`. These were draft checkpoints, not final capture evidence.

## Attribution and application

Janes' PDF pp.1–2 discusses controlled horizontal, vertical and diagonal pixel
runs and deliberate curve cadence. The supplied reading notes do **not** establish
that horizontal lines universally work better than vertical ones. Broad horizontal
branches are the user's current direction for this game. The PDF-supported rule
is to make intentional, clean shape/line decisions and preserve recognizable form.

Janes pp.4–5 and the character tutorial pp.3–5 support form/silhouette before
surface detail. The pinned Emerald reconstruction makes the related practical
point: a repeated unit can still read clearly as a tree when it has a recognizable
crown, leaf surface, dark underside and trunk relationship. Repetition itself
is not automatically a defect; repeating an unclear glowing emblem is.

## Why the previous canopy failed

In the old actual panels, repeated violet loops/strokes dominate a nearly black
mass. Their equal spacing and strong outlines read as a fence, runes or an
ornamental wall. The healthy canopy has finer green texture but little obvious
large crown/branch hierarchy. The quiet gray-olive floor is successful and should
stay unchanged; making it purple again would remove that useful contrast.

A successful replacement needs a recognizable leafy mother crown before the
infection is added. Use a few broad overlapping lobes, a lit upper plane, a
scalloped dark underside, readable pointed leaf clusters, and a lateral fork
beneath the foliage. A tree may still have a short vertical trunk. Horizontal
branch direction is not a reason to flatten the entire crown into stacked plates.

## Wide exploratory treatments

1. Branch-following luminous vascular veins.
2. Broad necrotic patches that retain leaf-volume planes.
3. Localized directional spore/dither infection islands.
4. Attached layered bracket fungi.
5. Bruised purple leaf clusters mixed with living leaves.
6. Wet black sap following lateral forks with short drips.
7. Parasitic silk concentrated in crown gaps.
8. Flowering/canker clusters attached to recognizable branches.

The current eight studies cover these treatment types. Veins, spores, fungi,
silk and cankers give the widest structural range; patches, violet leaves and
sap need native scene context to establish their differences clearly. All retain
actual connected green leaf clusters in the deep version, rather than a green
outline or isolated colored dots. Approximately 20% is a direction for the
remaining live canopy, not a claim that every cropped quadrant or whole scene
has an identical pixel percentage.

## Draft iteration critique

The first native preview looked like stacked thin green plates or lily pads.
The second gained volume but retained a rounded-brick/bean-stack risk. The third
added pointed leaf sprigs and coherent fork/trunk anatomy: individual source tree
units now read as trees. Diseased planes follow the same mother crown rather
than replacing it with independent glyph wallpaper. Actual connected-wall
repetition and live player occlusion still require the separate mGBA review.

Fungus caps and canker nodes should visibly attach to wood/foliage so that they
stay environmental growth rather than apparent loose pickups. A single shared
healthy construction is an honest controlled comparison for different disease
treatments; the final gallery should not imply eight unrelated healthy species.

## Final verification scope

Check direct native pixels, legal palettes and packed ROM frames; protect the
accepted gray grass and every non-canopy frame's visible colors. The new canopy
palette should leave old foliage, blight, ground, glitter and OBJ colors intact.
Check horizontal overhangs in movement and meaningful player visibility rather
than only one surviving pixel. Legitimately blank death/drowning animation frames
must be distinguished from disappearance caused by canopy occlusion.

Because room generation is unchanged, this focused review does not repeat the
previous 500,000-room generator corpus. It separately compares generator bytes,
physical metadata and old profile controls. Finite captured motion cannot by
itself prove every possible camera/action arrangement; the engine's bounded
visibility rule and its explicit limitations must also be reviewed.

## Actual pilot correction before freezing

The first new actual pilot (`pilot-full-style11`, ROM `741e2495…`) revealed that
source-unit recognition was insufficient. Its `living-cape-under-canopy/frame-018.png`
shows a connected healthy wall still reading as rounded green brickwork/hedge
masonry. The captured artist SHA `0a4323b1…` matched the then-current source, so
this was not an obsolete first draft. The repeated mother crown's large lower
lobes divide the nominal32px unit into quarter-sized masses. Recommended a
macro-only single dominant leafy dome, darker scalloped underside and short
lateral branch/trunk cue, then review the complete actual wall again. Standalone
trees can keep their larger multi-lobe crown construction.

The capture agent's IRQ/gameplay-update observation also exposed a real timing
regression in this pilot:13–14 zero-update intervals in128 walk frames versus
zero in the old6 control, with the same input ending seven pixels short.
Source cutoff/connectivity work must be optimized; the physical/input matcher
must remain strict. These failed pilots are diagnostic history and must not be
relabeled as final passing evidence. Final code/art review will be bound to
new frozen input hashes and a new actual run after the repairs.

## Revised actual form after the pilot critique

Reviewed fresh actual `pilot-latest-style11-landscapes/{healthy-canopy,
mixed-forest,deep-blight}.png`, ROM `1a125213…`, with the current artist module
SHA `e905aac03c5b46b2388b7e3f83c8e9763eef6e579cd6ee75b2786e9f3639e92e`.
The exposed brown forks/trunks at walkable edges now make the boundary read as
trees rather than masonry. The deep crown retains actual green leaf clusters,
diseased leaf planes and attached purple veins. The accepted gray floor remains
a quiet, clear travel surface. No concrete blocking form change remained before
freezing the eight treatments. Interior32px crown rhythm is still visible;
this is now a repetition tradeoff rather than the earlier loss of tree identity.
The mixed clearing can look spare because its generation is intentionally held.

This is an unfrozen actual-art review, not final source/ROM provenance. All eight
final deep treatments and live guard/action sequences still need their separate
frozen actual review. The artist has held the module at the hash above.
