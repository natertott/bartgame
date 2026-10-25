"""Import the BARTGAME sprite pack into art/pack/.

    python3 tools/import_pack.py

Two sources, in order:

 1. art/ref/pack/, the engine-sized pack: every sheet a 4-bit indexed
    PNG strip at the engine's frame size, frames side by side in the
    order manifest.json lists, index 0 clear. Each is taken index for
    index with the palette it carries; sheets of one palette group must
    carry the same colours (checked).
 2. art/ref/pack_art/, the illustrated sheets that came after it: large
    RGBA pictures, one figure per cell (tools/pack_art.py cuts them).
    They replace the Bloom, the shields, the small items, the pickups,
    the treasure icons, the folk, the hub's two and the portraits. Each
    sheet's cells are mapped to the engine's frames below, by pose where
    the picture has more cells than the engine has frames. Their palette
    groups are derived from them; a strip of stage 1 left in a group
    whose colours changed (the sword, the shield menu symbols) is
    remapped into it.

The output, which the build reads (art/pack.py):
  art/pack/<sheet>.png        the sprite sheets
  art/pack/tiles/<sheet>.png  the tile sheets and the HUD tiles
  art/pack/pack.json          frame names, sizes, groups and palettes
Needs numpy and Pillow.
"""
import json
import os
import shutil
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pack_art as PA  # noqa: E402

ROOT = os.path.dirname(HERE)
PACK = os.path.join(ROOT, 'art', 'ref', 'pack')
ARTS = os.path.join(ROOT, 'art', 'ref', 'pack_art')
OUT = os.path.join(ROOT, 'art', 'pack')

TILE_SHEETS = {'forest', 'wood', 'stone', 'cliff', 'blight', 'sewer', 'props', 'hud'}
# frame names the pack spells differently from the engine
RENAME = {'knight': {'walk1_s': 'walk_s1', 'walk2_s': 'walk_s2', 'walk1_n': 'walk_n1', 'walk2_n': 'walk_n2',
                     'walk1_e': 'walk_e1', 'walk2_e': 'walk_e2'}}


def hexes(pal):
    return ['#%02x%02x%02x' % tuple(c) for c in pal]


def art(name):
    return PA.solid(PA.load(os.path.join(ARTS, name + '.png')))


