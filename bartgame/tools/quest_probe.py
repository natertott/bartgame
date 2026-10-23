"""The three forest quests, played in the ROM.

  HUNT    the Hermit Knight: kill every monster in his glade, talk, a key drops
  FETCH   the Weeping Nun: take the relic from its chamber, bring it back,
          a heart container is granted
  TORCH   the Blind Gardener: light four censers with the lamp, talk, a key

Gates on the way are crossed by granting the items in RAM where needed
(the critical path probe proves the gates themselves).

    python3 tools/quest_probe.py [--seed N]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import probe as P  # noqa: E402
import critical_path as CP  # noqa: E402

S = os.environ.get('SNAPDIR', '/tmp')
res = []
ROLE = {0: '-', 1: 'ENTRY', 2: 'GOAL', 3: 'KEY', 4: 'chest', 5: 'hunt', 6: 'fetch', 7: 'torch', 8: 'relic', 9: 'shrine', 10: 'keych'}


def check(name, ok, detail=''):
    res.append(bool(ok))
    print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)


def grant_all(c):
    pl = P.sym('gPl')
    P.w8(c, pl + 8, 0x0F)   # items: sword, bombs, lamp, cloak
    P.w8(c, pl + 7, 20)     # bombs
    P.w8(c, pl + 6, 3)      # keys


def open_all_gates(c):
    """mark every crack, web and lock open in the world so rooms generate
    them open; chasms still need the cloak (granted)"""
    W = P.sym('gWorld')
    for i in range(25):
        a = W + 4 + i * 13
        opened = 0
        for s in range(4):
            if P.r8(c, a + s) in (3, 4, 5):
                opened |= 1 << s
        P.w8(c, a + 4, opened)


def clear_enemies(c):
    """monsters in the current room vanish: the walk is the test here"""
    A = P.sym('gActors')
    for i in range(1, 96):
        if P.actor(c, i)['kind'] == 2:
            P.w8(c, A + i * 64, 0)


def go(c, w, target):
    """BFS over all non-wall gates; chasms are jumped with the cloak"""
    from collections import deque
    cells = w['cells']
    start = CP.cell(c)
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == target:
            break
        for s in range(4):
            g = cells[cur]['gate'][s]
            if g in (0, 7):
                continue
            n = CP.ny_of(cur, s) if hasattr(CP, 'ny_of') else None
            x, y = cur % 5, cur // 5
            nx, ny = x + (1 if s == 1 else -1 if s == 3 else 0), y + (1 if s == 2 else -1 if s == 0 else 0)
            if not (0 <= nx < 5 and 0 <= ny < 5):
                continue
            n = ny * 5 + nx
            if n not in prev:
                prev[n] = (cur, s)
                q.append(n)
    route = []
    cur = target
    while prev.get(cur):
        p, s = prev[cur]
        route.append((p, s))
        cur = p
    route.reverse()
    for frm, s in route:
        g = cells[frm]['gate'][s]
        CP.heal(c)
        clear_enemies(c)
        # a hunt room counts its monsters: their vanishing can finish the
        # quest and open a box; close it before the walk
        P.run(c, 20)
        if P.r8(c, P.sym('gTbActive')):
            CP.dismiss(c)
        if g == 2:
            CP.face_gate(c, s)
            P.press(c, 'B', 2, 14)
            P.press(c, 'B', 2, 14)
        if g == 6:
            CP.equip_b(c, CP.EQ_CLOAK)
            x, y, key = CP.door_inside(s)
            CP.teleport(c, x, y)
            P.hold(c, key, 10)
            c.set_keys(P.key(c, key))
            P.press(c, 'A', 2, 0)
            for _ in range(70):
                c.run_frame()
            c.clear_keys(P.key(c, key))
            P.run(c, 60)
        else:
            CP.cross(c, s)
        if CP.cell(c) != (frm // 5 + (1 if s == 2 else -1 if s == 0 else 0)) * 5 + (frm % 5 + (1 if s == 1 else -1 if s == 3 else 0)):
            print('   crossing failed at', frm, 'side', s, 'now', CP.cell(c))
            return False
    return CP.cell(c) == target


def tt_floor(c, tx, ty):
    """is this tile plain floor, by the art's own type table"""
    sys.path.insert(0, os.path.join(HERE, '..', 'art'))
    import tiles
    v = CP.tt_at(c, tx, ty)
    return v is not None and v != 0xFFFF and tiles.METATILES[v]['type'] == 'FLOOR'


def npc_pos(c):
    a = CP.find_actor(c, 5)
    return a


def talk(c, npc):
    """stand below the NPC, face up, press A, then page through until the
    box closes (never re-opening it)"""
    tb = P.sym('gTbActive')
    if P.r8(c, tb):
        # a box is open already (a quest's own words): close it first, or
        # A would only turn its pages
        print('   (a box was open before the talk)')
        CP.dismiss(c)
    CP.heal(c)
    clear_enemies(c)
    CP.teleport(c, npc['x'], npc['y'] + 22)
    P.hold(c, 'UP', 6)
    P.press(c, 'A', 2, 30)
    print('   talk: box %d state %d hero %s' % (P.r8(c, tb), CP.gstate(c), P.player_pos(c)))
    for _ in range(12):
        if not P.r8(c, tb):
            break
        P.press(c, 'A', 2, 25)
    P.run(c, 10)


