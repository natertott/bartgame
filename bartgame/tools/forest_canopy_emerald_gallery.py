#!/usr/bin/env python3
"""Focused native-source and literal mGBA review for the leaf-crown canopy.

Profile 29 is explicit. Source pictures and palette inspection are separate
from unchanged emulator framebuffers; no source-rendered room is presented.
"""
import argparse
import hashlib
import importlib
import json
import math
from pathlib import Path
import sys

from PIL import Image, ImageDraw
import forest_canopy_adaptive_gallery as G

ROOT = Path(__file__).resolve().parents[1]
LOADED_SHA = G.sha(__file__)
GEOMETRY = ('broad-healthy', 'broad-deep', 'isolated-small', 'narrow-arm', 'separated-corner')


def snapshot():
    sys.path.insert(0, str(ROOT / 'art'))
    art = importlib.import_module('forest_canopy_emerald')
    paths = sorted((ROOT / 'art').glob('*.py')) + [ROOT / 'Makefile', ROOT / 'tools/build_assets.py']
    inputs = {str(p.relative_to(ROOT)): G.sha(p) for p in paths}
    palettes = [art.pulse_palettes(1, stage)[art.PALETTE_NAME] for stage in range(4)]
    for stage in palettes:
        assert len(stage) == 4
        for colors in stage:
            G.legal_palette(colors)
    entries = []
    def add(role, image, category, **metadata):
        assert image.mode == 'P' and set(image.tobytes()) <= set(range(16)) and image.getbbox()
        indices = list(image.tobytes())
        entries.append({'role': role, 'name': role, 'variation': 0,
                        'category': category, 'size': list(image.size), 'indices': indices,
                        'index_sha256': hashlib.sha256(bytes(indices)).hexdigest(),
                        'painted_bounds': image.getbbox(),
                        'painted_pixels': sum(i != 0 for i in indices),
                        'palette': art.PALETTE_NAME, 'owner': 'forest_canopy_emerald', **metadata})
    for spec in art.prefab_specs(1):
        add(spec['role'], art.prefab(1, spec['role']), 'resident_prefab',
            layer=spec['layer'], footprint=spec['footprint'])
    add('branch-solid', art.blocked_branch(1), 'resident_special_map',
        layer='solid narrow forest; separate from transparent projected branch',
        planner_role='branch', placement_flags=0)
    for large in (False, True):
        for second in (False, True):
            role = 'authored-' + ('large' if large else 'small') + ('-b' if second else '-a')
            add(role, art.authored_tree(1, large=large, second=second), 'authored_tree_group',
                layer='existing grouped-tree canvas; physical footprint retained')
    assert len(entries) == 14
    assert all(G.sha(ROOT / name) == digest for name, digest in inputs.items())
    return {'profile': 29, 'style': 1, 'name': art.NAMES[1], 'palette_bank': art.PALETTE_NAME,
            'stage_pulse_palettes': palettes, 'entries': entries,
            'retained_green_indices': list(art.GREEN_INDICES),
            'pulse_indices': list(art.PULSE_INDICES), 'source_input_sha256': inputs,
            'color_note': 'Authored RGB555 colors are stored as 8-bit channels divisible by8; mGBA framebuffer expansion is separate.'}


