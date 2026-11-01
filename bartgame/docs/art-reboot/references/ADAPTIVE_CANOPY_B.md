# Adaptive tree directions 6–10

These are original native GBA drawings for the map-first canopy brief. The
user rejected the former fixed-size repeating canopy studies. The current
work therefore treats a footprint as a drawing brief: a root remnant, a
complete tree, a shallow border and a large grove tell different visual
stories. None of these images is a resized or cropped 16/32px repeating tree.

The direct user feedback is the reference for this change. The existing read
pixel-art notes still guide silhouettes, clustered values and upper-left
lighting; no new website or unavailable reference figure is claimed here.
All graphics use final-size indexed pixels and the shared sixteen-ink RGB555
bank from `art/forest_canopy_adaptive.py`. Grey ground and unrelated assets
are outside this module's ownership.

## Directions and native anatomy

| Direction | Large-space anatomy | Small-space interpretation |
| --- | --- | --- |
| 6. Fallen Crown | One heavy fallen trunk/rootball, unequal woody forks and a broad canopy at one end. Living foliage grows at the edge of larger dead leaf planes. | A broken root fork or low stump; thin walk-under limbs can remain mostly bare wood. |
| 7. Lightning Cleft Oak | A split two-stem oak with unequal lateral limbs and a recessed central wound. Purple veins follow its actual vascular forks. | A split sapling or small fork, with a clear root contact rather than a tiny whole grove. |
| 8. Pale Birch Congregation | Three leaning pale trunks of different heights share a loose connected crown. Broken dark lenticels and lower-root infection distinguish bark from generic glowing columns. | One pale bent sapling, or a two-stem clump where the footprint permits it. |
| 9. Black Cedar Cathedral | A large conifer and smaller companion use unequal tapered needle shelves. The central trunk/branch hierarchy dominates the attached infection. | A young conifer spray, a bare needle-bearing branch or an explicit narrow trunk strip. |
| 10. Sorrow Arch Elm | A broad bent trunk sweeps into lateral boughs, with asymmetric foliage and a high recessed bark seam. The curve is woody anatomy rather than a rectangular entrance. | A compact curved trunk or root remnant, with the native root baseline retained. |

The nine fitting roles are `small` 16×16, `clump` 32×32, `tree` 48×48,
`grove` 64×64, `hero` 96×64, `branch` 64×16, `roots` 32×16,
`border` 96×32 and `column` 16×64. Each is drawn on its final canvas.
The shallow 96×32 border has long lateral anatomy designed for that space;
it is not a tall 96×64 hero clipped in half. A native narrow column likewise
has a coherent trunk strip rather than a rotated horizontal branch.

Separate 32×48 and 48×64 `authored_tree` groups keep the old grouped-tree foot
baseline at the bottom center while replacing their rejected artwork. Their
branch/crown arrangements are independently authored for those dimensions.
Alternative groups change native geometry without mirroring the lighting.

## Material and composition

Wood uses fixed dark, side and lit planes. Pale birch uses ivory and warm wood
shade; its trunk does not borrow the leaf inks that become green at healthy
depths. Leaf planes 5–7 change from green to dead plum with area depth; surviving
green roles 8–10 remain visible. Infection roles 11–14 are attached to branch
forks, bark seams and growth. They are subdued bark/dew at healthy depth and
purple light at deep blight. The approximate green fraction is a whole-mass
guide, never a reason to put one identical green pad in every logical tile.

Large foliage has room for additional uneven fan groups and internal shadow
breaks; small sprigs use only a few deliberate pixels. Rootballs and primary
limbs have more mass than forks and twigs. Light-facing wood was lifted in
the shared palette after source critique, so neon cannot become the only
visible structure. A small fungus on the Fallen Crown is positioned directly
on the log underside; a fixed lower-screen coordinate had made it appear to
float like a pickup in an early source draft.

The main module supplies subdued blocked underbrush behind the transparent
anatomy. This preserves the apparent solid forest footprint without replacing
large tree drawings with a row of little leaf symbols. The `branch` role
remains genuinely transparent for permitted walkable foreground projection.
Placement, clipping, coverage and player visibility belong to the room
composer; an attractive isolated drawing is not evidence that those work.

## Review status and remaining gate

The first Fallen Crown source draft had a thin-looking primary limb and
several similar green-centered pads. Independent critique led to a heavier
primary log, one chunky rootball with three unequal root contacts, merged
unequal foliage planes and simpler bare branch roles. The revised native
anatomy passed the source-only gate for a map/actual-room pilot.

The five 96px hero drafts have distinct source silhouettes: a fallen tree,
split oak, birch grove, conifers and bent elm. The critic specifically asked
that Cedar needle tiers avoid becoming straight bright rails, and that the
Elm bend retain readable wood planes rather than doorway geometry. Native
leaf-fan detail and the shared warmer wood planes address those concerns.

All 45 role images and twenty alternate grouped-tree images have legal indexed
inks/dimensions; grouped trees retain a painted bottom-center root contact.
This is source validation, not a final aesthetic or hardware pass. Actual
generated small, shallow-wide, corner and large-border components must be
reviewed before these ten directions are called complete. Source previews
are labelled separately from mGBA output. No previous rejected canopy art is
used as a new visual foundation.

The first actual mGBA profile-19 integration pilot was also inspected. That
pilot uses direction 1, not these five directions. It confirms that the new
large-tree anatomy can read as forest, while revealing a common boundary
problem: the initial underbrush backing forms rectangular pale bars and the
old contact treatment leaves a repeating wavy baseline. The common module and
room compositor are addressing those issues before judging direction 6 in an
actual room. This observation does not count as an actual-render approval of
directions 6–10.
