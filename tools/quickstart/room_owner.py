"""Which overworld region does a pocket room belong to?

A "? room" is its own room, so a rule written against the room the player
is standing in cannot tell that the cave they are in hangs off Lon Lon
Ranch. That matters for anything region-scoped - the overworld keys most
of all, whose whole safety property is "never drop inside the region this
key opens", and whose failure mode is a key sealed behind the very door it
unlocks.

This derives the map instead of hand-listing it. Every ring region's own
WARP_TYPE_AREA doors name the rooms they lead into; those rooms belong to
that region. Some pockets are only reached through another pocket (the
Boomerang chamber from the tree hollows, Grimblade's dojo from its ante
room, Goron Cave Main from its stairs), so ownership follows doors
transitively - but never back out through a ring room, or every pocket
would end up owned by everything.

Minish holes are included too: they are room-property special warps with
no Transition row at all (see minish_holes.py), so they are read from the
same property chain that tool walks. So are the surviving sQuickStartLinks
boxes, which are how the Grimblade arena and Link's smithy are entered -
neither has a Transition row anywhere, so a doors-only sweep reports them
as unreachable when they are two of the busiest ? rooms in the pool.

A room reachable from two different regions is reported as SHARED. For a
key that means "allowed only if every owner is allowed" - the conservative
reading, and the one the C table encodes.

Usage: python3 tools/quickstart/room_owner.py [--c]    (--c emits the table)
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_tables as P
import exit_lists as X
import minish_holes as M

RING = {  # room name -> the QS_RING_* name it is
    'ROOM_CASTLE_GARDEN_MAIN': 'CG',
    'ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD': 'NHF',
    'ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD': 'SHF',
    'ROOM_HYRULE_FIELD_LON_LON_RANCH': 'LLR',
    'ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS': 'TRIL',
    'ROOM_HYRULE_FIELD_EASTERN_HILLS_SOUTH': 'EH',
    'ROOM_HYRULE_FIELD_EASTERN_HILLS_CENTER': 'EH',
    'ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH': 'EH',
    'ROOM_HYRULE_FIELD_WESTERN_WOODS_SOUTH': 'WW',
    'ROOM_HYRULE_FIELD_WESTERN_WOODS_CENTER': 'WW',
    'ROOM_HYRULE_FIELD_WESTERN_WOODS_NORTH': 'WW',
    'ROOM_ROYAL_VALLEY_MAIN': 'RV',
    'ROOM_CASTOR_WILDS_MAIN': 'CW',
    'ROOM_RUINS_ENTRANCE': 'WR',
    'ROOM_RUINS_BEANSTALK': 'WR',
    'ROOM_RUINS_TEKTITES': 'WR',
    'ROOM_RUINS_LADDER_TO_TEKTITES': 'WR',
    'ROOM_RUINS_FORTRESS_ENTRANCE': 'WR',
    'ROOM_RUINS_BELOW_FORTRESS_ENTRANCE': 'WR',
}
# Two ? rooms are joined to their parent by a SCROLL SEAM, not by any kind
# of transition: rooms inside one area share a pixel grid and the player
# simply walks across the boundary. There is no row anywhere to read, so
# these two are stated rather than derived. Both are measured and
# documented at their use sites in game.c - the Grimblade arena sits
# directly above its ante room (43 frames of walking, no fade, and it is
# that seam the gauntlet's FLAG_BANK_11 state exists to survive), and
# Link's smithy adjoins the house entrance the same way.
SEAMS = {
    'ROOM_DOJOS_GRIMBLADE': ('AREA_DOJOS', 'ROOM_DOJOS_TO_GRIMBLADE'),
    'ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_SMITH':
        ('AREA_HOUSE_INTERIORS_2', 'ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_ENTRANCE'),
}

# Owning a region is necessary but not sufficient for a key drop. Some
# pockets sit BEHIND a gate inside their own region, which is the exact
# accident the key rule exists to prevent: put the graveyard key in a room
# you can only enter by opening the graveyard gate and the run is dead.
#
# Derived from the door's own position against the gated-zone rows in
# game.c. Royal Valley Main is 30x63 tiles in four disconnected pieces:
#   ty  4-21  north      - behind the graveyard gate (the gated zone is
#                          x 0-479, y 64-351). Holds both grave doors and
#                          the crypt.
#   ty 23-40  middle     - reachable only by solving the Lost Woods maze.
#                          Holds Dampe's house at (416,408).
#   ty 36-40  NE pocket  - where North Hyrule Field's border lands. No doors.
#   ty 43-62  south      - where Trilby's border lands, and the only piece
#                          the player is guaranteed to be able to walk out
#                          of. Holds the Great Fairy at (408,680) and the
#                          maze entrance.
# So of Royal Valley's four ? rooms exactly one - the Great Fairy - is in
# the part of the region the user described as "the lower portion of RV
# that connects to NHF and TH". The other three are sealed.
SEALED = {
    'ROOM_ROYAL_VALLEY_GRAVES_HEART_PIECE': 'ITEM_QST_GRAVEYARD_KEY',
    'ROOM_ROYAL_VALLEY_GRAVES_GINA': 'ITEM_QST_GRAVEYARD_KEY',
    # Not key-sealed, maze-sealed - but a key here is just as lost, and the
    # maze's own doors are still cancelled by containment, so nothing can
    # reach it at all yet.
    'ROOM_HOUSE_INTERIORS_2_DAMPE': 'ITEM_QST_GRAVEYARD_KEY',
    # Both ranch-house halves are behind the Lon Lon key's own door. Lon
    # Lon Ranch is already off that key's allow-list wholesale, so this is
    # belt and braces - and it is the row that stays right if the ranch is
    # ever added back.
    'ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_EAST': 'ITEM_QST_LONLON_KEY',
    'ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_WEST': 'ITEM_QST_LONLON_KEY',
}

ENUM = {'CG': 'QS_RING_CG', 'NHF': 'QS_RING_NHF', 'SHF': 'QS_RING_SHF', 'EH': 'QS_RING_EH',
        'LLR': 'QS_RING_LLR', 'TRIL': 'QS_RING_TRIL', 'WW': 'QS_RING_WW', 'RV': 'QS_RING_RV',
        'CW': 'QS_RING_CW', 'WR': 'QS_RING_WR'}


def doors_from(room_name):
    """Rooms this room's own WARP_TYPE_AREA doors lead into."""
    return X.area_doors(room_name)


