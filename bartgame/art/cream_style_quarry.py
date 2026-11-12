"""GILT QUARRY — optional native Curdled Cream environment study.

Broad quarried curdstone slabs, cool undercuts, worn tracks, timber climbing
braces and weathered bronze.  This is a source-art alternative, not an adopted
shared style.  All pixels are authored on their final indexed GBA canvases.
"""
from PIL import Image, ImageDraw


PALETTES = {
    'cream_floor0': ['#000000', '#282830', '#505050', '#a08858',
                     '#b8a878', '#c8b888', '#d8c898', '#e8d8b0',
                     '#f8f0d0', '#605840', '#887048', '#a89060',
                     '#384838', '#586848', '#889860', '#f8f0d8'],
    'cream_floor1': ['#000000', '#282830', '#484848', '#908058',
                     '#b0a078', '#c0b088', '#d0c098', '#e0d0a8',
                     '#f0e8c8', '#585038', '#786840', '#988858',
                     '#384030', '#586040', '#889050', '#f0e8d0'],
    'cream_floor2': ['#000000', '#181820', '#383838', '#807860',
                     '#a8a080', '#b8b090', '#c8c0a0', '#d8d0b0',
                     '#e8e0c8', '#484038', '#686048', '#908060',
                     '#302030', '#783088', '#c848e0', '#f8d8f8'],
    'cream_cliff0': ['#000000', '#202830', '#384048', '#685838',
                     '#a08858', '#b8a068', '#d0b880', '#e8d0a0',
                     '#f8e8c0', '#384038', '#586048', '#889060',
                     '#384838', '#607050', '#98a868', '#f8f0d8'],
    'cream_cliff1': ['#000000', '#202028', '#303840', '#585038',
                     '#887850', '#a09060', '#b8a878', '#d0c090',
                     '#e8d8b0', '#303830', '#505840', '#788050',
                     '#403040', '#685048', '#988060', '#f0e0c8'],
    'cream_cliff2': ['#000000', '#101820', '#202830', '#383838',
                     '#605848', '#887850', '#a89870', '#c0b088',
                     '#e0d0a8', '#202828', '#384038', '#686848',
                     '#302038', '#782890', '#d848f0', '#f8e0f8'],
    'cream_water': ['#000000', '#182830', '#304038', '#485840',
                    '#607050', '#809060', '#a8b880', '#d0d8a8',
                    '#f0e8c0', '#304038', '#486050', '#709070',
                    '#302038', '#702888', '#c840e0', '#f0c8f0'],
    'cream_props': ['#000000', '#202830', '#384040', '#584830',
                    '#806038', '#a88048', '#c8a860', '#e8c888',
                    '#f8e8b8', '#304038', '#506848', '#889860',
                    '#302038', '#782888', '#d048e8', '#f8e0f8'],
}


def _stage(stage):
    return max(0, min(2, int(stage)))


def _new(bank, fill=0, size=(16, 16)):
    image = Image.new('P', size, fill)
    colors = [int(c[k:k + 2], 16) for c in PALETTES[bank]
              for k in (1, 3, 5)]
    image.putpalette(colors + [0] * (768 - len(colors)))
    return image, ImageDraw.Draw(image)


def floor(stage=0, variant=0, path=False):
    """Quiet quarry dust; broad wear patches instead of a patterned tile grid."""
    stage = _stage(stage)
    variant = int(variant) % 4
    image, d = _new('cream_floor%d' % stage, 4)
    if path:
        # These broad close-valued areas merge into an abraded dusty route.
        shapes = (
            [(0, 4), (6, 3), (12, 4), (15, 6), (15, 12), (7, 13), (0, 11)],
            [(0, 5), (5, 4), (11, 5), (15, 4), (15, 11), (9, 12), (0, 12)],
            [(0, 3), (8, 4), (15, 3), (15, 11), (11, 13), (3, 12), (0, 10)],
            [(0, 5), (5, 3), (13, 3), (15, 5), (15, 12), (6, 11), (0, 12)],
        )
        d.polygon(shapes[variant], fill=5)
        if variant == 1:
            d.line((3, 11, 7, 11), fill=4)
        elif variant == 3:
            d.line((9, 4, 13, 4), fill=6)
    elif variant == 1:
        d.polygon([(1, 11), (3, 10), (6, 10), (7, 11), (3, 12)], fill=3)
        d.line((2, 12, 5, 12), fill=5)
    elif variant == 2:
        d.polygon([(10, 3), (13, 3), (14, 4), (11, 5), (9, 4)], fill=5)
        d.line((10, 5, 12, 5), fill=3)
    elif variant == 3:
        d.line([(3, 5), (5, 4), (8, 4)], fill=3)
        d.line((4, 6, 7, 5), fill=5)
    if stage and variant == 3:
        # Mold stays attached to a single depressed seam.
        d.polygon([(11, 11), (15, 10), (15, 14), (13, 13), (11, 14)], fill=12)
        d.line([(12, 12), (14, 11), (15, 11)], fill=13)
        if stage == 2:
            d.line([(13, 12), (14, 12), (15, 11)], fill=14)
    return image


