"""Five native 4bpp interface studies for the gilt-and-rot game.

All geometry starts as final 8px hardware tiles or 10px equipment drawings.
The selected environment variant is a review choice, not a production vote.
No imported illustration, filtered scaling or fractional alpha is used.
"""
import os
from PIL import Image, ImageDraw

VARIANT=int(os.environ.get('BART_UI','0'))
assert 0<=VARIANT<=10,('BART_UI must be0..10',VARIANT)
STYLE_NAMES={0:'Quiet Brass',1:'Ivory Wire',2:'Moulded Vellum',3:'Black Glass',4:'Wine Reliquary',5:'Salvage Ledger',
             6:'Winebound Folio',7:'Mossbound Fieldbook',8:'Ivory Reliquary',
             9:'Burgundy Archivist',10:'Verdigris Devotional'}
# Structure and color are separate choices. These five new studies use the
# requested old1/4/5 palettes exactly; none automatically changes by area yet.
# A future area can select a palette without replacing navigation or geometry.
STYLE_RECIPES={
 6:{'geometry':'winebound_folio','design_sources':(2,), 'palette':4},
 7:{'geometry':'mossbound_fieldbook','design_sources':(2,5), 'palette':5},
 8:{'geometry':'ivory_reliquary','design_sources':(4,), 'palette':1},
 9:{'geometry':'burgundy_archivist','design_sources':(4,5), 'palette':4},
 10:{'geometry':'verdigris_devotional','design_sources':(2,4,5), 'palette':5},
}
KEYS=('o','1','2','3','4','y','Y','G','W','c','s','h','r','p','b')
# Semantic role order is retained so every existing menu, cost, hint and
# speaker line remains meaningful. Light paper intentionally uses dark type.
THEMES={
1:dict(zip(KEYS,('#101820','#101820','#182028','#203038','#485848','#605038','#a08048','#d8c088','#f8f0d8','#e0e8d8','#98a8a0','#f8f8e0','#e07868','#d8d8b8','#302820'))),
2:dict(zip(KEYS,('#302820','#988060','#d8d0a8','#c8c098','#a8a080','#786040','#a07840','#805028','#f8f0d8','#302820','#685840','#101820','#983830','#e8e0b8','#483020'))),
3:dict(zip(KEYS,('#080f18','#101820','#101820','#202830','#607080','#504030','#a08040','#e8b858','#f8f0d8','#e0e8e0','#889898','#f8f8e8','#e87060','#202830','#e0e8e0'))),
4:dict(zip(KEYS,('#181018','#201018','#281820','#402030','#805860','#684030','#a87050','#e8b878','#f8e8c8','#f0d8b8','#b08880','#f8f0d8','#f08078','#382030','#e8d8c0'))),
5:dict(zip(KEYS,('#101820','#182820','#283828','#405040','#687860','#384830','#708060','#c8b878','#f8e8b8','#d8e0c0','#98a080','#f0f0c8','#d87868','#c0c8a0','#283820'))),
}

