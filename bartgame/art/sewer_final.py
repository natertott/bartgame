"""The selected Drain synthesis, authored directly in native indexed pixels.

Original room coordinates, collision and interaction semantics stay intact.
Per-occurrence final tiles allow side-facing walls and plumbing to survive
map assembly instead of borrowing an unrelated top-wall/floor occurrence.
"""
from functools import lru_cache
import re
from PIL import Image, ImageDraw
import sewer_concepts_terrain as T
import sewer_v3_fixtures as F

RECIPE = {'style':1,'floor':1,'masonry':3,'water':2,'metal':2,
          'bridge':5,'market':1,'sanctum':2,'props':3}


def palette():
    return T.palette(1)


def rail_sprite():
    """Selected rounded brass collars and restrained squared repairs (2/5)."""
    image=T.rail_sprite(2)
    d=ImageDraw.Draw(image)
    d.line((11,3,14,3),fill=8)
    return image


def frame_spec(layer,x,y):
    """Preserve original clocks, adding only the newly visible liquid motion."""
    original=T.ROOM[layer][y][x]
    spec=T.TILES.get(original,{})
    frames,speed=spec.get('frames',1),spec.get('anim_speed',0)
    if layer=='ground':
        if 1<=x<=3 and 9<=y<=11:return (8,8)
        if 4<=x<=5 and 2<=y<=3:return (8,8)
        # The two cistern spillways and their impact share the same flow clock.
        if 14<=x<=15 and 3<=y<=5:return (8,8)
    return (frames,speed)


def _new(fill=0):
    image=Image.new('P',(480,320),fill)
    return image,ImageDraw.Draw(image)


def _stamp(dst,src,xy):
    dst.paste(src,xy,src.point(lambda value:255 if value else 0,'1'))


def _arch_mask(box,inset=0):
    x0,y0,x1,y1=box
    x0+=inset;x1-=inset;y0+=inset
    radius=(x1-x0)//2
    image,d=_new()
    d.pieslice((x0,y0,x1,y0+radius*2),180,360,fill=1)
    d.rectangle((x0,y0+radius,x1,y1),fill=1)
    return image


def _lit_arch(g,box,inset=7):
    """One brass face; continuous upper-left edge and narrow right return.

    No arbitrary x/y threshold changes a broad portion of the arch's face.
    Dark ink belongs to the cavity, inner recess and actual right-side return.
    """
    x0,y0,x1,y1=box
    outer=_arch_mask(box);inner=_arch_mask(box,inset)
    g.paste(13,(0,0),outer.point(lambda value:255 if value else 0,'1'))
    d=ImageDraw.Draw(g)
    # A slender right-facing return is physically distinct from the face.
    for y in range(y0,y1+1):
        for x in range(x1-2,x1+1):
            if outer.getpixel((x,y)):d.point((x,y),fill=12)
    g.paste(1,(0,0),inner.point(lambda value:255 if value else 0,'1'))
    radius=(x1-x0)//2
    # Connected lighting follows the same arch contour into the left jamb.
    d.arc((x0+1,y0+1,x1-1,y0+radius*2-1),180,272,fill=14,width=2)
    d.line((x0+1,y0+radius,x0+1,y1-1),fill=14,width=2)
    d.arc((x0+inset-1,y0+inset-1,x1-inset+1,y0+radius*2-inset+1),180,360,fill=12)
    d.line((x0+inset-1,y0+radius,x0+inset-1,y1),fill=12)
    # Short specular, not a second perimeter or a changing face patch.
    d.arc((x0+2,y0+2,x1-2,y0+radius*2-2),207,239,fill=15)
    return inner


def _ladder(g,o):
    d=ImageDraw.Draw(g)
    _lit_arch(g,(128,0,175,71),7)
    # Taller dark recess, forty-four-pixel stiles and seven clear rungs.
    for x in (144,159):
        d.rectangle((x,27,x+1,71),fill=12)
        d.line((x,27,x,70),fill=14)
    for y in range(31,72,6):
        d.line((146,y,158,y),fill=14)
        d.line((147,y+1,158,y+1),fill=13)
        d.point((146,y),fill=15)
    # User-requested arrow ABOVE the ladder, entirely below the compact HUD.
    d.polygon([(151,14),(156,19),(153,19),(153,24),(149,24),
               (149,19),(146,19)],fill=15)
    d.line((144,71,160,71),fill=14)
    # Original foreground cells remain the only occluding cells.
    for y in range(0,48):
        for x in range(128,176):
            if x<144 or x>159 or y<27:o.putpixel((x,y),g.getpixel((x,y)))


