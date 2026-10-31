# Five forest-folk concept families

**Status:** exploratory source artwork for the five forest environments. No
family is adopted automatically. This pass changes neither NPC behavior nor
the selected Bloom, enemies, Drain keepers, interface geometry or global inks.

**Basis:** the user's request for complete forest-first alternatives and the
shared native-art rules in [the art bible](../ART_BIBLE.md), including the
already-adopted G01–G18 reference applications: silhouette and identifying
masses first, useful negative space, few directional value planes and quiet
subordinate detail. No new web source, inaccessible figure or additional
research is claimed. [The inventory](FOREST_ASSET_INVENTORY.md) records the
baseline identifiers and cross-area sharing traps.

## Identity before decoration

The Hermit Knight has a silver beard, a hood framing the face, broad shoulders,
folded hands and one worn shoulder plate. The Weeping Nun retains her black
veil, pale wimple, gray hem, downturned mouth and one connected tear. The Blind
Gardener has a broad blindfold, a work apron, brown beard and an unmistakably
grounded cultivation staff. Forked and hooked tool heads are matte material;
they do not resemble a detached pickup star or a flaming wizard's staff.

These three silhouette/identity groups remain consistent between the world
body and its separately drawn portrait. Fifteen live body drawings and
fifteen busts are authored directly at native size. Retained Sister Mary Grace
and Brother Mark descriptors intentionally alias Nun and Hermit within each
family, adding ten source body instances without inventing new characters.

| Environment | Local treatment | Deliberate limit |
| --- | --- | --- |
| Fern Oak | Rounded fern-green hoods, broad practical cloaks, a forked gray tool, silver beard/plate | Existing bank green is close to grass; pale face, beard, shoulder and tool give local separation instead of outlining every fold in white. |
| Silver Willow | Drooping hood silhouette, longer beard/cowl, pale silver-gray cloth, hooked cultivation staff | Pale mass belongs to a person; it is not a luminous halo or a new loot/glitter cue. |
| Copper Beech | Angular rust/russet hood and workwear, brown outer wrap, warm apron and hook | The Nun's central veil remains black. Warm cloth should read as dyed/worn material, rather than polished gold. |
| Velvet Cedar | Broad asymmetrical dark cowl, spare spruce cloak, compact beard and fork | This is the darkest study. The face/wimple, beard and gray hem remain deliberate high-value anchors; actual blighted-canopy occlusion still needs review. |
| Pale Orchard | Light hood/wrap and apron over warm shadow cloth, tapered beard, orchard crook | White/gray cloth is broken by existing dark planes. No broad glow or separate decorative sparkle is painted into the actor. |

## Native/API contract

Owner: `art/forest_concepts_folk.py` only. It imports the shared palette
vocabulary for immutable colours and native PNG inspection, never a global
forest profile or a screenshot/old pixel pack. Its optional study selector
is an explicit argument1–5. Root integration owns build selection and packing.

- `supports_frame(sheet,name)` accepts `npc` Hermit/Nun/Gardener and their two
  retained aliases, plus `face` Hermit/Nun/Gardener. All other names are false.
- `frame('npc',name,v)` returns an indexed32×32 image and physical alias`folk`.
- `frame('face',name,v)` returns indexed64×64 and alias`portrait`, with the
  native48×48 bust at `(0,0)` and zero right/bottom padding.
- `portrait(name,v)` returns the native48×48 bust.
- `portrait_palette(name,v)` returns sixteen RGB555 hex colours, identical to
  the existing hero/folk vocabulary. No global OBJ palette entry is altered.

Existing NPC IDs2–6 and face IDs3–5 remain unchanged; no frame is appended.
NPC Sage0/Merchant1 and portraits Bloom0/Peddler1/Wizard2 are unsupported and
remain protected. Per-speaker portrait loading can use its existing bank6;
world folk stay in bank5. The art does not consume another palette or another
resident frame. Ordinary world NPC streaming and the64×64 portrait reservation
keep their established allocation.

All bodies have a24-pixel painted height, with planted feet at row31 of the
32-pixel canvas. Hermit/Nun bodies are15–16 pixels wide; Gardener plus staff is
18 pixels. No image exceeds the renderer's existing18×24 visual-depth box.
The staff and hands remain connected. World collision, solid flag, dialogue
distance, rewards, AI, OAM priorities and actor feet coordinates do not change.

## Native review and source evidence

Source outputs are at `/workspace/setup/forest-concepts/folk/`:

- `overview.png` and integer-nearest`overview-2x.png`: all fifteen live people
  and matching busts, with each small body on green and brown fields.
- `silhouette.png` and `grayscale.png`, plus2× companions: native shape/value
  comparisons using the same art, separately labelled as source studies.
- Thirty transparent source PNGs, plus`source-review.json` and
  `native-validation.json`: legal indices, native extents and per-image hashes.

The source boards were inspected at1× and2×. The first hooked staff exceeded
the requested body box by a pixel at its upper/left outline; its hook was
redrawn within the native18×24 envelope, rather than reducing the whole image.
The first Nun mouth curved upward; the world and portrait mouths now turn
down, preserving her mournful identity and the small tear. No automatic blur,
fractional alpha or high-resolution reduction is used.

Validation covers25 body frame instances including the exact aliases,
15 native portraits, exact48→64 padding, indices0–15, RGB555 colours, planted
feet, compact bounds, five distinct live bodies/busts per identity and precise
exclusion of all protected names. Those are construction/coverage checks,
not proof that every scene is visually successful.

**Runtime review still belongs to the integrated frozen concepts:** inspect
all three actual quest NPCs on healthy and dark blighted fields, their dialogue
portraits, large-canopy overlap, pale/silver cloth against bright grass, the
dark Cedar cloak and the Gardener's tool/feet. Source boards are not emulator
captures and do not establish actual input, collision or palette restoration.
Root integration/publication should append the frozen ROM/source evidence and
retain any limits found in those clips.

Source after native review:
`fd39704a0634b15bf2330b3dda2368a8ea8a136caa03b08a033bfbbf058a8aae`.
