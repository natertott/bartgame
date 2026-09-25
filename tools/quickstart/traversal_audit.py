"""The traversability audit: every place in every overworld region, and what
we actually KNOW about walking from each one to each other one.

WHY THIS EXISTS. Three separate tables describe how this world connects, and
none of them is the graph:

  * src/data/transitions.c  - every door and border the ROM has, exact, but
    it only says "this rectangle sends you there". It never says whether the
    player can REACH that rectangle.
  * tools/quickstart/world_reach.py - the walked survey. Real measurements,
    but every one of them is the cost FROM ONE START POINT, so it prices
    start->place and nothing else.
  * tools/quickstart/overworld_paths.py - port-to-port crossings, at region
    granularity only.

The traversal graph the chain placer eventually needs is finer than all
three: for any two places A and B in a region, what does A->B cost? This
tool lays that question out as a matrix so the holes are countable, and
emits a second matrix saying how much the answers deserve to be trusted.

It measures nothing new. It is an inventory of what has been measured, so
the next round of measuring has somewhere to aim.

    python3 tools/quickstart/traversal_audit.py            # summary
    python3 tools/quickstart/traversal_audit.py --md       # write docs/
    python3 tools/quickstart/traversal_audit.py --json     # write docs/
    python3 tools/quickstart/traversal_audit.py --region CREN
"""
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse_tables as P
import exit_lists as EX
import world_reach as WR
import overworld_paths as OP

ROOT = P.ROOT
AREA_NAME = {}
for _k, _v in P.AREAS.items():
    AREA_NAME.setdefault(_v, _k)

# ---------------------------------------------------------- room id tables --
# parse_tables keeps name->id but drops which area a room belongs to, and the
# ids restart per area, so the association is the whole point here.
ROOMS_OF_AREA = {}
_cur, _n = None, 0
for _line in open(os.path.join(ROOT, 'include/roomid.h')):
    _mc = re.match(r'\s*// (AREA_\w+)', _line)
    if _mc:
        _cur = _mc.group(1)
        continue
    _l = re.sub(r'/\*.*?\*/', '', _line).split('//')[0].strip().rstrip(',')
    if not _l or _cur is None:
        continue
    if '=' in _l:
        _nm, _v = _l.split('=', 1)
        _nm = _nm.strip()
        try:
            _n = int(_v.strip(), 0)
        except ValueError:
            continue
    else:
        _nm = _l
    if re.match(r'^ROOM_\w+$', _nm):
        ROOMS_OF_AREA.setdefault(_cur, {}).setdefault(_n, _nm)
        _n += 1


def room_name(area_name, room_id):
    return ROOMS_OF_AREA.get(area_name, {}).get(room_id, 'ROOM_%s_?%d' % (area_name[5:], room_id))


def short(area_name, room_name_):
    """AREA_HYRULE_FIELD / ROOM_HYRULE_FIELD_LON_LON_RANCH -> HYRULE_FIELD/LON_LON_RANCH."""
    a = area_name[5:]
    r = room_name_[5:]
    if r.startswith(a + '_'):
        r = r[len(a) + 1:]
    return '%s/%s' % (a, r)


# ------------------------------------------------------------ room rectangles --
# gAreaRoomHeaders gives every room a rectangle on a global pixel grid, which
# is what makes a scroll seam findable: two rooms that share an edge are
# joined by walking, with no transition row anywhere. Reading past an area's
# real room count walks into the NEXT area's table and invents rooms, so the
# count comes from roomid.h rather than from a fixed 16.
OVERWORLD_AREAS = [
    'AREA_HYRULE_FIELD', 'AREA_MINISH_WOODS', 'AREA_LAKE_HYLIA', 'AREA_MT_CRENEL',
    'AREA_CASTOR_WILDS', 'AREA_RUINS', 'AREA_ROYAL_VALLEY', 'AREA_CASTLE_GARDEN',
    'AREA_VEIL_FALLS', 'AREA_CLOUD_TOPS', 'AREA_HYRULE_TOWN', 'AREA_FESTIVAL_TOWN',
    'AREA_VEIL_FALLS_TOP',
]

RECTS = {}      # (area_name, room_id) -> (x, y, w, h)
RECT_ERR = None
try:
    _ROM = open(os.path.join(ROOT, 'tmc.gba'), 'rb').read()
    _MAP = open(os.path.join(ROOT, 'build/USA/tmc.map')).read()

    def _sym(name):
        for line in _MAP.split('\n'):
            parts = line.split()
            if len(parts) == 2 and parts[1] == name and parts[0].startswith('0x'):
                return int(parts[0], 16) - 0x08000000
        raise KeyError(name)

    _HDR = _sym('gAreaRoomHeaders')
    for _an in OVERWORLD_AREAS:
        _aid = P.AREAS.get(_an)
        if _aid is None:
            continue
        _ptr = struct.unpack('<I', _ROM[_HDR + _aid * 4:][:4])[0]
        if not 0x08000000 <= _ptr < 0x0A000000:
            continue
        _base = _ptr - 0x08000000
        for _rid in sorted(ROOMS_OF_AREA.get(_an, {})):
            _x, _y, _w, _h, _ = struct.unpack('<5H', _ROM[_base + _rid * 10:][:10])
            if _w == 0 or _h == 0 or _w > 0x2000 or _h > 0x2000 or _x > 0x4000 or _y > 0x4000:
                continue
            RECTS[(_an, _rid)] = (_x, _y, _w, _h)
except Exception as _e:          # no ROM built yet - seams degrade, nothing else
    RECT_ERR = str(_e)


def rect_of(area_name, room_name_):
    for rid, nm in ROOMS_OF_AREA.get(area_name, {}).items():
        if nm == room_name_:
            return RECTS.get((area_name, rid))
    return None


