"""Indexed native illustrations and field glyphs for BARTGAME's card album."""
from PIL import Image, ImageDraw

from reboot_actors import ink_rows


RARITIES = ('common', 'uncommon', 'rare', 'ultra_rare')
RARITY_RAMPS = (
    ('#284838', '#508858', '#a0c878'),
    ('#183848', '#3088a8', '#88d8e0'),
    ('#202848', '#5058b8', '#a8b8f0'),
    ('#604020', '#b88028', '#f0d070'),
)
OUTLINE = '#101820'
PAPER = '#f8f0d8'
GROUND_PALETTE = ('#000000', OUTLINE, PAPER, '#405048',
                  *(color for ramp in RARITY_RAMPS for color in ramp))


def ground_card(rarity):
    """Reuse the same tilted card mask in all four ink ramps."""
    low, mid, high = (4 + rarity * 3 + offset for offset in range(3))
    return [row.format(o='1', d=format(low, 'x'), m=format(mid, 'x'),
                       h=format(high, 'x'), w='2') for row in (
        '...{o}{o}{o}{o}.',
        '..{o}{h}{h}{m}{o}.',
        '..{o}{h}{w}{m}{o}.',
        '.{o}{m}{w}{h}{m}{o}.',
        '.{o}{h}{m}{m}{d}{o}.',
        '.{o}{m}{m}{d}{o}..',
        '.{o}{d}{d}{o}{o}..',
        '..{o}{o}{o}...',
    )]


def bubble(width, height, y):
    im = Image.new('P', (32, 32))
    d = ImageDraw.Draw(im)
    left, right = 16 - width // 2, 16 + width // 2
    bottom = y + height
    d.polygon([(left + 3,y),(right - 3,y),(right,y + 3),(right,bottom - 3),
               (right - 3,bottom),(left + 3,bottom),(left,bottom - 3),
               (left,y + 3)], fill=11, outline=1)
    d.polygon([(left + 3,y + 1),(right - 3,y + 1),(right - 1,y + 3),
               (right - 1,bottom - 4),(right - 3,bottom - 2),
               (left + 3,bottom - 2),(left + 1,bottom - 4),(left + 1,y + 3)], fill=12)
    d.ellipse((14,bottom + 1,17,bottom + 4), fill=12, outline=1)
    d.point((14,bottom + 6), fill=1)
    d.point((15,bottom + 6), fill=12)
    return ink_rows(im)


def build_sheets():
    return (
        dict(name='trading_card', w=8, h=8, pal='portrait',
             frames={name: ground_card(i) for i, name in enumerate(RARITIES)}),
        dict(name='card_bubble', w=32, h=32, pal='fx', frames={
            'pop_1': bubble(8, 6, 12), 'pop_2': bubble(14, 10, 9),
            'open': bubble(22, 16, 5), 'bob': bubble(22, 16, 4),
        }),
    )


class Painting:
    """Rasterize the illustration's native paths directly into 48px and 24px."""

    def __init__(self, size, background):
        self.image = Image.new('P', (size, size), 2)
        self.draw = ImageDraw.Draw(self.image)
        self.scale = size / 48
        if background == 'forest':
            self.polygon([(0,0),(16,0),(9,12),(13,22),(6,33),(0,31)], 3)
            self.polygon([(44,0),(47,0),(47,41),(35,41),(38,28),(34,22),(41,15)], 3)
            self.ellipse((3,35,46,49), 3)
            self.line([(3,10),(12,8),(19,9),(32,6),(44,7)], 4)
        elif background == 'stone':
            self.polygon([(0,0),(47,0),(47,6),(14,10),(0,8)], 3)
            self.polygon([(0,31),(17,28),(32,31),(47,26),(47,47),(0,47)], 3)
            self.line([(0,37),(15,33),(28,36),(47,33)], 4)
            self.line([(0,43),(22,39),(47,41)], 4)
        else:
            self.ellipse((4,3,43,43), 3)
            self.arc((3,4,44,43), 183, 332, 4)
            self.arc((6,6,41,43), 10, 151, 4)

    def points(self, points):
        return [tuple(int(value * self.scale) for value in point) for point in points]

    def box(self, box):
        return tuple(int(value * self.scale) for value in box)

    def polygon(self, points, color, outline=None):
        self.draw.polygon(self.points(points), fill=color, outline=outline)

    def ellipse(self, box, color, outline=None):
        self.draw.ellipse(self.box(box), fill=color, outline=outline)

    def line(self, points, color, width=1):
        self.draw.line(self.points(points), fill=color, width=max(1, round(width * self.scale)))

    def arc(self, box, start, end, color, width=1):
        self.draw.arc(self.box(box), start, end, fill=color, width=max(1, round(width * self.scale)))

    def frame(self):
        """A clipped paper corner and the same fine rim at either size."""
        last = self.image.width - 1
        for x,y,dx,dy in ((0,0,1,1),(last,0,-1,1),(0,last,1,-1),(last,last,-1,-1)):
            self.draw.polygon([(x,y),(x+dx,y),(x,y+dy)], fill=0)
        self.draw.polygon([(2,0),(last-2,0),(last,2),(last,last-2),
                           (last-2,last),(2,last),(0,last-2),(0,2)], outline=1)
        self.draw.polygon([(3,1),(last-3,1),(last-1,3),(last-1,last-3),
                           (last-3,last-1),(3,last-1),(1,last-3),(1,3)], outline=14)


