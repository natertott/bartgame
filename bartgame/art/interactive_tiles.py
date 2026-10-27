"""Readable, native-resolution interaction materials.

The final painter uses the already resident material palettes. It leaves
metatile identifiers, behavior, collision, substrate rules and animation
cadence alone. Full-cell switches and broad hazard/obstacle silhouettes
remain legible among either living foliage or luminous blight.
"""
from copy import deepcopy
from PIL import Image, ImageDraw


def canvas(fill=0):
    im=Image.new('P',(16,16),fill)
    return im,ImageDraw.Draw(im)


def rows(im):
    return [''.join('%x'%im.getpixel((x,y)) for x in range(16)) for y in range(16)]


def plate(down=False):
    im,d=canvas()
    # The physical plate reaches every cell edge; bevelled corners let
    # a few substrate pixels remain without shrinking its footprint.
    d.polygon([(1,0),(14,0),(15,1),(15,14),(14,15),(1,15),(0,14),(0,1)],fill=1)
    d.rectangle((1,1,14,13),fill=11)
    d.line([(1,13),(14,13),(14,2)],fill=10,width=1)
    d.line([(1,12),(1,1),(13,1)],fill=15,width=1)
    d.line([(2,13),(13,13)],fill=7,width=1)
    d.rectangle((3,3 if not down else 4,12,11),fill=7 if down else 14)
    d.rectangle((4,4 if not down else 5,11,10),fill=9 if down else 12)
    if down:
        # Lit check rather than a subtle one-pixel height-only difference.
        d.line([(5,8),(7,10),(10,6)],fill=15,width=1)
        d.point((10,5),fill=15)
    else:
        d.polygon([(7,5),(10,7),(8,9),(5,7)],fill=1)
        d.line([(6,6),(7,5),(9,6)],fill=7,width=1)
    for x,y in ((2,2),(13,2),(2,12),(13,12)):
        d.point((x,y),fill=7 if down else 14)
    return rows(im)


def pit(blighted=False,frame=0,inner=False):
    im,d=canvas(1)
    if inner:
        # The same unlit void, without an artificial floor-looking teal dash.
        return rows(im)
    if blighted:
        # A recessed rim and near wall surround a very dark, quiet cavity.
        d.rectangle((0,0,15,1),fill=6)
        d.polygon([(0,0),(3,0),(3,2),(1,3),(0,5)],fill=5)
        d.polygon([(12,0),(15,0),(15,5),(14,3),(12,2)],fill=5)
        d.line([(0,4),(3,1),(11,1),(15,4)],fill=7)
        d.line([(0,12),(2,12),(3,13),(11,13),(12,12),(15,12)],fill=4)
        d.rectangle((0,14,15,15),fill=5)
        d.polygon([(0,10),(2,12),(4,13),(3,15),(0,15)],fill=4)
        d.polygon([(15,10),(13,12),(11,13),(12,15),(15,15)],fill=4)
        d.line([(1,14),(5,14),(6,15)],fill=7)
        d.line([(10,15),(11,14),(14,14)],fill=6)
        # Sparse fractures identify corruption without filling the hole.
        d.line([(2,0),(3,2),(2,3)],fill=10 if frame==0 else 9)
        d.line([(13,15),(12,13),(13,12)],fill=9 if frame==0 else 10)
        d.point((3,2),fill=11 if frame==0 else 10)
        d.point((12,13),fill=10 if frame==0 else 11)
    else:
        d.rectangle((0,0,15,1),fill=10)
        d.polygon([(0,0),(3,0),(3,2),(1,3),(0,5)],fill=9)
        d.polygon([(12,0),(15,0),(15,5),(14,3),(12,2)],fill=9)
        d.line([(0,3),(3,0),(11,0),(15,3)],fill=12)
        d.line([(0,12),(3,12),(4,13),(11,13),(12,12),(15,12)],fill=6)
        d.rectangle((0,14,15,15),fill=9)
        d.polygon([(0,10),(2,12),(4,13),(3,15),(0,15)],fill=6)
        d.polygon([(15,10),(13,12),(11,13),(12,15),(15,15)],fill=6)
        d.line([(0,12),(3,13),(4,14),(10,14),(12,13),(15,12)],fill=13)
        d.line([(2,15),(6,15)],fill=10)
        d.line([(11,15),(14,15)],fill=10)
    return rows(im)


