"""Every room the overworld regions lead into, and which of them the mode uses.

The simulator (sim.py) can only report on rooms it knows about: the walked
survey's destinations (include/quickstart/reach.h) and the region pool. A
room that hangs off a region but was never surveyed is invisible to it, so
"which rooms does a run never visit" cannot find it. This walks the map
itself instead and diffs the result against what the build incorporates.

THE WALK. From every region room (room_owner.RING), follow
  * DOORS     WARP_TYPE_AREA rows of the room's exit list, as the build
              compiles them (QUICKSTART branches resolved);
  * LINKS     sQuickStartLinks trigger boxes;
  * HOLES     Minish holes, from the region rooms only (room_owner);
  * SEAMS     two rooms of one area whose rectangles share an edge
              (gAreaRoomHeaders). That is how a bombable wall usually leads
              on: no door row at all, the rooms simply abut. The geometry
              says the rooms touch, not that the wall between them opens;
              every seam is listed so it can be checked by eye.
never stepping back into a region room. With --gate the walk is repeated
asking the ROM's own containment (survey_gate.ask) at every policed door,
which separates rooms the player can actually enter (OPEN) from rooms
whose door the build cancels (SHUT). The same walk is repeated over the
VANILLA exit lists, which finds rooms the build has cut off.

WHAT COUNTS AS INCORPORATED.
  SURVEYED   the room is a destination in the reach survey: the chain can
             price it, and the simulator sees it.
  SITE       the room hosts a ? room content site (sQuickStartRoomContentSites).
  POOL       the room is a region pool row.
A room with none of these is reachable but unused: no step can send the
player there and nothing happens in it.

    python3 tools/quickstart/room_census.py [--json out.json]
"""
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exit_lists as X
import minish_holes as M
import parse_tables as P
import room_owner as O
import seam_audit as S
import sim

AREA_OF_NUM = {v: k for k, v in P.AREAS.items()}

# The vanilla exit lists: the same text with QUICKSTART undefined.
_VSRC = X._resolve(X.RAW, defined=())
_VSRC = re.sub(r'/\*.*?\*/', '', _VSRC, flags=re.S)
_VSRC = re.sub(r'//[^\n]*', '', _VSRC)
_VLISTS = {}
for _m in re.finditer(r'const Transition (gExitList_\w+)\[\]\s*=\s*\{(.*?)\n\};', _VSRC, re.S):
    _VLISTS[_m.group(1)] = [(w, X._num(a), X._num(b), X._num(c), X._num(d), sh, ar, rm)
                            for w, a, b, c, d, sh, ar, rm in X.ROW.findall(_m.group(2))]
V_BY_ROOM = {}
for _m in re.finditer(r'const Transition\* const (gExitLists_\w+)\[\]\s*=\s*\{(.*?)\n\};', _VSRC, re.S):
    for _room, _ln in re.findall(r'\[(ROOM_\w+)\]\s*=\s*(gExitList_\w+)', _m.group(2)):
        V_BY_ROOM[_room] = _VLISTS.get(_ln, [])

_RECTS = {}


def rects(area):
    if area not in _RECTS:
        _RECTS[area] = S.room_rects(area, 64)
    return _RECTS[area]


def seam_neighbours(area_name, room_name):
    """Rooms of the same area whose rectangle shares an edge with this one."""
    area = P.AREAS[area_name]
    room = P.ROOMS.get(room_name)
    rs = rects(area)
    if room not in rs:
        return []
    x, y, w, h = rs[room]
    out = []
    for other, (ox, oy, ow, oh) in rs.items():
        if other == room:
            continue
        side = None
        if (oy + oh == y or y + h == oy) and ox < x + w and x < ox + ow:
            side = 'north' if oy + oh == y else 'south'
        elif (ox + ow == x or x + w == ox) and oy < y + h and y < oy + oh:
            side = 'west' if ox + ow == x else 'east'
        if side:
            name = M.room_name(area, other)
            if name.startswith('ROOM_'):
                out.append((area_name, name, side))
    return out


def edges(room_name, area_name, vanilla, is_ring):
    by_room = V_BY_ROOM if vanilla else X.BY_ROOM
    out = []
    for r in by_room.get(room_name, []):
        if r[0] == 'WARP_TYPE_AREA':
            out.append((r[6], r[7], 'door (%d,%d)' % (r[1], r[2])))
    if not vanilla:
        out += [(a, d, 'link') for a, d in O.links_from(room_name)]
    out += [(a, r, 'seam (stated)') for r, (a, parent) in O.SEAMS.items() if parent == room_name]
    if is_ring:
        out += [(a, d, 'minish hole') for a, d in O.minish_holes_from(room_name)]
    elif area_name:
        out += [(a, d, 'seam %s edge' % side) for a, d, side in seam_neighbours(area_name, room_name)]
    return out


