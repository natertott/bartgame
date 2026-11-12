"""BLACK RIND TERRACES — optional native Cream environment study.

Broad oyster shelves project from clotted curd and wet, mold-dark recesses.
All marks are authored directly on indexed 16px canvases (cave 32x48 and
chest 32x32).  This module does not import or alter production terrain.
"""
from PIL import Image, ImageDraw


# Index roles: 1 void, 2 wet cut, 3/4 shadow planes, 5/6 curd body,
# 7/8 upper-left lip, 9/10/11 living mold, 12/13/14 rot, 15 pinpoint light.
# Every component is an exact five-bit channel value, expressed as RGB888.
PALETTES = {
    'cream_floor0': ['#000000', '#282830', '#484840', '#909080', '#c8c0a8', '#d8d0b8', '#e0d8c0', '#e8e0c8', '#f0e8d0', '#405048', '#607060', '#889078', '#484050', '#685870', '#a080b0', '#f8f0d8'],
    'cream_floor1': ['#000000', '#282830', '#484848', '#888878', '#b8b8a8', '#c8c8b8', '#d0d0c0', '#d8d8c8', '#e8e8d8', '#484c48', '#687068', '#909080', '#484048', '#706078', '#a880b0', '#f0f0d8'],
    'cream_floor2': ['#000000', '#201828', '#403848', '#807880', '#b0a8a8', '#c0b8b0', '#c8c0b8', '#d8c8c0', '#e0d8d0', '#384038', '#586050', '#808870', '#482840', '#784880', '#c068d8', '#f0e0f0'],
    'cream_cliff0': ['#000000', '#202028', '#303830', '#485048', '#606050', '#888870', '#b0b098', '#d8d0b0', '#eee0c8', '#384838', '#587050', '#809068', '#383040', '#605068', '#a080b0', '#f8f0d8'],
    'cream_cliff1': ['#000000', '#202028', '#303038', '#484848', '#606058', '#808078', '#a0a090', '#c0c0a8', '#d8d8c0', '#384038', '#586058', '#788070', '#403040', '#685068', '#a070a8', '#f0e8d0'],
    'cream_cliff2': ['#000000', '#181820', '#282030', '#383040', '#504050', '#686058', '#908078', '#b8a098', '#d8c0b0', '#303830', '#485840', '#708060', '#482048', '#884890', '#d078e0', '#f8d8f8'],
    'cream_water': ['#000000', '#202828', '#384038', '#505848', '#687058', '#889078', '#b0b898', '#d0d0b0', '#e8e8c8', '#384840', '#586858', '#809078', '#382838', '#684870', '#a068b0', '#f0e0e8'],
    'cream_props': ['#000000', '#201828', '#383038', '#584838', '#806040', '#b08848', '#d0b068', '#f0d090', '#f8e8b8', '#304838', '#506850', '#809070', '#482840', '#884890', '#d070e0', '#f8f0d8'],
}
# Quantization is explicit, including the few aesthetically written literals.
PALETTES = {key: ['#%02x%02x%02x' % tuple(int(c[n:n+2], 16)//8*8
                for n in (1, 3, 5)) for c in bank]
            for key, bank in PALETTES.items()}


def _canvas(fill=0, size=(16, 16)):
    im = Image.new('P', size, fill)
    return im, ImageDraw.Draw(im)


def floor(stage=0, variant=0, path=False):
    """A quiet soft curd field, with sparse pressed horizontal impressions."""
    im, d = _canvas(4)
    variant %= 4
    # Nearly equal values are deliberate: the eye belongs to raised shelves.
    if variant == 0:
        d.polygon([(0, 0), (7, 0), (5, 2), (0, 2)], fill=5)
    elif variant == 1:
        d.line([(2, 10), (5, 9), (8, 9)], fill=3)
        d.line((3, 10, 7, 10), fill=5)
    elif variant == 2:
        d.polygon([(10, 3), (14, 3), (15, 4), (12, 5), (9, 5)], fill=5)
    else:
        d.line([(3, 4), (6, 3), (10, 3)], fill=5)
        if stage:
            d.polygon([(10, 12), (12, 10), (15, 10), (15, 13)], fill=11)
            d.line((12, 11, 14, 11), fill=10)
    if path:
        # The route is a pressed, broad light plane, never a checkerboard.
        d.polygon([(0, 6), (6, 5), (15, 6), (15, 10), (7, 10), (0, 9)], fill=5)
        if variant == 1:
            d.line((4, 8, 8, 8), fill=4)
    return im


