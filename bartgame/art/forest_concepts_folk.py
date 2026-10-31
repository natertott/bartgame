"""Five native forest-folk studies; shared game palettes remain untouched.

Static quest-giver bodies use the existing 32px feet canvas and folk OBJ bank.
Portraits are separately drawn 48px busts, padded only by the sheet adapter.
These are optional environment studies, not additional people or new AI.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
import reboot_core as R

NAMES = ('hermit', 'nun', 'gardener')
ALIASES = {'sister_mary_grace': 'nun', 'brother_mark': 'hermit'}
STYLE_NAMES = {1: 'Fern Oak', 2: 'Silver Willow', 3: 'Copper Beech',
               4: 'Velvet Cedar', 5: 'Pale Orchard'}
# Primary cloth, shadow, light. These are existing folk-bank ink indices.
CLOTH = {
    1: {'hermit': (9, 8, 10), 'nun': (8, 1, 13), 'gardener': (9, 8, 10)},
    2: {'hermit': (13, 8, 14), 'nun': (13, 1, 14), 'gardener': (13, 9, 14)},
    3: {'hermit': (2, 11, 3), 'nun': (11, 1, 12), 'gardener': (12, 11, 6)},
    4: {'hermit': (8, 1, 9), 'nun': (8, 1, 13), 'gardener': (8, 1, 10)},
    5: {'hermit': (13, 11, 14), 'nun': (14, 1, 13), 'gardener': (14, 11, 13)},
}


def _identity(name):
    name = ALIASES.get(name, name)
    if name not in NAMES:
        raise KeyError(name)
    return name


def _variant(variant):
    variant = int(variant)
    if variant not in STYLE_NAMES:
        raise ValueError('forest folk study must be 1..5')
    return variant


def _canvas(w, h):
    im = Image.new('P', (w, h), 0)
    return im, ImageDraw.Draw(im)


def _world_body(d, who, variant):
    cloth, shade, light = CLOTH[variant][who]
    # Feet remain planted at row31. Different shoulder/hem shapes describe
    # a person, not a decorative border pasted onto the same robe.
    shoulders = {
        1: [(9, 21), (12, 18), (19, 18), (23, 21), (23, 27), (21, 30), (10, 30), (8, 27)],
        2: [(11, 19), (18, 18), (22, 21), (22, 27), (20, 30), (10, 30), (9, 26)],
        3: [(9, 20), (12, 18), (20, 18), (23, 22), (22, 29), (11, 30), (8, 27)],
        4: [(8, 20), (12, 18), (19, 18), (23, 21), (23, 29), (10, 30), (8, 27)],
        5: [(10, 20), (13, 18), (19, 18), (22, 21), (23, 28), (20, 30), (10, 30), (9, 27)],
    }
    d.line([(13, 27), (13, 30), (11, 31)], fill=1, width=3)
    d.line([(18, 27), (19, 30), (21, 31)], fill=1, width=3)
    d.polygon(shoulders[variant], fill=1)
    d.polygon([(11, 21), (15, 19), (19, 20), (21, 24), (20, 28), (12, 28), (10, 26)], fill=cloth)
    d.polygon([(16, 21), (20, 21), (22, 26), (20, 29), (16, 28)], fill=shade)
    d.line([(11, 22), (12, 26)], fill=light)
    if who == 'nun':
        # The black veil and gray hem remain recognizable in every study.
        d.polygon([(13, 21), (18, 20), (20, 28), (18, 30), (12, 30)], fill=1)
        d.line([(11, 29), (20, 29)], fill=13)
        d.line([(10, 23), (14, 25)], fill=1, width=3)
        d.line([(21, 23), (18, 25)], fill=1, width=3)
        d.line([(14, 25), (17, 25)], fill=6)
        if variant == 5:
            d.line([(10, 21), (12, 23)], fill=14, width=2)
            d.line([(20, 21), (21, 24)], fill=13)
    elif who == 'hermit':
        d.line([(9, 23), (13, 25)], fill=1, width=3)
        d.line([(22, 23), (19, 25)], fill=1, width=3)
        d.point((13, 25), fill=6)
        d.line([(18, 25), (19, 25)], fill=6)
        # A small worn shoulder plate belongs to the hermit knight, rather
        # than a floating heraldic emblem or an unreadable metal filigree.
        d.line([(9, 21), (11, 20), (13, 21)], fill=13)
        d.point((10, 20), fill=14)
    else:
        d.polygon([(13, 22), (19, 22), (21, 28), (13, 28)], fill=11 if variant != 5 else 13)
        d.line([(14, 23), (14, 26)], fill=12 if variant != 5 else 14)
        d.line([(11, 22), (9, 24)], fill=1, width=3)
        d.line([(9, 24), (11, 24)], fill=6)
        d.line([(21, 22), (23, 25)], fill=1, width=3)
        d.point((23, 25), fill=6)


def _world_hood(d, who, variant):
    cloth, shade, light = CLOTH[variant][who]
    hoods = {
        1: [(10, 17), (10, 12), (12, 9), (15, 8), (19, 8), (22, 12), (22, 20), (12, 21)],
        2: [(10, 18), (11, 12), (13, 8), (18, 8), (22, 11), (23, 16), (21, 21), (11, 21)],
        3: [(10, 19), (10, 13), (12, 10), (16, 8), (20, 9), (22, 13), (22, 21), (11, 21)],
        4: [(9, 19), (10, 12), (11, 9), (17, 8), (21, 10), (22, 15), (23, 21), (11, 21)],
        5: [(10, 19), (10, 13), (12, 9), (15, 8), (19, 9), (21, 12), (22, 20), (12, 21)],
    }
    d.polygon(hoods[variant], fill=1)
    if who == 'nun':
        # One broad cream wimple around a pale face; the outer veil stays
        # black even under the pale and silver environment treatments.
        d.polygon([(12, 12), (14, 10), (18, 10), (20, 13), (20, 18), (18, 21), (12, 19)], fill=14 if variant == 2 else 7)
        d.polygon([(13, 13), (15, 12), (18, 12), (19, 14), (18, 18), (15, 19), (13, 17)], fill=6)
        d.line([(13, 13), (15, 12), (17, 12)], fill=7)
        d.point((14, 15), fill=1)
        d.point((18, 15), fill=1)
        d.line([(15, 18), (16, 17), (17, 18)], fill=11)
        d.line([(18, 17), (18, 18)], fill=14)
        d.line([(11, 13), (11, 19)], fill=13)
        d.line([(20, 18), (20, 20)], fill=13)
        return
    d.polygon([(11, 14), (13, 10), (17, 9), (20, 11), (21, 16), (20, 20), (11, 19)], fill=cloth)
    d.line([(12, 13), (14, 10), (17, 10)], fill=light)
    d.polygon([(19, 12), (21, 15), (21, 20), (19, 20)], fill=shade)
    d.polygon([(13, 13), (15, 12), (18, 12), (20, 14), (19, 19), (14, 20), (12, 17)], fill=6)
    d.line([(13, 14), (14, 13), (17, 13)], fill=7)
    if who == 'hermit':
        d.point((14, 15), fill=1)
        d.point((18, 15), fill=1)
        beards = {
            1: [(12, 17), (19, 17), (19, 20), (16, 24), (13, 22)],
            2: [(13, 17), (19, 17), (19, 21), (17, 25), (14, 22)],
            3: [(12, 17), (19, 17), (19, 21), (15, 23), (12, 20)],
            4: [(12, 17), (19, 17), (20, 20), (17, 23), (13, 23), (12, 20)],
            5: [(13, 17), (19, 17), (19, 20), (16, 24), (12, 21)],
        }
        d.polygon(beards[variant], fill=1)
        d.polygon([(13, 18), (18, 18), (18, 20), (16, 22), (14, 21)], fill=13)
        d.line([(13, 18), (14, 20), (16, 21)], fill=14)
        d.line([(15, 17), (17, 17)], fill=11)
    else:
        d.line([(13, 15), (20, 15)], fill=1, width=2)
        d.line([(20, 15), (21, 18)], fill=1)
        d.polygon([(13, 18), (19, 18), (18, 22), (15, 23), (12, 20)], fill=11)
        d.line([(14, 19), (15, 21), (17, 20)], fill=12)


def _world_tool(d, variant):
    # A grounded cultivation staff: two broad tines/hook and a gripped shaft.
    # It is not luminous, a projectile, or a detached item marker.
    d.line([(8, 13), (8, 30)], fill=1, width=3)
    d.line([(8, 13), (8, 30)], fill=12)
    if variant in (1, 4):
        d.line([(8, 13), (8, 8)], fill=1, width=3)
        d.line([(11, 9), (11, 12), (8, 14)], fill=1, width=3)
        d.line([(8, 9), (8, 13), (10, 12)], fill=13 if variant == 1 else 12)
        d.line([(11, 10), (11, 12)], fill=14 if variant == 1 else 13)
    else:
        d.line([(8, 14), (8, 12), (9, 10), (10, 9), (12, 10), (12, 12)], fill=1, width=3)
        d.line([(8, 13), (9, 11), (10, 10), (11, 10)], fill=13 if variant == 2 else 12)
        d.point((11, 10), fill=14 if variant == 2 else 6)
    d.line([(8, 24), (10, 24)], fill=6)


def _world(name, variant):
    who = _identity(name)
    variant = _variant(variant)
    im, d = _canvas(32, 32)
    _world_body(d, who, variant)
    if who == 'gardener':
        _world_tool(d, variant)
    _world_hood(d, who, variant)
    return im


def supports_frame(sheet, name):
    return ((sheet == 'npc' and name in NAMES + tuple(ALIASES)) or
            (sheet == 'face' and name in NAMES))


def frame(sheet, name, variant):
    if not supports_frame(sheet, name):
        raise KeyError((sheet, name))
    if sheet == 'npc':
        return _world(name, variant), 'folk'
    im = Image.new('P', (64, 64), 0)
    im.paste(portrait(name, variant), (0, 0))
    return im, 'portrait'


def portrait_palette(name, variant):
    _identity(name)
    _variant(variant)
    return list(R.PALETTES['hero'])


def _bust(d, who, variant):
    cloth, shade, light = CLOTH[variant][who]
    contours = {
        1: [(3, 47), (4, 38), (13, 31), (21, 29), (32, 30), (42, 36), (45, 47)],
        2: [(5, 47), (7, 37), (16, 30), (30, 29), (39, 36), (43, 47)],
        3: [(3, 47), (5, 36), (15, 29), (30, 29), (42, 36), (46, 47)],
        4: [(2, 47), (3, 37), (12, 30), (30, 29), (43, 34), (46, 47)],
        5: [(4, 47), (7, 37), (16, 30), (31, 30), (41, 36), (44, 47)],
    }
    d.polygon(contours[variant], fill=1)
    d.polygon([(6, 46), (8, 38), (16, 32), (24, 31), (36, 35), (41, 46)], fill=cloth)
    d.polygon([(24, 32), (35, 33), (42, 38), (44, 47), (25, 47)], fill=shade)
    d.polygon([(9, 39), (15, 34), (19, 34), (16, 39), (13, 46), (7, 46)], fill=light)
    d.line([(20, 37), (18, 44)], fill=shade)
    if who == 'hermit':
        d.polygon([(6, 38), (10, 34), (16, 33), (17, 36), (13, 39), (7, 40)], fill=1)
        d.polygon([(8, 37), (11, 35), (15, 35), (13, 37), (8, 38)], fill=13)
        d.line([(9, 36), (13, 35)], fill=14)
    elif who == 'nun':
        d.polygon([(17, 32), (31, 32), (36, 47), (14, 47)], fill=1)
        d.line([(16, 45), (33, 45)], fill=13)
        d.polygon([(17, 41), (20, 40), (24, 43), (28, 40), (31, 42), (28, 45), (23, 45), (20, 44)], fill=1)
        d.line([(20, 42), (23, 43), (26, 43), (28, 42)], fill=6, width=2)
    else:
        d.polygon([(18, 35), (30, 35), (35, 47), (16, 47)], fill=11 if variant != 5 else 13)
        d.polygon([(19, 37), (23, 36), (22, 44), (19, 46)], fill=12 if variant != 5 else 14)


def _portrait_face(d, who):
    d.polygon([(17, 14), (22, 11), (28, 12), (32, 17), (31, 26), (27, 30), (20, 29), (16, 23)], fill=6)
    d.polygon([(17, 15), (21, 13), (25, 13), (22, 17), (21, 22), (17, 21)], fill=7)
    d.polygon([(30, 18), (32, 20), (30, 26), (27, 28), (27, 25)], fill=12)
    if who == 'gardener':
        d.polygon([(15, 18), (31, 19), (33, 21), (31, 24), (16, 23)], fill=1)
        d.line([(17, 19), (28, 20)], fill=11)
        d.line([(31, 22), (34, 28)], fill=1, width=2)
        d.line([(23, 24), (23, 26)], fill=7)
    else:
        d.line([(18, 18), (21, 17)], fill=11)
        d.line([(27, 17), (30, 18)], fill=11)
        d.line([(19, 20), (20, 20)], fill=1)
        d.line([(28, 20), (29, 20)], fill=1)
        d.line([(24, 22), (24, 24)], fill=7)


def portrait(name, variant):
    who = _identity(name)
    variant = _variant(variant)
    im, d = _canvas(48, 48)
    cloth, shade, light = CLOTH[variant][who]
    _bust(d, who, variant)
    contours = {
        1: [(10, 29), (10, 17), (13, 8), (20, 3), (29, 3), (36, 9), (38, 23), (34, 35), (15, 35)],
        2: [(10, 31), (11, 17), (15, 6), (22, 2), (29, 4), (37, 12), (39, 22), (35, 36), (14, 36)],
        3: [(10, 32), (10, 18), (14, 8), (23, 3), (31, 5), (37, 13), (38, 28), (33, 35), (14, 35)],
        4: [(8, 31), (9, 17), (12, 6), (25, 3), (33, 7), (37, 17), (39, 34), (13, 36)],
        5: [(11, 30), (10, 18), (13, 8), (20, 3), (29, 4), (35, 10), (38, 25), (33, 35), (15, 35)],
    }
    d.polygon(contours[variant], fill=1)
    if who == 'nun':
        # Soft study-specific outer cloth, but the face remains in a black
        # veil with a white wimple, gray edge and one connected tear.
        d.polygon([(12, 28), (12, 16), (15, 9), (21, 6), (29, 7), (34, 14), (35, 29), (32, 35), (15, 34)], fill=1)
        d.line([(12, 15), (14, 10), (18, 7)], fill=13)
        d.polygon([(15, 17), (18, 11), (25, 9), (31, 12), (34, 19), (33, 28), (29, 33), (20, 33), (15, 27)], fill=14 if variant == 2 else 7)
        _portrait_face(d, who)
        d.line([(21, 28), (25, 26), (28, 28)], fill=11)
        d.line([(29, 23), (29, 27)], fill=14)
        d.point((28, 27), fill=15)
        d.line([(33, 20), (34, 29), (31, 33)], fill=13)
        if variant == 5:
            d.polygon([(13, 32), (16, 35), (13, 40), (8, 43), (10, 36)], fill=14)
            d.line([(35, 33), (38, 38)], fill=13, width=2)
    else:
        d.polygon([(12, 27), (12, 17), (16, 9), (22, 6), (29, 7), (34, 13), (36, 27), (32, 33), (16, 33)], fill=cloth)
        d.polygon([(13, 17), (17, 10), (22, 7), (25, 7), (20, 13), (17, 23), (14, 25)], fill=light)
        d.polygon([(29, 10), (34, 15), (36, 28), (32, 33), (30, 26)], fill=shade)
        _portrait_face(d, who)
        if who == 'hermit':
            beard = {
                1: [(16, 25), (21, 26), (26, 26), (32, 24), (33, 30), (29, 35), (24, 40), (18, 36), (15, 31)],
                2: [(17, 25), (23, 27), (31, 24), (32, 31), (28, 36), (26, 42), (20, 38), (16, 32)],
                3: [(16, 25), (22, 27), (30, 25), (33, 29), (31, 35), (24, 38), (17, 34), (15, 30)],
                4: [(15, 25), (22, 27), (31, 25), (34, 30), (31, 36), (24, 39), (17, 37), (14, 31)],
                5: [(17, 25), (23, 27), (31, 24), (32, 31), (27, 38), (23, 41), (17, 35), (15, 30)],
            }
            d.polygon(beard[variant], fill=1)
            d.polygon([(17, 27), (22, 29), (29, 27), (31, 30), (28, 34), (24, 37), (19, 33), (16, 30)], fill=13)
            d.polygon([(17, 28), (20, 29), (22, 33), (25, 35), (23, 36), (19, 32)], fill=14)
            d.line([(21, 27), (25, 28), (28, 26)], fill=11)
        else:
            d.polygon([(16, 26), (22, 28), (30, 26), (31, 31), (27, 36), (22, 37), (17, 33)], fill=1)
            d.polygon([(18, 28), (23, 30), (29, 28), (28, 33), (23, 35), (19, 32)], fill=11)
            d.line([(19, 29), (22, 32), (25, 33)], fill=12, width=2)
            _portrait_tool(d, variant)
    return im


def _portrait_tool(d, variant):
    d.line([(7, 18), (7, 47)], fill=1, width=4)
    d.line([(6, 18), (6, 47)], fill=12, width=2)
    if variant in (1, 4):
        d.line([(7, 20), (4, 16), (4, 10)], fill=1, width=3)
        d.line([(7, 20), (10, 16), (10, 11)], fill=1, width=3)
        d.line([(5, 11), (5, 15), (7, 18), (9, 15), (9, 12)], fill=13 if variant == 1 else 12)
        d.point((5, 11), fill=14)
    else:
        d.line([(7, 20), (4, 16), (4, 12), (7, 9), (10, 9), (12, 12), (12, 15)], fill=1, width=3)
        d.line([(6, 18), (5, 15), (5, 13), (7, 11), (10, 11), (11, 13)], fill=13 if variant == 2 else 12)
        d.line([(7, 10), (9, 10)], fill=14 if variant == 2 else 6)
    d.polygon([(5, 39), (8, 38), (11, 40), (10, 43), (6, 43)], fill=1)
    d.line([(6, 40), (9, 40), (9, 42)], fill=6, width=2)


def _rgba(im, palette):
    return R.rgba(im, palette)


def preview(outdir='/workspace/setup/forest-concepts/folk'):
    """Export source evidence only; never label these as emulator captures."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default()
    width, height = 180, 98
    board = Image.new('RGB', (width * 5, height * 3 + 25), '#182028')
    sil = board.copy()
    gray = board.copy()
    for page in (board, sil, gray):
        ImageDraw.Draw(page).text((5, 5), 'SOURCE STUDIES / native 32px bodies and 48px portraits / not emulator captures', font=font, fill='#f0d8a0')
    report = []
    for row, who in enumerate(NAMES):
        for variant in range(1, 6):
            x = (variant - 1) * width
            y = 25 + row * height
            world = _world(who, variant)
            bust = portrait(who, variant)
            palette = portrait_palette(who, variant)
            box = world.getbbox()
            assert box and 14 <= box[2] - box[0] <= 18 and 22 <= box[3] - box[1] <= 24, (who, variant, box)
            assert box[3] == 32, (who, variant, box)
            for image in (world, bust):
                assert image.mode == 'P' and set(image.tobytes()) <= set(range(16))
            for palette_color in palette:
                assert all(int(palette_color[j:j+2],16) % 8 == 0 for j in (1, 3, 5))
            for suffix, image in (('body', world), ('portrait', bust)):
                image = image.copy()
                image.putpalette([int(c[j:j+2],16) for c in palette for j in (1,3,5)])
                image.save(outdir / f'{variant}-{who}-{suffix}.png', transparency=0)
            a = _rgba(world, palette)
            b = _rgba(bust, palette)
            for page, mode in ((board, 'normal'), (sil, 'silhouette'), (gray, 'gray')):
                draw = ImageDraw.Draw(page)
                draw.text((x+5, y+1), str(variant)+' '+STYLE_NAMES[variant]+' / '+who, font=font, fill='#e8e0c0')
                draw.rectangle((x+4, y+20, x+76, y+88), fill='#385038')
                draw.rectangle((x+42, y+20, x+76, y+88), fill='#685838')
                aa, bb = a.copy(), b.copy()
                if mode == 'silhouette':
                    aa = Image.new('RGBA', a.size, '#f0e8c0');aa.putalpha(a.getchannel('A'))
                    bb = Image.new('RGBA', b.size, '#f0e8c0');bb.putalpha(b.getchannel('A'))
                elif mode == 'gray':
                    aa = a.convert('L').convert('RGBA');aa.putalpha(a.getchannel('A'))
                    bb = b.convert('L').convert('RGBA');bb.putalpha(b.getchannel('A'))
                page.paste(aa, (x+5, y+51), aa)
                page.paste(aa, (x+42, y+51), aa)
                page.paste(bb, (x+100, y+31), bb)
            report.append({'variant':variant, 'style':STYLE_NAMES[variant], 'identity':who,
                           'body_canvas':[32,32], 'body_bounds':list(box),
                           'portrait_canvas':[48,48], 'portrait_bounds':list(bust.getbbox()),
                           'body_palette':'folk', 'portrait_palette':palette})
    for name, image in (('overview', board), ('silhouette', sil), ('grayscale', gray)):
        image.save(outdir/(name+'.png'))
        image.resize((image.width*2,image.height*2),Image.Resampling.NEAREST).save(outdir/(name+'-2x.png'))
    (outdir/'source-review.json').write_text(json.dumps({'method':'Native source studies, not emulator frames.', 'frames':report}, indent=2)+'\n')
    return report


if __name__ == '__main__':
    preview()
