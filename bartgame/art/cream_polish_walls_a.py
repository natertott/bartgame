"""Three original native Cream rock refinements: folds, faults, and karst.

All coordinates are final game pixels.  The complete silhouettes stop inside
their canvases, with an explicit mask for compositing onto the real backing.
This prevents the former straight-cropped shelf or terminating bright crack.
Styles0--2 preserve the normalized Rind rock palettes exactly.
"""
from functools import lru_cache
from PIL import Image, ImageDraw
from cream_style_rind import PALETTES as _RIND

PALETTES = {name: list(bank) for name, bank in _RIND.items()}
STYLE_NAMES = ('Pearlstone Folds', 'Faulted Chalk', 'Ribbed Karst')
SPECS = (
    dict(name='shelf_fold', kind='shelf', variant=0, w=4, h=2),
    dict(name='shelf_cleft', kind='shelf', variant=1, w=4, h=2),
    dict(name='fracture_slant', kind='fracture', variant=0, w=6, h=2),
    dict(name='fracture_rib', kind='fracture', variant=1, w=6, h=2),
    dict(name='blind_bay', kind='arch', variant=0, w=4, h=3),
    dict(name='compact_knuckle', kind='compact', variant=0, w=2, h=2),
    dict(name='compact_split', kind='compact', variant=1, w=2, h=2),
)
_SIZES = {'shelf': (64,32), 'fracture': (96,32), 'arch': (64,48), 'compact': (32,32)}


def _canvas(size, stage):
    image = Image.new('P', size, 3)
    rgb = [int(c[n:n+2],16) for c in PALETTES['cream_cliff%d'%stage] for n in (1,3,5)]
    image.putpalette(rgb + [0]*(768-len(rgb)))
    mask = Image.new('L', size, 0)
    return image, ImageDraw.Draw(image), mask, ImageDraw.Draw(mask)


def _mass(d, md, outline, top, lit, face=4, top_ink=6):
    """One complete material mass: no concentric contour highlighting."""
    d.polygon(outline,fill=face);md.polygon(outline,fill=255)
    d.polygon(top,fill=top_ink)
    d.line(lit,fill=7)


def _seam(d, points, stage, branch=(), core=()):
    d.line(points, fill=2 if not stage else 1, width=1 if not stage else 2)
    if branch:d.line(branch,fill=2)
    if stage == 1:
        d.line(points[1:-1],fill=12)
    elif stage == 2:
        d.line(points,fill=12,width=2)
        d.line(points[1:-1],fill=13)
        if branch:d.line(branch[1:-1],fill=13)
        if core:d.line(core,fill=14)


def _mould(d, points, line):
    d.polygon(points,fill=9)
    d.line(line,fill=10)


