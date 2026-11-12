"""Moldglass Crags: original native-pixel optional Cream environment study.

Broken olive/teal glass coats ivory limestone. Quiet matte walking ground,
deep undercuts, and gilt climbing grips have deliberately different values.
All drawings are authored on their final indexed GBA canvas; no resampling.
This module supplies art only, never tile identifiers or collision changes.
"""
from PIL import Image, ImageDraw


PALETTES = {
    'cream_floor0': ['#000000', '#182020', '#606858', '#909080', '#c0c0a8', '#a8b098', '#d0d0b8', '#e0e0c8', '#f0e8d0', '#606850', '#809080', '#b0c0a8', '#384840', '#587868', '#a8c8b8', '#e8d098'],
    'cream_floor1': ['#000000', '#181820', '#586058', '#888878', '#b8b8a0', '#a0a890', '#c8c8b0', '#d8d8c0', '#e8e0c8', '#586048', '#788068', '#a8b898', '#383040', '#685068', '#a878b0', '#e0c890'],
    'cream_floor2': ['#000000', '#101018', '#505850', '#808078', '#b0b0a0', '#98a090', '#c0c0b0', '#d0d0c0', '#e0d8c0', '#485848', '#687868', '#98b0a0', '#282030', '#604070', '#a060c0', '#d8c088'],
    'cream_cliff0': ['#000000', '#101818', '#203830', '#385850', '#607860', '#809878', '#b0b890', '#d8d8b0', '#f0e8c8', '#484830', '#788850', '#b0c0a0', '#284848', '#588878', '#a0c8b0', '#e8d090'],
    'cream_cliff1': ['#000000', '#101818', '#203030', '#385048', '#586850', '#788860', '#a8b080', '#d0d0a0', '#e8e0b8', '#404028', '#708048', '#a0b890', '#302038', '#785088', '#c088d8', '#e0c880'],
    'cream_cliff2': ['#000000', '#080810', '#182020', '#283830', '#405848', '#607860', '#90a078', '#b8c098', '#e0d8b0', '#303820', '#587048', '#88a888', '#201028', '#703888', '#c070e8', '#d8c078'],
    'cream_water': ['#000000', '#101818', '#183830', '#285048', '#386860', '#588878', '#88b0a0', '#b0d0b8', '#e0e8c8', '#384830', '#607850', '#90a878', '#282038', '#683880', '#b070d8', '#e8d090'],
    'cream_props': ['#000000', '#101818', '#283830', '#485040', '#687058', '#889068', '#b0b890', '#d8d8b0', '#f0e8c8', '#284840', '#507868', '#90b8a0', '#281830', '#784090', '#c878e8', '#e8c878'],
}


def _new(size=(16, 16), fill=0, palette='cream_props'):
    im = Image.new('P', size, fill)
    rgb = [int(c[i:i + 2], 16) for c in PALETTES[palette] for i in (1, 3, 5)]
    im.putpalette(rgb + [0] * (768 - len(rgb)))
    return im, ImageDraw.Draw(im)


def _poly(d, points, fill, light=None, edge=None):
    """One faceted shard: a broad plane, one lit edge, one far-side cut."""
    d.polygon(points, fill=fill)
    if light is not None:
        d.line(points[:3], fill=light)
    if edge is not None:
        d.line(points[2:] + points[:1], fill=edge)


