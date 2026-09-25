"""WHEN is a chuchu boss actually hittable? Measured, per subAction.

The report was "Green and Blue ChuChu are sometimes resistant, sometimes
susceptible", and reading chuchuBoss.c says why it would be: the peel
handler sub_08027AA4 is not called from the tick, it is called by hand from
four of the twelve subAction handlers. Everywhere else a sword contact is
delivered, consumed by the collision matrix for zero damage, and dropped.

But which subActions a fight actually spends its time in is not something
the source tells you, so this asks the ROM. It engages a family for real
(the boss_kill.py recipe - the intro needs the player to WALK), then every
frame forges a sword contact whenever iframes are clear and watches the
peel counter on the body's Helper. Per subAction it reports contacts
delivered and counter advances; a row with contacts and no advances is a
window where the player's sword does nothing.

    python3 tools/quickstart/chuchu_windows.py [--form 0|4] [--frames N]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, entities, here, KIND_ENEMY, GENT, STRIDE, r16
import parse_tables as P
import boss_region as B
from callrom import call_keep

CONTACT_NOW = 0x80
CONTACT_SRC_SWORD = 4
OFF_SUBACTION, OFF_IFRAMES, OFF_CFLAGS, OFF_HITTYPE = 0x0d, 0x3d, 0x41, 0x3f
OFF_HEALTH, OFF_HELPER = 0x45, 0x84
H_STAGE, H_ROUND, H_STRETCH, H_PEEL = 3, 4, 5, 6


def r32(c, a):
    return (c.memory.u8[a] | (c.memory.u8[a + 1] << 8) |
            (c.memory.u8[a + 2] << 16) | (c.memory.u8[a + 3] << 24))


def bodies(c):
    return [GENT + idx * STRIDE
            for (idx, k, ident, t, x, y) in entities(c, kind=KIND_ENEMY)
            if ident == B.CHUCHU_BOSS and t == 0]


def spawn(c, x, y, form, settle=120):
    ox, oy = r16(c, 0x03000bf0 + 6), r16(c, 0x03000bf0 + 8)
    ptr = call_keep(c, B.CREATE_ENEMY, (B.CHUCHU_BOSS, form))
    if ptr == 0:
        return None
    B.w16a(c, ptr + 0x2e, ox + x)
    B.w16a(c, ptr + 0x32, oy + y)
    c.memory.u8[ptr + 0x38] = 1
    call_keep(c, B.UPDATE_SPRITE, (ptr,))
    for _ in range(settle):
        c.run_frame()
    B.clear_normals(c)
    return ptr


def run(form, frames):
    region = next(r for r in P.region_pool()
                  if r['roomName'] == 'ROOM_CASTLE_GARDEN_MAIN')
    rx, ry = region['reward']
    c = boot(os.path.join(P.ROOT, 'tmc.gba'))
    B.enter(c, region)
    if spawn(c, rx, ry, form) is None:
        print('  could not spawn form %d' % form)
        return None
    # Engage: the intro's first two stages wait on the player's action byte,
    # and a warped-in player never leaves PLAYER_ROOMTRANSITION by itself.
    for f in range(2400):
        k = c.KEY_RIGHT if (f // 30) % 2 == 0 else c.KEY_LEFT
        c.set_keys(k)
        B.heal(c)
        c.run_frame()
        c.clear_keys(k)
        bs = bodies(c)
        if bs and c.memory.u8[bs[0] + OFF_SUBACTION] != 0:
            break
    stats = {}
    prev_peel, prev_round = None, None
    for f in range(frames):
        bs = bodies(c)
        if not bs:
            break
        b = bs[0]
        sub = c.memory.u8[b + OFF_SUBACTION]
        helper = r32(c, b + OFF_HELPER)
        row = stats.setdefault(sub, dict(frames=0, contacts=0, peel_up=0,
                                         round_up=0, hittype=set()))
        row['frames'] += 1
        row['hittype'].add(c.memory.u8[b + OFF_HITTYPE])
        pk = c.memory.u8[helper + H_PEEL] if helper else 0
        rd = c.memory.u8[helper + H_ROUND] if helper else 0
        if prev_peel is not None and pk > prev_peel:
            row['peel_up'] += 1
        if prev_round is not None and rd > prev_round:
            row['round_up'] += 1
        prev_peel, prev_round = pk, rd
        if c.memory.u8[b + OFF_IFRAMES] == 0:
            c.memory.u8[b + OFF_CFLAGS] = CONTACT_NOW | CONTACT_SRC_SWORD
            row['contacts'] += 1
        # The core phase subtracts health through the collision system, which
        # a forged contact cannot do; keep it alive so the fight keeps
        # cycling instead of ending after one round.
        for (idx, _typ, hp, _x, _y) in B.pieces(c):
            if hp == 0:
                c.memory.u8[GENT + idx * STRIDE + OFF_HEALTH] = 0x20
        B.heal(c)
        c.run_frame()
    del c
    return stats


NAMES = {0: 'intro', 1: 'idle/hop', 2: 'settle', 3: 'wander', 4: 'falling',
         5: 'land', 6: 'post-peel beat', 7: 'split', 8: 'core exposed',
         9: 'cutscene beat', 10: 'peeled chase', 11: 're-armour', 12: 'death'}


def main():
    frames = int(sys.argv[sys.argv.index('--frames') + 1]) if '--frames' in sys.argv else 5400
    forms = [int(sys.argv[sys.argv.index('--form') + 1])] if '--form' in sys.argv else [0, 4]
    bad = []
    for form in forms:
        print('== form %d (%s)' % (form, 'green' if form == 0 else 'blue'))
        stats = run(form, frames)
        if not stats:
            continue
        print('   %-4s %-16s %7s %9s %8s %8s  %s'
              % ('sub', 'what', 'frames', 'contacts', 'peel+', 'round+', 'hitTypes'))
        for sub in sorted(stats):
            r = stats[sub]
            flag = ''
            # Only the ARMOURED phases can be judged here. Once hitType
            # leaves 0x7D the body is no longer the target - the exposed
            # core is, and the core's damage is subtracted by the collision
            # system, which a forged contactFlags write cannot do (the same
            # limit boss_kill.py documents). Flagging those rows would
            # report a probe limit as a game defect.
            if 0x7D in r['hittype'] and r['contacts'] > 8 and r['peel_up'] == 0 and r['round_up'] == 0:
                flag = '   <-- DEAD WINDOW'
                bad.append((form, sub))
            print('   %-4d %-16s %7d %9d %8d %8d  %s%s'
                  % (sub, NAMES.get(sub, '?'), r['frames'], r['contacts'],
                     r['peel_up'], r['round_up'], sorted(r['hittype']), flag))
    print()
    if bad:
        print('DEAD WINDOWS (contacts land, nothing advances): %s'
              % ', '.join('form %d subAction %d' % x for x in bad))
    else:
        print('no dead windows: every subAction that took contacts advanced something')
    return 0


if __name__ == '__main__':
    sys.exit(main())
