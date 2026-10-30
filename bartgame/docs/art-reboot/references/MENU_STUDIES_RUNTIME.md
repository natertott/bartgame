# Native interactive menu studies

`BART_MENU=0` is the production renderer and remains the default. `BART_MENU=1..10` selects ten optional native prototypes independently of `BART_UI=0..10`. The user has not selected a production replacement.

The source schema is `src/menu_studies.h`, recipe registry `src/menu_studies.c`, recipes `src/menu_layouts_a.c` (1–5) / `src/menu_layouts_b.c` (6–10), and optional renderer in `src/menu.c` guarded by `#if BART_MENU_VARIANT`.

All rendering starts at 240×160, RGB555, native 4bpp tiles. 32px art uses existing native menu illustrations; 16px art uses separately authored HUD drawings. Both keep their source material palettes. This is not an image downscale or high-resolution mock-up. A full tile bitmap lets each layout move text and frames freely while preserving original runtime icon sheets.

Controls: Start opens/closes; R cycles Items → Key Items → Map; D-pad selects an owned tool / browses the 5×5 map; A/B/L assign the selected tool through canonical `player_equip_set`; A zooms map, B returns overview. Only one button can hold a particular tool, as in the existing game. Tool and key focus persist separately across tabs; map cell and zoom persist across tabs. Toolwheel nodes remain in fixed canonical slots; unknown tools remain empty and cannot be selected/equipped. Other lists compact carried items.

Every inventory count, equipment state, room name, visited state, door/task/Folk/chest/relic/Heart hint, and map geometry comes from live game state. Map ownership and Astrolabe are distinct: Map charts room geometry; Astrolabe permits extra treasure/boss/barrier knowledge. Unknown cells never fetch terrain. Ordinary Folk do not receive Task labels; known connections without Astrolabe use neutral lines. Route diagrams underline visited rooms, without claiming a shortest or safe route. No new progression, combat, storage, or quantity mechanics are invented.

Native maps keep north up. Terrain overview and chamber zoom preserve geometry aspect; topological diagrams use their own rectangular grids. Twin Atlas keeps overview and selected chamber visible at once, then expands detail with A. A known-region/unknown-room fixture verifies fog guard behavior.

The pause renderer saves 32KB world character memory and the HUD icon allocation, pauses live tile animation, and restores the world and current legal animation frames on close. Secondary 16px equipment art uses spare palette banks rather than exhausting the seven-entry 32px icon cache. HUD and gameplay draw routines are unchanged by the layout selector.

Performance: cached native tile-row/mask compositing, glyph rows, page headings and overview pictures avoid full per-pixel reconstruction on each cursor step. A pause-only VBlank input queue retains quick taps during cold terrain-map generation and restores the previous VBlank hook on close. Actual pilot measurements: item focus/assignment and warm map cursor redraw ~2 video IRQ frames; chamber zoom ~4; the first full 25-room terrain chart ~52 (~0.87s). Graph/route maps do not generate terrain previews. Those measurements are not a claim of instant map generation.

Read-only presentation symbols: `gMenuStudyPage`, `gMenuStudyCursor`, `gMenuStudyMapCell`, `gMenuStudyZoom`, `gMenuStudyDrawFrames`. They report actual runtime state and are not drawing fixtures. Review tools never write them.

Door, chest, relic and gate markers use distinct [] / o / R / G symbols and an eight-row legend. Compact info panes prioritize that complete legend over a redundant aggregate Seen line. The wide16px strips in Twin Atlas6 and Quick Ribbon10 fit all eight compact marker labels (216 native pixels); their room/orientation labels move to the free y24 row. Twin Atlas overview labels Region and Chamber explicitly. Full-screen Twin chamber zoom returns to the overview/context legend with B.

Runtime reviews: 47/47 native mGBA checks passed for Workbench and all ten pilot layouts passed 550/550 checks, including standard two-frame taps, focus persistence, empty inventory, fogged overview/zoom, world/room/RNG invariance, static world VRAM, legal animated allocations, and world palettes after close. Final source freeze: src/menu.c SHA256 57ef53485442f2ba47b84020f616f4b0ac449fe66a794014fabb013225e35001.

Final all-ten native capture/audit is handled by `tools/ui_layout_review.py` and the review agent; source wording/header fixes after the first pilot must be included in the final freeze.

Final narrow QA corrections: wide40–48px title cards retain seed/arrow quantities on the same title line (real30/50 verified in `final-ammo/barrier-seeds.png` / `barrier-arrows.png`). Quick Ribbon overview/chamber both start y32, leaving the y24 orientation/room caption visible; final recipe SHA256 f575ca99eecc7880a5ffb1547c1a45903e1cac02463b2a6221680b983a8bc199. Root owns final immutable build/capture provenance; mutable pilot folders are diagnostic only.

## Final committed review

Source d113d39 produced sixteen immutable ROMs and312 actual mGBA cases.
The final controller suite passes1,166/1,166 checks, including 59 per layout
(590 total for the ten new arrangements). This supersedes the narrower pilot
result above. The separate native/source audit passes7,523/7,523 checks.
All 22 baseline selected framebuffers match the previous final Drain release.

Every 114 code/art input per build matches the freeze (1,824 hash comparisons).
All sixteen explicit `make -q` queries and the normal default query return0.
Default ROM SHA256 is 6d5d1ffe05653255da08f2077328c1a1f5c778d8d80a147a873459a6e228a141
and matches the restored frozen v0 exactly. Maximum linked study EWRAM use
is 201,688/262,144 bytes, leaving 60,456; IWRAM linker end 20,292/32,512 leaves
12,220 below its limit. These are linked allocations, not measured stack peaks.

Final terrain chart draw counters are 52–54 IRQ frames, with end-to-end page
transitions 53–55. Schematic cold draws are 5–6; Twin 9. Cached map moves take 2
except Twin 6; zoom 4–7. The bounded ordered input queue has 31 usable events;
the normal two-frame-tap sequences pass, but arbitrarily large bursts during
a cold draw are not an unbounded input guarantee. Existing hooks are restored
when the menu closes. Default MENU0 does not allocate this renderer/queue path.

[Published native evidence and download choices](../../../../art-review/ui-menu-exploration/README.md)
include exact clips, per-capture traces, timing table and independent UX critique.
The four final focus checks were added in review-only tooling after the game
freeze; the publication commit retains that exact checker. No game input or
art input changed after the ROM source commit.
