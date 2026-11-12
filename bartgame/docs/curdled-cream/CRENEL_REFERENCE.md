# Mount Crenel reference and Cream depth vocabulary

Research recorded 2026-11-12 for the user's requested synthesis of Cream
study2's contrast/arches, study3/5's wall materials, and especially study5's
palette. This is a reference note for **original Cream artwork**, not a new
default art selection. Nintendo pixels are not copied into game assets.

## Sources actually inspected

**Public map image:**
[CandyCrystal's Minish Cap Randomizer tracker overworld composite](https://github.com/CandyCrystal/CandyCrystal_TMCR_Map_Tracker/blob/a3f1daa29a0ad5b95467e1c75209c36facc6c9a3/images/maps/overworld.png).
Downloaded from this exact pinned URL:

`https://raw.githubusercontent.com/CandyCrystal/CandyCrystal_TMCR_Map_Tracker/a3f1daa29a0ad5b95467e1c75209c36facc6c9a3/images/maps/overworld.png`

- File: `/workspace/setup/cream-depth/references/tracker-overworld.png`.
- Size:3320×2108 RGBA;12,250,261 bytes.
- SHA256:`763682c80622722246a7199e69d20832539655ead387526db7dbe5544cf603d2`.
- Actually viewed the top-left Mount Crenel portion and the three crops below.
  This is a screenshot-derived tracker composite, with room divider lines;
  it is not a fresh emulator capture, animation recording or native asset sheet.
  Do not derive original sprite dimensions, precise collision rules or
  animation timing from this composite. Its original capture provenance and
  any intermediate resizing are unverified.

Inspection crops are unfiltered source rectangles `(left,top,right,bottom)`,
not Cream mockups or delivered game graphics:

| Local filename in the same reference directory | Source rectangle | SHA256 |
| --- | --- | --- |
| `crenel-ledge-detail.png` | `(375,145,665,435)` | `e044a0bd91c36a4fdeff416d00c3d383e11757208f664305fb8525365013fc6d` |
| `crenel-long-cliff-detail.png` | `(0,105,390,550)` | `043438beacbb7c7d4a8838d43198c300abc02763ff4f55e20ea42ae78ead6159` |
| `crenel-base-shadow-detail.png` | `(255,550,655,800)` | `cadea40b5e8ee689b3f314109a8cd4f0ea1e40d101da8cefdfd66e85cbb7d3fc` |

**User-supplied annotated map:** the earlier inline Mount Crenel image shows
the same arrangement of terraces. The user's blue annotations mean lateral
travel/climbing and red annotations mean drops, including long commitments.
Those route meanings come from the user's explanation, not from a collision
test of Nintendo's game. Its attachment binary is unavailable in this
workspace, so no file digest is claimed.

**Access limits:** ordinary HTTPS requests through the inherited verified
proxy to `https://www.zeldadungeon.net/wiki/Mount_Crenel`,
`https://zeldawiki.wiki/wiki/Mount_Crenel`, and
`https://www.vgmaps.com/Atlas/GBA/LegendOfZelda-TheMinishCap-MountCrenel.png`
were denied at CONNECT with403. Their pages/images were not read; the guessed
VGMaps filename is not verified. No proxy bypass or indirect image-fetch
service was used. The accessible GitHub tracker supplied the viewed pixels.

## What the viewed map demonstrates

1. **A shelf has distinct planes.** Pale, comparatively quiet yellow walking
   tops sit above warm rose cliff faces. Dark undercuts and lower seams give
   the faces weight. Height remains legible without outlining each floor cell.
2. **Blocked and open edges differ in silhouette.** Many blocked rims carry
   raised toothlike rocks/rough vegetation. The low flat ochre sill/cap groups
   interrupt that fringe at the intervals identified as drops in the user's
   annotation. The sill is a structural break rather than an unrelated arrow
   pasted onto the walking ground.
3. **Height is composed over an entire face.** Long cliffs have extended
   horizontal bands, uneven vertical erosion and joined corner returns.
   Small marks repeat, but the dominant object is the continuous cliff mass.
   A tall textured climbing region contrasts with the broader, quieter wall
   planes around it; narrow ladders are another clearly different structure.
4. **Terraces leave useful negative space.** Small landing shelves and larger
   encounter platforms alternate. Open walking ground separates the patterned
   cliff, props, cave mouth and ladder instead of giving everything equal detail.
5. **Contact shading supports depth.** There are dark overhang recesses and
   cliff-base seams. This still image does not establish a special destination
   shadow under every jump. A truthful landing cue in Cream is the user's
   requested addition, not a feature attributed to this screenshot.

## Native Cream rules derived for this pass

These dimensions are original implementation targets for Cream's16×16 cells
and240×160 viewport; they are not measurements of Nintendo assets.

| Feature | Original native construction | Required gameplay agreement |
| --- | --- | --- |
| Permanent blocked rim | Raised uneven silhouette;2–4px lit top planes above a deeper dark underside. Join adjacent spans, with distinct side returns. | Draw only over solid rim cells. Never imitate regular climb grips. |
| Jump sill | Low, broad, comparatively smooth ivory/ochre edge; interrupted raised fringe; darker face below. Give the two-cell takeoff one joined32px opening with physical endcaps. | Only actual directed drop takeoffs receive the open sill. Ordinary wall gaps do not promise a jump. |
| Cliff face | Light top, dark undercut, broad warm middle, darker toe seam. On available wall space, distribute unequal strata/cracks over48–96px or larger compositions instead of repeating one tiny arch or vein every16px. | Variants preserve collision and do not paint a fake path across the wall. |
| Climb strip | Recessed shaft with regular, readable pale grips and clear top/foot joins. Surrounding cracks stay irregular and lower contrast. | Bright grip cadence appears only where climbing actually works. |
| Floor below a cliff | A shallow dark contact band,2–4px where space allows, broken by existing floor texture and material joins. | Structural shadow follows a real cliff base. It does not imply a particular jump route. |
| Actual landing | A modest flattened patch about24–32px wide and6–10px deep, using darker floor inks and retained grain; avoid a black center or fully enclosed pit contour. | Derive its center from the same arrival calculation as gameplay. Paint only on the destination's dry supported walkable floor and do not cover hazards, mechanisms or return paths. |
| Large arch relief | Compose one unequal recessed bay across the measured wall mass; use shallow broken relief, warm lit left shoulder and darker right/underside. | A decorative relief has a closed rock backing. Reserve a deep traversable mouth and approach for actual cave entrances. |

Keep study5's quiet pale ground and warm mineral planes. Study2 contributes
the strong plane contrast and architectural ambition; study3/5 contribute
facets, grime and irregular material boundaries. Do not simply stack all of
their detail densities. Violet should describe a few connected fractures,
with sparse bright cores and attached darker bruising; fresh walls show
mostly dormant cracks, sour walls expose longer lit segments, and deep walls
can carry branching light over a large face while the walking surface stays
recognizable. Offset and vary the cracks according to wall shape so the same
bright symbol does not advertise every cell boundary.

For a multi-screen drop, its landing is in the actual destination room, not
automatically on the nearest floor below the source sill. Use the route graph
and arrival helper as the authority, and keep local cliff shading separate.
A static shadow must remain readable as ground in both color and grayscale;
it must not hide a smaller object or falsely resemble a hole. Where room
features overlap its footprint, retain the feature and clip/omit conflicting
shadow pixels rather than move the advertised landing somewhere untrue.

## Review evidence required

Review matched fresh/sour/deep rooms in actual mGBA frames at1×, including a
blocked edge next to an actual drop, a short landing, a multi-screen landing,
climbing and both wall corner returns. Check the actual destination against
the ground patch. Whole-room registered mosaics help judge repetition but
must be labelled separately from a single live240×160 viewport. The reference
images above do not qualify the new artwork or traversal by themselves.
