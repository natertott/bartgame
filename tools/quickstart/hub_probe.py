"""Hub travel (Oct 2026, the redesign's P2 section 8): two warp pads.

  PADS     the selection hall (Floor 3) holds a warp pad, and so does the
           shop hall (Floor 1).
  LOCKED   while the item selection is still running, standing on the
           Floor 3 pad does nothing (the draft cannot be skipped).
  SHOP     once the selection is over, the Floor 3 pad takes the player
           straight to the shop hall on Floor 1 - one transition where the
           stairs take two.
  OUT      the shop's pad takes the player straight out to the tower door
           in Cloud Tops, above the hole - one transition where the stairs
           take two more. Selection to the door: two, not four.
  SNAP     a screenshot of each pad.
  SHELF    with things found (the catalog ledger, gSave.figurines, forged
           full) and the draft over, the selection floor's lower hall shows
           nine of them as display-only ground sprites; standing on one
           takes nothing. Ids with no ground sprite (charms on unused item ids)
           are left off. A screenshot of the shelf.

    python3 tools/quickstart/hub_probe.py [--rom tmc-d3.gba] [--out DIR]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import entities, here, snap, r16, w16, press, KIND_OBJECT, PLAYER, ROOM_CONTROLS, GENT, STRIDE
import scenario as S
import parse_tables as P
ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else 'tmc-d3.gba'
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else '/tmp'
SAVE = 0x02002a40
FLAGS = SAVE + 0x25C
BANK11 = 0x9C0
MSG = 0x02000050
FIGURINES = 0xD0   # gSave.figurines (save.h)
WARP = P._enum(open(os.path.join(P.ROOT, 'include/object.h')).read())['WARP_POINT']
TOWER = P.AREAS['AREA_WIND_TRIBE_TOWER']
F1, F3 = P.ROOMS['ROOM_WIND_TRIBE_TOWER_FLOOR_1'], P.ROOMS['ROOM_WIND_TRIBE_TOWER_FLOOR_3']
CLOUD = (P.AREAS['AREA_CLOUD_TOPS'], P.ROOMS['ROOM_CLOUD_TOPS_CLOUD_TOPS'])
res = []
def check(name, ok, detail=''):
    res.append(bool(ok)); print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)
def run(c, n):
    for _ in range(n):
        c.run_frame()
def dismiss(c, limit=600):
    quiet = 0
    for _ in range(limit):
        if c.memory.u8[MSG] == 0:
            c.run_frame(); quiet += 1
            if quiet >= 30:
                return
            continue
        press(c, c.KEY_A, 3, 17); quiet = 0
def local(c):
    return r16(c, PLAYER + 0x2e) - r16(c, ROOM_CONTROLS + 6), r16(c, PLAYER + 0x32) - r16(c, ROOM_CONTROLS + 8)
def pads(c):
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    return [(e[0], e[4] - ox, e[5] - oy, c.memory.u8[GENT + e[0] * STRIDE + 0x0c]) for e in entities(c, KIND_OBJECT, WARP)
            if c.memory.u8[GENT + e[0] * STRIDE + 0x70] == 0]   # not the glow child
def set_phase(c, v):
    for b in range(4):
        bit = BANK11 + 85 + b
        if v & (1 << b):
            c.memory.u8[FLAGS + (bit >> 3)] |= 1 << (bit & 7)
        else:
            c.memory.u8[FLAGS + (bit >> 3)] &= ~(1 << (bit & 7)) & 0xFF
def stand_on(c, pad, frames):
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    start = here(c)
    for f in range(frames):
        if here(c) != start:
            run(c, 60); return f
        if f < 100:   # hold the player on the pad until the spin takes over
            w16(c, PLAYER + 0x2e, ox + pad[1]); w16(c, PLAYER + 0x32, oy + pad[2])
        c.run_frame()
    return None

c = S.boot(ROM, 0, seed=3, frames=300)
dismiss(c); run(c, 60)
p3 = pads(c)
check('PADS: a pad in the selection hall', here(c) == (TOWER, F3) and len(p3) == 1, 'room %s pads %s' % (here(c), p3))
snap(c, os.path.join(OUT, 'hub_pad_f3.png'))
if p3:
    moved = stand_on(c, p3[0], 300)
    check('LOCKED: asleep while the selection runs', moved is None and here(c) == (TOWER, F3), 'moved after %s, room %s' % (moved, here(c)))
    set_phase(c, 10); run(c, 120)
    moved = stand_on(c, pads(c)[0], 600)
    check('SHOP: the selection hall pad goes to the shop', here(c) == (TOWER, F1), 'after %s frames, room %s at %s' % (moved, here(c), local(c)))
    dismiss(c); run(c, 120)
    p1 = pads(c)
    check('PADS: a pad in the shop hall', len(p1) == 1, 'pads %s' % p1)
    snap(c, os.path.join(OUT, 'hub_pad_f1.png'))
    if p1:
        moved = stand_on(c, p1[0], 600)
        check('OUT: the shop pad goes out to the tower door', here(c) == CLOUD and abs(local(c)[0] - 488) <= 16,
              'after %s frames, room %s at %s' % (moved, here(c), local(c)))
# ---- SHELF
from emu import warp
c = S.boot(ROM, 0, seed=4, frames=300)
dismiss(c)
FIG = SAVE + FIGURINES
for i in range(36):
    c.memory.u8[FIG + i] = 0xFF
set_phase(c, 10)
c.memory.u8[SAVE + 0x3C] = 0x51   # probe warps are free
warp(c, TOWER, P.ROOMS['ROOM_WIND_TRIBE_TOWER_FLOOR_2'], 120, 264, frames=200); dismiss(c)
warp(c, TOWER, F3, 120, 248, frames=200); dismiss(c); run(c, 60)
ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
shelf = [e for e in entities(c, KIND_OBJECT, 0) if c.memory.u8[GENT + e[0] * STRIDE + 11] == 0x60]
off = all((c.memory.u8[GENT + e[0] * STRIDE + 0x10] & 0x80) == 0 for e in shelf)   # ENT_COLLIDE
check('SHELF: found things on show, all drawn, collision off', 5 <= len(shelf) <= 9 and off and all(r16(c, GENT + e[0] * STRIDE + 0x12) != 0 for e in shelf) and all(e[5] - oy == 264 for e in shelf),
      'room %s shelf %d items %s' % (here(c), len(shelf), sorted(e[3] for e in shelf)))
snap(c, os.path.join(OUT, 'hub_shelf.png'))
if shelf:
    inv0 = bytes(c.memory.u8[SAVE + 0xF2 + i] for i in range(34))
    w16(c, PLAYER + 0x2e, shelf[0][4]); w16(c, PLAYER + 0x32, shelf[0][5]); run(c, 90); dismiss(c)
    left = [e for e in entities(c, KIND_OBJECT, 0) if c.memory.u8[GENT + e[0] * STRIDE + 11] == 0x60]
    inv1 = bytes(c.memory.u8[SAVE + 0xF2 + i] for i in range(34))
    check('SHELF: standing on one takes nothing', len(left) == len(shelf) and inv0 == inv1,
          'shelf %d -> %d, inventory changed %s' % (len(shelf), len(left), inv0 != inv1))
print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
sys.exit(0 if all(res) else 1)
