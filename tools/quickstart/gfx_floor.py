"""Free GFX slots in one room at one difficulty - the invariant check's own
measurement, pulled out so a curve change can be iterated in a minute
instead of in the twenty-five the full sweep takes.

The floor is QUICKSTART_GFX_HARD_FLOOR: at least 2 of the 44 sheet slots
free at every frame, because a BOSS spawn needs sixteen to come free and a
room that sits at zero can never deliver one.

    python3 tools/quickstart/gfx_floor.py                 # the two tight rooms
    python3 tools/quickstart/gfx_floor.py --all           # every region room
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, here, poison_here, qs_set
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
MAX_GFX, GFXBASE, DIFF0 = 44, 0x02024490, 174
FLOOR = 2
SEED = None
# The two the full sweep flagged, plus the next-tightest three as controls -
# a curve change that fixes the two by pushing a third under the floor has
# not fixed anything.
WATCH = ['ROOM_HYRULE_FIELD_LON_LON_RANCH', 'ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD',
         'ROOM_CASTLE_GARDEN_MAIN', 'ROOM_CASTOR_WILDS_MAIN',
         'ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH']


def worst_free(rom, row, diff, frames=600):
    c = boot(rom, seed=SEED)
    for b in range(4):
        qs_set(c, DIFF0 + b, (diff >> b) & 1)
    poison_here(c)
    warp(c, row['area'], row['room'], row['entrance'][0], row['entrance'][1])
    if here(c) != (row['area'], row['room']):
        del c
        return None
    worst = MAX_GFX
    for _ in range(frames):
        c.run_frame()
        used = sum(1 for i in range(MAX_GFX)
                   if (c.memory.u8[GFXBASE + 4 + i * 12] & 0x0F) not in (0, 1, 2))
        worst = min(worst, MAX_GFX - used)
    del c
    return worst


def main():
    rooms = P.region_pool()
    if '--all' not in sys.argv:
        rooms = [r for r in rooms if r['roomName'] in WATCH]
    bad = 0
    print('%-42s %s' % ('room', '  d0   d4   d8  d12   worst'))
    for r in rooms:
        vals = []
        for diff in (0, 4, 8, 12):
            vals.append(worst_free(ROM, r, diff))
        got = [v for v in vals if v is not None]
        if not got:
            print('%-42s never landed' % r['roomName'][5:])
            continue
        w = min(got)
        flag = '' if w >= FLOOR else '   <-- BELOW FLOOR'
        bad += w < FLOOR
        print('%-42s %4s %4s %4s %4s   %3d%s'
              % (r['roomName'][5:], *[('-' if v is None else v) for v in vals], w, flag))
    print('\n%d room(s) below the floor of %d' % (bad, FLOOR))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
