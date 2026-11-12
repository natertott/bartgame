# BARTGAME

An original Game Boy Advance action game: Bloom, a small flower-and-root
wanderer, lives in the Drain and explores the Blighted Forest and Curdled Cream.
Both regions generate a different puzzle each run.
The influences are *The Minish Cap*, *Slay the Spire*, Bataille and Boorman’s
*Excalibur*: wet filth beside brilliant brass, decay beside exquisite flowers,
and plenty of glitter.

The current **native art reboot** replaces the active graphics pipeline.
Start with the [actual mGBA gallery](../art-review/reboot/README.md),
[playable downloads](../downloads/README.md),
[art bible](docs/art-reboot/ART_BIBLE.md) and
[implementation notes](docs/art-reboot/IMPLEMENTATION.md).
Historical `forest-review` galleries describe earlier builds.

Bloom now uses the selected **Step-and-cut** sword swing: whole-body weight
transfer, a four-update preparation, seven damaging updates and seven recovery
updates. Body, blade and damage bounds share one clock in every facing.
The [five comparison studies](docs/SWORD_STUDIES.md) remain available explicitly.

[The selected interfaces and enemy studies](../art-review/appearance-enemy-studies/README.md)
include title Options, a fixed Winebound HUD, Workbench inventory, event-labelled
regional/chamber maps, and sixty animated enemy alternatives. Menu/dialogue
frame style and colors are selected independently and persist between runs.
Normal builds use the final Drain9, UI6/MENU1 and the
[selected enemy set](../art-review/selected-enemies-heart/README.md): Coin Toad,
Quill Moth, Trumpet Bellflower, Pear Bladder, Moth Confessor and a new purple
Heart broken down the middle (`BART_ENEMY=11`). Explicit `BART_ENEMY=0..10`
builds retain the earlier comparison sets. Earlier
[Drain concept studies](docs/SEWER_CONCEPTS.md) remain available.

Five optional [forest environment studies](docs/FOREST_CONCEPTS.md) explore
Fern & Oak, Silver Willow, Copper Beech, Velvet Cedar and Pale Orchard.
`BART_FOREST=1..5` selects their complete terrain, props and forest folk;
ordinary builds use the refined repeated-tree forest (`BART_FOREST=32`).
The [room-composition review](../art-review/forest-room-cohesion/README.md)
shows matched generated rooms, native details, movement and water clips, plus
a playable ROM. The approved twelve tree drawings remain unchanged.
`BART_FOREST=0..31` retains historical forest profiles for comparison.
The normal `BART_HUD=1` adds larger native item pictograms, A/B/L press
feedback and a blinking gold-framed minimap. `BART_HUD=0` reproduces the
earlier compact HUD and item paintings; use it with historical forest
profiles when comparing their original ROM bytes. Menu/dialogue appearance
options remain independent. See the [HUD and item review](../art-review/hud-gilt/README.md).
The [second forest pass](docs/FOREST_CONCEPTS_V2.md), `BART_FOREST=6..10`,
explores much stronger purple infection, new characters and props, adjacency
joins and true foreground canopy/underpass depth. Earlier studies remain
available; [topology notes](docs/FOREST_TOPOLOGY.md) track the ongoing engine/art work.
The [five playable ROMs, actual recordings and native catalogs](../art-review/forest-concepts-v2/README.md)
keep source assemblies and deliberate renderer diagnostics clearly labelled.

Eight [leafy canopy studies](docs/FOREST_CANOPY_V3.md), `BART_FOREST=11..18`,
retain accepted grey ground and rebuild healthy/infected tree crowns around
horizontal boughs and surviving green leaves. Their conditional renderer
preserves a visible portion of Bloom's current native pose beneath foliage.
[Actual mGBA comparisons and all eight ROMs](../art-review/forest-canopy-v3/README.md)
remain unselected alternatives; earlier profiles0–10 retain their exact ROMs.

## Performance

The [performance diagnosis](docs/performance/README.md) and
[measured mGBA review](../performance-review/README.md) document the optimized
engine without reducing artwork, enemies, effects or mechanics. Normal builds
use `PROFILE=0`; `PROFILE=1` is development-only cycle accounting.

## Cream environment studies

[Five polish variations and15 ladder studies](../cream-polish-review/README.md)
extend the review with finished rock silhouettes, projecting drop sills,
wall-connected shade, paired ladders and animated blue1–3tile waterfalls.
Build optional profiles with `BART_CREAM=7..11`. Earlier0–6 remain selectable;
production0 and the previous6 ROMs reproduce exactly.

