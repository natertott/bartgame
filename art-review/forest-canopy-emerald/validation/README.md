# Focused leaf-canopy verification

Game/art source: `ead9bb68ca1cec93c8969dd813deda94c919af07`. New profile 29 compared with a fresh byte-identical prior19 control.

- [Independent audit](final-audit.json) and [visual qualification](INDEPENDENT_REVIEW.md): **2,090/2,090**, zero failures. Direct native/packed pixels, nine prefabs, a solid branch and four authored tree groups, palettes, protected non-canopy art and all 29 historical ROM identities are checked.
- [Actual runtime aggregate](runtime-aggregate.json): **420/420**,16contexts, 800 frame observations,4MP4s and4exact-paletteGIFs. New 29 passes 232 checks; control 19 passes 188. Raw reports under [actual/profile-29](../actual/profile-29/capture.json) and [actual/profile-19](../actual/profile-19/capture.json) remain byte-identical to their producers.
- [Methodology](RUNTIME_REVIEW.md): seed/position/inventory/standing/action-RNG fixtures, ordinary recorded inputs, scanline-matched hardware/body/cape proof and native-layer checks. Every recorded profile 29 canopy cell is checked live; a full material snapshot is retained once per case, with complete hash/count stability at subsequent samples.
- [Legacy preservation](legacy-preservation.json), [build commands](builds.json), [frozen19/29metadata/maps/headers](frozen/) and [selection plan](selection-plan.json). The one playable new29 ROM is in the [download package](../../../downloads/forest-canopy-emerald-ead9bb6/README.md).
- [Source inventory/manifest](../source/source-manifest.json) and [literal native panels](../actual-panel-manifest.json) bind native source files and ten untouched framebuffer rectangles separately. BG1/BG2 full-room exports are explicitly layer reconstructions.

The material check independently recomputes actual stored-floor priority, south/north/east/west eligible neighbor priority, and the no-floor grass rule (moss variants from a stateless hash, or deep sick grass). Actual BG2 quarters must equal the chosen native floor; actual BG1 quarters must equal every native prefab entry including transparent zero tiles. Collision/world/physical hashes and RNG comparisons remain strict. No recorded action pose or generated terrain is painted into the room.

Recorded ordinary gameplay has no missed update intervals. New displayed Bloom minima are 37 exact colored pixels / 14 connected; these finite cases are not a guarantee of every action in every room. The existing exact native body/cape guard remains unchanged. [Menu handoff](menu-handoff.json) retains the inherited three opening intervals without an update and one world-return frame without body OAM in both profiles; new 29 returns at tick 49 versus 19 at 50. It is reported as latency, not asserted identical overall timing.

Fresh final-bundle [entry19](final-entry19.json) and [entry29](final-entry29.json) measure 47 vs 45 video/VBlank frames, two main-loop updates in each. At GBA 59.7275 Hz that is about 0.79 vs 0.75 seconds. Measurements apply to the disclosed seed 6 / cell 4 transition.

Forest residency is 986/1,024 subtiles and 11/12 world banks. The renderer uses the existing resident atlas and room-first planner; physical maze/event generation and non-canopy art remain. Remaining busy leaf texture, grid-aligned joins and gray deep-foliage ambiguity are documented visual tradeoffs. No design is selected by these checks.
