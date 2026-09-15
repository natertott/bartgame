"""Walk switch puzzle #4 ("watch the eyes") in the running ROM.

Five things have to be true and none of them is provable by reading:

  1. the four-way variant roll can actually land on the blink sequence
     (flagBase+1 and flagBase+7 both set - the combination that used to be
     unreachable);
  2. three LIGHTABLE_SWITCH fixtures are dealt;
  3. during SHOW the switches BLINK - exactly one lit per step, all three
     appearing across the show, and a dark beat at the end;
  4. pressing them in the drawn order during INPUT opens the cage;
  5. the control: a WRONG press resets progress and leaves the cage shut.

Pressing is done by setting the switch's own flag, which is precisely what
LightableSwitch_Type0_Action1 does on a hit.
"""
import sys, os
sys.path.insert(0, os.path.abspath('tools/quickstart'))
from emu import boot, warp, here, poison_here, press, entities
import parse_tables as P

ROM = sys.argv[1] if len(sys.argv) > 1 else 'tmc.gba'
# The site's KIND is derived from the run seed now (QuickStartContentSiteRoll),
# not stored - so a probe cannot stamp QS_EVENT_GATE into a flag block the way
# the older plates probe did, and poking gRand does nothing to it. Pin the run
# seed instead and ask the ROM which sites the seed makes gate sites; at
# 0x11111111 the Goron cave's main chamber is one, and it is a big room, which
# a three-switch fan needs.
SEED = 0x11111111
AREA, ROOM = 47, 1           # AREA_GORON_CAVE / ROOM_GORON_CAVE_MAIN, site 18
# NOT (120,600): that is site 18's own content spot, so the player spawns
# standing on the caged prize, picks it up, and QuickStartSetupContentSite
# returns TRUE and marks the site DONE on the first frame - after which the
# dispatcher never calls it again and the puzzle simply never runs. That
# cost a probe round: the first read of it was "the blink does not blink".
SPAWN = (0x78, 0xc8)
GRAND = 0x03001150
ROOMFLAGS = 0x02034364       # gRoomVars.flags; QS room flag k = bit 256+k
KIND_OBJECT = 6
LIGHTABLE_SWITCH = None
for line in open('build/USA/enum_include/object.inc'):
    if line.startswith('.set LIGHTABLE_SWITCH,'):
        LIGHTABLE_SWITCH = int(line.strip().split(',')[1])

QS_EYES_STEP, QS_EYES_SHOW = 48, 48 * 4
QS_EYES_PERIOD = QS_EYES_SHOW + 48 * 9
PERM = [(0,1,2),(0,2,1),(1,0,2),(1,2,0),(2,0,1),(2,1,0)]
FRAMECOUNT = 0x030010A0      # gRoomTransition.frameCount (s32 at +0)


def rf(c, k):
    b = 256 + k
    return (c.memory.u8[ROOMFLAGS + (b >> 3)] >> (b & 7)) & 1


def set_rf(c, k, on=True):
    b = 256 + k
    a, m = ROOMFLAGS + (b >> 3), 1 << (b & 7)
    c.memory.u8[a] = (c.memory.u8[a] | m) if on else (c.memory.u8[a] & ~m)


def field(c, base, n):
    return sum(rf(c, base + i) << i for i in range(n))


def r32(c, a):
    return (c.memory.u8[a] | (c.memory.u8[a+1] << 8) |
            (c.memory.u8[a+2] << 16) | (c.memory.u8[a+3] << 24))


def switches(c):
    return [e for e in entities(c, kind=KIND_OBJECT) if e[2] == LIGHTABLE_SWITCH]


def deal(seed):
    """Boot on the pinned run seed, poke the LIVE rng so the per-visit variant
    roll differs, and walk in; return (core, flagBase) if the visit dealt the
    blink sequence, else None."""
    c = boot(ROM, seed=SEED)
    for i in range(4):
        c.memory.u8[GRAND + i] = (seed * 37 + i * 101 + 13) & 0xFF
    poison_here(c)
    warp(c, AREA, ROOM, SPAWN[0], SPAWN[1])
    if here(c) != (AREA, ROOM):
        del c
        return None
    for _ in range(150):
        c.run_frame()
    # Dismiss the deal's Ezlo hint - an open textbox freezes the room.
    for _ in range(30):
        press(c, c.KEY_A, 5, 5)
    for _ in range(60):
        c.run_frame()
    for base in range(64, 128, 8):
        if rf(c, base + 0) and rf(c, base + 1) and rf(c, base + 7):
            return c, base
    del c
    return None


fails = []


def check(ok, msg):
    print(('  ok   ' if ok else '  FAIL ') + msg)
    if not ok:
        fails.append(msg)


got = None
for sd in range(24):
    got = deal(sd)
    if got:
        print('== blink sequence dealt on seed %d, flagBase %d' % (sd, got[1]))
        break
if not got:
    print('  FAIL the four-way roll never dealt the blink sequence in 24 tries')
    sys.exit(1)
c, base = got
check(True, 'the variant roll reaches the blink sequence')
sw = switches(c)
check(len(sw) == 3, 'three lightable switches dealt (got %d)' % len(sw))
seq = PERM[field(c, 108, 3) % 6]
print('   drawn sequence: %s' % (seq,))

# ---- the blink ----------------------------------------------------------
lit_seen, dark_beat = [], False
for _ in range(QS_EYES_PERIOD):
    c.run_frame()
    phase = r32(c, FRAMECOUNT) % QS_EYES_PERIOD
    if phase < QS_EYES_SHOW:
        on = [k for k in range(3) if rf(c, 104 + k)]
        if len(on) == 1 and on[0] not in lit_seen:
            lit_seen.append(on[0])
        if phase >= QS_EYES_STEP * 3 and not on:
            dark_beat = True
check(sorted(lit_seen) == [0, 1, 2], 'all three switches blink during SHOW (saw %s)' % lit_seen)
check(dark_beat, 'the show ends on a dark beat')

# ---- the right order opens the cage --------------------------------------
def wait_for_input_phase(c):
    for _ in range(QS_EYES_PERIOD * 2):
        c.run_frame()
        if r32(c, FRAMECOUNT) % QS_EYES_PERIOD >= QS_EYES_SHOW + 8:
            return True
    return False

wait_for_input_phase(c)
for k in seq:
    set_rf(c, 104 + k, True)
    c.run_frame()
    c.run_frame()
print('   progress after the correct order: %d, cage open flag %d'
      % (field(c, 111, 2), rf(c, base + 6)))
check(rf(c, base + 6) == 1, 'the drawn order opens the cage')
del c

# ---- the control: a wrong press resets ------------------------------------
print('== control: a wrong press')
got = None
for sd in range(24):
    got = deal(sd)
    if got:
        break
c, base = got
seq = PERM[field(c, 108, 3) % 6]
wait_for_input_phase(c)
wrong = [k for k in range(3) if k != seq[0]][0]
set_rf(c, 104 + wrong, True)
c.run_frame()
c.run_frame()
print('   pressed %d (expected %d): progress %d, cage open %d'
      % (wrong, seq[0], field(c, 111, 2), rf(c, base + 6)))
check(field(c, 111, 2) == 0, 'a wrong press leaves progress at zero')
check(rf(c, base + 6) == 0, 'a wrong press leaves the cage shut')
check(not any(rf(c, 104 + k) for k in range(3)), 'a wrong press darkens every switch')

print('\n%s: %d failure(s)' % ('FAILED' if fails else 'OK', len(fails)))
sys.exit(1 if fails else 0)
