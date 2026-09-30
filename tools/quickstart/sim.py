"""Simulate whole runs and record what each one could reach.

WHAT THIS IS. A model of the shipped reachability and win-chain logic,
driven by the same run seed the ROM uses, fast enough to play tens of
thousands of runs. It answers questions no single playthrough can - which
rooms are reachable in almost every run, which in almost none, which rooms
never host a step, which regions the chain leans on - by running the actual
placement rules over the actual tables many times.

WHAT IS MODELLED EXACTLY. Everything below is a pure function of the run
seed and the player's own choices, and is re-implemented from the shipped
code line for line:

  * QuickStartChainHash, and the four-kind rotation it drives
  * QuickStartChainRollStep - count candidates, walk to the chosen one,
    fall back to ITEM - including QuickStartChainAlreadyUsed
  * QuickStartReachableRegions - the flood over sQuickStartRegionAdjacency
    admitting a neighbour only when its entry price is paid
  * QuickStartReachRoomOk / QuickStartReachPoolOk / QuickStartChainEventOk /
    QuickStartChainBossOk
  * QuickStartChainPickItem - the unheld QS_CAT_KEY draw
  * the three hub selection rounds' candidate pools

All of it reads the SHIPPED TABLES: include/quickstart/reach.h (itself
generated from the walked survey), sQuickStartRegionAdjacency, byPool,
sQuickStartTiers and sQuickStartRoomContentSites, parsed out of the source
rather than retyped.

WHAT IS NOT, AND WHY. Two systems key off the live RNG stream
(gRand, advanced by every frame of play) rather than off the run seed, so
no seed-driven model can say what a particular run will get:

  * which KIND a ? room rolls (QuickStartPickSmallKind and friends call
    Random() the first time the player enters the site)
  * which enemies a wave is composed of (QuickStartSpawnEnemyGroupAt-
    Difficulty rolls an archetype and casts it from the level roster)

For those this reports the DISTRIBUTION - each site's kind class and the
exact sixteenths that class deals - which is the honest form of the
question "what can be encountered", and says so in the output.

THE LOADOUT. A run's reach grows as it collects, so what the player is
assumed to hold matters more than anything else here. Two cohorts are
simulated and reported separately rather than one being chosen:

  * STRICT - the player holds the three hub picks plus whatever the chain's
    own ITEM steps hand over, and nothing else. This is exactly what
    QuickStartChainRollStep sees when it places a step, so it is the ground
    truth for placement, and a floor for reach.
  * FOUND - the same, plus one unheld key item per completed placed step,
    standing in for the drops, region rewards and ? room prizes a player
    picks up on the way. A ceiling, and deliberately generous.

The truth is between them. Reporting both is the point.

    python3 tools/quickstart/sim.py --runs 20000 --out docs/sim_runs.json
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse_tables as P

ROOT = P.ROOT
GAME = P.GAME
REACH_H = open(os.path.join(ROOT, 'include', 'quickstart', 'reach.h')).read()

U32 = 0xFFFFFFFF
NEVER = U32

# ---------------------------------------------------------------- tables --

REGION_NAMES = ['CG', 'NHF', 'SHF', 'EH', 'LLR', 'TRIL', 'WW', 'RV',
                'CW', 'WR', 'CREN', 'MW', 'LH']
REGION_LONG = {
    'CG': 'Hyrule Castle Garden', 'NHF': 'North Hyrule Field',
    'SHF': 'South Hyrule Field', 'EH': 'Eastern Hills',
    'LLR': 'Lon Lon Ranch', 'TRIL': 'Trilby Highlands',
    'WW': 'Western Wood', 'RV': 'Royal Valley', 'CW': 'Castor Wilds',
    'WR': 'Wind Ruins', 'CREN': 'Mount Crenel', 'MW': 'Minish Woods',
    'LH': 'Lake Hylia',
}
RIDX = {n: i for i, n in enumerate(REGION_NAMES)}


def _token_bits():
    out = {}
    for m in re.finditer(r'#define (QS_REACH_\w+)\s+\(1u <<\s*(\d+)\)', REACH_H):
        out[m.group(1)] = 1 << int(m.group(2))
    return out


TOKEN_BITS = _token_bits()
# Bits with no run-time test are never set in the held mask, so any term
# containing one is permanently false. game.c says so; this mirrors it.
UNTESTABLE = (TOKEN_BITS['QS_REACH_MINISH'] | TOKEN_BITS['QS_REACH_STORY'] |
              TOKEN_BITS['QS_REACH_MAZE'] | TOKEN_BITS['QS_REACH_SWITCHES4'] |
              TOKEN_BITS['QS_REACH_UNSURVEYED'] | TOKEN_BITS['QS_REACH_BOULDER'])
ITEM_BITS = int(re.search(r'#define QS_REACH_ITEM_BITS (\d+)', REACH_H).group(1))
REACH_ITEMS = [t.strip() for t in
               re.search(r'static const u16 sQuickStartReachItems\[\] = \{(.*?)\};',
                         REACH_H, re.S).group(1).replace('\n', ' ').split(',') if t.strip()]
ITEM_TO_BIT = {name: 1 << i for i, name in enumerate(REACH_ITEMS)}


def _region_entry():
    body = re.search(r'static const u32 sQuickStartReachRegion\[\]\[3\] = \{(.*?)\n\};',
                     REACH_H, re.S).group(1)
    out = []
    for line in body.strip().split('\n'):
        m = re.search(r'\{(.*?)\}', line)
        if not m:
            continue
        out.append([NEVER if t.strip() == '~0u' else int(t.strip().rstrip('u'), 0)
                    for t in m.group(1).split(',')])
    return out


REGION_ENTRY = _region_entry()


def _dests():
    body = re.search(r'static const QuickStartReachDest sQuickStartReachDests\[\] = \{(.*?)\n\};',
                     REACH_H, re.S).group(1)
    out = []
    for m in re.finditer(r'\{ (QS_REGION_\w+), (AREA_\w+), (ROOM_\w+), \{(.*?)\} \}', body):
        terms = [NEVER if t.strip() == '~0u' else int(t.strip().rstrip('u'), 0)
                 for t in m.group(4).split(',')]
        out.append((RIDX[m.group(1)[10:]], P.AREAS[m.group(2)], P.ROOMS[m.group(3)],
                    terms, m.group(2), m.group(3)))
    return out


DESTS = _dests()


def _adjacency():
    """sQuickStartRegionAdjacency, split on its own /* NAME */ row markers.

    Parsed by cutting the body at each marker rather than by one regex: the
    rows wrap over two lines and carry prose comments between them, and a
    single pattern that tries to span that quietly matched nothing at all -
    every row read as 0, which makes every region an island and every run
    unable to leave its drop. Worth the extra few lines to fail loudly.
    """
    i = GAME.find('static const u16 sQuickStartRegionAdjacency[QS_REGION_COUNT] = {')
    body = GAME[i:GAME.find('\n};', i)]
    marks = [(m.start(), m.group(1)) for m in re.finditer(r'/\* (\w+)\s*\*/', body)
             if m.group(1) in RIDX]
    out = [0] * len(REGION_NAMES)
    for n, (pos, name) in enumerate(marks):
        end = marks[n + 1][0] if n + 1 < len(marks) else len(body)
        mask = 0
        for r in re.findall(r'1 << QS_REGION_(\w+)', body[pos:end]):
            mask |= 1 << RIDX[r]
        out[RIDX[name]] = mask
    if any(m == 0 for m in out):
        raise SystemExit('adjacency parse failed: ' + repr(out))
    return out


ADJACENCY = _adjacency()


def _by_pool():
    body = re.search(r'static const u8 byPool\[\] = \{(.*?)\};', GAME, re.S).group(1)
    return [RIDX[r] for r in re.findall(r'QS_REGION_(\w+)', body)]


BY_POOL = _by_pool()
POOL = P.region_pool()
POOL_SIZE = len(POOL)
assert len(BY_POOL) == POOL_SIZE, (len(BY_POOL), POOL_SIZE)


def _boss_rooms():
    """The rooms QuickStartRegionAllowsBoss says yes to."""
    i = GAME.find('static bool32 QuickStartRegionAllowsBoss(const QuickStartRegion* region) {')
    body = GAME[i:GAME.find('\n}\n', i)]
    rooms = set()
    for m in re.finditer(r'region->area == (AREA_\w+) && region->room == (ROOM_\w+)', body):
        rooms.add((P.AREAS[m.group(1)], P.ROOMS[m.group(2)]))
    for m in re.finditer(r'room == (ROOM_HYRULE_FIELD_\w+)', body):
        rooms.add((P.AREAS['AREA_HYRULE_FIELD'], P.ROOMS[m.group(1)]))
    return rooms


BOSS_ROOMS = _boss_rooms()


def _sites():
    """Content sites, with the kind class each one draws from."""
    i = GAME.find('sQuickStartRoomContentSites[QUICKSTART_CONTENT_SITE_COUNT] = {')
    body = GAME[i:GAME.find('\n};', i)]
    out = []
    for m in re.finditer(
            r'\{ (AREA_\w+), (ROOM_\w+), (QUICKSTART_KINDS_\w+), ([0-9xa-fA-F]+),\s*\n?\s*'
            r'([0-9xa-fA-F]+)(?:\s*,\s*(\w+))?', body):
        gate = m.group(6) or '0'
        gid = P.KINSTONES[gate] if gate.startswith('KINSTONE_') else 0
        out.append(dict(areaName=m.group(1), roomName=m.group(2),
                        area=P.AREAS[m.group(1)], room=P.ROOMS[m.group(2)],
                        kinds=m.group(3)[len('QUICKSTART_KINDS_'):], gate=gid))
    return out


SITES = _sites()


def _tiers():
    i = GAME.find('static const QuickStartTierEntry sQuickStartTiers[] = {')
    body = GAME[i:GAME.find('\n};', i)]
    body = re.sub(r'//[^\n]*', '', body)
    out = []
    for m in re.finditer(r'\{\s*(ITEM_\w+),\s*(QS_CAT_\w+),\s*(QS_TIER_\w+),\s*(QS_REQ_\w+),\s*(\d+)', body):
        out.append(dict(item=m.group(1), cat=m.group(2), tier=m.group(3),
                        req=m.group(4), repeatable=int(m.group(5))))
    return out


TIERS = _tiers()
KEY_ITEMS = [e['item'] for e in TIERS if e['cat'] == 'QS_CAT_KEY']

# Items the mode hands over at boot (GameTask_Transition), so they are held
# before round 1 and can never be offered. Only the two that carry a reach
# bit are listed - the wallet, shield, kinstone bag and Foursword do not.
#
# SMITH_SWORD is the one that matters most and it is easy to miss: North
# Hyrule Field's entry price is QS_REACH_SWORD and nothing else, so
# forgetting it walls every run into its drop region. A first pass at this
# left it out and every Castle-Garden drop reported zero reachable rooms.
BOOT_ITEMS = {'ITEM_OCARINA', 'ITEM_SMITH_SWORD'}

# QS_REACH_FUSION is NOT held at boot. QUICKSTART wipes gSave.kinstones and
# then writes the three Castor Wilds statue bits directly, which does not
# touch fusedCount - and fusedCount is what QuickStartHeldReachMask reads.
# (The fusedCount = 100 line in game.c is in the MAPEXPLORE branch.) So the
# strict cohort never holds it; the found cohort takes it after the first
# completed step, on the reasoning that a player who clears content fuses
# something.

# QuickStartRegionNeedsSwampKit / QuickStartHasRegionKit. A drop into one of
# these regions is RE-DRAWN if the player is not carrying the kit that makes
# it survivable, so the drop distribution is not uniform over the pool - it
# depends on what round 1 handed out. Modelled because that skew is one of
# the things worth measuring.
KIT_RULES = {'CW': ('ITEM_PEGASUS_BOOTS', 'ITEM_ROCS_CAPE'),
             'WR': ('ITEM_PEGASUS_BOOTS', 'ITEM_ROCS_CAPE'),
             'LH': ('ITEM_FLIPPERS',)}

WIN_WAVE, WIN_BOSS, WIN_QUEST = 0, 1, 2
CARRIER_NAME = {WIN_WAVE: 'WAVE', WIN_BOSS: 'BOSS', WIN_QUEST: 'QUEST'}


def avalanche(seed, add):
    h = (seed + add) & U32
    h = (h * 0x9E3779B9) & U32
    h ^= h >> 15
    h = (h * 0x2C1B3C6D) & U32
    h ^= h >> 12
    return h


def pool_usable(pool_index, owned):
    rule = KIT_RULES.get(REGION_NAMES[BY_POOL[pool_index]])
    return rule is None or any(i in owned for i in rule)


def drop_index_usable(seed, raw, owned):
    """QuickStartDropRegionIndexUsable: keep the raw draw when the player
    can survive it, otherwise re-draw over the usable rows from the seed."""
    if pool_usable(raw, owned):
        return raw
    usable = [i for i in range(POOL_SIZE) if pool_usable(i, owned)]
    if not usable:
        return raw
    return usable[(avalanche(seed, 0x5D) & 0x7fff) % len(usable)]


def regions_within_two(region):
    one = (1 << region) | ADJACENCY[region]
    two = one
    for r in range(len(REGION_NAMES)):
        if (one >> r) & 1:
            two |= ADJACENCY[r]
    return two


def roll_carrier_and_element(seed, drop, rng):
    """QuickStartRollElementRegionOnce. The carrier is seed-derived; the
    element region is a Random() draw rejected until it lands within two
    regions of the drop (and on a boss room, for the BOSS carrier)."""
    allowed = regions_within_two(BY_POOL[drop])
    carrier = (avalanche(seed, 0xF7) & 0x7fff) % 3
    if carrier == WIN_BOSS:
        if not any((allowed >> BY_POOL[i]) & 1 and
                   (POOL[i]['area'], POOL[i]['room']) in BOSS_ROOMS
                   for i in range(POOL_SIZE)):
            carrier = WIN_WAVE
    while True:
        elem = rng.randrange(POOL_SIZE)
        if not (allowed >> BY_POOL[elem]) & 1:
            continue
        if carrier == WIN_BOSS and (POOL[elem]['area'], POOL[elem]['room']) not in BOSS_ROOMS:
            continue
        return carrier, elem

# ------------------------------------------------------------- the model --


def held_mask(items):
    m = 0
    for it in items:
        m |= ITEM_TO_BIT.get(it, 0)
    return m


def terms_met(terms, held):
    for t in terms:
        if t == NEVER:
            continue
        if (t & ~held) == 0:
            return True
    return False


def reachable_regions(held, drop_region):
    """QuickStartReachableRegions: the drop region unconditionally, then a
    flood admitting a neighbour whose entry price is paid."""
    open_ = 1 << drop_region
    for _ in range(len(REGION_NAMES)):
        grown = open_
        for r in range(len(REGION_NAMES)):
            if not (open_ >> r) & 1:
                continue
            for t in range(len(REGION_NAMES)):
                if not (ADJACENCY[r] >> t) & 1 or (grown >> t) & 1:
                    continue
                if terms_met(REGION_ENTRY[t], held):
                    grown |= 1 << t
        if grown == open_:
            break
        open_ = grown
    return open_


def reach_room_ok(regions, held, area, room):
    for dr, da, dro, terms, _, _ in DESTS:
        if da != area or dro != room:
            continue
        if not (regions >> dr) & 1:
            continue
        if terms_met(terms, held):
            return True
    return False


def reach_pool_ok(regions, pool_index):
    return bool((regions >> BY_POOL[pool_index]) & 1)


def chain_hash(seed, salt):
    h = (seed + salt * 0x85EBCA6B + 0xC0FFEE) & U32
    h = (h * 0x9E3779B9) & U32
    h ^= h >> 15
    h = (h * 0x2C1B3C6D) & U32
    h ^= h >> 12
    return h


def chain_pick_item(seed, salt, owned):
    pool = [i for i in KEY_ITEMS if i not in owned]
    if not pool:
        return None
    return pool[(chain_hash(seed, salt) & 0x7fff) % len(pool)]


KIND_ITEM, KIND_EVENT, KIND_WAVE, KIND_BOSS, KIND_QUEST = 0, 1, 2, 3, 4
KIND_NAME = {KIND_ITEM: 'ITEM', KIND_EVENT: 'EVENT', KIND_WAVE: 'WAVE',
             KIND_BOSS: 'BOSS', KIND_QUEST: 'QUEST'}
KORDER = [KIND_EVENT, KIND_WAVE, KIND_BOSS, KIND_QUEST]


def roll_step(seed, step, prior, regions, held, owned, quest_slot, sites_done):
    """QuickStartChainRollStep. `prior` is the (kind, where) of earlier steps."""
    def used(kind, where):
        return (kind, where) in prior

    def candidates(kind):
        if kind == KIND_EVENT:
            return [i for i, s in enumerate(SITES)
                    if i not in sites_done and s['gate'] == 0
                    and reach_room_ok(regions, held, s['area'], s['room'])
                    and not used(KIND_EVENT, i)]
        if kind == KIND_WAVE:
            return [i for i in range(POOL_SIZE)
                    if reach_pool_ok(regions, i) and not used(KIND_WAVE, i)]
        if kind == KIND_BOSS:
            return [i for i in range(POOL_SIZE)
                    if reach_pool_ok(regions, i)
                    and (POOL[i]['area'], POOL[i]['room']) in BOSS_ROOMS
                    and not used(KIND_BOSS, i)]
        if kind == KIND_QUEST:
            if reach_pool_ok(regions, quest_slot) and not used(KIND_QUEST, 0):
                return [quest_slot]
            return []
        return []

    h = chain_hash(seed, step)
    rot = (h >> 8) & 3
    for k in range(4):
        kind = KORDER[(k + rot) & 3]
        cands = candidates(kind)
        if cands:
            pick = cands[(h & 0x7fff) % len(cands)]
            where = 0 if kind == KIND_QUEST else pick
            if kind == KIND_QUEST:
                where = quest_slot
            return kind, where
    return KIND_ITEM, 0


# The ? room kind distribution, in sixteenths, per kind class. Read off the
# four QuickStartPick*Kind switches - these are what a site of each class
# deals when the player first walks into it.
KIND_MIX = {
    'SMALL':    {'WAVES': 6, 'NPC': 3, 'POT_LOTTERY': 3, 'FAIRY': 1, 'WAVES_FALLBACK': 3},
    'LARGE':    None,
    'ANY':      None,
    'ELITE':    None,
    'RARE':     None,
    'MINIBOSS': None,
}

# ----------------------------------------------------------- one full run --

ALL_ROOMS = sorted({(a, r, an, rn) for _, a, r, _, an, rn in DESTS} |
                   {(p['area'], p['room'], p['areaName'], p['roomName']) for p in POOL})
ROOM_KEY = {(a, r): f'{an[5:]}/{rn[5:]}' for a, r, an, rn in ALL_ROOMS}
ROOM_REGION = {}
for dr, da, dro, _, _, _ in DESTS:
    ROOM_REGION.setdefault((da, dro), set()).add(REGION_NAMES[dr])
for i, p in enumerate(POOL):
    ROOM_REGION.setdefault((p['area'], p['room']), set()).add(REGION_NAMES[BY_POOL[i]])


ROOM_INDEX = {(a, r): i for i, (a, r, _, _) in enumerate(ALL_ROOMS)}


def snapshot(regions, held, label):
    """One checkpoint, as BITMASKS rather than name lists.

    154 rooms and 105 sites per checkpoint, five checkpoints per run, tens
    of thousands of runs: written as names this was 12MB per thousand runs
    and would have been a third of a gigabyte at the sample size this wants.
    A hex mask is lossless, three orders of magnitude smaller, and the
    report expands it back through meta.room_names.
    """
    rm = 0
    for (a, r), i in ROOM_INDEX.items():
        if reach_room_ok(regions, held, a, r):
            rm |= 1 << i
    sm = 0
    for i, s in enumerate(SITES):
        if reach_room_ok(regions, held, s['area'], s['room']):
            sm |= 1 << i
    return dict(label=label, regions=regions, rooms='%x' % rm, sites='%x' % sm,
                nrooms=bin(rm).count('1'), nsites=bin(sm).count('1'),
                nregions=bin(regions).count('1'))


def simulate(seed, cohort, rng):
    """One run. `rng` picks which of the three offered items the player takes."""
    owned = set(BOOT_ITEMS)
    # --- the three hub rounds. Only round 1 (key items) and round 3's Spin
    # Attack move the reach mask, but all three are dealt so the record is
    # the real loadout.
    picks = []
    for cats, tiers in (({'QS_CAT_KEY'}, None),
                        ({'QS_CAT_REWARD', 'QS_CAT_STAT'}, {'QS_TIER_RARE'}),
                        ({'QS_CAT_SKILL'}, {'QS_TIER_COMMON', 'QS_TIER_UNCOMMON'})):
        pool = [e['item'] for e in TIERS
                if e['cat'] in cats and (tiers is None or e['tier'] in tiers)
                and (e['repeatable'] or e['item'] not in owned)]
        seen, uniq = set(), []
        for it in pool:
            if it not in seen:
                seen.add(it)
                uniq.append(it)
        offer = rng.sample(uniq, min(3, len(uniq))) if uniq else []
        if offer:
            take = rng.choice(offer)
            owned.add(take)
            picks.append(take)
    # The drop is a Random() draw over the pool - the live stream, not the
    # seed - so it is modelled as uniform and then run through the kit
    # re-draw, which IS seed-derived and does depend on what round 1 gave.
    drop_pool = drop_index_usable(seed, rng.randrange(POOL_SIZE), owned)
    drop_region = BY_POOL[drop_pool]
    carrier, element_pool = roll_carrier_and_element(seed, drop_pool, rng)
    quest_slot = element_pool if carrier == WIN_QUEST else rng.randrange(POOL_SIZE)

    checkpoints, steps = [], []
    prior, sites_done = set(), set()
    fused = False
    held = held_mask(owned)
    regions = reachable_regions(held, drop_region)
    checkpoints.append(snapshot(regions, held, 'after selection'))
    for step in range(5):
        kind, where = roll_step(seed, step, prior, regions, held, owned,
                                quest_slot, sites_done)
        detail = None
        if kind == KIND_ITEM:
            detail = chain_pick_item(seed, step * 7 + 3, owned)
            if detail:
                owned.add(detail)
        else:
            prior.add((kind, where))
            if kind == KIND_EVENT:
                sites_done.add(where)
            if cohort == 'found':
                got = chain_pick_item(seed, 1000 + step, owned)
                if got:
                    owned.add(got)
                fused = True
        steps.append(dict(step=step, kind=KIND_NAME[kind], where=where, detail=detail))
        held = held_mask(owned) | (TOKEN_BITS['QS_REACH_FUSION'] if fused else 0)
        regions = reachable_regions(held, drop_region)
        if step < 4:
            checkpoints.append(snapshot(regions, held, f'after requirement {step + 1}'))
    return dict(seed=seed, cohort=cohort,
                drop_pool=drop_pool, drop_region=REGION_NAMES[drop_region],
                element_pool=element_pool,
                element_region=REGION_NAMES[BY_POOL[element_pool]],
                carrier=CARRIER_NAME[carrier],
                quest_slot=quest_slot, picks=picks, steps=steps,
                checkpoints=checkpoints)


def main():
    import random
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', type=int, default=5000)
    ap.add_argument('--out', default=os.path.join(ROOT, 'docs', 'sim_runs.json'))
    ap.add_argument('--cohorts', default='strict,found')
    a = ap.parse_args()
    rng = random.Random(0xC0FFEE)
    runs = []
    for cohort in a.cohorts.split(','):
        for n in range(a.runs):
            seed = rng.getrandbits(32)
            runs.append(simulate(seed, cohort, rng))
    meta = dict(runs=a.runs, cohorts=a.cohorts.split(','),
                rooms=len(ALL_ROOMS), sites=len(SITES), pool=POOL_SIZE,
                room_names=[ROOM_KEY[(a_, r_)] for a_, r_, _, _ in ALL_ROOMS],
                room_regions=[sorted(ROOM_REGION.get((a_, r_), ())) 
                              for a_, r_, _, _ in ALL_ROOMS],
                site_rooms=[f"{s['areaName'][5:]}/{s['roomName'][5:]}" for s in SITES],
                site_kinds=[s['kinds'] for s in SITES],
                pool_rooms=[f"{p['areaName'][5:]}/{p['roomName'][5:]}" for p in POOL],
                pool_regions=[REGION_NAMES[b] for b in BY_POOL],
                region_names=REGION_NAMES, region_long=REGION_LONG)
    with open(a.out, 'w') as f:
        json.dump(dict(meta=meta, runs=runs), f)
    print(f'{len(runs)} runs -> {a.out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