def bloom(p):
    p.ellipse((8,40,38,46), 3)
    p.line([(23,25),(24,34),(20,40),(14,43)], 1, 5)
    p.line([(24,33),(28,40),(34,42)], 1, 5)
    p.line([(23,25),(24,34),(20,40),(14,42)], 10, 2)
    p.line([(24,34),(28,40),(34,42)], 9, 2)
    p.polygon([(22,34),(13,30),(10,31),(14,37),(22,37)], 9, 1)
    p.polygon([(25,34),(33,28),(38,28),(34,35),(26,38)], 10, 1)
    for box in ((8,12,23,26),(10,6,25,20),(20,4,33,18),
                (28,9,39,23),(24,18,37,31),(12,20,26,31)):
        p.ellipse(box, 6, 1)
        x,y,right,bottom = box
        p.arc((x+2,y+2,right-2,bottom-2), 185, 312, 8, 2)
    p.ellipse((16,13,32,26), 12, 1)
    p.ellipse((18,15,29,22), 13)
    p.line([(21,18),(21,20)], 1, 2)
    p.line([(27,18),(27,20)], 1, 2)
    p.line([(22,24),(26,24)], 5)


def peddler(p):
    p.polygon([(8,45),(11,31),(20,27),(34,28),(41,38),(42,46)], 5, 1)
    p.polygon([(12,45),(15,32),(23,34),(33,32),(36,46)], 10, 1)
    p.line([(16,44),(18,36),(28,37),(33,35)], 11, 2)
    p.polygon([(10,19),(11,12),(16,7),(23,11),(30,8),(37,10),
               (40,18),(44,25),(39,33),(27,36),(15,34),(7,29)], 6, 1)
    p.polygon([(10,23),(19,19),(36,18),(42,24),(37,30),(24,33),(13,30)], 7)
    p.line([(10,26),(17,28),(26,29),(36,25),(41,24)], 1, 2)
    p.line([(16,29),(23,31),(33,29)], 8)
    for x,y in ((17,15),(32,15)):
        p.ellipse((x-5,y-5,x+4,y+4), 12, 1)
        p.ellipse((x-2,y-2,x+2,y+2), 1)
        p.ellipse((x-2,y-2,x-1,y-1), 15)


def blightseeds(p):
    for x,y,r in ((14,32,8),(35,33,8),(24,21,13)):
        p.ellipse((x-r,y-r,x+r,y+r), 6, 1)
        p.polygon([(x-r,y-3),(x-5,y-r+2),(x+3,y-r+3),(x+7,y-4),
                   (x+3,y+3),(x-4,y+5)], 7)
        p.line([(x-r+3,y-3),(x-3,y-r+4),(x+2,y-r+4)], 8, 2)
        p.line([(x-3,y-r+2),(x-1,y-r-3),(x+3,y-r-6)], 10, 2)
    p.polygon([(24,12),(25,15),(29,16),(25,17),(24,21),(23,17),(20,16),(23,15)], 13)


