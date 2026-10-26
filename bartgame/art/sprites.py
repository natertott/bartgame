"""BARTGAME sprite sheets. Each sheet: frames of w x h pixels as rows of
hex digits ('.' = transparent), stored in OBJ 1D order.

Every sheet but the Drain's two keepers comes from the sprite pack
(art/pack/, imported from art/ref/pack/ by tools/import_pack.py), in its
palette group; the keepers are drawn by hand (sw_folk.py). The frame
order, which the engine's F_* constants follow, is the order of the
hand-drawn sheets the pack replaced (hero.py, monsters.py, items.py,
items32.py, folk.py, marks.py), so code that counts frames
(the roll's four turns, the pickups' table) keeps working."""
import pack
from hero import FRAMES as HERO_ORDER, SWORD as SWORD_ORDER, SHIELD as SHIELD_ORDER
from monsters import BEETLE, BAT, SLIME, SPITTER, KNIGHT, KSWORD, BOSS
from items import ITEMS, FX, PROJ, LIFT, ARROW, MOUTH
from folk import NPC
import sw_folk
from marks import MARKS, DOTS, CURSOR
from items32 import PICK32, ICON32

SHEETS = []


def sheet(name, order, extra=()):
    """the pack's sheet, its frames in the engine's order (and any the
    pack appends, after them)"""
    order = list(order) + list(extra)
    frames = pack.frames(name)
    assert set(frames) == set(order), (name, sorted(set(frames) ^ set(order)))
    s = pack.META['sheets'][name]
    w, h = s['w'], s['h']
    out = {k: frames[k] for k in order}
    for fname, rows in out.items():
        assert len(rows) == h and all(len(r) == w for r in rows), (name, fname)
    SHEETS.append({'name': name, 'pal': pack.group(name), 'w': w, 'h': h, 'frames': out})


sheet('hero', HERO_ORDER)
sheet('sword', SWORD_ORDER)
sheet('shield', SHIELD_ORDER)
sheet('items', ITEMS)
sheet('beetle', BEETLE)
sheet('bat', BAT)
sheet('slime', SLIME)
sheet('spitter', SPITTER)
sheet('knight', KNIGHT)
sheet('ksword', KSWORD)
sheet('fx', FX)
sheet('proj', PROJ)
# two folk the pack added, not yet placed in the game
sheet('npc', NPC, ['sister_mary_grace', 'brother_mark'])
sheet('boss', BOSS)
sheet('lift', LIFT)
sheet('arrow', ARROW)
sheet('mouth', MOUTH)
sheet('marks', MARKS)
sheet('dots', DOTS)
sheet('cursor', CURSOR)
sheet('pick32', PICK32)
sheet('icon32', ICON32)
# the UI's marks over its boxes (ui_kit.py)
import ui_kit
SHEETS.append({'name': 'uimarks', 'pal': 'uikit', 'w': 8, 'h': 8,
               'frames': {k: ui_kit.obj_rows(v) for k, v in ui_kit.OBJ_MARKS.items()}})
# the dialogue box's faces, drawn by hand (faces.py): 48x48 in sprites of
# 64x64, each in its own palette, loaded into the portrait slot with the
# speaker
import faces  # noqa: E402


def _face(pal, rows):
    idx = {k: '%x' % (i + 1) for i, (k, _) in enumerate(pal)}
    return [''.join('.' if ch == '.' else idx[ch] for ch in r) + '.' * 16 for r in rows] + ['.' * 64] * 16


SHEETS.append({'name': 'face', 'pal': 'portrait', 'w': 64, 'h': 64,
               'frames': {n: _face(p, r) for n, p, r in faces.FACES}})
# the Drain's two keepers, drawn by hand (sw_folk.py), not from the pack
for (_name, _pal, _w, _h, _frames) in sw_folk.SHEETS:
    for _f, _rows in _frames.items():
        assert len(_rows) == _h and all(len(r) == _w for r in _rows), (_name, _f)
    SHEETS.append({'name': _name, 'pal': _pal, 'w': _w, 'h': _h, 'frames': _frames})
