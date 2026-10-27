"""Bloom's separately anchored weapon sweeps and held tools.

Only one 32px frame is streamed to OBJ at a time. The sword's pale sweep
uses the same inclusive reach rectangles as player_sword_box; the south
canvas has eight rows above that rectangle for the non-cutting grip. There
are no detached dust, leaf or sparkle particles in these action frames.
"""
import math
from px import Canvas
from clean_items import Draw

# Canvas origin relative to each sword hitbox minimum corner. This is also
# useful to preview the contact area independently of the non-cutting grip.
SWORD_DRAW_OFFSET = {'n': (0, 0), 'e': (0, 0), 's': (0, -8), 'w': (0, 0)}
SWORD_REACH = {'n': (0, 0, 27, 20), 'e': (0, 0, 18, 24),
               's': (0, 8, 27, 26), 'w': (0, 0, 18, 24)}
# Every held-tool frame is drawn at Bloom's feet minus (16, 32).
TOOL_HAND = {'n': (23, 16), 'e': (26, 19), 's': (23, 23)}


def stroke(c, points, col, width=1):
    """A connected pixel stroke, with no anti-aliasing or isolated flecks."""
    d=Draw(32,native=True);d.c=c;d.line(points,col,width)


def arc_points(direction):
    x0,y0,x1,y1=SWORD_REACH[direction]
    w,h=x1-x0,y1-y0
    points=[]
    for i in range(41):
        a=-math.pi/2+math.pi*i/40
        if direction in ('n','s'):
            x=x0+w*(1+math.sin(a))/2
            y=y0+h*(1-math.cos(a)) if direction=='n' else y1-h*(1-math.cos(a))
        else:
            x=x1-w*(1-math.cos(a)) if direction=='e' else x0+w*(1-math.cos(a))
            y=y0+h*(1+math.sin(a))/2
        p=(round(x),round(y))
        if not points or p!=points[-1]:points.append(p)
    return points


def sword(direction, phase):
    """Three live swipes between a quiet wind-up and follow-through."""
    # East's mirror is exact, including the asymmetric western world box.
    if direction=='w':
        rs=sword('e',phase)
        return [r[:19][::-1]+'.'*13 for r in rs]
    c=Canvas(32,32)
    curve=arc_points(direction)
    x0,y0,x1,y1=SWORD_REACH[direction]
    if 1<=phase<=3:
        # A single restrained contour keeps the full outer reach visible;
        # the short cream leading segment travels with the steel blade.
        stroke(c,curve,2)
        q=(.82,.5,.18)[phase-1] if direction in ('n','s') else (.18,.5,.82)[phase-1]
        at=round(q*(len(curve)-1))
        # A tapered leading edge reads as a passing crescent, while the
        # quieter one-pixel remainder still describes the entire reach.
        back={'n':((x0+x1)/2,y1), 's':((x0+x1)/2,y0),
              'e':(x0,(y0+y1)/2)}[direction]
        for j in range(max(0,at-6),min(len(curve),at+7)):
            cx,cy=curve[j];dx,dy=back[0]-cx,back[1]-cy
            length=max(math.hypot(dx,dy),1)
            distance=abs(j-at)
            inset=3 if distance<3 else 2 if distance<5 else 1
            stroke(c,[(cx,cy),(round(cx+dx/length*inset),round(cy+dy/length*inset))],3)
            if distance<4:
                bright=max(0,inset-2)
                stroke(c,[(cx,cy),(round(cx+dx/length*bright),round(cy+dy/length*bright))],4)
        tip=curve[at]
    else:
        tip={'n':((26,7),(1,10)), 'e':((8,0),(12,23)), 's':((27,17),(0,18))}[direction][phase==4]
    pivots={'n':[(24,16),(24,16),(14,15),(4,16),(4,16)],
            'e':[(0,5),(0,5),(7,9),(0,13),(0,13)],
            's':[(24,1),(24,1),(14,8),(4,2),(4,2)]}
    px,py=pivots[direction][phase];tx,ty=tip
    dx,dy=tx-px,ty-py;length=max(math.hypot(dx,dy),1)
    ux,uy=dx/length,dy/length;vx,vy=-uy,ux
    # The brown grip and short brass guard make the blade intelligible even
    # at the back-facing flower, rather than a featureless white slash.
    grip=(px,py);guard=(px+ux*3,py+uy*3);base=(px+ux*4,py+uy*4)
    stroke(c,[grip,guard],1,4)
    stroke(c,[grip,guard],6,2)
    stroke(c,[(px-vx*.5,py-vy*.5),(guard[0]-vx*.5,guard[1]-vy*.5)],5)
    d=Draw(32,native=True);d.c=c
    d.poly([(base[0]-vx*1.5,base[1]-vy*1.5),
            (tx-ux*3-vx,ty-uy*3-vy),(tx,ty),
            (tx-ux*3+vx,ty-uy*3+vy),(base[0]+vx*1.5,base[1]+vy*1.5)],2)
    stroke(c,[base,(tx-ux,ty-uy)],3,2)
    stroke(c,[(base[0]-vx*.5,base[1]-vy*.5),(tx,ty)],4)
    stroke(c,[(guard[0]-vx*3,guard[1]-vy*3),(guard[0]+vx*3,guard[1]+vy*3)],7,2)
    stroke(c,[(guard[0]-vx*2,guard[1]-vy*2),(guard[0]+vx*2,guard[1]+vy*2)],8)
    # East/North fit entirely in their hit rectangles. Only the southern
    # non-cutting grip may sit above its contact rectangle.
    for y in range(32):
        for x in range(32):
            if x<x0 or x>x1 or y>y1 or (direction!='s' and y<y0):c.set(x,y,-1)
    return c.rows()


