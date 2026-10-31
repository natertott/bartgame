# Forest concept asset inventory

This is a **read-only scope audit**, dated 2026-10-31, for five exploratory
forest environment treatments. It does not adopt a concept or change pixels.
The current brief keeps green grass and brown earth visible through deep
blight; corruption should primarily change canopy, branches, vines and flowers,
with restrained floor detail. Bloom, the selected enemies, interface, item
icons, Drain and existing glitter are comparison context and remain protected.

The audit follows the root `AGENTS.md`, [art bible](../ART_BIBLE.md),
[direction log](../ART_DIRECTION_LOG.md) and [reference register](../REFERENCE_REGISTER.md).
It makes no new external research claim. Source-backed art guidance remains
in the existing six PDF notes and application matrix; the current user brief
supersedes the old purple-floor progression for these studies.

Baseline game/art source is the selected-enemy release, ROM SHA-256
`9330a44a4e27d99606a757134aa41a62adb122a74315c400e1ad3427048c8661`.
Inventory was measured at git HEAD `31b31513f354d9ead6577166d72fa06dad71358b`.
Defaults are Drain9, Step-and-cut3 and selected enemy11. The complete machine
manifest is `/workspace/setup/forest-concepts/inventory.json`; it records
all IDs, names, per-frame palettes, native extents, source hashes, ownership,
physical metadata, area residency and direct C references. Arithmetic group
placement means a direct-reference search alone is not a coverage test.

## Exact scope and packing

| Resident set | Logical metatiles | Authored frame instances | BG subtiles / 1,024 | Banks / 12 | Animation allocations / 255 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Forest | 376 | 437 | 693 | 8 | 59 |
| Cave/hollow/thicket and event extras | 97 | 104 | 114 | 5 | 6 |
| Selected final Drain | 657 | 1,554 | 822 | 1 | 69 |

Forest and interiors share ten metatiles / thirteen frame instances, giving
**463 distinct environment IDs and 528 source frame instances**. The shared
names are `moss0`, `moss1`, `moss2`, `boulder`, `torch`, `torch_lit`, `chest`,
`chest_open`, `sparkle` and `black`. These should have one authoring owner,
even though they are packed into two resident sets.

There are 1,570 total metatile IDs: the 463 environment IDs, 450 historical
Drain IDs and 657 selected final-Drain placement clones. None of the 463
environment IDs is resident in the selected Drain9 room. All 1,107 Drain IDs,
including the historical descriptors, are outside this redesign. Preserve
their actual drawings, physical metadata and palette rather than relying on
the fact that many are currently invisible.

`tools/build_assets.py` owns the actual inclusion predicates: forest excludes
`sw_`, `swh_`, `cave_`, `hollow_`, `thicket_`, `myst_`; interiors include their
three style prefixes, `myst_` and the ten extras above. Drain uses the selected
room's expanded ground/overlay IDs. `art/tiles.py` generates the native base
then appends the final Drain clones from `sewer_final_contracts.py`.

## BG families to cover

Every frame is 16×16 with literal indices0–15. Composite pictures are authored
at the listed full native size and then sliced; do not independently decorate
their component cells.

