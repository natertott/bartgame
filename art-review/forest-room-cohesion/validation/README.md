# Forest composition validation

Game/art source: `4024902d56c759ca124b2517c73f77e5234be66d`.
ROM SHA256: `5fcf4cba1c6ab3a5af4575a5a05a49d9813457a02b4f5d16a7e3abc05e41566e`.

| Evidence | Result | Report |
| --- | --- | --- |
| Frozen native art, scope and 128-seed actual C corpus | 1223/1223 | [Host/source audit](audit-host.json) |
| Fresh native camera and walking proof | 567/567 | [Capture audit](audit-capture.json) |
| Actual mGBA menus, cache, areas and progression | 80/80 | [Runtime](runtime/report.json) |
| After32 actual capture | 338/338 | [Eight rooms](../actual/after/capture.json) |
| Matched before31 actual capture | 336/336 | [Same eight cells](../actual/before/capture.json) |
| Literal image/source/media/ZIP/link checks | 694/694 | [Publication QA](publication-qa.json) |
| Historical build byte preservation | 32/32 | [Profiles0–31](legacy-preservation.json) |
| Default build | Exact selected ROM | [Ordinary make](default-build.json) |

The [actual C host report](host/report.json) and [run log](host/run.log) cover
3,200 generated rooms,800 opened-state cases,25,543 required approaches,
2,619 item pockets,32,000 inventory/boundary checks and 1,600 real-feet cases.
There are 805 bridge runs with 1,610 dry reachable landings and 6,059 anchored
lanterns. All 8,256 visible-trail refinements preserve tile types, collision
masks and authored overlays. All 128 collected-relic rebuilds preserve the
remembered path and lantern layout. The host suppresses hardware submission;
these are logic checks rather than emulator render claims.

All 939 forest metatiles and 1,049 authored native frames independently match
the linked4bpp atlas, flips and RGB555 palette. All twelve approved tree
pictures, anchors and source-alpha masks remain exact. Shared Bloom, enemies,
equipment, chests/entries/folk, UI/title, global BG palette and other regions'
resolved pictures retain their preceding source. Forest residency is 656/768
BG tiles and 10/12 world palette banks. Dynamic generation scratch uses EWRAM;
there is no per-frame trail search.

The native evidence contains144 camera views in total: eight before and eight
after full-room mosaics. Each 512×384 mosaic copies nine declared native
240×160 viewports without filtering or painted seams. Normal HUD/arrival
frames remain separate. The final after clips preserve504 walking frames and
384 water-animation frames. Bloom's colored/connected visibility minima are
79/14,95/24 and 90/14. Literal missed-update counts are 2/1/0; the previous rooms
had1/1/0 under different geometry and hazard-aware routes. This is not a
frame-perfect performance or speed-comparison claim.

The review harness discloses native navigation, safe initial standing,
enemy/projectile/boss isolation and health restoration. Recorded movement uses
ordinary keys selected against the real traversable grid. Required trials,
rewards and item gates run actual game logic; the harness does not grant
rewards or reduce enemy health. No art pixels are injected into screenshots.

Some path and pond contours remain visibly16px orthogonal; deep floor detail
is restrained and the approved repeated tree texture remains recognizable.
The Heart terrain mosaic isolates its boss for inspection. See the
[independent visual review](../../../bartgame/docs/art-reboot/references/FOREST_COHESION_REVIEW.md).
These finite cases do not imply that every random room was individually viewed.

[Frozen build and input hashes](frozen/v32/freeze.json) · [Header](frozen/v32/assets.h) ·
[Linker map](frozen/v32/bartgame.map) · [Asset coverage](frozen/v32/coverage.json) ·
[All 33 builds](builds.json) · [Gallery](../README.md)
