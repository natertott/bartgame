"""Ten native, behavior-led alternatives for each of six enemy families.

Profile zero preserves the existing production sprites. Profiles1..10 select
one alternative in every family for playable comparison; they do not rename
gameplay IDs or change movement, attack timing, hitboxes or damage.
"""
import os

VARIANT = int(os.environ.get('BART_ENEMY', '0'))
assert 0 <= VARIANT <= 10, 'BART_ENEMY must be 0..10'
FAMILIES = ('beetle', 'bat', 'spitter', 'slime', 'knight', 'boss')


def module_for(family):
    if family in ('beetle', 'bat'):
        import enemy_studies_small as module
    elif family in ('spitter', 'slime', 'proj'):
        import enemy_studies_soft as module
    else:
        import enemy_studies_heavy as module
    return module


def frame(family, variant, name):
    image = module_for(family).frame(family, variant, name)
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
                             'owner': module.__name__, 'canvas': list(image.size),
                             'enemy_study': VARIANT})
        for entry in coverage:
            if entry['sheet'] == family and entry['frame'] in targets:
                entry.update(owner=module.__name__, enemy_study=VARIANT)
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