| Family | Complete names / IDs | Construction and contract |
| --- | --- | --- |
| Healthy field | `moss0/1/2`, `moss_shade`, `tall_grass`, `moss_flowers/2`, `path`, `path_edge_n` | Nine quiet ground drawings, IDs0–10 excluding the two early-blight IDs. Grass and soil retain distinct material ramps. |
| Progression ground | `moss_blight/2`3–4; `blight_ground0..2`74–76; `blight_floor/2`, `blight_vein`; `forest_rot0..7`489–496; `forest_blight_vein0..7`898–905 | All must remain recognizable grass/earth under the new brief. Trace post-generation replacements as well as the original `sTrail`/floor choices. |
| Ground transitions | `shore_1..f`, `shore_c1..cf`; `verge_1..f`, `verge_c1..cf`; `pedge_1..f`, `pedge_c1..cf`; all47 `rot_*` IDs391–437 | Thirty per shore/verge/path family. Side bits1N/2E/4S/8W; `c` variants fill inner corners. `rot_` names use side and corner hex nibbles; the retained set has47 entries, not64 or256. Match terminal edge pixels across banks. |
| Connected walls | `canopy`, `canopy2`, `canopy_n/s`, `canopy_blight/2`, `canopy_lantern`, `canopy_glint`, `forest_canopy0..5`497–502, `blight_wall/2/lit`179–181 | Permanent connected masses with upper planes and darker hanging faces. All are retained scope even when a particular decorative variant is not currently chosen. |
| Ordinary trees | Oak19–24; `tree2_0..5`143–148; `birch_0..5`503–508; `fir_0..5`509–514; `sicktree_0..5`515–520; `btree_0..5`161–166 | 32×48 /2×3 cells. Four crown cells are overlays; two trunk cells use their own physical footprint. Birch trunk cells currently use stone while its crown uses foliage. |
| Great trees | `gtree_0..11`81–92; `gtree2_0..11`149–160 | 48×64 /3×4. Nine crown cells overlay the field, then a root/trunk row. The second family includes a lantern. |
| Corrupt tree extensions | `btree_6..11`167–172; `forest_blight_tree0..5`906–911; `dead_tree`, `forest_blight_dead_tree`897 | The six reserved `btree` extensions form48×32 and are not stamped by current generator calls; still cover their descriptors. The32×48 wall tree has six SOLID cells and differs physically from a free-standing tree. |
| Growing floor groups | `meadow_0..8`93–101; `clover_0..3`102–105; `shroomring_0..3`106–109 | Respectively48×48,32×32,32×32. Their repeated floor must join the common grass without a pasted rectangle. |
| Large scenery groups | `gboulder_0..3`110–113; `treerock_0..3`139–142; `hlog_0..1`114–115 | Native32×32,32×32 and32×16. Whole stone masses are permanent scenery, distinct from liftable rocks and bomb fractures. |
| Water and banks | `water`39; `water_1..f`40–54; `water_c1..cf`122–136; `water_lily`55; `water_foam`178; `waterfall`177; `raft_0..3`116–119 | Shared continuous liquid, near-bank face and visible fall/impact language. The32×32 raft group is logically WATER, not a bridge; preserve that surprising contract rather than making its drawing promise a safe crossing. |
| Crossings/elevation | `bridge/bridge_v`28–29; `ledge_s`, `ledge_n`, `ledge_s_w/e`120–121; `pit`, `pit_inner`, `forest_blight_pit`896 | Bridge art must lead between real banks. Pits need a dark cavity, ledges an exposed face, and walkable path edges neither. Do not replace water with a black pit or paint a step across a lethal tile. |
| Liftables | `bush`32, `rock_small`33, `boulder`34, `myst_pot`277 and each style's `floor_lift` | Pair with the exact four carried/thrown images described below. Heavy lift-only stone stays whole; ordinary liftable stone has no bomb-fracture cue. |
| Other solids | `fence`, `log`, `stump/sick_stump`, `rock/2/3`, `sick_rock`, `pillar`, `ruin_wall`, `statue`, `lantern_post`, `blight_crystal` | Permanent environment solids. Material clusters and contact shadows should distinguish them from bright interactive obstacles and transient pickups. |
| Flat details | `bones/sick_bones`, `mossy_stone`, `leaf_litter`, `fern_patch`, `relic`, `shrine_plate`, `sparkle/_white`, `blight_mist` | Not every bright detail is a pickup. Some FLOOR decorations have `prop=1` for underlay/depth handling; preserve that classification. |
| Temporary barriers | `thorn`30, `crack`60, `web`61, `door_locked/open`62–63 | Sword/candle-clearable thorns; bomb fracture; candle silk; key lock/open frame. Keep distinct silhouettes and truthful tool cues. Their transparent corners reveal an actual local floor. |
| Other interactions | `torch/lit`64–65; `chest/open`66–67; `mouth_cave/hollow/thicket`272–274; `stairs_down`73; `black`72 | Censers, logical treasure/portal fallbacks, region exit and closed void. Large treasure/portals are normally separate streamed OBJ; their logical BG fallback still needs coverage. |
| Damaging liquid | `blight_pool`11 | TypeHURT with no collision bits, unlike ordinary drowning WATER. Keep its hazard legible while retaining the surrounding field's green/brown ground. |