# ------------------------------------------------------------- the regions --
# A region's OVERWORLD rooms - the ones QuickStartRingRegionOfRoom blesses.
# Everything else a region owns (caves, houses, minish paths) hangs off these
# through doors and is discovered, not listed.
HF = 'AREA_HYRULE_FIELD'
REGION_ROOMS = [
    ('CG',   'Hyrule Castle Garden', [('AREA_CASTLE_GARDEN', 'ROOM_CASTLE_GARDEN_MAIN')]),
    ('NHF',  'North Hyrule Field',   [(HF, 'ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD')]),
    ('SHF',  'South Hyrule Field',   [(HF, 'ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD')]),
    ('EH-N', 'Eastern Hills North',  [(HF, 'ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH')]),
    ('EH-C', 'Eastern Hills Center', [(HF, 'ROOM_HYRULE_FIELD_EASTERN_HILLS_CENTER')]),
    ('EH-S', 'Eastern Hills South',  [(HF, 'ROOM_HYRULE_FIELD_EASTERN_HILLS_SOUTH')]),
    ('LLR',  'Lon Lon Ranch',        [(HF, 'ROOM_HYRULE_FIELD_LON_LON_RANCH')]),
    ('TRIL', 'Trilby Highlands',     [(HF, 'ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS')]),
    ('WW-N', 'Western Wood North',   [(HF, 'ROOM_HYRULE_FIELD_WESTERN_WOODS_NORTH')]),
    ('WW-C', 'Western Wood Center',  [(HF, 'ROOM_HYRULE_FIELD_WESTERN_WOODS_CENTER')]),
    ('WW-S', 'Western Wood South',   [(HF, 'ROOM_HYRULE_FIELD_WESTERN_WOODS_SOUTH')]),
    ('RV',   'Royal Valley',         [('AREA_ROYAL_VALLEY', 'ROOM_ROYAL_VALLEY_MAIN')]),
    ('CW',   'Castor Wilds',         [('AREA_CASTOR_WILDS', 'ROOM_CASTOR_WILDS_MAIN')]),
    ('WR',   'Wind Ruins',           [('AREA_RUINS', 'ROOM_RUINS_ENTRANCE'),
                                      ('AREA_RUINS', 'ROOM_RUINS_BEANSTALK'),
                                      ('AREA_RUINS', 'ROOM_RUINS_TEKTITES'),
                                      ('AREA_RUINS', 'ROOM_RUINS_LADDER_TO_TEKTITES'),
                                      ('AREA_RUINS', 'ROOM_RUINS_FORTRESS_ENTRANCE'),
                                      ('AREA_RUINS', 'ROOM_RUINS_BELOW_FORTRESS_ENTRANCE')]),
    ('MW',   'Minish Woods',         [('AREA_MINISH_WOODS', 'ROOM_MINISH_WOODS_MAIN')]),
    ('LH',   'Lake Hylia',           [('AREA_LAKE_HYLIA', 'ROOM_LAKE_HYLIA_MAIN')]),
    # Mount Crenel is five rooms on the area's own scroll grid. ENTRANCE is
    # what the user calls "Mount Crenel Base" - it is broken out in the node
    # list so measurements can be filed against it separately, but it stays
    # in CREN because every measurement we have was walked as one region.
    ('CREN', 'Mount Crenel',         [('AREA_MT_CRENEL', 'ROOM_MT_CRENEL_ENTRANCE'),
                                      ('AREA_MT_CRENEL', 'ROOM_MT_CRENEL_CENTER'),
                                      ('AREA_MT_CRENEL', 'ROOM_MT_CRENEL_WALL_CLIMB'),
                                      ('AREA_MT_CRENEL', 'ROOM_MT_CRENEL_CAVERN_OF_FLAMES_ENTRANCE'),
                                      ('AREA_MT_CRENEL', 'ROOM_MT_CRENEL_TOP')]),
]
REGION_NAME = dict((k, n) for k, n, _ in REGION_ROOMS)
ROOM_REGION = {}
for _k, _n, _rs in REGION_ROOMS:
    for _ar in _rs:
        ROOM_REGION[_ar] = _k

# Survey key -> port-model key, where the two models speak about the same
# thing. EH and WW are three survey regions to one port region, so a port
# crossing cannot be attributed to one of them; those are left out rather
# than guessed at.
OP_KEY = {'CG': 'CG', 'NHF': 'NHF', 'SHF': 'SHF', 'LLR': 'LLR', 'TRIL': 'TRIL',
          'RV': 'RV', 'CW': 'CW', 'WR': 'WR', 'LH': 'LH', 'CREN': 'CREN'}
OP_NEIGHBOUR_PORT = {}      # (op_key, neighbour_op_key) -> port
for (_a, _p), (_b, _bp) in OP.LINKS.items():
    OP_NEIGHBOUR_PORT.setdefault((_a, _b), _p)

# Regions whose survey was DERIVED from a collision flood rather than walked.
FLOOD_REGIONS = {'MW', 'LH'}

# Legs that were driven in the emulator, held-direction, by region_walk.py.
# (region, from area/room, to area/room) - the strongest evidence we have.
WALKED_LEGS = [
    ('EH-N', 'HYRULE_FIELD/EASTERN_HILLS_NORTH', 'MINISH_WOODS/MAIN', 'region_walk.py, y=104 and y=424'),
    ('EH-S', 'HYRULE_FIELD/EASTERN_HILLS_SOUTH', 'MINISH_WOODS/MAIN', 'region_walk.py, y=152'),
    ('LLR', 'HYRULE_FIELD/LON_LON_RANCH', 'LAKE_HYLIA/MAIN', 'region_walk.py, east edge y=440'),
    ('TRIL', 'HYRULE_FIELD/TRILBY_HIGHLANDS', 'MT_CRENEL/ENTRANCE', 'region_walk.py, west edge y=424'),
    ('MW', 'MINISH_WOODS/MAIN', 'HYRULE_FIELD/EASTERN_HILLS_NORTH', 'region_walk.py, west edge y=424'),
    ('LH', 'LAKE_HYLIA/MAIN', 'HYRULE_FIELD/LON_LON_RANCH', 'region_walk.py, west edge y=440'),
]


