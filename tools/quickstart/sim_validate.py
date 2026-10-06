"""Does the simulator's reach model agree with the shipped ROM?

sim.py re-implements QuickStartReachRoomOk so it can run tens of thousands
of runs in seconds. A re-implementation is a CLAIM about the C, never a
measurement of it, so this asks the ROM the same questions and compares.

QuickStartReachTestRoom(pool, held, area, room) is a pure function of its
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
        print('nodes:')
        for i, (ring, area, room, ent) in enumerate(sim.NODES):
            print(f'  {i:2d} {sim.REGION_NAMES[ring]:<5} area {area} room {room}{" (entrance)" if ent else ""}')
        print('pool -> node:', sim.POOL_NODE)
        print(f'{len(sim.EDGES)} edges')
        return 0

    rng = random.Random(0xA11CE)
    rooms = [(a_, r_) for a_, r_, _, _ in sim.ALL_ROOMS]
    testable = ((1 << sim.ITEM_BITS) - 1) | sim.TOKEN_BITS['QS_REACH_FUSION'] | \
        sim.TOKEN_BITS['QS_REACH_LLR_NORTH'] | sim.BOULDER_BITS
    cases = []
    for _ in range(a.cases):
        # Masks drawn over every bit the game can hold: the items, the
        # fusion, the boulders and the derived north-field bit. Including a
        # few all-ones and all-zeros cases on purpose: the edges are where a
        # term-logic bug hides.
        held = rng.getrandbits(32) & testable
        if rng.random() < 0.3:
            held = rng.getrandbits(32) & testable & rng.getrandbits(32)
        pool = rng.randrange(sim.POOL_SIZE)
        cases.append((pool, held) + rng.choice(rooms))
    cases.append((0, 0, *rooms[0]))
    cases.append((1, testable, *rooms[0]))

    fn_room = game_sym('QuickStartReachTestRoom')
    fn_regions = game_sym('QuickStartReachTestRegions')
    c = emu.boot(ROM)
    bad, agree = [], 0
    for pool, held, area, room in cases:
        rom = call_args(c, fn_room, (pool, held, area, room), budget=4000000) & 1
        nodes = sim.reachable_nodes(held, pool)
        model = 1 if sim.reach_room_ok(nodes, held, area, room) else 0
        rom_regions = call_args(c, fn_regions, (pool, held), budget=4000000) & 0xffff
        model_regions = sim.regions_of(nodes) & 0xffff
        if rom == model and rom_regions == model_regions:
            agree += 1
        else:
            bad.append((pool, hex(held), area, room, rom, model, hex(rom_regions), hex(model_regions)))
    del c
    print(f'{agree}/{len(cases)} agree')
    for row in bad[:20]:
        print('  MISMATCH pool=%s held=%s area=%d room=%d rom=%d model=%d regions rom=%s model=%s' % row)
    if not bad:
        print('the model and the ROM answer QuickStartReachTestRoom and QuickStartReachTestRegions identically')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
