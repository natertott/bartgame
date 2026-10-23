"""BARTGAME palettes. 16 colors each; index 0 is transparent for sprites
and the backdrop color for BG palette 0.

The look: grungy dark medieval, with gold sparkle. Deep blacks and
violets for the rot, mossy greens, cold stone, and pale gold highlights.
"""

# Shared ramps, so tiles and sprites agree.
BLACK = '#06050a'
GOLD = ['#5a3a10', '#a87a22', '#e8c04a', '#fff0a8']
MOSS = ['#0b150f', '#142619', '#1f3a24', '#2f5431', '#4a7a3f']
BLIGHT = ['#3a1e44', '#5d2a6e', '#8a3fa3', '#b865d0']
ROT_YELLOW = ['#5a6a1a', '#8c9e2a', '#c6d44f']
STONE = ['#15151c', '#24242e', '#383846', '#52526a', '#7a7a94']
BARK = ['#16100c', '#2a1c14', '#45301f', '#6a4a30']
WATER = ['#0a1a24', '#123546', '#1f5a6e', '#3a8aa0']
BONE = ['#8a8070', '#c8bca4', '#f0e8d8']

BG_PALETTES = [
    # 0 forest ground: moss, bark, rot, blight
    ('forest', [BLACK, MOSS[0], MOSS[1], MOSS[2], MOSS[3], MOSS[4],
                BARK[0], BARK[1], BARK[2], BARK[3],
                BLIGHT[0], BLIGHT[1], BLIGHT[2],
                ROT_YELLOW[0], ROT_YELLOW[1], ROT_YELLOW[2]]),
    # 1 forest detail: stone, water, gold, bone
    ('forest2', [BLACK, MOSS[1], STONE[1], STONE[2], STONE[3], STONE[4],
                 WATER[0], WATER[1], WATER[2], WATER[3],
                 GOLD[0], GOLD[1], GOLD[2], GOLD[3],
                 BONE[1], BLIGHT[3]]),
    # 2 sewer: wet stone, slime, rust, torchlight
    ('sewer', [BLACK, '#0e0e14', '#1b1b25', '#2a2a38', '#3d3d50', '#58586e',
               '#1a3a1c', '#2f6a2c', '#4f9a3c', '#0d2630', '#174a58', '#2a7a88',
               '#4a2412', '#7a3c1a', GOLD[2], GOLD[3]]),
    # 3 HUD and text
    ('hud', [BLACK, '#f4ecd8', '#2a1a10', '#c82838', '#ff5060', '#3a1a1a',
             GOLD[1], GOLD[2], GOLD[3], '#6a6a80', '#2a2a36', '#8ab0ff',
             '#5a3a7a', '#9a6ad0', '#101018', '#404050']),
]

OBJ_PALETTES = [
    # 0 hero: stalk greens, petal reds, pale face, steel and gold
    ('hero', ['#000000', '#0f2412', '#1e4a24', '#357a36', '#5aae4a',
              '#5a1020', '#9a1e38', '#d43a5c', '#f07a90',
              '#5a3a2a', '#c8a888', '#f0dcc0',
              '#3a3a4a', '#9aa0b8', '#e8ecf4', GOLD[3]]),
    # 1 effects and pickups: sparks, hearts, gilt, keys
    ('fx', ['#000000', '#101018', '#8a0a1a', '#d02838', '#ff6a6a',
            GOLD[0], GOLD[1], GOLD[2], GOLD[3], '#ffffff',
            '#4a3a8a', '#8a7ad8', '#c8c0ff', '#2a2a2a', '#6a6a6a', '#b0b0b0']),
    # 2 bugs: beetle, bat, slime (violet-black, yellow eyes)
    ('bugs', ['#000000', '#0c0a12', '#1e1828', '#352a48', '#52407a',
              '#7a60b0', '#a888e0', ROT_YELLOW[1], ROT_YELLOW[2], '#fff0a0',
              '#2a1a1a', '#6a2a2a', '#c03030', '#3a3a3a', '#808080', '#d0d0d0']),
    # 3 blight: spitter, boss (sick yellow-green, red veins)
    ('blight', ['#000000', '#1a1c0a', '#2e3412', '#4a5a1a', '#6e8622', '#9ab030',
                '#c8d84a', '#2a0a10', '#5a1020', '#9a1a30', '#d83050', '#ff8090',
                '#3a1e44', '#8a3fa3', '#f0e0a0', '#ffffff']),
    # 4 knights and NPCs: rusted steel, dark cloth, gold trim, skin
    ('iron', ['#000000', '#141418', '#2a2a32', '#44444f', '#6a6a7c', '#9a9aae',
              '#3a1a0a', '#6a3418', '#a05a28', '#2a1030', '#5a2060',
              '#e0c8a0', '#a08060', GOLD[1], GOLD[2], '#c02020']),
]
