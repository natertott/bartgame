# Optional enemy laboratory: validation method

The three prototypes are functional studies, not selected final enemy artwork
and not additions to the production encounter tables. Build with
`BART_ENEMY_LAB=1` to inspect them; the ordinary ROM uses `BART_ENEMY_LAB=0`.

`tools/enemy_prototype_review.py` runs the actual ROM in mGBA 0.10.5 and saves
unchanged 240×160 framebuffer PNGs, native GIFs, labeled filmstrips and a
per-video-frame JSON trace. The JSON records the ROM/source/tool hashes,
controls, positions, HP, AI phase/timers, collision, palettes, allocations,
projectiles and read-only lab event counters. GIF playback is checked against
the exact native samples and their intended frame durations.

Run from `bartgame/` after activating the configured toolchain:

```sh
source /workspace/setup/activate.sh
python tools/enemy_prototype_review.py \
  --bundle /path/to/frozen-lab-bundle \
  --out /path/to/review --backgrounds
```

The bundle must contain the matching `bartgame.gba`, `bartgame.elf`,
`bartgame.map`, `assets.h` and `source-commit.txt`. A failed assertion or
incomplete scenario makes the command exit nonzero. `--only` is for private
pilot diagnostics; final evidence must run the complete suite.

## What the suite establishes

| Scenario | Required actual observation |
| --- | --- |
| Gilt Leech | Acquires a cardinal line, tells for30 updates, charges at1.625px/update with heading locked after a player dodge, stops at a real floor/wall edge before its36-update timeout, begins36-update recovery. |
| Root Maw | Actual sword does no damage while buried. Emergence begins at least40px away on real dry floor, tells for24 updates, exposes a hittable/contact phase for180 updates, takes2HP from the sword, retreats and begins240 updates below ground. |
| Reliquary Snout | Real front sword and arrow create a clang without reducing4HP; real rear sword and arrow reduceHP by2. Tests use its ordinary locked windup, not an assigned AI phase. |
| Bomb phase checks | An actual bomb burns its full150-update fuse; a buried Maw retainsHP, whereas the8-damage blast kills a6HP exposed Maw. |
| Contact | Repeated overlap causes one2HP contact hit within22 updates; ordinary player invulnerability blocks repeated damage. |
| Mixed encounter | All three live AIs run with native one-update-per-video-frame cadence in the sampled healthy forest, sewer and deepest generated forest. |
| Graphics and menus | Prototype sheet payloads in OBJ VRAM match the ROM. Actors have nonzero tile allocations and their own expected palettes. Start/items/keys/overview/zoom/return work; a real bow shot consumes one arrow and retains its proper sheet/palette after menu closure. World allocations remain below HUD tile876. |

The source audit and proposal report separately distinguish inherited source
parameters from original adaptations. This finite suite does not establish
balance, route safety across every possible seed, or performance with the
maximum actor count.

## Disclosed fixtures

The lab selects a case through its own request API, clears unrelated actors,
grants a full inventory and80HP, and positions its actors on actual generated
floor. The review navigates real room transitions and uses coordinate-only
player/enemy placement to isolate direction, sword reach and collision tests.
It may set player facing, equipment and player health. All these actions are
recorded. Native AI waits and real button presses drive each action.

The bomb checks are damage-interface counterprobes: the target's coordinates
alone are placed into the real blast on fuse update149. Its current natural
buried/exposed phase andHP are preserved. These checks demonstrate damage
rules, not an unassisted player's combat positioning. The contact check
likewise intentionally repeats coordinate-only overlap without healing during
its22-update observation.

EnemyHP, AI state, timers, facing, flags, animation phase and pose are never
assigned by the harness. Room geometry, terrain, palettes, OAM, VRAM and the
framebuffer are never written. Native images are not re-painted or composited.
Filmstrip captions occupy separate pixels below each unmodified native frame.

Fixture setup performs bounded whole-room searches that can span several
video frames. The harness waits for the requested case, expected spawn count,
request consumption and three completed ordinary logic updates before it
starts an encounter recording. Setup/loading time is not presented as live AI
performance.

## Current evidence

The first lab build was piloted with all three prototypes and all three
backgrounds. The functional checks passed after correcting the harness to
wait for fixture setup and avoid contact-cancelling its front-sword input.
Those private pilot directories are not release evidence. The final frozen
bundle's `review.json` and media are the reproducible results; see the release
review index for their location and hashes.

Final source `ef63b92e3608805c60fddd2fbbb0b6c930e3033b` passes110/110 checks
across14 scenarios and2,952 video frames. The lab ROM SHA256 is
`ecc4c5effe2b1e872e9520387585ab0687ed8f3b634011b2a0076d226967d653`.
Mixed healthy/sewer/deep samples maintain one logic update per eligible video
frame; maximum world allocation is776 OBJ tiles, below the876-tile HUD boundary.
These finite samples do not certify arbitrary future enemy counts. The
[release index](../../../enemy-prototype-review/README.md) links the exact
recordings, trace archive and build inputs.

The final capture tool hash is
`9d0b5bf2ffe0b344c7907ec6b3cf23ddbfb577fbcf3380bbfcbe6e73fda53c8f`.
Its post-build revision adds ordinary camera-settling updates and closer bomb
escape fixtures so attacks remain visible; it changes no game code or ROM.
The original report preserves742 native PNG samples and14 exact-palette GIFs.
