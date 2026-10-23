"""The shield, the water's edge and the holes, played in the ROM.

  START    the run begins with the sword on B and the Bark Shield on L
  WATER    walking into water, the hero goes under the moment his feet
           cross the tile's edge, drowns in place, comes back on safe ground
  HOLE     the chasm gate without the cloak: he shrinks into the hole
  SHIELD   held up (L), a bite from the front is turned, a bite from
           behind is not

    python3 tools/guard_probe.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'art'))
import probe as P  # noqa: E402
import critical_path as CP  # noqa: E402
import lift_probe as LP  # noqa: E402
import tiles  # noqa: E402

S = os.environ.get('SNAPDIR', '/tmp')
res = []
PS_NORMAL, PS_FALL = 0, 4
EQ_SWORD, EQ_SHIELD = 1, 5


def check(name, ok, detail=''):
    res.append(bool(ok))
    print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)


def state(c):
    return P.actor(c, 0)['state']


def water_edge(c):
    """a water tile with floor to its west, both reached: (tx, ty)"""
    w, h, g = CP.room_tiles(c)
    for (x, y), v in sorted(g.items()):
        if tiles.METATILES[v]['type'] == 'WATER' and x > 2:
            l = g.get((x - 1, y)); l2 = g.get((x - 2, y))
            if l is not None and l2 is not None and tiles.METATILES[l]['type'] == 'FLOOR' and tiles.METATILES[l2]['type'] == 'FLOOR':
                return x, y
    return None


def main():
    c = P.boot()
    P.run(c, 40)
    w = CP.world(c)
    pl = P.sym('gPl')
    eq = [P.r8(c, pl + 9 + i) for i in range(3)]
    check('START: sword on B, shield on L, A free', eq == [0, EQ_SWORD, EQ_SHIELD], 'equip %s' % eq)
    P.enter_forest(c)
    P.snap(c, os.path.join(S, 'guard0.png'))
    # WATER: a pond room
    found = None
    for cell in range(25):
        gates = w['cells'][cell]['gate']
        LP.warp(c, cell, [s for s in range(4) if gates[s]][0])
        found = water_edge(c)
        if found:
            break
    check('WATER: a room has water with ground to its west', found is not None, 'cell %d %s' % (cell, found))
    if found:
        tx, ty = found
        CP.heal(c); CP.clear_enemies(c)
        CP.teleport(c, (tx - 2) * 16 + 8, ty * 16 + 12)
        P.hold(c, 'RIGHT', 2)
        edge = tx * 16
        x_at_fall = None
        for i in range(60):
            P.hold(c, 'RIGHT', 1)
            if state(c) == PS_FALL:
                x_at_fall = P.player_pos(c)[0]
                break
        # the feet point stood where? (the hero snaps to the tile's middle on falling, so measure the frame before)
        check('WATER: the hero goes under', x_at_fall is not None, 'state %d' % state(c))
        snaps = []
        for k in range(4):
            P.snap(c, os.path.join(S, 'drown%d.png' % k)); snaps.append(k)
            P.run(c, 8)
        P.run(c, 40)
        check('WATER: back on safe ground, a quarter heart down', state(c) == PS_NORMAL and CP.pl(c, 0, True) == 22, 'state %d hp %d pos %s' % (state(c), CP.pl(c, 0, True), P.player_pos(c)))
        # how far past the edge did the feet get before going under: walk again, one frame at a time, reading x
        CP.heal(c)
        CP.teleport(c, (tx - 2) * 16 + 8, ty * 16 + 12)
        P.hold(c, 'RIGHT', 2)
        last = P.player_pos(c)[0]
        for i in range(60):
            P.hold(c, 'RIGHT', 1)
            if state(c) == PS_FALL:
                break
            last = P.player_pos(c)[0]
        check('WATER: it happens within 2 px of the edge', edge - 1 <= last <= edge + 2, 'feet x %d edge %d' % (last, edge))
        P.run(c, 80)
    # HOLE: a chasm gate, no cloak
    chasm = [(i, s) for i in range(25) for s in range(4) if w['cells'][i]['gate'][s] == 6]
    check('HOLE: a chasm gate exists', bool(chasm), str(chasm[:2]))
    if chasm:
        cell, side = chasm[0]
        LP.warp(c, cell, [s for s in range(4) if w['cells'][cell]['gate'][s] not in (0, 6)][0])
        CP.heal(c); CP.clear_enemies(c)
        x, y, key = CP.door_inside(side)
        CP.teleport(c, x, y)
        fell = False
        for i in range(60):
            P.hold(c, key, 1)
            if state(c) == PS_FALL:
                fell = True
                break
        check('HOLE: he falls in at the chasm', fell, 'state %d pos %s' % (state(c), P.player_pos(c)))
        for k in range(3):
            P.snap(c, os.path.join(S, 'hole%d.png' % k))
            P.run(c, 8)
        P.run(c, 60)
        check('HOLE: back on safe ground', state(c) == PS_NORMAL and CP.cell(c) == cell, 'state %d cell %d' % (state(c), CP.cell(c)))
    # SHIELD: a beetle at the front, then at the back
    P.enter_forest(c) if False else None
    LP.warp(c, w['entry'], 2)
    CP.heal(c); CP.clear_enemies(c)
    hx, hy = 256, 230
    CP.teleport(c, hx, hy)
    d = P.sym('gDbgSpawn')
    P.w16(c, d, (1 << 8) | 0); P.w16(c, d + 2, 0)
    P.run(c, 3)
    A = P.sym('gActors')
    beetle = None
    for i in range(1, 96):
        if P.actor(c, i)['kind'] == 2:
            beetle = i
            break
    check('SHIELD: a beetle is spawned', beetle is not None, '')
    if beetle is not None:
        def put_beetle(bx, by):
            a = A + beetle * 64
            P.w16(c, a + 8, 0); P.w16(c, a + 10, bx); P.w16(c, a + 12, 0); P.w16(c, a + 14, by)
            P.w8(c, a + 28, 0)  # no iframes
        # face up, shield up, the beetle just north
        P.hold(c, 'UP', 2)
        hp0 = CP.pl(c, 0, True)
        c.set_keys(P.key(c, 'L'))
        P.run(c, 2)
        P.snap(c, os.path.join(S, 'guard_n.png'))
        put_beetle(hx, hy - 14)
        P.run(c, 12)
        hp1 = CP.pl(c, 0, True)
        P.snap(c, os.path.join(S, 'guard_block.png'))
        check('SHIELD: a bite from the front is turned', hp1 == hp0 and state(c) == PS_NORMAL, 'hp %d -> %d state %d' % (hp0, hp1, state(c)))
        # facing the shield down for the picture
        c.clear_keys(P.key(c, 'L'))
        CP.clear_enemies(c)
        P.hold(c, 'DOWN', 2); c.set_keys(P.key(c, 'L')); P.run(c, 2)
        P.snap(c, os.path.join(S, 'guard_s.png'))
        P.hold(c, 'RIGHT', 2); c.set_keys(P.key(c, 'L')); P.run(c, 2)
        P.snap(c, os.path.join(S, 'guard_e.png'))
        c.clear_keys(P.key(c, 'L'))
        # a bite from behind, shield still up: it lands
        P.w16(c, d, (1 << 8) | 0); P.w16(c, d + 2, 0)
        P.run(c, 3)
        beetle = next(i for i in range(1, 96) if P.actor(c, i)['kind'] == 2)
        P.hold(c, 'UP', 2)
        CP.teleport(c, hx, hy)
        c.set_keys(P.key(c, 'L')); P.run(c, 2)
        hp0 = CP.pl(c, 0, True)
        put_beetle(hx, hy + 14)
        P.run(c, 12)
        c.clear_keys(P.key(c, 'L'))
        check('SHIELD: a bite from behind lands', CP.pl(c, 0, True) < hp0, 'hp %d -> %d' % (hp0, CP.pl(c, 0, True)))
    # the pause menu shows the shield
    P.run(c, 40); CP.heal(c)
    P.press(c, 'START', 2, 6)
    P.snap(c, os.path.join(S, 'guard_pause.png'))
    P.press(c, 'START', 2, 6)
    print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
    return 0 if all(res) else 1


if __name__ == '__main__':
    sys.exit(main())
