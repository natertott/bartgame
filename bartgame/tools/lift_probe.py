"""The buttons and the hands, played in the ROM.

  ROLL     R while walking rolls
  LIFT     R before a bush lifts it: the hero carries it, the ground is bare
  THROW    R again throws it: it flies as an object, breaks, is gone
  BOULDER  R before a boulder only bumps; with the gauntlet it lifts
  PAUSE    START opens the pause menu, RIGHT walks the owned items, L puts
           the bombs on the L trigger, R turns to the map page, START closes

    python3 tools/lift_probe.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'art'))
import probe as P  # noqa: E402
import critical_path as CP  # noqa: E402
import tiles  # noqa: E402

S = os.environ.get('SNAPDIR', '/tmp')
res = []
PS_NORMAL, PS_ROLL, PS_LIFT, PS_CARRY = 0, 1, 10, 11
ITEM_BOMBS, ITEM_GAUNTLET = 0x02, 0x20
EQ_BOMBS = 2
GS_PLAY, GS_MAP = 1, 4
AK_OBJECT, OBJ_THROWN = 6, 20


def check(name, ok, detail=''):
    res.append(bool(ok))
    print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)


def ssym(name):
    """a static's address: the linker map lists its .bss section"""
    lines = open(P.MAP).read().splitlines()
    for i, l in enumerate(lines):
        parts = l.split()
        if parts and parts[0] == '.bss.' + name:
            if len(parts) >= 2 and parts[1].startswith('0x'):
                return int(parts[1], 16)
            return int(lines[i + 1].split()[0], 16)
    raise KeyError(name)


def warp(c, cell, side):
    """jump to a forest cell through the transition's own statics"""
    P.w8(c, ssym('sNextArea'), 1)
    P.w8(c, ssym('sNextCell'), cell)
    P.w8(c, ssym('sNextSide'), side)
    P.w8(c, ssym('sTransPhase'), 0)
    P.w8(c, P.sym('gGame'), 2)
    P.run(c, 70)
    assert CP.wait_play(c, 1), 'forest room transition did not settle'


def ttype(v):
    return tiles.METATILES[v]['type'] if v != 0xFFFF else 'NONE'


def state(c):
    return P.actor(c, 0)['state']


def find_tile(c, name):
    """(tx, ty, side, key) for a tile of this metatile with a floor tile
    beside it to stand on, or None"""
    w, h, g = CP.room_tiles(c)
    want = CP.mt(name)
    for (x, y), v in g.items():
        if v != want:
            continue
        for dx, dy, key in ((0, 1, 'UP'), (0, -1, 'DOWN'), (-1, 0, 'RIGHT'), (1, 0, 'LEFT')):
            n = g.get((x + dx, y + dy))
            if n is not None and ttype(n) == 'FLOOR':
                return x, y, (x + dx, y + dy), key
    return None


def stand_before(c, spot, key):
    sx, sy = spot
    CP.heal(c)
    CP.clear_enemies(c)
    CP.teleport(c, sx * 16 + 8, sy * 16 + 14)
    P.hold(c, key, 3)
    P.run(c, 2)


def thrown(c):
    for i in range(1, 96):
        a = P.actor(c, i)
        if a['kind'] == AK_OBJECT and a['type'] == OBJ_THROWN:
            return a
    return None


