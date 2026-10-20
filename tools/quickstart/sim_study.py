"""The simulation study: many runs, aggregated in memory, written as a report.

sim.py plays one run at a time and sim_report.py charts a saved dump of
them. This answers a fixed set of questions over far more runs than a dump
can hold, by aggregating as the runs are played (four worker processes, a
few hundred thousand runs, a few MB of counters):

  ROOMS     which rooms are reachable at the end of a run, which a run is
            SENT to (a chain step or the finale names it), which never are;
  CHAINS    the shape of each run's win chain (four step kinds and the
            finale carrier), most and least common;
  WHERE     the region and room each requirement must be met in, overworld
            or interior, per step kind and for the finale;
  ITEMS     everything a run is handed: the three hub picks, the chain's own
            ITEM steps, each step's prize (region clear, ? room prize);
  EVENTS    which ? room kinds the chain's EVENT steps deal, and which kinds
            sit in the rooms a run can reach (what exploring would meet).

Both cohorts are run (sim.py explains them). ITEMS are reported for the
rewards cohort, the one in which a step's prize is actually collected.

The ? room kind and prize are EXACT (sim.site_roll, checked against the ROM
by site_roll_validate.py). The drop region, the hub offers, the quest host
and a region clear's draw use the live RNG in the game and a seeded Python
RNG here, so their distributions are modelled, not replayed.

    python3 tools/quickstart/sim_study.py --runs 100000 \
        --census docs/sim_study_room_census.json \
        --md docs/QUICKSTART_SIM_STUDY.md --charts docs/sim_study

The census file is `room_census.py --gate --json docs/sim_study_room_census.json`
(it boots the ROM once per policed door, about half an hour).
"""
import argparse
import collections
import json
import multiprocessing
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sim as S

OVERWORLD = {f"{p['areaName'][5:]}/{p['roomName'][5:]}" for p in S.POOL}


def _ring_rooms():
    import room_owner as O
    out = set()
    for rn in O.RING:
        an = O.ring_area_of(rn)
        out.add(f'{an[5:]}/{rn[5:]}')
    return out


RING_ROOMS = _ring_rooms()


def is_overworld(room):
    return room in RING_ROOMS or room in OVERWORLD


def bits(hexmask):
    m = int(hexmask, 16)
    i = 0
    while m:
        if m & 1:
            yield i
        m >>= 1
        i += 1


def new_acc():
    C = collections.Counter
    return dict(n=0, reach_end=C(), reach_start=C(), sent=C(), sent_runs=C(), drop=C(),
                region_reach_end=C(), region_sent=C(), chain=C(), chain_set=C(), kinds_at=C(),
                carrier=C(), finale_region=C(), finale_room=C(), finale_fallback=0,
                step_region=C(), step_room=C(), step_ow=C(),
                items=C(), item_runs=C(), item_source=C(), items_per_run=C(), keys_per_run=C(),
                event_kind=C(), event_label=C(), reach_site_kind=C(), reach_site_label=C(),
                site_sent=C(), sites_reach_end=C(), unique_rooms=C(), nrooms_end=C(),
                room_unreached=C(), room_unreached_runs=0,
                drop_region=C(), drop_island=C(), drop_rooms=C())


