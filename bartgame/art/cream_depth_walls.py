"""Original native Cream depth study: broad curdstone, ribs and blind bays.

These are opaque wall paintings, not terrain layouts or cave entrances.  The
room composer selects a whole footprint on dry solid cliff, then cuts literal
16x16 cells from it.  Every coordinate below is a final native game pixel.
Palette banks intentionally match Black Rind Terraces exactly.  Stages share
their material shapes; actual missing chips and widening branching fissures
make the sour/deep progression more than a palette substitution.
"""
from PIL import Image, ImageDraw

try:
    from .cream_style_rind import PALETTES as _RIND_PALETTES
except ImportError:
    from cream_style_rind import PALETTES as _RIND_PALETTES


PALETTES = {key: list(bank) for key, bank in _RIND_PALETTES.items()}

# Dimensions are gameplay metatiles, never hardware subtiles.  One large blind
# bay is deliberately scarcer than the geological spans and compact remnants.
SPECS = [
    dict(name='shelf_fold', kind='shelf', variant=0, w=4, h=2),
    dict(name='shelf_cleft', kind='shelf', variant=1, w=4, h=2),
    dict(name='fracture_slant', kind='fracture', variant=0, w=6, h=2),
    dict(name='fracture_rib', kind='fracture', variant=1, w=6, h=2),
    dict(name='blind_bay', kind='arch', variant=0, w=4, h=3),
    dict(name='compact_knuckle', kind='compact', variant=0, w=2, h=2),
    dict(name='compact_split', kind='compact', variant=1, w=2, h=2),
]


def _canvas(size, stage):
    im = Image.new('P', size, 3)
    rgb = [int(c[i:i + 2], 16) for c in PALETTES['cream_cliff%d' % stage]
           for i in (1, 3, 5)]
    im.putpalette(rgb + [0] * (768 - len(rgb)))
    return im, ImageDraw.Draw(im)


def _mould(d, points, light, shade):
    """A connected damp deposit tucked under one material overhang."""
    d.polygon(points, fill=9)
    d.polygon(shade, fill=10)
    d.line(light, fill=11)


def _crack(d, points, branches=(), stage=0, glow=(), chips=()):
    """One long stress fracture; the luminous core stays exactly one pixel."""
    # Same path in all states makes the material's failure intelligible.  The
    # widening scar consumes actual stone pixels without recolouring the body.
    d.line(points, fill=2 if stage == 0 else 1, width=1 if stage == 0 else 2)
    for path in branches:
        # Secondary stress lines fail later than the main load-bearing split.
        # This also preserves quiet material instead of multiplying equal scars.
        d.line(path, fill=2, width=1)
    if stage:
        for shape in chips[:1 if stage == 1 else len(chips)]:
            d.polygon(shape, fill=1)
    if stage == 1:
        # A dark bruise at the root; healthy/sour are not glowing wallpaper.
        d.line(points[1:-1], fill=12)
    elif stage == 2:
        for path in (points,) + tuple(branches):
            d.line(path, fill=1, width=3 if path is points else 2)
            d.line(path, fill=12, width=2 if path is points else 1)
            d.line(path[1:-1] if len(path) > 3 else path, fill=13)
        for path in glow:
            d.line(path, fill=14)
        # Tiny pale-violet contact glints belong to the vein, not the wall rim.
        if glow:
            d.point(glow[0][0], fill=15)


