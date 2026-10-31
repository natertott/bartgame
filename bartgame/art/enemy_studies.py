"""Ten native, behavior-led alternatives for each of six enemy families.

Profile11 is the selected production set. Zero preserves pre-selection art;
profiles1..10 retain the complete comparison sets. None rename gameplay IDs
or change movement, attack timing, hitboxes or damage.
"""
import os

VARIANT = int(os.environ.get('BART_ENEMY', '11'))
assert 0 <= VARIANT <= 11, 'BART_ENEMY must be 0..11'
FAMILIES = ('beetle', 'bat', 'spitter', 'slime', 'knight', 'boss')
SELECTED_VARIANTS = {'beetle': 9, 'bat': 9, 'spitter': 5, 'slime': 9,
                     'knight': 6, 'ksword': 6, 'proj': 5}
SELECTED_NAMES = {'beetle': 'Coin Toad', 'bat': 'Quill Moth',
                  'spitter': 'Trumpet Bellflower', 'slime': 'Pear Bladder',
                  'knight': 'Moth Confessor', 'boss': 'Broken Heart'}


def module_for(family):
    if family in ('beetle', 'bat'):
        import enemy_studies_small as module
    elif family in ('spitter', 'slime', 'proj'):
        import enemy_studies_soft as module
    else:
        import enemy_studies_heavy as module
    return module


def frame(family, variant, name):
    if variant == 11 and family == 'boss':
        import enemy_heart
        image = enemy_heart.frame(name)
    else:
        choice = SELECTED_VARIANTS[family] if variant == 11 else variant
        image = module_for(family).frame(family, choice, name)
    assert image.mode == 'P', (family, name, image.mode)
    assert set(image.getdata()) <= set(range(16)), (family, name)
    return image


def rows(image):
    return [''.join(format(image.getpixel((x, y)), 'x')
                    for x in range(image.width)) for y in range(image.height)]


def apply(sheets, coverage):
    """Keep every old sheet/frame ID; append only explicit new action poses."""
    if not VARIANT:
        return
    names = set(FAMILIES) | {'ksword'}
    for sheet in sheets:
        family = sheet['name']
        companion = family == 'proj'
        if family not in names and not companion:
            continue
        module = module_for(family)
        owner = 'enemy_heart' if VARIANT == 11 and family == 'boss' else module.__name__
        if family in ('beetle', 'bat', 'slime'):
            # Bank10 is unused by live material-item frames: they all select
            # explicit per-frame banks. The paused icon cache may borrow it,
            # then restores all256 OBJ colors before enemies draw again.
            sheet['pal'] = 'items'
        targets = ('seed',) if companion else tuple(sheet['frames'])
        for name in targets:
            image = frame(family, VARIANT, name)
            assert image.size == (sheet['w'], sheet['h']), (family, name, image.size)
            sheet['frames'][name] = rows(image)
        for name in getattr(module, 'EXTRA_FRAMES', {}).get(family, ()):
            assert name not in sheet['frames'], (family, name)
            image = frame(family, VARIANT, name)
            assert image.size == (sheet['w'], sheet['h']), (family, name, image.size)
            sheet['frames'][name] = rows(image)
            coverage.append({'sheet': family, 'frame': name,
                             'owner': owner, 'canvas': list(image.size),
                             'enemy_study': VARIANT})
        for entry in coverage:
            if entry['sheet'] == family and entry['frame'] in targets:
                entry.update(owner=owner, enemy_study=VARIANT)
            if VARIANT == 11 and entry['sheet'] == family:
                entry['selected_design'] = SELECTED_NAMES.get(family, 'Selected companion')
                entry['selected_variant'] = SELECTED_VARIANTS.get(family)
    for sheet in sheets:
        if sheet['name'] in ('beetle', 'bat', 'slime'):
            continue
        used = set(sheet.get('frame_pal', {}).values())
        assert 'items' not in used, ('enemy-only bank used by item frame', sheet['name'])
        if sheet['pal'] == 'items':
            assert len(sheet.get('frame_pal', {})) == len(sheet['frames']), sheet['name']


def concepts():
    return {family: {'concepts': module_for(family).CONCEPTS[family],
                     'notes': module_for(family).NOTES[family]}
            for family in FAMILIES}