def floor(stage=0, variant=0, path=False):
    stage = max(0, min(2, stage))
    im, d = _new(fill=4, palette='cream_floor%d' % stage)
    # Broad low-contrast limestone scuffs, never a decorative grid or a hole.
    v = variant % 4
    if v == 0:
        d.polygon([(0, 11), (5, 10), (9, 11), (7, 13), (0, 13)], fill=5)
        d.line([(0, 10), (4, 9), (7, 10)], fill=6)
    elif v == 1:
        d.polygon([(8, 2), (13, 1), (15, 2), (15, 4), (10, 4)], fill=5)
        d.line([(9, 1), (12, 0), (15, 1)], fill=6)
        d.line([(2, 12), (4, 12), (6, 11)], fill=5)
    elif v == 2:
        d.polygon([(3, 5), (7, 4), (12, 5), (10, 6), (5, 6)], fill=6)
        d.line([(7, 7), (11, 7), (13, 6)], fill=5)
    else:
        d.polygon([(1, 3), (5, 2), (8, 3), (6, 4), (1, 4)], fill=5)
        d.line([(3, 1), (6, 1), (8, 2)], fill=6)
        d.polygon([(10, 11), (13, 9), (15, 10), (15, 12), (12, 13)], fill=5)
        if stage:
            # Attached, narrow stain on one variant; the route stays neutral.
            d.line([(13, 9), (12, 10), (13, 11), (15, 11)], fill=10)
            if stage == 2:
                d.line([(14, 10), (13, 11), (15, 12)], fill=13)
    if path:
        d.line([(4, 8), (7, 7), (11, 7)], fill=6)
        d.line([(6, 9), (9, 9)], fill=5)
    return im


def cliff(stage=0, kind='mid', variant=0):
    stage = max(0, min(2, stage))
    im, d = _new(fill=3, palette='cream_cliff%d' % stage)
    v = variant % 2
    # The same subdued boundary values run through adjacent variants. Each
    # interior contains unequal glass planes separated by deep damp cavities.
    d.rectangle((0, 5, 15, 6), fill=2)
    d.rectangle((0, 13, 15, 15), fill=2)
    if not v:
        _poly(d, [(0, 0), (9, 0), (12, 2), (8, 5), (0, 4)], 4, 6, 2)
        d.polygon([(0, 1), (7, 1), (9, 2), (4, 3), (0, 3)], fill=5)
        d.line([(0, 0), (6, 0), (9, 1)], fill=11)
        _poly(d, [(13, 0), (15, 0), (15, 5), (10, 5)], 5, 11, 2)
        d.polygon([(0, 8), (5, 6), (11, 7), (14, 10), (9, 13), (0, 12)], fill=1)
        _poly(d, [(0, 7), (6, 6), (12, 8), (8, 11), (0, 10)], 4, 6, 2)
        d.polygon([(1, 8), (6, 7), (9, 8), (5, 9), (1, 9)], fill=5)
        _poly(d, [(11, 8), (15, 7), (15, 12), (9, 13)], 3, 5, 1)
        d.line([(1, 13), (5, 12), (8, 13)], fill=10)
    else:
        _poly(d, [(0, 0), (4, 0), (8, 3), (5, 5), (0, 4)], 4, 6, 2)
        _poly(d, [(6, 0), (15, 0), (15, 4), (10, 5), (8, 3)], 5, 11, 2)
        d.polygon([(7, 1), (12, 1), (14, 2), (10, 3)], fill=6)
        d.polygon([(0, 8), (8, 6), (14, 8), (15, 13), (0, 13)], fill=1)
        _poly(d, [(0, 7), (3, 6), (8, 8), (5, 11), (0, 10)], 4, 6, 2)
        _poly(d, [(7, 7), (13, 6), (15, 7), (15, 12), (10, 11)], 4, 6, 2)
        d.polygon([(9, 8), (13, 7), (14, 8), (12, 10)], fill=5)
        d.line([(0, 14), (4, 13), (7, 14)], fill=10)
    # Tiny mineral glints are attached to broad material clusters.
    d.line((2 if not v else 10, 1, 3 if not v else 11, 1), fill=14 if not stage else 11)
    if v == 0:
        d.point((5, 7), fill=15)
    if stage:
        # Damage removes glass plates, exposing black seams and purple light.
        d.polygon([(9, 3), (12, 2), (11, 5), (8, 7), (10, 9), (7, 12), (7, 15), (5, 15), (6, 11), (8, 9), (6, 7), (9, 5)], fill=1)
        d.line([(11, 3), (10, 5), (7, 7), (9, 9), (6, 12), (6, 15)], fill=12, width=2)
        d.line([(10, 4), (10, 5), (7, 7), (9, 9), (6, 12)], fill=13)
        if stage == 2:
            d.polygon([(1, 8), (5, 7), (5, 9), (3, 10), (4, 12), (1, 13)], fill=1)
            d.line([(1, 8), (3, 8), (3, 9)], fill=13)
            d.line([(10, 5), (8, 6)], fill=14)
            d.line([(7, 10), (6, 11)], fill=14)
    if kind == 'top':
        d.polygon([(0, 0), (15, 0), (15, 2), (11, 2), (9, 3), (5, 2), (2, 3), (0, 2)], fill=7)
        d.line([(0, 0), (7, 0), (9, 1), (15, 1)], fill=8)
        d.line([(0, 3), (3, 4), (6, 3), (9, 4), (12, 3), (15, 3)], fill=1)
        d.line([(1, 1), (4, 1)], fill=15)
    elif kind in ('base', 'bottom'):
        d.polygon([(0, 11), (4, 12), (7, 11), (10, 13), (13, 12), (15, 12), (15, 15), (0, 15)], fill=1)
        d.line([(0, 15), (4, 14), (8, 15), (15, 15)], fill=2)
        d.line([(1, 11), (4, 12)], fill=5)
    elif kind == 'left':
        d.polygon([(0, 0), (2, 0), (3, 4), (2, 8), (3, 12), (2, 15), (0, 15)], fill=7)
        d.line([(0, 0), (1, 4), (0, 8), (1, 12), (0, 15)], fill=8)
        d.line([(3, 0), (4, 4), (3, 8), (4, 12), (3, 15)], fill=2)
    elif kind == 'right':
        d.polygon([(13, 0), (15, 0), (15, 15), (13, 15), (12, 11), (13, 7), (12, 3)], fill=1)
        d.line([(12, 0), (11, 4), (12, 8), (11, 12), (12, 15)], fill=4)
    return im


