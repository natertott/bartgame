"""The HUD captured from the ROM in the states a player meets: the first
steps in the hall, a long bar with the purse and both counts, the other
items, nothing held, the wood, and the gardener's dark room.

    cd bartgame && make && python3 tools/hud_shots.py OUTDIR [--rom ROM]

Writes, raw 240x160: hud_hall.png, hud_counts.png (ten hearts, six and a
half full, the seeds on A, the bow on L), hud_others.png (the lamp, the
cloak, the cap), hud_empty.png (half a heart, nothing held), hud_wood.png
and hud_dark.png; and hud_sheet.png, all of them at 2x, and
hud_bands.png, the top 32 rows of each at 4x.
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
ROLE_NPC_TORCH = 7
# gPl: hp, hp_max, gilt (s16, s16, u16), keys, bombs, items, equip[3]
# (A, B, L) from 6, arrows at 35
HP, HP_MAX, GILT, KEYS, BOMBS, ITEMS, EQUIP, ARROWS = 0, 2, 4, 6, 7, 8, 9, 35
EQ_NONE, EQ_SWORD, EQ_BOMBS, EQ_LAMP, EQ_CLOAK, EQ_SHIELD, EQ_BOW, EQ_HUBCAP = range(8)


def snap(c, name):
    p = os.path.join(OUT, name + '.png')
    P.snap(c, p)
    shots.append(p)


def equip(c, a, b, l):
    pl = P.sym('gPl')
    for s, eq in enumerate((a, b, l)):
        P.w8(c, pl + EQUIP + s, eq)


def main():
    c = P.boot(rom=ROM, seed=0xB4A7)
    P.run(c, 40)
    CP.dismiss(c)
    pl = P.sym('gPl')
    CP.teleport(c, 12 * 16 + 8, 9 * 16 + 4)
    P.run(c, 30)
    snap(c, 'hud_hall')
    P.w16(c, pl + HP_MAX, 80)
    P.w16(c, pl + HP, 52)
    P.w16(c, pl + GILT, 1234)
    P.w8(c, pl + KEYS, 2)
    P.w8(c, pl + ITEMS, 0x7F)
    P.w8(c, pl + BOMBS, 7)
    P.w8(c, pl + ARROWS, 23)
    equip(c, EQ_BOMBS, EQ_SWORD, EQ_BOW)
    P.run(c, 4)
    snap(c, 'hud_counts')
    equip(c, EQ_LAMP, EQ_CLOAK, EQ_HUBCAP)
    P.w16(c, pl + HP, 80)
    P.run(c, 4)
    snap(c, 'hud_others')
    equip(c, EQ_NONE, EQ_NONE, EQ_NONE)
    P.w16(c, pl + HP_MAX, 24)
    P.w16(c, pl + HP, 4)
    P.run(c, 4)
    snap(c, 'hud_empty')
    equip(c, EQ_BOMBS, EQ_SWORD, EQ_SHIELD)
    P.w16(c, pl + HP_MAX, 48)
    P.w16(c, pl + HP, 48)
    w = CP.world(c)
    P.enter_forest(c)
    P.run(c, 30)
    snap(c, 'hud_wood')
    dark = [i for i, cl in enumerate(w['cells']) if cl['role'] == ROLE_NPC_TORCH]
    if dark:
        LP.warp(c, dark[0], 2)
        P.run(c, 40)
        snap(c, 'hud_dark')
    cols = 2
    rows = (len(shots) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * 496, rows * 336), (24, 24, 24))
    for i, p in enumerate(shots):
        im = Image.open(p).resize((480, 320), Image.NEAREST)
        sheet.paste(im, ((i % cols) * 496 + 8, (i // cols) * 336 + 8))
    sheet.save(os.path.join(OUT, 'hud_sheet.png'))
    bands = Image.new('RGB', (960, len(shots) * 136 - 8), (24, 24, 24))
    for i, p in enumerate(shots):
        im = Image.open(p).crop((0, 0, 240, 32)).resize((960, 128), Image.NEAREST)
        bands.paste(im, (0, i * 136))
    bands.save(os.path.join(OUT, 'hud_bands.png'))
    print('wrote %d screens to %s' % (len(shots), OUT))


if __name__ == '__main__':
    main()
