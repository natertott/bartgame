#!/usr/bin/env python3
"""Publish five complete forest studies from final frozen-ROM evidence.

Source-native catalogs and actual mGBA output remain separate. Captured native
frames, filmstrips, exact-palette GIFs and full-rate MP4 viewing copies are
copied unchanged. Comparison sheets only concatenate literal 240x160 captured
frames, with captions outside the game pixels. Raw all-frame archives and
third-party game graphics stay local.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
NATIVE = (240, 160)
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
BG, FG = '#101820', '#e8c878'
GROUPS = ('landscapes', 'rooms', 'npcs', 'interiors', 'interactive', 'gates', 'control')
GROUP_LABELS = {'landscapes': 'Terrain and forest depth', 'rooms': 'All 25 generated room views',
                'npcs': 'Forest folk and dialogue', 'interiors': 'Cave, hollow and thicket interiors',
                'interactive': 'Objects, entrances and item interactions',
                'gates': 'Inter-room barriers: actual actions', 'control': 'Unchanged Drain control'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def markdown(path, lines):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines).rstrip() + '\n')


def safe(base, relative):
    base = Path(base).resolve()
    path = (base / relative).resolve()
    assert path.is_relative_to(base), ('evidence path escapes its folder', relative)
    return path


def exact_copy(source, destination):
    source, destination = Path(source), Path(destination)
    assert source.is_file(), source
    assert source.stat().st_size < 100_000_000, ('oversized publication file', source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    assert sha(source) == sha(destination), ('copy changed bytes', source, destination)


def passing(report, name):
    assert report['passed'] == report['total'] and not report.get('failures'), ('final evidence failed', name)
    assert report['total'] > 0, ('empty evidence report', name)


def validate_inputs(work):
    """Reject mutable pilots or incomplete runs before writing final output."""
    inventory = work / 'inventory.json'
    source = read(work / 'gallery/source-manifest.json')
    assert source['source_only'] is True and source['profiles'] == [1, 2, 3, 4, 5]
    assert source['total_frame_instances'] == 2760
    assert sha(inventory) == source['inventory_sha256'], 'source catalog inventory is stale'
    assert {v['profile'] for v in source['variants']} == set(range(1, 6))
    for variant in source['variants']:
        assert (variant['frame_count'], variant['bg_frame_count'], variant['sprite_frame_count']) == (552, 528, 24)
        for animation in variant['animations']:
            assert animation['exact_palette'] and animation['decoded_rgb_verified']
    for relative, expected in source['files'].items():
        expected = expected['sha256'] if isinstance(expected, dict) else expected
        assert sha(safe(work / 'gallery', relative)) == expected, ('source catalog file changed', relative)
    freezes, reports = {}, {}
    for variant in range(6):
        directory = work / f'frozen/v{variant}'
        frozen = freezes[variant] = read(directory / 'freeze.json')
        assert frozen['variant'] == frozen['forest_variant'] == variant
        assert sha(directory / 'bartgame.gba') == frozen['rom_sha256'], ('ROM differs from freeze', variant)
        assert (directory / 'bartgame.gba').stat().st_size == frozen['rom_bytes']
        for group in ('source_file_sha256', 'code_file_sha256'):
            for relative, expected in frozen.get(group, {}).items():
                assert sha(ROOT / relative) == expected, ('frozen source changed', variant, relative)
        for relative, expected in source['source_sha256'].items():
            assert sha(ROOT / relative) == expected, ('source gallery painter changed', relative)
            if relative in frozen.get('source_file_sha256', {}):
                assert frozen['source_file_sha256'][relative] == expected, ('source gallery differs from ROM', variant, relative)
        report = reports[variant] = read(work / f'runtime/v{variant}/capture.json')
        passing(report, f'runtime/v{variant}')
        assert report['complete'] is True and not report.get('missing'), ('incomplete forest review', variant)
        assert report['forest_variant'] == variant
        assert report['source_commit'] == frozen['source_commit']
        assert report['rom_sha256'] == frozen['rom_sha256']
        assert report['capture_tool_sha256'] == sha(ROOT / 'tools/forest_concept_review.py'), ('superseded capture tool', variant)
        assert report['freeze_sha256'] == sha(directory / 'freeze.json')
        for relative, expected in report['frozen_input_sha256'].items():
            assert sha(safe(directory, relative)) == expected, ('frozen capture input changed', variant, relative)
        assert report['capture_count'] == len(report['captures'])
        assert len({row['name'] for row in report['captures']}) == len(report['captures'])
        assert len([row for row in report['captures'] if row['group'] == 'rooms']) == 25
        assert len([row for row in report['captures'] if row.get('movie')]) == 10
        assert set(report['groups']) == set(GROUPS)
        assert all(check['passed'] for check in report['checks'])
        terminal = {check['name'] for check in report['checks'] if check['passed']}
        assert {'frozen ROM unchanged after capture', 'entire frozen bundle stayed immutable during capture',
                'capture tool stayed immutable during capture', 'every requested natural feature found'} <= terminal, ('capture has not finished', variant)
    assert len({f['source_commit'] for f in freezes.values()}) == 1, 'mixed source freezes'
    verification = read(work / 'source-gallery-verification.json')
    passing(verification, 'independent source catalog verification')
    assert verification['source_commit'] == freezes[0]['source_commit']
    baseline = {row['name']: row for row in reports[0]['captures']}
    for variant, report in reports.items():
        rows = {row['name']: row for row in report['captures']}
        assert rows.keys() == baseline.keys(), ('different case sets', variant)
        for name, row in rows.items():
            control = baseline[name]
            for field in ('group', 'seed', 'cell', 'position', 'target', 'facing', 'physical_contract',
                          'final_physical_contract', 'maze_sha256', 'inputs'):
                assert row.get(field) == control.get(field), ('mismatched comparison fixture', variant, name, field)
            assert row['initial']['camera'] == control['initial']['camera']
    static = read(work / 'audit/static.json'); passing(static, 'independent static audit')
    audit = read(work / 'audit/finalaudit.json'); passing(audit, 'independent final audit')
    assert audit['auditor_sha256'] == sha(ROOT / 'tools/forest_concept_audit.py'), 'superseded independent auditor'
    assert audit['inventory_sha256'] == sha(inventory)
    assert audit['runtime']['status'] == 'compared', 'final audit did not inspect actual runtime'
    assert {p['variant'] for p in audit['profiles']} == set(range(6))
    assert {p['variant'] for p in audit['runtime']['profiles']} == set(range(6))
    for row in audit['profiles']:
        frozen = freezes[row['variant']]
        assert row['rom_sha256'] == frozen['rom_sha256'] and row['source_commit'] == frozen['source_commit']
    for row in audit['runtime']['profiles']:
        report = reports[row['variant']]
        assert row['rom_sha256'] == report['rom_sha256'] and row['cases'] == report['capture_count']
        assert row['capture_checks'] == {'passed': report['passed'], 'total': report['total']}
    return source, freezes, reports, audit


def source_gallery(work, out, source):
    for path in sorted((work / 'gallery').rglob('*')):
        if path.is_file(): exact_copy(path, out / 'source' / path.relative_to(work / 'gallery'))
    return {'path': 'source/README.md', 'manifest': 'source/source-manifest.json',
            'native_frame_instances': source['total_frame_instances'], 'variants': source['variants'],
            'note': 'Native SOURCE catalogs and assembled patches. Fixed review holds are not real gameplay timing.'}


def copy_capture(work, out, variant, report, frozen):
    source = work / f'runtime/v{variant}'
    destination = out / 'actual' / (f'variant-{variant:02d}' if variant else 'control-v0')
    destination.mkdir(parents=True, exist_ok=True)
    result = copy.deepcopy(report)
    copied, omitted = set(), []
    for row in result['captures']:
        active = [row['image'], *row.get('native_frames', [])]
        for key in ('after_image', 'filmstrip', 'video'):
            if row.get(key): active.append(row[key])
        archival = {}
        if row.get('all_frames'):
            archival['all_frames'] = row.pop('all_frames')
            archival['note'] = 'Local archival raw frames only; this is not an active publication path.'
        else: row.pop('all_frames', None)
        if row.get('gif'):
            assert row['gif_metadata']['exact_palette'], ('inexact GIF listed as active', variant, row['name'])
            active.append(row['gif'])
        elif row.get('movie'):
            omitted.append({'capture': row['name'], 'metadata': row.get('gif_metadata'),
                            'note': 'Exact full-sequence GIF unavailable; native PNGs and full-rate MP4 remain.'})
        for relative in active:
            exact_copy(safe(source, relative), safe(destination, relative)); copied.add(relative)
        for relative in [row['image'], *row.get('native_frames', []), *([row['after_image']] if row.get('after_image') else [])]:
            with Image.open(destination / relative) as image:
                assert image.size == NATIVE, ('not a native framebuffer', variant, relative, image.size)
        if archival: row['archival_formats'] = archival
    result['rooms'] = [row for row in result['captures'] if row['group'] == 'rooms']
    result['publication'] = {'source_report_sha256': sha(source / 'capture.json'),
                             'source_commit': frozen['source_commit'], 'forest_variant': variant,
                             'method': 'Active media are byte-identical frozen-ROM captures; only raw archival path metadata is separated.'}
    write(destination / 'capture.json', result)
    exact_copy(source / 'capture.json', out / f'validation/runtime/v{variant}-original-capture.json')
    label = frozen['label'] if variant else 'Production forest control'
    browse(destination, label, result)
    return {'variant': variant, 'label': label, 'path': str(destination.relative_to(out)),
            'captures': len(result['captures']), 'passed': result['passed'], 'total': result['total'],
            'movies': sum(bool(row.get('video')) for row in result['captures']), 'files_copied': len(copied),
            'rom_sha256': frozen['rom_sha256'], 'source_report_sha256': sha(source / 'capture.json'),
            'omitted_gifs': omitted}


def human(name):
    special = {'healthy-canopy': 'Healthy forest', 'mixed-forest': 'Mixed forest', 'deep-blight': 'Deep forest',
               'water-bridge': 'Water and bridge', 'pit-bank': 'Recessed pit and bank', 'ledge-path': 'Ledge and path'}
    return special.get(name, name.replace('forest-', '').replace('outer-gate-', '').replace('-', ' ').replace('_', ' ').capitalize())


def browse(destination, label, report):
    lines = [f'# {label}: actual mGBA', '', '[Back to the five-study review](../../README.md)', '',
             'Exact 240×160 PNGs are the primary images. MP4s are full-rate, lossy viewing copies at 2× nearest-neighbour scale. '
             'Only exact-palette GIFs are linked. Captions and filmstrip labels sit outside the game pixels.', '',
             'These are generated rooms and real item actions. The report discloses seed, room, safe player position, inventory/health '
             'and cleared unrelated-enemy fixtures. It preserves terrain, generated descriptors, Bloom and ambient glitter. '
             'Source assemblies are cataloged separately.', '',
             f"{report['capture_count']} cases; {report['passed']}/{report['total']} capture checks. "
             '[Full provenance and action traces](capture.json).', '']
    for group in GROUPS:
        rows = [row for row in report['captures'] if row['group'] == group]
        if not rows: continue
        lines += ['## ' + GROUP_LABELS[group], '']
        for row in rows:
            detail = f"Seed {row['seed']}"
            if row.get('cell') is not None: detail += f" · room {row['cell']:02d}"
            if row.get('stage') is not None: detail += f" · stage {row['stage']}"
            if row.get('archetype'): detail += ' · ' + row['archetype']
            lines += ['### ' + human(row['name']), '', detail, '']
            if row.get('note'): lines += [row['note'], '']
            lines += [f'![Actual native framebuffer]({row["image"]})', '']
            links = []
            for key, text in (('after_image', 'After action'), ('filmstrip', 'Native chronological filmstrip'),
                              ('video', 'Full-rate MP4'), ('gif', 'Exact-palette GIF')):
                if row.get(key): links.append(f'[{text}]({row[key]})')
            if row.get('native_frames'): links.append(f'[Native keyframes]({row["name"]})')
            if links: lines += [' · '.join(links), '']
    markdown(destination / 'README.md', lines)


def label(draw, position, value):
    draw.fontmode = '1'; draw.text(position, str(value), font=FONT, fill=FG)


def board(out, name, title, rows, columns, reports, freezes, field='image'):
    """Literal native panels; independently decode the saved PNG to verify all."""
    width, height = 240 * len(columns), 36 + 188 * len(rows)
    image = Image.new('RGB', (width, height), BG); draw = ImageDraw.Draw(image)
    label(draw, (5, 4), title + ' / ACTUAL mGBA / unchanged 240x160 panels')
    panels = []
    for y, (variant, case_names) in enumerate(rows):
        by_name = {row['name']: row for row in reports[variant]['captures']}
        directory = 'actual/' + (f'variant-{variant:02d}' if variant else 'control-v0')
        for x, (column, case_name) in enumerate(zip(columns, case_names)):
            row = by_name[case_name]
            relative = directory + '/' + row[field]
            source = out / relative
            with Image.open(source) as decoded:
                assert decoded.size == NATIVE
                native = decoded.convert('RGB')
            px, py = x * 240, 36 + y * 188
            caption = (f"Room {row['cell']:02d} / stage {row.get('stage', '?')} / {row.get('archetype', '')}"
                       if row['group'] == 'rooms' else f"#{variant} {freezes[variant]['label']} / {column}")
            while FONT.getlength(caption) > 232: caption = caption[:-1]
            label(draw, (px + 4, py + 3), caption)
            image.paste(native, (px, py + 24))
            tick = row['video_frames'] - 1 if field == 'after_image' else 0
            state = next(state for state in row['trace'] if state['tick'] == tick)
            panels.append({'variant': variant, 'case': case_name, 'field': field,
                           'source_image': relative, 'source_png_sha256': sha(source),
                           'source_rgb_sha256': hashlib.sha256(native.tobytes()).hexdigest(),
                           'source_rectangle': [0, 0, 240, 160],
                           'destination_rectangle': [px, py + 24, px + 240, py + 184],
                           'fixture': {'seed': row['seed'], 'cell': row.get('cell'),
                                       'position': row['position'], 'facing': row['facing']},
                           'snapshot': {'tick': tick, 'area': state['area'], 'cell': state['cell'],
                                        'position': state['position'], 'camera': state['camera']},
                           'rom_sha256': freezes[variant]['rom_sha256']})
    image.save(out / name)
    with Image.open(out / name) as saved:
        saved = saved.convert('RGB')
        for panel in panels:
            with Image.open(out / panel['source_image']) as original:
                assert saved.crop(panel['destination_rectangle']).tobytes() == original.convert('RGB').tobytes(), ('changed board panel', name, panel)
    return {'path': name, 'title': title, 'sha256': sha(out / name), 'size': list(image.size),
            'pixel_policy': 'Literal full 240x160 native frames. Captions outside game pixels; no resizing, painting or grading.',
            'decoded_panels_verified': True, 'panels': panels}


def comparisons(out, reports, freezes):
    boards = []
    presets = [
        ('five-studies-healthy-mixed-deep-actual.png', 'Healthy / mixed / deep forest',
         ['Healthy', 'Mixed', 'Deep'], ['healthy-canopy', 'mixed-forest', 'deep-blight']),
        ('water-bridges-and-depth-actual.png', 'Water, usable crossings and depth',
         ['Water and bridge', 'Pit bank', 'Ledge and path'], ['water-bridge', 'pit-bank', 'ledge-path']),
        ('interiors-actual.png', 'Generated mystery interiors',
         ['Cave', 'Hollow', 'Thicket'], ['interior-cave', 'interior-hollow', 'interior-thicket']),
        ('gates-before-actual.png', 'Inter-room barriers before actual item use',
         ['Thorns', 'Bombable stone', 'Silk', 'Locked door', 'Cape crossing'],
         ['outer-gate-thorns', 'outer-gate-cracked-wall', 'outer-gate-cobweb', 'outer-gate-locked-door', 'outer-gate-chasm']),
        ('interactions-before-actual.png', 'Readable objects and item interactions',
         ['Wooden chest', 'Floor switch', 'Bombable wall', 'Silk', 'Cape hole'],
         ['forest-wood-chest', 'cave-floor-switch', 'forest-bomb-wall', 'forest-cobweb', 'forest-cape-hole']),
        ('forest-folk-actual.png', 'Forest folk in actual generated rooms',
         ['Hermit', 'Nun', 'Gardener'], ['forest-npc-hermit', 'forest-npc-nun', 'forest-npc-gardener']),
    ]
    for name, title, columns, cases in presets:
        boards.append(board(out, name, title, [(v, cases) for v in range(1, 6)], columns, reports, freezes))
    for before in ('gates', 'interactions'):
        preset = next(p for p in presets if p[0] == before + '-before-actual.png')
        boards.append(board(out, before + '-after-actual.png', preset[1] + ' / after',
                            [(v, preset[3]) for v in range(1, 6)], preset[2], reports, freezes, 'after_image'))
    for variant in range(6):
        rooms = sorted((r for r in reports[variant]['captures'] if r['group'] == 'rooms'), key=lambda row: row['cell'])
        rows = [(variant, [r['name'] for r in rooms[n:n + 5]]) for n in range(0, 25, 5)]
        name = f'actual/' + (f'variant-{variant:02d}' if variant else 'control-v0') + '/all-25-room-views-actual.png'
        value = board(out, name, '25 generated room viewports / ' + freezes[variant]['label'],
                      rows, [f'Column {n + 1}' for n in range(5)], reports, freezes)
        boards.append(value)
    result = {'source_commit': freezes[0]['source_commit'], 'boards': boards,
              'method': 'Saved board PNGs were independently decoded and every destination panel compared byte-for-byte with its linked native RGB framebuffer.'}
    write(out / 'actual-panel-manifest.json', result)
    return result


def pursuer_context(work, out, freezes):
    """Five targeted contrast clips, kept separate from the main forest suite."""
    summary = read(work / 'audit/pursuer-context-summary.json')
    assert summary['status'] == 'compared'
    assert {p['forest_variant'] for p in summary['profiles']} == set(range(1, 6))
    assert summary['passed'] == summary['total'] and summary['capture_count'] == 5
    destination = out / 'actual/pursuer-context'; destination.mkdir(parents=True, exist_ok=True)
    proof = []; copied = []; cases = []
    for record in sorted(summary['profiles'], key=lambda row: row['forest_variant']):
        variant = record['forest_variant']; frozen = freezes[variant]
        source = work / f'audit/pursuer-context/v{variant}'
        report = read(source / 'capture.json'); passing(report, f'Coin Toad context {variant}')
        assert report['capture_count'] == len(report['captures']) == record['capture_count'] == 1
        assert report['rom_sha256'] == record['rom_sha256'] == frozen['rom_sha256']
        assert report['source_commit'] == record['source_commit'] == frozen['source_commit']
        assert report['enemy_variant'] == record['enemy_variant'] == 11
        assert (record['checks_passed'], record['checks_total']) == (report['passed'], report['total'])
        mechanical = record['mechanical_comparison']
        assert mechanical['passed'] == mechanical['total'] and mechanical['candidate_rom_sha256'] == frozen['rom_sha256']
        row = report['captures'][0]
        assert row['name'] == 'pursuer-clearing' and row['kind'] == 0
        assert row['frames'] == len(row['trace']) == 96
        target = destination / f'variant{variant}'
        active = [row['image'], *row['native_frames'], row['filmstrip'], row['video']]
        result = copy.deepcopy(report); published = result['captures'][0]
        if row.get('gif'):
            assert row['gif_metadata']['exact_palette']; active.append(row['gif'])
        archive = published.pop('all_frames', None)
        if archive: published['archival_formats'] = {'all_frames': archive, 'note': 'Local raw archive, not an active publication path.'}
        for relative in active: exact_copy(safe(source, relative), safe(target, relative))
        for relative in [row['image'], *row['native_frames']]:
            with Image.open(target / relative) as image: assert image.size == NATIVE
        result['publication'] = {'forest_variant': variant, 'source_report_sha256': sha(source / 'capture.json'),
                                 'forest_binding': '../../../validation/audit/pursuer-context-summary.json',
                                 'note': 'Unchanged selected enemy11 rendered by this frozen forest ROM. Targeted contrast context, separate from the main forest capture suite.'}
        write(target / 'capture.json', result)
        exact_copy(source / 'capture.json', out / f'validation/runtime/pursuer-context-v{variant}-original-capture.json')
        links = [f'[Native filmstrip]({row["filmstrip"]})', f'[Full-rate MP4]({row["video"]})']
        if row.get('gif'): links.append(f'[Exact-palette GIF]({row["gif"]})')
        markdown(target / 'README.md', [f"# {variant}. {frozen['label']}: Coin Toad contrast", '',
                  '[Back to the five contexts](../README.md)', '', row['note'], '',
                  f'![Actual native framebuffer]({row["image"]})', '', ' · '.join(links), '',
                  '[Capture, natural spawn and player fixtures](capture.json)'])
        cases.append((variant, row, target / row['image']))
        copied.append({'forest_variant': variant, 'path': str(target.relative_to(out)),
                       'captures': 1, 'passed': report['passed'], 'total': report['total'],
                       'rom_sha256': frozen['rom_sha256'], 'source_report_sha256': sha(source / 'capture.json')})
    assert sum(row['passed'] for row in copied) == summary['passed']
    assert sum(row['total'] for row in copied) == summary['total']
    board = Image.new('RGB', (1200, 404), BG); draw = ImageDraw.Draw(board)
    label(draw, (5, 4), 'Selected Coin Toad / ACTUAL mGBA / native frames above; exact 96x80 crops at 2x nearest-neighbour below')
    for x, (variant, row, source) in enumerate(cases):
        tick = row['representative_tick']; state = row['trace'][tick]; enemy = state['target']
        with Image.open(source) as image: native = image.convert('RGB')
        ex = (enemy['x_q16'] >> 16) - state['camera'][0]
        ey = (enemy['y_q16'] >> 16) - (enemy['z_q16'] >> 16) - state['camera'][1]
        left, top = max(0, min(144, ex - 48)), max(0, min(80, ey - 48))
        crop = [left, top, left + 96, top + 80]
        label(draw, (240 * x + 4, 28), f"#{variant} {freezes[variant]['label']} / tick {tick}")
        label(draw, (240 * x + 4, 216), 'Exact captured crop / 2x NN')
        for rectangle, target_rectangle, scale in (([0, 0, 240, 160], [240*x, 48, 240*x+240, 208], 1),
                                                  (crop, [240*x+24, 236, 240*x+216, 396], 2)):
            image = native.crop(rectangle)
            if scale == 2: image = image.resize((192, 160), Image.Resampling.NEAREST)
            board.paste(image, tuple(target_rectangle[:2]))
            proof.append({'forest_variant': variant, 'case': row['name'], 'tick': tick,
                          'source_image': str(source.relative_to(out)), 'source_png_sha256': sha(source),
                          'source_rectangle': rectangle, 'destination_rectangle': target_rectangle,
                          'nearest_neighbour_scale': scale, 'rom_sha256': freezes[variant]['rom_sha256'],
                          'snapshot_camera': state['camera'], 'fixture': row['context']})
    path = destination / 'coin-toad-context-actual.png'; board.save(path)
    with Image.open(path) as decoded:
        decoded = decoded.convert('RGB')
        for panel in proof:
            with Image.open(out / panel['source_image']) as original:
                expected = original.convert('RGB').crop(panel['source_rectangle'])
            if panel['nearest_neighbour_scale'] == 2: expected = expected.resize((192, 160), Image.Resampling.NEAREST)
            assert decoded.crop(panel['destination_rectangle']).tobytes() == expected.tobytes(), ('changed Coin Toad panel', panel)
    write(destination / 'panel-manifest.json', {'source_commit': freezes[0]['source_commit'],
          'board': path.name, 'sha256': sha(path), 'decoded_panels_verified': True, 'panels': proof})
    markdown(destination / 'README.md', ['# Selected Coin Toad: five actual forest contexts', '',
             '[Back to the forest review](../../README.md)', '',
             'These five focused recordings show the unchanged selected Coin Toad on clear natural deep-forest ground. '
             'The same generated spawn, disclosed player position/health and 96 real AI updates are used in every forest treatment. '
             'This targeted contrast check is additional to the main room/interaction suite.', '',
             '![Actual native frames and exact enlarged crops](coin-toad-context-actual.png)', '',
             *[f"- [{v}. {freezes[v]['label']}](variant{v}/README.md)" for v in range(1, 6)], '',
             '[Exact panel provenance](panel-manifest.json) · [Independent forest binding and trajectory comparison](../../validation/audit/pursuer-context-summary.json)'])
    return {'captures': len(copied), 'passed': summary['passed'], 'total': summary['total'], 'profiles': copied,
            'index': 'actual/pursuer-context/README.md', 'board': 'actual/pursuer-context/' + path.name,
            'panel_manifest': 'actual/pursuer-context/panel-manifest.json'}


def validation(work, out, freezes, branch):
    base = out / 'validation'
    for name in ('inventory.json', 'builds.json', 'build-final-summary.log', 'build-baseline-final.log',
                 'source-gallery-verification.json', 'source-gallery-review.md', 'runtime-summary.json',
                 'build-restored-default.log', 'restored-default-build.log', 'build-default-restored.log'):
        if (work / name).is_file(): exact_copy(work / name, base / name)
    for variant in range(6):
        for name in ('freeze.json', 'coverage.json', 'assets.h', 'bartgame.map'):
            exact_copy(work / f'frozen/v{variant}' / name, base / f'frozen/v{variant}' / name)
        path = work / f'build-v{variant}.log'
        if path.is_file(): exact_copy(path, base / 'build' / path.name)
        path = work / f'runtime-v{variant}.log'
        if path.is_file(): exact_copy(path, base / 'runtime' / path.name)
    for name in ('static.json', 'static-summary.json', 'finalaudit.json', 'finalaudit-summary.json',
                 'visual-review-source.md', 'visual-review-actual.md', 'secondary-visual-critique.md',
                 'pursuer-context-summary.json', 'transition-timing-observations.json'):
        if (work / 'audit' / name).is_file(): exact_copy(work / 'audit' / name, base / 'audit' / name)
    probes = []
    for stem in ('actual-stages-native', 'actual-water-phases', 'actual-context-review'):
        if (work / 'audit' / (stem + '.png')).is_file():
            for suffix in ('.png', '.json'):
                exact_copy(work / 'audit' / (stem + suffix), out / 'actual/probes' / (stem + suffix))
            probes += [f'![Actual mGBA probe]({stem}.png)', '', f'[Unchanged provenance record]({stem}.json)', '']
    if probes:
        markdown(out / 'actual/probes/README.md', ['# Independent actual mGBA probes', '',
                 '[Back to the forest review](../../README.md)', '',
                 'These independent audit boards retain exact captured pixels. Stage and context panels are native framebuffers; '
                 'water panels are chronological 80×64 crops enlarged only at 2× nearest-neighbour. '
                 'Their unchanged provenance records retain local archival source filenames and hashes.', '', *probes])
    for name in ('pinned-fetches.json', 'fetches.json', 'native-source-measurements.json', 'object-source-measurements.json'):
        if (work / 'research' / name).is_file(): exact_copy(work / 'research' / name, base / 'research' / name)
    markdown(base / 'research/README.md', ['# Research provenance', '',
              'These records describe pinned source access and native measurements. The original Nintendo game graphics, '
              'source contact sheets, binary map/tileset files and extracted palettes remain local and are not redistributed here. '
              'The gallery contains original BARTGAME art and actual BARTGAME captures.', '',
              'See the project’s FOREST_READABILITY_RESEARCH.md for observations and adaptations.'])
    tools = {}
    for name in ('forest_concept_publish.py', 'forest_concept_gallery.py', 'forest_concept_audit.py', 'forest_concept_review.py'):
        relative = 'bartgame/tools/' + name
        tools[relative] = {'sha256': sha(ROOT / 'tools' / name),
                           'repository_url': f'https://github.com/natertott/bartgame/blob/{branch}/{relative}'}
    write(base / 'tool-provenance.json', {'game_art_source_commit': freezes[0]['source_commit'], 'tools': tools,
          'note': 'Review tools are separately hashed and linked in the publication branch. The game/art freeze predates final review tooling; it is not used as a false tool-code revision.'})


def slug(label):
    return re.sub(r'[^a-z0-9]+', '-', label.lower().replace('&', 'and')).strip('-')


def release_roms(work, release, freezes, branch, gallery):
    release.mkdir(parents=True, exist_ok=True)
    short = freezes[0]['source_commit'][:7]
    rows = []
    for variant in range(1, 6):
        frozen = freezes[variant]
        name = f'forest-{variant:02d}-{slug(frozen["label"])}-{short}.gba'
        exact_copy(work / f'frozen/v{variant}/bartgame.gba', release / name)
        assert sha(release / name) == frozen['rom_sha256']
        freeze_name = f'freezes/forest-{variant:02d}-freeze.json'
        exact_copy(work / f'frozen/v{variant}/freeze.json', release / freeze_name)
        rows.append({'variant': variant, 'label': frozen['label'], 'rom': name,
                     'rom_sha256': sha(release / name), 'freeze': freeze_name})
    text = [f'BARTGAME - five forest environment studies ({short})', '',
            'Five alternatives for review. None is adopted as the production forest.',
            'The ordinary profile0 remains byte-identical to the selected-enemy release.', '',
            'Each ROM uses the same generator, gameplay, Bloom, selected enemies,',
            'equipment, UI, Drain and existing glitter. Art changes across healthy,',
            'mixed and deep forest, mystery interiors and environmental interactions.', '']
    text += [f"{row['variant']}. {row['label']}: {row['rom']}" for row in rows]
    text += ['', 'Open one .gba in mGBA. No commercial game ROM is required.',
             'Start opens/closes inventory; R cycles pages; D-pad selects; A/B/L assign.',
             'On the map A zooms, B returns and D-pad browses rooms.', '',
             'Gallery and capture fixtures:', f'https://github.com/natertott/bartgame/blob/{branch}/{gallery}/README.md', '',
             'ROM-SHA256SUMS.txt checks the five ROMs. Each freezes/ file records its',
             'source commit, build command and protected/native source hashes.']
    markdown(release / 'README.txt', text)
    (release / 'ROM-SHA256SUMS.txt').write_text(''.join(f"{r['rom_sha256']}  {r['rom']}\n" for r in rows))
    archive = f'forest-concepts-{short}.zip'
    members = [row['rom'] for row in rows] + [row['freeze'] for row in rows] + ['README.txt', 'ROM-SHA256SUMS.txt']
    with zipfile.ZipFile(release / archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name in members: bundle.write(release / name, name)
    with zipfile.ZipFile(release / archive) as bundle:
        assert bundle.testzip() is None
        assert set(bundle.namelist()) == set(members) and len(bundle.namelist()) == len(members)
        assert len([name for name in bundle.namelist() if name.endswith('.gba')]) == 5
        for name in members: assert hashlib.sha256(bundle.read(name)).hexdigest() == sha(release / name), ('ZIP changed bytes', name)
    (release / 'SHA256SUMS.txt').write_text(''.join(f'{sha(release / name)}  {name}\n' for name in [*[row['rom'] for row in rows], archive]))
    return {'roms': rows, 'zip': archive, 'zip_sha256': sha(release / archive), 'zip_crc_verified': True,
            'zip_member_hashes_verified': True, 'production_baseline_included': False}


def actual_index(out, reviews):
    lines = ['# Five forest studies: actual mGBA', '', '[Back to the complete review](../README.md)', '',
             'All alternatives use matched generated rooms, standing points, camera positions and real item actions. '
             'The baseline is a control, and is not a sixth proposal.', '',
             '[Healthy / mixed / deep comparison](../five-studies-healthy-mixed-deep-actual.png) · '
             '[Water, bridges and depth](../water-bridges-and-depth-actual.png) · '
             '[Mystery interiors](../interiors-actual.png) · [Selected Coin Toad contrast](pursuer-context/README.md)', '']
    for review in reviews:
        directory = Path(review['path']).name
        lines += [f"- [{review['variant']}. {review['label']}]({directory}/README.md): "
                  f"{review['captures']} cases, {review['movies']} movies; "
                  f"[all 25 generated room viewports]({directory}/all-25-room-views-actual.png)."]
    markdown(out / 'actual/README.md', lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('work', 'out', 'release'): parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--branch', required=True)
    args = parser.parse_args()
    work, out, release = args.work.resolve(), args.out.resolve(), args.release.resolve()
    source, freezes, reports, audit = validate_inputs(work)
    out.mkdir(parents=True, exist_ok=True)
    catalog = source_gallery(work, out, source)
    reviews = [copy_capture(work, out, variant, reports[variant], freezes[variant]) for variant in [1, 2, 3, 4, 5, 0]]
    panels = comparisons(out, reports, freezes)
    bonus = pursuer_context(work, out, freezes)
    validation(work, out, freezes, args.branch)
    actual_index(out, reviews)
    releases = release_roms(work, release, freezes, args.branch, str(out.relative_to(REPO)))
    summary = {'source_commit': freezes[0]['source_commit'], 'source_art': catalog,
               'actual': reviews, 'cases': sum(r['captures'] for r in reviews),
               'capture_checks': {'passed': sum(r['passed'] for r in reviews), 'total': sum(r['total'] for r in reviews)},
               'bonus_context': bonus, 'all_actual_cases': sum(r['captures'] for r in reviews) + bonus['captures'],
               'all_actual_checks': {'passed': sum(r['passed'] for r in reviews) + bonus['passed'],
                                     'total': sum(r['total'] for r in reviews) + bonus['total']},
               'independent_audit': {'passed': audit['passed'], 'total': audit['total']},
               'actual_panel_manifest': 'actual-panel-manifest.json', 'actual_boards': len(panels['boards']),
               'releases': releases, 'format_policy': __doc__.strip()}
    write(out / 'validation/publication-summary.json', summary)
    manifest = {'source_commit': summary['source_commit'], 'files': {},
                'note': 'Hashes exclude this manifest. Parent refreshes after editorial README or direction-note additions.'}
    for directory in (out, release):
        for path in sorted(directory.rglob('*')):
            if path.is_file() and path != out / 'validation/publication-manifest.json':
                assert path.stat().st_size < 100_000_000, ('oversized publication file', path)
                manifest['files'][str(path.relative_to(REPO))] = {'sha256': sha(path), 'bytes': path.stat().st_size}
    write(out / 'validation/publication-manifest.json', manifest)
    print(json.dumps({'source': summary['source_commit'], 'cases': summary['cases'], 'checks': summary['capture_checks'],
                      'native_source_frames': source['total_frame_instances'], 'boards': summary['actual_boards'],
                      'roms': [row['rom'] for row in releases['roms']], 'zip': releases['zip'], 'files': len(manifest['files'])}))


if __name__ == '__main__':
    main()