def cracked_wall():
    im,d=canvas(6)
    # Chipped, pale stone slabs, rather than a decoration-like thin rune.
    d.rectangle((0,0,15,2),fill=11)
    d.line([(0,0),(6,0)],fill=13)
    d.rectangle((0,4,15,7),fill=10)
    d.rectangle((0,9,15,12),fill=11)
    d.rectangle((0,14,15,15),fill=9)
    for y,x in ((3,3),(8,12),(13,4)):
        d.line([(0,y),(15,y)],fill=1)
        d.line([(x,y-2),(x,y)],fill=1)
    # A broad broken zigzag with unlit depth and freshly exposed edges.
    crack=[(9,0),(8,3),(10,5),(6,8),(8,10),(5,13),(6,15)]
    d.line([(x+1,y) for x,y in crack],fill=14,width=2)
    d.line(crack,fill=1,width=2)
    d.line([(9,0),(8,2)],fill=5)
    d.line([(6,8),(4,7),(3,5)],fill=1,width=1)
    d.line([(8,10),(11,11),(12,13)],fill=1,width=1)
    d.point((4,6),fill=14)
    d.rectangle((3,13,4,14),fill=13)
    d.point((11,14),fill=14)
    return rows(im)


def cobweb():
    im,d=canvas(1)
    # A root frame encloses a radial web; open dark pockets preserve silk
    # separation instead of becoming an opaque white rectangular grate.
    d.line([(0,0),(1,4),(0,9),(1,15)],fill=7,width=2)
    d.line([(15,0),(14,4),(15,10),(14,15)],fill=3,width=2)
    hub=(7,8)
    anchors=[(0,0),(7,0),(15,1),(15,8),(14,15),(7,15),(0,14),(0,7)]
    for p in anchors:d.line([hub,p],fill=13,width=1)
    for pts in (
        [(5,5),(7,4),(10,5),(11,8),(10,11),(7,12),(4,11),(3,8),(5,5)],
        [(2,2),(7,2),(13,3),(13,8),(12,14),(7,14),(1,12),(1,7),(2,2)],
    ):d.line(pts,fill=14,width=1)
    d.point((7,4),fill=15)
    d.point((3,8),fill=15)
    d.point((13,3),fill=15)
    # Tiny amber cocoon supplies the established candle/burnable colour cue.
    d.ellipse((6,7,8,10),fill=5)
    d.point((6,7),fill=15)
    return rows(im)


def locked_gate(open_=False):
    im,d=canvas(1)
    d.rectangle((0,0,2,15),fill=10)
    d.rectangle((13,0,15,15),fill=9)
    d.line([(0,0),(15,0)],fill=13)
    d.line([(2,1),(2,15)],fill=12)
    d.line([(13,1),(13,15)],fill=11)
    if open_:
        d.rectangle((3,1,12,12),fill=1)
        d.rectangle((3,13,12,15),fill=8)
        d.line([(3,13),(12,13)],fill=13)
        d.line([(4,15),(11,15)],fill=4)
    else:
        d.rectangle((3,1,12,15),fill=7)
        for x in (3,6,9,12):d.line([(x,1),(x,15)],fill=4)
        for y in (3,12):
            d.rectangle((3,y,12,y+1),fill=5)
            d.point((4,y),fill=15)
            d.point((11,y),fill=14)
        d.rectangle((6,6,10,10),fill=5)
        d.line([(6,6),(9,6)],fill=15)
        d.ellipse((7,7,9,8),fill=1)
        d.point((8,9),fill=1)
    return rows(im)