def play(args):
    cohort, n, seed0 = args
    rng = random.Random(seed0)
    acc = new_acc()
    key_items = set(S.KEY_ITEMS) | {'QUICKSTART_ITEM_GOLD_FLOW', 'QUICKSTART_ITEM_GOLD_LEFT',
                                    'QUICKSTART_ITEM_GOLD_MIDDLE', 'QUICKSTART_ITEM_GOLD_RIGHT'}
    room_names = [S.ROOM_KEY[(a, r)] for a, r, _, _ in S.ALL_ROOMS]
    for _ in range(n):
        seed = rng.getrandbits(32)
        r = S.simulate(seed, cohort, rng)
        acc['n'] += 1
        end, start = r['checkpoints'][-1], r['checkpoints'][0]
        for i in bits(end['rooms']):
            acc['reach_end'][room_names[i]] += 1
        for i in bits(start['rooms']):
            acc['reach_start'][room_names[i]] += 1
        acc['nrooms_end'][end['nrooms']] += 1
        for k, nm in enumerate(S.REGION_NAMES):
            if (end['regions'] >> k) & 1:
                acc['region_reach_end'][nm] += 1
        acc['drop'][r['drop_room']] += 1
        acc['drop_region'][r['drop_region']] += 1
        acc['drop_rooms'][(r['drop_region'], end['nrooms'])] += 1
        if set(end['per_region']) <= {r['drop_region']}:
            acc['drop_island'][r['drop_region']] += 1
        # The chain's shape: four kinds in order, then the carrier.
        shape = '-'.join(st['kind'] for st in r['steps']) + ' > ' + r['carrier']
        acc['chain'][shape] += 1
        acc['chain_set']['+'.join(sorted(st['kind'] for st in r['steps'])) + ' > ' + r['carrier']] += 1
        sent_here = set()
        bad = [st['room'] for st in r['steps'] if st.get('room_ok') is False]
        if not r['finale_room_ok']:
            bad.append('FINALE ' + r['element_room'])
        for b in bad:
            acc['room_unreached'][b] += 1
        if bad:
            acc['room_unreached_runs'] += 1
        for st in r['steps']:
            acc['kinds_at'][(st['step'], st['kind'])] += 1
            if st['room'] is None:
                continue
            acc['sent'][st['room']] += 1
            sent_here.add(st['room'])
            acc['step_region'][(st['kind'], st['region'])] += 1
            acc['step_room'][(st['kind'], st['room'])] += 1
            acc['step_ow'][(st['kind'], 'overworld' if is_overworld(st['room']) else 'interior')] += 1
            acc['region_sent'][st['region']] += 1
            if st['kind'] == 'EVENT':
                acc['event_kind'][st['event'].split(' ')[0]] += 1
                acc['event_label'][st['event']] += 1
                acc['site_sent'][st['where']] += 1
        acc['carrier'][r['carrier']] += 1
        acc['finale_region'][(r['carrier'], r['element_region'])] += 1
        acc['finale_room'][(r['carrier'], r['element_room'])] += 1
        acc['step_ow'][('FINALE ' + r['carrier'], 'overworld' if is_overworld(r['element_room']) else 'interior')] += 1
        acc['region_sent'][r['element_region']] += 1
        if r['element_pool'] == r['drop_pool']:
            acc['finale_fallback'] += 1
        acc['sent'][r['element_room']] += 1
        sent_here.add(r['element_room'])
        for rm in sent_here:
            acc['sent_runs'][rm] += 1
        acc['unique_rooms'][len(sent_here | {r['drop_room']})] += 1
        # Items: hub picks, chain ITEM steps, step prizes.
        got = [('hub pick', it) for it in r['picks']]
        got += [('chain ITEM step', st['detail']) for st in r['steps'] if st['kind'] == 'ITEM' and st['detail']]
        got += [(f"{st['kind']} prize", st['prize']) for st in r['steps'] if st.get('prize')]
        for src, it in got:
            acc['items'][it] += 1
            acc['item_source'][(src, it)] += 1
        for it in {it for _s, it in got}:
            acc['item_runs'][it] += 1
        acc['items_per_run'][len(got)] += 1
        acc['keys_per_run'][sum(1 for _s, it in got if it in key_items)] += 1
        # The ? rooms a run can reach at its end, and what each would deal.
        for i in bits(end['sites']):
            if S.SITES[i]['gate'] != 0:
                continue
            acc['sites_reach_end'][i] += 1
            lab = S.event_label(seed, i)
            acc['reach_site_kind'][lab.split(' ')[0]] += 1
            acc['reach_site_label'][lab] += 1
    return acc


def merge(a, b):
    for k, v in b.items():
        if isinstance(v, collections.Counter):
            a[k].update(v)
        else:
            a[k] += v
    return a


