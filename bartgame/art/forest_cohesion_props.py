"""Grounded forest matter for the room-cohesion pass, profile32 only.

Native indexed drawings, transparent local contacts, restrained material planes.
Shared liftable and OBJ drawings deliberately keep the accepted source pixels;
this module supplies the forest BG presentation, never a recolored screenshot.
"""
from functools import lru_cache
from PIL import Image, ImageDraw
import forest_concepts_v2_props as BASE

BG_PALETTE_ALIASES = {name: list(colors) for name, colors in BASE.BG_PALETTE_ALIASES.items()}
TILE_NAMES = BASE.TILE_NAMES
FRAME_NAMES = BASE.FRAME_NAMES
ANCHORS = BASE.ANCHORS
RETAINED_TILE_NAMES = frozenset({'bush', 'rock_small', 'boulder', 'myst_pot', 'relic', 'door_open'})
OWNED_TILE_NAMES = TILE_NAMES - RETAINED_TILE_NAMES
RETAINED_FRAME_REASON = ('Shared OBJ/carry identity and its fixed physical palette stay exact; '
                         'forest placement and real floor provide the new context.')


def supports_tile(name):
    return name in TILE_NAMES


def supports_frame(sheet, frame):
    return BASE.supports_frame(sheet, frame)


def paint_frame(sheet, frame, variant=1):
    image, bank = BASE.paint_frame(sheet, frame, 1)
    return image.copy(), bank


def canvas(w=16, h=16):
    image = Image.new('P', (w, h), 0)
    return image, ImageDraw.Draw(image)


def _contact(d, x0=2, x1=13, y=14, ink=1):
    # An attached, short contact mass; exterior alpha is real local ground.
    d.line([(x0+1, y), (x1-1, y)], fill=ink)
    if x1-x0 > 7:
        d.line([(x0+3, y+1), (x1-3, y+1)], fill=ink)


def _rock(name):
    im, d = canvas()
    if name == 'mossy_stone':
        # This ID is walkable: a sunk low flagstone, not another tall boulder.
        d.polygon([(2,9),(5,6),(11,6),(14,9),(12,12),(5,13),(2,11)], fill=2)
        d.polygon([(3,9),(6,7),(11,7),(13,9),(10,11),(5,12)], fill=4)
        d.line([(5,8),(8,7),(10,7)], fill=5)
        d.line([(4,11),(7,11),(8,10)], fill=3)
        return im, 'forest_obj_stone'
    _contact(d, 0, 15, 14)
    if name == 'rock2':
        d.polygon([(0,7),(4,3),(10,2),(14,5),(15,11),(12,14),(3,14),(0,11)], fill=1)
        d.polygon([(1,7),(5,4),(10,3),(13,6),(13,10),(10,12),(3,12),(1,10)], fill=4)
        d.polygon([(2,7),(6,4),(10,4),(11,6),(7,8),(3,9)], fill=6)
        d.polygon([(10,8),(14,8),(14,12),(10,14),(6,14),(7,11)], fill=3)
        d.line([(3,6),(5,4),(8,4)], fill=7)
        d.line([(10,9),(12,9)], fill=5)
    elif name == 'rock3':
        d.polygon([(1,5),(5,1),(11,2),(14,5),(13,9),(15,12),(11,15),(3,14),(0,11)], fill=1)
        d.polygon([(2,5),(6,2),(11,3),(12,5),(10,8),(4,8)], fill=5)
        d.polygon([(2,10),(6,7),(12,8),(14,11),(10,13),(4,13)], fill=4)
        d.line([(4,4),(7,3),(10,3)], fill=7)
        d.line([(3,10),(7,9),(10,10)], fill=6)
        d.line([(3,12),(6,14),(11,14)], fill=2)
    else:
        d.polygon([(0,8),(3,3),(9,1),(13,4),(15,9),(14,13),(11,15),(3,14),(0,12)], fill=1)
        d.polygon([(1,8),(4,4),(9,2),(12,5),(14,9),(12,12),(8,13),(3,12)], fill=4)
        d.polygon([(2,8),(5,4),(9,3),(11,5),(8,8),(4,10)], fill=6)
        d.polygon([(9,9),(13,7),(14,10),(11,13),(7,13)], fill=3)
        d.line([(4,5),(6,3),(8,3)], fill=7)
        d.line([(2,12),(5,14),(10,14)], fill=2)
    if name == 'sick_rock':
        # Subordinate bruised stone, not the bombable wall's branching crack.
        d.line([(10,5),(12,6),(12,9),(10,10)], fill=3)
        d.line([(3,10),(5,11),(6,10)], fill=5)
    return im, 'forest_obj_stone'


