"""Curdstone Karst: native indexed study of porous ivory mountain terraces.

All construction is on the final 16px grid (32px for the two-column cliff
master, 32x48 for entrances).  The quiet walking stone, rounded shelf tops,
black undercuts and brass staples have separate value and shape vocabularies.
This exploratory direction supplies paintings only; cream_terrain owns IDs,
collision, animation metadata and the eventual selected-style assembly.
"""
from PIL import Image, ImageDraw


PALETTES = {
    'cream_floor0': ['#000000','#302830','#686050','#b0a080','#ded0a8','#eee0c0','#c8b890','#f8efd0','#f8f8e0','#687060','#909878','#b8c090','#484048','#785080','#c068d0','#f8d8f8'],
    'cream_floor1': ['#000000','#302830','#605848','#a09878','#c8c498','#ded8b0','#b0b080','#f0e8c8','#f8f0d8','#586048','#788860','#a8b080','#403840','#705078','#b860d0','#f0d0f8'],
    'cream_floor2': ['#000000','#281828','#585048','#989078','#b8b098','#d0c8b0','#a09880','#e0d8c0','#f0e8d0','#484848','#686858','#909078','#403048','#783898','#c850e8','#f8d8f8'],
    'cream_cliff0': ['#000000','#282028','#484038','#786850','#a09070','#c0b088','#d8c8a0','#eee0b8','#f8f0d8','#485048','#788060','#c8a050','#483848','#785080','#c068d0','#f8e8f8'],
    'cream_cliff1': ['#000000','#282028','#403c30','#686048','#888060','#a8a078','#c8c090','#e0d8a8','#f0e8c8','#404838','#687850','#c0a050','#403048','#784888','#c058d8','#f8e0f8'],
    'cream_cliff2': ['#000000','#201820','#382830','#504038','#706050','#988068','#b8a888','#d0c0a0','#f0e0c0','#383038','#585048','#c0a050','#482050','#8830a8','#d858f0','#f8d8f8'],
    'cream_water': ['#000000','#282830','#384840','#506050','#708068','#98a088','#c0c8a0','#e0e0b8','#f8f0d0','#485850','#687870','#a0b098','#483850','#784088','#b858d8','#f0d0f8'],
    'cream_props': ['#000000','#282028','#504030','#887050','#b0a080','#b88840','#d8c8a0','#e8c870','#f8f0d0','#485840','#708858','#a8b880','#483048','#8840a0','#d860e8','#f8e0f8'],
}
# GBA DAC values, deliberately authored then floored to five bits.
PALETTES = {n: ['#%02x%02x%02x' % tuple(int(c[i:i+2], 16)//8*8
              for i in (1, 3, 5)) for c in bank] for n, bank in PALETTES.items()}


def _new(size=(16, 16), fill=0, palette='cream_props'):
    image = Image.new('P', size, fill)
    values = [int(c[i:i+2], 16) for c in PALETTES[palette] for i in (1, 3, 5)]
    image.putpalette(values + [0]*(768-len(values)))
    image.info['transparency'] = 0
    return image, ImageDraw.Draw(image)


def _pore(d, x, y, w=3, h=2, large=False):
    """One attached, bevelled cavity, with light along its lower lip."""
    d.ellipse((x, y, x+w, y+h), fill=2)
    if large:
        d.line((x+1, y+1, x+w-1, y+1), fill=1)
    d.line((x+1, y+h+1, x+w-1, y+h+1), fill=5)


