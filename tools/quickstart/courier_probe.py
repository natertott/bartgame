"""The courier (Oct 2026, the redesign's P2 section 6.2), end to end by talking.

Boots a QUEST/COURIER scenario hosted in Castle Garden (row 0, whose only
neighbour is North Hyrule Field, so the receiver's region is known), and:

  GIVER     a giver stands in Castle Garden running the courier giver
            script; nobody runs the receiver's yet.
  OFFER     talking to it (R, the interact button, from a tile below) takes
            the parcel: state CARRYING, the receiver's row is NHF (row 3).
  HURRY     talking again changes nothing (the "please hurry" line).
  RECEIVER  in North Hyrule Field a receiver now stands running the
            receiver script.
  DELIVER   talking to it delivers: state DELIVERED, a RARE prize at the
            feet (taken on the spot, or lying there), and the run's side
            quest reads done (the chain's QUEST step and carrier).
  AGAIN     a second talk to the receiver pays nothing more.

The NPC behind a script is found by the script it runs: each NPC's
ScriptExecutionContext is reached from a pointer in the entity, and its
instruction pointer lies inside the courier script's range in the map.

    python3 tools/quickstart/courier_probe.py [--rom tmc-d3.gba]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import here, entities, warp, press, KIND_NPC, KIND_OBJECT, SAVE_FLAGS, FLAG_BANK_12, ROOM_CONTROLS, PLAYER, GENT, STRIDE, r16, w16
import scenario as S, callrom as C
ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else 'tmc-d3.gba'
SAVE = 0x02002a40
MSG = 0x02000050
res = []
def check(name, ok, detail=''):
    res.append(bool(ok)); print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)
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
def b12(c, bit):
    b = FLAG_BANK_12 + bit
    return (c.memory.u8[SAVE_FLAGS + (b >> 3)] >> (b & 7)) & 1
def bits(c, base, n):
    return sum(b12(c, base + i) << i for i in range(n))
state = lambda c: bits(c, 135, 2)
dest = lambda c: bits(c, 130, 5)

GIVER = C.map_sym('script_QuickStartCourierGiver')
RECV = C.map_sym('script_QuickStartCourierReceiver')
def u32(c, a):
    return c.memory.u8[a] | c.memory.u8[a + 1] << 8 | c.memory.u8[a + 2] << 16 | c.memory.u8[a + 3] << 24
def script_of(c, idx):
    base = GENT + idx * STRIDE
    for off in range(0, STRIDE, 4):
        p = u32(c, base + off)
        if 0x02000000 <= p < 0x02040000 or 0x03000000 <= p < 0x03008000:
            ip = u32(c, p)
            if GIVER <= ip < RECV:
                return 'giver'
            if RECV <= ip < RECV + 0x60:
                return 'receiver'
    return None
def npc_running(c, which):
    return [e for e in entities(c, KIND_NPC) if script_of(c, e[0]) == which]
def kit(c):
    """What a prize can change: the inventory bits, and the stats bytes
    that are not health (pinned by run()) or a ticking clock - wallet,
    heart pieces, bombs, arrows, bags, charm, bottles, rupees."""
    st = SAVE + 0xA8
    keep = [0, 1] + list(range(4, 0x12)) + [0x18, 0x19]
    return bytes(c.memory.u8[st + i] for i in keep) + bytes(c.memory.u8[SAVE + 0xF2 + i] for i in range(34))

def talk(c, e):
    for _ in range(120):   # out of an arrival state, or the write is undone
        run(c, 1)
    w16(c, PLAYER + 0x2e, e[4]); w16(c, PLAYER + 0x32, e[5] + 14); run(c, 10)
    press(c, c.KEY_UP, 4, 2)
    press(c, c.KEY_R, 4, 8); dismiss(c)

c = S.boot(ROM, S.KINDS['QUEST'], S.QUESTS.index('COURIER'), 0, kit=1, frames=600)
dismiss(c)
g = npc_running(c, 'giver')
check('GIVER: a giver in Castle Garden, no receiver yet', here(c) == (7, 0) and len(g) == 1 and not npc_running(c, 'receiver'),
      'room %s givers %d receivers %d state %d' % (here(c), len(g), len(npc_running(c, 'receiver')), state(c)))
if g:
    talk(c, g[0])
    run(c, 60); dismiss(c)
    check('OFFER: the parcel taken, the receiver in NHF', state(c) in (1, 2) and dest(c) == 3, 'state %d dest row %d' % (state(c), dest(c)))
    s0 = state(c)
    g = npc_running(c, 'giver')
    if g:
        talk(c, g[0])
    check('HURRY: a second talk changes nothing', state(c) == 2 and dest(c) == 3, 'state %d' % state(c))
rows = S.pool()
nhf = rows[3]
warp(c, nhf['area'], nhf['room'], nhf['entrance'][0], nhf['entrance'][1], frames=400); dismiss(c)
r = npc_running(c, 'receiver')
check('RECEIVER: a receiver stands in North Hyrule Field', here(c) == (nhf['area'], nhf['room']) and len(r) == 1,
      'room %s receivers %d' % (here(c), len(r)))
if r:
    items0 = len(entities(c, KIND_OBJECT, 0))
    snap0 = kit(c)
    talk(c, r[0])
    run(c, 60); dismiss(c)
    # the prize reached the player: a new ground item, or the stats/inventory
    # changed (taken on the spot - it lands at the feet)
    snap1 = kit(c)
    paid = len(entities(c, KIND_OBJECT, 0)) > items0 or snap1 != snap0
    done = C.call_keep(c, C.game_sym('QuickStartSideQuestDone'), ()) if True else 0
    check('DELIVER: delivered, paid, the side quest done', state(c) == 3 and done == 1 and paid,
          'state %d side quest %d paid %s ground items %d -> %d' % (state(c), done, paid, items0, len(entities(c, KIND_OBJECT, 0))))
    st = state(c); n0 = len(entities(c, KIND_OBJECT, 0))
    r = npc_running(c, 'receiver')
    if r:
        talk(c, r[0])
    check('AGAIN: a second talk pays nothing more', state(c) == st and len(entities(c, KIND_OBJECT, 0)) <= n0,
          'state %d items %d -> %d' % (state(c), n0, len(entities(c, KIND_OBJECT, 0))))
print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
sys.exit(0 if all(res) else 1)
