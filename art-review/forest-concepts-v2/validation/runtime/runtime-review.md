# Final native runtime review

All final reports bind game/art source `e5e3fcb21fe1bcc50c965943164146a2dc1e3c46`. New-study capture tool: `27f61fdfc4bac4dea3b0defe05cddcbff8f4ab05eedc4e761cb219698e15948b`. Production control uses the unchanged prior harness `17c6fc2de373b2cf0aee906a3e4044653879f81860d32b642362fb034678e181`.

## Results

| Build | Checks | Native cases | Movies/exact GIFs | Earned route |
| --- | ---: | ---: | ---: | ---: |
| 0 | 482/482 | 83 | 10/10 | Separate production control |
| 6 | 1399/1399 | 97 | 15/15 | 17/17 |
| 7 | 1463/1463 | 97 | 15/15 | 17/17 |
| 8 | 1463/1463 | 97 | 15/15 | 17/17 |
| 9 | 1463/1463 | 97 | 15/15 | 17/17 |
| 10 | 1463/1463 | 97 | 15/15 | 17/17 |

Total:7,733/7,733 checks;568 actual cases;85 movies and85 exact-palette sampled GIFs. Maximum sampled OAM is25/128. All five new profiles have strict matching physical maps, collision, positions, actual actions, progress, RNG and ordered state transitions. Their generator intentionally differs from production0, so its physical maps are a separate protected control.

## Scope and provenance

Each new study has97 cases:91 naturally generated contexts and6 explicitly labeled logical-room fixtures. All25 rooms of the primary seed are captured; curated real seeds provide the actual three mystery styles, interactions, deep non-arena room, NPC dialogues and clear root-arch context. Ordinary item actions create opened/cleared/pressed/lifted states. No natural-case terrain, event descriptor, enemy HP, drawn animation frame, z or action/AI timer is assigned. Initial standing state is part of the safe player-position fixture.

Fixtures select seed, room navigation, inventory/ammunition, health, safe player position/facing and unrelated-enemy clearing. After settling, the global comparison frame clock is normalized and64 actual frames run before recording, aligning ambient/palette animation without assigning a drawn frame. The Heart landscape retains the actual boss. The separate earned-route proof solves all three real trials and earns their rewards: no trial enemies, HP, event flags or rewards are injected. Its strategy uses approachable foes, actual sword inputs and disclosed player-position retreats during natural hurt recovery; all AI and timers remain live.

The six diagnostics explicitly replace logical gRoom cells, then invoke the same ROM renderer/collision builder through a temporary restored VBlank hook. They are not naturally generated rooms. They cover isolated1x1/2x2/3x3 and narrow/inner-corner canopy/water contexts, actual water entry/drowning/safe respawn, and isolated pools over healthy/sick/dirt floors. An additional457 actual diagnostic contracts cover all376 canopy quadrant/mask combinations,32 fringe masks,47 water shapes and2 lily/foam cases, without publishing hundreds of redundant screenshots.

## Depth, color and gameplay evidence

Before/Under/Emerged keyframes are exact native movie frames selected using decoded actual VRAM/OAM and applied BG1 scroll telemetry. Grounded foliage has visible soles and partial upper-body cover. Every roll/recoil frame retains a meaningful connected colored body at the real wall limit. The brief airborne wall-recoil exception is coarse GBA foreground sorting; it preserves the real physics, z and timers. Root-arch clips show a genuine lower trail beneath scenery, with no claimed accessible upper level.

Exact native BG2 quarter entries before/after genuine thorn/bomb/web/key clearing prove the original local substrate remains. One large keyhole spans its semantic gate pair and disappears after actual key use. Wooden B closed/open frames are checked against actual streamed OBJ VRAM. Four actual displayed glow phases are matched to frozen authored RGB555 words; selected OBJ and reserved UI palettes stay unchanged. Ordinary menu open/close at four phases and real area transitions restore native palettes.

PNGs are exact240x160 mGBA framebuffers. Filmstrips add labels outside native panels. MP4 is full-rate59.7275fps with a lossy2x nearest-neighbor viewing enlargement. GIF samples every two frames and is retained only with an exact complete sampled palette. Raw movie PNG frames remain local archives; referenced extra native phase/cleared/depth frames are explicitly listed in each capture report.

Only `v6`..`v10`, `control-v0`, and this final summary are final evidence. All `draft-*`, `preflight-*`, `regression-scenes-*` and `archive-*` outputs remain nonpublication diagnostics with their original provenance. The source gallery is separately labeled authored art, not an emulator run. Repetitive deep wood remains an art tradeoff for user review.
