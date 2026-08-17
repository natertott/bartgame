"""Every door in the ring: does it fire, and does it lead to a ? event.

"That door doesn't do anything" has three separate causes that look
identical from the outside:

  1. The exit row is compiled out under QUICKSTART (`#ifndef QUICKSTART`),
     so there is no door there at all - only scenery that looks like one.
     Both Minish Woods borders out of Eastern Hills are like this.
  2. The row exists, but nothing the player can stand on is inside its
     trigger rect. IsPosInTransitionRect (scroll.c) tests the player's own
     centre against startX/startY +- the shape's half-extents (6, 14 or 22
     px), and UpdateDoorTransition only looks at the actTile under the
     player's own tile - so if the doorway tile is solid and the tile in
     front of it is more than half a tile away, walking into the door
     stops one tile short forever. This is the interesting case and it is
     invisible in the data: the row looks perfectly normal.
  3. The row exists and fires, but the room behind it has no content site,
     so the player arrives in a bare vanilla room and reads that as
     "the door is broken".

Only (3) is fixed by adding a site row; (2) is fixed by an
sQuickStartLinks position box on the walkable tile in front of the door.

So this walks the player into every live door from every walkable side and
reports which of the three it is.

Usage:  python3 tools/quickstart/door_audit.py [ROOM_SUBSTRING ...]
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_tables as P
from emu import boot, warp, here, poison_here, room_dims, coll_at, r16, PLAYER, ROOM_CONTROLS

HERE = os.path.dirname(os.path.abspath(__file__))
ROM = os.path.abspath(os.path.join(HERE, '..', '..', 'tmc.gba'))
TRANS = open(os.path.join(HERE, '..', '..', 'src', 'data', 'transitions.c')).read()

# IsPosInTransitionRect's gShapeDimensions, indexed by shape.
SHAPE_HALF = {0: (6, 6), 1: (6, 6), 2: (6, 14), 3: (14, 6), 4: (22, 6)}


def exit_lists():
    """{exitListSymbol: [row fields, ...]} with the QUICKSTART guards honoured.

    A plain regex over the file reports doors this build does not have -
    the Minish Woods borders out of Eastern Hills are both inside
    `#ifndef QUICKSTART`, and reading them as live doors sends you looking
    for a bug in containment instead of for a missing row.
    """
    out = collections.OrderedDict()
    cur = None
    skip = 0
    stack = []
    pending = ''
    for line in TRANS.split('\n'):
        st = line.strip()
        if st.startswith('#ifndef QUICKSTART'):
            stack.append(True)
            skip += 1
            continue
        if st.startswith('#ifdef QUICKSTART'):
            stack.append(False)
            continue
        if st.startswith('#else') and stack:
            was = stack[-1]
            stack[-1] = not was
            skip += -1 if was else 1
            continue
        if st.startswith('#endif') and stack:
            if stack.pop():
                skip -= 1
            continue
        m = re.match(r'const Transition (gExitList_\w+)\[\]', st)
        if m:
            cur = m.group(1)
            out.setdefault(cur, [])
            pending = ''
            continue
        if cur is None or skip:
            continue
        if 'WARP_TYPE' in st and st.startswith('{'):
            pending = st
        elif pending:
            pending += ' ' + st
        else:
            continue
        if '},' not in pending:
            continue
        fields = [f.strip() for f in pending.strip('{} ,').split(',')]
        pending = ''
        if len(fields) >= 8:
            out[cur].append(fields)
    return out


LISTS = exit_lists()
DISPATCH = {}
for _m in re.finditer(r'\[(ROOM_\w+)\] = (gExitList_\w+),', TRANS):
    DISPATCH.setdefault(_m.group(2), []).append(_m.group(1))
BY_ROOM = {}
for _sym, _rows in LISTS.items():
    for _rn in DISPATCH.get(_sym, []):
        BY_ROOM.setdefault(_rn, []).extend(_rows)

SITES = {(r[0], r[1]) for r in P.content_sites()}
POOL = set(P.pool_doors().keys())
SHAPES = {}
for _m in re.finditer(r'(TRANSITION_SHAPE_AREA_\w+) = (\d+)', open(
        os.path.join(HERE, '..', '..', 'include', 'transitions.h')).read()):
    SHAPES[_m.group(1)] = int(_m.group(2))


def num(tok):
    return int(tok, 16) if tok.lower().startswith('0x') else int(tok)


APPROACH = (('UP', 0, 1), ('DOWN', 0, -1), ('LEFT', 1, 0), ('RIGHT', -1, 0))


def walk_in(area, room, dx, dy, key, offx, offy, tiles):
    """Stand `tiles` tiles off the door on the given side and walk into it."""
    c = boot(ROM)
    poison_here(c)
    warp(c, area, room, dx + offx * 16 * tiles, dy + offy * 16 * tiles)
    if here(c) != (area, room):
        return None
    k = getattr(c, 'KEY_' + key)
    c.set_keys(k)
    for _ in range(60 * tiles + 120):
        c.run_frame()
        if here(c) != (area, room):
            c.clear_keys(k)
            for _ in range(30):
                c.run_frame()
            return here(c)
    c.clear_keys(k)
    return False


def audit(room_filter=()):
    for r in P.region_pool():
        if room_filter and not any(f.upper() in r['roomName'] for f in room_filter):
            continue
        rows = [f for f in BY_ROOM.get(r['roomName'], []) if f[0] == 'WARP_TYPE_AREA']
        print(f"\n{r['roomName']}  {len(rows)} live door(s)")
        for f in rows:
            sx, sy = num(f[1]), num(f[2])
            an, drn = f[6], f[7]
            tag = 'SITE' if (an, drn) in SITES else ('POOL' if (an, drn) in POOL else '----')
            got = []
            for key, offx, offy in APPROACH:
                for tiles in (2, 3):
                    res = walk_in(r['area'], r['room'], sx, sy, key, offx, offy, tiles)
                    if res:
                        got.append(f'{key}@{tiles}->{res}')
                        break
            verdict = 'FIRES  ' + ', '.join(got) if got else 'DEAD - no approach fires it'
            print(f"    ({sx},{sy}) tile ({sx // 16},{sy // 16}) [{tag}] "
                  f"{an[5:]}/{drn[5:]}\n        {verdict}")


if __name__ == '__main__':
    audit(tuple(sys.argv[1:]))
