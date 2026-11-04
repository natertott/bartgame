"""Render-only local-floor path joins for the composed forest rooms."""
from copy import deepcopy
from forest_concepts_v2_topology import combinations
import forest_cohesion_terrain as ART

DECOR_NAMES = ('moss_flowers', 'moss_flowers2', 'tall_grass', 'fern_patch',
               'leaf_litter', 'moss_shade')


def append(tiles, coverage, variant=1):
    originals = {mt['name']: mt for mt in tiles}
    paths = [[[None for _ in range(16)] for _ in range(16)] for _ in range(2)]
    decor = [[None for _ in DECOR_NAMES] for _ in range(2)]
    specs = []
    for sick in range(2):
        for mask, corners in combinations():
            image, bank = ART.path_adjacency(mask, corners, bool(sick))
            name = 'cohesion_path_%d_%x%x' % (sick, mask, corners)
            mt = deepcopy(originals['path'])
            mt.update(name=name, pal=bank)
            mt.pop('frames', None); mt.pop('qpals', None)
            mt['art'] = [''.join(format(image.getpixel((x, y)), 'x') for x in range(16))
                         for y in range(16)]
            tiles.append(mt)
            spec = {'name': name, 'parent': 'path', 'visual_only': True,
                    'family': 'cohesion_path', 'sick': sick,
                    'mask': mask, 'corners': corners}
            specs.append(spec)
            paths[sick][mask][corners] = name
            coverage.append({'name': name, 'owner': 'forest_cohesion_topology',
                             'frames': 1, 'material': bank, 'glitter': False, **spec})
    for sick in range(2):
        for index, parent in enumerate(DECOR_NAMES):
            image, _ = ART.paint(parent)
            bank = 'decay_mix' if sick else 'ground'
            name = 'cohesion_decor_%d_%d' % (sick, index)
            mt = deepcopy(originals[parent])
            mt.update(name=name, pal=bank)
            mt.pop('frames', None); mt.pop('qpals', None)
            mt['art'] = [''.join(format(image.getpixel((x, y)), 'x') for x in range(16))
                         for y in range(16)]
            tiles.append(mt)
            spec = {'name': name, 'parent': parent, 'visual_only': True,
                    'family': 'cohesion_decor', 'sick': sick, 'index': index}
            specs.append(spec)
            decor[sick][index] = name
            coverage.append({'name': name, 'owner': 'forest_cohesion_topology',
                             'frames': 1, 'material': bank, 'glitter': False, **spec})
    return {'specs': specs, 'path': paths, 'decor': decor}
