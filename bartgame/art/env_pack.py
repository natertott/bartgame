"""The environment art pack, V3 (art/ref/pack_v3/, kept as delivered):
every background tile of the wood, the mystery rooms and the Drain, one
PNG per entry of the first tile spec (117 entries), in twelve palette
groups of fifteen colours. apply() lays them over the metatiles last, in
both builds, index for index: every pixel is one of its group's colours
exactly (checked), so the tiles are the pack's to the pixel.

A PNG holds an entry's tiles left to right (variants; a family of fifteen
in the order 1..15; a piece row by row) and its animation frames as
further rows below. Overlay entries and a tree's crown rows keep their
transparent pixels; every ground tile is opaque (checked).

What the game lays that the first spec had no entry for takes the art of
a pack tile (DERIVED): the hall's wider pieces are the pack's single
tiles repeated, a mystery room's crown is its wall and its floor's edges
its floor. What the game no longer lays takes a plain pack tile of its
area (SPARE), so it costs no palette and hardly a piece."""
import json
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, 'ref', 'pack_v3')
MANIFEST = json.load(open(os.path.join(REF, 'manifest.json')))
ASSETS = {a['key']: a for a in MANIFEST['assets']}
PREFIX = 'v3_'   # the pack's groups share names with the painted ones


def fam(pre):
    return [pre + '%x' % m for m in range(1, 16)]


def run(pre, n):
    return ['%s_%d' % (pre, i) for i in range(n)]


