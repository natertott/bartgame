"""Second forest study: clear interactions and ten native wooden chests.

Local variants 1..5 correspond to optional BART_FOREST profiles 6..10.
Only pixels and explicit new display frames originate here. The engine owns
underlay restoration, safe log placement and the larger landmark draw slots.
Existing carry-object materials and all physical OBJ palette banks stay exact.
"""
from functools import lru_cache
from pathlib import Path
import json
from PIL import Image, ImageDraw
import reboot_core as R
import forest_concepts_props as OLD

RECIPES = {1: 'Black Sap Oak', 2: 'Violet Strangler', 3: 'Witchfire Weep',
           4: 'Amethyst Canker', 5: 'Royal Bruise'}
ANCHORS = {'interactivechest': [16, 29], 'forestlandmark': [8, 32]}
BG_PALETTE_ALIASES = {name: list(colors) for name, colors in OLD.BG_PALETTE_ALIASES.items()}
TILE_NAMES = (OLD.TILE_NAMES - {'dead_tree', 'forest_blight_dead_tree'}) | {'hlog_0', 'hlog_1'}
LANDMARK_FRAMES = ('relic', 'shrine_available', 'shrine_spent', 'keylock')
FRAME_NAMES = {
    'lift': OLD.FRAME_NAMES['lift'],
    'interactivechest': OLD.FRAME_NAMES['interactivechest'] + ('wooden_b_closed', 'wooden_b_open'),
    'interactiveentry': OLD.FRAME_NAMES['interactiveentry'],
    'forestlandmark': LANDMARK_FRAMES,
}
CHEST_DESIGNS = (
    'Coopered travelling trunk', 'Hollow-log coffer',
    'Slatted packing chest', 'Woven willow hamper',
    'Acorn-cap coffer', 'Cut-stump cache',
    'Cedar footlocker', 'Nailed salvage chest',
    'Root-bound reliquary box', 'Carved bark casket',
)
OLD_VARIANTS = {1: 1, 2: 3, 3: 1, 4: 4, 5: 5}


def _check(variant):
    if int(variant) not in RECIPES:
        raise ValueError('forest prop local variant must be 1..5')
    return int(variant)


def supports_tile(name):
    return name in TILE_NAMES


def supports_frame(sheet, frame):
    return frame in FRAME_NAMES.get(sheet, ())


def canvas(w=16, h=16, fill=0):
    im = Image.new('P', (w, h), fill)
    return im, ImageDraw.Draw(im)


def _wood_lid(d, design, offset=0):
    """Draw a literal native lid; offset opens it without filtered scaling."""
    profiles = [
        [(5,17),(5,13),(8,9),(23,9),(26,13),(26,17)],
        [(4,17),(5,12),(9,10),(23,10),(27,13),(27,17)],
        [(5,16),(5,10),(26,10),(26,16)],
        [(5,17),(6,12),(10,10),(22,10),(26,12),(27,17)],
        [(5,18),(6,13),(9,9),(13,7),(19,7),(23,10),(26,14),(26,18)],
        [(6,17),(6,12),(9,9),(22,9),(25,12),(25,17)],
        [(4,16),(4,11),(27,11),(27,16)],
        [(5,17),(4,11),(12,9),(27,12),(26,18)],
        [(6,17),(6,12),(10,9),(22,9),(26,13),(26,17)],
        [(5,17),(6,12),(10,9),(22,10),(26,13),(27,17)],
    ]
    pts = [(x, y + offset) for x, y in profiles[design]]
    d.polygon(pts, fill=1)
    inner = [(x + (1 if x < 16 else -1), y + (1 if y < 16 else -1)) for x, y in profiles[design]]
    d.polygon([(x, y + offset) for x, y in inner], fill=5 if design not in (7,8) else 4)
    top = min(y for _, y in profiles[design]) + offset
    d.line([(10,top+1),(20,top+1)], fill=6)
    if design in (0,1):
        for x in (9,22):
            d.line([(x,top+2),(x-1,16+offset)], fill=7, width=2)
            d.point((x,top+2), fill=10)
        if design == 1:
            d.arc((5,12+offset,11,17+offset), 120, 300, fill=6)
    elif design == 2:
        for x in (11,19): d.line([(x,top+2),(x,15+offset)], fill=3)
        d.line([(7,top+2),(24,top+2)], fill=6)
        for x in (7,24): d.point((x,top+2), fill=10)
    elif design == 3:
        d.arc((7,top+2,25,19+offset), 180, 350, fill=6)
        for x in (10,15,20): d.line([(x,top+3),(x,15+offset)], fill=4)
    elif design == 4:
        d.line([(9,top+4),(13,top+2),(19,top+2),(23,top+5)], fill=6)
        for x,y in ((10,14),(14,11),(19,12),(22,15)):
            d.line([(x,y+offset),(x+1,y+1+offset)], fill=3)
    elif design == 5:
        d.ellipse((8,top+1,23,top+7), fill=6)
        d.arc((10,top+2,21,top+6), 20, 330, fill=3)
        d.line([(14,top+3),(18,top+3)], fill=5)
    elif design == 6:
        d.line([(6,top+1),(25,top+1)], fill=6)
        d.line([(6,top+3),(25,top+3)], fill=3)
        for x in (7,24): d.line([(x,top+1),(x,15+offset)], fill=8)
    elif design == 7:
        d.line([(6,top+2),(24,top+4)], fill=3, width=2)
        d.line([(8,top+2),(21,top+4)], fill=6)
        for x,y in ((7,12),(23,14)): d.point((x,y+offset), fill=11)
    elif design == 8:
        d.line([(8,top+4),(9,top+1),(13,top+2),(15,16+offset)], fill=3, width=2)
        d.line([(22,top+2),(21,top+5),(24,16+offset)], fill=7, width=2)
        d.line([(10,top+3),(12,top+3)], fill=14)
    else:
        d.line([(8,top+4),(13,top+1),(22,top+3)], fill=6)
        d.line([(10,top+5),(22,top+5)], fill=3)
        d.point((23,top+4), fill=10)
    d.line([(6,16+offset),(25,16+offset)], fill=2)


