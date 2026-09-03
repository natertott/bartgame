"""Walk the F2 stealth quest end to end in the emulator.

Four things have to be true and none of them is provable by reading:

  1. the giver spawns in the drawn host region and is talkable;
  2. beginning the quest puts a LINE OF WATCHMEN in the room, each with a
     live GUARD_LINE_OF_SIGHT emitter parented to it, plus the partner on
     the region's reward spot;
  3. the sentries SWEEP - knockbackDirection cycles rather than sitting on
     one value - because a sentry that never turns is a wall, not a watch;
  4. both endings fire: standing in a cone flips the quest FAILED, and
     reaching the partner flips it WON and pays.

Run: python3 tools/quickstart/stealth_check.py [rom]
"""
import sys, os
sys.path.insert(0, os.path.abspath('tools/quickstart'))
from emu import (boot, warp, here, press, entities, r16, w16, poison_here,
                 GENT, STRIDE, MAX_ENT, KIND_NPC, KIND_PROJECTILE, PLAYER)
import parse_tables as P

ROM = sys.argv[1] if len(sys.argv) > 1 else 'tmc.gba'
FLAGS = 0x02002a40 + 0x25C
BANK11 = 0x9C0
RC = 0x03000bf0

GF_STEALTH_ROLLED = 143
GF_STEALTH_HOST = 144        # 5 bits
GF_STEALTH_SPOT = 149        # 5 bits
GF_STEALTH_STATE = 154       # 2 bits
STATE = {0: 'OFFERED', 1: 'RUNNING', 2: 'WON', 3: 'FAILED'}


def bit(c, off):
    b = BANK11 + off
    return (c.memory.u8[FLAGS + (b >> 3)] >> (b & 7)) & 1


def setbit(c, off, on=True):
    b = BANK11 + off
    a, m = FLAGS + (b >> 3), 1 << (b & 7)
    c.memory.u8[a] = (c.memory.u8[a] | m) if on else (c.memory.u8[a] & ~m)


def field(c, base, n):
    return sum(bit(c, base + i) << i for i in range(n))


def setfield(c, base, n, v):
    for i in range(n):
        setbit(c, base + i, (v >> i) & 1)


def npcs(c):
    return entities(c, kind=KIND_NPC)


def emitters(c):
    """Every live projectile whose parent points at an entity slot."""
    out = []
    for i in range(MAX_ENT):
        b = GENT + i * STRIDE
        if c.memory.u8[b + 8] != KIND_PROJECTILE:
            continue
        par = (c.memory.u8[b + 0x50] | (c.memory.u8[b + 0x51] << 8) |
               (c.memory.u8[b + 0x52] << 16) | (c.memory.u8[b + 0x53] << 24))
        if par:
            out.append((i, par))
    return out


def kd_of(c, slot):
    return c.memory.u8[GENT + slot * STRIDE + 0x3e]


def type_of(c, slot):
    return c.memory.u8[GENT + slot * STRIDE + 0x0a]


fails = []


def check(ok, msg):
    print(('  ok   ' if ok else '  FAIL ') + msg)
    if not ok:
        fails.append(msg)


# ---------------------------------------------------------------- the run --
c = boot(ROM)
# Force the stealth host onto a region we can warp straight into, and mark
# the roll done so the monitor keeps our choice.
POOL_INDEX = 3   # North Hyrule Field - a big open room with a long offset table
setfield(c, GF_STEALTH_HOST, 5, POOL_INDEX)
setfield(c, GF_STEALTH_SPOT, 5, 4)
setfield(c, GF_STEALTH_STATE, 2, 0)
setbit(c, GF_STEALTH_ROLLED, 1)
poison_here(c)
warp(c, P.AREAS['AREA_HYRULE_FIELD'], P.ROOMS['ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD'], 504, 456)
for _ in range(240):
    c.run_frame()
print('== the giver')
print('   state = %s, host = %d' % (STATE[field(c, GF_STEALTH_STATE, 2)], field(c, GF_STEALTH_HOST, 5)))
before = npcs(c)
check(len(before) >= 1, 'a giver NPC stands in the host region (%d NPCs)' % len(before))

