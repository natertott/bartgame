"""Fractured Rind: native Cream synthesis following review of studies2/3/5.

Rind's exact eight RGB555 banks and quiet floor survive. Large rock pictures
are packed separately after the room's routes exist; these16px cells only
fill small remaining spaces. No enlarged miniature or image reduction.
"""
from PIL import ImageDraw
from cream_style_rind import PALETTES, climb, water, prop, chest, pit
from cream_style_rind import floor as _floor
from cream_style_basilica import cave as _arch
from cream_depth_walls import filler as cliff
from cream_depth_edges import rim


def floor(stage=0, variant=0, path=False):
    image = _floor(stage, variant, path).copy()
    if not path and variant % 4 == 0:
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 7, 2), fill=4)
        draw.line([(4, 10), (7, 9), (9, 9)], fill=3)
        draw.line((5, 11, 8, 10), fill=5)
    return image


def cave(stage=0):
    """One tall, usable pointed opening, distinct from sealed blind arches.

    Reuse study2's native construction with study5's palette roles. Only the
    masonry is wounded; the portal silhouette and approach remain intact.
    """
    image = _arch(stage).copy()
    draw = ImageDraw.Draw(image)
    # An unequal broken crown avoids a perfectly stamped miniature cathedral.
    draw.polygon([(22, 6), (25, 8), (25, 12), (23, 11), (22, 9)], fill=2)
    draw.line([(21, 6), (23, 8), (23, 10)], fill=6)
    if stage:
        draw.line([(4, 31), (3, 33), (4, 36), (2, 38), (3, 42)], fill=2, width=2)
    if stage == 2:
        draw.line([(4, 32), (3, 34), (4, 36), (3, 38)], fill=13)
        draw.point((3, 34), fill=14)
    return image
