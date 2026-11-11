# Curdled Cream: native art and physical rooms

This is an added area. Existing Forest, Drain, Bloom frames and their palettes
are preserved. The current user's annotated Mount Crenel reference informs
climbing, terraces, cave folds and committed drops. Its graphics are not copied.
The shared art bible remains authoritative; these ivory mountain materials are
local choices rather than a replacement palette for the other regions.

## Native asset contract

`art/cream_terrain.py` supplies 142 new 16×16 metatiles, with eight added 16-colour
RGB555 banks. Quiet ivory/curd floor stays readable at all three corruption
levels. Approach paths retain the same ivory substrate with light scuff marks,
so generated route rectangles never read as pasted brown blocks. Ochre shadows and irregular horizontal strata describe the cliff faces;
the deepest stage adds luminous purple veins while preserving pale walkways.
Distinct side faces avoid treating the top wall as a wall sliding down the sides.
Continuous climbable fissures contain regular, clearly lit handholds. Only real
climb/cave approaches receive lamps. Mold grows at cliff feet, and animated
whey trickles remain on solid faces outside paths and landings.

The new 32×48 cave mouth is composed of six metatiles. Its bottom half contains
a real 16-pixel opening; the outer halves collide with the architectural frame.
Bombable and flammable versions preserve that opening's correct art when
cleared. The first progression barrier reacts to bombs, the combined
Bomb+Lamp prefix reacts to flame, and the final three-gift seal opens when the
full capability mask is present. A prefix mask is not interpreted as a new tool.
Two-tile-wide drop notches are passable floor immediately above a solid cliff,
so Bloom can reach the displayed takeoff point without walking through a wall.

The new chest is painted on a 32×32 canvas, with an approximately 22-pixel body,
a clean gold latch and a contact shadow. Task altars and supply caches have
separate markers and interaction positions; a task cannot steal a chest's A
interaction. The area adds three original 32×32 folk, four new Bloom climbing
frames using the existing identity/palette, and a 32×64 cream peak monster with
32 poses/directions. During recovery its neck bows into a visible climbing ramp;
the exposed back core is centred at local(16,42), aligned with the new boss's
14×14 hit region centred at feet minus 24 pixels.

The two new Drain entrances use 32×64 hardware sprites, with 16 transparent
pixels above 48-pixel arches. The ascent has actual ivory steps and an upward
arrow above its arch. The annex bears a book sign and a large brass keyhole. A third, appended
frame has a downward arrow for the Cream entry return. That arch stands on a
reserved dry pad at(24,20), with a reachable lower front, away from the healing
cistern. Its A interaction returns to the Drain without an escape item or death.
The pure map preview marks the actual return mouth, and the new-area arrival
stands naturally in front of it.
Existing OBJ palette banks are reused because all 16 hardware banks are already
allocated. No earlier OBJ palette is changed.

## Graph-to-room agreement

The logical graph has 50 nodes: two separated terrace components in each of
25 rooms. A room is 32×24 metatiles. Four profile families vary upper shelf width,
headroom and ledge contours. The lower terrace starts at varying heights. Their
horizontal walk ports meet neighbouring rooms at consistent heights. Climb
shafts share a column coordinate across vertically adjacent rooms and extend
through the actual profile rather than stopping behind a strip of solid wall.
The top-row peak has a 25×10-tile dry upper arena.

Each physical route derives from a graph edge. Missing edges remain solid.
A local climb uses actual climbable metatiles between its two floors. North
climbs enter the northern room's lower component. Reverse downward routes
enter the southern room's upper component. Long drops have distinct notches
and target an explicit lower landing two to four rows below. Cave mouths are
paired only where the graph provides a cave edge. Room traversal never assumes
that a screen's centre identifies the right terrace.

`cream_room_arrival` derives the target room's profile without changing the
source room. It accounts for unequal neighbouring lip heights, cave front
pits and decorative fixture clearance. A local fall changes component without
reloading enemies. Its initial height is exactly landingY minus takeoffY;
other-screen arrivals enter from the top of the final room. A quadratic
downward acceleration and existing tucked descent pose avoid an upward pop or
an idle standing pose during the fall. Death state is never replaced by landing
recovery. Cleared physical gate bits persist independently for all 50
nodes; clearing a paired gate updates its reciprocal face. Existing
`gRoom.underlay` retains native substrates, avoiding a duplicate room-sized RAM
buffer. Enemy clear state, chests, caches and healing use the new area state.

`cream_room_preview` is a pure map query. It does not touch the active room,
collision, current profile or VRAM. The map receives the same profile formulas,
feature coordinates and actual exits as the live room.

## Verification and evidence

Run `python tools/cream_room_review.py --out <directory> --seeds 256` after the
normal asset build. The host adapter executes the actual `cream_room.c` and
`cream_world.c` against native metatile type/collision/prop metadata and the
engine's 8-pixel collision rules. The final qualification passed:

- 6,400 generated rooms and 6,400 non-mutating preview checks;
- 25,344 actual graph trigger checks and 25,344 target landing clearances;
- 58,559 enemy spawn clearances and 768 task approach checks;
- every sampled chest, folk, heal and cache approach;
- 160 closed gate footprint, native restoration and persistence checks.

The graph agent also ran `tools/cream_room_batch_review.py` across 100,000
seeds:2.5 million actual C-built rooms,9.9 million route/arrival pairs,
22,899,209 spawn checks and 3,472,886 content-front checks, with zero failures.
This uses the same qualified 8-pixel collision host adapter; its 25-room cache is
a host-only optimization and adds no ROM or game RAM cache. Runtime animation
and combat remain separately verified through mGBA.

ARM syntax checks for the room and runtime pass with `-Wall -Werror`.

Actual mGBA integration 3 review completed the three real mandatory tasks,
earned Bombs, Lamp, Cape and Pacci, opened physical bomb and flame gates with
their real tools, traversed cave folds and the final combined seal, and reached
the summit. Pacci hit the painted head, the real boss ramp raised Bloom to z 16,
and sixteen real sword blows reduced the peak monster from 32 HP to zero. The
game entered its actual win state. The full review passed 54 checks.

Separate seeded runs proved every intermediate background during long falls:

- seed 0xB4A7: two rows, rooms 12→17→22;
- seed 5: three rows, rooms 6→11→16→21;
- seed 1432: four rows, rooms 3→8→13→18→23.

Run `python tools/cream_runtime_review.py --bundle <frozen-ROM-directory>
--out <directory>` for the full seeded proof. Add `--seed 5
--stop-after-long-drop` or `--seed 1432 --stop-after-long-drop` for the other
fall spans. Its native 240×160 PNGs and sampled GIFs come from real mGBA video.
Hero position, facing and standing state are disclosed navigation fixtures;
seed selection and erased private SRAM are explicit new-run fixtures. The
harness makes real pause-menu choices and presses actual game buttons. It does
not assign inventory grants, player health, enemy health/state, completion bits,
gates, terrain, palettes, VRAM or framebuffer pixels. This establishes mechanic
execution with navigation fixtures, rather than an unassisted playthrough.

The source/host evidence is in `/workspace/setup/curdled-cream/`; the parent
integration owns the final pinned ROM, emulator suite and published gallery.
Host graph/collision qualification does not establish complete combat victory
or animation performance. Those require the separate production-ROM review.
