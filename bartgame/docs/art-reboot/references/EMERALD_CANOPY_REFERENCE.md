# Emerald tree reference: crown volume and ground contact

Status: direct user reference for the new forest canopy revision. This records
what can be seen in the supplied image and how the new study will apply it.
It is not a claim of having fetched or decoded a Pokémon asset repository.

The user supplied an inline crop attributed to **Pokémon Emerald** after
rejecting the ten adaptive tree designs: the trees sat on a solid purple-black
field with no useful background detail. The crop was inspected in the chat.
There is no separately supplied original asset file or measured source atlas
for this reference. Exact original tile dimensions and palette counts are
therefore not asserted here. Original BARTGAME pixels will be authored at
native GBA dimensions and palette limits; the reference pixels are not copied.

## What makes the reference read as a forest

The primary object is the **leaf crown**. A compact rounded dome carries many
small connected fan-like leaf groups. The groups repeat a material vocabulary
while changing position and orientation across the dome. Upper and upper-left
clusters are light; lower and far-side clusters become a darker hanging skirt.
That creates a raised leafy volume with a visible top and near side.

A short trunk and small contact shadow sit under that crown. They support the
leaf mass without occupying its center. The eye does not have to interpret a
large bare Y-shape surrounded by an empty field to recognize a tree.

Neighboring crowns overlap. Their outer leaf tips and small notches interrupt
the boundary against the grass, and the same ground continues around the
short base. Dark pixels belong to the underside, gaps among leaves, bark and
contact shadows. They do not form an unrelated rectangular backdrop filling
the entire area assigned to the tree.

The small highlighted clusters share a few values. The surface is detailed,
but the tree still reads as one dome at normal size. Neither a uniform color
field nor high-contrast noise scattered over every pixel achieves that effect.

## Application to the forest revision

- Make dense, rounded, layered crowns the dominant mass in both healthy and
  infected pieces. Show occasional supporting wood and short ground contacts.
- Use leaf clusters and broad dome planes together: local leaf detail should
  reinforce volume rather than erase it.
- Large available spaces receive unequal overlapping crown groups. Small
  remnants get a compact crown or shrub drawn for their own scale. The
  reference's coherent tree vocabulary does not reinstate a compulsory 3×3
  repeating illustration grid.
- Keep shadows local to foliage undersides and actual contacts. Render the
  real stage-local grass or soil behind exterior alpha, including the small
  gaps near the ground. Replace the previous featureless undergrowth panel.
- Make deep sickness visible **inside the crown structure**: discolored leaves,
  dead patches, attached violet veins/cankers and luminous wet glints. Keep
  surviving green groups, with the established approximate 80/20 composition
  guide across a stand. A flat purple replacement dome is not the goal.
- Ground remains comparatively quiet and readable. The accepted gray dead
  grass, unchanged interaction meanings and Bloom visibility remain context
  for this canopy work.

## Review gate

Review a native small piece, medium tree and large crown first, against the
actual local ground palette. Then inspect real generated broad, isolated,
narrow and concave cases in mGBA before completing the release.

Reject a prototype if the large empty center and bare branches remain, if a
flat dark/plum rectangle merely gains a little texture, if circular leaf icons
form another obvious masonry grid, or if the whole screen becomes a noisy
purple wash. Dense alpha alone is not proof of foliage: it can be filled by a
flat backing. Source diagnostics may count leaf inks, transparency and large
constant-color regions, but the native room view remains the visual test.

Verify actual ground and foreground separately. The engine must not secretly
restore a flat BG2 underlay beneath the new alpha edges. Dense leaves should
communicate the solid forest mass, while overhead tips may partly cover Bloom
on legitimately walkable ground. Entrances and interaction approaches stay
visible and physically unchanged. Still images, source assemblies, resident
layer reconstructions and actual ordinary-input motion retain separate labels.

This is a new local reference-led study, not the user's approval of any
finished canopy treatment. Its findings supersede the previous canopy
exploration's claim that broad flat underbrush backing was an acceptable
visual solution.

## Native and actual-room findings

The first new source sketch replaced bare branching diagrams with leafy
crowns and short trunks. Its large piece still made a nearly even two-row,
three-column set of round caps, and regular small fan rows began to resemble
checker or fish-scale texture. The revised source uses unequal dominant and
supporting crowns, more overlap, varying fan spacing and quieter dome planes.

The first actual-room gate confirmed the main improvement but exposed two
remaining integration errors. Crowns extending beyond their source canvas
were clipped into ruler-straight carpet edges. In addition, the inherited
canopy ground fallback selected the ordinary path tile for large healthy
interiors. That tile is native floor, but its material is brown dirt; a test
of floor type alone could approve another mismatched rectangular backdrop.

The focused correction keeps whole hanging crown skirts within the final
canvas and exposes actual ground at their tips. The canopy-specific substrate
rule preserves a valid stored floor, then an actual adjacent floor, and uses
green grass when neither exists; sick grass remains the deep fallback. Genuine
stored or adjacent paths remain appropriate contacts. Other barriers keep
their existing rules.

All five second-pass native mGBA views have been inspected: broad healthy and
deep forest, a small isolated fragment, a narrow arm and separated/concave
patches. The featureless purple-black panel and invented brown fallback are
gone. Healthy masses read as dense crowns; the infected version retains that
leaf volume with gray/olive sickness, surviving green and attached purple
wounds. Shallow strips read as thickets, and small remnants have compact
crowns rather than miniature large diagrams.

This passes the focused blending gate for publication as a review revision.
Remaining visual caveats are explicit: some grid-aligned joins and short
repeated leaf bands remain; healthy leaf texture is fairly busy; gray/olive
infected crowns can suggest mossy stone at a glance. These observations are
not the user's selection of a final style. Frozen packed-source, actual
substrate, movement and file/provenance checks follow separately.
