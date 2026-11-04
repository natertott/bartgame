# Gilt HUD: coordinated native item drawings — 2026-11-04

The direct source is the user's request for larger HUD items, clear buttons,
high contrast and shimmering gold frames. The recorded six-PDF application
matrix remains the design basis: silhouette first, broad connected value
planes, selective upper-left highlights and contextual contrast. This pass
claims no new external article or game measurement.

`art/hud_gilt_items.py` draws three independent native scales. Equipment and
key-item HUD icons use a 16×16 canvas with approximately 15–16px ink bounds;
menu/reward illustrations use their existing32×32 canvas; world drops retain
8–14px bodies on16×16 canvases. No image is resampled to create another size.
The diagonal blade has a broad bright face, gold guard and short grip; the
wood and leaf-charge shields remain distinct; lantern cage/flame, hood/cape,
visible bow/string, ribbed metal disc and broad palm/fingers carry one identity
each. Relic and astrolabe have different centers. A full heart container has
its perimeter; the fragment has a visible break and dark missing half.

Gold uses the existing literal material bank. Bombs gain a connected wine/
magenta highlight from their existing bank, rather than introducing a new
violet palette. Cloak green uses a continuous lighter upper-left plane and
rim over a dark hood recess. The already-selected physical sword swing,
held shield views, held lantern/bow effects, carried objects, projectile
arrows, Bloom, enemies, terrain, chests and entries remain unchanged.

`BART_HUD=1` selects these paintings only in the `items`, `pick32`, `icon32`
and `huditems` families. All65 existing frames retain their names, order,
canvas dimensions and material aliases. `BART_HUD=0` preserves original
source painters and the historical late10px HUD-glyph override. The old
`small()`/`large()` helpers are deliberately retained so physical sword
sheets cannot accidentally inherit the presentation redesign.

Native P/indexed and RGBA exports are source evidence, not emulator captures.
The export manifest records all65 frames, painted bounds, inks and palettes.
Real mGBA HUD readability, button placement, border shimmer, menu restoration
and native framebuffer captures are documented by the parent pass. Remaining
tradeoff: the preserved material palette makes the blightseed highlight wine/
pink rather than a newly saturated blue-violet. The ordinary world pickups
stay compact and intentionally have less detail than their menu counterparts.
