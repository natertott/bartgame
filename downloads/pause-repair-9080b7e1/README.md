# Pause-menu display repair

Newly acquired catalogue tools and keepsakes appear on the first pause screen.
The selected Cream map restores shared HUD/menu graphics on exit. Existing art,
item effects, terrain and gameplay are preserved.

Source: 9080b7e1d32e1b344722fcd6f89acefe1e621160
ROM SHA-256: 9b3c24cf17088a335c7efeaf2d49aacb627abb43569987a050decf910f6a5f5f

Build: ARM GCC 14.2, BART_CREAM=12, BART_FOREST=32, BART_SWING=3,
BART_SEWER=9, BART_UI=6, BART_HUD=1, BART_MENU=1, BART_ENEMY=11,
BART_ENEMY_LAB=0, PROFILE=0. The approved Cream map and terrain remain selected.

Start opens the owned-item Workbench. D-pad selects tools and crosses pages
when needed; A/B/L equip; R changes pages; Select opens the standard Satchel.
A newly received tool is selected on the first opening. Newly received passive
items are shown on Keys; if only a passive was received, that page opens first.
Start resumes play.

Verification: 30/30 focused native mGBA checks, baseline reproduction of both
reported bugs, 40/40 actual-C host inventory tests. The native room survey
covered 25 Cream rooms in seed 1. This is focused regression coverage, not a
claim of every item being collected in a full playthrough.

Screenshots and test details:
https://github.com/natertott/bartgame/tree/cream-art-studies/pause-repair-review
Complete 139-entry item catalogue:
https://github.com/natertott/bartgame/blob/cream-art-studies/bartgame/docs/items/PLAYER_ITEM_CATALOG.md