def _fan(d, x, y, wide=14, sick=0, lit=True):
    """One convex horizontal oyster fan with an attached dark underside."""
    # The scalloped outer contour runs across x, not down like a curtain.
    d.polygon([(x, y+3), (x+2, y+1), (x+5, y), (x+wide-4, y),
               (x+wide-1, y+2), (x+wide, y+4), (x+wide-2, y+6),
               (x+5, y+7), (x+1, y+5)], fill=1)
    d.polygon([(x, y+3), (x+2, y+1), (x+5, y), (x+wide-4, y),
               (x+wide-1, y+2), (x+wide, y+3), (x+wide-3, y+4),
               (x+3, y+4)], fill=6 if sick < 2 else 5)
    d.line([(x+1, y+2), (x+5, y+1), (x+wide-5, y+1)], fill=8 if sick == 0 and lit else 7)
    d.line([(x, y+3), (x+4, y+4), (x+wide-3, y+4), (x+wide, y+3)], fill=7)
    d.line([(x+3, y+5), (x+wide-3, y+5)], fill=3)
    d.line([(x+5, y+2), (x+wide-4, y+2)], fill=5)
    if sick == 1:
        # Sick brackets sag and split; the fissure removes actual top matter.
        d.line([(x+wide-5, y), (x+wide-6, y+2), (x+wide-3, y+4)], fill=2)
        d.line([(x+2, y+3), (x+3, y+4), (x+5, y+4)], fill=10)
    elif sick == 2:
        d.polygon([(x+6, y), (x+8, y), (x+7, y+2), (x+9, y+3),
                   (x+8, y+5), (x+5, y+5), (x+6, y+3)], fill=1)
        d.line([(x+6, y+2), (x+6, y+3), (x+7, y+4)], fill=13)
        d.point((x+6, y+2), fill=14)


def cliff(stage=0, kind='mid', variant=0):
    im, d = _canvas(3 if stage == 0 else 2)
    v = variant % 2
    # Broad connected backing supplies the physical mass behind the shelves.
    d.polygon([(0, 0), (9, 0), (12, 4), (10, 10), (15, 15),
               (0, 15)], fill=4 if stage < 2 else 3)
    d.polygon([(0, 3), (4, 1), (7, 2), (6, 8), (2, 12), (0, 11)], fill=5)
    # Unequal closed fans and offset heights prevent bricklike even bands.
    _fan(d, -2 if not v else 0, 1 if not v else 0, 16 if not v else 13, stage)
    _fan(d, 7 if not v else -3, (9 if not v else 10) + (stage == 1),
         12 if not v else 15, stage, lit=False)
    # Mold remains rooted in one recess; sparse wet threads stay short.
    if stage == 0:
        d.polygon([(0, 7), (3, 6), (6, 7), (7, 9), (4, 10), (0, 9)], fill=9)
        d.line([(0, 7), (3, 7), (5, 8)], fill=11)
        d.line((2, 9, 2, 12), fill=10)
        d.point((2, 13), fill=11)
    elif stage == 1:
        d.polygon([(0, 7), (4, 6), (7, 8), (5, 10), (1, 10)], fill=9)
        d.line([(1, 7), (4, 7), (5, 8)], fill=11)
        d.line([(12, 4), (11, 6), (13, 7)], fill=12)
    else:
        d.polygon([(0, 7), (4, 6), (7, 8), (6, 11), (1, 11)], fill=1)
        d.line([(1, 7), (4, 7), (5, 8), (4, 9)], fill=13)
        d.line((2, 7, 3, 7), fill=14)
        d.polygon([(12, 5), (15, 5), (15, 8), (13, 8)], fill=9)
        d.point((13, 5), fill=11)
    if kind == 'top':
        d.polygon([(0, 0), (15, 0), (15, 2), (12, 3), (8, 2),
                   (4, 3), (0, 2)], fill=7)
        d.line([(0, 0), (7, 0), (9, 1), (14, 1)], fill=8)
        d.line([(0, 3), (4, 4), (8, 3), (12, 4), (15, 3)], fill=1)
    elif kind == 'base':
        d.polygon([(0, 12), (4, 13), (7, 12), (12, 14), (15, 13),
                   (15, 15), (0, 15)], fill=1)
        d.line([(0, 14), (5, 15), (8, 14)], fill=3)
    elif kind == 'left':
        d.polygon([(0, 0), (2, 0), (3, 5), (2, 9), (3, 15), (0, 15)], fill=1)
        d.line([(3, 0), (4, 4), (3, 8), (4, 12), (4, 15)], fill=6)
    elif kind == 'right':
        d.polygon([(14, 0), (15, 0), (15, 15), (12, 15), (13, 9), (12, 5)], fill=1)
        d.line([(12, 1), (12, 4), (13, 6)], fill=3)
    return im