def _shelf(d, stage, variant):
    if variant == 0:
        # A large lifted slab and an unequal lower folded plate.  The planes
        # remain broad enough to read beside a native sixteen-pixel actor.
        d.polygon([(0, 5), (7, 3), (27, 2), (40, 6), (45, 13),
                   (39, 23), (24, 28), (4, 25), (0, 19)], fill=4)
        d.polygon([(1, 7), (8, 5), (26, 4), (38, 8), (40, 13),
                   (31, 19), (10, 20), (2, 17)], fill=5)
        d.polygon([(0, 6), (6, 3), (23, 2), (38, 5), (43, 10),
                   (40, 13), (26, 15), (8, 14), (0, 11)], fill=6)
        d.polygon([(3, 7), (10, 4), (23, 4), (32, 6), (26, 8),
                   (12, 8), (6, 10)], fill=7)
        d.line([(1, 6), (7, 3), (20, 2), (26, 3)], fill=8)
        d.polygon([(0, 12), (9, 15), (27, 16), (40, 13), (43, 11),
                   (41, 16), (29, 20), (9, 20), (0, 16)], fill=2)
        d.line([(1, 14), (11, 17), (28, 18), (39, 15)], fill=1)
        # Facets inside the mass, rather than parallel pillow-shading rings.
        d.polygon([(14, 10), (27, 8), (36, 9), (29, 12), (19, 12)], fill=5)
        d.polygon([(3, 21), (11, 22), (18, 27), (8, 26)], fill=5)
        _mould(d, [(8, 18), (17, 19), (23, 18), (27, 21), (23, 25),
                   (12, 24), (6, 22)], [(9, 19), (15, 20), (19, 20)],
               [(12, 21), (22, 20), (24, 22), (20, 23), (11, 22)])
        d.polygon([(25, 23), (31, 19), (44, 18), (57, 20), (63, 24),
                   (61, 28), (49, 30), (32, 29), (24, 26)], fill=2)
        d.polygon([(25, 22), (33, 18), (46, 17), (58, 20), (63, 23),
                   (57, 25), (43, 27), (31, 26)], fill=5)
        d.polygon([(28, 22), (36, 19), (47, 19), (55, 21),
                   (46, 23), (34, 23)], fill=6)
        d.line([(26, 22), (34, 18), (44, 17), (50, 18)], fill=7)
        d.line([(32, 28), (45, 29), (58, 27)], fill=1)
        d.polygon([(48, 3), (55, 4), (60, 9), (57, 15), (51, 14),
                   (47, 9)], fill=4)
        d.line([(49, 4), (54, 5), (56, 7)], fill=5)
        _crack(d, [(33, 5), (31, 9), (33, 12), (29, 17), (30, 21),
                   (27, 25), (28, 29)],
               ([(32, 12), (39, 10), (44, 11), (49, 9)],), stage,
               ([(30, 18), (30, 20)], [(29, 24), (28, 25)]),
               ([(31, 7), (34, 8), (34, 11), (31, 13), (30, 11)],
                [(28, 23), (31, 23), (30, 26), (27, 27)]))
    else:
        d.polygon([(0, 9), (13, 7), (27, 10), (29, 19), (20, 28),
                   (1, 29)], fill=4)
        d.polygon([(0, 7), (9, 3), (21, 4), (29, 8), (25, 11),
                   (14, 14), (2, 13), (0, 11)], fill=6)
        d.polygon([(0, 7), (9, 4), (16, 5), (22, 7), (13, 9),
                   (4, 10)], fill=7)
        d.line([(0, 6), (9, 3), (15, 3)], fill=8)
        d.polygon([(0, 13), (14, 15), (25, 12), (29, 9), (28, 15),
                   (19, 20), (4, 19), (0, 17)], fill=2)
        d.line([(1, 15), (11, 17), (19, 16), (25, 13)], fill=1)
        _mould(d, [(6, 18), (13, 18), (16, 21), (14, 26), (7, 26),
                   (3, 23)], [(5, 20), (9, 19), (12, 20)],
               [(8, 21), (12, 20), (13, 23), (10, 25), (7, 23)])
        d.polygon([(25, 7), (36, 3), (51, 4), (62, 10), (63, 22),
                   (56, 28), (41, 29), (30, 24), (23, 16)], fill=4)
        d.polygon([(27, 9), (37, 6), (49, 7), (59, 11), (56, 17),
                   (43, 23), (30, 20), (25, 16)], fill=5)
        d.polygon([(27, 8), (36, 3), (48, 4), (58, 8), (61, 13),
                   (54, 15), (39, 15), (29, 12)], fill=6)
        d.polygon([(31, 7), (38, 5), (47, 6), (52, 9), (42, 10)], fill=7)
        d.line([(27, 8), (36, 3), (43, 3)], fill=8)
        d.polygon([(30, 13), (41, 16), (56, 16), (61, 13), (59, 19),
                   (49, 22), (35, 21)], fill=2)
        d.line([(34, 16), (43, 18), (55, 18), (58, 16)], fill=1)
        d.polygon([(37, 23), (49, 22), (59, 24), (56, 27),
                   (44, 28), (37, 26)], fill=5)
        d.line([(38, 23), (47, 22), (52, 23)], fill=6)
        d.polygon([(2, 26), (7, 27), (11, 29), (2, 29)], fill=5)
        _crack(d, [(48, 5), (45, 9), (47, 12), (44, 16), (45, 21),
                   (42, 26), (43, 29)],
               ([(44, 16), (36, 18), (32, 17), (27, 19), (23, 18)],),
               stage, ([(46, 11), (47, 12)], [(44, 22), (43, 24)]),
               ([(43, 8), (47, 7), (48, 10), (46, 12), (44, 11)],
                [(42, 25), (45, 24), (46, 27), (44, 29), (41, 27)]))