def floor(stage=0, variant=0, path=False):
    image, d = _new(fill=4, palette='cream_floor%d' % stage)
    v = variant % 4
    # Eroded shallow plates, with detail clustered inside the cell.  The
    # edges remain the same substrate, so any permutation tiles cleanly.
    if v == 0:
        d.line([(3, 10), (6, 10), (8, 9), (11, 9)], fill=6)
        d.line((5, 11, 8, 11), fill=5)
        d.point((3, 9), fill=3)
    elif v == 1:
        d.polygon([(2, 4), (5, 3), (8, 4), (7, 6), (3, 6)], fill=6)
        d.line((3, 3, 5, 3), fill=5)
        d.line([(5, 5), (7, 6), (10, 6)], fill=3)
        d.point((10, 7), fill=6)
    elif v == 2:
        d.line([(8, 3), (8, 5), (6, 7), (7, 9)], fill=3)
        d.line([(9, 4), (9, 6), (7, 8)], fill=5)
        d.line((3, 11, 5, 11), fill=6)
    else:
        d.polygon([(7, 9), (11, 8), (13, 9), (12, 12), (9, 12)], fill=6)
        d.line((8, 8, 11, 8), fill=5)
        d.line([(10, 9), (11, 10), (13, 10)], fill=3)
    if path:
        # Broad polished scuffs, on the same stone rather than a boxed path.
        d.line((3, 6+v, 8, 6+v), fill=5)
        d.line((7, 12-v, 11, 12-v), fill=6)
    if stage == 1 and v == 3:
        d.line([(9, 11), (11, 12), (13, 11)], fill=10)
        d.point((12, 12), fill=9)
    elif stage == 2 and v == 3:
        d.line([(8, 11), (10, 10), (12, 11), (13, 9)], fill=12)
        d.line((10, 11, 12, 11), fill=13)
        d.point((12, 10), fill=14)
    return image


def _shelves(stage):
    """A native 32x16 master: complementary columns of one rounded shelf."""
    image, d = _new((32, 16), 3, 'cream_cliff%d' % stage)
    # Broad upper-left lit planes terminate in heavy overhanging bellies.
    d.polygon([(0, 0), (31, 0), (31, 4), (27, 4), (25, 5),
               (21, 5), (18, 4), (13, 4), (10, 5), (5, 5), (2, 4), (0, 4)], fill=5)
    d.polygon([(0, 0), (31, 0), (31, 2), (27, 2), (24, 3),
               (20, 3), (17, 2), (13, 2), (10, 3), (5, 3), (2, 2), (0, 2)], fill=6)
    d.line([(0, 0), (5, 0), (8, 1), (13, 0), (20, 0), (23, 1), (27, 0), (31, 0)], fill=7)
    d.line([(0, 5), (3, 5), (5, 6), (10, 6), (13, 5),
            (18, 5), (21, 6), (25, 6), (28, 5), (31, 5)], fill=1, width=2)
    d.line([(0, 7), (4, 7), (7, 8), (12, 8), (15, 7),
            (19, 7), (22, 8), (27, 8), (30, 7), (31, 7)], fill=2)
    # Second, asymmetric shelf turns out of the recess rather than forming
    # a featureless stripe. Both outer edges have identical entry heights.
    d.polygon([(0, 9), (4, 9), (7, 8), (13, 8), (17, 10),
               (21, 10), (24, 9), (29, 9), (31, 9), (31, 12),
               (28, 13), (23, 13), (21, 14), (17, 14), (13, 12),
               (8, 12), (5, 13), (1, 12), (0, 12)], fill=4)
    d.line([(0, 9), (4, 9), (7, 8), (12, 8), (16, 10),
            (20, 10), (24, 9), (29, 9), (31, 9)], fill=6)
    d.line([(1, 10), (5, 10), (8, 9), (11, 9)], fill=7)
    d.line([(0, 13), (3, 14), (6, 14), (9, 13), (13, 13),
            (17, 15), (22, 15), (25, 14), (29, 14), (31, 13)], fill=1, width=2)
    # Cup-shaped voids have coherent size groups; they are not random dots.
    # Unequal groups leave long quiet planes between the porous pockets.
    # Their offset upper/lower positions avoid a dotted horizontal border.
    for x, y, w, h in ((5, 1, 5, 2), (11, 2, 2, 1),
                       (24, 10, 5, 2)):
        _pore(d, x, y, w, h, w > 3)
    d.line((21, 1, 26, 1), fill=7)
    d.line((2, 10, 5, 10), fill=6)
    d.line((17, 6, 17, 8), fill=9)
    d.line((18, 7, 18, 9), fill=10)
    d.point((18, 10), fill=6)
    if stage == 1:
        d.polygon([(13, 4), (17, 4), (19, 7), (17, 10), (14, 9)], fill=9)
        d.line([(14, 4), (15, 7), (17, 8)], fill=10)
        d.line((28, 5, 28, 8), fill=9)
    elif stage == 2:
        # Missing shelf chunks and erupting seam matter as much as the bank.
        d.polygon([(12, 0), (16, 0), (15, 3), (18, 5), (16, 8),
                   (13, 7), (14, 4), (11, 3)], fill=1)
        d.line([(14, 1), (13, 3), (16, 5), (14, 8), (17, 10),
                (18, 13), (22, 15)], fill=12, width=3)
        d.line([(14, 1), (13, 3), (16, 5), (14, 8), (17, 10), (18, 13)], fill=13)
        d.line([(14, 3), (16, 5), (15, 7)], fill=14)
        d.point((16, 5), fill=15)
        d.polygon([(25, 9), (28, 9), (27, 12), (24, 13)], fill=1)
        d.line((25, 10, 25, 12), fill=13)
    return image