## All three interior styles

Each of `cave_`, `hollow_`, `thicket_` has **27 entries**: wall, face, crown;
floor0/1; edge1–f; prop; glow; exit; spring; and floor_switch/lift/chest.
That is81 style-specific entries, plus six `myst_` overlays and the ten shared
extras above. Their native rooms are12×9,18×12 or24×16 metatiles. All ten event
types remain in scope: pots, chest, NPC, healing spring, waves, survival,
miniboss, switches, torches and boulders. The last two use thicket material.

`src/myst.c:kStyle` resolves their function; `myst_ground()` selects the floor
edge beneath a cleared object. `myst_switch/down`, `myst_pot`,
`myst_chest/open` and `myst_spring` are explicit shared overlays. A glow or
ordinary floor on BG2 must include its opaque floor mass: transparent ink0
there previously produced black16×16 holes. Do not paint the healing spring
like the boss Heart or make trial-exit bars look like a permanent wall.

## OBJ, portraits and protected context

The current build has35 sheets /470 source frames. Numeric sheet IDs and frame
IDs in the machine manifest are the authoritative baseline.

| Scope | Sheet ID / native canvas | Frames / palettes | Runtime use |
| --- | --- | --- | --- |
| Environment treasure | `interactivechest`30 /32×32 | Six: wooden, brass, relic × closed/open; all `gear` slot9 | Stream one16-tile frame; actual closed art20×19, open20×22. The logical tile controls reward/collision. |
| Entrances/exits | `interactiveentry`31 /32×64 | Six: cave/hollow/thicket, then three closed states; cave `iron`4, organic frames `gear`9 | Stream one32-tile frame. Actual silhouette31–32×42–46, taller than Bloom; dark opening and threshold align to the existing logical entry/exit. |
| Forest people | `npc`12 /32×32 | `hermit`2, `nun`3, `gardener`4, plus retained aliases `sister_mary_grace`5 / `brother_mark`6; `folk` slot5 | Three live identities; Stranger reuses Hermit. Current painted extent19×24, feet at bottom row31. Sage0/Merchant1 are unused shared legacy fallback images and remain protected. |
| Matching busts | `face`23 /64×64 | Hermit3/Nun4/Gardener5; native drawing48×48 | Each portrait loads its separate `pal_face` bank into slot6. Keep the world/portrait identity coherent. Bloom0, Drain Peddler1 and Wizard2 remain exact. |
| Conditional shared lift identity | `lift`14 /16×16 | Bush0:`bugs`2; rock1/boulder2:`iron`4; pot3:`gear`9 | Four exact ground/carried/thrown images, bottom-aligned to16. Either keep all four unchanged or coordinate the entire BG→carry→throw family; this audit does not authorize changing their protected uses. |

The proposed environmental OBJ scope is20 frames: six chests, six entries,
five forest-folk source entries and three matching portraits. Four lift frames
are separately marked **conditional/shared** for the root scope decision.
Every other frame is protected comparison context: selected five enemy sets,
broken Heart and seed/weapon companions; Bloom/Step-and-cut and action effects;
world drops, HUD/menu/shop items, shields/arrows, UI marks/font, Drain actors,
their portraits and handrail, and existing glitter.

