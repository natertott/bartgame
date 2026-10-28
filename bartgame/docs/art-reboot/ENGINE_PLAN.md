# Native art reboot: engine and artwork contract

This is a planning proposal, before production artwork or runtime changes.
The frozen baseline is `/workspace/setup/art-reboot-before/`; ROM SHA256 is
`bbd08678b1e10fb110e562a6374b0242cb8e73affbdd747f033fd0ce99619eee`.

The important distinction is **painted size, hardware canvas, and physical
footprint**. They are separate quantities. Existing actor rendering already
uses a feet point, so small native artwork does not require rescaling the
world, changing the maze, or shrinking the 16×16 terrain grid.

Production integration now follows the selected mockup: hero 32×32, ordinary
painted body 14×22, and world pickup canvases 16×16. Resident addresses are
derived in `actor.h`; damage is 12×20 at `(0,-11)` and movement feet are 10×8
at `(0,-4)`. Ground sampling and portal triggers use that new foot centre.
The held-use hands are north `(5,-17)`, east `(7,-12)`, south `(3,-9)` and
west `(-8,-12)`; guarding south instead grips `(0,-8)`. Exact source grips
are shared with the native item painter. Carrying retains `z=24` and the
original continuous release origin. Arrows now have a dedicated 6×6 contact
box centred 14 pixels above their logical feet, matching their visible
16-pixel canvas and height; wall collision uses that same box. These physical
alignment changes are intentional and require new runtime validation rather
than an assertion that old per-frame gameplay traces remain identical.

Stable painted extents of 18×24, rather than transparent 32×32 canvases,
control Bloom/NPC depth sampling. The Heart uses a 32×50 painted extent and
a separate 28×40 contact box. A grounded contact shadow helps the small
roots meet the floor. Surface-attached glitter is a separate renderer with
24 potential viewport sites, staggered half-duty cycles, foreground/ground
depth and no actor-pool or world-RNG consumption. Its observable counters
are `gAmbientSiteCount`, `gAmbientPotential`, `gAmbientVisible` and
`gAmbientPeaks`.

## Proposed shared contract

| Asset | Painted extent | Hardware canvas | Anchor |
| --- | --- | --- | --- |
| Bloom, ordinary poses | About 14×22; nominal 16×24 design box | 32×32, 16 OBJ tiles | Feet at local `(16,32)` |
| Bloom, action bodies | Up to 18×24 | Same 32×32 | Same feet, no canvas changes between poses |
| Separate sword/tool/cape effect | Draw to authored hand and reach | 32×32, 16 streamed tiles | Explicit facing-specific world offset |
| World drops | 8–16 pixels, commonly 10–14 | 16×16, 4 tiles/frame | Bottom-centre; clear ground shadow if needed |
| Inventory/reward icon | Usually 20–26 visible pixels | Keep 32×32 | Existing icon layout |
| Carried bush/rock/pot | 12–16 pixels | Keep 16×16 | Bottom aligned consistently between all four loads |
| Ordinary NPC | About 16×24 | 32×32 | Bottom-centre |
| Small enemy | About 12–16×12–16 | Existing 16×16 where possible | Bottom-centre |
| Large enemy | 20–24×24–32 | 32×32 | Bottom-centre, separate weapon effect |
| Boss | Deliberately larger, about 32–48 pixels | 32×64 or 64×64 as needed | Explicit feet/ground anchor |

The final mockup and pose sheet determine the exact hand coordinates. These
numbers are a single interface to be agreed before drawing held props, rather
than independent guesses made by body and prop painters.

## Bloom canvas and reserved OBJ memory

`src/player.c` currently streams a **64×32** body into tiles `0..31`, keeps a
12-tile sword sheet at `32..43`, and streams a shield view into `44..55`.
`src/actor.c` starts dynamic allocation at tile 56. The apparent body is
23×30 pixels despite that large canvas. The sword is already separate.

Use a 32×32 hero sheet, retaining all 101 frame names/identifiers initially.
`hero_set_frame()` already derives upload size from the sheet. Update the
stale 64-pixel comments and fixed reservations together. Two safe choices:

1. Initially leave `SWORD_TILE=32`, `SHIELD_TILE=44`, and first-free tile 56.
   This wastes 16 tiles but minimizes layout changes during visual integration.
2. After the new shield dimensions are fixed, make the reserved addresses
   depend on the hero/sword/frame tile counts, aligned to an even tile index.
   A 16-tile hero, 12-tile sword sheet and 4-tile shield view need only 32
   reserved tiles, freeing 24 compared with the current 56.

