# Frozen-build asset audit for the art reboot

This audits the standalone game in the **inner `bartgame/` directory**. The
outer repository also contains a Minish Cap decompilation; those legacy game
assets and QuickStart documents are not the current standalone game's asset
pipeline.

The frozen pre-reboot ROM is `1 e66780`'s published build (game source
`3 d3 f8 aa`), SHA256:

```text
bbd08678 b1 e10 fb110 e562 a6374 b0242 cb8 e73 affbdd747 f033 fd0 ce99619 eee
```

Paired ROM, map and generated header were frozen under
`/workspace/setup/art-reboot-before/` before new art work began. The machine
inventory decodes packed ROM bytes rather than importing mutable art painters:
[all metatiles and sprite frames](asset-inventory.json),
[metatile CSV index](metatile-index.csv), and
[reproducible inventory tool](../../tools/art_reboot_inventory.py).

## Coverage and current limits

The build has **913 global metatile IDs**, **833 resident metatiles**, **32 OBJ
sheets** and **354 source sprite frames**. Resident means included in a compiled
area tileset; it does not assert that every generated run places every variant.
The 80 nonresident `sw_*` tiles are superseded by the painted `swh_*` Drain hall.
The CSV indexes all 913 IDs, their behavior and collision, transparent-prop
status, compiled resident sets and direct C references. Arithmetic variant
ranges may have no individual direct reference; they are not therefore unused.

| Area tileset | Resident metatiles | 8×8 subtiles | BG palette banks | Animated metatiles |
| --- | ---: | ---: | ---: | ---: |
| Healthy/blighted forest together | 376 | 997/1024 | 12/12 | 59 |
| Drain painted hall | 370 | 999/1024 | 11/12 | 38 |
| Caves/hollows/thickets together | 97 | 199/1024 | 8/12 | 6 |

There is intentional sharing between forest and mystery sets. Tiles use four
8×8 subtiles per 16×16 metatile, per-quarter flips/palette banks and transparent
index 0. Animation reserves a mutable four-subtile base and swaps frames into it.

The ordinary OBJ allocator stops at tile 876. Its latest 582-context sweep
reached 854 (22 tiles spare); all 1024 hardware OBJ tiles also include fixed HUD,
portrait and minimap reservations. Hardware has 128 OAM entries. A larger source
sheet does not imply all its frames are resident: Bloom, action effects,
portraits, keepers and large interactive scenery stream frames.

## Measured scale failures

These are alpha extents measured from the frozen packed 4 bpp pixels, not sprite
canvas dimensions or nominal collision boxes:

- Bloom south idle is **23×30**, while normal direction/action bodies range
  up to 29 px wide and 30 px high. The 64×32 canvas exaggerates the nominal sprite
  size, but the visible idle itself is still nearly two terrain tiles tall.
- Every world pickup in `pick32` is **25–30 px wide and 25–30 px high**. A routine
  heart or money drop is therefore about as large as Bloom, and larger than
  the 16 px barrier or small enemy beside it. This is the strongest hierarchy
  mismatch; inventory illustrations and world drops currently share enlarged
  design assumptions.
- Beetles are 13×13, spitters 12×14 and slimes 10–14 px wide. Knights are about
 14–16×30. The Heart's 27×29 visible body is approximately Bloom's height rather
  than a commanding boss silhouette.
- Ordinary NPCs are 18–26×26–31. The Gatekeeper is 32×54–55, and the merchant is
  a 50×20 body plus 39×24 head drawn as a multi-component figure.
- Chests are 22–26×20–26 after the latest enlargement. Portal frames are 32×47.
  These must be reassessed against the new character scale as a coherent set,
  rather than preserving every previous enlargement automatically.

## Exhaustive OBJ sheet map

Sizes below are full transparent canvases; the visible range is the minimum
and maximum nonempty alpha footprint across frames. Exact bounds and every
frame name, ID and packed-byte hash are in the JSON. A blank `none` frame is
excluded from the visible range.

