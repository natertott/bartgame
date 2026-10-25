"""The style boards, cut into the game: palettes derived from the boards,
sprites and tiles sampled from them. See sample.py for the cutting.
Every box is (left, top, right, bottom) on the named board.
"""
import sample as SM

BG = [(75, 75, 75), (60, 60, 60), (90, 90, 90), (70, 68, 66), (82, 80, 78), (100, 98, 96), (55, 55, 55)]
OUT = (26, 12, 16)

# ------------------------------------------------------------ palettes --
HERO_BIG = (40, 110, 215, 385)
PAL_HERO = [OUT] + SM.derive([('sheets', HERO_BIG)], 14, BG, 40)
PAL_FOLK = [(16, 12, 20)] + SM.derive([('sheets', (788, 118, 872, 206)), ('sheets', (1035, 85, 1235, 385)), ('sheets', (1268, 95, 1328, 180))], 14, BG, 40, spread=True)
# the three board faces, and a skin, a green and a gold for the drawn ones
PAL_PORTRAIT = [(16, 12, 20)] + SM.derive([('ui', (775, 235, 925, 385)), ('ui', (775, 420, 925, 570)), ('sheets', (1078, 112, 1182, 216))], 11, spread=True) + [(232, 200, 160), (46, 128, 64), (240, 192, 64)]
# the forest scene: the palettes come from the very crops the tiles use
F_GRASS, F_PATH, F_TREE, F_FLOWERS, F_BUSH, F_TUFT = (340, 575, 380, 615), (625, 290, 665, 330), (100, 662, 260, 812), (395, 705, 435, 745), (520, 170, 620, 250), (828, 300, 898, 380)
PAL_FOREST = SM.derive([('forest', b) for b in (F_GRASS, F_PATH, F_TREE, F_FLOWERS, F_BUSH, F_TUFT)], 15)
# water, its banks and the cliffs, the bridge, the well
C_WATER, C_BRIDGE, C_ROCK, C_WELL, C_FALL, C_LEDGE, C_BLUE = (400, 255, 440, 295), (350, 330, 480, 395), (1170, 380, 1236, 448), (600, 592, 710, 692), (520, 700, 580, 820), (130, 755, 290, 805), (200, 797, 245, 842)
PAL_CLIFF = SM.derive([('forest', b) for b in (C_WATER, C_BRIDGE, C_ROCK, C_WELL, C_FALL, C_LEDGE, C_BLUE)], 15)
# the blight
B_GRASS, B_BUSH, B_WALL, B_TREE, B_DOOR, B_PATH, B_ROCK = (1290, 305, 1330, 345), (968, 792, 1048, 872), (1098, 190, 1238, 250), (1360, 120, 1500, 300), (1088, 642, 1188, 742), (1050, 752, 1090, 792), (1098, 832, 1158, 892)
PAL_BLIGHT = SM.derive([('forest', b) for b in (B_GRASS, B_BUSH, B_WALL, B_TREE, B_DOOR, B_PATH, B_ROCK)], 15)
# the drain: stone, moss, water, pipes, lanterns, banners
S_WALL, S_FLOOR, S_WATER, S_FALL, S_PIPE, S_LANTERN, S_BANNER_T, S_BANNER_P, S_DRAIN = (812, 575, 868, 631), (540, 580, 604, 644), (140, 650, 204, 714), (705, 120, 800, 300), (28, 310, 76, 406), (490, 85, 560, 175), (550, 150, 620, 300), (908, 150, 978, 300), (660, 640, 870, 780)
PAL_SEWER = SM.derive([('sewer', b) for b in (S_WALL, S_FLOOR, S_WATER, S_FALL, S_PIPE, S_LANTERN, S_BANNER_T, S_BANNER_P, S_DRAIN)], 15)
# its props: the stall, the rug, crates and barrels, candles, skulls
P_CHEST, P_SKULL, P_CANDLES, P_AWNING, P_COUNTER, P_RUG, P_SHELF, P_BARREL, P_CRATE = (188, 428, 272, 510), (95, 410, 150, 470), (1358, 360, 1428, 440), (90, 170, 480, 300), (250, 400, 540, 520), (1100, 465, 1400, 555), (1068, 330, 1178, 470), (1360, 440, 1425, 520), (1440, 420, 1512, 500)
PAL_PROPS = SM.derive([('sewer', b) for b in (P_CHEST, P_SKULL, P_CANDLES, P_AWNING, P_COUNTER, P_RUG, P_SHELF, P_BARREL, P_CRATE)], 15)


