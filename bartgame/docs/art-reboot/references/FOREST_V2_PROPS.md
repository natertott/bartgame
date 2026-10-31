# Forest round two: objects that show their use

These are **unselected native studies** for `BART_FOREST=6..10`, local art
variants 1..5. The direct source is the user's latest review: reject the old
wooden chest and switch forms, widen the formal range, make the keyhole
unmistakable, distinguish the silk constructions, add vivid blight to the
preferred thorns, retain the preferred broad fractured stone, and give relics,
healing fonts and fallen logs greater presence.

The drawings originate at their final GBA sizes in
`art/forest_concepts_v2_props.py`. There is no generated illustration,
filtered reduction, screenshot grading or fractional alpha. G01–G18 and the
previously read six PDF notes remain the art basis; no new reference access
is claimed. In particular, the work applies form before texture, one identifying
feature, upper-left planes, contact shadows, selective contours and deliberate
material clusters. These are design interpretations of the user's review,
not claims that an article prescribed these particular objects.

## Ten wooden chests

Each local study has an A and B wooden design, both with closed and open
states. The existing 32×32 hardware canvas and lower-body contact remain.
The engine appends `wooden_b_closed` and `wooden_b_open` at frame IDs 6 and 7,
and selects A/B deterministically for wooden-value chests. This changes no
loot values, chest interaction footprint or key requirement.

| Study | Wooden A | Wooden B |
| --- | --- | --- |
| 1 — Black Sap Oak | Coopered travelling trunk: bowed staves and two plain hoops | Hollow-log coffer: a visible cut-ring end and an ordinary clasp |
| 2 — Violet Strangler | Slatted packing chest: flat lid, broad planks and small nail heads | Willow hamper: curved tapered body and a few woven ribs |
| 3 — Witchfire Weep | Acorn-cap coffer: a strongly domed wooden lid with a clear join | Cut-stump cache: cut-ring lid, root feet and an obvious front clasp |
| 4 — Amethyst Canker | Cedar footlocker: a wide low box with a flat hinged top | Salvage chest: misaligned planks, diagonal repair brace and nail heads |
| 5 — Royal Bruise | Root-bound box: dark timber, attached moss and woody bindings | Carved bark casket: an oval taper and broad carved grain |

All ten have an explicit lid seam and bright, simple latch. Their wood remains
matte and brown; small brass fittings do not turn the entire box into ornate
gold. The freely opened wooden chest latch has **no keyhole**. The lower body
is pixel-identical between closed/open states from rows 21–28. Open lids have
an upright wooden backboard, visible side hinges and a dark cavity joined to
the box; the first detached-cap draft was corrected before handoff. Some forms
are deliberately unusual, but the latch and opening construction keep their
interaction legible. Reinforced and relic tiers retain the first study's
construction, with the same familiar lid/latch/value distinctions.

## Five simple floor buttons

The pressure button is a physical raised face over a broad 16×16 foundation,
not a framed UI symbol. The five versions are a round stone button, a plain
square tread, a wooden treadle, a diamond slab and a small round plunger in a
stone well. There are no decorative checkmarks or arbitrary glyphs.

Pressed states lower the face by several native pixels, expose a dark recess
and add a restrained warm status mark or lit edge. Foundation, position and
footprint remain the same. The unpressed/pressed differences therefore survive
both color and grayscale inspection. These retain the existing `FLOOR` type:
Bloom can stand on them, and the existing puzzle performs the activation.

## Temporary barriers

- **Thorns:** retain the forked dry-twig construction of the favored first-pass
  2/3 family, but blacken the wood and add a saturated purple infection strand,
  fuchsia barbs, a pink-white hot knot and a few living green tips. The glow is
  made from explicit indexed clusters, not blur. The terrain's BG-only blight
  ramp supplies the hot colors; shared OBJ colors are unchanged.
- **Bombable stone:** retain the user's preferred #4 broad rounded broken
  slab, dark branching fracture and fresh pale fracture plane. It is intentionally
  the same chosen construction in all five local studies, rather than five
  nearly indistinguishable new cracks.
- **Silk:** five genuinely different fiber structures: a radial orb, a hanging
  curtain, a wrapped cocoon tangle, a corner fan and irregular stretched lace.
  Each reaches its anchors, has holes/negative space and uses pale connected
  fibers over a small contact shadow. Different constructions are visible at
  native scale; they are not merely shifted X patterns.
