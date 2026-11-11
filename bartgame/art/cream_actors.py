"""New Curdled Cream folk, climbing poses and peak monster at native GBA size.

Old sheets are never read back and modified. The climbing family shares the
existing Bloom head painter and palette as identity, with newly drawn hands,
root legs and weight transfer. Original sheets and every earlier frame stay
untouched. The peak monster is new art for the source-inspired Gleerok verb.
"""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
import reboot_actors as A
import reboot_core as R

POSES=('idle','walk1','walk2','tell','attack','recover','hurt','buried')
FACES=('n','e','s','w')


def climb_frame(phase):
    image=Image.new('P',(32,32),0);d=ImageDraw.Draw(image)
    side=1 if phase in (1,2) else -1
    # A planted root and a raised knee alternate; the stem leans over that
    # planted root rather than leaving the body suspended under waving arms.
    lean=side if phase in (1,3) else 0
    d.line([(15+lean,22),(16+lean,26),(13,29),(10,29 if side<0 else 26)],fill=1,width=3)
    d.line([(17+lean,22),(18+lean,26),(21,30),(23,30 if side<0 else 27)],fill=1,width=3)
    d.line([(16+lean,23),(17+lean,27)],fill=9,width=2)
    d.line([(14,28),(11,28 if side<0 else 25)],fill=12)
    d.line([(20,29),(22,29 if side<0 else 26)],fill=12)
    left=(8,14 if side<0 else 20);right=(24,20 if side<0 else 14)
    for shoulder,bend,grip in (((13+lean,24),(7,23),left),((19+lean,24),(25,23),right)):
        d.line([shoulder,bend,grip],fill=1,width=3)
        d.line([shoulder,bend,grip],fill=10,width=1)
        d.line((grip[0]-1,grip[1],grip[0]+1,grip[1]),fill=12)
    A._head(image,'n',dx=lean,dy=-1 if phase in (1,3) else 0)
    return image


def folk(style=0,phase=0):
    image=Image.new('P',(32,32),0);d=ImageDraw.Draw(image)
    step=1 if phase==2 else -1 if phase==1 else 0
    # Pale curd/bone faces against cool gray/ochre clothes; no violet friend
    # aura that would falsely advertise an enemy vulnerability or projectile.
    if style==0:
        d.polygon([(11,14),(21,14),(24,28),(21,30),(10,30),(8,27)],fill=1)
        d.polygon([(12,15),(20,15),(22,27),(11,28)],fill=4)
        d.line((12,17,12,26),fill=6);d.line((18,17,20,27),fill=3)
        d.rectangle((10,6,22,16),fill=1);d.rectangle((11,7,21,14),fill=5)
        d.line((12,7,20,7),fill=8);d.line((10,15,22,15),fill=13)
        d.rectangle((13,16,19,19),fill=7);d.point((14,17),fill=1);d.point((18,17),fill=1)
        d.line((8,22,6,18),fill=1,width=3);d.line((7,21,6,18),fill=6)
        d.line((24,26,26,12),fill=1,width=3);d.line((25,25,26,12),fill=12)
        d.ellipse((23,8,29,14),fill=1);d.ellipse((24,9,28,12),fill=7)
    elif style==1:
        d.polygon([(12,16),(21,16),(25,26),(20,29),(9,28)],fill=1)
        d.polygon([(13,17),(20,17),(23,25),(11,26)],fill=10)
        d.line((13,18,12,24),fill=12);d.line((20,20,22,25),fill=9)
        d.ellipse((10,7,22,19),fill=1);d.ellipse((12,9,21,17),fill=7)
        d.polygon([(6,10),(9,4),(22,3),(27,10),(22,12),(10,12)],fill=1)
        d.polygon([(9,9),(11,6),(21,5),(24,9),(21,10)],fill=11)
        d.point((14,14),fill=1);d.point((19,14),fill=1)
        d.line((9,21,5,24),fill=1,width=3);d.line((23,20,27,22),fill=1,width=3)
        d.ellipse((4,21,7,25),fill=7);d.ellipse((26,20,29,23),fill=7)
    else:
        d.polygon([(13,5),(20,5),(24,17),(24,29),(17,31),(8,29),(9,17)],fill=1)
        d.polygon([(14,7),(19,7),(22,17),(21,28),(10,27),(11,17)],fill=6)
        d.line((12,15,11,25),fill=8);d.line((20,14,21,26),fill=4)
        d.ellipse((12,10,21,19),fill=1);d.line((14,18,19,18),fill=3)
        d.line((8,21,5,24),fill=1,width=3);d.point((5,24),fill=8)
        d.line((25,31,25,11),fill=1,width=3);d.line((24,29,24,11),fill=12)
        d.polygon([(22,11),(22,7),(25,3),(28,7),(27,12)],fill=1)
        d.polygon([(24,10),(24,7),(26,6),(26,10)],fill=14)
        d.point((25,8),fill=15)
    d.line((11,30,13,31-step),fill=1,width=2);d.line((20,30,22,31+step),fill=1,width=2)
    if phase==3:d.line((15,20,18,20),fill=13)
    return image