def censer(lit=False,frame=0):
    im,d=canvas()
    d.rectangle((3,13,12,14),fill=1)
    d.line([(4,13),(11,13)],fill=14)
    d.rectangle((5,8,10,12),fill=11)
    d.rectangle((6,8,8,12),fill=13)
    d.line([(6,10),(9,10)],fill=7)
    d.polygon([(1,5),(14,5),(13,8),(10,9),(5,9),(2,8)],fill=1)
    d.line([(2,5),(13,5)],fill=15)
    d.line([(2,6),(4,8),(11,8),(13,6)],fill=7)
    d.line([(4,7),(11,7)],fill=12)
    d.line([(5,4),(10,4)],fill=10)
    if lit:
        flame=[(6,4),(5,3),(6,1),(7,2),(8,0),(9,2),(10,3),(9,4)]
        if frame:flame=[(6,4),(5,2),(7,3),(8,0),(9,1),(9,2),(10,3),(9,4)]
        d.polygon(flame,fill=7)
        d.line([(7,4),(8,2),(9,4)],fill=15)
    else:
        d.line([(6,4),(7,3),(8,4),(9,3)],fill=14)
    return rows(im)


def pot():
    im,d=canvas()
    d.polygon([(4,3),(11,3),(12,6),(14,8),(13,12),(11,14),(4,14),(2,12),(1,8),(3,6)],fill=1)
    d.polygon([(4,4),(11,4),(11,6),(13,8),(12,12),(10,13),(5,13),(3,11),(2,8),(4,6)],fill=8)
    d.polygon([(4,5),(7,5),(6,12),(4,12),(3,9)],fill=9)
    d.line([(4,7),(11,7)],fill=7)
    d.line([(4,11),(11,11)],fill=7)
    d.line([(4,7),(6,7)],fill=15)
    d.line([(3,3),(12,3)],fill=1,width=3)
    d.line([(3,2),(11,2),(12,3)],fill=14)
    d.line([(4,3),(11,3)],fill=1)
    d.point((4,5),fill=15)
    return rows(im)


def threshold(style):
    """Wide repeating steps underneath the enlarged interior exit portal."""
    im,d=canvas(1)
    dark,mid,light,gleam={'cave':(7,9,11,13),
                          'hollow':(5,7,9,11),
                          'thicket':(8,10,12,13)}[style]
    d.rectangle((0,2,15,4),fill=dark)
    d.line([(0,2),(15,2)],fill=light)
    d.rectangle((0,6,15,9),fill=mid)
    d.line([(0,6),(15,6)],fill=gleam)
    d.rectangle((0,11,15,15),fill=mid)
    d.line([(0,11),(15,11)],fill=light)
    d.line([(0,14),(15,14)],fill=dark)
    d.line([(2,7),(4,7)],fill=light)
    d.line([(10,12),(13,12)],fill=light)
    return rows(im)


def spring(frame=0):
    im,d=canvas()
    # A broad open basin with unmistakable water and an ivory healing gleam.
    d.ellipse((0,1,15,15),fill=1)
    d.ellipse((1,1,14,13),fill=9)
    d.arc((1,1,14,13),180,300,fill=11,width=1)
    d.ellipse((3,3,12,11),fill=4)
    d.ellipse((4,4,11,10),fill=5)
    d.line([(4,4),(9,4)],fill=6)
    d.line([(5,10),(10,10)],fill=6)
    x,y=((7,6) if frame==0 else (9,6))
    d.line([(x-1,y),(x+1,y)],fill=13)
    d.line([(x,y-1),(x,y+1)],fill=13)
    d.point((5,8 if frame==0 else 7),fill=12)
    return rows(im)


