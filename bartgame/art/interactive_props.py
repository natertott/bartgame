"""Large, readable interactive furniture in the existing lift OBJ palette.

Each chest is a 32x32 streamed frame. Entrances use 32x64, with the opening
and threshold aligned to the original 16px interaction tile. Transparent
corners preserve the scene; no floor rectangle is carried with the artwork.
These sheets share PAL_OBJ_LIFT and do not change any item or Bloom palette.
"""
from PIL import Image, ImageDraw

# Existing lift palette: outline, leaves, stone, cream, wood, brass and teal.
CLEAR, INK, LEAF_DARK, LEAF, LEAF_LIGHT, LEAF_TIP = range(6)
STONE_DARK, STONE, STONE_LIGHT, CREAM = 6, 7, 8, 9
WOOD_DARK, WOOD, WOOD_LIGHT, GOLD, GOLD_LIGHT, TEAL = range(10,16)


def _canvas(w,h):
    im=Image.new('P',(w,h),CLEAR)
    return im,ImageDraw.Draw(im)


def _rows(im):
    return [''.join('%x'%im.getpixel((x,y)) if im.getpixel((x,y)) else '.'
                    for x in range(im.width)) for y in range(im.height)]


def chest(kind,opened=False):
    """Wooden coffer, brass-banded chest and wide ceremonial green reliquary."""
    im,d=_canvas(32,32)
    tier={'wooden':0,'brass':1,'relic':2}[kind]
    left,right=5-tier,26+tier
    top=11-tier; bottom=29
    band=STONE if tier==0 else GOLD
    band_hi=STONE_LIGHT if tier==0 else GOLD_LIGHT
    body=WOOD if tier<2 else LEAF_DARK
    body_light=WOOD_LIGHT if tier<2 else LEAF
    # A connected shallow contact shadow, never a rectangular ground patch.
    d.line((left+2,30,right-1,30),fill=INK)
    d.polygon([(left,top+4),(left+2,top+1),(right-2,top),
               (right,top+3),(right,bottom-2),(right-2,bottom),
               (left+2,bottom),(left,bottom-2)],fill=INK)
    # Body: broad, quiet panels and a dark bevel at the bottom/right.
    d.rectangle((left+1,top+7,right-1,bottom-2),fill=WOOD_DARK)
    d.rectangle((left+2,top+8,right-3,bottom-3),fill=body)
    d.line((left+3,bottom-4,right-4,bottom-4),fill=body_light)
    d.line((right-2,top+8,right-2,bottom-3),fill=INK)
    if tier<2:
        # Only two grain cuts so this reads as wood at native resolution.
        d.line((left+4,top+10,left+9,top+10),fill=WOOD_DARK)
        d.line((right-9,bottom-6,right-5,bottom-6),fill=WOOD_DARK)
    else:
        d.rectangle((left+4,top+10,right-5,bottom-6),fill=LEAF)
        d.line((left+4,top+10,right-5,top+10),fill=LEAF_LIGHT)
        d.line((left+4,top+11,left+4,bottom-6),fill=LEAF_LIGHT)
    # Closed lid or raised lid. Both retain the same floor contact and width.
    if not opened:
        d.polygon([(left+1,top+5),(left+3,top+2),(right-3,top+1),
                   (right-1,top+4),(right-1,top+9),(left+1,top+9)],fill=WOOD_DARK)
        d.polygon([(left+2,top+5),(left+4,top+3),(right-4,top+2),
                   (right-2,top+4),(right-2,top+7),(left+2,top+7)],fill=body_light)
        d.line((left+4,top+3,right-4,top+2),fill=GOLD if tier==0 else GOLD_LIGHT)
        d.line((left+1,top+9,right-1,top+9),fill=INK)
        d.line((left+2,top+8,right-2,top+8),fill=WOOD)
        if tier==2:
            d.rectangle((left+7,top+4,right-7,top+7),fill=LEAF_DARK)
            d.line((left+7,top+4,right-7,top+4),fill=LEAF_LIGHT)
    else:
        raised=7-tier
        d.polygon([(left,raised+3),(left+3,raised),(right-3,raised),
                   (right,raised+3),(right,top+6),(left,top+6)],fill=INK)
        d.rectangle((left+2,raised+3,right-2,top+5),fill=WOOD_DARK)
        d.rectangle((left+3,raised+3,right-3,top+3),fill=body)
        d.line((left+3,raised+2,right-3,raised+2),fill=band_hi)
        d.line((left+2,raised+3,left+2,top+5),fill=band)
        d.line((right-2,raised+3,right-2,top+5),fill=band)
        # Dark oval mouth and bright continuous front rim clearly read open.
        d.rectangle((left+1,top+7,right-1,top+11),fill=INK)
        d.line((left+2,top+7,right-2,top+7),fill=WOOD_DARK)
        d.line((left+2,top+12,right-2,top+12),fill=band_hi)
    # Broad bands are attached to the lid/body, not disconnected sparkles.
    for bx in (left+3,right-5):
        if not opened:
            d.line((bx,top+3,bx,top+8),fill=band_hi,width=2)
        d.rectangle((bx,top+13 if opened else top+10,bx+1,bottom-3),fill=band)
        d.point((bx, bottom-4),fill=band_hi)
    # Latch: common treasure affordance, intentionally very visible.
    if not opened:
        d.rectangle((14,top+7,18,top+14),fill=INK)
        d.rectangle((14,top+7,17,top+13),fill=GOLD)
        d.line((14,top+7,17,top+7),fill=GOLD_LIGHT)
        d.rectangle((15,top+9,16,top+10),fill=INK)
        d.point((16,top+11),fill=INK)
    if tier==1:
        # Brass lower rim makes the medium tier identifiable without a glow.
        d.line((left+2,bottom-2,right-2,bottom-2),fill=GOLD)
        for x in (left+2,right-2):d.point((x,bottom-3),fill=GOLD_LIGHT)
    elif tier==2:
        d.line((left+2,bottom-2,right-2,bottom-2),fill=GOLD)
        for x in (left+1,right-2):
            d.rectangle((x,bottom-5,x+1,bottom-2),fill=GOLD_LIGHT)
        if not opened:
            # A small turquoise seal is part of the central brass clasp.
            d.polygon([(16,top+8),(20,top+12),(16,top+16),(12,top+12)],fill=INK)
            d.polygon([(16,top+9),(19,top+12),(16,top+15),(13,top+12)],fill=GOLD_LIGHT)
            d.polygon([(16,top+10),(18,top+12),(16,top+14),(14,top+12)],fill=TEAL)
            d.line((15,top+11,16,top+10),fill=CREAM)
    return _rows(im)


