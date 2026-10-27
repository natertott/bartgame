"""Original handheld item art: bold silhouettes and deliberate pixel clusters.

The 16px HUD/weapon sprites and 32px bag/reward sprites share materials, but
large tools have their own drawings rather than doubled HUD pixels. Lighting
comes from the upper left. No item carries a decorative frame or halo.
"""
from px import Canvas

PALETTE = ['#000000', '#182530', '#445468', '#91adb5', '#fff1cf',
           '#c18b50', '#75503b', '#ab7138', '#f4ce68', '#e5ce9e',
           '#ee8948', '#43745c', '#9cc985', '#7e79b0', '#f69b9b', '#cf4d60']
# 0 transparent; 1 ink; 2-4 steel; 5-6 leather/wood; 7-8 brass;
# 9 wax/parchment; 10 flame; 11-12 cloth/leaf; 13 violet; 14-15 heart.
PALETTES = {name: list(PALETTE) for name in ('gear', 'items', 'pick', 'icons')}


class Draw:
    """Hard pixel edges; small coordinates by default, native for large tools."""
    def __init__(self, size, native=False):
        self.size = size
        self.scale = 1 if native else size / 16
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
    d=Draw(size,native=True)
    if size==32:
        d.poly([(12,18),(24,5),(28,3),(26,9),(16,22)],3)
        d.poly([(12,18),(24,5),(28,3),(15,20)],4)
        d.line([(11,23),(7,27)],6,3)
        d.line([(10,23),(7,26)],5)
        d.line([(8,18),(18,26)],7,3)
        d.line([(8,17),(18,25)],8)
        d.line([(5,27),(7,29)],7,2)
    else:
        d.poly([(6,9),(12,3),(14,2),(13,5),(8,11)],3)
        d.poly([(6,9),(12,3),(14,2),(7,10)],4)
        d.line([(5,12),(3,14)],6,2)
        d.line([(5,11),(3,13)],5)
        d.line([(4,8),(9,13)],7,2)
        d.line([(4,8),(9,12)],8)
    return d.done()


def shield(size,side=False,back=False):
    d=Draw(size,native=True)
    if size==32:
        d.poly([(7,5),(25,5),(27,10),(25,19),(22,24),(16,29),(10,24),(7,19),(5,10)],2)
        d.poly([(7,6),(24,6),(25,10),(23,19),(20,23),(16,26),(11,22),(8,17),(6,10)],3)
        d.line([(8,6),(23,6)],4)
        d.line([(6,10),(8,17),(11,22)],4)
        d.poly([(9,9),(23,9),(23,14),(21,21),(16,25),(11,21),(9,14)],5)
        d.poly([(17,9),(23,9),(23,14),(21,21),(16,25),(17,21)],6)
        d.line([(10,10),(15,10)],9)
    elif side:
        d.poly([(6,3),(9,3),(10,6),(9,11),(7,14),(6,12)],2)
        d.poly([(6,4),(8,4),(9,7),(8,11),(7,13)],3)
        d.line([(6,4),(6,10)],4)
        d.rect(8,5,9,10,6)
    else:
        d.poly([(4,3),(12,3),(13,6),(12,10),(10,13),(8,14),(5,12),(3,7)],2)
        d.poly([(4,4),(11,4),(12,6),(11,10),(8,13),(5,10),(4,7)],3)
        d.line([(4,3),(11,3)],4)
        d.poly([(5,5),(11,5),(11,8),(10,10),(8,12),(6,10),(5,8)],5)
        d.poly([(8,5),(11,5),(11,8),(10,10),(8,12)],6)
        if back:
            d.rect(6,6,10,7,2);d.rect(6,9,10,10,2)
        else:
            d.rect(5,5,8,6,9)
    return d.done()


def bomb(size,phase=0):
    d=Draw(size)
    d.oval(8,10,4.5,4.5,2)
    d.oval(7.5,9.2,3.8,3.7,13)
    d.rect(5,7,7,8,4);d.rect(5,8,6,9,4)
    d.rect(6.5,5,9,6.5,6)
    d.rect(7,5,8.5,6,5)
    d.line([(8,4.5),(9,3),(10,3)],9)
    d.poly([(10,1.5 if phase else 2),(11.5,3),(10,3.5)],10)
    if size==32:
        d.rect(6.5,6.5,7,7,14)
        d.rect(9.5,12,10.5,12.5,13)
    return d.done()


