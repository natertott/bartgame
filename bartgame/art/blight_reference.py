"""Final native forest corruption art, guided by the supplied atlas.

Only decay materials change. The established rot masks retain their wide
side/corner grass transitions; physical tile contracts stay authoritative.
"""
from copy import deepcopy
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import wood_art as W
import forest_art as F
import blight_reference_source as S

SICK='glade_wood_sick'
DEEP='glade_wood_deep'
GROWTH='glade_wood_blight'
STONE='blight_reference_stone'
GROUPS={
 SICK:['#000000','#305038','#486840','#608448','#789848',
       '#101020','#281038','#382050','#503068','#704080',
       '#a018b8','#d830e8','#f080f8','#384838','#587050','#809058'],
 DEEP:['#000000','#100818','#181028','#201030','#301840','#402050',
       '#583068','#784080','#601078','#a018c0','#d830e8','#f078f8',
       '#f8b8f8','#304830','#506838','#886048'],
 GROWTH:['#000000','#080c18','#101c48','#1c2868','#303880','#241030',
         '#482050','#704080','#8010a0','#c020e0','#f050f8','#f8b0f8',
         '#504038','#203c28','#587838','#b09050'],
 STONE:['#000000','#080c18','#181828','#303040','#484450','#686060',
        '#a09070','#183828','#405c30','#789848','#281030','#581858',
        '#b020d8','#f070f8','#f8c0f8','#c8a860'],
}
OLD_GROUPS={SICK:F.GROUPS[SICK],DEEP:F.GROUPS[DEEP],GROWTH:F.GROUPS[GROWTH]}


def rgb(h):return tuple(int(h[i:i+2],16) for i in (1,3,5))


def quantize(image,group):
    a=np.asarray(image.convert('RGBA'));c=a[:,:,:3].astype('int32')
    p=np.asarray([rgb(h) for h in GROUPS[group][1:]],dtype='int32')
    # Emphasize value enough that shadow, soil and glowing cracks remain
    # distinct on the small screen; no noisy per-pixel error dithering.
    delta=c[:,:,None,:]-p[None,None,:,:]
    ix=(delta*delta*np.array([2,3,2])).sum(axis=3).argmin(axis=2)+1
    return [''.join('%x'%ix[y,x] if a[y,x,3]>=128 else '0' for x in range(a.shape[1])) for y in range(a.shape[0])]


def image(rows,palette):
    a=np.zeros((len(rows),len(rows[0]),4),dtype='uint8')
    for y,row in enumerate(rows):
        for x,ch in enumerate(row):
            v=0 if ch in '. ' else int(ch,16)
            if v:a[y,x]=(*rgb(palette[v]),255)
    return Image.fromarray(a)


@lru_cache(maxsize=None)
def floor(seed=0):
    a=np.asarray(S.rgba_tile('blight_floor')).copy()
    # Keep the source's mottled violet earth but lower its speckle contrast.
    # Opposite edges share the same subdued body colour, so seeded variants
    # can meet in any order without revealing square borders.
    base=np.array([42,22,60])
    a[:,:,:3]=np.clip(a[:,:,:3]*.76+base*.24,0,255).astype('uint8')
    a=np.roll(a,((seed*3)%16,(seed*5)%16),axis=(0,1))
    body=np.array([48,24,64])
    for edge in (0,15):
        a[edge,:,:3]=(a[edge,:,:3]*.25+body*.75).astype('uint8')
        a[:,edge,:3]=(a[:,edge,:3]*.25+body*.75).astype('uint8')
    a[:,:,3]=255
    return Image.fromarray(a)


def vein(seed=0,frame=0,subtle=False):
    out=floor(seed).copy();crack=S.rgba_tile('blight_vein',frame=frame)
    if subtle:
        a=np.asarray(crack).copy();yy,xx=np.mgrid[:16,:16]
        # Reveal one small connected fissure, retaining the atlas's branching
        # silhouette rather than scattering disconnected bright pixels.
        a[(xx-(7+seed%3))**2+(yy-8)**2>30,3]=0
        crack=Image.fromarray(a)
    out.alpha_composite(crack)
    return out


