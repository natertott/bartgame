"""QUICKSTART invariant checker (roadmap Phase A1).

Machine-validates every placement-bearing table after a build. The failure
class it exists for: hand-placed coordinates that are wrong for the room
they name - the cause of six separate shipped bugs (region exit box outside
its room, content spots below the floor, unmeasured shared entrances, shop
stock in a sealed alcove, spawn offsets inside walls).

Tiers:
  static    source-only: door tags on every 2-door pool room, pool size
            constants consistent with their arrays. Always runs.
  flags     source-only: every GF_* bit block expanded over its declared
            parameter range - no bit claimed twice, nothing at a bank's
            unwritable offset 0, nothing past the end of its bank, and every
            per-run bit covered by a run-start clear loop. Always runs.
  regions   5 emulator boots: each region row's entrance/reward on open
            ground, exit box inside room bounds and off the border row.
  pool      20 boots: every 2-door pool row's entrance is real open floor
  entrances (not solid, not water) and its content spot is in bounds.
  gfx       20 boots: no region runs the 44-slot GFX table below its
  budget    reserve at any difficulty (a full table drops sprites).
  hub       11 boots: every shop item on the hub's Floor 1 spawns where
            its table says and lifts from the walkway in front of it; the
            roof wave spawns entirely inside the component the player can
            reach from its arrival spot, and drops its reward on clearing.
  fusers    5 boots: every spot in a region's fuser scatter list is open
            ground inside the entrance's own reachable component, every gate
            reads un-fused on a fresh run, and the sprites this boot placed
            are standing on spots from that list. Checks the whole list, not
            just the spots the run's scatter roll happened to pick - a bad
            spot would otherwise only surface on some runs. A fuser behind
            the very obstacle its fusion removes is unwinnable.
  rooms     ~45 emulator boots: every ? room lands; every content site's
            spot is open, in bounds, and in the entrance's reachable
            component (multi-site rooms instead require one distinct floor
            segment per site - the Boomerang chamber's ladder layout);
            AND a forced chest-kind spawn drops a GROUND_ITEM near the spot
            (folded into the same boot, so it costs nothing extra).

Usage:  python3 tools/quickstart/invariant_check.py [--rom tmc.gba]
                 [--static-only | --regions | --rooms] [--seed N]
--seed pins the run's RNG (roadmap A3, tools/quickstart/seed.py) so a
failure can be reproduced, or so a sweep can test seeds other than the one
a blank-save boot always derives.
Runs everything by default. Batches emulator work across subprocesses
because mgba leaks a core per boot and corrupts the allocator eventually.
Exit code 0 = all PASS/WARN, 1 = any FAIL.
"""
import sys, os, re, json, subprocess, collections, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse_tables as P

GAME_C = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'src', 'game.c')

# Roadmap A3. None = let the run derive its own seed, which for a harness
# boot (no .sav behind it) is always the SAME seed - so the emulator tiers
# have only ever exercised one run's worth of content. --seed N pins a
# different one, which is how a seed-dependent placement bug gets found, and
# how a failure gets reproduced once it is.
SEED = None

# Rooms that are expected not to be reachable and why - reported WARN.
KNOWN = {}
GROUND_ITEM_ID = 0
QS_EVENT_ITEM_DROP = 0

# --- flags tier ------------------------------------------------------------
#
# QUICKSTART packs its whole persistent state into two of vanilla's local
# flag banks as hand-numbered bit blocks. Every block is a range of literals
# in a #define, and the ranges are only kept apart by arithmetic in comments.
# That has failed silently at least twice - once when the content site block
# grew into GF_NHF_BRIDGE_JOINED (joining North Hyrule Field's bridge marked
# the smithy "already randomized"), once when 286 bits of retired GF_DOOR_*
# storage sat unreclaimed and blocked the site table from growing past 30.
#
# So: parse every GF_* / QUICKSTART_*_BIT define out of game.c, expand it
# over its whole declared parameter range, resolve each to an absolute bit
# in gSave.flags, and assert no bit is claimed twice and no block runs past
# the end of its bank.

# bank -> (first absolute bit, one past last) from include/flags.h.
FLAG_BANKS = {11: (0x9C0, 0xA80), 12: (0xA80, 0x1000)}

# Macro-name prefix -> (bank, origin). Ordered; first match wins. Origin is
# either a literal or the name of a define parsed out of game.c. Many of
# these are read through helper functions (QuickStartGauntletReadBits,
# QuickStartQuestFlag, ...) rather than at the macro's own call site, so the
# family is declared here rather than inferred from usage.
FLAG_FAMILIES = [
    ('GF_CONTENT_SITE_', 12, 'QUICKSTART_SITE_FLAG_ORIGIN'),
    ('GF_SEED_PINNED', 11, 0),
    ('GF_QUEST_', 11, 0),
    ('QUICKSTART_CHARM_BIT', 11, 0),
    ('GF_SEAM_GAUNTLET_', 11, 0),
    ('GF_HANDICAP_', 11, 0),
    ('GF_HUNT_', 11, 0),
    ('GF_HUB_PHASE_BIT', 11, 0),
    ('GF_ROOF_', 11, 0),
    ('GF_SHOP_SLOT_BIT', 11, 0),
    ('GF_', 12, 'QUICKSTART_FLAG_ORIGIN'),  # default: the QUICKSTART window
]

# Parameter ranges that aren't stated in the define's own trailing comment.
# (prefix, param) -> (lo, hi) inclusive, or (lo, 'NAME - 1') to resolve a
# define. Anything left undeclared is a FAIL, not a skip - a new macro must
# say how wide it is before this tier can vouch for the layout.
FLAG_PARAM_RANGES = {
    ('GF_CONTENT_SITE_', 'i'): (0, 'QUICKSTART_CONTENT_SITE_MAX - 1'),
    ('GF_SLOT_', 'i'): (0, 3),
    ('GF_SHOP_REFILL_PRICE_BIT', 'i'): (0, 2),
    ('GF_SHOP_ONEOFF_PRICE_BIT', 'i'): (0, 3),
    ('GF_SHOP_HEART_PIECE_BUYS_BIT', 'b'): (0, 4),
    ('GF_SHOP_SLOT_SOLD_BIT', 'i'): (0, 3),
    ('GF_SHOP_SLOT_BIT', 'i'): (0, 3),
    ('GF_REGION_REWARD_STATE_BIT', 'i'): (0, 'QUICKSTART_REGION_STATE_MAX - 1'),
    ('GF_REGION_REWARD_STATE_BIT', 'b'): (0, 1),
    ('GF_REGION_WAVE_BIT', 'i'): (0, 'QUICKSTART_REGION_STATE_MAX - 1'),
    ('GF_REGION_WAVE_BIT', 'b'): (0, 7),
}

