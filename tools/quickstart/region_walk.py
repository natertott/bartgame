"""Can the player WALK into Minish Woods, Lake Hylia and Mount Crenel?

This exists because the last attempt to open these regions was verified
with tools/quickstart/seam_gate.py, which stages a transition by writing
area_next/room_next/transitioningOut and then runs the containment
functions. That proves the POLICY allows the crossing. It cannot prove
there is a crossing: the three borders had been deleted from
src/data/transitions.c outright under #ifndef QUICKSTART, so the gate was
opened on a door that did not exist and the player stayed exactly as stuck.

Warping is not walking. So: put the player near the real border, hold the
direction that leaves the room, and see where they end up.

Usage: python3 tools/quickstart/region_walk.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, here, poison_here, press, r16
import parse_tables as P

PLAYER = 0x03001160
RC = 0x03000bf0
ROM = os.path.join(P.ROOT, 'tmc.gba')

fails = []


def check(ok, msg):
    print(('  ok   ' if ok else '  FAIL ') + msg)
    if not ok:
        fails.append(msg)


def hold(c, key, limit=900):
    """Drive one direction until the room changes, or give up."""
    k = getattr(c, key)
    start = here(c)
    for _ in range(limit):
        c.set_keys(k)
        c.run_frame()
        if here(c) != start:
            c.clear_keys(k)
            for _ in range(120):
                c.run_frame()
            return True
    c.clear_keys(k)
    return False


def leg(label, area, room, x, y, key, want_area, want_room):
    c = boot(ROM)
    poison_here(c)
    warp(c, P.AREAS[area], P.ROOMS[room], x, y)
    for _ in range(10):
        press(c, c.KEY_A, 5, 5)
    if here(c) != (P.AREAS[area], P.ROOMS[room]):
        check(False, '%s: never landed in the start room (got %s)' % (label, here(c)))
        del c
        return
    moved = hold(c, key)
    got = here(c)
    want = (P.AREAS[want_area], P.ROOMS[want_room])
    check(moved and got == want,
          '%s: %s -> %s (wanted %s)' % (label, room, got, want))
    del c


def main():
    # The coordinates are MEASURED, not guessed. An overworld border is
    # open only in bands - the rest of the edge is cliff - and the first
    # version of this probe put every leg against one. Sweeping the east
    # edge of Eastern Hills North in 64px steps: y 40 and 104 cross, 168
    # through 360 do not, 424 crosses, 488 does not. That is the terrain,
    # not the transition table, and it is why "held RIGHT and nothing
    # happened" is not evidence of a missing row.
    print('into Minish Woods')
    leg('EH North east edge (y=104)', 'AREA_HYRULE_FIELD', 'ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH',
        440, 104, 'KEY_RIGHT', 'AREA_MINISH_WOODS', 'ROOM_MINISH_WOODS_MAIN')
    leg('EH North east edge (y=424)', 'AREA_HYRULE_FIELD', 'ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH',
        440, 424, 'KEY_RIGHT', 'AREA_MINISH_WOODS', 'ROOM_MINISH_WOODS_MAIN')
    leg('EH South east edge (y=152)', 'AREA_HYRULE_FIELD', 'ROOM_HYRULE_FIELD_EASTERN_HILLS_SOUTH',
        440, 152, 'KEY_RIGHT', 'AREA_MINISH_WOODS', 'ROOM_MINISH_WOODS_MAIN')
    print('into Lake Hylia')
    leg('Lon Lon east edge', 'AREA_HYRULE_FIELD', 'ROOM_HYRULE_FIELD_LON_LON_RANCH',
        680, 440, 'KEY_RIGHT', 'AREA_LAKE_HYLIA', 'ROOM_LAKE_HYLIA_MAIN')
    print('into Mount Crenel')
    leg('Trilby west edge (y=424)', 'AREA_HYRULE_FIELD', 'ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS',
        40, 424, 'KEY_LEFT', 'AREA_MT_CRENEL', 'ROOM_MT_CRENEL_ENTRANCE')
    print('and back out again')
    leg('Minish Woods west', 'AREA_MINISH_WOODS', 'ROOM_MINISH_WOODS_MAIN',
        24, 424, 'KEY_LEFT', 'AREA_HYRULE_FIELD', 'ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH')
    leg('Lake Hylia west', 'AREA_LAKE_HYLIA', 'ROOM_LAKE_HYLIA_MAIN',
        24, 440, 'KEY_LEFT', 'AREA_HYRULE_FIELD', 'ROOM_HYRULE_FIELD_LON_LON_RANCH')

    print()
    print('PASS' if not fails else 'FAIL: %d leg(s)' % len(fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