# ------------------------------------------------- the illustrated sheets --
def bloom():
    """The Bloom, 64x32 (the swing's arcs reach past 32), from bloom.png:
    57 poses in six rows for the engine's 50 frames. The rows: idles and
    walks; the swings (the sword drawn in); the roll; hurt, the leap, the
    prize held up, carrying; carrying and drowning; falling and guarding
    (a leaf for a shield). All at one scale, the front idle 31 pixels
    tall, each centred on its flower head with its row's ground on the
    last row.

    Choices where the sheet has no exact pose: the front walk takes the
    two three-quarter steps; the back walk is one step and its mirror;
    the back swing has one pose, the back idle winding up; the back leap
    is the back idle raised a pixel; the front carry bobs a pixel for its
    steps; the back carry's second step mirrors its first (cell 36 draws
    the barrel across her back, where the engine draws the real load).
    The coin held up in the prize pose is taken out (the engine draws the
    real prize there). Spare cells: 6, 9, 17, 18, 31, 33, 36, 41, 42, 44,
    46, 51, 52, 53."""
    src = art('bloom')
    # the crescent between the back swing and the side swipe is the back
    # swing's
    cells = PA.flat(PA.segment(src, [10, 8, 9, 11, 10, 9], xcuts={1: {5: 1046}}))
    assert len(cells) == 57, len(cells)
    x0, y0, x1, y1, _ = cells[0]
    scale = 31.0 / (y1 - y0)

    # the prize pose without its coin and glints: the gold in the upper
    # part of the cell
    get = cells[32]
    gx0, gy0, gx1, gy1, _ = get
    top = src[gy0:gy0 + int((gy1 - gy0) * 0.42), gx0:gx1]
    r, g, b = top[:, :, 0], top[:, :, 1], top[:, :, 2]
    coin = (r > 150) & (g > 120) & (b < 150) & (g > 0.55 * r)
    top[coin, 3] = 0
    # the specks of glow the coin leaves round it
    hi = top[:, :, 3] > 0
    for y in range(hi.shape[0]):
        for x in range(hi.shape[1]):
            if hi[y, x] and top[y, x, :3].sum() > 520:
                top[y, x, 3] = 0

    def at(i, dy=0):
        c = cells[i]
        return PA.place(src, c, 64, 32, scale, 'bottom', anchor_x=PA.head_x(src, c), base_y=c[4][3], dy=dy)

    pick = {
        'idle_s': 0, 'idle_n': 1, 'idle_e': 2,
        'walk_s1': 8, 'walk_s2': 3, 'walk_n1': 4, 'walk_e1': 5, 'walk_e2': 7,
        'atk_s1': 14, 'atk_s': 11, 'atk_s3': 10,
        'atk_n1': 1, 'atk_n': 15, 'atk_n3': 15,
        'atk_e1': 13, 'atk_e': 16, 'atk_e3': 12,
        'roll_1': 19, 'roll_2': 20, 'roll_3': 21, 'roll_4': 22, 'roll_5': 23, 'roll_6': 24, 'roll_7': 25,
        'hurt_s': 27, 'hurt_n': 28, 'hurt_e': 29,
        'jump_s': 26, 'jump_e': 30, 'itemget': 32,
        'carry_s': 38, 'carry_n': 34, 'carry_e': 35, 'carry_n1': 39, 'carry_e1': 37, 'carry_e2': 40,
        'drown_1': 43, 'drown_2': 45, 'drown_3': 47,
        'fall_1': 48, 'fall_2': 49, 'fall_3': 50,
        'guard_s': 54, 'guard_n': 55, 'guard_e': 56,
    }
    out = {k: at(i) for k, i in pick.items()}
    out['walk_n2'] = PA.hflip(out['walk_n1'])
    out['carry_n2'] = PA.hflip(out['carry_n1'])  # cell 36 draws the barrel on her back; the load does that
    out['jump_n'] = PA.raised(out['idle_n'], 1)
    out['carry_s1'] = PA.raised(out['carry_s'], 1)
    out['carry_s2'] = PA.raised(out['carry_s'], 1)
    return out


def shields():
    """The shields, 16x16, from shields.png: six rows of nine turns; the
    first of each row. Rows: the plain round shield front, edge, back;
    the upgraded tree shield front, edge, back."""
    src = art('shields')
    rows = PA.segment(src, [9] * 6)
    first = [r[0] for r in rows]
    scale = min(min(15.0 / (c[2] - c[0]), 15.0 / (c[3] - c[1])) for c in first)
    f = [PA.place(src, c, 16, 16, scale, 'center') for c in first]
    return {'front': f[0], 'side': f[1], 'back': f[2]}, {'front': f[3], 'side': f[4], 'back': f[5]}


def items16():
    """The small items, 16x16, from items16.png, each fitted to its slot."""
    src = art('items16')
    cells = PA.flat(PA.segment(src, [6, 6, 5, 3], smooth=31))
    names = ['none', 'bombs', 'lamp', 'cloak', 'key', 'heart_piece', 'heart_container', 'gilt_big', 'relic', 'heart',
             'gilt', 'bomb_pickup', 'spark', 'grail', 'gauntlet', 'bow', 'arrow1', 'arrow5', 'arrow10', 'hubcap']
    assert len(cells) == len(names)
    return {n: PA.fit(src, c, 16, 16, 1) for n, c in zip(names, cells)}


def pickups():
    """The ground pickups, 32x32, from pickups.png: four turns of each, the
    first taken (the engine bobs them): hearts; gilt and seeds; the gilt
    pouch and keys; the relic and the grail; one, five and ten arrows."""
    src = art('pickups')
    rows = PA.segment(src, [4, 8, 8, 8, 11], smooth=25)
    sel = {'heart': rows[0][0], 'gilt': rows[1][0], 'bomb_pickup': rows[1][4], 'gilt_big': rows[2][0],
           'key': rows[2][4], 'relic': rows[3][0], 'grail': rows[3][4], 'arrow1': rows[4][0],
           'arrow5': rows[4][4], 'arrow10': rows[4][7]}
    scale = min(min(30.0 / (c[2] - c[0]), 30.0 / (c[3] - c[1])) for c in sel.values())
    return {n: PA.place(src, c, 32, 32, scale, 'bottom') for n, c in sel.items()}


