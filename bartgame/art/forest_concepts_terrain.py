"""Five unselected native forest studies, preserving retained terrain contracts.

Every shape is drawn directly on its final pixel canvas. No old pixels, HD
source, screenshot or palette-graded image is used. Bank names retain the
shared vocabulary; only BG palettes may use palette(bank,variant).
"""
from functools import lru_cache
import json
from pathlib import Path
import math
from PIL import Image, ImageDraw
import reboot_core as R

RECIPES = {1:'Fern & Oak',2:'Silver Willow',3:'Copper Beech',4:'Velvet Cedar',5:'Pale Orchard'}
CONTRACTS = json.loads(Path(__file__).with_name('reboot_contracts.json').read_text())
NAMES = {m['name'] for m in CONTRACTS['tiles']}
# Interactive matter is authored by forest_concepts_props; glitter is protected.
EXCLUDED = set('bush rock_small boulder rock rock2 rock3 mossy_stone sick_rock stump sick_stump log fence thorn pillar ruin_wall statue bones sick_bones blight_crystal dead_tree forest_blight_dead_tree lantern_post relic shrine_plate myst_pot crack web door_locked door_open torch torch_lit chest chest_open myst_chest myst_chest_open myst_switch myst_switch_down myst_spring mouth_cave mouth_hollow mouth_thicket cave_prop hollow_prop thicket_prop cave_spring hollow_spring thicket_spring stairs_down sparkle sparkle_white'.split())
BANKS=('ground','foliage','water','stone','blight','decay_mix','rot_water')

