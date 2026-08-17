"""Sweep the ring for Minish-layer destinations and say which are wired.

Every exit the seven ring regions have, filtered to the Minish-ish areas
(the paths, the village, the cracks, the holes, the rafters, the caves,
plus TREE_INTERIORS and the MINISH_HOUSE_INTERIORS the shrink-doors lead
into), cross-referenced against sQuickStartRoomContentSites.

Static only - this reads the tables. Anything it flags still has to be
walked before it becomes a site row.
"""
import re
import sys
sys.path.insert(0, '/home/user/bartgame/tools/quickstart')
import parse_tables as P

TRANS = open('/home/user/bartgame/src/data/transitions.c').read()
GAME = open('/home/user/bartgame/src/game.c').read()

RING = [r['roomName'] for r in P.region_pool()]
print(f'{len(RING)} ring rooms: {[r[5:] for r in RING]}\n')

MINISH_AREAS = {a for a in P.AREAS if
                ('MINISH' in a or a == 'AREA_TREE_INTERIORS' or
                 'HOUSE_INTERIORS' in a)}

# content sites we already have, as (areaName, roomName)
SITES = {(r[0], r[1]) for r in P.content_sites()}
print(f'{len(SITES)} content sites already placed\n')


def exit_list_for(room_name):
    """The Transition rows of a room's exit list, as raw text blocks."""
    # exit lists are named gExitList_<Area><Room>; find the one the
    # dispatch table maps this room to.
    m = re.search(r'\[' + re.escape(room_name) + r'\] = (gExitList_\w+),', TRANS)
    if not m:
        return None, []
    name = m.group(1)
    # take the LAST definition of that symbol (the QUICKSTART branch, when
    # the file has an #ifdef pair, is the first - so collect all and merge)
    blocks = []
    for dm in re.finditer(r'const Transition ' + name + r'\[\] = \{(.*?)\n\};', TRANS, re.S):
        blocks.append(dm.group(1))
    rows = []
    for b in blocks:
        for row in re.finditer(
                r'\{\s*(WARP_TYPE_\w+),([^}]*?),\s*(AREA_\w+),\s*(ROOM_\w+),', b, re.S):
            nums = re.findall(r'0x[0-9a-fA-F]+|\d+', row.group(2))
            rows.append((row.group(1), row.group(3), row.group(4), nums))
    return name, rows


findings = []
for room in RING:
    name, rows = exit_list_for(room)
    if name is None:
        print(f'{room[5:]:<34} NO EXIT LIST FOUND')
        continue
    hits = [r for r in rows if r[1] in MINISH_AREAS]
    print(f'{room[5:]:<34} {len(rows):>2} exits, {len(hits)} into the Minish layer')
    for warp, area, dest, nums in hits:
        wired = (area, dest) in SITES
        mark = 'WIRED  ' if wired else 'UNWIRED'
        print(f'    [{mark}] {area[5:]:<24} {dest[5:]:<40} {warp[10:]}')
        if not wired:
            findings.append((room, area, dest))

print()
print(f'{len(findings)} unwired Minish destination(s):')
seen = set()
for room, area, dest in findings:
    if (area, dest) in seen:
        continue
    seen.add((area, dest))
    print(f'   {area:<32} {dest}')
print(f'({len(seen)} distinct rooms)')