def cliff(stage=0, kind='mid', variant=0):
    master = _shelves(stage)
    x = (variant % 2)*16
    image = master.crop((x, 0, x+16, 16)); d = ImageDraw.Draw(image)
    if kind == 'top':
        d.rectangle((0, 0, 15, 3), fill=6)
        d.line((0, 0, 15, 0), fill=8)
        d.line([(0, 4), (3, 4), (5, 5), (10, 5), (13, 4), (15, 4)], fill=7)
        d.line([(0, 5), (3, 5), (5, 6), (10, 6), (13, 5), (15, 5)], fill=1)
        _pore(d, 7 if variant % 2 else 2, 1, 3, 1)
    elif kind == 'base':
        d.polygon([(0, 10), (3, 10), (5, 11), (8, 10), (11, 11),
                   (15, 10), (15, 15), (0, 15)], fill=2)
        d.polygon([(0, 11), (3, 11), (5, 13), (9, 11), (12, 12),
                   (15, 11), (15, 14), (10, 14), (7, 13), (3, 14), (0, 13)], fill=4)
        d.line([(0, 11), (3, 11), (5, 12), (8, 11)], fill=6)
        d.point((15, 11), fill=6)
        d.point((15, 14), fill=2)
        d.line((0, 15, 15, 15), fill=1)
    elif kind == 'left':
        d.polygon([(0, 0), (2, 0), (3, 4), (2, 8), (3, 12),
                   (2, 15), (0, 15)], fill=2)
        d.line([(3, 0), (4, 3), (3, 7), (4, 11), (3, 15)], fill=7)
    elif kind == 'right':
        d.polygon([(13, 0), (15, 0), (15, 15), (12, 15),
                   (13, 12), (12, 9), (13, 5)], fill=1)
        d.line([(12, 0), (12, 4), (11, 8), (12, 12), (11, 15)], fill=3)
    return image


def climb(stage=0, kind='mid'):
    image = cliff(stage, 'mid', 0); d = ImageDraw.Draw(image)
    d.rectangle((3, 0, 12, 15), fill=2)
    d.line((3, 0, 3, 15), fill=1)
    d.line((4, 0, 4, 15), fill=4)
    d.line((12, 0, 12, 15), fill=6)
    # Deliberately regular four-pixel cadence; no natural wall has these.
    for y in (2, 6, 10, 14):
        d.line((5, y+1, 11, y+1), fill=1)
        d.line((5, y-1, 5, y), fill=11)
        d.line((10, y-1, 10, y), fill=11)
        d.line((5, y, 10, y), fill=11)
        d.line((5, y-1, 9, y-1), fill=8)
    if kind == 'top':
        d.line((0, 0, 15, 0), fill=7)
        d.point((1, 0), fill=8)
    elif kind == 'bottom':
        d.line((2, 15, 13, 15), fill=1)
        d.line((4, 14, 11, 14), fill=8)
    return image


