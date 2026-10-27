# Bloom animation suite: directional and motion polish

The [review gallery](../../forest-review/bloom-suite/README.md) contains 99
matched before/after recordings from the actual ROM in mGBA 0.10.5. It covers
the Drain, healthy forest, blighted forest, caves, foreground occlusion and
unusual state transitions. The source revision for the published ROM is
`c518ba9fbdc4efdee5b43330dcbd5105c329eaa6`.

## What changed

Bloom retains the approved flower, palette, nine original idle/walk images
and original 68 frame identifiers. The hero sheet now contains 101 frames.
New poses give guarding a walking cycle, lifting a directional progression,
bow use a stable grip, north/south rolls directional entry and exit, and
death a separate settling sequence. Hurt, pit-fall and drowning poses have
cleaner silhouettes. Drowning no longer stamps an opaque blue pool onto the
room's water.

Near-side props draw in front of Bloom and far-side props draw behind him,
using the same resolved terrain priority as the body. A north-facing shield
now shows its rim beyond the flower instead of covering Bloom's back. North
bow and lamp grips sit ahead of the body, while the cape remains visible on
the back. The physical candle flame, early bomb, arrow and thrown load use
the same directional ordering while they overlap Bloom. Foreground tree
crowns, rocks and Drain counters still occlude the complete actor correctly.

The north sword blade passes behind the actual posed head silhouette. Its
leading crescent and complete sweep remain visible; removing the straight
steel stripe over the petals does not remove the range cue. The sword's
hitbox, reach and 15-frame attack remain unchanged: ages 0–1 anticipate,
2–12 are live, and 13–14 recover.

Lifted bushes, stones, boulders and pots now resemble their room sprites.
Each eases from its real pickup position into the overhead grip. The held
position matches the physical throw origin, removing the vertical snap at
release. Turning and throwing keep the object attached to the hands until
release. Bow and lamp grips stay fixed as the body moves, and cape cloth
reads as clothing rather than a large inventory icon pasted onto Bloom.

All jump variants use takeoff, airborne and landing body poses. A small
ground shadow stays on the floor while Bloom rises, giving the arc a stable
reference. Only the actual cape jump shows the cape effect; ledge jumps,
return drops and knockback do not acquire an unrelated cloak.

## Recovery bugs found during the audit

Two existing bugs affected the apparent animation as well as gameplay:

- Taking damage during a jump could leave Bloom permanently suspended after
  the hurt timer ended. Hurt recovery now resumes an unfinished jump and
  reaches the ground.
- Rolling into a wall could leave Bloom hovering after the short knockback
  timer expired. Gravity now continues through the bounce until landing.

Gravity is applied once per update. Landing still checks water and pits, so
an interrupted jump over water correctly drowns instead of hovering. Real
enemy contacts and actual roll inputs reproduce both fixes in the gallery.
The 97 ordinary before/after clips have identical recorded gameplay traces;
the two recovery clips intentionally differ. Separate physical-input
comparisons also preserve all 940 recorded frames across 20 ordinary actions.

## Rendering and memory

The body still streams 32 OBJ tiles and the action layer 16. The new 16×8
ground shadow occupies two resident OBJ tiles. Pinning the bow effect to its
base frame avoids redundant uploads during body pose changes. No animation
fields were added to the save format.

The 582-context allocation sweep reached 838 of 876 available OBJ tiles,
leaving 38 tiles free. Menu icon pixels, palettes and restoration remain
exact. Repeated sword, shield and cape actions sustained 180 game updates
per 180 video frames in the Drain, forest, blight, cave and Heart samples.
These are representative samples with unrelated actors cleared, rather
than a worst-case combat benchmark.

## Coverage and evidence

The gallery contains 44 directional Drain actions, 27 repeated actions
across the three other backgrounds, 20 pickup/hazard/transition clips,
six foreground cases and two interruption cases. It records 99 of the 101
hero source frames naturally. The remaining legacy `jump_n` and `jump_e`
images are not selected by reachable gameplay; phased jump rendering is
covered in all directions. Swimming and sprinting are not implemented game
states. The unused talk/frozen enum values do not define additional action
animations.

Capture fixtures select inventory, location and facing and clear unrelated
actors. Actions then use real inputs and real generated terrain; the capture
tool does not assign animation poses or rewrite terrain. The cave and pot
room are entered through their generated mouths. Native PNGs are untouched
240×160 emulator output. GIFs enlarge complete frames 2× using nearest
neighbour sampling and retain every other video frame at approximately
30 fps. Two transition GIFs exceed the GIF palette limit; their native PNGs
remain exact. Filmstrips are chronological crops following the live player,
with time, state, source pose and height labels outside each crop.

The isolated rendering probe uses a documented physical-floor fixture to
inspect hardware OAM/VRAM and exact overlaps. Its fixture images are not
presented as generated gameplay screenshots.

| Check | Result |
| --- | ---: |
| Complete-suite hardware, motion and recovery probe | 489/489 |
| Sword timing, range, contact and input probe | 274/274 |
| Sprite memory and menu restoration | 2,046/2,046 |
| Retained artwork and physical contracts | 3,774/3,774 |
| Mechanics / lift / critical path and Heart / mysteries | 22/22, 14/14, 21/21, 28/28 |
| Foreground and surface rendering | 2,538/2,538 |
| Capture action activation | 166/166 |

The scope check compares packed ROM data. All environment animation frames,
physical metatile contracts, 26 unrelated sprite sheets, item icons, title
bitmap, palettes and original idle/walk art remain exact. Changes are confined
to Bloom's action bodies/effects, held-use graphics, liftable object graphics
and the rendering/recovery code described above.

## Reproduce

Run in the inner `bartgame/` directory after activating the environment:

```sh
source /workspace/setup/activate.sh
make -j4
python tools/bloom_suite_probe.py --skip-before --out /tmp/bloom-suite.json
python tools/bloom_probe.py --out /tmp/bloom-sword.json
python tools/bloom_budget.py --out /tmp/bloom-budget.json
python tools/wood_probe.py
python tools/lift_probe.py
python tools/critical_path.py --seed 0xB4A7 --boss
python tools/myst_probe.py
python tools/surface_probe.py
python tools/bloom_suite_review.py /tmp/bloom-clips --groups drain,forest,blight,cave,special,fore,interrupt
```

Omit `--skip-before` and provide `--before-rom`, `--before-map` and
`--before-header` to compare against a rebuilt frozen baseline. The gallery
baseline is the healthy-forest ROM with SHA256
`d346f72866060e452f8751efc51dc0b074d8cb240ceba159784b97939da78f59`.
The packed-art comparison tool, `bloom_suite_scope.py`, accepts the same
three baseline paths. `bloom_suite_review.py` also accepts `--match` for an
older group's `suite.json`, and `--only` for selected clip names.

Final ROM SHA256:

```text
d5f9eda0647c0b197011656cd9fd758f2438df6c4e7e212dd100d31fc3f130ac
```
