"""Selected Weathered Curdstone with continuous beds and carved ascents.

Native profile12 art only.  Earlier study painters are never mutated.  The
foreground masters retain their finished masks; the backing now joins across
its entire horizontal boundary instead of leaving an eight-pixel dark seam
between repeats.  Wall returns use short planes, not full-height bright bars.
"""
from PIL import Image, ImageDraw

from cream_style_rind import PALETTES as _RIND
from cream_style_depth import floor, cave
import cream_polish_walls_b as _WEATHERED
import cream_polish_ladders as _CLIMBS
import cream_polish_water as _WATER

PALETTES = {name:list(bank) for name,bank in _RIND.items()}
PALETTES['cream_water'] = list(_WATER.PALETTE)
SPECS = tuple(dict(spec) for spec in _WEATHERED.SPECS)
STYLE_NAME = 'Weathered Curdstone / continuous strata'
LADDER_DESIGNS = (6, 7, 8)
LADDER_NAMES = ('Stone Steps', 'Carved Ascent', 'Alternating Pins')
PHASES = _WATER.PHASES
EDGE_KINDS = ('solid_left','solid_right','toe',
              'outer_left','outer_right','inner_left','inner_right',
              'cap_left','cap_mid','cap_right','narrow')


def _canvas(stage=0,size=(16,16),fill=3,floor_bank=False):
    stage=max(0,min(2,int(stage)))
    image=Image.new('P',size,fill)
    bank=PALETTES[('cream_floor' if floor_bank else 'cream_cliff')+str(stage)]
    colors=[int(c[n:n+2],16) for c in bank for n in (1,3,5)]
    image.putpalette(colors+[0]*(768-len(colors)))
    return image,ImageDraw.Draw(image)


def panel(style=3,stage=0,kind='shelf',variant=0):
    """The selected complete Weathered master, unchanged from study4."""
    return _WEATHERED.panel(3,stage,kind,variant)


def panel_mask(style=3,stage=0,kind='shelf',variant=0):
    return _WEATHERED.panel_mask(3,stage,kind,variant)


def backing(style=3,stage=0):
    """A native128×48 bed with exact matching left/right material endpoints.

    No empty vertical matte surrounds the picture.  The broad beds continue
    through a repeat, while unequal inclinations and recesses break up its
    interior.  The quiet top/bottom join remains intentionally subordinate.
    """
    image,draw=_canvas(stage,(128,48))
    draw.polygon([(0,7),(18,7),(27,5),(48,5),(57,8),(75,8),
                  (86,6),(111,6),(121,7),(127,7),(127,17),
                  (111,17),(102,19),(81,19),(73,16),(53,16),
                  (45,14),(28,14),(18,17),(0,17)],fill=4)
    draw.polygon([(0,31),(15,31),(27,28),(50,28),(60,32),(84,32),
                  (93,29),(115,29),(127,31),(127,40),(111,40),
                  (101,42),(79,42),(68,38),(47,38),(39,40),
                  (18,40),(9,39),(0,40)],fill=4)
    # Connected horizontal seams cross the repeat without a dark vertical
    # interruption.  They are narrow recesses, not another bright ledge.
    draw.line([(0,21),(14,21),(23,23),(43,23),(52,21),(63,21)],fill=2)
    draw.line([(95,21),(115,21),(127,21)],fill=2)
    draw.line([(29,41),(39,42),(49,41),(59,42)],fill=2)
    # One deposit belongs to a real recessed seam, rather than each cell.
    draw.line([(91,22),(97,21),(103,23),(101,25),(96,25)],fill=9)
    draw.line((94,22,99,22),fill=10)
    if stage:
        draw.line([(68,29),(66,32),(68,34),(65,37)],fill=2)
    if stage>=2:
        draw.line([(68,29),(66,32),(68,34),(65,37)],fill=12)
        draw.line([(67,31),(66,32),(68,34)],fill=13)
        draw.point((66,32),fill=14)
    # Deliberately equal full columns; do not repair this with clipping or
    # filtering after generation.  Native wrapping is an authored contract.
    assert [image.getpixel((0,y)) for y in range(48)] == [image.getpixel((127,y)) for y in range(48)]
    return image


def filler(style=3,stage=0,kind='mid',variant=0):
    """Opaque small remnants with short material returns, never long poles."""
    if kind=='mid':return _canvas(stage)[0]
    if kind=='top':return edge(stage,'cap_mid',variant)
    if kind in ('base','bottom'):return edge(stage,'toe',variant)
    if kind=='left':return edge(stage,'solid_left',variant)
    if kind=='right':return edge(stage,'solid_right',variant)
    raise ValueError('unknown dynamic cliff filler '+kind)