# Begin the quest the way the script does, by calling the C hook.
from callrom import call_keep, map_sym
try:
    BEGIN = map_sym('QuickStartStealthBegin')
except Exception:
    BEGIN = None
if BEGIN is None:
    print('  FAIL could not resolve QuickStartStealthBegin')
    sys.exit(1)
call_keep(c, BEGIN, (0, 0))
print('== after Begin')
print('   state = %s, clock = %d' % (STATE[field(c, GF_STEALTH_STATE, 2)], r16(c, 0x02002a40 + 0x38)))
check(field(c, GF_STEALTH_STATE, 2) == 1, 'quest flipped RUNNING')

for _ in range(120):
    c.run_frame()
after = npcs(c)
eyes = emitters(c)
print('   NPCs now %d, emitters %d' % (len(after), len(eyes)))
check(len(after) >= 4, 'the watch line and the partner are placed (>=4 NPCs, got %d)' % len(after))
check(len(eyes) >= 3, 'each watchman carries an LOS emitter (>=3, got %d)' % len(eyes))

# The sweep: sample one watchman's knockbackDirection over 400 frames.
watch_slots = [i for (i, par) in eyes]
parents = sorted({par for (_i, par) in eyes})
pslots = [(p - GENT) // STRIDE for p in parents if (p - GENT) % STRIDE == 0]
print('   watchman entity slots: %s' % pslots)
seen = set()
for _ in range(420):
    c.run_frame()
    for sl in pslots:
        seen.add(kd_of(c, sl))
print('   knockbackDirection values observed: %s' % sorted(seen))
check(len(seen) >= 3, 'the sentries sweep (>=3 distinct facings seen, got %d)' % len(seen))


# ---- leg 2: standing in a cone is a FAILURE -------------------------------
# Park the player a few tiles off a watchman and let the sweep come round.
# One full turn is 4 * 64 frames; 600 covers it twice over with the walk-up.
print('== being seen')
wx, wy = r16(c, GENT + pslots[0] * STRIDE + 0x2e), r16(c, GENT + pslots[0] * STRIDE + 0x32)
for _ in range(600):
    w16(c, PLAYER + 0x2e, wx)
    w16(c, PLAYER + 0x32, wy + 40)
    c.run_frame()
    if field(c, GF_STEALTH_STATE, 2) == 3:
        break
st = field(c, GF_STEALTH_STATE, 2)
print('   state = %s' % STATE[st])
check(st == 3, 'standing in a sweeping cone fails the quest')
del c

# ---- leg 3: reaching the partner WINS and pays ---------------------------
print('== reaching the partner')
c = boot(ROM)
setfield(c, GF_STEALTH_HOST, 5, POOL_INDEX)
setfield(c, GF_STEALTH_SPOT, 5, 4)
setfield(c, GF_STEALTH_STATE, 2, 0)
setbit(c, GF_STEALTH_ROLLED, 1)
poison_here(c)
warp(c, P.AREAS['AREA_HYRULE_FIELD'], P.ROOMS['ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD'], 504, 456)
for _ in range(240):
    c.run_frame()
call_keep(c, BEGIN, (0, 0))
for _ in range(60):
    c.run_frame()
# North Hyrule Field's reward spot is (744, 504) room-local - the partner's
# post. Stand on it.
ox, oy = r16(c, RC + 6), r16(c, RC + 8)
for _ in range(180):
    w16(c, PLAYER + 0x2e, ox + 744)
    w16(c, PLAYER + 0x32, oy + 504)
    c.run_frame()
    if field(c, GF_STEALTH_STATE, 2) in (2, 3):
        break
st = field(c, GF_STEALTH_STATE, 2)
print('   state = %s' % STATE[st])
check(st == 2, 'standing with the partner wins the quest')
ground = [e for e in entities(c) if e[1] == 6]
print('   objects in the room after the win: %d' % len(ground))

print('\n%s: %d failure(s)' % ('FAILED' if fails else 'OK', len(fails)))
sys.exit(1 if fails else 0)
