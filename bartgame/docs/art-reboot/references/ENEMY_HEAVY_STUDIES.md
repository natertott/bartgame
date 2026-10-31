# Heavy-enemy animation alternatives

Status: ten original native proposals per mechanic family, not a selected
production replacement. Source authoring is `art/enemy_studies_heavy.py`.
The current user specifically permits disregarding enemy names; the labels
below describe forms for review and do not change AI names or gameplay rules.

## Basis and retained contracts

Read the shared art bible, direction log, reference register and the six-PDF
application matrix before drawing. Relevant inherited guidance is G01/G02/G03
(silhouette, scale and identity: R1 pp.4–5; R2 pp.3–8; R4 p.7 and pp.9–14),
G04–G09 (limited materials, directional mass and clear contours), G11/G12
(controlled texture and focal contrast), G14 (connected motion), and G15/G18
(full-family, native and scene review). The source-specific pages remain in
[the matrix](../REFERENCE_APPLICATION.md); this pass does not claim a new
article, missing illustration, or commercial game sprite was inspected.

Every drawing begins at its final integer pixel size. No high-resolution art,
filtered reduction, sampled artwork, alpha fringe or unrestricted palette is
used. Knight and weapon retain the existing iron OBJ bank, whose material is
`reboot_core.PALETTES['stone']`; the boss retains the blight bank. Each has
transparent zero plus at most fifteen RGB555 inks. Attached wet/gold highlights
support the form. No detached treasure-like glitter is added to attacks.

The actual native canvases differ from guesses based on the old contract:

| Family | Native canvas | Feet / grip | Complete authored frames per option |
| --- | --- | --- | --- |
| Heavy walker, internal `knight` |16×32|feet(8,32); runtime hands N(5,-17),E(7,-16),S(4,-13),W(-8,-16) relative to feet|12 original +12 appended =24|
| Its companion `ksword` |16×16|blade_e grip(2,8); blade_s grip(8,2); runtime flips north/west/raised|2 original|
| Phase boss, internal `boss` |32×64|feet(16,64); main collision center(0,-22),halfwidth14,halfheight20|3 original +10 appended =13|

Every original frame name remains first and present. The old boss contract
says 32×32, but the actual production painter overrides it to 32×64; that actual
streamed canvas is preserved. Main boss masses stay concentrated in x2–29,
y22–62; thin stalks/crowns may extend above, like the existing arteries.

The weapon drawings keep their physical grip and native reach. Vertical art
is a lossless integer transpose of the horizontal design, so the weapon does
not change material or scale with facing. West uses the engine's existing
mirroring. The body shifts its upper mass and bends its legs around the fixed
grip, rather than detaching the hand or substituting a moving arm alone.

## Ten heavy-walker concepts

| # | Form | Movement and attack reading |
| --- | --- | --- |
|1|Bell Washer|Flared, tarnished skirt, dark eye/cavity and tiny braced legs. The entire bell tilts into its clapper-blade strike.|
|2|Walking Tureen|A cracked pale vessel with lid and handles; the planted bowl shifts behind a ladle-shaped weapon.|
|3|Censer Stilt|A hot hanging bowl, narrow chained arms and long knees. The bowl pulls back before the incense knife cuts.|
|4|Molar Mason|A stained tooth crown and root-knees. Its cleft crown tips and its whole tooth drives a broad chisel.|
|5|Bad Boot|Folded cuff, laces and heavy dark sole. Its ankle compresses and stamps through a shoehorn cut.|
|6|Moth Confessor|Folded uneven wings, antennae and pale collar. The head and wing-cape lean together around a thorn-tine.|
|7|Snail Porter|Asymmetric coil over a soft body and stalked face. The body braces under its load before the reed cutter swings.|
|8|Broken Marionette|Wooden face, articulated torso and knees. Its body counter-rotates around the fixed toy-saber grip.|
|9|Oyster Bailiff|Fluted shell lobes around an animate pearl/mouth. The lobes shift as the shucking blade strikes.|
|10|Chandelier Drudge|Sooty stem, curled branches and three attached flames. Its stem and entire candle crown bend into the wax-edged cut.|

Each has south/north/east walk, idle and original attack, plus separate
windup/strike/recover/hurt for those three facings. West mirrors east. The
original atk frame intentionally aliases the corresponding strike drawing;
those three aliases are meaningful compatibility, not arbitrary pixels added
to defeat a uniqueness check. Each option has 21 unique body drawings in 24
named slots. All ten idle silhouettes differ.