def _fracture(d, stage, variant):
    if variant == 0:
        # One long lateral load-bearing shelf cuts through clotted geology.
        # It is not six small wall motifs placed next to one another.
        d.polygon([(0, 8), (11, 5), (29, 7), (42, 4), (57, 7),
                   (71, 4), (88, 7), (95, 13), (95, 27), (80, 29),
                   (65, 27), (48, 30), (29, 26), (12, 28), (0, 24)], fill=4)
        d.polygon([(0, 6), (10, 3), (28, 4), (38, 7), (49, 5),
                   (60, 7), (58, 12), (43, 15), (23, 13), (9, 15),
                   (0, 11)], fill=6)
        d.polygon([(2, 6), (11, 4), (25, 5), (32, 7), (22, 9),
                   (9, 8)], fill=7)
        d.line([(0, 6), (10, 3), (21, 3)], fill=8)
        d.polygon([(1, 12), (10, 16), (24, 14), (43, 16), (58, 13),
                   (61, 10), (59, 17), (45, 20), (26, 18), (11, 20),
                   (0, 17)], fill=2)
        d.line([(0, 14), (11, 18), (25, 16), (44, 18), (57, 15)], fill=1)
        d.polygon([(11, 22), (24, 21), (34, 25), (30, 29), (16, 29),
                   (8, 26)], fill=5)
        d.line([(10, 23), (22, 21), (28, 22)], fill=6)
        _mould(d, [(34, 18), (46, 18), (51, 22), (48, 26),
                   (36, 27), (30, 23)], [(33, 20), (39, 19), (45, 20)],
               [(37, 21), (45, 21), (47, 23), (42, 25), (35, 23)])
        d.polygon([(59, 14), (66, 7), (81, 5), (91, 8), (95, 13),
                   (91, 18), (78, 21), (64, 21), (58, 18)], fill=5)
        d.polygon([(62, 13), (69, 8), (81, 7), (90, 10), (89, 13),
                   (78, 15), (68, 16)], fill=6)
        d.line([(61, 13), (69, 7), (80, 5), (86, 6)], fill=7)
        d.line([(66, 10), (72, 7), (78, 6)], fill=8)
        d.polygon([(61, 19), (77, 22), (91, 19), (95, 15), (95, 21),
                   (82, 26), (69, 25), (60, 22)], fill=2)
        d.line([(65, 22), (77, 24), (88, 22)], fill=1)
        d.polygon([(79, 27), (89, 25), (95, 26), (95, 29), (85, 30)], fill=5)
        _crack(d, [(19, 5), (26, 10), (31, 10), (37, 14), (45, 13),
                   (51, 17), (58, 18), (64, 23), (74, 25), (80, 29)],
               ([(37, 14), (37, 20), (33, 24), (33, 29)],
                [(58, 18), (62, 14), (69, 12), (71, 8)]), stage,
               ([(45, 13), (48, 15)], [(62, 22), (64, 23)],
                [(37, 21), (35, 23)]),
               ([(35, 12), (38, 12), (40, 14), (38, 17), (35, 16)],
                [(57, 16), (62, 17), (63, 20), (60, 22), (57, 20)]))
    else:
        # A fossil rib, interrupted twice, emerges through unequal curd plates.
        d.polygon([(0, 7), (10, 4), (25, 7), (35, 14), (33, 26),
                   (16, 30), (0, 27)], fill=4)
        d.polygon([(0, 8), (8, 5), (21, 7), (30, 13), (23, 17),
                   (8, 16), (0, 13)], fill=5)
        d.polygon([(1, 7), (9, 4), (20, 6), (26, 10), (19, 11),
                   (6, 10)], fill=6)
        d.line([(0, 7), (9, 4), (15, 5)], fill=7)
        d.polygon([(0, 15), (10, 18), (25, 17), (31, 13), (29, 20),
                   (20, 23), (7, 22), (0, 19)], fill=2)
        d.line([(1, 18), (11, 20), (22, 19)], fill=1)
        _mould(d, [(7, 23), (18, 22), (24, 25), (22, 29), (10, 29),
                   (4, 27)], [(7, 24), (14, 23), (19, 24)],
               [(9, 25), (18, 24), (20, 27), (13, 28), (8, 27)])
        d.polygon([(28, 3), (35, 2), (40, 8), (39, 16), (42, 24),
                   (40, 30), (35, 29), (34, 22), (31, 17), (32, 9)], fill=2)
        d.polygon([(28, 3), (32, 2), (35, 8), (34, 16), (38, 23),
                   (37, 29), (34, 27), (33, 21), (30, 16), (31, 9)], fill=6)
        d.line([(28, 3), (30, 3), (32, 8), (31, 14)], fill=8)
        d.line([(32, 18), (35, 23), (35, 27)], fill=7)
        # The main mass changes to faceted bedding east of the fossil.
        d.polygon([(40, 7), (53, 3), (70, 5), (81, 3), (95, 8),
                   (95, 27), (80, 30), (61, 27), (47, 29), (39, 22)], fill=4)
        d.polygon([(41, 8), (53, 3), (68, 5), (75, 10), (71, 15),
                   (59, 18), (46, 15), (40, 12)], fill=6)
        d.polygon([(46, 8), (55, 5), (64, 6), (67, 8), (58, 10),
                   (48, 10)], fill=7)
        d.line([(42, 7), (53, 3), (60, 4)], fill=8)
        d.polygon([(41, 14), (49, 18), (60, 20), (73, 16), (76, 11),
                   (75, 19), (62, 24), (48, 22), (41, 19)], fill=2)
        d.line([(44, 18), (58, 22), (71, 19)], fill=1)
        d.polygon([(69, 16), (78, 9), (87, 9), (95, 13), (95, 18),
                   (85, 23), (74, 23), (67, 20)], fill=5)
        d.polygon([(73, 16), (80, 11), (86, 11), (92, 14),
                   (86, 17), (78, 18)], fill=6)
        d.line([(71, 16), (79, 10), (85, 10)], fill=7)
        d.line([(75, 24), (86, 25), (94, 21)], fill=1)
        d.polygon([(46, 25), (56, 25), (63, 28), (57, 30), (48, 29)], fill=5)
        _crack(d, [(61, 5), (59, 9), (62, 12), (58, 16), (59, 20),
                   (55, 24), (57, 29)],
               ([(59, 20), (67, 21), (72, 18), (79, 19), (85, 16),
                 (92, 17)],
                [(59, 9), (51, 10), (46, 8), (40, 9), (35, 7)]), stage,
               ([(60, 10), (62, 12)], [(57, 23), (55, 24)],
                [(75, 19), (78, 19)]),
               ([(58, 14), (62, 14), (63, 17), (59, 19), (56, 17)],
                [(33, 6), (37, 7), (38, 10), (35, 11), (33, 9)]))


