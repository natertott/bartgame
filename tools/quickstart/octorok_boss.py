"""Can the Big Octorok exist outside the Temple of Droplets, and can a sword
kill it?

Two questions, in that order, because the second is meaningless if the first
fails. The Big Octorok is not a single entity: OctorokBoss_Init zMallocs an
OctorokBossHeap and builds a family - WHOLE, four LEGs, a TAIL chain, a
TAIL_END and a MOUTH - every one of which dereferences that heap every
frame. It also drives affine sprites and calls LoadFixedGFX on a phase
change. None of that is arena-specific on paper; whether it survives being
dropped into an overworld room is a measurement, not a reading.

The vanilla gate is the LANTERN. In the frozen phases (bossPhase & 1) the
TAIL_END accepts exactly one contact source - 7, COL_LANTERN - and nothing
else does anything at all. That is the "gated on a specific item" the mode
cannot afford: a run that never drew a Lantern could not finish the fight.

    python3 tools/quickstart/octorok_boss.py            # spawn + survive
    python3 tools/quickstart/octorok_boss.py --fight    # + a sword-only kill
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, entities, here, KIND_ENEMY, GENT, STRIDE, r16
import parse_tables as P
import boss_region as B
from callrom import call_keep

OCTOROK_BOSS = next(int(l.split(',')[1]) for l in
                    open(os.path.join(P.ROOT, 'build/USA/enum_include/enemy.inc'))
                    if l.strip().startswith('.set OCTOROK_BOSS,'))
PLAYER = 0x03001160
OFF_ACTION, OFF_SUBACTION, OFF_TYPE = 0x0c, 0x0d, 0x0a
OFF_HITTYPE, OFF_HEALTH, OFF_CFLAGS, OFF_IFRAMES = 0x3f, 0x45, 0x41, 0x3d
CONTACT_NOW = 0x80


def pieces(c):
    return [(idx, typ, GENT + idx * STRIDE, x, y)
            for (idx, k, ident, typ, x, y) in entities(c, kind=KIND_ENEMY)
            if ident == OCTOROK_BOSS]


def spawn(c, x, y, settle=180):
    ox, oy = r16(c, 0x03000bf0 + 6), r16(c, 0x03000bf0 + 8)
    ptr = call_keep(c, B.CREATE_ENEMY, (OCTOROK_BOSS, 0))
    if ptr == 0:
        return None
    B.w16a(c, ptr + 0x2e, ox + x)
    B.w16a(c, ptr + 0x32, oy + y)
    c.memory.u8[ptr + 0x38] = 1
    call_keep(c, B.UPDATE_SPRITE, (ptr,))
    for _ in range(settle):
        B.heal(c)
        c.run_frame()
    return ptr


def main():
    fails = []

    def check(ok, msg):
        print(('  ok   ' if ok else '  FAIL ') + msg)
        if not ok:
            fails.append(msg)

    region = next(r for r in P.region_pool()
                  if r['roomName'] == 'ROOM_CASTLE_GARDEN_MAIN')
    rx, ry = region['reward']
    c = boot(os.path.join(P.ROOT, 'tmc.gba'))
    B.enter(c, region)
    check(here(c) == (region['area'], region['room']), 'landed in the room')
    B.clear_normals(c)
    ptr = spawn(c, rx, ry)
    check(ptr not in (None, 0), 'CreateEnemy(OCTOROK_BOSS) returned a slot')
    if not ptr:
        print('\nFAILED: %d' % len(fails))
        return 1
    fam = pieces(c)
    kinds = sorted(set(t for (_i, t, _b, _x, _y) in fam))
    print('   family: %d pieces, types %s' % (len(fam), kinds))
    check(len(fam) > 1, 'the family composed (heap allocated, parts created)')

    # Survive: the family must still be there, and the game still running, a
    # good while later. A heap deref on a cleared slot shows up as a
    # vanished family or a frozen frame counter, not as a tidy error.
    ticks0 = c.memory.u8[0x03001000 + 0x0C]
    for f in range(900):
        k = c.KEY_RIGHT if (f // 30) % 2 == 0 else c.KEY_LEFT
        c.set_keys(k)
        B.heal(c)
        c.run_frame()
        c.clear_keys(k)
    ticks1 = c.memory.u8[0x03001000 + 0x0C]
    fam = pieces(c)
    print('   after 900 frames: %d pieces, ticks %d -> %d' % (len(fam), ticks0, ticks1))
    check(len(fam) > 1, 'the family survived 900 frames in an overworld room')
    check(ticks0 != ticks1, 'the game is still ticking')

    whole = [b for (_i, t, b, _x, _y) in fam if t == 0]
    if whole:
        w = whole[0]
        print('   WHOLE: action %d subAction %d hitType 0x%02x health %d'
              % (c.memory.u8[w + OFF_ACTION], c.memory.u8[w + OFF_SUBACTION],
                 c.memory.u8[w + OFF_HITTYPE], c.memory.u8[w + OFF_HEALTH]))
        check(c.memory.u8[w + OFF_ACTION] != 3, 'the WHOLE is not stuck in OnDeath')

    if '--fight' in sys.argv:
        # Two questions, measured separately, because a free-roaming driver
        # answers neither cleanly. Chasing an eleven-piece boss around an
        # overworld room, this harness lands almost nothing - not because the
        # sword does not work but because staying in range of a wandering
        # family is a driving problem. So:
        #
        #   1. DOES A PLAIN SWORD HURT IT?  Stand beside it and swing.
        #   2. DOES THE WHOLE FIGHT FINISH? Deliver the same contacts the
        #      swing delivers, frame by frame, and watch all eight phases
        #      run to the death sequence.
        print('   1. a plain sword, standing beside it')
        w = [b for (_i, _t, b, _x, _y) in pieces(c) if _t == 0][0]
        hp0 = c.memory.u8[w + OFF_HEALTH]
        bx, by = r16(c, w + 0x2e), r16(c, w + 0x32)
        B.w16a(c, PLAYER + 0x2e, bx)
        B.w16a(c, PLAYER + 0x32, by + 24)
        for f in range(300):
            k = c.KEY_B if (f // 10) % 2 == 0 else 0   # B is the sword
            c.set_keys(k)
            B.heal(c)
            c.run_frame()
            c.clear_keys(k)
        hp1 = c.memory.u8[w + OFF_HEALTH]
        print('      body health %d -> %d in 300 frames' % (hp0, hp1))
        check(hp1 < hp0, 'a plain sword takes health off the Big Octorok')

        print('   2. the whole fight, phase by phase')
        c2 = boot(os.path.join(P.ROOT, 'tmc.gba'))
        B.enter(c2, region)
        B.clear_normals(c2)
        spawn(c2, rx, ry)
        w2 = [b for (_i, _t, b, _x, _y) in pieces(c2) if _t == 0][0]
        phases, killed = [], -1
        for f in range(7200):
            if not pieces(c2):
                killed = f
                break
            k = c2.KEY_RIGHT if (f // 30) % 2 == 0 else c2.KEY_LEFT
            c2.set_keys(k)
            if c2.memory.u8[w2 + OFF_IFRAMES] == 0:
                c2.memory.u8[w2 + OFF_CFLAGS] = CONTACT_NOW | 4
            B.heal(c2)
            c2.run_frame()
            c2.clear_keys(k)
            st = (c2.memory.u8[w2 + OFF_ACTION], c2.memory.u8[w2 + OFF_SUBACTION])
            if not phases or phases[-1] != st:
                phases.append(st)
        print('      %d (action, subAction) transitions; family gone at frame %s'
              % (len(phases), killed if killed >= 0 else 'never'))
        check(killed >= 0, 'the eight-phase fight runs to the death sequence')
        del c2

    del c
    print()
    print('PASS' if not fails else 'FAILED: %d' % len(fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