def candle(size):
    d=Draw(size)
    d.rect(6,7,10,13,9)
    d.rect(6,7,7,13,4)
    d.rect(9,8,10,13,5)
    d.rect(6,6.5,10,8,4)
    d.rect(8,7.5,9,9,9)
    d.line([(8,5),(8,6)],6)
    d.poly([(9,1.5),(9,3),(10,4),(9,5),(7,5),(6.5,4),(7.5,2.5)],10)
    d.poly([(8,3),(9,4.5),(7.5,4.5)],8)
    d.rect(5,13,11,14,7);d.rect(5,13,9,13.5,8)
    return d.done()


def cloak(size):
    d=Draw(size,native=True)
    if size==32:
        # A cut-out neckline, round shoulders, and a soft folded hem.
        d.poly([(10,5),(13,4),(14,8),(18,8),(19,4),(22,5),(24,9),(25,15),(28,27),
                (24,27),(21,25),(17,28),(13,26),(9,28),(4,27),(7,17),(8,10)],11)
        d.poly([(10,7),(12,6),(13,10),(16,11),(13,17),(11,24),(7,25),(9,17)],12)
        d.poly([(20,9),(22,11),(23,19),(26,26),(22,24),(18,27),(17,23),(19,17)],2)
        d.line([(10,6),(13,10),(18,10),(21,6)],12)
        d.rect(15,10,17,12,8)
        d.line([(14,15),(12,23)],11)
    else:
        d.poly([(5,3),(6,3),(7,5),(9,5),(10,3),(11,3),(12,5),(12,8),(14,13),
                (12,14),(10,13),(8,14),(6,13),(4,14),(2,13),(4,8),(4,5)],11)
        d.poly([(5,4),(6,5),(7,6),(6,9),(5,12),(3,12),(5,7)],12)
        d.poly([(10,5),(11,6),(11,9),(13,13),(10,12),(8,13),(8,11)],2)
        d.rect(7,5,9,6,8)
    return d.done()


def key(size):
    d=Draw(size,native=True)
    if size==32:
        d.oval(14,8,6,6,7);d.oval(13.5,7.5,5.5,5.5,8)
        d.oval(14,8,2.5,2.5,1)
        d.rect(12,13,17,28,7);d.rect(12,13,15,27,8)
        d.rect(16,21,22,24,8);d.rect(19,24,22,28,8)
        d.rect(10,4,13,5,4);d.rect(9,5,10,7,4)
    else:
        d.oval(7,4.5,3,3,7);d.oval(6.5,4,2.5,2.5,8)
        d.oval(7,4.5,1.3,1.3,1)
        d.rect(6,7,8,14,8)
        d.rect(8,10,11,11,8);d.rect(10,11,11,14,8)
        d.rect(5,2,7,3,4)
    return d.done()


def heart(size,piece=False,container=False):
    d=Draw(size)
    shape=[(8,5),(6,3),(4,3),(2,5),(2,8),(4,10),(8,14),(12,10),(14,8),(14,5),(12,3),(10,3)]
    d.poly(shape,3 if piece or container else 15)
    if piece:
        d.poly([(7,5),(7,8),(5,10),(3,8),(3,5),(4,4),(6,4)],15)
        d.line([(4,5),(5,5)],14)
        # The two quiet seams make the four-piece collectible legible.
        d.line([(8,6),(8,12)],2)
        d.line([(7,9),(11,9)],2)
    elif container:
        d.poly([(8,6),(6,4),(4,4),(3,5),(3,8),(8,13),(13,8),(13,5),(12,4),(10,4)],4)
        d.poly([(8,7),(6,5),(5,5),(4,6),(4,8),(8,12),(12,8),(12,6),(11,5),(10,5)],15)
        d.rect(5,6,6,7,14)
    else:
        d.rect(4,4,6,5,14);d.rect(3,5,4,6,14)
    return d.done()