def cliff(stage=0, kind='mid', variant=0):
    """Projecting horizontal quarry slabs with shared repeat-edge heights."""
    stage = _stage(stage)
    variant = int(variant) % 2
    image, d = _new('cream_cliff%d' % stage, 4)
    # One broad cut block per row.  The four-pixel cool recess is the deep
    # cast shadow beneath a projecting ledge, not an outline around each tile.
    d.polygon([(0, 0), (15, 0), (15, 8), (12, 9), (8, 9),
               (6, 10), (2, 9), (0, 8)], fill=5)
    d.polygon([(0, 0), (15, 0), (15, 2), (11, 2), (9, 3),
               (3, 3), (1, 2), (0, 2)], fill=7)
    d.line([(0, 3), (2, 3), (3, 4), (9, 4), (11, 3), (15, 3)], fill=6)
    d.polygon([(0, 10), (3, 11), (8, 11), (10, 10), (14, 10),
               (15, 10), (15, 15), (0, 15)], fill=1)
    d.line([(0, 14), (4, 14), (6, 13), (12, 13), (15, 14)], fill=2)
    d.line([(0, 9), (3, 10), (8, 10), (10, 9), (14, 9), (15, 9)], fill=3)
    if variant:
        # A wide diagonal chip rather than a vertical masonry grid.
        d.polygon([(9, 3), (12, 3), (11, 6), (8, 7), (7, 7)], fill=4)
        d.line([(8, 7), (11, 6), (12, 4)], fill=6)
        d.polygon([(2, 8), (5, 8), (7, 10), (3, 10)], fill=4)
    else:
        d.polygon([(3, 5), (6, 5), (7, 6), (4, 8), (2, 8)], fill=4)
        d.line((3, 5, 5, 5), fill=6)
        d.line((11, 7, 14, 7), fill=6)
    if stage:
        # Sour mats root in sheltered undersides, changing the cut silhouette.
        d.polygon([(0, 9), (3, 9), (4, 11), (6, 11), (5, 13),
                   (2, 12), (0, 13)], fill=9)
        d.line([(0, 9), (2, 10), (3, 11)], fill=10)
        if variant:
            d.polygon([(12, 8), (15, 8), (15, 13), (13, 12)], fill=9)
            d.line((14, 9, 15, 9), fill=11)
    if stage == 2:
        d.polygon([(0, 8), (4, 8), (5, 9), (8, 9), (10, 10),
                   (14, 9), (15, 9), (15, 14), (0, 14)], fill=1)
        d.line([(0, 11), (4, 11), (6, 12), (10, 12), (12, 11), (15, 11)], fill=12, width=2)
        if variant:
            d.line([(0, 11), (4, 11), (6, 12), (10, 12), (12, 11), (15, 11)], fill=13)
            d.line((7, 12, 10, 12), fill=14)
            d.line([(11, 11), (12, 9), (14, 8)], fill=13)
        else:
            d.line([(0, 11), (4, 11), (6, 12)], fill=13)
            d.line((1, 11, 3, 11), fill=14)
    if kind == 'top':
        d.polygon([(0, 0), (15, 0), (15, 3), (11, 3), (9, 4),
                   (3, 4), (2, 3), (0, 3)], fill=7)
        d.line([(0, 0), (15, 0)], fill=8)
        d.line([(0, 4), (2, 4), (3, 5), (9, 5), (11, 4), (15, 4)], fill=3)
        if variant:
            d.polygon([(10, 0), (12, 0), (11, 2), (9, 3), (8, 3)], fill=6)
    elif kind == 'base':
        d.polygon([(0, 12), (3, 12), (5, 13), (9, 13),
                   (11, 12), (15, 12), (15, 15), (0, 15)], fill=2)
        d.line([(0, 14), (4, 14), (6, 15), (15, 15)], fill=1)
        d.polygon([(1, 12), (4, 12), (5, 13), (2, 13)], fill=5)
        d.polygon([(10, 13), (13, 12), (15, 13), (14, 14)], fill=3)
    elif kind == 'left':
        d.polygon([(0, 0), (2, 0), (2, 3), (4, 5), (3, 9),
                   (2, 11), (3, 15), (0, 15)], fill=1)
        d.line([(3, 0), (3, 3), (5, 5)], fill=7)
        d.line([(3, 11), (4, 13), (4, 15)], fill=6)
    elif kind == 'right':
        d.polygon([(13, 0), (15, 0), (15, 15), (13, 15),
                   (12, 12), (13, 9), (12, 5), (13, 3)], fill=1)
        d.line([(12, 1), (12, 3), (11, 5)], fill=3)
        d.line((12, 12, 13, 15), fill=2)
    return image