def run_cohort(cohort, runs, workers):
    chunk = max(1, runs // (workers * 8))
    jobs = []
    left, k = runs, 0
    while left > 0:
        n = min(chunk, left)
        jobs.append((cohort, n, 0xC0FFEE + 7919 * k + (0 if cohort == 'strict' else 1 << 20)))
        left -= n
        k += 1
    acc = new_acc()
    with multiprocessing.Pool(workers) as pool:
        for part in pool.imap_unordered(play, jobs):
            merge(acc, part)
    return acc


# ------------------------------------------------------------------ report --

def pct(x, n):
    return 100.0 * x / n if n else 0.0


def fmt(x, n):
    p = pct(x, n)
    if p == 0:
        return '0'
    if p < 0.01:
        return '<0.01%'
    if p < 1:
        return f'{p:.2f}%'
    return f'{p:.1f}%'


def item_name(it):
    for pre in ('ITEM_QST_', 'ITEM_SKILL_', 'QUICKSTART_ITEM_', 'ITEM_'):
        if it.startswith(pre):
            return it[len(pre):].replace('_', ' ').title() if pre != 'ITEM_SKILL_' else \
                'Skill: ' + it[len(pre):].replace('_', ' ').title()
    return it


def charts(res, outdir):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    os.makedirs(outdir, exist_ok=True)
    INK, GRID = '#1c1c1f', '#e3e3e8'
    COL = {'strict': '#3b6ea5', 'rewards': '#c0603a'}
    plt.rcParams.update({'font.size': 9, 'axes.edgecolor': INK, 'axes.labelcolor': INK,
                         'xtick.color': INK, 'ytick.color': INK})
    files = []
    rw = res['rewards']
    # 1. Regions: reachable at the end vs sent to.
    fig, ax = plt.subplots(figsize=(9, 3.6))
    names = S.REGION_NAMES
    x = range(len(names))
    for off, co in ((-0.2, 'strict'), (0.2, 'rewards')):
        a = res[co]
        ax.bar([i + off for i in x], [pct(a['region_reach_end'][nm], a['n']) for nm in names],
               width=0.4, color=COL[co], label=f'{co}: reachable at the end')
    sent_tot = sum(rw['region_sent'].values())
    ax2 = ax.twinx()
    ax2.plot(list(x), [pct(rw['region_sent'][nm], sent_tot) for nm in names], 'k.-', label='rewards: share of sends')
    ax.set_xticks(list(x))
    ax.set_xticklabels(names)
    ax.set_ylabel('% of runs reachable')
    ax2.set_ylabel('% of all requirement sends')
    ax.grid(axis='y', color=GRID)
    ax.legend(loc='upper left', fontsize=7)
    ax2.legend(loc='upper right', fontsize=7)
    ax.set_title('Regions: reachable at the end of the chain, and where requirements send the player')
    fig.tight_layout()
    files.append('01_regions.png')
    fig.savefig(os.path.join(outdir, files[-1]), dpi=130)
    plt.close(fig)
    # 2. ? room kinds: chain EVENT steps vs reachable sites.
    fig, ax = plt.subplots(figsize=(9, 3.4))
    kinds = [k for k in S.EVENT_NAME if rw['reach_site_kind'][k] or rw['event_kind'][k]]
    et, rt = sum(rw['event_kind'].values()), sum(rw['reach_site_kind'].values())
    ax.bar([i - 0.2 for i in range(len(kinds))], [pct(rw['event_kind'][k], et) for k in kinds], width=0.4,
           color='#c0603a', label='chain EVENT steps')
    ax.bar([i + 0.2 for i in range(len(kinds))], [pct(rw['reach_site_kind'][k], rt) for k in kinds], width=0.4,
           color='#8a6fa8', label='every ? room reachable at the end')
    ax.set_xticks(range(len(kinds)))
    ax.set_xticklabels([k.replace('_', ' ').lower() for k in kinds])
    ax.set_ylabel('% of ? rooms')
    ax.grid(axis='y', color=GRID)
    ax.legend(fontsize=7)
    ax.set_title('? room kinds dealt (rewards cohort)')
    fig.tight_layout()
    files.append('02_event_kinds.png')
    fig.savefig(os.path.join(outdir, files[-1]), dpi=130)
    plt.close(fig)
    # 3. Items: share of runs that receive each item, top 30.
    top = rw['item_runs'].most_common(30)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh([item_name(k) for k, _ in top][::-1], [pct(v, rw['n']) for _, v in top][::-1], color='#5b8c5a')
    ax.set_xlabel('% of runs that are handed the item at least once')
    ax.grid(axis='x', color=GRID)
    ax.set_title('Items handed to the player, 30 most common (rewards cohort)')
    fig.tight_layout()
    files.append('03_items.png')
    fig.savefig(os.path.join(outdir, files[-1]), dpi=130)
    plt.close(fig)
    # 4. Rooms: reachable vs sent, every known room.
    rooms = sorted(set(rw['reach_end']) | set(rw['sent_runs']))
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter([pct(rw['reach_end'][r], rw['n']) for r in rooms],
               [pct(rw['sent_runs'][r], rw['n']) for r in rooms], s=10, color='#3b6ea5', alpha=0.7)
    ax.set_xlabel('% of runs in which the room is reachable at the end')
    ax.set_ylabel('% of runs in which a requirement sends the player there')
    ax.set_yscale('symlog', linthresh=0.1)
    ax.grid(color=GRID)
    ax.set_title('Every room: reachable vs sent to (rewards cohort)')
    fig.tight_layout()
    files.append('04_rooms.png')
    fig.savefig(os.path.join(outdir, files[-1]), dpi=130)
    plt.close(fig)
    return files


def report(res, census, md_path, chart_dir, chart_files, runs):
    out = []
    W = out.append
    st, rw = res['strict'], res['rewards']
    W('# QUICKSTART simulation study')
    W('')
    W(f'Generated by `tools/quickstart/sim_study.py` from {st["n"]:,} strict and {rw["n"]:,} rewards runs. '
      'Every number below is regenerated by running the tool; nothing is typed in by hand.')
    W('')
    W('**Cohorts.** `strict` holds the three hub picks plus the chain\'s own ITEM steps: the placer\'s floor. '
      '`rewards` also collects every step\'s prize (a region clear\'s draw, a ? room\'s seeded prize), which can '
      'pay key items and grow the reach. Items are reported for `rewards`.')
    W('')
    W('**Exact vs modelled.** The chain, the reach flood, the finale, the ? room kinds and their prizes are '
      're-implemented from the C and replayed from the seed (checked against the ROM: `sim_validate.py`, '
      '`site_roll_validate.py`). The drop region, the hub offers, the quest host and a region clear\'s item '
      'come from the live RNG in the game and from a seeded Python RNG here.')
    W('')
    for f in chart_files:
        W(f'![{f}]({os.path.relpath(os.path.join(chart_dir, f), os.path.dirname(md_path))})')
        W('')
    # ---- rooms
    W('## 1. Rooms: visited and reachable')
    W('')
    known = [S.ROOM_KEY[(a, r)] for a, r, _, _ in S.ALL_ROOMS]
    W(f'The model knows {len(known)} rooms (every surveyed destination and every region pool row). '
      'A room is VISITED when a requirement sends the player there (a chain step or the finale); '
      'the drop room is counted separately.')
    W('')
    W('| | strict | rewards |')
    W('|---|---|---|')
    for label, fn in (('rooms reachable in at least one run', lambda a: sum(1 for r in known if a['reach_end'][r])),
                      ('rooms reachable in every run', lambda a: sum(1 for r in known if a['reach_end'][r] == a['n'])),
                      ('rooms never reachable', lambda a: sum(1 for r in known if not a['reach_end'][r])),
                      ('rooms visited in at least one run', lambda a: sum(1 for r in known if a['sent_runs'][r])),
                      ('rooms never visited', lambda a: sum(1 for r in known if not a['sent_runs'][r])),
                      ('reachable sometimes but never visited',
                       lambda a: sum(1 for r in known if a['reach_end'][r] and not a['sent_runs'][r]))):
        W(f'| {label} | {fn(st)} | {fn(rw)} |')
    med = lambda c: sorted(c.elements())[sum(c.values()) // 2] if c else 0
    W(f'| median rooms reachable at the end of a run | {med(st["nrooms_end"])} | {med(rw["nrooms_end"])} |')
    W(f'| median distinct rooms a run sends the player to (drop included) | {med(st["unique_rooms"])} | {med(rw["unique_rooms"])} |')
    W('')
    W('### Most visited rooms (rewards)')
    W('')
    W('| room | runs visiting | reachable at end |')
    W('|---|---|---|')
    for rm, v in rw['sent_runs'].most_common(15):
        W(f'| {rm} | {fmt(v, rw["n"])} | {fmt(rw["reach_end"][rm], rw["n"])} |')
    W('')
    W('### Least visited rooms that are ever visited (rewards)')
    W('')
    W('| room | runs visiting | reachable at end |')
    W('|---|---|---|')
    for rm, v in sorted(((r, v) for r, v in rw['sent_runs'].items() if v), key=lambda kv: kv[1])[:15]:
        W(f'| {rm} | {fmt(v, rw["n"])} | {fmt(rw["reach_end"][rm], rw["n"])} |')
    W('')
    never = [r for r in known if rw['reach_end'][r] and not rw['sent_runs'][r]]
    W(f'### Reachable but never visited ({len(never)}, rewards)')
    W('')
    W('These rooms are inside the reach of some runs but host nothing a requirement can name: '
      'no ? room site, and not a region pool row.')
    W('')
    W('| room | regions | reachable at end |')
    W('|---|---|---|')
    regs = {S.ROOM_KEY[(a, r)]: sorted(S.ROOM_REGION.get((a, r), ())) for a, r, _, _ in S.ALL_ROOMS}
    for rm in sorted(never, key=lambda r: -rw['reach_end'][r]):
        W(f'| {rm} | {"+".join(regs[rm])} | {fmt(rw["reach_end"][rm], rw["n"])} |')
    W('')
    nr = [r for r in known if not rw['reach_end'][r]]
    W(f'### Never reachable ({len(nr)}, rewards)')
    W('')
    W(', '.join(sorted(nr)) if nr else 'None.')
    W('')
    W('### By drop region')
    W('')
    W('Where a run starts decides how much of the world it can ever see. A run is an ISLAND when, after all '
      'four requirements, it still cannot reach a single room outside the region it was dropped in.')
    W('')
    W('| drop region | runs dropped there | median rooms reachable at the end | island runs |')
    W('|---|---|---|---|')
    for nm in sorted(S.REGION_NAMES, key=lambda n: -rw['drop_region'][n]):
        n_ = rw['drop_region'][nm]
        c = collections.Counter({k[1]: v for k, v in rw['drop_rooms'].items() if k[0] == nm})
        W(f'| {nm} ({S.REGION_LONG[nm]}) | {fmt(n_, rw["n"])} | {med(c)} | {fmt(rw["drop_island"][nm], n_)} |')
    W('')
    # ---- chains
    W('## 2. Win-condition chains')
    W('')
    W('A chain is four requirements and a finale. The shape below is the four kinds in order, then the finale\'s '
      'carrier (`WAVE`, `BOSS` or `QUEST` in the element region).')
    W('')
    W(f'{len(rw["chain"]):,} distinct ordered shapes in the rewards cohort, '
      f'{len(rw["chain_set"]):,} if order is ignored.')
    W('')
    W('| | most common (rewards) | runs | | least common (rewards) | runs |')
    W('|---|---|---|---|---|---|')
    mc = rw['chain'].most_common(12)
    lc = sorted(rw['chain'].items(), key=lambda kv: (kv[1], kv[0]))[:12]
    for i in range(12):
        a = mc[i] if i < len(mc) else ('', 0)
        b = lc[i] if i < len(lc) else ('', 0)
        W(f'| {i + 1} | `{a[0]}` | {fmt(a[1], rw["n"])} | | `{b[0]}` | {fmt(b[1], rw["n"])} |')
    W('')
    W('Ignoring order:')
    W('')
    W('| kinds (any order) > finale | strict | rewards |')
    W('|---|---|---|')
    for k, v in rw['chain_set'].most_common(15):
        W(f'| `{k}` | {fmt(st["chain_set"][k], st["n"])} | {fmt(v, rw["n"])} |')
    W('')
    W('Step kind by position (rewards):')
    W('')
    W('| step | ' + ' | '.join(S.KIND_NAME[k] for k in (0, 1, 2, 3, 4)) + ' |')
    W('|---|' + '---|' * 5)
    for p in range(S.PRE_STEPS):
        W(f'| {p + 1} | ' + ' | '.join(fmt(rw['kinds_at'][(p, S.KIND_NAME[k])], rw['n']) for k in (0, 1, 2, 3, 4)) + ' |')
    W('')
    W('| finale carrier | strict | rewards |')
    W('|---|---|---|')
    for k in ('WAVE', 'BOSS', 'QUEST'):
        W(f'| {k} | {fmt(st["carrier"][k], st["n"])} | {fmt(rw["carrier"][k], rw["n"])} |')
    W(f'| fell back to the drop row | {fmt(st["finale_fallback"], st["n"])} | {fmt(rw["finale_fallback"], rw["n"])} |')
    W('')
    W('### Requirements dealt in a room outside reach')
    W('')
    W('A WAVE, BOSS or QUEST step and the finale are placed by the pool row\'s reach NODE '
      '(`QuickStartReachPoolOk`), not by the room test an EVENT uses. A row whose room the survey prices above '
      'its node can be dealt while the room itself is out of reach.')
    W('')
    W(f'Runs with such a requirement: strict {fmt(st["room_unreached_runs"], st["n"])}, '
      f'rewards {fmt(rw["room_unreached_runs"], rw["n"])}.')
    W('')
    if rw['room_unreached'] or st['room_unreached']:
        W('| requirement room | strict | rewards |')
        W('|---|---|---|')
        for k in sorted(set(st['room_unreached']) | set(rw['room_unreached'])):
            W(f'| {k} | {fmt(st["room_unreached"][k], st["n"])} | {fmt(rw["room_unreached"][k], rw["n"])} |')
        W('')
    # ---- where
    W('## 3. Where requirements must be met')
    W('')
    W('Overworld means a region room (a field screen); interior means a cave, house, dojo or other pocket room.')
    W('')
    W('| requirement | overworld | interior |')
    W('|---|---|---|')
    for k in ('EVENT', 'WAVE', 'BOSS', 'QUEST', 'FINALE WAVE', 'FINALE BOSS', 'FINALE QUEST'):
        o, i_ = rw['step_ow'][(k, 'overworld')], rw['step_ow'][(k, 'interior')]
        if o + i_:
            W(f'| {k} | {fmt(o, o + i_)} | {fmt(i_, o + i_)} |')
    W('')
    W('By region, share of each requirement kind (rewards):')
    W('')
    kinds = ('EVENT', 'WAVE', 'BOSS', 'QUEST')
    W('| region | ' + ' | '.join(kinds) + ' | finale | all sends |')
    W('|---|' + '---|' * (len(kinds) + 2))
    tot_k = {k: sum(v for (kk, _r), v in rw['step_region'].items() if kk == k) for k in kinds}
    fin_tot = sum(rw['finale_region'].values())
    sent_tot = sum(rw['region_sent'].values())
    for nm in sorted(S.REGION_NAMES, key=lambda n: -rw['region_sent'][n]):
        fin = sum(v for (c, rg), v in rw['finale_region'].items() if rg == nm)
        W(f'| {nm} ({S.REGION_LONG[nm]}) | ' + ' | '.join(fmt(rw['step_region'][(k, nm)], tot_k[k]) for k in kinds)
          + f' | {fmt(fin, fin_tot)} | {fmt(rw["region_sent"][nm], sent_tot)} |')
    W('')
    W('Finale carrier by element region (rewards):')
    W('')
    W('| region | WAVE | BOSS | QUEST |')
    W('|---|---|---|---|')
    for nm in S.REGION_NAMES:
        W(f'| {nm} | ' + ' | '.join(fmt(rw['finale_region'][(c, nm)], rw['n']) for c in ('WAVE', 'BOSS', 'QUEST')) + ' |')
    W('')
    W('Rooms hosting EVENT steps, most and least often (rewards):')
    W('')
    ev = collections.Counter({rm: v for (k, rm), v in rw['step_room'].items() if k == 'EVENT'})
    evt = sum(ev.values())
    W('| most | share | | least | share |')
    W('|---|---|---|---|---|')
    a_, b_ = ev.most_common(12), sorted(ev.items(), key=lambda kv: kv[1])[:12]
    for i in range(12):
        W(f'| {a_[i][0]} | {fmt(a_[i][1], evt)} | | {b_[i][0]} | {fmt(b_[i][1], evt)} |')
    W('')
    live = [i for i, s_ in enumerate(S.SITES) if s_['gate'] == 0]
    dead = [i for i in live if not rw['site_sent'][i]]
    W(f'{len(live)} ? room sites are live (not retired, no fusion gate). '
      f'{len(dead)} were never dealt as an EVENT step in the rewards cohort'
      + (': ' + ', '.join(f'{i} {S.SITES[i]["roomName"][5:]}' for i in dead) if dead else '') + '.')
    W('')
    # ---- items
    W('## 4. Items handed to the player (rewards)')
    W('')
    W('Counted: the three hub picks, every chain ITEM step, and every step prize (a WAVE or BOSS step\'s region '
      'clear, an EVENT step\'s ? room prize). Not counted: enemy drops, pots, fusions, side quests, ? rooms the '
      'chain does not name, and the finale\'s element. A pending ITEM step is paid by the next prize in the game; '
      'here the ITEM step is counted as its own delivery and the next prize as drawn.')
    W('')
    W(f'Median items per run: {med(rw["items_per_run"])}. Median key items per run: {med(rw["keys_per_run"])}.')
    W('')
    W('| most common | runs | | least common (ever handed) | runs |')
    W('|---|---|---|---|---|')
    a_ = rw['item_runs'].most_common(20)
    b_ = sorted(rw['item_runs'].items(), key=lambda kv: kv[1])[:20]
    for i in range(20):
        W(f'| {item_name(a_[i][0])} | {fmt(a_[i][1], rw["n"])} | | {item_name(b_[i][0])} | {fmt(b_[i][1], rw["n"])} |')
    W('')
    pool = sorted({e['item'] for e in S.TIERS if not S.is_pseudo(e['item'])})
    never_items = [it for it in pool if not rw['item_runs'][it] and it not in S.BOOT_ITEMS]
    W(f'Items in the tier table never handed over by the counted sources ({len(never_items)}): '
      + (', '.join(item_name(i) for i in never_items) if never_items else 'none')
      + '. (The Ocarina and the Smith\'s Sword are handed over at boot, so no draw offers them.)')
    W('')
    W('By source:')
    W('')
    srcs = sorted({s_ for s_, _ in rw['item_source']})
    W('| source | deliveries | top items |')
    W('|---|---|---|')
    for src in srcs:
        c = collections.Counter({it: v for (s_, it), v in rw['item_source'].items() if s_ == src})
        W(f'| {src} | {sum(c.values()):,} | ' + ', '.join(f'{item_name(k)} {fmt(v, sum(c.values()))}'
                                                      for k, v in c.most_common(6)) + ' |')
    W('')
    # ---- events
    W('## 5. ? room events')
    W('')
    W('What the chain\'s EVENT steps deal, and what every ? room a run can reach at its end would deal '
      '(the rooms an exploring player meets).')
    W('')
    et, rt = sum(rw['event_kind'].values()), sum(rw['reach_site_kind'].values())
    W('| kind | chain EVENT steps | reachable ? rooms |')
    W('|---|---|---|')
    for k in sorted(S.EVENT_NAME, key=lambda k: -rw['event_kind'][k]):
        W(f'| {k} | {fmt(rw["event_kind"][k], et)} | {fmt(rw["reach_site_kind"][k], rt)} |')
    W('')
    W('Finer labels (chain EVENT steps):')
    W('')
    W('| label | share |')
    W('|---|---|')
    for k, v in rw['event_label'].most_common():
        W(f'| {k} | {fmt(v, et)} |')
    W('')
    W('The survive-the-clock variant of WAVES is chosen per visit from the live stream (one visit in three) and '
      'is folded into WAVES here.')
    W('')
    # ---- census
    if census:
        W('## 6. Rooms the overworld leads to that the build does not use')
        W('')
        W('`tools/quickstart/room_census.py` walks every door, link, Minish hole and scroll seam out of every '
          'region room, asks the ROM\'s own containment at every policed door, and diffs the result against what '
          'the build incorporates (a survey destination, a ? room site, a pool row).')
        W('')
        wired = [r for r in census if r['wired']]
        W(f'{len(wired)} rooms hang off a region. {sum(1 for r in wired if r["tags"])} are incorporated. '
          f'{sum(1 for r in wired if not r["tags"] and r.get("enterable"))} can be entered but are unused; '
          f'{sum(1 for r in wired if not r["tags"] and not r.get("enterable"))} are shut by containment.')
        W('')
        W('Surveyed (reachable in the chain\'s model) but hosting no ? room site, so no requirement can send the '
          'player there:')
        W('')
        W('| room | region | reached via | runs reachable (rewards) |')
        W('|---|---|---|---|')
        for r in wired:
            if 'SURVEYED' in r['tags'] and not any(t.startswith('SITE') for t in r['tags']) and 'POOL' not in r['tags']:
                key = f'{r["area"][5:]}/{r["room"][5:]}'
                W(f'| {key} | {"+".join(r["owners"])} | {r["via"][0][5:]} {r["via"][1]} | {fmt(rw["reach_end"][key], rw["n"])} |')
        W('')
        W('A ? room site with no survey row (the chain cannot price it, so never names it):')
        W('')
        for r in wired:
            if any(t.startswith('SITE') for t in r['tags']) and 'SURVEYED' not in r['tags']:
                W(f'- {r["area"][5:]}/{r["room"][5:]} ({"+".join(r["owners"])})')
        W('')
        W('Enterable, not surveyed, no site (by owning region):')
        W('')
        by = collections.defaultdict(list)
        for r in wired:
            if not r['tags'] and r.get('enterable'):
                by['+'.join(r['owners'])].append(r['room'][5:])
        W('| region | rooms |')
        W('|---|---|')
        for k in sorted(by):
            W(f'| {k} | {", ".join(sorted(by[k]))} |')
        W('')
        shut = [r for r in wired if not r['tags'] and not r.get('enterable')]
        if shut:
            W('Shut by containment (a policed door into them is cancelled), unused:')
            W('')
            W('| room | region | door |')
            W('|---|---|---|')
            for r in shut:
                W(f'| {r["room"][5:]} | {"+".join(r["owners"])} | {r["via"][0][5:]} {r["via"][1]} |')
            W('')
    with open(md_path, 'w') as f:
        f.write('\n'.join(out) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', type=int, default=20000)
    ap.add_argument('--workers', type=int, default=os.cpu_count() or 2)
    ap.add_argument('--census', default=None)
    ap.add_argument('--md', default=os.path.join(S.ROOT, 'docs', 'QUICKSTART_SIM_STUDY.md'))
    ap.add_argument('--charts', default=os.path.join(S.ROOT, 'docs', 'sim_study'))
    ap.add_argument('--json', default=None, help='also dump the aggregates')
    a = ap.parse_args()
    res = {co: run_cohort(co, a.runs, a.workers) for co in ('strict', 'rewards')}
    census = json.load(open(a.census)) if a.census else None
    files = charts(res, a.charts)
    report(res, census, a.md, a.charts, files, a.runs)
    if a.json:
        with open(a.json, 'w') as f:
            json.dump({co: {k: ({str(kk): vv for kk, vv in v.items()} if isinstance(v, dict) else v)
                            for k, v in acc.items()} for co, acc in res.items()}, f)
    print(f'{a.runs} runs per cohort -> {a.md}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
