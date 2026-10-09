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
print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
sys.exit(0 if all(res) else 1)