`mouth`16 is the **Drain Cap return effect**, not the cave/hollow/thicket
entrance. Preserve it. Tiny BG treasure/portal pieces are display fallbacks:
`src/interactive.c` reserves the streamed chest/entry allocation per room and
`src/room.c` suppresses the fallback when that allocation is ready. Redrawing
only the fallback will not change the visible chest or door.

Chest OBJ origin is `(tileX*16-8,tileY*16-16)`. Outdoor entry origin is
`(tileX*16-8,tileY*16-48)`; interior exit omits the horizontal−8 offset because
its original threshold spans two tiles. Preserve these anchors, depth rules,
transparent outer corners, logical footprint and approach clearance.

## Palette and sharing traps

Forest's physical BG order is ground, decay_mix, rot_water, foliage, blight,
stone, gold, water. Interiors use ground, stone, gold, foliage, water. The
Drain's area-local bank is separate. Add/substitute **concept-local BG banks**
instead of editing the global `reboot_core.PALETTES`; every area still fits
at most12 banks, each sixteen RGB555 colours including transparent0.

All sixteen physical OBJ slots are occupied. `bugs`2 also paints the cloak and
carried bush; `iron`4 paints held tools, arrows, stone and the heavy enemy;
`gear`9 paints equipment/loot/chests/organic portals; `items`10 holds the selected
small-enemy palette. Shared index names do not imply a palette can be freely
recolored. Keep OBJ banks invariant and paint concept art in their existing
inks, or have the root explicitly design and verify a scoped replacement.

Do not change these shared painters to implement a local forest treatment:

- `reboot_core.tree()` also supplies trees in the **title screen**.
- `reboot_core.portal()` feeds the current entry sheet and historical Drain
  ladder art. Final Drain9 has its own painter and must remain exact.
- `reboot_core.lift_object()` supplies both BG liftables and the carried/
  thrown sheet, and supplies related permanent rocks.
- `reboot_core.chest()` supplies both tiny logical fallbacks and large chests.

Use one concept-local environment owner with explicit wrappers for BG, entries,
chests, forest folk and paired lift art if authorized. Active authors are
`reboot_terrain`, `reboot_items`, `reboot_actors`, `reboot_ui`, with Drain,
selected enemies, Step-and-cut and UI profile overrides. Historical
`forest_art.py`, `forest_sprites.py`, `interactive_props.py` and image packs
are not the active production painter and must not become accidental fallbacks.

## Review and capacity checks

Keep metatile IDs/type/collision/prop and contiguous group ordering stable.
Collision bits are the four8×8 quadrants, **not** the cardinal mask used for
edge variants. Preserve local underlay and overlay behavior: `prop` affects
depth, and the glitter flag selects reflective surfaces. Decorations must not
silently become barriers or change ambient-glitter coverage.

The present conservative full enemy/prop/menu union is816/876 playfield OBJ
tiles, leaving60; chest/entry streaming is already included. Background artwork
has331 forest subtiles of headroom and910 interior subtiles, but animated
metatiles reserve four independent subtiles each. Current exact whole-animation
sharing applies to the final Drain only, not automatically to new forest art.
The last measured maximum linked EWRAM is212,184/262,144 bytes. Re-measure all
of these after integration rather than treating source-frame counts as VRAM.

Review five complete native source atlases, source assemblies and actual mGBA
captures separately. Include every healthy-to-deep stage, all masks and compound
groups, water/fall/bridge/ledge contacts, each blocker against both fields,
treasure tiers/open states, entrances and closed trial exits, all three interior
styles/event families, folk/busts, and the fixed Bloom/enemies/UI in context.
Verify the final built identifiers, physical contracts, shared assets, palettes,
animation allocations and actual rendering against the frozen baseline. Coverage
means every retained asset is accounted for; it does not claim every descriptor
is activated in a finite procedural run or that a passing hash proves good art.