def climb(stage=0, kind='mid'):
    im = cliff(stage, 'mid', 0)
    d = ImageDraw.Draw(im)
    # Gilt limestone grip pairs, not the ordinary glass's diagonal facets.
    # The exterior edge stays identical for two-wide repetition and the
    # channel/rail reaches both vertical boundaries without phase changes.
    d.rectangle((3, 0, 12, 15), fill=1)
    d.line((3, 0, 3, 15), fill=2)
    d.line((12, 0, 12, 15), fill=4)
    d.line((4, 0, 4, 15), fill=6)
    d.line((11, 0, 11, 15), fill=3)
    for y in (3, 11):
        d.rectangle((4, y, 11, y + 2), fill=1)
        d.rectangle((4, y - 1, 7, y), fill=15)
        d.rectangle((9, y - 1, 11, y), fill=7)
        d.line((4, y - 1, 6, y - 1), fill=8)
        d.line((9, y - 1, 10, y - 1), fill=8)
        d.point((7, y + 1), fill=6)
    if kind == 'top':
        d.rectangle((0, 0, 15, 1), fill=7)
        d.line((0, 0, 15, 0), fill=8)
        d.rectangle((5, 1, 10, 2), fill=1)
    elif kind in ('base', 'bottom'):
        d.rectangle((2, 14, 13, 15), fill=1)
        d.line((4, 14, 11, 14), fill=15)
        d.line((4, 15, 7, 15), fill=7)
    return im