def edge(stage=0,kind='solid_left',variant=0):
    """Native stone caps, returns and corners in cream_cliff{stage}.

    All cells remain solid artwork.  A turned plane does not advertise a
    passable half-cell; the room generator owns the actual height/collision.
    Top/side joins share restrained inks3/4 and short light-facing shoulders.
    """
    if kind not in EDGE_KINDS:raise ValueError('unknown dynamic stone edge '+kind)
    image,draw=_canvas(stage)
    v=int(variant)&1
    if kind=='toe':
        draw.polygon([(0,1),(5,1),(8,3),(15,3),(15,8),(11,9),
                      (7,7),(3,8),(0,7)],fill=4)
        draw.line([(0,11),(4,11),(7,12),(11,11),(15,11)],fill=2)
        draw.line((0,15,15,15),fill=1)
        if v:draw.line((6,2,10,2),fill=5)
    elif kind in ('cap_left','cap_mid','cap_right'):
        profile=[(0,2),(5,2),(7,1),(11,1),(13,2),(15,2)]
        draw.polygon(profile+[(15,5),(11,6),(5,5),(0,5)],fill=6)
        draw.line(profile,fill=7)
        draw.line([(0,6),(5,6),(8,7),(12,6),(15,6)],fill=2)
        draw.polygon([(0,10),(7,9),(11,11),(15,10),(15,13),(0,13)],fill=4)
        if kind=='cap_left':
            draw.polygon([(0,0),(3,0),(3,3),(1,6),(0,6)],fill=3)
            draw.line([(3,1),(2,3),(2,4)],fill=5)
        elif kind=='cap_right':
            draw.polygon([(13,0),(15,0),(15,8),(13,6),(12,3)],fill=3)
            draw.line([(12,2),(13,4),(13,6)],fill=2)
    elif kind=='narrow':
        draw.polygon([(0,5),(4,3),(9,3),(15,5),(15,8),(10,9),(4,8),(0,9)],fill=4)
        draw.line([(1,5),(5,4),(10,4),(14,5)],fill=5)
        draw.line([(0,11),(5,10),(10,12),(15,11)],fill=2)
    elif kind.startswith('outer_'):
        left=kind.endswith('left')
        if left:
            draw.polygon([(4,0),(15,0),(15,4),(8,4),(5,6),(4,10),(0,10),(1,5)],fill=4)
            draw.line([(4,1),(8,1),(15,1)],fill=6)
            draw.line([(3,4),(2,6),(2,8)],fill=5)
            draw.line([(6,5),(8,6),(15,6)],fill=2)
        else:
            draw.polygon([(0,0),(10,0),(14,4),(15,9),(11,10),(10,6),(6,4),(0,4)],fill=4)
            draw.line((0,1,9,1),fill=6)
            draw.line([(10,5),(12,7),(12,9)],fill=2)
            draw.line([(0,6),(5,6),(8,7)],fill=2)
        draw.polygon([(0,12),(5,11),(9,13),(15,12),(15,15),(0,15)],fill=4)
    elif kind.startswith('inner_'):
        left=kind.endswith('left')
        draw.polygon([(0,2),(5,2),(8,4),(15,3),(15,8),(10,9),(4,7),(0,8)],fill=4)
        draw.line([(0,10),(5,10),(9,12),(15,11)],fill=2)
        x=1 if left else 14
        draw.line((x,11,x,14),fill=2)
        if left:draw.line((3,11,6,11),fill=5)
    else:
        # The near and far returns keep broad horizontal beds; only two
        # short edge contacts turn away.  No16px line becomes a room-high bar.
        left=kind=='solid_left'
        draw.polygon([(0,3),(5,3),(8,5),(15,4),(15,9),(10,10),(5,8),(0,9)],fill=4)
        draw.polygon([(0,13),(7,12),(11,14),(15,13),(15,15),(0,15)],fill=4)
        if left:
            draw.line((0,0,0,3),fill=2);draw.line((1,12,1,15),fill=2)
            draw.line([(2,2),(5,2),(7,3)],fill=5)
            draw.line((2,4,2,6),fill=4)
        else:
            draw.line((15,4,15,7),fill=2);draw.line((14,12,14,15),fill=2)
            draw.line([(8,4),(12,4),(13,5)],fill=3)
            draw.line((1,3,4,3),fill=5)
    return image


def ladder(design=0,stage=0,kind='mid'):
    return _CLIMBS.ladder(LADDER_DESIGNS[int(design)%3],stage,kind)


def foot_floor(design=0,stage=0):
    return _CLIMBS.foot_floor(LADDER_DESIGNS[int(design)%3],stage)


def ladder_mask(design=0,stage=0,kind='mid'):
    """Optional actual-carving alpha, avoiding an opaque32px shaft matte.

    Internal dark stone remains painted.  Only surroundings outside the cut
    treads, groove or pegs become transparent, so real backing beds can pass
    behind the climb while its existing CLIMB collision remains authoritative.
    The floor-foot can use the same mask on its separate floor-bank picture.
    """
    if kind not in ('top','mid','bottom'):
        raise ValueError('unknown carved climb segment '+kind)
    design=int(design)%3
    image=Image.new('L',(32,16),0);draw=ImageDraw.Draw(image)
    if design==0:
        for y in (2,10):draw.rectangle((7,y,24,min(15,y+5)),fill=255)
    elif design==1:
        draw.rectangle((6,0,25,15),fill=255)
    else:
        draw.rectangle((8,2,14,6),fill=255)
        draw.rectangle((17,10,23,14),fill=255)
    if kind=='top':
        draw.rectangle((2,0,29,1),fill=255)
        draw.rectangle((6,0,9,3),fill=255)
        draw.rectangle((22,0,25,3),fill=255)
    elif kind=='bottom':
        draw.rectangle((4,13,28,15),fill=255)
    return image


def masked_ladder(design=0,stage=0,kind='mid',floor_foot=False):
    """Native alpha version for the existing BG-ground blend cache."""
    image=(foot_floor(design,stage) if floor_foot and kind=='bottom' else
           ladder(design,stage,kind)).copy()
    mask=ladder_mask(design,stage,kind)
    image.putdata([ink if keep else 0 for ink,keep in zip(image.tobytes(),mask.tobytes())])
    return image


def fall(style=1,stage=0,width=1,kind='mid',phase=0):
    """The selected Whitewater Ribbons family, already four native phases."""
    return _WATER.fall(1,stage,width,kind,phase)


def pool(style=1,stage=0,phase=0):
    return _WATER.pool(1,stage,phase)
