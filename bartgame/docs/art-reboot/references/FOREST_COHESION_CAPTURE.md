# Forest cohesion: native capture contract

`tools/forest_cohesion_review.py` captures the prior integrated-tree build
(profile 31) and the new forest-composition build (profile 32). It reads each
bundle's actual ROM, linker symbols and generated header. This is emulator
evidence, distinct from the separately labelled source-art catalog.

## Natural generation and disclosed fixtures

A run is seeded before ordinary title Start. The game creates its real 5×5
world, and its normal forest entrance and selected-cell transition load the
requested room. Selecting a review cell is developer navigation, not a claim
to have walked a complete run. Neither room grids nor artwork are injected.

The initial native arrival image preserves the room's actual actors. Later
inspection isolates enemies, projectiles and actor effects, initializes a safe
standing point/facing, and restores health while the scene settles. NPCs,
chests and other interactions remain. The report identifies removed actors
and standing positions. These fixtures do not constitute combat play testing.

The optional census inspects every naturally generated room for two seeds.
Its 50-room coverage is diagnostic; ordinary gameplay is not changed to require
visiting all 25 cells. Composition telemetry and actual semantic/collision
grids are read from RAM. The final eight cases retain the same seeds and cell
indices on both builds. Their geometry intentionally differs. Case names such
as `pond` describe the new design being reviewed, not a claim that profile 31
already had the same motif.

## Complete rooms and native viewports

A complete 512×384 room image is a registered camera mosaic of nine untouched
240×160 GBA framebuffers. Camera origins are x=0/136/272 and y=0/112/224.
Disjoint source crops cover every output pixel exactly once. Captions and
inspection enlargement are outside this native pixel proof.

The native camera fixture holds the animation clock and omits the HUD/textbox.
It pauses movement, AI and ordinary simulation while using the game's normal
world/actor renderer. The same frozen actor coordinates are used in all nine
views. No sprite is cloned, relocated between views, erased or painted over.
Normal HUD-on views are recorded separately.

Each view records real PPU scroll at paired scanline 0 and 160 observations.
The helper reads mGBA's renderer-write register mirror; GBA scroll registers
are write-only and CPU open-bus reads would not prove camera position.
Resident static tiles, authored animation frames, physical room data, palette,
root ownership and exact lower-tree maps remain independently inspectable.
Ambient glitter may differ across overlapping viewports because of native
edge culling and object budgets. Literal crop seams are retained unpainted.

## Ordinary motion

The three walking clips retain 168 consecutive native video frames each.
Following the disclosed initial standing fixture, only ordinary directional
keys move Bloom. A read-only check of the real floor chooses alternate keys
before water, pits, ledges, exits or room entrances. This avoids mistaking an
intentional drowning/falling pose for a foliage-visibility failure. Every
requested direction, actual key, position and update interval is recorded.
There is no position or pose injection during the recorded walk.

Body proof compares actual native OBJ pixels, current palette and exact guard
subsets with the matching framebuffer scanout. The finite checks require at
least 37 colored body pixels and a 12-pixel connected region. They support the
recorded visibility contract, not an external recognition study or a claim
that every action/room in the game has been exercised.

Selected water clips retain 96 consecutive native frames. After a dry-bank
standing fixture, ordinary simulation and animation advance with the normal
HUD and camera. Native tile updates must remain authored ROM animation frames;
terrain and collision must stay unchanged. No time-hold camera is used for
these clips.

Every video frame is kept. Literal missed logic-update intervals are reported
per room; no allowance is inherited from a different historical room or profile.
MP4s are lossy viewing copies at the native GBA video rate. Any GIFs use exact
sampled RGB frames with fixed inspection holds and do not claim original timing.

## Completion and provenance

A report is complete only after immutable ROM/header/map and capture-helper
hash checks finish. Final publication requires `complete=true` and `pass=true`.
The report records the game/art source freeze independently from verification
tool hashes. A native source-art assembly is never substituted for an actual
room framebuffer or labelled as a gameplay capture.
