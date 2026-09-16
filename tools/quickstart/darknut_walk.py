"""Walk the Castor Wilds -> Darknut cave -> hall -> back route.

The user's report: entering the cave off Castor Wilds gives a fine first
room, but taking the stairs lands you in a Trilby tree interior, locked.
The cause was that ROOM_CASTOR_CAVES_DARKNUT was in the 2-door connector
pool AND a ? room content site at the same time, so its real exits carried
the connector's sentinel tags and got redirected to a drawn pool room.

This walks the fixed route and asserts the destination of every hop, which
is the part the static read cannot do:

    cave room --stairs--> CASTOR_DARKNUT/HALL --door--> back to the cave
    cave room --south--> CASTOR_WILDS/MAIN

Usage: python3 tools/quickstart/darknut_walk.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, here, poison_here, press, r16
import parse_tables as P

PLAYER = 0x03001160
RC = 0x03000bf0
ROM = 'tmc.gba'

A_CAVES, R_DARKNUT = P.AREAS['AREA_CASTOR_CAVES'], P.ROOMS['ROOM_CASTOR_CAVES_DARKNUT']
A_DK, R_HALL = P.AREAS['AREA_CASTOR_DARKNUT'], P.ROOMS['ROOM_CASTOR_DARKNUT_HALL']
A_WILDS, R_WILDS = P.AREAS['AREA_CASTOR_WILDS'], P.ROOMS['ROOM_CASTOR_WILDS_MAIN']

fails = []


def check(ok, msg):
    print(('  ok   ' if ok else '  FAIL ') + msg)
    if not ok:
        fails.append(msg)


def settle(c, n=240):
    for _ in range(n):
        c.run_frame()


def hold(c, key, budget=600):
    """Hold one direction until the room changes.

    NOT a coordinate-seeking walk. The first version of this steered toward
    the stairs' own startX/startY and never arrived, reporting three
    failures that were all the driver: the stair tile is SOLID in the
    collision grid (it is scenery with a warp box over it), so nothing can
    ever stand on it. A player walks INTO it and the box fires. So does
    this.
    """
    start = here(c)
    for _ in range(budget):
        c.set_keys(key)
        c.run_frame()
        c.clear_keys(key)
        if here(c) != start:
            settle(c, 150)
            return True
    return False


def steer(c, tx, ty, budget=400):
    """Walk to one open room-local pixel target. Waypoints only - the exits
    themselves are solid tiles and must be entered with hold()."""
    for _ in range(budget):
        ox, oy = r16(c, RC + 6), r16(c, RC + 8)
        px, py = r16(c, PLAYER + 0x2e) - ox, r16(c, PLAYER + 0x32) - oy
        if abs(tx - px) <= 6 and abs(ty - py) <= 6:
            return True
        k = 0
        if abs(tx - px) > 6:
            k |= c.KEY_RIGHT if tx > px else c.KEY_LEFT
        if abs(ty - py) > 6:
            k |= c.KEY_DOWN if ty > py else c.KEY_UP
        c.set_keys(k)
        c.run_frame()
        c.clear_keys(k)
    return False


# THE CAVE ROOM IS TWO CHAMBERS, and that is why each leg below starts
# where it does rather than all of them sharing one spawn.
#
# The player arrives from Castor Wilds at tile (8,7) - that coordinate is
# read off gExitList_CastorWilds_Main, not chosen - and the south border
# back out is reachable from there. The stairs are at tile (6,1) in the
# upper chamber, behind a walled-off column; in play the player walks
# around to them, but steering a driver through that route proved far more
# fragile than the thing being tested. What is under test is where each
# exit GOES, so each leg spawns in the chamber its exit lives in and walks
# into it.
ARRIVAL = (0x88, 0x78)   # from the Wilds - the south border is reachable here
UPPER = (0x68, 0x40)     # the stairs' own chamber


def main():
    c = boot(ROM)
    poison_here(c)
    # Land in the cave room the way the player does - through its own mouth.
    # (0x88,0x78) is where Castor Wilds' own door lands the player - read
    # off gExitList_CastorWilds_Main, not chosen. An earlier version spawned
    # at (0x68,0x40), which is a different chamber of this room entirely;
    # the south border is unreachable from there and the probe called that a
    # failure of the game.
    warp(c, A_CAVES, R_DARKNUT, UPPER[0], UPPER[1])
    settle(c)
    # A warped-in player sits in PLAYER_ROOMTRANSITION (action 22) and the
    # room's own ? event posts a hint; both have to clear before any input
    # does anything. Measured: action 22 -> 1 only after these presses.
    for _ in range(10):
        press(c, c.KEY_A, 4, 4)
    settle(c, 60)
    check(here(c) == (A_CAVES, R_DARKNUT), 'the cave room loads (the "first room is fine" half)')

    # The stairs: the WARP_TYPE_AREA row at startX/startY (0x68,0x18).
    moved = hold(c, c.KEY_UP)
    dest = here(c)
    print('   stairs -> area %d room %d' % dest)
    check(moved, 'the stairs fire at all')
    check(dest == (A_DK, R_HALL),
          'the stairs land in CASTOR_DARKNUT/HALL, not a drawn pool room')
    if dest == (A_DK, R_HALL):
        px, py = r16(c, PLAYER + 0x2e) - r16(c, RC + 6), r16(c, PLAYER + 0x32) - r16(c, RC + 8)
        print('   landed at room-local (%d,%d)' % (px, py))
        # And back out again: the hall's own door at (0x188,0x18).
        back = hold(c, c.KEY_UP)
        print('   hall door -> area %d room %d' % here(c))
        check(back and here(c) == (A_CAVES, R_DARKNUT),
              'the hall door leads back to the cave room (a real two-room pocket)')
    del c

    # The other exit: the south border back out to the Wilds.
    c = boot(ROM)
    poison_here(c)
    # (0x88,0x78) is where Castor Wilds' own door lands the player - read
    # off gExitList_CastorWilds_Main, not chosen. An earlier version spawned
    # at (0x68,0x40), which is a different chamber of this room entirely;
    # the south border is unreachable from there and the probe called that a
    # failure of the game.
    warp(c, A_CAVES, R_DARKNUT, ARRIVAL[0], ARRIVAL[1])
    settle(c)
    for _ in range(10):
        press(c, c.KEY_A, 4, 4)
    settle(c, 60)
    south = hold(c, c.KEY_DOWN)
    print('   south border -> area %d room %d' % here(c))
    check(south and here(c) == (A_WILDS, R_WILDS),
          'the south border returns to Castor Wilds')
    del c

    print('\n%s: %d failure(s)' % ('FAILED' if fails else 'OK', len(fails)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
