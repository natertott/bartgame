# Independent review of the final forest concepts

Reviewed frozen game/art source `e5e3fcb21fe1bcc50c965943164146a2dc1e3c46`, profiles6–10 (display options1–5). The files examined here are real 240×160 mGBA framebuffer captures from `runtime/v6` through `runtime/v10`. The optional inspection boards contain only crops or nearest-neighbour enlargements of those captures. Source assemblies were reviewed separately in `secondary-source-critique.md`.

There is no remaining blocking art or interaction defect in the reviewed evidence. These are five exploratory options, not a user-selected final art direction. Their remaining visual compromises are useful selection feedback.

## Actual appearance

| Display / profile | Observed strength | Remaining compromise |
| --- | --- | --- |
| 1 / 6 — Black Sap Oak | Dark raised trunks and thin angular violet sap lines separate clearly from the quiet gray-olive ground. The snail hermit's pale face and shell are visible beside Bloom; the compact friendly moth reads through its face/book. | Long blighted walls expose a regular repeated lightning/branch rhythm. Healthy crown shapes are deliberately close to the other options. |
| 2 / 7 — Violet Strangler | Curling purple growth has the most obvious vine identity. The morel hermit and frog gardener give distinct, readable faces at world scale. | The repeated curls become a chain pattern along a long wall. The narrow shrine's rectangular head is more sign-like than the other shrines. |
| 3 / 8 — Witchfire Weep | Slender violet streaks give the blight a quieter, hanging quality. The bell sister and carrot gardener have strong compact identities against the green floor. | A broad infected wall still shows repeated columns. The wooden switch is the quietest switch; its light studs help, but it has less immediate value contrast than the ivory/stone alternatives. |
| 4 / 9 — Amethyst Canker | Luminous attached nodules are easy to locate on the black bark. Owl, willow and salamander have distinguishable light faces. The shrine has a substantial raised stone form. | The nodules can resemble gems at first glance. They remain attached to wall masses, so they do not look like loose pickups in these captures. Pale small ground growths also attract more attention than in the other options. |
| 5 / 10 — Royal Bruise | Broad violet arcs and isolated bright nodes read at screen scale. Teapot, ragdoll and mole give a particularly odd, approachable set of silhouettes. | Repeated arcs give long walls a scalloped rhythm. The teapot's spout is clearer in its portrait than its tiny world drawing; world dialogue context still helps identify it. |

Across all five, Bloom's red flower and warm lamps are strong focal points. Paths, floor and loose debris stay substantially quieter than the luminous corruption. Purple light belongs primarily to attached growth rather than the entire walkable surface, so deep rooms remain navigable. This also means that a deep room's floor can be fairly subdued next to its spectacular wall; the result is a contrast choice rather than uniformly saturated blight.

## Interactions and landmarks

Actual `forest-locked-door` captures show one tall brass lock with a single large dark keyhole, legible beside Bloom. The native OAM/stream proof records one before unlocking and none after it. It is a much clearer instruction than several tiny repeated lock ornaments.

Both wooden chest forms have a dark base, warm timber body and clear latch. All five B forms were inspected in their actual room context. The rounded, banded, upright plank and angled constructions remain recognizably chests rather than oversized inventory icons. The stone and ivory floor switches read as broad plates; option3's wood plate remains the lower-contrast alternative noted above. Bomb stones share the same large split-rock language across options, which helps preserve the tool cue. Ivory webs remain visible against black/violet walls. Warm lamps give webs and thresholds local framing without recolouring their whole surroundings.

Shrines and relics occupy tall billboards above low physical pads rather than merely decorating a floor tile. The shrines now read as raised objects; option2's sign-like head remains a stylistic tradeoff. Entrances are large dark openings framed by a material mass and a small warm threshold. Their black openings can look austere in stills, but the ordinary movement/transition captures show an accessible entrance rather than a decorative recess. Hollow entrances share a square, trunk-like construction; five new options do not imply five entirely unrelated door systems.

The paired logs read as one horizontal trunk, with a visible cut end and body. Their two solid cells agree with their apparent span. This is real collision geometry, not a wide image pasted over a one-cell obstacle. Ledge banks carry a darker vertical face and pale upper lip, helping distinguish a height change from a path edge.

## Water, edges and depth

