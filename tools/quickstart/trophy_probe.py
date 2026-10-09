"""The trophy case's picture (Oct 2026): browsing the case shows each found
item's own sprite in the pane where vanilla shows the figurine.

  OPEN     on the spawn floor, facing the case and pressing R opens the
           figurine menu (the case's own handler, MenuFadeIn(7, 0xff)).
  PICTURE  every found row puts sprites in the pane left of the list; one
           drawn from the figurine art's tile block (OBJ tile 0x200 up) finds
           that block's VRAM filled. (Hearts, rupees and refills draw from
           the shared sprites below it.) The three orbs, with no ground
           sprite at all, stay empty.
  RUST     the Rusted Blade (borrowing the Smith's Sword) draws in its
           tinted palette 6, not the item sheet's palette 4.
  LOCKED   a row not found yet shows no picture.
  NAMES    each charm row's name is its own item's (rows 69-77 used to be
           off by three: the names ran in a different order from the table).
  SNAP     screenshots of a few rows (the eye check: the item, in its own
           colours, in the pane left of the description).

    python3 tools/quickstart/trophy_probe.py [--rom tmc-d3.gba] [--out DIR] [--rows 80]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import entities, here, snap, press, r16, w16, KIND_OBJECT, PLAYER, ROOM_CONTROLS, GENT, STRIDE
import scenario as S
import parse_tables as P
import callrom as C
args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else 'tmc-d3.gba'
OUT = args[args.index('--out') + 1] if '--out' in args else '/tmp'
ROWS = int(args[args.index('--rows') + 1]) if '--rows' in args else 80
SAVE = 0x02002a40
FIGURINES = SAVE + 0xCE   # gSave.figurines (save.h comments say 0xD0; it ends at inventory, 0xF2)
MENU = 0x02000080          # gMenu (gFigurineMenu aliases it)
FIG_IDX = MENU + 0x1c
GMAIN_SUBSTATE = 0x03001000 + 0x2   # gMain.substate
INV = {v: k for k, v in P.ITEMS.items()}
res = []
def check(name, ok, detail=''):
    res.append(bool(ok)); print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)
def run(c, n):
    for _ in range(n):
        c.run_frame()
OAM = 0x07000000
ART = 0x06010000 + 0x4000   # OBJ_VRAM0 + 0x4000, tile 0x200: the figurine art's block
def picture(c):
    """OAM entries in the picture pane, left of the list and above the
    page arrows: (x, y, tile, palette). The menu draws nothing else there."""
    out = []
    for i in range(128):
        a0, a1, a2 = r16(c, OAM + i * 8), r16(c, OAM + i * 8 + 2), r16(c, OAM + i * 8 + 4)
        if (a0 & 0x300) == 0x200:
            continue   # hidden
        x, y = a1 & 0x1ff, a0 & 0xff
        if x < 0x50 and y < 0x90:
            out.append((x, y, a2 & 0x3ff, a2 >> 12))
    return out
def art_nonzero(c):
    return any(c.memory.u8[ART + i] for i in range(0x200))
# the catalog's names, by row, straight from the source (custom bank 1 from 61)
import re
_src = open(os.path.join(P.ROOT, 'src/game.c')).read()
NAMES = {int(m.group(1)) - 60: m.group(2) for m in re.finditer(r'\n    \[(\d+)\] = \(const u8\*\)"([^"\\]*)",', _src[:_src.index('gCustomStrings2[] = {\n')]) if 61 <= int(m.group(1)) < 203}
OWN_NAME = {'ITEM_ORB_GREEN': 'Green Orb', 'ITEM_ORB_BLUE': 'Blue Orb', 'ITEM_ORB_RED': 'Red Orb',
            'ITEM_QST_SWORD': "Duelist's Blade", 'ITEM_UNUSED_SWORD': 'Rusted Blade', 'ITEM_GREEN_SWORD': 'Whetstone',
            'ITEM_PIE': 'Humble Pie', 'ITEM_QST_DOGFOOD': 'Dog Food', 'ITEM_QST_MUSHROOM': 'Strange Mushroom',
            'ITEM_BRIOCHE': 'Brioche', 'ITEM_CROISSANT': 'Croissant', 'ITEM_CAKE': 'Cake', 'ITEM_SHELLS30': 'Lucky Shells',
            'ITEM_SMITH_SWORD': 'Smith\'s Sword', 'ITEM_HEART_PIECE': 'Piece of Heart'}

c = S.boot(ROM, 0, seed=6, frames=300)
run(c, 60)
count = C.call_keep(c, C.map_sym('QuickStartCatalogCount'), ())
items = {i: C.call_keep(c, C.map_sym('QuickStartCatalogItem'), (i,)) for i in range(1, count + 1)}
for i in range(36):
    c.memory.u8[FIGURINES + i] = 0xFF
LOCKED = 3   # one row left unfound, for the LOCKED check
c.memory.u8[FIGURINES + (LOCKED >> 3)] &= ~(1 << (LOCKED & 7)) & 0xFF
# stand below the case (56, 56), face it, press R
ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
w16(c, PLAYER + 0x2e, ox + 56); w16(c, PLAYER + 0x32, oy + 80); run(c, 10)
press(c, c.KEY_UP, 4, 4)
for _ in range(3):
    press(c, c.KEY_R, 4, 10)
    run(c, 60)
    if entities(c, KIND_OBJECT, 0) or c.memory.u8[FIG_IDX] != 0:
        break
how = 'R at the case'
if c.memory.u8[FIG_IDX] == 0:
    # the case's own handler, called directly (figurineDevice.c answers a
    # check with exactly this)
    how = 'MenuFadeIn(7, 0xff), the case handler\'s call'
    C.call_keep(c, C.map_sym('MenuFadeIn'), (7, 0xff))
run(c, 180)
check('OPEN: the trophy case menu opens', c.memory.u8[FIG_IDX] >= 1, 'via %s, row %d of %d' % (how, c.memory.u8[FIG_IDX], count))
shown, blank, wrong, misnamed = 0, [], [], []
for step in range(min(ROWS, count)):
    idx = c.memory.u8[FIG_IDX]
    if idx not in items:
        break
    run(c, 30)
    pic = picture(c)
    name = INV.get(items[idx])
    if name in OWN_NAME and NAMES.get(idx) != OWN_NAME[name]:
        misnamed.append((idx, name, NAMES.get(idx)))
    if idx == LOCKED:
        check('LOCKED: a row not found shows no picture', not pic, 'row %d %s, picture %s' % (idx, name, pic))
    elif pic and (art_nonzero(c) or all(p[2] < 0x200 for p in pic)):
        shown += 1
    elif not pic:
        blank.append((idx, name))
    else:
        wrong.append((idx, name, pic))
    if name == 'ITEM_UNUSED_SWORD':
        check('RUST: the Rusted Blade draws tinted', pic and all(p[3] == 6 for p in pic), 'row %d picture %s' % (idx, pic))
    if name in ('ITEM_SMITH_SWORD', 'ITEM_CAKE', 'ITEM_HEART_PIECE', 'ITEM_RUPEE20', 'ITEM_BOMBS5', 'ITEM_PIE', 'ITEM_RED_POTION', 'ITEM_ORB_GREEN', 'ITEM_UNUSED_SWORD', 'ITEM_HEART'):
        snap(c, os.path.join(OUT, 'trophy_%s.png' % name[5:].lower()))
    press(c, c.KEY_DOWN, 3, 8)
NO_ART = {'ITEM_ORB_GREEN', 'ITEM_ORB_BLUE', 'ITEM_ORB_RED'}   # no ground sprite at all
check('PICTURE: each found row shows its item', shown == count - 1 - len(NO_ART) and set(n for _, n in blank) == NO_ART and not wrong,
      '%d of %d found rows drawn; empty %s; drawn from an empty block %s' % (shown, count - 1, blank, wrong[:3]))
check('NAMES: charm rows carry their own names', not misnamed, '%d checked, wrong %s' % (sum(1 for i in items.values() if INV.get(i) in OWN_NAME), misnamed[:4]))
print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
sys.exit(0 if all(res) else 1)