def rim(stage=0, variant=0, drop=False):
    im = floor(stage, variant)
    d = ImageDraw.Draw(im)
    # An ivory near lip above a dark vertical recess establishes elevation.
    d.polygon([(0, 11), (4, 11), (6, 10), (10, 10), (13, 11), (15, 11), (15, 15), (0, 15)], fill=2)
    d.line([(0, 10), (4, 10), (6, 9), (10, 9), (13, 10), (15, 10)], fill=8)
    d.line([(0, 11), (4, 11), (6, 10), (10, 10), (13, 11), (15, 11)], fill=6)
    d.line([(1, 13), (4, 13), (6, 12)], fill=3)
    if drop:
        # Wide uninterrupted landing edge; three pale descending chips cue
        # a deliberate drop without borrowing the climb grip pattern.
        d.rectangle((4, 9, 11, 10), fill=7)
        d.line((5, 9, 10, 9), fill=8)
        d.line((6, 12, 9, 12), fill=6)
        d.line((7, 14, 8, 14), fill=5)
    else:
        # Sharp rooted glass teeth mark an obstructed ledge silhouette.
        d.polygon([(0, 11), (1, 6), (4, 4), (6, 9), (5, 11)], fill=2)
        d.polygon([(1, 9), (2, 6), (4, 5), (4, 9)], fill=10)
        d.line([(2, 6), (4, 5)], fill=14 if not stage else 11)
        d.polygon([(9, 10), (10, 6), (13, 3), (15, 8), (15, 11)], fill=2)
        d.polygon([(10, 9), (11, 6), (13, 4), (13, 9)], fill=10)
        d.line([(11, 6), (13, 4)], fill=11)
        if stage == 2:
            d.line([(13, 6), (14, 8), (13, 10)], fill=13)
    return im


def cave(stage=0):
    stage = max(0, min(2, stage))
    im, d = _new((32, 48), palette='cream_cliff%d' % stage)
    # Asymmetric overhung mineral cleft, not a regular architectural arch.
    d.polygon([(0, 47), (0, 22), (3, 12), (8, 7), (10, 3), (20, 2), (27, 8), (29, 16), (31, 20), (31, 47)], fill=1)
    d.polygon([(1, 44), (2, 21), (5, 13), (9, 9), (12, 5), (20, 4), (25, 9), (28, 19), (30, 23), (29, 45)], fill=4)
    _poly(d, [(3, 18), (7, 10), (12, 7), (19, 5), (23, 8), (15, 12), (9, 19)], 5, 7, 2)
    d.line([(5, 14), (8, 10), (12, 8), (18, 6)], fill=8)
    _poly(d, [(1, 26), (4, 20), (9, 18), (8, 28), (3, 33), (1, 31)], 4, 6, 2)
    _poly(d, [(23, 13), (27, 17), (30, 23), (29, 35), (25, 30), (22, 23)], 3, 5, 1)
    _poly(d, [(2, 36), (7, 31), (9, 34), (7, 44), (1, 46)], 5, 6, 2)
    d.polygon([(8, 47), (8, 27), (11, 20), (15, 16), (20, 15), (23, 21), (25, 28), (25, 47)], fill=1)
    d.polygon([(8, 27), (11, 20), (15, 16), (20, 15), (18, 20), (13, 23), (10, 29)], fill=2)
    d.line([(10, 25), (12, 21), (15, 18)], fill=3)
    d.polygon([(25, 30), (29, 34), (28, 44), (25, 47), (23, 44)], fill=2)
    d.rectangle((9, 43, 24, 47), fill=2)
    d.line([(5, 46), (9, 45), (23, 45), (27, 46)], fill=7)
    d.line((10, 47, 23, 47), fill=6)
    d.line((9, 11, 11, 10), fill=15)
    if stage:
        d.polygon([(22, 5), (25, 9), (24, 15), (27, 22), (26, 29), (29, 34), (27, 42), (25, 39), (26, 34), (23, 28), (24, 22), (21, 15)], fill=1)
        d.line([(23, 8), (22, 15), (25, 22), (24, 28), (27, 34), (26, 40)], fill=13, width=1)
        if stage == 2:
            d.line([(24, 20), (25, 22), (24, 24)], fill=14)
            d.line([(26, 33), (27, 34), (26, 36)], fill=14)
    return im


