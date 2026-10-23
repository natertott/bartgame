"""How many monsters before the frame runs over.

Spawns N beetles around the hero in the forest entry through gDbgSpawn,
then counts game frames against VBlank frames for 300 frames: the lag
ratio. 1.000 is full speed. Also reports the live actor count, since
the pool itself is a ceiling.

    python3 tools/perf_probe.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import probe as P  # noqa: E402

S = os.environ.get('SNAPDIR', '/tmp')


def live(c):
    n = 0
    for i in range(1, 96):
        if P.actor(c, i)['kind'] == 2:
            n += 1
    return n


def main():
    for n, typ, name in ((16, 0, 'beetles'), (32, 0, 'beetles'), (48, 0, 'beetles'), (64, 0, 'beetles'), (24, 4, 'knights'), (40, 2, 'spitters')):
        c = P.boot()
        P.run(c, 20)
        P.hold(c, 'UP', 150); P.hold(c, 'RIGHT', 14); P.hold(c, 'UP', 60); P.run(c, 40)
        # the room's middle, away from the stairs the swarm would knock the hero onto
        A = P.sym('gActors')
        P.w16(c, A + 8, 0); P.w16(c, A + 10, 192); P.w16(c, A + 12, 0); P.w16(c, A + 14, 128)
        pl = P.sym('gPl')
        P.w16(c, pl + 2, 200); P.w16(c, pl, 200)
        d = P.sym('gDbgSpawn')
        P.w16(c, d, ((n << 8) | typ) & 0xFFFF)
        P.w16(c, d + 2, (n << 8) >> 16)
        P.run(c, 30)
        g = P.sym('gGame')
        f0 = P.r32(c, P.sym('gFrame'))
        r0 = P.r32(c, g + 8)
        for _ in range(300):
            P.w16(c, pl, 200)
            c.run_frame()
        f1 = P.r32(c, P.sym('gFrame'))
        r1 = P.r32(c, g + 8)
        lag = (r1 - r0) / float(f1 - f0) if f1 > f0 else 0
        print('%2d %-9s live %2d  game frames %3d / vblanks %3d  lag %.3f' % (n, name, live(c), r1 - r0, f1 - f0, lag), flush=True)
        if n == 48:
            P.snap(c, os.path.join(S, 'perf48.png'))
    # the music: does channel 2 change over time?
    c = P.boot()
    vals = set()
    for _ in range(240):
        c.run_frame()
        vals.add(P.r16(c, 0x0400006C) & 0x7FF)
    print('music: distinct channel-2 frequencies over 240 frames:', len(vals))


if __name__ == '__main__':
    main()
