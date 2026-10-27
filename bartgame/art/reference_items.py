"""Import the user's item/shield screenshots without redrawing their designs.

The screenshots contain an opaque checkerboard. Neutral light matte pixels
are removed, including enclosed checkerboard holes and JPEG ringing near
an outline. Warm metal highlights and coloured glints remain foreground.
Native item pixels are sampled with NEAREST, then converted to RGB555.
Large menu icons retain an individual 15-colour palette. World art shares
four 15-colour material banks, matching the existing OBJ palette slots.
"""
from functools import lru_cache
from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ITEM_SOURCE = HERE / 'ref' / 'items-reference.jpg'
SHIELD_SOURCE = HERE / 'ref' / 'shields-reference.jpg'
ITEM_ORDER = ('none', 'bombs', 'lamp', 'cloak', 'key', 'heart_piece',
              'heart_container', 'gilt_big', 'relic', 'heart', 'gilt',
              'bomb_pickup', 'spark', 'grail', 'gauntlet', 'bow',
              'arrow1', 'arrow5', 'arrow10', 'hubcap')
# Cell bounds include each source figure and its detached intended glints.
ITEM_X = (0, 250, 470, 700, 930, 1179)
ITEM_Y = (0, 264, 477, 683, 922)
SHIELD_X = (0, 470, 705, 1179)
SHIELD_Y = (0, 360, 735)
BANK_NAMES = ('gear', 'items', 'pick', 'icons')
BANK_SAMPLES = {
    'gear': ('shield', 'shield_side', 'shield_back', 'gauntlet', 'hubcap', 'sword'),
    'items': ('bombs', 'bomb_pickup', 'lamp', 'relic'),
    'pick': ('heart_piece', 'heart_container', 'heart', 'gilt', 'gilt_big', 'spark', 'grail', 'astrolabe'),
    'icons': ('cloak', 'bow', 'arrow1', 'arrow5', 'arrow10', 'key', 'map', 'shield_upgraded'),
}
EXTRA_RGB = {
    'gear': ('#445468', '#91adb5', '#fff1cf', '#75503b', '#c18b50', '#ab7138', '#f4ce68'),
    'icons': ('#e5ce9e', '#fff1cf'),
}


def _components(mask):
    """Four-connected components; source glints are much larger than JPEG noise."""
    h,w = mask.shape
    seen = np.zeros_like(mask)
    for y,x in zip(*np.nonzero(mask)):
        if seen[y,x]:
            continue
        queue = [(y,x)]; seen[y,x] = True; result = []
        while queue:
            yy,xx = queue.pop(); result.append((yy,xx))
            for y2,x2 in ((yy-1,xx), (yy+1,xx), (yy,xx-1), (yy,xx+1)):
                if 0<=y2<h and 0<=x2<w and mask[y2,x2] and not seen[y2,x2]:
                    seen[y2,x2] = True; queue.append((y2,x2))
        yield result


def _unmatte(image):
    rgb = np.asarray(image.convert('RGB')).astype('int16')
    low = rgb.min(axis=2); spread = rgb.max(axis=2)-low
    light_gray = (low>=190) & (spread<=40)
    background = np.zeros_like(light_gray)
    h,w = light_gray.shape
    for component in _components(light_gray):
        yy,xx = np.asarray(component).T
        values = low[yy,xx]
        edge = yy.min()==0 or xx.min()==0 or yy.max()==h-1 or xx.max()==w-1
        # A genuine checkerboard hole contains both screenshot matte tones.
        checker = len(component)>=24 and (values<247).mean()>.12 and (values>249).mean()>.12
        if edge or checker:
            background[yy,xx] = True
    # Gray JPEG islands beside the silhouette are matte ringing, not item
    # highlights. Preserve enclosed hot highlights farther inside the item.
    near = np.asarray(Image.fromarray((background*255).astype('uint8')).filter(ImageFilter.MaxFilter(7)))>0
    background |= light_gray & near
    foreground = ~background
    for component in _components(foreground):
        if len(component)<10:
            yy,xx = np.asarray(component).T; foreground[yy,xx] = False
    rgba = np.concatenate((rgb.astype('uint8'), (foreground*255).astype('uint8')[...,None]),axis=2)
    result = Image.fromarray(rgba)
    bbox = result.getbbox()
    return result.crop(bbox) if bbox else Image.new('RGBA',(1,1))


def _canonical(name, variant=0):
    if name=='shield_front': name='shield'
    if name.startswith('shield_upgraded'):
        name = name.replace('shield_upgraded','shield',1)
        variant = 1
    if name.startswith('upgraded_'):
        name='shield' if name=='upgraded_front' else 'shield_'+name[9:]
        variant=1
    return name,variant