def icons():
    """The treasures, 32x32, from icons.png: 23 cells for the engine's 16.
    Spare: two and three seeds, a second purse, a lone gilt, four gilt, a
    purse of gilt."""
    src = art('icons')
    cells = PA.flat(PA.segment(src, [6, 6, 6, 5], smooth=25))
    idx = {'none': 0, 'bombs': 1, 'lamp': 4, 'cloak': 5, 'key': 6, 'heart_piece': 7, 'heart_container': 8,
           'gilt_big': 9, 'relic': 12, 'gauntlet': 13, 'bow': 14, 'hubcap': 15, 'map': 16, 'astrolabe': 17,
           'sword': 18, 'shield': 19}
    scale = min(min(28.0 / (c[2] - c[0]), 28.0 / (c[3] - c[1])) for c in cells)
    return {n: PA.place(src, cells[i], 32, 32, scale, 'center') for n, i in idx.items()}


def folk():
    """The folk, 32x32, from folk.png: a row of poses each for the
    Gatekeeper, the Peddler, the Hermit Knight, the Weeping Nun, the
    Gardener, Sister Mary Grace and Brother Mark; the first of each (the
    front idle), all at one scale, feet on the last row."""
    src = art('folk')
    rows = PA.segment(src, [12, 11, 10, 11, 11, 12, 12], smooth=15)
    names = ['sage', 'merchant', 'hermit', 'nun', 'gardener', 'sister_mary_grace', 'brother_mark']
    scale = min(31.0 / (r[0][3] - r[0][1]) for r in rows)
    return {n: PA.place(src, r[0], 32, 32, scale, 'bottom') for n, r in zip(names, rows)}


def hub_folk():
    """The hub's two, 32x32, from hub_folk.png: the Gatekeeper twice (her
    orb flares), the Peddler at his stall twice (his hands meet). The
    Peddler is cut to himself at his counter, hood to counter top, since
    the hub's own stall stands round him."""
    src = art('hub_folk')
    rows = PA.segment(src, [2, 2])
    g1, g2 = rows[0]
    m1, m2 = rows[1]
    sg = 31.0 / (g1[3] - g1[1])
    out = {'sage_1': PA.place(src, g1, 32, 32, sg, 'bottom'), 'sage_2': PA.place(src, g2, 32, 32, sg, 'bottom')}
    for name, c in (('merchant_1', m1), ('merchant_2', m2)):
        ox, oy = c[0], c[1]
        box = (ox + 184, oy + 87, ox + 494, oy + 417)
        cell = (box[0], box[1], box[2], box[3], box)
        out[name] = PA.place(src, cell, 32, 32, 31.0 / (box[3] - box[1]), 'bottom')
    return out


def portraits():
    """The dialogue faces, 32x32, from portraits.png: a 3x3 grid in the
    spec's order, Sister Mary Grace and Brother Mark last. Each cell is cut
    to a square on the head (the middle of the figure's upper part; the
    Peddler's face is right of his pack) and keeps a palette of its own."""
    src = art('portraits')
    cells = PA.flat(PA.segment(src, [3, 3, 3], smooth=25))
    names = ['hero', 'hero_surprised', 'peddler', 'gatekeeper', 'hermit', 'nun', 'gardener',
             'sister_mary_grace', 'brother_mark']
    across = {'peddler': 0.72}
    out = {}
    for n, c in zip(names, cells):
        x0, y0, x1, y1, _ = c
        side = y1 - y0
        cx = x0 + (x1 - x0) * across[n] if n in across else PA.head_x(src, c, 0.6)
        out[n] = PA.place(src, c, 32, 32, 32.0 / side, 'bottom', anchor_x=cx)
    return out


