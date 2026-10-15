"""Walk out of the Wind Ruins from the far side of the tektite statue.

Vanilla's Ruins are one-way: the Entrance, the ladder room, up into the
Triple Tektites room, whose three tektites must die (LOST_02_00) before the
statue over the ladder up to the Beanstalk room lifts. A run dropped in the
Armos room (pool row 14) starts beyond it, and QuickStartRuinsStatueMonitor
sets the fight's flag for such a run. Three runs:

  FIX      dropped in the Armos room: the flag is set, and the player walks
           Armos room -> Fortress Entrance -> Beanstalk room -> down the
           ladder past the statue -> Tektites room -> ladder room -> the
           Entrance, room by room on the live collision grid (no items).
           Twice the player is stood further on inside a room, where vanilla
           ground the walker cannot read (the Fortress Entrance's grass, the
           Beanstalk room's ledges) lies between; the statue is not there.
  CONTROL  the same landing and walk, with the run's drop recorded as the
           Entrance (row 13), so the monitor never sets the flag: the build
           before the fix, for this walk. It must stop at the statue
  ENTRANCE dropped at the Entrance (row 13): the flag stays clear and the
           tektites still come, so the vanilla fight is kept there

    python3 tools/quickstart/ruins_statue_probe.py [--rom tmc-d3.gba]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
from emu import here, entities, KIND_ENEMY
import scenario as S
import parse_tables as P
import block_probe as BP
import carry_room_probe as R
import callrom as C

FLAG = 0x100 + 0x27   # FLAG_BANK_1 + LOST_02_00 (USA)
ROOMS = {P.ROOMS[n]: n[11:] for n in ('ROOM_RUINS_ENTRANCE', 'ROOM_RUINS_BEANSTALK', 'ROOM_RUINS_TEKTITES',
                                      'ROOM_RUINS_LADDER_TO_TEKTITES', 'ROOM_RUINS_FORTRESS_ENTRANCE',
                                      'ROOM_RUINS_BELOW_FORTRESS_ENTRANCE')}
# Room by room: an edge to walk off, or a tile to stand on and the key that
# takes the player on from it (a ladder).
ROUTE = [
    ('BELOW_FORTRESS_ENTRANCE', 'N'),
    # Vanilla grass (collision 0x5f) stands between the Armos room's door
    # and the rest of this room, and the walker does not cut: it is stood
    # by the west exit instead. Not what the fix changes.
    ('FORTRESS_ENTRANCE', ('TP', (1, 2)), 'W'),
    # The room's ledges and steps are more than the walker reads from the
    # collision map: stood above the ladder down onto the statue instead.
    ('BEANSTALK', ('TP', (5, 10)), ((5, 10), 'DOWN')),
    ('TEKTITES', ((8, 7), 'DOWN')),       # the ladder down to the ladder room
    ('LADDER_TO_TEKTITES', 'W'),
]


def flag(c):
    return (c.memory.u8[emu.SAVE_FLAGS + (FLAG >> 3)] >> (FLAG & 7)) & 1


def usable(c):
    """A real drop into the Ruins needs the swamp kit and the statues gate
    open (QuickStartDropRowUsable); the testbed lands there regardless, so
    the run is given both, or the drop the game believes in is elsewhere.
    The Pegasus Boots, not the Cape: the Cape could hop what is measured."""
    n = P.ITEMS['ITEM_PEGASUS_BOOTS']
    c.memory.u8[S.SAVE_BASE + 0xF2 + (n >> 2)] |= 1 << ((n & 3) * 2)
    emu.qs_set(c, 228, 0)   # GF_GOLD_GATE_SEALED_BIT(QS_GOLD_GATE_STATUES)


def drop_row(c, row):
    """The testbed's REGION landing does not record the drop row; a run's
    drop does (GF_DROP_REGION_BIT(0) = 467, GF_POOL_HI_DROP = 211)."""
    C.call_keep(c, C.game_sym('QuickStartWritePoolIdx'), (467, 211, row))


SOLID = {0x0F, 0x5F, 0xFF}   # full walls, vanilla grass (the walker does not cut)


def grid(c):
    """Walkable tiles: carry_room_probe's grid, but a partly solid tile
    (a corner or an edge, collision 1-0xe) is walkable, as it is to the
    player, and so are ladders."""
    w, h = emu.room_dims(c)
    tw, th = min(w // 16, 64), min(h // 16, 64)
    return tw, th, [[emu.coll_at(c, x, y) not in SOLID and emu.act_at(c, x, y) not in R.HAZ for x in range(tw)]
                    for y in range(th)]


def walk(c):
    run = lambda n: BP.run(c, n)
    passed = [ROOMS.get(here(c)[1], here(c))]
    for step in ROUTE:
        name, hop = step[0], step[-1]
        if here(c) != (P.AREAS['AREA_RUINS'], P.ROOMS['ROOM_RUINS_' + name]):
            return passed, 'expected %s' % name
        if len(step) == 3:
            ox, oy = BP.origin(c)
            emu.w16(c, emu.PLAYER + 0x2e, ox + step[1][1][0] * 16 + 8)
            emu.w16(c, emu.PLAYER + 0x32, oy + step[1][1][1] * 16 + 8)
            run(20)
        tw, th, g = grid(c)
        me = R.ltile(c)
        inside = R.piece(tw, th, g, me)
        if isinstance(hop, str):
            dx, dy = {'S': (0, 1), 'N': (0, -1), 'E': (1, 0), 'W': (-1, 0)}[hop]
            goals = sorted((t for t in inside if (t[0] + dx, t[1] + dy) not in inside),
                           key=lambda t: (-(t[0] * dx + t[1] * dy), abs(t[0] - me[0]) + abs(t[1] - me[1])))[:16]
            key = {'S': c.KEY_DOWN, 'N': c.KEY_UP, 'E': c.KEY_RIGHT, 'W': c.KEY_LEFT}[hop]
        else:
            goals, key = [hop[0]], getattr(c, 'KEY_' + hop[1])
        start = here(c)
        for goal in goals:
            R.walk_to(c, inside, goal, limit=4000)
            c.set_keys(key)
            for _ in range(180):
                run(1)
                if here(c) != start:
                    break
            c.clear_keys(key)
            if here(c) != start:
                break
        if here(c) == start:
            emu.snap(c, os.environ["RS_SNAP"]) if os.environ.get("RS_SNAP") else None
            return passed, "stuck at %s in %s (action %d, msg %d)" % (R.ltile(c), name, c.memory.u8[emu.PLAYER + 0x0c], c.memory.u8[BP.MSG])
        run(120)
        BP.settle(c, 60)
        passed.append(ROOMS.get(here(c)[1], here(c)))
    return passed, 'walked'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', default=os.path.join(P.ROOT, 'tmc-d3.gba'))
    a = ap.parse_args()
    bad = 0
    for tag, drop in (('FIX', 'WRN'), ('CONTROL', 'WR')):
        c = S.boot(a.rom, S.KINDS['REGION'], a=S.SHORT.index('WRN'), b=0, kit=0, diff=3, frames=300)
        usable(c)
        drop_row(c, S.SHORT.index(drop))
        BP.settle(c, 300)
        set_at_drop = flag(c)
        passed, note = walk(c)
        out = passed[-1] == 'ENTRANCE'
        ok = (set_at_drop and out) if tag == 'FIX' else (not set_at_drop and not out)
        bad += not ok
        print('%-8s %s  flag at drop %d  rooms %s  (%s)' % (tag, 'PASS' if ok else 'FAIL', set_at_drop,
                                                          ' -> '.join(map(str, passed)), note))
    c = S.boot(a.rom, S.KINDS['REGION'], a=S.SHORT.index('WR'), b=0, kit=0, diff=3, frames=300)
    usable(c)
    drop_row(c, S.SHORT.index('WR'))
    BP.settle(c, 300)
    kept = not flag(c)
    emu.warp(c, P.AREAS['AREA_RUINS'], P.ROOMS['ROOM_RUINS_TEKTITES'], 8 * 16 + 8, 5 * 16 + 8, frames=300)
    tektites = len(entities(c, KIND_ENEMY))
    ok = kept and not flag(c) and tektites > 0
    bad += not ok
    print('ENTRANCE %s  flag clear %d, tektites in the room %d' % ('PASS' if ok else 'FAIL', not flag(c), tektites))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
