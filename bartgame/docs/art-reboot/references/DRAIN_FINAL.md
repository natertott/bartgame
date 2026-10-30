# Final Drain synthesis

Status: a final area-art proposal assembled from the user's selected third-pass
components. The user requests one finished room rather than five more sewer
styles. Native UI studies remain a separate five-way choice. The room's grid,
physics, NPC feet, exit, bridge, flow channel and existing ambient glitter stay
in their established locations.

The shared art bible, decision log and source register were read before editing.
The six already-read PDF references remain applicable through G01–G18; no new
article, missing illustration or outside source is claimed in this iteration.
The latest user feedback is the direct evidence for the local choices below.

## Selected construction

| Family | Preferred study | Final treatment |
| --- | --- | --- |
| Pavement/debris | 1 and 5 | Quiet gray running-bond brick from1; a coherent herringbone repair panel from5 on the lower right; broken pottery and torn cloth in the retained debris sites. |
| North wall | 1 and 3 | Alternating broad gray courses with controlled cracks, damp seams and a clear lower ledge. |
| Broken pipe | 1/3, too hard to identify | Enlarged 18px cylinder with upper lit shoulder, collars, a missing section, exposed dark cut end, a falling leak and attached wet catch. |
| Forest ladder | 1 and 3; taller, larger arch; arrow above | 48×72 arched entrance,44px stiles and seven rungs; filled up-arrow at worldy14–24 directly above ladder. The new12px sparse HUD leaves it visible. |
| Cistern | 2; fix inconsistent arch shading | Preferred round bolted grate and split spillways; unified brass face with a narrow upper-left bevel and a right-side depth return. |
| Market | 1 and 3 | First-study striped canvas and third-study horizontal salvaged-board counter joinery. |
| Wizard corner | 2 | Worn rounded rug, chipped timber shelf and four candles; same NPC foot anchor. |
| Bridge | 2 and 5 | Fifth-study serviceable planks and second-study diagonal reinforcing repair. Surface cracks never claim an actual hole. |
| Upper railing | 2 and 5 | Rounded collars, squared repair details, attached tarnish and the original bridge gap. |
| Profile outlet | All previous rejected | Brass pipe enters from beyond the LEFT edge, faces right in profile, and pours rightward/downward into the actual river. Former front-facing right-bank ring is removed. |
| Storage | 2 and 3 | One braced crate, one plank crate, and a recognizably bunged/staved barrel. Grime sits near the feet instead of covering the wooden lids. |
| Floor drain | Any | Familiar subdued oval iron grate, dark recess and clearly separated bars. |
| Lower railing | 4 | Weathered low retaining rail and attached filth, distinct from the more polished upper handrail. |
| Side walls | Must differ from back wall | Narrow top-facing coping and dark inward return, with long cap joints. Neither side reuses a downward stack of north-facing block fronts. |

Frog and wizard remain the closest accepted identities: third-pass frog1 and
wizard1, which deliberately retained the earlier preferred frog1/pointed
wizard5 starting shapes. Their full animation IDs, palettes, head/body joins,
foot baseline and staff/flame anchor remain unchanged.

## Lighting and perspective corrections

Both arches use the same simple construction: one coherent brass face, a
continuous upper-left highlighted bevel, a narrow physical right return,
and a dark recessed opening/inner rim. No arbitrary broad x/y threshold turns
half an arch another colour. Short local speculars and small construction bolts
support the room's common upper-left light. This follows the established G06/G07
material-plane rules, and directly addresses the user's discoloration feedback.

The taller ladder has an enlarged opening, longer stiles and more rungs; its
arrow is a solid glyph above the rungs instead of a tiny ornate mark or a
side plaque. The smaller HUD makes the top of the scene available. Root's
runtime review must still confirm visibility at the actual northern camera.

Side walls now show a cap/inner-return perspective; the broad north-facing
masonry remains on the north wall. The bottom bank keeps a separate shadowed
retaining face. These forms communicate continuous room boundaries without
the old visual effect of a north wall falling down the side of the screen.

## Why placement clones are necessary

Earlier iterations drew complete fixtures on a source map, but reused IDs
then substituted a different first occurrence at assembly time. That erased
parts of pipes and reused north-wall fronts on side walls. Final mode uses
657 per-occurrence clones (`swh_f_g_XX_YY` / `swh_f_o_XX_YY`) with inherited
physical semantics. Source coordinates are therefore the actual final pixels
that enter the packed room. The original contract JSON and old eight studies
remain available unchanged.

The painter API is `palette()`, `paint(name, phase)`, `frame_spec(layer,x,y)`,
`full_layers(phase)`, `complete_layers(phase,period)` and `rail_sprite()`.
New liquid regions have explicit8-frame/8-update clocks, matching their
adjacent spill pieces. Every returned tile is indexed16×16/indices0–15; the
bank has sixteen exact RGB555 colours. All ground pixels remain opaque.

## Native review and capacity

The initial final source scene was inspected at1× and2× by the parent and the
independent validation agent. Both consider the profile outlet, enlarged
broken pipe, taller ladder/arrow, unified arch planes and side returns clear.
The herringbone panel reads as an intentional repair because its value stays
close to the surrounding pavement. Its denser texture remains a deliberate
local choice, rather than a palette-bright decal or randomly interleaved tiles.

`sewer-native-review.json` checks all657 placement IDs /1,554 authored frame
images, opaque ground, canvas/index range and RGB555 legality. Of130 declared
animated clone sequences,119 visibly change. Static reserved sequences are not
filled with meaningless pixels to manufacture change. The independent packed
review is separate evidence and does not reuse the builder's pixel packer.

An initial build needed1,066 resident subtiles because every animated clone
reserved a separate four-tile allocation. The integration pass shares only
animations whose COMPLETE sequence, hold and palette are exactly equal.
This preserves every per-occurrence image and all physical metadata, reducing
the final Drain to822/1,024 resident BG subtiles and69 distinct animated
allocations for130 declared animated clones. One Drain bank is used; forest693
and interior114 remain unchanged. These are capacity measures, not taste scores.

Source review images under `sewer-source/` include exact native/nearest2× full
rooms,14 fixture crops with nearest3× copies, and tick-sampled flow/leak/cistern
chronology. They are explicitly SOURCE assemblies, omit runtime ambient glitter,
and use representative unchanged NPC/Bloom idle poses. They must not be
presented as emulator captures. Actual mGBA evidence is produced separately.

Frozen painter SHA256:
`f6229d2aa7e0207b01b6c35be75884cbcdd6b7847ceedc945388b760360baf83`.

Remaining limits: final pipe/river motion and arrow/HUD interaction still need
actual camera review. Narrow coping and low-contrast seams should be checked
on real display brightness. The UI comparison remains exploratory; adopting
the final sewer does not select one of the five UI styles.