# key: (shape, the metatiles it draws in delivery order), as the first
# tile spec (tools/tile_spec, Oct 2026) gave them to the artist
ENTRIES = {
    'grass': (('vars', 3), ['moss0', 'moss1', 'moss2']),
    'grass_stain': (('vars', 2), ['moss_blight', 'moss_blight2']),
    'flowers': (('vars', 2), ['moss_flowers', 'moss_flowers2']),
    'tall_grass': (('one',), ['tall_grass']),
    'bones': (('one',), ['bones']),
    'trail': (('one',), ['path']),
    'flagstone': (('one',), ['mossy_stone']),
    'meadow': (('piece', 3, 3), run('meadow', 9)),
    'clover': (('piece', 2, 2), run('clover', 4)),
    'fairy_ring': (('piece', 2, 2), run('shroomring', 4)),
    'trail_edge': (('fam', 'side'), fam('pedge_')),
    'shore': (('fam', 'side'), fam('shore_')),
    'shore_corner': (('fam', 'corner'), fam('shore_c')),
    'verge': (('fam', 'side'), fam('verge_')),
    'water': (('one',), ['water']),
    'water_bank': (('fam', 'side'), fam('water_')),
    'water_nick': (('fam', 'corner'), fam('water_c')),
    'lily': (('one',), ['water_lily']),
    'lily_raft': (('piece', 2, 2), run('raft', 4)),
    'waterfall': (('one',), ['waterfall']),
    'foam': (('one',), ['water_foam']),
    'canopy': (('vars', 2), ['canopy', 'canopy2']),
    'canopy_glint': (('one',), ['canopy_glint']),
    'canopy_lantern': (('one',), ['canopy_lantern']),
    'canopy_face': (('one',), ['canopy_s']),
    'canopy_crown': (('one',), ['canopy_n']),
    'canopy_sick': (('one',), ['canopy_blight']),
    'canopy_sick_lit': (('one',), ['canopy_blight2']),
    'tree': (('piece', 2, 3), ['tree_top_nw', 'tree_top_ne', 'tree_mid_w', 'tree_mid_e', 'tree_trunk_w', 'tree_trunk_e']),
    'tree_lantern': (('piece', 2, 3), run('tree2', 6)),
    'great_tree': (('piece', 3, 4), run('gtree', 12)),
    'great_tree_2': (('piece', 3, 4), run('gtree2', 12)),
    'blight_tree': (('piece', 2, 3), run('btree', 6)),
    'bush': (('one',), ['bush']),
    'stone_small': (('one',), ['rock_small']),
    'boulder': (('one',), ['boulder']),
    'rocks': (('vars', 3), ['rock', 'rock2', 'rock3']),
    'stump': (('one',), ['stump']),
    'log': (('one',), ['log']),
    'hollow_log': (('piece', 2, 1), ['hlog_0', 'hlog_1']),
    'great_boulder': (('piece', 2, 2), run('gboulder', 4)),
    'tree_rock': (('piece', 2, 2), run('treerock', 4)),
    'pillar': (('one',), ['pillar']),
    'ruin_wall': (('one',), ['ruin_wall']),
    'statue': (('one',), ['statue']),
    'lantern_post': (('one',), ['lantern_post']),
    'thorns': (('one',), ['thorn']),
    'cliff': (('vars', 3), ['ledge_s_w', 'ledge_s', 'ledge_s_e']),
    'bridge': (('one',), ['bridge']),
    'bridge_ns': (('one',), ['bridge_v']),
    'pit': (('one',), ['pit']),
    'crack': (('one',), ['crack']),
    'web': (('one',), ['web']),
    'door_locked': (('one',), ['door_locked']),
    'door_open': (('one',), ['door_open']),
    'stairs': (('one',), ['stairs_down']),
    'chest': (('vars', 2), ['chest', 'chest_open']),
    'censer': (('one',), ['torch']),
    'censer_lit': (('one',), ['torch_lit']),
    'mouths': (('vars', 3), ['mouth_cave', 'mouth_hollow', 'mouth_thicket']),
    'blight_ground': (('vars', 2), ['blight_ground0', 'blight_ground1']),
    'blight_ground_lit': (('one',), ['blight_ground2']),
    'blight_floor': (('one',), ['blight_floor']),
    'blight_floor_pits': (('one',), ['blight_floor2']),
    'blight_vein': (('one',), ['blight_vein']),
    'blight_pool': (('one',), ['blight_pool']),
    'crystal': (('one',), ['blight_crystal']),
    'dead_tree': (('one',), ['dead_tree']),
    'blight_wall': (('vars', 2), ['blight_wall', 'blight_wall2']),
    'blight_wall_lit': (('one',), ['blight_wall_lit']),
    'sparkle': (('one',), ['sparkle']),
    'sparkle_white': (('one',), ['sparkle_white']),
    'mist': (('one',), ['blight_mist']),
    'cave': (('vars', 7), ['cave_wall', 'cave_face', 'cave_floor0', 'cave_floor1', 'cave_prop', 'cave_glow', 'cave_exit']),
    'hollow': (('vars', 7), ['hollow_wall', 'hollow_face', 'hollow_floor0', 'hollow_floor1', 'hollow_prop', 'hollow_glow', 'hollow_exit']),
    'thicket': (('vars', 7), ['thicket_wall', 'thicket_face', 'thicket_floor0', 'thicket_floor1', 'thicket_prop', 'thicket_glow', 'thicket_exit']),
    'plate': (('vars', 2), ['myst_switch', 'myst_switch_down']),
    'pot': (('one',), ['myst_pot']),
    'room_chest': (('vars', 2), ['myst_chest', 'myst_chest_open']),
    'spring': (('one',), ['myst_spring']),
    'd_floor': (('vars', 3), ['sw_floor0', 'sw_floor1', 'sw_floor2']),
    'd_grime': (('vars', 2), ['sw_floor_grime', 'sw_floor_grime2']),
    'd_crack': (('vars', 2), ['sw_floor_crack', 'sw_floor_crack2']),
    'd_moss': (('vars', 2), ['sw_floor_moss', 'sw_floor_moss2']),
    'd_puddle': (('one',), ['sw_floor_puddle']),
    'd_bones': (('one',), ['sw_floor_bones']),
    'd_shroom': (('one',), ['sw_floor_shroom']),
    'd_drip': (('one',), ['sw_floor_drip']),
    'd_wall_top': (('vars', 2), ['sw_wall_top', 'sw_wall_top_moss']),
    'd_wall': (('one',), ['sw_wall']),
    'd_wall_marks': (('vars', 7), ['sw_wall_slime', 'sw_wall_crack', 'sw_wall_moss', 'sw_wall_chain', 'sw_wall_tally', 'sw_wall_skull', 'sw_wall_rust']),
    'd_wall_drip': (('one',), ['sw_wall_drip']),
    'd_wall_web': (('vars', 2), ['sw_wall_web', 'sw_wall_web_r']),
    'd_wall_fungus': (('one',), ['sw_wall_fungus']),
    'd_wall_window': (('one',), ['sw_wall_window']),
    'd_pipes': (('vars', 2), ['sw_pipe', 'sw_pipe_h']),
    'd_banners': (('vars', 2), ['sw_banner_teal', 'sw_banner_red']),
    'd_lantern': (('one',), ['sw_lantern']),
    'd_torch': (('one',), ['sw_torch_lit']),
    'd_hole': (('one',), ['sw_hole']),
    'd_waterfall': (('one',), ['sw_waterfall']),
    'd_arch': (('one',), ['sw_arch']),
    'd_water': (('one',), ['sw_water']),
    'd_water_marks': (('vars', 3), ['sw_water_scum', 'sw_water_glint', 'sw_lilypad']),
    'd_bubble': (('one',), ['sw_water_bubble']),
    'd_bank_above': (('vars', 2), ['sw_water_edge_n', 'sw_water_edge_n_moss']),
    'd_bank_below': (('vars', 2), ['sw_water_edge_s', 'sw_water_edge_s_moss']),
    'd_grate': (('one',), ['sw_grate']),
    'd_ladder': (('one',), ['sw_ladder_down']),
    'd_drain': (('piece', 2, 2), ['sw_drain_nw', 'sw_drain_ne', 'sw_drain_sw', 'sw_drain_se']),
    'd_rug': (('piece', 2, 2), ['sw_rug_nw', 'sw_rug_ne', 'sw_rug_sw', 'sw_rug_se']),
    'd_awning': (('piece', 2, 1), ['sw_awning_l', 'sw_awning_r']),
    'd_counter': (('one',), ['sw_counter']),
    'd_props': (('vars', 5), ['sw_barrel', 'sw_crate', 'sw_skull', 'sw_gold', 'sw_rubble']),
    'd_pot': (('one',), ['sw_pot']),
    'd_candles': (('one',), ['sw_candles']),
    'd_glints': (('vars', 3), ['sw_glint', 'sw_glint2', 'sw_glint3']),
}