def _folds(d,md,w,variant,stage):
    """Unequal continuous folded mineral beds, with broad near-side faces."""
    end=w-3
    if not variant:
        _mass(d,md,[(3,9),(9,5),(22,4),(34,6),(44,5),(end-7,8),(end,13),
                    (end-3,21),(end-14,26),(w//2,28),(16,25),(5,26),(2,19)],
                   [(3,9),(10,5),(22,4),(34,6),(44,5),(end-8,8),(end-1,12),
                    (end-9,16),(w//2+3,14),(19,16),(5,13)],
                   [(5,8),(11,5),(21,5),(28,6)])
        d.polygon([(7,14),(18,17),(31,15),(43,17),(end-8,16),(end-2,13),
                   (end-4,18),(end-13,21),(39,20),(29,22),(14,20),(5,18)],fill=2)
        d.line([(8,17),(18,19),(29,18),(38,20)],fill=1)
        d.polygon([(7,22),(16,22),(27,25),(34,24),(42,25),(39,27),(23,27),(12,24)],fill=5)
        d.line([(11,9),(22,8),(30,10),(40,9),(48,11)],fill=5)
        d.line([(13,7),(20,7),(24,8)],fill=8)
        _mould(d,[(17,20),(25,21),(32,20),(38,23),(32,25),(22,24)],
               [(19,21),(24,22),(30,22)])
        x=w//2+7
        _seam(d,[(x,7),(x-2,10),(x,13),(x-3,16),(x-2,20),(x-5,24)],stage,
              [(x-3,16),(x+3,18),(x+9,16),(x+15,17)],[(x-2,20),(x-4,23)])
    else:
        _mass(d,md,[(2,14),(7,8),(20,7),(31,10),(39,6),(end-12,4),
                    (end-3,8),(end,16),(end-5,24),(end-20,27),(34,25),(20,28),(6,25)],
                   [(3,13),(8,8),(20,7),(31,10),(40,7),(end-12,4),(end-4,8),
                    (end-2,12),(end-11,16),(42,15),(30,17),(17,14)],
                   [(5,12),(9,9),(19,8),(26,10)])
        d.polygon([(5,16),(18,18),(31,21),(43,17),(end-11,18),(end-2,14),
                   (end-4,20),(end-13,23),(45,22),(32,25),(18,22),(6,20)],fill=2)
        d.line([(8,18),(20,20),(31,23),(41,20)],fill=1)
        d.polygon([(8,23),(18,24),(23,26),(32,24),(40,24),(35,27),(21,28),(9,25)],fill=5)
        d.line([(42,9),(48,7),(end-12,6)],fill=8)
        d.line([(39,11),(46,9),(end-11,10),(end-7,12)],fill=5)
        _mould(d,[(end-20,20),(end-13,20),(end-7,23),(end-14,25),(end-22,23)],
               [(end-20,21),(end-15,21),(end-11,23)])
        x=w//2-2
        _seam(d,[(x,11),(x-3,14),(x-2,18),(x-5,21),(x-4,25)],stage,
              [(x-2,18),(x+4,17),(x+9,19),(x+13,18)],[(x-3,14),(x-2,17)])


def _faults(d,md,w,variant,stage):
    """A broad bevelled chalk plate whose stress line is not a tile joint."""
    e=w-3
    if not variant:
        outline=[(2,12),(9,5),(25,4),(39,7),(52,4),(e-8,6),(e,14),(e-3,24),
                 (e-19,28),(w//2,25),(20,28),(5,23)]
        top=[(2,12),(9,5),(25,4),(39,7),(52,4),(e-8,6),(e-1,13),
             (e-13,15),(w//2+5,13),(26,16),(9,14)]
        lit=[(4,11),(10,6),(24,5),(33,7)]
    else:
        outline=[(2,9),(15,4),(29,6),(39,4),(53,7),(e-6,9),(e,17),(e-8,25),
                 (e-22,27),(w//2-3,24),(18,28),(6,23)]
        top=[(2,9),(15,4),(29,6),(39,4),(53,7),(e-6,9),(e-2,15),
             (e-13,17),(42,13),(28,15),(10,12)]
        lit=[(3,9),(15,5),(23,6),(29,7)]
    _mass(d,md,outline,top,lit)
    # A single break across the continuous cap, then a recessed far-side plane.
    d.polygon([(7,16),(21,18),(31,16),(44,18),(e-12,17),(e-2,14),
               (e-5,20),(e-18,24),(w//2+2,21),(25,24),(10,21)],fill=3)
    d.line([(9,17),(22,20),(31,18),(43,20),(e-13,19)],fill=2)
    d.polygon([(12,22),(24,24),(31,22),(40,24),(36,26),(23,27),(12,24)],fill=5)
    d.line([(12,9),(22,8),(31,11),(40,9)],fill=5)
    d.line([(11,6),(21,6),(26,7)],fill=8)
    _mould(d,[(e-25,21),(e-16,22),(e-11,20),(e-7,23),(e-14,25),(e-24,24)],
           [(e-22,22),(e-16,23),(e-12,22)])
    x=w//2+(7 if not variant else -6)
    _seam(d,[(x,7),(x-3,11),(x,15),(x-4,19),(x-3,23),(x-6,27)],stage,
          [(x,15),(x+6,14),(x+12,16),(min(e-3,x+19),14)],[(x-3,20),(x-3,22)])


def _karst(d,md,w,variant,stage):
    """Long joined limestone ribs; the rock reads as a face, not loose balls."""
    e=w-3
    _mass(d,md,[(2,11),(8,6),(21,4),(35,7),(w//2+7,5),(e-7,8),(e,14),
                (e-3,25),(e-16,28),(w//2,26),(18,28),(5,24)],
               [(3,10),(9,6),(21,4),(34,7),(w//2+7,5),(e-8,8),(e-2,12),
                (e-14,15),(w//2+5,12),(32,15),(17,13),(6,14)],
               [(5,9),(10,6),(20,5),(28,7)],top_ink=5)
    # Broad weathered bedding layers, deliberately unequal lengths/spacing.
    if not variant:
        ribs=[([(5,12),(18,10),(29,12),(43,10),(e-8,13)],6),
              ([(6,18),(18,17),(30,20),(44,17),(e-6,19)],5),
              ([(11,24),(24,23),(37,25),(e-13,22)],5)]
    else:
        ribs=[([(6,11),(19,9),(31,11),(45,9),(e-7,12)],6),
              ([(5,17),(17,18),(31,16),(46,19),(e-5,17)],5),
              ([(10,24),(23,22),(34,24),(e-11,23)],5)]
    for points,ink in ribs:
        d.line([(x,y+2) for x,y in points],fill=2,width=2)
        d.line(points,fill=ink,width=2)
        d.line(points[:3],fill=7 if ink==6 else 6)
    d.line([(11,7),(20,6),(26,8)],fill=8)
    _mould(d,[(14,19),(22,20),(26,18),(32,20),(28,23),(19,23)],
           [(16,20),(22,21),(26,20)])
    x=w//2+(9 if not variant else -5)
    _seam(d,[(x,7),(x-1,11),(x+2,14),(x-2,18),(x,21),(x-3,26)],stage,
          [(x-2,18),(x+5,18),(x+10,20),(min(e-4,x+16),18)],[(x+1,13),(x+2,14)])


def _arch(d,md,style,variant,stage):
    """A complete closed carved relief, safely inset on all four sides."""
    outline=[(3,42),(4,26),(8,17),(16,9),(28,4),(39,7),(49,14),(56,24),
             (60,40),(54,44),(39,45),(24,43),(10,45)]
    if style==1:
        outline=[(3,42),(4,25),(10,16),(19,9),(26,5),(38,5),(47,11),
                 (54,21),(59,39),(55,44),(40,45),(24,43),(10,45)]
    md.polygon(outline,fill=255);d.polygon(outline,fill=4)
    # Light-left/shadow-right, with no concentric bevel stack or black doorway.
    d.polygon([(5,38),(6,25),(11,17),(18,11),(28,6),(34,7),(28,10),(21,14),
               (15,21),(12,31),(12,40)],fill=6)
    d.line([(6,26),(10,18),(17,11),(28,5),(33,7)],fill=7)
    d.line([(10,18),(17,12),(25,8)],fill=8)
    d.polygon([(35,10),(44,16),(50,25),(53,38),(58,39),(54,25),(48,17),(40,10)],fill=3)
    # The recess is filled by a coherent seated stone. It is never ink1 void.
    d.polygon([(15,37),(16,26),(21,19),(28,14),(34,15),(41,21),(46,29),(47,38),
               (36,40),(23,39)],fill=2)
    d.polygon([(17,29),(21,21),(28,16),(34,17),(40,23),(44,29),(35,30),(27,28)],fill=5)
    d.polygon([(18,31),(27,29),(35,32),(44,31),(46,37),(36,39),(24,37)],fill=4)
    d.line([(20,32),(27,31),(35,34),(43,33)],fill=3)
    # A low seated crossbar denies the actual cave's dark, open approach.
    d.polygon([(4,38),(15,35),(26,37),(38,35),(52,37),(59,41),(55,44),
               (39,43),(25,45),(10,42)],fill=5)
    d.line([(6,38),(15,36),(26,38),(37,36),(49,38)],fill=6)
    d.line([(10,42),(25,44),(39,42),(53,43)],fill=2)
    if style==0:
        d.polygon([(6,30),(10,29),(14,32),(12,35),(7,34)],fill=5)
        d.line([(7,30),(10,30),(12,32)],fill=6)
    elif style==1:
        # A broad, squared crown/keystone gives this variation a corbelled
        # construction instead of merely recolouring the pointed fold.
        d.polygon([(21,11),(26,6),(37,6),(43,10),(39,13),(32,11),(26,13)],fill=6)
        d.line([(23,10),(27,7),(36,7)],fill=7)
        d.polygon([(28,6),(34,6),(35,12),(30,15),(27,12)],fill=5)
        d.line((28,7,32,7),fill=8)
        d.line([(15,22),(17,17),(22,13)],fill=5)
        d.line([(13,17),(16,19)],fill=3);d.line([(22,10),(24,13)],fill=4)
        d.line([(43,15),(45,17)],fill=2)
    else:
        # Joined eroded ribs and a low brow turn the same footprint into a
        # natural weathered vault. These do not become little nested rings.
        d.line([(7,27),(13,18),(21,13),(29,10),(37,13),(43,19)],fill=5,width=2)
        d.line([(7,27),(13,19),(21,14),(28,12)],fill=6)
        d.line([(5,32),(11,29),(14,30)],fill=5)
        d.line([(5,26),(10,24),(13,25)],fill=5)
        d.line([(49,27),(53,28),(56,27)],fill=2)
    _mould(d,[(39,28),(44,27),(48,30),(47,34),(42,36),(38,33)],
           [(40,29),(44,28),(46,30)])
    _seam(d,[(35,9),(33,13),(35,17),(32,21),(33,25),(30,30),(31,34)],stage,
          [(33,25),(26,26),(23,24),(19,26)],[(34,17),(33,19)])


def _compact(d,md,style,variant,stage):
    """Small footprint gets one complete cropped-to-neither-edge rock."""
    if not variant:
        outline=[(3,12),(8,6),(18,4),(25,8),(29,15),(26,24),(18,28),(7,25),(2,19)]
        top=[(3,12),(8,6),(18,4),(25,8),(28,13),(20,16),(11,14),(5,16)]
        light=[(4,11),(9,6),(17,5),(22,7)]
    else:
        outline=[(2,10),(10,4),(20,6),(27,12),(29,22),(23,27),(13,28),(4,23)]
        top=[(2,10),(10,4),(20,6),(27,12),(20,16),(13,13),(5,15)]
        light=[(3,10),(10,5),(18,7)]
    _mass(d,md,outline,top,light,top_ink=5 if style==2 else 6)
    d.line([(5,17),(12,19),(19,17),(26,18)],fill=2,width=2)
    d.line([(7,23),(14,25),(21,23)],fill=5)
    if style==1:d.line([(7,9),(12,8),(18,11)],fill=5)
    elif style==2:d.line([(5,12),(12,10),(21,13)],fill=6)
    _mould(d,[(7,19),(12,20),(15,23),(10,24),(6,22)],[(8,20),(11,21)])
    _seam(d,[(20,9),(18,13),(20,16),(17,20),(18,24)],stage,
          [(20,16),(25,15)],[(18,13),(19,15)])


@lru_cache(maxsize=None)
def _painting(style,stage,kind,variant):
    if style not in (0,1,2):raise ValueError('walls_a owns styles0,1,2')
    if kind not in _SIZES:raise ValueError('unknown panel kind %r'%kind)
    stage=max(0,min(2,int(stage)));variant=int(variant)%2
    image,d,mask,md=_canvas(_SIZES[kind],stage)
    if kind=='arch':_arch(d,md,style,variant,stage)
    elif kind=='compact':_compact(d,md,style,variant,stage)
    else:(_folds,_faults,_karst)[style](d,md,image.width,variant,stage)
    # Structural highlights/cracks must never continue out of their own rock.
    # Two quiet rows/columns also make an opaque fallback safe to butt up.
    w,h=image.size
    for y in range(h):
        for x in range(w):
            if x<2 or y<2 or x>=w-2 or y>=h-2 or mask.getpixel((x,y))==0:
                image.putpixel((x,y),3);mask.putpixel((x,y),0)
    return image,mask


def panel(style=0,stage=0,kind='shelf',variant=0):
    return _painting(int(style),int(stage),kind,int(variant))[0].copy()


def panel_mask(style=0,stage=0,kind='shelf',variant=0):
    """L0 outside the complete rock;255 inside, including internal ink3."""
    return _painting(int(style),int(stage),kind,int(variant))[1].copy()


def backing(style=0,stage=0):
    style=int(style);stage=max(0,min(2,int(stage)))
    if style not in (0,1,2):raise ValueError('walls_a owns styles0,1,2')
    image,d,mask,md=_canvas((128,48),stage)
    if style==0:
        planes=[[(3,12),(19,7),(35,8),(49,12),(66,10),(82,15),(89,20),(72,22),(54,18),(36,20),(18,16)],
                [(13,32),(30,27),(46,31),(63,27),(81,32),(101,28),(123,34),(121,39),(104,42),(87,38),(65,41),(44,36),(26,39)]]
        seams=[[(10,21),(26,23),(43,21),(60,24)],[(75,24),(92,26),(109,23),(121,26)]]
    elif style==1:
        planes=[[(3,11),(17,5),(35,7),(50,12),(70,9),(87,15),(80,21),(60,19),(40,22),(18,17)],
                [(8,33),(24,26),(43,30),(58,25),(78,29),(96,26),(123,33),(117,40),(96,38),(78,42),(53,37),(33,40)]]
        seams=[[(9,20),(25,23),(42,20),(57,24)],[(64,24),(80,25),(98,22),(116,26)]]
    else:
        planes=[[(3,11),(20,7),(39,11),(57,8),(79,12),(103,8),(122,14),(117,20),(96,18),(78,22),(55,18),(36,21),(16,16)],
                [(4,33),(23,29),(45,33),(64,29),(83,32),(104,28),(123,34),(119,40),(100,38),(78,42),(58,37),(36,41),(17,37)]]
        seams=[[(7,22),(25,24),(44,22),(62,25),(83,23)],[(39,40),(57,42),(76,40),(95,42)]]
    for points in planes:d.polygon(points,fill=4)
    for points in seams:d.line(points,fill=2)
    _mould(d,[(22,23),(29,22),(34,25),(29,27),(23,26)],[(24,24),(28,24),(31,25)])
    _mould(d,[(94,25),(100,23),(107,26),(104,30),(97,31),(92,28)],[(96,25),(101,25),(104,27)])
    if stage:d.line([(108,25),(106,28),(108,31),(106,34)],fill=2)
    if stage==2:
        d.line([(108,25),(106,28),(108,31),(106,34)],fill=12)
        d.line([(107,27),(106,28),(108,31)],fill=13)
        d.point((106,28),fill=14)
    return image


def filler(style=0,stage=0,kind='mid',variant=0):
    if int(style) not in (0,1,2):raise ValueError('walls_a owns styles0,1,2')
    image,d,mask,md=_canvas((16,16),max(0,min(2,int(stage))))
    if kind=='top':d.rectangle((0,0,15,2),fill=4);d.line((0,3,15,3),fill=2)
    elif kind in ('base','bottom'):d.rectangle((0,13,15,15),fill=2);d.line((0,15,15,15),fill=1)
    elif kind=='left':d.rectangle((0,0,1,15),fill=2);d.line((2,0,2,15),fill=4)
    elif kind=='right':d.rectangle((14,0,15,15),fill=2)
    elif kind!='mid':raise ValueError('unknown filler kind %r'%kind)
    return image
