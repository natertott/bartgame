"""Does the Boomerang chamber's ladder still loop after the vanilla restore?

The chamber's four ladders were the one MOVED transition with a stated
reason: they landed 0x30 below vanilla's spot because the tree hollow's own
ladder sits where vanilla puts you, so arriving there could drop the player
straight back down. The user's instruction is that every transition that is
not deliberately blocked routes as vanilla does, so the landing went back -
and this checks the hazard that motivated moving it.

A loop would show as: take the ladder up, and end up back in the chamber.

Usage: python3 tools/quickstart/boomerang_walk.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, here, poison_here, press, r16
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
CHAMBER = ('AREA_CAVES', 'ROOM_CAVES_BOOMERANG')
# The four ladder doors, from gExitList_Caves_Boomerang.
DOORS = [(0x48, 0x68, 'ROOM_TREE_INTERIORS_BOOMERANG_NORTHWEST'),
         (0x108, 0x68, 'ROOM_TREE_INTERIORS_BOOMERANG_NORTHEAST'),
         (0x48, 0xd8, 'ROOM_TREE_INTERIORS_BOOMERANG_SOUTHWEST'),
         (0x108, 0xd8, 'ROOM_TREE_INTERIORS_BOOMERANG_SOUTHEAST')]


def main():
    fails = []
    for (x, y, want) in DOORS:
        c = boot(ROM)
        poison_here(c)
        # Land ON the door tile: the transition fires from standing there.
        warp(c, P.AREAS[CHAMBER[0]], P.ROOMS[CHAMBER[1]], x, y)
        for _ in range(10):
            press(c, c.KEY_A, 5, 5)
        # Give it plenty of time to fire, arrive, and (if it loops) fall back.
        for _ in range(600):
            c.run_frame()
        got = here(c)
        in_chamber = got == (P.AREAS[CHAMBER[0]], P.ROOMS[CHAMBER[1]])
        arrived = got == (P.AREAS['AREA_TREE_INTERIORS'], P.ROOMS[want])
        ok = arrived or not in_chamber
        print('  %-9s door -> %s  %s' % (want.split('_')[-1], got,
                                         'ok' if ok else 'FAIL (fell back into the chamber)'))
        if not ok:
            fails.append(want)
        del c
    print()
    print('PASS: no ladder loops back' if not fails else 'FAIL: %d looped' % len(fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
