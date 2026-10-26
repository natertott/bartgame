"""The comparison build's tiles (BART_TILES=pack, `make pack-tiles`): the
sprite pack's own tile sheets (art/pack/tiles/) put into the metatiles
by what they show.

The pack's tiles are a first pass (its README calls them representative
families), so the default build keeps the tiles cut from the style
boards; this build is there to compare. The mapping:

  - one pack tile per metatile where the names agree (grass, path,
    flowers, canopy, oaks, doors, chests, torches, the sewer's floors,
    walls, water, pipes, the stall's props, the blight's ground);
  - the pack's foam-rimmed water (foam_01..15, rims north 1, east 2,
    south 4, west 8, as the engine counts) on the engine's banked water;
    the turf beside the water is plain grass, since the pack draws the
    rim on the water side;
  - path edges built from the four one-sided pack edges;
  - animated metatiles take the pack's frames where it has two or three,
    and hold one where it has one.

Every metatile the pack does not cover keeps its art, remapped colour by
colour into the pack's palette for its area (palettes.PACK_REMAP)."""
import os

from PIL import Image

import pack
import palettes

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pack', 'tiles')


def load(sheet):
    s = pack.META['tiles'][sheet]
    w, h = s['w'], s['h']
    px = Image.open(os.path.join(HERE, sheet + '.png')).load()
    return {n: [''.join('%x' % px[i * w + x, y] if px[i * w + x, y] else '.' for x in range(w)) for y in range(h)]
            for i, n in enumerate(s['frames'])}


T = {s: load(s) for s in pack.META['tiles']}


def hf(rows):
    return [r[::-1] for r in rows]


def vf(rows):
    return rows[::-1]


def pedge(m):
    """a path tile with turf edges on the sides the mask names: each side's
    pixels come from the pack's one-sided edge tile where it differs from
    the plain path"""
    base = T['forest']['path']
    sides = [(1, 'path_edge_n'), (2, 'path_edge_e'), (4, 'path_edge_s'), (8, 'path_edge_w')]
    out = [list(r) for r in base]
    for bit, name in sides:
        if m & bit:
            e = T['forest'][name]
            for y in range(16):
                for x in range(16):
                    if e[y][x] != base[y][x]:
                        out[y][x] = e[y][x]
    return [''.join(r) for r in out]


F, W, S, C, B, SW, P = T['forest'], T['wood'], T['stone'], T['cliff'], T['blight'], T['sewer'], T['props']
WATER = [S['water_1'], S['water_2'], S['water_3']]