def rim(stage=0, variant=0, drop=False):
    image = floor(stage, variant); d = ImageDraw.Draw(image)
    if drop:
        # A low walk-off sill and visible void, without a raised barricade.
        d.rectangle((0, 12, 15, 15), fill=1)
        d.line([(0, 10), (4, 10), (6, 11), (10, 11), (13, 10), (15, 10)], fill=7)
        d.line([(0, 11), (4, 11), (6, 12), (10, 12), (13, 11), (15, 11)], fill=6)
        d.line((6, 13, 10, 13), fill=2)
    else:
        # Thick upright calcite teeth are an unmistakable permanent stop.
        d.polygon([(0, 9), (2, 6), (5, 5), (8, 7), (10, 5),
                   (13, 5), (15, 7), (15, 15), (0, 15)], fill=2)
        d.polygon([(0, 8), (2, 5), (5, 4), (8, 6), (10, 4),
                   (13, 4), (15, 6), (15, 10), (12, 11),
                   (9, 10), (7, 11), (3, 10), (0, 10)], fill=6)
        d.line([(0, 8), (2, 5), (5, 4), (7, 5)], fill=8)
        d.line([(9, 6), (10, 4), (13, 4), (14, 5)], fill=7)
        d.line([(0, 11), (4, 12), (7, 12), (9, 11), (12, 12), (15, 11)], fill=1, width=2)
        d.ellipse((3, 7, 5, 8), fill=2)
        d.line((11, 7, 12, 7), fill=3)
        if stage == 2:
            d.line([(8, 6), (7, 8), (9, 10), (8, 12)], fill=12)
            d.point((8, 9), fill=14)
    return image


def cave(stage=0):
    image, d = _new((32, 48), palette='cream_cliff%d' % stage)
    # An irregular cavern arch is cut into three thick calcite shelves.
    outer = [(0, 47), (0, 21), (3, 13), (7, 7), (12, 3),
             (20, 2), (26, 6), (30, 15), (31, 24), (31, 47)]
    d.polygon(outer, fill=1)
    d.polygon([(1, 45), (2, 21), (5, 13), (9, 7), (14, 4),
               (20, 4), (25, 8), (28, 16), (30, 25), (29, 45)], fill=4)
    d.polygon([(3, 20), (6, 12), (11, 6), (16, 4), (22, 5),
               (26, 10), (26, 14), (21, 10), (15, 9), (10, 14), (7, 22)], fill=6)
    d.line([(4, 18), (7, 11), (12, 6), (17, 5), (21, 5)], fill=8)
    d.line([(1, 24), (5, 24), (7, 22)], fill=1, width=2)
    d.line([(25, 22), (28, 23), (31, 23)], fill=1, width=2)
    d.polygon([(7, 46), (7, 24), (8, 20), (11, 15), (14, 13),
               (19, 13), (22, 15), (25, 21), (26, 26), (26, 46)], fill=1)
    # Soft inner facet at left; the opening itself remains a single dark mass.
    d.line([(8, 29), (8, 23), (11, 17), (15, 14), (18, 13)], fill=2)
    d.line([(10, 23), (12, 19), (16, 16)], fill=3)
    for y in (29, 37):
        d.polygon([(1, y), (4, y-1), (7, y), (7, y+2), (3, y+3), (1, y+2)], fill=5)
        d.line((1, y, 5, y-1), fill=7)
        d.line((1, y+4, 6, y+3), fill=1)
        d.line((27, y+1, 30, y), fill=5)
        d.line((27, y+3, 30, y+3), fill=2)
    for x, y, w, h in ((7, 11, 2, 2), (14, 6, 3, 1), (22, 7, 2, 2),
                       (3, 26, 2, 1), (27, 33, 2, 2), (2, 39, 3, 1)):
        _pore(d, x, y, w, h, True)
    d.rectangle((8, 41, 25, 44), fill=2)
    d.polygon([(5, 45), (10, 43), (23, 43), (28, 46), (27, 47), (5, 47)], fill=6)
    d.line((8, 44, 23, 44), fill=8)
    d.line((6, 47, 27, 47), fill=4)
    if stage == 1:
        d.line([(27, 12), (28, 19), (27, 24), (29, 30), (28, 36)], fill=9, width=2)
        d.line((28, 17, 28, 23), fill=10)
    elif stage == 2:
        d.polygon([(23, 5), (26, 6), (27, 11), (25, 14), (23, 11)], fill=1)
        d.line([(24, 7), (24, 12), (27, 17), (26, 23), (28, 28), (27, 36)], fill=12, width=3)
        d.line([(24, 7), (24, 12), (27, 17), (26, 23), (28, 28), (27, 36)], fill=13)
        d.line((26, 19, 26, 23), fill=14)
        d.point((27, 28), fill=15)
    return image