def climb(stage=0, kind='mid'):
    """Timber-braced work face, with three unequivocal ivory metal staples."""
    stage = _stage(stage)
    image = cliff(stage, 'mid', 0)
    d = ImageDraw.Draw(image)
    d.rectangle((2, 0, 13, 15), fill=1)
    d.rectangle((4, 0, 11, 15), fill=2)
    # Timber side rails and black drill holes sit behind the shining staples.
    d.rectangle((2, 0, 3, 15), fill=3)
    d.line((2, 0, 2, 15), fill=5)
    d.rectangle((12, 0, 13, 15), fill=3)
    d.line((12, 0, 12, 15), fill=5)
    for y in (2, 7, 12):
        d.rectangle((3, y, 12, y + 2), fill=1)
        d.line((4, y, 11, y), fill=8)
        d.line((4, y + 1, 11, y + 1), fill=6)
        d.point((4, y + 2), fill=5)
        d.point((11, y + 2), fill=3)
    if kind == 'top':
        d.line((0, 0, 15, 0), fill=7)
        d.line((4, 0, 11, 0), fill=8)
    elif kind == 'bottom':
        d.line((2, 15, 13, 15), fill=6)
        d.line((4, 14, 11, 14), fill=7)
    return image


def rim(stage=0, variant=0, drop=False):
    stage = _stage(stage)
    image = floor(stage, variant)
    d = ImageDraw.Draw(image)
    if drop:
        # An unobstructed broad shelf, with an exposed face below the lip.
        d.polygon([(0, 11), (4, 11), (6, 10), (10, 10), (12, 11),
                   (15, 11), (15, 15), (0, 15)], fill=10)
        d.line([(0, 11), (4, 11), (6, 10), (10, 10), (12, 11), (15, 11)], fill=7)
        d.line([(0, 14), (5, 14), (7, 15), (15, 15)], fill=2)
        d.line((5, 12, 10, 12), fill=5)
    else:
        # Solid raised parapet: its large painted volume cannot read as a gap.
        d.polygon([(0, 7), (2, 5), (7, 5), (8, 6), (13, 5),
                   (15, 7), (15, 15), (0, 15)], fill=2)
        d.polygon([(0, 7), (2, 5), (7, 5), (8, 6), (13, 5),
                   (15, 7), (13, 9), (8, 10), (2, 9)], fill=6)
        d.line([(2, 5), (7, 5), (8, 6), (12, 5)], fill=8)
        d.polygon([(1, 10), (7, 11), (13, 10), (15, 9),
                   (15, 13), (10, 14), (3, 13), (1, 12)], fill=10)
        d.line((3, 10, 6, 10), fill=7)
        if stage:
            d.polygon([(11, 11), (15, 10), (15, 14), (12, 14)], fill=12)
            if stage == 2:
                d.line([(12, 12), (14, 11), (15, 11)], fill=14)
    return image