def climb(stage=0, kind='mid'):
    im, d = _canvas(2)
    # Deliberately engineered regular peg pairs: nothing on ordinary walls
    # repeats this cadence. Identical adjacent columns need no handed variant.
    d.rectangle((2, 0, 13, 15), fill=1)
    d.line((1, 0, 1, 15), fill=4)
    d.line((14, 0, 14, 15), fill=3)
    d.line((3, 0, 3, 15), fill=3)
    d.line((12, 0, 12, 15), fill=3)
    for y in (2, 8, 14):
        for x in (3, 10):
            d.rectangle((x, y, x+2, y+2), fill=2)
            d.line((x-1, y, x+2, y), fill=8)
            d.line((x, y+1, x+2, y+1), fill=7)
            d.point((x-1, y+1), fill=6)
    if kind == 'top':
        d.rectangle((0, 0, 15, 1), fill=7)
        d.line((0, 0, 15, 0), fill=8)
        d.rectangle((5, 0, 10, 3), fill=1)
        d.line((6, 0, 9, 0), fill=7)
    elif kind == 'bottom':
        d.rectangle((0, 14, 15, 15), fill=1)
        d.line((2, 14, 13, 14), fill=7)
        d.line((3, 15, 12, 15), fill=5)
    return im


def rim(stage=0, variant=0, drop=False):
    im = floor(stage, variant)
    d = ImageDraw.Draw(im)
    d.polygon([(0, 11), (4, 10), (9, 11), (13, 10), (15, 11),
               (15, 15), (0, 15)], fill=1)
    d.line([(0, 11), (4, 10), (9, 11), (13, 10), (15, 11)], fill=8)
    d.line([(0, 12), (4, 11), (9, 12), (13, 11), (15, 12)], fill=6)
    if drop:
        # A broad, open, recessed breach. No standing growth blocks the path.
        d.rectangle((4, 9, 11, 14), fill=4)
        d.line((4, 10, 4, 14), fill=7)
        d.line((11, 10, 11, 14), fill=2)
        d.line((5, 14, 10, 14), fill=7)
        d.line((6, 15, 9, 15), fill=3)
    else:
        for x in (0, 8):
            d.polygon([(x, 11), (x, 8), (x+2, 5), (x+5, 5),
                       (x+7, 8), (x+6, 12)], fill=1)
            d.polygon([(x, 8), (x+2, 5), (x+5, 5), (x+6, 7),
                       (x+5, 9), (x+1, 9)], fill=10 if stage < 2 else 12)
            d.line([(x+1, 7), (x+3, 6), (x+5, 6)], fill=11 if stage < 2 else 13)
            d.line((x+2, 9, x+1, 12), fill=2)
            if stage == 2:
                d.point((x+3, 6), fill=14)
    return im