@lru_cache(None)
def chest(tier, opened, variant, alternate=False):
    """Twenty complete wooden states plus the retained reinforced/relic tiers."""
    variant = _check(variant)
    if int(tier) != 0:
        return OLD.chest(int(tier), bool(opened), OLD_VARIANTS[variant]).copy()
    design = (variant - 1) * 2 + bool(alternate)
    im,d = canvas(32,32)
    d.ellipse((4,26,27,29), fill=1)
    bodies = [
        [(5,16),(26,16),(25,26),(23,28),(8,28),(6,26)],
        [(4,16),(27,16),(27,24),(24,28),(7,28),(4,25)],
        [(5,15),(26,15),(26,27),(25,28),(6,28),(5,27)],
        [(5,16),(27,16),(25,25),(22,28),(9,28),(6,25)],
        [(5,16),(26,16),(24,24),(21,28),(10,28),(7,24)],
        [(7,15),(24,15),(25,25),(28,28),(22,28),(20,27),(11,28),(5,28),(7,24)],
        [(4,15),(27,15),(27,26),(25,28),(6,28),(4,26)],
        [(5,16),(26,17),(26,25),(24,28),(7,28),(5,26)],
        [(6,16),(26,16),(25,26),(22,28),(9,28),(6,26)],
        [(5,16),(27,16),(26,25),(23,28),(9,28),(6,25)],
    ]
    d.polygon(bodies[design], fill=1)
    d.polygon([(7,17),(23,17),(24,25),(21,27),(9,27),(7,25)], fill=4 if design!=8 else 3)
    d.polygon([(7,17),(13,17),(12,25),(9,26),(7,24)], fill=5)
    d.polygon([(22,17),(25,17),(24,25),(21,27),(20,25)], fill=2 if design==8 else 3)
    if design in (0,1):
        for x in (9,22):
            d.line([(x,18),(x,26)], fill=7, width=2)
            d.point((x,20), fill=10)
        d.line([(12,23),(19,23)], fill=3)
        if design == 1:
            d.ellipse((4,17,11,27), fill=6)
            d.arc((5,18,10,26), 20, 330, fill=3)
            d.point((7,22), fill=4)
    elif design == 2:
        for x in (10,16,22): d.line([(x,19),(x,26)], fill=3)
        d.line([(7,25),(24,25)], fill=6)
        for x,y in ((7,20),(24,20),(8,25),(23,25)): d.point((x,y), fill=10)
    elif design == 3:
        for y in (20,23,26): d.line([(8,y),(23,y)], fill=6)
        for x in (10,16,22): d.line([(x,19),(x-1,26)], fill=3)
        d.line([(6,18),(8,25),(11,27),(21,27),(24,24)], fill=5)
    elif design == 4:
        for x in (10,15,20): d.line([(x,19),(x+1,25)], fill=5)
        d.line([(10,27),(20,27)], fill=6)
        d.polygon([(15,19),(18,21),(16,24),(14,22)], fill=8)
    elif design == 5:
        for x in (9,14,20,23):
            d.line([(x,18),(x-1,22),(x,26)], fill=3)
        d.line([(7,25),(5,28)], fill=5, width=2)
        d.line([(23,25),(27,28)], fill=3, width=2)
        d.line([(10,18),(10,24)], fill=6)
    elif design == 6:
        d.line([(6,21),(25,21)], fill=3)
        d.line([(6,24),(25,24)], fill=5)
        for x in (6,24):
            d.rectangle((x,19,x+1,26), fill=7)
            d.point((x,20), fill=10)
        d.line([(7,27),(10,27)], fill=2)
        d.line([(21,27),(24,27)], fill=2)
    elif design == 7:
        for y in (20,24): d.line([(7,y),(24,y+1)], fill=3)
        d.line([(8,26),(22,19)], fill=5, width=2)
        for p in ((9,25),(21,20),(23,25)): d.point(p, fill=10)
    elif design == 8:
        d.line([(8,18),(10,23),(8,27)], fill=7, width=2)
        d.line([(23,18),(21,22),(24,26)], fill=4, width=2)
        d.line([(13,21),(19,22)], fill=2)
        d.line([(7,23),(9,23)], fill=14)
        d.point((10,24), fill=13)
    else:
        d.line([(7,20),(13,18),(23,20)], fill=5)
        d.line([(8,24),(16,26),(23,23)], fill=3)
        for x in (8,23):d.point((x,21), fill=10)
    if opened:
        _wood_lid(d, design, -7)
        # The raised lid is an upright backboard, joined to the hinge. It
        # must never become a detached cap floating above the box.
        d.rectangle((5,8,26,15),fill=1)
        d.rectangle((6,8,25,14),fill=5 if design not in (7,8) else 4)
        d.line([(6,8),(6,13)],fill=6)
        if design in (0,1,6):
            for x in (9,22):d.line([(x,8),(x,13)],fill=7,width=2)
        elif design in (2,3):
            for x in (11,19):d.line([(x,8),(x,13)],fill=3)
        elif design==5:d.arc((9,7,22,13),0,340,fill=3)
        elif design==7:d.line([(8,12),(23,9)],fill=6,width=2)
        elif design==8:d.line([(10,8),(12,13)],fill=7,width=2)
        else:d.line([(10,10),(21,11)],fill=3)
        d.polygon([(6,14),(25,14),(25,19),(7,19)], fill=1)
        d.line([(6,13),(6,18)],fill=6)
        d.line([(25,13),(25,18)],fill=3)
        d.point((7,14),fill=8)
        d.point((24,14),fill=7)
        d.line([(8,18),(23,18)], fill=6)
        d.line([(7,15),(24,15)], fill=3)
    else:
        _wood_lid(d, design)
        # A simple clasp, not a false keyhole on a freely opened chest.
        d.rectangle((14,16,18,20), fill=1)
        d.rectangle((15,16,17,19), fill=9)
        d.line([(15,16),(17,16)], fill=12)
    return im


