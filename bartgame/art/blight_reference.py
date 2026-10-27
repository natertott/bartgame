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
       '#304030','#404038','#484048','#483048','#382040',
       '#503060','#603870','#802890','#b040b8','#d860e8','#f080f8'],
 DEEP:['#000000','#100818','#181028','#201030','#301840','#402050',
       '#583068','#784080','#601078','#a018c0','#d830e8','#f078f8',
       '#f8b8f8','#304830','#506838','#886048'],
 # Seven legacy snag colors are retained exactly because dead_tree also
 # appears in the healthy forest. Its RGB pixels are remapped losslessly.
 GROWTH:['#000000','#100c20','#302038','#503048','#805068','#d860e8',
         '#283c38','#503828','#101c48','#1c2868','#303880','#8010a0',
         '#c020e0','#f8b0f8','#587838','#989078'],
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
    a[:,:,:3]=np.clip(a[:,:,:3]*.48+base*.52,0,255).astype('uint8')
    a=np.roll(a,((seed*3)%16,(seed*5)%16),axis=(0,1))
    body=np.array([48,24,64])
    for edge in (0,15):
        a[edge,:,:3]=(a[edge,:,:3]*.25+body*.75).astype('uint8')
        a[:,edge,:3]=(a[:,edge,:3]*.25+body*.75).astype('uint8')
    a[:,:,3]=255
    return Image.fromarray(a)


def vein(seed=0,frame=0,subtle=False):
    """Quiet gravel and short subsurface root fissures, never a bright glyph.

    The supplied vein silhouette is intentionally fragmented and turned as
    material variation. Magenta is reserved for hazards and large growths.
    """
    out=floor(seed).copy();body=np.asarray(out).copy()
    crack=S.rgba_tile('blight_vein',frame=frame)
    crack=crack.transpose((Image.Transpose.FLIP_LEFT_RIGHT,Image.Transpose.ROTATE_90,
                           Image.Transpose.FLIP_TOP_BOTTOM,Image.Transpose.ROTATE_270)[seed%4])
    a=np.asarray(crack).copy();yy,xx=np.mgrid[:16,:16]
    # Keep just one crooked limb of the reference fissure. Rotate and offset
    # the oval so adjacent native tiles cannot form a carpet of repeated Ys.
    cx,cy=((5,7),(10,6),(6,10),(10,10),(5,11),(11,5),(8,5),(8,11))[seed%8]
    keep=((xx-cx)**2/32+(yy-cy)**2/20)<1
    fade=np.minimum(np.minimum(xx,15-xx),np.minimum(yy,15-yy))/3
    strength=(.13 if subtle else .22)*np.clip(fade,0,1)*keep*(a[:,:,3]/255)
    body[:,:,:3]=np.rint(body[:,:,:3]*(1-strength[:,:,None])+a[:,:,:3]*strength[:,:,None]).astype('uint8')
    return Image.fromarray(body)


def leaf(frame=0,lit=False):
    im=S.rgba_tile('canopy_sick_lit' if lit else 'canopy_sick',frame=frame)
    a=np.asarray(im).copy();behind=np.asarray(S.rgba_tile('canopy_sick')).copy()
    behind=np.roll(behind,(5,7),axis=(0,1));dark=a[:,:,:3].max(axis=2)<30
    fill=behind[:,:,:3]
    fill=np.where((fill.max(axis=2)<30)[:,:,None],np.array([16,24,56]),fill*.65).astype('uint8')
    a[dark,:3]=fill[dark]
    # The atlas reads as blue-violet leaf masses with a few luminous flowers.
    # Preserve two connected blossom pockets, cooling the remaining pink
    # foliage into quieter blue leaves so a whole wall does not glitter.
    yy,xx=np.mgrid[:16,:16]
    buds=((xx-4)**2+(yy-11)**2<10)|((xx-12)**2+(yy-7)**2<6)
    hot=(a[:,:,0]>90)&(a[:,:,2]>100)&(a[:,:,0]>a[:,:,1]*1.4)&~buds
    value=np.minimum(76,a[:,:,:3].astype(float).mean(axis=2)*.65)
    cool=np.stack((value*.6,value*.75,value*1.55),axis=2).astype('uint8')
    a[hot,:3]=cool[hot];a[:,:,3]=255
    return Image.fromarray(a)


def patch(name,frame=0):
    src=np.asarray(S.rgba_tile('blight_ground',variant=int(name.endswith('1')))).copy()
    if name=='blight_ground2':src=np.asarray(S.rgba_tile('blight_ground_lit',frame=frame)).copy()
    src[:,:,3]=255
    return Image.fromarray(src)


