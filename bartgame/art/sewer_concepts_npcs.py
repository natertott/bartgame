"""Five native-pixel frog Peddlers and hooded, flame-staff wizards.

Comparison art only: importing this module never modifies the live painter.
All canvases are authored directly in sixteen indexed GBA inks. Portraits
are independent 48px drawings, not enlarged world sprites. World head/body
anchors retain the current Peddler's two streamed hardware objects.

Wizard staff top: body (26,8). Draw the 8px flame at body (23,1), so its core
rests at (26,6) and its base meets the staff. Indices13/14 belong exclusively
to the flame; a palette pulse cannot recolour the purple robe.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


STYLE_NAMES={1:'Crown of Sludge',2:'Crooked Brassworks',3:'Moonlit Cistern',
             4:'Rotten Reliquary',5:'Royal Drains'}
PEDDLER_NAMES={1:'Puddle Prince',2:'Dawdling Tinker',3:'Sleepy Minnow',
               4:'Mossback',5:'Absent Steward'}
WIZARD_NAMES={1:'Bent Cowl',2:'Crooked Hat',3:'Moon Hood',4:'Ragged Pilgrim',5:'Gilt Abbot'}
HEAD_FRAMES=('open','blink','left','down','grin')
BODY_FRAMES=('rest','tap','tap2','lift','spin9','spin7','spin5','spin3',
             'spin5b','spin7b','spin9b','slap','rub0','rub1')
WIZARD_FRAMES=('idle','blink','breath','breath_blink','kindle','kindle_blink')
FLAME_FRAMES=('w0','w1','w2','w3')
FLAME_ORIGIN=(23,1)


def _style(style):
    style=int(style)
    if style not in STYLE_NAMES:raise ValueError('sewer NPC concept must be1..5')
    return style


def _new(w,h):
    image=Image.new('P',(w,h),0)
    return image,ImageDraw.Draw(image)


def peddler_palette(style):
    """1outline;2–7frog/cream;8–11apron;12–14brass;15warmwhite."""
    style=_style(style)
    greens={
        1:['#182820','#284830','#487040','#78a050','#a8c878','#d8d898'],
        2:['#183028','#285038','#408048','#78b058','#b0d880','#e0e0a8'],
        3:['#183030','#285048','#387860','#60a078','#98c898','#d0e0b8'],
        4:['#202818','#384828','#586838','#809848','#b0b868','#d8d088'],
        5:['#183028','#285038','#487848','#78a858','#a8d080','#e0e0b0'],
    }[style]
    apron={1:['#282028','#483030','#705040','#987048'],
           2:['#302020','#583828','#885038','#b07848'],
           3:['#182830','#284048','#386068','#608080'],
           4:['#282020','#403028','#605038','#887048'],
           5:['#202038','#383050','#585078','#8880a0']}[style]
    return ['#000000','#101820',*greens,*apron,'#885828','#c09040','#f0c868','#f8f0d0']


def wizard_palette(style):
    """Purple2–7, staff8–10, ivory11, ember12, flame13/14, hotwhite15."""
    style=_style(style)
    purple={1:['#201828','#382040','#583058','#784078','#a068a0','#c8a0c0'],
            2:['#201830','#382048','#583068','#804898','#b078c0','#d8b0d8'],
            3:['#181830','#282848','#403868','#605088','#8870b0','#b8a8d0'],
            4:['#201820','#382030','#503048','#704060','#906880','#c098b0'],
            5:['#201830','#382048','#583070','#8050a0','#b080c8','#d8b8e0']}[style]
    return ['#000000','#101018',*purple,'#483020','#805030','#b88038',
            '#e0d8b8','#c85020','#f09828','#f8c858','#f8f0c0']


def _pupil(d,box,frame,side=0):
    x0,y0,x1,y1=box
    d.ellipse(box,fill=1)
    if frame=='blink':
        d.line([(x0+1,y1-1),(x1-1,y1-1)],fill=4)
        return
    d.ellipse((x0+1,y0+1,x1-1,y1-1),fill=7)
    px=(x0+x1)//2 + (-1 if frame=='left' else 0)
    py=(y0+y1)//2 + (1 if frame=='down' else 0)
    # The two eyes intentionally focus at slightly different heights.
    py=min(y1-1,max(y0+1,py+side))
    d.point((px,py),fill=1)


def peddler_head(style,name):
    style=_style(style)
    if name not in HEAD_FRAMES:raise ValueError(name)
    im,d=_new(16,16)
    # Flat, broad muzzles and eyes on top distinguish all five from rats.
    face={1:(1,5,14,14),2:(1,5,14,14),3:(2,6,14,13),4:(0,6,15,15),5:(2,6,13,14)}[style]
    d.ellipse(face,fill=1)
    a,b,c,e=face
    d.ellipse((a+1,b+1,c-1,e-1),fill=4)
    d.arc((a+2,b+1,c-2,e-2),185,330,fill=5)
    chin={1:(3,10,12,14),2:(2,10,13,14),3:(4,10,12,13),4:(1,10,14,15),5:(4,10,11,14)}[style]
    d.ellipse(chin,fill=3)
    d.line([(chin[0]+1,chin[3]-2),(7,chin[3]-1),(chin[2]-1,chin[3]-2)],fill=6)
    eyes={1:((2,2,7,8),(9,2,14,8)),2:((2,1,7,8),(9,3,13,8)),
          3:((2,3,7,8),(9,3,14,8)),4:((1,3,6,8),(10,3,14,8)),
          5:((3,3,7,8),(9,3,13,8))}[style]
    for side,box in enumerate(eyes):
        _pupil(d,box,name,side if style in (1,2,5) else 0)
        if style==3 and name!='blink':
            d.line([(box[0]+1,box[1]+1),(box[2]-1,box[1]+1)],fill=4)
            d.line([(box[0]+1,box[1]+2),(box[2]-1,box[1]+2)],fill=5)
    d.point((5,8),fill=2);d.point((10,8),fill=2)
    if name=='grin':
        d.line([(3,10),(5,11),(10,11),(12,10)],fill=1)
        d.line([(5,12),(9,12)],fill=7)
    elif style==2:
        d.line([(4,10),(9,11)],fill=1)
        d.rectangle((9,11,10,12),fill=1)
    elif style==3:
        d.line([(3,10),(10,11),(12,10)],fill=1)
    elif style==4:
        d.line([(2,11),(12,11)],fill=1);d.point((13,12),fill=1)
    else:
        d.line([(3,10),(10,10)],fill=1)
        d.rectangle((10,10,11,12),fill=1)
        d.point((10,13),fill=7)
    if style==4:
        for p in ((1,8),(3,7),(12,7),(14,9)):d.point(p,fill=5)
    if style==5:
        # A small flat porter cap, perched between the eyes, changes the
        # silhouette without hiding the characteristic frog eye lobes.
        d.line([(5,1),(10,1)],fill=1)
        d.rectangle((5,2,10,3),fill=13);d.line([(4,4),(11,4)],fill=12)
        d.line([(6,2),(9,2)],fill=14)
    return im


def _hand(d,x,y,side):
    d.ellipse((x-1,y-1,x+1,y+1),fill=1)
    d.line([(x,y-1),(x,y+1)],fill=5)
    d.point((x+side,y),fill=6)


def peddler_body(style,name):
    style=_style(style)
    if name not in BODY_FRAMES:raise ValueError(name)
    im,d=_new(32,32)
    wide={1:8,2:10,3:6,4:10,5:7}[style]
    left,right=16-wide,16+wide
    top={1:17,2:19,3:17,4:19,5:20}[style]
    # Large webbed feet are connected to the haunches, with no floating flecks.
    d.polygon([(left+2,25),(left,30),(left-2,31),(left+5,31),(left+6,27)],fill=1)
    d.polygon([(left+3,26),(left+1,30),(left+4,30),(left+5,27)],fill=4)
    d.polygon([(right-2,25),(right+1,30),(right+3,31),(right-5,31),(right-6,27)],fill=1)
    d.polygon([(right-3,26),(right,30),(right-4,30),(right-5,27)],fill=4)
    if style==2:
        d.ellipse((left,top,right,30),fill=1)
        d.ellipse((left+1,top+1,right-1,29),fill=4)
        d.arc((left+2,top+1,right-2,29),185,320,fill=5)
    elif style==4:
        d.polygon([(left+3,top),(right-4,top),(right,24),(right-1,28),
                   (right-6,30),(left+5,29),(left,27),(left+1,23)],fill=1)
        d.polygon([(left+4,top+1),(right-5,top+1),(right-1,24),(right-2,27),
                   (right-6,29),(left+5,28),(left+1,26),(left+2,23)],fill=4)
    elif style==5:
        d.polygon([(left+3,top),(right-3,top),(right,26),(right-2,30),(left+2,30),(left,26)],fill=1)
        d.polygon([(left+4,top+1),(right-4,top+1),(right-1,26),(right-3,29),(left+3,29),(left+1,26)],fill=4)
    else:
        d.polygon([(left+2,top),(right-2,top),(right,24),(right-2,29),(left+2,29),(left,24)],fill=1)
        d.polygon([(left+3,top+1),(right-3,top+1),(right-1,24),(right-3,28),(left+3,28),(left+1,24)],fill=4)
    # A cream throat meets the separately streamed head at bodyy18..20.
    throat={1:(12,18,20,23),2:(10,18,22,24),3:(13,18,19,23),4:(10,19,22,24),5:(13,19,19,23)}[style]
    d.ellipse(throat,fill=6)
    apron_left,apron_right=left+3,right-3
    d.polygon([(apron_left,20),(apron_right,20),(apron_right+1,28),(apron_left-1,28)],fill=8)
    d.polygon([(apron_left+1,21),(apron_right-1,21),(apron_right,27),(apron_left,27)],fill=10)
    d.line([(apron_left,21),(apron_left,26)],fill=11)
    d.line([(apron_right-1,22),(apron_right,27)],fill=9)
    d.line([(12,19),(13,22)],fill=11);d.line([(20,19),(19,22)],fill=9)
    if style==1:
        d.rectangle((13,24,19,26),fill=9);d.line([(13,24),(18,24)],fill=12)
        d.point((17,25),fill=14)
    elif style==2:
        d.rectangle((13,23,18,26),fill=9);d.line([(14,24),(17,25)],fill=11)
        d.point((14,25),fill=12)
    elif style==3:
        d.line([(13,24),(18,24)],fill=7)
        d.line([(13,25),(17,26)],fill=9)
    elif style==4:
        d.polygon([(10,25),(13,24),(14,27),(12,28),(11,27)],fill=9)
        d.line([(16,24),(19,24)],fill=11)
    elif style==5:
        d.line([(12,21),(15,23),(16,21),(18,23),(20,21)],fill=12)
        d.point((16,24),fill=14);d.point((16,26),fill=13)
    ly=24;ry=24
    lx=left;rx=right
    if name=='tap':ly=23
    elif name=='tap2':ly=22
    elif name=='lift':ry=20
    elif name.startswith('spin'):ry=20
    elif name=='slap':ry=25;rx=23
    elif name in ('rub0','rub1'):
        ly=ry=22 if name=='rub0' else 23;lx=15;rx=19
    d.line([(left+2,20),(lx,ly)],fill=1,width=3)
    d.line([(left+2,20),(lx,ly)],fill=4,width=1)
    d.line([(right-2,20),(rx,ry)],fill=1,width=3)
    d.line([(right-2,20),(rx,ry)],fill=5,width=1)
    _hand(d,lx,ly,-1);_hand(d,rx,ry,1)
    if name.startswith('spin'):
        width={'9':5,'7':3,'5':2,'3':1}[name[4]]
        cy=13 if name.endswith('b') else 11
        d.ellipse((rx-width//2,cy-2,rx+width//2,cy+2),fill=1)
        d.line([(rx-width//2,cy-1),(rx+width//2,cy-1)],fill=13)
        d.point((rx,cy),fill=14)
    elif name=='lift':
        d.ellipse((rx-2,ry-4,rx+2,ry),fill=1)
        d.ellipse((rx-1,ry-3,rx+1,ry-1),fill=13);d.point((rx,ry-3),fill=15)
    elif name=='slap':
        d.ellipse((21,25,25,27),fill=12);d.line([(22,25),(24,25)],fill=14)
    return im


def wizard(style,name):
    style=_style(style)
    if name not in WIZARD_FRAMES:raise ValueError(name)
    im,d=_new(32,32)
    breathing=name.startswith('breath');kindle=name.startswith('kindle')
    # A bowed spine and irregular hem make an old figure without a large face.
    coat={1:[(10,15),(18,15),(21,28),(17,31),(7,30),(8,25)],
          2:[(10,15),(19,16),(22,28),(19,31),(7,30),(8,22)],
          3:[(11,15),(19,15),(23,29),(18,31),(7,30),(9,23)],
          4:[(9,15),(17,16),(22,23),(21,29),(18,28),(16,31),(13,29),(9,31),(6,28),(8,24)],
          5:[(10,15),(19,15),(23,29),(19,31),(7,30),(8,23)]}[style]
    d.polygon(coat,fill=1)
    d.polygon([(11,17),(18,17),(20,27),(17,29),(9,28),(10,23)],fill=3)
    d.polygon([(11,18),(13,17),(12,25),(10,28),(9,27)],fill=5)
    d.polygon([(16,18),(18,19),(19,27),(16,29),(14,28)],fill=4)
    d.line([(15,22),(14,27)],fill=2)
    d.line([(10,28),(16,29),(19,28)],fill=5 if style!=4 else 4)
    # One pale boot and beard give small age cues beneath the hidden face.
    d.line([(10,30),(12,30)],fill=8);d.line([(17,30),(19,30)],fill=8)
    hood={1:[(8,16),(9,10),(12,6),(16,4),(18,7),(20,10),(20,17),(17,20),(11,19)],
          2:[(8,15),(10,8),(16,2),(22,2),(20,5),(22,13),(20,18),(12,19)],
          3:[(9,15),(9,10),(12,6),(17,4),(21,8),(22,15),(19,19),(12,19)],
          4:[(7,16),(8,11),(11,7),(15,6),(19,9),(20,14),(22,17),(19,18),(17,21),(14,19),(10,20)],
          5:[(8,16),(10,10),(15,1),(18,5),(22,11),(22,17),(18,20),(11,19)]}[style]
    d.polygon(hood,fill=1)
    d.polygon([(10,13),(11,9),(14,6),(17,6),(20,11),(20,16),(17,18),(12,17)],fill=4)
    d.line([(11,10),(14,7 if style in (1,4) else 6),(17,7 if style in (1,4) else 6)],fill=6)
    d.polygon([(12,12),(14,10),(17,10),(19,13),(18,17),(13,17)],fill=1)
    d.line([(13,12),(15,11),(17,12)],fill=2)
    if style in (1,2):
        d.polygon([(13,17),(17,17),(16,20),(14,19)],fill=11)
        d.point((14,18),fill=7)
    elif style==3:
        d.line([(12,17),(17,18)],fill=6)
    elif style==4:
        d.line([(10,14),(10,17),(12,18)],fill=5)
        d.point((19,9),fill=5)
    else:
        d.polygon([(15,3),(17,6),(15,8),(13,8)],fill=5)
        d.line([(11,11),(14,7),(17,7),(20,12)],fill=10)
        d.point((15,7),fill=11)
        d.line([(10,20),(11,26)],fill=10)
    # Fixed staff and flame anchor permit unchanged streaming/OAM dimensions.
    d.line([(26,8),(26,30)],fill=1,width=3)
    d.line([(26,9),(26,29)],fill=9)
    d.line([(25,12),(26,11)],fill=10)
    d.line([(25,24),(26,23)],fill=10)
    if style==1:
        d.line([(24,8),(28,8)],fill=10);d.point((26,9),fill=11)
    elif style==2:
        d.line([(25,9),(28,9),(28,7)],fill=10)
    elif style==3:
        d.arc((23,6,29,11),0,180,fill=10,width=1)
    elif style==4:
        d.line([(25,9),(27,8),(27,6)],fill=9);d.point((24,13),fill=8)
    else:
        d.rectangle((24,8,28,10),fill=10);d.point((25,8),fill=11)
    # Broad sleeves hold the shaft; wrists stay connected through every pose.
    hand_y=16 if kindle else 20 if breathing else 22
    d.line([(19,19),(22,hand_y+1),(25,hand_y)],fill=1,width=4)
    d.line([(19,19),(22,hand_y+1),(24,hand_y)],fill=4,width=2)
    d.point((25,hand_y),fill=11)
    d.line([(10,20),(8,24),(10,25)],fill=1,width=4)
    d.line([(10,20),(9,23)],fill=5,width=2)
    d.point((10,25),fill=11)
    if 'blink' in name:
        d.line([(13,14),(17,14)],fill=2)
    if breathing:d.line([(12,23),(13,25)],fill=5)
    return im


def flame(style,name):
    style=_style(style)
    if name not in FLAME_FRAMES:raise ValueError(name)
    im,d=_new(8,8);phase=FLAME_FRAMES.index(name)
    tip=[(3,0),(4,1),(2,0),(3,1)][phase]
    # A teardrop, not a detached halo or orb. The base touches staffy8.
    d.polygon([tip,(5,3),(6,4),(5,6),(3,7),(1,6),(1,4),(2,3)],fill=12)
    d.polygon([(tip[0],tip[1]+1),(4,3),(5,5),(4,6),(2,6),(2,4)],fill=13)
    d.polygon([(3,3),(4,5),(3,6),(2,5)],fill=14)
    d.point((3,5),fill=15)
    if style in (2,4) and phase==2:d.point((5,2),fill=13)
    return im


def portrait(style,who):
    style=_style(style)
    if who in ('peddler','frog'):return _frog_portrait(style)
    if who in ('gatekeeper','wizard'):return _wizard_portrait(style)
    raise ValueError(who)


def _frog_portrait(style):
    im,d=_new(48,48)
    # Portrait design echoes the world silhouette but is independently drawn.
    wide={1:20,2:18,3:19,4:22,5:19}[style]
    left,right=24-wide,24+wide
    if style==2:
        d.ellipse((2,30,46,60),fill=1);d.ellipse((5,32,43,58),fill=4)
    elif style==4:
        d.polygon([(2,47),(5,36),(12,32),(33,32),(43,37),(47,47)],fill=1)
        d.polygon([(5,47),(8,37),(14,34),(31,34),(40,38),(44,47)],fill=4)
    elif style==5:
        d.polygon([(8,47),(11,36),(17,33),(31,33),(37,37),(40,47)],fill=1)
        d.polygon([(11,47),(14,37),(18,35),(30,35),(34,38),(37,47)],fill=4)
    else:
        d.polygon([(5,47),(8,35),(14,31),(33,31),(40,36),(45,47)],fill=1)
        d.polygon([(8,47),(11,36),(16,33),(31,33),(37,37),(42,47)],fill=4)
    d.ellipse((15,29,33,40),fill=6)
    d.polygon([(13,35),(34,35),(36,47),(11,47)],fill=8)
    d.polygon([(15,36),(32,36),(33,47),(13,47)],fill=10)
    d.line([(15,37),(14,45)],fill=11,width=2)
    d.line([(30,38),(32,46)],fill=9,width=2)
    d.ellipse((left,10,right,34),fill=1)
    d.ellipse((left+2,12,right-2,32),fill=4)
    d.arc((left+4,11,right-4,31),190,330,fill=5,width=2)
    d.ellipse((11,23,36,35),fill=3)
    d.line([(13,30),(20,32),(29,32),(34,29)],fill=6,width=2)
    eye_boxes={1:((6,3,20,19),(28,3,42,19)),2:((7,1,21,18),(28,6,40,20)),
               3:((6,5,20,20),(28,5,42,20)),4:((4,5,18,20),(29,6,43,20)),
               5:((8,5,20,19),(28,5,40,19))}[style]
    for side,box in enumerate(eye_boxes):
        x0,y0,x1,y1=box;d.ellipse(box,fill=1)
        d.ellipse((x0+2,y0+2,x1-2,y1-2),fill=7)
        px=(x0+x1)//2+(1 if side else -1)
        py=(y0+y1)//2+(2 if side else 0)
        d.rectangle((px,py,px+1,py+2),fill=1)
        if style==3:
            d.polygon([(x0+2,y0+2),(x1-2,y0+2),(x1-2,y0+6),(x0+2,y0+7)],fill=4)
            d.line([(x0+3,y0+3),(x1-3,y0+3)],fill=5)
    d.rectangle((17,21,18,22),fill=2);d.rectangle((29,21,30,22),fill=2)
    if style==2:
        d.line([(12,26),(24,28),(32,27)],fill=1,width=2)
        d.rectangle((29,28,33,31),fill=1)
        d.line([(30,31),(32,31)],fill=7)
    elif style==3:
        d.line([(10,26),(20,28),(31,28),(36,26)],fill=1,width=2)
        d.point((35,27),fill=6)
    elif style==4:
        d.line([(9,26),(34,26),(37,28)],fill=1,width=2)
        for x,y in ((5,20),(8,23),(37,20),(41,24),(12,17)):d.rectangle((x,y,x+1,y+1),fill=5)
    else:
        d.line([(10,26),(29,27)],fill=1,width=2)
        d.polygon([(28,27),(34,27),(33,32),(29,33)],fill=1)
        d.line([(29,32),(32,32)],fill=7)
    if style==1:
        d.rectangle((19,41,29,45),fill=9);d.line([(19,41),(28,41)],fill=12)
        d.point((26,42),fill=14)
    elif style==2:
        d.rectangle((17,40,25,46),fill=9);d.line([(18,41),(23,44)],fill=11)
    elif style==3:d.line([(17,40),(29,40)],fill=7,width=2)
    elif style==4:
        d.polygon([(13,42),(18,40),(21,45),(16,47)],fill=9)
        d.line([(24,41),(30,41)],fill=11)
    else:
        d.rectangle((17,0,31,1),fill=1)
        d.rectangle((17,2,31,6),fill=13)
        d.line([(18,2),(29,2)],fill=14,width=2)
        d.line([(14,7),(34,7)],fill=12,width=2)
        d.line([(14,35),(21,40),(24,37),(29,40),(34,35)],fill=12,width=2)
        d.rectangle((24,42,25,43),fill=14)
    return im


def _wizard_portrait(style):
    im,d=_new(48,48)
    d.polygon([(2,47),(6,33),(14,27),(30,28),(38,35),(43,47)],fill=1)
    d.polygon([(5,47),(9,35),(15,30),(29,31),(34,37),(38,47)],fill=3)
    d.polygon([(10,35),(16,31),(17,39),(13,47),(7,47)],fill=5)
    d.line([(27,35),(30,44),(29,47)],fill=4,width=3)
    hood={1:[(7,26),(8,16),(13,8),(22,4),(27,7),(32,14),(34,25),(29,33),(15,34)],
          2:[(6,27),(8,14),(16,5),(29,0),(34,1),(30,7),(35,19),(33,30),(17,34)],
          3:[(6,26),(7,17),(12,8),(24,3),(32,9),(36,20),(33,31),(17,35)],
          4:[(4,28),(5,19),(10,11),(19,7),(27,10),(32,18),(35,26),(31,29),(29,35),(23,33),(19,36),(12,33)],
          5:[(5,28),(9,14),(20,0),(25,6),(34,15),(36,27),(30,35),(15,34)]}[style]
    d.polygon(hood,fill=1)
    d.polygon([(9,25),(10,16),(16,8),(23,7),(30,15),(32,25),(28,31),(17,32)],fill=4)
    d.line([(11,17),(17,9),(22,8)],fill=6,width=2)
    d.polygon([(14,19),(18,14),(24,14),(29,19),(28,27),(23,30),(16,27)],fill=1)
    d.line([(17,18),(20,16),(24,17)],fill=2,width=2)
    d.line([(10,25),(13,29),(16,30)],fill=5,width=2)
    if style in (1,2):
        d.polygon([(17,28),(23,29),(28,27),(26,33),(22,36),(18,33)],fill=11)
        d.line([(19,29),(21,33)],fill=7,width=1)
    elif style==3:d.line([(16,29),(23,32),(27,30)],fill=6,width=2)
    elif style==4:
        d.line([(10,23),(12,28)],fill=2,width=2)
        d.line([(26,9),(29,13)],fill=5,width=2)
    else:
        d.polygon([(20,3),(24,8),(21,11),(17,11)],fill=5)
        d.line([(12,17),(18,10),(23,10),(30,19)],fill=10,width=2)
        d.rectangle((20,10,22,11),fill=11)
        d.line([(13,35),(12,44)],fill=10,width=2)
    # The staff stays visibly continuous from the flame to the lower edge.
    d.line([(41,12),(41,47)],fill=1,width=5)
    d.line([(41,13),(41,47)],fill=9,width=3)
    d.line([(40,16),(42,16)],fill=10,width=2)
    d.line([(40,37),(42,37)],fill=10,width=2)
    d.line([(31,35),(35,38),(39,34)],fill=1,width=6)
    d.line([(31,35),(35,37),(38,34)],fill=4,width=3)
    d.line([(39,34),(41,33)],fill=11,width=2)
    d.polygon([(40,0),(43,4),(46,7),(45,11),(42,14),(38,13),(36,9),(38,5)],fill=12)
    d.polygon([(40,3),(43,6),(44,9),(42,12),(39,12),(38,9)],fill=13)
    d.polygon([(41,6),(43,9),(41,11),(39,10)],fill=14)
    d.point((41,9),fill=15)
    return im


def rgba(image,palette):
    result=Image.new('RGBA',image.size)
    result.putdata([tuple(int(palette[i][n:n+2],16) for n in (1,3,5))+(255 if i else 0,)
                    for i in image.tobytes()])
    return result


def _validate():
    for style in STYLE_NAMES:
        for palette in (peddler_palette(style),wizard_palette(style)):
            assert len(palette)==16
            assert all(int(c[n:n+2],16)%8==0 for c in palette for n in (1,3,5))
        for painter,names,size in ((peddler_head,HEAD_FRAMES,(16,16)),(peddler_body,BODY_FRAMES,(32,32)),
                                   (wizard,WIZARD_FRAMES,(32,32)),(flame,FLAME_FRAMES,(8,8))):
            for name in names:
                image=painter(style,name)
                assert image.mode=='P' and image.size==size and max(image.tobytes())<16,(style,name)
        for who in ('peddler','wizard'):
            image=portrait(style,who)
            assert image.mode=='P' and image.size==(48,48) and max(image.tobytes())<16
        assert not set(wizard(style,'idle').tobytes())&{13,14},'flame pulse recolours robe'


def preview(out):
    """Labelled native-source review boards; these are not emulator captures."""
    _validate();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
    scene=Image.new('RGBA',(1080,290),'#182028');draw=ImageDraw.Draw(scene)
    draw.text((8,5),'NATIVE SOURCE CONCEPTS / world sprites4x, portraits2x / not gameplay',font=font,fill='#f0e0b0')
    for style in STYLE_NAMES:
        x=(style-1)*216
        draw.text((x+8,28),str(style)+'. '+STYLE_NAMES[style],font=font,fill='#f0e0b0')
        pair=Image.new('RGBA',(50,42))
        pair.alpha_composite(rgba(peddler_head(style,'open'),peddler_palette(style)),(8,14))
        pair.alpha_composite(rgba(peddler_body(style,'rest'),peddler_palette(style)),(0,8))
        # Separate50px panel per character avoids overlapping source objects.
        scene.alpha_composite(pair.resize((200,168),Image.Resampling.NEAREST),(x+8,48))
        wiz=Image.new('RGBA',(32,32))
        wiz.alpha_composite(rgba(wizard(style,'idle'),wizard_palette(style)))
        wiz.alpha_composite(rgba(flame(style,'w0'),wizard_palette(style)),FLAME_ORIGIN)
        scene.alpha_composite(wiz.resize((128,128),Image.Resampling.NEAREST),(x+94,68))
        scene.alpha_composite(rgba(portrait(style,'peddler'),peddler_palette(style)).resize((96,96),Image.Resampling.NEAREST),(x+8,189))
        scene.alpha_composite(rgba(portrait(style,'wizard'),wizard_palette(style)).resize((96,96),Image.Resampling.NEAREST),(x+110,189))
    scene.convert('RGB').save(out/'npc-concepts.png')
    print('PASS five NPC styles,145 world frames,10 independent portraits; source board',out/'npc-concepts.png')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',default='/workspace/setup/sewer-concepts/npcs')
    preview(parser.parse_args().out)
