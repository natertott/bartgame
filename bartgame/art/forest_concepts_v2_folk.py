"""Fifteen native, static forest quest-giver concepts, with matching busts.

Each role has five different creature/object silhouettes. These painters do
not change AI, frame identifiers, shared palettes or the selected characters.
Every world drawing starts on32x32; every portrait starts independently on48x48.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont
import reboot_core as R

NAMES = ('hermit', 'nun', 'gardener')
ALIASES = {'brother_mark': 'hermit', 'sister_mary_grace': 'nun'}
CONCEPTS = {
    'hermit': ('Snail Sage', 'Morel Abbot', 'Stump Librarian', 'Owl Reader', 'Chipped Teapot Hermit'),
    'nun': ('Weeping Moth Sister', 'Bellflower Veil', 'Mourning Bell', 'Weeping Willow Dryad', 'Tearstained Rag Doll'),
    'gardener': ('Compost Beetle', 'Frog Botanist', 'Carrot Sexton', 'Compost Salamander', 'Mole Planter'),
}


def _identity(name):
    name = ALIASES.get(name, name)
    if name not in NAMES:
        raise KeyError(name)
    return name


def _variant(variant):
    variant = int(variant)
    if not 1 <= variant <= 5:
        raise ValueError('forest v2 folk variant must be 1..5')
    return variant


def _canvas(w=32, h=32):
    image = Image.new('P', (w, h), 0)
    return image, ImageDraw.Draw(image)


def _poly(d, points, ink):
    d.polygon(points, fill=ink, outline=1)


def _oval(d, box, ink):
    d.ellipse(box, fill=ink, outline=1)


def _feet(d, left=12, right=19, ink=11):
    d.line([(left, 28), (left, 30), (left-2, 31)], fill=1, width=3)
    d.line([(right, 28), (right, 30), (right+2, 31)], fill=1, width=3)
    d.point((left-1, 30), fill=ink)
    d.point((right, 30), fill=ink)


def _eyes(d, x0, x1, y, closed=False):
    if closed:
        d.line([(x0-1, y), (x0, y+1), (x0+1, y)], fill=1)
        d.line([(x1-1, y), (x1, y+1), (x1+1, y)], fill=1)
    else:
        d.point((x0, y), fill=1)
        d.point((x1, y), fill=1)


def _book(d, x, y, w=10, h=5):
    d.rectangle((x, y, x+w-1, y+h-1), fill=1)
    d.rectangle((x+1, y+1, x+w-2, y+h-2), fill=6)
    d.line([(x+1, y+1), (x+w//2-1, y+1)], fill=7)
    d.line([(x+w//2, y+1), (x+w//2, y+h-2)], fill=11)
    d.line([(x+1, y+h-2), (x+w-2, y+h-2)], fill=13)


def _plant(d, x, y, large=False):
    if large:
        _poly(d, [(x, y), (x+14, y), (x+12, y+10), (x+3, y+10)], 12)
        d.line([(x+2, y+1), (x+12, y+1)], fill=6)
        d.line([(x+7, y), (x+7, y-9)], fill=1, width=3)
        d.line([(x+7, y-1), (x+7, y-8)], fill=9)
        _poly(d, [(x+6, y-5), (x, y-9), (x, y-4), (x+6, y-2)], 10)
        _poly(d, [(x+8, y-7), (x+14, y-11), (x+14, y-5), (x+8, y-3)], 9)
        d.line([(x+2, y-7), (x+5, y-5)], fill=10)
    else:
        _poly(d, [(x, y), (x+7, y), (x+6, y+5), (x+1, y+5)], 12)
        d.line([(x+1, y+1), (x+6, y+1)], fill=6)
        d.line([(x+3, y), (x+3, y-4)], fill=1)
        d.polygon([(x+3, y-2), (x, y-5), (x, y-2)], fill=10)
        d.polygon([(x+4, y-3), (x+7, y-6), (x+7, y-3)], fill=9)


def _can(d, x, y, large=False):
    if large:
        d.arc((x+2, y-6, x+12, y+5), 180, 355, fill=1, width=3)
        _poly(d, [(x, y), (x+13, y), (x+14, y+10), (x+2, y+12)], 13)
        d.polygon([(x+2, y+2), (x+6, y+1), (x+6, y+9), (x+3, y+10)], fill=14)
        _poly(d, [(x+13, y+3), (x+20, y-2), (x+22, y), (x+15, y+8)], 13)
        d.line([(x+16, y+2), (x+20, y)], fill=14)
    else:
        d.arc((x+1, y-3, x+5, y+2), 180, 350, fill=1)
        d.rectangle((x, y, x+5, y+6), fill=1)
        d.rectangle((x+1, y+1, x+4, y+5), fill=13)
        d.line([(x+1, y+1), (x+1, y+4)], fill=14)
        _poly(d, [(x+5, y+2), (x+8, y), (x+9, y+1), (x+5, y+5)], 13)


def _tear(d, x, y, length=2):
    d.line([(x, y), (x, y+length)], fill=13)
    d.point((x, y+length), fill=14)


def _snail_world():
    im, d = _canvas()
    # The shell rises behind a soft, forward-facing elder, with a broad foot.
    _oval(d, (9, 13, 25, 29), 12)
    d.polygon([(11, 17), (14, 14), (19, 14), (16, 18), (12, 22)], fill=6)
    d.line([(20, 18), (16, 17), (13, 20), (14, 25), (19, 26), (22, 22), (20, 20), (17, 21)], fill=11)
    _poly(d, [(7, 26), (11, 22), (16, 23), (19, 28), (24, 29), (25, 31), (6, 31)], 13)
    d.line([(8, 28), (14, 27), (18, 29)], fill=14)
    _oval(d, (9, 13, 18, 23), 13)
    d.line([(11, 14), (11, 9)], fill=1, width=3)
    d.line([(17, 14), (18, 9)], fill=1, width=3)
    d.line([(11, 13), (11, 10)], fill=13)
    d.line([(17, 13), (18, 10)], fill=13)
    d.point((11, 9), fill=7);d.point((18, 9), fill=7)
    _eyes(d, 12, 16, 18)
    d.line([(13, 21), (15, 21)], fill=11)
    _poly(d, [(10, 22), (17, 22), (16, 26), (13, 28)], 14)
    _book(d, 8, 26, 10, 5)
    return im


def _morel_world():
    im, d = _canvas();_feet(d)
    _poly(d, [(12, 18), (20, 18), (22, 29), (18, 30), (11, 29)], 13)
    d.polygon([(13, 20), (16, 19), (15, 27), (12, 28)], fill=14)
    _poly(d, [(15, 6), (19, 7), (22, 11), (24, 17), (22, 20), (9, 20), (7, 17), (10, 10)], 12)
    d.polygon([(14, 8), (17, 8), (14, 13), (12, 18), (9, 17), (11, 12)], fill=6)
    for box in ((14, 10, 15, 12), (18, 12, 20, 14), (13, 15, 14, 17), (20, 17, 21, 18)):
        d.rectangle(box, fill=11)
    d.line([(10, 20), (22, 20)], fill=11)
    _eyes(d, 14, 18, 22)
    _poly(d, [(13, 24), (19, 24), (18, 27), (16, 29)], 14)
    _book(d, 10, 26, 12, 5)
    return im


def _stump_world():
    im, d = _canvas()
    _poly(d, [(7, 9), (11, 11), (14, 9), (20, 10), (24, 8), (24, 14), (21, 18), (22, 27), (25, 31), (19, 31), (16, 29), (12, 31), (7, 31), (10, 27), (10, 18), (7, 15)], 12)
    d.polygon([(11, 13), (14, 11), (15, 25), (12, 29), (10, 28)], fill=6)
    d.polygon([(20, 13), (22, 13), (19, 19), (21, 28), (18, 29)], fill=11)
    _oval(d, (11, 14, 20, 24), 14)
    _eyes(d, 13, 18, 18)
    d.line([(14, 21), (17, 21)], fill=11)
    _poly(d, [(12, 22), (19, 22), (20, 26), (16, 28), (12, 25)], 13)
    d.line([(13, 23), (14, 25)], fill=14)
    _book(d, 10, 26, 12, 5)
    return im


def _owl_world():
    im, d = _canvas();_feet(d, ink=12)
    _oval(d, (9, 18, 23, 30), 11)
    _poly(d, [(8, 9), (13, 11), (19, 11), (24, 8), (23, 18), (21, 23), (11, 23), (8, 18)], 13)
    d.ellipse((10, 12, 17, 21), fill=6);d.ellipse((16, 12, 22, 21), fill=6)
    d.line([(11, 13), (14, 12)], fill=7)
    _eyes(d, 13, 19, 16, True)
    d.polygon([(15, 18), (17, 18), (16, 21)], fill=12)
    _poly(d, [(8, 22), (12, 23), (13, 29), (9, 28)], 13)
    _poly(d, [(23, 21), (20, 23), (19, 28), (23, 29)], 12)
    _book(d, 11, 25, 11, 5)
    return im


def _teapot_world():
    im, d = _canvas();_feet(d)
    d.ellipse((6, 18, 13, 25), outline=1, width=2)
    d.arc((7, 19, 12, 24), 90, 270, fill=13)
    _oval(d, (9, 15, 23, 29), 13)
    _poly(d, [(21, 19), (24, 16), (25, 17), (24, 22), (21, 25)], 13)
    d.polygon([(11, 18), (14, 16), (16, 17), (14, 25), (11, 25)], fill=14)
    d.line([(10, 15), (22, 15)], fill=1, width=3)
    d.line([(11, 14), (20, 14)], fill=14)
    _oval(d, (14, 10, 18, 14), 13)
    d.point((15, 11), fill=15)
    _eyes(d, 13, 19, 20)
    d.line([(15, 23), (17, 23)], fill=11)
    d.line([(11, 18), (11, 20)], fill=15)
    _book(d, 10, 26, 12, 5)
    return im


def _moth_world():
    im, d = _canvas();_feet(d, ink=13)
    _poly(d, [(6, 23), (7, 14), (10, 10), (14, 15), (15, 28), (11, 30), (7, 27)], 13)
    _poly(d, [(18, 15), (22, 10), (25, 14), (25, 24), (23, 29), (18, 30)], 13)
    d.polygon([(8, 17), (10, 13), (12, 16), (12, 24), (9, 26)], fill=14)
    d.polygon([(21, 17), (23, 14), (24, 24), (21, 27)], fill=8)
    d.line([(13, 12), (11, 8)], fill=1);d.point((11, 8), fill=14)
    d.line([(19, 12), (21, 8)], fill=1);d.point((21, 8), fill=14)
    _poly(d, [(12, 18), (16, 14), (20, 18), (20, 28), (16, 30), (12, 27)], 1)
    _oval(d, (12, 12, 20, 21), 7)
    d.ellipse((13, 14, 19, 20), fill=6)
    _eyes(d, 14, 18, 16)
    d.line([(15, 19), (16, 18), (17, 19)], fill=11)
    _tear(d, 18, 18)
    d.line([(14, 24), (17, 25), (19, 24)], fill=6)
    return im


def _flower_world():
    im, d = _canvas();_feet(d, ink=9)
    d.line([(16, 22), (16, 29)], fill=1, width=5)
    _poly(d, [(11, 24), (8, 21), (8, 25), (13, 28)], 9)
    _poly(d, [(20, 24), (24, 21), (23, 26), (19, 28)], 9)
    _poly(d, [(12, 12), (10, 17), (7, 23), (11, 25), (15, 22), (18, 25), (21, 23), (25, 24), (23, 15), (20, 11)], 13)
    d.polygon([(13, 13), (15, 13), (12, 21), (10, 23), (9, 22)], fill=14)
    d.polygon([(17, 13), (20, 13), (22, 19), (22, 22), (19, 23)], fill=14)
    _poly(d, [(10, 12), (12, 8), (16, 11), (20, 8), (22, 11), (19, 14), (13, 14)], 9)
    _oval(d, (12, 17, 20, 25), 6)
    _eyes(d, 14, 18, 20)
    d.line([(15, 23), (16, 22), (17, 23)], fill=11)
    _tear(d, 18, 22)
    return im


def _bell_world():
    im, d = _canvas();_feet(d, ink=12)
    _oval(d, (14, 8, 18, 12), 12)
    _poly(d, [(11, 13), (20, 13), (22, 21), (25, 28), (23, 30), (7, 30), (6, 28), (9, 21)], 12)
    d.polygon([(11, 16), (14, 14), (14, 24), (10, 27), (8, 28)], fill=6)
    d.polygon([(20, 16), (22, 23), (24, 28), (19, 28)], fill=11)
    d.line([(8, 28), (23, 28)], fill=6)
    _oval(d, (11, 14, 21, 23), 1)
    d.ellipse((13, 15, 19, 22), fill=6)
    _eyes(d, 14, 18, 18)
    d.line([(15, 21), (16, 20), (17, 21)], fill=11)
    _tear(d, 18, 20)
    d.line([(13, 25), (16, 26), (19, 25)], fill=13)
    d.point((11, 16), fill=7)
    return im


def _willow_world():
    im, d = _canvas()
    _poly(d, [(13, 17), (20, 17), (20, 27), (24, 31), (19, 31), (16, 29), (12, 31), (8, 31), (12, 27)], 12)
    d.polygon([(14, 19), (16, 19), (15, 27), (12, 29)], fill=6)
    # A forked woody crown and separated hanging boughs, rather than an
    # unbroken arch that would turn the dryad back into another hooded nun.
    d.line([(16, 16), (16, 11), (12, 7)], fill=1, width=3)
    d.line([(16, 11), (21, 8), (24, 11)], fill=1, width=3)
    d.line([(16, 14), (16, 11), (13, 8)], fill=12)
    _poly(d, [(7, 14), (9, 10), (12, 10), (11, 16), (8, 24), (6, 21)], 13)
    d.polygon([(8, 14), (10, 12), (10, 16), (8, 21)], fill=14)
    _poly(d, [(21, 12), (23, 12), (25, 18), (25, 25), (22, 22), (20, 16)], 13)
    d.polygon([(22, 16), (24, 20), (24, 23), (22, 20)], fill=8)
    _oval(d, (12, 13, 21, 23), 6)
    _eyes(d, 14, 19, 17)
    _tear(d, 19, 19)
    d.line([(15, 21), (16, 20), (17, 21)], fill=11)
    d.line([(11, 23), (14, 26), (17, 26), (21, 23)], fill=1, width=2)
    d.line([(14, 25), (17, 25)], fill=13)
    return im


def _doll_world():
    im, d = _canvas();_feet(d)
    _poly(d, [(12, 19), (19, 19), (22, 26), (21, 30), (10, 30), (9, 26)], 2)
    d.polygon([(12, 21), (15, 21), (14, 28), (11, 28)], fill=13)
    _oval(d, (7, 23, 12, 27), 6);_oval(d, (20, 23, 25, 27), 6)
    _poly(d, [(7, 12), (9, 8), (13, 11), (20, 10), (24, 10), (25, 16), (21, 18), (10, 18)], 1)
    _oval(d, (10, 11, 22, 22), 6)
    d.polygon([(12, 13), (15, 12), (14, 17), (11, 18)], fill=7)
    d.rectangle((13, 15, 14, 16), fill=1);d.rectangle((18, 15, 19, 16), fill=1)
    d.line([(14, 20), (16, 18), (18, 20)], fill=11)
    _tear(d, 20, 18)
    d.line([(11, 18), (12, 19)], fill=12)
    _book(d, 11, 26, 11, 5)
    return im


def _beetle_world():
    im, d = _canvas();_feet(d)
    _oval(d, (7, 16, 25, 30), 12)
    d.polygon([(9, 20), (13, 17), (15, 18), (14, 26), (10, 28)], fill=6)
    d.line([(17, 18), (18, 29)], fill=11)
    d.line([(11, 13), (10, 9)], fill=1);d.line([(19, 13), (21, 9)], fill=1)
    d.polygon([(9, 10), (9, 8), (12, 9), (11, 11)], fill=10)
    d.polygon([(20, 10), (22, 8), (23, 10)], fill=9)
    _oval(d, (10, 11, 21, 21), 13)
    d.ellipse((12, 13, 19, 20), fill=6)
    d.line([(11, 15), (20, 15)], fill=1, width=2)
    d.line([(14, 19), (16, 20), (18, 19)], fill=11)
    _can(d, 6, 24)
    d.point((12, 25), fill=6)
    return im


def _frog_world():
    im, d = _canvas();_feet(d, ink=9)
    _oval(d, (9, 20, 23, 30), 9)
    _oval(d, (8, 9, 15, 17), 9);_oval(d, (18, 9, 24, 17), 9)
    _oval(d, (6, 13, 25, 24), 9)
    d.polygon([(8, 16), (12, 14), (17, 15), (15, 18), (9, 20)], fill=10)
    d.line([(9, 14), (22, 14)], fill=1, width=2)
    d.line([(12, 18), (12, 18)], fill=1);d.point((20, 18), fill=1)
    d.ellipse((10, 19, 22, 23), fill=6)
    d.line([(12, 21), (20, 21)], fill=11)
    _poly(d, [(13, 24), (20, 24), (22, 29), (12, 29)], 11)
    _plant(d, 6, 26)
    d.point((14, 26), fill=6)
    return im


def _carrot_world():
    im, d = _canvas();_feet(d, ink=12)
    _poly(d, [(11, 13), (20, 13), (23, 17), (21, 25), (16, 30), (12, 26), (9, 18)], 4)
    d.polygon([(12, 16), (14, 15), (14, 24), (12, 24), (11, 19)], fill=5)
    d.polygon([(20, 17), (21, 19), (18, 26), (16, 28), (17, 21)], fill=2)
    _poly(d, [(14, 14), (10, 9), (10, 6), (15, 10), (17, 6), (18, 10), (22, 8), (20, 14)], 9)
    d.line([(12, 8), (15, 12)], fill=10)
    d.line([(11, 19), (21, 19)], fill=1, width=2)
    d.line([(14, 24), (16, 25), (18, 24)], fill=11)
    _plant(d, 6, 26)
    d.point((14, 26), fill=6)
    return im


def _salamander_world():
    im, d = _canvas();_feet(d)
    _poly(d, [(13, 27), (9, 28), (8, 26), (8, 23), (10, 22), (8, 21), (6, 23), (6, 28), (8, 30), (13, 31), (15, 29)], 12)
    d.line([(7, 24), (7, 27), (9, 29)], fill=6)
    _oval(d, (10, 18, 23, 30), 11)
    _poly(d, [(10, 15), (11, 11), (15, 9), (20, 10), (22, 13), (25, 14), (25, 19), (21, 22), (13, 20)], 12)
    d.polygon([(12, 12), (15, 10), (19, 11), (18, 14), (12, 15)], fill=9)
    d.line([(11, 14), (22, 14)], fill=1, width=2)
    d.polygon([(15, 17), (24, 16), (24, 19), (20, 21), (14, 19)], fill=6)
    d.point((24, 15), fill=1)
    d.line([(17, 19), (23, 18)], fill=11)
    _poly(d, [(13, 23), (20, 23), (22, 29), (12, 29)], 13)
    _can(d, 16, 24)
    d.point((16, 25), fill=6)
    return im


def _mole_world():
    im, d = _canvas();_feet(d)
    _oval(d, (8, 17, 24, 30), 11)
    _oval(d, (9, 9, 14, 15), 12);_oval(d, (18, 9, 23, 15), 12)
    _oval(d, (9, 11, 23, 23), 12)
    d.polygon([(11, 14), (14, 12), (16, 13), (13, 18), (10, 18)], fill=6)
    d.line([(10, 15), (22, 15)], fill=1, width=2)
    _poly(d, [(14, 18), (19, 18), (20, 20), (17, 23), (13, 21)], 6)
    _oval(d, (6, 23, 13, 28), 13);_oval(d, (20, 23, 25, 28), 13)
    d.line([(7, 24), (9, 24)], fill=14);d.line([(21, 24), (23, 24)], fill=14)
    _plant(d, 12, 26)
    return im


WORLD = {
    'hermit': (_snail_world, _morel_world, _stump_world, _owl_world, _teapot_world),
    'nun': (_moth_world, _flower_world, _bell_world, _willow_world, _doll_world),
    'gardener': (_beetle_world, _frog_world, _carrot_world, _salamander_world, _mole_world),
}


def _snail_portrait():
    im, d = _canvas(48, 48)
    _oval(d, (17, 9, 46, 43), 12)
    d.polygon([(22, 15), (29, 11), (36, 13), (28, 18), (22, 28), (19, 31)], fill=6)
    d.line([(37, 16), (28, 17), (23, 23), (24, 33), (32, 38), (40, 32), (40, 24), (34, 21), (29, 25), (31, 29), (35, 28)], fill=11, width=2)
    _poly(d, [(5, 37), (13, 28), (26, 30), (33, 41), (43, 43), (46, 47), (3, 47)], 13)
    _oval(d, (9, 12, 28, 35), 13)
    d.polygon([(12, 16), (17, 13), (19, 15), (16, 27), (11, 28)], fill=14)
    d.line([(13, 15), (12, 6)], fill=1, width=4);d.line([(25, 15), (27, 5)], fill=1, width=4)
    _oval(d, (9, 2, 15, 8), 14);_oval(d, (24, 1, 30, 7), 14)
    d.point((12, 5), fill=1);d.point((27, 4), fill=1)
    d.line([(16, 28), (20, 29), (24, 27)], fill=11)
    _poly(d, [(10, 32), (25, 32), (25, 39), (19, 44), (13, 39)], 14)
    d.polygon([(12, 34), (17, 34), (16, 39)], fill=15)
    _book(d, 7, 40, 28, 8)
    return im


def _morel_portrait():
    im, d = _canvas(48, 48)
    _poly(d, [(16, 24), (32, 24), (36, 47), (11, 47)], 13)
    d.polygon([(18, 27), (23, 26), (21, 41), (16, 43)], fill=14)
    _poly(d, [(21, 2), (29, 3), (35, 9), (41, 21), (40, 27), (9, 28), (6, 23), (11, 12), (16, 5)], 12)
    d.polygon([(19, 6), (24, 4), (23, 10), (16, 22), (10, 24), (12, 17)], fill=6)
    for pts in ([(24, 7), (28, 8), (29, 13), (25, 15), (23, 12)], [(16, 13), (20, 12), (18, 17), (14, 18)], [(31, 15), (34, 16), (36, 21), (32, 23), (30, 20)], [(21, 20), (25, 18), (27, 22), (24, 25), (20, 24)]):
        d.polygon(pts, fill=11)
    d.line([(10, 27), (38, 27)], fill=11, width=2)
    _eyes(d, 20, 28, 31, True)
    _poly(d, [(17, 34), (29, 34), (30, 39), (24, 45), (18, 41)], 14)
    d.line([(18, 36), (21, 40)], fill=15, width=2)
    _book(d, 10, 41, 28, 7)
    return im


def _stump_portrait():
    im, d = _canvas(48, 48)
    _poly(d, [(5, 11), (11, 16), (12, 9), (20, 7), (33, 9), (38, 14), (39, 8), (44, 5), (44, 20), (38, 28), (40, 47), (5, 47), (10, 31), (8, 24), (3, 20)], 12)
    d.polygon([(13, 13), (18, 11), (18, 34), (12, 42), (10, 35)], fill=6)
    d.polygon([(32, 14), (36, 17), (34, 30), (38, 45), (30, 44)], fill=11)
    _oval(d, (12, 4, 36, 14), 12)
    d.ellipse((17, 7, 31, 11), fill=6);d.line([(20, 9), (27, 9)], fill=11)
    _oval(d, (14, 17, 33, 36), 14)
    _eyes(d, 19, 28, 24, True)
    d.line([(20, 29), (24, 30), (28, 28)], fill=11)
    _poly(d, [(13, 31), (31, 31), (34, 38), (25, 46), (15, 40)], 13)
    d.polygon([(16, 33), (21, 34), (24, 42), (18, 39)], fill=14)
    _book(d, 10, 40, 28, 8)
    return im


def _owl_portrait():
    im, d = _canvas(48, 48)
    _oval(d, (7, 26, 41, 51), 11)
    _poly(d, [(6, 4), (17, 9), (29, 9), (41, 3), (39, 16), (40, 27), (33, 35), (14, 36), (7, 28), (8, 16)], 13)
    d.ellipse((9, 11, 25, 31), fill=6);d.ellipse((23, 11, 38, 31), fill=6)
    d.polygon([(11, 16), (17, 12), (21, 13), (15, 17), (12, 22)], fill=7)
    _eyes(d, 17, 31, 20, True)
    d.polygon([(22, 24), (26, 24), (27, 27), (24, 31), (21, 27)], fill=12)
    _poly(d, [(7, 31), (16, 34), (17, 46), (9, 45)], 13)
    _poly(d, [(40, 30), (32, 34), (30, 46), (40, 47)], 12)
    d.polygon([(20, 34), (27, 34), (25, 42)], fill=14)
    _book(d, 11, 40, 27, 8)
    return im


def _teapot_portrait():
    im, d = _canvas(48, 48)
    d.ellipse((1, 21, 17, 38), outline=1, width=4)
    d.arc((4, 24, 14, 35), 90, 270, fill=13, width=2)
    _oval(d, (10, 15, 38, 46), 13)
    _poly(d, [(34, 24), (41, 18), (46, 18), (45, 26), (40, 33), (35, 35)], 13)
    d.polygon([(13, 23), (18, 18), (22, 19), (19, 34), (13, 36)], fill=14)
    d.line([(12, 16), (36, 16)], fill=1, width=4)
    d.line([(13, 14), (34, 14)], fill=14, width=2)
    _oval(d, (20, 5, 27, 13), 13);d.line([(22, 7), (24, 6)], fill=15)
    _eyes(d, 18, 29, 26, True)
    d.line([(20, 33), (24, 34), (29, 32)], fill=11)
    d.line([(13, 22), (13, 26)], fill=15)
    # One glaze craze is a material chip, not a branching bomb fracture.
    d.line([(31, 18), (30, 22), (32, 24)], fill=8)
    _book(d, 10, 40, 28, 8)
    return im


def _moth_portrait():
    im, d = _canvas(48, 48)
    _poly(d, [(2, 29), (5, 16), (11, 11), (19, 20), (18, 40), (13, 47), (5, 44)], 13)
    _poly(d, [(29, 20), (36, 10), (43, 16), (46, 31), (43, 45), (34, 47), (28, 39)], 13)
    d.polygon([(7, 22), (11, 15), (15, 21), (14, 34), (8, 39), (5, 33)], fill=14)
    d.polygon([(36, 18), (41, 23), (43, 36), (38, 42), (33, 36)], fill=8)
    d.line([(19, 13), (16, 7), (13, 4)], fill=1, width=2)
    d.line([(28, 13), (31, 7), (35, 3)], fill=1, width=2)
    d.point((13, 4), fill=14);d.point((35, 3), fill=14)
    _poly(d, [(18, 24), (30, 24), (33, 47), (14, 47)], 1)
    _oval(d, (15, 10, 33, 31), 7)
    d.ellipse((18, 14, 30, 29), fill=6)
    _eyes(d, 21, 28, 20, True)
    d.line([(21, 27), (24, 25), (27, 27)], fill=11)
    _tear(d, 29, 23, 5)
    d.line([(18, 38), (23, 41), (28, 38)], fill=6, width=3)
    d.line([(17, 45), (30, 45)], fill=13)
    return im


def _flower_portrait():
    im, d = _canvas(48, 48)
    d.line([(24, 28), (24, 47)], fill=1, width=7)
    _poly(d, [(16, 33), (5, 29), (8, 39), (18, 45)], 9)
    _poly(d, [(32, 34), (43, 29), (40, 40), (30, 45)], 9)
    _poly(d, [(17, 9), (13, 15), (9, 24), (4, 34), (13, 37), (20, 31), (26, 37), (32, 32), (42, 36), (41, 25), (36, 12), (29, 8)], 13)
    d.polygon([(17, 12), (22, 10), (17, 24), (10, 33), (7, 32), (11, 23)], fill=14)
    d.polygon([(26, 11), (31, 12), (35, 21), (37, 31), (32, 33), (28, 23)], fill=14)
    _poly(d, [(13, 10), (16, 3), (23, 8), (30, 2), (35, 8), (30, 13), (19, 13)], 9)
    d.line([(18, 6), (22, 10)], fill=10)
    _oval(d, (16, 24, 32, 41), 6)
    d.polygon([(18, 28), (21, 26), (23, 27), (20, 33), (18, 34)], fill=7)
    _eyes(d, 21, 28, 31, True)
    d.line([(21, 38), (24, 36), (27, 38)], fill=11)
    _tear(d, 29, 34, 5)
    return im


def _bell_portrait():
    im, d = _canvas(48, 48)
    _oval(d, (20, 3, 28, 12), 12)
    _poly(d, [(15, 12), (32, 12), (37, 26), (43, 42), (45, 46), (3, 46), (6, 41), (11, 25)], 12)
    d.polygon([(14, 17), (19, 14), (18, 34), (9, 43), (6, 43), (11, 29)], fill=6)
    d.polygon([(31, 16), (36, 27), (41, 43), (32, 43)], fill=11)
    d.line([(6, 44), (42, 44)], fill=6, width=2)
    _oval(d, (14, 12, 34, 32), 1)
    d.ellipse((18, 15, 30, 30), fill=6)
    _eyes(d, 21, 28, 21, True)
    d.line([(21, 28), (24, 26), (27, 28)], fill=11)
    _tear(d, 29, 24, 5)
    d.line([(17, 36), (23, 39), (29, 36)], fill=13, width=3)
    d.point((14, 17), fill=7)
    return im


def _willow_portrait():
    im, d = _canvas(48, 48)
    _poly(d, [(17, 21), (31, 21), (33, 40), (40, 47), (28, 47), (24, 43), (19, 47), (7, 47), (15, 39)], 12)
    d.polygon([(19, 24), (23, 24), (21, 39), (16, 43)], fill=6)
    d.line([(24, 22), (23, 11), (16, 5), (12, 2)], fill=1, width=4)
    d.line([(23, 11), (30, 5), (37, 8)], fill=1, width=4)
    d.line([(24, 20), (23, 11), (17, 6)], fill=12, width=2)
    _poly(d, [(6, 14), (11, 7), (17, 8), (15, 17), (8, 32), (4, 29)], 13)
    d.polygon([(8, 15), (12, 10), (14, 10), (11, 21), (7, 28)], fill=14)
    _poly(d, [(19, 10), (23, 5), (28, 11), (27, 18), (22, 25), (18, 20)], 13)
    _poly(d, [(33, 9), (38, 12), (44, 26), (43, 35), (38, 32), (34, 22), (30, 17)], 13)
    d.polygon([(33, 13), (37, 16), (40, 25), (40, 29), (36, 23)], fill=8)
    _oval(d, (15, 16, 33, 35), 6)
    _eyes(d, 20, 28, 23, True)
    d.line([(21, 31), (24, 29), (27, 31)], fill=11)
    _tear(d, 29, 25, 7)
    d.line([(12, 37), (21, 42), (27, 42), (36, 37)], fill=1, width=4)
    d.line([(13, 37), (21, 41)], fill=12, width=2)
    d.line([(34, 38), (27, 41)], fill=12, width=2)
    d.line([(21, 41), (26, 41)], fill=13, width=2)
    return im


def _doll_portrait():
    im, d = _canvas(48, 48)
    _poly(d, [(14, 30), (32, 30), (40, 47), (6, 47)], 2)
    d.polygon([(13, 35), (19, 34), (17, 45), (10, 46)], fill=13)
    _poly(d, [(3, 13), (6, 2), (15, 8), (31, 7), (41, 5), (45, 19), (36, 25), (9, 25)], 1)
    _oval(d, (9, 8, 38, 36), 6)
    d.polygon([(12, 15), (19, 10), (23, 11), (18, 22), (12, 24)], fill=7)
    _oval(d, (15, 17, 20, 22), 1);_oval(d, (28, 17, 33, 22), 1)
    d.point((16, 18), fill=13);d.point((29, 18), fill=13)
    d.line([(20, 30), (25, 27), (30, 30)], fill=11)
    d.line([(12, 25), (15, 28)], fill=12)
    d.line([(12, 27), (14, 25)], fill=11)
    _tear(d, 32, 24, 7)
    _oval(d, (7, 38, 16, 45), 6);_oval(d, (32, 38, 41, 45), 6)
    _book(d, 15, 41, 19, 7)
    return im


def _beetle_portrait():
    im, d = _canvas(48, 48)
    _oval(d, (5, 21, 44, 51), 12)
    d.polygon([(9, 29), (17, 24), (22, 24), (18, 40), (10, 45)], fill=6)
    d.line([(26, 24), (29, 46)], fill=11, width=2)
    d.line([(18, 13), (14, 5)], fill=1, width=3);d.line([(29, 13), (34, 5)], fill=1, width=3)
    _poly(d, [(10, 7), (11, 2), (17, 5), (15, 9)], 10)
    _poly(d, [(32, 7), (35, 2), (39, 5), (36, 9)], 9)
    _oval(d, (12, 9, 35, 31), 13)
    d.ellipse((17, 13, 31, 28), fill=6)
    d.line([(15, 18), (33, 18)], fill=1, width=4)
    d.line([(17, 18), (28, 18)], fill=11)
    d.line([(20, 26), (24, 28), (29, 26)], fill=11)
    _can(d, 12, 35, True)
    d.line([(9, 37), (13, 39)], fill=13, width=3)
    d.line([(35, 38), (31, 40)], fill=13, width=3)
    return im


def _frog_portrait():
    im, d = _canvas(48, 48)
    _oval(d, (8, 27, 42, 50), 8)
    _oval(d, (8, 5, 22, 23), 9);_oval(d, (28, 5, 41, 23), 9)
    _oval(d, (5, 13, 43, 35), 9)
    d.polygon([(8, 19), (15, 15), (25, 17), (18, 22), (9, 25)], fill=10)
    d.line([(10, 18), (39, 18)], fill=1, width=4)
    d.line([(13, 17), (24, 17)], fill=8)
    d.point((17, 24), fill=1);d.point((32, 24), fill=1)
    d.ellipse((12, 26, 37, 33), fill=6)
    d.line([(16, 29), (32, 29)], fill=11)
    _poly(d, [(19, 35), (32, 35), (35, 47), (16, 47)], 11)
    _plant(d, 4, 38, True)
    d.line([(35, 39), (40, 41)], fill=6, width=3)
    return im


def _carrot_portrait():
    im, d = _canvas(48, 48)
    _poly(d, [(16, 12), (32, 12), (38, 22), (34, 36), (24, 47), (17, 41), (11, 26)], 4)
    d.polygon([(17, 18), (22, 15), (21, 32), (17, 36), (14, 25)], fill=5)
    d.polygon([(31, 17), (35, 23), (30, 38), (25, 43), (27, 29)], fill=2)
    _poly(d, [(20, 15), (13, 8), (12, 1), (22, 9), (25, 1), (28, 9), (36, 4), (32, 15)], 9)
    d.line([(16, 5), (22, 12)], fill=10, width=2)
    d.line([(15, 23), (34, 23)], fill=1, width=4)
    d.line([(34, 24), (36, 31)], fill=1, width=2)
    d.line([(21, 32), (25, 34), (29, 32)], fill=11)
    d.line([(25, 28), (25, 29)], fill=6)
    d.polygon([(28, 39), (31, 36), (29, 42), (26, 44)], fill=11)
    _plant(d, 2, 38, True)
    return im


def _salamander_portrait():
    im, d = _canvas(48, 48)
    _poly(d, [(16, 38), (9, 42), (5, 39), (4, 34), (7, 31), (5, 28), (1, 32), (1, 41), (7, 47), (19, 47)], 12)
    _oval(d, (12, 26, 39, 51), 11)
    _poly(d, [(13, 18), (15, 11), (23, 7), (33, 10), (36, 16), (44, 18), (45, 26), (40, 30), (23, 32), (15, 27)], 12)
    d.polygon([(16, 15), (23, 9), (31, 11), (27, 16), (16, 20)], fill=9)
    d.line([(16, 17), (36, 17)], fill=1, width=4)
    d.polygon([(24, 24), (42, 21), (43, 25), (39, 29), (25, 30), (19, 26)], fill=6)
    d.point((41, 20), fill=1)
    d.line([(27, 27), (40, 26)], fill=11)
    _poly(d, [(20, 35), (33, 35), (37, 47), (17, 47)], 13)
    _can(d, 24, 36, True)
    d.line([(21, 39), (26, 40)], fill=6, width=3)
    return im


def _mole_portrait():
    im, d = _canvas(48, 48)
    _oval(d, (7, 24, 40, 52), 11)
    _oval(d, (10, 6, 20, 19), 12);_oval(d, (29, 7, 39, 19), 12)
    d.ellipse((13, 9, 17, 16), fill=6);d.ellipse((32, 10, 36, 16), fill=6)
    _oval(d, (9, 11, 39, 36), 12)
    d.polygon([(12, 18), (18, 13), (23, 15), (18, 24), (11, 25)], fill=6)
    d.line([(12, 22), (37, 22)], fill=1, width=4)
    _poly(d, [(21, 25), (29, 25), (31, 29), (26, 33), (19, 30)], 6)
    d.line([(14, 29), (20, 30)], fill=13);d.line([(31, 30), (36, 29)], fill=13)
    _oval(d, (3, 35, 15, 46), 13);_oval(d, (33, 35, 45, 46), 13)
    for x in (5, 9, 35, 39):d.line([(x, 37), (x+1, 39)], fill=14)
    _plant(d, 17, 37, True)
    return im


PORTRAIT = {
    'hermit': (_snail_portrait, _morel_portrait, _stump_portrait, _owl_portrait, _teapot_portrait),
    'nun': (_moth_portrait, _flower_portrait, _bell_portrait, _willow_portrait, _doll_portrait),
    'gardener': (_beetle_portrait, _frog_portrait, _carrot_portrait, _salamander_portrait, _mole_portrait),
}


def supports_frame(sheet, name):
    return ((sheet == 'npc' and name in NAMES+tuple(ALIASES)) or
            (sheet == 'face' and name in NAMES))


def frame(sheet, name, variant):
    if not supports_frame(sheet, name):
        raise KeyError((sheet, name))
    who = _identity(name);variant = _variant(variant)
    if sheet == 'npc':
        return WORLD[who][variant-1](), 'folk'
    image = Image.new('P', (64, 64), 0)
    image.paste(portrait(who, variant), (0, 0))
    return image, 'portrait'


def portrait(name, variant):
    return PORTRAIT[_identity(name)][_variant(variant)-1]()


def portrait_palette(name, variant):
    _identity(name);_variant(variant)
    return list(R.PALETTES['hero'])


def preview(outdir='/workspace/setup/forest-concepts-v2/folk'):
    """Static source inspection; none of these panels is an emulator frame."""
    outdir = Path(outdir);outdir.mkdir(parents=True, exist_ok=True)
    cellw, cellh = 184, 104
    board = Image.new('RGB', (cellw*5, cellh*3+26), '#182028')
    silhouette = board.copy();gray = board.copy();font = ImageFont.load_default()
    report = []
    for page in (board, silhouette, gray):
        ImageDraw.Draw(page).text((5, 5), 'STATIC SOURCE CONCEPTS / native 32px bodies + 48px busts / not emulator captures', font=font, fill='#f0d8a0')
    for row, who in enumerate(NAMES):
        for variant in range(1, 6):
            name = CONCEPTS[who][variant-1];body, alias = frame('npc', who, variant)
            bust = portrait(who, variant);palette = portrait_palette(who, variant)
            bbox = body.getbbox();assert bbox, (who, variant)
            extent = (bbox[2]-bbox[0], bbox[3]-bbox[1])
            assert 14 <= extent[0] <= 20 and 20 <= extent[1] <= 26 and bbox[3] == 32, (who, variant, bbox)
            assert body.mode == bust.mode == 'P' and body.size == (32,32) and bust.size == (48,48)
            assert set(body.tobytes()) <= set(range(16)) and set(bust.tobytes()) <= set(range(16))
            a = R.rgba(body, palette);b = R.rgba(bust, palette)
            for suffix, image in (('body', body), ('portrait', bust)):
                image = image.copy();image.putpalette([int(c[j:j+2],16) for c in palette for j in (1,3,5)])
                image.save(outdir/f'{variant}-{who}-{suffix}.png', transparency=0)
            x, y = (variant-1)*cellw, 26+row*cellh
            for page, mode in ((board, 'color'), (silhouette, 'silhouette'), (gray, 'gray')):
                draw = ImageDraw.Draw(page)
                draw.text((x+4, y), f'{variant} {who} / static', font=font, fill='#e8e0c0')
                draw.text((x+4, y+12), name, font=font, fill='#e8e0c0')
                for i, color in enumerate(('#385038', '#685838', '#283028')):
                    draw.rectangle((x+3+i*32,y+29,x+34+i*32,y+94),fill=color)
                aa, bb = a.copy(), b.copy()
                if mode == 'silhouette':
                    aa = Image.new('RGBA', a.size, '#f0e8c0');aa.putalpha(a.getchannel('A'))
                    bb = Image.new('RGBA', b.size, '#f0e8c0');bb.putalpha(b.getchannel('A'))
                elif mode == 'gray':
                    aa = a.convert('L').convert('RGBA');aa.putalpha(a.getchannel('A'))
                    bb = b.convert('L').convert('RGBA');bb.putalpha(b.getchannel('A'))
                for i in range(3):page.paste(aa,(x+3+i*32,y+58),aa)
                page.paste(bb,(x+121,y+34),bb)
            report.append({'variant':variant,'role':who,'concept':name,'world_canvas':[32,32],
                           'world_bounds':list(bbox),'world_extent':list(extent),'world_palette':alias,
                           'world_sha256':hashlib.sha256(body.tobytes()).hexdigest(),
                           'silhouette_sha256':hashlib.sha256(bytes(v!=0 for v in body.tobytes())).hexdigest(),
                           'portrait_canvas':[48,48],'portrait_sha256':hashlib.sha256(bust.tobytes()).hexdigest(),
                           'portrait_palette':palette,'poses':'one static presentation; no runtime animation claimed'})
    for name, image in (('overview',board),('silhouette',silhouette),('grayscale',gray)):
        image.save(outdir/(name+'.png'))
        image.resize((image.width*2,image.height*2),Image.Resampling.NEAREST).save(outdir/(name+'-2x.png'))
    assert len({r['silhouette_sha256'] for r in report}) == 15
    (outdir/'source-review.json').write_text(json.dumps({'method':__doc__,
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'native_live_bodies':15,
        'native_body_instances_with_aliases':25,'native_portraits':15,'appended_frames':0,'concepts':report},indent=2)+'\n')
    return report


if __name__ == '__main__':
    preview()
