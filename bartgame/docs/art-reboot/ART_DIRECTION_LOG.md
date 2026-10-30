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
