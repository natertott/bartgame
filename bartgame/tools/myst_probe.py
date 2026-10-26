"""The mystery rooms, played in the ROM: every kind forced in turn on one
cell of the pinned seed, entered through its mouth, played to its reward,
and left by its way out.

    python3 tools/myst_probe.py [--seed N]
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
MYST_OFF = 4 + 25 * 13 + 2 + 3 + 3 + 3 + 25 + 1 + 1
FLAGS_OFF = MYST_OFF + 25
KINDS = ['none', 'pots', 'chest', 'npc', 'fairy', 'waves', 'survive', 'miniboss', 'switches', 'torches', 'boulders']
AREA_MYST = 2
GILT, KEYS, BOMBS, ITEMS, PIECES = 4, 6, 7, 8, 30


def check(name, ok, detail=''):
    res.append(bool(ok))
    print('%s %-46s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)


def area(c):
    return P.r8(c, P.sym('gGame') + 1)


def pack(kind, size, style):
    return KINDS.index(kind) | (size << 4) | (style << 6)


def grid(c, layer=0):
    R = P.sym('gRoom')
    w, h = P.r8(c, R), P.r8(c, R + 1)
    base = R + 2 + layer * 2048
    g = {}
    for y in range(h):
        for x in range(w):
            g[(x, y)] = P.r16(c, base + (y * 32 + x) * 2) & 0xFFFF
    return w, h, g


def tiles_of(c, pred, layer=0):
    w, h, g = grid(c, layer)
    return [k for k, v in g.items() if v != 0xFFFF and pred(tiles.METATILES[v])]


def enter(c, cell, kind, size, style):
    """force the cell's mystery, warp there, walk into the mouth"""
    P.w8(c, P.sym('gWorld') + MYST_OFF + cell, pack(kind, size, style))
    P.w8(c, P.sym('gWorld') + FLAGS_OFF + cell, 0)
    gates = CP.world(c)['cells'][cell]['gate']
    LP.warp(c, cell, [s for s in range(4) if gates[s]][0])
    mouths = tiles_of(c, lambda m: m['name'].startswith('mouth_'))
    if not mouths:
        return False
    mx, my = mouths[0]
    CP.heal(c); CP.clear_enemies(c)
    CP.teleport(c, mx * 16 + 8, (my + 1) * 16 + 14)
    for i in range(40):
        P.hold(c, 'UP', 2)
        if area(c) == AREA_MYST:
            break
    P.run(c, 60)
    return area(c) == AREA_MYST