def hexes(pal):
    return ['#%02x%02x%02x' % c for c in pal]


# ---------------------------------------------------------------- hero --
# the Bloom from the big drawing (sword masked) and from the sheets
def _masked_sheets():
    from PIL import ImageDraw
    im = SM.board('sheets').copy()
    d = ImageDraw.Draw(im)
    d.polygon([(150, 195), (215, 195), (215, 300), (165, 300), (148, 262)], fill=(75, 75, 75))
    # the Peddler's angry marks and the Gatekeeper's speech bubble
    d.rectangle([932, 98, 982, 142], fill=(75, 75, 75))
    d.rectangle([1390, 212, 1428, 262], fill=(75, 75, 75))
    return im


SM._boards['sheets_masked'] = _masked_sheets()
HERO_H = 30


def hero_fit(name, box, height=HERO_H, shift=(0, 0)):
    return SM.fit(name, box, 32, 32, PAL_HERO, BG, 40, height=height, shift=shift)


HERO_SRC = {
    'idle_s': hero_fit('sheets_masked', HERO_BIG),
    'idle_s2': hero_fit('sheets', (222, 100, 280, 175)),
    'walk_s1': hero_fit('sheets', (222, 205, 282, 280)),
    'walk_s2': hero_fit('sheets', (290, 205, 352, 280)),
    'walk_s3': hero_fit('sheets', (360, 205, 422, 280)),
    'walk_s4': hero_fit('sheets', (428, 205, 492, 280)),
    'dir_s': hero_fit('sheets', (220, 312, 262, 386)),
    'dir_n': hero_fit('sheets', (263, 312, 304, 386)),
    'dir_e': hero_fit('sheets', (305, 312, 346, 386)),
    'dir_w': hero_fit('sheets', (347, 312, 388, 386)),
    'sword': hero_fit('sheets', (395, 312, 458, 386)),
    'cast': hero_fit('sheets', (460, 312, 514, 386)),
}

# ---------------------------------------------------------------- folk --
def folk_fit(box, height=30, shift=(0, 0), name='sheets_masked'):
    return SM.fit(name, box, 32, 32, PAL_FOLK, BG, 40, height=height, shift=shift)


FOLK_SRC = {
    'peddler': folk_fit((788, 118, 872, 206)),
    'peddler_angry': folk_fit((888, 118, 975, 206)),
    'peddler_s': folk_fit((780, 290, 832, 386)),
    'peddler_s2': folk_fit((780, 290, 832, 386), shift=(0, 1)),
    'peddler_e': folk_fit((836, 290, 890, 386)),
    'peddler_n': folk_fit((890, 290, 938, 386)),
    'peddler_w': folk_fit((940, 290, 992, 386)),
    'gatekeeper': folk_fit((1268, 95, 1328, 180)),
    'gatekeeper2': folk_fit((1348, 95, 1412, 180)),
    'gatekeeper_cast': folk_fit((1245, 215, 1328, 292)),
    'gatekeeper_talk': folk_fit((1343, 215, 1395, 292)),
    'gatekeeper_s': folk_fit((1245, 322, 1292, 390)),
    'gatekeeper_e': folk_fit((1294, 322, 1346, 390)),
    'gatekeeper_n': folk_fit((1348, 322, 1397, 390)),
    'gatekeeper_w': folk_fit((1398, 322, 1436, 390)),
}

