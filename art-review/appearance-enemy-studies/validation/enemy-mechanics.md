# Current enemy mechanics and complete art scope

Inspected 2026-10-31 from source baseline `a9e09e5`. The six implemented AI
families require **60 proposals: ten alternatives per family**. Their source
identifiers remain useful for code/contract references; they do not constrain
new creature concepts. There is one stronger melee miniboss with the same AI,
not a seventh enemy family. Projectiles, weapons and hurt/death effects are
supporting parts of those six animation suites.

The source files and their inspection hashes are recorded in
`enemy-mechanics.json`. This is a code inventory and review plan, not a claim
that the new art or real-ROM review is finished. No new external reference
was read; the existing PDF applications and art bible guide this work.

## Native contracts and behavior

| Mechanic | Source key / native body | Current required body frames | Actual behavior / readable cue |
| --- | --- | --- | --- |
| Ground pursuer | `beetle`, 16×16, bugs/foliage palette | `walk_s1`, `walk_s2`, `walk_e1`, `walk_e2` | Wander at 0.5px/update, chase at 1.0 inside 80px, lose target beyond 120px. The gait doubles speed during chase. West mirrors east; north currently shares the south view. Use legs, rolling contact, or a forward-reaching silhouette to show intent. |
| Airborne rest/chaser | `bat`, 16×16, bugs/foliage | `fly1`, `fly2`, `rest` | Folds/rests 30–119 updates initially, then flies for 60–119; later rests 40–119. Flight is 1px/update with heading wobble, retargets every 16 updates, ignores tile collision, and bobs at z12±4. Open/closed silhouette must distinguish the two behaviors. |
| Projectile shooter | `spitter`, 16×16, blight | `idle/walk/spit` for S, N, E; W mirrors E | Cardinal 0.375px/update walks of 30/60/60/90 updates. If facing the player at the end, shoots 75% of the time. A shot lasts 24 updates, emitting one seed at remaining timer12. The spit pose starts below timer18. Mouth/nozzle must show the actual shot direction, including north. |
| Aimed hopper | `slime`, 16×16, bugs/foliage | `idle`, `squash`, `jump` | Wanders at 0.125px/update; detects inside72px and crouches18 updates before a locked-direction hop at1.25px/update. Launch z0.5/zvel1.75 and gravity0.125 give30 airborne updates. Near landing returns to24-update crouch; far landing to30-update idle. Compression then extension should make the hop predictable. |
| Heavy melee pursuer | `knight`, 16×32, iron/stone | `idle`, `walk1`, `walk2`, `atk` for S, N, E; W mirrors E | 0.375px/update chase, retarget every16 updates;16-update windup,14-update swing,24-update recovery. Swing damage is live at remaining timer4..11 before decrement. The whole body should announce weight transfer, facing and recovery. |
| Floating phase boss | `boss`, **32×64 actual override**, blight | `pulse1`, `pulse2`, `hurt` | 40HP. Above26HP drifts and emits8-spore rings;13–26 alternates aimed3-spore fans and two ground pursuers;12HP or less lunges40 updates at1.75px/update before fans. Pulse, emission, adds and lunge need distinct presentation states if expanded. |

The old contract JSON still says boss32×32, but `reboot_actors.SIZES` and the
actual asset builder use32×64. Actor drawing anchors every body by its feet:
`x - w/2, y - h - z`. Do not center a boss on its64px padding or move its
collision footprint because its proposal changes shape.

## Hurt, death and real weaknesses

- Health/damage units are eighths of a full heart. Common enemies have HP
  2/2/2/4/10; their contact damage is2, except melee4. The base sword deals2.
  The mystery miniboss has20HP and uses the same melee family/animations.
- **Every normal state of every enemy can be hit.** The melee enemy has no
  shield, front armor or back-only weakness. A closed shooter mouth and a
  boss shell must not imply immunity. Crouch, windup and recovery are genuine
  timing cues; they are not bonus-damage or vulnerability-window mechanics.
- Common hurt sets12 iframes plus12-update knockback. The common routine
  returns during knockback, pausing AI timers and existing body-frame updates.
  Drawing blinks while `iframes && (gFrame & 2)`. There are no old ordinary
  hurt-body frames. A presentation-only hurt pose may be added while retaining
  these numbers and movement.
