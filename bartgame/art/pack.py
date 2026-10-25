"""The sprite pack, as the build reads it: art/pack/ holds one indexed
strip per sprite sheet and pack.json with the frame names and the
palettes. tools/import_pack.py makes them from the pack in art/ref/pack/.

frames(sheet) gives the frames as rows of hex digits ('.' clear), by
name; GROUPS the 16-entry OBJ palettes by group; PORTRAIT_PALETTES one
16-entry palette per portrait, in the portrait sheet's order."""
import json
import os

from PIL import Image

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pack')
META = json.load(open(os.path.join(HERE, 'pack.json')))

GROUPS = {g: ['#000000'] + cols for g, cols in META['groups'].items()}
# a palette per portrait when the pack gives one, else the group's
PORTRAIT_PALETTES = [['#000000'] + META.get('portrait_palettes', {}).get(n, META['groups']['portrait'])
                     for n in META['sheets']['portrait']['frames']]


def group(sheet):
    return META['sheets'][sheet]['group']


def frames(sheet):
    s = META['sheets'][sheet]
    w, h = s['w'], s['h']
    im = Image.open(os.path.join(HERE, sheet + '.png'))
    assert im.mode == 'P' and im.size == (w * len(s['frames']), h), sheet
    px = im.load()
    out = {}
    for i, name in enumerate(s['frames']):
        out[name] = [''.join('%x' % px[i * w + x, y] if px[i * w + x, y] else '.' for x in range(w))
                     for y in range(h)]
    return out