def _plate(down, variant):
    """Five plain physical buttons: raised top, side face, depressed state."""
    im,d = canvas(fill=2)
    d.rectangle((0,0,15,15), outline=1)
    d.line([(1,0),(14,0)], fill=5)
    d.line([(0,2),(0,13)], fill=4)
    d.line([(1,14),(14,14)], fill=1)
    if variant == 1:
        d.ellipse((1,3,14,14), fill=1)
        d.ellipse((2,4,13,13), fill=3)
        y = 6 if down else 2
        d.ellipse((2,y,13,y+7), fill=5 if down else 7)
        d.arc((2,y,13,y+7), 180, 290, fill=8)
        if down:d.line([(5,11),(10,11)], fill=13)
    elif variant == 2:
        d.rectangle((2,4,13,13), fill=1)
        d.rectangle((3,5,12,12), fill=3)
        y = 6 if down else 2
        d.rectangle((2,y,13,y+6), fill=5 if down else 7)
        d.line([(3,y),(12,y)], fill=8)
        d.line([(2,y+1),(2,y+5)], fill=6)
        if down:
            d.point((3,11), fill=14);d.point((12,11), fill=14)
    elif variant == 3:
        d.rectangle((1,3,14,14), fill=1)
        d.rectangle((2,4,13,13), fill=9)
        y = 6 if down else 2
        d.rectangle((2,y,13,y+6), fill=11 if down else 12)
        d.line([(3,y),(12,y)], fill=14)
        d.line([(7,y+1),(7,y+5)], fill=10)
        for x in (3,12):d.point((x,y+4), fill=8)
    elif variant == 4:
        d.polygon([(8,1),(14,7),(14,10),(8,15),(1,10),(1,7)], fill=1)
        d.polygon([(8,3),(13,8),(8,13),(2,8)], fill=3)
        y = 3 if down else 0
        d.polygon([(8,y+1),(14,y+7),(8,y+12),(1,y+7)], fill=5 if down else 7)
        d.line([(2,y+6),(8,y+1),(13,y+6)], fill=8)
        if down:d.point((8,13), fill=13)
    else:
        d.ellipse((1,1,14,14), fill=1)
        d.ellipse((2,2,13,13), fill=6)
        d.ellipse((4,4,11,12), fill=2)
        y = 6 if down else 2
        d.ellipse((4,y,11,y+6), fill=12 if down else 7)
        d.arc((4,y,11,y+6), 190, 290, fill=15 if down else 8)
        if down:d.point((7,11), fill=14)
    return im


