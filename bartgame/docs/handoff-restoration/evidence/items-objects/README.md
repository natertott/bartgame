# Final native item and object review

All95checks pass on the exact release3 ROM:

- Source: `0b9344d781e65e304d245bd9ae4aecdbc7056837`
- ROM SHA256: `b348cf4d628aee1abb9b71d8885a9f04094332c5252490ff2dd8f8e7cd0bf1b8`

| Suite | Passed | Evidence |
|---|---:|---|
| Item controls and real effects |19|[Report](items/report.json)|
| Four courts, views and streamed OBJ pixels |48|[Report](objects/report.json)|
| Minish gap, clones, pressure gate and sword |8|[Report](forms/report.json)|
| Live mechanisms and tool forwarding |20|[Report](mechanisms/report.json)|

The PNGs are untouched240×160 mGBA framebuffers from actual runs. Inventory,
ammunition, bottle contents and navigation positions are disclosed fixtures
in each report. Tests never assign player HP, enemy HP/AI, action states,
clocks, room geometry, completion flags, palettes, VRAM or framebuffer pixels.
The object suite reads OBJ VRAM and compares it to the exact linked ROM art;
it also waits for the game's real camera easing after navigation.

Useful views:

- [Three copies, same sword phase](forms/clone-sword-same-phase.png)
- [Three real pressure plates](forms/clone-pressure-plates.png)
- [Inside the enclosed Minish pocket](forms/inside-minish-pocket.png)
- [Mirror Shield reflects the light ray](mechanisms/mirror-reflected-ray.png)
- [Mineral water melts the large ice block](mechanisms/mineral-water-melt.png)
- [Pacci flips the pot](mechanisms/pacci-flipped-pot.png)
- [Original Bow activates an eye switch](mechanisms/bow-eye-switch.png)
- [Completed mechanism court](mechanisms/completed-court.png)

Reproduce with the corresponding `tools/handoff_*_native.py` script, passing
`--bundle` (ROM, ELF, map, assets.h) and a separate `--out` directory. The
[manifest](manifest.json) records each artifact's exact SHA256. Host-only
simulation checks are separate: [259bomb checks](host/bomb-259.json) and
[277mechanism checks](host/objects-277.json). They
provide logic evidence, not additional emulator captures.
