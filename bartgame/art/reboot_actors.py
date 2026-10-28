"""Native actor art for the common gilt-and-rot vocabulary.

All pixels are authored on their final indexed canvases. Contracts provide
names and ordering only; no imported sprite pixels or reduced artwork enter
this module. Bodies share one feet baseline and explicit hand coordinates.
"""
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import reboot_core as C

HERE=Path(__file__).resolve().parent
BANK_ALIASES={'hero':'hero','bugs':'foliage','blight':'blight','iron':'stone',
              'fx':'gold','gear':'gold','folk':'hero','peddler':'gold',
              'gatekeeper':'stone'}
HANDS={'n':(5,-17),'e':(7,-12),'s':(3,-9),'w':(-8,-12)}
CARRY_HANDS=((-5,-24),(5,-24))
SWORD_BOUNDS={'n':(-14,-32,13,-12),'e':(4,-22,22,2),
              's':(-14,-6,13,12),'w':(-23,-22,-5,2)}


def blank(w,h):return Image.new('P',(w,h),0)


def ink_rows(im):
    return [''.join(format(im.getpixel((x,y)),'x') for x in range(im.width))
            for y in range(im.height)]


def stamp(dest,source,xy):
    mask=Image.new('L',source.size)
    mask.putdata([255 if value else 0 for value in source.tobytes()])
    dest.paste(source,xy,mask)


def line(d,points,ink=9,width=1):
    d.line(points,fill=1,width=width+2)
    d.line(points,fill=ink,width=width)


def facing_name(name):
    for face in ('n','e','s','w'):
        if '_'+face in name:return face
    return 's'


def _body(d,step=0,lean=0,squat=0):
    # Root feet end at row31 in every grounded pose.
    left=(10,31) if step<0 else (12,29) if step>0 else (11,31)
    right=(20,29) if step<0 else (22,31) if step>0 else (21,31)
    d.line([(15+lean,22+squat),(16,27),(left[0]+2,left[1]-1),left],fill=1,width=3)
    d.line([(17+lean,23+squat),(17,27),(right[0]-2,right[1]-1),right],fill=1,width=3)
    d.line([(15+lean,23+squat),(16,28)],fill=9,width=2)
    d.line([(16+lean,23+squat),(16,27)],fill=10)
    d.line([(left[0]+2,left[1]-2),(left[0]+1,left[1]-1)],fill=12)
    d.line([(right[0]-2,right[1]-2),(right[0]-1,right[1]-1)],fill=12)