def _opening(d):
    # The doorway itself is 20x31px; a head-height black void, not a small
    # floor mark. Four attached inner highlights give the arch some depth.
    d.polygon([(6,60),(6,32),(8,27),(12,24),(19,24),(23,27),(25,32),(25,60)],fill=INK)
    d.line((7,35,7,57),fill=WOOD_DARK)
    d.line((24,35,24,57),fill=STONE_DARK)
    d.line((9,28,12,26),fill=WOOD_DARK)
    d.line((20,26,23,29),fill=STONE_DARK)
    d.rectangle((8,57,23,59),fill=WOOD_DARK)
    d.line((9,58,22,58),fill=WOOD)
    d.line((6,61,25,61),fill=INK,width=2)
    d.line((6,60,25,60),fill=GOLD)
    d.line((8,60,22,60),fill=GOLD_LIGHT)


def entrance(kind,closed=False):
    """A large threshold with a warm rim that survives bright violet scenes."""
    im,d=_canvas(32,64)
    outer=[(0,60),(0,32),(2,25),(6,20),(11,17),(20,17),
           (25,20),(29,25),(31,32),(31,60),(29,63),(2,63)]
    d.polygon(outer,fill=INK)
    inner=[(2,60),(2,33),(4,27),(8,22),(12,20),(19,20),
           (23,22),(27,27),(29,33),(29,60)]
    if kind=='cave':
        d.polygon(inner,fill=STONE)
        # Heavy cut-stone arch stones, lit on the top-left edge.
        d.line([(3,59),(3,33),(5,27),(9,23),(13,21),(19,21),(23,23),(27,28)],fill=STONE_LIGHT,width=2)
        d.line([(28,33),(28,59)],fill=STONE_DARK,width=2)
        for points in [[(1,35),(7,35)],[(1,44),(7,43)],[(1,53),(7,53)],
                       [(25,35),(30,36)],[(25,45),(30,45)],[(25,54),(30,54)],
                       [(6,22),(10,27)],[(13,18),(13,24)],[(20,18),(19,24)],[(26,23),(22,28)]]:
            d.line(points,fill=INK)
        d.line((5,31,7,28),fill=CREAM)
        d.line((12,21,17,21),fill=CREAM)
        # A gold keystone is a consistent wayfinding cue across all styles.
        d.polygon([(13,18),(18,18),(18,24),(16,26),(13,24)],fill=GOLD)
        d.line((14,19,17,19),fill=GOLD_LIGHT)
        # Angular chipped margins distinguish a rock mouth from built timber.
        d.polygon([(0,35),(2,34),(2,37),(0,38)],fill=CLEAR)
        d.polygon([(29,47),(31,46),(31,50),(30,50)],fill=CLEAR)
        d.polygon([(1,29),(3,26),(5,29),(4,33),(2,33)],fill=STONE_DARK)
        d.line([(2,29),(3,27),(4,29)],fill=STONE_LIGHT)
        d.polygon([(27,39),(30,37),(30,43),(28,45)],fill=STONE_DARK)
        d.line([(28,39),(29,38),(29,42)],fill=STONE_LIGHT)
        d.line((2,55,5,57),fill=STONE_DARK)
    elif kind=='hollow':
        d.polygon(inner,fill=WOOD)
        d.line([(3,59),(3,35),(5,28),(9,23),(13,21),(20,21),(25,25)],fill=WOOD_LIGHT,width=2)
        d.line([(28,59),(28,34),(26,29)],fill=WOOD_DARK,width=2)
        # Long bark grain follows the arch, rather than disguising the hole.
        for points in [[(1,51),(3,47),(2,39)],[(5,59),(4,53)],
                       [(28,53),(27,47),(29,41)],[(8,23),(10,25)],[(21,22),(23,26)]]:
            d.line(points,fill=INK)
        d.line((4,34,4,43),fill=GOLD)
        d.line((26,35,26,41),fill=WOOD_LIGHT)
        d.polygon([(13,19),(18,19),(18,23),(16,25),(13,23)],fill=GOLD)
        d.line((14,20,17,20),fill=GOLD_LIGHT)
        # A hollow is part of a living trunk: visible knots and spreading roots.
        d.polygon([(0,56),(3,48),(5,45),(6,54),(9,61),(7,63),(1,63)],fill=INK)
        d.polygon([(1,60),(3,52),(4,50),(4,56),(7,61),(5,62)],fill=WOOD)
        d.line([(2,60),(3,56),(4,56),(6,61)],fill=WOOD_LIGHT)
        d.polygon([(25,49),(28,52),(31,58),(31,63),(26,63),(23,60)],fill=INK)
        d.polygon([(26,53),(28,56),(30,61),(26,61),(25,58)],fill=WOOD)
        d.line([(26,55),(28,58),(28,61)],fill=WOOD_LIGHT)
        d.ellipse((1,33,5,40),fill=WOOD_DARK)
        d.line([(2,36),(3,34),(4,36),(3,39)],fill=WOOD_LIGHT)
        d.line([(28,45),(26,42),(27,39)],fill=WOOD_LIGHT)
    elif kind=='thicket':
        # Woven bronze-brown branches are structural; leaves frame the void.
        d.polygon(inner,fill=WOOD_DARK)
        d.line([(3,60),(3,35),(6,28),(11,23),(16,20),(21,23),(26,28),(28,35),(28,60)],fill=WOOD_LIGHT,width=3)
        d.line([(4,59),(4,36),(8,28),(16,22),(24,28),(27,36),(27,59)],fill=GOLD)
        for x,y,flip in [(2,32,False),(3,42,False),(2,51,False),
                         (28,33,True),(28,43,True),(28,52,True),
                         (8,24,False),(23,24,True)]:
            dx=-1 if flip else 1
            d.polygon([(x,y+4),(x-dx*2,y),(x,y-4),(x+dx*3,y-2),(x+dx*2,y+2)],fill=LEAF_DARK)
            d.line((x,y+1,x+dx,y-2),fill=LEAF_LIGHT)
            d.point((x+dx,y-2),fill=LEAF_TIP)
        d.polygon([(13,19),(18,19),(18,23),(16,25),(13,23)],fill=GOLD)
        d.line((14,20,17,20),fill=GOLD_LIGHT)
        # Dense pointed sprays form leafy pilasters, not isolated green dots.
        for cx,cy in [(3,30),(2,39),(3,48),(2,57),(28,31),(29,40),(28,49),(29,57),
                      (8,24),(23,24),(12,20),(20,20)]:
            d.polygon([(cx-3,cy+1),(cx-3,cy-2),(cx-1,cy-4),(cx+2,cy-3),
                       (cx+3,cy),(cx+2,cy+3),(cx,cy+4)],fill=INK)
            d.polygon([(cx-2,cy),(cx-2,cy-2),(cx,cy-3),(cx+2,cy-1),
                       (cx+2,cy+2),(cx,cy+3)],fill=LEAF_DARK)
            d.polygon([(cx-2,cy-1),(cx,cy-3),(cx+1,cy-1),(cx,cy+1)],fill=LEAF)
            d.line([(cx-1,cy-1),(cx,cy-2)],fill=LEAF_LIGHT)
            d.point((cx,cy-2),fill=LEAF_TIP)
    else:
        raise ValueError(kind)
    # Restore the shared bright keystone above the leafy organic crown.
    if kind=='thicket':
        d.polygon([(14,18),(17,18),(18,21),(16,24),(13,21)],fill=GOLD)
        d.line((14,19,17,19),fill=GOLD_LIGHT)
    _opening(d)
    if closed:
        # Trial bars fill the same opening without introducing a key-lock
        # symbol: clearing the encounter, not finding a different key, opens it.
        if kind=='cave':
            for x in (9,14,19,23):
                d.line((x,29 if x in (14,19) else 33,x,58),fill=STONE_DARK,width=3)
                d.line((x,29 if x in (14,19) else 33,x,58),fill=STONE_LIGHT)
            d.line((8,36,23,36),fill=STONE,width=2)
            d.line((8,52,23,52),fill=STONE,width=2)
        elif kind=='hollow':
            d.polygon([(8,58),(8,33),(11,28),(20,28),(23,33),(23,58)],fill=WOOD_DARK)
            for x in (10,15,20):
                d.rectangle((x,31 if x==15 else 34,x+1,58),fill=WOOD)
                d.line((x,32 if x==15 else 35,x,56),fill=WOOD_LIGHT)
            d.line((9,36,22,36),fill=GOLD)
            d.line((9,53,22,53),fill=GOLD)
        else:
            for points in [[(8,32),(22,53),(21,58)],[(22,31),(10,51),(11,58)],
                           [(8,44),(20,58)],[(23,43),(12,58)]]:
                d.line(points,fill=WOOD_DARK,width=4)
                d.line(points,fill=WOOD_LIGHT,width=2)
            d.line((10,33,11,36),fill=LEAF_LIGHT,width=2)
            d.line((21,49,20,52),fill=LEAF_LIGHT,width=2)
        # One heavy common crossbar unmistakably marks the shut state.
        d.rectangle((7,42,24,46),fill=INK)
        d.rectangle((8,42,23,45),fill=GOLD)
        d.line((8,42,23,42),fill=GOLD_LIGHT)
        d.point((10,44),fill=WOOD_DARK)
        d.point((21,44),fill=WOOD_DARK)
    # Attached brass jamb marks are readable against either forest material.
    for x in (3,28):
        d.rectangle((x-1,38,x+1,43),fill=INK)
        d.line((x,39,x,42),fill=GOLD)
        d.point((x,39),fill=GOLD_LIGHT)
    # Low moss outside the threshold gives contact without hiding its edge.
    for x in (0,1,29,30):
        d.line((x,60,x,62),fill=LEAF_DARK)
    for y in range(17):
        for x in range(32):im.putpixel((x,y),CLEAR)
    return _rows(im)


