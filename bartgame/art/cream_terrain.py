"""Original Curdled Cream terrain, authored on native sixteen-pixel canvases.

This module only exports new names and RGB555 banks. It never mutates any
existing tile, palette, metatile identifier, or forest/sewer painter.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

PALETTES = {
 'cream_floor0':['#000000','#302830','#685840','#887850','#b8b080','#d0c898','#e8e0b0','#f8f0d0','#706048','#908058','#b8a878','#d8c890','#486048','#688060','#98a078','#f8f8e0'],
 'cream_floor1':['#000000','#302830','#605840','#807850','#a8a878','#c0c090','#d8d8a8','#f0e8c8','#685840','#887850','#a89868','#c0b880','#485840','#687050','#889068','#f0f0d0'],
 'cream_floor2':['#000000','#282030','#585040','#787058','#989078','#b0a890','#c8c0a0','#e0d8b8','#605038','#786848','#988458','#b8a478','#483850','#704068','#a848b8','#f8d8f8'],
 'cream_cliff0':['#000000','#302830','#504038','#685840','#887850','#a89868','#c0b880','#e0d8a0','#f8e8b8','#484030','#686040','#889058','#485048','#607058','#a8b878','#fff8d8'],
 'cream_cliff1':['#000000','#302830','#483838','#605040','#807048','#989060','#b0a878','#d0c890','#e8e0a8','#404030','#585840','#788050','#503050','#783878','#b848d8','#f8d8f8'],
 'cream_cliff2':['#000000','#281828','#403038','#584048','#786058','#907860','#a89870','#c0b088','#e0c8a0','#383030','#504038','#706048','#582060','#9828c0','#e050f0','#fff0f8'],
 'cream_water':['#000000','#302830','#404838','#586048','#788060','#a0a878','#c8d0a0','#e8e8b8','#f8f8d8','#586058','#788080','#a8b0a0','#504058','#783878','#b848d8','#f0b8f8'],
 'cream_props':['#000000','#281f28','#483830','#685038','#907048','#b89058','#d8b878','#f8d8a0','#fff0c8','#384838','#587050','#809870','#482850','#8838a8','#d850e8','#fff0f8'],
}
# Keep every literal RGB component representable in the GBA's five-bit DAC.
PALETTES = {name:['#%02x%02x%02x'%tuple(int(color[i:i+2],16)//8*8 for i in (1,3,5)) for color in colors]
            for name,colors in PALETTES.items()}
DIGITS='0123456789abcdef'


def rows(image):
    return [''.join(DIGITS[image.getpixel((x,y))] for x in range(image.width)) for y in range(image.height)]


def _new(fill=0):
    image=Image.new('P',(16,16),fill)
    return image,ImageDraw.Draw(image)


def floor(stage=0,variant=0,path=False):
    image,d=_new(4)
    # Quiet horizontal curd seams; no uniform checker/noise bed.
    if path and variant==0:
        d.line([(4,9),(7,8),(10,8)],fill=3)
        d.line((5,10,9,9),fill=5)
    if variant==1:
        d.line([(2,11),(4,10),(7,10)],fill=3)
        d.line([(3,12),(5,11),(8,11)],fill=5)
    elif variant==2:
        d.line([(10,3),(12,3),(13,4)],fill=3)
        d.line([(10,4),(12,4)],fill=5)
    elif variant==3:
        d.line([(4,5),(6,4),(9,4)],fill=3)
        d.line([(5,6),(8,5)],fill=5)
    if stage and variant==3:
        d.line([(10,11),(12,10),(13,10)],fill=12)
        d.point((12,11),fill=13)
        if stage==2:d.point((13,10),fill=14)
    return image


def cliff(stage=0,kind='mid',variant=0):
    image,d=_new(4)
    # Broad shelves and irregular horizontal strata describe height. Long
    # vertical divisions are limited to the recessed climbable fissure.
    phase=(variant*5)%13
    d.line([(0,5),(4,5),(6,4),(11,4),(14,5),(15,5)],fill=3)
    d.line([(0,6),(5,6),(7,5),(11,5)],fill=5)
    d.line([(0,13),(3,12),(8,12),(10,13),(15,13)],fill=2)
    d.line([(2,14),(7,13),(10,14)],fill=5)
    if variant:
        d.line([(phase,7),(phase+2,8),(min(15,phase+4),8)],fill=3)
    if kind=='top':
        d.polygon([(0,0),(15,0),(15,2),(12,3),(9,2),(5,3),(2,2),(0,3)],fill=7)
        d.line([(0,3),(3,4),(6,3),(10,3),(13,4),(15,3)],fill=2)
        d.line([(1,1),(5,1),(8,0),(12,1),(15,1)],fill=8)
    elif kind=='base':
        d.polygon([(0,12),(4,13),(6,11),(10,13),(13,12),(15,13),(15,15),(0,15)],fill=2)
        d.line([(0,15),(15,15)],fill=1)
    elif kind=='left':
        d.polygon([(0,0),(3,0),(4,5),(3,9),(4,15),(0,15)],fill=2)
        d.line([(4,0),(5,4),(4,8),(5,15)],fill=6)
    elif kind=='right':
        d.polygon([(12,0),(15,0),(15,15),(12,15),(11,10),(12,5)],fill=2)
    if stage and (variant or kind=='base'):
        d.line([(2,11),(4,9),(7,9),(9,7),(12,8),(15,5)],fill=12,width=2)
        d.line([(3,11),(5,9),(7,10),(9,8),(12,9),(15,6)],fill=13)
        if stage==2:d.line([(7,10),(9,8),(12,9)],fill=14)
    return image


def climb(stage=0,kind='mid'):
    image=cliff(stage,'mid',1);d=ImageDraw.Draw(image)
    d.rectangle((3,0,12,15),fill=2)
    d.line([(3,0),(3,15)],fill=1);d.line([(12,0),(12,15)],fill=5)
    d.line([(5,0),(5,15)],fill=6);d.line([(10,0),(10,15)],fill=3)
    for y in (3,9,15):
        d.line((4,y,11,y),fill=1,width=2)
        d.line((4,y-1,11,y-1),fill=7)
        d.point((5,y-2),fill=8)
    if kind=='top':
        d.line((0,0,15,0),fill=7)
        d.line((1,1,4,1),fill=8);d.line((11,1,14,1),fill=8)
    if kind=='bottom':
        d.line((2,15,13,15),fill=1)
        d.line((4,14,11,14),fill=7)
    return image


def rim(stage=0,variant=0,drop=False):
    image=floor(stage,variant);d=ImageDraw.Draw(image)
    # An obstructed rim has rooted curd knobs; the safe drop notch is open.
    d.line([(0,11),(4,11),(6,10),(10,10),(13,11),(15,11)],fill=2)
    d.polygon([(0,12),(4,12),(6,11),(10,11),(13,12),(15,12),(15,15),(0,15)],fill=8)
    d.line([(1,12),(4,12),(6,11),(10,11),(13,12)],fill=7)
    if not drop:
        for x in (1,9):
            d.polygon([(x,10),(x+1,6),(x+4,5),(x+6,8),(x+5,11)],fill=1)
            d.polygon([(x+1,9),(x+2,7),(x+4,7),(x+5,9)],fill=12 if stage<2 else 13)
            d.point((x+3,6),fill=14 if stage==2 else 13)
    else:
        d.line((4,10,11,10),fill=7)
        d.line((6,12,9,12),fill=6)
        d.point((7,13),fill=7)
    return image


def cave(stage=0):
    image=Image.new('P',(32,48),0);d=ImageDraw.Draw(image)
    d.polygon([(1,47),(1,17),(5,8),(12,3),(20,3),(27,10),(31,21),(31,47)],fill=1)
    d.polygon([(2,45),(3,18),(7,10),(13,5),(20,5),(26,12),(29,22),(29,45)],fill=4)
    d.line([(5,19),(9,11),(14,7),(19,7)],fill=7,width=3)
    d.line([(7,20),(11,13),(16,11),(21,14),(25,22)],fill=2,width=3)
    d.polygon([(7,47),(7,23),(11,16),(16,13),(22,17),(25,24),(25,47)],fill=1)
    d.line([(9,23),(12,18),(16,16),(19,17)],fill=2)
    d.rectangle((8,39,24,47),fill=2)
    d.line((5,46,27,46),fill=7);d.line((8,47,24,47),fill=6)
    for y in (24,34):d.line((2,y,6,y-1),fill=2);d.line((26,y,30,y+1),fill=2)
    if stage:
        d.line([(26,11),(24,20),(27,26),(26,34),(29,40)],fill=12,width=3)
        d.line([(26,11),(25,20),(28,26),(27,34)],fill=13)
        if stage==2:d.point((26,20),fill=14);d.point((28,26),fill=15)
    return image


def water(stage=0,phase=0,fall=False):
    image,d=_new(3)
    if fall:
        d.rectangle((0,0,2,15),fill=1);d.rectangle((13,0,15,15),fill=2)
        d.line((3,0,3,15),fill=5);d.line((11,0,11,15),fill=4)
        for y in (2+phase*2,9+phase*2):d.line((5,y%16,9,y%16),fill=6)
    else:
        for x,y in ((2,4),(9,11)):
            d.line((x+phase,y,x+3+phase,y),fill=5)
            d.line((x+1,y+1,x+4,y+1),fill=4)
        d.line((0,0,15,0),fill=2)
    if stage==2:
        d.line((6,6+phase,10,6+phase),fill=13);d.point((8,6+phase),fill=14)
    return image


def prop(kind='mold',stage=0,phase=0):
    image,d=_new()
    if kind=='mold':
        d.ellipse((1,10,14,15),fill=1)
        for x,y,r in ((4,7,3),(9,5,4),(12,10,2)):
            d.ellipse((x-r,y-r,x+r,y+r),fill=12 if stage==2 else 9)
            d.line((x-r+1,y-r+1,x,y-r),fill=13 if stage==2 else 11)
    elif kind=='lamp':
        d.line((7,8,7,15),fill=3,width=2);d.line((6,14,9,14),fill=1)
        d.polygon([(3,4),(7,1),(12,4),(11,11),(4,11)],fill=1)
        d.rectangle((5,4,10,9),fill=5);d.rectangle((6,5,9,8),fill=7)
        d.point((7,5 if phase else 6),fill=8)
        d.line((4,3,11,3),fill=6)
    elif kind=='shrine':
        d.rectangle((2,9,13,14),fill=1);d.rectangle((3,10,12,13),fill=4)
        d.polygon([(4,9),(5,5),(10,5),(12,9)],fill=5)
        d.polygon([(6,5),(6,2),(9,1),(11,3),(9,6)],fill=6)
        d.line((6,2,8,2),fill=8);d.point((8,3),fill=8)
    elif kind=='switch':
        d.ellipse((0,5,15,15),fill=1);d.ellipse((1,4,14,12),fill=3)
        d.ellipse((3,5,12,10),fill=6 if not phase else 10)
        d.line((4,6,10,6),fill=8 if not phase else 11)
    elif kind=='trial':
        d.ellipse((1,11,14,15),fill=1);d.rectangle((4,9,11,12),fill=5);d.line((3,12,12,12),fill=7)
        d.polygon([(5,9),(5,4),(7,1),(9,1),(11,4),(11,9)],fill=1)
        d.polygon([(6,8),(6,4),(8,2),(10,4),(10,8)],fill=6);d.line((7,4,9,4),fill=8)
        d.point((8,6),fill=8)
    elif kind=='cache':
        d.ellipse((1,11,15,15),fill=1)
        for x,y in ((3,9),(8,7),(10,11)):
            d.rectangle((x,y,x+4,y+2),fill=4);d.line((x,y,x+4,y),fill=7);d.point((x+1,y),fill=8)
    elif kind=='ward':
        d.ellipse((1,1,14,15),fill=1);d.ellipse((2,2,13,14),fill=12);d.ellipse((4,4,11,12),fill=1)
        for x,y in ((7,3),(4,10),(11,10)):
            d.rectangle((x-1,y-1,x+1,y+1),fill=6);d.point((x,y-1),fill=8)
        d.line((7,6,7,11),fill=13);d.point((7,8),fill=15)
    elif kind in ('thorn','web','crack'):
        d.ellipse((1,11,14,15),fill=1)
        if kind=='thorn':
            for pts in ([(2,13),(4,8),(3,3),(7,7),(9,2),(10,9),(14,6),(12,14)],):
                d.line(pts,fill=1,width=4);d.line(pts,fill=12,width=2);d.line(pts,fill=13)
                d.point((9,2),fill=15)
        elif kind=='web':
            for a,b in [((1,2),(14,14)),((14,2),(1,14)),((8,1),(8,15)),((1,8),(15,8))]:d.line((a,b),fill=7)
            d.polygon([(4,4),(11,4),(13,8),(11,12),(4,12),(2,8)],outline=6)
        else:
            d.polygon([(0,15),(1,5),(5,1),(12,2),(15,7),(14,15)],fill=2)
            d.polygon([(2,12),(3,6),(7,3),(12,4),(13,12)],fill=5)
            d.line([(9,3),(6,7),(9,9),(6,14)],fill=1,width=2)
            d.line((4,4,6,3),fill=8)
    return image



def chest(opened=False):
    image=Image.new('P',(32,32),0);d=ImageDraw.Draw(image)
    d.ellipse((3,27,29,31),fill=1)
    d.polygon([(5,27),(5,13),(8,8),(23,8),(27,13),(27,27),(23,30),(8,30)],fill=1)
    d.rectangle((7,14,25,27),fill=3)
    d.rectangle((9,17,23,26),fill=4)
    for x in (9,16,23):d.line((x,17,x,26),fill=2)
    d.line((7,26,25,26),fill=6);d.line((7,28,25,28),fill=5)
    if opened:
        d.polygon([(6,14),(6,5),(10,2),(23,2),(26,6),(26,14)],fill=1)
        d.rectangle((8,6,24,12),fill=5);d.line((8,5,23,5),fill=8)
        d.rectangle((8,14,24,19),fill=1);d.line((8,20,24,20),fill=6)
    else:
        d.polygon([(6,14),(8,9),(12,7),(21,7),(25,10),(27,14)],fill=5)
        d.line((10,9,22,9),fill=8);d.line((7,14,26,14),fill=6)
    for x in (9,22):
        d.rectangle((x,10 if not opened else 7,x+2,28),fill=6)
        d.line((x,11 if not opened else 8,x,26),fill=8)
    d.rectangle((14,18,19,23),fill=1);d.rectangle((15,19,18,22),fill=7)
    if not opened:d.point((16,20),fill=1);d.line((16,21,17,22),fill=1)
    return image

def pit(stage=0):
    image=floor(stage,0);d=ImageDraw.Draw(image)
    d.ellipse((0,2,15,15),fill=2);d.ellipse((1,3,14,14),fill=1)
    d.line((3,3,11,3),fill=7);d.line((4,14,11,14),fill=3)
    return image


def build():
    out=[]
    def add(name,image,pal,kind='FLOOR',coll=0,**kwargs):
        out.append(dict(name='cream_'+name,pal=pal,type=kind,coll=coll,art=rows(image),**kwargs))
    for stage in range(3):
        fp='cream_floor%d'%stage;cp='cream_cliff%d'%stage
        for v in range(4):
            add('floor_s%d_v%d'%(stage,v),floor(stage,v),fp)
            add('path_s%d_v%d'%(stage,v),floor(stage,v,True),fp)
        for kind in ('top','mid','base','left','right'):
            for v in range(2):add('cliff_%s_s%d_v%d'%(kind,stage,v),cliff(stage,kind,v),cp,'SOLID',15)
        add('rim_s%d'%stage,rim(stage),fp,'SOLID',15)
        add('drop_s%d'%stage,rim(stage,drop=True),fp,'FLOOR',0)
        for kind in ('top','mid','bottom'):add('climb_%s_s%d'%(kind,stage),climb(stage,kind),cp,'CLIMB',0)
        door=cave(stage)
        for y in range(3):
            for x in range(2):add('cave_s%d_%d_%d'%(stage,x,y),door.crop((x*16,y*16,x*16+16,y*16+16)),cp,'MYST' if y==2 else 'SOLID',(10 if x==0 else 5) if y==2 else 15,prop=1)
        for kind,tt in [('thorn','THORN'),('web','WEB'),('crack','CRACK')]:
            add('%s_s%d'%(kind,stage),prop(kind,stage),'cream_props',tt,15,prop=1)
        add('pit_s%d'%stage,pit(stage),fp,'PIT',0)
        for gate,tt in [('web','WEB'),('crack','CRACK'),('ward','SOLID')]:
            bottom=door.crop((0,32,32,48));bd=ImageDraw.Draw(bottom)
            overlay=prop(gate,stage)
            mask=Image.new('L',overlay.size);mask.putdata([255 if c else 0 for c in overlay.tobytes()]);bottom.paste(overlay,(8,0),mask)
            for x in range(2):add('cave_%s_s%d_%d'%(gate,stage,x),bottom.crop((x*16,0,x*16+16,16)),cp,tt,15,prop=1)
        add('mold_s%d'%stage,prop('mold',stage),'cream_props',prop=1)
        for kind in ('water','fall'):
            out.append(dict(name='cream_%s_s%d'%(kind,stage),pal='cream_water',type='WATER' if kind=='water' else 'SOLID',coll=0 if kind=='water' else 15,
                            frames=[rows(water(stage,p,kind=='fall')) for p in range(2)],anim_speed=16))
    for kind,tt,coll in [('trial','FLOOR',0),('cache','FLOOR',0),('ward','SOLID',15),('lamp','TORCH',15),('shrine','FLOOR',0),('switch','SWITCH',0)]:
        add(kind,prop(kind),'cream_props',tt,coll,prop=int(kind!='switch'))
    add('lamp_lit',prop('lamp',phase=1),'cream_props','TORCH_LIT',15,prop=1)
    add('switch_down',prop('switch',phase=1),'cream_props','SWITCH',0)
    for opened in (False,True):
        source=chest(opened)
        for y in range(2):
            for x in range(2):
                add('chest_%s_%d_%d'%('open' if opened else 'closed',x,y),source.crop((x*16,y*16,x*16+16,y*16+16)),'cream_props','CHEST_OPEN' if opened else 'CHEST',15,prop=1)
    return out


import cream_studies as _studies
VARIANT=_studies.VARIANT
_studies.install(globals())
METATILES=build()


def write_review(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    font=ImageFont.load_default()
    rows_per=9;cell=64;canvas=Image.new('RGB',(8*cell,((len(METATILES)+7)//8)*54+20),(24,24,32));d=ImageDraw.Draw(canvas);d.fontmode='1'
    d.text((4,3),'SOURCE ART / native16px + 2x nearest inspection; not emulator output',font=font,fill=(240,232,200))
    manifest=[]
    for i,mt in enumerate(METATILES):
        raw=(mt.get('frames') or [mt['art']])[0];im=Image.new('P',(16,16));im.putdata([int(c,16) for r in raw for c in r]);pal=PALETTES[mt['pal']]
        colors=[int(v[j:j+2],16) for v in pal for j in (1,3,5)];im.putpalette(colors+[0]*(768-len(colors)));x=(i%8)*cell;y=22+(i//8)*54
        canvas.paste(im.convert('RGB'),(x,y));canvas.paste(im.convert('RGB').resize((32,32),Image.Resampling.NEAREST),(x+20,y));d.text((x,y+34),mt['name'].replace('cream_','')[:11],fill=(224,216,184),font=font)
        manifest.append({k:mt[k] for k in ('name','pal','type','coll')})
    canvas.save(destination/'terrain-source.png');(destination/'manifest.json').write_text(json.dumps(dict(metatiles=manifest,palettes=PALETTES),indent=2)+'\n')


if __name__=='__main__':
    import sys
    write_review(sys.argv[1] if len(sys.argv)>1 else '/workspace/setup/curdled-cream/source')
