"""Final Drain placement identities, preserving the original physical cells.

The earlier study map reused pictures from the north wall on both side walls
and reused ordinary floor pictures inside large fixtures. Final art therefore
gives each occupied placement an independent image identity. The original
gameplay type, collision mask, prop flag and glitter flag are copied from its
source metatile by tiles.py; the immutable original contract stays untouched.
"""
from copy import deepcopy
import json
from pathlib import Path

CONTRACTS = json.loads(Path(__file__).with_name('reboot_contracts.json').read_text())
ORIGINAL_ROOM = CONTRACTS['rooms'][0]
ORIGINAL_TILES = {row['name']: row for row in CONTRACTS['tiles']}
ROOM = deepcopy(ORIGINAL_ROOM)
CLONES = []
BY_NAME = {}


def placement_name(layer, x, y):
    assert layer in ('ground', 'overlay')
    return 'swh_f_%s_%02d_%02d' % (layer[0], x, y)


def parse_name(name):
    """Return (layer,x,y) for one final picture identifier."""
    prefix, final, lane, x, y = name.split('_')
    assert prefix == 'swh' and final == 'f' and lane in ('g', 'o'), name
    return ('ground' if lane == 'g' else 'overlay', int(x), int(y))


for _layer in ('ground', 'overlay'):
    for _y, _row in enumerate(ORIGINAL_ROOM[_layer]):
        for _x, _source in enumerate(_row):
            if _source is None:
                continue
            _name = placement_name(_layer, _x, _y)
            _spec = ORIGINAL_TILES[_source]
            _record = {
                'name': _name, 'source': _source, 'source_id': _spec['id'],
                'layer': _layer, 'x': _x, 'y': _y,
                'type': _spec['type'], 'coll': _spec['coll'], 'prop': _spec['prop'],
                'frames': _spec['frames'], 'anim_speed': _spec['anim_speed'],
            }
            CLONES.append(_record)
            BY_NAME[_name] = _record
            ROOM[_layer][_y][_x] = _name

assert len(CLONES) == 657
assert len({row['name'] for row in CLONES}) == 657
assert ROOM['objects'] == ORIGINAL_ROOM['objects']