STYLES = ('cave', 'hollow', 'thicket')
# metatile: (key, tile of the entry) for what the first spec had no entry for
DERIVED = {
    'sw_arch_r': ('d_wall', 0),          # the hall's arch is one tile wide
    'sw_grate_r': ('d_grate', 0),        # the grate tiles every way
    'sw_counter_r': ('d_counter', 0),    # the counter repeats left-right
}
DERIVED.update({'sw_fall_%d' % i: ('d_waterfall', 0) for i in range(6)})
for _st in STYLES:
    DERIVED['%s_crown' % _st] = (_st, 0)                       # the wall
    DERIVED.update({'%s_edge_%x' % (_st, m): (_st, 2) for m in range(1, 16)})  # the floor
    DERIVED['%s_floor_switch' % _st] = (_st, 2)
    DERIVED['%s_floor_chest' % _st] = (_st, 2)
    DERIVED['%s_floor_lift' % _st] = (_st, 3)
# no longer laid: the painted rot and corner nicks, the atlas's 3x4
# blighted tree, the per-style springs (the spring is the pack's overlay)
SPARE_FOREST = ('grass', 0)
SPARE_DRAIN = ('d_floor', 0)
SPARE_NAMED = {'pit_inner': ('pit', 0), 'ledge_n': ('cliff', 1), 'path_edge_n': ('trail', 0)}
SPARE_NAMED.update({n: ('trail', 0) for n in fam('pedge_c')})
for _st in STYLES:
    SPARE_NAMED['%s_spring' % _st] = (_st, 2)


