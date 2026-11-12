"""Five original native blue-waterfall studies for the Cream polish pass.

Final-size indexed pixels, never reduced illustration.  The outer wet-rock
contacts belong only to the outside of a complete16/32/48px composition;
interior cells are uninterrupted blue water.  The caller fits this drawing to
real rock and supplies a true lower basin rather than inventing floor hazards.
"""
from PIL import Image, ImageDraw

# Exact RGB555 channels. 1/2 are wet contact stone,3..9 blue liquid/light,
#10/11 attached moss,12..14 sparse attached rot,15 an ivory foam glint.
PALETTE = ['#000000', '#202830', '#304840', '#104878', '#1868a0',
           '#2888c0', '#40a8d8', '#70c8e8', '#b0e8f0', '#e0f8f8',
           '#486058', '#789080', '#403048', '#8058b8', '#c080e8', '#f8f8e8']
NAMES = ('Azure Curtain', 'Whitewater Ribbons', 'Glassfall',
         'Split Silk', 'Cerulean Cascade')
PHASES = 4
KINDS = ('top', 'mid', 'bottom')


def _new(size, fill=4):
    im = Image.new('P', size, fill)
    rgb = [int(c[i:i+2],16) for c in PALETTE for i in (1,3,5)]
    im.putpalette(rgb + [0]*(768-len(rgb)))
    return im, ImageDraw.Draw(im)


def _stroke(d, x, y, length, color, width=1):
    """One downward streak wraps cleanly through16px animation segments."""
    for offset in range(length):
        yy = (y+offset) % 16
        d.line((x, yy, x+width-1, yy), fill=color)


def _body(d, style, width, phase):
    """Continuous liquid body, with grouped stream-specific flow marks."""
    size = width*16
    # A brighter left sheet and deeper right return establish volume without
    # adding a dark divider at internal metatile boundaries.
    d.rectangle((2, 0, size-3, 15), fill=5 if style != 2 else 6)
    d.line((2, 0, 2, 15), fill=7)
    d.line((size-3, 0, size-3, 15), fill=3)
    for base in range(0,size,16):
        if style == 0:
            # Broad clean curtain: a pale left ribbon, slim recessed run,
            # and two moving cyan streaks rather than little horizontal rungs.
            d.rectangle((max(3,base+3), 0, min(size-4,base+5), 15), fill=6)
            if base+10 < size-3:
                d.line((base+10,0,base+10,15),fill=4)
            for x,y,length,c in ((base+4,1+phase*4,5,8),(base+8,9+phase*4,4,7)):
                if 3 <= x < size-3:_stroke(d,x,y,length,c)
        elif style == 1:
            # Two unequal broad bright ribbons remain joined by azure water.
            for left,right,c in ((base+3,base+5,7),(base+9,base+11,6)):
                if left < size-3:d.rectangle((max(3,left),0,min(size-4,right),15),fill=c)
            for x,y,length,c in ((base+4,phase*4,6,9),(base+10,7+phase*4,5,8)):
                if 3 <= x < size-3:_stroke(d,x,y,length,c)
        elif style == 2:
            # A clear glass sheet: very few long highlights and a broad blue
            # plane instead of an outline around each separate stream.
            if base+11 < size-3:d.rectangle((base+9,0,base+11,15),fill=5)
            for x,y,length,c in ((base+4,2+phase*4,7,8),(base+7,11+phase*4,3,7)):
                if 3 <= x < size-3:_stroke(d,x,y,length,c)
        elif style == 3:
            # A split wet sheet, still one connected water surface. Recessed
            # blue channels are narrow; no brown branching root-like marks.
            if base+8 < size-3:d.rectangle((base+7,0,base+8,15),fill=4)
            if base+4 < size-3:d.line((base+4,0,base+4,15),fill=6)
            for x,y,length,c in ((base+3,3+phase*4,5,8),(base+10,10+phase*4,4,7)):
                if 3 <= x < size-3:_stroke(d,x,y,length,c,width=2 if x+1<size-3 else 1)
        else:
            # Broader cascading pulses travel downward through the blue body;
            # groups are broken across x so they cannot read as ladder rungs.
            if base+11 < size-3:d.line((base+11,0,base+11,15),fill=4)
            for x,y,length,c in ((base+3,phase*4,4,8),(base+8,6+phase*4,5,7)):
                if 3 <= x < size-3:_stroke(d,x,y,length,c,width=2 if x+1<size-3 else 1)
            if base+5 < size-3:_stroke(d,base+5,phase*4+3,3,6)


