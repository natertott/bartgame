"""Fifteen native32px Cream climbing studies, authored as paired halves.

These are exploratory source drawings, not selected production artwork.  A
whole32px ladder has one left rail and one right rail; splitting it at x16
never duplicates the rail pattern.  Top/mid/bottom share a deliberate8px tread
cadence and exact edge anchors.  All coordinates are final game pixels.
"""
from pathlib import Path
import json

from PIL import Image, ImageDraw, ImageFont, ImageOps

from cream_style_rind import PALETTES as _RIND_PALETTES


PALETTES = {name: list(bank) for name, bank in _RIND_PALETTES.items()}
NAMES = (
    'Ashwood Rails', 'Broad Oak', 'Rope Rails', 'Ivory Iron', 'Riveted Straps',
    'Cleft Ladder', 'Stone Staples', 'Carved Ascent', 'Alternating Pins',
    'Root Lashed', 'Hemp Loops', 'Bone Treads', 'Bolted Timber',
    'Miner Shelf', 'Pilgrim Rungs',
)
# One deliberately different construction per environment comparison.  These
# are recommendations for review, never a new persistent style selection.
RECOMMENDED = (0, 3, 6, 10, 12)
KINDS = ('top', 'mid', 'bottom')


def _palette(image, bank):
    rgb = [int(c[i:i+2],16) for c in PALETTES[bank] for i in (1,3,5)]
    image.putpalette(rgb + [0]*(768-len(rgb)))
    return image


def _canvas(stage):
    image = Image.new('P', (32,16), 3)
    return _palette(image, 'cream_cliff%d' % stage), ImageDraw.Draw(image)


def _tread(draw, y, left=8, right=23, thick=False, lit=7):
    """One horizontal solid tread, with its shadow down/right only."""
    draw.rectangle((left,y,right,y+2+(1 if thick else 0)),fill=2)
    draw.line((left,y,right-1,y),fill=lit)
    draw.line((left,y+1,right-1,y+1),fill=5 if thick else 6)
    if thick:
        draw.line((left,y+2,right-1,y+2),fill=4)


def _rail(draw, x, wide=3, color=5, bright=7):
    draw.rectangle((x,0,x+wide,15),fill=2)
    draw.rectangle((x,0,x+wide-1,15),fill=color)
    draw.line((x,0,x,15),fill=bright)
    if wide>2:
        draw.line((x+wide-2,0,x+wide-2,15),fill=4)


def _socket(draw, y, left=6, right=25, stone=False):
    """Mounting cuts connect the climbing fixture to the same cliff mass."""
    for x in (left,right):
        draw.rectangle((x-1,y,x+1,y+2),fill=2)
        draw.line((x-1,y,x+1,y),fill=5 if stone else 6)
        draw.point((x,y+1),fill=4)


def _decay(draw, stage, design):
    # Damage lives at mount/outer rock contacts and leaves every tread clear.
    # The same small pattern across states deliberately preserves clean lines
    # and reuses 8px subtiles; the RGB555 bank supplies broader discoloration.
    if stage:
        draw.line([(2,4),(3,6),(2,9),(3,11)],fill=2)
        draw.line((28,10,29,11),fill=9)
    if stage==2:
        draw.line([(2,5),(3,6),(2,9)],fill=12)
        draw.point((3,6),fill=13)
        draw.point((2,8),fill=14)


