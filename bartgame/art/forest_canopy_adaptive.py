"""Native, differently sized tree compositions for room-shaped forest masks.

Every piece is drawn on its final indexed canvas. A hero tree is a different
anatomical drawing from a sapling, not an enlarged 16/32 pixel repeating tile.
The room composer owns placement; these images do not choose a world grid.
"""
from functools import lru_cache
from PIL import Image, ImageDraw

PALETTE_NAME = 'canopy_adaptive'
PALETTE = [
    '#000000', '#080810', '#181820', '#484038', '#807058',
    '#201828', '#403048', '#685068', '#183828', '#385838',
    '#708848', '#401060', '#9820d0', '#d850e8', '#f0d8f0', '#a8a078',
]
GREEN_INDICES = (8, 9, 10)
PULSE_INDICES = (11, 12, 13, 14)
ROLE_SIZES = {
    'small': (16, 16), 'clump': (32, 32), 'tree': (48, 48),
    'grove': (64, 64), 'hero': (96, 64), 'branch': (64, 16),
    'roots': (32, 16), 'border': (96, 32), 'column': (16, 64),
}
ROLE_ORDER = tuple(ROLE_SIZES)
NAMES = {
    1: 'Ancient Oak Vault', 2: 'Crooked Willow', 3: 'Buttress Beech',
    4: 'Woven Bower', 5: 'Fungal Cathedral',
    6: 'Fallen Crown', 7: 'Lightning Cleft Oak', 8: 'Pale Birch Congregation',
    9: 'Black Cedar Cathedral', 10: 'Sorrow Arch Elm',
}


def new(w, h):
    im = Image.new('P', (w, h), 0)
    palette = [int(c[k:k+2], 16) for c in PALETTE for k in (1, 3, 5)]
    im.putpalette(palette + [0] * (768-len(palette)))
    return im, ImageDraw.Draw(im)


def _valid(style):
    style = int(style)
    if style not in NAMES:
        raise ValueError(style)
    return style


def stage_palette(style=1, stage=3):
    """One geometry atlas, four area-depth material ramps; old banks untouched."""
    _valid(style)
    stage = max(0, min(3, int(stage)))
    rows = [
        {5:'#183028', 6:'#305038', 7:'#587840', 11:'#302820',
         12:'#604830', 13:'#a88850', 14:'#e0d0a0'},
        {5:'#202828', 6:'#384838', 7:'#607048', 11:'#382838',
         12:'#704870', 13:'#b078b0', 14:'#e0c8d0'},
        {5:'#201c28', 6:'#403448', 7:'#685868', 11:'#401858',
         12:'#8828b8', 13:'#c858d8', 14:'#e8c8e8'},
        {},
    ]
    out = list(PALETTE)
    for index, color in rows[stage].items():
        rgb = [int(color[k:k+2], 16) & 248 for k in (1,3,5)]
        out[index] = '#'+''.join('%02x'%v for v in rgb)
    return out


def stage_palettes(style=1):
    return [stage_palette(style, stage) for stage in range(4)]


def extra_palettes(style=1):
    return {PALETTE_NAME: stage_palette(style, 3)}


def palette(name=PALETTE_NAME, style=1):
    if name != PALETTE_NAME:
        raise KeyError(name)
    return stage_palette(style, 3)


def pulse_palettes(style=1, stage=3):
    base = stage_palette(style, stage)
    states = []
    for offset in (0, 8, 16, -8):
        row = list(base)
        for index in PULSE_INDICES:
            rgb = [int(base[index][k:k+2],16) for k in (1,3,5)]
            row[index] = '#'+''.join('%02x'%max(0,min(248,c+offset)) for c in rgb)
        states.append(row)
    return {PALETTE_NAME: states}