def _stump(sick=False):
    im, d = canvas()
    _contact(d, 0, 15, 14)
    if sick:
        d.polygon([(3,5),(11,4),(12,10),(15,13),(12,15),(8,13),(3,15),(0,13),(3,10)], fill=8)
        d.polygon([(4,5),(10,5),(10,10),(12,13),(9,12),(5,13),(4,11)], fill=9)
        d.ellipse((2,2,12,7), fill=8)
        d.ellipse((3,2,11,5), fill=11)
        d.arc((4,3,10,5), 0, 270, fill=9)
        d.line([(4,7),(4,11)], fill=10)
        d.line([(9,5),(8,8),(9,11),(7,14)], fill=5, width=3)
        d.line([(9,5),(8,8),(9,11),(7,14)], fill=13)
        d.point((8,8), fill=7)
        return im, 'blight'
    d.polygon([(3,5),(12,5),(12,10),(15,13),(13,15),(8,13),(3,15),(0,13),(3,10)], fill=1)
    d.polygon([(4,5),(11,5),(11,10),(13,13),(9,12),(5,13),(3,12),(4,9)], fill=9)
    d.line([(4,6),(4,11),(2,13)], fill=10)
    d.line([(10,7),(10,11),(12,13)], fill=8)
    d.ellipse((2,2,13,7), fill=8)
    d.ellipse((3,2,12,5), fill=11)
    d.arc((4,2,11,5), 10, 270, fill=9)
    d.line([(5,3),(8,3)], fill=12)
    d.line([(2,12),(4,11),(5,12)], fill=5)
    return im, 'foliage'


@lru_cache(None)
def log_group(variant=1, orientation='h', opaque=False):
    im, d = canvas(32, 16)
    d.line([(3,14),(27,14)], fill=1)
    d.line([(8,15),(23,15)], fill=1)
    d.polygon([(1,6),(5,2),(27,2),(31,5),(31,11),(28,14),(5,14),(1,12)], fill=1)
    d.polygon([(5,3),(26,3),(30,5),(30,10),(27,12),(6,12)], fill=9)
    d.polygon([(7,9),(14,10),(22,8),(30,9),(29,11),(25,13),(7,13)], fill=8)
    d.line([(8,3),(25,3),(28,5)], fill=11)
    d.line([(9,5),(15,6),(19,5),(25,6)], fill=10)
    d.line([(12,9),(17,8),(23,9)], fill=8)
    d.ellipse((0,3,9,13), fill=8)
    d.ellipse((1,3,8,11), fill=11)
    d.arc((2,4,7,10), 10, 300, fill=9)
    d.line([(3,6),(5,5),(6,7),(4,9)], fill=10)
    d.line([(3,4),(5,4)], fill=12)
    # A short attached moss shelf, never a detached twig or bright debris.
    d.line([(19,3),(22,2),(25,3)], fill=3)
    d.line([(20,2),(23,2)], fill=5)
    if orientation == 'v':
        im = im.transpose(Image.Transpose.ROTATE_270)
    elif orientation != 'h':
        raise ValueError(orientation)
    return im, 'foliage'


def _bones(sick=False):
    im, d = canvas()
    d.line([(3,12),(10,12)], fill=2)
    # A low connected rib group. It no longer resembles a white pickup icon.
    d.arc((3,5,11,13), 175, 345, fill=4, width=2)
    d.arc((3,4,11,12), 175, 345, fill=6)
    d.line([(5,7),(5,10)], fill=5)
    d.line([(8,6),(8,10)], fill=5)
    d.line([(10,7),(10,9)], fill=5)
    d.line([(4,6),(6,5)], fill=7)
    if sick:
        d.line([(8,9),(10,10),(10,12)], fill=3)
    return im, 'forest_obj_stone'


