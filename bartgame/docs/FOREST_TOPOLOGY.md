# Forest art, topology and depth contracts

Artwork and generation must be designed together. A convincing individual tile
can still fail when it becomes an isolated cell, a thin strip, an inner corner,
a boundary against another material, or a foreground layer above a character.
The earlier forest studies made those relationships explicit, but their
fixed-scale canopy artwork is now rejected. New profiles 19–28 use a map-first
composition pass. The room's logical mask is generated first; connected spaces,
available rectangles and visible inner edges then determine which native tree
compositions fit. Old profiles 0–18 remain historical builds.

| Family | Picture/layer contract | Physical/generation contract |
| --- | --- | --- |
| Water | Forty-seven exposed-edge/concave-corner combinations. Isolated ponds have transparent outer corners on BG1 over local BG2 soil. | Existing water remains hazardous; bridges/rafts remain connected crossings. No painted land square around a puddle. |
| Canopy | Native 16/32/48/64/96px drawings compose unequal tree forms to suit connected space. Large borders carry large detailed structures; compact remnants use compact art. Quiet edge joins are not the primary forest image. | Generate the logical room first, then measure and fit visual compositions. Protect features and floor approaches. Dense backing keeps negative space inside a blocked region from promising false passage. |
| Overhang | Broad lateral leaf/branch fringes project into neighboring floor and partly cover Bloom's upper body. | The projected floor remains walkable. Bloom must retain a recognizable visible silhouette, including rolls/jumps and intersecting overhangs. Protect interaction targets and their approaches. |
| Large trees | Transparent space outside crown/root anatomy, with upper/lower material planes. | Existing trunk/crown footprints remain authoritative; decorative gaps must not imply passage through a fully solid cell. |
| Ledges | Raised grassy lip, substantial vertical face, bottom contact shadow and consistent ends. | Existing one-way drop behavior and footprint remain. More visible height does not invent a second navigation level. |
| Logs | A coherent 32×16 drawing spans two cells, with cut end, bark and contact. | Both cells carry the solid footprint; placement checks clearance and required approaches instead of hanging an oversized image over walkable space. |
| Shrine/relic | Tall 16×32 upstand plus visible base/pad, separated from background material. | Use actual shrine/relic spots and state. Healing approach stays visible; spent and available states differ. Legacy unplaced source markers are identified honestly. |
| Key gate | Bars plus one centered large padlock/keyhole, drawn above the bars. | Existing single-key rule remains. Cleared gate cells reveal the real local substrate. |
| Other barriers | Distinct thorns, fracture and silk, with common clear-floor result. | Sword/bomb/candle remove their own existing obstacle; they do not leave unrelated brown trim or ghost collision. |
| Interaction approaches | Keep a visible standing space at chest latches, entrances and quest censers. | Later props reserve earlier targets and their fronts. Rare fallback furniture uses a small dry clearing attached to the actual entry component; required censers must all fit. No perimeter gate or existing item barrier is carved through. |
| Root underpass | A raised root span on BG1, with visible Before/Under/Emerged body states. | At least one complete 16px lane is clear north/under/south. It is a real lower passage; the roots are scenery above, not a claimed walkable upper deck. |

## Existing planes and sorting

The game's floor is **BG2**, foreground is **BG1**, and HUD/UI is **BG0**.
OBJ actor and held-tool priorities cooperate with those planes. A canopy edge
must cover a sword/hand consistently with the torso, while a shadow remains
attached to the ground. The visible layer can differ from the semantic room
cell: read-only visual-ground/overlay arrays expose the selected pictures,
while collision and saved progression continue to use semantic data.

Purple glow is a native authored four-phase BG palette cycle, limited to the
infection's declared inks. It does not recolor the selected enemies, equipment,
HUD or existing glitter. Source inspection cycles and actual engine timing
are separate evidence. Palette restoration after menus/area changes is tested.

## Iteration workflow

1. Record user feedback and the intended material/interaction meaning.
2. Inspect generated space first, including connected areas, narrow arms,
   maximal fitting rectangles, walkable-facing boundaries and protected
   features. Author distinct native silhouettes and detail for the actual
   small, medium and large footprints instead of a fixed repeating block.
3. Pack the real tiles and sprites; check BG banks/subtiles, OBJ stream use,
   EWRAM and OAM rather than trusting a picture alone.
4. Exercise generated physical layouts and approaches independently. Larger
   art needs either a matching footprint or an explicit overhead projection.
5. Capture real movement and item use. Check the actual displayed camera,
   hardware tiles/palettes and actor overlap instead of guessing from a still.
6. Publish natural rooms separately from diagnostic room fixtures; retain
   before/after evidence, exact native PNGs and the remaining tradeoffs.

The initial adaptive palette/prefab atlas is resident for a room: larger native
drawings are stored as ordinary 8×8 GBA subtiles, not redrawn or resized from
high-resolution images. The visual planner arranges complete compositions and
does not change the maze's collision merely to make a picture fit. Existing
authored 32×48/48×64 tree groups receive new drawings at their known footprints,
so original root obstacles do not disappear or move underneath unrelated art.

## Lantern placement and discovery: next generation pass

The adopted [lighting rule](art-reboot/ART_BIBLE.md#lighting-and-discovery)
requires fixtures to serve pathways, water crossings or specific room
features. Plan the destination first, then place a readable sequence along
its intended approach. A lantern trail can cross grass without adding a dirt
road; some content should have neither kind of guide. Preserve a deliberate
mix of path-led, lantern-led and unmarked discoveries.

Place fixtures beside the travel line so they leave bridge landings,
interaction fronts and item gates usable. Check foreground occlusion so a
trail's successive lights can still be spotted. Existing random off-trail
lantern and canopy-light placement needs a future generator pass; the frozen
forest studies predate this note and do not yet enforce it.

## Next topology questions

A bridge with both a usable upper deck and lower route needs explicit elevation
state, route entry/exit rules, separate collision and actor sorting. The root
underpass does not implement that system. More broad placement grammars can
also help large forest masses, stream banks and clutter feel less repetitive.
Those are ongoing design tasks after selecting a visual direction, rather
than reasons to hide unsupported geometry in an attractive source mockup.

The [engine notes](art-reboot/references/FOREST_V2_ENGINE.md) describe the actual
implementation; the [second forest gallery](../../art-review/forest-concepts-v2/README.md)
links source assemblies, natural rooms and explicit diagnostics separately.

The [adaptive canopy engine notes](art-reboot/references/FOREST_ADAPTIVE_ENGINE.md)
describe the new room-first visual planner and its resident native compositions.
Earlier linked galleries remain historical evidence, not selected canopy art.
