# Soft-body and ranged enemy studies

Status: **twenty unselected native concepts**, ten for each existing mechanic.
These are new source sprites for the current enemy studies, not a production
replacement choice. Names below label the drawings for review; existing enemy
names did not constrain their forms. Source is `art/enemy_studies_soft.py`.

The current user asks for unusual/funny forms whose movement and attack read
clearly, stand apart from the scenery, and follow the established native art
rules. The shared art bible, direction log, reference register and the G01–G18
application matrix were read before drawing. No new external reference or
unread PDF illustration is claimed as evidence for this pass.

## Mechanical contracts retained

The ranged walker keeps the existing sixteen-pixel canvas and blight OBJ bank.
It walks in four cardinal directions, alternating idle/walk poses; west mirrors
east. It has 2HP, contact damage 2, and launches a wall-stopped, sword-reflectable,
shield-blockable seed at speed 2.5. The 24-update shot sequence emits when the
timer reaches 12. Native mouths end at the actual N `(0,-14)`, S `(0,+2)`, E
`(+8,0)` and W `(-8,0)` muzzle anchors, relative to the actor feet. North-facing
forms have a top outlet rather than an invisible forward mouth.

Every variant supplies all nine existing `idle/walk/spit × S/N/E` frames.
Three **presentation-only** `charge_s/charge_n/charge_e` frames constrict the
opening and expand the connected body above its planted feet. The intended
use is the first six updates of the existing shot, before its open release
pose. No projectile, turn, hitbox or vulnerability timing is changed by these
source drawings. Ten matching eight-pixel `proj/seed` drawings retain the fx
bank and projectile mechanic, with attached highlights and a coherent solid
body rather than loot-like sparkle crosses.

The hopper keeps its three existing `idle/squash/jump` frames, sixteen-pixel
canvas. Initial proofs used the bugs/foliage OBJ bank; the adopted follow-up
assigns hopper bodies the dedicated enemy material bank in physical OBJ slot ten
(`items` alias), preserving the original bugs bank for Petal Cloak and bushes. It has 4HP and contact damage 2, wanders at
0.125 pixels/update, then squashes for 18 updates when the player is within
72px. The hop moves at 1.25 pixels/update under the existing gravity; nearby
landings hold the squash for 24 updates. Every state remains sword-vulnerable.
The drawn seam, shell, mouth or expression is not a new armored/vulnerable
phase. Actor z/shadows describe the actual hop; source pose animations do not
pretend to simulate physics.

Both mechanics retain the engine's twelve-update hurt blink/knockback and
shared eighteen-frame puff after immediate ordinary-enemy removal. There is
no newly invented death or stun interval in this art-only family. Bloom,
backgrounds, shared glitter and companion attack mechanics stay outside this
painter's ownership.

## Ranged alternatives

| # | Form | Readable mechanical hook |
| --- | --- | --- |
| 1 | Waddling kettle | Loop handle and heavy belly; the spout constricts, opens and recoils. |
| 2 | Bellows hen | Pumping feet, plump feather mass and a bill aligned to the seed direction. |
| 3 | Hollow porcelain mask | Broad pale face, empty eye sockets and an opening that reads as a mouth/vent in all views. |
| 4 | Barrel organ grub | Wooden box, folded bellows and brass outlet; no ornate texture noise. |
| 5 | Trumpet bellflower | Petals draw inward on charge and flare around the directional opening. |
| 6 | Inside-out umbrella | Pointed canopy ribs pull around a short handle and central nozzle. |
| 7 | Coughing pipe elbow | Angular pipe, clear dark mouth, attached dripping feet and bulging seam. |
| 8 | Conch-foot pilgrim | Offset shell coil over a fleshy sole, with a retracting feeding tube. |
| 9 | Trumpet tick | Bent brass tube over thin jointed feet; its bell is the dangerous end. |
| 10 | Blinking box camera | Square body, viewfinder and extending lens that spits rather than making a treasure flash. |

## Hopping alternatives

