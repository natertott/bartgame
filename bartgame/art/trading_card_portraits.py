"""Inward-facing, native 48×64 portraits for the trading table."""

from PIL import Image, ImageDraw

import reboot_core
import sewer_concepts
import sewer_concepts_npcs


SIZE = (48, 64)
BLOOM = list(reboot_core.PALETTES['hero'])
BLOOM[13:15] = ['#709848', '#A0B860']
PEDDLER = sewer_concepts_npcs.peddler_palette(
    (sewer_concepts.RECIPE or {'peddler': 1})['peddler'])
MOSS = [
    '#000000', '#101820', '#203828', '#305038', '#486848', '#689050',
    '#90A860', '#B8C878', '#483830', '#705040', '#A08058', '#D8B880',
    '#D8B878', '#F0D898', '#889080', '#F8E8B8',
]
BROOK = [
    '#000000', '#101820', '#183040', '#204858', '#386878', '#589098',
    '#80B8B0', '#B8D8C0', '#302830', '#604038', '#987050', '#D0A078',
    '#886030', '#C09040', '#F0C860', '#F8E8B0',
]
RIND = [
    '#000000', '#181820', '#382028', '#582830', '#803840', '#A84848',
    '#C86850', '#E09068', '#382830', '#585050', '#888070', '#B0A088',
    '#D0B898', '#E8D0A8', '#987048', '#F8E8C0',
]


def canvas():
    image = Image.new('P', SIZE, 0)
    return image, ImageDraw.Draw(image)


def bloom():
    image, draw = canvas()

    # Rooted silhouette under a broad flower crown. The near leaf turns up
    # toward the trade, and the far leaf folds behind the stem.
    draw.polygon([(22, 31), (30, 34), (29, 45), (26, 49), (30, 54),
                  (35, 57), (34, 60), (27, 61), (23, 58), (19, 61),
                  (12, 61), (11, 58), (16, 55), (18, 50), (17, 44),
                  (11, 46), (7, 45), (4, 42), (5, 39), (10, 39),
                  (15, 36), (20, 36)], fill=8, outline=1)
    draw.polygon([(21, 34), (26, 37), (25, 46), (21, 50), (18, 54),
                  (17, 57), (13, 58), (15, 59), (20, 58), (23, 54),
                  (24, 51), (26, 47), (28, 39)], fill=10)
    draw.line([(22, 38), (21, 45), (19, 49)], fill=13, width=2)
    draw.line([(25, 52), (28, 56), (32, 58)], fill=9, width=2)
    draw.line([(15, 40), (10, 42), (6, 42)], fill=9, width=2)
    draw.line([(14, 43), (9, 44), (7, 43)], fill=10)
    draw.polygon([(26, 40), (29, 39), (32, 43), (37, 41), (40, 37),
                  (44, 36), (45, 38), (43, 41), (45, 40), (44, 43),
                  (39, 46), (34, 49), (29, 48), (25, 45)], fill=9, outline=1)
    draw.polygon([(28, 41), (32, 45), (35, 45), (42, 40), (43, 38),
                  (40, 39), (37, 43), (33, 44), (30, 41)], fill=13)
    draw.line([(35, 46), (40, 44), (43, 42)], fill=10)

    # Five irregular petal planes share a dark red core and orange top edges.
    draw.polygon([(16, 13), (16, 8), (19, 4), (23, 2), (28, 3),
                  (32, 6), (33, 13), (30, 20), (21, 21)], fill=3, outline=1)
    draw.polygon([(18, 11), (20, 6), (24, 4), (28, 5), (30, 8),
                  (29, 12), (24, 15), (21, 17)], fill=4)
    draw.line([(20, 7), (24, 5), (27, 5)], fill=5)
    draw.polygon([(19, 22), (13, 11), (8, 10), (4, 13), (2, 18), (3, 23),
                  (6, 27), (15, 29), (21, 26)], fill=3, outline=1)
    draw.polygon([(4, 18), (7, 13), (11, 12), (15, 14), (17, 19),
                  (11, 20), (7, 23), (4, 22)], fill=4)
    draw.line([(5, 17), (8, 14), (11, 13)], fill=5)
    draw.polygon([(30, 12), (33, 8), (39, 9), (43, 12), (45, 17), (44, 22),
                  (41, 25), (34, 26), (29, 22)], fill=3, outline=1)
    draw.polygon([(32, 14), (35, 10), (39, 11), (42, 14), (42, 18),
                  (37, 20), (32, 18)], fill=4)
    draw.line([(35, 11), (39, 12), (41, 14)], fill=5)
    draw.polygon([(14, 23), (21, 25), (25, 31), (23, 37), (18, 41),
                  (13, 41), (8, 38), (7, 33), (9, 27)], fill=3, outline=1)
    draw.polygon([(9, 32), (12, 27), (16, 26), (20, 29), (18, 34),
                  (12, 36), (9, 35)], fill=4)
    draw.line([(10, 31), (13, 28), (16, 28)], fill=5)
    draw.polygon([(28, 29), (36, 26), (42, 30), (44, 36), (40, 41),
                  (35, 42), (29, 39), (25, 34)], fill=2, outline=1)
    draw.polygon([(33, 29), (38, 29), (42, 33), (41, 36), (36, 37),
                  (31, 34)], fill=3)
    draw.line([(35, 30), (38, 31), (40, 33)], fill=4, width=2)

    # The face is offset toward the person on the right.
    draw.polygon([(19, 18), (24, 14), (32, 14), (39, 17), (42, 22),
                  (41, 28), (36, 33), (28, 35), (23, 33), (18, 29),
                  (17, 23)], fill=6, outline=1)
    draw.polygon([(19, 22), (22, 18), (27, 16), (34, 16), (38, 19),
                  (32, 20), (24, 22), (20, 25)], fill=7)
    draw.polygon([(37, 19), (40, 22), (39, 27), (35, 31), (29, 32),
                  (24, 30), (30, 30), (35, 27)], fill=5)
    draw.line([(25, 23), (25, 26)], fill=1, width=2)
    draw.line([(35, 20), (35, 24)], fill=1, width=2)
    draw.point((26, 23), fill=15)
    draw.point((36, 20), fill=15)
    draw.line([(28, 28), (31, 29), (34, 27)], fill=2)
    draw.point((22, 27), fill=5)
    return image


