# Five sword studies for selection

These are five playable, native-GBA comparison prototypes. No variation has
been selected for the released game. The normal build (`BART_SWING=0`) produces
the same ROM bytes as the approved art reboot, SHA256
`41dc680068c094416e92152d4c22637c10d6a055d2bee63ce7700c419490e92d`.

Start with the [actual mGBA comparison gallery](../../art-review/sword-studies/README.md)
and the [Zelda research with pinned sources](SWORD_STUDIES_RESEARCH.md).
Link's Awakening and Oracle coordinate the body, blade and contact region;
Minish Cap derives the weapon from the current body frame. The studies adopt
those relationships without copying their graphics or claiming identical
Nintendo timing.

## What is being compared

| No. | Gesture | Preparation / cutting / recovery | Total | Main tradeoff |
| --- | --- | --- | --- | --- |
| 1 | Planted slash | 4 / 7 / 5 updates | 16, about 268ms | Fast and restrained; smaller body commitment. |
| 2 | Broad sweep | 4 / 10 / 6 | 20, about 335ms | More hip/flower rotation and a longer outward contact hold. |
| 3 | Step-and-cut | 4 / 7 / 7 | 18, about 301ms | Strong forward lean/root placement, with a longer settle. |
| 4 | Overhand chop | 8 / 5 / 9 | 22, about 368ms | Most deliberate load/compression and the narrowest timing window. |
| 5 | Flowing backhand | 4 / 9 / 5 | 18, about 301ms | Reverse sweep, sustained contact and a more expressive follow-through. |

Times use the GBA video rate, about 59.7275Hz. The total includes the initial
input update at age 0. Contact is enabled only during the labelled cutting
interval. One generated clock selects body pose, sword image, hand anchor,
sound onset and damage bounds; windup and recovery are harmless.

All five have eight authored poses for north/east/south/west, with planted or
transferring roots, turning pelvis/shoulders, head lag and leaf-tunic movement.
The body remains a 32×32 hardware object and uses the current shared hero inks.
The weapon uses the current stone/steel bank. Its length is fixed within a
variation; its curved trail is short, tapered and dimmer than the leading
steel. Menu icons and unrelated art are not changed by these studies.

The step in variation 3 is drawn weight transfer, not a physical world lunge.
Movement, enemy behaviour, base sword damage and input buffering stay the same
across the comparison builds. Styles do vary the visible reach/sweep and its
matching contact region. This lets the user choose gesture and feel together.

## Corrections made during review

The old body had three pose groups on a different schedule from the blade's
five poses. It could look like anticipation while already dealing damage,
or recovery while still cutting. The studies replace that mismatch with the
single eight-pose clock.

Side-view grips were lowered three pixels to cut at a natural waist height and
meet low enemies. North grips stay outside the flower so the equipment is
legible, while a 32-degree inward aim brings the central stroke toward a threat
directly ahead. It avoids the former late contact caused by a vertical blade
off to the right of the target. The reverse backhand uses the opposite bias.
All masks and boxes are regenerated from the corrected visible art.

The bright, blocky tip trail of the pilot was also reduced to a faded taper;
it should read as motion behind the steel rather than an axe head or hook.
No persistent range cage, invisible forward extension or opaque fan is added.

## Collision and actual rendering

The source painter creates the visible steel/ribbon and a contact mask together.
Each live pose exports the inclusive AABB of that mask. These are ordinary
rectangular combat regions, not per-pixel collision; the diagnostic cyan box
shows their exact extent. Hidden north-facing pixels under the flower are
removed from both image and mask. No inactive pose has a damage mask.

`player_draw()` exports a study-only prepared snapshot. Capture tools match
its body and weapon bytes to real hardware OBJ VRAM/OAM before placing a box
on the screenshot. Current logic can be one upload ahead of the displayed
picture, so a box must not simply be drawn from the current actor timer.

All 80 clean cases use ordinary B presses on naturally generated forest,
Drain, blight and cave ground, four facings per style. Seed, safe position,
facing, inventory and clearing unrelated actors are disclosed fixtures;
terrain and attack poses/timers are never injected. Another 10 clips show real
contacts against constructor-spawned beetles with native HP, positioned ahead
and paused through zero-speed knockback to isolate timing. No enemy HP or
reward/death flags are written.

The full-rate MP4s preserve every video frame. Normal GIFs sample every second
frame and can omit a one-update pose; the clearly labelled 3× slow views retain
every source frame. Native selected PNGs remain exact 240×160 framebuffers.
Captions, timing bars and cyan diagnostic overlays are review presentation,
not ordinary game HUD elements. The compact gallery keeps all videos, selected
native frames, filmstrips and runtime traces; redundant per-case GIF archives
can be regenerated with the capture tool.

## Verified results and limits

Across the five exact frozen ROMs, the probes pass 3,878/3,878 checks, including
544 inside/one-pixel-outside contact cases and 20 full-swing forward targets.
The target centres are 24px ahead of Bloom's hurtbox centre and are first
proven outside body contact. Exact on-screen pose holds match their authored
durations in all 20 style/facing combinations. All 80 clean and 10 target clips
complete their expected action checks.

In the isolated centred-target test, first actual hit age, N/E/S/W, is:

| Style | North | East | South | West |
| --- | --- | --- | --- | --- |
| 1 | 5 | 4 | 5 | 4 |
| 2 | 5 | 5 | 7 | 5 |
| 3 | 6 | 4 | 6 | 4 |
| 4 | 8 | 8 | 10 | 8 |
| 5 | 5 | 5 | 5 | 5 |

These are measured logic ages for that target position, not a promise that
every enemy at every distance is hit on the same update. All lie within the
shown active interval. Normal gameplay still involves spacing and approach.

The visual critique is deliberately part of selection: 1 has subtler body
motion, 2 is the broadest and easiest to read, 3 shows effort without actual travel,
4 demands more anticipation, and 5 has a busier return. These are tradeoffs for
the user to judge in motion, not a reason to pick a default automatically.

## Reproduce

```sh
# Default: byte-identical released art reboot.
make -j4 BART_SWING=0

# One optional study. Use separate build directories when keeping several.
make -j4 BART_SWING=2 BUILD=build_swing2
```

The generated `build_swing2/gen/art-reboot-coverage.json` includes the study's
profile, durations, active flags, per-age lookup and visible geometry. Study
frames append to the existing hero/bloomfx sheets; original identifiers and
the live streamed VRAM allocation stay unchanged. No save structure changes.

Freeze the ROM, matching linker map and generated header/coverage together.
Then use `tools/sword_study_probe.py`, `tools/sword_study_review.py` and
`tools/sword_study_gallery.py` with `--help` for their paths/output options.
The Makefile records the chosen profile so changing `BART_SWING` cannot silently
reuse assets from a different study. Rebuilding without the option returns to 0.
