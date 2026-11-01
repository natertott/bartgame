# Pixel-art reference register

Record what has actually been accessed. An article's URL or title is not
evidence that its text and illustrations were read. Keep source notes linked
to the [art bible](ART_BIBLE.md) and [decision log](ART_DIRECTION_LOG.md).

## Read article PDFs — 2026-10-30

All six user-supplied PDFs have now been received and read. Direct website
requests previously returned 403; that access failure is not used as evidence
of the contents. Page citations refer to the uploaded browser-print PDFs,
including navigation and footers. [Source records](references/sources.json)
contain their real filenames, page counts, URLs and SHA256 hashes.

| Source | Requested page | PDF filename / pages | Status |
| --- | --- | --- | --- |
| R1 — Richard Janes | [Introduction to pixel art](http://rjanes.com/tutorials/introduction_to_pixel_art.php) | 5 pages; [notes](references/JANES_GALVAN_PALEF.md) | Read |
| R2 — the-pixel.art | [Pixel-art character design](https://the-pixel.art/articles/pixel-art-character-design/) | 10 pages; [notes](references/CHARACTER_DESIGN_LIVRESQUARE.md) | Read |
| R3 — Alain Galvan | [Pixel-art design for game development](https://alain.xyz/blog/pixel-art-design-for-game-dev) | 6 pages; [notes](references/JANES_GALVAN_PALEF.md) | Read |
| R4 — John Park / Adafruit | [Pixel-art fundamentals](https://learn.adafruit.com/homebrew-game-boy-games/pixel-art-fundamentals) | 39 pages; [notes](references/ADAfruit_FUNDAMENTALS.md) | Read |
| R5 — Thomas Palef | [Tips to make pixel art for your games](https://medium.com/@thomaspalef/tips-to-make-pixel-art-for-your-games-7b770ffcfde3) | 9 pages; [notes](references/JANES_GALVAN_PALEF.md) | Read |
| R6 — Livresquare | [Creating pixel character art](https://tips.clip-studio.com/en-us/articles/11408) | 37 pages; [notes](references/CHARACTER_DESIGN_LIVRESQUARE.md) | Read |

All tutorial text and available relevant illustrations were reviewed. R2's
embedded figures needed direct extraction when page rendering hid them. R6
contains introductory examples and costume sketches, but its later main
tutorial illustration spaces lack images in the supplied PDF. Their explicit
text was read; missing figures are not falsely claimed as inspected. R4's
actual article occupies pp. 6–19; other pages are navigation and related content.

The [application matrix](REFERENCE_APPLICATION.md) connects the recommendations
to adopted shared rules, native-GBA adaptations and the second Drain pass.

## Source notes and future references

Record the real filename, page count and content hash, then read both text
and available example images. Create source notes with page references, paraphrased
recommendations, relevant example observations and the affected design rules.
Distinguish an author's explicit advice from our interpretation.

For each recommendation, record its application to this game, its scope and
any necessary GBA adaptation. Guidance aimed at another resolution, platform,
genre or animation scale needs an explicit translation rather than automatic
adoption. Resolve conflicting recommendations against the user's goals and
the native hardware constraints, and record the reason.

The redesign review should connect each adopted rule to visible examples in
the five Drain sets and state any advice intentionally deferred or inapplicable.
The earlier [research register](RESEARCH.md) remains separate evidence; it must
not be presented as a substitute for reading later references.

## Follow-up Drain application — third pass

The user’s review of the second-pass gallery is the direct evidence for this
iteration, followed by their request to keep varying both NPCs. The existing
six PDF notes remain the reference basis; this pass does not claim a new
article or missing illustration was accessed. Concrete applications and
tradeoffs are recorded in [third-pass characters](references/DRAIN_V3_CHARACTERS.md),
[fixtures](references/DRAIN_V3_FIXTURES.md), [terrain](references/DRAIN_V3_TERRAIN.md)
and the [direction log](ART_DIRECTION_LOG.md).
The preferred second-pass #1 frog and #5 wizard are comparison anchors, not
new sources or automatic adoption of a whole room.

## Final Drain and interface exploration

The next pass uses the user's v3 feedback to synthesize one final Drain, and
explores five interface skins under the newly specified minimal HUD. The
already-read six PDFs remain the common reference basis; no new website or
missing figure is claimed as inspected. [Final room decisions](references/DRAIN_FINAL.md),
[integration](references/DRAIN_FINAL_INTEGRATION.md), [interface art](references/UI_STUDIES.md)
and [HUD runtime](references/UI_RUNTIME.md) connect the work to source guidance
and distinguish adopted user requirements from exploratory visual treatments.

## GBA menu/interface research — 2026-10-30

[Menu research](references/GBA_MENU_RESEARCH.md) records fifteen fetched source
files at pinned repository revisions, distinguishing ten files actually inspected
for claims from contextual fetches. The evidence covers Pokémon bags/maps, Minish
Cap inventory/navigation, Sacred Stones preparations/help and Metroid Fusion map
knowledge layers. Specific windows, controls and state handling are attributed
to source lines. Proposed BARTGAME adaptations remain design judgments. Direct
review pages were inaccessible; ratings or reviewer quotations are not claimed.
The original six supplied pixel-art PDFs remain the native art foundation.

The [published interface/menu gallery](../../../art-review/ui-menu-exploration/README.md)
links actual mGBA results, independent critique and compact URL/revision/hash
records. The ten layouts are original adaptations, not reproductions of those
games' exact screens. All fifteen proposals remain unselected. Final evidence
uses source `d113d39`; earlier mutable pilot imagery is not relabelled as final.

## Adopted appearance and behavior-led enemy studies — 2026-10-31

The user's explicit UI/menu/map selection and request for ten animated
alternatives per enemy are the direct brief. The six read PDF notes and
G01–G18 application matrix remain the art reference; the existing pinned GBA
menu findings guide focus, assignment, help and map knowledge. No new web
source or missing figure is claimed. ENEMY_SMALL_STUDIES, ENEMY_SOFT_STUDIES
and ENEMY_HEAVY_STUDIES document original mechanic-led concepts. Appearance
and map integration are recorded in APPEARANCE_OPTIONS and ADOPTED_MENU_MAP.

## Selected bestiary and broken Heart

The user's latest selection adopts Coin Toad, Quill Moth, Trumpet Bellflower,
Pear Bladder and Moth Confessor. The boss brief is a purplish heart broken
down the middle. This is direct user direction, not a newly fetched reference.
The existing six tutorial/PDF notes and native motion/scale rules guide the
new Heart painter; [Heart decisions](references/BROKEN_HEART.md) record its
phase construction, source critique and eventual real-ROM evidence.

## Forest-first environment alternatives — 2026-10-31

The latest user brief supplies the local forest rules: living green/brown
walkable ground at every depth, structural corruption, limited coherent
vegetation, and clear permanent/temporary/interactive silhouettes. The six PDF
notes and G01–G18 remain the shared art basis. The new
[forest readability research](references/FOREST_READABILITY_RESEARCH.md) records
fresh primary game-source access and distinguishes measured native assets,
implementation evidence and our adaptations. The
[asset inventory](references/FOREST_ASSET_INVENTORY.md),
[terrain concepts](references/FOREST_TERRAIN_CONCEPTS.md) and
[prop concepts](references/FOREST_PROP_CONCEPTS.md) document coverage and design
decisions. Five alternatives remain exploratory; no whole forest treatment is
adopted by this request to generate review variations.

Final native catalogs and actual mGBA evidence are published in the
[five-direction gallery](../../../art-review/forest-concepts/README.md).
[Forest folk notes](references/FOREST_FOLK_CONCEPTS.md) add matching native
world characters and48px portraits. Final art source is `73df5c1`; source-only
inspection holds remain distinct from actual motion and interactions. Original
reference-game graphics/reconstructions stay in the local research directory;
the published metadata contains URLs/revisions/hashes and measured facts.

## Second forest review: infection and depth — 2026-10-31

The user's latest asset-by-asset feedback and foreground/depth request are
the direct authority. They supersede the first study's very restrained deep
grass and canopy corruption. Existing six PDF notes/G01–G18 and pinned primary
forest research still guide native forms, lighting and interaction semantics;
no new article or inaccessible illustration is claimed. The second pass's
terrain, props, folk and engine notes will record each adaptation and its
source versus actual-game evidence. The five new treatments remain unselected.

The completed second-pass notes cover [terrain and palette glow](references/FOREST_V2_TERRAIN.md),
[props and footprints](references/FOREST_V2_PROPS.md),
[fifteen folk](references/FOREST_V2_FOLK.md) and
[renderer/generation contracts](references/FOREST_V2_ENGINE.md).
Source `e5e3fcb` is frozen for the [native/actual review](../../../art-review/forest-concepts-v2/README.md).
This pass uses the previously read references and direct user feedback; no new
website access or missing PDF figure is claimed. Source diagrams, diagnostic
room fixtures and natural mGBA contexts have separate provenance and labels.
The shared bible now explicitly includes foreground depth and reserved
interaction approaches; the five local visual treatments remain exploratory.

## Canopy recognition and surviving greenery — 2026-11-01

The user's latest review accepts grey dead grass but rejects both healthy and
blighted canopy recognition. It directs broad horizontal limbs, recognizable
leaf masses under varied infection overlays, roughly twenty percent surviving
green in deep canopy and continuous partial player visibility. This direct
feedback is the authority for the new canopy studies. Existing PDF notes and
native-scale/cluster guidance remain the research basis; no new website or
unavailable figure is claimed. Janes pp.1–2 discuss controlled horizontal,
vertical and diagonal pixel runs; the current preference for horizontal tree
structure is user direction, not a universal orientation rule attributed to
that tutorial. Source assemblies and eventual real movement captures remain
separate evidence.

The [canopy authoring notes](references/FOREST_V3_TERRAIN.md) and
[visibility implementation](references/FOREST_V3_DEPTH.md) record the final
native construction and actual-room corrections. Source `e923557` is frozen
for the [eight-way source/actual review](../../../art-review/forest-canopy-v3/README.md).
The accepted grey ground and all non-canopy art are verified against the
previous profile6; new actual captures separately test recognizable tree
boundaries, partial character cover and matched gameplay cadence. All eight
infection methods remain unselected. These observations extend the direct
user feedback and existing read references; no new article is attributed.

## Space-dependent canopy compositions — 2026-11-01

The user rejects the previous canopy artwork as a major regression and
explicitly withdraws the repeated 3×3-block advice. This direct brief is the
authority for a new map-first composition pass and ten new tree/canopy
directions. It supersedes the fixed 32px crown construction recorded above;
earlier native/runtime technical checks do not imply aesthetic acceptance.

The initial internal geometry census reads five existing seeded forests in
mGBA: 125 rooms and 457 connected canopy components, including 94 single-cell
remnants. Each sampled room has a logical 96×64 fitting rectangle before
protected-feature exclusions. This measures available space; it does not
authorize painting across events or prove that an attractive composition is
visible from the walkable route. Native source anatomy, fit diagnostics and
actual room compositions will therefore be reviewed separately. Existing read
PDF/native-art references remain relevant; no new external article is claimed.

The [ten-direction adaptive review](../../../art-review/forest-canopy-adaptive/README.md)
now binds new source `c6dc060` to native-size catalogs, recorded-fit diagrams
and actual healthy/deep generated-room captures. It supersedes the rejected
eight-way artwork as the working exploration. Its
[independent critique](../../../art-review/forest-canopy-adaptive/validation/INDEPENDENT_REVIEW.md)
records remaining rectangular contacts, family resemblance and loading/menu
latency. These are observations from the new work and the direct brief; no
additional external reference is claimed.

## Pokémon Emerald tree crop — 2026-11-01

Direct reference: the user's inline image of overlapping green Emerald trees
over grass. No workspace source filename or source-pixel hash is available.
The image was inspected directly for foliage volume, small directional leaf
clusters, hanging shadow planes, short trunks and continuous local grass in
exterior gaps. The [reference analysis](references/EMERALD_CANOPY_REFERENCE.md)
distinguishes those observations from our new native-GBA implementation.

The prior ten adaptive studies are now rejected as the working canopy style.
The new focused leaf-crown pass preserves map-first composition while replacing
its skeletal anatomy and flat backing. Existing PDF guidance remains relevant;
no new article or copied source sprite is claimed.

The [focused leaf-crown gallery](../../../art-review/forest-canopy-emerald/README.md)
now binds source `ead9bb6` to fourteen native pieces and matched healthy/deep,
isolated, narrow and corner cases in actual mGBA. Hardware floor and alpha
checks establish the local-ground correction independently of source art.
Its [independent review](../../../art-review/forest-canopy-emerald/validation/INDEPENDENT_REVIEW.md)
records remaining texture, grid and gray-leaf readability limits. The preceding
ten-study anatomy is retained as rejected historical evidence.

## Uploaded GBA Sprite Art Guide — 2026-11-01

File: `GBA_Sprite_Art_Guide.pdf`, supplied workspace basename
`1-GBA_Sprite_Art_Guide.pdf`, fourteen pages, 1,001,327 bytes. SHA256:
`bc5400b675d76d7088f9b59f6a11feb04292c5c01ed34ce7cedece84b33fb4e1`.
All page text and illustrated teaching/game pages 1–12 were reviewed across
the root and independent reference review. The
[page-cited application note](references/TREE_GUIDE_APPLICATION.md) records
what applies to this tree-only study, the guide's factual/proposal distinctions
and the user's overriding dimensions/scope. Books and external readings listed
in the PDF were not independently read as part of this pass.

The user sets canopy work aside and requests a repeated 32×32/16×32 tree kit
with healthy/sick/dead structure and palette refinement. Source figures,
deliberately planted mGBA groves and natural procedural rooms remain distinct.

The [tree-only source/actual review](../../../art-review/forest-tree-study/README.md)
now binds source `c269b67` to twelve native assets and deliberately repeated
actual mGBA layouts on three floors. The
[independent qualification](../../../art-review/forest-tree-study/validation/INDEPENDENT_REVIEW.md)
records the structural state changes, clean contacts, tested overlap and
remaining small/dead-form composition limits. Uploaded-guide recommendations
are applied to this local tree kit; no newly read external source is implied.


## Approved tree kit — production integration, 2026-11-01

The user approved the twelve native tree assets in the preceding
[tree study](../../../art-review/forest-tree-study/README.md) for implementation
in actual procedural forest rooms. The uploaded *GBA Sprite Art Guide* remains
the source (same filename/hash above); no new external reading is claimed.
Its pp.6–9 guidance informs real floor under alpha, explicit root footprints,
ground-contact sorting and partial player visibility. The production
integration retains the approved indexed pixels and bank; it changes their
placement, layering and normal-build selection. Prior study renders remain
labelled diagnostic layouts; new whole-room evidence must come from actual
generated rooms in mGBA.


The [production integration review](../../../art-review/forest-trees-integrated/README.md)
now binds game/art source`fd7465d` to actual generated healthy, mixed and deep
rooms, native viewports and movement proof. The
[independent review](references/FOREST_TREES_INTEGRATION_REVIEW.md) records
source fidelity, real-floor contact, root/crown depth and remaining clearance
tradeoffs against the already-read guide. No additional external source is
claimed. The preceding diagnostic-only gallery remains historical evidence.