def cave(stage=0):
    im, d = _canvas(0, (32, 48))
    d.polygon([(0, 47), (0, 20), (3, 10), (9, 4), (16, 2),
               (24, 5), (29, 12), (31, 23), (31, 47)], fill=1)
    d.polygon([(1, 43), (2, 20), (5, 11), (11, 6), (17, 4),
               (24, 8), (28, 17), (29, 43)], fill=4)
    # Broad cap, then separately lit oyster brackets on the jambs.
    d.polygon([(3, 12), (8, 6), (14, 3), (21, 4), (27, 10),
               (25, 13), (20, 10), (13, 9), (7, 13)], fill=6)
    d.line([(4, 11), (9, 6), (14, 4), (20, 5)], fill=8, width=2)
    d.line([(5, 14), (12, 11), (20, 12), (26, 15)], fill=1, width=2)
    for x, y, w in ((-3, 19, 14), (-4, 31, 13), (23, 21, 13), (24, 34, 12)):
        _fan(d, x, y, w, stage)
    # The portal has substantial empty black mass and a walkable threshold.
    d.polygon([(8, 44), (8, 25), (10, 19), (14, 15), (18, 15),
               (22, 20), (24, 27), (24, 44)], fill=1)
    d.line([(9, 25), (11, 20), (14, 17), (17, 16)], fill=2)
    d.polygon([(6, 44), (11, 40), (23, 40), (27, 45), (25, 47),
               (7, 47)], fill=5)
    d.line((7, 45, 26, 45), fill=8)
    d.line((8, 47, 25, 47), fill=3)
    # Small sacred nail over the opening: gold is kept for prop bank assets;
    # the cliff-bank portal uses an ivory devotional inlay instead.
    d.rectangle((14, 9, 18, 12), fill=1)
    d.line((15, 10, 17, 10), fill=8)
    d.point((16, 12), fill=7)
    if stage == 0:
        d.polygon([(1, 16), (4, 13), (7, 14), (6, 17), (2, 19)], fill=9)
        d.line((3, 14, 5, 14), fill=11)
        d.line((3, 18, 3, 22), fill=10)
    elif stage == 1:
        d.line([(25, 9), (23, 14), (26, 18)], fill=2, width=2)
        d.polygon([(0, 28), (5, 26), (7, 29), (4, 32), (0, 31)], fill=10)
    else:
        d.line([(23, 8), (22, 13), (25, 16), (24, 21)], fill=12, width=3)
        d.line([(23, 9), (23, 13), (25, 16)], fill=13)
        d.line((23, 11, 23, 13), fill=14)
        d.point((25, 16), fill=15)
        d.polygon([(1, 27), (5, 26), (6, 29), (2, 30)], fill=9)
    return im


def water(stage=0, phase=0, fall=False):
    im, d = _canvas(3 if stage < 2 else 12)
    p = phase % 2
    if fall:
        d.rectangle((0, 0, 2, 15), fill=1)
        d.rectangle((13, 0, 15, 15), fill=2)
        d.line((3, 0, 3, 15), fill=5)
        d.rectangle((4, 0, 7, 15), fill=4)
        d.line((11, 0, 11, 15), fill=2)
        for y in (1+4*p, 9+4*p):
            d.line((5, y, 5, min(15, y+3)), fill=7)
            d.line((9, (y+3) % 16, 9, min(15, (y+3) % 16+2)), fill=5)
        d.line((4, 15, 10, 15), fill=6 if not p else 5)
    else:
        d.rectangle((0, 0, 15, 1), fill=2)
        d.line((1, 2, 6, 2), fill=4)
        d.line((2+p*2, 6, 7+p*2, 6), fill=5)
        d.line((3+p*2, 7, 6+p*2, 7), fill=4)
        d.line((10-p*2, 12, 14-p*2, 12), fill=4)
    if stage == 2:
        d.line((6, 4+p*4, 9, 4+p*4), fill=13)
        d.point((6, 4+p*4), fill=14)
    return im


def _base(d):
    d.ellipse((1, 11, 15, 15), fill=1)