def _fence():
    im, d = canvas()
    # No borrowed rectangular grass color: the local floor supplies all gaps.
    for x, top in ((1,2),(11,1)):
        d.rectangle((x,top,x+3,15), fill=8)
        d.line([(x+1,top+1),(x+1,14)], fill=10)
        d.line([(x+2,top+1),(x+2,top+4)], fill=11)
    d.polygon([(0,6),(15,5),(15,8),(0,9)], fill=8)
    d.line([(0,6),(7,6),(12,5),(15,5)], fill=10)
    d.line([(1,9),(14,8)], fill=1)
    return im, 'foliage'


def _stonework(name):
    im, d = canvas()
    _contact(d, 0, 15, 14)
    if name == 'statue':
        d.polygon([(3,13),(5,8),(4,4),(6,1),(10,1),(12,4),(11,8),(13,13)], fill=1)
        d.polygon([(5,12),(6,8),(5,4),(7,2),(9,2),(10,4),(9,8),(11,12)], fill=4)
        d.line([(6,5),(7,2),(8,2)], fill=6)
        d.line([(6,7),(8,8),(10,7)], fill=3)
        d.polygon([(1,12),(13,12),(15,14),(2,15),(0,14)], fill=3)
        d.line([(2,12),(11,12)], fill=6)
        d.line([(7,4),(7,6)], fill=7)
    elif name == 'pillar':
        d.polygon([(2,3),(5,1),(8,2),(10,0),(13,2),(13,13),(15,14),(14,15),(1,15),(0,14),(2,12)], fill=1)
        d.rectangle((3,3,12,12), fill=4)
        d.line([(3,3),(3,11)], fill=6)
        d.line([(6,3),(11,3)], fill=5)
        d.line([(8,5),(7,8),(9,10)], fill=3)
        d.line([(2,13),(12,13)], fill=5)
        d.line([(4,14),(13,14)], fill=3)
    else:
        d.polygon([(0,4),(3,2),(6,3),(8,1),(13,2),(15,4),(15,14),(0,14)], fill=2)
        d.polygon([(0,4),(4,3),(7,4),(9,2),(13,3),(15,5),(15,8),(0,8)], fill=5)
        d.line([(1,4),(4,3),(6,4)], fill=6)
        d.rectangle((0,8,15,12), fill=4)
        d.line([(0,9),(15,9)], fill=3)
        d.line([(6,4),(6,7)], fill=3)
        d.line([(10,10),(10,12)], fill=2)
        d.line([(0,13),(15,13)], fill=2)
        d.line([(1,11),(3,11)], fill=5)
    return im, 'forest_obj_stone'


def _thorns():
    im, d = canvas()
    d.polygon([(1,12),(4,8),(2,3),(5,2),(8,6),(12,1),(14,3),(11,8),(15,12),(12,15),(7,13),(2,15)], fill=8)
    for points in ([(2,14),(5,10),(4,5)], [(5,11),(9,8),(12,3)], [(8,13),(11,10),(14,12)]):
        d.line(points, fill=9, width=3)
        d.line([(x-1,y) for x,y in points], fill=10)
    for points in ([(4,8),(2,7),(3,10)],[(8,8),(8,5),(6,7)],[(11,10),(13,8),(13,11)]):
        d.polygon(points, fill=11)
    d.line([(3,13),(6,11),(9,11),(11,8)], fill=5, width=3)
    d.line([(3,13),(6,11),(9,11),(11,8)], fill=13)
    d.point((7,11), fill=7)
    d.line([(2,15),(5,14)], fill=12)
    return im, 'blight'


