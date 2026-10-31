# Actual native appearance review

All56 images are unchanged240×160 mGBA framebuffers from frozen source
`5eedc6dae94d8c1ea21c55b8668435bcf0be884d`, productionvariant0.
Board labels are outside each native screen. No image is recolored or filtered.

- [Nine Options combinations](nine-options.png)
- [Nine selected Workbench combinations](nine-items.png)
- [Nine named-wizard dialogue combinations](nine-dialogue.png)
- [Nine market combinations](nine-shop.png)
- [Fixed Winebound HUD across all nine](nine-hud.png)
- [Title without a run save](title-no-save.png)
- [Title with a real death-created save](title-with-save.png)

The shape/color selectors are driven with ordinary two-frame button taps.
Actual reset, New Game and Continue retain the choice. Fixtures are initial
blank/corrupt SRAM, seed, inventory, resources and safe NPC positions; no
preference variable, menu focus, canvas, palette or pose is assigned.

All280/280 runtime checks pass. The separate legacy-save regression passes6/6.
The native kit/pointer encodings, actual menu corner, pointer colors after
closing inventory, identical fixed HUD/minimap, preference checksum fallback
and separate run/preferences storage are checked. The recorded death/save
compatibility fixture explicitly uses save_probe's normal save-path fixture.
This is behavior/encoding evidence, not an aesthetic score.

All nine final Options/items/dialogue/shop boards were personally inspected
at native size. No clipping or contrast blocker was observed in those states.
These are final committed-ROM captures, not mutable pilot evidence.

[Detailed checks and ROM provenance](appearance-review.json) ·
[Legacy save checks](legacy-save-review.json) · [Save log](legacy-save-review.log).
