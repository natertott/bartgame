"""Reference-led native frog Peddlers and flame-staff wizards.

Five proportion/shape studies share one lighting and pixel-cluster grammar.
Authoring starts on16px heads,32px bodies,8px flames and48px portraits. The
source2 silhouette/idle advice, Janes' directional form, and the material
and palette lessons in all six uploaded PDFs guide the deliberately broad
planes. No high-resolution drawing is resized into these production pixels.

The existing head/body anchors and frame identifiers are retained. Staff
shaft(26,8), flame origin(23,1), and reserved emissive indices13/14 are fixed.
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
             'spin5b','spin7b','spin9b','slap','rub0','rub1','breathe')
WIZARD_FRAMES=('idle','blink','breath','breath_blink','kindle','kindle_blink')
FLAME_FRAMES=('w0','w1','w2','w3')
FLAME_ORIGIN=(23,1)


def _style(style):
    style=int(style)
    if style not in STYLE_NAMES:raise ValueError('sewer NPC concept must be1..5')
    return style


def _new(w,h):
    im=Image.new('P',(w,h),0)
    return im,ImageDraw.Draw(im)


def _stamp(dst,src,xy):
    dst.paste(src,xy,src.point(lambda v:255 if v else 0,'1'))


def _shift(points,dy=0,dx=0):return [(x+dx,y+dy) for x,y in points]


def peddler_palette(style):
    """Three greens2/3/4; throat5/6; eyes7; cloth8..11; brass12..14."""
    style=_style(style)
    skin={1:['#284038','#507848','#98b860','#a0b078','#d0d898','#f0e8b8'],
          2:['#204038','#488048','#88b858','#a0b070','#d0d890','#f0e8b0'],
          3:['#203840','#387868','#78a888','#90b8a0','#c0d8b8','#e8f0c8'],
          4:['#303828','#687040','#a0a858','#a0a068','#c8c888','#e8e0a8'],
          5:['#203c30','#487850','#88b878','#a0b878','#d0e0a0','#f0f0c0']}[style]
    # Every hex component is explicitly quantized to RGB555 below.
    cloth={1:['#302830','#504038','#806048','#b09060'],
           2:['#302830','#583828','#986038','#c09058'],
           3:['#202838','#304850','#507078','#88a098'],
           4:['#282828','#403828','#685840','#988060'],
           5:['#282038','#403048','#685078','#a088a8']}[style]
    colors=['#000000','#101820',*skin,*cloth,'#705030','#b08038','#e8c060','#f8e8b8']
    return [_q(c) for c in colors]


def wizard_palette(style):
    """Cloth uses2/3/4 only;1cavity;8..10staff;11hand;12..15flame."""
    style=_style(style)
    purple={1:['#282038','#604068','#a07098'],
            2:['#282038','#684078','#b078b8'],
            3:['#202840','#504878','#9890b8'],
            4:['#282030','#604058','#a07888'],
            5:['#282038','#684088','#b080c8']}[style]
    return [_q(c) for c in ['#000000','#101820',*purple,
            '#786850','#a09070','#c0b898','#483028','#906038','#d0a058',
            '#c8c098','#c85020','#f09828','#f8c858','#f8f0c0']]


def _q(color):
    return '#'+''.join('%02x'%(int(color[i:i+2],16)//8*8) for i in (1,3,5))


# Clean, final-size masks: eyes and jaw are the signature; three large green
# values describe forehead, cheek and far-side plane rather than ellipse rings.
HEADS={
1:(
'................',
'..2222....2222..',
'.233332..233332.',
'.237732..237732.',
'.23773222377332.',
'.23333333333332.',
'.24444333333332.',
'2344433333333332',
'2344333333333322',
'2333333333333222',
'.23111111111322.',
'..235555553322..',
'...2355555322...',
'....22222222....',
'................',
'................'),
2:(
'................',
'..2222..........',
'.233332...2222..',
'.237732..233332.',
'.237732..237732.',
'.23333222377332.',
'2344443333333332',
'2344433333333332',
'2333333333333322',
'2331111111133322',
'.23355555113322.',
'..235555511322..',
'...2355555322...',
'....22222222....',
'................',
'................'),
3:(
'................',
'................',
'..2222....2222..',
'.233332..233332.',
'.244332..244332.',
'.23773222377332.',
'..3333333333332.',
'.23443333333332.',
'.23443333333322.',
'..331111111332..',
'...3355555332...',
'....35555532....',
'.....222222.....',
'................',
'................',
'................'),
4:(
'................',
'................',
'.2222......2222.',
'233332....233332',
'2377322222237732',
'2333333333333332',
'2444433333333332',
'2344433333333322',
'2343333333333322',
'2311111111111322',
'2335555555553322',
'.23555555555322.',
'..235555555322..',
'...2222222222...',
'................',
'................'),
5:(
'................',
'.....111111.....',
'.....edddd1.....',
'..222ccccc2222..',
'.233332..233332.',
'.237732..237732.',
'.23773222377332.',
'..344433333332..',
'..344333333332..',
'..331111111332..',
'...3355555332...',
'....35555532....',
'.....222222.....',
'................',
'................',
'................')}
EYES={1:((3,3,5,4),(10,3,12,4)),2:((3,3,5,4),(10,4,12,5)),
      3:((3,5,5,5),(10,5,12,5)),4:((2,4,4,4),(11,4,13,4)),
      5:((3,5,5,6),(10,5,12,6))}


def peddler_head(style,name):
    style=_style(style)
    if name not in HEAD_FRAMES:raise ValueError(name)
    im,d=_new(16,16)
    for y,row in enumerate(HEADS[style]):
        assert len(row)==16
        for x,ink in enumerate(row):
            if ink!='.':im.putpixel((x,y),int(ink,16))
    for side,(x0,y0,x1,y1) in enumerate(EYES[style]):
        if name=='blink':
            d.rectangle((x0,y0,x1,y1),fill=3)
            d.line((x0,y1,x1,y1),fill=2)
            continue
        px=(x0+x1)//2+(-1 if name=='left' else 0)
        py=y1 if name=='down' or side and style in (1,2,5) else y0
        d.point((px,py),fill=1)
    if name=='grin':
        y={1:10,2:9,3:9,4:9,5:9}[style]
        left,right={1:(3,11),2:(3,12),3:(4,10),4:(2,13),5:(4,10)}[style]
        d.line([(left,y),(left+1,y+1),(right-1,y+1),(right,y)],fill=1)
        d.line((left+2,y+1,right-2,y+1),fill=7)
    elif name=='down':
        # One lowered jaw corner is a gesture, not a new face texture.
        x,y={1:(10,10),2:(11,9),3:(10,9),4:(12,9),5:(10,9)}[style]
        d.point((x,y+1),fill=1)
    return im


BODY_SHAPES={
1:{'outline':[(11,17),(20,17),(23,20),(24,25),(22,29),(19,30),(11,30),(8,27),(8,22)],
   'base':[(11,18),(19,18),(22,21),(23,25),(21,28),(18,29),(12,29),(9,26),(9,22)],
   'light':[(11,19),(13,18),(16,18),(14,21),(12,25),(10,25),(10,22)],
   'cloth':[(12,21),(19,21),(21,27),(18,29),(11,27)],'near':(9,24),'far':(23,24)},
2:{'outline':[(10,18),(20,18),(24,20),(26,24),(25,28),(21,30),(10,30),(6,27),(6,23)],
   'base':[(10,19),(20,19),(23,21),(25,24),(24,27),(20,29),(10,29),(7,26),(7,23)],
   'light':[(10,20),(14,19),(16,19),(14,23),(11,25),(8,24),(8,22)],
   'cloth':[(12,22),(19,22),(22,28),(18,30),(10,28)],'near':(7,24),'far':(25,24)},
3:{'outline':[(12,16),(18,17),(20,20),(21,25),(19,29),(15,30),(10,29),(9,25),(10,20)],
   'base':[(12,17),(17,18),(19,21),(20,25),(18,28),(15,29),(11,28),(10,25),(11,21)],
   'light':[(12,18),(14,18),(13,22),(12,26),(10,25),(11,21)],
   'cloth':[(13,21),(17,21),(19,28),(16,29),(12,28)],'near':(9,24),'far':(20,23)},
4:{'outline':[(9,18),(21,18),(25,21),(27,25),(25,28),(21,30),(10,30),(5,28),(4,24),(6,21)],
   'base':[(9,19),(21,19),(24,22),(26,25),(24,27),(21,29),(10,29),(6,27),(5,24),(7,22)],
   'light':[(8,21),(11,19),(16,19),(14,22),(10,25),(6,25),(6,23)],
   'cloth':[(11,22),(20,22),(22,28),(18,30),(10,28)],'near':(6,25),'far':(26,25)},
5:{'outline':[(12,18),(19,18),(22,21),(23,27),(20,30),(11,30),(9,27),(10,21)],
   'base':[(12,19),(18,19),(21,22),(22,26),(19,29),(12,29),(10,26),(11,22)],
   'light':[(12,20),(14,19),(15,20),(13,24),(11,25),(11,22)],
   'cloth':[(13,21),(18,21),(21,27),(18,29),(12,28)],'near':(10,24),'far':(22,24)}}


def _hand(d,x,y,left=False):
    d.polygon([(x-1,y-1),(x+1,y-1),(x+2,y),(x+1,y+2),(x-1,y+1)],fill=2)
    d.line((x-1,y,x+1,y),fill=4 if left else 3)


def peddler_body(style,name):
    style=_style(style)
    if name not in BODY_FRAMES:raise ValueError(name)
    im,d=_new(32,32);s=BODY_SHAPES[style]
    # Feet never leave the same baseline. Short filled shins join the haunch
    # and three-toed flipper; there are no detached horizontal sole fragments.
    lf,rf={1:(10,21),2:(8,23),3:(12,18),4:(7,24),5:(11,20)}[style]
    for x,direction in ((lf,-1),(rf,1)):
        d.polygon([(x-1,26),(x+2,26),(x+2,29),(x+3+direction,30),
                   (x+3+direction,31),(x-3+direction,31),(x-3+direction,30),(x-1,28)],fill=1)
        d.polygon([(x,27),(x+1,27),(x+1,30),(x+2+direction,30),
                   (x-2+direction,30),(x-1,29)],fill=3)
        d.line((x-1,29,x+direction,30),fill=4)
    compress=1 if name in ('tap2','slap','rub1','breathe') else 0
    lift=-1 if name=='lift' or name.startswith('spin') else compress
    def body_points(points):return [(x,y+lift if y<26 else y) for x,y in points]
    d.polygon(body_points(s['outline']),fill=1)
    d.polygon(body_points(s['base']),fill=3)
    d.polygon(body_points(s['light']),fill=4)
    # The far haunch is one grouped cool shadow, not a contour-following ring.
    right=max(x for x,y in s['base'])
    d.polygon([(right-2,22),(right,24),(right-1,27),(right-4,29),(right-5,27)],fill=2)
    d.polygon([(12,18+lift),(19,18+lift),(20,20+lift),(18,23+lift),(13,23+lift),(11,21+lift)],fill=5)
    d.line((13,19+lift,17,19+lift),fill=6)
    d.polygon(body_points(s['cloth']),fill=10)
    cp=body_points(s['cloth'])
    # One cloth shadow plane and one broad shoulder catch replace tiny
    # pockets, embroidery, buttons and the previous stack of apron borders.
    cx=sum(x for x,y in cp)//len(cp)
    d.polygon([(cx+1,22+lift),(cx+4,23+lift),(cx+5,27),(cx+1,29)],fill=9)
    if style in (1,2):
        d.line((12,21+lift,12,25+lift),fill=11)
    elif style==3:
        d.polygon([(12,20+lift),(14,21+lift),(13,26),(12,27)],fill=11)
    elif style==4:
        d.polygon([(11,24),(13,24),(12,28),(10,27)],fill=9)
    else:
        d.line((13,22+lift,13,26),fill=11)
        d.point((17,24),fill=12)
    lx,ly=s['near'];rx,ry=s['far']
    if name=='breathe':ly+=1;ry+=1
    elif name=='tap':ly-=1
    elif name=='tap2':ly-=2
    elif name=='lift' or name.startswith('spin'):ry=18
    elif name=='slap':rx,ry=23,26
    elif name in ('rub0','rub1'):
        lx,rx=14,18;ly=ry=22+compress
    la=(min(12,lx+2),20+lift);ra=(min(21,rx-2),20+lift)
    for start,end,left in ((la,(lx,ly),True),(ra,(rx,ry),False)):
        d.line([start,end],fill=1,width=3)
        d.line([start,end],fill=3 if left else 2,width=1)
        _hand(d,*end,left)
    if name.startswith('spin'):
        width={'9':5,'7':4,'5':3,'3':1}[name[4]]
        cy=11 if not name.endswith('b') else 13
        d.polygon([(rx-width//2,cy-1),(rx+width//2,cy-1),(rx+width//2,cy+1),
                   (rx-width//2,cy+1)],fill=12)
        d.line((rx-width//2,cy-1,rx+width//2,cy-1),fill=14)
        d.point((rx,cy),fill=13)
    elif name=='lift':
        d.rectangle((rx-1,ry-4,rx+1,ry-1),fill=13)
        d.line((rx-1,ry-4,rx+1,ry-4),fill=14)
    elif name=='slap':
        d.line((22,26,25,26),fill=13)
        d.point((22,25),fill=14)
    return im


WIZARD_SHAPES={
1:{'coat':[(10,15),(16,14),(20,17),(21,24),(20,28),(17,31),(8,31),(7,28),(8,22)],
   'base':[(10,17),(16,15),(19,18),(20,24),(18,28),(16,30),(9,30),(8,27),(9,22)],
   'light':[(10,17),(13,16),(13,21),(11,25),(9,28),(8,26)],
   'shade':[(17,17),(19,19),(20,24),(18,28),(16,30),(14,28),(16,23)],
   'hood':[(8,16),(8,11),(10,7),(13,5),(17,6),(19,9),(19,15),(17,19),(11,20)],
   'hoodbase':[(9,15),(9,11),(11,8),(13,6),(16,7),(18,10),(18,15),(16,18),(11,18)],
   'hoodlight':[(9,11),(11,8),(13,6),(15,7),(12,9),(11,13),(10,15)],
   'cavity':[(12,12),(14,10),(16,11),(17,14),(16,17),(12,17)]},
2:{'coat':[(9,16),(17,16),(20,19),(22,26),(20,30),(16,31),(7,31),(6,28),(7,22)],
   'base':[(9,17),(17,17),(19,20),(21,26),(19,29),(15,30),(8,30),(7,27),(8,22)],
   'light':[(9,18),(12,17),(13,20),(11,24),(9,29),(7,27)],
   'shade':[(17,19),(19,21),(21,26),(19,29),(16,30),(15,27)],
   'hood':[(7,16),(8,10),(11,6),(15,3),(21,3),(23,5),(20,6),(20,10),(21,16),(18,20),(11,20)],
   'hoodbase':[(8,15),(9,10),(12,7),(16,4),(20,4),(19,6),(19,10),(20,15),(17,18),(11,19)],
   'hoodlight':[(9,11),(12,7),(16,4),(19,4),(15,6),(12,10),(11,15)],
   'cavity':[(12,12),(15,10),(18,12),(18,16),(16,18),(12,17)]},
3:{'coat':[(11,16),(17,16),(20,19),(21,25),(22,30),(18,31),(9,31),(8,28),(9,23)],
   'base':[(11,17),(17,17),(19,20),(20,26),(21,29),(17,30),(10,30),(9,27),(10,23)],
   'light':[(11,18),(13,17),(14,19),(12,24),(11,28),(9,27)],
   'shade':[(17,19),(19,21),(20,26),(21,29),(17,30),(15,29),(16,24)],
   'hood':[(9,15),(9,10),(11,7),(14,5),(18,5),(21,8),(22,12),(21,17),(18,20),(12,20)],
   'hoodbase':[(10,15),(10,10),(12,8),(14,6),(17,6),(20,9),(21,12),(20,16),(17,19),(12,18)],
   'hoodlight':[(10,11),(12,8),(14,6),(17,6),(17,7),(13,9),(12,13)],
   'cavity':[(13,12),(15,10),(18,11),(19,14),(18,17),(15,18),(12,16)]},
4:{'coat':[(8,17),(15,16),(19,18),(21,23),(23,28),(21,29),(19,28),(17,31),(14,30),(11,31),(7,29),(5,29),(6,24)],
   'base':[(8,18),(15,17),(18,19),(20,23),(22,27),(19,27),(17,30),(14,29),(11,30),(8,28),(6,28),(7,24)],
   'light':[(8,19),(11,18),(13,18),(12,22),(9,26),(7,27),(6,26)],
   'shade':[(16,19),(18,20),(20,24),(22,27),(19,27),(17,30),(15,29),(14,26)],
   'hood':[(7,17),(7,12),(9,9),(12,7),(16,7),(19,9),(20,13),(22,17),(19,18),(17,21),(13,19),(10,20)],
   'hoodbase':[(8,16),(8,12),(10,10),(13,8),(16,8),(18,10),(19,13),(20,16),(18,17),(16,19),(13,18),(10,19)],
   'hoodlight':[(8,13),(10,10),(13,8),(15,8),(13,10),(11,13),(10,16)],
   'cavity':[(12,12),(15,11),(17,13),(18,16),(16,18),(12,17)]},
5:{'coat':[(11,15),(18,15),(20,19),(22,26),(23,30),(19,31),(8,31),(8,29),(9,23)],
   'base':[(11,16),(17,16),(19,20),(21,26),(22,29),(18,30),(9,30),(9,28),(10,23)],
   'light':[(11,17),(13,16),(14,18),(12,24),(11,28),(9,28)],
   'shade':[(17,18),(19,21),(21,26),(22,29),(18,30),(16,29),(16,24)],
   'hood':[(8,16),(9,11),(12,6),(15,2),(18,5),(21,9),(22,14),(20,19),(13,20)],
   'hoodbase':[(9,16),(10,11),(13,7),(15,3),(17,6),(20,10),(21,14),(19,18),(13,19)],
   'hoodlight':[(10,12),(13,7),(15,3),(16,6),(14,9),(12,14)],
   'cavity':[(13,12),(16,10),(18,12),(19,15),(17,18),(13,17)]}}


def wizard(style,name):
    style=_style(style)
    if name not in WIZARD_FRAMES:raise ValueError(name)
    im,d=_new(32,32);s=WIZARD_SHAPES[style]
    breath=name.startswith('breath');kindle=name.startswith('kindle')
    # Planted hem and boots; only upper cloth, hood and arm transfer weight.
    d.polygon(s['coat'],fill=1)
    d.polygon(s['base'],fill=3)
    d.polygon(s['shade'],fill=2)
    light=[(x,y+1 if breath and y<24 else y) for x,y in s['light']]
    d.polygon(light,fill=4)
    d.line((10,30,12,30),fill=8);d.line((17,30,19,30),fill=8)
    dy=1 if breath else 0
    for part,ink in (('hood',2),('hoodbase',3),('hoodlight',4),('cavity',1)):
        d.polygon(_shift(s[part],dy),fill=ink)
    if style in (1,2):
        d.polygon(_shift([(12,17),(16,18),(15,20),(13,19)],dy),fill=7)
    if 'blink' in name:
        # A closed/settling cowl changes the lip; no face or glowing eyes
        # emerge from the deliberately obscured hood.
        d.line((12,16+dy,16,17+dy),fill=2)
    if style==5:
        d.line((11,18+dy,12,22+dy),fill=10)
    elif style==4:
        d.line((7,26,8,28),fill=2)
    d.line([(26,8),(26,30)],fill=8,width=3)
    d.line([(26,9),(26,29)],fill=9)
    d.line((25,10,27,10),fill=10)
    if style==1:d.line((24,8,28,8),fill=9)
    elif style==2:d.line([(25,8),(28,8),(28,7)],fill=10)
    elif style==3:d.line([(24,8),(25,10),(27,10),(28,8)],fill=10)
    elif style==4:d.line([(25,8),(27,7),(27,9)],fill=9)
    else:d.line((24,8,28,8),fill=10);d.point((25,9),fill=11)
    hand_y=16 if kindle else 21 if breath else 22
    # The crossed arm has two deliberate segments and a clear gap below it.
    d.line([(19,19+dy),(22,hand_y+1),(25,hand_y)],fill=2,width=4)
    d.line([(19,19+dy),(22,hand_y),(24,hand_y)],fill=3,width=2)
    d.point((25,hand_y),fill=11)
    d.line([(10,20+dy),(8,24),(10,25)],fill=2,width=3)
    d.line([(10,20+dy),(9,23)],fill=4)
    d.point((10,25),fill=7)
    return im


FLAMES=(
('...c....','..cdd...','..dddc..','.cdddc..','.cdeedc.','.cdeedc.','..deec..','...ec...'),
('....c...','...ddc..','..dddc..','..ddedc.','.cdeedc.','.cdeedc.','..deec..','...ec...'),
('..c.....','..ddc...','..dddc..','.cddedc.','.cdeedc.','.cdeedc.','..deec..','...ec...'),
('...c....','...dc...','..dddc..','.cddedc.','.cdeedc.','.cdeedc.','..deec..','...ec...'))


def flame(style,name):
    style=_style(style)
    if name not in FLAME_FRAMES:raise ValueError(name)
    phase=FLAME_FRAMES.index(name);im,d=_new(8,8)
    for y,row in enumerate(FLAMES[phase]):
        for x,c in enumerate(row):
            if c!='.':im.putpixel((x,y),int(c,16))
    # Material identity varies by the tapered tongue, never by a wandering
    # orb. All bases touch the fixed shaft at bodyy8 across every frame.
    if style==2:
        d.point((1,2),fill=12);d.point((0,4),fill=12)
        if phase in (0,2):d.point((4,2),fill=14)
    elif style==3:
        for y in range(8):d.point((1,y),fill=0);d.point((6,y),fill=0)
        d.point((2,4),fill=14)
    elif style==4:
        d.line((6,2,6,3),fill=12)
        if phase==1:d.point((4,3),fill=12)
    elif style==5:
        d.point((6,4),fill=0);d.point((6,5),fill=0)
        d.point((1,5),fill=0)
    if style!=4:d.point((3,5),fill=15)
    else:d.point((3,6),fill=15)
    return im


def portrait(style,who):
    style=_style(style)
    if who in ('peddler','frog'):return _frog_portrait(style)
    if who in ('gatekeeper','wizard'):return _wizard_portrait(style)
    raise ValueError(who)


def _frog_portrait(style):
    im,d=_new(48,48)
    widths={1:(4,44),2:(1,46),3:(8,40),4:(1,46),5:(8,40)}
    left,right=widths[style]
    shoulder={1:[(5,47),(8,35),(16,30),(31,30),(40,35),(45,47)],
              2:[(1,47),(4,38),(12,32),(34,32),(43,37),(47,47)],
              3:[(11,47),(12,35),(18,30),(29,30),(35,36),(37,47)],
              4:[(0,47),(2,39),(11,32),(35,32),(45,39),(47,47)],
              5:[(8,47),(10,36),(18,31),(29,31),(37,37),(40,47)]}[style]
    d.polygon(shoulder,fill=2)
    d.polygon([(x+1 if x<24 else x-1,y if y==47 else y+1) for x,y in shoulder],fill=3)
    d.polygon([(8 if style!=3 else 13,38),(16,33),(21,34),(17,42),(14,47),(7 if style!=3 else 12,47)],fill=4)
    d.polygon([(29,35),(37 if style!=3 else 33,39),(40 if style!=3 else 35,47),(29,47)],fill=2)
    d.polygon([(17,29),(30,29),(33,36),(29,40),(17,40),(14,36)],fill=5)
    d.polygon([(18,31),(25,31),(24,35),(17,37),(16,35)],fill=6)
    apron={1:[(15,36),(30,36),(35,47),(11,47)],2:[(13,37),(31,37),(37,47),(9,47)],
           3:[(19,36),(29,36),(31,47),(16,47)],4:[(13,37),(33,37),(36,47),(10,47)],
           5:[(16,36),(30,36),(34,47),(13,47)]}[style]
    d.polygon(apron,fill=10)
    d.polygon([(27,38),(32,40),(35,47),(26,47)],fill=9)
    d.line((16,38,14,46),fill=11,width=2)
    if style==4:d.polygon([(13,44),(17,42),(18,46),(15,47)],fill=9)
    elif style==5:d.rectangle((25,41,26,42),fill=12)
    top={1:12,2:13,3:14,4:15,5:15}[style]
    chin={1:34,2:35,3:32,4:35,5:33}[style]
    face=[(left,top+5),(left+4,top),(right-5,top),(right,top+5),
          (right-2,chin-3),(right-7,chin),(left+7,chin),(left+2,chin-3)]
    d.polygon(face,fill=2)
    d.polygon([(left+2,top+5),(left+5,top+1),(right-6,top+1),(right-2,top+5),
               (right-4,chin-4),(right-8,chin-1),(left+8,chin-1),(left+3,chin-4)],fill=3)
    d.polygon([(left+3,top+6),(left+6,top+2),(24,top+2),(20,top+7),
               (left+10,top+10),(left+4,top+9)],fill=4)
    d.polygon([(right-10,top+5),(right-3,top+6),(right-4,chin-4),(right-8,chin-1),
               (24,chin-1),(28,chin-5)],fill=2)
    d.polygon([(left+8,chin-6),(right-8,chin-6),(right-9,chin-2),(left+9,chin-2)],fill=5)
    eyes={1:((6,3,18,17),(29,4,41,18)),2:((5,1,18,17),(30,7,42,20)),
          3:((10,7,21,20),(28,7,39,20)),4:((4,8,16,20),(31,9,43,21)),
          5:((9,7,20,20),(28,7,39,20))}[style]
    for side,(x0,y0,x1,y1) in enumerate(eyes):
        points=[(x0,y0+4),(x0+3,y0),(x1-3,y0),(x1,y0+4),(x1,y1-2),(x1-3,y1),(x0+3,y1),(x0,y1-3)]
        d.polygon(points,fill=2)
        d.polygon([(x0+2,y0+4),(x0+4,y0+2),(x1-3,y0+2),(x1-2,y0+4),
                   (x1-2,y1-3),(x1-4,y1-1),(x0+3,y1-2)],fill=7)
        if style==3:
            d.polygon([(x0+1,y0+2),(x1-2,y0+1),(x1-1,y0+6),(x0+2,y0+7)],fill=3)
            d.line((x0+3,y0+3,x1-4,y0+3),fill=4,width=2)
            py=y0+8
        else:py=(y0+y1)//2+(2 if side else 0)
        px=(x0+x1)//2+(-1 if side==0 else 1)
        d.rectangle((px,py,px+1,py+2),fill=1)
    mouth_y={1:27,2:27,3:27,4:28,5:27}[style]
    ml,mr={1:(12,35),2:(9,36),3:(15,34),4:(7,38),5:(15,33)}[style]
    d.line([(ml,mouth_y),(ml+5,mouth_y+2),(mr-3,mouth_y+2),(mr,mouth_y)],fill=1,width=2)
    if style in (1,2,5):
        d.polygon([(mr-7,mouth_y+2),(mr-2,mouth_y+2),(mr-3,mouth_y+6),(mr-6,mouth_y+5)],fill=1)
    if style==4:
        d.line((ml+4,mouth_y+3,mr-5,mouth_y+3),fill=5,width=2)
    if style==5:
        d.polygon([(17,2),(28,2),(31,5),(30,7),(15,7),(14,5)],fill=12)
        d.line((17,2,27,2),fill=14,width=2)
        d.line((13,8,34,8),fill=13,width=2)
    return im


def _wizard_portrait(style):
    im,d=_new(48,48)
    shoulders={1:[(2,47),(5,37),(13,29),(25,28),(34,33),(39,47)],
               2:[(1,47),(4,38),(11,31),(26,31),(35,36),(40,47)],
               3:[(6,47),(8,36),(15,28),(28,29),(35,37),(39,47)],
               4:[(0,47),(3,38),(11,32),(25,30),(34,34),(39,45),(35,47)],
               5:[(4,47),(7,35),(15,27),(28,27),(35,35),(39,47)]}[style]
    d.polygon(shoulders,fill=2)
    d.polygon([(x+2 if x<22 else x-2,y if y==47 else y+1) for x,y in shoulders],fill=3)
    light={1:[(7,38),(14,31),(18,30),(17,38),(11,47),(5,47)],
           2:[(6,39),(12,33),(17,33),(16,38),(9,47),(3,47)],
           3:[(10,37),(15,30),(19,30),(18,36),(12,45),(8,47)],
           4:[(5,39),(12,34),(16,33),(15,39),(10,44),(3,47)],
           5:[(9,36),(15,29),(19,28),(18,35),(13,44),(8,47)]}[style]
    d.polygon(light,fill=4)
    d.polygon([(26,32),(32,35),(36,43),(38,47),(27,47),(24,41)],fill=2)
    hood={1:[(7,28),(7,19),(11,11),(16,7),(22,6),(28,10),(32,16),(32,27),(27,34),(17,35)],
          2:[(5,28),(7,18),(12,10),(19,3),(30,1),(35,4),(29,7),(30,12),(33,20),(32,29),(26,35),(14,35)],
          3:[(8,27),(8,18),(12,11),(18,7),(25,7),(31,12),(35,20),(34,28),(29,35),(18,36),(11,33)],
          4:[(5,30),(5,22),(9,15),(14,10),(22,9),(28,12),(32,19),(35,29),(31,30),(29,36),(24,34),(20,37),(13,34)],
          5:[(7,29),(9,18),(14,10),(21,1),(27,8),(33,15),(35,25),(32,32),(26,36),(16,35)]}[style]
    d.polygon(hood,fill=2)
    interior=[(x+1 if x<22 else x-1,y+1 if y<31 else y-1) for x,y in hood]
    d.polygon(interior,fill=3)
    hlight={1:[(9,20),(13,13),(17,9),(22,8),(21,11),(15,15),(12,22),(10,28)],
            2:[(8,19),(13,12),(20,5),(29,3),(26,6),(21,9),(16,14),(12,23),(9,29)],
            3:[(10,19),(14,13),(19,9),(24,9),(24,11),(18,14),(15,20),(13,28)],
            4:[(7,23),(11,17),(15,12),(21,11),(19,14),(14,19),(11,26),(8,30)],
            5:[(10,20),(15,12),(21,3),(24,7),(21,12),(17,17),(14,25),(11,30)]}[style]
    d.polygon(hlight,fill=4)
    cavity={1:[(15,19),(19,15),(24,16),(27,21),(26,28),(22,31),(16,29)],
            2:[(14,20),(19,15),(25,17),(28,22),(26,29),(21,32),(15,29)],
            3:[(16,20),(21,16),(27,18),(30,23),(28,29),(23,33),(17,30),(14,26)],
            4:[(13,22),(18,17),(24,18),(27,23),(27,28),(22,33),(16,30)],
            5:[(16,21),(22,16),(27,19),(30,24),(28,30),(23,33),(17,30)]}[style]
    d.polygon(cavity,fill=1)
    if style in (1,2):
        d.polygon([(16,29),(20,30),(25,29),(24,33),(21,36),(18,33)],fill=7)
    if style==4:
        d.polygon([(6,42),(9,42),(8,47),(5,47)],fill=2)
    elif style==5:
        d.line((14,34,13,42),fill=10,width=2)
    # Clear staff-side negative space remains below and above the actual grip.
    d.line((41,13,41,47),fill=8,width=5)
    d.line((41,14,41,47),fill=9,width=3)
    d.line((39,16,43,16),fill=10)
    grip_y=34 if style!=2 else 36
    d.line([(30,34),(35,grip_y+2),(39,grip_y)],fill=2,width=6)
    d.line([(30,34),(35,grip_y+1),(38,grip_y)],fill=3,width=3)
    d.line((39,grip_y,41,grip_y-1),fill=11,width=2)
    d.polygon([(40,0),(43,4),(45,6),(46,9),(44,12),(41,14),(37,12),(36,9),(38,5)],fill=12)
    d.polygon([(40,3),(42,6),(44,8),(43,11),(40,12),(38,10),(38,7)],fill=13)
    d.polygon([(40,6),(42,8),(42,10),(40,11),(39,9)],fill=14)
    d.point((40,9),fill=15)
    return im


def rgba(image,palette):
    out=Image.new('RGBA',image.size)
    out.putdata([tuple(int(palette[i][n:n+2],16) for n in (1,3,5))+(255 if i else 0,) for i in image.tobytes()])
    return out


def _validate():
    for style in STYLE_NAMES:
        for pal in (peddler_palette(style),wizard_palette(style)):
            assert len(pal)==16 and all(int(c[n:n+2],16)%8==0 for c in pal for n in (1,3,5))
        for painter,frames,size in ((peddler_head,HEAD_FRAMES,(16,16)),(peddler_body,BODY_FRAMES,(32,32)),
                                    (wizard,WIZARD_FRAMES,(32,32)),(flame,FLAME_FRAMES,(8,8))):
            for frame in frames:
                im=painter(style,frame)
                assert im.mode=='P' and im.size==size and max(im.tobytes())<16,(style,frame)
        for who in ('peddler','wizard'):
            im=portrait(style,who)
            assert im.mode=='P' and im.size==(48,48) and max(im.tobytes())<16
        for frame in WIZARD_FRAMES:
            assert not set(wizard(style,frame).tobytes())&{13,14},'pulse reaches cloth'


def _world(style,who,phase=0):
    im,_=_new(32,32)
    if who=='peddler':
        # Same front-to-back compositing order and relative anchors as the ROM.
        _stamp(im,peddler_head(style,('open','open','blink','open')[phase]),(8,6+(phase in (1,2))))
        _stamp(im,peddler_body(style,('rest','breathe','breathe','rest')[phase]),(0,0))
    else:
        _stamp(im,flame(style,FLAME_FRAMES[phase]),FLAME_ORIGIN)
        _stamp(im,wizard(style,('idle','breath','breath_blink','idle')[phase]),(0,0))
    return im


def preview(out):
    """Source-only native/nearest-neighbour and shape/value review boards."""
    _validate();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
    board=Image.new('RGB',(1110,456),'#182028');d=ImageDraw.Draw(board)
    d.text((8,6),'NATIVE SOURCE / five newly authored shape and material studies / not emulator output',font=font,fill='#e0d8b0')
    for style in STYLE_NAMES:
        x=(style-1)*222
        d.text((x+8,30),str(style)+'. '+STYLE_NAMES[style],font=font,fill='#e0d8b0')
        for row,who in enumerate(('peddler','wizard')):
            pal=peddler_palette(style) if row==0 else wizard_palette(style)
            im=rgba(_world(style,who),pal)
            board.paste(im,(x+12,58+row*146),im)
            zoom=im.resize((128,128),Image.Resampling.NEAREST)
            board.paste(zoom,(x+65,54+row*146),zoom)
        for k,who in enumerate(('peddler','wizard')):
            pal=peddler_palette(style) if k==0 else wizard_palette(style)
            im=rgba(portrait(style,who),pal).resize((96,96),Image.Resampling.NEAREST)
            board.paste(im,(x+8+k*106,350),im)
    board.save(out/'npc-concepts.png')
    value=Image.new('RGB',(1110,250),'#b0b0a0');d=ImageDraw.Draw(value)
    d.text((8,6),'NATIVE SOURCE / silhouettes and three-value checks / 4x nearest neighbour',font=font,fill='#182028')
    for style in STYLE_NAMES:
        x=(style-1)*222
        for col,who in enumerate(('peddler','wizard')):
            im=rgba(_world(style,who),peddler_palette(style) if who=='peddler' else wizard_palette(style))
            alpha=im.getchannel('A')
            sil=Image.new('RGBA',im.size,'#182028');sil.putalpha(alpha)
            value.paste(sil.resize((96,96),Image.Resampling.NEAREST),(x+8+col*106,34),sil.resize((96,96),Image.Resampling.NEAREST))
            gray=im.convert('L').point(lambda v:40 if v<70 else 112 if v<150 else 216).convert('RGBA');gray.putalpha(alpha)
            gray=gray.resize((96,96),Image.Resampling.NEAREST)
            value.paste(gray,(x+8+col*106,142),gray)
    value.save(out/'silhouettes-and-values.png')
    for style in STYLE_NAMES:
        frames=[]
        for phase in range(4):
            scene=Image.new('RGB',(384,192),'#384848')
            for k,who in enumerate(('peddler','wizard')):
                im=rgba(_world(style,who,phase),peddler_palette(style) if k==0 else wizard_palette(style)).resize((160,160),Image.Resampling.NEAREST)
                scene.paste(im,(16+k*192,16),im)
            frames.append(scene)
        frames[0].save(out/f'idle-study-{style}.gif',save_all=True,append_images=frames[1:],duration=[250,150,250,150],loop=0,disposal=2)
    print('PASS five source NPC designs,150 world frames,10 portraits; source previews:',out)


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',default='/workspace/setup/sewer-concepts-v2/npcs')
    preview(ap.parse_args().out)
