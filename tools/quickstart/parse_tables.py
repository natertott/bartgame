"""Parse every placement-bearing QUICKSTART table straight from source.

The checker validates what will actually compile, so this reads the same
files the build does - no cached JSON, no hand-copied ids.
"""
import re, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AREA_H = open(os.path.join(ROOT, 'include/area.h')).read()
ROOM_H = open(os.path.join(ROOT, 'include/roomid.h')).read()
TRANS = open(os.path.join(ROOT, 'src/data/transitions.c')).read()
GAME = open(os.path.join(ROOT, 'src/game.c')).read()


def _enum(src):
    out = {}
    for blk in re.findall(r'typedef enum \{(.*?)\n\}', src, re.S):
        n = 0
        names = {}
        for line in blk.split('\n'):
            line = re.sub(r'/\*.*?\*/', '', line).split('//')[0].strip().rstrip(',')
            if not line:
                continue
            if '=' in line:
                nm, v = line.split('=', 1)
                nm = nm.strip()
                try:
                    n = int(v.strip(), 0)
                except ValueError:
                    continue
            else:
                nm = line
            if re.match(r'^\w+$', nm):
                names[nm] = n
            n += 1
        if len(names) > len(out):
            out = names
    return out


AREAS = _enum(AREA_H)

ROOMS = {}
cur, n = None, 0
for line in ROOM_H.split('\n'):
    mc = re.match(r'\s*// (AREA_\w+)', line)
    if mc:
        cur = mc.group(1)
        continue
    l2 = re.sub(r'/\*.*?\*/', '', line).split('//')[0].strip().rstrip(',')
    if not l2 or cur is None:
        continue
    if '=' in l2:
        nm, v = l2.split('=', 1)
        nm = nm.strip()
        try:
            n = int(v.strip(), 0)
        except ValueError:
            continue
    else:
        nm = l2
    if re.match(r'^ROOM_\w+$', nm):
        ROOMS.setdefault(nm, n)
        n += 1


def content_sites():
    i = GAME.find('sQuickStartRoomContentSites[QUICKSTART_CONTENT_SITE_COUNT] = {')
    j = GAME.find('\n};', i)
    rows = re.findall(r'\{ (AREA_\w+), (ROOM_\w+), \w+, ([0-9xa-fA-F]+),\s*\n?\s*([0-9xa-fA-F]+)', GAME[i:j])
    return [(an, rn, AREAS[an], ROOMS[rn], int(cx, 0), int(cy, 0)) for an, rn, cx, cy in rows]


def region_pool():
    i = GAME.find('sQuickStartRegionPool[] = {')
    j = GAME.find('\n};', i)
    body = GAME[i:j]
    out = []
    NUM = r'(0x[0-9a-fA-F]+|\d+)'
    for m in re.finditer(
            r'\{ (AREA_\w+), (ROOM_\w+), ' + ', '.join([NUM] * 6) + r',(?:.*?)'
            + NUM + r', ' + NUM + r',\s*\n?\s*(?:QuickStart\w+|NULL) \}', body, re.S):
        an, rn = m.group(1), m.group(2)
        out.append({'areaName': an, 'roomName': rn, 'area': AREAS[an], 'room': ROOMS[rn],
                    'entrance': (int(m.group(3), 0), int(m.group(4), 0)),
                    'exitBox': (int(m.group(5), 0), int(m.group(6), 0), int(m.group(7), 0), int(m.group(8), 0)),
                    'reward': (int(m.group(9), 0), int(m.group(10), 0))})
    return out