def source_main(args):
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    freeze = G.frozen(args.work.resolve(), 29, args.final)
    value = snapshot()
    value.update(source_commit=freeze['source_commit'], rom_sha256=freeze.get('rom_sha256'),
                 gallery_tool_sha256=LOADED_SHA)
    G.write(out / 'source-art.json', value, compact=True)
    native = []
    cw, ch, cols = 240, 112, 3
    board = Image.new('RGB', (cw * cols, 54 + ch * math.ceil(len(value['entries']) / cols)), G.BG)
    d = ImageDraw.Draw(board)
    status = 'FROZEN' if args.final else 'DRAFT'
    G.label(d, (5, 3), f'{status} SOURCE / Leafwoven Canopy / original native GBA drawings')
    G.label(d, (5, 22), 'Healthy + deep at1x. Transparent pixels use a neutral inspection background, not a game substrate.', G.DIM)
    for n, entry in enumerate(value['entries']):
        role = entry['role']; size = entry['size']; folder = out / 'native'; folder.mkdir(exist_ok=True)
        index = folder / (role + '-indexed.png')
        G.indexed(entry['indices'], size, value['stage_pulse_palettes'][3][0]).save(index, bits=4)
        healthy = G.rgba(entry['indices'], size, value['stage_pulse_palettes'][0][0])
        deep = G.rgba(entry['indices'], size, value['stage_pulse_palettes'][3][0])
        hp, dp = folder / (role + '-healthy.png'), folder / (role + '-deep.png')
        healthy.save(hp); deep.save(dp)
        assert Image.open(index).convert('RGBA').tobytes() == deep.tobytes()
        x, y = n % cols * cw, 54 + n // cols * ch
        G.label(d, (x + 5, y), f'{role} / {size[0]}x{size[1]}')
        G.label(d, (x + 5, y + 16), 'healthy', G.DIM); G.label(d, (x + 125, y + 16), 'deep', G.DIM)
        G.paste(board, healthy, (x + 5, y + 34)); G.paste(board, deep, (x + 125, y + 34))
        native.append({k: v for k, v in entry.items() if k != 'indices'} | {
            'native_indexed': str(index.relative_to(out)), 'native_healthy': str(hp.relative_to(out)),
            'native_deep': str(dp.relative_to(out)),
            'catalog_healthy_rect': [x + 5, y + 34, *size],
            'catalog_native_rect': [x + 125, y + 34, *size]})
    board.save(out / 'native-healthy-deep-source.png')
    G.write(out / 'native-manifest.json', {'profile': 29, 'style': 1, 'entries': native,
            'catalog_background': G.BG,
            'footprint_note': 'Native art/alpha bounds, planner placement rectangles and physical collision are different contracts.'})
    hero = next(e for e in value['entries'] if e['role'] == 'hero'); frames = []
    for phase in range(4):
        image = Image.new('RGB', (432, 116), G.BG); draw = ImageDraw.Draw(image)
        G.label(draw, (5, 3), f'SOURCE palette inspection / phase{phase} / fixed180ms hold')
        for stage in range(4):
            G.label(draw, (stage * 108 + 5, 24), f'Depth stage{stage}', G.DIM)
            G.paste(image, G.rgba(hero['indices'], hero['size'], value['stage_pulse_palettes'][stage][phase]),
                    (stage * 108 + 5, 45))
        image.save(out / f'palette-phase-{phase}-source.png'); frames.append(image)
    gif = G.exact_gif(frames, out / 'palette-inspection-source.gif')
    G.write(out / 'source-gif.json', gif)
    G.markdown(out / 'README.md', ['# Leafwoven Canopy: native source', '',
        '**SOURCE drawings and palette inspection. Actual mGBA frames are separate.**', '',
        '![Fourteen native pieces](native-healthy-deep-source.png)', '',
        '[Native files and physical-role metadata](native-manifest.json) · [Four-stage palette inspection](palette-inspection-source.gif) · [Source/index/palette data](source-art.json)', '',
        'The fourteen pieces are nine resident roles, one solid branch map and four authored-tree groups. '
        'Healthy/deep images share original native geometry with dedicated RGB555 material tables. '
        'Transparent pixels in this source sheet use a neutral inspection background; the actual renderer reveals local grass/soil.', '',
        'The reference-informed leaf crowns are drawn at their final native sizes. '
        'The source GIF uses fixed inspection holds and makes no engine-timing claim. '
        'The source catalog does not simulate a room or establish in-game contact/visibility by itself.'])
    files = {str(p.relative_to(out)): {'sha256': G.sha(p), 'bytes': p.stat().st_size}
             for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'source-manifest.json'}
    manifest = {'source_commit': freeze['source_commit'], 'profile': 29, 'style': 1,
                'rom_sha256': freeze.get('rom_sha256'), 'gallery_tool_sha256': LOADED_SHA,
                'gallery_dependency_sha256': {Path(G.__file__).name: G.sha(G.__file__)},
                'source_input_sha256': value['source_input_sha256'], 'native_images': len(native),
                'resident_prefabs': 9, 'special_native_maps': 1, 'authored_tree_groups': 4,
                'exact_source_palette_GIFs': 1, 'files': files,
                'kind': 'frozen source inspection' if args.final else 'unfrozen source inspection'}
    assert G.sha(__file__) == LOADED_SHA
    G.write(out / 'source-manifest.json', manifest)
    print(json.dumps({k: manifest[k] for k in ('source_commit', 'native_images', 'resident_prefabs', 'special_native_maps', 'authored_tree_groups')}))


