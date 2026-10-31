"""Render-only topology contracts for forest profiles 6..10.

Original room identifiers remain semantic. These appended pictures are selected
by the renderer, never substituted into collision or saved world data. The 47
valid blob combinations use quarter-local artwork so the packer can share
8x8 cells rather than reserving hundreds of unrelated canopy pictures.
"""
from copy import deepcopy

HEALTHY = frozenset({'canopy', 'canopy2', 'canopy_s', 'canopy_n',
                     'canopy_lantern', 'canopy_glint',
                     'forest_canopy0', 'forest_canopy1',
                     'forest_canopy2', 'forest_canopy3'})
BLIGHT = frozenset({'canopy_blight', 'canopy_blight2', 'blight_wall',
                    'blight_wall2', 'blight_wall_lit'})
CONNECTORS = frozenset('forest_blight_tree%d' % i for i in range(6))


def eligible_corners(mask):
    return ((0 if mask & 9 else 1) | (0 if mask & 3 else 2) |
            (0 if mask & 6 else 4) | (0 if mask & 12 else 8))


def combinations():
    return [(mask, corners) for mask in range(16) for corners in range(16)
            if not corners & ~eligible_corners(mask)]


def append(tiles, coverage, variant):
    import forest_concepts_v2_terrain as art
    import forest_concepts as FC
    originals = {mt['name']: mt for mt in tiles}
    specs = []
    canopy = [[[[None for _ in range(16)] for _ in range(16)] for _ in range(4)] for _ in range(2)]
    fringe = [[None for _ in range(16)] for _ in range(2)]

    def emit(name, parent, images, bank, topology, visual=True, glitter=None):
        mt = deepcopy(originals[parent])
        mt.update(name=name, pal=bank)
        mt.pop('qpals', None); mt.pop('art', None); mt.pop('frames', None)
        frames = [FC.rows(im) for im in images]
        assert all(im.size == (16, 16) for im in images), name
        if len(frames) == 1:
            mt['art'] = frames[0]
        else:
            mt['frames'] = frames
        if glitter is not None:
            mt['glitter'] = int(glitter)
        tiles.append(mt)
        spec = {'name': name, 'parent': parent, 'visual_only': visual, **topology}
        specs.append(spec)
        coverage.append({'name': name, 'owner': 'forest_concepts_v2_topology',
                         'frames': len(frames), 'material': bank,
                         'glitter': bool(mt.get('glitter')), **spec})
        return name

    assert len(combinations()) == 47
    for kind, parent in enumerate(('canopy', 'blight_wall')):
        for quadrant in range(4):
            for mask, corners in combinations():
                image, bank = art.paint_adjacency(parent+'@q%d'%quadrant, mask, corners, 0, variant)
                name = 'f2_canopy_%d_%d_%x%x' % (kind, quadrant, mask, corners)
                canopy[kind][quadrant][mask][corners] = emit(name, parent, [image], bank,
                    {'family': 'canopy', 'kind': kind + 1, 'quadrant': quadrant,
                     'mask': mask, 'corners': corners})
        for mask in range(1, 16):
            image, bank = art.fringe(parent, mask, variant)
            name = 'f2_fringe_%d_%x' % (kind, mask)
            fringe[kind][mask] = emit(name, 'moss0', [image], bank,
                {'family': 'fringe', 'kind': kind + 1, 'mask': mask}, glitter=False)

    water = [[None for _ in range(16)] for _ in range(16)]
    for mask, corners in combinations():
        frames=[]
        for phase in range(2):
            image, bank = art.paint_adjacency('water', mask, corners, phase, variant)
            frames.append(image)
        name='f2_water_%x%x'%(mask,corners)
        water[mask][corners] = emit(name, 'water', frames, bank,
            {'family':'water','mask':mask,'corners':corners})
    isolated = []
    for parent in ('water_lily', 'water_foam'):
        count = len(originals[parent].get('frames', [None]))
        frames, bank = [], None
        for phase in range(count):
            image, bank = art.paint_adjacency(parent, 15, 0, phase, variant)
            frames.append(image)
        isolated.append(emit('f2_' + parent + '_isolated', parent, frames, bank,
            {'family': 'isolated_water', 'mask': 15, 'corners': 0}))

    arch, bank = art.arch_group(variant)
    assert arch.size == (32, 16), arch.size
    arches = [emit('f2_arch_%d' % i, 'moss0',
                   [arch.crop((i*16, 0, i*16+16, 16))], bank,
                   {'family': 'overhead_root_arch', 'part': i},
                   visual=False, glitter=True) for i in range(2)]
    return {'specs': specs, 'canopy': canopy, 'fringe': fringe,
            'water':water, 'isolated_water': isolated, 'arch': arches}


def classes(tiles):
    canopy, water = [], []
    for mt in tiles:
        name = mt['name']
        canopy.append(1 if name in HEALTHY else 2 if name in BLIGHT else
                      3 if name in CONNECTORS else 0)
        water.append(2 if name == 'water_lily' else 3 if name == 'water_foam'
                     else 1 if name == 'water' or name.startswith('water_')
                     else 4 if name == 'waterfall' or name in ('bridge', 'bridge_v')
                     or name.startswith('raft_') else 0)
    return canopy, water


def special_trees(tiles):
    return [int(mt['name'] in CONNECTORS or mt['name'] in
                ('dead_tree','forest_blight_dead_tree')) for mt in tiles]


def authored_crowns(tiles):
    names={'tree_top_nw','tree_top_ne','tree_mid_w','tree_mid_e'}
    for prefix in ('tree2_', 'birch_', 'fir_', 'sicktree_', 'btree_'):
        names.update(prefix+str(i) for i in range(4))
    for prefix in ('gtree_', 'gtree2_'):
        names.update(prefix+str(i) for i in range(9))
    return [int(mt['name'] in names) for mt in tiles]
