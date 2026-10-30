# Final native interface review

Source ROM freeze: `d113d398692e9b98903e5d5a944ea3cadc2d6282`. Sixteen independently frozen ROMs comprise one baseline, five optional skins with the existing menu structure, and ten optional menu layouts using the same Winebound skin. No study is adopted as the production default.

Actual mGBA: **312 captures;1,166/1,166 checks passed**. Baseline22cases/86checks; five skins28cases/98checks each; ten layouts15cases/59checks each. Maximum observed OAM use40/128. Native PNGs are unchanged240×160 framebuffers. Filmstrips and integer zooms add labels outside the game image. Full-rate MP4s are lossy review conveniences; walkthroughs contain labelled cuts between real input segments.

Independent source/ROM audit: **7,523/7,523 checks passed**, including all sixteen frozen code/art/ROM hashes, all world/Drain/Bloom/StepCut tiles, sprites, palettes, animation clocks, IDs/contracts, native UI encodings and original font. All six earlierUI0..5 profiles retain exact decoded native source bytes. The baseline’s22 selected actual screenshots are also pixel-for-pixel equal to the previous final Drain baseline. These checks establish preservation and correct encoding, not artistic preference.

Each layout was driven through actual D-pad navigation, all seven tools, selected seeds/bow quantities, A/B/L assignment, non-equipable keys, independent tool/key focus, overview/zoom, preserved map focus, full/empty inventory and unknown map cells. No menu cursor, image, canvas, animation phase or pose was assigned by the harness. Seed, safe location, inventory/resources and visited flags are disclosed fixtures. Every static world tile and palette is restored after close; animated allocations match legal authored frames. Paused menu/map traversal preserves the world, current room and gameplay RNG. Unknown rooms never fetch terrain without the required knowledge.

Personally inspected the final native critical states: Atlas4 and Barrier9 show seed30/arrow50 on their compact title row; Twin6 has distinct Region/Chamber labels and complete compact Heart/seed help; Twin6 and Quick10 retain all eight legend symbols; Quick10’s overview/chamber captions remain unobscured at y24. No panel, number, icon, footer or description overlap observed in those final states. The five skin output families include sewer/healthy forest/blighted forest/cave HUD contrast, conditional0/9/99/255ammo, empty equipment, menus/maps, market, dialogue, chest reward, title and victory.

## Measured redraw cost

These are actual IRQ/video-frame measurements from the final runs, not inferred FPS claims. Cold full-terrain charts build the25room previews once; graph/route charts avoid that work. Cached cursor redraws are faster. Twin also redraws the inspected chamber.

|Layout|Cold overview|Cached cursor|Chamber zoom|
|---|---:|---:|---:|
|1. Loadout Workbench|52|2|4|
|2. Pocket Ledger|5|2|6|
|3. Fieldbook|52|2|4|
|4. Tactical Atlas|6|2|6|
|5. Toolwheel|6|2|6|
|6. Twin Atlas|9|6|5|
|7. Expedition Dashboard|6|2|6|
|8. Focus Cards|54|2|5|
|9. Barrier Index|6|2|7|
|10. Quick Ribbon|52|2|5|

The slowest first terrain charts take about0.9seconds. Input is queued during that cold chart; normal tested button taps last two video frames. Sequential ledgers/ribbons may take six D-pad presses between distant tools; grids/wheel reduce that travel but their spatial arrangement requires familiarity. Menus can show compact functional help instead of full prose; the Fieldbook and Focus Cards favor explanation. No automatic shortest/safe route, invented quest objective, new item mechanic or completion guarantee is displayed. The overview remains a truthful map of available knowledge.

Evidence: `audit-summary.json`, `review-summary.json`, per-ROM `capture.json` traces, `gallery-verification.json`, `baseline-pixel-preservation.json`. Independent research/UX findings are in the source research notes and associated UX record.
