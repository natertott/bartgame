"""Does containment let the player walk into, around and out of Melari's Mine?

The mine's whole route was already vanilla in the data. What stopped it was
policy: Mount Crenel's rooms are named region rooms, so
QuickStartEnforceFieldRegionContainment polices them, and the mountain's own
Minish holes land in rooms nothing had blessed - CRENEL_MINISH_PATHS/MELARI,
MELARIS_MINE/MAIN, CRENEL_MINISH_PATHS/BEAN, MINISH_CRACKS/MT_CRENEL. An
unblessed Minish hole is cancelled the frame it fires, which from the
player's side is falling in and landing nowhere.

Same method as seam_gate.py: stage a transition the way vanilla's door and
border code does (area_next, room_next, transitioningOut), run all three
containment functions, and see whether the flag survives. This asks the gate
itself rather than trying to walk a Minish-sized Link onto a hole box.

Two things about the controls here.

Melari's Mine and the Crenel Minish paths are NOT policed areas - they are
not contained and not on the field-region list - so every transition that
STARTS in one of them is allowed by default. A control has to start
somewhere policed, so the refusals below start on the mountain (a real
forecourt door to a cave that is not a site) and in Minish House Interiors,
which is contained (the mine's east side room, from its south-west one).

The other direction is the one that could trap a player: the three side
rooms live in AREA_MINISH_HOUSE_INTERIORS, which IS contained, so walking
back out of them is checked - and passes only because the mine is now a
pocket interior. Those three cases are the point of this probe.

Usage: python3 tools/quickstart/melari_gate.py
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

FORECOURT = ('AREA_MT_CRENEL', 'ROOM_MT_CRENEL_CAVERN_OF_FLAMES_ENTRANCE', 472, 200)
ENTRANCE = ('AREA_MT_CRENEL', 'ROOM_MT_CRENEL_ENTRANCE', 861, 54)
TOP = ('AREA_MT_CRENEL', 'ROOM_MT_CRENEL_TOP', 240, 151)
MINE = ('AREA_MELARIS_MINE', 'ROOM_MELARIS_MINE_MAIN', 256, 256)
PATHS = ('AREA_CRENEL_MINISH_PATHS', 'ROOM_CRENEL_MINISH_PATHS_MELARI', 120, 72)
SW = ('AREA_MINISH_HOUSE_INTERIORS', 'ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHWEST', 120, 40)
SE = ('AREA_MINISH_HOUSE_INTERIORS', 'ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHEAST', 120, 40)
EAST = ('AREA_MINISH_HOUSE_INTERIORS', 'ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_EAST', 36, 86)

# (label, from, to area/room, expected)
CASES = [
    # --- the mountain's six Minish holes -------------------------------
    ('hole  forecourt -> Minish paths (Melari)', FORECOURT,
     'AREA_CRENEL_MINISH_PATHS', 'ROOM_CRENEL_MINISH_PATHS_MELARI', True),
    ('hole  forecourt -> Melari\'s Mine', FORECOURT,
     'AREA_MELARIS_MINE', 'ROOM_MELARIS_MINE_MAIN', True),
    ('hole  entrance  -> Minish paths (Bean)', ENTRANCE,
     'AREA_CRENEL_MINISH_PATHS', 'ROOM_CRENEL_MINISH_PATHS_BEAN', True),
    ('hole  entrance  -> Minish paths (Spring)', ENTRANCE,
     'AREA_CRENEL_MINISH_PATHS', 'ROOM_CRENEL_MINISH_PATHS_SPRING_WATER', True),
    ('hole  entrance  -> Minish crack', ENTRANCE,
     'AREA_MINISH_CRACKS', 'ROOM_MINISH_CRACKS_MT_CRENEL', True),
    ('seam  top       -> Minish paths (Rain)', TOP,
     'AREA_CRENEL_MINISH_PATHS', 'ROOM_CRENEL_MINISH_PATHS_RAIN', True),
    # --- around the mine (origins are unpoliced; recorded, not proven) ---
    ('door  paths     -> Melari\'s Mine', PATHS,
     'AREA_MELARIS_MINE', 'ROOM_MELARIS_MINE_MAIN', True),
    ('door  mine      -> south-west room', MINE,
     'AREA_MINISH_HOUSE_INTERIORS', 'ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHWEST', True),
    ('door  mine      -> south-east room', MINE,
     'AREA_MINISH_HOUSE_INTERIORS', 'ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHEAST', True),
    ('door  mine      -> east room', MINE,
     'AREA_MINISH_HOUSE_INTERIORS', 'ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_EAST', True),
    # --- out again: the three that could trap a player -------------------
    ('OUT   south-west -> mine', SW, 'AREA_MELARIS_MINE', 'ROOM_MELARIS_MINE_MAIN', True),
    ('OUT   south-east -> mine', SE, 'AREA_MELARIS_MINE', 'ROOM_MELARIS_MINE_MAIN', True),
    ('OUT   east       -> mine', EAST, 'AREA_MELARIS_MINE', 'ROOM_MELARIS_MINE_MAIN', True),
    # --- controls: policed origins, destinations that must stay refused --
    ('CONTROL forecourt -> Pillar cave (no site)', FORECOURT,
     'AREA_CRENEL_CAVES', 'ROOM_CRENEL_CAVES_PILLAR_CAVE', False),
    ('CONTROL forecourt -> Bridge switch (no site)', FORECOURT,
     'AREA_CRENEL_CAVES', 'ROOM_CRENEL_CAVES_BRIDGE_SWITCH', False),
    # Not "south-west -> east room": both are in AREA_MINISH_HOUSE_INTERIORS,
    # and QuickStartEnforceContainment's last line only cancels when the
    # DESTINATION is outside the contained set, so contained-to-contained is
    # allowed by construction and proves nothing. This leaves the contained
    # area for somewhere the mine does not reach, which is what makes the
    # three OUT rows above mean something: they pass because the mine is a
    # blessed pocket, not because leaving a side room is free.
    ('CONTROL south-west -> Pillar cave (no site)', SW,
     'AREA_CRENEL_CAVES', 'ROOM_CRENEL_CAVES_PILLAR_CAVE', False),
    ('CONTROL east       -> Pillar cave (no site)', EAST,
     'AREA_CRENEL_CAVES', 'ROOM_CRENEL_CAVES_PILLAR_CAVE', False),
]


def run(label, frm, ta, tr, expect):
    fa, fr, sx, sy = frm
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
    print(f'{label:<46} {"allowed" if allowed else "cancelled":<9} '
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
    print('PASS: %d gate checks' % len(real) if not bad else 'FAIL: %d of %d' % (bad, len(real)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