# --------------------------------------------------------------- the nodes --
# A node is a PLACE: somewhere the player can stand and that the graph has to
# be able to talk about. Four kinds, and the kind decides what evidence can
# possibly exist for it.
#
#   room  - a whole room, entered through a door. "Being in it" is the place.
#   seam  - a crossing OUT of the region: a border row, or a bare scroll seam
#           between two rooms that share an edge and have no row at all.
#   door  - a transition row inside the region that leads somewhere not-region.
#   spot  - a surveyed position that is neither: a pocket, a ledge, a shore.
#
# Each carries `req`, the DNF cost of reaching it FROM THE REGION'S START,
# and `src`, where that cost came from. req None means "the survey looked and
# could not get there"; req missing (not in the dict) means nobody has looked.

def _dnf(req):
    if req is None:
        return None
    return [sorted(t) for t in req]


# A WARP_TYPE_BORDER row carries no trigger rectangle - startX/startY are
# both zero and endX/endY are where you LAND on the far side. The edge it
# covers is in `shape` instead, as an edge plus which half of it, so that is
# what has to be read to say where on the map the crossing is.
BORDER_SHAPE = {
    'TRANSITION_SHAPE_BORDER_NORTH_WEST': ('north', 'west'),
    'TRANSITION_SHAPE_BORDER_NORTH_EAST': ('north', 'east'),
    'TRANSITION_SHAPE_BORDER_NORTH': ('north', None),
    'TRANSITION_SHAPE_BORDER_EAST_NORTH': ('east', 'north'),
    'TRANSITION_SHAPE_BORDER_EAST_SOUTH': ('east', 'south'),
    'TRANSITION_SHAPE_BORDER_EAST': ('east', None),
    'TRANSITION_SHAPE_BORDER_SOUTH_WEST': ('south', 'west'),
    'TRANSITION_SHAPE_BORDER_SOUTH_EAST': ('south', 'east'),
    'TRANSITION_SHAPE_BORDER_SOUTH': ('south', None),
    'TRANSITION_SHAPE_BORDER_WEST_NORTH': ('west', 'north'),
    'TRANSITION_SHAPE_BORDER_WEST_SOUTH': ('west', 'south'),
    'TRANSITION_SHAPE_BORDER_WEST': ('west', None),
}


def _edge_of(x, y, w, h, slack=40):
    if x is None or y is None:
        return None
    if x <= slack:
        return 'west'
    if x >= w - slack:
        return 'east'
    if y <= slack:
        return 'north'
    if y >= h - slack:
        return 'south'
    return None


def geometric_seams(area_name, room_name_, same_area=True):
    """Scroll seams of one room: edges another room's rectangle butts against.

    These are the crossings with NO transition row - the player just walks off
    the edge - so they exist nowhere in transitions.c and would be invisible to
    any audit built on it alone. Most of Hyrule Field is joined this way.

    SAME AREA ONLY, and that restriction is the whole correctness of this
    function. The scroll seam is an ENGINE mechanism: rooms of one area share
    a pixel grid and the camera walks between them. Two rooms in DIFFERENT
    areas can sit flush against each other on the world map and still have no
    crossing at all - Minish Woods and Eastern Hills North are flush, and the
    player gets between them only because transitions.c owns a
    WARP_TYPE_BORDER row there. Reading abutment as a seam invented a dozen
    crossings that do not exist, including a Wind Ruins / Western Wood border.
    Call with same_area=False to ask the other question - who is NEXT TO whom
    on the map - which map_adjacency() uses to find where a crossing could go.
    """
    me = rect_of(area_name, room_name_)
    if not me:
        return []
    x, y, w, h = me
    out = []
    for (oa, orid), (ox, oy, ow, oh) in sorted(RECTS.items()):
        onm = room_name(oa, orid)
        if (oa, onm) == (area_name, room_name_):
            continue
        if same_area != (oa == area_name):
            continue
        if x + w == ox and oy < y + h and y < oy + oh:
            out.append(('east', (max(y, oy) - y, min(y + h, oy + oh) - y), oa, onm))
        if ox + ow == x and oy < y + h and y < oy + oh:
            out.append(('west', (max(y, oy) - y, min(y + h, oy + oh) - y), oa, onm))
        if y + h == oy and ox < x + w and x < ox + ow:
            out.append(('south', (max(x, ox) - x, min(x + w, ox + ow) - x), oa, onm))
        if oy + oh == y and ox < x + w and x < ox + ow:
            out.append(('north', (max(x, ox) - x, min(x + w, ox + ow) - x), oa, onm))
    return out


