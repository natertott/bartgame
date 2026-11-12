"""Native Cream synthesis: raised borders, open drops and floor contacts.

All pictures are authored directly as indexed sixteen-pixel cells.  Palette
banks are the unchanged, RGB555-normalized Rind banks.  ``rim``, ``landing``
and ``floor_toe`` use the floor bank; solid side returns use its cliff bank.
Drop side returns use the floor bank.  Nothing here changes collision or picks
a landing position: the room renderer must supply a real, dry arrival floor.
"""
from PIL import Image, ImageDraw

from cream_style_rind import PALETTES as _RIND_PALETTES
from cream_style_rind import floor as _rind_floor


PALETTES = {name: colors[:] for name, colors in _RIND_PALETTES.items()}


def _quiet_floor(stage=0, variant=0):
    """Match study five's installed quiet floor, including its common cell."""
    image = _rind_floor(stage, variant % 3).copy()
    if variant % 3 == 0:
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 7, 2), fill=4)
        draw.line([(4, 10), (7, 9), (9, 9)], fill=3)
        draw.line((5, 11, 8, 10), fill=5)
    return image


def rim(stage=0, variant=0, drop=False):
    """A SOLID raised rind or a FLOOR open takeoff, in a floor palette.

    The raised border projects above the floor and has a broad dark front.
    The open edge stays low and has an uninterrupted central standing plane.
    Neither drawing has a grip cadence, arrow, gold mark or false ladder.
    """
    image = _quiet_floor(stage, variant % 2)
    draw = ImageDraw.Draw(image)
    v = variant % 2
    if drop:
        # A low, worn sill.  The standing field reaches the sill across its
        # full width; it does not inherit the raised rim's bright parapet.
        profile = ([(0, 12), (4, 12), (5, 11), (10, 11),
                    (12, 12), (15, 12)] if not v else
                   [(0, 12), (3, 12), (5, 11), (8, 11),
                    (10, 12), (15, 12)])
        draw.polygon(profile + [(15, 15), (0, 15)], fill=3)
        draw.line(profile, fill=5)
        draw.line((0, 15, 15, 15), fill=2)
        # Two tiny surface indentations are worn matter, not target glyphs.
        for x, y in (((4, 10), (11, 11)) if not v else
                     ((3, 11), (10, 10))):
            draw.line((x, y, x+1, y), fill=3)
        draw.line((6 if not v else 5, 12, 9 if not v else 8, 12), fill=4)
        draw.line((2, 14, 6, 14), fill=4)
        return image

    # The cap is 3--5px broad, then turns into an occluded near face.  Tile
    # boundaries meet at the same height while interior chips vary naturally.
    profile = ([(0, 8), (3, 8), (5, 7), (9, 7), (11, 8), (15, 8)]
               if not v else
               [(0, 8), (2, 8), (4, 7), (7, 7), (10, 8), (15, 8)])
    draw.polygon(profile + [(15, 15), (0, 15)], fill=3)
    draw.polygon(profile + [(15, 10), (12, 10), (10, 11),
                            (5, 10), (2, 11), (0, 10)], fill=6)
    draw.line(profile, fill=7)
    draw.line([(0, 11), (3, 12), (6, 11), (10, 12), (15, 11)], fill=2)
    draw.polygon([(0, 13), (4, 13), (6, 14), (10, 13),
                  (13, 14), (15, 13), (15, 15), (0, 15)], fill=1)
    draw.line((1, 14, 4, 14), fill=3)
    draw.line((10, 14, 12, 14), fill=2)

    # A connected rooted obstruction, with unequal mounds rather than paired
    # rungs.  Its silhouette remains visibly high in grayscale.
    if not v:
        dark = [(0, 9), (1, 5), (3, 3), (5, 3), (7, 5),
                (8, 8), (11, 8), (12, 5), (14, 5), (15, 7), (15, 11)]
        body = [(1, 7), (2, 5), (4, 4), (6, 5), (6, 7),
                (4, 8), (2, 8)]
        other = [(12, 7), (13, 6), (14, 6), (15, 8), (14, 9), (12, 9)]
        root = [(5, 8), (6, 10), (4, 12)]
    else:
        dark = [(0, 6), (2, 5), (4, 7), (5, 7), (6, 4),
                (9, 3), (11, 5), (12, 8), (15, 9), (15, 11), (0, 11)]
        body = [(6, 7), (7, 5), (9, 4), (10, 5), (11, 7),
                (9, 8), (7, 8)]
        other = [(0, 7), (2, 6), (3, 7), (3, 8), (1, 9), (0, 9)]
        root = [(10, 8), (11, 10), (9, 12)]
    draw.polygon(dark, fill=1)
    draw.polygon(body, fill=9)
    draw.polygon(other, fill=9)
    draw.line(root, fill=2, width=2)
    if not v:
        draw.line([(2, 5), (4, 4), (5, 5)], fill=11)
        draw.line((12, 7, 13, 6), fill=10)
    else:
        draw.line([(7, 5), (9, 4), (10, 5)], fill=11)
        draw.line((0, 7, 1, 6), fill=10)
    if stage == 1:
        draw.line([(5 if not v else 9, 5), (4 if not v else 8, 7),
                   (5 if not v else 9, 9)], fill=2)
    elif stage >= 2:
        # Corruption stays attached to a split in the raised material.  Floor
        # contacts below deliberately never borrow these violet inks.
        x = 4 if not v else 8
        draw.line([(x+1, 4), (x, 6), (x+1, 8), (x, 10)], fill=12, width=2)
        draw.line([(x+1, 5), (x, 6), (x+1, 8)], fill=13)
        draw.point((x, 6), fill=14)
    return image


