# Bloom action animation

The [mGBA review gallery](../../forest-review/bloom-animation/README.md) shows
the animation changes on generated forest ground. Bloom's original idle,
walking frames and palette are retained.

## Body and prop layers

`art/bloom_animations.py` overrides the imported action bodies after the pack
is loaded. Rolls keep a single connected tumbler with an aligned baseline;
detached leaves, speed strokes and baked gray shadows are removed. Attack,
guard and carry bodies contain no baked weapon, leaf shield or barrel.
Nine tool-use poses and nine cape poses add short changes in stance and arms.

`art/bloom_fx.py` supplies a separately anchored 32×32 layer. One frame uses
16 OBJ tiles, streamed as needed. The steel blade and leading crescent move
across the swing while a subdued outer sweep retains its full reach. The
effect draws before the body in OAM, keeping northward swings visible over
the back of the flower. The cape draws behind the body. Tools use the hand
anchors documented in the body module; west mirrors east.

## Sword contact and timing

Rendering and `player_sword_box()` share `sword_bounds()` in `player.c`.
Bounds are inclusive, relative to Bloom's feet:

| Facing | Left | Top | Right | Bottom |
| --- | ---: | ---: | ---: | ---: |
| North | −14 | −32 | 13 | −12 |
| East | 4 | −22 | 22 | 2 |
| South | −14 | −6 | 13 | 12 |
| West | −23 | −22 | −5 | 2 |

The dim sweep marks those extents; the southern cutting area has an 8px
inset within its effect canvas to leave room above it for the grip. Enemies,
pickups, reflected projectiles and cuttable brush all use the same live box.
Contact uses the target's hitbox, so its centre can lie outside the sword's
extent while its edge is struck.

The attack lasts 15 displayed frames: two anticipation frames (ages 0–1),
eleven live frames (2–12), and two recovery frames (13–14). The former input
frame could deal an invisible hit, turn off, then become live again; this
discontinuity is removed. Range and damage are retained. Body contact can
interrupt anticipation, which the frontal-hit regression now accounts for.

## Other items

Bow, candle and bomb use have transient visual timers outside `PlayerState`
and save data. They do not freeze movement or alter resource/cooldown rules.
Turning or entering another action cancels the held-tool pose. A successful
bow shot shows the held bow and release; an empty bow does not play a shot.
The candle has a visible held flame as well as its existing burning effect.

The planted bomb itself passes from the hand to the ground over eight
frames; it has no duplicate held sprite. Its clean item art alternates with
a lit frame as the fuse runs. Its physical placement and 150-frame fuse are
retained. Carrying draws only the actual load; lifting eases into its held
position, and throwing has a brief body follow-through. Cape jumps have
takeoff, tucked airborne and landing poses. Guards hold the wooden shield.

The extra action layer exposed an existing OBJ allocation problem after
opening the menu and using more tools. Inventory/reward icons now share an
eight-frame LRU cache instead of retaining the full large-icon sheet.
Menu map markers resolve their tile bases through the allocator after each
room reset. Artwork and palette slots are unchanged by this cache fix.

## Reproduce

```sh
source /workspace/setup/activate.sh
make -j4
python tools/bloom_probe.py --out /workspace/art-review/bloom-checks.json
python tools/bloom_budget.py --out /workspace/art-review/bloom-budget.json
python tools/bloom_review.py /workspace/art-review/bloom
python tools/wood_probe.py
python tools/lift_probe.py
python tools/guard_probe.py
python tools/menu_probe.py
python tools/critical_path.py --seed 0xB4A7 --boss
```

The review tool supports `--rom`, `--map` and `--assets-header` for a matched
older build. Actions come from real button inputs; inventory, positioning
and cleared actors are fixtures. The review never assigns an animation pose
or changes generated terrain. Native PNGs are unmodified 240×160 frames.
GIFs sample every other video frame with alternating 30/30/40ms delays.
