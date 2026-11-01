#!/usr/bin/env python3
"""Native repeated-tree sources and literal mGBA diagnostic-grove review.

The six planted review layouts are deliberate fixtures, not procedural forest
adoption. Source floor previews and palette studies are never framebuffers.
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw
import forest_canopy_adaptive_gallery as G

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 30
LOADED_SHA = G.sha(__file__)
FLOORS = ('moss0', 'path', 'blight_floor')
FLOOR_LABELS = ('Grass', 'Dirt path', 'Sick ground')


def sources():
    sys.path.insert(0, str(ROOT / 'art'))
    art = importlib.import_module('forest_tree_study')
    terrain = importlib.import_module('forest_concepts_v2_terrain')
    previous = importlib.import_module('forest_canopy_emerald')
    paths = sorted((ROOT / 'art').glob('*.py')) + [ROOT / 'Makefile', ROOT / 'tools/build_assets.py']
    inputs = {str(p.relative_to(ROOT)): G.sha(p) for p in paths}
    colors = art.palette(); G.legal_palette(colors)
    entries = []
    for spec in art.specs():
        im = art.tree(spec['size'], spec['variety'], spec['state'])
        assert im.mode == 'P' and im.size == tuple(spec['size_pixels'])
        assert im.size in ((32, 32), (16, 32)) and spec['anchor'] == [im.width//2, 30]
        indices = list(im.tobytes())
        assert any(indices) and set(indices) <= set(range(16))
        entries.append({**spec, 'indices': indices,
                        'index_sha256': hashlib.sha256(bytes(indices)).hexdigest(),
                        'painted_bounds': im.getbbox(), 'painted_pixels': sum(v != 0 for v in indices)})
    assert len(entries) == 12
    floors = []
    for name, title in zip(FLOORS, FLOOR_LABELS):
        image, bank = terrain.paint(name, 0, 1)
        palette = terrain.palette(bank, 1); G.legal_palette(palette)
        floors.append({'name': name, 'title': title, 'bank': bank,
                       'indices': list(image.tobytes()), 'size': list(image.size), 'palette': palette})
    assert all(G.sha(ROOT / name) == digest for name, digest in inputs.items())
    return {'profile': PROFILE, 'name': 'Compact repeated trees', 'entries': entries,
            'palette': colors, 'palette_bank': art.PALETTE_NAME,
            'palette_roles': {'contour': [1], 'contact': [2], 'wood': list(art.WOOD_INDICES),
                              'healthy_foliage': list(art.GREEN_INDICES),
                              'sick_foliage': list(art.SICK_INDICES),
                              'attached_infection': list(art.GLOW_INDICES)},
            'previous_healthy_palette': previous.stage_palette(1, 0),
            'previous_deep_palette': previous.stage_palette(1, 3),
            'floor_sources': floors, 'source_input_sha256': inputs}


def background(floor, size):
    rgba = G.rgba(floor['indices'], floor['size'], floor['palette'])
    canvas = Image.new('RGB', size)
    for y in range(0, size[1], rgba.height):
        for x in range(0, size[0], rgba.width):
            canvas.paste(rgba.convert('RGB'), (x, y))
    return canvas


def frame(entry, colors):
    return G.rgba(entry['indices'], entry['size_pixels'], colors)


def catalog(value, out, silhouettes=False):
    cw, rh, header = 176, 132, 68
    image = Image.new('RGB', (cw*3, header+rh*4), G.BG); d = ImageDraw.Draw(image)
    G.label(d, (5, 3), 'SOURCE / repeated tree silhouettes' if silhouettes else 'SOURCE / compact repeated trees')
    G.label(d, (5, 22), 'Native 32x32 / 16x32 + exact 3x inspection. Deliberate source layout, not mGBA.', G.DIM)
    for col, state in enumerate(('Healthy', 'Sick', 'Dead')):
        G.label(d, (col*cw+5, 47), state)
    panels = []
    for n, entry in enumerate(value['entries']):
        row, col = n//3, n%3; x, y = col*cw, header+row*rh
        G.label(d, (x+5, y), f'{entry["variety_name"]} / {entry["w"]}x32', G.DIM)
        ground = Image.new('RGB', (cw-4, 106), G.BG) if silhouettes else background(value['floor_sources'][0], (cw-4, 106))
        picture = frame(entry, value['palette'])
        if silhouettes:
            picture.paste('#e0d8b0', (0, 0, picture.width, picture.height), picture.getchannel('A'))
        native_x = 8+(32-picture.width)//2
        G.paste(ground, picture, (native_x, 67))
        G.paste(ground, picture, (62+(96-picture.width*3)//2, 4), 3)
        image.paste(ground, (x+2, y+22))
        panels.append({'name': entry['name'], 'native_rect': [x+2+native_x, y+89, picture.width, 32],
                       'inspection_scale': 3, 'kind': 'silhouette diagnostic' if silhouettes else 'source on unchanged grass art'})
    target = out / ('silhouettes-source.png' if silhouettes else 'tree-states-source.png')
    image.save(target)
    return {'path': target.name, 'sha256': G.sha(target), 'panels': panels}


def floor_board(value, out):
    cw, rh, header = 144, 82, 56
    image = Image.new('RGB', (cw*3, header+rh*4), G.BG); d = ImageDraw.Draw(image)
    G.label(d, (5, 3), 'SOURCE / same trees on three unchanged forest floors')
    G.label(d, (5, 22), 'H / S / D left to right in every cell; native size. Not an emulator scene.', G.DIM)
    for col, floor in enumerate(value['floor_sources']):
        G.label(d, (col*cw+5, 40), floor['title'])
    panels = []
    for row in range(4):
        group = value['entries'][row*3:row*3+3]
        for col, floor in enumerate(value['floor_sources']):
            x, y = col*cw, header+row*rh
            G.label(d, (x+5, y), group[0]['variety_name'], G.DIM)
            patch = background(floor, (cw-4, 58))
            for state, entry in enumerate(group):
                picture = frame(entry, value['palette']); px = 9+state*43+(32-picture.width)//2
                G.paste(patch, picture, (px, 20))
                panels.append({'name': entry['name'], 'floor': floor['name'],
                               'native_rect': [x+2+px, y+40, picture.width, picture.height]})
            image.paste(patch, (x+2, y+20))
    image.save(out/'floor-contacts-source.png')
    return {'path': 'floor-contacts-source.png', 'sha256': G.sha(out/'floor-contacts-source.png'), 'panels': panels}


def palette_board(value, out):
    image = Image.new('RGB', (592, 266), G.BG); d = ImageDraw.Draw(image)
    G.label(d, (5, 3), 'SOURCE / palette iteration / authored RGB555 colors')
    G.label(d, (5, 22), 'Previous material tables are references; the new trees share ONE bank in every state.', G.DIM)
    rows = [('Previous healthy leaf-crown bank', value['previous_healthy_palette']),
            ('Previous deep leaf-crown bank', value['previous_deep_palette']),
            ('New shared tree bank: healthy + sick + dead coexist', value['palette'])]
    for row, (title, colors) in enumerate(rows):
        y = 45+row*57; G.label(d, (5, y), title)
        for i, color in enumerate(colors):
            x = 6+i*36; d.rectangle((x, y+18, x+31, y+34), fill=color)
            G.label(d, (x, y+36), str(i), G.DIM)
    G.label(d, (5, 221), 'New roles: 1 contour / 2 contact / 3-5 wood / 6-9 green / 10-12 olive / 13-15 violet light', G.DIM)
    G.label(d, (5, 241), 'Quieter planes; warm wood and olive connect with dirt/grass; purple stays attached to damage.', G.DIM)
    image.save(out/'palette-iteration-source.png')


def source_main(args):
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    freeze = G.frozen(args.work.resolve(), PROFILE, args.final)
    value = sources(); value.update(source_commit=freeze['source_commit'], rom_sha256=freeze.get('rom_sha256'),
                                    gallery_tool_sha256=LOADED_SHA)
    G.write(out/'source-art.json', value, compact=True)
    native = []; folder = out/'native'; folder.mkdir(exist_ok=True)
    for entry in value['entries']:
        stem = entry['name']; p = folder/(stem+'-indexed.png'); r = folder/(stem+'.png')
        G.indexed(entry['indices'], entry['size_pixels'], value['palette']).save(p, bits=4)
        picture = frame(entry, value['palette']); picture.save(r)
        assert Image.open(p).convert('RGBA').tobytes() == picture.tobytes()
        native.append({k: v for k, v in entry.items() if k != 'indices'} | {
            'native_indexed': str(p.relative_to(out)), 'native_rgba': str(r.relative_to(out))})
    boards = [catalog(value, out), catalog(value, out, True), floor_board(value, out)]
    gray = Image.open(out/'tree-states-source.png').convert('L').convert('RGB')
    gd = ImageDraw.Draw(gray); gd.rectangle((0, 0, gray.width, 42), fill='#202020')
    G.label(gd, (5, 3), 'GRAYSCALE SOURCE DIAGNOSTIC / same native shapes and floors', '#e0e0e0')
    G.label(gd, (5, 22), 'Diagnostic luminance only; native indexed assets keep the shared RGB555 palette.', '#b0b0b0')
    gray.save(out/'grayscale-source.png')
    palette_board(value, out)
    G.write(out/'native-manifest.json', {'profile': PROFILE, 'entries': native, 'boards': boards,
             'note': 'Native canvas, visible bounds, ground origin and physical collider are separate contracts.'})
    G.markdown(out/'README.md', ['# Compact repeated trees: native source', '',
        '**SOURCE artwork and floor previews. Actual mGBA diagnostic groves are separate.**', '',
        '![Twelve trees: native and 3x inspection](tree-states-source.png)', '',
        '[Same trees on three floors](floor-contacts-source.png) · [Silhouettes](silhouettes-source.png) · '
        '[Grayscale diagnostic](grayscale-source.png) · '
        '[Palette iteration](palette-iteration-source.png) · [Native files and origins](native-manifest.json)', '',
        'The kit has two forms per footprint (32×32 and 16×32), each healthy, sick and dead: twelve pieces, not twelve styles. '
        'Every state has its own structural drawing. All use one 16-entry RGB555 bank with transparent index0 and a fixed bottom-center origin at y30.', '',
        'Healthy trees keep full crowns; sick trees lose or sag foliage and expose damaged branches; dead trees use bare broken forks. '
        'The existing green/olive/wood/violet palette family is simplified into quiet connected masses and local root shadows. '
        'The same unchanged grass, dirt and sick-ground source art is used for background comparisons. No background is baked into the native PNGs.', '',
        'Regular forest/canopy artwork, generation and old colliders are not replaced by this source study. Integer enlargements are inspection views only.'])
    files = {str(p.relative_to(out)): {'sha256': G.sha(p), 'bytes': p.stat().st_size}
             for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'source-manifest.json'}
    manifest = {'source_commit': freeze['source_commit'], 'profile': PROFILE, 'rom_sha256': freeze.get('rom_sha256'),
                'gallery_tool_sha256': LOADED_SHA, 'gallery_dependency_sha256': {Path(G.__file__).name: G.sha(G.__file__)},
                'source_input_sha256': value['source_input_sha256'], 'native_images': len(native), 'palette_banks': 1,
                'files': files, 'kind': 'frozen source inspection' if args.final else 'unfrozen source inspection'}
    assert G.sha(__file__) == LOADED_SHA
    G.write(out/'source-manifest.json', manifest)
    print(json.dumps({'native_images': len(native), 'files': len(files), 'source_commit': freeze['source_commit']}))


def row_files(row):
    paths = set()
    for item in row.get('native_frames', []):
        if isinstance(item, dict):
            paths.add(item['path'])
        else:
            paths.add(item)
    for field in ('image', 'after_image', 'filmstrip', 'video', 'gif'):
        if row.get(field):
            paths.add(row[field])
    for group in ('phase_keyframes', 'action_keyframes', 'keyframes'):
        for item in row.get(group, []):
            if isinstance(item, dict) and item.get('path'):
                paths.add(item['path'])
            elif isinstance(item, str):
                paths.add(item)
    return paths


def actual_main(args):
    work, out = args.work.resolve(), args.out.resolve()
    base = (args.report.parent if args.report else work/'runtime/v30').resolve()
    report_path = args.report.resolve() if args.report else base/'capture.json'
    report = json.loads(report_path.read_text()); freeze = G.frozen(work, PROFILE, args.final)
    profile = report.get('forest_variant', report.get('profile', report.get('variant')))
    assert profile == PROFILE
    rows = report.get('captures', report.get('cases'))
    assert isinstance(rows, list) and len(rows) == 8
    overview = rows[:6]
    assert [row.get('request') for row in overview] == list(range(6))
    assert {row['name'] for row in rows[6:]} == {'broad-tree-walk-around', 'narrow-tree-walk-around'}
    if args.final:
        assert report.get('complete') and not report.get('unfrozen_pilot', False)
        assert not report.get('failures') and report['passed'] == report['total']
        assert report['source_commit'] == freeze['source_commit']
        assert report['rom_sha256'] == freeze['rom_sha256']
        assert report['capture_tool_sha256'] == G.sha(ROOT/'tools/forest_tree_review.py')
    destination = out/'actual'; destination.mkdir(parents=True, exist_ok=True)
    G.exact_copy(report_path, destination/'capture.json')
    paths = {p for row in rows for p in row_files(row)}
    for row in rows:
        for item in row.get('native_frames', []):
            if isinstance(item, dict) and item.get('sha256'):
                assert G.sha(base/item['path']) == item['sha256']
    for relative in sorted(paths):
        source = (base/relative).resolve()
        assert source.is_relative_to(base) and 'all-frames' not in source.parts
        G.exact_copy(source, destination/relative)
    lines = ['# Actual mGBA tree-study groves', '',
             '**These are deliberately planted diagnostic layouts, not naturally generated forest rooms.**', '',
             'The actual retained ROM routine places the native trees over existing forest floors, with Bloom for scale. '
             'Normal forest/canopy artwork and procedural placement are unchanged. These captured game pixels are not source composites.', '',
             '[Exact capture report](capture.json)', '']
    for row in rows:
        lines += [f'## {row["name"]}', '', f'![Actual native framebuffer]({row["image"]})', '']
        links = [f'[{title}]({row[field]})' for field, title in
                 [('after_image', 'After'), ('filmstrip', 'Native filmstrip'), ('video', 'Full-rate MP4'), ('gif', 'Exact-color GIF')]
                 if row.get(field)]
        lines += [' · '.join(links), '']
    lines += ['Native PNGs and exact-color GIFs retain their stated fidelity; MP4s are lossy viewing copies. '
              'Raw all-frame recordings remain local. Canvas bounds, planted root collision and ground origins are different recorded contracts.']
    G.markdown(destination/'README.md', lines)
    board = Image.new('RGB', (480, 58+3*184), G.BG); d = ImageDraw.Draw(board)
    G.label(d, (5, 3), ('FROZEN' if args.final else 'PILOT')+' / ACTUAL mGBA / native 240x160 panels')
    G.label(d, (5, 22), 'Deliberately planted tree studies; normal forest/canopy placement is unchanged.', G.DIM)
    G.label(d, (5, 40), 'All twelve trees', G.DIM); G.label(d, (245, 40), 'Repeated mixed grove', G.DIM)
    # The engine emits catalog floor0..2 followed by repeated-grove floor0..2.
    # Prefer recorded fixture IDs; the documented row order is a fallback.
    def fixture_id(row, n):
        for key in ('request', 'preset', 'fixture', 'scene'):
            if isinstance(row.get(key), int):
                return row[key]
        for key in ('info', 'tree_study_info'):
            if isinstance(row.get(key), list) and len(row[key]) > 1:
                return row[key][1]
        return n
    keyed = {fixture_id(row, n): row for n, row in enumerate(overview)}
    assert set(keyed) == set(range(6)), ('Review fixture IDs', list(keyed))
    panels = []
    for floor in range(3):
        for col, fixture in enumerate((floor, floor+3)):
            row = keyed[fixture]; path = destination/row['image']; native = Image.open(path).convert('RGB')
            assert native.size == (240, 160)
            x, y = col*240, 58+floor*184
            G.label(d, (x+5, y), FLOOR_LABELS[floor], G.DIM); board.paste(native, (x, y+22))
            panels.append({'profile': PROFILE, 'case': row['name'], 'fixture': fixture,
                           'source': str(path.relative_to(out)), 'source_sha256': G.sha(path),
                           'rect': [x, y+22, 240, 160], 'rgb_sha256': hashlib.sha256(native.tobytes()).hexdigest(),
                           'kind': 'actual mGBA framebuffer of deliberately planted diagnostic grove'})
    target = out/'tree-groves-actual.png'; board.save(target)
    check = Image.open(target).convert('RGB')
    for panel in panels:
        x, y, width, height = panel['rect']
        assert check.crop((x, y, x+width, y+height)).tobytes() == Image.open(out/panel['source']).convert('RGB').tobytes()
    G.write(out/'actual-panel-manifest.json', {'boards': [{'path': target.name, 'sha256': G.sha(target), 'panels': panels}],
            'method': 'Literal native 240x160 framebuffer crops, byte-checked against copied PNGs. Captions are outside game pixels.'})
    summary = {'profile': PROFILE, 'source_commit': report['source_commit'], 'rom_sha256': report['rom_sha256'],
               'contexts': len(rows), 'passed': report['passed'], 'total': report['total'],
               'movies': sum(bool(r.get('video')) for r in rows), 'gifs': sum(bool(r.get('gif')) for r in rows),
               'boards': 1, 'panels': len(panels), 'gallery_tool_sha256': LOADED_SHA,
               'capture_report_sha256': G.sha(destination/'capture.json'), 'copied_media_files': len(paths),
               'fixture_scope': 'Deliberate repeated-tree diagnostic plantings, not natural forest generation or a canopy redesign.'}
    G.write(out/'actual-publication-summary.json', summary)
    assert G.sha(__file__) == LOADED_SHA
    print(json.dumps(summary))


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='mode', required=True)
    for name in ('source', 'actual'):
        q = sub.add_parser(name); q.add_argument('--work', type=Path, required=True)
        q.add_argument('--out', type=Path, required=True); q.add_argument('--final', action='store_true')
        if name == 'actual':
            q.add_argument('--report', type=Path)
    args = p.parse_args(); (source_main if args.mode == 'source' else actual_main)(args)


if __name__ == '__main__':
    main()
