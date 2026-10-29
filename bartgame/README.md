# BARTGAME

An original Game Boy Advance action game: Bloom, a small flower-and-root
wanderer, lives in the Drain and explores a different Blighted Forest each run.
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

## Current game

The Drain is the hub, with the Billious Peddler, Pale Gatekeeper and a
stone-framed, brass-rung ladder to the forest. The forest is area one of nine;
the other eight areas have not been implemented.

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
Death and victory save to SRAM, and continuing wakes Bloom in the Drain.

## Controls

| Button | Action |
| --- | --- |
| D-pad | Walk. |
| A | Use assigned item; talk to the person Bloom faces. Initially empty. |
| B | Use assigned item. Initially the sword. |
| L | Use/hold assigned item. Initially the Bark Shield; guarding fixes facing and slows walking. |
| R | Roll while walking; lift while standing; throw a carried object. |
| Start | Open/close the item, key-item and map pages. |

Assign items to A/B/L in the pause menu. The sword cuts bushes, gathers nearby
hearts/coins and reflects seeds. Bombs open cracked stone, the candle burns
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
The 24-pixel HUD keeps the familiar menu structure while freeing playfield.

| Source | Responsibility |
| --- | --- |
| `art/reboot_core.py` | Shared RGB555 inks, material roles, perspective and reusable native shapes. |
| `art/reboot_terrain.py` | Forest, progressive blight, Drain, interiors and interactive metatiles. |
| `art/reboot_actors.py` | Bloom, weapons/actions, enemies, NPCs, keepers and Heart. |
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
