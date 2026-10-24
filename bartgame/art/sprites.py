"""BARTGAME sprite sheets. Each sheet: frames of w x h pixels as rows of
hex digits ('.' = transparent), stored in OBJ 1D order. The drawings live
in hero.py, monsters.py, items.py and folk.py; this module only lists
them in the order the engine's F_* constants are generated."""
from tiles import A, hflip, vflip  # noqa: F401
from hero import FRAMES as HERO, SWORD, SHIELD
from monsters import BEETLE, BAT, SLIME, SPITTER, KNIGHT, KSWORD, BOSS
from items import ITEMS, FX, PROJ, LIFT, ARROW, MOUTH
from folk import NPC, BIG
from portraits import PORTRAITS
from marks import MARKS, DOTS, CURSOR

SHEETS = []


def sheet(name, pal, w, h, frames):
    for fname, rows in frames.items():
        assert len(rows) == h and all(len(r) == w for r in rows), (name, fname, len(rows), [len(r) for r in rows])
    SHEETS.append({'name': name, 'pal': pal, 'w': w, 'h': h, 'frames': frames})


sheet('hero', 'hero', 16, 32, HERO)
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
