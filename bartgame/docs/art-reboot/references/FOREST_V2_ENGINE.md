# Second forest pass: terrain joins and real depth

The latest user review explicitly authorizes changes to the boundary between
procedural placement and native artwork. These features are enabled only for
optional forest profiles **6–10**. Production profile 0 and the first five
comparison profiles retain their previous generation and rendering paths.
The read-only `gForestV2DisplayedCamera` records scroll values submitted with
the actual hardware frame, rather than the next eased camera update.

The source art remains authored at GBA pixel sizes; this is not a screenshot
filter or a high-resolution illustration reduced into tiles.

## Semantic terrain and rendered pictures

`gRoom.ground`, `gRoom.overlay`, their stored underlay, and the quarter-cell
collision grid remain the authoritative gameplay data. Canopy and water
pictures are selected from physical neighbors in `room.c`; the original
semantic IDs are not replaced by decorative aliases in the room or save.
`gRoomVisualGround` and `gRoomVisualOverlay` record the exact metatile IDs sent
to the two hardware tile maps, so probes can distinguish physical and visual
representations without guessing from screenshots.

The renderer uses the usual four exposed-side bits, N=1, E=2, S=4, W=8.
Concave gaps use NW=1, NE=2, SE=4, SW=8 and are allowed only when both adjacent
cardinal neighbors are connected. This yields **47 valid blob combinations**.
Healthy and blighted canopy masses connect across their common boundary.
Authored full black-tree wall skins connect to canopy but retain their large
complete drawing rather than being rewritten as generic foliage.

Canopy artwork has four macro quadrants, selected by
`(x & 1) | ((y & 1) << 1)`. A connected 32×32 mass can therefore carry a few
larger wounds rather than repeating one purple glyph every sixteen pixels.
The appended table contains 2 material kinds × 4 macro quadrants × 47 shapes.
Individual 8×8 quarters are still deduplicated by the normal asset packer.
Every alias records its parent, masks, quadrant, palette and frame contract in
the generated coverage report.

The same 47 combinations cover water's exposed banks and concave joins.
Fully isolated cells use rounded pond artwork on BG1 over the real local BG2
floor, so transparent corners also blend on dirt and sick grass. Bodies and
held tools are promoted above that isolated water surface unless an actual
foreground canopy occludes them; the physical water remains hazardous. If a
meaningful authored crown already occupies BG1, that foreground is retained
above a full water surface rather than revealing a backdrop hole. Lily and foam variants
retain their two additional isolated pictures. Original named side/corner
water and new aliases call the same painter. For profiles 6–10 only, exact
whole-animation deduplication reuses payloads with identical pixels, timing
and palette assignment; similar-looking moving surfaces are never merged
merely because their first frame happens to match.

## Two layers make actual overhangs

Rounded canopy silhouettes are transparent BG1 pictures over a local BG2
substrate. Their outside corners therefore reveal soil instead of painting a
green rectangle onto a dirt boundary. Stored legitimate floor is preferred;
wall cells otherwise infer an adjacent lane or the area's floor. This is a
bounded material rule, not a claim that two arbitrary contradictory floor
materials can be blended perfectly by one cell.

Transparent root silhouettes likewise reveal their stored floor. Full-cell
SOLID black-tree wall skins keep a dense, connected visible wood/canopy mass:
large apparently walkable holes are not painted inside blocked cells.
Ordinary tree crowns and their existing smaller root footprints retain their
authored walk-under geometry.

A thin additional canopy fringe projects into adjacent walkable floor through
BG1. North-facing foliage occupies only the upper few pixels; side leaves are
narrow. The center of the route and the player's feet remain visible. The
projection is omitted around chests, quest givers, relics, shrines, pocket
rewards, mystery entrances and their approaches, and never replaces an
existing meaningful overlay such as a switch or portal.

Bloom and his held sword, shield, lamp, bow and carried object share the same
terrain priority. When their visible bodies intersect a foreground canopy,
fringe or root arch, their world priority remains behind BG1 even if flat
litter would otherwise promote them. The ground shadow stays on the floor.
HUD and dialogue objects do not pass through this world-depth predicate.

One bounded readability exception handles Bloom's natural roll-wall recoil.
The existing physics switches to NORMAL before its small airborne bounce
settles, which could lift the entire compact body into the low fringe. Only
that player state with positive height, grounded over dry floor carrying a
rendered low-fringe alias, draws body and held tools in front of the leaf edge
until landing. Its shadow remains behind on the ground. Ordinary walking,
rolling, jumping, full tree crowns and root arches do not use this exception.
The same explicit player-only modifier runs after terrain sorting for held
parts and after the final generic actor sort for the body, so the second
environment pass cannot split their priorities. It never changes non-player
actors or explicit effect priorities.
This is coarse GBA layer sorting for a brief readable recoil, not a new height
or collision rule; no animation pixels, physics, timers or z values change.

