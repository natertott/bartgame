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
