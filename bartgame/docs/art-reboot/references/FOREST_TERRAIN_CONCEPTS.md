# Five forest terrain studies — exploratory, not adopted

These are five local forest alternatives, not a change to the common art
bible. `art/forest_concepts_terrain.py` owns their terrain. It paints native
indexed canvases for retained metatile names and returns the existing material
bank name. The build integration selects a study without changing tile types,
collision masks, prop associations, frame counts, clocks or room generation.
The interactive matter and carried-object matching are a separate props pass.

## Basis actually read

This pass read `ART_BIBLE.md`, `ART_DIRECTION_LOG.md`, `REFERENCE_REGISTER.md`,
`REFERENCE_APPLICATION.md`, and the source notes
`JANES_GALVAN_PALEF.md` / `ADAfruit_FUNDAMENTALS.md`. The six uploaded articles
remain identified by their real filenames, hashes and page counts in
`sources.json`; these new drawings do not claim a newly accessed article or a
missing reference figure. The implementation follows the recorded guidance:

- **G01–G03, G10, G12:** establish the silhouette, native proportions and
  scene hierarchy before small identifying marks. Ground is quiet; foliage
  carries denser deliberate clusters. A pit is a recessed cavity, not a raised
  outline. Side faces and root collars establish height and contact.
- **G04–G07:** cool shadow / warm selected light, native value groups and
  directional material planes. Internal leaf masses are connected; no concentric
  pillow bands or equal heavy outlines around every clump. The lower/right
  pockets and the near-side overhang supply depth.
- **G08–G09, G13:** all art starts at final 16px gameplay tile / 32×48 tree
  sizes. Curves and irregular leaf contours use deliberate pixel runs. No
  filtered HD reduction, photographic texture or post-render grading.
- **G15–G16, G18:** retain source iterations, inspect 1×/3×, and correct the
  authored RGB555 banks. Source assemblies are explicitly distinct from mGBA.

The source critic found the first study's internal leaf planes resembled
shingles or faceted rocks, the willow resembled wire bars, roots made a thin
Y, and water had a repeated full-width stripe. The second iteration removes
closed interior clump outlines, rounds and overlaps leaf edges, gives willow
an umbrella volume with only a few uneven lances, broadens a bent trunk into
an irregular root collar, and shortens water into separated ripple groups.
It keeps the readable green floor and warm-earth path from iteration one.

## Material constraints shared by all five

Grass remains grassy green at every depth, including `blight_floor`,
`forest_rot*`, `rot_*` and `forest_blight_vein*`. A typical floor is one middle
value with zero or one short blade/seam. There is no purple floor, dither
field, bright free-floating mote or all-over veins. Warm earth paths retain
quiet material-dark edges and a grass tongue at each retained transition.

Blight changes structure: missing crown lobes, exposed broken limbs, wineskin
or mauve leaf remnants, pale attached parasites, root fingers and a restrained
stagnant pool. It does not simply hue-shift the healthy tree. A shared skeletal
construction limits the vocabulary, while each study's reach, droop, parasite
and surviving crown explain its relationship to the living foliage.

The palette API preserves existing bank names and index roles. `ground`,
`foliage`, `water`, `stone`, `blight`, `decay_mix`, `rot_water` each have exactly
16 RGB555 colours. These are BG-only alternatives: no global `R.PALETTES` or
OBJ bank is mutated. The selected enemies, Bloom, Drain (`sw_`/`swh_`) and
protected sparkle tiles are not owned or repainted here.

Banks have exact shared ground colours at their grass indices. A tree's last
row is green ground with roots, not an opaque brown/purple base rectangle.
Canopy quadrants come from a coherent native 32×32 mass; connected foliage and
short hanging faces distinguish raised walls from traversable turf. Banks
remain topological families; bridges leave the travel axis open; ledges have
a consistent dark near-side face; pits use a genuinely dark cavity.

## The five directions

| ID / name | Native construction and identity | Local corruption |
| --- | --- | --- |
| **1 — Fern & Oak** | Rounded overlapping oak lobes, short pointed leaf clusters, broad bent bark collar, paired fern blades. Rounded wet cave stone and knotted root walls. | Gaps expose the old branch forks; a pale bracket grows from the trunk. |
| **2 — Silver Willow** | One umbrella canopy volume with a few descending lances, silver-grey bark, thin slate shelves and long pale root planes. | Sparse hanging lichen strands and exposed limbs replace some weeping leaves. |
| **3 — Copper Beech** | Broad irregular fans, long selected leaf highlights, warm copper bark and shallow curved bark scars; wide cave masses. | Folded wine leaves remain attached to a largely exposed fork. |
| **4 — Velvet Cedar** | Asymmetric tiered boughs and combed fan tips, dark cedar strips and squat shaded stone. | A small sagging dark veil spans exposed limbs; no whole-floor colour wash. |
| **5 — Pale Orchard** | Lobed orchard crowns with branch pockets, entwined root walls and small ivory parasite shelves. | Pale attached pods and broken thorn branches, still related to the living crown. |

Two crown arrangements (ordinary/second) and one bare skeletal tree per direction
cover the many retained oak/birch/fir/great-tree names coherently. They do not
introduce a new unrelated species for every legacy ID. Great trees are drawn
on their native 48×64 canvas, never resized from a smaller tree.

The retained `btree_6`–`btree_11` extension cells are intentionally retired
unplaced floor contracts: they render exact grassy footing, rather than
inventing an unrelated extra tree. The placed `btree_0`–`btree_5` remains the
complete native dead tree. Large boulder/tree-rock ground corners use exact
green inks in the ground bank, with their stone material on indices12–14,
so they do not introduce rectangular gray bases.

Mystery-room architecture also follows each construction: rounded stone,
slate shelves, broad planes, squat mass or parasite shelves for caves; oak
knots, willow roots, smooth beech scars, cedar strips or orchard braids for
hollows. Thickets inherit their direction's leaf mass. Floors remain quiet
and floor-edge banks match the floor's actual material.

## Review evidence and limits

The early mutable pilot was superseded after critique; its imagery is not
relabelled as final. Iteration02 is retained as a frozen source-review subfolder.

Source review artifacts are in `/workspace/setup/forest-concepts/terrain/`:

- `five-directions-native.png`: paired living/deep native source assemblies;
- `01-living-native.png` through `05-deep-native.png`: exact 240×160 sources;
- matching `*-3x.png` and `*-gray.png` files for integer/detail/value review;
- `*-tree-families-native.png` / `*-tree-families-3x.png` for complete tree
  construction, disease and the shared bare skeleton;
- `source-review.json`: scope and provenance.

The authoring check exercises all **469 terrain frame instances per direction**
at native 16×16, with only indices0–15. Every bank has sixteen RGB555 colours.
Full packed-tile limits, protected-runtime comparisons and actual mGBA room
views belong to the integrated build review. Do not label these source
assemblies as screenshots or claim the studies are adopted before selection.


## Allocated clocks and restrained motion

The retained frame counts and timing are unchanged. Lantern windows, lit wall
fungus, attached sick-canopy brackets, moving water/waterfalls and the water
beside lily rafts have local existing-ink phase variation. They do not add an
independent ambient glitter system or change the protected sparkle tiles.

The logical animated ground IDs `blight_ground2`, `blight_floor2`,
`blight_vein`, `forest_blight_vein0`–`7` and `forest_blight_pit` intentionally
have static painted phases. The allocated clocks remain in their contracts,
but ordinary soil, root marks and a pit rim do not blink or crawl. This keeps
the ground quiet and avoids suggesting a moving hazard or pickup where none
exists; structural canopy/parasite and actual water motion carry corruption.
