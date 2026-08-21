"""Walk the under-bush hide mode end to end.

Forces the scav roll's outputs (host = North Hyrule Field, mode undecided)
and rerolls gRand until the giver-spawn decision picks BUSH. Then, via the
shipped code only: Begin starts the search clock with nothing released;
transforming the hidden tile (the monitor's own predicate - the sword's
ability to do that is what cut_diff already proved) releases the Keaton
and swarm AT the tile; killing the marked set wins and drops the reward.
Timeout control: a search never finished fails with the F1c stake path.
"""
import sys
sys.path.insert(0, '/home/user/bartgame/tools/quickstart')
from emu import boot, warp, here, poison_here, press, entities, r16, qs_set, GENT, STRIDE, KIND_ENEMY
from callrom import call_keep, game_sym

ROM = '/home/user/bartgame/tmc.gba'
SET_TILE_TYPE = 0x08085734
GRAND = 0x03001150
GSAVE = 0x02002a40
TIMER4 = GSAVE + 0x49C
KEATON = None
import re
for line in open('/home/user/bartgame/build/USA/enum_include/enemy.inc'):
    m = re.match(r'\.set (KEATON), (\d+)', line.strip())
    if m:
        KEATON = int(m.group(2))
BEGIN = game_sym('QuickStartScavBegin')

GF_SCAV_ROLLED = 474
GF_SCAV_HOST = 475
GF_SCAV_MODE = 599
GF_SCAV_TILE_X = 601
GF_SCAV_TILE_Y = 607
NHF_POOL_IDX = 3

SAVE_FLAGS = GSAVE + 0x25C
QS_BIT0 = 3388

def qbit(c, n):
    b = QS_BIT0 + n
    return (c.memory.u8[SAVE_FLAGS + (b >> 3)] >> (b & 7)) & 1

def qsbits(c, first, count):
    return sum(qbit(c, first + b) << b for b in range(count))

def r32(c, a):
    return c.memory.u8[a] | (c.memory.u8[a+1]<<8) | (c.memory.u8[a+2]<<16) | (c.memory.u8[a+3]<<24)

def w32(c, a, v):
    for i in range(4):
        c.memory.u8[a+i] = (v >> (8*i)) & 0xFF

def setup(seed):
    c = boot(ROM)
    qs_set(c, GF_SCAV_ROLLED, 1)
    for b in range(4):
        qs_set(c, GF_SCAV_HOST + b, (NHF_POOL_IDX >> b) & 1)
    for i in range(4):
        c.memory.u8[GRAND + i] = (seed * 73 + i * 41 + 9) & 0xFF
    poison_here(c)
    warp(c, 3, 6, 0x1f8, 0x318)
    for _ in range(240):
        c.run_frame()
    for _ in range(10):
        press(c, c.KEY_A, 5, 5)
    for _ in range(120):
        c.run_frame()
    return c

c = None
for seed in range(20):
    c = setup(seed)
    mode = qsbits(c, GF_SCAV_MODE, 2)
    if mode == 2:
        print(f'seed {seed}: mode BUSH')
        break
    print(f'seed {seed}: mode {mode}')
    c = None
if c is None:
    print('bush mode never rolled'); sys.exit(1)

htx = qsbits(c, GF_SCAV_TILE_X, 6)
hty = qsbits(c, GF_SCAV_TILE_Y, 6)
print(f'hidden tile ({htx},{hty})')

call_keep(c, BEGIN, (0, 0))
for _ in range(30):
    c.run_frame()
t = r32(c, TIMER4)
keatons = [e for e in entities(c, kind=KIND_ENEMY) if e[2] == KEATON]
print(f'after Begin: timer4 {t} (want 2100), state RUNNING, keatons {len(keatons)} (want 0)')
ok_begin = t in range(2000, 2101) and not keatons

# cut the bush (the monitor's predicate reads the tile type; the sword's
# power to transform these types is cut_diff's already-proven half).
# Straight into gMapBottom.mapData - SetTileType under the hijack waits on
# a VRAM path that never comes.
MAPDATA = 0x02025eb0 + 4
pos = htx | (hty << 6)
c.memory.u8[MAPDATA + pos * 2] = 0
c.memory.u8[MAPDATA + pos * 2 + 1] = 0
for _ in range(60):
    c.run_frame()
keatons = [e for e in entities(c, kind=KIND_ENEMY) if e[2] == KEATON]
print(f'after cut: keatons {len(keatons)} (want 1), timer4 {r32(c, TIMER4)}')
ok_release = len(keatons) == 1

# kill the marked set the blunt way; the carrier chase already ships on
# the real pipeline, and the state machine is what is under test here
for (idx, k, ident, typ, x, y) in entities(c, kind=KIND_ENEMY):
    c.memory.u8[GENT + idx * STRIDE + 8] = 0
for _ in range(30):
    c.run_frame()
state = qsbits(c, 484, 2)
print(f'after kill: scav state {state} (want 2=WON), timer4 {r32(c, TIMER4)}')
ok_win = state == 2

# timeout control
c2 = None
for seed in range(20, 40):
    c2 = setup(seed)
    if qsbits(c2, GF_SCAV_MODE, 2) == 2:
        break
    c2 = None
ok_fail = None
if c2:
    call_keep(c2, BEGIN, (0, 0))
    for _ in range(30):
        c2.run_frame()
    w32(c2, TIMER4, 3)
    for _ in range(30):
        c2.run_frame()
    state = qsbits(c2, 484, 2)
    keatons = [e for e in entities(c2, kind=KIND_ENEMY) if e[2] == KEATON]
    print(f'timeout control: state {state} (want 3=FAILED), keatons {len(keatons)} (want 0)')
    ok_fail = state == 3 and not keatons

print('\nPASS' if (ok_begin and ok_release and ok_win and ok_fail) else '\nFAIL')
sys.exit(0 if (ok_begin and ok_release and ok_win and ok_fail) else 1)
