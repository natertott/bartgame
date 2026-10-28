"""Inventory the frozen pre-reboot ROM without importing mutable art painters.

Alpha bounds are measured from packed 4bpp pixels. Resident means included in
an area's compiled tileset, not proof of a placement in every generated run.
"""
import argparse
import csv
import json
from pathlib import Path

from blight_scope_probe import Rom, digest

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE = Path('/workspace/setup/art-reboot-before')


def alpha_bounds(data, width, height):
    points = []
    columns = width // 8
    for y in range(height):
        for x in range(width):
            tile = (y // 8) * columns + x // 8
            value = data[tile * 32 + (y % 8) * 4 + (x % 8) // 2]
            if (value >> (4 * (x & 1))) & 15:
                points.append((x, y))
    if not points:
        return None
    return [min(x for x, y in points), min(y for x, y in points),
            max(x for x, y in points) + 1, max(y for x, y in points) + 1]


def source_refs(root, token):
    return [str(path.relative_to(root)) for path in sorted((root / 'src').glob('*.c'))
            if token in path.read_text()]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', type=Path, default=DEFAULT_BASE)
    ap.add_argument('--out', type=Path, default=ROOT / 'docs/art-reboot/asset-inventory.json')
    args = ap.parse_args()
    r = Rom(args.baseline / 'bartgame.gba', args.baseline / 'bartgame.map', args.baseline / 'assets.h')
    sets = {area: r.tileset(area) for area in ('forest', 'sewer', 'myst')}
    types = {v: k[3:].lower() for k, v in r.defs.items() if k.startswith('TT_')}
    palettes = {v: k[8:].lower() for k, v in r.defs.items()
                if k.startswith('PAL_OBJ_') and k != 'PAL_OBJ_COUNT'}
    metatiles = []
    for name, index in sorted(r.metatiles.items(), key=lambda item: item[1]):
        areas = {}
        for area, set_ in sets.items():
            art = r.tile_art(set_, name)
            if art is not None:
                entries = r.unpack('<4H', set_['mapping'] + index * 8)
                areas[area] = {'frames': art[0], 'speed': art[1],
                               'palette_banks': sorted(set(entry >> 12 for entry in entries)),
                               'frame_rgba_sha256': [digest(frame) for frame in art[2]]}
        metatiles.append({'id': index, 'name': name.lower(),
                          'type': types[r.named('metatile_type', len(r.metatiles))[index]],
                          'collision_quarters': r.named('metatile_coll', len(r.metatiles))[index],
                          'transparent_prop': bool(r.named('metatile_prop', len(r.metatiles))[index]),
                          'resident_areas': areas,
                          'direct_runtime_references': source_refs(ROOT, 'MT_' + name)})
    sheets = []
    for name, index in sorted(r.sheet_names.items(), key=lambda item: item[1]):
        metadata, data = r.sheet(name)
        tile_count, frame_tiles, shape, size, palette, width, height = metadata
        prefix = 'F_' + name.upper() + '_'
        frames = []
        for frame_name, frame_index in sorted(
                ((key[len(prefix):].lower(), value) for key, value in r.defs.items() if key.startswith(prefix)),
                key=lambda item: item[1]):
            raw = data[frame_index * frame_tiles * 32:(frame_index + 1) * frame_tiles * 32]
            box = alpha_bounds(raw, width, height)
            frames.append({'id': frame_index, 'name': frame_name, 'bounds_xyxy': box,
                           'visible_size': [box[2] - box[0], box[3] - box[1]] if box else [0, 0],
                           'sha256': digest(raw)})
        sheets.append({'id': index, 'name': name, 'canvas': [width, height],
                       'frame_count': len(frames), 'frame_tiles': frame_tiles, 'source_tiles': tile_count,
                       'palette_slot': palette, 'palette_group': palettes.get(palette),
                       'direct_runtime_references': source_refs(ROOT, 'SHEET_' + name.upper()),
                       'frames': frames})
    ui = {
        'frame_tiles_8x8': r.defs['UI_TILE_COUNT'],
        'hud_tiles_8x8': r.defs['HUD_TILE_COUNT'],
        'glyph_count': r.defs['VWF_COUNT'], 'glyph_height': r.defs['VWF_HEIGHT'],
        'glyph_widths': list(r.named('vwf_w', r.defs['VWF_COUNT'])),
        'glyph_bits_sha256': digest(r.named('vwf_bits', r.defs['VWF_COUNT'] * r.defs['VWF_HEIGHT'])),
        'title': {'canvas': [r.defs['TITLE_WIDTH'], r.defs['TITLE_HEIGHT']],
                  'format': 'Mode3 RGB555', 'bytes': r.defs['TITLE_BITMAP_BYTES'],
                  'unique_colors': len(set(r.unpack('<%dH' % r.defs['TITLE_BITMAP_PIXELS'], r.symbols['title_bitmap']))),
                  'sha256': digest(r.named('title_bitmap', r.defs['TITLE_BITMAP_BYTES']))},
    }
    report = {
        'rom_sha256': digest(r.data), 'rom_bytes': len(r.data),
        'method': __doc__.strip(), 'global_metatile_count': len(metatiles),
        'resident_metatile_count': sum(bool(m['resident_areas']) for m in metatiles),
        'sprite_sheet_count': len(sheets), 'sprite_source_frames': sum(s['frame_count'] for s in sheets),
        'areas': {area: {'subtiles': s['tile_count'], 'palette_banks': s['palette_count'],
                         'animation_count': len(s['animations']),
                         'resident_metatiles': sum(area in m['resident_areas'] for m in metatiles)}
                  for area, s in sets.items()},
        'obj_budget': {'dynamic_sheet_limit': 876, 'baseline_measured_peak': 854,
                       'measured_headroom': 22, 'hardware_total_tiles': 1024, 'oam_entries': 128},
        'ui': ui, 'sheets': sheets, 'metatiles': metatiles,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    csv_path = args.out.with_name('metatile-index.csv')
    with csv_path.open('w', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['id', 'name', 'type', 'collision_quarters', 'transparent_prop', 'resident_areas', 'direct_runtime_references'])
        for row in metatiles:
            writer.writerow([row['id'], row['name'], row['type'], row['collision_quarters'], row['transparent_prop'],
                             '|'.join(row['resident_areas']), '|'.join(row['direct_runtime_references'])])
    print('Inventoried %d global/%d resident metatiles, %d sheets, %d source frames' % (
        len(metatiles), report['resident_metatile_count'], len(sheets), report['sprite_source_frames']))
    print('ROM SHA256', report['rom_sha256'])


if __name__ == '__main__':
    main()
