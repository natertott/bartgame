"""Reference-led native frog Peddlers and flame-staff wizards.

Five related descendants of the preferred round frog and pointed purple cowl
share one lighting and pixel-cluster grammar.
Authoring starts on16px heads,32px bodies,8px flames and48px portraits. The
source2 silhouette/idle advice, Janes' directional form, and the material
and palette lessons in all six uploaded PDFs guide the deliberately broad
planes. No high-resolution drawing is resized into these production pixels.

The existing head/body anchors and frame identifiers are retained. Staff
shaft(26,8), flame origin(23,1), and reserved emissive indices13/14 are fixed.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

STYLE_NAMES={1:'Ashlar & Amber',2:'Crooked Brickwork',3:'Floodworn Flags',
             4:'Crumbling Vault',5:'Silted Cloister'}
PEDDLER_NAMES={1:'Puddle Prince',2:'Muddle',3:'Drowsy Droplet',
               4:'Old Puddle',5:'Little Puddle'}
WIZARD_NAMES={1:'Gilt Cowl',2:'Bowed Cowl',3:'Long Cowl',4:'Frayed Cowl',5:'Cloister Cowl'}
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
    """The liked warm-green frog's skin/apron family, with modest local shifts."""
    style=_style(style)
    skin={1:['#284038','#507848','#98b860','#a0b078','#d0d898','#f0e8b8'],
          2:['#284038','#587c48','#a0b868','#a8b078','#d8d898','#f0e8c0'],
          3:['#284038','#507850','#98b868','#a0b080','#d0d898','#f0e8b8'],
          4:['#303c30','#607848','#a0b060','#a8b078','#d0d090','#f0e8b8'],
          5:['#284038','#507c48','#a0c068','#a8b878','#d8e098','#f8f0c0']}[style]
    cloth={1:['#302830','#504038','#806048','#b09060'],
           2:['#302828','#583c30','#886048','#b89868'],
           3:['#282830','#484038','#786048','#a89068'],
           4:['#302830','#504030','#785840','#a08860'],
           5:['#302830','#584038','#886848','#b89868']}[style]
    return [_q(c) for c in ['#000000','#101820',*skin,*cloth,
                           '#705030','#b08038','#e8c060','#f8e8b8']]


def wizard_palette(style):
    """All five retain the preferred pointed wizard's purple/black identity.

    Emissive13/14 are reserved for flame, never cloth or staff.
    """
    style=_style(style)
    purple={1:['#282038','#684088','#b080c8'],
            2:['#282038','#704888','#b888c8'],
            3:['#282040','#604080','#a880c0'],
            4:['#282038','#684080','#b080b8'],
            5:['#302038','#704888','#b888c8']}[style]
    return [_q(c) for c in ['#000000','#101820',*purple,
            '#786850','#a09070','#c0b898','#483028','#906038','#d0a058',
            '#c8c098','#c85020','#f09828','#f8c858','#f8f0c0']]


