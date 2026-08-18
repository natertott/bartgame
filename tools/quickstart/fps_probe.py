"""What the game's frame rate actually is, per region and difficulty.

How the measurement works, and why it needs no instrumentation: main.c's
game loop does `gMain.ticks++`, runs the frame's work, then calls
WaitForNextFrame -> VBlankIntrWait. If the work fits inside one frame the
loop waits for the very next VBlank and ticks advances once per hardware
frame. If the work overruns, the loop has already sailed past one VBlank by
the time it starts waiting, so it waits for the one after that and ticks
advances once per TWO hardware frames. So

    fps = 60 * (ticks advanced) / (hardware frames elapsed)

is the game's real frame rate, read straight out of RAM. mGBA is
cycle-accurate for CPU and DMA, so an overrun here is an overrun on
hardware.

Reported per sample: that rate, the worst 30-frame window inside the run
(a wave that stalls for half a second matters even if the average is
fine), how many enemies were live, and how many distinct enemy kinds
they came from.

Usage:
    python3 tools/quickstart/fps_probe.py [--frames N] [--seed S] [ROOM...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_tables as P
from emu import boot, warp, here, qs_set, entities, KIND_ENEMY, MAX_ENT, GENT, STRIDE

ROM = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tmc.gba'))
GMAIN_TICKS = 0x03001000 + 0x0C
DIFF0 = 174
GFXBASE, MAX_GFX = 0x02024490, 44


def ticks(c):
    return c.memory.u8[GMAIN_TICKS] | (c.memory.u8[GMAIN_TICKS + 1] << 8)


def gfx_used(c):
    return sum(1 for i in range(MAX_GFX)
               if (c.memory.u8[GFXBASE + 4 + i * 12] & 0x0F) not in (0, 1, 2))


def sample(area, room, x, y, diff, frames, seed=None, settle=240):
    c = boot(ROM, seed=seed)
    for b in range(4):
        qs_set(c, DIFF0 + b, (diff >> b) & 1)
    c.memory.u8[0x03000bf0 + 5] = 0xff
    warp(c, area, room, x, y)
    if here(c) != (area, room):
        return None
    for _ in range(settle):
        c.run_frame()
    t0 = ticks(c)
    worst, worst_at = 60.0, 0
    win = 30
    hist = []
    peak_enemies, peak_kinds, peak_gfx, peak_ents = 0, 0, 0, 0
    for f in range(frames):
        c.run_frame()
        hist.append(ticks(c))
        if len(hist) > win:
            adv = (hist[-1] - hist[-1 - win]) & 0xffff
            rate = 60.0 * adv / win
            if rate < worst:
                worst, worst_at = rate, f
        if f % 10 == 0:
            en = entities(c, KIND_ENEMY)
            ents = sum(1 for i in range(MAX_ENT) if c.memory.u8[GENT + i * STRIDE + 8] != 0)
            kinds = len({e[2] for e in en})
            if len(en) > peak_enemies:
                peak_enemies = len(en)
            if kinds > peak_kinds:
                peak_kinds = kinds
            g = gfx_used(c)
            if g > peak_gfx:
                peak_gfx = g
            if ents > peak_ents:
                peak_ents = ents
    avg = 60.0 * ((ticks(c) - t0) & 0xffff) / frames
    del c
    return dict(avg=avg, worst=worst, worst_at=worst_at, enemies=peak_enemies,
                kinds=peak_kinds, gfx=peak_gfx, ents=peak_ents)


def main():
    args = sys.argv[1:]
    frames = 600
    seed = None
    if '--frames' in args:
        frames = int(args[args.index('--frames') + 1])
    if '--seed' in args:
        seed = int(args[args.index('--seed') + 1], 0)
    names = [a for a in args if not a.startswith('--') and not a.isdigit()]
    print(f'{"room":<34} {"diff":>4} {"fps":>6} {"worst":>6} {"enemies":>8} {"kinds":>6} '
          f'{"gfx":>4} {"ents":>5}')
    for r in P.region_pool():
        if names and not any(n.upper() in r['roomName'] for n in names):
            continue
        for diff in (0, 4, 8, 12):
            s = sample(r['area'], r['room'], r['entrance'][0], r['entrance'][1], diff, frames, seed)
            if s is None:
                print(f'{r["roomName"][5:]:<34} {diff:>4}   did not land')
                continue
            print(f'{r["roomName"][5:]:<34} {diff:>4} {s["avg"]:>6.1f} {s["worst"]:>6.1f} '
                  f'{s["enemies"]:>8} {s["kinds"]:>6} {s["gfx"]:>4} {s["ents"]:>5}')


if __name__ == '__main__':
    main()
