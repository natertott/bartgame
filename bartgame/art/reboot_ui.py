"""One native gilt-and-rot interface vocabulary.

Literal pixel geometry at final size. Shared RGB555 inks, no imported graphic,
image resampling, antialiasing or generated high-resolution source.
"""
from PIL import Image,ImageDraw
import reboot_core as C
import ui_font as F

KEYS=['o','1','2','3','4','y','Y','G','W','c','s','h','r','p','b']
UI_HEX=[C.PALETTES['ui'][i] for i in (1,2,2,3,4,5,6,7,9,8,5,9,12,8,1)]
# Warm cream lettering stays distinct from the high ivory highlight.
UI_HEX[9]=C.PALETTES['stone'][8]
UI_HEX[10]=C.PALETTES['stone'][6]
UI_HEX[14]=C.PALETTES['gold'][2]
PAL=list(zip(KEYS,[C.rgb(h) for h in UI_HEX]));INDEX={k:i+1 for i,k in enumerate(KEYS)};RGB=dict(PAL)
TEXT={'cream':'c','dim':'s','high':'h','red':'r','gold':'G','ink':'b','dark':'o'}
MAP_KEYS=['o','n','N','k','g','G','L','w','W','b','v','V','U','y','c']
MAP_HEX=[C.PALETTES['ui'][1],C.PALETTES['ui'][2],C.PALETTES['ui'][3],
 C.PALETTES['foliage'][2],C.PALETTES['foliage'][4],C.PALETTES['foliage'][6],C.PALETTES['ground'][15],
 C.PALETTES['water'][4],C.PALETTES['water'][7],C.PALETTES['gold'][5],C.PALETTES['blight'][5],
 C.PALETTES['blight'][7],C.PALETTES['stone'][4],C.PALETTES['gold'][10],C.PALETTES['stone'][8]]
MAP_PAL=list(zip(MAP_KEYS,[C.rgb(h) for h in MAP_HEX]));MAP_INDEX={k:i+1 for i,k in enumerate(MAP_KEYS)};MAP_RGB=dict(MAP_PAL)
HUD_KEYS=['o','2','3','4','R','r','q','W','c','s','g','G','b','h','n']
HUD_HEX=[C.PALETTES['ui'][1],C.PALETTES['ui'][2],C.PALETTES['ui'][3],C.PALETTES['stone'][5],
 C.PALETTES['hero'][2],C.PALETTES['hero'][3],C.PALETTES['hero'][4],C.PALETTES['ui'][9],
 C.PALETTES['stone'][8],C.PALETTES['stone'][6],C.PALETTES['gold'][7],C.PALETTES['gold'][10],
 C.PALETTES['gold'][3],C.PALETTES['gold'][11],C.PALETTES['ui'][2]]
HUD_PAL=list(zip(HUD_KEYS,[C.rgb(h) for h in HUD_HEX]));HUD_INDEX={k:i+1 for i,k in enumerate(HUD_KEYS)}
OBJ_PAL=[(k,MAP_RGB['g'] if k=='p' else MAP_RGB['G'] if k=='b' else col) for k,col in PAL]
def hexpal(p):return ['#000000']+['#%02x%02x%02x'%v for _,v in p]
GROUPS={'menu':hexpal(PAL),'map':hexpal(MAP_PAL),'hud':hexpal(HUD_PAL),
        'uikit':hexpal(OBJ_PAL),'ui':hexpal(OBJ_PAL),'portrait':C.PALETTES['hero']}
for pal in GROUPS.values():assert len(pal)==16 and all(all(v%8==0 for v in C.rgb(h)) for h in pal)


def image(w=8,h=8,fill=0):
    im=Image.new('P',(w,h),fill);return im,ImageDraw.Draw(im)
def hexrows(im):return [''.join('%x'%im.getpixel((x,y)) for x in range(im.width)) for y in range(im.height)]
def letters(im,keys=KEYS):return [''.join('.' if not im.getpixel((x,y)) else keys[im.getpixel((x,y))-1] for x in range(im.width)) for y in range(im.height)]
def glyph(d,x,y,ch,ink,scale=1):
    _,rs=F.glyph(ch)
    for yy,row in enumerate(rs):
        for xx,v in enumerate(row):
            if v=='#':d.rectangle((x+xx*scale,y+yy*scale,x+(xx+1)*scale-1,y+(yy+1)*scale-1),fill=ink)
def text(d,x,y,s,ink,scale=1):
    for ch in s:
        glyph(d,x,y,ch,ink,scale);x+=(3 if ch==' ' else F.glyph(ch)[0]+1)*scale
    return x