def water(stage=0, phase=0, fall=False):
    p = phase % 2
    im, d = _new(fill=3, palette='cream_water')
    if fall:
        d.rectangle((0, 0, 2, 15), fill=1)
        d.rectangle((13, 0, 15, 15), fill=2)
        d.rectangle((4, 0, 6, 15), fill=5)
        d.line((4, 0, 4, 15), fill=7)
        d.line((10, 0, 10, 15), fill=4)
        for y in (1 + 3 * p, 9 + 3 * p):
            d.line((7, y, 8, y + 3), fill=6)
            d.line((11, y + 2, 11, y + 4), fill=5)
        d.line((3, 15, 6, 15), fill=6)
    else:
        # Reflections are long grouped strokes on a coherent dark teal body.
        d.line([(0, 3), (3, 3), (5, 2), (8, 2)], fill=4)
        d.line([(10, 10), (13, 10), (15, 9)], fill=4)
        d.line((2 + p, 5, 6 + p, 5), fill=6)
        d.line((3 + p, 6, 8 + p, 6), fill=4)
        d.line((10 - p, 12, 13 - p, 12), fill=5)
    if stage:
        d.line((9, 8 + p, 12, 8 + p), fill=12 if stage == 1 else 13)
        if stage == 2:
            d.point((10, 8 + p), fill=14)
    return im


