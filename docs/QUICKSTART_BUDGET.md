# QUICKSTART budget: the measured walls

The F8 measurement pass (roadmap 8.2 step 5). Everything here is measured
on the real build in mgba, not estimated. Re-run the tools after any
change to rosters, spawners, bosses, or anything that loads a sprite;
quote this doc when sizing a feature ("a second boss costs N slots; we
have M").

## The hard limits

- **72 entities** game-wide (`MAX_ENTITIES`), everything included -
  player, items, effects, props, enemies.
- **44 GFX slots** (`MAX_GFX_SLOTS`, OBJ VRAM sheets): 4 permanently
  reserved for palettes, so **40 usable** for every sprite sheet on
  screen. This table, not the entity table, is what the overworld runs
  out of.
- `QUICKSTART_GFX_RESERVE` = 4: our own reaper deletes the farthest
  enemy when free slots fall below 4 - but only on one frame in 64, and
  spawn gates read counts that lag deletion, so transients below the
  reserve are real and measured (below).
- The GBA frame budget is ~280k cycles; when game logic overruns it the
  main loop misses VBlanks and the game visibly slows. `cpu_probe.py`
  measures this directly as the **lag ratio** (game frames per video
  frame, 1.000 = full speed).

## The tools

- `measure_budget.py` - per-region, per-difficulty peak entity/GFX sweep,
  plus `--combo id:form:count+...` to stage a boss + escort roster and
  price it.
- `gfx_trace.py` - per-frame GFX slot table sampling: sheet loads,
  lifetimes, refcount-0-to-freed reaper latency, zero-free windows.
- `cpu_probe.py` - the lag ratio + a host-time proxy per staged scenario.
  Run it alone; concurrent emulators pollute the proxy column.
- **The measurement mailbox** (`QuickStartMeasureMailbox`, game.c): 12
  bytes at `0x0203FF00` (magic `0x51534D42`, then id|form<<8|count<<16,
  then x|y<<16). The harness writes it; the game spawns raw
  `CreateEnemy` calls - no caps, no reserve gates - so probes can stage
  what the guards would normally prevent. Inert in play: one guarded
  compare per frame, at an address ~50KB above everything the linker
  places.

## Findings

### 1. The per-region sweep (difficulties 0/4/8/12, 900 frames, peaks)

    region                 diff  ents enemies kinds  gfx  free
    CASTLE_GARDEN            0    21    14      3    24    20
    CASTLE_GARDEN            4    42    35      3    24    20
    CASTLE_GARDEN            8    27    16      3    21    23
    CASTLE_GARDEN           12    21    14      3    28    16
    LON_LON_RANCH            0    45    26      3    31    13
    LON_LON_RANCH            4    59    40      3    33    11
    LON_LON_RANCH            8    39    16      3    36     8
    LON_LON_RANCH           12    34    11      3    39     5
    SOUTH_HYRULE_FIELD       0    43    26      3    21    23
    SOUTH_HYRULE_FIELD       4    57    40      3    28    16
    SOUTH_HYRULE_FIELD       8    33    16      3    22    22
    SOUTH_HYRULE_FIELD      12    45    16      3    36     8
    NORTH_HYRULE_FIELD       0    48    31      2    24    20
    NORTH_HYRULE_FIELD       4    57    40      3    27    17
    NORTH_HYRULE_FIELD       8    33    16      3    27    17
    NORTH_HYRULE_FIELD      12    27    10      2    34    10
    TRILBY_HIGHLANDS         0    25    18      3    23    21
    TRILBY_HIGHLANDS         4    33    26      3    23    21
    TRILBY_HIGHLANDS         8    66    54     11    30    14
    TRILBY_HIGHLANDS        12    47    16      3    38     6
    EASTERN_HILLS_SOUTH      0    20     9      3    14    30
    EASTERN_HILLS_SOUTH      4    20     9      3    11    33
    EASTERN_HILLS_SOUTH      8    23     9      3    17    27
    EASTERN_HILLS_SOUTH     12    25     9      3    26    18
    EASTERN_HILLS_CENTER     0    13    11      3    26    18
    EASTERN_HILLS_CENTER     4    17    15      3    30    14
    EASTERN_HILLS_CENTER     8    28    20      3    24    20
    EASTERN_HILLS_CENTER    12    61    15      2    31    13
    EASTERN_HILLS_NORTH      0    24    18      3    22    22
    EASTERN_HILLS_NORTH      4    32    26      3    22    22
    EASTERN_HILLS_NORTH      8    70    61     11    28    16
    EASTERN_HILLS_NORTH     12    46    16      3    37     7
    WESTERN_WOODS_SOUTH      0    10     8      3    25    19
    WESTERN_WOODS_SOUTH      4    16    14      3    24    20
    WESTERN_WOODS_SOUTH      8    21    14      3    32    12
    WESTERN_WOODS_SOUTH     12    20    18      3    29    15
    WESTERN_WOODS_CENTER     0     8     4      2    11    33
    WESTERN_WOODS_CENTER     4    13     9      3    12    32
    WESTERN_WOODS_CENTER     8    15     9      3    17    27
    WESTERN_WOODS_CENTER    12    17     9      3    20    24
    WESTERN_WOODS_NORTH      0    42    24      3    26    18
    WESTERN_WOODS_NORTH      4    42    24      3    22    22
    WESTERN_WOODS_NORTH      8    41    16      3    37     7
    WESTERN_WOODS_NORTH     12    70    53     11    37     7

  Tightest rooms at high difficulty: Lon Lon Ranch (5 free), Trilby (6),
  Eastern Hills North / Western Wood North (7). Anything new that loads a
  sheet in those rooms at difficulty 12 is spending the reserve.

### 2. Waves chain themselves, and the kind cap is per WAVE

  The 54-70-entity, **11-kind** peaks (Trilby 8, EH-N 8, WW-N 12, EH-C
  12) happen with the probe player standing still: enemies walk into
  water/pits, the wave reads cleared, and the escalating next wave spawns
  - each drawing its OWN kinds. `QUICKSTART_MAX_ENEMY_KINDS` bounds one
  wave; a session in one room accumulates the union of every wave's
  sheets, and only the reaper (slow - finding 4) trims it. Budget rule:
  size features against the multi-wave peak column above, not against
  one wave's roster.

### 3. Boss + escort pricing (the F6 shortlist, measured)

  Combos staged by mailbox at Castle Garden diff 8; "cleared" = region
  wave suppressed, "live" = on top of the natural wave. A chuchu boss
  family is 5 entities / ~4 sheets from a cleared baseline.

    combo                                   staging   peak gfx  min free
    green boss alone                        cleared      26        18
    blue boss alone                         cleared      26        18
    blue boss + 6 ice wizzrobes             cleared      32        12
    boss + 2 bomb peahats                   cleared      28        16
    boss + 4 sparks                         cleared      27        17
    blue boss + 6 ice wizzrobes             live, CG 8   42         2
    blue boss + 6 ice wizzrobes             live, NHF 12 44         0 (!!)

  The (!!) row: the table filled completely and **the boss family failed
  to spawn at all** (0 live pieces of id 19) - CreateEnemy could not fit
  its sheets. Rules that fall out:
  - An escorted boss must be priced against the LIVE wave of the hosting
    region at its difficulty, never an empty room.
  - Wizzrobe escorts (fresh sheets + ungated projectile sheets, the
    WW-N lesson) do not fit on top of a live high-difficulty wave.
    If F6 wants boss + wizzrobes, the wave must be despawned first
    (which F1's quest swap already knows how to do).
  - Bomb peahats and sparks are cheap escorts (2-3 slots over the boss)
    and stay affordable everywhere measured.

### 4. The reaper is slow by design - and measurably

  `gfx_trace.py` on the blue-boss-plus-wizzrobes combo: slots sat at
  refCount 0 for a **median 663 frames (11 seconds)** before being
  freed, and 4 slots were still waiting at trace end. Both reapers are
  throttled on purpose (vanilla compaction only on slot exhaustion, our
  reserve reaper 1-in-64 frames and only below 4 free), so a sheet that
  stops being used is NOT free capacity for ~10+ seconds. This is the
  mechanism behind two known facts: spawn gates read stale counts, and
  bumping the reserve does nothing. Natural-wave traces (SHF 8, WW-N 12)
  showed zero loads over 900 idle frames - all loading happens in the
  spawn burst, which is why the burst window is where failures live.

### 5. CPU: the lag ratio

  Measured solo, staged scenarios wave-suppressed via the room-flag-0
  latch pin (see cpu_probe.py for method; lag 1.000 = full speed,
  "live" = enemies still alive when the timed window ended):

    scenario                              lag      live at end
    empty room (wave killed+suppressed)   1.000         0
    natural wave, SHF diff 0              1.000        26
    natural wave, SHF diff 8              1.000        46
    natural wave, NHF diff 12             1.000        10
    1 acro placement, engaged             1.000         6
    2 acro placements, engaged            1.000         5
    3 acro placements, engaged            1.000        11
    4 acro placements, engaged            0.923         0
    6 acro placements, engaged            1.000        20
    green boss alone                      1.000         5
    blue boss alone                       1.000         5
    blue boss + 6 ice wizzrobes           1.000         9
    boss + 2 bomb peahats                 1.000         9
    boss + 4 sparks                       1.000         9
    boss + 12 keese (instance flood)      1.000        10

  Two solid conclusions and one honest limitation:
  - **Normal content never lags.** Every wave, boss, and escort combo
    measured - including 46 live enemies and a boss with a six-wizzrobe
    escort - holds 1.000 exactly. CPU is NOT the binding constraint for
    ordinary content; the GFX table is.
  - **Only acro scenarios ever dip.** Across every probe run (including
    an earlier methodology that kept the room in kill-respawn churn),
    the ONLY rows that ever fell below 1.000 were acro rows: 0.92-0.96,
    repeatedly. The dip in the table above landed in the window where
    the 4-placement pile burst and died at once.
  - **The harness cannot hold a stable engaged-gang population** - the
    burst is proximity-triggered and the engagement input that triggers
    it also kills gang members - so the knee's exact position is NOT
    pinned by measurement. The user's in-play report (3-4 gangs on
    screen = serious slowdown) remains the position estimate, and every
    measurement is consistent with it. The F9 cap (2 placements, at
    most ~12 gang members) sits below every dip ever observed.

  Rule that falls out: gang/macro AIs are the one enemy class that can
  push CPU over budget - price any future one (see the F9 note about
  other gang kinds) with this tool before it reaches the tier table.

## Caveats

- The lag ratio is cycle-accurate and trustworthy. The ms/f column in
  cpu_probe.py is a host-load proxy - only compare within one run on an
  idle machine, never across runs.
- All staged numbers are seed 0x42; wave composition varies by seed, so
  the live-wave rows have seed-sized error bars. The cleared-room combo
  rows are deterministic.
- gfx_used counts status nibbles outside {0,1,2} as occupied, matching
  QuickStartFreeGfxSlots - the same definition the in-game gates use.
