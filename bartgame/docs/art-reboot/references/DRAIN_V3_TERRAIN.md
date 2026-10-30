# Drain materials — feedback-led revision 3

Status: five exploratory alternatives, frozen for native/context and emulator
review. These are new local proposals rather than a final production selection.
Source artist changes are confined to `art/sewer_concepts_terrain.py`; fixture
work is installed from `art/sewer_v3_fixtures.py`. Default study zero, room IDs,
placements, collision, type, props, glitter flags, Bloom, and other areas stay
outside these painters' scope.

## User feedback applied

The user rejected every previous floor and wall (wall 4 closest), every ladder
(ladder 1 closest, arrows illegible), and every falling-water drawing (root-like).
They preferred bridge 4; rail 1/2 plus 4's decay; floor grate 4; banks 1/2/4.
The materials therefore share damaged retaining masonry descended from old 4,
weathered brass rails descended from old 1/2, and repaired timber bridge
construction descended from old 4. None of the five new floors reuses an old
floor's drawing. Fixture decisions are recorded separately.

## New construction choices

1. **Ashlar & Amber:** broad gray running-bond bricks with partially eroded
   mortar; heavy irregular blocks, repaired timber and restrained brass straps.
2. **Crooked Brickwork:** unequal-height reclaimed brick courses; short wall
   courses with chipped corners and broad, readable wooden bridge planks.
3. **Floodworn Flags:** staggered longitudinal setts; broad damp wall flags and
   a repaired crossing with a single iron reinforcing strap.
4. **Crumbling Vault:** oversized chipped flags with coherent boundaries,
   broken retaining blocks, surface-cracked wood and attached dark grime.
5. **Silted Cloister:** small horizontal/vertical paired bricks in a repaired
   herringbone panel, eroded long masonry and patched timber. This is deliberately
   the densest option; its joint contrast and short seams were reduced after
   native review so it competes less with small actors and objects.

Floors have gray faces, not green bodies or all-over gold edging. The lower/right
joints are muted shadow colors; top light is sparse, local and directional.
Mortar describes actual stone boundaries, rather than floating scratches. Wall
blocks have a darker return and attached damp patches. Connected filth collects
in seams, below plumbing and at bank edges; it is not decorative pickup-like
noise. The bright foam ink is no longer used by ordinary ground slime.

The water plane is dark gray-teal with asymmetrical short wavelets and calm
intervals. Wavelets translate laterally over the declared period; their
vertical position varies using the real reused tile identifier, avoiding the
previous rigid repeated rows. Pale silver/cyan inks are reserved for water
highlights and foam. `_fall_image` authors straight sheets with disconnected
falling streaks. The fixture module supplies the large and small actual pours,
with a broad liquid plane, descending glints and a clear splash/ripple impact.
No twisting two-stem or branch-like fall silhouette remains.

The floor drain is a low oval iron frame with unmistakable bars across a dark
recess, rather than a glowing gold treasure emblem. Bank tops have broad
light-facing coping, a shadowed retaining face, uneven attached slime and
short contact shadows. Foreground handrail strips remain seamless 16x8 OBJ
art in the existing gold/FX bank; the bridge gap and all existing anchors are
unchanged.

## Reference relationship

This pass follows the already-read six-PDF guidance documented in the art bible
and source notes, interpreted through the user's new feedback. Native silhouette
and material masses precede detail (Adafruit pp7,18; Palef pp3–7); clean pixel
cadence and restrained contour treatment follow Janes pp1–2,5 and Livresquare
pp7–12. Gray face/shadow separation, cool shadow/warm metal light, and material
specific highlights follow Janes pp2–5 and Livresquare pp15–24. Material-shaped
water/texture rather than arbitrary dither follows Galvan p4. These specific
Drain floor bonds, flow directions and plumbing designs are our interpretation,
not examples copied from those sources. No tutorial or existing-game pixels
were imported; all game drawings start at native indexed GBA sizes.

## Native review and corrections

