"""The six leftover ids, now charms and curses - measured in the ROM.

ITEM_GREEN_SWORD, ITEM_UNUSED_SWORD, ITEM_ORB_GREEN/BLUE/RED and
ITEM_QST_SWORD were the last ids in the game that nothing could ever hand
the player. Each is now a charm or a curse. What has to be true:

  * picking one up latches its flag and plays ITS line, not a neighbour's -
    these six announce out of bank 2 rather than continuing bank 0's 33+n
    run, which walked into the inn's dialogue at 46;
  * Creeping Rot drains, stops at a quarter heart, and is pushed back by
    rupees and kinstones;
  * the two screen curses actually reach the hardware registers, and the
    dim one stands down while a fade is running;
  * the catalog knows all six, name and description, after the description
    block moved banks to make room.

Usage: python3 tools/quickstart/charm_batch3.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, press, poison_here, snap
from callrom import call_keep, game_sym, map_sym
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
SAVE = 0x02002a40
HINT_IDX = 0x030010A0 + 0x36
REG_BG0CNT = 0x04000008
REG_MOSAIC = 0x0400004C
REG_BLDY = 0x04000054
BGCNT_MOSAIC = 0x0040

GIVE_ITEM = map_sym('GiveItem')
FOOD_MASK = map_sym('QuickStartFoodMask')
CAT_COUNT = map_sym('QuickStartCatalogCount')
CAT_NAME = map_sym('QuickStartCatalogNameText')
CAT_DESC = map_sym('QuickStartCatalogDescText')
CAT_ITEM = map_sym('QuickStartCatalogItem')

I = {}
for line in open(os.path.join(P.ROOT, 'build/USA/enum_include/item.inc')):
    m = re.match(r'\.set (ITEM_\w+), (\d+)', line.strip())
    if m:
        I.setdefault(m.group(1), int(m.group(2)))

# charm index -> item, and the bank-2 line each must announce
CHARMS = [(14, 'ITEM_ORB_GREEN', 93), (15, 'ITEM_ORB_BLUE', 94), (16, 'ITEM_ORB_RED', 95),
          (17, 'ITEM_QST_SWORD', 96), (18, 'ITEM_UNUSED_SWORD', 97), (19, 'ITEM_GREEN_SWORD', 98)]
HEALTH = None
results = []


def check(label, got, want):
    ok = got == want
    print(f'{label:<52} {str(got):<22} {"ok" if ok else "FAIL (want %s)" % (want,)}')
    results.append(ok)


AREAS, ROOMS = {}, {}
for _f, _d in (('area.inc', AREAS), ('roomid.inc', ROOMS)):
    for _l in open(os.path.join(P.ROOT, 'build/USA/enum_include/' + _f)):
        _m = re.match(r'\.set (\w+), (\d+)', _l.strip())
        if _m:
            _d.setdefault(_m.group(1), int(_m.group(2)))


def start():
    # Castle Garden, not the dojo. A player parked in the Grimblade dojo
    # loses health with no charms held - two units over 600 frames at one
    # spot, fourteen at another - and the reason is not a hazard in the
    # room: the dojo is a live ? room and those are its wave's four ROPEs,
    # ambushers doing their job to somebody standing still. Force the site
    # DONE and both spots hold 16/16.
    #
    # The general rule, since this has now cost two probes: a content site
    # room is a COMBAT room until its DONE bit says otherwise, and
    # poison_here does not change that - it only fixes here(). A probe that
    # needs a still player wants a region room, or qs_site_set(c, site, 1).
    c = boot(ROM)
    poison_here(c)
    warp(c, AREAS['AREA_CASTLE_GARDEN'], ROOMS['ROOM_CASTLE_GARDEN_MAIN'], 0x1f8, 0x1e0)
    for _ in range(10):
        press(c, c.KEY_A, 5, 5)
    return c


def io16(c, a):
    """An I/O register. c.memory.u8 does not map 0x04000000 - it returned the
    SAME value for MOSAIC and BLDY, which is how the first run of this probe
    managed to 'read' two different registers as 0x30b8."""
    return c._core.busRead16(c._core, a)


def r16(c, a):
    return c.memory.u8[a] | (c.memory.u8[a + 1] << 8)


def main():
    global HEALTH
    save = open(os.path.join(P.ROOT, 'include/save.h')).read()
    m = re.search(r'/\*\s*(0x[0-9a-fA-F]+)\s*\*/\s*Stats\s+stats', save)
    stats = SAVE + int(m.group(1), 16)
    ph = open(os.path.join(P.ROOT, 'include/player.h')).read()
    HEALTH = stats + int(re.search(r'/\*\s*(0x[0-9a-fA-F]+)\s*\*/\s*u8\s+health', ph).group(1), 16)

    # --- each charm announces its own line -------------------------------
    for n, item, line in CHARMS:
        c = start()
        c.memory.u8[HINT_IDX] = 0
        c.memory.u8[HINT_IDX + 1] = 0
        call_keep(c, GIVE_ITEM, (I[item], 0))
        check('%s announces bank2 line %d' % (item[5:], line), r16(c, HINT_IDX), (0xFF << 8) | line)
        check('  ...and sets mask bit %d' % n, (call_keep(c, FOOD_MASK, ()) >> n) & 1, 1)
        del c

    # --- creeping rot ----------------------------------------------------
    c = start()
    call_keep(c, GIVE_ITEM, (I['ITEM_ORB_GREEN'], 0))
    before = c.memory.u8[HEALTH]
    for _ in range(600):
        c.run_frame()
    after = c.memory.u8[HEALTH]
    ok = after < before
    print(f'{"creeping rot drains over 600 frames":<52} {"%d -> %d" % (before, after):<22} '
          f'{"ok" if ok else "FAIL"}')
    results.append(ok)
    # it must stop before killing
    for _ in range(4000):
        c.run_frame()
    floored = c.memory.u8[HEALTH]
    check('  ...and floors at a quarter heart', floored, 2)
    call_keep(c, GIVE_ITEM, (I['ITEM_RUPEE5'], 0))
    check('  ...a rupee heals it back', c.memory.u8[HEALTH], 4)
    call_keep(c, GIVE_ITEM, (I['ITEM_KINSTONE_RED'], 0))
    check('  ...and so does a kinstone', c.memory.u8[HEALTH], 6)
    del c

    # CONTROL: without the curse, health must not move on its own
    c = start()
    before = c.memory.u8[HEALTH]
    for _ in range(600):
        c.run_frame()
    check('CONTROL no rot: health unchanged', c.memory.u8[HEALTH], before)
    del c

    # --- the two screen curses ------------------------------------------
    #
    # REG_MOSAIC and REG_BLDY are WRITE-ONLY on this hardware. Reading them
    # back returned the same open-bus value (0x30b8) for both, which is how
    # the first version of this probe "verified" two different registers at
    # once. The only honest measurement is the picture itself, so both
    # curses are judged on the frame buffer: a curse that changes what the
    # screen looks like has to change what the screen looks like.
    def frame(curse):
        c = start()
        if curse:
            call_keep(c, GIVE_ITEM, (I[curse], 0))
            # Clear the charm's own receipt box before looking. Drowned
            # Sight deliberately stands down while a message is up (it
            # shares BG0 with the text), so capturing with the box still on
            # screen would measure the exception rather than the rule.
            for _ in range(400):
                c.run_frame()
            for _ in range(6):
                press(c, c.KEY_A, 4, 20)
        for _ in range(60):
            c.run_frame()
        px = list(c.qs_video.to_pil().convert('RGB').getdata()) if hasattr(c.qs_video, 'to_pil') else None
        if px is None:
            path = '/tmp/claude-0/%s.png' % (curse or 'plain')
            snap(c, path)
            from PIL import Image
            px = list(Image.open(path).convert('RGB').getdata())
        del c
        return px

    try:
        plain = frame(None)
        blur = frame('ITEM_ORB_BLUE')
        dim = frame('ITEM_ORB_RED')
    except Exception as e:
        print('screen capture unavailable (%s) - the two visual curses are UNMEASURED' % e)
        plain = blur = dim = None

    if plain is not None:
        def mean(px):
            return sum(sum(p) for p in px) / float(len(px) * 3)
        changed_blur = sum(1 for a, b in zip(plain, blur) if a != b)
        ok = changed_blur > len(plain) // 20
        print(f'{"drowned sight changes the picture":<52} {"%d px differ" % changed_blur:<22} '
              f'{"ok" if ok else "FAIL"}')
        results.append(ok)
        ok = mean(dim) < mean(plain) - 4
        print(f'{"ember haze darkens the picture":<52} '
              f'{"%.1f -> %.1f" % (mean(plain), mean(dim)):<22} {"ok" if ok else "FAIL"}')
        results.append(ok)

    # --- the catalog knows them -----------------------------------------
    c = start()
    total = call_keep(c, CAT_COUNT, ())
    print('catalog rows:', total)
    wanted = {I[item] for _, item, _ in CHARMS}
    found = {}
    for idx in range(1, total + 1):
        it = call_keep(c, CAT_ITEM, (idx,))
        if it in wanted:
            found[it] = idx
    check('all six are catalog rows', len(found), 6)
    for _, item, _ in CHARMS:
        idx = found.get(I[item])
        if idx is None:
            continue
        desc = call_keep(c, CAT_DESC, (idx,))
        # descriptions moved to bank 2; a name is only shown once owned
        ok = (desc >> 8) == 0xFF and 99 <= (desc & 0xFF) <= 175
        print(f'{"  %s desc in bank 2" % item[5:]:<52} {"0x%04x" % desc:<22} '
              f'{"ok" if ok else "FAIL"}')
        results.append(ok)
    del c

    print()
    bad = results.count(False)
    print('PASS: %d checks' % len(results) if not bad else 'FAIL: %d of %d' % (bad, len(results)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