def bow(direction, phase):
    d=Draw(32,native=True)
    if direction=='n':
        limbs=[(16,21),(18,18),(21,16),(23,16),(26,17),(28,18),(30,21)]
        string=[(16,21),(23,23 if phase==0 else 21),(30,21)]
    elif direction=='s':
        limbs=[(16,18),(18,21),(21,23),(23,23),(26,22),(28,21),(30,18)]
        string=[(16,18),(23,16 if phase==0 else 18),(30,18)]
    else:
        limbs=[(21,11),(24,14),(26,17),(26,19),(25,23),(23,25),(21,27)]
        string=[(21,11),(18 if phase==0 else 21,19),(21,27)]
    d.line(string,3)
    d.line(limbs,1,3);d.line(limbs,5)
    hx,hy=TOOL_HAND[direction]
    d.rect(hx-1,hy-1,hx+1,hy+2,7);d.rect(hx-1,hy-1,hx,hy+1,8)
    return d.c.rows()


def lamp(direction, phase):
    d=Draw(32,native=True);hx,hy=TOOL_HAND[direction]
    d.rect(hx-2,hy-6,hx+2,hy,1)
    d.rect(hx-1,hy-5,hx+1,hy,9);d.rect(hx-1,hy-5,hx,hy,4)
    d.rect(hx-3,hy,hx+3,hy+1,7);d.rect(hx-2,hy,hx+2,hy+1,8)
    d.rect(hx,hy-8,hx+1,hy-6,6)
    lean=(-1,1,0)[phase]
    d.poly([(hx+lean,hy-13),(hx+2,hy-10),(hx+2,hy-8),
            (hx+1,hy-7),(hx-1,hy-7),(hx-2,hy-9),(hx-1,hy-11)],10)
    d.poly([(hx,hy-11),(hx+1,hy-9),(hx,hy-8),(hx-1,hy-9)],8)
    return d.c.rows()


def cape(direction, phase):
    d=Draw(32,native=True)
    if direction=='e':
        edge=[[(12,15),(17,17),(16,24),(10,29),(5,27),(9,23)],
              [(10,15),(17,18),(16,23),(9,27),(3,25),(6,22)],
              [(12,15),(17,17),(16,25),(11,30),(7,28),(10,24)]][phase]
        d.poly(edge,2)
        d.poly([(12,16),(15,18),(13,23),(7,26),(5,25),(10,22)],11)
        d.line([(12,17),(11,21),(8,24)],12)
    else:
        left=(8,4,7)[phase];right=32-left
        hem=(28,27,31)[phase]
        d.poly([(12,15),(20,15),(22,20),(right,hem-2),(right-3,hem),
                (19,hem-2),(16,hem),(12,hem-2),(left+2,hem),(left,hem-2),(10,20)],2)
        d.poly([(12,16),(19,16),(20,21),(right-2,hem-2),(20,hem-3),
                (16,hem-1),(12,hem-3),(left+2,hem-1),(10,21)],11)
        d.poly([(12,17),(14,17),(12,23),(left+3,hem-2),(left+2,hem-3),(10,21)],12)
    return d.c.rows()


FRAMES={}
for direction in ('n','e','s','w'):
    for phase in range(5):FRAMES['sword_%s%d'%(direction,phase)]=sword(direction,phase)
for tool,draw in (('bow',bow),('lamp',lamp),('cape',cape)):
    for direction in ('n','e','s'):
        for phase in range(3):FRAMES['%s_%s%d'%(tool,direction,phase)]=draw(direction,phase)
for name,rows in FRAMES.items():
    assert len(rows)==32 and all(len(row)==32 for row in rows),name
SHEETS=[{'name':'bloomfx','w':32,'h':32,'pal':'gear','frames':FRAMES}]
