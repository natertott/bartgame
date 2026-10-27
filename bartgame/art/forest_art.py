"""Forest-only art direction: verdigris, candle gold and luminous decay.

The terrain painter supplies collision-compatible silhouettes and edge families;
this pass authors the final forest/mystery-room artwork AFTER the legacy pack.
No Drain, UI, hero or item art is changed. All pixels are native 4bpp indices.
"""
import numpy as np
import wood_art as W
import paint as P

# Blue shadows and yellow light, rather than a green monochrome wash.
INKS = dict(
    outline='#081820', leaf_deep='#082838', shadow='#103c38', leaf_md='#185044',
    leaf_mid='#20684c', leaf_lt='#308450', leaf_br='#60a850', leaf_hl='#a8c868',
    grass_d='#305038', grass_m='#486840', grass_l='#608448', grass_b='#789848', grass_t='#b0c870',
    soil='#302820', trail_d='#685038', trail_m='#987848', trail_l='#b89860', trail_h='#d8c088',
    bark_dk='#201c20', bark='#503828', bark_l='#806040', bark_ll='#b09050', wood_cut='#d0b070',
    white='#e8e8c8', yellow='#e8c060', blue='#78c0d8', amber='#c88830', glow='#ffe0a0', gold_l='#fff0b8',
    water_deep='#081c38', water_dk='#103850', water_md='#185068', water_mid='#206880',
    water_lt='#388898', ripple='#70b8c8', foam='#c0e8e0',
    stone_0='#202830', stone_1='#384048', stone_2='#586058', stone_3='#808878', stone_4='#b0b898',
    v_0='#180c30', v_1='#281840', v_2='#402050', v_3='#583068', v_4='#804088',
    mag_d='#702090', mag='#b038d8', mag_l='#f088f8',
    sick_d='#283c38', sick_m='#485040', sick_l='#989078',
    bt_o='#100c20', bt_d='#302038', bt_m='#503048', bt_l='#805068', bt_g='#d860e8',
    earth_0='#182030', earth_1='#283040', earth_2='#384048', earth_3='#505858',
    earth_4='#686868', earth_5='#888080', earth_6='#a8a098',
    bl_deep='#101830', bl_dk='#182838', bl_md='#283848', bl_mid='#404850',
    bl_lt='#586858', bl_br='#788060', bl_hl='#a0a078',
    cave_glow='#58b8d0', cave_glow_l='#c0f0e8', thorn='#b050a0', thorn_vine='#302038')
HEX = {i: INKS.get(n, h) for i, (n, h) in enumerate(W.COLORS, 1)}
PREFIX = 'glade_'


def stroke(img, points, colour, width=1, wrap=False):
    """Native pixel branch strokes, shared by living roots and exposed veins."""
    h,w=img.shape
    for (x0,y0),(x1,y1) in zip(points,points[1:]):
        n=max(abs(x1-x0),abs(y1-y0),1)
        for i in range(n+1):
            x=round(x0+(x1-x0)*i/n); y=round(y0+(y1-y0)*i/n)
            for dy in range(width):
                for dx in range(width):
                    X,Y=x+dx,y+dy
                    if wrap: X%=w; Y%=h
                    if 0<=X<w and 0<=Y<h: img[Y,X]=colour