# Macros that only exist to be composed into the ones above; their own range
# is covered by their users, and expanding them separately would report the
# whole block as a self-collision.
FLAG_BASE_MACROS = ('GF_CONTENT_SITE_BASE', 'GF_SLOT_BASE')

# Bits that are deliberately NOT cleared at the start of a run. The seed pin
# is the clearest case: its entire job is to survive into the next run.
FLAG_PERSISTENT = ('GF_DIFFICULTY_BIT', 'GF_SEED_PINNED')

DEFINE_RE = re.compile(r'^#define\s+(\w+)(\([^)]*\))?\s+(.*?)\s*(?://\s*(.*))?$')


def _parse_defines(src):
    """name -> (params, body, trailing comment) for every #define in game.c."""
    out = {}
    for line in src.split('\n'):
        m = DEFINE_RE.match(line.strip())
        if not m:
            continue
        name, params, body, comment = m.groups()
        params = [p.strip() for p in params[1:-1].split(',')] if params else []
        out[name] = (params, body.strip(), comment or '')
    return out


def _build_namespace(defines):
    """Evaluate every define into a Python value or lambda, best effort."""
    ns = {}
    for _ in range(4):  # a few passes: bodies reference other defines
        for name, (params, body, _c) in defines.items():
            if name in ns:
                continue
            try:
                if params:
                    src = 'lambda %s: %s' % (', '.join(params), body)
                    fn = eval(src, dict(ns))
                    fn(*([0] * len(params)))  # smoke-test it resolves
                    ns[name] = fn
                else:
                    ns[name] = eval(body, dict(ns))
            except Exception:
                pass
    return ns


def _param_range(name, param, comment, ns):
    """(lo, hi) inclusive for one macro parameter."""
    m = re.search(r'\b%s\s*=\s*(\d+)\.\.(\d+)' % re.escape(param), comment)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r'\b%s\s*=\s*(\d+)\s*,\s*(\d+)\b' % re.escape(param), comment)
    if m:  # "b = 0,1" - an enumeration, not a range
        return int(m.group(1)), int(m.group(2))
    for (prefix, p), rng in FLAG_PARAM_RANGES.items():
        if name.startswith(prefix) and p == param:
            lo, hi = rng
            return (lo if isinstance(lo, int) else eval(lo, dict(ns)),
                    hi if isinstance(hi, int) else eval(hi, dict(ns)))
    return None


