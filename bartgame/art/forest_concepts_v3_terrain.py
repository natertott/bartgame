"""Eight native leafy-canopy studies, layered disease over readable trees.

Existing non-canopy pixels and palette ramps delegate to forest v2 option1.
Only the new canopy3_blight BG bank is added. No HD image or filtered reduction
is involved: every contour is drawn on its final indexed pixel canvas.
"""
from functools import lru_cache
from PIL import Image, ImageDraw
import forest_concepts_v2_terrain as V2
import forest_concepts_terrain as H

RECIPES = {
    1: 'Veinbound Oak', 2: 'Patchblight Beech', 3: 'Spore Drift',
    4: 'Bracketwood', 5: 'Violet Leaf Mosaic', 6: 'Black Sap Bough',
    7: 'Silkbound Crown', 8: 'Canker Bloom',
}
BANKS = V2.BANKS
GREEN_INDICES = {'foliage': (2, 3, 4, 5, 6, 7),
                 'canopy3_blight': (9, 10, 11)}
PULSE_INDICES = {**V2.PULSE_INDICES, 'canopy3_blight': (5, 6, 7, 13, 14)}

# Dark leaf planes remain static. Green is an actual connected living lobe,
# not a bright outline or isolated colored points. Every value is RGB555.
_INFECTED = [
    '#000000', '#101418', '#181c20', '#302438', '#503848',
    '#401068', '#9028c8', '#e0a8f0', '#281c20', '#284830',
    '#486838', '#708c50', '#604830', '#c838d8', '#f0d0f8', '#b0a8b0',
]


def _variant(v):
    v = int(v)
    if v not in RECIPES:
        raise ValueError(v)
    return v


def extra_palettes(variant=1):
    _variant(variant)
    return {'canopy3_blight': list(map(H._q, _INFECTED))}


def palette(name, variant=1):
    _variant(variant)
    return extra_palettes(variant)[name] if name == 'canopy3_blight' else V2.palette(name, 1)


def supports(name):
    return V2.supports(name)


_TREE_NAMES = ['tree_top_nw', 'tree_top_ne', 'tree_mid_w', 'tree_mid_e',
               'tree_trunk_w', 'tree_trunk_e']


def owns(name):
    """Names redrawn here; delegation coverage must not imply new pixels."""
    return (name.startswith(('canopy', 'forest_canopy', 'blight_wall',
                             'forest_blight_tree', 'tree2_', 'birch_', 'fir_',
                             'gtree_', 'gtree2_', 'sicktree_')) or
            name in _TREE_NAMES or
            (name.startswith('btree_') and int(name[6:]) < 6) or
            name in ('dead_tree', 'forest_blight_dead_tree'))


def _new(w=16, h=16, fill=0):
    im = Image.new('P', (w, h), fill)
    return im, ImageDraw.Draw(im)


