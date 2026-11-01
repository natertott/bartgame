"""Retire legacy tree pictures; compact approved frames are packed separately.

Semantic IDs retain their maze/collision contracts. The renderer supplies real
local floor below transparent tree layers, with no dark canopy backing.
"""
from PIL import Image
import forest_tree_study as TREES
import forest_concepts_v2_terrain as BASE
from forest_canopy_adaptive_terrain import owns as legacy_owns

BANKS = BASE.BANKS
supports = BASE.supports


def owns(name):
    return legacy_owns(name) or name.startswith('btree_')


def palette(name, variant=1):
    return TREES.palette(name) if name == TREES.PALETTE_NAME else BASE.palette(name, 1)


def extra_palettes(variant=1):
    return {TREES.PALETTE_NAME: TREES.palette()}


def paint(name, phase=0, variant=1):
    if owns(name):
        return Image.new('P', (16, 16), 0), TREES.PALETTE_NAME
    return BASE.paint(name, phase, 1)


def paint_adjacency(parent, mask, corners=0, phase=0, variant=1, quadrant=None):
    if owns(parent.split('@q')[0]):
        return Image.new('P', (16, 16), 0), TREES.PALETTE_NAME
    return BASE.paint_adjacency(parent, mask, corners, phase, 1, quadrant)


def fringe(parent, mask, variant=1):
    return Image.new('P', (16, 16), 0), TREES.PALETTE_NAME


def arch_group(variant=1):
    return BASE.arch_group(1)


def pulse_palettes(variant=1):
    return BASE.pulse_palettes(1)
