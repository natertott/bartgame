# Enemy foreground separation and dedicated material palette

Status: parent adopted this palette for the thirty small-enemy concepts in
positive enemy-study profiles. Source `art/enemy_studies_palette.py` exports
`colors()` (a copy of sixteen RGB555 hex colors) and `applies_to(family)` for
`beetle`, `bat`, `slime`. It performs no global palette mutation on import.
Parent-owned integration assigns only those enemy sheets to the existing
physical OBJ bank ten (`items` alias) with these colors. Profile zero retains
its historical art/palettes. The forms remain unselected concepts.

## Why this follow-up was needed

The first source sheets inherited the background foliage palette. On simple
solid swatches their dark outlines separated, but the actual forest's green
floor, debris and warm paths shared many of the same body values. At native
size the sage-colored tooth/cloth/wax, the teacup lip, ribbon wings and several
green bodies lost identifying planes. Dark outline alone was insufficient.
This agrees with the user's request that enemies stand apart from scenery and
with shared G02/G05/G09/G12/G15: role-scaled silhouettes, distinct value groups,
selective edge strength, clear focal actors and scene review.

The solution changes **authored actor-bank inputs**, not screenshot grading.
No shape, frame clock, hitbox or movement changes are part of this palette.
The near-black moving contour remains identical. Green ramps become lighter
jade, wood becomes warm tarnished honey, and index fifteen becomes ivory for
material highlights, eyes and deliberately pale cloth/tooth planes. Cool
recesses remain dark; there is no bright outline around every creature.

| Index | Role | Original foliage | Dedicated enemy palette |
| --- | --- | --- | --- |
| 0 | Transparent | #000000 | #000000 |
| 1 | Moving contour | #101820 | #101820 |
| 2 | Cool green deep | #102828 | #182830 |
| 3 | Green shadow | #183830 | #204840 |
| 4 | Green body | #204838 | #386858 |
| 5 | Green lit plane | #306048 | #508870 |
| 6 | Green light | #487850 | #78a080 |
| 7 | Green highlight | #689858 | #b0c898 |
| 8 | Warm deep | #302820 | #302828 |
| 9 | Warm shadow | #483828 | #584030 |
| 10 | Wood body | #685038 | #886040 |
| 11 | Wood lit plane | #907048 | #c09058 |
| 12 | Warm highlight | #b09058 | #e8c880 |
| 13 | Cool recess | #183838 | #284850 |
| 14 | Cool cloth/wet plane | #305850 | #80a8a8 |
| 15 | Eye, ivory, material glint | #789880 | #f0e8c8 |

All colors are exact multiples of eight in RGB; each bank has fifteen visible
inks and transparent zero. The two material ramps remain distinct instead of
making every object pale or flattening wood/cloth/green into one ramp.

## Shared-bank hazard and protected artwork

The original `bugs` bank is **not** enemy-only. Contract bodies beetle/bat/slime
use it, but runtime per-frame aliases also assign it to `items/cloak`,
`huditems/cloak` and `lift/bush`. `icon32/cloak` has its own explicit menu bank.
Replacing the global bugs palette would silently recolor Petal Cloak graphics
and carried bushes, violating this pass's scope.

The chosen integration instead changes the three enemy sheet palette fields
and bank ten. Source audit found every actual SHEET_ITEMS spawn/draw supplies
`items_frame_pal`, whose aliases never select `items`; default sheet metadata
alone is not evidence of its rendered bank. The pause renderer temporarily
borrows spare banks but restores all OBJ palette bytes on close. Parent's
ROM/runtime audit must confirm these facts and preserved item/held/HUD output;
this source-review task does not claim the real-run proof itself.

## Actual-background comparison evidence

`/workspace/setup/appearance-enemy-studies/palette-review/` contains four
`all30-*-palette-comparison-source.png` boards for forest, blight, Drain and
cave. Each covers all ten variants of the three families: **120 before/after
scene comparisons**, showing an exact 1× pair and integer 2× inspection.
Left and right use the same current indexed sprite, placement and ungraded
background; only its input palette changes.

Background crops come from the previous immutable real mGBA capture set
`art-review/ui-menu-exploration/actual/v1/`: `hud-healthy.png`,
`hud-blighted.png`, `hud-sewer-max.png`, and `hud-cave.png`. Their exact file
hashes, 240×160 dimensions and crop coordinates are recorded in
`source-composite-provenance.json`. Every background pixel outside the sprite
mask is asserted unchanged. These are **SOURCE COMPOSITES**, explicitly not
new emulator captures or gameplay/occlusion simulations. Choosing actual
floor/path/slime crops improves context evidence but does not replace motion
review in full tilemap rooms.

Additional `*-all-pose-palette-source.png` boards show every current pose of
all thirty concepts before/after, at 2× inspection. Swatches show the real
quantized inputs. The separate soft source suite now uses the adopted actor
bank for hopper previews, while its old-bank comparison remains labelled.
The small-family painter's original pre-palette diagnostic boards are historical
source evidence rather than final colors.

## Independent visual observations and tradeoffs

All thirty forms were examined in all four comparisons, not only a favorable
example. The strongest gains are the teacup's rim/eyes, turnip's pale mass,
soap body, ribbon wing edges, wax pudding, tooth and handkerchief. Warm loaf,
boot, walnut and quill forms retain warmer material planes instead of turning
into white icons. Green snail and pear retain green bodies with clearer lit
planes. Inkpot and snapping purse remain intentionally darker, but their
lips/teeth/cavity edges now survive the busy forest field better.

The pale tooth and cloth use larger ivory areas because that is their material;
other forms use ivory mainly in small identifying groups. This is a useful
role/material difference, not a directive to maximize specular white pixels.
The lantern/soap can still resemble objects at rest: their eyes, limbs and
actual movement must carry the enemy reading. No palette can prove hostility
without animation and gameplay context. Parent's real mGBA suite remains the
final check for these thirty live alternatives.

A separate all-frame review flagged seed companion #5 as potentially cross-like
because its small pale center dominated a teal grain. Parent authorized a
narrow asymmetric bronze pod with one attached tail. It keeps the same 8×8
canvas, fx bank and reflectable-seed mechanic; the correction adds no star or
attack particles. Soft source proofs were regenerated after that pixel change.