def leave(c):
    w, h, g = grid(c)
    CP.heal(c); CP.clear_enemies(c)
    CP.teleport(c, (w // 2) * 16, (h - 2) * 16 + 10)
    for i in range(40):
        P.hold(c, 'DOWN', 2)
        if area(c) != AREA_MYST:
            break
    P.run(c, 60)
    return area(c)


def open_chest(c):
    chests = tiles_of(c, lambda m: m['type'] == 'CHEST')
    if not chests:
        return False
    tx, ty = chests[0]
    CP.heal(c); CP.clear_enemies(c)
    CP.teleport(c, tx * 16 + 8, (ty + 1) * 16 + 14)
    P.hold(c, 'UP', 20)
    P.run(c, 30)
    CP.dismiss(c)
    return not tiles_of(c, lambda m: m['type'] == 'CHEST')


def kill_all(c):
    CP.clear_enemies(c)


def main():
    seed = int(sys.argv[sys.argv.index('--seed') + 1], 0) if '--seed' in sys.argv else 0xB4A7
    c = P.boot(seed=seed)
    P.run(c, 40)
    w = CP.world(c)
    pl = P.sym('gPl')
    P.enter_forest(c)
    W = P.sym('gWorld')
    mysts = [(i, P.r8(c, W + MYST_OFF + i)) for i in range(25) if P.r8(c, W + MYST_OFF + i)]
    check('WORLD: the wood has mystery rooms', 5 <= len(mysts) <= 15, '%d: %s' % (len(mysts), [(i, KINDS[m & 15], (m >> 4) & 3, (m >> 6) & 3) for i, m in mysts]))
    cell = [i for i in range(25) if i not in (w['entry'], w['goal']) and w['cells'][i]['role'] != 7][0]
    # CHEST, small cave
    ok = enter(c, cell, 'chest', 0, 0)
    check('CHEST: a mouth in the wall leads into a cave', ok, 'area %d' % area(c))
    P.snap(c, os.path.join(S, 'myst_chest.png'))
    g0 = P.r16(c, pl + GILT)
    check('CHEST: the chest opens and pays ten gilt', open_chest(c) and P.r16(c, pl + GILT) == g0 + 10, 'gilt %d -> %d' % (g0, P.r16(c, pl + GILT)))
    check('CHEST: the way out leads back to the wood', leave(c) == 1 and CP.cell(c) == cell, 'area %d cell %d' % (area(c), CP.cell(c)))
    # POTS, medium hollow
    ok = enter(c, cell, 'pots', 1, 1)
    check('POTS: a medium hollow', ok, 'area %d' % area(c))
    P.snap(c, os.path.join(S, 'myst_pots.png'))
    g0 = P.r16(c, pl + GILT)
    pots = tiles_of(c, lambda m: m['name'] == 'myst_pot', 1)
    for (tx, ty) in pots:
        # lift each pot, drop it, and gather whatever lies on the floor
        CP.heal(c)
        CP.teleport(c, tx * 16 + 8, (ty + 1) * 16 + 14)
        P.hold(c, 'UP', 3)
        P.press(c, 'R', 2, 16)
        P.press(c, 'R', 2, 40)
        for i in range(1, 96):
            a = P.actor(c, i)
            if a['kind'] == 4:
                CP.teleport(c, a['x'], a['y'] + 2)
                P.run(c, 8)
    check('POTS: one pot held the prize', P.r16(c, pl + GILT) >= g0 + 10, 'gilt %d -> %d (%d pots)' % (g0, P.r16(c, pl + GILT), len(pots)))
    leave(c)
    # SWITCHES, medium thicket
    ok = enter(c, cell, 'switches', 1, 2)
    check('SWITCHES: a medium thicket', ok, 'area %d' % area(c))
    P.snap(c, os.path.join(S, 'myst_switches.png'))
    sw = tiles_of(c, lambda m: m['name'] == 'myst_switch', 1)
    for (tx, ty) in sw:
        CP.teleport(c, tx * 16 + 8, ty * 16 + 12)
        P.run(c, 6)
    P.run(c, 20)
    check('SWITCHES: every plate pressed, a chest appears', len(sw) == 4 and bool(tiles_of(c, lambda m: m['type'] == 'CHEST')), 'plates %d' % len(sw))
    k0 = P.r8(c, pl + PIECES)
    check('SWITCHES: the chest pays a piece of heart', open_chest(c) and P.r8(c, pl + PIECES) == k0 + 1, 'pieces %d -> %d' % (k0, P.r8(c, pl + PIECES)))
    leave(c)
    # WAVES, large cave
    ok = enter(c, cell, 'waves', 2, 0)
    check('WAVES: a large cave', ok, 'area %d' % area(c))
    exits = tiles_of(c, lambda m: m['type'] == 'MYST')
    check('WAVES: the way out is shut', len(exits) == 0, 'exits %d' % len(exits))
    P.run(c, 60)
    n1 = len([i for i in range(1, 96) if P.actor(c, i)['kind'] == 2])
    P.snap(c, os.path.join(S, 'myst_waves.png'))
    for wave in range(3):
        kill_all(c)
        P.run(c, 70)
    check('WAVES: monsters came in waves', n1 >= 3, 'first wave %d' % n1)
    check('WAVES: three waves down, a chest and the way out', bool(tiles_of(c, lambda m: m['type'] == 'CHEST')) and len(tiles_of(c, lambda m: m['type'] == 'MYST')) == 2, '')
    keys0 = P.r8(c, pl + KEYS)
    check('WAVES: the large chest pays a key', open_chest(c) and P.r8(c, pl + KEYS) == keys0 + 1, 'keys %d -> %d' % (keys0, P.r8(c, pl + KEYS)))
    leave(c)
    # MINIBOSS, large hollow
    ok = enter(c, cell, 'miniboss', 2, 1)
    check('MINIBOSS: a large hollow', ok, 'area %d' % area(c))
    P.run(c, 60)
    knights = [i for i in range(1, 96) if P.actor(c, i)['kind'] == 2 and P.actor(c, i)['type'] == 4]
    P.snap(c, os.path.join(S, 'myst_miniboss.png'))
    check('MINIBOSS: a knight captain with twenty hp', len(knights) == 1 and P.actor(c, knights[0])['hp'] == 20, str([P.actor(c, i)['hp'] for i in knights]))
    kill_all(c); P.run(c, 20)
    check('MINIBOSS: slain, a chest', bool(tiles_of(c, lambda m: m['type'] == 'CHEST')), '')
    leave(c)
    # SURVIVE, small thicket
    ok = enter(c, cell, 'survive', 0, 2)
    check('SURVIVE: a small thicket', ok, 'area %d' % area(c))
    for i in range(16):
        P.run(c, 60); kill_all(c)
    P.run(c, 30)
    check('SURVIVE: the clock runs out, a chest', bool(tiles_of(c, lambda m: m['type'] == 'CHEST')), '')
    leave(c)
    # FAIRY, small hollow
    ok = enter(c, cell, 'fairy', 0, 1)
    check('FAIRY: a small hollow', ok, 'area %d' % area(c))
    P.w16(c, pl, 6)
    spring = tiles_of(c, lambda m: m['name'].endswith('_spring'))
    if spring:
        CP.teleport(c, spring[0][0] * 16 + 8, spring[0][1] * 16 + 12)
        P.run(c, 10); CP.dismiss(c)
    P.snap(c, os.path.join(S, 'myst_fairy.png'))
    check('FAIRY: the spring fills the hearts', P.r16(c, pl) == P.r16(c, pl + 2), 'hp %d / %d' % (P.r16(c, pl), P.r16(c, pl + 2)))
    leave(c)
    # NPC, small cave
    ok = enter(c, cell, 'npc', 0, 0)
    check('NPC: a stranger in a small cave', ok and CP.find_actor(c, 5) is not None, '')
    P.w16(c, pl + GILT, 25)
    npc = CP.find_actor(c, 5)
    p0 = P.r8(c, pl + PIECES)
    if npc:
        CP.teleport(c, npc['x'], npc['y'] + 22); P.hold(c, 'UP', 6)
        P.press(c, 'A', 2, 30); CP.dismiss(c)
    P.snap(c, os.path.join(S, 'myst_npc.png'))
    check('NPC: ten gilt buys a piece of heart', P.r16(c, pl + GILT) == 15 and P.r8(c, pl + PIECES) == p0 + 1, 'gilt %d pieces %d' % (P.r16(c, pl + GILT), P.r8(c, pl + PIECES)))
    leave(c)
    # TORCHES, medium thicket, with the lamp on A
    P.w8(c, pl + ITEMS, P.r8(c, pl + ITEMS) | 0x04)
    CP.equip_b(c, CP.EQ_LAMP)
    ok = enter(c, cell, 'torches', 1, 2)
    check('TORCHES: a medium thicket', ok, '')
    for (tx, ty) in tiles_of(c, lambda m: m['name'] == 'torch'):
        CP.heal(c); CP.teleport(c, tx * 16 + 8, (ty + 1) * 16 + 14)
        P.hold(c, 'UP', 4); P.press(c, 'A', 2, 30)
    P.run(c, 20)
    check('TORCHES: three censers lit, a chest', bool(tiles_of(c, lambda m: m['type'] == 'CHEST')), 'unlit %d' % len(tiles_of(c, lambda m: m['name'] == 'torch')))
    P.snap(c, os.path.join(S, 'myst_torches.png'))
    leave(c)
    # BOULDERS, large thicket, with the gauntlet
    P.w8(c, pl + ITEMS, P.r8(c, pl + ITEMS) | 0x20)
    ok = enter(c, cell, 'boulders', 2, 2)
    check('BOULDERS: a large thicket', ok, '')
    for (tx, ty) in tiles_of(c, lambda m: m['name'] == 'boulder'):
        CP.heal(c); CP.teleport(c, tx * 16 + 8, (ty + 1) * 16 + 14)
        P.hold(c, 'UP', 3); P.press(c, 'R', 2, 16); P.press(c, 'R', 2, 50)
    P.run(c, 20)
    check('BOULDERS: every boulder lifted, a chest', bool(tiles_of(c, lambda m: m['type'] == 'CHEST')), 'left %d' % len(tiles_of(c, lambda m: m['name'] == 'boulder')))
    P.snap(c, os.path.join(S, 'myst_boulders.png'))
    check('BOULDERS: the way out, and the wood', leave(c) == 1, '')
    print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
    return 0 if all(res) else 1


if __name__ == '__main__':
    sys.exit(main())
