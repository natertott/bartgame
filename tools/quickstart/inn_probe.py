"""The inn's blessing table (Oct 2026, the redesign's P2 section 8).

  TABLE    the first visit of a run lays three pastries in a row on the inn
           floor - a brioche, a croissant and a cake - exactly one GOLD.
  SNAP     a screenshot of the table (the eye check: on open floor, the
           gold one gold).
  CHOOSE   taking one pays its blessing (the food mask grows) and clears
           the other two off the table.
  ONCE     leaving and coming back the same run: no table.
  RUN      a new run lays it again (the latch is in the run-start wipe).
  KEYS     (P3) the dungeon key bag is empty at a run's start.

    python3 tools/quickstart/inn_probe.py [--rom tmc-d3.gba] [--out DIR]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import entities, r16, w16, warp, here, snap, press, KIND_OBJECT, PLAYER, ROOM_CONTROLS, SAVE_FLAGS, FLAG_BANK_12
import scenario as S
import parse_tables as P
import callrom as C
ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else 'tmc-d3.gba'
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else '/tmp'
SAVE = 0x02002a40
MSG = 0x02000050
I = P.ITEMS
PASTRIES = {I['ITEM_BRIOCHE']: 'brioche', I['ITEM_CROISSANT']: 'croissant', I['ITEM_CAKE']: 'cake'}
INN = (P.AREAS['AREA_WIND_TRIBE_TOWER'], P.ROOMS['ROOM_WIND_TRIBE_TOWER_FLOOR_2'])
TABLE_Y = 280   # QUICKSTART_INN_TABLE_Y
res = []
def check(name, ok, detail=''):
    res.append(bool(ok)); print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)

def dismiss(c, limit=600):
    quiet = 0
    for _ in range(limit):
        if c.memory.u8[MSG] == 0:
            c.run_frame(); quiet += 1
            if quiet >= 30:
                return
            continue
        press(c, c.KEY_A, 3, 17); quiet = 0

def taken(c):
    b = FLAG_BANK_12 + 118
    return (c.memory.u8[SAVE_FLAGS + (b >> 3)] >> (b & 7)) & 1

def table(c):
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    out = []
    for e in entities(c, KIND_OBJECT, 0):
        if e[3] in PASTRIES and e[5] - oy == TABLE_Y:
            tier = c.memory.u8[0x030015a0 + e[0] * 0x88 + 11]
            out.append((PASTRIES[e[3]], tier, e[4], e[5]))
    return sorted(out, key=lambda t: t[2])

def to_inn(c):
    warp(c, INN[0], INN[1], 120, 264, frames=240); dismiss(c)

mask = lambda c: C.call_keep(c, C.map_sym('QuickStartFoodMask'), ())

c = S.boot(ROM, 0, seed=7, frames=300)
c.memory.u8[SAVE + 0x3C] = 0x51   # probe warps are free (QuickStartProbeWarpsFree)
keys = [c.memory.u8[SAVE + 0x45C + i] for i in range(16)]
check('KEYS: the dungeon key bag is empty at the start', not any(keys), str(keys))
to_inn(c)
t = table(c)
check('TABLE: three pastries on the floor, one gold', here(c) == INN and len(t) == 3 and
      sorted(x[0] for x in t) == ['brioche', 'cake', 'croissant'] and sum(1 for x in t if x[1] == 2) == 1,
      'room %s table %s' % (here(c), [(x[0], x[1]) for x in t]))
path = os.path.join(OUT, 'inn_table.png'); snap(c, path)
check('SNAP: the table, saved', os.path.exists(path), path)
if len(t) == 3:
    gold = [x for x in t if x[1] == 2][0]
    m0 = mask(c)
    for _ in range(120):   # out of the arrival state, or the write is undone
        c.run_frame()
    w16(c, PLAYER + 0x2e, gold[2]); w16(c, PLAYER + 0x32, gold[3])
    for _ in range(6):
        for _ in range(30):
            c.run_frame()
        dismiss(c)
    m1 = mask(c)
    check('CHOOSE: the gold one pays, the others go', m1 != m0 and table(c) == [] and taken(c) == 1,
          '%s: mask %#x -> %#x, left %s, latch %d' % (gold[0], m0, m1, table(c), taken(c)))
    warp(c, 48, 0, 120, 264, frames=200); dismiss(c)
    to_inn(c)
    check('ONCE: no second table this run', table(c) == [], 'table %s' % table(c))
c = S.boot(ROM, 0, seed=8, frames=300)
c.memory.u8[SAVE + 0x3C] = 0x51
to_inn(c)
check('RUN: a new run lays it again', len(table(c)) == 3, 'table %s' % [(x[0], x[1]) for x in table(c)])
print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
sys.exit(0 if all(res) else 1)
