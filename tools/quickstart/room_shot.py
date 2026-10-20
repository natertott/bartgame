"""One picture of a whole room, stitched from screenshots.

Boots the ROOM scenario into the room, then moves the player over a grid so
the camera visits every part of it, and pastes each frame where the camera
stood (gRoomControls.scroll_x/y). The player and the HUD are in every
frame; the middle of each frame is kept, where they cover least. Tile
numbers every 4 tiles along the edges, for reading spots off the image.

    python3 tools/quickstart/room_shot.py AREA_NAME ROOM_NAME OUT.png [--rom tmc-d3.gba]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
from emu import r16, w16, ROOM_CONTROLS, PLAYER
import scenario as S
import parse_tables as P
from chain_audit import dismiss


def shoot(rom, area, room, out):
    from PIL import Image, ImageDraw
    c = S.boot(rom, S.KINDS['ROOM'], a=area, b=room, c=4, d=4, frames=300)
    dismiss(c)
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    w, h = r16(c, ROOM_CONTROLS + 0x1e), r16(c, ROOM_CONTROLS + 0x20)
    pad = 24
    big = Image.new('RGB', (w + 2 * pad, h + 2 * pad), (40, 40, 40))
    tmp = out + '.frame.png'
    for py in list(range(80, h, 96)) + [max(80, h - 80)]:
        for px in list(range(120, w, 160)) + [max(120, w - 120)]:
            w16(c, PLAYER + 0x2e, ox + px)
            w16(c, PLAYER + 0x32, oy + py)
            for _ in range(8):
                c.run_frame()
            dismiss(c, 120)
            sx, sy = r16(c, ROOM_CONTROLS + 0x0a) - ox, r16(c, ROOM_CONTROLS + 0x0c) - oy
            emu.snap(c, tmp)
            im = Image.open(tmp).convert('RGB').crop((16, 24, 224, 136))
            big.paste(im, (pad + sx + 16, pad + sy + 24))
    os.remove(tmp)
    d = ImageDraw.Draw(big)
    for t in range(0, max(w, h) // 16 + 1, 4):
        if t * 16 <= w:
            d.text((pad + t * 16, 4), str(t), fill=(255, 255, 0))
        if t * 16 <= h:
            d.text((2, pad + t * 16), str(t), fill=(255, 255, 0))
    big.save(out)
    return w, h


def main():
    rom = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else os.path.join(P.ROOT, 'tmc-d3.gba')
    area, room, out = sys.argv[1], sys.argv[2], sys.argv[3]
    a = P.AREAS[area] if not area.isdigit() else int(area)
    r = P.ROOMS[room] if not room.isdigit() else int(room)
    w, h = shoot(rom, a, r, out)
    print('%s %s %dx%d -> %s' % (area, room, w, h, out))


if __name__ == '__main__':
    main()
