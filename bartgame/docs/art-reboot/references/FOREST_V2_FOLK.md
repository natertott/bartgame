# Forest folk v2: fifteen different forms

**Status:** five optional character sets for the second forest study. No set
is adopted by producing this comparison. These are new creature/object forms,
not five clothing colours applied to the earlier hooded humans.

**Brief and sources:** the user asks for the successful Drain sprite principles
and a much broader, stranger design range. The shared art bible, the already
read [reference application matrix](../REFERENCE_APPLICATION.md) and
[Drain character decisions](DRAIN_V2_CHARACTERS.md) supply the method: native
silhouettes before detail, one memorable hook, deliberate negative space,
upper-left material planes, limited inks and matching separately drawn busts.
G01–G07, G09, G12–G15 and G18 are the relevant existing applications. This pass
does not claim a new external source or fresh access to missing illustrations.

## The fifteen original silhouettes

Variant numbers below are local1–5; root integration maps them to optional
`BART_FOREST=6..10`. Role names, conversations, quest rewards and behavior stay
unchanged. A creature filling the Hermit role is still the same quest-giver,
not a new enemy or an additional gameplay species.

| Local set | Hermit role | Nun role | Gardener role |
| --- | --- | --- | --- |
| 1 | **Snail Sage:** upright eye stalks, warm spiral shell, pale mucus beard and open book. | **Weeping Moth Sister:** soft folded wings, round warm face, prayer hands and a connected tear. | **Compost Beetle:** broad brown wing cases, leafy antennae, blindfold and a tin watering can. |
| 2 | **Morel Abbot:** tall honeycombed fungus cap over a short pale stalk/beard, reading quietly. | **Bellflower Veil:** drooping pale petal lobes and living calyx framing a mournful face; leaf hands and root feet. | **Frog Botanist:** broad jaw, separate eye lobes behind the blindfold, work apron and a seedling. |
| 3 | **Stump Librarian:** broken side branches, sawn top, hollow face and root collar; the book stays subordinate. | **Mourning Bell:** a tarnished bronze bell body, black face recess, tear and small folded hands. | **Carrot Sexton:** orange tapering root, sprouting leaves, dirt, blindfold and a young potted plant. |
| 4 | **Owl Reader:** pointed ear tufts, a pale facial disc, tiny beak, folded wings and book. | **Weeping Willow Dryad:** a branching woody crown with separate hanging boughs, pale face, twig hands and rooted feet. | **Compost Salamander:** long blunt snout, broad pale jaw, curled tail, blindfold, apron and watering can. |
| 5 | **Chipped Teapot Hermit:** pale ceramic body, open handle, spout and lid knob; a book and gentle face make it a person. | **Tearstained Rag Doll:** floppy black cloth corners, linen face, button eyes, one mended cheek and a book. | **Mole Planter:** round ears, pale muzzle, broad gardening mitts, blindfold and a seedling held between the palms. |

The shared book identifies the contemplative Hermit role without a combat
weapon. Mournful expression, prayer and a tear link the five Nun forms even
when the body is an insect, flower or object. Blindfold and cultivation work
link the five Gardeners. No bright central patch promises an enemy weak point,
and no actor carries an aggressive windup or an invented attack animation.

The grotesque/glorious contrast lives in materials: beautiful wet snail skin
and an old shell, clean book pages against crumbling bark, tarnished brass,
chipped ceramic, patched cloth, compost and young plants. Highlights attach
to those materials. There are no detached sparkle crosses or decorative
particles painted around these static bodies. The existing ambient glitter
system remains unchanged.

## Native construction and fixed contracts

Implementation owner is `art/forest_concepts_v2_folk.py`. It imports only the
existing shared palette/native inspection helpers and Pillow. It does not
import the v1 people as a fallback, scale a larger image, mutate a palette or
depend on the global forest selection during drawing.

- `supports_frame(sheet,name)` accepts NPC Hermit/Nun/Gardener plus
  Brother Mark/Sister Mary Grace aliases, and only those three face names.
- `frame('npc',name,v)` returns a native indexed32×32 image with physical
  OBJ alias`folk`; `frame('face',name,v)` returns64×64 with alias`portrait`.
- `portrait(name,v)` draws an independent native48×48 bust. The face adapter
  pads it at `(0,0)` with transparent right/bottom margins.