def _arch(d, stage):
    # Continuous stone across all four boundaries makes this a blind bay
    # embedded in a wall.  It has no black portal, open jamb or floor threshold.
    d.polygon([(0, 6), (9, 4), (22, 7), (34, 3), (48, 6), (63, 3),
               (63, 41), (51, 44), (35, 41), (20, 45), (0, 41)], fill=4)
    d.polygon([(8, 34), (8, 25), (12, 16), (19, 9), (29, 4),
               (39, 8), (48, 15), (53, 25), (54, 37), (48, 40),
               (15, 40)], fill=2)
    # Explicit blocked stone backing fills the complete recess.  Unequal
    # bedding planes and a broken cross-rib further deny a walkable doorway.
    d.polygon([(16, 34), (15, 26), (18, 19), (24, 14), (30, 11),
               (37, 14), (43, 21), (46, 30), (45, 36), (33, 38),
               (21, 37)], fill=4)
    d.polygon([(18, 24), (24, 17), (30, 15), (36, 18), (40, 24),
               (35, 26), (26, 24)], fill=5)
    d.polygon([(20, 29), (28, 26), (35, 29), (43, 28), (44, 34),
               (35, 36), (23, 34)], fill=3)
    d.line([(18, 25), (25, 23), (33, 26), (41, 25)], fill=2)
    d.line([(23, 33), (30, 31), (37, 33)], fill=4)
    # The rib is a broad asymmetric load-bearing stone body, not nested rings.
    d.polygon([(6, 34), (7, 23), (12, 14), (20, 7), (29, 2),
               (40, 6), (49, 13), (53, 21), (54, 32), (50, 34),
               (47, 23), (42, 16), (36, 11), (29, 8), (22, 12),
               (16, 18), (12, 26), (12, 35)], fill=5)
    d.polygon([(7, 25), (12, 15), (21, 7), (29, 3), (35, 5),
               (29, 7), (21, 11), (15, 17), (10, 27), (10, 33),
               (7, 34)], fill=6)
    d.line([(7, 24), (12, 14), (20, 7), (29, 2), (33, 4)], fill=7)
    d.line([(10, 19), (13, 14), (20, 8), (25, 5)], fill=8)
    d.polygon([(39, 9), (46, 14), (50, 22), (51, 31), (48, 28),
               (46, 21), (41, 15)], fill=3)
    d.line([(12, 26), (16, 18), (22, 12), (29, 8)], fill=2)
    # Weathering interrupts only selected parts of the rib.  No small repeated
    # voussoir grid; these large unequal chips retain the architecture's age.
    d.polygon([(15, 13), (18, 12), (20, 14), (17, 16)], fill=4)
    d.line([(26, 6), (27, 8), (25, 10)], fill=3)
    d.polygon([(44, 16), (47, 18), (48, 21), (45, 20)], fill=4)
    # A closed curdstone bedding slab overlaps both jambs and all lower backing.
    d.polygon([(2, 37), (12, 34), (27, 36), (39, 34), (54, 36),
               (62, 40), (59, 44), (42, 45), (25, 43), (9, 44),
               (1, 41)], fill=2)
    d.polygon([(2, 36), (13, 33), (27, 35), (40, 33), (54, 35),
               (61, 39), (54, 40), (40, 39), (26, 41), (10, 40)], fill=5)
    d.polygon([(5, 36), (14, 34), (26, 36), (22, 38), (10, 38)], fill=6)
    d.line([(3, 36), (13, 33), (21, 34)], fill=7)
    d.line([(9, 42), (25, 43), (40, 41), (54, 42)], fill=1)
    _mould(d, [(40, 25), (45, 24), (49, 27), (48, 34), (44, 36),
               (38, 33)], [(41, 26), (44, 25), (46, 27)],
           [(43, 28), (46, 28), (46, 32), (42, 34), (40, 31)])
    # Isolated left rock lends asymmetry without creating a second bay.
    d.polygon([(0, 11), (3, 10), (5, 14), (3, 20), (0, 19)], fill=5)
    d.line([(0, 11), (2, 10), (3, 12)], fill=6)
    _crack(d, [(35, 5), (34, 10), (37, 14), (34, 20), (36, 25),
               (33, 30), (34, 36), (30, 40), (31, 44)],
           ([(36, 25), (29, 27), (24, 25), (19, 27)],
            [(34, 10), (41, 9), (46, 6), (52, 7)]), stage,
           ([(36, 14), (35, 16)], [(35, 25), (33, 27)],
            [(32, 39), (30, 40)]),
           ([(33, 8), (36, 7), (38, 10), (36, 13), (33, 11)],
            [(33, 34), (37, 34), (38, 37), (34, 39), (31, 37)]))