The actual mechanic remains a tough slow chaser: HP 10 (trial miniboss 20),
contact/swing damage 4, movement 0.375 pixels per update, 16-update windup,
14-update swing and 24-update recovery. The live sword interval uses the
existing timer 4–11 front 20×20 box. Every form remains damageable from any side
and in every living state. No shell, metal, eye, crown or cavity represents
new armor immunity or an exclusive weak point. Recovery communicates the
existing stationary opportunity; it does not multiply damage.

## Ten boss concepts

| # | Form | Existing phase behavior made visible |
| --- | --- | --- |
|1|Split Coronation Bell|A ruptured gilded sounding body opens its cavity before firing; the low bell lip thrusts during a lunge.|
|2|Glutton Chalice|A huge living vessel with a toothy bowl and sagging stem. Filling, opening and tipping make it clearly a hostile body rather than the Grail pickup.|
|3|Silk Stomach|A stitched hanging sack tightens around its vent, releases, then sags; its central stitch split widens while dying.|
|4|Crowned Leech Coil|A wet ring cinches around a fanged front head; the jaw stretches before release and pursuit.|
|5|Funeral Peacock|A drooping beak and diseased uneven fan prepare a volley; its fan and breast collapse into the dying pose.|
|6|Slime Banquet|Three mouths occupy a wet heap on a platter. The heap rises before firing and slumps in recovery.|
|7|Choir of Molars|A stained tooth chorus compresses its gum base and opens several mouths together.|
|8|Wound-up Moon|A cratered, cracked face over an irregular mainspring. The jaw loads, releases and leads the lunge.|
|9|Inverted Bouquet|An upside-down flower mass surrounds a grub mouth. Petals pull back; one clean bloom remains among diseased tissue.|
|10|Processional Bath|A scum-filled claw-foot vessel with a furious face. Its contents rise for release and pitch forward in pursuit.|

All 13 named drawings are distinct in every boss option: pulse1/pulse2/hurt,
charge1/charge2, release1/release2, spawn1/spawn2, lunge1/lunge2 and
dying1/dying2. Changes affect connected material masses, cavities and folds,
not a translated idle plus independent dust. Dying widens negative space and
collapses the lower mass; it does not imply active contact damage.

The existing 40 HP phases remain: above 26 radial 8-spore bursts;13–26 alternating
three-shot fans/two spawned chasers;12 or less lunging followed by a fan.
The original state clock chooses these presentation frames. No shot schedule,
projectile damage, spawn count, hurt immunity or reward is invented by the art.
All living states remain damageable; mouths/light splits are identification,
not exclusive weak points. Generic normal-enemy death still uses the shared
puff effect; the boss has its existing timed death sequence.

## API and integration

`frame(family,variant,name)` returns a native indexed P image for variants 1–10.
`CONCEPTS`, `NOTES`, `SIZES`, `PALETTES`, `BASE_FRAMES` and `EXTRA_FRAMES` expose
metadata. Parent integration appends new names after old frame IDs, preserves
sheet identifiers, and selects the bonus poses from existing states only.
The parent owns C wiring and actual mGBA evidence; source boards alone do not
establish that a pose ran or that the combat performance is correct.

Appended knight names are windup_n/e/s, strike_n/e/s, recover_n/e/s and
hurt_n/e/s. Appended boss names are charge1/2,release1/2,spawn1/2,lunge1/2,
dying1/2. Their current export ordering follows `EXTRA_FRAMES` literally.

## Source review and honest limits

Authoring exports 390 named native frames across the ten profiles:
240 bodies, 20 weapons and 130 boss frames. Direct checks cover mode P, exact
canvases, 0–15 indices, nonempty frames, every current/appended name and exact
body/weapon hand coverage. Every boss has13 distinct poses; original knight
atk/strike aliases are deliberate. Silhouette/context boards, all 20 full-pose
sheets and two animated source comparison GIFs are under the work root's
`heavy/` folder. They explicitly say SOURCE/not emulator output and use only
integer nearest-neighbor review enlargements. The four context colors are
simple sewer/healthy/blight/cave material swatches, not room screenshots.

Visually inspected the two ten-way boards, native context board and selected
complete pose sheets. Frames keep connected silhouettes with one principal
material hook. Remaining comparison tradeoffs: the narrow 16px walker canvas
forces simplified hands and face details; stone/bronze variants share a
restrained palette; tiny directional changes are intentionally economical;
some 32px boss glyphs are less immediately animal-like than others. These are
options for user feedback, not a claim that every concept is equally strong.
Actual terrain contrast, weapon/body OAM depth, phase timing, hurt replacement
and streamed allocation remain the parent's runtime review responsibilities.

## Production selection follow-up

Moth Confessor6 and its paired weapon are adopted. None of the ten boss forms is adopted: the boss remains a purplish heart broken down its middle, authored in enemy_heart.py and documented in BROKEN_HEART.md. Profile11 selects this combination.
