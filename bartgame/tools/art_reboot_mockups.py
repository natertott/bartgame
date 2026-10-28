"""Native 240x160 reboot mockups, not emulator screenshots.

Everything is painted directly at game resolution from literal 4bpp inks.
Nearest-neighbour enlarged copies are for viewing only, never art inputs.
"""
from pathlib import Path
import sys,json,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'art'))
import reboot_core as R
OUT=Path('/workspace/setup/art-reboot-mockups');OUT.mkdir(parents=True,exist_ok=True)


def tile_ground(kind='forest',variant=0):
    im,d=R.indexed(16,16,4 if kind=='forest' else 3)
    if kind=='forest':
        # Quiet broad stains, not isolated confetti pixels.
        if variant%3==0:d.polygon([(0,11),(5,9),(9,10),(11,15),(0,15)],fill=3)
        if variant%3==1:d.line([(2,3),(4,3),(5,4)],fill=5)
        if variant%3==2:d.line([(10,10),(13,10),(14,11)],fill=3)
        if variant%5==0:d.line([(3,13),(4,11),(5,13)],fill=6)
    elif kind=='blight':
        d.rectangle((0,0,15,15),fill=2)
        d.polygon([(0,3),(5,1),(10,3),(11,8),(6,10),(0,8)],fill=3)
        if variant%3==0:
            d.line([(2,15),(5,11),(4,8),(7,5)],fill=1)
            d.line([(5,12),(6,11),(5,8)],fill=4)
        if variant%4==0:d.line([(11,6),(14,7),(15,10)],fill=8)
    else:
        d.rectangle((0,0,15,15),fill=3)
        d.line([(0,0),(15,0)],fill=5);d.line([(0,15),(15,15)],fill=1)
        seam=5 if variant%2 else 11
        d.line([(seam,1),(seam,14)],fill=1)
        d.line([(seam+1,1),(seam+1,5)],fill=4)
        if variant%3==0:d.rectangle((2,10,5,12),fill=9)
    return im


def path_tile(mask=15,blight=False):
    fill=2 if blight else 4;shade=3 if blight else 8;base=4 if blight else 9;lit=5 if blight else 10
    im,d=R.indexed(16,16,fill)
    # Neighbour-connected arms keep the lane wide enough to read, with a
    # chipped two-pixel verge instead of hard square tile boundaries.
    d.rectangle((2,2,13,13),fill=base)
    for bit,box in [(1,(2,0,13,7)),(2,(8,2,15,13)),(4,(2,8,13,15)),(8,(0,2,7,13))]:
        if mask&bit:d.rectangle(box,fill=base)
    if not mask&1:d.line([(3,2),(8,2),(9,3),(12,3)],fill=lit);d.point((13,2),fill=fill)
    if not mask&4:d.line([(2,13),(5,13),(6,12),(12,12)],fill=shade);d.point((2,12),fill=fill)
    if not mask&8:d.line([(2,3),(2,7),(3,8),(3,12)],fill=shade);d.point((2,5),fill=fill)
    if not mask&2:d.line([(13,2),(13,6),(12,7),(12,11)],fill=lit);d.point((13,9),fill=fill)
    d.line([(6,7),(9,7),(10,8)],fill=shade)
    return im


