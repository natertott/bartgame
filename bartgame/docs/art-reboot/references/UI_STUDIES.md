# Five interface studies: native source freeze

Status: five exploratory interface treatments. The user has selected a final
Drain combination but has not selected a UI study. `BART_UI=0` retains the
previous Quiet Brass menu material with the new compact HUD; options1–5 are
new complete skins. The user's latest steering retains the minimap and asks
for current ammunition only when blightseeds or the bow are equipped. The
old24px solid top ribbon and unrelated key/resource readouts remain superseded.

The repository AGENTS.md, shared art bible, direction log and source register
were read before editing. This pass applies the recorded native, silhouette,
value, material and selective ornament principles (G01–G18); it does not claim
any new article or unavailable reference figure was read. The direct source is
the user's request for a wide visual swath, filth beside glitter, minimal
backgrounds and an unobstructed view of the upper room.

## Five structural and material alternatives

1. **Ivory Wire:** thin, slightly broken ivory/gilt wire; open corners; quiet
   blue-black panels, light proportional type and pinprick joins. Most spare.
2. **Moulded Vellum:** rounded, imperfect paper edges; fine ink rules and warm
   light parchment, dark type, narrow folded-paper selection tabs. This is a
   deliberately bright interface alternative to the existing dark palettes.
3. **Black Glass:** clipped Art Deco corners; stepped double rails; near-black
   glass and hot brass; angled cursor brackets and diamond currency marker.
4. **Wine Reliquary:** wine-dark cloth, leaf-like corner knots and embroidered
   gilt rails, diamond continuation marker and floriate cursor. This is the
   most ornate study, deliberately offered as the broad end of the range.
5. **Salvage Ledger:** desaturated green ledger field, offset frame joins,
   interrupted stitches, small rivets and repaired-tab selections. Grime is
   conveyed through material and damage instead of illegible text noise.

Every theme reauthors corner, top, side, plate, active/inactive tab, slot,
selected slot, list row, selected row, speech bubble/tail, button badge, coin,
key, divider and rule geometry. The inventory cursor and next/pick markers
also change their native geometry. This is more than a palette comparison.

Each menu uses the same semantic ink roles and text hierarchy. The light
vellum study intentionally maps the cream/high text roles to dark ink. The
map's world greens, water and blight remain semantically consistent, while
its neutral field/grid/ink coordinate with each skin. Shared functional map
symbols retain their silhouettes. The native font and advances remain the
established readable face; no title lettering or portrait geometry is changed
by font transformations. The opening illustration and world item art remain
outside this interface redraw.

## Compact HUD asset contract

The HUD shows equipped item identities, hearts and gilt, plus the minimap
retained by the user's later steering. Ammunition appears only on an equipped
blightseed or bow slot. There is no always-present ammunition/resource/key
readout. The runtime agent owns the twelve-pixel-high separated top pods,
native3x5 numeric type and a compact corner minimap, leaving the upper center
open. The source art provides transparent
8x8 full/half/empty hearts with a dark contour, and **seventeen separately
authored10px equipment glyphs** inside existing16x16 hardware canvases. The
visible icon extent stays withinx2..11,y1..10; the other pixels are transparent.
These are neither clipped16px world drops nor reduced32px menu illustrations.
The original item frame identifiers and per-item material palettes remain.

The ordinary weapon/tool identities do not change between interface themes:
blade, shield, round blightseed, lamp, cloak, bow and vented hubcap stay readily
recognizable. The runtime varies small pod ends and button-label presentation
without adding a full-width opaque bar. World drops, reward illustrations,
Bloom's animation and the Step-and-cut blade/hit relationship remain untouched.

`ui_studies.hud_icon(name)` supplies native indexed pixels to the existing
`huditems` sheet. `reboot_ui` installs the selected palette,51kit tiles,
markers and cursor from `ui_studies` while preserving engine-facing IDs.
`HUD_INDEX['.']=0` encodes real transparency for the heart tiles. All existing
font widths, per-screen strings, costs and navigation meanings stay stable.

## Native review and evidence

`five-ui-source.png` shows representative native menu/dialogue skin assemblies,
explicitly labelled as **source studies, not emulator screenshots**. Their
layout demonstrates palette/geometry/readability and does not stand in for
actual final screen captures. Separate native240x160 images are kept for all
five views. `compact-hud-icons.png` shows each10px glyph at1x and3x using its
actual retained item material bank.

Source critique: Ivory Wire is quietest; Vellum makes broad structural contrast
without low-contrast type; Black Glass has a heavier formal frame; Wine is
visibly the busiest, with repeated ornament that may be too much for some
players; Ledger is restrained but has the most intentionally broken edge.
No ornament is drawn into the interior text field. Actual final dialogue,
shop and menu screenshots must still be checked for clipping and contrast.

`native-validation.json` records **666/666 passed** across all six variants:
16-entry RGB555 groups;51valid8x8 kit tiles; transparent heart edges; all six
8x8 marker frames;32x32 cursor canvas; all seventeen legal16px equipment
canvases with10px painted bounds. The five complete kit geometry hashes are
distinct. These are source/hardware integrity checks, not taste scores or
claims of runtime performance. Actual packed-ROM and mGBA checks are separate.

Frozen source SHA256:

- `art/ui_studies.py`: `ba3a63e813b1e2eb3f47d5b6e2844a0dfa3074a5aa4e7e06c5921a35ecc7a23b`
- `art/reboot_ui.py`: `6963ac2536f37580c1e398228b22359ea03c39460b9814fb751d4de82c98dfc7`
- Unchanged `art/ui_font.py`: `48ae0da7d1daa4f01c144a856d18694c5be06674288029e62913a513bcb8388e`

No further source edits are planned unless actual screen review identifies a
specific clipping/readability problem. Font metrics and the title remain
protected. A future selected UI direction should preserve this compact HUD
contract even if its ornamental material is refined.

## Follow-up HUD steering and floating-text contrast

The later user correction retains the minimap and current ammunition only
for an equipped blightseed or bow. This needs no change to the five source
kits or compact item glyphs. The UI OBJ bank already retains dedicated world
green roles for minimap terrain; existing map icons and marker semantics
remain consistent in all five themes. The runtime owns the isolated map rim
and placement, and the native outlined3x5 ammo numbers beside equipped items.
A count must not be shown for a non-ammunition item or for an unequipped weapon.

Numbers over the playfield should use the invariant HUD palette's cream with
a dark contour. They must not borrow the light-vellum menu's dark `CREAM` or
`HIGH` text roles without a paper backing. The review agent identified the
same distinction for title/Continue/New Game/victory prompts floating over
a dark illustration: use the existing `UI_INK_PALE` (`W`) role, which remains
light in all five themes, with a dark contour as needed. Paper menu body text
continues using dark cream/high roles for proper contrast. This is a placement
contrast rule, not a reason to make all text indiscriminately pale.

Source hashes and666native checks above are unchanged by this runtime-layout
steering. Actual minimap, equipped-ammo and floating-prompt screenshots are
required context evidence, handled by the runtime/review agents.
