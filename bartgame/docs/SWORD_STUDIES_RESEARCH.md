# Sword studies: Zelda evidence and Bloom design rules

Research date: 2026-10-29. The five Bloom options are review prototypes; the
user will choose their preferred direction before a production change.
The reference graphics were inspected at native resolution and integer
magnification. Bloom's studies use original native drawings and the existing
GBA palette, rather than imported or reduced Nintendo sprites.

## What was actually studied

| Reference | Pinned source revision | Evidence inspected |
| --- | --- | --- |
| Link's Awakening DX | `2a5c2c0d6df93a54df81ae9e1fe28b5c2fd60d03` | Native Link and sword sheets; ordinary swing state machine; direction/body/blade/collision tables. |
| Oracle of Ages/Seasons | `21c924afdc8a13225e849214479d5113da2ec226` | Native Link/sword sheets; ordinary sword parent state; body animation script; weapon arc and collision radii. |
| The Minish Cap | `6fb6dfb4a7efbe24d0fd1dda5097af6131faacde` | Separate sword entity; body-frame-derived sword graphic/hitbox; animation-event collision and impact feedback. |

The numeric observations below are readings of native data and update code.
They are not claimed to be an emulator measurement of Nintendo's exact
button-to-first-hit latency. Input order, VBlank transfer, hitstop and special
states can affect that distinction. The Bloom studies must measure their own
real input, active state, body, blade and hardware display.

## Link's Awakening: the body and blade form one pose

The ordinary sword starts `SWORD_ANIMATION_STATE_DRAW` with countdown `3`.
`UpdateLinkAnimation` advances through the draw/start/middle states. Its
countdown table gives `3` to the next start state and `8` to the middle
state, then ends on state `4`. These are short, deliberately unequal holds,
not a sequence of equally spaced interpolation pictures.

The same direction-by-sword-state index selects:

- A dedicated Link body animation, not a standing body with a rotating arm.
- The sword's visible direction and position relative to Link.
- Small body sprite offsets for selected poses.
- The sword interaction rectangle and whether collision is enabled.

The native sheets visibly change the head/hat orientation, shoulder/chest
silhouette, arm reach and root/boot stance together. The small body reads
as turning into a cut despite its limited pixel count. The sprite renderer
composes Link from two 8×16 objects and streams the chosen native body tiles;
it does not rotate or filter a large illustration.

Primary sources:

