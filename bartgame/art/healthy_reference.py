"""Living woodland materials that meet the atlas-guided decay naturally.

Native pixel silhouettes, shared cool shadows and quiet ground support the
forest's gold light. Existing named material banks and physical contracts
are retained; no title, item, actor, Drain or blight-specific art is painted.
"""
from copy import deepcopy
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import forest_art as F
import wood_art as W
import paint as P

GRASS='glade_wood_grass';LEAF='glade_wood_leaf';TREE='glade_wood_tree'
BARK='glade_wood_bark';WATER='glade_wood_water';STONE='glade_wood_stone'
OLD_GROUPS={n:list(F.GROUPS[n]) for n in (GRASS,LEAF,TREE,BARK,WATER,STONE)}
GROUPS=deepcopy(OLD_GROUPS)
# Grass body colours match the atlas pass's grass-to-decay fringe exactly.
GROUPS[GRASS]=['#000000','#101828','#183c38','#305038','#486840','#608448','#789848','#b0c870',
               '#383028','#705840','#907850','#b09868','#c8b088','#e8e8d0','#e8c060','#88c8d8']
GROUPS[LEAF]=['#000000','#101828','#102c38','#184040','#185844','#287454','#388c60','#68a868',
              '#a8c880','#486840','#608448','#28202c','#605038','#a08058','#d8a048','#ffe0a0']
GROUPS[TREE]=['#000000','#101828','#102c38','#184040','#185844','#287454','#388c60','#68a868',
              '#a8c880','#305038','#e8e8d0','#28202c','#605038','#a08058','#d8a048','#ffe0a0']
GROUPS[BARK]=['#000000','#101828','#183c38','#305038','#608448','#28202c','#605038','#987848',
              '#b89860','#d0b888','#d8a048','#ffe0a0','#b050a0','#302038','#000000','#000000']
GROUPS[WATER]=['#000000','#101828','#383028','#705840','#907850','#b09868','#101c38','#183848',
               '#205468','#287080','#489898','#88c0c0','#d0e8d8','#38683c','#789850','#e8e0d0']
GROUPS[STONE]=['#000000','#101828','#183c38','#305038','#486840','#608448','#789848','#e8c060',
               '#605038','#987848','#242838','#404850','#687068','#909880','#c0c0a0','#fff0b8']


def stroke(a,pts,ink,width=1,wrap=False):F.stroke(a,pts,W.ID[ink] if isinstance(ink,str) else ink,width,wrap)


def leaf_spray(a,cx,cy,rx,ry,seed,wrap=False):
    """Small pointed leaves grouped into a softly lit, asymmetrical bough."""
    h,w=a.shape;yy,xx=np.mgrid[:h,:w];dx=xx-cx;dy=yy-cy
    if wrap:dx=(dx+w/2)%w-w/2;dy=(dy+h/2)%h-h/2
    oval=(dx/rx)**2+(dy/ry)**2;light=-dx/rx*.45-dy/ry*.55
    edge=.93+np.sin(np.arctan2(dy,dx)*7+seed)*.09
    body=oval<edge
    ramp=W.C('leaf_deep','shadow','leaf_md','leaf_mid','leaf_lt')
    levels=np.clip(np.floor((light+.9)*2.2),0,4).astype(int)
    levels=np.where((oval>.67)&(light<.25),0,levels)
    for i,ink in enumerate(ramp):a[body&(levels==i)]=ink
    r=P.rng(seed)
    for _ in range(int(rx*ry*.9)):
        x=int(round(cx+r.uniform(-.86,.86)*rx));y=int(round(cy+r.uniform(-.8,.8)*ry));X,Y=x%w,y%h
        if not body[Y,X]:continue
        lit=light[Y,X]>.12
        hi=W.ID['leaf_br' if lit else 'leaf_lt'];mid=W.ID['leaf_lt' if lit else 'leaf_mid'];dark=W.ID['shadow']
        # Two- and three-pixel lanceolate leaves; whole clusters carry light.
        shape=['.h.','hmd','.d.'] if (x+y+seed)&1 else ['.h','hm','d.']
        P.stamp(a,x,y,shape,dict(h=hi,m=mid,d=dark),wrap=wrap,mask=body)
    return a


@lru_cache(maxsize=None)
def crown_mass():
    a=np.full((32,32),W.ID['leaf_deep'],np.uint8)
    for i,(x,y,rx,ry) in enumerate(((3,2,10,7),(19,3,12,8),(30,13,11,8),(13,14,12,8),(1,26,11,8),(22,28,13,9))):
        leaf_spray(a,x,y,rx,ry,321+i*43,True)
    return a


