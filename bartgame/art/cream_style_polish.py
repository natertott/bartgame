"""Five native Cream refinements; original regions/profiles stay independent."""
import os
from PIL import ImageDraw
from cream_style_depth import floor, cave
from cream_style_rind import PALETTES as RIND, prop, chest, pit
import cream_polish_water as W
import cream_polish_ladders as L
import cream_polish_walls_a as A
import cream_polish_walls_b as B

STYLE = int(os.environ.get('BART_CREAM','7'))-7
assert 0 <= STYLE < 5
WALLS = A if STYLE < 3 else B
PALETTES = {name:list(colors) for name,colors in RIND.items()}
PALETTES['cream_water'] = list(W.PALETTE)
LADDER = L.RECOMMENDED[STYLE]


def cliff(stage=0,kind='mid',variant=0):
    return WALLS.filler(STYLE,stage,kind,variant)


def climb(stage=0,kind='mid'):
    image = L.foot_floor(LADDER,stage) if kind == 'bottom' else L.ladder(LADDER,stage,kind)
    return image.crop((0,0,16,16))


def rim(stage=0,variant=0,drop=False):
    image=floor(stage,variant)
    d=ImageDraw.Draw(image)
    if drop:
        # A continuous low projecting sill; the vertical front is a separate
        # solid cell immediately below the actual takeoff, never fake floor.
        d.rectangle((0,12,15,15),fill=5)
        d.line((0,12,15,12),fill=7)
        d.line((0,14,15,14),fill=6)
        d.line((0,15,15,15),fill=2)
        d.line((3 if variant%2 else 9,13,5 if variant%2 else 11,13),fill=4)
    else:
        from cream_depth_edges import rim as raised
        image=raised(stage,variant,False)
    return image


def water(stage=0,phase=0,fall=False):
    return W.fall(STYLE,stage,1,'mid',phase) if fall else W.pool(STYLE,stage,phase)