def ladder(design=0, stage=0, kind='mid'):
    """Return an opaqueP32×16 segment in cream_cliff{stage}.

    Slice x0..15 and16..31 once.  The two halves must never be substituted
    for one another or repeated independently.  Bottom-on-floor placement may
    instead use foot_floor(), in the existing floor bank.
    """
    design=int(design)
    if not 0<=design<len(NAMES):
        raise ValueError('ladder design must be0..14')
    if kind not in KINDS:
        raise ValueError('ladder kind must be top,mid,bottom')
    stage=max(0,min(2,int(stage)))
    image,d=_canvas(stage)
    # Quiet shallow rock shoulders, not a full-width black cutout.  Ends meet
    # adjacent cliff at ink3, making the shaft an intentional integrated cut.
    d.line((5,0,5,15),fill=2)
    d.line((26,0,26,15),fill=2)
    d.line((4,0,4,15),fill=4)
    d.line((27,0,27,15),fill=3)

    if design==0:                         # simple weathered staves
        _rail(d,7,3,5,6);_rail(d,22,3,5,6)
        for y in (3,11):_tread(d,y,8,23,True)
        d.line((8,0,8,2),fill=7)
    elif design==1:                       # broad, visibly structural oak
        _rail(d,6,4,5,7);_rail(d,22,4,4,6)
        for y in (3,11):
            _tread(d,y,9,22,True)
            d.point((7,y),fill=8);d.point((24,y),fill=6)
    elif design==2:                       # slim continuous rope rails
        for x in (8,23):
            d.line((x+1,0,x+1,15),fill=2)
            d.line((x,0,x,15),fill=6)
            for y in (1,9):d.line((x-1,y,x,y+1),fill=7)
        for y in (3,11):
            _tread(d,y,8,23,True,6)
            for x in (7,22):
                d.line((x,y,x+2,y),fill=7)
                d.line((x,y+2,x+2,y+2),fill=4)
    elif design==3:                       # clean narrow iron with lit edges
        _rail(d,7,3,4,7);_rail(d,22,3,4,6)
        for y in (3,11):_tread(d,y,8,23,False,8)
        _socket(d,0)
    elif design==4:                       # strap metal, readable broad ties
        _rail(d,7,3,5,6);_rail(d,22,3,4,6)
        for y in (3,11):
            _tread(d,y,8,23,False,7)
            for x in (7,22):
                d.rectangle((x-1,y-1,x+3,y+1),fill=2)
                d.line((x-1,y-1,x+2,y-1),fill=6)
                d.point((x+1,y),fill=8)
    elif design==5:                       # iron ladder fitted to a carved cleft
        d.rectangle((6,0,25,15),fill=2)
        d.line((6,0,6,15),fill=5);d.line((25,0,25,15),fill=3)
        _rail(d,8,2,4,6);_rail(d,22,2,4,6)
        for y in (3,11):_tread(d,y,9,22,False,7)
    elif design==6:                       # broad continuous carved staples
        for y in (2,10):
            d.rectangle((7,y,24,y+5),fill=2)
            d.rectangle((8,y,23,y+2),fill=5)
            d.line((8,y,22,y),fill=7)
            d.line((8,y+1,8,y+3),fill=6)
            d.line((10,y+3,22,y+3),fill=3)
        d.line((6,0,6,15),fill=4);d.line((25,0,25,15),fill=4)
    elif design==7:                       # a hewn groove with separate step lips
        d.rectangle((7,0,24,15),fill=2)
        d.line((6,0,6,15),fill=5);d.line((25,0,25,15),fill=4)
        for y in (3,11):
            d.rectangle((8,y,23,y+3),fill=4)
            d.line((8,y,22,y),fill=7)
            d.line((8,y+1,8,y+2),fill=6)
            d.line((8,y+4,23,y+4),fill=1)
    elif design==8:                       # two staggered columns of stone pins
        d.line((7,0,7,15),fill=4);d.line((24,0,24,15),fill=4)
        for x,y in ((9,2),(18,10)):
            d.rectangle((x-1,y,x+5,y+4),fill=2)
            d.rectangle((x,y,x+4,y+2),fill=5)
            d.line((x,y,x+3,y),fill=7)
            d.point((x,y+1),fill=6)
    elif design==9:                       # restrained root, regular treads
        for x in (7,23):
            d.line([(x,0),(x+1,4),(x,8),(x+1,12),(x,15)],fill=2,width=3)
            d.line([(x-1,0),(x,4),(x-1,8),(x,12),(x-1,15)],fill=5)
            d.line([(x-1,0),(x,3)],fill=7)
        for y in (3,11):
            _tread(d,y,8,23,True,6)
            d.line((6,y+1,9,y+1),fill=9)
            d.point((7,y),fill=11)
    elif design==10:                      # taut ropes with shallow hanging loops
        for x in (8,23):
            d.line((x,0,x,15),fill=6)
            d.line((x+1,0,x+1,15),fill=2)
        for y in (2,10):
            d.line([(8,y+1),(12,y+3),(19,y+3),(23,y+1)],fill=2,width=2)
            d.line([(8,y),(12,y+2),(19,y+2),(23,y)],fill=7)
            d.line((13,y+3,18,y+3),fill=5)
    elif design==11:                      # matte pale treads, dark supports
        _rail(d,7,2,4,5);_rail(d,23,2,4,5)
        for y in (3,11):
            d.rounded_rectangle((7,y,25,y+3),radius=1,fill=2)
            d.line((8,y,23,y),fill=8)
            d.line((8,y+1,24,y+1),fill=6)
            d.line((10,y+2,22,y+2),fill=5)
    elif design==12:                      # hybrid timber and honest iron cuffs
        _rail(d,7,3,5,6);_rail(d,22,3,4,6)
        for y in (3,11):
            _tread(d,y,8,23,True,7)
            d.rectangle((6,y-1,10,y+2),fill=2)
            d.line((6,y-1,9,y-1),fill=7)
            d.point((8,y),fill=8)
            d.rectangle((22,y-1,26,y+2),fill=2)
            d.line((22,y-1,25,y-1),fill=6)
            d.point((24,y),fill=7)
    elif design==13:                      # small mine treads between curdstone cheeks
        d.rectangle((6,0,8,15),fill=5);d.line((6,0,6,15),fill=6)
        d.rectangle((23,0,25,15),fill=4);d.line((23,0,23,15),fill=5)
        for y in (3,11):
            d.polygon([(8,y),(22,y),(24,y+2),(23,y+4),(8,y+4),(7,y+2)],fill=2)
            d.polygon([(8,y),(22,y),(23,y+1),(21,y+2),(8,y+2)],fill=5)
            d.line((8,y,21,y),fill=7)
    else:                                # the smallest, cleanest ritual fixture
        _rail(d,9,2,4,7);_rail(d,21,2,4,6)
        for y in (3,11):_tread(d,y,10,22,False,7)
        d.line((8,0,8,15),fill=2);d.line((24,0,24,15),fill=2)

    _decay(d,stage,design)
    if kind=='top':
        # Hooked shoulders meet a lit upper lip.  The center opening continues
        # directly from the walking plane; it is not a third/fourth rail.
        d.line((2,0,29,0),fill=6)
        d.line((3,1,7,1),fill=7);d.line((24,1,28,1),fill=5)
        for x in (7,23):
            d.rectangle((x-1,0,x+2,3),fill=2)
            d.line((x-1,0,x+1,0),fill=7)
            d.line((x-1,1,x-1,2),fill=6)
        d.line((10,0,21,0),fill=4)
    elif kind=='bottom':
        # Shaft meets a shallow toe instead of ending as two severed poles.
        d.rectangle((4,13,28,15),fill=3)
        d.line((6,13,25,13),fill=2)
        d.line((8,13,23,13),fill=5)
        d.line((9,14,22,14),fill=4)
        d.line((10,15,21,15),fill=3)
    return image