def cave(stage=0):
    """A tall quarry adit: heavy lintel, deep opening and a lit landing."""
    stage = _stage(stage)
    image, d = _new('cream_cliff%d' % stage, size=(32, 48))
    d.polygon([(0, 47), (1, 13), (4, 5), (9, 2), (24, 2),
               (29, 6), (31, 17), (31, 47)], fill=1)
    d.polygon([(2, 43), (3, 13), (6, 6), (10, 4), (23, 4),
               (28, 8), (29, 18), (29, 44)], fill=4)
    # Unequal hand-cut header blocks project beyond the timber jambs.
    d.polygon([(3, 11), (5, 5), (10, 2), (24, 2), (28, 6),
               (30, 12), (26, 14), (7, 14)], fill=6)
    d.polygon([(5, 6), (10, 2), (24, 2), (27, 5), (23, 7), (9, 7)], fill=7)
    d.line([(8, 4), (11, 3), (22, 3)], fill=8)
    d.line([(4, 12), (9, 14), (25, 14), (29, 12)], fill=3, width=2)
    d.line([(16, 5), (14, 8), (17, 11)], fill=4)
    # Large negative space stays visibly larger than Bloom.
    d.polygon([(7, 44), (7, 17), (9, 15), (23, 15),
               (25, 18), (25, 44)], fill=1)
    # The large interior is painted deep ink rather than transparent ground.
    d.rectangle((9, 18, 23, 41), fill=1)
    d.line((8, 18, 8, 40), fill=2)
    d.rectangle((5, 16, 7, 42), fill=3)
    d.line((5, 17, 5, 40), fill=5)
    d.rectangle((25, 16, 27, 42), fill=3)
    d.line((25, 17, 25, 40), fill=5)
    d.rectangle((5, 15, 27, 18), fill=3)
    d.line((6, 15, 26, 15), fill=6)
    d.line((7, 19, 11, 23), fill=3, width=2)
    d.line((25, 19, 21, 23), fill=3, width=2)
    d.line((7, 19, 10, 22), fill=5)
    for y in (25, 35):
        d.line((2, y, 4, y - 1), fill=2)
        d.line((28, y - 1, 30, y), fill=2)
    # Copper lamp mounted outside the opening, amber rather than violet.
    d.rectangle((26, 25, 29, 30), fill=1)
    d.line((26, 24, 29, 24), fill=6)
    d.rectangle((27, 26, 28, 28), fill=7)
    d.point((27, 26), fill=8)
    d.polygon([(5, 43), (9, 41), (23, 41), (27, 43),
               (29, 47), (3, 47)], fill=3)
    d.polygon([(7, 43), (11, 42), (23, 42), (26, 44), (6, 44)], fill=6)
    d.line((4, 46, 28, 46), fill=7)
    d.line((6, 47, 26, 47), fill=5)
    if stage:
        d.polygon([(2, 29), (5, 28), (5, 35), (3, 38), (2, 42)], fill=9)
        d.line([(3, 30), (4, 33), (3, 35)], fill=10)
        d.polygon([(24, 3), (27, 5), (29, 8), (26, 8), (25, 11), (23, 9)], fill=3)
    if stage == 2:
        d.line([(24, 4), (24, 9), (27, 12), (28, 18), (29, 21)], fill=12, width=3)
        d.line([(24, 4), (24, 9), (27, 12), (28, 18), (29, 21)], fill=13)
        d.line([(25, 10), (27, 12), (27, 14)], fill=14)
        d.polygon([(1, 33), (4, 32), (4, 37), (2, 42), (1, 42)], fill=1)
        d.line([(2, 34), (3, 36), (2, 39)], fill=13)
    return image


