# Drain terrain revision 2 — source-led decisions

Scope: only `art/sewer_concepts_terrain.py`; all room IDs, placements, physical
metadata, palette roles, animation counts/speeds, Bloom and glitter contracts
remain outside this painter's changes. These are five exploratory local Drain
styles, not an automatic selection of the game's final sewer design.

## Sources read

Read all three complete research-note sets from the uploaded PDFs. Citations
below refer to actual PDF pages. Janes and Galvan's notes document their
illustration examples; Adafruit's main content is pp6–19 and its embedded
MiniBoss chart is p7. The later Clip Studio diagram spaces are missing from the
uploaded print, so only its text and available introduction examples are used.
No article illustration pixels are copied or imported by the painter.

## Decisions applied to every style

- **Mass and hierarchy before texture.** The floor, masonry, liquid, inlet and
  market are blocked as coherent material planes. The canopy is cloth over a
  dark recess and the counter has a top/near face, rather than a decorative
  outlined box. Main references: Adafruit p7 embedded MiniBoss chart and p18
  form→shade→edge sequence; Palef pp3–7; the-pixel.art pp3,5–6.
- **Floor is quiet but explicitly masonry.** Travel-plane shadows/mortar use
  interrupted or broad16px bonds instead of an all-over8px black grid. Each
  style keeps a readable native bond: broad flags, rounded cobbles, long flags,
  damaged pavers, or chamfered ordered flags. Sparse lit plane groups are
  supporting texture rather than a bright outline around every stone. This is
  our native environment application of Galvan p3, Adafruit p7 and Palef pp2–7.
- **Directional material volume.** Hue-shifted RGB555 role banks separate cool
  shadows from warmer lit faces. Gold inlet/pipe planes have asymmetric bright
  upper-left facets, a darker right return, and brief local speculars rather
  than concentric pillow bands. Crates/barrels have readable top and side
  planes and matte wood; iron bands use different reflectivity. References:
  Janes pp2–5; Galvan pp2–5; Livresquare pp15–24 (text).
- **Purposeful contours.** Native step patterns and contour masks keep the
  original inset inlet inside unique room-ID footprints. Lit contour sections
  use material colours; genuine apertures use the deep dark. Organic tears
  and damage describe material rather than randomized raster kinks. References:
  Janes pp1–2,5; the-pixel.art p3; Livresquare pp7–12.
- **Few values per material.** Typical floor, cloth, wood and water groups use
  two or three principal values. A16-ink bank is the shared ceiling, not an
  instruction to shade every object with fifteen inks. Deep cavity/contact
  shadows and isolated metal highlights have separate roles. References:
  the-pixel.art pp5–6; Palef pp2–3; Adafruit pp7–14; Galvan p2.
- **Filth accumulates in connected masses.** Broad low-contrast grease/slime
  deposits sit beneath plumbing, along banks and at a handful of known debris
  sites. Gray crockery, fish remains, glass or a grease rag do not share loot's
  bright gold/ivory marker. Existing runtime glitter is preserved, so static
  detail is made quieter rather than disabling the sparkle. References:
  Galvan p4 material-pattern principle; Adafruit p7 focus on identifying
  details; Palef pp3–7. The specific sewage/debris forms are our design, not
  prescribed by any author.
- **Liquid has a separate material grammar.** Water uses connected elongated
  ribbon/eddy clusters, calm intervals and staggered groups rather than random
  bright dashes or mechanical dither. All translating flow follows the actual
  declared period. The wall fall has two irregular pouring curtains separated
  by dark negative space, moving streaks and attached impact ripples/splashes;
  it must not read as a green architectural column. Reference: Galvan p4's
  material-informed water pattern, simplified to native size; Adafruit p18.
- **Native production and presentation.** Every tile remains indexed16×16 and
  the additional handrail16×8; review2×images use nearest neighbour. No HD
  tracing/downsample, blur, automated posterization, unrestricted colours or
  fractional alpha. References: Adafruit pp7,9–19; Galvan pp1–2; Palef pp4–6;
  Livresquare pp4–7,24–33 translated to the user's stricter GBA-first mandate.
  Software menus, large128×256 character examples and the NES/SNES examples
  are not GBA hardware prescriptions.

## Five local vocabularies

1. **Crown of Sludge:** broad Roman ashlar/flags, heavy recessed inlet,
   compressed metal joints and simple draped market cloth. Broad slab bridge.
2. **Crooked Brassworks:** rounded masonry, patched scalloped awning, squat
   cylindrical fittings and thick wood planks with matte grain/cast shadows.
3. **Moonlit Cistern:** long cool flags and restrained masonry planes, pointed
   inlet, pulled tarp and quiet stone crossing; warm fittings punctuate blue-gray.
4. **Rotten Reliquary:** limited connected masonry fractures, accumulated muck,
   broad ragged fabric and damaged bridge planks; the travel plane stays readable.
5. **Royal Drains:** ordered chamfered masonry, plane-based gilt inlet, restrained
   trim on taut cloth and metal-grate crossing. Decorative contrast is subordinate
   to the functional forest ladder and primary sewer mouth.

## Iteration record and remaining review

The first native revision2 sketch made broad triangular highlights repeat into
zigzagging floor texture. It was rejected locally; the next pass reduced those
patches, then restored coherent broad mortar courses in1/3 after parent review
so the floor did not become featureless concrete. The first broad waterfall
read as a green pillar; it was reauthored as separated irregular curtains and
an impact splash. Perfectly aligned continuous water rows read as fabric, so
calm gaps, eddies and staggered vertical placement were restored while keeping
coherent large clusters. This follows Palef's iteration advice (pp6–7), not an
assertion that the first generated image was finished.

Source assemblies live under `terrain/`, with native and nearest2×copies. They
include current NPC source poses for context and omit runtime ambient glitter.
Root must inspect packed real-mGBA views and hardware budgets before publishing.
The whole room is480×320 world pixels, not one GBA240×160 screen. Some small
seam pieces or transparent overlay lanes can remain shared deliberately; no
meaningless pixels are added merely to force five unique hashes.