- The existing boss `hurt` pose is effectively skipped on ordinary weapon hits:
  the common knockback return prevents `boss_update` from selecting it until
  the iframes expire. A new hurt presentation should be selected outside that
  skipped AI path; do not change health/AI timing just to display it.
- Normal death frees the actor immediately, rolls loot and shows shared
  `FX_PUFF`: puff1/2/3 over18 updates. A complete proposal should include its
  replacement death/support sequence, without delaying the kill/reward logic.
- Boss death lasts120 updates: x-shake, puff every8 and hit sound every16,
  then six blasts, add removal and the Grail. Damage/collision flags turn off
  at defeat. Its source currently keeps pulsing while dying.
- Sword damage uses a2D box and does not reject airborne enemies by z. Ordinary
  actor/contact and projectile overlaps require relative z<12. Do not claim
  flyers/hoppers are categorically immune while airborne.

## Weapon and projectile companions

The melee weapon sheet is16×16 with `blade_e` and `blade_s`; preserve grips
(2,8)/(8,2), or coordinate a truthful new anchor. Current world hand offsets
from feet are N(5,-17), E(7,-16), S(4,-13), W(-8,-16). Windup raises the
weapon; north draws the body before the weapon, other facings reverse that
order. The real directional swing boxes are20×20, relative to feet:
N(-10,-36..10,-16), S(-10,-8..10,12), E(6,-20..26,0), W(-26,-20..-6,0).
The body's old `atk` pose does not distinguish windup from swing, a clear
presentation gap for the new full suite.

The shooter seed leaves at2.5px/update and deals2; muzzle offsets from feet
are N(0,-14), S(0,+2), E(+8,0), W(-8,0). Boss spores deal2, with ring speed1.0
and fan center1.5/sides1.25. Seeds collide with walls; spores drift through
canopy. A sword reflects both at3px/update into friendly projectiles. The
forward held shield can block incoming damage. All share the8×8 `proj`
canvas. `shard` has an existing frame/handler but no current enemy emitter.
Friendly arrows, general flame, shared loot and Bloom art are outside the
requested enemy-redesign scope unless specifically needed for a companion.

## Where these enemies appear

The procedural forest chooses common enemies from theme/stage. Theme0 favors
pursuers/flyers; theme1 shooters/hoppers/pursuers; theme2 flyers/hoppers; later
stages introduce the heavy melee family. Other themes mix the first four.
Mystery combat waves use the same picker. A miniboss trial has one20HP melee
enemy plus two pursuers. The generated goal arena spawns the boss; its middle
phase spawns pursuers. The Drain hub has no ordinary enemy spawn roster.

## Proposed review evidence

1. **Complete source suites:** validate every contract and new state frame,
   indices0–15, native hardware canvas, nonblank painted bounds, meaningful
   distinct silhouettes, stable foot/muzzle/grip anchors and legal RGB555
   banks. Publish every proposal's full atlas, 1×/integer zoom, grayscale and
   fixed-background comparisons. Animation loops composed from source poses
   must be labelled source sequences, never actual mGBA gameplay.
2. **Actual native runs:** freeze ten enemy-profile ROMs. Boot a fixed seed,
   use real world generation/spawns, and position/heal the player or clear
   unrelated actors only as disclosed fixtures. Record actual AI state, timer,
   frame, direction, hp, position, height and projectiles each update. Never
   set animation state/frame/timer/phase to fabricate a behavioral clip.
3. **Behavior coverage:** six families in each profile; movement/chase, folded
   rest/flight, shot direction/emission, prehop/flight/landing, melee
   anticipation/live/recovery, all boss HP phases and real hurt/death. Source
   atlases establish full authored coverage; clips establish actual state
   selection and cues. Do not imply every facing occurs in one clip.
4. **Damage evidence:** actual player inputs create hurt, deflection and death;
   health fixtures may accelerate boss phase checks but must be disclosed.
   Compare movement/AI/health/timer traces across variants to establish that
   appearance changes do not alter mechanics.

`wood_probe.spawn_enemy` currently forces idle/timer200, so it cannot be used
unchanged as natural-AI evidence. `gDbgSpawn` can spawn an ordinary common
enemy, but also needs a disclosed position fixture. Boss should come from the
actual generated goal room; passing EN_BOSS through the ordinary debug hook
would initially give it the melee sheet until `boss_spawn` establishes it.