def water(stage=0, phase=0, fall=False):
    stage = _stage(stage)
    phase = int(phase) % 2
    image, d = _new('cream_water', 3)
    if fall:
        d.rectangle((0, 0, 2, 15), fill=1)
        d.rectangle((13, 0, 15, 15), fill=2)
        d.rectangle((3, 0, 5, 15), fill=5)
        d.rectangle((6, 0, 10, 15), fill=4)
        d.line((3, 0, 3, 15), fill=6)
        d.line((11, 0, 11, 15), fill=2)
        for y in (1 + phase * 4, 10 + phase * 3):
            d.line((5, y, 5, min(15, y + 3)), fill=7)
            d.line((8, max(0, y - 2), 8, y), fill=6)
        d.line((11, phase * 4 + 4, 11, phase * 4 + 8), fill=5)
    else:
        d.polygon([(0, 3), (4, 3), (6, 4), (12, 4), (15, 3),
                   (15, 7), (10, 7), (7, 6), (0, 6)], fill=4)
        d.line((1 + phase, 4, 5 + phase, 4), fill=5)
        d.line((9 - phase, 11, 13 - phase, 11), fill=5)
        d.line((10 - phase, 12, 14 - phase, 12), fill=4)
        d.line((2 + phase, 4, 3 + phase, 4), fill=6)
    if stage == 1:
        d.line((0, 14, 4, 14), fill=9)
        d.line((1, 13, 3, 13), fill=10)
    elif stage == 2:
        if fall:
            d.line([(10, 0), (9, 4), (10, 8), (9, 12), (10, 15)], fill=12, width=2)
            d.line((10, 4 + phase * 4, 10, 7 + phase * 4), fill=14)
        else:
            d.polygon([(0, 12), (3, 11), (6, 12), (8, 14), (15, 14), (15, 15), (0, 15)], fill=12)
            d.line([(0, 12), (3, 12), (6, 13), (8, 14), (11, 14)], fill=13)
            d.line((3 + phase, 12, 5 + phase, 12), fill=14)
    return image


