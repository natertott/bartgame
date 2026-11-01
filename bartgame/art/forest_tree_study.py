"""Native repeated trees: two footprints, two forms, three structural states.

The current request deliberately sets large canopy work aside. These trees
start on their final 32x32 or 16x32 indexed canvases and share one RGB555 bank.
Index zero is transparent; the background is supplied by the real floor.
"""
from functools import lru_cache
from PIL import Image, ImageDraw

PALETTE_NAME = 'forest_tree_study'
PALETTE = [
    '#000000', '#183028', '#283828', '#403830',
    '#786048', '#b0a078', '#204830', '#487840',
    '#80a850', '#b0c878', '#505030', '#889050',
    '#b8b078', '#582078', '#b848e0', '#f0d8f0',
]
STATES = ('healthy', 'sick', 'dead')
SIZES = {'broad': (32, 32), 'narrow': (16, 32)}
VARIETIES = {'broad': ('Round oak', 'Crooked oak'),
             'narrow': ('Small poplar', 'Forked birch')}
GREEN_INDICES = (6, 7, 8, 9)
SICK_INDICES = (10, 11, 12)
WOOD_INDICES = (3, 4, 5)
GLOW_INDICES = (13, 14, 15)


def palette(name=None):
    if name not in (None, PALETTE_NAME):
        raise KeyError(name)
    return list(PALETTE)


def _new(w, h=32):
    im = Image.new('P', (w, h), 0)
    colors = [int(c[k:k+2], 16) for c in PALETTE for k in (1, 3, 5)]
    im.putpalette(colors + [0] * (768-len(colors)))
    im.info['transparency'] = 0
    return im


def _contact(d, x, broad):
    # A narrow native ground shadow, never a box of borrowed floor color.
    span = 7 if broad else 4
    d.line([(x-span+2, 29), (x+span-1, 29)], fill=2, width=2)
    d.line([(x-span+4, 30), (x+span-3, 30)], fill=2)
    d.line([(x-2, 28), (x-5, 30)], fill=3)
    d.line([(x+1, 28), (x+4, 29)], fill=3)


def _limb(d, points, width=3, pale=False):
    """One connected woody mass with an upper-left light-facing strip."""
    d.line(points, fill=1, width=width+2)
    d.line(points, fill=3, width=width)
    if width > 2:
        d.line([(x-1, y) for x, y in points], fill=4, width=max(1, width-1))
    else:
        d.line(points[:-1], fill=4, width=1)
    if pale:
        d.line([(x-1, y) for x, y in points[:2]], fill=5, width=1)


def _wound(d, points):
    # Attached infection is small enough to leave the wood readable.
    d.line(points, fill=13, width=3)
    d.line(points, fill=14, width=1)
    if len(points) > 1:
        x, y = points[1]
        d.point((x, y), fill=15)


