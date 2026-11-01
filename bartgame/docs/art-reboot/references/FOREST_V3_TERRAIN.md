# Leafy canopy studies: eight ways to show infection

The user's latest review accepts the gray dead grass and rejects both the
healthy and infected canopy as unrecognizable. This pass rebuilds tree form
first, then overlays disease. Deep crowns retain approximately one fifth
recognizable living foliage. Existing gray turf, water, props, NPCs, Bloom,
equipment, interfaces, Drain and established glitter remain the comparison
context. These eight directions are exploratory, not a selected replacement.

## Basis and native construction

Read the root `AGENTS.md`, shared art bible, direction log, reference register
and prior forest terrain notes before authoring. The six previously read PDF
notes and native silhouette/value/line-control guidance remain the foundation;
no new website, reference-game pixel or missing PDF figure is claimed.
Horizontal branches are direct current user direction. Controlled horizontal,
vertical and diagonal pixel runs still serve the stepped curves and anatomy;
the earlier research is not recast as a universal ban on vertical lines.

Every picture is authored on its final indexed canvas: 16×16 metatiles,
32×32 connected canopy macros, 32×48 ordinary trees and 48×64 retained large
tree groups. There is no HD reduction, filtered edge, screenshot grading or
imported reference-game artwork. Integer enlargements are inspection views.

The first mutable prototype made its leaf lobes too shallow. In rows they
resembled plates or rails, even though the branches extended horizontally.
That construction was rejected. Substantial domed mother crowns, a dark
underside and pointed leaf sprigs made the ordinary trees recognizable. Real
room pilots then exposed another failure: wrapped lower shoulder lobes broke
the connected wall into four quarter-sized capsules, with a repeated black
diagonal seam. A readable standalone tree had not proved a readable forest.

The wall macro now contains one whole 32px dome, without wrapped quarter
shoulders, plus a short local bark fork/trunk over dense dark underbrush.
Exposed south faces receive the same short tree cue even when the semantic
boundary cuts through an upper macro row. One fork spans the two horizontal
quadrants; it is not a continuous black rail across the room. The ordinary
tree retains overlapping leafy shoulders, a short visible trunk and a
coherent grounded root collar. Broad and domed tree anchors are reused across
the eight studies, so the principal comparison is disease construction rather
than eight unrelated tree species.

Fresh unfrozen mGBA pilot 11 landscape views after this correction show visible
edge forks and larger leafy masses in healthy, mixed and deep rooms. The
boundary now supplies a tree cue instead of relying on the standalone tree
sprites to explain an otherwise ambiguous wall. Deep living-green clusters
connect purple infection back to foliage. Interior connected masses still
show a regular 32px rhythm and can feel hedge-like; broader natural forest
composition remains a tradeoff for review. These are actual pilot observations,
not a claim that the final frozen motion evidence has already passed.

## Eight disease constructions

| Local option / build | Name | Main blight treatment |
| --- | --- | --- |
| 1 / 11 | Veinbound Oak | Narrow branching vascular veins follow a bent lateral fork and leaf ribs. |
| 2 / 12 | Patchblight Beech | Broad irregular necrotic patches have dark wounds and purple inner edges. |
| 3 / 13 | Spore Drift | Localized directional dither islands and small attached purple spore groups. |
| 4 / 14 | Bracketwood | Overlapping horizontal fungal caps attach to a visible woody branch. |
| 5 / 15 | Violet Leaf Mosaic | Entire leaf fans become bruised violet while their leaf contours remain. |
| 6 / 16 | Black Sap Bough | Wet black sap collects along a substantial fork, with short purple rivulets. |
| 7 / 17 | Silkbound Crown | Pale parasitic threads span selected gaps between leaf masses. |
| 8 / 18 | Canker Bloom | Ragged flowering cankers grow from a recognizable leafy crown. |

All eight share an authored ink vocabulary. Their anatomy, coverage and
material cues supply the variation; they are not eight palette swaps. Purple
light remains attached to a tree. It does not become a loose pickup, new
ambient actor or replacement for gray ground.

## Green retention and blocked footprints

`canopy_macro()` keeps one connected living lobe crossing all four world
quadrants. Current native macro coverage is 20.61–20.80% living-green pixels.
This is an aggregate area measurement, not a quota for each tiny hardware
quarter or every screenshot. All four isolated 16×16 canopy quadrants retain
green after the rounded outer mask; the native isolated samples contain
22–41 living pixels each. The earlier two-island prototype left some isolated
quadrants entirely dead and was superseded before freezing.

Sick tree groups keep the corresponding healthy tree's leaf-volume planes,
with localized disease drawn over them. Ordinary diseased tree groups retain
about 20% living green across their painted extent. The legacy name `btree`
does not require an entirely leafless glyph: its lateral anatomy and a live
leaf clutch preserve the requested forest identity.

The six `forest_blight_tree0..5` connector IDs are fully blocked 32×48 wall
skins. They now assemble one actual tree with trunk and roots against dense
underbrush. Their root row is not a repeated crown quadrant, and it does not
show apparently walkable floor through a fully solid collider. Ordinary
FLOOR tree crowns retain transparency outside their silhouettes. The old
unplaced `btree_6..11` extensions still delegate to their accepted gray floor.

## Palette and packing contracts

`art/forest_concepts_v3_terrain.py` delegates every non-owned picture and every
existing bank to v2 option1. The existing `foliage` bank supplies healthy
leaves and bark without recoloring bridges or other foliage-bank context.
One additional BG bank, `canopy3_blight`, supplies diseased leaves, wood,
violet light and living-green indices 9–11. No OBJ bank changes.

`extra_palettes(variant)` exposes that bank. RGB555 quantization occurs at the
authored palette boundary. `pulse_palettes()` preserves the existing base
`blight` cycle and adds four states for the new canopy bank. Only new-bank
indices 5/6/7/13/14 pulse; living green, leaf volume, wood and other materials
stay fixed. Static geometry remains distinct from an authored palette pulse
or an existing animated tile's local bitmap phases.

The 47-case exposed-side/concave-corner grammar and four world-aligned macro
quadrants remain compatible with the earlier topology tables. Each 8px quarter
depends only on its touching edges and corner, allowing hardware tile sharing.
Canopy exteriors use transparent zero over the renderer's real floor.
Non-canopy water adjacency and the raised root arch delegate unchanged.

## Foreground and review boundaries

Horizontal branch fringes are genuinely transparent foreground pictures.
The north fringe retains its 12px central clear lane below the two-pixel
header. Longer leafy tips remain at the sides; this avoids a deep hanging
curtain above the route. A source alpha study alone cannot prove that Bloom
remains recognizable at every position or action frame. The engine's player
visibility handling and real mGBA traversal evidence own that guarantee.
The conservative shallow branch projection is less dramatic than a broad
canopy reaching far into grass; increasing that projection is a future local
art/visibility decision rather than an undocumented change in these studies.

Direct authoring checks exercised 7,000 native/alias/fringe cases across all
eight options: legal indexed shapes, unchanged delegated non-canopy pixels,
exact existing BG banks, all 47 adjacency combinations, the north clear lane,
green in every isolated quadrant, and stable non-light inks across all four
pulse states. Focused source catalogs and actual room captures provide the
separate final evidence. Early local source previews are mutable pilots and
are not relabelled as final gameplay.

Remaining review points are the visible rhythm of long connected walls,
recognition of small fungus/canker attachments, and the amount of body covered
by a foreground edge during ordinary movement and action. Rounded joins and
green ratios are necessary construction checks; they do not substitute for
an actual room's forest identity or readable player motion.
