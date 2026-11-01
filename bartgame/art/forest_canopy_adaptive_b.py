"""Native adaptive tree compositions, directions six through ten.

The footprint is part of the drawing brief. A tiny root remnant, a complete
tree, a shallow border and a large grove have different anatomy; none is a
filtered enlargement of a small repeating crown. Transparent space outside
the anatomy is composited over the engine's blocked underbrush substrate.
"""
from functools import lru_cache
from PIL import Image, ImageDraw

NAMES = {
    6: 'Fallen Crown',
    7: 'Lightning Cleft Oak',
    8: 'Pale Birch Congregation',
    9: 'Black Cedar Cathedral',
    10: 'Sorrow Arch Elm',
}
SIZES = {
    'small': (16, 16), 'clump': (32, 32), 'tree': (48, 48),
    'grove': (64, 64), 'hero': (96, 64), 'branch': (64, 16),
    'roots': (32, 16), 'border': (96, 32),
    'column': (16, 64),
}
_PREVIEW_PALETTE = [
    '#000000', '#080810', '#181820', '#484038', '#807058',
    '#201828', '#403048', '#685068', '#183828', '#385838',
    '#708848', '#401060', '#9820d0', '#d850e8', '#f0d8f0', '#a8a078',
]


def _image(w,h):
    im=Image.new('P',(w,h),0)
    colors=[int(c[k:k+2],16) for c in _PREVIEW_PALETTE for k in (1,3,5)]
    im.putpalette(colors+[0]*(768-len(colors)))
    return im


def _new(role):
    im = _image(*SIZES[role])
    return im, ImageDraw.Draw(im)