# Roles are stable. Five distinct structural vocabularies also have their own
# authored cool-shadow/warm-light ramps, already quantized to 5-bit channels.
_GREEN={
1:['#142820','#203c28','#385838','#507048','#708850'],
2:['#182c28','#284838','#406448','#608458','#88a070'],
3:['#202c20','#34482c','#506038','#70804c','#98985c'],
4:['#142828','#203c30','#345840','#507450','#788c60'],
5:['#202c28','#304c38','#486840','#688450','#98a868']}
# Quantize explicitly at authored-bank boundary, rather than trusting arbitrary
# eight-bit hex literals to survive RGB555 unchanged.
def _q(h):
    return '#'+''.join('%02x'%(int(h[i:i+2],16)//8*8) for i in (1,3,5))
_BARK={1:('#282820','#483828','#705038','#907048','#b09060'),
       2:('#283030','#505850','#909888','#b0b8a0','#d0d0b8'),
       3:('#302820','#584028','#885838','#b08048','#d0a868'),
       4:('#282028','#483030','#705040','#987058','#b89870'),
       5:('#30282c','#584038','#806048','#a88060','#c8b088')}
PALETTES={}
for _v in RECIPES:
    _g=list(map(_q,_GREEN[_v]));_b=list(map(_q,_BARK[_v]))
    _ground=['#000000','#101820',*_g,'#403828','#605038','#806848','#a08858','#c0a878','#384840','#586858','#909880','#d8d0a8']
    _foliage=['#000000','#101820',_g[0],_g[1],_g[2],_g[3],_g[4],'#b0c088',*_b,'#183030','#385850','#a0b098']
    _water=['#000000','#101820','#102830','#183c48','#285868','#407880','#68a098','#a8c0b0','#d0d8c0',_g[0],_g[1],_g[2],'#605038','#806848','#b09868','#e0d8b8']
    _stone=['#000000','#101820','#283030','#384038','#50584c','#707868','#909880','#b0b098','#d0d0b0',*_b,'#d8c088','#f0e8c8']
    _blight=['#000000','#141820',_g[0],_g[1],_g[2],'#382838','#604050','#906878',_b[0],_b[1],_b[2],_b[3],_g[3],'#b8b098','#d8c8b0','#eee0c8']
    _decay=['#000000','#101820',_g[0],_g[1],_g[2],'#50402c','#705838','#987448','#302830','#483038','#705048','#987060','#385850','#886048','#d8d0b0','#e8d8a8']
    _rotwater=list(_water);_rotwater[2:9]=['#182828','#283c38','#405048','#586858','#788878','#a0b098','#d0d0b8']
    PALETTES[_v]={n:list(map(_q,p)) for n,p in zip(BANKS,(_ground,_foliage,_water,_stone,_blight,_decay,_rotwater))}
    assert all(len(p)==16 for p in PALETTES[_v].values())


def palette(name,variant=1):
    """Sixteen RGB555 hex inks for an existing BG bank; never install in OBJ."""
    return list(PALETTES[int(variant)].get(name,R.PALETTES[name]))


def supports(name):
    return name in NAMES and name not in EXCLUDED and not name.startswith(('sw_','swh_'))


def _new(w=16,h=16,fill=0):
    im=Image.new('P',(w,h),fill)
    return im,ImageDraw.Draw(im)


def _paste(dst,src,xy):
    dst.paste(src,xy,src.point(lambda v:255 if v else 0,'1'))


def _poly(d,pts,base,lit=None):
    d.polygon(pts,fill=base)
    if lit is not None:d.line(pts[:max(2,len(pts)//2)],fill=lit)


def _floor(variant=1,n=0,earth=False):
    # One quiet middle value, with at most a short blade or material seam.
    im,d=_new(fill=9 if earth else 4)
    if n%4==1:d.line((3,11,5,11),fill=8 if earth else 3)
    elif n%4==2:d.line((11,5,12,4),fill=10 if earth else 5)
    return im


def _side_masks(mask=0,corners=0):
    """Shared quarter masks keep transition families affordable and coherent."""
    im,d=_new()
    # Each 8px quarter depends only on its touching side/corner bits.
    side_polys={1:[(0,0),(15,0),(15,1),(12,2),(9,1),(6,3),(3,2),(0,3)],
        2:[(15,0),(15,15),(13,15),(12,12),(13,9),(11,6),(12,3),(12,0)],
        4:[(0,15),(15,15),(15,13),(12,12),(9,13),(6,11),(3,12),(0,12)],
        8:[(0,0),(0,15),(2,15),(3,12),(2,9),(4,6),(3,3),(3,0)]}
    for bit,pts in side_polys.items():
        if mask&bit:d.polygon(pts,fill=1)
    for bit,pts in ((1,[(0,0),(4,0),(3,2),(0,4)]),(2,[(15,0),(11,0),(12,2),(15,4)]),
                    (4,[(15,15),(11,15),(12,13),(15,11)]),(8,[(0,15),(4,15),(3,13),(0,11)])):
        if corners&bit:d.polygon(pts,fill=1)
    return im


def _transition(mask=0,corners=0,variant=1,kind='path'):
    floor=_floor(variant,0,earth=kind=='path');px=floor.load();m=_side_masks(mask,corners).load()
    for y in range(16):
        for x in range(16):
            if m[x,y]:px[x,y]=4 if kind=='path' else 3 if kind=='verge' else 7
    # The narrow lower/right material contact is quieter than a wall outline.
    for y in range(1,15):
        for x in range(1,15):
            if m[x,y] and not m[x,y+1]:px[x,y]=3 if kind=='path' else 2 if kind=='verge' else 8
    return floor


def _rot_floor(variant=1,n=0,root=False):
    im=_floor(variant,n);d=ImageDraw.Draw(im)
    # Ground remains green. Rot is a rooted structural occurrence, not a hue wash.
    if root and n%3==0:
        d.line([(2,15),(4,13),(5,9)],fill=2)
        d.line([(3,15),(5,13)],fill=5)
    elif n==7:d.line((12,9,13,9),fill=8)
    return im


def _rot_edge(sides,corners,variant):
    im=_floor(variant);d=ImageDraw.Draw(im)
    # Blended damp green earth deliberately avoids a repeated purple-grid floor.
    keep=_side_masks(sides,corners);px=im.load();m=keep.load()
    for y in range(16):
        for x in range(16):
            if not m[x,y]:px[x,y]=4
    return im


def _frond(d,x,y,s,light=5,dark=3):
    d.line([(x,y),(x+1,y-s)],fill=dark)
    for k in range(1,s,2):
        span=max(1,(s-k)//2)
        d.line([(x-span,y-k),(x+1,y-k+1),(x+span+1,y-k-1)],fill=light)


def _decor(name,variant=1):
    im=_floor(variant);d=ImageDraw.Draw(im)
    if name in ('moss_flowers','moss_flowers2'):
        x,y=(5,9) if name.endswith('2') else (10,5)
        d.line((x,y,x,y+2),fill=3);d.line((x-1,y,x+1,y),fill=15);d.point((x,y-1),fill=15)
        return im
    if name=='fern_patch' or name=='tall_grass':
        if variant==1:_frond(d,7,13,9)
        elif variant==2:
            for x,y in ((5,12),(10,12)):d.line([(x,y),(x-2,y-6)],fill=3);d.line([(x,y),(x+2,y-7)],fill=5)
        elif variant==3:
            d.polygon([(4,11),(3,6),(7,3),(8,9)],fill=3);d.line([(4,7),(7,4)],fill=5)
        elif variant==4:
            for x,y in ((4,10),(8,6),(12,12)):d.line([(x-2,y),(x,y-2),(x+2,y)],fill=5)
        else:
            d.line([(3,12),(6,7),(10,5),(12,8)],fill=3);d.ellipse((9,4,12,6),fill=15)
    elif name=='leaf_litter':
        # One connected leaf cluster, not scattered objects resembling pickups.
        d.polygon([(5,10),(7,8),(10,9),(8,11)],fill=8);d.line((6,9,9,9),fill=10)
    return im


def _leaf(d,x,y,rx,ry,kind,shade=3,light=4,deep=2):
    """Connected leaf volumes: no ink outline around each interior cluster."""
    if kind in (1,3,5):
        # Rounded stepped silhouette. Beech spreads farther, orchard leaves
        # break into small lobes, but none uses a faceted stone outline.
        pts=[(x-rx,y-1),(x-rx+1,y-ry+3),(x-rx+3,y-ry+1),
             (x-rx+6,y-ry),(x+2,y-ry),(x+5,y-ry+1),(x+rx-2,y-ry+2),
             (x+rx,y-ry+5),(x+rx,y+2),(x+rx-2,y+ry-1),
             (x+3,y+ry),(x-3,y+ry-1),(x-rx+3,y+ry),(x-rx+1,y+ry-3)]
        d.polygon(pts,fill=shade)
        # A single broad upper-left light mass, with a lobed transition.
        d.polygon([(x-rx+1,y-1),(x-rx+3,y-ry+3),(x-rx+6,y-ry+1),
                   (x+1,y-ry+1),(x+4,y-ry+2),(x+rx-3,y-ry+3),
                   (x+rx-4,y-ry+5),(x+2,y-2),(x-2,y),
                   (x-rx+4,y+1),(x-rx+2,y+ry-2)],fill=light)
        # Irregular near-side leaves hang over the darker body. Their small
        # negative pockets are shadow, not a ring round the volume.
        for j,(lx,ly) in enumerate(((x-rx+4,y+ry-2),(x+1,y+ry-2),(x+rx-2,y+2))):
            d.polygon([(lx-2,ly),(lx,ly+2),(lx+2,ly),(lx+1,ly+3),(lx-1,ly+3)],fill=deep)
        marks=[(x-rx//2,y-ry//2),(x+rx//4,y-ry//3)]
        for j,(lx,ly) in enumerate(marks):
            if kind==3:
                d.line([(lx-2,ly),(lx,ly-1),(lx+3,ly)],fill=5)
                d.line([(lx,ly),(lx+2,ly+2)],fill=shade)
            else:
                d.polygon([(lx-2,ly),(lx,ly-1),(lx+2,ly),(lx+1,ly+1),(lx-1,ly+1)],fill=5)
                if j==0:d.line((lx-1,ly-1,lx+1,ly-1),fill=6)
        if kind==5:
            d.line([(x+rx-3,y+1),(x+rx-5,y+4)],fill=deep)
            d.line([(x-rx+2,y),(x-rx+4,y+2)],fill=deep)
    elif kind==2:
        # A broad umbrella top with a few irregular leaf lances below it.
        pts=[(x-rx,y),(x-rx+1,y-ry+3),(x-rx+4,y-ry+1),(x+2,y-ry),
             (x+rx-2,y-ry+2),(x+rx,y-ry+5),(x+rx-1,y+3),
             (x+rx-4,y+ry),(x+2,y+ry-2),(x-1,y+ry+1),
             (x-4,y+ry-2),(x-rx+1,y+ry)]
        d.polygon(pts,fill=shade)
        d.polygon([(x-rx+2,y-1),(x-rx+4,y-ry+2),(x+1,y-ry+1),
                   (x+rx-3,y-ry+3),(x+3,y-2),(x-3,y),(x-rx+3,y+2)],fill=light)
        for j,(ox,ln) in enumerate(((-rx+3,ry-1),(-2,ry+2),(rx-4,ry-2))):
            d.polygon([(x+ox-1,y),(x+ox+3,y-1),(x+ox+2,y+ln-2),
                       (x+ox,y+ln),(x+ox-1,y+ln-2)],fill=shade)
            d.line([(x+ox,y+1),(x+ox,y+ln-3)],fill=4 if j==0 else 3)
            d.line([(x+ox+2,y+ln-4),(x+ox+1,y+ln-1)],fill=deep)
        d.line([(x-rx+4,y-ry+3),(x-rx+6,y-ry+2),(x-rx+3,y-ry+5)],fill=5)
    else:
        # Cedar: overlapping combed fans, no symmetric diamond bevel.
        pts=[(x-rx,y),(x-rx+3,y-2),(x-3,y-ry),(x,y-ry+1),
             (x+4,y-ry+3),(x+rx,y+2),(x+rx-2,y+ry),
             (x+4,y+ry-1),(x+1,y+ry+1),(x-2,y+ry-1),(x-rx+1,y+ry)]
        d.polygon(pts,fill=shade)
        d.polygon([(x-rx+2,y),(x-3,y-ry+2),(x,y-ry+2),
                   (x+4,y-ry+4),(x+rx-3,y+1),(x+2,y),(x-2,y+2)],fill=light)
        for ox,oy in ((-rx+3,2),(-2,ry-1),(rx-4,3)):
            d.line([(x+ox-2,y+oy),(x+ox,y+oy-2),(x+ox+2,y+oy),
                    (x+ox+3,y+oy-1)],fill=3)
            d.line([(x+ox-1,y+oy+1),(x+ox,y+oy+2)],fill=deep)
        d.line([(x-4,y-ry+3),(x-2,y-ry+2),(x+1,y-ry+4)],fill=5)


@lru_cache(None)
def _canopy32(variant=1,sick=False):
    im,d=_new(32,32,fill=2)
    lobes=((2,3,9,6),(18,3,11,7),(30,13,8,7),(11,15,11,8),(1,28,10,7),(23,29,12,8))
    for i,(x,y,rx,ry) in enumerate(lobes):
        # Wrapped copies ensure every quadrant joins itself at a macro edge.
        for oy in (-32,0,32):
            for ox in (-32,0,32):
                _leaf(d,x+ox,y+oy,rx,ry,variant,3,4,2)
    if sick:
        # Rooting branches create structure; reduced mauve leaves remain local.
        for pts in ([(3,31),(8,23),(6,16),(10,10)],[(25,32),(24,25),(29,19),(30,10)]):
            d.line(pts,fill=8,width=3);d.line([(x-1,y) for x,y in pts],fill=9)
        for x,y in ((8,9),(24,19)):
            d.polygon([(x-3,y),(x,y-2),(x+4,y),(x+1,y+3)],fill=5)
            d.line([(x-2,y),(x,y-1),(x+2,y)],fill=6)
        d.line([(24,25),(27,24),(29,25)],fill=13)
    return im


def _canopy(n=0,face=None,sick=False,variant=1,lantern=False,phase=0):
    macro=_canopy32(variant,sick);im=macro.crop(((n%2)*16,(n//2%2)*16,(n%2+1)*16,(n//2%2+1)*16));d=ImageDraw.Draw(im)
    if face=='s':
        d.rectangle((0,9,15,15),fill=2)
        for x in (3,11):
            d.line([(x,7),(x-1,13),(x+1,15)],fill=8,width=3);d.line([(x-1,9),(x-1,13)],fill=9)
        _leaf(d,3,7,6,4,variant,3,4,2);_leaf(d,12,7,6,5,variant,3,4,2)
    elif face=='n':
        # Raised foliage above a visible near-side trunk shadow.
        d.rectangle((0,0,15,3),fill=2)
        d.line([(0,3),(4,4),(8,2),(12,3),(15,2)],fill=3)
    if lantern:
        d.line((10,4,10,8),fill=8);d.rectangle((8,8,12,13),fill=8)
        d.rectangle((9,9,11,12),fill=11);d.point((9,9),fill=12)
        if phase%2:d.point((10,11),fill=12)
    return im


@lru_cache(None)
def _tree(variant=1,large=False,second=False,sick=False,dead=False):
    w,h=(48,64) if large else (32,48)
    im,d=_new(w,h)
    # Upper crown/overhang is transparent. The last row is the exact grassy
    # footing, with a small contact patch, never a solid purple rectangle.
    for tx in range(w//16):im.paste(_floor(variant), (tx*16,h-16))
    d=ImageDraw.Draw(im);mid=w//2;root=h-9
    # A bent solid trunk widens into a root collar, with three short root
    # directions. No uniformly stroked stick/Y silhouette.
    trunk=[(mid-3,h-34),(mid+3,h-34),(mid+4,h-24),(mid+2,h-16),
           (mid+4,h-9),(mid+9,h-5),(mid+12,h-4),(mid+11,h-2),
           (mid+4,h-3),(mid,h-7),(mid-5,h-3),(mid-13,h-2),
           (mid-12,h-4),(mid-7,h-6),(mid-4,h-12),(mid-5,h-22)]
    d.polygon(trunk,fill=1)
    d.polygon([(mid-2,h-33),(mid+2,h-33),(mid+3,h-24),(mid,h-16),
               (mid+2,h-9),(mid+7,h-4),(mid+3,h-5),(mid,h-10),
               (mid-5,h-5),(mid-10,h-3),(mid-7,h-5),(mid-2,h-13),(mid-3,h-23)],fill=9)
    d.line([(mid-2,h-31),(mid-1,h-24),(mid-3,h-18),(mid-1,h-11)],fill=10)
    d.line([(mid+2,h-21),(mid+1,h-15),(mid+2,h-10)],fill=8)
    d.polygon([(mid-3,h-11),(mid,h-12),(mid+3,h-9),(mid+1,h-6),(mid-2,h-7)],fill=8)
    d.line([(mid-2,h-10),(mid,h-11),(mid+1,h-9)],fill=10)
    if dead:
        limbs=[[(mid,h-21),(mid-7,h-30),(mid-11,h-41),(mid-15,h-44)],
               [(mid-7,h-30),(mid-13,h-31),(mid-15,h-35)],
               [(mid,h-25),(mid+7,h-32),(mid+11,h-43),(mid+15,h-46)],
               [(mid+6,h-32),(mid+13,h-34),(mid+14,h-39)],
               [(mid,h-27),(mid-1,h-38),(mid+2,h-46)]]
        if variant==2:
            limbs[0]=[(mid,h-21),(mid-8,h-29),(mid-12,h-37),(mid-14,h-39)]
            limbs[1]=[(mid-10,h-34),(mid-13,h-30),(mid-14,h-23)]
            limbs[3]=[(mid+6,h-32),(mid+12,h-29),(mid+13,h-23)]
        elif variant==3:
            limbs[0]=[(mid,h-21),(mid-8,h-29),(mid-14,h-33),(mid-15,h-38)]
            limbs[2]=[(mid,h-25),(mid+7,h-32),(mid+14,h-35),(mid+15,h-41)]
        elif variant==4:
            limbs[0]=[(mid,h-21),(mid-8,h-27),(mid-14,h-29),(mid-15,h-33)]
            limbs[1]=[(mid-5,h-30),(mid-12,h-35),(mid-13,h-39)]
            limbs[2]=[(mid,h-25),(mid+7,h-29),(mid+14,h-31),(mid+15,h-35)]
            limbs[3]=[(mid+4,h-32),(mid+9,h-36),(mid+8,h-40)]
        elif variant==5:
            limbs[0]=[(mid,h-21),(mid-7,h-30),(mid-10,h-38),(mid-14,h-42)]
            limbs[3]=[(mid+7,h-34),(mid+13,h-37),(mid+12,h-43)]
        for pts in limbs:
            d.line(pts,fill=1,width=4);d.line(pts,fill=8,width=2);d.line([(x-1,y) for x,y in pts],fill=9)
        # Each recipe gives the same limited skeleton a different parasite.
        if variant==1:d.line([(mid+3,h-27),(mid+7,h-28),(mid+10,h-26)],fill=13,width=2)
        elif variant==2:
            d.line([(mid-11,h-39),(mid-12,h-27)],fill=6);d.line([(mid+10,h-35),(mid+8,h-24)],fill=7)
        elif variant==3:d.polygon([(mid+6,h-34),(mid+11,h-36),(mid+13,h-33),(mid+9,h-31)],fill=5);d.line([(mid+7,h-34),(mid+10,h-35)],fill=6)
        elif variant==4:d.line([(mid-6,h-31),(mid-3,h-34),(mid+2,h-31)],fill=5,width=3)
        else:
            for x,y in ((mid-10,h-39),(mid+10,h-36),(mid+1,h-43)):
                d.ellipse((x-1,y,x+2,y+3),fill=13);d.point((x,y),fill=14)
        return im
    if variant==1:
        lobes=[(mid-3,8,10,7),(mid+7,13,8,7),(mid-9,17,9,8),(mid+2,23,11,8)]
    elif variant==2:
        lobes=[(mid-4,7,9,6),(mid+7,10,8,7),(mid-9,16,8,12),(mid+8,20,7,12),(mid,21,10,9)]
    elif variant==3:
        lobes=[(mid-5,8,11,7),(mid+7,12,9,7),(mid-10,19,8,8),(mid+3,23,12,7)]
    elif variant==4:
        lobes=[(mid,5,5,5),(mid-2,11,9,5),(mid+2,18,12,6),(mid-1,25,14,6),(mid+6,30,9,4)]
    else:
        lobes=[(mid-6,7,8,7),(mid+6,8,8,6),(mid-10,18,6,8),(mid+9,19,7,7),(mid,24,9,6)]
        d.line([(mid-2,h-29),(mid-10,h-34),(mid-13,h-42)],fill=8,width=3)
        d.line([(mid+1,h-28),(mid+10,h-34),(mid+13,h-42)],fill=8,width=3)
    if large:lobes += [(8,31,8,8),(mid,37,13,9),(w-9,31,9,8)]
    for i,(x,y,rx,ry) in enumerate(lobes):
        if sick and i in (1,3):continue
        if second:x+=(-1 if i%2 else 1);y+=i%2
        _leaf(d,x,y,rx,ry,variant,3,4,2)
    if sick:
        # Bare anatomy breaks the healthy silhouette, rather than recolouring it.
        for pts in ([(mid,h-18),(mid-4,h-29),(mid-10,h-38)],[(mid,h-23),(mid+8,h-30),(mid+13,h-37)]):
            d.line(pts,fill=8,width=3);d.line([(x-1,y) for x,y in pts],fill=9)
        d.polygon([(mid-4,h-29),(mid-1,h-31),(mid+3,h-29),(mid,h-26)],fill=5)
        d.line([(mid-3,h-29),(mid-1,h-30),(mid+1,h-29)],fill=6)
        d.line([(mid+4,h-24),(mid+7,h-26),(mid+10,h-24)],fill=13)
    return im


def _water(mask=0,corners=0,phase=0,variant=1,rot=False,lily=False):
    im,d=_new(fill=3)
    # Two broad current segments, one crest. Never a field of pickup-like dots.
    if phase%2:d.line([(3,8),(6,7),(8,7)],fill=4)
    else:d.line([(2,7),(5,6),(7,6)],fill=4)
    d.line([(11,12),(13,11),(14,11)],fill=4)
    m=_side_masks(mask,corners);a=im.load();b=m.load()
    for y in range(16):
        for x in range(16):
            if b[x,y]:a[x,y]=2
    for y in range(16):
        for x in range(16):
            if b[x,y] and any(0<=x+dx<16 and 0<=y+dy<16 and not b[x+dx,y+dy] for dx,dy in ((0,1),(0,-1),(1,0),(-1,0))):a[x,y]=6
    if lily:
        d.polygon([(5,10),(7,8),(11,8),(13,10),(11,12),(7,12)],fill=10)
        d.line([(7,9),(10,9)],fill=11)
    return im


def _ledge(name,variant):
    im,d=_new(fill=4)
    d.polygon([(0,0),(15,0),(15,12),(12,14),(7,13),(4,15),(0,13)],fill=12)
    d.polygon([(0,0),(15,0),(15,4),(12,3),(8,5),(4,3),(0,4)],fill=5)
    d.line([(0,4),(4,3),(8,5),(12,3),(15,4)],fill=13)
    for x,top in ((3,5),(10,6)):
        d.line([(x,top),(x-1,10),(x,14)],fill=2)
    if name=='ledge_n':return im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return im


def _bridge(vertical=False,variant=1):
    im,d=_new(fill=9)
    # Bridge ends are flat and open; no closed rail across the travel axis.
    if not vertical:
        d.rectangle((0,0,15,2),fill=2);d.rectangle((0,13,15,15),fill=2)
        for x in (2,7,12):
            d.line((x,3,x,12),fill=8);d.line((x+1,3,x+1,12),fill=10)
        d.line((0,3,15,3),fill=11)
    else:
        d.rectangle((0,0,2,15),fill=2);d.rectangle((13,0,15,15),fill=2)
        for y in (2,7,12):
            d.line((3,y,12,y),fill=8);d.line((3,y+1,12,y+1),fill=10)
        d.line((3,0,3,15),fill=11)
    return im


def _pit(inner=False):
    im,d=_new(fill=1)
    if not inner:
        d.line((0,0,15,0),fill=4);d.line((1,1,14,1),fill=2)
        d.line((2,2,7,2),fill=3);d.line((10,2,13,2),fill=3)
    return im


def _myst(style,rest,variant=1,phase=0):
    if rest.startswith('floor') or rest.startswith('edge_') or rest=='glow':
        if style=='cave':
            im,d=_new(fill=4)
            if rest=='floor1':d.line((4,11,7,10),fill=3)
            if rest.startswith('edge_'):
                mask=int(rest[5:],16)
                m=_side_masks(mask);im.paste(3,(0,0,16,16),m.point(lambda v:255 if v else 0,'1'))
            return im,'stone'
        im=_floor(variant,earth=style=='hollow')
        if rest.startswith('edge_'):
            m=_side_masks(int(rest[5:],16))
            im.paste(8 if style=='hollow' else 3,(0,0,16,16),m.point(lambda v:255 if v else 0,'1'))
        return im,'ground'
    if rest in ('wall','face','crown'):
        if style=='thicket':return _canopy(0,'s' if rest=='face' else 'n' if rest=='crown' else None,variant=variant),'foliage'
        if style=='hollow':
            im,d=_new(fill=8)
            if variant==1:
                # Broad oak root-buttresses with a single knot.
                d.polygon([(1,0),(6,0),(6,5),(4,10),(6,15),(1,15),(0,9),(2,5)],fill=9)
                d.line([(2,1),(3,5),(2,10)],fill=10)
                d.polygon([(9,0),(13,0),(14,6),(12,11),(15,15),(10,15),(9,9),(10,4)],fill=9)
                d.line([(10,1),(11,5),(10,7)],fill=10)
                d.ellipse((7,6,10,10),fill=8);d.line([(7,8),(8,6),(10,7)],fill=11)
            elif variant==2:
                # Close willow roots with long pale, vertically broken planes.
                for x,y in ((1,0),(7,2),(13,0)):
                    d.polygon([(x,0),(x+2,0),(x+1,6),(x+3,15),(x,15),(x-1,8)],fill=9)
                    d.line([(x+1,1),(x,6),(x+1,10)],fill=11)
                d.line([(3,11),(5,10),(6,11)],fill=15)
            elif variant==3:
                # Smooth broad beech bark and a curved root scar.
                d.polygon([(0,0),(9,0),(8,6),(10,15),(0,15)],fill=9)
                d.polygon([(1,0),(5,0),(4,7),(5,13),(2,15),(1,8)],fill=10)
                d.line([(9,3),(7,5),(8,9),(11,11)],fill=8)
                d.line([(10,1),(12,6),(11,15)],fill=9,width=2)
            elif variant==4:
                # Cedar strips sag and overlap rather than becoming wire bars.
                for pts in ([(0,0),(4,0),(3,6),(5,11),(4,15),(1,15),(1,7)],
                            [(6,0),(10,0),(9,8),(11,15),(7,15),(8,7)],
                            [(12,0),(15,0),(15,15),(13,15),(12,8)]):
                    d.polygon(pts,fill=9)
                d.line([(2,1),(2,5),(3,7)],fill=10)
                d.line([(8,8),(9,11),(8,14)],fill=10)
            else:
                # Orchard roots entwine around a small recessed parasite shelf.
                d.line([(1,0),(4,5),(3,11),(6,15)],fill=9,width=4)
                d.line([(13,0),(10,6),(12,12),(11,15)],fill=9,width=4)
                d.line([(2,1),(5,6),(4,11)],fill=10)
                d.line([(4,8),(8,6),(11,8)],fill=15)
            if rest!='wall':d.rectangle((0,13,15,15),fill=1)
            return im,'foliage'
        im,d=_new(fill=3)
        if variant==1:
            # Wet rounded woodland stone, with large left-facing planes.
            d.polygon([(0,1),(5,0),(8,3),(7,7),(4,9),(0,8)],fill=4)
            d.polygon([(9,1),(15,0),(15,8),(11,9),(8,5)],fill=4)
            d.line([(1,2),(5,1),(7,3)],fill=6)
            d.polygon([(0,10),(5,9),(9,12),(7,15),(0,15)],fill=4)
            d.line([(1,11),(4,10),(6,11)],fill=5)
        elif variant==2:
            # Thin slate shelves; lichen lies on one attached ledge.
            for y,off in ((0,1),(5,3),(11,0)):
                d.polygon([(0,y+1),(6,y),(11,y+1),(15,y),(15,y+3),(8,y+4),(0,y+3)],fill=4)
                d.line([(1,y+1),(6,y),(10,y+1)],fill=5)
            d.line([(8,6),(11,5),(13,6)],fill=7)
        elif variant==3:
            d.polygon([(0,1),(8,0),(11,4),(8,9),(0,8)],fill=5)
            d.polygon([(0,2),(7,1),(9,4),(6,5),(0,5)],fill=6)
            d.polygon([(11,1),(15,0),(15,11),(12,10),(10,6)],fill=4)
            d.polygon([(1,10),(7,10),(10,14),(8,15),(0,15)],fill=4)
        elif variant==4:
            # Squat dark mass, weight supported by one broad upper facet.
            d.polygon([(0,2),(4,0),(11,1),(15,5),(13,10),(5,11),(0,7)],fill=4)
            d.polygon([(1,2),(5,1),(10,2),(12,4),(4,5)],fill=5)
            d.polygon([(0,12),(6,10),(12,12),(15,11),(15,15),(0,15)],fill=4)
            d.line([(1,13),(5,11),(8,12)],fill=5)
        else:
            d.polygon([(0,0),(6,1),(8,6),(5,11),(0,10)],fill=4)
            d.polygon([(10,0),(15,0),(15,11),(11,10),(8,5)],fill=4)
            d.line([(1,1),(5,2),(6,5)],fill=6)
            d.line([(2,12),(7,10),(11,12),(15,11)],fill=3,width=3)
            d.line([(8,11),(11,10),(13,11)],fill=8)
        if rest!='wall':d.rectangle((0,13,15,15),fill=2)
        return im,'stone'
    if rest=='exit':
        im,d=_new(fill=1);d.line((2,0,2,15),fill=4);d.line((13,0,13,15),fill=3)
        d.line((3,14,12,14),fill=5)
        return im,'stone' if style=='cave' else 'foliage'
    raise KeyError((style,rest))


def _group(kind,variant):
    w,h=(48,48) if kind=='meadow' else (32,16) if kind=='hlog' else (32,32)
    im,d=_new(w,h,fill=4)
    if kind in ('meadow','clover','shroomring'):
        # A small coherent landmark; only a few restrained flowers/fronds.
        if kind=='meadow':
            for x,y in ((8,12),(30,9),(22,30)):
                _frond(d,x,y,5,5,3)
                d.point((x+2,y-2),fill=15)
        elif kind=='clover':
            d.polygon([(8,16),(12,10),(18,11),(21,17),(17,22),(11,21)],fill=3)
            d.line([(11,14),(14,12),(17,13)],fill=5)
        else:
            for x,y in ((9,8),(22,10),(23,23),(8,24)):
                d.line((x,y,x,y+3),fill=3);d.line((x-2,y,x+2,y),fill=15);d.point((x,y-1),fill=11)
        return im,'ground'
    if kind=='raft':
        im,d=_new(32,32,fill=3)
        d.polygon([(5,17),(10,8),(20,6),(28,15),(25,25),(13,28)],fill=2)
        d.polygon([(6,15),(11,7),(20,5),(27,13),(23,23),(13,25)],fill=10)
        d.line([(10,10),(14,8),(21,8)],fill=11)
        return im,'water'
    # Large scenery is native assembled material with a single footprint.
    if kind in ('gboulder','treerock'):
        d.polygon([(3,19),(5,9),(13,4),(22,5),(28,14),(26,25),(18,28),(7,26)],fill=1)
        d.polygon([(5,17),(7,10),(14,6),(21,7),(26,14),(22,19),(12,21)],fill=5)
        d.polygon([(7,10),(14,6),(21,7),(22,10),(13,13)],fill=7)
        d.polygon([(12,21),(22,19),(26,14),(25,24),(18,26),(8,24)],fill=3)
        if kind=='treerock':d.line([(15,16),(12,23),(5,29)],fill=9,width=3)
        # Stone planes share a ground bank so transparent-looking corners are
        # actual exact grass, not a rectangular gray base around the boulder.
        lut=list(range(256))
        for old,new in ((1,1),(3,12),(4,4),(5,13),(7,14),(9,8)):lut[old]=new
        return im.point(lut),'ground'
    if kind=='hlog':
        d.polygon([(1,8),(5,3),(26,4),(31,9),(28,14),(5,15)],fill=8)
        d.polygon([(3,7),(6,4),(25,5),(28,8),(24,10),(6,10)],fill=10)
        d.ellipse((23,5,30,13),fill=1);d.line((7,12,21,12),fill=9)
        return im,'foliage'
    raise KeyError(kind)


@lru_cache(None)
def _paint(name,phase,variant):
    if not supports(name):raise KeyError(name)
    if name=='black':return _new(fill=1)[0],'ground'
    if name.startswith(('pedge_','verge_','shore_')):
        family,code=name.split('_',1);corner=code.startswith('c') and len(code)>1
        mask=int(code[1:] if corner else code,16)
        return _transition(0 if corner else mask,mask if corner else 0,variant,'path' if family=='pedge' else family),'ground'
    if name.startswith('rot_'):
        return _rot_edge(int(name[4],16),int(name[5],16),variant),'decay_mix'
    if name.startswith('water_c') and len(name)>7:return _water(corners=int(name[7:],16),phase=phase,variant=variant),'water'
    if name=='water' or name.startswith('water_'):
        if name=='water_lily':return _water(phase=phase,variant=variant,lily=True),'water'
        if name=='water_foam':
            im=_water(phase=phase,variant=variant);d=ImageDraw.Draw(im);d.line([(0,7),(4,6),(8,8),(12,6),(15,7)],fill=7)
            return im,'water'
        return _water(0 if name=='water' else int(name[6:],16),phase=phase,variant=variant),'water'
    if name=='waterfall':
        im,d=_new(fill=3)
        for x in (2,7,12):
            d.line((x,0,x,15),fill=4)
            for start in (-7,2,11):
                y=(start+phase*3)%18-3
                d.line((x,y,x,y+4),fill=6)
                d.line((x+1,y+1,x+1,y+3),fill=5)
        d.line([(0,14),(3,13),(5,15)],fill=7)
        d.line([(9,15),(11,13),(14,14)],fill=8)
        return im,'water'
    if name in ('moss0','moss1','moss2','moss_shade','path','path_edge_n'):
        if name.startswith('path'):return _transition(1 if name.endswith('_n') else 0,variant=variant),'ground'
        return _floor(variant,int(name[-1]) if name[-1].isdigit() else 0),'ground'
    if name in ('moss_flowers','moss_flowers2','fern_patch','tall_grass','leaf_litter'):
        return _decor(name,variant),'ground'
    if name.startswith('forest_rot') or name.startswith('blight_ground') or name in ('moss_blight','moss_blight2','blight_floor','blight_floor2','blight_vein') or name.startswith('forest_blight_vein'):
        n=int(name[-1]) if name[-1].isdigit() else 0
        # These are all still living or damp grassy ground at every depth.
        return _rot_floor(variant,n,root='vein' in name),'ground'
    if name.startswith('canopy') or name.startswith('forest_canopy'):
        n=int(name[-1]) if name.startswith('forest_canopy') else 1 if name.endswith('2') else 0
        sick='blight' in name;face='s' if name=='canopy_s' else 'n' if name=='canopy_n' else None
        im=_canopy(n,face,sick,variant,name=='canopy_lantern',phase)
        if name=='canopy_blight2':
            d=ImageDraw.Draw(im);d.line([(10,9),(12,8),(14,9)],fill=13)
            if phase%2:d.point((12,8),fill=14)
        return im,'blight' if sick else 'foliage'
    tree_names=['tree_top_nw','tree_top_ne','tree_mid_w','tree_mid_e','tree_trunk_w','tree_trunk_e']
    if name in tree_names:
        n=tree_names.index(name);im=_tree(variant)
        return im.crop(((n%2)*16,(n//2)*16,(n%2+1)*16,(n//2+1)*16)),'foliage'
    for pre in ('tree2_','birch_','fir_','sicktree_'):
        if name.startswith(pre):
            n=int(name[len(pre):]);sick=pre=='sicktree_';im=_tree(variant,second=pre in ('tree2_','fir_'),sick=sick)
            return im.crop(((n%2)*16,(n//2)*16,(n%2+1)*16,(n//2+1)*16)),'blight' if sick else 'foliage'
    for pre in ('gtree_','gtree2_'):
        if name.startswith(pre):
            n=int(name[len(pre):]);im=_tree(variant,large=True,second=pre=='gtree2_')
            return im.crop(((n%3)*16,(n//3)*16,(n%3+1)*16,(n//3+1)*16)),'foliage'
    if name.startswith('btree_'):
        n=int(name[6:]);im=_tree(variant,dead=True)
        if n<6:return im.crop(((n%2)*16,(n//2)*16,(n%2+1)*16,(n//2+1)*16)),'blight'
        # Legacy unplaced extension tiles preserve their declared floor footprint.
        return _floor(variant),'ground'
    if name.startswith('forest_blight_tree'):
        n=int(name[-1]);im=_canopy(n,sick=True,variant=variant);part=_tree(variant,dead=True).crop(((n%2)*16,(n//2)*16,(n%2+1)*16,(n//2+1)*16))
        _paste(im,part,(0,0));return im,'blight'
    for pre,w,kind in (('meadow_',3,'meadow'),('clover_',2,'clover'),('shroomring_',2,'shroomring'),('gboulder_',2,'gboulder'),('treerock_',2,'treerock'),('hlog_',2,'hlog'),('raft_',2,'raft')):
        if name.startswith(pre):
            n=int(name[len(pre):]);im,bank=_group(kind,variant)
            im=im.crop(((n%w)*16,(n//w)*16,(n%w+1)*16,(n//w+1)*16))
            if kind=='raft':
                d=ImageDraw.Draw(im)
                for sx,y in ((1,1),(12,1),(1,14),(12,14)):
                    if all(im.getpixel((x,y)) in (2,3,4) for x in range(sx,sx+3)):
                        for x in range(sx,sx+3):d.point((x,y),fill=4 if (x+phase)%3 else 5)
                        break
            return im,bank
    if name in ('ledge_s','ledge_s_w','ledge_s_e','ledge_n'):return _ledge(name,variant),'ground'
    if name in ('bridge','bridge_v'):return _bridge(name.endswith('_v'),variant),'foliage'
    if name in ('pit','pit_inner','forest_blight_pit'):return _pit(name=='pit_inner'),'stone'
    if name in ('blight_wall','blight_wall2','blight_wall_lit'):
        im=_canopy(0,face='s',sick=True,variant=variant)
        d=ImageDraw.Draw(im);d.line([(2,14),(4,9),(2,3)],fill=8,width=2)
        if name=='blight_wall_lit':
            d.line([(4,8),(7,7),(9,8)],fill=13)
            if phase%2:d.point((7,7),fill=14)
        return im,'blight'
    if name=='blight_pool':return _water(phase=phase,variant=variant,rot=True),'rot_water'
    if name=='blight_mist':
        # Sparse low root/mould wisps remain subordinate to protected glitter.
        im,d=_new();d.line([(1,12),(4,11),(6,12)],fill=5 if phase%2 else 6)
        return im,'blight'
    for style in ('cave','hollow','thicket'):
        if name.startswith(style+'_'):return _myst(style,name[len(style)+1:],variant,phase)
    raise KeyError('Unpainted native forest terrain: '+name)


def paint(name,phase=0,variant=1):
    """Return a fresh native P16×16 canvas and its retained BG-bank name."""
    variant=int(variant)
    if variant not in RECIPES:raise ValueError(variant)
    im,bank=_paint(name,int(phase),variant)
    assert im.mode=='P' and im.size==(16,16),(name,im.mode,im.size)
    assert set(im.getdata())<=set(range(16)),name
    return im.copy(),bank
