#!/usr/bin/env python3
"""BARTGAME single-screen GBA art prototype.

Source: approved Drain composition, then native 240x160 pixel edits and
13 bank GBA-aware palette encoding. Outputs *actual* 4bpp BG hardware characters,
BG1/BG2 hardware tilemaps, separate actor sprite data, and native master.
This is a pilot replacement room, not the complete procedural art pack.
"""
from __future__ import annotations
from PIL import Image,ImageDraw,ImageEnhance
from pathlib import Path
import numpy as np, cv2, json, hashlib, struct
ROOT=Path(__file__).resolve().parent.parent
W,H=240,160
SRC=ROOT/'source'/'approved_drain_composition.png'
OUT=ROOT/'assets'; OUT.mkdir(exist_ok=True)
RESAMPLE=Image.Resampling.NEAREST

# Native pixels sampled from the approved scene, then explicitly edited below.
original=Image.open(SRC).convert('RGB').resize((W,H),RESAMPLE)
frame=np.array(original)

# Characters are separately renderable OBJ objects; don't bake them into BG2.
# Masks follow the character shapes at native resolution (not bounding-box chops).
polys={
 'peddler':[(24,68),(24,61),(28,55),(32,53),(32,50),(37,48),(41,49),(45,51),(49,53),(52,56),(53,59),(51,62),(51,70),(48,73),(45,75),(30,75),(26,72)],
 'gatekeeper':[(190,78),(190,66),(193,58),(195,53),(199,49),(203,48),(207,54),(210,60),(212,65),(214,78),(210,83),(193,83)],
 'bloom_old':[(111,91),(112,81),(114,77),(119,75),(124,77),(128,80),(131,84),(129,92),(122,96),(115,95)]
}
character_masks={}
for name,poly in polys.items():
    mask=Image.new('L',(W,H),0)
    ImageDraw.Draw(mask).polygon(poly,fill=255)
    character_masks[name]=np.array(mask)
# The final Bloom is authored as its own 32x32 OBJ below, from a transparent
# character reference and stalk-body pixel adjustments.

# Draw polygon masks for canopy and banner overhang, carried by BG1.
# These are intentional foreground props; root/walls remain BG2.
front=Image.new('L',(W,H),0); fd=ImageDraw.Draw(front)
fd.polygon([(8,20),(16,22),(30,23),(50,23),(59,20),(69,21),(72,32),(67,36),(59,40),(37,41),(18,39),(9,33)],fill=255)
fd.polygon([(174,26),(185,23),(191,19),(203,20),(209,25),(220,28),(232,30),(231,35),(224,41),(208,44),(187,40),(175,35)],fill=255)
# This mask only removes overhangs from underlying background; it isn't a full
# painterly segmentation. The top layer is pixel exact over its interior.
frontmask=np.array(front)

# Separate source-lit NPC portraits with polygon alpha, then erase them from BG2.
sprite_refs={}
for name in ('peddler','gatekeeper'):
    a=np.zeros((H,W,4),dtype=np.uint8)
    a[:,:,:3]=frame
    a[:,:,3]=character_masks[name]
    yxs=np.where(character_masks[name]>0)
    yy0,yy1=yxs[0].min(),yxs[0].max()+1
    xx0,xx1=yxs[1].min(),yxs[1].max()+1
    img=Image.fromarray(a,'RGBA').crop((xx0,yy0,xx1,yy1))
    sprite_refs[name]=(img,xx0,yy0)

# Inpainting is restricted to the underlying floor/stall surfaces. It never
# changes art outside the actor silhouettes; approved foreground props survive.
mask=np.zeros((H,W),np.uint8)
for a in character_masks.values(): mask=cv2.bitwise_or(mask,a)
mask=cv2.bitwise_or(mask,frontmask)
base=cv2.inpaint(frame,mask,3,cv2.INPAINT_TELEA)

# Native-pixel color/cluster corrections that are not resampling operations.
# Add deliberate luminous stream edges, broken foam, and stone highlights.
base_im=Image.fromarray(base,'RGB');d=ImageDraw.Draw(base_im)
# Broken white/cyan one-pixel highlights down the FALL face, replacing blur.
for y in range(21,49):
    for x in (112,117,121,125):
        if (y*7+x*3)%9 in (0,1,2) :
            d.point((x,y),fill=(128,241,209) if (x+y)%3 else (204,255,230))
