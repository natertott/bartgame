"""Walk the maze's critical path in the real ROM: every key gate opened
with its key item, in order, until the goal room.

  KEYS     each key chest opens and grants its item
  CRACK    a bomb beside the cracked wall opens it
  WEB      the lamp burns the web
  CHASM    the cloak leaps the chasm
  GOAL     the goal room is entered

Rooms are crossed by teleporting the hero next to the door and walking
through it (the probe tests gates, not room interiors).

    python3 tools/critical_path.py [--rom bartgame.gba]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import probe as P  # noqa: E402

S = os.environ.get('SNAPDIR', '/tmp')
GATE = {0: 'WALL', 1: 'open', 2: 'thorn', 3: 'CRACK', 4: 'WEB', 5: 'LOCK', 6: 'CHASM', 7: 'exit'}
W_ROOM, H_ROOM = 24, 16
res = []


def check(name, ok, detail=''):
    res.append(bool(ok))
    print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)


def world(c):
    W = P.sym('gWorld')
    cells = []
    for i in range(25):
        a = W + 4 + i * 13
        cells.append({'gate': [P.r8(c, a + s) for s in range(4)], 'role': P.r8(c, a + 5), 'arg': P.r8(c, a + 6),
                      'stage': P.r8(c, a + 7)})
    base = W + 4 + 25 * 13
    entry, goal = P.r8(c, base), P.r8(c, base + 1)
    gate_cell = [P.r8(c, base + 2 + i) for i in range(3)]
    gate_side = [P.r8(c, base + 5 + i) for i in range(3)]
    key_cell = [P.r8(c, base + 8 + i) for i in range(3)]
    path_len = P.r8(c, base + 11 + 25)
    path = [P.r8(c, base + 11 + i) for i in range(path_len)]
    return {'cells': cells, 'entry': entry, 'goal': goal, 'gate_cell': gate_cell, 'gate_side': gate_side,
            'key_cell': key_cell, 'path': path}


def cell(c):
    return P.r8(c, P.sym('gGame') + 2)


def gstate(c):
    return P.r8(c, P.sym('gGame'))


def teleport(c, x, y):
    a = P.sym('gActors')
    P.w16(c, a + 8, 0); P.w16(c, a + 10, x)
    P.w16(c, a + 12, 0); P.w16(c, a + 14, y)
    for _ in range(3):
        c.run_frame()


def room_tiles(c):
    R = P.sym('gRoom')
    w, h = P.r8(c, R), P.r8(c, R + 1)
    g = {}
    for y in range(h):
        for x in range(w):
            g[(x, y)] = P.r16(c, R + 2 + (y * 32 + x) * 2) & 0xFFFF
    return w, h, g


def mt(name):
    return int(open(os.path.join(HERE, '..', 'build', 'gen', 'assets.h')).read().split('#define MT_%s ' % name)[1].split()[0])


def tt_at(c, tx, ty):
    """metatile type at a tile, via metatile_type in ROM (assets.h ids)"""
    w, h, g = room_tiles(c)
    return g.get((tx, ty))


def dismiss(c, frames=400):
    """Close item-get and text boxes: A presses until play resumes."""
    for _ in range(frames // 8):
        P.press(c, 'A', 2, 6)
        st = P.actor(c, 0)['state']
        if st == 0:
            break
    for _ in range(10):
        c.run_frame()


def door_inside(side):
    """a standing spot two tiles inside a door (the tiles the generator
    keeps clear), and the key to walk out. The hero's feet are 4 px above
    the y given, so the north spot sits one row lower than the others."""
    if side == 0:
        return (W_ROOM * 8, 3 * 16 + 8, 'UP')
    if side == 2:
        return (W_ROOM * 8, (H_ROOM - 3) * 16 + 8, 'DOWN')
    if side == 1:
        return ((W_ROOM - 3) * 16 + 8, H_ROOM * 8 + 8, 'RIGHT')
    return (2 * 16 + 8, H_ROOM * 8 + 8, 'LEFT')


def heal(c):
    P.w16(c, P.sym('gPl'), 24)


def cross(c, side, frames=160):
    """leave the current room through a side; returns the new cell. The
    hero is healed first: this tests gates, not fights."""
    x, y, key = door_inside(side)
    heal(c)
    teleport(c, x, y)
    before = cell(c)
    P.hold(c, key, frames)
    for _ in range(60):
        c.run_frame()
    if P.r8(c, P.sym('gTbActive')):
        # walked into a chest or a sign on arrival: close it
        dismiss(c)
    return cell(c), before


def side_between(a, b):
    ax, ay, bx, by = a % 5, a // 5, b % 5, b // 5
    if by == ay - 1: return 0
    if bx == ax + 1: return 1
    if by == ay + 1: return 2
    return 3


def face_gate(c, side):
    x, y, key = door_inside(side)
    teleport(c, x, y)
    P.hold(c, key, 24)  # walk up to the gate tiles
    for _ in range(5):
        c.run_frame()


def clear_enemies(c):
    """monsters in the room vanish: this probe tests gates and chests,
    not fights (a bite at the teleport knocks the hero off the chest)"""
    A = P.sym('gActors')
    for i in range(1, 96):
        if P.actor(c, i)['kind'] == 2:
            P.w8(c, A + i * 64, 0)


def open_chest(c):
    """stand under the room's chest and push into it; up to three tries"""
    w, h, g = room_tiles(c)
    chest = [k for k, v in g.items() if v == mt('CHEST')]
    if not chest:
        return False
    tx, ty = chest[0]
    for attempt in range(3):
        heal(c)
        clear_enemies(c)
        P.run(c, 4)
        teleport(c, tx * 16 + 8, (ty + 1) * 16 + 14)
        P.hold(c, 'UP', 20)
        for _ in range(80):
            c.run_frame()
        dismiss(c)
        if tt_at(c, tx, ty) == mt('CHEST_OPEN'):
            return True
    return False


