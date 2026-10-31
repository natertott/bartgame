BARTGAME - selected interface and ten enemy-art comparison builds

00 uses the selected HUD, item layout1, map layout2 and title Options, with
existing enemy art. enemy-study01..10 each select one alternative per current
six enemy mechanics: sixty alternatives in ten playable comparison ROMs.
Enemy forms remain proposals; names do not change mechanics. No commercial ROM
is needed. Source: 5eedc6dae94d8c1ea21c55b8668435bcf0be884d

Title: select Options; Up/Down chooses Style or Colors; Left/Right cycles;
A/B/Start keeps the choice and returns. Settings survive reset independently
of run saves. Menu/dialogue shapes and colors are independent; HUD is fixed.
Start opens/closes inventory; R cycles pages; A/B/L assign tools. Map A zooms,
B returns. D-pad browses. The minimap and equipped-item ammo stay on the HUD.

Normal build: make -j4 (BART_UI=6 BART_MENU=1 BART_ENEMY=0).
Study build: make -j4 BART_ENEMY=1..10 BUILD=build_enemy_N.
Gallery: https://github.com/natertott/bartgame/blob/appearance-enemy-studies/art-review/appearance-enemy-studies/README.md
