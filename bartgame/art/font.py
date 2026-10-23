"""The text font: 8x8 glyphs for ASCII 32..126, rendered from a system
TTF and thresholded, so every glyph is 1 (ink) on 0 (clear) with a 2
(shadow) pixel down-right where the ink does not already sit."""
import os

from PIL import Image, ImageDraw, ImageFont

CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf',
]


def render():
    path = next(p for p in CANDIDATES if os.path.exists(p))
    fnt = ImageFont.truetype(path, 10)
    glyphs = []
    for code in range(32, 127):
        im = Image.new('L', (8, 8), 0)
        d = ImageDraw.Draw(im)
        ch = chr(code)
        # DejaVu Mono at 10px is 6 wide and about 8 tall with descenders;
        # shift up by one so lowercase descenders keep their tails.
        d.text((1, -2), ch, font=fnt, fill=255)
        px = im.load()
        g = [[1 if px[x, y] > 110 else 0 for x in range(8)] for y in range(8)]
        # drop shadow
        for y in range(7, -1, -1):
            for x in range(7, -1, -1):
                if g[y][x] == 1:
                    if y + 1 < 8 and g[y + 1][x] == 0:
                        g[y + 1][x] = 2
        glyphs.append(g)
    return glyphs


if __name__ == '__main__':
    gs = render()
    for g in gs[33:60]:
        print('\n'.join(''.join('#' if c == 1 else '+' if c == 2 else '.' for c in row) for row in g))
        print()
