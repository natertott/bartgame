"""Native forest material kit for the composed-room refinement.

One quiet ground vocabulary, shared earth across living/sick grass, transparent
water-bank edges, and restrained horizontal surface motion. Approved compact
tree pictures remain in forest_tree_study; old canopy pictures stay retired.
"""
from functools import lru_cache
from PIL import Image, ImageDraw
import forest_trees_terrain as PREVIOUS
import forest_concepts_v2_terrain as BASE
import forest_tree_study as TREES

BANKS = BASE.BANKS
supports = BASE.supports
owns = PREVIOUS.owns


def palette(name, variant=1):
    if name == TREES.PALETTE_NAME:
        return TREES.palette()
    colors = BASE.palette(name, 1)
    if name == 'water':
        # The reservoir is blue-green, with short silver/green reflections.
        colors[2:9] = ['#183038', '#204850', '#306068', '#487880',
                       '#78a8a8', '#b0c8c0', '#d8e0c8']
        # Exterior pixels are transparent. These living greens are used only
        # by lily pads, not as a baked green rectangle around every bank.
        colors[9:12] = BASE.palette('ground', 1)[3:6]
    elif name == 'decay_mix':
        # Match the ground bank's earth positions exactly. All path stages
        # share native indices/pixel payloads and only their grass changes.
        colors[5:7] = ['#606048', '#788060']
        colors[7:12] = BASE.palette('ground', 1)[7:12]
        colors[12] = BASE.palette('ground', 1)[4]
    return list(colors)


def extra_palettes(variant=1):
    return {TREES.PALETTE_NAME: TREES.palette()}


def _new(w=16, h=16, fill=0):
    image = Image.new('P', (w, h), fill)
    return image, ImageDraw.Draw(image)


def _ground(n=0, sick=False, root=False):
    image, d = _new(fill=4)
    # Few connected, horizontal leaf/soil marks. These source variants are
    # selected spatially by the generator; no every-tile V-shaped glyph.
    if n % 4 == 1:
        d.line([(3, 10), (5, 9), (7, 10)], fill=3)
        d.line([(4, 11), (6, 11)], fill=5)
    elif n % 4 == 2:
        d.line([(10, 5), (12, 4), (13, 5)], fill=3)
        d.line([(10, 6), (12, 6)], fill=5)
    elif n % 4 == 3:
        d.line([(5, 12), (8, 11), (10, 12)], fill=3)
    if root:
        d.line([(1, 13), (4, 11), (8, 12)], fill=7)
        d.line([(2, 13), (4, 12), (6, 12)], fill=8)
        if sick and n % 3 == 0:
            d.line([(3, 12), (5, 11), (7, 12)], fill=13)
            d.point((5, 11), fill=14)
    return image


def _edge_mask(mask, corners):
    """Quarter-local soil/grass boundaries shared by all path orientations."""
    result = Image.new('1', (16, 16), 0)
    px = result.load()
    # Two to four native pixels of uneven living fringe; connected surfaces
    # do not acquire an outline at an internal metatile seam.
    depth = (3, 3, 2, 2, 3, 2, 3, 3)
    for y in range(16):
        for x in range(16):
            west, north = x < 8, y < 8
            sx, sy = (x if west else 15-x), (y if north else 15-y)
            horizontal = bool(mask & (8 if west else 2))
            vertical = bool(mask & (1 if north else 4))
            cb = 1 if west and north else 2 if north else 8 if west else 4
            fringe = (horizontal and sx < depth[y & 7]) or (vertical and sy < depth[x & 7])
            if horizontal and vertical and sx < 5 and sy < 5:
                fringe = fringe or sx + sy < 7
            if not horizontal and not vertical and corners & cb:
                fringe = sx + sy < 3
            px[x, y] = int(fringe)
    return result


def path_adjacency(mask, corners=0, sick=False):
    """Same native pixels in ground/decay_mix; index4 is the local grass."""
    fringe = _edge_mask(mask, corners)
    fp = fringe.load()
    image, d = _new(fill=9)
    p = image.load()
    for y in range(16):
        for x in range(16):
            if not fp[x, y]:
                continue
            p[x, y] = 4
            # A few attached grass lips describe contact without a heavy
            # black/brown border or checkerboard dither along the path.
            if y < 15 and not fp[x, y+1] and x % 8 in (2, 3, 6):
                p[x, y] = 3
            if x < 15 and not fp[x+1, y] and y % 8 == 3:
                p[x, y] = 5
    return image, 'decay_mix' if sick else 'ground'