- **Key gate:** the BG gate contains bars and cross-bracing only. The new engine
  draws **one** large padlock for the complete two-cell gate, rather than
  repeating a tiny lock in each tile. The 16×32 lock has a visibly closed
  shackle and a six-by-nine-pixel dark round-and-stem keyhole in a bright brass
  face. The shackle's far leg was brightened after source review so it cannot
  read as already open.

Cleared thorn, bomb, silk and key barriers must restore the stored walkable
underlay through the engine. `door_open` therefore has a plain floor fallback
with no surviving posts or gold trim. The exact before/after floor restoration
is an engine/runtime requirement, not simulated in a source transition image.
Cape crossing cavities retain the existing mechanic and are reviewed by the
terrain/engine pass.

## Tall landmarks and longer logs

The new `forestlandmark` sheet uses a legal **16×32** canvas with four frames,
in this fixed order: `relic`, `shrine_available`, `shrine_spent`, `keylock`.
Every frame touches contact row 31. Four streamed eight-tile slots consume
32 additional OBJ tiles; allocation and draw ordering belong to the engine.
All images use existing `gear`/gold or `iron`/stone OBJ ramps.

The relic forms are a gem obelisk, a hanging reliquary, a golden offering hand,
a pointed cabinet and an antlered monstrance. Their mounted jewel/base
construction distinguishes them from loose item pickups. The real generated
relic location is a mossy stone plus pickup actor; the old `relic` metatile is
an unused legacy floor picture. Its tiny prior symbol is explicitly retired
to quiet footing, and the new marker is drawn at the real feature position.

Healing landmarks are a round stone basin, a root-mounted square trough,
a flower-like font, a faceted font and a three-legged carved basin. All have
an open bowl and support/base. Available water has an attached bright drop
or waterline; spent states remove it and expose the dark empty bowl. The
billboard replaces the old solid statue picture and is anchored to the
statue cell's foot. The healing pad below remains genuinely walkable: its
new drawing is a quiet low oval approach slab with a short water mark. It is
not falsely covered by a solid basin.

`log_group(variant, orientation='h', opaque=False)` draws the full fallen log
at **32×16** (or its literal 16×32 rotation). Its cut end, long bark body,
knots, broken branch and attached shadow form one coherent object across
`hlog_0` and `hlog_1`. Both cells retain `SOLID` collision. The generator can
promote individual decorative logs to this existing safe two-cell kit.
Transparent corner ink is authoritative: the existing prop/underlay renderer
then shows the actual dirt or sick grass, avoiding an opaque green rectangle.
An opaque grass option exists only for explicit source assembly inspection.

## Preserved identity, palette and scope

Ground bushes, small rocks, heavy stones and pots retain exactly the same
pixels and literal colors as their carried/thrown counterparts. The two BG-only
`forest_obj_foliage` and `forest_obj_stone` aliases preserve those colors while
forest terrain ramps change. No `reboot_core` palette or OBJ bank is mutated.
Equipment, pickups, Bloom, selected enemies/Heart, Drain keepers and UI are not
redrawn here. Native cave/hollow/thicket entrances retain their established
large canvases, using the favored 1/4 cave and 1/3 organic constructions as
anchors. They do not borrow the outer gate's keyhole: closed trial grilles
continue to mean a trial closure rather than falsely promising a key lock.

This painter delegates explicitly retained utility forms to the earlier native
prop module. That is a documented retention of project-owned drawings, not a
claim that all catalog entries were newly invented. It hands the two small
sick/dead-tree identifiers to the terrain painter, which now owns their
blackened, glowing anatomy along with the large tree families.

## Source review and validation

Source proofs are under `/workspace/setup/forest-concepts-v2/props/`:
`ten-wooden-chests-source.png`, `interaction-v2-source.png`, its grayscale
companion, exact native PNGs and `native-validation.json`. These are source
sheets/inspection states, **not mGBA captures or engine animation timings**.

All **380 native instances** (54 BG phases plus 22 OBJ frames per study) pass
P-mode, legal canvas and sixteen-index checks. All twenty ground/carried
comparisons match pixels and palettes; all twenty wooden states share the
same lower-body geometry; every landmark reaches its contact row. The ten
closed wooden silhouettes, five silk patterns and five simple buttons have
distinct native pixel hashes. Color, native-size, enlargement and grayscale
source views were inspected. Actual generated contexts, gate-floor restoration,
new draw-slot bounds and above/below occlusion require the parent engine's
separate frozen ROM/mGBA review.