def _crack():
    im, d = canvas()
    d.polygon([(0,6),(3,2),(9,1),(13,3),(15,7),(15,13),(12,15),(2,15),(0,12)], fill=1)
    d.polygon([(1,6),(4,3),(9,2),(12,4),(14,7),(13,12),(10,14),(3,13),(1,11)], fill=4)
    d.polygon([(2,6),(5,3),(9,3),(11,5),(8,8),(3,9)], fill=6)
    d.line([(3,5),(5,3),(8,3)], fill=7)
    fracture = [(9,2),(8,6),(10,8),(7,10),(8,14)]
    d.line(fracture, fill=1, width=2)
    d.line([(8,6),(4,6),(3,9)], fill=1)
    d.line([(10,8),(13,9)], fill=1)
    d.line([(7,3),(7,5)], fill=8)
    d.line([(6,10),(6,12)], fill=7)
    return im, 'forest_obj_stone'


def _web():
    im, d = canvas()
    # Connected stretched silk: the supports are secondary, the light net is
    # one clear burnable sheet, with large open windows revealing local floor.
    for p in ([(0,2),(2,1),(3,4)], [(13,1),(14,3),(15,2)], [(0,13),(2,12),(3,15)], [(13,14),(14,12),(15,14)]):
        d.line(p, fill=3, width=2)
    hub = (8,8)
    for p in ((1,2),(7,0),(14,2),(15,9),(13,14),(6,15),(1,13),(0,7)):
        d.line([p,hub], fill=6)
    d.line([(3,4),(7,3),(12,4),(13,8),(11,12),(6,13),(3,11),(2,7),(3,4)], fill=7)
    d.line([(5,6),(8,5),(11,6),(11,9),(9,11),(6,10),(5,8),(5,6)], fill=6)
    d.line([(3,4),(7,3),(10,4)], fill=8)
    d.line([(5,6),(8,5)], fill=8)
    return im, 'forest_obj_stone'


def _lock():
    im, d = canvas()
    # The real forest gate has one shared16x32 keylock OBJ across its paired
    # cells. This BG frame deliberately has no duplicate tiny keyholes.
    for x in (1,12):
        d.rectangle((x,1,x+2,15), fill=8)
        d.line([(x,2),(x,13)], fill=10)
        d.line([(x+1,2),(x+1,6)], fill=11)
    for top in (3,10):
        d.rectangle((0,top,15,top+3), fill=8)
        d.line([(0,top),(14,top)], fill=10)
        d.line([(2,top+1),(11,top+1)], fill=9)
    d.line([(3,12),(12,5)], fill=8, width=3)
    d.line([(3,11),(11,5)], fill=10)
    return im, 'foliage'


def _plate(down=False):
    im, d = canvas()
    d.polygon([(0,7),(3,4),(12,4),(15,7),(14,14),(2,15),(0,13)], fill=1)
    d.polygon([(1,8),(4,5),(11,5),(14,8),(13,13),(3,14),(1,12)], fill=3)
    top = 6 if down else 2
    d.polygon([(2,top+3),(5,top),(11,top),(14,top+3),(12,top+7),(5,top+8),(2,top+6)], fill=4 if down else 6)
    d.line([(3,top+2),(5,top),(10,top)], fill=5 if down else 8)
    d.line([(3,top+7),(7,top+8),(12,top+7)], fill=2 if down else 4)
    if down:
        d.line([(5,12),(10,12)], fill=13)
        d.point((6,12), fill=14)
    return im, 'forest_obj_stone'


def _lantern(phase=0, censer=False, lit=True):
    im, d = canvas()
    if censer:
        _contact(d, 2, 13, 14)
        d.polygon([(3,10),(12,10),(11,13),(9,14),(5,14)], fill=2)
        d.line([(3,10),(12,10)], fill=11)
        d.line([(4,11),(10,12)], fill=12)
        d.line([(7,13),(7,15)], fill=4)
        if lit:
            d.polygon([(6,10),(4,7),(6,4),(7,1+phase%2),(9,5),(11,7),(10,10)], fill=12)
            d.polygon([(6,9),(6,6),(8,3+phase%2),(9,7),(9,9)], fill=14)
            d.line([(7,8),(7,6)], fill=15)
        return im, 'forest_obj_stone'
    d.line([(3,14),(3,2),(8,2),(9,4)], fill=2, width=3)
    d.line([(2,13),(2,2),(7,2)], fill=10)
    d.line([(4,14),(5,15)], fill=3)
    d.polygon([(7,5),(9,4),(12,5),(14,7),(13,12),(8,12),(7,10)], fill=2)
    d.polygon([(8,6),(11,5),(13,7),(12,10),(9,10),(8,9)], fill=12)
    d.line([(9,6),(9,9)], fill=15)
    d.line([(10,6),(11,6)], fill=14 if phase%2 else 15)
    d.line([(8,12),(12,12)], fill=10)
    _contact(d, 1, 7, 14, 2)
    return im, 'forest_obj_stone'


