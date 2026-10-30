"""Five authored, native-resolution Drain material studies.

Only the fixed map identifiers and occurrence positions come from the room
contract. Every pixel here is drawn at its final GBA size, with one sixteen
ink bank. Equal material roles let the review builds mix individual parts.
This module is opt-in; it does not replace the released Drain painter.
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
 1:['#000000','#101818','#202828','#384040','#505858','#687068','#889088','#b0b0a0',
    '#182828','#284838','#486048','#789068','#604020','#a07828','#e8b848','#f8e8b0'],
 2:['#000000','#181820','#282830','#404040','#585858','#707068','#989888','#c0b8a0',
    '#182828','#285040','#487858','#80a070','#684020','#a87028','#f0b840','#f8e8b0'],
 3:['#000000','#101820','#202830','#384048','#505860','#687880','#90a0a0','#b8c8c0',
    '#102830','#184840','#306858','#689880','#504028','#887038','#d8b868','#f8f0c8'],
 4:['#000000','#181818','#282828','#404038','#585850','#787868','#989880','#c0c0a0',
    '#202820','#384830','#586040','#889060','#584020','#907028','#d8a838','#f8e0a0'],
 5:['#000000','#101820','#202830','#384048','#505858','#708078','#98a098','#c0c8b8',
    '#182828','#284838','#487060','#80a080','#604020','#a07830','#f0c858','#f8f0c8']}


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
        d.line((0,2,15,2),fill=10);d.line((0,3,15,3),fill=8)
        d.line((0,4,15,4),fill=7)
    elif style==2:
        d.line((0,2,15,2),fill=11);d.line((0,3,15,3),fill=9)
        d.line((0,4,15,4),fill=7)
        d.rectangle((6,1,9,5),fill=8);d.line((6,1,9,1),fill=10)
    elif style==3:
        d.line((0,2,15,2),fill=11);d.line((0,3,15,3),fill=8)
        d.point((7,2),fill=12)
    elif style==4:
        d.line((0,2,15,2),fill=9);d.line((0,3,15,3),fill=7)
        d.rectangle((5,1,8,4),fill=8);d.point((5,1),fill=10)
        d.line((9,2,11,2),fill=8)
    else:
        d.line((0,2,15,2),fill=10);d.line((0,3,15,3),fill=8)
        d.line((0,4,15,4),fill=7)
        d.rectangle((6,1,9,5),fill=9);d.point((7,1),fill=12)
        d.line((6,5,9,5),fill=8)
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
    if style==2:
        d.ellipse((x,y,x+w,y+h),fill=9)
        d.ellipse((x+min(3,w//3),y,x+max(w//2,w-4),y+max(1,h-2)),fill=10)
        d.line((x+5,y+1,x+9,y+1),fill=11)
    else:
        d.polygon([(x,y+1),(x+w//4,y),(x+w-3,y+2),(x+w,y+h//2),
                   (x+w-5,y+h),(x+w//2,y+h-2),(x+3,y+h),(x,y+h//2)],fill=9)
        d.line([(x+3,y+2),(x+w//3,y+1),(x+w//2,y+3)],fill=10)
        if style in (3,5):d.line((x+5,y+2,x+9,y+2),fill=11)


def floor_tile(style=1,variant=0):
    """Quiet gray masonry, with connected two-to-four-pixel grime clusters."""
    im,d=_new(fill=3)
    if style==1:
        # Wide dressed flags, staggered at half a tile.
        for y,x in ((0,4),(8,12)):
            d.line((0,y,15,y),fill=2)
            d.line((x,y+1,x,min(15,y+7)),fill=2)
            d.line((x+1,y+1,min(15,x+6),y+1),fill=4)
            if x>3:d.line((1,y+1,x-2,y+1),fill=4)
    elif style==2:
        # Rounded cartoon cobbles, broad lit face and shallow dark mortar.
        for y in (0,8):
            split=9 if y==0 else 5
            for x0,x1 in ((-2,split),(split,18)):
                d.rounded_rectangle((x0+1,y+1,x1-1,y+7),radius=2,fill=4)
                d.line((max(0,x0+3),y+1,min(15,x1-3),y+1),fill=5)
                d.line((max(0,x0+2),y+7,min(15,x1-2),y+7),fill=2)
    elif style==3:
        for y in (0,8):
            d.line((0,y,15,y),fill=2)
            split=11 if y==0 else 3
            d.line((split,y+1,split,y+7),fill=2)
            d.line((0,y+1,15,y+1),fill=4)
        if variant%3==0:d.line((3,12,8,12),fill=5)
    elif style==4:
        for y in (0,8):
            split=(3 if y==0 else 11)
            d.line((0,y,15,y),fill=2)
            d.line((split,y+1,split,y+7),fill=2)
            d.line((split+1,y+1,min(15,split+5),y+1),fill=4)
        if variant%3==1:d.line([(12,1),(10,4),(12,6),(10,7)],fill=2)
    else:
        # Thin bonded brick courses with a restrained damp specular edge.
        for y in (0,8):
            d.line((0,y,15,y),fill=2)
            split=7 if y==0 else 15
            d.line((split,y+1,split,y+7),fill=2)
            d.line((0,y+1,5,y+1),fill=4)
        d.line((10,9,14,9),fill=5)
    if variant%7 in (2,5):
        _slime(d,1 if variant%2 else 8,10,6,4,style)
    elif variant%11==4:
        d.line([(4,4),(6,5),(5,7),(7,9)],fill=2)
    return im


def wall_tile(style=1,variant=0):
    im,d=_new(fill=2)
    h=8 if style in (1,3,5) else 8
    for y in range(0,16,h):
        split=(8 if y==0 else 0) if style!=2 else (6 if y==0 else 14)
        d.rectangle((0,y+1,15,y+6),fill=3 if style!=2 else 4)
        d.line((0,y,15,y),fill=5 if style in (1,5) else 4)
        d.line((split,y+1,split,y+6),fill=1)
        if style==2:
            d.point((max(0,split-1),y+1),fill=3)
            d.point((min(15,split+1),y+6),fill=3)
        elif style==4:
            d.line([(12,y+1),(10,y+3),(11,y+5)],fill=2)
        if style in (1,3,5):d.point((min(15,split+2),y+1),fill=6)
        if style==5:
            d.line((0,y+1,15,y+1),fill=4)
            d.line((1,y+6,5,y+6),fill=2)
    if variant%5==2:
        d.polygon([(0,0),(6,0),(5,3),(3,2),(2,8),(0,5)],fill=9)
        d.point((1,2),fill=10)
    return im


def water_tile(style=1,phase=0,variant=0,period=8):
    im,d=_new(fill=8)
    shift=(int(phase)*16//max(1,int(period)))%16
    # The reflection travels downstream instead of alternating random pixels.
    length={1:7,2:5,3:9,4:4,5:8}[style]
    for y,start in ((3,2),(10,10)):
        x=(start+shift+variant*3)%16
        for xx in range(x,x+length):d.point((xx%16,y),fill=9)
        if style in (2,4):d.point(((x+length)%16,y+1),fill=10)
        else:
            for xx in range(x+2,x+length-2):d.point((xx%16,y+1),fill=10)
    if variant%4==1:
        x=(11+shift)%16;d.arc((x-2,11,x+2,14),0,180,fill=10)
    if style==3 and variant%3==0:d.line((2,6,5,6),fill=11)
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
    im,d=_new(fill=3)
    if side=='n':
        d.rectangle((0,0,15,6),fill=4)
        d.line((0,0,15,0),fill=14,width=2)
        d.line((0,2,15,2),fill=12)
        d.line((0,7,15,7),fill=1)
        d.rectangle((0,8,15,15),fill=8)
        if style==1:
            d.line((7,3,7,6),fill=2);d.line((0,3,5,3),fill=6)
        elif style==2:
            d.line((0,1,15,1),fill=15)
            d.ellipse((3,3,11,8),fill=3);d.line((5,4,9,4),fill=5)
        elif style==3:
            d.line((0,3,15,3),fill=7)
            d.line((0,5,15,5),fill=2);d.point((variant%13+1,6),fill=5)
        elif style==4:
            d.line([(4,3),(7,4),(5,6)],fill=2)
            d.polygon([(10,5),(15,5),(14,9),(12,7),(11,11)],fill=9)
        else:
            d.line((0,3,15,3),fill=6)
            d.point((4,4),fill=13);d.point((12,4),fill=13)
            d.line((8,5,8,6),fill=2)
    elif side=='s':
        d.line((0,0,15,0),fill=6)
        d.line((0,1,15,1),fill=4)
        if style==1:
            d.line((7,3,7,15),fill=2);d.line((1,2,6,2),fill=5)
        elif style==2:
            d.rounded_rectangle((1,2,14,14),radius=3,fill=4)
            d.line((3,3,11,3),fill=6);d.line((2,14,13,14),fill=2)
        elif style==3:
            d.line((0,4,15,4),fill=2)
            d.line((3,5,3,15),fill=2);d.line((4,6,11,6),fill=4)
        elif style==4:
            d.line([(12,2),(8,6),(10,9),(7,14)],fill=2)
            d.line((2,2,5,2),fill=5)
        else:
            d.line((0,4,15,4),fill=2)
            d.line((8,5,8,15),fill=2);d.line((1,6,6,6),fill=5)
    else:
        im,d=_new(fill=2)
        d.line((0,0,15,0),fill=6);d.line((0,3,15,3),fill=1)
        if style==1:
            d.polygon([(2,1),(10,1),(8,8),(6,6),(5,14),(2,8)],fill=9)
            d.line((3,2,4,8),fill=10)
        elif style==2:
            d.rectangle((2,1,10,7),fill=9)
            d.ellipse((2,3,6,12),fill=9);d.ellipse((7,2,10,8),fill=10)
            d.point((3,5),fill=11)
        elif style==3:
            d.line((3,2,3,12),fill=9,width=2)
            d.line((9,2,9,8),fill=10);d.point((3,13),fill=11)
        elif style==4:
            d.polygon([(0,1),(12,1),(11,6),(8,4),(9,10),(6,8),(5,15),(2,10)],fill=9)
            d.line([(2,2),(4,6),(3,9)],fill=10)
        else:
            d.line((0,2,15,2),fill=4)
            d.polygon([(4,3),(11,3),(10,9),(8,7),(7,12),(5,8)],fill=9)
            d.line((5,4,6,8),fill=10)
    return im


def _bridge(style=1,w=32,h=64):
    im,d=_new(w,h,1)
    if style==1:
        for y in range(0,h,8):
            d.rectangle((2,y+1,w-3,y+6),fill=4)
            d.line((3,y+1,w-4,y+1),fill=7)
            d.point((5,y+3),fill=13);d.point((w-6,y+3),fill=13)
        d.line((1,0,1,h-1),fill=13);d.line((w-2,0,w-2,h-1),fill=14)
    elif style==2:
        for y in range(0,h,8):
            d.rectangle((2,y+1,w-3,y+7),fill=12)
            d.line((3,y+1,w-4,y+1),fill=14)
            d.line((6,y+5,w-8,y+5),fill=13)
        for x in (1,w-2):d.line((x,0,x,h-1),fill=14)
    elif style==3:
        d.rectangle((3,0,w-4,h-1),fill=5)
        for y in range(1,h,4):d.line((4,y,w-5,y),fill=2)
        d.line((2,0,2,h-1),fill=14);d.line((w-3,0,w-3,h-1),fill=13)
        for y in range(3,h,16):d.point((4,y),fill=15);d.point((w-5,y),fill=15)
    elif style==4:
        for y in range(0,h,8):
            d.polygon([(2,y),(w-4,y+1),(w-3,y+6),(3,y+7)],fill=12)
            d.line((4,y+1,w-7,y+1),fill=14)
            d.line([(w-10,y+3),(w-8,y+4),(w-12,y+5)],fill=1)
        d.line((1,0,1,h-1),fill=13);d.line((w-2,0,w-2,h-1),fill=13)
    else:
        d.rectangle((2,0,w-3,h-1),fill=4)
        for y in range(0,h,8):
            d.line((3,y,w-4,y),fill=2);d.line((3,y+1,w-4,y+1),fill=6)
        for x in (1,w-2):
            d.line((x,0,x,h-1),fill=13)
            for y in range(2,h,8):d.point((x,y),fill=15)
    return im


def _arch(d,box,style=1,gold=True,bars=True):
    x0,y0,x1,y1=box;w=x1-x0;radius=w//2
    edge=12 if gold else 2;face=13 if gold else 4;lit=14 if gold else 6
    # A true wall opening: vertical jambs, semicircular crown, dark interior.
    d.rounded_rectangle((x0,y0,x1,y1),radius=radius,fill=1)
    d.rounded_rectangle((x0+1,y0+1,x1-1,y1-1),radius=max(1,radius-1),fill=edge)
    d.rounded_rectangle((x0+3,y0+3,x1-3,y1-2),radius=max(1,radius-3),fill=face)
    inset=min(max(2,radius-2),8 if style in (1,4) else 6)
    d.rounded_rectangle((x0+inset,y0+inset,x1-inset,y1),radius=max(1,radius-inset),fill=1)
    d.arc((x0+2,y0+2,x1-2,y0+w-2),180,350,fill=lit,width=2)
    d.line((x0+3,y0+radius,x0+3,y1-2),fill=lit)
    if style==1:
        for t in range(1,6):
            xx=x0+4+t*(w-8)//6;yy=y0+3+abs(t-3)*2
            d.line((xx,yy,xx,yy+5),fill=edge)
        d.polygon([(x0+radius-5,y0),(x0+radius+5,y0),(x0+radius+3,y0+9),(x0+radius-3,y0+9)],fill=lit)
    elif style==2:
        for xx,yy in [(x0+5,y0+radius),(x1-5,y0+radius),(x0+radius,y0+5)]:
            d.ellipse((xx-2,yy-2,xx+2,yy+2),fill=edge);d.point((xx-1,yy-1),fill=15)
    elif style==3:
        d.arc((x0-2,y0-2,x1+2,y0+w+2),180,360,fill=6)
    elif style==4:
        d.line([(x0+6,y0+radius),(x0+5,y0+radius+8),(x0+8,y0+radius+14)],fill=9,width=2)
        d.point((x1-4,y1-6),fill=10)
    else:
        d.line((x0+5,y0+radius,x0+5,y1-3),fill=15)
        d.line((x1-4,y0+radius,x1-4,y1-3),fill=14)
    if bars:
        for x in range(x0+inset+5,x1-inset,10 if style!=2 else 12):
            d.line((x,y0+radius,x,y1-3),fill=4,width=3)
            d.line((x-1,y0+radius+1,x-1,y1-4),fill=6)
        d.line((x0+inset+2,y0+radius+14,x1-inset-2,y0+radius+14),fill=3,width=2)


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
    """An unbroken64pxgoldgrate, confined to the map's unique wall cells.

    Row3cols12and17 are reused plain masonry elsewhere. The aperture sits
    wholly within cols13..16 so its gilded rim is not cut by those aliases.
    Its large basin retains the original broad blocked footprint below.
    """
    d=ImageDraw.Draw(g)
    box=(208,16,271,86)
    for inset,ink in ((0,1),(1,12),(2,14),(4,13),(7,12)):
        x0,y0,x1,y1=box
        _outfall_shape(d,(x0+inset,y0+inset,x1-inset,y1),style,ink)
    mask,md=_new(480,320)
    _outfall_shape(d,(218,26,261,86),style,2)
    _outfall_shape(md,(220,28,259,86),style,1)
    _outfall_shape(d,(220,28,259,86),style,1)
    # A substantial face of real gold rods, including their shaded sides.
    inks={1:((-1,14),(0,13),(1,12)),
          2:((-1,12),(0,14),(1,13),(2,12)),
          3:((0,14),(1,12)),
          4:((-1,13),(0,12),(1,1)),
          5:((-1,14),(0,13),(1,13),(2,12))}[style]
    for x in range(222,259,7 if style!=2 else 9):
        first=None
        for y in range(27,85):
            if mask.getpixel((x,y)):
                if first is None:first=y
                for dx,ink in inks:
                    if mask.getpixel((x+dx,y)):d.point((x+dx,y),fill=ink)
                if style==4 and y%13 in (0,1):d.point((x-1,y),fill=9)
        if first is not None:d.point((x,first+2),fill=15)
    for y in (45,62):
        for yy,ink in ((y,14),(y+1,13),(y+2,12)):
            for x in range(219,261):
                if mask.getpixel((x,yy)):d.point((x,yy),fill=ink)
    if style==1:
        d.polygon([(235,17),(245,17),(243,26),(237,26)],fill=14)
        d.line((237,18,242,18),fill=15)
        d.line((210,48,210,77),fill=15)
        for xx,yy in ((215,32),(222,23),(257,23),(265,32)):
            d.line((xx,yy,xx+2,yy+5),fill=12)
    elif style==2:
        for xx,yy in ((222,23),(256,23),(212,42),(267,42),(214,67),(265,67)):
            d.ellipse((xx-2,yy-2,xx+2,yy+2),fill=12)
            d.point((xx-1,yy-1),fill=15);d.point((xx,yy),fill=14)
    elif style==3:
        d.line([(211,52),(213,42),(225,27),(239,19),(254,28),(267,45)],fill=15)
        d.line((211,55,211,79),fill=14)
        d.polygon([(237,20),(239,17),(242,20),(239,23)],fill=15)
    elif style==4:
        d.line([(218,26),(220,31),(216,37)],fill=1)
        d.line([(265,45),(262,50),(266,57)],fill=1)
        d.polygon([(209,58),(214,59),(215,67),(212,64),(211,75),(208,69)],fill=9)
        d.line((210,59,211,65),fill=10)
    else:
        d.rectangle((220,17,259,20),fill=14)
        d.line((221,17,257,17),fill=15)
        for xx in (226,236,246,256):d.point((xx,20),fill=12)
        d.rectangle((210,36,214,81),fill=13);d.line((211,37,211,80),fill=15)
        d.rectangle((265,36,269,81),fill=12);d.line((266,37,266,80),fill=14)
        for x in range(222,259,7):
            for y in (36,56):
                if mask.getpixel((x,y)):d.point((x,y),fill=15)


def _pipe(d,box,style=1,horizontal=False):
    x0,y0,x1,y1=box
    d.rectangle(box,fill=1)
    if horizontal:
        d.rectangle((x0+1,y0+1,x1-1,y1-1),fill=12)
        d.rectangle((x0+1,y0+1,x1-1,y0+3),fill=14)
        d.line((x0+2,y0+4,x1-2,y0+4),fill=13)
        for x in range(x0+10,x1-2,22 if style!=2 else 16):
            d.rectangle((x,y0-2,x+3,y1+2),fill=12)
            d.line((x,y0-2,x+2,y0-2),fill=15)
    else:
        d.rectangle((x0+1,y0+1,x1-1,y1-1),fill=12)
        d.rectangle((x0+1,y0+1,x0+3,y1-1),fill=14)
        d.line((x0+4,y0+2,x0+4,y1-2),fill=13)
        for y in range(y0+8,y1-2,20):
            d.rectangle((x0-2,y,x1+2,y+3),fill=12)
            d.line((x0-1,y,x1+1,y),fill=14)
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
    # Existing market footprint: left rear wall, counter and canopy.
    d.rectangle((16,65,127,109),fill=1)
    d.rectangle((20,67,123,108),fill=12)
    for x in range(24,124,12):
        d.line((x,70,x,106),fill=13)
        d.line((x+1,71,x+1,104),fill=12)
    if style==1:
        for x in range(16,128,16):
            d.rectangle((x,57,x+15,74),fill=9 if x%32 else 13)
            d.polygon([(x,74),(x+7,80),(x+15,74)],fill=9 if x%32 else 13)
            d.line((x+2,58,x+12,58),fill=14)
        d.line((18,56,125,56),fill=14)
    elif style==2:
        for x in range(16,128,8):
            top=58+(1 if (x//8)%3==0 else 0)
            d.rectangle((x,top,x+7,75),fill=10 if x%16 else 13)
            d.ellipse((x,71,x+7,81),fill=10 if x%16 else 13)
            d.point((x+1,top),fill=14)
    elif style==3:
        d.rectangle((16,57,127,75),fill=9)
        for x in range(17,127,16):
            d.line((x,58,x+10,58),fill=11)
            d.polygon([(x,75),(x+5,80),(x+10,75)],fill=10)
        d.line((17,57,126,57),fill=14)
    elif style==4:
        d.polygon([(16,60),(42,57),(69,59),(96,56),(127,59),(127,76),(111,75),(105,80),(87,75),(75,79),(62,75),(53,81),(38,75),(16,77)],fill=9)
        for x in (28,57,86,114):d.line((x,59,x-2,74),fill=10)
        d.line([(17,59),(43,58),(70,60),(98,57),(125,60)],fill=14)
    else:
        d.rectangle((16,57,127,75),fill=12)
        for x in range(16,128,14):
            d.rectangle((x+2,58,min(127,x+10),75),fill=9)
            d.line((x+3,59,min(127,x+9),59),fill=10)
        d.line((16,56,127,56),fill=14)
        for x in range(19,126,14):d.polygon([(x,75),(x+4,80),(x+8,75)],fill=13)
    # Counter goods deliberately read as jars, wrapped seeds and a coin dish.
    for x,y in ((36,84),(100,83)):
        if style==1:
            d.rectangle((x-3,y-4,x+3,y+5),fill=1)
            d.rectangle((x-2,y-3,x+2,y+4),fill=10)
            d.line((x-2,y-4,x+2,y-4),fill=14);d.point((x-1,y-2),fill=15)
        elif style==2:
            d.ellipse((x-4,y-3,x+4,y+5),fill=1)
            d.ellipse((x-3,y-2,x+3,y+4),fill=10)
            d.line((x-2,y-4,x+2,y-4),fill=14);d.point((x-2,y),fill=15)
        elif style==3:
            d.rectangle((x-2,y-5,x+2,y+5),fill=1)
            d.rectangle((x-1,y-4,x+1,y+4),fill=11)
            d.line((x-2,y-5,x+2,y-5),fill=14);d.point((x-1,y-3),fill=15)
        elif style==4:
            d.polygon([(x-4,y-2),(x+4,y-2),(x+3,y+4),(x-2,y+5)],fill=1)
            d.polygon([(x-3,y-1),(x+3,y-1),(x+2,y+3),(x-1,y+4)],fill=9)
            d.line((x-3,y-2,x+3,y-2),fill=13);d.line((x,y,x+1,y+2),fill=1)
        else:
            d.ellipse((x-4,y-2,x+4,y+5),fill=1)
            d.ellipse((x-3,y-1,x+3,y+4),fill=9)
            d.rectangle((x-2,y-4,x+2,y-2),fill=13)
            d.line((x-2,y+1,x+2,y+1),fill=14);d.point((x-2,y-1),fill=11)
    d.ellipse((81,83,93,89),fill=12);d.line((83,85,90,85),fill=14)
    d.polygon([(52,88),(54,81),(60,80),(64,86),(62,91),(54,91)],fill=12)
    d.line((54,83,59,82),fill=14)
    # The near face uses only authored overlay cells, ending at y106.
    d.rectangle((25,92,111,108),fill=1)
    d.rectangle((26,93,110,106),fill=12)
    d.line((25,92,111,92),fill=14)
    for x in range(33,111,16):d.line((x,95,x,105),fill=13)
    od.rectangle((32,94,111,106),fill=12)
    od.line((32,94,111,94),fill=14)
    od.line((33,105,110,105),fill=13)
    for x in (43,67,91):od.line((x,97,x,104),fill=1)
    if style==2:
        for x in (35,59,83,107):od.point((x,96),fill=15)
    elif style==3:od.line((34,99,109,99),fill=13)
    elif style==4:od.line([(37,95),(41,98),(39,103)],fill=9)
    elif style==5:
        for x in (44,68,92):od.polygon([(x-2,97),(x,95),(x+2,97),(x,100)],fill=14)


def _sanctum(g,style=1,phase=0):
    d=ImageDraw.Draw(g)
    d.rectangle((304,71,382,111),fill=1)
    if style==1:
        d.rectangle((307,74,379,108),fill=9)
        d.rectangle((310,77,376,105),outline=13)
        for x,y in ((314,81),(372,81),(314,101),(372,101)):d.rectangle((x-1,y-1,x+1,y+1),fill=14)
        d.line((319,91,367,91),fill=10)
    elif style==2:
        d.rounded_rectangle((307,74,379,108),radius=5,fill=10)
        d.rounded_rectangle((310,77,376,105),radius=4,outline=13)
        for x in range(315,376,8):d.line((x,109,x,111),fill=12)
        d.ellipse((330,82,354,101),outline=11)
    elif style==3:
        d.rectangle((307,74,379,108),fill=8)
        d.rectangle((310,77,376,105),outline=10)
        d.polygon([(344,79),(359,91),(344,103),(329,91)],outline=13)
        d.ellipse((336,83,351,99),outline=11)
    elif style==4:
        d.polygon([(307,74),(379,76),(377,108),(309,107)],fill=9)
        d.line([(311,78),(375,80),(373,103),(314,103),(311,78)],fill=13)
        d.line([(321,78),(319,83),(321,87)],fill=1)
        d.line([(369,101),(365,98),(366,95)],fill=1)
    else:
        d.rectangle((307,74,379,108),fill=9)
        d.rectangle((309,76,377,106),outline=14)
        d.rectangle((312,79,374,103),outline=10)
        for x in (316,370):d.line((x,81,x,101),fill=13)
        d.polygon([(343,81),(351,91),(343,101),(335,91)],outline=13)
    # Low shelf and candles stay in their original solid/occlusion footprint.
    d.rectangle((288,62,382,68),fill=12)
    d.line((289,62,380,62),fill=14)
    for x in (299,310,363,374):
        d.line((x,54,x,61),fill=7,width=2)
        d.polygon([(x-2,54),(x-1,51),(x+phase%2,49),(x+2,53),(x+1,55)],fill=14)
        d.point((x,52),fill=15)


def _crate(d,x,y,style=1,w=22,h=28):
    d.rectangle((x,y,x+w,y+h),fill=1)
    d.rectangle((x+2,y+2,x+w-2,y+h-2),fill=12)
    if style in (1,5):
        for xx in range(x+5,x+w-1,5):d.line((xx,y+3,xx,y+h-3),fill=13)
        for yy in (y+4,y+h-5):d.line((x+2,yy,x+w-2,yy),fill=14)
        if style==5:
            d.rectangle((x+w//2-2,y+3,x+w//2+2,y+h-3),fill=13)
            d.polygon([(x+w//2-2,y+h//2),(x+w//2,y+h//2-3),(x+w//2+2,y+h//2),(x+w//2,y+h//2+3)],fill=14)
    elif style==2:
        d.line((x+3,y+3,x+w-3,y+h-3),fill=13,width=3)
        d.line((x+w-3,y+3,x+3,y+h-3),fill=13,width=3)
    elif style==3:
        d.rectangle((x+3,y+3,x+w-3,y+h-3),outline=13)
        d.line((x+w//2,y+4,x+w//2,y+h-4),fill=14)
    else:
        d.line((x+3,y+3,x+w-4,y+h-3),fill=13,width=2)
        d.line([(x+8,y+2),(x+6,y+12),(x+8,y+18)],fill=1)
    d.line((x+2,y+2,x+w-3,y+2),fill=14)


def _debris(style=1,variant=0):
    im,d=_new()
    _slime(d,1,8,13,6,style)
    if style==1:
        # A smashed stoneware dish and two dull shards, rather than loot.
        d.polygon([(3,8),(5,4),(10,3),(11,7),(7,10)],fill=5)
        d.line([(5,4),(9,4),(10,6)],fill=7)
        d.polygon([(11,10),(14,9),(13,13)],fill=6)
        d.line((2,12,5,12),fill=4)
    elif style==2:
        # Cartoon fish skeleton: broad backbone, recognisable empty head.
        d.ellipse((2,5,7,10),fill=6);d.point((3,7),fill=1)
        d.line((7,8,12,8),fill=6)
        d.line([(9,5),(9,10),(11,6),(11,10)],fill=6)
        d.polygon([(12,8),(14,5),(14,11)],fill=5)
    elif style==3:
        d.polygon([(3,9),(5,3),(7,8)],fill=6)
        d.line((5,4,5,7),fill=7)
        d.polygon([(8,10),(11,5),(14,9),(11,12)],fill=5)
        d.line((11,6,13,9),fill=7)
        d.point((5,12),fill=4)
    elif style==4:
        d.line((3,6,11,10),fill=6,width=2)
        for x,y in ((3,6),(11,10)):
            d.point((x,y-1),fill=7);d.point((x,y+1),fill=7)
        d.ellipse((9,3,14,7),fill=5)
        d.point((11,5),fill=1);d.point((13,5),fill=1)
    else:
        d.polygon([(2,6),(8,4),(12,6),(13,11),(7,13),(3,10)],fill=5)
        d.polygon([(3,7),(8,5),(11,7),(8,8),(7,12),(5,9)],fill=6)
        d.line([(6,6),(7,8),(6,10)],fill=3)
    if variant%2:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return im


def _grate(d,box,style=1):
    x0,y0,x1,y1=box
    if style in (1,3):
        d.ellipse(box,fill=1);d.ellipse((x0+2,y0+1,x1-2,y1-1),fill=13 if style==1 else 5)
        d.ellipse((x0+6,y0+4,x1-6,y1-4),fill=1)
    elif style==2:
        d.rounded_rectangle(box,radius=5,fill=1)
        d.rounded_rectangle((x0+2,y0+2,x1-2,y1-2),radius=4,fill=13)
        d.rounded_rectangle((x0+5,y0+4,x1-5,y1-4),radius=3,fill=1)
    elif style==4:
        d.ellipse(box,fill=1);d.ellipse((x0+2,y0+2,x1-2,y1-1),fill=12)
        d.ellipse((x0+5,y0+4,x1-5,y1-3),fill=1)
    else:
        d.rectangle(box,fill=1);d.rectangle((x0+2,y0+2,x1-2,y1-2),fill=13)
        d.rectangle((x0+5,y0+4,x1-5,y1-4),fill=1)
    for x in range(x0+10,x1-7,7 if style!=2 else 9):
        d.line((x,y0+6,x,y1-6),fill=5,width=2)
        d.line((x-1,y0+6,x-1,y1-7),fill=7)
    for y in range(y0+10,y1-5,8):d.line((x0+8,y,x1-8,y),fill=3)
    d.arc((x0+2,y0+1,x1-2,y1-1),180,340,fill=14)


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
            od.point((x+5,131),fill=15)
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
            od.line((x+5,131,x+9,131),fill=15)
            od.line((x+7,135,x+7,143),fill=14)
        else:
            od.rectangle((x+6,132,x+8,143),fill=1)
            od.line((x+7,133,x+7,142),fill=14)
            od.polygon([(x+5,133),(x+7,130),(x+9,133)],fill=13)
            od.point((x+7,131),fill=15)
    for x0,x1 in ((16,223),(256,463)):
        d.line((x0,145,x1,145),fill=12,width=3)
        d.line((x0,144,x1,144),fill=14,width=2)
        if style in (2,4):d.line((x0,148,x1,148),fill=12)
    # Near edge, same authored 27 foreground tiles, readable waist-high rail.
    for x in range(16,448,16):
        od.line((x+1,260,x+1,271),fill=1,width=3)
        od.line((x+1,261,x+1,270),fill=13 if style==4 else 14)
        od.line((x,267,x+15,267),fill=12)
        od.line((x,266,x+15,266),fill=14)
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
    d.ellipse((192,63,287,104),fill=1)
    d.ellipse((195,65,284,101),fill=13)
    d.ellipse((199,67,280,97),fill=8)
    d.arc((195,65,284,101),0,180,fill=14,width=2)
    basin_mask,bmd=_new(480,320)
    bmd.ellipse((200,68,279,96),fill=1)
    waves=water_tile(s['water'],phase,s['water'],period)
    for yy in range(68,97):
        for xx in range(200,280):
            if basin_mask.getpixel((xx,yy)) and waves.getpixel((xx%16,yy%16))!=8:
                d.point((xx,yy),fill=waves.getpixel((xx%16,yy%16)))
    spacing={1:4,2:5,3:3,4:6,5:4}[s['water']]
    for x in range(226,253,spacing):
        width=2 if s['water']==3 else 3
        d.line((x,28,x,87),fill=9 if x%8 else 10,width=width)
        yy=31+(phase*3+x+s['water']*2)%47
        d.line((x,yy,x,min(88,yy+5+s['water'])),fill=11)
    for x in range(219,260,9):
        yy=83+(phase+x)%3;d.arc((x,yy,x+14,yy+8),0,180,fill=11)
    for x,yy in ((208,78),(255,77),(219,93),(257,91)):
        d.line((x+phase%3,yy,x+5+phase%3,yy),fill=9)
    _ladder(g,o,s['metal'])
    _pipe(d,(18,32,125,41),s['metal'],True)
    _pipe(d,(417,6,427,62),s['metal'])
    _market(g,o,s['market'],phase)
    _sanctum(g,s['sanctum'],phase)
    for x in (400,424):_crate(d,x,65,s['props'])
    d.ellipse((440,72,458,95),fill=1)
    d.ellipse((442,73,456,93),fill=12)
    for y in (77,89):d.line((442,y,456,y),fill=5);d.line((443,y-1,455,y-1),fill=7)
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
    for x,y in ((176,112),(378,120),(58,238),(302,218),(411,232)):
        d.ellipse((x-2,y+2,x+9,y+5),fill=2)
        if s['props']==1:
            d.polygon([(x,y),(x+4,y-2),(x+7,y+1),(x+3,y+3)],fill=5)
            d.line((x,y,x+3,y-1),fill=7)
        elif s['props']==2:
            d.ellipse((x,y-2,x+7,y+3),fill=12)
            d.arc((x+1,y-2,x+6,y+2),180,360,fill=14)
        elif s['props']==3:
            d.polygon([(x,y+1),(x+4,y-3),(x+8,y),(x+5,y+3)],fill=5)
            d.line((x+4,y-2,x+7,y),fill=7)
        elif s['props']==4:
            d.line((x,y,x+7,y+2),fill=7,width=2)
            for xx,yy in ((x,y),(x+7,y+2)):
                d.point((xx,yy-1),fill=7);d.point((xx,yy+1),fill=7)
        else:
            d.polygon([(x,y),(x+6,y-1),(x+8,y+2),(x+2,y+4)],fill=9)
            d.line((x+1,y,x+5,y),fill=11)
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
        d.line((2,0,2,15),fill=13);d.line((13,0,13,15),fill=14)
        for y in (2,7,12):
            d.line((3,y,12,y),fill=15 if style==3 else 14,width=2 if style==2 else 1)
            d.point((4,y),fill=15)
            if style==4:d.point((8,y),fill=12)
            elif style==5:d.line((3,y+1,12,y+1),fill=12);d.point((11,y),fill=15)
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
        for x in (0,8):
            d.rectangle((x,0,x+7,10),fill=9 if x==0 else 13)
            if style==2:d.ellipse((x,8,x+7,14),fill=9 if x==0 else 13)
            elif style==3:d.polygon([(x,10),(x+4,12),(x+7,10)],fill=9 if x==0 else 13)
            elif style==4:d.polygon([(x,10),(x+2,12),(x+4,11),(x+5,15),(x+7,10)],fill=9 if x==0 else 13)
            elif style==5:d.rectangle((x,10,x+7,12),fill=12);d.point((x+3,12),fill=14)
            else:d.polygon([(x,10),(x+3,14),(x+7,10)],fill=9 if x==0 else 13)
            d.line((x+1,1,x+5,1),fill=14)
        return im
    im,d=_new()
    if kind in ('counter','counter_r'):
        d.rectangle((0,1,15,15),fill=12);d.line((0,1,15,1),fill=14)
        d.line((0,7,15,7),fill=1);d.line((4,9,4,15),fill=13);d.line((12,9,12,15),fill=13)
        if style==2:d.point((2,3),fill=15);d.point((13,3),fill=15)
        elif style==3:d.line((0,4,15,4),fill=13)
        elif style==4:d.line([(7,9),(9,11),(7,14)],fill=9)
        elif style==5:d.polygon([(6,12),(8,9),(10,12),(8,14)],fill=14)
    elif kind=='crate':_crate(d,0,0,style,15,15)
    elif kind=='barrel':
        d.ellipse((2,0,13,15),fill=1);d.ellipse((3,1,12,14),fill=12)
        for y in (4,11):d.line((3,y,12,y),fill=5);d.line((4,y-1,11,y-1),fill=7)
        if style==1:d.line((7,2,7,13),fill=13)
        elif style==2:d.ellipse((4,5,11,10),outline=13)
        elif style==3:d.line((4,6,11,6),fill=14)
        elif style==4:d.line([(6,2),(5,7),(7,10),(6,13)],fill=1)
        else:d.line((4,8,11,8),fill=13);d.point((7,7),fill=14)
    elif kind=='skull':
        d.ellipse((3,2,12,11),fill=1);d.ellipse((4,3,11,10),fill=7)
        d.point((6,6),fill=1);d.point((9,6),fill=1);d.rectangle((5,10,10,13),fill=6)
        if style==2:d.ellipse((3,2,6,5),fill=6);d.line((4,12,11,12),fill=7)
        elif style==3:d.line([(8,3),(7,5),(8,7)],fill=4)
        elif style==4:d.rectangle((8,10,10,13),fill=0);d.point((5,4),fill=5)
        elif style==5:d.line((5,3,10,3),fill=7);d.point((7,11),fill=1)
    elif kind=='pot':
        d.ellipse((3,3,12,14),fill=1);d.ellipse((4,4,11,13),fill=12)
        d.line((3,3,12,3),fill=14);d.line((5,6,5,10),fill=13)
        if style==2:d.ellipse((1,5,5,10),outline=13);d.ellipse((10,5,14,10),outline=13)
        elif style==3:d.line((4,8,11,8),fill=5);d.line((5,9,10,9),fill=7)
        elif style==4:d.line([(9,4),(8,7),(10,10),(9,12)],fill=1)
        elif style==5:d.line((4,11,11,11),fill=14);d.point((8,7),fill=14)
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
        if layer=='overlay' and y==5:
            style=dict(zip(CATEGORIES,key))['market'];d=ImageDraw.Draw(result)
            # These canopy/counter overlay cells contain only the near lip.
            # Keep the original lower-two-pixel footprint while varying its
            # manufacture: dressed rim, rounded bead, steel, chipped, embossed.
            if style==1:d.point((8,15),fill=13)
            elif style==2:
                for xx in (2,10):d.point((xx,14),fill=15)
                d.line((1,15,14,15),fill=13)
            elif style==3:d.line((0,14,15,14),fill=7);d.line((0,15,15,15),fill=13)
            elif style==4:
                d.line((4,14,6,14),fill=12);d.point((5,15),fill=1)
            else:
                for xx in (3,11):d.point((xx,14),fill=15);d.point((xx,15),fill=13)
        if layer=='overlay' and y==6:
            style=dict(zip(CATEGORIES,key))['market'];d=ImageDraw.Draw(result)
            if style==1:d.line((7,2,7,9),fill=13)
            elif style==2:d.point((3,1),fill=15);d.point((12,1),fill=15)
            elif style==3:d.line((0,3,15,3),fill=13)
            elif style==4:d.line([(7,1),(9,4),(7,8)],fill=9)
            else:d.polygon([(6,4),(8,2),(10,4),(8,7)],fill=14)
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
