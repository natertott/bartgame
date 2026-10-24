"""The pause menu and the save file, played in the ROM.

  PAGES    Start opens the items page; R turns to the key items, the
           map, and round again; Start closes
  GRID     the cursor walks the owned items four to a row; A, B and L
           put the chosen one on their button
  MAP      the overview's cursor moves by cell; A looks closer, B comes
           back; the relic shows once the Nun has asked
  SAVE     a death writes the file; after a reset the title offers
           CONTINUE, and the run resumes in the drain with what it had

    python3 tools/menu_probe.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import probe as P  # noqa: E402
import critical_path as CP  # noqa: E402
import lift_probe as LP  # noqa: E402

S = os.environ.get('SNAPDIR', '/tmp')
res = []
GS_PLAY, GS_MAP = 1, 4
EQ_SWORD, EQ_SHIELD, EQ_BOMBS, EQ_BOW = 1, 5, 2, 6
PG_ITEMS, PG_KEYS, PG_MAP = 0, 1, 2


def check(name, ok, detail=''):
    res.append(bool(ok))
    print('%s %-46s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)


def page(c):
    return P.r8(c, LP.ssym('sPage'))


def zoom(c):
    return P.r8(c, LP.ssym('sZoom'))


def cursor(c):
    return P.r8(c, LP.ssym('sCursor'))


def map_cur(c):
    return P.r8(c, LP.ssym('sMapCur'))


def main():
    c = P.boot()
    P.run(c, 40)
    w = CP.world(c)
    pl = P.sym('gPl')
    P.w8(c, pl + 8, P.r8(c, pl + 8) | 0x02 | 0x20)  # bombs and the gauntlet
    P.w8(c, pl + 7, 7)
    P.w16(c, pl + 4, 123)
    P.enter_forest(c)
    LP.warp(c, w['entry'], 2)
    # PAGES
    P.press(c, 'START', 2, 8)
    check('PAGES: Start opens the items page', CP.gstate(c) == GS_MAP and page(c) == PG_ITEMS, 'state %d page %d' % (CP.gstate(c), page(c)))
    P.snap(c, os.path.join(S, 'menu_p0.png'))
    P.press(c, 'R', 2, 8)
    check('PAGES: R turns to the key items', page(c) == PG_KEYS, 'page %d' % page(c))
    P.press(c, 'R', 2, 8)
    check('PAGES: R turns to the map', page(c) == PG_MAP, 'page %d' % page(c))
    P.press(c, 'R', 2, 8)
    check('PAGES: R turns round to the items', page(c) == PG_ITEMS, 'page %d' % page(c))
    # GRID: sword, shield, bombs owned: the cursor walks them
    P.press(c, 'RIGHT', 2, 4); P.press(c, 'RIGHT', 2, 4)
    check('GRID: the cursor walks right to the bombs', cursor(c) == 2, 'cursor %d' % cursor(c))
    P.press(c, 'RIGHT', 2, 4)
    check('GRID: it stops at the last item', cursor(c) == 2, 'cursor %d' % cursor(c))
    P.press(c, 'L', 2, 4)
    check('GRID: L puts the bombs on the L trigger', P.r8(c, pl + 11) == EQ_BOMBS, 'equip %d %d %d' % (P.r8(c, pl + 9), P.r8(c, pl + 10), P.r8(c, pl + 11)))
    P.press(c, 'LEFT', 2, 4); P.press(c, 'LEFT', 2, 4); P.press(c, 'A', 2, 4)
    check('GRID: A puts the sword on A, off B', P.r8(c, pl + 9) == EQ_SWORD and P.r8(c, pl + 10) == 0, 'equip %d %d %d' % (P.r8(c, pl + 9), P.r8(c, pl + 10), P.r8(c, pl + 11)))
    P.press(c, 'B', 2, 4)
    check('GRID: B takes it back', P.r8(c, pl + 10) == EQ_SWORD and P.r8(c, pl + 9) == 0, '')
    # eight items: a second row, and a scroll for a third
    P.w8(c, pl + 8, 0x7F); P.w8(c, pl + 36, 3)
    P.press(c, 'R', 2, 4); P.press(c, 'R', 2, 8); P.press(c, 'R', 2, 8)  # round to the items, redrawn
    P.press(c, 'DOWN', 2, 4)
    check('GRID: DOWN moves to the second row', cursor(c) == 4, 'cursor %d' % cursor(c))
    P.snap(c, os.path.join(S, 'menu_p0b.png'))
    # MAP
    P.press(c, 'R', 2, 8); P.press(c, 'R', 2, 8)
    cur0 = map_cur(c)
    check('MAP: the cursor starts on this cell', cur0 == w['entry'], 'cursor %d entry %d' % (cur0, w['entry']))
    P.press(c, 'UP', 2, 4)
    check('MAP: UP moves the cursor a row', map_cur(c) == cur0 - 5, 'cursor %d' % map_cur(c))
    P.press(c, 'A', 2, 8)
    check('MAP: A looks closer', zoom(c) == 1, 'zoom %d' % zoom(c))
    P.snap(c, os.path.join(S, 'menu_zoom.png'))
    P.press(c, 'B', 2, 4)
    check('MAP: B comes back', zoom(c) == 0, 'zoom %d' % zoom(c))
    P.press(c, 'START', 2, 8)
    check('PAGES: Start closes', CP.gstate(c) == GS_PLAY, 'state %d' % CP.gstate(c))
    # SAVE: the game saves itself at a death
    P.w16(c, pl, 2)
    A = P.sym('gActors')
    P.w8(c, A + 2, 7)   # the hero's state: dead
    P.w16(c, pl, 0)
    for _ in range(200):
        c.run_frame()
    check('SAVE: a death takes the hero home', CP.area(c) == 0, 'area %d' % CP.area(c))
    CP.dismiss(c)
    P.w16(c, pl + 4, 123)
    gilt = P.r16(c, pl + 4)
    items = P.r8(c, pl + 8)
    c.reset()
    for _ in range(60):
        c.run_frame()
    has = P.r8(c, LP.ssym('sTitleHasSave'))
    check('SAVE: after a reset the title knows the file', has == 1, 'has %d' % has)
    P.snap(c, os.path.join(S, 'menu_title.png'))
    P.press(c, 'START', 2, 40)
    for _ in range(60):
        c.run_frame()
    P.press(c, 'A', 2, 20); P.press(c, 'A', 2, 20)
    check('SAVE: CONTINUE wakes in the drain', CP.gstate(c) == GS_PLAY and CP.area(c) == 0, 'state %d area %d' % (CP.gstate(c), CP.area(c)))
    check('SAVE: with the items it had', P.r8(c, pl + 8) == items, 'items %d' % P.r8(c, pl + 8))
    w2 = CP.world(c)
    check('SAVE: the same wood', w2['entry'] == w['entry'] and w2['goal'] == w['goal'] and w2['cells'][0]['gate'] == w['cells'][0]['gate'], '')
    # NEW GAME from the title is still there
    c.reset()
    for _ in range(60):
        c.run_frame()
    P.press(c, 'DOWN', 2, 4)
    P.press(c, 'START', 2, 40)
    for _ in range(60):
        c.run_frame()
    P.press(c, 'A', 2, 20); P.press(c, 'A', 2, 20)
    check('SAVE: NEW GAME begins afresh', CP.gstate(c) == GS_PLAY and P.r16(c, pl + 4) == 0, 'gilt %d' % P.r16(c, pl + 4))
    print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
    return 0 if all(res) else 1


if __name__ == '__main__':
    sys.exit(main())