def report_files(row):
    paths = set(row.get('native_frames', []))
    paths.update(row[k] for k in ('image', 'after_image', 'filmstrip', 'video', 'gif') if row.get(k))
    paths.update(f['path'] for f in G.keyframes(row) if f.get('path'))
    paths.update(v['path'] for k, v in row.items() if k.startswith('resident_BG') and isinstance(v, dict) and v.get('path'))
    return paths


def actual_main(args):
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    reports = {}
    for profile in (19, 29):
        base = (args.work.resolve() / f'runtime/v{profile}').resolve()
        report = json.loads((base / 'capture.json').read_text()); freeze = G.frozen(args.work.resolve(), profile, args.final)
        assert report['forest_variant'] == profile
        if args.final:
            assert report['complete'] and not report.get('unfrozen_pilot') and not report['failures']
            assert report['passed'] == report['total'] and report['source_commit'] == freeze['source_commit']
            assert report['rom_sha256'] == freeze['rom_sha256']
            assert report['capture_tool_sha256'] == G.sha(ROOT / 'tools/forest_canopy_adaptive_review.py')
        destination = out / 'actual' / f'profile-{profile}'; destination.mkdir(parents=True, exist_ok=True)
        G.exact_copy(base / 'capture.json', destination / 'capture.json')
        for relative in sorted({p for row in report['captures'] for p in report_files(row)}):
            path = (base / relative).resolve()
            assert path.is_relative_to(base) and 'all-frames' not in path.parts
            G.exact_copy(path, destination / relative)
        lines = [f'# Profile{profile}: actual mGBA', '',
                 ('Previous exposed-tree control.' if profile == 19 else 'New leaf-crown canopy.'), '',
                 'Untouched native framebuffers and ordinary-input recordings from the frozen ROM. '
                 'Player/camera/inventory/standing and controlled post-generation action-RNG fixtures are disclosed in the report. '
                 'Resident BG1/BG2 exports are read-only layer reconstructions, not game screenshots.', '',
                 '[Exact capture report](capture.json)', '']
        for row in report['captures']:
            lines += [f'## {row["name"]}', '', f'Seed {row.get("seed")} · room {row.get("cell")}', '',
                      f'![Actual native framebuffer]({row["image"]})', '']
            links = [f'[{title}]({row[field]})' for field, title in [('after_image','After'),('filmstrip','Native filmstrip'),('video','Full-rate MP4'),('gif','Exact-palette GIF')] if row.get(field)]
            links += [f'[{f["label"]}]({f["path"]})' for f in G.keyframes(row)]
            links += [f'[{key[9:]} layer reconstruction]({value["path"]})' for key, value in row.items()
                      if key.startswith('resident_BG') and isinstance(value, dict) and value.get('path')]
            lines += [' · '.join(links), '']
        lines += ['MP4s are lossy full-rate viewing copies. Native PNGs and exact-palette GIFs preserve their stated fidelity. '
                  'Raw all-frame archives remain local. Menu/loading timelines remain explicit observations, separate from ordinary playing cadence.']
        G.markdown(destination / 'README.md', lines)
        reports[profile] = report
    assert len({r['source_commit'] for r in reports.values()}) == 1
    boards = []
    def board(name, cases):
        image = Image.new('RGB', (480, 48 + len(cases) * 184), G.BG); d = ImageDraw.Draw(image)
        status = 'ACTUAL mGBA / frozen source' if args.final else 'PILOT actual mGBA'
        G.label(d, (4, 3), status + ' / native240x160 panels')
        G.label(d, (4, 23), 'Previous exposed-tree control', G.DIM); G.label(d, (244, 23), 'New leaf-crown canopy', G.DIM)
        panels = []
        for n, case in enumerate(cases):
            for col, profile in enumerate((19, 29)):
                row = next(r for r in reports[profile]['captures'] if r['name'] == case)
                path = out / 'actual' / f'profile-{profile}' / row['image']; native = Image.open(path).convert('RGB')
                assert native.size == (240, 160)
                x, y = col * 240, 48 + n * 184
                G.label(d, (x + 4, y), case, G.DIM); image.paste(native, (x, y + 22))
                panels.append({'profile': profile, 'case': case, 'source': str(path.relative_to(out)),
                               'source_sha256': G.sha(path), 'rect': [x, y + 22, 240, 160],
                               'rgb_sha256': hashlib.sha256(native.tobytes()).hexdigest()})
        target = out / name; image.save(target); check = Image.open(target).convert('RGB')
        for p in panels:
            x, y, w, h = p['rect']
            assert check.crop((x, y, x+w, y+h)).tobytes() == Image.open(out / p['source']).convert('RGB').tobytes()
        return {'path': name, 'sha256': G.sha(target), 'panels': panels}
    boards.append(board('healthy-deep-before-after-actual.png', ('broad-healthy', 'broad-deep')))
    boards.append(board('canopy-boundaries-before-after-actual.png', ('isolated-small', 'narrow-arm', 'separated-corner')))
    G.write(out / 'actual-panel-manifest.json', {'boards': boards,
            'method': 'Every native240x160 panel is independently decoded and byte-compared to its copied mGBA framebuffer. Captions are outside captured pixels; no scene recomposition.'})
    G.markdown(out / 'actual/README.md', ['# Actual leaf-canopy review', '',
        '[Healthy/deep comparison](../healthy-deep-before-after-actual.png) · [Isolated/narrow/corner comparison](../canopy-boundaries-before-after-actual.png)', '',
        '- [New profile29: all eight views and recordings](profile-29/README.md)',
        '- [Previous profile19 control: all eight views and recordings](profile-19/README.md)', '',
        'The source catalog and resident layer reconstructions have separate labels. '
        'The full world view, player, HUD and actual foreground interaction are shown only by the native framebuffer images and recordings.'])
    summary = {'source_commit': next(iter(reports.values()))['source_commit'],
               'contexts': sum(len(r['captures']) for r in reports.values()),
               'passed': sum(r['passed'] for r in reports.values()), 'total': sum(r['total'] for r in reports.values()),
               'movies': sum(bool(row.get('video')) for r in reports.values() for row in r['captures']),
               'gifs': sum(bool(row.get('gif')) for r in reports.values() for row in r['captures']),
               'boards': len(boards), 'panels': sum(len(b['panels']) for b in boards),
               'gallery_tool_sha256': LOADED_SHA,
               'gallery_dependency_sha256': {Path(G.__file__).name: G.sha(G.__file__)},
               'profiles': [{'profile': p, 'report_sha256': G.sha(out / 'actual' / f'profile-{p}' / 'capture.json'),
                             'rom_sha256': r['rom_sha256'], 'contexts': len(r['captures']),
                             'passed': r['passed'], 'total': r['total']} for p, r in reports.items()]}
    assert G.sha(__file__) == LOADED_SHA
    G.write(out / 'actual-publication-summary.json', summary)
    print(json.dumps(summary))


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='mode', required=True)
    for name in ('source', 'actual'):
        q = sub.add_parser(name); q.add_argument('--work', type=Path, required=True)
        q.add_argument('--out', type=Path, required=True); q.add_argument('--final', action='store_true')
    args = p.parse_args()
    (source_main if args.mode == 'source' else actual_main)(args)


if __name__ == '__main__':
    main()
