"""Turn a pile of simulated runs into charts and a report.

Reads the JSON sim.py writes and answers the questions a single playthrough
cannot: which rooms are reachable in almost every run (the ones that will
get stale), which in almost none, which never; which rooms and regions the
win chain leans on to host its requirements; how the reachable world grows
as a run progresses; and what the common and rare shapes of a run are.

Every number here is over BOTH cohorts unless a chart says otherwise - see
sim.py for what strict and rewards mean. Where they disagree the disagreement
is the finding, so the two are drawn together rather than averaged.

    python3 tools/quickstart/sim_report.py --in docs/sim_runs.json \
        --charts docs/sim --md docs/QUICKSTART_SIM_REPORT.md
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# One palette, used everywhere, so the charts read as one document.
INK = '#1c1c1f'
MUTED = '#6b6b76'
GRID = '#e3e3e8'
SERIES = ['#3b6ea5', '#c0603a', '#5b8c5a', '#8a6fa8', '#b58b2a', '#4f8f96']
COHORT_COLOR = {'strict': '#3b6ea5', 'rewards': '#c0603a'}
CKPT = ['after selection', 'after req 1', 'after req 2', 'after req 3', 'after req 4']


def entry_prices(region_names):
    """What it costs to CROSS INTO each region, read back from the reach
    graph the simulator parsed out of reach.h (the entrance-aware model of
    Oct 2026: nodes per (region, entrance), edges with a price each).

    A region's entry price is the OR over every edge that lands on one of
    its nodes from a node of another region. Printed in the report so the
    prices are auditable by someone who knows the world - which is how the
    two wrong ones were caught in the second pass.
    """
    import sim as S
    bits = {v: k[len('QS_REACH_'):].lower() for k, v in S.TOKEN_BITS.items()}
    out = {}
    for ri, rg in enumerate(region_names):
        terms = []
        for frm, to, dnf in S.EDGES:
            if S.NODES[to][0] != ri or S.NODES[frm][0] == ri:
                continue
            for t in dnf:
                if t == S.NEVER:
                    continue
                if t == 0:
                    text = 'free'
                else:
                    text = ' + '.join(bits.get(1 << b, 'bit%d' % b) for b in range(32) if (t >> b) & 1)
                if text not in terms:
                    terms.append(text)
        # drop any term that is a superset of another (the cheaper way wins)
        sets = [frozenset(t.split(' + ')) if t != 'free' else frozenset() for t in terms]
        keep = [terms[k] for k, st in enumerate(sets) if not any(o < st for o in sets)]
        out[rg] = ' or '.join(keep) if keep else 'never (no crossing in; drop only)'
    return out


def style(ax, title=None, xlabel=None, ylabel=None):
    ax.set_facecolor('white')
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8, length=3)
    ax.grid(axis='y', color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, color=INK, fontsize=11, loc='left', pad=10, fontweight='600')
    if xlabel:
        ax.set_xlabel(xlabel, color=MUTED, fontsize=9)
    if ylabel:
        ax.set_ylabel(ylabel, color=MUTED, fontsize=9)


def save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor='white')
    plt.close(fig)
    print('  wrote', path)


def bits(hexstr):
    v = int(hexstr, 16)
    out = []
    i = 0
    while v:
        if v & 1:
            out.append(i)
        v >>= 1
        i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--charts', required=True)
    ap.add_argument('--md', required=True)
    a = ap.parse_args()
    os.makedirs(a.charts, exist_ok=True)
    blob = json.load(open(a.inp))
    meta, runs = blob['meta'], blob['runs']
    ROOMS = meta['room_names']
    ROOM_REGIONS = meta['room_regions']
    REGIONS = meta['region_names']
    RLONG = meta['region_long']
    REGION_SIZE = meta.get('region_size', {})
    ENTRY_PRICE = entry_prices(REGIONS)
    SITE_ROOMS = meta['site_rooms']
    SITE_KINDS = meta['site_kinds']
    POOL_ROOMS = meta['pool_rooms']
    POOL_REGIONS = meta['pool_regions']
    cohorts = meta['cohorts']
    by_cohort = collections.defaultdict(list)
    for r in runs:
        by_cohort[r['cohort']].append(r)
    N = len(by_cohort[cohorts[0]])
    out = {}

    # ---- 1. how the reachable world grows -------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    for ax, key, lab in zip(axes, ('nrooms', 'nregions', 'nsites'),
                            ('rooms', 'regions', '? room sites')):
        for co in cohorts:
            data = [[r['checkpoints'][c][key] for r in by_cohort[co]] for c in range(5)]
            med = [np.median(d) for d in data]
            lo = [np.percentile(d, 10) for d in data]
            hi = [np.percentile(d, 90) for d in data]
            ax.fill_between(range(5), lo, hi, color=COHORT_COLOR[co], alpha=0.16, linewidth=0)
            ax.plot(range(5), med, color=COHORT_COLOR[co], marker='o', ms=4, lw=2, label=co)
        style(ax, f'{lab} reachable', ylabel='count')
        ax.set_xticks(range(5))
        ax.set_xticklabels([c.replace('after ', '') for c in CKPT], rotation=20, ha='right')
        ax.legend(frameon=False, fontsize=8, labelcolor=MUTED)
    fig.suptitle('How much of the world a run can reach, by checkpoint  '
                 '(median, with the 10th-90th percentile band)',
                 color=INK, fontsize=12, x=0.01, ha='left', fontweight='600')
    save(fig, os.path.join(a.charts, '01_growth.png'))

    # ---- 2. region openness heatmap -------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.4))
    for ax, co in zip(axes, cohorts):
        m = np.zeros((len(REGIONS), 5))
        for c in range(5):
            for r in by_cohort[co]:
                reg = r['checkpoints'][c]['regions']
                for i in range(len(REGIONS)):
                    if (reg >> i) & 1:
                        m[i, c] += 1
        m = m / len(by_cohort[co]) * 100
        im = ax.imshow(m, cmap='YlGnBu', vmin=0, vmax=100, aspect='auto')
        ax.set_yticks(range(len(REGIONS)))
        ax.set_yticklabels([RLONG[x] for x in REGIONS], fontsize=8)
        ax.set_xticks(range(5))
        ax.set_xticklabels([c.replace('after ', '') for c in CKPT], rotation=20, ha='right', fontsize=8)
        ax.set_title(f'{co} cohort', color=INK, fontsize=10, loc='left', pad=8, fontweight='600')
        ax.tick_params(colors=MUTED, length=0)
        for i in range(len(REGIONS)):
            for j in range(5):
                ax.text(j, i, f'{m[i, j]:.0f}', ha='center', va='center', fontsize=7,
                        color='white' if m[i, j] > 55 else INK)
        out.setdefault('region_open', {})[co] = m
    fig.suptitle('Percentage of runs in which each region is reachable',
                 color=INK, fontsize=12, x=0.01, ha='left', fontweight='600')
    save(fig, os.path.join(a.charts, '02_region_openness.png'))

    # ---- 2b. ENTERED vs EXPLORABLE --------------------------------------
    #
    # The user's correction, made into a measurement: "We are not simply
    # concerned with whether the player can walk into the entrance of a
    # region but whether or not they can explore the rooms in that region."
    #
    # QuickStartReachableRegions answers the first question and
    # QuickStartReachPoolOk is built on it, so a region whose ENTRY is free
    # but whose interior is priced scores as fully open to the chain while
    # the player stands on the doorstep. Mount Crenel is the case: free to
    # walk into, and everything past the entrance wants the Grip Ring.
    #
    # Left bar: share of runs that can be inside the region at all.
    # Right bar: the median share of that region's own rooms those runs can
    # actually get into. A tall left bar over a short right one is a region
    # the chain believes is open and the player experiences as a wall.
    co = cohorts[0]
    entered, explor = [], []
    for i, rg in enumerate(REGIONS):
        runs_in = [r for r in by_cohort[co]
                   if (r['checkpoints'][4]['regions'] >> i) & 1]
        entered.append(len(runs_in) / len(by_cohort[co]) * 100)
        size = REGION_SIZE.get(rg, 0)
        if runs_in and size:
            fr = [r['checkpoints'][4]['per_region'].get(rg, 0) / size * 100
                  for r in runs_in]
            explor.append(float(np.median(fr)))
        else:
            explor.append(0.0)
    order = np.argsort(-np.array(entered))
    fig, ax = plt.subplots(figsize=(13, 4.6))
    x = np.arange(len(REGIONS))
    ax.bar(x - 0.2, np.array(entered)[order], width=0.38, color=SERIES[0],
           label='runs that can be inside the region')
    ax.bar(x + 0.2, np.array(explor)[order], width=0.38, color=SERIES[1],
           label="median %% of that region's rooms those runs can enter")
    ax.set_xticks(x)
    ax.set_xticklabels([RLONG[REGIONS[i]] for i in order], rotation=28,
                       ha='right', fontsize=8)
    ax.set_ylim(0, 105)
    style(ax, ylabel='% of runs  /  % of rooms')
    ax.legend(frameon=False, fontsize=8, labelcolor=MUTED, loc='lower left')
    fig.suptitle('Entered is not explored  (strict cohort, fourth requirement)',
                 color=INK, fontsize=12, x=0.01, ha='left', fontweight='600')
    save(fig, os.path.join(a.charts, '02b_entered_vs_explored.png'))
    out['entered'] = {REGIONS[i]: entered[i] for i in range(len(REGIONS))}
    out['explorable'] = {REGIONS[i]: explor[i] for i in range(len(REGIONS))}

    # ---- 3. per-room reachability, final checkpoint ---------------------
    freq = {co: np.zeros(len(ROOMS)) for co in cohorts}
    for co in cohorts:
        for r in by_cohort[co]:
            for i in bits(r['checkpoints'][4]['rooms']):
                freq[co][i] += 1
        freq[co] = freq[co] / len(by_cohort[co]) * 100
    order = np.argsort(-freq[cohorts[0]])
    fig, ax = plt.subplots(figsize=(13, 4.2))
    x = np.arange(len(ROOMS))
    ax.bar(x, freq[cohorts[0]][order], color=COHORT_COLOR[cohorts[0]], width=1.0, label=cohorts[0])
    ax.plot(x, freq[cohorts[1]][order], color=COHORT_COLOR[cohorts[1]], lw=1.2, label=cohorts[1])
    style(ax, 'Every room, sorted by how often a run can reach it (at the last checkpoint)',
          xlabel='rooms, most reachable to least', ylabel='% of runs')
    ax.set_xlim(-1, len(ROOMS))
    ax.legend(frameon=False, fontsize=8, labelcolor=MUTED)
    never = int((freq[cohorts[0]] == 0).sum())
    always = int((freq[cohorts[0]] >= 99.5).sum())
    ax.axhline(99.5, color=MUTED, lw=0.8, ls='--')
    ax.text(len(ROOMS) * 0.52, 92, f'{always} rooms reachable in ~every run', fontsize=8, color=MUTED)
    ax.text(len(ROOMS) * 0.52, 6, f'{never} rooms never reachable in any run', fontsize=8, color=MUTED)
    save(fig, os.path.join(a.charts, '03_room_frequency.png'))
    out['freq'] = freq

    # ---- 4. step kinds --------------------------------------------------
    kinds = ['EVENT', 'WAVE', 'BOSS', 'QUEST', 'ITEM']
    fig, axes = plt.subplots(1, 2, figsize=(13, 3.8))
    for ax, co in zip(axes, cohorts):
        counts = {k: [0] * 5 for k in kinds}
        for r in by_cohort[co]:
            for st in r['steps']:
                counts[st['kind']][st['step']] += 1
        bottom = np.zeros(5)
        for k, col in zip(kinds, SERIES):
            v = np.array(counts[k]) / len(by_cohort[co]) * 100
            ax.bar(range(5), v, bottom=bottom, color=col, label=k, width=0.62)
            bottom += v
        style(ax, f'{co} cohort', xlabel='requirement', ylabel='% of runs')
        ax.set_xticks(range(5))
        ax.set_xticklabels(['1st', '2nd', '3rd', '4th', '5th'])
        ax.legend(frameon=False, fontsize=8, labelcolor=MUTED, ncol=5,
                  loc='upper center', bbox_to_anchor=(0.5, -0.22))
        out.setdefault('kinds', {})[co] = counts
    fig.suptitle('What kind of thing each requirement asks for',
                 color=INK, fontsize=12, x=0.01, ha='left', fontweight='600')
    save(fig, os.path.join(a.charts, '04_step_kinds.png'))

    # ---- 5. which regions host requirements -----------------------------
    host = {co: collections.Counter() for co in cohorts}
    host_room = {co: collections.Counter() for co in cohorts}
    site_host = {co: collections.Counter() for co in cohorts}
    for co in cohorts:
        for r in by_cohort[co]:
            for st in r['steps']:
                if st['kind'] in ('WAVE', 'BOSS', 'QUEST'):
                    host[co][POOL_REGIONS[st['where']]] += 1
                    host_room[co][POOL_ROOMS[st['where']]] += 1
                elif st['kind'] == 'EVENT':
                    host[co][(ROOM_REGIONS[0] or ['?'])[0]
                             if False else _site_region(SITE_ROOMS[st['where']], ROOMS, ROOM_REGIONS)] += 1
                    host_room[co][SITE_ROOMS[st['where']]] += 1
                    site_host[co][st['where']] += 1
    fig, ax = plt.subplots(figsize=(13, 4.0))
    xs = np.arange(len(REGIONS))
    w = 0.38
    for i, co in enumerate(cohorts):
        tot = sum(host[co].values()) or 1
        ax.bar(xs + (i - 0.5) * w, [host[co].get(rg, 0) / tot * 100 for rg in REGIONS],
               width=w, color=COHORT_COLOR[co], label=co)
    style(ax, 'Where the win chain puts its requirements',
          ylabel='% of all placed requirements')
    ax.set_xticks(xs)
    ax.set_xticklabels([RLONG[x] for x in REGIONS], rotation=28, ha='right', fontsize=8)
    ax.legend(frameon=False, fontsize=8, labelcolor=MUTED)
    save(fig, os.path.join(a.charts, '05_host_regions.png'))
    out['host'], out['host_room'], out['site_host'] = host, host_room, site_host

    # ---- 6. drop region vs element region -------------------------------
    fig, ax = plt.subplots(figsize=(8.2, 6.2))
    m = np.zeros((len(REGIONS), len(REGIONS)))
    for r in runs:
        m[REGIONS.index(r['drop_region']), REGIONS.index(r['element_region'])] += 1
    m = m / len(runs) * 100
    im = ax.imshow(m, cmap='YlGnBu', aspect='auto')
    ax.set_xticks(range(len(REGIONS)))
    ax.set_xticklabels([RLONG[x] for x in REGIONS], rotation=40, ha='right', fontsize=8)
    ax.set_yticks(range(len(REGIONS)))
    ax.set_yticklabels([RLONG[x] for x in REGIONS], fontsize=8)
    ax.tick_params(colors=MUTED, length=0)
    ax.set_title('Where a run lands, and where its Earth Element ends up\n'
                 '(% of all runs; the element is drawn within two regions of the drop)',
                 color=INK, fontsize=11, loc='left', pad=12, fontweight='600')
    ax.set_xlabel('element region', color=MUTED, fontsize=9)
    ax.set_ylabel('drop region', color=MUTED, fontsize=9)
    fig.colorbar(im, ax=ax, shrink=0.75).ax.tick_params(colors=MUTED, labelsize=8)
    save(fig, os.path.join(a.charts, '06_drop_element.png'))
    out['drop_element'] = m

    # ---- 7. site usage --------------------------------------------------
    site_reach = np.zeros(len(SITE_ROOMS))
    for r in runs:
        for i in bits(r['checkpoints'][4]['sites']):
            site_reach[i] += 1
    site_reach = site_reach / len(runs) * 100
    site_used = np.zeros(len(SITE_ROOMS))
    for co in cohorts:
        for i, n in site_host[co].items():
            site_used[i] += n
    site_used = site_used / len(runs) * 100
    fig, ax = plt.subplots(figsize=(13, 4.2))
    o = np.argsort(-site_reach)
    ax.bar(np.arange(len(SITE_ROOMS)), site_reach[o], color='#3b6ea5', width=1.0,
           label='reachable at the last checkpoint')
    ax.plot(np.arange(len(SITE_ROOMS)), site_used[o] * 10, color='#c0603a', lw=1.3,
            label='hosted a requirement (x10 for scale)')
    style(ax, '? room sites: how often each one is reachable, and how often the chain uses it',
          xlabel='the 105 content sites, most reachable to least', ylabel='% of runs')
    ax.set_xlim(-1, len(SITE_ROOMS))
    ax.legend(frameon=False, fontsize=8, labelcolor=MUTED)
    save(fig, os.path.join(a.charts, '07_sites.png'))
    out['site_reach'], out['site_used'] = site_reach, site_used

    # ---- 8. pathways ----------------------------------------------------
    paths = collections.Counter()
    for r in runs:
        seq = []
        for st in r['steps']:
            if st['kind'] == 'ITEM':
                seq.append('·')
            elif st['kind'] == 'EVENT':
                seq.append(_site_region(SITE_ROOMS[st['where']], ROOMS, ROOM_REGIONS))
            else:
                seq.append(POOL_REGIONS[st['where']])
        paths[' → '.join(seq)] += 1
    top = paths.most_common(18)
    fig, ax = plt.subplots(figsize=(13, 5.4))
    ys = np.arange(len(top))
    ax.barh(ys, [c / len(runs) * 100 for _, c in top], color='#3b6ea5', height=0.7)
    ax.set_yticks(ys)
    ax.set_yticklabels([p for p, _ in top], fontsize=7.5, family='monospace')
    ax.invert_yaxis()
    style(ax, 'The most common shapes a run takes  (region of each requirement in order; · = a "hold an item" step)',
          xlabel='% of runs')
    ax.grid(axis='x', color=GRID, linewidth=0.7)
    ax.grid(axis='y', visible=False)
    save(fig, os.path.join(a.charts, '08_pathways.png'))
    out['paths'] = paths

    # ---- 9. how far from the drop a run gets --------------------------
    import sim as S
    dist = {}
    for src in range(len(REGIONS)):
        d = {src: 0}
        q = collections.deque([src])
        while q:
            u = q.popleft()
            for v in range(len(REGIONS)):
                if (S.ADJACENCY[u] >> v) & 1 and v not in d:
                    d[v] = d[u] + 1
                    q.append(v)
        dist[src] = d
    fig, ax = plt.subplots(figsize=(11, 3.8))
    for co in cohorts:
        rows = []
        for c in range(5):
            far = []
            for r in by_cohort[co]:
                src = REGIONS.index(r['drop_region'])
                reg = r['checkpoints'][c]['regions']
                far.append(max((dist[src].get(i, 0) for i in range(len(REGIONS))
                                if (reg >> i) & 1), default=0))
            rows.append(far)
        ax.plot(range(5), [np.mean(x) for x in rows], marker='o', ms=4, lw=2,
                color=COHORT_COLOR[co], label=co)
    style(ax, 'How far from the landing a run can get, in region hops',
          ylabel='mean distance to the farthest reachable region')
    ax.set_xticks(range(5))
    ax.set_xticklabels([c.replace('after ', '') for c in CKPT], rotation=20, ha='right')
    ax.legend(frameon=False, fontsize=8, labelcolor=MUTED)
    save(fig, os.path.join(a.charts, '09_distance.png'))
    out['dist'] = dist

    # ---- root causes for the rooms the model never counts --------------
    gettable = 0
    for it in set(S.KEY_ITEMS) | S.BOOT_ITEMS | {'ITEM_SKILL_SPIN_ATTACK'}:
        gettable |= S.ITEM_TO_BIT.get(it, 0)
    gettable |= S.TOKEN_BITS['QS_REACH_FUSION']
    # The golden gates (Oct 2026): held when the run rolled them open, so a
    # room priced at one is affordable in half the runs.
    gettable |= S.TOKEN_BITS['QS_REACH_SOURCE_FLOW'] | S.TOKEN_BITS['QS_REACH_STATUES']
    tokname = {v: k[len('QS_REACH_'):] for k, v in S.TOKEN_BITS.items()}
    causes = collections.defaultdict(list)
    for i in range(len(ROOMS)):
        if any(out['freq'][co][i] > 0 for co in cohorts):
            continue
        area, room, _, _ = S.ALL_ROOMS[i]
        rows = [t for (_, da, dro, t, _, _) in S.DESTS if da == area and dro == room]
        if not rows:
            causes['no row in the survey at all'].append(ROOMS[i])
            continue
        blockers, affordable = set(), False
        for terms in rows:
            for t in terms:
                if t == S.NEVER:
                    continue
                miss = t & ~gettable
                if miss == 0:
                    affordable = True
                else:
                    for b, n in tokname.items():
                        if miss & b:
                            blockers.add(n)
        if affordable:
            causes['the room is affordable but its region never opens'].append(ROOMS[i])
        elif not blockers:
            causes['every route is priced "never" in the survey'].append(ROOMS[i])
        else:
            soft = blockers & {'MINISH', 'STORY', 'MAZE', 'SWITCHES4', 'UNSURVEYED'}
            rocks = {b for b in blockers if b.startswith('BOULDER_')}
            if soft:
                causes['needs a token with no run-time test: ' + ', '.join(sorted(soft))].append(ROOMS[i])
            elif rocks:
                causes['behind a boulder the model never pushes (testable in play): ' + ', '.join(sorted(rocks))].append(ROOMS[i])
            else:
                causes['needs an item no run can be given: ' + ', '.join(sorted(blockers))].append(ROOMS[i])
    out['causes'] = causes

    dupq = sum(1 for r in runs if sum(1 for s in r['steps'] if s['kind'] == 'QUEST') > 1)
    out['dupquest'] = dupq

    _write_md(a, meta, runs, by_cohort, cohorts, out, ROOMS, ROOM_REGIONS,
              REGIONS, RLONG, SITE_ROOMS, SITE_KINDS, POOL_ROOMS, POOL_REGIONS,
              ENTRY_PRICE)
    return 0


def _site_region(site_room, rooms, room_regions):
    try:
        i = rooms.index(site_room)
    except ValueError:
        return '?'
    rs = room_regions[i]
    return rs[0] if rs else '?'


def _write_md(a, meta, runs, by_cohort, cohorts, out, ROOMS, ROOM_REGIONS,
              REGIONS, RLONG, SITE_ROOMS, SITE_KINDS, POOL_ROOMS, POOL_REGIONS,
              ENTRY_PRICE):
    freq = out['freq']
    L = []
    W = L.append
    N = len(by_cohort[cohorts[0]])
    W(f'# What {len(runs):,} simulated runs say about this game\n')
    W(f'{len(runs):,} runs - {N:,} in each of two loadout cohorts - played through the '
      'three hub selection rounds and all five Earth Element requirements, '
      'with reachability measured at five checkpoints.\n')
    W('Generated by `tools/quickstart/sim_report.py` from `tools/quickstart/sim.py`. '
      'The reach model is validated against the shipped ROM by '
      '`tools/quickstart/sim_validate.py` - 402 of 402 random cases agree.\n')

    kindtot = collections.Counter()
    for r in runs:
        for st in r['steps']:
            kindtot[st['kind']] += 1
    _h = out['host'][cohorts[0]]
    out['host_share'] = {r: _h.get(r, 0) / max(1, sum(_h.values())) * 100 for r in REGIONS}
    # ---- the third pass's own numbers --------------------------------------
    import sim as S
    strict0 = np.mean([r['checkpoints'][0]['nrooms'] for r in by_cohort['strict']])
    strict4 = np.mean([r['checkpoints'][4]['nrooms'] for r in by_cohort['strict']])
    rw0 = np.mean([r['checkpoints'][0]['nrooms'] for r in by_cohort['rewards']])
    rw4 = np.mean([r['checkpoints'][4]['nrooms'] for r in by_cohort['rewards']])
    def _gates(seed):
        o = set(); S.roll_gates(seed, o)
        return ('GATE_FLOW_OPEN' in o, 'GATE_STATUES_OPEN' in o)
    rw = by_cohort['rewards']; st_ = by_cohort['strict']
    keyed = collections.Counter(st['detail'] for r in rw for st in r['steps']
                                if st['kind'] == 'ITEM' and st['detail'])
    item_runs = sum(1 for r in st_ if any(x['kind'] == 'ITEM' for x in r['steps'])) / len(st_) * 100
    ranch_runs = sum(1 for r in st_ if any(x['kind'] == 'EVENT' and 'RANCH_HOUSE' in SITE_ROOMS[x['where']]
                                          for x in r['steps'])) / len(st_) * 100
    sealed_flow = sum(1 for r in rw if not _gates(r['seed'])[0]) / len(rw) * 100
    sealed_stat = sum(1 for r in rw if not _gates(r['seed'])[1]) / len(rw) * 100
    vf_drop = sum(1 for r in runs if r['drop_region'] == 'VF') / len(runs) * 100
    wr_drop = sum(1 for r in runs if r['drop_region'] == 'WR') / len(runs) * 100
    vf_drop_sealed = sum(1 for r in runs if r['drop_region'] == 'VF' and not _gates(r['seed'])[0])
    wr_drop_sealed = sum(1 for r in runs if r['drop_region'] == 'WR' and not _gates(r['seed'])[1])
    vf_elem_sealed = sum(1 for r in runs if r['element_region'] == 'VF' and not _gates(r['seed'])[0])
    wr_elem_sealed = sum(1 for r in runs if r['element_region'] == 'WR' and not _gates(r['seed'])[1])
    pieces = collections.Counter(it for r in rw for it in r.get('rewards', []) if str(it).startswith('QUICKSTART'))
    drop_share = collections.Counter(r['drop_region'] for r in runs)
    never_strict = int((freq['strict'] == 0).sum())
    never_both = sum(len(v) for v in out['causes'].values())
    W('\n## Headline findings\n')
    W('This is the THIRD pass (Oct 2026). Since the second: the reach model became '
      'entrance-aware (a node per (region, entrance), boulders as live tokens the player pushes), '
      'Veil Falls joined as the fourteenth region, and the two golden-kinstone gates were added. '
      'The first two passes\' errors stay on the record below ("What the first pass got wrong"); '
      'this pass adds one of its own, caught before publication: the checkpoint code handed the '
      'room test a REGION mask where it wanted a NODE mask, so the first sweep of this data counted '
      'about 10 rooms per run and 161 rooms never reached. Fixed in `sim.py`; these are the '
      're-run numbers.\n')
    W(f'**1. The reachable world is smaller than the second pass said, and the reason is the '
      f'model, not the game.** A run holds ONE key item out of the hub (round 1 draws one `QS_CAT_KEY` '
      f'row) plus the sword and the ocarina. Against the entrance-aware table that opens a median '
      f'{np.median([r["checkpoints"][0]["nrooms"] for r in st_]):.0f} of {len(ROOMS)} rooms, where the '
      'second pass reported 59 of 164: the old table let any node of a region reach any other for '
      'free and priced every boulder as pushed. The strict cohort then stays flat '
      f'({strict0:.1f} to {strict4:.1f} rooms), and the rewards cohort grows to {rw4:.1f} by the fourth '
      'requirement. Growth still comes from the region-clear draw, as before.\n')
    W(f'**2. The keyed pair, after the rebalance.** The pair is rolled one step in '
      f'{S.PAIR_MOD} and asks about ONE key per roll, round-robin from the step index '
      '(`QuickStartChainRollKeyedPair`; it used to try all four and let the first eligible one '
      'win, which was the Lon Lon key 95% of the time, put an ITEM step in 40% of runs and sent '
      f'49% of runs to the ranch house). Now {item_runs:.0f}% of runs carry an ITEM step and '
      f'{ranch_runs:.0f}% visit the ranch house - the house is also an ordinary ? room site, which '
      f'is where the rest of that figure comes from. Keyed deals over {len(rw):,} rewards runs: '
      f'Lon Lon key {keyed.get("ITEM_QST_LONLON_KEY", 0):,}, graveyard key '
      f'{keyed.get("ITEM_QST_GRAVEYARD_KEY", 0):,}, the Source of the Flow piece '
      f'{keyed.get("QUICKSTART_ITEM_GOLD_FLOW", 0)}, the statue set {keyed.get("QUICKSTART_ITEM_GOLD_STATUES", 0)}. '
      'The Lon Lon key still leads because it is eligible far more often (its regions are always '
      'reached, its sealed sites always open with it); the others are limited by eligibility, not '
      'by the roll.\n')
    W(f'**3. Drops and elements follow the pool rows, not the regions.** Eastern Hills and Western '
      f'Wood have three pool rows each, so they take {drop_share["EH"]/len(runs)*100:.0f}% and '
      f'{drop_share["WW"]/len(runs)*100:.0f}% of all drops and about a third of all placed '
      'requirements between them; a one-row region takes 6-7%. Lake Hylia takes '
      f'{drop_share["LH"]/len(runs)*100:.1f}% (the flippers kit), Castor Wilds and the Ruins about 1% '
      '(the swamp kit), Veil Falls '
      f'{vf_drop:.1f}% (half the runs seal its gate). If the intent is "any region, evenly", the drop '
      'should be drawn over regions and then over that region\'s rows.\n')
    W(f'**4. The golden gates behave as designed, and the chain barely uses them.** The stone seals '
      f'in {sealed_flow:.0f}% of runs and the statues in {sealed_stat:.0f}%; no drop and no element ever '
      f'landed behind a sealed gate ({vf_drop_sealed + wr_drop_sealed} drops, {vf_elem_sealed + wr_elem_sealed} '
      f'elements). The chain dealt the flow piece as a keyed pair {keyed.get("QUICKSTART_ITEM_GOLD_FLOW", 0)} '
      f'times and the statue set never, because the falls\' sites want the bombs and the lantern held at '
      'roll time and the Ruins want a Castor boulder pushed, which this model never does. The pieces '
      f'came out of region-clear draws {sum(pieces.values())} times in {len(rw):,} runs. In play the '
      'statue pair is live the moment a boulder is pushed; in this model the gates are mostly a '
      'drop filter.\n')
    W(f'**5. Four regions are nearly dead content.** Entered at the fourth requirement: Royal Valley '
      f'{out["entered"].get("RV", 0):.0f}%, Lake Hylia {out["entered"].get("LH", 0):.0f}%, the Wind Ruins '
      f'{out["entered"].get("WR", 0):.0f}%, Veil Falls {out["entered"].get("VF", 0):.0f}% (and that is '
      'mostly the Lon Lon strip, one room). They host '
      f'{out["host_share"].get("RV", 0):.1f}%, {out["host_share"].get("LH", 0):.1f}%, '
      f'{out["host_share"].get("WR", 0):.1f}% and {out["host_share"].get("VF", 0):.1f}% of placed '
      'requirements. Castor Wilds is the opposite failure: entered in 98% of runs (its border from '
      'the Western Wood is free) and a median 0% of its rooms explorable, because everything inside '
      'is swamp priced at the boots or the cape.\n')
    W(f'**6. {never_strict} rooms are never reached by a strict run and {never_both} by any run.** '
      'The strict number is the one-key-item start: anything priced at two items or at a fusion is '
      'out until the region clears pay. The nine that no loadout reaches are structural and listed '
      'below with their cause: the Wind Ruins\' three rooms (the pool row\'s own room has no survey '
      'row, the other two are priced "never"), the Goron cave behind Lon Lon\'s boulder 2, the two '
      'unsurveyed Minish Woods rooms, and two rooms whose price no run assembled in 50,000 tries '
      '(Mount Crenel\'s dig cave; the falls\' heart-piece nook, four items and a fusion). '
      f'{int((out["site_reach"] == 0).sum())} of {len(SITE_ROOMS)} ? room sites are never reachable, '
      'four of them Mount Crenel caves whose rooms have no survey row at all.\n')

    W('\n## The two cohorts\n')
    W('| cohort | what the player is assumed to hold |\n|---|---|')
    W('| `strict` | the three hub picks, plus whatever the chain\'s own ITEM steps hand over. '
      'This is exactly what the placer sees, and a floor for reach. |')
    W('| `rewards` | the same, plus the actual region clear reward on every WAVE and BOSS '
      'step, drawn the way `QuickStartSpawnRegionRewardItem` draws it - '
      '`QuickStartDrawItem(Random() & 0x3f, QS_CAT_ALL)`, modelled over all 64 equiprobable '
      'seeds with the real tier curve and the real usability tests. Plus the fusion bit after '
      'the first clear. |')
    W('\nThe truth is between them, and much nearer `rewards`: a player who finishes five '
      'requirements has cleared regions, and a region clear pays out. `strict` is kept because '
      'it is exactly what the placer would see if the player picked up nothing, which makes it '
      'the honest floor.\n')
    W('\nEVENT and QUEST steps are deliberately NOT modelled as growth. A "? room" pays '
      '`QS_CAT_DROP`, which excludes key items by construction, and a quest pays its own table; '
      'neither can move the reach mask.\n')

    W('\n## Reachability\n')
    W('![growth](sim/01_growth.png)\n')
    for co in cohorts:
        first = [r['checkpoints'][0]['nrooms'] for r in by_cohort[co]]
        last = [r['checkpoints'][4]['nrooms'] for r in by_cohort[co]]
        W(f'- **{co}**: median {np.median(first):.0f} of {len(ROOMS)} rooms reachable after the '
          f'item selection, {np.median(last):.0f} by the fourth requirement '
          f'(10th-90th percentile {np.percentile(last,10):.0f}-{np.percentile(last,90):.0f}).')
    W('\n![regions](sim/02_region_openness.png)\n')

    W('\n### What the model now believes a region costs to enter\n')
    W('Read off the entrance-aware graph: the cheapest edge from another region\'s node onto any '
      'node of this one. "Free" means SOME entrance is free - Veil Falls\' Lon Lon strip, Castor '
      'Wilds\' Western Wood border - not that the region is open; see "Entered is not explored" '
      'for what the inside costs. Two of these were wrong in the first pass and were caught by a '
      'reader, so the whole table stays printed for audit.\n')
    W('| region | entry price | reachable in |\n|---|---|---|')
    for r in REGIONS:
        W(f'| {RLONG[r]} | `{ENTRY_PRICE.get(r, "?")}` | {out["entered"].get(r, 0):.0f}% of runs |')
    W('')

    W('\n### Entered is not explored\n')
    W('The measure above asks whether a run can be INSIDE a region. That is also the only '
      'question `QuickStartReachPoolOk` asks, which means it is the question the chain uses when '
      'it decides where a WAVE or a BOSS step may go. It is not the same as how much of the '
      'region the player can walk.\n')
    W('![entered](sim/02b_entered_vs_explored.png)\n')
    gaps = sorted(((out['entered'][r] - out['explorable'][r], r) for r in REGIONS
                   if out['entered'][r] > 25), reverse=True)[:6]
    W('| region | runs that can be inside it | median share of its rooms they can enter |'
      '\n|---|---|---|')
    for _g, r in gaps:
        W(f'| {RLONG[r]} | {out["entered"][r]:.0f}% | {out["explorable"][r]:.0f}% |')
    W('\nOne caveat before reading those numbers as gameplay, because the first pass of this '
      'report made exactly that mistake: the denominator is every room the survey attributes to '
      'the region, and a large share of those are Minish cracks and Minish houses that the '
      'reach model can never count (see "Rooms the reach model never counts"). So a low '
      'explorable share is partly a statement about the region and partly a statement about the '
      '`MINISH` token. North Hyrule Field is the clearest case of the second kind. Mount Crenel '
      'is the clearest case of the first: its interior is priced at the Grip Ring, which the '
      'model CAN test, so its gap is real.\n')
    W('\nThe widest gaps are regions the chain treats as open and the player experiences as a '
      'doorstep. Mount Crenel is the designed example - free to walk into, Grip Ring for '
      'everything past the entrance - and it is worth deciding whether a wave or a boss placed '
      '"in Mount Crenel" should have to be placed somewhere the player can actually stand, or '
      'whether the entrance strip is enough (for a wave, which spawns around the player, it '
      'probably is; for a boss, which spawns at the region\'s fixed reward spot, it matters).\n')

    W('![rooms](sim/03_room_frequency.png)\n')

    strict = freq[cohorts[0]]
    both_never = [ROOMS[i] for i in range(len(ROOMS))
                  if all(freq[co][i] == 0 for co in cohorts)]
    W(f'\n### Rooms the reach model never counts ({len(both_never)} of {len(ROOMS)})\n')
    W('**Read this carefully, because the obvious reading is wrong.** These rooms are not '
      'sealed off in the world - a player can walk into most of them. What is true is that '
      '`QuickStartReachRoomOk` never returns TRUE for them under any loadout a run can '
      'assemble, which means the win chain can never place a requirement in one and the '
      'mode believes they are out of reach. That is a large fraction of the built world '
      'that the run structure cannot use.\n')
    W('\n#### Why, grouped by cause\n')
    W('| rooms | cause |\n|---|---|')
    for cause, names in sorted(out['causes'].items(), key=lambda kv: -len(kv[1])):
        W(f'| **{len(names)}** | {cause} |')
    W('\n- **`MINISH` has no run-time test** and is now the single largest cause. Being Minish '
      'is a state, not an inventory item, so `QuickStartHeldReachMask` can never set the bit '
      'and every term containing it is permanently false. That is a deliberate conservative '
      'choice in the reach model; the cost of it, measured here, is that a large block of rooms '
      'is invisible to the chain even though the player has a Minish Cap and the portals work. '
      'It is the one remaining decision that would move this number materially.')
    W('- **Bombs used to be the other big cause, and are not any more.** They were '
      '`QS_CAT_WEAPON` only, so neither hub round 1 (which draws `QS_CAT_KEY`) nor a chain ITEM '
      'step could ever hand them over, and fourteen bomb-priced rooms - the whole of Mount '
      "Crenel's base among them - sat outside the chain's reach for the life of a run. The row "
      'is `QS_CAT_WEAPON | QS_CAT_KEY` now: bombs stay a weapon for the shop and the "? room" '
      'drop pool and are a key item everywhere reach is decided. This run is measured with that '
      'change in.')
    W('\n<details><summary>All of them</summary>\n')
    W('\n| room | region |\n|---|---|')
    for nm in sorted(both_never):
        i = ROOMS.index(nm)
        W(f'| `{nm}` | {", ".join(ROOM_REGIONS[i]) or "-"} |')
    W('\n</details>\n')

    order = np.argsort(-strict)
    W('\n### The 15 most reachable rooms - the staleness watchlist\n')
    W('| room | strict | rewards |\n|---|---|---|')
    for i in order[:15]:
        W(f'| `{ROOMS[i]}` | {strict[i]:.1f}% | {freq[cohorts[1]][i]:.1f}% |')
    rare = [i for i in order if strict[i] > 0][-15:]
    W('\n### The 15 rarest rooms that are reachable at all\n')
    W('| room | strict | rewards |\n|---|---|---|')
    for i in rare:
        W(f'| `{ROOMS[i]}` | {strict[i]:.2f}% | {freq[cohorts[1]][i]:.2f}% |')

    W('\n## What the chain asks for, and where\n')
    W('![kinds](sim/04_step_kinds.png)\n')
    W('![hosts](sim/05_host_regions.png)\n')
    hosts = out['host']
    W('\n| region | % of placed requirements (strict) | (rewards) |\n|---|---|---|')
    tot = {co: sum(hosts[co].values()) or 1 for co in cohorts}
    for rg in sorted(REGIONS, key=lambda r: -hosts[cohorts[0]].get(r, 0)):
        W(f'| {RLONG[rg]} | {hosts[cohorts[0]].get(rg,0)/tot[cohorts[0]]*100:.1f}% '
          f'| {hosts[cohorts[1]].get(rg,0)/tot[cohorts[1]]*100:.1f}% |')

    hr = collections.Counter()
    for co in cohorts:
        hr.update(out['host_room'][co])
    W('\n### The 15 rooms that host requirements most often\n')
    W('| room | share of all placed requirements |\n|---|---|')
    tt = sum(hr.values()) or 1
    for nm, c in hr.most_common(15):
        W(f'| `{nm}` | {c/tt*100:.2f}% |')

    W('\n![drop](sim/06_drop_element.png)\n')
    W('\n## ? room sites\n')
    W('![sites](sim/07_sites.png)\n')
    sr, su = out['site_reach'], out['site_used']
    never_site = [i for i in range(len(SITE_ROOMS)) if sr[i] == 0]
    never_used = [i for i in range(len(SITE_ROOMS)) if su[i] == 0]
    W(f'- {len(never_site)} of {len(SITE_ROOMS)} sites were never reachable in any run.')
    W(f'- {len(never_used)} were never chosen to host a requirement.')
    if never_site:
        W('\n**Never reachable:**\n')
        W('| site | room | kind class |\n|---|---|---|')
        for i in never_site:
            W(f'| {i} | `{SITE_ROOMS[i]}` | {SITE_KINDS[i]} |')
    W('\n### The 12 sites the chain leans on most\n')
    W('| site | room | reachable | hosted |\n|---|---|---|---|')
    for i in np.argsort(-su)[:12]:
        W(f'| {i} | `{SITE_ROOMS[i]}` | {sr[i]:.1f}% | {su[i]:.2f}% |')

    W('\n![distance](sim/09_distance.png)\n')

    W('\n## The bug this turned up, and its fix\n')
    W('The first pass measured **15,827 of 50,000 runs (31.7%)** being dealt the side quest as '
      'TWO separate requirements. There is only one quest per run, so the second copy was '
      'already satisfied the moment it was dealt and the run silently lost one of its five '
      'steps. The cause was a two-line mismatch in `QuickStartChainRollStep`\'s helpers:\n')
    W('```c\n'
      '// the guard asked whether where == 0 ...\n'
      '!QuickStartChainAlreadyUsed(step, QS_CHAIN_QUEST, 0)\n\n'
      '// ... but the store writes the pool row, which is 0 in only 1 case of 18\n'
      'gSave.chain_where[step] = (u8)QuickStartQuestSlot();\n'
      '```\n')
    W('The simulation agreed exactly with that reading: of the 15,827 duplicate runs, **zero** '
      'had a quest slot of 0. The comment above the guard reads "One quest per run", so the '
      'intent was never in doubt.\n')
    W('The guard now asks about `(u8)QuickStartQuestSlot()`. Over this run of '
      f'{len(runs):,} the simulator, carrying the same fix, reports **{out["dupquest"]}** '
      'duplicate-quest runs.\n')

    W('\n## What the first pass got wrong\n')
    W('Three of the four headline findings in the first version of this report were wrong or '
      'badly overstated, and all three were caught by the user reading them rather than by the '
      'tooling. They are recorded here because the failure mode is worth keeping: in each case '
      'the simulation faithfully reproduced what the code does, and the error was in what the '
      'measurement was taken to MEAN.\n')
    W('| the claim | why it was wrong |\n|---|---|')
    W('| "The reachable world does not grow." | It does. Every WAVE and BOSS step is a region '
      'clear, and `QuickStartSpawnRegionRewardItem` draws over `QS_CAT_ALL`, key items included. '
      'The chain rolls one step at a time off the live inventory, so the placer sees those '
      'grants. What the first pass measured was a cohort defined to pick nothing up; its '
      'flatness was a tautology, not a finding. The reward draw is now modelled exactly. |')
    W('| "Castle Garden is reachable in 7% of runs." | True as measured, and the measurement '
      'was of a data gap, not of the world. Castle Garden had no survey block, so it was priced '
      '"never" and only a run that DROPPED there ever saw it. The crossing from North Hyrule '
      'Field is a plain border with no gate. |')
    W('| "Royal Valley and Mount Crenel are reachable in 100% of runs." | Royal Valley was '
      'priced FREE when its only crossing wants bombs and the Power Bracelets. Mount Crenel is '
      'genuinely free to ENTER, but the number was reported as if it meant the region was open, '
      'when everything past the entrance is priced at the Grip Ring. Both are now measured '
      'properly - the first as a corrected entry price, the second with a separate '
      'explorability measure. |')
    W('\nThe common root of the two pricing errors: `gen_reach` built the region entry table '
      'from each region\'s own `room_req`, which is the cost of moving around INSIDE a region. '
      'For a region whose entry price is recorded as an exit row in its NEIGHBOUR\'s survey '
      'block, that price was never read. `world_reach.ENTRY` now states crossings directly.\n')

    W('\n## The shape of a run\n')
    W('![paths](sim/08_pathways.png)\n')
    paths = out['paths']
    W(f'- {len(paths):,} distinct requirement-region sequences across {len(runs):,} runs.')
    W(f'- the most common accounts for {paths.most_common(1)[0][1]/len(runs)*100:.2f}% of runs.')
    singles = sum(1 for _, c in paths.items() if c == 1)
    W(f'- {singles:,} sequences occurred exactly once.')

    W('\n## Appendix: what is modelled, and what is a distribution\n')
    W('Two systems key off the live RNG stream rather than the run seed, so no seed-driven '
      'model can say what a particular run gets. For those this reports the distribution '
      'the tables deal, which is the honest form of "what can be encountered".\n')
    W('\n### ? room kinds, in sixteenths\n')
    W("A site's kind class decides which draw it uses. Read off the switch statements in "
      '`QuickStartPickSmallKind` and friends.\n')
    W('\n| class | WAVES | MINIBOSS | NPC | POT_LOTTERY | GATE | FAIRY |\n|---|---|---|---|---|---|---|')
    W('| SMALL | 7 | - | 3 | 3 | - | 1 |')
    W('| LARGE | 7 | 6 | - | - | 2 | 1 |')
    W('| ANY | 4 | 5 | 2 | 1 | 3 | 1 |')
    kindcount = collections.Counter(SITE_KINDS)
    W('\nSite classes in the table: ' +
      ', '.join(f'{k} x{v}' for k, v in sorted(kindcount.items(), key=lambda kv: -kv[1])) + '.\n')
    W('\n### Enemy rosters\n')
    W("Wave composition is an archetype roll cast from the difficulty tier's roster, so what "
      'a given wave contains is a live-RNG question. What IS fixed is the roster each tier '
      'draws from:\n')
    W('\n| level | distinct enemies |\n|---|---|')
    for lv, n in (('1', 10), ('2', 15), ('3', 17), ('4', 12), ('5', 11)):
        W(f'| {lv} | {n} |')
    W('\nA difficulty-3 run - the shipped build - draws mostly from levels 1-3, so roughly '
      'forty distinct enemy kinds are in play across a run, and the mix inside a wave is '
      'shaped by the archetype roll rather than picked flat.\n')

    open(a.md, 'w').write('\n'.join(L) + '\n')
    print('  wrote', a.md)


if __name__ == '__main__':
    sys.exit(main())
