"""Walk the win chain's spheres without walking, and check every step is
somewhere the player could actually be standing.

The chain's whole safety claim is "a step is only ever placed inside the
sphere the player has already opened". This proves it from the outside: boot
the ROM, read the step the game dealt, INDEPENDENTLY recompute reachability
in Python from the same survey the C table was generated from, and complain
if the two disagree. Then satisfy the step the way the game would see it
satisfied, let the reward land, and do it again for the next one.

    python3 tools/quickstart/chain_probe.py [rom]
"""
import sys, os
sys.path.insert(0, os.path.abspath('tools/quickstart'))
from emu import boot, warp, here
import parse_tables as P
import world_reach as W
import gen_reach as G

SAVE = 0x02002a40
CHAIN_KIND, CHAIN_WHERE, CHAIN_DETAIL = SAVE + 0x26, SAVE + 0x2B, SAVE + 0x30
CHAIN_PROGRESS, CHAIN_ROLLED = SAVE + 0x35, SAVE + 0x36
INV, FLAGS = SAVE + 0xF2, SAVE + 0x25C
# QS_BIT0 is the gSave.flags bit of QUICKSTART WINDOW offset 0, which is
# FLAG_BANK_12 offset 700. The site block is different: those are RAW bank-12
# offsets based at 1, 700 lower. Getting this backwards makes every read look
# plausible and be wrong, which cost one round of "unreachable" verdicts that
# were really just the drop region read from the wrong bits.
QS_BIT0 = 3388                       # QUICKSTART window offset 0
BANK12_BIT0 = QS_BIT0 - 700          # FLAG_BANK_12 offset 0
BANK11_BIT0 = BANK12_BIT0 + (0x9C0 - 0xA80)
KINDS = ['ITEM', 'EVENT', 'WAVE', 'BOSS', 'QUEST']
RINGS = ['CG', 'NHF', 'SHF', 'EH', 'LLR', 'TRIL', 'WW', 'RV', 'CW', 'WR']
ADJ = {  # mirrors sQuickStartRingAdjacency in game.c
    'CG': ['NHF'], 'NHF': ['CG', 'SHF', 'LLR', 'TRIL', 'RV'],
    'SHF': ['NHF', 'EH', 'WW'], 'EH': ['SHF', 'LLR', 'MW'],
    'LLR': ['EH', 'NHF', 'TRIL', 'LH'], 'TRIL': ['LLR', 'NHF', 'WW', 'RV', 'CREN'],
    'WW': ['TRIL', 'SHF', 'CW'], 'RV': ['NHF', 'TRIL'],
    'CW': ['WW', 'WR'], 'WR': ['CW'], 'CREN': ['TRIL'],
    # Spurs, not a loop: the MW-LH border exists in the exit lists but
    # neither room's arrival component reaches it. See game.c's own
    # comment on sQuickStartRingAdjacency.
    'MW': ['EH'], 'LH': ['LLR'],
}
# This table is a hand copy of one in game.c, so it can drift - and it did:
# Mt Crenel went into the ring, the game started placing steps there, and
# this model called every one of them unreachable because it had never heard
# of the region. The names come from the generator, so at least a MISSING
# region is loud now rather than a wrong verdict.
assert set(ADJ) == {r.replace('QS_RING_', '') for r in G.RINGS}, (
    'chain_probe ADJ is out of step with gen_reach RINGS: %s'
    % (set(ADJ) ^ {r.replace('QS_RING_', '') for r in G.RINGS}))
# ...and symmetric, which the game's own table is.
for _a in ADJ:
    for _b in ADJ[_a]:
        assert _a in ADJ[_b], 'ring adjacency is not symmetric: %s -> %s' % (_a, _b)
# Mt Crenel is deliberately absent: it is a ring member but NOT a pool row,
# so nothing drops the player there and no region wave loop runs in it.
POOL_RING = ['CG', 'LLR', 'SHF', 'NHF', 'TRIL', 'EH', 'EH', 'EH',
             'WW', 'WW', 'WW', 'RV', 'CW', 'WR', 'WR', 'MW', 'LH']