# metatile -> art (rows) or frames (a list of rows)
MAP = {
    # the forest floor
    'moss0': F['grass_1'], 'moss1': F['grass_2'], 'moss2': F['grass_3'], 'moss_shade': F['grass_2'],
    'moss_flowers': F['flowers'], 'tall_grass': F['tall_grass'], 'path': F['path'], 'path_edge_n': F['path_edge_n'],
    'clover_0': F['clover'], 'clover_1': F['clover'], 'clover_2': F['clover'], 'clover_3': F['clover'],
    'shroomring_0': F['mushroom_ring'], 'shroomring_1': F['mushroom_ring'],
    'shroomring_2': F['mushroom_ring'], 'shroomring_3': F['mushroom_ring'],
    # the wood
    'canopy': W['canopy_wall_1'], 'canopy2': W['canopy_wall_2'], 'canopy_s': W['canopy_wall_1'], 'canopy_n': W['canopy_wall_2'],
    'canopy_glint': [W['canopy_wall_1'], W['canopy_glint']], 'canopy_lantern': [W['lantern1'], W['lantern2']],
    'lantern_post': [W['lantern1'], W['lantern2']],
    'bush': W['bush_1'], 'log': W['log_h'], 'hlog_0': W['log_h'], 'hlog_1': W['log_h'], 'fence': W['fence_n'], 'thorn': W['thorn_1'],
    'tree_top_nw': W['oak_a_0_0'], 'tree_top_ne': W['oak_a_1_0'], 'tree_mid_w': W['oak_a_0_1'], 'tree_mid_e': W['oak_a_1_1'],
    'tree_trunk_w': W['oak_a_0_2'], 'tree_trunk_e': W['oak_a_1_2'],
    'tree2_0': W['oak_b_0_0'], 'tree2_1': W['oak_b_1_0'], 'tree2_2': W['oak_b_0_1'], 'tree2_3': W['oak_b_1_1'],
    'tree2_4': W['oak_b_0_2'], 'tree2_5': W['oak_b_1_2'],
    # water, ruins, the cliffs
    'water': WATER, 'water_lily': [S['lily'], S['lily']], 'waterfall': [S['waterfall_1'], S['waterfall_2']],
    'raft_0': [S['raft'], S['raft']], 'raft_1': [S['raft'], S['raft']], 'raft_2': [S['raft'], S['raft']], 'raft_3': [S['raft'], S['raft']],
    'door_locked': S['door_locked'], 'door_open': S['door_open'], 'chest': S['chest_closed'], 'chest_open': S['chest_open'],
    'torch': S['torch_2'], 'torch_lit': [S['torch_1'], S['torch_2']], 'crack': S['crack'], 'web': S['web'],
    'statue': S['statue'], 'stairs_down': S['stairs'], 'mossy_stone': S['moss_brick'],
    'ledge_s': C['ledge_s'], 'ledge_n': C['ledge_n'], 'ledge_s_w': C['ledge_s_end_l'], 'ledge_s_e': C['ledge_s_end_r'],
    'rock': C['rock_1'], 'rock2': C['rock_2'], 'rock3': C['rock_3'], 'rock_small': C['rock_3'],
    'boulder': C['boulder_1'], 'pit': C['pit'], 'bridge': C['bridge_h1'], 'bridge_v': C['bridge_v1'],
    # the blight
    'blight_ground0': B['ground_1'], 'blight_ground1': B['ground_2'], 'blight_ground2': [B['ground_3'], B['ground_3']],
    'blight_floor': B['ground_1'], 'blight_floor2': [B['ground_2'], B['ground_2']],
    'blight_vein': [B['vein1'], B['vein2']], 'blight_crystal': B['crystals'],
    'blight_wall': B['wall_plain'], 'blight_wall2': B['wall_plain'], 'blight_wall_lit': [B['wall_lit'], B['wall_lit']],
    'blight_pool': [B['pool_1'], B['pool_2']], 'blight_mist': [B['mist_1'], B['mist_2']], 'dead_tree': B['dead_root'],
    'btree_0': B['blighted_oak_0_0'], 'btree_1': B['blighted_oak_1_0'], 'btree_2': B['blighted_oak_0_1'],
    'btree_3': B['blighted_oak_1_1'], 'btree_4': B['blighted_oak_0_2'], 'btree_5': B['blighted_oak_1_2'],
    # the Drain
    'sw_floor0': SW['floor1'], 'sw_floor1': SW['floor2'], 'sw_floor2': SW['floor3'],
    'sw_floor_grime': SW['grime'], 'sw_floor_grime2': SW['grime'], 'sw_floor_crack': SW['cracks'], 'sw_floor_crack2': SW['cracks'],
    'sw_floor_moss': SW['moss'], 'sw_floor_moss2': SW['moss'], 'sw_floor_puddle': [SW['puddle'], SW['puddle']],
    'sw_floor_bones': SW['bones'], 'sw_floor_shroom': [SW['mushrooms'], SW['mushrooms']], 'sw_floor_drip': [SW['drips'], SW['drips']],
    'sw_wall': SW['wall_plain'], 'sw_wall_crack': SW['wall_crack'], 'sw_wall_moss': SW['wall_moss'], 'sw_wall_chain': SW['wall_chains'],
    'sw_wall_drip': [SW['wall_drips'], SW['wall_drips']], 'sw_wall_web': SW['wall_web'], 'sw_wall_web_r': hf(SW['wall_web']),
    'sw_wall_fungus': [SW['wall_fungus'], SW['wall_fungus']], 'sw_wall_tally': SW['wall_tallies'],
    'sw_wall_window': [SW['wall_window'], SW['wall_window']], 'sw_wall_skull': SW['wall_skull'], 'sw_wall_rust': SW['wall_rust'],
    'sw_water': [SW['water_1'], SW['water_2'], SW['water_3']], 'sw_water_scum': [SW['scum'], SW['scum']],
    'sw_water_bubble': [SW['bubbles'], SW['bubbles']], 'sw_water_glint': [SW['glints'], SW['glints']],
    'sw_water_edge_n': SW['water_edge_n'], 'sw_water_edge_s': SW['water_edge_s'],
    'sw_water_edge_n_moss': SW['water_edge_n'], 'sw_water_edge_s_moss': SW['water_edge_s'],
    'sw_grate': SW['grate'], 'sw_drain_nw': SW['drain_0'], 'sw_drain_ne': SW['drain_1'], 'sw_drain_sw': SW['drain_2'], 'sw_drain_se': SW['drain_3'],
    'sw_pipe': SW['pipe_v'], 'sw_pipe_h': SW['pipe_h'], 'sw_ladder': SW['ladder'], 'sw_ladder_down': SW['ladder'],
    'sw_torch_lit': [SW['torch_1'], SW['torch_2']], 'sw_lantern': SW['lantern_1'],
    'sw_banner_teal': SW['banner2'], 'sw_banner_red': SW['banner1'], 'sw_arch': SW['arch'], 'sw_rubble': SW['rubble'],
    # the stall
    'sw_candles': [P['candle1'], P['candle2']], 'sw_counter': P['counter'], 'sw_awning_l': P['awning_l'], 'sw_awning_r': P['awning_r'],
    'sw_rug_nw': P['rug_0'], 'sw_rug_ne': P['rug_1'], 'sw_rug_sw': P['rug_2'], 'sw_rug_se': P['rug_3'],
    'sw_barrel': P['barrel'], 'sw_crate': P['crate'], 'sw_skull': P['skull'], 'sw_pot': P['pot'], 'sw_gold': P['gold'],
}
for _m in range(1, 16):
    MAP['water_%x' % _m] = S['foam_%02d' % _m]
    MAP['water_c%x' % _m] = WATER
    MAP['shore_%x' % _m] = F['grass_1']
    MAP['shore_c%x' % _m] = F['grass_1']
    MAP['pedge_%x' % _m] = pedge(_m)