CHESTS={f'{kind}_{state}':chest(kind,state=='open')
        for kind in ('wooden','brass','relic') for state in ('closed','open')}
ENTRIES={kind:entrance(kind) for kind in ('cave','hollow','thicket')}
ENTRIES.update({kind+'_closed':entrance(kind,True) for kind in ('cave','hollow','thicket')})
SHEETS=[{'name':'interactivechest','pal':'lift','w':32,'h':32,'frames':CHESTS},
        {'name':'interactiveentry','pal':'lift','w':32,'h':64,'frames':ENTRIES}]


def preview(path):
    """Source-only scale comparison, explicitly not an emulator capture."""
    import pack
    from PIL import ImageFont
    palette=pack.GROUPS['lift']
    def rgba(rows,pal):
        img=Image.new('RGBA',(len(rows[0]),len(rows)),(0,0,0,0))
        for y,row in enumerate(rows):
            for x,ch in enumerate(row):
                if ch not in '.0':img.putpixel((x,y),(*tuple(bytes.fromhex(pal[int(ch,16)][1:])),255))
        return img
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
    out=Image.new('RGB',(1000,600),'#101820');d=ImageDraw.Draw(out)
    d.text((12,10),'Interactive prop source art / 1x and 4x scale / not an emulator capture',font=font,fill='#fff0cb')
    for i,(name,rows) in enumerate(CHESTS.items()):
        x=14+i*162;y=40;img=rgba(rows,palette)
        d.rectangle((x,y,x+143,y+143),fill='#24403d')
        out.paste(img.resize((128,128),Image.Resampling.NEAREST),(x+8,y+8),img.resize((128,128),Image.Resampling.NEAREST))
        out.paste(img,(x+58,y+148),img)
        d.text((x,y+183),name,font=font,fill='#fff0cb')
    for i,(name,rows) in enumerate(list(ENTRIES.items())[:3]):
        x=18+i*244;y=262;img=rgba(rows,palette)
        # Door enlarged2x here to fit the complete 64px authored canvas.
        d.rectangle((x,y,x+224,y+263),fill='#24403d')
        big=img.resize((128,256),Image.Resampling.NEAREST)
        out.paste(big,(x+8,y+8),big);out.paste(img,(x+162,y+200),img)
        d.text((x,y+278),name+' / 4x and 1x',font=font,fill='#fff0cb')
    hero=rgba(pack.frames('hero')['idle_s'],pack.GROUPS[pack.group('hero')])
    big=hero.resize((256,128),Image.Resampling.NEAREST)
    out.paste(big,(744,398),big);out.paste(hero,(900,535),hero)
    d.text((756,574),'Bloom / same 4x and 1x scale',font=font,fill='#fff0cb')
    out.save(path)
    return path