SITES = P.content_sites()
POOL = P.region_pool()
ITEM_NAME = {v: k for k, v in P.ITEMS.items()}
ITEM_OF_TOKEN = {tok: item for tok, _, item in G.TOKENS if item}


def qs_flag(c, off):
    b = QS_BIT0 + off
    return (c.memory.u8[FLAGS + (b >> 3)] >> (b & 7)) & 1


def set_bank_bit(c, bit, on=True):
    a, m = FLAGS + (bit >> 3), 1 << (bit & 7)
    c.memory.u8[a] = (c.memory.u8[a] | m) if on else (c.memory.u8[a] & ~m)


def held_tokens(c):
    """The tokens the player currently satisfies, as the game would see it."""
    out = set()
    for tok, item in ITEM_OF_TOKEN.items():
        n = P.ITEMS[item]
        if (c.memory.u8[INV + (n >> 2)] >> ((n & 3) * 2)) & 3:
            out.add(tok)
    if c.memory.u8[SAVE + 0x114 + 3]:      # kinstones.fusedCount
        out.add('fusion')
    return out


def terms_met(req, held):
    return any(all(t in held for t in term) for term in req) if req else True


def reachable_regions(c, held):
    # Five bits, not four: the pool passed sixteen rows with Minish Woods
    # and Lake Hylia, so each pool-index field grew a high bit in the
    # 208-212 run (GF_POOL_HI_*). GF_DROP_REGION_BIT(0..3) is still 467.
    drop = 0
    for b in range(4):
        if qs_flag(c, 467 + b):
            drop |= 1 << b
    if qs_flag(c, 211):
        drop |= 16
    drop %= len(POOL_RING)
    open_ = {POOL_RING[drop]}
    entry = {}
    for key, r in W.SURVEY.items():
        ring = G.RING[key].replace('QS_RING_', '')
        entry.setdefault(ring, []).extend(r['room_req'] or [[]])
    changed = True
    while changed:
        changed = False
        for r in list(open_):
            for t in ADJ[r]:
                if t in open_ or t not in entry:
                    continue
                if terms_met(entry[t], held):
                    open_.add(t)
                    changed = True
    return drop, open_


def room_reachable(regions, held, area, room):
    for key, r in W.SURVEY.items():
        ring = G.RING[key].replace('QS_RING_', '')
        if ring not in regions:
            continue
        for e in r['dests']:
            if 'AREA_' + e['area'] == area and 'ROOM_%s_%s' % (e['area'], e['room']) == room:
                if terms_met(e['req'], held):
                    return True
    return False


def check(c, n):
    """Describe step n and verify it against the Python model."""
    kind, where, detail = (c.memory.u8[CHAIN_KIND + n], c.memory.u8[CHAIN_WHERE + n],
                           c.memory.u8[CHAIN_DETAIL + n])
    held = held_tokens(c)
    drop, regions = reachable_regions(c, held)
    if kind == 0:
        return 'ITEM  %s' % ITEM_NAME.get(detail, '0x%02x' % detail), True
    if kind == 1:
        an, rn = SITES[where][0], SITES[where][1]
        ok = room_reachable(regions, held, an, rn)
        return 'EVENT site %-2d %s' % (where, rn), ok
    if kind in (2, 3, 4):
        ring = POOL_RING[where]
        ok = ring in regions
        label = {2: 'WAVE ', 3: 'BOSS ', 4: 'QUEST'}[kind]
        extra = ' -> wave %d' % detail if kind == 2 else ''
        return '%s pool %-2d %-42s [%s]%s' % (label, where, POOL[where]['roomName'], ring, extra), ok
    return 'kind %d ??' % kind, False