def main():
    c = P.boot()
    P.run(c, 40)
    w = CP.world(c)
    P.enter_forest(c)
    pl = P.sym('gPl')
    # ROLL: R while walking
    CP.heal(c)
    CP.clear_enemies(c)
    x, y, key = CP.door_inside(2)
    CP.teleport(c, x, y - 40)
    P.hold(c, 'UP', 4)
    P.hold(c, ['UP', 'R'], 2)
    rolled = False
    for _ in range(6):
        rolled = rolled or state(c) == PS_ROLL
        P.hold(c, 'UP', 1)
    P.run(c, 30)
    check('ROLL: R while walking rolls', rolled, 'state %d' % state(c))
    # LIFT: a bush in the entry room
    found = find_tile(c, 'BUSH')
    check('LIFT: the entry room grows a bush', found is not None, str(found))
    if found:
        bx, by, spot, key = found
        stand_before(c, spot, key)
        P.press(c, 'R', 2, 0)
        for _ in range(24):
            if state(c) == PS_CARRY:
                break
            c.run_frame()
        P.snap(c, os.path.join(S, 'lift1.png'))
        w_, h_, g = CP.room_tiles(c)
        check('LIFT: R lifts it and the hero carries it', state(c) == PS_CARRY, 'state %d' % state(c))
        check('LIFT: the ground under it is bare', ttype(g[(bx, by)]) == 'FLOOR', tiles.METATILES[g[(bx, by)]]['name'])
        # carry a few steps, then THROW: the object is looked for on the
        # frame after the press, before it can break on a near wall
        P.hold(c, 'DOWN', 12)
        P.hold(c, 'R', 1)
        t = thrown(c)
        P.run(c, 3)
        P.snap(c, os.path.join(S, 'lift2.png'))
        check('THROW: R throws it as an object', t is not None and state(c) == PS_NORMAL, 'object %s state %d' % (t is not None, state(c)))
        P.run(c, 90)
        check('THROW: it breaks and is gone', thrown(c) is None, '')
    # BOULDER: find a room with one
    boulder = None
    for cell in range(25):
        gates = w['cells'][cell]['gate']
        side = [s for s in range(4) if gates[s] != 0][0]
        warp(c, cell, side)
        boulder = find_tile(c, 'BOULDER')
        if boulder:
            break
    check('BOULDER: a room keeps a boulder', boulder is not None, 'cell %d %s' % (cell, boulder))
    if boulder:
        bx, by, spot, key = boulder
        P.w8(c, pl + 8, P.r8(c, pl + 8) & ~ITEM_GAUNTLET)
        stand_before(c, spot, key)
        P.press(c, 'R', 2, 0)
        P.run(c, 16)
        check('BOULDER: without the gauntlet it only bumps', state(c) == PS_NORMAL, 'state %d' % state(c))
        P.w8(c, pl + 8, P.r8(c, pl + 8) | ITEM_GAUNTLET)
        stand_before(c, spot, key)
        P.press(c, 'R', 2, 0)
        for _ in range(24):
            if state(c) == PS_CARRY:
                break
            c.run_frame()
        P.snap(c, os.path.join(S, 'lift3.png'))
        check('BOULDER: with the gauntlet it lifts', state(c) == PS_CARRY, 'state %d' % state(c))
        P.press(c, 'R', 2, 0)
        P.run(c, 90)
        w_, h_, g = CP.room_tiles(c)
        check('BOULDER: thrown, the alcove is open', ttype(g[(bx, by)]) == 'FLOOR', tiles.METATILES[g[(bx, by)]]['name'])
    # PAUSE: the bombs on L
    P.w8(c, pl + 8, P.r8(c, pl + 8) | ITEM_BOMBS)
    P.w8(c, pl + 7, 5)
    P.w8(c, pl + 11, 0)
    P.press(c, 'START', 2, 6)
    check('PAUSE: START opens the pause menu', CP.gstate(c) == GS_MAP, 'state %d' % CP.gstate(c))
    P.snap(c, os.path.join(S, 'pause1.png'))
    P.press(c, 'RIGHT', 2, 4)
    P.press(c, 'RIGHT', 2, 4)  # sword, shield, then the bombs
    P.press(c, 'L', 2, 4)
    check('PAUSE: L puts the bombs on the L trigger', P.r8(c, pl + 11) == EQ_BOMBS, 'equip %d %d %d' % (P.r8(c, pl + 9), P.r8(c, pl + 10), P.r8(c, pl + 11)))
    P.snap(c, os.path.join(S, 'pause2.png'))
    P.press(c, 'R', 2, 4)
    P.snap(c, os.path.join(S, 'pause3.png'))
    P.press(c, 'START', 2, 6)
    check('PAUSE: START closes it', CP.gstate(c) == GS_PLAY, 'state %d' % CP.gstate(c))
    # the L trigger now drops a bomb
    before = P.r8(c, pl + 7)
    P.press(c, 'L', 2, 10)
    check('PAUSE: the L trigger uses the bombs', P.r8(c, pl + 7) == before - 1, 'bombs %d -> %d' % (before, P.r8(c, pl + 7)))
    P.snap(c, os.path.join(S, 'lift4.png'))
    print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
    return 0 if all(res) else 1


if __name__ == '__main__':
    sys.exit(main())