def q(color):
    return '#'+''.join('%02x'%(int(color[i:i+2],16)//8*8) for i in (1,3,5))
THEMES={n:{key:q(value) for key,value in theme.items()} for n,theme in THEMES.items()}
for _profile,_recipe in STYLE_RECIPES.items():
    THEMES[_profile]=dict(THEMES[_recipe['palette']])

def theme(number=None):
    return THEMES.get(VARIANT if number is None else number)


def palette_profile(number=None):
    """The reusable color recipe, independent of this study's shape recipe."""
    number=VARIANT if number is None else int(number)
    return STYLE_RECIPES.get(number,{}).get('palette',number)


def geometry_recipe(number=None):
    number=VARIANT if number is None else int(number)
    return STYLE_RECIPES.get(number,{}).get('geometry',STYLE_NAMES[number])

def indexed(w=8,h=8,fill=0):
    im=Image.new('P',(w,h),fill)
    return im,ImageDraw.Draw(im)

def _letters(im,index,keys=KEYS):
    return [''.join('.' if not im.getpixel((x,y)) else keys[im.getpixel((x,y))-1] for x in range(im.width)) for y in range(im.height)]

def _glint(d,x,y,ink):
    d.line((x-2,y,x+2,y),fill=ink);d.line((x,y-2,x,y+2),fill=ink)


def remixed_frame_tile(name,index,style):
    """Five newly drawn structures informed by folio, brocade and ledger.

    Every coordinate is a final8px tile coordinate. Quiet runs leave a usable
    text field; the richer motifs stay at the corners or selection boundary.
    """
    im,d=indexed();i=index
    kind,part=name.rsplit('_',1)
    selected=kind in ('sel','srow');empty=kind=='empty';bubble=kind=='bub'
    slot=kind in ('slot','sel','row','srow')
    bg=i['p'] if bubble else i['3'] if slot else i['2']
    edge=i['G'] if selected else i['Y'];hot=i['W'] if selected else i['G']
    if part!='tl':d.rectangle((0,0,7,7),fill=bg)
    if empty:
        if part=='tl':
            d.line((1,6,1,2),fill=i['s']);d.line((2,1,6,1),fill=i['s'])
            if style in (7,9):d.point((2,2),fill=i['y'])
            if style in (8,10):d.point((3,3),fill=i['4'])
        elif part=='t':d.line((1,2,3 if style in (7,9) else 5,2),fill=i['s'])
        else:d.line((2,1,2,3 if style in (7,9) else 5),fill=i['s'])
        return _letters(im,i)
    if style==6: # A rolled folio: rounded contour and one turned brass leaf.
        if part=='tl':
            d.polygon([(0,5),(1,3),(3,1),(7,1),(7,7),(0,7)],fill=i['o'])
            d.polygon([(1,5),(2,3),(4,2),(7,2),(7,7),(1,7)],fill=bg)
            d.line([(1,5),(2,3),(4,1),(7,1)],fill=edge)
            d.polygon([(3,2),(6,2),(4,4)],fill=i['y']);d.point((4,2),fill=hot)
        elif part=='t':d.line((0,1,7,1),fill=edge);d.line((1,3,5,3),fill=i['y'])
        else:d.line((1,0,1,7),fill=edge);d.point((3,5),fill=i['4'])
    elif style==7: # Mended fieldbook: lapped corner, stitches and broad paper.
        if part=='tl':
            d.polygon([(0,3),(2,3),(2,0),(7,0),(7,7),(0,7)],fill=i['o'])
            d.polygon([(1,4),(4,4),(4,1),(7,1),(7,7),(1,7)],fill=bg)
            d.line((4,1,7,1),fill=edge);d.line((1,4,1,7),fill=edge)
            d.line((2,2,5,2),fill=i['y']);d.point((3,3),fill=hot)
        elif part=='t':
            d.line((0,0,7,0),fill=i['o']);d.line((0,2,2,2),fill=edge);d.line((5,2,7,2),fill=edge)
            d.point((3,4),fill=i['y'])
        else:
            d.line((0,0,0,7),fill=i['o']);d.line((2,0,2,2),fill=edge);d.line((2,5,2,7),fill=edge)
            d.point((4,3),fill=i['y'])
    elif style==8: # Restrained reliquary: corner leaves, an otherwise quiet wire.
        if part=='tl':
            d.polygon([(0,5),(2,2),(5,0),(7,0),(7,7),(0,7)],fill=bg)
            d.line([(0,6),(1,3),(3,1),(7,0)],fill=i['y'])
            d.polygon([(1,4),(3,1),(5,1),(3,3)],fill=edge)
            d.polygon([(2,6),(4,3),(6,3),(4,5)],fill=i['Y'])
            d.point((2,2),fill=hot)
        elif part=='t':d.line((0,1,7,1),fill=edge);d.point((4,3),fill=i['y'])
        else:d.line((1,0,1,7),fill=edge);d.point((3,4),fill=i['y'])
    elif style==9: # Archival reinforcement: a rivet and broken double rail.
        if part=='tl':
            d.rectangle((0,0,7,7),fill=bg)
            d.line((0,5,0,0),fill=i['o']);d.line((0,0,7,0),fill=i['o'])
            d.line((1,6,1,1),fill=edge);d.line((1,1,7,1),fill=edge)
            d.rectangle((1,1,3,3),fill=i['y']);d.point((2,2),fill=hot)
            d.line((5,3,7,3),fill=i['Y']);d.line((3,5,3,7),fill=i['Y'])
        elif part=='t':
            d.line((0,0,7,0),fill=i['o']);d.line((0,1,7,1),fill=edge)
            d.line((0,3,2,3),fill=i['y']);d.line((5,3,7,3),fill=i['y'])
        else:
            d.line((0,0,0,7),fill=i['o']);d.line((1,0,1,7),fill=edge)
            d.line((3,0,3,2),fill=i['y']);d.line((3,5,3,7),fill=i['y'])
    else: # Verdigris devotional: folio shape with attached paired leaf growth.
        if part=='tl':
            d.polygon([(0,4),(1,2),(3,0),(7,0),(7,7),(0,7)],fill=bg)
            d.line([(0,6),(0,3),(3,0),(7,0)],fill=i['y'])
            d.polygon([(1,4),(2,1),(4,2),(3,4)],fill=edge)
            d.polygon([(3,6),(4,3),(6,4),(5,6)],fill=i['Y'])
            d.point((2,2),fill=hot);d.point((4,4),fill=i['4'])
        elif part=='t':
            d.line((0,1,7,1),fill=edge);d.line((0,3,3,3),fill=i['y']);d.point((5,2),fill=i['4'])
        else:
            d.line((1,0,1,7),fill=edge);d.line((3,0,3,3),fill=i['y']);d.point((2,5),fill=i['4'])
    return _letters(im,i)


def frame_tile(name,index,style):
    """A native corner/edge/side; the engine mirrors each opposite edge."""
    if style>=6:return remixed_frame_tile(name,index,style)
    im,d=indexed();i=index
    kind,part=name.rsplit('_',1)
    selected=kind in ('sel','srow')
    empty=kind=='empty'
    bubble=kind=='bub'
    slot=kind in ('slot','sel','row','srow')
    bg=i['p'] if bubble else i['3'] if slot else i['2']
    edge=i['G'] if selected else i['Y'];hot=i['W'] if selected else i['G']
    if part!='tl':d.rectangle((0,0,7,7),fill=bg)
    if empty:
        if part=='tl':d.line((1,5,1,1),fill=i['s']);d.line((1,1,5,1),fill=i['s'])
        elif part=='t':d.line((1,1,3,1),fill=i['s'])
        elif part=='l':d.line((1,1,1,3),fill=i['s'])
        return _letters(im,i)
    if style==1: # Thin ivory wire: open corners, light only where joined.
        if part=='tl':
            d.rectangle((2,2,7,7),fill=bg)
            d.line((1,6,1,3),fill=edge);d.line((3,1,7,1),fill=hot)
            d.point((2,2),fill=i['W']);d.point((4,4),fill=i['y'])
        elif part=='t':d.line((0,1,7,1),fill=hot)
        else:d.line((1,0,1,7),fill=edge)
    elif style==2: # Rounded torn paper with an ink rule, not gold casing.
        if part=='tl':
            d.polygon([(0,4),(1,2),(3,1),(7,1),(7,7),(0,7)],fill=i['y'])
            d.polygon([(1,4),(2,2),(7,2),(7,7),(1,7)],fill=bg)
            d.line((3,2,7,2),fill=i['W']);d.point((2,4),fill=i['4'])
            if selected:d.line((3,5,6,5),fill=i['G'])
        elif part=='t':d.line((0,0,7,0),fill=i['y']);d.line((0,1,7,1),fill=i['W']);d.line((0,3,7,3),fill=edge)
        else:d.line((0,0,0,7),fill=i['y']);d.line((1,0,1,7),fill=i['W']);d.point((2,6),fill=i['4'])
    elif style==3: # Clipped black glass and stepped Art Deco brass.
        if part=='tl':
            d.polygon([(0,5),(5,0),(7,0),(7,7),(0,7)],fill=i['o'])
            d.polygon([(1,5),(5,1),(7,1),(7,7),(1,7)],fill=edge)
            d.polygon([(3,6),(6,3),(7,3),(7,7),(3,7)],fill=bg)
            d.line((1,5,5,1),fill=hot);d.point((6,4),fill=i['4'])
        elif part=='t':d.line((0,0,7,0),fill=i['o']);d.line((0,1,7,1),fill=hot);d.line((0,3,7,3),fill=i['y'])
        else:d.line((0,0,0,7),fill=i['o']);d.line((1,0,1,7),fill=edge);d.line((3,0,3,7),fill=i['y'])
    elif style==4: # Brocade: small leaves and pinprick gilt, dark wine silk.
        if part=='tl':
            d.rectangle((1,1,7,7),fill=bg)
            d.line((0,6,0,2),fill=i['y']);d.line((2,0,7,0),fill=i['y'])
            d.polygon([(1,4),(3,1),(5,2),(3,4)],fill=edge)
            d.polygon([(2,6),(5,3),(6,5),(4,6)],fill=i['Y'])
            d.point((2,2),fill=hot);d.point((5,5),fill=i['W'] if selected else i['G'])
        elif part=='t':
            d.line((0,0,7,0),fill=i['y']);d.line((0,2,7,2),fill=edge)
            d.point((3,1),fill=hot);d.point((4,3),fill=i['y'])
        else:
            d.line((0,0,0,7),fill=i['y']);d.line((2,0,2,7),fill=edge)
            d.point((1,3),fill=hot);d.point((3,4),fill=i['y'])
    else: # Salvaged ledger: offset joins, rivets, stitched field repairs.
        if part=='tl':
            d.polygon([(0,2),(3,2),(3,0),(7,0),(7,7),(0,7)],fill=i['o'])
            d.polygon([(1,3),(4,3),(4,1),(7,1),(7,7),(1,7)],fill=bg)
            d.line((4,1,7,1),fill=edge);d.line((1,4,1,7),fill=edge)
            d.rectangle((3,3,5,5),fill=i['y']);d.point((3,3),fill=hot)
        elif part=='t':d.line((0,0,7,0),fill=i['o']);d.line((0,2,3,2),fill=edge);d.line((6,2,7,2),fill=edge)
        else:d.line((0,0,0,7),fill=i['o']);d.line((2,0,2,3),fill=edge);d.line((2,6,2,7),fill=edge)
    return _letters(im,i)


def remixed_kit(original,index,font,style):
    """Keep semantic tile IDs while drawing new folio/cloth/repair structure."""
    base=STYLE_RECIPES[style]['design_sources'][0]
    out=kit(original,index,font,base);i=index
    for name in original:
        part=name.rsplit('_',1)[-1]
        if part in ('tl','t','l') and name.startswith(('panel_','slot_','sel_','empty_','row_','srow_','bub_','hud_')):
            out[name]=remixed_frame_tile(name,i,style);continue
        im,d=indexed(fill=i['2'])
        if name.startswith(('plate_','tab_','tabon_')):
            active=name.startswith('tabon');end='_l_' in name;top=name.endswith('top')
            d.rectangle((0,0,7,7),fill=i['2'] if active else i['3'])
            yy=0 if top else 7;edge=i['G'] if active else i['Y']
            if style==6:
                d.line((0,yy,7,yy),fill=i['y']);d.line((1,2 if top else 5,7,2 if top else 5),fill=edge)
                if end:d.line((0,3,0,5),fill=i['Y']);d.point((1,2),fill=i['W'])
                if active and top:d.line((3,4,6,4),fill=i['W'])
            elif style==7:
                d.line((0,yy,7,yy),fill=i['o']);d.line((0,2 if top else 5,2,2 if top else 5),fill=edge);d.line((5,2 if top else 5,7,2 if top else 5),fill=edge)
                if end:d.line((1,3,1,6),fill=i['y']);d.point((2,2),fill=i['G'])
                if active and top:d.point((3,4),fill=i['W'])
            elif style==8:
                d.line((0,yy,7,yy),fill=edge)
                if end:
                    d.polygon([(0,3),(2,1),(4,2),(2,4)],fill=i['G']);d.point((2,2),fill=i['W'])
                if active and top:d.line((4,3,7,3),fill=i['y'])
            elif style==9:
                d.line((0,yy,7,yy),fill=i['o']);d.line((0,1 if top else 6,7,1 if top else 6),fill=edge)
                if end:d.rectangle((1,2,3,4),fill=i['y']);d.point((2,3),fill=i['W'])
                if active and top:d.line((5,3,7,3),fill=i['G'])
            else:
                d.line((0,yy,7,yy),fill=i['y']);d.line((0,2 if top else 5,7,2 if top else 5),fill=edge)
                if end:d.polygon([(0,4),(1,1),(3,2),(2,4)],fill=i['Y']);d.point((1,2),fill=i['W'])
                if active and top:d.point((5,4),fill=i['G'])
        elif name.startswith('badge_'):
            im,d=indexed()
            if style==6:
                d.polygon([(0,3),(2,1),(7,1),(7,6),(5,7),(0,7)],fill=i['3']);d.line((2,1,6,1),fill=i['G'])
            elif style==7:
                d.rectangle((0,1,7,7),fill=i['3']);d.line((1,1,3,1),fill=i['Y']);d.point((6,6),fill=i['y'])
            elif style==8:
                d.rounded_rectangle((0,0,7,7),radius=2,fill=i['2']);d.point((1,1),fill=i['G']);d.point((6,6),fill=i['Y'])
            elif style==9:
                d.rectangle((0,0,7,7),fill=i['3']);d.rectangle((0,0,2,2),fill=i['y']);d.point((1,1),fill=i['G'])
            else:
                d.polygon([(0,3),(2,0),(7,0),(7,5),(5,7),(0,7)],fill=i['3']);d.line((1,3,3,1),fill=i['Y'])
            _,rows=font.glyph(name[-1].upper())
            for y,row in enumerate(rows[1:7]):
                for x,v in enumerate(row):
                    if v=='#' and x<5:d.point((x+1,y+1),fill=i['W'])
        elif name.startswith('div_'):
            d.line((2,0,2,7),fill=i['Y'])
            if style in (6,9,10):d.line((4,0,4,3),fill=i['y']);d.line((4,6,4,7),fill=i['y'])
            if name=='div_t':
                if style in (8,10):d.polygon([(0,4),(2,1),(4,3),(2,5)],fill=i['G'])
                elif style==9:d.rectangle((1,1,3,3),fill=i['y']);d.point((2,2),fill=i['W'])
                elif style==7:d.line((0,2,4,2),fill=i['G'])
                else:d.point((2,2),fill=i['W'])
        elif name=='bub_tail':
            im,d=indexed()
            if style in (7,9):outline=[(7,0),(7,7),(3,6),(3,4),(1,4)]
            else:outline=[(7,0),(7,6),(1,4)]
            d.polygon(outline,fill=i['Y'] if style==8 else i['y']);d.polygon([(7,1),(7,5),(3,4)],fill=i['p'])
        elif name=='bub_join':d.rectangle((0,0,7,7),fill=i['p'])
        elif name.startswith('rule'):
            y=2 if style in (7,9) else 3
            d.line((0,y,6 if name.endswith('end') else 7,y),fill=i['Y'])
            if style in (6,9):d.line((0,y+2,2,y+2),fill=i['y'])
            if name.endswith('end'):
                if style in (8,10):d.polygon([(4,y-1),(6,y),(4,y+2),(3,y)],fill=i['G'])
                elif style==9:d.point((5,y),fill=i['W']);d.point((6,y+1),fill=i['y'])
                else:d.point((6,y),fill=i['W'])
        else:continue
        out[name]=_letters(im,i)
    return out


def kit(original,index,font,style):
    """Reauthor every interface tile without changing the C-facing IDs."""
    if not style:return original
    if style>=6:return remixed_kit(original,index,font,style)
    result={};i=index
    for name in original:
        im,d=indexed(fill=i['2'])
        part=name.rsplit('_',1)[-1]
        if part in ('tl','t','l') and name.startswith(('panel_','slot_','sel_','empty_','row_','srow_','bub_','hud_')):
            result[name]=frame_tile(name,i,style);continue
        if name in ('fill','slot_fill','bub_fill'):
            d.rectangle((0,0,7,7),fill=i['p'] if name=='bub_fill' else i['3'] if name=='slot_fill' else i['2'])
        elif name.startswith(('plate_','tab_','tabon_')):
            active=name.startswith('tabon');end='_l_' in name;top=name.endswith('top')
            bg=i['3'] if not active else i['2'];d.rectangle((0,0,7,7),fill=bg)
            yy=0 if top else 7;ink=i['W'] if active else i['Y']
            if style==1:
                d.line((0,yy,7,yy),fill=ink)
                if end:d.line((0,1,0,6),fill=i['G']);d.point((1,1 if top else 6),fill=i['W'])
            elif style==2:
                d.line((0,yy,7,yy),fill=i['y']);d.line((0,1 if top else 6,7,1 if top else 6),fill=i['W'])
                if end:d.line((0,2,0,5),fill=i['y'])
                if active and top:d.line((2,4,6,4),fill=i['G'])
            elif style==3:
                d.line((0,yy,7,yy),fill=i['o']);d.line((0,2 if top else 5,7,2 if top else 5),fill=ink)
                if end:d.line((0,2,2,0),fill=i['G']);d.line((2,3,2,7),fill=i['y'])
            elif style==4:
                d.line((0,yy,7,yy),fill=i['y']);d.line((0,2 if top else 5,7,2 if top else 5),fill=ink)
                if end:d.polygon([(0,3),(2,1),(4,3),(2,5)],fill=i['G']);d.point((2,3),fill=i['W'])
            else:
                d.line((0,yy,7,yy),fill=i['o']);d.line((0,2 if top else 5,3,2 if top else 5),fill=ink)
                if end:d.rectangle((1,2,3,4),fill=i['Y']);d.point((1,2),fill=i['W'])
        elif name.startswith('badge_'):
            im,d=indexed()
            if style==2:d.rounded_rectangle((0,0,7,7),radius=2,fill=i['2']);d.arc((0,0,7,7),185,275,fill=i['y'])
            elif style==3:d.polygon([(2,0),(7,0),(7,5),(5,7),(0,7),(0,2)],fill=i['3']);d.line((1,2,3,0),fill=i['G'])
            elif style==4:d.ellipse((0,0,7,7),fill=i['3']);d.point((1,1),fill=i['G']);d.point((6,6),fill=i['Y'])
            elif style==5:d.rectangle((0,1,7,6),fill=i['3']);d.point((0,1),fill=i['G']);d.point((7,6),fill=i['y'])
            else:d.rectangle((0,0,7,7),outline=i['G'])
            _,rows=font.glyph(name[-1].upper())
            for y,row in enumerate(rows[1:7]):
                for x,v in enumerate(row):
                    if v=='#' and x<5:d.point((x+1,y+1),fill=i['c'] if style==2 else i['W'])
        elif name.startswith('div_'):
            x=2 if style in (1,5) else 3
            d.line((x,0,x,7),fill=i['Y'])
            if style in (3,4):d.line((x+2,0,x+2,7),fill=i['y'])
            if name=='div_t':
                if style==4:d.polygon([(1,3),(3,1),(6,3),(3,5)],fill=i['G'])
                elif style==3:d.line((1,1,5,5),fill=i['G'])
                else:d.point((x,2),fill=i['W'])
        elif name=='bub_tail':
            im,d=indexed();d.polygon([(7,0),(7,6),(1,4)],fill=i['y'] if style==2 else i['G'] if style==1 else i['o'])
            d.polygon([(7,1),(7,5),(3,4)],fill=i['p'])
        elif name=='bub_join':d.rectangle((0,0,7,7),fill=i['p'])
        elif name=='coin':
            im,d=indexed()
            if style==3:d.polygon([(3,0),(7,3),(4,7),(0,4)],fill=i['o']);d.polygon([(3,1),(6,3),(4,6),(1,4)],fill=i['G'])
            elif style==5:d.rectangle((1,1,6,6),fill=i['y']);d.rectangle((2,1,5,5),fill=i['G'])
            else:d.ellipse((0,0,7,7),fill=i['o']);d.ellipse((1,1,6,6),fill=i['G'])
            d.line((2,2,4,2),fill=i['W']);d.line((3,3,3,5),fill=i['y'])
        elif name=='key':
            im,d=indexed();d.ellipse((0,0,4,4),fill=i['G']);d.point((2,2),fill=i['2']);d.line((3,3,7,7),fill=i['G'],width=2);d.point((6,5),fill=i['W'])
        elif name.startswith('rule'):
            y=3 if style in (1,2,5) else 2;d.line((0,y,6 if name.endswith('end') else 7,y),fill=i['Y'])
            if style==3:d.line((0,5,7,5),fill=i['y'])
            if name.endswith('end'):
                if style==4:_glint(d,4,3,i['G'])
                else:d.point((6,y),fill=i['W'])
        else:raise KeyError(name)
        result[name]=_letters(im,i)
    return result


def marks(original,index,style):
    if not style:return original
    if style>=6:return remixed_marks(index,style)
    out={};i=index
    for name in ('next','pick','corner'):
        im,d=indexed()
        if name=='next':
            if style==2:d.line([(1,2),(3,5),(6,2)],fill=i['c'],width=1)
            elif style==3:d.polygon([(0,1),(7,1),(4,6),(3,6)],fill=i['o']);d.line((2,2,5,2),fill=i['G']);d.line((3,3,4,3),fill=i['W'])
            elif style==4:d.polygon([(3,0),(6,3),(3,7),(0,3)],fill=i['o']);d.polygon([(3,1),(5,3),(3,6),(1,3)],fill=i['G']);d.point((3,2),fill=i['W'])
            else:d.line([(1,2),(3,4),(5,2)],fill=i['G']);d.point((3,5),fill=i['W'])
        elif name=='pick':
            if style==4:d.polygon([(0,3),(3,0),(7,3),(3,7)],fill=i['o']);d.polygon([(1,3),(3,1),(5,3),(3,5)],fill=i['G'])
            elif style==2:d.line([(1,1),(5,3),(1,6)],fill=i['c'],width=2)
            elif style==5:d.rectangle((1,2,6,5),fill=i['G']);d.point((1,2),fill=i['W'])
            else:d.polygon([(1,0),(6,3),(1,7)],fill=i['o']);d.line([(2,1),(5,3),(2,6)],fill=i['G'])
        else:
            if style==4:d.polygon([(0,5),(2,2),(5,0),(4,3),(2,4)],fill=i['G']);d.point((2,2),fill=i['W'])
            elif style==3:d.line([(0,7),(0,4),(4,0),(7,0)],fill=i['G'])
            elif style==5:d.line([(1,6),(1,1),(6,1)],fill=i['Y']);d.rectangle((0,0,2,2),fill=i['G'])
            else:d.line([(0,6),(0,0),(6,0)],fill=i['G']);d.point((1,1),fill=i['W'])
        out[name]=_letters(im,i)
    return out


def remixed_marks(index,style):
    """The same down/right/corner meanings, in five related constructions."""
    out={};i=index
    for name in ('next','pick','corner'):
        im,d=indexed()
        if name=='next':
            if style==6:
                d.line([(1,2),(3,5),(6,2)],fill=i['o'],width=3)
                d.line([(1,2),(3,5),(6,2)],fill=i['G']);d.point((3,6),fill=i['W'])
            elif style==7:
                d.polygon([(1,1),(6,1),(6,3),(4,6),(2,4)],fill=i['Y']);d.line((2,2,5,2),fill=i['W'])
            elif style==8:
                d.line([(0,2),(3,5),(6,2)],fill=i['G']);d.point((3,6),fill=i['W']);d.point((3,1),fill=i['y'])
            elif style==9:
                d.rectangle((1,1,6,3),fill=i['y']);d.polygon([(1,3),(6,3),(4,6),(3,6)],fill=i['G']);d.point((3,3),fill=i['W'])
            else:
                d.polygon([(0,2),(3,1),(3,4),(6,2),(5,5),(3,7),(1,5)],fill=i['G']);d.point((3,5),fill=i['W'])
        elif name=='pick':
            if style==6:
                d.polygon([(1,0),(6,3),(6,4),(1,7)],fill=i['o']);d.line([(2,1),(5,3),(2,6)],fill=i['G']);d.line((2,2,2,5),fill=i['W'])
            elif style==7:
                d.polygon([(0,1),(3,1),(6,3),(6,4),(3,6),(0,6)],fill=i['Y']);d.line((1,2,3,2),fill=i['W'])
            elif style==8:
                d.polygon([(1,1),(4,2),(7,3),(4,5),(1,6),(3,3)],fill=i['G']);d.point((4,3),fill=i['W'])
            elif style==9:
                d.rectangle((0,1,2,6),fill=i['y']);d.polygon([(2,1),(7,3),(7,4),(2,6)],fill=i['G']);d.point((3,3),fill=i['W'])
            else:
                d.polygon([(1,0),(3,3),(6,3),(5,5),(1,7),(2,4)],fill=i['G']);d.point((3,3),fill=i['W'])
        else:
            if style==6:
                d.line([(0,7),(0,4),(2,1),(6,0)],fill=i['G']);d.line((2,3,5,1),fill=i['y']);d.point((2,2),fill=i['W'])
            elif style==7:
                d.line([(0,7),(0,3),(3,3),(3,0),(7,0)],fill=i['Y']);d.point((2,2),fill=i['W'])
            elif style==8:
                d.polygon([(0,5),(1,2),(4,0),(4,2),(2,4)],fill=i['G']);d.line((1,6,1,3),fill=i['y']);d.point((2,2),fill=i['W'])
            elif style==9:
                d.line([(0,7),(0,0),(7,0)],fill=i['Y']);d.rectangle((0,0,2,2),fill=i['y']);d.point((1,1),fill=i['W'])
            else:
                d.polygon([(0,5),(2,1),(4,2),(2,4)],fill=i['Y']);d.polygon([(2,6),(4,3),(6,4),(4,6)],fill=i['G']);d.point((2,2),fill=i['W'])
        out[name]=_letters(im,i)
    return out


def heart_tiles(original,index,style):
    """Transparent8px hearts with ink-bound silhouettes on every background."""
    out={};i=index
    for name in original:
        if not name.startswith('heart'):
            out[name]=original[name];continue
        im,d=indexed()
        d.polygon([(0,2),(1,1),(3,1),(4,2),(5,1),(6,1),(7,2),(7,4),(4,7),(0,4)],fill=i['o'])
        body=i['r'] if name=='heart_full' else i['3']
        d.polygon([(1,2),(3,2),(4,3),(5,2),(6,2),(6,4),(4,6),(1,4)],fill=body)
        if name=='heart_half':d.polygon([(1,2),(3,2),(4,3),(4,6),(1,4)],fill=i['r'])
        if name!='heart_empty':d.point((2,2),fill=i['W']);d.point((2,3),fill=i['q'])
        else:d.line((2,2,3,3),fill=i['4'])
        if style==3:d.point((0,2),fill=0);d.point((7,2),fill=0)
        if style==5:d.point((6,2),fill=i['s'])
        out[name]=[''.join('.' if not im.getpixel((x,y)) else list(index)[im.getpixel((x,y))-1] for x in range(8)) for y in range(8)]
    return out


def hud_icon(name):
    """A separately authored10px glyph, not a clipped16px world pickup.

    Existing per-frame material palettes remain in force: bomb=blight,
    cloak=foliage, blade/hubcap=stone, other equipment=gold.
    """
    im,d=indexed(16,16)
    # Work directly inside x2..11,y1..10. The black silhouette is a native
    # one-pixel ink contour; each material uses only two/three useful planes.
    if name=='none':return im
    if name=='sword':
        d.line((3,9,10,2),fill=1,width=3);d.line((3,9,10,2),fill=7);d.line((4,8,10,2),fill=8)
        d.line((3,5,7,9),fill=1,width=3);d.line((3,5,7,9),fill=12);d.line((3,8,4,9),fill=11)
    elif name in ('shield','shield_upgraded'):
        if name=='shield':pts=[(2,2),(10,2),(11,5),(9,9),(6,10),(3,9),(2,6)]
        else:pts=[(2,1),(11,1),(11,6),(9,9),(6,10),(3,8),(2,5)]
        d.polygon(pts,fill=1);d.polygon([(3,3),(10,3),(9,7),(6,9),(4,7)],fill=10)
        d.polygon([(4,3),(9,3),(8,7),(6,8),(4,6)],fill=13 if name.endswith('upgraded') else 4)
        d.line((5,3,5,6),fill=14 if name.endswith('upgraded') else 6);d.point((3,3),fill=12)
    elif name=='bombs':
        d.ellipse((2,3,10,10),fill=1);d.ellipse((3,4,9,9),fill=4)
        d.polygon([(4,4),(6,4),(7,6),(5,7),(4,6)],fill=6);d.point((4,4),fill=14)
        d.line([(7,3),(7,2),(9,1),(10,2)],fill=10);d.point((10,1),fill=15)
    elif name=='lamp':
        d.rectangle((4,2,9,3),fill=1);d.line((5,1,8,1),fill=10)
        d.rectangle((3,3,10,10),fill=1);d.rectangle((4,4,9,9),fill=7)
        d.rectangle((5,4,8,8),fill=3);d.line((6,5,6,8),fill=11);d.point((6,6),fill=12)
        d.line((4,9,9,9),fill=10);d.point((4,4),fill=12)
    elif name=='cloak':
        d.polygon([(6,1),(9,2),(10,5),(9,6),(11,10),(7,9),(5,10),(2,9),(4,5),(4,2)],fill=1)
        d.polygon([(6,2),(8,2),(9,4),(7,5),(4,8),(3,9),(6,8),(8,9),(9,8),(8,5)],fill=4)
        d.polygon([(6,2),(7,2),(5,4),(5,6),(4,7),(5,3)],fill=6);d.point((7,6),fill=11)
    elif name=='bow':
        d.line([(3,2),(7,3),(10,5),(10,7),(7,8),(3,9)],fill=1,width=3)
        d.line([(3,1),(7,3),(9,5),(9,7),(6,9),(3,10)],fill=6)
        d.line((3,2,3,9),fill=11);d.line((5,5,10,5),fill=10);d.point((6,2),fill=14)
    elif name=='hubcap':
        d.ellipse((2,1,11,10),fill=1);d.ellipse((3,2,10,9),fill=5);d.arc((3,2,10,9),185,280,fill=8)
        for x,y in ((5,3),(8,4),(5,7),(8,7)):d.rectangle((x,y,x+1,y+1),fill=2)
    elif name in ('heart_piece','heart_container'):
        d.polygon([(2,3),(4,2),(6,4),(8,2),(10,3),(11,5),(6,10),(2,6)],fill=1)
        d.polygon([(3,4),(4,3),(6,5),(8,3),(9,4),(10,5),(6,9),(3,6)],fill=3)
        if name=='heart_piece':d.polygon([(6,5),(10,4),(10,6),(6,9)],fill=1)
        d.line((4,4,5,5),fill=7)
    elif name=='key':
        d.ellipse((2,1,8,7),fill=1);d.ellipse((3,2,7,6),fill=10);d.rectangle((4,3,6,5),fill=1)
        d.line((7,6,10,9),fill=10,width=2);d.point((9,7),fill=12);d.point((3,2),fill=12)
    elif name in ('gilt_big','relic','astrolabe'):
        d.polygon([(6,1),(11,5),(6,10),(2,5)],fill=1);d.polygon([(6,2),(10,5),(6,9),(3,5)],fill=9)
        d.line((6,2,6,8),fill=12);d.line((3,5,9,5),fill=11)
    elif name=='gauntlet':
        d.polygon([(2,5),(4,1),(6,1),(6,4),(8,1),(10,2),(10,5),(11,6),(9,10),(4,10)],fill=1)
        d.polygon([(3,6),(5,3),(5,6),(7,4),(8,3),(9,4),(8,6),(10,6),(8,9),(4,9)],fill=8)
        d.line((4,8,8,9),fill=11);d.point((4,6),fill=12)
    elif name=='map':
        d.polygon([(2,2),(5,1),(8,3),(11,2),(10,10),(7,9),(4,10),(2,9)],fill=1)
        d.polygon([(3,3),(5,2),(8,4),(10,3),(9,9),(7,8),(4,9),(3,8)],fill=11)
        d.line([(5,3),(5,7),(7,6),(9,7)],fill=4)
    else:raise KeyError(name)
    assert im.getbbox() is None or (im.getbbox()[0]>=2 and im.getbbox()[1]>=1 and im.getbbox()[2]<=12 and im.getbbox()[3]<=11),(name,im.getbbox())
    return im


def apply(namespace):
    """Install study art after the baseline semantic kit has been declared."""
    style=VARIANT
    if style:
        pal=[(key,tuple(int(theme()[key][j:j+2],16) for j in (1,3,5))) for key in namespace['KEYS']]
        namespace['PAL']=pal;namespace['RGB']=dict(pal)
        namespace['cursor']=lambda:selection_cursor(style)
        namespace['TILES']=kit(namespace['TILES'],namespace['INDEX'],namespace['F'],style)
        marks_=marks(namespace['OBJ_MARKS'],namespace['INDEX'],style)
        for name in ('badge_a','badge_b','badge_l'):marks_[name]=namespace['TILES'][name]
        namespace['OBJ_MARKS']=marks_
        # Keep real map semantics in the map bank, changing only its neutral
        # paper/ink field to coordinate the cartography with each interface.
        mp=namespace['MAP_PAL'][:]
        for pos,key in ((0,'o'),(1,'2'),(2,'4'),(12,'3'),(14,'c')):
            mp[pos]=(mp[pos][0],dict(pal)[key])
        namespace['MAP_PAL']=mp;namespace['MAP_RGB']=dict(mp)
        namespace['OBJ_PAL']=[(k,namespace['MAP_RGB']['g'] if k=='p' else namespace['MAP_RGB']['G'] if k=='b' else col) for k,col in pal]
        if style>=6:
            # Dark palette material carries through to the small HUD pods.
            # Health reds and actual equipment palettes retain their meanings.
            roles={'o':'o','2':'2','3':'3','4':'4','W':'W','c':'c','s':'s',
                   'g':'y','G':'G','b':'y','h':'W','n':'2'}
            namespace['HUD_PAL']=[(key,dict(pal)[roles[key]] if key in roles else color)
                                  for key,color in namespace['HUD_PAL']]
    namespace['HUD_INDEX']['.']=0
    namespace['HUD_TILES']=heart_tiles(namespace['HUD_TILES'],namespace['HUD_INDEX'],style)
    namespace['GROUPS'].update({'menu':namespace['hexpal'](namespace['PAL']),
                               'map':namespace['hexpal'](namespace['MAP_PAL']),
                               'hud':namespace['hexpal'](namespace['HUD_PAL']),
                               'ui':namespace['hexpal'](namespace['OBJ_PAL']),
                               'uikit':namespace['hexpal'](namespace['OBJ_PAL'])})


def selection_cursor(style):
    """Native32px inventory cursor around the existing24px-tall cell."""
    im,d=indexed(32,32)
    if style>=6:
        for x,y,sx,sy in ((0,0,1,1),(31,0,-1,1),(0,23,1,-1),(31,23,-1,-1)):
            if style==6:
                d.polygon([(x,y+sy*7),(x,y+sy*3),(x+sx*3,y),(x+sx*8,y),(x+sx*3,y+sy*3)],fill=6)
                d.line([(x,y+sy*7),(x,y+sy*3),(x+sx*3,y),(x+sx*8,y)],fill=8)
                d.point((x+sx*2,y+sy*2),fill=9)
            elif style==7:
                d.line([(x,y+sy*8),(x,y+sy*4),(x+sx*4,y+sy*4),(x+sx*4,y),(x+sx*8,y)],fill=1,width=3)
                d.line([(x,y+sy*8),(x,y+sy*4),(x+sx*4,y+sy*4),(x+sx*4,y),(x+sx*8,y)],fill=8)
                d.point((x+sx*2,y+sy*2),fill=9)
            elif style==8:
                d.line((x,y+sy*7,x,y),fill=6);d.line((x,y,x+sx*7,y),fill=6)
                d.polygon([(x+sx,y+sy*5),(x+sx*2,y+sy*2),(x+sx*5,y+sy),(x+sx*4,y+sy*3)],fill=8)
                d.point((x+sx*2,y+sy*2),fill=9)
            elif style==9:
                d.line((x,y,x+sx*9,y),fill=8);d.line((x,y,x,y+sy*9),fill=8)
                d.line((x+sx*3,y+sy*6,x+sx*3,y+sy*3),fill=6);d.line((x+sx*3,y+sy*3,x+sx*6,y+sy*3),fill=6)
                d.rectangle((min(x,x+sx*2),min(y,y+sy*2),max(x,x+sx*2),max(y,y+sy*2)),fill=7);d.point((x+sx,y+sy),fill=9)
            else:
                d.line([(x,y+sy*8),(x,y+sy*3),(x+sx*3,y),(x+sx*8,y)],fill=6)
                d.polygon([(x+sx,y+sy*6),(x+sx*2,y+sy*2),(x+sx*5,y+sy),(x+sx*4,y+sy*4)],fill=8)
                d.polygon([(x+sx*4,y+sy*7),(x+sx*5,y+sy*4),(x+sx*7,y+sy*5)],fill=7)
                d.point((x+sx*2,y+sy*2),fill=9)
        return [''.join('%x'%im.getpixel((x,y)) for x in range(32)) for y in range(32)]
    if style==1:
        for x,y,sx,sy in ((0,0,1,1),(31,0,-1,1),(0,23,1,-1),(31,23,-1,-1)):
            d.line((x,y+sy*6,x,y),fill=1);d.line((x,y,x+sx*6,y),fill=8)
            d.point((x+sx,y+sy),fill=9)
    elif style==2:
        for x,y,sx,sy in ((0,0,1,1),(31,0,-1,1),(0,23,1,-1),(31,23,-1,-1)):
            d.polygon([(x,y),(x+sx*7,y),(x+sx*2,y+sy*3),(x,y+sy*6)],fill=8)
            d.line((x+sx,y+sy,x+sx*5,y+sy),fill=9)
    elif style==3:
        for x,y,sx,sy in ((0,0,1,1),(31,0,-1,1),(0,23,1,-1),(31,23,-1,-1)):
            pts=[(x,y+sy*7),(x,y+sy*4),(x+sx*4,y),(x+sx*7,y)]
            d.line(pts,fill=1,width=3);d.line(pts,fill=8)
            d.point((x+sx*3,y+sy),fill=9)
    elif style==4:
        for x,y,sx,sy in ((0,0,1,1),(31,0,-1,1),(0,23,1,-1),(31,23,-1,-1)):
            d.line((x,y,x+sx*8,y),fill=6);d.line((x,y,x,y+sy*8),fill=6)
            d.polygon([(x,y+sy*6),(x+sx*2,y+sy*2),(x+sx*6,y),(x+sx*5,y+sy*3),(x+sx*3,y+sy*5)],fill=8)
            d.point((x+sx*2,y+sy*2),fill=9)
    else:
        for x,y,sx,sy in ((0,0,1,1),(31,0,-1,1),(0,23,1,-1),(31,23,-1,-1)):
            d.line((x,y+sy*6,x,y),fill=1,width=3);d.line((x,y,x+sx*6,y),fill=8,width=2)
            d.rectangle((min(x,x+sx*2),min(y,y+sy*2),max(x,x+sx*2),max(y,y+sy*2)),fill=7)
            d.point((x,y),fill=9)
    return [''.join('%x'%im.getpixel((x,y)) for x in range(32)) for y in range(32)]
