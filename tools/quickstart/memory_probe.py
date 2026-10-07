"""The two-room blink memory event, on the real spawn path.

Finds this seed's lesson and recital sites (QuickStartMemorySite), lands in
each with the testbed, and measures:

  LESSON   three switches and a sprite; the switches light one at a time in
           a repeating order that matches the seed's sequence; a hit on a
           switch changes nothing; the sprite's Call latches the site DONE
           and the content is still there on a second visit.
  RECITAL  three switches and a sprite; a wrong order spawns enemies and
           resets; the right order (hits forged on the switches - the real
           contact path, see chuchu_contact.py for why forging is only
           trusted here because the switch's own toggle is what it drives)
           drops a prize, and taking it latches the site DONE.

    python3 tools/quickstart/memory_probe.py [--rom tmc-d3.gba]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import here, entities, press, KIND_OBJECT, KIND_NPC, KIND_ENEMY, GENT, ROOM_CONTROLS, PLAYER, r16, w16, SAVE_FLAGS, FLAG_BANK_12
import scenario as S
import callrom as C
import parse_tables as P
ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else 'tmc-d3.gba'
ROOMVARS = 0x02034350
LIGHTABLE = 0  # object id, resolved below
STRIDE = 0x88
res = []
def check(name, ok, detail=''):
    res.append(ok); print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)
def run(c, n):
    for _ in range(n): c.run_frame()
MSG = 0x02000050   # gMessage: state at +0 (4 typing, 7 waiting for A, 0 closed)
def dismiss(c, limit=900):
    """Close every textbox in turn. A fixed count of presses is wrong twice
    over: when the boot lands the player beside the sprite (the barrel
    house, site 99) a press while free TALKS to it, and on a region's first
    arrival Ezlo stacks two or three hints. So: press only while a box is
    up, never while free, and stop after thirty quiet frames."""
    quiet = 0
    for _ in range(limit):
        if c.memory.u8[MSG] == 0 and c.memory.u8[PLAYER + 0x0c] not in (0x16, 0x7):   # free
            c.run_frame()
            quiet += 1
            if quiet >= 30:
                return
            continue
        press(c, c.KEY_A, 3, 17)
        quiet = 0
def room_flag(c, n):
    b = 256 + n
    return (c.memory.u8[ROOMVARS + 0x14 + (b >> 3)] >> (b & 7)) & 1
def switches(c):
    """The three switches ORDERED BY THEIR FLAG INDEX (QS_SWITCH_HIT_FLAG(k) at
    entity +0x86), not by x: the spot finder can nudge a switch past its
    neighbour, so left-to-right is not k."""
    out = []
    for e in entities(c, KIND_OBJECT):
        if e[2] != LIGHTABLE:
            continue
        f = c.memory.u8[GENT + e[0] * STRIDE + 0x86] | (c.memory.u8[GENT + e[0] * STRIDE + 0x87] << 8)
        out.append((f - (0x8000 + 256 + 104), e))
    out.sort()
    return [e for _k, e in out]
def site_done(c, site):
    b = FLAG_BANK_12 + 1 + site
    return (c.memory.u8[SAVE_FLAGS + (b >> 3)] >> (b & 7)) & 1
def forge_hit(c, ent_index):
    c.memory.u8[GENT + ent_index * STRIDE + 0x41] = 0x80 | 4
# object id of LIGHTABLE_SWITCH from the header
objs = P._enum(open(os.path.join(P.ROOT, 'include/object.h')).read())
LIGHTABLE = objs['LIGHTABLE_SWITCH']
sites = P.content_sites()

c = S.boot(ROM, 0)
L = C.call_keep(c, C.game_sym('QuickStartMemorySite'), (0,))
R = C.call_keep(c, C.game_sym('QuickStartMemorySite'), (1,))
seqp = C.call_keep(c, C.game_sym('QuickStartMemorySequence'), ())
seq = [c.memory.u8[seqp + i] for i in range(3)]
print('lesson site', L, sites[L][1], '| recital site', R, sites[R][1], '| sequence', seq)
check('two distinct sites in distinct rooms', L != R and (sites[L][2], sites[L][3]) != (sites[R][2], sites[R][3]))

# ---- the lesson
c = S.boot(ROM, S.KINDS['SITE'], L, 7, 0, frames=500); dismiss(c)
sw = switches(c); npcs = [e for e in entities(c, KIND_NPC) if e[2] == 0x28]
check('lesson: three switches and a sprite', here(c) == (sites[L][2], sites[L][3]) and len(sw) == 3 and len(npcs) >= 1,
      'room %s switches %d npcs %d' % (here(c), len(sw), len(npcs)))
order = []
for f in range(900):
    c.run_frame()
    lit = [k for k in range(3) if room_flag(c, 104 + k)]
    if len(lit) == 1 and (not order or order[-1] != lit[0]):
        order.append(lit[0])
    if f == 300 and sw:
        forge_hit(c, sw[0][0])
# the watch may start mid-cycle (dismiss() presses a variable number of
# times), so judge from the first time the sequence's own first switch lit
start = order.index(seq[0]) if seq[0] in order else len(order)
cycle = order[start:]
check('lesson: switches blink in the seed order', len(cycle) >= 3 and all(cycle[i] == seq[i % 3] for i in range(len(cycle))),
      'seen %s seq %s' % (order[:9], seq))
C.call_keep(c, C.map_sym('QuickStartMemoryLessonTaught'), (0, 0))
check('lesson: the sprite latches DONE', site_done(c, L) == 1)
# leave and come back: the content must still be there
from emu import warp, poison_here
poison_here(c); warp(c, 48, 3, 120, 104, frames=250); dismiss(c)
poison_here(c); warp(c, sites[L][2], sites[L][3], sites[L][4], sites[L][5] + 24, frames=350); dismiss(c)
check('lesson: content stays after DONE', here(c) == (sites[L][2], sites[L][3]) and len(switches(c)) == 3,
      'room %s switches %d' % (here(c), len(switches(c))))

# ---- the recital
c = S.boot(ROM, S.KINDS['SITE'], R, 7, 1 | (5 << 1), kit=1, frames=500); dismiss(c)
sw = switches(c); npcs = [e for e in entities(c, KIND_NPC) if e[2] == 0x28]
check('recital: three switches and a sprite', here(c) == (sites[R][2], sites[R][3]) and len(sw) == 3 and len(npcs) >= 1,
      'room %s switches %d npcs %d' % (here(c), len(sw), len(npcs)))
# one wrong first strike: the switch that is NOT the sequence's first
wrong_first = seq[1]
enemies_before = len(entities(c, KIND_ENEMY))
forge_hit(c, sw[wrong_first][0]); run(c, 30)
lit_after = [k for k in range(3) if room_flag(c, 104 + k)]
enemies_after = len(entities(c, KIND_ENEMY))
check('recital: a wrong order spawns enemies and resets', enemies_after > enemies_before and lit_after == [],
      'enemies %d -> %d lit %s' % (enemies_before, enemies_after, lit_after))
# kill the wave (health 0) so the right answer is measured cleanly
for e in entities(c, KIND_ENEMY):
    c.memory.u8[GENT + e[0] * STRIDE + 0x45] = 0
run(c, 60)
for k in seq:
    forge_hit(c, sw[k][0]); run(c, 20)
run(c, 30)
# the prize lands a tile south of the sprite (the content spot); the dead
# wave's own drops litter the room, so pick the ground item nearest that spot
ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
px, py = ox + sites[R][4], oy + sites[R][5] + 16
items = sorted([e for e in entities(c, KIND_OBJECT) if e[2] == 0], key=lambda e: abs(e[4] - px) + abs(e[5] - py))
prize = [e for e in items if abs(e[4] - px) + abs(e[5] - py) <= 24]
check('recital: the right order drops a prize', bool(prize) or c.memory.u8[PLAYER + 0x0c] == 8, 'prize %s (spot %s)' % (prize[:1], (px, py)))
if prize:
    w16(c, PLAYER + 0x2e, prize[0][4]); w16(c, PLAYER + 0x32, prize[0][5] + 4); run(c, 120); dismiss(c)
run(c, 60)
check('recital: taking it latches DONE', site_done(c, R) == 1, 'done %d' % site_done(c, R))
print('RESULT', 'PASS' if all(res) else 'FAIL', '%d/%d' % (sum(res), len(res)))
sys.exit(0 if all(res) else 1)
