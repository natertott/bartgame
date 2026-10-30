# Independent menu-study UX review

Status: first Workbench pilot pixels inspected; full ten-layout capture review pending.
Research basis: pinned primary GBA source findings in GBA_MENU_RESEARCH.md.
This is a usability critique, not a taste score or production-style vote.

## Control semantics verified before viewing

The actual current BARTGAME inventory assigns A/B/L directly. Start closes;
R changes page. B returns from map zoom to overview, not from every menu.
An initial research adaptation incorrectly called B a global Back binding;
that statement was corrected after inspecting menu_update(), and all layout
/runtime agents were notified. Layout 1–5 planning notes already had the right
bindings. Actual captures must verify discoverable context-sensitive hints.

## Review checklist

- Every native word, number and selection is legible without integer zoom.
- Selected/unselected states remain distinct with a stable description target.
- Every item is reachable with predictable D-pad movement; graph navigation
  works for nonrectangular layouts without requiring diagonal input.
- A/B/L assignment reflects immediately in shown loadout, and Start/R/B are
  advertised only for their actual context.
- Page focus and selected overview room persist when changing page/zoom.
- Current-player and menu-selected room markers are distinguishable.
- Map/visited/Astrolabe knowledge stays truthful; no unknown gates, loot or
  arbitrary completion percentages appear for decorative usefulness.
- Descriptions match real capabilities, especially Drain Cap=return home.
- Content stays inside its panel and never overlaps other icons or footer.
- Each of ten studies supports a distinct player task rather than just moving
  the same boxes, and its navigation/readability tradeoff is recorded.
- Skin styles remain independent of layout so the comparison stays fair.

Actual source/ROM captures will be appended below when available.

## First actual pilot, before input-settling fix

Viewed native mGBA pixels:
- `review-skin-pilot/menu-items.png`, `menu-map-zoom.png`: baseline
  skin6 item names/descriptions, slot letters and zoom legend remain legible.
- `review-layout-pilot-1/layout-items.png`, `layout-key-items.png`: Workbench
  fits seven icons, stable A/B/L loadout, status, names and wrapped prose.
  Counts remain inside item frames; the key page correctly omits equip hints.
  No panel or footer collision observed in these two actual states.

The first controller suite caught a missed B assignment and failure to settle
onto the map page with short input pulses. This is a functional usability
blocker even though still images look readable. The runtime/review owners
are profiling renderer cost and input timing; approval waits for a passing
ordinary-controls run and actual overview/zoom pixels.

Source-level review fixes present in the current renderer (pixel confirmation
pending): ordinary NPCs now use F/Folk rather than !/Task, the Heart has its
own H marker, graph open/closed link color is gated by Astrolabe ownership,
and the wheel retains source-index item positions when tools are unowned.

## Additional source risks queued for actual-pixel confirmation

- Purpose/verb labels must apply to usable tools only. On key-item pages all
  items have EQ_NONE, so the shared fallback would label every key as Keep.
  Runtime owner notified to use the actual distinct key names instead.
- Review input script originally used Right for every layout. Layouts2/4/6
  are vertical lists; Down is their legitimate movement. Review owner notified
  so a correct one-column list is not marked broken by the wrong test.
- The Wheel's 72×40 detail center plus an ammo line can leave too few rows for
  a complete use description. Requested real bomb/bow-focused frames before
  judging; no claimed visual failure yet.

## Source-derived navigation cost (not a controller pass)

Recomputed the current weighted D-pad neighbor algorithm against each recipe's
native coordinates. All seven owned tools are reachable from every other tool.
The workbench, fieldbook, dashboard and barrier grid require at most3 presses;
the wheel also at most3. Vertical ledgers and one-row ribbons require at most6.
That is an explicit tradeoff: small grids reduce travel while rows/ledgers
provide a simpler sequence. Do not call a ribbon automatically faster.

The fixed-position wheel stays connected for all127 nonempty ownership subsets
(448 possible starting item states). This is a source calculation, not evidence
that short real button presses are accepted; emulator controls still must pass.
Calculation details: `research/navigation-audit.json` (all-owned adjacency).

## Workbench fast2: actual overview, zoom and fog

Viewed `review-layout-pilot-1-fast2/layout-map.png`, `layout-zoom-map.png`,
`layout-fog-map.png`, `layout-fog-zoom.png` at native size. The overview keeps
all25 cells in stable orientation; terrain is deliberately dense at that
scale. Chamber zoom is easier to read, follows the selected cell, and keeps
the same overview focus on return. The no-Map fixture shows one explored cell;
the selected unknown neighbor says Not charted and discloses no terrain.

