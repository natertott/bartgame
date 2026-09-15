"""Every Minish hole in the ring, and where it tries to go.

A Minish hole is not a door and has no Transition row, which is why the
exit-table sweeps never saw one. It is room-property data driven by
SpecialWarpManager (src/manager/specialWarpManager.c): the room's entity
list carries `manager subtype=0x6, paramA=N`, property N is a list of
`exit_region_raw` boxes, and each box names an `exitIndex` into the room's
own property table where an `exit_raw` gives the destination. The manager
fires DoExitTransition on it when a MINISH-sized player stands in the box.

Which means a hole can be perfectly intact and still do nothing under
QUICKSTART: DoExitTransition sets transitioningOut, and
QuickStartEnforceFieldRegionContainment cancels that the same frame unless
the destination is a blessed pocket - i.e. unless it is in
sQuickStartRoomContentSites. Falling in and landing nowhere is what an
unblessed destination looks like from the player's side.

Static only: this reads data/map/entity_headers.s and the site table.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_tables as P

ROOT = P.ROOT
SRC = open(os.path.join(ROOT, 'data', 'map', 'entity_headers.s')).read()
LINES = SRC.split('\n')

AREA_LISTS = {}
for m in re.finditer(r'^(Area_\w+)::.*?\n((?:\t\.4byte .*\n)+)', SRC, re.M):
    rooms = [r.strip().split()[-1] for r in m.group(2).strip().split('\n')]
    AREA_LISTS[m.group(1)] = rooms


def block(symbol):
    """The lines of a `symbol::` block, up to the next blank line."""
    out = []
    started = False
    for line in LINES:
        if line.startswith(symbol + '::'):
            started = True
            continue
        if started:
            if not line.strip():
                break
            out.append(line.strip())
    return out


def properties(room_symbol):
    return [l.split()[-1] for l in block(room_symbol) if l.startswith('.4byte')]


def num(tok):
    return int(tok, 16) if tok.lower().startswith('0x') else int(tok)


def kv(line):
    return {k: num(v) for k, v in re.findall(r'(\w+)=((?:0x)?[0-9a-fA-F]+)', line)}


SITES = {(P.AREAS[a], P.ROOMS[r]) for a, r, *_ in [(x[0], x[1]) + tuple(x[2:]) for x in P.content_sites()]}
AREA_NAME = {v: k for k, v in P.AREAS.items()}
ROOMS_BY_AREA = {}
for rn, rv in P.ROOMS.items():
    ROOMS_BY_AREA.setdefault(rv, []).append(rn)


def room_name(area, room):
    """roomid.h reuses numbers across areas, so pick the name that belongs
    to this area by matching the area's own prefix."""
    prefix = 'ROOM_' + AREA_NAME.get(area, '')[5:]
    best = [n for n in ROOMS_BY_AREA.get(room, []) if n.startswith(prefix)]
    return best[0] if best else f'{AREA_NAME.get(area, area)}/room {room}'


def main():
    ring = [(r['areaName'], r['roomName'], r['area'], r['room']) for r in P.region_pool()]
    # Room record symbol for each ring room, via the area's own room list.
    total = 0
    for an, rn, area, room in ring:
        area_sym = 'Area_' + ''.join(w.capitalize() for w in an[5:].split('_'))
        rooms = AREA_LISTS.get(area_sym)
        if not rooms or room >= len(rooms):
            print(f'{rn[5:]:<38} no room list for {area_sym}')
            continue
        room_sym = rooms[room]
        props = properties(room_sym)
        # Which property index the room's SpecialWarpManager reads.
        indices = set()
        for prop in props:
            if prop == '0x00000000':
                continue
            for line in block(prop):
                if 'manager ' in line and 'subtype=0x6' in line:
                    d = kv(line)
                    if 'paramA' in d:
                        indices.add(d['paramA'])
        if not indices:
            print(f'{rn[5:]:<38} no Minish holes')
            continue
        for idx in sorted(indices):
            if idx >= len(props) or props[idx] == '0x00000000':
                print(f'{rn[5:]:<38} warp list property {idx} is empty')
                continue
            for line in block(props[idx]):
                if not line.startswith('exit_region_raw'):
                    continue
                d = kv(line)
                ei = d['exitIndex']
                dest = '?'
                if ei < len(props) and props[ei] != '0x00000000':
                    for el in block(props[ei]):
                        if el.startswith('exit_raw'):
                            e = kv(el)
                            da, dr = e.get('destArea', 0), e.get('destRoom', 0)
                            tag = 'SITE' if (da, dr) in SITES else 'NOT A SITE'
                            dest = f'{room_name(da, dr)[5:]:<44} [{tag}]'
                            break
                total += 1
                print(f'{rn[5:]:<38} hole at ({d["centerX"]:>4},{d["centerY"]:>4})  -> {dest}')
    print(f'\n{total} Minish hole(s) in the ring')


if __name__ == '__main__':
    main()