def check_flags():
    out = []
    src = open(GAME_C).read()
    defines = _parse_defines(src)
    ns = _build_namespace(defines)

    claimed = {}  # absolute bit -> macro name
    blocks = collections.defaultdict(list)  # macro -> [absolute bits]
    for name, (params, _body, comment) in sorted(defines.items()):
        if not (name.startswith('GF_') or name == 'QUICKSTART_CHARM_BIT'):
            continue
        if name in FLAG_BASE_MACROS:
            continue
        fam = next((f for f in FLAG_FAMILIES if name.startswith(f[0])), None)
        if fam is None:
            out.append(('FAIL', f'{name}: no FLAG_FAMILIES entry - which bank does it live in?'))
            continue
        _prefix, bank, origin = fam
        origin = origin if isinstance(origin, int) else ns.get(origin)
        if origin is None:
            out.append(('FAIL', f'{name}: could not resolve its origin constant'))
            continue
        if name not in ns:
            out.append(('FAIL', f'{name}: could not evaluate its definition'))
            continue
        ranges = []
        for p in params:
            r = _param_range(name, p, comment, ns)
            if r is None:
                out.append(('FAIL', f'{name}: parameter "{p}" has no declared range '
                                    f'(say "// {p} = 0..N" on the define, or add it to '
                                    f'FLAG_PARAM_RANGES)'))
                break
            ranges.append(range(r[0], r[1] + 1))
        else:
            values = ([ns[name](*combo) for combo in itertools.product(*ranges)]
                      if params else [ns[name]])
            for v in values:
                blocks[name].append(FLAG_BANKS[bank][0] + origin + v)

    # 1. no bit claimed by two different macros
    for name, bits in sorted(blocks.items()):
        for b in bits:
            if b in claimed and claimed[b] != name:
                out.append(('FAIL', f'{name} and {claimed[b]} both claim absolute bit {b} '
                                    f'(0x{b:x}) - overlapping flag blocks'))
            claimed[b] = name

    # 2. nothing may claim offset 0 of a bank: SetLocalFlagByBank (flags.c)
    #    is `if (flag != 0) WriteBit(...)`, so vanilla reserves offset 0
    #    everywhere as "no flag" and a block based there silently loses its
    #    first bit. This has bitten twice - the content site block's
    #    RANDOMIZED latch, and chain slot 0's wave counter.
    for name, bits in sorted(blocks.items()):
        for bank, (lo, _hi) in FLAG_BANKS.items():
            if lo in bits:
                out.append(('FAIL', f'{name} claims offset 0 of bank {bank} - '
                                    f'SetLocalFlagByBank silently drops it'))

    # 3. no block runs past the end of its bank
    for name, bits in sorted(blocks.items()):
        fam = next(f for f in FLAG_FAMILIES if name.startswith(f[0]))
        lo, hi = FLAG_BANKS[fam[1]]
        if min(bits) < lo or max(bits) >= hi:
            out.append(('FAIL', f'{name} spans {min(bits)}..{max(bits)}, outside bank '
                                f'{fam[1]} ({lo}..{hi - 1})'))
        if max(bits) >= 4096:
            out.append(('FAIL', f'{name} runs past the end of gSave.flags (4096 bits)'))

    # 4. the run-start wipes actually cover what they claim to
    m = re.search(r'for \(bit = 0; bit < (\d+); bit\+\+\) \{\s*'
                  r'ClearLocalFlagByBank\(FLAG_BANK_12, bit\);', src)
    site_max = (ns.get('QUICKSTART_SITE_FLAG_ORIGIN', 0) +
                ns.get('QUICKSTART_CONTENT_SITE_MAX', 0) * ns.get('QUICKSTART_CONTENT_SITE_BITS', 0))
    if not m:
        out.append(('FAIL', 'no run-start clear loop found for the content site block'))
    elif int(m.group(1)) < site_max:
        out.append(('FAIL', f'the content site block is {site_max} bits but the run-start '
                            f'clear only covers {m.group(1)} - the top sites carry over'))
    else:
        out.append(('PASS', f'run-start clear covers all {site_max} bits of the site block'))

    b11 = [b for n, bits in blocks.items() for b in bits
           if FLAG_BANKS[11][0] <= b < FLAG_BANKS[11][1] and not n.startswith(FLAG_PERSISTENT)]
    cleared11 = set()
    for lo, hi in re.findall(r'for \(bit = (\d+); bit <= (\d+); bit\+\+\) \{\s*'
                             r'ClearLocalFlagByBank\(FLAG_BANK_11, bit\);', src):
        cleared11 |= set(range(int(lo), int(hi) + 1))
    missed = sorted({b - FLAG_BANKS[11][0] for b in b11} - cleared11)
    if not cleared11:
        out.append(('FAIL', 'no run-start clear loop found for FLAG_BANK_11'))
    elif missed:
        out.append(('FAIL', f'FLAG_BANK_11 offsets {missed[:8]} are used but never cleared '
                            f'at the start of a run'))
    else:
        out.append(('PASS', f'run-start clear covers all {len(set(b11))} per-run bank 11 bits'))

    # 5. the site block clear must not be undone

    # 6. no area QUICKSTART actually enters may share bank 12 with the site
    #    block, which is raw-addressed from 0 and would collide with that
    #    area's own vanilla local flags.
    b12_areas = set()
    meta = open(os.path.join(os.path.dirname(GAME_C), 'data', 'areaMetadata.c')).read()
    rows = re.findall(r'^\s*\{[^}]*LOCAL_BANK_(\d+)[^}]*\},', meta, re.M)
    for idx, bank in enumerate(rows):
        if bank == '12':
            b12_areas.add(idx)
    used = {row[2] for row in P.content_sites()} | {P.AREAS[an] for an, _rn in P.pool_doors()}
    clash = sorted(used & b12_areas)
    if clash:
        out.append(('FAIL', f'areas {clash} use LOCAL_BANK_12 and are reachable in this mode - '
                            f'their vanilla flags alias the content site block'))
    else:
        out.append(('PASS', f'no reachable area shares FLAG_BANK_12 '
                            f'({len(b12_areas)} bank-12 areas, all unreachable)'))

    span = max(claimed) if claimed else 0
    out.append(('PASS', f'{len(claimed)} flag bits claimed by {len(blocks)} blocks, '
                        f'no overlaps, highest bit {span} of 4095'))
    return out


def check_static():
    out = []
    for (an, rn), d in P.pool_doors().items():
        doors = d['doors']
        if len(doors) < 2:
            out.append(('FAIL', f'{rn}: fewer than 2 door rows'))
            continue
        tags = (doors[0]['ex'], doors[1]['ex'])
        if tags != (0x3fe, 0x3fd):
            out.append(('FAIL', f'{rn}: door tags {tags[0]:#x}/{tags[1]:#x}, want 0x3fe/0x3fd'))
        else:
            out.append(('PASS', f'{rn}: door tags OK'))
    game = P.GAME
    import re
    for const, arr in (('QUICKSTART_2DOOR_SMALL_ROOM_POOL_SIZE', 'sQuickStart2DoorSmallRoomPool'),
                       ('QUICKSTART_2DOOR_LARGE_ROOM_POOL_SIZE', 'sQuickStart2DoorLargeRoomPool')):
        m = re.search(r'#define ' + const + r' (\d+)', game)
        i = game.find(arr + '[] = {')
        j = game.find('\n};', i)
        rows = len(re.findall(r'\{ AREA_\w+,', game[i:j]))
        n = int(m.group(1))
        lvl = 'PASS' if n <= rows else 'FAIL'
        out.append((lvl, f'{const}={n} vs {rows} rows'))

    # The tier table, which replaced the flat reward pools. Two things worth
    # asserting, both of which have already gone wrong once:
    #
    # 1. The tier roll must be able to reach RARE. The draw seed is six bits
    #    (0-63) and the roll was originally "seed % 100 < 60", which meant a
    #    seed could never land in the 90-99 band and rare was unreachable.
    #    Buckets out of ten divide exactly and work at any seed width.
    # 2. Every category that a "? room" can draw from needs at least one entry
    #    per tier it can actually reach, or the draw silently falls back.
    tiers = {}
    i = game.find('static const QuickStartTierEntry sQuickStartTiers[] = {')
    j = game.find('\n};', i)
    rows = re.findall(r'\{\s*(\w+),\s*(QS_CAT_\w+),\s*(QS_TIER_\w+),\s*(QS_REQ_\w+),\s*(\d)\s*\}', game[i:j])
    if not rows:
        out.append(('FAIL', 'tier table did not parse'))
        return out
    for item, cat, tier, _req, _rep in rows:
        tiers.setdefault((cat, tier), []).append(item)
    buckets = int(re.search(r'#define QS_TIER_BUCKETS (\d+)', game).group(1))
    common = int(re.search(r'#define QS_TIER_COMMON_BUCKETS (\d+)', game).group(1))
    uncommon = int(re.search(r'#define QS_TIER_UNCOMMON_BUCKETS (\d+)', game).group(1))
    seed_range = int(re.search(r'#define QUICKSTART_DRAW_SEED_RANGE (\d+)', game).group(1))
    rare = buckets - common - uncommon
    if rare <= 0:
        out.append(('FAIL', f'no rare bucket: {common}+{uncommon} of {buckets}'))
    elif seed_range < buckets:
        out.append(('FAIL', f'draw seed range {seed_range} is smaller than {buckets} tier buckets'))
    else:
        hit = {t: 0 for t in ('common', 'uncommon', 'rare')}
        for seed in range(seed_range):
            r = seed % buckets
            hit['common' if r < common else ('uncommon' if r < common + uncommon else 'rare')] += 1
        if min(hit.values()) == 0:
            out.append(('FAIL', f'a tier is unreachable from the seed range: {hit}'))
        else:
            pct = {k: round(v * 100.0 / seed_range, 1) for k, v in hit.items()}
            out.append(('PASS', f'tier roll reaches every tier: {pct}'))
    # A "? room" draws QS_CAT_DROP = REWARD|WEAPON|SKILL|STAT.
    for tier in ('QS_TIER_COMMON', 'QS_TIER_UNCOMMON', 'QS_TIER_RARE'):
        n = sum(len(v) for (c, t), v in tiers.items()
                if t == tier and c != 'QS_CAT_KEY')
        lvl = 'PASS' if n > 0 else 'FAIL'
        out.append((lvl, f'{tier.replace("QS_TIER_", "").lower()} drop entries: {n}'))
    # The lottery table is separate and positional, so its size must match.
    m = re.search(r'#define QUICKSTART_LOTTERY_PRIZE_COUNT (\d+)', game)
    i = game.find('sQuickStartLotteryPrizes[8] = {')
    j = game.find('\n};', i)
    entries = re.findall(r'ITEM_\w+', game[i:j])
    n = int(m.group(1))
    if n != len(entries):
        out.append(('FAIL', f'QUICKSTART_LOTTERY_PRIZE_COUNT={n} vs {len(entries)} entries'))
    elif n & (n - 1):
        out.append(('FAIL', f'lottery prize count {n} is not a power of two'))
    else:
        out.append(('PASS', f'lottery prize table: {n} entries, power of two'))
    return out