def edge(stage=0, kind='solid_left', variant=0):
    """Opaque 16px side returns and a dark wall foot.

    ``solid_left``, ``solid_right`` and ``toe`` use cliff banks and SOLID15.
    ``drop_left``/``drop_right`` use floor banks and FLOOR0.  The handed open
    returns are narrow worn cheeks, keeping the central floor easy to read.
    """
    if kind not in ('solid_left', 'solid_right', 'drop_left', 'drop_right', 'toe'):
        raise ValueError('unknown Cream edge kind: %s' % kind)
    v = variant % 2
    if kind.startswith('drop_'):
        image = rim(stage, v, True)
        draw = ImageDraw.Draw(image)
        # The cheek is visibly much lower and thinner than the solid return.
        if kind == 'drop_left':
            draw.polygon([(0, 7), (1, 7), (2, 9), (2, 12),
                          (3, 13), (2, 15), (0, 15)], fill=3)
            draw.line([(0, 7), (1, 9), (1, 11)], fill=5)
            draw.line((0, 13, 0, 15), fill=2)
        else:
            draw.polygon([(14, 7), (15, 7), (15, 15), (12, 15),
                          (13, 12), (13, 9)], fill=3)
            draw.line([(14, 8), (14, 11)], fill=4)
            draw.line((15, 12, 15, 15), fill=2)
        return image

    image = Image.new('P', (16, 16), 3)
    draw = ImageDraw.Draw(image)
    if kind == 'toe':
        # The wall foot continues its vertical face to a full-width dark base.
        # Any floor shadow is a separate FLOOR tile placed on real dry ground.
        draw.polygon([(0, 0), (6, 0), (8, 3), (13, 3), (15, 1),
                      (15, 8), (12, 9), (8, 8), (4, 10), (0, 8)], fill=4)
        draw.polygon([(0, 0), (5, 0), (7, 2), (5, 4), (0, 4)], fill=5)
        draw.line([(0, 6), (4, 7), (7, 6), (10, 7)], fill=2)
        draw.polygon([(0, 10), (3, 11), (6, 10), (10, 12),
                      (13, 11), (15, 11), (15, 15), (0, 15)], fill=1)
        draw.line([(0, 12), (3, 13), (6, 12)], fill=3)
        draw.line((10, 14, 14, 14), fill=2)
        if v:
            draw.polygon([(8, 0), (13, 0), (15, 2), (11, 3), (8, 2)], fill=5)
            draw.line((9, 0, 12, 0), fill=6)
        return image

    # Broad faceted mass plus a 4--5px turn of the side wall.  The return has
    # no regular dashes that could be confused with a climbing feature.
    if kind == 'solid_left':
        draw.polygon([(4, 0), (15, 0), (15, 15), (5, 15),
                      (4, 11), (5, 7), (4, 3)], fill=4)
        draw.polygon([(5, 1), (12, 0), (14, 3), (10, 5), (5, 5)], fill=5)
        draw.line([(4, 0), (5, 3), (4, 6), (5, 10), (5, 14)], fill=6)
        draw.polygon([(0, 0), (2, 0), (3, 4), (2, 8),
                      (3, 12), (2, 15), (0, 15)], fill=2)
        draw.line([(7, 9), (10, 10), (15, 9)], fill=2)
        draw.line((6, 2, 10, 1), fill=7)
        if v:
            draw.polygon([(7, 6), (12, 5), (15, 7), (13, 9), (8, 8)], fill=5)
    else:
        draw.polygon([(0, 0), (10, 0), (11, 4), (10, 8),
                      (11, 12), (10, 15), (0, 15)], fill=4)
        draw.polygon([(0, 0), (6, 0), (9, 3), (7, 5), (0, 4)], fill=5)
        draw.line((0, 1, 4, 1), fill=6)
        draw.polygon([(12, 0), (15, 0), (15, 15), (11, 15),
                      (12, 10), (11, 5)], fill=2)
        draw.line([(14, 0), (14, 4), (13, 7), (14, 11), (14, 15)], fill=1)
        draw.line([(0, 10), (4, 11), (8, 10), (11, 11)], fill=2)
        if v:
            draw.polygon([(0, 6), (5, 6), (8, 8), (5, 9), (0, 8)], fill=5)
    return image