def _web(variant):
    im,d = canvas()
    paths = []
    if variant == 1:
        hub=(8,8)
        paths += [[p,hub] for p in ((0,0),(8,0),(15,1),(15,10),(12,15),(1,15),(0,7))]
        paths += [[(4,3),(8,2),(12,4),(13,9),(10,13),(4,12),(2,7),(4,3)],
                  [(6,6),(9,5),(11,8),(9,10),(6,10),(5,8),(6,6)]]
    elif variant == 2:
        paths += [[(0,1),(5,2),(10,1),(15,0)],[(1,1),(3,6),(2,11),(4,15)],
                  [(6,2),(5,6),(7,11),(6,14)],[(11,1),(10,6),(11,10),(10,15)],
                  [(15,0),(13,5),(14,9),(13,14)],[(2,7),(5,8),(10,7),(14,8)],
                  [(3,12),(6,13),(10,12),(13,14)]]
    elif variant == 3:
        paths += [[(0,0),(5,4),(10,5),(15,2)],[(0,14),(5,11),(11,12),(15,15)],
                  [(0,6),(5,7),(10,8),(15,6)],[(2,15),(5,10),(5,5),(4,0)],
                  [(12,0),(10,5),(11,11),(14,15)],
                  [(7,3),(10,5),(11,10),(8,13),(5,10),(5,6),(7,3)]]
        d.ellipse((6,5,9,10), fill=7)
        d.line([(7,5),(8,5),(7,9)], fill=15)
    elif variant == 4:
        hub=(1,1)
        paths += [[hub,p] for p in ((15,0),(15,7),(15,15),(7,15),(0,15))]
        paths += [[(7,0),(6,3),(5,5),(3,6),(0,7)],
                  [(13,0),(12,5),(9,9),(5,12),(0,13)],
                  [(15,7),(13,11),(10,14),(7,15)]]
    else:
        paths += [[(0,3),(4,1),(9,2),(15,0)],[(0,15),(3,12),(8,14),(15,12)],
                  [(2,1),(5,6),(3,12)],[(8,2),(8,8),(8,14)],
                  [(13,1),(11,6),(13,13)],[(0,7),(5,6),(8,8),(11,6),(15,8)],
                  [(2,10),(5,9),(8,11),(12,10),(15,12)]]
    for p in paths:
        d.line([(x,min(15,y+1)) for x,y in p], fill=2)
        d.line(p, fill=8)
    # A few attached wet fibre highlights, not free loot-like sparkles.
    for p in (paths[0][:2], paths[-1][-2:]):d.line(p, fill=15)
    return im


def _thorns(variant):
    im,d = canvas()
    branches = {
        1:[[(1,15),(4,9),(2,2)],[(6,15),(10,8),(14,2)],[(3,9),(8,4),(11,0)]],
        2:[[(2,15),(6,10),(4,4),(8,0)],[(10,15),(11,8),(15,4)],[(0,8),(5,6),(12,8)]],
        3:[[(1,14),(4,9),(4,2)],[(7,15),(9,10),(12,3),(15,1)],[(0,6),(5,4),(10,6)]],
        4:[[(0,14),(5,11),(5,4),(2,0)],[(9,15),(11,10),(10,3),(14,0)],[(3,7),(8,6),(14,8)]],
        5:[[(2,15),(4,10),(3,5),(6,0)],[(10,15),(10,9),(14,3)],[(0,4),(5,7),(12,6),(15,2)]],
    }
    for points in branches[variant]:
        d.line(points, fill=1, width=3)
        d.line(points, fill=10)
    for x,y in ((3,5),(5,10),(10,7),(12,4)):
        d.polygon([(x-1,y),(x+3,y-2),(x,y+3)], fill=13)
        d.line([(x,y),(x+1,y-1)], fill=14)
    # One rooted infected strand carries a bright line along black wood.
    vein = branches[variant][0]
    d.line(vein, fill=5, width=3)
    d.line(vein, fill=6)
    d.point(vein[1], fill=7)
    d.line([(11,11),(13,10),(14,11)], fill=12)
    return im


def _barred_gate(variant):
    im,d = canvas(fill=9)
    # The engine draws ONE large padlock across a two-cell gate assembly.
    for x in (1,6,11,15):
        d.line([(x,0),(x,15)], fill=1, width=3)
        d.line([(x,0),(x,14)], fill=13 if variant in (2,4) else 12)
    if variant in (2,5):
        d.line([(0,4),(15,8)], fill=1, width=3)
        d.line([(0,3),(15,7)], fill=14)
    else:
        d.line([(0,5),(15,5)], fill=1, width=3)
        d.line([(0,4),(15,4)], fill=14)
    return im


