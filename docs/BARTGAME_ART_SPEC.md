# BARTGAME sprite specification

Everything the game draws as a sprite, sheet by sheet, with what each
frame is for and what the engine expects of it. Written so that an
artist or an art-generating model can produce the set without reading
the code. Tiles (the ground, walls and props) are listed at the end in
brief; they follow the same rules.

## 1. Hard rules (Game Boy Advance)

- **Format.** Hardware sprites, 4 bits per pixel. Each sheet uses one
  16-colour palette; colour 0 is transparent, so **15 opaque colours per
  palette group**. Several sheets share a group (listed per sheet). The
  build quantizes delivered PNGs to the group's palette, so deliver
  with as few colours as the drawing needs and never more than 15.
- **Pixels.** Exact dimensions as listed. No anti-aliasing, no partial
  alpha, no gradients finer than the palette. Every pixel is either one
  of the colours or fully transparent.
- **Delivery.** One PNG per sheet: frames side by side in the order
  listed, no gaps, with a flat background of pure magenta `#FF00FF`
  (or a real alpha channel). Alternatively one PNG per frame named
  `sheet_frame.png`. Frame order matters: the engine addresses frames
  by index.
- **Style.** Chibi top-down adventure in the manner of The Minish Cap,
  after the four BARTGAME style boards: "grime and glamour". A 1 pixel
  dark outline in the group's darkest colour round every figure, three
  tones per material plus a gleam, light from the upper left. Heads are
  more than half the figure. Faces are expressive.
- **Anchor.** Standing figures put their feet on the **bottom row** and
  are **horizontally centred** in the frame. The engine places a sprite
  at its feet point, so a frame whose feet sit higher will float.
- **West is east flipped.** The engine mirrors east-facing frames for
  west, so draw east only, and keep east frames free of details that
  would be wrong mirrored (a sword or shield in a specific hand is
  fine because the blade and shield are separate sprites).
- **Hit boxes** are fixed by the engine, not by the art. The Bloom's is
  12x12 pixels centred 8 pixels above her feet; small monsters 10x10
  or 14x14; the knight 14x26; the boss 28x28. Keep the visual mass
  within those.
- **Animation timing** is given in frames at 60 per second.

### Palette groups (current colours, for reference)

The build derives these from the style boards; an artist may propose
better ones, but each group stays at 15 colours. Listed in index order
1..15 after the transparent 0.

| Group | Used by | Colours |
|---|---|---|
| hero | the Bloom, sword, shield | `#1a0c10 #130b09 #231b14 #213017 #671914 #6e3c1c #c82428 #716937 #dd432a #739045 #e85f2f #eb7532 #ee8b3a #c3bb70 #f8dfa3` (outline, deep browns, tunic greens, petal reds and oranges, cream face) |
| folk | the five NPCs, the two big hub NPCs | `#100c14 #0a0203 #12081e #24150e #35172d #43164f #622858 #694128 #873d85 #825342 #9c5557 #b06e31 #b36f73 #d08c6c #f0c18f` (outline, violets, purple hide, browns, gold, mauve skin, cream) |
| portrait | dialogue faces | `#100c14 #06030a #412f3f #912037 #ee1e30 #7e7162 #d75945 #b27b6a #8f9e48 #f77d40 #d89f76 #fbde92 #e8c8a0 #2e8040 #f0c040` |
| fx | items, pickups, icons, effects, projectiles, arrows, the mouth | `#180c18 #901020 #e83040 #ff8080 #885818 #e0b030 #fff0a0 #ffffff #4a2888 #8a60d8 #c8b0ff #383848 #7a7a90 #c0c0d0 #58c8ff` (outline, reds, golds, white, violets, greys, blue glow) |
| bugs | beetle, bat, slime | `#100818 #2a1840 #482870 #7040a8 #a070d8 #d8b0ff #88a020 #d0f040 #f8ffc0 #801828 #e03048 #186860 #30b0a0 #80f0d8 #e8e8f0` (outline, chitin violets, chartreuse eyes, reds, jelly teals, bone) |
| blight | spitter, boss | `#141408 #304010 #507020 #80a830 #b8d848 #e8f888 #500818 #901030 #d82850 #ff6080 #ffb0c0 #401058 #9038c0 #f0e0c0 #ffffff` (outline, sick greens, raw flesh reds, violets, bone, white) |
| iron | knight, its sword | `#101420 #283048 #4a5878 #8090b0 #c0d0e8 #f0f8ff #601020 #c02038 #301848 #6838a0 #f0c8a0 #b08060 #906018 #f8d050 #ff4040` (outline, steels, crimson, violets, skin, golds, eye glow) |
| lift | carried objects | `#081410 #145838 #1e8048 #3aa858 #78d070 #d060f0 #2c3040 #4c5060 #787c88 #aab0b8 #3a2410 #6a4420 #a07040 #e0e4e8 #f8d050` |
| ui | map marks, dots, cursor | `#161020 #e8d8a8 #b8a070 #8a5c18 #e8b838 #fff4b0 #2a6a30 #58a048 #f03030 #ffffff #38a0ff #8890a0 #3a3a48 #ff80c0 #ffe070` |