class Region(object):
    def __init__(self, key):
        self.key = key
        self.name = REGION_NAME[key]
        self.rooms = [r for k, _n, rs in REGION_ROOMS if k == key for r in rs]
        self.survey = WR.SURVEY.get(key)
        self.nodes = []
        self._by_key = {}
        self.unmatched_survey = []
        self.build()

    # -- node bookkeeping --------------------------------------------------
    def add(self, nkey, **kw):
        if nkey in self._by_key:
            return self._by_key[nkey]
        n = dict(idx=len(self.nodes), key=nkey, req='?', src='', note='', flags=[])
        n.update(kw)
        self.nodes.append(n)
        self._by_key[nkey] = n
        return n

    def add_dest_room(self, da, dr, note):
        # The room on the far side of a door or seam is a place too - and a
        # room that belongs to ANOTHER region still has to be a column here,
        # or the border the player walks through leads to nothing the matrix
        # can name.
        if (da, dr) in [(a, r) for a, r in self.rooms]:
            return self._by_key[('room', da, dr)]
        foreign = ROOM_REGION.get((da, dr))
        n = self.add(('room', da, dr), kind='room', label=short(da, dr),
                     area=da, room=dr, x=None, y=None,
                     note=('LEAVES this region, into %s' % foreign) if foreign else note)
        if foreign:
            n['foreign'] = foreign
        return n

    def find_room(self, area_name, rn):
        return self._by_key.get(('room', area_name, rn))

    # -- construction ------------------------------------------------------
    def build(self):
        own_short = set(short(a, r) for a, r in self.rooms)

        multi = len(self.rooms) > 1

        def where(a, r):
            # A label prefix. One-room regions do not need one; Wind Ruins and
            # Mount Crenel are several rooms, and an unprefixed seam label
            # there names two different places with the same words.
            return (short(a, r).split('/')[1] + ' | ') if multi else ''

        # 1. the region's own overworld rooms, in the order REGION_ROOMS gives
        for a, r in self.rooms:
            self.add(('room', a, r), kind='room', label=short(a, r), area=a, room=r,
                     x=None, y=None, note='the region itself'
                     if len(self.rooms) == 1 else 'overworld room of this region')

        # 2. the start the survey was walked from
        if self.survey:
            sa, sr, sx, sy = self.survey['start']
            an, rn = 'AREA_' + sa, 'ROOM_%s_%s' % (sa, sr)
            self.start = self.add(('start',), kind='start',
                                  label='START  ' + short(an, rn), area=an, room=rn,
                                  x=sx, y=sy, note=self.survey.get('note', ''))
            self.start['req'] = []
            self.start['src'] = 'the survey start'
        else:
            self.start = None

        # 3. every transition row the region's own rooms own. startX..endY is
        #    the trigger rectangle in LOCAL coordinates, so this is the exact
        #    list of exit LOCATIONS, not just exit destinations.
        for a, r in self.rooms:
            rect = rect_of(a, r)
            for row in EX.BY_ROOM.get(r, []):
                warp, sx, sy, ex, ey, shape, da, dr = row
                dshort = short(da, dr)
                kind = 'seam' if (warp == 'WARP_TYPE_BORDER' or (da, dr) in ROOM_REGION) else 'door'
                border = BORDER_SHAPE.get(shape) if warp == 'WARP_TYPE_BORDER' else None
                if border:
                    edge, half = border
                    desc = 'border %s%s' % (edge, (' (%s half)' % half) if half else '')
                    px = py = None
                else:
                    desc = 'door (%d,%d)' % (sx, sy)
                    px, py = sx, sy
                n = self.add(('exit', r, sx, sy, dr, shape), kind=kind,
                             label='%s%s -> %s' % (where(a, r), desc, dshort),
                             area=a, room=r, x=px, y=py)
                n['rect'] = None if border else (sx, sy, ex, ey)
                n['dest'] = (da, dr)
                n['warp'] = warp
                n['shape'] = shape
                if border:
                    n['border'] = border
                # the room on the far side is a place too
                self.add_dest_room(da, dr, 'reached through ' + short(a, r))

        # 4. scroll seams, which own no row at all
        for a, r in self.rooms:
            for edge, span, oa, onm in geometric_seams(a, r):
                if (oa, onm) in ROOM_REGION and ROOM_REGION[(oa, onm)] == self.key:
                    tag = 'another room of this region'
                else:
                    tag = ROOM_REGION.get((oa, onm), 'a room outside the region')
                self.add(('seam', r, edge, oa, onm), kind='seam',
                         label='%sscroll seam %s %s-%s -> %s' % (
                             where(a, r), edge, span[0], span[1], short(oa, onm)),
                         area=a, room=r, x=None, y=None,
                         note='no transition row, the player walks off the edge '
                              '(into %s)' % tag,
                         edge=edge, span=span, dest=(oa, onm))
                self.add_dest_room(oa, onm, 'across a scroll seam')

        # 5. hang the survey's measurements on the nodes they describe
        if self.survey:
            for e in self.survey['dests']:
                self.attach(e)
            # the start stands in a room, so that room costs nothing to be in
            home = self._by_key.get(('room', self.start['area'], self.start['room']))
            if home is not None and home['req'] == '?':
                home['req'] = []
                home['src'] = 'the survey start stands in it'

        # 6. a door is priced by the room behind it. The survey never records
        #    door positions - it records what it cost to END UP somewhere - so
        #    the cost of the room on the far side is also the cost of reaching
        #    the door, PROVIDED that door is the only way in. Where a room has
        #    several doors from this region the survey cannot say which one it
        #    walked to, and guessing would put a price on a door that may be
        #    the expensive one; those stay unmeasured and say why.
        doors_to = {}
        for n in self.nodes:
            if n.get('dest') and n['kind'] in ('door', 'seam'):
                doors_to.setdefault(n['dest'], []).append(n)
        for dest, ds in doors_to.items():
            room = self._by_key.get(('room',) + dest)
            if room is None or room['req'] == '?':
                continue
            if len(ds) == 1:
                ds[0]['req'] = room['req']
                ds[0]['src'] = 'implied: the only door to a priced room'
                ds[0]['flags'] = list(ds[0]['flags']) + [f for f in room['flags']
                                                         if f not in ds[0]['flags']]
                ds[0]['implied'] = True
            else:
                for n in ds:
                    n['note'] = (n['note'] + '; ' if n['note'] else '') + \
                        ('%d doors lead to %s, so the survey\'s price for that '
                         'room cannot be pinned on this one' % (len(ds), short(*dest)))

    def attach(self, e):
        an, rn = 'AREA_' + e['area'], 'ROOM_%s_%s' % (e['area'], e['room'])
        x, y = e['local']
        req = _dnf(e['req'])
        src = 'flood-derived' if self.key in FLOOD_REGIONS else 'walked survey'
        target = None

        if (an, rn) in [(a, r) for a, r in self.rooms]:
            # a place INSIDE the region: an exit rectangle, a scroll seam, or
            # a pocket the survey named by coordinate alone.
            if x is not None and 0 <= x <= 2000 and 0 <= y <= 2000:
                for n in self.nodes:
                    if n.get('rect') and n['room'] == rn:
                        sx, sy, ex, ey = n['rect']
                        if min(sx, ex) - 24 <= x <= max(sx, ex) + 24 and \
                           min(sy, ey) - 24 <= y <= max(sy, ey) + 24:
                            target = n
                            break
                if target is None:
                    rect = rect_of(an, rn)
                    if rect:
                        edge = _edge_of(x, y, rect[2], rect[3])
                        if edge:
                            along = y if edge in ('east', 'west') else x
                            extent = rect[3] if edge in ('east', 'west') else rect[2]
                            for n in self.nodes:
                                if n.get('edge') == edge and n['room'] == rn and \
                                        n['span'][0] - 48 <= along <= n['span'][1] + 48:
                                    target = n
                                    break
                            # a border row instead: it owns no rectangle, so
                            # the edge and which HALF of it is all there is to
                            # match on.
                            if target is None:
                                half = ('north' if along < extent / 2 else 'south') \
                                    if edge in ('east', 'west') else \
                                    ('west' if along < extent / 2 else 'east')
                                cands = [n for n in self.nodes
                                         if n.get('border') and n['room'] == rn
                                         and n['border'][0] == edge]
                                exact = [n for n in cands if n['border'][1] == half]
                                whole = [n for n in cands if n['border'][1] is None]
                                if exact:
                                    target = exact[0]
                                elif whole:
                                    target = whole[0]
                                elif cands:
                                    target = cands[0]
            if target is None:
                target = self.add(('spot', rn, x, y), kind='spot',
                                  label='%s (%s,%s)' % (short(an, rn), x, y),
                                  area=an, room=rn, x=x, y=y)
        else:
            target = self.find_room(an, rn)
            if target is None:
                target = self.add(('room', an, rn), kind='room', label=short(an, rn),
                                  area=an, room=rn, x=None, y=None,
                                  note='named by the survey; no row from this region '
                                       'room reaches it directly')
                self.unmatched_survey.append(short(an, rn))

        # A node can be named by more than one survey row (two entrances to
        # one pocket). Keep the CHEAPER reading and say so, never silently.
        if target['req'] == '?' or target['req'] is None:
            target['req'] = req
        elif req is not None and len(req) and target['req'] is not None:
            for t in req:
                if t not in target['req']:
                    target['req'].append(t)
        target['src'] = src
        if e.get('note'):
            target['note'] = (target['note'] + '; ' if target['note'] else '') + e['note']
        if req and any('unsurveyed' in t for t in req):
            target['flags'].append('unsurveyed')
        if e.get('note') and 'one-way' in e['note']:
            target['flags'].append('one-way')
        if req is None:
            target['flags'].append('not-reachable-from-start')