@lru_cache(maxsize=None)
def _source_figure(name,variant=0):
    name,variant = _canonical(name,variant)
    if name in ('shield','shield_side','shield_back'):
        col = ('shield','shield_side','shield_back').index(name)
        bounds = (SHIELD_X[col],SHIELD_Y[variant],SHIELD_X[col+1],SHIELD_Y[variant+1])
        with Image.open(SHIELD_SOURCE) as source:
            return _unmatte(source.crop(bounds))
    if name in ITEM_ORDER and name!='none':
        index=ITEM_ORDER.index(name);row,col=divmod(index,5)
        bounds=(ITEM_X[col],ITEM_Y[row],ITEM_X[col+1],ITEM_Y[row+1])
        with Image.open(ITEM_SOURCE) as source:
            return _unmatte(source.crop(bounds))
    if name=='none':
        return Image.new('RGBA',(1,1))
    if name=='bomb_lit':
        image = _source_figure('bomb_pickup').copy()
        a=np.asarray(image).copy(); r,g,b=a[:,:,:3].transpose(2,0,1).astype('int16')
        purple=(b>r*.9)&(b>g*1.3)&(a[:,:,3]>0)
        # The warning frame changes the live bomb's purple body to red;
        # its source shape, fuse and gold light stay intact.
        a[purple,0]=np.maximum(a[purple,0],a[purple,2])
        a[purple,2]=(a[purple,2].astype('uint16')*2//5).astype('uint8')
        return Image.fromarray(a)
    raise KeyError(name)


def _legacy(name,size):
    import clean_items
    rows=clean_items.make(name,size)
    pal=clean_items.PALETTE
    result=Image.new('RGBA',(size,size))
    for y,row in enumerate(rows):
        for x,ch in enumerate(row):
            if ch not in '.0 ':
                h=pal[int(ch,16)].lstrip('#')
                result.putpixel((x,y),tuple(int(h[i:i+2],16) for i in (0,2,4))+(255,))
    return result


@lru_cache(maxsize=None)
def _native(name,size=32,variant=0):
    name,variant=_canonical(name,variant)
    if name not in ITEM_ORDER and not name.startswith('shield') and name!='bomb_lit':
        return _legacy(name,size)
    source=_source_figure(name,variant)
    canvas=Image.new('RGBA',(size,size))
    if not source.getbbox():return canvas
    fit=size-2 if size<=16 else size-2
    scale=min(fit/source.width,fit/source.height)
    w,h=max(1,round(source.width*scale)),max(1,round(source.height*scale))
    source=source.resize((w,h),Image.Resampling.NEAREST)
    canvas.alpha_composite(source,((size-w)//2,(size-h)//2))
    return canvas


def native_image(name,size=32,variant=0):
    """Return original imported colours/alpha, padded to the requested square."""
    return _native(name,size,variant).copy()


def _rgb555_pixels(image):
    a=np.asarray(image.convert('RGBA'))
    return (a[:,:,:3][a[:,:,3]>0] & 248).reshape(-1,3)


def _palette(pixels):
    if len(pixels)==0:return ['#000000']*16
    image=Image.fromarray(np.asarray(pixels,dtype='uint8').reshape(1,-1,3))
    quant=image.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    raw=quant.getpalette();used=sorted(set(quant.tobytes()))
    colours=[]
    for i in used:
        c=tuple(v&248 for v in raw[i*3:i*3+3])
        if c not in colours:colours.append(c)
    # Stable dark-to-light order makes hand inspection of the banks easier.
    colours.sort(key=lambda c:(sum(c),c))
    out=['#000000']+['#%02x%02x%02x'%c for c in colours]
    return (out+['#000000']*16)[:16]


def _quantize(image,palette):
    rgba=np.asarray(image.convert('RGBA'))
    rgb=rgba[:,:,:3].astype('int32')
    pal=np.asarray([tuple(int(h[i:i+2],16) for i in (1,3,5)) for h in palette[1:]],dtype='int32')
    distance=((rgb[:,:,None,:]-pal[None,None,:,:])**2).sum(axis=3)
    ix=distance.argmin(axis=2)+1
    return [''.join('.' if rgba[y,x,3]==0 else '%x'%ix[y,x] for x in range(image.width))
            for y in range(image.height)]


@lru_cache(maxsize=None)
def _menu(name,variant=0):
    image=_native(name,32,variant)
    pal=_palette(_rgb555_pixels(image))
    return _quantize(image,pal),pal


def menu_frame(name,variant=0):
    rows,palette=_menu(name,variant)
    return list(rows),list(palette)


def frame_art(name,size=32,variant=0):
    """Per-frame palette art; menu_frame is the explicit native32 equivalent."""
    image=_native(name,size,variant)
    return _quantize(image,_palette(_rgb555_pixels(image)))


def frame_palette(name,size=32,variant=0):
    return _palette(_rgb555_pixels(_native(name,size,variant)))


def _make_banks():
    result={}
    for bank,names in BANK_SAMPLES.items():
        samples=[_rgb555_pixels(_native(n,32)) for n in names]
        # Retain the old blade/marker materials alongside the imported art.
        for h in EXTRA_RGB.get(bank,()):
            c=[int(h[i:i+2],16)&248 for i in (1,3,5)]
            samples.append(np.tile(np.asarray(c,dtype='uint8'),(32,1)))
        result[bank]=_palette(np.concatenate(samples,axis=0))
    return result


BANK_PALETTES=_make_banks()


def bank_for(name,variant=0):
    name,variant=_canonical(name,variant)
    if name.startswith('shield'):
        return 'icons' if variant else 'gear'
    if name=='bomb_lit':return 'pick'
    for bank,names in BANK_SAMPLES.items():
        if name in names:return bank
    if name=='none':return 'items'
    raise KeyError('No world bank for '+name)


def world_quantize(image,bank):
    return _quantize(image,BANK_PALETTES[bank])


def world_frame(name,size,variant=0):
    bank=bank_for(name,variant)
    return world_quantize(_native(name,size,variant),bank),bank


def _paint(rows,palette):
    im=Image.new('RGBA',(len(rows[0]),len(rows)))
    for y,row in enumerate(rows):
        for x,ch in enumerate(row):
            if ch!='.':
                h=palette[int(ch,16)].lstrip('#')
                c=tuple(int(h[i:i+2],16) for i in (0,2,4))
                im.putpixel((x,y),c+(255,))
    return im


def preview(path='/workspace/setup/reference-items-preview.png'):
    entries=[(n,0) for n in ITEM_ORDER if n!='none']+[('shield',0),('shield_side',0),('shield_back',0),('shield',1),('shield_side',1),('shield_back',1)]
    width,height=208,172
    out=Image.new('RGB',(5*width,52+height*((len(entries)+4)//5)),'#101820')
    draw=ImageDraw.Draw(out)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
    draw.text((12,10),'Imported screenshot pixels — native32 + 3x / native16 + 3x',font=font,fill='#eee9d7')
    for i,(name,variant) in enumerate(entries):
        x=(i%5)*width;y=52+(i//5)*height
        rows,pal=menu_frame(name,variant);large=_paint(rows,pal)
        small_rows,bank=world_frame(name,16,variant);small=_paint(small_rows,BANK_PALETTES[bank])
        for im,scale,at in ((large,3,(x+8,y)),(large,1,(x+116,y+64)),(small,3,(x+150,y+48)),(small,1,(x+174,y+12))):
            zoom=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST);out.paste(zoom,at,zoom)
        draw.text((x+8,y+108),name+(' upgraded' if variant else ''),font=font,fill='#eee9d7')
        draw.text((x+8,y+128),bank+' world / individual menu',font=font,fill='#9eafba')
    out.save(path)
    return path


def metadata():
    return {'sources':{'items':{'path':'art/ref/items-reference.jpg','sha256':hashlib.sha256(ITEM_SOURCE.read_bytes()).hexdigest()},
                       'shields':{'path':'art/ref/shields-reference.jpg','sha256':hashlib.sha256(SHIELD_SOURCE.read_bytes()).hexdigest()}},
            'item_cell_cuts':{'x':ITEM_X,'y':ITEM_Y},'shield_cell_cuts':{'x':SHIELD_X,'y':SHIELD_Y},
            'resample':'NEAREST','native_sizes':[16,32],'opaque_extent':'14px small / 30px large; aspect preserved',
            'matte':'Border-connected light neutral checkerboard, enclosed checker holes and near-boundary JPEG neutral ringing removed; tiny compression components removed.',
            'menu_palette':'Per-frame15colours plus transparency, RGB555','world_palettes':BANK_PALETTES}


if __name__=='__main__':
    import sys
    path=preview(sys.argv[1] if len(sys.argv)>1 else '/workspace/setup/reference-items-preview.png')
    Path(path).with_suffix('.json').write_text(json.dumps(metadata(),indent=2)+'\n')
    print('Wrote',path)
