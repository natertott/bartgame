"""Which QUICKSTART rooms share a scroll seam with a neighbour?

Rooms inside one area live on a shared pixel grid (gAreaRoomHeaders gives
each room's map_x/map_y and pixel size). Two rooms whose rectangles touch
along an edge are joined by a SCROLL seam, not a door: the player crosses by
walking, and the engine wipes gRoomVars.flags on the way - which resets every
per-visit "already spawned this event" latch QUICKSTART keeps there.

That is harmless for a chest and fatal for a fight, so the combat kinds need
to know. Run from the repo root; prints every content-site / pool room that
has a seam, with the edge it is on.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_tables as P

ROOT = P.ROOT
ROM = open(os.path.join(ROOT, 'tmc.gba'), 'rb').read()
MAP = open(os.path.join(ROOT, 'build/USA/tmc.map')).read()


def sym(name):
    for line in MAP.split('\n'):
        parts = line.split()
        if len(parts) == 2 and parts[1] == name and parts[0].startswith('0x'):
            return int(parts[0], 16) - 0x08000000
    raise KeyError(name)


def room_rects(area, max_rooms=16):
    """(map_x, map_y, w, h) for every room in `area` that has a real size."""
    ptr = struct.unpack('<I', ROM[sym('gAreaRoomHeaders') + area * 4:][:4])[0]
    if not 0x08000000 <= ptr < 0x0A000000:
        return {}
    base = ptr - 0x08000000
    out = {}
    for room in range(max_rooms):
        x, y, w, h, _ts = struct.unpack('<5H', ROM[base + room * 10:base + room * 10 + 10])
        if w == 0 or h == 0 or w > 0x2000 or h > 0x2000:
            continue
        out[room] = (x, y, w, h)
    return out


def seams(area, room):
    """Edges of (area, room) that another room in the same area butts against."""
    rects = room_rects(area)
    if room not in rects:
        return []
    x, y, w, h = rects[room]
    found = []
    for other, (ox, oy, ow, oh) in rects.items():
        if other == room:
            continue
        # Overlap on the perpendicular axis is what makes a seam walkable;
        # touching only at a corner is not a seam.
        if oy + oh == y and ox < x + w and x < ox + ow:
            found.append(('north', other))
        if y + h == oy and ox < x + w and x < ox + ow:
            found.append(('south', other))
        if ox + ow == x and oy < y + h and y < oy + oh:
            found.append(('west', other))
        if x + w == ox and oy < y + h and y < oy + oh:
            found.append(('east', other))
    return found


def main():
    rooms = {}
    for row in P.content_sites():
        _kinds, _large, area, room, _cx, _cy = row
        rooms.setdefault((area, room), []).append('content site')
    try:
        for d in P.pool_doors():
            rooms.setdefault((d['area'], d['room']), []).append('2-door pool')
    except Exception:
        pass
    bad = 0
    for (area, room), uses in sorted(rooms.items()):
        s = seams(area, room)
        if not s:
            continue
        bad += 1
        print('area %-3d room %-3d (%s): %s' % (area, room, ', '.join(sorted(set(uses))),
                                                ', '.join('%s->room %d' % e for e in s)))
    print('\n%d of %d QUICKSTART rooms have a scroll seam.' % (bad, len(rooms)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