def _cistern(g,phase,period):
    d=ImageDraw.Draw(g)
    inner=_lit_arch(g,(208,16,271,85),8)
    for x in range(222,260,9):
        for y in range(28,83):
            if inner.getpixel((x,y)):
                d.point((x,y),fill=13)
                if inner.getpixel((x+1,y)):d.point((x+1,y),fill=12)
    d.line((217,59,261,59),fill=13,width=2)
    for x,y in ((214,38),(265,38),(211,62),(268,62)):
        d.rectangle((x-1,y-1,x+1,y+1),fill=12)
        d.point((x-1,y-1),fill=14)
    # Preferred option2 split-water construction, kept independent of metal.
    F._basin(g,2,phase,period)


def _north_pipe(g,phase,period):
    """Large broken cylinder, exposed dark cut ends and a falling leak."""
    d=ImageDraw.Draw(g)
    for x0,x1 in ((18,73),(91,125)):
        d.rectangle((x0,28,x1,45),fill=12)
        d.rectangle((x0,29,x1,41),fill=13)
        d.rectangle((x0,29,x1,32),fill=14)
        d.line((x0+2,29,min(x1-2,x0+16),29),fill=15)
    for x in (29,54,112):
        d.rectangle((x-2,26,x+3,46),fill=12)
        d.rectangle((x-1,27,x+2,43),fill=13)
        d.line((x-1,27,x+2,27),fill=14)
        d.point((x,44),fill=14)
    # A right-facing break with an elliptical cut rim, and a ragged opposite.
    d.ellipse((69,28,80,45),fill=14)
    d.ellipse((72,30,79,43),fill=1)
    d.arc((69,28,80,45),185,270,fill=15)
    d.line((72,43,78,43),fill=12)
    d.polygon([(91,28),(96,29),(94,34),(96,37),(93,41),(94,45),
               (89,45),(90,40),(88,36),(91,32)],fill=12)
    d.line((91,28,94,29),fill=14)
    # A small wet catch at the masonry ledge: contact ties leak to material.
    d.ellipse((72,53,88,57),fill=8)
    d.line((74,54,85,54),fill=10)
    travel=(int(phase)*12//max(1,period))%12
    for offset in (0,7):
        yy=43+(travel+offset)%12
        d.line((77,yy,77,min(55,yy+2)),fill=10)
        d.point((77,yy),fill=11)
    if phase%4==0:d.line((74,55,80,55),fill=11)


def _side_walls(g):
    d=ImageDraw.Draw(g)
    # Continuous parapet cap and inward-facing return; no north-wall block
    # fronts are copied down either side of the screen.
    for x0,inner in ((0,15),(464,464)):
        d.rectangle((x0,0,x0+15,271),fill=2)
        if x0==0:
            d.rectangle((2,0,9,271),fill=4)
            d.line((2,0,2,271),fill=5)
            d.rectangle((10,0,13,271),fill=3)
            d.rectangle((14,0,15,271),fill=1)
        else:
            d.rectangle((467,0,477,271),fill=3)
            d.line((467,0,467,271),fill=4)
            d.rectangle((464,0,466,271),fill=1)
            d.line((478,0,478,271),fill=2)
        # Top-facing coping joints run across the narrow cap, at long intervals.
        for y in range(15,272,24):
            d.line((x0+2,y,x0+11,y),fill=2)
            if (y//24)%3==1:
                d.line((x0+4,y-4,x0+7,y-1),fill=3)
        for y in (73,121,218,247):
            if x0==0:
                d.polygon([(11,y),(13,y+2),(13,y+10),(11,y+7)],fill=9)
            else:
                d.polygon([(466,y),(469,y+1),(468,y+8),(466,y+12)],fill=9)


def _left_outlet(g,phase,period):
    """Profile outlet from the left wall, dumping rightward into the river."""
    d=ImageDraw.Draw(g)
    # Horizontal body exits beyond the left screen edge. Thin end ellipse is
    # seen in PROFILE, rather than the former front-facing gold bank ring.
    d.rectangle((0,152,27,165),fill=12)
    d.rectangle((0,153,27,162),fill=13)
    d.rectangle((0,153,25,155),fill=14)
    d.line((0,153,12,153),fill=15)
    d.rectangle((11,150,16,167),fill=12)
    d.rectangle((12,151,15,164),fill=13)
    d.line((12,151,15,151),fill=14)
    d.ellipse((23,151,31,166),fill=14)
    d.ellipse((27,154,31,163),fill=1)
    d.line((25,164,30,164),fill=12)
    # A short coherent ballistic sheet bends once with gravity, from lip to
    # landing. Pale packets and spray move DOWNSTREAM on this same silhouette.
    d.polygon([(30,157),(35,158),(41,162),(46,168),(48,175),
               (44,177),(41,170),(37,166),(33,164),(30,163)],fill=9)
    d.polygon([(30,158),(35,159),(40,163),(44,169),(46,175),
               (44,175),(40,169),(36,165),(31,162)],fill=10)
    trajectory=((31,159),(35,161),(39,164),(42,168),(44,172),(45,175))
    start=(int(phase)*len(trajectory)//max(1,period))%len(trajectory)
    for n in (start,(start+1)%len(trajectory)):
        x,y=trajectory[n];d.line((x,y,x+1,y+1),fill=11)
    d.ellipse((40,174,55,180),fill=10)
    for x in (41,46,51):
        yy=174+(phase+x)%3
        d.ellipse((x,yy,x+3,yy+2),fill=11)
    rr=(phase*3//max(1,period))
    d.arc((36-rr,174,59+rr,185),5,170,fill=9)
    d.line((49,170+(phase%3),49,172+(phase%3)),fill=11)


@lru_cache(maxsize=32)
def complete_layers(phase=0,period=8):
    phase=int(phase);period=max(1,int(period))
    g,d=_new(3);o,od=_new()
    # Selected #1 running-bond pavement, with one coherent #5 repair panel.
    for y in range(20):
        for x in range(30):
            style=5 if 18<=x<=23 and 13<=y<=15 else 1
            g.paste(T.floor_tile(style,x+y*7),(x*16,y*16))
    for y in range(4):
        for x in range(30):g.paste(T.wall_tile(1 if y%2==0 else 3,(x+y)%5),(x*16,y*16))
    d.line((0,62,479,62),fill=5);d.line((0,63,479,63),fill=1)
    for x in (26,177,302,392):T._slime(d,x,55,17,8,1)
    # The fixed river, banks and bridge preserve the original walking lane.
    d.rectangle((16,144,463,207),fill=8)
    for y in (160,176,288,304):
        for x in range(16 if y<200 else 0,464 if y<200 else 480,16):
            g.paste(T.water_tile(2,phase,x//16+y//16*7,period),(x,y))
    for x in range(16,464,16):
        g.paste(T._bank_tile(1,'n',x//16),(x,144))
        g.paste(T._bank_tile(1,'s',x//16),(x,192))
    for x in range(0,480,16):g.paste(T._bank_tile(4,'b',x//16),(x,272))
    bridge=T._bridge(5)
    bd=ImageDraw.Draw(bridge)
    bd.line((3,19,9,25),fill=5,width=2) # preferred second-study repair
    _stamp(g,bridge,(224,144))
    _cistern(g,phase,period)
    _north_pipe(g,phase,period)
    _ladder(g,o)
    F._pipe(d,(417,6,427,62),3)
    F._market(g,o,1,phase)
    # Horizontal salvage-board counter joinery from selected market3.
    od.line((33,98,110,98),fill=13);od.line((33,102,110,102),fill=13)
    od.rectangle((66,96,75,103),fill=2)
    F._sanctum(g,2,phase)
    F._crate(d,400,65,2);F._crate(d,424,65,3);F._barrel(d,440,72,3)
    for x,y,w,h in ((165,108,28,13),(367,116,29,13),(49,223,32,14),(388,245,27,14),(425,92,18,6)):
        T._slime(d,x,y,w,h,1)
    T._grate(d,(207,225,273,255),1)
    for (x,y),n in T.DEBRIS_SITES.items():
        _stamp(g,T._debris(1 if n%2==0 else 5,n),(x*16,y*16))
    # Selected upper2/5 rail silhouette and lower4 weathered rail.
    T._rails(g,o,5)
    lower_g,lower_o=g.copy(),o.copy()
    T._rails(lower_g,lower_o,4)
    o.paste(lower_o.crop((0,256,480,272)),(0,256))
    _side_walls(g)
    _left_outlet(g,phase,period)
    # Structural corner caps connect side parapets to north wall and lower bank.
    d.line((0,0,479,0),fill=4)
    return g,o


def _parse(name):
    match=re.fullmatch(r'swh_f_([go])_(\d{2})_(\d{2})',name)
    if not match:raise KeyError(name)
    return ('ground' if match[1]=='g' else 'overlay',int(match[2]),int(match[3]))


def paint(name,phase=0):
    if name.startswith('swh_f_'):
        layer,x,y=_parse(name)
        frames,_=frame_spec(layer,x,y)
        g,o=complete_layers(int(phase),frames)
        return (g if layer=='ground' else o).crop((x*16,y*16,x*16+16,y*16+16))
    return T.paint(name,phase,RECIPE)


def full_layers(phase=0):
    """Assemble the final per-occurrence clones exactly as the game does."""
    g,_=_new();o,_=_new()
    for layer,dst,prefix in (('ground',g,'g'),('overlay',o,'o')):
        for y,row in enumerate(T.ROOM[layer]):
            for x,name in enumerate(row):
                if name:dst.paste(paint(f'swh_f_{prefix}_{x:02}_{y:02}',phase),(x*16,y*16))
    return g,o
