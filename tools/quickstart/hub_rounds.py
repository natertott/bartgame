"""The hub's three selection rounds, after they were moved onto the tier table.

Two things to prove, per seed:
  - each round offers 3 DISTINCT items drawn from the band it is supposed to
    draw from (round 1: key items; round 2: rare rewards/stat upgrades, with
    the documented widening; round 3: skills, no rares);
  - every one of those items, taken, actually advances the round. That is
    the part the rework put at risk: detection is now "an item left the row"
    rather than "the inventory changed", and it fires on the frame the
    vanilla item-get cutscene STARTS.

Usage: python3 scratchpad/choice_rounds.py [seed ...]
"""
import re
import sys

sys.path.insert(0, 'tools/quickstart')
from emu import here, entities, ROOM_CONTROLS, PLAYER, r16, w16
from seed import boot_pinned

SAVE_FLAGS = 0x02002a40 + 0x25C
FLAG_BANK_11 = 0x9C0
HUB_PHASE_BIT = FLAG_BANK_11 + 85
ROW_Y = 72
ROW_X = (88, 120, 152)

names = {}
for line in open('build/USA/enum_include/item.inc'):
    m = re.match(r'\.set (ITEM_\w+), (\d+)', line.strip())
    if m:
        names.setdefault(int(m.group(2)), m.group(1))


def phase(c):
    v = 0
    for b in range(4):
        bit = HUB_PHASE_BIT + b
        if (c.memory.u8[SAVE_FLAGS + (bit >> 3)] >> (bit & 7)) & 1:
            v |= 1 << b
    return v


def row(c):
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    out = []
    for e in entities(c):
        if e[1] != 6:
            continue
        lx, ly = e[4] - ox, e[5] - oy
        if ly == ROW_Y and lx in ROW_X:
            out.append((lx, e[3]))
    return sorted(out)


def take(c, lx):
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    w16(c, PLAYER + 0x2e, ox + lx)
    w16(c, PLAYER + 0x32, oy + ROW_Y + 8)
    for _ in range(30):
        c.run_frame()
    for _ in range(240):
        c.set_keys(c.KEY_A)
        c.run_frame()
        c.clear_keys(c.KEY_A)
        c.run_frame()


def advance_to_round(c, target):
    while phase(c) < target:
        items = row(c)
        if not items:
            return False
        take(c, items[0][0])
        for _ in range(120):
            c.run_frame()
    return True


def nm(i):
    return names.get(i, hex(i))


ROUNDS = ((1, 0, 'round 1 key items'),
          (2, 2, 'round 2 rare reward/stat'),
          (3, 4, 'round 3 skills, no rare'))

seeds = [int(a, 0) for a in sys.argv[1:]] or [0x1, 0xDEADBEEF, 0x5EED5EED]

for sd in seeds:
    print(f'########## seed 0x{sd:08x}')
    for rnd, ph, label in ROUNDS:
        c = boot_pinned('tmc.gba', sd)
        if not advance_to_round(c, ph):
            print(f'  {label}: could not reach it')
            continue
        items = row(c)
        ids = [i for _, i in items]
        dup = '' if len(set(ids)) == len(ids) else '  *** DUPLICATE ***'
        print(f'  {label}: ' + ', '.join(f'{nm(i)}@{x}' for x, i in items) + dup)
        for x, item in items:
            c2 = boot_pinned('tmc.gba', sd)
            advance_to_round(c2, ph)
            before = phase(c2)
            take(c2, x)
            for _ in range(150):
                c2.run_frame()
            after = phase(c2)
            print(f'      take {nm(item):26s} phase {before} -> {after} '
                  f'{"ok" if after > before else "STUCK"}')