def votive_statue():
    """A carved figure holding the shrine's warm sun at its chest."""
    im,d=canvas()
    # Crown/head, shoulders and robe form one connected, readable carving.
    d.ellipse((5,0,10,5),fill=1)
    d.ellipse((6,1,9,4),fill=14)
    d.line([(7,1),(8,1)],fill=15)
    d.polygon([(5,4),(10,4),(12,7),(12,11),(11,13),(4,13),(3,11),(3,7)],fill=1)
    d.polygon([(6,5),(9,5),(11,8),(10,12),(5,12),(4,8)],fill=9)
    d.line([(5,7),(4,9),(5,11)],fill=14)
    d.line([(10,6),(11,9),(10,11)],fill=8)
    d.line([(6,10),(6,12)],fill=13)
    d.line([(9,10),(9,12)],fill=8)
    # The forearms hold a luminous medallion, matching the floor marker.
    d.line([(4,8),(6,10)],fill=14)
    d.line([(11,8),(9,10)],fill=13)
    d.ellipse((6,6,9,9),fill=7)
    d.line([(7,6),(7,8)],fill=15)
    d.point((8,7),fill=15)
    # Broad stepped plinth: the colliding feet still occupy the lower half.
    d.rectangle((1,13,14,14),fill=1)
    d.line([(3,13),(12,13)],fill=14)
    d.line([(3,14),(12,14)],fill=11)
    d.line([(1,15),(14,15)],fill=1)
    return rows(im)


def shrine_plate():
    """A sun medallion distinguishes the heal trigger from ordinary flowers."""
    im,d=canvas()
    d.ellipse((0,0,15,15),fill=1)
    d.ellipse((1,0,14,13),fill=11)
    d.arc((1,0,14,13),175,315,fill=7,width=1)
    d.arc((1,1,14,14),5,145,fill=9,width=1)
    d.ellipse((3,2,12,11),fill=2)
    # Ivory/gold is resident in this palette; introducing cyan would require
    # another palette and disturb the established scene/material contracts.
    rays=[((7,3),(7,4)),((10,4),(9,5)),((11,7),(10,7)),
          ((10,10),(9,9)),((7,11),(7,10)),((4,10),(5,9)),
          ((3,7),(4,7)),((4,4),(5,5))]
    for a,b in rays:d.line([a,b],fill=7)
    d.polygon([(7,5),(9,7),(7,9),(5,7)],fill=7)
    d.line([(7,5),(7,7),(6,7)],fill=15)
    d.point((4,1),fill=15)
    return rows(im)


REPLACEMENTS={
    'myst_switch':[plate(False)],'myst_switch_down':[plate(True)],
    'pit':[pit()],'pit_inner':[pit(inner=True)],
    'forest_blight_pit':[pit(True,0),pit(True,1)],
    'crack':[cracked_wall()],'web':[cobweb()],
    'door_locked':[locked_gate()],'door_open':[locked_gate(True)],
    'torch':[censer()],'torch_lit':[censer(True,0),censer(True,1)],
    'myst_pot':[pot()],
    'cave_exit':[threshold('cave')],'hollow_exit':[threshold('hollow')],
    'thicket_exit':[threshold('thicket')],
    'myst_spring':[spring(0),spring(1)],
    'statue':[votive_statue()],
}
CHANGED_NAMES=set(REPLACEMENTS)
POT_ROWS=REPLACEMENTS['myst_pot'][0]
POT_PALETTE='glade_wood_stone'
ADDED_TILES=[{'name':'shrine_plate','pal':'glade_wood_stone','type':'FLOOR',
              'coll':0,'prop':True,'art':shrine_plate()}]
CHANGED_NAMES.update(m['name'] for m in ADDED_TILES)


