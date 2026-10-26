"""The Drain's two keepers (art/sw_folk.py) rendered as the screen shows
them: every frame of their sheets on a contact sheet, or the pair in
their places over the painted hall.

    python3 tools/folk_preview.py sheet out.png [--scale 4]
    python3 tools/folk_preview.py hall out.png [--head open] [--body rest]
            [--gate idle] [--wisp w0] [--scale 3]
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'art'))
import sw_folk as F  # noqa: E402

# where the engine draws them (npc.c): the sprites' top left in the hall
PEDDLER_HEAD_AT = (40, 46)
PEDDLER_BODY_AT = (40, 62)
GATEKEEPER_AT = (312, 30)


def rgb(c):
    return tuple(v | v >> 5 for v in c)


def frame_image(rows, pal):
    cols = [None] + [rgb(c) for _, c in pal]
    h, w = len(rows), len(rows[0])
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != '.':
                im.putpixel((x, y), cols[int(ch, 16)] + (255,))
    return im


def pal_of(name):
    return F.PEDDLER_PAL if name == 'peddler' else F.GATEKEEPER_PAL


def contact(out, scale):
    tiles = []
    for (name, pal, w, h, frames) in F.SHEETS:
        for fname, rows in frames.items():
            tiles.append(('%s %s' % (name, fname), frame_image(rows, pal_of(pal))))
    cw = max(t.width for _, t in tiles) * scale + 8
    ch = max(t.height for _, t in tiles) * scale + 20
    per = 6
    sheet = Image.new('RGB', (cw * per, ch * ((len(tiles) + per - 1) // per)), (64, 68, 76))
    d = ImageDraw.Draw(sheet)
    for i, (label, t) in enumerate(tiles):
        x, y = (i % per) * cw, (i // per) * ch
        sheet.paste(t.resize((t.width * scale, t.height * scale), Image.NEAREST), (x + 4, y + 16), t.resize((t.width * scale, t.height * scale), Image.NEAREST))
        d.text((x + 4, y + 2), label, fill=(230, 230, 230))
    sheet.save(out)


def hall(out, head, body, gate, wisp, scale, t=0):
    import sw_hall as HL
    g, o = HL.paint(t)
    im = g.to_image().convert('RGBA')
    sheets = {n: (pal, fr) for (n, pal, w, h, fr) in F.SHEETS}
    for (sheet, fname, at) in (('peddler_body', body, PEDDLER_BODY_AT), ('peddler_head', head, PEDDLER_HEAD_AT),
                               ('gatekeeper', gate, GATEKEEPER_AT),
                               ('wisp', wisp, (GATEKEEPER_AT[0] + F.WISP_AT[0], GATEKEEPER_AT[1] + F.WISP_AT[1]))):
        pal, fr = sheets[sheet]
        im.alpha_composite(frame_image(fr[fname], pal_of(pal)), at)
    im.alpha_composite(o.to_image())
    im.convert('RGB').resize((im.width * scale, im.height * scale), Image.NEAREST).save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('what', choices=('sheet', 'hall'))
    ap.add_argument('out')
    ap.add_argument('--scale', type=int, default=0)
    ap.add_argument('--head', default='open')
    ap.add_argument('--body', default='rest')
    ap.add_argument('--gate', default='idle')
    ap.add_argument('--wisp', default='w0')
    a = ap.parse_args()
    if a.what == 'sheet':
        contact(a.out, a.scale or 4)
    else:
        hall(a.out, a.head, a.body, a.gate, a.wisp, a.scale or 2)


if __name__ == '__main__':
    main()
