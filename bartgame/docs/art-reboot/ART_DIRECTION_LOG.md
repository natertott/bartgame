# Shared art-direction decision log

The [art bible](ART_BIBLE.md) is the current common specification. This log
records changes and their status; the [reference register](REFERENCE_REGISTER.md)
records which source material has actually been read. Keep all three aligned.

## How to record each art pass

Add an entry when an art-direction decision changes, including during iterative
work. Update its status and evidence as the pass proceeds. Individual pixel
edits need not become separate entries when they implement the same decision.

Each entry records:

- **Status:** requested, exploratory, adopted, superseded or blocked.
- **Scope:** shared game vocabulary or a named local area/asset family.
- **Evidence:** user feedback or a source filename/URL and page numbers.
- **Decision and reason:** the concrete rule or visual change.
- **Implementation:** affected painter, engine and documentation paths.
- **Review:** source comparisons, real-run captures, ROM/source version and
  relevant verification; state tradeoffs or unresolved issues explicitly.

## Established baseline, recorded 2026-10-30

**Status:** adopted shared foundation. This backfills decisions established
before this log; it is not a new redesign or a claim of reading new sources.

The art bible's native GBA construction, compact world scale, explicit anchors,
coherent materials, upper-left diffuse light, interaction vocabulary, and
surface-attached glitter remain the shared baseline. The intended contrast is
filth beside glorious light and gold, informed by the user's Bataille and
*Excalibur* direction. The Drain is the hub; the forest is the first of nine
planned regions. Local palettes must extend this common vocabulary.

Evidence: the user's art-reboot request, the existing
[research](RESEARCH.md), [critique](MOCKUP_CRITIQUE.md) and
[native art review](../../../art-review/reboot/README.md).

Implementation: `art/reboot_core.py`, native terrain/actor/item/UI painters,
and the art bible. The original reboot review identifies its own ROM; later
releases must retain their separate provenance.

## Selected Bloom sword gesture, recorded 2026-10-30

**Status:** adopted character-motion choice.

The user chose Step-and-cut from the five sword studies. Whole-body weight
transfer, blade pose and damage region share an eight-pose clock, with four
preparation, seven live and seven recovery updates. The apparent step does not
move Bloom's world position. This is the baseline to preserve during sewer work.

Implementation/source: `7c46553ff80bf558daa66f02c2b6d4d9f468e888`,
`art/sword_studies.py`, `src/player.c` and [sword notes](../SWORD_STUDIES.md).
Review: [selected swing](../../../art-review/step-and-cut/README.md).

## Drain identity and first five concepts, recorded 2026-10-30

**Status:** requested identities; exploratory visual treatments.

The user requires gray slimy masonry, flowing sewage, filth and debris,
conspicuous gold sewer fittings, a clear forest ladder, rails, a usable bridge,
a cartoon frog Billious Peddler with simple speech, and a hooded purple wizard
with a flame-tipped staff. The existing room layout, Bloom and glitter remain
fixed. These requested identities apply to every revised Drain concept.

Crown of Sludge, Crooked Brassworks, Moonlit Cistern, Rotten Reliquary and Royal
Drains are five unselected studies, with three mixed recipes. Their particular
brick bonds, silhouettes and palettes are proposals, not adopted shared rules.
The new decorative handrail separates foreground art from reused floor tiles
without changing the physical room or glitter surfaces.

Implementation/source: `486c1c3b8c05f33003ce3bf43ab240ecd8414120`,
`art/sewer_concepts*.py` and [Drain notes](../SEWER_CONCEPTS.md).
Review: [first concepts](../../../art-review/sewer-concepts/README.md),
published in `ffc5d86739bc45d5cbb1ce2c8e87d3a1e9c92008`.

## Reference-led second Drain pass — 2026-10-30

**Status:** completed redesigned studies; shared principles adopted; five local
Drain treatments remain available for user selection.

The user requests that all six supplied pixel-art articles guide future art,
that shared art-direction changes remain continuously documented, and that
all five Drain concepts and their complete deliverables be redesigned.

The documentation practice is recorded in the art bible, this log and the
repository's `AGENTS.md`. Initial website requests returned 403 and PDFs were
not exposed. The user then supplied all six files. Their complete text and
available illustrations have now been read; the [reference register](REFERENCE_REGISTER.md)
records exact filenames, page counts, hashes and image-availability limits.

**Adopted shared refinement:** G01–G18 in the
[application matrix](REFERENCE_APPLICATION.md): silhouette/form before detail,
role-appropriate scale and negative space, few material values, hue-shifting
ramps, directional volume, selective outlines/AA, coherent texture and value
hierarchy, material-specific highlights, planted idle motion and native review.
The matrix distinguishes explicit source guidance from our GBA interpretation
and records conflicting/optional advice rather than blindly applying it.

**Local implementation in progress:** reauthor all five Drain terrain and NPC
sets, preserving layout, Bloom and glitter. Floors become quieter masses;
architecture, metal and robes use light-facing and shadow planes instead of
pillow bands; filth is accumulated material rather than repeated symbols.
Frog and wizard silhouettes and full pose families are redrawn. The existing
fourteen frog action IDs stay stable; an appended concept-only `breathe` pose
coordinates upper-body movement with the existing head bob while feet remain
planted (R2 p. 7). Live streamed OBJ allocation stays unchanged.

Implementation: `art/sewer_concepts_terrain.py`, `art/sewer_concepts_npcs.py`,
`art/sprites.py`, `src/npc.c` and the scope/gallery tools. The original study
in `ffc5d86` remains the before reference. New source comparisons will include
silhouettes, grayscale values and rest/breathe joins as well as the complete
tile/NPC atlas. Final source/build hashes, actual mGBA coverage and observed
tradeoffs will be appended after the redesigned sources are frozen.

**Native sketch review:** the first new floor highlight pass created a
zigzag rhythm, so it was reduced. A later very sparse mortar pass risked
reading as plain concrete instead of brick, and overly continuous sewage
bands risked reading as a solid pillar or striped surface. The next refinement
keeps recognizable masonry masses, pouring-water breaks and impact shapes
without restoring all-over grid/noise. G01/G12 mean clear material hierarchy,
not simplification that removes the object's identity.

**Source freeze after native review:** the five reauthored terrain sets and
all five character/portrait families have been reviewed in their fixed room
context. Terrain source hash is
`6afdc6421cf3c611e05de3a18ead7b2fe07ab7b42cd5df27c255dc82361f5ae7`;
NPC source hash is
`7a1c388d75fa7ae77bc8c1a66f76c323fb8c31e81f6fea772c7a24c0ae7bb8bb`.
[Terrain decisions](references/DRAIN_V2_TERRAIN.md) and
[character decisions](references/DRAIN_V2_CHARACTERS.md) preserve page citations,
rejected sketches and native review notes. The native legal-art checks cover
3,680 terrain-frame options, five handrails, 150 world NPC frames and ten
portraits. These counts establish source coverage, not subjective quality or
proof of runtime presentation; packed-ROM and actual mGBA checks follow.

Remaining visual tradeoffs to judge in motion: Crooked and Royal floor bonds
are more patterned than Moonlit's flags; Reliquary is deliberately darker and
grubbier. Tiny world expressions remain simpler than their portraits. No
meaningless pixels are added to force all blank/seam pieces to differ.

**Packed and actual-run review:** game/art source
`476d1ede7162e20212707ede84d586a770f940f1` was frozen into nine builds: unchanged
default zero, five complete sets and three mixes. The independent decoder
passes 20,827/20,827 checks, including every packed native frame, exact original
IDs, the single appended breathing pose, fixed foot rows, and unchanged room,
Bloom/Step-and-cut, glitter, forest/interior, unrelated sprites, UI/font/title
and protected palette data. The audit's generic descriptor expectation was
corrected precisely for the approved extra source body frame; its hardware
canvas, per-frame streamed allocation and palette remain unchanged.

All 80 fresh mGBA cases pass 1,144/1,144 runtime checks. Each market clip has
75 unique uploaded rest samples with head/body offset `(8,6)` and 39 breathing
samples at `(8,7)`, with no phase mismatch. Every idle sample runs one update
per VBlank. Peak recorded OAM is 42/128; Drain BG use is 547–587/1024 subtiles
and one area palette. These measurements are sample coverage, not a promise
of worst-case performance. The default ROM remains byte-identical to the
approved Step-and-cut release (`547674bf…832c97a`).

The [second-pass gallery](../../../art-review/sewer-concepts-v2/README.md)
regenerates all asset options and eight source rooms, adds before/after,
silhouette/value and rest/breathe diagnostics, and includes fresh exact native
PNGs, normal-speed GIFs, full-rate videos and playable builds. Runtime clips
activate 11/15 frog body poses and 4/5 head poses; authored atlas coverage and
packed-source checks cover the entire family without claiming every pose was
activated by the idle fixture. All four flame frames are observed.

The remaining local tradeoffs are recorded for feedback: Crooked and
Reliquary have denser texture; Moonlit has quieter fields; small expressions
cannot carry portrait-level information. The shared G01–G18 rules stay in the
art bible while the user chooses a complete Drain treatment or mixed parts.

## Feedback-led third Drain pass — 2026-10-30

**Status:** exploratory revision in progress; no production room selected.

**Evidence:** the user likes the second-pass frog #1 and wizard #5, and then
explicitly asks for continued variation of both. All five new actor studies
therefore start from those preferred identities; they are not five identical
copies and the old options are retained as comparison evidence.

