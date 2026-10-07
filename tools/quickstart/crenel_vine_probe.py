"""Mount Crenel's bean vine (Oct 2026, a user report): is it really grown?

The run start sets WATERBEAN_OUT and WATERBEAN_PUT, and for a long time the
mode believed that was the whole pre-grow - "both sprouts sit in action 4,
their grown state". Action 4 is the seed in its hole waiting for the water.
The vine itself is laid only once the sprout's LOCAL flag (YAMA_04_00 /
YAMA_04_01, the sprout's type2) is set, and the run start wipes every local
flag. So: climbing up from the base did nothing, and a player who climbed
DOWN from Center - whose vine tiles are map data - arrived at the seam on a
solid tile inside the mountain. The run start sets the two flags now.

  GROWN    no CRENEL_BEAN_SPROUT entity is left in Entrance (a grown sprout
           lays its vine and deletes itself), and the three tiles above the
           Entrance bean at x=17 are climbable (act tile 0x53), not wall.
  UP       a player below the vine who holds UP rises out of Entrance into
           Center.
  DOWN     a player on Center's vine who holds DOWN comes through the seam
           and down the Entrance vine onto open floor, never inside a wall.

    python3 tools/quickstart/crenel_vine_probe.py [--rom tmc-d3.gba]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, press, r16, coll_at, act_at, entities, here, poison_here, KIND_OBJECT, PLAYER, ROOM_CONTROLS
import parse_tables as P
ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else 'tmc-d3.gba'
res = []
def check(name, ok, detail=''):
    res.append(ok); print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)
objs = P._enum(open(os.path.join(P.ROOT, 'include/object.h')).read())
SPROUT = objs['CRENEL_BEAN_SPROUT']
MC = P.AREAS['AREA_MT_CRENEL']; ENT = P.ROOMS['ROOM_MT_CRENEL_ENTRANCE']; CEN = P.ROOMS['ROOM_MT_CRENEL_CENTER']
def local(c):
    return (r16(c, PLAYER + 0x2e) - r16(c, ROOM_CONTROLS + 6), r16(c, PLAYER + 0x32) - r16(c, ROOM_CONTROLS + 8))
MSG = 0x02000050   # gMessage: state at +0 (4 typing, 7 waiting for A, 0 closed)
def dismiss(c, limit=900):
    """Close every textbox in turn (the region's arrival stacks Ezlo's
    hints); press only while a box is up, stop after 30 quiet frames."""
    quiet = 0
    for _ in range(limit):
        if c.memory.u8[MSG] == 0 and c.memory.u8[PLAYER + 0x0c] not in (0x16, 0x7):
            c.run_frame(); quiet += 1
            if quiet >= 30:
                return
            continue
        press(c, c.KEY_A, 3, 17); quiet = 0
c = boot(ROM)
poison_here(c); warp(c, MC, ENT, 280, 56, frames=300); dismiss(c)
sprouts = [e for e in entities(c, KIND_OBJECT) if e[2] == SPROUT]
# The sprout at tile (17,2) lays the vine's base there (walkable, the
# plant's foot) and two climb tiles above it, act 0x53, up to the seam.
vine = [(coll_at(c, 17, ty), act_at(c, 17, ty)) for ty in (0, 1)]
foot = coll_at(c, 17, 2)
check('GROWN: no sprout left, the vine tiles climb', here(c) == (MC, ENT) and not sprouts and all(a == 0x53 for _, a in vine) and foot == 0,
      'sprouts %d, climb tiles (coll, act) %s, foot coll %d' % (len(sprouts), vine, foot))
for i in range(120):
    press(c, c.KEY_UP, 4, 0)
    if here(c) != (MC, ENT):
        break
check('UP: the base climbs into Center', here(c) == (MC, CEN), 'room %s player %s after %d presses' % (here(c), local(c), i + 1))
c = boot(ROM)
poison_here(c); warp(c, MC, CEN, 280, 340, frames=300); dismiss(c)
seam = None
for i in range(120):
    press(c, c.KEY_DOWN, 4, 0)
    if here(c) == (MC, ENT):
        seam = i
        break
# Arriving in Entrance raises Ezlo's region line a few frames later; a
# player reads it and climbs on. Take it, then keep going down.
for _ in range(20):
    press(c, c.KEY_DOWN, 4, 0)
dismiss(c)
for _ in range(80):
    press(c, c.KEY_DOWN, 4, 0)
px, py = local(c)
solid = coll_at(c, px >> 4, py >> 4)
check('DOWN: through the seam and onto Entrance floor', here(c) == (MC, ENT) and solid not in (0x0f, 0x17) and py > 56,
      'room %s player %s, tile coll %d, seam at press %s' % (here(c), (px, py), solid, seam))
print('RESULT', 'PASS' if all(res) else 'FAIL', '%d/%d' % (sum(res), len(res)))
sys.exit(0 if all(res) else 1)