def _fungus():
    im, d = canvas()
    # Keep the engine's existing crystal ID, but show rooted fungal shelves.
    d.polygon([(1,12),(4,8),(6,9),(9,5),(12,7),(14,12),(12,15),(4,15)], fill=8)
    for x,y,h in ((4,13,5),(8,14,10),(12,13,6)):
        d.line([(x,y),(x,y-h+2)], fill=9, width=2)
        d.polygon([(x-3,y-h+3),(x-2,y-h+1),(x+1,y-h),(x+3,y-h+2),(x+3,y-h+3)], fill=5)
        d.line([(x-2,y-h+1),(x+1,y-h),(x+2,y-h+1)], fill=13)
        d.point((x,y-h+1), fill=7)
    d.line([(2,14),(5,13)], fill=12)
    return im, 'blight'


def _shrine_pad():
    im, d = canvas()
    d.polygon([(1,8),(4,5),(11,5),(15,8),(13,13),(9,15),(3,14),(0,11)], fill=2)
    d.polygon([(2,8),(5,6),(11,6),(13,8),(12,11),(8,13),(3,12)], fill=4)
    d.line([(3,7),(6,6),(10,6)], fill=6)
    d.line([(3,11),(6,12),(10,12)], fill=3)
    d.line([(6,8),(7,10),(10,8)], fill=11)
    return im, 'forest_obj_stone'


def _spring(phase=0):
    im, d = canvas()
    d.polygon([(0,7),(3,3),(11,3),(15,6),(15,12),(11,15),(3,15),(0,12)], fill=2)
    d.polygon([(1,7),(4,4),(10,4),(14,7),(13,11),(10,13),(4,13),(1,11)], fill=4)
    d.line([(2,6),(5,4),(10,4)], fill=6)
    d.polygon([(3,7),(6,6),(11,7),(12,10),(9,12),(5,11),(3,9)], fill=2)
    d.line([(4+phase%2,8),(8+phase%2,8)], fill=7)
    d.line([(7-phase%2,10),(10-phase%2,10)], fill=5)
    return im, 'forest_obj_stone'


def _mouth(style):
    im, d = canvas()
    if style == 'cave':
        d.polygon([(0,9),(3,3),(6,1),(11,2),(15,7),(15,15),(0,15)], fill=2)
        d.line([(1,8),(4,3),(7,2),(10,3)], fill=6)
        d.polygon([(3,15),(3,8),(6,5),(10,5),(13,9),(13,15)], fill=1)
        return im, 'forest_obj_stone'
    d.polygon([(0,8),(3,2),(8,0),(13,3),(15,9),(15,15),(0,15)], fill=8 if style == 'hollow' else 2)
    d.polygon([(3,15),(3,8),(6,4),(10,4),(13,8),(13,15)], fill=1)
    if style == 'hollow':
        d.line([(2,8),(4,3),(7,2)], fill=10)
        d.line([(12,4),(14,9),(14,13)], fill=9)
    else:
        d.line([(2,7),(4,3),(7,1)], fill=5)
        d.line([(12,3),(14,7)], fill=6)
    return im, 'foliage'


