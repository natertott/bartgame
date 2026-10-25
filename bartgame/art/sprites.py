"""BARTGAME sprite sheets. Each sheet: frames of w x h pixels as rows of
hex digits ('.' = transparent), stored in OBJ 1D order. The drawings live
in hero.py, monsters.py, items.py and folk.py; this module only lists
them in the order the engine's F_* constants are generated."""
from tiles import A, hflip, vflip  # noqa: F401
from hero import FRAMES as HERO_OLD, SWORD, SHIELD
import hero32
import style as ST
import palettes
from monsters import BEETLE, BAT, SLIME, SPITTER, KNIGHT, KSWORD, BOSS
from items import ITEMS, FX, PROJ, LIFT, ARROW, MOUTH
from folk import NPC, BIG
from portraits import PORTRAITS
from marks import MARKS, DOTS, CURSOR
from items32 import PICK32, ICON32

SHEETS = []

# the style boards: the Bloom, the Peddler and the Gatekeeper come from
# the sheets, their portraits from the UI board; what is still drawn by
# hand is remapped into the boards' palettes
HERO = {k: hero32.FRAMES[k] for k in HERO_OLD if k in hero32.FRAMES}
assert set(HERO) == set(HERO_OLD), set(HERO_OLD) - set(HERO)


def remapped(frames, pal):
    m = palettes.REMAP_OBJ[pal]
    return {k: palettes.remap_rows(v, m) for k, v in frames.items()}


SWORD = remapped(SWORD, 'hero')
SHIELD = remapped(SHIELD, 'hero')
NPC = remapped(NPC, 'folk')
BIG = {
    'sage_1': ST.FOLK_SRC['gatekeeper'], 'sage_2': ST.FOLK_SRC['gatekeeper_talk'],
    # the Peddler's front view reads best at this size; the second frame is a breath
    'merchant_1': ST.FOLK_SRC['peddler_s'], 'merchant_2': ST.FOLK_SRC['peddler_s2'],
}
PORTRAITS = remapped(PORTRAITS, 'portrait')
PORTRAITS['hero'] = ST.PORTRAIT_SRC['hero']
PORTRAITS['hero_surprised'] = ST.PORTRAIT_SRC['hero']
PORTRAITS['peddler'] = ST.PORTRAIT_SRC['peddler']
PORTRAITS['gatekeeper'] = ST.PORTRAIT_SRC['gatekeeper']


def sheet(name, pal, w, h, frames):
    for fname, rows in frames.items():
        assert len(rows) == h and all(len(r) == w for r in rows), (name, fname, len(rows), [len(r) for r in rows])
    SHEETS.append({'name': name, 'pal': pal, 'w': w, 'h': h, 'frames': frames})


sheet('hero', 'hero', 32, 32, HERO)
sheet('sword', 'hero', 16, 16, SWORD)
sheet('shield', 'hero', 16, 16, SHIELD)
sheet('items', 'fx', 16, 16, ITEMS)
sheet('beetle', 'bugs', 16, 16, BEETLE)
sheet('bat', 'bugs', 16, 16, BAT)
sheet('slime', 'bugs', 16, 16, SLIME)
sheet('spitter', 'blight', 16, 16, SPITTER)
sheet('knight', 'iron', 16, 32, KNIGHT)
sheet('ksword', 'iron', 16, 16, KSWORD)
sheet('fx', 'fx', 16, 16, FX)
sheet('proj', 'fx', 8, 8, PROJ)
sheet('npc', 'folk', 16, 32, NPC)
sheet('folk32', 'folk', 32, 32, BIG)
sheet('boss', 'blight', 32, 32, BOSS)
sheet('portrait', 'portrait', 32, 32, PORTRAITS)
sheet('lift', 'lift', 16, 16, LIFT)
sheet('arrow', 'fx', 16, 16, ARROW)
sheet('mouth', 'fx', 32, 32, MOUTH)
sheet('marks', 'ui', 16, 16, MARKS)
sheet('dots', 'ui', 8, 8, DOTS)
sheet('cursor', 'ui', 32, 32, CURSOR)
sheet('pick32', 'fx', 32, 32, PICK32)
sheet('icon32', 'fx', 32, 32, ICON32)