def healthy_tree(p):
    p.polygon([(20,17),(27,18),(27,32),(29,37),(36,42),(32,44),(24,41),
               (19,45),(12,44),(18,39)], 9, 1)
    p.line([(23,23),(22,36),(18,41)], 11, 2)
    for box in ((5,12,27,31),(20,12,43,30),(11,5,37,25),(9,20,32,35)):
        p.ellipse(box, 6, 1)
        x,y,right,bottom = box
        p.ellipse((x+2,y+2,right-3,bottom-5), 7)
        p.arc((x+4,y+3,right-4,bottom-5), 178, 282, 8, 2)
    p.line([(22,33),(22,24),(28,21)], 9, 2)
    p.line([(9,24),(13,21),(17,22)], 8)
    p.ellipse((35,34,37,36), 12)


def gatekeeper(p):
    p.polygon([(6,43),(12,32),(15,20),(11,18),(19,9),(25,4),(35,17),
               (33,26),(39,44),(30,45),(21,42),(12,46)], 6, 1)
    p.polygon([(12,40),(17,27),(19,17),(24,8),(29,14),(22,23),(23,42)], 7)
    p.polygon([(18,23),(18,19),(24,15),(30,19),(31,25),(26,30),(20,28)], 1)
    p.line([(22,22),(24,22)], 13, 2)
    p.line([(27,21),(28,21)], 13, 2)
    p.line([(34,42),(35,24),(37,14)], 1, 4)
    p.line([(34,42),(35,24),(37,14)], 10, 2)
    p.polygon([(35,15),(31,12),(32,8),(35,5),(36,9),(39,3),(42,8),(42,13),(38,16)], 12, 1)
    p.polygon([(37,13),(35,11),(38,7),(40,10),(39,13)], 15)
    p.line([(14,32),(12,39),(17,39)], 8, 2)


def lamp(p):
    p.arc((15,3,32,20), 180, 360, 1, 5)
    p.arc((17,5,30,18), 180, 360, 8, 2)
    p.polygon([(12,13),(35,13),(39,18),(36,22),(36,37),(39,40),(34,44),
               (12,44),(8,40),(11,36),(11,22),(8,18)], 6, 1)
    p.polygon([(15,21),(32,21),(32,36),(15,36)], 9, 1)
    p.polygon([(21,36),(17,32),(19,27),(22,24),(23,29),(27,22),(30,29),
               (29,34),(26,36)], 12)
    p.polygon([(22,35),(21,32),(24,28),(27,33),(26,35)], 15)
    p.line([(11,17),(35,17)], 8, 2)
    p.line([(12,40),(35,40)], 8, 2)
    p.line([(13,22),(13,35)], 7, 2)


def bow(p):
    curve = [(12,5),(25,9),(34,16),(37,26),(28,35),(19,43)]
    p.line(curve, 1, 6)
    p.line(curve, 6, 4)
    p.line([(13,6),(25,11),(32,17),(34,23)], 8, 2)
    p.line([(12,5),(19,43)], 12)
    p.line([(7,29),(36,22)], 11, 2)
    p.polygon([(35,18),(43,20),(37,25),(36,23)], 13, 1)
    p.polygon([(8,28),(4,26),(10,25),(13,27),(12,30),(7,33)], 9, 1)
    p.polygon([(30,13),(29,7),(35,15),(33,18)], 7, 1)
    p.polygon([(30,34),(37,33),(32,38),(28,36)], 6, 1)
    p.line([(33,27),(36,25),(36,22)], 10, 2)


def quill_moth(p):
    p.polygon([(23,25),(13,12),(3,7),(6,24),(16,39),(24,35),
               (31,40),(42,26),(45,9),(34,14)], 6, 1)
    p.polygon([(6,12),(16,17),(22,28),(15,34),(9,24)], 8)
    p.polygon([(42,14),(42,24),(32,36),(26,28),(34,20)], 7)
    for start,tip in (((19,30),(10,17)),((18,34),(8,28)),((27,30),(39,19)),((29,35),(40,29))):
        p.line([start,tip], 5, 3)
        p.line([(start[0],start[1]-1),tip], 8)
    p.ellipse((19,18,29,38), 10, 1)
    p.ellipse((19,15,29,25), 7, 1)
    p.line([(22,21),(22,22)], 12, 2)
    p.line([(27,21),(27,22)], 12, 2)
    p.line([(22,16),(18,11),(14,10)], 9, 2)
    p.line([(27,16),(31,11),(35,10)], 9, 2)
    p.line([(23,28),(24,34)], 11, 2)