def _arm(d,start,grip,near=True):
    # A connected tapered leaf/vine rather than a detached hand dot.
    sx,sy=start;gx,gy=grip
    bend=((sx+gx)//2, min(sy,gy)+2 if gy<sy else (sy+gy)//2)
    d.line([start,bend,grip],fill=1,width=3)
    d.line([start,bend,grip],fill=10 if near else 9,width=1)
    d.point(grip,fill=10)


def _head(im,face,dx=0,dy=0):
    head=C.hero(face,0).crop((0,0,16,14))
    stamp(im,head,(8+dx,10+dy))


def _normal(face,step=0,bob=0):
    im=blank(32,32);d=ImageDraw.Draw(im)
    _body(d,step)
    _arm(d,(14,24),(10,27),False)
    _arm(d,(18,24),(22,27))
    _head(im,face,dy=bob)
    return im


def _raised(face,step=0,stage=2):
    im=blank(32,32);d=ImageDraw.Draw(im)
    _body(d,step,squat=1 if stage==0 else 0)
    if stage==0:grips=((10,27),(22,27))
    elif stage==1:grips=((9,18),(23,18))
    else:grips=((11,8),(21,8))
    for shoulder,grip in zip(((13,24),(19,24)),grips):
        if stage==2:
            sx,sy=shoulder;gx,gy=grip
            d.line([(sx,sy),(8 if gx<16 else 24,17),(gx,gy)],fill=1,width=3)
            d.line([(sx,sy),(8 if gx<16 else 24,17),(gx,gy)],fill=10,width=1)
        else:_arm(d,shoulder,grip)
    _head(im,face,dy=1 if stage==0 else 0)
    # The palms touch the bottom-aligned16px load at worldy−24.
    if stage==2:
        d.point((11,8),fill=10);d.point((21,8),fill=10)
    return im


def _tool(face,phase=1,kind='use',step=0):
    im=blank(32,32);d=ImageDraw.Draw(im)
    lean=0 if phase!=0 else (-1 if face=='e' else 1 if face=='w' else 0)
    _body(d,step if kind=='guard' else -1 if phase==0 else 1 if phase==1 else 0,lean)
    gx,gy=HANDS[face];grip=(16+gx,32+gy)
    if kind=='guard' and face=='s':grip=(16,24)
    if face=='n':
        _arm(d,(18,24),grip,False);_arm(d,(13,24),(12,21),False)
    elif face=='s':
        _arm(d,(18,24),grip);_arm(d,(13,24),(12,26),False)
    else:
        _arm(d,(18,24),grip);_arm(d,(13,24),(12,26) if phase==2 else (15,24),False)
    _head(im,face,dy=0 if phase!=0 else 1)
    if face!='n':d.point(grip,fill=10)
    return im


def _roll(phase=2,face='e'):
    # One contiguous curled flower; no detached dust or speed strokes.
    if phase in (0,6):
        im=_normal(face,0)
        # Directional entry/exit keep the head/feet relationship intact.
        return im
    im=blank(32,32);d=ImageDraw.Draw(im)
    cx=16;cy=25
    d.ellipse((cx-6,cy-6,cx+5,cy+5),fill=1)
    d.ellipse((cx-5,cy-5,cx+4,cy+4),fill=2)
    a=(phase-1)*math.pi/2
    for i in range(5):
        angle=a+i*math.tau/5;x=round(cx+3*math.cos(angle));y=round(cy+3*math.sin(angle))
        d.ellipse((x-2,y-2,x+2,y+2),fill=3)
        d.point((x-1,y-1),fill=4)
    d.ellipse((13,22,18,27),fill=6 if phase%2 else 8)
    d.line([(14,22),(16,21),(18,23)],fill=7 if phase%2 else 10)
    d.line([(12,28),(16,29),(20,27)],fill=9)
    return im


def _jump(face,phase):
    if phase!=1:return _normal(face,0,bob=1 if phase==0 else 0)
    im=blank(32,32);d=ImageDraw.Draw(im)
    d.polygon([(14,23),(18,23),(20,26),(18,29),(15,28),(12,29),(11,27)],fill=1)
    d.line([(14,24),(17,27),(19,27)],fill=9,width=2)
    d.line([(14,26),(12,27)],fill=12)
    _arm(d,(13,24),(10,23),False);_arm(d,(19,24),(22,23))
    _head(im,face)
    return im


def hero_frame(name):
    face=facing_name(name)
    if name.startswith(('idle_','walk_')):
        step=(-1 if name.endswith('1') else 1) if name.startswith('walk_') else 0
        return _normal(face,step,bob=-1 if step==-1 else 0)
    if name.startswith('roll_'):
        if name.startswith(('roll_n','roll_s')):
            return _roll(0 if name.endswith('1') else 6,face)
        return _roll(int(name.rsplit('_',1)[1])-1,'e')
    if name.startswith('carry_'):
        step=-1 if name.endswith('1') else 1 if name.endswith('2') else 0
        return _raised(face,step)
    if name.startswith('lift_'):return _raised(face,0,int(name[-1]))
    if name.startswith('cape_'):return _jump(face,int(name[-1])-1)
    if name.startswith('jump_'):return _jump(face,1)
    if name.startswith('guard_'):
        step=-1 if name.endswith('1') else 1 if name.endswith('2') else 0
        return _tool(face,1,'guard',step)
    if name.startswith(('use_','bow_','atk_')):
        phase=(int(name[-1])-1 if name.startswith('use_') else int(name[-1]) if name.startswith('bow_') else 0 if name.endswith('1') else 2 if name.endswith('3') else 1)
        return _tool(face,phase,'bow' if name.startswith('bow') else 'sword' if name.startswith('atk') else 'use')
    if name=='itemget':return _raised('s',0,2)
    if name.startswith('hurt_'):
        im=_normal(face,1,bob=1);d=ImageDraw.Draw(im)
        d.line([(12,26),(10,24)],fill=10);d.line([(19,25),(22,23)],fill=10)
        return im
    if name.startswith('drown_'):
        n=int(name[-1]);im=blank(32,32)
        head=C.hero('s').crop((0,0,16,14))
        visible=(12,7,3)[n-1]
        stamp(im,head.crop((0,0,16,visible)),(8,32-visible))
        # One short pale waterline; never an opaque blue pool.
        d=ImageDraw.Draw(im);d.line([(10,31),(13,31)],fill=14)
        return im
    if name.startswith('fall_'):
        n=int(name[-1]);im=blank(32,32);d=ImageDraw.Draw(im)
        if n==1:return _jump('s',1)
        if n==2:
            d.ellipse((11,20,20,29),fill=1);d.ellipse((12,21,19,28),fill=3)
            d.rectangle((14,23,17,25),fill=6);d.line([(13,27),(17,28)],fill=9)
        else:
            d.ellipse((13,25,18,29),fill=1);d.line([(14,26),(17,27)],fill=3)
        return im
    if name.startswith('dead_'):
        n=int(name[-1]);im=blank(32,32);d=ImageDraw.Draw(im)
        if n==0:
            _body(d,1,squat=1);_head(im,'s',dy=2)
        else:
            d.line([(10,30),(16,29),(23,31)],fill=1,width=3)
            d.line([(11,30),(17,30)],fill=9)
            d.ellipse((14,23 if n==1 else 26,25,31),fill=1)
            d.ellipse((15,24 if n==1 else 27,24,30),fill=3)
            d.line([(16,25 if n==1 else 28),(22,25 if n==1 else 28)],fill=4)
            d.rectangle((18,27 if n==1 else 29,21,29 if n==1 else 30),fill=6)
        return im
    raise ValueError('Unhandled hero pose '+name)


def sword_frame(face,phase):
    im=blank(32,32);d=ImageDraw.Draw(im)
    bounds=SWORD_BOUNDS[face];x0,y0,x1,y1=bounds
    origin=(x0,y0-8 if face=='s' else y0)
    w=x1-x0;h=y1-origin[1]
    grip=(HANDS[face][0]-origin[0],HANDS[face][1]-origin[1])
    # A narrow, low-value sweep establishes reach without an opaque fan.
    if 1<=phase<=3:
        if face=='n':d.arc((0,0,w,h*2),180,360,fill=4)
        elif face=='s':d.arc((0,8-(h-8),w,h),0,180,fill=4)
        elif face=='e':d.arc((-w,0,w,h),270,450,fill=4)
        else:d.arc((0,0,w*2,h),90,270,fill=4)
    arc=im.copy()
    tips={
        'n':[(27,18),(27,3),(13,0),(0,9),(3,19)],
        'e':[(2,0),(16,0),(18,11),(16,24),(0,23)],
        's':[(0,10),(0,20),(13,26),(27,20),(27,9)],
        'w':[(16,0),(2,0),(0,11),(2,24),(18,23)],
    }
    tip=tips[face][phase]
    if 1<=phase<=3:
        if face in ('n','s'):
            start=max(0,tip[0]-4);end=min(w,tip[0]+4)
            d.line([(start,tip[1]),(end,tip[1])],fill=8)
        else:
            start=max(0,tip[1]-4);end=min(h,tip[1]+4)
            d.line([(tip[0],start),(tip[0],end)],fill=8)
        arc=im.copy()
    d.line([grip,tip],fill=1,width=3)
    d.line([grip,tip],fill=7,width=1)
    # A cream cutting point and simple brass grip distinguish blade and hilt.
    d.point(tip,fill=15)
    gx,gy=grip;dx=tip[0]-gx;dy=tip[1]-gy
    guard=((gx-2,gy),(gx+2,gy)) if abs(dy)>=abs(dx) else ((gx,gy-2),(gx,gy+2))
    d.line(guard,fill=13);d.point(grip,fill=10)
    if face=='n':
        head=hero_frame('atk_n')
        for y in range(10,24):
            for x in range(32):
                hx=x+origin[0]+16
                if 0<=hx<32 and head.getpixel((hx,y)):
                    im.putpixel((x,y),arc.getpixel((x,y)))
    return im


def cape_frame(face,phase):
    im=blank(32,32);d=ImageDraw.Draw(im)
    # Collar sits behind shoulders at worldy−11; cloth is not a hood icon.
    if face=='n':pts=[(11,21),(21,21),(24,27+phase%2),(20,26),(18,30),(15,28),(11,30),(8,27)]
    elif face=='s':pts=[(11,20),(21,20),(24,25),(20,24),(18,27),(14,26),(10,27),(8,24)]
    else:pts=[(14,20),(19,20),(23,24),(22,28),(18,26),(14,29),(11,26)]
    d.polygon(pts,fill=1);d.polygon([(x+(1 if x<16 else -1),y-1) for x,y in pts],fill=8)
    d.line([(12,22),(16,24),(20,23)],fill=10)
    d.line([(14,23),(13,27)],fill=9)
    return im


def beetle_frame(name):
    im=blank(16,16);d=ImageDraw.Draw(im);step=1 if name.endswith('1') else -1
    for x in (3,12):
        for y in (7,10,13):
            d.line([(x,y),(x-1 if x<8 else x+1,y+(step if x<8 else -step))],fill=1)
    d.ellipse((3,3,12,14),fill=1);d.ellipse((4,4,11,12),fill=5)
    d.polygon([(5,5),(7,4),(7,12),(4,10)],fill=6)
    d.line([(6,5),(6,8)],fill=7);d.line([(8,4),(8,12)],fill=1)
    if '_e' in name:
        d.ellipse((10,5,14,10),fill=1);d.point((13,7),fill=15)
    else:
        d.ellipse((5,10,10,15),fill=1);d.line([(6,12),(9,12)],fill=15)
    return im


def bat_frame(name):
    im=blank(16,16);d=ImageDraw.Draw(im)
    if name=='rest':
        d.polygon([(4,4),(7,6),(11,4),(12,13),(8,15),(3,12)],fill=1)
        d.line([(4,6),(7,12),(8,7)],fill=8);d.line([(11,6),(9,12)],fill=9)
    else:
        up=name=='fly1'
        left=[(6,8),(4,3 if up else 8),(0,1 if up else 12),(1,9 if up else 15),(4,10),(6,12)]
        right=[(15-x,y) for x,y in left]
        d.polygon(left,fill=1);d.polygon(right,fill=1)
        d.polygon([(round((x*2+7)/3),y+1 if up else y-1) for x,y in left],fill=9)
        d.polygon([(round((x*2+8)/3),y+1 if up else y-1) for x,y in right],fill=9)
        d.line([(5,8),(2,5 if up else 11),(1,3 if up else 13)],fill=10)
        d.line([(10,8),(13,5 if up else 11),(14,3 if up else 13)],fill=10)
    d.ellipse((5,5,10,13),fill=1);d.ellipse((6,6,9,11),fill=10)
    d.point((6,7),fill=7);d.point((9,7),fill=7)
    return im


def slime_frame(name):
    im=blank(16,16);d=ImageDraw.Draw(im)
    if name=='squash':box=(1,9,14,15)
    elif name=='jump':box=(3,2,12,14)
    else:box=(2,6,13,15)
    x0,y0,x1,y1=box
    d.ellipse(box,fill=1);d.ellipse((x0+1,y0+1,x1-1,y1-1),fill=4)
    d.ellipse((x0+2,y0+1,x1-3,y1-3),fill=6)
    d.line([(x0+3,y0+2),(x0+5,y0+2)],fill=7)
    d.point((x0+3,y0+1),fill=7)
    ey=y0+4;d.point((6,ey),fill=1);d.point((10,ey),fill=1)
    d.line([(7,ey+2),(9,ey+2)],fill=2)
    return im


def spitter_frame(name):
    im=blank(16,16);d=ImageDraw.Draw(im);face=facing_name(name);spit=name.startswith('spit')
    d.line([(5,12),(2 if name.startswith('walk') else 3,15)],fill=1,width=3)
    d.line([(11,12),(12 if name.startswith('walk') else 13,14 if name.startswith('walk') else 15)],fill=1,width=3)
    d.ellipse((3,3,12,14),fill=1);d.ellipse((4,4,11,12),fill=9)
    d.polygon([(4,5),(6,2),(10,2),(13,5),(11,7),(4,7)],fill=1)
    d.line([(5,4),(8,3),(11,5)],fill=12,width=2)
    d.point((6,3),fill=15);d.point((10,5),fill=13)
    if face=='n':
        d.line([(6,8),(9,10)],fill=10);d.point((6,8),fill=11)
    elif face=='e':
        d.point((10,7),fill=15);d.ellipse((10,9,15,13 if spit else 11),fill=1)
        if spit:d.line([(12,10),(14,10)],fill=11)
    else:
        d.point((5,7),fill=15);d.point((10,7),fill=15)
        d.ellipse((5,9,10,14 if spit else 12),fill=1)
        if spit:d.line([(6,10),(9,10)],fill=11)
    return im


def knight_frame(name):
    im=blank(16,32);d=ImageDraw.Draw(im);face=facing_name(name)
    step=-1 if name.endswith('1') else 1 if name.endswith('2') else 0
    # Dense stone-coloured armour with a simple gold closure; onehuman scale.
    left=(2,31) if step<0 else (4,29) if step>0 else (3,31)
    right=(12,29) if step<0 else (14,31) if step>0 else (13,31)
    d.line([(6,23),(5,27),left],fill=1,width=4)
    d.line([(10,23),(11,27),right],fill=1,width=4)
    d.line([(5-step,28),(3-step,29)],fill=4,width=2)
    d.line([(11+step,28),(13+step,29)],fill=3,width=2)
    d.polygon([(3,12),(12,12),(14,22),(11,26),(4,26),(1,22)],fill=1)
    d.polygon([(4,13),(11,13),(12,22),(9,24),(5,24),(3,21)],fill=4)
    d.line([(4,14),(7,13),(7,22)],fill=6,width=2)
    d.line([(4,23),(11,23)],fill=10);d.point((8,23),fill=14)
    hand=(15,16) if face=='e' else (12,19) if face=='s' else (13,15)
    d.line([(11,14),hand],fill=1,width=4);d.line([(11,14),hand],fill=5,width=2)
    d.line([(4,14),(1,20)],fill=1,width=4);d.line([(4,14),(1,20)],fill=3,width=2)
    # Helmet has a broad top and a short near face, not an oversized head.
    d.polygon([(4,4),(11,4),(13,7),(13,13),(10,16),(4,15),(2,12),(2,7)],fill=1)
    d.polygon([(5,5),(10,5),(12,8),(11,12),(4,12),(3,8)],fill=5)
    d.line([(5,5),(9,5),(11,7)],fill=8)
    if face=='n':d.line([(5,10),(9,10)],fill=4)
    elif face=='e':d.line([(8,10),(12,10)],fill=1);d.point((10,11),fill=13)
    else:d.line([(4,10),(11,10)],fill=1);d.point((6,11),fill=13);d.point((9,11),fill=13)
    d.line([(8,2),(8,5)],fill=9,width=2);d.point((8,2),fill=14)
    return im


def knight_sword(name):
    im=blank(16,16);d=ImageDraw.Draw(im)
    if name=='blade_e':
        d.line([(2,8),(14,8)],fill=1,width=3)
        d.line([(4,7),(13,7),(15,8),(12,9),(4,9)],fill=7)
        d.line([(4,7),(13,7)],fill=8);d.line([(3,5),(3,11)],fill=13)
        d.line([(0,8),(3,8)],fill=10)
    else:
        d.line([(8,2),(8,14)],fill=1,width=3)
        d.polygon([(7,4),(9,4),(9,12),(8,15),(7,12)],fill=7)
        d.line([(7,4),(7,12)],fill=8);d.line([(5,3),(11,3)],fill=13)
        d.line([(8,0),(8,3)],fill=10)
    return im


def boss_frame(name):
    im=blank(32,64);d=ImageDraw.Draw(im);pulse=name=='pulse2'
    # Root arteries and a wet, asymmetrical organ, not a large pickup heart.
    arteries=[[(15,57),(11,52),(8,45),(4,40)],[(18,54),(24,48),(27,40),(30,36)],
              [(14,30),(10,24),(8,18),(3,15)],[(20,31),(23,23),(21,17),(26,13)],
              [(13,56),(8,61),(1,62)],[(19,56),(24,61),(30,62)]]
    for pts in arteries:
        d.line(pts,fill=1,width=4);d.line(pts,fill=8,width=2)
        d.line([(x-1,y) for x,y in pts],fill=10)
    hull=[(15,26),(10,21),(5,22),(1 if pulse else 2,28),(2,39),(7,48),(14,57),(18,57),(26,49),(30,38),(29,28),(24,23),(20,24)]
    d.polygon(hull,fill=1)
    d.polygon([(15,29),(10,24),(6,25),(4,29),(5,39),(10,48),(16,54),(23,47),(27,38),(26,29),(22,26),(18,29)],fill=4)
    d.polygon([(8,26),(12,28),(15,34),(13,43),(9,43),(6,37),(6,30)],fill=6)
    d.polygon([(20,28),(24,29),(25,36),(22,43),(17,48),(15,42),(18,35)],fill=12)
    d.line([(9,27),(11,29),(12,34)],fill=14,width=2)
    d.line([(20,29),(22,30),(23,34)],fill=13,width=2)
    d.line([(16,31),(14,37),(17,43),(15,50)],fill=1,width=2)
    d.line([(18,32),(17,37),(19,40),(18,45)],fill=13)
    d.line([(6,35),(10,38),(9,42)],fill=12)
    d.line([(23,39),(21,43),(24,46)],fill=8)
    # A tiny unblemished ivory flower grows from diseased tissue.
    for box in [(24,18,27,21),(27,20,30,23),(24,22,27,25),(21,20,24,23)]:d.ellipse(box,fill=15)
    d.point((25,21),fill=11)
    # Bright wet highlights are compact, not a glowing full-body outline.
    d.line([(8,28),(10,28)],fill=15);d.point((8,29),fill=14)
    d.point((23,31),fill=15);d.point((15,51),fill=14)
    if name=='hurt':
        d.line([(8,26),(11,29),(12,34)],fill=15,width=2)
        d.line([(20,29),(22,31),(23,36)],fill=15)
    return im


def npc_frame(name):
    im=blank(32,32);d=ImageDraw.Draw(im)
    # Ordinary folk use the same compact anatomy and upper-left light.
    d.line([(13,26),(12,30),(9,31)],fill=1,width=3)
    d.line([(18,26),(19,30),(22,31)],fill=1,width=3)
    robe=8 if name in ('gardener','hermit','brother_mark') else 11 if name=='merchant' else 1
    light=10 if robe==8 else 12 if robe==11 else 13
    d.polygon([(11,18),(20,18),(23,28),(19,30),(10,30),(8,27)],fill=1)
    d.polygon([(12,19),(18,19),(21,27),(18,28),(11,28),(10,26)],fill=robe)
    d.line([(12,20),(13,27)],fill=light)
    d.line([(11,21),(7,25)],fill=1,width=3);d.point((7,25),fill=6)
    d.line([(20,21),(23,25)],fill=1,width=3);d.point((23,25),fill=6)
    d.ellipse((10,8,21,21),fill=1)
    hood=8 if name in ('hermit','gardener','brother_mark') else 13 if name=='sage' else 11 if name=='merchant' else 1
    d.polygon([(11,10),(13,8),(18,8),(21,11),(21,18),(10,18)],fill=hood)
    if hood==8:d.line([(12,10),(14,8),(17,8)],fill=10)
    d.ellipse((12,12,19,19),fill=6);d.line([(13,12),(17,12)],fill=7)
    d.point((13,15),fill=1);d.point((18,15),fill=1)
    if name in ('hermit','brother_mark'):
        d.polygon([(12,17),(19,17),(18,21),(15,23),(12,20)],fill=13)
        d.line([(13,18),(15,21)],fill=14)
    elif name=='gardener':
        d.polygon([(12,17),(19,17),(18,21),(14,22),(12,20)],fill=11)
        d.line([(13,18),(15,20)],fill=12)
        # Blindfold rather than miniature eye detail.
        d.line([(12,15),(19,15)],fill=1)
    elif name in ('nun','sister_mary_grace'):
        d.line([(10,11),(11,20),(14,22)],fill=13)
        d.point((18,17),fill=14)
        d.line([(14,24),(17,24)],fill=7)
        d.line([(11,28),(19,28)],fill=13)
        d.point((11,27),fill=14)
    elif name=='sage':
        d.line([(11,8),(19,8)],fill=7)
        d.line([(24,18),(24,31)],fill=12);d.point((24,18),fill=7)
    return im


def peddler_head(name):
    im=blank(16,16);d=ImageDraw.Draw(im)
    # Teal hood and small pointed ears keep the trader's rat-like identity.
    d.polygon([(2,9),(2,4),(5,2),(11,2),(14,5),(14,12),(11,14),(4,14)],fill=1)
    d.polygon([(3,8),(3,5),(6,3),(10,3),(13,6),(12,12),(4,12)],fill=13)
    d.line([(5,4),(8,3),(11,5)],fill=14)
    d.polygon([(4,7),(3,5),(5,6),(6,9)],fill=11)
    d.polygon([(10,7),(13,5),(12,10)],fill=11)
    d.ellipse((5,7,11,13),fill=11)
    d.line([(6,8),(9,8)],fill=12)
    if name=='blink':d.line([(6,10),(10,10)],fill=3)
    else:
        d.point((5 if name=='left' else 7,9),fill=1)
        d.point((10,9),fill=1)
    d.polygon([(8,10),(13,11),(10,13),(7,12)],fill=12)
    d.point((13,11),fill=15)
    if name=='grin':d.line([(8,13),(11,13)],fill=1)
    elif name=='down':d.point((8,10),fill=1)
    return im


def peddler_body(name):
    im=blank(32,32);d=ImageDraw.Draw(im)
    d.line([(13,26),(12,31)],fill=1,width=3);d.line([(18,26),(20,31)],fill=1,width=3)
    d.polygon([(10,17),(21,17),(23,28),(20,30),(10,30),(8,27)],fill=1)
    d.polygon([(11,18),(20,18),(21,27),(18,28),(11,28)],fill=4)
    d.line([(12,19),(12,26)],fill=6);d.line([(17,18),(17,28)],fill=3)
    d.line([(12,25),(20,25)],fill=7);d.point((16,25),fill=10)
    ly=24 if name not in ('rub0','rub1') else 21
    ry=21 if name in ('lift','spin9','spin7','spin5','spin3','spin5b','spin7b','spin9b') else 24
    if name=='tap2':ly=22
    d.line([(11,19),(8,ly)],fill=1,width=3);d.line([(11,19),(8,ly)],fill=4)
    d.point((8,ly),fill=11)
    d.line([(20,19),(24,ry)],fill=1,width=3);d.line([(20,19),(24,ry)],fill=5)
    d.point((24,ry),fill=12)
    if name.startswith('spin'):
        width=1 if '3' in name else 2 if '5' in name else 3 if '7' in name else 4
        cy=13 if name.endswith('b') else 11
        d.ellipse((24-width//2,cy-2,24+width//2,cy+2),fill=1)
        d.line([(24-width//2,cy-1),(24+width//2,cy-1)],fill=10)
        d.point((24,cy),fill=12)
    elif name=='slap':d.ellipse((21,23,26,25),fill=9);d.point((23,23),fill=12)
    elif name=='lift':d.ellipse((22,16,25,20),fill=9);d.point((23,17),fill=12)
    return im


def gatekeeper_frame(name):
    im=blank(32,32);d=ImageDraw.Draw(im)
    d.line([(13,26),(11,31)],fill=1,width=3);d.line([(18,26),(20,31)],fill=1,width=3)
    d.polygon([(11,17),(20,17),(23,28),(18,31),(9,29),(8,26)],fill=1)
    d.polygon([(12,18),(19,18),(21,27),(17,29),(10,27)],fill=3)
    d.line([(12,19),(12,26)],fill=6);d.line([(14,23),(13,27)],fill=5)
    if name.startswith('breath'):
        d.line([(14,21),(16,24)],fill=5)
        d.point((11,27),fill=6)
    d.line([(11,20),(7,25)],fill=1,width=3);d.point((7,25),fill=8)
    d.line([(20,20),(23,22),(23,19)],fill=1,width=3);d.line([(20,20),(23,22)],fill=6)
    d.line([(23,19),(23,22)],fill=12)
    d.ellipse((10,7,21,20),fill=1);d.ellipse((12,9,19,18),fill=7)
    d.polygon([(10,12),(11,7),(15,5),(20,8),(22,14),(20,12),(18,9),(13,9),(11,15)],fill=3)
    d.line([(12,8),(15,6),(19,8)],fill=6)
    d.line([(12,10),(19,10)],fill=12);d.point((15,10),fill=15)
    if 'blink' in name:d.line([(13,14),(18,14)],fill=4)
    else:d.point((13,14),fill=1);d.point((18,14),fill=1)
    d.line([(14,17),(16,17)],fill=4)
    # Only the orb/wisp uses13/14: its pulse cannot recolour her cloak.
    d.ellipse((21,15,25,19),fill=1);d.ellipse((22,16,24,18),fill=13)
    d.point((23,16),fill=14)
    if 'kindle' in name:d.line([(24,21),(25,19)],fill=8)
    return im


def wisp_frame(name):
    im=blank(8,8);d=ImageDraw.Draw(im);phase=int(name[-1])
    # Brightcentre3,4 matchesWISP_AT(20,13) and the orb at(23,17).
    pts=[(3,1),(5,3),(4,6),(2,6),(1,4)]
    d.polygon(pts,fill=13)
    d.line([(3,2),(3,5)],fill=14)
    if phase in (1,2):d.line([(1,4),(5,4)],fill=14)
    if phase==3:d.point((3,0),fill=13)
    return im


def glitter_frame(name):
    im=blank(8,8);d=ImageDraw.Draw(im)
    if name=='none':return im
    if name=='dim':d.point((3,3),fill=8)
    elif name=='fade':d.point((3,3),fill=6)
    elif name in ('glint','glint2'):
        d.point((3,3),fill=11);d.point((3,2),fill=9);d.point((2,3),fill=9)
        if name=='glint2':d.point((4,3),fill=10);d.point((3,4),fill=10)
    elif name=='star':
        d.line([(3,0),(3,6)],fill=9);d.line([(0,3),(6,3)],fill=9)
        d.line([(3,1),(3,5)],fill=11);d.line([(1,3),(5,3)],fill=11)
        d.point((3,3),fill=12)
    else:raise ValueError(name)
    return im


def effect_frame(name):
    im=blank(16,16);d=ImageDraw.Draw(im)
    if name.startswith('puff'):
        p=int(name[-1]);r=(3,5,6)[p-1]
        for cx,cy in ((8,8),(5,10),(10,11)):
            d.ellipse((cx-r//2,cy-r//2,cx+r//2,cy+r//2),fill=3 if p==3 else 5)
            d.line([(cx-r//2+1,cy-r//2),(cx,cy-r//2)],fill=7)
        if p==3:d.ellipse((5,8,10,12),fill=0)
    elif name=='clang':
        d.line([(8,2),(8,14)],fill=10);d.line([(2,8),(14,8)],fill=10)
        d.line([(5,5),(11,11)],fill=8);d.line([(5,11),(11,5)],fill=8)
        d.line([(8,5),(8,11)],fill=12);d.line([(5,8),(11,8)],fill=12)
    elif name.startswith('blast'):
        p=int(name[-1]);r=(4,6,7)[p-1]
        pts=[(8+round((r if i%2==0 else r//2)*math.cos(i*math.pi/4)),8+round((r if i%2==0 else r//2)*math.sin(i*math.pi/4))) for i in range(8)]
        d.polygon(pts,fill=5 if p==3 else 9)
        if p<3:d.ellipse((8-r//2,8-r//2,8+r//2,8+r//2),fill=12)
        else:d.ellipse((5,5,11,11),fill=0)
    elif name.startswith('flame'):
        p=int(name[-1]);d.polygon([(5,14),(3,10),(5,6),(6,2),(9,6),(11,4+p),(13,10),(11,14)],fill=9)
        d.polygon([(6,13),(5,10),(7,7),(9,10),(10,13)],fill=11)
        d.line([(7,12),(7,10)],fill=12)
    elif name.startswith('bomb'):
        d.ellipse((3,5,12,14),fill=1);d.ellipse((4,6,11,13),fill=3)
        d.line([(7,5),(9,2),(11,3)],fill=8);d.point((6,7),fill=6)
        if name=='bomb2':d.line([(11,1),(11,5)],fill=12);d.line([(9,3),(13,3)],fill=11)
    elif name.startswith('firefly'):
        gl=glitter_frame('glint' if name.endswith('1') else 'star');stamp(im,gl,(4,4))
    else:raise ValueError(name)
    return im


def projectile_frame(name):
    im=blank(8,8);d=ImageDraw.Draw(im)
    if name=='seed':
        d.ellipse((2,1,6,6),fill=1);d.ellipse((3,2,5,5),fill=7);d.point((3,2),fill=11)
    elif name=='spore':
        d.polygon([(3,0),(6,2),(7,5),(4,7),(1,5),(0,2)],fill=1)
        d.ellipse((2,2,5,5),fill=9);d.point((2,2),fill=12)
    elif name=='shard':
        d.polygon([(4,0),(7,3),(3,7),(0,5)],fill=1)
        d.line([(4,1),(5,3),(2,5)],fill=11);d.point((4,1),fill=12)
    else:raise ValueError(name)
    return im


def mouth_frame(name):
    im=blank(32,32);d=ImageDraw.Draw(im);p=int(name[-1])
    box=((7,23,24,31),(3,18,28,31),(5,20,26,31))[p-1]
    d.ellipse(box,fill=1);d.arc(box,0,180,fill=7,width=2)
    d.arc((box[0]+2,box[1]+2,box[2]-2,box[3]),180,350,fill=4,width=1)
    d.line([(8,29),(11,31),(18,30),(24,31)],fill=5)
    for x,y in ((8,25),(22,24),(18,29)):d.point((x,y),fill=9)
    return im


DRAWERS={'hero':hero_frame,'beetle':beetle_frame,'bat':bat_frame,
         'slime':slime_frame,'spitter':spitter_frame,'knight':knight_frame,
         'ksword':knight_sword,'npc':npc_frame,'boss':boss_frame,
         'peddler_head':peddler_head,'peddler_body':peddler_body,
         'gatekeeper':gatekeeper_frame,'wisp':wisp_frame,
         'fx':effect_frame,'proj':projectile_frame,'mouth':mouth_frame}
SIZES={'hero':(32,32),'boss':(32,64),'peddler_head':(16,16),
       'peddler_body':(32,32),'gatekeeper':(32,32),'wisp':(8,8)}


def build_sheets(contracts):
    """Return this painter's complete sheets, keeping every old frame id."""
    out={}
    for old in contracts['sheets']:
        name=old['name']
        if name not in DRAWERS and name not in ('bloomfx','bloomshadow'):continue
        w,h=SIZES.get(name,(old['w'],old['h']))
        framepal={};frames={}
        for frame in old['frames']:
            if name=='bloomfx':
                kind,facephase=frame.split('_',1);face=facephase[0];phase=int(facephase[1:])
                if kind=='sword':im=sword_frame(face,phase);pal='iron'
                elif kind=='cape':im=cape_frame(face,phase);pal='hero'
                else:
                    import reboot_items
                    im=reboot_items.held_item(kind,face,phase)
                    pal=reboot_items.held_palette(kind)
                framepal[frame]=pal
            elif name=='bloomshadow':
                im=blank(16,8);ImageDraw.Draw(im).ellipse((4,3,11,5),fill=1)
            else:im=DRAWERS[name](frame)
            assert im.size==(w,h),(name,frame,im.size,(w,h))
            frames[frame]=ink_rows(im)
        sheet={'name':name,'pal':old['pal'],'w':w,'h':h,'frames':frames}
        if framepal:sheet['frame_pal']=framepal
        out[name]=sheet
    out['glitter']={'name':'glitter','pal':'fx','w':8,'h':8,
                    'frames':{name:ink_rows(glitter_frame(name)) for name in
                              ('none','dim','glint','star','glint2','fade')}}
    return out


def actor_preview(path='/workspace/setup/reboot-actors-source.png'):
    contracts=json.loads((HERE/'reboot_contracts.json').read_text())
    sheets=build_sheets(contracts)
    selected=[]
    for name in DRAWERS:
        if name=='hero':continue
        old=next(r for r in contracts['sheets'] if r['name']==name)
        for frame in (old['frames'][:3] if name not in ('npc','peddler_head','gatekeeper') else old['frames']):
            selected.append((name,frame))
    cols=6;cw=170;ch=172
    out=Image.new('RGB',(cols*cw,42+math.ceil(len(selected)/cols)*ch),'#101820');d=ImageDraw.Draw(out)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
    d.text((8,8),'Native actor vocabulary / 1x and 3x / SOURCE ART, not emulator output',font=font,fill='#f0d898')
    for index,(name,frame) in enumerate(selected):
        sheet=sheets[name];im=Image.new('P',(sheet['w'],sheet['h']))
        im.putdata([int(v,16) for row in sheet['frames'][frame] for v in row])
        image=C.rgba(im,C.PALETTES[BANK_ALIASES[sheet['pal']]])
        x=index%cols*cw+8;y=index//cols*ch+42
        size=(image.width*3,image.height*3)
        if size[1]>124:
            image=image.crop((0,image.height-48,image.width,image.height));size=(image.width*2,image.height*2)
        big=image.resize(size,Image.Resampling.NEAREST)
        out.paste(big,(x,y),big);out.paste(image,(x+112,y+80),image)
        d.text((x,y+132),name,font=font,fill='#f0d898');d.text((x,y+146),frame,font=font,fill='#b0c0a0')
    out.save(path);return path


def context_preview(path='/workspace/setup/reboot-actors-context.png'):
    selected=[('beetle','walk_s1'),('bat','fly1'),('slime','idle'),
              ('spitter','idle_s'),('knight','idle_s'),('npc','nun'),
              ('npc','hermit'),('gatekeeper','idle'),('boss','pulse1')]
    contracts=json.loads((HERE/'reboot_contracts.json').read_text())
    sheets=build_sheets(contracts);cw=144;ch=184
    out=Image.new('RGB',(cw*len(selected),40+ch*3),'#101820');d=ImageDraw.Draw(out)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
    d.text((6,8),'Native actor silhouette checks / grass, blight, Drain / 3x and1x / SOURCE, not emulator',font=font,fill='#f0d898')
    for row,(material,index) in enumerate((('ground',4),('blight',3),('drain',4))):
        for col,(name,frame) in enumerate(selected):
            sh=sheets[name];a=Image.new('P',(sh['w'],sh['h']))
            a.putdata([int(v,16) for r in sh['frames'][frame] for v in r])
            # Boss viewing crop removes unused canvas padding, never scales
            # an asset into another asset. The native pixel sample is kept.
            image=C.rgba(a,C.PALETTES[BANK_ALIASES[sh['pal']]])
            if name=='boss':image=image.crop((0,12,32,64))
            x=col*cw;y=40+row*ch
            d.rectangle((x,y,x+cw-2,y+ch-19),fill=C.PALETTES[material][index])
            big=image.resize((image.width*3,image.height*3),Image.Resampling.NEAREST)
            out.paste(big,(x+8,y+2),big)
            out.paste(image,(x+108,y+52),image)
            d.text((x+3,y+ch-17),name+' '+frame,font=font,fill='#f0d898')
    out.save(path);return path


def _source_actor(im,face,feet,scene):
    if face=='w':im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    image=C.rgba(im,C.PALETTES['hero'])
    scene.alpha_composite(image,(feet[0]-16,feet[1]-32))


def motion_preview(path='/workspace/setup/reboot-hero-motion.gif',background='grass'):
    """A native compositing/anchor study. This is not gameplay evidence."""
    import reboot_items as I
    contracts=json.loads((HERE/'reboot_contracts.json').read_text())
    item_sheets=I.build_sheets(contracts)
    actions=('walk','roll','sword','guard','bow','lamp','cape','carry')
    width,height=4*96,30+len(actions)*84
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',10)
    frames=[]
    for tick in range(32):
        board=Image.new('RGB',(width,height),'#101820');draw=ImageDraw.Draw(board)
        draw.text((4,4),'Native source motion / 2x inspection / NOT mGBA',font=font,fill='#f0d898')
        for col,face in enumerate(('n','e','s','w')):
            for row,action in enumerate(actions):
                material,index={'grass':('ground',4),'blight':('blight',3),'cave':('stone',4),'drain':('drain',4)}[background]
                scene=Image.new('RGBA',(96,64),C.PALETTES[material][index]);feet=(48,52)
                d=ImageDraw.Draw(scene);d.line([(4,56),(14,56)],fill=C.PALETTES[material][index-1]);d.point((78,32),fill=C.PALETTES[material][index+1])
                d.ellipse((feet[0]-4,feet[1]-2,feet[0]+3,feet[1]),fill=C.PALETTES['hero'][1])
                nativeface='e' if face=='w' else face
                phase=(tick//4)%4
                if action=='walk':
                    name=('idle_'+nativeface,'walk_'+nativeface+'1','idle_'+nativeface,'walk_'+nativeface+'2')[phase]
                    body=hero_frame(name)
                elif action=='roll':
                    r=(tick//3)%8
                    if r in (0,6,7):
                        name='roll_'+nativeface+('1' if r==0 else '6' if r==6 else '7') if nativeface in ('n','s') else 'roll_'+str(1 if r==0 else 6 if r==6 else 7)
                    else:name='roll_'+str(r+1)
                    body=hero_frame(name)
                elif action=='sword':
                    p=min(4,(tick%20)//4)
                    name='atk_'+nativeface+('1' if p==0 else '3' if p>=3 else '')
                    body=hero_frame(name)
                    x0,y0,_,_=SWORD_BOUNDS[face]
                    blade=C.rgba(sword_frame(face,p),C.PALETTES['stone'])
                    # Same front OAM compositing as production; the north
                    # shaft mask is authored from the actual posed head.
                    _source_actor(body,face,feet,scene)
                    scene.alpha_composite(blade,(feet[0]+x0,feet[1]+y0-(8 if face=='s' else 0)))
                    body=None
                elif action=='guard':
                    body=hero_frame('guard_'+nativeface+('1' if phase==1 else '2' if phase==3 else ''))
                    frame='back' if face=='n' else 'front' if face=='s' else 'side'
                    rs=item_sheets['shield']['frames'][frame];shield=blank(16,16)
                    shield.putdata([int(v,16) if v!='.' else 0 for r in rs for v in r])
                    if face=='w':shield=shield.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    shield=C.rgba(shield,C.PALETTES['gold'])
                    pos={'n':(-3,-25),'e':(-1,-20),'s':(-8,-16),'w':(-15,-20)}[face]
                    if face=='n':scene.alpha_composite(shield,(feet[0]+pos[0],feet[1]+pos[1]))
                    _source_actor(body,face,feet,scene)
                    if face!='n':scene.alpha_composite(shield,(feet[0]+pos[0],feet[1]+pos[1]))
                    body=None
                elif action in ('bow','lamp'):
                    p=min(2,(tick//4)%3)
                    body=hero_frame(('bow_' if action=='bow' else 'use_')+nativeface+str(p if action=='bow' else p+1))
                    tool=I.held_item(action,nativeface,p)
                    if face=='w':tool=tool.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    tool=C.rgba(tool,C.PALETTES['gold'])
                    if face=='n':scene.alpha_composite(tool,(feet[0]-16,feet[1]-32))
                    _source_actor(body,face,feet,scene)
                    if face!='n':scene.alpha_composite(tool,(feet[0]-16,feet[1]-32))
                    body=None
                elif action=='cape':
                    heights=(0,3,6,9,10,9,6,3)
                    z=heights[(tick//2)%8]
                    p=0 if z<3 else 2 if tick%16>=12 else 1
                    body=hero_frame('cape_'+nativeface+str(p+1));cape=cape_frame(nativeface,p)
                    if face=='w':cape=cape.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    cape=C.rgba(cape,C.PALETTES['hero']);airfeet=(feet[0],feet[1]-z)
                    if face!='n':scene.alpha_composite(cape,(airfeet[0]-16,airfeet[1]-32))
                    _source_actor(body,face,airfeet,scene)
                    if face=='n':scene.alpha_composite(cape,(airfeet[0]-16,airfeet[1]-32))
                    body=None
                else:
                    body=hero_frame('carry_'+nativeface+('1' if phase==1 else '2' if phase==3 else ''))
                    rs=item_sheets['lift']['frames']['pot'];pot=blank(16,16)
                    pot.putdata([int(v,16) if v!='.' else 0 for r in rs for v in r])
                    _source_actor(body,face,feet,scene)
                    scene.alpha_composite(C.rgba(pot,C.PALETTES['stone']),(feet[0]-8,feet[1]-40))
                    body=None
                if body is not None:_source_actor(body,face,feet,scene)
                x=col*96;y=30+row*84
                board.paste(scene.convert('RGB'),(x,y));draw.text((x+3,y+65),action+' '+face,font=font,fill='#f0d898')
        frames.append(board)
    samples=[im.resize((width*2,height*2),Image.Resampling.NEAREST) for im in frames]
    samples[0].save(path,save_all=True,append_images=samples[1:],duration=70,loop=0,disposal=2)
    frames[0].save(Path(path).with_suffix('.png'))
    # Four chronology samples retain enough source-scale detail to assess
    # contact and direction without pretending to be an emulator filmstrip.
    contact=Image.new('RGB',(width*4,height),'#101820')
    for n,t in enumerate((0,8,16,24)):contact.paste(frames[t],(n*width,0))
    contact.save(Path(path).with_name(Path(path).stem+'-contact.png'))
    return path


def hero_preview(path='/workspace/setup/reboot-hero-source.png'):
    rowspec=[('idle',['idle_n','idle_e','idle_s']),('walk',['walk_n1','walk_e1','walk_s1']),
             ('sword',['atk_n1','atk_e','atk_s3']),('guard',['guard_n','guard_e','guard_s']),
             ('lift',['lift_n0','lift_e1','lift_s2']),('carry',['carry_n','carry_e1','carry_s2']),
             ('bow',['bow_n0','bow_e1','bow_s2']),('cape',['cape_n2','cape_e2','cape_s2']),
             ('hurt',['hurt_n','hurt_e','hurt_s']),('water',['drown_1','drown_2','drown_3']),
             ('roll',['roll_n1','roll_3','roll_s7']),('death',['dead_0','dead_1','dead_2'])]
    out=Image.new('RGB',(780,44+len(rowspec)*116),'#101820');d=ImageDraw.Draw(out)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
    d.text((8,8),'Native Bloom pose study / source art, not emulator output / 1x and 3x',font=font,fill='#f0d898')
    for y,(label,names) in enumerate(rowspec):
        for x,name in enumerate(names):
            im=C.rgba(hero_frame(name),C.PALETTES['hero']);px=12+x*258;py=44+y*116
            back=Image.new('RGB',(96,96),'#385038');big=im.resize((96,96),Image.Resampling.NEAREST);back.paste(big,(0,0),big)
            out.paste(back,(px,py));out.paste(im,(px+112,py+56),im)
            d.text((px+148,py+44),name,font=font,fill='#f0d898')
    out.save(path);return path


if __name__=='__main__':
    print(hero_preview())
