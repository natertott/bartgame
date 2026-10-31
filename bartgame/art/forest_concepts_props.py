"""Five native forest interaction vocabularies; opt-in presentation only.

Every pixel is authored on its actual 16px metatile or legal OBJ canvas.
Physics, identifiers, frame counts and action semantics are supplied elsewhere.
Ground/carried liftables share exact source pixels and unmodified material banks.
"""
from functools import lru_cache
from PIL import Image, ImageDraw
import reboot_core as R

RECIPES = {
    1: 'Fern Oak', 2: 'Silver Willow', 3: 'Copper Beech',
    4: 'Velvet Cedar', 5: 'Pale Orchard',
}
BG_PALETTE_ALIASES = {
    'forest_obj_foliage': list(R.PALETTES['foliage']),
    'forest_obj_stone': list(R.PALETTES['stone']),
}
TILE_NAMES = frozenset({
    'bush','rock_small','boulder','rock','rock2','rock3','mossy_stone','sick_rock',
    'stump','sick_stump','log','fence','thorn','pillar','ruin_wall','statue',
    'bones','sick_bones','blight_crystal','dead_tree','forest_blight_dead_tree',
    'lantern_post','relic','shrine_plate','myst_pot','crack','web','door_locked',
    'door_open','torch','torch_lit','chest','chest_open','myst_chest',
    'myst_chest_open','myst_switch','myst_switch_down','myst_spring',
    'mouth_cave','mouth_hollow','mouth_thicket','cave_prop','hollow_prop',
    'thicket_prop','cave_spring','hollow_spring','thicket_spring','stairs_down',
})
FRAME_NAMES = {
    'lift': ('bush','rock','boulder','pot'),
    'interactivechest': tuple(a+'_'+b for a in ('wooden','brass','relic') for b in ('closed','open')),
    'interactiveentry': ('cave','hollow','thicket','cave_closed','hollow_closed','thicket_closed'),
}


def supports_tile(name):
    return name in TILE_NAMES


def supports_frame(sheet, frame):
    return frame in FRAME_NAMES.get(sheet, ())


def canvas(w=16, h=16, fill=0):
    im = Image.new('P', (w,h), fill)
    return im, ImageDraw.Draw(im)


def _check(variant):
    if variant not in RECIPES:
        raise ValueError('forest prop variant must be 1..5')


def _leaf(d, x, y, style, dark=3, mid=5, light=6):
    if style in (1,3):
        pts=[(x-3,y),(x-2,y-2),(x+1,y-3),(x+3,y-1),(x+2,y+2),(x-1,y+3),(x-3,y+1)]
    elif style==2:
        pts=[(x-2,y-1),(x+1,y-4),(x+2,y-1),(x+1,y+3),(x-1,y+4),(x-2,y+1)]
    elif style==4:
        pts=[(x,y-4),(x+3,y+1),(x+1,y),(x+2,y+3),(x-3,y+2),(x-2,y)]
    else:
        pts=[(x-3,y-1),(x-1,y-3),(x+1,y-2),(x+3,y),(x+2,y+2),(x,y+3),(x-2,y+1)]
    d.polygon(pts,fill=dark)
    d.line([(x-1,y-2),(x-2,y),(x,y+1)],fill=light)
    d.line([(x+1,y),(x+1,y+2)],fill=mid)