def floor_toe(stage=0, variant=0):
    """Quiet FLOOR0 contact directly below an actual wall base.

    This is distinct from ``edge(kind='toe')``, which is still a solid wall.
    A continuous grey upper cut fades into the existing floor by row eight.
    """
    image = _quiet_floor(stage, variant % 2)
    original = image.copy()
    draw = ImageDraw.Draw(image)
    draw.polygon([(0, 0), (15, 0), (15, 4), (12, 4), (12, 5),
                  (8, 5), (8, 4), (5, 4), (5, 6), (2, 6),
                  (2, 5), (0, 5)], fill=3)
    # Preserve a little floor grain as material seen through the shade.
    for y in range(7):
        for x in range(16):
            if image.getpixel((x, y)) == 3 and original.getpixel((x, y)) == 5:
                image.putpixel((x, y), 4)
    for x, y in ((0, 6), (3, 7), (6, 5), (8, 6), (11, 6), (14, 5)):
        draw.point((x, y), fill=3)
    if variant % 2:
        draw.line((9, 5, 11, 5), fill=4)
        draw.line((13, 6, 14, 6), fill=3)
    else:
        draw.line((3, 4, 5, 4), fill=4)
        draw.line((5, 7, 6, 7), fill=3)
    return image


def _landing_master(stage=0, variant=0):
    """A shallow 48x32 cast shadow with an irregular horizontal upper cut."""
    image = Image.new('P', (48, 32), 4)
    for part in range(6):
        x, y = (part % 3) * 16, (part // 3) * 16
        image.paste(_quiet_floor(stage, (part + variant) % 3), (x, y))
    original = image.copy()
    draw = ImageDraw.Draw(image)
    # The long upper cut and unequal, low projecting planes describe a ledge's
    # cast shape.  It touches the upper edge instead of enclosing an oval.
    # True arrival feet are local (16,14) when the renderer anchors this master
    # one cell left of the feet's column, on the feet's actual floor row.
    draw.polygon([(0, 0), (12, 0), (12, 1), (21, 1), (21, 0),
                  (40, 0), (40, 1), (45, 1), (45, 3), (47, 3),
                  (47, 6), (44, 6), (44, 8), (39, 8), (39, 10),
                  (35, 10), (35, 12), (28, 12), (28, 14),
                  (23, 14), (23, 15), (12, 15), (12, 13),
                  (8, 13), (8, 10), (3, 10), (3, 7), (0, 7)], fill=3)
    # Retain the original floor's light grain in a shaded ink, rather than
    # replacing its interior with an untextured puddle of flat grey.
    for y in range(16):
        for x in range(48):
            if image.getpixel((x, y)) == 3 and original.getpixel((x, y)) == 5:
                image.putpixel((x, y), 4)
    # Dither only in the short transition, using the existing grey and floor
    # inks.  It is intentionally asymmetric and never a halo around a target.
    for x, y in ((1, 8), (3, 11), (5, 11), (7, 12), (9, 14),
                 (11, 15), (13, 16), (15, 17), (18, 16), (21, 17),
                 (24, 16), (26, 15), (28, 15), (30, 13), (33, 13),
                 (36, 11), (38, 11), (40, 9), (42, 9), (45, 7)):
        draw.point((x, y), fill=3)
    for x, y in ((1, 6), (3, 8), (7, 10), (9, 12), (12, 14),
                 (15, 15), (20, 15), (23, 13), (27, 13), (31, 12),
                 (34, 10), (38, 9), (42, 7), (45, 5)):
        draw.point((x, y), fill=4)
    # Two small residual floor ridges interrupt the cast shape without a
    # highlight around it or a bright center that would resemble a target.
    draw.line((7, 5, 8, 5), fill=5)
    draw.line((30, 9, 31, 9), fill=5)
    if variant % 2:
        draw.line((29, 14, 31, 14), fill=3)
        draw.point((34, 14), fill=3)
        draw.line((7, 11, 9, 11), fill=4)
    return image


def landing(stage=0, part=0, variant=0):
    """One of six row-major FLOOR0 shadow cells, all in the floor bank.

    Assemble parts 0,1,2 above 3,4,5 around an actual arrival.  The renderer
    must only replace valid dry floor cells and keep the true arrival clear.
    Index zero is never painted.  Only grey shadow ink3 is added, including
    deep corruption: violet is reserved for attached fractures and hazards.
    """
    if not 0 <= part < 6:
        raise ValueError('landing part must be in 0..5')
    master = _landing_master(stage, variant % 2)
    x, y = (part % 3) * 16, (part // 3) * 16
    return master.crop((x, y, x+16, y+16))