def transition(name):
    """A broad, irregular grass-to-bruise fringe for every side and corner."""
    sides,corners=int(name[4],16),int(name[5],16)
    yy,xx=np.mgrid[:16,:16];depth=11.5
    waves={side:W.rot_wave(1700+side)+(depth-W.ROT_D) for side in (1,2,4,8)}
    distances={1:(yy+.5)/waves[1][xx],4:(15.5-yy)/waves[4][xx],
               8:(xx+.5)/waves[8][yy],2:(15.5-xx)/waves[2][yy]}
    terms=[distances[side] for side in (1,2,4,8) if sides&side]
    for bit,(cx,cy) in ((1,(0,0)),(2,(16,0)),(4,(16,16)),(8,(0,16))):
        if corners&bit:terms.append(np.sqrt((xx+.5-cx)**2+(yy+.5-cy)**2)/depth)
    u=-.14*np.log(sum(np.exp(-t/.14) for t in terms)) if terms else np.full((16,16),9.)
    blend=np.clip((u-.14)/.94,0,1)
    blend=blend*blend*(3-2*blend)
    # Dither only the intermediate band. Both the outside edge and interior
    # retain their authored colors and meet adjacent tiles without a seam.
    intermediate=(blend>0)&(blend<1)
    jitter=(W.P.B4[yy%4,xx%4]-.5)*.10
    blend=np.clip(blend+intermediate*jitter,0,1)
    turf=F.woodland_grass(0)
    grass=np.array([[rgb(F.HEX[int(v)]) for v in row] for row in turf],dtype=float)
    purple=np.asarray(floor(0)).copy()
    purple[:,:,:3]=np.rint(grass*(1-blend[:,:,None])+purple[:,:,:3]*blend[:,:,None]).astype('uint8')
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


@lru_cache(maxsize=1)
def tree_art():
    a=np.asarray(S.tree_image()).copy()
    # Reveal the source's warm bark between its violet veins. No extra
    # outline, glow cloud or floating particles are added to its silhouette.
    bark=(a[:,:,3]>0)&(a[:,:,0]>a[:,:,2]*.85)&(a[:,:,1]>a[:,:,0]*.35)
    lifted=np.minimum(255,a[:,:,:3].astype(float)*1.22+np.array([7,9,3])).astype('uint8')
    a[bark,:3]=lifted[bark]
    return Image.fromarray(a)


def tree_parts(variant=0):
    im=tree_art()
    if variant:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return [im.crop((x*16,y*16,x*16+16,y*16+16)) for y in range(3) for x in range(2)]


def wall_tree_parts():
    """The full atlas tree can also emerge from a solid canopy boundary."""
    tree=tree_art();back=Image.new('RGBA',(32,48))
    for y in range(3):
        for x in range(2):
            tile=leaf().transpose(Image.Transpose.FLIP_LEFT_RIGHT) if (x+y)%2 else leaf()
            back.alpha_composite(tile,(x*16,y*16))
    # A quiet pocket behind the trunk separates dark bark from busy leaves.
    a=np.asarray(back).copy();yy,xx=np.mgrid[:48,:32]
    pocket=np.exp(-((xx-16)**2/55+(yy-26)**2/240))*.6
    dark=np.array([20,16,32])
    a[:,:,:3]=np.rint(a[:,:,:3]*(1-pocket[:,:,None])+dark*pocket[:,:,None]).astype('uint8')
    back=Image.fromarray(a);back.alpha_composite(tree)
    return [back.crop((x*16,y*16,x*16+16,y*16+16)) for y in range(3) for x in range(2)]


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
    put('forest_blight_dead_tree',GROWTH,[S.rgba_tile('dead_tree')])
    for prefix,variant in (('btree',0),('sicktree',1)):
        for i,piece in enumerate(tree_parts(variant)):put('%s_%d'%(prefix,i),GROWTH,[piece])
    put('blight_mist',SICK,[haze(f) for f in range(2)],20)
    put('forest_blight_pit',DEEP,[S.rgba_tile('blight_floor_pits',frame=f) for f in range(2)],20)
    for i in range(8):put('forest_blight_vein%d'%i,DEEP,[vein(i,f) for f in range(2)],24)
    for i,piece in enumerate(wall_tree_parts()):put('forest_blight_tree%d'%i,GROWTH,[piece])
    return t


TILES=_data()
CHANGED_NAMES=set(TILES)
PROPS={'blight_crystal','forest_blight_dead_tree'}


def apply(metatiles,palettes):
    """Install material art only; retain every existing type/collision/id."""
    # Append the cosmetic clone so every established metatile id stays fixed.
    if not any(m['name']=='forest_blight_pit' for m in metatiles):
        clone=deepcopy(next(m for m in metatiles if m['name']=='pit'))
        clone['name']='forest_blight_pit';clone['prop']=False;metatiles.append(clone)
    legacy_tree=deepcopy(next(m for m in metatiles if m['name']=='dead_tree'))
    for name,source in [('forest_blight_dead_tree','dead_tree')]+[
            ('forest_blight_vein%d'%i,'blight_vein') for i in range(8)]+[
            ('forest_blight_tree%d'%i,'canopy_blight') for i in range(6)]:
        if not any(m['name']==name for m in metatiles):
            clone=deepcopy(next(m for m in metatiles if m['name']==source))
            clone['name']=name;metatiles.append(clone)
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
    preserved=next(m for m in metatiles if m['name']=='dead_tree')
    assert preserved.get('prop')==legacy_tree.get('prop')
    assert np.array_equal(np.asarray(image(legacy_tree['art'],OLD_GROUPS[GROWTH])),
                          np.asarray(image(preserved['art'],GROUPS[GROWTH]))), 'shared dead_tree colors changed'


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