Confirmed defect: the narrow legend was ellipsized to + You ! Task .., hiding
Folk/Heart meaning. Runtime owner reports latest source already replaces this
with bounded wrapping. Final pixels must confirm that wording fix.

The review owner reports47/47 checks over13 cases with stock2-frame A/B/L and
D-pad taps. Page transitions now issue one R and poll completion rather than
queuing repeated R during a cold map redraw. The final profiling correction reports full cold chart52 IRQ frames,
cached map-cursor2, item focus2 and chamber zoom4. The earlier11-frame
shorthand referred to a fresh fog map with one known room, not a warm
full-chart update. These are distinct cases. Cold chart latency remains
acknowledged separately from accepted2-frame input taps.

Runtime owner also reports current source uses real key names on key pages,
complete short Toolwheel help and omits redundant selected-card count there.
These fixes await the final ten-layout pixels.

Viewed the Workbench navigation chronology filmstrip (16 actual frames):
selection and description change together; no stale text or tearing observed.
The subsequent cached pilot passes47/47 again. Its legend pixels still predate
the final wording-only rebuild; do not count that as fix verification yet.

## All ten pilots: native pixel review

Viewed every native item layout individually, the ten key-item/overview/zoom/
fog/seed boards, and individual critical wheel/bow and narrow-card states.
The boards preserve each actual240×160 framebuffer; added labels sit outside
those frames. These are real mGBA captures, not source-rendered mockups.
The review owner reports550/550 functional checks over150 captures, including
all-owned D-pad reachability, real A/B/L assignment, page focus, overview/zoom,
fog privacy and world/VRAM/RNG restoration. That numerical result belongs to
the independent controller suite; the observations below are pixel inspection.

| Study | Observed useful distinction | Honest tradeoff / limitation |
| --- | --- | --- |
|1 Loadout Workbench | Large pack icons and stable A/B/L strip make comparison direct. | Right detail card is narrow and uses compact functional help. |
|2 Pocket Ledger | Vertical actions, ammo and actual key names are readable together. | Up/Down sequence takes up to6 presses; the selected card supplies full identity for action labels. |
|3 Fieldbook | Small pack plus generous right prose region gives a clear reading target. | Tiny unlabelled choices favor familiar tools; details identify the selected one. |
|4 Tactical Atlas | Tool choice, true known-route diagram and loadout stay simultaneous. | Small icons; this pilot omits menu ammo count in its short card (HUD still shows equipped ammo). |
|5 Toolwheel | Fixed large tool positions, icon ammo and complete short center help. | Nonrectangular D-pad choices need learning; max3 presses but not a literal analog radial selector. |
|6 Twin Atlas | Actual region context remains visible beside selected chamber. | Both maps shrink; initial pilot lacked pane labels/legend and clipped some counted-item prose. Latest source fixes await final pixels. |
|7 Expedition Dashboard | Gilt, keys, truthful seen% and three loadout slots stay visible. | Resources consume description width; seen% is exploration, not required win progress. |
|8 Focus Cards | Large selected illustration and full item prose explain use/resource cost. | Unselected rail icons are16px and sequential movement takes up to6 presses. |
|9 Barrier Index | Cut/Guard/Blast/Burn/Leap/Shoot/Return labels directly explain tool roles. | Key names ellipsize but selected identity is complete. This pilot omits menu ammo count in its short card. |
|10 Quick Ribbon | Every large item and relevant icon quantity can be compared at once. | A simple row takes up to6 presses; its initial map lacked a legend, now fixed in source awaiting final pixels. |

No panel/description/footer overlap was seen across the150-case pilot suite's
inspected overview boards and critical states. Ordinary map legends now fit
seven rows with truthful Task/Folk/Heart separation. Every fog board shows only
known geometry. Zoom changes scale without changing room orientation.

Last source corrections requested from actual evidence:
- Distinguish the gate glyph from the Chest glyph and label it G/Gate.
- Add Region/Chamber labels to Twin Atlas and a compact eight-glyph strip
  to Twin/Quick maps, using native measured216px text in216px available width.
- Use complete short functional text for h<=48 cards so Twin's counted Heart
  and seed descriptions do not end mid-sentence.
Runtime owner reports all three changes included before final source freeze.
Final rebuilt pixels must verify them; older pilot boards should not be used
as evidence that these final changes were already seen.

Optional discoverability suggestion (deferred, not blocker): zoom already
supports D-pad room browsing, while its footer only advertises B/R/Start.
A future selected design can advertise that useful control explicitly.
Menu ammo absence in4/9 is also reported as a design tradeoff rather than
a false failure of the separate HUD requirement. No winning style selected.
