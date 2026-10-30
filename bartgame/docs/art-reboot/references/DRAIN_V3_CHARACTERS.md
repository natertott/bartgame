# Drain v3 character studies

Status: five exploratory local alternatives, based on the user's preferred
second-pass frog #1 and wizard #5. The user's follow-up explicitly requests
continued variation in both characters; they are not fixed across all rooms.

The art bible, direction log, reference register and recorded character
reference notes were read before editing. This pass applies the already-read
reference principles: silhouette/negative space and role proportions (R2
pp3–6), planted connected idle (R2 p7), directional light and restrained
material values (R1 pp4–5; R6 pp15–24), native drawing and review (R2 pp4–5,
R4 pp7–14). No new source illustrations are claimed as inspected in this pass.

## Shared identities retained

All frogs keep warm green skin, raised cream eye lobes, a broad/heavy jaw,
short joined webbed feet and a quiet brown working apron. They look vacant
or drowsy instead of heroic or sinister. All wizards keep the preferred
pointed purple cowl, fully hidden face, one quieter gold seam at most, and a
separate staff with a warm flame. No beard, glowing eyes or decorative badges
replace the selected identity.

## Five local shape plans

| Option | Frog | Wizard |
| --- | --- | --- |
| 1 Ashlar & Amber | Closest anchor: round heavy jaw and widely raised eyes; plain preferred apron/body. | Closest pointed-cowl anchor, broad clean drape and restrained warm fastening. |
| 2 Crooked Brickwork | Uneven eye heights, lopsided slack mouth and wider hunched haunches. | Tip bends sideways while the shoulder/hem remain rounded and bowed. |
| 3 Floodworn Flags | Narrower soft jaw, broad sleepy upper lids and a quieter apron. | Tall narrow point, long narrow drape, cooler purple material shift. |
| 4 Crumbling Vault | Low wide jaw, crooked smile and slumped broad body/apron. | Worn pointed hood and deliberately torn hem; cloth breaks describe real tears. |
| 5 Silted Cloister | Compact hunch and conspicuous high pale eyes; narrower apron. | Shorter, broader pointed cowl and broad shoulders, restrained fastening. |

The world head masks and every expression were reauthored for all five. All
wizard poses were rebuilt around the five related pointed-cowl shapes; flame
phases were reworked as connected tapered fire. The ten48×48 portraits were
separately authored, preserving their matching world eye/jaw/hood proportions.
No portrait is an enlarged or reduced world sprite.

Option1 intentionally retains the preferred v2 frog #1's fifteen body/action
frames. Its new head changes every assembled expression; the other four body
families change. Thus135/150 individual world frame geometries differ from
the same-number v2 sets, not150. Adding arbitrary pixels to force a hash
change would undermine the user's preference and the common art discipline.

## Native and animation contracts

- Five16×16 head frames, fifteen32×32 body frames, six32×32 wizard frames,
  four8×8 flame frames and two48×48 portraits per option.
- Existing identifiers, action order, palette-bank roles and canvas sizes stay
  unchanged. Breathing frame remains appended at ID14.
- Rest/breathe head anchors stay(8,6)/(8,7); upper body and head compress together
  while body rows29–31 remain byte-identical. All five joins overlap naturally.
- Flame origin stays(23,1), its base meets the staff at body(26,8), and every
  flame phase forms one connected silhouette. Wizard cloth/staff use no
  emissive13/14 ink; only flame is affected by the runtime warm pulse.
- Every returned palette has sixteen legalRGB555 colours including transparent
  index0; every source image is indexed4bpp-range opaque pixel art.

## Review

`npc-concepts.png` shows1×/4× actors and2× portraits.
`preferred-to-new-characters.png` compares the preferred v2 actor anchors with
all five new composites at1×/3×.
`silhouettes-and-values.png` shows flat silhouettes and a three-value check.
`idle-study-N.gif` files are source pose studies, not emulator recordings or a
claim that their presentation timing matches the game.

Independent source review by the gallery agent found the preferred identities,
world/portrait consistency and sleepy/pointed/torn features clear at native
size, with no blocker. The frog #5 apron button remains subordinate to its
throat and eyes. The actual counter masks most body detail, so eye lobes,
expression and shoulders must carry the market view. Actual packed-ROM,
background/occlusion and mGBA motion review are performed by the parent task.

`native-review.json` records273/273 passed source checks, all source frames,
retention exceptions, fixed feet, connected head/body and flame shapes, five
distinct actor composites, legal canvases/palettes and the frozen painter hash.
An initial validator incorrectly required every world frame to differ from
v2; that assertion was replaced by an explicit check that only the approved
fifteen option1 body/action frames are retained. The changed-frame count is a
descriptive finding, not a reason to add arbitrary pixels. These checks
establish native source integrity and scope, not a subjective quality score.

Frozen painter SHA256:
`3ac84ca8f1024bfbbbb391f3c817d06d73609e82d17239aa05981e0633b130bb`.
