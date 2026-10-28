# Native art reboot: implemented build

This replaces the active visual pipeline for the whole current game. It is
not an overlay of new props on the previous packs. The Drain hub, healthy and
progressively blighted forest, interiors, Bloom, enemies, NPCs, Heart, drops,
held equipment, interactive scenery, title and interface now use the selected
verdigris/earth/brass vocabulary.

The [actual mGBA gallery](../../../art-review/reboot/README.md) and its
[release validation](../../../art-review/reboot/validation/summary.json) identify
the exact published ROM. Design studies are labelled source mockups, never
presented as emulator evidence. Start with the [research](RESEARCH.md),
[mockup critique](MOCKUP_CRITIQUE.md) and [nine-area art bible](ART_BIBLE.md)
for the decisions that precede this implementation.

## One source of visual rules

`reboot_core.py` owns RGB555 inks, material ramps, top/near-side planes, contact
shadows and shared native shapes. The terrain, actor, item and interface
modules build from those roles. `tiles.py` and `sprites.py` assert complete
ownership; there is no previous-pack fallback. The Makefile does not depend
on the old importers, JPEGs or reference sprite sheets.

All 913 original metatile names/IDs, physical types, collision flags, property
bits and animation frame counts/speeds retain their metadata contracts. The
Drain’s 30×20 grid retains its ground/overlay/object records. These contracts
are metadata in `reboot_contracts.json`, not preserved pictures.

All 354 original sprite frames are owned by native generators. Seventeen
small HUD items and six glitter frames bring the total to 377 frames across
34 sheets. The source coverage report also names the 51 interface tiles,
four HUD tiles, 97 glyphs, six portraits and native title. Every listed family
has an authoring module, including compatibility entries not currently drawn.

Two transparent `none` frames and a blank menu illustration remain blank.
Uniform black/pit fills remain uniform. Nine lowercase glyphs and ten simple
space/punctuation/symbol primitives retain their basic bit patterns; four
straight interface line/join tiles retain their geometry. They have new
ownership and palettes. This is deliberately not a claim that every possible
primitive bit pattern must change to count as a redesign.

## Scale, performance and contact

| Category | Implemented native size |
| --- | --- |
| Bloom | Ordinary body about 14×22; action hands up to 18×24; legal 32×32 canvas. |
| World drops | Commonly 10–14px, maximum 16×16; sheet name `pick32` retained for identifiers only. |
| HUD equipment | Dedicated 16×16 drawings in the 24px-high HUD. |
| Inventory and raised rewards | Usually 24–28px within 32×32; distinct from world drops. |
| Chests | About 20×19 closed, up to 20×22 open; wood, brass and relic tiers. |
| Entrances | About 31–32×42–46 in 32×64 hardware canvases. |
| Shields | About 10×12 front/back and 6×12 side, with a visible far-side north rim. |
| Drain keepers | Compact world figures, roughly 20×27 including hat/orb; portraits stay separate. |
| Heart | Main organ about 28×36 with arteries reaching 32×52 in 32×64. |

Bloom uses feet at bottom-centre, a 12×20 hurt box centred 11px above the feet,
and a 10×8 ground footprint centred 4px above them. Stable painted 18×24 extents,
rather than transparent canvas margins, control ordinary actor depth. The
Heart has its own 28×40 contact box and 32×50 depth extent. Arrows have a 6×6
contact box aligned with their actual raised sprite and wall checks.

These are intentional physical changes. The save structures, generated world
records and progression contracts remain stable; it would be incorrect to
claim that all old per-frame combat/collision traces are identical.

Held tools use explicit directional hands, shared with their source painters.
Carried objects use the same native design/palette as the ground object. The
held load and first thrown frame preserve the same screen origin at 24px
height. Shadows stay on the ground during jumps. North sword/shield/lamp
composition is checked against the actual head silhouette.

The sword has a fixed roughly 14px blade, a short local tip trail and five
poses. The 15-update action retains two anticipation updates and 11 damaging
updates, followed by recovery. Generated `bloom_sword_origin` and
`bloom_sword_hit` arrays come from the blade’s cutting mask for each facing
and pose. Guard, hilt and proximal blade are excluded. Damage uses inclusive
AABBs from that mask, not per-pixel contact. The former static wide rectangle
and cage-like envelope are removed.

The HUD keeps the familiar menu/slot hierarchy and reduces its true hardware
height from 32 to 24 pixels. HP and currency changes redraw the same native
vitals panel; release validation separately measures damage-to-replacement-OAM
latency so good quiet-scene timing cannot hide a slow dirty-HUD update.

