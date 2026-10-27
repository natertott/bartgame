"""Check that interactive scenery polish leaves unrelated packed artwork exact.

The frozen and current ROMs, rather than source previews, supply every pixel.
Backgrounds are decoded through their actual 4bpp subtiles, hardware flips,
palette banks, RGB555 colours and resident animation frames. A deliberately
small semantic allowlist is intersected with the painter's declared names.
"""
import argparse
import importlib.util
import json
from pathlib import Path

from blight_scope_probe import Rom, digest

ROOT = Path(__file__).resolve().parent.parent
BASE = Path('/workspace/setup/interactive-before')

# These are interactions, not a broad permission to repaint forest materials.
# Logical chest/mouth placeholders may remain unchanged when the large actor
# layer supplies their visible art. Their original contracts stay authoritative.
INTERACTIVE_NAMES = {
    'MYST_SWITCH', 'MYST_SWITCH_DOWN', 'MYST_POT', 'MYST_SPRING',
    'PIT', 'PIT_INNER', 'FOREST_BLIGHT_PIT', 'CRACK', 'WEB',
    'DOOR_LOCKED', 'DOOR_OPEN', 'TORCH', 'TORCH_LIT',
    'CHEST', 'CHEST_OPEN', 'MYST_CHEST', 'MYST_CHEST_OPEN',
    'STAIRS_DOWN', 'MOUTH_CAVE', 'MOUTH_HOLLOW', 'MOUTH_THICKET',
    'CAVE_EXIT', 'HOLLOW_EXIT', 'THICKET_EXIT',
    'CAVE_FLOOR_CHEST', 'HOLLOW_FLOOR_CHEST', 'THICKET_FLOOR_CHEST',
    'SW_LADDER', 'SW_HOLE', 'SW_TORCH_LIT', 'SW_POT', 'SWH_063',
}
NEW_SHEETS = {'interactivechest': (32, 32), 'interactiveentry': (32, 64)}