- [UseSword and ordinary/static interaction setup](https://github.com/zladx/LADX-Disassembly/blob/2a5c2c0d6df93a54df81ae9e1fe28b5c2fd60d03/src/code/bank0.asm#L2198).
- [Body, blade and collision lookup tables](https://github.com/zladx/LADX-Disassembly/blob/2a5c2c0d6df93a54df81ae9e1fe28b5c2fd60d03/src/code/bank2.asm#L758).
- [Countdown-driven update and shared pose selection](https://github.com/zladx/LADX-Disassembly/blob/2a5c2c0d6df93a54df81ae9e1fe28b5c2fd60d03/src/code/bank2.asm#L986).
- [Native body frame-to-tile selection](https://github.com/zladx/LADX-Disassembly/blob/2a5c2c0d6df93a54df81ae9e1fe28b5c2fd60d03/src/code/bank20.asm#L1632)
  and [two-object sprite composition](https://github.com/zladx/LADX-Disassembly/blob/2a5c2c0d6df93a54df81ae9e1fe28b5c2fd60d03/src/code/home/animated_tiles.asm#L445).
- Native [body sheet](https://github.com/zladx/LADX-Disassembly/blob/2a5c2c0d6df93a54df81ae9e1fe28b5c2fd60d03/src/gfx/characters/oam_link_2.cgb.png)
  and [sword/effect sheet](https://github.com/zladx/LADX-Disassembly/blob/2a5c2c0d6df93a54df81ae9e1fe28b5c2fd60d03/src/gfx/characters/oam_link_1.cgb.png).

## Oracle: a short setup and a readable contact hold

The sword maps to body animation mode `0x22`. In Ages' normal above-ground
animation data, the script begins at `animationData19fef` and continues into
`animationData19ff2`:

| Duration in update ticks | Body frame base | Animation parameter |
| --- | --- | --- |
| 3 | `0xac` | `0x00` |
| 3 | `0xb0` | `0x02` |
| 8 | `0xb4` | `0x64` |
| 3 | `0xb0` | `0x06` |
| End marker | `0xb0` | `0x86` |

The last record contains a `0x7f` duration, but bit 7 of its parameter makes
the parent leave the ordinary swing immediately. It is **not** a 127-frame
recovery. The meaningful preceding holds are **3, 3, 8, 3 ticks**. Their total
is 17 script ticks; this is not an independently measured end-to-end input
latency. Special underwater, riding, charged and ring-modified actions are
separate paths and should not be conflated with the ordinary swing.

The weapon's post-update uses that animation parameter and Link's direction
to choose blade orientation and an arc-table entry. Each entry provides
collision radii and position offsets. For example, one entry has vertical
radius 9, horizontal radius 6 and an x offset of +16 pixels. The reference
therefore uses generous pose-dependent rectangles, rather than treating the
thin steel pixels as the entire practical contact area.

This gives two useful lessons. Hold an important outward pose long enough
to be read, rather than holding every angle equally. Also make the swept
contact region visually plausible and forgiving: showing only a tiny tip
while silently testing a broad distant rectangle is unhelpful, but requiring
the exact moving tip to coincide with an enemy for one update is brittle.

Primary sources:

- [Sword-to-Link animation selection](https://github.com/Stewmath/oracles-disasm/blob/21c924afdc8a13225e849214479d5113da2ec226/data/ages/itemUsageTables.s#L61).
- [Mode-to-script table](https://github.com/Stewmath/oracles-disasm/blob/21c924afdc8a13225e849214479d5113da2ec226/data/ages/specialObjectAnimationData.s#L262)
  and [ordinary script](https://github.com/Stewmath/oracles-disasm/blob/21c924afdc8a13225e849214479d5113da2ec226/data/ages/specialObjectAnimationData.s#L708).
- [Counter/parameter/frame decoder](https://github.com/Stewmath/oracles-disasm/blob/21c924afdc8a13225e849214479d5113da2ec226/code/specialObjectAnimationsAndDamage.s#L15).
- [Sword parent and end-marker handling](https://github.com/Stewmath/oracles-disasm/blob/21c924afdc8a13225e849214479d5113da2ec226/object_code/common/itemParents/swordParent.s#L50).
- [Shared blade animation, arc position and collision radii](https://github.com/Stewmath/oracles-disasm/blob/21c924afdc8a13225e849214479d5113da2ec226/object_code/common/items/postUpdate.s#L176).
- Native [Link sheet](https://github.com/Stewmath/oracles-disasm/blob/21c924afdc8a13225e849214479d5113da2ec226/gfx/common/spr_link.png)
  and [sword sheet](https://github.com/Stewmath/oracles-disasm/blob/21c924afdc8a13225e849214479d5113da2ec226/gfx/common/spr_swords.png).

## The Minish Cap: one body-frame contract

The sword is a separate entity, but `sub_080A78B8` selects its frame from the
player's body `frameIndex - 0x6a`. `sub_080A7A54` uses the same index to load
its mutable hitbox's x/y offset and width/height. Horizontal flip is reconciled
with the player's direction. Animation events also control collision in the
special airborne attack path. The exact ordinary animation timing is not
inferred from that airborne branch.

On wall contact, the implementation couples tile interaction, clipped impact
sound and a local effect. This is relevant to feel: the player learns not just
from the weapon's outline, but also from an immediate, localized response
when the weapon really meets something.

Primary source: [pinned PlayerItemSword implementation](https://github.com/zeldaret/tmc/blob/6fb6dfb4a7efbe24d0fd1dda5097af6131faacde/src/playerItem/playerItemSword.c#L266).
No exact Minish Cap ordinary-swing frame count or Link sheet size is asserted
here without decoding its corresponding animation data.

## Concrete problems in the current Bloom attack

The released native reboot has two clocks. The blade's five pictures change
at ages `2, 5, 9, 13`, but the body's three pictures change at ages `5, 9`.
The first live blade pose therefore appears while the body still shows its
preparation picture; the final live blade pose appears while the body has
already selected its third picture. Native pixel ownership and hitbox checks
alone do not make that motion convincing.

The original 15-update attack is live from ages 2 through 12. The cutting
mask excludes the grip/proximal four pixels and supplies one AABB per pose.
The short blade/trail is honest about those bounds but gives little indication
of the complete sweep. This research supports redrawing the performance and
its coverage together, rather than merely adding more flash to the same
arm/body timing.

## Rules for the five Bloom studies

1. Use one pose clock for body, hand, blade, trail and damage. Each option must
   state preparation, live contact and recovery clearly. No harmless recovery
   flare should imply that an enemy can still be hit.
2. Put weight into the pose: plant the rear root, counter-turn the shoulder
   and flower in preparation, turn the chest into contact, extend the front
   root, then settle. Keep the face readable. Do not stretch or rotate the
   completed bitmap; draw the key silhouettes natively.
3. Let a short, brighter cutting edge and a limited local trail describe the
   active sweep. The sword stays a consistent length. A full hemisphere,
   closed range cage or detached decorative ring obscures the action.
4. Make north reach visible beyond the flower. The far hand/shaft can be
   occluded, but the part that can hit must still have an understandable
   outward silhouette. Diagnose all four facings independently.
5. Avoid invisible gaps between active samples. Show and test the union of
   the swept region; if using per-pose AABBs, expose those actual boxes in
   the diagnostic view. A pretty painted arc is not proof of collision.
6. Contact must produce a timely real response. Use a visible target/HP
   change in the comparison captures, and distinguish actual hits from an
   explanatory overlay.
7. Show each option at normal speed first, then slowed and with a separately
   labelled hitbox view. Keep seed, background, target and camera comparable.
   Native GBA images remain the primary evidence; enlarged boards are for
   inspection only.

The five useful contrasts are compact fast slash, waist-led broad sweep,
step-and-cut, overhead chop and flowing reverse follow-through. These should
differ in stance, weight, arc and timing, while keeping Bloom's existing
identity and the game's common palette. They are alternative experiments,
not five upgrades that silently stack into the production game.