def peddler():
    image, draw = canvas()
    draw.polygon([(15, 34), (30, 31), (38, 35), (44, 42), (46, 52),
                  (44, 57), (46, 60), (41, 62), (32, 62), (29, 59),
                  (20, 61), (11, 62), (5, 60), (6, 56), (10, 54),
                  (8, 45), (10, 38)], fill=2, outline=1)
    draw.polygon([(15, 36), (28, 34), (32, 37), (27, 45), (22, 55),
                  (15, 58), (10, 59), (12, 54), (10, 47), (12, 40)], fill=3)
    draw.line([(11, 46), (14, 40), (18, 39)], fill=4, width=2)
    draw.line([(33, 55), (37, 59), (40, 59), (43, 58)], fill=3, width=2)
    draw.polygon([(14, 42), (21, 39), (32, 37), (36, 45), (38, 56),
                  (32, 60), (17, 60), (12, 55)], fill=9, outline=8)
    draw.polygon([(17, 43), (24, 41), (31, 41), (33, 45), (32, 55),
                  (27, 58), (17, 57), (15, 53)], fill=10)
    draw.line([(17, 45), (16, 49), (17, 55)], fill=11, width=2)
    draw.polygon([(23, 50), (31, 50), (30, 56), (25, 57), (22, 54)], fill=9)
    draw.line([(23, 50), (28, 50)], fill=11)
    draw.line([(18, 42), (18, 38), (21, 36)], fill=11, width=2)
    draw.line([(30, 41), (34, 36)], fill=8, width=3)
    draw.rectangle((29, 39, 32, 42), fill=13, outline=12)
    draw.point((29, 39), fill=14)
    draw.polygon([(15, 46), (12, 45), (8, 48), (5, 47), (2, 48), (1, 51),
                  (5, 53), (10, 53), (16, 51)], fill=3, outline=1)
    draw.line([(3, 49), (7, 50), (13, 47)], fill=4, width=2)
    draw.polygon([(34, 42), (39, 40), (43, 44), (43, 49), (39, 51),
                  (36, 49), (34, 46)], fill=3, outline=1)
    draw.line([(36, 43), (38, 42), (40, 44)], fill=4)

    # Wide mouth, asymmetric eye lobes and a light curved jaw place the
    # shopkeeper unmistakably in the same frog family as his world sprite.
    draw.polygon([(9, 17), (14, 12), (23, 11), (30, 11), (37, 14),
                  (43, 19), (45, 25), (43, 31), (38, 36), (31, 41),
                  (21, 42), (13, 39), (7, 36), (3, 30), (3, 24)], fill=3, outline=1)
    draw.polygon([(5, 24), (8, 18), (15, 15), (23, 14), (30, 16),
                  (27, 20), (16, 22), (12, 27), (5, 28)], fill=4)
    draw.polygon([(38, 17), (43, 22), (43, 28), (38, 34), (32, 38),
                  (28, 34), (33, 28), (36, 22)], fill=2)
    draw.polygon([(6, 31), (12, 30), (20, 32), (29, 30), (35, 28),
                  (34, 33), (29, 37), (21, 39), (12, 37), (8, 34)], fill=5)
    draw.line([(10, 34), (16, 36), (22, 37), (26, 36)], fill=6)
    for x, y, offset in ((8, 5, 1), (27, 8, 0)):
        draw.polygon([(x, y+5), (x+3, y+1), (x+8, y), (x+12, y+3),
                      (x+14, y+7), (x+13, y+13), (x+9, y+16),
                      (x+4, y+15), (x+1, y+12)], fill=3, outline=1)
        draw.polygon([(x+2, y+6), (x+5, y+3), (x+9, y+3), (x+12, y+6),
                      (x+11, y+11), (x+8, y+13), (x+4, y+12),
                      (x+2, y+9)], fill=7)
        draw.line([(x+3, y+10), (x+7, y+12), (x+11, y+10)], fill=6)
        draw.rectangle((x+3+offset, y+6, x+5+offset, y+10), fill=1)
        draw.point((x+4+offset, y+6), fill=15)
    draw.line([(6, 29), (12, 30), (20, 31), (28, 29), (33, 27)], fill=1, width=2)
    draw.line([(31, 29), (34, 26), (32, 25)], fill=2)
    draw.point((8, 25), fill=2)
    draw.point((13, 24), fill=2)
    return image