# -------------------------------------------------------------- the pack --
def main():
    man = json.load(open(os.path.join(PACK, 'manifest.json')))
    meta = {'revision': man.get('revision', ''), 'groups': {}, 'sheets': {}, 'tiles': {}}
    strips = {}
    for s in man['sheets']:
        name, w, h = s['name'], s['frame_width'], s['frame_height']
        frames = [RENAME.get(name, {}).get(f, f) for f in s['frames']]
        im = Image.open(os.path.join(PACK, s['png_path']))
        assert im.mode == 'P', (name, im.mode)
        assert im.size == (w * len(frames), h), (name, im.size)
        assert max(im.getextrema()) <= 15, (name, 'index above 15')
        raw = im.getpalette()[:48]
        pal = [tuple(raw[i * 3:i * 3 + 3]) for i in range(1, 16)]
        a = np.array(im)
        strips[name] = {'group': s['group'], 'w': w, 'h': h, 'pal': pal,
                        'frames': {f: a[:, i * w:(i + 1) * w].astype(np.uint8) for i, f in enumerate(frames)}}

    # stage 2: the illustrated sheets, by group
    shield, shield_up = shields()
    drawn = {
        'hero': ('hero', bloom()),
        'shield': ('gear', shield), 'shield_upgraded': ('gear', shield_up),
        'items': ('items', items16()),
        'pick32': ('pick', pickups()),
        'icon32': ('icons', icons()),
        'npc': ('folk', folk()),
        'folk32': ('folk32', hub_folk()),
    }
    # the strips left in the hero group go with the shields
    for name in ('sword', 'shield_menu'):
        st = strips[name]
        drawn[name] = ('gear', {k: PA.indexed_to_rgba(v, st['pal']) for k, v in st['frames'].items()})
    groups = {}
    for name, (group, frames) in drawn.items():
        groups.setdefault(group, []).extend(frames.values())
    pals = {g: PA.derive(fr) for g, fr in groups.items()}
    sheets = {}
    for name, (group, frames) in drawn.items():
        any_f = next(iter(frames.values()))
        sheets[name] = {'group': group, 'w': any_f.shape[1], 'h': any_f.shape[0],
                        'frames': {k: PA.quantize(v, pals[group]) for k, v in frames.items()}}
    por = portraits()
    ppal = {k: PA.derive([v]) for k, v in por.items()}
    sheets['portrait'] = {'group': 'portrait', 'w': 32, 'h': 32,
                          'frames': {k: PA.quantize(v, ppal[k]) for k, v in por.items()}}
    pals['portrait'] = ppal['hero']
    meta['portrait_palettes'] = {k: hexes(v) for k, v in ppal.items()}

    # stage 1 for everything else
    for name, st in strips.items():
        if name in sheets:
            continue
        if name in TILE_SHEETS:
            meta['tiles'][name] = {'w': st['w'], 'h': st['h'], 'frames': list(st['frames']), 'palette': hexes(st['pal'])}
            continue
        g = st['group']
        assert g not in pals or hexes(pals[g]) == hexes(st['pal']), (name, 'group colours changed', g)
        pals[g] = st['pal']
        sheets[name] = {'group': g, 'w': st['w'], 'h': st['h'], 'frames': st['frames']}

    # write
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'tiles'))

    def strip_png(path, frames, w, h, pal):
        names = list(frames)
        a = np.zeros((h, w * len(names)), np.uint8)
        for i, n in enumerate(names):
            a[:, i * w:(i + 1) * w] = frames[n]
        im = Image.fromarray(a, 'P')
        pl = [255, 0, 255] + [v for c in pal for v in c]
        im.putpalette(pl + [0] * (48 - len(pl)))  # sixteen colours, as the pack's own strips
        im.save(path, transparency=0)
        return names

    for name, s in sheets.items():
        names = strip_png(os.path.join(OUT, name + '.png'), s['frames'], s['w'], s['h'], pals[s['group']])
        meta['sheets'][name] = {'group': s['group'], 'w': s['w'], 'h': s['h'], 'frames': names}
    for name in meta['tiles']:
        st = strips[name]
        strip_png(os.path.join(OUT, 'tiles', name + '.png'), st['frames'], st['w'], st['h'], st['pal'])
    meta['groups'] = {g: hexes(p) for g, p in pals.items()}
    json.dump(meta, open(os.path.join(OUT, 'pack.json'), 'w'), indent=1, sort_keys=True)
    print('art/pack: %d sprite sheets in %d groups (%d from the illustrated sheets), %d tile sheets'
          % (len(meta['sheets']), len(meta['groups']), len(drawn) + 1, len(meta['tiles'])))


if __name__ == '__main__':
    main()
