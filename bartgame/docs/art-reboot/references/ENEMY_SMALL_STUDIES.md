# Small enemy studies: movement before names

Status: twenty exploratory designs, ten alternatives for each of two existing
mechanic families. No winner is adopted. Old internal sheet names remain IDs;
the working concept labels below do not constrain future enemy naming.

The direct source is the user's 2026-10-31 request: invent unusual, funny or
weird forms that communicate movement, damage and actual weaknesses, rather
than reskinning a name. The shared art bible, direction log, reference register
and six-PDF application matrix were read before authoring. No new external
article, missing figure or commercial sprite is claimed as inspected.

## Actual behavior and the limits of visual promises

The small ground pursuer wanders at 0.5 pixels/update, begins chasing within
80 pixels, moves at 1 pixel/update during pursuit and disengages beyond 120.
Its two-pose gait changes every eight updates normally and four when chasing.
The four existing pose names are `walk_s1`, `walk_s2`, `walk_e1`, `walk_e2`.
The original renderer uses south art for north; west flips east. Positive
comparison profiles now append `walk_n1` and `walk_n2`, genuine north-heading
backs that the presentation helper selects using the existing facing and gait
clock. Every design preserves the original identifiers, planted lower baseline
and 16×16 OBJ canvas. The original profile-zero path remains available.

The small flyer rests, then wobbles through a 60–119-update flight, periodically
retargeting Bloom. It uses `rest`, `fly1` and `fly2`, with the two flight poses
alternating every four updates. Its altitude and movement come from the real
AI. Rest is folded/compressed, not a promise that the creature has landed.

Both have two HP, contact damage two and no separate shield, armor, protected
side or vulnerability window. Being apparently brass, a cup or a buckle does
not imply invulnerability. Hurt uses the existing twelve-update blink and
knockback; ordinary death frees the body immediately and uses the shared puff.
These study modules contain the complete current body pose suites, not an
invented body death sequence or a falsely advertised new combat mechanic.

## Ten ground pursuer alternatives

| Option | Working form | Motion/recognition hook |
| --- | --- | --- |
| 1 | Tarnished Teacup | Open black rim, continuous handle and alternating dirty feet. |
| 2 | Briar Turnip | Pale tapered root, thorn-leaf crown and two forked root contacts. |
| 3 | Runaway Boot | Open ankle and broad bent toe; the sole flexes rather than hovering. |
| 4 | Crab Buckle | Rectangular brass loop, dark opening and asymmetric grasping pincers. |
| 5 | Louse Loaf | Low crusty horizontal body, scored crust and short underside legs. |
| 6 | Acorn Urchin | Angular leafy cap, tapered nut and shuffling thorn roots. |
| 7 | Snapping Purse | Sagging leather bag, attached latch and toothed seam. |
| 8 | Crawling Inkpot | Wide bottle shoulder, dark opening, glass reflection and bent nib feet. |
| 9 | Coin Toad | Broad separate eye lobes, flattened jaw and alternating paddle toes. |
| 10 | Soap Slug | Chipped pale bar, narrow eye stalks and connected greasy underside. |

## Ten airborne hunter alternatives

| Option | Working form | Flight/rest hook |
| --- | --- | --- |
| 1 | Bell Wasp | Tiny living bell between full insect wings; folded wings in rest. |
| 2 | Tattered Glove | Large finger fan flaps around an eye-bearing palm, then closes. |
| 3 | Flying Teeth | A clamped resting jaw opens between short bony wing lobes. |
| 4 | Mouldy Bowtie | Cloth lobes lift and fold around the stable eye-bearing knot. |
| 5 | Lantern Gnat | Ragged wings carry a square light cavity with an attached handle. |
| 6 | Fishbone Kite | Rib-fins open/draw inward around one spine and folded tail. |
| 7 | Ribbon Ray | Broad pale membranes flex around a small face and trailing tail. |
| 8 | Mushroom Parasol | Narrow folded rest becomes a broad pulsing cap in flight. |
| 9 | Quill Moth | Pointed overlapping dirty quills fold around the thorax. |
| 10 | Wheezing Bagpipe | Side bellows flap while three uneven pipes identify every pose. |

