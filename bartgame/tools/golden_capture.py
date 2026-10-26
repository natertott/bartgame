"""Capture fixed scenes from the real engine, for comparing art with what the
game draws: the raw 240x160 framebuffer (no scaling, no filter) and a
layout of exactly what is on screen.

    cd bartgame && make && python3 tools/golden_capture.py OUTDIR [SCENE...]

Scenes: drain (the hall at the camera's top left), living (a living room of
the pinned seed), blighted (a blighted room of it). Each SCENE dir gets

    engine_capture_240x160.png         the whole frame: HUD, ground, overlay, sprites
    engine_capture_bg_240x160.png      the room only: BG2 ground and BG1 overlay
    engine_capture_ground_240x160.png  BG2 only
    layout.json                        camera, frame counter, every visible
        16x16 cell (ground and overlay: metatile, pack file and tile,
        frame, palette group and bank, type, collision), the hardware
        8x8 screen entries of BG2 and BG1 read from VRAM, the BG palette
        RAM, the visible sprites read from OAM
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'art'))
import probe as P  # noqa: E402
import critical_path as CP  # noqa: E402
import lift_probe as LP  # noqa: E402
import tiles  # noqa: E402
import palettes  # noqa: E402
import env_pack  # noqa: E402

OUT = sys.argv[1]
SCENES = sys.argv[2:] or ['drain', 'living', 'blighted']
SEED = 0xB4A7
NAMES = [m['name'] for m in tiles.METATILES]
BY = {m['name']: m for m in tiles.METATILES}
ART = {}
for _k, (_, _mts) in env_pack.ENTRIES.items():
    for _i, _n in enumerate(_mts):
        ART[_n] = (_k, _i)
for _n, (_k, _i) in env_pack.DERIVED.items():
    ART[_n] = (_k, _i)
QUARTERS = (('tl', 8), ('tr', 4), ('bl', 2), ('br', 1))
DISPCNT = 0x04000000
MODE0_OBJ1D = 0x0040
BG0, BG1, BG2, OBJ = 0x0100, 0x0200, 0x0400, 0x1000


def rgb555(v):
    r, g, b = v & 31, (v >> 5) & 31, (v >> 10) & 31
    return '#%02x%02x%02x' % ((r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2))


def u16(c, a):
    return P.r16(c, a) & 0xFFFF


def room_grid(c):
    R = P.sym('gRoom')
    w, h = P.r8(c, R), P.r8(c, R + 1)
    layers = []
    for layer in (0, 1):
        base = R + 2 + layer * 2048
        layers.append([[u16(c, base + (y * 32 + x) * 2) for x in range(w)] for y in range(h)])
    return w, h, layers


def screen_entry(c, sb_base, tx, ty):
    """a 64x64-tile BG map is four screenblocks: top left, top right, bottom left, bottom right"""
    sb = sb_base + (ty // 32) * 2 + (tx // 32)
    e = u16(c, 0x06000000 + sb * 0x800 + ((ty % 32) * 32 + tx % 32) * 2)
    return {'piece': e & 0x3FF, 'hflip': bool(e & 0x400), 'vflip': bool(e & 0x800), 'bank': e >> 12}


def cell_info(mt_id, frame_counter, bank_of):
    if mt_id == 0xFFFF:
        return None
    n = NAMES[mt_id]
    m = BY[n]
    frames = len(m['frames']) if 'frames' in m else 1
    speed = m.get('anim_speed') if frames > 1 else None
    coll = m.get('coll', tiles.default_coll(m['type']))
    k = ART.get(n)
    group = palettes.MERGE.get(m['pal'], m['pal'])
    return {'metatile': n, 'id': mt_id, 'type': m['type'],
            'collision_quarters': {q: bool(coll & b) for q, b in QUARTERS},
            'pack_key': k[0] if k else None, 'pack_file': ('assets/' + env_pack.ASSETS[k[0]]['path']) if k else None,
            'tile': k[1] if k else None,
            'frames': frames, 'frame_duration_60ths': speed,
            'frame_shown': (frame_counter // speed) % frames if speed else 0,
            'palette_group': group, 'bank': bank_of.get(group)}


def oam(c):
    out = []
    for i in range(128):
        a0, a1, a2 = (u16(c, 0x07000000 + i * 8 + k) for k in (0, 2, 4))
        if (a0 & 0x0300) == 0x0200 or (a0 & 0x0C00) == 0x0800:   # hidden, or the OBJ window
            continue
        shape, size = a0 >> 14, a1 >> 14
        w, h = [[(8, 8), (16, 16), (32, 32), (64, 64)], [(16, 8), (32, 8), (32, 16), (64, 32)], [(8, 16), (8, 32), (16, 32), (32, 64)]][shape][size]
        y, x = a0 & 0xFF, a1 & 0x1FF
        y = y - 256 if y >= 160 else y
        x = x - 512 if x >= 240 else x
        if x + w <= 0 or y + h <= 0 or x >= 240 or y >= 160:
            continue
        out.append({'slot': i, 'x': x, 'y': y, 'w': w, 'h': h, 'tile': a2 & 0x3FF, 'priority': (a2 >> 10) & 3,
                    'palette': a2 >> 12, 'hflip': bool(a1 & 0x1000), 'vflip': bool(a1 & 0x2000)})
    return out


def capture(c, name, scene, extra):
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    CP.clear_enemies(c)
    P.run(c, 2)
    full = P.r16(c, DISPCNT) & 0xFFFF
    fc = P.r32(c, P.sym('gFrame'))
    cam = (P.r16(c, P.sym('gCamX')), P.r16(c, P.sym('gCamY')))
    P.snap(c, os.path.join(d, 'engine_capture_240x160.png'))
    # the same frame's room, then its ground alone (the layers are set only
    # on a state change, so a write here holds until the next run)
    shots = {}
    for tag, bits in (('bg', BG1 | BG2), ('ground', BG2)):
        P.w16(c, DISPCNT, MODE0_OBJ1D | bits)
        c.run_frame()
        shots[tag] = P.r32(c, P.sym('gFrame'))
        P.snap(c, os.path.join(d, 'engine_capture_%s_240x160.png' % tag))
    P.w16(c, DISPCNT, full)
    w, h, (ground, overlay) = room_grid(c)
    # the palette RAM's BG banks and which group sits in each
    banks = [[rgb555(u16(c, 0x05000000 + (b * 16 + k) * 2)) for k in range(16)] for b in range(16)]
    bank_of = {}
    for g, cols in palettes.BG_PALETTES:
        q = [rgb555(int(x[1:3], 16) >> 3 | (int(x[3:5], 16) >> 3) << 5 | (int(x[5:7], 16) >> 3) << 10) for x in cols]
        for b in range(13):
            if banks[b][1:] == q[1:] and g not in bank_of:
                bank_of[g] = b
    x0, y0 = cam[0] // 16, cam[1] // 16
    x1, y1 = (cam[0] + 239) // 16, (cam[1] + 159) // 16
    cells = []
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            cells.append({'x': x, 'y': y, 'ground': cell_info(ground[y][x], shots['bg'], bank_of),
                          'overlay': cell_info(overlay[y][x], shots['bg'], bank_of)})
    hw = {}
    for bg, sb in (('BG2', 28), ('BG1', 24)):
        tx0, ty0 = cam[0] // 8, cam[1] // 8
        hw[bg] = {'first_tile': [tx0, ty0], 'scroll_px': list(cam),
                  'entries': [[screen_entry(c, sb, tx, ty) for tx in range(tx0, tx0 + 31)] for ty in range(ty0, ty0 + 21)]}
    layout = {
        'scene': name, 'seed': SEED, 'engine_frame_counter': {'full': fc, 'bg': shots['bg'], 'ground': shots['ground']},
        'area': scene['area'], 'room_metatiles': [w, h], 'camera_px': list(cam),
        'view_cells': {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'cell_offset_px': [cam[0] % 16, cam[1] % 16]},
        'how_to_read': {
            'cells': 'every 16x16 room cell touching the 240x160 view; ground is BG2 (opaque), overlay BG1 (index 0 transparent, drawn over sprites of priority 2)',
            'frame_shown': 'the animation frame on screen in the bg capture: (frame counter // frame_duration_60ths) % frames',
            'hardware': 'the 8x8 screen entries actually in VRAM for the 31x21 tiles covering the view, from first_tile, scrolled by scroll_px',
            'bg_palette_ram': 'the 16 BG banks as the hardware holds them (BGR555, shown as 8-bit RGB the way mGBA expands them)',
            'sprites': 'OAM entries on screen in the full capture; priority 2 draws over BG2 and under BG1',
        },
        'cells': cells, 'hardware': hw, 'bg_palette_ram': banks,
        'palette_bank_of_group': bank_of, 'sprites': oam(c),
    }
    layout.update(extra)
    json.dump(layout, open(os.path.join(d, 'layout.json'), 'w'), indent=1)
    print('%s: camera %s, frame %d, %d cells, %d sprites' % (name, cam, fc, len(cells), len(layout['sprites'])))


def settle(c, hx, hy, frames=150):
    CP.heal(c)
    CP.clear_enemies(c)
    CP.teleport(c, hx, hy)
    P.run(c, frames)


def best_window(c):
    """the tile-aligned camera whose view holds the most kinds of tile, with
    floor under the hero at its middle"""
    w, h, (ground, overlay) = room_grid(c)
    best = None
    for cy in range(0, h - 10 + 1):
        for cx in range(0, w - 15 + 1):
            hx, hy = cx + 7, cy + 6
            n = NAMES[ground[hy][hx]]
            if BY[n]['type'] != 'FLOOR' or overlay[hy][hx] != 0xFFFF:
                continue
            kinds = {ground[y][x] for y in range(cy, cy + 10) for x in range(cx, cx + 15)}
            kinds |= {overlay[y][x] for y in range(cy, cy + 10) for x in range(cx, cx + 15)}
            if best is None or len(kinds) > best[0]:
                best = (len(kinds), cx, cy)
    return best[1] * 16, best[2] * 16


for name in SCENES:
    c = P.boot(seed=SEED)
    P.run(c, 40)
    if name == 'drain':
        # the camera at the hall's top left: the stall, the hole, the fall, the channel
        settle(c, 0 + 120, 0 + 104)
        capture(c, name, {'area': 'sewer'}, {'room': 'sewer_main (art/rooms.py)', 'objects': 'OBJ_SPAWN (12,15), OBJ_EXIT the hole (9,1), OBJ_NPC the Gatekeeper (21,4), OBJ_SHOP the Peddler (4,4)'})
        continue
    w = CP.world(c)
    P.enter_forest(c)
    cell = {'living': 11, 'blighted': 13}[name]
    gates = w['cells'][cell]['gate']
    LP.warp(c, cell, [s for s in range(4) if gates[s]][0])
    camx, camy = best_window(c)
    settle(c, camx + 120, camy + 104)
    capture(c, name, {'area': 'forest'}, {'cell': cell, 'stage': w['cells'][cell]['stage'], 'blighted': name == 'blighted'})
