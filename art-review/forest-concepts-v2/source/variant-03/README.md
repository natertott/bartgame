# 3. Witchfire Weep: complete native source

Runtime selector: `BART_FOREST=8`. **SOURCE art, not emulator screenshots.**

Coverage: 920 BG IDs / 1034 BG phases, plus 30 OBJ frames. This includes all 457 new render topology pictures and the new wooden-B/landmark frames; original/protected context is explicitly retained.

[1×1/2×2/3×3 and concave assemblies](adjacency-islands-source.png) · [Layer explanations](foreground-layer-diagrams-source.png) · [Diagnostic physical-footprint overlays](physical-footprint-overlays-source.png) · [Standing/roll source-only clearance](standing-roll-clearance-source.png)

[All47 healthy canopy cases](all47-healthy-cases-source.png) · [All47 infected canopy cases](all47-blight-cases-source.png) · [All47 water cases](all47-water-cases-source.png)

[Authored palette-pulse source cycle](palette-pulse-source.gif). Only BG blight inks5/6/7/13/14 change; indices are fixed and holds are 180ms for inspection. This is not the actual game clock. Shared OBJ/UI/glitter colors are not pulsed. Base PNGs show palette phase0; the four ramps are in the manifest.

[Bitmap phase catalog](bitmap-motion-source.gif) · [Discrete interaction states](interaction-states-source.gif) · [All assembled groups](assembled-groups-source.png) · [Value/contour diagnostic](value-contour-diagnostics-source.png)

The floor under source islands is explicitly chosen grass/soil. It is not evidence of an automatically inferred generated underlay. Transparent visual corners retain their semantic collider. Parity swatches are separate samples; a physical island uses a different adjacency mask for each cell. The engine world layers are BG2 ground and BG1 foreground around depth-sorted OBJ actors; HUD BG0 stays above.

Canonical original canopy pictures and their allocated phases remain in this complete catalog. In the new forest renderer their semantic IDs select the new adjacency/parity aliases; the canonical bitmap alone is not a claim of the exact live picture at every position. Render routes are recorded per original ID. The pulse preview uses a live canopy alias and fixed source indices.

| Complete category | Native1× + integer3× atlas |
| --- | --- |
| floor_and_overlay_details | [PNG](atlases/floor_and_overlay_details-source.png) |
| ground_and_growing_details | [PNG](atlases/ground_and_growing_details-source.png) |
| hazardous_pool | [PNG](atlases/hazardous_pool-source.png) |
| interactive_scenery | [PNG](atlases/interactive_scenery-source.png) |
| interior_cave | [PNG](atlases/interior_cave-source.png) |
| interior_hollow | [PNG](atlases/interior_hollow-source.png) |
| interior_shared | [PNG](atlases/interior_shared-source.png) |
| interior_thicket | [PNG](atlases/interior_thicket-source.png) |
| obj-face | [PNG](atlases/obj-face-source.png) |
| obj-forestlandmark | [PNG](atlases/obj-forestlandmark-source.png) |
| obj-interactivechest | [PNG](atlases/obj-interactivechest-source.png) |
| obj-interactiveentry | [PNG](atlases/obj-interactiveentry-source.png) |
| obj-lift | [PNG](atlases/obj-lift-source.png) |
| obj-npc | [PNG](atlases/obj-npc-source.png) |
| solid_scenery | [PNG](atlases/solid_scenery-source.png) |
| terrain_transitions | [PNG](atlases/terrain_transitions-source.png) |
| topology_canopy_blight | [PNG](atlases/topology_canopy_blight-source.png) |
| topology_canopy_healthy | [PNG](atlases/topology_canopy_healthy-source.png) |
| trees_and_canopy | [PNG](atlases/trees_and_canopy-source.png) |
| water_crossings_and_elevation | [PNG](atlases/water_crossings_and_elevation-source.png) |

[All native files, IDs, banks, physical metadata and exact hashes](source-manifest.json). Retained legacy tree/root IDs and static allocated phases are kept honestly in the catalog; coverage does not imply every old ID is a unique species or every allocated phase visibly animates.
