# Larger gilt HUD — runtime decisions

2026-11-04. Adopted implementation of the user's direct request for larger
items/buttons and minimap, sparkling gold borders, blinking player position
and physical-button feedback. The shared native-art and original GBA menu
research remain the reference foundation. No new commercial graphics or web
research are claimed by this runtime change.

## Geometry and reading locations

The render target remains240×160. Hearts/gilt retain their existing positions
and twelve-pixel height, with local dark instruments and gold bevels. A heart
pod grows with the actual heart capacity; unused space stays transparent.
Equipment instruments begin at x148/178/208, have29×20 painted extents and
leave a clear one-pixel separation. Each item is a separately authored16×16
OBJ at its pod's x+12,y2; item pixels are not enlarged through interpolation.
The associated A/B/L sits to the left in a9×11 medallion. Its native5×7 letter
is larger than the former3×5 assignment glyph. Bomb/arrow ammunition occupies
the left strip below that medallion, never hiding the item silhouette. Empty
equipment slots paint no pod or button.

The top-center x116..147 stays clear and there is no full-width opaque HUD
ribbon. Only the right-hand equipment group reaches20px tall. This updates the
HUD height used by ambient-glitter clipping, so unrelated world glints do not
float over the equipment. Matte dark backing, a dark outer lip and warm
upper-left gold bevel separate the instruments from both pale and dark land.
The brighter points are attached to their rims; they do not become loose
pickup-like sparkles.

The minimap uses a native32×32 hardware sprite at214,134. Its artwork occupies
24×24 pixels, through238,158 exclusive; the remainder is transparent. The room
field has20px pitch: five columns/rows at4px intervals, with3×3 painted faces
and a one-pixel separator. The spacing between room origins increases from3px to4px. The field receives
20px of space and the final24px framed instrument is50% wider than the former
16px complete map; the rim adds dedicated pixels beyond the room field.
The current forest room alternates every32 frames between a pale face and a
darker gold face, retaining a red center in both phases. In a mystery room the parent forest
cell blinks with a gold center, instead of incorrectly marking the entry. Seen/fog/goal meanings
remain the previous map meanings; secret content is not newly revealed.

A bottom-right24px map overlaps the dialogue's continuation arrow. It is
therefore temporarily absent while a textbox is active; the top HUD stays
visible. It reappears as soon as the modal box closes. Shops and full-screen
menus retain their own existing interfaces.

## Timing and memory

Physical `gKeysHeld` input illuminates the assigned medallion even when a
cooldown, current state or lack of ammunition prevents the tool from acting.
A six-frame release tail makes a short tap readable. This is visual feedback,
not an action timer: no player, weapon, resource or save field changes.
Gold-rim glints advance every eight frames; most of each individual rim's
cycle is calm. The current map face blinks independently every32 frames.
HUD painting/VRAM upload happens on a data, button-state or glint change,
rather than unconditionally every logic frame.

The first actual mGBA pilot exposed a full-redraw cost:44 missed logic intervals
in180 deep-room hardware frames and36 in144 walking frames. That pilot is
rejected. The implementation now caches the static2880B HUD frame. An
eight-frame glint tick restores only sixty packed scanline words and paints
its new highlights; changed buttons, hearts and quantities repaint only their
own rectangles. Full instruments repaint only on HUD restoration, equipment
change or heart-capacity change. The minimap writes directly to its native
4bpp cache; normal animation patches twenty rim pixels and nine current-room
pixels instead of rebuilding/packing a1024-pixel intermediate. The optimized actual mGBA pilot passes290/290 checks. Deep idle180 hardware
frames produces179 one-step logic intervals and zero missed intervals; the
144-frame walk produces143 one-step intervals and zero misses, matching the
retained baseline in both cases. The final frozen-source review repeats
these checks for publication.

The map uses the existing sixteen reserved OBJ hardware tiles1008..1023,
previously using only the first four. The three equipment allocations remain
876+s×16. Menu save/restore still covers their existing60-tile allocation;
no enemy sheet, portrait or menu-art address moves. A512B EWRAM staging buffer
holds the map, and a2880B static-frame cache replaces the old1920B base cache.
The existing384-tile VWF backing store is unchanged. Reserving90 HUD tiles
instead of60 leaves238 transient text tiles; even the broad130-tile dialogue
and a maximal nameplate remain within that budget. Full-screen menu/shop
pages continue borrowing the full pool and mark the HUD stale on return.

`BART_HUD=1` selects this pass. `BART_HUD=0` keeps the entire legacy HUD source
branch and original60-tile reserve. Build0 preservation and actual mGBA capture
results are recorded by the parent pass's independent validation, rather than
inferred from these implementation notes.
