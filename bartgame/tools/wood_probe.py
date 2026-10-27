"""The wood's new mechanics, played in the ROM.

  KNIGHT   a sword blow to a knight's front lands
  GATHER   a swing that reaches a heart gathers it
  DEFLECT  a swing turns a spitter's seed back, the hero's now
  CARRY    the load held, a swing drops it and the sword comes out
  BOW      a chest holds the bow; an arrow loosed, a beetle hit;
           the Peddler sells arrows once the bow is owned
  CAP      the Drain Cap, owned and unequipped from the start; used in
           the wood, a mouth takes the hero and he drops from the
           drain's ceiling onto his spawn; used in the drain, only words

    python3 tools/wood_probe.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'art'))
import probe as P  # noqa: E402
import critical_path as CP  # noqa: E402
import lift_probe as LP  # noqa: E402

S = os.environ.get('SNAPDIR', '/tmp')
res = []
PS_NORMAL, PS_ATTACK, PS_JUMP, PS_CARRY, PS_SWALLOWED = 0, 2, 5, 11, 12
AK_ENEMY, AK_PROJ, AK_PICKUP = 2, 3, 4
EN_BEETLE, EN_KNIGHT = 0, 4
EQ_BOW, EQ_HUBCAP = 6, 7
ITEM2_BOW, ITEM2_HUBCAP = 1, 2
ROLE_CHEST, CHEST_BOW = 4, 6
PL_CARRY, PL_ARROWS, PL_ITEMS2 = 33, 35, 36


def check(name, ok, detail=''):
    res.append(bool(ok))
    print('%s %-46s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)


def state(c):
    return P.actor(c, 0)['state']


def free_slot(c):
    for i in range(1, 96):
        if P.actor(c, i)['kind'] == 0:
            return i
    return None


def put_actor(c, i, kind, type_, x, y, hitbox, flags=0, dir_=0, speed=0, damage=0, timer=10):
    """write an actor into a free slot, the fields the game reads"""
    a = P.sym('gActors') + i * 64
    for k in range(64):
        P.w8(c, a + k, 0)
    P.w8(c, a, kind); P.w8(c, a + 1, type_)
    P.w8(c, a + 4, timer); P.w8(c, a + 6, dir_)
    P.w16(c, a + 8, 0); P.w16(c, a + 10, x); P.w16(c, a + 12, 0); P.w16(c, a + 14, y)
    P.w16(c, a + 24, speed)
    P.w8(c, a + 31, flags); P.w8(c, a + 34, hitbox)
    P.w8(c, a + 42, 16); P.w8(c, a + 43, 16)
    P.w8(c, a + 47, damage)


def find_actor(c, kind, type_=None):
    for i in range(1, 96):
        a = P.actor(c, i)
        if a['kind'] == kind and (type_ is None or a['type'] == type_):
            return i, a
    return None, None


def spawn_enemy(c, type_, x, y, facing=None):
    d = P.sym('gDbgSpawn')
    P.w16(c, d, (1 << 8) | type_); P.w16(c, d + 2, 0)
    P.run(c, 2)
    i, a = find_actor(c, AK_ENEMY, type_)
    base = P.sym('gActors') + i * 64
    P.w16(c, base + 8, 0); P.w16(c, base + 10, x); P.w16(c, base + 12, 0); P.w16(c, base + 14, y)
    P.w8(c, base + 28, 0)
    P.w8(c, base + 2, 0); P.w8(c, base + 4, 200)  # idle, a long timer: it stands
    if facing is not None:
        P.w8(c, base + 7, facing); P.w8(c, base + 6, facing * 8)
    return i


def north_shot_position(c):
    """A natural, unobstructed firing lane, independent of forest dressing."""
    room = P.sym('gRoom')
    w, h, grid = CP.room_tiles(c)
    solid = bytes(P.r8(c, room + 4098 + i) for i in range(4096))
    types = P.sym('metatile_type')
    floor = {mt for mt in set(grid.values()) if P.r8(c, types + mt) == 0}
    candidates = []
    for ty in range(6, h - 2):
        for tx in range(2, w - 2):
            x, y = tx * 16 + 8, ty * 16 + 14
            points = [(x + dx, y - up) for dx in (-6, 0, 5) for up in range(0, 73, 4)]
            if all(grid.get((px >> 4, py >> 4)) in floor and not solid[(py >> 3) * 64 + (px >> 3)]
                   for px, py in points):
                candidates.append((abs(x - 256) + abs(y - 230), x, y))
    assert candidates, 'fixture needs a clear natural northbound firing lane'
    return min(candidates)[1:]


def main():
    c = P.boot()
    P.run(c, 40)
    w = CP.world(c)
    pl = P.sym('gPl')
    A = P.sym('gActors')
    # CAP: owned from the start, on no button
    eq = [P.r8(c, pl + 9 + i) for i in range(3)]
    check('CAP: the Drain Cap is in the pack at the start', P.r8(c, pl + PL_ITEMS2) & ITEM2_HUBCAP, 'items2 %d' % P.r8(c, pl + PL_ITEMS2))
    check('CAP: it is on no button', EQ_HUBCAP not in eq, 'equip %s' % eq)
    # BOW: a chest holds it
    bow_cells = [i for i in range(25) if w['cells'][i]['role'] == ROLE_CHEST and w['cells'][i]['arg'] == CHEST_BOW]
    check('BOW: a chest in the wood holds the bow', len(bow_cells) == 1, 'cells %s stage %s' % (bow_cells, [w['cells'][i]['stage'] for i in bow_cells]))
    P.enter_forest(c)
    LP.warp(c, w['entry'], 2)
    CP.heal(c); CP.clear_enemies(c)
    hx, hy = 256, 230
    CP.teleport(c, hx, hy)
    P.hold(c, 'UP', 2)
    # KNIGHT: facing the hero (south), struck from the south. Stand outside
    # body contact so the two-frame sword anticipation can complete; this
    # checks a frontal sword hit, not a bite interrupting the wind-up.
    fx, fy = P.player_pos(c)
    k = spawn_enemy(c, EN_KNIGHT, fx, fy - 28, facing=2)
    hp0 = P.actor(c, k)['hp']
    P.press(c, 'B', 2, 14)
    hp1 = P.actor(c, k)['hp'] if P.actor(c, k)['kind'] == AK_ENEMY else 0
    check('KNIGHT: a blow to its front lands', hp1 < hp0, 'hp %d -> %d' % (hp0, hp1))
    P.snap(c, os.path.join(S, 'wood_knight.png'))
    CP.clear_enemies(c); P.run(c, 20)
    # GATHER: a heart two tiles up, reached by the swing, not by touch
    P.w16(c, pl, 16)
    fx, fy = P.player_pos(c)
    i = free_slot(c)
    put_actor(c, i, AK_PICKUP, 0, fx, fy - 28, 2)
    P.run(c, 8)
    check('GATHER: out of reach, the heart stays', P.r16(c, pl) == 16 and P.actor(c, i)['kind'] == AK_PICKUP, 'hp %d kind %d' % (P.r16(c, pl), P.actor(c, i)['kind']))
    P.press(c, 'B', 2, 14)
    check('GATHER: a swing gathers it', P.r16(c, pl) == 24, 'hp %d' % P.r16(c, pl))
    # DEFLECT: a seed coming down from the north
    P.run(c, 10)
    i = free_slot(c)
    fx, fy = P.player_pos(c)
    put_actor(c, i, AK_PROJ, 0, fx, fy - 30, 6, flags=1, dir_=16, speed=0x100, damage=2, timer=1)
    P.press(c, 'B', 2, 4)
    a = P.actor(c, i)
    v0 = P.r8(c, A + i * 64 + 48)
    check('DEFLECT: the seed is turned north, the hero\'s', a['kind'] == AK_PROJ and v0 == 1 and P.r8(c, A + i * 64 + 6) == 0, 'kind %d v0 %d dir %d' % (a['kind'], v0, P.r8(c, A + i * 64 + 6)))
    y0 = a['y']
    P.run(c, 6)
    check('DEFLECT: it flies away up the room', P.actor(c, i)['kind'] != AK_PROJ or P.actor(c, i)['y'] < y0, 'y %d -> %d' % (y0, P.actor(c, i)['y']))
    P.run(c, 40)
    # DEFLECT: the turned seed hurts a beetle in its way. Isolate the shot
    # from earlier projectiles, random path decoration and chasing AI; the
    # target remains beyond sword reach, so only the reflected seed can hit.
    CP.clear_enemies(c)
    for j in range(1, 96):
        if P.actor(c, j)['kind'] == AK_PROJ:
            P.w8(c, A + j * 64, 0)
    fx, fy = north_shot_position(c)
    CP.teleport(c, fx, fy)
    P.w8(c, A + 7, 0); P.w8(c, A + 6, 0)
    i = free_slot(c)
    put_actor(c, i, AK_PROJ, 0, fx, fy - 30, 6, flags=1, dir_=16, speed=0x100, damage=2, timer=1)
    b = spawn_enemy(c, EN_BEETLE, fx, fy - 60)
    P.w8(c, A + b * 64 + 29, 200); P.w16(c, A + b * 64 + 32, 0)
    P.press(c, 'B', 2, 40)
    check('DEFLECT: the turned seed hurts a beetle', P.actor(c, b)['kind'] != AK_ENEMY or P.actor(c, b)['hp'] < 2, 'kind %d hp %d' % (P.actor(c, b)['kind'], P.actor(c, b)['hp']))
    CP.clear_enemies(c); P.run(c, 20)
    # CARRY: a bush lifted, then the sword
    found = LP.find_tile(c, 'BUSH')
    if not found:
        for cell in range(25):
            LP.warp(c, cell, [s for s in range(4) if w['cells'][cell]['gate'][s]][0])
            found = LP.find_tile(c, 'BUSH')
            if found:
                break
    check('CARRY: a bush to lift', found is not None, str(found))
    if found:
        bx, by, spot, key = found
        LP.stand_before(c, spot, key)
        P.press(c, 'R', 2, 16)
        check('CARRY: lifted, arms up', state(c) == PS_CARRY and P.r8(c, pl + PL_CARRY) == 1, 'state %d carry %d' % (state(c), P.r8(c, pl + PL_CARRY)))
        P.snap(c, os.path.join(S, 'wood_carry.png'))
        P.press(c, 'B', 2, 3)
        check('CARRY: a swing drops it and the sword comes out', P.r8(c, pl + PL_CARRY) == 0 and state(c) == PS_ATTACK and LP.thrown(c) is not None, 'state %d carry %d thrown %s' % (state(c), P.r8(c, pl + PL_CARRY), LP.thrown(c) is not None))
        P.run(c, 40)
        check('CARRY: the dropped load broke', LP.thrown(c) is None, '')
    # BOW: given, an arrow loosed at a beetle
    LP.warp(c, w['entry'], 2)
    CP.heal(c); CP.clear_enemies(c)
    CP.teleport(c, hx, hy)
    P.w8(c, pl + PL_ITEMS2, P.r8(c, pl + PL_ITEMS2) | ITEM2_BOW)
    P.w8(c, pl + PL_ARROWS, 20)
    CP.equip_b(c, EQ_BOW)
    P.hold(c, 'UP', 2)
    b = spawn_enemy(c, EN_BEETLE, hx, hy - 48)
    P.press(c, 'A', 2, 2)
    i, arrow = find_actor(c, AK_PROJ, 3)
    check('BOW: A looses an arrow, one fewer', arrow is not None and P.r8(c, pl + PL_ARROWS) == 19, 'arrows %d arrow %s' % (P.r8(c, pl + PL_ARROWS), arrow))
    P.snap(c, os.path.join(S, 'wood_arrow.png'))
    P.run(c, 30)
    check('BOW: the arrow hit the beetle', P.actor(c, b)['kind'] != AK_ENEMY, 'kind %d hp %d' % (P.actor(c, b)['kind'], P.actor(c, b)['hp']))
    CP.clear_enemies(c)
    # BOW: with no arrows, nothing flies
    P.w8(c, pl + PL_ARROWS, 0)
    P.run(c, 20)
    P.press(c, 'A', 2, 2)
    check('BOW: no arrows, nothing flies', find_actor(c, AK_PROJ, 3)[0] is None, '')
    P.w8(c, pl + PL_ARROWS, 5)
    # CAP: used in the wood
    P.run(c, 20)
    CP.equip_b(c, EQ_HUBCAP)
    P.press(c, 'A', 2, 2)
    check('CAP: the mouth takes the hero', state(c) == PS_SWALLOWED, 'state %d' % state(c))
    snaps = []
    for k in range(4):
        P.snap(c, os.path.join(S, 'wood_cap%d.png' % k)); snaps.append(k)
        P.run(c, 9)
    zmax = 0
    for k in range(140):
        P.run(c, 1)
        if CP.area(c) == 0:
            zmax = max(zmax, P.actor(c, 0)['z'])
            if k % 8 == 0 and zmax and len(snaps) < 7:
                P.snap(c, os.path.join(S, 'wood_cap%d.png' % len(snaps))); snaps.append(1)
    pos = P.player_pos(c)
    check('CAP: home in the drain, at the spawn', CP.area(c) == 0 and pos == (12 * 16 + 8, 16 * 16 + 14), 'area %d pos %s' % (CP.area(c), pos))
    check('CAP: he dropped in from the ceiling', zmax >= 40 and state(c) == PS_NORMAL, 'zmax %d state %d' % (zmax, state(c)))
    # CAP: in the drain, only words
    P.press(c, 'A', 2, 4)
    tb = P.sym('gTbActive')
    check('CAP: in the drain, the cap only speaks', P.r8(c, tb) and state(c) == PS_NORMAL, 'box %d state %d' % (P.r8(c, tb), state(c)))
    CP.dismiss(c)
    # BOW: the Peddler's third ware
    CP.teleport(c, 4 * 16 + 8, 7 * 16 + 6)
    P.hold(c, 'UP', 8)
    P.press(c, 'A', 2, 30)
    count = P.r8(c, LP.ssym('sShopCount'))
    check('BOW: the Peddler sells arrows now', count == 3, 'wares %d' % count)
    P.snap(c, os.path.join(S, 'wood_shop.png'))
    P.press(c, 'DOWN', 2, 4); P.press(c, 'DOWN', 2, 4)
    P.w16(c, pl + 4, 50)
    P.press(c, 'A', 2, 30)
    check('BOW: ten arrows for ten gilt', P.r8(c, pl + PL_ARROWS) == 15 and P.r16(c, pl + 4) == 40, 'arrows %d gilt %d' % (P.r8(c, pl + PL_ARROWS), P.r16(c, pl + 4)))
    CP.dismiss(c)
    print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
    return 0 if all(res) else 1


if __name__ == '__main__':
    sys.exit(main())