## Terrain and glitter

Quiet walkable floors separate characters from the environment. Clustered
cool canopy, warm paths, dark bank faces and small verge breaks share one
perspective. Healthy-to-blighted transitions change anatomy and material:
exposed roots, bare limbs, sick pools, cracked stone and wet fungal growths
retain occasional brilliant flowers and glints. The Drain uses the same inks
and construction, with corroded copper, stained masonry and scum beside brass.
Cave, hollow and thicket floors have their own materials without noisy
wallpaper patterns or opaque black squares beneath glow overlays.

Interactive objects use a shared vocabulary: whole heavy boulders, branching
fractures for bombs, pale connected silk for fire, recessed dark pits, broad
plates with distinct states, clear chest lids/latches and tall framed doors.
The ladder to the forest has an explicit stone threshold and brass rungs.

Glitter is abundant but attached to eligible wet, metallic, leafy and decayed
surfaces. `ambient.c` caches up to 1024 sites and samples at most 24 potential
sites in a viewport with staggered half-duty cycles. Six 8×8 source frames
include sparse points and occasional larger ivory/gold crosses. It consumes
neither ordinary actor slots nor world RNG. Depth distinguishes ground from
raised surfaces; the HUD area is excluded. The old six wandering firefly
actors are retired so they cannot float over the interface.

Representative recorded 192-frame action samples show about 11–12 visible
ambient glints on average, with 24 potential sites and small staggered peaks.
Those quiet/isolated action samples are not a worst-case combat benchmark;
the release publishes their exact counters and separate HUD contact samples.

## Packed hardware budgets

| Area | BG 8×8 tiles / 1024 | Resident metatiles | Animated metatiles | World banks |
| --- | --- | --- | --- | --- |
| Forest | 693 | 376 | 59 | 8 |
| Drain | 532 | 370 | 38 | 1 |
| Mystery interiors | 114 | 97 | 6 | 5 |

The title is authored directly at 240×160 using 27 shared RGB555 colours. All
sprite canvases are valid hardware shapes. The source catalogue contains 4497
sprite tiles, not simultaneously resident tiles. The 582-context allocation
sweep peaks at 716 of 876 available dynamic OBJ tiles, leaving 160 tiles. Current
banks/streams and all animation uploads are verified against the built ROM.

## Actual review and verification limits

The canonical review records 171 cases: 40 screen clips, 91 Bloom action clips
and 40 interactive scenery clips. It covers all 25 forest cells, three Drain
views, every interior style, five ordinary enemy species, the Heart, death,
return and victory. Separate captures cover the title, six HUD states, menus,
shop, maps and all six dialogue portraits. A supplementary camera view shows
the complete Heart rather than only its lower edge.

Cases use real mGBA runs and ordinary buttons. Seed selection, position,
facing, inventory/healing and removal of unrelated enemies are disclosed
review fixtures. Generated terrain and mystery descriptors are not painted
over. Special enemy-contact fixtures are labelled. Native PNGs are exact
240×160 framebuffers. GIFs enlarge with nearest neighbour; where a whole clip
exceeds 256 colours the GIF is quantized, while the supplied PNGs remain exact.
The MP4 is a lossy convenience copy. Source atlases are decoded assets, not
screenshots of gameplay.

The action union selects 99 of 101 Bloom frames. The redrawn legacy `jump_n`
and `jump_e` descriptor entries are not selected by the current renderer;
cape jumping uses the cape family, and swallowing uses `jump_s`. Unimplemented
swimming/sprinting and unused enum states are not claimed as reviewed gameplay.

Verification includes native coverage/palettes/VRAM,96 inside/outside sword
edge contacts, action interruptions, first replacement OAM after hurt,
lift/throw continuity, pickups, portals, all mandatory trials, item pockets,
quests, saves and 625 generated-room traversal checks across 25 seeds. Consult
the release reports for the measured counts and hash, and
[probe notes](PROBE_NOTES.md) for fixture and latency methodology.

## Extending the remaining eight areas

Use the adaptation sheet in the art bible before drawing. Retain Bloom’s
scale, foot/hand anchors, shared ivory/gold and interaction shapes. Change
materials, ecology, architecture and each area’s filth/glory pairing. Do not
introduce another independently shaded sprite pack. Build one native room,
critique it at 1×/grayscale, pack it under the measured budgets, and record real
actions on its floor before expanding it into a full area.
