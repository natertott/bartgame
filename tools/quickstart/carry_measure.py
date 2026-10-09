"""Measurements for the single-room carry quest (docs/QUICKSTART_CARRY_SINGLE_ROOM.md).

Before the parcel pot is built, what does a VANILLA pot do, and what do the
candidate rooms look like?

  ROOMS   per candidate room: its size in tiles, how many tiles are open
          (collision 0), and how many of those carry a hazard act tile (pit
          0x0D, deep water 0x10/0x11, swamp 0x13, lava 0x5A) - the tiles a
          collision-only flood would wrongly count as walkable with a pot.
  LIFT    a pot spawned beside Link is lifted by R (heldObject set).
  WALK    held, Link walks; the pot rides along.
  THROW   R again throws it; where it lands, and that a plain pot breaks.
  HIT     a hit while holding: what happens to the pot.

    python3 tools/quickstart/carry_measure.py [--rom tmc-d3.gba]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import (entities, here, warp, press, r16, w16, room_dims, coll_at, act_at, snap,
                 KIND_OBJECT, PLAYER, ROOM_CONTROLS, GENT, STRIDE)
import scenario as S
import parse_tables as P
import callrom as C

args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else 'tmc-d3.gba'
OUT = args[args.index('--out') + 1] if '--out' in args else '/tmp'
SAVE = 0x02002a40
MSG = 0x02000050
PSTATE = 0x03003f80
HELD = PSTATE + 5
OBJ = P._enum(open(os.path.join(P.ROOT, 'include/object.h')).read())
POT = OBJ['POT']
HAZ = {0x0D: 'pit', 0x10: 'water', 0x11: 'water', 0x13: 'swamp', 0x5A: 'lava'}
ROOMS = [
    ('NHF', 'AREA_HYRULE_FIELD', 'ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD', 960, 638),
    ('MW', 'AREA_MINISH_WOODS', 'ROOM_MINISH_WOODS_MAIN', 8, 424),
    ('VF', 'AREA_VEIL_FALLS', 'ROOM_VEIL_FALLS_MAIN', 296, 500),
    ('CREN', 'AREA_MT_CRENEL', 'ROOM_MT_CRENEL_CAVERN_OF_FLAMES_ENTRANCE', 101, 271),
    ('CREN-BASE', 'AREA_MT_CRENEL', 'ROOM_MT_CRENEL_ENTRANCE', 994, 416),
    ('CW', 'AREA_CASTOR_WILDS', 'ROOM_CASTOR_WILDS_MAIN', 1000, 333),
]


def run(c, n):
    for _ in range(n):
        c.memory.u8[PLAYER + 0x45] = 24
        c.run_frame()


def dismiss(c, limit=600):
    quiet = 0
    for _ in range(limit):
        if c.memory.u8[MSG] == 0:
            run(c, 1); quiet += 1
            if quiet >= 30:
                return
            continue
        press(c, c.KEY_A, 3, 17); quiet = 0


def survey_room(c):
    w, h = room_dims(c)
    tw, th = min(w // 16, 64), min(h // 16, 64)
    opn = haz = 0
    kinds = {}
    for ty in range(th):
        for tx in range(tw):
            if coll_at(c, tx, ty) == 0:
                opn += 1
                a = act_at(c, tx, ty)
                if a in HAZ:
                    haz += 1
                    kinds[HAZ[a]] = kinds.get(HAZ[a], 0) + 1
    return w // 16, h // 16, opn, haz, kinds


def spawn_pot(c, lx, ly):
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    ptr = C.call_keep(c, C.map_sym('CreateObject'), (POT, 0xFF, 0))
    if not ptr:
        return None
    # on a tile centre, like every placed pot: its solid tile and its lift
    # hitbox only line up there
    w16(c, ptr + 0x2e, ox + (lx & ~15) + 8); w16(c, ptr + 0x32, oy + (ly & ~15) + 8)
    run(c, 2)
    return (ptr - GENT) // STRIDE


def pot_state(c, idx):
    b = GENT + idx * STRIDE
    if c.memory.u8[b + 8] != 6 or c.memory.u8[b + 9] != POT:
        return None
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    return dict(action=c.memory.u8[b + 0xc], sub=c.memory.u8[b + 0xd], x=r16(c, b + 0x2e) - ox, y=r16(c, b + 0x32) - oy)


c = S.boot(ROM, 0, seed=6, frames=300)
c.memory.u8[SAVE + 0x3C] = 0x51   # probe warps are free
dismiss(c)
print('ROOMS')
for name, an, rn, x, y in ROOMS:
    warp(c, P.AREAS[an], P.ROOMS[rn], x, y, frames=300); dismiss(c)
    tw, th, opn, haz, kinds = survey_room(c)
    print('  %-10s room %s  %dx%d tiles  open %d  hazard-on-open %d %s' % (name, here(c), tw, th, opn, haz, kinds))

# LIFT / WALK / THROW in North Hyrule Field. Position writes to Link do not
# stick for a while after a warp (an arrival state), so he WALKS into a pot
# spawned in his path: the same approach a player makes.
def lift_from(c, lx, ly, key, gap=24):
    """Spawn a pot `gap` px from Link toward `key`, walk into it, press R."""
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    px, py = r16(c, PLAYER + 0x2e) - ox, r16(c, PLAYER + 0x32) - oy
    dx, dy = {c.KEY_LEFT: (-gap, 0), c.KEY_RIGHT: (gap, 0), c.KEY_UP: (0, -gap), c.KEY_DOWN: (0, gap)}[key]
    idx = spawn_pot(c, px + dx, py + dy)
    run(c, 6)
    print('  spawned at', (px + dx, py + dy), '->', pot_state(c, idx), 'player', (r16(c, PLAYER + 0x2e) - ox, r16(c, PLAYER + 0x32) - oy))
    # walk until he stops moving (blocked by the pot's tile); pressing on
    # into it shoves it a tile (measured: 16 px), as a player would see
    c.set_keys(key)
    last, still = None, 0
    for _ in range(60):
        run(c, 1)
        here_ = (r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32))
        still = still + 1 if here_ == last else 0
        last = here_
        if still >= 2:
            break
    c.clear_keys(key); run(c, 2)
    near = (r16(c, PLAYER + 0x2e) - ox, r16(c, PLAYER + 0x32) - oy)
    press(c, c.KEY_R, 3, 30)
    print('  lift_from: player %s -> %s, pot %s, held %d' % ((px, py), near, pot_state(c, idx), c.memory.u8[HELD]))
    return idx

def open_strip(c, near, length=7):
    """A tile whose row runs `length` open tiles to its left, with open rows
    above and below - room to walk into a pot and on with it."""
    w, h = room_dims(c)
    best = None
    for ty in range(2, min(h // 16, 64) - 2):
        for tx in range(length, min(w // 16, 64) - 1):
            if all(coll_at(c, tx - k, ty + d) == 0 and act_at(c, tx - k, ty + d) not in HAZ
                   for k in range(length + 1) for d in (-1, 0, 1)):
                dist = abs(tx * 16 + 8 - near[0]) + abs(ty * 16 + 8 - near[1])
                if best is None or dist < best[0]:
                    best = (dist, tx * 16 + 8, ty * 16 + 8)
    return best[1:] if best else None

name, an, rn, x, y = ROOMS[0]
warp(c, P.AREAS[an], P.ROOMS[rn], x, y, frames=300); dismiss(c)
sx, sy = open_strip(c, (x, y))
warp(c, P.AREAS[an], P.ROOMS[rn], sx, sy, frames=300); dismiss(c); run(c, 60)
ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
idx = lift_from(c, 0, 0, c.KEY_LEFT)
print('LIFT  held %d, pot %s' % (c.memory.u8[HELD], pot_state(c, idx)))
snap(c, os.path.join(OUT, 'carry_lift.png'))
c.set_keys(c.KEY_UP); run(c, 40); c.clear_keys(c.KEY_UP); run(c, 4)
print('WALK  player at', (r16(c, PLAYER + 0x2e) - ox, r16(c, PLAYER + 0x32) - oy), 'held', c.memory.u8[HELD], 'pot', pot_state(c, idx))
press(c, c.KEY_R, 3, 1)
seen = []
for f in range(90):
    run(c, 1)
    s = pot_state(c, idx)
    seen.append(None if s is None else (s['action'], s['sub']))
    if s is None:
        break
print('THROW held %d, pot (action, sub) over the flight: %s' % (c.memory.u8[HELD], [k for i, k in enumerate(seen) if i == 0 or seen[i - 1] != k]))

# HIT: carrying, a chuchu dropped on Link. What does the pot go through?
import re
ENEMY = {m.group(2): int(m.group(1), 16) for m in re.finditer(r'/\*0x([0-9a-f]+)\*/ (\w+),', open(os.path.join(P.ROOT, 'include/enemy.h')).read())}
warp(c, P.AREAS[an], P.ROOMS[rn], sx, sy, frames=300); dismiss(c); run(c, 60)
ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
idx = lift_from(c, 0, 0, c.KEY_LEFT)
lx_, ly_ = r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32)
e = C.call_keep(c, C.map_sym('CreateEnemy'), (ENEMY['CHUCHU'], 0))
if e:
    w16(c, e + 0x2e, lx_ + 16); w16(c, e + 0x32, ly_)
    c.memory.u8[e + 0x38] = c.memory.u8[PLAYER + 0x38]   # Link's collision layer
run(c, 2)
print('  enemy', hex(e), [(x[2], x[4] - ox, x[5] - oy) for x in entities(c, 3)])
seen = []
h0 = c.memory.u8[PLAYER + 0x45]
for f in range(240):
    c.run_frame()   # health NOT pinned: the hit has to land
    s = pot_state(c, idx)
    seen.append(None if s is None else (s['action'], s['sub']))
    if s is None or (seen[-1] != (2, 1) and f > 10 and seen[-1] == (1, 0)):
        break
print('HIT   life %d -> %d, held %d, pot (action, sub): %s, last %s' % (h0, c.memory.u8[PLAYER + 0x45], c.memory.u8[HELD],
      [k for i, k in enumerate(seen) if i == 0 or seen[i - 1] != k], pot_state(c, idx)))