def peak_boss(pose='idle',face='s'):
    image=Image.new('P',(32,64),0);d=ImageDraw.Draw(image)
    if pose=='buried':
        d.ellipse((1,50,30,63),fill=1);d.ellipse((3,50,28,60),fill=3)
        d.line((8,53,23,53),fill=12);d.point((16,51),fill=14)
        return image
    dy=1 if pose=='walk2' else -1 if pose=='tell' else 0
    # Heavy folded cream hide, branching neck and broad planted feet. The
    # tall neck is a continuous body, not a floating head/body pair.
    d.ellipse((2,42,29,62),fill=1);d.ellipse((4,43,27,59),fill=9)
    d.polygon([(7,56),(7,40),(11,31),(11,17+dy),(15,9+dy),(23,10+dy),(27,17+dy),(24,28),(20,34),(23,44),(24,58)],fill=1)
    d.polygon([(9,54),(9,41),(13,31),(13,18+dy),(17,11+dy),(22,12+dy),(24,18+dy),(22,27),(18,34),(21,44),(22,55)],fill=11)
    d.line([(11,51),(11,42),(16,32),(15,19),(18,14)],fill=15,width=2)
    d.line([(21,17),(22,24),(17,34),(20,44),(21,53)],fill=10,width=2)
    for y in (22,30,39,47):
        d.line((13,y,19,y+1),fill=8)
        d.point((14,y-1),fill=15)
    # When stunned, the long neck folds down into a visible climbable ramp.
    # The back core stays fixed at local (16,42), feet minus 22 pixels.
    if pose in ('recover','hurt'):
        d.rectangle((0,0,31,31),fill=0)
        d.polygon([(11,37),(10,30),(14,24),(25,23),(29,28),(24,34),(19,39)],fill=1)
        d.polygon([(12,35),(12,30),(16,26),(24,25),(26,28),(22,31),(18,36)],fill=11)
        d.line([(13,33),(16,28),(22,27)],fill=15,width=2)
    # Broad armor plates on the head use sharp edges and a dark underside.
    hx=17 if face in ('s','n') else 22 if face=='e' else 11
    hy=11+dy if pose!='attack' else 16
    if pose in ('recover','hurt'):hx=22 if face!='w' else 10;hy=26
    if pose=='attack':
        d.polygon([(11,29),(10,20),(hx-6,hy),(hx+6,hy),(26,24),(23,33)],fill=1)
        d.line([(13,28),(13,21),(hx-3,hy+2)],fill=11,width=3)
    d.polygon([(hx-8,hy+2),(hx-5,hy-4),(hx+4,hy-5),(hx+9,hy+1),(hx+8,hy+10),(hx+2,hy+14),(hx-6,hy+10)],fill=1)
    d.polygon([(hx-6,hy+2),(hx-3,hy-2),(hx+3,hy-3),(hx+7,hy+2),(hx+6,hy+8),(hx+1,hy+11),(hx-4,hy+8)],fill=4)
    d.line([(hx-4,hy),(hx+1,hy-2),(hx+5,hy+1)],fill=11,width=2)
    d.line((hx-4,hy+5,hx+5,hy+5),fill=2)
    for x in (hx-3,hx+4):
        d.line((x,hy+3,x+1,hy+3),fill=14);d.point((x,hy+4),fill=1)
    d.polygon([(hx-5,hy-3),(hx-8,hy-8),(hx-2,hy-5)],fill=1)
    d.polygon([(hx+4,hy-4),(hx+8,hy-9),(hx+8,hy-1)],fill=1)
    # Purple dorsal blister is the explicit weak spot. Recovery opens the
    # outer plates and exposes a larger bright core, matching the mechanic.
    exposed=pose in ('recover','hurt')
    d.polygon([(9,45),(10,36),(15,32),(21,36),(23,45),(17,50)],fill=1)
    if exposed:
        d.polygon([(10,44),(12,37),(16,35),(20,39),(21,45),(16,48)],fill=12)
        d.ellipse((12,37,20,46),fill=13);d.ellipse((14,39,18,44),fill=14)
        d.line((15,40,17,40),fill=15);d.line((16,39,16,44),fill=15)
    else:
        d.polygon([(10,43),(12,37),(16,34),(21,38),(22,44),(17,48)],fill=3)
        d.line([(12,39),(16,37),(20,40)],fill=5)
        d.line((16,38,17,45),fill=12);d.point((17,42),fill=13)
    for x,mirror in ((4,False),(25,True)):
        yy=57 if pose=='walk1' and mirror or pose=='walk2' and not mirror else 60
        d.line([(x+3,51),(x,yy),(x-2 if mirror else x+4,yy+1)],fill=1,width=4)
        d.line([(x+2,52),(x,yy-1)],fill=11,width=2)
        d.point((x,yy),fill=15)
    if pose=='tell':
        d.line((4,27,9,30),fill=12);d.line((24,28,28,24),fill=12)
        d.point((4,27),fill=14);d.point((28,24),fill=14)
    if pose=='hurt':d.line((11,39,13,37),fill=15)
    # Direction remains legible without multiplying the boss's mass/collider.
    if face=='n':
        d.polygon([(hx-5,hy+2),(hx,hy-2),(hx+5,hy+2),(hx+3,hy+8),(hx-3,hy+8)],fill=3)
        d.line((hx-3,hy+1,hx+2,hy+1),fill=11)
    return image