def prop(kind='mold', stage=0, phase=0):
    im, d = _canvas()
    if kind == 'mold':
        _base(d)
        # A rooted, blocked bush; overlapping scalloped caps, no climb pegs.
        for x, y, w in ((1, 8, 8), (5, 4, 9), (9, 10, 6)):
            d.polygon([(x, y+3), (x, y+1), (x+2, y-1), (x+w-3, y-1),
                       (x+w-1, y+1), (x+w-1, y+3)], fill=1)
            d.polygon([(x+1, y+1), (x+2, y-1), (x+w-3, y-1),
                       (x+w-2, y+1), (x+w-3, y+2), (x+2, y+2)], fill=10 if stage < 2 else 12)
            d.line((x+2, y, x+w-4, y), fill=11 if stage < 2 else 13)
        d.line((4, 11, 3, 14), fill=9)
        if stage == 1:
            d.line([(9, 4), (8, 6), (11, 8)], fill=2)
        elif stage == 2:
            d.line((8, 4, 10, 4), fill=14)
    elif kind == 'lamp':
        _base(d)
        d.rectangle((7, 9, 8, 14), fill=4)
        d.line((6, 14, 10, 14), fill=6)
        d.polygon([(3, 4), (7, 1), (11, 3), (12, 9), (9, 12), (4, 10)], fill=1)
        d.polygon([(4, 4), (7, 2), (10, 4), (10, 9), (5, 9)], fill=5)
        d.rectangle((5, 5, 9, 8), fill=2)
        d.rectangle((6, 5, 8, 8), fill=7)
        d.point((6 if phase else 7, 5), fill=15)
        d.line((4, 4, 10, 4), fill=8)
        d.line((5, 10, 9, 10), fill=6)
    elif kind == 'shrine':
        _base(d)
        d.rectangle((2, 11, 13, 14), fill=3)
        d.line((2, 11, 13, 11), fill=7)
        d.rectangle((4, 8, 11, 10), fill=5)
        d.polygon([(4, 8), (4, 4), (7, 1), (10, 3), (11, 8)], fill=1)
        d.polygon([(5, 7), (5, 4), (7, 2), (9, 4), (10, 7)], fill=6)
        d.line((6, 4, 8, 3), fill=8)
        d.rectangle((7, 5, 8, 7), fill=2)
        d.point((7, 5), fill=15)
    elif kind == 'switch':
        # Full-cell grounded plate, before and after pressing; no tiny button.
        d.polygon([(0, 4), (3, 1), (12, 1), (15, 4), (15, 14), (0, 14)], fill=1)
        d.polygon([(1, 4), (4, 2), (11, 2), (14, 4), (14, 11), (1, 11)], fill=5)
        d.line((2, 4, 12, 4), fill=8)
        d.line((1, 12, 14, 12), fill=3)
        d.rectangle((3, 5, 12, 10), fill=2)
        d.rectangle((4, 6 if phase else 5, 11, 10 if phase else 9), fill=10 if phase else 6)
        d.line((5, 7 if phase else 5, 10, 7 if phase else 5), fill=11 if phase else 8)
        d.rectangle((6, 7 if not phase else 8, 9, 8 if not phase else 9), fill=4 if not phase else 9)
    elif kind == 'trial':
        _base(d)
        d.rectangle((3, 11, 12, 13), fill=5)
        d.line((3, 11, 12, 11), fill=8)
        d.polygon([(5, 10), (4, 5), (7, 1), (10, 1), (12, 5), (10, 10)], fill=1)
        d.polygon([(6, 9), (5, 5), (8, 2), (10, 5), (9, 9)], fill=6)
        d.line((6, 5, 8, 3), fill=8)
        d.line((8, 5, 8, 8), fill=15)
    elif kind == 'cache':
        _base(d)
        d.polygon([(2, 12), (2, 8), (6, 5), (11, 5), (14, 9), (13, 13)], fill=1)
        d.polygon([(3, 10), (4, 7), (7, 6), (11, 7), (12, 10)], fill=5)
        d.line((4, 8, 8, 6), fill=8)
        d.line((3, 11, 12, 11), fill=6)
        d.rectangle((7, 9, 9, 12), fill=7)
        d.point((8, 10), fill=1)
    elif kind == 'ward':
        # Brass braced barrier: obvious solid gate and central sealed heart.
        d.polygon([(0, 15), (1, 3), (4, 0), (12, 0), (15, 3), (15, 15)], fill=1)
        for x in (2, 12):
            d.rectangle((x, 3, x+1, 14), fill=5)
            d.line((x, 3, x, 12), fill=8)
        d.line((3, 3, 12, 3), fill=6, width=2)
        d.line((3, 12, 12, 12), fill=6)
        d.line((4, 5, 11, 10), fill=5, width=2)
        d.line((11, 5, 4, 10), fill=5, width=2)
        d.rectangle((6, 5, 9, 10), fill=1)
        d.rectangle((7, 6, 8, 9), fill=13)
        d.point((7, 6), fill=15)
    elif kind == 'thorn':
        _base(d)
        d.line([(2, 14), (4, 9), (3, 3), (7, 7), (10, 2), (10, 10), (14, 6), (13, 14)], fill=1, width=3)
        d.line([(3, 13), (5, 9), (4, 5), (7, 8), (9, 5), (10, 12), (13, 9)], fill=12, width=2)
        d.line((5, 9, 6, 11), fill=13)
        d.point((9, 5), fill=14)
    elif kind == 'web':
        # Dry silk bridge across the whole tile, with a big central opening.
        for a, b in (((0, 0), (15, 15)), ((15, 0), (0, 15)), ((7, 0), (7, 15)), ((0, 7), (15, 7))):
            d.line((a, b), fill=3, width=3)
            d.line((a, b), fill=7)
        d.polygon([(4, 4), (10, 3), (13, 7), (11, 12), (4, 12), (2, 8)], outline=6)
        d.line((4, 4, 7, 3), fill=8)
        d.line((2, 8, 4, 12), fill=5)
    elif kind == 'crack':
        # One unmistakable broad black fracture with offset pale curd plates.
        d.polygon([(0, 15), (0, 5), (4, 1), (11, 1), (15, 5), (15, 15)], fill=1)
        d.polygon([(1, 13), (2, 5), (5, 2), (8, 2), (6, 6), (8, 8), (5, 13)], fill=5)
        d.polygon([(10, 2), (13, 5), (14, 13), (8, 13), (10, 9), (8, 6)], fill=4)
        d.line([(2, 5), (5, 3), (7, 3)], fill=8)
        d.line([(9, 4), (8, 6), (10, 8), (7, 12), (8, 14)], fill=2)
        d.line((2, 14, 13, 14), fill=3)
    return im