def moss_archivist():
    image, draw = canvas()
    draw.polygon([(26, 26), (35, 27), (40, 34), (44, 44), (46, 59),
                  (42, 63), (12, 63), (8, 59), (10, 50), (7, 44),
                  (10, 35), (17, 30)], fill=3, outline=1)
    draw.polygon([(16, 34), (25, 31), (23, 40), (18, 46), (17, 58),
                  (11, 60), (12, 53), (11, 46), (12, 39)], fill=4)
    draw.polygon([(30, 31), (36, 31), (42, 40), (44, 52), (44, 59),
                  (40, 62), (36, 60), (39, 49), (34, 42)], fill=2)
    draw.polygon([(20, 35), (29, 32), (34, 36), (34, 46), (30, 49),
                  (25, 45), (23, 41)], fill=2)
    draw.line([(24, 41), (25, 49), (22, 60)], fill=5, width=2)
    draw.line([(33, 52), (34, 59), (36, 61)], fill=2, width=2)
    draw.polygon([(12, 18), (14, 10), (21, 4), (30, 2), (39, 3),
                  (45, 1), (43, 9), (37, 17), (39, 25), (34, 34),
                  (27, 38), (18, 35), (12, 29), (10, 23)], fill=3, outline=1)
    draw.polygon([(13, 17), (17, 10), (24, 5), (35, 4), (42, 3),
                  (37, 8), (30, 13), (22, 15), (18, 23), (13, 24)], fill=5)
    draw.polygon([(15, 14), (20, 8), (26, 6), (37, 5), (30, 8),
                  (23, 11), (20, 16)], fill=6)
    draw.line([(16, 17), (21, 11), (28, 9), (35, 6), (41, 4)], fill=7)
    draw.line([(27, 12), (29, 15), (29, 20)], fill=4)
    draw.line([(32, 8), (35, 10), (36, 12)], fill=4)
    draw.polygon([(17, 20), (22, 16), (30, 17), (34, 22), (32, 28),
                  (27, 34), (20, 33), (16, 29), (13, 28), (15, 25)], fill=9, outline=2)
    draw.polygon([(17, 21), (22, 18), (28, 19), (30, 23), (25, 29),
                  (20, 30), (16, 27)], fill=10)
    draw.line([(16, 25), (17, 22), (21, 21)], fill=11)
    draw.line((17, 24, 20, 24), fill=1, width=2)
    draw.point((17, 23), fill=15)
    draw.line([(17, 28), (21, 30), (24, 29)], fill=8)
    draw.polygon([(33, 18), (37, 24), (35, 30), (29, 35), (25, 34),
                  (29, 30), (31, 23)], fill=4)

    # Open ledger with separate vellum, cloth and exposed page block.
    draw.polygon([(6, 43), (18, 42), (29, 48), (27, 57), (16, 54),
                  (4, 53)], fill=8, outline=1)
    draw.polygon([(7, 44), (17, 43), (27, 48), (25, 54), (16, 51),
                  (6, 52)], fill=13)
    draw.line([(17, 44), (16, 49), (16, 52)], fill=10)
    draw.line([(8, 46), (11, 45), (15, 46)], fill=10)
    draw.line([(19, 47), (24, 49)], fill=10)
    draw.line([(8, 49), (14, 48)], fill=12)
    draw.line([(19, 50), (23, 51)], fill=12)
    draw.polygon([(7, 50), (4, 51), (4, 54), (7, 56), (11, 54),
                  (10, 52)], fill=10, outline=8)
    draw.line((6, 52, 8, 52), fill=11)
    draw.polygon([(30, 44), (33, 43), (35, 47), (31, 51), (26, 51),
                  (24, 49), (27, 47)], fill=9, outline=2)
    draw.line([(26, 49), (29, 48), (31, 46)], fill=11)
    return image