for _i in range(9):
    MAP['meadow_%d' % _i] = F['meadow']
SAMPLED = set(MAP)


def _in(rows, src, dst):
    """rows drawn in the pack sheet src's colours, in sheet dst's"""
    a = ['#000000'] + pack.META['tiles'][src]['palette']
    b = ['#000000'] + pack.META['tiles'][dst]['palette']
    return palettes.remap_rows(rows, palettes._remap(a, b))


# The ground layer has nothing under it, so a pack tile with clear pixels
# there is filled with its area's floor; the overlay ('wood') stays clear.
FLOOR = {
    'forest': F['grass_1'], 'stone': _in(F['grass_1'], 'forest', 'stone'), 'cliff': _in(F['grass_1'], 'forest', 'cliff'),
    'blight': B['ground_1'], 'sewer': SW['floor1'], 'props': _in(SW['floor1'], 'sewer', 'props'),
}


def grounded(rows, pal):
    base = FLOOR.get(pal)
    if base is None:
        return rows
    return [''.join(b if c == '.' else c for c, b in zip(r, br)) for r, br in zip(rows, base)]


def apply(metatiles):
    names = {m['name'] for m in metatiles}
    assert SAMPLED <= names, sorted(SAMPLED - names)
    for m in metatiles:
        rep = MAP.get(m['name'])
        if rep is not None:
            if isinstance(rep[0], list):
                m['frames'] = [grounded(f, m['pal']) for f in rep]
                m.pop('art', None)
                m.setdefault('anim_speed', 20)
            else:
                m['art'] = grounded(rep, m['pal'])
                m.pop('frames', None)
            continue
        rm = palettes.PACK_REMAP.get(m['pal'])
        if not rm:
            continue
        if 'frames' in m:
            m['frames'] = [palettes.remap_rows(f, rm) for f in m['frames']]
        else:
            m['art'] = palettes.remap_rows(m['art'], rm)
