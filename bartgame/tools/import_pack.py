"""Import the BARTGAME GBA sprite pack into art/pack/.

    python3 tools/import_pack.py [PACK_DIR]      (default art/ref/pack)

The pack (art/ref/pack/, from the sprite pack zip) holds every sheet as
a 4-bit indexed PNG strip at the engine's frame size, frames side by
side in the order manifest.json lists, index 0 clear. Each sheet is
taken as it is, index for index, with the palette it carries; sheets of
one palette group must carry the same colours (checked).

The output, which the build reads (art/pack.py):
  art/pack/<sheet>.png        the sprite sheets
  art/pack/tiles/<sheet>.png  the tile sheets and the HUD tiles
  art/pack/pack.json          frame names, sizes, groups and palettes
Needs Pillow.
"""
import json
import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PACK = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'art', 'ref', 'pack')
OUT = os.path.join(ROOT, 'art', 'pack')

TILE_SHEETS = {'forest', 'wood', 'stone', 'cliff', 'blight', 'sewer', 'props', 'hud'}
# frame names the pack spells differently from the engine
RENAME = {'knight': {'walk1_s': 'walk_s1', 'walk2_s': 'walk_s2', 'walk1_n': 'walk_n1', 'walk2_n': 'walk_n2',
                     'walk1_e': 'walk_e1', 'walk2_e': 'walk_e2'}}


def hexes(pal):
    return ['#%02x%02x%02x' % c for c in pal]


def main():
    man = json.load(open(os.path.join(PACK, 'manifest.json')))
    meta = {'revision': man.get('revision', ''), 'groups': {}, 'sheets': {}, 'tiles': {}}
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'tiles'))
    for s in man['sheets']:
        name, w, h, frames = s['name'], s['frame_width'], s['frame_height'], s['frames']
        frames = [RENAME.get(name, {}).get(f, f) for f in frames]
        im = Image.open(os.path.join(PACK, s['png_path']))
        assert im.mode == 'P', (name, im.mode)
        assert im.size == (w * len(frames), h), (name, im.size)
        assert max(im.getextrema()) <= 15, (name, 'index above 15')
        raw = im.getpalette()[:48]
        pal = [tuple(raw[i * 3:i * 3 + 3]) for i in range(1, 16)]
        entry = {'w': w, 'h': h, 'frames': frames}
        if name in TILE_SHEETS:
            entry['palette'] = hexes(pal)
            meta['tiles'][name] = entry
            dst = os.path.join(OUT, 'tiles', name + '.png')
        else:
            group = s['group']
            if group in meta['groups']:
                assert meta['groups'][group] == hexes(pal), (name, 'differs from its group', group)
            meta['groups'][group] = hexes(pal)
            entry['group'] = group
            meta['sheets'][name] = entry
            dst = os.path.join(OUT, name + '.png')
        # the strip as it is, its palette entry 0 marked clear
        out = im.copy()
        out.save(dst, transparency=0)
    json.dump(meta, open(os.path.join(OUT, 'pack.json'), 'w'), indent=1, sort_keys=True)
    print('art/pack: %d sprite sheets in %d groups, %d tile sheets (%s)'
          % (len(meta['sheets']), len(meta['groups']), len(meta['tiles']), meta['revision']))


if __name__ == '__main__':
    main()
