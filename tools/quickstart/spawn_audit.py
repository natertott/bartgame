"""Where do the ? room waves actually put their enemies?

The user, after a playthrough: "Some of the ? rooms have enemies that are
spawning into the very corner of the room, usually the upper-right corner.
This is affecting the winability of certain ? events like three wave clear
rooms. Do an audit on all of the eligible ? rooms to see where enemies spawn
and make sure that they are spawning in the walkable part of the room."

One boot per eligible content site (SMALL/LARGE/ANY kinds, no kinstone
gate) through the scenario testbed, forced to the WAVES event, with a full
kit so the fight does not end the measurement. The run is stepped ONE FRAME
AT A TIME from the landing and every enemy is recorded on the frame it
appears, so the tile written down is the tile the placer chose and not
wherever the body wandered to.

Each enemy is then checked against three things, all asked of the shipped C
rather than of a Python model of it:

  REACH   QuickStartMarkReachableTiles seeded from the player's own tile:
          is the enemy on ground the player can walk to?
  OPEN    QuickStartTileIsOpen: collision 0 (the placer's own test).
  EDGE    is the tile on the room rectangle's outermost row/column, or
          one in from it? A legitimate chamber tile is almost never there;
          the void outside a cave's walls very often is.

Usage: python3 tools/quickstart/spawn_audit.py [--rom tmc-d3.gba] [--out DIR]
                                               [--sites 4,5,16] [--kit 2] [--diff 5]

For every flagged room an ASCII map and a screenshot land in DIR. Exit 0
when no enemy is flagged, 1 otherwise, 2 if nothing spawned anywhere (a
probe that measured nothing proves nothing).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import r16, entities, snap, KIND_ENEMY, GENT, STRIDE, MAX_ENT, ENT_KIND, ENT_ID, ENT_X, ENT_Y
import scenario as S
import parse_tables as P
import callrom as C

PLAYER = 0x03001160
ROOM_CONTROLS = 0x03000bf0
SCRATCH = 0x0203E000
SCRATCH_OPEN = 0x0203E400
WAVES = S.EVENTS.index('WAVES')


def eligible_sites():
    """(index, areaName, roomName, area, room, cx, cy) for every site a ?
    room event may be dealt to (the same test as QuickStartMemorySiteEligible)."""
    src = P.GAME
    i = src.find('sQuickStartRoomContentSites[QUICKSTART_CONTENT_SITE_COUNT] = {')
    j = src.find('\n};', i)
    rows = re.findall(r'\{ (AREA_\w+), (ROOM_\w+), (\w+), ([0-9xa-fA-F]+),\s*\n?\s*([0-9xa-fA-F]+)', src[i:j])
    full = P.content_sites_full()
    out = []
    for n, (an, rn, kinds, cx, cy) in enumerate(rows):
        if kinds not in ('QUICKSTART_KINDS_SMALL', 'QUICKSTART_KINDS_LARGE', 'QUICKSTART_KINDS_ANY'):
            continue
        if full[n][6] != 0:
            continue
        out.append((n, an, rn, P.AREAS[an], P.ROOMS[rn], int(cx, 0), int(cy, 0)))
    return out


def bit(c, base, tx, ty):
    i = (ty << 6) | tx
    return (c.memory.u8[base + (i >> 3)] >> (i & 7)) & 1


def origin(c):
    return r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)


def flood(c, seedTX, seedTY):
    """QuickStartMarkReachableTiles seeded from a tile: (reach set, open set)."""
    w = r16(c, ROOM_CONTROLS + 0x1e) >> 4
    h = r16(c, ROOM_CONTROLS + 0x20) >> 4
    C.call_keep(c, C.game_sym('QuickStartMarkReachableTiles'), (SCRATCH, SCRATCH_OPEN, seedTX, seedTY),
                budget=3200000)
    W, H = min(w, 64), min(h, 64)
    reach = {(x, y) for y in range(H) for x in range(W) if bit(c, SCRATCH, x, y)}
    opn = {(x, y) for y in range(H) for x in range(W) if bit(c, SCRATCH_OPEN, x, y)}
    return reach, opn


def player_tile(c):
    ox, oy = origin(c)
    return (r16(c, PLAYER + 0x2e) - ox) >> 4, (r16(c, PLAYER + 0x32) - oy) >> 4


def kill_all(c):
    """Clear every enemy the way the wave counter sees it (the kind byte;
    a health write leaves some kinds standing)."""
    for i in range(MAX_ENT):
        b = GENT + i * STRIDE
        if c.memory.u8[b + ENT_KIND] == KIND_ENEMY:
            c.memory.u8[b + ENT_KIND] = 0


def audit_site(rom, site, kit, diff, waves=3, frames=2400):
    n, an, rn, area, room, cx, cy = site
    c = S.boot(rom, S.KINDS['SITE'], n, WAVES, 0, 0, kit=kit, diff=diff, frames=0)
    seen = set()
    spawns = []  # per wave: list of dicts
    wave = []
    last = None
    quiet = 0
    for f in range(frames):
        c.run_frame()
        if (c.memory.u8[ROOM_CONTROLS + 4], c.memory.u8[ROOM_CONTROLS + 5]) != (area, room):
            continue
        ox, oy = origin(c)
        fresh = []
        for i in range(MAX_ENT):
            b = GENT + i * STRIDE
            if c.memory.u8[b + ENT_KIND] != KIND_ENEMY:
                seen.discard(i)
                continue
            if i in seen:
                continue
            seen.add(i)
            fresh.append((i, c.memory.u8[b + ENT_ID], (r16(c, b + ENT_X) - ox) >> 4, (r16(c, b + ENT_Y) - oy) >> 4))
        if fresh:
            # Only the player's tile is taken now. The flood it implies is
            # computed after the run: calling into the ROM between frames
            # of a wave that is still being dealt loses the rest of the
            # wave (measured - the second kind never arrived, nor did the
            # next wave), and the room's geometry does not change.
            ptx, pty = player_tile(c)
            for (i, ident, tx, ty) in fresh:
                wave.append({'frame': f, 'id': ident, 'tx': tx, 'ty': ty, 'player': (ptx, pty)})
            last = f
            quiet = 0
        elif wave:
            quiet += 1
            if quiet > 120:
                spawns.append(wave)
                wave = []
                if len(spawns) >= waves:
                    break
                kill_all(c)
    if wave:
        spawns.append(wave)
    here = (c.memory.u8[ROOM_CONTROLS + 4], c.memory.u8[ROOM_CONTROLS + 5])
    if here != (area, room):
        return {'site': site, 'error': 'landed in %s not %s' % (here, (area, room))}
    w = r16(c, ROOM_CONTROLS + 0x1e) >> 4
    h = r16(c, ROOM_CONTROLS + 0x20) >> 4
    ptx, pty = player_tile(c)
    reach, opn = flood(c, ptx, pty)
    chamber, _ = flood(c, cx >> 4, cy >> 4)
    if not reach:
        # The player's seed failed (a doorway walled on four sides); the
        # placer floods from the content spot in that case, so judge by
        # the same set.
        reach = chamber
    # The placer's own view at each spawn: the flood seeded from where the
    # player stood, and whether the placer trusts it (non-empty and holding
    # the anchor - see QuickStartSpawnEnemiesOnOpenTiles).
    floods = {}
    for wv in spawns:
        for e in wv:
            if e['player'] not in floods:
                floods[e['player']] = flood(c, *e['player'])[0]
            r = floods[e['player']]
            e['usable'] = bool(r) and (cx >> 4, cy >> 4) in r
            e['inPlayerFlood'] = (e['tx'], e['ty']) in r
            tx, ty = e['tx'], e['ty']
            inside = 0 <= tx < w and 0 <= ty < h
            e['reach'] = inside and (tx, ty) in reach
            e['open'] = inside and (tx, ty) in opn
            e['chamber'] = inside and (tx, ty) in chamber
            e['edge'] = (not inside) or tx <= 1 or ty <= 1 or tx >= w - 2 or ty >= h - 2
            tags = []
            if not e['open']:
                tags.append('SOLID')
            elif not e['reach'] and not e['chamber']:
                tags.append('VOID')
            elif not e['reach']:
                tags.append('UNREACH')
            if e['edge']:
                tags.append('RIM')
            e['tags'] = tags
            e['flag'] = bool(tags)
    return {
        'site': site, 'w': w, 'h': h, 'player': (ptx, pty), 'content': (cx >> 4, cy >> 4),
        'reach': reach, 'open': opn, 'chamber': chamber, 'waves': spawns,
        'enemies': [e for wv in spawns for e in wv], 'core': c,
    }


def ascii_map(res):
    w, h = min(res['w'], 64), min(res['h'], 64)
    grid = [['#'] * w for _ in range(h)]
    for (x, y) in res['open']:
        grid[y][x] = '.'
    for (x, y) in res['reach']:
        grid[y][x] = ','
    cx, cy = res['content']
    if 0 <= cx < w and 0 <= cy < h:
        grid[cy][cx] = 'C'
    px, py = res['player']
    if 0 <= px < w and 0 <= py < h:
        grid[py][px] = 'P'
    for e in res['enemies']:
        if 0 <= e['tx'] < w and 0 <= e['ty'] < h:
            grid[e['ty']][e['tx']] = 'X' if e['flag'] else 'e'
    return '\n'.join(''.join(r) for r in grid)


def main(argv):
    rom = 'tmc-d3.gba'
    out = None
    only = None
    kit, diff = 2, 5
    if '--rom' in argv:
        rom = argv[argv.index('--rom') + 1]
    if '--out' in argv:
        out = argv[argv.index('--out') + 1]
        os.makedirs(out, exist_ok=True)
    if '--sites' in argv:
        only = {int(x) for x in argv[argv.index('--sites') + 1].split(',')}
    if '--kit' in argv:
        kit = int(argv[argv.index('--kit') + 1])
    if '--diff' in argv:
        diff = int(argv[argv.index('--diff') + 1])
    sites = eligible_sites()
    if only is not None:
        sites = [s for s in sites if s[0] in only]
    total = flagged = 0
    flagged_rooms = []
    for site in sites:
        res = audit_site(rom, site, kit, diff)
        n, an, rn = site[0], site[1][5:], site[2][5:]
        if 'error' in res:
            print('%3d %-45s ERROR %s' % (n, rn, res['error']))
            sys.stdout.flush()
            continue
        es = res['enemies']
        bad = [e for e in es if e['flag']]
        total += len(es)
        flagged += len(bad)
        unreach = len(res['open']) - len(res['reach'])
        trust = ''.join('u' if any(e['usable'] for e in wv) else 'U' for wv in res['waves'])
        print('%3d %-45s %2dx%-2d player %-6s content %-6s waves %-8s trust %-3s flagged %d  void %3d%s' % (
            n, rn, res['w'], res['h'], '%d,%d' % res['player'], '%d,%d' % res['content'],
            '/'.join(str(len(wv)) for wv in res['waves']), trust, len(bad), unreach,
            ('  ' + ' '.join('%s@%d,%d:%s' % (hex(e['id']), e['tx'], e['ty'], '+'.join(e['tags']))
                             for e in bad)) if bad else ''))
        sys.stdout.flush()
        if bad or not es:
            flagged_rooms.append(n)
            if out:
                with open(os.path.join(out, 'site%03d_%s.txt' % (n, rn)), 'w') as fh:
                    fh.write('site %d %s/%s %dx%d player %s content %s\n' % (n, an, rn, res['w'], res['h'],
                                                                         res['player'], res['content']))
                    fh.write('# solid  . open-unreachable  , reachable  P player  C content  e enemy  X flagged\n')
                    fh.write(ascii_map(res) + '\n')
                    for e in es:
                        fh.write('%r\n' % e)
                snap(res['core'], os.path.join(out, 'site%03d_%s.png' % (n, rn)))
    print()
    print('%d sites, %d enemies, %d flagged (unreachable or on the rim); rooms: %s' % (
        len(sites), total, flagged, flagged_rooms))
    if total == 0:
        return 2
    return 1 if flagged else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
