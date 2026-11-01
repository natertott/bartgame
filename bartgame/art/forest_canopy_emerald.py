"""Original native foliage-first canopy, informed by the supplied Emerald crop.

The reference supplies crown/cluster/contact design principles, not pixel data.
Every role is drawn on its final indexed canvas. Exterior gaps are transparent;
there is no rectangular underbrush/backdrop layer in these pictures.
"""
from functools import lru_cache
from PIL import Image, ImageDraw

PALETTE_NAME = 'canopy_emerald'
NAMES = {1: 'Leafwoven Canopy'}
ROLE_SIZES = {
    'small': (16, 16), 'clump': (32, 32), 'tree': (48, 48),
    'grove': (64, 64), 'hero': (96, 64), 'branch': (64, 16),
    'roots': (32, 16), 'border': (96, 32), 'column': (16, 64),
}
ROLE_ORDER = tuple(ROLE_SIZES)
LEAF_INDICES = (4, 5, 6, 7, 8, 9, 10, 15)
GREEN_INDICES = (8, 9, 10)
PULSE_INDICES = (11, 12, 13, 14)
# 1 outline, 2/3 exposed wood, 4..7 major crown planes, 8..10 surviving
# living sprays, 11..14 attached infection/light, 15 matte leaf-tip light.
PALETTE = [
    '#000000', '#182828', '#202020', '#585040', '#202830',
    '#405040', '#606850', '#889068', '#184830', '#388048',
    '#80b060', '#403058', '#9030c8', '#d060e0', '#f0d8f0', '#b0b088',
]
_STAGES = (
    {1:'#183828',2:'#302820',3:'#786040',4:'#184830',5:'#286838',
     6:'#508848',7:'#88b858',8:'#185038',9:'#408850',10:'#98c068',
     11:'#385040',12:'#608048',13:'#a8c878',14:'#e0e0a8',15:'#c0d878'},
    {1:'#203828',2:'#282820',3:'#706048',4:'#204830',5:'#386040',
     6:'#688050',7:'#a0b070',8:'#185038',9:'#408850',10:'#90b860',
     11:'#404048',12:'#786088',13:'#b898b8',14:'#e0d8d0',15:'#c0c888'},
    {1:'#202828',2:'#202020',3:'#605840',4:'#283830',5:'#485040',
     6:'#788060',7:'#a8a880',8:'#184830',9:'#388048',10:'#80b060',
     11:'#403050',12:'#8838b0',13:'#c868d0',14:'#e8d0e8',15:'#c0c098'},
    {},
)


def _valid(style):
    if int(style) != 1:
        raise ValueError(style)
    return 1


def stage_palette(style=1, stage=3):
    _valid(style)
    result = list(PALETTE)
    for index, color in _STAGES[max(0, min(3, int(stage)))].items():
        result[index] = color
    return ['#'+''.join('%02x'%(int(c[k:k+2],16)&248) for k in (1,3,5)) for c in result]


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
    for step in (0, 8, 16, -8):
        row = list(base)
        for index in PULSE_INDICES:
            rgb = [int(base[index][k:k+2], 16) for k in (1, 3, 5)]
            row[index] = '#' + ''.join('%02x' % max(0, min(248, v+step)) for v in rgb)
        states.append(row)
    return {PALETTE_NAME: states}


def _new(w, h):
    im = Image.new('P', (w, h), 0)
    colors = [int(c[k:k+2], 16) for c in stage_palette(1,3) for k in (1, 3, 5)]
    im.putpalette(colors + [0]*(768-len(colors)))
    return im