def _chest_tile(opened=False):
    im, d = canvas()
    _contact(d, 0, 15, 14)
    d.polygon([(1,7),(14,7),(14,13),(12,15),(3,15),(1,13)], fill=1)
    d.rectangle((2,8,13,12), fill=4)
    d.line([(2,12),(12,13)], fill=3)
    if opened:
        d.rectangle((2,2,13,7), fill=2)
        d.line([(2,2),(13,2),(13,7)], fill=5)
        d.rectangle((3,7,12,10), fill=1)
    else:
        d.polygon([(1,7),(2,3),(5,1),(11,1),(14,4),(14,8)], fill=5)
        d.line([(3,3),(5,2),(10,2)], fill=6)
        d.line([(2,8),(13,8)], fill=2)
    d.line([(4,3),(4,12)], fill=7)
    d.line([(11,3),(11,12)], fill=7)
    d.rectangle((7,8,9,10), fill=9)
    d.point((7,8), fill=11)
    return im, 'gold'


@lru_cache(None)
def paint_tile(name, phase=0, variant=1):
    if name not in TILE_NAMES:
        raise KeyError(name)
    if name in RETAINED_TILE_NAMES:
        image, bank = BASE.paint_tile(name, phase, 1)
        return image.copy(), bank
    if name in ('hlog_0','hlog_1','log'):
        image, bank = log_group()
        x = 16 if name == 'hlog_1' else 0
        return image.crop((x,0,x+16,16)), bank
    if name in ('rock','rock2','rock3','mossy_stone','sick_rock','cave_prop'):
        return _rock(name)
    if name in ('stump','sick_stump','hollow_prop','thicket_prop'):
        return _stump(name == 'sick_stump')
    if name in ('bones','sick_bones'):
        return _bones(name == 'sick_bones')
    if name == 'fence':
        return _fence()
    if name in ('pillar','ruin_wall','statue'):
        return _stonework(name)
    if name == 'thorn':
        return _thorns()
    if name == 'crack':
        return _crack()
    if name == 'web':
        return _web()
    if name == 'door_locked':
        return _lock()
    if name in ('myst_switch','myst_switch_down'):
        return _plate(name.endswith('_down'))
    if name in ('torch','torch_lit'):
        return _lantern(phase, censer=True, lit=name.endswith('_lit'))
    if name == 'lantern_post':
        return _lantern(phase)
    if name == 'blight_crystal':
        return _fungus()
    if name == 'shrine_plate':
        return _shrine_pad()
    if name in ('myst_spring','cave_spring','hollow_spring','thicket_spring'):
        return _spring(phase)
    if name.startswith('mouth_'):
        return _mouth(name.split('_')[1])
    if name in ('chest','chest_open','myst_chest','myst_chest_open'):
        return _chest_tile(name.endswith('_open'))
    if name == 'stairs_down':
        im, d = canvas()
        d.polygon([(1,5),(4,2),(12,2),(15,5),(14,14),(1,14)],fill=2)
        d.polygon([(3,6),(5,4),(11,4),(13,6),(12,13),(3,13)],fill=1)
        for x,y,length in ((4,6,8),(5,9,7),(6,12,6)):
            d.line([(x,y),(x+length-1,y)],fill=5)
            d.point((x,y),fill=6)
        return im, 'forest_obj_stone'
    raise AssertionError(('uncovered forest prop', name))


def validate():
    import json
    from pathlib import Path
    specs = {m['name']:m for m in json.loads(Path(__file__).with_name('reboot_contracts.json').read_text())['tiles']}
    native = 0
    for name in sorted(TILE_NAMES):
        for phase in range(specs[name]['frames']):
            image, _ = paint_tile(name, phase)
            assert image.mode == 'P' and image.size == (16,16)
            assert set(image.tobytes()) <= set(range(16))
            native += 1
    carried = []
    for tile, frame in (('bush','bush'),('rock_small','rock'),('boulder','boulder'),('myst_pot','pot')):
        bg, _ = paint_tile(tile)
        obj, _ = paint_frame('lift',frame)
        assert bg.tobytes() == obj.tobytes(), (tile, 'carry identity changed')
        carried.append(tile)
    return {'native_prop_frames':native, 'redrawn_tile_ids':len(OWNED_TILE_NAMES),
            'retained_tile_ids':sorted(RETAINED_TILE_NAMES), 'exact_carry_pairs':carried,
            'shared_OBJ_frames':'unchanged accepted source', 'extra_palette_banks':0}