def force(c, n):
    kind, where, detail = (c.memory.u8[CHAIN_KIND + n], c.memory.u8[CHAIN_WHERE + n],
                           c.memory.u8[CHAIN_DETAIL + n])
    if kind == 0:
        a, sh = INV + (detail >> 2), (detail & 3) * 2
        c.memory.u8[a] = (c.memory.u8[a] & ~(3 << sh)) | (1 << sh)
        return 'granted %s' % ITEM_NAME.get(detail, detail)
    if kind == 1:
        # One bit per site now: raw FLAG_BANK_12 offset ORIGIN + index.
        set_bank_bit(c, BANK12_BIT0 + 1 + where)
        return 'set site %d DONE' % where
    if kind == 2:
        for b in range(8):
            on = (detail >> b) & 1
            if where < 12:
                set_bank_bit(c, QS_BIT0 + 362 + where * 8 + b, on)
            else:
                # Extension slots. These used to be borrowed scraps of
                # FLAG_BANK_11 and were colliding with seventeen of that
                # bank's own offsets; they now live in four free runs of
                # the QUICKSTART window itself. Mirrors
                # QuickStartExtSlotFlag in game.c - keep the two in step.
                lin = (where - 12) * 16 + 2 + b
                if lin < 39:
                    off = 617 + lin
                elif lin < 71:
                    off = 658 + (lin - 39)
                elif lin < 84:
                    off = 496 + (lin - 71)
                else:
                    off = 213 + (lin - 84)
                set_bank_bit(c, QS_BIT0 + off, on)
        return 'wave counter := %d' % detail
    if kind == 3:
        return 'SKIP boss (needs a real kill in the room)'
    if kind == 4:
        set_bank_bit(c, BANK11_BIT0 + 39)   # the quest flags live in FLAG_BANK_11
        return 'set GF_QUEST_DONE'
    return 'SKIP'


def run(rom, seed):
    bad = 0
    c = boot(rom, seed=seed)
    # Out of the hub first. The chain deliberately refuses to roll while the
    # player is still in it (the kit is not chosen yet and a reward dropped
    # there is dropped in a room the run is leaving), so a probe that stays
    # put would watch nothing happen forever. Any real room will do - the
    # sphere is measured from the DROP region, not from wherever the player
    # is standing - and the first monitor pass corrects the drop bits from
    # the rolled row to the usable one, which is what the check reads.
    warp(c, P.AREAS['AREA_HYRULE_FIELD'], P.ROOMS['ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD'], 240, 400)
    for _ in range(300):
        c.run_frame()
    drop, regions = reachable_regions(c, held_tokens(c))
    print('  drop pool %d [%s], sphere 0 = %s'
          % (drop, POOL_RING[drop], ','.join(sorted(regions))))
    for n in range(4):
        for _ in range(300):
            c.run_frame()
            if c.memory.u8[CHAIN_ROLLED] > n:
                break
        if c.memory.u8[CHAIN_ROLLED] <= n:
            print('  step %d: NEVER ROLLED' % n)
            return 1
        desc, ok = check(c, n)
        print('  step %d: %-70s %s' % (n, desc, 'ok' if ok else '*** UNREACHABLE ***'))
        bad += 0 if ok else 1
        note = force(c, n)
        if note.startswith('SKIP'):
            print('           %s - stopping this seed here' % note)
            return bad
        for _ in range(900):
            c.run_frame()
            if c.memory.u8[CHAIN_PROGRESS] > n:
                break
        if c.memory.u8[CHAIN_PROGRESS] <= n:
            print('           %s, but the step did NOT advance' % note)
            return bad + 1
    print('  all four pre-steps done (progress=%d)' % c.memory.u8[CHAIN_PROGRESS])
    return bad


rom = sys.argv[1] if len(sys.argv) > 1 else 'tmc.gba'
total = 0
for sd in (None, 0x11111111, 0x22222222, 0x33333333, 0x44444444, 0x55555555):
    print('== seed %s' % ('derived' if sd is None else '0x%08x' % sd))
    total += run(rom, sd)
    sys.stdout.flush()
print('\n%d problem(s)' % total)