POOL_LISTS = {
 ('AREA_CASTOR_CAVES','ROOM_CASTOR_CAVES_DARKNUT'): 'gExitList_CastorCaves_Darknut',
 ('AREA_CRENEL_CAVES','ROOM_CRENEL_CAVES_BRIDGE_SWITCH'): 'gExitList_CrenelCaves_BridgeSwitch',
 ('AREA_CRENEL_CAVES','ROOM_CRENEL_CAVES_CHUCHU_POT_CHEST'): 'gExitList_CrenelCaves_ChuchuPotChest',
 ('AREA_CRENEL_CAVES','ROOM_CRENEL_CAVES_HELMASAUR_HALLWAY'): 'gExitList_CrenelCaves_HelmasaurHallway',
 ('AREA_CRENEL_CAVES','ROOM_CRENEL_CAVES_LADDER_TO_SPRING_WATER'): 'gExitList_CrenelCaves_LadderToSpringWater',
 ('AREA_VEIL_FALLS_CAVES','ROOM_VEIL_FALLS_CAVES_EXIT'): 'gExitList_VeilFallsCaves_Exit',
 ('AREA_VEIL_FALLS_CAVES','ROOM_VEIL_FALLS_CAVES_HALLWAY_SECRET_STAIRCASE'): 'gExitList_VeilFallsCaves_SecretStaircases',
 ('AREA_CRENEL_MINISH_PATHS','ROOM_CRENEL_MINISH_PATHS_MELARI'): 'gExitList_CrenelMinishPaths_MelarisMine',
 ('AREA_CRENEL_MINISH_PATHS','ROOM_CRENEL_MINISH_PATHS_RAIN'): 'gExitList_CrenelMinishPaths_Rainfall',
 ('AREA_MINISH_PATHS','ROOM_MINISH_PATHS_MINISH_VILLAGE'): 'gExitList_MinishPaths_ToMinishVillage',
 ('AREA_VEIL_FALLS_CAVES','ROOM_VEIL_FALLS_CAVES_HALLWAY_RUPEE_PATH'): 'gExitList_VeilFallsCaves_RupeePath',
 ('AREA_HOUSE_INTERIORS_1','ROOM_HOUSE_INTERIORS_1_INN_EAST_2F'): 'gExitList_HouseInteriors1_InnEast2F',
 ('AREA_HOUSE_INTERIORS_1','ROOM_HOUSE_INTERIORS_1_LIBRARY_1F'): 'gExitList_HouseInteriors1_Library1F',
 ('AREA_HOUSE_INTERIORS_1','ROOM_HOUSE_INTERIORS_1_LIBRARY_2F'): 'gExitList_HouseInteriors1_Library2F',
 ('AREA_HOUSE_INTERIORS_1','ROOM_HOUSE_INTERIORS_1_SCHOOL_WEST'): 'gExitList_HouseInteriors1_SchoolWest',
 ('AREA_MINISH_HOUSE_INTERIORS','ROOM_MINISH_HOUSE_INTERIORS_FESTARI'): 'gExitList_MinishHouseInteriors_Festari',
 ('AREA_DARK_HYRULE_CASTLE','ROOM_DARK_HYRULE_CASTLE_3F_TRIPLE_DARKNUT'): 'gExitList_DarkHyruleCastle_3FTripleDarknut',
 ('AREA_DARK_HYRULE_CASTLE_BRIDGE','ROOM_DARK_HYRULE_CASTLE_BRIDGE_MAIN'): 'gExitList_DarkHyruleCastleBridge_Main',
 ('AREA_SANCTUARY_ENTRANCE','ROOM_SANCTUARY_ENTRANCE_MAIN'): 'gExitList_SanctuaryEntrance_Main',
 ('AREA_NULL_61','ROOM_NULL_61_0'): 'gExitList_61_0',
}


def pool_doors():
    out = {}
    for (an, rn), listname in POOL_LISTS.items():
        m = re.search(r'const Transition ' + re.escape(listname) + r'\[\] = \{(.*?)\n\};', TRANS, re.S)
        body = re.sub(r'//.*', '', m.group(1))
        rows = re.findall(
            r'\{\s*(WARP_TYPE_\w+),\s*(0x[0-9a-fA-F]+|\d+),\s*(0x[0-9a-fA-F]+|\d+),'
            r'\s*(0x[0-9a-fA-F]+|\d+),\s*(0x[0-9a-fA-F]+|\d+),\s*(\w+),', body)
        out[(an, rn)] = {
            'area': AREAS[an], 'room': ROOMS[rn],
            'doors': [{'warp': wt, 'sx': int(sx, 0), 'sy': int(sy, 0),
                       'ex': int(ex, 0), 'ey': int(ey, 0), 'shape': sh}
                      for wt, sx, sy, ex, ey, sh in rows[:2]]}
    return out


def site_index_of(area_name, room_name):
    for idx, (an, rn, _a, _r, _x, _y) in enumerate(content_sites()):
        if an == area_name and rn == room_name:
            return idx
    return -1


def pool_rows():
    """The 2-door pool tables: {area, room, ex, ey, dx, dy} per row, resolved
    to numeric ids. Source of truth for the pool-entrance checker tier."""
    out = []
    for m in re.finditer(r'\{ (AREA_\w+), (ROOM_\w+), (-?\d+), (-?\d+), (-?\d+), (-?\d+) \}', GAME):
        an, rn, ex, ey, dx, dy = m.groups()
        if an in AREAS and rn in ROOMS:
            out.append({'areaName': an, 'roomName': rn, 'area': AREAS[an], 'room': ROOMS[rn],
                        'ex': int(ex), 'ey': int(ey), 'dx': int(dx), 'dy': int(dy)})
    return out


def fusers():
    """sQuickStartFusers: {areaName, roomName, area, room, kinstone, x, y}."""
    i = GAME.find('sQuickStartFusers[] = {')
    j = GAME.find('\n};', i)
    rows = re.findall(r'\{ (AREA_\w+), (ROOM_\w+), KINSTONE_([0-9A-F]+), (-?\d+), (-?\d+) \}', GAME[i:j])
    return [{'areaName': an, 'roomName': rn, 'area': AREAS[an], 'room': ROOMS[rn],
             'kinstone': int(k, 16), 'x': int(x), 'y': int(y)}
            for an, rn, k, x, y in rows]
