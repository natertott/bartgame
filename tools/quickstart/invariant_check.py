"""QUICKSTART invariant checker (roadmap Phase A1).

Machine-validates every placement-bearing table after a build. The failure
class it exists for: hand-placed coordinates that are wrong for the room
they name - the cause of six separate shipped bugs (region exit box outside
its room, content spots below the floor, unmeasured shared entrances, shop
stock in a sealed alcove, spawn offsets inside walls).

Tiers:
  static    source-only: door tags on every 2-door pool room, pool size
            constants consistent with their arrays. Always runs.
  regions   5 emulator boots: each region row's entrance/reward on open
            ground, exit box inside room bounds and off the border row.
  pool      20 boots: every 2-door pool row's entrance is real open floor
  entrances (not solid, not water) and its content spot is in bounds.
  gfx       20 boots: no region runs the 44-slot GFX table below its
  budget    reserve at any difficulty (a full table drops sprites).
  hub       10 boots: every shop item on the hub's Floor 1 spawns where
            its table says and lifts from the walkway in front of it.
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
                 [--static-only | --regions | --rooms]
Runs everything by default. Batches emulator work across subprocesses
because mgba leaks a core per boot and corrupts the allocator eventually.
Exit code 0 = all PASS/WARN, 1 = any FAIL.
"""
import sys, os, json, subprocess, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse_tables as P

# Rooms that are expected not to be reachable and why - reported WARN.
KNOWN = {
    ('AREA_HYRULE_CASTLE_CELLAR', 'ROOM_HYRULE_CASTLE_CELLAR_0'):
        'shadowed by the Castle Garden NW ladder redirect (survey finding #1)',
}
GROUND_ITEM_ID = 0
QS_EVENT_ITEM_DROP = 0


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
        c = boot(rom)
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
            c = boot(rom)
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
        c = boot(rom)
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
        c = boot(rom)
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
        for x, y in spots:
            if not (0 <= x < W and 0 <= y < H):
                msgs.append(f'scatter spot ({x},{y}) out of bounds {W}x{H}')
            elif grid[y // 16][x // 16] != 0:
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
    from emu import boot, warp, here, room_dims, coll_at, qs_set, GENT, STRIDE, MAX_ENT, r16
    sites = P.content_sites()
    rooms = []
    seen = set()
    for idx, (an, rn, a, rm, cx, cy) in enumerate(sites):
        key = (a, rm)
        if key not in seen:
            seen.add(key)
            rooms.append({'an': an, 'rn': rn, 'a': a, 'r': rm, 'spots': []})
        for rec in rooms:
            if (rec['a'], rec['r']) == key:
                rec['spots'].append((idx, cx, cy))
    for (an, rn), d in P.pool_doors().items():
        rooms.append({'an': an, 'rn': rn, 'a': d['area'], 'r': d['room'], 'spots': []})
    out = []
    for rec in rooms[start:end]:
        an, rn = rec['an'], rec['rn']
        if (an, rn) in KNOWN:
            out.append(('WARN', f'{rn}: skipped - {KNOWN[(an, rn)]}'))
            continue
        c = boot(rom)
        c.memory.u8[0x03000bf0 + 4] = 0
        # Force every site in this room to the chest kind before entering, so
        # the same boot verifies both geometry and a live spawn.
        for idx, _cx, _cy in rec['spots']:
            base = 266 + idx * 13
            qs_set(c, base, 1)
            for b in range(3):
                qs_set(c, base + 1 + b, (QS_EVENT_ITEM_DROP >> b) & 1)
            for b in range(8):
                qs_set(c, base + 4 + b, 0)
            qs_set(c, base + 12, 0)
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
        multi = len(rec['spots']) > 1
        seen_comps = {}
        for idx, cx, cy in rec['spots']:
            if not (0 <= cx < W and 0 <= cy < H):
                msgs.append(f'site {idx} spot ({cx},{cy}) out of bounds {W}x{H}')
                continue
            if grid[cy // 16][cx // 16] != 0:
                msgs.append(f'site {idx} spot ({cx},{cy}) on solid tile')
            elif multi:
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
HUB_SHOP_SPOTS = [(48, 88), (80, 88), (112, 88), (144, 88), (176, 88),
                  (64, 120), (96, 120), (128, 120), (160, 120)]
HUB_SHOP_WALKWAY_Y = 104
HUB_MERCHANT = (192, 104)
PLAYER_STATE = 0x03003f80


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
    c = emu.boot(rom)
    emu.warp(c, 48, 1, 120, HUB_SHOP_WALKWAY_Y, frames=300)
    if emu.here(c) != (48, 1):
        return [('FAIL', f'could not reach the hub shop floor, landed in {emu.here(c)}')]
    ox = c.memory.u8[emu.ROOM_CONTROLS + 6] | (c.memory.u8[emu.ROOM_CONTROLS + 7] << 8)
    oy = c.memory.u8[emu.ROOM_CONTROLS + 8] | (c.memory.u8[emu.ROOM_CONTROLS + 9] << 8)
    placed = {(e[4] - ox, e[5] - oy) for e in emu.entities(c, emu.KIND_OBJECT)}
    missing = [s for s in HUB_SHOP_SPOTS if s not in placed]
    if missing:
        out.append(('FAIL', f'shop props missing from {missing}'))
    else:
        out.append(('PASS', f'all {len(HUB_SHOP_SPOTS)} shop props spawned on their table spots'))
    npcs = [(e[4] - ox, e[5] - oy) for e in emu.entities(c, emu.KIND_NPC)]
    if HUB_MERCHANT not in npcs:
        out.append(('FAIL', f'merchant not at {HUB_MERCHANT}; NPCs at {npcs}'))
    else:
        out.append(('PASS', f'merchant standing at {HUB_MERCHANT}'))

    unliftable = []
    for (ix, iy) in HUB_SHOP_SPOTS:
        cc = emu.boot(rom)
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
    return out


def main():
    rom = 'tmc.gba'
    args = sys.argv[1:]
    if '--rom' in args:
        rom = args[args.index('--rom') + 1]
    if '--batch-rooms' in args:
        i = args.index('--batch-rooms')
        res = emu_rooms(rom, int(args[i + 1]), int(args[i + 2]))
        print(json.dumps(res))
        return 0
    results = [('static', check_static())]
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
                pr = subprocess.run([sys.executable, os.path.abspath(__file__), '--rom', rom,
                                     '--batch-rooms', str(s), str(s + 6)],
                                    capture_output=True, text=True)
                try:
                    batch += json.loads(pr.stdout.strip().split('\n')[-1])
                except Exception:
                    batch.append(('FAIL', f'batch {s}: subprocess error: {pr.stderr[-300:]}'))
            results.append(('rooms', batch))
    fails = 0
    for tier, res in results:
        print(f'== {tier} ==')
        for lvl, msg in res:
            print(f'  [{lvl}] {msg}')
            fails += (lvl == 'FAIL')
    print(f'\n{"FAILED" if fails else "OK"}: {fails} failure(s)')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
