"""Brine Basilica: original native-GBA limestone and ruined gilt architecture.

An exploratory Cream treatment, not an emulator capture or an adopted rule.
Every mark is drawn directly on its final indexed canvas.  The two cliff
variants are the literal halves of one native 32x16 vaulted masonry bay.
"""
from PIL import Image, ImageDraw


PALETTES = {
    'cream_floor0': ['#000000', '#302830', '#786848', '#a09068', '#b8b088', '#d0c8a0', '#e0d8b8', '#f0e8c8', '#f8f0d8', '#606048', '#888868', '#b0b090', '#584058', '#885890', '#c878e0', '#f0d0f8'],
    'cream_floor1': ['#000000', '#302830', '#706848', '#908858', '#a8a878', '#c0c098', '#d8d8b0', '#e8e8c0', '#f0f0d0', '#505840', '#788060', '#a0a880', '#503850', '#805080', '#b860d8', '#e8c8f0'],
    'cream_floor2': ['#000000', '#281828', '#685868', '#887878', '#a09888', '#b8b098', '#d0c8b0', '#e0d8c0', '#f0e8d0', '#483850', '#706070', '#a09898', '#482050', '#8838a8', '#d068f0', '#f0d0f8'],
    'cream_cliff0': ['#000000', '#282028', '#403828', '#605038', '#887850', '#a89870', '#c0b888', '#e0d8a8', '#f8f0c8', '#384038', '#586048', '#889070', '#503848', '#805878', '#b088a8', '#e8d0d0'],
    'cream_cliff1': ['#000000', '#282028', '#383828', '#585038', '#787048', '#989068', '#b0b080', '#d0d098', '#e8e8b8', '#303830', '#485840', '#788860', '#482840', '#784870', '#b060a0', '#e8c0e0'],
    'cream_cliff2': ['#000000', '#201020', '#302030', '#483840', '#685858', '#887870', '#a89888', '#c8b8a0', '#e8d8b8', '#282030', '#484048', '#706878', '#502060', '#9038b8', '#d868f0', '#f8d8f8'],
    'cream_water': ['#000000', '#282830', '#384038', '#505848', '#687860', '#889878', '#b0c0a0', '#d8e0b8', '#f0f0d0', '#484840', '#687060', '#909880', '#482850', '#783890', '#b860d8', '#e8c8f0'],
    'cream_props': ['#000000', '#281f28', '#483830', '#685038', '#907048', '#b89058', '#d8b878', '#f0d8a0', '#fff0c8', '#384838', '#587050', '#809870', '#482850', '#8838a8', '#d850e8', '#fff0f8'],
}
# GBA RGB555 storage: do the rounding in the bank, never after drawing.
PALETTES = {name: ['#%02x%02x%02x' % tuple(int(c[i:i+2], 16) // 8 * 8 for i in (1, 3, 5)) for c in bank]
            for name, bank in PALETTES.items()}


def _canvas(size=(16, 16), fill=0, palette='cream_props'):
    im = Image.new('P', size, fill)
    colours = [int(c[i:i+2], 16) for c in PALETTES[palette] for i in (1, 3, 5)]
    im.putpalette(colours + [0] * (768 - len(colours)))
    im.info['transparency'] = 0
    return im, ImageDraw.Draw(im)


def _stage(stage):
    return max(0, min(2, int(stage)))


def floor(stage=0, variant=0, path=False):
    """Quiet worn flagstones, with one restrained deposit per variant."""
    stage = _stage(stage)
    variant %= 4
    im, d = _canvas(fill=6, palette='cream_floor%d' % stage)
    # The paving's broad stone surface dominates; joints never box each tile.
    if variant == 0:
        d.line((0, 13, 3, 13), fill=5)
        d.line((1, 14, 4, 14), fill=7)
        d.point((3, 4), fill=7)
    elif variant == 1:
        d.line([(2, 9), (5, 9), (6, 11), (9, 12)], fill=4)
        d.line([(3, 10), (5, 10), (6, 12), (8, 13)], fill=7)
        d.line((6, 11, 6, 14), fill=5)
    elif variant == 2:
        d.polygon([(10, 2), (14, 1), (15, 3), (14, 5), (11, 5), (9, 4)], fill=5)
        d.line((11, 2, 14, 2), fill=7)
        if stage:
            d.line([(12, 3), (14, 3), (15, 4)], fill=11 if stage == 1 else 9)
            if stage == 2:
                d.point((14, 3), fill=13)
    else:
        d.line([(10, 9), (12, 10), (12, 12), (15, 13)], fill=5)
        d.line([(10, 10), (11, 11), (11, 13)], fill=7)
        d.line((0, 2, 2, 2), fill=5)
    if path:
        # Dry travel wears the same limestone rather than adding brown tiles.
        for x, y in ((3, 5), (8, 8), (11, 6)):
            d.line((x, y, x+2, y), fill=7)
        if variant == 2:
            d.line((4, 12, 8, 11), fill=5)
    return im


def _vault(stage, kind):
    im, d = _canvas((32, 16), 4, 'cream_cliff%d' % stage)
    # Native two-column bay: a real dark recess underneath raised stone ribs.
    d.rectangle((4, 0, 28, 15), fill=3)
    d.polygon([(5, 15), (5, 10), (8, 6), (12, 3), (16, 1), (21, 4), (25, 8), (28, 13), (28, 15)], fill=2)
    d.polygon([(8, 15), (8, 11), (11, 7), (16, 4), (20, 7), (23, 12), (23, 15)], fill=1)
    # Strong upper-left stone plane; the right side is broad shadow.
    d.line([(4, 15), (4, 11), (7, 7), (11, 4), (16, 1), (21, 4), (25, 8), (28, 13), (28, 15)], fill=5, width=3)
    d.line([(3, 14), (3, 11), (6, 7), (10, 4), (16, 0)], fill=7)
    d.line([(6, 14), (6, 11), (9, 7), (13, 4), (16, 2)], fill=6)
    d.line([(18, 4), (22, 8), (25, 13), (25, 15)], fill=3)
    # Buttress: lit left slab, narrow face, deep cast shadow to its right.
    d.rectangle((0, 0, 1, 15), fill=7)
    d.line((2, 0, 2, 15), fill=5)
    d.line((3, 0, 3, 8), fill=2)
    d.rectangle((30, 0, 31, 15), fill=4)
    d.line((29, 0, 29, 15), fill=2)
    for y in (4, 12):
        d.line((0, y, 2, y), fill=3)
        d.point((0, y+1), fill=8)
        d.line((30, y, 31, y), fill=2)
    # Geological bedding remains visible through the cut architecture.
    d.line((11, 13, 21, 13), fill=2)
    d.line((11, 14, 18, 14), fill=3)
    d.line((13, 8, 17, 8), fill=2)
    # Individual worn voussoirs interrupt the rib, without becoming noise.
    d.line((7, 7, 9, 8), fill=3)
    d.line((12, 3, 13, 5), fill=4)
    d.line((21, 5, 23, 5), fill=3)
    d.point((7, 6), fill=8)
    d.polygon([(25, 11), (27, 12), (27, 14), (26, 13)], fill=4)
    d.point((11, 6), fill=8)
    d.point((20, 5), fill=6)
    if stage >= 1:
        # Decay undercuts the rib and gathers below the stone ledge.
        d.polygon([(21, 9), (24, 10), (25, 13), (22, 15), (20, 15)], fill=9)
        d.line([(22, 10), (22, 12), (24, 13)], fill=10)
        d.line((7, 12, 8, 15), fill=10)
        d.line([(27, 2), (27, 4), (26, 5)], fill=2)
    if stage == 2:
        # Lost voussoirs expose a branching luminous cavity, not a hue swap.
        d.polygon([(9, 5), (13, 3), (13, 5), (11, 7), (10, 10), (7, 11), (7, 8)], fill=1)
        d.line([(8, 10), (10, 8), (10, 6), (13, 4)], fill=12, width=3)
        d.line([(8, 10), (10, 8), (10, 6), (12, 4)], fill=13)
        d.line((10, 7, 10, 8), fill=14)
        d.point((11, 5), fill=15)
        d.line([(21, 15), (21, 12), (23, 11), (24, 8)], fill=13)
        d.point((23, 11), fill=14)
        d.rectangle((30, 9, 31, 12), fill=1)
    if kind == 'top':
        # Projecting broken cornice has a pale top and a deep overhang.
        d.rectangle((0, 0, 31, 2), fill=6)
        d.line((0, 0, 31, 0), fill=8)
        d.line((0, 3, 31, 3), fill=1)
        d.line((0, 4, 31, 4), fill=2)
        d.line((0, 1, 11, 1), fill=7)
        d.rectangle((12, 0, 14, 1), fill=5)
        d.line((25, 2, 28, 2), fill=3)
        if stage:
            d.polygon([(22, 0), (24, 0), (24, 2), (22, 3), (20, 2)], fill=3)
            if stage == 2:
                d.point((22, 2), fill=14)
    elif kind == 'base':
        d.rectangle((0, 12, 31, 13), fill=3)
        d.line((0, 12, 31, 12), fill=6)
        d.rectangle((0, 14, 31, 15), fill=1)
        d.line((0, 14, 12, 14), fill=2)
        d.line((18, 14, 27, 14), fill=2)
        d.line([(9, 13), (12, 12), (15, 13), (17, 13)], fill=10 if stage < 2 else 12)
        if stage == 2:
            d.line((12, 12, 14, 12), fill=14)
    return im


def cliff(stage=0, kind='mid', variant=0):
    stage = _stage(stage)
    image = _vault(stage, kind)
    half = (variant % 2) * 16
    im = image.crop((half, 0, half+16, 16))
    d = ImageDraw.Draw(im)
    if kind == 'left':
        d.rectangle((0, 0, 2, 15), fill=2)
        d.line((3, 0, 3, 15), fill=7)
        d.line((4, 0, 4, 15), fill=5)
    elif kind == 'right':
        d.rectangle((12, 0, 15, 15), fill=1)
        d.line((11, 0, 11, 15), fill=4)
    return im


def climb(stage=0, kind='mid'):
    """A continuous recessed shaft, with four unmistakable brass staples."""
    stage = _stage(stage)
    im = cliff(stage, 'mid', 0)
    d = ImageDraw.Draw(im)
    d.rectangle((3, 0, 12, 15), fill=1)
    d.line((3, 0, 3, 15), fill=3)
    d.line((4, 0, 4, 15), fill=6)
    d.line((11, 0, 11, 15), fill=3)
    d.line((12, 0, 12, 15), fill=5)
    for y in (2, 6, 10, 14):
        d.rectangle((5, y, 10, y+1), fill=2)
        d.line((5, y, 10, y), fill=7)
        d.point((5, y-1), fill=8)
        d.point((10, y+1), fill=5)
    if kind == 'top':
        d.line((0, 0, 15, 0), fill=7)
        d.line((0, 1, 3, 1), fill=8)
        d.line((12, 1, 15, 1), fill=6)
    elif kind == 'bottom':
        d.line((2, 15, 13, 15), fill=3)
        d.line((4, 14, 11, 14), fill=7)
    if stage == 2:
        d.line((2, 7, 2, 11), fill=13)
        d.point((2, 8), fill=14)
    return im


def rim(stage=0, variant=0, drop=False):
    stage = _stage(stage)
    im = floor(stage, variant)
    d = ImageDraw.Draw(im)
    if drop:
        # Clear, broad dry takeoff; nothing projects above the low broken lip.
        d.rectangle((0, 12, 15, 15), fill=2)
        d.line((0, 11, 15, 11), fill=7)
        d.line((0, 12, 15, 12), fill=4)
        d.line((4, 12, 11, 12), fill=5)
        d.line((6, 13, 9, 13), fill=3)
        d.point((7, 14), fill=4)
    else:
        # Solid raised parapet, squared at the foot and crenellated above.
        d.rectangle((0, 8, 15, 15), fill=2)
        d.rectangle((0, 7, 15, 10), fill=5)
        d.line((0, 7, 15, 7), fill=8)
        d.line((0, 11, 15, 11), fill=1)
        for x in (0, 10):
            d.rectangle((x, 4, min(x+5, 15), 8), fill=4)
            d.line((x, 4, min(x+5, 15), 4), fill=7)
            d.line((x, 5, x, 7), fill=6)
        d.line((0, 14, 15, 14), fill=3)
        d.line((3, 12, 3, 13), fill=1)
        if stage:
            d.polygon([(12, 9), (14, 8), (15, 10), (15, 13), (13, 13)], fill=9)
            if stage == 2:
                d.line((14, 9, 14, 12), fill=13)
                d.point((14, 10), fill=14)
    return im


def cave(stage=0):
    """A ruined pointed portal; lower opening is exactly sixteen pixels wide."""
    stage = _stage(stage)
    im, d = _canvas((32, 48), 0, 'cream_cliff%d' % stage)
    # Unequal broken buttresses and an intact dry doorway, all native pixels.
    d.polygon([(0, 47), (0, 18), (3, 18), (3, 9), (7, 9), (7, 6), (11, 6), (16, 0), (21, 6), (26, 8), (26, 16), (31, 19), (31, 47)], fill=1)
    d.polygon([(1, 46), (1, 20), (4, 20), (4, 11), (8, 11), (8, 8), (12, 8), (16, 3), (21, 8), (25, 10), (25, 19), (30, 21), (30, 46)], fill=4)
    d.rectangle((1, 23, 5, 44), fill=6)
    d.line((1, 23, 1, 43), fill=8)
    d.rectangle((26, 24, 30, 45), fill=3)
    d.line((26, 24, 26, 43), fill=5)
    d.polygon([(5, 46), (5, 23), (7, 17), (10, 12), (16, 7), (21, 12), (25, 18), (27, 24), (27, 46)], fill=2)
    d.line([(5, 44), (5, 24), (8, 17), (11, 13), (16, 8), (21, 13), (24, 19), (26, 24), (26, 44)], fill=6, width=3)
    d.line([(4, 40), (4, 24), (7, 17), (10, 13), (16, 7)], fill=8)
    d.line([(7, 39), (7, 25), (10, 19), (16, 13), (21, 19), (24, 25), (24, 40)], fill=3, width=2)
    # Dark mouth taller than Bloom, with broad black negative space.
    d.polygon([(8, 45), (8, 26), (10, 21), (13, 17), (16, 14), (20, 18), (23, 24), (23, 45)], fill=1)
    d.line([(9, 27), (11, 22), (14, 19), (16, 17)], fill=2)
    d.rectangle((8, 32, 23, 45), fill=1)
    # Worn voussoirs: darker joints sit across the arch rather than on top.
    for points in ([(6, 24), (8, 25)], [(8, 17), (10, 19)], [(11, 13), (13, 15)], [(20, 13), (18, 15)], [(24, 20), (22, 21)]):
        d.line(points, fill=3)
    d.line((2, 29, 5, 29), fill=3)
    d.line((2, 30, 5, 30), fill=7)
    d.line((27, 33, 30, 33), fill=2)
    # Projecting cornices cast shadows; they do not cover the usable mouth.
    for x, y, w in ((0, 20, 6), (25, 21, 6), (0, 42, 7), (25, 43, 6)):
        d.rectangle((x, y, x+w, y+2), fill=3)
        d.line((x, y, x+w, y), fill=7)
        d.line((x, y+3, x+w, y+3), fill=1)
    d.rectangle((7, 46, 24, 47), fill=5)
    d.line((7, 46, 24, 46), fill=8)
    d.line((9, 47, 22, 47), fill=6)
    if stage:
        d.polygon([(27, 28), (30, 27), (31, 30), (31, 40), (28, 40), (27, 36)], fill=9)
        d.line([(28, 29), (28, 33), (30, 35), (29, 39)], fill=10)
        d.polygon([(5, 10), (8, 8), (10, 9), (8, 12), (6, 14)], fill=2)
    if stage == 2:
        d.line([(28, 28), (28, 32), (30, 35), (29, 39)], fill=13)
        d.line((28, 31, 28, 32), fill=14)
        d.point((30, 35), fill=15)
        d.polygon([(19, 7), (22, 8), (23, 11), (20, 13), (19, 10)], fill=1)
        d.line([(20, 8), (21, 10), (20, 12)], fill=13)
        d.point((21, 10), fill=14)
    return im


def water(stage=0, phase=0, fall=False):
    stage = _stage(stage)
    phase %= 2
    im, d = _canvas(fill=3, palette='cream_water')
    if fall:
        # Stone channel, continuous wet sheet and staggered downward streaks.
        d.rectangle((0, 0, 2, 15), fill=2)
        d.rectangle((13, 0, 15, 15), fill=1)
        d.line((3, 0, 3, 15), fill=6)
        d.line((4, 0, 4, 15), fill=5)
        d.rectangle((5, 0, 10, 15), fill=4)
        d.line((11, 0, 11, 15), fill=2)
        for x, y, length in ((5, 1, 4), (8, 8, 5), (10, 3, 3)):
            y = (y + phase * 3) % 16
            d.line((x, y, x, min(15, y+length)), fill=6)
            d.point((x, y), fill=7)
        d.line((3, 12+phase, 4, 12+phase), fill=7)
    else:
        d.rectangle((0, 0, 15, 1), fill=2)
        d.line((0, 2, 15, 2), fill=4)
        for x, y, width in ((1, 5, 4), (9, 10, 5), (2, 14, 3)):
            x = (x + phase) % 12
            d.line((x, y, min(15, x+width), y), fill=5)
            d.line((x+1, y+1, min(15, x+width-1), y+1), fill=4)
        d.line((2+phase, 5, 4+phase, 5), fill=6)
        d.point((10+phase, 10), fill=7)
    if stage == 1:
        d.line((2, 7+phase, 5, 7+phase), fill=10)
    elif stage == 2:
        d.line((5, 7+phase, 10, 7+phase), fill=12)
        d.line((7, 7+phase, 9, 7+phase), fill=13)
        d.point((8, 7+phase), fill=14)
    return im


def prop(kind='mold', stage=0, phase=0):
    stage = _stage(stage)
    im, d = _canvas()
    if kind == 'mold':
        d.polygon([(1, 14), (3, 10), (6, 9), (8, 11), (12, 9), (15, 12), (14, 15), (3, 15)], fill=1)
        for x, y, w in ((2, 10, 6), (7, 7, 6), (10, 11, 5)):
            d.polygon([(x, y+1), (x+2, y), (x+w-1, y+1), (x+w, y+3), (x, y+3)], fill=12 if stage == 2 else 9)
            d.line((x+1, y+1, x+w-2, y+1), fill=13 if stage == 2 else 11)
            d.line((x+1, y+3, x+w-1, y+3), fill=1)
        if stage == 2:
            d.point((9, 8), fill=14)
    elif kind == 'lamp':
        # A small hanging censer, with separate bowl and warm flame.
        d.line((7, 0, 7, 4), fill=5)
        d.line((4, 3, 11, 3), fill=1)
        d.line((4, 4, 4, 9), fill=6)
        d.line((11, 4, 11, 9), fill=3)
        d.polygon([(2, 9), (13, 9), (11, 13), (5, 13)], fill=1)
        d.line((3, 9, 12, 9), fill=7)
        d.line((5, 11, 11, 11), fill=5)
        d.point((5, 10), fill=8)
        if phase:
            d.polygon([(6, 8), (6, 6), (8, 3), (10, 7), (9, 8)], fill=5)
            d.line((7, 7, 8, 5), fill=8)
        else:
            d.line((6, 8, 9, 8), fill=3)
            d.point((7, 7), fill=4)
        d.line((7, 14, 9, 14), fill=3)
    elif kind == 'shrine':
        d.ellipse((1, 12, 14, 15), fill=1)
        d.rectangle((3, 10, 12, 13), fill=3)
        d.line((3, 10, 12, 10), fill=7)
        d.polygon([(4, 9), (4, 4), (8, 0), (12, 4), (12, 9)], fill=1)
        d.polygon([(5, 9), (5, 4), (8, 2), (10, 4), (10, 9)], fill=6)
        d.line([(5, 7), (5, 4), (8, 1)], fill=8)
        d.ellipse((7, 4, 9, 7), fill=1)
        d.point((8, 5), fill=14 if stage == 2 else 7)
        d.line((6, 12, 10, 12), fill=5)
    elif kind == 'switch':
        # Full tile backing prevents accidental alpha holes in this floor.
        im, d = _canvas(fill=3)
        d.rectangle((0, 0, 15, 15), fill=3)
        d.line((0, 0, 15, 0), fill=5)
        d.line((0, 0, 0, 15), fill=5)
        d.rectangle((2, 3 if not phase else 5, 13, 13), fill=1)
        d.rectangle((3, 3 if not phase else 5, 12, 11 if not phase else 12), fill=6 if not phase else 10)
        d.line((3, 3 if not phase else 5, 12, 3 if not phase else 5), fill=8 if not phase else 11)
        if not phase:
            d.line((3, 12, 12, 12), fill=4)
        else:
            d.line((4, 6, 11, 6), fill=7)
    elif kind == 'trial':
        d.ellipse((1, 12, 14, 15), fill=1)
        d.rectangle((3, 10, 12, 12), fill=4)
        d.line((3, 10, 12, 10), fill=7)
        d.polygon([(5, 9), (4, 5), (8, 0), (12, 5), (11, 9)], fill=1)
        d.polygon([(6, 8), (6, 5), (8, 2), (10, 5), (10, 8)], fill=5)
        d.line([(6, 5), (8, 2), (9, 4)], fill=8)
        d.line((8, 5, 8, 7), fill=7)
        d.line((6, 13, 10, 13), fill=3)
    elif kind == 'cache':
        d.ellipse((1, 12, 14, 15), fill=1)
        d.polygon([(2, 12), (2, 7), (6, 4), (12, 5), (14, 8), (13, 13)], fill=1)
        d.polygon([(3, 7), (6, 5), (11, 6), (12, 8), (7, 10)], fill=7)
        d.polygon([(3, 8), (7, 11), (7, 13), (3, 12)], fill=4)
        d.polygon([(8, 10), (13, 8), (12, 12), (8, 13)], fill=5)
        d.line((5, 6, 10, 7), fill=8)
        d.line((8, 6, 6, 9), fill=3)
        d.point((7, 10), fill=8)
    elif kind == 'ward':
        # One brass lock, not a field of decorative rune dots.
        d.polygon([(2, 14), (2, 6), (5, 2), (11, 2), (14, 6), (14, 14)], fill=1)
        d.polygon([(3, 13), (3, 6), (6, 3), (10, 3), (13, 6), (13, 13)], fill=5)
        d.line([(3, 10), (3, 6), (6, 3), (10, 3)], fill=8)
        d.line((4, 13, 12, 13), fill=3)
        d.ellipse((6, 5, 10, 9), fill=1)
        d.polygon([(7, 8), (9, 8), (10, 12), (6, 12)], fill=1)
        d.point((6, 6), fill=3)
        if stage == 2:
            d.line((12, 7, 12, 10), fill=13)
            d.point((12, 8), fill=14)
    elif kind == 'thorn':
        d.ellipse((1, 12, 14, 15), fill=1)
        stems = [[(3, 14), (5, 9), (4, 4), (1, 2)], [(7, 14), (9, 9), (9, 3), (12, 1)], [(11, 14), (12, 10), (15, 7)]]
        for points in stems:
            d.line(points, fill=1, width=3)
            d.line(points, fill=12 if stage == 2 else 3)
        for points in ([(5, 10), (1, 7), (3, 11)], [(9, 7), (13, 4), (10, 9)], [(11, 13), (15, 10), (13, 14)], [(4, 5), (7, 2), (6, 7)]):
            d.polygon(points, fill=13 if stage == 2 else 5)
            d.point(points[1], fill=14 if stage == 2 else 7)
    elif kind == 'web':
        spokes = [((0, 1), (15, 15)), ((15, 1), (1, 15)), ((8, 0), (8, 15)), ((0, 8), (15, 8))]
        rings = [[(3, 4), (7, 3), (12, 4), (13, 8), (12, 12), (8, 13), (3, 12), (2, 8), (3, 4)], [(5, 6), (8, 5), (10, 6), (11, 8), (10, 10), (8, 11), (5, 10), (4, 8), (5, 6)]]
        # A one-pixel cast shadow keeps pale silk legible on ivory paving.
        for points in spokes + rings:
            d.line([(x+1, y+1) for x, y in points], fill=3)
        for points in spokes:
            d.line(points, fill=7)
        for points in rings:
            d.line(points, fill=6)
        d.line((3, 4, 7, 3), fill=8)
        d.line((1, 1, 4, 4), fill=8)
    elif kind == 'crack':
        d.polygon([(0, 15), (0, 6), (3, 2), (11, 1), (15, 5), (15, 15)], fill=1)
        d.polygon([(1, 13), (1, 6), (4, 3), (11, 2), (14, 6), (14, 13)], fill=4)
        d.polygon([(1, 6), (4, 3), (10, 3), (8, 6), (4, 8)], fill=6)
        d.line([(8, 2), (7, 6), (10, 8), (7, 11), (8, 15)], fill=1, width=2)
        d.line([(6, 6), (3, 7), (1, 10)], fill=1)
        d.line([(10, 8), (13, 7), (15, 8)], fill=1)
        d.line([(8, 3), (8, 5)], fill=8)
        d.line([(9, 9), (7, 12)], fill=7)
        d.line((3, 4, 5, 3), fill=8)
        if stage == 2:
            d.point((8, 10), fill=14)
    return im


def chest(opened=False):
    """Compact reliquary coffer: twenty-two pixels wide, readable lid/latch."""
    im, d = _canvas((32, 32))
    d.ellipse((4, 27, 28, 30), fill=1)
    d.polygon([(5, 26), (5, 13), (8, 9), (23, 9), (26, 13), (26, 26), (23, 28), (8, 28)], fill=1)
    d.rectangle((6, 16, 25, 25), fill=3)
    d.rectangle((8, 18, 22, 25), fill=4)
    d.rectangle((23, 17, 25, 25), fill=2)
    for x in (11, 17):
        d.line((x, 19, x, 24), fill=3)
    d.line((6, 26, 24, 26), fill=5)
    d.line((7, 27, 23, 27), fill=3)
    if opened:
        d.polygon([(5, 13), (5, 6), (8, 3), (22, 3), (26, 7), (26, 13)], fill=1)
        d.polygon([(7, 11), (7, 6), (9, 4), (21, 4), (24, 7), (24, 11)], fill=4)
        d.line((8, 5, 21, 5), fill=8)
        d.rectangle((7, 13, 24, 18), fill=1)
        d.line((8, 19, 23, 19), fill=6)
        d.line((9, 7, 21, 7), fill=3)
    else:
        d.polygon([(6, 14), (8, 10), (11, 8), (21, 8), (24, 11), (25, 14)], fill=5)
        d.polygon([(8, 12), (11, 9), (21, 9), (23, 11), (23, 12)], fill=6)
        d.line((11, 9, 20, 9), fill=8)
        d.line((7, 15, 24, 15), fill=1)
        d.line((7, 14, 24, 14), fill=7)
    for x in (8, 21):
        if opened:
            d.rectangle((x, 6, x+2, 11), fill=5)
            d.line((x, 7, x, 11), fill=8)
            d.rectangle((x, 19, x+2, 25), fill=5)
            d.line((x, 19, x, 25), fill=8)
        else:
            d.rectangle((x, 10, x+2, 25), fill=5)
            d.line((x, 11, x, 25), fill=8)
        d.point((x+1, 24), fill=2)
    d.rectangle((13, 18, 18, 22), fill=1)
    d.rectangle((14, 18, 17, 21), fill=7)
    d.point((14, 18), fill=8)
    if not opened:
        d.point((15, 19), fill=1)
        d.point((15, 20), fill=1)
    return im


def pit(stage=0):
    stage = _stage(stage)
    im = floor(stage)
    d = ImageDraw.Draw(im)
    d.polygon([(1, 5), (4, 2), (12, 2), (15, 5), (15, 13), (12, 15), (3, 15), (0, 12), (0, 7)], fill=2)
    d.polygon([(2, 6), (5, 4), (11, 4), (14, 6), (14, 12), (11, 14), (4, 14), (1, 11)], fill=1)
    d.line([(1, 5), (4, 2), (12, 2)], fill=7)
    d.line((4, 3, 11, 3), fill=4)
    d.line((4, 15, 11, 15), fill=3)
    if stage == 2:
        d.line((12, 6, 13, 7), fill=12)
        d.point((13, 7), fill=13)
    return im
