# Forest room cohesion: independent review

Status: implementation review in progress. The current user request is to
refine forest generation and environment details together, so a generated room
reads as a place rather than a random collection of tiles. The previously
approved twelve native tree pictures remain the reference tree kit.

## Baseline observations

The three published profile31 room mosaics were inspected at native scale.
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

`tools/forest_cohesion_audit.py` reads the linked ROM's actual 4bpp tiles,
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
wrong-item optional pockets, deterministic rebuilds and Bloom's real10×8 feet.
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

`tools/forest_cohesion_runtime.py` uses actual mGBA input and disclosed navigation
fixtures for title, menus, region/zoom maps, forest/mystery/Drain handoff,
ordinary bush cutting and cache restoration. Required trial completion and
bomb/candle/cape barriers use actual game logic. The inherited combat fixture
chooses an enemy with a safe approach instead of waiting forever on an
obstructed first actor; it does not alter enemy health, event flags or rewards.

## Early findings

The first32-seed corpus covers800 generated rooms plus800 opened states.
Required fixture, gate, pocket, real-feet, determinism and cache checks pass.
Independent landscape checks expose53 bridge-quality failures, chiefly legacy
door-lane conversions producing deck segments without visible perpendicular
water, plus several final landing obstructions. Those failures were reported
to the generator author; they are not waived as acceptable randomness.
All1,756 observed lanterns have meaningful anchors. Of3,847 detail cells,
3,837 are within three cells of a material/feature context. This finite
proximity count does not establish aesthetic quality.

The first actual mGBA integration pilot passes80/80 checks, including all17
required-trial/item-gate checks and the live motif metadata across menus and
previews. These are preliminary findings, not frozen release evidence.

## Final qualification

Pending held source/build, repaired bridge geometry, final corpus, native
source/packed comparison and new actual mGBA room/movement evidence.