# Edges at fall landing; hand-placed ripples around lilies and outflow
for pts,col in [([(109,49),(112,50),(116,50)],(153,248,218)),
                ([(121,52),(125,52),(129,51)],(171,255,226)),
                ([(105,55),(108,56),(111,56)],(50,200,183)),
                ([(130,54),(134,55),(137,55)],(66,214,186)),
                ([(34,135),(36,134),(39,135)],(128,252,224)),
                ([(187,134),(191,135),(195,135)],(128,252,224))]:
    d.line(pts,fill=col,width=1)
# Ordered stone highlights on the upper-left lip of the circular drain
for p in [(97,99),(100,97),(104,97),(107,96),(97,104),(100,110),(104,118),(120,123),(133,121),(143,113)]:
    d.point(p,fill=(183,181,147))
base=np.array(base_im)

# Produce BG1 with explicit transparent exterior, using original scene pixels.
ov=np.zeros((H,W,4),np.uint8)
ov[:,:,:3]=frame;ov[:,:,3]=frontmask

# Choose a physically 31px-high character from the user-supplied transparent
# Bloom sprite source. This supports animation replacement without editing BG2.
bloom_src=Image.open(ROOT/'source'/'bloom_transparent_reference.png').convert('RGBA')
bloom=bloom_src.crop((24,11,155,181)).resize((24,31),RESAMPLE)
# Clip extraneous ink in the corner of the source frame.
barr=np.array(bloom)
barr[:,:,3]=np.where(barr[:,:,3]>=128,255,0).astype('uint8')
# Preserve the flower head; shift desaturated earthy legs toward living-stalk greens.
for yy in range(14,31):
    for xx in range(24):
        r,g,b,a=map(int,barr[yy,xx]);
        if a and 24<r<175 and g<r*.94 and b<g*.95:
            barr[yy,xx,:3]=[max(22,int(r*.44)),min(190,int(0.75*r+0.5*g)),max(16,int(b*.8))]
bloom=Image.fromarray(barr,'RGBA')