def pl(c, off, w=False):
    s = P.sym('gPl')
    return P.r16(c, s + off) if w else P.r8(c, s + off)


ITEMS, BOMBS, KEYS = 8, 7, 6


def main():
    c = P.boot()
    P.run(c, 40)
    w = world(c)
    print('entry', w['entry'], 'goal', w['goal'], 'path', w['path'])
    print('gates', [(w['gate_cell'][i], w['gate_side'][i], GATE[w['cells'][w['gate_cell'][i]]['gate'][w['gate_side'][i]]]) for i in range(3)])
    print('keys', w['key_cell'])
    # into the forest
    P.hold(c, 'UP', 150); P.hold(c, 'RIGHT', 14); P.hold(c, 'UP', 60); P.run(c, 40)
    check('ENTRY: the drain leads to the entry cell', cell(c) == w['entry'], 'cell %d' % cell(c))

    def go_to(target):
        """follow tree edges by BFS over the world's open gates"""
        cells = w['cells']
        from collections import deque
        start = cell(c)
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
        for (frm, s) in route:
            g = cells[frm]['gate'][s]
            if g == 2:  # thorns: cut them first
                heal(c)
                face_gate(c, s)
                for _ in range(2):
                    P.press(c, 'A', 2, 14)
            elif g == 5 and pl(c, KEYS) == 0:
                print('   route needs a key at', frm, s)
            new, before = cross(c, s)
            print('   cross %d side %d: %d -> %d pos %s hp %d' % (frm, s, before, new, P.player_pos(c), pl(c, 0, True)), flush=True)
            if new == before:
                # maybe a thorn remained; try once more
                face_gate(c, s)
                P.press(c, 'A', 2, 14)
                new, before = cross(c, s)
            if new != (ny_of(frm, s)):
                print('   crossing failed at', frm, 'side', s, 'got', new)
                return False
        return cell(c) == target

    def ny_of(frm, s):
        x, y = frm % 5, frm // 5
        nx, ny = x + (1 if s == 1 else -1 if s == 3 else 0), y + (1 if s == 2 else -1 if s == 0 else 0)
        return ny * 5 + nx

    # 1. bombs
    ok = go_to(w['key_cell'][0])
    check('KEYS: reached the bombs chest room', ok, 'cell %d' % cell(c))
    open_chest(c)
    check('KEYS: the chest grants the bombs', pl(c, ITEMS) & 2, 'items 0x%02x bombs %d' % (pl(c, ITEMS), pl(c, BOMBS)))
    P.snap(c, os.path.join(S, 'cp1.png'))
    # 2. the crack: go to the gate cell, bomb it
    gc, gs = w['gate_cell'][0], w['gate_side'][0]
    ok = go_to(gc)
    check('CRACK: reached the cracked wall', ok, 'cell %d' % cell(c))
    face_gate(c, gs)
    P.press(c, 'B', 2, 4)
    x, y, key = door_inside(gs)
    P.hold(c, {'UP': 'DOWN', 'DOWN': 'UP', 'LEFT': 'RIGHT', 'RIGHT': 'LEFT'}[key], 30)
    P.run(c, 170)
    P.snap(c, os.path.join(S, 'cp2.png'))
    new, before = cross(c, gs)
    check('CRACK: the bomb opened it', new == ny_of(gc, gs), 'cell %d -> %d' % (before, new))
    # 3. lamp
    ok = go_to(w['key_cell'][1])
    check('KEYS: reached the lamp chest room', ok, 'cell %d' % cell(c))
    open_chest(c)
    check('KEYS: the chest grants the lamp', pl(c, ITEMS) & 4, 'items 0x%02x' % pl(c, ITEMS))
    gc, gs = w['gate_cell'][1], w['gate_side'][1]
    ok = go_to(gc)
    check('WEB: reached the web', ok, 'cell %d' % cell(c))
    # select the lamp with L (bombs -> lamp)
    for _ in range(6):
        if pl(c, 9) == 2:
            break
        P.press(c, 'L', 2, 4)
    face_gate(c, gs)
    P.press(c, 'B', 2, 30)
    P.snap(c, os.path.join(S, 'cp3.png'))
    new, before = cross(c, gs)
    check('WEB: the lamp burned it', new == ny_of(gc, gs), 'cell %d -> %d' % (before, new))
    # 4. cloak
    ok = go_to(w['key_cell'][2])
    check('KEYS: reached the cloak chest room', ok, 'cell %d' % cell(c))
    open_chest(c)
    check('KEYS: the chest grants the cloak', pl(c, ITEMS) & 8, 'items 0x%02x' % pl(c, ITEMS))
    gc, gs = w['gate_cell'][2], w['gate_side'][2]
    ok = go_to(gc)
    check('CHASM: reached the chasm', ok, 'cell %d' % cell(c))
    for _ in range(6):
        if pl(c, 9) == 3:
            break
        P.press(c, 'L', 2, 4)
    x, y, key = door_inside(gs)
    teleport(c, x, y)
    P.hold(c, key, 10)
    c.set_keys(P.key(c, key))
    P.press(c, 'B', 2, 0)
    for _ in range(60):
        c.run_frame()
    c.clear_keys(P.key(c, key))
    for _ in range(60):
        c.run_frame()
    P.snap(c, os.path.join(S, 'cp4.png'))
    check('CHASM: the cloak crossed it', cell(c) == ny_of(gc, gs), 'cell %d (hp %d)' % (cell(c), pl(c, 0, True)))
    ok = go_to(w['goal'])
    check('GOAL: the goal room is entered', ok, 'cell %d' % cell(c))
    P.snap(c, os.path.join(S, 'cp5.png'))
    if '--boss' in sys.argv:
        boss_fight(c)
    print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
    return 0 if all(res) else 1


