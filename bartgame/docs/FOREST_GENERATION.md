# The wood: routes, trials and terrain

The maze is still a seeded 5×5 grid. A room's geography is derived from its
seed/cell, while its progression stage says which barriers lie before it.
All three item barriers remain unavoidable on the route to the Heart.

## Pacing a run

`world_generate(seed)` uses the balanced profile. Developers can call
`world_generate_tuned(seed, &world_profiles[WORLD_FOCUSED])` (or BALANCED /
WANDERING). The knobs are in `WorldTuning`, in `src/world.h`:

| Profile | Required room crossings | Minimum off-spine reward detours | Minimum optional rooms |
| --- | --- | --- | --- |
| Focused | 18–24 | 1 | 6 |
| Balanced | 24–32 | 2 | 4 |
| Wandering | 25–34 | 3 | 3 |

These count a shortest lock-free route from entry through the three rewards
in order and on to the Heart, including returns from branches. They do not
count time fighting, walking inside a room, optional looting, or getting
lost. A player can therefore take much longer. The candidate graph includes
same-stage loops, and keys can sit in branches of branches. Branch depth,
route length and optional cells are scored together; distance is not just
the direct entry-to-boss path.

Generation is bounded (24/32/64 candidates by profile). If none fits a named
profile, a certified graph is used with the player's seed retained for room
composition. This rare fallback preserves the pacing and optional-room
contracts without an unbounded loading loop. Arbitrary custom tuning can be
infeasible and is best effort. `world_route_metrics()` exposes the selected
route metrics; the debug symbols `gWorldGenerationAttempts` and
`gWorldGenerationFallback` expose the bounded search.

## Earn the three keys

Each required reward has a guaranteed reachable medium mystery room before
its barrier. There is no free key-item chest in the forest:

1. Floor plates reward Blightseeds, which break cracked masonry.
2. A wave fight rewards the candle/lamp, which burns silk and brush.
3. A guardian fight rewards the Petal Cape, which crosses chasms.

The starting sword is sufficient for all three trials. Required trials allow
retreat; an earned but unclaimed chest survives leaving and returning. Each
item grants once. Optional combat mysteries retain their sealed-until-won
exit. No mandatory reward is placed in an optional item-gated pocket.

## Rooms and wayfinding

Clearings have rounded boundaries around reserved through-routes. Water
follows a continuous watershed, with a connected basin where space allows.
Crossings follow paths and reserve dry landings against later dressing.
Terraces have ramps and waterfalls rather than isolated arbitrary ledges.

Dirt is a suggestion. Some junctions have an overgrown exit lane; other
trails turn toward optional loot instead of the next mandatory barrier.
The traversable lane remains protected even when its dirt is absent. Thus
an attractive path can be a detour without the alternative becoming a
pixel-hunt or an impassable secret.

Optional pockets are enclosed glades with a cracked, webbed, or two-tile pit
neck. Their hoards can be seen before the relevant item is owned. Bomb and
candle openings persist; pits remain jumpable with the cape. Taking the
hoard persists independently. RoomSpots appends pocket coordinates/kind
without changing existing field offsets. The original World/Cell save
layout is retained.

Healthy oaks, birches and firs give way to diseased trees, sick ground props,
rot, and then dead woods. The Heart arena adds luminous rot veins. Native
4bpp art, shore/trail edge families and shared material colours blend the
surfaces while preserving collision silhouettes.

## Saves and validation

Version-1 saves migrate to version 2 without discarding inventory, the
existing maze, opened gates, loot, or counters. Unclaimed key rewards become
trials; owned rewards remain owned. Already won but unclaimed new trials
survive save/load as well. A corrupt checksum is rejected.

```sh
source /workspace/setup/activate.sh
make -j4
make verify-world
python tools/roomgen_probe.py --seeds 0xB4A7,0xDEADBEEF,1,7,42 --out build/room-report.json
python tools/mandatory_trials.py --seed 0xB4A7
python tools/pocket_probe.py --seed 0xB4A7
python tools/critical_path.py --seed 0xB4A7 --boss
python tools/myst_probe.py
python tools/generation_review.py /workspace/art-review/generation --seed 0xB4A7
```

The host suite independently checks gates and reward reachability across
19,999 seeds, and all three pacing profiles across 5,000 seeds each. The
mGBA room validator reads collision quarters from the ROM, checks every
exit and required approach, both bridge banks, and correct-item-only pocket
access. Runtime probes actually solve trials, use bombs/fire/jumps, take
rewards, revisit, and fight the Heart. Capture JSON records a ROM digest and
the actual seeded route; PNGs are native mGBA framebuffers with debug room
navigation, not externally composed scenery.