## Native construction and review

`art/enemy_studies_small.py` exposes `frame(family, variant, name)`, returning
one indexed 16×16 image, plus `CONCEPTS`, `NOTES` and exact `FRAMES` registries.
The initial source pass used existing `bugs` material roles; final positive
profiles use the approved actor-only bank described below. Indices stay 0–15,
with transparent zero; no draw size, enemy hitbox or actor anchor changes.
Warm brown/sand planes contrast with cool wet greens and pale attached
highlights. No detached treasure-like sparkle is drawn.

G01–G03/G13 guided native silhouette, scale and one identity hook. G04–G07
guided small material ramps and broad upper-left planes. G08–G12 guided
controlled contours and focal contrast rather than pixel texture. G14/G15
guided connected motion, preserved contacts and full-family inspection.
G18 requires exact native evidence and explicit source/emulator labels.
The underlying tutorial page citations remain in `REFERENCE_APPLICATION.md`;
these applications are project decisions, not quotations from those authors.

Source review output under `small/` includes both ten-option boards, all-frame
strips with native/silhouette diagnostics, exact-palette source pose GIFs and
`small-native-validation.json`. All ninety authored frames (seventy original
poses plus twenty north-heading poses) pass
native shape/index/nonempty validation, and each required gait/flap pose is
distinct for a meaningful motion reason. Both boards were visually inspected
at 1× and 3×. Quiet Drain/ground/blight/stone value fields expose dark edges;
these fields are source diagnostics, not an assertion of real scene testing.

The source GIFs preserve native pixels and use holds derived from the current
animation clocks, rounded to GIF's ten-millisecond duration units. They are
explicitly pose loops: they do not simulate AI positions or prove combat.
Actual mGBA runs, varied terrain, hit feedback and real gameplay timing belong
to the parent capture/behavior review and must be linked separately.

Tradeoffs: a 16px canvas requires exaggerated hooks; glass/soap details are
material suggestions rather than unrestricted colors. Hardware-mirrored west
preserves the current engine contract but limits independent directional
lighting. The source boards establish clean shapes, not a winning
style, guaranteed recognition or a measured human usability score.

## Final comparison palette follow-up

The parent approved a dedicated small-enemy material bank after 120 source
comparisons on exact native Drain/healthy/blighted/cave background crops.
For positive enemy profiles only, ground pursuer, airborne hunter and hopping
body sheets use `enemy_studies_palette.colors()` through the existing `items`
OBJ10 alias. The original shared bugs/foliage bank also colors the Petal Cloak
and carried bushes, so it is preserved rather than globally recolored.

This changes the input material values, not these twenty indexed silhouettes,
frame IDs, gait, damage or collision. Earlier `small/` foliage-bank boards are
historical source-authoring diagnostics. The final generic source gallery is
regenerated with the actual actor-only bank and includes its API SHA256,
every frame's actual palette role/hash and exact native RGBA files. It must
not present the earlier shared-foliage colors as the final compiled result.

## North-heading pose correction

All ten ground pursuers now have true north views rather than front faces
moving backward. The cup's handle moves to the opposite side of its plain
back, the boot presents a narrow heel and rear seam, buckle pincers project
north above a leather back bar, the loaf's feeding end leads its crusted back,
and the toad shows broad rear thighs under far eyelids. Leaf roots, purse
straps, bottle shoulder and soap eye stalks similarly turn through construction.
These are not upside-down south sprites or eye deletion alone. Feet remain
authored at the original lower contact plane in both gait phases.

The added poses are presentation-only choices from existing facing and gait;
they do not change target selection, speed, radius, collision or HP. Generic
source coverage consequently rises from 620 to 640 frame instances across the
whole sixty-concept set. All original frame names stay first in the compiled
sheet and the two north names are appended.

## Production selection follow-up

Coin Toad9 and Quill Moth9 are now adopted by the user. Profile11 uses their complete existing poses; other alternatives remain historical studies.
