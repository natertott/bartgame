"""Compare two 240x160 frames pixel for pixel: an approved master (or a
composed frame) against an engine capture.

    python3 tools/compare_frames.py A.png B.png [--tolerance 8] [--output diff.png] [--report report.json] [--cell 16]

A pixel matches when no RGB channel differs by more than the tolerance
(8 covers the hardware's 5 bits a channel). diff.png shows B in grey with
every mismatched pixel in magenta; the report gives the count, the worst
difference, and the mismatched pixels in each cell of the grid, so a fault
can be traced to a tile. Exit status 0 when every pixel matches, 1 when
not.
"""
import json
import sys

from PIL import Image

args = sys.argv[1:]


def opt(name, default):
    if name in args:
        i = args.index(name)
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return default


tol = int(opt('--tolerance', 8))
out = opt('--output', None)
rep = opt('--report', None)
cell = int(opt('--cell', 16))
a, b = (Image.open(p).convert('RGB') for p in args[:2])
assert a.size == b.size == (240, 160), ('both frames must be 240x160', a.size, b.size)
pa, pb = a.load(), b.load()
diff = Image.new('RGB', a.size)
pd = diff.load()
bad = 0
worst = 0
cells = {}
for y in range(160):
    for x in range(240):
        d = max(abs(u - v) for u, v in zip(pa[x, y], pb[x, y]))
        worst = max(worst, d)
        if d > tol:
            bad += 1
            pd[x, y] = (255, 0, 255)
            k = '%d,%d' % (x // cell, y // cell)
            cells[k] = cells.get(k, 0) + 1
        else:
            g = sum(pb[x, y]) // 6
            pd[x, y] = (g, g, g)
if out:
    diff.save(out)
report = {'a': args[0], 'b': args[1], 'tolerance': tol, 'pixels': 240 * 160, 'mismatched': bad,
          'match_percent': round(100.0 * (1 - bad / (240 * 160.0)), 3), 'worst_channel_difference': worst,
          'mismatched_by_cell': dict(sorted(cells.items(), key=lambda kv: -kv[1])), 'cell_px': cell, 'pass': bad == 0}
if rep:
    json.dump(report, open(rep, 'w'), indent=1)
print('%s vs %s: %d of %d pixels differ by more than %d (worst %d), %s' % (args[0], args[1], bad, 240 * 160, tol, worst, 'PASS' if bad == 0 else 'FAIL'))
sys.exit(0 if bad == 0 else 1)
