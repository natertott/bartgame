"""The free-roam hunt: one region drawn per run hides the Earth Element.

Per seed: reads the drawn element region out of the flag bank, clears wave 0
in a NON-element region (expects a normal tier-draw reward at that region's
reward spot) and in the element region (expects an ITEM_EARTH_ELEMENT ground
item). Run after anything that touches the region monitor, the wave
spawner, the reward path, or the per-region flag block.

Usage: python3 tools/quickstart/freeroam.py [seed ...]
"""
import sys
sys.path.insert(0, 'tools/quickstart')
from emu import here, warp, entities, ROOM_CONTROLS, r16, GENT, STRIDE, MAX_ENT
from seed import boot_pinned

SAVE_FLAGS = 0x02002a40 + 0x25C
FLAG_BANK_12 = 0xA80
QS = 700
GMESSAGE = 0x02000050
ITEM_EARTH_ELEMENT = 0x40  # check item.inc

POOL = [  # (area, room, entrance x, y, reward x, y) from sQuickStartRegionPool
    (7, 0, 504, 480, 504, 264),
    (3, 5, 344, 870, 264, 712),
    (3, 1, 504, 264, 648, 552),
    (3, 6, 504, 456, 744, 504),
    (3, 7, 360, 360, 360, 504),
]

def qs(c, off):
    b = FLAG_BANK_12 + QS + off
    return (c.memory.u8[SAVE_FLAGS + (b >> 3)] >> (b & 7)) & 1

def elem_region(c):
    if not qs(c, 332):
        return None
    return sum(qs(c, 333 + b) << b for b in range(4)) % len(POOL)

def wave_count(c, i):
    return sum(qs(c, 362 + i * 8 + b) << b for b in range(8))

def kill_wave(c):
    """Zero every enemy's health until the room reads clear.

    Mashes A the whole time: an Ezlo hint can queue AFTER the initial
    post-warp dismissal burst, and an active textbox freezes every enemy
    (EntityDisabled reads PRIO_MESSAGE), which makes a healthy wave look
    unkillable - the recurring false-"broken" trap."""
    for f in range(900):
        alive = 0
        for i in range(MAX_ENT):
            b = GENT + i * STRIDE
            if c.memory.u8[b + 8] == 3:  # ENEMY
                c.memory.u8[b + 0x45] = 0
                alive += 1
        if (f // 4) % 2 == 0:
            c.set_keys(c.KEY_A)
        else:
            c.clear_keys(c.KEY_A)
        c.run_frame()
        if alive == 0:
            c.clear_keys(c.KEY_A)
            for _ in range(60):
                c.run_frame()
            return True
    return False

def ground_items(c):
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    return [(e[3], e[4]-ox, e[5]-oy) for e in entities(c, 6) if e[2] == 0]

import re
names = {}
for line in open('build/USA/enum_include/item.inc'):
    m = re.match(r'\.set (\w+), (\d+)', line.strip())
    if m: names.setdefault(int(m.group(2)), m.group(1))

import sys as _sys
seeds = [int(a, 0) for a in _sys.argv[1:]] or [0x1, 0xDEADBEEF, 0x5EED5EED, 0x42]
for sd in seeds:
    c = boot_pinned('tmc.gba', sd)
    er = elem_region(c)
    print(f'seed 0x{sd:08x}: element region = {er}')
    if er is None:
        continue
    # 1) a NON-element region pays a normal reward on wave-0 clear
    non = (er + 1) % len(POOL)
    a, r, ex, ey, rx, ry = POOL[non]
    warp(c, a, r, ex, ey, frames=300)
    for _ in range(120):
        c.set_keys(c.KEY_A); c.run_frame(); c.clear_keys(c.KEY_A); c.run_frame()
    w0 = wave_count(c, non)
    ok = kill_wave(c)
    items = ground_items(c)
    w1 = wave_count(c, non)
    got = [names.get(t, hex(t)) for t, x, y in items if (x, y) == (rx, ry)]
    print(f'  non-element region {non}: wave {w0}->{w1}, cleared={ok}, reward at spot: {got}')
    # 2) the element region drops the Earth Element on wave-0 clear
    a, r, ex, ey, rx, ry = POOL[er]
    warp(c, a, r, ex, ey, frames=300)
    for _ in range(120):
        c.set_keys(c.KEY_A); c.run_frame(); c.clear_keys(c.KEY_A); c.run_frame()
    ok = kill_wave(c)
    items = ground_items(c)
    got = [names.get(t, hex(t)) for t, x, y in items]
    print(f'  element region {er}: cleared={ok}, ground items: {got}')
