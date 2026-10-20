"""Hyrule Town's well and the underground it drops into (Oct 2026).

The well is a hole (holeManager.c, gHoleTransitions row 60): falling in
sends the player to the well room, ROOM_HYRULE_TOWN_UNDERGROUND_1. Neither
underground room was in a region, so containment cancelled the fall's
transition after the player had started falling, and they were left
invisible in PLAYER_FALL for good (the user's freeze). The two rooms are
Hyrule Town region rooms now.

  FALL     the player falls in the well (PLAYER_FALL forced on the hole,
           which is what landing in it does; the rim is solid, so the way
           in is a jump): they land in the well room, visible and walking
  SNAP     a screenshot of the arrival (the eye check)
  LADDER   the well room's ladder climbs back to the square, beside the well
  PASSAGE  the well room's east passage leads into the underground's main
           room
  HATCH    the main room's ladder climbs to a house roof in the square's
           north-east (vanilla: it comes out of the chimney). The roof is
           walled; its only way off without the Cape is the chimney
  CHIMNEY  down the chimney from the roof is back in the main room
  SHUT     a door out of the main room to a room outside the region (the
           school's cellar) is cancelled: the player stays, and walks

Before the fix FALL read: the transition asked for (65, 1) and was
cancelled, the player undrawn in PLAYER_FALL 850 frames later.

    python3 tools/quickstart/well_probe.py [--rom tmc-d3.gba] [--out DIR]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
from emu import r16, w16, here, snap, PLAYER, ROOM_CONTROLS
import scenario as S
import parse_tables as P
from chain_audit import dismiss

ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else os.path.join(P.ROOT, 'tmc-d3.gba')
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else '/tmp'
TOWN = (P.AREAS['AREA_HYRULE_TOWN'], P.ROOMS['ROOM_HYRULE_TOWN_MAIN'])
UG = P.AREAS['AREA_HYRULE_TOWN_UNDERGROUND']
WELL = (UG, P.ROOMS['ROOM_HYRULE_TOWN_UNDERGROUND_1'])
MAIN = (UG, P.ROOMS['ROOM_HYRULE_TOWN_UNDERGROUND_0'])
HOLE = (776, 648)            # inside the well's hole box, room-local
PLAYER_NORMAL, PLAYER_FALL = 1, 3
res = []


def check(name, ok, detail=''):
    res.append(bool(ok))
    print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)


def local(c):
    return (r16(c, PLAYER + 0x2e) - r16(c, ROOM_CONTROLS + 6), r16(c, PLAYER + 0x32) - r16(c, ROOM_CONTROLS + 8))


def standing(c):
    return c.memory.u8[PLAYER + 0x0c] == PLAYER_NORMAL and c.memory.u8[PLAYER + 0x18] & 3


def settle(c, n=4):
    for _ in range(n):
        dismiss(c)
        for _ in range(60):
            c.run_frame()


def teleport(c, x, y):
    w16(c, PLAYER + 0x2e, r16(c, ROOM_CONTROLS + 6) + x)
    w16(c, PLAYER + 0x32, r16(c, ROOM_CONTROLS + 8) + y)
    for _ in range(4):
        c.run_frame()


def fall_in(c):
    """Land in the well's hole; True once the player stands in the well room."""
    # position and action in the same frame: a teleport left to run first is
    # answered by RespawnPlayer (the hole under the player), back to the
    # last safe spot
    w16(c, PLAYER + 0x2e, r16(c, ROOM_CONTROLS + 6) + HOLE[0])
    w16(c, PLAYER + 0x32, r16(c, ROOM_CONTROLS + 8) + HOLE[1])
    c.memory.u8[PLAYER + 0x0c], c.memory.u8[PLAYER + 0x0d] = PLAYER_FALL, 0
    for _ in range(400):
        c.run_frame()
        if here(c) == WELL and standing(c):
            return True
    return False


def walk(c, key, until, frames=300):
    """Hold a direction until here() is `until`. False at once if already
    there (a check that starts in the wrong room proves nothing)."""
    if here(c) == until:
        return False
    c.set_keys(key)
    try:
        for _ in range(frames):
            c.run_frame()
            if here(c) == until:
                break
    finally:
        c.clear_keys(key)
    for _ in range(120):
        c.run_frame()
    return here(c) == until


def boot():
    c = S.boot(ROM, S.KINDS['ROOM'], a=TOWN[0], b=TOWN[1], c=32, d=41, frames=400)
    settle(c)
    return c


def main():
    c = boot()
    ok = fall_in(c)
    check('FALL: the well drops the player in its room', ok,
          'room %s at %s, action %d' % (here(c), local(c), c.memory.u8[PLAYER + 0x0c]))
    settle(c, 2)
    path = os.path.join(OUT, 'well_room.png')
    snap(c, path)
    check('SNAP: the arrival', os.path.exists(path), path)
    ok = walk(c, c.KEY_UP, TOWN)
    check('LADDER: the well room climbs back to the square', ok and standing(c),
          'room %s at %s' % (here(c), local(c)))

    c = boot()
    fall_in(c)
    settle(c, 2)
    ok = walk(c, c.KEY_RIGHT, MAIN)
    check('PASSAGE: the well room leads into the main room', ok and standing(c),
          'room %s at %s' % (here(c), local(c)))
    settle(c, 2)
    teleport(c, 648, 290)   # below the ladder to the north-east hatch
    ok = walk(c, c.KEY_UP, TOWN)
    check('HATCH: the main room climbs to the chimney roof', ok and standing(c),
          'room %s at %s' % (here(c), local(c)))
    teleport(c, 824, 280)   # the ladder's own landing, beside the chimney
    ok = walk(c, c.KEY_DOWN, MAIN)
    check('CHIMNEY: the chimney leads back down', ok and standing(c),
          'room %s at %s' % (here(c), local(c)))

    c = boot()
    fall_in(c)
    settle(c, 2)
    walk(c, c.KEY_RIGHT, MAIN)
    settle(c, 2)
    emu.warp(c, P.AREAS['AREA_HOUSE_INTERIORS_1'], P.ROOMS['ROOM_HOUSE_INTERIORS_1_SCHOOL_WEST'], 120, 72, frames=200)
    check('SHUT: a door out of the region is cancelled', here(c) == MAIN and standing(c),
          'room %s at %s, action %d' % (here(c), local(c), c.memory.u8[PLAYER + 0x0c]))
    print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
    return 0 if all(res) else 1


if __name__ == '__main__':
    sys.exit(main())