def _broad_round(state):
    im = _new(32); d = ImageDraw.Draw(im)
    _contact(d, 16, True)
    if state == 'dead':
        _limb(d, [(16,29), (14,22), (15,15), (13,8), (15,3)], 4, True)
        _limb(d, [(15,19), (9,16), (5,10), (5,7)], 3, True)
        _limb(d, [(10,16), (5,16), (3,13)], 2)
        _limb(d, [(15,16), (22,11), (25,5)], 3, True)
        _limb(d, [(21,12), (27,12), (29,8)], 2)
        d.line([(14,3), (17,3)], fill=5)
        d.line([(24,5), (26,6)], fill=5)
        d.line([(5,7), (7,8)], fill=5)
        _wound(d, [(15,24), (14,20), (16,16)])
        return im
    _limb(d, [(16,29), (15,22), (17,15)], 5)
    if state == 'healthy':
        # Three unequal interlocking lobes: high rear, low left, small right.
        d.polygon([(3,11),(5,11),(5,7),(9,7),(9,4),(12,4),(12,1),
                   (18,1),(18,2),(22,2),(22,5),(25,5),(25,8),(28,8),
                   (28,10),(30,10),(30,16),(29,16),(29,20),(26,20),
                   (26,23),(21,23),(21,25),(17,25),(17,23),(14,23),
                   (14,25),(9,25),(9,23),(5,23),(5,21),(2,21),
                   (2,17),(1,17),(1,13),(3,13)], fill=1)
        d.polygon([(4,11),(6,8),(10,8),(10,5),(13,5),(13,2),(18,2),
                   (21,4),(21,6),(25,7),(27,10),(29,12),(28,18),
                   (25,22),(21,22),(20,24),(18,23),(16,21),(13,23),
                   (10,24),(7,22),(4,20),(2,16)], fill=6)
        # Rear lobe's light top and the front lobe's separate light plane.
        d.polygon([(11,6),(14,3),(18,3),(21,5),(22,8),(19,11),
                   (16,12),(12,10),(9,10)], fill=7)
        d.polygon([(13,6),(15,4),(18,4),(19,6),(17,8),(14,8)], fill=8)
        d.line([(15,5),(17,5)], fill=9)
        d.polygon([(4,13),(7,10),(11,10),(14,12),(16,15),(15,19),
                   (12,22),(8,21),(5,19),(3,16)], fill=7)
        d.polygon([(6,12),(9,11),(12,12),(13,14),(10,16),(7,15),
                   (5,16),(4,14)], fill=8)
        d.line([(7,12),(9,12)], fill=9)
        d.polygon([(19,12),(23,9),(26,10),(28,13),(27,16),(24,18),
                   (21,18),(18,16)], fill=7)
        d.polygon([(21,12),(24,11),(26,12),(25,14),(22,15),(20,14)], fill=8)
        # A handful of leaf-lip notches, not an all-over fan texture.
        d.line([(6,19),(8,20),(10,19)], fill=6)
        d.line([(22,18),(24,19),(26,18)], fill=6)
        d.line([(13,24),(15,22),(16,24)], fill=3)
    else:
        # Missing right crown reveals the matching branch; wilt changes shape.
        _limb(d, [(16,22),(21,16),(26,14),(28,10)], 3)
        d.line([(27,10),(29,11)], fill=5)
        d.polygon([(3,10),(5,6),(10,5),(12,2),(19,2),(22,6),(22,11),
                   (20,15),(17,17),(17,22),(14,23),(11,20),(7,20),
                   (4,18),(2,14)], fill=1)
        d.polygon([(4,10),(6,7),(11,6),(13,3),(18,3),(21,7),(20,12),
                   (17,15),(15,20),(12,19),(9,18),(5,17),(3,14)], fill=10)
        d.polygon([(5,10),(9,7),(13,5),(17,5),(19,8),(17,12),(13,13),
                   (11,17),(7,16),(5,14)], fill=11)
        d.polygon([(7,9),(12,6),(15,6),(16,8),(13,10),(10,10)], fill=12)
        d.polygon([(3,12),(6,10),(9,11),(9,14),(6,16),(4,14)], fill=7)
        d.line([(5,12),(7,11)], fill=8)
        d.polygon([(20,18),(23,17),(25,19),(23,22),(21,23)], fill=10)
        d.line([(21,19),(23,19),(22,21)], fill=11)
        _wound(d, [(16,25),(15,21),(16,18)])
        d.line([(17,12),(18,14),(16,16)], fill=13)
        d.point((18,14), fill=14)
    return im