def main():
    seed = int(sys.argv[sys.argv.index('--seed') + 1], 0) if '--seed' in sys.argv else 0x28c
    c = P.boot(seed=seed)
    P.run(c, 20)
    w = CP.world(c)
    roles = {i: ROLE[w['cells'][i]['role']] for i in range(25)}
    print('seed', hex(seed), 'roles', {k: v for k, v in roles.items() if v != '-'})
    grant_all(c)
    open_all_gates(c)
    P.enter_forest(c)
    pl = P.sym('gPl')

    def cells_with(role):
        return [i for i in range(25) if roles[i] == role]

    # HUNT
    for cellid in cells_with('hunt')[:1]:
        ok = go(c, w, cellid)
        check('HUNT: reached the hermit', ok, 'cell %d' % CP.cell(c))
        npc = npc_pos(c)
        check('HUNT: the hermit stands in his glade', npc is not None and npc['type'] == 2, str(npc))
        if npc:
            talk(c, npc)
            # kill everything by hand: set each enemy's hp to 0 through the sword? use RAM
            A = P.sym('gActors')
            for i in range(1, 96):
                a = P.actor(c, i)
                if a['kind'] == 2:
                    P.w16(c, A + i * 64 + 26, 1)
            # strike each from behind (a thorn knight's shield takes hits
            # from the front), rotating through the survivors
            for step in range(60):
                en = [P.actor(c, i) for i in range(1, 96)]
                en = [e for e in en if e['kind'] == 2]
                if not en:
                    break
                e = en[step % len(en)]
                CP.heal(c)
                f = e['facing']  # 0 N, 1 E, 2 S, 3 W: stand on the far side
                if f == 1:
                    CP.teleport(c, e['x'] - 14, e['y'] + 2); key = 'RIGHT'
                elif f == 3:
                    CP.teleport(c, e['x'] + 14, e['y'] + 2); key = 'LEFT'
                elif f == 0:
                    CP.teleport(c, e['x'], e['y'] + 18); key = 'UP'
                else:
                    CP.teleport(c, e['x'], e['y'] - 14); key = 'DOWN'
                P.hold(c, key, 2)
                P.press(c, 'B', 2, 16)
            keys0 = P.r8(c, pl + 6)
            talk(c, npc)
            P.run(c, 60)
            # the key dropped: walk over it
            k = CP.find_actor(c, 4, 4)
            if k:
                CP.teleport(c, k['x'], k['y'] + 2)
                P.run(c, 10)
            check('HUNT: the reward key is given', P.r8(c, pl + 6) == keys0 + 1, 'keys %d -> %d' % (keys0, P.r8(c, pl + 6)))
            P.snap(c, os.path.join(S, 'q1.png'))

    # FETCH
    for cellid in cells_with('fetch')[:1]:
        relic_cell = w['cells'][cellid]['arg']
        ok = go(c, w, relic_cell)
        check('FETCH: reached the relic chamber', ok, 'cell %d (want %d)' % (CP.cell(c), relic_cell))
        r = CP.find_actor(c, 4, 5)
        check('FETCH: the relic lies there', r is not None, str(r))
        if r:
            CP.teleport(c, r['x'], r['y'] + 2)
            P.run(c, 10)
        check('FETCH: the relic is carried', P.r8(c, pl + 8) & 0x10, 'items 0x%02x' % P.r8(c, pl + 8))
        ok = go(c, w, cellid)
        check('FETCH: back to the nun', ok, 'cell %d' % CP.cell(c))
        npc = npc_pos(c)
        hpmax0 = P.r16(c, pl + 2)
        if npc:
            talk(c, npc)
        check('FETCH: the nun grants a heart container', P.r16(c, pl + 2) == hpmax0 + 8, 'hp_max %d -> %d' % (hpmax0, P.r16(c, pl + 2)))
        P.snap(c, os.path.join(S, 'q2.png'))

    # TORCH
    for cellid in cells_with('torch')[:1]:
        ok = go(c, w, cellid)
        check('TORCH: reached the gardener', ok, 'cell %d' % CP.cell(c))
        CP.equip_b(c, CP.EQ_LAMP)
        w_, h_, g = CP.room_tiles(c)
        torches = [k for k, v in g.items() if v == CP.mt('TORCH')]
        check('TORCH: four censers stand cold', len(torches) == 4, str(torches))
        for (tx, ty) in torches:
            # from below first, then whichever side has ground
            for dx, dy, key in ((0, 1, 'UP'), (-1, 0, 'RIGHT'), (1, 0, 'LEFT'), (0, -1, 'DOWN')):
                if tt_floor(c, tx + dx, ty + dy):
                    CP.heal(c)
                    clear_enemies(c)  # a bite cancels the swing: this tests the lamp
                    CP.teleport(c, (tx + dx) * 16 + 8, (ty + dy) * 16 + 14)
                    P.hold(c, key, 4)
                    P.press(c, 'A', 2, 30)
                    break
        w_, h_, g = CP.room_tiles(c)
        lit = [k for k, v in g.items() if v == CP.mt('TORCH_LIT')]
        check('TORCH: the lamp lights them', len(lit) == 4, 'lit %d' % len(lit))
        npc = npc_pos(c)
        keys0 = P.r8(c, pl + 6)
        if npc:
            talk(c, npc)
            P.run(c, 40)
            k = CP.find_actor(c, 4, 4)
            if k:
                CP.teleport(c, k['x'], k['y'] + 2)
                P.run(c, 10)
        check('TORCH: the gardener pays a key', P.r8(c, pl + 6) == keys0 + 1, 'keys %d -> %d' % (keys0, P.r8(c, pl + 6)))
        P.snap(c, os.path.join(S, 'q3.png'))
    print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
    return 0 if all(res) else 1


if __name__ == '__main__':
    sys.exit(main())
