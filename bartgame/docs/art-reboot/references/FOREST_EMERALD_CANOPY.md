# Foliage-first canopy authoring

Status: focused exploratory direction with the representative actual-room
gate completed. The previous ten adaptive tree anatomies are rejected as a
visual basis. This note records the source contract and completed source/room
corrections; final frozen capture and publication qualification remain separate.

## Reference and intended reading

The direct reference is the small Pokémon Emerald tree crop attached by the
user in this turn. It has been inspected visually in the conversation. No ROM
asset was extracted and none of its sprite pixels are copied. Its useful
principles are a dense domed leaf crown, interlocking small leaf fans, brighter
upper planes, a darker hanging underside, a small supporting trunk and localized
contact with real grass. Neighboring crowns overlap into forest mass while
exterior gaps expose ground. The leaf volume carries tree identity.

These observations supersede the preceding exposed-bough/flat-underbrush
approach. The new art uses neither the old drawing functions nor a solid
purple-black panel behind the tree. Quiet residual joins are textured leaves.
Renderer-owned local floor must remain underneath exterior alpha; no source
background color is baked into the asset.

## Native roles and materials

`art/forest_canopy_emerald.py` draws P-mode pixels directly on each final canvas:
16×16 small growth, 32×32 clump, 48×48 tree, 64×64 grove, 96×64 broad stand,
64×16 projected leaf skirt, 32×16 low understory/root contact, 96×32 shallow
border and 16×64 narrow stand. A separate backed 64×16 solid strip contains
actual foliage rather than a flat backing. The existing standalone obstacle
footprints receive new 32×48 and 48×64 leafy trees with small rooted trunks.

The broad stand has a dominant 57-pixel crown and unequal smaller crowns at
uneven depths. The set is not an even two-row/three-column carpet of identical
caps. The medium and small roles are their own native compositions; no rendered
crown is resized for use. Integer enlargement appears only in labelled source
inspection sheets.

The sixteen indexed inks are:

- 0: transparent exterior.
- 1: localized underside/contact contour.
- 2–3: short visible wood.
- 4–7: principal crown/leaf planes.
- 8–10: connected surviving-green leaf sprays.
- 11–14: attached infection/light, the only pulsing inks.
- 15: matte leaf-tip highlight.

`LEAF_INDICES`, `GREEN_INDICES` and `PULSE_INDICES` declare these roles for
source diagnostics. Pixel counts are supporting evidence, not an aesthetic
pass threshold. `stage_palette` explicitly quantizes every channel to RGB555.
Healthy crowns use greens and pale warm tips. Diseased crowns retain the same
leaf volume with sick gray-green/olive planes, surviving-green sprays and
localized violet fissures/cankers. Infection is attached to leaf groups rather
than a large bare Y-shaped trunk. Existing ground and non-canopy palettes are
outside this module.

## Source critique so far

The first prototype established foliage-first volume and short trunk contact,
but its large stand used an even six-cap arrangement and its fan texture read
as regular fish scales. The second makes crown sizes and overlap unequal;
its quiet patches were then too broad. The third uses pointed paired leaves,
underside-only shadows, unequal row/cluster spacing and smaller quiet regions.
This retains detail without a closed dark ring around every leaf group.

The source preview uses the actual profile6 `moss0` and `blight_floor` source
substrates and is labelled SOURCE. It is not an emulator screenshot. Actual
healthy/deep rooms, isolated cells, thin arms, component edges and walk-under
motion remain required review evidence. In particular, a passing native-index
check cannot establish natural contact or hide an unattractive room-scale
pattern. The renderer's logical solid region and drawn alpha are distinct;
large internal clear-looking holes inside impassable forest are unsuitable.

The first actual profile29 gate confirms dense leafy tree volume and removes
the flat purple-black void, but it exposes straight cutoffs on broad stands.
The source cause is crowns pasted beyond the large piece bounds: their lower
skirts were cropped into a carpet edge. The fourth contact pass keeps the
same native leaf construction and palette, placing complete unequal crown
skirts inside the hero/grove/border/column canvases. Only scattered leaf tips
meet their first/last rows. The hero retains about 89% painted coverage and the
grove 86%, with dense overlapping interiors; this is an organic contour change,
not a constant rectangular inset. Exterior grass glimpses are intended as contact slivers; actual review must
check that they do not suggest a clear route through solid forest. A revised
actual-room gate must verify both outer contacts and neighboring stand joins.

The solid 64×16 narrow strip receives the same whole-skirt correction: three
unequal shallow crowns end inside its canvas, rather than a cropped full-width
leaf bar. The projected branch retains its naturally hanging bottom silhouette.

## Second actual-room gate

All five second-pilot natural views were inspected at native 240×160:
broad healthy forest, broad deep forest, isolated growth, the shallow riverbank
arm and separated/concave groups. The new leaf volume survives at room scale;
organic complete skirts meet real green grass or the retained sick ground.
The purple-black backing is absent. The small standalone trees retain a
visible supporting trunk and localized contact; shallow solid strips read as
leafy hedgerows with unequal tips.

The engine also corrects the new profile's absent-underlay fallback to local
grass instead of unrelated dirt, preserving valid stored/neighbor substrates.
That renderer change is documented separately; the source art alone did not
fix the brown substrate exposed by genuine alpha.

This gate supports freezing the focused direction for review. Remaining
limitations are visible: dense bright fan texture is busy, some joins retain
the logical grid, and gray/olive deep foliage can suggest a stony surface.
Those are candid review tradeoffs rather than an all-seed aesthetic claim.
No additional art redraw is required by this gate. Final frozen native/source
and runtime evidence will retain their separate build/hash provenance.
