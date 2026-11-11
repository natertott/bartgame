"""Original final-size traversal annex; existing artwork/palettes preserved.
Quiet horizontal wood/stone planes, legible brass rails, open bridge slats
and a pale silk parachute contrast against the existing dirty banks. All
canvases are indexed4bpp native16px tiles or valid32x32 OBJ frames.
"""
from PIL import Image,ImageDraw

def rows(im):return [''.join(format(im.getpixel((x,y)),'x') for x in range(im.width)) for y in range(im.height)]
def new(w=16,h=16,fill=0):
    im=Image.new('P',(w,h),fill);return im,ImageDraw.Draw(im)
def tile(kind):
    overlay=kind.startswith('deck')
    im,d=new(fill=0 if overlay else 4)
    if kind=='water':
        d.rectangle((0,0,15,15),fill=3)
        d.line((0,4,6,4),fill=4);d.line((9,12,15,12),fill=4);d.line((2,3,5,3),fill=6)
        d.line((9,11,12,11),fill=5)
    elif kind=='pit':
        d.rectangle((0,0,15,15),fill=1);d.line((0,0,15,0),fill=2)
        d.line((1,1,5,1),fill=3);d.line((11,14,15,14),fill=2)
    elif kind.startswith('rail') or kind=='stop':
        for y in (3,11):
            if kind!='rail_v':d.line((0,y,15,y),fill=1,width=2);d.line((0,y-1,15,y-1),fill=8)
        if kind=='rail_v':
            for x in (3,11):d.line((x,0,x,15),fill=1,width=2);d.line((x-1,0,x-1,15),fill=8)
            for y in (0,7,14):d.line((1,y,13,y),fill=3)
        elif kind=='stop':d.ellipse((3,3,12,12),fill=1);d.ellipse((4,4,11,11),fill=7);d.ellipse((6,6,9,9),fill=2)
        elif kind in ('rail_se','rail_nw'):
            d.rectangle((0,0,15,15),fill=4)
            for x,y in ((3,3),(11,11)):
                d.line((x,15,x,y,15,y),fill=1,width=2);d.line((x-1,15,x-1,y-1,15,y-1),fill=8)
            if kind=='rail_nw':im=im.rotate(180)
        else:
            for x in (1,8,15):d.line((x,1,x,13),fill=3)
    elif overlay:
        for y in (1,5,9,13):
            d.rectangle((0,y,15,y+2),fill=2);d.line((0,y,15,y),fill=7);d.line((0,y+1,15,y+1),fill=5)
        if kind!='deck':
            x=1 if kind.endswith('w') else 14
            d.line((x,0,x,15),fill=1,width=3);d.line((x,0,x,15),fill=8)
            for y in (1,13):d.rectangle((max(0,x-1),y,min(15,x+1),y+1),fill=15)
    elif kind=='ramp':
        for y in (1,5,9,13):d.line((0,y,15,y),fill=2);d.line((0,y+1,15,y+1),fill=7)
        d.line((1,0,1,15),fill=8);d.line((14,0,14,15),fill=2)
    elif kind=='cliff':
        d.rectangle((0,0,15,15),fill=3)
        for y in (1,7,13):d.line((0,y,5,y,7,y-1,15,y-1),fill=2);d.line((1,y+1,7,y+1,9,y,15,y),fill=5)
    elif kind=='launch':
        d.line((0,13,15,13),fill=1,width=2);d.line((0,12,15,12),fill=8)
        d.polygon([(6,2),(9,2),(9,6),(12,6),(8,10),(3,6),(6,6)],fill=1)
        d.polygon([(7,3),(8,3),(8,7),(10,7),(8,9),(5,7),(7,7)],fill=15)
    elif kind=='socket':
        d.ellipse((2,2,13,13),fill=1);d.ellipse((3,3,12,12),fill=8);d.ellipse((5,5,10,10),fill=12)
        d.line((6,5,9,5),fill=14)
    elif kind in ('prize','open'):
        d.rectangle((2,4,13,13),fill=1);d.rectangle((3,5,12,11),fill=7);d.line((3,5,12,5),fill=15)
        if kind=='prize':d.rectangle((6,7,9,10),fill=8);d.point((7,7),fill=15)
        else:d.rectangle((4,6,11,10),fill=2)
    else:
        d.line((7,9,7,15),fill=2,width=2);d.rectangle((1,1,14,9),fill=1);d.rectangle((2,2,13,7),fill=7)
        d.line((4,3,11,3),fill=2);d.line((4,5,9,5),fill=2)
    return im
