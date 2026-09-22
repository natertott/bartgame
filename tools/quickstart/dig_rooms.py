"""Dig rooms: enemies on the floor, and enemies in about a third of the chests.

Three things the user asked for, and one control each:

  * dig rooms are no longer ? rooms (no content site claims one);
  * they are still populated with enemies on arrival;
  * roughly one chest in three holds an enemy that comes out when opened,
    and the rest still hold items.

The chest roll is measured by re-running the restock many times and
counting, because "about a third" is a distribution, not a value. The
control is a NON-dig room's chest, which must never hold an enemy.

Usage: python3 tools/quickstart/dig_rooms.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, press, poison_here, entities, r16, here, KIND_ENEMY
from callrom import call_keep, game_sym, map_sym
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
CHESTS = 0x02017660
CHEST_ENEMY = 0xE7
RESTOCK = game_sym('QuickStartRestockSmallChests')
IS_DIG = game_sym('QuickStartIsDigRoom')
OPEN_CHEST = map_sym('OpenSmallChest')
results = []


def check(label, got, want):
    ok = got == want
    print('%-52s %-22s %s' % (label, got, 'ok' if ok else 'FAIL (want %s)' % (want,)))
    results.append(ok)


def chest_rows(c):
    out = []
    for i in range(8):
        b = CHESTS + i * 8
        tp = c.memory.u8[b + 4] | (c.memory.u8[b + 5] << 8)
        if tp:
            out.append({'slot': i, 'item': c.memory.u8[b + 2], 'param': c.memory.u8[b + 3],
                        'flag': c.memory.u8[b + 1], 'pos': tp, 'redrawn': c.memory.u8[b + 7]})
    return out


def enter(area, room, x, y):
    c = boot(ROM)
    poison_here(c)
    warp(c, P.AREAS[area], P.ROOMS[room], x, y)
    for _ in range(10):
        press(c, c.KEY_A, 5, 5)
    return c


def main():
    # --- no dig room is a content site any more ---------------------------
    dig_areas = {'AREA_HYRULE_DIG_CAVES', 'AREA_DIG_CAVES', 'AREA_CRENEL_DIG_CAVE',
                 'AREA_VEIL_FALLS_DIG_CAVE', 'AREA_CASTOR_WILDS_DIG_CAVE', 'AREA_HYLIA_DIG_CAVES'}
    sites = [s for s in P.content_sites() if s[0] in dig_areas]
    check('no dig room is a content site', len(sites), 0)

    # --- the room knows what it is ---------------------------------------
    c = enter('AREA_DIG_CAVES', 'ROOM_DIG_CAVES_TRILBY_HIGHLANDS', 184, 104)
    check('QuickStartIsDigRoom in a dig room', call_keep(c, IS_DIG, ()), 1)
    for _ in range(240):
        c.run_frame()
    n = len([1 for e in entities(c, kind=KIND_ENEMY)])
    ok = n > 0
    print('%-52s %-22s %s' % ('dig room populated with enemies', '%d enemies' % n, 'ok' if ok else 'FAIL'))
    results.append(ok)
    del c

    c = enter('AREA_CASTLE_GARDEN', 'ROOM_CASTLE_GARDEN_MAIN', 0x1f8, 0x1e0)
    check('CONTROL not a dig room', call_keep(c, IS_DIG, ()), 0)
    del c

    # --- the chest roll ---------------------------------------------------
    for label, area, room, x, y, expect_enemies in (
            ('dig room', 'AREA_DIG_CAVES', 'ROOM_DIG_CAVES_TRILBY_HIGHLANDS', 184, 104, True),
            ('CONTROL Castle Garden', 'AREA_CASTLE_GARDEN', 'ROOM_CASTLE_GARDEN_MAIN', 0x1f8, 0x1e0, False)):
        c = enter(area, room, x, y)
        rows = chest_rows(c)
        if not rows:
            print('%-52s %s' % (label + ': no chests in this room', 'SKIPPED'))
            del c
            continue
        enemy = total = 0
        for _ in range(300):
            # Clear the once-per-load marker so the restock rolls again.
            for r in rows:
                c.memory.u8[CHESTS + r['slot'] * 8 + 7] = 0
            call_keep(c, RESTOCK, ())
            for r in chest_rows(c):
                total += 1
                if r['param'] == CHEST_ENEMY:
                    enemy += 1
        pct = 100.0 * enemy / total if total else 0
        if expect_enemies:
            ok = 25 <= pct <= 42
            print('%-52s %-22s %s' % (label + ': chests holding an enemy', '%.1f%% of %d' % (pct, total),
                                      'ok' if ok else 'FAIL (want ~33%%)'))
        else:
            ok = enemy == 0
            print('%-52s %-22s %s' % (label + ': chests holding an enemy', '%.1f%% of %d' % (pct, total),
                                      'ok' if ok else 'FAIL (must never)'))
        results.append(ok)
        del c

    # --- opening one really produces an enemy -----------------------------
    c = enter('AREA_DIG_CAVES', 'ROOM_DIG_CAVES_TRILBY_HIGHLANDS', 184, 104)
    rows = chest_rows(c)
    if rows:
        r = rows[0]
        b = CHESTS + r['slot'] * 8
        c.memory.u8[b + 2] = 1       # CHUCHU
        c.memory.u8[b + 3] = CHEST_ENEMY
        before = len([1 for e in entities(c, kind=KIND_ENEMY)])
        call_keep(c, OPEN_CHEST, (r['pos'], 1))
        for _ in range(30):
            c.run_frame()
        after = len([1 for e in entities(c, kind=KIND_ENEMY)])
        ok = after > before
        print('%-52s %-22s %s' % ('opening an enemy chest spawns one', '%d -> %d' % (before, after),
                                  'ok' if ok else 'FAIL'))
        results.append(ok)
    del c

    print()
    bad = results.count(False)
    print('PASS: %d checks' % len(results) if not bad else 'FAIL: %d of %d' % (bad, len(results)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