def frame_tile(part,selected=False,empty=False,hud=False,bubble=False):
    im,d=image(fill=0 if empty or part.endswith('_tl') else INDEX['p'] if bubble else INDEX['3'] if part.startswith(('slot','row')) else INDEX['2'])
    edge=INDEX['G'] if selected else INDEX['Y'] if not part.startswith(('slot','row')) else INDEX['4']
    dark=INDEX['o'];light=INDEX['W'] if selected else INDEX['G']
    if part.endswith('_tl'):
        if empty:
            d.line([(2,1),(5,1)],fill=INDEX['s']);d.line([(1,2),(1,5)],fill=INDEX['s']);d.point((1,1),fill=0)
        else:
            d.polygon([(0,2),(2,0),(7,0),(7,7),(0,7)],fill=dark)
            d.polygon([(1,3),(3,1),(7,1),(7,7),(1,7)],fill=edge)
            d.polygon([(2,4),(4,2),(7,2),(7,7),(2,7)],fill=INDEX['p'] if bubble else INDEX['3'] if part.startswith(('slot','row')) else INDEX['2'])
            d.line([(3,1),(7,1)],fill=light);d.point((2,2),fill=light)
            if selected:d.point((3,3),fill=INDEX['W'])
    elif part.endswith('_t'):
        if empty:d.line([(1,1),(3,1)],fill=INDEX['s']);d.line([(6,1),(7,1)],fill=INDEX['s'])
        else:d.line([(0,0),(7,0)],fill=dark);d.line([(0,1),(7,1)],fill=light);d.line([(0,2),(7,2)],fill=edge)
    elif part.endswith('_l'):
        if empty:d.line([(1,1),(1,3)],fill=INDEX['s']);d.line([(1,6),(1,7)],fill=INDEX['s'])
        else:d.line([(0,0),(0,7)],fill=dark);d.line([(1,0),(1,7)],fill=edge)
    # HUD has a transparent one-pixel outer rim, keeping the visual band below24.
    if hud:
        if part.endswith('_tl'):d.point((0,0),fill=0)
    return letters(im)

TILE_ORDER=['panel_tl','panel_t','panel_l','fill','div_t','div_m','plate_l_top','plate_l_bot','plate_m_top','plate_m_bot','slot_tl','slot_t','slot_l','slot_fill','sel_tl','sel_t','sel_l','empty_tl','empty_t','empty_l','tab_l_top','tab_l_bot','tab_m_top','tab_m_bot','tabon_l_top','tabon_l_bot','tabon_m_top','tabon_m_bot','badge_a','badge_b','badge_l','badge_r','row_tl','row_t','row_l','srow_tl','srow_t','srow_l','bub_tl','bub_t','bub_l','bub_fill','bub_tail','bub_join','coin','rule','rule_end','hud_tl','hud_t','hud_l','key']

def kit():
    out={}
    for n in TILE_ORDER:
        im,d=image(fill=INDEX['2'])
        if n.startswith(('panel_','slot_','row_','hud_','empty_','bub_')) and n.rsplit('_',1)[-1] in ('tl','t','l'):
            out[n]=frame_tile(n,empty=n.startswith('empty'),hud=n.startswith('hud'),bubble=n.startswith('bub'));continue
        if n.startswith(('sel_','srow_')):
            out[n]=frame_tile(('slot' if n.startswith('sel') else 'row')+'_'+n.rsplit('_',1)[-1],selected=True);continue
        if n in ('fill','slot_fill','bub_fill'):
            d.rectangle((0,0,7,7),fill=INDEX['p'] if n=='bub_fill' else INDEX['3'] if n=='slot_fill' else INDEX['2'])
        elif n.startswith('div_'):
            d.line([(3,0),(3,7)],fill=INDEX['y']);d.line([(4,0),(4,7)],fill=INDEX['G'])
            if n=='div_t':d.rectangle((2,1,5,3),fill=INDEX['Y']);d.point((3,1),fill=INDEX['W'])
        elif n.startswith(('plate_','tab_','tabon_')):
            on=n.startswith('tabon');end='_l_' in n;top=n.endswith('top')
            fill=INDEX['G'] if on else INDEX['3'];d.rectangle((0,0,7,7),fill=fill)
            y=0 if top else 7;d.line([(0,y),(7,y)],fill=INDEX['W'] if top and on else INDEX['Y'])
            if end:d.line([(0,1),(0,6)],fill=INDEX['Y']);d.point((0,y),fill=INDEX['o']);d.point((1,y),fill=INDEX['G'])
            if on and top:d.line([(1,1),(7,1)],fill=INDEX['W'])
        elif n.startswith('badge_'):
            d.rectangle((0,0,7,7),fill=0);d.rounded_rectangle((0,0,7,7),radius=1,fill=INDEX['o'])
            d.rectangle((1,1,6,6),fill=INDEX['4'])
            ch=n[-1].upper();w,rs=F.glyph(ch)
            # Handheld button lettering uses the native face, with six rows.
            for yy,row in enumerate(rs[1:7]):
                for xx,v in enumerate(row):
                    if v=='#' and xx<5:d.point((1+xx,1+yy),fill=INDEX['W'])
        elif n=='bub_tail':
            d.rectangle((0,0,7,7),fill=0);d.polygon([(7,0),(7,6),(1,4)],fill=INDEX['o']);d.polygon([(7,1),(7,5),(3,4)],fill=INDEX['p'])
        elif n=='bub_join':d.rectangle((0,0,7,7),fill=INDEX['p']);d.line([(0,6),(0,7)],fill=INDEX['o'])
        elif n=='coin':
            d.rectangle((0,0,7,7),fill=0);d.polygon([(2,0),(5,0),(7,2),(7,5),(5,7),(2,7),(0,5),(0,2)],fill=INDEX['o'])
            d.polygon([(2,1),(5,1),(6,2),(6,5),(5,6),(2,6),(1,5),(1,2)],fill=INDEX['Y']);d.line([(2,2),(4,1),(5,2)],fill=INDEX['W']);d.line([(3,3),(3,5)],fill=INDEX['G'])
        elif n=='key':
            d.rectangle((0,0,7,7),fill=0);d.rectangle((1,1,4,4),fill=INDEX['o']);d.rectangle((2,2,3,3),fill=INDEX['G']);d.point((2,2),fill=INDEX['W'])
            d.line([(4,4),(7,7)],fill=INDEX['G'],width=2);d.point((6,5),fill=INDEX['Y']);d.point((7,6),fill=INDEX['W'])
        elif n.startswith('rule'):
            end=6 if n=='rule_end' else 7;d.line([(0,3),(end,3)],fill=INDEX['y']);d.line([(0,4),(end,4)],fill=INDEX['Y'])
            if n=='rule_end':d.point((6,3),fill=INDEX['W'])
        else:raise KeyError(n)
        out[n]=letters(im)
    return out
