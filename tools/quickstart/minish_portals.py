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
# THE TRANSFORM POINT IS A MANAGER, NOT AN OBJECT, and two scans went wrong
# before that landed. The first looked for jar/stone/tree OBJECTS and found
# five points in the whole ring, contradicting the user twice. The second
# widened to every portal-ish object id and "found" Lon Lon a free one -
# a MINISH_SIZED_ENTRANCE, which minishSizedEntrance.c shows is a
# Minish-ONLY DOORWAY (it tests gPlayerState.flags & PL_MINISH before it
# will fire), so it is somewhere to go once small, not a way to get small.
#
# What actually shrinks the player is MINISH_PORTAL_MANAGER (manager
# subtype 3, src/manager/minishPortalManager.c): stand in its 0x40 proximity
# box and it sets gArea.portal_mode. Its `type` field is the PT_* kind.
MINISH_PORTAL_MANAGER = 3
PT_NAME = {0: 'PT_TREESTUMP', 1: 'PT_ROCK', 2: 'PT_2', 3: 'PT_DUNGEON',
           4: 'PT_JAR', 5: 'PT_5', 6: 'PT_TOD'}

# A TREE_HIDING_PORTAL object sitting on the same spot as a portal manager
# is the tree the user described - the stump underneath is unusable until
# the tree is rammed with the Pegasus Boots (treeHidingPortal.c triggers on
# PLAYER_BOUNCE). A manager with no tree on top of it is free.
TREE_HIDING_PORTAL = 156
TREE_NEAR = 48   # pixels; tree and stump are authored at the same spot

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
    """Every transform point in a room, as (pt_type, x, y, hidden)."""
    managers, trees = [], []
    for prop in properties(room_symbol):
        for line in block(prop):
            d = kv(line)
            if 'manager' in line and d.get('subtype') == MINISH_PORTAL_MANAGER:
                managers.append((d.get('type', 0), d.get('x', 0), d.get('y', 0)))
            elif 'object' in line and d.get('subtype') == TREE_HIDING_PORTAL:
                trees.append((d.get('x', 0), d.get('y', 0)))
    out = []
    for t, x, y in managers:
        hidden = any(abs(x - tx) <= TREE_NEAR and abs(y - ty) <= TREE_NEAR
                     for tx, ty in trees)
        out.append((t, x, y, hidden))
    return out


def describe(found):
    free = [f for f in found if not f[3]]
    if not found:
        return 'none', ''
    price = 'FREE' if free else 'BOOTS (all hidden)'
    txt = ', '.join('%s@(%d,%d)%s' % (PT_NAME.get(t, t), x, y, ' [under tree]' if h else '')
                    for t, x, y, h in found)
    return price, txt


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
        price, txt = describe(found)
        verdicts[rn] = (price, txt)
        print('%-38s %-18s %s' % (rn[5:], price, txt))
    print('\nsummary')
    for price in ('FREE', 'BOOTS (all hidden)', 'none'):
        rooms = [r[5:] for r, (p, _) in verdicts.items() if p == price]
        print('  %-18s %d: %s' % (price, len(rooms), ', '.join(rooms) or '-'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