| # | Form | Readable mechanical hook |
| --- | --- | --- |
| 1 | Concertina mushroom | Broad cap over gills that fold flat and extend on the hop. |
| 2 | Tallow pudding | Unlit bent wick, pale greasy body and sockets that stretch with the wax. |
| 3 | Spring walnut | Split shell and root spring compress/release, without suggesting armor immunity. |
| 4 | Loose molar | A pale crown over wet roots; the whole tooth settles into the crouch. |
| 5 | Leech purse | A mouthy clasp and leech feet keep this animated bag separate from passive loot. |
| 6 | Puddle snail | Eye stalks fold and the shell pitches with the hopping sole. |
| 7 | Unruly boot | Eyes in its cuff; a sole folds under the shaft and snaps long in flight. |
| 8 | Haunted handkerchief | Asymmetric square folds and a knotted face, deliberately revised away from a glitter/star shape. |
| 9 | Pear bladder | Rubber body spreads wide on charge and pulls tall in flight. |
| 10 | Scum bucket | Dented rim, hinged handle and scum feet compress and extend together. |

## Applying the shared direction

- G01/G02/G03: start from a distinct mass and one identity hook, then preserve
  that hook through every pose. These twenty options change construction,
  contour and anatomy rather than swapping colors on the same silhouette.
- G04/G05/G06: use the existing RGB555 banks, a dark moving contour and broad
  upper-left material planes. Pale pink/tan masses distinguish the ranged
  forms; the hoppers use the dedicated jade/wood/ivory enemy bank after actual-
  background comparison showed the initial shared foliage values too subdued.
  The original terrain, cloak and carried-bush palettes stay intact.
- G07/G11/G12: wetness and metal use a few attached gleams. No unrelated
  sparkle, confetti or detached fluff explains an attack. The seed is a solid
  directional/tumbling object instead of a collectible star.
- G08/G09/G13/G14: all positions are native pixels, feet keep the y15 baseline,
  and top/body contours change with the action. Pose generation does not
  resize a finished image or shift an idle wholesale to fake animation.
- G15/G18: source boards include native-size context samples, nearest-neighbor
  inspection, every frame, grayscale/silhouettes and clearly labelled source
  pose loops. Parent-owned mGBA captures are separate evidence of AI behavior.

## Evidence and honest tradeoffs

`/workspace/setup/appearance-enemy-studies/soft/` contains:

- `spitter-ten-source.png`, `slime-ten-source.png`: 3× forms beside 1× samples
  over grass, blight, Drain and cave material fields. These are simple source
  context diagnostics, **not actual tilemap rooms or emulator output**.
- `spitter-all-frames-source.png`, `slime-all-frames-source.png`: all current
  and appended poses, with exact native transparent PNGs in `native/`.
- `spitter-motion-source.gif`, `slime-motion-source.gif`: source pose chronology,
  labelled as such; no claim that world movement or damage was simulated.
- `seed-companions-source.png`, `soft-silhouette-grayscale-source.png`.
- `native-validation.json`: 160 indexed nonblank frames (120 ranged, 30 hopper,
  10 projectile) with sizes, occupancy and raw indexed hashes. Per-variant
  animation frames differ, and all ten concepts have distinct hashes in every
  corresponding state. These checks measure valid/complete data, not taste.

Native pixel inspection caught a star-like first cloth silhouette and replaced
it with asymmetric square folds before final source delivery. Overview labels
and integer enlargements were kept outside the pixels. The kettle/camera/organ
emphasize outlet direction; mushroom/molar/boot offer the easiest hopping form
comparisons. Tiny pupil/handle details necessarily disappear sooner than the
main masses at 1×. The green hoppers need real forest/background motion review
to verify the dedicated palette while moving. The [palette review](ENEMY_PALETTE_REVIEW.md)
records all thirty small forms on four actual background crops. Seed companion
#5 was also revised from a teal diamond to an asymmetric bronze pod after
independent concern about its pale center reading as glitter. None of these
source diagnostics alone establishes the winning enemy design.