# ------------------------------------------------------------- the evidence --
# One letter per ordered pair. The letter says WHAT KIND of thing we know,
# the digit in the second matrix says how much it is worth.
CODES = [
    ('.', 'the diagonal - a place to itself, nothing to measure'),
    ('W', 'WALKED. Driven in the emulator, held-direction, and it arrived. '
          'tools/quickstart/region_walk.py'),
    ('D', 'DOOR. A transition row or a shared room edge joins these two '
          'directly; crossing is instant and free once you are standing on it. '
          'src/data/transitions.c and gAreaRoomHeaders'),
    ('d', 'DOOR, RETURN SIDE. The far room owns a row back here, so a way back '
          'exists - but where inside that room it starts is not measured'),
    ('S', 'SURVEY. The user walked it in the mapexplore build and wrote down '
          'the cost. An UPPER BOUND from the start point, never a proof that '
          'no cheaper route exists'),
    ('s', 'SURVEY, ONE STEP BACK. The survey priced the ROOM behind this door, '
          'and exactly one door leads there, so reaching the door cost at most '
          'the same. Sound where the door is the only way in; silent about '
          'which of several doors was used when there is more than one'),
    ('F', 'FLOOD. Derived by flooding the live collision grid, not walked. '
          'Geometry only: it can prove a door is walkable, it cannot tell a '
          'wall from a wall with a bomb crack'),
    ('P', 'PORT MODEL. The region-level entrance-to-entrance survey in '
          'tools/quickstart/overworld_paths.py'),
    ('i', 'INFERRED. No direct measurement; both ends are priced from the '
          'start, so A -> start -> B is the route. ASSUMES the trip back to '
          'the start is free, which nobody has measured'),
    ('X', 'MEASURED UNREACHABLE. The survey looked for a way and found none '
          'from its start point'),
    ('-', 'NOTHING. No measurement, no inference. This is the gap to fill'),
]
PRIORITY = {'-': 0, 'i': 1, 'P': 2, 's': 3, 'd': 3, 'F': 4, 'S': 5, 'X': 5, 'D': 6, 'W': 7}
CONF = {'.': '.', 'W': 4, 'D': 4, 'd': 3, 'S': 3, 'X': 3, 'P': 2, 's': 2, 'F': 1, 'i': 1, '-': 0}
CONF_LEGEND = [
    (4, 'HIGH - the ROM says so, or the emulator did it'),
    (3, 'GOOD - the user walked it; still an upper bound from one start'),
    (2, 'FAIR - the coarser port-level model, region granularity only'),
    (1, 'LOW - an inference, or geometry with the gates guessed at'),
    (0, 'NONE - nothing at all'),
]


def and_req(a, b):
    """AND two DNFs and drop any term that is a superset of another."""
    if a is None or b is None:
        return None
    terms = []
    for ta in (a or [[]]):
        for tb in (b or [[]]):
            terms.append(sorted(set(ta) | set(tb)))
    out = []
    for t in terms:
        if any(set(o) < set(t) for o in terms):
            continue
        if t not in out:
            out.append(t)
    return out