## 2. The Bloom (the hero)

Sheet `hero`, **32x32**, group hero, **50 frames** in this order.

A chibi flower child: a ring of eight orange-red petals round a round
cream face with big dark eyes and a small smile; a green hood collar
over a green tunic with leaf sleeves; a belt with a gold buckle; brown
boots. About 30 pixels tall with the petals; the head (petals
included) is more than half the figure. She holds a sword only in the
attack frames and the engine draws the blade separately, so her hand
shows a hilt at most. Feet on row 31, centred on column 16.

Suffixes: `_s` faces the camera (south), `_n` shows her back (the back
of the bloom, petals and the hood), `_e` faces right in three-quarter
profile. West is `_e` mirrored.

| Frame | What it is | Requirements |
|---|---|---|
| `idle_s` `idle_n` `idle_e` | standing | the resting pose; also the first frame of every walk cycle |
| `walk_s1` `walk_s2`, `walk_n1` `walk_n2`, `walk_e1` `walk_e2` | walking | two frames, left foot forward and right foot forward, alternated every 8 frames with a petal bob of 1 pixel; both keep the feet on the bottom row |
| `atk_s1` `atk_n1` `atk_e1` | sword wind-up | 5 frames; the sword arm drawn back, body twisted the other way; no blade |
| `atk_s` `atk_n` `atk_e` | the blow | 5 frames; the arm fully extended toward the facing; the blade sprite is placed at the hand, so the hand must sit at a consistent spot: facing south at the bottom centre, east at the right edge mid-height, north above the head |
| `atk_s3` `atk_n3` `atk_e3` | follow-through | 5 frames; the arm across the body on the far side |
| `roll_1` | the duck | 3 frames; crouched, petals flattened |
| `roll_2` `roll_3` `roll_4` `roll_5` | the ball | a tucked ball turning a quarter turn per frame; each shows 3 frames, the four cycle twice (12 frames of tumbling); petals, tunic and boots visible as it turns; the ball sits on the bottom row; mirrored when rolling west |
| `roll_6` | landing squash | 3 frames; wide and low |
| `roll_7` | rising | 3 frames; between squash and idle |
| `hurt_s` `hurt_n` `hurt_e` | knocked back | eyes shut, petals flung back, arms out; also the death pose, which the engine blinks |
| `jump_s` `jump_n` `jump_e` | the Petal Cloak leap | legs tucked, the cloak's petals spread wide like a parachute above; drawn 2 pixels higher than idle |
| `itemget` | holding a prize up | facing the camera, both arms straight up, hands together above the petals; the prize is drawn separately 28 pixels above her feet; also the lifting pose when picking up a bush or stone |
| `carry_s` `carry_n` `carry_e` | carrying a load | arms straight up holding something over the head (the load is a separate 16x16 sprite drawn 44 pixels above the feet); standing |
| `carry_s1` `carry_s2`, `carry_n1` `carry_n2`, `carry_e1` `carry_e2` | carrying, walking | the two walk steps with the arms up |
| `drown_1` `drown_2` `drown_3` | sinking in water | 12 frames each; the figure sinking (chest deep, then shoulders, then only the petals above a ring of ripples); the water line stays near the frame's bottom; never mirrored |
| `fall_1` `fall_2` `fall_3` | falling into a pit | 8 frames each; shrinking and dropping toward the centre, arms up, then gone but for the petals; never mirrored |
| `guard_s` `guard_n` `guard_e` | shield raised | braced stance, the shield arm forward; the shield itself is a separate sprite placed in front |