def prop(kind='mold', stage=0, phase=0):
    im, d = _new()
    if kind == 'mold':
        d.polygon([(1, 13), (4, 10), (11, 10), (15, 13), (13, 15), (3, 15)], fill=1)
        for pts in ([(2, 11), (3, 7), (6, 4), (8, 8), (6, 12)], [(7, 12), (8, 5), (11, 2), (13, 8), (12, 12)], [(11, 13), (13, 9), (15, 10), (14, 14)]):
            _poly(d, pts, 9 if stage < 2 else 12, 10 if stage < 2 else 13, 1)
        d.line([(4, 7), (6, 5), (6, 8)], fill=11)
        d.line([(9, 6), (11, 3), (11, 7)], fill=11 if stage < 2 else 14)
        d.point((5, 6), fill=15)
    elif kind == 'lamp':
        # A physical brass cage and one local light source, no ambient halo.
        d.ellipse((3, 12, 13, 15), fill=1)
        d.rectangle((7, 9, 9, 13), fill=3)
        d.line((7, 10, 7, 13), fill=6)
        d.polygon([(3, 4), (6, 1), (10, 1), (13, 4), (12, 10), (4, 10)], fill=1)
        d.rectangle((5, 4, 10, 8), fill=5)
        d.rectangle((6, 4, 9, 7), fill=15 if phase else 7)
        d.line((7, 4, 7, 7), fill=8)
        d.line((4, 3, 11, 3), fill=6)
        d.line((5, 9, 11, 9), fill=6)
        d.line((10, 4, 10, 8), fill=3)
    elif kind == 'shrine':
        d.polygon([(1, 12), (4, 9), (12, 9), (15, 12), (13, 15), (2, 15)], fill=1)
        d.polygon([(2, 11), (5, 9), (11, 9), (14, 11), (11, 13), (5, 13)], fill=5)
        d.line((4, 10, 11, 10), fill=7)
        d.polygon([(5, 9), (5, 4), (8, 1), (11, 4), (10, 10)], fill=1)
        d.polygon([(6, 8), (6, 4), (8, 2), (9, 4), (9, 8)], fill=10)
        d.line([(6, 4), (8, 2)], fill=8)
        d.line((7, 5, 7, 7), fill=15 if not phase else 5)
    elif kind == 'switch':
        # Broad plate occupies almost the full cell; state changes its height.
        d.polygon([(0, 7), (3, 3), (12, 3), (15, 7), (15, 13), (12, 15), (2, 15), (0, 12)], fill=1)
        d.polygon([(1, 7), (4, 4), (11, 4), (14, 7), (13, 12), (3, 12)], fill=3)
        y = 7 if phase else 5
        d.polygon([(2, y + 2), (4, y), (11, y), (13, y + 2), (11, y + 5), (4, y + 5)], fill=10 if phase else 6)
        d.line((4, y, 10, y), fill=11 if phase else 8)
        d.line((4, y + 5, 11, y + 5), fill=9 if phase else 4)
        d.line((1, 13, 13, 13), fill=2)
    elif kind == 'trial':
        d.ellipse((1, 12, 14, 15), fill=1)
        d.polygon([(3, 11), (5, 9), (11, 9), (13, 11), (11, 13), (4, 13)], fill=5)
        d.line((4, 11, 11, 11), fill=15)
        # Two separated glass prongs frame one small sacred gilt bead.
        d.polygon([(4, 10), (3, 4), (6, 1), (6, 8)], fill=1)
        d.line([(4, 8), (4, 4), (6, 2)], fill=11)
        d.polygon([(10, 10), (10, 3), (12, 1), (13, 7)], fill=1)
        d.line([(11, 8), (11, 4), (12, 2)], fill=10)
        d.rectangle((7, 5, 8, 7), fill=15)
        d.point((7, 5), fill=8)
    elif kind == 'cache':
        d.ellipse((1, 11, 14, 15), fill=1)
        for x, y in ((2, 9), (7, 6), (9, 11)):
            d.polygon([(x, y + 2), (x + 1, y), (x + 5, y), (x + 5, y + 3), (x + 3, y + 4), (x, y + 4)], fill=3)
            d.line((x + 1, y, x + 4, y), fill=15)
            d.line((x, y + 1, x + 3, y + 1), fill=7)
            d.line((x + 4, y + 1, x + 4, y + 2), fill=5)
    elif kind == 'ward':
        d.polygon([(1, 15), (1, 5), (5, 1), (11, 1), (14, 5), (14, 15)], fill=1)
        d.polygon([(2, 13), (2, 5), (6, 2), (10, 2), (13, 5), (13, 13)], fill=10)
        d.line([(3, 6), (6, 3), (10, 3)], fill=11)
        # Exactly one large, high-contrast keyhole and no decorative holes.
        d.ellipse((5, 4, 10, 9), fill=15)
        d.polygon([(6, 8), (9, 8), (10, 12), (5, 12)], fill=15)
        d.ellipse((6, 5, 9, 8), fill=1)
        d.rectangle((7, 8, 8, 11), fill=1)
        d.line((3, 14, 12, 14), fill=3)
    elif kind == 'thorn':
        d.ellipse((0, 12, 15, 15), fill=1)
        for pts in ([(1, 14), (4, 9), (3, 3), (7, 7), (9, 1)], [(7, 14), (10, 9), (14, 5), (13, 11), (15, 12)]):
            d.line(pts, fill=1, width=3)
            d.line(pts, fill=9 if stage < 2 else 12)
        d.line([(3, 4), (5, 7), (4, 10)], fill=11 if not stage else 13)
        d.line([(10, 9), (13, 6)], fill=10 if stage < 2 else 14)
        d.point((9, 1), fill=7 if stage < 2 else 14)
    elif kind == 'web':
        # Connected pale fibres with dark undersides, visibly burnable silk.
        strands = [[(1, 1), (7, 7), (14, 14)], [(14, 1), (8, 7), (1, 14)], [(7, 0), (8, 15)], [(0, 8), (15, 7)]]
        for pts in strands:
            d.line([(x + 1, y) for x, y in pts], fill=2)
            d.line(pts, fill=8)
        d.line([(4, 4), (10, 4), (12, 8), (10, 11), (5, 12), (3, 8), (4, 4)], fill=6)
        d.line([(6, 6), (9, 6), (10, 8), (8, 10), (6, 9), (5, 7)], fill=7)
    elif kind == 'crack':
        d.polygon([(0, 15), (0, 7), (4, 2), (10, 1), (15, 6), (15, 15)], fill=1)
        d.polygon([(1, 12), (2, 7), (5, 3), (10, 2), (14, 6), (13, 13)], fill=5)
        d.polygon([(2, 7), (5, 3), (9, 3), (7, 6)], fill=7)
        d.line([(9, 3), (7, 7), (10, 9), (7, 13), (7, 15)], fill=1, width=2)
        d.line([(7, 7), (3, 8), (2, 10)], fill=1)
        d.line([(8, 8), (12, 6), (14, 7)], fill=1)
        d.line([(9, 4), (8, 6)], fill=8)
        d.line([(10, 10), (8, 13)], fill=7)
        d.line((3, 6, 5, 4), fill=8)
    return im


