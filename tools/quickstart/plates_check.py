"""Walk the linger-plate puzzle end to end in the Grimblade dojo.

Deal the site as QS_EVENT_GATE and reroll visits until the plates variant
comes up. Then: plates visible on screen (screenshot - the doctrine-6
check), stepping on one presses it, stepping off starts the linger,
reaching the second in time opens the cage (ring pots gone), and - the
control - waiting out the linger first leaves the cage shut.
"""
import re
import sys
sys.path.insert(0, '/home/user/bartgame/tools/quickstart')
from emu import boot, warp, here, poison_here, press, entities, r16, qs_site_set, GENT, STRIDE, snap
import parse_tables as P

ROM = '/home/user/bartgame/tmc.gba'
SITE = 16
AREA, ROOM = 37, 5
GRAND = 0x03001150
PLAYER = 0x03001160
POT = PLATE = None
for line in open('/home/user/bartgame/build/USA/enum_include/object.inc'):
    m = re.match(r'\.set (POT|PRESSURE_PLATE), (\d+)', line.strip())
    if m:
        if m.group(1) == 'POT':
            POT = int(m.group(2))
        else:
            PLATE = int(m.group(2))
KIND_OBJECT = 6
QS_EVENT_GATE = 7

def w16a(c, a, v):
    c.memory.u8[a] = v & 0xFF
    c.memory.u8[a + 1] = (v >> 8) & 0xFF

def objs(c, ident):
    return [(idx, x, y) for (idx, k, i2, typ, x, y) in entities(c, kind=KIND_OBJECT) if i2 == ident]

def deal_plates(seed):
    c = boot(ROM)
    base = SITE * 13
    qs_site_set(c, base, 1)
    for b in range(3):
        qs_site_set(c, base + 1 + b, (QS_EVENT_GATE >> b) & 1)
    for b in range(8):
        qs_site_set(c, base + 4 + b, 0)
    qs_site_set(c, base + 12, 0)
    for i in range(4):
        c.memory.u8[GRAND + i] = (seed * 37 + i * 101 + 13) & 0xFF
    poison_here(c)
    warp(c, AREA, ROOM, 0x78, 0xa0)
    if here(c) != (AREA, ROOM):
        return None
    for _ in range(120):
        c.run_frame()
    # Dismiss the deal's own Ezlo hint: an open textbox makes
    # PlayerCanBeMoved() false, and IsCollidingPlayer refuses everything
    # while it is - a standing player who cannot press a plate.
    for _ in range(30):
        press(c, c.KEY_A, 5, 5)
    for _ in range(60):
        c.run_frame()
    return c if objs(c, PLATE) else None

c = None
for seed in range(24):
    c = deal_plates(seed)
    if c:
        print(f'plates dealt on seed {seed}')
        break
if c is None:
    print('plates variant never dealt in 24 seeds')
    sys.exit(1)

plates = objs(c, PLATE)
pots0 = len(objs(c, POT))
print(f'{len(plates)} plate(s) at {[(x, y) for _, x, y in plates]}, {pots0} cage/ring pot(s)')
snap(c, '/tmp/claude-0/-home-user-bartgame/650f03f8-c7a6-58cd-957d-b2eef0cb4e82/scratchpad/plates_deal.png')

def act(idx):
    return c.memory.u8[GENT + idx * STRIDE + 0x0c]

def stand(x, y, frames):
    for _ in range(frames):
        w16a(c, PLAYER + 0x2e, x)
        w16a(c, PLAYER + 0x32, y)
        c.run_frame()

if len(plates) < 2:
    print('short deal - need 2 plates for the walk'); sys.exit(1)
(iA, ax, ay), (iB, bx, by) = plates[0], plates[1]
stand(ax, ay, 30)
print(f'on plate A: action {act(iA)} (want 2)')
okA = act(iA) == 2
stand(bx, by, 30)   # walk to B while A lingers
print(f'on plate B: A action {act(iA)}, B action {act(iB)}')
for _ in range(30):
    c.run_frame()
pots1 = len(objs(c, POT))
print(f'ring pots after both down: {pots1} (want 0 = cage opened)')
ok_open = okA and pots1 == 0
snap(c, '/tmp/claude-0/-home-user-bartgame/650f03f8-c7a6-58cd-957d-b2eef0cb4e82/scratchpad/plates_open.png')

# Control: fresh visit, wait out the linger between plates.
c2 = None
for seed in range(24, 48):
    c2 = deal_plates(seed)
    if c2:
        break
ok_ctrl = None
if c2:
    c = c2
    plates = objs(c, PLATE)
    if len(plates) >= 2:
        (iA, ax, ay), (iB, bx, by) = plates[0], plates[1]
        stand(ax, ay, 30)
        stand(ax, ay - 40, 340)  # step off, wait past the longest linger
        released = act(iA) == 1
        stand(bx, by, 30)
        for _ in range(30):
            c.run_frame()
        pots2 = len(objs(c, POT))
        print(f'control: plate A released after wait: {released}; ring pots after late B: {pots2} (want >0)')
        ok_ctrl = released and pots2 > 0

print('\nPASS' if (ok_open and ok_ctrl) else '\nFAIL')
sys.exit(0 if (ok_open and ok_ctrl) else 1)