def water(stage=0, phase=0, fall=False):
    image, d = _new(fill=3, palette='cream_water')
    p = phase % 2
    if fall:
        d.rectangle((0, 0, 2, 15), fill=1)
        d.rectangle((3, 0, 4, 15), fill=2)
        d.rectangle((12, 0, 15, 15), fill=2)
        d.line((5, 0, 5, 15), fill=5)
        d.line((10, 0, 10, 15), fill=4)
        for y in (p*3, 8+p*3):
            d.line((6, y, 8, y+2), fill=6)
            d.line((9, y+3, 10, y+5), fill=5)
    else:
        d.line([(0, 3), (3, 3), (5, 2), (9, 2), (11, 3), (15, 3)], fill=2)
        d.line((2+p, 5, 6+p, 5), fill=5)
        d.line((3+p, 6, 7+p, 6), fill=4)
        d.line((9-p, 12, 13-p, 12), fill=5)
        d.line((10-p, 13, 13-p, 13), fill=4)
    if stage == 1:
        d.line((2, 9, 5, 9), fill=9)
        d.point((4, 8), fill=10)
    elif stage == 2:
        d.line((6, 7+p, 10, 7+p), fill=12)
        d.line((7, 7+p, 9, 7+p), fill=13)
        d.point((8, 7+p), fill=14)
    return image