[Fractured Rind synthesis](../cream-depth-review/README.md) combines the selected
study2 contrast/arches with study3/5 rock structure and study5's exact palette.
`BART_CREAM=6` fits unequal native cliff pictures and broad backing into the
generated room, distinguishes blocked rims from real drop sills, and shades
actual landing coordinates. The gallery includes ordinary live short/four-room
drops and registered room surveys. Default0 and studies1–5 remain selectable.

[Five new native material directions](../cream-art-review/README.md) add shelf
depth, clear climbing grips, stronger interactables and structural corruption.
`BART_CREAM=1..5` builds the review alternatives; default0 retains the existing
production art. Matched actual mGBA room mosaics and ordinary live climb clips
keep review rendering separate from gameplay footage.

## Current game

The Drain is the hub, with the Billious Peddler, Pale Gatekeeper and a
stone-framed, brass-rung ladder to the forest. The Forest and The Curdled Cream
are the first two regions of nine; seven future regions remain unspecified.
The second wall ladder repeats the Forest ladder's selected artwork and leads
to Cream. See the [regional handoff release and actual mGBA views](../regional-handoff-review/README.md)
and the [complete handoff ledger](../docs/handoff-restoration/AUDIT.md).

The Cream is a separate 5×5 directed climbing puzzle: two terraces per room,
upward climbs, lateral connections, caves and committed one-to-four-screen
descents. Three earned tools unlock its summit route. The boss occupies a
random top-row peak. Its original native terrain and actors append to the
existing art pack. Restored events, seven rotating quest forms, certified
puzzle boards, fusers, physical mechanisms and useful crossings now belong to
the generated regions and their cave, hollow and thicket interiors. The old
invented Annex selection hub is absent from normal exploration; its scene IDs
remain internal for save compatibility. Select from the existing pause screen
opens the expanded Satchel; R resolves the current region's atlas.

New runs offer three rounds of starting gifts. Physical Drain services supply
rolled wares, three priced rests, a fusion-location broker, route hints and
Trophy preferences. Both regions host escalating waves and once-only initial
rewards. Four live regional objectives provide an additional Earth Element win
route, with the final seal requiring three actual Forest or Cream trials.
The original Heart and summit victories remain available. See
[events and run flow](docs/handoff-restoration/EVENTS.md),
[regional placement](docs/handoff-restoration/REGIONAL_CONTENT.md) and
[mechanisms](docs/handoff-restoration/REGIONAL_MECHANISMS.md) for the precise
adaptations and their verification scopes.

The forest is a seeded 5×5 maze with a balanced target of 24–32 required room
crossings. Three required trials award Blightseed Bombs, the candle/Grail Lamp
and Petal Cloak before their corresponding cracked wall, web and chasm gates.
The route includes reward detours and optional branches without requiring all
25 rooms. Side locks use small keys; mandatory rewards remain reachable
without spending those keys. Item-gated pockets give reasons to revisit rooms.
Paths offer clues and occasional detours; tool/barrier meanings stay reliable.
See [forest generation](docs/FOREST_GENERATION.md) for the generation rules.

Caves, hollows and thickets contain treasure, healing, merchants, fights,
floor plates, censers or lifting puzzles. Forest strangers offer quests.
The deepest room contains the Blight Heart; defeating it releases the Grail.
Death saves a resumable run to SRAM; victory retires the completed run, so the
next play starts a new seed. Extended gear, both regional maps and preferences
use a separate checksummed save extension, retaining the earlier save format.

## Controls

| Button | Action |
| --- | --- |
| D-pad | Walk. |
| A | Use assigned item; talk to the person Bloom faces. Initially empty. |
| B | Use assigned item. Initially the sword. |
| L | Use/hold assigned item. Initially the Bark Shield; guarding fixes facing and slows walking. |
| R | Roll while walking; lift while standing; throw a carried object. |
| Start | Open/close the item, key-item and map pages. |
| Select in pause | Open the expanded Satchel; A/B/L assign, R opens its atlas, Select returns to the original pause. |

Assign items to A/B/L in the pause menu. The sword cuts bushes, gathers nearby
hearts/coins and reflects seeds. Hold and release the bomb button to throw:
a tap drops at Bloom's feet, half a second reaches 1½ tiles, one second caps at
2 tiles. Bombs explode on ground/wall impact. Bombs open cracked stone, the candle burns
webs/brush and lights censers, and the cloak jumps gaps. The bow uses arrows;
the Drain Cap returns Bloom to the hub. The Rot Gauntlet permits heavy lifting.
A sword swing while carrying drops the load. Approach a chest from below to
open it; walk into a locked door with a key. Push into a ledge to drop.
Water and pits cost a quarter heart and return Bloom to safe ground.