def sewer_door(style=0):
    """New 32x64 OAM canvases with a 32x48 entrance; old Drain pixels and OBJ bank remain intact."""
    image=Image.new('P',(32,48),0);d=ImageDraw.Draw(image)
    d.ellipse((1,43,30,47),fill=1)
    d.polygon([(1,45),(1,16),(5,7),(12,3),(20,3),(27,8),(31,17),(31,45)],fill=1)
    d.polygon([(3,43),(3,17),(7,10),(13,6),(20,6),(25,11),(28,18),(28,43)],fill=4)
    d.line([(5,18),(9,11),(14,8),(19,8)],fill=7,width=2)
    d.line([(7,21),(11,14),(16,12),(22,16),(25,22)],fill=2,width=3)
    d.polygon([(8,44),(8,23),(11,17),(16,14),(21,17),(24,23),(24,44)],fill=1)
    if style in (0,2):
        # A continuous pale staircase, not a symbol pasted onto a dark door.
        for y,width in ((25,7),(29,9),(34,11),(40,13)):
            left=16-width//2
            d.rectangle((left,y,left+width,y+2),fill=6)
            d.line((left,y,left+width,y),fill=8)
            d.line((left,y+3,left+width,y+3),fill=2)
        if style==0:
            d.polygon([(11,6),(16,0),(21,6),(18,6),(18,10),(14,10),(14,6)],fill=1)
            d.polygon([(13,5),(16,2),(19,5),(17,5),(17,8),(15,8),(15,5)],fill=8)
        else:
            d.polygon([(13,0),(19,0),(19,4),(23,4),(16,11),(9,4),(13,4)],fill=1)
            d.polygon([(15,2),(17,2),(17,6),(20,6),(16,9),(12,6),(15,6)],fill=8)
        for x,y in ((4,26),(26,30),(3,37)):
            d.line((x,y,x+2,y),fill=6);d.point((x,y-1),fill=8)
    else:
        d.rectangle((9,24,23,43),fill=3)
        for x in (11,16,21):d.line((x,25,x,42),fill=2)
        d.line((9,25,23,25),fill=6);d.line((9,42,23,42),fill=6)
        # Open book sign and large keyhole clearly name an explorable annex.
        d.polygon([(7,13),(15,15),(16,13),(24,11),(24,20),(17,22),(15,22),(7,20)],fill=1)
        d.polygon([(9,14),(15,16),(15,20),(9,18)],fill=7)
        d.polygon([(17,15),(22,13),(22,18),(17,20)],fill=8)
        d.line((16,15,16,21),fill=6)
        d.ellipse((13,29,20,36),fill=6);d.ellipse((15,31,18,34),fill=1)
        d.polygon([(16,33),(15,38),(18,38),(17,33)],fill=1)
    padded=Image.new('P',(32,64),0);padded.paste(image,(0,16))
    return padded