def canopy_tile(variant=0,face=False):
    im,d=R.indexed(16,16,2)
    patterns=[[(-3,-2,10,8),(6,2,10,7),(-1,8,12,9)],[(1,-3,12,10),(-4,7,10,8),(9,9,10,8)],[(-4,-3,10,10),(5,2,12,10),(-2,10,10,8)],[(4,-4,14,10),(-4,2,12,11),(6,10,12,8)]]
    for x,y,w,h in patterns[variant%4]:
        d.polygon([(x,y+3),(x+3,y),(x+w-2,y+1),(x+w,y+4),(x+w-3,y+h),(x+2,y+h-1)],fill=3)
        d.polygon([(x+2,y+3),(x+4,y+1),(x+w-3,y+2),(x+w-2,y+4),(x+4,y+5)],fill=4)
        d.line([(x+4,y+2),(x+w-4,y+2)],fill=5)
        if (x+y+variant)%3==0:d.point((x+4,y+2),fill=6)
    if face:
        d.rectangle((0,12,15,15),fill=1)
        d.line([(2,12),(2,15)],fill=8);d.line([(12,11),(12,15)],fill=9)
        d.polygon([(0,8),(4,9),(5,13),(3,12),(2,14),(1,11),(0,12)],fill=2)
        d.polygon([(7,8),(12,8),(15,10),(14,13),(12,11),(10,14),(9,11)],fill=3)
        d.line([(8,9),(11,9),(13,10)],fill=4)
    return im


def stone_tile(blight=False,variant=0):
    im,d=R.indexed(16,16,2)
    d.rectangle((0,1,15,6),fill=4);d.rectangle((0,9,15,14),fill=3)
    d.line([(0,0),(15,0)],fill=6);d.line([(0,8),(15,8)],fill=5)
    for x,y in [(5,1),(12,9)]:d.line([(x,y),(x,y+5)],fill=1);d.point((x+1,y+1),fill=6)
    d.rectangle((1,4,3,6),fill=9);d.line([(2,3),(4,4),(3,5)],fill=10)
    if blight:
        d.line([(12,0),(10,4),(12,8),(9,12),(10,15)],fill=12)
        d.point((11,8),fill=14)
    return im


def water_tile(kind='forest',variant=0):
    im,d=R.indexed(16,16,3)
    d.polygon([(0,10),(4,8),(8,9),(10,12),(15,11),(15,15),(0,15)],fill=2)
    d.line([(2,4),(6,4)],fill=5 if variant%2==0 else 4)
    d.line([(9,11),(13,11)],fill=4)
    if variant%3==0:d.line([(3,5),(5,5)],fill=6)
    return im


