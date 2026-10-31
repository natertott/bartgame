# Final enemy animation runtime review

Frozen game/art source: `5eedc6dae94d8c1ea21c55b8668435bcf0be884d`.
Eleven immutable ROMs comprise the adopted interface with current enemies
(profile 0), plus ten optional complete enemy-art profiles. Each positive
contains one alternative for each of the six implemented AI families:
**60 enemy concepts in total**. This pass does not select a winning enemy set.

## Actual mGBA evidence

**132 actual cases and 900/900 runtime checks pass**: twelve cases per ROM;
80 checks for the production enemy baseline and 82 for each positive profile.
The two additional positive checks verify that real nonlethal combat actually
selects the new heavy-enemy and boss hurt poses. Full-rate videos total 35,288
native video frames. The maximum sampled OAM count is 29/128; that is a sampled
budget, not a worst-case actor guarantee.

Each profile records:

1. A naturally spawned pursuer moving/chasing on healthy forest ground.
2. A naturally spawned flyer folding/resting and flying, with actual altitude
   changes on healthy forest ground.
3. A naturally spawned shooter preparing, emitting a real seed and returning
   to walking/resting in blighted woodland.
4. A naturally spawned hopper crouching, launching, landing and repeating in
   an intermediate forest room.
5. A naturally spawned heavy enemy's real windup, live swing and recovery.
6. The same heavy encounter after actual Start-open/Start-close item-menu use.
7. Real D-pad/B sword combat causing nonlethal hurt and then heavy-enemy death.
8. The naturally spawned boss's ring, pulse and drift at its original 40HP.
9. Its real middle-phase aimed fans and add spawning, selected with a disclosed
   HP 26 fixture.
10. Its real low-health lunges and fans, selected with a disclosed HP 12 fixture.
11. Real D-pad/B sword hits causing nonlethal boss hurt and the original
    120-update death event, accelerated with a disclosed HP 4 fixture.
12. An actual generated cave combat trial entered through its natural mouth,
    retaining the whole naturally spawned enemy group.

The seed, room transitions, initial safe player position/facing, inventory and
health, and clearing of unrelated actors are disclosed fixtures. Camera
settling uses 100 ordinary updates; it is not assigned. Enemy states, timers,
frames, poses, animation phases, positions and heights are never assigned by
this reviewer. Boss HP fixtures are the only writes to enemy fields. The
final blow and hurt come through ordinary input and combat code. The Drain
contains no normal enemy spawn roster, so no synthetic Drain enemy scene is
misrepresented as a natural run.

## Mechanical preservation and phase evidence

The independent native auditor verifies **108/108 whole-flow comparisons**:
profiles 2–10 versus profile 1, twelve flows each. Actual AI state/timer,
direction, facing, position, height, velocity, HP, invulnerability/knockback,
flags, damage, projectile trajectories and ownership, hero mechanics, enemy
counts and gameplay RNG match exactly. This comparison independently reads
and canonicalizes the JSON traces; it does not trust a capture-side digest.

The baseline 0 and positive 1 also match all eight common/cave flows exactly.
Their four boss flows begin one update apart, with different global-frame
ring offsets, due to legacy resident versus new streamed boss loading. The
first divergences are preserved in `baseline-vs-positive-mechanics.json`;
they are not silently normalized away. Source/control-flow audit separately
establishes unchanged AI, hitboxes, attack/vulnerability timing and damage.
Every baseline and positive boss flow independently passes its real behavior,
normal update cadence and defeat checks. Do not claim exact baseline-boss
video timelines.

All **thirteen boss presentation poses are actually selected in each of the
ten positives**, including pulse, charge, release, spawning, lunge, hurt and
dying. The other families' rare directions and old compatibility attack poses
are honestly listed as `source_only_in_this_capture_suite`. Their complete
source atlases/cycles establish authored coverage; the runtime suite does not
pretend every direction was seen in a short natural encounter.