def _q(color):
    return '#'+''.join('%02x'%(int(color[i:i+2],16)//8*8) for i in (1,3,5))


# Native16px head silhouettes. All retain the preferred #1 eye-lobes and
# heavy jaw; structural proportions/eyelids vary before any surface detail.
FROG_HEADS={
1:{'outline':[(2,1),(5,1),(7,4),(9,4),(11,1),(14,1),(15,4),(14,7),(15,10),(13,13),(10,14),(5,14),(2,13),(0,10),(1,7),(1,3)],
   'face':[(2,4),(6,4),(8,5),(11,4),(14,4),(13,7),(14,10),(12,12),(10,13),(5,13),(2,11),(1,9)],
   'light':[(2,6),(6,5),(9,6),(7,8),(3,9),(1,8)],
   'eyes':[(3,2,5,4),(11,2,13,4)],'mouth':[(3,10),(10,10),(11,11),(10,12)],
   'jaw':[(4,11),(9,11),(9,13),(5,13)]},
2:{'outline':[(2,0),(5,0),(7,4),(9,5),(11,2),(14,2),(15,5),(14,7),(15,11),(12,14),(5,14),(2,13),(0,10),(1,5),(1,2)],
   'face':[(2,4),(6,4),(8,6),(11,5),(14,5),(13,8),(14,11),(11,13),(5,13),(2,11),(1,9)],
   'light':[(2,6),(6,5),(8,7),(6,9),(2,9),(1,8)],
   'eyes':[(3,1,5,3),(11,3,13,5)],'mouth':[(3,10),(8,11),(11,10),(12,11)],
   'jaw':[(4,11),(10,12),(9,13),(5,13)]},
3:{'outline':[(3,1),(6,1),(7,4),(10,4),(11,1),(14,1),(15,4),(14,7),(14,11),(12,14),(6,14),(3,13),(1,10),(1,6),(2,3)],
   'face':[(3,4),(6,5),(10,5),(13,4),(14,6),(13,9),(13,11),(11,13),(6,13),(3,11),(2,8)],
   'light':[(3,6),(6,5),(9,6),(7,8),(3,9),(2,8)],
   'eyes':[(4,3,6,4),(11,3,13,4)],'mouth':[(4,10),(11,10),(11,11),(10,11)],
   'jaw':[(5,11),(10,11),(10,13),(6,13)]},
4:{'outline':[(1,2),(4,1),(6,3),(7,5),(10,5),(11,2),(14,2),(15,5),(14,7),(15,10),(14,12),(11,14),(4,14),(1,12),(0,9),(0,5)],
   'face':[(2,5),(5,5),(8,6),(11,5),(14,5),(13,8),(14,10),(12,12),(10,13),(4,13),(1,10),(1,7)],
   'light':[(2,7),(5,6),(8,7),(6,9),(2,9),(1,8)],
   'eyes':[(2,3,4,5),(11,3,13,5)],'mouth':[(2,10),(5,11),(10,11),(12,10)],
   'jaw':[(4,12),(10,12),(10,13),(5,13)]},
5:{'outline':[(3,1),(6,1),(7,4),(9,4),(10,1),(13,1),(15,4),(14,7),(14,10),(12,13),(9,14),(6,14),(3,13),(1,10),(1,7),(1,4)],
   'face':[(3,4),(6,4),(8,5),(11,4),(13,4),(13,7),(13,10),(11,12),(9,13),(6,13),(3,11),(2,8)],
   'light':[(3,6),(6,5),(9,6),(7,8),(3,9),(2,8)],
   'eyes':[(3,2,5,4),(11,2,13,4)],'mouth':[(4,10),(10,10),(11,11),(10,12)],
   'jaw':[(5,11),(9,11),(9,13),(6,13)]}}


def peddler_head(style,name):
    style=_style(style)
    if name not in HEAD_FRAMES:raise ValueError(name)
    im,d=_new(16,16);s=FROG_HEADS[style]
    d.polygon(s['outline'],fill=2)
    d.polygon(s['face'],fill=3)
    d.polygon(s['light'],fill=4)
    d.polygon(s['jaw'],fill=5)
    for side,(x0,y0,x1,y1) in enumerate(s['eyes']):
        if name=='blink':
            d.line((x0,y1,x1,y1),fill=2)
            continue
        d.rectangle((x0,y0,x1,y1),fill=7)
        # Large eyes carry the expression; the asymmetry is deliberate.
        px=x0+(0 if name=='left' else 1)
        py=y1 if name=='down' or side else y0+1
        d.point((px,py),fill=1)
        if style==3 and name!='down':
            d.line((x0,y0,x1,y0),fill=3)
    if name=='grin':
        ml={1:3,2:3,3:4,4:2,5:4}[style]
        mr={1:12,2:12,3:11,4:13,5:11}[style]
        d.line([(ml,10),(ml+1,11),(mr-1,11),(mr,10)],fill=1)
        d.line((ml+2,11,mr-2,11),fill=7)
    else:
        d.line(s['mouth'],fill=1)
        if name=='down':d.point((s['mouth'][-1][0],12),fill=1)
    return im


BODY_SHAPES={
1:{'outline':[(11,17),(20,17),(23,20),(24,25),(22,29),(19,30),(11,30),(8,27),(8,22)],
   'base':[(11,18),(19,18),(22,21),(23,25),(21,28),(18,29),(12,29),(9,26),(9,22)],
   'light':[(11,19),(13,18),(16,18),(14,21),(12,25),(10,25),(10,22)],
   'cloth':[(12,21),(19,21),(20,27),(18,29),(11,27)],'near':(9,24),'far':(23,24)},
2:{'outline':[(10,18),(20,17),(23,19),(25,23),(25,27),(22,30),(10,30),(7,27),(7,22)],
   'base':[(10,19),(20,18),(22,20),(24,23),(24,26),(21,29),(11,29),(8,26),(8,22)],
   'light':[(10,20),(14,19),(16,19),(14,22),(11,25),(9,25),(8,23)],
   'cloth':[(12,22),(20,21),(22,27),(19,29),(11,28)],'near':(8,24),'far':(24,23)},
3:{'outline':[(11,18),(19,18),(22,21),(23,26),(21,29),(18,30),(11,30),(9,27),(9,22)],
   'base':[(11,19),(18,19),(21,22),(22,26),(20,28),(17,29),(12,29),(10,26),(10,22)],
   'light':[(11,20),(14,19),(16,20),(14,23),(12,26),(10,25),(10,22)],
   'cloth':[(13,22),(18,22),(20,28),(17,29),(12,28)],'near':(9,25),'far':(22,25)},
4:{'outline':[(10,18),(20,18),(24,21),(26,25),(24,28),(21,30),(10,30),(6,28),(6,23)],
   'base':[(10,19),(20,19),(23,22),(25,25),(23,27),(20,29),(11,29),(7,27),(7,23)],
   'light':[(9,21),(12,19),(16,19),(14,22),(11,25),(8,25),(7,23)],
   'cloth':[(12,22),(20,22),(21,27),(18,29),(15,28),(11,29)],'near':(7,25),'far':(25,25)},
5:{'outline':[(12,17),(19,17),(22,20),(23,25),(21,29),(18,30),(12,30),(9,27),(10,21)],
   'base':[(12,18),(18,18),(21,21),(22,25),(20,28),(17,29),(12,29),(10,26),(11,22)],
   'light':[(12,19),(14,18),(16,19),(14,22),(12,25),(11,25),(11,22)],
   'cloth':[(13,21),(18,21),(20,27),(17,29),(12,27)],'near':(10,24),'far':(22,24)}}


def _hand(d,x,y,left=False):
    d.polygon([(x-1,y-1),(x+1,y-1),(x+2,y),(x+1,y+2),(x-1,y+1)],fill=2)
    d.line((x-1,y,x+1,y),fill=4 if left else 3)


def peddler_body(style,name):
    style=_style(style)
    if name not in BODY_FRAMES:raise ValueError(name)
    im,d=_new(32,32);s=BODY_SHAPES[style]
    # Feet never leave the same baseline. Short filled shins join the haunch
    # and three-toed flipper; there are no detached horizontal sole fragments.
    lf,rf={1:(10,21),2:(9,22),3:(11,20),4:(8,23),5:(11,20)}[style]
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


# Every cowl descends from the selected tall pointed #5, rather than
# replacing the character with unrelated hats, faces or coloured costumes.
WIZARD_SHAPES={
1:{'coat':[(11,15),(18,15),(20,19),(22,26),(23,30),(19,31),(8,31),(8,29),(9,23)],
   'base':[(11,16),(17,16),(19,20),(21,26),(22,29),(18,30),(9,30),(9,28),(10,23)],
   'light':[(11,17),(13,16),(14,18),(12,24),(11,28),(9,28)],
   'shade':[(17,18),(19,21),(21,26),(22,29),(18,30),(16,29),(16,24)],
   'hood':[(8,16),(9,11),(12,6),(15,2),(18,5),(21,9),(22,14),(20,19),(13,20)],
   'hoodbase':[(9,16),(10,11),(13,7),(15,3),(17,6),(20,10),(21,14),(19,18),(13,19)],
   'hoodlight':[(10,12),(13,7),(15,3),(16,6),(14,9),(12,14)],
   'cavity':[(13,12),(16,10),(18,12),(19,15),(17,18),(13,17)]},
2:{'coat':[(10,16),(18,16),(20,20),(22,26),(23,29),(20,31),(8,31),(7,29),(8,23)],
   'base':[(10,17),(17,17),(19,21),(21,26),(22,29),(19,30),(9,30),(8,28),(9,23)],
   'light':[(10,18),(13,17),(14,20),(12,24),(10,29),(8,28)],
   'shade':[(17,19),(19,22),(21,27),(21,29),(19,30),(16,29),(15,25)],
   'hood':[(7,17),(8,11),(11,6),(15,2),(19,2),(21,4),(18,5),(20,10),(21,16),(19,20),(12,21)],
   'hoodbase':[(8,17),(9,11),(12,7),(16,3),(18,3),(17,5),(19,11),(20,15),(18,19),(12,20)],
   'hoodlight':[(9,12),(12,7),(16,3),(18,3),(15,6),(13,10),(11,16)],
   'cavity':[(12,13),(15,11),(18,13),(18,17),(16,19),(12,18)]},
3:{'coat':[(11,16),(17,16),(19,20),(20,25),(22,30),(19,31),(9,31),(8,29),(9,23)],
   'base':[(11,17),(16,17),(18,21),(19,26),(21,29),(18,30),(10,30),(9,28),(10,23)],
   'light':[(11,18),(13,17),(14,19),(12,25),(11,29),(9,28)],
   'shade':[(16,19),(18,22),(19,26),(21,29),(18,30),(16,29),(15,25)],
   'hood':[(9,16),(9,11),(12,6),(16,0),(18,4),(20,9),(21,15),(19,19),(13,20)],
   'hoodbase':[(10,16),(10,11),(13,7),(16,2),(17,5),(19,10),(20,14),(18,18),(13,19)],
   'hoodlight':[(10,13),(13,7),(16,2),(16,6),(14,10),(12,15)],
   'cavity':[(13,12),(15,10),(17,11),(18,15),(16,18),(13,17)]},
4:{'coat':[(10,16),(17,16),(20,20),(22,26),(23,29),(21,30),(19,29),(17,31),(14,30),(11,31),(7,30),(8,24)],
   'base':[(10,17),(17,17),(19,21),(21,26),(22,28),(19,28),(17,30),(14,29),(11,30),(8,29),(9,24)],
   'light':[(10,18),(13,17),(14,20),(12,24),(10,28),(8,28)],
   'shade':[(17,19),(19,22),(21,26),(22,28),(19,28),(17,30),(15,28),(15,24)],
   'hood':[(7,17),(8,11),(11,6),(14,2),(17,4),(20,9),(21,15),(20,18),(18,20),(15,19),(12,21)],
   'hoodbase':[(8,17),(9,11),(12,7),(14,3),(16,5),(19,10),(20,14),(19,17),(17,19),(15,18),(12,20)],
   'hoodlight':[(9,13),(12,7),(14,3),(15,6),(13,10),(11,16)],
   'cavity':[(12,13),(15,10),(17,12),(18,16),(16,18),(13,18)]},
5:{'coat':[(10,16),(18,16),(21,20),(23,27),(23,30),(19,31),(8,31),(7,28),(8,23)],
   'base':[(10,17),(17,17),(20,21),(22,27),(22,29),(18,30),(9,30),(8,28),(9,23)],
   'light':[(10,18),(13,17),(14,20),(12,24),(10,28),(8,27)],
   'shade':[(17,19),(20,22),(22,27),(22,29),(18,30),(16,28),(16,24)],
   'hood':[(7,17),(8,11),(11,7),(14,3),(17,5),(21,10),(22,15),(20,20),(13,21)],
   'hoodbase':[(8,17),(9,11),(12,8),(14,4),(16,6),(20,11),(21,15),(19,19),(13,20)],
   'hoodlight':[(9,13),(12,8),(14,4),(15,7),(13,11),(11,16)],
   'cavity':[(12,13),(15,11),(18,13),(19,16),(17,19),(13,18)]}}


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
    if 'blink' in name:
        # A closed/settling cowl changes the lip; no face or glowing eyes
        # emerge from the deliberately obscured hood.
        d.line((12,16+dy,16,17+dy),fill=2)
    if style in (1,5):
        d.line((11,19+dy,12,22+dy),fill=10)
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
('...c....','..cdd...','..dddc..','.cdddc..','.cdedc..','.cdeedc.','..deec..','...ec...'),
('....c...','...dd...','..cddc..','..dddc..','.cdeedc.','.cdeedc.','..deec..','...ec...'),
('..c.....','..ddc...','..dddc..','.cdddc..','.cdeedc.','.cdeedc.','..deec..','...ec...'),
('...c....','...dc...','..cddc..','.cdddc..','.cdedc..','.cdeedc.','..deec..','...ec...'))


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


# Busts are separately authored at48px. They retain the world eye/hood
# proportions and the same quiet apron/robe identity; no scaled sprite pixels.
FROG_BUSTS={
1:{'shoulder':[(4,47),(7,37),(15,32),(31,32),(40,37),(44,47)],
   'face':[(4,16),(8,11),(36,11),(43,16),(43,27),(39,33),(31,36),(15,36),(7,32),(3,26)],
   'eyes':[(7,3,18,18),(30,3,41,18)],'mouth':[(11,27),(31,27),(34,28),(33,32)],
   'jaw':[(14,29),(29,29),(30,34),(17,35)]},
2:{'shoulder':[(2,47),(5,38),(14,32),(32,32),(42,37),(46,47)],
   'face':[(3,16),(7,11),(36,13),(44,18),(43,28),(38,34),(31,36),(14,36),(6,32),(2,25)],
   'eyes':[(6,1,18,17),(30,6,42,21)],'mouth':[(10,27),(23,29),(34,27),(36,29)],
   'jaw':[(13,30),(29,31),(29,35),(16,35)]},
3:{'shoulder':[(7,47),(9,38),(16,32),(30,32),(37,38),(41,47)],
   'face':[(7,16),(11,11),(34,11),(40,17),(39,28),(35,34),(28,36),(17,36),(11,33),(6,26)],
   'eyes':[(10,4,21,19),(29,4,40,19)],'mouth':[(14,28),(32,28),(33,30),(30,31)],
   'jaw':[(17,30),(29,30),(29,35),(19,35)]},
4:{'shoulder':[(0,47),(4,38),(13,33),(33,33),(44,39),(47,47)],
   'face':[(2,17),(7,13),(36,13),(44,18),(45,26),(41,32),(33,36),(13,36),(5,32),(1,25)],
   'eyes':[(4,6,16,20),(31,7,43,21)],'mouth':[(8,27),(15,30),(30,30),(37,27)],
   'jaw':[(13,32),(31,32),(30,35),(16,35)]},
5:{'shoulder':[(6,47),(8,37),(17,31),(29,31),(38,38),(42,47)],
   'face':[(6,16),(11,11),(34,11),(41,16),(40,28),(35,34),(28,36),(17,36),(10,33),(5,27)],
   'eyes':[(8,3,20,18),(29,3,41,18)],'mouth':[(14,27),(30,27),(33,29),(31,32)],
   'jaw':[(17,30),(28,30),(28,35),(19,35)]}}


def _frog_portrait(style):
    im,d=_new(48,48);s=FROG_BUSTS[style]
    d.polygon(s['shoulder'],fill=2)
    d.polygon([(x+1 if x<24 else x-1,y if y==47 else y+1)
               for x,y in s['shoulder']],fill=3)
    d.polygon([(8,40),(15,34),(21,34),(17,43),(14,47),(6,47)],fill=4)
    d.polygon([(29,35),(37,40),(40,47),(29,47)],fill=2)
    d.polygon([(17,33),(29,33),(32,38),(29,41),(17,41),(14,38)],fill=5)
    d.polygon([(18,35),(25,35),(24,38),(17,39)],fill=6)
    apron={1:[(15,38),(30,38),(34,47),(11,47)],
           2:[(14,39),(31,37),(36,47),(10,47)],
           3:[(18,38),(29,38),(32,47),(14,47)],
           4:[(14,39),(31,39),(34,46),(29,47),(25,46),(20,47),(11,47)],
           5:[(17,37),(29,37),(33,47),(13,47)]}[style]
    d.polygon(apron,fill=10)
    d.polygon([(27,40),(31,41),(34,47),(27,47)],fill=9)
    d.line((17,40,15,46),fill=11,width=2)
    d.polygon(s['face'],fill=2)
    d.polygon([(x+1 if x<23 else x-1,y+1 if y<26 else y-1)
               for x,y in s['face']],fill=3)
    d.polygon([(7,20),(13,14),(23,14),(22,18),(17,22),(7,24)],fill=4)
    d.polygon([(33,17),(41,20),(40,28),(36,32),(28,34),(29,28)],fill=2)
    d.polygon(s['jaw'],fill=5)
    for side,(x0,y0,x1,y1) in enumerate(s['eyes']):
        points=[(x0,y0+4),(x0+3,y0),(x1-3,y0),(x1,y0+4),
                (x1,y1-3),(x1-3,y1),(x0+3,y1),(x0,y1-3)]
        d.polygon(points,fill=2)
        d.polygon([(x0+2,y0+4),(x0+4,y0+2),(x1-3,y0+2),
                   (x1-2,y0+4),(x1-2,y1-3),(x1-4,y1-1),(x0+3,y1-2)],fill=7)
        if style==3:
            d.polygon([(x0+1,y0+2),(x1-2,y0+1),(x1-1,y0+6),(x0+2,y0+7)],fill=3)
            d.line((x0+3,y0+3,x1-4,y0+3),fill=4,width=2)
        px=(x0+x1)//2+(-1 if side==0 else 1)
        py=(y0+y1)//2+(2 if side else 0)
        d.rectangle((px,py,px+1,py+2),fill=1)
    d.line(s['mouth'],fill=1,width=2)
    return im


WIZARD_BUSTS={
1:{'shoulder':[(4,47),(7,35),(15,27),(28,27),(35,35),(39,47)],
   'light':[(9,36),(15,29),(19,28),(18,35),(13,44),(8,47)],
   'hood':[(7,29),(9,18),(14,10),(21,1),(27,8),(33,15),(35,25),(32,32),(26,36),(16,35)],
   'light_hood':[(10,20),(15,12),(21,3),(24,7),(21,12),(17,17),(14,25),(11,30)],
   'face':[(16,21),(22,16),(27,19),(30,24),(28,30),(23,33),(17,30)]},
2:{'shoulder':[(2,47),(5,37),(14,29),(28,29),(36,36),(40,47)],
   'light':[(7,38),(14,31),(19,30),(18,36),(11,46),(5,47)],
   'hood':[(5,30),(7,19),(12,10),(19,2),(28,1),(33,4),(28,7),(30,14),(33,23),(32,31),(26,37),(15,36)],
   'light_hood':[(8,21),(13,12),(21,4),(28,3),(25,7),(19,12),(14,20),(10,30)],
   'face':[(14,23),(20,18),(26,21),(28,27),(26,32),(21,34),(15,32)]},
3:{'shoulder':[(6,47),(9,35),(16,28),(27,28),(33,35),(38,47)],
   'light':[(11,36),(17,30),(20,29),(18,36),(14,45),(10,47)],
   'hood':[(9,29),(10,18),(15,10),(24,0),(27,7),(31,15),(33,25),(30,33),(24,36),(17,35)],
   'light_hood':[(12,21),(17,12),(24,3),(24,9),(20,15),(17,22),(15,29)],
   'face':[(17,21),(22,16),(26,19),(28,26),(25,31),(21,33),(17,30)]},
4:{'shoulder':[(2,47),(6,36),(14,29),(27,29),(35,36),(40,46),(36,47),(33,45),(29,47),(26,46),(20,47)],
   'light':[(8,37),(15,31),(18,30),(17,36),(12,44),(7,46)],
   'hood':[(5,30),(7,20),(12,11),(19,2),(25,7),(31,15),(33,25),(31,31),(28,35),(24,34),(20,37),(15,35)],
   'light_hood':[(9,22),(14,13),(19,4),(22,8),(19,14),(15,20),(12,30)],
   'face':[(14,23),(20,17),(25,20),(28,27),(25,32),(21,34),(16,32)]},
5:{'shoulder':[(1,47),(5,36),(13,29),(28,29),(37,36),(41,47)],
   'light':[(7,37),(14,31),(19,30),(17,37),(11,45),(5,46)],
   'hood':[(5,30),(7,20),(12,12),(19,4),(26,9),(33,17),(35,27),(31,35),(25,38),(15,36)],
   'light_hood':[(9,23),(14,14),(19,6),(22,10),(19,16),(15,23),(12,31)],
   'face':[(14,24),(20,19),(26,22),(29,28),(26,34),(21,35),(16,33)]}}


def _wizard_portrait(style):
    im,d=_new(48,48);s=WIZARD_BUSTS[style]
    d.polygon(s['shoulder'],fill=2)
    d.polygon([(x+1 if x<22 else x-1,y if y==47 else y+1)
               for x,y in s['shoulder']],fill=3)
    d.polygon(s['light'],fill=4)
    d.polygon([(26,32),(32,36),(36,43),(38,47),(27,47),(24,41)],fill=2)
    d.polygon(s['hood'],fill=2)
    d.polygon([(x+1 if x<22 else x-1,y+1 if y<31 else y-1)
               for x,y in s['hood']],fill=3)
    d.polygon(s['light_hood'],fill=4)
    d.polygon(s['face'],fill=1)
    if style in (1,5):d.line((14,35,13,42),fill=10,width=2)
    elif style==4:d.line([(9,40),(8,43),(6,44)],fill=2,width=2)
    # Staff is fixed at the same hand side as the world sprite; a genuine
    # negative-space gap remains above and below the grip.
    d.line((41,13,41,47),fill=8,width=5)
    d.line((41,14,41,47),fill=9,width=3)
    d.line((39,16,43,16),fill=10)
    grip_y={1:34,2:36,3:34,4:35,5:36}[style]
    d.line([(30,34),(35,grip_y+2),(39,grip_y)],fill=2,width=6)
    d.line([(30,34),(35,grip_y+1),(38,grip_y)],fill=3,width=3)
    d.line((39,grip_y,41,grip_y-1),fill=11,width=2)
    # Fire has a continuous base and a tapered active tip, never loose sparks.
    tongue={1:[(40,0),(43,4),(45,7),(45,10),(42,14),(38,13),(36,10),(37,6)],
            2:[(42,0),(42,4),(45,7),(45,10),(42,14),(38,13),(36,10),(38,5)],
            3:[(40,0),(42,5),(44,7),(44,11),(41,14),(38,12),(37,9),(38,5)],
            4:[(39,0),(42,5),(44,5),(45,9),(43,13),(39,14),(36,11),(37,6)],
            5:[(41,0),(43,5),(45,7),(45,10),(42,14),(38,13),(36,10),(38,5)]}[style]
    d.polygon(tongue,fill=12)
    d.polygon([(40,4),(42,6),(44,8),(43,11),(40,13),(38,11),(38,8)],fill=13)
    d.polygon([(40,7),(42,8),(42,11),(40,12),(39,10)],fill=14)
    d.line((40,9,40,11),fill=15)
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
    ap.add_argument('--out',default='/workspace/setup/sewer-concepts-v3/npcs')
    preview(ap.parse_args().out)
