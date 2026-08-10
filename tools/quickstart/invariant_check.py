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
LADDER_KIND_CHEST = 0


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

    # The reward pool, which had two separate ways to go quietly wrong.
    #
    # 1. The size must be a POWER OF TWO. agbcc turns "% 8" into a mask but
    #    emits __umodsi3 for "% 6", and its runtime lib has no such symbol -
    #    so a non-power-of-two size does not misbehave at runtime, it fails
    #    to link, with an error pointing at an unrelated function.
    # 2. ITEM_BOW must be in it, and must come before ITEM_LARGE_QUIVER. The
    #    quiver is a pure quiverType++ upgrade (itemUtils.c case 0xa) and does
    #    nothing at all without a Bow, so a pool carrying the upgrade and not
    #    the weapon hands out dud rewards - which is exactly what shipped
    #    once the Bow stopped being a boot grant.
    m = re.search(r'#define QUICKSTART_LADDER_REWARD_POOL_SIZE (\d+)', game)
    i = game.find('sQuickStartLadderRewardPool[] = {')
    j = game.find('\n};', i)
    entries = re.findall(r'ITEM_\w+', game[i:j])
    n = int(m.group(1))
    if n != len(entries):
        out.append(('FAIL', f'QUICKSTART_LADDER_REWARD_POOL_SIZE={n} vs {len(entries)} entries'))
    elif n & (n - 1):
        out.append(('FAIL', f'reward pool size {n} is not a power of two (agbcc has no __umodsi3)'))
    elif 'ITEM_BOW' not in entries:
        out.append(('FAIL', 'reward pool has no ITEM_BOW; quivers would be dud drops'))
    elif 'ITEM_LARGE_QUIVER' in entries and entries.index('ITEM_LARGE_QUIVER') < entries.index('ITEM_BOW'):
        out.append(('FAIL', 'reward pool lists ITEM_LARGE_QUIVER before ITEM_BOW'))
    else:
        out.append(('PASS', f'reward pool: {n} entries, power of two, Bow present'))

    # The lottery prize field has to be wide enough for the pool. It is
    # derived from the pool size rather than written out, so this is really
    # checking that nobody has un-derived it - which is exactly how it went
    # wrong before: the mask was a literal 3, the pool doubled, and the two
    # silently disagreed. A too-narrow field does not fail to build, it just
    # makes the top half of the pool unreachable from lotteries and, in the
    # pot room, bleeds the spilled bit into the winner field.
    src = game[game.find('#define QUICKSTART_LOTTERY_PRIZE_MASK'):][:200]
    if 'QUICKSTART_LADDER_REWARD_POOL_SIZE - 1' not in src:
        out.append(('FAIL', 'QUICKSTART_LOTTERY_PRIZE_MASK is not derived from the pool size'))
    else:
        # Prize occupies bits [shift, shift+bits); the pot room's winner field
        # starts at QUICKSTART_POT_WINNER_SHIFT. They must not overlap, and
        # the whole thing must fit in the 8-bit stored `extra`.
        shift = int(re.search(r'#define QUICKSTART_LOTTERY_PRIZE_SHIFT (\d+)', game).group(1))
        win = int(re.search(r'#define QUICKSTART_POT_WINNER_SHIFT (\d+)', game).group(1))
        buckets = int(re.search(r'#define QUICKSTART_POT_WINNER_BUCKETS (\d+)', game).group(1))
        bits = n.bit_length() - 1
        top = win + (buckets.bit_length() - 1)
        if shift + bits > win:
            out.append(('FAIL', f'lottery prize field (bits {shift}-{shift+bits-1}) '
                                f'overlaps the pot winner field at bit {win}'))
        elif top > 8:
            out.append(('FAIL', f'pot lottery extra needs {top} bits, only 8 are stored'))
        else:
            out.append(('PASS', f'lottery extra: prize bits {shift}-{shift+bits-1}, '
                                f'pot winner bits {win}-{top-1}, fits in 8'))
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
                qs_set(c, base + 1 + b, (LADDER_KIND_CHEST >> b) & 1)
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
