# Repeated-tree study validation

Game/art source: `c269b67b9f0652902a5295906f4d0c4d07e2710c`. The current task is trees only; normal canopy/procedural forest and existing colliders remain unchanged.

- [Independent audit](final-audit.json) and [visual qualification](INDEPENDENT_REVIEW.md): **599/599**, zero failures. Twelve direct native frames/shared palette/anchors, compact atlas/flip maps, actual floor quarters, source catalog and regular forest/canopy/OBJ/UI data are checked. All historical profiles 0–29 compare byte-identically.
- [Raw final capture](../actual/capture.json): **104/104**, eight contexts, 352 actual scanout observations. Six catalogs/repeated groves on grass/path/sick grass, plus two ordinary walk-around clips. The report is byte-identical to its producer.
- [Source catalog](../source/source-manifest.json): twelve native indexed/RGBA frames and 32 hash-bound source files, including same-tree floor/value and palette iteration diagnostics.
- [Literal actual panels](../actual-panel-manifest.json): six untouched 240×160 framebuffer rectangles; source drawings and diagnostics are separate.
- [Legacy identities](legacy-preservation.json), [builds](builds.json) and [frozen metadata/maps/headers](frozen/). Profile 30 regular forest/canopy data is inherited unchanged from 29; its review atlas is separate.

The new native frames use a single sixteen-entry RGB555 bank at world slot 11, transparent index 0, fixed root anchor [width/2,30]. They are 32×32 or 16×32 canvases, with separately declared shallow 16×8 diagnostic root footprints. Visible bounds/canvas are not game colliders. The dedicated atlas is 129 8×8 subtiles (4,128 bytes), instead of adding 144 raw tree subtiles to the full normal forest atlas.

The in-ROM function installs actual moss/path/sick-floor pixels and native tree maps. The harness selects a diagnostic fixture at a stable callback and then uses ordinary game inputs. It never injects tree pictures or recorded action poses. Full BG1/BG2 entry maps, palette/atlas snapshots, placement/root records and raw native body/guard OAM/palette/bytes permit independent reconstruction. The first empty-tree development render was rejected and is not published as final evidence.

Independent checks reconstruct the 12 placement records, all 600 BG1/BG2 quarters, root grid, alpha-ground composition and visible tree/native body pixels in captured frames. Recorded behind/front priorities, guard contents, unobstructed placement and collision pushes pass. New Bloom minima are 43 exact colored pixels / 12 connected, with no zero-update intervals in the recorded ordinary walking clips. These finite fixtures are not a universal gameplay or player-recognition study.

Two MP4s preserve full GBA playback. Two GIFs use exact sampled colors and fixed 130ms inspection holds every eight frames, explicitly not full-rate playback. Native PNGs and filmstrips preserve exact captured RGB; the grayscale/silhouette source figures are labelled transformations for inspection.

The ZIP provides indexed and RGBA PNGs, raw 4bpp tiles, one 32-byte RGB555 palette and an explicit JSON import contract. It is an art pack, not a playable ROM or an adoption of new procedural tree placement.