def brook_locksmith():
    image, draw = canvas()
    draw.polygon([(14, 27), (34, 24), (41, 30), (45, 42), (45, 54),
                  (42, 63), (10, 63), (8, 56), (10, 44), (7, 39),
                  (9, 32)], fill=3, outline=1)
    draw.polygon([(12, 33), (20, 30), (25, 34), (21, 43), (18, 56),
                  (19, 61), (11, 61), (12, 49), (10, 40)], fill=4)
    draw.polygon([(31, 29), (39, 31), (43, 42), (43, 54), (40, 61),
                  (33, 62), (36, 50), (33, 46), (36, 37)], fill=2)
    draw.line([(20, 39), (17, 49), (16, 58)], fill=5, width=2)
    draw.line([(28, 41), (27, 52), (23, 61)], fill=2, width=2)
    draw.polygon([(6, 16), (14, 7), (25, 4), (37, 6), (43, 12), (45, 19),
                  (41, 29), (35, 35), (22, 38), (13, 34), (7, 28), (4, 22)], fill=3, outline=1)
    draw.polygon([(6, 20), (10, 14), (17, 9), (25, 7), (33, 8), (39, 12),
                  (37, 14), (25, 13), (18, 16), (15, 21), (9, 24)], fill=5)
    draw.line([(10, 16), (16, 12), (24, 9), (32, 10)], fill=6, width=2)
    draw.line([(17, 17), (25, 15), (33, 16), (37, 19)], fill=4, width=2)
    draw.polygon([(11, 23), (16, 18), (26, 17), (32, 20), (34, 26),
                  (29, 32), (22, 35), (15, 33), (10, 29), (8, 28)], fill=9, outline=2)
    draw.polygon([(13, 22), (19, 19), (26, 19), (29, 23), (28, 28),
                  (23, 31), (15, 30), (11, 27)], fill=10)
    draw.line([(12, 25), (15, 22), (20, 21)], fill=11)
    draw.line([(14, 24), (18, 24)], fill=1, width=2)
    draw.point((15, 23), fill=15)
    draw.line([(13, 29), (17, 30), (21, 29)], fill=8)
    draw.polygon([(32, 17), (40, 17), (42, 21), (38, 29), (33, 35),
                  (22, 38), (18, 35), (29, 32), (33, 26)], fill=4)
    draw.line([(35, 19), (38, 19), (38, 22), (35, 27)], fill=5, width=2)
    draw.line([(24, 36), (31, 34), (35, 30)], fill=6)
    draw.polygon([(12, 50), (21, 52), (35, 49), (41, 46), (41, 50),
                  (34, 55), (20, 57), (11, 55)], fill=8)
    draw.line([(14, 51), (21, 53), (32, 51), (37, 49)], fill=12)
    draw.line([(28, 50), (27, 57), (23, 61)], fill=1, width=2)

    # A single raised brass key swings from the near hand.
    draw.polygon([(16, 39), (19, 40), (19, 44), (15, 49), (10, 49),
                  (8, 47), (10, 43)], fill=10, outline=8)
    draw.line([(10, 46), (12, 44), (15, 44)], fill=11)
    draw.line([(12, 48), (11, 53), (13, 58)], fill=1, width=4)
    draw.line([(12, 48), (11, 53), (13, 58)], fill=13, width=2)
    draw.ellipse((6, 55, 16, 63), fill=12, outline=1)
    draw.arc((7, 56, 15, 62), 160, 300, fill=14, width=2)
    draw.ellipse((9, 58, 13, 60), fill=1)
    draw.line((12, 53, 15, 53), fill=14, width=2)
    draw.point((12, 49), fill=15)
    return image


