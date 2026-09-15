"""How many distinct TILE CLASSES does the world actually use?

Stage 1 of the world-reachability model (see the roadmap). The answer this
printed on the fifteen region rooms - 397 classes over ~24,000 tiles - is
what says the model is tractable at all: a requirement is a property of the
CLASS, so the measurement burden is a few hundred things once rather than
tens of thousands of things ever.

The scaling question behind a world-reachability model is not "how many
squares are there" (tens of thousands) but "how many distinct kinds of
square are there" - because a requirement is a property of the KIND, and
each kind only has to be measured once, anywhere.

A class here is the triple the engine itself keys on:
    collisionData[pos]                 - what blocks movement
    tileTypes[mapData[pos]]            - what the tile IS
    actTiles[pos]                      - the special behaviour (holes, ledges)
"""
import sys, gc, collections
sys.path.insert(0, '/home/user/bartgame/tools/quickstart')
from emu import boot, warp, here, poison_here, room_dims
import parse_tables as P

MAP = 0x02025eb0
MAPDATA = MAP + 0x0004
COLL = MAP + 0x2004
TILETYPES = MAP + 0x5004
ACT = MAP + 0xb004


def u16(c, a):
    return c.memory.u8[a] | (c.memory.u8[a + 1] << 8)


classes = collections.Counter()
per_room = {}
rooms = [(r['areaName'], r['roomName'], r['area'], r['room'], r['entrance']) for r in P.region_pool()]
for an, rn, a, r, ent in rooms:
    gc.collect()
    c = boot('/home/user/bartgame/tmc.gba')
    poison_here(c)
    warp(c, a, r, ent[0], ent[1], 400)
    if here(c) != (a, r):
        print('%-40s did not land' % rn[5:])
        del c
        continue
    W, H = room_dims(c)
    tw, th = W // 16, H // 16
    seen = set()
    for ty in range(min(th, 64)):
        for tx in range(min(tw, 64)):
            pos = tx + (ty << 6)
            col = c.memory.u8[COLL + pos]
            idx = u16(c, MAPDATA + pos * 2)
            typ = u16(c, TILETYPES + (idx & 0x3ff) * 2)
            act = c.memory.u8[ACT + pos]
            key = (col, typ, act)
            classes[key] += 1
            seen.add(key)
    per_room[rn[5:]] = len(seen)
    print('%-40s %2dx%-2d tiles, %3d distinct classes' % (rn[5:], tw, th, len(seen)), flush=True)
    del c

print('\n%d distinct (collision, tileType, actTile) classes across %d region rooms'
      % (len(classes), len(per_room)))
print('\nthe 30 most common:')
for (col, typ, act), n in classes.most_common(30):
    print('   coll %#04x  type %#06x  act %#04x   %6d tiles' % (col, typ, act, n))
walk = sum(n for (col, typ, act), n in classes.items() if col == 0)
print('\ncollision 0 (plain floor) covers %d tiles in %d classes'
      % (walk, sum(1 for (col, t, a) in classes if col == 0)))
print('non-zero collision: %d classes' % sum(1 for (col, t, a) in classes if col != 0))