def canopy(k=0):
    a=crown_mass();k%=4
    return a[(k//2)*16:(k//2+1)*16,(k%2)*16:(k%2+1)*16].copy()


def canopy_face():
    a=canopy(2);a[9:]=W.ID['leaf_deep']
    for x in (3,11):
        stroke(a,[(x,7),(x-1,11),(x,15)],'bark_dk',3)
        stroke(a,[(x,9),(x-1,13),(x,15)],'bark',1)
    for i,(x,y) in enumerate(((0,7),(8,7),(16,6))):leaf_spray(a,x,y,6,4,610+i,True)
    # Loose moss toes meet the soil; no horizontal black base stripe.
    for x,y in ((2,13),(6,15),(10,14),(14,15)):
        P.stamp(a,x,y,['.h','hd'],dict(h=W.ID['grass_m'],d=W.ID['shadow']),wrap=False)
    return a


def grass(seed=0):
    """Damp, fine-textured turf with quiet low-contrast leaf-shaped patches."""
    field=P.fbm(16,16,1400+seed,((2,.75),(4,.25)))
    a=np.full((16,16),W.ID['grass_m'],np.uint8)
    a[field<.34]=W.ID['grass_d'];a[field>.72]=W.ID['grass_l']
    for i,(x,y) in enumerate(P.scatter(1407+seed*29,12,mind=3)):
        if i%4==0:P.stamp(a,x,y,['.l','md'],dict(l=W.ID['grass_l'],m=W.ID['grass_m'],d=W.ID['grass_d']),wrap=True)
        else:
            a[y,x]=W.ID['grass_d'];a[y,(x+1)%16]=W.ID['grass_m' if i%2 else 'grass_d']
    # A rare warm tip belongs to a tuft, not isolated bright noise.
    for x,y in P.scatter(1517+seed,2,mind=9):
        P.stamp(a,x,y,['.l','md'],dict(l=W.ID['grass_b'],m=W.ID['grass_l'],d=W.ID['grass_d']),wrap=True)
    return a


def earth():
    f=P.fbm(16,16,1703,((2,.7),(4,.3)))
    a=np.full((16,16),W.ID['trail_m'],np.uint8)
    a[f<.31]=W.ID['trail_d'];a[f>.72]=W.ID['trail_l']
    for i,(x,y) in enumerate(P.scatter(1733,8,mind=4)):
        a[y,x]=W.ID['trail_d' if i%3 else 'trail_l']
        if i%3==0:a[y,(x+1)%16]=W.ID['trail_m']
    return a


def tree(cols=2,variant=0,species='oak',lantern=False):
    w,h=cols*16,(cols+1)*16;mid=w//2;root=h-8;a=np.zeros((h,w),np.uint8)
    if species=='birch':
        for tx in (mid-5,mid+3):
            pts=[(tx+1,18),(tx-1,h-18),(tx+1,root)]
            stroke(a,pts,'bark_dk',4);stroke(a,pts,'white',2)
            for y in range(22,root,5):stroke(a,[(tx-1,y),(tx+1,y)],'bark',1)
        boughs=[(mid-6,8,10,7),(mid+6,10,9,7),(mid-8,18,8,6),(mid+6,22,9,6),(mid-2,25,11,6)]
    elif species=='fir':
        stroke(a,[(mid,5),(mid,root)],'bark_dk',5);stroke(a,[(mid-1,11),(mid-1,root)],'bark_l',2)
        boughs=[(mid,5,4,4),(mid-1,11,7,5),(mid+1,18,10,5),(mid-1,24,13,5),(mid+1,29,13,5)]
    else:
        pts=[(mid-2,h-35),(mid+2,h-23),(mid-1,root)]
        stroke(a,pts,'bark_dk',7);stroke(a,[(mid-1,h-34),(mid+1,h-22),(mid-2,root)],'bark_l',3)
        stroke(a,[(mid,h-23),(mid-9,h-32),(mid-12,h-40)],'bark',3)
        stroke(a,[(mid,h-23),(mid+10,h-31),(mid+13,h-37)],'bark',3)
        boughs=[(mid-3,8,mid*.63,7),(mid-9,16,mid*.58,8),(mid+8,15,mid*.6,8),(mid-1,23,mid*.8,8)]
        if cols==3:boughs += [(9,30,10,8),(38,30,10,8),(23,36,14,8)]
    for i,(x,y,rx,ry) in enumerate(boughs):leaf_spray(a,x+variant*(1 if i&1 else -1),y,rx,ry,731+i*31+variant*79)
    # Exposed roots carry the same warm wood as the lantern supports.
    for sign in (-1,1):
        pts=[(mid,root-3),(mid+sign*5,root+1),(mid+sign*(mid-4),h-3)]
        stroke(a,pts,'bark_dk',3);stroke(a,pts,'bark_l',1)
    for x,y in ((mid-4,root+2),(mid+8,root+3),(mid+2,root)):
        P.stamp(a,x,y,['.l','ld'],dict(l=W.ID['grass_l'],d=W.ID['grass_d']))
    if lantern:
        x=mid-9;y=h-24;stroke(a,[(x,y-4),(x,y+4)],'bark_dk')
        a[y:y+5,x-1:x+2]=W.ID['amber'];a[y+1:y+4,x]=W.ID['glow']
    return [a[y:y+16,x:x+16].copy() for y in range(0,h,16) for x in range(0,w,16)]


def bank_water(raw):
    """Cool bank shadows and broken reflection; foam is for actual falls."""
    a=raw.copy();foam=W.ID['foam'];lt=W.ID['water_lt'];rip=W.ID['ripple']
    yy,xx=np.mgrid[:16,:16]
    bright=(a==foam)|(a==rip)
    # Keep a few short reflected highlights, eliminating the bright border.
    a[bright]=lt;a[bright&((xx+yy*3)%7<2)]=W.ID['water_md']
    return a


def rematerial(raw,name):
    a=raw.copy();oldgrass=F.woodland_grass(0);newgrass=grass(0)
    grass_ids=W.C('grass_d','grass_m','grass_l','grass_b','grass_t')
    mask=np.isin(a,grass_ids)&(a==oldgrass)
    a[mask]=newgrass[mask]
    # Paths share exactly the same packed-earth body beneath every edge.
    oldearth=W.trail(0);newe=earth();mask=(a==oldearth)&np.isin(a,W.C('trail_d','trail_m','trail_l','trail_h'))
    a[mask]=newe[mask]
    if name.startswith('shore_'):
        # Wet moss replaces the former pale sand/cream ribbon.
        a[a==W.ID['trail_h']]=W.ID['grass_l'];a[a==W.ID['trail_l']]=W.ID['grass_d']
        a[a==W.ID['soil']]=W.ID['shadow']
    return a


def prop(kind):
    a=np.zeros((16,16),np.uint8)
    if kind=='fern_patch':
        for x,y in ((4,13),(11,14)):
            stroke(a,[(x,y),(x+1,y-8)],'grass_d',2);stroke(a,[(x,y),(x+1,y-8)],'grass_l')
            for k in range(4):
                yy=y-k*2;span=3-k//2
                stroke(a,[(x-span,yy-1),(x,yy+1),(x+span,yy-1)],'grass_l')
                a[max(0,yy-1),min(15,x-span)]=W.ID['grass_b']
    elif kind=='leaf_litter':
        for i,(x,y) in enumerate(((2,4),(10,3),(12,11),(5,12))):
            P.stamp(a,x,y,['.h.','hmd','.d.'],dict(h=W.ID['trail_l'],m=W.ID['trail_d'],d=W.ID['grass_d']))
    elif kind=='bush':
        leaf_spray(a,8,9,7,5,1901);stroke(a,[(7,11),(6,14)],'bark_dk',2)
        for x,y in ((3,12),(10,13)):a[y,x]=W.ID['grass_m']
    return a


def _raw_tiles():
    t={}
    def put(name,group,frames,speed=None):t[name]=(group,frames,speed)
    for i in range(3):put('moss%d'%i,GRASS,[grass(i)])
    for n,i in (('canopy',0),('canopy2',1),('canopy_glint',2)):
        put(n,LEAF,[canopy(i)])
    put('canopy_s',LEAF,[canopy_face()]);put('canopy_n',LEAF,[canopy(1)])
    for i in range(6):put('forest_canopy%d'%i,LEAF,[canopy(i)])
    # Lantern action keeps the original two-frame timing and light extent.
    count=len(F.TILES['canopy_lantern'][1]);fr=[]
    for frame in range(count):
        a=canopy_face();a[8:13,6:9]=W.ID['amber'];a[9:12,7]=W.ID['glow' if frame%2 else 'yellow'];fr.append(a)
    put('canopy_lantern',LEAF,fr,F.TILES['canopy_lantern'][2])
    for prefix,cols,variant,lantern,species in (('tree',2,0,False,'oak'),('tree2',2,1,True,'oak'),('gtree',3,0,False,'oak'),('gtree2',3,1,True,'oak'),('birch',2,0,False,'birch'),('fir',2,0,False,'fir')):
        parts=tree(cols,variant,species,lantern)
        names=['tree_top_nw','tree_top_ne','tree_mid_w','tree_mid_e','tree_trunk_w','tree_trunk_e'] if prefix=='tree' else ['%s_%d'%(prefix,i) for i in range(len(parts))]
        for n,a in zip(names,parts):put(n,TREE,[a])
    for n in ('fern_patch','leaf_litter','bush'):put(n,TREE if n=='bush' else GRASS,[prop(n)])
    for n,(group,frames,speed) in F.TILES.items():
        if n in t:continue
        if group=='wood_grass' and not n.startswith(('thicket_','myst_')):
            if n=='black':continue
            put(n,GRASS,[rematerial(a,n) for a in frames],speed)
        elif group=='wood_water':
            put(n,WATER,[bank_water(a) if n.startswith('water_') and n!='water_foam' else a.copy() for a in frames],speed)
    return t


TILES=_raw_tiles();CHANGED_NAMES=set(TILES);ALLOWED_NAMES=set(TILES)


def rgb(h):return tuple(int(h[i:i+2],16) for i in (1,3,5))


def quantize(a,group):
    # Keep each represented ink's semantic slot: bark highlights stay
    # highlights even when their new hue is nearer an old middle tone.
    # Unrepresented global inks use the nearest material colour.
    values=np.array([rgb(F.HEX[i]) for i in range(1,len(W.COLORS)+1)],dtype='int32')
    palette=np.array([rgb(h) for h in GROUPS[group][1:]],dtype='int32')
    delta=values[:,None,:]-palette[None,:,:]
    lut=np.concatenate(([0],(delta*delta*np.array([2,3,2])).sum(axis=2).argmin(axis=1)+1))
    semantic={h:i for i,h in enumerate(OLD_GROUPS[group]) if i}
    for i in range(1,len(W.COLORS)+1):
        if F.HEX[i] in semantic:lut[i]=semantic[F.HEX[i]]
    q=lut[a]
    return [''.join('%x'%v for v in row) for row in q]


def apply(metatiles,palettes):
    contracts={m['name']:(m['type'],m.get('coll'),m.get('prop')) for m in metatiles}
    untouched={m['name']:deepcopy(m) for m in metatiles if m['pal'] not in GROUPS and m['name'] not in TILES}
    for m in metatiles:
        n=m['name']
        if n in TILES:
            group,frames,speed=TILES[n]
            old_count=len(m.get('frames') or [m['art']])
            assert len(frames)==old_count,(n,len(frames),old_count)
            m['pal']=group;m.pop('qpals',None);m.pop('art',None);m.pop('frames',None)
            rows=[quantize(a,group) for a in frames]
            if len(rows)>1:m['frames']=rows
            else:m['art']=rows[0]
            # Keep the original animation speed contract.
        # Non-repainted props and woodland interiors intentionally keep
        # their semantic indices: every material ramp retains its slot
        # order (outline, shadow, body, highlights, wood/stone/water).
        if m['pal'] in GROUPS:ALLOWED_NAMES.add(n)
        assert (m['type'],m.get('coll'),m.get('prop'))==contracts[n],n
    assert all(next(m for m in metatiles if m['name']==n)==old for n,old in untouched.items())


def preview(metatiles,path='/workspace/setup/healthy-final-tiles.png'):
    names=['moss0','moss1','moss2','path','pedge_1','pedge_3','shore_1','water_1','canopy_s','forest_canopy0','forest_canopy1','forest_canopy2','forest_canopy3','bush','fern_patch','leaf_litter','tree_top_nw','tree_top_ne','tree_mid_w','tree_mid_e','tree_trunk_w','tree_trunk_e','birch_0','fir_0']
    selected=[m for n in names for m in metatiles if m['name']==n]
    out=Image.new('RGB',(6*170,46+((len(selected)+5)//6)*110),'#101820');d=ImageDraw.Draw(out);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
    for i,m in enumerate(selected):
        rows=(m.get('frames') or [m['art']])[0];p=GROUPS[m['pal']];a=np.zeros((16,16,4),np.uint8)
        for y,row in enumerate(rows):
            for x,v in enumerate(row):
                if int(v,16):a[y,x]=(*rgb(p[int(v,16)]),255)
        tile=Image.fromarray(a);x=i%6*170+8;y=46+i//6*110
        out.paste(tile.resize((64,64),Image.Resampling.NEAREST),(x,y),tile.resize((64,64),Image.Resampling.NEAREST));out.paste(tile,(x+80,y+48),tile);d.text((x,y+72),m['name'],font=font,fill='#e8e8d0')
    d.text((10,12),'Living forest / native material preview (not an emulator capture)',font=font,fill='#e8e8d0');out.save(path);return path