def prop(kind='mold', stage=0, phase=0):
    image, d = _new()
    if kind == 'mold':
        d.ellipse((1, 11, 14, 15), fill=1)
        for x, y, w in ((2, 9, 6), (7, 6, 7), (4, 3, 6)):
            d.ellipse((x, y, x+w, y+5), fill=12 if stage == 2 else 9)
            d.ellipse((x, y, x+w, y+3), fill=13 if stage == 2 else 11)
            d.line((x+1, y+1, x+w-1, y+1), fill=14 if stage == 2 else 6)
            d.line((x+2, y+2, x+w-2, y+2), fill=12 if stage == 2 else 10)
    elif kind == 'lamp':
        d.ellipse((4, 13, 12, 15), fill=1)
        d.rectangle((7, 9, 9, 13), fill=2)
        d.line((7, 10, 7, 13), fill=5)
        d.polygon([(3, 5), (5, 2), (9, 1), (12, 4), (12, 10), (9, 12), (4, 10)], fill=1)
        d.rectangle((5, 4, 10, 9), fill=5)
        d.rectangle((6, 5, 9, 8), fill=7 if phase else 4)
        d.line((4, 4, 11, 4), fill=7)
        d.line((5, 9, 10, 9), fill=5)
        d.line((7, 4, 7, 9), fill=2)
        if phase:d.point((8, 6), fill=8)
    elif kind == 'shrine':
        d.ellipse((1, 12, 14, 15), fill=1)
        d.polygon([(2, 10), (7, 8), (13, 10), (12, 13), (3, 13)], fill=4)
        d.line((3, 10, 10, 9), fill=6)
        d.rectangle((6, 5, 9, 10), fill=5)
        d.polygon([(3, 4), (6, 5), (8, 2), (10, 5), (13, 4), (11, 8), (5, 8)], fill=1)
        d.line([(4, 4), (6, 6), (8, 3), (10, 6), (12, 4)], fill=7)
        d.line((6, 7, 10, 7), fill=5)
        d.point((8, 2), fill=8)
    elif kind == 'switch':
        # The engine draws a plate as a full floor cell, not an alpha prop.
        d.rectangle((0, 0, 15, 15), fill=4)
        d.polygon([(1, 5), (5, 2), (11, 2), (15, 6), (14, 12), (10, 15), (4, 14), (0, 10)], fill=2)
        d.polygon([(2, 5), (5, 3), (11, 3), (14, 6), (13, 10), (10, 12), (4, 12), (1, 9)], fill=6)
        d.line([(2, 5), (5, 3), (10, 3)], fill=8)
        d.ellipse((4, 5+bool(phase), 11, 10+bool(phase)), fill=9 if phase else 3)
        d.line((5, 6+bool(phase), 10, 6+bool(phase)), fill=11 if phase else 7)
        d.point((7, 8+bool(phase)), fill=8 if phase else 5)
    elif kind == 'trial':
        d.ellipse((1, 12, 14, 15), fill=1)
        d.polygon([(3, 11), (6, 9), (11, 10), (13, 13), (3, 13)], fill=4)
        d.line((3, 11, 10, 10), fill=6)
        d.polygon([(5, 8), (5, 4), (8, 0), (12, 5), (11, 9), (8, 11)], fill=1)
        d.polygon([(6, 5), (8, 2), (10, 5), (8, 8)], fill=7)
        d.polygon([(8, 8), (10, 5), (10, 8), (8, 10)], fill=5)
        d.line((7, 5, 8, 3), fill=8)
    elif kind == 'cache':
        d.ellipse((1, 11, 14, 15), fill=1)
        d.polygon([(2, 8), (5, 5), (11, 5), (14, 9), (12, 13), (3, 13)], fill=3)
        d.polygon([(2, 8), (5, 5), (10, 5), (12, 8), (10, 10), (4, 10)], fill=6)
        d.line((4, 6, 9, 6), fill=8)
        d.line((7, 5, 8, 12), fill=2)
        d.rectangle((6, 8, 9, 10), fill=5)
        d.line((6, 8, 8, 8), fill=7)
    elif kind == 'ward':
        # Broad lock plate and unmistakable circular-bow/keyhole stem.
        d.polygon([(2, 3), (7, 0), (13, 3), (14, 11), (8, 15), (1, 11)], fill=1)
        d.polygon([(3, 4), (7, 2), (12, 4), (12, 10), (8, 13), (3, 10)], fill=12)
        d.line([(3, 4), (7, 2), (11, 4)], fill=13)
        d.ellipse((4, 4, 11, 11), fill=5)
        d.line((5, 4, 9, 4), fill=8)
        d.ellipse((6, 5, 9, 8), fill=1)
        d.polygon([(7, 7), (8, 7), (9, 10), (6, 10)], fill=1)
        d.point((12, 6), fill=14)
    elif kind == 'thorn':
        d.ellipse((1, 12, 14, 15), fill=1)
        branches = [[(2, 13), (4, 9), (3, 3)], [(4, 10), (8, 12), (11, 9), (12, 3)],
                    [(7, 12), (7, 6), (9, 1)], [(10, 10), (14, 7)]]
        for pts in branches:d.line(pts, fill=1, width=3)
        for pts in branches:d.line(pts, fill=12 if stage == 2 else 9)
        for poly in ([(3, 8), (0, 6), (3, 6)], [(7, 8), (11, 5), (8, 6)],
                     [(11, 7), (15, 4), (12, 5)], [(6, 12), (3, 14), (5, 11)]):
            d.polygon(poly, fill=13 if stage == 2 else 10)
        d.point((9, 1), fill=14 if stage == 2 else 6)
    elif kind == 'web':
        # Off-center suspended web: radial spokes plus three curved rings.
        ends = ((1, 1), (8, 0), (14, 2), (15, 9), (12, 15), (3, 15), (0, 9))
        # Tiny attached fibre shadows keep ivory silk legible over ivory rock.
        for ex, ey in ends:
            d.line((8, 9, ex+1, ey+1), fill=2)
        d.line([(4, 5), (8, 4), (12, 5), (13, 9), (11, 13), (6, 13), (3, 10), (4, 5)], fill=2)
        for end in ends:
            d.line((7, 8, *end), fill=6)
        d.line([(3, 4), (7, 3), (11, 4), (12, 8), (10, 12), (5, 12), (2, 9), (3, 4)], fill=6)
        d.line([(5, 6), (7, 5), (9, 6), (10, 8), (9, 10), (6, 10), (4, 9), (5, 6)], fill=8)
        d.line([(1, 2), (7, 1), (13, 3)], fill=8)
        if stage == 2:d.line((7, 8, 11, 12), fill=13)
    elif kind == 'crack':
        d.polygon([(0, 15), (1, 6), (4, 2), (11, 1), (15, 5), (15, 15)], fill=1)
        d.polygon([(1, 13), (2, 6), (5, 3), (11, 2), (14, 6), (13, 14)], fill=4)
        d.polygon([(2, 6), (5, 3), (10, 2), (12, 4), (10, 6), (5, 7)], fill=6)
        d.line([(9, 2), (7, 5), (9, 7), (6, 10), (8, 13), (6, 15)], fill=1, width=2)
        d.line([(8, 7), (11, 9), (13, 8)], fill=2)
        d.line((4, 4, 6, 3), fill=8)
        d.line((2, 14, 5, 13), fill=3)
        if stage == 2:d.line([(8, 7), (7, 9), (8, 11)], fill=13)
    return image


