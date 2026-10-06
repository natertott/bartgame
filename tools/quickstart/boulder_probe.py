"""The one-way boulders, measured in the ROM.

Three things, each against a control:

  1. NO AUTO-FILL. Entering Trilby Highlands puts its rock at (344,664),
     the rock's own spot, and not in the hole at (344,648) where the
     retired QuickStartFillBoulderHoles used to drive it. With the rock's
     flag (HYRULE_FIELD local 0x92) set beforehand, the manager spawns it
     IN the hole - the flag is the save's word for "pushed".

  2. THE HELD MASK. QuickStartHeldReachMask reports QS_REACH_BOULDER_TRIL_1
     exactly when that flag is set, and QS_REACH_LLR_NORTH when boulder 3's
     flag (0x7a) OR the Lon Lon Key is held.

  3. THE PARTITION. For each Lon Lon Ranch and Trilby entrance the survey
     named, a collision flood from the landing with the boulders out and
     with each one in, reporting which doors and borders the landing's
     component holds. This is the user's 2026-10-06 partition measured
     from the ROM's own collision - the cross-check the report asked for.

Usage: python3 tools/quickstart/boulder_probe.py [--rom tmc-d3.gba]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, press, r16, room_dims, coll_at, act_at, entities, KIND_OBJECT, SAVE_FLAGS, poison_here, ROOM_CONTROLS, PLAYER
import parse_tables as P
import callrom as C

HF = P.AREAS['AREA_HYRULE_FIELD']
TRIL = P.ROOMS['ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS']
LLR = P.ROOMS['ROOM_HYRULE_FIELD_LON_LON_RANCH']
PUSHABLE_ROCK = 46
LONLON_KEY = P.ITEMS.get('ITEM_QST_LONLON_KEY', 0x3b)


def bank_bit(c, area, flag):
    base = C.call_keep(c, C.map_sym('GetFlagBankOffset'), (area,))
    return base + flag


def set_flag(c, area, flag, v=1):
    b = bank_bit(c, area, flag)
    a = SAVE_FLAGS + (b >> 3)
    m = 1 << (b & 7)
    c.memory.u8[a] = (c.memory.u8[a] | m) if v else (c.memory.u8[a] & ~m)


def rocks(c):
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    return sorted((x - ox, y - oy) for (_i, _k, ident, _t, x, y) in entities(c, KIND_OBJECT) if ident == PUSHABLE_ROCK)


def flood(c, sx, sy):
    w, h = room_dims(c)
    w >>= 4
    h >>= 4
    seen, stack = set(), [(sx, sy)]
    while stack:
        x, y = stack.pop()
        # Collision 0 and not a pit: a hole's tile reads open to a collision
        # flood and swallows a player, and the holes beside these boulders
        # are exactly where that matters (act tiles 25 and 240 are what the
        # rock itself tests for, pushableRock.c).
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h) or coll_at(c, x, y) != 0 \
                or act_at(c, x, y) in (25, 240):
            continue
        seen.add((x, y))
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return seen


def near(comp, x, y, r=2):
    tx, ty = x >> 4, y >> 4
    return any((tx + dx, ty + dy) in comp for dx in range(-r, r + 1) for dy in range(-r, r + 1))


LLR_PLACES = [
    ('house W door', 344, 632), ('house E door', 392, 632), ('cave lower door', 232, 436),
    ('cave upper door (Tingle)', 184, 340), ('wallet cave', 504, 520), ('Goron stairs', 136, 852),
    ('exit W (Trilby)', 8, 560), ('exit NW (NHF)', 10, 163), ('exit N (Veil)', 88, 16),
    ('exit E445', 712, 445), ('exit E750', 712, 750), ('exit E903', 712, 903), ('exit S (EH)', 298, 968),
    ('Minish paths door', 480, 372), ('stump (313,391)', 313, 391), ('pocket (427,278)', 427, 278),
]
LLR_STARTS = [('S', 298, 950), ('E903', 700, 903), ('E445', 700, 445), ('E750', 700, 750), ('W', 20, 560), ('NW', 20, 163)]
TRIL_PLACES = [
    ('Percy treehouse', 64, 904), ('Keese chest cave', 136, 546), ('rupee cave', 56, 680),
    ('fairy fountain', 408, 690), ('dig cave', 136, 148), ('ladder cave near (280,644)', 280, 644),
    ('ladder cave far (152,644)', 152, 644), ('exit S (WW-N)', 363, 950), ('exit E (LLR)', 470, 560),
    ('exit NE (NHF)', 470, 129), ('exit W (Crenel)', 8, 414), ('gold chest (280,455)', 280, 455),
    ('old boss spot (88,600)', 88, 600), ('entrance (360,360)', 360, 360), ('reward (360,504)', 360, 504),
]
TRIL_STARTS = [('NE', 460, 129), ('S', 363, 940), ('E', 460, 560), ('W', 20, 414)]


def partition(rom, room, starts, places, flags):
    print('  %-28s' % 'flags set' + ''.join(' %-5s' % s[0] for s in starts))
    for label, fl in flags:
        comps = []
        for name, x, y in starts:
            c = boot(rom)
            for f in fl:
                set_flag(c, HF, f)
            poison_here(c)
            warp(c, HF, room, x, y)
            for _ in range(10):
                press(c, c.KEY_A, 5, 5)
            ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
            px = (r16(c, PLAYER + 0x2e) - ox) >> 4
            py = (r16(c, PLAYER + 0x32) - oy) >> 4
            comps.append((flood(c, px, py), rocks(c)))
        print('  -- %s: rocks %s' % (label, comps[0][1]))
        for name, x, y in places:
            print('  %-28s' % name + ''.join(' %-5s' % ('yes' if near(comp, x, y) else '-') for comp, _ in comps))


def main():
    rom = 'tmc-d3.gba'
    if '--rom' in sys.argv:
        rom = sys.argv[sys.argv.index('--rom') + 1]
    ok = True
    # 1. no auto-fill, and the flag puts the rock in the hole
    c = boot(rom)
    poison_here(c)
    warp(c, HF, TRIL, 360, 360)
    for _ in range(10):
        press(c, c.KEY_A, 5, 5)
    r0 = rocks(c)
    print('Trilby rock with no flag:', r0)
    c = boot(rom)
    set_flag(c, HF, 0x92)
    poison_here(c)
    warp(c, HF, TRIL, 360, 360)
    for _ in range(10):
        press(c, c.KEY_A, 5, 5)
    r1 = rocks(c)
    print('Trilby rock with flag 0x92:', r1)
    t1 = r0 == [(344, 664)] and r1 == [(344, 648)]
    print('PASS' if t1 else 'FAIL', 'rock stays at its spot without the flag and sits in the hole with it')
    ok &= t1
    # 2. the held mask
    held = C.call_keep(c, C.game_sym('QuickStartHeldReachMask'), ())
    c2 = boot(rom)
    held0 = C.call_keep(c2, C.game_sym('QuickStartHeldReachMask'), ())
    TRIL_BIT, NORTH_BIT = 1 << 25, 1 << 22
    t2 = (held & TRIL_BIT) and not (held0 & TRIL_BIT)
    print('PASS' if t2 else 'FAIL', 'held mask: boulder TRIL bit %s with the flag, %s without' % (bool(held & TRIL_BIT), bool(held0 & TRIL_BIT)))
    ok &= t2
    set_flag(c2, HF, 0x7a)
    heldN = C.call_keep(c2, C.game_sym('QuickStartHeldReachMask'), ())
    c3 = boot(rom)
    C.call_keep(c3, C.map_sym('SetInventoryValue'), (LONLON_KEY, 1))
    heldK = C.call_keep(c3, C.game_sym('QuickStartHeldReachMask'), ())
    t3 = (heldN & NORTH_BIT) and (heldK & NORTH_BIT) and not (held0 & NORTH_BIT)
    print('PASS' if t3 else 'FAIL', 'LLR_NORTH: flag 0x7a %s, key %s, neither %s' % (bool(heldN & NORTH_BIT), bool(heldK & NORTH_BIT), bool(held0 & NORTH_BIT)))
    ok &= t3
    # 3. room reach through the test window: Percy's treehouse from the Trilby drop
    fn = C.game_sym('QuickStartReachTestRoom')
    tree = (P.AREAS['AREA_TREE_INTERIORS'], P.ROOMS['ROOM_TREE_INTERIORS_PERCYS_TREEHOUSE'])
    a = C.call_keep(c3, fn, (4, 0) + tree, budget=4000000)
    b = C.call_keep(c3, fn, (4, TRIL_BIT) + tree, budget=4000000)
    d = C.call_keep(c3, fn, (4, 1 << 2) + tree, budget=4000000)
    t4 = a == 0 and b == 1 and d == 1
    print('PASS' if t4 else 'FAIL', "Percy's treehouse from the Trilby drop: nothing %d, boulder %d, bracelets %d" % (a, b, d))
    ok &= t4
    # 4. the partitions
    print('\nLon Lon Ranch, what each landing can walk to (collision flood):')
    partition(rom, LLR, LLR_STARTS, LLR_PLACES, [('none', []), ('boulder 1 (0x7b)', [0x7b]), ('boulder 3 (0x7a)', [0x7a]), ('all three', [0x7a, 0x7b, 0x7c])])
    print('\nTrilby Highlands:')
    partition(rom, TRIL, TRIL_STARTS, TRIL_PLACES, [('none', []), ('boulder (0x92)', [0x92])])
    print('\nRESULT', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
