BARTGAME - five new UI skins and ten playable menu layouts

00 is the unchanged-looking production baseline. style01..05 use new skins
with the existing menu layout. layout01..10 use one fixed new skin and ten
interactive arrangements, so structure can be judged independently of color.
All share the final Drain/Bloom/forest/gameplay. No commercial ROM needed.
Source: d113d398692e9b98903e5d5a944ea3cadc2d6282
Build: make BART_UI=6..10 BART_MENU=0 for skins; BART_UI=6 BART_MENU=1..10 for layouts.
D-pad selects; A/B/L assign selected tools; R cycles pages; Start closes.
On maps A zooms and B returns. Old baseline retains its established controls.

Gallery: https://github.com/natertott/bartgame/blob/ui-menu-exploration/art-review/ui-menu-exploration/README.md
