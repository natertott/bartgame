"""Five reference-led, native-resolution Drain material studies.

Only the fixed map identifiers and occurrence positions come from the room
contract. Every pixel here is drawn at its final GBA size, with one sixteen
ink bank. Equal material roles let the review builds mix individual parts.
This module is opt-in; it does not replace the released Drain painter.

Revision 2 models large lit masses before texture: quiet ground, darker raised
masonry, broad dirty-water clusters and selective metallic speculars. The PDF
notes are recorded in docs/art-reboot; no source illustration pixels are used.
"""
from functools import lru_cache
import json
from pathlib import Path
from PIL import Image, ImageDraw

STYLE_NAMES = {1:'Crown of Sludge', 2:'Crooked Brassworks', 3:'Moonlit Cistern',
               4:'Rotten Reliquary', 5:'Royal Drains'}
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
 1:['#000000','#182028','#283840','#485050','#606858','#889080','#a8b0a0','#c8d0b8',
    '#102830','#304838','#506850','#90a878','#705030','#a88038','#e0b850','#f8e8b0'],
 2:['#000000','#202030','#383840','#586058','#788070','#98a088','#b0b8a0','#d0d0b0',
    '#183038','#385040','#608058','#a0b878','#785030','#b08038','#f0c058','#f8e8b0'],
 3:['#000000','#101828','#203040','#405058','#586868','#809088','#a0b0a8','#c8d0b8',
    '#102830','#284850','#487878','#88b0a0','#685038','#a08040','#e0c078','#f8f0c8'],
 4:['#000000','#182028','#303838','#505848','#687058','#909078','#b0b098','#d0d0b0',
    '#182828','#384838','#586840','#98a860','#685030','#a08038','#d8b050','#f0e0a8'],
 5:['#000000','#181828','#283840','#485860','#687878','#909888','#b0b8a0','#d0d8b8',
    '#102830','#304840','#507868','#98b888','#705038','#a88848','#e8c868','#f8f0c8']}


def palette(style=1):
    return list(PALETTES[int(style)])