TILES=kit()

HUD_TILES={}
for name in ('heart_full','heart_half','heart_empty','hand'):
    im,d=image(fill=HUD_INDEX['2'])
    if name.startswith('heart'):
        d.polygon([(0,2),(1,1),(3,1),(4,2),(5,1),(6,1),(7,2),(7,4),(4,7),(0,4)],fill=HUD_INDEX['o'])
        d.polygon([(1,2),(3,2),(4,3),(5,2),(6,2),(6,4),(4,6),(1,4)],fill=HUD_INDEX['r'] if name=='heart_full' else HUD_INDEX['3'])
        if name=='heart_half':d.polygon([(1,2),(3,2),(4,3),(4,6),(1,4)],fill=HUD_INDEX['r'])
        if name!='heart_empty':d.point((2,2),fill=HUD_INDEX['W']);d.line([(2,3),(3,3)],fill=HUD_INDEX['q'])
        else:d.point((2,2),fill=HUD_INDEX['4'])
    else:
        d.polygon([(2,1),(3,1),(3,3),(4,0),(5,0),(5,3),(6,1),(7,2),(6,5),(4,7),(2,6),(0,4),(1,3),(2,4)],fill=HUD_INDEX['o'])
        d.polygon([(3,2),(3,4),(5,2),(5,4),(6,3),(5,6),(3,6),(1,4),(2,5)],fill=HUD_INDEX['c'])
        d.point((4,5),fill=HUD_INDEX['s'])
    HUD_TILES[name]=letters(im,HUD_KEYS)

OBJ_MARKS={}
for n in ('next','pick','corner'):
    im,d=image()
    if n=='next':
        d.polygon([(1,2),(6,2),(4,5),(3,5)],fill=INDEX['o']);d.line([(2,3),(5,3),(4,4),(3,4)],fill=INDEX['G']);d.point((2,2),fill=INDEX['W'])
    elif n=='pick':
        d.polygon([(1,0),(6,3),(6,4),(1,7)],fill=INDEX['o']);d.polygon([(2,1),(5,3),(5,4),(2,6)],fill=INDEX['G']);d.line([(2,1),(4,3)],fill=INDEX['W'])
    else:
        d.line([(0,6),(0,0),(6,0)],fill=INDEX['o'],width=2);d.line([(1,5),(1,1),(5,1)],fill=INDEX['G']);d.point((1,1),fill=INDEX['W'])
    OBJ_MARKS[n]=letters(im)
for n in ('badge_a','badge_b','badge_l'):OBJ_MARKS[n]=TILES[n]

def obj_rows(rs):return [''.join('.' if ch=='.' else '%x'%INDEX[ch] for ch in r) for r in rs]