def _other_relic(variant):
    im,d=canvas(16,32)
    d.ellipse((0,28,15,31),fill=1)
    if variant==2:
        d.line([(3,28),(3,11),(5,5),(10,3),(13,6),(13,9)],fill=1,width=3)
        d.line([(3,27),(3,11),(5,5),(10,4),(12,6)],fill=8)
        d.line([(4,11),(6,6),(10,5)],fill=11)
        d.line([(10,7),(10,10)],fill=8)
        d.ellipse((6,9,14,21),fill=1)
        d.ellipse((7,10,13,20),fill=8)
        d.ellipse((8,12,12,18),fill=13)
        d.line([(9,12),(9,16)],fill=14)
        d.line([(8,10),(10,10)],fill=12)
        d.rectangle((2,27,12,30),fill=8)
        d.line([(2,27),(11,27)],fill=12)
    elif variant==3:
        hand=[(3,18),(1,14),(2,10),(2,4),(4,3),(5,9),(6,1),(8,1),(8,9),(10,3),(12,4),(11,11),(14,7),(15,9),(13,15),(10,18),(10,26),(13,28),(13,30),(2,30),(2,28),(5,26),(5,18)]
        d.polygon(hand,fill=1)
        d.polygon([(4,17),(2,13),(3,11),(3,5),(4,9),(6,12),(7,3),(7,11),(10,6),(10,13),(13,9),(12,14),(9,17),(8,26),(6,27),(6,18)],fill=9)
        d.line([(3,11),(4,15),(6,17)],fill=12)
        d.polygon([(8,10),(10,13),(8,16),(6,13)],fill=13)
        d.line([(7,13),(8,11)],fill=14)
        d.rectangle((3,28,12,30),fill=8)
        d.line([(3,28),(11,28)],fill=11)
    elif variant==4:
        d.rectangle((5,20,10,28),fill=1)
        d.rectangle((6,21,9,28),fill=8)
        d.line([(6,21),(6,27)],fill=11)
        d.polygon([(1,20),(1,10),(4,6),(8,1),(12,6),(14,10),(14,20)],fill=1)
        d.polygon([(2,19),(2,11),(5,7),(8,3),(11,7),(13,11),(13,19)],fill=8)
        d.line([(3,11),(6,7),(8,5)],fill=12)
        d.polygon([(8,7),(11,12),(8,17),(5,12)],fill=1)
        d.polygon([(8,9),(10,12),(8,15),(6,12)],fill=13)
        d.line([(7,12),(8,10)],fill=14)
        d.rectangle((2,27,13,30),fill=8)
        d.line([(2,27),(12,27)],fill=12)
    else:
        d.line([(8,28),(8,16)],fill=1,width=4)
        d.line([(7,27),(7,18)],fill=9,width=2)
        for pts in ([(3,10),(0,7),(0,2)],[(12,10),(15,6),(14,1)]):
            d.line(pts,fill=1,width=3);d.line(pts,fill=8)
        d.line([(0,3),(1,7),(3,9)],fill=11)
        d.ellipse((2,4,13,19),fill=1)
        d.ellipse((3,5,12,18),fill=8)
        d.ellipse((5,7,10,16),fill=1)
        d.arc((3,5,12,18),180,290,fill=12)
        d.polygon([(8,8),(10,11),(8,15),(6,11)],fill=13)
        d.line([(7,11),(8,9)],fill=14)
        d.line([(3,30),(7,26),(12,29)],fill=8,width=3)
        d.line([(4,29),(7,27)],fill=11)
    return im


