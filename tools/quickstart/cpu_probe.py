"""CPU cost probe (F8, docs/QUICKSTART_BUDGET.md).

Two readings per scenario:

- lag ratio: game main-loop frames (gRoomTransition.frameCount, +0 at
  0x030010A0) advanced per emulated VIDEO frame. The GBA main loop waits
  for VBlank; when game logic overruns the ~280k-cycle frame budget the
  loop misses VBlanks and this ratio drops below 1.00 - that IS the
  slowdown the player sees, measured cycle-accurately and immune to host
  noise. 1.00 = full speed; 0.50 = half speed.
- ms/f: host wallclock per emulated frame, a secondary proxy (more game
  code per frame = more emulation work). Only comparable within one run
  of this tool on an otherwise idle host.

Scenarios are staged through the measurement mailbox (raw CreateEnemy, no
caps) - this is the tool that reproduces the uncapped Acro-Bandit pile the
F9 cap now prevents, and prices boss escorts for F6. Staged scenarios kill
the region's wave once and then PIN QS room flag 0 (the "wave is out"
latch, gRoomVars.flags bit 256 = byte 0x02034384 bit 0) every frame, which
starves the respawn loop: the monitor reads set+cleared, bumps the wave
counter, clears the latch, and the pin re-arms it before it can spawn.
Killing enemies per frame instead (the first version) put the room in a
permanent kill-respawn churn that swamped every reading. The player mashes
A and strolls so proximity-triggered AIs (the acro pop-up) actually engage;
gangs multiply their placement count, so trust the live column, not the
request.

Usage: python3 tools/quickstart/cpu_probe.py [--frames N]
Run it ALONE - concurrent emulator processes pollute the ms/f column.
"""
import sys, time, gc
sys.path.insert(0, '/home/user/bartgame/tools/quickstart')
from emu import warp, here, qs_set, GENT, STRIDE, MAX_ENT
from seed import boot_pinned
from measure_budget import regions, mailbox_spawn, counts, HEALTH

DIFF0 = 174
FRAMECOUNT = 0x030010A0  # gRoomTransition.frameCount, s32 at offset 0
WAVE_LATCH = 0x02034384  # gRoomVars.flags byte 32: QS room flag 0 lives in bit 0
CG = 'CASTLE_GARDEN_MAIN'


def game_frames(c):
    v = (c.memory.u8[FRAMECOUNT] | (c.memory.u8[FRAMECOUNT + 1] << 8)
         | (c.memory.u8[FRAMECOUNT + 2] << 16) | (c.memory.u8[FRAMECOUNT + 3] << 24))
    return v


def pin_latch(c):
    c.memory.u8[WAVE_LATCH] = c.memory.u8[WAVE_LATCH] | 1


def engage(c, frames, staged):
    """Mash A and stroll in a small box so proximity AIs trigger."""
    dirs = (c.KEY_RIGHT, c.KEY_DOWN, c.KEY_LEFT, c.KEY_UP)
    for f in range(frames):
        c.memory.u8[HEALTH] = 0x20
        if staged:
            pin_latch(c)
        d = dirs[(f // 30) % 4]
        if f % 12 < 3:
            c.set_keys(d, c.KEY_A)
        else:
            c.set_keys(d)
        c.run_frame()
        c.clear_keys(d, c.KEY_A)


def measure(c, frames, staged):
    times = []
    g0 = game_frames(c)
    for _ in range(frames):
        c.memory.u8[HEALTH] = 0x20
        if staged:
            pin_latch(c)
        t0 = time.perf_counter()
        c.run_frame()
        times.append((time.perf_counter() - t0) * 1000.0)
    g1 = game_frames(c)
    times.sort()
    ratio = (g1 - g0) / float(frames)
    return ratio, times[len(times) // 2]


def scenario(label, spec=None, diff=0, region=CG, settle=420, frames=300):
    gc.collect()
    r = regions[region]
    c = boot_pinned('tmc.gba', 0x42)
    for b in range(4):
        qs_set(c, DIFF0 + b, (diff >> b) & 1)
    warp(c, r['area'], r['room'], r['entrance'][0], r['entrance'][1], 400)
    assert here(c) == (r['area'], r['room']), 'no land'
    staged = spec is not None
    if staged:
        from measure_budget import kill_everything
        kill_everything(c)
        for _ in range(30):
            pin_latch(c)
            c.memory.u8[HEALTH] = 0x20
            c.run_frame()
        for part in (spec.split('+') if spec else []):
            bits = [int(x, 0) for x in part.split(':')]
            while len(bits) < 3:
                bits.append(1 if len(bits) == 2 else 0)
            mailbox_spawn(c, bits[0], bits[1], bits[2])
    engage(c, settle, staged)
    ratio, ms = measure(c, frames, staged)
    tot, enemies, kinds = counts(c)
    print(f'{label:38s} lag {ratio:5.3f}   {ms:7.3f} ms/f   ({enemies} enemies, {kinds} kinds live)')
    return ratio, ms


if __name__ == '__main__':
    args = sys.argv[1:]
    frames = int(args[args.index('--frames') + 1]) if '--frames' in args else 300
    print('lag = game frames per video frame (1.000 = full speed); '
          f'ms/f = host proxy. {frames} timed frames per scenario.')
    scenario('empty room (wave killed + suppressed)', spec='')
    scenario('natural wave, SHF diff 0', spec=None, region='HYRULE_FIELD_SOUTH_HYRULE_FIELD')
    scenario('natural wave, SHF diff 8', spec=None, diff=8, region='HYRULE_FIELD_SOUTH_HYRULE_FIELD')
    scenario('natural wave, NHF diff 12', spec=None, diff=12, region='HYRULE_FIELD_NORTH_HYRULE_FIELD')
    print('--- the acro knee (uncapped piles; F9 caps play at 2 placements) ---')
    for n in (1, 2, 3, 4, 6):
        scenario(f'{n} acro placement(s), engaged', spec=f'46:0:{n}')
    print('--- bosses and escorts (F6 shortlist) ---')
    scenario('green chuchu boss alone', spec='19:0:1')
    scenario('blue chuchu boss alone', spec='19:4:1')
    scenario('blue boss + 6 ice wizzrobes', spec='19:4:1+41:0:6')
    scenario('boss + 2 bomb peahats', spec='19:0:1+27:0:2')
    scenario('boss + 4 sparks', spec='19:0:1+28:0:4')
    scenario('boss + 12 keese (instance flood)', spec='19:0:1+8:0:12')