def links_from(room_name):
    """Destinations of the sQuickStartLinks trigger boxes this room owns."""
    i = P.GAME.find('sQuickStartLinks[] = {')
    j = P.GAME.find('\n};', i)
    body = re.sub(r'//[^\n]*', '', P.GAME[i:j])
    out = []
    for m in re.finditer(
            r'\{ (AREA_\w+), (ROOM_\w+),(?:\s*-?(?:0x)?[0-9a-fA-F]+,){4}'
            r'\s*(AREA_\w+),\s*(ROOM_\w+),', body):
        if m.group(2) == room_name:
            out.append((m.group(3), m.group(4)))
    return out


def minish_holes_from(room_name):
    """Destinations of this room's Minish holes, via the room-property chain."""
    out = []
    area_name = next((r['areaName'] for r in P.region_pool() if r['roomName'] == room_name), None)
    room_no = next((r['room'] for r in P.region_pool() if r['roomName'] == room_name), None)
    if area_name is None:
        return out
    area_sym = 'Area_' + ''.join(w.capitalize() for w in area_name[5:].split('_'))
    rooms = M.AREA_LISTS.get(area_sym)
    if not rooms or room_no >= len(rooms):
        return out
    props = M.properties(rooms[room_no])
    idxs = set()
    for prop in props:
        if prop == '0x00000000':
            continue
        for line in M.block(prop):
            if 'manager ' in line and 'subtype=0x6' in line:
                d = M.kv(line)
                if 'paramA' in d:
                    idxs.add(d['paramA'])
    for idx in sorted(idxs):
        if idx >= len(props) or props[idx] == '0x00000000':
            continue
        for line in M.block(props[idx]):
            if not line.startswith('exit_region_raw'):
                continue
            ei = M.kv(line)['exitIndex']
            if ei >= len(props) or props[ei] == '0x00000000':
                continue
            for el in M.block(props[ei]):
                if el.startswith('exit_raw'):
                    e = M.kv(el)
                    da, dr = e.get('destArea', 0), e.get('destRoom', 0)
                    name = M.room_name(da, dr)
                    inv = {v: k for k, v in P.AREAS.items()}
                    out.append((inv.get(da, str(da)), name))
                    break
    return out


def build():
    owners = collections.defaultdict(set)
    for start, region in RING.items():
        seen = {start}
        frontier = [start]
        while frontier:
            cur = frontier.pop()
            edges = doors_from(cur) + links_from(cur)
            edges += [(a, r) for r, (a, parent) in SEAMS.items() if parent == cur]
            if cur == start:
                edges += minish_holes_from(cur)
            for area_name, dest in edges:
                if dest in RING or dest in seen:
                    continue
                seen.add(dest)
                owners[(area_name, dest)].add(region)
                frontier.append(dest)
    return owners


def main():
    owners = build()
    sites = {(row[0], row[1]) for row in P.content_sites()}
    print(f'{len(owners)} pocket rooms owned by a region\n')
    shared = 0
    rows = []
    for (area, room), regs in sorted(owners.items(), key=lambda kv: (sorted(kv[1]), kv[0][1])):
        tag = 'SITE' if (area, room) in sites else '    '
        if len(regs) > 1:
            shared += 1
        rows.append((area, room, sorted(regs), tag))
        print(f'  [{tag}] {room[5:]:<46} {"+".join(sorted(regs))}')
    print(f'\n{shared} room(s) reachable from more than one region')
    if '--c' in sys.argv:
        print('\n// generated by tools/quickstart/room_owner.py')
        for area, room, regs, tag in rows:
            if (area, room) not in sites:
                continue
            mask = ' | '.join(f'(1 << {ENUM[r]})' for r in regs)
            print(f'    {{ {area}, {room},\n      {mask}, {SEALED.get(room, "0")} }},')
    return 0


if __name__ == '__main__':
    sys.exit(main())