def mark(name):
    im,d=image(16,16);o=1;g=8;cream=9;dim=5;red=13;green=15
    if name=='here':
        for b in [(5,1,10,5),(2,4,6,9),(9,4,13,9),(4,9,10,13)]:d.ellipse(b,fill=o);d.ellipse((b[0]+1,b[1]+1,b[2]-1,b[3]-1),fill=red)
        d.rectangle((5,5,10,10),fill=cream);d.point((6,7),fill=o);d.point((9,7),fill=o)
    elif name=='door':
        d.polygon([(3,14),(3,6),(5,2),(10,2),(12,6),(12,14)],fill=o);d.line([(4,13),(4,6),(6,3),(9,3),(11,6),(11,13)],fill=dim,width=2);d.line([(4,14),(11,14)],fill=g)
    elif name=='folk':
        d.polygon([(3,14),(4,7),(4,4),(7,1),(10,4),(10,7),(12,14)],fill=o);d.polygon([(4,13),(5,7),(7,3),(9,6),(11,13)],fill=green);d.rectangle((6,5,9,8),fill=cream);d.point((7,6),fill=o)
    elif name=='quest':
        d.polygon([(7,1),(13,7),(7,14),(1,7)],fill=o);d.polygon([(7,2),(12,7),(7,13),(2,7)],fill=g);d.line([(7,4),(7,8)],fill=o,width=2);d.point((7,10),fill=o)
    elif name=='relic':
        d.polygon([(7,1),(12,7),(7,13),(2,7)],fill=o);d.polygon([(7,2),(11,7),(7,11),(3,7)],fill=g);d.line([(7,3),(7,10)],fill=cream);d.line([(4,7),(10,7)],fill=cream);d.rectangle((4,13,10,14),fill=g)
    elif name=='chest':
        d.rectangle((1,5,14,13),fill=o);d.rectangle((2,6,13,12),fill=6);d.line([(2,8),(13,8)],fill=o);d.line([(4,5),(4,12)],fill=g,width=2);d.line([(11,5),(11,12)],fill=g,width=2);d.rectangle((7,8,8,10),fill=cream);d.line([(3,4),(12,4)],fill=g)
    elif name in ('heart','boss'):
        d.polygon([(2,3),(5,2),(7,4),(10,2),(13,3),(14,6),(7,14),(1,6)],fill=o);d.polygon([(3,4),(5,3),(7,5),(10,3),(12,4),(13,6),(7,12),(2,6)],fill=red)
        if name=='boss':d.line([(8,3),(6,6),(9,8),(7,12)],fill=o)
        else:d.point((4,4),fill=cream)
    elif name=='crack':
        d.rectangle((1,2,14,13),fill=o);d.rectangle((2,3,13,12),fill=dim);d.line([(9,2),(7,5),(9,7),(5,10),(6,13)],fill=o,width=2);d.line([(10,3),(8,5)],fill=cream)
    elif name=='web':
        for x,y in [(1,1),(14,1),(1,14),(14,14),(7,1),(7,14)]:d.line([(7,7),(x,y)],fill=cream)
        d.line([(3,3),(7,2),(12,3),(13,7),(12,12),(7,13),(3,12),(2,7),(3,3)],fill=cream)
        d.line([(5,5),(9,5),(10,9),(6,10),(5,5)],fill=cream)
    elif name=='lock':
        d.arc((4,1,11,10),180,360,fill=g,width=2);d.rectangle((2,6,13,14),fill=o);d.rectangle((3,7,12,13),fill=g);d.rectangle((7,9,8,11),fill=o);d.point((4,7),fill=cream)
    elif name=='chasm':
        d.ellipse((1,3,14,12),fill=dim);d.ellipse((2,4,13,10),fill=o);d.line([(4,12),(11,12)],fill=g)
    elif name=='thorn':
        d.line([(5,14),(7,10),(6,7),(9,3)],fill=green,width=2)
        for x,y in [(5,11),(7,7),(9,4)]:d.polygon([(x-3,y-2),(x+2,y),(x,y+2)],fill=o);d.point((x-1,y),fill=green)
    else:raise KeyError(name)
    return hexrows(im)


def dot(name):
    im,d=image();o=1;g=8;c=9;r=13;s=5
    if name=='here':d.polygon([(3,0),(7,3),(4,7),(0,4)],fill=o);d.polygon([(3,1),(6,3),(4,6),(1,4)],fill=r);d.point((3,2),fill=c)
    elif name=='door':d.rectangle((1,3,6,7),fill=o);d.arc((1,0,6,7),180,360,fill=s,width=2);d.line([(1,7),(6,7)],fill=g)
    elif name=='quest':d.rectangle((2,0,5,7),fill=o);d.line([(3,1),(3,4)],fill=g,width=2);d.point((3,6),fill=c)
    elif name=='chest':d.rectangle((0,2,7,6),fill=o);d.rectangle((1,3,6,5),fill=g);d.line([(0,4),(7,4)],fill=o);d.point((3,4),fill=c)
    elif name in ('boss','relic'):
        d.polygon([(3,0),(7,3),(4,7),(0,4)],fill=o);d.polygon([(3,1),(6,3),(4,6),(1,4)],fill=r if name=='boss' else g);d.point((3,3),fill=c)
    elif name=='folk':d.ellipse((2,0,5,3),fill=c);d.polygon([(3,3),(6,7),(1,7)],fill=15)
    elif name=='crack':d.rectangle((0,1,7,6),fill=s);d.line([(4,1),(2,3),(5,4),(3,6)],fill=o)
    elif name=='web':d.line([(0,0),(7,7)],fill=c);d.line([(0,7),(7,0)],fill=c);d.rectangle((2,2,5,5),outline=c)
    elif name=='lock':d.arc((2,0,5,5),180,360,fill=g);d.rectangle((1,3,6,7),fill=g);d.point((3,5),fill=o)
    elif name=='chasm':d.ellipse((0,1,7,6),fill=s);d.ellipse((1,2,6,5),fill=o)
    elif name=='thorn':d.line([(2,7),(4,4),(3,1)],fill=15,width=2);d.line([(1,2),(6,5)],fill=15)
    else:raise KeyError(name)
    return hexrows(im)


