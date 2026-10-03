"""The carry quest, end to end, on the real spawn path.

Boots a QUEST/CARRY scenario hosted in Castle Garden (whose only neighbour is
North Hyrule Field, so the parcel's region is known), accepts through the
script's own hook, walks to the parcel, lifts it with a real R press, drops
it by force (what a hit does), lifts again, carries it over NHF's south
border into South Hyrule Field, then warps - another seam - to the giver and
is paid.

    python3 tools/quickstart/carry_probe.py [--rom tmc-d3.gba]

PASS: all nine steps. Measured facts this encodes: borders fire while
carrying; the hold is rebuilt on the far side of a seam within ~100 frames;
a forced drop lands within a tile of the player; the reward lands at the
feet and is picked up on the spot; a finished carry counts as the run's side
quest.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import here, entities, warp, snap, KIND_OBJECT, KIND_NPC, SAVE_FLAGS, ROOM_CONTROLS, PLAYER, r16, w16, GROUND_ITEM_ID
import scenario as S, callrom as C
SAVE = 0x02002a40; FLAG_BANK_11 = 0x9C0; PSTATE = 0x03003f80
OUT = os.environ.get('CARRY_PROBE_OUT', '/tmp')
def bank11(c, bit):
    b = FLAG_BANK_11 + bit; return (c.memory.u8[SAVE_FLAGS + (b >> 3)] >> (b & 7)) & 1
def bits(c, base, n): return sum(bank11(c, base + i) << i for i in range(n))
def run(c, n):
    for _ in range(n): c.run_frame()
def hold(c, key, n):
    c.set_keys(key); run(c, n); c.clear_keys(key)
def held(c): return c.memory.u8[PSTATE + 5]
def pxy(c): return r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32)
def place(c, x, y):
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    w16(c, PLAYER + 0x2e, ox + x); w16(c, PLAYER + 0x32, oy + y)
def local(c, wx, wy): return wx - r16(c, ROOM_CONTROLS + 6), wy - r16(c, ROOM_CONTROLS + 8)
def parcels(c, want): return [e for e in entities(c, KIND_OBJECT) if e[2] == 2 and e[3] == want]
def dismiss(c, n=6):
    for _ in range(n): hold(c, c.KEY_A, 3); run(c, 20)
def lift(c, want):
    ps = parcels(c, want)
    if not ps: return False
    lx, ly = local(c, ps[0][4], ps[0][5])
    place(c, lx, ly + 24); run(c, 20)
    hold(c, c.KEY_UP, 16); run(c, 5); hold(c, c.KEY_R, 6); run(c, 40)
    return held(c) == 4
res = []
def check(name, ok, detail=''):
    res.append(ok); print('%s %-40s %s' % ('PASS' if ok else 'FAIL', name, detail))

rows = S.pool()
ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else 'tmc-d3.gba'
c = S.boot(ROM, S.KINDS['QUEST'], 4, 0, kit=1, frames=600)
want = c.memory.u8[SAVE + 0x3f]
giver = [e for e in entities(c, KIND_NPC) if e[2] == 0x28][0]
gx, gy = local(c, giver[4], giver[5])
C.call_keep(c, C.map_sym('QuickStartCarryBegin'), (0, 0)); run(c, 120); dismiss(c)
check('accept -> RUNNING, parcel row = NHF', bits(c, 167, 2) == 2 and bits(c, 169, 5) == 3, 'state %d row %d' % (bits(c,167,2), bits(c,169,5)))
home = rows[3]
warp(c, home['area'], home['room'], home['entrance'][0], home['entrance'][1], frames=400); dismiss(c, 8)
check('parcel at home', bool(parcels(c, want)), str(parcels(c, want)))
check('lift', lift(c, want), 'held %d' % held(c))
# Forced drop: what a hit does to the carry system.
C.call_keep(c, C.map_sym('ResetActiveItems'), ()); run(c, 10)
ps = parcels(c, want)
d = (abs(ps[0][4] - pxy(c)[0]) + abs(ps[0][5] - pxy(c)[1])) if ps else 999
check('forced drop lands at the feet', bool(ps) and d <= 24, 'held %d parcel %s player %s dist %d' % (held(c), ps, pxy(c), d))
check('lift again', lift(c, want), 'held %d' % held(c))
# Seam: NHF's south border into SHF, parcel overhead.
place(c, 504, 760); run(c, 10)
hold(c, c.KEY_DOWN, 120)
r1 = (here(c), held(c), c.memory.u8[SAVE+0x3e])
run(c, 150)
check('border fires while carrying', here(c) != (home['area'], home['room']), 'here %s (at exit: %s)' % (here(c), r1))
check('parcel rebuilt and held across the seam', held(c) == 4 and bool(parcels(c, want)) and c.memory.u8[SAVE+0x3e] == 0,
      'held %d parcels %s carry_item %d' % (held(c), parcels(c, want), c.memory.u8[SAVE+0x3e]))
snap(c, OUT + '/carry_across.png')
# (The walk back north was traced separately: the hold survives the seam
# both ways, and NHF's wave then lands a hit that drops the parcel at the
# feet - the designed behaviour, but not a deterministic probe step.)
# Deliver: warp into Castle Garden carrying it, landing beside the giver. The
# warp is a seam (stash + rebuild); the hold takes ~100 frames in, and the
# proximity test pays out on that frame. Landing AT the giver rather than at
# the drop spot keeps the probe out of the region's wave (traced: standing at
# the drop spot for 400 frames collects hits, and a knockback drops the parcel).
cg = rows[0]
warp(c, cg['area'], cg['room'], gx, gy + 16, frames=250)
items = [e for e in entities(c, KIND_OBJECT) if e[2] == GROUND_ITEM_ID]
# The reward lands at the feet, and the feet are where the player stands:
# measured, it is picked up on the spot ("You got Din's Charm!"), so a
# ground item OR the item-get state OR its textbox all mean "paid".
paid = bool(items) or c.memory.u8[PLAYER + 0x0c] == 8 or (c.memory.u8[0x02000050] & 0x7f) != 0
check('delivery: WON, parcel gone, reward paid', bits(c, 167, 2) == 3 and not parcels(c, want) and held(c) == 0 and paid,
      'state %d held %d parcels %s items %s pact %d msg %x' % (bits(c,167,2), held(c), parcels(c, want), items, c.memory.u8[PLAYER+0x0c], c.memory.u8[0x02000050] & 0x7f))
snap(c, OUT + '/carry_delivered.png')
sq = C.call_keep(c, C.game_sym('QuickStartSideQuestDone'), ())
check('counts as the side quest', sq == 1, 'SideQuestDone %d' % sq)
print('RESULT', 'PASS' if all(res) else 'FAIL', '%d/%d' % (sum(res), len(res)))
sys.exit(0 if all(res) else 1)
