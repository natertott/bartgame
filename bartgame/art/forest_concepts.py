"""Opt-in forest environment studies; profile zero preserves production art.

Only the environment painters and their explicitly owned object frames vary.
The selected bestiary, Bloom, equipment, interfaces and physical metadata keep
their established contracts. No global palette object is mutated.
"""
import os

VARIANT = int(os.environ.get('BART_FOREST', '0'))
assert 0 <= VARIANT <= 5, ('BART_FOREST must be 0..5', VARIANT)
NAMES = {
    0: 'Current production forest',
    1: 'Fern & Oak',
    2: 'Silver Willow',
    3: 'Copper Beech',
    4: 'Velvet Cedar',
    5: 'Pale Orchard',
}
TERRAIN_BANKS = {'ground', 'foliage', 'water', 'stone', 'blight',
                 'decay_mix', 'rot_water'}


def tile(name, phase=0):
    """Return (native image, BG bank, owner), or None for a protected tile."""
    if not VARIANT:
        return None
    import forest_concepts_props as props
    import forest_concepts_terrain as terrain
    if props.supports_tile(name):
        image, bank = props.paint_tile(name, phase, VARIANT)
        return image, bank, 'forest_concepts_props'
    if terrain.supports(name):
        image, bank = terrain.paint(name, phase, VARIANT)
        return image, bank, 'forest_concepts_terrain'
    return None


def rows(image):
    assert image.mode == 'P' and set(image.getdata()) <= set(range(16))
    return [''.join(format(image.getpixel((x, y)), 'x')
                    for x in range(image.width)) for y in range(image.height)]


def bg_palettes(palettes):
    if not VARIANT:
        return palettes
    import forest_concepts_props as props
    import forest_concepts_terrain as terrain
    out = [(name, terrain.palette(name, VARIANT) if name in TERRAIN_BANKS
            else colors) for name, colors in palettes]
    aliases = props.BG_PALETTE_ALIASES
    assert not set(aliases) & {name for name, _ in out}
    out.extend(aliases.items())
    return out


def apply_sprites(sheets, coverage):
    if not VARIANT:
        return
    import forest_concepts_props as props
    import forest_concepts_folk as folk
    for sheet in sheets:
        for frame in sheet['frames']:
            if props.supports_frame(sheet['name'], frame):
                image, bank = props.paint_frame(sheet['name'], frame, VARIANT)
                owner = 'forest_concepts_props'
            elif folk.supports_frame(sheet['name'], frame):
                image, bank = folk.frame(sheet['name'], frame, VARIANT)
                owner = 'forest_concepts_folk'
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
