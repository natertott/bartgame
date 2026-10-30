# Independent menu-study usability review

Reviewed final immutable source d113d39 and actual native mGBA captures.
Outcome: no blocking text overlap, missing identity, false knowledge marker or
incorrect control hint remains in the examined states. This review selects no
final visual style; the user should compare the working alternatives.

## Evidence and scope

- Inspected all ten native item layouts individually; ten-layout key-item,
  overview, zoom, fog and seed boards; individual wheel/bow and narrow-card
  states; Workbench navigation chronology; and the final changed4/6/9/10
  screenshots. Each game framebuffer is240×160, with board labels outside it.
- Final targeted files: `captures/v9/layout-{seeds,bow}.png`,
  `captures/v11/layout-{key-items,seeds,map,zoom-map}.png`,
  `captures/v14/layout-{seeds,bow}.png`, and
  `captures/v15/layout-{map,zoom-map}.png`.
- The separate controller/capture owner reports1166/1166 checks over312
  actual cases across the16-ROM comparison. That is suite evidence, not a
  claim that I individually watched every frame in all312 cases.
- Real bindings: A/B/L equip on Items; Start closes; R changes page; B returns
  from map zoom. Key pages do not advertise equipping. Actual stock2-frame
  taps are used; page changes send one R and wait for drawing completion.
- Research basis: pinned primary sources in GBA_MENU_RESEARCH.md. Inaccessible
  external reviews were not read or quoted; no review scores are invented.

## Recommended comparison shortlist

Compare1 Loadout Workbench for visible equipment relationships,6 Twin Atlas
for navigating the procedural maze, and8 Focus Cards for learning what a tool
does. Add5 Toolwheel if spatial item switching is a priority to test by hand.
These cover different player tasks; this is not a palette or style ranking.

## Ten distinct alternatives

| ID / layout | Useful distinction observed | Tradeoff to judge |
| --- | --- | --- |
|1 Loadout Workbench | Large pack icons plus persistent A/B/L strip make assignments direct. | Narrow right card favors short functional help. |
|2 Pocket Ledger | Readable action list, quantities and full key names in stable rows. | Up to6 navigation presses; selected card supplies identity for action labels. |
|3 Fieldbook | Compact pack leaves a generous stable prose region. | Small unlabelled icons favor familiar tools. |
|4 Tactical Atlas | Tool selection, known-route graph and loadout remain simultaneous. |16px choices are small; short help carries less detail than full cards. |
|5 Toolwheel | Large fixed tool positions, icon counts and complete center help. | D-pad movement around a wheel needs learning; it is not an analog radial selector. |
|6 Twin Atlas | Region context stays visible beside the selected chamber. | Each simultaneous map shrinks; fullscreen chamber zoom temporarily gives space to terrain rather than its legend. |
|7 Expedition Dashboard | Gilt, keys, seen% and loadout remain visible together. | Resources reduce description width; seen% is exploration, not required victory progress. |
|8 Focus Cards | Large selected illustration and generous prose explain function/resource cost. | Nearby rail icons are16px; sequential navigation takes up to6 presses. |
|9 Barrier Index | Cut/Guard/Blast/Burn/Leap/Shoot/Return directly recall tool roles. | Several key names ellipsize; selected name/help remains complete. |
|10 Quick Ribbon | All large items and relevant quantities are visible in one row. | Simple sequence takes up to6 presses; it is not automatically faster than a grid. |

## Corrections confirmed in final pixels

- Ordinary maps fit their vertical legend. Task, Folk, Heart and Gate are
  distinct; an edge barrier is no longer labeled only as Chest.
- Twin/Quick maps show a complete compact eight-glyph legend. Region/Chamber
  and selected-room captions provide orientation. No final legend cutoff seen.
- Key pages use actual names rather than repeated Keep labels.
- Toolwheel bomb/bow help and Twin counted-key/seed help end in complete
  statements. Counts remain visible in the icon/list or selected header.
- Atlas4 and Barrier9 now show30 seeds/50 arrows inline without adding height.
- Fog views disclose only known terrain; unknown chamber zoom says Not
  charted. Overview selection and player position remain separate concepts.

## Remaining imperfections and limits

- Some16px menu icons and Barrier Index key abbreviations need selection to
  identify confidently. This is a real density tradeoff, not a scale defect
  to hide by enlarging the review images.
- Terrain overviews are dense. Graph views explain connections more clearly;
  zoom explains local floor/bank/wall geometry. No one view does both equally.
- Short cards omit flavor and some detail. Their complete minimal statements
  are useful, while Focus Cards/Fieldbook support fuller reading.
- Zoom accepts D-pad room browsing but its footer does not advertise it; a
  selected design can improve that hint in a later iteration.
- Measured Workbench first full terrain chart costs52 IRQ frames (about0.9s),
  while cached map-cursor redraw is2 and chamber zoom4. A fresh one-room fog
  map is a separate case, not a warm full-map benchmark.

## Navigation proof versus real controls

Source-derived weighted-direction graph calculation finds all seven tools
reachable from every starting tool. Grids1/3/7/9 and wheel5 need at most3
presses; lists2/4/6 and ribbons8/10 at most6. Fixed wheel positions remain
connected for all127 nonempty ownership subsets (448 starting states).
This is a source proof of connectivity, not a timed user test or an emulator
check of every sparse subset. Real all-owned reachability, equipment assignment,
independent page focus, selected-room persistence, fog privacy and world/VRAM/
RNG preservation are separately exercised by the final controller suite.

Historical review/fix notes: `research/ux-review-history.md`.
Source navigation audit: `research/navigation-audit.json` (hashes captured
before final wording-only changes; navigation coordinates/algorithm unchanged).
