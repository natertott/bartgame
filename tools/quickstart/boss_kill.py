"""Engage a chuchu boss family for real, then kill it - the F6 gate.

The roadmap listed one blocker in front of multi-boss combos: "killing an
ENGAGED boss by script", a bar the harness had never met anywhere, Castle
Garden included. The recorded diagnosis was that the engaged fight ignores
sword taps at 1 hp because "the peel wants real contact windows the dumb
driver doesn't hit".

THAT DIAGNOSIS WAS WRONG, and the truth is simpler. Measured here: the
family never engaged at all. Its intro is a nine-stage machine on the body's
Helper (unk_03), and stages 1 and 2 are gated on the PLAYER'S action byte:

    sub_08026328:  if (gPlayerEntity.base.action != PLAYER_ROOMTRANSITION)
    sub_08026358:  if (gPlayerEntity.base.action != PLAYER_ROOM_EXIT)

A warped-in player sits in PLAYER_ROOMTRANSITION (action 22) and never
leaves it on its own, so the intro parked at stage 1 forever - measured, for
1500 frames - and every piece stayed at action 1 / subAction 0. subAction 0
is the intro dispatcher and is the ONE subAction that never calls the peel
handler (sub_08027AA4), so no sword tap could ever have registered. The
"boss" the old driver was hitting was an inert stack, exactly as the
roadmap's trap #1 describes for an undismissed textbox - same symptom, a
different cause, and pressing A only fixed it by accident (it nudges the
player out of the transition action).

The fix is one line of driver: WALK. Give the player real movement input and
action 22 drops to 1, the intro runs 1 -> 3 -> 5 -> 9, and subAction leaves
0 into the live fight. From there the peel handler runs and the fight is
genuinely engaged.

WHAT IS REAL HERE AND WHAT IS SYNTHESISED, stated plainly because a harness
that blurs it is worthless:
  * the engagement is real - the shipped intro machine, driven only by
    ordinary player input;
  * the peel is real - contacts are delivered by writing contactFlags the
    way the collision system does, and the shipped sub_08027AA4 does
    everything downstream (counter, particles, sounds, the transition);
  * the FINAL BLOW is health := 0 on the exposed pieces. The collision
    system, not the receiving entity, subtracts health, so a forged contact
    cannot do it. Everything after the zero - GetNextFunction routing to
    ChuchuBoss_OnDeath, the family teardown, the QUICKSTART death hooks - is
    the shipped path, which is exactly what the dual-death question is
    about.

    python3 tools/quickstart/boss_kill.py [ROOM_NAME] [--dual]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, entities, here, KIND_ENEMY, GENT, STRIDE, r16
import parse_tables as P
import boss_region as B

PLAYER = 0x03001160
PLAYER_ROOMTRANSITION = 22
CONTACT_NOW = 0x80
CONTACT_SRC_SWORD = 4
OFF_ACTION, OFF_SUBACTION = 0x0c, 0x0d
OFF_IFRAMES, OFF_CFLAGS, OFF_HITTYPE, OFF_HEALTH = 0x3d, 0x41, 0x3f, 0x45
OFF_HELPER = 0x84


def r32(c, a):
    return (c.memory.u8[a] | (c.memory.u8[a + 1] << 8) |
            (c.memory.u8[a + 2] << 16) | (c.memory.u8[a + 3] << 24))


def family(c):
    """(slot, type, base) for every live chuchu-boss piece."""
    return [(idx, c.memory.u8[GENT + idx * STRIDE + 0x0a], GENT + idx * STRIDE)
            for (idx, k, ident, t, x, y) in entities(c, kind=KIND_ENEMY)
            if ident == B.CHUCHU_BOSS]


def bodies(c):
    """The type-0 pieces - one per family, and the only ones that carry a
    Helper (the intro stage machine and the peel counter both live there)."""
    return [b for (_i, t, b) in family(c) if t == 0]


def engage(c, want, frames=2400):
    """Walk until every family's body has left subAction 0.

    The walking is the whole point - see the module docstring. Direction
    alternates so the driver cannot wander into a wall and stall against it.
    """
    for f in range(frames):
        k = c.KEY_RIGHT if (f // 30) % 2 == 0 else c.KEY_LEFT
        c.set_keys(k)
        B.heal(c)
        c.run_frame()
        c.clear_keys(k)
        bs = bodies(c)
        if len(bs) >= want and all(c.memory.u8[b + OFF_SUBACTION] != 0 for b in bs):
            return f
    return -1


def peel(c, frames=1200):
    """Deliver sword contacts to every body while its iframes are clear.

    Returns the number of times a body's hitType was seen at 0 - the peeled
    state, where the armour is off and the core is exposed. iframes are
    respected rather than overridden: that spacing is what makes a contact
    count once per swing instead of once per frame of overlap.
    """
    peels = 0
    for _f in range(frames):
        for b in bodies(c):
            if c.memory.u8[b + OFF_IFRAMES] == 0:
                c.memory.u8[b + OFF_CFLAGS] = CONTACT_NOW | CONTACT_SRC_SWORD
            if c.memory.u8[b + OFF_HITTYPE] == 0:
                peels += 1
        B.heal(c)
        c.run_frame()
    return peels


def kill(c, settle=600, hold=30):
    """Zero every piece on ONE frame, then let the death machinery run.

    One frame on purpose: simultaneous deaths across two engaged families is
    the case #125 was filed about, and staggering them would measure the
    easy version.

    The `hold` window re-zeros for half a second afterwards, and it is not
    belt-and-braces - it is load-bearing. A peel in flight writes
    `super->child->health = 0xff` (chuchuBoss.c, the armour-restore path), so
    a single zero landing on the wrong frame is undone and the family walks
    away immortal. Measured: killing after a 300-frame peel worked, killing
    after 1200 frames left all five pieces standing, and that difference is
    entirely this race. The first zero is still the one that starts the
    death machine; the hold only stops the boss from healing out of it.
    """
    for (_i, _t, b) in family(c):
        c.memory.u8[b + OFF_HEALTH] = 0
    for f in range(settle):
        if f < hold:
            for (_i, _t, b) in family(c):
                c.memory.u8[b + OFF_HEALTH] = 0
        B.heal(c)
        c.run_frame()
        if not family(c):
            return []
    return family(c)


def main():
    room = next((a for a in sys.argv[1:] if not a.startswith('--')),
                'ROOM_CASTLE_GARDEN_MAIN')
    dual = '--dual' in sys.argv
    region = next(r for r in P.region_pool() if r['roomName'] == room)
    rx, ry = region['reward']
    want = 2 if dual else 1

    fails = []

    def check(ok, msg):
        print(('  ok   ' if ok else '  FAIL ') + msg)
        if not ok:
            fails.append(msg)

    print('== %s%s' % (room, ' (DUAL)' if dual else ''))
    c = boot(os.path.join(P.ROOT, 'tmc.gba'))
    B.enter(c, region)
    check(here(c) == (region['area'], region['room']), 'landed in the room')
    for fam in range(want):
        off = (fam * 96 - 48) if dual else 0
        if B.spawn_family(c, rx + off, ry) is None:
            check(False, 'family %d spawned' % fam)
            print('\nFAILED: %d' % len(fails))
            return 1
    check(len(bodies(c)) == want, '%d family bodies composed (got %d)' % (want, len(bodies(c))))

    print('   player action after warp: %d (%s)'
          % (c.memory.u8[PLAYER + OFF_ACTION],
             'ROOMTRANSITION - the intro is blocked here'
             if c.memory.u8[PLAYER + OFF_ACTION] == PLAYER_ROOMTRANSITION else 'already walking'))
    f = engage(c, want)
    stages = [c.memory.u8[r32(c, b + OFF_HELPER) + 3] for b in bodies(c)]
    subs = [c.memory.u8[b + OFF_SUBACTION] for b in bodies(c)]
    print('   engaged at frame %d; intro stages %s, subActions %s' % (f, stages, subs))
    check(f >= 0, 'every family engaged (subAction left the intro)')

    peels = peel(c)
    print('   peeled-state frames observed: %d' % peels)
    check(peels > 0, 'the peel handler runs on the engaged body')

    left = kill(c)
    print('   pieces left after the kill: %d' % len(left))
    check(len(left) == 0, 'the whole family died')

    # Responsiveness: #125 was filed as a SOFTLOCK, so the question is not
    # only "did they die" but "is the game still playable afterwards".
    # ALL FOUR directions, and "any" passes. One direction is not a
    # responsiveness test: measured against a no-boss control in the same
    # room, the player refuses three of the four from this spot simply
    # because the geometry blocks them, and reading that as a freeze
    # invents a softlock that is not there.
    moved = False
    for key in (c.KEY_UP, c.KEY_DOWN, c.KEY_LEFT, c.KEY_RIGHT):
        px, py = r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32)
        for _ in range(90):
            c.set_keys(key)
            c.run_frame()
            c.clear_keys(key)
        if (r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32)) != (px, py):
            moved = True
            break
    print('   player moved after the kill: %s; room %s' % (moved, here(c)))
    check(moved, 'the player still responds to input after the deaths')
    check(here(c) == (region['area'], region['room']), 'still in the same room')
    del c

    print('\n%s: %d failure(s)' % ('FAILED' if fails else 'OK', len(fails)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