def find_actor(c, kind, typ=None):
    for i in range(1, 96):
        a = P.actor(c, i)
        if a['kind'] == kind and (typ is None or a['type'] == typ):
            return a
    return None


def boss_fight(c):
    """Swing at the Heart until it dies, take the Grail, reach the win."""
    boss = find_actor(c, 2, 5)
    check('BOSS: the Heart is in the goal room', boss is not None, str(boss))
    swings = 0
    for step in range(400):
        heal(c)
        boss = find_actor(c, 2, 5)
        if boss is None:
            break
        px, py = P.player_pos(c)
        dx, dy = boss['x'] - px, boss['y'] + 8 - py
        keys = []
        if abs(dx) > 12: keys.append('RIGHT' if dx > 0 else 'LEFT')
        if abs(dy) > 10: keys.append('DOWN' if dy > 0 else 'UP')
        if keys:
            P.hold(c, keys, 6)
        if abs(dx) < 30 and abs(dy) < 30:
            P.press(c, 'A', 2, 14)
            swings += 1
        if step == 60:
            P.snap(c, os.path.join(S, 'cp6.png'))
    check('BOSS: the Heart dies to the sword', find_actor(c, 2, 5) is None, 'swings %d hp left %s' % (swings, find_actor(c, 2, 5)))
    P.run(c, 140)
    grail = find_actor(c, 4, 6)
    check('BOSS: the Grail drops', grail is not None or gstate(c) == 6, str(grail))
    if grail:
        teleport(c, grail['x'], grail['y'] + 2)
        P.run(c, 10)
    P.run(c, 200)
    st = gstate(c)
    check('WIN: the Grail ends the run', st == 6, 'state %d' % st)
    P.snap(c, os.path.join(S, 'cp7.png'))


if __name__ == '__main__':
    sys.exit(main())