def apply(metatiles,palettes):
    for m in metatiles:
        if m['name'] not in REPLACEMENTS:continue
        contract=deepcopy({k:v for k,v in m.items() if k not in ('art','frames')})
        old_count=len(m.get('frames') or [m['art']]);new=REPLACEMENTS[m['name']]
        assert len(new)==old_count,(m['name'],old_count,len(new))
        assert all(len(frame)==16 and all(len(row)==16 for row in frame) for frame in new)
        if len(new)>1:m['frames']=new;m.pop('art',None)
        else:m['art']=new[0];m.pop('frames',None)
        assert {k:v for k,v in m.items() if k not in ('art','frames')}==contract,m['name']
    # Append after all imported/painted tile ids, preserving saved and authored
    # contracts. This marker is used only by an unused healing shrine.
    existing={m['name'] for m in metatiles}
    assert not existing.intersection(m['name'] for m in ADDED_TILES)
    metatiles.extend(deepcopy(ADDED_TILES))


def preview(metatiles,path='/workspace/setup/interactive-tiles-source.png'):
    """Source art audit only; real gameplay evidence is captured in mGBA."""
    import palettes
    groups=dict(palettes.BG_PALETTES)
    selected=[m for n in list(REPLACEMENTS)+[m['name'] for m in ADDED_TILES]
              for m in metatiles if m['name']==n]
    out=Image.new('RGB',(864,42+((len(selected)+5)//6)*130),'#101820')
    d=ImageDraw.Draw(out)
    d.text((10,10),'Interactive materials / native source art (not an emulator capture)',fill='#e8e8d0')
    for i,m in enumerate(selected):
        frame=(m.get('frames') or [m['art']])[0];pal=groups[m['pal']]
        im=Image.new('RGBA',(16,16));pix=im.load()
        for y,row in enumerate(frame):
            for x,ch in enumerate(row):
                index=int(ch,16)
                if index:pix[x,y]=(*tuple(int(pal[index][j:j+2],16) for j in (1,3,5)),255)
        x=(i%6)*144+5;y=42+(i//6)*130
        big=im.resize((96,96),Image.Resampling.NEAREST);out.paste(big,(x,y),big)
        out.paste(im,(x+105,y+80),im)
        d.text((x,y+102),m['name'],fill='#e8e8d0')
    out.save(path)
    return path


def background_preview(metatiles,path='/workspace/setup/interactive-tiles-backgrounds.png'):
    """Source composites over actual terrain pixels, labelled as source art."""
    import palettes
    groups=dict(palettes.BG_PALETTES)
    table={m['name']:m for m in metatiles}
    def tile(m):
        frame=(m.get('frames') or [m['art']])[0];pal=groups[m['pal']]
        im=Image.new('RGBA',(16,16));pix=im.load()
        for y,row in enumerate(frame):
            for x,ch in enumerate(row):
                index=0 if ch=='.' else int(ch,16)
                if index:pix[x,y]=(*tuple(int(pal[index][j:j+2],16) for j in (1,3,5)),255)
        return im
    names=list(REPLACEMENTS)+[m['name'] for m in ADDED_TILES]
    out=Image.new('RGB',(936,50+((len(names)+2)//3)*146),'#101820');d=ImageDraw.Draw(out)
    d.text((10,10),'Actual tile pixels / healthy, blight, cave backgrounds / SOURCE COMPOSITES, not gameplay',fill='#e8e8d0')
    bases=[tile(table[n]) for n in ('moss0','blight_floor','cave_floor0')]
    for i,name in enumerate(names):
        x=(i%3)*312;y=50+(i//3)*146;d.text((x+6,y),name,fill='#e8e8d0')
        for k,base in enumerate(bases):
            panel=Image.new('RGBA',(32,32))
            for by in (0,16):
                for bx in (0,16):panel.alpha_composite(base,(bx,by))
            panel.alpha_composite(tile(table[name]),(8,8))
            out.paste(panel.resize((96,96),Image.Resampling.NEAREST),(x+k*104+4,y+19))
            d.text((x+k*104+4,y+118),('healthy','blight','cave')[k],fill='#e8e8d0')
    out.save(path)
    return path
