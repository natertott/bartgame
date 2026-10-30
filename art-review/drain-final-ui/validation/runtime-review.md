# Independent review of the final Drain and five UI studies

Final game/art source: 87abc1b4aa90d8f993896669a4bbebec8dd2112e.
All six builds received 39 freshly recorded presentations each: 234 actual
mGBA cases, 894/894 functional checks. The source gallery contains 657 final
placement identifiers and 1,554 native frame drawings, with all frame hashes.

## Visual review

The final room's enlarged broken pipe has an exposed cut cavity and a visible
leak. The forest arch and ladder are taller, and the arrow is above its rungs
inside the open center of the compact HUD. Both arches now use a continuous
upper-left highlight with a quieter right return, rather than unrelated dark
patches. Sidewalls are narrow capped side-facing masonry; they no longer
continue the north wall's horizontal face down the screen. The left-edge
profile pipe visibly points into the channel and discharges into a splash.
Storage retains recognizable wooden lids and barrel staves; bridge and rail
connect their intended banks. These findings were checked in native source
assemblies and actual settled-camera mGBA views.

All five styles were reviewed at actual native size in the six-screen main
board and the 27 individual comparison families: HUD on sewer/healthy/blight/
cave,ammo 0/9/99/255, non-ammo slots,inventory/equipment/key items,map/zoom,
shop/selected/unaffordable/purchase response, two wizard pages,reward, death
return, title/Continue/NewGame and victory. Ivory Wire is the quietest; Black
Glass is more formal; Vellum makes the largest value/material change; Wine
Reliquary is deliberately busiest; Salvage Ledger is rougher and muted. These
are user-selectable studies, not a ranking or automatic production choice.

An earlier full pilot passed all functional checks but visual review caught
two semantic-ink failures: dark selected-tab letters on new dark skins, and
dark outlined prose merging on the light Vellum victory panel. Those cases
were archived as pilot-443e7aa. The narrow C fixes select themed high ink for
study tabs, invariant pale outlined item-count overlays and floating prompts,
and plain dark backed Vellum victory prose. A separate UI2 pilot and all new
final screenshots confirm readable selected tabs/counts and crisp victory
prose. No final image is reused from the superseded pilot.

## Runtime observations and publication limits

Actual BG0 and HUD OBJ alpha remain within the twelve-pixel top region and
the 16×16 corner minimap(x222..237,y142..157). The center gap x116..147 remains
transparent. Keys do not alter HUD pixels; equipped ammunition values create
distinct pixels, while changing unequipped ammunition does not. Natural room
navigation changes the actual minimap allocation. Every ordinary idle sample
keeps one game update per VBlank. The maximum sampled OAM count is 40/128;
these samples are not a worst-case guarantee.

Every individual GIF except death/return fits an exact shared palette. That
transition spans 298–316 colors across different scenes; its quantized GIF is
retained locally and explicitly omitted from publication. Native selected
PNGs and full-rate MP4 preserve the event, with MP4 labelled as a lossy review
convenience. Five-style composite GIFs also publish only when their palette
union fits 256 colors. Labels sit outside actual game pixels.

Menus, dialogue, purchases, chest reward, death/save return and Heart victory
use real controls/events. Seed, inventory, safe position and navigation are
disclosed fixtures. No UI canvas, image, pose or completion state is assigned.
No standalone yes/no dialog exists in this engine; actual shop and title
choices are shown instead. Root's independent packed-ROM/physical audit is
separate from this visual/runtime review.