def _compact(d, stage, variant):
    # These are independently drawn remnants, not resized/cropped large bays.
    if variant == 0:
        d.polygon([(0, 7), (6, 3), (18, 4), (28, 10), (30, 20),
                   (24, 28), (10, 30), (0, 26)], fill=4)
        d.polygon([(0, 7), (7, 3), (17, 4), (25, 8), (28, 13),
                   (22, 16), (10, 15), (1, 12)], fill=6)
        d.polygon([(2, 7), (8, 5), (15, 6), (20, 8), (12, 10),
                   (5, 9)], fill=7)
        d.line([(0, 7), (6, 3), (12, 3)], fill=8)
        d.polygon([(1, 13), (10, 16), (22, 17), (28, 13), (27, 20),
                   (20, 23), (8, 21), (0, 17)], fill=2)
        d.line([(1, 16), (10, 19), (20, 20), (25, 17)], fill=1)
        d.polygon([(7, 24), (15, 23), (24, 26), (22, 29), (11, 29),
                   (5, 27)], fill=5)
        d.line([(7, 24), (14, 23), (18, 24)], fill=6)
        _mould(d, [(0, 20), (6, 20), (10, 24), (7, 28), (0, 27)],
               [(0, 21), (4, 21), (6, 23)],
               [(1, 23), (5, 22), (7, 25), (4, 26), (0, 25)])
        _crack(d, [(20, 6), (18, 10), (20, 14), (17, 18), (18, 23),
                   (15, 28)], ([(17, 18), (12, 17), (8, 19)],), stage,
               ([(19, 14), (18, 16)],),
               ([(17, 9), (20, 9), (21, 12), (18, 14), (16, 12)],
                [(16, 23), (19, 23), (19, 26), (16, 28), (14, 26)]))
    else:
        d.polygon([(0, 9), (6, 5), (15, 6), (21, 3), (30, 7),
                   (31, 25), (23, 29), (11, 27), (0, 29)], fill=4)
        d.polygon([(0, 10), (5, 5), (13, 6), (17, 10), (13, 15),
                   (3, 16), (0, 13)], fill=5)
        d.polygon([(0, 9), (5, 5), (12, 6), (14, 8), (8, 10),
                   (2, 11)], fill=6)
        d.line([(0, 9), (5, 5), (9, 5)], fill=7)
        d.polygon([(0, 15), (5, 18), (13, 17), (17, 12), (16, 20),
                   (8, 23), (0, 20)], fill=2)
        d.line([(1, 18), (6, 20), (12, 19)], fill=1)
        d.polygon([(16, 10), (20, 4), (27, 5), (31, 9), (31, 17),
                   (23, 20), (17, 16)], fill=6)
        d.polygon([(19, 10), (22, 6), (27, 7), (28, 9), (24, 12)], fill=7)
        d.line([(18, 8), (20, 4), (25, 4)], fill=8)
        d.polygon([(18, 17), (24, 21), (31, 18), (31, 23), (25, 26),
                   (19, 23)], fill=2)
        d.line([(21, 21), (25, 23), (30, 21)], fill=1)
        _mould(d, [(4, 23), (11, 22), (16, 25), (15, 29), (5, 29),
                   (1, 27)], [(4, 24), (10, 23), (12, 24)],
               [(6, 25), (11, 24), (14, 26), (10, 28), (5, 27)])
        _crack(d, [(12, 6), (13, 10), (10, 14), (13, 18), (12, 23),
                   (16, 28)], ([(13, 18), (20, 17), (24, 18), (28, 16)],),
               stage, ([(11, 14), (12, 16)], [(13, 24), (14, 25)]),
               ([(10, 12), (13, 12), (14, 15), (11, 17), (9, 15)],
                [(11, 22), (14, 22), (16, 25), (13, 26), (11, 24)]))