def blighted_tree(p):
    p.polygon([(8,45),(13,40),(18,40),(21,30),(18,23),(12,22),(8,17),
               (3,15),(7,13),(15,17),(17,17),(15,6),(18,3),(21,10),
               (25,19),(32,10),(31,5),(35,5),(36,13),(32,19),(39,19),
               (43,16),(45,18),(41,22),(31,24),(28,30),(27,38),(39,43),
               (32,45),(24,42),(19,46)], 6, 1)
    p.line([(17,7),(20,19),(24,25),(24,37),(19,42)], 8, 2)
    p.line([(33,13),(27,20),(27,26)], 7, 2)
    p.line([(12,43),(17,41),(22,34),(23,27)], 9, 2)
    p.line([(38,43),(30,40),(27,35)], 5, 2)
    p.ellipse((23,26,27,31), 12, 1)
    p.ellipse((22,26,25,28), 13)
    p.ellipse((24,32,30,34), 13, 1)
    p.ellipse((23,34,30,37), 12, 1)


def cloak(p):
    p.polygon([(17,5),(30,5),(37,13),(36,20),(43,41),(36,44),(30,41),
               (23,45),(16,42),(7,45),(4,40),(12,20),(11,13)], 6, 1)
    p.polygon([(12,14),(17,7),(27,7),(35,14),(32,22),(19,25),(13,20)], 7, 1)
    p.polygon([(16,15),(20,10),(27,10),(31,14),(31,18),(23,22),(17,20)], 5)
    p.line([(15,14),(19,9),(26,8)], 8, 2)
    p.polygon([(13,23),(19,25),(16,35),(8,42),(7,40)], 8)
    p.polygon([(31,24),(36,24),(40,40),(36,41),(29,36)], 5)
    p.line([(23,27),(18,38)], 9, 2)
    p.polygon([(22,20),(27,20),(28,24),(24,28),(20,24)], 12, 1)
    p.ellipse((22,22,24,24), 15)


def moth_confessor(p):
    p.polygon([(6,33),(8,23),(12,16),(19,21),(23,18),(30,19),(36,16),
               (39,24),(40,38),(35,41),(31,40),(28,44),(22,41),(16,44),
               (13,40),(6,42),(8,37)], 6, 1)
    p.polygon([(10,32),(11,23),(15,21),(20,26),(21,37),(16,41),(14,37),(10,39)], 7)
    p.polygon([(28,25),(34,20),(37,24),(37,37),(34,39),(31,36),(27,41)], 5)
    p.line([(13,24),(16,28),(15,32),(17,35)], 8, 2)
    p.line([(33,24),(32,32),(34,35)], 7, 2)
    p.line([(18,15),(15,8),(10,7)], 1, 4)
    p.line([(27,15),(31,8),(35,7)], 1, 4)
    p.line([(17,14),(14,9),(11,8)], 8, 2)
    p.line([(27,14),(32,9),(34,8)], 8, 2)
    p.ellipse((14,11,32,28), 9, 1)
    p.line([(18,16),(24,14),(28,16)], 10, 2)
    p.polygon([(12,25),(16,21),(21,24),(24,23),(29,21),(33,25),(29,29),
               (24,29),(21,32),(17,29)], 11, 1)
    p.line([(19,18),(20,20)], 15, 2)
    p.line([(26,18),(27,20)], 15, 2)
    p.line([(31,38),(39,13),(42,9)], 1, 5)
    p.line([(32,37),(40,13),(42,10)], 13, 2)
    p.line([(38,18),(36,15),(37,12)], 13, 2)
    p.line([(31,31),(35,33)], 12, 2)


