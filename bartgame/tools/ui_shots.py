"""The game's boxes and menus captured from the ROM, as a player sees them:
the Gatekeeper's words, the Peddler's shop and his words after a sale,
the pause menu's pages and the map, looked at closer.

    cd bartgame && make && python3 tools/ui_shots.py OUTDIR [--rom ROM]

Writes, raw 240x160: dialogue_gatekeeper.png, shop.png, dialogue_peddler.png,
pause_items.png, pause_keys.png, pause_map.png, pause_zoom.png,
pause_map_full.png and pause_zoom_full.png (with the Map and the
Astrolabe); and
ui_sheet.png, all of them at 2x side by side.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import probe as P  # noqa: E402
import critical_path as CP  # noqa: E402
import lift_probe as LP  # noqa: E402

args = sys.argv[1:]
ROM = P.ROM
if '--rom' in args:
    i = args.index('--rom')
    ROM = args[i + 1]
    del args[i:i + 2]
OUT = args[0]
os.makedirs(OUT, exist_ok=True)
shots = []


def snap(c, name):
    p = os.path.join(OUT, name + '.png')
    P.snap(c, p)
    shots.append(p)


def main():
    c = P.boot(rom=ROM, seed=0xB4A7)
    P.run(c, 40)
    CP.dismiss(c)
    pl = P.sym('gPl')
    P.w16(c, pl + 4, 123)       # gilt to buy with
    # the Gatekeeper's words
    CP.teleport(c, 21 * 16 + 8, 7 * 16 + 4)
    P.run(c, 60)
    P.hold(c, 'UP', 6)
    P.press(c, 'A', 2, 90)
    snap(c, 'dialogue_gatekeeper')
    CP.dismiss(c)
    # the shop, and the Peddler's words after a sale
    CP.teleport(c, 4 * 16 + 8, 7 * 16 + 6)
    P.run(c, 60)
    P.hold(c, 'UP', 6)
    P.press(c, 'A', 2, 30)
    snap(c, 'shop')
    P.press(c, 'A', 2, 90)
    snap(c, 'dialogue_peddler')
    CP.dismiss(c)
    # the pause menu, in the wood, with a full bag
    P.w8(c, pl + 8, 0x7F)
    P.w8(c, pl + 36, 3)
    P.w8(c, pl + 7, 3)
    w = CP.world(c)
    P.enter_forest(c)
    LP.warp(c, w['entry'], 2)
    P.run(c, 30)
    P.press(c, 'START', 2, 12)
    snap(c, 'pause_items')
    P.press(c, 'R', 2, 12)
    snap(c, 'pause_keys')
    P.press(c, 'R', 2, 20)
    snap(c, 'pause_map')
    P.press(c, 'A', 2, 20)
    snap(c, 'pause_zoom')
    P.press(c, 'B', 2, 20)
    P.press(c, 'START', 2, 20)
    # the map again with the Map and the Astrolabe: every cell drawn, the
    # chests, the Heart and the barriers marked; a cell up the wood closer
    P.w8(c, pl + 36, P.r8(c, pl + 36) | 0x0C)
    P.run(c, 30)
    P.press(c, 'START', 2, 20)
    P.press(c, 'R', 2, 16)
    P.press(c, 'R', 2, 60)       # the first look at every cell takes a moment
    snap(c, 'pause_map_full')
    P.press(c, 'UP', 2, 20)
    P.press(c, 'A', 2, 20)
    snap(c, 'pause_zoom_full')
    P.press(c, 'B', 2, 20)
    P.press(c, 'START', 2, 20)
    cols = 4
    rows = (len(shots) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * 496, rows * 336), (24, 24, 24))
    for i, p in enumerate(shots):
        im = Image.open(p).resize((480, 320), Image.NEAREST)
        sheet.paste(im, ((i % cols) * 496 + 8, (i // cols) * 336 + 8))
    sheet.save(os.path.join(OUT, 'ui_sheet.png'))
    print('wrote %d screens to %s' % (len(shots), OUT))


if __name__ == '__main__':
    main()
