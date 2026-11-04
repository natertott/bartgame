# Actual mGBA workload survey

`tools/performance_scenarios.py` measures the running ROM, rather than host
execution time. Its immutable bundle supplies the ROM, linker symbols, generated
asset header and source identity. `gFrame` counts real VBlank interrupts;
`gGame.run_frames` counts gameplay/transition updates. Every sampled video frame
retains both ages, actual game/player state, physical action flags and prepared
OAM count. Enemy/effect/projectile/pickup counts are sampled every15 video frames.

The normal corpus has146 scenarios:75 natural forest rooms across three seeds,
three Drain contexts,24 actual generated mystery interiors,30 explicit enemy
stress cases,12 item-action contexts and two modal views. Interiors cover cave,
hollow and thicket, all ten implemented mystery kinds, mandatory rewards,
wave/survival/miniboss events and ordinary quiet rooms. Boss rosters remain live
in each seed's natural goal and separate Heart action contexts.

Natural rooms never clear their actors. Their original generated enemies retain
ordinary AI, health, attack timers, collision and movement. Player health is
restored to80 during samples to permit sustained measurement, and full ordinary
inventory exercises ten hearts plus real tool/ammunition rendering. Developer
positioning uses actual dry floor and the normal room-transition request;
terrain, artwork, camera easing and framebuffer pixels are never substituted.
The transition/generation/fade latency is a separate record.

Stress cases explicitly clear the nonplayer actor roster and request4/8/12/16/24
original enemies through `gDbgSpawn`, separately for each of five families and a
mixture. They are synthetic throughput scenarios, not a claim that the generator
normally creates24 monsters. Combat is real and can reduce the enemy population;
initial, periodic and final counts must accompany throughput claims.
`--stress-mode idle` runs the same30 synthetic cases without player offense,
retaining live enemy AI/HP and health restoration only. It supplies an additional
throughput sample whose enemy count is not reduced by faster player attacks.
Any naturally lost enemies remain explicitly reported rather than silently replaced.

A zero gameplay-age delta while ordinary play is expected means a repeated
video frame, not a slower host machine. Named dialogue, shops, pause pages and
transitions are identified separately. The paused menu is not falsely called a
zero-FPS gameplay failure; its input-to-state and native draw-frame latencies
are measured with real Start/R/A/B controls. Cold overview/zoom costs are kept
separate from steady gameplay.

## Reproduction

Activate `/workspace/setup/activate.sh`, then run from the standalone game:

```sh
python3 tools/performance_scenarios.py \
  --bundle /workspace/setup/performance/before/bundle \
  --out /workspace/setup/performance/before/broad \
  --suite all \
  --record 'forest-0000b4a7-cell10|stress-knights-16'
```

Use `--reference BEFORE_REPORT` for a subsequent build. It reuses the baseline's
planned dry player tile and checks that the tile is still dry/walkable. It never
forces enemy HP, timers or AI to manufacture matching states. Per-case records
say whether initial enemy types/counts, player position and actual camera match.
The input schedule is fixed in video time: a faster build naturally advances
more simulation and may accept inputs the old build missed. Such runs establish
experienced throughput; they do not establish bit-identical simulation at equal
video ages. Exact behavior/visual equivalence needs independent fixed-logic and
native rendering checks.

`--warmup 120` runs120 ordinary unheld video frames before each nonmodal sample.
Use it on both builds for an additional steady-camera comparison; default runs
include the ordinary camera approach following developer positioning. No camera
coordinates are written. `--case REGEX` selects a focused reproduction, and
`--suite` selects natural, interiors, stress, actions or UI independently.

`--record REGEX` retains every selected native240×160 framebuffer and a GIF
sampling every sixth frame, with100ms viewing holds (approximately real59.73Hz
playback). Captions, image filtering and diagnostic painting are absent from
these game pixels. The JSON records each raw frame/hash and its actual video
and logic ages, so a low-FPS source remains visibly low-FPS in its recording.

## Baseline diagnosis

The frozen pre-optimization ROM is source
`11b872e9897320398fa02344cef1418733c04e9a`, SHA256
`1bd913bc5bf1ad81e9c1dcc7e07ebc38eac855d390a5bb613257f8fbfe128e59`.
The75 natural rooms produce12,723 game updates across13,500 eligible video
frames.41 rooms fall below99% throughput; two spend the whole sample at half
speed. The three unlit torch/NPC rooms have particularly high cost: mean52.8%
throughput versus100% for the three goal rooms. OAM is well below its128-entry
hardware ceiling, so the observed failures occur before sprite-entry exhaustion.

An isolated seed0xB4A7/cell10 reproduction retains its six natural enemies and
runs90 updates in180 video frames. Warming the actual camera for120 video frames
still produces90/180, ruling out an explanation limited to teleport/camera
settling. Ground-enemy stress populations of24 also run at half speed; airborne
hunters are cheaper than comparable ground rosters. These workload correlations
motivate profiling; they are not substitutes for cycle-level attribution.

Final optimized counts belong to the frozen after-build reports. Representative
success does not establish a worst-case bound for every possible future state,
area, enemy population or effects combination.
