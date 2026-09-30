"""Generate sQuickStartDifficultyTiers, and check the one in game.c.

THE RULE THIS ENCODES. The user: "The difficulty scaling should not be
about what tiers or types of enemies are possible, but rather the chance
that various tiers spawn." So no column is ever zero once the ramp has
started - difficulty moves the ODDS, it does not unlock content. The table
that shipped before this did the opposite: difficulty 3 was
{ 30, 50, 20, 0, 0, 0 }, which is a hard gate wearing a weighted die's
clothes, and 29 of the roster's 71 entries could not appear at the shipped
difficulty at all.

SHAPE. A discrete gaussian over the six columns (levels 1-5 plus Elites)
whose peak walks from level 1 at step 0 to level 4 at step 12, with two
corrections:

  * the Elite column is damped to 18% of its natural weight, because four
    of its six entries are Darknut forms - it is the Darknut dial, and a
    pile of Darknuts is the thing the wave rework exists to prevent;
  * a per-column FLOOR, which is what actually answers the brief. The
    gaussian alone puts 0.4% in level 5 at step 3, and integer rounding
    turns that into the same gate as before.

    python3 tools/quickstart/tier_curve.py          # print the C table
    python3 tools/quickstart/tier_curve.py --check  # compare with game.c
"""
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
MAXD = 12
LEVELS = 6

# Unchanged from the table this replaced: the user asked about WHICH
# enemies spawn, not how many, and density is tuned against the entity
# budget (QUICKSTART_MAX_LIVE_ENEMIES, QuickStartRoomEnemyCeiling).
DENSITY = [25, 22, 17, 13, 12, 11, 10, 10, 9, 8, 7, 6, 6]

# Steps 0-2 are the tutorial ramp and keep a little gating; from step 3 -
# the shipped baseline - every column is live.
FLOOR = {0: [0, 0, 0, 0, 0, 0],
         1: [0, 0, 1, 1, 1, 0],
         2: [0, 0, 1, 2, 1, 1]}
FLOOR_DEFAULT = [0, 0, 1, 4, 2, 1]
ELITE_DAMP = 0.18


def curve():
    rows = []
    for d in range(MAXD + 1):
        mu = 0.15 + d * (3.45 / MAXD)
        sigma = 0.85 + d * (0.55 / MAXD)
        w = [math.exp(-((i - mu) ** 2) / (2 * sigma * sigma)) for i in range(LEVELS)]
        w[5] *= ELITE_DAMP
        total = sum(w)
        pct = [x / total * 100 for x in w]
        ints = [int(x) for x in pct]
        order = sorted(range(LEVELS), key=lambda i: -(pct[i] - ints[i]))
        for i in order[:100 - sum(ints)]:
            ints[i] += 1
        floor = FLOOR.get(d, FLOOR_DEFAULT)
        for i in range(LEVELS):
            if ints[i] < floor[i]:
                need = floor[i] - ints[i]
                ints[i] = floor[i]
                for _ in range(need):
                    j = max(range(LEVELS), key=lambda k: ints[k] if k != i else -1)
                    ints[j] -= 1
        rows.append(ints)
    return rows


def check(rows):
    """The invariants. A table that breaks one of these is a regression."""
    bad = []
    for d, r in enumerate(rows):
        if sum(r) != 100:
            bad.append('step %d sums to %d, not 100 - QuickStartRollEnemyLevel '
                       'rolls Random() %% 100 and would fall through' % (d, sum(r)))
        if any(x < 0 for x in r):
            bad.append('step %d has a negative weight' % d)
    for d in range(3, MAXD + 1):
        for i in range(LEVELS):
            if rows[d][i] == 0:
                bad.append('step %d has a ZERO column at level %d - difficulty must '
                           'move the odds, not gate the content' % (d, i + 1))
    means = [sum((i + 1) * r[i] for i in range(LEVELS)) / 100.0 for r in rows]
    for d in range(MAXD):
        if means[d] > means[d + 1] + 1e-9:
            bad.append('mean level FALLS from step %d (%.2f) to %d (%.2f)'
                       % (d, means[d], d + 1, means[d + 1]))
    for i in (3, 4, 5):
        col = [r[i] for r in rows]
        if any(col[d] > col[d + 1] for d in range(MAXD)):
            bad.append('the level-%d column is not monotone: %s' % (i + 1, col))
    return bad, means


def from_game_c():
    src = open(os.path.join(ROOT, 'src/game.c')).read()
    i = src.index('sQuickStartDifficultyTiers[QUICKSTART_MAX_DIFFICULTY + 1] = {')
    body = src[i:src.index('\n};', i)]
    rows, dens = [], []
    for m in re.finditer(r'\{\s*\{([^}]*)\}\s*,\s*(\d+)\s*\}', body):
        rows.append([int(x) for x in m.group(1).split(',')])
        dens.append(int(m.group(2)))
    return rows, dens


def main():
    rows = curve()
    bad, means = check(rows)
    if '--check' in sys.argv:
        have, hdens = from_game_c()
        if have != rows or hdens != DENSITY:
            print('STALE: src/game.c does not match this curve')
            for d in range(min(len(have), len(rows))):
                if have[d] != rows[d] or hdens[d] != DENSITY[d]:
                    print('  step %-2d game.c %s/%s  curve %s/%s'
                          % (d, have[d], hdens[d], rows[d], DENSITY[d]))
            return 1
        print('src/game.c matches the curve (%d steps)' % len(rows))
    else:
        print('    //        L1  L2  L3  L4  L5  EL    density')
        for d, r in enumerate(rows):
            note = '  // the shipped baseline' if d == 3 else ''
            print('    /* %2d */ { { %2d, %2d, %2d, %2d, %2d, %2d }, %2d },%s'
                  % (d, r[0], r[1], r[2], r[3], r[4], r[5], DENSITY[d], note))
        print()
        print('  step | low(1-2) | mid(3) | high(4-5-EL) | mean level')
        for d, r in enumerate(rows):
            print('  %4d |   %3d%%   |  %3d%%  |     %3d%%     |   %.2f'
                  % (d, r[0] + r[1], r[2], r[3] + r[4] + r[5], means[d]))
    if bad:
        print('\nFAILED:')
        for b in bad:
            print('  ' + b)
        return 1
    print('\nOK: sums, floors and monotonicity all hold')
    return 0


if __name__ == '__main__':
    sys.exit(main())
