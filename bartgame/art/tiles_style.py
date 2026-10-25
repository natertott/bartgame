"""The boards' tiles into the metatiles: the sampled art of style.py
replaces the hand-drawn art by name, and what is not sampled is
remapped into the boards' palettes. apply() is called at the end of
tiles.py, so every reader of METATILES sees the result."""
import palettes
import style as ST

F = ST.FOREST_SRC
S = ST.SEWER_SRC
P = S['props']


def slab(rows, x, y, w, h):
    return [r[x:x + w] for r in rows[y:y + h]]


def crown_masked(rows, cx, cy, rx, ry):
    """the overlay rows of a tree: clear outside an ellipse round the crown"""
    out = []
    for y, r in enumerate(rows):
        o = ''
        for x, ch in enumerate(r):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            o += ch if dx * dx + dy * dy <= 1.0 else '.'
        out.append(o)
    return out


def shifted(rows, dy):
    """the rows moved down by dy, wrapping (for a falling water frame)"""
    return rows[-dy:] + rows[:-dy] if dy else rows


def tree_pieces(rows48):
    """a 32x48 tree: four crown tiles masked round an ellipse, two trunk tiles"""
    crown = crown_masked(rows48[:32], 16, 15, 16, 16)
    return {
        'nw': slab(crown, 0, 0, 16, 16), 'ne': slab(crown, 16, 0, 16, 16),
        'sw': slab(crown, 0, 16, 16, 16), 'se': slab(crown, 16, 16, 16, 16),
        'tw': slab(rows48, 0, 32, 16, 16), 'te': slab(rows48, 16, 32, 16, 16),
    }


TREE = tree_pieces(F['tree48'])
TREE2 = tree_pieces(F['tree2_48'])
BTREE = tree_pieces(F['blight_tree'])
WF = slab(S['waterfall'], 8, 12, 16, 16)
WF2 = slab(S['waterfall'], 8, 20, 16, 16)
FWF = slab(F['waterfall'], 0, 0, 16, 16)