def coin(size,big=False):
    d=Draw(size)
    if big:
        d.poly([(6,5),(10,5),(12,8),(12.5,11),(11,14),(5,14),(3.5,12),(4,8)],6)
        d.poly([(6,6),(9,6),(10,8),(10,12.5),(8,13),(5,12),(4.5,10),(5,8)],5)
        d.poly([(5,2.5),(8,3.5),(11,2.5),(10,5),(6,5)],5)
        d.line([(6,5),(10,5)],7)
        d.line([(6,6),(5,7)],9)
        d.oval(11,11.5,2.5,2.5,7);d.oval(10.5,11,1.8,1.9,8)
        d.rect(10,10,10.5,12,4)
    else:
        d.oval(8,8,4.5,5,7)
        d.oval(7.5,7.5,3.5,4,8)
        d.line([(8,5),(8,10)],7)
        d.line([(5,5),(6,4),(7,4)],4)
        if size==32:d.rect(5,8,5.5,9.5,9)
    return d.done()


def relic(size):
    d=Draw(size)
    d.line([(7,3),(7,1.5),(9,1.5),(9,3)],7)
    d.poly([(8,3),(12,6),(11,11),(8,14),(5,11),(4,6)],7)
    d.poly([(8,3.5),(11,6),(10,10.5),(8,13),(5.5,10),(5,6)],8)
    d.poly([(8,5),(10,6.5),(9.5,10),(8,11.5),(6.5,10),(6,6.5)],3)
    d.poly([(8,5),(8,10.5),(6.5,10),(6,6.5)],4)
    if size==32:d.line([(5.5,6),(5.5,8)],9,.5)
    return d.done()


def gauntlet(size):
    d=Draw(size,native=True)
    if size==32:
        d.poly([(7,10),(7,6),(10,6),(10,3),(13,3),(13,2),(16,2),(16,4),(19,4),(19,14),
                (21,12),(23,12),(25,15),(23,19),(20,23),(19,27),(9,27),(8,22),(6,18),(6,10)],5)
        d.poly([(17,5),(19,5),(19,14),(21,13),(23,13),(24,15),(21,19),(18,22),(18,25),(14,25),(15,18)],6)
        d.line([(10,7),(10,13)],6)
        d.line([(13,4),(13,11)],6)
        d.line([(16,5),(16,11)],6)
        d.line([(8,10),(8,15)],9)
        d.rect(8,23,20,29,2);d.rect(8,23,19,27,3);d.rect(8,23,11,27,4)
    else:
        d.poly([(3,6),(3,4),(5,4),(5,2),(7,2),(7,1),(9,1),(9,3),(10,3),(10,7),
                (12,6),(13,7),(12,9),(10,11),(10,13),(5,13),(4,10),(3,9)],5)
        d.poly([(9,3),(10,3),(10,7),(12,6),(13,7),(11,10),(9,11),(8,9)],6)
        d.line([(5,4),(5,7)],6);d.line([(7,3),(7,6)],6)
        d.rect(4,11,11,14,2);d.rect(4,11,10,13,3);d.rect(4,11,6,13,4)
    return d.done()


def bow(size):
    d=Draw(size,native=True)
    if size==32:
        d.line([(10,4),(10,28)],3)
        d.line([(10,3),(17,6),(21,12),(22,16),(21,20),(17,26),(10,29)],6,3)
        d.line([(10,3),(16,6),(20,12),(21,16),(20,20),(16,26),(10,29)],5)
        d.line([(11,4),(14,6),(17,10)],9)
        d.rect(20,13,23,19,7);d.rect(20,13,21,18,8)
        d.line([(10,3),(11,4)],8);d.line([(10,28),(11,29)],8)
    else:
        d.line([(5,2),(5,14)],3)
        d.line([(5,2),(9,4),(11,7),(11,9),(9,12),(5,14)],6,2)
        d.line([(5,2),(8,4),(10,7),(10,9),(8,12),(5,14)],5)
        d.rect(10,7,12,10,7);d.rect(10,7,11,9,8)
        d.rect(6,3,7,4,9)
    return d.done()


def hubcap(size):
    d=Draw(size)
    d.oval(8,8,6,6,2)
    d.oval(7.5,7.5,5.5,5.5,3)
    d.oval(7.5,7.5,4.5,4.5,2)
    d.oval(7.3,7.2,4,4,3)
    for x in (5,8,11):d.rect(x-.5,5,x+.5,11,2)
    d.line([(4,4.5),(5.5,3.5),(7,3)],4)
    return d.done()