The user rejects every floor and wall (wall #4 is closest), all ladders
(ladder #1 closest; all arrows unclear), all water (falls resemble roots),
and all markets (#1/#2 closest). Preferred cues: cistern arches #1/#4; wizard
corner atmosphere #1/#2/#5 plus #4 decay; bridge #4; rails #1/#2 with #4 damage;
storage #1/#2 without the ambiguous blob; grate #4; banks #1/#2/#4. The small
gold outfall's purpose is unclear. These are starting points, not wholesale
approvals of any existing treatment.

**Decision:** five new coherent gray-brick floor constructions and damaged
wall treatments, with attached localized grime, readable pouring liquid, a
filled high-contrast up-arrow separate from ladder rungs, explicit pipe mouth
and discharge, clearly wooden storage lids, and newly constructed market and
wizard corners. Preserve the room layout, Bloom, sword timing, glitter and
unrelated art. Add the silhouette/flow/readability lessons to the shared art
bible; keep exact architecture and character choices local and exploratory.

**Implementation:** `art/sewer_concepts.py`, `art/sewer_concepts_terrain.py`,
new `art/sewer_v3_fixtures.py`, `art/sewer_concepts_npcs.py`, the Makefile
dependency list and review/publication tools. Existing article guidance G01–G18
remains applicable; no new source is claimed as read. The second-pass source
gallery remains immutable before evidence. Native source review, all ID/frame
atlases, five complete rooms, three mixed rooms, fresh mGBA recordings and
playable study ROMs will be linked after source freeze.

**Native freeze:** after source critique, all five floors have new bonds:
running bond, reclaimed unequal courses, long setts, chipped flags and
herringbone. The fifth remains deliberately denser, a comparison tradeoff.
Walls use damaged fourth-study masonry as their shared starting vocabulary.
The first sheet-water sketch still looked like a solid pillar, so the final
pass adds broken fringe, descending light packets, detached spray, impact
foam and pool arcs. An actual prior-ROM camera inspection found that the old
ladder arrow was beneath the fixed 24-pixel HUD. The new filled sign sits at
world `(160..174,32..46)` beside the original climb lane. Storage slime is
moved off its identifying wooden top to the foot of the stack.

Native drawing validation covers 3,680 terrain frame alternatives and five
rails. NPC source validation passes 273 checks for all 150 world frames and
ten separately drawn portraits. Option 1 intentionally retains the fifteen
preferred first frog's body poses; its new head changes the assembled actor.
The other 135 world-frame geometries change. Five distinct assembled frogs
and five pointed-purple wizard families remain available. This is honest
coverage, not a requirement to perturb every retained pixel.

Frozen terrain: `4cf8f2a0d0eeb0b64c808906c858c48cbd4ffc42600347c8a51f265e0058f86b`;
fixtures: `c148ceb7ca479cd76f0b82fdf1d6c02b930bb0be76c0982dee1ce71489a65c8a`;
NPCs: `3ac84ca8f1024bfbbbb391f3c817d06d73609e82d17239aa05981e0633b130bb`.
Full engine packing and real mGBA review follow this freeze, including a new
dedicated cistern viewpoint to inspect the complaint directly.

**First ROM pilot exposed an assembly failure:** the packed images matched
their source exactly, but reused floor IDs discarded most of the small outlet
fixture. Full-room visual review caught this; technical checks alone did not.
The outlet now has its mouth on the unique bank cells230/231 and falling
liquid/foam in unique animated cell241. The two reused north-wall pipe panels
058/059 now preserve pipe material, since all occurrences are in the same
horizontal pipe. The long pipe no longer breaks into disconnected fragments.
This changes no IDs, placements, collision, palettes, actors or engine behavior.
The initial `e354268` pilot is retained locally as superseded evidence.

After review of actual-map source crops, final source hashes are terrain
`913e22af37f33949d248675b8f3987daf17d989e0c7c8c04e32c76845ae8f561`,
fixtures `1f7d4289575f8a4a933ac6fef1b37a5510308a1ed31c4815629cd9a0c5d8ea12`,
with NPCs unchanged from the preceding native freeze. All final ROMs, atlases
and mGBA recordings are rebuilt from this corrected source rather than reused
from the pilot. Runtime review separately checks the actual outlet's animated
VRAM allocation, not merely another part of the stream changing.

**Final packed and actual-run review:** corrected game/art source `22b0af6`
produces nine frozen builds: unchanged default zero, five full studies and
three mixes. The independent decoder/provenance audit passes 20,845/20,845
checks. All 88 fresh real mGBA cases pass 1,280/1,280 checks, for 22,125 combined.
The new cistern and outlet checks track their own exact ROM/VRAM allocations;
another animated stream tile cannot satisfy them. Actual native images confirm
the visible outlet mouth, continuous wall pipe and below-HUD arrow.

Final Drain BG use across variants 1–8 is 601,598,603,606,587,600,588,606 of 1024,
one bank each; forest 693/interior 114 remain unchanged. Sampled peak OAM 42/128;
every idle sample has one game update per VBlank. All 88 source GIF palettes
are exact (largest individual color union 66). These are sampled measurements,
not worst-case or subjective-quality guarantees. The default ROM remains
byte-identical to the released Step-and-cut (`547674bf…832c97a`).

Independent reviewers examined all 12 assembled fixture families, native room
contexts, all five character silhouettes/values, and actual water/NPC
chronology. Runtime activated 11/15 frog bodies, 4/5 heads, 5/6 wizard poses and
all four flame poses; the packed-source audit covers all authored poses. The
[third-pass gallery](../../../art-review/sewer-concepts-v3/README.md) publishes
185 source-gallery files, every tile/frame option, all 88 actual cases, fresh
before/after comparisons and eight playable builds.

Remaining artistic tradeoffs are explicit: #5's herringbone is denser, #4
leans more filthy, floor joints depend on display brightness, and tiny world
expressions stay simpler than portraits. No whole Drain treatment is selected
for production. The user's preferred actor identities guide variation rather
than freezing the same two drawings across all rooms.

## Final Drain synthesis and five interface studies — 2026-10-30

**Status:** requested final Drain artwork; five exploratory interface treatments;
adopted compact HUD information hierarchy. Work in progress.

**Evidence:** the user's review prefers v3 floors/debris #1/#5, top walls #1/#3,
market #1/#3, wizard corner #2, bridge/rail #2/#5, storage #2/#3 and lower rail
#4; floor drains are all acceptable. Cistern #2 is preferred, but both arches
have illogical shading. The ladder/arch should be larger and taller, with the
arrow above. The wall pipe is unclear and should be larger with visible damage
and drips. The small outlet must project from the left edge in profile, pouring
into the river. Side walls need their own perspective, not repeated rear-wall
faces. These instructions supersede the previous unselected whole-room status.

**Decision:** synthesize one final room, preserving its physical arrangement,
Bloom, combat, forest and glitter while correcting perspective, flow and upper-left
lighting. Keep the familiar broad-eyed frog and pointed purple wizard identities.
Art identifiers may be cloned per placement where sharing prevents distinct side
walls or erases a fixture; compare resolved physical metadata, not merely ID bytes.
The previous v3 studies remain immutable comparison evidence.

**Interface request:** five genuinely distinct native styles, ranging beyond the
current brass vocabulary while retaining filth beside glitter. Gameplay HUD shows
only equipped items, hearts and gilt, with minimal backing and a clear top-center
world view. The old 24-pixel full-width HUD/minimap/resource layout is superseded.
Menus retain useful information and familiar controls. UI0 provides a neutral
compact baseline; UI1–5 are optional style studies rather than a selected skin.

**Implementation:** new final Drain painter/contracts and profile9, minimal HUD
runtime, native `ui_studies.py` skin families, six frozen ROMs, independent packed
audit and fresh real mGBA interface/world captures. Source assemblies and actual
framebuffers will be labelled separately. Existing six-PDF guidance remains the
reference basis; no new external source is claimed as read. Final scope, source
hashes, qualitative review and checks will be appended during the pass.

**Native source review and integration:** the final room now combines a broad
brick field with a value-matched repaired herringbone patch, preferred market
and wizard-corner forms, repaired timber, rounded brass rail and worn lower
rail. Enlarged arches have one continuous front material, a connected upper-left
bevel and a narrow right return. The taller ladder carries a filled up-arrow
above its rungs at world y14–24. The larger severed wall pipe has a dark cut
opening and leak; the side-profile outlet enters from the left and discharges
rightward into the river. Side walls use narrow capped inward-facing returns.

The original picture IDs are retained; 657 per-placement pictures are appended
so side-wall perspective and fixtures no longer inherit unrelated repeated
wall/floor images. All 657 resolved cell types, collision, prop and glitter
flags remain exact. Save formats and existing picture identifiers stay stable.
The first resident allocation exceeded capacity; exact whole-animation sharing
(same every-frame pixels, orientation, palette and timing) reduces it to
822/1024 BG subtiles, 69 resident animation allocations and one Drain bank.
This final-profile-only optimization does not simplify or skip authored motion.

The six UI profiles pass 666 native palette/canvas checks. Five study kits have
distinct frame/tab/marker geometry: Ivory Wire, Moulded Vellum, Black Glass,
Wine Reliquary and Salvage Ledger. Font metrics remain unchanged. Seventeen
10-pixel equipment pictograms are separately authored within valid 16-pixel
canvases; hearts have transparent surrounds. No large icon is cropped down.

The HUD places hearts at x2–81, gilt at x84–115, and equipped item pods on the
right. Empty slots and x120–175 remain transparent. All paint fits in 12 rows;
pilot hardware coverage ends at y9. It retains dirty-cache updates and removes
minimap/ammo/key/R-prompt data from the gameplay HUD. Relevant menu information
and input flow remain intact. The unchanged glitter emitter can now show glints
in the newly exposed top band because its HUD exclusion follows the new height.

Source and emulator pilots confirm the direction: the final-room independent
decoder passes 9,842 checks, and HUD runtime passes 23 checks including hidden
resource invariance, immediate visible updates, menu restoration and one-frame
hurt/OAM replacement at normal and maximum health. These are pilots, not the
final six-build evidence. Final freezes and full-screen review follow.

**User follow-up before freeze:** keep the minimap in the HUD, and show current
ammunition when the equipped item consumes blightseeds or arrows. This supersedes
the earlier no-minimap/no-ammo proposal and its corresponding pilot assertions.
Keep the top band compact: 30-pixel equipment anchors allow a small native
conditional count beside the icon, while non-ammo items use smaller local
backplates. Move the native 16-pixel explored/current-room minimap to a bottom
corner, outside the northern view. Keys and unrelated ammunition stay hidden.
Validation must check visible ammo changes only for the corresponding equipped
item, as well as actual maze exploration/current-room updates. The initial HUD
pilot remains useful history but is not final evidence for these new requirements.

**HUD source freeze after that follow-up:** the top remains at most 12 painted
rows. Equipment anchors are x148/178/208, with a 20-pixel local pod for normal
items and a 22/26/30-pixel pod for one/two/three ammunition digits. The actual
count is shown even at zero; only the corresponding equipped consumable reads
that count. x116–147 stays transparent. The original 16-pixel visited/fog/current
minimap now sits at (222,142) in its existing four reserved OBJ tiles. It updates
on navigation, not through a per-frame redraw. Floating title/continue/new-game
and victory prompts use an invariant pale ink with dark contours so the light
vellum theme's dark body ink cannot disappear into the title bitmap.
The five skin drawings and font metrics remain unchanged by this layout update.

**Full-screen pilot review found contrast defects:** frozen `443e7aa` passes its
byte, physical and functional checks, but actual native screens expose an old
dark-on-gold assumption: selected tab text is too dark on the new dark tabs.
All new skins now use their semantic high-contrast ink for the active tab;
legacy UI0 retains dark type on its gold field. Unbacked item-count figures use
invariant pale ink with a dark contour. The vellum victory body's dark semantic
ink was also passed through a floating-title outline helper, smudging letters;
backed victory prose now uses plain centered body type. Floating title prompts
retain pale ink and a dark outline. Other backed shop/dialogue/reward fields
were reviewed and already have the appropriate semantic inks.

The `443e7aa` technical success is recorded as superseded pilot evidence, not
proof of visual quality. All six ROMs and actual recordings are regenerated
after these narrow UI-runtime fixes. Native art/palettes remain frozen.
A death-and-return GIF crosses palette fades/areas and exceeds GIF's 256 colors;
publish its exact native PNGs and full-rate MP4 instead of presenting a
quantized GIF as faithful framebuffer colors.

**Final corrected review complete:** game/art source `87abc1b` is frozen in six
ROMs: the final Drain with neutral UI0, plus the five optional skins. The
independent decoder/provenance/regression audit passes 59,509/59,509 checks,
including 414 mGBA runtime checks. All 36 normal-enemy damage samples replace
sword OAM one video frame after hurt. Exact minimap states, conditional ammo,
hidden keys, cache updates and menu restoration pass across all six builds.
All 52 code inputs match the frozen git commit and every art input hash is
recorded. The UI cursor is explicitly a permitted styled interface asset and
is decoded against its source; it is not exempted as an unchecked world sprite.

The separate visual-capture suite passes 894/894 checks in 234 fresh real mGBA
cases (39 per profile). All 27 five-way screen families were visually examined,
including menus/key items/maps/zoom, shop choices/purchases/unaffordable state,
two dialogue pages, rewards, title choices, death/return and actual Heart
victory. An additional 15 native selected-tab contexts confirm readability.
Maximum sampled OAM is 40/128; ordinary idle updates match VBlanks. The Drain
uses 822/1024 BG subtiles in one bank; forest 693 and interior 114 stay exact.
These are sample evidence and preservation checks, not aesthetic scores or
worst-case guarantees.

The [final room/interface gallery](../../../art-review/drain-final-ui/README.md)
publishes the full native room, 14 fixture crops, every placement/frame atlas,
five material/geometry UI directions, and original native framebuffers. All
quantized death/return GIFs are omitted; exact PNGs and full-rate lossy MP4
viewing copies remain. Earlier pilots are kept separately, never relabelled
as final. Source assemblies and mGBA captures are explicitly distinguished.

**Adoption:** normal builds now use final Drain profile 9 and the neutral
compact UI0, with minimap and relevant ammunition retained. The five skins
remain proposals for user choice. The original room art and three prior study
branches remain available as historical evidence. Remaining tradeoffs: the
herringbone repair patch is denser, Wine is intentionally most ornate, Vellum
most bright, and tiny HUD icons simpler than inventory illustrations.

## Five interface remixes and ten menu layouts — 2026-10-30

**Status:** exploratory prototypes; production UI0 and the final Drain remain
the baseline. The user likes design structures #2/#4/#5 and primarily palettes
#4/#5, then explicitly requests new structures using palettes #1/#4/#5. We
follow that explicit palette set, keeping light-vellum coloring out of the new
studies. Structure and palette become independent recipes for future regions;
automatic area changes are not introduced before a palette policy is selected.

**Five new styles:** Winebound Folio (revised folio, wine), Mossbound Fieldbook
(folio/ledger, green), Ivory Reliquary (restrained brocade, ivory-wire palette),
Burgundy Archivist (reinforced brocade/ledger, wine), Verdigris Devotional
(repaired folio/embroidered ledger, green). All new drawings remain native
4bpp/RGB555. Old UI0–5 exported artwork and the seventeen compact equipment
glyphs must remain exact. The HUD retains hearts, gilt, equipment, corner
minimap and ammo only for equipped blightseeds/bow.

**Ten independent menu layouts:** loadout workbench, pocket ledger, fieldbook,
tactical atlas, toolwheel, twin atlas, expedition dashboard, focus cards,
barrier/tool index and quick ribbon. Each explores a gameplay or usability
priority rather than merely rearranging decoration. Compare them using one
common new skin; compare the five skins using the original menu layout. All
item/key/map/zoom views remain real interactive prototypes with actual inventory,
known-map gates and current/generated room data. No new loot or mechanics are
implied by a presentation change. R changes pages; Start closes; A/B/L assign
on the item page; map A zooms and B returns.

**Research:** [GBA menu evidence](references/GBA_MENU_RESEARCH.md) studies pinned
public implementations of Pokémon Emerald/FireRed, The Minish Cap, Fire Emblem
The Sacred Stones and Metroid Fusion: category focus memory, explicit neighbor
navigation, anchored help, separate map knowledge layers, zoom continuity and
visible equipment assignment. It distinguishes source facts from our proposals.
Review-site requests were blocked; no rating or reviewer endorsement is invented.
No Nintendo artwork/code or commercial ROM is imported into production assets.

**Implementation:** new style recipes6–10 and independent menu profiles1–10,
with preserved defaults. Declarative native geometry and a study-only renderer
restore the playfield charblocks on close. Native/source and actual mGBA review
will cover selection, all assignments, focus persistence, empty/partial inventory,
map/zoom and fog, pause-state invariance and restoration. Source hashes, review
findings, choices/tradeoffs and final evidence are recorded as the work proceeds.

**Native and interactive preflight:** all new UI6–10 structures and HUD pods
are authored at native size; the 0–5 exported art remains exact (738 independent
checks) and seventeen compact equipment glyphs stay unchanged. Structure/palette
recipes explicitly use former2/4/5 forms with former1/4/5 colors.

The ten layouts now run in the real engine. A common native 600-tile pause
canvas permits distinct compositions without consuming the original font pool.
It saves/restores world characters and HUD sprite allocation; defaultMENU0
retains the original path. Early pixel-by-pixel redraws missed short button taps;
cached tile-word/mask/glyph rendering and an ordered pause-only input queue
correct that. Actual input remains two-frame taps. Header/page/overview caching
keeps typical tool focus and cached map motion near two video frames. First
all-25 terrain chart generation takes about52–54 frames; schematic graph/route
views avoid that generation. These are measured prototype tradeoffs, not a claim
that every menu/map opens instantly. Prototype buffers fit native EWRAM; default
production does not allocate the study renderer.

All ten pilot flows pass 550/550 checks over150 actual presentations: reachable
items, all A/B/L assignments through the canonical unique-item rule, persistent
item/key/map focus, empty inventory, no unknown terrain disclosure, unchanged
world/room/RNG during pause and legal static/live-animated VRAM/palettes after
close. A new Winebound skin pilot passes98 checks over28 presentations. These
are preflight results; final committed sixteen builds and fresh captures follow.

Native review corrected generic key labels, clipped compact descriptions, last
ammo digits, narrow legends, ambiguous Gate/Chest and Door/Relic glyphs, and
unlabelled dual-map panes. Gate is G, Relic R, and the eight-entry key is fitted
without inventing map knowledge. Twin Atlas labels Region/Chamber. Quick Ribbon
leaves room for its caption. Short wide cards show selected consumable quantity
on the same title line, preserving concise action help. Compact fieldbook/grid
icons intentionally trade illustration detail for open space; Workbench, Wheel
and Ribbon offer larger native illustrations for comparison.

**Final immutable evidence:** game/art source `d113d398692e9b98903e5d5a944ea3cadc2d6282`
is frozen in sixteen ROMs: UI0/MENU0 baseline, five skins UI6–10/MENU0, and
ten layouts UI6/MENU1–10. All 312 actual mGBA presentations pass 1,166/1,166
runtime checks. The independent source/ROM decoder passes7,523/7,523 checks,
including exact protected world/sprite/animation data and historical UI0–5.
All 22 selected baseline framebuffers additionally match the previous final
Drain output pixel for pixel. These are behavioral/preservation evidence,
not aesthetic scores or human playtest results.

The final native review verified short-card seed/arrow counts, distinct
Gate/Relic markers, Twin Region/Chamber labels, complete eight-marker legends,
Quick Ribbon caption clearance, counted-key wording, empty pages and fog.
All ten layouts accept ordinary two-frame inputs, retain item/key/map focus,
apply the canonical unique-item assignment rule, and restore room/HUD memory
after close. The default ROM is restored byte-identical to this freeze's v0;
its baseline screenshot behavior remains exact to the previous release.

[The new gallery](../../../art-review/ui-menu-exploration/README.md) separates
five visual skins on the existing layout from ten arrangements in one common
skin. It includes actual item/key/map/chamber views, native PNGs, full-rate
cut-labelled control clips, individual playable ROMs and the sixteen-ROM ZIP.
Source geometry proofs are labelled separately. Five over-256-color
death/return GIFs are omitted; exact PNGs and lossy MP4 viewing copies remain.
Gallery assembly independently verifies 275 native crops/enlargements.

**Selection status and limits:** all fifteen options remain exploratory;
normal UI0/MENU0 is unchanged. The source-backed research yields usable design
patterns, not reviewer ratings or imported Nintendo assets. Workbench emphasizes
loadout, Twin Atlas navigation, Focus Cards learning and Quick Ribbon simple
sequential reassignment. Compact 3/7 glyphs, wheel direction learning, long-row
travel and cold terrain-map cost are explicit comparison tradeoffs. No automatic
regional palette policy is adopted. Future work should combine user-selected
geometry/palette/layout and then profile that chosen production path.

## Selected appearance, event maps and enemy alternatives — 2026-10-31

**User selection:** HUD1 Winebound Folio; item layout1 Loadout Workbench;
map layout2 Pocket Ledger. Add Options to the home screen, available with or
without an existing run. Menu/dialogue frame style may be Winebound Folio,
Mossbound Fieldbook or Ivory Reliquary, and the three palettes cycle separately.
Keep preferences independently of run saves. The selected HUD stays Winebound.
These elements are adopted; no enemy alternative is selected yet.

**Map correction:** overview rectangles summarize all permitted known event
types without overlapping them. Chamber charts use the generator's exact
feature positions, with a distinct player/selection/Heart/shrine vocabulary.
Readable outlined pictograms and letter cues replace ambiguous tiny glyphs.
Completed-state and Map/Astrolabe/fog rules remain truthful. A paused full-room
metadata preview snapshots/restores live room, spots, saved marks and local
RNG while suppressing rendering, avoiding invented centered coordinates.

**Enemy scope:** six existing AI families, ten full alternatives each: grounded
pursuit, airborne hunter, cardinal projectile shooter, elastic hopper, heavy
directional attacker and phase boss. Names are mechanic identifiers for review,
not constraints on subject matter. Concepts may be weird animals, animated
objects, ceremonial debris or abject organisms. Silhouette, motion and attack
readability precede texture, using the existing native banks and foot anchors.
All old frame IDs remain, with added presentation-only inhale, windup, strike,
recovery, hurt and boss-phase poses where useful. Movement, damage, collision,
AI timers, drops and actual vulnerabilities do not change between concepts.
Ordinary death still uses the shared puff rather than a fictional body state.

**Sources:** current user feedback and the already-read six PDF tutorials
(G01–G18 in REFERENCE_APPLICATION), plus the pinned GBA menu research from the
previous pass. No new inaccessible article is claimed as read. Existing
Drain/world/Bloom/glitter are retained. Source pose boards and complete frame
atlases are labelled separately from actual mGBA AI/controls recordings.
Final frozen builds, captures, review findings and delivery evidence follow.

**Native review refinements:** the first solid/background composites exposed
weak separation in the foliage-colored small enemies. All 30 such concepts
were compared on four actual captured material backgrounds (120 before/after
source composites). The study-only enemy bank uses brighter jade/wood planes
and ivory attached highlights, retaining the original dark contour. Physical
OBJ bank 10 is reserved for these three enemy bodies; all world material items
select explicit other frame palettes, and the paused icon cache restores the
entire live palette on return. The protected cloak/carried-bush bank remains
unchanged. A seed shaped too much like a glitter cross becomes an asymmetric
bronze pod. Ten genuine back views also correct the grounded pursuer's old
south-facing artwork when travelling north, without changing its gait clock.

The boss's expanded thirteen-pose set streams one32-tile frame instead of
keeping 416 tiles resident. Skipping its unused temporary knight sheet keeps
the conservative all-enemy/prop/menu allocation under the 876-tile playfield
limit. Draw-only presentation restores the Actor's original AI-frame field;
hurt selection works during the existing knockback pause. None of these
presentation refinements changes damage or actual vulnerability windows.
The Options page previews all nine frame/color combinations, persists its
own CRC-checked SRAM record, and styles the continuation/picker marks without
recoloring the fixed Winebound HUD or minimap.

**Final core evidence:** source `5eedc6dae94d8c1ea21c55b8668435bcf0be884d`
is frozen in eleven ROMs: selected interfaces/current enemies (default 0), and
enemy alternatives 1–10. All nine frame/palette combinations pass 280 appearance
checks over 56 actual mGBA views; legacy save migration/roundtrip/corruption
passes 6. The hybrid Workbench/map suite passes 223 checks over 36 views, including
all 25 generated rooms, a genuine shrine, live moving Heart, cold unvisited
Astrolabe preview, Map-only/fog/completion, assignment/focus and full pause/
restore invariants. Map symbols are outlined 7px designs with a nine-entry key;
the healing Shrine and boss Heart are explicitly different labels.

The eleven enemy builds pass 900 checks over 132 natural-AI encounters, including
hurt/death, boss phases, natural cave combat and post-menu weapon/palette
restoration. All thirteen boss poses occur in every positive profile. The
independent ROM/source audit passes 11,632 checks, including 108 exact positive
gameplay-flow comparisons. Protected world/Bloom/items/font/glitter and original
IDs remain exact. The baseline's four boss sample timelines differ by an
initial update/global-frame phase from the expanded streamed presentation;
their unchanged source AI is distinguished from that clip-alignment limit.

The final source gallery contains 640 native frame instances: 610 body poses,
20 weapon and 10 seed companions. Six exact-palette source GIFs show every
body pose at 150ms for inspection, with companions in complete native atlases;
they do not pretend to reproduce actual attack timing. Real mGBA clips have
their own truthful event/input traces. Source and actual captures are separate
in [the new gallery](../../../art-review/appearance-enemy-studies/README.md).

Linked maximum EWRAM is 212,184/262,144 bytes; the conservative union of all
enemy/prop/menu allocations is 816/876 OBJ tiles. The normal build is restored
byte-identical to frozen v0 and every profile's `make -q` is current. Native
marker/maps, nine appearance combinations and sixty concept silhouettes were
visually inspected. Several rounded boss maw forms rely on appendages and
phase behavior for identity. Enemy proposals are still unselected; the user's
interface choices and Options behavior are adopted.

**Final visibility follow-up:** the longer healthy pursuer encounter correctly
draws bridge rails over the lower body, making it less useful for comparing
leg motion. It remains a depth-context recording. Ten additional natural
spawn encounters (seed 6/cell 9, open blighted floor) each show 96 actual updates
with the complete body footprint on unobstructed floor. All 960 footprints,
60 checks and 9 matching comparison flows pass. No enemy state/position/pose
or terrain is assigned. The combined publication contains 234 actual cases and
1,469 runtime/save checks; the original 132 enemy reports remain unchanged.
The main gallery links this clear-floor view for grounded gait comparison,
while source GIFs retain complete facing/pose coverage. No ROM/art input
changed for this camera/context refinement.

## Selected enemies and the broken Heart — 2026-10-30 (Pacific)

**User adoption:** Coin Toad9, Quill Moth9, Trumpet Bellflower5, Pear Bladder9
and Moth Confessor6 are selected from their respective behavior families.
The shooter keeps its matching seed5; the heavy attacker keeps weapon6.
The boss must remain a purplish heart broken down the middle, rather than one
of the ten experimental object/maw forms. These choices are now production
defaults, preserving historical profiles0–10 for comparison.

**Implementation:** profile11 dispatches each selected family to its complete
existing native artwork; only the Heart receives a new painter. Its13 poses
keep the established32×64 canvas, foot anchor and collision scale. A jagged
middle fracture, two lobes and a tapered point carry its identity through
pulse, charge, release, spawning, lunge, hurt and death. Purple material planes
use the existing blight bank, preserving the selected bellflower's colors.
No combat/AI/physics, world, UI preference, save or Bloom changes are required.

**Basis and evidence:** the current user choice supersedes the prior unselected
status for these five enemies and the boss direction. Existing native/PDF
rules and source notes still apply; no new external article or source image is
claimed. Native source critique and actual mGBA recordings will be published
with a frozen default ROM, exact selected-frame comparisons and the complete
Heart phase review. Source galleries remain separate from actual gameplay.

**Final evidence:** ordinary `make -j4` at game/art source `770b542` produces
SHA256 `9330a44a4e27d99606a757134aa41a62adb122a74315c400e1ad3427048c8661`.
All thirteen actual mGBA cases pass 88 runtime checks, including the Heart's
ring, fan/spawning, lunge, hurt and defeat. The independent audit passes
12,919 checks, including all 51 selected non-boss native frame instances,
all thirteen new Heart poses and actual visible sprite pixels for every pose.
Protected world/Bloom/items/UI/font/glitter, palettes and every `src/*` file
are exact to the prior release. All thirteen sampled gameplay trajectories
match its prior positive-profile behavior. Source catalogs use fixed review
holds; separate actual footage establishes gameplay timing. Historical
profiles0–10 remain unchanged, with an explicit profile1 rebuild byte-identical
to its frozen release. OBJ remains816/876 and EWRAM212,184/262,144.

[Selected-enemy gallery](../../../art-review/selected-enemies-heart/README.md)
and [playable release](../../../downloads/selected-enemies-770b542/README.md)
record the final adoption. The purple Heart is recognizable in the actual
blighted-room captures; the continuous central fracture remains visible in
all thirteen live poses. No new external research is claimed for this choice.

## Forest-first environment studies — 2026-10-31

**User direction:** prepare five complete forest art alternatives for review.
Every depth must communicate forest before corruption. Preserve readable green
grass and brown earth; show blight through foliage structure, dead limbs,
parasitic vines, flowers and restrained accents. Keep floor detail subordinate,
use a limited versatile tree/prop vocabulary, and distinguish walkable space,
permanent solids and temporary interactions by shape, value and contact shadow.
Water, bridges, recessed holes and openings inherit the successful Drain's
semantic clarity, with clearer forest water. Keys, bombs, candle and cape must
continue to mean the same things.

**Exploration:** Fern & Oak, Silver Willow, Copper Beech, Velvet Cedar and Pale
Orchard are five different native constructions, each spanning healthy, mixed
and deep forest, ground transitions, water, tree groups, props, gates, chests,
entrances and the three mystery-interior styles. `BART_FOREST=1..5` will select
the alternatives explicitly; ordinary builds retain production profile0 until
the user chooses. Environment OBJ props are shared portable/chest/entry drawings
in those study ROMs. Bloom, chosen enemies, gear/pickups, UI, Drain architecture
and keepers, physics, generator layout and existing glitter remain protected.
BG-only object palette aliases preserve exact ground/carry colors without
recoloring the cloak or selected enemies.

**Evidence plan:** inventory every retained environment identifier and pose;
apply the six already-read PDFs/G01–G18; inspect fresh primary game sources for
terrain and interaction readability. Record actual URLs and observations in
FOREST_READABILITY_RESEARCH. Review native source sheets, coherent group
assemblies and value/silhouette diagnostics before packing. Capture the same
generated rooms and interactions in real mGBA for all five, preserving source
and actual evidence separately. Art preferences remain unselected; physical
contracts and production-profile bytes will be checked against the prior
selected-enemy release. Final counts, critique and release links follow after
the frozen build/capture audit.

**Pre-publication correction:** independent source/ROM checks found that the
unchanged `sparkle_white` tile pixels inherited a restyled stone BG ramp. The
study integration now routes those pixels to the existing BG-only original
stone alias, preserving their exact visible white highlight and animation
clock. OBJ glitter remains unchanged. All six builds and matched capture
provenance are regenerated after this correction; the earlier source draft is
not relabelled as final evidence.

**Final forest evidence:** game/art source `73df5c1` is frozen in six builds:
control 0 and optional profiles 1–5. The control and restored ordinary build
remain byte-identical to production, SHA256
`9330a44a4e27d99606a757134aa41a62adb122a74315c400e1ad3427048c8661`.
Every `src/*` file and all sixteen OBJ banks are unchanged. Bloom, selected
enemies/Heart, equipment/pickups, interface layout/font/title, final Drain
architecture/keepers and existing glitter retain their art. The studies cover
463 BG identifiers (523 owned phases plus five protected sparkle phases),
24 environment OBJ/portrait instances and local BG ramps. IDs, collision,
prop/glitter flags and animation clocks remain stable. Forest use is 590–609
of 1,024 subtiles with ten of twelve banks; interiors use 109 tiles/six banks;
the final Drain remains at 822 tiles/one bank.

The source catalogs contain 2,760 frame instances, 552 per option, with eighteen
atlases each, eight five-way family sheets, fifteen exact source GIFs and
19,750 passing export/atlas/hash checks. Source state pairs and 180ms inspection
holds do not represent engine timing. Six unused root-extension cells are
explicitly retired to grassy footing; allocated soil/root/pit phases remain
visually quiet. Initial shingle-like crowns, wire-like willow leaves and
repeated water stripes were refined into connected foliage, thicker root
collars and shorter ripple groups before freezing.

The main mGBA suite passes 3,307 checks across 498 cases, 83 per build, including
all 25 room viewports, natural mystery styles, NPC dialogue and real item
interactions. The independent source/ROM/runtime audit passes 75,315 checks.
A focused follow-up adds five natural Coin Toad encounters/30 checks, with exact
prior AI trajectories and visible contact on unobstructed green ground. The
combined publication contains 503 cases, 3,337 runtime checks and 65 full-rate
clips. Native PNGs are exact; MP4s are lossy viewing copies, GIFs require exact
colors, and raw recording archives stay local. Every report discloses fixtures
and distinguishes source artwork from actual captures.

One observation matters to comparison limits: smaller BG payloads can finish
a chasm transition one VBlank earlier. With movement held across that boundary,
the old fixture ended two pixels farther along in some studies. The final
shared input releases movement before play resumes; initial/final positions,
geometry, RNG, progress and ordered mechanic states then match. Original
transition ticks remain disclosed. No engine, physics, generator or art change
was made to force timing equality. Earlier held-direction recordings remain
archived as superseded fixtures.

**Critique and status:** Willow and Cedar have the strongest canopy silhouette
changes; Oak, Beech and Orchard share a closer broadleaf family. Ground stays
quiet and readable, though open rooms can feel spare. Repeated canopy bands
still expose some grid rhythm; wood/brass chest tiers are subtler than relic
chests; unlit censers and leafy thicket frames remain next-pass targets. The
green Coin Toad is less prominent than Bloom, but its contour, eyes and movement
remain readable. These are tradeoffs for the user's selection. None of the
five directions is adopted. The [actual/source review](../../../art-review/forest-concepts/README.md)
and [five-ROM release](../../../downloads/forest-concepts-73df5c1/README.md)
record every alternative. Research notes separate primary evidence from
original adaptations; no reference-game pixels are imported.

## Forest second pass: black sap, purple fever and layered depth — 2026-10-31

**Direct user feedback:** the first five deep forests are far too restrained.
The second pass needs blackened dead wood, sick sparse grass, filth and vivid
glowing purple blight veins. Healthy grass remains a useful anchor. Keep the
favored healthy canopy1/3 and trees1/5 as references; cave walls1/4 and hollow/
thicket walls1/3 guide construction. Vibrant thorns2/3 gain purple infection;
bomb stone starts from4. Redesign all dead/sick trees, blighted canopy/walls,
tall grass and ledges. Five webs must differ in construction. Locks require an
obvious keyhole; all four cleared barrier kinds return the correct normal
floor. Explore much wider wooden-chest forms and simpler physical switches.
Relic/shrine markers should stand taller, and logs can occupy multiple cells.

**New character scope:** fifteen original forest folk concepts, five per
existing Hermit/Nun/Gardener role, with matching native portraits. Follow the
sewer's silhouette, single-hook, material-plane and native-scale rules rather
than merely recoloring hooded humans. Selected enemies, Bloom, equipment,
Drain keepers/layout, interfaces and established glitter remain protected.

**Engine/art intersection:** add adjacency-aware visual aliases for isolated
water/canopy, ends and joins; preserve semantic room/collision data wherever
only the rendering changes. Use genuine foreground canopy fringes over
walkable grass, with partial player occlusion and visible feet. A raised root
arch demonstrates a real walkable underpass; it does not claim an accessible
upper bridge deck. Investigate height through consistent ledge lips, vertical
faces and shadows, and safe multi-cell log placement. Keep larger marker
billboards and one clear lock synchronized with their interaction state.

**Exploration and evidence plan:** profiles6–10 map to five new local options,
Black Sap Oak, Violet Strangler, Witchfire Weep, Amethyst Canker and Royal
Bruise. Profiles0–5 remain historical choices; the normal build stays0.
Native authored BG palette phases make attached purple veins actually pulse
in game, while shared OBJ/UI/glitter inks stay stable. Source sheets show all
states and adjacency assemblies. Real mGBA captures will show generated rooms,
isolated cases, under/overhang movement, taller landmarks, both wooden-chest
forms and actual barrier clearing. Clearly label diagnostic room fixtures and
distinguish them from natural generated placements. Test reachability and
physical footprints where generation changes; update the implementation notes
and remaining topology gaps as part of this ongoing process.

**Integration corrections before final evidence:** isolated water originally
carried healthy-green corner pixels even after its outline was rounded. Its
exterior now uses transparent ink and the renderer supplies the actual BG2
substrate below BG1 water; healthy grass, sick turf and dirt are checked
separately. Canopy uses the same real layer separation. A keyhole priority fix
keeps the single lock above its bars. Root spans require a complete walkable
north/under/south lane rather than merely two empty cells beneath the image.

Actual movement also exposed an overly deep north fringe: the rolled body
could vanish, and standing recovery feet were obscured by long flank leaves.
The final contour keeps a twelve-pixel shallow center (columns2–13, at most
two pixels deep) with longer outer tips. This changes foliage clearance,
not Bloom's sprite or physical position. Readability is verified at the real
collision limit rather than choosing a camera that conceals the problem.
Hardware telemetry records the displayed camera for precise pixel/occlusion
comparisons. Source diagrams identify BG2 floor, BG1 foreground and BG0 UI.

**Generator and sorting regression fixes:** the larger frozen host corpus
found later corridor/feature repairs overwriting one half of some log pairs.
A final v2-only pass removes orphan halves to local floor instead of rebuilding
obstacles across repaired routes. The targeted seeds and a6,000-room preflight
now pass; the final frozen corpus is rerun separately. A natural roll-wall
impact also has a brief airborne NORMAL recoil, distinct from rolling and
grounded walking. At low foliage only, body and held parts share a narrow
post-environment priority override during that lift; shadows retain ground
sorting. Ordinary rolls, walking, full crowns and root-arch roofs retain real
occlusion. A code review caught and fixed a second generic body-priority pass
overwriting the held-part decision. These are explicit coarse layer-sorting
and prefab-integrity rules, not changes to damage, physics or jump timing.

**Approach repairs found during final generation review:** paired old0/new6
inspection identified twelve sparse findings across ten seeds in both builds.
Four chest fronts were genuinely blocked; three entrance fronts could be
occupied by another chest; one mouth return/spawn could attach to a detached
component. Two gardener rooms contained only two/zero censers despite their
four-censer dialogue. A south-only NPC check was stronger than talk physics,
but its missing quest furniture was still a real task defect. Ordinary ledge
drops and already-owned tools did not explain the blocked chest fronts.

The new profiles now reserve existing landmarks and their interaction lanes.
Rare furniture fallbacks find an existing fronted site or open a small dry
recess attached to reached floor, using an already-solid center so placing the
object cannot cut its new connection. Mouth fallback routing connects directly
to the actual entry component while protecting its frame. Required-censer
shortages receive bounded connected space before retrying. All repairs happen
before optional item pockets; existing barriers, perimeter gates, water/cliffs,
meaningful overlays and earlier targets stay protected. A reconstruction
review also corrected the first water threshold's bridge axis. All ten named
stage traces pass; frozen corpus and emulator results are recorded separately.
Old profiles0–5 keep their previous bytes and behavior. The general rule that
an interaction owns its standing space is now explicit in the shared bible.

**Final second-pass evidence:** source `e5e3fcb21fe1bcc50c965943164146a2dc1e3c46`
is frozen in profiles 0,1,5 and 6–10. Production 0 and the two historical controls
remain byte-identical to their prior ROMs. Restored normal 0 still has SHA256
`9330a44a4e27d99606a757134aa41a62adb122a74315c400e1ad3427048c8661`.
The five new directions remain unselected. Renderer/generator changes are
conditional; Bloom/Step-and-cut, selected bestiary/Heart, equipment/pickups,
Drain architecture/keepers, interface layout/font/title and existing glitter
keep their art. Study environment objects and forest portraits are explicitly
redrawn, including shared chests/entrances/portable forms outside the forest.

The complete source catalogs contain 5,320 native frame instances and twenty
albums per option, including all 47 adjacency cases, four macroquadrants,
ten wooden chest constructions/states and fifteen named folk with native 48px
portraits. Independent export verification passes 47,515/47,515 checks.
All 10,950 PNG/GIF bytes match the held artwork checkpoint; C-only placement
repairs have fresh source provenance rather than relabelled old captures.
Palette/state inspection GIFs and fixed-foot source diagrams remain distinct
from engine timing, natural movement and physical passage.

Final actual evidence has 568 recorded contexts: 485 new-style contexts
(455 generated and 30 explicit diagnostic rooms) plus 83 production-control
contexts. Runtime checks pass 7,733/7,733, with 85 full-rate clips and 85 exact
sampled-palette GIFs. Each new style also earns the three trial rewards,
uses actual gates and enters the Heart through a 17/17 progression proof.
Navigation, health and attack-position fixtures are disclosed; enemy HP,
quest flags and rewards are not assigned. Those extra progression snapshots
are separate from the art-context count. All four new-style comparisons match
the reference new style's physical layouts, RNG, progress and mechanic states.

Independent native/static checks pass 121,211/121,211; combined native/runtime
audit passes 139,478/139,478. The one final frozen host corpus covers 20,000
seeds, 500,000 rooms and 60,000 tuned world graphs with zero failures, including
256,812 complete log pairs, 11,884 underpasses, 263,746 item pockets and
3,182,406 required approaches. Earlier failed or partial runs are archived
locally and excluded from final publication.

Forest graphics use 851–855/1,024 subtiles, ten/twelve world banks and 73
animation allocations. Interiors use 107 subtiles/six banks; the Drain remains
822 subtiles/one bank. The conservative OBJ union is 848/876, including four landmark slots.
Frozen linked memory is 216,284/262,144 EWRAM bytes and 21,900/32,256 IWRAM
bytes before the declared stack reservation. The connector scratch belongs to
IWRAM, correcting an earlier EWRAM label. Sampled runtime OAM peaks at 25/128;
this is recorded-case resource evidence, not a universal frame-time guarantee.

**Final critique and next work:** foreground leaves and the raised root arch
show real overlap during movement. The root span supports a lower route only;
a usable upper deck still needs explicit elevation/collision routing. Long
healthy crown bands repeat, and deep purple strokes/loops can read as a glowing
fence or rune pattern instead of branching wood. Rounded adjacency solves hard
corners but not broad composition. Future work should group larger forest
masses and vary their rhythm after selection. Sparse sick soil can look bare;
some unusual chests rely on their latch, and the friendly Moth Sister shares a
wing family with the enemy Confessor. These limits remain visible in the
[actual/source gallery](../../../art-review/forest-concepts-v2/README.md),
alongside [all five ROMs](../../../downloads/forest-concepts-v2-e5e3fcb/README.md).

## Lantern placement and hidden routes — 2026-10-31 (Pacific)

**Direct user direction, adopted design rule:** lanterns and other light
fixtures belong near pathways, water crossings or identifiable room features.
Do not scatter fixtures into empty grass without a lighting purpose. Content
can sit away from the dirt path; a chain of lanterns across grass can guide
players to a relic, healing cistern, NPC, entrance, chest or other feature.
Players should learn to notice and follow that second kind of trail. Preserve
more concealed discoveries with neither a dirt path nor lantern guidance.

**Scope and application:** the shared art bible now records three discovery
treatments: path-led, lantern-led without a road, and fully unmarked. The
forest topology notes carry the generation follow-up: choose a destination
and usable approach first, then place readable successive lights beside it.
Keep crossings, interaction fronts and item gates clear. Ambient surface
glitter retains its existing atmospheric role.

**Status and review:** this is a documentation-only change. Existing
`V_LANTERN` dressing and random canopy-light placement in `src/roomgen.c`
do not yet enforce the new rule; generator implementation and real-run
placement review remain pending. The frozen ROMs and captures are unchanged.
Reviewed against existing interaction-clearance, foreground-depth and
misleading-path rules; no new external reference is claimed. The future
placement pass should retain a mix of guided and unmarked discoveries so
lanterns help exploration without revealing every secret.

## Canopy recognition, living remnants and lateral boughs — 2026-11-01

**Direct user feedback:** grey discolored/dead grass is working and should
remain. Both healthy and blighted canopies are unrecognizable; black infected
blobs and repeated long vertical marks fail to communicate trees. Retain
greenery at every depth, with roughly an eighty/twenty disease/green split in
the deep canopy. Start from recognizable crowns and explore a wide range of
attached veins, patches, changed leaves, dithered spore light and other
infection treatments. Broad horizontal branches may overhang Bloom, but
canopy must never conceal him completely.

**Adopted requirements and exploratory scope:** the shared bible now records
grey-ground retention, clear crown/branch anatomy, visible living leaf groups
and continuous partial player visibility. Eight new canopy-only directions
are exploratory profiles11–18: Veinbound Oak, Patchblight Beech, Spore Drift,
Bracketwood, Violet Leaf Mosaic, Black Sap Bough, Silkbound Crown and Canker
Bloom. Other environment art uses second-pass Black Sap Oak as fixed context;
the existing forest alternatives and production default remain available.
The lantern placement note remains a separate pending generator change.

**Implementation/evidence plan:** author at native GBA sizes and RGB555 limits,
with a separate canopy infection bank so accepted soil and unrelated materials
retain their colors. Draw horizontal leafy volumes before infection. Compare
healthy/deep crowns, isolated cells, strips, concave joins and real overhang
movement. Preserve semantic collision, maze generation, Bloom artwork/action
timing, selected enemies, items, interfaces and glitter. A conditional renderer
safety layer may retain part of Bloom's current native silhouette while his
upper body remains behind branches. Its actual behavior and costs must be
verified in mGBA; source composites alone do not establish visibility. Existing
PDF guidance supports deliberate clusters and controlled lines; horizontal
tree emphasis is recorded as current user direction.

**Final canopy evidence:** game/art source `e923557aa74b01626f3e599f7c4b50366e096507`
is frozen in all nineteen profiles 0–18. Every previous profile 0–10 rebuilds
byte-identically. Production 0 remains SHA256
`9330a44a4e27d99606a757134aa41a62adb122a74315c400e1ad3427048c8661`.
All eight new styles keep accepted grey ground and other environment art at
previous profile 6. The generator, item rules, Bloom artwork/physics/action
timing, selected bestiary, equipment, UI, Drain and existing glitter remain
unchanged. The lantern-placement note remains pending.

Actual-room review rejected two intermediate constructions: flattened leaf
plates, then small closed crown quarters that still looked like masonry in
connected walls. Final art uses one larger 32px crown and short bark forks on
exposed lower edges, with dense underbrush backing rather than false walkable
holes. All 1,504 infected adjacency cases retain green leaves. Complete deep
source macros measure 20.61–20.80% declared living-green ink; this is a mass
composition measure, not a biological claim or per-tile quota.

The foreground safeguard copies a lower portion of the current native Bloom
frame only where canopy would cover it. It preserves directional tool order
and uses a dedicated upload packet without shrinking the normal queue. An
early runtime pose-analysis prototype caused missed gameplay updates; final
immutable metadata for 133 native body frames removes that work. A tiny
shrinking pose is protected in full without inventing new pixels. An attached
back-worn cape can cover body pixels naturally; the actual character proof
accepts only its exact native phase, palette, anchor and OAM composition.
Source-body visibility against canopy is checked separately.

Final mGBA evidence passes 3,477/3,477 checks across 198 contexts: 176 new-style
contexts (128 generated, 48 explicit diagnostics) and 22 previous-profile 6
controls. There are 63 full-rate clips and 63 exact sampled-color GIFs. Across
16,272 video observations, new styles have no fully canopy-hidden displayed
characters; measured minimum is 30 exact colored pixels/8 connected. Native
body-versus-canopy minimum is 37 colored/14 connected. The previous study has
46 fully hidden observations. Same-input positions, states, geometry, RNG and
recorded game/IRQ cadence match. One inherited menu redraw frame without hero
OAM is explicitly disclosed in every profile; it is not foliage occlusion.

Independent combined native/source/runtime verification passes 186,010/186,010.
The focused source catalog contains 3,952 frame instances (704 canonical,
3,248 canopy/fringe aliases), all 47 corner cases, four parities and eight exact
palette inspection GIFs. Actual comparison boards contain 360 literal native
panels. Source assemblies and inspection timing stay separate from naturally
generated mGBA contexts and deliberately inserted renderer diagnostics.

Forest BG usage is 814–824/1,024 subtiles and 11/12 world banks. The conservative
OBJ union is 864/876; the safeguard adds 16 tiles and at most one drawn OBJ.
Frozen linked memory is 216,820 EWRAM bytes and 21,928 IWRAM bytes. These are
resource measurements and recorded-case cadence checks, not a universal
performance or all-seed gameplay guarantee.

**Critique and selection status:** Veinbound Oak, Spore Drift and Canker Bloom
show the clearest distinct infection approaches at native scale. Patchblight,
Violet Leaf Mosaic and Black Sap Bough are quieter and closer; silk can read
as pale strapping. Tree cues are stronger on exposed edges and standalone
trees than inside dense connected masses, where 32px repetition remains.
Isolated fragments read as pieces of canopy rather than mature trees. The
[eight-way review](../../../art-review/forest-canopy-v3/README.md) and
[playable alternatives](../../../downloads/forest-canopy-v3-e923557/README.md)
retain these tradeoffs. No whole canopy treatment is selected by this pass.

## Rejected canopy studies and map-first composition reset — 2026-11-01

**Direct user decision:** the previous blighted canopy is a major regression
and must be scrapped. The user withdraws the repeating 3×3-block advice.
Uniformly sized repeated crowns are the wrong basis for large forest regions.
Generate the room, assess the available space, and choose native artwork that
suits it: small isolated growth, medium tree groups, or large intricate canopy
compositions along broad borders. Art detail and variety must scale with the
space. Ten genuinely different designs are requested.

**Adopted process and rejected art:** the fixed 32px canopy approach and its
eight treatments are historical rejected studies. Their technical passing
checks did not establish visual success. New work retains accepted grey grass,
legible floors/interactions and partial player visibility, while replacing
the tree/canopy artwork entirely. Hardware 8×8 subtiles remain storage units;
they do not impose a fixed illustration size or repeated3×3 motif.

**Exploration:** new optional profiles 19–28 investigate Ancient Oak Vault,
Crooked Willow, Buttress Beech, Woven Bower, Fungal Cathedral, Fallen Crown,
Lightning Cleft Oak, Pale Birch Congregation, Black Cedar Cathedral and Sorrow
Arch Elm. The visual planner measures actual components and clearance after
logical generation, then fits unequal 16/32/48/64/96px compositions near visible
inner boundaries. Nine separately authored native roles include a 96×64 focal
tree and 96×32 broad border; smaller roles are different drawings, not resized
copies. Existing standalone-tree physical footprints receive new native art.

**Evidence gate:** inspect a large tree within a real generated broad border
and inspect compact/narrow cases before approving all ten directions. A good
isolated source drawing cannot excuse a tiled or empty played view. Ensure
dense quiet backing, correct contact and readable walkable edges; preserve
feature clearances, existing maze/item logic, Bloom action timing, palettes
for unrelated assets and glitter. Measure resident GBA tile/bank budgets and
actual movement/cadence. Source assemblies, geometric fit diagrams and real
mGBA frames must retain separate labels. No final visual design is adopted by
this request; the lantern-generation note remains a separate pending change.

**Representative actual-room gate:** fresh natural profile 19 and 24 captures
show connected standing oak and fallen-log anatomy at native 240×160, with
small remnants and narrow arms using different-sized drawings. The first
contact pass still formed bright repeated underbrush waves and rectangular
panels; the second removes those waves, uses shallow unequal margins, and
corrects connector ground backing. A separate backed 64×16 limb serves thin
solid strips; its transparent counterpart remains the walkable projection.
Both five-geometry pilots pass 113 runtime checks. These pilots establish the
pipeline's direction, not final-source provenance or approval of all ten.

All ten source atlases preflight at 867–942/1,024 forest subtiles and 11/12
world banks. The representative visual review finds no blocker to freezing
the ten alternatives. Long edges and some tiny remnants still reveal the
semantic rectangular footprint; native semantic fit does not provide an
arbitrary pixel contour clip. Full frozen captures and independent review
follow. No candidate becomes the production default in this study.

**Compatibility and loading refinement:** adding an empty translation unit
changed GNU ld's ARM/Thumb division-veneer order in older builds despite
unchanged behavior. Profiles 0–18 now omit that file completely and all
nineteen prior ROMs compare byte-for-byte. The production default remains 0.

Direct mGBA timing exposed a separate one-time composition cost. Exact row
bitmasks replace repeated full-room prefix tables; cached floor-exposure masks
and a small IWRAM candidate-search path preserve placement order and score.
All five sampled complete BG1/BG2 maps, visual arrays, masks and native
placements remain byte-identical. The measured seed 6 / cell 4 transition
improves from 108 to 47 video/VBlank frames, about 1.81 to 0.79 seconds at
GBA timing. Prior profile 6 takes 28 frames, about 0.47 seconds. The remaining
19-frame / 0.32-second overhead is an explicit local tradeoff, not a claim of
identical entry performance or a worst-case bound.

Different loading durations also let unrelated enemies consume different
global random draws before recording fixtures clear them. The review tool
now declares one common action-RNG starting value after complete natural
generation, enemy clearing and standing settle. It records assignment/readback
and unchanged room/world/progress hashes, then retains strict initial/final
RNG and gameplay comparisons throughout ordinary inputs. This fixture does
not claim equal pre-capture AI histories. Failed pilot reports remain separate
from the fresh final recordings. No game/art RNG call is added by the planner.

**Completed ten-direction review:** game/art source
`c6dc060043aa6d0d5e2eb43d4d09e97ddf77450a` is frozen in profiles 0–28.
All nineteen historical 0–18 ROMs are byte-identical. The new source catalog
contains 140 native maps/tree groups, twenty recorded-plan source figures and
ten exact palette-inspection GIFs. Native, plan, layer-reconstruction and real
framebuffer evidence are explicitly distinct.

Fresh mGBA recordings pass 1,961/1,961 capture checks across 79 contexts and
3,248 frame observations: 71 new-style cases plus eight profile 6 controls.
There are 22 full-rate clips and 22 exact-palette GIFs; the ten-style gallery
contains twenty of each and eighty literal native panels. Recorded ordinary
movement has no missed update intervals. The minimum new displayed character
measure is 36 colored pixels / 14 connected; this finite sample is not a
universal silhouette guarantee. Existing lower-body protection remains.

The independent audit records 12,823/12,824 assertions, retaining one strict
absolute menu-cadence failure: the measured new menu handoff returns at tick
50 instead of 47, about 50ms later. Both retain the same three handoff intervals
without an update, and all recorded PLAY intervals advance once per IRQ. This
is an accepted, disclosed redraw-latency tradeoff for the exploratory builds,
alongside the entry-time difference above. The raw failed assertion remains
published; it is not converted into a passing check. All other native/scope,
palette, fit, actual visibility, physical, RNG and media assertions pass.

Final static use is 234,772 EWRAM bytes and 23,220 IWRAM bytes. Forest residency
is 867–942/1,024 subtiles and 11/12 world banks. These resource and finite-case
measurements do not establish every-seed performance.

**Visual judgment:** standing oak, buttress, fallen wood and split oak give
the clearest tree anatomy. Pale birch adds a distinct stand; fungi are busier,
cedar is sparse and can suggest parasol tiers, and the bowed elm can resemble
an angular arch. The ten share a material vocabulary rather than ten unrelated
rendering styles. Long contacts and some tiny fragments still reveal the
semantic rectangular footprint; the finite resident kit recurs across rooms.
No design is selected as production art.

The [ten-direction source/actual review](../../../art-review/forest-canopy-adaptive/README.md),
[explicit independent critique](../../../art-review/forest-canopy-adaptive/validation/INDEPENDENT_REVIEW.md)
and [playable builds](../../../downloads/forest-canopy-adaptive-c6dc060/README.md)
retain these caveats and exact source/build/file provenance.

## Emerald reference and foliage-first correction — 2026-11-01

**Direct feedback:** the ten adaptive trees still look bad and disconnected
from the background, with a featureless purple-black field behind them. The
user supplies an inline Pokémon Emerald tree crop as the new canopy reference.
This rejects the sparse branch-and-panel construction as the working art;
passing technical checks did not make that construction successful.

**Adopted design correction:** dense rounded leaf volume carries the tree
silhouette, supported by overlapping fan clusters, directional crown shading,
a hanging underskirt, short trunk and local ground shadow. Deep infection
changes material within that volume; surviving green and attached violet
wounds remain. Actual local floor must show through exterior alpha.

**Implementation in progress:** one focused original native study, profile
29, uses `art/forest_canopy_emerald.py` and its terrain wrapper. It retains
room-first fitting of differently sized art. Profile 29 clears transparent
BG1 prefab entries and removes the forced interior `MT_BLIGHT_WALL` BG2 fill;
unclaimed canopy cells receive dense leaf joins rather than a flat dark field.
Previous profiles 0–28 remain historical controls. Bloom, accepted grey ground,
non-canopy art, maze/collision/progression and glitter retain their contracts.

**Reference interpretation:** the provided crop is the direct visual source.
No additional website or inaccessible reference is claimed. This pass starts
with one coherent set for healthy through deep conditions; it does not create
ten more loosely related experiments before verifying the core tree read.
The first source sketch had a regular six-cap layout and fish-scale leaf rows;
source critique requires unequal overlapping crowns and quieter broken leaf
planes. The actual-room gate must check dense foliage and real ground contact,
not merely alpha coverage or source thumbnail attractiveness.

**Representative actual-room gate completed:** profile 29 now shows dense
rounded leaf crowns over real local grass and sick grass. The first real
render still cropped broad crowns at their canvas bounds; complete unequal
leaf skirts replace those rectangular cutoffs. A second engine correction
removes the old no-underlay `MT_PATH` fallback beneath canopy: valid stored
floor and real adjacent floor remain, otherwise stage-appropriate grass is
chosen with a stateless hash. Physical floor/collision data are untouched.

Five second-pass natural geometries pass 146 pilot checks; walking, rolling,
recoil, cape and menu probes pass 107 more. Hardware inspection checks every
prefab entry including transparent subtiles, and independently verifies every
canopy cell's actual native BG2 floor and its stored/neighbor/fallback rule.
Full floor evidence is retained once per case; repeated observations keep
counts and hashes. These pilots guide the freeze and are not final provenance.

The flat purple-black field and invented brown interior patches are removed.
Some short bands/joins retain the grid, the healthy fan texture is busy, and
the deepest gray/olive leaf masses can suggest mossy stone at a glance. The
focused study is suitable for a final native/runtime review with those caveats;
it is not a declaration that the user has selected the final game art.

**Final focused review:** source
`ead9bb68ca1cec93c8969dd813deda94c919af07` is frozen in all thirty profiles.
Every historical profile 0–28 rebuilds byte-identically. The new forest uses
986/1,024 BG subtiles and 11/12 world banks. The source catalog contains
fourteen native pieces: nine composition roles, a solid strip and four authored
tree groups, with healthy/deep pixels and exact source palette inspection.

Fresh matched profile 19/29 recordings pass 420/420 checks across sixteen
contexts and 800 actual frame observations, with four full-rate videos and
four exact-color GIFs. Independent verification passes 2,090/2,090, including
the actual stored/neighbor/grass-fallback rule and every BG1 entry, even blank
subtiles. Source material statistics alone are not used to claim the backing
is gone; native BG2 quarters, raw per-cell snapshots and real frames establish it.

Recorded new-character visibility has a minimum of 37 colored pixels and a
14-pixel connected component, with no missed ordinary gameplay updates. These
are finite cases. The measured entry is 45 video/IRQ frames versus 47 in the
prior adaptive control (about 0.75 versus 0.79 seconds). Menu world handoff is
one frame earlier, tick 49 versus 50; inherited opening and body-return gaps
remain disclosed. No universal performance claim follows.

The [focused actual/source gallery](../../../art-review/forest-canopy-emerald/README.md)
and [playable review ROM](../../../downloads/forest-canopy-emerald-ead9bb6/README.md)
show the corrected leafy volume and real grass contacts. The busy fan pattern,
some repeated/grid-aligned joins, and deep gray/olive foliage's occasional
mossy-stone reading remain visible. This is one coherent reference-led review
set; no final production canopy is selected.

## Compact repeated trees and the supplied field guide — 2026-11-01

**Direct request:** use `GBA_Sprite_Art_Guide.pdf` to begin the next forest
redesign with repeated trees and a few varieties. Make healthy, sick and dead
versions, blend them into the forest floor, iterate existing palettes, and
forget the canopy for now. The requested two-by-two and one-by-two sizes are
interpreted as 16px gameplay tiles: 32×32 and 16×32 pixels, as stated to the user.

**Guide application:** all fourteen pages were read, with teaching/game
figures inspected. Pages 5/12 support silhouette and a few connected masses
before texture; 6/10 support local contact, real-background checks and clean
alpha; 7 supports structural state cues beyond hue; 8 distinguishes visible
art, canvas and collision; 9 calls for tested depth/ground-contact sorting;
11 calls for an explicit native/palette/origin contract. The guide distinguishes
hardware facts from its proposed design ranges and selected-frame readings.
No underlying book or external linked tutorial is claimed as newly read.

**Exploration:** two varieties per footprint, each healthy/sick/dead, form a
twelve-piece native kit in `art/forest_tree_study.py`. One shared RGB555 bank
extends familiar greens, olive sickness, wood and localized violet infection.
Healthy full crowns become missing/drooping crowns with exposed wood, then
clearly bare broken forks. New large leaf lobes replace the first egg-like
prototype, keeping the earlier noisy fan pattern out of this study.

**Scope and evidence:** regular forest/canopy assets and procedural generation
stay unchanged. A compact separate review atlas and deliberately planted
in-ROM grove provide real mGBA context and ordinary Bloom movement without
silently fitting new small art to old larger colliders. These diagnostic
layouts are not presented as natural generated forest. The source kit and
actual scene evidence will be published separately after the native gate.

**Representative native/actual gate:** all twelve source pieces now have
readable compact tree forms and distinct healthy, damaged and bare silhouettes.
The native mGBA catalog shows their actual 32×32/16×32 scale beside Bloom.
The first scene test incorrectly initialized sprites after installing the
review atlas; an existing reset cleared the tree maps. That empty failed pilot
was rejected. Initialization now precedes installation, and the corrected
qualified eight-case pilot passes 104 checks across grass, path and sick grass,
with two ordinary walk-around clips. Raw BG maps, palette/atlas data, shallow
root footprints and current body/guard OAM bytes make the proof independently
inspectable. Ground-contact sorting uses the art's y=30 anchor.

The kit uses one shared sixteen-entry RGB555 bank. Its separate compact atlas
is 129 subtiles including the three actual floor materials; it replaces the
world atlas only during the explicit diagnostic scene. Normal forest/canopy
art, existing tree colliders and procedural placement remain unchanged. Final
review publication will provide the art pack and labelled grove captures; it
will not imply that normal game boot automatically enters this test scene.

**Final tree-only review:** source
`c269b67b9f0652902a5295906f4d0c4d07e2710c` is frozen in profiles 0–30.
Every historical 0–29 ROM compares byte-for-byte; normal forest/canopy, old
tree colliders and procedural placement remain unchanged. The source catalog
contains the twelve requested native state pieces, same-tree three-floor
previews, silhouettes/grayscale and a shared-bank palette iteration.

Fresh actual mGBA fixtures pass 104/104 capture checks across eight contexts
and 352 scanout observations. Six native catalogs/repeated groves show grass,
path and sick-ground contact; two ordinary walk-around clips test behind/front
ordering and the shallow diagnostic root footprint. Minimum visible Bloom is
43 exact colored pixels / 12 connected, with no missed ordinary update
intervals. Independent verification passes 599/599 for packed/source art,
normal-world protection, root/map/palette/body/guard proof and literal frames.
These are finite diagnostic layouts, not natural procedural forest rooms.

The [tree review](../../../art-review/forest-tree-study/README.md) and
[art pack](../../../downloads/forest-trees-c269b67/README.md) provide the
original 32×32/16×32 indexed PNGs, RGBA previews, raw 4bpp tiles, shared
32-byte RGB555 palette and explicit import/anchor contract. This is not a
player-ready ROM release; the retained test scene is opened by the developer
harness. GIFs use fixed inspection holds, while MP4s preserve full-rate GBA
playback. Dead narrow forms remain deliberately slender; dense future scene
composition needs another review. No canopy redesign or production placement
is adopted by this tree-only pass.


## 2026-11-01 — Adopt approved compact trees in procedural forest

**User selection:** “These are great. Go ahead and implement them and make
renders of the entire room using these.” The twelve drawings in
`art/forest_tree_study.py` are adopted without pixel or palette changes.
Profile31 becomes the normal forest build; profiles0–30 remain historical.
This supersedes the preceding tree-study-only production restriction.

**Implementation:** replace the retired large canopy and old authored tree
pictures with deterministic repeated broad32×32/narrow16×32 forms. Healthy,
sick and dead proportions follow room depth without consuming placement RNG.
BG2 keeps actual local grass/soil, BG1 carries upper crowns and BG3 carries
lower bases. Native transparency permits overlapping rows without black
backing or erasing another tree. Reserve screens12–15 for BG3 and cap the
forest atlas at768subtiles. Preserve maze barriers, optional item alcoves,
feature approaches and existing shallow free-standing root masks.

**Review plan:** actual mGBA complete-room camera mosaics for healthy, mixed
and deeply blighted natural rooms, untouched HUD-on views and ordinary input
walks. Camera/clock/HUD viewing fixtures and any enemy isolation are disclosed.
Mosaics register literal native frames; they are not single GBA framebuffers.
Packed/source fidelity, physical geometry, layering/menu restoration and
unrelated-art protection must be checked before publication. Remaining visual
risk is the apparent width of transparent dead-tree bases versus solid maze
cells; inspect real rooms rather than declaring this solved numerically.