def _other_shrine(variant,spent):
    im,d=canvas(16,32)
    d.ellipse((0,28,15,31),fill=1)
    if variant==2:
        d.line([(4,29),(7,24),(8,17)],fill=1,width=4)
        d.line([(7,26),(13,29)],fill=1,width=3)
        d.line([(5,28),(7,23),(7,18)],fill=11,width=2)
        d.line([(6,25),(7,21)],fill=12)
        d.line([(8,26),(12,29)],fill=9)
        d.rectangle((1,8,14,18),fill=1)
        d.rectangle((2,10,13,17),fill=4)
        d.line([(2,10),(2,15)],fill=7)
        d.rectangle((2,8,13,12),fill=7)
        d.rectangle((4,9,11,11),fill=2)
        surface=[(4,10),(8,10),(10,10)]
        d.line([(3,8),(12,8)],fill=8)
    elif variant==3:
        d.line([(8,29),(8,17)],fill=1,width=4)
        d.line([(7,28),(7,19)],fill=6)
        d.line([(7,20),(7,25)],fill=7)
        d.line([(7,25),(3,23),(1,26)],fill=9,width=2)
        d.line([(8,26),(12,23),(14,26)],fill=10,width=2)
        d.polygon([(0,12),(1,8),(4,6),(7,8),(11,5),(15,9),(13,16),(8,20),(3,17)],fill=1)
        d.polygon([(1,12),(2,9),(4,8),(7,10),(11,7),(14,10),(12,15),(8,18),(4,16)],fill=5)
        d.line([(2,9),(4,8),(7,10)],fill=8)
        d.line([(9,9),(11,7),(13,10)],fill=7)
        d.ellipse((4,10,12,15),fill=2)
        surface=[(5,12),(8,11),(11,12)]
        d.rectangle((3,28,12,30),fill=5)
        d.line([(3,28),(11,28)],fill=8)
    elif variant==4:
        d.rectangle((5,18,10,29),fill=1)
        d.rectangle((6,19,9,28),fill=3)
        d.line([(6,20),(6,27)],fill=6)
        d.polygon([(0,9),(4,5),(12,5),(15,9),(13,17),(9,20),(5,19),(2,16)],fill=1)
        d.polygon([(1,10),(4,7),(12,7),(14,10),(12,16),(9,18),(5,17),(3,15)],fill=5)
        d.line([(1,10),(4,7),(11,7)],fill=8)
        d.polygon([(3,9),(5,8),(11,8),(13,10),(11,13),(5,13)],fill=2)
        surface=[(5,10),(8,10),(11,11)]
        d.rectangle((1,28,14,30),fill=4)
        d.line([(2,28),(13,28)],fill=7)
    else:
        for pts in ([(4,17),(4,23),(2,29)],[(8,19),(8,29)],[(12,17),(12,24),(14,29)]):
            d.line(pts,fill=1,width=3);d.line(pts,fill=10)
        d.line([(3,24),(2,28)],fill=12)
        d.ellipse((0,7,15,20),fill=1)
        d.ellipse((1,7,14,17),fill=6)
        d.ellipse((3,9,12,14),fill=2)
        d.line([(3,8),(7,7),(11,8)],fill=8)
        d.line([(2,15),(5,19),(10,19),(13,15)],fill=3)
        for x in (3,12):d.line([(x,13),(x+(-1 if x==3 else 1),18)],fill=10,width=2)
        surface=[(4,11),(7,10),(11,11)]
    if spent:
        d.line(surface,fill=3)
    else:
        d.line(surface,fill=14)
        d.line([(6,surface[-1][1]+2),(10,surface[-1][1]+2)],fill=12)
        # A droplet touches the rim, tying the healing cue to the object.
        dropx=8 if variant!=3 else 11
        d.line([(dropx,2),(dropx-1,5),(dropx,7)],fill=15)
        d.point((dropx+1,5),fill=8)
    return im


@lru_cache(None)
def landmark(frame, variant):
    variant = _check(variant)
    if frame not in LANDMARK_FRAMES:raise KeyError(frame)
    im,d = canvas(16,32)
    if frame == 'keylock':
        d.line([(4,17),(4,10),(6,7),(10,7),(12,10),(12,17)], fill=1, width=3)
        d.line([(4,16),(4,11),(6,8),(10,8),(11,10)], fill=8, width=2)
        d.line([(5,10),(6,9),(9,9)], fill=12)
        d.line([(12,10),(12,16)],fill=8,width=2)
        d.line([(11,9),(12,11)],fill=7)
        d.rounded_rectangle((1,16,14,31), radius=2, fill=1)
        d.rectangle((2,17,13,29), fill=8)
        d.rectangle((2,17,11,28), fill=10)
        d.line([(3,17),(11,17)], fill=12)
        d.line([(2,18),(2,25)], fill=11)
        d.ellipse((5,20,10,25), fill=1)
        d.polygon([(7,24),(9,24),(10,28),(6,28)], fill=1)
        d.line([(3,30),(12,30)], fill=7)
        return im,'gear'
    if frame == 'relic':
        if variant>1:return _other_relic(variant),'gear'
        d.ellipse((0,28,15,31), fill=1)
        d.polygon([(3,28),(4,23),(4,17),(3,15),(3,8),(6,3),(8,1),(11,5),(13,9),(13,15),(11,18),(11,24),(13,28)], fill=1)
        d.polygon([(5,15),(5,9),(8,4),(11,9),(11,15),(8,18)], fill=8)
        d.line([(6,10),(8,6),(9,8)], fill=12)
        d.polygon([(8,7),(10,11),(8,15),(6,11)], fill=13)
        d.line([(8,9),(8,12)], fill=14)
        d.line([(6,19),(6,25)], fill=10, width=2)
        d.line([(10,19),(10,26)], fill=6)
        d.rectangle((3,26,12,29), fill=8)
        d.line([(3,26),(11,26)], fill=12)
        d.line([(2,30),(13,30)], fill=7)
        if variant in (2,5):d.point((9,5), fill=12)
        return im,'gear'
    down = frame == 'shrine_spent'
    if variant>1:return _other_shrine(variant,down),'iron'
    # Broad stone basin and its supporting stem are one two-cell-tall object.
    d.ellipse((0,28,15,31), fill=1)
    d.rectangle((5,18,10,28), fill=1)
    d.rectangle((6,19,9,27), fill=4)
    d.line([(6,20),(6,26)], fill=7)
    d.rectangle((2,27,13,30), fill=4)
    d.line([(2,27),(12,27)], fill=8)
    d.polygon([(0,12),(1,9),(5,7),(10,7),(14,10),(15,13),(13,18),(10,20),(5,20),(1,17)], fill=1)
    d.ellipse((1,8,14,17), fill=5 if down else 7)
    d.ellipse((3,10,12,15), fill=2)
    d.line([(3,16),(6,19),(10,19),(13,16)], fill=3)
    d.line([(3,9),(7,8),(11,9)], fill=8)
    if down:
        d.line([(5,13),(9,14)], fill=3)
        d.point((8,11), fill=4)
    else:
        d.line([(4,12),(7,11),(10,12)], fill=14)
        d.line([(6,14),(10,14)], fill=12)
        # One attached tall drop is clearly water rather than a loose item.
        d.polygon([(8,0),(10,4),(10,6),(8,8),(6,6),(6,4)], fill=1)
        d.line([(8,2),(7,5),(8,6),(9,5)], fill=15)
        d.point((8,4), fill=8)
    return im,'iron'


