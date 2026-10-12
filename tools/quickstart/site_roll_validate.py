"""Does sim.site_roll deal the same ? room as the ROM?

QuickStartContentSiteRoll seeds the shared stream from (run seed, site),
so a site's kind and extra byte are a pure function of the run seed and
the tables - the memory pair is too, read from the same seed. This sets
gSave.run_seed, asks the ROM for every site, and compares with the model.

    python3 tools/quickstart/site_roll_validate.py [--seeds 12]
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
SAVE = 0x02002a40
RUN_SEED = SAVE + 0x4C
MEMORY_KEY = SAVE + 0x86   # gSave.qs_memory_key: cleared per seed, see below
OUT = 0x0203FF00   # two scratch bytes at the top of EWRAM


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=12)
    a = ap.parse_args()
    fn = game_sym('QuickStartContentSiteRoll')
    c = emu.boot(ROM)
    rng = random.Random(0x517E)
    seeds = [0, 1, 0xFFFFFFFF] + [rng.getrandbits(32) for _ in range(a.seeds)]
    agree, bad = 0, []
    for seed in seeds:
        for b in range(4):
            c.memory.u8[RUN_SEED + b] = (seed >> (8 * b)) & 0xff
        # The memory pair is cached under a 16-bit hash of the seed, and
        # seeds 0, 1 and 0xFFFFFFFF all hash to 1 - without this the ROM
        # answers for the previous seed's pair.
        c.memory.u8[MEMORY_KEY] = 0
        c.memory.u8[MEMORY_KEY + 1] = 0
        for i in range(len(sim.SITES)):
            c.memory.u8[OUT] = 0xEE
            c.memory.u8[OUT + 1] = 0xEE
            call_args(c, fn, (i, OUT, OUT + 1), budget=4000000)
            rom = (c.memory.u8[OUT], c.memory.u8[OUT + 1])
            model = sim.site_roll(seed, i)
            if rom == model:
                agree += 1
            else:
                bad.append((hex(seed), i, sim.SITES[i]['roomName'], rom, model))
    del c
    print(f'{agree}/{agree + len(bad)} site rolls agree over {len(seeds)} seeds x {len(sim.SITES)} sites')
    for row in bad[:20]:
        print('  MISMATCH seed=%s site=%d %s rom=%s model=%s' % row)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
