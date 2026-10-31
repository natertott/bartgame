"""Native forest studies v2: black deadwood, violet wounds and sick ecology.

Opt-in only. Healthy constructions retain the user's favored v1 anchors;
new pixels describe disease, height and adjacency. No global palette or old
painter is mutated. Images are authored on native canvases, never reduced.
"""
from functools import lru_cache
from PIL import Image, ImageDraw
import forest_concepts_terrain as H
import reboot_core as R

RECIPES={1:'Black Sap Oak',2:'Violet Strangler',3:'Witchfire Weep',4:'Amethyst Canker',5:'Royal Bruise'}
BANKS=H.BANKS
PULSE_INDICES={'blight':(5,6,7,13,14)}
CANOPY_ANCHOR={1:1,2:3,3:1,4:3,5:1}
TREE_ANCHOR={1:1,2:5,3:5,4:1,5:5}
HOLLOW_ANCHOR={1:1,2:3,3:1,4:3,5:3}
CAVE_ANCHOR={1:1,2:4,3:1,4:4,5:1}
# BG-only roles: 1deep outline,2–4sickgrass,5violethalo,6purplebody,
# 7pink-whitecore,8BLACKwood,9charcoal,10plane,11rim,12littlelivinggreen,
# 13fuchsia,14hotpink,15fungalivory. RGB555 is explicit at this boundary.
_DISEASE={1:('#182820','#283828','#485038'),2:('#202820','#383828','#505038'),
          3:('#182828','#303c30','#485448'),4:('#202428','#343830','#4c5038'),
          5:('#202820','#383c28','#505438')}
_NEON={1:('#381060','#9828e8','#e8b0f8','#d840f0','#f8d8f8'),
       2:('#401060','#a828e8','#f0b8f8','#e050f0','#f8e0f8'),
       3:('#281068','#7828e8','#d8b0f8','#b850f8','#f0d8f8'),
       4:('#381068','#9020d8','#e0a8f8','#d048f0','#f8d0f8'),
       5:('#400c60','#a020d8','#e8a8f0','#e040e8','#f8d8f8')}
PALETTES={}
for _v in RECIPES:
    b={name:H.palette(name,CANOPY_ANCHOR[_v]) for name in BANKS}
    g=list(map(H._q,_DISEASE[_v]));n=list(map(H._q,_NEON[_v]))
    b['blight']=['#000000','#08080c',*g,n[0],n[1],n[2],'#080810','#282830','#403848','#585060','#304830',n[3],n[4],'#d8c0c0']
    b['decay_mix']=['#000000','#101410',*g,'#403824','#605034','#887044','#181820','#303028','#484038','#685048','#405040',n[0],n[1],'#c0b898']
    b['rot_water']=['#000000','#101014','#181c20','#282c30','#384034','#505040','#707058','#989078','#b8b098',g[0],g[1],g[2],'#403824','#605034','#887044','#d0c8a8']
    PALETTES[_v]={k:list(map(H._q,p)) for k,p in b.items()}
    assert all(len(p)==16 for p in PALETTES[_v].values())


def palette(name,variant=1):
    return list(PALETTES[int(variant)][name]) if name in BANKS else list(R.PALETTES[name])


def supports(name):
    return (H.supports(name) and name not in ('hlog_0','hlog_1')) or name in ('dead_tree','forest_blight_dead_tree')


def _new(w=16,h=16,fill=0):
    im=Image.new('P',(w,h),fill)
    return im,ImageDraw.Draw(im)


def _pulse(d,points,phase=0,width=3):
    """A native 2–3 ink halo/core, with a traveling bright wound segment."""
    d.line(points,fill=5,width=width+2)
    d.line(points,fill=13 if phase%4 in (1,2) else 6,width=width)
    if len(points)>1:
        k=phase%max(1,len(points)-1)
        a,b=points[k],points[k+1]
        # Pink light is concentrated, never an outline around every branch.
        scale=max(abs(b[0]-a[0]),abs(b[1]-a[1]),1)
        step=min(1,scale)
        mid=(round(a[0]+(b[0]-a[0])*step/scale),round(a[1]+(b[1]-a[1])*step/scale))
        d.line([a,mid],fill=7,width=1)
        if phase%2:d.point(mid,fill=14)


