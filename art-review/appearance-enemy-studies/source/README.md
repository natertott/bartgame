# Sixty native enemy source-art proposals

These are **SOURCE pose studies**, not emulator footage or AI simulations. Each of six current enemy mechanics has ten alternatives. Working concept labels are secondary to the existing mechanic; no body form or enemy name is adopted here.

Every drawing starts at its actual legal GBA canvas size, with indices 0–15 and sixteen RGB555 inks including transparent zero. Native indexed and RGBA PNGs are retained. Enlargements are integer 3× nearest-neighbor; labels stay outside game art.

**Final comparison palette:** the ground pursuer, airborne hunter and compress-and-hop bodies use the approved actor-only `enemy_studies_palette.colors()` bank, compiled as the existing `items` / OBJ10 alias for positive enemy profiles. That bank was chosen after 120 source comparisons on actual background crops. The original shared bugs/foliage bank stays intact for the cloak and carried bushes; the other three enemy material banks and companion palettes remain unchanged. Earlier painter-specific foliage boards are historical authoring diagnostics, not the final colors shown here. The source manifest records the exact palette API hash and every frame’s input bank.

[Forty ordinary concepts](ordinary-summary-source.png) · [Twenty heavy/boss concepts](heavy-summary-source.png) · [Companion weapons/projectile](companions-source.png) · [Native coverage and hashes](source-manifest.json)

## Complete source pose cycles

Every animated board shows all authored body frames, including appended anticipation, melee recovery and boss phases. Each pose has a fixed 150 ms review hold. This deliberately does **not** claim to reproduce AI state duration, actual attack damage windows, real movement, hurt blinking or physics. The separate mGBA gallery provides runtime evidence.

| Mechanic / internal sheet ID | Native canvas | Body frames per option | Ten alternatives | Complete pose cycle | Value/silhouette check |
| --- | --- | ---: | --- | --- | --- |
| Ground pursuer / `beetle` | 16×16 | 6 | [PNG](beetle-ten-source.png) | [GIF](beetle-all-poses-source.gif) | [PNG](beetle-diagnostic-source.png) |
| Airborne hunter / `bat` | 16×16 | 3 | [PNG](bat-ten-source.png) | [GIF](bat-all-poses-source.gif) | [PNG](bat-diagnostic-source.png) |
| Directional shooter / `spitter` | 16×16 | 12 | [PNG](spitter-ten-source.png) | [GIF](spitter-all-poses-source.gif) | [PNG](spitter-diagnostic-source.png) |
| Compress-and-hop / `slime` | 16×16 | 3 | [PNG](slime-ten-source.png) | [GIF](slime-all-poses-source.gif) | [PNG](slime-diagnostic-source.png) |
| Heavy melee striker / `knight` | 16×32 | 24 | [PNG](knight-ten-source.png) | [GIF](knight-all-poses-source.gif) | [PNG](knight-diagnostic-source.png) |
| Three-phase boss / `boss` | 32×64 | 13 | [PNG](boss-ten-source.png) | [GIF](boss-all-poses-source.gif) | [PNG](boss-diagnostic-source.png) |

The boss is drawn on its **actual 32×64 current canvas**, not the obsolete 32×32 dimensions recorded with its historical sheet ID. Shared damage/death effects are existing engine art; body suites do not invent ordinary death poses or weaknesses. The knight retains intentional old `atk` / new `strike` pose aliases.

## Full per-option frame atlases

Atlases include native and 3× body poses, plus separately labelled weapon/seed companions where applicable. Each native folder also contains indexed PNGs and exact RGBA PNGs for every pose.

