"""The single-room carry quest, played (docs/QUICKSTART_CARRY_SINGLE_ROOM.md).

For every pair in include/quickstart/carry_pairs.h, a QUEST/CARRY scenario
forces the room and the pair (scenario_c = its index in the room + 1), and
the probe plays it with key presses:

  GIVER     a giver stands at A and a receiver at B.
  ACCEPT    talking to the giver (R, from below) accepts: state ACCEPTED,
            the parcel pot on its home tile, three tiles from the giver.
  LIFT      walking into the pot and pressing R lifts it; the state goes
            LIFTED and the first wave is out (enemies counted, by role).
  CARRY     Link walks the carry path to B with the pot overhead - a path
            re-planned from wherever he is, on the same carry grid the pairs
            were made from - lifting it again if it leaves his hands. His
            invulnerability frames are held up for the walk, so the waves'
            hits do not knock it loose: this proves the PATH (a knocked-loose
            parcel and its re-lift were measured separately, 1 to 6 re-lifts
            per pair with the waves free to hit). The second wave comes past
            half-way.
  DELIVER   at B the quest closes (WON) and a reward lies at the receiver's
            feet; no parcel is left in the room.

Then, once per room kind it applies to:

  LOST-HAZARD  the parcel thrown onto a hazard tile (Castor Wilds' swamp)
               comes back to the tile it was lifted from.
  LOST-DRY     thrown onto open ground outside the carry grid's piece (a
               ledge top or a pocket), it comes back the same way.
  KEPT         thrown onto good ground, it stays where it landed.

    python3 tools/quickstart/carry_room_probe.py [--rom tmc-d3.gba] [--only NHF] [--out DIR]
    python3 tools/quickstart/carry_room_probe.py --throws    # the three throws
"""
import os, re, sys
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import (entities, here, warp, press, r16, w16, snap, room_dims, coll_at, act_at,
                 KIND_OBJECT, KIND_ENEMY, KIND_NPC, PLAYER, ROOM_CONTROLS, GENT, STRIDE)
import scenario as S
import parse_tables as P
import callrom as C

args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else 'tmc-d3.gba'
OUT = args[args.index('--out') + 1] if '--out' in args else '/tmp'
ONLY = args[args.index('--only') + 1] if '--only' in args else None
SAVE = 0x02002a40
FLAGS = SAVE + 0x25C
BANK11 = 0x9C0
MSG = 0x02000050
PSTATE = 0x03003f80
HELD = PSTATE + 5
POT = P._enum(open(os.path.join(P.ROOT, 'include/object.h')).read())['POT']
ENEMY = {m.group(2): int(m.group(1), 16) for m in
         re.finditer(r'/\*0x([0-9a-f]+)\*/ (\w+),', open(os.path.join(P.ROOT, 'include/enemy.h')).read())}
PARCEL = 0x50
HAZ = (0x0D, 0x10, 0x11, 0x13, 0x5A)
SHOOTERS = {ENEMY['OCTOROK'], ENEMY['BOW_MOBLIN'], ENEMY['WIZZROBE_WIND']}
IMPAIRERS = {ENEMY['WISP'], ENEMY['FLYING_SKULL'], ENEMY['BEETLE'], ENEMY['WIZZROBE_ICE'], ENEMY['WIZZROBE_FIRE']}
res = []


def check(name, ok, detail=''):
    res.append(bool(ok)); print('%s %-40s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)


def b11(c, bit):
    b = BANK11 + bit
    return (c.memory.u8[FLAGS + (b >> 3)] >> (b & 7)) & 1


def state(c):
    return b11(c, 166) | (b11(c, 167) << 1)


GUARD = [False]


def run(c, n):
    for _ in range(n):
        c.memory.u8[PLAYER + 0x45] = 24   # health pinned: the waves are real
        if GUARD[0]:
            # invulnerability frames held up (entity +0x3d, what the draw
            # routine blinks on): no hit lands, so no hit knocks the pot
            # loose - the walk tests the PATH, the waves are counted apart
            c.memory.u8[PLAYER + 0x3d] = 30
        c.run_frame()


def dismiss(c, limit=900):
    quiet = 0
    for _ in range(limit):
        if c.memory.u8[MSG] == 0:
            run(c, 1); quiet += 1
            if quiet >= 30:
                return
            continue
        press(c, c.KEY_A, 3, 17); quiet = 0


def origin(c):
    return r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)