def rail_sprite(style=1):
    """A seamless16x8OBJhandrail in the existing shared gold/FX bank.

    At worldY136 the upper edge is Y138, crossing the existing post centres.
    Both end pixels join the next segment; the bridge opening is left empty
    by the caller. This adds no new physical obstruction or palette bank.
    """
    im,d=_new(16,8)
    if style==1:
        d.line((0,2,15,2),fill=10);d.line((0,3,15,3),fill=7)
        d.rectangle((6,1,8,4),fill=8);d.line((6,1,8,1),fill=10)
    elif style==2:
        d.line((0,2,15,2),fill=10);d.line((0,3,15,3),fill=7)
        d.polygon([(5,2),(6,0),(9,0),(11,2),(9,4),(6,4)],fill=8)
        d.line((6,1,8,1),fill=11)
    elif style==3:
        d.line((0,2,15,2),fill=11);d.line((0,3,15,3),fill=7)
        d.line((7,1,7,4),fill=8)
    elif style==4:
        d.line((0,2,15,2),fill=9);d.line((0,3,15,3),fill=7)
        d.polygon([(5,1),(8,1),(9,4),(6,5),(5,3)],fill=8)
        d.line((6,1,7,1),fill=10);d.line((11,2,13,2),fill=7)
    else:
        d.line((0,2,15,2),fill=10);d.line((0,3,15,3),fill=7)
        d.rectangle((6,0,9,4),fill=8)
        d.line((6,0,9,0),fill=10);d.point((6,1),fill=12)
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
        d.line((x+w//4,y+1,x+w//4+3,y+1),fill=11)


def floor_tile(style=1,variant=0):
    """Quiet gray flags: material suggestion, not a contour around each brick."""
    im,d=_new(fill=3)
    # Mortar runs are interrupted and the lit top plane is sparse. Adjacent
    # floor cells are a continuous travel plane, not a grid of outlined icons.
    if style==1:
        d.line((0,15,15,15),fill=2)
        cut=4 if variant%2 else 12
        d.line((cut,0,cut,3),fill=2)
        if variant%4==0:d.rectangle((1,1,8,2),fill=4)
    elif style==2:
        d.line([(2,13),(4,15),(11,15),(13,13)],fill=2)
        if variant%3==0:d.line([(1,3),(3,2),(8,2)],fill=4)
        if variant%2:d.line((14,3,15,4),fill=2)
    elif style==3:
        d.line((0,15,15,15),fill=2)
        if variant%2:d.line((6,0,6,2),fill=2)
        if variant%5==1:d.rectangle((3,1,10,2),fill=4)
    elif style==4:
        d.line([(0,14),(4,14),(6,15),(10,15)],fill=2)
        if variant%4==1:d.line([(13,15),(11,13),(12,11)],fill=2)
        if variant%5==0:d.line((1,2,6,2),fill=4)
    else:
        d.line([(0,13),(2,15),(7,15)],fill=2)
        d.line((13,15,15,13),fill=2)
        if variant%2:d.line((8,0,8,2),fill=2)
        if variant%5==3:d.line((3,1,9,1),fill=4)
    if variant%9==2:_slime(d,2,9,12,5,style)
    return im


def wall_tile(style=1,variant=0):
    im,d=_new(fill=2)
    if style==1:
        for y in (0,8):
            split=10 if y==0 else 2
            d.rectangle((0,y+1,15,y+6),fill=3)
            d.line((0,y+1,15,y+1),fill=4)
            d.line((split,y+1,split,y+6),fill=2)
            d.line((0,y+7,15,y+7),fill=1)
            if variant%3==0:d.line((split+1,y+2,min(15,split+4),y+2),fill=5)
    elif style==2:
        for y,split in ((0,6),(8,14)):
            for xa,xb in ((-3,split),(split+1,18)):
                d.polygon([(xa,y+3),(xa+2,y+1),(xb-2,y+1),(xb,y+3),(xb,y+6),(xa,y+6)],fill=3)
                d.line((max(0,xa+2),y+1,min(15,xb-2),y+1),fill=5)
                d.line((max(0,xa+1),y+2,min(15,xb-3),y+2),fill=4)
    elif style==3:
        d.rectangle((0,1,15,14),fill=3)
        d.line((0,1,15,1),fill=4)
        d.line((0,15,15,15),fill=1)
        d.line((12 if variant%2 else 4,2,12 if variant%2 else 4,13),fill=2)
        d.line((1,3,5,3),fill=5)
    elif style==4:
        d.rectangle((0,1,15,14),fill=3)
        d.line((0,15,10,15),fill=1)
        d.line((1,1,8,1),fill=4)
        d.line((12,2,12,5),fill=2)
        if variant%3==1:d.line([(12,5),(10,7),(12,10),(11,14)],fill=2)
        d.polygon([(0,11),(3,12),(2,15),(0,15)],fill=2)
    else:
        for y in (0,8):
            d.polygon([(0,y+2),(2,y),(13,y),(15,y+2),(15,y+6),(0,y+6)],fill=3)
            d.line((2,y+1,12,y+1),fill=5)
            d.line((0,y+7,15,y+7),fill=1)
            split=7 if y==0 else 15
            d.line((split,y+2,split,y+6),fill=2)
    if variant%5==2:_slime(d,-2,0,12,7,style)
    return im


def water_tile(style=1,phase=0,variant=0,period=8):
    im,d=_new(fill=8)
    shift=(int(phase)*16//max(1,int(period)))%16
    # Translated connected ribbons describe flow and keep the pixel clusters
    # coherent through the exact animation period; no random dither is used.
    ribbons={1:[(0,4),(4,2),(11,2),(14,4),(10,5),(3,5)],
             2:[(1,4),(3,2),(9,2),(13,5),(9,6),(3,5)],
             3:[(0,4),(6,3),(14,3),(15,4),(11,5),(3,5)],
             4:[(1,4),(5,2),(10,3),(14,5),(10,6),(3,5)],
             5:[(0,4),(3,2),(11,2),(14,4),(10,5),(3,5)]}
    patch,pd=_new(16,16,8)
    pd.polygon(ribbons[style],fill=9)
    if variant%4==1:
        pd.line((4,3,9 if style!=3 else 12,3),fill=10)
        pd.line((10,11,14,11),fill=9)
    elif variant%4==3:
        pd.line([(8,10),(11,9),(14,10)],fill=9)
    elif variant%4==0:
        # Leave a larger calm interval between neighbouring current groups.
        pd.rectangle((10,0,15,7),fill=8)
    yshift=(variant*3+style)%7
    for y in range(16):
        for x in range(16):im.putpixel(((x+shift+variant*3)%16,(y+yshift)%16),patch.getpixel((x,y)))
    return im


def _fall_image(width=16,height=16,style=1,phase=0):
    im,d=_new(width,height,8)
    spacing={1:4,2:5,3:3,4:6,5:4}[style]
    offset=2 if style==5 else 1
    for x in range(offset,width,spacing):
        d.line((x,0,x,height-1),fill=9,width=2 if style in (2,5) else 1)
        yy=(phase*3+x+style)%max(1,height-3)
        d.line((x,yy,x,min(height-1,yy+3+style)),fill=11)
        if style==4:d.point((x-1,min(height-1,yy+1)),fill=10)
    return im


def _bank_tile(style=1,side='n',variant=0):
    """One lit coping plane over a darker vertical bank, with attached slime."""
    im,d=_new(fill=3)
    if side=='n':
        d.rectangle((0,0,15,2),fill=5)
        d.rectangle((0,3,15,6),fill=3)
        d.line((0,7,15,7),fill=1)
        d.rectangle((0,8,15,15),fill=8)
        if style==1:d.line((7,3,7,6),fill=2)
        elif style==2:d.line([(1,3),(3,5),(11,5),(13,3)],fill=4)
        elif style==3:d.line((0,3,15,3),fill=4)
        elif style==4:
            d.polygon([(9,4),(15,5),(14,9),(11,8),(10,11)],fill=9)
            d.line((1,3,6,3),fill=4)
        else:d.line((0,2,15,2),fill=6);d.line((8,4,8,6),fill=2)
    elif side=='s':
        d.line((0,0,15,0),fill=5)
        d.rectangle((0,1,15,3),fill=4)
        d.line((0,4,15,4),fill=2)
        if style==1:d.line((7,5,7,15),fill=2)
        elif style==2:
            d.line([(1,7),(3,6),(11,6),(13,8)],fill=4)
            d.line((3,14,10,14),fill=2)
        elif style==3:d.line((3,5,3,14),fill=2)
        elif style==4:
            d.line((0,14,6,14),fill=2)
            if variant%2:d.line([(12,5),(11,8),(12,11)],fill=2)
            d.polygon([(1,5),(8,5),(7,8),(4,7),(3,10)],fill=9)
        else:d.line((8,5,8,15),fill=2);d.line((1,6,5,6),fill=4)
    else:
        im,d=_new(fill=2)
        d.rectangle((0,0,15,2),fill=4)
        d.line((0,3,15,3),fill=1)
        depth=7+(variant%4)*2
        if style==1:
            d.polygon([(1,2),(11,2),(9,depth),(6,depth-2),(4,depth+2),(2,7)],fill=9)
            d.line((3,3,4,depth-1),fill=10)
        elif style==2:
            d.polygon([(1,2),(13,2),(12,6),(9,7),(8,depth),(4,depth+1),(2,7)],fill=9)
            d.line((3,3,8,3),fill=10)
        elif style==3:
            d.line((3,3,3,depth),fill=9,width=2)
            d.line((10,3,10,depth-3),fill=10)
        elif style==4:
            d.polygon([(0,2),(14,2),(12,7),(10,6),(9,depth),(6,depth-2),(4,min(15,depth+2)),(1,8)],fill=9)
            d.line([(2,3),(4,6),(3,9)],fill=10)
        else:
            d.polygon([(4,3),(12,3),(11,depth-1),(8,depth-3),(6,depth),(4,7)],fill=9)
            d.line((5,3,6,depth-2),fill=10)
    return im


def _bridge(style=1,w=32,h=64):
    # The painted crossing is always the same usable 32px lane. Top planes
    # stay lighter than undersides; this cannot be mistaken for a ladder.
    im,d=_new(w,h,2)
    if style==1:
        d.rectangle((3,0,w-4,h-1),fill=4)
        for y in range(0,h,16):
            d.line((3,y,w-4,y),fill=2)
            d.polygon([(4,y+1),(w-6,y+1),(w-9,y+4),(4,y+5)],fill=5)
            d.line((w//2,y+8,w//2,y+15),fill=3)
        d.line((1,0,1,h-1),fill=13,width=2)
        d.line((w-2,0,w-2,h-1),fill=12,width=2)
    elif style==2:
        for y in range(0,h,8):
            d.polygon([(3,y+1),(w-5,y),(w-3,y+2),(w-3,y+6),(4,y+7)],fill=13)
            d.line((5,y+1,w-6,y+1),fill=14)
            d.line((8,y+4,w-10,y+4),fill=12)
            d.point((5,y+4),fill=5);d.point((w-6,y+4),fill=5)
        for x in (1,w-2):d.line((x,0,x,h-1),fill=12,width=2)
    elif style==3:
        d.rectangle((3,0,w-4,h-1),fill=4)
        d.rectangle((5,0,w-6,h-1),fill=3)
        for y in range(0,h,16):
            d.line((4,y,w-5,y),fill=2)
            d.line((5,y+1,w-6,y+1),fill=5)
            d.line((w//2,y+3,w//2,y+11),fill=2)
        d.line((1,0,1,h-1),fill=13);d.line((w-2,0,w-2,h-1),fill=12)
    elif style==4:
        for y in range(0,h,8):
            d.polygon([(3,y+1),(w-5,y),(w-3,y+6),(16,y+7),(13,y+6),(3,y+7)],fill=12)
            d.line((5,y+1,w-7,y+1),fill=13)
            d.line([(w-10,y+3),(w-12,y+4),(w-10,y+6)],fill=2)
        d.line((1,0,1,h-1),fill=13);d.line((w-2,0,w-2,h-1),fill=12)
        d.polygon([(4,0),(7,0),(6,10),(4,7)],fill=9)
    else:
        d.rectangle((3,0,w-4,h-1),fill=5)
        for y in range(0,h,8):
            d.rectangle((7,y+2,w-8,y+5),fill=2)
            d.line((7,y+1,w-8,y+1),fill=6)
        d.line((2,0,2,h-1),fill=14);d.line((w-3,0,w-3,h-1),fill=12,width=2)
        for y in range(3,h,16):d.point((3,y),fill=15)
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


def _outfall_shape(d,box,style,ink):
    x0,y0,x1,y1=box;w=x1-x0;cx=(x0+x1)//2
    if style==1 or style==4:
        radius=min(w//2,(y1-y0)*2//3)
        d.pieslice((x0,y0,x1,y0+2*radius),180,360,fill=ink)
        d.rectangle((x0,y0+radius,x1,y1),fill=ink)
    elif style==2:
        d.ellipse(box,fill=ink)
    elif style==3:
        d.polygon([(cx,y0),(cx+w//4,y0+7),(x1-3,y0+23),
                   (x1,y0+35),(x1,y1),(x0,y1),(x0,y0+35),
                   (x0+3,y0+23),(cx-w//4,y0+7)],fill=ink)
    else:
        cut=max(4,w//7)
        d.polygon([(x0+cut,y0),(x1-cut,y0),(x1,y0+cut),
                   (x1,y1),(x0,y1),(x0,y0+cut)],fill=ink)


def _grand_outfall(g,style,phase):
    """A recessed mouth and asymmetric gold planes, not nested bevel rings."""
    d=ImageDraw.Draw(g)
    outer,om=_new(480,320);inner,im=_new(480,320)
    box=(208,16,271,86)
    _outfall_shape(om,box,style,1)
    _outfall_shape(im,(218,26,261,86),style,1)
    # One broad lit mass, a shadowed right return and true cavity shadow.
    for y in range(16,87):
        for x in range(208,272):
            if not outer.getpixel((x,y)):continue
            if inner.getpixel((x,y)):
                d.point((x,y),fill=1)
                continue
            ink=13
            if x>=259 or y>79:ink=12
            if x<238 and y<36 or x<214 and y<77:ink=14
            if x in (208,271) or y==86:ink=12
            d.point((x,y),fill=ink)
    # Short upper-left speculars and facet breaks give cylindrical metal a
    # different light response from matte bricks or cloth.
    for x,y in ((218,25),(219,24),(220,23),(221,22),(222,21)):
        if outer.getpixel((x,y)) and not inner.getpixel((x,y)):d.point((x,y),fill=15)
    for x in range(222,260,8 if style!=2 else 9):
        for y in range(27,85):
            if not inner.getpixel((x,y)):continue
            d.point((x,y),fill=14 if style!=4 else 13)
            if inner.getpixel((x+1,y)):d.point((x+1,y),fill=12)
    for y in (46,63):
        for x in range(219,261):
            if inner.getpixel((x,y)):
                d.point((x,y),fill=13)
                d.point((x,y+1),fill=12)
    if style==1:
        d.polygon([(234,18),(243,18),(241,29),(236,27)],fill=14)
        d.line((235,18,242,18),fill=15)
        d.line((211,46,211,58),fill=15)
        d.line((265,49,265,76),fill=12,width=3)
    elif style==2:
        for x,y in ((218,29),(263,36),(211,57),(264,66)):
            d.ellipse((x-2,y-2,x+2,y+2),fill=12)
            d.point((x-1,y-1),fill=14)
        d.line((211,42,211,49),fill=15)
    elif style==3:
        d.line([(219,32),(229,24),(239,19)],fill=15)
        d.line((211,53,211,74),fill=14)
        d.line((266,50,266,77),fill=12,width=2)
    elif style==4:
        d.polygon([(263,37),(267,41),(264,47),(267,51),(263,56)],fill=1)
        d.polygon([(209,61),(215,63),(214,69),(211,67),(210,76),(208,72)],fill=9)
        d.line((210,62,212,66),fill=10)
        d.line((217,27,222,23),fill=15)
    else:
        d.rectangle((219,18,259,22),fill=13)
        d.polygon([(219,18),(253,18),(249,20),(219,20)],fill=14)
        d.line((220,18,232,18),fill=15)
        d.rectangle((210,37,215,81),fill=13)
        d.line((211,38,211,64),fill=14)
        d.rectangle((264,37,269,81),fill=12)


def _basin(g,style,phase,period):
    d=ImageDraw.Draw(g)
    # Lip, liquid plane and thick near face, all inside the old blocked basin.
    d.ellipse((192,63,287,104),fill=12)
    d.ellipse((193,63,286,100),fill=13)
    d.ellipse((198,66,281,96),fill=8)
    d.arc((193,63,286,100),180,292,fill=14,width=2)
    d.arc((194,65,285,101),10,170,fill=12,width=3)
    d.line((207,68,220,66),fill=15)
    mask,md=_new(480,320);md.ellipse((199,67,280,96),fill=1)
    waves=water_tile(style,phase,1,period)
    for y in range(67,97):
        for x in range(199,281):
            ink=waves.getpixel((x%16,y%16))
            if mask.getpixel((x,y)) and ink!=8:d.point((x,y),fill=ink)
    # Two falling curtains have irregular side profiles and a clear dark gap
    # between them; a single straight mass would read as a green column.
    d.polygon([(230,38),(236,38),(235,55),(237,68),(233,84),
               (228,88),(227,85),(232,68),(231,57)],fill=9)
    d.polygon([(242,43),(247,43),(246,58),(247,72),(244,82),
               (248,88),(244,90),(240,83),(243,68)],fill=9)
    d.line([(231,40),(232,55),(233,67),(230,82)],fill=10,width=2)
    d.line([(244,46),(244,59),(245,70),(242,81)],fill=10)
    shift=(phase*48//max(1,period))%48
    for x,start in ((232,1),(244,18)):
        for y in range(40,84):
            if ((y-29-start-shift)%48)<8:d.line((x,y,x+1,y),fill=11)
    d.line([(220,88),(226,86),(232,89),(239,87),(247,90),(254,88)],fill=10)
    d.line([(226,93),(235,95),(247,93),(253,91)],fill=10)
    d.line((231,91,235,91),fill=11)
    d.line([(223,86),(222,83),(220,82)],fill=11)
    d.line([(250,86),(251,82),(253,81)],fill=10)


def _pipe(d,box,style=1,horizontal=False):
    x0,y0,x1,y1=box
    # Cylinder: a broad warm face, a narrow lit shoulder and cool dark return.
    # Collars cast a short local shadow, rather than outlining the full pipe.
    d.rectangle(box,fill=12)
    if horizontal:
        d.rectangle((x0+1,y0+1,x1-1,y1-2),fill=13)
        d.rectangle((x0+2,y0+1,x1-2,y0+2),fill=14)
        for x in range(x0+12,x1-2,26 if style!=2 else 22):
            d.rectangle((x+1,y0-1,x+5,y1+2),fill=12)
            d.rectangle((x-1,y0-2,x+2,y1+1),fill=13)
            d.line((x-1,y0-2,x+2,y0-2),fill=14)
        d.line((x0+4,y0+1,min(x0+13,x1-2),y0+1),fill=15)
    else:
        d.rectangle((x0+1,y0+1,x1-2,y1-1),fill=13)
        d.line((x0+1,y0+2,x0+1,y1-2),fill=14,width=2)
        for y in range(y0+8,y1-2,22):
            d.rectangle((x0-1,y+1,x1+2,y+5),fill=12)
            d.rectangle((x0-2,y-1,x1+1,y+2),fill=13)
            d.line((x0-2,y-1,x1,y-1),fill=14)
        d.line((x0+1,y0+3,x0+1,min(y0+10,y1-2)),fill=15)
    if style==4:
        d.line((x1-2,y0+5,x1-2,min(y1-2,y0+12)),fill=9)
    elif style==2:
        if horizontal:d.ellipse((x0+3,y0-1,x0+7,y1+1),fill=13)
        else:d.ellipse((x0-1,y0+3,x1+1,y0+7),fill=13)
    elif style==3:
        if horizontal:d.line((x0+3,y0+2,x1-3,y0+2),fill=15)
        else:d.line((x0+2,y0+3,x0+2,y1-3),fill=15)
    elif style==5:
        if horizontal:
            for x in range(x0+8,x1-2,16):d.point((x,y0+4),fill=15)
        else:
            for y in range(y0+6,y1-2,12):d.point((x0+4,y),fill=15)


def _ladder(g,o,style=1):
    d=ImageDraw.Draw(g);od=ImageDraw.Draw(o)
    # The 16px ladder lane is held at x144..159, the actual forest exit.
    _arch(d,(132,16,171,63),style,True,False)
    d.rectangle((144,29,159,63),fill=1)
    left,right=(146,157) if style!=2 else (145,158)
    for x in (left,right):
        d.line((x,30,x,63),fill=12,width=2)
        d.line((x-1,31,x-1,62),fill=14)
    gap=5 if style in (1,3) else 6
    for y in range(32,63,gap):
        d.line((left+1,y,right-1,y),fill=15 if style==3 else 14,width=2 if style==2 else 1)
        d.point((left+2,y),fill=15)
        if style==4:d.point((151,y),fill=12)
        elif style==5:
            d.line((left+1,y+1,right-1,y+1),fill=12)
            d.point((right-2,y),fill=15)
    if style in (1,5):
        d.polygon([(147,23),(151,19),(155,23),(153,27),(149,27)],fill=14)
        d.point((151,21),fill=15)
    elif style==2:
        d.line([(150,26),(150,21),(147,24)],fill=15)
        d.line([(150,21),(153,24)],fill=15)
    elif style==3:d.line([(147,25),(151,20),(155,25)],fill=15)
    else:
        d.line([(146,24),(151,20),(155,24)],fill=14)
        d.line((151,20,151,27),fill=15)
    d.line((144,63,159,63),fill=15)
    # Only the original six overlay cells can cover Bloom, with a clear lane.
    for y in range(16,48):
        for x in range(128,176):
            v=g.getpixel((x,y))
            if v and (x<144 or x>159 or y<29):o.putpixel((x,y),v)


def _market(g,o,style=1,phase=0):
    d=ImageDraw.Draw(g);od=ImageDraw.Draw(o)
    # The shop reads as cloth, a dark recess and a solid wooden counter.
    # Its broad planes are quieter than the frog's contrasting eye/jaw mass.
    d.rectangle((18,66,125,107),fill=12)
    d.rectangle((23,72,120,92),fill=2)
    d.rectangle((20,67,23,108),fill=13)
    d.rectangle((121,67,124,108),fill=12)
    d.line((20,67,22,67),fill=14)
    if style==1:
        d.polygon([(16,57),(127,57),(124,77),(105,79),(88,77),(72,80),(53,77),(35,79),(16,77)],fill=9)
        d.polygon([(17,58),(125,58),(117,62),(26,62)],fill=10)
        for x in (35,72,109):d.polygon([(x,60),(x+3,61),(x+7,77),(x+3,78)],fill=8)
        d.line((18,56,125,56),fill=13)
    elif style==2:
        d.polygon([(16,59),(42,56),(76,58),(103,56),(127,60),(125,74),(117,80),(102,80),(92,75),(80,81),(64,80),(54,75),(43,80),(27,80),(17,74)],fill=9)
        d.polygon([(18,60),(43,57),(73,60),(68,64),(35,62)],fill=10)
        d.rectangle((96,61,110,68),fill=4)
        d.line((98,63,104,63),fill=3)
        d.line((96,67,100,67),fill=3)
    elif style==3:
        d.polygon([(16,57),(127,57),(122,77),(83,76),(72,80),(59,76),(20,77)],fill=9)
        d.polygon([(18,58),(125,58),(118,61),(25,61)],fill=10)
        d.polygon([(37,61),(39,61),(47,76),(44,77)],fill=8)
        d.polygon([(103,60),(105,60),(100,77),(97,77)],fill=8)
        d.line((18,57,124,57),fill=13)
    elif style==4:
        d.polygon([(16,61),(40,58),(69,60),(97,57),(127,60),(125,76),(113,75),(106,81),(98,76),(85,79),(77,75),(64,81),(56,76),(39,80),(35,76),(17,78)],fill=9)
        d.polygon([(17,62),(41,59),(69,61),(65,64),(28,64)],fill=10)
        d.polygon([(79,60),(84,61),(89,76),(83,77)],fill=8)
        d.line((38,62,36,74),fill=8)
        d.line((116,62,118,73),fill=8)
    else:
        d.polygon([(16,57),(127,57),(125,76),(114,79),(29,79),(18,76)],fill=9)
        d.polygon([(18,58),(125,58),(116,62),(27,62)],fill=10)
        d.rectangle((17,56,126,58),fill=12)
        d.line((18,56,43,56),fill=14)
        for x in (38,101):d.polygon([(x,62),(x+4,62),(x+1,77),(x-2,77)],fill=8)
        d.polygon([(17,74),(22,75),(29,79),(25,79),(18,77)],fill=13)
    # Two jars, a tied seed sack and a dull coin dish remain within the counter.
    for x,y in ((36,84),(100,83)):
        body=10 if style in (1,2) else 9
        if style==2:
            shape=[(x-4,y-2),(x-2,y-5),(x+2,y-5),(x+4,y-2),(x+3,y+5),(x-3,y+5)]
        elif style==4:shape=[(x-4,y-2),(x+3,y-3),(x+4,y+2),(x+1,y+5),(x-3,y+4)]
        else:shape=[(x-3,y-3),(x-2,y-5),(x+2,y-5),(x+3,y-3),(x+3,y+5),(x-3,y+5)]
        d.polygon(shape,fill=2)
        d.polygon([(x-2,y-2),(x+1,y-3),(x+2,y+3),(x-2,y+3)],fill=body)
        d.line((x-2,y-4,x+2,y-4),fill=13)
        d.line((x-1,y-2,x-1,y+1),fill=11)
    d.ellipse((82,84,93,89),fill=12);d.line((84,84,90,84),fill=13)
    d.polygon([(52,88),(54,83),(57,81),(61,83),(64,88),(61,91),(54,91)],fill=12)
    d.polygon([(54,85),(57,83),(60,84),(61,87),(55,88)],fill=13)
    d.line((56,82,60,82),fill=2)
    # Top surface, near face and cast shadow have different values. A single
    # foreground face occludes the frog's legs, matching its established mask.
    d.rectangle((25,91,111,108),fill=12)
    d.polygon([(25,91),(111,91),(109,94),(27,94)],fill=13)
    d.line((27,91,60,91),fill=14)
    od.rectangle((32,94,111,106),fill=12)
    od.line((32,94,111,94),fill=13)
    od.line((33,106,110,106),fill=2)
    if style==1:
        for x in (48,80):od.line((x,97,x,104),fill=13)
        od.rectangle((33,101,110,102),fill=13)
    elif style==2:
        for x in (40,64,88):od.polygon([(x,97),(x+8,101),(x+7,103),(x-1,99)],fill=13)
        od.line((35,95,58,95),fill=14)
    elif style==3:
        od.line((33,98,110,98),fill=13)
        for x in (52,91):od.line((x,100,x,104),fill=2)
    elif style==4:
        od.polygon([(34,99),(46,98),(52,103),(42,105)],fill=9)
        od.line([(88,96),(85,99),(88,103)],fill=2)
    else:
        od.rectangle((36,97,107,104),outline=13)
        od.line((71,98,71,103),fill=2)

def _sanctum(g,style=1,phase=0):
    d=ImageDraw.Draw(g)
    # A cloth plane lies ON the floor: no black pit-like outline around it.
    d.rectangle((307,75,380,110),fill=2)
    if style==2:
        d.rounded_rectangle((305,72,380,107),radius=6,fill=9)
        d.rounded_rectangle((308,75,377,104),radius=4,outline=10)
        d.ellipse((330,81,356,99),outline=10)
    elif style==4:
        d.polygon([(305,72),(380,74),(378,106),(365,107),(361,105),(348,108),(337,106),(307,107)],fill=9)
        d.line([(309,76),(376,78),(373,102),(312,102)],fill=10)
        d.polygon([(313,74),(324,75),(322,80),(316,81)],fill=8)
    else:
        d.rectangle((305,72,380,107),fill=9 if style!=3 else 8)
        d.rectangle((308,75,377,104),outline=10)
        if style==1:
            d.polygon([(343,81),(351,90),(343,99),(335,90)],fill=10)
            d.line((312,77,331,77),fill=13)
        elif style==3:
            d.line((312,78,372,78),fill=9)
            d.line((313,100,371,100),fill=9)
            d.polygon([(343,82),(350,90),(343,98),(336,90)],outline=10)
        else:
            d.rectangle((310,77,375,102),outline=13)
            d.polygon([(343,83),(349,90),(343,97),(337,90)],fill=10)
    if style in (2,4):
        for x in range(311,377,9):d.line((x,108,x-1,110),fill=9)
    # Candle shelf is matte wood; its shadow does not compete with the flame.
    d.rectangle((288,62,382,69),fill=12)
    d.polygon([(288,62),(382,62),(379,65),(290,65)],fill=13)
    d.line((289,69,380,69),fill=2)
    for x in (299,310,363,374):
        d.line((x,54,x,61),fill=7,width=2)
        d.line((x+1,55,x+1,61),fill=5)
        d.polygon([(x-2,54),(x-1,51),(x+phase%2,49),(x+2,53),(x+1,55)],fill=14)
        d.point((x,52),fill=15)

def _crate(d,x,y,style=1,w=22,h=28):
    # A real shallow top and dark right return distinguish wood from a gilt UI
    # rectangle. Bright edges are not painted around every crate perimeter.
    d.polygon([(x,y+4),(x+w-4,y),(x+w,y+3),(x+w,y+h),(x+3,y+h),(x,y+h-3)],fill=12)
    d.polygon([(x+1,y+4),(x+w-5,y+1),(x+w-1,y+4),(x+4,y+7)],fill=13)
    d.polygon([(x+3,y+8),(x+w-5,y+5),(x+w-5,y+h-1),(x+3,y+h-1)],fill=13)
    d.line((x+w-4,y+6,x+w-4,y+h-1),fill=2)
    for xx in (x+8,x+14):d.line((xx,y+8,xx,y+h-2),fill=12)
    if style==1:
        for yy in (y+11,y+h-6):d.line((x+3,yy,x+w-5,yy-2),fill=5,width=2)
    elif style==2:
        d.line((x+4,y+11,x+w-6,y+h-5),fill=12,width=3)
        d.line((x+w-6,y+9,x+4,y+h-4),fill=12,width=3)
    elif style==3:
        d.line((x+5,y+12,x+11,y+11),fill=14)
        d.line((x+5,y+h-7,x+12,y+h-8),fill=12)
    elif style==4:
        d.line([(x+10,y+8),(x+8,y+14),(x+10,y+20),(x+8,y+h-1)],fill=2)
        d.polygon([(x+2,y+h-9),(x+8,y+h-8),(x+7,y+h-2),(x+3,y+h-1)],fill=9)
    else:
        d.line((x+4,y+10,x+w-6,y+7),fill=5,width=2)
        d.line((x+4,y+h-4,x+w-6,y+h-6),fill=5,width=2)
        d.rectangle((x+9,y+13,x+12,y+17),fill=12)
    d.line((x+2,y+4,x+w-6,y+1),fill=14)


def _barrel(d,x,y,style=1):
    d.ellipse((x,y,x+18,y+24),fill=12)
    d.rectangle((x+2,y+6,x+16,y+19),fill=12)
    d.polygon([(x+3,y+5),(x+10,y+4),(x+11,y+22),(x+4,y+21)],fill=13)
    d.ellipse((x+1,y,x+17,y+8),fill=5)
    d.ellipse((x+3,y+1,x+15,y+6),fill=12)
    d.arc((x+1,y,x+17,y+8),180,300,fill=6)
    for yy in (y+9,y+18):
        d.arc((x+1,yy-3,x+17,yy+4),0,180,fill=5,width=2)
        d.line((x+2,yy-1,x+6,yy),fill=6)
    d.line((x+8,y+9,x+8,y+17),fill=12)
    if style==4:d.polygon([(x+1,y+19),(x+7,y+20),(x+6,y+24),(x+3,y+23)],fill=9)

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
    x0,y0,x1,y1=box
    # Ground-facing frame: a lit back/left lip and a deep near-side return.
    # Bars stay plainly visible, so the opening never reads as an unguarded pit.
    if style==2:
        d.rounded_rectangle(box,radius=5,fill=12)
        d.rounded_rectangle((x0+2,y0+1,x1-2,y1-2),radius=4,fill=13)
        d.rounded_rectangle((x0+5,y0+4,x1-5,y1-5),radius=2,fill=1)
    elif style==5:
        d.polygon([(x0+4,y0),(x1-4,y0),(x1,y0+4),(x1,y1-3),(x1-3,y1),(x0+3,y1),(x0,y1-3),(x0,y0+4)],fill=12)
        d.rectangle((x0+2,y0+2,x1-2,y1-3),fill=13)
        d.rectangle((x0+5,y0+5,x1-5,y1-6),fill=1)
    else:
        d.ellipse(box,fill=12)
        d.ellipse((x0+2,y0+1,x1-2,y1-3),fill=13 if style!=3 else 4)
        d.ellipse((x0+6,y0+4,x1-6,y1-6),fill=1)
    small=x1-x0<24
    for x in range(x0+(3 if small else 10),x1-(2 if small else 7),3 if small else (8 if style!=2 else 10)):
        d.line((x,y0+(3 if small else 6),x,y1-(3 if small else 7)),fill=5,width=1 if small else 2)
        if not small:d.line((x-1,y0+6,x-1,y1-8),fill=6)
    if small:d.line((x0+3,(y0+y1)//2,x1-3,(y0+y1)//2),fill=4)
    else:d.line((x0+7,y0+11,x1-7,y0+11),fill=4)
    d.arc((x0+2,y0+1,x1-2,y1-3),190,280,fill=14,width=2)
    d.arc((x0+2,y0+1,x1-2,y1-2),15,155,fill=12,width=2)
    if style==4:d.polygon([(x0+3,y1-9),(x0+13,y1-8),(x0+10,y1-3),(x0+5,y1-2)],fill=9)

def _rails(g,o,style=1):
    d=ImageDraw.Draw(g);od=ImageDraw.Draw(o)
    # North channel bank. Only the original alternating post overlay cells
    # cover the player; the continuous lower rails live below their feet.
    for x in range(16,464,32):
        if 224<=x<256:continue
        d.line((x+7,142,x+7,150),fill=12,width=3)
        if style==2:
            od.rectangle((x+5,132,x+9,143),fill=1)
            od.rectangle((x+6,133,x+8,142),fill=13)
            od.ellipse((x+4,130,x+10,135),fill=14)
            od.point((x+5,131),fill=14)
        elif style==3:
            od.line((x+7,132,x+7,143),fill=1,width=3)
            od.line((x+6,133,x+6,142),fill=7)
            od.rectangle((x+5,131,x+9,133),fill=14)
        elif style==4:
            od.line((x+7,132,x+7,143),fill=1,width=3)
            od.line([(x+6,133),(x+7,136),(x+6,142)],fill=13)
            od.point((x+6,132),fill=14)
        elif style==5:
            od.rectangle((x+5,131,x+9,134),fill=13)
            od.line((x+5,131,x+9,131),fill=14)
            od.line((x+7,135,x+7,143),fill=14)
        else:
            od.rectangle((x+6,132,x+8,143),fill=1)
            od.line((x+7,133,x+7,142),fill=14)
            od.polygon([(x+5,133),(x+7,130),(x+9,133)],fill=13)
            od.point((x+7,131),fill=14)
    for x0,x1 in ((16,223),(256,463)):
        d.line((x0,145,x1,145),fill=12,width=3)
        d.line((x0,144,x1,144),fill=13)
        if style in (2,4):d.line((x0,148,x1,148),fill=12)
    # Near edge, same authored 27 foreground tiles, readable waist-high rail.
    for x in range(16,448,16):
        od.line((x+1,260,x+1,271),fill=1,width=3)
        od.line((x+1,261,x+1,270),fill=13 if style==4 else 14)
        od.line((x,267,x+15,267),fill=12)
        od.line((x,266,x+15,266),fill=13)
        if style==2:od.rectangle((x,259,x+2,262),fill=14)
        elif style==3:od.point((x+1,260),fill=15)
        elif style==5:od.line((x+7,267,x+7,271),fill=13)


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
    _pipe(d,(431,116,443,141),s['metal'])
    d.ellipse((427,134,448,146),fill=1)
    d.ellipse((429,135,446,145),fill=13)
    d.ellipse((433,137,442,142),fill=1)
    d.polygon([(434,141),(441,141),(442,162),(447,169),(445,175),(431,175),(428,170),(433,163)],fill=9)
    d.line([(436,143),(435,161),(432,169)],fill=11)
    d.line((439,145+phase%5,439,151+phase%5),fill=10)
    _grate(d,(207,225,273,255),s['metal'])
    # Deliberate visual debris clusters: broken crockery, bones, rags and slime.
    # They sit away from the clear bridge and exit approaches.
    for x,y in ((139,101),(320,122),(88,228),(322,228),(389,246),(49,223)):
        _slime(d,x,y,22,8,s['props'])
    # Broad attached grease deposits have subdued contrast. The handful of
    # recognizable debris pieces are authored only in DEBRIS_SITES, never
    # sprinkled as bright false-pickup icons across the traversable floor.
    for x,y,w,h in ((27,43,26,16),(85,43,30,16),(425,60,24,18),
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
    if y<4:return wall_tile(styles['masonry'],n)
    if all(xx in (14,15) and 9<=yy<=12 for _,xx,yy in ps):
        return _bridge(styles['bridge']).crop((0 if x==14 else 16,0,16 if x==14 else 32,16))
    if TILES[name]['coll']==0:return floor_tile(styles['floor'],n)
    im,d=_new(fill=3)
    if y in (10,11,18,19):return water_tile(styles['water'],phase,n%4,TILES[name]['frames'])
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
