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
    grass_d='#305038', grass_m='#486040', grass_l='#587848', grass_b='#789848', grass_t='#b0c870',
    soil='#302820', trail_d='#685038', trail_m='#987848', trail_l='#b89860', trail_h='#d8c088',
    bark_dk='#201c20', bark='#503828', bark_l='#806040', bark_ll='#b09050', wood_cut='#d0b070',
    white='#e8e8c8', yellow='#e8c060', blue='#78c0d8', amber='#c88830', glow='#ffe0a0', gold_l='#fff0b8',
    water_deep='#081c38', water_dk='#103850', water_md='#185068', water_mid='#206880',
    water_lt='#388898', ripple='#70b8c8', foam='#c0e8e0',
    stone_0='#202830', stone_1='#384048', stone_2='#586058', stone_3='#808878', stone_4='#b0b898',
    v_0='#180c30', v_1='#281840', v_2='#402050', v_3='#583068', v_4='#804088',
    mag_d='#702090', mag='#b038d8', mag_l='#f088f8',
    sick_d='#283c38', sick_m='#485040', sick_l='#686850',
    bt_o='#100c20', bt_d='#302038', bt_m='#503048', bt_l='#805068', bt_g='#d860e8',
    earth_0='#182030', earth_1='#283040', earth_2='#384048', earth_3='#505858',
    earth_4='#686868', earth_5='#888080', earth_6='#a8a098',
    bl_deep='#101830', bl_dk='#182838', bl_md='#283848', bl_mid='#404850',
    bl_lt='#586858', bl_br='#788060', bl_hl='#a0a078',
    cave_glow='#58b8d0', cave_glow_l='#c0f0e8', thorn='#b050a0', thorn_vine='#302038')
HEX = {i: INKS.get(n, h) for i, (n, h) in enumerate(W.COLORS, 1)}
PREFIX = 'glade_'


def leaf_cluster(img, cx, cy, rx, ry, seed, sick=False, wrap=False):
    """Overlapping pointed leaves; light occupies one side of the crown."""
    rng = P.rng(seed)
    h, w = img.shape
    ramp = W.C('outline', 'leaf_deep', 'shadow', 'leaf_mid', 'leaf_lt', 'leaf_br', 'leaf_hl')
    if sick:
        ramp = W.C('bt_o', 'v_0', 'v_1', 'v_2', 'v_3', 'mag_d', 'mag')
    # Broad overlapping volumes first; small leaf strokes are accents.
    P.clump(img, cx, cy, rx, ramp[1:6], wrap=wrap, rough=0.14, seed=seed)
    mask = P.disc(w, h, cx, cy, rx * 0.85, ry * 0.85, wrap=wrap)
    for i in range(5):
        x=int(cx-rx*.65+rng.rand()*rx*1.2)
        y=int(cy-ry*.65+rng.rand()*ry*1.1)
        P.stamp(img,x,y,['.h','lm'],dict(h=ramp[5],l=ramp[4],m=ramp[3]),wrap=wrap,mask=mask)
    return img


def canopy(seed=0, sick=False):
    img = np.full((16, 16), W.ID['v_0' if sick else 'leaf_deep'], np.uint8)
    for i, (x,y,rx,ry) in enumerate(((2,3,7,5), (12,2,6,5), (6,11,7,5), (15,12,6,6))):
        leaf_cluster(img,x,y,rx,ry,seed*31+i,sick,True)
    return img