| Mechanic | Full authored suites |
| --- | --- |
| Ground pursuer | [v01](atlases/beetle-v01-all-frames-source.png) · [v02](atlases/beetle-v02-all-frames-source.png) · [v03](atlases/beetle-v03-all-frames-source.png) · [v04](atlases/beetle-v04-all-frames-source.png) · [v05](atlases/beetle-v05-all-frames-source.png) · [v06](atlases/beetle-v06-all-frames-source.png) · [v07](atlases/beetle-v07-all-frames-source.png) · [v08](atlases/beetle-v08-all-frames-source.png) · [v09](atlases/beetle-v09-all-frames-source.png) · [v10](atlases/beetle-v10-all-frames-source.png) |
| Airborne hunter | [v01](atlases/bat-v01-all-frames-source.png) · [v02](atlases/bat-v02-all-frames-source.png) · [v03](atlases/bat-v03-all-frames-source.png) · [v04](atlases/bat-v04-all-frames-source.png) · [v05](atlases/bat-v05-all-frames-source.png) · [v06](atlases/bat-v06-all-frames-source.png) · [v07](atlases/bat-v07-all-frames-source.png) · [v08](atlases/bat-v08-all-frames-source.png) · [v09](atlases/bat-v09-all-frames-source.png) · [v10](atlases/bat-v10-all-frames-source.png) |
| Directional shooter | [v01](atlases/spitter-v01-all-frames-source.png) · [v02](atlases/spitter-v02-all-frames-source.png) · [v03](atlases/spitter-v03-all-frames-source.png) · [v04](atlases/spitter-v04-all-frames-source.png) · [v05](atlases/spitter-v05-all-frames-source.png) · [v06](atlases/spitter-v06-all-frames-source.png) · [v07](atlases/spitter-v07-all-frames-source.png) · [v08](atlases/spitter-v08-all-frames-source.png) · [v09](atlases/spitter-v09-all-frames-source.png) · [v10](atlases/spitter-v10-all-frames-source.png) |
| Compress-and-hop | [v01](atlases/slime-v01-all-frames-source.png) · [v02](atlases/slime-v02-all-frames-source.png) · [v03](atlases/slime-v03-all-frames-source.png) · [v04](atlases/slime-v04-all-frames-source.png) · [v05](atlases/slime-v05-all-frames-source.png) · [v06](atlases/slime-v06-all-frames-source.png) · [v07](atlases/slime-v07-all-frames-source.png) · [v08](atlases/slime-v08-all-frames-source.png) · [v09](atlases/slime-v09-all-frames-source.png) · [v10](atlases/slime-v10-all-frames-source.png) |
| Heavy melee striker | [v01](atlases/knight-v01-all-frames-source.png) · [v02](atlases/knight-v02-all-frames-source.png) · [v03](atlases/knight-v03-all-frames-source.png) · [v04](atlases/knight-v04-all-frames-source.png) · [v05](atlases/knight-v05-all-frames-source.png) · [v06](atlases/knight-v06-all-frames-source.png) · [v07](atlases/knight-v07-all-frames-source.png) · [v08](atlases/knight-v08-all-frames-source.png) · [v09](atlases/knight-v09-all-frames-source.png) · [v10](atlases/knight-v10-all-frames-source.png) |
| Three-phase boss | [v01](atlases/boss-v01-all-frames-source.png) · [v02](atlases/boss-v02-all-frames-source.png) · [v03](atlases/boss-v03-all-frames-source.png) · [v04](atlases/boss-v04-all-frames-source.png) · [v05](atlases/boss-v05-all-frames-source.png) · [v06](atlases/boss-v06-all-frames-source.png) · [v07](atlases/boss-v07-all-frames-source.png) · [v08](atlases/boss-v08-all-frames-source.png) · [v09](atlases/boss-v09-all-frames-source.png) · [v10](atlases/boss-v10-all-frames-source.png) |

## Form choices by mechanic

These notes explain the intended visual analogy; they are not claims about new mechanics or exclusive weak points.

### Ground pursuer / `beetle`

| Option | Working form | Animation/recognition intent |
| --- | --- | --- |
| v01 | Tarnished Teacup | A hollow cup on greasy feet; the planted gait accelerates with the existing chase clock. The handle and black rim stay readable. |
| v02 | Briar Turnip | A pale root with a thorn-leaf crown; alternating forked roots expose its approach direction. No armored crown is implied. |
| v03 | Runaway Boot | An abandoned boot walks itself toward Bloom; the sole flexes while its open ankle and toe keep a clear silhouette. |
| v04 | Crab Buckle | A living brass buckle shuffles on crab legs; asymmetric pincers open the silhouette without implying a separate ranged attack. |
| v05 | Louse Loaf | A crusty loaf with a blunt biting end; underside feet alternate under a broad highlighted crust, keeping the moving body connected. |
| v06 | Acorn Urchin | An acorn carried by thorn roots; the crown and tapered nut stay distinct while two roots plant in alternating positions. |
| v07 | Snapping Purse | A purse with a toothed seam and grasping legs; the brass latch is attached, rather than a floating loot sparkle. |
| v08 | Crawling Inkpot | A squat leaking inkpot crawls on bent nibs; the dark cavity, wide shoulder and glass reflection separate it from loose scenery. |
| v09 | Coin Toad | A muddy toad with a broad plated brow; its left/right feet paddle alternately. The bright brow is decorative, not actual armor. |
| v10 | Soap Slug | A dirty soap bar dragged by a slug; two eye stalks and a continuous dark underside distinguish the hunter from a dropped object. |