def _sick_floor(v=1,n=0,root=False,phase=0):
    im,d=_new(fill=4)
    # Bald/cankered tufts have a few connected soil pixels, never sparkle noise.
    if n%4==1:
        d.polygon([(3,10),(5,9),(8,10),(7,12),(4,12)],fill=3)
        d.line([(4,10),(6,10)],fill=5)
    elif n%4==2:
        d.line([(10,6),(11,4),(12,6)],fill=3);d.point((11,6),fill=5)
    elif n%4==3:
        d.line([(5,12),(7,11),(9,12)],fill=5)
    if root:
        # Visible dirt/root trail remains far quieter than neon on wood.
        d.line([(1,13),(4,11),(6,12)],fill=8)
        d.line([(1,14),(3,12)],fill=9)
    return im


def _sick_transition(sides,corners,v=1):
    im=_sick_floor(v);px=im.load();mask=H._side_masks(sides,corners).load()
    # Edge green has the exact current healthy grass colour. Interior remains
    # desaturated sick green, avoiding a square all-purple carpet.
    old=palette('ground',v)[4];new=palette('decay_mix',v)
    edge=min(range(2,13),key=lambda i:sum((H.rgb(old)[j]-H.rgb(new[i])[j])**2 for j in range(3))) if hasattr(H,'rgb') else 12
    for y in range(16):
        for x in range(16):
            if mask[x,y]:px[x,y]=edge
    return im


def _tall_grass(v=1,sick=False):
    im,d=_new(fill=4)
    # Broad leaf blades are connected to one low shadow/soil mat.
    d.polygon([(1,13),(3,8),(6,10),(9,7),(13,10),(15,14),(12,15),(5,15)],fill=3)
    if v==1:
        blades=[[(3,13),(1,7),(3,2),(5,8),(6,13)],[(6,13),(6,5),(9,0),(9,8),(8,14)],[(10,14),(11,5),(14,3),(13,11),(12,14)]]
    elif v==2:
        blades=[[(2,13),(1,6),(4,3),(4,10),(6,14)],[(6,14),(7,4),(10,2),(9,11),(8,14)],[(10,14),(12,6),(15,4),(13,13)]]
    elif v==3:
        blades=[[(2,13),(2,5),(6,2),(5,10),(7,14)],[(7,14),(8,6),(12,3),(11,11),(10,14)],[(11,14),(13,8),(15,8),(14,13)]]
    elif v==4:
        blades=[[(2,13),(1,7),(4,5),(7,9),(6,14)],[(6,13),(5,3),(8,1),(9,8),(8,14)],[(10,14),(11,5),(14,6),(15,11),(13,14)]]
    else:
        blades=[[(2,13),(3,5),(7,1),(6,9),(7,14)],[(7,14),(8,7),(12,4),(11,11),(10,14)],[(11,13),(13,8),(15,9),(14,14)]]
    for i,pts in enumerate(blades):
        d.polygon(pts,fill=3)
        d.line(pts[:3],fill=5 if not sick else 2)
        if not sick:d.line([pts[0],(pts[0][0]+1,pts[0][1]-3)],fill=4)
    return im


