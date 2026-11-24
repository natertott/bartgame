"""Native brass, oxidized metal and velvet for the Drain trophy case."""
from PIL import Image, ImageDraw


PALETTE = (
    '#000000', '#101820', '#182828', '#203030',
    '#304840', '#406058', '#282030', '#382830',
    '#584050', '#503828', '#886038', '#b88850',
    '#d8b878', '#f0d8a8', '#584838', '#888878',
)


def bevel(draw, box, fill, upper, lower):
    left, top, right, bottom = box
    draw.rectangle(box, fill=fill, outline=1)
    draw.line([(left + 1, bottom - 1), (left + 1, top + 1),
               (right - 2, top + 1)], fill=upper)
    draw.line([(left + 2, bottom - 1), (right - 1, bottom - 1),
               (right - 1, top + 2)], fill=lower)


def pin(draw, x, y):
    draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=1)
    draw.rectangle((x - 1, y - 1, x + 1, y + 1), fill=10)
    draw.point((x - 1, y - 1), fill=13)
    draw.point((x + 1, y + 1), fill=9)


def tab(selected=False):
    image = Image.new('P', (56, 16), 2)
    draw = ImageDraw.Draw(image)
    bevel(draw, (0, 1, 55, 14), 7 if selected else 3,
          11 if selected else 5, 10 if selected else 4)
    if selected:
        draw.line((2, 2, 14, 2), fill=12)
        draw.line((22, 13, 33, 13), fill=12)
    return image


def row(selected=False):
    image = Image.new('P', (112, 16), 2)
    draw = ImageDraw.Draw(image)
    draw.line((0, 0, 0, 15), fill=4)
    draw.line((111, 0, 111, 15), fill=1)
    if selected:
        bevel(draw, (2, 0, 109, 14), 7, 11, 9)
        draw.line((3, 1, 22, 1), fill=12)
        draw.polygon([(4, 5), (8, 7), (4, 9)], fill=11)
        draw.line((4, 7, 6, 6), fill=13)
    else:
        draw.rectangle((2, 0, 109, 13), fill=3)
        draw.line((2, 14, 109, 14), fill=4)
    return image


def cabinet():
    image = Image.new('P', (240, 160), 1)
    draw = ImageDraw.Draw(image)
    draw.polygon([(5, 1), (234, 1), (238, 5), (238, 154),
                  (234, 158), (5, 158), (1, 154), (1, 5)], fill=3)
    draw.line([(2, 110), (2, 6), (6, 2), (233, 2), (237, 6)], fill=5)
    draw.line([(237, 7), (237, 153), (233, 157), (6, 157),
               (2, 153), (2, 111)], fill=2)
    draw.rectangle((5, 6, 234, 153), fill=1)
    bevel(draw, (7, 4, 232, 15), 7, 11, 9)
    bevel(draw, (7, 136, 232, 153), 7, 11, 9)
    for y in (9, 144):
        pin(draw, 12, y)
        pin(draw, 227, y)
    for x in (5, 234):
        for y in (34, 131):
            pin(draw, x, y)
    for x in (8, 64, 120, 176):
        image.paste(tab(), (x, 16))
    return image, draw


def cradle(draw, left, right):
    center = (left + right + 1) // 2
    bevel(draw, (left, 32, right, 95), 6, 10, 9)
    draw.rectangle((left + 3, 37, right - 3, 83), fill=3)
    draw.rectangle((left + 4, 40, right - 4, 76), fill=2)
    draw.line((left + 3, 38, right - 3, 38), fill=5)
    draw.polygon([(left + 5, 42), (left + 21, 42),
                  (left + 5, 58)], fill=3)
    draw.line((right - 14, 46, right - 6, 38), fill=5)
    draw.line((right - 11, 49, right - 6, 44), fill=4)
    draw.rectangle((left + 3, 80, right - 3, 92), fill=7)
    draw.line((left + 4, 81, right - 4, 81), fill=8)
    draw.ellipse((center - 24, 85, center + 25, 91), fill=6)
    draw.polygon([(center - 18, 81), (center + 17, 81),
                  (center + 21, 86), (center + 20, 90),
                  (center - 21, 90), (center - 22, 86)], fill=9, outline=1)
    draw.line([(center - 21, 86), (center - 17, 82),
               (center + 17, 82), (center + 21, 86)], fill=11)
    draw.line((center - 16, 82, center + 5, 82), fill=12)
    draw.line((center - 18, 87, center + 18, 87), fill=10)


def browser():
    image, draw = cabinet()
    bevel(draw, (8, 32, 119, 135), 2, 4, 3)
    draw.line((10, 39, 117, 39), fill=1)
    for y in range(40, 120, 16):
        image.paste(row(), (8, y))
    draw.line((10, 122, 117, 122), fill=4)
    draw.line((10, 133, 117, 133), fill=1)
    cradle(draw, 128, 231)
    bevel(draw, (128, 96, 231, 135), 2, 11, 9)
    draw.line((131, 98, 168, 98), fill=10)
    return image


def detail():
    image, draw = cabinet()
    cradle(draw, 8, 83)
    bevel(draw, (8, 96, 83, 135), 2, 11, 9)
    draw.line((11, 98, 43, 98), fill=10)
    bevel(draw, (85, 32, 231, 135), 3, 11, 9)
    draw.line((86, 33, 115, 33), fill=12)
    draw.line((88, 55, 228, 55), fill=2)
    draw.line((89, 56, 227, 56), fill=4)
    draw.line((87, 133, 119, 133), fill=10)
    return image


def sealed(center):
    """A small unlit lock sits on the empty exhibit plinth."""
    image = Image.new('P', (32, 32))
    draw = ImageDraw.Draw(image)
    draw.arc((center - 8, 4, center + 8, 22), 180, 359, fill=1, width=5)
    draw.arc((center - 7, 5, center + 7, 21), 180, 359, fill=10, width=2)
    draw.arc((center - 8, 5, center + 7, 21), 191, 273, fill=11, width=1)
    draw.line((center - 8, 12, center - 8, 17), fill=1)
    draw.line((center - 7, 12, center - 7, 17), fill=10)
    draw.line((center + 7, 12, center + 7, 17), fill=9)
    draw.line((center + 8, 12, center + 8, 17), fill=1)
    draw.polygon([(center - 8, 13), (center + 8, 13), (center + 10, 15),
                  (center + 10, 23), (center + 7, 25), (center - 8, 25),
                  (center - 10, 23), (center - 10, 15)], fill=9, outline=1)
    draw.rectangle((center - 8, 15, center + 7, 22), fill=10)
    draw.line((center - 8, 15, center + 5, 15), fill=11)
    draw.ellipse((center - 2, 17, center + 2, 20), fill=1)
    draw.rectangle((center - 1, 19, center + 1, 22), fill=1)
    return image