Do not reduce the reservation without moving every consumer. `SWORD_TILE` is
currently loaded even though the visible sword swing uses `BLOOMFX`; remove
that legacy reservation only after confirming the pause/menu code no longer
reads it. Existing tests and developer comments sometimes assume hero shape
`wide,size3`, 64×32 or 1,024 bytes: these must inspect the generated sheet
metadata instead of preserving that obsolete shape assertion.

## Feet, damage and interaction footprints

Current `HB_HERO` is width 12, height 24 centred 14 pixels above the feet;
its top reaches 26 pixels above the feet. That would extend above a new
22-pixel body. Current movement feet are 12×12 centred six pixels up.

A coherent optional retune is a **12×20 hurt box at `(0,-11)`** and
**10×8 movement feet at `(0,-4)`**. This is a real gameplay change, unlike
redrawing the body. It needs real collision/corner-assist, ledge, pit, water,
shield contact, enemy and sword boundary checks. Keeping the old feet box
for the first visual build is also safe because a 16-pixel body can cover
its 12-pixel width; the hurt box still needs an explicit visual decision.

Tile interactions sample feet and facing, not sprite dimensions. Chest
opening, lifting, locks, portals, switches and shrine triggers can keep their
logical tile coordinates. Any movement-box change must be checked against
16-pixel passages and the procedural room solver. Actor pool stride and
`PlayerState`/save layout do not need to change.

## Every held anchor that must be reconciled

All coordinates below are world pixels relative to Bloom's feet, before
camera and airborne height subtraction. Source art local coordinate is
`(world_x+16, world_y+32)` for the proposed body canvas.

- **Body:** bottom-centre remains fixed. Do not recenter each pose on its
  opaque bounding box; that produces shaking and makes jumps look detached.
- **Sword:** `sword_bounds()` is the shared inclusive hit box and drawing
  anchor. Current north reach is `(-14,-32)..(13,-12)`; east
  `(4,-22)..(22,2)`; south `(-14,-6)..(13,12)`; west
  `(-23,-22)..(-5,2)`. A smaller body can still use these extents if the
  complete sweep is drawn honestly. Prefer a deliberately authored compact
  blade/sweep first, then choose reach from that drawing. Do not shrink the
  picture while silently retaining an invisible wide hit box. Preserve the
  15-frame anticipation/live/recovery timing unless deliberately redesigned.
- **Sword occlusion:** north-facing blade/hilt must pass behind the actual
  new head silhouette while the forward cutting crescent remains visible.
  The old source mask maps a 64-pixel body; it must be rebuilt for the new
  head rather than translated blindly.
- **Bow/lamp/cape:** the current action origin is `(-16,-32)` and north bow
  is raised a further four pixels. This was designed for a 30-pixel body.
  Keep a 32×32 effect canvas, but redraw its grips at the new actual hands.
  Keep north-held tools on the far side and back-worn cape on the correct
  body side; preserve the directional OAM composition.
- **Shield:** current draw origins are north/east `(+2,-24)`, south
  `(-8,-16)`, west `(-18,-24)`. Those origins assume the present 16×16 shield
  with a large painted rim. A smaller 8–12-pixel visible shield requires
  its own painted grip and per-facing anchor. Ensure the north shield reads
  beyond the head rather than covering the back or disappearing completely.
- **Bomb:** `bomb_place()` stores release hands at north `(+7,-10)`, east
  `(+10,-7)`, south `(+7,-3)`, west `(-10,-7)`. These are actor bottom-centre
  release positions, not source top-lefts. Reconcile them with the new small
  16×16 bomb art and its visible alpha before keeping the hand-to-ground ease.
- **Bow projectile:** `player_shoot()` starts from feet minus four pixels,
  plus six in the facing direction. The arrow actor additionally rises six
  pixels and uses its own canvas origin. Compare the first real projectile
  frame with the final drawn bow grip, including that projection; do not
  align only their logical centres.
- **Lamp contact:** `player_lamp_box()` is an independent roughly one-tile
  facing rectangle. Redraw the flame to communicate this reach and test its
  overlap with real webs and censers.
- **Lift/carry/throw:** current held load top-left is `(-8,-40)` and a thrown
  16-pixel load starts at `z=24`, giving exactly the same screen top-left.
  This is not necessarily too high: with alpha reaching local row 15 its
  visible bottom is `-25`, only 2–3 pixels above the proposed head top `-22`.
  Draw raised hands to contact that bottom, or change both held and thrown
  rendering deliberately. Moving the held load to `-34` alone makes release
  jump six pixels. Changing thrown `z` also changes flight time and range.