### Airborne hunter / `bat`

| Option | Working form | Animation/recognition intent |
| --- | --- | --- |
| v01 | Bell Wasp | A tiny living bell with insect wings; folded rest versus full wing extension communicates when the drifting pursuit is active. |
| v02 | Tattered Glove | A discarded glove flaps its fingers; fingers close around the palm during rest, never becoming separate flying particles. |
| v03 | Flying Teeth | A winged pair of teeth; a clamped resting jaw opens in flight. Its bite is contact damage, with no invented attack interval. |
| v04 | Mouldy Bowtie | A rotted bowtie with an eye-bearing knot; cloth lobes lift and fold as wings while the knot remains the collision-bearing body. |
| v05 | Lantern Gnat | A square lantern carried by two ragged wings; the handle and glowing central cavity remain attached through both flight poses. |
| v06 | Fishbone Kite | A small fish skeleton swims through air; rib-fins open and draw inward around a continuous spine, with a folded resting tail. |
| v07 | Ribbon Ray | A pale ribbon-like ray; broad flexible membranes alternate above/below the face and the trailing tail follows the same connected body. |
| v08 | Mushroom Parasol | A parasol fungus pulses its cap; the narrow closed rest silhouette becomes a broad canopy in flight. No new umbrella shielding is implied. |
| v09 | Quill Moth | A moth made from dirty quills; pointed overlapping wing vanes open and fold while the small eye-bearing thorax stays stable. |
| v10 | Wheezing Bagpipe | A wheezing bagpipe flaps its bellows; three uneven pipes identify the creature even in its compressed resting pose. |

### Directional shooter / `spitter`

| Option | Working form | Animation/recognition intent |
| --- | --- | --- |
| v01 | Waddling kettle | Loop handle and broad belly identify the kettle; cheeks swell, the directional spout opens, then the body recoils. |
| v02 | Bellows hen | Plump hen with tiny pumping legs; the bill contracts before a seed cough and projects in the real firing direction. |
| v03 | Hollow porcelain mask | A pale, empty ceramic face on short rooted feet; the round mouth inflates and opens, with a visible top vent when north-facing. |
| v04 | Barrel organ grub | A squat wooden organ on grub feet; the bellows rise and brass outlet opens after the inhalation. |
| v05 | Trumpet bellflower | An upright folded flower with a trumpet mouth; petals draw inward for charge and flare around the directional opening. |
| v06 | Inside-out umbrella | A living inverted umbrella walks on its handle and ribs; a central nozzle flexes as the canopy pulls in and snaps outward. |
| v07 | Coughing pipe elbow | A broken pipe section with two dripping feet; the elbow points at the target and its seam bulges before discharge. |
| v08 | Conch-foot pilgrim | A curled shell supported by a fleshy sole; the short feeding tube contracts then flares in the actual firing direction. |
| v09 | Trumpet tick | A squat trumpet carried by four jointed feet; the round brass bell is the clear dangerous end, with no shield implication. |
| v10 | Blinking box camera | A box camera on two wooden legs; the lens draws in for charge and extends on release, never flashing like treasure. |

### Compress-and-hop / `slime`

| Option | Working form | Animation/recognition intent |
| --- | --- | --- |
| v01 | Concertina mushroom | The cap sits over accordion gills; the body compresses wide, extends tall on hop and folds again on landing. |
| v02 | Tallow pudding | A greasy wax pudding with a bent wick and drooping eye sockets; it pools, stretches and settles without implying fire damage. |
| v03 | Spring walnut | A split walnut squeezes its root spring flat then extends it on hop; the shell seam is expressive, not an armored phase. |
| v04 | Loose molar | A loose molar waddles on two wet roots; the crown flattens into its socket and the roots trail during a leap. |
| v05 | Leech purse | A mouthy purse with leech feet; its broad clasp and angry face avoid looking like a passive coin pickup. |
| v06 | Puddle snail | A snail in a living puddle; the shell pitches and the eye stalks fold before the whole animal hops. |
| v07 | Unruly boot | An abandoned boot with two eyes in its cuff; its sole folds under the shaft then snaps long as it jumps. |
| v08 | Haunted handkerchief | A knotted handkerchief with a face in the fold; its corners pull inward, billow on hop and flatten on landing. |
| v09 | Pear bladder | A pear-shaped swollen bladder with a pinched stem; the rubbery lower body spreads during charge and pulls tall in flight. |
| v10 | Scum bucket | A dented bucket animated by scum; its handle folds, liquid compresses below the rim and its sludge feet extend during the hop. |