def prefab_specs(style=1):
    _valid(style)
    return [{'name': role, 'role': role, 'variation': 0,
             'w': w, 'h': h, 'size': [w, h], 'footprint': [w//16, h//16],
             'palette': PALETTE_NAME,
             'layer': 'projection' if role == 'branch' else 'blocked_canopy',
             'anchor': [w//2, h-1]}
            for role, (w, h) in ROLE_SIZES.items()]


def _fan(d, x, y, wide, dark, mid, light, tip=False):
    """Pointed overlapping leaves; shadow only beneath, not a closed stone rim."""
    if wide:
        d.polygon([(x-3,y),(x-1,y+3),(x+1,y+1),(x+3,y+3),
                   (x+5,y),(x+2,y-1)], fill=dark)
        d.polygon([(x-3,y),(x-1,y-3),(x,y-1),(x+2,y-3),
                   (x+5,y),(x+2,y+1),(x+1,y),(x-1,y+1)], fill=mid)
        d.line([(x-2,y-1),(x-1,y-2),(x,y-1)], fill=light)
        d.line([(x+1,y-1),(x+2,y-2),(x+3,y-1)], fill=light)
        if tip: d.point((x-1,y-2), fill=15)
    else:
        d.line((x-2,y+1,x+2,y+1), fill=dark)
        d.polygon([(x-2,y),(x,y-2),(x+2,y),(x+1,y+1),
                   (x,y),(x-1,y+1)], fill=mid)
        d.point((x,y-1), fill=light)


@lru_cache(None)
def _crown(w, h, seed=0, living=False, infection=True):
    """Dense domed crown on its own native canvas, with a hanging leaf skirt.

    Crown dimensions alter anatomy and cluster count directly; no rendered
    asset is resized. Leaf rows follow the dome, rather than a world tile grid.
    """
    im = _new(w, h); d = ImageDraw.Draw(im)
    # Unequal tips and lobes form the silhouette; the south skirt is narrower
    # and darker than the broad light-catching upper leaf volume.
    cx = w//2
    pts = [(0,h*3//8),(2,h//4),(w//8,h//4),(w//8,h//8),
           (w//4,h//8),(w//4,2),(cx-3,0),(cx+3,1),
           (w*3//4,3),(w*3//4,h//8),(w*7//8,h//6),
           (w-3,h//3),(w-1,h//3+2),(w-1,h*3//5),
           (w-3,h*3//5),(w-3,h*3//4),(w*7//8,h*3//4),
           (w*7//8,h*7//8),(w*3//4,h*7//8),
           (w*3//4,h-2),(cx+3,h-2),(cx,h-1),
           (cx-4,h-3),(w//4,h-3),(w//4,h*7//8),
           (w//8,h*7//8),(w//8,h*3//4),(2,h*3//4),(2,h*5//8),(0,h*5//8)]
    d.polygon(pts, fill=1)
    shape = im.point(lambda v: 255 if v else 0, 'L')
    plane = _new(w, h); p = ImageDraw.Draw(plane)
    dark, mid, light = (8,9,10) if living else (4,5,6)
    p.rectangle((0,0,w-1,h-1), fill=dark)
    p.polygon([(0,h//5),(w//4,0),(w*3//4,1),(w-1,h//3),
               (w-3,h*3//5),(w*3//4,h*4//5),(w//3,h*3//4),
               (1,h*3//5)], fill=mid)
    p.polygon([(1,h//3),(w//4,2),(cx+4,1),(w*3//4,h//5),
               (w*3//4,h//2),(cx,h*3//5),(w//5,h//2)], fill=light)
    # Deliberately offset rows and fan group sizes. Far-side/lower fans keep
    # their dark underside; upper-left tips pick up the warm key light.
    row = 0
    y = 4
    while y < h-2:
        # Cluster groups travel around the dome in unequal curved rows. Small
        # quiet patches expose its broad volume instead of a full fish-scale grid.
        offset = (2,5,1,4,3)[(row+seed)%5]
        x = offset; col = 0
        while x < w:
            yy = y + ((col+row*2+seed)%3-1)
            upper = y < h*3//5 and x < w*3//4
            lower = y > h*3//4
            quiet = ((x-w//3)**2+(y-h//3)**2 < max(4,w//10)**2 and
                     (row+col+seed)%3 == 0)
            if living:
                a,b,c = (8,9,10)
            elif lower:
                a,b,c = (4,5,6)
            elif upper:
                a,b,c = (5,6,7)
            else:
                a,b,c = (4,5,6)
            if not quiet:
                _fan(p,x,yy,(row+col+seed)%4 != 0,a,b,c,
                     tip=upper and (row+col+seed)%7==1)
            x += (5,7,6,8)[(col+row+seed)%4]; col += 1
        y += (4,5,4,6)[(row+seed)%4]; row += 1
    # A few surviving sprays are material-attached, unequal patches, not one
    # equal green oval in every 16px cell. The same ink roles remain green at depth.
    if not living:
        spots = [(w//5,h//3),(w*3//4,h//2),(cx-2,h*3//5)]
        pick = (seed*5+1)%3
        for i in range(2 if w>=30 else 1):
            x,y = spots[(pick+i)%3]
            for dx,dy,wide in ((-3,0,True),(2,0,True),(5,3,False),(-1,4,True)):
                _fan(p,x+dx,y+dy,wide,8,9,10)
    # Follow cracks between leaf clusters. No large naked trunk/Y is drawn.
    if infection and w>=18:
        x=w*3//5 + (seed%3-1)*2;y=h//2
        path=[(x-3,y-5),(x,y-2),(x-1,y+1),(x+3,y+3),(x+2,y+6)]
        p.line(path, fill=11, width=3)
        p.line(path, fill=12, width=1)
        p.line(path[1:3], fill=13, width=1)
        p.point(path[1], fill=14)
        if w>=30:
            p.line([(x+3,y+3),(x+7,y+2),(x+9,y+4)], fill=12)
            p.point((x+8,y+3), fill=13)
    # Restore the native irregular outline after masking the foliage planes.
    # The open top uses leaf tips, while the darkest contact is localized to
    # the lower hanging skirt instead of surrounding the entire object.
    im.paste(plane, (0,0), shape)
    pix=im.load();mask=shape.load()
    for y in range(h):
        for x in range(w):
            if not mask[x,y]:continue
            boundary = any(not(0<=xx<w and 0<=yy<h) or not mask[xx,yy]
                           for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
            if boundary:
                pix[x,y] = 4 if not living else 8
                if y>h*3//4:pix[x,y]=1
    return im


def _paste(dst, src, at):
    dst.paste(src, at, src.point(lambda v: 255 if v else 0, 'L'))


def _trunk(dst, x, y, height=7, width=5):
    d=ImageDraw.Draw(dst)
    d.ellipse((x-width-4,y+height-2,x+width+4,y+height+1), fill=1)
    d.polygon([(x-width//2,y),(x+width//2,y),(x+width//2,y+height-2),
               (x+width,y+height),(x-1,y+height-1),(x-width,y+height)], fill=2)
    d.line([(x-1,y+1),(x-1,y+height-2),(x-3,y+height-1)], fill=3)


def _prototype(role):
    w,h=ROLE_SIZES[role];im=_new(w,h)
    if role=='clump':
        _trunk(im,16,25,6,4)
        _paste(im,_crown(29,28,2),(1,0))
    elif role=='tree':
        _trunk(im,25,38,9,7)
        _paste(im,_crown(44,41,4),(2,0))
        _paste(im,_crown(21,24,5),(0,18))
    elif role=='hero':
        # Whole unequal skirts end within this native frame. Only individual
        # leaf tips meet its edges, so exterior ground contact is scalloped.
        _paste(im,_crown(35,35,1),(0,0))
        _paste(im,_crown(43,39,3),(53,0))
        _paste(im,_crown(42,47,6),(0,17))
        _paste(im,_crown(57,54,4),(20,0))
        _paste(im,_crown(39,45,9),(57,19))
        _paste(im,_crown(44,40,8),(27,24))
    return im


def prefab(style=1, role='hero', variation=0):
    _valid(style)
    if role in ('hero','tree','clump'):
        return _prototype(role)
    w,h=ROLE_SIZES[role];im=_new(w,h)
    if role=='small':
        _trunk(im,8,12,3,2)
        _paste(im,_crown(15,14,3, infection=False),(0,0))
        d=ImageDraw.Draw(im);d.line([(9,5),(10,7),(9,9)],fill=12);d.point((10,7),fill=13)
    elif role=='grove':
        _paste(im,_crown(31,35,3),(0,0))
        _paste(im,_crown(42,46,8),(22,0))
        _paste(im,_crown(36,41,2),(0,23))
        _paste(im,_crown(33,36,6),(31,28))
    elif role=='branch':
        # Upper leaf skirt projects over floor; alpha between the unequal
        # hanging sprays lets ground and Bloom remain visible below it.
        _paste(im,_crown(24,17,8),(-5,-5))
        _paste(im,_crown(29,19,3),(12,-7))
        _paste(im,_crown(25,16,6),(40,-5))
    elif role=='roots':
        _trunk(im,14,9,6,3)
        _paste(im,_crown(19,15,2, infection=False),(-2,-3))
        _paste(im,_crown(23,17,5, infection=False),(10,-5))
        d=ImageDraw.Draw(im);d.line([(13,9),(14,11),(13,13)],fill=12);d.point((14,11),fill=13)
    elif role=='border':
        _paste(im,_crown(30,30,6),(0,0))
        _paste(im,_crown(38,32,2),(24,0))
        _paste(im,_crown(33,29,7),(63,1))
        _paste(im,_crown(23,22,5),(56,9))
    elif role=='column':
        _paste(im,_crown(15,24,2),(0,0))
        _paste(im,_crown(16,30,7),(0,16))
        _paste(im,_crown(15,28,3),(1,36))
    return im


def blocked_branch(style=1):
    """Narrow blocked forest strip: overlapping leaves, without a backdrop."""
    _valid(style)
    im=_new(64,16)
    _paste(im,_crown(28,16,2),(0,0))
    _paste(im,_crown(31,16,6),(18,0))
    _paste(im,_crown(25,15,3),(39,1))
    return im


def authored_tree(style=1, large=False, second=False):
    _valid(style)
    w,h=(48,64) if large else (32,48)
    im=_new(w,h)
    if large:
        _trunk(im,24,48,14,8)
        _paste(im,_crown(45,53,7 if second else 3),(1,0))
        if second:_paste(im,_crown(23,27,2),(-2,25))
        else:_paste(im,_crown(23,25,6),(26,28))
    else:
        _trunk(im,16,35,11,5)
        _paste(im,_crown(30,39,4 if second else 1),(1,0))
        if second:_paste(im,_crown(15,17,6),(-1,21))
    return im


def quiet_fill(style=1, variation=0):
    """Subordinate dense foliage join; every dark patch contains leaf planes."""
    _valid(style)
    im=_new(16,16);d=ImageDraw.Draw(im);d.rectangle((0,0,15,15),fill=5)
    for x,y,wide in ((1,1,True),(10,2,True),(5,6,False),(14,8,True),
                     (1,11,True),(8,13,True)):
        _fan(d,x,y,wide,4,5,6)
    if variation&1:_fan(d,9,8,True,5,6,7)
    return im
