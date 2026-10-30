"""Five reference-led, native-resolution Drain material studies.

Only the fixed map identifiers and occurrence positions come from the room
contract. Every pixel here is drawn at its final GBA size, with one sixteen
ink bank. Equal material roles let the review builds mix individual parts.
This module is opt-in; it does not replace the released Drain painter.

Revision 3 follows the user's component-by-component feedback. Pavement is
new gray masonry, architecture retains the damaged fourth-study vocabulary,
and water uses planar sheets and travelling wavelets rather than root-like
silhouettes. Fixture revisions are installed from sewer_v3_fixtures below.
"""
from functools import lru_cache
import json
from pathlib import Path
from PIL import Image, ImageDraw

STYLE_NAMES = {1:'Ashlar & Amber', 2:'Crooked Brickwork', 3:'Floodworn Flags',
               4:'Crumbling Vault', 5:'Silted Cloister'}
CATEGORIES = ('floor','masonry','water','metal','bridge','market','sanctum','props')
CONTRACTS = json.loads(Path(__file__).with_name('reboot_contracts.json').read_text())
ROOM = CONTRACTS['rooms'][0]
TILES = {t['name']:t for t in CONTRACTS['tiles']}
OCCURRENCES = {}
for _layer in ('ground','overlay'):
    for _y,_row in enumerate(ROOM[_layer]):
        for _x,_name in enumerate(_row):
            if _name: OCCURRENCES.setdefault(_name, []).append((_layer,_x,_y))
DEBRIS_SITES = {(2,7):0,(6,7):1,(24,7):2,(5,14):3,(20,14):4,(6,15):5,(19,15):6}

PALETTES = {
 1:['#000000','#182028','#485058','#606870','#788080','#909890','#b0b8a8','#d0d8c8',
    '#102830','#304848','#789088','#c0d0c8','#685038','#a07838','#e0b850','#f8e8b0'],
 2:['#000000','#202028','#505858','#687070','#808880','#989890','#b8b8a8','#d8d8c0',
    '#182830','#384848','#809888','#c8d0b8','#705030','#a88040','#e8b858','#f8e8b0'],
 3:['#000000','#182028','#404850','#586068','#707880','#889898','#a8b8b8','#d0d8d0',
    '#102830','#284850','#7898a0','#c0d8d8','#685038','#a08040','#d8b858','#f8e8b8'],
 4:['#000000','#182020','#485048','#606860','#788070','#909880','#b0b8a0','#d0d8b8',
    '#182828','#384838','#889880','#c8d0b0','#685030','#a07838','#d8b050','#f0e0a8'],
 5:['#000000','#182028','#505858','#606868','#788080','#909890','#b0b8b0','#d0d8c8',
    '#102830','#304840','#789890','#c8d8c0','#705038','#a88040','#e0c060','#f8e8b8']}


def palette(style=1):
    return list(PALETTES[int(style)])


def rail_sprite(style=1):
    """Brass pipe handrail, with worn straps; unchanged seamless OBJ anchors."""
    im,d=_new(16,8)
    # FX palette indices, NOT the terrain bank. Bright upper lip is polished
    # locally by hands; underside remains tarnished and the silhouette joins.
    d.line((0,2,15,2),fill=10 if style!=4 else 9)
    d.line((0,3,15,3),fill=7)
    if style in (1,3):
        d.rectangle((6,1,8,4),fill=8)
        d.line((6,1,8,1),fill=10)
    elif style==2:
        d.polygon([(5,2),(6,0),(9,0),(10,2),(9,4),(6,4)],fill=8)
        d.line((6,1,8,1),fill=10)
    elif style==4:
        d.polygon([(5,1),(8,1),(9,4),(7,5),(5,4)],fill=8)
        d.line((6,1,7,1),fill=10)
        d.line((11,2,13,2),fill=7)
    else:
        d.rectangle((6,1,9,4),fill=8)
        d.line((6,1,9,1),fill=10)
        d.point((10,3),fill=8)
    return im


def recipe_key(recipe=None):
    if recipe is None: recipe = {'style':1}
    if isinstance(recipe, int): recipe = {'style':recipe}
    base = int(recipe.get('style', recipe.get('base', 1)))
    result = tuple(int(recipe.get(k, base)) for k in CATEGORIES)
    assert all(v in STYLE_NAMES for v in result), result
    return result


def _new(w=16,h=16,fill=0):
    im=Image.new('P',(w,h),fill)
    return im,ImageDraw.Draw(im)


def _paste(dst,src,xy):
    dst.paste(src,xy,src.point(lambda v:255 if v else 0,'1'))


def _glint(d,x,y,phase=0):
    # Sparse attached specular pixels; the engine's ambient glitter is intact.
    if phase%4==0: d.point((x,y),fill=15)
    elif phase%4==1:
        d.line((x-1,y,x+1,y),fill=15); d.line((x,y-1,x,y+1),fill=15)
    elif phase%4==2:
        d.point((x,y),fill=15);d.point((x-1,y),fill=14)


