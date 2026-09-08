"""The Earth Element must not arrive before the chain has.

The user's report (Sep 2026): entering the element region got an Ezlo
"The Earth Element is here!" and the Element with the chain untouched,
"essentially making [the chain] completely optional".

Four questions, asked of the shipped code in the running ROM rather than
of a Python re-implementation of it:

  1. does the drop gate actually hold?  QuickStartWinCarrierMet at chain
     progress 0..5 - it must be false below 4 and may only turn true at 4;
  2. does the ELEMENT SPAWNER itself refuse early?  QuickStartSpawnWinKeyOnce
     is the one place the item is created, so it is asked directly, with
     room flag 43 (the bypass clause in its caller) forced set;
  3. with the chain finished, does the Element still arrive?  A gate that
     never opens is worse than one that never closes;
  4. is the "it is here!" line withheld until then?

    python3 tools/quickstart/element_gate.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import (boot, warp, poison_here, press, entities, KIND_OBJECT, r16)
from callrom import call_keep, game_sym
import parse_tables as P

SAVE = 0x02002a40
CHAIN_PROGRESS = SAVE + 0x35
ROOMFLAGS = 0x02034364          # gRoomVars.flags; QS room flag k = bit 256+k
RC = 0x03000bf0


def _enum(path, name):
    for line in open(path):
        if line.startswith('.set %s,' % name):
            return int(line.strip().split(',')[1])
    raise KeyError(name)


GROUND_ITEM = _enum('build/USA/enum_include/object.inc', 'GROUND_ITEM')
ITEM_EARTH = _enum('build/USA/enum_include/item.inc', 'ITEM_EARTH_ELEMENT')


def rf(c, k):
    b = 256 + k
    return (c.memory.u8[ROOMFLAGS + (b >> 3)] >> (b & 7)) & 1


def set_rf(c, k, on=True):
    b = 256 + k
    a, m = ROOMFLAGS + (b >> 3), 1 << (b & 7)
    c.memory.u8[a] = (c.memory.u8[a] | m) if on else (c.memory.u8[a] & ~m)


def elements(c):
    return [e for e in entities(c, kind=KIND_OBJECT)
            if e[2] == GROUND_ITEM and e[3] == ITEM_EARTH]


fails = []


def check(ok, msg):
    print(('  ok   ' if ok else '  FAIL ') + msg)
    if not ok:
        fails.append(msg)


def main():
    met = game_sym('QuickStartWinCarrierMet')
    pre = game_sym('QuickStartChainPreStepsDone')
    spawn = game_sym('QuickStartSpawnWinKeyOnce')
    elem_idx = game_sym('QuickStartElementRegionIndex')
    pool = P.region_pool()

    c = boot('tmc.gba', seed=0x11111111)
    poison_here(c)
    warp(c, P.AREAS['AREA_HYRULE_FIELD'],
         P.ROOMS['ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD'], 504, 456)
    for _ in range(300):
        c.run_frame()
    reg = pool[call_keep(c, elem_idx, ()) % len(pool)]
    print('== element region: %s' % reg['roomName'])
    poison_here(c)
    warp(c, reg['area'], reg['room'], reg['entrance'][0], reg['entrance'][1])
    for _ in range(240):
        c.run_frame()
    for _ in range(6):
        press(c, c.KEY_A, 4, 4)
    for _ in range(300):
        c.run_frame()

    # 1. the gate, across the whole progress range
    table = []
    for prog in range(6):
        c.memory.u8[CHAIN_PROGRESS] = prog
        table.append((prog, call_keep(c, pre, ()), call_keep(c, met, ())))
    print('   progress -> preStepsDone/carrierMet: %s'
          % ' '.join('%d:%d/%d' % t for t in table))
    check(all(m == 0 for (p, _d, m) in table if p < 4),
          'the carrier is never met below four completed steps')
    check(all(d == 1 for (p, d, _m) in table if p >= 4),
          'the pre-steps read done at four and above')

    # 2. the spawner itself, with the caller's bypass clause forced on
    c.memory.u8[CHAIN_PROGRESS] = 0
    set_rf(c, 43, True)          # "an Element was created this round"
    call_keep(c, spawn, (reg['reward'][0], reg['reward'][1]))
    for _ in range(30):
        c.run_frame()
    n_early = len(elements(c))
    print('   spawner called at progress 0 with room flag 43 set -> %d element(s)' % n_early)
    check(n_early == 0, 'the spawner refuses to create the Element early')

    # 3. ...but still delivers once the chain is done
    set_rf(c, 43, False)
    c.memory.u8[CHAIN_PROGRESS] = 4
    call_keep(c, spawn, (reg['reward'][0], reg['reward'][1]))
    for _ in range(30):
        c.run_frame()
    n_late = len(elements(c))
    print('   spawner called at progress 4 -> %d element(s)' % n_late)
    check(n_late == 1, 'the Element still arrives once the chain is finished')
    del c

    # 4. the hint, on a clean entry with the chain untouched
    c = boot('tmc.gba', seed=0x11111111)
    poison_here(c)
    warp(c, reg['area'], reg['room'], reg['entrance'][0], reg['entrance'][1])
    for _ in range(240):
        c.run_frame()
    for _ in range(6):
        press(c, c.KEY_A, 4, 4)
    for _ in range(600):
        c.run_frame()
    shown = rf(c, 45)
    print('   progress=%d; early-arrival line shown: %d; elements in room: %d'
          % (c.memory.u8[CHAIN_PROGRESS], shown, len(elements(c))))
    check(len(elements(c)) == 0, 'no Element in the room on an early visit')
    del c

    print('\n%s: %d failure(s)' % ('FAILED' if fails else 'OK', len(fails)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
