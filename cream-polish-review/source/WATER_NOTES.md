# Native blue waterfall families

These are original indexed source drawings for optional Cream polish profiles
7–11. They are not emulator screenshots and do not select a new default.
The user's feedback asks for brighter blue water, convincing flowing liquid
and1/2/3-tile widths. No new external reference pixels are used.

| Profile | Source style | Construction | Unique8px patterns |
| --- | --- | --- | --- |
|7|Azure Curtain|A broad blue sheet with a pale left ribbon and sparse long cyan streaks.|83|
|8|Whitewater Ribbons|Unequal bright streams stay joined by blue water; foam is stronger.|116|
|9|Glassfall|A quieter cyan plane with a few long reflections.|73|
|10|Split Silk|Connected blue liquid divided by narrower darker blue channels.|77|
|11|Cerulean Cascade|Grouped cyan pulses and brighter foot spray.|117|

`art/cream_polish_water.py` draws complete16/32/48×16 segments before they
are split into16px cells. `fall(style,stage,width,kind,phase)` supplies a
crown, continuous middle or foaming foot. The two wet-rock contacts belong
only to the outer edges of the complete width, so wide curtains do not have
black/stone seams at internal tile boundaries. `pool()` supplies open blue
water material where the game already has genuine water physics.

The sixteen-color bank is exact RGB555: navy and cobalt shadows, azure body,
pale cyan/ivory reflections, green-grey wet contacts and sparse attached
purple rot. Blue remains blue at every corruption depth. The other Rind banks
remain unchanged. Every source frame is opaque indexedP, using indices1–15.
The pattern counts include all three widths, three segments, three corruption
stages, four poses and pool material, before sharing with other asset families.

Four poses advance the long flow streaks by four native pixels and wrap after
16px. At the intended8-gameframe pose interval this retains a32-frame cycle
while giving smoother steps than the older two-frame fall. Source GIF timing
is an inspection aid; ordinary mGBA clips establish the actual runtime result.

The runtime fits a complete channel into generated rock and leaves climbs,
caves, route gates and actual landing geometry intact. The last solid-face
segment has foam contact, not newly invented water collision on dry floor.
This preserves terrain meaning; a receiving basin would need its own coherent
geometry and water metadata rather than a blue picture painted over floor.

Source file SHA256:
`80dfee998e37b064efe63b7bd8b9db1d31954dffd8cd1b37e2a945ef30ae0281`.
The source review tests all540 fall calls and60 pool calls for native dimensions,
opacity and legal indices. Native sheets and nearest-neighbor inspection
copies are separate from the gallery's real mGBA room surveys/live clips.

Real-view review initially confirmed coherent blue1/2/3-wide curtains in
profile7's registered full rooms. Wet contacts stay outside the wide sheet;
small pale spray marks reach the wall foot, without the old brown root read.
A regular16px liquid-ribbon rhythm remains visible across the widest falls.
The foot is intentionally compact and can still feel abrupt where no larger
receiving basin exists. Those are visual tradeoffs, not imported assets or
changes to traversal mechanics.

Final profile7 ordinary frames for all three widths were also inspected: the
blue sheet and foam remain visible as the cyan marks move. Capture review found
an initially offscreen width3 view; normal camera settling now corrects that,
and per-frame screen bounds/blue-pixel checks verify visible water rather than
only offscreen animation. No camera/clock override is used in ordinary clips.
The gallery's capture/visual notes record that qualification and its limits.
