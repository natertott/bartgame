"""What enemy LEVELS actually spawn at a given difficulty?

sQuickStartDifficultyTiers states the intended odds and
tools/quickstart/tier_curve.py checks that table's arithmetic, but neither
measures the game. This walks into real region rooms, lets the region wave
spawn, and maps every live enemy back to the roster level it came from - so
the answer is what the ROM did, not what the table says it should do.

It exists because the table before this one gated levels 4, 5 and the
Elites to zero at the shipped difficulty, and nothing in the tooling
noticed for months: a weight of 0 and a weight of 2 look equally plausible
in a table, and only a count tells them apart.

    python3 tools/quickstart/tier_mix.py [rooms] [seeds]
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
LEVEL_ARRAYS = ['sQuickStartLevel1', 'sQuickStartLevel2', 'sQuickStartLevel3',
                'sQuickStartLevel4', 'sQuickStartLevel5', 'sQuickStartElites']
LEVEL_NAME = ['L1', 'L2', 'L3', 'L4', 'L5', 'ELITE']


def enemy_ids():
    """ENEMY_* / kind names -> numeric id, from the build's own enum."""
    out = {}
    path = os.path.join(P.ROOT, 'build/USA/enum_include/enemy.inc')
    for line in open(path):
        m = re.match(r'\.set (\w+),\s*(\d+)', line)
        if m:
            out[m.group(1)] = int(m.group(2))
    return out


def roster():
    """(id, form) -> level index, parsed from the six roster arrays."""
    src = open(os.path.join(P.ROOT, 'src/game.c')).read()
    ids = enemy_ids()
    table, unknown = {}, set()
    for lv, name in enumerate(LEVEL_ARRAYS):
        i = src.index('static const QuickStartEnemyPick %s[] = {' % name)
        body = src[i:src.index('\n};', i)]
        body = re.sub(r'//[^\n]*', '', body)
        for m in re.finditer(r'\{\s*(\w+),\s*(\d+)', body):
            nm, form = m.group(1), int(m.group(2))
            if nm not in ids:
                unknown.add(nm)
                continue
            table[(ids[nm], form)] = lv
    return table, unknown


def main():
    nrooms = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    nseeds = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    table, unknown = roster()
    if unknown:
        print('  (roster names not in enemy.inc, skipped: %s)'
              % ', '.join(sorted(unknown)))
    pool = P.region_pool()[:nrooms]
    hist = collections.Counter()
    unmapped = collections.Counter()
    for s in range(nseeds):
        seed = 0x1000_0000 + s * 0x9E3779B9
        for row in pool:
            c = emu.boot(ROM, seed=seed & 0xffffffff)
            emu.poison_here(c)
            emu.warp(c, row['area'], row['room'], row['entrance'][0], row['entrance'][1])
            if emu.here(c) != (row['area'], row['room']):
                del c
                continue
            # The region intro hint holds PL_BUSY and the wave does not run
            # until it is dismissed.
            for _ in range(10):
                emu.press(c, c.KEY_A, 5, 10)
            for _ in range(240):
                c.run_frame()
            for i in range(emu.MAX_ENT):
                b = emu.GENT + i * emu.STRIDE
                if c.memory.u8[b + emu.ENT_KIND] != emu.KIND_ENEMY:
                    continue
                key = (c.memory.u8[b + emu.ENT_ID], c.memory.u8[b + emu.ENT_TYPE])
                if key in table:
                    hist[table[key]] += 1
                elif (key[0], 0) in table:
                    hist[table[(key[0], 0)]] += 1
                else:
                    unmapped[key] += 1
            del c
    total = sum(hist.values())
    print('\n%d live enemies sampled over %d rooms x %d seeds'
          % (total, len(pool), nseeds))
    if not total:
        print('  nothing spawned - check the warp and the hint dismissal')
        return 1
    print('  level | count | share')
    for lv in range(6):
        print('  %-5s | %5d | %5.1f%%'
              % (LEVEL_NAME[lv], hist[lv], hist[lv] / total * 100))
    if unmapped:
        print('  not in any roster (vanilla room population): %d across %d kinds'
              % (sum(unmapped.values()), len(unmapped)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
