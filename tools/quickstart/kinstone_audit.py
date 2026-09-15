"""Audit every Kinstone fusion whose world event lands in a room we use.

QUICKSTART pre-fuses all 100 vanilla fusions at boot, which is what holds the
overworld in its post-fusion shape. Any fusion we want the player to earn has
to be un-fused - but only the ones that actually change a room we visit are
worth wiring a fuser for.

This reads the two ROM tables that decide that:

  gKinstoneWorldEvents[kinstoneId]  -> worldEventId (when subtask == 8)
  gWorldEvents[worldEventId]        -> area, room, type, position

and cross-references them against the QUICKSTART region list and the ? room
content sites, so the answer comes from the shipped data rather than a survey.
"""
import os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_tables as T

ROOT = T.ROOT
ROM = open(os.path.join(ROOT, 'tmc.gba'), 'rb').read()
MAP = open(os.path.join(ROOT, 'build/USA/tmc.map')).read()

SUBTASK_WORLDEVENT = 8

WORLD_EVENT_TYPES = {
    0: 'nothing',
    1: 'load room entity (global-flag gated)',
    2: 'sub_08018BB4 - treasure/chest marker',
    3: 'load room entity (inventory gated)',
    4: 'sub_08018A58',
    5: 'sub_08018B50 - remove water / open path',
    6: 'sub_08018AB4 - place blocking tile when NOT fused',
    7: 'load room entity or sub_080189EC',
    8: 'set a tile type',
    9: 'load room entity + set tile type',
    10: 'beanstalk',
    11: 'load room entity + entity rails',
    15: 'load one of two room entities',
    17: 'set local flag + load room entity list',
}

AREA_NAME = {v: k for k, v in T.AREAS.items()}


def sym(name):
    for line in MAP.split('\n'):
        parts = line.split()
        if len(parts) == 2 and parts[1] == name and parts[0].startswith('0x'):
            return int(parts[0], 16) - 0x08000000
    raise KeyError(name)


def room_name(area, room):
    an = AREA_NAME.get(area, 'AREA_%d' % area)
    for nm, idx in T.ROOMS.items():
        if idx != room:
            continue
        # roomid.h groups room names under their area comment; match on prefix.
        stem = an.replace('AREA_', 'ROOM_')
        if nm.startswith(stem):
            return nm
    return '%s room %d' % (an, room)


def main():
    kwe = sym('gKinstoneWorldEvents')
    we = sym('gWorldEvents')

    # Rooms we care about: every QUICKSTART region and every ? room site.
    interesting = {}
    for r in T.region_pool():
        interesting[(T.AREAS[r['areaName']], T.ROOMS[r['roomName']])] = 'region ' + r['roomName']
    for an, rn, area, room, _cx, _cy in T.content_sites():
        interesting.setdefault((area, room), '? site ' + rn)
    for p in T.pool_rows():
        interesting.setdefault((T.AREAS[p['areaName']], T.ROOMS[p['roomName']]), 'pool ' + p['roomName'])

    # A fusion only completes when the piece the player picks has the same
    # `shape` as the target (kinstoneMenu.c, KinstoneMenu_Type3_Overlay1).
    # Piece ids 0x65..0x75 are the ones AddKinstoneToBag accepts; 0x6E..0x75
    # are the eight the enemy droptable can actually produce.
    shape_of = {}
    for pid in range(0x65, 0x76):
        shape_of[pid] = ROM[kwe + pid * 8 + 5]
    droppable = {pid: shape_of[pid] for pid in range(0x6E, 0x76)}

    hits, misses = [], 0
    for kid in range(1, 101):
        objPalette, gfxPiece, gfxFull, subtask, weid, shape, bubble, marker = ROM[kwe + kid * 8: kwe + kid * 8 + 8]
        if subtask != SUBTASK_WORLDEVENT or weid == 0:
            continue
        off = we + weid * 20
        etype, entity_idx, area, room = ROM[off:off + 4]
        ox, oy, x, y = struct.unpack('<4H', ROM[off + 4:off + 12])
        key = (area, room)
        if key in interesting:
            hits.append((kid, weid, etype, shape, x, y, interesting[key]))
        else:
            misses += 1

    print('Kinstone fusions with a world event in a room QUICKSTART uses')
    print('=' * 78)
    by_room = {}
    for kid, weid, etype, shape, x, y, why in hits:
        by_room.setdefault(why, []).append((kid, weid, etype, shape, x, y))
    for why in sorted(by_room):
        print('\n%s' % why)
        for kid, weid, etype, shape, x, y in sorted(by_room[why]):
            pieces = ' '.join('%02X' % p for p, s in sorted(droppable.items()) if s == shape)
            print('  KINSTONE_%-3X we %-3d type %-2d shape %-3d at (%4d,%4d)  %-40s  drop pieces: %s'
                  % (kid, weid, etype, shape, x, y, WORLD_EVENT_TYPES.get(etype, '?'),
                     pieces or 'NONE - not obtainable from enemy drops'))
    print('\n%d fusion(s) land in rooms we use; %d land elsewhere in the game.'
          % (len(hits), misses))

    print('\nDroppable piece id -> shape: '
          + ', '.join('%02X:%d' % (p, s) for p, s in sorted(droppable.items())))


if __name__ == '__main__':
    main()