@lru_cache(None)
def _sick_tree(v=1,large=False,dead=False,phase=0):
    w,h=(48,64) if large else (32,48);mid=w//2
    im,d=_new(w,h)
    # True foreground alpha reveals the engine's actual stored floor.
    d=ImageDraw.Draw(im)
    # Heavy twisted collar is one black mass with narrow charcoal light planes.
    trunk=[(mid-4,h-37),(mid+4,h-36),(mid+6,h-27),(mid+3,h-19),(mid+5,h-12),
           (mid+11,h-6),(mid+15,h-4),(mid+13,h-2),(mid+5,h-4),(mid,h-8),
           (mid-7,h-3),(mid-15,h-2),(mid-13,h-5),(mid-7,h-9),(mid-5,h-18),(mid-7,h-29)]
    d.polygon(trunk,fill=8)
    d.polygon([(mid-3,h-36),(mid+1,h-35),(mid+2,h-26),(mid-1,h-19),(mid+1,h-11),
               (mid-5,h-6),(mid-10,h-4),(mid-6,h-9),(mid-3,h-18),(mid-5,h-28)],fill=9)
    d.line([(mid-3,h-34),(mid-2,h-27),(mid-4,h-20)],fill=10)
    if v==1:
        limbs=[[(mid,h-25),(mid-9,h-34),(mid-12,h-44),(mid-16,h-46)],
               [(mid-8,h-34),(mid-15,h-34),(mid-17,h-39)],
               [(mid,h-27),(mid+8,h-33),(mid+12,h-43),(mid+16,h-47)],
               [(mid+7,h-33),(mid+15,h-34),(mid+17,h-40)],[(mid,h-28),(mid-1,h-42),(mid+3,h-48)]]
    elif v==2:
        limbs=[[(mid,h-24),(mid-9,h-33),(mid-13,h-40),(mid-8,h-46)],
               [(mid-9,h-33),(mid-16,h-32),(mid-17,h-40)],
               [(mid,h-27),(mid+9,h-32),(mid+15,h-41),(mid+10,h-46)],
               [(mid+8,h-33),(mid+17,h-32),(mid+18,h-39)]]
    elif v==3:
        limbs=[[(mid,h-23),(mid-8,h-31),(mid-15,h-35),(mid-16,h-43)],
               [(mid,h-29),(mid+7,h-39),(mid+14,h-43),(mid+16,h-39)],
               [(mid+6,h-38),(mid+17,h-33),(mid+16,h-26)],[(mid-8,h-31),(mid-13,h-24)]]
    elif v==4:
        limbs=[[(mid,h-24),(mid-8,h-34),(mid-14,h-39)],[(mid,h-26),(mid+9,h-34),(mid+14,h-39)],
               [(mid,h-28),(mid+1,h-44),(mid-4,h-47)],[(mid-7,h-33),(mid-15,h-30)]]
    else:
        limbs=[[(mid,h-25),(mid-8,h-33),(mid-12,h-44),(mid-15,h-47)],
               [(mid,h-29),(mid+7,h-35),(mid+12,h-44),(mid+15,h-46)],
               [(mid-7,h-33),(mid-16,h-31),(mid-18,h-38)],
               [(mid+7,h-35),(mid+17,h-31),(mid+19,h-38)],[(mid,h-31),(mid-2,h-43),(mid+2,h-48)]]
    for i,pts in enumerate(limbs):
        d.line(pts,fill=8,width=6 if i<2 else 4)
        d.line([(x-1,y) for x,y in pts],fill=9,width=2)
        d.line([(x-2,y) for x,y in pts[:2]],fill=10)
    if v==1:
        _pulse(d,[(mid-9,h-4),(mid-3,h-12),(mid-2,h-23),(mid-9,h-34),(mid-11,h-42)],phase,2)
        _pulse(d,[(mid-2,h-23),(mid+5,h-30),(mid+10,h-39)],phase+1,1)
        d.line([(mid+3,h-17),(mid+7,h-19),(mid+11,h-17)],fill=5,width=4)
        d.line([(mid+4,h-18),(mid+7,h-19),(mid+10,h-18)],fill=13)
    elif v==2:
        # Violet constrictors turn around the collar, not a uniform wire mesh.
        for i,pts in enumerate(([(mid-7,h-15),(mid+5,h-18),(mid+8,h-23)],
                                 [(mid+6,h-24),(mid-5,h-27),(mid-9,h-33)],
                                 [(mid-9,h-34),(mid-4,h-38),(mid+5,h-36),(mid+9,h-33)])):
            _pulse(d,pts,phase+i,2)
        d.ellipse((mid-10,h-35,mid-3,h-29),fill=8);_pulse(d,[(mid-9,h-32),(mid-6,h-34),(mid-4,h-31)],phase,1)
    elif v==3:
        _pulse(d,[(mid-10,h-3),(mid-3,h-14),(mid-2,h-28),(mid+6,h-38),(mid+13,h-41)],phase,2)
        for i,(x,y,ln) in enumerate(((mid-13,h-35,12),(mid+13,h-39,16),(mid+6,h-35,11))):
            d.line([(x,y),(x-1,y+ln)],fill=8,width=4)
            _pulse(d,[(x,y+2),(x-1,y+ln-2)],phase+i,1)
    elif v==4:
        # Coal-black bark plates surround wet cankers with purple living rims.
        for i,(x,y) in enumerate(((mid-7,h-32),(mid+5,h-28),(mid-3,h-16))):
            d.polygon([(x-5,y),(x-3,y-5),(x+3,y-6),(x+6,y-1),(x+3,y+5),(x-2,y+5)],fill=8)
            d.line([(x-4,y),(x-2,y-4),(x+2,y-5)],fill=10)
            _pulse(d,[(x-2,y+3),(x-3,y-1),(x,y-3),(x+3,y-1),(x+1,y+2)],phase+i,2)
        _pulse(d,[(mid-5,h-6),(mid-1,h-12)],phase,2)
    else:
        _pulse(d,[(mid-10,h-4),(mid-3,h-13),(mid,h-26),(mid-6,h-34),(mid-10,h-42)],phase,1)
        _pulse(d,[(mid,h-26),(mid+7,h-34),(mid+12,h-41)],phase+2,1)
        for i,(x,y) in enumerate(((mid-13,h-38),(mid+14,h-35),(mid+1,h-44))):
            d.ellipse((x-2,y-1,x+2,y+5),fill=5)
            d.ellipse((x-1,y,x+1,y+3),fill=13 if (phase+i)%2 else 6)
            d.line((x,y+1,x,y+2),fill=7)
    if not dead:
        # Tiny remnant green contrasts against black wood, never a green canopy.
        for x,y in ((mid-13,h-40),(mid+12,h-32)):
            d.polygon([(x-2,y),(x,y-3),(x+2,y-1),(x+1,y+2)],fill=12)
    return im