def prefab_specs(style=1):
    _valid(style)
    return [{'name': role, 'role': role, 'variation': 0,
             'w': size[0], 'h': size[1], 'size': list(size),
             'footprint': [size[0]//16, size[1]//16],
             'palette': PALETTE_NAME,
             'layer': 'projection' if role == 'branch' else 'blocked_canopy',
             'anchor': [size[0]//2, size[1]-1]}
            for role, size in ROLE_SIZES.items()]


def wood(d, points, width=5, light=True):
    """Tapered woody limb: outline, far plane, upper-left irregular bark plane."""
    points = [(int(x),int(y)) for x,y in points]
    for i in range(len(points)-1):
        a,b = points[i:i+2]
        thick = max(1, int(width)-i)
        d.line([a,b], fill=1, width=thick+2)
        d.line([a,b], fill=2, width=thick)
        if thick > 2:
            d.line([(a[0]-1,a[1]-1),(b[0]-1,b[1]-1)],fill=3,width=max(1,thick-2))
        if light and thick > 3:
            d.line([(a[0]-2,a[1]-1),(b[0]-2,b[1]-1)],fill=4,width=1)
    for x,y in points[1:-1]:
        d.line([(x+1,y),(x+2,y+2),(x+1,y+4)],fill=1)


def vein(d, points, width=1, bright=True):
    pts = [(int(x),int(y)) for x,y in points]
    d.line(pts,fill=11,width=width+2)
    d.line(pts,fill=12,width=width)
    if bright and len(pts)>1:
        d.line(pts[1:3] or pts,fill=13,width=1)
        x,y=pts[1];d.point((x,y),fill=14)


def leaves(d, cx, cy, rx, ry, live=False, seed=0, vein_ribs=True):
    """Irregular leaf mass with pointed fans; no closed oval/capsule outline."""
    cx,cy,rx,ry=map(int,(cx,cy,rx,ry))
    dark,mid,lit=(8,9,10) if live else (5,6,7)
    # Unequal notches and leaf-tip runs keep a crown from looking like masonry.
    pts=[(cx-rx,cy+1),(cx-rx+2,cy-3),(cx-rx+rx//4,cy-ry+3),
         (cx-rx//2-2,cy-ry),(cx-rx//3,cy-ry+2),(cx-1,cy-ry-2),
         (cx+rx//4,cy-ry+1),(cx+rx//2,cy-ry+2),(cx+rx//2+2,cy-ry),
         (cx+rx-2,cy-ry+5),(cx+rx,cy-2),(cx+rx-2,cy+2),
         (cx+rx-5,cy+ry-1),(cx+rx//2,cy+ry+1),(cx+4,cy+ry-1),
         (cx+1,cy+ry+2),(cx-3,cy+ry),(cx-rx//2,cy+ry+1),
         (cx-rx+3,cy+ry-1)]
    if seed&1:
        pts[4]=(cx-rx//3,cy-ry-1);pts[13]=(cx+rx//2,cy+ry-1)
    d.polygon(pts,fill=dark)
    d.polygon([(x+1 if x<cx else x-1,y+1 if y<cy else y-2)
               for x,y in pts],fill=mid)
    d.polygon([(cx-rx+4,cy-1),(cx-rx+rx//3,cy-ry+4),
               (cx-rx//3,cy-ry+2),(cx,cy-ry+3),(cx+rx//3,cy-ry+4),
               (cx+rx-4,cy-2),(cx+rx//2,cy+1),(cx+1,cy-1),
               (cx-rx//3,cy+2)],fill=lit)
    # Individual sprays vary by size: large masses contain leaf ribs, small
    # saplings carry only two/three strong leaf planes, not a reduced texture.
    sprays=max(2,min(8,rx//3))
    for i in range(sprays):
        x=cx-rx+4+(i*(2*rx-8))//max(1,sprays-1)
        y=cy-2+((i*3+seed)%7)-3
        d.polygon([(x-3,y+1),(x-1,y-2),(x+2,y-2),(x+4,y),
                   (x+1,y+2),(x-1,y)],fill=lit if i%3 else mid)
        if vein_ribs and rx>=10:
            d.line([(x-2,y+2),(x+1,y),(x+3,y)],fill=dark)
    if rx>=14:
        d.line([(cx-rx+5,cy+ry-2),(cx-rx+9,cy+ry-1)],fill=dark)
        d.line([(cx+rx-9,cy+ry),(cx+rx-5,cy+ry-2)],fill=dark)


def sparkle(d,x,y,ink=14,size=1):
    d.point((x,y),fill=ink)
    if size:
        d.line((x-size,y,x+size,y),fill=13)
        d.line((x,y-size,x,y+size),fill=13)
        d.point((x,y),fill=ink)


def bracket(d,x,y,rx=9,ry=3):
    d.polygon([(x-rx,y),(x-rx+3,y-ry),(x-3,y-ry-2),(x+3,y-ry-1),
               (x+rx-1,y-1),(x+rx,y+1),(x+rx-3,y+ry),
               (x-rx+2,y+ry-1)],fill=1)
    d.polygon([(x-rx+2,y),(x-rx+4,y-ry+1),(x-2,y-ry),
               (x+3,y-ry+1),(x+rx-2,y),(x+rx-3,y+1),(x-rx+4,y+1)],fill=12)
    d.line([(x-rx+3,y+1),(x-3,y+ry-1),(x+4,y+ry),(x+rx-3,y+1)],fill=15)
    d.line([(x-rx+5,y-1),(x-1,y-ry+1),(x+3,y-ry+2)],fill=13)


def _roots(d, x, y, span, style):
    wood(d,[(x-3,y-7),(x-9,y-3),(x-span,y-1)],4)
    wood(d,[(x+3,y-7),(x+11,y-4),(x+span,y-6)],4)
    wood(d,[(x,y-6),(x+3,y-1),(x+8,y)],3)
    if style in (1,3,5):vein(d,[(x-3,y-7),(x-7,y-3),(x-span+3,y-2)],1)


def _oak(im,d,role,variation):
    w,h=im.size
    if role=='small':
        wood(d,[(8,15),(7,10),(9,5),(13,2)],3)
        leaves(d,4,5,4,3,False);leaves(d,11,4,4,3,True)
        vein(d,[(8,13),(7,9),(9,6)],1);return
    if role=='roots':
        _roots(d,16,15,15,1);leaves(d,5,11,5,3,True);return
    if role=='branch':
        wood(d,[(0,13),(13,10),(25,11),(38,6),(52,7),(63,2)],5)
        wood(d,[(26,10),(20,3),(11,1)],3)
        leaves(d,13,3,10,4,False);leaves(d,47,5,13,5,True)
        vein(d,[(2,12),(17,9),(26,10),(39,5),(52,6)],1);return
    if role=='column':
        wood(d,[(9,63),(7,49),(10,34),(6,20),(9,3)],8)
        for y,x in ((9,5),(27,10),(47,5)):
            leaves(d,x,y,7,5,y==27,seed=y)
        vein(d,[(10,58),(8,46),(10,33),(7,24),(9,11)],1)
        _roots(d,8,63,7,1);return
    if role=='border':
        # Wide shallow branch/crown system, NOT a clipped 96x64 tree.
        for c in ((17,11,17,10,False),(44,8,21,9,False),
                  (78,10,17,11,False),(56,18,14,8,True)):
            leaves(d,*c,seed=variation+int(c[0]))
        wood(d,[(3,28),(23,25),(40,28),(58,21),(77,24),(94,20)],7)
        wood(d,[(39,28),(37,18),(26,12),(16,9)],5)
        wood(d,[(59,23),(70,13),(85,9)],4)
        leaves(d,12,20,10,6,False);leaves(d,83,21,11,6,True)
        vein(d,[(8,27),(24,24),(39,27),(58,20),(72,22)],1)
        sparkle(d,54,20);return
    if role=='clump':
        leaves(d,11,11,10,8,False);leaves(d,24,13,8,7,True)
        wood(d,[(16,31),(15,23),(20,18),(27,16)],5)
        wood(d,[(16,23),(9,18),(3,16)],3)
        leaves(d,7,20,7,5,False);vein(d,[(15,29),(14,23),(20,18)],1)
        _roots(d,16,31,11,1);return
    if role=='tree':
        crowns=[(11,13,10,9,False),(27,11,15,9,False),(37,20,11,8,True),(9,24,8,6,False)]
        trunk=[(23,47),(22,35),(26,24),(20,16)]
        arms=[([(24,34),(12,27),(5,23)],5), ([(25,29),(35,22),(44,22)],5)]
        living=(37,20,11,8)
    elif role=='grove':
        crowns=[(13,16,12,11,False),(37,12,17,11,False),(53,25,12,12,False),(14,35,13,8,True),(41,31,14,9,False)]
        trunk=[(31,63),(28,50),(34,38),(28,23)]
        arms=[([(31,42),(18,32),(5,29)],7), ([(34,38),(47,27),(60,24)],6), ([(29,29),(18,17),(9,13)],5)]
        living=(14,35,13,8)
    else:
        crowns=[(18,17,16,13,False),(43,11,13,10,False),(79,17,16,13,False),
                (16,34,14,9,True),(80,36,14,10,False),(51,27,17,10,False)]
        trunk=[(48,63),(44,50),(49,37),(43,24)]
        arms=[([(48,39),(32,29),(17,26),(3,21)],8),
              ([(48,34),(43,23),(31,13),(22,10)],6),
              ([(51,38),(65,28),(80,26),(94,20)],8),
              ([(57,33),(64,18),(77,8),(84,5)],5)]
        living=(16,34,14,9)
    for c in crowns:leaves(d,*c,seed=int(c[0])+variation)
    wood(d,trunk,11 if role=='hero' else 9)
    for points,width in arms:wood(d,points,width)
    _roots(d,trunk[0][0],h-1,min(w//2-3,24),1)
    # Foreground leaf sprays partly interrupt the limbs; the important forks
    # remain visible rather than being smothered by one continuous canopy disk.
    leaves(d,*living,True,seed=9)
    if role=='hero':
        leaves(d,67,17,11,6,True,seed=3)
        leaves(d,29,14,10,7,False,seed=4)
        vein(d,[(31,60),(42,53),(46,42),(40,32),(30,27),(17,25)],2)
        vein(d,[(46,42),(60,32),(70,29),(81,26)],1)
        d.ellipse((47,45,53,53),fill=1);d.line([(48,46),(50,45),(52,47)],fill=4)
        sparkle(d,46,42);sparkle(d,79,26,13,0)
    else:
        vein(d,[(trunk[0][0]-4,h-4),(trunk[1][0],trunk[1][1]),(trunk[2][0],trunk[2][1])],1)


def _willow(im,d,role,variation):
    w,h=im.size
    if role in ('small','roots','branch','column'):
        _oak(im,d,role,variation)
        if role=='small':d.line([(12,5),(13,9)],fill=9)
        elif role=='branch':
            for x,y in ((13,5),(29,8),(47,7)):
                d.line([(x,y),(x+2,y+5),(x+1,y+8)],fill=6)
                d.line([(x+1,y+5),(x+3,y+7)],fill=7)
        return
    if role=='border':
        for c in ((15,9,14,8,False),(40,8,18,8,True),(69,10,23,9,False),(87,14,9,7,False)):
            leaves(d,*c,seed=int(c[0]))
        wood(d,[(4,29),(23,22),(41,25),(63,18),(80,22),(94,17)],5)
        for x,y in ((10,14),(25,15),(51,14),(66,16),(82,17)):
            wood(d,[(x,y),(x+3,y+5),(x+1,y+11)],2,False)
            leaves(d,x+2,y+8,5,3,x==51,seed=x)
        vein(d,[(8,27),(24,20),(41,23),(62,16),(79,20)],1);return
    cx=w*3//5
    crown_y=10 if h<=48 else 14
    leaves(d,w//4,crown_y+2,w//4-1,9 if h<=48 else 12,False,seed=1)
    leaves(d,w*3//5,crown_y-3,w//4,8 if h<=48 else 10,True,seed=2)
    leaves(d,w*4//5,crown_y+8,w//5-1,9,False,seed=3)
    trunk=[(cx+5,h-1),(cx-1,h-14),(cx-7,h-28),(cx-16,crown_y+8)]
    wood(d,trunk,9 if w>=64 else 7)
    wood(d,[(cx-4,h-23),(w//3,crown_y+15),(4,crown_y+13)],6)
    wood(d,[(cx-9,h-30),(w*3//4,crown_y+10),(w-3,crown_y+4)],5)
    _roots(d,cx+5,h-1,min(w//2-4,20),2)
    # Broken drooping twigs are short and unequal, attached to broad arcs.
    for i,x in enumerate(range(7,w-5,12 if w>=64 else 10)):
        y=crown_y+11+(i%3)*3;ln=7+(i*3)%7
        wood(d,[(x,y),(x+3,y+ln//2),(x+1,y+ln)],2,False)
        leaves(d,x+2,y+ln-2,5,3,i==2,seed=i)
    vein(d,[(cx+3,h-6),(cx-3,h-18),(cx-8,h-29),(w//3,crown_y+14),(6,crown_y+12)],1)
    if w>=64:
        d.ellipse((cx-3,h-23,cx+3,h-16),fill=1)
        d.line([(cx-2,h-21),(cx+1,h-22)],fill=13)
        sparkle(d,cx-4,h-28)


def _beech(im,d,role,variation):
    w,h=im.size
    if role in ('small','branch','column'):
        _oak(im,d,role,variation)
        if role=='column':d.line([(6,5),(4,17),(7,28),(5,39),(8,55)],fill=15)
        return
    if role=='roots':
        d.polygon([(11,0),(21,0),(22,7),(31,13),(30,15),(20,12),(16,9),(11,13),(0,15),(1,12),(9,7)],fill=1)
        d.polygon([(13,0),(19,0),(20,7),(28,13),(21,10),(16,6),(10,10),(3,13),(11,6)],fill=3)
        d.line([(14,1),(13,7),(6,12)],fill=15);vein(d,[(19,2),(19,8),(24,12)],1);return
    if role=='border':
        for c in ((15,11,15,10,False),(46,8,25,9,False),(81,12,15,10,True)):
            leaves(d,*c,seed=int(c[0]))
        wood(d,[(43,31),(42,24),(47,14),(36,8)],12)
        wood(d,[(43,24),(27,19),(10,20)],7)
        wood(d,[(47,16),(64,15),(82,19),(94,16)],6)
        d.line([(39,30),(39,23),(44,14)],fill=15)
        vein(d,[(47,30),(45,24),(50,18),(65,16)],1);return
    cx=w//2
    for c in ((w//4,12,w//4-1,10,False),(w*3//5,10,w//4+1,9,False),
              (w*4//5,24,w//5-1,10,True)):
        leaves(d,*c,seed=int(c[0]))
    # Buttresses are visibly broader than the upright bole, asymmetrical roots.
    trunk=[(cx-6,h-1),(cx-7,h-18),(cx-1,23),(cx-4,12)]
    wood(d,trunk,15 if w>=64 else 11)
    for points,width in (([(cx-3,31),(w//4,23),(3,23)],7),
                          ([(cx-2,23),(w*3//4,18),(w-4,14)],7)):
        wood(d,points,width)
    d.polygon([(cx-10,h-19),(cx-2,h-16),(cx+5,h-5),(w-4,h-1),(w-14,h-1),
               (cx-1,h-9),(cx-7,h-2),(4,h-1),(cx-16,h-10)],fill=1)
    d.polygon([(cx-8,h-18),(cx-3,h-15),(cx+3,h-5),(w-10,h-2),
               (cx-1,h-7),(cx-7,h-4),(9,h-2),(cx-13,h-9)],fill=3)
    d.line([(cx-8,h-6),(cx-10,h-17),(cx-6,24),(cx-8,18)],fill=15)
    d.line([(cx-3,h-16),(cx+1,h-6),(w-12,h-2)],fill=4)
    vein(d,[(cx+1,h-8),(cx-3,h-18),(cx+2,29),(cx+7,24),(cx+2,20)],2)
    d.polygon([(cx-4,h-27),(cx+3,h-29),(cx+6,h-23),(cx+2,h-17),(cx-3,h-20)],fill=1)
    d.line([(cx-2,h-25),(cx+1,h-27),(cx+4,h-23)],fill=13)
    if w>=64:leaves(d,14,35,12,7,True,seed=2)


def _bower(im,d,role,variation):
    w,h=im.size
    if role in ('small','roots','column'):
        _oak(im,d,role,variation)
        if role=='roots':wood(d,[(0,4),(10,7),(21,4),(31,9)],3)
        return
    if role=='branch':
        wood(d,[(0,13),(15,6),(31,8),(48,2),(63,5)],4)
        wood(d,[(0,3),(17,9),(33,4),(47,10),(63,8)],4)
        leaves(d,13,4,11,4,False);leaves(d,44,5,13,5,True)
        vein(d,[(1,12),(16,5),(31,7),(47,1)],1);return
    if role=='border':
        for c in ((12,11,12,10,True),(38,9,19,9,False),(68,10,24,10,False),(89,17,8,7,False)):
            leaves(d,*c,seed=int(c[0]))
        wood(d,[(12,31),(20,24),(36,17),(54,21),(73,12),(94,15)],5)
        wood(d,[(75,31),(70,23),(52,16),(36,21),(17,13),(2,16)],6)
        vein(d,[(13,30),(21,24),(36,17),(54,21),(73,12)],1);return
    left=w//4;right=w*3//4
    for c in ((left,13,w//4-1,10,False),(w//2,8,w//4,8,False),
              (right,18,w//4-1,12,True),(w//2,29,w//4-2,9,False)):
        leaves(d,*c,seed=int(c[0]))
    wood(d,[(left-4,h-1),(left+4,h-16),(w//2,31),(right-7,21),(w-3,18)],8)
    wood(d,[(right+3,h-1),(right-5,h-14),(w//2-2,34),(left+2,22),(3,20)],7)
    wood(d,[(w//2,32),(w//2+2,19),(w//2-8,10)],5)
    wood(d,[(left+4,h-16),(left-6,h-25),(4,h-24)],4)
    _roots(d,left-4,h-1,min(17,left-2),4);_roots(d,right+3,h-1,min(15,w-right-3),4)
    vein(d,[(left-2,h-5),(left+7,h-17),(w//2+1,32),(right-5,23)],1)
    vein(d,[(right+1,h-4),(right-7,h-15),(w//2-1,35),(left+3,24)],1,False)
    if w>=64:leaves(d,w//2+12,35,13,7,True,seed=4)


def _fungal(im,d,role,variation):
    w,h=im.size
    if role=='small':
        wood(d,[(7,15),(6,9),(10,4)],5)
        leaves(d,11,4,4,3,True,seed=3)
        bracket(d,7,9,6,2);return
    if role=='roots':
        wood(d,[(9,1),(13,9),(27,14)],7)
        wood(d,[(14,8),(6,12),(0,11)],4)
        bracket(d,16,6,11,3);leaves(d,26,10,5,3,True);return
    if role=='branch':
        wood(d,[(0,12),(17,10),(24,5),(41,6),(54,2),(63,3)],6)
        leaves(d,17,4,12,4,False);leaves(d,55,4,8,4,True)
        for x,y,rx in ((12,10,9),(32,6,12),(51,4,7)):
            bracket(d,x,y,rx,2)
        vein(d,[(1,12),(16,10),(24,5),(40,6)],1);return
    if role=='column':
        wood(d,[(6,63),(11,48),(5,35),(10,20),(7,3)],8)
        leaves(d,7,7,7,5,False);leaves(d,11,30,5,4,True)
        for x,y,rx in ((6,18,7),(9,37,7),(5,52,5)):
            bracket(d,x,y,rx,3)
        vein(d,[(5,60),(10,48),(5,35)],1);return
    if role=='border':
        leaves(d,15,10,14,9,False);leaves(d,49,8,22,8,False);leaves(d,79,12,16,10,True)
        wood(d,[(4,29),(24,25),(47,28),(68,19),(94,23)],9)
        for x,y,rx in ((18,22,12),(46,19,15),(66,25,12),(84,19,10)):bracket(d,x,y,rx,3)
        vein(d,[(5,27),(24,23),(46,26),(67,17),(87,21)],1);return
    # A low, heavily leaning bole makes shelves into steps along one long
    # diagonal. This is its own tree anatomy, not the oak with extra caps.
    layouts={
        'clump': ([(9,31),(7,23),(14,15),(23,11)],7,
                  [[(13,17),(9,9),(2,5)]],
                  [(9,6,8,5,False),(24,8,7,6,True)],
                  [(9,25,7),(16,16,9)]),
        'tree': ([(14,47),(10,35),(21,26),(34,21),(39,11)],10,
                 [[(21,26),(15,16),(3,13)],[(32,22),(27,12),(30,5)]],
                 [(12,10,11,7,False),(31,8,12,7,False),(40,23,7,7,True)],
                 [(14,36,10),(26,25,12),(36,15,8)]),
        'grove': ([(20,63),(14,48),(24,37),(42,29),(53,15)],13,
                  [[(25,38),(17,24),(4,19)],[(42,29),(36,16),(42,7)]],
                  [(14,16,13,11,False),(39,10,15,8,False),(53,23,10,11,False),
                   (12,35,10,7,True)],
                  [(20,49,13),(34,35,16),(49,23,12)]),
        'hero': ([(31,63),(23,51),(32,39),(56,30),(73,18),(84,10)],15,
                 [[(32,40),(23,29),(12,22),(2,18)],
                  [(51,33),(43,22),(50,9)],[(68,22),(83,24),(94,19)]],
                 [(16,14,15,11,False),(43,11,16,9,False),
                  (76,10,19,10,False),(86,30,9,9,True),(12,36,10,7,True)],
                 [(30,51,15),(45,36,20),(65,25,16),(81,14,10)]),
        'authored_small': ([(16,47),(10,35),(16,26),(24,18),(26,7)],9,
                           [[(16,27),(8,18),(2,16)],[(23,19),(16,10),(19,4)]],
                           [(9,11,8,8,False),(23,8,8,7,False),(26,25,5,6,True)],
                           [(14,37,10),(21,25,10),(25,15,6)]),
        'authored_large': ([(24,63),(15,49),(22,36),(36,26),(42,14)],12,
                           [[(22,37),(13,26),(2,20)],[(35,27),(27,16),(31,6)]],
                           [(12,15,11,10,False),(31,10,13,9,False),
                            (40,29,7,8,True),(9,36,8,6,True)],
                           [(22,49,13),(28,35,16),(39,23,10)]),
    }
    if role=='authored':role='authored_large' if w==48 else 'authored_small'
    trunk,width,arms,crowns,shelves=layouts.get(role,layouts['tree'])
    for c in crowns:leaves(d,*c,seed=variation+int(c[0]))
    wood(d,trunk,width)
    for i,points in enumerate(arms):wood(d,points,max(4,width-5-i))
    _roots(d,trunk[0][0],h-1,min(w//2-3,22),5)
    for i,(x,y,rx) in enumerate(shelves):
        bracket(d,x,y,rx,3 if w<64 else 4)
        if i%2==0:d.line([(x-rx+5,y-1),(x-2,y-2),(x+4,y)],fill=6)
    vein(d,[(trunk[0][0]-2,h-4)]+[(x-1,y) for x,y in trunk[1:4]],1)
    if w>=48:
        x,y=trunk[2]
        d.ellipse((x-4,y-5,x+3,y+2),fill=1)
        d.line([(x-2,y-3),(x,y-4),(x+2,y-1)],fill=12)
        sparkle(d,x,y-3)


def _authored_oak(im,d,large=False,second=False):
    """Old authored footprint, new explicitly drawn 32x48/48x64 tree."""
    w,h=im.size
    if not large:
        for c in ((8,11,8,9,False),(22,10,10,8,False),(10,23,9,6,True)):
            leaves(d,*c,seed=int(c[0]))
        points=[(17,47),(14,36),(18,26),(15,16)]
        wood(d,points,8)
        wood(d,[(17,28),(8,23),(1,19)],5)
        wood(d,[(18,25),(26,20),(31,17)],4)
        _roots(d,17,47,12,1)
        vein(d,[(13,45),(12,37),(16,28),(10,24)],1)
        if second:leaves(d,25,25,7,5,False,seed=5)
    else:
        for c in ((12,13,11,10,False),(33,12,13,10,False),
                  (11,30,10,8,True),(36,28,11,9,False),(25,19,11,8,False)):
            leaves(d,*c,seed=int(c[0]))
        wood(d,[(25,63),(21,50),(27,37),(22,25),(27,15)],10)
        wood(d,[(25,39),(12,30),(2,24)],6)
        wood(d,[(27,35),(38,29),(47,20)],6)
        _roots(d,25,63,20,1)
        leaves(d,8,35,8,5,True,seed=1)
        vein(d,[(15,60),(20,52),(24,40),(18,32),(8,28)],1)
        if second:leaves(d,37,18,9,7,True,seed=7)


@lru_cache(None)
def authored_tree(style=1, large=False, second=False):
    """Explicit native art for the existing grouped tree physical footprints."""
    style=_valid(style)
    if style>=6:
        import forest_canopy_adaptive_b as other
        im=other.authored_tree(style,large,second)
    else:
        im,d=new(*( (48,64) if large else (32,48) ))
        if style==1:
            _authored_oak(im,d,bool(large),bool(second))
        elif style==5:
            _fungal(im,d,'authored',int(second))
        else:
            (_willow,_beech,_bower)[style-2](im,d,'authored',int(second))
    assert im.mode=='P' and im.size==((48,64) if large else (32,48))
    assert set(im.getdata())<=set(range(16))
    return im


def _blocked_backing(im,style,role,variation):
    """Dense subdued forest behind a full blocked rectangle, not a floor hole.

    Flat ink5 joins the component's quiet backing. Only a small organic outer
    margin is transparent; the visible trunk/crown owns the visual hierarchy.
    This is deliberately not a row of little tree/leaf icons.
    """
    w,h=im.size
    back,d=new(w,h)
    # A contact fringe is not a flat panel. Unequal native contour runs are
    # independent of the 16px world cell, while the full interior remains a
    # truthful dense obstacle. Native roots are restored over this silhouette.
    top=(3,3,1,2,4,2,1,3,2,2,4,1,2)
    bottom=(3,1,2,4,3,2,5,3,1,2,4,2,3,1,4)
    side=(2,3,1,2,4,2,1,3,2,2,4)
    span=max(3,w//13)
    shift=(style+variation+len(role))%len(bottom)
    px=back.load()
    for y in range(h):
        left=side[(y//5+style)%len(side)]
        right=side[(y//4+style+3)%len(side)]
        for x in range(left,w-right):
            upper=top[(x//span+style)%len(top)]
            lower=bottom[(x//span+shift)%len(bottom)]
            if upper<=y<h-lower:px[x,y]=5
    # Sparse attached tufts break a contact without drawing a bright repeating
    # wave, continuous ledge or equal green pads around each prefab rectangle.
    for n,x in enumerate(range(7,w-3,23 if w>=48 else 17)):
        floor=h-bottom[(x//span+shift)%len(bottom)]-1
        y=max(3,floor-3-(n%2))
        d.line([(x-2,y+2),(x,y),(x+2,y+1)],fill=2)
        if n%2==0:d.line([(x+1,y),(x+2,y-2)],fill=6)
    mask=Image.frombytes('L',im.size,bytes(255 if v else 0 for v in im.tobytes()))
    back.paste(im,(0,0),mask)
    return back


@lru_cache(None)
def prefab(style=1, role='hero', variation=0):
    style=_valid(style)
    if role not in ROLE_SIZES:
        raise KeyError(role)
    if style>=6:
        import forest_canopy_adaptive_b as other
        im=other.paint(style,role,variation)
    else:
        im,d=new(*ROLE_SIZES[role])
        (_oak,_willow,_beech,_bower,_fungal)[style-1](im,d,role,int(variation))
    assert im.mode=='P' and im.size==ROLE_SIZES[role],(style,role,im.mode,im.size)
    assert set(im.getdata()) <= set(range(16)),(style,role)
    if role!='branch':
        im=_blocked_backing(im,style,role,int(variation))
    return im


def quiet_fill(style=1, variation=0):
    """Low-contrast underbrush backing, not a field of repeated tree icons."""
    _valid(style)
    # Detail belongs to the tree composition, not a repeated bright rim in
    # every residual tile. The boundary alias supplies the organic alpha edge.
    im,d=new(16,16);d.rectangle((0,0,15,15),fill=5)
    return im


@lru_cache(None)
def blocked_branch(style=1):
    """Long native limb with quiet mass for a solid thin forest component.

    The ordinary branch role remains transparent for overhangs on clear floor.
    This separately packed map keeps a thin blocked arm visually impassable.
    """
    style=_valid(style)
    return _blocked_backing(prefab(style,'branch'),style,'solid_branch',0)