## 3. The sword blade

Sheet `sword`, **16x16**, group hero, **3 frames**.

A short straight blade with a cross guard and a wrapped grip, steel
with a gleam line, gold at the pommel. The engine positions and flips
these round the Bloom's hand through the three swing phases and uses
`blade_s` as the A button's HUD icon.

| Frame | Orientation |
|---|---|
| `blade_s` | vertical, point down, hilt at the top edge (flipped vertically for north) |
| `blade_e` | horizontal, point right, hilt at the left edge (mirrored for west) |
| `blade_se` | diagonal, point to the lower right, hilt in the upper-left corner (flipped both ways for the other diagonals) |

## 4. The Bark Shield

Sheet `shield`, **16x16**, group hero, **3 frames**. Planks bound in
brass with a central boss. Drawn in front of the guarding Bloom.

| Frame | What it shows |
|---|---|
| `front` | the shield face on, held before her when facing south; also the HUD icon when equipped |
| `side` | the shield edge on, seen from the side, held out to the right (mirrored for west) |
| `back` | the shield seen from behind over her shoulders when she faces north: its rim and straps |

## 5. Items at 16 pixels

Sheet `items`, **16x16**, group fx, **20 frames**. Used in the HUD's
equipment slots and the shop list. Centred, with an outline; each must
read at 16 pixels on a dark navy slot.

| Frame | What it is |
|---|---|
| `none` | empty (fully transparent) |
| `bombs` | a Blightseed: a violet pod with a bright seam and a short fuse |
| `lamp` | the Grail Lamp: a gold chalice with a flame |
| `cloak` | the Petal Cloak: a cape of orange petals on a clasp |
| `key` | a small gold key |
| `heart_piece` | a quarter wedge of a red heart |
| `heart_container` | a full red heart with a gold rim |
| `gilt_big` | a leather purse of coins |
| `relic` | the Nun's relic: a cut violet gem in a gold setting |
| `heart` | a red heart (the healing petal in the shop) |
| `gilt` | one gold coin, face on |
| `bomb_pickup` | a single small Blightseed |
| `spark` | a four-point white star |
| `grail` | the chalice without its flame |
| `gauntlet` | the Root Gauntlet: a glove of bark and root, gold knuckles |
| `bow` | the Thorn Bow: a stave of dark gold wood, grey string, an arrow nocked pointing right |
| `arrow1` | one arrow: grey shaft, white head, red fletching |
| `arrow5` | five arrows banded together |
| `arrow10` | a quiver of ten |
| `hubcap` | the Drain Cap: a ringed, studded iron manhole cover with a violet gleam |

## 6. Pickups on the ground at 32 pixels

Sheet `pick32`, **32x32**, group fx, **10 frames**. What lies on the
floor after a bush is cut or a monster dies. Drawn about 24 pixels wide,
centred, resting on the bottom rows; the engine bobs them. Same
subjects as the 16-pixel versions, with more detail: `heart`, `gilt`,
`bomb_pickup`, `gilt_big`, `key`, `relic`, `grail`, `arrow1`,
`arrow5`, `arrow10`.