def drain_bed():
    """A narrow cot with an ivory pillow and patched blanket at native size."""
    image=Image.new('P',(32,32),0);d=ImageDraw.Draw(image)
    # Vertical length and an exposed pale pillow carry the familiar bed read.
    d.polygon([(6,5),(8,2),(24,2),(26,5),(26,28),(24,31),(7,30),(5,27),(5,7)],fill=1)
    d.polygon([(8,5),(23,5),(24,7),(24,26),(8,27)],fill=11)
    d.rectangle((8,7,23,25),fill=6)
    d.rectangle((9,8,22,13),fill=7);d.line((10,8,21,8),fill=8)
    d.line((10,13,21,13),fill=5)
    d.polygon([(8,15),(23,15),(23,26),(9,27)],fill=3)
    d.line((9,15,22,15),fill=5);d.line((9,16,9,25),fill=4)
    d.rectangle((14,20,19,24),fill=4);d.line((15,20,18,20),fill=6)
    d.line((8,27,23,27),fill=12);d.line((8,28,23,28),fill=10)
    for x,y in ((5,3),(24,3),(6,28),(24,28)):
        d.rectangle((x,y,x+2,min(31,y+3)),fill=1)
        d.line((x,y,x,y+2),fill=12);d.point((x,y),fill=14)
    return image


def drain_trophy():
    """One unmistakable gold cup on a tarnished low plinth, in the FX bank."""
    image=Image.new('P',(32,32),0);d=ImageDraw.Draw(image)
    d.ellipse((7,27,25,31),fill=1)
    d.polygon([(8,23),(23,23),(26,27),(24,30),(8,30),(5,27)],fill=1)
    d.polygon([(9,24),(22,24),(24,27),(8,27)],fill=7)
    d.line((9,24,21,24),fill=9);d.line((9,28,23,28),fill=3)
    d.rectangle((14,15,18,22),fill=1);d.rectangle((15,15,17,21),fill=9)
    d.line((15,16,15,20),fill=11)
    d.ellipse((6,5,13,14),outline=1,width=3);d.ellipse((20,5,27,14),outline=1,width=3)
    d.arc((7,6,13,13),75,285,fill=9,width=1)
    d.arc((20,6,26,13),255,105,fill=8,width=1)
    d.polygon([(9,4),(24,4),(22,13),(19,17),(14,17),(11,13)],fill=1)
    d.polygon([(11,6),(22,6),(20,12),(18,15),(15,15),(13,12)],fill=9)
    d.line((12,7,13,11),fill=12,width=2)
    d.line((11,5,22,5),fill=11);d.line((14,22,19,22),fill=10)
    d.rectangle((15,8,18,11),fill=15);d.point((15,8),fill=11)
    return image