# ----------------------------------------------------------- portraits --
PORTRAIT_SRC = {
    'hero': SM.tile('ui', (775, 235, 925, 385), 32, 32, PAL_PORTRAIT, wrap=False),
    'peddler': SM.tile('ui', (775, 420, 925, 570), 32, 32, PAL_PORTRAIT, wrap=False),
    'gatekeeper': SM.fit('sheets', (1078, 112, 1182, 216), 32, 32, PAL_PORTRAIT, BG, 40, height=32, bottom=False),
}

# --------------------------------------------------------- forest tiles --
def ft(box, w=16, h=16, wrap=True, pal=None):
    return SM.tile('forest', box, w, h, pal or PAL_FOREST, wrap)


def ct(box, w=16, h=16, wrap=False):
    return SM.tile('forest', box, w, h, PAL_CLIFF, wrap)


def bt(box, w=16, h=16, wrap=True):
    return SM.tile('forest', box, w, h, PAL_BLIGHT, wrap)


FOREST_SRC = {
    'grass': ft(F_GRASS), 'grass2': ft((345, 580, 385, 620)), 'grass3': ft((335, 590, 375, 630)),
    'path': ft(F_PATH), 'path2': ft((775, 580, 815, 620)),
    'canopy': ft((130, 665, 170, 705)), 'canopy2': ft((200, 668, 240, 708)),
    'flowers_white': ft(F_FLOWERS, wrap=False), 'flowers_blue': ct(C_BLUE),
    'bush': ft((300, 672, 380, 742), wrap=False), 'bush2': ft(F_BUSH, wrap=False),
    'grass_tuft': ft(F_TUFT, wrap=False), 'stump': ft((118, 278, 166, 330), wrap=False),
    'rock': ct(C_ROCK), 'rock_small': ct((1105, 838, 1150, 886)),
    'log': ft((848, 702, 968, 762), 32, 16, False),
    'tree': ft(F_TREE, 32, 40, False), 'tree2': ft((968, 600, 1088, 730), 32, 40, False),
    'tree48': ft((105, 660, 255, 810), 32, 48, False), 'tree2_48': ft((968, 600, 1088, 730), 32, 48, False),
    'sign': ft((768, 320, 828, 392), 16, 24, False),
    'water': ct(C_WATER, wrap=True), 'water2': ct((440, 590, 480, 630), wrap=True),
    'lily': ct((472, 855, 528, 910)),
    'waterfall': ct(C_FALL, 16, 32), 'waterfall2': ct((240, 400, 300, 512), 16, 32),
    'bridge': ct(C_BRIDGE, 32, 16), 'bridge_v': ct((270, 852, 370, 982), 16, 32),
    'cliff': ct(C_LEDGE, 32, 16), 'cliff2': ct((190, 350, 330, 400), 32, 16),
    'well': ct(C_WELL, 32, 32), 'post': ct((710, 662, 760, 742), 16, 32),
    'chest': ct((185, 240, 275, 320)),
    'blight_grass': bt(B_GRASS), 'blight_grass2': bt((1330, 330, 1370, 370)), 'blight_path': bt(B_PATH),
    'blight_bush': bt(B_BUSH, wrap=False), 'blight_crystal': bt((1098, 260, 1168, 330), wrap=False), 'blight_crystal2': bt((1228, 692, 1298, 772), wrap=False),
    'blight_tree': bt(B_TREE, 32, 48, False), 'dead_tree_small': bt((1410, 110, 1510, 290), wrap=False),
    'blight_wall': bt(B_WALL, 32, 16, False), 'blight_wall2': bt((1288, 812, 1468, 872), 32, 16, False),
    'blight_door': bt(B_DOOR, 32, 32, False), 'blight_arch': bt((858, 90, 1098, 260), 48, 48, False),
    'blight_water': bt((1380, 560, 1420, 600)), 'blight_boulder': bt(B_ROCK, wrap=False),
    'blight_pillar': bt((1358, 642, 1408, 742), 16, 32, False), 'blight_canopy': bt((1150, 10, 1190, 50)),
    'blight_chest': bt((1148, 260, 1218, 320), wrap=False),
}


# ---------------------------------------------------------- sewer tiles --
def st(box, w=16, h=16, wrap=True, pal=None):
    return SM.tile('sewer', box, w, h, pal or PAL_SEWER, wrap)


