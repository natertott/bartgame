"""Where a player can BECOME Minish, and what it costs, per region room.

minish_holes.py answers the other half of the question - where a Minish-sized
player can go once small. This answers the half that actually gates the
model: a Minish room needs a TRANSFORM POINT within reach, and not every
transform point is free.

The user: "In order to reach a Minish room, there are a few requirements:
1) the player must have the Minish cap ... 2) there must be a tree
stump/stone/pot nearby for the player to transform into a Minish. It's the
second requirement that really makes things difficult. There are some rooms
where Tree stumps are given freely ... There are other regions/rooms, though,
where the tree stump/stone/portal is initially hidden. Sometimes they require
another item to reveal. An example is the Tree Stump in NHF or HCG. These
stumps are hidden underneath specials trees that the player must ram with the
Pegasus boots to reveal the stump."

That distinction is not a judgement call - the game ships it as three
DIFFERENT OBJECT TYPES, and the room's own entity list names which one is
standing there:

    MINISH_PORTAL_STONE (116)  a stone portal, standing in the open
    JAR_PORTAL          (56)   a jar/pot portal, standing in the open
    TREE_HIDING_PORTAL  (156)  hidden under a tree until it is rammed

So the per-region price is read off the data rather than guessed: free where
a region has a stone or a jar, Pegasus Boots where all it has is a tree.

Static only: reads data/map/entity_headers.s, the same source minish_holes.py
walks, so it needs no emulator.

    python3 tools/quickstart/minish_portals.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_tables as P

ROOT = P.ROOT
SRC = open(os.path.join(ROOT, 'data', 'map', 'entity_headers.s')).read()
LINES = SRC.split('\n')

# object.inc
JAR_PORTAL, MINISH_PORTAL_STONE, TREE_HIDING_PORTAL = 56, 116, 156
FREE_PORTALS = {JAR_PORTAL: 'jar', MINISH_PORTAL_STONE: 'stone'}
PORTAL_NAME = {JAR_PORTAL: 'JAR_PORTAL', MINISH_PORTAL_STONE: 'MINISH_PORTAL_STONE',
               TREE_HIDING_PORTAL: 'TREE_HIDING_PORTAL'}

AREA_LISTS = {}
for m in re.finditer(r'^(Area_\w+)::.*?\n((?:\t\.4byte .*\n)+)', SRC, re.M):
    AREA_LISTS[m.group(1)] = [r.strip().split()[-1] for r in m.group(2).strip().split('\n')]


def block(symbol):
    out, started = [], False
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


def portals_in(room_symbol):
    """Every transform point in a room's entity lists, as (kind, x, y)."""
    found = []
    for prop in properties(room_symbol):
        for line in block(prop):
            if 'object' not in line:
                continue
            d = kv(line)
            oid = d.get('subtype')
            if oid in PORTAL_NAME:
                found.append((oid, d.get('x', 0), d.get('y', 0)))
    return found


def scan_all():
    """Every room in every area, not just the eighteen region rooms - a
    transform point in a sub-room still serves the region it hangs off."""
    rows = []
    for area_sym, rooms in sorted(AREA_LISTS.items()):
        for idx, room_sym in enumerate(rooms):
            found = portals_in(room_sym)
            if found:
                rows.append((area_sym, idx, room_sym, found))
    print('every room carrying a transform point:')
    for area_sym, idx, room_sym, found in rows:
        kinds = ', '.join('%s@(%d,%d)' % (PORTAL_NAME[k], x, y) for k, x, y in found)
        free = any(k in FREE_PORTALS for k, _, _ in found)
        print('  %-34s room %-3d %-18s %s'
              % (area_sym, idx, 'FREE' if free else 'BOOTS', kinds))
    print('\n  %d room(s) with a transform point; %d of them FREE'
          % (len(rows), sum(1 for _, _, _, f in rows
                            if any(k in FREE_PORTALS for k, _, _ in f))))
    return 0


def main():
    if '--all' in sys.argv:
        return scan_all()
    ring = [(r['areaName'], r['roomName'], r['area'], r['room']) for r in P.region_pool()]
    print('%-38s %s' % ('region room', 'transform points'))
    verdicts = {}
    for an, rn, area, room in ring:
        area_sym = 'Area_' + ''.join(w.capitalize() for w in an[5:].split('_'))
        rooms = AREA_LISTS.get(area_sym)
        if not rooms or room >= len(rooms):
            print('%-38s no room list for %s' % (rn[5:], area_sym))
            continue
        found = portals_in(rooms[room])
        if not found:
            print('%-38s none' % rn[5:])
            verdicts[rn] = ('none', [])
            continue
        kinds = sorted({PORTAL_NAME[k] for k, _, _ in found})
        free = [f for f in found if f[0] in FREE_PORTALS]
        price = 'FREE' if free else 'BOOTS (tree only)'
        verdicts[rn] = (price, kinds)
        print('%-38s %-18s %s' % (rn[5:], price, ', '.join(
            '%s@(%d,%d)' % (PORTAL_NAME[k][:18], x, y) for k, x, y in found)))
    print('\nsummary')
    for price in ('FREE', 'BOOTS (tree only)', 'none'):
        rooms = [r[5:] for r, (p, _) in verdicts.items() if p == price]
        print('  %-18s %d: %s' % (price, len(rooms), ', '.join(rooms) or '-'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
