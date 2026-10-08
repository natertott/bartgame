"""Hyrule Town, the fifteenth region (Oct 2026, the redesign's P2 section
5): is it wired the way the plan says - no ? rooms, every door shut, the
square full of monsters?

  LAND     the REGION scenario on the town's pool row lands in the square;
           the region the game reads there is the town's.
  SWEPT    no vanilla NPC stands in the square (the quirk hook sweeps the
           town's cast); our own sprites only.
  WAVES    enemies are dealt, and killed ones are replaced (the wave loop
           runs), and the first clear pays a reward at the square's centre.
  GATES    the four gates cross both ways, by walking: North and South
           Hyrule Field, Lon Lon Ranch's west pocket and Trilby's east
           landing all open onto the town, and the town's four edges lead
           back to them. With containment live (no probe bypass).
  DOORS    every one of the town's 31 door transitions is refused: standing
           on its trigger and pushing in leaves the player in the square.
  PAUSE    the pause menu opens and closes in the square (a boot-spawn into
           town once froze it on a dungeon-index underflow; a real
           transition must not).
  BOSS     the BOSS scenario on the town row composes a boss in the square.
  HINT     the town's region and element lines are the town's own
           (QuickStartRegionHintLine 14 -> 241, QuickStartElementHintLine
           14 -> 247), not a neighbour's by arithmetic.

    python3 tools/quickstart/town_probe.py [--rom tmc-d3.gba]
"""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import warp, r16, w16, poison_here, ROOM_CONTROLS, PLAYER, here, press, entities, KIND_ENEMY, KIND_NPC, KIND_OBJECT, GENT, STRIDE
import scenario as S
import parse_tables as P
import callrom as C
ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else 'tmc-d3.gba'
SAVE = 0x02002a40
res = []
def check(name, ok, detail=''):
    res.append(ok); print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)
MSG = 0x02000050
GMAIN_TICKS = 0x03001000 + 0x0C
def dismiss(c, limit=900):
    quiet = 0
    for _ in range(limit):
        st, act = c.memory.u8[MSG], c.memory.u8[PLAYER + 0x0c]
        if st == 0 and act not in (0x16, 0x7):
            c.run_frame(); quiet += 1
            if quiet >= 30:
                return
            continue
        press(c, c.KEY_B if (st == 0 and act == 0x16) else c.KEY_A, 3, 17); quiet = 0
def run(c, n):
    for _ in range(n):
        c.run_frame()
def local(c):
    return (r16(c, PLAYER + 0x2e) - r16(c, ROOM_CONTROLS + 6), r16(c, PLAYER + 0x32) - r16(c, ROOM_CONTROLS + 8))
def heal(c):
    c.memory.u8[PLAYER + 0x45] = 24
def go(c, area, room, x, y):
    """A probe warp past containment (QuickStartProbeWarpsFree), then the
    bypass is switched OFF again so the walk that follows is policed."""
    c.memory.u8[SAVE + 0x3C] = 0x51
    dismiss(c); poison_here(c); warp(c, area, room, x, y, frames=20)
    # off again as soon as the warp is under way: a landing that puts the
    # player on a door trigger must meet live containment, not the bypass
    c.memory.u8[SAVE + 0x3C] = 0
    run(c, 280); dismiss(c); heal(c)
    return here(c) == (area, room)
