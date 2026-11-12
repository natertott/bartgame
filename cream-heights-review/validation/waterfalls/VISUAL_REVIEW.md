# Final Cream12 waterfall native review

Source `f4b917f7964941d488c4d20fce073f3f58b950bc`; ROM SHA256
`a2e98b9551213c5335e826c59642fea5c03a4998746a811d5a9d464a96e24f86`.
Actual mGBA 0.10.5 recordings, not source animations or game mockups.

The normal title-seed fixture 0 produces actual one-, two-, and three-tile falls in cells 6, 10, and 24. The room/map survey seed 0xb4a7 does not contain a one-wide fall under its dynamic topology, so these water-specific captures use seed 0. No terrain, waterfall width, gate, inventory, health, action result, camera, clock, VRAM, or framebuffer is assigned. The inherited ordinary-load/navigation fixture selects living supported positions.

Each clip advances 96 actual simulation frames, with HP staying at 32. Every one of the 24 captured frame samples per case shows the full fall width and sufficient blue body. Twelve raw native BG2 body samples per case cycle through exactly four distinct phase hashes. The width-three GIF encodes 22 frames because its encoder merges identical adjacent sampled images; its input still contains all 24 unmodified sampled frames.

I inspected the final four-phase contact sheet, composed from unmodified ordinary 240×160 emulator frames for all three widths. The world, Bloom, enemies, and normal HUD advance during recording. Whitewater Ribbons reads as blue liquid, with falling bright threads, compact foam, and no interior black seams between waterfall tiles.

The one-wide spring and two-wide sheet show their full width and moving body, while their tall crowns extend partly above the ordinary viewport. The three-wide fall is fully visible and is the strongest standalone clip: `width-3/flow.gif`. Registered full-room mosaics show the complete taller compositions and are separately labelled rather than presented as ordinary gameplay footage.

A regular ribbon cadence and compact dry-floor contact remain deliberate native-art choices. These captures establish actual generated placement, moving water, and a living visible hero for these examples; they do not establish every possible seed’s hydraulic composition.

## Results

| Width | Cell | Simulated frames | Minimum HP | Native flow phases | Captured samples | GIF frames |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 6 | 96 | 32 | 4 | 24 | 24 |
| 2 | 10 | 96 | 32 | 4 | 24 | 24 |
| 3 | 24 | 96 | 32 | 4 | 24 | 22 |