def compose(kind='forest',warm=False,phase=0):
    bg=Image.new('RGBA',(240,160),R.rgb(R.bank('ground',warm)[4])+(255,))
    foliage=Image.new('RGBA',(240,160));world=Image.new('RGBA',(240,160))
    use={};tiles=[];stamps=[]
    planes={n:{'index':Image.new('P',(240,160)), 'bank':Image.new('I',(240,160),-1)} for n in ('BG2','BG1')}
    palette_ids={n:i for i,n in enumerate(R.PALETTES)}
    def stamp(layer,im,xy,pal):
        use.setdefault(pal,set()).update(im.getdata());R.paste(layer,im,xy,R.bank(pal,warm))
        plane='BG2' if layer is bg else 'BG1' if layer is foliage else 'OBJ'
        stamps.append({'layer':plane,'xy':list(xy),'size':list(im.size),'palette':pal,'colors':len(set(im.getdata()))})
        if plane in planes:
            dest=planes[plane]['index'];banks=planes[plane]['bank'];px=im.load();dp=dest.load();bp=banks.load()
            for yy in range(im.height):
                for xx in range(im.width):
                    dx,dy=xy[0]+xx,xy[1]+yy;v=px[xx,yy]
                    if v and 0<=dx<240 and 0<=dy<160:dp[dx,dy]=v;bp[dx,dy]=palette_ids[pal]

    terrain_pal='ground' if kind=='forest' else 'blight' if kind=='blight' else 'drain'
    for ty in range(10):
        for tx in range(15):
            t=tile_ground(kind,(tx*3+ty*7)%11);stamp(bg,t,(tx*16,ty*16),terrain_pal)
            tiles.append({'xy':[tx,ty],'palette':terrain_pal,'colors':len(set(t.getdata()))})
    # An unbroken, calm dirt route and a meaningful side branch to the bridge.
    path={(7,9),(7,8),(7,7),(8,7),(8,6),(8,5),(8,4),(9,4),(10,4),(10,3), (6,7),(5,7),(4,7)}
    if kind!='drain':
        for x,y in path:
            mask=sum(bit for dx,dy,bit in [(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)] if (x+dx,y+dy) in path)
            stamp(bg,path_tile(mask,blight=kind=='blight'),(x*16,y*16),terrain_pal)
        # Water has a pond to the north and one continuous outlet stream.
        wet={(x,y) for y in (5,6) for x in range(3,7)}|{(5,y) for y in range(4,10)}
        for x,y in wet:
            stamp(bg,water_tile(kind,x+y),(x*16,y*16),'water' if kind=='forest' else 'rot_water')
            # A bank inherits the water bank; no square grass patch pasted on it.
            rim=R.indexed(16,16)[0];rd=ImageDraw.Draw(rim)
            for dx,dy,edge in [(-1,0,'w'),(1,0,'e'),(0,-1,'n'),(0,1,'s')]:
                if (x+dx,y+dy) not in wet:
                    if edge=='w':rd.line([(0,0),(0,15)],fill=12);rd.line([(1,3),(1,8),(2,10)],fill=9)
                    if edge=='e':rd.line([(15,0),(15,15)],fill=12);rd.line([(14,0),(14,5),(13,7)],fill=9)
                    if edge=='n':rd.line([(0,0),(15,0)],fill=11);rd.line([(2,1),(8,1),(10,2)],fill=10)
                    if edge=='s':rd.rectangle((0,13,15,15),fill=9);rd.line([(0,13),(15,13)],fill=11);rd.line([(3,14),(8,14)],fill=12)
            # Grass-coloured corner wedges soften convex pond corners.
            for ax,ay,bx,by,pts in [(-1,0,0,-1,[(0,0),(4,0),(0,4)]),(1,0,0,-1,[(15,0),(11,0),(15,4)]),(-1,0,0,1,[(0,15),(4,15),(0,11)]),(1,0,0,1,[(15,15),(11,15),(15,11)])]:
                if (x+ax,y+ay) not in wet and (x+bx,y+by) not in wet:rd.polygon(pts,fill=10)
            stamp(bg,rim,(x*16,y*16),'water' if kind=='forest' else 'rot_water')
        # Wet mud and accumulated leaves collect along the bank, with broad
        # organic silhouettes rather than random one-pixel noise.
        mud,md=R.indexed(32,16)
        md.polygon([(0,8),(4,4),(11,3),(15,6),(23,4),(31,8),(28,13),(19,14),(12,12),(4,14)],fill=8 if kind=='forest' else 8)
        md.line([(5,7),(11,5),(16,8),(23,7)],fill=9)
        md.line([(8,11),(13,10),(17,12)],fill=10)
        stamp(world,mud,(99,75),terrain_pal)
        matter,md=R.indexed(16,16)
        md.polygon([(1,4),(5,2),(9,4),(14,3),(14,7),(10,8),(7,6),(3,8)],fill=9)
        md.line([(3,4),(6,4),(8,5)],fill=11)
        md.line([(10,4),(12,4)],fill=10)
        stamp(world,matter,(49,88),'water' if kind=='forest' else 'rot_water')
        # The bridge connects two actual banks across the outlet.
        bridge,d=R.indexed(48,16)
        d.rectangle((0,2,47,14),fill=1)
        for x in range(0,48,6):
            d.rectangle((x+1,3,x+5,12),fill=5);d.line([(x+1,3),(x+5,3)],fill=6);d.line([(x+1,11),(x+5,11)],fill=3)
        d.line([(0,1),(47,1)],fill=8);d.line([(0,14),(47,14)],fill=7)
        stamp(world,bridge,(64,112),'gold')
        # Dense canopy forms the room boundary, with irregular but readable fringe.
        wall={(x,y) for y in (1,2) for x in range(15)}|{(x,y) for x in (0,14) for y in range(2,10)}
        wall|={(x,3) for x in (0,1,2,3,4,11,12,13,14)}
        for x,y in wall:stamp(foliage,canopy_tile(x*5+y*3,face=(x,y+1) not in wall),(x*16,y*16),'foliage' if kind=='forest' else 'blight')
        for x,y in [(12,36),(186,32),(195,113),(8,117)]:stamp(foliage,R.tree(kind=='blight'),(x,y),'foliage' if kind=='forest' else 'blight')
        # An old raised masonry terrace, with accessible stair landing.
        for x,y in [(11,6),(12,6),(13,6),(13,7)]:stamp(bg,stone_tile(kind=='blight',x+y),(x*16,y*16),'stone' if kind=='forest' else 'blight')
        stair,d=R.indexed(16,32,1)
        for y in range(0,32,6):d.rectangle((2,y+1,13,y+4),fill=5);d.line([(2,y+1),(13,y+1)],fill=8)
        stamp(world,stair,(176,96),'stone')
        stamp(world,R.portal('hollow' if kind=='forest' else 'thicket'),(152,25),'gold')
        stamp(world,R.chest(0 if kind=='forest' else 2),(41,111),'gold')
        stamp(world,R.plate(False),(200,91),'stone')
        # A pristine pale flower grows at the lip of the dirty bank.
        flower,fd=R.indexed(8,8)
        fd.line([(3,4),(3,7)],fill=10);fd.line([(2,6),(0,5)],fill=9)
        fd.line([(1,2),(5,2)],fill=15);fd.line([(3,0),(3,4)],fill=15);fd.point((3,2),fill=11)
        stamp(world,flower,(111,90),'blight')
        stamp(world,R.pickup('key' if kind=='forest' else 'bomb'),(145,128),'gold')
        stamp(world,R.beetle(kind=='blight'),(153,96),'foliage' if kind=='forest' else 'blight')
        if kind=='blight':
            # Filth has a specific material: wet ulcer pools, bare roots and bone.
            pool,d=R.indexed(32,16)
            d.ellipse((0,2,31,15),fill=1);d.ellipse((2,3,28,13),fill=3)
            d.line([(5,6),(10,4),(16,6),(21,5),(25,8)],fill=12)
            d.line([(7,10),(13,11),(17,9)],fill=13)
            d.point((14,10),fill=14)
            stamp(world,pool,(112,51),'blight')
            bone,d=R.indexed(16,16)
            d.line([(3,11),(12,4)],fill=1,width=3);d.line([(3,10),(11,4)],fill=15)
            d.ellipse((1,9,4,12),fill=15);d.ellipse((10,2,13,5),fill=15)
            stamp(world,bone,(192,74),'blight')
            roots,d=R.indexed(32,32)
            for pts in [[(0,23),(10,15),(13,2)],[(8,31),(14,20),(29,14)],[(12,18),(20,8),(27,6)]]:
                d.line(pts,fill=1,width=3);d.line(pts,fill=9)
            stamp(world,roots,(96,68),'blight')
    else:
        # Drain: raised back masonry, copper outlet and an unmistakable ladder.
        for ty in range(1,4):
            for tx in range(15):stamp(bg,stone_tile(False,tx+ty),(tx*16,ty*16),'drain')
        for ty in range(4,10):
            for tx in (0,14):stamp(bg,stone_tile(False,tx+ty),(tx*16,ty*16),'drain')
        wet={(x,y) for y in (7,8,9) for x in range(1,14)}
        for x,y in wet:stamp(bg,water_tile('drain',x+y),(x*16,y*16),'water')
        # Narrow footbridge actually crosses the channel, into the walkable hall.
        bridge,d=R.indexed(32,64)
        d.rectangle((3,0,28,63),fill=1)
        for y in range(0,64,6):d.rectangle((5,y,26,y+4),fill=5);d.line([(5,y),(26,y)],fill=6)
        d.line([(2,0),(2,63)],fill=8);d.line([(29,0),(29,63)],fill=7)
        stamp(world,bridge,(104,96),'gold')
        # A 32x40 framed ladder exit with lit rungs and green daylight.
        entry=R.portal('cave');ed=ImageDraw.Draw(entry)
        ed.rectangle((11,13,20,41),fill=1)
        for x in (11,20):ed.line([(x,13),(x,41)],fill=7,width=2)
        for y in range(15,40,5):ed.line([(12,y),(19,y)],fill=14)
        ed.line([(13,11),(18,11)],fill=14)
        stamp(world,entry,(151,20),'stone')
        # Copper pipes and grime remain material rather than random props.
        pipe,d=R.indexed(64,16)
        d.rectangle((0,5,63,11),fill=1);d.rectangle((0,6,63,9),fill=4)
        d.line([(0,6),(63,6)],fill=6)
        for x in (4,24,44):d.rectangle((x,4,x+3,12),fill=7);d.line([(x,4),(x+2,4)],fill=9)
        stamp(world,pipe,(10,44),'gold')
        stall,d=R.indexed(56,32)
        d.rectangle((0,9,55,29),fill=1);d.rectangle((2,12,53,27),fill=4)
        d.line([(2,12),(53,12)],fill=9);d.line([(2,28),(53,28)],fill=7)
        for x in (8,24,40):d.line([(x,14),(x,27)],fill=3)
        for x in range(0,56,8):d.rectangle((x,1,x+6,7),fill=14 if x%16 else 15)
        stamp(world,stall,(21,60),'gold')
        stamp(world,R.pickup('coin'),(202,86),'gold')
        stamp(world,R.chest(1),(181,91),'gold')
        # Grease and damp descend from the copper pipe and collect at the
        # same walls/edges, so grime has causes instead of random texture.
        damp,dd=R.indexed(64,40)
        dd.polygon([(0,0),(63,0),(61,5),(54,4),(52,10),(48,7),(44,18),(38,9),(30,12),(25,28),(21,17),(15,20),(10,10),(3,12)],fill=2)
        for pts in [[(9,3),(10,12),(9,18)],[(25,3),(24,15),(25,26)],[(44,3),(43,11),(44,18)],[(54,3),(54,9)]]:dd.line(pts,fill=9,width=2)
        dd.line([(10,4),(12,6),(11,11)],fill=10)
        stamp(world,damp,(16,44),'drain')
        grease,gd=R.indexed(40,16)
        gd.polygon([(0,9),(5,5),(13,3),(20,5),(26,3),(37,8),(39,12),(33,15),(23,13),(15,15),(7,13)],fill=1)
        gd.line([(6,8),(11,6),(18,7),(23,6),(31,9)],fill=9)
        gd.line([(16,11),(22,12),(28,10)],fill=10)
        stamp(world,grease,(146,92),'drain')
        # Corroded outlet and thick scum in the channel below it.
        outlet,od=R.indexed(32,48)
        od.rectangle((11,0,19,16),fill=1);od.rectangle((12,0,18,15),fill=4)
        od.line([(12,1),(12,12)],fill=9)
        od.ellipse((7,10,23,21),fill=1);od.ellipse((9,11,21,19),fill=7);od.ellipse((11,12,19,17),fill=1)
        od.polygon([(11,17),(19,17),(20,36),(26,41),(24,45),(8,45),(5,41),(10,35)],fill=13)
        od.line([(13,20),(12,36),(10,40)],fill=14)
        stamp(world,outlet,(202,69),'gold')
        # Slime stains and drips are clustered along edges, not on every floor cell.
        slime,d=R.indexed(48,16)
        d.polygon([(0,3),(8,1),(16,4),(24,2),(34,5),(47,3),(47,8),(36,7),(30,10),(17,8),(9,11),(0,8)],fill=9)
        d.line([(3,3),(9,2),(14,4)],fill=11);d.line([(27,5),(34,6),(40,4)],fill=10)
        stamp(world,slime,(6,99),'drain')
    contact,cd=R.indexed(16,8)
    cd.ellipse((2,2,13,5),fill=1);cd.line([(4,2),(11,2)],fill=2)
    stamp(world,contact,(119,118),'ground')
    # Small Bloom occupies less than one-quarter of the 32x48 entrance width/height area.
    stamp(world,R.hero('s',phase%2),(119,98),'hero')
    scene=Image.alpha_composite(bg,foliage);scene=Image.alpha_composite(scene,world)
    # Glitter grammar: many tiny ambient twinkles, few readable objective glints.
    sd=ImageDraw.Draw(scene)
    ambient=[(12,30),(33,44),(64,33),(91,28),(115,38),(141,28),(198,29),(222,45),(15,92),(35,132),(67,89),(93,101),(188,72),(217,100),(228,140),(180,139),(24,151),(160,151),(53,69),(209,59)]
    for i,(x,y) in enumerate(ambient):
        age=(phase+i)%4
        c=R.rgb(R.bank('gold',warm)[11 if age==0 else 9 if age==1 else 6])
        if age==0:sd.line((x-1,y,x+1,y),fill=c);sd.point((x,y-1),fill=c)
        elif age<3:sd.point((x,y),fill=c)
    glints=[(168,33),(55,119),(150,135),(203,93),(79,113),(182,87)] if kind!='drain' else [(167,29),(27,45),(130,103),(204,91),(205,87),(54,73)]
    for j,(x,y) in enumerate(glints):
        if (phase+j)%6<4:
            sd.line((x-2,y,x+2,y),fill=R.rgb(R.PALETTES['gold'][10]));sd.line((x,y-2,x,y+2),fill=R.rgb(R.PALETTES['gold'][11]));sd.point((x,y),fill=R.rgb(R.PALETTES['gold'][12]))
        else:sd.point((x,y),fill=R.rgb(R.PALETTES['gold'][9]))
    # Compact fixed HUD uses the established gold-frame and A/B/L vocabulary.
    hud,d=R.indexed(240,20,1)
    d.rectangle((1,1,238,18),fill=2);d.line([(1,19),(238,19)],fill=6)
    for x in (4,13,22):
        d.polygon([(x,5),(x+2,4),(x+4,6),(x+6,4),(x+8,5),(x+8,8),(x+4,12),(x,8)],fill=10)
        d.polygon([(x+1,5),(x+2,5),(x+4,7),(x+6,5),(x+7,5),(x+7,8),(x+4,11),(x+1,8)],fill=12)
        d.point((x+2,6),fill=9)
    # Literal pixel digits and slot initials avoid a high-resolution font.
    tiny={'0':['111','101','101','101','111'],'1':['010','110','010','010','111'],'2':['111','001','111','100','111'],'A':['010','101','111','101','101'],'B':['110','101','110','101','110'],'L':['100','100','100','100','111']}
    def label(text,x,y,c=8):
        for ch in text:
            for yy,row in enumerate(tiny[ch]):
                for xx,v in enumerate(row):
                    if v=='1':d.point((x+xx,y+yy),fill=c)
            x+=4
    d.ellipse((40,5,46,12),fill=7);d.line([(42,6),(44,6),(44,10)],fill=9);label('12',51,7)
    for x,ch in [(142,'A'),(174,'B'),(206,'L')]:
        d.rectangle((x,2,x+29,17),fill=1);d.rectangle((x+1,3,x+28,16),outline=6);label(ch,x+3,5)
    # Native sword, shield and lamp glyphs inside the three slots.
    d.line([(156,5),(162,11)],fill=9,width=2);d.line([(155,11),(160,6)],fill=7);d.line([(160,12),(163,15)],fill=7)
    d.polygon([(190,5),(198,5),(198,11),(194,15),(190,11)],fill=7);d.line([(191,6),(197,6)],fill=9)
    d.rectangle((222,6,228,14),fill=7);d.rectangle((224,8,226,12),fill=9);d.arc((223,3,227,8),180,360,fill=8)
    R.paste(scene,hud,(0,0),R.PALETTES['ui'])
    # Exact indexed output after composing already native 4bpp assets.
    rgbim=scene.convert('RGB');colors=sorted(set(rgbim.getdata()));assert len(colors)<=256,len(colors)
    pal=[]
    for c in colors:pal.extend(c)
    pal.extend([0]*(768-len(pal)))
    out=Image.new('P',(240,160));out.putpalette(pal);lut={c:i for i,c in enumerate(colors)};out.putdata([lut[c] for c in rgbim.getdata()])
    assert all(all(v%8==0 for v in c) for c in colors)
    # Pack the actual mockup's two background planes into4bpp8x8subtiles.
    # Each cell must reference one16-colourbank; flippedduplicatesreusebytes.
    keys=set();bg_banks=set();nonempty=0
    for plane,data in planes.items():
        for y in range(0,160,8):
            for x in range(0,240,8):
                values=tuple(data['index'].getpixel((x+xx,y+yy)) for yy in range(8) for xx in range(8))
                banks={data['bank'].getpixel((x+xx,y+yy)) for yy in range(8) for xx in range(8) if values[yy*8+xx]}
                assert len(banks)<=1,(plane,x,y,banks)
                if banks:bg_banks.update(banks);nonempty+=1
                grid=[values[i:i+8] for i in range(0,64,8)]
                variations=[]
                for hf in (False,True):
                    for vf in (False,True):
                        rows=grid[::-1] if vf else grid
                        variations.append(tuple(v for row in rows for v in (row[::-1] if hf else row)))
                keys.add(min(variations))
    assert len(keys)<=1024 and len(bg_banks)<=12
    # Everyworldobjectcanbesplit/paddedinto8x8tiles andvalidOBJshapes.
    # This upper bound usesone8x8OBJeach tile; actualproductionuseslargershapes.
    world_tiles=sum(((a['size'][0]+7)//8)*((a['size'][1]+7)//8) for a in stamps if a['layer']=='OBJ')
    shapes=[(8,8),(16,16),(32,32),(64,64),(16,8),(32,8),(32,16),(64,32),(8,16),(8,32),(16,32),(32,64)]
    obj_plan=[]
    for a in stamps:
        if a['layer']!='OBJ':continue
        sw,sh=a['size'];w,h=min((p for p in shapes if p[0]>=sw and p[1]>=sh),key=lambda p:p[0]*p[1])
        obj_plan.append({'native_source':a['size'],'padded_hardware_shape':[w,h],'palette':a['palette'],'resident_tiles':w*h//64})
    padded_tiles=sum(p['resident_tiles'] for p in obj_plan)
    # Conservatively give every sparkle its own8x8tile and everyworldstamp
    # its own padded sprite, even when their frames could be shared.
    assert len(obj_plan)+26<=128 and padded_tiles+26<=876
    return out,{'native_resolution':[240,160],'unique_scene_colors':len(colors),'material_palettes':sorted(use),'palette_index_usage':{k:sorted(v) for k,v in use.items()},'ground_metatiles':tiles,'ambient_twinkles':20,'large_interaction_glints':6,'phase':phase,'background_pack':{'unique_4bpp_subtiles_with_flips':len(keys),'subtile_limit':1024,'resident_bg_palette_banks':len(bg_banks),'bg_palette_limit':12,'valid_one_bank_per_8x8':True,'nonempty_bg_map_cells':nonempty},'world_obj_source_tiles':world_tiles,'obj_hardware_plan':{'padded_resident_tiles':padded_tiles,'glitter_additional_tile_upper_bound':26,'combined_tiles_upper_bound':padded_tiles+26,'reserved_engine_limit_reference':876,'world_sprites':len(obj_plan),'glitter_sprite_upper_bound':26,'combined_oam_upper_bound':len(obj_plan)+26,'oam_limit':128,'palette_banks':len({a['palette'] for a in obj_plan}),'shape_plan':obj_plan},'glitter_obj_upper_bound':26,'source_stamps':stamps}


def board(images,path,title,scale=3):
    w,h=240*scale,160*scale
    out=Image.new('RGB',(len(images)*w+(len(images)+1)*12,h+52),'#101820');d=ImageDraw.Draw(out)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
    d.text((12,8),title,font=font,fill='#f0d898')
    for i,(name,im) in enumerate(images):
        x=12+i*(w+12);out.paste(im.resize((w,h),Image.Resampling.NEAREST),(x,36));d.text((x,h+39),name,font=font,fill='#e8e0c0')
    out.save(path)


def calibration():
    assets=[('Bloom14x22',R.hero(),'hero'),('Bloomback',R.hero('n'),'hero'),('key13x14',R.pickup('key'),'gold'),('coin10x12',R.pickup('coin'),'gold'),('woodenchest',R.chest(),'gold'),('relicchest',R.chest(2),'gold'),('tree',R.tree(),'foliage'),('rottree',R.tree(True),'blight'),('hollow',R.portal(),'gold'),('cave',R.portal('cave'),'stone'),('thicket',R.portal('thicket'),'gold'),('plate',R.plate(),'stone')]
    out=Image.new('RGB',(960,42+2*230),'#101820');d=ImageDraw.Draw(out)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
    d.text((10,10),'Native source assets / 4x and1x / selectedApalette / NOT emulator captures',font=font,fill='#f0d898')
    measurements={}
    for i,(name,asset,pal) in enumerate(assets):
        a=R.rgba(asset,R.PALETTES[pal]);x=(i%6)*160+8;y=42+(i//6)*230
        out.paste(a.resize((a.width*4,a.height*4),Image.Resampling.NEAREST),(x,y),a.resize((a.width*4,a.height*4),Image.Resampling.NEAREST))
        out.paste(a,(x+118,y+150),a)
        box=asset.getbbox();dims=[box[2]-box[0],box[3]-box[1]]
        measurements[name]={'canvas':list(asset.size),'visible_bounds':list(box),'visible_size':dims,'inks_including_transparency':len(set(asset.getdata())),'palette':pal}
        d.text((x,y+199),name+' '+str(dims),font=font,fill='#e0d8b8')
    out.save(OUT/'scale-calibration.png')
    (OUT/'scale-calibration.json').write_text(json.dumps(measurements,indent=2)+'\n')

def main():
    scenes=[];reports={}
    for name,kind,warm in [('direction-a-verdigris','forest',False),('direction-b-tarnished','forest',True),('deep-blight','blight',False),('drain','drain',False)]:
        frames=[]
        for phase in range(4):
            im,r=compose(kind,warm,phase);frames.append(im)
            if phase==0:
                im.save(OUT/(name+'-native.png'));im.resize((960,640),Image.Resampling.NEAREST).save(OUT/(name+'-4x.png'));reports[name]=r;scenes.append((name,im))
        frames[0].save(OUT/(name+'.gif'),save_all=True,append_images=frames[1:],duration=180,loop=0,disposal=2)
    calibration()
    board(scenes[:2],OUT/'directions.png','Native 240x160 design mockups / 3x nearest display / NOT emulator captures',3)
    board([scenes[0],scenes[2],scenes[3]],OUT/'three-scenes.png','One shared pixel grammar / native 240x160 design mockups / NOT emulator captures',2)
    (OUT/'constraints.json').write_text(json.dumps({'method':__doc__.strip(),'all_colors_rgb555':True,'base_palettes':R.PALETTES,'variants':reports,'assets':{'bloom_canvas':[16,24],'pickups_canvas':[16,16],'chest_canvas':[32,32],'portal_canvas':[32,48],'tree_canvas':[32,48]},'notes':['Native object canvases map to padded GBA OBJ shapes in production; no image was downscaled.','Final indexed scene has fewer than 256 colours; source material banks have exactly 16 inks including transparency.','This is a design mockup, not a running game or verified GBA tileset build.']},indent=2)+'\n')
    print(OUT)

if __name__=='__main__':main()