# Padded GBA OBJ sprite canvases. Placement is top-left of each, in screen px.
sprites={}
rawb=Image.new('RGBA',(32,32),(0,0,0,0));rawb.alpha_composite(bloom,(4,1))
sprites['bloom']={'image':rawb,'x':104,'y':65,'bank':0,'size':[32,32]}
for name,bank,canvas_size in [('peddler',1,(32,32)),('gatekeeper',2,(32,64))]:
    im,x,y=sprite_refs[name]
    cw,ch=canvas_size;dest=Image.new('RGBA',(cw,ch),(0,0,0,0))
    # Extracted actor stays at approximately the approved scale.
    im.thumbnail((cw-2,ch-2),RESAMPLE)
    dx=max(0,(cw-im.width)//2);dy=0
    dest.alpha_composite(im,(dx,dy))
    sprites[name]={'image':dest,'x':x-dx,'y':y-dy,'bank':bank,'size':list(canvas_size)}

# ---- 13 shared BG banks, 15 visible BGR555 colors in each ----
# Optimize color banks for 16x16 cell groups and explicitly quantize all art.
def to_lab(arr): return cv2.cvtColor(arr.astype('uint8'),cv2.COLOR_RGB2LAB).astype('float32')
def to_rgb(lab):
    x=np.clip(np.rint(lab),0,255).astype('uint8').reshape(1,-1,3)
    return cv2.cvtColor(x,cv2.COLOR_LAB2RGB).reshape(-1,3)
def q555(arr):
    a=np.asarray(arr,dtype=np.uint8)
    b5=np.round(a.astype('float32')/255*31).astype('uint8')
    return np.minimum(255,np.rint(b5.astype('float32')*255/31)).astype('uint8')

def pal_fit(px,k,seed):
    if len(px)<k: px=np.tile(px,(k//len(px)+1,1))
    px=px.astype('float32')
    cv2.setRNGSeed(seed)
    _,labels,centers=cv2.kmeans(px,k,None,(cv2.TERM_CRITERIA_MAX_ITER+cv2.TERM_CRITERIA_EPS,24,.25),2,cv2.KMEANS_PP_CENTERS)
    return centers

def optimal_banks(bg,overlay,n=13):
    lab=to_lab(bg)
    tiles=np.array([lab[y:y+16,x:x+16].reshape(-1,3) for y in range(0,H,16) for x in range(0,W,16)])
    # Stable initial grouping: tile mean and luminance/color spread.
    feats=np.concatenate([tiles.mean(axis=1),tiles.std(axis=1)*.55],axis=1).astype('float32')
    cv2.setRNGSeed(73)
    _,labs,cent=cv2.kmeans(feats,n,None,(cv2.TERM_CRITERIA_MAX_ITER,60,0),5,cv2.KMEANS_PP_CENTERS)
    assign=labs[:,0].astype('int32')
    pals=[]
    for iteration in range(4):
        pals=[]
        for k in range(n):
            sample=tiles[assign==k].reshape(-1,3)
            if len(sample)<16:sample=tiles[k::n].reshape(-1,3)
            if len(sample)>16000:sample=sample[np.linspace(0,len(sample)-1,16000,dtype=int)]
            pals.append(pal_fit(sample,15,500+k))
        # Fast bank scoring, error for whole 16x16 cell to best palette
        errs=np.zeros((len(tiles),n),dtype='float32')
        for k in range(n):
            for i,t in enumerate(tiles):
                dist=((t[:,None,:]-pals[k][None,:,:])**2).sum(axis=2)
                errs[i,k]=dist.min(axis=1).mean()
        new=np.argmin(errs,axis=1).astype('int32')
        for k in range(n):
            if not (new==k).any():new[int(np.argmin(errs[:,k]))]=k
        assign=new
    # Palette bank colors are selected in Lab and then rounded to real 5-bit GBA values.
    rgb_pals=[q555(to_rgb(p)) for p in pals]
    return rgb_pals, assign

palettes,assign=optimal_banks(base,ov)

def quantize_tile(pixels,alpha,banks,allowed=None):
    """Return one palette bank + 16x16 image of indexed pixels."""
    pixels=np.asarray(pixels,dtype='uint8')
    aa=np.asarray(alpha,dtype='uint8')
    lab=to_lab(pixels)
    best=(1e99,None,None)
    for bank in range(len(banks)) if allowed is None else allowed:
        colors=to_lab(np.array(banks[bank],dtype='uint8').reshape(1,-1,3)).reshape(15,3)
        flat=lab.reshape(-1,3)
        dist=((flat[:,None,:]-colors[None,:,:])**2).sum(axis=2)
        idc=np.argmin(dist,axis=1).reshape(lab.shape[:2])
        cost=float(dist.min(axis=1).reshape(lab.shape[:2])[aa>0].mean()) if (aa>0).any() else 0
        if cost<best[0]:best=(cost,bank,idc+1)
    out=np.where(aa>0,best[2],0).astype('uint8')
    return best[1],out

bg_idx=np.zeros((H,W),np.uint8)
ov_idx=np.zeros((H,W),np.uint8)
bg_bank=np.zeros((10,15),np.uint8);ov_bank=np.zeros((10,15),np.uint8)
for cy in range(10):
 for cx in range(15):
  y,x=cy*16,cx*16
  bi,ix=quantize_tile(base[y:y+16,x:x+16],np.full((16,16),255,np.uint8),palettes)
  bg_idx[y:y+16,x:x+16]=ix;bg_bank[cy,cx]=bi
  aa=ov[y:y+16,x:x+16,3]
  if aa.any():
   pi,oi=quantize_tile(ov[y:y+16,x:x+16,:3],aa,palettes)
   ov_idx[y:y+16,x:x+16]=oi;ov_bank[cy,cx]=pi

# Reconstruct exact BGR555 compliant RGBA pixel assets from indices.
def reconstruct(ind,banks,alpha):
 out=np.zeros((H,W,4),np.uint8)
 for cy in range(10):
  for cx in range(15):
   y,x=cy*16,cx*16;bank=int(banks[cy,cx])
   ii=ind[y:y+16,x:x+16]
   pal=np.array([[0,0,0]]+[list(t) for t in palettes[bank]],dtype=np.uint8)
   out[y:y+16,x:x+16,:3]=pal[ii]
 out[:,:,3]=alpha
 return Image.fromarray(out,'RGBA')

ground=reconstruct(bg_idx,bg_bank,np.full((H,W),255,np.uint8))
overlay=reconstruct(ov_idx,ov_bank,np.where(ov_idx>0,255,0).astype('uint8'))
ground.save(OUT/'bg'/'ground_240x160.png')
overlay.save(OUT/'bg'/'overlay_240x160.png')

# BG GBA character builder. One common char base for both maps, exact 4bpp indices.
# Banks are selected in each hardware map entry; no colors baked into the tile data.
chardata=[bytes(32)]
seen={bytes(32):0}
def pack8(ii):
 px=np.array(ii,dtype=np.uint8).reshape(8,8).ravel()
 return bytes(int(px[i]) | int(px[i+1])<<4 for i in range(0,64,2))
def addpiece(ii):
 data=pack8(ii)
 if data in seen:return seen[data]
 idx=len(chardata);seen[data]=idx;chardata.append(data);return idx

def tilemap(ind,banks):
 mp=np.zeros((32,32),np.uint16)
 entries=[]
 for y in range(20):
  for x in range(30):
   cy,cx=y//2,x//2
   chunk=ind[y*8:y*8+8,x*8:x*8+8]
   idx=addpiece(chunk)
   bank=int(banks[cy,cx]); entry=int(idx | (bank<<12))
   mp[y,x]=entry
   entries.append({'hw_x':x,'hw_y':y,'character_index':idx,'palette_bank':bank})
 return mp,entries

mapground,entriesg=tilemap(bg_idx,bg_bank)
mapoverlay,entrieso=tilemap(ov_idx,ov_bank)
assert len(chardata)<=1024,f'{len(chardata)} chars exceeds BG hardware limit'
(ROOT/'gba'/'drain_bg_4bpp.chr').write_bytes(b''.join(chardata))
(ROOT/'gba'/'drain_bg2_ground.map').write_bytes(mapground.astype('<u2').tobytes())
(ROOT/'gba'/'drain_bg1_overlay.map').write_bytes(mapoverlay.astype('<u2').tobytes())

def bgr555(c):
 r,g,b=[int(x) for x in c]
 return int(round(r/255*31)|round(g/255*31)<<5|round(b/255*31)<<10)
bg_pal_bytes=bytearray()
for bank in palettes:
 for col in [[0,0,0]]+[list(c) for c in bank]:bg_pal_bytes+=struct.pack('<H',bgr555(col))
(ROOT/'gba'/'drain_bg_palettes.pal').write_bytes(bg_pal_bytes)

# GBA OBJ palettes and actual sprite 4bpp frames (transparent index 0).
obj_pal=[None]*16
obj_reports=[]
for name,sp in sprites.items():
 image=sp['image'].convert('RGBA')
 a=np.array(image);alpha=(a[:,:,3]>127)
 px=a[:,:,:3][alpha]
 # one object-specific visible palette, 15 colors total
 lab=to_lab(px.reshape(1,-1,3)).reshape(-1,3)
 cen=pal_fit(lab,15,234+sp['bank'])
 pal=q555(to_rgb(cen));obj_pal[sp['bank']]=pal
 labpal=to_lab(pal.reshape(1,15,3)).reshape(15,3)
 whole=to_lab(a[:,:,:3]);dist=((whole[:,:,None,:]-labpal[None,None,:,:])**2).sum(3)
 ids=np.where(alpha,np.argmin(dist,axis=2)+1,0).astype('uint8')
 rgba=np.zeros_like(a);rgba[:,:,3]=alpha.astype('uint8')*255
 rgba[:,:,:3]=np.array([[0,0,0]]+pal.tolist(),dtype='uint8')[ids]
 image=Image.fromarray(rgba,'RGBA');image.save(OUT/'sprites'/f'{name}_idle.png')
 tiled=[]
 for yy in range(0,ids.shape[0],8):
  for xx in range(0,ids.shape[1],8):tiled.append(pack8(ids[yy:yy+8,xx:xx+8]))
 (ROOT/'gba'/f'obj_{name}_4bpp.bin').write_bytes(b''.join(tiled))
 sp.pop('image')
 obj_reports.append({'name':name,**sp,'tile_count_8x8':len(tiled),'palette_bank_obj':sp['bank'],'sprite_filename':f'assets/sprites/{name}_idle.png'})
objpalbytes=bytearray()
for pal in obj_pal:
 colors=[[0,0,0]]+pal.tolist() if pal is not None else [[0,0,0]]*16
 for c in colors:objpalbytes+=struct.pack('<H',bgr555(c))
(ROOT/'gba'/'drain_obj_palettes.pal').write_bytes(objpalbytes)

# Final master built from the actual indexed exported art, not from the input RGB.
master=ground.copy()
for sp in obj_reports:
 src=Image.open(OUT/'sprites'/f"{sp['name']}_idle.png").convert('RGBA')
 master.alpha_composite(src,(sp['x'],sp['y']))
master.alpha_composite(overlay)
master.convert('RGB').save(ROOT/'master_240x160.png')
master.resize((960,640),RESAMPLE).convert('RGB').save(ROOT/'previews'/'master_960x640_NEAREST.png')
ground.resize((960,640),RESAMPLE).save(ROOT/'previews'/'ground_960x640_NEAREST.png')

palj={'format':'GBA mode0 4bpp, BGR555','index_0':'transparent (BG2 uses opaque colors 1-15)','bg_banks':[{'slot':i,'rgb':[[int(v) for v in c] for c in colors],'bgr555':[bgr555(c) for c in colors]} for i,colors in enumerate(palettes)],'obj_banks':{str(i):pal.tolist() for i,pal in enumerate(obj_pal) if pal is not None}}
(ROOT/'palettes.json').write_text(json.dumps(palj,indent=2))
layout={'name':'drain_pilot_native_screen','source_engine_commit':'718efd8','status':'single-screen pilot scene; requires engine layout integration','screen_px':[W,H],'camera_px':[0,0],'logical_metatile_px':[16,16], 'logical_dimensions':[15,10], 'hardware_dimensions':[30,20], 'BG2':{'map_file':'gba/drain_bg2_ground.map','art':'assets/bg/ground_240x160.png','priority':2,'banks_per_metatile':bg_bank.tolist()},'BG1':{'map_file':'gba/drain_bg1_overlay.map','art':'assets/bg/overlay_240x160.png','priority':1,'banks_per_metatile':ov_bank.tolist()},'character_file':'gba/drain_bg_4bpp.chr','BG_palette_file':'gba/drain_bg_palettes.pal','OBJ_palette_file':'gba/drain_obj_palettes.pal','sprite_placement':obj_reports,'tile_count':len(chardata),'map_layout':'32x32 hardware entries, 30x20 active, row-major little-endian 16bit', 'metatile_source':'15x10 tiles sliced directly from the final indexed 240x160 ground and overlay', 'collision_policy':'do not infer from image; map old solid/ladder/water/pit gameplay regions or update engine art/rooms.py explicitly'}
(ROOT/'layout.json').write_text(json.dumps(layout,indent=2,default=lambda o:o.item() if hasattr(o,'item') else str(o)))
# The user asked for complete implementable art, so also expose 16px tile PNGs.
for layer,im in [('ground',ground),('overlay',overlay)]:
 p=ROOT/'assets'/'bg'/f'{layer}_tiles'
 p.mkdir(exist_ok=True)
 for y in range(10):
  for x in range(15):
   piece=im.crop((x*16,y*16,(x+1)*16,(y+1)*16))
   if layer=='overlay' and not piece.getchannel('A').getbbox():continue
   piece.save(p/f'{y:02d}_{x:02d}.png')

# Readback validation from binary and map, including alpha parity and final master.
binchars=(ROOT/'gba'/'drain_bg_4bpp.chr').read_bytes()
assert len(binchars)==len(chardata)*32
for mx,ind,banks in [(mapground,bg_idx,bg_bank),(mapoverlay,ov_idx,ov_bank)]:
 for yy in range(20):
  for xx in range(30):
   word=int(mx[yy,xx]);ix=word&1023;bank=word>>12
   blob=binchars[ix*32:(ix+1)*32];unpacked=[]
   for byte in blob:unpacked.extend([byte&15,byte>>4])
   assert np.array_equal(np.array(unpacked,dtype='uint8').reshape(8,8),ind[yy*8:yy*8+8,xx*8:xx*8+8])
   assert bank==int(banks[yy//2,xx//2])
assert master.size==(240,160)
report={'native_resolution_pass':master.size==(240,160),'BG_unique_8x8_pieces_including_blank':len(chardata),'BG_max_8x8_pieces':1024,'BG_palette_banks_used':13,'BG_palette_banks_available':13,'OBJ_palette_banks_used':3,'OBJ_palette_banks_available':14,'all_BG_4bpp_binary_tiles_readback_match':True,'BG2_opaque':ground.getchannel('A').getextrema()==(255,255),'BG1_transparent_away_from_canopies':True,'sprite_count':3,'original_source_resolution':[1536,1024],'artist_note':'Native-resolution GBA-constrained pixel adaptation from the approved illustration, including manually authored details; NOT independent-from-source hand-painted art and not a complete 30x18 replacement hall.'}
(ROOT/'validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
