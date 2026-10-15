"""Generate the portal ? room tables (docs/QUICKSTART_PORTAL_POCKETS.md).

A portal pair is two win-chain steps: an EVENT at a ? room the player can
reach (portal A), whose warp point wakes when the room is cleared, then an
ITEM step for the pocket's escape item, paid by the next prize won inside
the pocket. This writes the two tables the ROM and the simulator share:

  pockets  where each portal lands, how the player gets out, what pays
           the escape item and what counts as inside (POCKETS below,
           chosen and walked by hand: portal_probe.py)
  tiles    per ? room site alone in its room (build/block_rooms.json), the
           tile its portal stands on: plain floor joined to the arrival,
           open on all four sides, three tiles or more from the arrival,
           clear of the doors, the room's edges, the reserved tiles and the
           prize spot's ring, as near the middle of the floor as it gets

The captured floor does not hold the room's own objects, and a pot or a
statue is as solid as a wall: a portal under the Heart Piece hallway's
pots could not be stood on (portal_probe.py --sweep). So the tiles also
read build/portal_census.json (portal_probe.py --census, measured in the
ROM): no portal on or beside an object, joined to the arrival around
them. And none in a room the player enters Minish-sized (every MINISH
area and the beanstalks): the testbed lands a full-size player there, and
two Minish houses failed the sweep (the pad was never reached, or never
dealt).

Writes include/quickstart/portals.h.

    python3 tools/quickstart/portal_rooms.py [--check]
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_tables as P
from block_puzzles import Floor, ROOMS, DIRS

OUT_H = os.path.join(P.ROOT, 'include', 'quickstart', 'portals.h')
CENSUS = os.path.join(P.ROOT, 'build', 'portal_census.json')

# Sites whose ? room never gets past its first frame (lantern_rooms.py
# BROKEN_SITES): never a portal's either end.
BROKEN_SITES = {47, 65}
# Portal A deals a fight, and these rooms' wave room spawns nobody: the
# prize drops with no fight at all (portal_probe.py --sweep, the Veil Falls
# cave's 1F hallway). A known defect of the site, logged in the roadmap.
NO_FIGHT_SITES = {107}
OPEN_KINDS = {'ANY', 'LARGE', 'SMALL'}
KEEP_CLEAR = 3                 # tiles (Manhattan) from the arrival

# The pockets, in table order. `node` is the reach node the flood is seeded
# with while the portal is lit (portal_pockets.NAMES), None when the pocket
# is rooms inside a node the mainland already holds; `land_site` lands the
# player on that site's portal tile (two-way: the return pad stands there);
# `inside` is what counts as the pocket for the payout, a room of None
# meaning the whole area.
#
# Veil Falls' plateau is the doc's fourth pocket and is not built: nothing
# on it pays a prize with the boot kit. Its region row is barred from
# paying a clear (QuickStartRegionAllowsWave) and its ? rooms want the
# Lantern or the Grip Ring.
POCKETS = [
    dict(name='WR', label='the Wind Ruins', node='WR', two_way=False,
         land=('AREA_RUINS', 'ROOM_RUINS_ENTRANCE', 216 // 16, 456 // 16), land_site=None,
         escape=('ITEM_PEGASUS_BOOTS', 'ITEM_ROCS_CAPE'),
         inside=[('AREA_RUINS', None)]),
    dict(name='CW', label='Castor Wilds, the far bank', node=None, two_way=True,
         land=None, land_site=70,
         escape=('ITEM_PEGASUS_BOOTS', 'ITEM_ROCS_CAPE'),
         inside=[('AREA_CASTOR_DARKNUT', 'ROOM_CASTOR_DARKNUT_MAIN'),
                 ('AREA_CASTOR_CAVES', 'ROOM_CASTOR_CAVES_DARKNUT')]),
    dict(name='LH', label='the Lake Hylia ladder pocket', node='LH-LADDER', two_way=True,
         land=None, land_site=88,
         escape=('ITEM_FLIPPERS', None),
         inside=[('AREA_HOUSE_INTERIORS_4', 'ROOM_HOUSE_INTERIORS_4_MAYOR_LAKE_CABIN')]),
]
NODE_NAMES = ['SHF', 'SHF@NNE', 'SHF@NNW', 'EH-N', 'EH-C', 'EH-S', 'LLR', 'LLR@E903', 'LLR@E445', 'LLR@E750',
              'LLR@W', 'LLR@NW', 'LLR@N', 'LLR@POCKET', 'NHF', 'NHF@VF', 'CG', 'RV', 'TRIL', 'TRIL@S', 'TRIL@E',
              'TRIL@N', 'WW-N', 'WW-N@W', 'WW-N@S', 'WW-N@E', 'WW-C', 'WW-S', 'CW', 'WR', 'HT', 'CREN', 'MW', 'LH',
              'MV', 'LH-CREST', 'LH-SW', 'LH-LADDER', 'CREN-BASE', 'VF', 'VF@NHF', 'VF@LLR', 'VF@POCKET']


def portal_tile(floor, objects=()):
    """The tile a portal stands on, or None."""
    from block_puzzles import flood
    sx, sy = floor.start
    # Something stands on the arrival tile in a few rooms as the census
    # lands (the player's own effects): never an obstacle.
    objects = [o for o in objects if tuple(o) != floor.start]
    near_obj = {(x + dx, y + dy) for (x, y) in objects for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    walk = flood(floor.comp - set(map(tuple, objects)), floor.start)
    spot = (floor.r['spot'][0] // 16, floor.r['spot'][1] // 16)
    near_key = {(x + dx, y + dy) for (x, y) in floor.keys for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    cands = []
    for t in floor.comp & floor.ground:
        x, y = t
        if abs(x - sx) + abs(y - sy) < KEEP_CLEAR or t in near_key or t in near_obj or t not in walk:
            continue
        if abs(x - spot[0]) <= 1 and abs(y - spot[1]) <= 1:
            continue
        if not all((x + dx, y + dy) in floor.comp for dx, dy in DIRS):
            continue
        cands.append(t)
    if not cands:
        return None
    cx = sum(x for x, _ in floor.comp) / len(floor.comp)
    cy = sum(y for _, y in floor.comp) / len(floor.comp)
    return min(cands, key=lambda t: ((t[0] - cx) ** 2 + (t[1] - cy) ** 2, t[1], t[0]))


def tiles():
    rooms = json.load(open(ROOMS))
    census = {int(k): v for k, v in json.load(open(CENSUS)).items()}
    land_sites = {p['land_site'] for p in POCKETS if p['land_site'] is not None}
    out = {}
    for key in sorted((k for k in rooms if k.startswith('site:')), key=lambda k: int(k.split(':')[1])):
        site = int(key.split(':')[1])
        r = rooms[key]
        if site in BROKEN_SITES or site in NO_FIGHT_SITES or (r['kinds'] not in OPEN_KINDS and site not in land_sites):
            continue
        seen = census.get(site)
        # Minish-sized rooms by area: the testbed lands a full-size player
        # there, so the census's own Minish reading is not the player's
        if seen is None or seen['minish'] or 'MINISH' in r['area'] or r['area'] == 'AREA_BEANSTALKS':
            continue
        t = portal_tile(Floor(r), [tuple(o) for o in seen['objects']])
        if t is not None:
            out[site] = (t, r['room'])
    return out


def emit(table):
    ts = {s: t for s, (t, _r) in table.items()}
    lines = ['// GENERATED by tools/quickstart/portal_rooms.py - do not edit.',
             '// Portal ? rooms: docs/QUICKSTART_PORTAL_POCKETS.md.',
             '#ifndef QUICKSTART_PORTALS_H', '#define QUICKSTART_PORTALS_H', '',
             '#define QS_PORTAL_POCKETS %d' % len(POCKETS),
             '#define QS_PORTAL_NO_NODE 0xFF',
             '#define QS_PORTAL_NO_SITE 0xFF',
             '#define QS_PORTAL_ANY_ROOM 0xFF', '',
             'static const QuickStartPortalPocket sQuickStartPortalPockets[QS_PORTAL_POCKETS] = {']
    for p in POCKETS:
        if p['land_site'] is not None:
            s = P_SITES[p['land_site']]
            (tx, ty) = ts[p['land_site']]
            land = (s[0], s[1], tx, ty)
        else:
            land = p['land']
        node = NODE_NAMES.index(p['node']) if p['node'] else None
        ins = p['inside'] + [(None, None)] * (2 - len(p['inside']))
        cell = lambda a, r: '%s, %s' % (a or '0xFF', r or 'QS_PORTAL_ANY_ROOM') if a else '0xFF, 0xFF'
        lines.append('    { %s, %s, %d, %d, %d, %s, %s, %s, %s, %s, %s }, // %s' % (
            land[0], land[1], land[2], land[3], 1 if p['two_way'] else 0,
            node if node is not None else 'QS_PORTAL_NO_NODE',
            p['escape'][0], p['escape'][1] or 'ITEM_NONE',
            p['land_site'] if p['land_site'] is not None else 'QS_PORTAL_NO_SITE',
            cell(*ins[0]), cell(*ins[1]), p['label']))
    lines += ['};', '', '// The tile each site\'s portal stands on, room-local tiles.',
              'static const QuickStartPortalTile sQuickStartPortalTiles[] = {']
    for s, ((x, y), room) in sorted(table.items()):
        lines.append('    { %d, %d, %d }, // %s' % (s, x, y, room.replace('ROOM_', '')))
    lines += ['};', '', '#endif', '']
    return '\n'.join(lines)


P_SITES = None


def parse_header(text=None):
    """(pockets, tiles) as the ROM sees them, for sim.py."""
    text = text if text is not None else open(OUT_H).read()
    pockets = []
    body = re.search(r'sQuickStartPortalPockets\[QS_PORTAL_POCKETS\] = \{(.*?)\n\};', text, re.S).group(1)
    for m in re.finditer(r'\{ (\w+), (\w+), (\d+), (\d+), (\d), (\w+), (\w+), (\w+), (\w+), (\w+), (\w+), (\w+), (\w+) \}',
                         body):
        g = m.groups()
        pockets.append(dict(land_area=g[0], land_room=g[1], land_x=int(g[2]), land_y=int(g[3]), two_way=g[4] == '1',
                            node=None if g[5] == 'QS_PORTAL_NO_NODE' else int(g[5]),
                            escape=[g[6]] + ([g[7]] if g[7] != 'ITEM_NONE' else []),
                            land_site=None if g[8] == 'QS_PORTAL_NO_SITE' else int(g[8]),
                            inside=[(g[9], None if g[10] == 'QS_PORTAL_ANY_ROOM' else g[10]),
                                    (g[11], None if g[12] == 'QS_PORTAL_ANY_ROOM' else g[12])]))
    tiles_ = {int(m.group(1)): (int(m.group(2)), int(m.group(3)))
              for m in re.finditer(r'\{ (\d+), (\d+), (\d+) \}, //', text)}
    return pockets, tiles_


def main():
    global P_SITES
    P_SITES = {i: s for i, s in enumerate(P.content_sites())}
    table = tiles()
    text = emit(table)
    if '--check' in sys.argv:
        ok = os.path.exists(OUT_H) and open(OUT_H).read() == text
        print('portals.h', 'up to date' if ok else 'STALE')
        return 0 if ok else 1
    open(OUT_H, 'w').write(text)
    print('%d portal tiles, %d pockets -> %s' % (len(table), len(POCKETS), os.path.relpath(OUT_H, P.ROOT)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
