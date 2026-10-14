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
round-trips to T.

That is not enough to SEE one. A tileset can list the torch's tile and
still draw nothing there: the Minish houses do (their character data at
the torch's subtiles is blank). So with --draw, at every site that lists
it, an unlit torch is painted on open floor beside the player the way
game.c paints one (SetTileType, SetTile, the top tile cleared, then
UpdateScrollVram at once) and the 16x16 pixels there are compared before
and after: `draws` is whether they changed. Debris that is a sprite (SPIDER_WEB, the DUST enemy's cloud) needs no
tileset and is not surveyed here: lantern_gust_spike.py shows both draw
in a cave.

    python3 tools/quickstart/lantern_gust_survey.py [--rom tmc-d3.gba] [--sites 0-118] [--draw] [--json OUT]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenario as S
import parse_tables as P
from emu import here, r16, ROOM_CONTROLS, PLAYER
import callrom as C

MAP_TOP, MAP_BOTTOM = 0x0200b650, 0x02025eb0
TILE_TYPES, TILE_INDICES, MAP_DATA = 0x5004, 0x6004, 0x0004
TORCH, TORCH_LIT = 0x75, 0x76
DUST = [387] + list(range(1018, 1026))


def u16(c, a):
    return c.memory.u8[a] | (c.memory.u8[a + 1] << 8)


def has_type(c, layer, t):
    idx = u16(c, layer + TILE_INDICES + 2 * t)
    return idx < 0x800 and u16(c, layer + TILE_TYPES + 2 * idx) == t


def pixels(c, x0, y0):
    img = c.qs_video.to_pil().convert('RGB') if hasattr(c.qs_video, 'to_pil') else None
    if img is None:
        import io
        import emu
        buf = '/tmp/_lg_draw.png'
        emu.snap(c, buf)
        from PIL import Image
        img = Image.open(buf).convert('RGB')
    return [img.getpixel((x, y)) for y in range(y0, y0 + 16) for x in range(x0, x0 + 16) if 0 <= x < 240 and 0 <= y < 160]


def draws(c):
    """Paint an unlit torch on open floor two tiles above the player and
    say whether the screen changed there."""
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    sx, sy = r16(c, ROOM_CONTROLS + 0x0a), r16(c, ROOM_CONTROLS + 0x0c)   # camera
    px, py = r16(c, PLAYER + 0x2e) - ox, r16(c, PLAYER + 0x32) - oy
    for dy in (-2, -3, 2, 3):
        tx, ty = px >> 4, (py >> 4) + dy
        pos = tx + ty * 64
        if c.memory.u8[MAP_BOTTOM + 0x2004 + pos] != 0:      # collision: not open floor
            continue
        x0, y0 = ox + tx * 16 - sx, oy + ty * 16 - sy
        before = pixels(c, x0, y0)
        C.call_keep(c, C.map_sym('SetTileType'), (TORCH, pos, 1))
        C.call_keep(c, C.map_sym('SetTile'), (u16(c, MAP_BOTTOM + TILE_INDICES + 2 * TORCH), pos, 1))
        C.call_keep(c, C.map_sym('SetTile'), (0, pos, 2))
        c.memory.u8[0x02000070] = 1
        C.call_keep(c, C.map_sym('UpdateScrollVram'), ())
        for _ in range(3):
            c.run_frame()
        return before != pixels(c, x0, y0)
    return None


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
        if '--draw' in args and row['bottom']['torch'] and row['bottom']['lit']:
            row['draws'] = draws(c)
        out.append(row)
        b, t = row['bottom'], row['top']
        print('%3d %-48s torch %s/%s  dust %s/%s%s' % (i, row['room'], 'Y' if b['torch'] and b['lit'] else '-',
              'Y' if t['torch'] and t['lit'] else '-', 'Y' if b['dust'] else '-', 'Y' if t['dust'] else '-',
              '  draws %s' % row['draws'] if 'draws' in row else ''), flush=True)
        del c
    if '--json' in args:
        json.dump(out, open(args[args.index('--json') + 1], 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