def _banks(d, size, stage):
    # Only outermost wet contacts, never repeated down each16px water column.
    d.rectangle((0,0,1,15),fill=2)
    d.line((0,0,0,15),fill=10)
    d.line((1,0,1,15),fill=1)
    d.rectangle((size-2,0,size-1,15),fill=1)
    d.line((size-2,0,size-2,15),fill=2)
    # Keep corruption on the stone contact, not across blue liquid.
    if stage:
        d.line((0,7,0,10),fill=12 if stage == 1 else 13)
        if stage >= 2:d.point((0,8),fill=14)


def fall(style=0, stage=0, width=1, kind='mid', phase=0):
    """Return a complete native16/32/48×16 waterfall segment, opaqueP.

    Width counts16px gameplay cells. Split only after drawing so outer banks
    never appear between two adjacent water cells. `top` is the feed over a
    rock lip; `bottom` is a splash contact on the last solid face, not a
    newly created traversable pool. All styles use four animation phases.
    """
    style,stage,phase=int(style)%5,max(0,min(2,int(stage))),int(phase)%PHASES
    width=int(width)
    if width not in (1,2,3):raise ValueError('waterfall width must be1,2or3tiles')
    if kind not in KINDS:raise ValueError('unknown waterfall segment '+str(kind))
    size=width*16
    im,d=_new((size,16),4)
    _body(d,style,width,phase)
    if kind == 'top':
        # Pale rounded feed turns over one shared dark wet lip. The sheet
        # remains continuous below it; no circle/root outline defines the fall.
        d.rectangle((2,0,size-3,2),fill=6)
        d.line((2,3,size-3,3),fill=4)
        for x in range(3,size-3,8):
            d.line((x,1,min(size-4,x+3),1),fill=8)
            if (x//8+style)%2==0:d.line((x+1,2,min(size-4,x+4),2),fill=7)
        if style in (1,4):
            for x in range(4+phase,size-4,12):
                d.line((x,3,min(size-4,x+2),3),fill=9)
    elif kind == 'bottom':
        # A continuous azure skirt and pale uneven splashcap make the water
        # reach the real wall foot. Foamy groups don't box individual cells.
        d.rectangle((2,11,size-3,15),fill=5)
        for x in range(3,size-3,8):
            shift=(phase*2+(x//8)%2)
            d.line((x,12+((x//8+phase)&1),min(size-4,x+4),12+((x//8+phase)&1)),fill=7)
            d.line((x+1,14,min(size-4,x+5),14),fill=6)
            if (x//8+style+phase)%2==0:
                d.line((x+1,11,min(size-4,x+3),11),fill=8)
                d.point((min(size-4,x+2),10),fill=9)
        if style in (1,4):
            for x in range(4+phase,size-4,12):d.line((x,13,min(size-4,x+2),13),fill=9)
    _banks(d,size,stage)
    return im


def pool(style=0, stage=0, phase=0):
    """Open blue pool material, not a bordered isolated square or new hazard."""
    style,stage,phase=int(style)%5,max(0,min(2,int(stage))),int(phase)%2
    im,d=_new((16,16),4)
    d.rectangle((0,0,15,5),fill=5)
    d.line((0,6,15,6),fill=3)
    # Long broken horizontal reflections clearly differ from falling water.
    d.line((1+phase,3,6+phase,3),fill=7 if style != 2 else 8)
    d.line((2+phase,4,7+phase,4),fill=6)
    d.line((9-phase,10,14-phase,10),fill=6)
    d.line((10-phase,11,15-phase,11),fill=5)
    if style in (1,4):d.line((4,14-phase,7,14-phase),fill=7)
    if stage >= 2:
        d.line((12,1,15,1),fill=12)
        d.point((14,1),fill=13)
    return im