def leaf(frame=0,lit=False):
    im=S.rgba_tile('canopy_sick_lit' if lit else 'canopy_sick',frame=frame)
    a=np.asarray(im).copy();behind=np.asarray(S.rgba_tile('canopy_sick')).copy()
    behind=np.roll(behind,(5,7),axis=(0,1));dark=a[:,:,:3].max(axis=2)<30
    fill=behind[:,:,:3]
    fill=np.where((fill.max(axis=2)<30)[:,:,None],np.array([16,24,56]),fill*.65).astype('uint8')
    a[dark,:3]=fill[dark];a[:,:,3]=255
    return Image.fromarray(a)


def patch(name,frame=0):
    src=np.asarray(S.rgba_tile('blight_ground',variant=int(name.endswith('1')))).copy()
    if name=='blight_ground2':src=np.asarray(S.rgba_tile('blight_ground_lit',frame=frame)).copy()
    src[:,:,3]=255
    return Image.fromarray(src)


def transition(name):
    raw=F.TILES[name][1][0]
    purple=np.asarray(floor(0)).copy()
    healthy=set(W.C('grass_d','grass_m','grass_l','grass_b','grass_t'))
    fringe={W.ID['sick_d']:(56,64,56),W.ID['sick_m']:(72,64,72),W.ID['sick_l']:(104,72,112)}
    for y in range(16):
        for x in range(16):
            v=int(raw[y,x])
            if v in healthy:purple[y,x]=(*rgb(F.HEX[v]),255)
            elif v in fringe:
                mix=.30 if v==W.ID['sick_d'] else .52 if v==W.ID['sick_m'] else .72
                turf=np.array(rgb(F.HEX[W.ID['grass_m']]))
                purple[y,x,:3]=(turf*(1-mix)+purple[y,x,:3]*mix).astype('uint8')
    return Image.fromarray(purple)


def haze(frame):
    a=np.asarray(S.rgba_tile('mist',frame=frame)).copy()
    # A proper vapor cloud: retain soft source opacity through a stable
    # ordered transparency pattern rather than painting a solid rectangle.
    bayer=np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]])
    yy,xx=np.mgrid[:16,:16]
    strength=np.clip((a[:,:,:3].max(axis=2).astype(float)-12)/150,0,.8)*(a[:,:,3]/255)
    a[:,:,3]=np.where(strength>(bayer[(yy+frame)%4,xx%4]+.5)/16,255,0)
    return Image.fromarray(a)


def tree_parts(variant=0):
    im=S.tree_image()
    if variant:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return [im.crop((x*16,y*16,x*16+16,y*16+16)) for y in range(3) for x in range(2)]


def _data():
    t={}
    def put(name,group,frames,speed=16):t[name]=(group,[quantize(im,group) for im in frames],speed)
    put('canopy_blight',GROWTH,[leaf()])
    put('canopy_blight2',GROWTH,[leaf(f,True) for f in range(2)],18)
    for n,variant in (('blight_wall',0),('blight_wall2',1)):
        put(n,STONE,[S.rgba_tile('blight_wall',variant=variant)])
    put('blight_wall_lit',STONE,[S.rgba_tile('blight_wall_lit',frame=f) for f in range(2)],16)
    for i in range(2):put('blight_ground%d'%i,SICK,[patch('blight_ground%d'%i)])
    put('blight_ground2',SICK,[patch('blight_ground2',f) for f in range(2)],18)
    for n in ('moss_blight','moss_blight2'):
        raw=F.TILES[n][1][0];a=np.zeros((16,16,4),dtype='uint8');base=np.asarray(patch('blight_ground0'))
        for y in range(16):
            for x in range(16):
                v=int(raw[y,x]);a[y,x]=(*rgb(F.HEX[v]),255)
                if v in W.C('earth_2','earth_3','earth_4','earth_5','earth_6','v_1','v_2','v_3','v_4','mag_d'):a[y,x]=base[y,x]
        put(n,SICK,[Image.fromarray(a)])
    for name in F.TILES:
        if name.startswith('rot_'):put(name,SICK,[transition(name)])
    put('blight_floor',DEEP,[floor()])
    put('blight_floor2',DEEP,[vein(1,f,True) for f in range(2)],20)
    for i in range(8):put('forest_rot%d'%i,DEEP,[vein(i,0,True) if i==7 else floor(i)])
    put('blight_vein',DEEP,[vein(0,f) for f in range(2)],16)
    put('blight_pool',DEEP,[S.rgba_tile('blight_pool',frame=f) for f in range(2)],16)
    put('blight_crystal',GROWTH,[S.rgba_tile('crystal')])
    put('dead_tree',GROWTH,[S.rgba_tile('dead_tree')])
    for prefix,variant in (('btree',0),('sicktree',1)):
        for i,piece in enumerate(tree_parts(variant)):put('%s_%d'%(prefix,i),GROWTH,[piece])
    put('blight_mist',SICK,[haze(f) for f in range(2)],20)
    put('forest_blight_pit',DEEP,[S.rgba_tile('blight_floor_pits',frame=f) for f in range(2)],20)
    return t