def cursor():
    im,d=image(32,32)
    for pts in [[(0,6),(0,0),(6,0)],[(25,0),(31,0),(31,6)],[(0,17),(0,23),(6,23)],[(25,23),(31,23),(31,17)]]:
        d.line(pts,fill=1,width=3);d.line(pts,fill=8,width=1)
    for x,y in [(0,0),(31,0),(0,23),(31,23)]:d.point((x,y),fill=9)
    return hexrows(im)

FACE_NAMES=['bloom_surprised','peddler','gatekeeper','hermit','nun','gardener']
FACE_BANKS=['hero','gold','stone','hero','hero','hero']

def portrait(name):
    im,d=image(48,48);o=1
    if name=='bloom_surprised':
        # Petal clusters are the same five-lobed flower as the world avatar.
        for box in [(16,1,31,17),(4,11,20,30),(27,10,43,29),(9,28,25,44),(24,28,39,44)]:
            d.ellipse(box,fill=o);d.ellipse((box[0]+2,box[1]+2,box[2]-2,box[3]-2),fill=3);d.line([(box[0]+4,box[1]+3),(box[2]-4,box[1]+3)],fill=4,width=2);d.point((box[0]+5,box[1]+5),fill=5)
        d.ellipse((13,12,34,34),fill=o);d.ellipse((15,14,32,32),fill=6);d.line([(18,15),(28,15)],fill=7,width=2)
        d.rectangle((19,20,20,24),fill=o);d.rectangle((27,20,28,24),fill=o);d.rectangle((23,28,25,30),fill=o)
        d.polygon([(16,39),(23,35),(31,39),(37,47),(9,47)],fill=8);d.line([(17,41),(23,39),(29,41)],fill=10,width=2)
    elif name=='peddler':
        d.polygon([(2,47),(6,32),(13,29),(34,28),(42,35),(46,47)],fill=o);d.polygon([(4,47),(9,34),(17,32),(32,31),(39,36),(43,47)],fill=4)
        d.line([(12,36),(10,47)],fill=6,width=3);d.line([(31,33),(33,47)],fill=3,width=2)
        d.polygon([(7,20),(8,7),(17,2),(33,5),(39,14),(39,30),(33,36),(28,30),(13,31)],fill=o)
        d.polygon([(9,20),(11,8),(18,4),(32,7),(36,15),(35,27),(30,30),(14,29)],fill=13)
        d.line([(12,11),(19,6),(29,8)],fill=14,width=2)
        # Rat-like ears, muzzle and single strong gold earring.
        d.polygon([(10,14),(8,7),(16,12)],fill=o);d.polygon([(11,13),(10,10),(14,13)],fill=15)
        d.polygon([(32,14),(36,9),(37,18)],fill=o);d.point((35,13),fill=15)
        d.polygon([(15,15),(29,14),(31,21),(37,24),(31,28),(26,33),(16,29),(13,22)],fill=11)
        d.line([(16,17),(24,16)],fill=12,width=2);d.rectangle((18,20,19,22),fill=o);d.rectangle((28,20,29,21),fill=o)
        d.polygon([(31,22),(38,24),(31,26)],fill=6);d.point((37,24),fill=o)
        d.line([(20,28),(28,29),(30,27)],fill=2);d.rectangle((11,26,13,30),outline=10,width=1);d.point((12,26),fill=12)
        d.rectangle((21,36,26,39),fill=8);d.point((22,36),fill=12)
    else:
        keeper=name=='gatekeeper';nun=name=='nun';gardener=name=='gardener'
        coat=3 if keeper else 1 if nun else 8
        shade=2 if keeper else 1 if nun else 9
        lit=5 if keeper else 13 if nun else 10
        d.polygon([(1,47),(5,33),(13,29),(34,29),(42,35),(47,47)],fill=o)
        d.polygon([(4,47),(8,35),(15,32),(32,32),(39,36),(44,47)],fill=coat)
        d.line([(11,36),(8,46)],fill=lit,width=2);d.line([(33,34),(38,47)],fill=shade,width=2)
        d.polygon([(10,27),(7,15),(12,5),(21,1),(32,5),(39,16),(36,32),(29,37),(16,35)],fill=o)
        d.polygon([(11,26),(10,15),(14,7),(22,4),(31,8),(36,17),(33,31),(28,34),(17,32)],fill=coat)
        d.line([(13,12),(18,7),(24,6),(31,10)],fill=lit,width=2)
        face=7 if keeper else 6;fhi=8 if keeper else 7
        d.ellipse((15,12,32,32),fill=o);d.ellipse((17,14,30,31),fill=face);d.line([(19,15),(27,15)],fill=fhi,width=2)
        d.line([(16,13),(31,13)],fill=o,width=2)
        d.rectangle((19,20,21,21),fill=1);d.rectangle((27,20,29,21),fill=1)
        d.line([(23,22),(22,25),(25,25)],fill=5 if keeper else 12)
        d.line([(22,29),(26,29)],fill=1)
        if keeper:
            d.line([(13,12),(20,10),(28,11),(34,14)],fill=13,width=2);d.point((22,10),fill=15)
            d.line([(18,20),(20,20)],fill=8);d.line([(27,20),(29,20)],fill=8)
            d.ellipse((17,35,30,47),fill=1);d.ellipse((19,37,28,46),fill=13);d.ellipse((21,38,27,44),fill=14);d.point((23,39),fill=15)
        elif nun:
            # One connected tear; the black veil leaves the face uncovered.
            d.polygon([(9,14),(15,8),(17,13),(15,26),(12,36),(8,31)],fill=1)
            d.polygon([(32,11),(38,18),(36,34),(31,37),(32,26)],fill=1)
            d.line([(28,22),(28,25),(27,27)],fill=14);d.point((27,27),fill=15)
            d.line([(22,36),(25,36),(25,42),(22,42)],fill=7);d.point((23,36),fill=15)
            d.line([(35,14),(36,20),(35,29)],fill=13)
            d.line([(5,45),(11,46),(36,46),(43,45)],fill=13)
            d.line([(8,45),(11,46)],fill=14)
        else:
            # White-bearded hermit or brown-bearded gardener, matching world.
            beard=11 if gardener else 13;blit=12 if gardener else 14
            d.polygon([(16,25),(21,26),(24,25),(28,26),(32,24),(31,32),(25,38),(18,33)],fill=1)
            d.polygon([(18,27),(23,28),(26,27),(29,27),(29,32),(25,35),(20,32)],fill=beard)
            d.line([(19,28),(21,31),(24,32)],fill=blit,width=2)
            if not gardener:d.line([(19,20),(21,20)],fill=15);d.line([(27,20),(29,20)],fill=15)
            else:
                d.polygon([(10,13),(9,5),(14,8),(15,2),(19,8),(23,7),(18,13)],fill=1)
                d.line([(12,10),(12,7),(16,10),(16,6)],fill=10,width=2)
    # Two-pixel folds and worn patches belong to clothing; no random noise.
    if name not in ('bloom_surprised','peddler'):
        coat=3 if name=='gatekeeper' else 1 if name=='nun' else 8
        shade=2 if name=='gatekeeper' else 1 if name=='nun' else 9
        lit=5 if name=='gatekeeper' else 13 if name=='nun' else 10
        d.polygon([(7,40),(13,35),(15,38),(12,46),(8,46)],fill=shade)
        d.line([(9,40),(12,37)],fill=lit,width=1)
        d.polygon([(33,38),(39,42),(40,47),(35,47)],fill=1)
        d.line([(34,39),(37,43)],fill=shade,width=2)
    elif name=='peddler':
        d.polygon([(6,43),(12,37),(15,39),(13,47),(7,47)],fill=3)
        d.line([(9,41),(12,39)],fill=6,width=1)
        d.rectangle((34,40,39,45),fill=2);d.line([(35,40),(38,40)],fill=5)
        d.line([(35,42),(38,43)],fill=4)
    return im