def prop(kind='mold', stage=0, phase=0):
    stage = _stage(stage)
    phase = int(phase) % 2
    image, d = _new('cream_props')
    if kind == 'mold':
        d.polygon([(0, 14), (3, 11), (8, 11), (11, 10), (15, 12), (14, 15), (2, 15)], fill=1)
        # Slime collects around discarded curdstone and one snapped chisel.
        d.polygon([(2, 12), (4, 8), (8, 8), (10, 11), (8, 14), (3, 14)], fill=9 if stage < 2 else 12)
        d.polygon([(9, 10), (11, 7), (14, 8), (15, 12), (12, 14), (9, 13)], fill=10 if stage < 2 else 13)
        d.line((4, 9, 7, 9), fill=11 if stage < 2 else 13)
        d.polygon([(5, 12), (7, 10), (9, 11), (8, 13)], fill=4)
        d.line((6, 11, 7, 11), fill=7)
        d.line((1, 13, 4, 10), fill=3, width=2)
        d.point((2, 12), fill=6)
        if stage == 1:
            d.polygon([(10, 8), (12, 8), (13, 10), (11, 11)], fill=9)
        elif stage == 2:
            d.line([(10, 10), (12, 9), (13, 10)], fill=14)
            d.point((12, 9), fill=15)
    elif kind == 'lamp':
        d.line((7, 8, 7, 14), fill=3, width=3)
        d.line((6, 14, 10, 14), fill=1)
        d.line((6, 9, 6, 13), fill=6)
        d.polygon([(2, 6), (4, 8), (11, 8), (14, 5), (13, 9), (10, 11), (5, 10)], fill=1)
        d.polygon([(3, 6), (12, 6), (11, 9), (5, 9)], fill=5)
        d.line((3, 6, 12, 6), fill=7)
        d.line((5, 9, 10, 9), fill=6)
        d.polygon([(6, 6), (5, 4), (7, 1 + phase), (8, 3), (10, 2), (10, 5), (9, 6)], fill=6)
        d.line((7, 3 + phase, 7, 5), fill=8)
        d.point((6, 7), fill=8)
    elif kind == 'shrine':
        d.polygon([(1, 14), (3, 10), (13, 10), (15, 14), (13, 15), (2, 15)], fill=1)
        d.polygon([(2, 11), (4, 9), (12, 9), (14, 11), (12, 13), (4, 13)], fill=6)
        d.rectangle((4, 11, 12, 13), fill=4)
        d.line((3, 11, 12, 11), fill=7)
        d.polygon([(5, 10), (5, 4), (7, 1), (10, 1), (12, 4), (11, 10)], fill=1)
        d.polygon([(6, 9), (6, 4), (8, 2), (10, 3), (10, 9)], fill=5)
        d.line([(7, 8), (7, 4), (8, 3)], fill=7)
        d.rectangle((8, 5, 9, 8), fill=9 if phase else 7)
        if not phase:
            d.point((8, 5), fill=8)
    elif kind == 'switch':
        # The complete collision-cell footprint is the broad pressure face.
        d.polygon([(0, 4), (3, 1), (12, 1), (15, 4), (15, 13), (12, 15), (3, 15), (0, 13)], fill=1)
        if phase:
            d.polygon([(1, 5), (4, 3), (11, 3), (14, 5), (14, 12), (11, 14), (4, 14), (1, 12)], fill=3)
            d.polygon([(3, 7), (5, 5), (11, 5), (12, 7), (12, 11), (10, 12), (5, 12), (3, 10)], fill=6)
            d.line((5, 5, 11, 5), fill=8)
            d.line((2, 13, 12, 13), fill=7)
        else:
            d.polygon([(1, 4), (4, 1), (11, 1), (14, 4), (14, 10), (11, 12), (4, 12), (1, 10)], fill=5)
            d.polygon([(3, 4), (5, 3), (11, 3), (12, 5), (12, 9), (10, 10), (4, 10), (3, 8)], fill=6)
            d.line([(2, 4), (4, 2), (11, 2)], fill=7)
            d.line((4, 13, 11, 13), fill=3)
    elif kind == 'trial':
        d.polygon([(1, 14), (4, 11), (12, 11), (15, 14), (12, 15), (3, 15)], fill=1)
        d.rectangle((4, 11, 11, 13), fill=5)
        d.line((4, 11, 11, 11), fill=7)
        d.polygon([(4, 10), (4, 4), (7, 0), (10, 0), (13, 4), (12, 10)], fill=1)
        d.polygon([(6, 9), (6, 4), (8, 1), (11, 4), (10, 9)], fill=6)
        d.line([(7, 4), (8, 2), (9, 3)], fill=8)
        d.line((8, 5, 8, 7), fill=8)
    elif kind == 'cache':
        d.polygon([(0, 13), (3, 10), (12, 10), (15, 13), (14, 15), (2, 15)], fill=1)
        for x, y in ((2, 10), (7, 8), (8, 12)):
            d.polygon([(x, y), (x + 2, y - 2), (x + 5, y - 2), (x + 6, y), (x + 4, y + 2), (x, y + 2)], fill=4)
            d.line((x + 1, y, x + 5, y), fill=7)
            d.line((x + 2, y - 1, x + 4, y - 1), fill=6)
        d.point((9, 7), fill=8)
    elif kind == 'ward':
        d.polygon([(0, 15), (0, 4), (3, 1), (12, 1), (15, 4), (15, 15)], fill=1)
        d.polygon([(1, 13), (1, 4), (4, 2), (11, 2), (14, 4), (14, 13)], fill=4)
        d.line([(2, 4), (4, 2), (11, 2)], fill=7)
        d.rectangle((4, 3, 11, 13), fill=6)
        d.line((4, 4, 4, 12), fill=8)
        # One bold keyhole: a round head and flared shaft at native size.
        d.ellipse((6, 5, 10, 9), fill=1)
        d.polygon([(7, 8), (9, 8), (10, 12), (6, 12)], fill=1)
        d.line((12, 5, 12, 12), fill=3)
    elif kind == 'thorn':
        d.polygon([(0, 14), (3, 11), (13, 11), (15, 15), (1, 15)], fill=1)
        branches = [([(2, 14), (5, 10), (4, 5), (7, 8), (9, 4), (10, 10), (14, 6)], 3),
                    ([(4, 14), (9, 11), (13, 12), (14, 9)], 2)]
        for points, width in branches:
            d.line(points, fill=1, width=width + 2)
            d.line(points, fill=9 if stage < 2 else 12, width=width)
            d.line(points, fill=10 if stage < 2 else 13)
        for points in ([(4, 7), (1, 4), (4, 5)], [(8, 7), (8, 1), (10, 5)],
                       [(11, 10), (15, 7), (14, 11)]):
            d.polygon(points, fill=3 if stage < 2 else 13)
        d.line((5, 10, 5, 12), fill=11 if stage < 2 else 14)
    elif kind == 'web':
        # Pale, connected fibres remain visibly separate from living mold.
        d.line([(1, 1), (7, 6), (15, 2)], fill=3, width=2)
        d.line([(0, 13), (7, 7), (14, 15)], fill=3, width=2)
        for line in (((1, 1), (14, 15)), ((15, 2), (0, 13)), ((8, 0), (7, 15)), ((0, 7), (15, 9))):
            d.line(line, fill=7)
        d.polygon([(4, 4), (10, 3), (13, 8), (10, 12), (4, 12), (2, 7)], outline=6)
        d.polygon([(6, 6), (9, 5), (11, 8), (9, 10), (6, 10), (4, 7)], outline=8)
        d.line((2, 2, 4, 4), fill=8)
    elif kind == 'crack':
        d.polygon([(0, 15), (0, 6), (4, 1), (11, 1), (15, 5), (15, 15)], fill=1)
        d.polygon([(1, 12), (2, 6), (5, 2), (10, 2), (14, 6), (13, 13), (5, 14)], fill=4)
        d.polygon([(3, 6), (5, 2), (10, 2), (12, 5), (8, 7)], fill=6)
        d.line([(4, 4), (6, 3), (9, 3)], fill=8)
        d.line([(10, 2), (7, 6), (9, 9), (6, 14)], fill=1, width=2)
        d.line([(7, 6), (4, 8), (2, 8)], fill=1)
        d.line([(9, 9), (12, 10), (14, 9)], fill=1)
        d.line([(9, 3), (6, 6), (7, 8)], fill=7)
        d.line((8, 10, 6, 12), fill=6)
    return image


