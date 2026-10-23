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
    for y, row in enumerate(rows):
        assert len(row) == w * 2, 'room row %d has %d chars, want %d' % (y, len(row), w * 2)
        for x in range(w):
            code = row[x * 2:x * 2 + 2]
            name = LEGEND[code]
            out.append(0xFFFF if name is None else mt_names[name])
    return out


# The Drain: a vaulted hall. A waterfall pours from the top wall into a
# basin; the drain hole up to the wood is beside it. The Peddler's stall
# stands under a red awning on the left, the Gatekeeper's rug glows on
# the right. A channel crosses the hall with a grate bridge, the great
# round drain lies below it, and ladders go down into the pools in the
# lower corners.
room('sewer_main', '''
TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
WWWWPPWWWWLNWWBTWWHHWWWWWFWFWFWWWWBRWWLNWWWWPHPHPHWWttWWWWWW
WWWWWWWSWWWWWWWWWW..WWWWWFWFWFWWWWWWWWWWWWWWWWWWWWWSWWWWWWWW
..,,A1A2A1A2..;;..,,..;;~~~~~~..,,..;;..,,..;;..,,BB..;;..,,
,,CRCCCCCCCC..,,GD..,,..ESESES..;;..,,BB..R1R2..CN..,,..;;..
;;SK..PT....,,..;;..,,..;;..,,..,,..;;..,,R3R4..,,..;;..,,PT
..,,..;;..,,CN..,,..;;..,,..;;..;;..,,..;;..,,..CR..,,..;;..
,,..;;..,,..;;..,,RR..,,..;;..,,..;;..,,..;;..,,..;;..,,..,,
WEWEWEWEWEWEWEWEWEWEWEWEWEWEGGGGWEWEWEWEWEWEWEWEWEWEWEWEWEWE
~~~~LP~~~~~~~~~~~~LP~~~~~~~~GGGG~~~~~~~~LP~~~~~~~~~~~~~~LP~~
~~~~~~~~~~LP~~~~~~~~~~~~~~~~GGGG~~~~~~~~~~~~~~LP~~~~~~~~~~~~
ESESESESESESESESESESESESESESGGGGESESESESESESESESESESESESESES
..,,..;;..,,..;;..,,..;;..,,..;;..,,..;;..,,..;;..,,..;;..,,
,,..;;..,,GD..;;..CN..;;D1D2..,,PT;;..,,..;;..,,..;;RR..,,..
WELDWEWE..,,..;;..,,..;;D3D4..;;..,,..;;..,,..;;WEWEWELDWE..
~~~~~~~~,,..;;..,,..;;..,,..;;..,,..;;..,,SK..,,~~~~~~~~~~..
~~~~~~~~..;;..,,..;;..,,..;;..,,..;;..,,..;;..,,~~~~~~~~~~,,
WWWWWWWWWWWWttWWWWWWWWWWWWWWAAWWWWWWWWWWWWWWWWttWWWWWWWWWWWW
''', objects=[
    (OBJ_SPAWN, 12, 15, 0),
    (OBJ_EXIT, 9, 1, 1),        # the drain hole: up to the wood
    (OBJ_NPC, 21, 4, 0),        # the Pale Gatekeeper on the rug
    (OBJ_SHOP, 4, 4, 0),        # the Billious Peddler behind the counter
])