def leaf_cluster(img, cx, cy, rx, ry, seed, sick=False, wrap=False):
    """A broken oval of leaves, lit as a whole rather than separate spheres."""
    h,w=img.shape
    yy,xx=np.mgrid[0:h,0:w]
    dx=xx-cx; dy=yy-cy
    if wrap:
        dx=(dx+w/2)%w-w/2; dy=(dy+h/2)%h-h/2
    jitter=P.vnoise(w,h,max(2,w//5),max(2,h//5),seed)
    oval=(dx/rx)**2+(dy/ry)**2
    angle=np.arctan2(dy,dx)
    body=oval < .88+np.sin(angle*9+seed)*.07+(jitter-.5)*.28
    light=-dx/rx*.65-dy/ry*.55
    ramp=W.C('leaf_deep','shadow','leaf_md','leaf_mid','leaf_lt','leaf_br','leaf_hl')
    if sick: ramp=W.C('bt_o','v_0','v_1','v_2','v_3','v_4','mag_d')
    tones=np.where(light<-.5,0,np.where(light<-.15,1,np.where(light<.15,2,np.where(light<.45,3,4))))
    tones=np.where((oval>.65)&(light<.2),0,tones)
    for i,c in enumerate(ramp): img[body & (tones==i)]=c
    # Paired pointed leaves appear in small groups with clear rest between.
    rng=P.rng(seed)
    for _ in range(max(7,int(rx*ry/4))):
        x=int(cx+(rng.rand()-.5)*rx*1.5); y=int(cy+(rng.rand()-.5)*ry*1.3)
        X,Y=x%w,y%h
        if not body[Y,X]: continue
        lit=light[Y,X]>.05
        mark=['.hh.','hlm.','.dd.'] if (x+y)%2 else ['.hh.','.mlh','.dd.']
        P.stamp(img,x,y,mark,
                dict(h=ramp[5 if lit else 3],l=ramp[4 if lit else 2],m=ramp[3 if lit else 1],d=ramp[1]),
                wrap=wrap,mask=body)
    return img


def canopy_mass(sick=False):
    """A 32px continuous crown: its four tiles meet as one irregular mass."""
    img=np.full((32,32),W.ID['v_0' if sick else 'leaf_deep'],np.uint8)
    lobes=((4,5,11,8),(20,2,12,9),(30,15,11,9),(13,14,13,10),(4,29,12,9),(23,29,14,11))
    for i,(x,y,rx,ry) in enumerate(lobes):
        leaf_cluster(img,x,y,rx,ry,193+i*17,sick,True)
    return img


def canopy(seed=0,sick=False):
    img=canopy_mass(sick)
    k=seed%4
    return img[(k//2)*16:(k//2+1)*16,(k%2)*16:(k%2+1)*16].copy()


def canopy_face(seed=0):
    img=canopy(seed)
    img[8:,:]=W.ID['leaf_deep']
    for x in (3+seed%2,11):
        stroke(img,[(x,6),(x-1,12),(x+1,15)],W.ID['bark_dk'],3)
        stroke(img,[(x,8),(x-1,13)],W.ID['bark'],1)
    for i,(x,y) in enumerate(((1,6),(8,7),(15,6))):
        leaf_cluster(img,x,y,6,4,319+i+seed,wrap=True)
    img[15,:]=W.ID['shadow']
    for x in (1,6,13): img[15,x]=W.ID['grass_m']
    return img


def woodland_grass(seed,tufts=3):
    """Quiet turf leaves room for landmarks and readable enemies."""
    img=np.full((16,16),W.ID['grass_m'],np.uint8)
    for x,y in P.scatter(1201+seed*31,7,mind=4):
        img[y,x]=W.ID['grass_d']
        img[y,(x+1)%16]=W.ID['grass_d']
    for i,(x,y) in enumerate(P.scatter(1301+seed*19,tufts,mind=6)):
        P.stamp(img,x,y,['.l','ld'],dict(l=W.ID['grass_l'],d=W.ID['grass_d']),wrap=True)
        if i==0: img[y,x]=W.ID['grass_b']
    return img


def flowing_water(seed,frame):
    """Deep open water and sparse arcs; banks use this identical body tone."""
    yy,xx=np.mgrid[0:16,0:16]
    f=P.vnoise(16,16,2,2,301+seed)
    img=np.where(f>.54,W.ID['water_md'],W.ID['water_dk']).astype(np.uint8)
    for i,(x,y) in enumerate(((1,3),(10,10))):
        x=(x+frame*2)%16
        P.stamp(img,x,y,['.rrr.','l...l'],dict(r=W.ID['water_lt'],l=W.ID['water_md']),wrap=True)
    return img


def tree(cols=2,lantern=False,sick=False,variant=0,species='oak'):
    """A full silhouette with branches, irregular crown, and rooted footing."""
    w,h=cols*16,(cols+1)*16; mid=w//2
    img=np.zeros((h,w),np.uint8)
    for x in range(cols):
        img[-16:,x*16:x*16+16]=woodland_grass(x%3) if not sick else rotten(variant)
    bark=W.C('outline','bark_dk','bark','bark_l','bark_ll') if not sick else W.C('bt_o','bt_d','bt_m','bt_l','bt_g')
    root=h-10
    trunkx=mid+(1 if variant else -1)
    if species=='birch':
        # Two silver trunks, deliberately distinct from the broad old oak.
        for tx in (mid-5,mid+3):
            stroke(img,[(tx+2,h-31),(tx-1,h-15),(tx+1,root)],W.ID['bark_dk'],4)
            stroke(img,[(tx+2,h-31),(tx-1,h-15),(tx+1,root)],W.ID['white'],2)
            for y in range(h-27,root,5): img[y,tx:tx+2]=W.ID['bark']
        blobs=[(mid-7,8,9,7),(mid+5,9,9,7),(mid-9,18,8,7),(mid+7,20,8,7),(mid,23,10,7)]
    elif species=='fir':
        stroke(img,[(mid,8),(mid,root)],bark[1],5)
        stroke(img,[(mid,8),(mid-1,root)],bark[3],2)
        # Long drooping boughs, a tapering dark yew rather than a cone icon.
        blobs=[(mid,5,4,5),(mid-1,11,7,5),(mid+1,17,10,6),(mid-1,24,13,6),(mid+2,29,13,5)]
    else:
        stroke(img,[(trunkx-2,h-35),(trunkx+2,h-22),(trunkx-1,root)],bark[1],7)
        stroke(img,[(trunkx-1,h-35),(trunkx+1,h-22),(trunkx-2,root)],bark[3],3)
        stroke(img,[(mid,h-24),(mid-9,h-32),(mid-12,h-41)],bark[2],3)
        stroke(img,[(mid,h-22),(mid+10,h-31),(mid+13,h-37)],bark[2],3)
        blobs=[(mid-3,9,mid*.62,8),(mid-9,17,mid*.57,9),(mid+8,16,mid*.58,9),(mid-2,24,mid*.79,9)]
        if cols==3: blobs += [(9,31,9,9),(38,30,10,9),(23,38,14,8)]
    for sign in (-1,1):
        stroke(img,[(mid,root-2),(mid+sign*6,root+2),(mid+sign*(w//2-4),h-3)],bark[1],3)
        stroke(img,[(mid,root-2),(mid+sign*6,root+2),(mid+sign*(w//2-4),h-4)],bark[3],1)
    if sick:
        # Some clinging diseased foliage; splintered branches still read below.
        for sign in (-1,1):
            pts=[(mid,h-24),(mid+sign*7,h-33),(mid+sign*13,h-37),(mid+sign*11,h-43)]
            stroke(img,pts,bark[1],3); stroke(img,pts,bark[3],1)
        for i,(x,y,rx,ry) in enumerate([] if species=='dead' else blobs[:3]):
            leaf_cluster(img,x,y,rx*.65,ry*.65,291+i,sick=True)
        if species=='dead':
            for pts in ([(mid,h-22),(mid-3,h-34),(mid-2,h-44),(mid-5,h-47)],
                        [(mid-3,h-34),(mid-11,h-38),(mid-14,h-36)],
                        [(mid+3,h-29),(mid+11,h-33),(mid+14,h-41)],
                        [(mid+10,h-34),(mid+5,h-38),(mid+7,h-44)]):
                stroke(img,pts,bark[1],3);stroke(img,pts,bark[3],1)
        for x,y in ((mid-2,h-20),(mid+5,h-33),(mid-9,h-31)):
            stroke(img,[(x,y-2),(x-1,y+2),(x+1,y+4)],W.ID['mag_d'],2)
            img[y,x]=W.ID['mag_l']
    else:
        for i,(x,y,rx,ry) in enumerate(blobs):
            leaf_cluster(img,x+variant*(1 if i%2 else -1),y,rx,ry,71+i*29+variant)
        if lantern:
            x=mid-10;y=h-26
            stroke(img,[(x,y-3),(x,y+4)],W.ID['bark_dk'])
            img[y:y+5,x-1:x+2]=W.ID['amber'];img[y+1:y+4,x]=W.ID['glow']
    return [img[y:y+16,x:x+16].copy() for y in range(0,h,16) for x in range(0,w,16)]


def rotten(seed=0, glow=False):
    """Bruised earth with sparse, branching veins; no all-over neon fill."""
    r=P.rng(seed+321)
    img=np.full((16,16),W.ID['v_1'],np.uint8)
    for x,y in P.scatter(seed+17,10,mind=3):
        img[y,x]=W.ID['v_0' if (x+y)%2 else 'v_2']
        if x<15: img[y,x+1]=W.ID['v_2']
    for x,y in P.scatter(seed+58, 1 if seed%3 else 2, mind=8):
        for k in range(3+seed%4):
            xx=(x+k//2)%16; yy=(y+k)%16
            img[yy,xx]=W.ID['v_3']
            if k%3==0: img[yy,(xx+1)%16]=W.ID['mag_d']
        if glow: img[y,x]=W.ID['mag_l']
    return img


def crystal(seed=0):
    img=rotten(seed)
    for cx,top,wide in ((4,6,3),(9,1,4),(13,8,2)):
        for y in range(top,14):
            radius=min(wide,(y-top)//2+1, max(1,(16-y)//2))
            for x in range(cx-radius,cx+radius+1):
                if 0<=x<16:
                    img[y,x]=W.ID['v_0' if x>cx else 'mag_d' if x==cx else 'mag']
            if y<top+7: img[y,max(0,cx-radius)]=W.ID['mag_l']
    return img


def masonry(seed=0, lit=False):
    img=np.full((16,16),W.ID['v_0'],np.uint8)
    for y in range(16):
        shift=4 if y//7%2 else 0
        for x in range(16):
            if y%7==0 or (x+shift)%8==0: continue
            img[y,x]=W.ID['v_3' if y%7==1 else 'v_1' if y%7==6 else 'v_2']
    # Violet rot in the joints rather than recoloured healthy leaves.
    for y in range(4,16):
        x=(seed*5+y//3)%16
        img[y,x]=W.ID['mag_d']
        if lit and y%4==0: img[y,x]=W.ID['mag_l']
    img[0:2,:]=W.ID['sick_d']
    return img


def forest_prop(kind):
    sick=kind.startswith('sick_')
    img=rotten(4) if sick else woodland_grass(1)
    if kind=='leaf_litter':
        for x,y in ((2,5),(9,3),(12,11),(5,12)):
            P.stamp(img,x,y,['.t.','tmd','.d.'],
                    dict(t=W.ID['trail_l'],m=W.ID['trail_d'],d=W.ID['grass_d']),wrap=True)
    elif kind=='fern_patch':
        for x,y in ((4,11),(11,12)):
            stroke(img,[(x,y),(x+1,y-7)],W.ID['grass_b'])
            for k in range(4):
                stroke(img,[(x-3+k//2,y-k*2),(x,y-k*2+1),(x+3-k//2,y-k*2-1)],W.ID['grass_l'])
    elif kind=='sick_bones':
        for x,y in ((2,5),(10,10)):
            stroke(img,[(x,y),(x+3,y+3)],W.ID['bt_l'],2)
            img[y,x]=W.ID['sick_l'];img[y+3,x+3]=W.ID['sick_l']
        img[8:11,6:9]=W.ID['bt_d'];img[8,6:9]=W.ID['sick_l'];img[9,6]=W.ID['bt_o'];img[9,8]=W.ID['bt_o']
    elif kind=='sick_stump':
        body=P.disc(16,16,8,10,5,4)
        img[body]=W.ID['bt_d']
        img[body & (np.indices((16,16))[1]<6)]=W.ID['bt_l']
        img[5:8,4:12]=W.ID['bt_m'];img[5,5:11]=W.ID['bt_l']
        stroke(img,[(8,5),(7,8),(9,10)],W.ID['mag_d'])
        img[7,7]=W.ID['mag_l']
        stroke(img,[(4,11),(1,14)],W.ID['bt_d'],2);stroke(img,[(11,11),(14,14)],W.ID['bt_m'],2)
    elif kind=='sick_rock':
        body=P.disc(16,16,8,9,6,5)
        img[body]=W.ID['bt_d'];img[body & (np.indices((16,16))[1]<7)]=W.ID['bt_l']
        stroke(img,[(6,6),(10,6),(12,8)],W.ID['sick_l'])
        stroke(img,[(8,5),(7,8),(9,10),(8,13)],W.ID['bt_o'])
        img[11,8]=W.ID['mag_d']
    return img


def barrier(kind):
    """The three tools have a repeatable visual language on every barrier."""
    img=np.full((16,16),W.ID['outline'],np.uint8)
    if kind=='crack':
        yy,xx=np.mgrid[0:16,0:16]
        img[:]=W.ID['stone_1']
        for y in range(16):
            for x in range(16):
                if y%6==0 or (x+(y//6%2)*4)%8==0: img[y,x]=W.ID['stone_0']
                elif y%6==1: img[y,x]=W.ID['stone_3']
                elif y%6==5: img[y,x]=W.ID['stone_1']
                else: img[y,x]=W.ID['stone_2']
        # A jagged ochre fracture is not a decorative random crack.
        pts=[(8,1),(6,4),(9,7),(6,10),(8,14)]
        stroke(img,pts,W.ID['outline'],3)
        stroke(img,pts,W.ID['yellow'])
        img[7,9]=W.ID['gold_l']
        stroke(img,[(5,14),(2,15)],W.ID['stone_0'],2)
    elif kind=='web':
        img[:]=W.ID['shadow']
        # Tree-root frame and layered silk; a small amber cocoon at its heart.
        for x in (1,13): stroke(img,[(x,0),(x+1,7),(x,15)],W.ID['bark_dk'],2)
        for x,y in ((1,1),(8,0),(15,2),(15,8),(13,15),(8,15),(0,14),(0,7)):
            stroke(img,[(x,y),(8,8)],W.ID['silk'])
        for r in (3,6):
            pts=[(8-r,8-r),(8,8-r-1),(8+r,8-r),(8+r+1,8),(8+r,8+r),(8,8+r+1),(8-r,8+r),(8-r-1,8),(8-r,8-r)]
            stroke(img,pts,W.ID['silk'])
        img[7:9,7:9]=W.ID['yellow'];img[7,7]=W.ID['gold_l']
    else:
        img[:]=W.ID['outline']
        img[1,:]=W.ID['stone_0'];img[0,:]=W.ID['stone_2']
        img[2,1:6]=W.ID['stone_1'];img[2,10:15]=W.ID['stone_1']
        img[14,3:8]=W.ID['shadow'];img[15,9:14]=W.ID['shadow']
    return img


def event_object(kind):
    """Ceramic, gilt wood and worn stone, on transparent room overlays."""
    from px import Canvas
    c = Canvas(16,16,0)
    stone=W.ID['stone_2']; light=W.ID['stone_3']; dark=W.ID['stone_0']
    gold=W.ID['yellow']; ivory=W.ID['gold_l']
    if kind.startswith('chest'):
        img=W.chest(kind.endswith('open'))
        remove=set(W.C('grass_d','grass_m','grass_l','grass_b','grass_t','shadow'))
        return np.where(np.isin(img,list(remove)),0,img).astype(np.uint8)
    if kind=='pot':
        c.ellipse(8,10,5,5,dark); c.ellipse(7,9,4,4,stone)
        c.hline(4,10,5,light); c.hline(5,10,4,dark)
        c.hline(5,10,6,gold); c.hline(4,10,12,gold)
        c.vline(5,8,10,light); c.set(6,7,ivory)
        c.hline(5,10,14,dark)
    elif kind.startswith('plate'):
        c.rect(2,5,13,13,dark); c.rect(3,5,12,11,stone)
        c.hline(3,12,5,light); c.vline(3,6,10,light)
        c.rect(6,7,9,9,gold if kind.endswith('down') else dark)
        c.set(7,7,ivory if kind.endswith('down') else light)
    return np.asarray(c.g,np.uint8)


def build():
    # Build using the existing native-resolution drawing vocabulary, replacing
    # the pack's flattened cut-outs with ground/face/crown-aware metatiles.
    grass_before,water_before=W.grass,W.water
    rot_depth_before=W.ROT_D
    W.ROT_D=8.5
    W.grass,W.water=woodland_grass,flowing_water
    try:
        T={n:(g,[a.copy() for a in frames],speed) for n,(g,frames,speed) in W.tiles().items()}
    finally:
        W.grass,W.water=grass_before,water_before
        W.ROT_D=rot_depth_before
    # The middle wood decays through grass/bruise edge families, rather than
    # isolated hard-edged purple squares or a grey earth substitute.
    decay={W.ID['earth_2']:W.ID['v_1'], W.ID['earth_3']:W.ID['v_2'],
           W.ID['earth_4']:W.ID['v_3'], W.ID['earth_5']:W.ID['v_4'],
           W.ID['earth_6']:W.ID['mag_d']}
    for n,(g,frames,speed) in list(T.items()):
        if n.startswith('rot_'):
            painted=[]
            for frame in frames:
                a=frame.copy()
                for src,dst in decay.items(): a[frame==src]=dst
                painted.append(a)
            T[n]=('wood_sick',painted,speed)
    for i in range(3): T['moss%d'%i]=('wood_grass',[woodland_grass(i,3)],None)
    for n,i in (('canopy',0),('canopy2',1),('canopy_glint',2)):
        T[n]=('wood_leaf',[canopy(i)],None)
    T['canopy_s']=('wood_leaf',[canopy_face()],None)
    # Reuse the painter's silhouette-specific faces with the new leaf texture.
    for prefix,parts in (('tree',tree()),('tree2',tree(lantern=True,variant=1)),
                         ('gtree',tree(3)),('gtree2',tree(3,True,variant=1))):
        names=['tree_top_nw','tree_top_ne','tree_mid_w','tree_mid_e','tree_trunk_w','tree_trunk_e'] if prefix=='tree' else ['%s_%d'%(prefix,i) for i in range(len(parts))]
        for i,(n,a) in enumerate(zip(names,parts)):
            T[n]=('wood_tree',[a],None)
    for i,a in enumerate(tree(sick=True,species='dead')):
        T['btree_%d'%i]=('wood_blight',[a],None)
    for name,parts,sick in (('birch',tree(species='birch'),False),
                            ('fir',tree(species='fir'),False),
                            ('sicktree',tree(sick=True,variant=1),True)):
        for i,a in enumerate(parts): T['%s_%d'%(name,i)]=('wood_blight' if sick else 'wood_tree',[a],None)

    for n,seed in (('blight_floor',0),('blight_floor2',1)):
        T[n]=('wood_deep',[rotten(seed,n.endswith('2'))],None)
    # A violet dirt trail remains visibly walkable against the bruised turf.
    T['blight_vein']=('wood_deep',[np.where(W.trail(0)==W.ID['trail_d'],W.ID['v_2'],W.ID['v_3']).astype(np.uint8)],None)
    for i in range(8):
        T['forest_rot%d'%i]=('wood_deep',[rotten(i+2,i==7)],None)
    for i in range(6):
        T['forest_canopy%d'%i]=('wood_leaf',[canopy(i)],None)
    T['blight_crystal']=('wood_blight',[crystal()],None)
    for n,seed in (('blight_wall',0),('blight_wall2',1),('blight_wall_lit',2)):
        T[n]=('wood_blight',[masonry(seed,seed==2)],None)
    for n,i in (('canopy_blight',0),('canopy_blight2',1)):
        T[n]=('wood_blight',[canopy(i,True)],None)
    for kind in ('leaf_litter','fern_patch','sick_bones','sick_stump','sick_rock'):
        T[kind]=('wood_blight' if kind.startswith('sick_') else 'wood_grass',[forest_prop(kind)],None)
    for kind in ('crack','web','pit'):
        T[kind]=('wood_gate',[barrier(kind)],None)
    for n,kind in (('myst_pot','pot'),('myst_switch','plate'),('myst_switch_down','plate_down'),
                   ('myst_chest','chest'),('myst_chest_open','chest_open')):
        T[n]=('wood_stone',[event_object(kind)],None)
    return T


# Decorative objects are material layers, never a replacement patch of grass.
# Compare before palette quantization so a shared foreground colour is kept
# unless the painter left the exact substrate pixel unchanged.
PROP_NAMES=set()

def remove_substrates(T):
    bases={}
    plain=woodland_grass(0)
    for n in ('bush','bones','rock_small','boulder','rock','rock2','rock3','stump','log',
              'pillar','ruin_wall','statue','lantern_post','thorn','mossy_stone',
              'chest','chest_open','torch','torch_lit'):
        bases[n]=plain
    for prefix, seeds in (('gboulder',(0,1,2,0)),('treerock',(1,0,0,2)),('hlog',(0,1))):
        for i,seed in enumerate(seeds): bases['%s_%d'%(prefix,i)]=woodland_grass(seed)
    for prefix in ('tree2','birch','fir'):
        for i in range(2):bases['%s_%d'%(prefix,4+i)]=woodland_grass(i)
    for i,n in enumerate(('tree_trunk_w','tree_trunk_e')):bases[n]=woodland_grass(i)
    for prefix in ('gtree','gtree2'):
        for i in range(3):bases['%s_%d'%(prefix,9+i)]=woodland_grass(i%3)
    for prefix,variant in (('btree',0),('sicktree',1)):
        for i in range(2):bases['%s_%d'%(prefix,4+i)]=rotten(variant)
    for n in ('leaf_litter','fern_patch'):bases[n]=woodland_grass(1)
    for n in ('sick_bones','sick_stump','sick_rock'):bases[n]=rotten(4)
    for style in ('cave','hollow','thicket'):
        bases[style+'_prop']=woodland_grass(0) if style=='thicket' else W.myst_floor(style,5)
    for n,base in bases.items():
        if n not in T:continue
        g,frames,speed=T[n]
        T[n]=(g,[np.where(a==base,0,a).astype(np.uint8) for a in frames],speed)
        PROP_NAMES.add(n)
    return T

TILES=remove_substrates(build())
# The painter uses named global inks; compress each material to its own 15.
# Nearest-colour conversion is confined to build-time, never the GBA runtime.
GROUPS={}
ORDERS={}
for n,(g,frames,speed) in TILES.items():
    ORDERS.setdefault(g,set()).update(int(v) for a in frames for v in np.unique(a) if v)
# Trees combine grass, bark and foliage. Quantize those to the shared leaf ramp.
for g,used in ORDERS.items():
    if len(used)>15:
        priority=['outline','leaf_deep','shadow','leaf_mid','leaf_lt','leaf_br','leaf_hl','bark_dk','bark','bark_l','bark_ll','grass_m','white','amber','glow'] if g=='wood_tree' else ['bt_o','bt_d','bt_m','bt_l','bt_g','v_0','v_1','v_2','v_3','mag_d','mag','mag_l','sick_d','bark','sick_l']
        order=[W.ID[n] for n in priority] if g in ('wood_tree', 'wood_blight') else W.build()[1][g][:15]
    else: order=sorted(used)
    GROUPS[PREFIX+g]=['#000000']+[HEX[i] for i in order]+['#000000']*(15-len(order))
    ORDERS[g]=order


def rgb(h): return tuple(int(h[i:i+2],16) for i in (1,3,5))


def closest(h, pal):
    c=rgb(h)
    return min(range(1,16),key=lambda i:sum((c[j]-rgb(pal[i])[j])**2 for j in range(3)))


def apply(metatiles, palettes):
    """Replace forest and its interiors only; retain metatile ids/physics."""
    for m in metatiles:
        n=m['name']
        if n.startswith(('sw_','swh_')): continue
        if n in PROP_NAMES: m['prop']=True
        if n in TILES:
            g,frames,speed=TILES[n]; pal=GROUPS[PREFIX+g]
            lut={v:closest(HEX[v],pal) for a in frames for v in np.unique(a) if v}
            rows=[[''.join('%x'%lut[int(v)] if v else '0' for v in row) for row in a] for a in frames]
            m['pal']=PREFIX+g
            m.pop('qpals',None)
            m.pop('art',None); m.pop('frames',None)
            if len(rows)>1: m['frames']=rows; m['anim_speed']=speed or 16
            else: m['art']=rows[0]
        else:
            # Remaining legacy pieces (including room event overlays) are
            # recoloured into their area's authored material, without adding
            # hardware palette slots. Their alpha and footprint are retained.
            g='myst_cave' if n.startswith(('cave_','myst_')) else 'myst_hollow' if n.startswith('hollow_') else 'wood_leaf' if n.startswith('thicket_') else 'wood_blight' if n.startswith('btree_') else 'wood_grass'
            pal=GROUPS[PREFIX+g]; old=palettes[m['pal']]
            lut={0:0,**{i:closest(old[i],pal) for i in range(1,16)}}
            for key in ('art','frames'):
                if key in m:
                    def mapped(rs): return [''.join('%x'%lut[int(ch,16)] if ch not in '. ' else '0' for ch in r) for r in rs]
                    m[key]=mapped(m[key]) if key=='art' else [mapped(a) for a in m[key]]
            m['pal']=PREFIX+g
