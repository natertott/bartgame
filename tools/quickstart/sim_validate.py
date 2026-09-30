"""Does the simulator's reach model agree with the shipped ROM?

sim.py re-implements QuickStartReachRoomOk so it can run tens of thousands
of runs in seconds. A re-implementation is a CLAIM about the C, never a
measurement of it, so this asks the ROM the same questions and compares.

QuickStartReachRoomOk(regions, held, area, room) is a pure function of its
four arguments and the compiled tables - it reads no save state - so it can
be called with arbitrary arguments and the answer is directly comparable.
That is the whole reach table and the DNF term logic, which is the part of
the model everything else rests on.

NOT validated here, and worth being explicit about: QuickStartReachable-
Regions reads the drop region out of the save, so it is not a pure function
and cannot be called with a made-up argument. Its flood is eight lines over
sQuickStartRegionAdjacency and sQuickStartReachRegion, both of which sim.py
parses out of the source and prints for eyeballing (--tables).

Usage: python3 tools/quickstart/sim_validate.py [--cases 400]
"""
import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
from callrom import call_args, game_sym
import parse_tables as P
import sim

ROM = os.path.join(P.ROOT, 'tmc.gba')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cases', type=int, default=400)
    ap.add_argument('--tables', action='store_true')
    a = ap.parse_args()
    if a.tables:
        print('region entry costs:')
        for i, n in enumerate(sim.REGION_NAMES):
            print(f'  {n:<5} {[hex(t) for t in sim.REGION_ENTRY[i]]}')
        print('adjacency:')
        for i, n in enumerate(sim.REGION_NAMES):
            print(f'  {n:<5} ' + ','.join(sim.REGION_NAMES[j] for j in range(13)
                                          if (sim.ADJACENCY[i] >> j) & 1))
        return 0

    rng = random.Random(0xA11CE)
    rooms = [(a_, r_) for a_, r_, _, _ in sim.ALL_ROOMS]
    cases = []
    for _ in range(a.cases):
        # Masks drawn over the ITEM bits plus the fusion bit, which are the
        # only ones the game can ever hold. Including a few all-ones and
        # all-zeros cases on purpose: the edges are where a term-logic bug
        # hides.
        held = rng.getrandbits(sim.ITEM_BITS) | (sim.TOKEN_BITS['QS_REACH_FUSION']
                                                 if rng.random() < 0.5 else 0)
        regions = rng.getrandbits(len(sim.REGION_NAMES))
        cases.append((regions, held) + rng.choice(rooms))
    cases.append((0, 0, *rooms[0]))
    cases.append(((1 << len(sim.REGION_NAMES)) - 1,
                  (1 << sim.ITEM_BITS) - 1 | sim.TOKEN_BITS['QS_REACH_FUSION'], *rooms[0]))

    fn = game_sym('QuickStartReachRoomOk')
    c = emu.boot(ROM)
    bad, agree = [], 0
    for regions, held, area, room in cases:
        rom = call_args(c, fn, (regions, held, area, room)) & 1
        model = 1 if sim.reach_room_ok(regions, held, area, room) else 0
        if rom == model:
            agree += 1
        else:
            bad.append((hex(regions), hex(held), area, room, rom, model))
    del c
    print(f'{agree}/{len(cases)} agree')
    for row in bad[:20]:
        print('  MISMATCH regions=%s held=%s area=%d room=%d rom=%d model=%d' % row)
    if not bad:
        print('the model and the ROM answer QuickStartReachRoomOk identically')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