def _rot_edge(mask, corners):
    # Gray grass meets living ground through identical, irregular tufts.
    image = _ground(sick=True)
    fringe = _edge_mask(mask, corners)
    px, fp = image.load(), fringe.load()
    # decay_mix12 is the exact original living ground4 contact ink.
    for y in range(16):
        for x in range(16):
            if fp[x, y]:
                px[x, y] = 12
    return image


def _water(mask=0, corners=0, phase=0, kind='water'):
    if mask == 15:
        image, d = _new()
        # A shallow mud puddle is a low, uneven water shape; it does not use
        # four complete riverbanks squeezed into a sixteen-pixel square.
        d.polygon([(2, 8), (4, 5), (9, 4), (13, 6), (14, 10),
                   (11, 12), (6, 13), (2, 11)], fill=12)
        d.polygon([(3, 8), (5, 6), (9, 5), (12, 7), (13, 10),
                   (10, 11), (6, 12), (3, 10)], fill=2)
        d.polygon([(4, 8), (6, 7), (10, 6), (12, 8), (10, 10),
                   (6, 11), (4, 10)], fill=3)
        d.line([(5+phase % 2, 8), (8+phase % 2, 8)], fill=5)
        return image
    land = _edge_mask(mask, corners)
    lp = land.load()
    image, d = _new(fill=3)
    # Small, broad surface sheets rather than vertical roots or a repeated
    # white zig-zag cage. Each eight-pixel quarter remains independently
    # reusable by the 47 valid blob orientations.
    d.line([(1+phase % 2, 4), (4+phase % 2, 4), (6, 3)], fill=4)
    d.line([(10, 12), (13, 12), (14-phase % 2, 11)], fill=4)
    if phase % 2:
        d.line([(2, 5), (4, 5)], fill=5)
    else:
        d.line([(11, 13), (13, 13)], fill=5)
    p = image.load()
    for y in range(16):
        for x in range(16):
            if lp[x, y]:
                # Only a soil lip remains outside the surface. Farther
                # exterior alpha exposes the real floor layer, any stage.
                near = any(0 <= x+dx < 16 and 0 <= y+dy < 16 and not lp[x+dx, y+dy]
                           for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)))
                p[x, y] = (13 if y < 8 else 12) if near else 0
            elif any(0 <= x+dx < 16 and 0 <= y+dy < 16 and lp[x+dx, y+dy]
                     for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                p[x, y] = 2
    if kind == 'water_lily':
        d.polygon([(5, 10), (6, 8), (9, 8), (11, 10), (9, 12),
                   (6, 12), (5, 11), (8, 10)], fill=9)
        d.line([(6, 9), (8, 9)], fill=11)
    elif kind == 'water_foam':
        # Local fall/bridge foam is a short broken horizontal crest.
        d.line([(2, 8+phase % 2), (5, 8+phase % 2)], fill=6)
        d.line([(9, 9-phase % 2), (12, 9-phase % 2)], fill=5)
    return image


def _fall(phase=0):
    image, d = _new(fill=3)
    # One connected falling sheet with dark outer edges, broad inner light,
    # and a moving short crest. There are no detached branch-like strokes.
    d.rectangle((0, 0, 1, 15), fill=2)
    d.rectangle((14, 0, 15, 15), fill=2)
    d.rectangle((4, 0, 8, 15), fill=4)
    d.rectangle((5, 0, 6, 15), fill=5)
    for base in (-5, 3, 11):
        y = (base+phase*3) % 19-3
        d.line([(3, y), (6, y+1), (10, y)], fill=6)
    d.line([(2, 14), (5, 13), (8, 15), (11, 14), (13, 15)], fill=7)
    return image


def _bridge(vertical=False):
    image, d = _new(fill=9)
    # Attached side beams have a coherent light-facing plane and recess.
    # Plank ends stay open along the actual walking axis.
    if vertical:
        d.rectangle((0, 0, 2, 15), fill=8)
        d.rectangle((13, 0, 15, 15), fill=8)
        d.line((1, 0, 1, 15), fill=10)
        d.line((14, 0, 14, 15), fill=1)
        for y in (3, 7, 11, 15):
            d.line((3, y, 12, y), fill=8)
            if y < 15:
                d.line((3, y+1, 11, y+1), fill=10)
        d.line((5, 1, 8, 1), fill=11)
    else:
        d.rectangle((0, 0, 15, 2), fill=8)
        d.rectangle((0, 13, 15, 15), fill=8)
        d.line((0, 1, 15, 1), fill=10)
        d.line((0, 14, 15, 14), fill=1)
        for x in (3, 7, 11, 15):
            d.line((x, 3, x, 12), fill=8)
            if x < 15:
                d.line((x+1, 3, x+1, 11), fill=10)
        d.line((1, 5, 1, 8), fill=11)
    return image


def _ledge(name):
    image, d = _new(fill=4)
    d.rectangle((0, 4, 15, 12), fill=8)
    d.line([(0, 4), (4, 3), (7, 4), (12, 3), (15, 4)], fill=7)
    d.line([(0, 2), (4, 2), (7, 3), (11, 2), (15, 2)], fill=5)
    d.line([(0, 13), (4, 14), (8, 13), (12, 14), (15, 13)], fill=2)
    d.line([(3, 6), (5, 6), (5, 10)], fill=9)
    d.line([(11, 5), (10, 8), (12, 11)], fill=7)
    d.line([(1, 12), (6, 12), (10, 13), (14, 12)], fill=3)
    if name == 'ledge_s_w':
        d.polygon([(0, 0), (3, 0), (3, 4), (2, 7), (3, 11),
                   (2, 14), (0, 15)], fill=4)
    elif name == 'ledge_s_e':
        d.polygon([(15, 0), (12, 0), (12, 4), (13, 7), (12, 11),
                   (13, 14), (15, 15)], fill=4)
    elif name == 'ledge_n':
        # Reverse the land/face placement, keeping the small highlight on
        # the upper-left edge instead of simply flipping the lighting.
        image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        d = ImageDraw.Draw(image)
        d.line((0, 3, 15, 3), fill=7)
        d.line((1, 7, 4, 7), fill=9)
    return image


def _pit(inner=False):
    image, d = _new(fill=1)
    if not inner:
        # Soil above a real dark recess. No violet fill or light inner disk
        # to make a hole look like a crystal, water or a decorative button.
        d.line([(0, 0), (3, 1), (7, 0), (11, 1), (15, 0)], fill=9)
        d.line([(0, 1), (4, 2), (8, 1), (12, 2), (15, 1)], fill=7)
        d.line([(2, 2), (5, 2), (7, 3)], fill=8)
    return image


def _vegetation(name):
    image, d = _new(fill=4)
    if name in ('moss_flowers', 'moss_flowers2'):
        points = ((5, 9), (9, 7)) if name.endswith('2') else ((9, 9), (12, 7))
        for x, y in points:
            d.line((x, y, x, y+3), fill=3)
            d.line([(x-1, y), (x, y-1), (x+1, y)], fill=14)
            d.point((x, y), fill=15)
        d.line((6, 12, 9, 12), fill=3)
    elif name == 'leaf_litter':
        d.polygon([(4, 10), (6, 8), (9, 9), (11, 8), (12, 10),
                   (8, 12), (5, 12)], fill=8)
        d.line([(5, 10), (8, 10), (9, 9)], fill=10)
        d.line([(8, 12), (10, 11)], fill=7)
    else:
        # Connected low rosettes; a horizontal leaf shelf gives volume
        # without the old three tall vertical scratches per tile.
        d.polygon([(1, 12), (3, 9), (7, 10), (9, 8), (13, 10),
                   (15, 13), (12, 15), (5, 15)], fill=3)
        leaves = [[(7, 13), (3, 11), (2, 8), (5, 9)],
                  [(7, 12), (5, 8), (7, 5), (9, 8)],
                  [(9, 13), (10, 9), (14, 8), (13, 11)],
                  [(6, 14), (3, 13), (2, 11), (6, 12)]]
        if name == 'fern_patch':
            leaves = [[(8, 13), (3, 9), (2, 6), (6, 8)],
                      [(8, 12), (7, 6), (9, 3), (10, 8)],
                      [(8, 13), (12, 8), (15, 7), (13, 11)]]
        for points in leaves:
            d.polygon(points, fill=5)
            d.line(points[:2], fill=3)
    return image


def _group(kind):
    width = 48 if kind == 'meadow' else 32
    image, d = _new(width, width, fill=4)
    if kind == 'meadow':
        # Flowers live along one low crescent of grass, not a regular nine
        # tile decoration stamp. The center remains calm walking ground.
        for x, y in ((5, 32), (10, 36), (16, 34), (30, 12), (36, 17)):
            d.line([(x-2, y+2), (x, y), (x+2, y+2)], fill=3)
            d.point((x, y-1), fill=14)
            d.line((x, y, x, y+2), fill=5)
    elif kind == 'clover':
        for x, y in ((9, 16), (14, 11), (19, 17), (14, 21)):
            d.polygon([(x-4, y), (x-2, y-3), (x, y-2), (x+2, y-3),
                       (x+4, y), (x+1, y+2), (x, y+5), (x-2, y+2)], fill=3)
            d.line([(x-2, y-1), (x, y), (x+2, y-1)], fill=5)
    else:
        for x, y, w in ((9, 13, 4), (15, 20, 5), (22, 15, 3)):
            d.line((x, y, x, y+4), fill=14)
            d.line((x-1, y+4, x+2, y+4), fill=3)
            d.polygon([(x-w, y), (x-w+1, y-2), (x-1, y-3),
                       (x+w-1, y-2), (x+w, y), (x+w-1, y+1),
                       (x-w+1, y+1)], fill=8)
            d.line([(x-w+1, y-1), (x, y-2), (x+w-2, y-1)], fill=11)
    return image


@lru_cache(None)
def _paint(name, phase):
    if owns(name):
        return Image.new('P', (16, 16), 0), TREES.PALETTE_NAME
    if name in ('moss0', 'moss1', 'moss2', 'moss_shade'):
        n = int(name[-1]) if name[-1].isdigit() else 3
        return _ground(n), 'ground'
    if name in ('path', 'path_edge_n'):
        return path_adjacency(1 if name.endswith('_n') else 0)
    if name.startswith(('pedge_', 'verge_', 'shore_')):
        family, code = name.split('_', 1)
        corner = code.startswith('c') and len(code) > 1
        mask = int(code[1:] if corner else code, 16)
        if family == 'pedge':
            return path_adjacency(0 if corner else mask, mask if corner else 0)
        return _ground(0), 'ground'
    if name.startswith('rot_'):
        return _rot_edge(int(name[4], 16), int(name[5], 16)), 'decay_mix'
    if name.startswith(('forest_rot', 'blight_ground', 'forest_blight_vein')) or name in (
            'moss_blight', 'moss_blight2', 'blight_floor', 'blight_floor2', 'blight_vein'):
        n = int(name[-1]) if name[-1].isdigit() else 0
        return _ground(n, sick=True, root='vein' in name), 'decay_mix'
    if name in ('moss_flowers', 'moss_flowers2', 'leaf_litter', 'tall_grass', 'fern_patch'):
        return _vegetation(name), 'ground'
    for prefix, columns, kind in (('meadow_', 3, 'meadow'), ('clover_', 2, 'clover'),
                                  ('shroomring_', 2, 'shroomring')):
        if name.startswith(prefix):
            n = int(name[len(prefix):]); group = _group(kind)
            x, y = n % columns*16, n // columns*16
            return group.crop((x, y, x+16, y+16)), 'ground'
    if name == 'waterfall':
        return _fall(phase), 'water'
    if name in ('water_lily', 'water_foam'):
        return _water(phase=phase, kind=name), 'water'
    if name == 'water' or name.startswith('water_'):
        code = name[6:] if name != 'water' else '0'
        corner = code.startswith('c') and len(code) > 1
        mask = int(code[1:] if corner else code, 16)
        return _water(0 if corner else mask, mask if corner else 0, phase), 'water'
    if name in ('bridge', 'bridge_v'):
        return _bridge(name.endswith('_v')), 'foliage'
    if name in ('ledge_s', 'ledge_s_w', 'ledge_s_e', 'ledge_n'):
        return _ledge(name), 'ground'
    if name in ('pit', 'pit_inner', 'forest_blight_pit'):
        return _pit(name == 'pit_inner'), 'ground'
    if name == 'blight_mist':
        image, d = _new()
        d.line([(2, 12), (5, 11), (8, 12)], fill=5)
        if phase % 2:
            d.line([(9, 11), (12, 10)], fill=13)
        return image, 'blight'
    if name == 'blight_pool':
        image = _water(15, phase=phase)
        return image, 'rot_water'
    return PREVIOUS.paint(name, phase, 1)


def paint(name, phase=0, variant=1):
    image, bank = _paint(name, int(phase))
    assert image.mode == 'P' and image.size == (16, 16), name
    assert set(image.tobytes()) <= set(range(16)), name
    return image.copy(), bank


def paint_adjacency(parent, mask, corners=0, phase=0, variant=1, quadrant=None):
    if owns(parent.split('@q')[0]):
        return Image.new('P', (16, 16), 0), TREES.PALETTE_NAME
    if parent.startswith('water'):
        return _water(mask, corners, phase, parent), 'water'
    return paint(parent, phase, variant)


def fringe(parent, mask, variant=1):
    return Image.new('P', (16, 16), 0), TREES.PALETTE_NAME


def arch_group(variant=1):
    return BASE.arch_group(1)


def pulse_palettes(variant=1):
    return BASE.pulse_palettes(1)
