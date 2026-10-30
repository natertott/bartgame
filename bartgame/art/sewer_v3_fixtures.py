"""Native Drain fixtures for the feedback-led third concept pass.

The room remains the original 30x20 cell contract.  Functions are installed
into sewer_concepts_terrain only for its opt-in study builds.  This module
authors final indexed pixels: no imported picture, scaling or new palette.
"""
from PIL import Image, ImageDraw

def _new(w=480, h=320, fill=0):
    im = Image.new('P', (w, h), fill)
    return im, ImageDraw.Draw(im)


def _arch_mask(box, inset=0):
    x0, y0, x1, y1 = box
    im, d = _new()
    x0 += inset; x1 -= inset; y0 += inset
    radius = max(1, (x1 - x0) // 2)
    d.pieslice((x0, y0, x1, y0 + radius*2), 180, 360, fill=1)
    d.rectangle((x0, y0+radius, x1, y1), fill=1)
    return im


def _grand_outfall(g, style=1, phase=0):
    """Round gold barred sewer mouth, with five distinct damaged frames."""
    d = ImageDraw.Draw(g)
    # All outlines stay inside the uniquely-addressed rear gate footprint.
    outer = _arch_mask((208, 16, 271, 85))
    inner = _arch_mask((208, 16, 271, 85), 7 if style in (1, 5) else 8)
    for y in range(16, 86):
        for x in range(208, 272):
            if not outer.getpixel((x, y)): continue
            if inner.getpixel((x, y)):
                d.point((x, y), fill=1)
            else:
                ink = 13
                if x < 217 or y < 24: ink = 14
                if x > 262 or y > 80: ink = 12
                d.point((x, y), fill=ink)
    # Separate vertical rods read as a grate.  There is no false open door.
    for x in range(222, 260, 7 if style in (1, 3) else 9):
        for y in range(27, 82):
            if inner.getpixel((x, y)):
                d.point((x, y), fill=13)
                d.point((x+1, y), fill=12)
    if style == 1:
        d.line((217, 43, 261, 43), fill=12, width=2)
        d.line((217, 42, 261, 42), fill=14)
        d.line((219, 26, 228, 21), fill=15)
        for x, y in ((211, 49), (266, 49), (211, 72), (266, 72)):
            d.rectangle((x-1, y-1, x+1, y+1), fill=12)
            d.point((x-1, y-1), fill=14)
    elif style == 2:
        # Bolted removable grille, rounded cap and thick hardware shoes.
        for x, y in ((216, 33), (263, 33), (211, 58), (267, 58)):
            d.ellipse((x-2, y-2, x+2, y+2), fill=12)
            d.point((x-1, y-1), fill=15)
        d.rectangle((209, 75, 217, 84), fill=12)
        d.rectangle((263, 75, 270, 84), fill=12)
        d.line((219, 27, 226, 22), fill=15)
        d.line((217, 59, 261, 59), fill=13, width=2)
    elif style == 3:
        # Exposed stone shoulders around an older brass insert.
        d.line((208, 52, 212, 52), fill=2, width=2)
        d.line((266, 62, 271, 62), fill=2, width=2)
        d.line((214, 33, 219, 29), fill=15)
        d.line((217, 48, 261, 48), fill=13)
        d.polygon([(264, 35), (268, 38), (265, 43), (268, 48), (263, 50)], fill=2)
    elif style == 4:
        # Closest to the selected decayed fourth study: chipped right jamb,
        # tarnish attached to masonry and a short bent bar, never vine water.
        d.polygon([(265, 32), (269, 35), (265, 41), (268, 47), (264, 53)], fill=2)
        d.polygon([(209, 62), (215, 63), (213, 71), (210, 69), (208, 77)], fill=9)
        d.line((217, 55, 262, 55), fill=13)
        d.line([(255, 58), (252, 65), (254, 79)], fill=12)
        d.line((217, 28, 223, 23), fill=15)
    else:
        # A grand frame worn down to a few intact glorious metal facets.
        d.rectangle((231, 17, 248, 21), fill=13)
        d.line((232, 17, 246, 17), fill=15)
        d.line((211, 43, 211, 61), fill=15)
        d.line((218, 48, 260, 48), fill=14)
        d.polygon([(266, 62), (270, 63), (268, 70), (265, 74)], fill=9)


def _sheet(d, box, phase, period, style=1):
    """Straight connected pouring plane, disconnected downward glints.

    The previous pair of winding strokes read as roots.  The falling mass is
    now a broad rectangular liquid plane, with a pale impact line that fixes
    its destination.  Highlight packets translate downward, never grow limbs.
    """
    x0, y0, x1, y1 = box
    d.rectangle((x0, y0, x1, y1), fill=9)
    d.rectangle((x0+2, y0, x1-3, y1), fill=10)
    # Dark intervals in the sheet imply thin transparent water, rather than
    # a solid green column. They remain straight and do not join into roots.
    for x in range(x0+5, x1-1, 6):
        d.line((x, y0+2, x, y1-3), fill=9)
    height = y1-y0+1
    shift = (int(phase)*height // max(1, int(period))) % height
    for n, x in enumerate(range(x0+2, x1-1, 5)):
        yy = (shift+n*9+style*3) % height
        for step in range(6 if style in (1, 3, 5) else 4):
            y = y0 + (yy+step) % height
            d.point((x, y), fill=11)
            if step in (1,2):d.point((x+1,y),fill=11)
    # One-pixel edge breaks travel with gravity. Broad terminal foam and a
    # little spreading apron distinguish poured liquid from hanging cloth.
    for yy in range(y0, y1-3):
        if (yy-shift)%11<3:d.point((x0-1,yy),fill=9)
        if (yy-shift+6)%13<2:d.point((x1+1,yy),fill=10)
    d.polygon([(x0,y1-4),(x1,y1-4),(x1+3,y1),
               (x1+1,y1+2),(x0-2,y1+2),(x0-4,y1)],fill=10)
    for x in range(x0-2,x1+2,5):
        yy=y1-1+((x+phase)%3)
        d.ellipse((x,yy,x+4,yy+2),fill=11)
    d.line((x0+1,y1+3,x1-1,y1+3),fill=9)


def _basin(g, style=1, phase=0, period=8):
    d = ImageDraw.Draw(g)
    # Keep the liked round basin and recessed gate geometry, but replace the
    # woody waterfall with a single gravity-aligned curtain.
    d.ellipse((192, 63, 287, 104), fill=12)
    d.ellipse((193, 63, 286, 100), fill=13)
    d.ellipse((198, 66, 281, 96), fill=8)
    d.arc((194, 64, 285, 100), 180, 280, fill=14, width=2)
    d.arc((194, 65, 285, 101), 10, 166, fill=12, width=3)
    d.line((205, 68, 219, 66), fill=15)
    # Calm liquid around a fall reads as a pool; sparse broken expanding arcs
    # carry motion instead of a repeated textured patch over every pixel.
    rr = int(phase)*5//max(1, int(period))
    for rad in (11+rr, 24+rr, 35+rr):
        box = (240-rad, 83-rad//4, 240+rad, 84+rad//4)
        d.arc(box, 7, 72, fill=10)
        d.arc(box, 104, 169, fill=9 if rad > 30 else 10)
    width = {1:22, 2:28, 3:18, 4:26, 5:20}[style]
    left = 240-width//2
    if style == 2:
        # A split spillway: two broad straight sheets separated by clear air.
        _sheet(d, (226,52,236,84), phase, period, style)
        _sheet(d, (242,49,253,84), phase+2, period, style)
    elif style == 4:
        # A wide broken curtain, with small transparent gaps at the upper lip.
        _sheet(d, (left,54,left+width-1,84), phase, period, style)
        d.rectangle((left+5,54,left+6,58),fill=8)
        d.rectangle((left+18,54,left+19,60),fill=8)
    elif style == 5:
        # A narrow top spreads into a wider bright impact apron.
        d.polygon([(left,69),(left+width-1,69),(left+width+2,83),
                   (left-3,83)],fill=9)
        _sheet(d, (left,50,left+width-1,84), phase, period, style)
    else:
        _sheet(d, (left,49 if style == 1 else 53,left+width-1,84), phase, period, style)
    d.line((226, 89, 235, 89), fill=11)
    d.line((242, 89, 253, 89), fill=10)
    d.line((231, 92, 242, 92), fill=10)
    # Separate spray droplets have a short falling cycle close to the impact.
    for x, offset in ((left-3, 0), (left+width+2, 3)):
        yy = 80 + (int(phase)+offset) % 6
        d.line((x, yy, x, yy+1), fill=11)


def _pipe(d, box, style=1, horizontal=False):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=12)
    if horizontal:
        d.rectangle((x0+1, y0+1, x1-1, y1-2), fill=13)
        d.line((x0+2, y0+1, x1-2, y0+1), fill=14)
        for x in range(x0+15, x1-3, 29 if style in (1, 5) else 23):
            d.rectangle((x-1, y0-2, x+3, y1+1), fill=12)
            d.line((x, y0-2, x+2, y0-2), fill=14)
        d.line((x0+4, y0+1, min(x0+13, x1-2), y0+1), fill=15)
    else:
        d.rectangle((x0+1, y0+1, x1-2, y1-1), fill=13)
        d.line((x0+1, y0+2, x0+1, y1-2), fill=14)
        for y in range(y0+9, y1-2, 22):
            d.rectangle((x0-2, y-1, x1+1, y+3), fill=12)
            d.line((x0-2, y-1, x0+3, y-1), fill=14)
        d.line((x0+1, y0+3, x0+1, min(y0+10, y1-2)), fill=15)
    # Visible damage describes a pipe; sparse verdigris never hides its form.
    if style in (3, 4):
        if horizontal: d.line((x1-14, y1-1, x1-9, y1-1), fill=9)
        else: d.line((x1-1, y0+5, x1-1, min(y0+11, y1-1)), fill=9)


def _small_outfall(g, style=1, phase=0, period=8):
    """A legible elbow pipe pouring into the existing stream, not a gold icon."""
    d = ImageDraw.Draw(g)
    # Only unique bank cells (27,9)/(28,9) can hold this fitting.  The former
    # floor riser was erased by reused walkable tile IDs in the REAL map.
    # A horizontal wall stub now leads to a front-facing outlet on the bank.
    d.rectangle((457,146,479,151),fill=12)
    d.rectangle((458,147,478,149),fill=13)
    d.line((459,146,477,146),fill=14)
    d.rectangle((469,145,472,152),fill=12)
    d.line((469,145,471,145),fill=14)
    d.ellipse((448,145,463,159),fill=12)
    d.ellipse((449,145,462,157),fill=14)
    d.ellipse((452,148,460,155),fill=1)
    d.arc((449,145,462,157),185,280,fill=15)
    d.line((451,156,461,156),fill=12)
    # The full moving fall is inside UNIQUE animated tile (28,10), x448..463.
    # Painting any flowing pixel at x<448 would spread it to repeated stream
    # tiles or be erased; every splash/impact pixel stays within this lane.
    _sheet(d,(452,155,458,171),phase,period,style)
    r=int(phase)*2//max(1,int(period))
    d.arc((449,169,462,174+r),5,175,fill=10)
    d.line((450,173,454,173),fill=11)
    d.line((458,174,461,174),fill=10)


def _up_arrow(d, cx, top, style=1):
    # Common functional glyph across every variation, eleven pixels wide.
    # A dark sign field separates this cue from the metal arch and rails.
    d.rectangle((cx-7, top-2, cx+7, top+12), fill=1)
    d.line((cx-6, top-1, cx+6, top-1), fill=12)
    d.polygon([(cx, top), (cx+5, top+5), (cx+2, top+5),
               (cx+2, top+10), (cx-2, top+10), (cx-2, top+5),
               (cx-5, top+5)], fill=15)
    d.point((cx, top+1), fill=7)


def _ladder(g, o, style=1):
    d = ImageDraw.Draw(g)
    # The forest trigger is the original x144..159 lane. Its dark recess and
    # two bright rails remain visible below the new dedicated up-arrow sign.
    outer = _arch_mask((132, 16, 171, 63))
    inner = _arch_mask((132, 16, 171, 63), 5 if style in (1, 5) else 6)
    for y in range(16, 64):
        for x in range(132, 172):
            if outer.getpixel((x, y)):
                d.point((x, y), fill=1 if inner.getpixel((x, y)) else
                        (14 if x < 140 or y < 22 else 12 if x > 165 else 13))
    # Alternative construction details stay peripheral to the navigation cue.
    if style == 2:
        for x in (135, 168):
            for y in (36, 56):
                d.rectangle((x-1, y-1, x+1, y+1), fill=12)
                d.point((x-1, y-1), fill=15)
    elif style == 3:
        d.line((132, 48, 137, 48), fill=2)
        d.line((166, 39, 171, 39), fill=2)
        d.polygon([(167, 50), (171, 48), (169, 55), (171, 58), (166, 60)], fill=2)
    elif style == 4:
        d.line([(168, 35), (166, 39), (169, 44)], fill=2)
        d.line((135, 49, 135, 56), fill=9)
    elif style == 5:
        d.rectangle((134, 47, 138, 61), fill=13)
        d.rectangle((166, 47, 170, 61), fill=12)
    for x in (145, 158):
        d.rectangle((x, 33, x+1, 63), fill=12)
        d.line((x, 33, x, 62), fill=14)
    for y in (35, 41, 47, 53, 59):
        d.line((147, y, 157, y), fill=14, width=2)
        d.line((148, y+1, 157, y+1), fill=13)
        d.point((147, y), fill=15)
    # Actual northern-camera review caught the original cap arrow under the
    # fixed 24px HUD. Put the functional sign BESIDE the climb lane at y34,
    # wholly below the HUD, in an existing unique right-jamb overlay cell.
    _up_arrow(d, 167, 34, style)
    d.line((144, 63, 159, 63), fill=15)
    for y in range(16, 48):
        for x in range(128, 176):
            ink = g.getpixel((x, y))
            if ink and (x < 144 or x > 159 or y < 33): o.putpixel((x, y), ink)


def _jar(d, x, y, style=1):
    d.polygon([(x-4,y-2),(x-2,y-5),(x+2,y-5),(x+4,y-2),
               (x+4,y+4),(x+2,y+6),(x-3,y+5)], fill=2)
    d.polygon([(x-2,y-2),(x+1,y-3),(x+2,y+4),(x-2,y+3)], fill=10)
    d.line((x-2,y-4,x+2,y-4), fill=13)
    d.line((x-1,y-2,x-1,y+1), fill=11)


def _market(g, o, style=1, phase=0):
    d=ImageDraw.Draw(g); od=ImageDraw.Draw(o)
    # Dark stall interior, timber uprights, visible tabletop. Frog stays at
    # its existing anchor, with its hands above the occluding counter front.
    d.rectangle((19, 66, 125, 106), fill=12)
    d.rectangle((24, 70, 120, 92), fill=1)
    for x in (20, 121):
        d.rectangle((x, 64, x+3, 108), fill=12)
        d.line((x, 65, x, 106), fill=13)
    if style == 1:
        # A striped, low pitched canvas canopy over an old market booth.
        d.polygon([(16, 60),(30, 56),(113, 56),(127,60),(124,78),
                   (113,80),(103,77),(91,80),(79,77),(67,80),(55,77),
                   (43,80),(31,77),(19,79)], fill=9)
        d.polygon([(18,60),(31,57),(112,57),(123,60),(119,63),(23,63)], fill=10)
        for x in (32, 56, 80, 104):
            d.polygon([(x,58),(x+8,58),(x+7,77),(x+1,78)], fill=4)
            d.line((x+1,59,x+6,59), fill=5)
        d.line((18,60,124,60), fill=12)
    elif style == 2:
        # Patched canvas with a sloped left pole and broad scalloped valance.
        d.polygon([(16,60),(43,56),(75,58),(106,56),(127,60),
                   (125,74),(117,80),(104,80),(96,76),(85,81),(69,80),
                   (60,76),(48,80),(31,80),(18,74)], fill=9)
        d.polygon([(19,60),(43,57),(75,60),(70,63),(37,62)], fill=10)
        d.rectangle((91,61,109,70), fill=4)
        d.line((94,63,106,63), fill=5)
        for x in (92,97,102,107): d.point((x,70), fill=2)
        d.line((18,61,20,74), fill=10)
    elif style == 3:
        # Little salvaged-board roof, still the same shop frontage/footprint.
        d.polygon([(16,61),(28,56),(115,56),(127,62),(124,77),(18,77)], fill=12)
        for x in range(21, 121, 11):
            d.polygon([(x,59),(x+8,57),(x+9,74),(x,75)], fill=13)
            d.line((x,60,x+6,58), fill=14)
        d.line((18,76,125,76), fill=12, width=3)
        d.polygon([(92,64),(105,62),(105,72),(96,74)], fill=9)
    elif style == 4:
        # Ragged but functional salvaged striped canvas; no generic slimeblob.
        d.polygon([(16,60),(40,57),(75,58),(101,56),(127,60),(124,76),
                   (113,75),(108,80),(99,76),(88,80),(78,76),(67,81),
                   (58,77),(42,80),(34,76),(18,78)], fill=9)
        for x in (31, 59, 88, 112):
            d.polygon([(x,59),(x+5,58),(x+7,76),(x+2,78)], fill=4)
        d.line((19,60,37,58), fill=10)
        d.line((47,61,44,73), fill=8)
        d.line((112,62,115,73), fill=8)
    else:
        # Once-fine roll canopy, a torn corner and a crooked lower brass rod.
        d.polygon([(16,60),(30,56),(114,56),(127,60),(124,75),(115,80),
                   (33,79),(25,77),(18,78)], fill=9)
        d.polygon([(20,59),(31,57),(113,57),(121,60),(115,63),(26,63)], fill=10)
        for x in (35, 100): d.polygon([(x,62),(x+6,62),(x+4,77),(x,77)], fill=4)
        d.line((20,76,112,78), fill=13)
        d.line((21,76,42,76), fill=14)
        d.polygon([(116,75),(124,75),(122,80),(118,77)], fill=1)
    # A clear horizontal top, two separate little jars, one tied goods sack.
    d.rectangle((26,90,111,108), fill=12)
    d.polygon([(26,89),(112,89),(110,94),(27,94)], fill=13)
    d.line((28,89,61,89), fill=14)
    _jar(d,37,84,style); _jar(d,102,83,style)
    d.polygon([(50,88),(52,83),(56,81),(60,83),(63,88),(60,91),(53,91)], fill=12)
    d.polygon([(53,85),(56,83),(59,85),(60,88),(53,88)], fill=13)
    d.line((54,82,59,82), fill=2)
    d.ellipse((83,85,94,89), fill=12)
    d.line((85,85,91,85), fill=14)
    # All five share an unmistakable counter silhouette but differ in joinery.
    od.rectangle((32,94,111,106), fill=12)
    od.line((32,94,111,94), fill=13)
    od.line((33,106,110,106), fill=2)
    if style == 1:
        for x in (46, 73, 98): od.line((x,96,x,104), fill=13)
        od.line((34,101,109,101), fill=13)
    elif style == 2:
        od.line((36,96,60,104), fill=13, width=2)
        od.line((61,96,36,104), fill=13, width=2)
        od.line((81,96,105,104), fill=13, width=2)
    elif style == 3:
        for y in (98, 102): od.line((33,y,110,y), fill=13)
        od.rectangle((66,96,75,103), fill=2)
    elif style == 4:
        od.polygon([(35,97),(44,96),(51,104),(40,105)], fill=13)
        od.line([(89,96),(85,99),(89,104)], fill=2)
        od.line((66,99,79,99), fill=13)
    else:
        od.rectangle((36,97,106,103), outline=13)
        od.line((71,98,71,102), fill=2)
        od.line((91,103,102,103), fill=12)


def _sanctum(g, style=1, phase=0):
    d=ImageDraw.Draw(g)
    # Five once-fine, now worn corners.  The rug remains a floor plane;
    # holes expose actual underlying gray brick instead of black pit marks.
    base = 9 if style in (1, 2, 4) else 8
    if style == 2:
        rug=[(310,72),(375,72),(380,77),(379,104),(375,108),(309,108),(305,103),(305,77)]
    elif style == 4:
        rug=[(306,73),(379,74),(378,106),(367,107),(361,105),(347,108),(336,106),(307,107)]
    elif style == 5:
        rug=[(306,73),(378,72),(380,104),(372,108),(307,106)]
    else:
        rug=[(305,73),(380,73),(379,107),(307,107)]
    d.polygon(rug,fill=base)
    # A single broken brass border beats an ornate beveled UI rectangle.
    d.line((310,77,376,77), fill=13)
    d.line((309,78,310,103), fill=10)
    d.line((312,103,339,103), fill=13)
    d.line((349,103,374,103), fill=13)
    if style in (1,5):
        d.polygon([(343,82),(350,90),(343,99),(336,90)], outline=10)
        if style == 5: d.line((318,80,330,80), fill=13)
    elif style == 2:
        d.arc((328,79,358,101), 18, 164, fill=10)
        d.arc((328,79,358,101), 198, 344, fill=10)
    elif style == 3:
        d.line((316,82,369,82), fill=9)
        d.line((316,98,369,98), fill=9)
        d.polygon([(343,84),(348,90),(343,96),(338,90)], fill=10)
    else:
        d.polygon([(341,81),(351,89),(344,100),(335,91)], outline=10)
        d.polygon([(309,75),(320,76),(318,81),(312,82)], fill=3)
    # Frays point along the cloth plane; damage never covers the staff flame.
    for x in ((314, 328, 363, 374) if style != 4 else (310, 319, 351, 370)):
        d.line((x,108,x-1,110), fill=base)
    d.line((374,93,379,95), fill=3)
    # Uneven old timber shelf, short end returns and a chip in its lower face.
    d.polygon([(288,62),(382,62),(380,69),(362,69),(359,67),
               (354,70),(290,69)], fill=12)
    d.line((289,62,377,62), fill=13)
    d.line((292,63,316,63), fill=14)
    if style in (2,4): d.line((318,65,328,66), fill=2)
    candles = {1:(299,310,363,374), 2:(297,311,365,376),
               3:(300,312,366,376), 4:(299,311,364,374),
               5:(299,309,365,375)}[style]
    for n,x in enumerate(candles):
        top=54+(n%2 if style in (2,4) else 0)
        d.line((x,top,x,61), fill=7, width=2)
        d.line((x+1,top+1,x+1,61), fill=5)
        lean=(phase+n)%2
        d.polygon([(x-2,top),(x-1,top-3),(x+lean,top-5),(x+2,top-1),(x+1,top+1)], fill=14)
        d.point((x,top-2), fill=15)


def _crate(d, x, y, style=1, w=22, h=28):
    # Closed timber lid is explicitly built from warm plank masses.  Never
    # paint the former gray-green cap or slime over its identity-carrying top.
    face_right=x+w-4
    d.polygon([(x,y+5),(x+w-5,y),(x+w,y+4),(x+w,y+h),
               (x+3,y+h),(x,y+h-3)], fill=12)
    d.polygon([(x+1,y+5),(x+w-5,y+1),(x+w-1,y+4),(x+4,y+8)], fill=13)
    d.line((x+2,y+5,x+w-6,y+2), fill=14)
    d.line((x+6,y+5,x+w-3,y+3), fill=12)
    d.polygon([(x+3,y+9),(face_right,y+6),(face_right,y+h-1),(x+3,y+h-1)], fill=13)
    for xx in (x+w//3,x+2*w//3):
        d.line((xx,y+9,xx,y+h-2), fill=12)
    d.line((face_right+1,y+6,face_right+1,y+h-1), fill=2)
    if style in (1,3,5):
        for yy in (y+12,y+h-5):
            d.line((x+3,yy,face_right-1,yy-2), fill=12, width=2)
        if style == 3: d.line((x+5,y+13,face_right-2,y+h-6), fill=14)
        if style == 5: d.line((x+5,y+h-7,face_right-2,y+12), fill=12)
    else:
        d.line((x+4,y+12,face_right-2,y+h-5), fill=12, width=2)
        d.line((face_right-2,y+10,x+4,y+h-4), fill=12, width=2)
        if style == 4: d.line([(x+11,y+9),(x+9,y+14),(x+11,y+20)], fill=2)
    for xx,yy in ((x+4,y+11),(face_right-1,y+h-5)):
        d.point((xx,yy),fill=2)


def _barrel(d, x, y, style=1):
    # Wooden bunged lid, vertical staves and thin dull hoops are recognisable
    # barrel construction; its top is no longer a green/gray blob.
    d.ellipse((x,y,x+18,y+24),fill=12)
    d.rectangle((x+2,y+5,x+16,y+19),fill=12)
    d.polygon([(x+3,y+6),(x+9,y+5),(x+11,y+22),(x+5,y+22)],fill=13)
    d.ellipse((x+1,y,x+17,y+8),fill=12)
    d.ellipse((x+2,y+1,x+16,y+7),fill=13)
    d.arc((x+2,y+1,x+16,y+7),180,282,fill=14)
    d.line((x+5,y+2,x+5,y+6),fill=12)
    d.line((x+11,y+2,x+11,y+6),fill=12)
    d.rectangle((x+8,y+3,x+9,y+4),fill=12)
    for xx in (x+5,x+10,x+14): d.line((xx,y+9,xx,y+21),fill=12)
    for yy in (y+10,y+18):
        d.arc((x+1,yy-3,x+17,yy+4),0,180,fill=4,width=2)
        d.line((x+2,yy-1,x+6,yy),fill=5)
    if style == 4: d.line([(x+12,y+10),(x+11,y+14),(x+13,y+18)],fill=2)


def install(namespace):
    """Install fixture hooks after the compatibility painter definitions."""
    for name in ('_grand_outfall','_basin','_pipe','_small_outfall','_ladder',
                 '_market','_sanctum','_crate','_barrel'):
        namespace[name]=globals()[name]