def _wood(d, points, width=5, pale=False):
    """Unequal connected limb; a lit upper-left plane, not concentric rings."""
    d.line(points, fill=1, width=width + 2, joint='curve')
    d.line(points, fill=2, width=width, joint='curve')
    upper = [(x-1, y-1) for x, y in points]
    d.line(upper, fill=3 if not pale else 4, width=max(1, width-2), joint='curve')
    d.line([(x-2, y-1) for x, y in points[:-1]],
           fill=4 if not pale else 15, width=max(1, width//4), joint='curve')


def _vein(d, points, bright=False):
    d.line(points, fill=11, width=3, joint='curve')
    d.line(points, fill=12, width=1, joint='curve')
    if len(points) > 2:
        d.line(points[1:3], fill=13, width=1)
    if bright:
        x, y = points[len(points)//2]
        d.line((x-1, y, x+1, y), fill=14)
        d.line((x, y-1, x, y+1), fill=13)


def _leaf(d, x, y, rx, ry, live=False, seed=0):
    """Ragged connected foliage with angular leaf fans and broad lit planes."""
    outer = [(x-rx, y+1), (x-rx+2, y-2), (x-rx+1, y-ry+3),
             (x-rx+5, y-ry+2), (x-4, y-ry), (x-1, y-ry+2),
             (x+3, y-ry+1), (x+6, y-ry+3), (x+rx-2, y-ry+2),
             (x+rx-3, y-2), (x+rx, y), (x+rx-2, y+3),
             (x+rx-5, y+2), (x+5, y+ry), (x+2, y+ry-2),
             (x-2, y+ry+1), (x-4, y+ry-1), (x-rx+4, y+ry),
             (x-rx+5, y+3)]
    dark, mid, lit = (8, 9, 10) if live else (5, 6, 7)
    d.polygon(outer, fill=1)
    d.polygon([(px, py-1) for px, py in outer[1:-1]], fill=dark)
    d.polygon([(x-rx+3,y), (x-rx+4,y-ry+4), (x-4,y-ry+2),
               (x+2,y-ry+3), (x+rx-4,y-ry+4), (x+rx-2,y),
               (x+5,y+ry-2), (x-3,y+ry-1), (x-rx+5,y+ry-2)], fill=mid)
    d.polygon([(x-rx+4,y-1), (x-rx+6,y-ry+4), (x-4,y-ry+3),
               (x-1,y-ry+4), (x+rx-5,y-ry+4), (x+rx-4,y-2),
               (x+3,y-1), (x-2,y-3), (x-6,y-1)], fill=lit)
    # Pointed fans interrupt the edge and say leaves rather than a closed cap.
    for k, dx in enumerate((-rx+5, -3, rx-6)):
        if rx < 8 and k != 1:
            continue
        yy = y + ((k+seed) % 3) - 1
        d.line([(x+dx-3,yy+1),(x+dx,yy-2),(x+dx+2,yy)], fill=dark)
        d.line([(x+dx-2,yy),(x+dx,yy-2),(x+dx+3,yy-1)], fill=lit)


def _sprig(d, x, y, live=True, left=False):
    dark, mid, lit = (8, 9, 10) if live else (5, 6, 7)
    sign = -1 if left else 1
    d.line([(x,y+3),(x+sign*3,y),(x+sign*8,y-2)], fill=dark)
    d.polygon([(x+sign*2,y+1),(x+sign*3,y-3),(x+sign*6,y-4),
               (x+sign*5,y-1)], fill=mid)
    d.line([(x+sign*3,y-2),(x+sign*5,y-3)], fill=lit)
    d.polygon([(x+sign*5,y),(x+sign*8,y-1),(x+sign*10,y+1),
               (x+sign*7,y+2)], fill=mid)


def _rich_leaf(d,x,y,rx,ry,live=False,seed=0):
    _leaf(d,x,y,rx,ry,live,seed)
    if rx<13 or ry<8:return
    shade,mid,lit=(8,9,10) if live else (5,6,7)
    # Large masses have room for additional uneven fan groups. Their count
    # follows the native area, not the placement of logical map cells.
    count=max(4,rx*ry//38)
    for i in range(count):
        dx=((i*13+seed*7)%(2*rx-12))-rx+6
        dy=((i*7+seed*3)%(2*ry-8))-ry+4
        if (dx*dx*100)//(rx*rx)+(dy*dy*100)//(ry*ry)>63:continue
        d.polygon([(x+dx-3,y+dy+2),(x+dx-2,y+dy-1),
                   (x+dx,y+dy-2),(x+dx+2,y+dy),
                   (x+dx+4,y+dy-1),(x+dx+2,y+dy+2)],fill=shade)
        d.line([(x+dx-2,y+dy),(x+dx,y+dy-2),(x+dx+2,y+dy)],fill=lit)
        d.line([(x+dx+1,y+dy+2),(x+dx+3,y+dy+1)],fill=mid)


def _shelf(d, x, y, width=5):
    d.polygon([(x-width,y),(x-width+2,y-2),(x+1,y-3),
               (x+width,y-1),(x+width+1,y+1),(x-width+1,y+2)], fill=1)
    d.line([(x-width+1,y),(x-1,y-2),(x+width-1,y)], fill=7, width=2)
    d.line([(x-width+1,y+1),(x+width,y+1)], fill=15)


def _rootball(d, x, y, large=False):
    r = 9 if large else 6
    d.polygon([(x-r,y-4),(x-r+4,y-r),(x+2,y-r+1),
               (x+r,y-2),(x+r-2,y+5),(x+1,y+r),
               (x-r+2,y+5)], fill=1)
    d.polygon([(x-r+2,y-3),(x-r+5,y-r+2),(x+1,y-r+3),
               (x+r-2,y-1),(x+r-3,y+4),(x,y+r-2),(x-r+3,y+3)], fill=3)
    d.line([(x-r+3,y-3),(x-r+6,y-r+3),(x,y-r+3)], fill=4,width=2)
    d.polygon([(x-3,y-3),(x+2,y-4),(x+5,y),(x+1,y+4),(x-3,y+1)],fill=2)
    d.line([(x-2,y-2),(x+1,y-2),(x+3,y)],fill=4)


def _fallen(role, variation=0):
    im, d = _new(role)
    if role == 'small':
        # A broken root fork with a leaf sprig; not a tiny whole hero tree.
        _wood(d, [(2,13),(7,10),(11,5),(14,4)], 3)
        _wood(d, [(7,10),(5,5),(2,3)], 2)
        d.polygon([(1,12),(5,11),(6,14),(2,15)], fill=4)
        _vein(d, [(5,12),(8,9),(11,6)])
        _sprig(d, 9, 4, True)
    elif role == 'clump':
        _leaf(d, 23, 10, 10, 7, False, 1)
        _wood(d, [(4,26),(12,22),(24,18),(30,18)], 6)
        _wood(d, [(12,22),(11,13),(6,7)], 3)
        d.polygon([(3,23),(7,21),(10,24),(8,29),(3,29)], fill=4)
        _vein(d, [(6,25),(14,21),(23,20)], True)
        _leaf(d, 21, 7, 7, 4, True, 3)
        _sprig(d, 10, 15, True, True)
    elif role in ('tree', 'grove', 'hero'):
        if role == 'tree':
            limbs = [([(7,42),(15,35),(30,31),(42,26)],7),
                     ([(19,35),(20,23),(12,14)],4),
                     ([(31,31),(34,18),(41,12)],3)]
            crowns = [(36,14,12,9),(18,17,10,7),(40,28,8,7)]
            greens = [(36,10,7,5),(12,19,6,4)]
            veins = [[(8,40),(17,34),(29,33),(40,27)],[(29,32),(32,21),(37,17)]]
            roots = [[(9,40),(2,36)],[(8,42),(3,46)],[(11,41),(14,46)]]
        elif role == 'grove':
            limbs = [([(8,53),(20,46),(36,44),(51,34),(59,34)],9),
                     ([(22,46),(23,31),(15,19),(7,17)],4),
                     ([(39,42),(39,25),(47,16)],5),
                     ([(50,35),(56,24),(62,21)],3)]
            crowns = [(16,18,14,10),(46,15,16,11),(53,33,12,9)]
            greens = [(43,10,10,6),(15,17,7,5),(58,34,6,4)]
            veins = [[(9,52),(23,45),(36,45),(49,36)],[(38,41),(39,28),(44,20)]]
            roots = [[(10,51),(3,42)],[(10,54),(2,60)],[(15,52),(19,61)]]
        else:
            limbs = [([(10,52),(24,46),(45,43),(65,32),(80,34),(91,30)],15),
                     ([(25,46),(28,32),(39,25),(45,12)],5),
                     ([(48,42),(47,25),(35,15),(24,13)],5),
                     ([(65,33),(71,21),(84,15),(93,14)],4),
                     ([(79,33),(82,43),(92,46)],2)]
            crowns = [(29,15,18,11),(68,17,27,15),(87,39,8,6)]
            greens = [(69,6,16,7),(27,22,8,5)]
            veins = [[(11,51),(26,45),(43,45),(63,34),(78,35)],
                     [(47,41),(46,28),(36,18)],[(66,32),(73,22),(83,17)]]
            roots = [[(9,50),(1,43)],[(8,53),(1,61)],[(15,54),(21,62)]]
        for x,y,rx,ry in crowns:
            _leaf(d,x,y,rx,ry,False,variation)
        for points, width in limbs:
            _wood(d,points,width)
        for points in roots:
            _wood(d,points,4 if role=='hero' else 3)
        if role in ('grove','hero'):
            _rootball(d,11 if role=='hero' else 10,51 if role=='hero' else 52,role=='hero')
        for points in veins:
            _vein(d,points,role=='hero')
        for x,y,rx,ry in greens:
            _leaf(d,x,y,rx,ry,True,variation+1)
        if role=='hero':
            _sprig(d,85,35,True)
        # The cap grows directly from the log's underside. A fixed lower
        # screen coordinate would make it a floating, pickup-like shape.
        sx,sy={'tree':(24,35),'grove':(35,46),'hero':(50,42)}[role]
        _shelf(d,sx,sy,4)
    elif role == 'branch':
        _wood(d,[(1,12),(17,8),(32,10),(46,5),(62,7)],5)
        _wood(d,[(29,9),(34,3),(42,1)],2)
        _wood(d,[(47,5),(51,13),(60,15)],2)
        _vein(d,[(3,11),(16,7),(31,9),(44,5)])
        _sprig(d,47,3,True)
        _sprig(d,22,10,True,True)
    elif role == 'roots':
        for pts in [[(15,2),(12,7),(3,13)],[(15,3),(21,9),(29,12)],
                    [(16,4),(17,10),(13,15)]]:
            _wood(d,pts,4)
        _vein(d,[(15,3),(12,8),(5,11)])
        _sprig(d,21,7,True)
    elif role == 'border':
        # Wide, shallow old bough: no space for a standing trunk here.
        for x,y,rx,ry in [(15,9,15,9),(42,10,19,10),(77,8,18,9),(86,22,10,7)]:
            _leaf(d,x,y,rx,ry,False,variation)
        _wood(d,[(0,28),(22,21),(40,24),(61,16),(79,21),(95,17)],8)
        _wood(d,[(31,23),(32,12),(24,7)],3)
        _wood(d,[(64,17),(66,5),(75,1)],4)
        _vein(d,[(2,27),(22,21),(40,25),(60,17),(78,22)])
        _leaf(d,43,6,12,6,True,2)
        _leaf(d,82,17,9,6,True,1)
        _sprig(d,19,11,True,True)
    elif role == 'column':
        _wood(d,[(7,63),(9,48),(6,33),(10,18),(8,1)],7)
        _wood(d,[(8,43),(1,37)],3)
        _wood(d,[(8,25),(15,17)],3)
        _vein(d,[(7,61),(10,47),(7,33),(11,19),(9,4)],True)
        _sprig(d,4,18,True)
        _sprig(d,12,42,True,True)
    return im


def _lightning_tree(w, h, detail=2, second=False):
    im=_image(w,h);d=ImageDraw.Draw(im)
    cx=w//2;spread=w//2-5;cy=max(8,h//4)+(2 if second else 0)
    if detail>=3:
        crowns=[(w//5,cy,20,13),(w*3//4,cy+4,23,15),(cx+3,7,14,8)]
    elif detail==2:
        crowns=[(w//4,cy+1,max(10,w//4),11),(w*3//4,cy+5,max(9,w//4),12)]
    else:
        crowns=[(w//3,cy+3,max(8,w//3),10),(w*3//4,cy-1,max(7,w//4),8)]
    for x,y,rx,ry in crowns:_rich_leaf(d,x,y,rx,ry,False,detail)
    yfork=h*9//16
    left=[(cx-4,h-3),(cx-7,yfork+9),(cx-9,yfork),(cx-spread,cy+6),(cx-spread+3,cy-3)]
    right=[(cx+5,h-2),(cx+7,yfork+7),(cx+10,yfork-1),(cx+spread-3,cy+6),(cx+spread,cy-2)]
    _wood(d,left,10 if detail>=3 else 7)
    _wood(d,right,9 if detail>=3 else 6)
    _wood(d,[(cx-8,yfork+1),(cx-1,cy+10),(cx+1,cy-4)],5 if detail>=2 else 3)
    _wood(d,[(cx+10,yfork-1),(cx+spread+1,yfork-7),(w-2,yfork-13)],3)
    if detail>=2:
        _wood(d,[(cx-spread+3,cy+7),(5,cy+6),(1,cy-1)],3)
        _wood(d,[(cx+spread-4,cy+7),(w-5,cy+10),(w-1,cy+6)],2)
    rootspread=min(22,w//2-2)
    for pts in [[(cx-4,h-5),(cx-rootspread+6,h-1),(cx-rootspread,h-1)],
                [(cx+5,h-5),(cx+rootspread-6,h-2),(cx+rootspread,h-1)],
                [(cx,h-7),(cx+1,h-1)]]:_wood(d,pts,4)
    # The split is a recessed wound in a recognizable two-stem tree.
    d.polygon([(cx-1,h-7),(cx-2,yfork+4),(cx+2,cy+12),
               (cx+6,yfork+4),(cx+3,h-5)],fill=1)
    _vein(d,[(cx-4,h-8),(cx-5,yfork+4),(cx-10,yfork-4),(cx-spread+4,cy+5)],True)
    _vein(d,[(cx+5,h-9),(cx+5,yfork+3),(cx+12,yfork-6),(cx+spread-1,cy+5)],True)
    _vein(d,[(cx-5,yfork+4),(cx+1,cy+11),(cx+2,cy-1)],False)
    _leaf(d,max(7,w//8),cy+1,max(7,w//9),6,True,2)
    _leaf(d,w-10,cy+10,max(7,w//10),7,True,3)
    if second:_sprig(d,cx+9,yfork-7,False,True)
    if detail>=3:_leaf(d,cx+3,5,10,5,True,0)
    return im


def _birch_tree(w,h,detail=2,second=False):
    im=_image(w,h);d=ImageDraw.Draw(im)
    if detail>=3:
        crowns=[(18,13,18,11),(44,10,23,13),(77,27,20,12),(83,11,10,8)]
        stems=[([(15,h-2),(20,41),(17,25),(22,13)],6),
               ([(47,h-1),(45,42),(36,28),(42,6)],9),
               ([(81,h-2),(75,45),(83,34),(79,23)],7)]
        cross=[[(36,28),(52,19),(67,22),(86,15)],[(45,40),(61,33),(73,35),(89,30)]]
        greens=[(14,11,9,6),(79,30,11,7),(45,4,10,5)]
    elif detail==2:
        crowns=[(w//4,12,max(10,w//4),10),(w*3//4,20,max(10,w//4),12)]
        stems=[([(w//3,h-2),(w//3-3,h*2//3),(w//3+1,24),(w//3-3,7)],7),
               ([(w*2//3,h-1),(w*2//3+3,h*2//3),(w*2//3-2,18)],6)]
        cross=[[(w//3,31),(w//2,20),(w-5,24)],[(w*2//3,38),(w-5,34)]]
        greens=[(w//5,9,8,6),(w-9,23,9,6)]
    else:
        crowns=[(w//2-2,13,max(9,w//2-3),10)]
        stems=[([(w//2,h-2),(w//2+2,h*2//3),(w//2-3,22),(w//2,6)],6)]
        cross=[[(w//2-2,27),(5,18),(2,11)],[(w//2,23),(w-5,15)]]
        greens=[(w//2+3,8,8,5)]
    for x,y,rx,ry in crowns:_rich_leaf(d,x,y,rx,ry,False,2)
    for pts,width in stems:_wood(d,pts,width,True)
    for pts in cross:_wood(d,pts,3,True)
    for i,(pts,width) in enumerate(stems):
        bx=pts[0][0]
        for k,yy in enumerate(range(25+i*3,h-8,9)):
            # Broken horizontal bark lenticels, not repeated glowing bars.
            xx=bx+(-2 if (k+i)%2 else 1)
            d.line((xx-2,yy,xx+1,yy-1),fill=2)
        _wood(d,[(bx,h-6),(bx-7,h-1)],3)
        _wood(d,[(bx,h-5),(bx+8,h-1)],3)
        _vein(d,[(bx,h-9),(bx+2,h-17),(pts[1][0],pts[1][1]+2)],i==1)
    for x,y,rx,ry in greens:_leaf(d,x,y,rx,ry,True,4)
    if second:_shelf(d,w//2,h-18,4)
    for pts in cross:
        x,y=pts[-1];_sprig(d,x-5,y-2,False,True)
    return im


def _cedar_bough(d,x,y,rx,ry,live=False):
    dark,mid,lit=(8,9,10) if live else (5,6,7)
    # Long pointed conifer sprays form unequal drooping shelves, not domes.
    points=[(x-rx,y+ry-1),(x-rx+5,y),(x-rx+9,y+1),
            (x-rx+12,y-3),(x-5,y-ry+2),(x,y-ry),
            (x+6,y-ry+3),(x+rx-8,y-1),(x+rx-5,y+2),
            (x+rx,y+ry),(x+rx-8,y+ry-1),(x+rx-13,y+ry+2),
            (x+3,y+ry),(x-1,y+ry+3),(x-8,y+ry),(x-rx+8,y+ry+1)]
    d.polygon(points,fill=1)
    d.polygon([(px,py-1) for px,py in points[1:-1]],fill=dark)
    d.polygon([(x-rx+8,y),(x-5,y-ry+3),(x,y-ry+2),
               (x+7,y-ry+5),(x+rx-7,y+2),(x+9,y+1),
               (x+1,y+3),(x-9,y+1)],fill=mid)
    d.line([(x-rx+10,y),(x-4,y-ry+4),(x,y-ry+3),(x+8,y-ry+6)],fill=lit,width=2)
    for dx in (-rx+10,-8,6,rx-12):
        d.line([(x+dx-3,y+2),(x+dx,y-1),(x+dx+2,y+3)],fill=mid)


def _cedar_tree(w,h,detail=2,second=False):
    im=_image(w,h);d=ImageDraw.Draw(im)
    cx=w//2+(3 if second else -2)
    _wood(d,[(cx,h-2),(cx-3,h*3//4),(cx+2,h//2),(cx-1,8),(cx+2,1)],8 if detail>=3 else 6)
    # Separate native arrangements, with more branch layers only when there
    # is space. The second tree in a hero grove is deliberately smaller.
    layers=[(cx,10,max(9,w//5),7),(cx-4,24,max(12,w//3),9),
            (cx+3,40,max(14,w//2-5),11)] if h>=60 else [
            (cx,10,max(9,w//4),7),(cx-2,25,max(12,w//2-4),10)]
    for i,(x,y,rx,ry) in enumerate(layers):
        _cedar_bough(d,x,y,rx,ry,False)
        _wood(d,[(cx,y+5),(x-rx+6,y+ry-3)],3)
        _wood(d,[(cx,y+5),(x+rx-5,y+ry-2)],3)
        _vein(d,[(cx,y+5),(x-rx//2,y+ry-2),(x-rx+8,y+ry-2)],False)
    if detail>=3:
        _wood(d,[(w-13,h-2),(w-15,39),(w-11,20)],5)
        _cedar_bough(d,w-13,24,14,8,False)
        _cedar_bough(d,w-14,41,19,10,False)
        _vein(d,[(w-14,h-7),(w-16,44),(w-12,27)],True)
    _vein(d,[(cx,h-9),(cx-1,h*3//4),(cx+2,h//2),(cx-1,15)],True)
    _cedar_bough(d,cx-2,10,max(8,w//6),5,True)
    if detail>=2:
        _cedar_bough(d,cx+14,39 if h>=60 else 25,max(9,w//7),6,True)
        _cedar_bough(d,cx-17,25 if h>=60 else 17,max(8,w//10),5,True)
        _sprig(d,cx+14,39 if h>=60 else 25,True,False)
        _sprig(d,cx-20,35 if h>=60 else 25,True,True)
    for pts in [[(cx,h-6),(cx-10,h-1),(cx-17,h-1)],
                [(cx,h-7),(cx+11,h-1),(cx+17,h-1)]]:_wood(d,pts,4)
    return im


def _elm_tree(w,h,detail=2,second=False):
    im=_image(w,h);d=ImageDraw.Draw(im)
    cx=w//2;left=10 if detail>=3 else max(6,w//5)
    # One ancient trunk curves through the whole composition, giving a
    # vault-like opening between limbs without repeating tree medallions.
    crowns=[(w//4,12,max(12,w//4),11),(w*3//5,9,max(13,w//4),12),
            (w-14,24,max(10,w//5),13)] if detail>=2 else [
            (w//3,12,max(9,w//3),10),(w-9,22,max(7,w//4),10)]
    for x,y,rx,ry in crowns:_rich_leaf(d,x,y,rx,ry,False,1)
    _wood(d,[(cx-10,h-2),(cx-18,h-14),(cx-20,h*3//5),
             (left+2,26),(left+1,20),(left+7,14),
             (cx-2,8),(cx+13,9),(w-9,13)],12 if detail>=3 else 8)
    _wood(d,[(cx-18,h*3//5),(cx,32),(w-17,30),(w-7,20)],6 if detail>=2 else 4)
    _wood(d,[(left+8,15),(left,9),(2,10)],3)
    _wood(d,[(cx+3,8),(cx+10,20),(w*3//4,26)],4)
    _wood(d,[(w-16,31),(w-8,43),(w-2,44)],3)
    # A recessed seam in the bent trunk; it is high on the wood, not a cave
    # portal at ground level.
    d.polygon([(cx-18,h-18),(cx-19,h-28),(cx-15,h-32),
               (cx-13,h-24),(cx-14,h-16)],fill=1)
    _vein(d,[(cx-9,h-8),(cx-17,h-17),(cx-19,h*3//5),
             (left+4,25),(left+11,15),(cx+6,10)],True)
    _vein(d,[(cx-16,h*3//5),(cx+2,34),(w-18,33),(w-10,24)],False)
    _leaf(d,w*3//5,4,max(9,w//7),6,True,2)
    _leaf(d,w-11,26,max(7,w//8),7,True,3)
    _leaf(d,left+7,13,max(7,w//10),6,True,0)
    _sprig(d,left+6,20,True,True)
    for pts in [[(cx-10,h-7),(cx-22,h-1),(cx-30,h-2)],
                [(cx-11,h-6),(cx-1,h-1),(cx+12,h-1)],
                [(cx-13,h-8),(cx-13,h-1)]]:_wood(d,pts,4)
    return im


def _elm_compact(w,h,second=False):
    im=_image(w,h);d=ImageDraw.Draw(im)
    cx=w//2
    _rich_leaf(d,cx-5-(2 if second else 0),12,max(10,w//2-4),10,False,3)
    _leaf(d,w-7,19+(3 if second else 0),max(7,w//4),8,False,0)
    points=[(cx,h-2),(cx-7,h-12),(cx-9,h-23),(cx-7,19),
            (cx,11),(w-3,9+(3 if second else 0))]
    _wood(d,points,7 if w==32 else 9)
    _wood(d,[(cx-8,25),(cx+5,25),(w-3,18)],4)
    _wood(d,[(cx-5,15),(4,10),(1,12)],2)
    _vein(d,[(cx,h-7),(cx-6,h-14),(cx-7,24),(cx-3,16),(w-7,12+(3 if second else 0))],True)
    _leaf(d,cx-6,9,8,5,True,1)
    _sprig(d,w-10,17,True)
    _wood(d,[(cx,h-6),(cx-10,h-1)],4)
    _wood(d,[(cx,h-6),(cx+10,h-1)],4)
    return im


def _minor(style,role,variation=0):
    im,d=_new(role);w,h=im.size
    if role=='roots':
        cx=15
        rootsets={7:[[(cx,0),(cx-2,6),(3,14)],[(cx+3,0),(cx+5,9),(29,13)],[(cx,5),(cx,15)]],
                  8:[[(9,1),(8,8),(1,13)],[(22,0),(23,8),(30,13)],[(10,4),(16,12),(21,15)]],
                  9:[[(15,1),(9,9),(0,15)],[(16,2),(22,8),(31,15)],[(15,5),(15,15)]],
                  10:[[(13,0),(10,6),(1,10)],[(14,1),(20,9),(30,14)],[(13,3),(10,12),(5,15)]]}
        for pts in rootsets[style]:_wood(d,pts,4,style==8)
        _vein(d,rootsets[style][0],True)
        _sprig(d,20,5,True,False)
    elif role=='column':
        paths={7:[(6,63),(9,47),(5,32),(10,17),(8,0)],
               8:[(7,63),(10,44),(6,27),(8,0)],
               9:[(8,63),(7,42),(9,21),(8,0)],
               10:[(11,63),(5,48),(4,30),(10,17),(13,0)]}
        pts=paths[style];_wood(d,pts,7,style==8);_vein(d,pts,style!=8)
        _wood(d,[(pts[2][0],pts[2][1]),(0,pts[2][1]-6)],3,style==8)
        _wood(d,[(pts[1][0],pts[1][1]),(15,pts[1][1]-8)],3,style==8)
        if style==9:
            _cedar_bough(d,8,18,9,4,True)
            _cedar_bough(d,7,39,9,5,False)
        else:
            _sprig(d,5,18,True)
            _sprig(d,12,40,True,True)
    elif role=='small':
        if style==9:
            _wood(d,[(8,15),(7,8),(9,2)],3)
            _cedar_bough(d,8,5,6,3,False)
            _cedar_bough(d,8,10,8,3,True)
            _vein(d,[(8,14),(7,9),(8,5)])
        elif style==8:
            _wood(d,[(5,15),(7,9),(6,2)],4,True)
            _wood(d,[(7,10),(13,6)],2,True)
            _sprig(d,8,3,True,True)
            _vein(d,[(5,14),(6,10),(7,8)])
        elif style==7:
            _wood(d,[(8,15),(7,9),(3,3)],4)
            _wood(d,[(8,14),(10,8),(14,3)],3)
            _vein(d,[(8,14),(8,9),(11,6)],True)
            _sprig(d,3,5,True)
        else:
            _wood(d,[(10,15),(5,11),(4,6),(9,2),(14,3)],4)
            _vein(d,[(10,14),(5,11),(5,7),(10,4)])
            _sprig(d,7,2,True,True)
    elif role=='clump':
        if style==9:
            _wood(d,[(17,31),(15,18),(17,3)],5)
            _cedar_bough(d,17,8,10,6,False)
            _cedar_bough(d,16,19,15,7,False)
            _cedar_bough(d,17,8,8,4,True)
            _vein(d,[(17,29),(15,19),(17,10)],True)
        else:
            _rich_leaf(d,16,10,14,8,False,style)
            paths={7:[[(13,30),(12,22),(6,13)],[(19,31),(20,21),(27,12)]],
                   8:[[(12,31),(10,20),(13,8)],[(23,31),(24,23),(20,16)]],
                   10:[[(18,31),(9,23),(8,16),(17,8),(29,10)]]}
            for pts in paths[style]:_wood(d,pts,5,style==8)
            _vein(d,paths[style][0],True)
            _leaf(d,20,6,8,5,True,1)
            _sprig(d,7,15,True,True)
    elif role in ('branch','border'):
        if style==9:
            width=w//2
            _cedar_bough(d,w//2,h//2,width-1,max(4,h//3),False)
            _wood(d,[(0,h-4),(w//3,h//2),(w*2//3,h//2+2),(w-1,h//3)],4)
            _vein(d,[(2,h-5),(w//3,h//2-1),(w*2//3,h//2+1)],False)
            _cedar_bough(d,w*2//3,h//2-1,max(8,w//6),max(3,h//5),True)
        elif style==8:
            _wood(d,[(0,h-5),(w//4,h//2),(w//2,h//2+2),(w-1,5)],5,True)
            _wood(d,[(w//2,h//2+2),(w//2-7,2)],3,True)
            _vein(d,[(3,h-5),(w//4,h//2+1),(w//2,h//2+3)],False)
            if role=='border':
                _rich_leaf(d,w//4,8,20,9,False,2)
                _rich_leaf(d,w*3//4,17,20,10,False,1)
                _leaf(d,w*3//4+6,12,11,6,True,2)
            _sprig(d,w//4,5,True)
        elif style==7:
            _wood(d,[(0,h-3),(w//3,h//2+2),(w//2,h//2),(w*3//4,5),(w-1,7)],6)
            _wood(d,[(w//2,h//2),(w//2-4,2),(w//2-13,0)],3)
            _wood(d,[(w*3//4,5),(w-7,h-1)],2)
            _vein(d,[(2,h-4),(w//3,h//2+1),(w//2,h//2-1),(w*3//4,5)],True)
            if role=='border':
                _rich_leaf(d,20,7,20,9,False,1)
                _rich_leaf(d,71,17,25,12,False,3)
                _leaf(d,72,8,13,6,True,2)
            _sprig(d,w//3,4,True,True)
        else:
            pts=[(0,h-2),(w//5,h//2+4),(w//2,h//2-2),(w*3//4,3),(w-1,7)]
            _wood(d,pts,7)
            _wood(d,[(w//2,h//2-2),(w*2//3,h-3),(w-4,h-1)],3)
            _vein(d,[(2,h-3),(w//5,h//2+3),(w//2,h//2-3),(w*3//4,4)],True)
            if role=='border':
                _rich_leaf(d,w//3,8,25,10,False,2)
                _rich_leaf(d,w-17,17,20,11,False,0)
                _leaf(d,w//3+8,3,13,6,True,3)
            _sprig(d,w-12,8,True,True)
    return im


@lru_cache(None)
def authored_tree(style,large=False,second=False):
    """New native two-/three-column tree groups, with fixed foot baseline."""
    w,h=(48,64) if large else (32,48)
    if style==6:
        im=_image(w,h);d=ImageDraw.Draw(im);cx=w//2
        _rich_leaf(d,w*3//4,13,w//3,10 if large else 8,False,2)
        _leaf(d,w//4,22,w//4+2,9 if large else 6,False,0)
        _wood(d,[(cx,h-2),(cx-4,h-14),(cx+3,h//2),(w-5,18)],8 if large else 6)
        _wood(d,[(cx-1,h//2+4),(w//4,23),(3,15 if not second else 20)],4)
        _wood(d,[(cx+3,h//2),(cx+4,12)],3)
        _vein(d,[(cx,h-7),(cx-3,h-15),(cx+3,h//2+2),(w-8,21)],True)
        _leaf(d,w*3//4,8,w//4,6 if large else 4,True,1)
        _sprig(d,w//4,19,True,True)
        _wood(d,[(cx,h-7),(cx-11,h-1)],4)
        _wood(d,[(cx,h-6),(cx+10,h-1)],4)
        return im
    if style==7:return _lightning_tree(w,h,2 if large else 1,second)
    if style==8:
        im=_birch_tree(w,h,2 if large else 1,second);d=ImageDraw.Draw(im)
        if large:
            _wood(d,[(w//3,h-7),(w//2,h-1)],3,True)
            _wood(d,[(w*2//3,h-7),(w//2,h-1)],3,True)
        return im
    if style==9:return _cedar_tree(w,h,2 if large else 1,second)
    if style==10:return _elm_compact(w,h,second)
    raise ValueError(style)


@lru_cache(None)
def paint(style, role, variation=0):
    """Return a native indexed composition for one concrete fitting role."""
    style, variation = int(style), int(variation)
    if style not in NAMES or role not in SIZES:
        raise ValueError((style,role))
    if style == 6:
        return _fallen(role,variation)
    if role=='hero':
        return {7:_lightning_tree,8:_birch_tree,9:_cedar_tree,10:_elm_tree}[style](96,64,3,bool(variation&1))
    if role in ('small','clump','branch','roots','border','column'):
        return _minor(style,role,variation)
    if role in ('tree','grove'):
        w,h=SIZES[role];detail=2
        return {7:_lightning_tree,8:_birch_tree,9:_cedar_tree,10:_elm_tree}[style](w,h,detail,bool(variation&1))
    raise NotImplementedError((style,role))