- **Item-get:** the current 32-pixel reward icon starts at `(-16,-60)` and
  moves down during its introduction. Keep this celebratory large image
  separate from small world drops. Set a deliberate gap above the smaller
  head; do not reuse the world sprite as the reward display automatically.
- **Ground shadow:** retain its ground feet anchor, independent of airborne
  `z`. A 10×4 or 12×4 painted ellipse is enough for a 14-pixel body, within
  the current 16×8 two-tile canvas.

## World pickups versus inventory icons

Keep the generated sheet name `pick32` if retaining its identifiers avoids
unnecessary C churn, but change its **sheet dimensions** to 16×16 and redraw
all ten frames. The historical name need not imply actual dimensions.
`pickup_spawn()` uses `actor_set_sheet()`, so actor width, height and bottom
centering adapt automatically. The ten frames then need 40 resident tiles
instead of 160, freeing **120 OBJ tiles** while making drops appropriately
small. Do not scale source bitmaps at runtime or reuse inventory PNGs.

Keep `icon32` at 32×32. It serves bag pages, descriptions, HUD equipment
slots and raised rewards. Its seven-frame LRU is the minimum for the seven
simultaneous distinct icons on the current bag page. `ICON32` palette arrays,
HUD upload strides and exact menu palette restoration remain separate from
world pickup palettes. Small in-world items may share design motifs and
colours with their inventory symbols without sharing pixel layouts.

## Special NPCs, scenery and doors

Ordinary forest NPCs already use 32×32 sheets and standard bottom-centre
actor rendering. Their painted bodies can adopt the same 16×24 scale.
The two Drain keepers are exceptions:

- Peddler head draws at feet `(-32,-48)` with a one-pixel breathing offset;
  body at `(-32,-32)`. Both use wide canvases and independent streams.
- Gatekeeper draws at `(-32,-64)` with a separately anchored wisp.
  Palette glow changes two explicit indices over time.

Redrawing these to ordinary scale requires changing their manual draw
anchors or placing their new images at the matching locations in their
existing canvases. Do not leave 32×55 and 50-pixel special NPC bodies beside
14×22 Bloom unless their exceptional size is an intentional character trait.
Portraits are separate 48×48 images padded into 64×64 OBJ canvases and can
remain illustration-size while adopting the same line/shade grammar.

The large chest/portal module is already independent from logical metatiles.
New roughly 20×18 chests and 24–32×36–40 entrances can reuse its streams,
while preserving opening/closing states and logical tile alignment. Visible
sizes must be checked beside the **new Bloom**, not against the old body.
The Drain's forest ladder belongs to the painted `sw_hall.py` mosaic, not
legacy `sw_ladder`. Change its real artwork or provide a deliberate portal
renderer; editing an unused legacy tile will not fix the complaint.

## HUD and menu recommendation

Keep the familiar inventory/menu structure while redrawing its materials,
icons, highlights, text palette and frames under the common style guide.
The current HUD genuinely occupies **32 pixels**: three 32×32 equipment
icons, a 32×32 minimap, four-tile-high borders, counts at y14 and purse at
BG row2. Simply changing `HUD_H` to 3 does not compact it; sprites still
extend to y32 and old tiles may remain uncleared.

A true 24-pixel HUD needs a separate 16×16 HUD-icon display or a natively
redrawn 24-pixel representation inside a supported canvas, revised slot
frames/count positions, a compact map, and explicit clearing of all old
32-pixel rows. Preserve the 32×32 inventory sheet. A dedicated HUD sheet or
native icon source is preferable to CPU shrinking the menu images.
If the mockup keeps the 32-pixel HUD, revise only its artwork first; that is
the safer way to retain the currently liked layout.

## Glitter and validation

Abundant glitter need not consume one actor per spark. Use native animated
background flecks in canopy, wet stone and water, with multiple authored
phases/variants, and reserve a small number of actor effects for important
interactions. Ambient 1–3-pixel twinkles and larger deliberate reward glints
must differ in shape, timing and placement. Do not use a common loot-star
silhouette as incidental floor noise or make all glitter flash in lockstep.

The first production integration should prove native dimensions/palette
limits from packed ROM data and actual VRAM, then capture the complete Bloom
suite and representative screens at 240×160. Existing tests with hard-coded
hero width, shape, upload byte count, shadow or old art colour assumptions
need metadata-driven checks; their gameplay assertions should remain.
Required regression areas are movement/corner assistance, damage and sword
boundaries, first projectile alignment, lifting/throwing continuity, directional
shield/tool depth, water/pits, all portal styles, item pockets, quest/trial
rewards, menu cache/palette restoration, save round-trip and all 25 generated
rooms across several seeds. Do not present native source mockups as emulator
screenshots: both are valuable evidence, but answer different questions.