_GATE = {}
CONTAINED = {'AREA_CASTLE_GARDEN', 'AREA_MINISH_HOUSE_INTERIORS', 'AREA_TREE_INTERIORS'}


def gate_open(parent, area, room):
    """Does the build's containment let this transition fire? Asked of the
    ROM (survey_gate.ask) only where the room being left is policed; an
    unpoliced room lets everything through by default."""
    import survey_gate as G
    # Policed as the three containment functions police: a region room
    # (QuickStartEnforceFieldRegionContainment / ...LonLon...) or a room in
    # a contained area (QuickStartAreaContained). survey_gate.policed()
    # predates Hyrule Town and Veil Falls, so it is not used here.
    if not (parent in O.RING or G.AREA_OF.get(parent) in CONTAINED):
        return True
    key = (parent, area, room)
    if key not in _GATE:
        ans = G.ask(parent, area, room)
        _GATE[key] = True if ans is None else ans
    return _GATE[key]


def walk(vanilla, gate=False):
    """{(area, room): {'owners': set, 'via': (parent, how)}}"""
    found = {}
    for start, region in O.RING.items():
        start_area = O.ring_area_of(start)
        seen = {start}
        frontier = [(start_area, start)]
        while frontier:
            area_name, cur = frontier.pop(0)
            for a, dest, how in edges(cur, area_name, vanilla, cur in O.RING):
                if dest in O.RING or dest in seen or not dest.startswith('ROOM_'):
                    continue
                if gate and (how.startswith('door') or how == 'minish hole') and not gate_open(cur, a, dest):
                    continue
                seen.add(dest)
                rec = found.setdefault((a, dest), dict(owners=set(), via=None))
                rec['owners'].add(region)
                if rec['via'] is None:
                    rec['via'] = (cur, how)
                frontier.append((a, dest))
    return found


def incorporated():
    surveyed = {(an, rn) for _n, _a, _r, _t, an, rn in sim.DESTS}
    sites = collections.Counter((s['areaName'], s['roomName']) for s in sim.SITES)
    retired = {(s['areaName'], s['roomName']) for s in sim.SITES if s['gate'] == -1}
    pool = {(p['areaName'], p['roomName']) for p in sim.POOL}
    return surveyed, sites, retired, pool


def census(gate=False):
    built = walk(False)
    vanilla = walk(True)
    entered = walk(False, gate=True) if gate else built
    surveyed, sites, retired, pool = incorporated()
    rows = []
    for key in sorted(set(built) | set(vanilla), key=lambda k: (k[0], k[1])):
        a, r = key
        b = built.get(key)
        v = vanilla.get(key)
        tags = []
        if key in surveyed:
            tags.append('SURVEYED')
        if key in sites:
            tags.append('SITE x%d' % sites[key])
        if key in pool:
            tags.append('POOL')
        rows.append(dict(area=a, room=r, wired=b is not None, vanilla=v is not None,
                         enterable=key in entered,
                         owners=sorted((b or v)['owners']),
                         via=(b or v)['via'], tags=tags,
                         sealed=O.SEALED.get(r)))
    return rows


def main():
    rows = census(gate='--gate' in sys.argv)
    out = None
    if '--json' in sys.argv:
        out = sys.argv[sys.argv.index('--json') + 1]
    wired = [r for r in rows if r['wired']]
    unused = [r for r in wired if not r['tags']]
    cut = [r for r in rows if not r['wired']]
    print(f'{len(wired)} rooms wired to a region in the build, {len(cut)} more only in vanilla wiring')
    print(f'{sum(1 for r in wired if r["tags"])} incorporated, {len(unused)} wired but unused\n')
    print('WIRED BUT UNUSED (no survey row, no site, not a pool row)')
    for r in unused:
        tag = 'OPEN  ' if r['enterable'] else 'SHUT  '
        print(f'  {tag}{r["room"][5:]:<48} {"+".join(r["owners"]):<10} via {r["via"][0][5:]} {r["via"][1]}')
    print('\nSITE BUT NOT SURVEYED (content the chain cannot price)')
    for r in wired:
        if any(t.startswith('SITE') for t in r['tags']) and 'SURVEYED' not in r['tags']:
            print(f'  {r["room"][5:]:<48} {"+".join(r["owners"]):<10} {r["tags"]}')
    print('\nCUT IN THE BUILD (reached only through vanilla doors)')
    for r in cut:
        print(f'  {r["room"][5:]:<48} {"+".join(r["owners"]):<10} via {r["via"][0][5:]} {r["via"][1]}')
    if out:
        with open(out, 'w') as f:
            json.dump(rows, f, indent=1, default=list)
    return 0


if __name__ == '__main__':
    sys.exit(main())