def _palette(group):
    cols = [tuple(a['palette_png_rgba_colors']) for a in MANIFEST['assets'] if a['group'] == group]
    assert len(set(cols)) == 1, ('one palette a group', group)
    assert cols[0][0] == 'transparent' and len(cols[0]) == 16, group
    return list(cols[0][1:])


GROUPS = {PREFIX + g: ['#000000'] + _palette(g) for g in sorted({a['group'] for a in MANIFEST['assets']})}


def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def _cols_rows(shape):
    if shape[0] == 'piece':
        return shape[1], shape[2]
    if shape[0] == 'fam':
        return 15, 1
    if shape[0] == 'vars':
        return shape[1], 1
    return 1, 1


_CUT = {}


def cut(key):
    """the entry's tiles in delivery order, each a list of frames, each 16
    rows of hex digits (0 transparent)"""
    if key in _CUT:
        return _CUT[key]
    shape, mts = ENTRIES[key]
    a = ASSETS[key]
    im = Image.open(os.path.join(REF, 'assets', a['path'])).convert('RGBA')
    cols, rows = _cols_rows(shape)
    nf = a['frame_count']
    assert im.size == (cols * 16, rows * 16 * nf), (key, im.size, cols, rows, nf)
    assert len(mts) == cols * rows, (key, len(mts), cols * rows)
    lut = {_rgb(h): i + 1 for i, h in enumerate(_palette(a['group']))}
    px = im.load()
    crown_rows = rows - 1 if shape[0] == 'piece' and a['layer'].startswith('crown') else 0
    overlay = a['layer'].startswith('overlay')
    out = []
    for t in range(cols * rows):
        c, r = t % cols, t // cols
        frames = []
        for f in range(nf):
            lines = []
            for y in range(16):
                line = ''
                for x in range(16):
                    p = px[c * 16 + x, f * rows * 16 + r * 16 + y]
                    if p[3] == 0:
                        assert overlay or r < crown_rows, ('a ground tile is opaque', key, t, x, y)
                        line += '0'
                    else:
                        assert p[3] == 255 and p[:3] in lut, ('a colour of its group', key, p)
                        line += '%x' % lut[p[:3]]
                lines.append(line)
            frames.append(lines)
        out.append(frames)
    _CUT[key] = out
    return out


def _put(m, key, tile):
    import palettes  # here: palettes reads this module's groups
    a = ASSETS[key]
    frames = cut(key)[tile]
    m['pal'] = palettes.MERGE.get(PREFIX + a['group'], PREFIX + a['group'])
    if len(frames) > 1:
        m['frames'] = frames
        m.pop('art', None)
        m['anim_speed'] = a['frame_duration_60ths'] or 20
    else:
        m['art'] = frames[0]
        m.pop('frames', None)


def apply(metatiles):
    by = {m['name']: m for m in metatiles}
    assert set(ENTRIES) == set(ASSETS), sorted(set(ENTRIES) ^ set(ASSETS))
    laid = set()
    for key, (shape, mts) in ENTRIES.items():
        for i, n in enumerate(mts):
            _put(by[n], key, i)
            laid.add(n)
    for n, (key, tile) in DERIVED.items():
        _put(by[n], key, tile)
        laid.add(n)
    for m in metatiles:
        n = m['name']
        if n in laid:
            continue
        key, tile = SPARE_NAMED.get(n) or (SPARE_DRAIN if n.startswith('sw_') else SPARE_FOREST)
        _put(m, key, tile)
    # the black that fills outside a room: the darkest of the wood's ground
    by['black']['art'] = ['1' * 16] * 16
    by['black'].pop('frames', None)
