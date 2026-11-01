# Repeated forest trees: native authoring contract

Status: twelve source trees have passed the reference/source direction gate.
Actual in-game planting and ground contact still require the final emulator
review. These are tree assets, not another large-canopy redesign.

## User scope and reference

The current user asks for repeated trees with a few varieties, healthy/sick/dead
states, palette iteration and ground blending. The stated “2x2 pixel” and
“1x2 tall” sizes are interpreted as gameplay tiles: 32×32 and 16×32 pixels.
That interpretation was stated to the user before authoring. The current tree
request supersedes earlier advice about large bespoke canopy compositions for
this pass; it does not authorize revising unrelated scenery or Bloom.

The supplied **GBA_Sprite_Art_Guide.pdf** has been read in full. Its figures on
pages 3, 5, 6, 8, 9, 10 and 12 were inspected directly. Its game readings and
proposed size ranges are interpretations, not universal commercial-game rules.
No linked book or external tutorial is claimed as newly read here.

The specific applications are:

- **Pages 5 and 12, masses before marks:** rounded healthy trees use a few
  unequal connected crown volumes. A few leaf lips explain material; there is
  no repeated fan grid, salt-and-pepper texture or ring around every leaf.
- **Page 6, context and transparency:** a clean native alpha edge reveals the
  actual ground. Only a narrow root/contact shadow is painted. No floor-colored
  rectangle, light fringe or opaque black/purple matte is part of a tree.
- **Page 7, state beyond hue:** the sick form loses crown volume, sags and
  reveals a branch. The dead form has a bare broken fork silhouette. Neither
  state is simply a recolored healthy image.
- **Pages 8 and 12, canvas versus collision:** 32×32 and 16×32 are native art
  canvases. The fixed origin is explicit; an engine must choose collision
  independently. These trees do not declare a new invisible solid rectangle.
- **Pages 9 and 10, contact and light:** the trunk/root remains at the same
  ground point in all states. Upper-left planes are brighter, hanging foliage
  is darker, and bare wood has only a restrained light-facing grain strip.
- **Page 11, conversion contract:** the palette order, transparent index,
  dimensions, state identifiers and anchor are explicit before import. All
  pixels are authored at native dimensions; integer enlargement is inspection.

## Twelve pieces, one family

`art/forest_tree_study.py` owns the new source pixels.

| Footprint | Variety 0 | Variety 1 | States |
| --- | --- | --- | --- |
| 32×32 / 2×2 tiles | Round oak | Crooked oak | healthy, sick, dead |
| 16×32 / 1×2 tiles | Small poplar | Forked birch | healthy, sick, dead |

Each tree has at least a one-pixel transparent external margin. The broad
origin is `(16,30)` and the narrow origin is `(8,30)`, measured from the top-left
of the native canvas. State changes keep that origin fixed. The sick and dead
silhouettes retain the matching variety's trunk flow, while showing an actual
change in foliage and branch structure.

The first broad healthy sketch read as one dome/cloud. Source critique changed
it into three unequal connected lobes with a small shaded overlap and visible
short trunk fork. The first narrow healthy sketch was too popsicle-like; its
revised crown has unequal lateral tiers. Second varieties are newly drawn
asymmetric forms, not horizontally mirrored first varieties. Bare branch runs
were moved inward where a thick contour touched a canvas edge.

The deliberate remaining source tradeoff is simple rounded foliage. The
source critic recommends judging that at 1× beside Bloom, rather than adding
texture to make the editor view look busier.

## Palette iteration and floor relationships

All twelve pieces share **one sixteen-entry RGB555 bank**, named
`forest_tree_study`. Healthy, sick and dead trees can coexist without a palette
swap. Index zero is transparent and carries no visible background color.

| Inks | Material | Colors |
| --- | --- | --- |
| 1 | forest contour | `#183028` |
| 2 | local ground contact | `#283828` |
| 3–5 | dark, middle and pale wood | `#403830`, `#786048`, `#b0a078` |
| 6–9 | shaded, middle, light and tip greens | `#204830`, `#487840`, `#80a850`, `#b0c878` |
| 10–12 | sick olive planes | `#505030`, `#889050`, `#b8b078` |
| 13–15 | attached infection and tiny glint | `#582078`, `#b848e0`, `#f0d8f0` |

This extends the existing greens, olive dead grass, amber wood and violet
infection rather than introducing a separate global art palette. The current
profile6 grass base is `#385838`; the contact ink is closely related to its
deep green shadow and exactly matches an existing sick-floor shadow role.
Tree middle/light greens sit above that quiet floor in value. Sick foliage
shifts toward warm olive instead of a gray stone crown. Dead wood becomes
paler and branch-shaped, while the contour/contact continue to relate it to
the same floor. Bright violet is limited to attached wounds/cankers; it is not
an outline on every branch or an unattached pickup-shaped flare.

Every color channel is a multiple of eight at the authoring boundary. The
module returns new palette lists and image copies so an importer cannot mutate
the cached source art. Transparent index zero is also recorded in PNG metadata.

## Import API and budget

- `palette(name=None)` returns the sixteen source colors.
- `tree(size='broad', variety=0, state='healthy')` returns a P-mode native image.
- `specs()` returns twelve records containing name, size category, variety,
  state, `size_pixels`, width/height, palette, transparent index and fixed anchor.

Six 32×32 4bpp pieces use 3,072 raw bytes; six 16×32 pieces use 1,536. The total
is **4,608 raw bytes / 144 8×8 subtiles**, before packer deduplication, plus the
shared 32-byte palette. This is the tree-library budget, not a claim about the
complete area's resident tile or object usage.

The SOURCE previews under the review workspace show native pixels and labelled
3× integer inspection over actual existing `moss0` and `blight_floor` source
tiles. They are not emulator screenshots. Final packing, repeated planting,
other floor contexts and comparison beside Bloom remain separate evidence.