def pt(box, w=16, h=16, wrap=False):
    return SM.tile('sewer', box, w, h, PAL_PROPS, wrap)


SEWER_SRC = {
    'floor': st(S_FLOOR), 'floor2': st((600, 660, 640, 700)), 'floor_moss': st((588, 618, 628, 658)),
    'wall': st(S_WALL), 'wall2': st((600, 560, 656, 616)), 'wall_top': st((650, 515, 706, 560)),
    'water': st(S_WATER), 'water2': st((1300, 680, 1364, 744)),
    'waterfall': st(S_FALL, 32, 48, False), 'waterfall_small': st((1152, 695, 1210, 780), 16, 32, False),
    'pipe_v': st(S_PIPE, 16, 32, False), 'pipe_h': st((1360, 826, 1392, 858), 16, 16, False),
    'pipe_elbow': st((1418, 592, 1508, 712), 32, 32, False),
    'grate': st((520, 515, 630, 600), 32, 32, False), 'grate16': st((520, 515, 630, 600), 16, 16, False),
    'drain': st(S_DRAIN, 32, 32, False),
    'lantern': st(S_LANTERN, 16, 32, False), 'lantern16': st(S_LANTERN, 16, 16, False),
    'banner_teal': st(S_BANNER_T, 16, 32, False), 'banner_purple': st(S_BANNER_P, 16, 32, False),
    'banner_teal16': st(S_BANNER_T, 16, 16, False), 'banner_purple16': st(S_BANNER_P, 16, 16, False),
    'ladder': st((112, 600, 188, 760), 16, 32, False), 'ladder16': st((112, 600, 188, 680), 16, 16, False),
    'post': st((384, 520, 430, 620), 16, 32, False), 'post2': st((480, 692, 520, 782), 16, 32, False),
    'moss_wall': st((1410, 890, 1480, 960)),
    'arch': st((600, 40, 900, 200), 48, 32, False),
}
SEWER_SRC['props'] = {
    'crate': pt(P_CRATE), 'crate2': pt((1430, 512, 1510, 570)), 'barrel': pt(P_BARREL),
    'chest': pt(P_CHEST), 'skull': pt(P_SKULL), 'candles': pt(P_CANDLES),
    'awning': pt(P_AWNING, 32, 16), 'counter': pt(P_COUNTER, 32, 16), 'rug': pt(P_RUG, 32, 32),
    'shelf': pt(P_SHELF, 16, 32), 'gold': pt((285, 440, 345, 500)), 'pot': pt((1028, 390, 1068, 450)),
}


# -------------------------------------------------------------- the UI --
# the HUD and the boxes: hearts, the coin, the dialogue frame on its
# navy fill, the item slots. Cream and ink are pinned for the hand-drawn
# tiles that stay (the key, the bomb, the button letters, the cursor).
U_HEARTS, U_COIN, U_FRAME, U_FILL, U_SLOT_LIT, U_SLOT = (54, 215, 230, 251), (613, 215, 647, 249), (935, 215, 1000, 280), (1300, 255, 1332, 287), (640, 698, 712, 770), (738, 698, 810, 770)
# the board's navy, golds and reds, with the blue and violet the drawn
# key, bomb and map tiles need
# in the drawn palette's order (room.c takes the gold text ink from 6 and 8):
# cream, ink, heart red, heart bright, heart dark, gold dark, gold, gold
# bright, grey, frame fill, blue, blue dark, violet, box fill, slate
PAL_HUD = [(248, 240, 216), (42, 28, 16), (212, 41, 47), (240, 120, 120), (130, 16, 26), (130, 90, 30), (209, 174, 117), (247, 230, 177),
           (102, 102, 97), (34, 37, 51), (56, 160, 255), (24, 72, 160), (144, 64, 216), (12, 16, 30), (58, 58, 72)]

# the board's UI elements do not scale cleanly to 8x8 tiles, so the
# HUD's hearts, coin, slots and frames stay drawn, in this palette.
UI_SRC = {}
