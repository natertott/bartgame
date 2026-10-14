"""Which ? room sites can host the lantern and gust-jar events, by tileset.

A torch is a TILE here, not an object: TILE_TYPE_117 (unlit) and
TILE_TYPE_118 (lit) - lightLevelSetManager.c and flameManager.c read them
that way; tiles.h's comments sit one off (119 is a raised floor button,
button.c). Tile types are global, but a room can only DRAW the
ones its tileset carries - SetTileType looks the type up in the layer's
tileIndices (the inverse of tileTypes), so a type the tileset lacks lands
as tile index 0xFFFF and draws nothing. The same holds for Mount Crenel's removable
dust, which REMOVABLE_DUST type 0 sits on (tile types 387 and 1018-1025).

So this lands in every ? room site (scenario SITE, the FAIRY kind: nothing
solid placed) and reads, for each layer, whether tileTypes[tileIndices[T]]
round-trips to T. Debris that is a sprite (SPIDER_WEB, the DUST enemy's cloud) needs no
tileset and is not surveyed here: lantern_gust_spike.py shows both draw
in a cave.

    python3 tools/quickstart/lantern_gust_survey.py [--rom tmc-d3.gba] [--sites 0-118] [--json OUT]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenario as S
import parse_tables as P
from emu import here

MAP_TOP, MAP_BOTTOM = 0x0200b650, 0x02025eb0
TILE_TYPES, TILE_INDICES, MAP_DATA = 0x5004, 0x6004, 0x0004
TORCH, TORCH_LIT = 0x75, 0x76
DUST = [387] + list(range(1018, 1026))


def u16(c, a):
    return c.memory.u8[a] | (c.memory.u8[a + 1] << 8)


def has_type(c, layer, t):
    idx = u16(c, layer + TILE_INDICES + 2 * t)
    return idx < 0x800 and u16(c, layer + TILE_TYPES + 2 * idx) == t


def main():
    args = sys.argv[1:]
    rom = args[args.index('--rom') + 1] if '--rom' in args else os.path.join(P.ROOT, 'tmc-d3.gba')
    sites = P.content_sites_full()
    lo, hi = 0, len(sites) - 1
    if '--sites' in args:
        lo, hi = [int(x) for x in args[args.index('--sites') + 1].split('-')]
    out = []
    for i in range(lo, hi + 1):
        an, rn = sites[i][0], sites[i][1]
        c = S.boot(rom, S.KINDS['SITE'], i, S.EVENTS.index('FAIRY'), 0, kit=2, diff=3, frames=300)
        row = dict(site=i, room=rn.replace('ROOM_', ''), here=list(here(c)))
        for name, base in (('bottom', MAP_BOTTOM), ('top', MAP_TOP)):
            row[name] = dict(torch=has_type(c, base, TORCH), lit=has_type(c, base, TORCH_LIT),
                             dust=all(has_type(c, base, t) for t in DUST))
        out.append(row)
        b, t = row['bottom'], row['top']
        print('%3d %-48s torch %s/%s  dust %s/%s' % (i, row['room'], 'Y' if b['torch'] and b['lit'] else '-',
              'Y' if t['torch'] and t['lit'] else '-', 'Y' if b['dust'] else '-', 'Y' if t['dust'] else '-'), flush=True)
        del c
    if '--json' in args:
        json.dump(out, open(args[args.index('--json') + 1], 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
