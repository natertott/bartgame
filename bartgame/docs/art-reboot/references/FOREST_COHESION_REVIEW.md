# Forest room cohesion: independent review

Status: independently qualified against frozen source
`4024902d56c759ca124b2517c73f77e5234be66d`, profile 32. The forest generation and
environment details were refined together so a room reads as a place rather
than a random collection of tiles. The previously approved twelve native tree
pictures remain unchanged. [Actual mGBA room gallery and motion](../../../../art-review/forest-room-cohesion/README.md)
are separate from the authored native-source studies.

The reviewed 650,168-byte ROM has SHA256
`5fcf4cba1c6ab3a5af4575a5a05a49d9813457a02b4f5d16a7e3abc05e41566e`.
The matched prior profile 31 ROM is
`977f38406e3f5cf12e7108e3840356d305d364bd665bc0d9ef578ec8f5937e78`.

## Baseline observations

The three published profile 31 room mosaics were inspected at native scale.
Tree masses read coherently, but short rectangular water features look placed
into a clearing without an inlet, outlet or natural pond shape. Several dirt
loops advertise the coarse planning grid. Large pale bones and isolated grass,
rocks and columns compete with meaningful pickups or fail to accumulate around
any environmental cause. These are visual observations, not new external
research or a finding that every generated room has those flaws.

The existing art bible and already-read uploaded GBA guide supply the native
size, palette, connected-mass, ground-contact and clear-interaction rules. No
new commercial-game measurements or external tutorials are claimed here.

## Independent checks

[`forest_cohesion_audit.py`](../../../tools/forest_cohesion_audit.py) reads the linked ROM's actual 4bpp tiles,
flips, palettes, metatile descriptors and animation payloads. It protects all
approved tree source pixels, RGB555 colors, anchors and source-alpha masks.
It separately protects Bloom, all other shared OBJ sheets, UI/title/palette
payloads, the global BG palette, original physical metadata, other regions'
resolved tilesets and their original map entries. New forest-only aliases may
append; zero entries outside the forest do not imply an out-of-area redraw.
A clean source subprocess can compare every authored forest metatile/frame
with the linked atlas without importing the packer's deduplicator or parser.

The host corpus executes actual C room generation, collision and tree planning
against metadata extracted from that ROM. Hardware submission is suppressed;
it is a logic test, not an emulator render. Independent flood fills check
required approaches, all eight progression-item boundary cutsets, correct and
wrong-item optional pockets, deterministic rebuilds and Bloom's real 10×8 feet.
Opened gate/pocket states, paused-map previews and same-room bush-clear cache
behavior receive separate checks.

Landscape checks inspect the completed semantic room. Water components include
their real decks; single-cell fragments are rejected. Every contiguous bridge
run needs two dry, collision-clear, reachable landings and visible water beside
the crossing. Pond motifs require a connected substantial body. Lanterns must
anchor to a visible route, crossing, meaningful feature/interaction approach or
a connected clue chain. Debris distance to roots, water, embedded stone or
features is measured as supporting evidence, not a mathematical guarantee of
natural composition. Motif metadata is descriptive and never substitutes for
actual geometry.

Every actual call to `forest_paths_refine` is independently wrapped to compare
the physical type, collision mask and authored overlay of all 768 cells before
and after the cosmetic trail pass. Collected relic rooms are rebuilt with
their real persistent flag; their road mask and lantern positions must stay
stable while the prize disappears.

[`forest_cohesion_runtime.py`](../../../tools/forest_cohesion_runtime.py) uses actual mGBA input and disclosed navigation
fixtures for title, menus, region/zoom maps, forest/mystery/Drain handoff,
ordinary bush cutting and cache restoration. Required trial completion and
bomb/candle/cape barriers use actual game logic. The inherited combat fixture
chooses an enemy with a safe approach instead of waiting forever on an
obstructed first actor; it does not alter enemy health, event flags or rewards.

## Final qualification

Three separate reports use the same final source and ROM. The capture-only
report does not copy results from the host corpus.