def _narrow_poplar(state):
    im = _new(16); d = ImageDraw.Draw(im)
    _contact(d, 8, False)
    if state == 'dead':
        _limb(d, [(8,29),(7,22),(9,15),(7,8),(9,2)], 3, True)
        _limb(d, [(8,21),(3,17),(3,12)], 2)
        _limb(d, [(9,16),(13,12),(13,7)], 2)
        _limb(d, [(7,10),(3,7),(3,4)], 2)
        d.line([(8,2),(10,3)], fill=5)
        d.point((13,7), fill=5)
        _wound(d, [(8,25),(7,22),(9,19)])
        return im
    _limb(d, [(8,29),(8,22),(7,17)], 3)
    if state == 'healthy':
        d.polygon([(6,1),(9,1),(9,3),(11,3),(11,6),(13,6),
                   (13,11),(12,12),(14,13),(14,19),(12,19),(12,23),
                   (9,23),(9,25),(6,25),(6,23),(3,23),(3,20),
                   (1,20),(1,13),(3,11),(3,8),(4,8),(4,4),(6,4)], fill=1)
        d.polygon([(6,4),(7,2),(9,3),(10,5),(10,7),(12,8),(12,11),
                   (10,13),(13,14),(13,18),(11,20),(11,22),(8,24),
                   (6,23),(5,21),(3,20),(2,17),(3,13),(5,11),
                   (4,9),(5,5)], fill=6)
        d.polygon([(6,5),(8,3),(9,5),(9,8),(11,9),(11,11),
                   (8,13),(5,12),(4,10),(5,8)], fill=7)
        d.polygon([(6,5),(8,4),(8,8),(6,10),(5,9)], fill=8)
        d.point((7,5), fill=9)
        d.polygon([(3,15),(6,13),(9,13),(10,16),(9,19),(6,21),
                   (4,19),(2,18)], fill=7)
        d.polygon([(4,15),(6,14),(8,15),(8,17),(5,18),(3,17)], fill=8)
        d.line([(5,15),(6,15)], fill=9)
        d.line([(10,17),(12,17)], fill=7)
        d.line([(5,21),(7,22),(9,21)], fill=6)
    else:
        _limb(d, [(8,24),(12,18),(13,12)], 2)
        d.line([(12,12),(14,13)], fill=5)
        d.polygon([(6,2),(10,2),(11,5),(11,9),(9,13),(9,17),
                   (7,21),(4,21),(3,18),(1,16),(2,11),(4,8),(4,5)], fill=1)
        d.polygon([(7,3),(9,3),(10,6),(9,10),(7,13),(8,17),
                   (6,20),(4,18),(2,15),(3,12),(5,9),(5,5)], fill=10)
        d.polygon([(7,4),(9,5),(8,9),(6,10),(5,13),(7,15),
                   (5,17),(3,15),(4,12),(6,8)], fill=11)
        d.line([(7,5),(8,6),(7,8)], fill=12)
        d.polygon([(9,19),(12,19),(13,21),(11,24),(9,23)], fill=7)
        d.line([(10,20),(11,20)], fill=8)
        _wound(d, [(8,25),(8,22),(10,19)])
    return im