def fmt_req(r):
    if r == '?':
        return '?'
    if r is None:
        return 'IMPOSSIBLE'
    if not r or r == [[]]:
        return 'free'
    return ' OR '.join('+'.join(t) for t in r)


class Matrix(object):
    def __init__(self, region):
        self.R = region
        n = len(region.nodes)
        self.n = n
        self.code = [['-'] * n for _ in range(n)]
        self.req = [[None] * n for _ in range(n)]
        self.why = [[''] * n for _ in range(n)]
        self.fill()

    def put(self, i, j, code, req, why):
        if i == j:
            return
        if PRIORITY[code] < PRIORITY[self.code[i][j]]:
            return
        self.code[i][j] = code
        self.req[i][j] = req
        self.why[i][j] = why

    def fill(self):
        R = self.R
        nodes = R.nodes
        for i in range(self.n):
            self.code[i][i] = '.'

        # -- inference through the start, the weakest thing we allow --------
        priced = [n for n in nodes
                  if n['req'] not in ('?', None)
                  and 'one-way' not in n['flags'] and n['kind'] != 'start']
        for a in priced:
            for b in priced:
                if a is b:
                    continue
                self.put(a['idx'], b['idx'], 'i', and_req(a['req'], b['req']),
                         'back to %s, then out again' % (R.start['label'] if R.start else 'start'))

        # -- the port model, where a region maps one-to-one onto one --------
        opk = OP_KEY.get(R.key)
        if opk:
            seams = [n for n in nodes if n['kind'] == 'seam' and n.get('dest')]
            for a in seams:
                for b in seams:
                    if a is b:
                        continue
                    ra = ROOM_REGION.get(a['dest'])
                    rb = ROOM_REGION.get(b['dest'])
                    pa = OP_NEIGHBOUR_PORT.get((opk, OP_KEY.get(ra)))
                    pb = OP_NEIGHBOUR_PORT.get((opk, OP_KEY.get(rb)))
                    if not pa or not pb or pa == pb:
                        continue
                    dnf = OP.TRAVERSAL.get((opk, pa, pb))
                    if dnf is None:
                        continue
                    if dnf == OP.IMPOSSIBLE:
                        self.put(a['idx'], b['idx'], 'X', None,
                                 'overworld_paths: %s %s->%s is one-way shut' % (opk, pa, pb))
                    else:
                        self.put(a['idx'], b['idx'], 'P', [sorted(t) for t in dnf],
                                 'overworld_paths %s %s->%s' % (opk, pa, pb))

        # -- what the survey actually measured ------------------------------
        if R.start:
            s = R.start['idx']
            for n in nodes:
                if n['kind'] == 'start' or n['req'] == '?':
                    continue
                if n['req'] is None:
                    self.put(s, n['idx'], 'X', None, 'the survey found no route from the start')
                    continue
                if n.get('implied'):
                    code = 's'
                else:
                    code = 'F' if R.key in FLOOD_REGIONS else 'S'
                self.put(s, n['idx'], code, n['req'], n['src'])
                if 'one-way' not in n['flags']:
                    self.put(n['idx'], s, 'i', n['req'],
                             'the reverse of a one-way measurement; not itself measured')

        # -- doors and seams: the ROM's own edges ---------------------------
        by_room = {}
        for n in nodes:
            if n['kind'] == 'room':
                by_room[(n['area'], n['room'])] = n
        for n in nodes:
            dest = n.get('dest')
            if not dest or n['kind'] == 'room':
                continue
            tgt = by_room.get(dest)
            here = by_room.get((n['area'], n['room']))
            if tgt is not None:
                self.put(n['idx'], tgt['idx'], 'D', [],
                         'transitions.c row' if n.get('warp') else 'shared room edge')
                # the way back, if the far room owns a row pointing at us
                back = any(row[7] == n['room'] for row in EX.BY_ROOM.get(dest[1], []))
                if n.get('edge'):
                    back = True          # a scroll seam is two-way geometry
                if back:
                    self.put(tgt['idx'], n['idx'], 'd', None,
                             'the far room has a way back, but where in it is unmeasured')
            if here is not None:
                # standing in the room is not standing on the door; that walk
                # is exactly what is unmeasured, so no edge is drawn here.
                pass

        # -- emulator walks, which beat everything --------------------------
        for reg, a_short, b_short, why in WALKED_LEGS:
            if reg != R.key:
                continue
            for n in nodes:
                if not n.get('dest'):
                    continue
                if short(n['area'], n['room']) != a_short:
                    continue
                if short(*n['dest']) != b_short:
                    continue
                tgt = by_room.get(n['dest'])
                if tgt is not None:
                    self.put(n['idx'], tgt['idx'], 'W', [], why)

    def counts(self):
        out = {}
        for row in self.code:
            for c in row:
                out[c] = out.get(c, 0) + 1
        return out


# ------------------------------------------------------------- the regions --
def all_regions():
    return [Region(k) for k, _n, _r in REGION_ROOMS]


def map_adjacency(regs=None):
    """Rooms that are flush against each other on the world map but in
    different areas - so the engine will NOT walk between them, and a
    WARP_TYPE_BORDER row is the only way across.

    Where a row exists this says nothing new. Where one does not, it is a
    place a crossing COULD be put, and a place the map looks connected to a
    player and is not."""
    regs = regs or all_regions()
    out = []
    for R in regs:
        for a, r in R.rooms:
            for edge, span, oa, onm in geometric_seams(a, r, same_area=False):
                rows = [row for row in EX.BY_ROOM.get(r, []) if row[7] == onm]
                out.append(dict(region=R.key, frm=short(a, r), edge=edge, span=span,
                                to=short(oa, onm), to_region=ROOM_REGION.get((oa, onm)),
                                rows=len(rows)))
    return out


