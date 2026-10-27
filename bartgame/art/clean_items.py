"""Plain, legible item silhouettes at the GBA's native resolutions.

The same material colours and shapes serve the HUD, inventory, item-get,
pickups and resident weapon sheets. No icon carries its own frame, halo,
jewel border or ornamental sparkle. The engine's frame contracts stay intact.
"""
from px import Canvas

PALETTE = ['#000000', '#182028', '#384850', '#809898', '#e8e8d0',
           '#a08050', '#604830', '#b08030', '#e8c060', '#d8c898',
           '#e88838', '#487858', '#90b888', '#786898', '#e89898', '#c84848']
# 0 transparent; 1 ink; 2-4 steel; 5-6 leather/wood; 7-8 brass;
# 9 wax/parchment; 10 flame; 11-12 cloth/leaf; 13 violet; 14-15 heart.
PALETTES = {name: list(PALETTE) for name in ('gear', 'items', 'pick', 'icons')}


class Draw:
    """Coordinates are in a 16-unit square; edges are native hard pixels."""
    def __init__(self, size):
        self.size = size
        self.scale = size / 16
        self.c = Canvas(size, size)

    def poly(self, points, color):
        pts = [(x*self.scale, y*self.scale) for x,y in points]
        for y in range(self.size):
            for x in range(self.size):
                px,py=x+.5,y+.5
                inside=False
                for i,(ax,ay) in enumerate(pts):
                    bx,by=pts[(i+1)%len(pts)]
                    if (ay>py)!=(by>py) and px < (bx-ax)*(py-ay)/(by-ay)+ax:
                        inside=not inside
                if inside:self.c.set(x,y,color)

    def rect(self,x0,y0,x1,y1,color):
        self.poly([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],color)

    def oval(self,cx,cy,rx,ry,color):
        self.c.ellipse(cx*self.scale,cy*self.scale,rx*self.scale,ry*self.scale,color)

    def line(self,points,color,width=1):
        width=max(1,round(width*self.scale))
        for (ax,ay),(bx,by) in zip(points,points[1:]):
            ax,ay,bx,by=[v*self.scale for v in (ax,ay,bx,by)]
            steps=max(round(abs(bx-ax)),round(abs(by-ay)),1)
            for k in range(steps+1):
                x=round(ax+(bx-ax)*k/steps);y=round(ay+(by-ay)*k/steps)
                self.c.rect(x-(width-1)//2,y-(width-1)//2,x+width//2,y+width//2,color)

    def done(self):
        self.c.outline(1)
        return self.c.rows()


def sword(size):
    d=Draw(size)
    d.poly([(6,10),(12.5,2.5),(14,2),(13.5,4),(8,12)],3)
    d.poly([(6,10),(12.5,2.5),(14,2),(7,11)],4)
    d.line([(4.5,11),(7.5,14)],6,1.5)
    d.line([(4.5,9.5),(9.5,14.5)],7)
    d.line([(5,9.5),(9.5,14)],8)
    return d.done()


def shield(size,side=False,back=False):
    d=Draw(size)
    if side:
        d.poly([(6,3),(9,3),(10,6),(9,11),(7,14),(6,12)],3)
        d.poly([(7,4),(8.5,4),(9,7),(8,12),(7,13)],5)
    else:
        shape=[(4,3),(12,3),(13,6),(11.5,11),(8,14),(4.5,11),(3,6)]
        d.poly(shape,3)
        d.poly([(4.5,4),(11.5,4),(12,6),(10.5,10.5),(8,12.5),(5.5,10.5),(4,6)],5)
        d.poly([(8,4),(11.5,4),(12,6),(10.5,10.5),(8,12.5)],6)
        if back:
            d.rect(6,6,10,7,2);d.rect(6,9,10,10,2)
        else:
            d.line([(4.5,4),(11.5,4)],4)
    return d.done()


def bomb(size,phase=0):
    d=Draw(size)
    d.oval(8,10,4.4,4.4,2)
    d.oval(7.5,9.5,3.8,3.8,13)
    d.oval(6.7,8,1.1,.7,4)
    d.rect(6.5,5,9,6.5,6)
    d.line([(8,5),(8.5,3),(10,2.5)],9)
    d.rect(10,2 if not phase else 1.5,11,3,10)
    return d.done()


def candle(size):
    d=Draw(size)
    d.rect(6.5,6,10,13.5,9)
    d.rect(6.5,6,7.5,13,4)
    d.line([(8,5.5),(8,6.5)],6)
    d.poly([(8.5,1.5),(6.5,4),(7,5.5),(9,6),(10,4.5)],10)
    d.poly([(8.5,3),(7.5,4.5),(8.5,5.5),(9,4.5)],8)
    d.rect(5,13,11.5,14,7)
    return d.done()


def cloak(size):
    d=Draw(size)
    d.poly([(6,3),(10,3),(11,5),(13.5,13.5),(9,12.5),(8,14),(6.5,12.5),(2.5,13.5),(5,5)],11)
    d.poly([(8,4),(10,4),(11,7),(12,12),(9,11.5),(8,13)],2)
    d.poly([(6,4),(7.5,4),(6,11.5),(4,12)],12)
    d.line([(6,3),(8,4),(10,3)],12)
    d.rect(7.5,3.5,8.5,4.5,8)
    return d.done()


def key(size):
    d=Draw(size)
    d.oval(7,4.5,2.7,2.7,8)
    d.oval(7,4.5,1.2,1.2,1)
    d.rect(6.2,7,7.8,13.8,8)
    d.rect(7,10.5,10.5,12,8)
    d.rect(9,12,10.5,13.5,8)
    d.rect(5.5,3,6.5,4,4)
    return d.done()


def heart(size,piece=False):
    d=Draw(size)
    shape=[(8,4.7),(10,3.3),(12.5,3.7),(14,6),(13.5,8.5),(8,14),(2.5,8.5),(2,6),(3.5,3.7),(6,3.3)]
    d.poly(shape,3 if piece else 15)
    if piece:
        d.poly([(8,5),(8,9),(5,10.5),(3.5,8),(3,6),(4,4.8),(6,4.5)],15)
    else:
        d.poly([(3,6),(4,4.5),(6,4.3),(7,5.5),(4.5,6.5)],14)
    return d.done()


def coin(size,big=False):
    d=Draw(size)
    if big:
        # A small plain purse rather than an enormous jewel or medallion.
        d.poly([(5,5),(11,5),(12.5,9),(12,13),(10,14),(5,14),(3.5,12),(3.5,9)],5)
        d.poly([(9,6),(11,6),(12,9),(11.5,12.5),(9,13.5)],6)
        d.line([(5,6),(11,6)],7)
        d.poly([(5,3),(7,4),(9,4),(11,3),(10,5),(6,5)],6)
        d.oval(10.5,11.5,2,2,8)
    else:
        d.oval(8,8.5,4.5,4.8,7)
        d.oval(7.5,8,3.6,4,8)
        d.line([(8,5.5),(8,10.5)],7)
        d.line([(5,5),(6,4)],4)
    return d.done()


def relic(size):
    d=Draw(size)
    d.line([(7,3),(7,1.5),(9,1.5),(9,3)],7)
    d.poly([(8,3),(11.5,6),(11,11),(8,14),(5,11),(4.5,6)],7)
    d.poly([(8,4.5),(10,6.5),(9.5,10.5),(8,12.2),(6.5,10),(6,6.5)],3)
    d.poly([(8,4.5),(8,11.5),(6.5,10),(6,6.5)],4)
    return d.done()


def gauntlet(size):
    d=Draw(size)
    d.poly([(4,4),(5.5,4),(5.5,2.5),(7,2.5),(7,2),(8.5,2),(8.5,3),(10,3),(10,6.5),(11.5,5.5),(13,7),(10.5,11),(5,11),(4,8)],5)
    d.poly([(8.5,3),(10,3),(10,6.5),(11.5,5.5),(13,7),(10.5,11),(8.5,11)],6)
    d.rect(5,11,10.5,14,3)
    d.rect(5,11,6.5,13.5,4)
    d.line([(5.5,4),(5.5,7)],6)
    return d.done()


def bow(size):
    d=Draw(size)
    d.line([(6,2),(9.5,3),(11.5,5.5),(12,8),(11.5,10.5),(9.5,13),(6,14)],6,1.6)
    d.line([(6,2),(9,3),(11,5.5),(11.5,8),(11,10.5),(9,13),(6,14)],5)
    d.line([(6,2),(6,14)],4)
    d.rect(10.5,6.5,12,9.5,7)
    return d.done()


def hubcap(size):
    d=Draw(size)
    d.oval(8,8,6,6,2)
    d.oval(7.7,7.7,5.3,5.3,3)
    for x in (5,8,11):d.rect(x-.5,4.5,x+.5,11.5,2)
    d.line([(4,4.5),(5.5,3.5)],4)
    return d.done()


def map_icon(size):
    d=Draw(size)
    d.poly([(3,4),(6.5,3),(10,4),(13,3),(13,12),(10,13),(6.5,12),(3,13)],9)
    d.poly([(3,4),(6.5,3),(6.5,12),(3,13)],4)
    d.line([(6.5,3.5),(6.5,11.5)],5)
    d.line([(4,8),(5,7),(8,8),(10,6),(12,7)],11)
    return d.done()


def compass(size):
    d=Draw(size)
    d.oval(8,8.5,5,5,7)
    d.oval(8,8.5,4,4,9)
    d.poly([(10.5,4.5),(8.5,9),(5.5,12.5),(7.5,8)],3)
    d.poly([(10.5,4.5),(7.5,8),(8.5,9)],15)
    d.rect(7.5,1.5,8.5,3.5,8)
    return d.done()


def grail(size):
    d=Draw(size)
    d.poly([(3.5,3),(12.5,3),(11.5,7),(9,9),(7,9),(4.5,7)],8)
    d.poly([(8,4),(11.5,4),(10.5,7),(8,8)],7)
    d.rect(7,9,9,12.5,7)
    d.rect(5,12.5,11,14,8)
    return d.done()


def arrow(size,count=1,direction='n'):
    d=Draw(size)
    n=1 if count==1 else 2 if count==5 else 3
    for i in range(n):
        x=8+(i-(n-1)/2)*3
        d.line([(x,12.5),(x,4)],5)
        d.poly([(x,2),(x-2,5),(x+2,5)],3)
        d.line([(x-1.5,11),(x,12),(x+1.5,11)],4)
    rows=d.done()
    if direction=='s':return rows[::-1]
    if direction=='e':return [''.join(rows[size-1-x][y] for x in range(size)) for y in range(size)]
    return rows


def blade(frame):
    d=Draw(16)
    if frame=='blade_s':
        d.rect(7,5,9,13,3);d.poly([(7,13),(9,13),(8,15)],3)
        d.rect(7,5,8,13,4);d.rect(7,1,9,4,6);d.rect(5,4,11,5,8)
    elif frame=='blade_e':
        d.rect(5,7,13,9,3);d.poly([(13,7),(15,8),(13,9)],3)
        d.rect(5,7,13,8,4);d.rect(1,7,4,9,6);d.rect(4,5,5,11,8)
    else:
        d.poly([(5,6),(6,5),(13,12),(14,14),(12,13)],3)
        d.line([(6,6),(12,12)],4)
        d.line([(2,2),(4,4)],6,1.5);d.line([(2,5),(5,2)],8)
    return d.done()


def make(name,size):
    if name=='none':return ['.'*size]*size
    if name in ('bombs','bomb_pickup'):return bomb(size,name=='bomb_pickup')
    if name=='lamp':return candle(size)
    if name=='cloak':return cloak(size)
    if name=='key':return key(size)
    if name in ('heart','heart_piece','heart_container'):return heart(size,name=='heart_piece')
    if name in ('gilt','gilt_big'):return coin(size,name=='gilt_big')
    if name=='relic':return relic(size)
    if name=='gauntlet':return gauntlet(size)
    if name=='bow':return bow(size)
    if name=='hubcap':return hubcap(size)
    if name=='map':return map_icon(size)
    if name=='astrolabe':return compass(size)
    if name=='sword':return sword(size)
    if name=='shield':return shield(size)
    if name=='grail':return grail(size)
    if name.startswith('arrow'):return arrow(size,int(name[5:]))
    if name=='spark':
        d=Draw(size);d.poly([(8,3),(9,7),(13,8),(9,9),(8,13),(7,9),(3,8),(7,7)],8);return d.done()
    raise ValueError('missing clean item '+name)


def apply(sheets):
    """Change pixels only; keep sheet names, bounds, order and palette slots."""
    for s in sheets:
        name=s['name']
        if name in ('icon32','items','pick32'):
            s['frames']={n:make(n,s['w']) for n in s['frames']}
        elif name=='sword':s['frames']={n:blade(n) for n in s['frames']}
        elif name=='shield':s['frames']={n:shield(16,n=='side',n=='back') for n in s['frames']}
        elif name=='arrow':
            # This sheet shares FX's palette, so map the clean materials into
            # that existing palette rather than recolouring unrelated effects.
            import pack
            def rgb(h):return tuple(int(h[i:i+2],16) for i in (1,3,5))
            pal=pack.GROUPS[s['pal']]
            lut={'.':'.'}
            for i,h in enumerate(PALETTE[1:],1):
                c=rgb(h);k=min(range(1,16),key=lambda j:sum((c[t]-rgb(pal[j])[t])**2 for t in range(3)))
                lut['%x'%i]='%x'%k
            s['frames']={n:[''.join(lut[ch] for ch in row) for row in arrow(16,direction=n)] for n in s['frames']}
        if name in ('icon32','items','pick32','sword','shield','arrow'):
            for n,rows in s['frames'].items():
                assert len(rows)==s['h'] and all(len(row)==s['w'] for row in rows),(name,n)