def chest(opened=False):
    """A 22px quarry pay chest: timber, brass straps, one generous latch."""
    image, d = _new('cream_props', size=(32, 32))
    d.ellipse((4, 27, 28, 31), fill=1)
    d.polygon([(5, 27), (5, 15), (8, 11), (23, 11), (27, 15),
               (27, 27), (24, 30), (8, 30)], fill=1)
    d.rectangle((7, 17, 25, 27), fill=3)
    d.rectangle((8, 19, 24, 26), fill=4)
    d.line((8, 22, 24, 22), fill=3)
    d.line((8, 26, 24, 26), fill=5)
    d.line((8, 28, 24, 28), fill=6)
    if opened:
        d.polygon([(5, 16), (5, 7), (9, 4), (23, 4), (27, 8), (27, 16)], fill=1)
        d.polygon([(7, 14), (7, 8), (10, 6), (22, 6), (25, 9), (25, 14)], fill=4)
        d.line((9, 6, 22, 6), fill=7)
        d.rectangle((8, 16, 24, 20), fill=1)
        d.line((8, 21, 24, 21), fill=6)
        for x in (9, 22):
            d.line((x, 7, x, 14), fill=6, width=2)
            d.line((x, 23, x, 27), fill=6, width=2)
            d.line((x, 7, x, 12), fill=8)
        d.rectangle((14, 22, 19, 25), fill=1)
        d.line((15, 23, 18, 23), fill=6)
    else:
        d.polygon([(6, 16), (8, 12), (12, 10), (21, 10), (25, 13), (26, 16)], fill=5)
        d.line((11, 11, 21, 11), fill=7)
        d.line((8, 16, 24, 16), fill=6)
        for x in (9, 22):
            d.rectangle((x, 13, x + 1, 27), fill=6)
            d.line((x, 13, x, 24), fill=8)
        d.rectangle((13, 17, 20, 24), fill=1)
        d.rectangle((14, 18, 19, 23), fill=6)
        d.line((14, 18, 18, 18), fill=8)
        d.rectangle((16, 20, 17, 21), fill=1)
        d.point((16, 22), fill=1)
    return image


def pit(stage=0):
    stage = _stage(stage)
    image = floor(stage, 0)
    d = ImageDraw.Draw(image)
    d.polygon([(0, 4), (3, 2), (11, 2), (15, 5), (15, 15),
               (1, 15), (0, 12)], fill=3)
    d.polygon([(1, 5), (4, 3), (11, 3), (14, 6), (14, 14),
               (3, 14), (1, 11)], fill=2)
    d.polygon([(3, 6), (5, 5), (11, 5), (13, 7), (13, 14),
               (4, 14), (2, 11)], fill=1)
    d.line([(1, 4), (4, 2), (10, 2)], fill=7)
    d.line((4, 15, 12, 15), fill=9)
    return image
