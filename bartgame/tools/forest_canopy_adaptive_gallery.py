#!/usr/bin/env python3
"""Native prefab and real placement-plan review for adaptive canopy studies.

New tree drawings keep their authored native dimensions. Source assemblies,
actual engine placement diagnostics and 240x160 mGBA frames have distinct
labels. No rejected canopy image or fixed small-crown assembly is imported.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art'
BG, FG, DIM = '#101820', '#f0d898', '#b0c0a0'
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
LOADED_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
STYLES = tuple(range(1, 11))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value, compact=False):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    opts = {'separators': (',', ':')} if compact else {'indent': 2}
    path.write_text(json.dumps(value, **opts) + '\n')


def markdown(path, lines):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n')


def label(draw, xy, text, color=FG):
    draw.fontmode = '1'; draw.text(xy, str(text), font=FONT, fill=color)


def rgb(color):
    return tuple(int(color[n:n+2], 16) for n in (1, 3, 5))


def legal_palette(colors):
    assert len(colors) == 16
    assert all(color.startswith('#') and len(color) == 7 and
               all(c % 8 == 0 for c in rgb(color)) for color in colors), colors


def rgba(indices, size, colors, display=False):
    legal_palette(colors)
    assert len(indices) == size[0] * size[1] and set(indices) <= set(range(16))
    image = Image.new('RGBA', tuple(size))
    def color(index):
        values = rgb(colors[index])
        if display:
            values = tuple(c | (c >> 5) for c in values)
        return values + (255 if index else 0,)
    image.putdata([color(i) for i in indices])
    return image


def indexed(indices, size, colors):
    image = Image.new('P', tuple(size)); image.putdata(indices)
    table = [n for color in colors for n in rgb(color)]
    image.putpalette(table + [0] * (768 - len(table))); image.info['transparency'] = 0
    return image


def paste(canvas, image, point, scale=1):
    if scale != 1:
        image = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
    canvas.paste(image, point, image if image.mode == 'RGBA' else None)


def exact_gif(frames, path, duration=180):
    colors = sorted({c for frame in frames for _, c in frame.getcolors(frame.width * frame.height)})
    assert len(colors) <= 256, ('Source GIF needs too many colors', len(colors))
    mapping = {c: n for n, c in enumerate(colors)}
    table = [n for color in colors for n in color]
    converted = []
    for frame in frames:
        image = Image.new('P', frame.size); image.putpalette(table + [0] * (768 - len(table)))
        data = frame.tobytes()
        image.putdata([mapping[c] for c in zip(data[0::3], data[1::3], data[2::3])]); converted.append(image)
    converted[0].save(path, save_all=True, append_images=converted[1:], duration=duration,
                      loop=0, optimize=False, disposal=2)
    with Image.open(path) as check:
        decoded = [(f.convert('RGB').copy(), f.info['duration']) for f in ImageSequence.Iterator(check)]
    assert len(decoded) == len(frames)
    assert all(a.tobytes() == b.tobytes() and hold == duration for (a, hold), b in zip(decoded, frames))
    return {'frames': len(frames), 'colors': len(colors), 'inspection_hold_ms': duration,
            'exact_rgb_roundtrip': True, 'engine_timing_claim': False}


def frozen(work, profile, final):
    if not final:
        return {'source_commit': None, 'status': 'UNFROZEN SOURCE STUDY'}
    path = work / f'frozen/v{profile}/freeze.json'; value = json.loads(path.read_text())
    assert value.get('variant', value.get('forest_variant')) == profile
    for key in ('source_file_sha256', 'code_file_sha256'):
        for name, digest in value.get(key, {}).items():
            assert sha(ROOT / name) == digest, ('Frozen source drift', name)
    assert sha(path.parent / 'bartgame.gba') == value['rom_sha256']
    return {**value, 'freeze_sha256': sha(path)}


def worker(args):
    sys.path.insert(0, str(ART))
    paths = sorted(ART.glob('*.py')) + [ROOT / 'tools/build_assets.py', ROOT / 'Makefile']
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    art = importlib.import_module(args.art_module)
    bank = art.PALETTE_NAME
    stages = [art.pulse_palettes(args.style, stage)[bank] for stage in range(4)]
    for stage in stages:
        assert len(stage) == 4
        for palette in stage: legal_palette(palette)
    entries = []
    for spec in art.prefab_specs(args.style):
        role, variation = spec['role'], spec.get('variation', 0)
        image = art.prefab(args.style, role, variation)
        assert image.mode == 'P' and image.size == tuple(spec['size']), (role, image.size, spec)
        values = list(image.tobytes()); assert any(values) and set(values) <= set(range(16))
        entries.append({**spec, 'category': 'resident_prefab', 'size': list(image.size), 'indices': values,
                        'index_sha256': hashlib.sha256(bytes(values)).hexdigest(),
                        'painted_bounds': image.getbbox(), 'painted_pixels': sum(i != 0 for i in values),
                        'owner': args.art_module if args.style <= 5 else args.art_module + '_b'})
    if hasattr(art, 'authored_tree'):
        for large in (False, True):
            for second in (False, True):
                image = art.authored_tree(args.style, large=large, second=second)
                size = (48, 64) if large else (32, 48)
                assert image.mode == 'P' and image.size == size
                values = list(image.tobytes()); assert set(values) <= set(range(16)) and any(values)
                role = 'authored-' + ('large' if large else 'small') + ('-b' if second else '-a')
                entries.append({'name': role, 'role': role, 'variation': 0, 'category': 'authored_tree_group',
                                'size': list(size), 'indices': values, 'palette': bank,
                                'layer': 'Existing grouped-tree canvas; physical footprint is unchanged',
                                'index_sha256': hashlib.sha256(bytes(values)).hexdigest(),
                                'painted_bounds': image.getbbox(), 'painted_pixels': sum(i != 0 for i in values),
                                'owner': args.art_module if args.style <= 5 else args.art_module + '_b'})
    if hasattr(art, 'blocked_branch'):
        image = art.blocked_branch(args.style); values = list(image.tobytes())
        assert image.mode == 'P' and image.size == (64, 16) and set(values) <= set(range(16))
        entries.append({'name': 'branch-solid', 'role': 'branch-solid', 'variation': 0,
                        'category': 'resident_special_map', 'planner_role': 'branch', 'placement_flags': 0,
                        'size': [64, 16], 'palette': bank, 'layer': 'Blocked narrow arm; separate from the open projected branch',
                        'indices': values, 'index_sha256': hashlib.sha256(bytes(values)).hexdigest(),
                        'painted_bounds': image.getbbox(), 'painted_pixels': sum(i != 0 for i in values),
                        'owner': args.art_module})
    backing = []
    if hasattr(art, 'quiet_fill'):
        for variation in range(3):
            image = art.quiet_fill(args.style, variation)
            backing.append({'role': 'quiet_fill', 'variation': variation, 'size': list(image.size),
                            'indices': list(image.tobytes()), 'layer': 'blocked underbrush backing'})
    assert all(sha(ROOT / name) == digest for name, digest in inputs.items()), 'Art changed while exporting'
    write(args.snapshot, {'style': args.style, 'profile': args.style + 18,
                          'name': art.NAMES[args.style], 'palette_bank': bank,
                          'stage_pulse_palettes': stages, 'entries': entries, 'backing': backing,
                          'retained_green_indices': list(art.GREEN_INDICES),
                          'pulse_indices': list(art.PULSE_INDICES), 'source_input_sha256': inputs}, compact=True)


def image_of(snapshot, entry, stage=3, phase=0):
    return rgba(entry['indices'], entry['size'], snapshot['stage_pulse_palettes'][stage][phase])


def find(snapshot, role, variation=0):
    return next(e for e in snapshot['entries'] if e['role'] == role and e.get('variation', 0) == variation)


def source_catalog(snapshot, out, status):
    out.mkdir(parents=True, exist_ok=True)
    native = []
    cw, ch, cols = 330, 204, 3
    board = Image.new('RGB', (cw * cols, 56 + ch * math.ceil(len(snapshot['entries']) / cols)), BG)
    draw = ImageDraw.Draw(board)
    label(draw, (6, 3), f'{status} / {snapshot["style"]}. {snapshot["name"]} / new native prefabs and grouped trees')
    label(draw, (6, 22), 'Each role is drawn at its own final dimensions. Native deep form + exact2x inspection; no small image is enlarged into a new asset.', DIM)
    for n, entry in enumerate(snapshot['entries']):
        role, variation = entry['role'], entry.get('variation', 0)
        folder = out / 'native'; folder.mkdir(exist_ok=True)
        stem = f'{role}-v{variation}'
        colors = snapshot['stage_pulse_palettes'][3][0]
        pi = folder / f'{stem}-indexed.png'; indexed(entry['indices'], entry['size'], colors).save(pi, bits=4)
        for stage in (0, 3):
            path = folder / f'{stem}-stage{stage}.png'; image_of(snapshot, entry, stage).save(path)
        check = Image.open(pi).convert('RGBA'); expected = image_of(snapshot, entry)
        assert check.tobytes() == expected.tobytes()
        x, y = n % cols * cw, 56 + n // cols * ch
        label(draw, (x + 6, y + 2), f'{role} / {entry["size"][0]}x{entry["size"][1]} native pixels')
        label(draw, (x + 6, y + 19), entry.get('layer', 'BG drawing'), DIM)
        paste(board, expected, (x + 6, y + 45)); paste(board, expected, (x + 124, y + 45), 2)
        native.append({k: v for k, v in entry.items() if k != 'indices'} | {
            'native_indexed': str(pi.relative_to(out)),
            'native_healthy': f'native/{stem}-stage0.png', 'native_deep': f'native/{stem}-stage3.png',
            'catalog_native_rect': [x + 6, y + 45, *entry['size']],
            'catalog_inspection_rect': [x + 124, y + 45, entry['size'][0] * 2, entry['size'][1] * 2]})
    board.save(out / 'native-roles-source.png')
    write(out / 'native-manifest.json', {'style': snapshot['style'], 'entries': native,
          'footprint_note': 'Prefab footprint is a placement extent in metatiles, not a newly invented collider. The room plan owns collision and permitted overhang.'})
    hero = find(snapshot, 'hero'); frames = []
    for phase in range(4):
        frame = Image.new('RGB', (480, 194), BG); d = ImageDraw.Draw(frame)
        label(d, (5, 3), f'{status} / {snapshot["name"]}: literal palette phase{phase}, fixed180ms SOURCE hold')
        for stage in range(4):
            label(d, (stage * 120 + 5, 29), f'Depth stage{stage}', DIM)
            paste(frame, image_of(snapshot, hero, stage, phase), (stage * 120 + 5, 55))
        frame.save(out / f'hero-palette-phase-{phase}-source.png'); frames.append(frame)
    gif = exact_gif(frames, out / 'hero-palette-pulse-source.gif')
    write(out / 'source-gif.json', gif)
    comparisons = []
    for left in snapshot['entries']:
        for right in snapshot['entries']:
            if left['role'] >= right['role'] or left['size'] == right['size']:
                continue
            a = indexed(left['indices'], left['size'], snapshot['stage_pulse_palettes'][3][0])
            b = indexed(right['indices'], right['size'], snapshot['stage_pulse_palettes'][3][0])
            equal = a.resize(tuple(right['size']), Image.Resampling.NEAREST).tobytes() == b.tobytes()
            assert not equal, ('Different native roles are identical nearest-neighbor resizes', left['role'], right['role'])
            comparisons.append({'roles': [left['role'], right['role']], 'identical_nearest_resize': equal})
    write(out / 'native-size-distinctions.json', {'comparisons': comparisons,
          'method': 'Compare final nibble data under nearest-neighbor resizing only as a diagnostic. Authored assets themselves are never resized for use.'})
    markdown(out / 'README.md', [f'# {snapshot["style"]}. {snapshot["name"]}: native adaptive source', '',
        '**SOURCE drawings and palette inspection, not mGBA screenshots.**', '',
        '![All native roles](native-roles-source.png)', '',
        '[Native files and physical-role metadata](native-manifest.json) · '
        '[Four depth/pulse palette states](hero-palette-pulse-source.gif) · '
        '[Different-size drawing check](native-size-distinctions.json)', '',
        'Small remnants, standalone trees, groves, long branches and large hero compositions are distinct native drawings. '
        'The resident atlas and real room plan decide which fits. A source canvas/alpha bound is not a claim of walkable space or collision.', '',
        'The phase GIF uses fixed inspection holds. Healthy/deep changes use the engine-declared RGB555 palette tables over the new native geometry; '
        'no screenshot is graded. Retained-green ink roles stay distinct from other leaves that become discolored with depth.'])
    prefabs = [e for e in snapshot['entries'] if e['category'] == 'resident_prefab']
    authored = [e for e in snapshot['entries'] if e['category'] == 'authored_tree_group']
    special = [e for e in snapshot['entries'] if e['category'] == 'resident_special_map']
    return {'style': snapshot['style'], 'profile': snapshot['profile'], 'name': snapshot['name'],
            'native_prefabs': len(prefabs), 'special_native_maps': len(special),
            'authored_tree_instances': len(authored), 'native_images': len(native),
            'native_pixels': sum(e['size'][0] * e['size'][1] for e in snapshot['entries']),
            'raw_prefab_8x8_cells': sum(e['size'][0] * e['size'][1] // 64 for e in prefabs + special),
            'raw_authored_8x8_cells': sum(e['size'][0] * e['size'][1] // 64 for e in authored),
            'source_gif': gif}


def hero_board(snapshots, out, status):
    cw, ch, cols = 426, 196, min(2, len(snapshots))
    board = Image.new('RGB', (cw * cols, 56 + ch * math.ceil(len(snapshots) / cols)), BG); draw = ImageDraw.Draw(board)
    label(draw, (5, 3), f'{status} / {len(snapshots)} adaptive canopy directions / native96px hero drawings')
    label(draw, (5, 22), 'Native healthy + native deep + exact2x deep inspection. These are new large source anatomies, not enlarged small crowns.', DIM)
    panels = []
    for n, snapshot in enumerate(snapshots):
        entry = find(snapshot, 'hero'); x, y = n % cols * cw, 56 + n // cols * ch
        label(draw, (x + 5, y), f'{snapshot["style"]}. {snapshot["name"]}')
        for col, stage in enumerate((0, 3)):
            image = image_of(snapshot, entry, stage)
            paste(board, image, (x + 5 + col * 108, y + 34))
            panels.append({'style': snapshot['style'], 'role': 'hero', 'stage': stage,
                           'rect': [x + 5 + col * 108, y + 34, *image.size], 'scale': 1,
                           'rgba_sha256': hashlib.sha256(image.tobytes()).hexdigest()})
        paste(board, image_of(snapshot, entry), (x + 222, y + 34), 2)
    board.save(out / 'native-hero-directions-source.png')
    write(out / 'source-comparison-manifest.json', {'hero_panels': panels})


def plan_figure(snapshot, row, report_path, out):
    """Current native art on a recorded engine plan, never a fake framebuffer."""
    plan = row['adaptive_planner']; semantic = row['semantic_canopy']
    w, h = plan.get('room_dimensions', semantic['dimensions']); cell = 16
    size = (w * cell, h * cell); stage = int(plan['stats']['stage'])
    solid = {tuple(p) for p in plan['solid_cells']}
    projected = {tuple(p) for p in plan['projected_cells']}
    eligible = {tuple(p) for p in semantic['mask_cells']}
    field = Image.new('RGB', size, '#485038')
    layer_note = 'Flat grey diagnostic ground; other scene content is not drawn.'
    reconstruction = row.get('resident_BG2_layer')
    if reconstruction and reconstruction.get('path'):
        layer_path = (report_path.parent / reconstruction['path']).resolve()
        assert layer_path.is_relative_to(report_path.parent.resolve())
        if reconstruction.get('sha256'): assert sha(layer_path) == reconstruction['sha256']
        field = Image.open(layer_path).convert('RGB'); assert field.size == size
        layer_note = 'Actual resident BG2 ground-layer reconstruction; other BG1/OBJ content is not drawn.'
    mask = Image.new('RGB', size, '#485038'); md = ImageDraw.Draw(mask)
    for x, y in eligible:
        assert 0 <= x < w and 0 <= y < h
        md.rectangle((x * cell, y * cell, x * cell + 15, y * cell + 15), fill='#283c30')
    for x, y in projected:
        md.rectangle((x * cell, y * cell, x * cell + 15, y * cell + 15), fill='#807040')
    source = field.copy(); colors = snapshot['stage_pulse_palettes'][stage][0]
    if snapshot['backing']:
        backing = snapshot['backing'][0]
        base = rgba(backing['indices'], backing['size'], colors, display=True)
        for x, y in solid: paste(source, base, (x * cell, y * cell))
    placements = []
    for placed in plan['placements']:
        role = 'branch-solid' if placed['role'] == 'branch' and not placed['flags'] & 2 else placed['role']
        entry = find(snapshot, role, 0)
        assert entry['category'] in ('resident_prefab', 'resident_special_map')
        assert entry['size'] == placed['native_size_pixels'], placed
        x, y = placed['origin_cells']; px, py = x * cell, y * cell
        ww, hh = entry['size']
        assert placed['bounds_pixels'] == [px, py, px + ww, py + hh]
        assert 0 <= px and 0 <= py and px + ww <= size[0] and py + hh <= size[1]
        picture = rgba(entry['indices'], entry['size'], colors, display=True)
        paste(source, picture, (px, py))
        placements.append({'role': entry['role'], 'component': placed['component'],
                           'flags': placed['flags'], 'native_size_pixels': entry['size'],
                           'bounds_pixels': placed['bounds_pixels'], 'index_sha256': entry['index_sha256']})
    annotated = source.copy(); ad = ImageDraw.Draw(annotated)
    for n, placed in enumerate(placements):
        x0, y0, x1, y1 = placed['bounds_pixels']
        ad.rectangle((x0, y0, x1-1, y1-1), outline='#c8a850' if placed['flags'] & 2 else '#a8b8b0')
        label(ad, (x0 + 2, y0 + 1), n, '#f8e8b0')
    selected = row.get('selected_native_placement')
    if selected:
        box = selected['bounds_pixels']; ad.rectangle((box[0], box[1], box[2]-1, box[3]-1), outline='#f8e8b0', width=2)
    board = Image.new('RGB', (size[0] * 3, 70 + size[1]), BG); draw = ImageDraw.Draw(board)
    label(draw, (5, 3), f'SOURCE PLAN / {snapshot["name"]} / {row["name"]} / recorded engine mask and native sizes')
    label(draw, (5, 22), 'This is a room-scale source/placement reconstruction, not a240x160 mGBA framebuffer. No drawing is scaled to fit.', DIM)
    for col, (title, image) in enumerate((('Recorded eligible mask / projected lanes', mask),
                                         ('Native source drawings on that plan', source),
                                         ('Exact native bounds / placement IDs', annotated))):
        label(draw, (col * size[0] + 5, 48), title, DIM); board.paste(image, (col * size[0], 70))
    name = row['name'] + '-recorded-plan-source.png'; board.save(out / name)
    return {'path': name, 'source_report': str(report_path), 'source_report_sha256': sha(report_path),
            'source_case': row['name'], 'source_rom_sha256': None,
            'room_size_pixels': list(size), 'cell_size': cell, 'stage': stage, 'phase': 0,
            'method': layer_note + ' Underbrush is schematic quiet backing; native prefab pixels/positions/sizes are literal. '
                      'The actual renderer boundary treatment, other layers, actors and palette time are not simulated.',
            'eligible_cells': len(eligible), 'solid_cells': len(solid), 'projected_cells': len(projected),
            'placements': placements, 'planner_stats': plan['stats']}


def source_main(args):
    out, work = args.out.resolve(), args.work.resolve(); out.mkdir(parents=True, exist_ok=True); work.mkdir(parents=True, exist_ok=True)
    freezes = {s: frozen(work, s + 18, args.final) for s in args.styles}
    def run(style):
        path = work / 'source-snapshots' / f'style-{style:02}.json'; path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, str(Path(__file__).resolve()), 'worker', '--style', str(style),
                        '--snapshot', str(path), '--art-module', args.art_module], check=True, cwd=ROOT)
        return style, json.loads(path.read_text())
    with ThreadPoolExecutor(max_workers=min(4, len(args.styles))) as pool: snapshots = dict(pool.map(run, args.styles))
    inputs = snapshots[args.styles[0]]['source_input_sha256']
    assert all(s['source_input_sha256'] == inputs for s in snapshots.values()), 'Mixed source inputs'
    assert all(sha(ROOT / p) == digest for p, digest in inputs.items()), 'Source changed during export'
    status = 'FROZEN' if args.final else 'DRAFT'
    summaries = []
    for style in args.styles:
        base = out / f'variant-{style:02}'; summary = source_catalog(snapshots[style], base, status)
        summary['freeze'] = freezes[style]; summaries.append(summary)
        write(base / 'snapshot.json', snapshots[style], compact=True)
    hero_board([snapshots[s] for s in args.styles], out, status)
    plans = []
    if args.plan_report:
        report = json.loads(args.plan_report.read_text())
        if args.final:
            assert report['source_commit'] == freezes[args.styles[0]]['source_commit']
        selected = [row for row in report['captures'] if row['name'] in args.plan_cases]
        assert {r['name'] for r in selected} == set(args.plan_cases)
        for style in args.styles:
            base = out / f'variant-{style:02}'
            for row in selected:
                record = plan_figure(snapshots[style], row, args.plan_report.resolve(), base)
                record['path'] = f'variant-{style:02}/' + record['path']; record['style'] = style
                record['source_rom_sha256'] = report['rom_sha256']; plans.append(record)
        write(out / 'recorded-plan-source-manifest.json', {'plans': plans})
    markdown(out / 'README.md', [f'# {len(args.styles)} native adaptive canopy directions', '',
        '**SOURCE assets and original native sizes. Real mGBA evidence is separate.**', '',
        '![Native large compositions](native-hero-directions-source.png)', '',
        *[f'- [{s["style"]}. {s["name"]}](variant-{s["style"]:02}/README.md)' for s in summaries], '',
        'Every role has its own native anatomy and dimensions. The room mask/placement plan chooses a fitting drawing; '
        'the gallery does not generate a field of repeated small caps. Separate plan diagnostics show actual drawing bounds, '
        'placement extents and the room’s physical mask. Source figures alone do not establish in-game composition or visibility.', '',
        *(['[Recorded room-plan source figures](recorded-plan-source-manifest.json)'] if plans else []), '',
        '[Source inputs, native inventory and file hashes](source-manifest.json)'])
    manifest = {'source_commit': next(iter({v['source_commit'] for v in freezes.values()})),
                'status': status, 'tool_sha256': LOADED_SHA, 'profiles': summaries,
                'recorded_plan_figures': len(plans),
                'source_input_sha256': inputs, 'files': {}}
    assert len({v['source_commit'] for v in freezes.values()}) == 1
    if args.final:
        for style in args.styles: assert frozen(work, style + 18, True) == freezes[style]
    for p in sorted(out.rglob('*')):
        if p.is_file() and p != out / 'source-manifest.json':
            manifest['files'][str(p.relative_to(out))] = {'sha256': sha(p), 'bytes': p.stat().st_size}
    assert sha(__file__) == LOADED_SHA, 'Gallery tool changed during export'
    write(out / 'source-manifest.json', manifest)
    print(json.dumps({'styles': len(summaries), 'prefabs': sum(s['native_prefabs'] for s in summaries),
                      'files': len(manifest['files']), 'source': manifest['source_commit']}))


def keyframes(row):
    frames = row.get('phase_keyframes', []) + row.get('action_keyframes', [])
    for field in ('worst_visibility_keyframe', 'displayed_character_keyframe'):
        value = row.get(field)
        if value and value not in frames: frames.append(value)
    return frames


def exact_copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
    assert sha(source) == sha(target)


def capture_root(out, profile):
    return out / 'actual' / f'variant-{profile - 18:02}'


def actual_board(out, reports, case_name, name, title, selections=None):
    grid = selections is None
    cols = 2 if grid else len(selections)
    nrows = math.ceil(len(reports) / cols) if grid else len(reports)
    board = Image.new('RGB', (240 * cols, 54 + 190 * nrows), BG); draw = ImageDraw.Draw(board)
    label(draw, (5, 3), title)
    label(draw, (5, 22), 'ACTUAL mGBA / native 240x160; captions outside game pixels.', DIM)
    panels = []
    for n, (profile, report) in enumerate(sorted(reports.items())):
        row = next(r for r in report['captures'] if r['name'] == case_name)
        choices = [('image', row['image'])] if grid else [(choice, next(f['path'] for f in keyframes(row) if f['label'] == choice)) for choice in selections]
        for col, (choice, relative) in enumerate(choices):
            x, y = ((n % cols) * 240, 54 + (n // cols) * 190) if grid else (col * 240, 54 + n * 190)
            path = capture_root(out, profile) / relative
            image = Image.open(path).convert('RGB'); assert image.size == (240, 160)
            label(draw, (x + 3, y), f'{profile - 18}. {report.get("recipe", "Adaptive canopy")}')
            label(draw, (x + 3, y + 14), case_name if grid else choice, DIM)
            board.paste(image, (x, y + 30))
            panels.append({'profile': profile, 'style': profile - 18, 'case': case_name, 'selector': choice,
                           'source': str(path.relative_to(out)), 'source_sha256': sha(path),
                           'rgb_sha256': hashlib.sha256(image.tobytes()).hexdigest(),
                           'rect': [x, y + 30, 240, 160], 'kind': row.get('fixture_kind')})
    target = out / name; board.save(target); check = Image.open(target).convert('RGB')
    for panel in panels:
        x, y, w, h = panel['rect']
        assert check.crop((x, y, x+w, y+h)).tobytes() == Image.open(out / panel['source']).convert('RGB').tobytes()
    return {'path': name, 'sha256': sha(target), 'panels': panels}


def actual_main(args):
    work, out = args.work.resolve(), args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    reports, summaries = {}, []
    for style in args.styles:
        profile = style + 18; base = work / f'runtime/v{profile}'
        report_path = base / 'capture.json'; report = json.loads(report_path.read_text())
        expected = frozen(work, profile, args.final)
        assert report['forest_variant'] == profile
        if args.final:
            assert report.get('complete') and report['passed'] == report['total'] and not report.get('failures')
            assert report['source_commit'] == expected['source_commit'] and report['rom_sha256'] == expected['rom_sha256']
            assert report['capture_tool_sha256'] == sha(ROOT / 'tools/forest_canopy_adaptive_review.py')
        destination = capture_root(out, profile); destination.mkdir(parents=True, exist_ok=True)
        exact_copy(report_path, destination / 'capture.json')
        paths = set()
        for row in report['captures']:
            paths.update(row.get('native_frames', []))
            for field in ('image', 'after_image', 'filmstrip', 'video', 'gif'):
                if row.get(field): paths.add(row[field])
            for frame in keyframes(row):
                paths.add(frame['path'])
                if frame.get('sha256'): assert sha(base / frame['path']) == frame['sha256']
            layer = row.get('resident_BG2_layer')
            if layer and layer.get('path'): paths.add(layer['path'])
        for relative in sorted(paths):
            path = (base / relative).resolve(); assert path.is_relative_to(base.resolve())
            assert 'all-frames' not in Path(relative).parts
            exact_copy(path, destination / relative)
        lines = [f'# {style}. {report.get("recipe", "Adaptive canopy")}: actual mGBA', '',
                 'Generated-room views and ordinary-input motion from the frozen ROM. Player, camera, inventory and controlled action-RNG fixtures are disclosed in the report. '
                 'Source drawings and room-layer reconstructions are separate.', '', '[Complete report](capture.json)', '']
        for row in report['captures']:
            lines += [f'## {row["name"]}', '', f'Seed {row.get("seed")} · room {row.get("cell")} · {row.get("note", "")}', '',
                      f'![Actual native framebuffer]({row["image"]})', '']
            links = [f'[{title}]({row[field]})' for field, title in [('after_image','After'),('filmstrip','Native filmstrip'),('video','Full-rate MP4'),('gif','Exact-palette GIF')] if row.get(field)]
            links += [f'[{f["label"]}]({f["path"]})' for f in keyframes(row)]
            if row.get('resident_BG2_layer', {}).get('path'):
                links.append('[Ground-layer reconstruction, not a framebuffer](' + row['resident_BG2_layer']['path'] + ')')
            lines += [' · '.join(links), '']
        lines += ['Body-only and complete displayed-character minima are different measurements; a native attached cape can legitimately cover body pixels. '
                  'MP4s are lossy viewing copies; exact-color GIFs and native PNGs retain their stated fidelity. Raw all-frame archives remain local.']
        markdown(destination / 'README.md', lines)
        reports[profile] = report
        summaries.append({'style': style, 'profile': profile, 'contexts': len(report['captures']),
                          'passed': report['passed'], 'total': report['total'],
                          'movies': sum(bool(r.get('video')) for r in report['captures']),
                          'gifs': sum(bool(r.get('gif')) for r in report['captures']), 'active_files': len(paths),
                          'rom_sha256': report['rom_sha256']})
    common = set.intersection(*[{r['name'] for r in report['captures']} for report in reports.values()])
    boards = []
    for case in ('isolated-small','narrow-arm','broad-healthy','broad-deep','separated-corner'):
        if case in common:
            filename = {'broad-healthy': 'ten-healthy-canopies-actual.png',
                        'broad-deep': 'ten-deep-canopies-actual.png'}.get(case, case + '-ten-directions-actual.png')
            boards.append(actual_board(out, reports, case, filename,
                                       'Ten adaptive canopy directions / ' + case))
    for case in sorted(common):
        rows = [next(r for r in report['captures'] if r['name'] == case) for report in reports.values()]
        if all({'Before','Under','Emerged'} <= {f['label'] for f in keyframes(row)} for row in rows):
            boards.append(actual_board(out, reports, case, case + '-motion-actual.png',
                                       'Actual native passage / ' + case, ['Before','Under','Emerged']))
    assert boards, 'No actual comparison board could be constructed'
    write(out / 'actual-panel-manifest.json', {'boards': boards,
          'method': 'Every native240x160 rectangle independently decoded and compared byte-for-byte with its linked mGBA framebuffer.'})
    markdown(out / 'actual/README.md', ['# Actual adaptive-canopy mGBA recordings', '',
        '[Ten healthy views](../ten-healthy-canopies-actual.png) · [Ten deep-blighted views](../ten-deep-canopies-actual.png)', '',
        *[f'- [Option {r["style"]}](variant-{r["style"]:02}/README.md): {r["contexts"]} contexts.' for r in summaries], '',
        'Resident ground-layer exports are labelled reconstructions; they are not hardware framebuffers. '
        'Native placement sizes and connected-mask plans are recorded separately from visual screenshots.'])
    assert sha(__file__) == LOADED_SHA, 'Publication tool changed during copy'
    summary = {'styles': summaries, 'contexts': sum(r['contexts'] for r in summaries),
               'passed': sum(r['passed'] for r in summaries), 'total': sum(r['total'] for r in summaries),
               'movies': sum(r['movies'] for r in summaries), 'gifs': sum(r['gifs'] for r in summaries),
               'boards': len(boards), 'panels': sum(len(b['panels']) for b in boards), 'tool_sha256': LOADED_SHA,
               'source_commits': sorted({r['source_commit'] for r in reports.values()})}
    write(out / 'actual-publication-summary.json', summary)
    print(json.dumps({k:v for k,v in summary.items() if k != 'styles'}))


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('worker'); p.add_argument('--style', type=int, required=True); p.add_argument('--snapshot', type=Path, required=True)
    p.add_argument('--art-module', default='forest_canopy_adaptive')
    p = sub.add_parser('source'); p.add_argument('--work', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--styles', type=int, nargs='+', default=list(STYLES)); p.add_argument('--art-module', default='forest_canopy_adaptive')
    p.add_argument('--plan-report', type=Path); p.add_argument('--plan-cases', nargs='+', default=['broad-healthy', 'broad-deep'])
    p.add_argument('--final', action='store_true')
    p = sub.add_parser('actual'); p.add_argument('--work', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--styles', type=int, nargs='+', default=list(STYLES)); p.add_argument('--final', action='store_true')
    args = parser.parse_args()
    if args.mode == 'worker': worker(args)
    elif args.mode == 'source':
        assert args.styles and set(args.styles) <= set(STYLES)
        source_main(args)
    else:
        assert args.styles and set(args.styles) <= set(STYLES)
        actual_main(args)


if __name__ == '__main__': main()