@lru_cache(None)
def _black_canopy32(v=1,phase=0):
    im,d=_new(32,32,fill=8)
    # A connected 32px wood mass. The engine selects coherent macroquadrants,
    # avoiding both a diagonal wire lattice and one glowing icon per cell.
    d.polygon([(0,0),(12,0),(18,8),(17,17),(22,25),(21,31),(8,31),
               (7,25),(10,19),(7,11),(0,8)],fill=9)
    d.polygon([(23,0),(31,0),(31,13),(27,17),(31,23),(31,31),
               (24,31),(19,23),(22,15),(24,9)],fill=9)
    d.line([(1,1),(9,2),(12,7),(12,13)],fill=10,width=2)
    d.line([(24,2),(26,8),(25,12)],fill=11)
    d.line([(11,23),(12,27),(11,31)],fill=10,width=2)
    d.line([(0,19),(7,16),(11,13)],fill=9,width=4)
    d.line([(18,10),(25,9),(31,5)],fill=9,width=4)
    if v==1:
        _pulse(d,[(10,29),(9,24),(11,20),(8,15),(10,10),(9,5)],phase,2)
        _pulse(d,[(22,8),(24,12),(23,17)],phase+1,1)
        d.line([(23,25),(26,23),(30,24)],fill=5,width=3)
        d.line([(24,24),(27,23),(29,24)],fill=13)
    elif v==2:
        d.polygon([(8,4),(17,5),(21,12),(18,20),(21,27),(14,31),
                   (7,26),(9,18),(5,11)],fill=8)
        d.line([(9,5),(14,7),(15,12)],fill=10,width=2)
        _pulse(d,[(6,9),(11,6),(18,9),(21,14)],phase,2)
        _pulse(d,[(22,17),(19,22),(11,23),(7,20)],phase+1,2)
        _pulse(d,[(8,27),(14,29),(19,26)],phase+2,1)
    elif v==3:
        d.polygon([(2,3),(10,2),(12,10),(8,16),(9,27),(5,31),(1,25)],fill=8)
        d.line([(4,4),(7,8),(6,14)],fill=10,width=2)
        d.polygon([(2,1),(10,3),(12,10),(8,19),(9,29),(4,31),(1,25)],fill=9)
        d.line([(4,3),(7,9),(5,15)],fill=10,width=2)
        _pulse(d,[(6,6),(8,12),(6,18),(7,24)],phase,1)
        d.polygon([(21,2),(28,4),(29,11),(25,18),(27,29),(22,31),(20,21)],fill=9)
        d.line([(23,3),(25,9),(23,15)],fill=10,width=2)
        _pulse(d,[(25,7),(24,12),(26,18),(24,26)],phase+2,1)
        d.polygon([(12,18),(17,18),(18,26),(15,29),(12,25)],fill=8)
    elif v==4:
        for i,(x,y,rx,ry) in enumerate(((9,10,7,8),(24,22,6,8))):
            d.polygon([(x-rx,y-2),(x-rx+2,y-ry),(x+3,y-ry),
                       (x+rx,y-2),(x+rx-2,y+ry),(x-3,y+ry)],fill=8)
            d.line([(x-rx+1,y-1),(x-rx+3,y-ry+1),(x+2,y-ry+1)],fill=11)
            d.polygon([(x-4,y),(x-2,y-5),(x+2,y-4),(x+4,y),(x+2,y+5),(x-2,y+3)],fill=5)
            d.polygon([(x-2,y-3),(x+1,y-3),(x+3,y),(x,y+2),(x-2,y+1)],fill=6 if (phase+i)%2 else 13)
            d.line([(x-1,y-3),(x+1,y-2)],fill=7)
            _pulse(d,[(x-2,y+3),(x-3,y+6),(x-1,y+8)],phase+i,1)
        _pulse(d,[(7,29),(10,27),(11,24)],phase+2,1)
    else:
        d.line([(0,27),(10,18),(16,7),(14,0)],fill=8,width=7)
        d.line([(10,18),(23,17),(31,22)],fill=8,width=6)
        d.line([(20,9),(26,4),(26,0)],fill=8,width=5)
        _pulse(d,[(10,26),(12,20),(11,15)],phase,1)
        _pulse(d,[(16,18),(20,18),(23,20)],phase+1,1)
        for i,(x,y) in enumerate(((24,6),(19,26))):
            d.ellipse((x-3,y-2,x+3,y+5),fill=5)
            d.ellipse((x-2,y-1,x+2,y+3),fill=13 if (phase+i)%2 else 6)
            d.line((x-1,y,x-1,y+2),fill=7)
    d.polygon([(17,28),(19,25),(21,27),(19,29)],fill=12)
    return im


