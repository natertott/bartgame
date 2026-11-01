# Focused canopy runtime review

Game/art source: `e923557aa74b01626f3e599f7c4b50366e096507`. Capture tool: `87b4f48479dcd414037581c35bdbdfc319123ab035b2a3d7f6991403cc6f3802`.

All nine completed reports use the same held capture tool and committed frozen inputs. The preserved base6 report and the first new study report were complete, unfiltered and source-bound from their first passing run; they are retained byte for byte. `runtime/v11` is a read mirror of the original `protocol-smoke-v11` directory, whose command and path provenance remain unchanged. Failed or unfrozen pilots remain separate local evidence.

| Profile | Checks | Contexts | Movies / exact GIFs | Minimum native body ink / cluster | Minimum displayed character ink / cluster | Fully hidden character frames |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | 285/285 | 22 | 7 / 7 | 0 / 0 | 0 / 0 | 46 |
| 11 | 399/399 | 22 | 7 / 7 | 37 / 14 | 30 / 8 | 0 |
| 12 | 399/399 | 22 | 7 / 7 | 37 / 14 | 30 / 8 | 0 |
| 13 | 399/399 | 22 | 7 / 7 | 37 / 14 | 30 / 8 | 0 |
| 14 | 399/399 | 22 | 7 / 7 | 37 / 14 | 30 / 8 | 0 |
| 15 | 399/399 | 22 | 7 / 7 | 37 / 14 | 30 / 8 | 0 |
| 16 | 399/399 | 22 | 7 / 7 | 37 / 14 | 30 / 8 | 0 |
| 17 | 399/399 | 22 | 7 / 7 | 37 / 14 | 30 / 8 | 0 |
| 18 | 399/399 | 22 | 7 / 7 | 37 / 14 | 30 / 8 | 0 |

Inclusive result: **3,477/3,477 checks, 198 contexts, 63 full-rate movies and 63 exact sampled-palette GIFs**, with 16,272 observed video frames. Eight new styles account for 176 contexts and 3,192 checks. Each profile has 16 generated contexts and six explicitly constructed diagnostics; base6 is an old-art comparison, not a production0 runtime control. Maximum sampled OAM is24/128.

## Generated scenes and disclosed fixtures

The three broad views use actual healthy, mixed and deep generated rooms. Other generated cases exercise ordinary walking, rolling into the real wall limit/recoil, four-facing sword and shield inputs, cape jumps, and one menu open/close/resume beneath foliage. Fixtures select seed, room navigation, initial standing position/facing, health/inventory and unrelated-enemy clearing. The reference clock is normalized after settling, then64 actual frames run. Mid-case sword-to-shield A-slot assignments are explicitly recorded equipment fixtures. No drawn pose, animation timer, z, terrain or video pixel is assigned in generated contexts.

Six diagnostics per profile deliberately replace semantic room ground/overlay/underlay cells, then invoke the same frozen `room_render` and ambient reset through a restored VBlank hook. The hook waits for two observed IRQ entries and three real game updates before recording. Isolated sizes, narrow/concave forms and two motion stress scenes are diagnostic fixtures rather than claims about natural generation. No VRAM or framebuffer art is painted by the probe.

## Actual scanout and character ownership

mGBA0.10.5 calls videoFrameStarted at visible scanline0 and videoFrameEnded at160 (`src/gba/video.c` in the local emulator source). A read-only start callback decodes actual OAM, resident body/guard VRAM, palette words, BG1 tiles, flips and the applied camera. Its model is paired with that exact scanout’s unchanged finished framebuffer. Every recorded frame asserts start0/end160 and identical emulator frame-counter tags. Post-run CPU state can describe the following update; it is not substituted for the hardware that drew the PNG.

The native body guard test remains strict: at least25% of meaningful body-colored ink, at least12 colored pixels, and an8-pixel connected component. Its foreground fragment must be an exact subset of the current resident native body frame, at the same position, palette and flip. Recorded minima for all eight styles are37 native colored pixels /14 connected pixels. The protected pixels coexist with real upper-body canopy coverage.

For displayed character color, the validator independently resolves the body, guard and only a current native cape using actual priority and OAM-index ordering. A cape is eligible only when its streamed bytes match a frozen BLOOMFX_CAPE frame, its phase agrees with the native body pose, its palette agrees with the frozen frame metadata, and its x/y/shape/size/flip exactly match the body. Frame IDs are read explicitly because breathing aliases leave gaps between hero cape IDs. Matching an idle bitmap alone never implies a cape exists. Floating weapons, magic effects, glitter, interface icons and nearby actors never count as Bloom.

A north-facing cape is intentionally in front of the body. Consequently body-only screenshot matches can fall to11 pixels /7 connected while the actual native body-plus-cape remains clearly present. Those separate numbers and exact cape payload/anchor evidence are retained; the actual displayed character requirement stays12 pixels /8 connected. Across all new styles the measured minimum is30 /8, with zero fully hidden character frames. `Cape overlaps body` and `Least visible displayed character` keyframes preserve the actual relevant PNGs.

The old base6 capture records46 gameplay frames with zero displayed character-colored pixels in these contexts. These historical deficits are retained honestly, rather than treating the old canopy as a passing never-hidden implementation.

## Cadence and menu resume

All source geometry, collision, maze/RNG/progress, input schedules, initial/final positions and ordered mechanic states match the reference. Every new case adds zero missed gameplay-update video intervals relative to its comparison. Each profile has the same three zero-update intervals at the menu return boundary; the non-menu cases record none. This is finite-case gameplay cadence evidence, not a CPU-cycle benchmark or a universal performance guarantee.

The paired scanout identifies one return-boundary frame (tick47) with source GS_PLAY/world planes but no hardware player OBJ, identically in base6 and all new styles. That existing interface transfer gap is reported and bounded against the control. It is not mislabeled as canopy occlusion. Every resumed player/world frame is checked, and native palette/map restoration is verified. Earlier post-run observations appeared to span two frames because software/hardware boundaries were not yet paired.

An earlier unfrozen guard implementation performed per-frame cutoff/connectivity work and caused13–15 missed updates in some cases. The current frozen engine replaces that work with immutable generated pose metadata. Failed pilots keep their original source/ROM/tool bindings outside final publication; their data is not relabeled as the final passing run.

## Formats and limits

Native PNGs are exact240×160 framebuffers. Filmstrips add captions outside their literal native panels. MP4s preserve the actual full-rate frame sequence at59.7275fps but are lossy2× nearest-neighbor viewing copies. GIFs sample every second native frame and are kept only when every sampled color remains exact. Raw all-frame movie directories stay local. Source artwork and inspection diagrams are separate from these actual recordings.

The render guard covers vegetation, while architectural roofs/root-arch timber retain their separate depth rules. These cases do not implement an accessible upper bridge deck, retest the full enemy suite, or assert that every possible player pose and random room has been exhaustively recorded. Shared native-art and old0–10 byte-preservation evidence belongs to the separate frozen build/native audit. All runtime reports, input hashes and dependencies were reverified after the final processes ended.