TILES=_data()
CHANGED_NAMES=set(TILES)
PROPS={'blight_crystal','dead_tree'}


def apply(metatiles,palettes):
    """Install material art only; retain every existing type/collision/id."""
    # Append the cosmetic clone so every established metatile id stays fixed.
    if not any(m['name']=='forest_blight_pit' for m in metatiles):
        clone=deepcopy(next(m for m in metatiles if m['name']=='pit'))
        clone['name']='forest_blight_pit';clone['prop']=False;metatiles.append(clone)
    unchanged={m['name']:deepcopy(m) for m in metatiles if m['pal'] not in OLD_GROUPS and m['name'] not in TILES}
    physical={m['name']:(m['type'],m.get('coll')) for m in metatiles}
    for m in metatiles:
        name=m['name'];g=m['pal']
        if name in TILES:
            group,frames,speed=TILES[name]
        elif g in OLD_GROUPS:
            group=g;old=OLD_GROUPS[g]
            frames=[quantize(image(a,old),group) for a in m.get('frames') or [m['art']]]
            speed=m.get('anim_speed',16);CHANGED_NAMES.add(name)
        else:continue
        m['pal']=group;m.pop('qpals',None);m.pop('art',None);m.pop('frames',None)
        if len(frames)>1:m['frames']=frames;m['anim_speed']=speed
        else:m['art']=frames[0]
        if name in PROPS:m['prop']=True
        assert (m['type'],m.get('coll'))==physical[name],name
    assert all(next(m for m in metatiles if m['name']==n)==value for n,value in unchanged.items())


def preview(metatiles,path='/workspace/setup/blight-final-tiles.png'):
    selected=[m for m in metatiles if m['name'] in CHANGED_NAMES and not m['name'].startswith('rot_')]
    selected+=[next(m for m in metatiles if m['name']==n) for n in ('rot_00','rot_10','rot_01','rot_ff') if any(m['name']==n for m in metatiles)]
    w,h=180,120;out=Image.new('RGB',(w*6,48+h*((len(selected)+5)//6)),'#101820');d=ImageDraw.Draw(out)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
    d.text((12,10),'Final native blight art — source preview, not emulator capture',font=font,fill='#eee9d7')
    for i,m in enumerate(selected):
        x=i%6*w;y=48+i//6*h;rows=(m.get('frames') or [m['art']])[0]
        tile=image(rows,GROUPS[m['pal']]);large=tile.resize((64,64),Image.Resampling.NEAREST)
        out.paste(large,(x+8,y),large);out.paste(tile,(x+88,y+48),tile)
        d.text((x+8,y+74),m['name'],font=font,fill='#eee9d7')
        d.text((x+8,y+91),m['type']+' / '+str(len(m.get('frames',[])) or 1)+' frames',font=font,fill='#9eafba')
    out.save(path)
    return path