@lru_cache(None)
def log_group(variant, orientation='h', opaque=False):
    variant = _check(variant)
    if orientation not in ('h','v'):raise ValueError(orientation)
    im,d = canvas(32,16,4 if opaque else 0)
    d.polygon([(1,6),(6,3),(27,3),(31,5),(31,12),(27,14),(5,14),(1,12)], fill=1)
    d.polygon([(6,4),(27,4),(30,6),(30,11),(26,13),(6,13)], fill=9)
    d.line([(7,4),(26,4),(29,6)], fill=11)
    d.polygon([(7,10),(15,11),(23,9),(30,10),(29,12),(25,13),(7,13)], fill=8)
    d.line([(10,6),(15,7),(19,6),(26,7)], fill=10)
    d.line([(12,10),(17,9),(22,10)], fill=8)
    d.ellipse((0,4,9,13), fill=1)
    d.ellipse((1,4,8,12), fill=11)
    d.arc((2,5,7,11), 20, 330, fill=8)
    d.line([(3,7),(5,6),(6,8),(5,10)], fill=10)
    d.point((3,6), fill=12)
    if variant == 1:
        d.line([(20,4),(20,2),(17,0)], fill=1, width=3)
        d.line([(20,4),(20,2),(18,1)], fill=9)
    elif variant == 2:
        d.line([(26,5),(29,1)], fill=1, width=3)
        d.line([(26,5),(28,2)], fill=11)
        d.line([(13,11),(15,13),(18,13)], fill=13)
    elif variant == 3:
        d.line([(14,5),(18,6),(23,5)], fill=12)
        d.ellipse((20,7,24,10), outline=8)
    elif variant == 4:
        d.line([(11,4),(12,7),(14,7)], fill=8)
        d.line([(23,9),(24,12)], fill=11)
    else:
        d.line([(18,4),(18,2),(15,0)], fill=1, width=3)
        d.line([(18,3),(16,1)], fill=10)
        d.line([(25,4),(29,3)], fill=12)
    if orientation == 'v':im=im.transpose(Image.Transpose.ROTATE_270)
    return im,'foliage'


def paint_frame(sheet, frame, variant):
    variant = _check(variant)
    if not supports_frame(sheet,frame):raise KeyError((sheet,frame))
    if sheet == 'forestlandmark':return landmark(frame,variant)
    if sheet == 'lift':return OLD.paint_frame(sheet,frame,OLD_VARIANTS[variant])
    if sheet == 'interactiveentry':
        style = frame.split('_')[0]
        favored = {'cave': (1,4,1,4,1), 'hollow': (1,3,1,3,1), 'thicket': (1,3,3,1,3)}
        return OLD.entry(style,frame.endswith('_closed'),favored[style][variant-1])
    alternate = frame.startswith('wooden_b_')
    tier = 0 if frame.startswith('wooden') else 1 if frame.startswith('brass') else 2
    return chest(tier,frame.endswith('_open'),variant,alternate),'gear'