| Evidence | Result | Coverage |
| --- | --- | --- |
| [Frozen host, source-art and scope audit](../../../../art-review/forest-room-cohesion/validation/audit-host.json) | 1223/1223 pass | 128 seeds × 25 rooms; actual C plus independent native-ROM decoding |
| [Actual mGBA integration](../../../../art-review/forest-room-cohesion/validation/runtime/report.json) | 80/80 pass | Includes all 17 required-trial, item-barrier and Heart-entry checks |
| [Independent capture audit](../../../../art-review/forest-room-cohesion/validation/audit-capture.json) | 567/567 pass | Eight final rooms, 72 native camera views and 504 native walking frames |
| [Capture helper's own report](../../../../art-review/forest-room-cohesion/actual/after/capture.json) | 338/338 pass | Fresh final source 402 capture; four water clips, 384 native frames total |

The host corpus checks 25,543 required approaches, 2,619 item pockets, 32,000
inventory/boundary cases, 1,600 real-feet room-state cases, 3,200 deterministic
rebuilds, 800 preview checks and 800 live-cache checks. It verifies 2,019,827
tree-root ownership cases across 1,216,122 placed trees. All twelve approved
tree frames occur, and state proportions shift toward sick/dead trees with
depth while retaining living green.

The completed rooms contain 1,351 water components and 46,080 water cells.
All 805 bridge runs pass their 1,610 landing checks; no isolated single-cell
water fragment or unanchored lantern is accepted. All 6,059 lanterns have a
visible route, crossing, feature or connected clue-chain context. Of 15,484
detail cells, 15,437 lie within three cells of a material/feature context;
the remaining 47 are reported, not relabeled as proof of natural composition.
Detached decorative terraces were retired; this corpus contains no ledge
cells. It does not demonstrate a new raised-landform system.

All 8,256 trail-refinement calls preserve physical cell types, collision masks
and authored overlays. All 128 relic collection/revisit cases preserve their
road masks and lantern positions. The six motif counts are 890 dry glades,
628 brooks, 723 ponds, 429 damp hollows, 402 ruined edges and 128 Heart arenas.
There are zero host failures.

Native source/packed comparison covers 939 metatiles, 1,049 frames and 268,544
pixels. It finds no mismatch. The approved tree pixels, colors, anchors and
alpha masks are exact. All 36 shared OBJ sheets, 20 protected scalar arrays,
global BG palette and other regions' resolved artwork remain exact. The
forest pass changes 308 old metatiles, retains 1,719 and appends 106 visual
aliases; this is not a claim that every existing tile was redrawn.

## Corrections driven by the review

The initial 800-room corpus exposed 53 bridge-quality failures. Actual door
lanes could produce lengthwise deck fragments or obstruct landings after
water planning. Door lanes and banks are now reserved before and after water
placement, and nearby crossings are consolidated. Follow-up checks caught a
lamp occupying an item-pocket approach and lamps anchored only to stale path
planning data. Pocket approaches are protected and lamps now use actual
visible trail geometry.

The expanded 128-seed run also caught three rare collected-relic rooms whose
lanterns moved on re-entry. Removing the prize too early changed placement
eligibility and later random draws. Profile 32 now retains a temporary occupied
relic marker throughout generation and removes it at the end for a collected
prize. Persistent item/reward flags remain authoritative. The final 128-seed
rerun passes all collection/revisit checks; the failed intermediate build is
not the reviewed release.

## Visual observations and limits

All eight final room mosaics were inspected: healthy, mixed, deep, pond,
damp-root-hollow, dry-glade, Heart arena and brook-crossing. Connected streams,
broader ponds and bridges joining actual dry banks now read as environmental
features. Quiet ground, clustered debris and preserved tree silhouettes keep
portals, prizes and lantern cues more legible. Healthy and sick floors retain
green and earth rather than becoming an undifferentiated purple field.
These are observations of the supplied scenes, not a claim that every one of
the 3,200 generated rooms was visually inspected.

Some trail turns and pond margins still reveal the 16px grid. Repetition remains
visible in dense tree masses. The deep floor deliberately stays restrained;
the tree kit supplies most of its dead-wood and purple-vein contrast. Existing
tree-base collision masks remain conservative around exposed trunks. None of
the proximity or reachability checks establishes aesthetic perfection.

Each 512×384 room overview is a registered mosaic of nine literal 240×160 mGBA
views. The review camera holds time and hides the HUD; it does not inject
terrain or paint screenshot pixels. Ambient glitter can differ at native
viewport seams. Untouched arrival/HUD frames are supplied separately. Enemy,
projectile and effect isolation is disclosed; the quiet Heart overview does
not depict its playable boss roster.

The three walking clips preserve 168 native frames each. Minimum visible Bloom
pixels are 79/95/90; minimum connected body pixels are 14/24/14. Literal missed
logic-update intervals are 2/1/0. These counts are disclosed rather than tested
against an unrelated historical timing allowance. They do not establish
frame-perfect performance or an unassisted complete playthrough. MP4s are
lossy viewing copies at approximately 59.73Hz; GIFs are inspection copies.

## Reproducibility

The [host statistics](../../../../art-review/forest-room-cohesion/validation/host/report.json)
and [literal host log](../../../../art-review/forest-room-cohesion/validation/host/run.log)
are published with the review. Final local reports are under
`/workspace/setup/forest-room-cohesion/`:

| Report | SHA256 |
| --- | --- |
|`audit-final-402-host/report.json`|`a4500407ad289ee37a81d9a1aae152117b7185a9404060901b016f9b39004ddd`|
|`runtime-final-402/report.json`|`c16b634487682eda1886136f4c43dc0c7f3021a77b7a2929ffeee7af71bccfcf`|
|`audit-final-402-capture/report.json`|`054a6360a5ec5b493fb6b3a4de3a96cfa359d7a47655edd3c90e85893e92ba27`|
|`final-after/capture.json`|`5985f2f18c22ec35e6b9a2200e052265a1749afb7f090a95bd9ca383db933075`|

Held helper SHA256 values are
`a9516f3705d306ea0ab07aa62b0dda7d3d50e9ccf83a5284b9c731e8a7431a73`
(audit) and
`d6e690395a46a2347e844ad0324ff02a0643600c8c9f30ab7be7a14056ac3be8`
(runtime). The capture helper is
`7e8d0735bd1c35f4fcc8f75601c55856786917cf4ecf1429e75e91ccf7503219`.