# name -> (palette, art or [frames])
REPLACE = {
    'moss0': ('forest', F['grass']), 'moss1': ('forest', F['grass2']), 'moss2': ('forest', F['grass3']),
    'moss_shade': ('forest', F['grass2']), 'path': ('forest', F['path']),
    'moss_flowers': ('forest', F['flowers_white']), 'moss_flowers2': ('cliff', F['flowers_blue']),
    'tall_grass': ('forest', F['grass_tuft']), 'stump': ('forest', F['stump']),
    'canopy': ('wood', F['canopy']), 'canopy2': ('wood', F['canopy2']), 'canopy_s': ('wood', F['canopy2']), 'canopy_n': ('wood', F['canopy']),
    'bush': ('wood', F['bush']), 'log': ('wood', slab(F['log'], 0, 0, 16, 16)),
    'hlog_0': ('wood', slab(F['log'], 0, 0, 16, 16)), 'hlog_1': ('wood', slab(F['log'], 16, 0, 16, 16)),
    'tree_top_nw': ('wood', TREE['nw']), 'tree_top_ne': ('wood', TREE['ne']), 'tree_mid_w': ('wood', TREE['sw']), 'tree_mid_e': ('wood', TREE['se']),
    'tree_trunk_w': ('forest', TREE['tw']), 'tree_trunk_e': ('forest', TREE['te']),
    'tree2_0': ('wood', TREE2['nw']), 'tree2_1': ('wood', TREE2['ne']), 'tree2_2': ('wood', TREE2['sw']), 'tree2_3': ('wood', TREE2['se']),
    'tree2_4': ('forest', TREE2['tw']), 'tree2_5': ('forest', TREE2['te']),
    'bridge': ('cliff', slab(F['bridge'], 0, 0, 16, 16)), 'bridge_v': ('cliff', slab(F['bridge_v'], 0, 0, 16, 16)),
    'rock': ('cliff', F['rock']), 'rock_small': ('cliff', F['rock_small']), 'pillar': ('cliff', slab(F['post'], 0, 0, 16, 16)),
    'water': ('stone', [F['water'], F['water2']]), 'water_lily': ('stone', [F['lily'], F['lily']]),
    'waterfall': ('stone', [FWF, shifted(FWF, 5), shifted(FWF, 10)]),
    'ledge_s': ('cliff', slab(F['cliff'], 0, 0, 16, 16)), 'ledge_s_w': ('cliff', slab(F['cliff2'], 0, 0, 16, 16)), 'ledge_s_e': ('cliff', slab(F['cliff2'], 16, 0, 16, 16)),
    'chest': ('stone', F['chest']),
    'blight_ground0': ('blight', F['blight_grass']), 'blight_ground1': ('blight', F['blight_grass2']),
    'blight_ground2': ('blight', [F['blight_grass'], F['blight_grass2']]), 'blight_floor': ('blight', F['blight_grass2']),
    'blight_vein': ('blight', [F['blight_path'], F['blight_path']]), 'blight_crystal': ('blight', F['blight_crystal']),
    'dead_tree': ('blight', F['dead_tree_small']),
    'blight_wall': ('blight', slab(F['blight_wall'], 0, 0, 16, 16)), 'blight_wall2': ('blight', slab(F['blight_wall2'], 0, 0, 16, 16)),
    'btree_0': ('blight', BTREE['nw']), 'btree_1': ('blight', BTREE['ne']), 'btree_2': ('blight', BTREE['sw']), 'btree_3': ('blight', BTREE['se']),
    'btree_4': ('blight', BTREE['tw']), 'btree_5': ('blight', BTREE['te']),
    'canopy_blight': ('blight', F['blight_canopy']), 'blight_pool': ('blight', [F['blight_water'], F['blight_water']]),
    'sw_floor0': ('sewer', S['floor']), 'sw_floor1': ('sewer', S['floor2']), 'sw_floor2': ('sewer', S['floor_moss']),
    'sw_wall': ('sewer', S['wall']), 'sw_wall_top': ('sewer', S['wall_top']),
    'sw_water': ('sewer', [S['water'], S['water2']]), 'sw_waterfall': ('sewer', [WF, WF2]),
    'sw_pipe': ('sewer', slab(S['pipe_v'], 0, 0, 16, 16)), 'sw_pipe_h': ('sewer', slab(S['pipe_h'], 0, 0, 16, 16)),
    'sw_grate': ('sewer', S['grate16']),
    'sw_drain_nw': ('sewer', slab(S['drain'], 0, 0, 16, 16)), 'sw_drain_ne': ('sewer', slab(S['drain'], 16, 0, 16, 16)),
    'sw_drain_sw': ('sewer', slab(S['drain'], 0, 16, 16, 16)), 'sw_drain_se': ('sewer', slab(S['drain'], 16, 16, 16, 16)),
    'sw_lantern': ('sewer', S['lantern16']), 'sw_banner_teal': ('sewer', S['banner_teal16']), 'sw_banner_red': ('sewer', S['banner_purple16']),
    'sw_ladder': ('sewer', S['ladder16']),
    'sw_crate': ('props', P['crate']), 'sw_barrel': ('props', P['barrel']), 'sw_skull': ('props', P['skull']),
    'sw_candles': ('props', [P['candles'], P['candles']]),
    'sw_awning_l': ('props', slab(P['awning'], 0, 0, 16, 16)), 'sw_awning_r': ('props', slab(P['awning'], 16, 0, 16, 16)),
    'sw_counter': ('props', slab(P['counter'], 0, 0, 16, 16)),
    'sw_rug_nw': ('props', slab(P['rug'], 0, 0, 16, 16)), 'sw_rug_ne': ('props', slab(P['rug'], 16, 0, 16, 16)),
    'sw_rug_sw': ('props', slab(P['rug'], 0, 16, 16, 16)), 'sw_rug_se': ('props', slab(P['rug'], 16, 16, 16, 16)),
    'sw_gold': ('props', P['gold']), 'sw_pot': ('props', P['pot']),
}
SAMPLED = set(REPLACE)


def apply(metatiles):
    for m in metatiles:
        rep = REPLACE.get(m['name'])
        if rep:
            pal, art = rep
            m['pal'] = pal
            if isinstance(art[0], list):
                m['frames'] = art
                m.pop('art', None)
                m.setdefault('anim_speed', 20)
            else:
                m['art'] = art
                m.pop('frames', None)
            continue
        rm = palettes.REMAP_BG.get(m['pal'])
        if not rm:
            continue
        if 'frames' in m:
            m['frames'] = [palettes.remap_rows(f, rm) for f in m['frames']]
        else:
            m['art'] = palettes.remap_rows(m['art'], rm)