def chest(opened=False):
    image, d = _new((32, 32))
    # Twenty-two pixels across: round coopered lid and flat framed front.
    d.ellipse((5, 27, 27, 31), fill=1)
    d.polygon([(5, 27), (5, 16), (7, 11), (11, 9), (21, 9),
               (26, 13), (26, 27), (23, 29), (8, 29)], fill=1)
    d.rectangle((7, 17, 24, 26), fill=3)
    d.rectangle((9, 19, 22, 25), fill=4)
    d.line((15, 19, 15, 25), fill=2)
    d.line((7, 27, 24, 27), fill=5)
    if opened:
        d.polygon([(6, 15), (6, 7), (10, 4), (22, 4), (26, 8), (26, 15)], fill=1)
        d.polygon([(8, 13), (8, 8), (11, 6), (21, 6), (24, 9), (24, 13)], fill=3)
        d.line((10, 6, 21, 6), fill=7)
        d.line((8, 8, 8, 12), fill=5)
        d.rectangle((8, 15, 24, 19), fill=1)
        d.line((8, 20, 23, 20), fill=5)
    else:
        d.polygon([(6, 16), (8, 12), (12, 10), (20, 10), (24, 12), (26, 16)], fill=3)
        d.polygon([(8, 14), (10, 12), (13, 11), (20, 11), (23, 13), (24, 15)], fill=4)
        d.line((11, 11, 19, 11), fill=6)
        d.line((7, 16, 25, 16), fill=5)
    for x in (9, 21):
        d.rectangle((x, 8 if opened else 12, x+2, 27), fill=5)
        d.line((x, 8 if opened else 12, x, 25), fill=7)
        d.point((x, 18), fill=8)
    if opened:d.rectangle((9, 15, 23, 18), fill=1)
    d.rectangle((14, 19, 18, 23), fill=1)
    d.rectangle((15, 19, 18, 22), fill=7)
    d.point((16, 20), fill=1)
    d.point((16, 21), fill=1)
    return image


def pit(stage=0):
    image = floor(stage, 0); d = ImageDraw.Draw(image)
    d.ellipse((0, 2, 15, 15), fill=2)
    d.ellipse((1, 4, 14, 14), fill=1)
    d.line([(1, 5), (3, 3), (6, 2), (10, 2), (13, 4)], fill=7)
    d.line((4, 14, 11, 14), fill=3)
    d.line((3, 6, 3, 8), fill=2)
    return image