def paint_tile(name, phase, variant):
    variant = _check(variant)
    if not supports_tile(name):raise KeyError(name)
    if name in ('hlog_0','hlog_1'):
        im,bank = log_group(variant)
        x = int(name[-1])*16
        return im.crop((x,0,x+16,16)),bank
    if name == 'thorn':return _thorns(variant),'blight'
    if name == 'web':return _web(variant),'forest_obj_stone'
    if name == 'crack':
        # The broad rounded fracture of the user's preferred first-pass #4.
        return OLD._gate('crack',4)[0].copy(),'forest_obj_stone'
    if name == 'door_locked':return _barred_gate(variant),'ground'
    if name == 'door_open':return canvas(fill=9)[0],'ground'
    if name in ('myst_switch','myst_switch_down'):
        return _plate(name.endswith('_down'),variant),'forest_obj_stone'
    if name in ('chest','chest_open','myst_chest','myst_chest_open'):
        return chest(0,name.endswith('_open'),variant).crop((8,13,24,29)),'gold'
    if name == 'log':
        im,bank = log_group(variant)
        return im.crop((0,0,16,16)),bank
    if name == 'sick_stump':
        im,d=canvas()
        d.ellipse((0,11,15,15),fill=1)
        d.rectangle((3,4,12,12),fill=8)
        d.ellipse((2,2,13,7),fill=10)
        d.arc((4,3,11,6),0,310,fill=8)
        vein=[(10,4),(9,8),(11,11),(9,14)]
        d.line(vein,fill=5,width=3);d.line(vein,fill=6);d.point((9,8),fill=7)
        return im,'blight'
    if name == 'blight_crystal':
        im,d=canvas()
        d.ellipse((0,11,15,15),fill=8)
        for x,y,h in ((3,13,7),(8,14,12),(12,13,6)):
            d.line([(x,y),(x,y-h+3)],fill=9,width=2)
            d.polygon([(x-3,y-h+3),(x-2,y-h+1),(x,y-h),(x+3,y-h+2),(x+3,y-h+3)],fill=5)
            d.line([(x-2,y-h+1),(x,y-h),(x+2,y-h+1)],fill=13)
            d.point((x,y-h+1),fill=7)
        return im,'blight'
    if name == 'shrine_plate':
        # The large basin stands in the solid statue cell above this genuinely
        # walkable pad. Keep the pad low, clear and attached to its approach.
        im,d=canvas()
        d.ellipse((0,5,15,15),fill=1)
        d.ellipse((1,4,14,12),fill=4)
        d.arc((1,4,14,12),180,290,fill=7)
        d.line([(3,11),(12,11)],fill=3)
        d.line([(4,8),(6,7),(8,8),(11,7)],fill=12)
        return im,'forest_obj_stone'
    if name == 'relic':
        # This legacy FLOOR-only picture is not the generated relic feature.
        # The real feature gets its dedicated tall marker at gSpots.relic.
        return canvas(fill=4)[0],'ground'
    return OLD.paint_tile(name,phase,OLD_VARIANTS[variant])


def validate():
    specs={m['name']:m for m in json.loads(Path(__file__).with_name('reboot_contracts.json').read_text())['tiles']}
    checked=0;carry=0;wood=set();web=set();plates=set()
    for variant in RECIPES:
        for name in sorted(TILE_NAMES):
            for phase in range(specs[name]['frames']):
                im,bank=paint_tile(name,phase,variant)
                assert im.mode=='P' and im.size==(16,16),(variant,name,phase)
                assert set(im.getdata()) <= set(range(16)),(variant,name,phase)
                checked+=1
        for sheet,frames in FRAME_NAMES.items():
            size=(16,16) if sheet=='lift' else (32,32) if sheet=='interactivechest' else (32,64) if sheet=='interactiveentry' else (16,32)
            for name in frames:
                im,bank=paint_frame(sheet,name,variant)
                assert im.mode=='P' and im.size==size,(variant,sheet,name,im.size)
                assert set(im.getdata()) <= set(range(16))
                if sheet=='lift':assert im.getbbox()[3]==16,(variant,name,im.getbbox())
                checked+=1
        for tile,frame in (('bush','bush'),('rock_small','rock'),('boulder','boulder'),('myst_pot','pot')):
            bg,bp=paint_tile(tile,0,variant);ob,op=paint_frame('lift',frame,variant)
            assert bg.tobytes()==ob.tobytes(),(variant,tile,'carry pixels')
            aliases={'forest_obj_foliage':'foliage','forest_obj_stone':'stone','gold':'gold'}
            objs={'bugs':'foliage','iron':'stone','gear':'gold'}
            assert R.PALETTES[aliases[bp]]==R.PALETTES[objs[op]],(variant,tile,'carry palette')
            carry+=1
        for alternate in (False,True):wood.add(chest(0,False,variant,alternate).tobytes())
        web.add(_web(variant).tobytes());plates.add(_plate(False,variant).tobytes())
    assert len(wood)==10 and len(web)==5 and len(plates)==5
    return {'native_instances':checked,'carry_equalities':carry,'distinct_closed_wooden_chests':len(wood),'distinct_webs':len(web),'distinct_simple_buttons':len(plates),'landmark_canvas':[16,32],'landmark_order':list(LANDMARK_FRAMES),'source_only':True}
