"""The new grant rules, asked of the ROM rather than of the diff.

Four things changed in how items land:

  bottles      A bottled item used to be thrown away when no bottle held
               0x20. GiveItem case 4 now spends an empty bottle first,
               grants a NEW bottle when every one in hand is full, and only
               overwrites slot 0 when all four are full.
  bomb bag     ITEM_BOMBS / ITEM_REMOTE_BOMBS now grant ITEM_BOMBBAG, so
               later bag draws EXPAND the bag (10 -> 30 -> 50 -> 99)
               instead of being spent granting it.
  light arrow  a new rare row behind the Bow. The risk worth measuring is
               not the grant, it is the PAUSE MENU: the lantern's two ids
               hang it, and the bow's two share a menu slot as well.
  sword arts   three new rare SKILL rows.

Usage: python3 tools/quickstart/item_grants.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, press, poison_here
from callrom import call_keep, map_sym
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
SAVE = 0x02002a40
GIVE_ITEM = map_sym('GiveItem')
GET_INV = map_sym('GetInventoryValue')

I = {}
for line in open(os.path.join(P.ROOT, 'build/USA/enum_include/item.inc')):
    m = re.match(r'\.set (ITEM_\w+), (\d+)', line.strip())
    if m:
        I.setdefault(m.group(1), int(m.group(2)))

# gSave.stats offsets, from include/save.h
STATS = None


def find_offsets():
    """bottles[4] and bombBagType. The Stats struct lives in player.h, not
    save.h - read both rather than hardcoding, so a struct edit breaks the
    probe loudly instead of pointing it at the wrong bytes."""
    txt = open(os.path.join(P.ROOT, 'include/player.h')).read()
    out = {}
    for name, decl in (('bottles', r'u8\s+bottles'), ('bombBagType', r'u8\s+bombBagType')):
        m = re.search(r'/\*\s*(0x[0-9a-fA-F]+)\s*\*/\s*' + decl, txt)
        if m:
            out[name] = int(m.group(1), 16)
    return out


def start(c=None):
    c = boot(ROM)
    poison_here(c)
    warp(c, 7, 0, 0x78, 0xa0)
    for _ in range(10):
        press(c, c.KEY_A, 5, 5)
    return c


def inv(c, item):
    return call_keep(c, GET_INV, (I[item],))


def main():
    off = find_offsets()
    if 'bottles' not in off or 'bombBagType' not in off:
        print('could not locate gSave.stats fields in include/save.h - INCONCLUSIVE')
        return 2
    # stats is a sub-struct; its base is what makes the absolute address.
    m = re.search(r'/\*\s*(0x[0-9a-fA-F]+)\s*\*/\s*Stats\s+stats', open(os.path.join(P.ROOT, 'include/save.h')).read())
    if not m:
        print('could not locate gSave.stats - INCONCLUSIVE')
        return 2
    base = SAVE + int(m.group(1), 16)
    BOTTLES = base + off['bottles']
    BAGTYPE = base + off['bombBagType']
    results = []

    def check(label, got, want):
        ok = got == want
        print(f'{label:<46} {str(got):<28} {"ok" if ok else "FAIL (want %s)" % (want,)}')
        results.append(ok)

    # --- bottles ---------------------------------------------------------
    c = start()
    bottles = lambda: [c.memory.u8[BOTTLES + i] for i in range(4)]
    owned = lambda: [inv(c, 'ITEM_BOTTLE%d' % (i + 1)) for i in range(4)]
    print('boot state: bottles', bottles(), 'owned', owned())
    # one empty bottle is pre-granted, so the first bottled item fills it
    call_keep(c, GIVE_ITEM, (I['ITEM_BOTTLE_FAIRY'], 0))
    check('bottled item fills the empty bottle', bottles()[0], I['ITEM_BOTTLE_FAIRY'])
    check('  ...without granting a second bottle', owned(), [1, 0, 0, 0])
    # now every bottle in hand is full: a new one should arrive with it
    call_keep(c, GIVE_ITEM, (I['ITEM_BOTTLE_RED_POTION'], 0))
    check('full bottle -> a NEW bottle is granted', owned(), [1, 1, 0, 0])
    check('  ...and the item is in the new one', bottles()[:2],
          [I['ITEM_BOTTLE_FAIRY'], I['ITEM_BOTTLE_RED_POTION']])
    call_keep(c, GIVE_ITEM, (I['ITEM_BOTTLE_BLUE_POTION'], 0))
    call_keep(c, GIVE_ITEM, (I['ITEM_BOTTLE_FAIRY'], 0))
    check('four bottled items -> four bottles', owned(), [1, 1, 1, 1])
    before = bottles()
    call_keep(c, GIVE_ITEM, (I['ITEM_BOTTLE_RED_POTION'], 0))
    check('fifth item replaces slot 1 only', bottles(),
          [I['ITEM_BOTTLE_RED_POTION'], before[1], before[2], before[3]])
    del c

    # --- bomb bag --------------------------------------------------------
    c = start()
    check('boot: no bomb bag', inv(c, 'ITEM_BOMBBAG'), 0)
    call_keep(c, GIVE_ITEM, (I['ITEM_BOMBS'], 0))
    check('ITEM_BOMBS grants the bomb bag', inv(c, 'ITEM_BOMBBAG'), 1)
    check('  ...at the smallest size', c.memory.u8[BAGTYPE], 0)
    call_keep(c, GIVE_ITEM, (I['ITEM_BOMBBAG'], 0))
    check('a later bag EXPANDS it', c.memory.u8[BAGTYPE], 1)
    call_keep(c, GIVE_ITEM, (I['ITEM_BOMBBAG'], 0))
    call_keep(c, GIVE_ITEM, (I['ITEM_BOMBBAG'], 0))
    call_keep(c, GIVE_ITEM, (I['ITEM_BOMBBAG'], 0))
    check('and caps at the largest', c.memory.u8[BAGTYPE], 3)
    del c

    c = start()
    call_keep(c, GIVE_ITEM, (I['ITEM_REMOTE_BOMBS'], 0))
    check('ITEM_REMOTE_BOMBS grants it too', inv(c, 'ITEM_BOMBBAG'), 1)
    del c

    # --- light arrow + sword arts ---------------------------------------
    c = start()
    call_keep(c, GIVE_ITEM, (I['ITEM_BOW'], 0))
    call_keep(c, GIVE_ITEM, (I['ITEM_LIGHT_ARROW'], 0))
    check('light arrow grants', inv(c, 'ITEM_LIGHT_ARROW'), 1)
    check('  ...alongside the bow', inv(c, 'ITEM_BOW'), 1)
    for art in ('ITEM_SKILL_SPIN_ATTACK', 'ITEM_SKILL_FAST_SPIN',
                'ITEM_SKILL_FAST_SPLIT', 'ITEM_SKILL_LONG_SPIN'):
        call_keep(c, GIVE_ITEM, (I[art], 0))
        check('%s grants' % art[11:].lower(), inv(c, art), 1)
    # The real question for the bow pair: does the pause menu still run?
    # The lantern pair hangs its slot fill loop forever, and these two also
    # share a menu slot.
    # gMain.ticks. gMain is a linker symbol; the offset is counted off the
    # Main struct in include/main.h (11 bytes then a u16 at 12).
    TICKS = 0x03001000 + 0x0C
    before = c.memory.u8[TICKS] | (c.memory.u8[TICKS + 1] << 8)
    press(c, c.KEY_START, 4, 4)
    for _ in range(180):
        c.run_frame()
    after = c.memory.u8[TICKS] | (c.memory.u8[TICKS + 1] << 8)
    moved = (after - before) & 0xFFFF
    ok = moved > 100
    print(f'{"pause menu still ticking with both bow ids":<46} {"+%d ticks" % moved:<28} '
          f'{"ok" if ok else "FAIL (frozen)"}')
    results.append(ok)
    del c

    print()
    bad = results.count(False)
    print('PASS: %d checks' % len(results) if not bad else 'FAIL: %d of %d' % (bad, len(results)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
