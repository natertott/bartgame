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


def drive_to(c, tx, ty, budget=900):
    """Walk the player at a room-local target until the room changes."""
    start = here(c)
    for _ in range(budget):
        ox, oy = r16(c, RC + 6), r16(c, RC + 8)
        px, py = r16(c, PLAYER + 0x2e) - ox, r16(c, PLAYER + 0x32) - oy
        k = 0
        if abs(tx - px) > 4:
            k |= c.KEY_RIGHT if tx > px else c.KEY_LEFT
        if abs(ty - py) > 4:
            k |= c.KEY_DOWN if ty > py else c.KEY_UP
        c.set_keys(k)
        c.run_frame()
        c.clear_keys(k)
        if here(c) != start:
            settle(c, 120)
            return True
    return False


def main():
    c = boot(ROM)
    poison_here(c)
    # Land in the cave room the way the player does - through its own mouth.
    warp(c, A_CAVES, R_DARKNUT, 0x68, 0x40)
    settle(c)
    for _ in range(6):
        press(c, c.KEY_A, 4, 4)
    check(here(c) == (A_CAVES, R_DARKNUT), 'the cave room loads (the "first room is fine" half)')

    # The stairs: the WARP_TYPE_AREA row at startX/startY (0x68,0x18).
    moved = drive_to(c, 0x68, 0x18)
    dest = here(c)
    print('   stairs -> area %d room %d' % dest)
    check(moved, 'the stairs fire at all')
    check(dest == (A_DK, R_HALL),
          'the stairs land in CASTOR_DARKNUT/HALL, not a drawn pool room')
    if dest == (A_DK, R_HALL):
        px, py = r16(c, PLAYER + 0x2e) - r16(c, RC + 6), r16(c, PLAYER + 0x32) - r16(c, RC + 8)
        print('   landed at room-local (%d,%d)' % (px, py))
        # And back out again: the hall's own door at (0x188,0x18).
        back = drive_to(c, 0x188, 0x18)
        print('   hall door -> area %d room %d' % here(c))
        check(back and here(c) == (A_CAVES, R_DARKNUT),
              'the hall door leads back to the cave room (a real two-room pocket)')
    del c

    # The other exit: the south border back out to the Wilds.
    c = boot(ROM)
    poison_here(c)
    warp(c, A_CAVES, R_DARKNUT, 0x68, 0x40)
    settle(c)
    for _ in range(6):
        press(c, c.KEY_A, 4, 4)
    south = drive_to(c, 0x68, 0x200)
    print('   south border -> area %d room %d' % here(c))
    check(south and here(c) == (A_WILDS, R_WILDS),
          'the south border returns to Castor Wilds')
    del c

    print('\n%s: %d failure(s)' % ('FAILED' if fails else 'OK', len(fails)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