def filler(stage=0, kind='mid', variant=0):
    """Quiet 16px solid backing for thin remnants between whole paintings.

    It deliberately carries no fans, tiny cracks or arch motif.  The large
    panels supply the illustration; this subdued connected stone supplies the
    joins.  Boundary kinds add only restrained plane/contact cues.  Physical
    cliff edges and the visible upper rim use the dedicated border painter.
    """
    stage = max(0, min(2, int(stage)))
    im, d = _canvas((16, 16), stage)
    if int(variant) % 2:
        d.polygon([(0, 6), (5, 4), (11, 5), (15, 8), (12, 10),
                   (5, 9), (0, 10)], fill=4)
    else:
        d.polygon([(0, 2), (6, 2), (10, 4), (8, 6), (2, 5), (0, 6)], fill=4)
    if kind == 'top':
        d.rectangle((0, 0, 15, 2), fill=4)
        d.line((0, 3, 15, 3), fill=2)
    elif kind in ('base', 'bottom'):
        d.rectangle((0, 13, 15, 15), fill=2)
        d.line((0, 15, 15, 15), fill=1)
    elif kind == 'left':
        d.rectangle((0, 0, 1, 15), fill=2)
        d.line((2, 0, 2, 15), fill=4)
    elif kind == 'right':
        d.rectangle((14, 0, 15, 15), fill=2)
    elif kind != 'mid':
        raise ValueError('unknown Cream wall backing kind: %r' % (kind,))
    return im


def panel(stage=0, kind='shelf', variant=0):
    """Return one final-size opaque P painting; no scaling or filtering.

    ``stage`` clamps to fresh/sour/deep.  Kind variants wrap, so the single
    scarce blind bay accepts any variant without introducing another asset.
    Unknown kinds raise a useful error instead of supplying misleading art.
    """
    stage = max(0, min(2, int(stage)))
    sizes = {'shelf': (64, 32), 'fracture': (96, 32),
             'arch': (64, 48), 'compact': (32, 32)}
    if kind not in sizes:
        raise ValueError('unknown Cream wall panel kind: %r' % (kind,))
    im, d = _canvas(sizes[kind], stage)
    variant = int(variant) % 2
    if kind == 'shelf':
        _shelf(d, stage, variant)
    elif kind == 'fracture':
        _fracture(d, stage, variant)
    elif kind == 'arch':
        _arch(d, stage)
    else:
        _compact(d, stage, variant)
    return im