## 7. Treasure icons at 32 pixels

Sheet `icon32`, **32x32**, group fx, **16 frames**. The pause menu's
item grid (shown on navy slots with a gold frame) and the item-get pose
(held above the Bloom's head). About 24 pixels wide, centred both ways.
`none` (transparent), `bombs`, `lamp`, `cloak`, `key`, `heart_piece`,
`heart_container`, `gilt_big`, `relic`, `gauntlet`, `bow`, `hubcap`,
and four with no 16-pixel version:

| Frame | What it is |
|---|---|
| `map` | the Map of the Wood: a rolled parchment with a drawn path |
| `astrolabe` | a brass astrolabe: rings and a pointer |
| `sword` | the Bloom's sword, upright, for the menu |
| `shield` | the Bark Shield face on, for the menu |

## 8. Monsters

All face the camera, their back or east; west is east mirrored. Feet
on the bottom row.

**Rot beetle.** Sheet `beetle`, **16x16**, group bugs, 4 frames. A
domed violet shell split down the middle, a small head with chartreuse
eyes, six scuttling legs, two antennae. `walk_s1` `walk_s2` (seen from
above walking toward the camera; also used for north) and `walk_e1`
`walk_e2` (walking right). The two frames alternate legs every 8
frames.

**Spore bat.** Sheet `bat`, **16x16**, group bugs, 3 frames. Ragged
violet wings, a furred body, chartreuse eyes, bone-white fangs.
`fly1` wings up, `fly2` wings down (alternated every 4 frames, fast);
`rest` hanging folded, eyes shut, before it wakes.

**Gloom slime.** Sheet `slime`, **16x16**, group bugs, 3 frames. A dome
of teal jelly over a violet shadow, two dark eyes with a glint, a
gleam on the crown. `idle` the dome at rest; `squash` flattened wide
(the crouch before a hop and the landing); `jump` stretched tall and
narrow (in the air). The engine alternates idle and squash slowly
while it waits.

**Blight spitter.** Sheet `spitter`, **16x16**, group blight, 9 frames.
A round sick-green pod with two bulging white eyes, a raw red spout of
a mouth, warts, three stubby feet. For each of `_s` `_n` `_e`: `idle`
(mouth closed), `walk` (one foot forward, a lean), `spit` (the spout
open wide, cheeks puffed: the seed sprite leaves from the mouth).

**Thorn knight.** Sheet `knight`, **16x32**, group iron, 12 frames.
Chrome plate, a great helm with a crown of crimson thorns and a
burning red eye slit, a crimson tabard with a gold cross, a violet
kite shield rimmed in gold. The sword is a separate sprite. For each of
`_s` `_n` `_e`: `walk1`, `walk2` (a heavy two-step), `idle` (standing,
shield before him), `atk` (the sword arm raised high, the shield
tucked). Facing south the shield is on his left (screen right); facing
east he holds the shield before him toward the viewer's right.

**The knight's sword.** Sheet `ksword`, **16x16**, group iron, 2 frames.
A broad dark blade with a crimson grip and a gold pommel. `blade_e`
horizontal, point right, hilt at the left; `blade_s` vertical, point
down, hilt at the top. The engine places it low beside him at rest and
raised above during the attack, flipping as needed.

**The Blight Heart (boss).** Sheet `boss`, **32x32**, group blight, 3
frames. A swollen heart of raw flesh, veined violet, a single sick
yellow eye with a slit pupil in its face, blight roots growing from
the top lobes. It flies. `pulse1` relaxed, `pulse2` clenched smaller
(alternated every 16 frames, a heartbeat); `hurt` flinching, the eye
shut, lit pale. Centred, filling most of the frame.

## 9. Projectiles and arrows

**Projectiles.** Sheet `proj`, **8x8**, group fx, 3 frames. `seed` a
dark round seed with a highlight (the spitter's shot; the sword
deflects it); `spore` a soft violet puff (the bat's, also deflected);
`shard` a grey splinter (shatters on the sword). Each a round blob
with a 1 pixel outline, centred.

**Arrows in flight.** Sheet `arrow`, **16x16**, group fx, 3 frames.
A grey shaft, white head, red fletching, 14 pixels long. `e` pointing
right (mirrored for west), `s` pointing down, `n` pointing up.

## 10. Effects

Sheet `fx`, **16x16**, group fx, 13 frames, all centred in the frame.

| Frame | What it is |
|---|---|
| `puff1` `puff2` `puff3` | a grey dust puff growing then breaking into specks (6 frames each): a monster's death, a landing |
| `clang` | a white and gold four-point flash with a ring: a deflected shot, a blocked blow |
| `blast1` `blast2` `blast3` | a Blightseed burst: a small white core, then a wide gold and red ring, then violet smoke (4, 8, 12 frames) |
| `flame1` `flame2` | the lamp's flame on a web or thorn, two flickering shapes alternated every 4 frames |
| `bomb1` `bomb2` | a placed Blightseed with its fuse, normal and flashed brighter (the engine alternates faster as it is about to burst) |
| `firefly1` `firefly2` | a white spark in a gold glow, bright and dim |

**The mouth in the ground.** Sheet `mouth`, **32x32**, group fx, 3
frames. The Drain Cap's exit: lips of blight violet in the ground part
(`m1`, 10 frames), open on a dark gullet ringed with teeth and a red
tongue (`m2`, 16 frames), then clench shut (`m3`). Seen from above,
centred; the Bloom is drawn sinking into it.

## 11. Carried objects

Sheet `lift`, **16x16**, group lift, 4 frames. What rides above the
Bloom's head and is thrown. `bush` a round green shrub; `rock` a grey
stone; `boulder` a larger, darker stone with a crack; `pot` a brown
clay pot. Each centred, resting on the bottom rows, outlined.

## 12. Folk (NPCs)

**Small NPCs.** Sheet `npc`, **16x32**, group folk, 5 frames, facing
the camera, feet on the bottom row.

| Frame | Who |
|---|---|
| `sage` | the Pale Gatekeeper: a tall violet hat with a gold band, a long pale face and nose, white hair, a violet robe hemmed in gold, a staff crowned with a violet-glowing orb (used only where she appears small) |
| `merchant` | the Billious Peddler: hunched under a red hood, purple hide, a hooked nose, gold eyes, a gold medallion, a pack behind him |
| `hermit` | the Hermit Knight: bald, a white beard, plate gone to rust, a crimson sash, a rusted sword at his hip |
| `nun` | the Weeping Nun: a white wimple, a dark habit, folded hands, a gold cross, a tear on her cheek |
| `gardener` | the Blind Gardener: a green hood, a blindfold, a grey beard, a brown apron, a rake, a flower in his belt |

**The hub's two, large.** Sheet `folk32`, **32x32**, group folk, 4
frames; about 30 pixels tall, feet on the bottom row, facing the
camera. `sage_1` the Gatekeeper standing with her staff; `sage_2` the
same with her orb flared bright (shown briefly, as a blink). `merchant_1`
the Peddler behind his counter, hands together; `merchant_2` the same
with the hands rubbing, a glint in the eye (also brief). Keep the two
frames of each pair identical except for the change, or the blink will
jitter.

## 13. Dialogue portraits

Sheet `portrait`, **32x32**, group portrait, 7 frames. A bust, face
filling the frame, shown in a gold frame on navy at the left of the
text box. Lit oval faces with a shadow lower right, eyes with a glint,
a dark outline round everything. Opaque to the frame edge is fine.

`hero` the Bloom smiling; `hero_surprised` the Bloom with round eyes
and an open mouth; `peddler`; `gatekeeper`; `hermit`; `nun`;
`gardener` (as described above).

## 14. Map marks

Group ui. Drawn over the pause menu's parchment map.

**Marks.** Sheet `marks`, **16x16**, 13 frames, for the zoomed cell:
`here` the Bloom's petal head; `door` a dark doorway; `folk` a hooded
figure; `quest` the same figure with a gold mark; `relic` a violet gem;
`chest` a closed chest; `heart` a red heart (a shrine); `boss` a dark
cracked heart; `crack` a cracked wall; `web` a cobweb; `lock` a padlock;
`chasm` a dark gap; `thorn` a thorn bramble. Simple, high contrast,
centred.

**Dots.** Sheet `dots`, **8x8**, 12 frames, the same subjects without
`heart`, as round dots of one colour each (the engine's overview map):
`here` red, `door` slate, `folk` white, `quest` gold, `relic` pink,
`chest` gold, `boss` red on dark, `crack`, `web`, `lock`, `chasm`,
`thorn` in muted tones.

**Cursor.** Sheet `cursor`, **32x32**, 1 frame `cell`: a gold corner
bracket frame the size of one overview cell (32 wide, 24 tall, drawn
in the upper 24 rows), transparent inside.

## 15. Tiles, in brief

Background tiles are 16x16 (some 32 or 48 wide pieces split into
16x16), one 16-colour palette per area, drawn to wrap where they
repeat. The style boards cover most of these already; the ones still
hand-drawn are marked.

- **Forest** (group forest, 15 colours): grass in three variants,
  flowers, tall grass, path, path edges; shore edges round water in
  every combination (hand-drawn, 30 tiles); meadow, clover and
  mushroom-ring clusters (hand-drawn).
- **Wood** (overlay layer, shares the forest colours): canopy walls in
  two variants with a glint and a lantern (animated), bushes, logs,
  fences, thorns, two oaks as 32x48 pieces (crown quarters, trunk
  halves), the hollow and thicket cave sets (hand-drawn).
- **Stone** (water and ruins): water with animated foam edges in every
  combination, lilies, rafts, a waterfall, locked and open doors,
  chests closed and open, torches, cracks, webs, statues, stairs.
- **Cliff**: ledges south and north with ends, rocks in three sizes,
  boulders, pits, bridges, the cave set.
- **Blight**: purple ground in three variants, veins (animated),
  crystals, dead trees and blighted oaks (2x3), walls plain and lit,
  pools, mist.
- **Sewer** (the Drain): floors in three variants plus grime, cracks,
  moss, puddles, bones, mushrooms, drips; walls plain and with cracks,
  moss, chains, drips, webs, fungus, tallies, a window, a skull, rust;
  water with scum, bubbles, glints and edges; a grate, the big drain in
  four quarters, pipes vertical and horizontal, ladders, torches,
  lanterns, two banners, an arch, rubble.
- **Props** (the stall): candles (animated), counter, awning halves,
  rug quarters, barrel, crate, skull, pot, gold.

## 16. The HUD and boxes

8x8 BG tiles in the HUD palette (cream, ink, three heart reds, three
golds, grey, navy, blue, violet, slate): hearts full, half and empty; a
coin; a key; a bomb; the A, B, L and R button badges; item slots in
four corners, lit and unlit; a box frame (corner, top, side, fill,
bottom corner, bottom) in gold on navy; a cursor hand; map cells; a
rule; an arrow. These are drawn at 8x8 and the board's drawings do not
scale to that size cleanly, so they are the one place where the art
is made for the game rather than cut from the boards.

## 17. Checklist for a delivery

1. Every frame at its exact size, in the listed order, on magenta or alpha.
2. At most 15 opaque colours per palette group; outline in the group's darkest colour.
3. Feet on the bottom row and centred for every standing figure; east frames only, never west.
4. Pairs that alternate (walk steps, blinks, pulses) differ only where they should.
5. Attack frames without a blade; the hand at the stated spot.
6. Nothing drawn outside the frame; petals included.