def _leaf(d, x, y, rx, ry, sick=False, living=False, kind=1):
    """Broad upper plane, dark scalloped underside; horizontal leaf clusters."""
    if sick and not living:
        deep, shade, top, light, peak = 2, 3, 4, 4, 15
    elif sick:
        deep, shade, top, light, peak = 9, 9, 10, 11, 11
    else:
        deep, shade, top, light, peak = 2, 3, 4, 5, 6
    pts = [(x-rx, y), (x-rx+1, y-2), (x-rx+3, y-ry+1),
           (x-3, y-ry), (x+2, y-ry+1), (x+rx-3, y-ry+1),
           (x+rx, y-2), (x+rx, y+1), (x+rx-2, y+ry-1),
           (x+4, y+ry), (x+1, y+ry-1), (x-3, y+ry+1),
           (x-6, y+ry-1), (x-rx+2, y+ry-1)]
    if kind in (2, 4, 7):
        pts[3] = (x-4, y-ry+1)
        pts[8] = (x+rx-3, y+ry)
    d.polygon(pts, fill=deep)
    d.polygon([(x-rx+1,y-1),(x-rx+3,y-ry+2),(x-3,y-ry+1),
               (x+2,y-ry+2),(x+rx-3,y-ry+2),(x+rx-1,y),
               (x+rx-3,y+ry-2),(x+3,y+ry-1),(x-2,y+ry-2),
               (x-5,y+ry-1),(x-rx+3,y+ry-2)], fill=shade)
    d.polygon([(x-rx+2,y-1),(x-rx+4,y-ry+2),(x-3,y-ry+1),
               (x+3,y-ry+2),(x+rx-4,y-ry+2),(x+rx-2,y-1),
               (x+rx-4,y+ry//2),(x+4,y+ry//2+1),
               (x-2,y+ry//2),(x-rx+3,y+ry//2+1)], fill=top)
    # Short groups of leaf tips, not long vertical hanging strands.
    for dx, dy in ((-rx//2,-ry//3),(rx//3,1)):
        d.polygon([(x+dx-3,y+dy),(x+dx-1,y+dy-2),(x+dx+2,y+dy-1),
                   (x+dx+4,y+dy),(x+dx+1,y+dy+1),(x+dx-2,y+dy+1)],fill=light)
    if not sick or living:
        d.line([(x-rx+5,y-ry+2),(x-rx+8,y-ry+1),(x-rx+10,y-ry+2)], fill=peak)


def _sprig(d,x,y,sick=False,living=False):
    """Two pointed leaf faces share one short lateral twig."""
    ink=11 if sick and living else 3 if sick else 5
    stem=9 if sick and living else 2 if sick else 3
    d.line([(x-4,y+1),(x+3,y)],fill=stem)
    d.polygon([(x-4,y),(x-2,y-2),(x+1,y-2),(x,y),(x-2,y+1)],fill=ink)
    d.polygon([(x,y),(x+2,y-3),(x+5,y-3),(x+3,y),(x+1,y+1)],fill=ink)


def _mother(d,x,y,v,sick=False):
    """One dominant domed crown with overlapping lower leafy shoulders."""
    broad=v in (2,4,7)
    _leaf(d,x,y-3,16 if broad else 15,10 if broad else 12,sick=sick,kind=v)
    _leaf(d,x-10,y+8,11,7,sick=sick,kind=v)
    _leaf(d,x+11,y+9,12,7,sick=sick,kind=v)
    for dx,dy in ((-8,-8),(-1,-11),(7,-6),(-5,1),(4,0),(-11,10),(10,11)):
        _sprig(d,x+dx,y+dy,sick)


def _branch(d, points, sick=False, width=4):
    d.line(points, fill=1, width=width+2)
    d.line(points, fill=8, width=width)
    d.line([(x,y-1) for x,y in points], fill=12 if sick else 10, width=max(1,width-2))


def _vein(d, points, width=1, core=True):
    d.line(points, fill=5, width=width+2)
    d.line(points, fill=6, width=width)
    if core:
        d.line(points[1:3] if len(points)>2 else points, fill=13, width=1)
        d.point(points[1 if len(points)>1 else 0], fill=7)


def _disease(d, v, phase=0):
    if v == 1:
        # Branching vascular infection spreads sideways with the leaf ribs.
        _vein(d, [(8,27),(14,23),(17,17),(23,13),(29,14)], 1)
        _vein(d, [(17,17),(12,14),(9,10)], 1, False)
        _vein(d, [(22,14),(20,8),(24,5)], 1, False)
    elif v == 2:
        # Broad necrotic wounds retain recognizable ragged leaf edges.
        d.polygon([(15,1),(24,2),(29,5),(27,9),(20,10),(15,7),(11,6)], fill=2)
        d.polygon([(17,3),(23,3),(27,5),(24,7),(19,7),(15,5)], fill=5)
        d.line([(15,5),(19,3),(24,4)], fill=13)
        d.polygon([(2,20),(8,17),(15,19),(18,24),(14,28),(6,29),(2,26)], fill=2)
        d.polygon([(5,21),(10,20),(14,22),(15,25),(10,27),(5,26)], fill=5)
        d.line([(5,21),(9,20),(12,21)], fill=6)
    elif v == 3:
        # Localized directional spore/dither island, never a screen-wide grid.
        d.polygon([(10,3),(24,3),(31,9),(27,15),(15,13),(8,9)], fill=5)
        for y in range(4,14):
            for x in range(9,30):
                if (x+2*y)%5==0 and abs(x-20)+2*abs(y-9)<18:
                    d.point((x,y), fill=6)
        for x,y in ((16,5),(24,8),(12,9),(27,12),(19,11)):
            d.line((x,y,x+1,y),fill=13)
        d.line((23,7,24,7),fill=7)
        d.polygon([(2,25),(7,22),(13,23),(15,27),(9,29),(2,28)],fill=5)
    elif v == 4:
        # Attached bracket fungus: broad layered caps on a horizontal limb.
        _branch(d,[(1,25),(9,22),(18,24),(30,20)],True,3)
        for x,y,w in ((4,18,7),(17,19,8),(25,9,6)):
            d.polygon([(x-w,y),(x-w+2,y-3),(x,y-4),(x+w-2,y-2),
                       (x+w,y),(x+w-2,y+2),(x-w+2,y+2)],fill=2)
            d.polygon([(x-w+1,y-1),(x-2,y-3),(x+3,y-2),(x+w-1,y)],fill=6)
            d.line([(x-w+2,y),(x,y+1),(x+w-2,y)],fill=15)
            d.line([(x-w+3,y-2),(x-1,y-3),(x+2,y-2)],fill=13)
    elif v == 5:
        # Bruised foliage itself is violet, still organized into leaf fans.
        for x,y,rx in ((22,6,9),(7,21,10),(27,28,8)):
            d.polygon([(x-rx,y),(x-rx+3,y-3),(x-2,y-4),(x+rx-2,y-2),
                       (x+rx,y),(x+rx-3,y+3),(x+2,y+2),(x-3,y+4)],fill=5)
            d.line([(x-rx+3,y-1),(x-2,y-2),(x+rx-3,y-1)],fill=6)
            d.line([(x-rx+5,y),(x-1,y+1),(x+3,y)],fill=13)
    elif v == 6:
        # Wet black sap pools along a broad lateral fork, with short drips.
        _branch(d,[(2,24),(10,21),(16,22),(24,18),(30,19)],True,5)
        d.line([(3,25),(11,23),(17,24),(24,20),(29,21)],fill=2,width=3)
        _vein(d,[(4,23),(10,21),(16,22)],1)
        _vein(d,[(18,21),(23,18),(29,19)],1)
        d.line([(12,24),(13,27),(12,29)],fill=2,width=3)
        d.line([(13,25),(13,27)],fill=6)
        d.line([(25,21),(26,24),(25,26)],fill=2,width=3)
        d.point((25,25),fill=13)
    elif v == 7:
        # Pale parasite silk spans a few lateral leaf gaps; not a fence.
        for pts in ([(7,13),(14,10),(21,13),(28,11)],
                    [(4,21),(11,18),(19,20),(26,17)],
                    [(14,10),(13,18),(17,25),(23,27)]):
            d.line(pts,fill=5,width=3);d.line(pts,fill=15)
        d.line([(8,14),(15,15),(22,13),(27,14)],fill=6)
        d.line([(12,18),(19,17),(25,19)],fill=13)
        d.line([(21,13),(19,20)],fill=15)
    else:
        # Ragged flowering cankers remain attached to an intact leafy crown.
        for x,y,rx in ((22,7,7),(6,22,6),(27,27,5)):
            d.polygon([(x-rx,y),(x-rx+2,y-4),(x-2,y-3),(x+1,y-5),
                       (x+rx-1,y-2),(x+rx,y+2),(x+3,y+3),
                       (x,y+5),(x-3,y+3),(x-rx+1,y+2)],fill=2)
            d.polygon([(x-rx+2,y),(x-2,y-2),(x+2,y-3),(x+rx-2,y),
                       (x+2,y+2),(x-1,y+3),(x-3,y+1)],fill=6)
            d.line([(x-3,y-1),(x,y-2),(x+3,y)],fill=13,width=2)
            d.line([(x-1,y-2),(x+1,y-1)],fill=7)
            d.line([(x-rx+1,y+1),(x-rx-3,y+2),(x-rx-5,y+1)],fill=5)


@lru_cache(None)
def _macro(v, sick=False, phase=0):
    im,d = _new(32,32,2)
    # ONE whole32px crown is the repeating unit. The earlier wrapped shoulder
    # lobes subdivided it into four closed16px capsules and read as masonry
    # in actual rooms even though the standalone tree drawing was readable.
    # A single large dome, pointed leaf faces and its short woody underside
    # make the repeating unit recognizable as a tree at native screen size.
    _leaf(d,16,12,16,11,sick=sick,kind=v)
    for dx,dy in ((-9,-6),(-1,-9),(8,-5),(-6,2),(5,2),(-10,7),(9,8)):
        _sprig(d,16+dx,12+dy,sick)
    # Dense low underbrush stays visually blocked, rather than a transparent
    # floor slit underneath a full-solid canopy cell. A fork is short and
    # local; there is no continuous black diagonal rim across the whole row.
    d.polygon([(0,24),(4,22),(8,24),(12,23),(17,25),(22,23),
               (27,24),(31,22),(31,31),(0,31)],fill=2)
    d.line([(7,26),(11,26),(16,28),(21,25),(25,26)],fill=8,width=3)
    d.line([(16,26),(16,31)],fill=8,width=4)
    d.line([(11,25),(16,27),(21,24)],fill=12 if sick else 10)
    d.line([(15,28),(15,31)],fill=12 if sick else 10)
    if sick:
        _disease(d,v,phase)
        # One substantial connected living lobe crosses all four macro
        # quadrants. An isolated q1/q2 cell must retain greenery as well.
        _leaf(d,16,16,10,6,sick=True,living=True,kind=v)
        _sprig(d,15,16,True,True)
    return im


def canopy_macro(variant=1, sick=False, phase=0):
    return _macro(_variant(variant),bool(sick),int(phase)).copy()


@lru_cache(None)
def _tree(v, large=False, second=False, sick=False, dead=False, phase=0):
    w,h = (48,64) if large else (32,48)
    im,d = _new(w,h)
    mid=w//2
    # A short stable trunk, exposed broad forks and a grounded root collar.
    d.polygon([(mid-4,h-30),(mid+4,h-30),(mid+4,h-17),(mid+6,h-9),
               (mid+13,h-4),(mid+12,h-2),(mid+5,h-4),(mid,h-9),
               (mid-6,h-4),(mid-13,h-2),(mid-14,h-4),(mid-7,h-9),
               (mid-4,h-17)],fill=1)
    d.polygon([(mid-2,h-29),(mid+2,h-29),(mid+2,h-17),(mid+4,h-9),
               (mid+10,h-4),(mid+5,h-5),(mid,h-11),(mid-6,h-5),
               (mid-10,h-4),(mid-5,h-10),(mid-2,h-18)],fill=8 if sick else 9)
    d.line([(mid-2,h-27),(mid-1,h-18),(mid-2,h-12),(mid-7,h-7)],fill=12 if sick else 10,width=2)
    _branch(d,[(2,h-29),(11,h-32),(mid,h-28),(w-10,h-30),(w-2,h-28)],sick,3)
    _branch(d,[(mid,h-23),(mid+7,h-24),(w-3,h-22)],sick,3)
    # Reuse broad leaf vocabulary but author on the actual32x48/48x64 canvas.
    if large:
        _leaf(d,mid-1,17,20,15,sick=sick,kind=v)
        _leaf(d,mid-14,34,13,10,sick=sick,kind=v)
        _leaf(d,mid+13,36,14,10,sick=sick,kind=v)
        for dx,dy in ((-12,9),(-1,5),(11,14),(-7,22),(9,25),(-14,34),(10,37)):
            _sprig(d,mid+dx,dy,sick)
    else:
        _mother(d,mid+(1 if second else 0),14+(1 if second else 0),v,sick)
    if sick:
        # Apply the same disease construction across the coherent crown area.
        disease,dd=_new(32,32);_disease(dd,v,phase)
        # Preserve the exact leaf-volume planes of the corresponding healthy
        # tree; disease is a localized overlay, not replacement wallpaper.
        pp=im.load();cp=disease.load()
        for y in range(h-16):
            for x in range(w):
                ink=cp[x%32,y%32]
                if ink and pp[x,y] in (2,3,4,15):pp[x,y]=ink
        # A live branch remains connected on both sick and skeletal trees.
        if large:
            _leaf(d,mid-9,15,11,7,sick=True,living=True,kind=v)
            _leaf(d,mid+13,37,8,5,sick=True,living=True,kind=v)
            _sprig(d,mid-10,15,True,True);_sprig(d,mid+12,37,True,True)
        else:
            _leaf(d,mid-7,10,8,5,sick=True,living=True,kind=v)
            _leaf(d,mid+9,27,6,4,sick=True,living=True,kind=v)
            _sprig(d,mid-8,10,True,True);_sprig(d,mid+8,27,True,True)
        if dead:
            # A dead specimen keeps a live parasitic green clutch: recognizable
            # crown remains, while the same tree retains its lateral anatomy.
            _branch(d,[(2,h-28),(mid-5,h-31),(mid+4,h-27),(w-2,h-29)],True,3)
            _vein(d,[(3,h-29),(mid-5,h-30),(mid+4,h-28),(w-3,h-29)],1)
    return im


def tree_group(variant=1, large=False, second=False, sick=False, dead=False, phase=0):
    return _tree(_variant(variant),bool(large),bool(second),bool(sick),bool(dead),int(phase)).copy()


def _crop(im,n,columns=2):
    return im.crop(((n%columns)*16,(n//columns)*16,(n%columns+1)*16,(n//columns+1)*16))


def _sick(name):
    return name.startswith(('blight_wall','forest_blight','sicktree_','btree_')) or 'blight' in name or name=='dead_tree'


def paint(name, phase=0, variant=1):
    v=_variant(variant);phase=int(phase)
    if not owns(name):return V2.paint(name,phase,1)
    sick=_sick(name);bank='canopy3_blight' if sick else 'foliage'
    if name.startswith('forest_blight_tree'):
        n=int(name[len('forest_blight_tree'):])
        # These canonical32x48 connector cells are fully blocked wall skins.
        # Give them a real trunk/roots against dense underbrush, not repeated
        # crown quadrants or a falsely walkable transparent root row.
        wall,wd=_new(32,48,2)
        _leaf(wd,5,41,10,6,sick=True,kind=v)
        _leaf(wd,27,42,10,6,sick=True,kind=v)
        H._paste(wall,_tree(v,sick=True,dead=True,phase=phase),(0,0))
        return _crop(wall,n),'canopy3_blight'
    if name.startswith(('canopy','forest_canopy','blight_wall')):
        q=int(name[-1])%4 if name[-1].isdigit() else 0
        im=_crop(_macro(v,sick,phase),q)
        if name=='canopy_lantern':
            # Existing feature cue remains small and warm; no new random light
            # placement is introduced by this canopy-only study.
            d=ImageDraw.Draw(im);d.line((10,7,10,11),fill=8);d.rectangle((9,10,11,13),fill=7)
        return im,bank
    if name in _TREE_NAMES:
        return _crop(_tree(v),_TREE_NAMES.index(name)),'foliage'
    for prefix in ('tree2_','birch_','fir_','sicktree_','btree_'):
        if name.startswith(prefix):
            n=int(name[len(prefix):])
            return _crop(_tree(v,False,prefix in ('tree2_','fir_'),sick,prefix=='btree_',phase),n),bank
    for prefix in ('gtree_','gtree2_'):
        if name.startswith(prefix):
            n=int(name[len(prefix):])
            return _crop(_tree(v,True,prefix=='gtree2_'),n,3),'foliage'
    if name in ('dead_tree','forest_blight_dead_tree'):
        im,d=_new()
        _branch(d,[(1,5),(6,3),(9,5),(14,3)],True,2)
        d.line([(8,5),(8,10),(5,14)],fill=8,width=3)
        _leaf(d,5,3,5,3,sick=True,living=True,kind=v)
        _vein(d,[(7,5),(10,5),(14,4)],1)
        return im,'canopy3_blight'
    raise KeyError(name)


def paint_adjacency(parent, mask, corners=0, phase=0, variant=1, quadrant=None):
    v=_variant(variant);mask=int(mask)&15;corners=int(corners)&15
    if '@q' in parent:
        parent,q=parent.rsplit('@q',1);quadrant=int(q)
    if not owns(parent):return V2.paint_adjacency(parent,mask,corners,phase,1,quadrant)
    if not parent.startswith(('canopy','forest_canopy','blight_wall')):
        return paint(parent,phase,v)
    sick=_sick(parent)
    q=int(quadrant or 0)%4
    im=_crop(_macro(v,sick,int(phase)),q);p=im.load()
    if mask&4:
        # Exposed near faces need the same tree cue even when the semantic
        # boundary cuts through the upper half of a32px mother crown. One
        # short fork/trunk is shared across the two horizontal quadrants.
        # Keep the original live leaf clutch where it overlaps the face.
        face,fd=_new(32,16)
        fd.polygon([(0,10),(4,8),(8,10),(12,9),(17,11),(22,9),
                    (27,10),(31,8),(31,15),(0,15)],fill=2)
        fd.line([(7,11),(11,11),(16,13),(21,10),(25,11)],fill=8,width=3)
        fd.line([(16,11),(16,15)],fill=8,width=4)
        fd.line([(11,10),(16,12),(21,9)],fill=12 if sick else 10)
        fd.line([(15,13),(15,15)],fill=12 if sick else 10)
        fp=face.load();xoff=(q%2)*16
        for y in range(8,16):
            for x in range(16):
                ink=fp[x+xoff,y]
                if ink and not (sick and p[x,y] in GREEN_INDICES['canopy3_blight']):p[x,y]=ink
    # Retain exact quarter-local shape grammar so 47cases share8px hardware
    # tiles and isolated masses have round organic corners instead of boxes.
    for y in range(16):
        for x in range(16):
            west=x<8;north=y<8;sx=x if west else 15-x;sy=y if north else 15-y
            hbit=8 if west else 2;vbit=1 if north else 4
            cb=1 if west and north else 2 if north else 8 if west else 4
            eh=bool(mask&hbit);ev=bool(mask&vbit)
            outside=(eh and sx<2) or (ev and sy<2)
            if eh and ev and sx<6 and sy<6:outside=(sx-5)**2+(sy-5)**2>24
            if not eh and not ev and corners&cb and sx+sy<4:outside=True
            if outside:p[x,y]=0
    return im,'canopy3_blight' if sick else 'foliage'


def fringe(parent, mask, variant=1):
    v=_variant(variant);mask=int(mask)&15;sick=_sick(parent)
    im,d=_new()
    if mask&1:
        # One horizontal limb header, not a hanging curtain. Long side leaves
        # sit outside the12px central root-foot lane retained by v2.
        d.line((0,0,15,0),fill=8,width=2)
        _leaf(d,-1,0,5,4,sick=sick,living=sick,kind=v)
        _leaf(d,17,0,5,4,sick=sick,kind=v)
        d.line((1,1,14,1),fill=12 if sick else 10)
    if mask&8:
        _leaf(d,-5,5,8,3,sick=sick,living=sick,kind=v)
        _leaf(d,-4,12,7,3,sick=sick,kind=v)
    if mask&2:
        _leaf(d,20,7,8,3,sick=sick,living=sick,kind=v)
        _leaf(d,20,13,7,2,sick=sick,kind=v)
    if mask&4:
        d.line((0,15,15,15),fill=2)
    if mask&1:
        p=im.load()
        for y in range(2,16):
            for x in range(2,14):p[x,y]=0
    return im,'canopy3_blight' if sick else 'foliage'


def arch_group(variant=1):
    _variant(variant)
    return V2.arch_group(1)


def pulse_palettes(variant=1):
    v=_variant(variant);out=V2.pulse_palettes(1)
    base=extra_palettes(v)['canopy3_blight'];states=[]
    for offset in (0,8,16,-8):
        row=list(base)
        for k in PULSE_INDICES['canopy3_blight']:
            rgb=[int(base[k][i:i+2],16) for i in (1,3,5)]
            row[k]='#'+''.join('%02x'%max(0,min(248,c+offset)) for c in rgb)
        states.append(row)
    out['canopy3_blight']=states
    return out
