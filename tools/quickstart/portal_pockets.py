"""Where a portal could take the player: the reach graph's pockets.

For the portal ? room research (docs/QUICKSTART_PORTAL_POCKETS.md). Reads
the same reach graph the game floods (include/quickstart/reach.h, through
sim.py) and answers, for every node the mainland cannot walk to with the
boot kit (the Smith's Sword and the Ocarina):

  entry    the fewest items that walk there from a South Hyrule Field
           drop (tokens that are not items - a golden gate, a boulder -
           count as unmet; a portal skips them all)
  escape   the fewest items that walk from the node back to the mainland;
           "ocarina only" when no three items do (the Ocarina always
           warps home from an overworld area, so that is never a trap)
  inside   what the boot kit reaches from the node without leaving it:
           its other nodes, the region pool rows standing there (waves,
           bosses, quests, a region clear's key-item draw) and the ?
           room sites
  kind     TRAP when getting out needs an item, SHORTCUT when only
           getting in does

A portal skips the entry; the escape is what the pocket would have to pay.

    python3 tools/quickstart/portal_pockets.py [--json OUT]
"""
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim as S

BASE = {'ITEM_SMITH_SWORD', 'ITEM_OCARINA'}
ITEMS = [it for it in S.REACH_ITEMS if it not in BASE and it != 'ITEM_SKILL_SPIN_ATTACK']
NAMES = ['SHF', 'SHF@NNE', 'SHF@NNW', 'EH-N', 'EH-C', 'EH-S', 'LLR', 'LLR@E903', 'LLR@E445', 'LLR@E750',
         'LLR@W', 'LLR@NW', 'LLR@N', 'LLR@POCKET', 'NHF', 'NHF@VF', 'CG', 'RV', 'TRIL', 'TRIL@S', 'TRIL@E',
         'TRIL@N', 'WW-N', 'WW-N@W', 'WW-N@S', 'WW-N@E', 'WW-C', 'WW-S', 'CW', 'WR', 'HT', 'CREN', 'MW', 'LH',
         'MV', 'LH-CREST', 'LH-SW', 'LH-LADDER', 'CREN-BASE', 'VF', 'VF@NHF', 'VF@LLR', 'VF@POCKET']
assert len(NAMES) == len(S.NODES)
MAINLAND_DROP = 0   # the South Hyrule Field node


def held(items):
    return S.held_mask(set(items) | BASE)


def flood(seeds, h):
    nodes = 0
    for n in seeds:
        nodes |= 1 << n
    changed = True
    while changed:
        changed = False
        for f, t, terms in S.EDGES:
            if (nodes >> f) & 1 and not (nodes >> t) & 1 and S.terms_met(terms, h):
                nodes |= 1 << t
                changed = True
    return nodes


def members(mask):
    return [i for i in range(len(S.NODES)) if (mask >> i) & 1]


def cheapest(test):
    for k in range(4):
        for combo in itertools.combinations(ITEMS, k):
            if test(held(combo)):
                return list(combo)
    return None


def sites_in(mask, h):
    out = []
    for i, s in enumerate(S.SITES):
        if s['gate'] or S.site_retired(s):
            continue
        if S.reach_room_ok(mask, h, s['area'], s['room']):
            out.append(i)
    return out


def main():
    base = held([])
    mainland = flood([MAINLAND_DROP], base)
    home_sites = set(sites_in(mainland, base))
    rows = []
    for n in range(len(S.NODES)):
        if (mainland >> n) & 1:
            continue
        entry = cheapest(lambda h: (flood([MAINLAND_DROP], h) >> n) & 1)
        escape = cheapest(lambda h: flood([n], h) & mainland)
        inside = flood([n], base)
        pocket_nodes = [m for m in members(inside) if not (mainland >> m) & 1]
        pool = [i for i in range(S.POOL_SIZE) if (inside >> S.POOL_NODE[i]) & 1 and not (mainland >> S.POOL_NODE[i]) & 1]
        sites = [i for i in sites_in(inside, base) if i not in home_sites]
        rows.append(dict(node=n, name=NAMES[n], kind='TRAP' if escape != [] else 'SHORTCUT',
                         entry=entry, escape=escape, pocket=[NAMES[m] for m in pocket_nodes], pool_rows=pool,
                         sites=[[i, S.SITES[i]['roomName'][5:]] for i in sites]))
    short = lambda c: 'items not enough' if c is None else ('+'.join(x[5:].lower() for x in c) or 'free')
    for r in rows:
        esc = 'ocarina only' if r['escape'] is None else short(r['escape'])
        print('%-10s %-8s entry %-30s escape %-22s pocket %s rows %s sites %s' % (
            r['name'], r['kind'], short(r['entry']), esc, r['pocket'], r['pool_rows'],
            ', '.join('%d %s' % tuple(s) for s in r['sites']) or '-'))
    if '--json' in sys.argv:
        json.dump(rows, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
