"""Which region seams does containment let the player walk?

Minish Woods and Lake Hylia had pool rows, reach-table entries and content
sites, and were still unreachable: QuickStartRingRegionOfRoom had no line
for either area, so every border out of Eastern Hills or Lon Lon Ranch into
them was cancelled the frame it fired.

This asks the gate directly rather than walking the player across a
thousand-pixel overworld room. Stage a transition the way vanilla's own
door/border code does - area_next, room_next, transitioningOut - then run
the three containment functions and see whether the flag survives. The exit
lists (tools/quickstart/exit_lists.py) are what prove the seam EXISTS in the
data; this is what proves the mode stops cancelling it.

Controls matter more than usual here, because "allowed" is the default for
anything the policy does not cover: each opened seam is paired with a
transition out of the SAME room that must still be refused.

Usage: python3 tools/quickstart/seam_gate.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, press, poison_here, here
from callrom import call_keep, game_sym
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
ROOM_TRANSITION = 0x030010A0
TRANSITIONING_OUT = ROOM_TRANSITION + 0x08
AREA_NEXT = ROOM_TRANSITION + 0x0c
ROOM_NEXT = ROOM_TRANSITION + 0x0d

GATES = [game_sym(n) for n in ('QuickStartEnforceContainment',
                               'QuickStartEnforceLonLonContainment',
                               'QuickStartEnforceFieldRegionContainment')]


def ids(path):
    out = {}
    for line in open(os.path.join(P.ROOT, 'build/USA/enum_include/' + path)):
        m = re.match(r'\.set (\w+), (\d+)', line.strip())
        if m:
            out.setdefault(m.group(1), int(m.group(2)))
    return out


A, R = ids('area.inc'), ids('roomid.inc')

# (label, from area/room/spawn, to area/room, expected)
CASES = [
    ('EH North  -> Minish Woods', 'AREA_HYRULE_FIELD', 'ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH', 264, 264,
     'AREA_MINISH_WOODS', 'ROOM_MINISH_WOODS_MAIN', True),
    ('EH South  -> Minish Woods', 'AREA_HYRULE_FIELD', 'ROOM_HYRULE_FIELD_EASTERN_HILLS_SOUTH', 328, 104,
     'AREA_MINISH_WOODS', 'ROOM_MINISH_WOODS_MAIN', True),
    ('Lon Lon   -> Lake Hylia', 'AREA_HYRULE_FIELD', 'ROOM_HYRULE_FIELD_LON_LON_RANCH', 344, 870,
     'AREA_LAKE_HYLIA', 'ROOM_LAKE_HYLIA_MAIN', True),
    ('Minish W. -> EH North', 'AREA_MINISH_WOODS', 'ROOM_MINISH_WOODS_MAIN', 8, 424,
     'AREA_HYRULE_FIELD', 'ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH', True),
    ('Lake Hyl. -> Lon Lon', 'AREA_LAKE_HYLIA', 'ROOM_LAKE_HYLIA_MAIN', 40, 440,
     'AREA_HYRULE_FIELD', 'ROOM_HYRULE_FIELD_LON_LON_RANCH', True),
    ('Minish W. -> Deepwood (site)', 'AREA_MINISH_WOODS', 'ROOM_MINISH_WOODS_MAIN', 8, 424,
     'AREA_DEEPWOOD_SHRINE', 'ROOM_DEEPWOOD_SHRINE_ENTRANCE', True),
    # --- controls: same rooms, destinations that must stay refused --------
    #
    # Choosing these took two passes. The Witch Hut, Librari and Mount
    # Crenel's entrance all looked like obvious "should be sealed"
    # destinations and all three came back ALLOWED - correctly, because
    # every one of them is a content site, and a site's door is blessed by
    # QuickStartIsPocketInteriorRoom wherever it lives. A control has to be
    # a door that is genuinely not part of the mode, so these are the exits
    # from the same two rooms that no site table names.
    ('CONTROL  Minish W. -> Minish cave N1', 'AREA_MINISH_WOODS', 'ROOM_MINISH_WOODS_MAIN', 8, 424,
     'AREA_MINISH_CAVES', 'ROOM_MINISH_CAVES_MINISH_WOODS_NORTH_1', False),
    ('CONTROL  Minish W. -> Great Fairy tree', 'AREA_MINISH_WOODS', 'ROOM_MINISH_WOODS_MAIN', 8, 424,
     'AREA_TREE_INTERIORS', 'ROOM_TREE_INTERIORS_MINISH_WOODS_GREAT_FAIRY', False),
    ('CONTROL  Lake Hyl. -> Lake Woods cave', 'AREA_LAKE_HYLIA', 'ROOM_LAKE_HYLIA_MAIN', 40, 440,
     'AREA_LAKE_WOODS_CAVE', 'ROOM_LAKE_WOODS_CAVE_MAIN', False),
]


def run(label, fa, fr, sx, sy, ta, tr, expect):
    if ta not in A or tr not in R:
        print(f'{label}: destination not in this build - SKIPPED')
        return None
    c = boot(ROM)
    poison_here(c)
    warp(c, A[fa], R[fr], sx, sy)
    for _ in range(10):
        press(c, c.KEY_A, 5, 5)
    landed = here(c)
    if landed != (A[fa], R[fr]):
        print(f'{label}: never landed in the FROM room (got {landed}) - INCONCLUSIVE')
        del c
        return None
    c.memory.u8[AREA_NEXT] = A[ta]
    c.memory.u8[ROOM_NEXT] = R[tr]
    c.memory.u8[TRANSITIONING_OUT] = 1
    for g in GATES:
        call_keep(c, g, ())
    allowed = c.memory.u8[TRANSITIONING_OUT] != 0
    ok = allowed == expect
    print(f'{label}: {"allowed" if allowed else "cancelled":<9} '
          f'(want {"allowed" if expect else "cancelled"})  {"ok" if ok else "FAIL"}')
    del c
    return ok


def main():
    res = [run(*case) for case in CASES]
    real = [r for r in res if r is not None]
    print()
    if not real:
        print('INCONCLUSIVE: nothing ran')
        return 2
    bad = real.count(False)
    print('PASS: %d seam checks' % len(real) if not bad else 'FAIL: %d of %d' % (bad, len(real)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