KINDS=('water','pit','rail_h','rail_v','rail_se','rail_nw','stop','deck','deck_w','deck_e','ramp','cliff','launch','socket','prize','open','sign')
METATILES=[dict(name='lh_mob_'+k,pal='lh_element' if k=='water' else 'lh_earth',type='WATER' if k=='water' else 'PIT' if k=='pit' else 'SOLID' if k=='cliff' else 'FLOOR',coll=15 if k=='cliff' else 0,art=rows(tile(k))) for k in KINDS]

def cart(face,phase):
    im,d=new(32,32)
    d.ellipse((3,25,28,30),fill=1)
    if face in ('e','w'):
        d.polygon([(3,11),(27,11),(25,24),(7,24)],fill=1)
        d.polygon([(5,12),(25,12),(23,21),(8,21)],fill=6)
        d.polygon([(7,13),(23,13),(21,16),(9,16)],fill=2)
        d.line((5,11,25,11),fill=12,width=2);d.line((7,23,23,23),fill=9)
        for x in (9,22):
            d.ellipse((x-3,23,x+3,29),fill=1);d.ellipse((x-2,24,x+2,28),fill=8)
            d.point((x+(1 if phase else -1),26),fill=12)
        d.line((15,17,15,21),fill=9)
        if face=='w':im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    else:
        d.polygon([(6,10),(24,10),(25,25),(5,25)],fill=1)
        d.polygon([(7,12),(23,12),(22,22),(8,22)],fill=6)
        d.rectangle((8,12,22,16),fill=2);d.line((7,11,23,11),fill=12,width=2)
        d.line((8,21,22,21),fill=9);d.rectangle((4,24,8,28),fill=1);d.rectangle((22,24,26,28),fill=1)
        d.line((5,25+phase,7,25+phase),fill=10);d.line((23,25+phase,25,25+phase),fill=10)
        if face=='n':d.line((7,15,23,15),fill=9,width=2)
    return im

def chute(phase):
    im,d=new(32,32);sway=phase
    d.line((3+sway,13,13,29),fill=1);d.line((28+sway,13,19,29),fill=1)
    d.line((4+sway,13,14,28),fill=11);d.line((27+sway,13,18,28),fill=11)
    d.polygon([(1,12),(4,5),(10,1),(21,1),(27,5),(30,12),(28,16),(24,13),(20,16),(16,13),(12,16),(8,13),(4,16)],fill=1)
    d.polygon([(3,11),(6,6),(11,3),(20,3),(25,6),(28,11),(26,13),(23,11),(20,13),(16,11),(12,13),(8,11),(5,13)],fill=11)
    d.polygon([(11,3),(15,2),(14,11),(11,13),(9,11)],fill=12)
    d.polygon([(17,2),(21,3),(24,11),(20,13),(18,11)],fill=10)
    d.line((6,6,10,3),fill=12);d.line((14,29,18,29),fill=8)
    return im

def build_sheets():
    return [dict(name='handoff_mobility',w=32,h=32,pal='gear',frames={**{f'cart_{f}{p}':rows(cart(f,p)) for f in ('n','e','s','w') for p in (0,1)},**{f'parachute{p}':rows(chute(p)) for p in (0,1)}})]