The first material-only draft was reviewed at 1x in the full fixed 480x320 room,
and at 2x for floors. Two flag variants initially resembled concrete with
floating scratch seams; their joints were rebuilt as coherent brick/flag faces.
The third's unbroken vertical seams resembled wall panels; their joins were
interrupted and staggered. The fifth became a more distinct herringbone option,
then had its mortar contrast and two small seams reduced after the independent
reviewer found it excessively grid-like. The new surface water was staggered
using full IDs rather than a four-tile y cycle. Pale pouring-water inks were
lightened after the first fixture draft still resembled opaque cloth. The final
reviewer reports that the sheets, descending streaks and impact foam read as
liquid, and the independent fixture review considers the ladder arrow readable.
Motion must still be checked in actual mGBA; native source assemblies do not
prove runtime presentation or performance.

The old `_slime(...425,60,24,18)` storage-top deposit was moved to the crate foot
at `(425,92,18,6)`. The fixture module also removes the ambiguous pipe elbow
above storage. Crate tops remain recognizable wood. Dead superseded fixture
functions were removed from the main material painter after the new module was
installed; legacy catalogue paths resolve the installed current fixture hooks.

## Frozen validation

- Main material painter SHA256:
  `4cf8f2a0d0eeb0b64c808906c858c48cbd4ffc42600347c8a51f265e0058f86b`.
- Fixture module SHA256:
  `c148ceb7ca479cd76f0b82fdf1d6c02b930bb0be76c0982dee1ce71489a65c8a`.
- `terrain/validation.json`: 3,680 indexed tile-frame drawings checked at 16x16,
  legal indices0–15 and RGB555 colors; every active ground ID remains opaque.
  All five additional handrails are legal16x8 art; standard surface loops return
  exactly at phase8. The original contract JSON is byte-identical to v2.
- Five complete asset builds pass: Drain BG subtiles **591,587,592,595,577 of1024**,
  one Drain palette each; unrelated forest693 and mystery114 remain unchanged.
  These are encoded capacity measurements, not subjective quality scores.
- Each style has **30 actually changing active IDs** of38 declared animated IDs.
  Two old fall-top IDs, `swh_068/069` at worldx224..255,y32..47, now contain static
  upper grate because the water starts lower beneath the crossbar. Their four
  frames and hold contracts remain intact. The other six static reserved slots
  were already static; no fake pixels were added simply to force frame hashes
  to differ. `terrain/animation-difference.json` records the precise changes.
- Native room renders under `terrain/room-N-native.png` and nearest2x copies use
  actual reused-ID resolution and current NPC source poses. They omit runtime
  ambient glitter and are labeled source assemblies, never emulator screenshots.

Remaining tradeoffs: the fifth floor is denser; the fourth is intentionally
filthier; subtle floor joint contrast may depend on real display brightness.
Final real mGBA videos, packed-ROM checks, and user selection remain the relevant
next evidence before choosing one of these five treatments for production.

## Assembled-map correction after the first ROM pilot

The first packed pilot was technically exact but a full fixture review found
that reused floor IDs erased the small outlet's riser and mouth. The fixture
module now places the mouth on existing unique bank cells230/231 and the
falling sheet/foam entirely in unique animated water cell241. The bank and
collision remain unchanged; the whole open pipe survives actual tile assembly.
The two reused north-wall panels058/059 also previously erased the middle of
the long brass pipe. Both occur only in that same pipe at the same height;
they now retain the source pipe crop so its silhouette joins across the wall.
No unrelated occurrence receives a pipe. Actual `full_layers` crops verified
the fixes before rebuilding. The first pilot is archived, not relabelled as
final evidence. Final terrain SHA256 is
`913e22af37f33949d248675b8f3987daf17d989e0c7c8c04e32c76845ae8f561`;
final fixture SHA256 is
`1f7d4289575f8a4a933ac6fef1b37a5510308a1ed31c4815629cd9a0c5d8ea12`.