def ltile(c):
    ox, oy = origin(c)
    return (r16(c, PLAYER + 0x2e) - ox) >> 4, (r16(c, PLAYER + 0x32) - oy) >> 4


def pairs():
    out = []
    for m in re.finditer(r'\{ (AREA_\w+), (ROOM_\w+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), sQuickStartCarryPiece\d+ \}, // ([\w-]+)',
                         open(os.path.join(P.ROOT, 'include/quickstart/carry_pairs.h')).read()):
        out.append(dict(area=m.group(1), room=m.group(2), a=(int(m.group(3)), int(m.group(4))),
                        h=(int(m.group(5)), int(m.group(6))), b=(int(m.group(7)), int(m.group(8))),
                        length=int(m.group(9)), label=m.group(10)))
    return out


def carry_grid(c):
    w, h = room_dims(c)
    tw, th = min(w // 16, 64), min(h // 16, 64)
    return tw, th, [[coll_at(c, x, y) == 0 and act_at(c, x, y) not in HAZ for x in range(tw)] for y in range(th)]


def piece(tw, th, g, seed):
    seen = {seed}; q = deque([seed])
    while q:
        a, b = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            t = (a + dx, b + dy)
            if 0 <= t[0] < tw and 0 <= t[1] < th and g[t[1]][t[0]] and t not in seen:
                seen.add(t); q.append(t)
    return seen


def path(inside, src, dst):
    par = {src: None}; q = deque([src])
    while q:
        t = q.popleft()
        if t == dst:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            u = (t[0] + dx, t[1] + dy)
            if u in inside and u not in par:
                par[u] = t; q.append(u)
    if dst not in par:
        return None
    out = []
    t = dst
    while t is not None:
        out.append(t); t = par[t]
    return out[::-1]


def step_toward(c, tx, ty, frames=4):
    """Hold the direction toward a tile centre for a few frames - one axis
    at a time, the longer first (a diagonal snags on corners). TRUE when
    already there."""
    ox, oy = origin(c)
    dx = tx * 16 + 8 - (r16(c, PLAYER + 0x2e) - ox)
    dy = ty * 16 + 8 - (r16(c, PLAYER + 0x32) - oy)
    if abs(dx) <= 2 and abs(dy) <= 2:
        return True
    if abs(dx) > 2 and (abs(dx) >= abs(dy) or abs(dy) <= 2):
        key = c.KEY_RIGHT if dx > 0 else c.KEY_LEFT
    else:
        key = c.KEY_DOWN if dy > 0 else c.KEY_UP
    c.set_keys(key)
    run(c, frames)
    c.clear_keys(key)
    return False


def walk_to(c, inside, goal, limit=3000, on_frame=None):
    """Walk to a tile on the carry grid, re-planning from wherever Link is."""
    frames = 0
    stuck = 0
    last = None
    while frames < limit:
        here_t = ltile(c)
        if here_t == goal:
            for _ in range(20):
                if step_toward(c, goal[0], goal[1], 2):
                    break
            return True
        start = here_t if here_t in inside else min(inside, key=lambda t: abs(t[0] - here_t[0]) + abs(t[1] - here_t[1]))
        p = path(inside, start, goal)
        if p is None:
            return False
        # the very next tile: aiming two ahead cuts the corner of a
        # staircase-shaped path (one axis at a time, into the wall)
        nxt = p[min(1, len(p) - 1)] if here_t in inside else start
        step_toward(c, nxt[0], nxt[1], 4)
        frames += 4
        if on_frame:
            on_frame()
        pos = (r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32))
        stuck = stuck + 1 if pos == last else 0
        last = pos
        if stuck > 12:   # pinned on a corner: a nudge sideways
            step_toward(c, here_t[0] + (1 if (frames // 48) % 2 else -1), here_t[1], 6)
            stuck = 0
    return False


def parcel(c):
    for e in entities(c, KIND_OBJECT, POT):
        if c.memory.u8[GENT + e[0] * STRIDE + 0xb] == PARCEL:
            return e
    return None


def face_and_lift(c, inside, target):
    """Stand on a carry tile beside `target` (a tile), face it, press R."""
    beside = [(target[0] + dx, target[1] + dy) for dx, dy in ((0, 1), (-1, 0), (1, 0), (0, -1))]
    beside = [t for t in beside if t in inside]
    if not beside:
        return False
    me = ltile(c)
    spot = min(beside, key=lambda t: abs(t[0] - me[0]) + abs(t[1] - me[1]))
    walk_to(c, inside, spot, limit=1500)
    key = {(0, 1): c.KEY_UP, (-1, 0): c.KEY_RIGHT, (1, 0): c.KEY_LEFT, (0, -1): c.KEY_DOWN}[(spot[0] - target[0], spot[1] - target[1])]
    c.set_keys(key)
    last, still = None, 0
    for _ in range(30):
        run(c, 1)
        pos = (r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32))
        still = still + 1 if pos == last else 0
        last = pos
        if still >= 2:
            break
    c.clear_keys(key)
    press(c, c.KEY_R, 3, 30)
    return c.memory.u8[HELD] != 0


def enemies_by_role(c):
    ids = [e[2] for e in entities(c, KIND_ENEMY)]
    return dict(total=len(ids), shooters=sum(1 for i in ids if i in SHOOTERS), impairers=sum(1 for i in ids if i in IMPAIRERS))


def settle(c, area, room, x, y):
    """Warp in and wait until the room is really there: in it, Link
    standing normally near the target, for a while. A stray START from the
    scenario boot can leave the pause menu open - and with it open the room
    reads (0, 0), which IS Minish Woods (measured) - so the position is the
    test, and START closes a menu that is in the way."""
    for attempt in range(4):
        warp(c, area, room, x, y, frames=240); dismiss(c)
        ok = 0
        for _ in range(300):
            run(c, 1)
            ox, oy = origin(c)
            near = abs(r16(c, PLAYER + 0x2e) - ox - x) < 48 and abs(r16(c, PLAYER + 0x32) - oy - y) < 48
            ok = ok + 1 if (here(c) == (area, room) and c.memory.u8[PLAYER + 0xc] == 1 and near) else 0
            if ok >= 60:
                return True
        press(c, c.KEY_START, 3, 30)
    return False


def play(p, idx_in_room, row):
    GUARD[0] = False
    print('== %s pair %d: A %s -> B %s (%d tiles)' % (p['label'], idx_in_room, p['a'], p['b'], p['length']), flush=True)
    c = S.boot(ROM, S.KINDS['QUEST'], S.QUESTS.index('CARRY'), row, idx_in_room + 1, frames=300)
    c.memory.u8[SAVE + 0x3C] = 0x51
    dismiss(c)
    area, room = P.AREAS[p['area']], P.ROOMS[p['room']]
    ax, ay = p['a']; bx, by = p['b']
    settle(c, area, room, ax * 16 + 8, ay * 16 + 24)
    tw, th, g = carry_grid(c)
    inside = piece(tw, th, g, (bx, by))
    ox, oy = origin(c)
    npcs = [(e[4] - ox >> 4, e[5] - oy >> 4) for e in entities(c, KIND_NPC)]
    check('GIVER: giver at A, receiver at B', here(c) == (area, room) and (ax, ay) in npcs and (bx, by) in npcs,
          'room %s npcs %s' % (here(c), npcs[:6]))
    # talk to the giver from below
    walk_to(c, inside, (ax, ay + 1), limit=600)
    press(c, c.KEY_UP, 2, 2); press(c, c.KEY_R, 3, 10); dismiss(c); run(c, 30)
    pc = parcel(c)
    check('ACCEPT: talked, parcel beside the giver', state(c) == 1 and pc is not None and
          ((pc[4] - ox) >> 4, (pc[5] - 3 - oy) >> 4) == p['h'], 'state %d parcel %s' % (state(c), pc and ((pc[4] - ox) >> 4, (pc[5] - oy) >> 4)))
    if pc is None:
        return c, inside
    e0 = enemies_by_role(c)
    ok = face_and_lift(c, inside, p['h'])
    run(c, 30)
    e1 = enemies_by_role(c)
    check('LIFT: lifted, LIFTED, first wave out', ok and state(c) == 2 and e1['total'] > e0['total'],
          'held %d state %d enemies %d -> %d (shooters %d, impairers %d)' % (c.memory.u8[HELD], state(c), e0['total'], e1['total'], e1['shooters'], e1['impairers']))
    snap(c, os.path.join(OUT, 'carry_%s_%d_lift.png' % (p['label'], idx_in_room)))
    # carry to B, re-lifting when knocked
    GUARD[0] = True
    relifts, wave2 = 0, False
    goal_near = [(bx + dx, by + dy) for dx, dy in ((0, 1), (-1, 0), (1, 0), (0, -1), (0, 2))]
    goal = next((t for t in goal_near if t in inside), (bx, by + 1))
    for attempt in range(12):
        if state(c) == 3:
            break
        if c.memory.u8[HELD] == 0:
            pc = parcel(c)
            if pc is None:
                run(c, 30)
                continue
            if face_and_lift(c, inside, ((pc[4] - ox) >> 4, (pc[5] - 3 - oy) >> 4)):
                relifts += 1
        walk_to(c, inside, goal, limit=1200, on_frame=None)
        run(c, 10)
        wave2 = wave2 or b11(c, 168) == 1
    GUARD[0] = False
    e2 = enemies_by_role(c)
    rewards = [e for e in entities(c, KIND_OBJECT, 0)]
    check('CARRY: second wave past half-way', b11(c, 168) == 1, 'wave2 %d, re-lifts %d, enemies now %d' % (b11(c, 168), relifts, e2['total']))
    check('DELIVER: WON, reward at B, no parcel left', state(c) == 3 and parcel(c) is None and len(rewards) > 0,
          'state %d parcel %s ground items %d at %s' % (state(c), parcel(c), len(rewards), ltile(c)))
    snap(c, os.path.join(OUT, 'carry_%s_%d_done.png' % (p['label'], idx_in_room)))
    return c, inside


DIRS = {(1, 0): 'RIGHT', (-1, 0): 'LEFT', (0, 1): 'DOWN', (0, -1): 'UP'}


def throw_from(c, inside, stand, d):
    """Carrying, walk to `stand`, face `d`, throw. Returns (last tile of the
    thrown pot, the parcel's tile after) - tiles, or None."""
    for _ in range(4):   # knocked out of his hands on the way: lift it again
        walk_to(c, inside, stand, limit=1500)
        if c.memory.u8[HELD] != 0 and ltile(c) == stand:
            break
        if c.memory.u8[HELD] == 0:
            pc = parcel(c)
            ox, oy = origin(c)
            if pc:
                face_and_lift(c, inside, ((pc[4] - ox) >> 4, (pc[5] - 3 - oy) >> 4))
    for _ in range(120):   # the lift finished (heldObject 3 is mid-lift; R then drops it)
        if c.memory.u8[HELD] == 4:
            break
        run(c, 1)
    key = getattr(c, 'KEY_' + DIRS[d])
    press(c, key, 1, 2)
    ox, oy = origin(c)
    old = parcel(c)
    print('  throwing from %s (wanted %s), held %d, parcel %s' % (ltile(c), stand, c.memory.u8[HELD], old and ((old[4] - ox) >> 4, (old[5] - oy) >> 4)), flush=True)
    press(c, c.KEY_R, 3, 1)
    last = None
    for _ in range(120):
        run(c, 1)
        e = c.memory.u8[GENT + old[0] * STRIDE + 8], c.memory.u8[GENT + old[0] * STRIDE + 9]
        if e != (6, POT):
            break
        last = ((r16(c, GENT + old[0] * STRIDE + 0x2e) - ox) >> 4, (r16(c, GENT + old[0] * STRIDE + 0x32) - oy) >> 4)
    run(c, 10)
    now = parcel(c)
    return last, (now and ((now[4] - ox) >> 4, (now[5] - 3 - oy) >> 4))


DONE = []


def simulate_dry(c, inside, tw, th, g, lifted_at):
    """No room offers a throw onto unreachable dry ground: a thrown pot is
    stopped by cliff faces, and no pit or channel beside a carry piece has
    dry ground just beyond it (searched in every room). The rule is still
    checked, on the game's own code: the held parcel is placed on open
    ground outside the piece and handed to QuickStartParcelLanded with no
    hazard - exactly what pot.c does when a flight ends there."""
    for _ in range(120):
        if c.memory.u8[HELD] == 4:
            break
        run(c, 1)
    pc = parcel(c)
    ox, oy = origin(c)
    me = ltile(c)
    away = min(((x, y) for y in range(th) for x in range(tw) if g[y][x] and (x, y) not in inside),
               key=lambda t: abs(t[0] - me[0]) + abs(t[1] - me[1]))
    b = GENT + pc[0] * STRIDE
    w16(c, b + 0x2e, ox + away[0] * 16 + 8); w16(c, b + 0x32, oy + away[1] * 16 + 8)
    lost = C.call_keep(c, C.map_sym('QuickStartParcelLanded'), (b, 0))
    fresh = [e for e in entities(c, KIND_OBJECT, POT) if c.memory.u8[GENT + e[0] * STRIDE + 0xb] == PARCEL and e[0] != pc[0]]
    fresh_t = fresh and ((fresh[0][4] - ox) >> 4, (fresh[0][5] - oy) >> 4)
    DONE.append(('LOST-DRY', fresh_t == lifted_at))
    check('LOST-DRY (rule, on a held parcel): comes back', lost == 1 and fresh_t == lifted_at and b11(c, 169) == 1,
          'placed on %s (dry, outside the piece): replacement at %s, lifted at %s, Ezlo said %d' % (away, fresh_t, lifted_at, b11(c, 169)))


def throw_tests():
    rows = {r['roomName']: i for i, r in enumerate(S.pool())}
    labels = sorted({q['label'] for q in pairs()})
    for label, want in [('CW', 'hazard'), ('NHF', 'kept')] + [(l, 'dry') for l in labels]:
        if want == 'dry' and any(r and n.startswith('LOST-DRY') for n, r in DONE):
            break
        p = [q for q in pairs() if q['label'] == label][0]
        print('== throws in %s (%s)' % (label, want), flush=True)
        c = S.boot(ROM, S.KINDS['QUEST'], S.QUESTS.index('CARRY'), rows[p['room']], 1, frames=300)
        c.memory.u8[SAVE + 0x3C] = 0x51
        dismiss(c)
        area, room = P.AREAS[p['area']], P.ROOMS[p['room']]
        ax, ay = p['a']
        settle(c, area, room, ax * 16 + 8, ay * 16 + 24)
        tw, th, g = carry_grid(c)
        inside = piece(tw, th, g, p['b'])
        GUARD[0] = False
        # a stand tile in the piece and a direction whose tiles 2..4 ahead
        # are what the test wants
        def ahead(t, d, k):
            return (t[0] + d[0] * k, t[1] + d[1] * k)
        found = None
        me = (ax, ay + 1)
        for t in sorted(inside, key=lambda t: abs(t[0] - me[0]) + abs(t[1] - me[1])):
            for d in DIRS:
                tiles = [ahead(t, d, k) for k in (1, 2, 3, 4)]
                if not all(0 <= x < tw and 0 <= y < th for x, y in tiles):
                    continue
                acts = [act_at(c, x, y) for x, y in tiles]
                if want == 'hazard' and tiles[0] in inside and all(a == 0x13 for a in acts[1:]):
                    found = (t, d)
                elif want == 'kept' and all(x in inside for x in tiles) and ahead(t, d, -1) in inside:
                    found = (t, d)
                elif (want == 'dry' and acts[0] in (0x0D, 0x10, 0x11) and
                      (acts[1] in (0x0D, 0x10, 0x11) or g[tiles[1][1]][tiles[1][0]]) and
                      all(g[y][x] and (x, y) not in inside for x, y in tiles[2:])):
                    # over a pit or a water channel - which a thrown pot
                    # flies over, where a cliff face stops it - onto dry
                    # ground in another piece
                    found = (t, d)
                if found:
                    break
            if found:
                break
        simulate = False
        if not found:
            if want == 'dry':
                print('  no pit or channel with dry ground beyond in %s' % label)
                if label != labels[-1] or any(n.startswith('LOST-DRY') for n, r in DONE):
                    continue
                simulate = True
            else:
                check('THROW %s: a spot to throw %s' % (label, want), False, 'none in the piece')
                continue
        walk_to(c, inside, (ax, ay + 1), limit=600)
        press(c, c.KEY_UP, 2, 2); press(c, c.KEY_R, 3, 10); dismiss(c); run(c, 30)
        if not face_and_lift(c, inside, p['h']):
            check('THROW %s: lifted' % label, False, 'could not lift')
            continue
        lifted_at = p['h']
        # the throws are about the parcel, not the fight - and only now:
        # held-up invulnerability frames stop the lift itself (measured)
        GUARD[0] = True
        if simulate:
            simulate_dry(c, inside, tw, th, g, lifted_at)
            continue
        (stand, d) = found
        landed, now = throw_from(c, inside, stand, d)
        said = b11(c, 169)
        if want == 'kept':
            check('KEPT: thrown onto good ground, it stays', now is not None and now != lifted_at and now in inside and
                  abs(now[0] - stand[0]) + abs(now[1] - stand[1]) >= 2,
                  'from %s %s: landed %s, parcel now %s (lifted at %s)' % (stand, DIRS[d], landed, now, lifted_at))
        else:
            DONE.append(('LOST-%s' % want.upper(), now == lifted_at))
            check('LOST-%s: it comes back where it was lifted' % want.upper(), now == lifted_at and (said == 1 or want == 'dry'),
                  'from %s %s: last seen %s (act %s), parcel now %s, lifted at %s, Ezlo said %d' %
                  (stand, DIRS[d], landed, landed and hex(act_at(c, *landed)), now, lifted_at, said))
        snap(c, os.path.join(OUT, 'carry_throw_%s.png' % want))


def main():
    rows = {r['roomName']: i for i, r in enumerate(S.pool())}
    all_pairs = pairs()
    seen = {}
    if '--throws' in args:
        throw_tests()
        print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
        sys.exit(0 if all(res) else 1)
    for p in all_pairs:
        k = seen.get(p['room'], 0)
        seen[p['room']] = k + 1
        if ONLY and p['label'] != ONLY:
            continue
        play(p, k, rows[p['room']])
    print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
    sys.exit(0 if all(res) else 1)


if __name__ == '__main__':
    main()