- `portrait_palette(name,v)` returns the same sixteen RGB555 colours used by
  the world folk bank, so ceramic, silk, bark, fur and face colours agree.

Every world concept is one connected drawing with a grounded bottom at row31.
Painted extents are17–20 pixels wide and22–26 high, within the requested
14–20×20–26 design envelope. Tall caps/leaves and broad wings deliberately
change proportion. The native hardware canvas and streamed16-tile frame stay
unchanged. Their inherited physical collision and conversation distance are
unchanged; painted shape is not silently converted into a new hitbox.

NPC IDs2–6 and face IDs3–5 remain fixed. Brother Mark is an exact Hermit alias
and Sister Mary Grace an exact Nun alias within each set. This gives25 body
frame instances and15 portraits without inventing extra people or appended
poses. The existing Stranger still reuses the Hermit presentation. Sage,
Merchant, Bloom, the selected bestiary, Drain keepers and their portraits,
equipment, UI and glitter are unsupported/protected by this module.

All world forms use the unchanged physical folk bank5. Portrait slot6 receives
its normal per-speaker bank, matching the existing hero/folk vocabulary here.
No new OBJ palette or resident allocation is required. Material planes use a
few of those inks at a time: broad matte cloth/fur, narrow ceramic/metal glints,
warm wood faces and cool shadows. Invariant shared colours help these strange
subjects belong to the same game as Bloom and the Drain.

## Source critique and refinements

The first native overview made the design range visible before detailed
finishing: snail stalks/shell, fungus cap, stump branches, owl disc, teapot
spout, wings, flower bell, metal bell, roots, floppy cloth, antennae, frog jaw,
carrot leaves, tail and mole mitts supply distinct silhouettes. All15 binary
body masks are different; that is a construction fact, not an aesthetic score.

One first draft still treated the Willow as an unbroken hood-shaped arch.
It was redrawn as a forked woody crown with separated hanging leaf masses,
visible gaps and rooted trunk. Independent source review also found the
Salamander's head/tool more prominent than its animal identity. Its world and
portrait now share a longer angular snout, larger pale jaw and a clearer
curled tail, retaining the blindfold and watering can.

The source review found the friendly Moth Sister's pale folded-wing family
could still overlap the selected Moth Confessor at tiny scale. A round warm
unarmored face, soft broad wings, folded hands and absence of a weapon separate
the intentions; actual nearby-enemy context remains an explicit comparison
tradeoff. This is not labelled as proven friendliness by a hash check. Willow's
central face is still humanoid, but its branches, boughs and roots carry the
body's tree identity. Tiny world expressions remain simpler than their busts.

## Evidence and remaining runtime review

Source evidence is in `/workspace/setup/forest-concepts-v2/folk/`:

- `overview.png`, `silhouette.png`, `grayscale.png` and integer-nearest2×
  companions show all15 bodies and matching busts. Each body appears on green,
  brown and dark material fields. These are labelled **static source concepts**.
- Thirty transparent native PNGs supply the15 live bodies and15 native busts.
  Aliases are checked exactly rather than adding redundant pictures.
- `source-review.json` records names, canvases, extents, image/silhouette
  hashes and palettes. `native-validation.json` records134 passing native/API
  checks: legal4bpp indices, RGB555 colours, exact padding, planted bounds,
  connected bodies, exact aliases,15 distinct silhouettes/busts and protected
  name exclusion.

The overview was inspected at1× and2×, including grayscale and filled masks.
This is one static presentation per actual NPC descriptor. No idle, breathing,
tool use or gesture animation is claimed or illustrated as implemented. NPC
motion would need an explicit engine/frame-clock integration; none is added
by this source-only art module.

Root integration must freeze the new study ROMs and examine actual quest-giver
placement, A-button conversations, portrait identity/palette loading, canopy
depth and enemy proximity on healthy/mixed/deep fields. In particular, inspect
the broad20-pixel bodies and26-pixel caps/boughs against the inherited depth
priority box, the Moth Sister near the armed Confessor, and pale material
separation against bright grass. Source boards are not emulator captures and
cannot establish those runtime results.

Native source after this review:
`f90c9b814cc992d865306d3b75e6458fe7226fe920e5c5add2f3ffa42e2e18ee`.