### Heavy melee striker / `knight`

| Option | Working form | Animation/recognition intent |
| --- | --- | --- |
| v01 | Bell Washer | A tarnished walking bell shifts its entire skirt before the clapper-blade cut. The exposed eye is identity, not an exclusive weak spot. |
| v02 | Walking Tureen | A cracked soup tureen plants its handles and tiny feet, draws back its ladle, then pours its weight into the strike. |
| v03 | Censer Stilt | A long-legged censer draws its chain-like arms close during preparation; the broad hot bowl pitches forward with its blade. |
| v04 | Molar Mason | A stained molar roots itself on two bent root-legs. Its pale crown tilts back, then the whole tooth drives the chisel forward. |
| v05 | Bad Boot | A sour-faced old boot winds its ankle, stamps through the cut and settles onto its heavy sole. The shoehorn is the weapon. |
| v06 | Moth Confessor | A folded moth leans its head and wing-cape together. Unequal wing panels make its front, back and side readable. |
| v07 | Snail Porter | A carrying snail braces its soft lower body beneath a heavy coil. Its head recoils into the shell before swinging a reed blade. |
| v08 | Broken Marionette | A loose wooden puppet bends at shoulder, hip and knee. Its sword and wrist keep one grip while its wooden body counter-rotates. |
| v09 | Oyster Bailiff | A walking oyster opens a narrow dark mouth, shifts both shell lobes and thrusts a small shucking blade. Its shell is not a shield mechanic. |
| v10 | Chandelier Drudge | A soot-stained chandelier bends its central stem and candle crown into the cut. Flame highlights remain attached to candle tips. |

### Three-phase boss / `boss`

| Option | Working form | Animation/recognition intent |
| --- | --- | --- |
| v01 | Split Coronation Bell | A split gilded bell swells around its filthy sounding cavity. Its seam spreads before shots; its lower lip thrusts into a lunge. |
| v02 | Glutton Chalice | A huge living chalice has a dark toothy bowl and sagging stem. The bowl fills during charge, opens for the volley and tips into pursuit. |
| v03 | Silk Stomach | A suspended silk stomach tightens its stitches before bursting from a central vent. Loose folds sag during recovery and split on death. |
| v04 | Crowned Leech Coil | A ring of wet leech flesh cinches around a dark maw. The front head pulls back for a volley and stretches into a lunge. |
| v05 | Funeral Peacock | A funereal bird opens an uneven fan before firing. Its hunched breast and drooping beak move together; the fan loses its spread during dying. |
| v06 | Slime Banquet | A serving platter carries a heaped wet body with three mouths. The pile rises before release, slumps after and tears apart during dying. |
| v07 | Choir of Molars | A choir of giant stained teeth compresses its gum base before a shot. Dark mouths open together; no individual tooth is an exclusive weak point. |
| v08 | Wound-up Moon | A cratered face is pulled by a broken mainspring. Its jaw compresses for charge, springs open to release and leads the lunge. |
| v09 | Inverted Bouquet | An inverted flower bunch hangs from a fleshy stalk. Petals fold back to reveal its mouth; one immaculate bloom remains among sick tissue. |
| v10 | Processional Bath | An ambulant bath carries a dripping, furious face in its scum. Its body rises over claw feet for a volley and pitches down during the lunge. |

## Validation scope

All 640 authored body/companion frame instances are validated for legal geometry, index range, existing palette roles and exact native PNG decoding. All six GIFs round-trip to their source RGB boards with exact union palettes; no GIF is color-quantized. Source code hashes, per-frame index/RGBA hashes, PNG hashes, original/appended frame lists and full coverage are in the manifest.

Native silhouette/value diagnostics use quiet swatches, not fabricated game screenshots. These checks establish encoding and source completeness, **not** human recognition, balanced mechanics or a winning art choice. Actual terrain/combat/input evidence and final adoption status belong to the parent review.
