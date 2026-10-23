"""Warp through every forest cell of a seed: render each room from RAM
(a layout review, art sources and all) and take an in-game screenshot at
its first monster spot; then a 5x5 sheet of each.

    python3 tools/roomshots.py OUTDIR [--seed N]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import probe as P  # noqa: E402
import roomdump  # noqa: E402
import critical_path as CP  # noqa: E402
from PIL import Image  # noqa: E402

OUT = sys.argv[1]
SEED = int(sys.argv[sys.argv.index('--seed') + 1], 0) if '--seed' in sys.argv else 0xB4A7
os.makedirs(OUT, exist_ok=True)
ARCH = ['glade', 'grove', 'ruins', 'pond', 'thicket', 'boneyard', 'arena', 'entry']


def ssym(name):
    lines = open(P.MAP).read().splitlines()
    for i, l in enumerate(lines):
        if l.strip().startswith('.bss.' + name) and (l.strip() == '.bss.' + name or l.split()[0] == '.bss.' + name):
            parts = l.split()
            if len(parts) >= 2 and parts[1].startswith('0x'):
                return int(parts[1], 16)
            return int(lines[i + 1].split()[0], 16)
    raise KeyError(name)


def warp(c, cell, side):
    P.w8(c, ssym('sNextArea'), 1)
    P.w8(c, ssym('sNextCell'), cell)
    P.w8(c, ssym('sNextSide'), side)
    P.w8(c, ssym('sTransPhase'), 0)
    P.w8(c, P.sym('gGame'), 2)
    P.run(c, 70)


def spots(c):
    g = P.sym('gSpots')
    n = P.r8(c, g + 24)
    return [(P.r8(c, g + i * 2), P.r8(c, g + i * 2 + 1)) for i in range(n)]


c = P.boot(seed=SEED)
P.run(c, 40)
w = CP.world(c)
P.enter_forest(c)
W = P.sym('gWorld')
renders, snaps, info = [], [], []
for cell in range(25):
    gates = w['cells'][cell]['gate']
    side = [s for s in range(4) if gates[s] not in (0,)][0]
    warp(c, cell, side)
    arch = P.r8(c, W + 4 + cell * 13 + 8)
    stage = w['cells'][cell]['stage']
    names = roomdump.render(c, os.path.join(OUT, 'room_%02d.png' % cell), scale=1)
    flat = [n for row in names for n in row]
    floor = sum(1 for n in flat if n not in ('canopy', 'canopy2', 'canopy_s', 'canopy_n', 'canopy_lan', 'canopy_bli'))
    info.append((cell, ARCH[arch], stage, floor, len(flat)))
    feats = {k: sum(1 for n in flat if n.startswith(k)) for k in ('ledge_s', 'waterfall', 'water_foam', 'blight_wal', 'water', 'bridge', 'bush', 'rock_small', 'boulder', 'tree_trunk', 'lantern_po', 'canopy_lan', 'moss_shade', 'path')}
    print('   ', ' '.join('%s=%d' % kv for kv in feats.items() if kv[1]))
    sp = spots(c)
    if sp:
        x, y = sp[0]
        CP.teleport(c, x * 16 + 8, y * 16 + 12)
        P.run(c, 40)
    P.snap(c, os.path.join(OUT, 'snap_%02d.png' % cell))
    renders.append(Image.open(os.path.join(OUT, 'room_%02d.png' % cell)).convert('RGB'))
    snaps.append(Image.open(os.path.join(OUT, 'snap_%02d.png' % cell)).convert('RGB'))
    print('cell %2d %-8s stage %d floor %d/%d gates %s spots %d' % (cell, ARCH[arch], stage, floor, len(flat), gates, len(sp)), flush=True)

sheet = Image.new('RGB', (5 * 256, 5 * 192))
for i, im in enumerate(renders):
    sheet.paste(im.resize((256, 192)), ((i % 5) * 256, (i // 5) * 192))
sheet.save(os.path.join(OUT, 'rooms_sheet.png'))
sheet = Image.new('RGB', (5 * 240, 5 * 160))
for i, im in enumerate(snaps):
    sheet.paste(im, ((i % 5) * 240, (i // 5) * 160))
sheet.save(os.path.join(OUT, 'snaps_sheet.png'))
print('done')