def pacci(p):
    p.line([(13,43),(17,34),(23,23),(28,15)], 1, 8)
    p.line([(13,43),(17,34),(23,23),(28,15)], 6, 5)
    p.line([(12,42),(17,32),(21,24)], 8, 2)
    p.polygon([(23,19),(20,15),(21,9),(25,5),(30,4),(38,7),(42,13),
               (40,20),(35,24),(27,23)], 6, 1)
    p.polygon([(24,15),(24,10),(29,7),(35,8),(38,12),(37,17),
               (33,20),(29,19),(28,16),(31,13),(34,14),(32,16),(34,17),
               (36,14),(33,10),(29,11),(27,14),(29,19),(26,20)], 12)
    p.line([(24,10),(28,7),(33,7)], 15, 2)
    p.line([(20,29),(25,31)], 9, 2)
    p.line([(17,35),(22,37)], 9, 2)


def heart(p):
    p.line([(14,16),(10,11),(11,7)], 1, 6)
    p.line([(32,15),(36,11),(37,6)], 1, 6)
    p.line([(14,16),(11,11),(12,8)], 8, 3)
    p.line([(32,15),(36,10),(36,7)], 7, 3)
    p.polygon([(24,16),(19,11),(12,11),(6,14),(4,23),(7,30),(13,38),
               (20,41),(22,46),(23,39),(18,34),(21,29),(18,25),(23,20)], 6, 1)
    p.polygon([(26,17),(31,12),(39,12),(43,19),(43,28),(37,37),(29,43),
               (25,46),(28,39),(23,34),(26,29),(23,25)], 7, 1)
    p.polygon([(6,21),(9,15),(17,14),(20,17),(15,21),(13,27),(8,29)], 8)
    p.line([(9,18),(15,15),(18,16)], 13, 2)
    p.line([(36,16),(39,21),(38,27),(33,34)], 8, 2)
    p.line([(23,19),(19,25),(22,28),(19,34),(25,39)], 12, 2)
    p.line([(27,20),(24,25),(29,29),(25,35),(29,39)], 12)
    p.ellipse((19,28,21,30), 15)


def summit_guardian(p):
    p.polygon([(7,38),(11,29),(16,22),(24,23),(27,18),(29,8),(37,6),
               (42,10),(46,19),(40,23),(36,26),(37,35),(43,38),(43,43),
               (37,44),(31,39),(17,43),(10,42)], 6, 1)
    p.polygon([(15,33),(20,27),(27,26),(31,22),(31,14),(37,10),
               (41,13),(43,18),(36,19),(34,24),(33,33),(27,36),(18,37)], 7)
    p.polygon([(29,10),(29,5),(34,8),(40,5),(42,11),(45,14),(39,14),(35,11)], 6, 1)
    p.line([(32,16),(39,13),(44,17)], 8, 2)
    p.line([(41,17),(43,17)], 15, 2)
    p.line([(36,21),(42,21)], 1, 2)
    p.ellipse((12,26,25,37), 9, 1)
    p.ellipse((15,27,23,35), 10)
    p.ellipse((17,28,21,32), 13)
    p.line([(17,28),(20,28)], 15)
    p.line([(10,38),(14,37),(19,40),(26,38)], 8, 2)


def bracelet(p):
    p.ellipse((5,12,42,39), 6, 1)
    p.ellipse((12,16,35,32), 3, 1)
    p.arc((7,14,40,38), 174, 286, 8, 3)
    p.arc((6,15,41,37), 10, 157, 5, 3)
    p.arc((12,16,36,33), 9, 143, 7, 2)
    for x,y in ((10,25),(16,34),(24,36),(33,32),(39,24)):
        p.polygon([(x-2,y),(x,y-2),(x+2,y),(x,y+2)], 8, 5)
    p.polygon([(16,12),(22,7),(29,10),(32,15),(26,19),(20,18)], 10, 1)
    p.polygon([(19,12),(22,9),(28,12),(25,15),(21,15)], 11)
    p.line([(20,12),(22,10),(25,11)], 15)


