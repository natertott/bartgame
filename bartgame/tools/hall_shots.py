"""Screenshots of the Drain's hall from the real ROM: the views a player
sees, and the whole hall stitched from raw captures.

    cd bartgame && make && python3 tools/hall_shots.py OUTDIR [--rom ROM --map MAP]

Writes, raw 240x160 unless named otherwise:

    view_<name>.png    the hero stood at a spot, the camera settled on him,
                       HUD and all, as a player sees it
    hall_full.png      the whole room: four captures with the HUD
                       and the sprites off, laid edge to edge
    hall_full_3x.png   the same at 3x, nearest neighbour
    views_sheet.png    the views side by side at 2x
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import probe as P  # noqa: E402
import critical_path as CP  # noqa: E402

args = sys.argv[1:]


def opt(name, default):
    if name in args:
        i = args.index(name)
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return default


ROM = opt('--rom', P.ROM)
P.MAP = opt('--map', P.MAP)
OUT = args[0]
os.makedirs(OUT, exist_ok=True)
DISPCNT = 0x04000000
MODE0_OBJ1D = 0x0040
BG1, BG2, OBJ = 0x0200, 0x0400, 0x1000

# where the hero stands for each view, in room pixels (his feet)
VIEWS = [
    ('spawn', None),                       # where a run begins
    ('peddler', (4 * 16 + 8, 7 * 16 + 10)),
    ('falls', (15 * 16, 7 * 16 + 14)),
    ('gatekeeper', (21 * 16 + 8, 8 * 16 + 4)),
    ('hole', (9 * 16 + 8, 4 * 16 + 14)),
    ('bridge', (15 * 16, 13 * 16 + 14)),
    ('lower_left', (5 * 16 + 8, 15 * 16 + 14)),
    ('lower_right', (24 * 16 + 8, 15 * 16 + 14)),
]


def settle(c, x, y, frames=120):
    CP.teleport(c, x, y)
    P.run(c, frames)


c = P.boot(rom=ROM, seed=0xB4A7)
P.run(c, 60)
CP.dismiss(c)
shots = []
for name, at in VIEWS:
    if at:
        settle(c, *at)
    else:
        P.run(c, 30)
    p = os.path.join(OUT, 'view_%s.png' % name)
    P.snap(c, p)
    shots.append(p)

# the whole hall: the camera at each corner, the HUD and the sprites off
full = P.r16(c, DISPCNT) & 0xFFFF
R = P.sym('gRoom')
RW, RH = P.r8(c, R) * 16, P.r8(c, R + 1) * 16
hall = Image.new('RGB', (RW, RH))
for cx, cy in ((0, 0), (RW - 240, 0), (0, RH - 160), (RW - 240, RH - 160)):
    # the spot the camera centres on this corner (the sprites are off, and
    # nothing in the hall makes the hero fall, so any spot will do)
    settle(c, cx + 120, cy + 104, 150)
    P.w16(c, DISPCNT, MODE0_OBJ1D | BG1 | BG2)
    c.run_frame()
    cam = (P.r16(c, P.sym('gCamX')), P.r16(c, P.sym('gCamY')))
    assert cam == (cx, cy), ('the camera did not settle', cam, (cx, cy))
    p = os.path.join(OUT, '_part.png')
    P.snap(c, p)
    hall.paste(Image.open(p), (cx, cy))
    P.w16(c, DISPCNT, full)
    c.run_frame()
os.remove(os.path.join(OUT, '_part.png'))
hall.save(os.path.join(OUT, 'hall_full.png'))
hall.resize((RW * 3, RH * 3), Image.NEAREST).save(os.path.join(OUT, 'hall_full_3x.png'))
cols = 3
rows = (len(shots) + cols - 1) // cols
sheet = Image.new('RGB', (cols * 248 * 2, rows * 168 * 2), (24, 24, 24))
for i, p in enumerate(shots):
    im = Image.open(p).resize((480, 320), Image.NEAREST)
    sheet.paste(im, ((i % cols) * 496 + 8, (i // cols) * 336 + 8))
sheet.save(os.path.join(OUT, 'views_sheet.png'))
print('wrote %d views and the hall to %s' % (len(shots), OUT))