def comparison_preview(path):
    """Before/after source silhouettes on real ground swatches, not gameplay."""
    import tiles,palettes,pack
    from PIL import ImageFont
    metas={m['name']:m for m in tiles.METATILES}
    pals=dict(palettes.BG_PALETTES)
    def rgba(rows,pal):
        img=Image.new('RGBA',(len(rows[0]),len(rows)),(0,0,0,0))
        for y,row in enumerate(rows):
            for x,ch in enumerate(row):
                if ch not in '.0':img.putpixel((x,y),(*tuple(bytes.fromhex(pal[int(ch,16)][1:])),255))
        return img
    def tile(name):
        m=metas[name];r=(m.get('frames') or [m['art']])[0]
        return rgba(r,pals[m['pal']])
    cases=[('Wooden treasure','chest',CHESTS['wooden_closed']),
           ('Brass treasure','chest',CHESTS['brass_closed']),
           ('Relic treasure','chest',CHESTS['relic_closed']),
           ('Cave threshold','mouth_cave',ENTRIES['cave']),
           ('Hollow threshold','mouth_hollow',ENTRIES['hollow']),
           ('Thicket threshold','mouth_thicket',ENTRIES['thicket'])]
    out=Image.new('RGB',(840,1420),'#101820');d=ImageDraw.Draw(out)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
    d.text((12,10),'Before / after native source pixels at 3x; terrain swatches only, NOT mGBA captures',font=font,fill='#fff0cb')
    headers=['Before / living ground','After / living ground','Before / blighted ground','After / blighted ground']
    for col,label in enumerate(headers):d.text((12+col*208,39),label,font=font,fill='#fff0cb')
    for row,(label,oldname,newrows) in enumerate(cases):
        y=62+row*224
        for col in range(4):
            base=tile('moss0' if col<2 else 'blight_floor')
            scene=Image.new('RGBA',(64,64))
            for ty in range(0,64,16):
                for tx in range(0,64,16):scene.alpha_composite(base,(tx,ty))
            if col%2:
                obj=rgba(newrows,pack.GROUPS['lift']);at=(16,30 if obj.height==32 else -2)
            else:
                obj=tile(oldname);at=(24,46)
            scene.alpha_composite(obj,at)
            large=scene.resize((192,192),Image.Resampling.NEAREST)
            out.paste(large,(12+col*208,y))
        d.text((12,y+198),label,font=font,fill='#fff0cb')
    out.save(path);return path
