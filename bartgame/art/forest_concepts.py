"""Opt-in forest environment studies; profile zero preserves production art.

Only the environment painters and their explicitly owned object frames vary.
The selected bestiary, Bloom, equipment, interfaces and physical metadata keep
their established contracts. No global palette object is mutated.
"""
import os

VARIANT = int(os.environ.get('BART_FOREST', '0'))
assert 0 <= VARIANT <= 30, ('BART_FOREST must be 0..30', VARIANT)
ROUND2 = VARIANT >= 6
CANOPY_ROUND = VARIANT >= 11
ADAPTIVE_ROUND = VARIANT >= 19
TREE_ROUND = VARIANT == 30
EMERALD_ROUND = VARIANT in (29, 30)
LOCAL_VARIANT = 1 if EMERALD_ROUND else VARIANT - 18 if ADAPTIVE_ROUND else VARIANT - 10 if CANOPY_ROUND else VARIANT - 5 if ROUND2 else VARIANT
# Canopy studies keep the accepted grey ground and all other environment art
# from Black Sap Oak; only the canopy painter receives the local study style.
ENV_VARIANT = 1 if CANOPY_ROUND else LOCAL_VARIANT
NAMES = {
    0: 'Current production forest',
    1: 'Fern & Oak',
    2: 'Silver Willow',
    3: 'Copper Beech',
    4: 'Velvet Cedar',
    5: 'Pale Orchard',
    6: 'Black Sap Oak',
    7: 'Violet Strangler',
    8: 'Witchfire Weep',
    9: 'Amethyst Canker',
    10: 'Royal Bruise',
    11: 'Veinbound Oak',
    12: 'Patchblight Beech',
    13: 'Spore Drift',
    14: 'Bracketwood',
    15: 'Violet Leaf Mosaic',
    16: 'Black Sap Bough',
    17: 'Silkbound Crown',
    18: 'Canker Bloom',
    19: 'Ancient Oak Vault',
    20: 'Crooked Willow',
    21: 'Buttress Beech',
    22: 'Woven Bower',
    23: 'Fungal Cathedral',
    24: 'Fallen Crown',
    25: 'Lightning Cleft Oak',
    26: 'Pale Birch Congregation',
    27: 'Black Cedar Cathedral',
    28: 'Sorrow Arch Elm',
    29: 'Leafwoven Canopy',
    30: 'Repeated Tree Study',
}
TERRAIN_BANKS = {'ground', 'foliage', 'water', 'stone', 'blight',
                 'decay_mix', 'rot_water'}


def painters():
    if EMERALD_ROUND:
        import forest_concepts_v2_props as props
        import forest_canopy_emerald_terrain as terrain
    elif ADAPTIVE_ROUND:
        import forest_concepts_v2_props as props
        import forest_canopy_adaptive_terrain as terrain
    elif CANOPY_ROUND:
        import forest_concepts_v2_props as props
        import forest_concepts_v3_terrain as terrain
    elif ROUND2:
        import forest_concepts_v2_props as props
        import forest_concepts_v2_terrain as terrain
    else:
        import forest_concepts_props as props
        import forest_concepts_terrain as terrain
    return props, terrain


def folk_painter():
    if ROUND2:
        import forest_concepts_v2_folk as folk
    else:
        import forest_concepts_folk as folk
    return folk


def tile(name, phase=0):
    """Return (native image, BG bank, owner), or None for a protected tile."""
    if not VARIANT:
        return None
    props, terrain = painters()
    if props.supports_tile(name):
        image, bank = props.paint_tile(name, phase, ENV_VARIANT)
        return image, bank, props.__name__
    if terrain.supports(name):
        image, bank = terrain.paint(name, phase, LOCAL_VARIANT)
        return image, bank, terrain.__name__
    return None


def rows(image):
    assert image.mode == 'P' and set(image.getdata()) <= set(range(16))
    return [''.join(format(image.getpixel((x, y)), 'x')
                    for x in range(image.width)) for y in range(image.height)]


def bg_palettes(palettes):
    if not VARIANT:
        return palettes
    props, terrain = painters()
    out = [(name, terrain.palette(name, LOCAL_VARIANT) if name in TERRAIN_BANKS
            else colors) for name, colors in palettes]
    aliases = props.BG_PALETTE_ALIASES
    assert not set(aliases) & {name for name, _ in out}
    out.extend(aliases.items())
    if CANOPY_ROUND:
        extra = terrain.extra_palettes(LOCAL_VARIANT)
        assert not set(extra) & {name for name, _ in out}
        out.extend(extra.items())
    return out


def apply_sprites(sheets, coverage):
    if not VARIANT:
        return
    props, _ = painters()
    folk = folk_painter()
    for sheet in sheets:
        for frame in sheet['frames']:
            if props.supports_frame(sheet['name'], frame):
                image, bank = props.paint_frame(sheet['name'], frame, ENV_VARIANT)
                owner = props.__name__
            elif folk.supports_frame(sheet['name'], frame):
                image, bank = folk.frame(sheet['name'], frame, ENV_VARIANT)
                owner = folk.__name__
            else:
                continue
            assert image.size == (sheet['w'], sheet['h']), (sheet['name'], frame)
            sheet['frames'][frame] = rows(image)
            if 'frame_pal' not in sheet:
                sheet['frame_pal'] = {name: sheet['pal'] for name in sheet['frames']}
            sheet['frame_pal'][frame] = bank
            for row in coverage:
                if row['sheet'] == sheet['name'] and row['frame'] == frame:
                    row.update(owner=owner, forest_concept=VARIANT)