def chest(opened=False):
    im, d = _new((32, 32))
    # Twenty-two-pixel body, brass bindings, dark floor contact, bright latch.
    d.ellipse((3, 26, 29, 31), fill=1)
    d.polygon([(5, 14), (8, 10), (23, 10), (26, 14), (26, 27), (23, 29), (7, 29), (5, 27)], fill=1)
    d.rectangle((6, 17, 25, 26), fill=3)
    d.rectangle((8, 18, 22, 26), fill=4)
    d.line((8, 25, 23, 25), fill=5)
    d.line((6, 27, 24, 27), fill=6)
    for x in (12, 18):
        d.line((x, 19, x, 25), fill=3)
    if opened:
        d.polygon([(5, 15), (5, 6), (8, 3), (23, 3), (26, 7), (26, 15)], fill=1)
        d.polygon([(7, 12), (7, 7), (10, 5), (22, 5), (24, 8), (24, 12)], fill=5)
        d.line((9, 5, 22, 5), fill=8)
        d.line((8, 12, 23, 12), fill=6)
        d.rectangle((7, 15, 24, 19), fill=1)
        d.line((8, 20, 23, 20), fill=5)
    else:
        d.polygon([(5, 15), (7, 11), (11, 8), (21, 8), (25, 11), (26, 15)], fill=5)
        d.polygon([(8, 12), (12, 9), (20, 9), (23, 12)], fill=6)
        d.line((11, 9, 20, 9), fill=8)
        d.line((6, 15, 25, 15), fill=7)
        d.line((6, 16, 25, 16), fill=1)
    for x in (8, 22):
        d.rectangle((x, 11 if not opened else 7, x + 1, 27), fill=6)
        d.line((x, 12 if not opened else 8, x, 25), fill=15)
        d.point((x, 23), fill=8)
    d.rectangle((14, 18, 18, 23), fill=1)
    d.rectangle((15, 18, 17, 21), fill=15 if not opened else 5)
    d.line((15, 18, 17, 18), fill=8)
    if not opened:
        d.point((16, 20), fill=1)
    return im


def pit(stage=0):
    im = floor(stage, 0)
    d = ImageDraw.Draw(im)
    d.polygon([(0, 6), (3, 2), (11, 1), (15, 5), (15, 13), (12, 15), (2, 15), (0, 12)], fill=2)
    d.polygon([(1, 7), (4, 4), (11, 3), (14, 6), (14, 13), (11, 15), (3, 15), (1, 12)], fill=1)
    d.line([(1, 5), (4, 2), (10, 2)], fill=7)
    d.line([(3, 4), (8, 3), (11, 4)], fill=3)
    d.line([(3, 15), (7, 14), (12, 14)], fill=3)
    if stage == 2:
        d.line([(12, 5), (13, 7), (12, 8)], fill=13)
        d.point((13, 7), fill=14)
    return im
