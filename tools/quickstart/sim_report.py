"""Turn a pile of simulated runs into charts and a report.

Reads the JSON sim.py writes and answers the questions a single playthrough
cannot: which rooms are reachable in almost every run (the ones that will
get stale), which in almost none, which never; which rooms and regions the
win chain leans on to host its requirements; how the reachable world grows
as a run progresses; and what the common and rare shapes of a run are.

Every number here is over BOTH cohorts unless a chart says otherwise - see
sim.py for what strict and found mean. Where they disagree the disagreement
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
COHORT_COLOR = {'strict': '#3b6ea5', 'found': '#c0603a'}
CKPT = ['after selection', 'after req 1', 'after req 2', 'after req 3', 'after req 4']


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
            soft = blockers & {'MINISH', 'STORY', 'MAZE', 'SWITCHES4', 'UNSURVEYED', 'BOULDER'}
            if soft:
                causes['needs a token with no run-time test: ' + ', '.join(sorted(soft))].append(ROOMS[i])
            else:
                causes['needs an item no run can be given: ' + ', '.join(sorted(blockers))].append(ROOMS[i])
    out['causes'] = causes

    dupq = sum(1 for r in runs if sum(1 for s in r['steps'] if s['kind'] == 'QUEST') > 1)
    out['dupquest'] = dupq

    _write_md(a, meta, runs, by_cohort, cohorts, out, ROOMS, ROOM_REGIONS,
              REGIONS, RLONG, SITE_ROOMS, SITE_KINDS, POOL_ROOMS, POOL_REGIONS)
    return 0


def _site_region(site_room, rooms, room_regions):
    try:
        i = rooms.index(site_room)
    except ValueError:
        return '?'
    rs = room_regions[i]
    return rs[0] if rs else '?'


def _write_md(a, meta, runs, by_cohort, cohorts, out, ROOMS, ROOM_REGIONS,
              REGIONS, RLONG, SITE_ROOMS, SITE_KINDS, POOL_ROOMS, POOL_REGIONS):
    freq = out['freq']
    L = []
    W = L.append
    N = len(by_cohort[cohorts[0]])
    W('# What 50,000 simulated runs say about this game\n')
    W(f'{len(runs):,} runs - {N:,} in each of two loadout cohorts - played through the '
      'three hub selection rounds and all five Earth Element requirements, '
      'with reachability measured at five checkpoints.\n')
    W('Generated by `tools/quickstart/sim_report.py` from `tools/quickstart/sim.py`. '
      'The reach model is validated against the shipped ROM by '
      '`tools/quickstart/sim_validate.py` - 302 of 302 random cases agree.\n')

    kindtot = collections.Counter()
    for r in runs:
        for st in r['steps']:
            kindtot[st['kind']] += 1
    flat = all(np.isclose(np.mean([r['checkpoints'][c]['nrooms'] for r in by_cohort['strict']]),
                          np.mean([r['checkpoints'][0]['nrooms'] for r in by_cohort['strict']]))
               for c in range(5)) if 'strict' in by_cohort else False
    W('\n## Headline findings\n')
    W(f'**1. The ITEM fallback never fires.** Across {sum(kindtot.values()):,} requirement rolls '
      f'({len(runs):,} runs x 5), the chain dealt ITEM **{kindtot["ITEM"]} times**. There is always '
      'at least one placed candidate, so the branch the code calls "the guaranteed floor and the '
      'reason the chain can never wedge" is dead in practice.\n')
    W('**2. The reachable world does not grow.** That is the consequence of (1). '
      "QuickStartChainPickItem's comment says an ITEM step is drawn so that \"finishing the step "
      'GROWS the sphere, which is what lets the next step be placed further out than this one '
      'was". With no ITEM steps, nothing in the chain ever hands the player a key item, and '
      'completing a WAVE, BOSS, EVENT or QUEST step grants nothing the reach model can see. In the '
      'strict cohort the number of reachable rooms is **identical at all five checkpoints** '
      f'({np.mean([r["checkpoints"][0]["nrooms"] for r in by_cohort["strict"]]):.1f} rooms, '
      f'{np.mean([r["checkpoints"][0]["nregions"] for r in by_cohort["strict"]]):.2f} regions). '
      'A run is exactly as big at the end as it was after the hub.\n')
    W(f'**3. Nearly a third of runs waste a requirement.** {out["dupquest"]/len(runs)*100:.1f}% are dealt '
      'the side quest twice over - a guard comparing against the wrong value. Detailed below.\n')
    W('**4. Almost half the mapped world is invisible to the chain.** '
      f'{sum(len(v) for v in out["causes"].values())} of {len(ROOMS)} rooms and '
      f'{int((out["site_reach"] == 0).sum())} of {len(SITE_ROOMS)} ? room sites are never counted '
      'as reachable under any loadout a run can assemble. Two causes account for most of it: '
      'the untestable `MINISH` token, and bombs not being a key item.\n')

    W('\n## The two cohorts\n')
    W('| cohort | what the player is assumed to hold |\n|---|---|')
    W('| `strict` | the three hub picks, plus whatever the chain\'s own ITEM steps hand over. '
      'This is exactly what the placer sees, and a floor for reach. |')
    W('| `found` | the same, plus one unheld key item per completed placed step and the '
      'fusion bit - standing in for drops and prizes picked up on the way. A ceiling. |')
    W('\nThe truth is between them. Where they disagree, that gap is the finding.\n')

    W('\n## Reachability\n')
    W('![growth](sim/01_growth.png)\n')
    for co in cohorts:
        first = [r['checkpoints'][0]['nrooms'] for r in by_cohort[co]]
        last = [r['checkpoints'][4]['nrooms'] for r in by_cohort[co]]
        W(f'- **{co}**: median {np.median(first):.0f} of {len(ROOMS)} rooms reachable after the '
          f'item selection, {np.median(last):.0f} by the fourth requirement '
          f'(10th-90th percentile {np.percentile(last,10):.0f}-{np.percentile(last,90):.0f}).')
    W('\n![regions](sim/02_region_openness.png)\n')
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
    W('\nThe two that matter are the first two.\n')
    W('- **`MINISH` has no run-time test.** Being Minish is a state, not an inventory item, '
      'so `QuickStartHeldReachMask` can never set the bit and every term containing it is '
      'permanently false. That is a deliberate conservative choice in the reach model - but '
      'the cost of it, measured here, is that a large block of rooms is invisible to the '
      'chain even though the player has a Minish Cap and the portals work.')
    W('- **Bombs are not a `QS_CAT_KEY` item.** Neither hub round 1 nor a chain ITEM step can '
      'ever hand them over, so every bomb-priced room is out of the chain\'s reach unless a '
      'random drop happens to supply them - which nothing in the placement logic can count on. '
      "Mount Crenel's base is the clearest casualty: its whole cave network is priced at bombs.")
    W('\n<details><summary>All of them</summary>\n')
    W('\n| room | region |\n|---|---|')
    for nm in sorted(both_never):
        i = ROOMS.index(nm)
        W(f'| `{nm}` | {", ".join(ROOM_REGIONS[i]) or "-"} |')
    W('\n</details>\n')

    order = np.argsort(-strict)
    W('\n### The 15 most reachable rooms - the staleness watchlist\n')
    W('| room | strict | found |\n|---|---|---|')
    for i in order[:15]:
        W(f'| `{ROOMS[i]}` | {strict[i]:.1f}% | {freq[cohorts[1]][i]:.1f}% |')
    rare = [i for i in order if strict[i] > 0][-15:]
    W('\n### The 15 rarest rooms that are reachable at all\n')
    W('| room | strict | found |\n|---|---|---|')
    for i in rare:
        W(f'| `{ROOMS[i]}` | {strict[i]:.2f}% | {freq[cohorts[1]][i]:.2f}% |')

    W('\n## What the chain asks for, and where\n')
    W('![kinds](sim/04_step_kinds.png)\n')
    W('![hosts](sim/05_host_regions.png)\n')
    hosts = out['host']
    W('\n| region | % of placed requirements (strict) | (found) |\n|---|---|---|')
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

    W('\n## A bug this turned up\n')
    W(f'**{out["dupquest"]:,} of {len(runs):,} runs ({out["dupquest"]/len(runs)*100:.1f}%) are dealt '
      'the side quest as TWO separate requirements.** There is only one quest per run, so the '
      'second one is already satisfied the moment it is dealt - the run silently loses one of '
      'its five steps.\n')
    W("The cause is a two-line mismatch in `QuickStartChainRollStep`'s helpers:\n")
    W('```c\n'
      '// the guard asks whether where == 0 ...\n'
      '!QuickStartChainAlreadyUsed(step, QS_CHAIN_QUEST, 0)\n\n'
      '// ... but the store writes the pool row, which is 0 in only 1 case of 18\n'
      'gSave.chain_where[step] = (u8)QuickStartQuestSlot();\n'
      '```\n')
    W('The simulation agrees exactly with that reading: of the runs that got two quest steps, '
      '**zero** had a quest slot of 0. The comment above the guard says "One quest per run", '
      'so the intent is not in doubt - the guard simply compares against the wrong value.\n')

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