| Sheet | Canvas | Frames | Tiles/frame | Visible width×height range | Palette group | Current role/source |
| --- | --- | ---: | ---: | --- | --- | --- |
| `hero` | 64×32 | 101 | 32 | 10–29 × 6–30 | `hero` | Bloom body, every action; streamed frame at fixed HERO_TILE0. Source: pack → bloom_animations. |
| `sword` | 16×16 | 3 | 4 | 8–15 × 8–15 | `gear` | Small sword/equipment display in pause menu; action sword is bloomfx. Source: pack → clean_items/reference_assets. |
| `shield` | 16×16 | 6 | 4 | 5–14 × 14–14 | `gear` | Held guard in four directions; pause equipment. Front/back/side plus upgrade. Source: reference_assets. |
| `items` | 16×16 | 21 | 4 | 10–14 × 12–14 | `items` | 16 px tool/bomb frames and shop icons. Source: pack → clean_items → reference_assets. |
| `beetle` | 16×16 | 4 | 4 | 13–13 × 13–13 | `bugs` | Rot beetle enemy, forest and mystery fights. Source: forest_sprites. |
| `bat` | 16×16 | 3 | 4 | 7–13 × 10–11 | `bugs` | Flying enemy and shadow-facing sprite. Source: forest_sprites. |
| `slime` | 16×16 | 3 | 4 | 10–14 × 6–10 | `bugs` | Slime enemy. Source: forest_sprites. |
| `spitter` | 16×16 | 9 | 4 | 12–12 × 14–14 | `blight` | Directional spitter enemy. Source: forest_sprites. |
| `knight` | 16×32 | 12 | 8 | 14–16 × 30–30 | `iron` | Tall knight and miniboss body. Source: forest_sprites. |
| `ksword` | 16×16 | 2 | 4 | 9–16 × 9–14 | `iron` | Enemy sword separate from knight body. Source: forest_sprites. |
| `fx` | 16×16 | 13 | 4 | 3–15 × 3–15 | `fx` | Puff/splash/spark/flame/bomb/sparkle/firefly runtime effects. Source: pack → clean_items/reference_assets. |
| `proj` | 8×8 | 3 | 1 | 6–7 × 6–7 | `fx` | Seed/projectile micro-sprites. Source: pack. |
| `npc` | 32×32 | 7 | 16 | 18–26 × 26–31 | `folk` | Ordinary forest quest folk; only hermit/nun/gardener currently use this route. Sage/merchant use special sheets; two extras are unplaced. Source: pack. |
| `boss` | 32×32 | 3 | 16 | 27–27 × 29–29 | `blight` | The Heart boss pulse frames. Source: forest_sprites. |
| `lift` | 16×16 | 4 | 4 | 12–16 × 10–15 | `lift` | Carried/thrown bush, small rock, boulder, pot. Source: bloom_loads; pot from interactive_tiles. |
| `arrow` | 16×16 | 3 | 4 | 5–14 × 5–14 | `icons` | Directional player arrows. Source: reference_assets. |
| `mouth` | 32×32 | 3 | 16 | 28–28 × 25–25 | `fx` | Drain Cap swallowing/return effect, not cave entrance art. Source: pack → clean_items/reference_assets. |
| `marks` | 16×16 | 13 | 4 | 9–16 × 8–15 | `ui` | Large pause-map event/quest/gate symbols. Source: pack. |
| `dots` | 8×8 | 12 | 1 | 6–6 × 6–6 | `ui` | Small overview/legend/map marks. Source: pack. |
| `cursor` | 32×32 | 1 | 16 | 32–32 × 23–23 | `ui` | Compiled legacy map cursor; no current C consumer. Current map cursor uses four uimarks corners. Source: pack. |
| `pick32` | 32×32 | 10 | 16 | 25–30 × 25–30 | `pick` | All loose world pickups: hearts, money/hoard, bombs, key, relic, Grail, arrows. Source: reference_assets. |
| `icon32` | 32×32 | 17 | 16 | 21–30 × 22–30 | `icons` | Inventory/reward/HUD item icons, including per-frame exact menu palette. Source: reference_assets. |
| `uimarks` | 8×8 | 6 | 1 | 5–8 × 5–8 | `uikit` | Advance arrow, selection pointer, cursor corner, A/B/L badges. Source: ui_kit. |
| `face` | 64×64 | 6 | 64 | 46–48 × 46–48 | `portrait` | Six dialogue/shop portraits, 48 px art inside 64 px canvas. Source: faces. |
| `peddler_head` | 64×32 | 5 | 32 | 39–39 × 24–24 | `peddler` | Streamed merchant head/body composite in Drain. Source: sw_folk. |
| `peddler_body` | 64×32 | 14 | 32 | 50–50 × 20–20 | `peddler` | Streamed merchant body/gesture component. Source: sw_folk. |
| `gatekeeper` | 64×64 | 6 | 64 | 32–32 × 54–55 | `gatekeeper` | Streamed tall Drain keeper body. Source: sw_folk. |
| `wisp` | 16×16 | 4 | 4 | 6–7 × 10–11 | `gatekeeper` | Keeper orb/wisp separate animated sprite. Source: sw_folk. |
| `bloomfx` | 32×32 | 47 | 16 | 5–28 × 8–27 | `gear` | Bloom sword/cape/bow/lamp visual action layer. Source: bloom_fx → reference_assets. |
| `bloomshadow` | 16×8 | 1 | 2 | 12–12 × 4–4 | `hero` | Airborne Bloom ground anchor. Source: bloom_animations. |
| `interactivechest` | 32×32 | 6 | 16 | 22–26 × 20–26 | `lift` | Enlarged wood/brass/relic closed/open display over logical chest. Source: interactive_props. |
| `interactiveentry` | 32×64 | 6 | 32 | 32–32 × 47–47 | `lift` | Cave/hollow/thicket open/closed display over logical mouth/exit. Source: interactive_props. |