def foot_floor(design=0, stage=0):
    """Optional bottom in cream_floor{stage}, with a real floor-colored toe.

    Native colors are assigned by material role, not image resampling.  The
    two rock shoulders disappear into the floor; the last supports and tread
    retain a short cool contact shadow.  No new palette slot is required.
    """
    stage=max(0,min(2,int(stage)))
    source=ladder(design,stage,'bottom')
    lookup={1:1,2:3,3:4,4:4,5:3,6:5,7:6,8:8,9:9,10:10,11:11,12:12,13:13,14:14,15:15}
    image=Image.new('P',(32,16),4)
    image.putdata([lookup[p] for p in source.tobytes()])
    d=ImageDraw.Draw(image)
    # Floor is retained at both outside edges; these are not cliff slots.
    d.rectangle((0,0,5,15),fill=4);d.rectangle((27,0,31,15),fill=4)
    d.line((4,11,6,11),fill=3);d.line((25,13,27,13),fill=3)
    return _palette(image,'cream_floor%d'%stage)


def assembled(design=0, stage=0, floor_foot=True):
    """Return an RGB source assembly32×96; this is never a game screenshot."""
    result=Image.new('RGB',(32,96))
    for row,kind in enumerate(('top','mid','mid','mid','mid','bottom')):
        segment=foot_floor(design,stage) if floor_foot and kind=='bottom' else ladder(design,stage,kind)
        result.paste(segment.convert('RGB'),(0,row*16))
    return result


