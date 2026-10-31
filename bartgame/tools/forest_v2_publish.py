#!/usr/bin/env python3
"""Publish the second five native forest studies and truthful mGBA evidence.

Natural generated contexts, explicit diagnostic-room fixtures, historical
illustrations and source assemblies are separate. Native game pixels are
never painted, filtered or graded. Captions sit outside captured panels.
Only referenced native keyframes, exact GIFs and full-rate lossy MP4 viewing
copies are published; raw all-frame recording directories stay local.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import zipfile

from PIL import Image, ImageDraw

import forest_concept_publish as P

ROOT, REPO = P.ROOT, P.REPO
PROFILES = tuple(range(6, 11))
FROZEN_PROFILES = (0, 1, 5, *PROFILES)
RECIPES = {6: 'Black Sap Oak', 7: 'Violet Strangler', 8: 'Witchfire Weep',
           9: 'Amethyst Canker', 10: 'Royal Bruise'}
PRODUCTION_SHA = '9330a44a4e27d99606a757134aa41a62adb122a74315c400e1ad3427048c8661'
GROUPS = ('landscapes', 'depth', 'rooms', 'npcs', 'interiors', 'interactive', 'gates', 'control')
GROUP_LABELS = {**P.GROUP_LABELS, 'depth': 'Generated depth, logs, ledges, landmarks and second wooden chest'}
EXTRA_FRAME_KEYS = ('depth_keyframes', 'pulse_phase_keyframes', 'pulse_keyframes', 'phase_keyframes',
                    'cleared_barrier_keyframe', 'cleared_keyframe')
sha, read, write, safe, exact_copy, markdown = P.sha, P.read, P.write, P.safe, P.exact_copy, P.markdown


def passing(value, label):
    assert value['passed'] == value['total'] and value['total'] > 0 and not value.get('failures'), ('failed final evidence', label)


def local(variant):
    return variant - 5


def folder(variant):
    return f'actual/variant-{local(variant):02d}' if variant in PROFILES else 'actual/control-v0'


def extra_frames(row):
    for key in EXTRA_FRAME_KEYS:
        entries = row.get(key, [])
        if isinstance(entries, dict): entries = [entries]
        for entry in entries:
            if isinstance(entry, str): yield {'path': entry}
            else:
                assert isinstance(entry, dict), (key, entry)
                if entry.get('path') or entry.get('image'):
                    label = entry.get('label')
                    if label is None and key in ('pulse_phase_keyframes', 'pulse_keyframes'): label = f'Glow phase {entry.get("phase")}'
                    if label is None and key in ('cleared_barrier_keyframe', 'cleared_keyframe'): label = 'Same-room cleared state'
                    yield {**entry, 'path': entry.get('path', entry.get('image')), 'label': label or 'Measured keyframe'}


def png_refs(row):
    return [row['image'], *row.get('native_frames', []),
            *([row['after_image']] if row.get('after_image') else []), *[r['path'] for r in extra_frames(row)]]


def validate(work):
    """Only immutable final source, complete captures and a full audit pass."""
    source = read(work / 'gallery/source-manifest.json')
    assert source['source_only'] is True and set(source['profiles']) == set(PROFILES)
    assert {r['profile'] for r in source['variants']} == set(PROFILES)
    assert source['total_frame_instances'] == sum(r['frame_count'] for r in source['variants'])
    for variant in source['variants']:
        for animation in variant.get('animations', []):
            assert animation['exact_palette'] and animation['decoded_rgb_verified']
    for relative, expected in source['files'].items():
        expected = expected['sha256'] if isinstance(expected, dict) else expected
        assert sha(safe(work / 'gallery', relative)) == expected, ('stale source gallery', relative)
    for relative, expected in source['source_sha256'].items():
        assert sha(ROOT / relative) == expected, ('source painter changed', relative)
    freezes = {}
    for variant in FROZEN_PROFILES:
        directory = work / f'frozen/v{variant}'
        frozen = freezes[variant] = read(directory / 'freeze.json')
        assert frozen.get('forest_variant', frozen['variant']) == variant
        assert sha(directory / 'bartgame.gba') == frozen['rom_sha256']
        for group in ('source_file_sha256', 'code_file_sha256'):
            assert frozen.get(group), ('missing frozen source hashes', variant, group)
            for relative, expected in frozen[group].items():
                assert sha(ROOT / relative) == expected, ('frozen live input changed', variant, relative)
        for relative, expected in source['source_sha256'].items():
            if relative in frozen.get('source_file_sha256', {}):
                assert frozen['source_file_sha256'][relative] == expected, ('catalog/ROM input differs', variant, relative)
    assert len({f['source_commit'] for f in freezes.values()}) == 1, 'mixed game/art source freezes'
    assert source['git_base_commit'] == freezes[6]['source_commit'], 'source gallery provenance has not been rebound to final freeze'
    verification = read(work / 'source-gallery-verification.json'); passing(verification, 'independent source gallery verification')
    assert verification['source_commit'] == freezes[6]['source_commit'] and verification['current_source_matches'] is True
    assert not verification['current_drift'] and verification['native_frames'] == source['total_frame_instances']
    assert verification['files'] == len(source['files'])
    assert freezes[0]['rom_sha256'] == PRODUCTION_SHA, 'production control changed'
    reports = {}
    for variant in (*PROFILES, 0):
        source_dir = work / ('runtime/control-v0' if not variant else f'runtime/v{variant}')
        report = reports[variant] = read(source_dir / 'capture.json')
        passing(report, f'capture {variant}')
        frozen = freezes[variant]
        assert report['complete'] is True and not report.get('missing')
        assert report['forest_variant'] == variant and report['source_commit'] == frozen['source_commit']
        assert report['rom_sha256'] == frozen['rom_sha256']
        assert report['freeze_sha256'] == sha(work / f'frozen/v{variant}/freeze.json')
        for relative, expected in report['frozen_input_sha256'].items():
            assert sha(safe(work / f'frozen/v{variant}', relative)) == expected
        assert report['capture_count'] == len(report['captures'])
        assert len({r['name'] for r in report['captures']}) == len(report['captures'])
        assert all(r['passed'] for r in report['checks'])
        terminal = {r['name'] for r in report['checks'] if r['passed']}
        if variant:
            assert report['schema'] == 2 and report['forest_study_round'] == 2 and report['display_variant'] == local(variant)
            assert report['capture_tool_sha256'] == sha(ROOT / 'tools/forest_v2_review.py')
            assert report['inherited_capture_tool_sha256'] == sha(ROOT / 'tools/forest_concept_review.py')
            for relative, expected in report['capture_dependency_sha256'].items():
                assert sha(ROOT / 'tools' / relative) == expected, ('capture dependency changed', relative)
            assert {'new capture tool stayed immutable during capture', 'inherited capture dependencies stayed immutable',
                    'every requested feature found'} <= terminal, ('unfinished capture', variant)
            diagnostic = [r for r in report['captures'] if r['group'] == 'diagnostic']
            natural = [r for r in report['captures'] if r['group'] != 'diagnostic']
            assert report['diagnostic_capture_count'] == len(diagnostic) and report['natural_capture_count'] == len(natural)
            assert diagnostic and natural
            assert all(r.get('diagnostic_room') and r['fixture_kind'].startswith('diagnostic') for r in diagnostic)
            assert all(r['fixture_kind'].startswith('natural') and not r.get('diagnostic_room') for r in natural)
            trials = [r['critical_path'] for r in report['routes'] if 'critical_path' in r]
            assert len(trials) == 1 and trials[0]['status'] == 0
            assert trials[0]['passed'] == trials[0]['total'] and all(trials[0]['checks'])
        else:
            assert report['capture_tool_sha256'] == sha(ROOT / 'tools/forest_concept_review.py')
            assert 'capture tool stayed immutable during capture' in terminal
    baseline = {r['name']: r for r in reports[6]['captures']}
    for variant in PROFILES:
        rows = {r['name']: r for r in reports[variant]['captures']}
        assert rows.keys() == baseline.keys(), ('different new-style case sets', variant)
        for name, row in rows.items():
            for field in ('group', 'fixture_kind', 'diagnostic_room', 'seed', 'cell', 'position', 'target', 'facing',
                          'physical_contract', 'final_physical_contract', 'maze_sha256', 'inputs'):
                assert row.get(field) == baseline[name].get(field), ('new-style comparison mismatch', variant, name, field)
    audit = read(work / 'audit/finalaudit.json'); passing(audit, 'independent final audit')
    assert audit['auditor_sha256'] == sha(ROOT / 'tools/forest_v2_audit.py')
    assert {p['variant'] for p in audit['profiles']} == set(FROZEN_PROFILES)
    assert audit['runtime']['status'] == 'compared' and audit['runtime']['baseline_profile'] == 6
    assert {p['variant'] for p in audit['runtime']['profiles']} == set(PROFILES)
    for profile in audit['profiles']:
        frozen = freezes[profile['variant']]
        assert profile['source_commit'] == frozen['source_commit'] and profile['rom_sha256'] == frozen['rom_sha256']
    for profile in audit['runtime']['profiles']:
        report = reports[profile['variant']]
        for field in ('rom_sha256', 'capture_count', 'passed', 'total', 'natural_capture_count', 'diagnostic_capture_count'):
            assert profile[field] == report[field], ('independent audit/capture mismatch', profile['variant'], field)
        if profile.get('capture_report_sha256'):
            assert profile['capture_report_sha256'] == sha(work / f"runtime/v{profile['variant']}/capture.json")
    for field in ('rom_sha256', 'capture_count', 'passed', 'total'):
        assert audit['runtime']['production_control'][field] == reports[0][field], ('independent production-control mismatch', field)
    host = audit['host_generator']; statistics = host['statistics']
    assert host['exit_code'] == 0 and statistics['failures'] == 0
    assert statistics['seeds'] >= 20000 and statistics['rooms'] == statistics['seeds'] * 25
    assert statistics['world_graphs'] == statistics['seeds'] * 3 and statistics['logs'] > 0 and statistics['item_pockets'] > 0
    assert host['rom_sha256'] == freezes[6]['rom_sha256']
    for relative, expected in host['source_sha256'].items():
        assert sha(ROOT / relative) == expected, ('host-tested source changed', relative)
    return source, freezes, reports, audit


def copy_source(work, out, manifest):
    for path in sorted((work / 'gallery').rglob('*')):
        if path.is_file(): exact_copy(path, out / 'source' / path.relative_to(work / 'gallery'))
    return {'path': 'source/README.md', 'manifest': 'source/source-manifest.json',
            'note': 'Native source assemblies and palette inspection cycles. Fixed review-clock GIFs do not claim actual engine timing.',
            'total_frame_instances': manifest.get('total_frame_instances'),
            'profiles': manifest['profiles']}


def copy_capture(work, out, variant, report):
    source = work / ('runtime/control-v0' if not variant else f'runtime/v{variant}')
    destination = out / folder(variant); destination.mkdir(parents=True, exist_ok=True)
    result = copy.deepcopy(report); copied = set(); omitted = []
    for row in result['captures']:
        active = png_refs(row)
        for key in ('filmstrip', 'video'):
            if row.get(key): active.append(row[key])
        archive = row.pop('all_frames', None)
        if archive: row['archival_formats'] = {'all_frames': archive, 'note': 'Local raw recording archive; not an active publication path.'}
        if row.get('gif'):
            assert row['gif_metadata']['exact_palette'], ('inexact active GIF', variant, row['name'])
            active.append(row['gif'])
        elif row.get('movie'): omitted.append(row['name'])
        for relative in active:
            assert not relative.startswith('all-frames/'), ('raw path listed as active media', relative)
            exact_copy(safe(source, relative), safe(destination, relative)); copied.add(relative)
        for relative in png_refs(row):
            with Image.open(destination / relative) as image: assert image.size == P.NATIVE, (relative, image.size)
        for entry in extra_frames(row):
            if entry.get('sha256'): assert sha(destination / entry['path']) == entry['sha256'], ('extra frame proof changed', variant, entry)
    result['rooms'] = [r for r in result['captures'] if r['group'] == 'rooms']
    route_images = 0
    for route in result.get('routes', []):
        if 'critical_path' not in route: continue
        trial = route['critical_path']
        for relative in [trial['log'], *trial['images']]:
            exact_copy(safe(source, relative), safe(destination, relative)); copied.add(relative)
        for relative in trial['images']:
            with Image.open(destination / relative) as image: assert image.size == P.NATIVE
        route_images += len(trial['images'])
    result['publication'] = {'source_report_sha256': sha(source / 'capture.json'), 'forest_variant': variant,
                             'display_variant': local(variant) if variant else 0,
                             'method': 'Referenced media copied unchanged. Source assemblies, diagnostics and natural contexts are separately labelled.'}
    write(destination / 'capture.json', result)
    exact_copy(source / 'capture.json', out / f'validation/runtime/v{variant}-original-capture.json')
    browse(destination, variant, result)
    natural = sum(r['group'] != 'diagnostic' for r in result['captures'])
    diagnostic = len(result['captures']) - natural
    return {'forest_variant': variant, 'display_variant': local(variant) if variant else 0,
            'path': folder(variant), 'captures': len(result['captures']), 'natural_contexts': natural,
            'diagnostic_contexts': diagnostic, 'passed': report['passed'], 'total': report['total'],
            'movies': sum(bool(r.get('video')) for r in result['captures']), 'files_copied': len(copied),
            'additional_earned_progression_images': route_images,
            'rom_sha256': report['rom_sha256'], 'omitted_gifs': omitted}


def browse(destination, variant, report):
    title = f'{local(variant)}. {RECIPES[variant]}' if variant else 'Unchanged production control'
    diagnostic = [r for r in report['captures'] if r['group'] == 'diagnostic']
    natural = [r for r in report['captures'] if r['group'] != 'diagnostic']
    lines = [f'# {title}: actual mGBA', '', '[Back to the complete review](../../README.md)', '',
             f"{len(natural)} non-diagnostic recorded contexts; {len(diagnostic)} explicit diagnostic-room contexts. "
             f"{report['passed']}/{report['total']} capture checks. [Complete report and fixtures](capture.json).", '',
             'Natural cases use generated terrain with disclosed navigation, player, health/inventory and unrelated-enemy-clearing fixtures. '
             'New profiles share their own generated geometry; production control0 is separate. '
             'Diagnostic cases deliberately replace logical terrain and call the real ROM renderer/collision builder. '
             'They are actual mGBA output, and are not naturally generated rooms.', '',
             'Native PNGs and filmstrips are exact. MP4s are full-rate lossy 2× viewing copies. '
             'Only exact-palette GIFs are linked; raw all-frame archives remain local.', '']
    if diagnostic: lines += ['[Six disclosed diagnostic-room fixtures](diagnostic/README.md)', '']
    if variant: lines += ['[All 25 generated room viewports on one native board](all-25-room-views-actual.png)', '']
    for group in GROUPS:
        rows = [r for r in natural if r['group'] == group]
        if rows: lines += ['## ' + GROUP_LABELS[group], '']
        for row in rows: lines += case_markdown(row)
    for route in report.get('routes', []):
        if 'critical_path' not in route: continue
        trial = route['critical_path']
        lines += ['## Additional earned progression proof', '',
                  'These five actual snapshots and the run log record the three earned trials, genuine item-gate actions and Heart entry. '
                  'They are additional validation images outside the art-context count. Navigation, health and attack-position fixtures are disclosed; '
                  'rewards, event flags and enemy HP are not assigned.', '', f'[Complete progression log]({trial["log"]})', '']
        for image in trial['images']: lines += [f'![Actual earned progression snapshot]({image})', '']
    markdown(destination / 'README.md', lines)
    if diagnostic:
        lines = [f'# {title}: explicit diagnostic rooms', '', '[Back to natural contexts](../README.md)', '',
                 'Every scene below deliberately injects a small semantic terrain fixture. The frozen game then builds '
                 'actual adjacency pictures and collision in mGBA. These six contexts are counted separately from generated rooms.', '']
        for row in diagnostic: lines += case_markdown(row, '../')
        markdown(destination / 'diagnostic/README.md', lines)


def case_markdown(row, prefix=''):
    subtitle = f"Seed {row['seed']} · room {row.get('cell')}"
    if row.get('stage') is not None: subtitle += f" · stage {row['stage']}"
    lines = ['### ' + P.human(row['name']), '', subtitle, '', row.get('note', ''), '',
             f'![Actual native framebuffer]({prefix}{row["image"]})', '']
    links = []
    for key, label in (('after_image', 'After action'), ('filmstrip', 'Native chronological filmstrip'),
                       ('video', 'Full-rate MP4'), ('gif', 'Exact-palette GIF')):
        if row.get(key): links.append(f'[{label}]({prefix}{row[key]})')
    for entry in extra_frames(row): links.append(f'[{entry.get("label", entry.get("phase", "Measured keyframe"))}]({prefix}{entry["path"]})')
    if links: lines += [' · '.join(links), '']
    return lines


def scene(out, variant, row, image=None, tick=0, caption=None, kind=None):
    relative = image or row['image']
    state = next((t for t in row['trace'] if t['tick'] == tick), None)
    reference = next((entry for entry in extra_frames(row) if entry['path'] == relative), None)
    return {'image': folder(variant) + '/' + relative, 'caption': caption or P.human(row['name']),
            'forest_variant': variant, 'display_variant': local(variant) if variant else 0,
            'case': row['name'], 'tick': tick, 'evidence_kind': kind or row.get('fixture_kind', 'production control generated context'),
            'fixture': {k: row.get(k) for k in ('seed', 'cell', 'position', 'target', 'facing', 'diagnostic_room')},
            'measured_keyframe': reference,
            'snapshot': {k: state.get(k) for k in ('area', 'cell', 'position', 'camera', 'depth_visibility',
                                                 'motion_phase', 'z_q16', 'player_priority',
                                                 'authored_BG_palette_phase', 'displayed_BG_palette_phase')} if state else None}


def sheet(out, relative, title, entries, columns):
    rows = math.ceil(len(entries) / columns)
    title_lines = ['']
    for word in (title + ' / ACTUAL mGBA / literal 240x160 panels').split():
        candidate = (title_lines[-1] + ' ' + word).strip()
        if P.FONT.getlength(candidate) > columns * 240 - 10: title_lines.append(word)
        else: title_lines[-1] = candidate
    header = max(32, 8 + len(title_lines) * 16)
    board = Image.new('RGB', (columns * 240, header + rows * 188), P.BG); draw = ImageDraw.Draw(board)
    for index, text in enumerate(title_lines): P.label(draw, (5, 4 + index * 16), text)
    panels = []
    for index, item in enumerate(entries):
        x, y = index % columns * 240, header + index // columns * 188
        caption = item['caption']
        while P.FONT.getlength(caption) > 232: caption = caption[:-1]
        P.label(draw, (x + 4, y + 3), caption)
        path = out / item['image']
        with Image.open(path) as image:
            assert image.size == P.NATIVE; image = image.convert('RGB')
        board.paste(image, (x, y + 24))
        panels.append({**item, 'source_png_sha256': sha(path), 'source_rgb_sha256': hashlib.sha256(image.tobytes()).hexdigest(),
                       'source_rectangle': [0, 0, 240, 160], 'destination_rectangle': [x, y + 24, x + 240, y + 184]})
    path = out / relative; path.parent.mkdir(parents=True, exist_ok=True); board.save(path)
    with Image.open(path) as saved:
        saved = saved.convert('RGB')
        for panel in panels:
            with Image.open(out / panel['image']) as original:
                assert saved.crop(panel['destination_rectangle']).tobytes() == original.convert('RGB').tobytes(), ('changed panel', relative, panel)
    return {'path': relative, 'title': title, 'sha256': sha(path), 'size': list(board.size),
            'decoded_panels_verified': True, 'panels': panels}


def keyframe(row, key, label=None):
    value = row.get(key)
    entries = [value] if isinstance(value, dict) else value or []
    if label:
        normalize = lambda text: str(text).lower().strip().replace('emerged', 'emerge')
        entries = [r for r in entries if normalize(r.get('label', r.get('phase', ''))) == normalize(label)]
    if not entries: return None
    entry = entries[0]
    return {**entry, 'path': entry.get('path', entry.get('image')), 'tick': entry['tick'],
            'label': entry.get('label', entry.get('phase', 'measured keyframe'))}


def actual_boards(out, reports):
    by = {v: {r['name']: r for r in reports[v]['captures']} for v in PROFILES}
    boards = []
    groups = [
        ('healthy-mixed-deep-actual.png', 'New forest studies: generated healthy / mixed / deep', ['healthy-canopy', 'mixed-forest', 'deep-blight']),
        ('water-and-ledges-actual.png', 'Generated water, bridges and ledges', ['water-bridge', 'pit-bank', 'ledge-path']),
        ('mystery-interiors-actual.png', 'Natural generated mystery interiors', ['interior-cave', 'interior-hollow', 'interior-thicket']),
        ('wooden-chests-before-actual.png', 'Ten real wooden chest forms / A and B closed', ['blight-wood-chest', 'forest-wood-B-chest']),
        ('landmarks-and-logs-actual.png', 'Actual large logs, vertical shrine and relic', ['large-log-collision', 'shrine-plinth-depth', 'relic-plinth-depth']),
        ('forest-folk-before-actual.png', 'Fifteen new forest folk / actual world bodies', ['forest-npc-hermit', 'forest-npc-nun', 'forest-npc-gardener']),
    ]
    for name, title, cases in groups:
        names = {'blight-wood-chest': 'Wood A / closed', 'forest-wood-B-chest': 'Wood B / closed'}
        entries = [scene(out, v, by[v][case], caption=f'{local(v)} {RECIPES[v]} / {names.get(case, P.human(case))}') for v in PROFILES for case in cases]
        boards.append(sheet(out, name, title, entries, len(cases)))
    for variant in PROFILES:
        rooms = sorted((r for r in reports[variant]['captures'] if r['group'] == 'rooms'), key=lambda r: r['cell'])
        entries = [scene(out, variant, r, caption=f"Room {r['cell']:02d} / stage {r.get('stage')} / {r.get('archetype')}") for r in rooms]
        boards.append(sheet(out, folder(variant) + '/all-25-room-views-actual.png', RECIPES[variant] + ' / 25 generated viewports', entries, 5))
    for kind in ('water', 'living-canopy', 'sick-canopy'):
        entries = []
        for variant in PROFILES:
            cases = [r for r in reports[variant]['captures'] if r['group'] == 'diagnostic' and r.get('diagnostic_room', {}).get('kind') == kind]
            for row in cases:
                entries.append(scene(out, variant, row, caption=f'{local(variant)} {RECIPES[variant]} / '+row['diagnostic_room']['shape']))
        if entries:
            boards.append(sheet(out, f'diagnostic-{kind}-actual.png', 'DISCLOSED DIAGNOSTIC ROOM FIXTURES / ' + kind, entries, len(entries) // 5))
    for name in ('living-canopy-walkunder', 'sick-canopy-walkunder', 'root-arch-underpass'):
        entries = []
        for variant in PROFILES:
            row = by[variant][name]
            for phase in ('before', 'under', 'emerge'):
                frame = keyframe(row, 'depth_keyframes', phase) or keyframe(row, 'phase_keyframes', phase)
                assert frame is not None, ('missing measured depth phase keyframe', variant, name, phase)
                visibility = frame['visibility']
                assert visibility.get('feet_covered', 0) == 0
                if phase == 'under':
                    assert 0 < visibility['upper_body_covered'] < visibility['upper_body_opaque']
                else: assert visibility['upper_body_covered'] == 0
                entries.append(scene(out, variant, row, frame['path'], frame['tick'], f'{local(variant)} {RECIPES[variant]} / {phase}'))
        boards.append(sheet(out, name + '-actual.png', 'Generated depth: ' + P.human(name) + ' / measured phases', entries, 3))
    barrier_cases = ['outer-gate-thorns', 'outer-gate-cracked-wall', 'outer-gate-cobweb', 'outer-gate-locked-door']
    for phase in ('before', 'cleared'):
        entries = []
        for variant in PROFILES:
            for name in barrier_cases:
                row = by[variant][name]
                frame = keyframe(row, 'cleared_barrier_keyframe') if phase == 'cleared' else None
                if phase == 'cleared': assert frame is not None, ('missing same-room cleared barrier view', variant, name)
                if frame:
                    assert frame['cell'] == row['initial']['cell']
                    assert frame['target_ground'] != row['initial']['target_ground']
                    assert frame['target_BG_ground_quarters'] == row['initial']['target_BG_ground_quarters']
                entries.append(scene(out, variant, row, frame['path'] if frame else None, frame['tick'] if frame else 0,
                                     f'{local(variant)} {RECIPES[variant]} / {P.human(name)} {phase}'))
        boards.append(sheet(out, 'gates-' + phase + '-actual.png', 'Actual barrier states / ' + phase + ' / original local substrate', entries, 4))
    for name, cases, title in (
        ('wooden-chests-open-actual.png', ['blight-wood-chest', 'forest-wood-B-chest'], 'Ten wooden forms after real opening'),
        ('forest-folk-dialogue-actual.png', ['forest-npc-hermit', 'forest-npc-nun', 'forest-npc-gardener'], 'Fifteen actual matching forest portraits/dialogues')):
        entries = []
        for variant in PROFILES:
            for case in cases:
                row = by[variant][case]
                entries.append(scene(out, variant, row, row['after_image'], row['video_frames'] - 1,
                                     f'{local(variant)} {RECIPES[variant]} / {P.human(case)}'))
        boards.append(sheet(out, name, title, entries, len(cases)))
    entries = []
    for variant in PROFILES:
        row = by[variant]['deep-blight']
        frames = row.get('pulse_phase_keyframes', row.get('pulse_keyframes', []))
        assert len(frames) == 4 and {r['phase'] for r in frames} == {0, 1, 2, 3}, ('missing four actual glow-phase frames', variant)
        for frame in frames:
            entries.append(scene(out, variant, row, frame['path'], frame['tick'],
                                 f'{local(variant)} {RECIPES[variant]} / phase {frame.get("phase")}'))
    boards.append(sheet(out, 'four-glow-phases-actual.png', 'Actual authored BG palette pulse / four real engine phases', entries, 4))
    return boards


def historical_deep(out, reports, new_commit):
    """Historical context, deliberately not a matched-layout comparison."""
    entries = []; records = []
    old_root = REPO / 'art-review/forest-concepts/actual'
    for old in range(1, 6):
        report_path = old_root / f'variant-{old:02d}/capture.json'; report = read(report_path)
        row = next(r for r in report['captures'] if r['name'] == 'deep-blight')
        relative = f'actual/historical-v1/variant-{old:02d}-deep.png'
        exact_copy(report_path.parent / row['image'], out / relative)
        record = {'image': relative, 'caption': f'V1 #{old} / {report.get("recipe", "historical option")}',
                  'evidence_kind': 'Historical V1 generated context, not a matching new room', 'case': row['name'],
                  'source_commit': report['source_commit'], 'rom_sha256': report['rom_sha256'],
                  'source_report_sha256': sha(report_path), 'fixture': {k: row.get(k) for k in ('seed', 'cell', 'position')},
                  'snapshot': row['trace'][0], 'tick': 0}
        old_freeze = read(REPO / 'art-review/forest-concepts/validation/frozen' / f'v{old}/freeze.json')
        record['caption'] = f"V1 {old_freeze['label']} / {report['source_commit'][:7]}"
        records.append(record)
    # Put old options and new options in their own blocks. Row alignment is
    # an index convenience, not a family mapping or a geometric claim.
    entries.extend(records)
    for variant in PROFILES:
        row = next(r for r in reports[variant]['captures'] if r['name'] == 'deep-blight')
        entries.append(scene(out, variant, row, caption=f'V2 {RECIPES[variant]} / {new_commit[:7]}',
                             kind='New generated context; historical illustration, different generation/seed/camera'))
    board = sheet(out, 'v1-v2-deep-historical-actual.png', 'V1 and V2 deep forests / HISTORICAL ILLUSTRATION / different generation, seeds and cameras', entries, 5)
    write(out / 'actual/historical-v1/provenance.json', {'method': 'Only selected old native stills copied unchanged. No 1:1 family, room geometry or camera match is claimed.',
          'historical_source': '73df5c1296f84ac469102c92f106dc9ad17b9a27', 'new_source': new_commit, 'frames': records})
    markdown(out / 'actual/historical-v1/README.md', ['# Historical first-pass deep forest', '', '[Back to the second pass](../../README.md)', '',
             'These unchanged first-pass captures retain their original names and source73df5c1. The new studies change generation and choose '
             'different deep views. The comparison is illustrative; aligned option numbers do not establish family identity or pixel correspondence.', '',
             *[f'![{r["caption"]}]({Path(r["image"]).name})' for r in records], '', '[Original snapshot provenance](provenance.json)'])
    return board


def validation(work, out, freezes, branch):
    base = out / 'validation'
    names = ('inventory.json', 'builds.json', 'runtime-summary.json', 'source-gallery-verification.json',
             'source-gallery-review.md', 'source-authoring-api.json', 'source-api.json', 'glow-table-guards.json',
             'build-default-restored.log', 'build-final-summary.log', 'code-review.md')
    for name in names:
        if (work / name).is_file(): exact_copy(work / name, base / name)
    if (work / 'runtime/final-summary.json').is_file():
        exact_copy(work / 'runtime/final-summary.json', base / 'runtime/final-summary.json')
    for variant in FROZEN_PROFILES:
        for name in ('freeze.json', 'coverage.json', 'assets.h', 'bartgame.map'):
            exact_copy(work / f'frozen/v{variant}' / name, base / f'frozen/v{variant}' / name)
        for filename in (f'build-v{variant}.log', f'runtime-v{variant}.log'):
            if (work / filename).is_file(): exact_copy(work / filename, base / 'logs' / filename)
        path = work / 'runtime' / (f'v{variant}.log' if variant else 'control-v0.log')
        if path.is_file(): exact_copy(path, base / 'logs' / path.name)
    allowed_audit = {'native.json', 'native-summary.json', 'static.json', 'static-summary.json', 'finalaudit.json', 'finalaudit-summary.json',
                     'visual-review-source.md', 'visual-review-actual.md', 'secondary-visual-critique.md',
                     'secondary-source-critique.md',
                     'transition-timing-observations.json', 'source-guard-proof.json', 'palette-pulse-proof.json',
                     'timing-observations.json',
                     'runtime-contracts.json'}
    for path in sorted((work / 'audit').rglob('*')):
        if not path.is_file(): continue
        relative = path.relative_to(work / 'audit')
        if len(relative.parts) == 1 and path.name not in allowed_audit: continue
        if len(relative.parts) > 1 and relative.parts[:2] != ('host', 'v6'): continue
        if any(part in ('draft', 'old', 'superseded') for part in relative.parts): continue
        if path.suffix not in ('.json', '.md', '.log', '.c', '.h', '.txt'): continue
        if 'draft' in path.name or 'pending' in path.name: continue
        # Failed interim JSON and logs never become final proof by copying.
        if path.suffix == '.json':
            value = read(path)
            if isinstance(value, dict) and (value.get('failures') or value.get('passed') is False): continue
        exact_copy(path, base / 'audit' / path.relative_to(work / 'audit'))
    tools = {}
    for name in ('forest_v2_publish.py', 'forest_v2_gallery.py', 'forest_v2_audit.py', 'forest_v2_review.py',
                 'forest_concept_publish.py', 'forest_concept_review.py'):
        relative = 'bartgame/tools/' + name
        tools[relative] = {'sha256': sha(ROOT / 'tools' / name),
                           'repository_url': f'https://github.com/natertott/bartgame/blob/{branch}/{relative}'}
    if (work / 'verify_source_gallery.py').is_file():
        exact_copy(work / 'verify_source_gallery.py', base / 'tool-sources/verify_source_gallery.py')
        tools['local-source-gallery-verifier'] = {'sha256': sha(work / 'verify_source_gallery.py'),
                    'published_source': 'validation/tool-sources/verify_source_gallery.py',
                    'note': 'Separately hashed local verification script, not claimed as part of the game/art freeze.'}
    write(base / 'tool-provenance.json', {'game_art_source_commit': freezes[6]['source_commit'], 'tools': tools,
          'note': 'Publication/review tools are separately hashed and linked. Game/art freeze and review-tool revision are different provenance records.'})


def releases(work, destination, freezes, branch, gallery):
    destination.mkdir(parents=True, exist_ok=True); short = freezes[6]['source_commit'][:7]
    records = []
    for variant in PROFILES:
        name = f'forest-v2-{local(variant):02d}-{P.slug(RECIPES[variant])}-{short}.gba'
        exact_copy(work / f'frozen/v{variant}/bartgame.gba', destination / name)
        freeze_name = f'freezes/forest-profile-{variant:02d}.json'
        exact_copy(work / f'frozen/v{variant}/freeze.json', destination / freeze_name)
        records.append({'display_variant': local(variant), 'forest_variant': variant, 'label': RECIPES[variant],
                        'rom': name, 'rom_sha256': sha(destination / name), 'freeze': freeze_name})
    text = [f'BARTGAME - forest concepts round2 ({short})', '',
            'Five unselected forest directions. Local options1..5 use game profiles6..10.',
            'Production profile0 and historical1..5 remain separate unchanged builds.',
            'These ROMs add blackened infected forest, actual palette glow, resolved',
            'terrain adjacency, foreground fringes, a true lower root-arch passage,',
            'two-cell solid logs, tall landmarks, two wooden chest forms and new folk.',
            'A 32px root span has at least one true 16px lower lane; its upper wood is',
            'scenery, not a second walkable deck. Grounded feet stay clear. Brief',
            'airborne wall recoil has an explicit coarse foreground-sorting exception',
            'at low foliage; normal walking/rolling/crowns retain real occlusion.', '',
            *[f"{r['display_variant']}. {r['label']}: {r['rom']}" for r in records], '',
            'Open one .gba in mGBA. No commercial game ROM is required.',
            'Start opens/closes inventory; R cycles pages; D-pad selects; A/B/L assign.',
            'Map: A zooms, B returns, D-pad browses rooms.', '',
            f'https://github.com/natertott/bartgame/blob/{branch}/{gallery}/README.md', '',
            'The gallery separates natural generated captures, disclosed diagnostic',
            'room fixtures, native source assemblies and historical illustrations.',
            'ROM-SHA256SUMS.txt checks all five ROMs; freezes/ records their sources.']
    markdown(destination / 'README.txt', text)
    (destination / 'ROM-SHA256SUMS.txt').write_text(''.join(f"{r['rom_sha256']}  {r['rom']}\n" for r in records))
    archive = f'forest-concepts-v2-{short}.zip'
    members = [r['rom'] for r in records] + [r['freeze'] for r in records] + ['README.txt', 'ROM-SHA256SUMS.txt']
    with zipfile.ZipFile(destination / archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name in members: bundle.write(destination / name, name)
    with zipfile.ZipFile(destination / archive) as bundle:
        assert bundle.testzip() is None and set(bundle.namelist()) == set(members) and len(bundle.namelist()) == len(members)
        assert len([name for name in bundle.namelist() if name.endswith('.gba')]) == 5
        for name in members: assert hashlib.sha256(bundle.read(name)).hexdigest() == sha(destination / name)
    (destination / 'SHA256SUMS.txt').write_text(''.join(f'{sha(destination / name)}  {name}\n' for name in [*[r['rom'] for r in records], archive]))
    return {'roms': records, 'zip': archive, 'zip_sha256': sha(destination / archive), 'zip_crc_and_member_hashes_verified': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('work', 'out', 'release'): parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--branch', required=True)
    args = parser.parse_args(); work, out, release = args.work.resolve(), args.out.resolve(), args.release.resolve()
    source, freezes, reports, audit = validate(work)
    out.mkdir(parents=True, exist_ok=True)
    catalog = copy_source(work, out, source)
    reviews = [copy_capture(work, out, variant, reports[variant]) for variant in (*PROFILES, 0)]
    boards = actual_boards(out, reports)
    boards.append(historical_deep(out, reports, freezes[6]['source_commit']))
    write(out / 'actual-panel-manifest.json', {'source_commit': freezes[6]['source_commit'], 'boards': boards,
          'method': 'Every saved panel independently decoded and compared byte-for-byte with its linked native framebuffer. Diagnostic and historical evidence types are explicit.'})
    validation(work, out, freezes, args.branch)
    bundle = releases(work, release, freezes, args.branch, str(out.relative_to(REPO)))
    new = [r for r in reviews if r['forest_variant'] in PROFILES]
    control = next(r for r in reviews if not r['forest_variant'])
    summary = {'source_commit': freezes[6]['source_commit'], 'source_art': catalog, 'actual': reviews,
               'new_style_contexts': sum(r['captures'] for r in new), 'natural_contexts': sum(r['natural_contexts'] for r in new),
               'diagnostic_contexts': sum(r['diagnostic_contexts'] for r in new),
               'new_capture_checks': {'passed': sum(r['passed'] for r in new), 'total': sum(r['total'] for r in new)},
               'all_recorded_art_contexts': sum(r['captures'] for r in reviews),
               'all_capture_checks': {'passed': sum(r['passed'] for r in reviews), 'total': sum(r['total'] for r in reviews)},
               'all_movies': sum(r['movies'] for r in reviews),
               'separate_production_control': control, 'independent_audit': {'passed': audit['passed'], 'total': audit['total']},
               'actual_panel_manifest': 'actual-panel-manifest.json', 'actual_boards': len(boards),
               'release': bundle, 'format_policy': __doc__.strip()}
    write(out / 'validation/publication-summary.json', summary)
    lines = ['# Forest second pass: actual mGBA', '', '[Back to the full review](../README.md)', '',
             'Five new styles share matched new generated geometry. Production0 is a separate historical control. '
             'Explicit diagnostic-room fixtures have their own indexes and counts; they are not natural generated landscapes.', '']
    for row in reviews:
        name = RECIPES[row['forest_variant']] if row['forest_variant'] else 'Production control0'
        room_link = f" [All 25 room viewports]({Path(row['path']).name}/all-25-room-views-actual.png)." if row['forest_variant'] else ''
        lines += [f"- [{row['display_variant']}. {name}]({Path(row['path']).name}/README.md): "
                  f"{row['natural_contexts']} non-diagnostic contexts +{row['diagnostic_contexts']} diagnostic fixtures.{room_link}"]
    lines += ['', '[Historical first-pass deep views](historical-v1/README.md)']
    markdown(out / 'actual/README.md', lines)
    manifest = {'source_commit': freezes[6]['source_commit'], 'files': {},
                'note': 'Excludes itself. Parent refreshes after final editorial additions.'}
    for base in (out, release):
        for path in sorted(base.rglob('*')):
            if path.is_file() and path != out / 'validation/publication-manifest.json':
                assert path.stat().st_size < 100_000_000, ('oversized publication file', path)
                manifest['files'][str(path.relative_to(REPO))] = {'sha256': sha(path), 'bytes': path.stat().st_size}
    write(out / 'validation/publication-manifest.json', manifest)
    print(json.dumps({'source': summary['source_commit'], 'new_contexts': summary['new_style_contexts'],
                      'natural': summary['natural_contexts'], 'diagnostic': summary['diagnostic_contexts'],
                      'control': control['captures'], 'boards': len(boards), 'files': len(manifest['files']),
                      'roms': [r['rom'] for r in bundle['roms']], 'zip': bundle['zip']}))


if __name__ == '__main__':
    main()