## Background ownership and runtime use

The exact per-tile index is exhaustive; the semantic families below explain
which runtime systems consume it and which source painters currently compete
for ownership.

| Display/families | Source and composition | Runtime owners/contracts |
| --- | --- | --- |
| Healthy terrain: moss/grass/path/verges/roots/leaf litter, dirt/rot transitions | `forest_art.py`, then `healthy_reference.py`; shared woodland palettes also recolour older untouched material | `roomgen.c` ground dressing, route lanes, blend side/corner masks; IDs and contiguous range arithmetic matter |
| Healthy canopy, trunks, oak/birch/fir and foliage props | Original `tiles.py` declarations followed by forest/healthy painters | Multi-metatile trees use physical lower trunk cells and passable overlay crowns; `room_prop_priority()` resolves actor depth |
| Blighted ground/ruins/walls/trees/crystals/veins/pools/mist | `forest_art.py`, atlas-derived `blight_reference.py`, plus its appended clones | Stage-dependent roomgen; stage 3/Heart decoration, animated hazard frames and cosmetics share logical contracts |
| Water/banks/corners/bridges/ledges | Terrain painters plus healthy material remap | `roomgen.c` continuous watersheds, cardinal/corner shore masks, bridges, drop direction; visual edge must match collision/traversal |
| Bush, small rock, boulder, thorn, stump, bone/litter props | Forest/healthy painters; lift silhouette copied separately | `react.c`, `objects.c`, `player.c`; cutting, lifting and clearing reveal stored underlay. Carried and ground silhouettes need one source |
| Chests and mouths | Logical 16 px background placeholders plus `interactive_props.py` OBJ image | `interactive.c` suppresses old background picture while preserving collision/reward/transition tile. Frame tiers read existing loot |
| Plates, cracks, web, locks, censers, pot, pit, spring, statue/shrine plate | Final `interactive_tiles.py` painter | `myst.c`, `react.c`, `items.c`, `game.c`; open/pressed/burned/lit/spent states. CRACK/WEB display on BG1 over local floor |
| Cave/hollow/thicket interior wall/face/crown/floor/edges/glow/exit | `tiles.py` + forest/environment painters; final interaction overrides | `myst.c` three styles/sizes and all event variants; floor-switch/lift/chest logical clones carry interaction type under overlays |
| Painted Drain `swh_000…369` | `sw_hall.py` native 480×320 scene → `sw_cut.py` palette/tiles → `sw_drain.py` cell contracts | `rooms.py` ground/overlay map + actual collision quarters. Editing legacy `sw_ladder` does not change the visible hall exit |
| Legacy `sw_*` hand tiles | `tiles.py`, old style/atlas layers | Not resident in current compiled sets; no visible hall effect. May be retired or completely restyled, but must not be mistaken for current Drain work |
| Animated glitter/motes, mist, water glints | Metatile animation + `fx` actors + keeper wisp/orb pulse | `tiles_animate()`, `objects.c`, `npc.c`; animation cadence and effect emphasis need shared art-direction rules |

## All non-world visual surfaces