def validate():
    """Native opacity, pairing and hardware-pattern budget, not a quality score."""
    from PIL import Image as I
    assert PALETTES==_RIND_PALETTES
    assert all(len(bank)==16 and all(int(c[n:n+2],16)%8==0
               for c in bank for n in (1,3,5)) for bank in PALETTES.values())

    def pattern(image):
        return min(image.tobytes(),
                   image.transpose(I.Transpose.FLIP_LEFT_RIGHT).tobytes(),
                   image.transpose(I.Transpose.FLIP_TOP_BOTTOM).tobytes(),
                   image.transpose(I.Transpose.ROTATE_180).tobytes())

    def collect(image, store):
        assert image.mode=='P' and image.size==(32,16)
        assert all(1<=value<=15 for value in image.tobytes())
        # Distinct native halves are the essential correction to four rails.
        assert image.crop((0,0,16,16)).tobytes()!=image.crop((16,0,32,16)).tobytes()
        for y in (0,8):
            for x in (0,8,16,24):store.add(pattern(image.crop((x,y,x+8,y+8))))

    designs=[]
    for design,name in enumerate(NAMES):
        cliff,foot=set(),set()
        for stage in range(3):
            for kind in KINDS:collect(ladder(design,stage,kind),cliff)
            collect(foot_floor(design,stage),foot)
        total=len(cliff|foot)
        assert total<=55,(design,total)
        designs.append(dict(design=design,display_number=design+1,name=name,
                            recommended=design in RECOMMENDED,
                            unique_patterns=len(cliff),with_floor_foot_patterns=total))
    return dict(method='Source-only native32x16 paintings; flip-aware8px pattern count across three stages. No ROM or gameplay qualification.',
                palette_exact=True,opaque=True,distinct_paired_halves=True,
                canvas=[32,16],stages=3,designs=designs)


def write_review(folder):
    """Fifteen source options, native and nearest inspection; no ROM edits."""
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    font=ImageFont.load_default()
    stages=('HEALTHY','SOUR','DEEP')
    for stage in range(3):
        sheet=Image.new('RGB',(720,520),'#17151f');d=ImageDraw.Draw(sheet)
        d.text((5,4),'15 NATIVE LADDER STUDIES / SOURCE ASSEMBLIES, NOT GAMEPLAY / '+stages[stage],font=font,fill='#e0d8c0')
        for design,name in enumerate(NAMES):
            col,row=design%5,design//5;x=col*144;y=22+row*166
            d.text((x+4,y),f'{design+1:02d} '+name,font=font,fill='#e0d8c0')
            # Native broad wall context and a floor strip reveal real contacts.
            mounted=Image.new('P',(80,128),3)
            _palette(mounted,'cream_cliff%d'%stage)
            m=ImageDraw.Draw(mounted)
            m.polygon([(0,38),(15,33),(26,36),(37,31),(56,34),(79,30),(79,39),(65,43),(45,42),(27,46),(10,44),(0,47)],fill=4)
            m.polygon([(0,76),(16,79),(32,73),(49,76),(67,72),(79,75),(79,82),(61,87),(39,83),(20,89),(0,86)],fill=4)
            m.line([(0,58),(13,56),(23,58),(43,54),(63,57),(79,55)],fill=2)
            context=mounted.convert('RGB')
            floor=Image.new('P',(80,16),4);_palette(floor,'cream_floor%d'%stage)
            context.paste(floor.convert('RGB'),(0,0))
            context.paste(floor.convert('RGB'),(0,96));context.paste(floor.convert('RGB'),(0,112))
            context.paste(assembled(design,stage),(24,16))
            sheet.paste(context,(x+28,y+15))
            d.text((x+4,y+146),'32x96 / '+('suggested' if design in RECOMMENDED else 'option'),font=font,fill='#9ca08c')
        sheet.save(folder/f'ladders-{stage}-native.png')
        sheet.resize((1440,1040),Image.Resampling.NEAREST).save(folder/f'ladders-{stage}-2x.png')
        if stage==0:
            ImageOps.grayscale(sheet).save(folder/'ladders-grayscale-native.png')
    # Every segment at native size makes the32px pairing and joins inspectable.
    segments=Image.new('RGB',(768,196),'#17151f');d=ImageDraw.Draw(segments)
    d.text((4,3),'NATIVE SEGMENTS / TOP MID BOTTOM FLOOR FOOT / SOURCE ONLY',fill='#e0d8c0',font=font)
    for design,name in enumerate(NAMES):
        x=(design%5)*152;y=20+(design//5)*58
        d.text((x+3,y),f'{design+1:02d} '+name,fill='#e0d8c0',font=font)
        for n,kind in enumerate(KINDS):segments.paste(ladder(design,0,kind).convert('RGB'),(x+n*36,y+14))
        segments.paste(foot_floor(design,0).convert('RGB'),(x+108,y+14))
    segments.save(folder/'native-segments.png')
    segments.resize((1536,392),Image.Resampling.NEAREST).save(folder/'segments-2x.png')
    (folder/'validation.json').write_text(json.dumps(validate(),indent=2)+'\n')


if __name__=='__main__':
    import sys
    write_review(sys.argv[1] if len(sys.argv)>1 else '/workspace/setup/cream-polish/ladders')