`gEnemyPresentedFrame` is a read-only draw-selected frame, not a fixture. A
queued boss upload can lag one VBlank. Actual hardware OAM is recorded
separately, and each representative image requires a full on-screen body
canvas below the HUD with hardware OAM present. No invisible blink/off-camera
thumbnail is used as a sprite example. Original actor AI frame values are
recorded independently and restored after presentation selection.

## Item-menu and hardware restoration

Every ROM's real heavy encounter opens and closes the adopted large-item
menu. The paused enemy's mechanical state remains exact. Before and after
close, all native heavy-weapon bytes in its resident OBJ allocation match
its ROM sheet. Both the hardware palette and `gPalObj` buffer match the native
source for OBJ bank 2 (retained foliage/cloak) and bank 10 (the positive small
enemy palette). This explicitly checks the live palette/cache interaction
between menus, equipment and enemy art.

The native source/ROM/budget auditor separately passes **11,632/11,632 checks**
across all eleven ROMs. It covers all 640 authored study frames, protected world
and Bloom assets, palettes, identifiers, combat-code preservation and legal
OBJ allocation. Its conservative positive resident budget is 816/876 ordinary
sheet tiles, leaving 60; the boss streams one 32-tile frame.

## Visual review scope and media fidelity

The reviewer inspected native profile 1 representative images and critical
behavior/attack/hurt/death chronology during preflight, then corrected an
actual review-harness problem: an early healthy-pursuer thumbnail preceded
normal camera settling. Final recordings include the ordinary settle and
hardware visibility check. Final ten-way native crop boards for flyers, shooters, hoppers, heavy melee
and bosses were also inspected: the forms remain distinct on the actual
materials. The healthy pursuer encounter runs along a bridge edge, whose
foreground naturally occludes the lower body/legs. This usefully samples
terrain depth but is a weaker full-silhouette comparison; its complete source
atlas/cycle provides the unobstructed form. This is not a claim that every
frame in all 132 recordings was manually watched.

Every selected native PNG is unchanged 240×160 mGBA output. The five native
chronology samples and sixteen-image filmstrip per case preserve actual
pixels; labels lie outside the native images. GIFs use integer nearest-neighbor
viewing copies and publish only an exact palette. All eleven boss-defeat GIFs
exceed 256 colors (323–331) and are omitted; their native PNGs and full-rate MP4
viewing copies remain. MP4 is explicitly a lossy convenience format. Source
pose loops are labelled source assemblies, separate from real gameplay.

Evidence files: `enemy-review-summary.json`, per-ROM `enemy-reviews/vN/capture.json`,
`enemy-review-batch.log`, `run-enemy-reviews.py`, `baseline-vs-positive-mechanics.json`,
and independent `audit.json`/`audit-summary.json`. The initial mechanic inventory
pins prior published source `a9e09e5`; it is not relabelled as the expanded final
frame contract.

## Supplementary unobstructed pursuer comparison

The ten positive profiles now also have one **96-update natural clearing
encounter each: ten additional cases, 60/60 checks**. Every one of the 960
recorded body footprints lies wholly over ordinary floor with no collision,
raised prop, foreground overlay, bridge, water or ledge. The selected context
is naturally generated seed 6/cell 9/spawn 5; only the player is positioned and
healed, and unrelated actors are cleared. Eighty ordinary setup updates settle
the camera before the 96-update recording. Enemy position, state, timer, frame
and terrain remain untouched.

The first sixteen-frame native chronology was visually inspected for the full
body and alternating leg poses. These short open-ground samples supplement the
original bridge-depth encounters; they do not replace or edit the main 132
recordings. Their explicit short duration avoids presenting later mist/ambient
overlays as an unobstructed silhouette test. The nine positive-profile comparisons
against profile 1 match all actual mechanics traces exactly. Evidence:
`pursuer-clearing/vN/capture.json`, `pursuer-clearing-summary.json`,
`pursuer-clearing-mechanics.json` and `run-clearing-reviews.py`.

Combined enemy evidence is now **142 actual cases and 960/960 checks**, with
36,248 full-rate video frames. The original 132-case/900-check result and its
immutable reports retain their original identities.