| Surface | Asset source | Runtime/compositor |
| --- | --- | --- |
| Title/continue screen | `title.py` resizes `art/ref/title-reference.jpg` with Lanczos to 240×160; packed Mode 3 RGB555 with **2,070 colours**,76,800 bytes | `game.c` title bitmap, fading, PressStart/Continue/New text and pointer. This explicitly violates the proposed native-first production rule and needs a fresh native composition |
| HUD panels, slots, dividers, plates, tabs, shop rows, pause frames | **51 8×8 UI kit tiles**, `ui_kit.py` | `ui.c` procedural nine-slice/frame layouts; `text.c` HUD/shop/dialogue; `menu.c` bag/key pages/maps; `game.c` win screen |
| Hearts and contextualR hand | **4 8×8 HUD tiles**, separate HUD palette | `text.c`; hearts, half-heart, empty-heart and hand. These are not the `pick32` ground heart frames |
| Text face | **97 glyphs** (ASCII32…128),9 rows each; visible letter widths 1–5 px,3 px space,1 px tracking | `ui_font.py` → packed `vwf_w`/`vwf_bits`; `vwf.c` rasterizes to BG or OBJ canvas. Dialogue, shop, inventory descriptions, title prompts and win stats all use it |
| Speaker/shop portraits | Six 48×48 faces padded into 64×64 OBJ frames; per-face 16-colour palette | `faces.py`; `text.c` fixed portrait tile 944 and face slot. Portraits must be redrawn with the same characters as overworld bodies |
| Bag/key-item illustrations and HUD equipment | `icon32`32×32 frames; exact per-frame menu palettes plus four world/HUD palette banks | `objects.c` seven-slot LRU tile/palette cache; `menu.c`, `text.c`, player item-get. Redrawing world pickup size does not require shrinking inventory illustrations |
| Overworld and zoomed pause maps | `marks`, `dots`, UI corners, UI map palette; map pixels are generated from world state | `menu.c` procedural room thumbnails, gate/event marks, fog, cursor and legend; `text.c` HUD minimap 16 tiles at 1008 |
| Dialogue panel, shop, death-return text, completion screen | Reuse the UI kit, VWF font, portraits and item sheets | `text.c`, `npc.c`, `game.c`; they have no independent background PNG that can be overlooked |

## Why the current pipeline produces mixed styles

Background declarations pass through up to nine visual owners: base hex art,
style-board remapping, optional comparison-pack replacement, illustrated tile
atlas, `wood_art`, environment pack, native forest painter, imported blight
atlas material, healthy rematerialization, and final interactive painter. The
Drain follows an entirely separate painted-scene cutter. Palettes undergo
another sequence of merging, added groups and semantic recolouring.

Sprite declarations load an imported pack, then enemies, clean-item silhouettes,
Bloom bodies/effects, screenshot-derived item/shield art, lifted-object material
copies and enlarged interactive props. These painters use different assumptions
about scale, value ramps, texture density and silhouette. No coverage manifest
requires them to agree. Native-resolution later patches cannot by themselves
unify these competing source languages.

## Minimal engine interface for a coherent smaller set

1. Use a 32×32 Bloom canvas with a deliberate 16×24-ish visible body, not a
   resize of the old image. A transparent 64×32 canvas could preserve anchors
   temporarily, but the fixed 32-tile body reservation would then stay larger
   than needed. Keep the original frame IDs/state durations unless intentionally
   redesigning gameplay.
2. `player.c` owns explicit anchors: body at feet minus halfcanvas/height,
   action FX at feet(−16,−32), north bow an additional−4, shield offsets,
   item-get illustration, load target(−8,−40) and shadow. Redesign these as one
   grip/feet contract; shrinking the body alone leaves disjoint tools.
3. `pick32` can keep its engine name while becoming a 16×16 sheet with 10 frames.
   `pickup_spawn()` takes its width/height from sheet metadata, so ordinary
   drawing centers automatically. Keep `icon32` separate for inventory/HUD.
4. Smaller overworld NPCs require explicit special-keeper anchor changes:
   merchant head at feet−48/body−32; keeper 64 px canvas and orb coordinates.
   Reusing these old component offsets would float compact redrawn faces.
5. Heart/boss growth needs residency planning. Its present three 32×32 frames
   load as 48 tiles together. Three 32×64 frames would load 96 tiles and exceed
   current headroom; stream one 32-tile frame instead if choosing a taller boss.
6. Room/UI fonts and layout constants are independent of sprite scale. Keep
   readable layouts, but redraw their source tiles/glyphs, palettes and icons
   under the same native rules. The user likes the current UI organization;
   wholesale UI structure changes are unnecessary.

## Single-owner pipeline recommendation

Use one new art-direction package with shared RGB555 master ramps, pixel
primitives, semantic material definitions and scale constants. Its dedicated
`paint_metatiles`, `paint_sheets`, `paint_ui` and `paint_title` entry points should
be the **only final owners**; older painters should not remain invisible final
fallbacks. Separate modules may implement materials, but they consume the same
specification and report to one package rather than stacking overrides.

The package should declare exhaustive coverage: every resident metatile ID,
every source sprite-frame ID, all UI tiles/marks/HUD tiles, all 97 glyphs, all
six portrait palettes, item exact-frame palettes and the title bitmap. Produce
a build report listing redesigned/retired resources and fail when an active
resource lacks an owner. Keep a native 1×1 review image for every asset and use
only integer nearest-neighbour enlargement for presentations.

Use this inventory as the pre-reboot coverage baseline. New art should be
reviewed at 240×160 first, with full scenes and animation contact sheets, before
judging enlarged detail. Preserve physical contracts separately from visible
bounds so decorative overhangs cannot silently change accessible ground.
