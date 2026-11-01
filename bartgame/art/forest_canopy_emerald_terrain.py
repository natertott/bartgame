"""Dense native foliage over real ground, with the existing forest context."""
from PIL import Image
import forest_canopy_emerald as A
import forest_concepts_v2_terrain as BASE
import forest_canopy_adaptive_terrain as CONTRACT
import forest_concepts_v2_topology as T

BANKS = BASE.BANKS
owns = CONTRACT.owns
supports = BASE.supports


def palette(name, variant=1):
    return A.stage_palette(variant, 3) if name == A.PALETTE_NAME else BASE.palette(name, 1)


def extra_palettes(variant=1):
    return A.extra_palettes(variant)


def paint(name, phase=0, variant=1):
    if not owns(name):
        return BASE.paint(name, phase, 1)
    if name in T.HEALTHY or name in T.BLIGHT or name in T.CONNECTORS:
        return A.quiet_fill(variant), A.PALETTE_NAME
    if name in CONTRACT._TREE:
        return CONTRACT._part(A.authored_tree(variant), CONTRACT._TREE.index(name)), A.PALETTE_NAME
    for prefix in ('tree2_', 'birch_', 'fir_', 'sicktree_', 'btree_'):
        if name.startswith(prefix):
            return CONTRACT._part(A.authored_tree(variant, second=prefix in ('tree2_', 'fir_')),
                                  int(name[len(prefix):])), A.PALETTE_NAME
    for prefix in ('gtree_', 'gtree2_'):
        if name.startswith(prefix):
            return CONTRACT._part(A.authored_tree(variant, large=True, second=prefix == 'gtree2_'),
                                  int(name[len(prefix):]), 3), A.PALETTE_NAME
    return A.prefab(variant, 'small'), A.PALETTE_NAME


def paint_adjacency(parent, mask, corners=0, phase=0, variant=1, quadrant=None):
    if not owns(parent.split('@q')[0]):
        return BASE.paint_adjacency(parent, mask, corners, phase, 1, quadrant)
    image = A.quiet_fill(variant).copy()
    pixels = image.load()
    # Only residual cells use these joins. Full tree crowns are selected from
    # generated component geometry. Exterior alpha exposes the actual floor.
    contact = (3, 3, 2, 2, 4, 3, 2, 2, 3, 4, 3, 2, 2, 3, 2, 3)
    for y in range(16):
        for x in range(16):
            west, north = x < 8, y < 8
            sx, sy = (x if west else 15-x), (y if north else 15-y)
            horizontal = bool(mask & (8 if west else 2))
            vertical = bool(mask & (1 if north else 4))
            corner = 1 if west and north else 2 if north else 8 if west else 4
            outside = ((horizontal and sx < contact[(y+(2 if west else 5)) % 16]) or
                       (vertical and sy < contact[(x+(0 if north else 7)) % 16]))
            if horizontal and vertical and sx < 6 and sy < 6:
                outside = (sx-5)**2 + (sy-5)**2 > 24
            if not horizontal and not vertical and corners & corner and sx+sy < 4:
                outside = True
            if outside:
                pixels[x, y] = 0
    return image, A.PALETTE_NAME


def fringe(parent, mask, variant=1):
    return Image.new('P', (16, 16), 0), A.PALETTE_NAME


def arch_group(variant=1):
    return BASE.arch_group(1)


def pulse_palettes(variant=1):
    return BASE.pulse_palettes(1)