@lru_cache(None)
def lift_object(name, variant):
    _check(variant)
    im,d=canvas()
    if name=='bush':
        silhouettes={
            1:[(1,9),(2,6),(5,4),(8,3),(11,4),(14,7),(15,10),(13,14),(10,15),(5,15),(2,13)],
            2:[(2,10),(1,7),(4,4),(6,2),(8,4),(10,2),(13,5),(14,10),(12,14),(9,15),(4,15)],
            3:[(1,8),(4,4),(7,3),(10,4),(13,6),(15,10),(13,13),(10,15),(5,15),(1,12)],
            4:[(1,11),(4,8),(2,7),(6,5),(5,3),(8,1),(12,6),(10,7),(14,11),(12,14),(9,15),(4,15)],
            5:[(1,10),(2,6),(5,5),(5,3),(8,2),(11,4),(12,6),(15,8),(14,12),(11,15),(5,15),(2,13)],
        }
        d.polygon(silhouettes[variant],fill=1)
        for x,y in ((5,8),(9,7),(11,11),(6,12)):
            _leaf(d,x,y,variant)
        d.line([(4,14),(8,14),(11,13)],fill=2)
        # One connected cuttable clump with a bright upper-left leaf cluster.
        d.line([(3,7),(5,5),(6,5)],fill=7)
        if variant==3:d.line([(8,4),(11,6)],fill=6)
        if variant==5:d.rectangle((8,5,9,6),fill=7)
        return im,'foliage'
    if name in ('rock','boulder'):
        big=name=='boulder'
        outlines={
            1:[(0,8),(3,3),(8,1),(12,3),(15,7),(15,12),(12,15),(3,15),(0,12)],
            2:[(0,10),(2,5),(6,2),(11,1),(14,5),(15,11),(12,15),(3,15)],
            3:[(0,8),(4,2),(10,1),(15,6),(15,12),(11,15),(3,15),(0,12)],
            4:[(0,9),(4,4),(7,1),(12,2),(15,8),(14,13),(11,15),(3,15)],
            5:[(0,8),(3,4),(7,2),(12,3),(15,7),(15,12),(12,15),(3,15),(0,12)],
        }
        pts=outlines[variant]
        if not big:pts=[(2+(x*12)//16,4+(y*12)//16) for x,y in pts]
        d.polygon(pts,fill=1)
        if big:
            d.polygon([(1,8),(4,4),(9,2),(12,4),(14,8),(13,12),(10,14),(4,14),(1,11)],fill=4)
            d.polygon([(2,8),(5,4),(9,3),(11,5),(9,8),(4,10)],fill=6)
            d.polygon([(10,8),(13,6),(14,9),(12,12),(9,13)],fill=3)
            d.line([(4,5),(6,3),(8,3)],fill=8)
            d.line([(2,12),(5,14),(10,14)],fill=2)
        else:
            d.polygon([(3,10),(5,7),(9,5),(11,7),(12,10),(10,13),(6,14),(3,12)],fill=4)
            d.polygon([(4,9),(6,7),(9,6),(10,8),(7,10)],fill=6)
            d.line([(5,8),(6,7),(8,7)],fill=8)
            d.line([(4,13),(6,14),(9,14)],fill=2)
        if variant==2:
            d.polygon([(7,3 if big else 6),(11,5 if big else 7),(12,10 if big else 11),(8,13),(6,9)],fill=5)
            d.line([(7,4 if big else 7),(7,8 if big else 9)],fill=8)
        elif variant==3:
            d.line([(3,8 if big else 10),(8,8 if big else 10),(10,6 if big else 8)],fill=5)
        elif variant==4:
            d.polygon([(7,3 if big else 6),(10,7 if big else 8),(8,10 if big else 11),(4,9 if big else 10)],fill=7)
        if variant==3:d.line([(10,4 if big else 7),(12,6 if big else 9)],fill=5)
        if variant==5:d.point((5,6 if big else 9),fill=8)
        # The lowest contact row remains y15 in every carried frame.
        d.line([(5,15),(10 if big else 8,15)],fill=1)
        return im,'stone'
    if name=='pot':
        forms={
            1:[(4,4),(11,4),(11,6),(14,9),(13,13),(10,15),(5,15),(2,13),(1,9),(4,6)],
            2:[(5,3),(10,3),(10,7),(12,8),(13,11),(11,14),(9,15),(5,15),(3,12),(3,9),(5,7)],
            3:[(3,4),(12,4),(12,7),(14,9),(13,13),(10,15),(5,15),(2,13),(1,9),(3,7)],
            4:[(5,2),(10,2),(10,6),(13,8),(14,12),(11,15),(4,15),(1,12),(2,8),(5,6)],
            5:[(4,3),(11,3),(11,6),(14,10),(12,14),(10,15),(5,15),(2,13),(1,10),(4,6)],
        }
        d.polygon(forms[variant],fill=1)
        d.polygon([(5,5),(10,5),(10,7),(12,9),(12,12),(9,14),(5,13),(3,11),(3,9),(5,7)],fill=5)
        d.polygon([(5,7),(7,7),(6,11),(4,12),(3,10)],fill=8)
        d.polygon([(10,8),(12,10),(11,13),(8,14),(8,12)],fill=3)
        d.line([(3,9),(12,9)],fill=10 if variant!=2 else 11)
        top=2 if variant==4 else 3
        d.rectangle((4,top,11,top+2),fill=1)
        d.line([(4,top),(10,top)],fill=11)
        d.line([(5,top+2),(10,top+2)],fill=6)
        d.point((4,10),fill=11)
        if variant==5:d.line([(6,10),(8,12),(10,10)],fill=11)
        return im,'gold'
    raise KeyError(name)


@lru_cache(None)
def chest(tier, opened, variant):
    _check(variant)
    im,d=canvas(32,32)
    l,r=6,25
    # A coherent 20px chest and a shallow contact shadow, not a giant bag icon.
    d.ellipse((5,26,26,29),fill=1)
    if variant==2:
        body=[(l,16),(l+2,14),(r-2,14),(r,16),(r,25),(r-2,27),(l+2,27),(l,25)]
    elif variant==4:
        body=[(l,16),(l+2,13),(r-2,13),(r,16),(r-1,26),(r-3,28),(l+2,28),(l,25)]
    else:body=[(l,15),(r,15),(r,26),(r-1,28),(l+1,28),(l,26)]
    d.polygon(body,fill=1)
    base=13 if variant==4 or tier==2 and variant in (2,5) else 4
    lit=14 if base==13 else 6
    d.rectangle((l+1,17,r-1,26),fill=base)
    d.polygon([(l+1,18),(l+6,19),(l+6,25),(l+1,25)],fill=lit)
    d.polygon([(r-5,18),(r-1,17),(r-1,26),(r-5,27)],fill=2 if tier==2 else 3)
    for y in (20,24):d.line([(l+2,y),(r-2,y)],fill=3 if tier<2 else 2)
    metal=(7,9,10)[tier]
    bright=(10,11,12)[tier]
    if variant==2:metal=(10,11,11)[tier];bright=(11,12,12)[tier]
    if variant==3:
        d.line([(l+2,22),(r-2,22)],fill=6 if tier<2 else 10)
    if variant==5:
        d.line([(l+6,18),(l+6,25)],fill=6)
        d.line([(r-6,18),(r-6,25)],fill=3)
    band_x=(l+3,r-3) if variant!=3 else (l+4,r-4)
    if opened:
        top=6 if variant in (1,3,5) else 7
        d.polygon([(l,top+2),(l+2,top),(r-2,top),(r,top+2),(r,15),(l,15)],fill=1)
        d.rectangle((l+1,top+2,r-1,13),fill=5)
        d.line([(l+2,top+1),(r-2,top+1)],fill=bright)
        d.rectangle((l+1,15,r-1,19),fill=2)
        d.line([(l+2,19),(r-2,19)],fill=6)
        for x in band_x:d.line([(x,top+2),(x,13)],fill=metal,width=2)
    else:
        if variant in (1,3):
            lid=[(l,16),(l,13),(l+3,10),(r-3,10),(r,13),(r,16)]
            top=[(l+1,14),(l+3,11),(r-3,11),(r-1,14),(r-1,16),(l+1,16)]
        elif variant==2:
            lid=[(l,16),(l+2,11),(l+5,10),(r-4,10),(r-1,12),(r,16)]
            top=[(l+1,15),(l+3,12),(l+5,11),(r-4,11),(r-2,13),(r-1,15)]
        elif variant==4:
            lid=[(l,16),(l+1,12),(l+4,9),(r-4,9),(r-1,12),(r,16)]
            top=[(l+1,15),(l+3,12),(l+5,10),(r-5,10),(r-2,13),(r-1,15)]
        else:
            lid=[(l,16),(l,11),(l+2,10),(r-2,10),(r,12),(r,16)]
            top=[(l+1,15),(l+1,12),(l+3,11),(r-2,11),(r-1,13),(r-1,15)]
        d.polygon(lid,fill=1);d.polygon(top,fill=5 if tier<2 else base)
        d.line([(l+3,11),(r-5,11)],fill=lit)
        d.line([(l+1,16),(r-1,16)],fill=2)
        for x in band_x:
            d.line([(x,12),(x,26)],fill=metal,width=2)
            d.point((x,12),fill=bright)
        d.rectangle((14,16,17,21),fill=1)
        d.rectangle((14,16,17,19),fill=bright)
        d.rectangle((15,17,16,18),fill=2)
    for x in band_x:
        d.line([(x,20),(x,27)],fill=metal,width=2)
        d.point((x,21),fill=bright)
    d.line([(l+2,27),(r-2,27)],fill=metal)
    if tier==2:
        # A large clasp and strong material bands identify value, not extra size.
        if not opened:
            d.polygon([(16,14),(19,17),(16,21),(13,17)],fill=11)
            d.polygon([(16,15),(17,17),(16,19),(15,17)],fill=13)
        for x in (l+1,r-1):d.point((x,24),fill=bright)
    return im


@lru_cache(None)
def entry(style, closed, variant):
    _check(variant)
    im,d=canvas(32,64)
    y0=16
    def P(points):return [(x,y+y0) for x,y in points]
    def line(points,**kw):d.line(P(points),**kw)
    def poly(points,**kw):d.polygon(P(points),**kw)
    def box(b,**kw):d.rectangle((b[0],b[1]+y0,b[2],b[3]+y0),**kw)
    def ellipse(b,**kw):d.ellipse((b[0],b[1]+y0,b[2],b[3]+y0),**kw)
    pointed=variant in (2,4)
    if style=='cave':
        outer=[(0,45),(0,23),(3,13),(8,6),(15,2),(22,5),(28,13),(31,24),(31,45)] if not pointed else [(0,45),(0,25),(4,14),(10,6),(16,0),(23,6),(29,17),(31,25),(31,45)]
        if variant==3:outer=[(0,45),(0,22),(2,14),(5,7),(9,5),(23,5),(29,10),(31,20),(31,45)]
        if variant==4:outer=[(0,45),(0,24),(3,15),(8,8),(13,2),(19,2),(24,9),(29,16),(31,25),(31,45)]
        if variant==5:outer=[(0,45),(0,22),(3,12),(8,7),(15,5),(24,7),(29,14),(31,25),(30,45)]
        inner=[(6,44),(6,24),(9,16),(13,12),(18,12),(23,18),(25,26),(25,44)] if not pointed else [(6,44),(6,26),(9,18),(13,12),(16,7),(20,13),(24,22),(25,27),(25,44)]
        if variant==3:inner=[(6,44),(6,24),(8,17),(11,13),(20,13),(24,18),(25,25),(25,44)]
        if variant==5:inner=[(6,44),(6,25),(8,18),(12,14),(19,14),(24,20),(25,27),(25,44)]
        poly(outer,fill=1)
        poly([(2,43),(2,23),(5,14),(9,8),(15,4),(22,7),(27,15),(29,25),(29,43)],fill=4)
        # Broad top-left planes; side faces follow the same light source.
        poly([(2,29),(3,20),(7,12),(11,8),(16,5),(19,6),(16,10),(11,14),(8,22),(6,34),(3,42),(2,42)],fill=6)
        poly([(25,17),(29,25),(29,42),(26,42),(24,30)],fill=3)
        poly(inner,fill=1)
        for points in ([(3,23),(7,24)],[(6,14),(10,17)],[(12,8),(14,12)],[(22,8),(20,13)],[(27,19),(24,22)],[(27,33),(29,33)]):line(points,fill=2)
        line([(3,28),(3,38)],fill=8)
        line([(8,11),(11,8),(14,6)],fill=8)
        if variant==3:line([(4,24),(4,31)],fill=12)
        if variant==5:
            for x,y in ((2,20),(3,35),(27,14)):line([(x,y),(x+1,y+1)],fill=8)
        pal='iron'
    else:
        # A real trunk or a woven hedge keeps a wide, tall dark aperture.
        trunk=[(0,46),(2,35),(1,19),(4,8),(9,2),(22,1),(27,7),(30,19),(29,35),(31,46),(25,46),(24,37),(25,24),(23,17),(19,12),(13,12),(9,17),(7,25),(7,38),(6,46)]
        # Paint a real dark cavity, not transparent scenery through a tree frame.
        poly([(6,44),(6,24),(9,16),(13,12),(19,12),(23,17),(25,25),(25,44)],fill=1)
        poly(trunk,fill=1)
        poly([(2,44),(4,34),(3,19),(6,9),(11,4),(21,3),(25,9),(28,21),(27,35),(29,44),(26,44),(24,35),(25,24),(22,15),(19,10),(13,10),(9,14),(6,23),(6,36),(4,44)],fill=5)
        line([(5,21),(7,12),(11,6),(17,5),(22,7)],fill=8,width=2)
        line([(3,37),(5,30),(4,24)],fill=6)
        line([(26,17),(28,24),(26,36),(28,42)],fill=3,width=2)
        line([(4,44),(1,46),(7,45)],fill=10)
        line([(26,43),(30,46)],fill=6)
        if variant==3:
            box((8,3,23,7),fill=5)
            line([(9,3),(22,3)],fill=8)
        elif variant==4:
            poly([(7,8),(11,1),(16,0),(21,3),(25,10),(21,8),(16,4),(12,7)],fill=1)
            line([(11,3),(16,2),(20,4)],fill=8)
        if variant==2:
            line([(11,4),(9,14),(10,21)],fill=11)
            line([(21,5),(23,16),(22,20)],fill=8)
        elif variant==3:
            for x,y in ((4,23),(5,31),(26,26)):line([(x,y),(x+1,y+4)],fill=2)
            ellipse((3,17,8,22),outline=8)
        elif variant==4:
            poly([(8,8),(15,1),(23,8),(20,9),(16,5),(12,10)],fill=3)
            line([(8,14),(7,22),(9,29)],fill=2)
        elif variant==5:
            line([(4,32),(5,26),(4,20)],fill=11)
            line([(27,36),(28,30),(26,24)],fill=8)
            line([(1,23),(3,21),(6,22)],fill=11,width=2)
            line([(25,33),(28,31),(30,32)],fill=11,width=2)
        if style=='thicket':
            # One restrained family of pointed clumps frames the dark opening.
            sites=((4,13),(10,6),(21,6),(27,16),(28,29),(4,33))
            for x,y in sites:
                points=[(x-3,y),(x-1,y-4),(x+2,y-3),(x+4,y),(x+2,y+4),(x-2,y+4)]
                poly(points,fill=1)
                poly([(x-2,y),(x,y-3),(x+2,y-1),(x+2,y+2),(x-1,y+3)],fill=13)
                line([(x-1,y-1),(x,y-2)],fill=14)
                if variant==5:line([(x,y),(x+1,y)],fill=11)
        pal='gear'
    # A clean pale threshold is the persistent approach cue across all styles.
    line([(6,43),(25,43)],fill=12 if pal=='iron' else 10,width=2)
    line([(7,43),(22,43)],fill=15 if pal=='iron' else 11)
    if not closed:
        line([(7,44),(25,44)],fill=3)
    else:
        # This is the actual trial grille, not a fictional key-locked entrance.
        for x in (10,15,20):
            line([(x,16),(x,42)],fill=1,width=3)
            line([(x,17),(x,41)],fill=6 if pal=='iron' else 8)
        line([(8,28),(24,28)],fill=5 if pal=='iron' else 7,width=2)
        line([(9,27),(23,27)],fill=8 if pal=='iron' else 11)
    return im,pal


def _plate(down, variant):
    im,d=canvas(fill=1)
    shapes={1:[(2,0),(13,0),(15,2),(15,13),(13,15),(2,15),(0,13),(0,2)],2:[(5,0),(10,0),(14,3),(15,8),(13,13),(10,15),(4,15),(0,11),(0,5)],3:[(1,0),(14,0),(15,1),(15,14),(14,15),(1,15),(0,14),(0,1)],4:[(4,0),(11,0),(15,4),(15,11),(11,15),(4,15),(0,11),(0,4)],5:[(3,0),(12,0),(15,3),(15,12),(12,15),(3,15),(0,12),(0,3)]}
    d.polygon(shapes[variant],fill=1)
    d.polygon([(3,1),(12,1),(14,3),(14,11),(11,14),(3,14),(1,11),(1,3)],fill=4)
    d.line([(3,1),(11,1),(14,4)],fill=8)
    d.line([(1,4),(1,11),(4,14),(11,14)],fill=2)
    y=5 if down else 3
    d.rectangle((3,y,12,11),fill=12 if down else 6)
    d.line([(3,y),(11,y)],fill=14 if down else 8)
    if down:
        d.line([(5,8),(7,10),(10,7)],fill=15,width=1)
    else:
        if variant==2:d.ellipse((5,5,10,9),outline=3)
        elif variant==4:d.polygon([(7,5),(10,8),(7,10),(5,8)],fill=3)
        elif variant==5:d.line([(5,8),(7,6),(10,8),(7,10),(5,8)],fill=3)
        else:d.line([(5,7),(7,5),(10,7),(8,9),(5,7)],fill=3)
    return im


def _gate(kind, variant):
    im,d=canvas()
    if kind=='crack':
        silhouettes={1:[(0,5),(3,1),(12,0),(15,4),(15,13),(12,15),(2,15),(0,12)],2:[(0,4),(5,0),(12,1),(15,5),(14,14),(10,15),(1,14)],3:[(0,5),(4,0),(12,0),(15,4),(15,14),(11,15),(1,15),(0,12)],4:[(0,6),(3,2),(8,0),(13,2),(15,7),(15,13),(12,15),(2,15),(0,12)],5:[(0,5),(3,1),(9,0),(14,3),(15,9),(13,14),(9,15),(1,14)]}
        d.polygon(silhouettes[variant],fill=1)
        d.polygon([(1,6),(4,2),(11,1),(14,5),(14,12),(11,14),(3,14),(1,11)],fill=5)
        d.polygon([(2,5),(5,2),(10,2),(12,4),(10,7),(4,8)],fill=7)
        d.polygon([(11,8),(14,5),(14,12),(10,14),(8,11)],fill=3)
        cracks={1:[(9,1),(7,5),(9,8),(6,11),(7,14)],2:[(6,1),(7,5),(5,8),(8,11),(7,14)],3:[(10,1),(8,4),(9,8),(6,10),(5,14)],4:[(7,1),(9,4),(7,8),(10,11),(9,14)],5:[(9,1),(7,4),(8,7),(5,10),(7,14)]}
        pts=cracks[variant]
        d.line([(x+1,y) for x,y in pts],fill=8,width=2)
        d.line(pts,fill=1,width=2)
        d.line([pts[2],(3,7 if variant%2 else 10)],fill=1)
        d.point((3,5),fill=8)
        return im,'forest_obj_stone'
    if kind=='web':
        # Anchored connected pale silk, never loose pickup-like stars.
        hubs={1:(8,8),2:(7,6),3:(8,9),4:(9,7),5:(6,8)}
        cx,cy=hubs[variant]
        anchors=[(0,0),(15,0),(15,15),(0,15),(0,8),(15,8)]
        for p in anchors:
            d.line([(p[0],min(15,p[1]+1)),(cx,min(15,cy+1))],fill=2)
            d.line([p,(cx,cy)],fill=8)
        loops=[[(3,3),(8,2),(12,3),(13,8),(12,12),(8,13),(3,12),(2,8),(3,3)],[(5,5),(8,4),(10,5),(11,8),(10,10),(8,11),(5,10),(4,8),(5,5)]]
        if variant==2:loops=[[(2,3),(7,2),(12,3),(12,7),(10,11),(5,12),(2,9),(2,3)],[(4,5),(7,4),(10,5),(10,8),(8,10),(5,9),(4,5)]]
        elif variant==4:loops=[[(3,2),(9,1),(13,4),(14,9),(10,13),(4,13),(1,8),(3,2)],[(5,5),(9,3),(12,6),(11,10),(7,11),(4,8),(5,5)]]
        for points in loops:d.line(points,fill=7)
        d.line([(0,0),(3,3),(5,5)],fill=15)
        d.point((15,0),fill=15)
        return im,'forest_obj_stone'
    if kind=='locked':
        im,d=canvas(fill=1)
        # Four open slats expose negative space; a single central lock owns focus.
        d.line([(1,0),(1,15)],fill=1,width=3)
        d.line([(14,0),(14,15)],fill=1,width=3)
        for x in (2,6,10,14):
            d.line([(x,2),(x,14)],fill=6 if variant in (1,3,5) else 4,width=2)
            d.line([(x,2),(x,12)],fill=10 if variant in (1,3,5) else 11)
        d.line([(0,5),(15,5)],fill=8,width=2)
        d.line([(1,4),(14,4)],fill=11)
        d.rectangle((5,6,11,13),fill=1)
        d.rectangle((5,6,10,11),fill=10)
        d.line([(6,6),(10,6)],fill=12)
        d.ellipse((7,7,9,9),fill=1)
        d.line([(8,9),(8,11)],fill=1,width=2)
        return im,'gold'
    raise KeyError(kind)


def _censer(lit, phase, variant):
    im,d=canvas()
    if variant in (1,3,5):
        d.ellipse((2,13,13,15),fill=1)
        d.line([(7,8),(7,13)],fill=5,width=3)
        d.polygon([(1,6),(14,6),(12,10),(9,11),(5,10),(2,8)],fill=1)
        d.line([(2,6),(13,6)],fill=15)
        d.line([(3,8),(5,10),(10,10),(12,8)],fill=12)
        d.line([(3,14),(11,14)],fill=12)
    else:
        d.rectangle((3,13,12,15),fill=1)
        d.line([(5,14),(10,14)],fill=12)
        d.line([(7,9),(7,13)],fill=5,width=3)
        d.polygon([(2,6),(13,6),(12,10),(4,10)],fill=1)
        d.line([(3,6),(12,6)],fill=15)
        d.rectangle((4,7,11,9),fill=12)
    if lit:
        poses=[[(5,5),(5,3),(7,4),(8,0),(11,4),(10,5)],[(5,5),(6,2),(7,3),(9,0),(9,2),(11,4),(10,5)],[(5,5),(4,3),(7,4),(7,1),(10,2),(11,5)]]
        d.polygon(poses[phase%3],fill=14)
        d.line([(7,5),(8,2),(9,5)],fill=15)
    else:
        d.line([(5,5),(7,4),(10,5)],fill=4)
        d.point((8,4),fill=2)
    return im


def _spring(phase,variant):
    im,d=canvas()
    if variant in (2,5):
        d.polygon([(2,4),(6,2),(11,3),(15,7),(14,12),(10,15),(4,14),(0,10),(0,7)],fill=1)
        d.polygon([(2,6),(6,4),(11,4),(13,7),(12,11),(9,13),(4,12),(2,10)],fill=11)
    else:
        d.ellipse((0,3,15,15),fill=1)
        d.ellipse((1,3,14,13),fill=11)
    d.ellipse((3,5,12,11),fill=2)
    d.line([(3,5),(6,4),(10,4)],fill=14)
    d.line([(4+(phase&1),7),(8+(phase&1),7)],fill=7)
    d.line([(7-(phase&1),10),(10-(phase&1),10)],fill=5)
    return im


def _prop(name,phase,variant):
    im,d=canvas()
    if name in ('stump','sick_stump','hollow_prop','thicket_prop'):
        # Cut wood has a flat readable ellipse; roots stay attached to the mass.
        d.ellipse((0,11,15,15),fill=1)
        d.polygon([(3,4),(12,4),(12,10),(15,13),(12,14),(3,14),(0,13),(3,10)],fill=1)
        d.rectangle((4,5,11,12),fill=9)
        d.ellipse((3,2,12,7),fill=11)
        d.arc((4,3,11,6),10,300,fill=8)
        d.line([(4,8),(4,11)],fill=10)
        d.line([(11,8),(11,12)],fill=8)
        if variant==2:d.line([(5,7),(4,12)],fill=12)
        if variant==3:d.line([(9,7),(10,11)],fill=10)
        if variant==4:d.line([(6,8),(7,11)],fill=8)
        if name=='sick_stump':
            d.line([(10,4),(9,7),(11,10),(9,14)],fill=2)
            d.line([(10,7),(11,9)],fill=7)
        return im,'foliage'
    if name=='log':
        d.rectangle((0,5,15,13),fill=1)
        d.rectangle((0,6,15,11),fill=9)
        d.line([(3,6),(15,6)],fill=11)
        d.line([(8,8),(13,9),(15,8)],fill=8)
        d.ellipse((0,5,6,13),fill=11)
        d.arc((1,6,5,12),-80,200,fill=8)
        d.point((2,7),fill=12)
        if variant in (2,4):d.line([(10,5),(12,2)],fill=1,width=2)
        return im,'foliage'
    if name=='fence':
        im,d=canvas(fill=4)
        # Permanent boundary: subordinate dark wood, without lock-like gold.
        for x in (1,11):
            d.rectangle((x,2,x+3,15),fill=1)
            d.line([(x+1,3),(x+1,14)],fill=9)
        if variant in (2,4):
            d.line([(0,5),(15,9)],fill=8,width=3);d.line([(0,4),(15,8)],fill=10)
        else:
            d.rectangle((0,6,15,9),fill=8);d.line([(0,6),(15,6)],fill=10)
        return im,'foliage'
    if name=='thorn':
        # Burnable/cuttable brush uses dry pale twigs, not background dark canopy.
        for points in ([(2,15),(5,9),(3,2)],[(7,15),(10,9),(14,4)],[(3,8),(8,4),(12,0)]):
            d.line(points,fill=1,width=3);d.line(points,fill=10)
        for x,y in ((4,5),(6,10),(11,7),(9,3)):
            d.polygon([(x,y),(x+3,y-2),(x+1,y+2)],fill=12)
        if variant==2:d.line([(0,11),(6,13),(13,11)],fill=11)
        if variant==4:d.line([(3,1),(4,4)],fill=7)
        return im,'foliage'
    if name in ('pillar','ruin_wall','statue'):
        if name=='statue':
            d.ellipse((1,12,14,15),fill=1)
            d.polygon([(4,13),(5,8),(4,5),(7,1),(10,2),(12,6),(10,9),(12,13)],fill=1)
            d.polygon([(5,12),(6,8),(5,6),(7,3),(9,3),(10,6),(9,9),(11,12)],fill=4)
            d.line([(6,5),(7,3),(8,3)],fill=7)
            d.line([(7,8),(9,8)],fill=14)
        else:
            d.rectangle((2,1,13,14),fill=1)
            d.rectangle((3,2,12,12),fill=4)
            d.line([(3,2),(3,11)],fill=7)
            d.rectangle((1,12,14,15),fill=1)
            d.line([(2,12),(13,12)],fill=6)
            d.rectangle((2,0,13,3),fill=5)
            d.line([(3,0),(12,0)],fill=8)
            if name=='ruin_wall':
                d.rectangle((0,5,15,11),fill=3)
                d.line([(0,5),(15,5)],fill=5)
                d.line([(7,5),(7,10)],fill=2)
        if variant==2:d.line([(4,8),(5,10)],fill=6)
        elif variant==3:d.line([(10,3),(11,5)],fill=12)
        elif variant==4:d.line([(7,1),(8,3)],fill=3)
        elif variant==5:d.point((4,3),fill=8)
        return im,'stone'
    if name in ('bones','sick_bones'):
        # A connected rib or joint is ground litter, never a detached loot star.
        if variant in (2,4):
            d.arc((3,3,12,13),160,370,fill=1,width=3)
            d.arc((3,2,12,12),160,370,fill=8,width=2)
            for x,y in ((4,7),(7,5),(10,7)):d.line([(x,y),(x-1,y+3)],fill=7)
        else:
            d.line([(2,12),(11,5)],fill=1,width=3)
            d.line([(2,11),(11,4)],fill=8,width=2)
            d.ellipse((0,9,4,12),fill=8);d.ellipse((9,2,13,5),fill=8)
            d.line([(3,11),(10,5)],fill=7)
        return im,'stone'
    if name in ('dead_tree','forest_blight_dead_tree'):
        if name=='dead_tree':im,d=canvas(fill=4)
        for points in ([(8,15),(7,9),(7,5),(4,2)],[(7,10),(11,7),(13,1)],[(7,6),(9,2)]):
            d.line(points,fill=1,width=3);d.line(points,fill=9)
        d.line([(6,14),(7,10),(6,7)],fill=11)
        d.line([(2,15),(6,13),(9,15),(13,14)],fill=8)
        d.point((11,6),fill=14 if variant in (1,3,4) else 15)
        if variant==2:d.line([(12,3),(14,4)],fill=7)
        if variant==5:d.rectangle((4,4,5,5),fill=7)
        return im,'blight'
    if name=='blight_crystal':
        # The old identifier now draws a rooted fungal growth, still decorative.
        d.ellipse((0,11,15,15),fill=2)
        for x,y,h in ((3,13,6),(8,14,11),(12,13,5)):
            d.line([(x,y),(x,y-h+3)],fill=9,width=2)
            d.polygon([(x-3,y-h+3),(x-2,y-h+1),(x,y-h),(x+3,y-h+2),(x+3,y-h+3)],fill=1)
            d.line([(x-2,y-h+1),(x,y-h),(x+2,y-h+1)],fill=14 if variant in (1,3,4) else 15)
        return im,'blight'
    if name=='lantern_post':
        d.line([(3,15),(3,2),(10,2),(11,5)],fill=1,width=3)
        d.line([(3,14),(3,2),(9,2)],fill=10)
        d.rectangle((7,5,14,13),fill=1)
        d.polygon([(8,6),(12,6),(13,8),(12,11),(9,11)],fill=12)
        d.line([(9,7),(9,10)],fill=15)
        d.line([(7,12),(14,12)],fill=6)
        if phase&1:d.point((11,8),fill=15)
        return im,'stone'
    if name in ('relic','shrine_plate'):
        if name=='relic':
            im,d=canvas(fill=2)
            d.rectangle((0,0,15,15),outline=1)
            d.line([(1,0),(14,0)],fill=5)
        d.ellipse((0,1,15,15),fill=1)
        d.ellipse((1,1,14,13),fill=4)
        d.line([(3,3),(6,2),(10,2)],fill=7)
        d.ellipse((3,3,12,11),fill=2)
        d.line([(7,4),(7,10)],fill=14,width=2)
        d.line([(4,7),(11,7)],fill=14)
        d.point((7,6),fill=15)
        if variant in (2,5):d.point((10,4),fill=8)
        return im,'stone'
    raise KeyError(name)


def paint_frame(sheet,frame,variant):
    _check(variant)
    if not supports_frame(sheet,frame):raise KeyError((sheet,frame))
    if sheet=='lift':
        im,bank=lift_object(frame,variant)
        return im,{'foliage':'bugs','stone':'iron','gold':'gear'}[bank]
    if sheet=='interactivechest':
        tier,state=frame.split('_')
        return chest(('wooden','brass','relic').index(tier),state=='open',variant),'gear'
    if sheet=='interactiveentry':
        return entry(frame.split('_')[0],frame.endswith('_closed'),variant)
    raise KeyError((sheet,frame))


def paint_tile(name,phase,variant):
    _check(variant)
    if not supports_tile(name):raise KeyError(name)
    if name in ('bush','rock_small','boulder','myst_pot'):
        im,bank=lift_object({'rock_small':'rock','myst_pot':'pot'}.get(name,name),variant)
        return im,{'foliage':'forest_obj_foliage','stone':'forest_obj_stone','gold':'gold'}[bank]
    if name in ('rock','rock2','rock3','mossy_stone','sick_rock','cave_prop'):
        im,_=lift_object('boulder',variant);im=im.copy()
        d=ImageDraw.Draw(im)
        if name in ('mossy_stone','sick_rock'):
            d.line([(2,7),(4,5),(6,5)],fill=5)
            if name=='sick_rock':d.line([(12,4),(12,6)],fill=8)
        return im,'forest_obj_stone'
    if name in ('crack','web','door_locked'):
        return _gate({'crack':'crack','web':'web','door_locked':'locked'}[name],variant)
    if name=='door_open':
        # Direct BG ground draw: opaque warm lane, no black transparent square.
        im,d=canvas(fill=9)
        d.line([(1,0),(1,15)],fill=8)
        d.line([(14,0),(14,15)],fill=8)
        d.line([(2,0),(2,15)],fill=10)
        d.line([(13,0),(13,15)],fill=7)
        return im,'ground'
    if name in ('torch','torch_lit'):return _censer(name.endswith('lit'),phase,variant),'forest_obj_stone'
    if name in ('chest','chest_open','myst_chest','myst_chest_open'):
        return chest(0,name.endswith('open'),variant).crop((8,13,24,29)),'gold'
    if name in ('myst_switch','myst_switch_down'):
        return _plate(name.endswith('down'),variant),'forest_obj_stone'
    if name in ('myst_spring','cave_spring','hollow_spring','thicket_spring'):
        return _spring(phase,variant),'water'
    if name.startswith('mouth_'):
        style=name[6:]
        im,d=canvas(fill=1)
        d.line([(1,15),(1,6),(4,2),(8,0),(12,2),(14,6),(14,15)],fill=6 if style=='cave' else 8,width=2)
        d.line([(2,14),(13,14)],fill=14 if style=='cave' else 11)
        return im,'forest_obj_stone' if style=='cave' else 'gold'
    if name=='stairs_down':
        im,d=canvas(fill=1)
        d.line([(0,1),(0,14),(15,14),(15,1)],fill=4)
        d.line([(1,0),(14,0)],fill=8)
        for y in (3,7,11):
            d.line([(2,y),(13,y)],fill=6)
            d.line([(2,y+1),(13,y+1)],fill=2)
        d.line([(2,14),(13,14)],fill=14)
        return im,'forest_obj_stone'
    return _prop(name,phase,variant)
