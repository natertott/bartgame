"""Additive native GBA bestiary for the original-game migration handoff.

The first 71 sheets follow source_catalogue.json order exactly. Existing game
sheets/palettes are never read, modified, traced or replaced. These drawings
start on their final 16/32px indexed canvases with existing RGB555 banks.
Eight whole-body pose families describe anticipation, commitment, exposure,
recovery and disguise; no ambient sparkles substitute for an attack cue.

Exported atlases are SOURCE ART, never emulator evidence. The shared rules
and source provenance are recorded in docs/handoff-restoration/ENEMIES.md.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont
import reboot_core as R

POSES=('idle','walk1','walk2','tell','attack','recover','hurt','buried')
FACES=('n','e','s','w')
CATALOGUE=Path(__file__).resolve().parents[1]/'docs/enemy-prototypes/source_catalogue.json'
ENTRIES=json.loads(CATALOGUE.read_text())['entries']
LARGE={'STALFOS','KEATON','ARMOS','EYEGORE','LIKE_LIKE','RUPEE_LIKE','GOBDO',
       'SCISSORS_BEETLE','ENEMY_4D','BOW_MOBLIN','SPEAR_MOBLIN','WIZZROBE_FIRE',
       'WIZZROBE_ICE','WIZZROBE_WIND','DARK_NUT','BALL_CHAIN_SOLIDER'}

class Canvas:
    def __init__(self,w,h,pose,face,form=0):
        self.im,self.d=R.indexed(w,h);self.w=w;self.h=h
        self.pose=pose;self.face=face;self.form=form;self.dx=0;self.dy=0;self.bare=False
        self.step=-1 if pose=='walk1' else 1 if pose=='walk2' else 0
        self.side=-1 if face=='w' else 1 if face=='e' else 0
    def pt(self,p):return (self.w//2+p[0]+self.dx,self.h-2+p[1]+self.dy)
    def poly(self,points,ink):self.d.polygon([self.pt(p) for p in points],fill=ink)
    def line(self,points,ink,width=1):self.d.line([self.pt(p) for p in points],fill=ink,width=width)
    def rect(self,b,ink):self.d.rectangle((*self.pt(b[:2]),*self.pt(b[2:])),fill=ink)
    def ell(self,b,ink):self.d.ellipse((*self.pt(b[:2]),*self.pt(b[2:])),fill=ink)
    def dot(self,p,ink):self.d.point(self.pt(p),fill=ink)
    def eyes(self,x,y,separation=3,closed=False):
        if self.face=='n':
            self.line([(x-separation,y-1),(x+separation,y-1)],3)
        elif self.face in ('e','w'):
            ex=x+(2 if self.face=='e' else -2)
            self.line([(ex,y-1),(ex,y+1)],15 if not closed else 3)
            if not closed:self.dot((ex+self.side,y),1)
        elif closed:self.line([(x-separation,y),(x+separation,y)],1)
        else:
            self.rect((x-separation,y-1,x-separation+1,y+1),15)
            self.rect((x+separation-1,y-1,x+separation,y+1),15)
            self.dot((x-separation+1,y),1);self.dot((x+separation,y),1)
    def volume(self,b,base=4,light=6,shadow=3):
        x0,y0,x1,y1=b
        self.ell(b,1);self.ell((x0+1,y0+1,x1-1,y1-1),base)
        self.poly([(x0+2,y0+2),((x0+x1)//2,y0+1),((x0+x1)//2+1,(y0+y1)//2),
                   (x0+2,(y0+y1)//2)],light)
        self.line([(x0+3,y1-2),(x1-3,y1-2)],shadow)
    def mound(self):
        self.poly([(-7,0),(-5,-3),(-1,-4),(4,-3),(7,0)],1)
        self.poly([(-5,-1),(-3,-3),(2,-3),(5,-1)],9)
        self.line([(-4,-2),(0,-3),(2,-2)],11)
    def feet(self,width=4,y=0,ink=9):
        for s in (-1,1):
            off=self.step*s
            self.line([(s*(width-1),y-3),(s*width+off,y-1),(s*(width+2)+off,y)],1,2)
            self.dot((s*width+off,y-1),ink)
    def shadow(self,r=5):self.ell((-r,-1,r,1),2)


def _beetle(c,kind):
    p=c.pose;c.shadow(5)
    if p=='buried' and kind=='SPINY_BEETLE':
        c.poly([(-6,0),(-7,-5),(-3,-11),(3,-12),(7,-7),(6,0)],1)
        c.poly([(-5,-2),(-5,-6),(-2,-10),(2,-10),(5,-6),(4,-2)],8)
        c.line([(-3,-8),(0,-10),(3,-7)],10);c.dot((-1,-9),11);return
    if p=='recover' and kind in ('SPIKED_BEETLE','ROLLOBITE'):
        c.volume((-6,-11,6,0),5,7,3)
        c.line([(-3,-7),(3,-7)],12);c.line([(-3,-4),(3,-4)],12)
        for s in (-1,1):
            for y in (-9,-5):c.line([(s*4,y),(s*7,y-2)],1)
        c.eyes(0,-9,2);return
    dy=1 if p=='tell' else 0
    for s in (-1,1):
        for y,k in ((-9,1),(-6,-1),(-3,1)):
            step=c.step*k*s
            c.line([(s*3,y+dy),(s*6,y+step),(s*7,y+step+1)],1)
            c.dot((s*6,y+step),10)
    c.dy=dy
    c.volume((-5,-12,5,-1),4 if kind!='MULLDOZER' else 8,6 if kind!='MULLDOZER' else 10,3)
    c.line([(0,-10),(0,-3)],12)
    if kind=='MULLDOZER' and c.form:
        c.line([(-3,-8),(3,-8)],14);c.line([(-3,-5),(3,-5)],12)
    if kind=='ROLLOBITE':
        for y in (-9,-6,-3):c.line([(-3,y),(3,y)],11)
    if kind in ('SPIKED_BEETLE','SPINY_BEETLE','MULLDOZER'):
        for x in (-3,0,3):
            c.poly([(x-1,-9),(x,-14 if p!='tell' else -11),(x+2,-9)],1)
            c.line([(x,-10),(x,-12)],15 if kind=='SPIKED_BEETLE' else 11)
    hy=-11 if c.face=='n' else -3 if c.face=='s' else -7
    hx=c.side*4
    c.volume((hx-3,hy-3,hx+3,hy+2),5,7,3);c.eyes(hx,hy,2)
    if kind=='BEETLE':
        c.line([(hx-2,hy-2),(hx-3,max(-14,hy-3))],1);c.line([(hx+2,hy-2),(hx+3,max(-14,hy-3))],1)
    if kind=='HELMASAUR' and not c.bare:
        if c.face in ('n','s'):plate=(-5,hy-3,5,hy+3)
        else:plate=(hx-3,-12,hx+3,-1)
        c.volume(plate,9,11,8)
        c.line([(plate[0]+2,plate[1]+2),(plate[2]-2,plate[1]+2)],15)
        c.eyes(hx,hy,2,True)
    c.dy=0


def _wing(c,side,raised,feather=False):
    reach=7;hy=-10
    pts=[(side*2,hy),(side*reach,-14 if raised else -8),(side*6,-6 if raised else -2),
         (side*3,-8 if raised else -5),(side*1,-5)]
    c.poly(pts,1)
    c.poly([(side*2,hy),(side*6,-13 if raised else -8),(side*5,-7 if raised else -4),(side*2,-6)],4)
    c.line([(side*2,-10),(side*5,-12 if raised else -7)],6)
    if feather:c.line([(side*3,-7),(side*5,-9 if raised else -5)],12)


def _flyer(c,kind):
    p=c.pose;raised=p in ('walk1','tell','attack')
    if kind in ('PEAHAT','BOMB_PEAHAT'):
        c.shadow(4)
        if p=='recover':
            c.volume((-4,-8,4,0),9,11,8);c.eyes(0,-5,2);c.feet(3);return
        c.volume((-4,-9,4,-1),4,6,3)
        if kind=='BOMB_PEAHAT':
            c.volume((-4,-6,4,1),2,4,1);c.line([(0,-7),(1,-10)],11);c.dot((2,-10),14)
        y=-10 if p!='tell' else -9
        if raised:
            c.poly([(-7,y),(-6,y-3),(-2,y-1),(0,y),(2,y-2),(7,y-2),(6,y+1),(1,y+1)],1)
            c.line([(-5,y-2),(-1,y),(5,y-1)],7)
        else:
            c.line([(-7,y),(7,y)],1,3);c.line([(-6,y-1),(5,y-1)],7)
        c.eyes(0,-5,2);return
    if kind in ('SMALL_PESTO','PESTO'):
        c.shadow(4)
        for s in (-1,1):
            yy=-12 if raised else -6
            c.poly([(s*2,-9),(s*7,yy),(s*6,yy+4),(s*2,-5)],1)
            c.line([(s*3,-8),(s*6,yy+1),(s*5,yy+3)],7 if c.form else 6)
        c.volume((-3,-12,3,-3),4,6,3);c.line([(0,-4),(1,0)],12)
        c.eyes(0,-10,2)
        if kind=='PESTO':c.volume((-3,-5,3,0),8,11,9)
        return
    for s in (-1,1):_wing(c,s,raised,kind!='KEESE')
    c.volume((-3,-12,3,-2),3,5,2)
    if kind=='KEESE':
        c.poly([(-3,-10),(-4,-14),(-1,-13),(1,-13),(4,-14),(3,-10)],1)
        c.line([(-2,-12),(-2,-14)],12);c.line([(2,-12),(3,-14)],12)
    else:
        c.poly([(-2,-4),(0,0),(3,-4)],1)
        c.volume((-3,-13,3,-7),3,5,2)
        b=c.side*5 if c.side else 0;by=-11 if c.face=='n' else -6
        c.poly([(b-2,by-2),(b+2,by-2),(b+c.side*2,by+1)],11)
        if kind=='TAKKURI':
            c.poly([(-2,-12),(-4,-14),(0,-14),(1,-14),(3,-12)],12)
            c.volume((0,-5,5,0),9,11,8)
    c.eyes(0,-10,2)
    if p=='buried' and kind in ('CROW','KEESE'):
        c.poly([(-4,-9),(-3,-3),(0,-1),(3,-4),(4,-9),(1,-6),(-1,-6)],2)


def _tektite(c):
    p=c.pose;c.shadow(5)
    crouch=p in ('tell','recover');y=-6 if crouch else -10
    for s in (-1,1):
        c.line([(s*2,y),(s*6,y-2 if not crouch else y),(s*7,0)],1,2)
        c.line([(s*2,y+2),(s*5,y+4),(s*4+c.step*s,1)],1,2)
        c.dot((s*6,y-1),11)
    c.poly([(-5,y),(-2,y-4),(2,y-4),(5,y),(3,y+4),(-3,y+4)],1)
    c.poly([(-3,y),(-1,y-2),(2,y-2),(3,y),(1,y+2),(-2,y+2)],6 if not c.form else 7)
    c.ell((-2,y-1,2,y+2),15);c.dot((c.side,y+1),1)


def _jelly(c,kind):
    p=c.pose;c.shadow(5)
    mini=kind=='MINI_SLIME';r=4 if mini else 6
    y0=-8 if mini else -12
    if p in ('tell','recover'):y0+=4;r+=1 if not mini else 0
    if p=='attack':y0-=1;r-=1
    c.poly([(-r,0),(-r,-4),(-r+2,y0+2),(-2,y0),(2,y0),(r-2,y0+2),(r,-4),(r,0)],1)
    c.poly([(-r+1,-1),(-r+1,-4),(-r+3,y0+3),(-2,y0+1),(2,y0+1),(r-1,-4),(r-1,-1)],5 if c.form!=2 else 6)
    c.poly([(-r+2,-4),(-r+3,y0+3),(-1,y0+2),(0,min(-2,y0+6)),(-3,min(-2,y0+7))],7)
    c.line([(-r+2,-1),(r-2,-1)],3)
    c.eyes(0,-4 if mini else y0+6,2)
    if kind=='ROCK_CHUCHU' and not c.bare:
        c.poly([(-6,-1),(-6,-9),(-3,-13),(3,-12),(6,-8),(5,-1)],1)
        c.poly([(-4,-3),(-4,-9),(-2,-11),(2,-10),(4,-7),(3,-2)],8)
        c.line([(-3,-9),(0,-10),(2,-8)],11);c.line([(0,-10),(0,-6),(3,-4)],2)
        c.eyes(0,-5,2)
    if kind=='SPINY_CHUCHU' and p in ('idle','walk1','walk2','tell'):
        for x in (-5,0,5):c.poly([(x-2,-6),(x,-14 if p=='tell' else -12),(x+2,-6)],1);c.dot((x,-10),14)
    if c.form in (1,2):
        c.line([(-4,-3),(-2,-7),(0,-5),(2,-9),(4,-5)],13)
        c.dot((-2,-7),14)


def _octorok(c,kind):
    p=c.pose;r=5;c.shadow(5)
    for s in (-1,1):
        y=-1+c.step*s
        c.poly([(s*2,-4),(s*6,-4),(s*7,y),(s*4,y+1),(s*3,-1)],1)
        c.line([(s*3,-3),(s*5,-2),(s*6,y)],6)
    c.volume((-5,-12,5,-2),5 if not c.form else 6,7,3)
    c.eyes(0,-8,3)
    if c.side:
        x=c.side*5;c.rect((min(x,x+c.side*2),-7,max(x,x+c.side*2),-4),1)
        c.line([(x,-6),(x+c.side*2,-6)],11)
        if p=='attack':c.dot((x+c.side*2,-5),15)
    else:
        y=-12 if c.face=='n' else -4
        c.ell((-2,y-2,2,y+2),1);c.line([(-1,y-1),(1,y-1)],11)
        if p=='attack':c.ell((-1,y,1,y+1),15)
    if kind=='OCTOROK2':c.poly([(-4,-11),(-5,-14),(-1,-13),(1,-14),(4,-11)],12)


def _rope(c):
    p=c.pose;c.shadow(5)
    if p=='tell':
        c.volume((-5,-10,5,0),4,6,3);c.line([(-3,-3),(3,-3),(3,-6),(-2,-7)],12)
        hx=0;hy=-10
    elif c.side:
        y=-5
        c.poly([(-7,-1),(-7,-5),(-3,-8),(2,-8),(7,-6),(7,-1)],1)
        c.poly([(-6,-2),(-5,-5),(-2,-6),(2,-6),(6,-4),(6,-2)],5)
        c.line([(-4,-5),(0,-6),(3,-4)],12);hx=c.side*4;hy=-6
    else:
        c.poly([(-4,0),(-5,-4),(-3,-8),(-4,-12),(0,-14),(4,-11),(3,-7),(5,-3),(3,0)],1)
        c.line([(0,-1),(2,-4),(0,-7),(-1,-10),(0,-12)],6,3)
        c.line([(-1,-2),(1,-4),(0,-7)],12);hx=0;hy=-12 if c.face=='n' else -3
    c.volume((hx-3,hy-2,hx+3,hy+3),5,7,3);c.eyes(hx,hy,2)
    if p=='attack':
        if c.side:c.line([(hx,hy+2),(hx+c.side*3,hy+2)],13)
        else:c.line([(hx,hy),(hx,hy+3 if c.face=='s' else hy-2)],13)


def _bomb(c,floating=False):
    p=c.pose;c.shadow(5)
    if not floating:c.feet(4,0,11)
    c.volume((-6,-12,6,-1),3,5,2)
    if floating:
        for x,y in ((-5,-9),(5,-9),(-5,-3),(5,-3),(0,-12)):
            c.poly([(x-1,y+2),(x,y-2),(x+2,y+1)],1);c.dot((x,y),11)
        c.eyes(0,-8,2)
        if p in ('tell','attack'):c.line([(-3,-4),(3,-4)],13);c.dot((0,-5),15)
    else:
        c.eyes(0,-7,2);c.line([(0,-12),(1,-14),(3,-14)],11)
        if p in ('tell','attack','hurt'):
            c.dot((3,-14),14);c.dot((4,-14),15);c.line([(-4,-4),(2,-4)],12)
        c.line([(-2,-11),(0,-11)],7)


def _leever(c):
    if c.pose=='buried':c.mound();return
    c.mound();height=-8 if c.pose in ('tell','recover') else -13
    for s in (-1,1):
        c.line([(s*3,-5),(s*5,-2),(s*7,-1)],1,2);c.dot((s*5,-2),11)
    c.poly([(-5,0),(-5,height+4),(-3,height),(3,height),(5,height+4),(5,0)],1)
    c.poly([(-3,-2),(-3,height+3),(-1,height+1),(2,height+2),(3,-2)],6 if c.form else 4)
    c.ell((-3,height+2,3,-2),15);c.ell((-2,height+3,2,-3),1)
    c.line([(0,height+5),(0,-5)],13);c.dot((0,height+4),14)


def _worm(c,kind):
    c.shadow(6)
    if c.pose=='buried':c.mound();return
    if kind=='MOLDWORM':
        c.volume((-6,-11,6,0),9,11,8)
        c.ell((-5,-9,5,-1),15);c.ell((-4,-8,4,-2),1)
        c.line([(-3,-6),(-2,-4)],15);c.line([(3,-6),(2,-4)],15)
        c.line([(0,-7),(0,-3)],13)
    elif kind=='MADDERPILLAR':
        c.poly([(-6,0),(-7,-8),(-4,-13),(0,-11),(4,-13),(7,-8),(6,0)],1)
        c.poly([(-5,-2),(-5,-7),(-3,-11),(0,-9),(3,-11),(5,-7),(5,-2)],9)
        c.line([(-4,-7),(4,-7)],11);c.line([(0,-9),(0,-3)],12)
        c.eyes(0,-5,3)
    else:
        c.volume((-6,-12,6,0),4,6,3)
        c.poly([(-5,-9),(-7,-14),(-3,-12),(-1,-9)],1)
        c.poly([(5,-9),(7,-14),(3,-12),(1,-9)],1)
        c.line([(-5,-12),(-4,-10)],13);c.line([(5,-12),(4,-10)],13)
        c.eyes(0,-7,3);c.line([(-3,-3),(0,-1),(3,-3)],15)
    if c.pose=='tell':
        c.line([(-4,-7),(-1,-8)],13);c.line([(1,-8),(4,-7)],13)
    elif c.pose=='attack':
        c.ell((-4,-6,4,-1),1);c.line([(-3,-5),(-2,-3)],15);c.line([(3,-5),(2,-3)],15)
        c.line([(-1,-3),(1,-3)],13)


def _ghost(c,mirage=False):
    p=c.pose
    if p=='buried':
        c.line([(-4,-2),(0,-4),(4,-2)],4);c.line([(-3,-1),(3,-1)],12);return
    top=-14;bottom=-1 if p!='attack' else 1
    c.poly([(-6,-5),(-5,-10),(-2,top),(2,top),(5,-10),(6,-4),(4,bottom),
            (2,bottom-2),(0,bottom),(-2,bottom-2),(-5,bottom)],1)
    c.poly([(-4,-5),(-3,-10),(-1,-12),(2,-11),(4,-6),(3,-2),(0,-3),(-3,-2)],6 if not mirage else 4)
    c.line([(-3,-9),(-2,-11),(0,-12)],7)
    if mirage:
        c.poly([(-4,-8),(0,-11),(4,-8),(3,-4),(-3,-4)],2)
        c.line([(-3,-6),(-1,-6)],14);c.line([(1,-6),(3,-6)],14)
        if p=='attack':c.ell((-3,-4,3,0),15);c.ell((-2,-3,2,-1),1)
    else:
        c.eyes(0,-8,2);c.ell((-1,-5,1,-3),1)
    if p in ('tell','attack'):
        c.line([(-4,-6),(-7,-4),(-7,-2)],1,2);c.line([(4,-6),(7,-4),(7,-2)],1,2)


def _cloud(c,kind):
    p=c.pose
    if kind=='CLOUD_PIRANHA':
        if p=='buried':
            for x in (-4,0,4):c.volume((x-3,-7,x+3,0),6,7,4)
            return
        c.poly([(-6,-3),(-6,-9),(-3,-12),(3,-12),(6,-9),(6,-3),(2,-1),(-2,-1)],1)
        c.poly([(-4,-4),(-4,-8),(-2,-10),(3,-10),(4,-7),(3,-3)],5)
        c.poly([(-3,-11),(0,-14),(2,-11)],12)
        c.ell((-5,-8,5,-2),15);c.ell((-4,-7,4,-3),1)
        c.line([(-3,-7),(-2,-5)],15);c.line([(3,-7),(2,-5)],15)
        c.eyes(0,-10,2)
        if p=='tell':c.line([(-4,-5),(4,-5)],13,2)
        elif p=='attack':
            c.ell((-5,-8,5,-1),15);c.ell((-4,-7,4,-2),1)
            c.line([(-3,-7),(-2,-4)],15);c.line([(3,-7),(2,-4)],15)
    else:
        if not c.bare:
            for x,y in ((-4,-3),(0,-2),(4,-3)):
                c.volume((x-3,y-5,x+3,y+2),6,7,4)
        c.volume((-4,-14,4,-5),9,11,8)
        c.poly([(-4,-10),(-5,-14),(-1,-13),(1,-14),(4,-11)],1)
        c.line([(-2,-12),(2,-12)],12);c.eyes(0,-9,2)
        if p in ('tell','attack'):c.line([(4,-7),(6,-10),(5,-12)],1,2);c.dot((5,-12),14)


def _spark(c,wisp=False):
    p=c.pose
    if p=='buried':return
    if wisp:
        c.poly([(-4,0),(-6,-4),(-4,-9),(-1,-14),(1,-10),(4,-12),(6,-6),(4,-2),(1,0)],1)
        c.poly([(-3,-2),(-4,-5),(-2,-9),(0,-11),(1,-7),(3,-9),(4,-5),(2,-2)],12 if not c.form else 6)
        c.line([(-1,-4),(0,-8),(2,-6)],14);c.eyes(0,-5,2)
        if p in ('tell','attack','walk2'):
            c.line([(-3,-8),(-2,-11),(0,-13)],14)
            c.line([(1,-2),(3,-4),(3,-7)],7 if c.form else 13)
    else:
        c.poly([(0,-14),(2,-10),(6,-12),(5,-7),(7,-5),(3,-3),(3,1),(0,-1),(-4,1),(-3,-4),(-7,-6),(-3,-9),(-4,-12)],1)
        c.poly([(0,-12),(1,-7),(4,-8),(2,-5),(2,-1),(0,-3),(-3,-2),(-1,-6),(-4,-7),(-1,-8)],13)
        c.rect((-1,-8,1,-4),15);c.line([(-3,-6),(3,-6)],14)
        if p in ('walk2','tell','attack'):
            c.line([(-4,-10),(-2,-9),(-1,-7)],15)
            c.line([(1,-5),(3,-3),(4,-2)],14)


def _flame(c,mini=False):
    p=c.pose;c.shadow(4)
    r=4 if mini else 6;top=(-10 if mini else -14)+(1 if p=='walk1' else 2 if p in ('walk2','tell') else 0)
    c.poly([(-r,0),(-r,-5),(-r+2,-9),(0,top),(1,top+4),(r-1,-11),(r,-5),(r,0)],1)
    c.poly([(-r+1,-1),(-r+1,-4),(-2,-8),(0,top+3),(1,-5),(r-2,-8),(r-1,-3),(r-2,-1)],12)
    c.poly([(-2,-1),(-2,-4),(0,-8),(2,-3),(2,-1)],14)
    c.dot((0,-3),15);c.eyes(0,-5,2)
    if p in ('tell','attack'):
        c.line([(-2,-7),(-1,-10 if not mini else -8)],14)
        c.line([(2,-5),(3,-8)],13)
    if p=='recover':c.line([(-4,-2),(0,-4),(4,-2)],6)


def _mushroom(c):
    p=c.pose;c.shadow(5);c.feet(3,0,11)
    c.poly([(-3,-1),(-2,-10),(2,-10),(3,-1)],1)
    c.poly([(-1,-2),(-1,-9),(1,-9),(1,-2)],11)
    c.eyes(0,-4,2)
    if not c.bare:
        y=-8 if p=='tell' else -9
        c.poly([(-7,y+1),(-6,y-3),(-3,y-5),(2,y-5),(6,y-3),(7,y+1)],1)
        c.poly([(-5,y),(-4,y-3),(-2,y-4),(2,y-4),(5,y)],5)
        c.line([(-4,y),(4,y)],12);c.rect((-3,y-3,-2,y-2),14);c.dot((2,y-3),14)


def _bandit(c):
    c.shadow(4);c.feet(3,0,11)
    y=1 if c.pose=='tell' else 0
    c.poly([(-5,-1),(-4,-8),(-2,-11),(2,-11),(4,-8),(5,-1)],1)
    c.poly([(-3,-2),(-2,-8),(2,-8),(3,-2)],4)
    c.volume((-5,-14+y,5,-6+y),3,5,2)
    c.rect((-4,-11+y,4,-8+y),15);c.eyes(0,-10+y,2)
    c.line([(-4,-6),(-6,-4)],1,2);c.line([(4,-6),(6,-4)],1,2)
    c.line([(-2,-4),(2,-4)],12)


def _weapon(c,kind,behind=False):
    p=c.pose;face=c.face
    attack=p=='attack';tell=p=='tell'
    if (face=='n')!=behind:return
    if kind=='BOW_MOBLIN':
        x=7 if face!='w' else -7
        c.line([(x,-19),(x+2,-16),(x+3,-12),(x+2,-8),(x,-6)],1,2)
        c.line([(x,-18),(x+1,-15),(x+2,-12),(x+1,-9),(x,-7)],11)
        c.line([(x,-18),(x-2 if tell else x,-12),(x,-7)],7)
        if tell:c.line([(x-4,-12),(x+5,-12)],11);c.poly([(x+5,-12),(x+2,-14),(x+2,-10)],15)
    elif kind=='SPEAR_MOBLIN':
        x=8 if face!='w' else -8
        if face in ('n','s'):
            y0=-29 if attack and face=='n' else -23;y1=-1 if face=='s' and attack else -3
            c.line([(x,y0),(x,y1)],1,3);c.line([(x,y0+2),(x,y1)],11)
            tipy=y1 if face=='s' else y0
            c.poly([(x-2,tipy+3 if face=='n' else tipy-3),(x,tipy-1 if face=='n' else tipy+1),(x+2,tipy+3 if face=='n' else tipy-3)],15)
        else:
            end=13 if attack else 11
            c.line([(-6,-13),(end,-13)],1,3);c.line([(-5,-14),(end-2,-14)],11)
            c.poly([(end-2,-16),(end+1,-13),(end-2,-10)],15)
    elif kind in ('DARK_NUT','KEATON'):
        hand=(6,-12);length=12 if kind=='DARK_NUT' else 7
        if tell:tip=(11,-25)
        elif attack:
            tip={'n':(0,-29),'e':(14,-13),'s':(2,-1),'w':(-14,-13)}[face]
        else:tip=(11,-8)
        if face=='w' and not attack:hand=(-hand[0],hand[1]);tip=(-tip[0],tip[1])
        c.line([hand,tip],1,3);c.line([(hand[0],hand[1]-1),(tip[0],tip[1]-1)],15 if kind=='DARK_NUT' else 11)
        c.line([(hand[0]-2,hand[1]+1),(hand[0]+2,hand[1]-1)],12)
    elif kind in ('BALL_CHAIN_SOLIDER','ENEMY_4D'):
        x=7 if face!='w' else -7
        c.line([(x-1,-14),(x+2,-11),(x+2,-8)],1,3)
        c.rect((x,-12,x+2,-10),11);c.line([(x+2,-9),(x+3,-7)],7)
    elif kind.startswith('WIZZROBE'):
        x=8 if face!='w' else -8
        c.line([(x,-3),(x,-24)],1,3);c.line([(x,-4),(x,-23)],11)
        if kind=='WIZZROBE_FIRE':
            c.poly([(x-3,-23),(x-3,-26),(x,-30),(x+1,-27),(x+3,-28),(x+3,-23)],1)
            c.poly([(x-1,-24),(x-1,-26),(x,-28),(x+2,-25)],13);c.dot((x,-25),15)
        elif kind=='WIZZROBE_ICE':
            c.poly([(x,-30),(x+3,-26),(x,-22),(x-3,-26)],1)
            c.line([(x,-28),(x,-24)],15);c.line([(x-1,-27),(x+1,-25)],7)
        else:
            c.line([(x-2,-24),(x+2,-25),(x+2,-29),(x-1,-30),(x-3,-28)],1,3)
            c.line([(x-2,-25),(x+1,-26),(x+1,-28),(x-1,-29)],15)
        if p=='attack':
            c.line([(x-3,-23),(x-5,-20),(x-3,-18)],13)


def _humanoid(c,kind):
    p=c.pose;iswiz=kind.startswith('WIZZROBE')
    if p=='buried' and iswiz:
        c.line([(-5,-1),(0,-3),(5,-1)],12);return
    c.shadow(8)
    if p=='tell':c.dy=2
    elif p=='attack':c.dx=c.side;c.dy=0
    _weapon(c,kind,True)
    # Feet remain planted; the waist and shoulders rotate over them.
    waist=-9;step=c.step
    if iswiz:
        c.poly([(-5,-18),(4,-18),(8,-3),(4,-2),(1,-4),(-3,-2),(-8,-3)],1)
        c.poly([(-4,-17),(3,-17),(5,-3),(0,-3),(-5,-2)],5 if kind=='WIZZROBE_FIRE' else 6 if kind=='WIZZROBE_ICE' else 4)
        c.line([(-3,-15),(-4,-5)],7);c.line([(2,-14),(4,-4)],3)
        c.line([(-5,-14),(-8,-11),(-9,-7)],1,3);c.line([(4,-14),(7,-12),(8,-7)],1,3)
        if p in ('tell','attack'):c.line([(-7,-12),(-10,-17),(-11,-18)],7,2)
        c.poly([(-7,-15),(-6,-23),(-2,-28),(3,-26),(6,-23),(7,-15),(3,-12),(-3,-12)],1)
        c.poly([(-5,-16),(-4,-22),(-1,-26),(3,-24),(5,-21),(5,-16)],5)
        c.line([(-4,-21),(-1,-25),(1,-25)],7)
        if c.face!='n':
            c.poly([(-4,-18),(-3,-21),(3,-21),(4,-17),(2,-15),(-2,-15)],2)
            c.line([(-2,-18),(-1,-18)],14);c.line([(1,-18),(2,-18)],14)
        _weapon(c,kind);c.dx=c.dy=0;return
    # Distinct articulated legs and a transferred support foot.
    bodydy=c.dy;c.dy=0
    for s in (-1,1):
        off=step*s
        c.line([(s*3,-9),(s*(4+off),-5),(s*4+off,-1)],1,4)
        c.line([(s*3,-8),(s*4+off,-3)],9 if kind not in ('STALFOS','GOBDO') else 7,2)
        c.rect((s*4+off-2,-2,s*4+off+2,0),1)
        c.line([(s*4+off-1,-2),(s*4+off+1,-2)],11)
    c.dy=bodydy
    if kind=='STALFOS':
        c.line([(0,-20),(0,-8)],1,3);c.line([(0,-18),(0,-9)],7)
        for y in (-16,-13,-10):c.line([(-4,y),(0,y+1),(4,y)],15)
        c.line([(-4,-17),(-7,-14),(-8,-10)],1,3);c.line([(4,-17),(7,-14),(8,-10)],1,3)
        c.line([(-5,-16),(-7,-13)],7);c.line([(5,-16),(7,-13)],7)
        c.volume((-5,-27,5,-18),7,15,5)
        if c.face!='n':
            c.rect((-3,-24,-1,-22),1);c.rect((1,-24,3,-22),1)
            c.dot((0,-21),1);c.line([(-3,-19),(3,-19)],1)
            c.line([(-2,-20),(-2,-18)],15);c.line([(2,-20),(2,-18)],15)
        if c.form:c.line([(-4,-26),(3,-26)],12)
        if p=='attack':c.line([(7,-12),(10,-16),(11,-18)],15,2)
    elif kind=='GOBDO':
        c.poly([(-5,-19),(5,-19),(6,-9),(3,-7),(-3,-7),(-6,-10)],1)
        c.rect((-4,-18,4,-10),7)
        for y in (-17,-13,-10):c.line([(-4,y),(4,y+1)],10)
        c.line([(-5,-17),(-8,-13),(-8,-8)],1,3);c.line([(5,-17),(8,-13),(8,-8)],1,3)
        c.line([(-7,-13),(-7,-9)],7,2);c.line([(7,-13),(7,-9)],7,2)
        c.volume((-5,-27,5,-18),7,15,5)
        for y in (-25,-22,-19):c.line([(-4,y),(4,y+1)],10)
        if c.face!='n':c.rect((-3,-23,3,-21),1);c.dot((-2,-22),13);c.dot((2,-22),13)
    elif kind=='KEATON':
        c.poly([(-5,-18),(4,-18),(6,-9),(1,-7),(-6,-10)],1)
        c.poly([(-3,-17),(3,-17),(4,-10),(-1,-9),(-4,-11)],9)
        c.line([(-4,-12),(4,-11)],12)
        c.line([(-5,-16),(-8,-12),(-7,-8)],1,3);c.line([(4,-14),(7,-13),(8,-10)],1,3)
        c.poly([(-6,-18),(-6,-26),(-8,-29),(-2,-27),(2,-27),(7,-30),(6,-21),(3,-17)],1)
        c.poly([(-4,-20),(-4,-25),(-2,-24),(2,-25),(4,-27),(4,-21),(1,-18)],10)
        if c.face!='n':
            c.line([(-4,-23),(-1,-22)],1);c.line([(1,-22),(4,-23)],1)
            c.poly([(-2,-20),(0,-18),(2,-20)],1)
        c.line([(-3,-17),(-6,-15),(-9,-17)],12,2)
    elif kind in ('BOW_MOBLIN','SPEAR_MOBLIN'):
        c.poly([(-6,-18),(5,-18),(7,-10),(3,-7),(-5,-8),(-7,-12)],1)
        c.poly([(-4,-17),(4,-17),(5,-11),(1,-9),(-5,-10)],5)
        c.line([(-5,-10),(5,-10)],11)
        c.line([(-6,-16),(-9,-12),(-8,-8)],1,3);c.line([(5,-16),(8,-12),(8,-8)],1,3)
        c.volume((-7,-27,6,-17),9,11,8)
        c.poly([(-5,-25),(-8,-29),(-2,-27)],1);c.poly([(3,-26),(7,-29),(6,-23)],1)
        if c.face!='n':
            c.volume((-4+c.side*2,-22,4+c.side*2,-17),10,11,8)
            c.dot((-1+c.side*2,-20),1);c.dot((2+c.side*2,-20),1)
            c.eyes(0,-24,3)
            c.line([(-5,-20),(-4,-17)],15);c.line([(5,-20),(4,-17)],15)
    else:
        # Armored knights and chain guards share a coherent metal material,
        # with distinct helmets, stance, shoulders and chest construction.
        chain=kind in ('BALL_CHAIN_SOLIDER','ENEMY_4D')
        c.poly([(-7,-20),(6,-20),(8,-11),(4,-7),(-5,-8),(-8,-12)],1)
        c.poly([(-5,-19),(4,-19),(5,-11),(1,-9),(-5,-11)],9 if chain else 4+c.form%3)
        c.line([(-5,-18),(-3,-18),(-3,-12)],11)
        c.line([(-5,-10),(5,-10)],12)
        c.line([(-7,-17),(-10,-14),(-9,-9)],1,4);c.line([(7,-17),(10,-14),(9,-9)],1,4)
        c.line([(-9,-14),(-9,-11)],11);c.line([(9,-14),(9,-11)],7)
        c.volume((-6,-28,6,-18),9 if chain else 4,11 if chain else 6,8 if chain else 3)
        if chain:
            c.rect((-5,-25,5,-23),2)
            for x in (-3,0,3):c.dot((x,-24),15)
            if kind=='ENEMY_4D':
                c.poly([(-6,-26),(-8,-29),(-3,-28)],1);c.line([(-5,-27),(4,-27)],12)
            else:c.rect((-3,-29,3,-28),11)
        elif c.face=='n':
            c.line([(-3,-25),(3,-25)],7)
            c.poly([(-3,-17),(0,-20),(3,-17),(0,-14)],12);c.dot((0,-17),14)
        else:
            c.rect((-4,-25,4,-22),2);c.line([(-3,-24),(3,-24)],14)
            c.line([(0,-22),(0,-19)],11)
            if c.form>=2:c.poly([(-5,-26),(-7,-30),(-2,-28)],12);c.poly([(5,-26),(7,-30),(2,-28)],12)
        if not chain:
            # The shield stays on the facing side; the rear jewel remains
            # visible in a north-facing back view instead of a pasted shield.
            if c.face=='n':
                c.line([(-6,-23),(-8,-21),(-8,-18)],11)
            else:
                sx=-7 if c.face!='w' else 7
                c.poly([(sx-4,-17),(sx+3,-17),(sx+4,-10),(sx,-6),(sx-4,-10)],1)
                c.poly([(sx-2,-15),(sx+1,-15),(sx+2,-11),(sx,-9),(sx-2,-11)],9)
                c.line([(sx-2,-16),(sx+1,-16)],15)
    _weapon(c,kind)
    c.dx=c.dy=0


def _statue(c,eye=False):
    p=c.pose;c.shadow(8)
    c.feet(6,0,10)
    y=2 if p=='tell' else -1 if p=='attack' else 0;c.dy=y
    c.poly([(-8,-18),(-5,-21),(5,-21),(8,-18),(9,-8),(5,-4),(-5,-4),(-9,-8)],1)
    c.poly([(-6,-17),(-4,-19),(4,-19),(6,-16),(6,-8),(3,-6),(-5,-7)],8)
    c.line([(-5,-17),(-3,-18),(3,-18)],11)
    c.line([(-6,-13),(5,-13)],9);c.line([(-3,-19),(-3,-8)],9)
    if eye:
        c.volume((-7,-27,7,-15),8,10,9)
        if p in ('tell','attack','hurt'):
            c.ell((-5,-24,5,-17),1);c.ell((-4,-23,4,-18),15)
            c.ell((-2+c.side,-23,2+c.side,-18),12);c.line([(c.side,-22),(c.side,-19)],1)
        else:c.line([(-5,-21),(0,-20),(5,-21)],1,2)
        c.line([(-7,-12),(-10,-9),(-10,-5)],1,4);c.line([(7,-12),(10,-9),(10,-5)],1,4)
        c.line([(-10,-9),(-10,-6)],11);c.line([(10,-9),(10,-6)],10)
    else:
        c.poly([(-7,-19),(-7,-26),(-3,-29),(4,-29),(7,-25),(7,-19)],1)
        c.poly([(-5,-20),(-5,-25),(-2,-27),(3,-27),(5,-24),(5,-20)],10)
        if c.face!='n':c.rect((-4,-24,4,-22),2);c.dot((-2,-23),14);c.dot((2,-23),14)
        else:c.poly([(-3,-22),(0,-25),(3,-22),(0,-19)],12);c.dot((0,-22),14)
        c.line([(-7,-15),(-10,-12),(-10,-7)],1,4);c.line([(7,-15),(10,-12),(10,-7)],1,4)
        c.line([(-10,-12),(-10,-8)],10);c.line([(10,-12),(10,-8)],9)
    c.dy=0


def _tube(c,rupee=False):
    p=c.pose;c.shadow(8)
    if rupee and p=='buried':
        c.poly([(0,-12),(5,-7),(4,-2),(0,1),(-4,-2),(-5,-7)],1)
        c.poly([(0,-10),(3,-7),(2,-3),(0,-1),(-2,-3),(-3,-7)],11 if c.form==0 else 14 if c.form==1 else 7)
        c.line([(-1,-8),(0,-9),(0,-2)],15)
        if c.form:c.line([(-2,-5),(2,-5)],12)
        return
    y=-19 if p in ('attack','walk1') else -16 if p=='tell' else -22
    c.poly([(-8,0),(-9,-4),(-7,y+3),(-5,y),(5,y),(7,y+3),(9,-4),(8,0)],1)
    c.poly([(-6,-2),(-7,-5),(-5,y+3),(-3,y+1),(4,y+1),(5,-5),(7,-3),(6,-2)],5 if not rupee else 9 if c.form==0 else 6 if c.form==1 else 7)
    for yy in range(y+6,-2,4):
        c.line([(-6,yy),(-2,yy+1),(3,yy),(6,yy+1)],3 if not rupee else 8)
        c.line([(-5,yy-1),(-2,yy),(1,yy-1)],7 if not rupee else 11)
    c.ell((-7,y-1,7,y+7),1);c.ell((-5,y,5,y+5),15)
    c.ell((-4,y+1,4,y+4),1)
    c.line([(-3,y+1),(-2,y+2)],13);c.line([(2,y+2),(3,y+1)],13)
    if p=='attack':c.line([(-3,y+3),(0,y+7),(3,y+3)],13,2)
    if rupee:c.poly([(-2,-9),(0,-12),(2,-9),(0,-6)],12);c.dot((0,-10),14)


def _scissors(c):
    p=c.pose;c.shadow(7);c.feet(6,0,11)
    c.volume((-7,-18,7,-3),4,6,3)
    c.line([(0,-16),(0,-5)],12)
    # Pincers visibly open for preparation and project in front on attack;
    # the synthetic collision parts use the same forward 18px offset.
    hy=-17 if c.face=='n' else -9 if c.face=='s' else -12
    hx=c.side*7
    c.volume((hx-3,hy-3,hx+3,hy+3),9,11,8);c.eyes(hx,hy,2)
    spread=6 if p=='tell' else 2 if p=='attack' else 4
    if c.side:
        for s in (-1,1):
            c.line([(hx,hy+s*2),(hx+c.side*5,hy+s*spread),(hx+c.side*7,hy+s*2)],1,3)
            c.line([(hx+c.side*2,hy+s*3),(hx+c.side*5,hy+s*(spread-1))],11)
    else:
        ahead=-1 if c.face=='n' else 1
        for s in (-1,1):
            c.line([(s*2,hy),(s*spread,hy+ahead*5),(s*2,hy+ahead*8)],1,3)
            c.line([(s*3,hy+ahead*2),(s*(spread-1),hy+ahead*5)],11)


def _giant(c,electric=False):
    p=c.pose;c.shadow(12)
    if p in ('recover','hurt'):
        c.poly([(-13,0),(-14,-5),(-10,-12),(-3,-16),(5,-15),(12,-9),(14,-3),(12,0)],1)
        c.poly([(-11,-2),(-12,-5),(-8,-10),(-2,-14),(4,-12),(10,-7),(11,-2)],5)
        c.ell((-7,-13,7,-2),1);c.ell((-5,-12,5,-4),12)
        c.poly([(-3,-8),(0,-11),(3,-8),(0,-5)],14);c.dot((-1,-9),15)
        c.line([(-11,-5),(-7,-6)],7);c.line([(7,-4),(11,-3)],3)
        return
    top=-20 if p=='tell' else -29 if p=='attack' else -26
    c.poly([(-12,0),(-14,-5),(-11,-13),(-8,top+4),(-4,top),(4,top),
            (8,top+4),(11,-13),(14,-5),(12,0),(5,-1),(0,1),(-5,-1)],1)
    c.poly([(-10,-2),(-11,-6),(-8,-14),(-6,top+5),(-3,top+2),(3,top+2),
            (6,top+5),(9,-10),(11,-5),(10,-2),(5,-3),(0,-1),(-5,-3)],4 if electric else 6)
    c.poly([(-8,-7),(-7,-15),(-4,top+4),(0,top+3),(-1,-14),(-3,-8)],7)
    c.line([(-10,-3),(-5,-4),(-1,-2),(5,-4),(10,-3)],3)
    c.eyes(0,top+12,4)
    if electric:
        c.line([(-7,-5),(-3,-9),(-5,-13),(-1,-17),(1,-21)],13,2)
        c.line([(3,-5),(6,-9),(3,-12),(6,-17)],13)
        c.dot((-3,-9),15);c.dot((3,-12),15);c.dot((1,-20),14)
    else:
        c.line([(-7,-5),(-5,-10),(-2,-9),(0,-14),(3,-13),(6,-18)],12)
        c.dot((0,-14),14);c.dot((6,-18),14)
    c.line([(-3,top+5),(-1,top+4)],15)


def _big_oct(c,frozen=False):
    p=c.pose;c.shadow(13)
    top=-20 if p=='tell' else -26 if p=='attack' else -24
    for s in (-1,1):
        for yy,xx in ((-4,8),(-10,10)):
            c.poly([(s*4,yy-4),(s*xx,yy-3),(s*14,yy+1),(s*13,yy+4),
                    (s*9,yy+3),(s*7,yy),(s*4,yy)],1)
            c.line([(s*5,yy-2),(s*(xx+1),yy),(s*12,yy+2)],6,2)
            c.dot((s*11,yy+3),14)
    c.volume((-11,top,11,-4),5,7,3)
    c.poly([(-8,top+3),(-11,top-2),(-5,top+1),(0,top-3),(5,top+1),(10,top-2),(8,top+4)],1)
    c.line([(-6,top+2),(-2,top+1),(0,top-1)],12)
    c.eyes(0,top+11,5)
    if c.face=='n':
        c.line([(-4,-9),(0,-6),(4,-9)],3)
        c.poly([(-3,-4),(0,-1),(3,-4),(1,-7)],12)
    elif c.side:
        x=c.side*9
        c.poly([(x,-15),(x+c.side*5,-14),(x+c.side*5,-9),(x,-8)],1)
        c.line([(x+c.side,-13),(x+c.side*4,-12)],11)
        c.line([(x+c.side*4,-12),(x+c.side*4,-10)],1)
    else:
        c.volume((-5,-14,5,-5),9,11,8);c.ell((-3,-11,3,-7),1)
        if p=='attack':c.ell((-2,-10,2,-8),15)
    if frozen:
        # Ice is an attached pale shell with flat crystalline planes, not a
        # recolored living body. Purple core still shows through the cracks.
        c.poly([(-10,-8),(-12,-16),(-8,top+2),(-3,top-1),(3,top),
                (9,top+4),(11,-15),(8,-7),(4,-10),(0,-6),(-4,-10)],7)
        c.line([(-8,-16),(-5,top+4),(-1,top+2),(1,top+7)],15,2)
        c.line([(8,-13),(5,-16),(6,top+4)],15)
        c.line([(-2,-8),(0,-14),(-2,-18),(2,-20)],12)
        c.poly([(-3,-5),(0,-2),(3,-5),(0,-8)],13);c.dot((-1,-6),14)
        if c.face!='n':c.eyes(0,top+11,5)


def _part(frame):
    c=Canvas(16,16,'idle','s');name=frame
    if name=='orb':
        c.poly([(-6,-2),(-7,-7),(-4,-12),(1,-14),(5,-11),(7,-6),(4,-1),(0,1)],1)
        c.volume((-5,-11,5,-1),8,10,9)
        for x,y in ((-5,-9),(4,-10),(-6,-4),(5,-3)):
            c.poly([(x-1,y+1),(x,y-2),(x+2,y+1)],1);c.dot((x,y),15)
        c.line([(-3,-8),(0,-10),(2,-8)],11)
    elif name=='segment':
        c.volume((-6,-11,6,0),4,6,3)
        c.line([(-4,-8),(4,-8)],9);c.line([(-4,-4),(4,-4)],9)
        c.line([(-3,-9),(-1,-10)],11);c.line([(0,-8),(0,-3)],12)
    elif name=='tail':
        c.poly([(-4,0),(-6,-4),(-5,-9),(0,-14),(5,-9),(6,-4),(4,0)],1)
        c.poly([(-3,-2),(-4,-5),(-3,-9),(0,-12),(3,-8),(4,-4),(2,-2)],12)
        c.poly([(-2,-5),(0,-10),(2,-5),(0,-2)],14);c.dot((-1,-7),15)
    elif name=='bone':
        c.line([(-4,-3),(4,-11)],1,5);c.line([(-4,-3),(4,-11)],7,3)
        for x,y in ((-5,-3),(-3,-1),(3,-12),(5,-10)):
            c.ell((x-1,y-1,x+1,y+1),1);c.dot((x,y),15)
    elif name=='flame':_flame(c)
    elif name=='ice':
        c.poly([(0,-14),(5,-9),(3,-1),(-3,1),(-6,-6)],1)
        c.poly([(0,-13),(3,-8),(2,-3),(-2,-1),(-4,-6)],7)
        c.line([(0,-12),(-1,-4),(-3,-6)],15);c.line([(0,-8),(2,-5)],14)
    elif name=='gust':
        c.line([(-6,-3),(0,-1),(5,-4),(6,-8),(3,-11),(-2,-10),(-4,-6),(-1,-4),(2,-5)],1,3)
        c.line([(-6,-4),(0,-2),(4,-5),(5,-8),(2,-10),(-1,-9),(-3,-6),(0,-5),(2,-6)],7)
        c.line([(-5,-10),(-2,-13),(3,-13),(6,-11)],13)
    elif name=='bomb':_bomb(c)
    elif name=='stone':
        c.poly([(-5,-2),(-7,-7),(-3,-12),(2,-13),(6,-9),(6,-4),(2,0)],1)
        c.poly([(-4,-3),(-5,-7),(-2,-10),(2,-11),(4,-8),(4,-4),(1,-2)],9)
        c.line([(-3,-7),(-1,-10),(2,-9)],11);c.line([(0,-7),(3,-5)],8)
    elif name=='spore':
        c.poly([(-5,-3),(-6,-8),(-3,-12),(3,-12),(6,-7),(4,-2),(-1,0)],1)
        c.ell((-4,-10,4,-2),12);c.ell((-2,-9,2,-4),13)
        c.dot((-2,-8),15);c.line([(0,-11),(1,-14)],9)
    elif name=='mark':
        # A large ground target has no filled disk: it remains distinct from
        # pickups and ambient pinpricks without covering terrain underneath.
        c.line([(-6,-3),(-7,-7),(-5,-10),(-2,-11)],1,3)
        c.line([(6,-3),(7,-7),(5,-10),(2,-11)],1,3)
        c.line([(-5,-3),(-6,-7),(-4,-9),(-2,-10)],14)
        c.line([(5,-3),(6,-7),(4,-9),(2,-10)],14)
        c.line([(-4,-1),(0,0),(4,-1)],1,3);c.line([(-3,-2),(0,-1),(3,-2)],13)
        c.line([(0,-8),(0,-4)],15)
    elif name=='fairy':
        for s in (-1,1):
            c.poly([(0,-7),(s*5,-12),(s*7,-8),(s*4,-4),(s*5,-1),(0,-4)],1)
            c.poly([(s,-7),(s*4,-10),(s*5,-7),(s*3,-5)],7)
        c.volume((-2,-10,2,-3),12,14,3);c.line([(0,-4),(0,-1)],15)
    return c.im


def paint(name,form,pose,face,bare=False,frozen=False):
    size=32 if name in LARGE or name in ('GIANT_GREEN','GIANT_ELECTRIC','BIG_OCTOROK') else 16
    c=Canvas(size,size,pose,face,form);c.bare=bare
    if name in ('BEETLE','HELMASAUR','SPIKED_BEETLE','SPINY_BEETLE','MULLDOZER','ROLLOBITE'):_beetle(c,name)
    elif name in ('KEESE','SMALL_PESTO','PESTO','CROW','TAKKURI','PEAHAT','BOMB_PEAHAT'):_flyer(c,name)
    elif name in ('TEKTITE','TEKTITE_GOLDEN'):_tektite(c)
    elif name in ('MINI_SLIME','SLIME','CHUCHU','ROCK_CHUCHU','SPINY_CHUCHU'):_jelly(c,name)
    elif name in ('OCTOROK','OCTOROK2','OCTOROK_GOLDEN'):_octorok(c,name)
    elif name in ('ROPE','ROPE_GOLDEN'):_rope(c)
    elif name in LARGE and name not in ('ARMOS','EYEGORE','LIKE_LIKE','RUPEE_LIKE','SCISSORS_BEETLE'):_humanoid(c,name)
    elif name=='ARMOS':_statue(c)
    elif name=='EYEGORE':_statue(c,True)
    elif name in ('LIKE_LIKE','RUPEE_LIKE'):_tube(c,name=='RUPEE_LIKE')
    elif name=='SCISSORS_BEETLE':_scissors(c)
    elif name in ('BOBOMB','BOMBAROSSA'):_bomb(c,name=='BOMBAROSSA')
    elif name=='LEEVER':_leever(c)
    elif name in ('MOLDORM','MOLDWORM','MADDERPILLAR'):_worm(c,name)
    elif name in ('GHINI','ENEMY_50'):_ghost(c,name=='ENEMY_50')
    elif name in ('CLOUD_PIRANHA','LAKITU'):_cloud(c,name)
    elif name in ('WISP','SPARK'):_spark(c,name=='WISP')
    elif name in ('FIREBALL_GUY','MINI_FIREBALL_GUY'):_flame(c,name=='MINI_FIREBALL_GUY')
    elif name=='PUFFSTOOL':_mushroom(c)
    elif name=='ACRO_BANDIT':_bandit(c)
    elif name in ('GIANT_GREEN','GIANT_ELECTRIC'):_giant(c,name=='GIANT_ELECTRIC')
    elif name=='BIG_OCTOROK':_big_oct(c,frozen)
    else:raise ValueError(('unpainted family',name,form))
    if 'GOLDEN' in name:
        # Existing fx/gold bank: ivory12, warm brass8..11, wine15 for rot.
        lookup={0:0,1:1,2:2,3:7,4:8,5:9,6:10,7:11,8:3,9:5,10:6,11:9,12:15,13:15,14:12,15:12}
        c.im.putdata([lookup[i] for i in c.im.getdata()])
    return c.im


def rows(image):
    return [''.join(format(image.getpixel((x,y)),'x') for x in range(image.width)) for y in range(image.height)]


def build_sheets():
    sheets=[]
    specs=[(e['name'],e['form']) for e in ENTRIES]+[('GIANT_GREEN',0),('GIANT_ELECTRIC',0),('BIG_OCTOROK',0)]
    for name,form in specs:
        frames={}
        suffixes=('', 'bare_') if name in ('HELMASAUR','PUFFSTOOL','LAKITU','ROCK_CHUCHU') else ('','frozen_') if name=='BIG_OCTOROK' else ('',)
        for suffix in suffixes:
            for pose in POSES:
                for face in FACES:
                    im=paint(name,form,pose,face,bare=suffix=='bare_',frozen=suffix=='frozen_')
                    assert im.mode=='P' and im.size in ((16,16),(32,32))
                    assert set(im.getdata())<=set(range(16))
                    frames[suffix+pose+'_'+face]=rows(im)
        sheetname='legacy_'+name.lower()+(('_'+str(form)) if not name.startswith(('GIANT_','BIG_')) else '')
        # Sheet names of the three bosses omit a source form suffix by contract.
        sheets.append(dict(name=sheetname,w=im.width,h=im.height,pal='fx' if 'GOLDEN' in name else 'blight',frames=frames))
    partnames=('orb','segment','tail','bone','flame','ice','gust','bomb','stone','spore','mark','fairy')
    sheets.append(dict(name='legacy_parts',w=16,h=16,pal='blight',frames={name:rows(_part(name)) for name in partnames}))
    assert len(sheets)==75 and len({s['name'] for s in sheets})==75
    return sheets


def export(directory):
    import palettes
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    banks=dict(palettes.OBJ_PALETTES);sheets=build_sheets()
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',10)
    cellw=176;cellh=104;cols=6;rowsn=(len(sheets)+cols-1)//cols
    board=Image.new('RGB',(cols*cellw,40+rowsn*cellh),'#16201e');d=ImageDraw.Draw(board);d.fontmode='1'
    d.text((9,7),'ORIGINAL HANDOFF BESTIARY / NATIVE SOURCE ART / NOT EMULATOR EVIDENCE',font=font,fill='#f0d898')
    manifest=[]
    for i,sh in enumerate(sheets):
        x=(i%cols)*cellw;y=40+(i//cols)*cellh
        label=sh['name'].replace('legacy_','')
        d.text((x+4,y),label,font=font,fill='#e8d0a0')
        chosen=('idle_s','tell_s','attack_s','recover_s') if sh['name']!='legacy_parts' else ('orb','segment','tail','mark')
        for k,frame in enumerate(chosen):
            image=Image.new('P',(sh['w'],sh['h']),0)
            image.putdata([int(q,16) for row in sh['frames'][frame] for q in row])
            rgba=R.rgba(image,banks[sh['pal']])
            board.paste(rgba,(x+5+k*42,y+19),rgba)
            if k<2:
                im2=rgba.resize((sh['w']*2,sh['h']*2),Image.Resampling.NEAREST)
                board.paste(im2,(x+5+k*75,y+46),im2)
        fn=directory/(sh['name']+'.png')
        # An exact indexed source strip; all colors are existing RGB555 inks.
        images=[]
        for frame,rr in sh['frames'].items():
            im=Image.new('P',(sh['w'],sh['h']),0);im.putdata([int(q,16) for row in rr for q in row]);images.append(im)
        strip=Image.new('P',(sh['w']*4,sh['h']*((len(images)+3)//4)),0)
        flat=[channel for color in banks[sh['pal']] for channel in R.rgb(color)];strip.putpalette(flat+[0]*(768-len(flat)))
        for j,im in enumerate(images):strip.paste(im,((j%4)*sh['w'],(j//4)*sh['h']))
        strip.info['transparency']=0;strip.save(fn)
        manifest.append(dict(sheet=sh['name'],canvas=[sh['w'],sh['h']],palette=sh['pal'],frames=list(sh['frames']),
                             frame_tiles=sh['w']*sh['h']//64,sha256=hashlib.sha256(fn.read_bytes()).hexdigest(),file=fn.name))
    board.save(directory/'bestiary-source.png')
    (directory/'manifest.json').write_text(json.dumps(dict(kind='Original native source art; not emulator output.',
        preserved_old_art=True,palette_changes=False,sheets=manifest),indent=2)+'\n')
    return manifest

if __name__=='__main__':
    import sys
    export(sys.argv[1] if len(sys.argv)>1 else '/workspace/setup/handoff-enemies')