def gilt_leech(p):
    curve = [(6,30),(12,36),(20,39),(29,34),(32,27),(27,21),(19,22),
             (13,17),(14,11),(21,8),(29,8),(35,12)]
    p.line(curve, 1, 11)
    p.line(curve, 6, 8)
    p.line([(7,28),(14,34),(21,35),(28,30),(28,25),(23,23)], 7, 2)
    p.line([(16,15),(17,11),(22,9),(29,10)], 8, 3)
    p.ellipse((29,6,43,19), 7, 1)
    p.polygon([(32,15),(37,11),(43,11),(44,15),(40,19),(35,18)], 5, 1)
    p.ellipse((34,9,38,12), 12, 1)
    p.line([(36,10),(37,10)], 15)
    p.line([(38,16),(41,16)], 8)
    for points in ([(15,32),(12,36)],[(21,34),(22,40)],[(27,30),(31,34)],
                   [(27,23),(31,22)],[(17,24),(18,19)],[(12,12),(16,13)],[(23,4),(24,10)]):
        p.line(points, 5, 2)


def _palette(background, body, detail, lighting):
    return ('#000000', OUTLINE, *background, *body, *detail, *lighting)


FOREST = ('#203038', '#304838', '#486050')
GROTTO = ('#202030', '#303040', '#484858')
STONE = ('#282830', '#404048', '#585850')
HEIRLOOM = ('#202830', '#383040', '#484058')
PETAL = ('#683038', '#a83840', '#d85848', '#f89858')
VERDIGRIS = ('#304028', '#486840', '#709050', '#a8b868')
BARK = ('#483030', '#785038', '#b88858')
BRASS = ('#583828', '#886038', '#b88848', '#e8c078')
BROWN = ('#483038', '#785040', '#a87850', '#d0b080')
VIOLET = ('#382840', '#604068', '#906888', '#c090b8')
LIGHT = ('#c0a868', '#e0c888', '#e8e0b0', PAPER)
EMBER = ('#e06838', '#f0a048', '#f8d070', PAPER)
ROT = ('#883068', '#c04890', '#e088b8', '#f8e0e8')

# Keep these in trading_cards.h's stable card ID order.
CARDS = (
    (bloom, 'forest', _palette(FOREST, PETAL, ('#283828','#507038','#809850'), LIGHT)),
    (peddler, 'stone', _palette(STONE, VERDIGRIS, BARK, LIGHT)),
    (blightseeds, 'heirloom', _palette(HEIRLOOM, VIOLET, BARK, ROT)),
    (healthy_tree, 'forest', _palette(FOREST, VERDIGRIS, BARK, LIGHT)),
    (gatekeeper, 'stone', _palette(STONE, VIOLET, BARK, EMBER)),
    (lamp, 'heirloom', _palette(HEIRLOOM, BRASS, ('#482830','#884838','#b86838'), EMBER)),
    (bow, 'forest', _palette(FOREST, BROWN, ('#486048','#786848','#b89858'), LIGHT)),
    (quill_moth, 'forest', _palette(FOREST, BROWN, ('#283838','#587060','#789880'), LIGHT)),
    (blighted_tree, 'forest', _palette(GROTTO, VIOLET, BARK, ROT)),
    (cloak, 'heirloom', _palette(HEIRLOOM, VERDIGRIS, ('#384838','#687850','#98a870'), LIGHT)),
    (moth_confessor, 'forest', _palette(FOREST, VIOLET, ('#302830','#705868','#c8b8a0'), LIGHT)),
    (pacci, 'heirloom', _palette(HEIRLOOM, BROWN, ('#602838','#906040','#b08858'), EMBER)),
    (heart, 'heirloom', _palette(GROTTO, VIOLET, ('#482840','#785068','#a86890'), ROT)),
    (summit_guardian, 'stone', _palette(STONE, BRASS, ('#482048','#885090','#b880a8'), ROT)),
    (bracelet, 'heirloom', _palette(HEIRLOOM, BRASS, ('#287060','#508868','#90b888'), LIGHT)),
    (gilt_leech, 'stone', _palette(STONE, BRASS, BARK, LIGHT)),
)


def illustrations(size):
    for card, (subject, background, palette) in enumerate(CARDS):
        painting = Painting(size, background)
        subject(painting)
        painting.frame()
        rarity = RARITY_RAMPS[card // 4][2]
        yield painting.image, palette[:14] + (rarity, palette[15])