Actual isolated-water diagnostics include healthy grass, sick turf and dirt substrates. The one-cell pools have rounded rims without an opaque green or black rectangle around them; the proper floor remains visible outside the pool. Wider connected water still has a tile-based stair-step contour. Flowing crests remain attached to water and the bridge joins usable banks. Water is still a real hazard: the disclosed diagnostic action walks into it, drowns and returns to a safe position. This check does not claim that every diagnostic arrangement was generated naturally.

The six explicitly labelled adjacency scenes per style exercise isolated sizes, narrow strips and inner corners. The separate457-case hardware corpus checks all canopy quadrants, both canopy families, water configurations and empty/nonempty fringes. The alpha contour changes presentation; solid canopy is still solid even where an outer corner is visually transparent. Cropping its outline is not a promise that every visible sliver is walkable.

For actual depth motion I inspected the before/under/emerged frames and intermediate native frame sequences, including the sick-fringe wall impact and root-arch passage. The healthy canopy gives partial upper-body occlusion with visible feet. Deep under the sick fringe, much of the head/body is intentionally covered; the feet remain the main continuity cue. That is more convincing foreground depth but less immediate body readability than an entirely visible sprite.

The brief airborne NORMAL recoil uses the documented low-fringe priority exception. In the reviewed sequence the body comes in front of the low fringe at tick29 and stays coherent with held parts. Its coarse priority change is visible as a small pop; it is not smooth per-pixel depth sorting. The ground shadow remains below. Bloom's sprite pixels, jump/roll physics, item timing and sword mechanics are protected. The true root arch retains ordinary roof occlusion, and Bloom can enter below its crown and emerge above it. This is a walkable underpass, not a claim that the top of the root is a traversable bridge deck.

## Motion, folk and protected art

The four actual deep-blight palette phases change only authored BG glow inks. They are a restrained breathing pulse, not a full-screen grade; Bloom, enemies, wood, UI and glitter retain their native palettes. All attached veins sharing that bank pulse together. This can make a large wall feel rhythmically synchronized rather than like many independent organisms. Water/foam and supported bitmap motion remain separate from that colour pulse.

All fifteen selected world NPC forms and their dialogue contexts were inspected across the five styles. Pale faces, books/tools and stationary interaction presentation distinguish them from scenery. The friendly moth and armed Moth Confessor share a family resemblance: the friendly round face/book/compact wings differ from the enemy's long-legged armed stance, but this remains a visual vocabulary overlap. Forest folk are static poses in this pass, not new walking or talking animation sets. Gardener scenes are deliberately dim; their pale faces and tools remain readable without making the surrounding thicket uniformly bright.

This review does not claim a new full enemy-animation study. The final native audit verifies the adopted enemy sheets and all protected Bloom, sword, items, UI, font, glitter and Drain art unchanged. The fresh production0 control separately records83 cases,10 movies and482 passing checks on the byte-identical production ROM.

## Evidence and limits

`finalaudit.json` passes139,478 independent checks. It binds the fresh five-style actual reports to the final ROMs/source and checks their native hardware/media evidence. New-style runtime coverage is485 cases,75 movies and2,285 exhaustive renderer contracts; adding the production control gives568 cases and85 movies. Each new profile records a successful ordinary-input critical path,17/17 steps. The disclosed navigation/setup helpers are not a claim that an unattended player solved every random seed.

The one final frozen host corpus passes20,000 seeds:500,000 generated rooms and60,000 world graphs across three pacing settings. It checks256,812 complete log pairs,11,884 underpasses,263,746 item pockets and3,182,406 required approaches. This exposed and led to repairs for orphan log halves and rare inherited blocked approaches/missing censers. Superseded failing runs are retained locally with explicit labels; they are not relabelled as final passes. Host generation is real C logic with frozen native physical metadata, not emulator video and not a universal-solvability proof.

Recorded transition states and ticks match across all97 final same-input cases in profiles6–10; `timing-observations.json` records that observation. It does not benchmark CPU time or guarantee identical loading behaviour on every path. Old0/1/5 ROMs remain wholly byte-identical. New log placement, foreground spans and guarded approach repairs intentionally change some new-profile geometry relative to the older concepts; cross-generation views should be labelled historical context rather than exact-position before/after comparisons.