def chest(opened=False):
    """A 22px-wide brass-banded curdwood coffer, with a full contact shadow."""
    im, d = _canvas(0, (32, 32))
    d.ellipse((4, 25, 29, 31), fill=1)
    d.polygon([(5, 13), (8, 8), (22, 8), (26, 12), (26, 27),
               (22, 29), (8, 28), (5, 25)], fill=1)
    d.rectangle((6, 15, 25, 25), fill=3)
    d.rectangle((7, 16, 23, 24), fill=4)
    d.polygon([(24, 15), (25, 14), (25, 25), (23, 27), (23, 17)], fill=2)
    d.line((7, 25, 23, 25), fill=5)
    d.line((8, 27, 22, 27), fill=6)
    if opened:
        d.polygon([(5, 13), (5, 5), (9, 2), (22, 2), (26, 6), (26, 14)], fill=1)
        d.polygon([(7, 6), (10, 4), (21, 4), (24, 7), (24, 11), (7, 11)], fill=5)
        d.line((8, 5, 21, 5), fill=8)
        d.rectangle((8, 7, 22, 10), fill=3)
        d.rectangle((7, 13, 24, 18), fill=1)
        d.line((8, 18, 23, 18), fill=6)
    else:
        d.polygon([(6, 13), (8, 9), (11, 7), (21, 7), (25, 10), (26, 14)], fill=5)
        d.polygon([(8, 11), (11, 8), (20, 8), (23, 10), (24, 12)], fill=6)
        d.line((10, 8, 20, 8), fill=8)
        d.line((6, 14, 25, 14), fill=7)
        d.line((7, 15, 24, 15), fill=1)
    for x in (9, 21):
        d.rectangle((x, 10 if not opened else 7, x+2, 26), fill=6)
        d.line((x, 10 if not opened else 7, x, 25), fill=8)
        d.line((x+2, 17, x+2, 25), fill=4)
    d.rectangle((14, 17, 18, 22), fill=1)
    d.rectangle((15, 18, 17, 21), fill=7)
    if not opened:
        d.point((16, 19), fill=1)
        d.point((16, 20), fill=1)
    d.point((10, 10 if not opened else 7), fill=15)
    return im


def pit(stage=0):
    im = floor(stage)
    d = ImageDraw.Draw(im)
    d.polygon([(0, 7), (2, 3), (6, 1), (12, 2), (15, 6),
               (15, 12), (12, 15), (3, 15), (0, 12)], fill=2)
    d.polygon([(1, 7), (3, 4), (6, 3), (12, 4), (14, 7),
               (13, 12), (10, 14), (4, 13), (1, 11)], fill=1)
    d.line([(2, 5), (5, 2), (11, 3)], fill=7)
    d.line([(2, 12), (5, 14), (11, 14)], fill=3)
    return im