def _slime(d,x,y,w=20,h=8,style=1):
    # One connected accumulation, with a wet edge rather than scattered dots.
    w=max(4,w);h=max(3,h)
    d.polygon([(x,y+h//3),(x+w//4,y),(x+w*3//4,y+1),
               (x+w,y+h//2),(x+w-2,y+h-1),(x+w//2,y+h),
               (x+w//3,y+h-2),(x+1,y+h-1)],fill=9)
    if style==2:
        d.ellipse((x+1,y+1,x+w//2,y+h-1),fill=10)
    elif style==4:
        d.polygon([(x+1,y+h//3),(x+w//3,y+1),(x+w//2,y+3),
                   (x+w//3,y+h-2),(x+2,y+h-1)],fill=10)
    else:
        d.line([(x+2,y+h//3),(x+w//4,y+1),(x+w//2,y+2)],fill=10,width=2 if h>5 else 1)
    if w>14 and h>5:
        d.line((x+w//4,y+1,x+w//4+2,y+1),fill=10)


def floor_tile(style=1,variant=0):
    """Five new gray masonry bonds, kept quieter than all functional objects.

    The joints are shadow-coloured, intermittently filled with the face ink;
    no pale bevel runs around an entire stone. Each native cell meets its
    neighbours without a transparent edge or a dark sprite-like contour.
    """
    im,d=_new(fill=3)
    v=int(variant)
    if style==1:
        # Broad running-bond bricks. Courses meet through flat eroded seams.
        for y,cut in ((7,4),(15,12)):
            d.line((0,y,15,y),fill=2)
            d.line((cut,(y-7)%16,cut,y-1),fill=2)
        d.line((1 if v%2 else 10,7,4 if v%2 else 13,7),fill=3)
        d.line((7,15,11,15),fill=3)
        if v%5==1:d.line((6,1,12,1),fill=4)
        if v%7==4:d.line((0,11,3,11),fill=4)
    elif style==2:
        # Unequal-height reclaimed bricks. Every joint belongs to a face;
        # disconnected scratch marks would read as concrete, not masonry.
        d.line((0,9,15,9),fill=2);d.line((0,15,15,15),fill=2)
        d.line((10,0,10,8),fill=2);d.line((3,10,3,14),fill=2)
        d.line((13,9,15,9),fill=3);d.line((7,15,10,15),fill=3)
        if v%4==1:d.line((1,1,6,1),fill=4)
        if v%7==2:d.polygon([(9,7),(12,7),(10,9)],fill=2)
    elif style==3:
        # Longitudinal setts: the course turns ninety degrees, a distinct bond.
        d.line((7,1,7,5),fill=2);d.line((7,9,7,13),fill=2)
        d.line((15,2,15,8),fill=2);d.line((15,13,15,14),fill=2)
        d.line((0,11,6,11),fill=2);d.line((8,3,14,3),fill=2)
        if v%4==0:d.line((1,1,5,1),fill=4)
        if v%5==3:d.line((9,5,13,5),fill=4)
    elif style==4:
        # Reclaimed oversized flags; occasional broad chips, no all-over noise.
        d.line([(0,14),(4,14),(5,15),(15,15)],fill=2)
        d.line([(14,0),(14,4),(15,5),(15,14)],fill=2)
        if v%3==0:d.line([(11,15),(10,12),(12,10)],fill=2)
        if v%5==2:d.line((1,2,6,2),fill=4)
        if v%7==1:d.polygon([(0,14),(2,12),(3,14),(2,15)],fill=2)
    else:
        # A small repaired herringbone panel: paired horizontal and vertical
        # bricks, with no continuous rectangular cell border.
        for xa,ya,xb,yb in ((0,0,7,3),(8,0,11,7),(12,0,15,7),
                            (0,4,3,11),(4,4,7,11),(8,8,15,11),
                            (0,12,7,15),(8,12,15,15)):
            d.line((xa,yb,xb,yb),fill=2)
            d.line((xb,ya,xb,yb),fill=2)
        d.line((15,1,15,3),fill=3);d.line((2,15,5,15),fill=3)
        d.line((7,5,7,6),fill=3);d.line((10,11,12,11),fill=3)
    # A few broad wet seams, never a loose icon or a blob on every floor tile.
    if v%17==6:
        d.polygon([(0,13),(3,12),(6,13),(8,15),(0,15)],fill=9)
        d.line((1,13,4,13),fill=10)
    return im


def wall_tile(style=1,variant=0):
    """Damaged retaining masonry descended from the preferred fourth wall."""
    im,d=_new(fill=2)
    v=int(variant)
    # A large heavy block with a shadowed lower return; its broken face is
    # darker than floor flags. Five treatments alter construction, not a hue.
    if style==1:
        d.polygon([(0,1),(13,1),(15,3),(15,13),(12,14),(0,14)],fill=3)
        d.line((1,1,10,1),fill=4)
        d.line((0,15,11,15),fill=1)
        if v%3==1:d.line([(11,3),(10,7),(12,10),(11,14)],fill=2)
    elif style==2:
        for y,cut in ((0,11),(8,4)):
            d.polygon([(0,y+1),(15,y+1),(15,y+5),(13,y+6),(0,y+6)],fill=3)
            d.line((1,y+1,8,y+1),fill=4)
            d.line((cut,y+1,cut,y+6),fill=2)
            d.line((0,y+7,13,y+7),fill=1)
        if v%3==2:d.polygon([(11,10),(15,9),(15,13),(13,14)],fill=2)
    elif style==3:
        d.rectangle((0,1,15,13),fill=3)
        d.line((1,1,11,1),fill=4)
        d.line((0,14,15,14),fill=1)
        d.line((12,2,12,8),fill=2)
        if v%3==0:d.line([(12,8),(10,10),(11,13)],fill=2)
    elif style==4:
        d.polygon([(0,1),(11,1),(14,3),(15,9),(13,14),(0,14)],fill=3)
        d.line((1,1,8,1),fill=4)
        d.line((0,15,10,15),fill=1)
        d.line([(12,2),(12,5),(10,7),(12,10),(11,14)],fill=2)
        if v%2:d.polygon([(0,10),(4,11),(2,15),(0,15)],fill=1)
    else:
        d.polygon([(0,1),(13,1),(15,3),(15,14),(0,14)],fill=3)
        d.line((1,1,10,1),fill=4)
        d.line((0,15,15,15),fill=1)
        d.line((5,2,5,5),fill=2)
        if v%3==1:d.line([(5,5),(7,8),(6,11),(8,14)],fill=2)
    if v%5==2:
        # Dampness grows from mortar, with a broken hanging edge.
        d.polygon([(0,0),(10,0),(9,2),(6,2),(5,6),(3,4),(2,8),(0,5)],fill=9)
        d.line((1,1,4,1),fill=10)
    return im


def water_tile(style=1,phase=0,variant=0,period=8):
    """A liquid plane with short asymmetric travelling wavelets, not roots."""
    im,d=_new(fill=8)
    shift=(int(phase)*16//max(1,int(period)))%16
    v=int(variant)
    # Wavelets are drawn on a periodic tile then translated as one surface.
    # Their far edge is dark; there are large uninterrupted areas of water.
    p,pd=_new(16,16,8)
    y=(2+v*5)%14
    length={1:11,2:9,3:12,4:8,5:10}[style]
    x=(v*5+style)%8-3
    pd.line((x,y,x+length,y),fill=9)
    pd.line((x+2,y+1,x+length-2,y+1),fill=9)
    if v%2==0:
        pd.line((x+3,y,x+7,y),fill=10)
        pd.line((x+length-2,y-1,x+length-1,y-1),fill=9)
    if v%7==3:pd.line((8,(y+6)%16,12,(y+6)%16),fill=9)
    # Very occasional foam at one crest. No pervasive luminous fish scales.
    if style in (2,4) and v%9==2:pd.line((x+4,y-1,x+5,y-1),fill=11)
    for yy in range(16):
        for xx in range(16):im.putpixel(((xx+shift)%16,yy),p.getpixel((xx,yy)))
    return im


def _fall_image(width=16,height=16,style=1,phase=0):
    """Straight translucent-looking water sheet with falling broken streaks."""
    im,d=_new(width,height,8)
    left=max(1,width//6);right=width-left-1
    d.rectangle((left,0,right,height-1),fill=9)
    d.rectangle((left+1,0,min(right,left+max(2,width//4)),height-1),fill=10)
    travel=(int(phase)*3)%max(8,height)
    for x,offset in ((left+1,0),(width//2,7),(right-1,13)):
        for y in range(height):
            if (y-travel-offset)%max(8,height)<3:d.point((x,y),fill=11)
    return im


def _bank_tile(style=1,side='n',variant=0):
    """Thick coping, a shadowed retaining face and locally accumulated filth."""
    im,d=_new(fill=3)
    v=int(variant)
    if side=='n':
        d.rectangle((0,0,15,2),fill=5)
        d.rectangle((0,3,15,6),fill=2)
        d.line((0,7,15,7),fill=1)
        d.rectangle((0,8,15,15),fill=8)
        d.line((0,3,5,3),fill=3)
        if style in (2,5):d.line((10,3,14,3),fill=3)
        if v%3==1:d.line((8,1,8,5),fill=2)
        if v%4==2:
            d.polygon([(1,4),(8,4),(7,7),(5,9),(3,8)],fill=9)
            d.line((2,4,5,4),fill=10)
    elif side=='s':
        d.line((0,0,15,0),fill=5)
        d.rectangle((0,1,15,3),fill=4)
        d.line((0,4,15,4),fill=2)
        if v%2:d.line((7,5,7,12),fill=2)
        if style in (1,3):d.line((1,6,4,6),fill=4)
        if v%4==0 or style==4:
            d.polygon([(0,3),(7,3),(8,5),(5,7),(1,6)],fill=9)
            d.line((1,4,4,4),fill=10)
    else:
        im,d=_new(fill=2)
        d.rectangle((0,0,15,2),fill=4)
        d.line((0,3,15,3),fill=1)
        # The lower retaining wall remains masonry under an attached slime
        # fringe; unequal drips stop it reading as a picket fence.
        d.line((9,5,9,14),fill=1)
        if v%3!=1:
            depth=7+(v%3)*2
            end=11 if style in (1,4) else 8
            d.polygon([(0,2),(end,2),(end-1,5),(7,6),(5,depth),(3,depth-2),(1,8)],fill=9)
            d.line((1,3,5,3),fill=10)
        if style==4:d.polygon([(12,4),(15,4),(15,9),(13,8)],fill=9)
    return im


def _bridge(style=1,w=32,h=64):
    """Five repaired/dilapidated timber crossings derived from preferred #4.

    The sound 32-pixel walking lane never changes. Splits are surface cracks,
    not holes that claim a different collision rule. Side strings join banks.
    """
    im,d=_new(w,h,2)
    for y in range(0,h,8):
        # Thick cross-planks show a lit top, dark near edge and restrained
        # grain. All five keep the recognizable patched-wood construction.
        if style==1:
            points=[(3,y+1),(w-4,y),(w-3,y+6),(4,y+6)]
        elif style==2:
            points=[(3,y),(w-5,y+1),(w-3,y+6),(4,y+7)]
        elif style==3:
            points=[(3,y+1),(w-4,y+1),(w-4,y+6),(3,y+6)]
        elif style==4:
            points=[(3,y+1),(w-5,y),(w-3,y+5),(w-6,y+7),(4,y+6)]
        else:
            points=[(3,y),(w-4,y+1),(w-3,y+6),(3,y+6)]
        d.polygon(points,fill=12)
        d.line((4,y+1,w-6,y+1),fill=13)
        d.line((8,y+3,w-11,y+3),fill=13 if style==3 else 12)
        # Iron fastenings catch less light than the main gold fittings.
        d.point((5,y+4),fill=4);d.point((w-6,y+4),fill=4)
        if style in (2,4):d.line([(w-10,y+2),(w-12,y+4),(w-10,y+6)],fill=2)
        if style==5:d.line((11,y+5,19,y+5),fill=2)
    d.line((1,0,1,h-1),fill=13)
    d.line((w-2,0,w-2,h-1),fill=12,width=2)
    if style in (1,4):
        d.polygon([(3,0),(7,0),(7,5),(5,8),(3,6)],fill=9)
        d.line((3,1,5,1),fill=10)
    if style==2:d.line((3,19,9,25),fill=5,width=2)
    elif style==3:d.rectangle((4,31,w-5,33),fill=4)
    elif style==4:d.line((3,41,12,44),fill=12,width=2)
    elif style==5:d.line((4,47,w-5,47),fill=5)
    return im


def _arch(d,box,style=1,gold=True,bars=True):
    x0,y0,x1,y1=box;w=x1-x0;radius=max(1,w//2)
    edge,face,lit=(12,13,14) if gold else (2,3,5)
    inset=max(2,min(5,w//5))
    # The left/top planes catch light, while the right jamb is in shadow.
    # Avoid concentric brightness rings: the face is a shaped material mass.
    d.rounded_rectangle(box,radius=radius,fill=edge)
    d.rounded_rectangle((x0+1,y0+1,x1-1,y1),radius=max(1,radius-1),fill=face)
    d.rectangle((x1-inset,y0+radius,x1,y1),fill=edge)
    d.rounded_rectangle((x0+inset,y0+inset,x1-inset,y1),radius=max(1,radius-inset),fill=1)
    d.arc((x0+1,y0+1,x1-1,y0+w-1),185,282,fill=lit,width=2 if w>20 else 1)
    d.line((x0+1,y0+radius,x0+1,y1-3),fill=lit)
    if style==2:
        d.ellipse((x0+1,y0+radius-2,x0+4,y0+radius+1),fill=lit)
    elif style==3:
        d.line((x0+radius-1,y0+1,x0+radius+2,y0+1),fill=15 if gold else 6)
    elif style==4:
        d.line([(x1-2,y0+radius),(x1-4,y0+radius+3),(x1-2,y0+radius+6)],fill=9)
    elif style==5:
        d.line((x0+inset,y0+2,x0+radius,y0+2),fill=lit)
    if bars:
        for x in range(x0+inset+2,x1-inset,5 if w<24 else 8):
            d.line((x,y0+radius,x,y1-3),fill=face,width=2)
            d.line((x,y0+radius,x,y1-4),fill=lit)


def _debris(style=1,variant=0):
    im,d=_new()
    _slime(d,1,8,13,6,style)
    if style==1:
        # A smashed stoneware dish and two dull shards, rather than loot.
        d.polygon([(2,9),(5,4),(10,3),(11,7),(7,10)],fill=4)
        d.line([(5,4),(9,4),(10,6)],fill=5)
        d.polygon([(11,10),(14,9),(13,13)],fill=4)
        d.line((2,12,5,12),fill=4)
    elif style==2:
        # Cartoon fish skeleton: broad backbone, recognisable empty head.
        d.ellipse((2,5,7,10),fill=5);d.point((3,7),fill=2)
        d.line((7,8,12,8),fill=5)
        d.line([(9,5),(9,10),(11,6),(11,10)],fill=5)
        d.polygon([(12,8),(14,5),(14,11)],fill=4)
    elif style==3:
        d.polygon([(3,9),(5,3),(7,8)],fill=10)
        d.line((5,4,5,7),fill=5)
        d.polygon([(8,10),(11,5),(14,9),(11,12)],fill=9)
        d.line((11,6,13,9),fill=10)
        d.point((5,12),fill=4)
    elif style==4:
        d.line((3,6,11,10),fill=5,width=2)
        for x,y in ((3,6),(11,10)):
            d.point((x,y-1),fill=5);d.point((x,y+1),fill=5)
        d.ellipse((9,3,14,7),fill=4)
        d.point((11,5),fill=2);d.point((13,5),fill=2)
    else:
        d.polygon([(2,6),(8,4),(12,6),(13,11),(7,13),(3,10)],fill=8)
        d.polygon([(3,7),(8,5),(11,7),(8,8),(7,12),(5,9)],fill=9)
        d.line([(6,6),(7,8),(6,10)],fill=10)
    if variant%2:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return im


def _grate(d,box,style=1):
    """Worn oval iron floor drain: a true barred recess, based on old #4."""
    x0,y0,x1,y1=box
    w=x1-x0;h=y1-y0;small=w<24
    d.ellipse(box,fill=1)
    d.ellipse((x0+1,y0,x1-1,y1-2),fill=4)
    d.ellipse((x0+3,y0+2,x1-3,y1-4),fill=2)
    d.ellipse((x0+5,y0+3,x1-5,y1-5),fill=1)
    # Bars are unmistakable and subdued iron, never gold treasure trim.
    step=3 if small else (7 if style in (1,3) else 8)
    for x in range(x0+(3 if small else 9),x1-(2 if small else 7),step):
        top=y0+(3 if small else 6);bottom=y1-(3 if small else 7)
        d.line((x,top,x,bottom),fill=4,width=1 if small else 2)
        if not small:d.line((x-1,top,x-1,bottom-1),fill=5)
    if not small:
        d.line((x0+7,y0+11,x1-7,y0+11),fill=3)
        d.arc((x0+2,y0+1,x1-2,y1-3),198,265,fill=5,width=2)
        if style in (2,4):
            d.polygon([(x0+3,y1-9),(x0+12,y1-8),(x0+10,y1-4),(x0+5,y1-3)],fill=9)
        if style==4:d.line((x1-10,y0+6,x1-12,y0+12),fill=1,width=2)
    else:d.line((x0+3,(y0+y1)//2,x1-3,(y0+y1)//2),fill=3)


def _rails(g,o,style=1):
    """Readable Crown/Crooked brasswork with uneven wear and attached tarnish."""
    d=ImageDraw.Draw(g);od=ImageDraw.Draw(o)
    for x in range(16,464,32):
        if 224<=x<256:continue
        d.line((x+7,142,x+7,150),fill=12,width=3)
        od.rectangle((x+5,132,x+9,143),fill=1)
        od.line((x+6,133,x+6,142),fill=13)
        od.line((x+7,133,x+7,141),fill=14 if style!=4 else 13)
        if style in (2,5):
            od.ellipse((x+4,130,x+10,135),fill=13)
            od.line((x+5,131,x+8,131),fill=14)
        else:
            od.polygon([(x+5,133),(x+7,130),(x+9,133)],fill=13)
            od.point((x+6,132),fill=14)
        if (x//32+style)%4==0:
            od.line((x+7,138,x+7,142),fill=9)
            od.point((x+7,138),fill=10)
    for x0,x1 in ((16,223),(256,463)):
        d.line((x0,145,x1,145),fill=12,width=3)
        d.line((x0,144,x1,144),fill=13)
        for x in range(x0+19,x1,64):d.line((x,144,min(x+6,x1),144),fill=9)
    for x in range(16,448,16):
        od.line((x+1,260,x+1,271),fill=1,width=3)
        od.line((x,261,x,270),fill=13)
        od.line((x+1,261,x+1,267),fill=14 if style!=4 else 13)
        od.line((x,267,x+15,267),fill=12)
        od.line((x,266,x+15,266),fill=13)
        if style in (2,5):od.rectangle((x,259,x+2,262),fill=13)
        if (x//16+style)%5==0:od.line((x+6,266,x+10,266),fill=9)


from sewer_v3_fixtures import install as _install_feedback_fixtures
_install_feedback_fixtures(globals())


@lru_cache(maxsize=128)


def _layers(key,phase,period=8):
    s=dict(zip(CATEGORIES,key));phase=int(phase)
    g,d=_new(480,320,3);o,od=_new(480,320,0)
    # All floors begin with seamless final-size brick cells. The physical room
    # controls where the walkable flags stop; no invented obstacle is added.
    for y in range(20):
        for x in range(30):g.paste(floor_tile(s['floor'],x+y*7),(x*16,y*16))
    for y in range(4):
        for x in range(30):g.paste(wall_tile(s['masonry'],(x+y)%5),(x*16,y*16))
    for y in range(4,17):
        for x in (0,29):g.paste(wall_tile(s['masonry'],y%5),(x*16,y*16))
    # The same 64px north wall has a strong ledge and damp lower courses.
    d.line((0,62,479,62),fill=6);d.line((0,63,479,63),fill=1)
    for x in (24,88,181,302,392,447):
        _slime(d,x,55,16,8,s['props'])
    # Stream and foreground reservoir. Stream banks are fixed at y144/193.
    d.rectangle((16,144,463,207),fill=1)
    for y in (160,176,288,304):
        for x in range(16 if y<200 else 0,464 if y<200 else 480,16):
            g.paste(water_tile(s['water'],phase,(x//16+y//16)%4,period),(x,y))
    d.rectangle((16,151,463,159),fill=8)
    for x in range(18,461,24):
        off=(phase*24//max(1,period))%24
        d.line((x+off,155,x+6+off,155),fill=9)
    d.rectangle((16,144,463,150),fill=4)
    d.line((16,144,463,144),fill=6);d.line((16,151,463,151),fill=1)
    d.rectangle((16,193,463,207),fill=3)
    d.line((16,193,463,193),fill=6);d.line((16,207,463,207),fill=1)
    for x in (24,85,151,294,374,424):_slime(d,x,153,24,7,s['props'])
    for x in range(16,464,16):
        g.paste(_bank_tile(s['masonry'],'n',x//16),(x,144))
        g.paste(_bank_tile(s['masonry'],'s',x//16),(x,192))
    _paste(g,_bridge(s['bridge']),(224,144))
    d.rectangle((0,272,479,287),fill=2)
    d.line((16,272,463,272),fill=6)
    for x in range(0,480,16):g.paste(_bank_tile(s['masonry'],'b',x//16),(x,272))
    # Large unmistakably gold barred sewer in the rear wall.
    _grand_outfall(g,s['metal'],phase)
    _basin(g,s['water'],phase,period)
    _ladder(g,o,s['metal'])
    _pipe(d,(18,32,125,41),s['metal'],True)
    _pipe(d,(417,6,427,62),s['metal'])
    _market(g,o,s['market'],phase)
    _sanctum(g,s['sanctum'],phase)
    for x in (400,424):_crate(d,x,65,s['props'])
    _barrel(d,440,72,s['props'])
    # The outfall discharges into the actual stream, never a false wet floor.
    _small_outfall(g,s['metal'],phase,period)
    _grate(d,(207,225,273,255),s['metal'])
    # Deliberate visual debris clusters: broken crockery, bones, rags and slime.
    # They sit away from the clear bridge and exit approaches.
    for x,y in ((139,101),(320,122),(88,228),(322,228),(389,246),(49,223)):
        _slime(d,x,y,22,8,s['props'])
    # Broad attached grease deposits have subdued contrast. The handful of
    # recognizable debris pieces are authored only in DEBRIS_SITES, never
    # sprinkled as bright false-pickup icons across the traversable floor.
    for x,y,w,h in ((27,43,26,16),(85,43,30,16),(425,92,18,6),
                    (165,108,28,13),(367,116,29,13),(49,223,32,14),(388,245,27,14)):
        _slime(d,x,y,w,h,s['props'])
    _rails(g,o,s['metal'])
    for i,(x,y) in enumerate(((33,34),(119,33),(151,30),(225,16),(261,83),(295,62),(372,62),(438,137),(219,229),(265,246))):
        _glint(d,x,y,phase+i)
    return g,o


def category(name):
    if name.startswith('swh_'):
        layer,x,y=OCCURRENCES[name][0]
        if layer=='overlay':return 'market' if 2<=x<=6 and 5<=y<=6 else 'metal'
        if (x,y) in DEBRIS_SITES:return 'props'
        if 14<=x<=15 and 9<=y<=12:return 'bridge'
        if y in (10,11,18,19):return 'water'
        if 1<=x<=7 and 3<=y<=6:return 'market'
        if 18<=x<=23 and 3<=y<=6:return 'sanctum'
        if 8<=x<=10 and 1<=y<=3 or 11<=x<=18 and y<=6 or x>=26 and 1<=y<=10:return 'metal'
        if y<4 or x in (0,29):return 'masonry'
        if y in (9,12,17):return 'masonry'
        if 13<=x<=17 and 14<=y<=15:return 'metal'
        if x>=25 and y in (4,5):return 'props'
        return 'floor'
    s=name[3:]
    if s.startswith('floor'):return 'floor'
    if s.startswith('water') or s.startswith('fall') or s=='lilypad':return 'water'
    if s.startswith('wall'):return 'masonry'
    if s.startswith(('awning','counter','banner')):return 'market'
    if s.startswith('rug') or s in ('candles','torch_lit','lantern'):return 'sanctum'
    if s in ('pipe','pipe_h','ladder','ladder_down','hole','arch','arch_r','grate','grate_r') or s.startswith(('drain','glint')):return 'metal'
    return 'props'


def _repeated(name,phase,key):
    ps=OCCURRENCES[name];layer,x,y=ps[0]
    if layer=='overlay' or len(ps)==1:return None
    styles=dict(zip(CATEGORIES,key));s=styles[category(name)]
    n=int(name[4:])
    # These two reused panels occur only within the same horizontal wall
    # pipe. Keep their continuous tube instead of replacing its middle with
    # plain masonry. Their duplicate occurrences use the same material and
    # height, so sharing these exact crops creates no stray pipe elsewhere.
    if name in ('swh_058','swh_059'):
        ground,_=_layers(key,phase,TILES[name]['frames'])
        return ground.crop((x*16,y*16,x*16+16,y*16+16))
    if y<4:return wall_tile(styles['masonry'],n)
    if all(xx in (14,15) and 9<=yy<=12 for _,xx,yy in ps):
        return _bridge(styles['bridge']).crop((0 if x==14 else 16,0,16 if x==14 else 32,16))
    if TILES[name]['coll']==0:return floor_tile(styles['floor'],n)
    im,d=_new(fill=3)
    if y in (10,11,18,19):return water_tile(styles['water'],phase,n,TILES[name]['frames'])
    if TILES[name]['coll']==12 and y<9:
        d.rectangle((0,0,15,6),fill=4);d.line((0,0,15,0),fill=6);d.line((0,7,15,7),fill=1)
        style=styles['masonry']
        if style==1:d.line((7,2,7,6),fill=2)
        elif style==2:d.rounded_rectangle((2,2,13,6),radius=2,fill=5)
        elif style==3:d.line((0,3,15,3),fill=5)
        elif style==4:d.line([(4,1),(7,3),(5,5)],fill=2)
        else:d.line((0,2,15,2),fill=7);d.point((7,5),fill=13)
        return im
    if y==9:
        return _bank_tile(styles['masonry'],'n',n)
    if y==12:
        return _bank_tile(styles['masonry'],'s',n)
    if y==17:
        return _bank_tile(styles['masonry'],'b',n)
    return wall_tile(styles['masonry'],n)


def _legacy(name,phase,key):
    s=dict(zip(CATEGORIES,key));kind=name[3:];style=s[category(name)]
    if kind.startswith('floor'):
        im=floor_tile(style,sum(map(ord,kind))%31);d=ImageDraw.Draw(im)
        if any(p in kind for p in ('slime','grime','moss')):_slime(d,0,7,14,7,style)
        elif 'crack' in kind:d.line([(2,1),(6,5),(4,9),(8,14)],fill=2)
        elif 'puddle' in kind:
            d.ellipse((1,5,14,13),fill=8);d.line((4+phase%3,7,9+phase%3,7),fill=10)
        elif 'bones' in kind:
            d.line((3,7,12,11),fill=7,width=2)
            for x,y in ((3,7),(12,11)):d.point((x,y-1),fill=7);d.point((x,y+1),fill=7)
        elif 'shroom' in kind:
            d.line((7,9,7,14),fill=7);d.ellipse((3,5,12,10),fill=9);d.line((4,6,9,6),fill=11)
        elif 'drip' in kind:_glint(d,8,9,phase)
        return im
    if kind.startswith('wall'):
        im=wall_tile(style,sum(map(ord,kind))%13);d=ImageDraw.Draw(im)
        if any(p in kind for p in ('slime','moss','fungus','drip')):
            d.polygon([(0,0),(14,0),(12,3),(9,2),(8,9),(5,5),(3,12),(1,5)],fill=9)
            d.line((2,1,3,6),fill=10)
        if 'crack' in kind:d.line([(11,0),(8,5),(10,8),(7,15)],fill=1)
        if 'chain' in kind:
            for y in (0,4,8,12):d.ellipse((6,y,9,y+4),outline=6)
        if 'drip' in kind:d.point((7,8+phase%5),fill=11)
        if 'web' in kind:
            for end in ((15,0),(12,9),(7,15),(0,15)):d.line((0,0,*end),fill=6)
            d.line([(0,5),(3,4),(5,0)],fill=6);d.line([(0,10),(6,8),(10,0)],fill=6)
        if 'tally' in kind:
            for x in (3,5,7,9):d.line((x,4,x,10),fill=7)
            d.line((2,10,10,4),fill=7)
        if 'window' in kind:
            d.rectangle((3,2,12,13),fill=1);d.line((7,3,7,12),fill=5);d.point((10,6),fill=14+phase%2)
        if 'skull' in kind:
            d.ellipse((4,3,11,10),fill=7);d.point((6,6),fill=1);d.point((9,6),fill=1);d.rectangle((5,9,10,11),fill=6)
        if 'rust' in kind:d.line([(3,2),(3,10),(5,13)],fill=12,width=2)
        return im
    if kind.startswith('water') or kind=='lilypad':
        if kind=='waterfall':
            return _fall_image(16,16,style,phase)
        im=water_tile(style,phase,0,TILES[name]['frames']);d=ImageDraw.Draw(im)
        if 'edge_n' in kind:d.rectangle((0,0,15,3),fill=4);d.line((0,3,15,3),fill=6)
        if 'edge_s' in kind:d.rectangle((0,12,15,15),fill=3);d.line((0,12,15,12),fill=6)
        if 'scum' in kind:_slime(d,0,5,15,6,style)
        if 'bubble' in kind:
            r=phase%3;d.ellipse((6-r,6-r,9+r,9+r),outline=10)
        if 'glint' in kind:_glint(d,8,7,phase)
        if kind=='lilypad':d.ellipse((3,5,12,12),fill=10);d.line((7,6,7,9),fill=9)
        return im
    if kind.startswith('fall_'):
        n=int(kind[-1]);im=_fall_image(48,32,style,phase)
        return im.crop(((n%3)*16,(n//3)*16,(n%3+1)*16,(n//3+1)*16))
    if kind.startswith('glint'):
        im,d=_new();_glint(d,8,8,phase);return im
    if kind in ('ladder','ladder_down','hole'):
        im,d=_new(fill=1)
        d.rectangle((1,0,3,15),fill=13);d.line((1,0,1,15),fill=14)
        d.rectangle((12,0,14,15),fill=12);d.line((12,1,12,14),fill=13)
        for y in (2,8,14):
            d.line((4,y,11,y),fill=14,width=2 if style==2 else 1)
            d.line((4,y+1,11,y+1),fill=12)
            if style in (1,3):d.point((4,y),fill=15)
            elif style==4:d.point((8,y),fill=13)
            elif style==5:d.point((5,y),fill=15)
        return im
    if kind in ('arch','arch_r'):
        im,d=_new();_arch(d,(0,-1,15,16),style,True,False);return im
    if kind in ('pipe','pipe_h'):
        im,d=_new();_pipe(d,(5,-2,11,17),style)
        return im.transpose(Image.Transpose.ROTATE_90) if kind=='pipe_h' else im
    if kind in ('grate','grate_r') or kind.startswith('drain_'):
        im,d=_new(fill=3)
        if kind.startswith('drain_'):
            big,bd=_new(32,32,3);_grate(bd,(0,0,31,31),style)
            x=16 if kind.endswith(('ne','se')) else 0;y=16 if kind.endswith(('sw','se')) else 0
            return big.crop((x,y,x+16,y+16))
        _grate(d,(0,0,15,15),style);return im
    if kind in ('torch_lit','candles','lantern'):
        im,d=_new();d.rectangle((6,8,9,14),fill=12);d.line((5,14,10,14),fill=14)
        d.polygon([(5,8),(5,5),(8+phase%2,1),(10,5),(10,8)],fill=14);d.point((7,6),fill=15)
        if kind=='lantern':d.rectangle((3,4,12,12),outline=13)
        if style==2:d.ellipse((4,9,11,14),fill=13)
        elif style==3:d.line((6,9,6,13),fill=7)
        elif style==4:d.line([(6,10),(5,12),(7,14)],fill=9)
        elif style==5:d.line((4,13,11,13),fill=14);d.point((7,10),fill=15)
        return im
    if kind.startswith('banner'):
        im,d=_new();d.rectangle((2,0,13,12),fill=9 if kind.endswith('teal') else 12)
        d.polygon([(2,12),(7,15),(13,12)],fill=9 if kind.endswith('teal') else 12)
        d.line((2,0,13,0),fill=14)
        if style==1:d.line((7,3,7,10),fill=14);d.line((5,6,9,6),fill=14)
        elif style==2:d.ellipse((5,4,10,9),outline=14)
        elif style==3:d.line([(4,5),(7,9),(11,5)],fill=14)
        elif style==4:d.line([(6,3),(8,6),(6,10)],fill=13);d.line((9,11,9,15),fill=0)
        else:d.polygon([(7,3),(11,7),(7,11),(4,7)],outline=14)
        return im
    if kind.startswith('rug_'):
        big,bd=_new(32,32,9);bd.rectangle((1,1,30,30),outline=13);bd.rectangle((4,4,27,27),outline=10)
        if style==1:bd.polygon([(16,6),(25,16),(16,25),(7,16)],outline=14)
        elif style==2:bd.ellipse((8,8,24,24),outline=11);bd.point((16,16),fill=14)
        elif style==3:bd.polygon([(16,5),(27,16),(16,27),(5,16)],outline=11);bd.ellipse((11,11,21,21),outline=13)
        elif style==4:bd.line([(7,8),(10,12),(8,17),(12,21)],fill=1);bd.polygon([(16,7),(24,16),(16,25),(8,16)],outline=13)
        else:bd.rectangle((8,8,24,24),outline=14);bd.polygon([(16,10),(22,16),(16,22),(10,16)],outline=13)
        x=16 if kind.endswith(('ne','se')) else 0;y=16 if kind.endswith(('sw','se')) else 0
        return big.crop((x,y,x+16,y+16))
    if kind.startswith('awning'):
        im,d=_new()
        d.rectangle((0,0,15,10),fill=9)
        d.polygon([(0,1),(15,1),(11,4),(2,4)],fill=10)
        if style==2:d.polygon([(0,9),(15,9),(13,13),(10,14),(6,14),(2,12)],fill=9)
        elif style==4:d.polygon([(0,9),(15,9),(14,13),(10,11),(7,15),(5,12),(1,13)],fill=9)
        else:d.polygon([(0,9),(15,9),(11,13),(7,15),(3,12)],fill=9)
        if style==3:d.polygon([(7,3),(9,3),(12,11),(10,12)],fill=8)
        elif style==5:d.line((0,0,15,0),fill=12)
        return im
    im,d=_new()
    if kind in ('counter','counter_r'):
        d.rectangle((0,2,15,15),fill=12)
        d.polygon([(0,0),(15,0),(13,3),(1,3)],fill=13)
        d.line((1,0,7,0),fill=14)
        d.line((0,4,15,4),fill=2)
        if style==1:d.line((5,6,5,14),fill=13)
        elif style==2:d.line((2,7,13,12),fill=13,width=2)
        elif style==3:d.line((1,9,14,9),fill=13)
        elif style==4:d.polygon([(2,8),(8,7),(10,12),(4,14)],fill=9)
        else:d.rectangle((2,7,13,13),outline=13)
    elif kind=='crate':_crate(d,0,0,style,15,15)
    elif kind=='barrel':
        d.ellipse((2,0,13,15),fill=12)
        d.polygon([(4,4),(8,3),(9,14),(4,13)],fill=13)
        d.ellipse((3,0,12,5),fill=5);d.ellipse((4,1,11,4),fill=12)
        for y in (6,12):d.line((3,y,12,y),fill=5);d.line((4,y-1,7,y-1),fill=6)
        if style==2:d.line((10,6,10,11),fill=12)
        elif style==3:d.point((4,3),fill=6)
        elif style==4:d.line([(6,7),(5,9),(7,11)],fill=2)
        elif style==5:d.line((11,6,11,11),fill=12)
    elif kind=='skull':
        d.ellipse((3,2,12,11),fill=1);d.ellipse((4,3,11,10),fill=7)
        d.point((6,6),fill=1);d.point((9,6),fill=1);d.rectangle((5,10,10,13),fill=6)
        if style==2:d.ellipse((3,2,6,5),fill=6);d.line((4,12,11,12),fill=7)
        elif style==3:d.line([(8,3),(7,5),(8,7)],fill=4)
        elif style==4:d.rectangle((8,10,10,13),fill=0);d.point((5,4),fill=5)
        elif style==5:d.line((5,3,10,3),fill=7);d.point((7,11),fill=1)
    elif kind=='pot':
        d.polygon([(4,3),(11,3),(10,6),(13,9),(12,13),(9,15),(5,14),(3,11),(4,7)],fill=2)
        d.polygon([(5,5),(9,5),(9,7),(11,9),(10,12),(5,12),(4,10),(6,7)],fill=4)
        d.polygon([(5,6),(7,6),(6,9),(6,11),(4,10)],fill=5)
        d.line((4,3,11,3),fill=5);d.line((6,4,10,4),fill=2)
        if style==2:d.ellipse((1,5,5,10),outline=4);d.ellipse((10,5,14,10),outline=4)
        elif style==3:d.line((5,10,10,10),fill=5)
        elif style==4:d.line([(9,6),(8,8),(10,11)],fill=2)
        elif style==5:d.line((6,12,10,12),fill=3)
    elif kind=='gold':
        d.ellipse((3,4,12,12),fill=12);d.ellipse((4,4,11,10),fill=14);d.line((6,5,8,5),fill=15)
        if style==2:d.ellipse((1,8,7,13),fill=13);d.line((2,9,5,9),fill=14)
        elif style==3:d.polygon([(4,5),(8,3),(12,6),(8,11)],fill=13);d.line((5,5,8,4),fill=15)
        elif style==4:d.line([(9,4),(7,7),(9,9)],fill=12)
        elif style==5:d.rectangle((5,6,10,9),outline=13)
    elif kind=='rubble':
        d.polygon([(1,12),(4,5),(9,4),(14,11),(11,14),(3,14)],fill=2)
        d.polygon([(3,11),(5,6),(9,5),(11,9),(8,12)],fill=5);d.line((5,6,8,6),fill=7)
        if style==2:d.ellipse((0,8,5,13),fill=4)
        elif style==3:d.polygon([(10,5),(14,8),(12,12)],fill=6)
        elif style==4:d.line([(6,6),(5,9),(7,12)],fill=2)
        elif style==5:d.line((7,6,10,9),fill=6)
    else:raise KeyError('Unpainted sewer concept tile '+name)
    return im


def paint(name,phase=0,recipe=None):
    key=recipe_key(recipe)
    if name.startswith('sw_'):
        result=_legacy(name,int(phase),key)
    elif name.startswith('swh_'):
        layer,x,y=OCCURRENCES[name][0]
        result=_repeated(name,int(phase),key)
        if result is None:
            g,o=_layers(key,int(phase),TILES[name]['frames'])
            result=(g if layer=='ground' else o).crop((x*16,y*16,x*16+16,y*16+16))
        if layer=='ground' and (x,y) in DEBRIS_SITES:
            _paste(result,_debris(dict(zip(CATEGORIES,key))['props'],DEBRIS_SITES[x,y]),(0,0))
    else:raise KeyError(name)
    assert result.size==(16,16) and max(result.getdata())<=15,name
    return result


def full_layers(recipe=None,phase=0):
    """Assemble precisely the fixed map, including all reused metatile IDs."""
    g,_=_new(480,320);o,_=_new(480,320)
    for layer,dst in (('ground',g),('overlay',o)):
        for y,row in enumerate(ROOM[layer]):
            for x,name in enumerate(row):
                if name:dst.paste(paint(name,phase,recipe),(x*16,y*16))
    return g,o