def cross_region(regs=None):
    """Region x region: which regions touch, by how many crossings, and what
    the survey charges for the one it priced.

    A cell here is the answer to "can a run walk from this region into that
    one at all", which is the coarsest version of the same question the
    per-region matrices ask. It is also the only view that shows a region
    with no way out."""
    regs = regs or all_regions()
    grid = {}
    for R in regs:
        for n in R.nodes:
            dest = n.get('dest')
            if not dest:
                continue
            other = ROOM_REGION.get(dest)
            if not other or other == R.key:
                continue
            cell = grid.setdefault((R.key, other), dict(ways=[], req='?', kinds=set()))
            cell['ways'].append(n['label'])
            cell['kinds'].add('seam' if n.get('edge') else 'row')
            if n['req'] not in ('?', None) and cell['req'] == '?':
                cell['req'] = n['req']
    return grid


# ------------------------------------------------------------------ output --
def summary():
    regs = all_regions()
    print('=== traversability audit ===')
    if RECT_ERR:
        print('  !! no room rectangles (%s) - scroll seams are MISSING from this run' % RECT_ERR)
    tot = dict()
    print('\n%-6s %-22s %5s %5s %5s %5s %5s   %s' %
          ('key', 'region', 'nodes', 'seams', 'doors', 'rooms', 'spots', 'cells with no data'))
    for R in regs:
        M = Matrix(R)
        c = M.counts()
        for k, v in c.items():
            tot[k] = tot.get(k, 0) + v
        kinds = {}
        for n in R.nodes:
            kinds[n['kind']] = kinds.get(n['kind'], 0) + 1
        cells = R_cells = len(R.nodes) * (len(R.nodes) - 1)
        print('%-6s %-22s %5d %5d %5d %5d %5d   %5d / %-5d (%3d%%)' %
              (R.key, R.name, len(R.nodes), kinds.get('seam', 0), kinds.get('door', 0),
               kinds.get('room', 0), kinds.get('spot', 0),
               c.get('-', 0), cells, (100 * c.get('-', 0) // cells) if cells else 0))
    print('\ncell totals: ' + ', '.join('%s=%d' % (k, tot[k]) for k in sorted(tot)))

    print('\n--- places with NO measurement of any kind (req never taken) ---')
    n_gap = 0
    for R in regs:
        gaps = [n for n in R.nodes if n['req'] == '?' and n['kind'] != 'room']
        rooms = [n for n in R.nodes if n['req'] == '?' and n['kind'] == 'room']
        if not gaps and not rooms:
            continue
        print('  %-6s %2d exits/seams, %2d rooms' % (R.key, len(gaps), len(rooms)))
        n_gap += len(gaps) + len(rooms)
    print('  %d places total' % n_gap)

    print('\n--- measurements tainted by an untestable token ---')
    for R in regs:
        bad = [n for n in R.nodes if 'unsurveyed' in n['flags']]
        if bad:
            print('  %-6s %d: %s' % (R.key, len(bad), ', '.join(n['label'] for n in bad)))


def grid_block(M, R):
    """The matrix as fixed-width text: one column per node, indexed by number."""
    n = M.n
    w = max(2, len(str(n)))
    head = []
    for digit in range(len(str(n))):
        line = ' ' * (w + 1)
        for j in range(n):
            s = str(j + 1).rjust(len(str(n)))
            line += s[digit] + ' '
        head.append(line.rstrip())
    return head, w


def md_region(R, out):
    M = Matrix(R)
    n = len(R.nodes)
    out.append('')
    out.append('### %s  `%s`' % (R.name, R.key))
    out.append('')
    if R.survey:
        out.append('Survey start: `%s` at %s. %s' % (
            R.start['label'].replace('START  ', ''),
            (R.start['x'], R.start['y']), R.survey.get('note', '')))
        if R.survey['room_req']:
            out.append('')
            out.append('**Region entry cost: %s** - every row below is on top of it.'
                       % fmt_req(_dnf(R.survey['room_req'])))
    else:
        out.append('_No survey has been walked in this region._')
    out.append('')
    out.append('| # | kind | place | cost from start | evidence | notes |')
    out.append('|--:|:--|:--|:--|:--|:--|')
    for i, nd in enumerate(R.nodes):
        flag = ' ⚠' if nd['flags'] else ''
        out.append('| %d | %s | `%s` | %s | %s | %s |' % (
            i + 1, nd['kind'], nd['label'], fmt_req(nd['req']),
            nd['src'] or ('—' if nd['req'] == '?' else ''),
            (nd['note'] + flag).replace('|', '/')))
    for title, mat in (('Evidence', M.code), ('Confidence', None)):
        out.append('')
        out.append('**%s matrix** — row = FROM, column = TO.' % title)
        out.append('')
        out.append('```')
        hdr, w = grid_block(M, R)
        for h in hdr:
            out.append(h)
        for i in range(n):
            row = str(i + 1).rjust(w) + ' '
            for j in range(n):
                c = M.code[i][j]
                row += (c if mat is not None else str(CONF[c])) + ' '
            out.append(row.rstrip() + '   ' + R.nodes[i]['label'][:46])
        out.append('```')
    c = M.counts()
    out.append('')
    out.append('%d nodes, %d ordered pairs, **%d with no data** (%d%%).' % (
        n, n * (n - 1), c.get('-', 0),
        (100 * c.get('-', 0) // (n * (n - 1))) if n > 1 else 0))
    return M


def write_md(path):
    regs = all_regions()
    out = []
    out.append('# Traversability audit')
    out.append('')
    out.append('Generated by `tools/quickstart/traversal_audit.py`. Do not hand-edit: '
               'add measurements to `tools/quickstart/world_reach.py` and regenerate.')
    out.append('')
    out.append('This is an inventory of what has been MEASURED about walking around '
               'this world, not a claim about what is walkable. Every blank cell is '
               'a question nobody has asked yet.')
    out.append('')
    out.append('## How to read a cell')
    out.append('')
    out.append('| code | meaning |')
    out.append('|:--:|:--|')
    for c, why in CODES:
        out.append('| `%s` | %s |' % (c, why))
    out.append('')
    out.append('| confidence | meaning |')
    out.append('|:--:|:--|')
    for c, why in CONF_LEGEND:
        out.append('| `%s` | %s |' % (c, why))
    out.append('')
    out.append('## Regions')
    out.append('')
    out.append('| key | region | nodes | seams | doors | rooms | spots | no data |')
    out.append('|:--|:--|--:|--:|--:|--:|--:|--:|')
    mats = {}
    for R in regs:
        M = Matrix(R)
        mats[R.key] = M
        kinds = {}
        for nd in R.nodes:
            kinds[nd['kind']] = kinds.get(nd['kind'], 0) + 1
        cells = len(R.nodes) * (len(R.nodes) - 1)
        out.append('| `%s` | %s | %d | %d | %d | %d | %d | %d%% |' % (
            R.key, R.name, len(R.nodes), kinds.get('seam', 0), kinds.get('door', 0),
            kinds.get('room', 0), kinds.get('spot', 0),
            (100 * M.counts().get('-', 0) // cells) if cells else 0))
    # -- region x region ------------------------------------------------
    grid = cross_region(regs)
    keys = [R.key for R in regs]
    out.append('')
    out.append('## Region to region')
    out.append('')
    out.append('How many crossings lead from the row region into the column '
               'region, and what the survey charges for one of them. `·` is '
               'the diagonal; blank means the two regions do not touch.')
    out.append('')
    out.append('```')
    out.append('FROM \\ TO   ' + ' '.join(k.rjust(4) for k in keys))
    for a in keys:
        line = a.ljust(11) + ' '
        for b in keys:
            if a == b:
                line += '   . '
            else:
                c = grid.get((a, b))
                line += (('%3dx ' % len(c['ways'])) if c else '     ')
        out.append(line.rstrip())
    out.append('```')
    out.append('')
    out.append('| from | to | crossings | cheapest priced crossing |')
    out.append('|:--|:--|--:|:--|')
    for (a, b), c in sorted(grid.items()):
        out.append('| `%s` | `%s` | %d | %s |' % (a, b, len(c['ways']), fmt_req(c['req'])))
    # -- flush on the map, but not joined ---------------------------------
    adj = [a for a in map_adjacency(regs) if not a['rows']]
    out.append('')
    out.append('## Flush on the map, no crossing')
    out.append('')
    out.append('Rooms in DIFFERENT areas whose rectangles touch. The engine '
               'only scroll-walks between rooms of the same area, so these '
               'look joined on the map and are not: crossing needs a '
               '`WARP_TYPE_BORDER` row, and none of these has one. Each is '
               'either a border we could add or a wall the player will '
               'believe is a path.')
    out.append('')
    if not adj:
        out.append('_None - every flush pair has a border row._')
    else:
        out.append('| region | room | edge | span | touches | that region |')
        out.append('|:--|:--|:--|:--|:--|:--|')
        for a in adj:
            out.append('| `%s` | `%s` | %s | %d-%d | `%s` | %s |' % (
                a['region'], a['frm'], a['edge'], a['span'][0], a['span'][1],
                a['to'], a['to_region'] or '—'))
    out.append('')
    out.append('## Per-region node lists and matrices')
    for R in regs:
        md_region(R, out)
    open(path, 'w').write('\n'.join(out) + '\n')
    return path


def write_json(path):
    regs = all_regions()
    blob = dict(regions=[], codes=CODES, confidence=CONF_LEGEND,
                conf_map=dict((k, v) for k, v in CONF.items()),
                cross=[dict(frm=a, to=b, ways=c['ways'], req=fmt_req(c['req']))
                       for (a, b), c in sorted(cross_region(regs).items())],
                flush=[a for a in map_adjacency(regs) if not a['rows']])
    for R in regs:
        M = Matrix(R)
        blob['regions'].append(dict(
            key=R.key, name=R.name, surveyed=bool(R.survey),
            note=(R.survey or {}).get('note', ''),
            room_req=_dnf((R.survey or {}).get('room_req') or []),
            start=R.start['label'] if R.start else None,
            rooms=[short(a, r) for a, r in R.rooms],
            nodes=[dict(i=nd['idx'], kind=nd['kind'], label=nd['label'],
                        area=nd['area'], room=nd['room'], x=nd['x'], y=nd['y'],
                        req=(None if nd['req'] == '?' else nd['req']),
                        measured=(nd['req'] != '?'), src=nd['src'],
                        note=nd['note'], flags=nd['flags'],
                        dest=(short(*nd['dest']) if nd.get('dest') else None))
                   for nd in R.nodes],
            code=[''.join(r) for r in M.code],
            conf=[''.join(str(CONF[c]) for c in r) for r in M.code],
            # SPARSE. A full N x N of strings is almost entirely the empty
            # cell repeated, and for Mount Crenel alone that is 5,400 copies
            # of nothing; only the cells that say something are stored.
            cell=dict(('%d,%d' % (i, j),
                       dict(why=M.why[i][j],
                            req=(fmt_req(M.req[i][j]) if M.req[i][j] != '?' else '?')))
                      for i in range(M.n) for j in range(M.n)
                      if M.code[i][j] not in ('-', '.'))))
    open(path, 'w').write(json.dumps(blob, separators=(',', ':')))
    return path


def main():
    if '--md' in sys.argv:
        print('wrote', write_md(os.path.join(ROOT, 'docs', 'QUICKSTART_TRAVERSAL_AUDIT.md')))
    if '--json' in sys.argv:
        print('wrote', write_json(os.path.join(ROOT, 'docs', 'quickstart_traversal.json')))
    if '--region' in sys.argv:
        key = sys.argv[sys.argv.index('--region') + 1]
        out = []
        md_region(Region(key), out)
        print('\n'.join(out))
        return 0
    if '--md' not in sys.argv and '--json' not in sys.argv:
        summary()
    return 0


if __name__ == '__main__':
    sys.exit(main())