## A real lower path beneath roots

The generator can place one raised two-cell root arch above an existing
trail where solid banks support the span. Its two logical overlay cells have
FLOOR type and zero collision. A player can genuinely walk beneath the
foreground roots; no invisible barrier or artwork-only crossing is introduced.
At least one lane must have zero-collision floor north of, beneath and south
of the span. Its two-cell picture can therefore cover a one-cell lower route;
probes choose the actually open lane center rather than assuming the central
seam is traversable. No two-cell-wide clearance is promised.
Placement uses the existing trail and event clearance, a deterministic hash
rather than consuming extra layout RNG, and excludes reward/NPC approaches.

The upper wood is **scenery**, not an accessible second route. Existing river
bridges remain ground-level bridges over water. Full walk-over and walk-under
bridge routing would require explicit elevation state, collision selection,
entry/exit rules and map semantics; that system is not claimed by this arch.

## Props match their spatial claims

Scattered one-cell logs are promoted to the existing `hlog_0` / `hlog_1`
two-cell kit. Both cells remain truly SOLID, and the existing plain-ground fit
and connectivity guards must accept the complete two-cell footprint.
Transparent corners expose the actual stored substrate. Existing chunk-based
hollow logs already use this safe pair and now share its new art.

The independent large-seed test found a late-pass interaction: required lane
repairs or event placement could replace one of the two cells after the log
was safely stamped. A final integrity pass now removes only such orphaned
halves and restores their stored dry floor. It never recreates a missing half
over a repaired passage or feature, and complete pairs remain untouched. The
pass runs after every semantic repair and material skin, before the optional
root arch and rendering, and consumes no RNG or progression state. Seeds 88
and 240 are named regressions; the full seed/room audit checks final pairs,
collision, required approaches and item-gated pockets together.

A new 16×32 streamed `forestlandmark` sheet has four frames: relic,
shrine-available, shrine-spent and key-lock. Original sheet IDs stay stable;
it is appended after the final Drain strip. Available relic markers are
anchored to the real `gSpots.relic` pedestal (which is logically MOSSY_STONE
with a pickup, rather than the old unused RELIC tile). Shrine art stands on
the existing statue's footprint; the healing pad one cell south remains a
walkable activation surface. The larger picture suppresses the small legacy
statue instead of doubling the furniture.

A locked pair of gate cells shares one large upright padlock and keyhole.
The two BG cells contain bars without duplicate keyholes. The lock remains at
foreground priority one so those bars cannot hide its keyhole when Bloom
approaches from the south. Opening the gate
removes the marker. This does not change the existing single-key cost.
Relic/shrine/lock images reserve only their required streamed frame slots,
within the existing world OBJ range; menus and HUD keep their reserved space.

Wooden chest B adds closed/open frames 6 and 7 after the six existing chest
frames. A wooden reward uses B when `hash32(seed, cell) & 1` is set; no layout
RNG is consumed and no chest reward tier changes. Both A and B are therefore
real game alternatives rather than source-only ornament proposals.

## Clearing and glow

Thorns, cracked stone, silk and key gates all restore their actual local
underlay when removed. Previously some callers supplied grass, some trail and
some a painted DOOR_OPEN tile. The new path intercepts those cosmetic fallbacks
and restores stored floor. Regenerated already-open crack/web/key gates use
the same trail as the cleared lane. Physics, key consumption and world flags
remain owned by the existing gameplay actions.

Static black wood and veins gain an authored four-phase BG-only glow ramp.
`pulse_palettes()` declares the changed inks; generated tables map each bank
to the resident tileset's physical slot. While playing in forest/interior
areas, phase `(gFrame >> 3) & 3` loads one of those exact RGB555 ramps. Wood,
soil and interface inks stay fixed. No OBJ bank, Drain palette or original
white sparkle ramp is recolored. Existing tile animations retain their clocks.

## Review and limits

These are unselected prototypes, not adoption of a final forest design.
Required review includes isolated/concave canopy and water, macro-cell joins,
dirt/sick-soil abutments, real foreground body/tool/shadow occlusion,
underpass walking, log connectivity, larger landmark foot anchors, both wood
chest states, one-lock gates and identical cleared-floor results. Diagnostic
terrain fixtures must be labelled separately from naturally generated rooms.

The first draft packed the forest into 848/1,024 BG subtiles and ten/twelve
world banks, with 73 animation allocations; Drain remained 822 tiles/one bank.
The draft C build succeeded, with total BSS 235,748 bytes, including 4,096
bytes for visual-map diagnostics. These are draft measurements, superseded
by the final frozen build and independent source/ROM/runtime audit.