FACES=[]
for name,family in zip(FACE_NAMES,FACE_BANKS):
    pal=C.PALETTES[family]
    FACES.append((name,[(format(i,'x'),C.rgb(pal[i])) for i in range(1,16)],[''.join('.' if ch=='0' else ch for ch in r) for r in hexrows(portrait(name))]))


def title_image():
    # Exactly native240×160, composed from shared RGB555 inks throughout.
    # ≤48 colours are selected before any pixel is drawn.
    chosen=[]
    for family,indices in [('ui',[1,2,3,5,6,7,8,9]),('foliage',[1,2,3,4,5,6]),('gold',[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]),('blight',[1,2,3,4,5,6,7,12,13,14,15]),('drain',[2,3,4,5,6,7,8,9,10,11,12,13,14])]:
        for i in indices:
            col=C.PALETTES[family][i]
            if col not in chosen and len(chosen)<48:chosen.append(col)
    # Semantic title colours are fixed entries of these shared ramps.
    def ink(f,i):return C.rgb(C.PALETTES[f][i])
    im=Image.new('RGB',(240,160),ink('ui',1));d=ImageDraw.Draw(im)
    # A castle silhouette over bruised hills; no texture outside authored masses.
    d.polygon([(0,46),(13,31),(23,35),(37,15),(51,37),(65,30),(79,47),(93,36),(105,56),(136,49),(150,31),(166,38),(183,17),(198,34),(215,28),(239,46),(239,96),(0,96)],fill=ink('blight',3))
    d.polygon([(0,62),(16,55),(25,58),(39,44),(50,51),(67,46),(81,63),(98,57),(116,70),(142,60),(162,48),(174,57),(194,44),(213,55),(228,49),(239,60),(239,103),(0,103)],fill=ink('blight',2))
    for x,h,w in [(13,21,5),(27,31,7),(46,16,5),(65,26,6),(174,22,6),(190,31,7),(211,19,5),(225,27,6)]:
        y=71-h;d.rectangle((x,y,x+w,82),fill=ink('ui',1));d.polygon([(x-1,y),(x+w//2,y-6),(x+w+1,y)],fill=ink('ui',1))
        d.rectangle((x+2,y+8,x+3,y+12),fill=ink('gold',8))
    # Moon uses literal crescent pixels and two bruised values.
    d.ellipse((197,13,222,38),fill=ink('gold',9));d.ellipse((192,10,215,35),fill=ink('blight',3));d.line([(219,20),(221,25),(219,31)],fill=ink('gold',11))
    # Border is a worn one-pixel brass rule with native four-point ornaments.
    d.rectangle((3,3,236,156),outline=ink('gold',8));d.line([(6,5),(233,5)],fill=ink('gold',5));d.line([(5,7),(5,153)],fill=ink('gold',5))
    for x,y in [(4,4),(235,4),(4,155),(235,155),(120,4),(120,155)]:
        d.line([(x-3,y),(x+3,y)],fill=ink('gold',10));d.line([(x,y-3),(x,y+3)],fill=ink('gold',10));d.point((x,y),fill=ink('gold',12))
    # Damp black-green canopy below the metal and skyline.
    for x,y,w in [(0,80,35),(26,75,32),(54,83,33),(82,81,31),(113,83,30),(142,80,34),(173,74,37),(205,80,35)]:
        d.polygon([(x,y+4),(x+5,y),(x+11,y+3),(x+18,y-2),(x+24,y+3),(x+w,y+2),(x+w,y+32),(x,y+32)],fill=ink('foliage',2))
        d.line([(x+5,y+4),(x+10,y+4),(x+12,y+6)],fill=ink('foliage',4));d.line([(x+19,y+3),(x+23,y+5),(x+28,y+4)],fill=ink('foliage',3))
    # Reuse the actual native canopy vocabulary, not a different title-only
    # illustration style. Leaves are pasted one source pixel to one pixel.
    for xx,yy in [(-6,78),(24,74),(55,81),(85,78),(116,80),(148,77),(180,73),(212,79)]:
        tree=C.rgba(C.tree(),C.PALETTES['foliage'])
        im.paste(tree,(xx,yy),tree)
    # Grail, bright and unspoiled above a tarnished world.
    d.line([(120,11),(120,65)],fill=ink('gold',5));d.line([(96,38),(144,38)],fill=ink('gold',7));d.line([(104,22),(136,54)],fill=ink('gold',5));d.line([(104,54),(136,22)],fill=ink('gold',5))
    d.polygon([(105,21),(135,21),(133,35),(127,43),(123,46),(123,57),(131,59),(131,63),(109,63),(109,59),(117,57),(117,46),(111,42),(107,35)],fill=ink('ui',1))
    d.polygon([(107,23),(133,23),(131,35),(125,42),(122,44),(121,57),(128,59),(128,61),(112,61),(112,59),(119,57),(118,44),(113,41),(109,34)],fill=ink('gold',9))
    d.line([(108,24),(131,24)],fill=ink('gold',12),width=2);d.line([(110,27),(111,34),(116,40)],fill=ink('gold',11),width=2);d.line([(126,27),(126,35),(122,42)],fill=ink('gold',8),width=2)
    d.polygon([(120,29),(123,32),(120,36),(117,32)],fill=ink('gold',15));d.point((119,30),fill=ink('gold',12))
    d.line([(113,59),(126,59)],fill=ink('gold',12));d.line([(120,45),(120,56)],fill=ink('gold',11))
    # Hand-set native pixel lettering, with hard stepped metal highlights.
    label='BARTGAME';total=sum(F.glyph(ch)[0]+1 for ch in label)*3-3;x0=(240-total)//2
    text(d,x0+2,73+2,label,ink('ui',1),3);text(d,x0,73,label,ink('gold',7),3)
    # Individual high pixels on the top-left of each actual letter stroke.
    x=x0
    for ch in label:
        _,rs=F.glyph(ch)
        for yy,row in enumerate(rs):
            for xx,v in enumerate(row):
                if v=='#' and (yy<3 or xx==0):d.rectangle((x+xx*3,73+yy*3,x+xx*3+2,73+yy*3+1),fill=ink('gold',11 if yy<3 else 9))
        x+=(F.glyph(ch)[0]+1)*3
    sub='a game of the drain';sx=(240-F.width(sub))//2;text(d,sx,102,sub,ink('gold',11))
    # Dirty roots, clogged masonry and reflected metal at the same scale.
    for y in [115,123,131]:
        for x in range(7,234,17):
            off=8 if y==123 else 0;xx=x-off
            d.rectangle((xx,y,xx+15,y+6),fill=ink('drain',3));d.line([(xx+1,y),(xx+13,y)],fill=ink('drain',5));d.line([(xx+15,y+1),(xx+15,y+5)],fill=ink('drain',2))
    for x in [17,42,67,178,201,224]:
        d.line([(x,110),(x-2,117),(x+1,124),(x-1,131)],fill=ink('gold',3),width=3);d.line([(x-1,110),(x-3,116),(x-1,121)],fill=ink('foliage',4))
        d.line([(x+3,113),(x+5,121)],fill=ink('foliage',3),width=2)
    # The prompt sits over an open dark-water channel, not a separate UI
    # plaque. Its banks merge into the same masonry and roots as the sides.
    d.polygon([(77,115),(86,113),(152,113),(163,116),(170,124),(176,138),
               (176,153),(64,153),(64,138),(69,124)],fill=ink('drain',2))
    d.line([(75,116),(70,123),(68,132),(64,138)],fill=ink('drain',4),width=2)
    d.line([(165,118),(170,125),(172,133),(177,138)],fill=ink('drain',3),width=2)
    d.line([(72,125),(70,130)],fill=ink('drain',6));d.line([(169,126),(171,132)],fill=ink('foliage',3))
    d.rectangle((7,138,232,153),fill=ink('drain',2))
    for xx,yy,ww in [(8,140,42),(22,144,32),(47,150,18),(179,141,39),(185,146,27),(207,151,20)]:
        d.line([(xx,yy),(xx+ww,yy)],fill=ink('drain',4))
        d.line([(xx+4,yy-1),(xx+ww//2,yy-1)],fill=ink('drain',6))
        d.point((xx+6,yy-1),fill=ink('gold',10))
    # Broad shadowy ripples connect the centre to the filthy side pools.
    # The actual prompt lettering lives between x90..151, y122..149.
    for xx,yy,ww in [(11,135,61),(164,136,64),(68,131,20),(155,129,19),
                     (74,146,12),(159,148,17),(87,153,28),(132,153,22)]:
        d.line([(xx,yy),(xx+ww,yy)],fill=ink('drain',3))
    d.line([(70,118),(68,124),(70,128)],fill=ink('foliage',3))
    d.line([(172,116),(175,123),(174,129)],fill=ink('gold',3),width=2)
    d.point((70,128),fill=ink('gold',8))
    # The rule is the last material layer, so foliage cannot erase its edge.
    d.rectangle((3,3,236,156),outline=ink('gold',8))
    for xx,yy in [(4,4),(235,4),(4,155),(235,155),(120,4),(120,155)]:
        d.line([(xx-3,yy),(xx+3,yy)],fill=ink('gold',10));d.line([(xx,yy-3),(xx,yy+3)],fill=ink('gold',10));d.point((xx,yy),fill=ink('gold',12))
    # Twenty-eight surface glints; different sizes communicate wet sheen vsholyflare.
    sites=[(15,17),(35,9),(64,20),(84,14),(97,8),(146,14),(162,9),(181,16),(231,38),(9,50),(59,47),(86,58),(151,56),(183,49),(230,63),(18,94),(51,96),(194,95),(222,100),(29,117),(59,125),(183,126),(218,136),(22,146),(190,150),(91,47),(149,35),(120,13)]
    for i,(x,y) in enumerate(sites):
        radius=3 if i in (0,5,15,20,26,27) else 1
        d.line([(x-radius,y),(x+radius,y)],fill=ink('gold',10 if radius>1 else 8));d.line([(x,y-radius),(x,y+radius)],fill=ink('gold',10 if radius>1 else 8));d.point((x,y),fill=ink('gold',12))
    assert len(set(im.getdata()))<=48,len(set(im.getdata()))
    return im


def build_sheets(contracts):
    out={};spec={s['name']:s for s in contracts['sheets']}
    def add(n,w,h,frames,pal):out[n]={'name':n,'w':w,'h':h,'pal':pal,'frames':frames}
    add('uimarks',8,8,{n:obj_rows(OBJ_MARKS[n]) for n in spec['uimarks']['frames']},'uikit')
    add('marks',16,16,{n:mark(n) for n in spec['marks']['frames']},'ui')
    add('dots',8,8,{n:dot(n) for n in spec['dots']['frames']},'ui')
    add('cursor',32,32,{n:cursor() for n in spec['cursor']['frames']},'ui')
    faces={}
    for n in spec['face']['frames']:
        rs=hexrows(portrait(n));faces[n]=[r+'0'*16 for r in rs]+['0'*64]*16
    add('face',64,64,faces,'portrait')
    return out


def preview(path='/workspace/setup/art-reboot-ui-source.png'):
    # Source board only. Hardware evidence is captured later from the ROM.
    out=Image.new('RGB',(960,870),'#101820');d=ImageDraw.Draw(out)
    d.text((8,8),'NATIVE UI / title / portraits / source art, not emulator output',fill='#f8f0c8')
    def show(im,pal,x,y,scale=3):
        if im.mode=='P':im=C.rgba(im,pal)
        big=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST);out.paste(big,(x,y),big if big.mode=='RGBA' else None)
    for i,(n,bank) in enumerate(zip(FACE_NAMES,FACE_BANKS)):
        show(portrait(n),C.PALETTES[bank],8+i*158,40,3);d.text((8+i*158,188),n,fill='#f8f0c8')
    for i,n in enumerate(TILE_ORDER):
        im,_=image();pix=im.load()
        for yy,row in enumerate(TILES[n]):
            for xx,ch in enumerate(row):pix[xx,yy]=0 if ch=='.' else INDEX[ch]
        show(im,GROUPS['menu'],8+(i%17)*55,220+(i//17)*45,4)
    ti=title_image();out.paste(ti.resize((720,480),Image.Resampling.NEAREST),(8,370))
    out.save(path)
    ti.save('/workspace/setup/art-reboot-title-native.png')
    return path