def build_sheets():
    folk_frames={'folk%d_%s'%(s,p):A.ink_rows(folk(s,i))
                 for s in range(3) for i,p in enumerate(('idle','walk1','walk2','talk'))}
    # Append to an existing late-added family: all sheet IDs and its twelve
    # original frame IDs/pixels remain exact. The legacy ascent picture stays
    # available for old evidence; the real Drain now repeats its BG ladder.
    folk_frames['drain_bed']=A.ink_rows(drain_bed())
    folk_frames['drain_trophy']=A.ink_rows(drain_trophy())
    return [
        dict(name='creamdoors',w=32,h=64,pal='iron',frames={'ascent':A.ink_rows(sewer_door(0)),'annex':A.ink_rows(sewer_door(1)),'return':A.ink_rows(sewer_door(2))}),
        dict(name='creamclimb',w=32,h=32,pal='hero',frames={'climb_%d'%i:A.ink_rows(climb_frame(i)) for i in range(4)}),
        dict(name='creamfolk',w=32,h=32,pal='iron',frames=folk_frames,
             frame_pal={name:'fx' if name=='drain_trophy' else 'iron' for name in folk_frames}),
        dict(name='cream_boss',w=32,h=64,pal='blight',frames={p+'_'+f:A.ink_rows(peak_boss(p,f)) for p in POSES for f in FACES}),
    ]


def write_review(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    sheets=build_sheets();font=ImageFont.load_default();canvas=Image.new('RGB',(640,1150),(24,24,32));d=ImageDraw.Draw(canvas);d.fontmode='1'
    d.text((6,5),'SOURCE ART / native canvases; added frames only, no old art changed',fill=(240,232,200),font=font)
    banks={'hero':R.PALETTES['hero'],'iron':R.PALETTES['stone'],'blight':R.PALETTES['blight'],'fx':R.PALETTES['gold']}
    y=30;manifest=[]
    for sheet in sheets:
        d.text((6,y),sheet['name'],fill=(240,232,200),font=font);y+=16
        for i,(name,raw) in enumerate(sheet['frames'].items()):
            bank=sheet.get('frame_pal',{}).get(name,sheet['pal'])
            image=Image.new('P',(sheet['w'],sheet['h']));image.putdata([int(c,16) for row in raw for c in row]);colors=[int(v[j:j+2],16) for v in banks[bank] for j in (1,3,5)];image.putpalette(colors+[0]*(768-len(colors)))
            cols=6 if len(sheet['frames'])<=12 else 8;stride=102 if cols==6 else 78;rowh=sheet['h']*(2 if cols==6 else 1)+18
            x=8+(i%cols)*stride;yy=y+(i//cols)*rowh;canvas.paste(image.convert('RGB'),(x,yy));d.text((x,yy+sheet['h']+1),name,fill=(216,208,184),font=font)
            if len(sheet['frames'])<=12:canvas.paste(image.convert('RGB').resize((sheet['w']*2,sheet['h']*2),Image.Resampling.NEAREST),(x+32,yy))
            manifest.append(dict(sheet=sheet['name'],frame=name,canvas=[sheet['w'],sheet['h']],palette=bank))
        y+=((len(sheet['frames'])+cols-1)//cols)*rowh+12
    canvas.crop((0,0,640,y)).save(destination/'actors-source.png');(destination/'actors-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':
    import sys
    write_review(sys.argv[1] if len(sys.argv)>1 else '/workspace/setup/curdled-cream/source')
