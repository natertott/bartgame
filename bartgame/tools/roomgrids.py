"""Dump every wood room of some seeds as grids of metatile names, and
render such dumps from the art sources, so art can be judged on many real
rooms without rebuilding the ROM.

    python3 tools/roomgrids.py dump OUT.json SEED [SEED...]
    python3 tools/roomgrids.py myst OUT.json
    python3 tools/roomgrids.py render IN.json OUTDIR [--scale N]

A dump records, per room, the seed, cell, kind and stage, and the ground
and overlay layers as metatile names ('' where the overlay is empty). Names
outlive metatile ids, so a dump stays good while art is added; a change to
the room generator wants a new dump.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'art'))

ARCH = ['glade', 'grove', 'ruins', 'pond', 'thicket', 'boneyard', 'arena', 'entry']


def dump(out, seeds):
    import probe as P
    import critical_path as CP
    import tiles

    def ssym(name):
        lines = open(P.MAP).read().splitlines()
        for i, l in enumerate(lines):
            if l.strip().startswith('.bss.' + name) and (l.strip() == '.bss.' + name or l.split()[0] == '.bss.' + name):
                parts = l.split()
                if len(parts) >= 2 and parts[1].startswith('0x'):
                    return int(parts[1], 16)
                return int(lines[i + 1].split()[0], 16)
        raise KeyError(name)

    names = [m['name'] for m in tiles.METATILES]
    rooms = []
    for seed in seeds:
        c = P.boot(seed=seed)
        P.run(c, 40)
        w = CP.world(c)
        P.enter_forest(c)
        W = P.sym('gWorld')
        R = P.sym('gRoom')
        for cell in range(25):
            gates = w['cells'][cell]['gate']
            side = [s for s in range(4) if gates[s]][0]
            P.w8(c, ssym('sNextArea'), 1)
            P.w8(c, ssym('sNextCell'), cell)
            P.w8(c, ssym('sNextSide'), side)
            P.w8(c, ssym('sTransPhase'), 0)
            P.w8(c, P.sym('gGame'), 2)
            P.run(c, 70)
            rw, rh = P.r8(c, R), P.r8(c, R + 1)
            layers = []
            for layer in (0, 1):
                base = R + 2 + layer * 2048
                grid = []
                for y in range(rh):
                    row = []
                    for x in range(rw):
                        v = P.r16(c, base + (y * 32 + x) * 2) & 0xFFFF
                        row.append('' if v == 0xFFFF else names[v])
                    grid.append(row)
                layers.append(grid)
            rooms.append({'seed': seed, 'cell': cell, 'arch': ARCH[P.r8(c, W + 4 + cell * 13 + 8)],
                          'stage': w['cells'][cell]['stage'], 'ground': layers[0], 'overlay': layers[1]})
            print('seed %#x cell %d %s stage %d' % (seed, cell, rooms[-1]['arch'], rooms[-1]['stage']), flush=True)
    with open(out, 'w') as f:
        json.dump(rooms, f)


def dump_myst(out, seed=0xB4A7):
    """every style at every size, each with an event that furnishes it"""
    import probe as P
    import critical_path as CP
    import myst_probe as MP
    import tiles
    names = [m['name'] for m in tiles.METATILES]
    c = P.boot(seed=seed)
    P.run(c, 40)
    w = CP.world(c)
    P.enter_forest(c)
    cell = [i for i in range(25) if i not in (w['entry'], w['goal']) and w['cells'][i]['role'] != 7][0]
    rooms = []
    kinds = ['pots', 'switches', 'torches', 'boulders', 'chest', 'fairy']
    for style in range(3):
        for size in range(3):
            kind = kinds[(style * 3 + size) % len(kinds)]
            if not MP.enter(c, cell, kind, size, style):
                print('no way in', style, size)
                continue
            layers = []
            for layer in (0, 1):
                wd, ht, g = MP.grid(c, layer)
                layers.append([['' if g[(x, y)] == 0xFFFF else names[g[(x, y)]] for x in range(wd)] for y in range(ht)])
            rooms.append({'seed': seed, 'cell': style * 3 + size, 'arch': ['cave', 'hollow', 'thicket'][style] + '_' + kind,
                          'stage': 0, 'ground': layers[0], 'overlay': layers[1]})
            print('style %d size %d %s' % (style, size, kind), flush=True)
            MP.leave(c)
    with open(out, 'w') as f:
        json.dump(rooms, f)


def tile_rgba(m, frame=0):
    import palettes
    pal = dict(palettes.BG_PALETTES)[palettes.MERGE.get(m['pal'], m['pal'])]
    art = (m.get('frames') or [m['art']])
    rows = art[min(frame, len(art) - 1)]
    out = []
    for r in rows:
        line = []
        for ch in r:
            if ch in '. 0':
                line.append(None)
            else:
                h = pal[int(ch, 16)].lstrip('#')
                line.append(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
        out.append(line)
    return out


def render_room(room, by_name, scale=1, cache=None):
    from PIL import Image
    cache = {} if cache is None else cache
    g, o = room['ground'], room['overlay']
    h, w = len(g), len(g[0])
    im = Image.new('RGB', (w * 16, h * 16), (0, 0, 0))
    px = im.load()
    for layer, grid in ((0, g), (1, o)):
        for y in range(h):
            for x in range(w):
                n = grid[y][x]
                if not n:
                    continue
                if n not in cache:
                    cache[n] = tile_rgba(by_name[n]) if n in by_name else None
                t = cache[n]
                if t is None:
                    continue
                for yy in range(16):
                    for xx in range(16):
                        col = t[yy][xx]
                        if col is None:
                            if layer == 1:
                                continue
                            col = (0, 0, 0)
                        px[x * 16 + xx, y * 16 + yy] = col
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    return im


def render(inp, outdir, scale=1):
    import tiles
    rooms = json.load(open(inp))
    os.makedirs(outdir, exist_ok=True)
    by_name = {m['name']: m for m in tiles.METATILES}
    cache = {}
    for r in rooms:
        im = render_room(r, by_name, scale, cache)
        im.save(os.path.join(outdir, 'r_%x_%02d_s%d_%s.png' % (r['seed'], r['cell'], r['stage'], r['arch'])))
    missing = sorted({n for r in rooms for L in (r['ground'], r['overlay']) for row in L for n in row if n and n not in by_name})
    if missing:
        print('names no longer drawn:', missing)


if __name__ == '__main__':
    if sys.argv[1] == 'myst':
        dump_myst(sys.argv[2])
    elif sys.argv[1] == 'dump':
        dump(sys.argv[2], [int(a, 0) for a in sys.argv[3:]])
    else:
        sc = int(sys.argv[sys.argv.index('--scale') + 1]) if '--scale' in sys.argv else 1
        render(sys.argv[2], sys.argv[3], sc)