def declared_names(path):
    """Read the painter's declaration without importing the terrain pipeline."""
    spec = importlib.util.spec_from_file_location('interactive_scope_painter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {name.upper() for name in module.CHANGED_NAMES}


def art_detail(value):
    if value is None:
        return None
    return {'frames': value[0], 'speed': value[1],
            'rgba_sha256': [digest(frame) for frame in value[2]]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before-rom', default=str(BASE / 'bartgame.gba'))
    ap.add_argument('--before-map', default=str(BASE / 'bartgame.map'))
    ap.add_argument('--before-header', default=str(BASE / 'assets.h'))
    ap.add_argument('--rom', default=str(ROOT / 'bartgame.gba'))
    ap.add_argument('--map', default=str(ROOT / 'build/bartgame.map'))
    ap.add_argument('--header', default=str(ROOT / 'build/gen/assets.h'))
    ap.add_argument('--painter', default=str(ROOT / 'art/interactive_tiles.py'))
    ap.add_argument('--out', default='/workspace/setup/interactive-scope.json')
    args = ap.parse_args()
    before = Rom(args.before_rom, args.before_map, args.before_header)
    after = Rom(args.rom, args.map, args.header)
    declared = declared_names(args.painter)
    checks, failures, counts, changed = [], [], {}, {}

    def check(group, name, ok, detail=None):
        row = {'group': group, 'name': name, 'passed': bool(ok)}
        if detail is not None:
            row['detail'] = detail
        checks.append(row)
        if not ok:
            failures.append(row)

    check('scope_declaration', 'only named interactions declared',
          declared <= INTERACTIVE_NAMES, sorted(declared - INTERACTIVE_NAMES))
    check('metatile_contracts', 'all names and identifiers retained',
          before.metatiles == after.metatiles)
    for name, index in before.metatiles.items():
        if name not in after.metatiles:
            continue
        for field in ('type', 'coll', 'prop'):
            old = before.read(before.symbols['metatile_' + field] + index, 1)
            new = after.read(after.symbols['metatile_' + field] + after.metatiles[name], 1)
            check('metatile_contracts', name + ' ' + field, old == new)
    counts['physical_metatiles'] = len(before.metatiles)

    for area in ('forest', 'sewer', 'myst'):
        oldset, newset = before.tileset(area), after.tileset(area)
        retained = retained_frames = changed_frames = 0
        changed[area] = []
        for name in sorted(before.metatiles):
            old = before.tile_art(oldset, name)
            new = after.tile_art(newset, name)
            if old is None and new is None:
                continue
            if old == new:
                retained += 1
                retained_frames += old[0] if old else 0
                check('retained_terrain', area + ' ' + name, True)
                continue
            changed[area].append(name.lower())
            changed_frames += new[0] if new else 0
            permitted = name in INTERACTIVE_NAMES and name in declared
            check('interactive_art', area + ' ' + name, permitted,
                  {'before': art_detail(old), 'after': art_detail(new)})
            # An old blank tile has no packed image to report a cadence for.
            if old is not None and new is not None:
                check('animation_contracts', area + ' ' + name,
                      old[:2] == new[:2])
        check('hardware_budget', area + ' subtiles', newset['tile_count'] <= 1024)
        check('hardware_budget', area + ' palettes', newset['palette_count'] <= 12)
        counts[area] = {
            'retained_tiles': retained, 'retained_animation_frames': retained_frames,
            'changed_tiles': len(changed[area]), 'changed_animation_frames': changed_frames,
            'subtiles': newset['tile_count'], 'palettes': newset['palette_count'],
            'animated_metatiles': len(newset['animations']),
        }

    check('sprite_contracts', 'exactly two new scenery sheets',
          set(after.sheet_names) - set(before.sheet_names) == set(NEW_SHEETS))
    check('sprite_contracts', 'all original sheet identifiers retained',
          all(after.sheet_names.get(name) == index
              for name, index in before.sheet_names.items()))
    for name in before.sheet_names:
        if name not in after.sheet_names:
            check('retained_sprites', name + ' exists', False)
            continue
        old, new = before.sheet(name), after.sheet(name)
        check('sprite_contracts', name + ' metadata', old[0] == new[0])
        if name != 'lift':
            check('retained_sprites', name, old[1] == new[1])
            continue
        stride = old[0][1] * 32
        lift_changes = []
        for frame_name, index in before.defs.items():
            if not frame_name.startswith('F_LIFT_'):
                continue
            oldpixels = old[1][index * stride:(index + 1) * stride]
            newpixels = new[1][index * stride:(index + 1) * stride]
            if oldpixels != newpixels:
                lift_changes.append(frame_name)
            check('carried_objects', frame_name,
                  oldpixels == newpixels or frame_name == 'F_LIFT_POT')
        counts['changed_lift_frames'] = lift_changes
    counts['retained_sprite_sheets'] = len(before.sheet_names) - 1
    counts['hero_source_frames'] = after.defs['SHEET_HERO_FRAMES']

    lift_palette = before.sheet('lift')[0][4]
    for name, dimensions in NEW_SHEETS.items():
        if name not in after.sheet_names:
            check('new_scenery', name + ' exists', False)
            continue
        metadata, _ = after.sheet(name)
        check('new_scenery', name + ' dimensions', metadata[5:7] == dimensions)
        check('new_scenery', name + ' existing lift palette', metadata[4] == lift_palette)
        check('new_scenery', name + ' one-frame tile footprint',
              metadata[1] == dimensions[0] * dimensions[1] // 64)
    for name, value in before.defs.items():
        if name.startswith('F_'):
            check('frame_identifiers', name, after.defs.get(name) == value)

    arrays = {'pal_obj': 512, 'title_bitmap': 240 * 160 * 2,
              'pal_bg': before.defs['PAL_BG_COUNT'] * 32}
    for name in ('items', 'pick32', 'icon32', 'shield', 'bloomfx'):
        arrays[name + '_frame_pal'] = before.defs['SHEET_' + name.upper() + '_FRAMES']
    arrays['icon32_exact_tiles'] = before.defs['SHEET_ICON32_TILES'] * 32
    arrays['icon32_exact_pal'] = before.defs['SHEET_ICON32_FRAMES'] * 32
    check('palette_contracts', 'background palette count',
          before.defs['PAL_BG_COUNT'] == after.defs['PAL_BG_COUNT'])
    check('palette_contracts', 'object palette count',
          before.defs['PAL_OBJ_COUNT'] == after.defs['PAL_OBJ_COUNT'])
    for name, size in arrays.items():
        check('retained_assets', name, before.named(name, size) == after.named(name, size))

    report = {
        'before_rom_sha256': digest(before.data), 'rom_sha256': digest(after.data),
        'method': 'Packed real-ROM comparison: all resident BG frames decoded through '
                  '4bpp subtiles, hardware flips, palette banks and RGB555; exact original '
                  'sprite metadata/frame IDs and pixels except the remapped carried pot; '
                  'all BG/OBJ palettes, item tables and title bitmap retained.',
        'declared_interactive_materials': sorted(name.lower() for name in declared),
        'changed_materials': changed, 'counts': counts,
        'passed': len(checks) - len(failures), 'total': len(checks),
        'failures': failures, 'checks': checks,
    }
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    for row in failures:
        print('FAIL', row['group'], row['name'], row.get('detail', ''))
    print('RESULT %s %d/%d interactive scope checks; changed BG tiles: %s' % (
        'FAIL' if failures else 'PASS', report['passed'], report['total'],
        ', '.join('%s=%d' % (area, len(names)) for area, names in changed.items())))
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
