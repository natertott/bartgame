# Forest prop cohesion — native authoring pass

This is a local forest refinement for the 2026-11-03 user request, not a new
art direction for the other eight planned regions. `forest_cohesion_props.py`
authors the existing sixteen-pixel BG identities directly at native resolution.
It follows the already-recorded tutorial/guide rules: connected value masses,
upper-left light, understated material edges, explicit ground contact and real
local floor visible through alpha. No new external reference or copied sprite
is claimed. Source swatch boards remain source illustrations, not emulator
screenshots.

The approved twelve-tree kit and its palette are unchanged. Ordinary rocks,
wood, ruins and litter now share its restrained mass/shadow hierarchy instead
of behaving like assorted inventory illustrations pasted on grass.

## Coverage

The module accepts all48 existing prop tile IDs and their54 native frames.
Forty-two IDs receive new forest BG art:

- Solid rocks have distinct broad, low or stacked masses. The nonblocking
  `mossy_stone` ID is now a sunk flat flagstone instead of a full-height boulder.
- Bones are a small connected, muted rib group rather than an oversized white
  diagonal pickup-like symbol. Their placement belongs to generator clusters.
- Stumps and paired logs use continuous dark bark, a light-facing cut surface,
  a short attached moss shelf and a compact contact footprint. Logs remain the
  existing32×16 paired construction; no detached twig decoration is added.
- Ruin walls, pillars and statues share a weathered stone construction with a
  visible top/near face. The generator must connect these to a landform or
  feature; art alone cannot justify an isolated column.
- Thorn brush retains recognizable branches and a localized violet wound.
  Bombable stone has a branching fracture. Webs are connected stretched silk
  with open windows. A locked gate uses a connected timber frame beneath its existing single
  large keyhole OBJ; its BG cells do not add extra lock symbols.
- Plates use a clear raised/depressed top. Lanterns/censers have a connected
  supporting structure, warm window/flame and modest footing. Springs, shrine
  ground, fallback entrances, fallback chests and stair recesses use the same
  matter/contact discipline.

The six explicitly retained IDs are `bush`, `rock_small`, `boulder`, `myst_pot`,
`door_open` and the legacy floor-only `relic`. All four liftable BG pictures remain exact
matches to their existing carried/thrown OBJ frames and physical OBJ palettes.
Shared OBJ chests, entrances, landmarks, liftables and their anchors are retained:
those readable drawings are used outside the forest too, and a global repaint
would change other regions. This pass improves their generated setting and
underlying floor rather than silently changing their identity everywhere.

All BG alias palettes retain the preceding bank values. No new palette bank is
introduced. Native validation covers every54 prop tile frame and all four
BG/carried identity pairs; packed residency and actual room composition remain
separate gates owned by the integration/review pipeline.

## Alpha and physical contracts

Transparent pixels are not a borrowed green rectangle. Most props already
render over their stored underlay. Two formerly opaque, non-prop IDs require
explicit local-floor rendering: `fence` must reveal the floor between its
beams, and `stairs_down` must reveal the floor outside its recessed opening.
A direct draw of those alpha corners on the lowest BG plane would reveal the
backdrop; the renderer therefore needs a real floor plus a transparent picture
layer. Webs, cracks and key barriers already use that layering pattern.

The `door_open` fallback is quiet opaque dirt only as a compatibility fallback.
The actual cleared barrier should restore the stored or neighboring floor; no
single source tile can correctly represent both dirt and grass in every room.
Nonforest tilesets must continue to pack the preceding profile31 versions of
shared canonical IDs and banks. The integration handles that area boundary.

Pictures retain existing IDs, frame counts and collision metadata. A shallow
statue/lantern base remains shallow; a full solid rock remains visibly substantial.
The compact litter and embedded flagstone pictures remain nonblocking. These
source contracts do not claim that all rendered arrangements are already good:
healthy/mixed/deep room captures, item use and actual ground/layer readbacks
are required before publication.