def _broad_crooked(state):
    im = _new(32); d = ImageDraw.Draw(im)
    _contact(d, 16, True)
    _limb(d, [(16,29),(19,23),(18,16),(21,10)], 4, state == 'dead')
    if state == 'dead':
        _limb(d, [(19,18),(17,12),(19,7),(18,2)], 3, True)
        _limb(d, [(17,13),(9,10),(6,5)], 3, True)
        _limb(d, [(10,10),(5,11),(3,8)], 2)
        _limb(d, [(19,22),(27,17),(28,10)], 3, True)
        _limb(d, [(26,18),(29,18),(29,14)], 2)
        d.line([(17,2),(20,3)], fill=5)
        d.line([(5,5),(7,6)], fill=5)
        d.line([(27,10),(29,11)], fill=5)
        d.line([(16,26),(18,24)], fill=13)
        d.point((17,25), fill=14)
        return im
    _limb(d, [(18,22),(11,18),(7,14)], 3)
    if state == 'healthy':
        d.polygon([(3,8),(6,8),(6,4),(10,4),(10,2),(16,2),(16,3),
                   (20,3),(20,6),(23,6),(23,9),(27,9),(27,12),
                   (30,12),(30,18),(28,18),(28,21),(25,21),(25,24),
                   (21,24),(21,25),(17,25),(17,23),(11,23),(11,21),
                   (6,21),(6,19),(3,19),(3,16),(1,16),(1,11),(3,11)], fill=1)
        d.polygon([(4,9),(7,6),(11,3),(15,3),(19,5),(20,8),
                   (23,10),(27,11),(29,14),(28,19),(25,22),(22,24),
                   (18,23),(15,21),(11,22),(7,20),(4,18),(2,14)], fill=6)
        d.polygon([(5,9),(8,6),(12,4),(16,4),(18,6),(17,9),
                   (19,12),(16,16),(12,17),(8,15),(4,15),(3,12)], fill=7)
        d.polygon([(7,8),(11,5),(15,5),(15,7),(12,9),(9,9),
                   (7,12),(5,11)], fill=8)
        d.line([(10,6),(12,6)], fill=9)
        d.polygon([(19,15),(22,12),(26,12),(28,15),(26,19),(23,21),
                   (20,20),(17,18)], fill=7)
        d.polygon([(21,15),(24,13),(26,14),(25,17),(22,18),(20,17)], fill=8)
        d.line([(22,15),(24,14)], fill=9)
        d.line([(6,16),(9,17),(11,16)], fill=6)
        d.line([(22,21),(25,21)], fill=6)
        d.line([(17,24),(18,22),(20,24)], fill=3)
    else:
        # Bare upper fork and a low hanging lobe retain this tree's lean.
        _limb(d, [(18,17),(17,10),(19,5)], 3)
        d.line([(18,5),(20,6)], fill=5)
        d.polygon([(2,9),(5,6),(10,6),(13,8),(13,12),(11,15),
                   (10,18),(7,20),(4,18),(2,15),(1,12)], fill=1)
        d.polygon([(3,10),(6,7),(10,7),(12,10),(10,14),(8,17),
                   (6,18),(3,15),(2,12)], fill=10)
        d.polygon([(4,10),(7,8),(10,9),(10,11),(7,14),(5,15),(3,13)], fill=11)
        d.line([(6,10),(8,9)], fill=12)
        d.polygon([(20,14),(24,11),(28,12),(30,16),(28,20),(25,23),
                   (22,22),(19,19)], fill=1)
        d.polygon([(21,15),(25,12),(28,14),(29,17),(26,20),(24,22),
                   (22,20),(20,18)], fill=10)
        d.polygon([(23,14),(26,13),(28,15),(26,17),(24,18),(21,17)], fill=11)
        d.line([(24,14),(26,14)], fill=12)
        d.polygon([(6,7),(8,7),(10,9),(8,11),(5,10)], fill=7)
        d.line([(6,8),(8,8)], fill=8)
        _wound(d, [(18,25),(19,21),(18,18)])
        d.line([(24,19),(25,17),(27,16)], fill=13)
        d.point((25,17), fill=14)
    return im


def _narrow_birch(state):
    im = _new(16); d = ImageDraw.Draw(im)
    _contact(d, 8, False)
    _limb(d, [(8,29),(6,22),(7,15),(5,8)], 3, True)
    if state == 'dead':
        _limb(d, [(7,18),(8,11),(5,4),(6,1)], 2, True)
        _limb(d, [(7,24),(12,17),(11,10),(13,6)], 2, True)
        _limb(d, [(7,14),(3,11),(3,7)], 2)
        d.line([(5,2),(7,2)], fill=5)
        d.point((13,6), fill=5)
        d.line([(7,25),(8,23)], fill=13)
        d.point((7,24), fill=14)
        return im
    _limb(d, [(7,22),(11,17),(12,11)], 2, True)
    if state == 'healthy':
        d.polygon([(4,1),(8,1),(8,3),(10,3),(10,6),(12,6),(12,10),
                   (11,11),(14,12),(14,18),(13,18),(13,22),(10,22),
                   (10,24),(7,24),(7,22),(4,22),(4,20),(2,20),
                   (2,15),(1,15),(1,9),(2,9),(2,5),(4,5)], fill=1)
        d.polygon([(4,5),(5,2),(7,2),(9,5),(10,8),(10,11),(12,12),
                   (13,15),(12,19),(10,21),(9,23),(7,21),(5,20),
                   (3,18),(3,15),(2,12),(3,8)], fill=6)
        d.polygon([(4,6),(5,3),(7,3),(8,6),(9,8),(7,11),(6,14),
                   (3,13),(2,10),(3,8)], fill=7)
        d.polygon([(5,5),(6,4),(7,7),(6,10),(4,11),(4,8)], fill=8)
        d.point((6,5), fill=9)
        d.polygon([(7,14),(10,12),(12,14),(12,17),(10,20),(8,21),
                   (6,19),(5,17)], fill=7)
        d.polygon([(8,14),(10,13),(11,15),(10,17),(7,18),(7,16)], fill=8)
        d.line([(8,15),(9,14)], fill=9)
        d.line([(6,19),(8,20),(10,19)], fill=6)
    else:
        _limb(d, [(7,16),(9,9),(7,3)], 2, True)
        d.line([(6,3),(8,3)], fill=5)
        d.polygon([(2,6),(5,5),(7,8),(7,12),(5,15),(3,14),(1,11)], fill=1)
        d.polygon([(3,7),(5,6),(6,9),(5,12),(3,13),(2,10)], fill=10)
        d.line([(3,8),(4,7),(5,9),(4,11)], fill=11)
        d.point((4,8), fill=12)
        d.polygon([(10,14),(13,13),(14,16),(13,20),(11,23),
                   (9,22),(8,19)], fill=1)
        d.polygon([(10,15),(12,14),(13,17),(12,20),(10,22),(9,19)], fill=10)
        d.line([(10,16),(12,15),(12,18),(10,20)], fill=11)
        d.polygon([(2,9),(4,9),(5,11),(3,12),(2,11)], fill=7)
        _wound(d, [(7,25),(7,22),(9,19)])
    return im


