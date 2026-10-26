"""Hand-authored rooms (the sewer hub). A room is a grid of two-character
codes, one per metatile, for the ground layer and optionally an overlay
layer. The legend maps codes to metatile names.

Objects: (kind, x_tile, y_tile, arg) bytes, read by the game at load.
"""

LEGEND = {
    '..': 'sw_floor0', ',,': 'sw_floor1', ';;': 'sw_floor2', 'SS': 'sw_floor_slime',
    'TT': 'sw_wall_top', 'WW': 'sw_wall', 'WS': 'sw_wall_slime',
    'PP': 'sw_pipe', 'PH': 'sw_pipe_h', 'LN': 'sw_lantern', 'BT': 'sw_banner_teal', 'BR': 'sw_banner_red',
    'tt': 'sw_torch_lit', 'HH': 'sw_hole', 'WF': 'sw_waterfall', 'LL': 'sw_ladder',
    '~~': 'sw_water', 'LP': 'sw_lilypad', 'WE': 'sw_water_edge_n', 'ES': 'sw_water_edge_s',
    'GG': 'sw_grate', 'LD': 'sw_ladder_down',
    'D1': 'sw_drain_nw', 'D2': 'sw_drain_ne', 'D3': 'sw_drain_sw', 'D4': 'sw_drain_se',
    'R1': 'sw_rug_nw', 'R2': 'sw_rug_ne', 'R3': 'sw_rug_sw', 'R4': 'sw_rug_se',
    'CC': 'sw_counter', 'A1': 'sw_awning_l', 'A2': 'sw_awning_r',
    'BB': 'sw_barrel', 'CR': 'sw_crate', 'SK': 'sw_skull', 'GD': 'sw_gold', 'CN': 'sw_candles',
    'RR': 'sw_rubble', 'AA': 'sw_arch', 'ST': 'stairs_down', 'PT': 'sw_pot',
    # the atlas's wider pieces: the arch's and the grate's right halves, the
    # counter's, the waterfall three by two
    'AR': 'sw_arch_r', 'GR': 'sw_grate_r', 'CS': 'sw_counter_r',
    'F1': 'sw_fall_0', 'F2': 'sw_fall_1', 'F3': 'sw_fall_2', 'F4': 'sw_fall_3', 'F5': 'sw_fall_4', 'F6': 'sw_fall_5',
    # grime: stained, cracked, mossed slabs, a puddle, bones, fungus, a drip
    'gr': 'sw_floor_grime', 'g2': 'sw_floor_grime2', 'cr': 'sw_floor_crack', 'c2': 'sw_floor_crack2',
    'ms': 'sw_floor_moss', 'm2': 'sw_floor_moss2', 'pd': 'sw_floor_puddle', 'bn': 'sw_floor_bones',
    'sh': 'sw_floor_shroom', 'dp': 'sw_floor_drip',
    # the bricks: cracked, mossed, chained, dripping, webbed, glowing, scratched, rusted
    'WC': 'sw_wall_crack', 'WM': 'sw_wall_moss', 'CH': 'sw_wall_chain', 'WD': 'sw_wall_drip',
    'W1': 'sw_wall_web', 'W2': 'sw_wall_web_r', 'FU': 'sw_wall_fungus', 'TA': 'sw_wall_tally',
    'WN': 'sw_wall_window', 'SU': 'sw_wall_skull', 'RU': 'sw_wall_rust', 'TM': 'sw_wall_top_moss',
    # the channel: scum, bubbles, glints, mossed banks
    '~s': 'sw_water_scum', '~b': 'sw_water_bubble', '~g': 'sw_water_glint',
    'EM': 'sw_water_edge_n_moss', 'SM': 'sw_water_edge_s_moss',
    # glints, for the overlay layer
    '*1': 'sw_glint', '*2': 'sw_glint2', '*3': 'sw_glint3',
    '  ': None,
}

# object kinds (must match room.h)
OBJ_NPC = 1
OBJ_EXIT = 2   # arg: destination id
OBJ_SPAWN = 3  # player start, arg: facing
OBJ_SHOP = 4
OBJ_SIGN = 5

ROOMS = []


def room(name, ground, overlay=None, objects=()):
    rows = [r for r in ground.strip('\n').splitlines()]
    w = len(rows[0]) // 2
    h = len(rows)
    for i, r in enumerate(rows):
        assert len(r) == w * 2, 'room %s row %d has %d chars, want %d' % (name, i, len(r), w * 2)
    ROOMS.append({'name': name, 'w': w, 'h': h, 'ground': rows,
                  'overlay': [r for r in overlay.strip('\n').splitlines()] if overlay else None,
                  'objects': list(objects)})


def expand(rows, w, h, mt_names):
    out = []
    assert len(rows) == h, 'room has %d rows, want %d' % (len(rows), h)
    if not isinstance(rows[0], str):
        # rows of metatile names (a painted room), None where empty
        for row in rows:
            assert len(row) == w
            out += [0xFFFF if n is None else mt_names[n] for n in row]
        return out
    for y, row in enumerate(rows):
        assert len(row) == w * 2, 'room row %d has %d chars, want %d' % (y, len(row), w * 2)
        for x in range(w):
            code = row[x * 2:x * 2 + 2]
            name = LEGEND[code]
            out.append(0xFFFF if name is None else mt_names[name])
    return out


# The Drain: painted whole (sw_hall.py) and cut into its own cells
# (sw_drain.py). The objects are its own too: where a run begins, the
# drain hole up to the wood, the Gatekeeper on her rug, the Peddler
# behind his counter.
import sw_drain  # noqa: E402
ROOMS.append({'name': 'sewer_main', 'w': sw_drain.W, 'h': sw_drain.H,
              'ground': sw_drain.GROUND, 'overlay': sw_drain.OVERLAY,
              'objects': [(OBJ_SPAWN, 12, 16, 0),
                          (OBJ_EXIT, 9, 2, 1),
                          (OBJ_NPC, 21, 5, 0),
                          (OBJ_SHOP, 4, 5, 0)]})
