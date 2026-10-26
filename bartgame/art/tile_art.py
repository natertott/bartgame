"""The illustrated tile atlases (art/ref/tile_art/, imported by
tools/import_tiles.py into art/tile_art/tiles.json) over the metatiles.

GROUPS are their palette groups, which take the place of the board
palettes they replace (RETIRE). apply() is called last in tiles.py, in
both builds: each imported tile replaces the art of the metatile of its
name, a metatile still drawn in a retired palette is remapped into the
group that took its place, colour by nearest colour, and one drawn in a
palette merged into another (palettes.MERGE) moves to that one."""
import json
import os

import palettes

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, 'tile_art', 'tiles.json')))
GROUPS = {g: ['#000000'] + cols for g, cols in sorted(DATA['palettes'].items())}
# The Drain's floor is a mottle of two tones; brought closer together, it
# lies quiet under what stands on it (its props carry the same floor)
CALM = {'drain_stone': {'#635141': '#594a3d'}, 'drain_props': {'#61533b': '#574a3a'}}
for _g, _m in CALM.items():
    GROUPS[_g] = [_m.get(c, c) for c in GROUPS[_g]]
TILES = DATA['tiles']
RETIRE = {'sewer': 'drain_stone', 'props': 'drain_props', 'blight': 'blight_floor'}


def apply(metatiles):
    names = {m['name'] for m in metatiles}
    assert set(TILES) <= names, sorted(set(TILES) - names)
    for m in metatiles:
        m['pal'] = palettes.MERGE.get(m['pal'], m['pal'])
        t = TILES.get(m['name'])
        if t:
            m['pal'] = t['pal']
            if len(t['frames']) > 1:
                m['frames'] = t['frames']
                m.pop('art', None)
                m['anim_speed'] = t.get('anim_speed', 20)
            else:
                m['art'] = t['frames'][0]
                m.pop('frames', None)
            continue
        new = RETIRE.get(m['pal'])
        if not new:
            continue
        rm = palettes._remap(palettes.TILE_ART_FROM[m['pal']], GROUPS[new])
        m['pal'] = new
        if 'frames' in m:
            m['frames'] = [palettes.remap_rows(f, rm) for f in m['frames']]
        else:
            m['art'] = palettes.remap_rows(m['art'], rm)
