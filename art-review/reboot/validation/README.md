# Exact-ROM validation

ROM SHA256: `41dc680068c094416e92152d4c22637c10d6a055d2bee63ce7700c419490e92d`. Source: `202c75e8ffbfa6079d011a2848f5d9f6305ca9dc`.
All checks below were rerun against this frozen binary in mGBA 0.10.5.

| Check | Result | Evidence |
| --- | --- | --- |
| Native ownership, palettes and runtime presentation | 6577/6577 | [Report](native-ownership.json) |
| Phase-specific sword and interruption checks | 435/435 | [Report](sword-phases.json) |
| Broader Bloom action suite | 469/469 | [Report](bloom-suite.json) |
| OBJ allocation and menu cache sweep | 2046/2046 | [Report](sprite-budget.json) |
| Representative action/glitter performance | 29/29 | [Report](action-performance.json) |
| Generated room traversal | 625/625 | [Report](room-traversal.json) |
| mechanics | 22/22 | [Report](mechanics.log) |
| lift | 14/14 | [Report](lift.log) |
| critical | 21/21 | [Report](critical.log) |
| trials | 54/54 | [Report](trials.log) |
| myst | 28/28 | [Report](myst.log) |
| pockets | 18/18 | [Report](pockets.log) |
| quest | 12/12 | [Report](quest.log) |
| save | 6/6 | [Report](save.log) |
| Interface: title | 80/80 | [Report](../actual/interface/validation.json) |
| Interface: hud | 6/6 | [Report](../actual/interface/validation.json) |
| Interface: menu | 21/21 | [Report](../actual/interface/validation.json) |
| Interface: portraits | 6/6 | [Report](../actual/interface/validation.json) |
| Interface: hud_equivalence | 34/34 | [Report](../actual/interface/validation.json) |
| Interface: latency_normal | 20/20 | [Report](../actual/interface/validation.json) |
| Interface: latency_maximum_hearts | 20/20 | [Report](../actual/interface/validation.json) |

[Machine-readable release summary](summary.json) · [Build log](build.log) ·
[Complete native ownership](asset-coverage.json) ·
[Probe methods, fixtures and limits](../../../bartgame/docs/art-reboot/PROBE_NOTES.md).

HP 24 and maximum HP 80 contact tests each measure one video frame to replacement
hardware OAM in all 20 paired trials, equal to the frozen baseline. Independent
ten-trial repeats agree. HUD pixels match across 34 value/restoration cases.
Representative action performance sustains 192 updates / 192 VBlanks in each of four
isolated grounds; this is not a worst-case combat benchmark.

Capture PNGs/reports are unchanged copies. Text log trailing whitespace is
normalized for repository checks. Blank fills, simple glyphs and straight UI
primitives have explicit exceptions; 99 of 101 Bloom frames are actually selected.