def map_icon(size):
    d=Draw(size)
    d.poly([(2.5,4),(6.5,3),(10,4),(13.5,3),(13.5,12),(10,13),(6.5,12),(2.5,13)],9)
    d.poly([(2.5,4),(6.5,3),(6.5,12),(2.5,13)],4)
    d.line([(6.5,4),(6.5,11.5)],5)
    d.line([(10,4.5),(10,11.5)],5)
    d.line([(4,9),(5,7),(8,8),(11,6),(12,6.5)],11)
    d.rect(10.5,5.5,12,6.5,15)
    return d.done()


def compass(size):
    d=Draw(size)
    d.rect(7,1.5,9,4,7)
    d.rect(7.5,2,8.5,3,1)
    d.oval(8,8.5,5.5,5.5,7)
    d.oval(7.7,8.2,4.8,4.8,8)
    d.oval(8,8.5,3.8,3.8,9)
    d.poly([(10.5,5),(8.5,9),(5.5,12),(7.5,8)],2)
    d.poly([(10.5,5),(7.5,8),(8.5,9)],15)
    d.line([(4,5.5),(5,4.5),(6,4)],4)
    if size==32:d.rect(7.5,8,8.5,9,4)
    return d.done()


def grail(size):
    d=Draw(size)
    d.poly([(3,3),(13,3),(12,7),(10,9),(9,9),(9,12),(11,13),(11,14),(5,14),(5,13),(7,12),(7,9),(6,9),(4,7)],7)
    d.poly([(4,4),(12,4),(11,7),(9,8),(7,8),(5,7)],8)
    d.rect(3,3,13,4,8);d.rect(4,3,10,3.5,4)
    d.rect(5,4,6,6,4)
    d.rect(7,9,8,12,8)
    d.rect(5,13,11,14,8)
    return d.done()


def arrow(size,count=1,direction='n'):
    d=Draw(size)
    n=1 if count==1 else 2 if count==5 else 3
    # Staggered heads and fletching keep bundles from becoming a rake.
    for i in range(n):
        x=8+(i-(n-1)/2)*3.5
        off=(n-1-i)*1.5
        tail=12.5 if n==1 else 10.5+off
        head=2 if n==1 else 1.5
        d.line([(x,tail),(x,4+off)],6)
        d.line([(x,6+off),(x,tail-1)],5)
        d.poly([(x,2+off),(x-head,5+off),(x,4.5+off),(x+head,5+off)],3)
        d.line([(x-1,tail-2),(x,tail-.5),(x+1,tail-2)],4)
        if size==32:d.line([(x,2.5+off),(x-1,4+off)],4,.5)
    rows=d.done()
    if direction=='s':return rows[::-1]
    if direction=='e':return [''.join(rows[size-1-x][y] for x in range(size)) for y in range(size)]
    return rows


def blade(frame):
    d=Draw(16)
    if frame=='blade_s':
        d.rect(7,5,9,13,3);d.poly([(7,13),(9,13),(8,15)],3)
        d.rect(7,5,8,13,4);d.rect(7,1,9,4,6);d.rect(7,1,8,3,5)
        d.rect(5,4,11,5,7);d.rect(5,4,10,5,8)
    elif frame=='blade_e':
        d.rect(5,7,13,9,3);d.poly([(13,7),(15,8),(13,9)],3)
        d.rect(5,7,13,8,4);d.rect(1,7,4,9,6);d.rect(1,7,3,8,5)
        d.rect(4,5,5,11,7);d.rect(4,5,5,10,8)
    else:
        d.poly([(5,6),(6,5),(13,12),(14,14),(12,13)],3)
        d.line([(6,6),(12,12)],4)
        d.line([(2,2),(4,4)],6,2);d.line([(2,2),(3,3)],5)
        d.line([(2,5),(5,2)],7,2);d.line([(2,5),(5,2)],8)
    return d.done()


def make(name,size):
    if name=='none':return ['.'*size]*size
    if name in ('bombs','bomb_pickup'):return bomb(size,name=='bomb_pickup')
    if name=='bomb_lit':
        return [r.translate(str.maketrans({'d':'f','4':'8'})) for r in bomb(size,1)]
    if name=='lamp':return candle(size)
    if name=='cloak':return cloak(size)
    if name=='key':return key(size)
    if name in ('heart','heart_piece','heart_container'):return heart(size,name=='heart_piece',name=='heart_container')
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
            if name=='items':s['frames']['bomb_lit']=make('bomb_lit',16)
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