## Native art construction

Every active visual family comes from the same native generators, not imported
high-resolution sheets. Screens are 240×160, cells 16×16, hardware tiles 8×8,
inks RGB555 and world/sprite art 4bpp. The title is drawn directly at 240×160.

Bloom’s ordinary painted body is about 14×22 inside a legal 32×32 canvas.
World pickups are commonly 10–14 pixels in 16×16 canvases. Dedicated HUD icons
and larger menu/reward illustrations are separate drawings. All held tools
share explicit hand anchors with the body. Sword contact bounds are generated
from each live blade pose; the north-facing shield sits on the far side.
The compact top HUD occupies twelve rows, with a separate corner minimap;
only equipped ammunition is shown. Menus use the selected native frame kit.

| Source | Responsibility |
| --- | --- |
| `art/reboot_core.py` | Shared RGB555 inks, material roles, perspective and reusable native shapes. |
| `art/reboot_terrain.py` | Forest, progressive blight, Drain, interiors and interactive metatiles. |
| `art/reboot_actors.py` | Bloom, weapons/actions, enemies, NPCs, keepers and Heart. |
| `art/enemy_studies*.py` | Selected enemy dispatch plus sixty comparison alternatives, native companions and a dedicated small-enemy palette. |
| `art/enemy_heart.py` | Thirteen native poses for the selected broken purple Heart. |
| `art/sword_studies.py` | Selected Step-and-cut body/weapon poses, clock and contact geometry. |
| `art/reboot_items.py` | World drops, equipment, liftables, chests and entrances. |
| `art/reboot_ui.py`, `ui_font.py`, `ui_kit.py`, `faces.py`, `title.py` | Interface, native font, portraits and title. |
| `art/reboot_contracts.json` | Identifier/physics metadata only; no retained source pixels. |
| `tools/build_assets.py` | Packed C assets, palette/VRAM checks, sword geometry and coverage report. |
| `src/ambient.c` | Surface-attached, staggered glitter with bounded OAM use. |

`art/tiles.py`, `sprites.py`, `palettes.py` and `rooms.py` are strict integration
points. There is no old-art fallback. Older importers/reference sheets remain
in the repository as history and are not dependencies of `make`.
The [research](docs/art-reboot/RESEARCH.md) measures native Pokémon examples
and studies Minish Cap implementation details; no Nintendo graphics are used.

## Build

```sh
make -j4       # bartgame.gba
make assets   # generated C assets and build/gen/art-reboot-coverage.json
make clean
```

`make` selects Step-and-cut (`BART_SWING=3`), including direct asset generation.
Set `BART_SWING=1..5` explicitly to compare another study, or `BART_SWING=0`
for the previous sword. The animated step transfers weight without moving
Bloom's world position. Existing saves and item controls remain compatible.

Requires `arm-none-eabi-gcc`/binutils, Python 3 with Pillow, and the repository’s
`../tools/bin/gbafix`. This standalone game needs no commercial base ROM.

Code lives in `src/`; `gba.ld` places hot loops in IWRAM and maps in EWRAM.
Rooms use scrolling BG maps and per-area deduplicated tilesets. The actor pool
streams current sprite frames rather than keeping every source frame in VRAM.

## Verify and review

Runtime tools use mGBA’s Python bindings and inspect the built ROM by linker
symbols. Run `--help` for frozen-ROM/map paths and output options.

```sh
python3 tools/art_reboot_probe.py --help    # ownership, hardware and native scale
python3 tools/sword_study_probe.py --help   # selected sword timing, hardware poses and contacts
python3 tools/bloom_suite_probe.py --help   # broader actions; --skip-before omits historical trace comparison
python3 tools/critical_path.py --boss       # required progression through victory
python3 tools/wood_probe.py                # bow, gathering, reflection, hub return
python3 tools/lift_probe.py                # lift/throw and inventory controls
python3 tools/mandatory_trials.py               # earned mandatory rewards
python3 tools/art_reboot_review.py --help   # actual screens, actions and interactions
```

Capture tools disclose position/inventory/healing fixtures and keep native
240×160 framebuffer PNGs. Source mockups/atlases are labelled separately.
See [probe methods and limits](docs/art-reboot/PROBE_NOTES.md) and the gallery’s
release validation for measured budgets, tests, contact latency and ROM hash.
