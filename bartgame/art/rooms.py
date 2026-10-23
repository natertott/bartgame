"""Hand-authored rooms (the sewer hub). A room is a grid of two-character
codes, one per metatile, for the ground layer and optionally an overlay
layer. The legend maps codes to metatile names.

Objects: (kind, x_tile, y_tile, arg) bytes, read by the game at load.
"""

LEGEND = {
    '..': 'sw_floor0', ',,': 'sw_floor1', ';;': 'sw_floor2',
    'WW': 'sw_wall', 'TT': 'sw_wall_top', 'WS': 'sw_wall_slime',
    '~~': 'sw_water', 'WE': 'sw_water_edge_n',
    'GG': 'sw_grate', 'PP': 'sw_pipe', 'LL': 'sw_ladder', 'HH': 'sw_hole',
    'tt': 'sw_torch_lit', 'AA': 'sw_arch', 'CC': 'sw_counter', 'RR': 'sw_rubble',
    'SS': 'sw_floor_slime', 'ST': 'stairs_down',
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


# The sewer's main chamber: a vaulted hall, a channel of black water down
# the middle with a grate bridge, torches, the drain hole to the forest at
# the top, the sage by the stairs, the shopkeeper's counter on the right.
room('sewer_main', '''
TTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
WWWWWWWWWWWWWWttWWHHWWttWWWWWW
WWWWWWWSWWWWWW..WW..WW..WWWWWW
WW..,,..;;..,,..;;..,,..;;..WW
WW,,..;;..,,..;;..,,..;;..,,WW
WW..;;..,,..;;..,,..;;..,,..WW
WW;;..,,..;;..,,..;;..,,..;;WW
WW..,,..;;..,,..;;..,,..;;..WW
WWWEWEWEWEWEWEWEGGWEWEWEWEWEWW
WW~~~~~~~~~~~~~~GG~~~~~~~~~~WW
WW~~~~~~~~~~~~~~GG~~~~~~~~~~WW
WW..,,..;;..,,..;;..,,..;;..WW
WW,,..;;..,,..;;..,,..;;..,,WW
WW..;;..,,..SS..,,..;;CCCCCCWW
WWRR..,,..;;SSSS..,,..;;..,,WW
WW..,,..;;..SS..;;..,,..;;..WW
WW,,..;;..,,..;;..,,..;;..,,WW
WWWWWWttWWWWWWWWWWWWWWttWWWWWW
''', objects=[
    (OBJ_SPAWN, 8, 11, 0),
    (OBJ_EXIT, 9, 1, 1),        # the drain hole: to the forest
    (OBJ_NPC, 4, 4, 0),         # the Sage of the Drain
    (OBJ_SHOP, 12, 13, 0),      # the shopkeeper behind the counter
    (OBJ_SIGN, 3, 14, 0),
])
