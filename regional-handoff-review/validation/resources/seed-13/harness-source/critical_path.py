"""Walk the maze's critical path in the real ROM: every key gate opened
with its key item, in order, until the goal room.

  TRIALS   three earned mystery rewards grant the barrier-opening items
  CRACK    a bomb beside the cracked wall opens it
  WEB      the lamp burns the web
  CHASM    the cloak leaps the chasm
  GOAL     the goal room is entered

Rooms are crossed by teleporting the hero next to the door and walking
through it (the probe tests gates, not room interiors).

    python3 tools/critical_path.py [--seed N] [--boss]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import probe as P  # noqa: E402

S = os.environ.get('SNAPDIR', '/tmp')
GATE = {0: 'WALL', 1: 'open', 2: 'thorn', 3: 'CRACK', 4: 'WEB', 5: 'LOCK', 6: 'CHASM', 7: 'exit'}
W_ROOM, H_ROOM = 32, 24
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


def area(c):
    return P.r8(c, P.sym("gGame") + 1)


def gstate(c):
    return P.r8(c, P.sym('gGame'))


def teleport(c, x, y):
    """put the hero at (x, y) standing, and make it his safe ground, so a
    fall in progress does not snap him back to where he was"""
    a = P.sym('gActors')
    pl = P.sym('gPl')
    P.w16(c, a + 8, 0); P.w16(c, a + 10, x)
    P.w16(c, a + 12, 0); P.w16(c, a + 14, y)
    P.w8(c, a + 2, 0)   # state: normal
    P.w16(c, pl + 14, x); P.w16(c, pl + 16, y)
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
    """Close item-get and text boxes: A presses until the box is gone and
    play resumes (a box can be open while the hero's state reads normal)."""
    tb = P.sym('gTbActive')
    for _ in range(frames // 8):
        if not P.r8(c, tb) and P.actor(c, 0)['state'] == 0:
            break
        P.press(c, 'A', 2, 6)
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
    clear_enemies(c)
    teleport(c, x, y)
    before = cell(c)
    walk_until_new_room(c, key, frames)
    if P.r8(c, P.sym('gTbActive')):
        # walked into a chest or a sign on arrival, or a box opened on the
        # way: close it, and walk again if the room did not change
        dismiss(c)
        if cell(c) == before:
            teleport(c, x, y)
            walk_until_new_room(c, key, frames)
            if P.r8(c, P.sym('gTbActive')):
                dismiss(c)
    return cell(c), before


def wait_play(c, expected_area=1, frames=600):
    """Room generation can span video frames. Inspect only a settled room."""
    for _ in range(frames):
        if gstate(c)==1 and area(c)==expected_area:
            return True
        c.run_frame()
    return False


def walk_until_new_room(c, key, frames):
    """hold the key until the room changes (or frames run out), then let
    the transition finish with nothing held: the hero stays at the door
    instead of walking on into whatever the new room has there"""
    start = cell(c)
    k = P.key(c, key)
    c.set_keys(k)
    for _ in range(frames):
        c.run_frame()
        if cell(c) != start:
            break
    c.clear_keys(k)
    wait_play(c,1)


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


def enter_trial(c):
    """Walk into this forest cell's actual generated mystery mouth."""
    import myst_probe as M
    mouths = M.tiles_of(c, lambda m: m['type'] == 'MYST')
    if not mouths:
        return False
    tx,ty=mouths[0]
    heal(c); clear_enemies(c)
    teleport(c,tx*16+8,(ty+1)*16+14)
    for _ in range(40):
        P.hold(c,'UP',2)
        if area(c)==2:
            break
    return wait_play(c,2)


def trial_attack_position(c, enemy, turn):
    """Choose a safe sword approach using the current actor/room geometry.

    Positioning is a fixture, as it is for crossing the maze. Facing and
    damage still use real controls. In particular, never place Bloom in a
    monster's contact box or on the trial's retreat doorway: knockback at
    that doorway can leave the event before it has been completed.
    """
    R=P.sym('gRoom'); types=P.sym('metatile_type')
    w,h,g=room_tiles(c)
    hitboxes=P.sym('gHitboxes'); actors=P.sym('gActors')

    def body_box(index, x, y):
        hb=P.r8(c,actors+index*64+34)
        values=[P.r8(c,hitboxes+hb*4+i) for i in range(4)]
        ox,oy,hw,hh=[v-256 if v>=128 else v for v in values]
        return (x+ox-hw,y+oy-hh,x+ox+hw-1,y+oy+hh-1)

    bodies=[]
    for i in range(1,96):
        a=P.actor(c,i)
        if a['kind']==2:
            bodies.append(body_box(i,a['x'],a['y']-a['z']))

    # Horizontal flanks give the small avatar clearance from contact
    # damage. The north-facing fallback also keeps the head below the
    # target, with the live distal blade reaching its contact box.
    candidates=[(enemy['x']-24,enemy['y']+6,'RIGHT'),
                (enemy['x']+24,enemy['y']+6,'LEFT'),
                (enemy['x']-5,enemy['y']+30,'UP')]
    for x,y,key in candidates[turn%3:]+candidates[:turn%3]:
        # Include the next directional-input step around the 10x8 feet.
        safe=True
        for px in (x-7,x+6):
            for py in (y-10,y+1):
                if not (0<=px<w*16 and 0<=py<h*16):
                    safe=False; continue
                tile=g[(px//16,py//16)]
                if P.r8(c,R+4098+(py//8)*64+px//8) or tile==0xffff or P.r8(c,types+tile) not in (0,15,20,25):
                    safe=False
        if not safe:
            continue
        hx0,hy0,hx1,hy1=body_box(0,x,y)
        # A four-pixel margin also covers AI movement during positioning
        # and the one-frame directional tap that establishes facing.
        if any(not (hx1+4<ex0 or ex1+4<hx0 or hy1+4<ey0 or ey1+4<hy0)
               for ex0,ey0,ex1,ey1 in bodies):
            continue
        return x,y,key
    return None


def earn_trial(c, claim=True):
    """Solve an actual required event and claim its chest. Combat drives
    sword hits through the game, with healing/debug positioning to isolate
    event completion; enemy HP and the reward flags are never written."""
    import myst_probe as M
    if not enter_trial(c):
        return False
    W=P.sym('gWorld'); here=cell(c)
    packed=P.r8(c,W+M.MYST_OFF+here)
    kind=M.KINDS[packed&15]
    if not (P.r8(c,W+M.FLAGS_OFF+here)&4):
        if M.tiles_of(c,lambda m:m['type']=='CHEST'):
            return False  # a required gift cannot be a free chest
        if kind=='switches':
            for tx,ty in M.tiles_of(c,lambda m:m['name']=='myst_switch',1):
                heal(c); teleport(c,tx*16+8,ty*16+12); P.run(c,8)
        elif kind in ('waves','miniboss'):
            for turn in range(240):
                heal(c)
                if area(c)!=2 or cell(c)!=here:
                    return False  # do not mistake a forest fight for the trial
                if M.tiles_of(c,lambda m:m['type']=='CHEST'):
                    break
                # Let actual knockback/attack recovery finish before the
                # next positioning fixture, rather than resetting state
                # while a pending knockback can still move the avatar.
                if P.actor(c,0)['state']!=0 or P.r8(c,P.sym('gActors')+29):
                    P.run(c,16)
                    continue
                enemy=find_actor(c,2)
                if enemy:
                    approach=trial_attack_position(c,enemy,turn)
                    if approach is None:
                        P.run(c,16)
                        continue
                    x,y,key=approach
                    teleport(c,x,y)
                    P.hold(c,key,1)
                    P.press(c,'B',2,16)
                else:
                    P.run(c,60)
        else:
            return False  # deliberately no item-dependent trial in this pool
    won=area(c)==2 and cell(c)==here and bool(P.r8(c,W+M.FLAGS_OFF+here)&4)
    if not won or not claim:
        return won
    if not M.open_chest(c):
        return False
    dismiss(c)
    return M.leave(c)==1


def pl(c, off, w=False):
    s = P.sym('gPl')
    return P.r16(c, s + off) if w else P.r8(c, s + off)


ITEMS, BOMBS, KEYS = 8, 7, 6
EQ_NONE, EQ_SWORD, EQ_BOMBS, EQ_LAMP, EQ_CLOAK, EQ_SHIELD = range(6)


def equip_b(c, eq):
    """put an item on A through gPl.equip (A, B, L at 9, 10, 11), clearing
    any other button that held it. The sword starts on B and the shield
    on L, so A is the probes' item button (the name is historical)."""
    s = P.sym('gPl')
    for slot in range(3):
        if P.r8(c, s + 9 + slot) == eq:
            P.w8(c, s + 9 + slot, 0)
    P.w8(c, s + 9, eq)


def main():
    seed = int(sys.argv[sys.argv.index('--seed') + 1], 0) if '--seed' in sys.argv else 0xB4A7
    c = P.boot(seed=seed)
    P.run(c, 40)
    print('seed', hex(seed))
    w = world(c)
    print('entry', w['entry'], 'goal', w['goal'], 'path', w['path'])
    print('gates', [(w['gate_cell'][i], w['gate_side'][i], GATE[w['cells'][w['gate_cell'][i]]['gate'][w['gate_side'][i]]]) for i in range(3)])
    print('keys', w['key_cell'])
    # into the forest
    P.enter_forest(c)
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
            if g == 2:  # thorns: cut them first, no monster at the hero's back
                heal(c)
                clear_enemies(c)
                face_gate(c, s)
                for _ in range(2):
                    P.press(c, 'B', 2, 14)
            elif g == 5 and pl(c, KEYS) == 0:
                print('   route needs a key at', frm, s)
            new, before = cross(c, s)
            print('   cross %d side %d: %d -> %d pos %s hp %d' % (frm, s, before, new, P.player_pos(c), pl(c, 0, True)), flush=True)
            if new == before:
                # maybe a thorn remained; try once more
                face_gate(c, s)
                P.press(c, 'B', 2, 14)
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
    check('TRIAL: reached the seed trial room', ok, 'cell %d' % cell(c))
    check('TRIAL: its event is completed and claimed', earn_trial(c))
    check('KEYS: the earned chest grants the bombs', pl(c, ITEMS) & 2, 'items 0x%02x bombs %d' % (pl(c, ITEMS), pl(c, BOMBS)))
    P.snap(c, os.path.join(S, 'cp1.png'))
    # 2. the crack: go to the gate cell, bomb it
    gc, gs = w['gate_cell'][0], w['gate_side'][0]
    ok = go_to(gc)
    check('CRACK: reached the cracked wall', ok, 'cell %d' % cell(c))
    equip_b(c, EQ_BOMBS)
    face_gate(c, gs)
    P.press(c, 'A', 2, 4)
    x, y, key = door_inside(gs)
    P.hold(c, {'UP': 'DOWN', 'DOWN': 'UP', 'LEFT': 'RIGHT', 'RIGHT': 'LEFT'}[key], 30)
    P.run(c, 170)
    P.snap(c, os.path.join(S, 'cp2.png'))
    new, before = cross(c, gs)
    check('CRACK: the bomb opened it', new == ny_of(gc, gs), 'cell %d -> %d' % (before, new))
    # 3. lamp
    ok = go_to(w['key_cell'][1])
    check('TRIAL: reached the candle trial room', ok, 'cell %d' % cell(c))
    check('TRIAL: its event is completed and claimed', earn_trial(c))
    check('KEYS: the earned chest grants the lamp', pl(c, ITEMS) & 4, 'items 0x%02x' % pl(c, ITEMS))
    gc, gs = w['gate_cell'][1], w['gate_side'][1]
    ok = go_to(gc)
    check('WEB: reached the web', ok, 'cell %d' % cell(c))
    equip_b(c, EQ_LAMP)
    face_gate(c, gs)
    P.press(c, 'A', 2, 30)
    P.snap(c, os.path.join(S, 'cp3.png'))
    new, before = cross(c, gs)
    check('WEB: the lamp burned it', new == ny_of(gc, gs), 'cell %d -> %d' % (before, new))
    # 4. cloak
    ok = go_to(w['key_cell'][2])
    check('TRIAL: reached the cape trial room', ok, 'cell %d' % cell(c))
    check('TRIAL: its event is completed and claimed', earn_trial(c))
    check('KEYS: the earned chest grants the cloak', pl(c, ITEMS) & 8, 'items 0x%02x' % pl(c, ITEMS))
    gc, gs = w['gate_cell'][2], w['gate_side'][2]
    ok = go_to(gc)
    check('CHASM: reached the chasm', ok, 'cell %d' % cell(c))
    equip_b(c, EQ_CLOAK)
    x, y, key = door_inside(gs)
    teleport(c, x, y)
    P.hold(c, key, 10)
    c.set_keys(P.key(c, key))
    P.press(c, 'A', 2, 0)
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
            P.press(c, 'B', 2, 14)
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
