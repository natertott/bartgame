# Five forest interaction vocabularies

These are **unselected native art studies** for `BART_FOREST=1..5`. The user's
new brief preserves forest identity at every blight depth: green/brown travel
planes, structural corruption, quiet ground and clear interactions. Shape,
material value and contact shadows distinguish a temporary obstacle from the
connected permanent forest. These forms are authored directly in
`art/forest_concepts_props.py`; no high-resolution illustration or screenshot
is reduced into game art.

## Shared construction and five local forms

| Study | Construction | Interactive treatment |
| --- | --- | --- |
| 1 — Fern & Oak | Rounded compact clumps, bowed lids, broad rounded openings | Familiar wood/brass chests, a broad stone slab with a jagged bomb fracture, a rooted hollow and connected pale silk. |
| 2 — Silver Willow | Slender leaf points, longer facets, pointed arch | Lighter metal straps, tall narrow pot neck, pointed stone threshold and trailing bark highlights. |
| 3 — Copper Beech | Squarer masses, strong horizontal planes, flatter lintels | Heavy chest straps and cross-bracing, broad pottery and stone facets, visibly flattened trunk cap. |
| 4 — Velvet Cedar | Tapered leaf clump and peaked opening | Dark teal chest bodies, angular shoulders, upright pot, pointed root crown and broad simple latch. |
| 5 — Pale Orchard | Rounded knotted growths and attached pale shelves | Compact petal-like bush highlight, rounded stone opening, small fungal shelves attached to the hollow and a plain wooden chest body. |

The palette alone does not carry these differences. Small utility drawings
share a restrained construction when their mechanics need a stable meaning.
Closed/open chest states preserve the same box and bands; a lifted object uses
exactly the standing object's pixels. The five pressure plates change their
outer bed and stamp while retaining the same broad contact area and obvious
pressed state. Web fibers remain anchored to the surrounding opening.

## Interaction grammar

- **Cut/lift bush:** one connected leafy clump with a dark lower contact and a
  broad lighter upper-left plane. It differs from continuous canopy masses.
- **Lift rock / heavy boulder:** whole compact stone with broad unbroken facets;
  the heavy version fills the cell. Neither carries the bomb barrier's seam.
- **Bombable slab:** a broad pale broken mass with one dark branching fracture
  and a fresh light edge. It fills the blocked lane rather than resembling a
  small collectible crystal or random floor scar.
- **Burnable barrier:** connected pale silk reaches its anchors. Dry thorn
  brush uses recognizable attached twigs and lighter dead material.
- **Key gate:** an open-slatted metal construction in a dark recess with one
  central, clearly cut keyhole on each retained logical gate tile. The current
  two-tile doorway repeats that retained tile; this art pass does not change
  placement or invent a new single-door mechanic.
- **Open gate:** opaque warm earth continues through the old gate footprint.
  The faint side remnants are passable trim. It is not a black cavity.
- **Pressure plate:** a whole 16×16 bed; the inner face visibly drops and lights
  when pressed. Its stamp is not a keyhole.
- **Censer:** a broad bowl, stem, foot and separate wick/flame. Lit flame poses
  change inside their existing frame and timing contracts.
- **Treasure:** every chest has a lid, side plane, broad latch, bands and short
  contact shadow. Wood, brass and relic tiers remain distinguishable through
  construction and material without changing their physical interaction tile.
- **Entrance:** a dark opening taller than Bloom with a pale sill and an
  unobstructed central approach. Cave stone, rooted hollow and leafy thicket
  retain distinct material masses. Closed trial grilles show bars; they do not
  falsely advertise a key requirement.

The source review exposed a transparent center in the initial hollow frame.
That center is now a real dark cavity in every open/closed hollow and thicket;
background grass cannot show through it. The first bush pass was also too dark
against the new grass. Broader upper planes now use the existing brighter
foliage inks while the low contact remains dark.

## Exact source and palette contracts

The module owns 48 retained BG names, with **54 native BG frame instances per
study**, and these three existing sprite sheets:

| Sheet | Native canvas | Frames per study |
| --- | --- | ---: |
| `lift` | 16×16 | 4 |
| `interactivechest` | 32×32 | 6 |
| `interactiveentry` | 32×64 | 6 |

Every lift frame reaches contact row 15. Standing `bush`, `rock_small`,
`boulder` and `myst_pot` are identical to their carried `lift` frames, including
literal colors. BG-only aliases `forest_obj_foliage` and `forest_obj_stone`
copy the existing core ramps. They let the terrain BG foliage/stone change
without recoloring the shared cloak, selected enemies or carried objects.
Gold retains the established bank. No global palette is mutated.

The enlarged closed chest is about 20×19 painted pixels with a shallow shadow
inside the existing 32×32 canvas. Entrances retain 32×64 canvases and the
established content offset of 16 rows. Their usable aperture is about 20 pixels
wide and at least 31 high. These are display sizes, not new collision boxes.
Existing frame identifiers, physical types, quarter collisions, prop flags,
animation counts and clocks remain unchanged.

Some old BG assets are direct floor pictures rather than transparent props.
The open gate is therefore an opaque earth tile. The legacy `relic` becomes a
full-cell low stone plinth rather than leaving accidental black corners. The
prop-zero fence and small dead tree use a matching grass background; the
separate blighted dead-tree overlay retains transparent corners. Portal/stair
cavities and the key gate's dark recess are intentional full openings. Plated
switches occupy their entire tile. Standard props and carried sprites keep
transparent backgrounds and use the engine's stored underlying floor.

**Shared OBJ scope:** liftables, enlarged chests and entrances are existing
shared sheets in each optional study ROM. They are not runtime per-region
skins. Their colors remain compatible with the selected enemies and gear.
The parent integration preserves Drain architecture, keepers, Bloom, selected
bestiary, equipment/pickup icons, UI and existing glitter. The normal forest
profile remains unchanged until the user chooses an alternative.

## Reference basis and review

The current user brief is the direct source for this pass. Existing read
six-PDF guidance remains applicable: R2 pp.3–6 (silhouette, proportions and
signature), R3 pp.2–4 (few material colors, selective outline and material
patterns), R5 pp.2–7 (economy and native iteration), and the shared G01–G18
application matrix. These page references belong to the already-read uploaded
PDFs recorded in `REFERENCE_REGISTER.md`; this note does not claim new article
access. The fresh primary-game comparison is recorded separately in
[forest readability research](FOREST_READABILITY_RESEARCH.md).

The source review is under `/workspace/setup/forest-concepts/props/`:
`interaction-variants-source.png`, its grayscale companion, native RGBA files
and `native-validation.json`. The complete **350 frame instances** (270 BG and
80 OBJ) pass indexed-canvas, sixteen-ink, size and lift-contact validation.
Standing/carried equality is explicitly checked. Native and 3× views were
inspected; large chests and black-aperture entrances were reviewed separately.
These are source inspections, **not emulator screenshots or playtest claims**.
Actual generated rooms, motion, interactions and packed-ROM audits belong to
the parent gallery's separate frozen-build review.

Remaining tradeoffs: small rock variants retain a common whole-stone silhouette;
the bright fixed carried-object banks stand out more strongly than decorative
stone. The deepest structural corruption belongs mainly to canopy and trees,
so functional gates keep their trustworthy material meanings across depths.