def emu_regions(rom):
    from emu import boot, warp, here, room_dims, coll_at
    out = []
    for r in P.region_pool():
        c = boot(rom, seed=SEED)
        c.memory.u8[0x03000bf0 + 4] = 0
        warp(c, r['area'], r['room'], r['entrance'][0], r['entrance'][1])
        if here(c) != (r['area'], r['room']):
            out.append(('FAIL', f"{r['roomName']}: did not land ({here(c)})"))
            continue
        W, H = room_dims(c)
        x0, x1, y0, y1 = r['exitBox']
        fails, warns = [], []
        # The Lon Lon lesson, encoded precisely: a box CLIPPED by the room
        # edge still has reachable interior and fires (SHF's north band,
        # Trilby's east band both work in play); a box whose intersection
        # with the room is EMPTY can never fire (Lon Lon's old y 966-984 in
        # a 960-tall room).
        ix0, ix1 = max(x0, 0), min(x1, W - 1)
        iy0, iy1 = max(y0, 0), min(y1, H - 1)
        if ix0 > ix1 or iy0 > iy1:
            fails.append(f'exit box {r["exitBox"]} has NO overlap with room {W}x{H}')
        elif (x0, x1, y0, y1) != (ix0, ix1, iy0, iy1):
            warns.append(f'exit box {r["exitBox"]} clipped by room {W}x{H} edge')
        for label, (px, py) in (('entrance', r['entrance']), ('reward', r['reward'])):
            if not (0 <= px < W and 0 <= py < H):
                fails.append(f'{label} ({px},{py}) out of bounds')
            else:
                v = coll_at(c, px // 16, py // 16)
                if v == 0x0f:
                    fails.append(f'{label} ({px},{py}) on fully solid tile')
                elif v != 0:
                    # Partial/special collision (stair edges, path tiles like
                    # Castle Garden's 0x5f) - standable in practice, so worth
                    # eyes, not a build failure.
                    warns.append(f'{label} ({px},{py}) on special tile {v:#x}')
        if fails:
            out.append(('FAIL', f"{r['roomName']}: " + '; '.join(fails + warns)))
        elif warns:
            out.append(('WARN', f"{r['roomName']}: " + '; '.join(warns)))
        else:
            out.append(('PASS', f"{r['roomName']}: entrance/reward/exit box OK"))
    return out


def emu_gfx_budget(rom):
    """No region may run the GFX table down to nothing, at any difficulty.

    MAX_GFX_SLOTS is 44 game-wide and it is the overworld's real ceiling -
    a full table drops sprites (entities exist, nothing renders) and costs
    frame time. Before the reserve existed, South and North Hyrule Field
    both sat at 44/44 from difficulty 8 up. QuickStartEnforceGfxReserve now
    holds a floor; this tier is what stops it regressing.
    """
    from emu import boot, warp, here, qs_set, GENT, STRIDE, MAX_ENT
    MAX_GFX, GFXBASE, DIFF0 = 44, 0x02024490, 174
    FLOOR = 2  # the hard floor QUICKSTART_GFX_HARD_FLOOR promises
    out = []
    for r in P.region_pool():
        worst_free, worst_diff = MAX_GFX, None
        landed_any = False
        for diff in (0, 4, 8, 12):
            c = boot(rom, seed=SEED)
            for b in range(4):
                qs_set(c, DIFF0 + b, (diff >> b) & 1)
            c.memory.u8[0x03000bf0 + 4] = 0
            warp(c, r['area'], r['room'], r['entrance'][0], r['entrance'][1])
            if here(c) != (r['area'], r['room']):
                continue
            landed_any = True
            for _ in range(600):
                c.run_frame()
                used = sum(1 for i in range(MAX_GFX)
                           if (c.memory.u8[GFXBASE + 4 + i * 12] & 0x0F) not in (0, 1, 2))
                if MAX_GFX - used < worst_free:
                    worst_free, worst_diff = MAX_GFX - used, diff
            del c
        if not landed_any:
            out.append(('WARN', f"{r['roomName']}: never landed, GFX not measured"))
        elif worst_free < FLOOR:
            out.append(('FAIL', f"{r['roomName']}: only {worst_free} free GFX slots at "
                                f"difficulty {worst_diff} (floor is {FLOOR})"))
        else:
            out.append(('PASS', f"{r['roomName']}: >= {worst_free} free GFX slots at every difficulty"))
    return out


def emu_pool_entrances(rom):
    """Every 2-door pool row's entrance must be on open ground (collision 0).

    The failure this exists for: the shared, unmeasured (100,100) default.
    It is floor in most pool rooms and NOT floor in some - solid in the Dark
    Hyrule Castle bridge (spawns in midair), water (0x30) in the Veil Falls
    rupee-path hallway (spawns in a pool and gets stuck). Both shipped.
    """
    from emu import boot, warp, here, room_dims, coll_at
    out = []
    for row in P.pool_rows():
        c = boot(rom, seed=SEED)
        c.memory.u8[0x03000bf0 + 4] = 0
        warp(c, row['area'], row['room'], row['ex'], row['ey'])
        if here(c) != (row['area'], row['room']):
            out.append(('FAIL', f"{row['roomName']}: did not land ({here(c)})"))
            continue
        W, H = room_dims(c)
        msgs = []
        for label, x, y in (('entrance', row['ex'], row['ey']),
                            ('content spot', row['ex'] + row['dx'], row['ey'] + row['dy'])):
            if not (0 <= x < W and 0 <= y < H):
                msgs.append(f'{label} ({x},{y}) out of bounds {W}x{H}')
                continue
            v = coll_at(c, x // 16, y // 16)
            if v != 0 and label == 'entrance':
                msgs.append(f'{label} ({x},{y}) on collision {v:#04x}, want open floor')
        if msgs:
            out.append(('FAIL', f"{row['roomName']}: " + '; '.join(msgs)))
        else:
            out.append(('PASS', f"{row['roomName']}: entrance on open ground"))
    return out


def emu_fusers(rom):
    """Every Kinstone fuser must be reachable while its own gate is still shut.

    The failure this exists for is specific and unwinnable: a fuser placed
    behind the very obstacle its fusion removes. So the boot deliberately
    does NOT pre-fuse anything - it walks in on a fresh run and floods the
    walkable graph from the region entrance, exactly as the player would.
    """
    from emu import boot, warp, here, room_dims, coll_at, GENT, MAX_ENT, STRIDE, ROOM_CONTROLS, r16
    KIN = 0x02002a40 + 0x114 + 301  # gSave.kinstones.fusedKinstones
    ZELDA, NPC_KIND = 0x28, 7
    by_room = collections.OrderedDict()
    for f in P.fusers():
        by_room.setdefault((f['areaName'], f['roomName'], f['area'], f['room']), []).append(f)
    out = []
    for (an, rn, area, room), rows in by_room.items():
        r = next((x for x in P.region_pool() if x['area'] == area and x['room'] == room), None)
        if r is None:
            out.append(('FAIL', f'{rn}: fusers placed in a room that is not a region'))
            continue
        c = boot(rom, seed=SEED)
        c.memory.u8[ROOM_CONTROLS + 4] = 0
        warp(c, area, room, r['entrance'][0], r['entrance'][1])
        if here(c) != (area, room):
            out.append(('FAIL', f'{rn}: did not land ({here(c)})'))
            continue
        W, H = room_dims(c)
        tw, th = W // 16, H // 16
        grid = [[coll_at(c, tx, ty) for tx in range(tw)] for ty in range(th)]
        seed = (r['entrance'][0] // 16, r['entrance'][1] // 16)
        if grid[seed[1]][seed[0]] == 0x0f:
            seed = min(((abs(x - seed[0]) + abs(y - seed[1]), x, y)
                        for y in range(th) for x in range(tw) if grid[y][x] == 0))[1:]
        reach = {seed}
        q = collections.deque([seed])
        while q:
            t = q.popleft()
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (t[0] + d[0], t[1] + d[1])
                if n not in reach and 0 <= n[0] < tw and 0 <= n[1] < th and grid[n[1]][n[0]] != 0x0f:
                    reach.add(n)
                    q.append(n)
        # Give the room monitor a moment to place them, then read the sprites
        # back out of the entity list - the table saying where a fuser goes
        # is not proof one is standing there.
        for _ in range(120):
            c.run_frame()
        live = {(r16(c, GENT + i * STRIDE + 0x2e) - r16(c, ROOM_CONTROLS + 6),
                 r16(c, GENT + i * STRIDE + 0x32) - r16(c, ROOM_CONTROLS + 8))
                for i in range(MAX_ENT)
                if c.memory.u8[GENT + i * STRIDE + 8] == NPC_KIND
                and c.memory.u8[GENT + i * STRIDE + 9] == ZELDA}
        msgs = []
        for f in rows:
            kid = f['kinstone']
            if (c.memory.u8[KIN + (kid >> 3)] >> (kid & 7)) & 1:
                msgs.append('KINSTONE_%02X is already fused on a fresh run - '
                            'its fuser can never be used' % kid)
        # Every spot the per-run scatter roll can hand out, not just the ones
        # this boot happened to use - the roll is a run-time value, so a bad
        # spot would only surface on some runs.
        spots = next((x['spots'] for x in P.fuser_spots()
                      if (x['area'], x['room']) == (area, room)), None)
        if spots is None:
            msgs.append('no scatter list for this region')
            spots = []
        # Tiles a live entity is standing on. A pot or an enemy STAMPS collision
        # onto the map, so a spot can read solid purely because something is
        # sitting on it - and which spot that is moves with the run's RNG, so
        # the check passed or failed by luck. Measured: Castle Garden's
        # (776,328) reads 0x00 on a bare room load and 0x1d once a hidden-
        # ladder grass pot has spawned on it. The map is the question here;
        # what is standing on it is not.
        occupied = set()
        for i in range(MAX_ENT):
            if c.memory.u8[GENT + i * STRIDE + 8] in (3, 6):  # ENEMY, OBJECT
                ex = r16(c, GENT + i * STRIDE + 0x2e) - r16(c, ROOM_CONTROLS + 6)
                ey = r16(c, GENT + i * STRIDE + 0x32) - r16(c, ROOM_CONTROLS + 8)
                occupied.add((ex // 16, ey // 16))
        for x, y in spots:
            tile = (x // 16, y // 16)
            if not (0 <= x < W and 0 <= y < H):
                msgs.append(f'scatter spot ({x},{y}) out of bounds {W}x{H}')
            elif grid[y // 16][x // 16] != 0 and tile not in occupied:
                msgs.append(f'scatter spot ({x},{y}) on non-open tile {grid[y // 16][x // 16]:#x}')
            elif (x // 16, y // 16) not in reach:
                msgs.append(f'scatter spot ({x},{y}) not in the entrance component')
        # And every un-fused fuser has to be standing on one of those spots,
        # one each. Counted by occupied spots rather than by total sprites:
        # the fusers borrow the ZELDA entity kind, and so do the ? room signs
        # and the region hint NPC, so "how many Zeldas are in the room" is not
        # the same question.
        used = [p for p in spots if p in live]
        if len(used) != len(rows):
            msgs.append(f'{len(rows)} un-fused fuser(s) but {len(used)} scatter spot(s) occupied')
        out.append(('FAIL', f'{rn}: ' + '; '.join(msgs)) if msgs
                   else ('PASS', f'{rn}: {len(rows)} fuser(s) un-fused, on {len(spots)} '
                                 f'verified scatter spots, spawned'))
    return out


def emu_rooms(rom, start, end):
    from emu import boot, warp, here, room_dims, coll_at, qs_set, qs_site_set, GENT, STRIDE, MAX_ENT, r16
    sites = P.content_sites_full()
    rooms = []
    seen = set()
    for idx, (an, rn, a, rm, cx, cy, gate) in enumerate(sites):
        key = (a, rm)
        if key not in seen:
            seen.add(key)
            rooms.append({'an': an, 'rn': rn, 'a': a, 'r': rm, 'spots': []})
        for rec in rooms:
            if (rec['a'], rec['r']) == key:
                rec['spots'].append((idx, cx, cy))
                rec.setdefault('gates', set())
                if gate:
                    rec['gates'].add(gate)
    for (an, rn), d in P.pool_doors().items():
        rooms.append({'an': an, 'rn': rn, 'a': d['area'], 'r': d['room'], 'spots': []})
    out = []
    for rec in rooms[start:end]:
        an, rn = rec['an'], rec['rn']
        if (an, rn) in KNOWN:
            out.append(('WARN', f'{rn}: skipped - {KNOWN[(an, rn)]}'))
            continue
        c = boot(rom, seed=SEED)
        c.memory.u8[0x03000bf0 + 4] = 0
        # A gated site does not exist until its fusion is done (Goron Cave's
        # four chambers), so fuse every gate this room needs before entering
        # or the site correctly refuses to spawn and the check reads as a
        # missing event. gSave.kinstones.fusedKinstones, which is
        # CheckKinstoneFused's own bitfield.
        for _g in sorted(rec.get('gates', ())):
            _b = 0x02002a40 + 0x114 + 301 + (_g >> 3)
            c.memory.u8[_b] |= 1 << (_g & 7)
        # Force every site in this room to the chest kind before entering, so
        # the same boot verifies both geometry and a live spawn.
        for idx, _cx, _cy in rec['spots']:
            base = idx * 13  # raw FLAG_BANK_12 offset - see qs_site_set
            qs_site_set(c, base, 1)
            for b in range(3):
                qs_site_set(c, base + 1 + b, (QS_EVENT_ITEM_DROP >> b) & 1)
            for b in range(8):
                qs_site_set(c, base + 4 + b, 0)
            qs_site_set(c, base + 12, 0)
        sx, sy = (rec['spots'][0][1], rec['spots'][0][2] + 24) if rec['spots'] else (120, 120)
        warp(c, rec['a'], rec['r'], sx, sy)
        for _ in range(150):
            c.run_frame()
        if here(c) != (rec['a'], rec['r']):
            out.append(('FAIL', f'{rn}: did not land ({here(c)})'))
            continue
        W, H = room_dims(c)
        msgs = []
        # BFS from the player over fully-open tiles.
        px = r16(c, 0x03001160 + 0x2e) - r16(c, 0x03000bf0 + 6)
        py = r16(c, 0x03001160 + 0x32) - r16(c, 0x03000bf0 + 8)
        tw, th = W // 16, H // 16
        grid = [[coll_at(c, tx, ty) for tx in range(tw)] for ty in range(th)]
        seedt = (max(0, min(px // 16, tw - 1)), max(0, min(py // 16, th - 1)))
        if grid[seedt[1]][seedt[0]] != 0:
            best = None
            for ty in range(th):
                for tx in range(tw):
                    if grid[ty][tx] == 0:
                        dd = abs(tx - seedt[0]) + abs(ty - seedt[1])
                        if best is None or dd < best[0]:
                            best = (dd, tx, ty)
            seedt = (best[1], best[2]) if best else None
        reach = set()
        if seedt:
            q = collections.deque([seedt])
            reach.add(seedt)
            while q:
                tx, ty = q.popleft()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nt = (tx + dx, ty + dy)
                    if nt not in reach and 0 <= nt[0] < tw and 0 <= nt[1] < th and grid[nt[1]][nt[0]] == 0:
                        reach.add(nt)
                        q.append(nt)
        # Full component labeling, needed for multi-site rooms (below).
        comp = {}
        for ty in range(th):
            for tx in range(tw):
                if grid[ty][tx] == 0 and (tx, ty) not in comp:
                    cid = len(comp)
                    q = collections.deque([(tx, ty)])
                    comp[(tx, ty)] = cid
                    while q:
                        x, y = q.popleft()
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            nt = (x + dx, y + dy)
                            if nt not in comp and 0 <= nt[0] < tw and 0 <= nt[1] < th and grid[nt[1]][nt[0]] == 0:
                                comp[nt] = comp[(x, y)]
                                q.append(nt)
        items = [(r16(c, GENT + i * STRIDE + 0x2e) - r16(c, 0x03000bf0 + 6),
                  r16(c, GENT + i * STRIDE + 0x32) - r16(c, 0x03000bf0 + 8))
                 for i in range(MAX_ENT)
                 if c.memory.u8[GENT + i * STRIDE + 8] == 6 and c.memory.u8[GENT + i * STRIDE + 9] == GROUND_ITEM_ID]
        # Reachability semantics depend on how many sites share the room.
        # Single-site rooms: the spot must sit in the component the player
        # arrives in. Multi-site rooms (the Boomerang chamber): each site is
        # entered by its OWN ladder into its own sealed segment, so instead
        # every spot must land in a DISTINCT open component - two sites
        # sharing a segment would put two events in one sub-area, which is
        # exactly the containment bug the per-site ownership code fixed.
        #
        # GATED sites are the exception, and they are why this rule cannot
        # simply be tightened. Goron Cave's four chambers are one room whose
        # sites are separated in TIME, not in topology: each is sealed until
        # its kinstone fusion punches the wall open, and this boot has fused
        # all of them so the player can be walked to every spot. Once fused
        # they are deliberately one connected shaft, so the distinct-segment
        # rule is meaningless for them. What keeps their content apart is the
        # gate plus per-site tile ownership, both checked directly elsewhere.
        gated = {idx for idx, _cx, _cy in rec['spots']} & {
            i for i, r in enumerate(P.content_sites_full())
            if r[6] and (r[2], r[3]) == (rec['a'], rec['r'])}
        multi = len(rec['spots']) > 1
        seen_comps = {}
        for idx, cx, cy in rec['spots']:
            if not (0 <= cx < W and 0 <= cy < H):
                msgs.append(f'site {idx} spot ({cx},{cy}) out of bounds {W}x{H}')
                continue
            if grid[cy // 16][cx // 16] != 0:
                msgs.append(f'site {idx} spot ({cx},{cy}) on solid tile')
            elif multi and not gated:
                cid = comp.get((cx // 16, cy // 16))
                if cid in seen_comps:
                    msgs.append(f'site {idx} spot ({cx},{cy}) shares a floor segment with site {seen_comps[cid]}')
                else:
                    seen_comps[cid] = idx
            elif (cx // 16, cy // 16) not in reach:
                msgs.append(f'site {idx} spot ({cx},{cy}) not in entrance component')
            if not any(abs(ix - cx) <= 48 and abs(iy - cy) <= 48 for ix, iy in items):
                msgs.append(f'site {idx}: forced chest spawned no GROUND_ITEM within 48px of ({cx},{cy})')
        out.append(('FAIL', f'{rn}: ' + '; '.join(msgs)) if msgs
                   else ('PASS', f'{rn}: landed, spots OK'
                                 + (f', {len(rec["spots"])} chest spawn(s) verified' if rec['spots'] else '')))
    return out



# Tower Floor 1's shop catalog, mirrored from game.c's own table. Kept here
# deliberately rather than parsed: this tier's job is to catch the table
# drifting off the floor it was measured against, and a parser that reads the
# same numbers it is checking cannot do that.
HUB_SHOP_SPOTS = [(64, 120), (96, 120), (128, 120), (160, 120),
                  (48, 88), (80, 88), (112, 88), (144, 88)]
# Slots 1 and 2 - ten arrows and ten bombs. Gated on owning the Bow / Bombs,
# so on a fresh run these two shelves are correctly empty.
HUB_SHOP_AMMO_SPOTS = [(96, 120), (128, 120)]
HUB_SHOP_WALKWAY_Y = 104
HUB_MERCHANT = (192, 104)
PLAYER_STATE = 0x03003f80
# Where the player arrives on the roof from Floor 3, and where its reward goes.
ROOF_ARRIVAL = (184, 328)
ROOF_REWARD = (120, 200)


def emu_hub(rom):
    """10 boots: the hub's shop floor.

    Every catalog prop must spawn where the table says AND actually lift from
    the walkway tile in front of it. Reasoning from the collision map is what
    made the old Stockwell layout take four attempts - two of them shipped
    with stock the player could see and not pick up - so this tier presses R
    and reads gPlayerState.heldObject instead.
    """
    import emu
    out = []
    c = emu.boot(rom, seed=SEED)
    emu.warp(c, 48, 1, 120, HUB_SHOP_WALKWAY_Y, frames=300)
    if emu.here(c) != (48, 1):
        return [('FAIL', f'could not reach the hub shop floor, landed in {emu.here(c)}')]
    ox = c.memory.u8[emu.ROOM_CONTROLS + 6] | (c.memory.u8[emu.ROOM_CONTROLS + 7] << 8)
    oy = c.memory.u8[emu.ROOM_CONTROLS + 8] | (c.memory.u8[emu.ROOM_CONTROLS + 9] << 8)
    placed = {(e[4] - ox, e[5] - oy) for e in emu.entities(c, emu.KIND_OBJECT)}
    missing = [s for s in HUB_SHOP_SPOTS if s not in placed and s not in HUB_SHOP_AMMO_SPOTS]
    if missing:
        out.append(('FAIL', f'shop props missing from {missing}'))
    else:
        out.append(('PASS', f'all {len(HUB_SHOP_SPOTS) - len(HUB_SHOP_AMMO_SPOTS)} '
                            'always-stocked shop props spawned on their table spots'))
    # The two ammo slots carry QS_REQ_BOW / QS_REQ_BOMBS and a fresh run holds
    # neither weapon, so they are SUPPOSED to be bare here. Asserting that is
    # the only cheap check available that the requirement is wired at all - if
    # they spawn, ten arrows are on sale to a player with no bow.
    early = [s for s in HUB_SHOP_AMMO_SPOTS if s in placed]
    if early:
        out.append(('FAIL', f'ammo on sale with no weapon to use it: {early}'))
    else:
        out.append(('PASS', 'the two ammo slots stand bare until the run finds the weapon'))
    npcs = [(e[4] - ox, e[5] - oy) for e in emu.entities(c, emu.KIND_NPC)]
    if HUB_MERCHANT not in npcs:
        out.append(('FAIL', f'merchant not at {HUB_MERCHANT}; NPCs at {npcs}'))
    else:
        out.append(('PASS', f'merchant standing at {HUB_MERCHANT}'))

    unliftable = []
    for (ix, iy) in HUB_SHOP_SPOTS:
        if (ix, iy) in HUB_SHOP_AMMO_SPOTS:
            continue
        cc = emu.boot(rom, seed=SEED)
        emu.warp(cc, 48, 1, ix, HUB_SHOP_WALKWAY_Y, frames=240)
        if emu.here(cc) != (48, 1):
            unliftable.append((ix, iy))
            continue
        key = cc.KEY_UP if iy < HUB_SHOP_WALKWAY_Y else cc.KEY_DOWN
        for _ in range(10):
            cc.set_keys(key)
            cc.run_frame()
        cc.clear_keys(key)
        for _ in range(10):
            cc.run_frame()
        for _ in range(10):
            emu.press(cc, cc.KEY_R, 4, 6)
            if cc.memory.u8[PLAYER_STATE + 5]:
                break
        if not cc.memory.u8[PLAYER_STATE + 5]:
            unliftable.append((ix, iy))
    if unliftable:
        out.append(('FAIL', f'shop stock that will not lift from the walkway: {unliftable}'))
    else:
        out.append(('PASS', 'every shop item lifts from the walkway in front of it'))

    # The roof wave. Its offsets are hand-placed inside one measured component,
    # and the failure that matters is an enemy landing outside it - the roof's
    # top rows are open tiles the player cannot reach, so a spot that drifts up
    # there is a wave that can never be cleared and a reward never earned.
    cc = emu.boot(rom, seed=SEED)
    emu.warp(cc, 49, 0, ROOF_ARRIVAL[0], ROOF_ARRIVAL[1], frames=90)
    if emu.here(cc) != (49, 0):
        out.append(('FAIL', f'could not reach the tower roof, landed in {emu.here(cc)}'))
        return out
    ox = cc.memory.u8[emu.ROOM_CONTROLS + 6] | (cc.memory.u8[emu.ROOM_CONTROLS + 7] << 8)
    oy = cc.memory.u8[emu.ROOM_CONTROLS + 8] | (cc.memory.u8[emu.ROOM_CONTROLS + 9] << 8)
    w, h = emu.room_dims(cc)
    tw, th = w // 16, h // 16
    grid = [[emu.coll_at(cc, tx, ty) for tx in range(tw)] for ty in range(th)]
    seen = {(ROOF_ARRIVAL[0] // 16, ROOF_ARRIVAL[1] // 16)}
    queue = collections.deque(seen)
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < tw and 0 <= ny < th and (nx, ny) not in seen and grid[ny][nx] == 0:
                seen.add((nx, ny))
                queue.append((nx, ny))
    foes = [(e[4] - ox, e[5] - oy) for e in emu.entities(cc, emu.KIND_ENEMY)]
    if not foes:
        out.append(('FAIL', 'the roof wave did not spawn'))
    else:
        stray = [p for p in foes if (p[0] // 16, p[1] // 16) not in seen]
        if stray:
            out.append(('FAIL', f'roof enemies outside the reachable component: {stray}'))
        else:
            out.append(('PASS', f'roof wave: {len(foes)} enemies, all inside the '
                                f'{len(seen)}-tile reachable component'))
    # And the reward lands on its spot once the wave is gone.
    for e in emu.entities(cc, emu.KIND_ENEMY):
        cc.memory.u8[emu.GENT + e[0] * emu.STRIDE + emu.ENT_KIND] = 0
    for _ in range(120):
        cc.run_frame()
    drops = [(e[4] - ox, e[5] - oy) for e in emu.entities(cc, emu.KIND_OBJECT, emu.GROUND_ITEM_ID)]
    if ROOF_REWARD not in drops:
        out.append(('FAIL', f'no roof reward at {ROOF_REWARD} after the clear; ground items: {drops}'))
    else:
        out.append(('PASS', f'roof reward dropped at {ROOF_REWARD}'))
    return out


def main():
    rom = 'tmc.gba'
    args = sys.argv[1:]
    if '--rom' in args:
        rom = args[args.index('--rom') + 1]
    global SEED
    if '--seed' in args:
        SEED = int(args[args.index('--seed') + 1], 0)
    if '--batch-rooms' in args:
        i = args.index('--batch-rooms')
        res = emu_rooms(rom, int(args[i + 1]), int(args[i + 2]))
        print(json.dumps(res))
        return 0
    results = [('static', check_static()), ('flags', check_flags())]
    if '--static-only' not in args:
        if '--rooms' not in args:
            results.append(('regions', emu_regions(rom)))
            results.append(('pool entrances', emu_pool_entrances(rom)))
            results.append(('fusers', emu_fusers(rom)))
            results.append(('hub', emu_hub(rom)))
        if '--gfx' in args or ('--rooms' not in args and '--regions' not in args):
            results.append(('gfx budget', emu_gfx_budget(rom)))
        if '--regions' not in args:
            n_rooms = len({(a, r) for _, _, a, r, _, _ in P.content_sites()}) + len(P.pool_doors()) + 1
            batch = []
            for s in range(0, n_rooms + 6, 6):
                cmd = [sys.executable, os.path.abspath(__file__), '--rom', rom,
                       '--batch-rooms', str(s), str(s + 6)]
                if SEED is not None:
                    cmd += ['--seed', str(SEED)]
                pr = subprocess.run(cmd, capture_output=True, text=True)
                try:
                    batch += json.loads(pr.stdout.strip().split('\n')[-1])
                except Exception:
                    batch.append(('FAIL', f'batch {s}: subprocess error: {pr.stderr[-300:]}'))
            results.append(('rooms', batch))
    fails = 0
    if any(t != 'static' and t != 'flags' for t, _ in results):
        print(f'seed: {"0x%08x (pinned)" % SEED if SEED is not None else "derived (re-run with --seed to vary)"}')
    for tier, res in results:
        print(f'== {tier} ==')
        for lvl, msg in res:
            print(f'  [{lvl}] {msg}')
            fails += (lvl == 'FAIL')
    print(f'\n{"FAILED" if fails else "OK"}: {fails} failure(s)')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