def rind_collector():
    image, draw = canvas()
    draw.polygon([(13, 30), (34, 27), (40, 33), (45, 43), (46, 56),
                  (42, 62), (12, 63), (9, 58), (10, 52), (6, 48),
                  (9, 40)], fill=3, outline=1)
    draw.polygon([(14, 34), (22, 33), (21, 41), (16, 49), (17, 58),
                  (12, 60), (12, 53), (10, 47), (12, 42)], fill=5)
    draw.polygon([(35, 31), (40, 35), (44, 44), (44, 54), (41, 61),
                  (34, 60), (36, 48), (30, 43)], fill=2)
    draw.line([(21, 41), (20, 48), (21, 55), (19, 60)], fill=4, width=2)
    draw.polygon([(19, 47), (32, 41), (38, 36), (39, 39), (35, 45),
                  (23, 52)], fill=8, outline=2)
    draw.line([(21, 48), (32, 44), (37, 39)], fill=14)
    draw.polygon([(22, 51), (34, 48), (39, 51), (39, 59), (35, 62),
                  (24, 62), (20, 58)], fill=9, outline=2)
    draw.polygon([(22, 52), (32, 49), (37, 51), (34, 55), (23, 56)], fill=14)
    draw.line((24, 53, 34, 51), fill=11)
    draw.rectangle((28, 54, 31, 57), fill=8)
    draw.point((29, 54), fill=13)

    # Pointed traveling cowl with pale curdstone dust caught in the seams.
    draw.polygon([(5, 20), (12, 13), (17, 9), (26, 5), (33, 1),
                  (40, 3), (37, 10), (43, 15), (46, 22), (44, 29),
                  (38, 34), (28, 39), (19, 37), (12, 32), (8, 26),
                  (3, 25)], fill=4, outline=1)
    draw.polygon([(6, 21), (15, 13), (24, 8), (32, 4), (36, 4),
                  (31, 10), (24, 14), (17, 17), (10, 24), (6, 24)], fill=6)
    draw.line([(13, 16), (19, 12), (26, 9), (33, 5)], fill=7, width=2)
    draw.polygon([(35, 12), (42, 17), (45, 23), (42, 29), (36, 34),
                  (27, 36), (32, 31), (37, 26), (36, 21), (32, 17)], fill=3)
    draw.line([(37, 15), (41, 19), (42, 23)], fill=5, width=2)
    draw.polygon([(13, 21), (20, 17), (27, 16), (33, 20), (35, 25),
                  (31, 31), (25, 35), (18, 34), (12, 31), (8, 27)], fill=9, outline=2)
    draw.polygon([(11, 26), (16, 21), (22, 19), (28, 20), (31, 24),
                  (30, 28), (25, 32), (17, 32), (13, 29)], fill=11)
    draw.line([(14, 24), (19, 22), (26, 21)], fill=12, width=2)
    draw.line([(13, 26), (17, 26)], fill=1, width=2)
    draw.point((14, 25), fill=15)
    draw.line([(14, 29), (18, 30), (22, 29)], fill=9)
    draw.line([(24, 25), (23, 27), (24, 30)], fill=10)

    draw.polygon([(9, 43), (13, 40), (17, 40), (19, 44), (17, 49),
                  (12, 52), (7, 50), (6, 47)], fill=8, outline=2)
    draw.polygon([(5, 40), (10, 37), (15, 39), (17, 43), (14, 48),
                  (8, 48), (4, 45)], fill=11, outline=8)
    draw.polygon([(6, 41), (10, 38), (14, 40), (12, 43), (7, 44)], fill=13)
    draw.line([(10, 39), (9, 42), (11, 44)], fill=10)
    draw.line([(10, 46), (13, 44), (15, 43)], fill=12)
    draw.point((7, 41), fill=15)
    draw.line([(7, 48), (10, 49), (13, 48)], fill=14, width=2)
    return image


def portraits():
    """Return the UI's fixed Bloom, Peddler, Moss, Brook and Rind order."""
    return ((bloom(), BLOOM), (peddler(), PEDDLER), (moss_archivist(), MOSS),
            (brook_locksmith(), BROOK), (rind_collector(), RIND))