def tree(cols=2, lantern=False, sick=False, variant=0):
    w, h = cols*16, (cols+1)*16
    crown_h = h-16
    img = np.zeros((h,w), np.uint8)
    # Ground-contact roots are opaque; the rest can overlap the floor.
    for x in range(cols):
        img[-16:,x*16:x*16+16] = W.grass(x%3) if not sick else rotten(0)
    bark = W.C('outline','bark_dk','bark','bark_l','bark_ll') if not sick else W.C('bt_o','bt_d','bt_m','bt_l','bt_g')
    mid=w//2
    for yy in range(h-28,h-4):
        radius = 3 + max(0,yy-(h-12))//2
        for xx in range(mid-radius,mid+radius+1):
            img[yy,xx] = bark[1 if xx>mid+1 else 3 if xx<mid-1 else 2]
        if yy%6!=0: img[yy,mid-1]=bark[4 if sick else 1]
    # Splayed roots and long branches give the tree a recognisable silhouette.
    for sign in (-1,1):
        for k in range(12 if cols==3 else 8):
            x=mid+sign*k; y=h-8+k//3
            img[y:y+2,x]=bark[2]; img[y,x]=bark[3]
    if sick:
        # Dead thorned branches, a wound like a tarnished reliquary.
        for sign in (-1,1):
            for k in range(mid-2):
                x=mid+sign*k; y=crown_h-5-k
                img[y:y+3,x]=bark[2]
                img[y,x]=bark[3]
                if k%4==0: img[max(0,y-3):y,x]=bark[1]
        img[h-22:h-15,mid-2:mid+3]=W.ID['v_0']
        img[h-21:h-16,mid-1:mid+2]=W.ID['mag_d']
        img[h-20:h-17,mid:mid+1]=W.ID['mag_l']
    else:
        blobs = [(mid,9,mid*.56,8), (mid-7,16,mid*.53,8), (mid+7,18,mid*.5,8),
                 (mid,25,mid*.7,8)]
        if cols==3: blobs += [(10,29,9,9),(37,30,10,9),(24,38,14,8)]
        for i,(x,y,rx,ry) in enumerate(blobs):
            leaf_cluster(img,x+(variant if i%2 else -variant),y,rx,ry,71+i*11+variant)
        if lantern:
            y=crown_h-8; x=mid-9
            img[y:y+8,x:x+3]=W.ID['bark_dk']
            img[y+2:y+6,x+1]=W.ID['glow']
            img[y+6,x:x+3]=W.ID['amber']
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
    T={n:(g,[a.copy() for a in frames],speed) for n,(g,frames,speed) in W.tiles().items()}
    for i in range(3): T['moss%d'%i]=('wood_grass',[W.grass(i,3)],None)
    for n,i in (('canopy',0),('canopy2',1),('canopy_glint',2)):
        T[n]=('wood_leaf',[canopy(i)],None)
    # Reuse the painter's silhouette-specific faces with the new leaf texture.
    for prefix,parts in (('tree',tree()),('tree2',tree(lantern=True,variant=1)),
                         ('gtree',tree(3)),('gtree2',tree(3,True,variant=1))):
        names=['tree_top_nw','tree_top_ne','tree_mid_w','tree_mid_e','tree_trunk_w','tree_trunk_e'] if prefix=='tree' else ['%s_%d'%(prefix,i) for i in range(len(parts))]
        for i,(n,a) in enumerate(zip(names,parts)):
            T[n]=('wood_tree',[a],None)
    for i,a in enumerate(tree(sick=True)):
        T['btree_%d'%i]=('wood_blight',[a],None)
    for n,seed in (('blight_floor',0),('blight_floor2',1)):
        T[n]=('wood_deep',[rotten(seed,n.endswith('2'))],None)
    # A violet dirt trail remains visibly walkable against the bruised turf.
    T['blight_vein']=('wood_deep',[np.where(W.trail(0)==W.ID['trail_d'],W.ID['v_2'],W.ID['v_3']).astype(np.uint8)],None)
    for i in range(8):
        T['forest_rot%d'%i]=('wood_deep',[rotten(i+2,i==7)],None)
    for i in range(6):
        T['forest_canopy%d'%i]=('wood_leaf',[canopy(i+3)],None)
    T['blight_crystal']=('wood_blight',[crystal()],None)
    for n,seed in (('blight_wall',0),('blight_wall2',1),('blight_wall_lit',2)):
        T[n]=('wood_blight',[masonry(seed,seed==2)],None)
    for n,i in (('canopy_blight',0),('canopy_blight2',1)):
        T[n]=('wood_blight',[canopy(i,True)],None)
    for n,kind in (('myst_pot','pot'),('myst_switch','plate'),('myst_switch_down','plate_down'),
                   ('myst_chest','chest'),('myst_chest_open','chest_open')):
        T[n]=('wood_stone',[event_object(kind)],None)
    return T


TILES=build()
# The painter uses named global inks; compress each material to its own 15.
# Nearest-colour conversion is confined to build-time, never the GBA runtime.
GROUPS={}
ORDERS={}
for n,(g,frames,speed) in TILES.items():
    ORDERS.setdefault(g,set()).update(int(v) for a in frames for v in np.unique(a) if v)
# Trees combine grass, bark and foliage. Quantize those to the shared leaf ramp.
for g,used in ORDERS.items():
    if len(used)>15:
        priority=['outline','leaf_deep','shadow','leaf_mid','leaf_lt','leaf_br','leaf_hl','bark_dk','bark','bark_l','bark_ll','grass_m','grass_l','amber','glow'] if g=='wood_tree' else ['bt_o','bt_d','bt_m','bt_l','bt_g','v_0','v_1','v_2','v_3','mag_d','mag','mag_l','sick_d','bark','sick_l']
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
