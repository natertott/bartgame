"""Native, contiguous curdstone faces with exposed rock holds."""
from PIL import Image, ImageDraw


DIGITS = '0123456789abcdef'


def shelf(draw, lip):
    """A pale upper-left shoulder and a short undercut in the same rock."""
    x, y = lip[0]
    end_x, end_y = lip[-1]
    draw.polygon(lip + [(end_x - 2, end_y + 4), (x + 3, y + 4)], fill=2)
    draw.polygon(lip + [(end_x - 2, end_y + 2), (x + 2, y + 2)], fill=5)
    draw.line(lip, fill=6)
    if end_x - x >= 12:
        draw.line((x + 3, y - 1, x + 7, y - 1), fill=7)


def bands():
    """Paint across four cells, reusing the middle surface in either join."""
    face = Image.new('P', (64, 16), 3)
    draw = ImageDraw.Draw(face)
    draw.polygon([(0, 5), (10, 5), (18, 3), (31, 3), (41, 6), (53, 6),
                  (63, 5), (63, 11), (53, 11), (45, 12), (36, 10),
                  (24, 9), (10, 11), (0, 11)], fill=4)
    draw.line([(0, 12), (12, 12), (23, 10), (33, 10), (44, 13),
               (53, 13), (63, 12)], fill=2)
    for lip in (
        [(4, 6), (8, 4), (12, 4), (16, 5)],
        [(23, 10), (26, 8), (35, 8), (39, 10)],
        [(44, 5), (47, 3), (51, 3), (55, 5)],
        [(52, 12), (56, 10), (60, 11)],
    ):
        shelf(draw, lip)

    top = face.copy()
    draw = ImageDraw.Draw(top)
    draw.rectangle((0, 0, 63, 7), fill=3)
    ridge = [(0, 2), (11, 2), (16, 0), (25, 0), (32, 2),
             (45, 2), (49, 1), (56, 1), (63, 2)]
    draw.polygon(ridge + [(63, 5), (49, 5), (44, 6), (32, 6),
                          (21, 4), (11, 6), (0, 5)], fill=6)
    draw.line(ridge, fill=7)
    draw.line([(0, 6), (11, 7), (21, 5), (31, 7), (45, 7),
               (50, 6), (63, 6)], fill=2)

    base = face.copy()
    draw = ImageDraw.Draw(base)
    draw.rectangle((0, 8, 63, 15), fill=3)
    draw.polygon([(0, 8), (63, 8), (63, 11), (49, 11), (42, 12),
                  (31, 10), (24, 10), (17, 12), (7, 11), (0, 11)], fill=4)
    draw.line([(0, 12), (8, 12), (17, 13), (27, 11), (33, 11),
               (42, 13), (52, 12), (63, 12)], fill=2)
    draw.line((0, 15, 63, 15), fill=1)
    return (('top', top), ('mid', face), ('base', base))


def metatiles():
    for kind, image in bands():
        for column in range(4):
            tile = image.crop((column * 16, 0, column * 16 + 16, 16))
            pixels = iter(tile.getdata())
            art = [''.join(DIGITS[next(pixels)] for _ in range(16)) for _ in range(16)]
            # All elevations share indexed pixels and select their native bank.
            for stage in range(3):
                yield dict(name=f'cream_wall_{kind}_s{stage}_{column}',
                           pal=f'cream_cliff{stage}', type='CREAM_WALL', coll=15, art=art)


METATILES = list(metatiles())