@lru_cache(None)
def _tree(size, variety, state):
    if size not in SIZES or variety not in (0, 1) or state not in STATES:
        raise ValueError((size, variety, state))
    if size == 'broad':
        return _broad_crooked(state) if variety else _broad_round(state)
    return _narrow_birch(state) if variety else _narrow_poplar(state)


def tree(size='broad', variety=0, state='healthy'):
    return _tree(size, int(variety), state).copy()


def specs():
    return [{'name': f'tree_{size}_{variety}_{state}', 'size': size,
             'state': state, 'variety': variety,
             'variety_name': VARIETIES[size][variety],
             'size_pixels': list(SIZES[size]), 'w': SIZES[size][0], 'h': 32,
             'anchor': [SIZES[size][0]//2, 30],
             'palette': PALETTE_NAME, 'transparent_index': 0}
            for size in SIZES for variety in range(2) for state in STATES]


def prototype(path, variety=0):
    """SOURCE-only native and integer inspection on actual forest floor art."""
    import forest_concepts_v2_terrain as floor
    out = Image.new('RGB', (552, 300), '#13201c')
    d = ImageDraw.Draw(out)
    d.text((6, 5), 'SOURCE / native32x32 and16x32 / fixed shared RGB555 bank / 3x inspection', fill='#d8d0a8')
    def expand(v):
        return (v & 248) | (v >> 5)
    rgb = [tuple(expand(int(c[k:k+2],16)) for k in (1,3,5)) for c in PALETTE]
    for row, size in enumerate(SIZES):
        for col, state in enumerate(STATES):
            x, y = 6 + col*182, 30 + row*134
            d.text((x,y), f'{size}: {state}', fill='#d8d0a8')
            bg, bank = floor.paint('moss0' if state == 'healthy' else 'blight_floor', 0, 1)
            colors = floor.palette(bank,1)
            ground = Image.new('RGB',(176,104))
            for gy in range(104):
                for gx in range(176):
                    ink = bg.getpixel((gx%16,gy%16));c = colors[ink]
                    ground.putpixel((gx,gy),tuple(expand(int(c[k:k+2],16)) for k in (1,3,5)))
            pic = tree(size,variety,state); rgba = Image.new('RGBA',pic.size)
            rgba.putdata([(*rgb[v],255 if v else 0) for v in pic.tobytes()])
            ground.paste(rgba,(12,57),rgba)
            zoom = rgba.resize((pic.width*3,96),Image.Resampling.NEAREST)
            ground.paste(zoom,(65,4),zoom)
            out.paste(ground,(x,y+17))
    out.save(path)