def walk(c, key, want, frames=200):
    for _ in range(frames // 8):
        heal(c); press(c, key, 8, 0)
        if here(c)[:2] == want:
            run(c, 60); dismiss(c)
            return True
    return here(c)[:2] == want
AT, RT = P.AREAS['AREA_HYRULE_TOWN'], P.ROOMS['ROOM_HYRULE_TOWN_MAIN']
HF = P.AREAS['AREA_HYRULE_FIELD']
R = {n: P.ROOMS['ROOM_HYRULE_FIELD_' + n] for n in ('NORTH_HYRULE_FIELD', 'SOUTH_HYRULE_FIELD', 'LON_LON_RANCH', 'TRILBY_HIGHLANDS')}
pool = P.region_pool()
row = [i for i, p in enumerate(pool) if p['roomName'] == 'ROOM_HYRULE_TOWN_MAIN']
check('the town has a pool row', len(row) == 1, 'rows %s of %d' % (row, len(pool)))
row = row[0] if row else 0
QS_REGION_HT = 14

# LAND, SWEPT, WAVES
c = S.boot(ROM, S.KINDS['REGION'], row, 0, kit=2, frames=400); dismiss(c)
ring = C.call_keep(c, C.game_sym('QuickStartRegionOfRoom'), (AT, RT))
check('LAND: the REGION scenario lands in the square', here(c) == (AT, RT), 'here %s player %s' % (here(c), local(c)))
check('LAND: the square is region 14 (Hyrule Town)', ring == QS_REGION_HT, 'region %d' % ring)
npcs = [e for e in entities(c, KIND_NPC) if e[2] != 0x28]
check('SWEPT: no vanilla NPC in the square', not npcs, 'npcs %s' % [(e[2], e[3]) for e in npcs][:6])
n0 = len(entities(c, KIND_ENEMY))
killed = 0; replaced = 0; reward = None
ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
for _ in range(10):
    heal(c)
    for e in entities(c, KIND_ENEMY):
        c.memory.u8[GENT + e[0] * STRIDE + 0x45] = 0; killed += 1
    run(c, 150); dismiss(c)
    replaced = max(replaced, len(entities(c, KIND_ENEMY)))
    reward = C.call_keep(c, C.game_sym('QuickStartGetRegionRewardState'), (row,))
check('WAVES: enemies are dealt, and replaced', n0 > 0 and replaced > 0, 'first %d, killed %d, next waves up to %d' % (n0, killed, replaced))
# The clear reward drops at the player's feet (QuickStartSpawnRegionRewardItem)
# and a player standing still takes it at once: state 1 dropped, 2 taken.
check('WAVES: the first clear pays a reward', reward in (1, 2), 'reward state %s' % reward)

# PAUSE
t0 = c.memory.u8[GMAIN_TICKS]
press(c, c.KEY_START, 4, 60); run(c, 60)
paused_ticking = c.memory.u8[GMAIN_TICKS] != t0
press(c, c.KEY_START, 4, 60); run(c, 120); dismiss(c)
t1 = c.memory.u8[GMAIN_TICKS]; run(c, 30)
check('PAUSE: the menu opens and closes, the game runs on', paused_ticking and c.memory.u8[GMAIN_TICKS] != t1 and here(c) == (AT, RT),
      'here %s' % (here(c),))

# HINT
rl = C.call_keep(c, C.game_sym('QuickStartRegionHintLine'), (QS_REGION_HT,))
el = C.call_keep(c, C.game_sym('QuickStartElementHintLine'), (QS_REGION_HT,)) if True else 0
check('HINT: the town speaks its own lines', rl == 241 and el == 247, 'region line %d, element line %d' % (rl, el))

# DOORS
src = open(os.path.join(P.ROOT, 'src/data/transitions.c')).read()
body = src[src.index('const Transition gExitList_HyruleTown_0[] = {'):]
body = body[:body.index('TransitionListEnd')]
doors = [(int(x, 16), int(y, 16), dst) for x, y, dst in
         re.findall(r'WARP_TYPE_AREA, (0x[0-9a-fA-F]+), (0x[0-9a-fA-F]+), [^\n]*?(AREA_\w+)', body)]
refused = 0; leaked = []
if here(c) != (AT, RT):
    go(c, AT, RT, 520, 664)
for x, y, dst in doors:
    # No warp: the player is MOVED inside the square (same room, no
    # transition) to just below the door, then pushes into it. A warp's own
    # landing can sit on a trigger and muddies which transition is which.
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    w16(c, PLAYER + 0x2e, ox + x); w16(c, PLAYER + 0x32, oy + y + 28)
    run(c, 10)
    for _ in range(10):
        heal(c); press(c, c.KEY_UP, 8, 0)
        if here(c) != (AT, RT):
            break
    run(c, 60)
    if here(c) == (AT, RT):
        refused += 1
    else:
        leaked.append((hex(x), hex(y), here(c)))
        go(c, AT, RT, 520, 664)
check('DOORS: every door transition is refused', not leaked and refused == len(doors), '%d of %d refused %s' % (refused, len(doors), leaked[:4]))

# GATES, by walking with containment live
cases = [
    ('SHF north gate -> town', HF, R['SOUTH_HYRULE_FIELD'], 504, 40, c.KEY_UP),
    ('NHF south gate -> town', HF, R['NORTH_HYRULE_FIELD'], 504, 770, c.KEY_DOWN),
    ('LLR west pocket -> town', HF, R['LON_LON_RANCH'], 40, 560, c.KEY_LEFT),
    ('TRIL east landing -> town', HF, R['TRILBY_HIGHLANDS'], 440, 552, c.KEY_RIGHT),
    ('town north -> NHF', AT, RT, 504, 48, c.KEY_UP),
    ('town south -> SHF', AT, RT, 504, 930, c.KEY_DOWN),
    ('town west -> TRIL', AT, RT, 40, 240, c.KEY_LEFT),
    ('town east -> LLR', AT, RT, 960, 240, c.KEY_RIGHT),
]
want = {'town north -> NHF': (HF, R['NORTH_HYRULE_FIELD']), 'town south -> SHF': (HF, R['SOUTH_HYRULE_FIELD']),
        'town west -> TRIL': (HF, R['TRILBY_HIGHLANDS']), 'town east -> LLR': (HF, R['LON_LON_RANCH'])}
for name, a, r, x, y, key in cases:
    landed = go(c, a, r, x, y)
    target = want.get(name, (AT, RT))
    ok = landed and walk(c, key, target)
    check('GATES: ' + name, ok, 'landed %s, now %s at %s' % (landed, here(c), local(c)))

# BOSS
c = S.boot(ROM, S.KINDS['BOSS'], row, 0, kit=2, frames=400); dismiss(c)
seen = set()
for _ in range(20):
    heal(c); run(c, 60); dismiss(c)
    seen |= {e[2] for e in entities(c, KIND_ENEMY)}
    if C.call_keep(c, C.game_sym('QuickStartIsBossId'), (max(seen) if seen else 0,)) or any(C.call_keep(c, C.game_sym('QuickStartIsBossId'), (i,)) for i in seen):
        break
bosses = [i for i in seen if C.call_keep(c, C.game_sym('QuickStartIsBossId'), (i,))]
check('BOSS: the BOSS scenario composes a boss in the square', here(c) == (AT, RT) and bool(bosses), 'enemy ids %s, bosses %s' % (sorted(seen), bosses))

print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
sys.exit(0 if all(res) else 1)