def _canopy(name,phase=0,v=1):
    n=int(name[-1]) if name.startswith(('forest_canopy','forest_blight_tree')) else 1 if name.endswith('2') else 0
    macro=_black_canopy32(v,phase)
    im=macro.crop(((n%2)*16,(n//2%2)*16,(n%2+1)*16,(n//2%2+1)*16))
    if name in ('blight_wall','blight_wall2','blight_wall_lit'):
        d=ImageDraw.Draw(im)
        d.polygon([(0,10),(4,8),(8,11),(12,9),(15,11),(15,15),(0,15)],fill=8)
        d.line([(2,15),(3,10),(6,9)],fill=10,width=2)
        if name=='blight_wall_lit':_pulse(d,[(7,15),(8,12),(12,11)],phase,2)
    return im


def _ledge(name,v=1):
    im,d=_new(fill=12)
    # A clearly raised grassy lip, short vertical exposed face and contact shade.
    d.polygon([(0,0),(15,0),(15,3),(12,4),(9,3),(6,5),(3,3),(0,4)],fill=4)
    d.line([(0,3),(3,2),(6,4),(9,2),(12,3),(15,2)],fill=5)
    d.polygon([(0,6),(5,5),(9,6),(15,5),(15,11),(12,12),(8,11),(3,12),(0,10)],fill=12)
    d.line([(0,5),(4,4),(8,5),(12,4),(15,4)],fill=13)
    for pts in ([(3,6),(4,9),(3,12)],[(10,6),(9,10),(11,12)]):d.line(pts,fill=1)
    d.polygon([(0,12),(4,14),(8,13),(12,14),(15,12),(15,15),(0,15)],fill=1)
    d.line([(1,12),(4,13),(8,12),(12,13),(14,12)],fill=2)
    return im.transpose(Image.Transpose.FLIP_TOP_BOTTOM) if name=='ledge_n' else im


def _isolated_water(phase=0,v=1,rot=False):
    # Exterior is real foreground alpha: the engine supplies the actual
    # grassy, sick or dirt floor below this tiny pond, never a green square.
    im,d=_new()
    d.polygon([(4,1),(10,1),(14,4),(14,10),(11,14),(4,14),(1,11),(1,5)],fill=12)
    d.polygon([(4,2),(10,2),(13,5),(13,10),(10,13),(4,13),(2,10),(2,5)],fill=2)
    d.polygon([(5,3),(9,3),(12,5),(12,9),(9,12),(5,12),(3,9),(3,6)],fill=3)
    d.line([(5,5+phase%2),(7,4+phase%2),(9,5+phase%2)],fill=4)
    d.line([(5,13),(9,13),(12,11)],fill=13)
    return im


def _water_surface(mask=0,corners=0,phase=0,v=1,kind='water'):
    if mask==15:im=_isolated_water(phase,v)
    else:im=H._water(mask,corners,phase,CANOPY_ANCHOR[v])
    if kind=='water_lily':
        d=ImageDraw.Draw(im)
        if mask==15:
            d.polygon([(5,8),(7,6),(10,7),(10,9),(7,10)],fill=10)
            d.line((7,7,8,7),fill=11)
        else:
            d.polygon([(5,10),(7,8),(11,8),(13,10),(11,12),(7,12)],fill=10)
            d.line((7,9,10,9),fill=11)
    elif kind=='water_foam':
        d=ImageDraw.Draw(im)
        if mask==15:d.line([(4,10),(6,11),(8,10),(10,11)],fill=7)
        else:d.line([(0,7),(4,6),(8,8),(12,6),(15,7)],fill=7)
    return im


def _is_sick(name):
    return name.startswith(('blight_','forest_blight','forest_rot','btree_','sicktree_')) or name in ('moss_blight','moss_blight2','canopy_blight','canopy_blight2','dead_tree')


@lru_cache(None)
def _paint(name,phase,v):
    if not supports(name):raise KeyError(name)
    if name=='tall_grass' or name=='fern_patch':return _tall_grass(v),'ground'
    if name in ('dead_tree','forest_blight_dead_tree'):
        im,d=_new()
        d.polygon([(4,15),(6,11),(6,5),(3,1),(7,3),(8,7),(11,3),(14,1),(12,7),(9,10),(10,13),(14,15)],fill=8)
        d.line([(6,13),(7,9),(6,5)],fill=10,width=2)
        _pulse(d,[(4,15),(7,11),(7,6),(4,2)],phase,1)
        return im,'blight'
    if name.startswith('rot_'):
        return _sick_transition(int(name[4],16),int(name[5],16),v),'decay_mix'
    if name.startswith(('forest_rot','blight_ground','forest_blight_vein')) or name in ('moss_blight','moss_blight2','blight_floor','blight_floor2','blight_vein'):
        n=int(name[-1]) if name[-1].isdigit() else 0
        return _sick_floor(v,n,'vein' in name,phase),'decay_mix'
    if name in ('canopy_blight','canopy_blight2','blight_wall','blight_wall2','blight_wall_lit'):
        return _canopy(name,phase,v),'blight'
    if name.startswith('sicktree_'):
        n=int(name[9:]);im=_sick_tree(v,phase=phase)
        return im.crop(((n%2)*16,(n//2)*16,(n%2+1)*16,(n//2+1)*16)),'blight'
    if name.startswith('btree_'):
        n=int(name[6:])
        if n>=6:return _sick_floor(v),'decay_mix'
        im=_sick_tree(v,dead=True,phase=phase)
        return im.crop(((n%2)*16,(n//2)*16,(n%2+1)*16,(n//2+1)*16)),'blight'
    if name.startswith('forest_blight_tree'):
        n=int(name[-1]);im=_canopy(name,phase,v)
        part=_sick_tree(v,dead=True,phase=phase).crop(((n%2)*16,(n//2)*16,(n%2+1)*16,(n//2+1)*16))
        # These six IDs are full SOLID wallskin, unlike FLOOR tree crowns.
        # Dense wood backing makes the blocked footprint visually truthful.
        H._paste(im,part,(0,0));return im,'blight'
    if name in ('ledge_s','ledge_s_w','ledge_s_e','ledge_n'):return _ledge(name,v),'ground'
    if name=='water' or name.startswith('water_'):
        if name in ('water_lily','water_foam'):return _water_surface(phase=phase,v=v,kind=name),'water'
        if name.startswith('water_c') and len(name)>7:
            return _water_surface(corners=int(name[7:],16),phase=phase,v=v),'water'
        return _water_surface(0 if name=='water' else int(name[6:],16),phase=phase,v=v),'water'
    if name=='blight_pool':
        im,d=_new(fill=11)
        d.polygon([(0,5),(3,1),(11,0),(15,4),(15,12),(11,15),(3,14),(0,11)],fill=2)
        d.polygon([(2,6),(5,3),(11,2),(13,5),(12,11),(8,13),(3,11)],fill=3)
        d.line([(3,6+phase%2),(6,5+phase%2),(9,6+phase%2)],fill=4)
        return im,'rot_water'
    if name=='blight_mist':
        im,d=_new();d.polygon([(1,11),(5,9),(9,10),(13,8),(15,9),(10,12),(5,11)],fill=5)
        d.line([(4,10),(7,10),(9,11)],fill=6 if phase%2 else 5)
        return im,'blight'
    if name=='forest_blight_pit':return H._pit(),'stone'
    # Native favorite healthy constructions remain anchors; no old source is
    # modified and no body is resized. Architecture favorites are chosen perstyle.
    anchor=CANOPY_ANCHOR[v]
    if name.startswith(('tree','birch_','fir_','gtree')):anchor=TREE_ANCHOR[v]
    if name.startswith(('hollow_','thicket_')):anchor=HOLLOW_ANCHOR[v]
    if name.startswith('cave_'):anchor=CAVE_ANCHOR[v]
    im,bank=H.paint(name,phase,anchor)
    rootpart=name in ('tree_trunk_w','tree_trunk_e')
    for prefix,start in (('tree2_',4),('birch_',4),('fir_',4),('gtree_',9),('gtree2_',9)):
        if name.startswith(prefix):rootpart=int(name[len(prefix):])>=start
    if rootpart:
        # The retained healthy native root drawing sits on flat ink4 turf.
        # Remove that substrate only; bark/leaf pixels retain favorite shapes.
        im=im.copy();p=im.load()
        for y in range(16):
            for x in range(16):
                if p[x,y]==4:p[x,y]=0
    return im,bank


def paint(name,phase=0,variant=1):
    variant=int(variant)
    if variant not in RECIPES:raise ValueError(variant)
    im,bank=_paint(name,int(phase),variant)
    assert im.mode=='P' and im.size==(16,16) and set(im.getdata())<=set(range(16)),name
    return im.copy(),bank


def paint_adjacency(parent,mask,corners=0,phase=0,variant=1,quadrant=None):
    """Exposed N1,E2,S4,W8; concave NW1,NE2,SE4,SW8 gap flags.

    Every 8px quarter depends only on its two touching sides and its corner.
    Logical room IDs/collision stay unchanged; engine owns the render aliases.
    """
    variant=int(variant);mask=int(mask)&15;corners=int(corners)&15
    if '@q' in parent:
        parent,q=parent.rsplit('@q',1);quadrant=int(q)
    if parent.startswith('water'):
        return _water_surface(mask,corners,phase,variant,parent),'water'
    sick=_is_sick(parent)
    im,bank=paint(parent,phase,variant)
    if not (parent.startswith(('canopy','forest_canopy')) or parent.startswith('blight_wall')):return im,bank
    if quadrant is not None:
        q=int(quadrant)%4
        if sick:
            macro=_black_canopy32(variant,phase)
            im=macro.crop(((q%2)*16,(q//2)*16,(q%2+1)*16,(q//2+1)*16))
        else:
            face='s' if parent=='canopy_s' else 'n' if parent=='canopy_n' else None
            im=H._canopy(q,face,False,CANOPY_ANCHOR[variant],parent=='canopy_lantern',phase)
    out=im.copy();p=out.load()
    # Quarter-local rounded outside corners and small true concave cuts.
    for y in range(16):
        for x in range(16):
            west=x<8;north=y<8
            sx=x if west else 15-x;sy=y if north else 15-y
            hbit=8 if west else 2;vbit=1 if north else 4
            cornerbit=1 if west and north else 2 if north else 8 if west else 4
            eh=bool(mask&hbit);ev=bool(mask&vbit)
            outside=(eh and sx<2) or (ev and sy<2)
            if eh and ev and sx<6 and sy<6:outside=(sx-5)**2+(sy-5)**2>24
            if not eh and not ev and corners&cornerbit and sx+sy<4:outside=True
            if outside:p[x,y]=0
    # A near-side contact shadow remains on the ground, separate from a pit.
    if mask&4:
        for x in range(2,14):
            if p[x,13]==0 and p[x,12]!=0:p[x,13]=1
    assert out.size==(16,16) and max(out.getdata())<=15
    return out,bank


def pulse_palettes(variant=1):
    """Authored BG-only light breathing; every material ink stays invariant.

    Engine uses these four bank states for real static-tree glow. Native
    phase artwork on already animated IDs supplies local movement as well.
    """
    base=palette('blight',variant);states=[]
    for offsets in ((0,0,0),(8,8,8),(16,16,16),(-8,-8,-8)):
        row=list(base)
        for k in PULSE_INDICES['blight']:
            c=H.rgb(base[k]) if hasattr(H,'rgb') else tuple(int(base[k][i:i+2],16) for i in (1,3,5))
            row[k]='#'+''.join('%02x'%max(0,min(248,c[i]+offsets[i])) for i in range(3))
        states.append(row)
    return {'blight':states}


def fringe(parent,mask,variant=1):
    """True transparent overhang, touching canopy N1/E2/S4/W8.

    North has a 2px central band and 6–7px flank tips; sides stay 3–4px. The lower central floor
    and foot lane stay empty. Engine places this on foreground BG1 only.
    """
    v=int(variant);mask=int(mask)&15;sick=_is_sick(parent)
    im,d=_new();kind=CANOPY_ANCHOR[v]
    if mask&1:
        if sick:
            d.polygon([(0,0),(15,0),(15,3),(12,4),(10,2),(7,5),(4,3),(2,5),(0,3)],fill=8)
            d.line([(1,1),(5,2),(9,1),(13,2)],fill=9,width=2)
            d.line([(4,1),(5,4),(4,6)],fill=8,width=3)
            _pulse(d,[(9,0),(10,2),(8,4)],v%4,1)
            if v==3:
                d.line([(2,2),(1,6)],fill=8,width=2);d.line([(13,1),(14,6)],fill=8,width=2)
        else:
            H._leaf(d,3,0,7,5,kind,3,4,2);H._leaf(d,12,0,6,4,kind,3,4,2)
            d.line([(1,5),(4,6),(6,4)],fill=2)
    if mask&8:
        if sick:
            d.polygon([(0,0),(2,0),(3,4),(2,8),(4,11),(2,15),(0,15)],fill=8)
            d.line([(0,4),(2,7),(1,11)],fill=9)
            _pulse(d,[(0,8),(2,10),(1,13)],v%3,1)
        else:
            H._leaf(d,-2,7,5,7,kind,3,4,2)
            d.line([(3,6),(4,8),(2,11)],fill=2)
    if mask&2:
        if sick:
            d.polygon([(15,0),(13,0),(12,4),(13,8),(11,11),(13,15),(15,15)],fill=8)
            d.line([(15,3),(13,6),(14,11)],fill=9)
        else:H._leaf(d,18,8,5,7,kind,3,4,2)
    if mask&4:
        # Below-camera foliage shows only a tiny contact rim, not a full
        # inverted fringe that would hide Bloom's feet or invent a platform.
        d.polygon([(0,15),(2,14),(4,15),(7,14),(10,15),(13,14),(15,15)],fill=8 if sick else 2)
    if mask&1:
        # Real roll captures showed that a full 6px central fringe could
        # combine with the base canopy and hide the entire low rolling body.
        # Keep only a 2px central header; long hanging leaves/twigs remain
        # at the flanks, while lower body and soles have a transparent lane.
        p=im.load()
        for y in range(2,16):
            for x in range(4,12):p[x,y]=0
    return im,'blight' if sick else 'foliage'


def arch_group(variant=1):
    """Native 32×16 raised root span. Upper surface is scenery, not a level."""
    v=int(variant);im,d=_new(32,16)
    roots=[(0,14),(3,9),(7,5),(12,2),(19,2),(25,5),(29,10),(31,14)]
    d.line(roots,fill=1,width=6)
    d.line([(x,y-1)for x,y in roots],fill=8,width=4)
    d.line([(x,y-2)for x,y in roots[1:-1]],fill=9,width=3)
    d.line([(4,7),(9,3),(14,1),(18,1)],fill=10)
    # A second tangling root explains the raised collar and its contact ends.
    d.line([(0,12),(6,8),(12,7),(19,4),(26,7),(31,13)],fill=8,width=3)
    d.line([(6,7),(11,6),(16,5)],fill=10)
    if v in (1,4):
        d.polygon([(9,2),(11,0),(15,0),(17,2),(14,4),(10,4)],fill=3)
        d.line([(11,1),(14,1)],fill=5)
    elif v==2:
        d.line([(18,1),(22,3),(25,3)],fill=11)
        d.line([(7,5),(7,8)],fill=8)
    elif v==3:
        d.polygon([(21,3),(24,1),(28,3),(25,5)],fill=3);d.line([(23,2),(25,3)],fill=5)
    else:
        d.line([(12,1),(14,3),(17,2)],fill=15)
    return im,'foliage'
