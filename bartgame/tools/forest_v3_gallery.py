#!/usr/bin/env python3
"""Focused native SOURCE and truthful mGBA publication for canopy studies.

Source assemblies are deliberately separate from captured gameplay. Canonical
canopy frames are exported individually; the many adjacency aliases share
literal indexed sheets, with every native rectangle recorded in JSON. No
unrelated prop, portrait or equipment catalog is copied from the prior pass.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw

import forest_concept_gallery as G

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art'
PROFILES = tuple(range(11, 19))
BG, FIELD, FG, DIM = G.BG, G.FIELD, G.FG, G.DIM
LOADED_TOOL_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value, compact=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    options = {'separators': (',', ':')} if compact else {'indent': 2}
    path.write_text(json.dumps(value, **options) + '\n')


def markdown(path, lines):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text('\n'.join(lines) + '\n')


def crop_record(entry, rect):
    return {'name': entry['name'], 'id': entry['id'], 'phase': entry['phase'],
            'palette': entry['palette'], 'rect': list(rect),
            'index_sha256': entry['index_sha256'], 'rgba_sha256': entry['rgba_sha256']}


def freeze(work, profile, final):
    if not final:
        return {'source_commit': None, 'status': 'UNFROZEN SOURCE PILOT'}
    path = work / f'frozen/v{profile}/freeze.json'
    if not path.exists():
        assert not final, ('Final export needs frozen source', path)
        return {'source_commit': None, 'status': 'UNFROZEN SOURCE PILOT'}
    value = json.loads(path.read_text())
    assert value.get('variant', value.get('forest_variant')) == profile
    for key in ('source_file_sha256', 'code_file_sha256'):
        for name, expected in value.get(key, {}).items():
            assert sha(ROOT / name) == expected, ('Current source differs from freeze', profile, name)
    if final:
        assert value.get('source_commit'), path
        rom = path.parent / 'bartgame.gba'
        assert sha(rom) == value['rom_sha256'], rom
    return {**value, 'freeze_sha256': sha(path)}


def worker(args):
    os.environ['BART_FOREST'] = str(args.profile)
    sys.path.insert(0, str(ART))
    inputs = sorted(ART.glob('*.py')) + [ART / 'reboot_contracts.json', ROOT / 'tools/build_assets.py', ROOT / 'Makefile']
    input_hashes = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    import forest_concepts as FC
    import forest_concepts_v3_terrain as V3
    import palettes
    import tiles

    assert FC.VARIANT == args.profile
    local = args.profile - 10
    colors = dict(palettes.BG_PALETTES)
    topology = getattr(tiles, 'FOREST_V2_TOPOLOGY')
    specs = {spec['name']: spec for spec in topology['specs']}
    coverage = {row['name']: row for row in tiles.COVERAGE}
    entries, context = [], {}
    for tile_id, mt in enumerate(tiles.METATILES):
        name = mt['name']
        spec = specs.get(name)
        selected = bool(V3.owns(name) or (spec and spec['family'] in ('canopy', 'fringe')))
        is_context = name in ('moss0', 'blight_floor', 'path') or (spec and spec['family'] == 'overhead_root_arch')
        if not selected and not is_context:
            continue
        for phase, rows in enumerate(mt.get('frames') or [mt['art']]):
            entry = {'kind': 'tile', 'name': name, 'id': tile_id, 'phase': phase,
                     'canvas': [16, 16], 'palette': mt['pal'], 'colors': colors[mt['pal']],
                     'indices': G.indices(rows, (16, 16)), 'type': mt['type'],
                     'coll': mt.get('coll', 0), 'owner': coverage[name]['owner'],
                     'glitter': bool(mt.get('glitter')), 'anim_speed': mt.get('anim_speed', 8),
                     'topology': spec, 'scope': 'appended_alias' if spec else 'canonical_canopy'}
            if mt.get('qpals'):
                entry['quarter_colors'] = [colors[n] for n in mt['qpals']]
                entry['quarter_palettes'] = mt['qpals']
            G.assert_palette(entry['colors'])
            entry['index_sha256'] = hashlib.sha256(bytes(entry['indices'])).hexdigest()
            entry['rgba_sha256'] = hashlib.sha256(G.rgba(entry).tobytes()).hexdigest()
            if selected:
                entries.append(entry)
            elif phase == 0:
                context[name] = entry
    pulse = V3.pulse_palettes(local)
    for bank, phases in pulse.items():
        assert len(phases) == 4 and phases[0] == colors[bank], bank
        for phase in phases:
            G.assert_palette(phase)
    macro = {}
    for sick in (False, True):
        image = V3.canopy_macro(local, sick=sick, phase=0)
        assert image.mode == 'P' and image.size == (32, 32)
        bank = 'canopy3_blight' if sick else 'foliage'
        macro['deep' if sick else 'healthy'] = {
            'kind': 'tile', 'name': 'canopy_macro', 'canvas': [32, 32],
            'palette': bank, 'colors': colors[bank], 'indices': list(image.tobytes())}
    label = FC.NAMES[args.profile]
    green = {k: list(v) for k, v in V3.GREEN_INDICES.items()}
    assert all(sha(ROOT / name) == digest for name, digest in input_hashes.items()), 'Source changed during snapshot'
    write(args.snapshot, {'profile': args.profile, 'local_variant': local, 'label': label,
                          'entries': entries, 'context': context, 'bg_colors': colors,
                          'pulse_palettes': pulse, 'green_indices': green, 'macro': macro,
                          'source_input_sha256': input_hashes})


def lookup(snapshot):
    return {(e['name'], e['phase']): e for e in snapshot['entries']}


def entry_image(snapshot, entry, phase=0):
    bank = entry['palette']
    if bank in snapshot['pulse_palettes']:
        entry = {**entry, 'colors': snapshot['pulse_palettes'][bank][phase % 4]}
    return G.rgba(entry)


def find(snapshot, name, phase=0):
    values = [e for e in snapshot['entries'] if e['name'] == name]
    if not values:
        return snapshot['context'][name]
    return next(e for e in values if e['phase'] == phase % len(values))


def alias(snapshot, kind, q, mask, corners=0):
    return next(e for e in snapshot['entries'] if e.get('topology') and
                e['topology']['family'] == 'canopy' and e['topology']['kind'] == kind and
                e['topology']['quadrant'] == q and e['topology']['mask'] == mask and
                e['topology']['corners'] == corners)


def tiled_floor(snapshot, size, name='blight_floor'):
    image = Image.new('RGB', size, BG)
    tile = G.rgba(snapshot['context'][name])
    for y in range(0, size[1], 16):
        for x in range(0, size[0], 16):
            G.paste(image, tile, (x, y))
    return image


def map_assembly(snapshot, cells, palette_phase=0, floor='blight_floor', world_origin=(0, 0)):
    """A declared source shape using the renderer's four parity selections."""
    h, w = len(cells), len(cells[0])
    image = tiled_floor(snapshot, (w * 16, h * 16), floor)
    def present(x, y):
        return 0 <= x < w and 0 <= y < h and bool(cells[y][x])
    panels = []
    for y, row in enumerate(cells):
        for x, kind in enumerate(row):
            if not kind:
                continue
            n, e, s, west = present(x, y - 1), present(x + 1, y), present(x, y + 1), present(x - 1, y)
            mask = (0 if n else 1) | (0 if e else 2) | (0 if s else 4) | (0 if west else 8)
            corners = (0 if not n or not west or present(x - 1, y - 1) else 1) | (
                0 if not n or not e or present(x + 1, y - 1) else 2) | (
                0 if not s or not e or present(x + 1, y + 1) else 4) | (
                0 if not s or not west or present(x - 1, y + 1) else 8)
            wx, wy = x + world_origin[0], y + world_origin[1]
            entry = alias(snapshot, kind, (wx & 1) | ((wy & 1) << 1), mask, corners)
            G.paste(image, entry_image(snapshot, entry, palette_phase), (x * 16, y * 16))
            panels.append({**crop_record(entry, (x * 16, y * 16, 16, 16)),
                           'cell': [x, y], 'world_cell': [wx, wy]})
    return image, panels


def stage_assembly(snapshot, stage, phase=0):
    # Mixed is an explicit source material boundary, not an invented middle
    # palette or an assertion that engine stage2 is painted this exact way.
    cells = [[0] * 6 for _ in range(4)]
    for y in range(1, 3):
        for x in range(1, 5):
            cells[y][x] = 1 if stage == 'healthy' or (stage == 'mixed' and x < 3) else 2
    # Offset the floor border by one world cell so the two complete32px
    # source crowns start on even parity. Separate alias/island sheets expose
    # arbitrary parity and clipped edge cases instead of hiding those tests.
    return map_assembly(snapshot, cells, phase, 'moss0' if stage == 'healthy' else 'blight_floor', (1, 1))


def group_image(snapshot, group, phase=0):
    cols, names = G.GROUPS[group]
    image = Image.new('RGBA', (cols * 16, math.ceil(len(names) / cols) * 16))
    for n, name in enumerate(names):
        G.paste(image, entry_image(snapshot, find(snapshot, name), phase), (n % cols * 16, n // cols * 16))
    return image


def export_entries(snapshot, out):
    canonical = [e for e in snapshot['entries'] if not e['topology']]
    exports = G.export_native({'entries': canonical}, out)
    alias_groups = {}
    for entry in snapshot['entries']:
        spec = entry['topology']
        if spec:
            key = spec['family'] + ('-healthy' if spec['kind'] == 1 else '-blight')
            alias_groups.setdefault(key, []).append(entry)
    sheets = []
    for family, entries in alias_groups.items():
        assert len({e['palette'] for e in entries}) == 1, family
        cols = 16
        image = Image.new('P', (cols * 16, math.ceil(len(entries) / cols) * 16))
        indexed = G.indexed(entries[0]); image.putpalette(indexed.getpalette()); image.info['transparency'] = 0
        rectangles = []
        for n, entry in enumerate(entries):
            x, y = n % cols * 16, n // cols * 16
            image.paste(G.indexed(entry), (x, y))
            rectangles.append(crop_record(entry, (x, y, 16, 16)))
        stem = out / 'native-aliases' / family
        stem.parent.mkdir(parents=True, exist_ok=True)
        path_i, path_r = stem.with_name(stem.name + '-indexed.png'), stem.with_name(stem.name + '.png')
        image.save(path_i); image.convert('RGBA').save(path_r)
        check = Image.open(path_i).convert('RGBA')
        for entry, rect in zip(entries, rectangles):
            x, y, w, h = rect['rect']
            assert check.crop((x, y, x + w, y + h)).tobytes() == G.rgba(entry).tobytes()
        sheets.append({'family': family, 'palette': entries[0]['palette'],
                       'indexed_png': str(path_i.relative_to(out)), 'rgba_png': str(path_r.relative_to(out)),
                       'entries': rectangles})
    write(out / 'native-manifest.json', {'canonical_frames': exports, 'alias_sheets': sheets})
    return canonical, sheets


def adjacency_board(snapshot, kind):
    combos = sorted({(e['topology']['mask'], e['topology']['corners']) for e in snapshot['entries']
                     if e.get('topology') and e['topology']['family'] == 'canopy'})
    assert len(combos) == 47
    cw, ch, cols = 104, 79, 8
    board = Image.new('RGB', (cw * cols, 56 + math.ceil(len(combos) / cols) * ch), BG)
    draw = ImageDraw.Draw(board)
    G.label(draw, (6, 4), f'{snapshot["label"]}: all47 {"healthy" if kind == 1 else "infected"} SOURCE cases')
    G.label(draw, (6, 23), 'Each group: four separate world-parity samples. They are not a falsely connected island.', DIM)
    panels = []
    for n, (mask, corners) in enumerate(combos):
        x, y = n % cols * cw, 56 + n // cols * ch
        G.label(draw, (x + 4, y), f'edges:{mask:x} inner:{corners:x}', DIM)
        for q in range(4):
            entry = alias(snapshot, kind, q, mask, corners)
            tile = entry_image(snapshot, entry)
            xx, yy = x + 4 + q * 24, y + 24
            field = tiled_floor(snapshot, (16, 16), 'moss0' if kind == 1 else 'blight_floor')
            G.paste(field, tile, (0, 0))
            board.paste(field, (xx, yy))
            panels.append({**crop_record(entry, (xx, yy, 16, 16)), 'source_substrate': 'moss0' if kind == 1 else 'blight_floor'})
    return board, panels


def islands_board(snapshot):
    patterns = [
        ('isolated', [[1]]), ('short row', [[1, 1]]), ('short column', [[1], [1]]),
        ('2x2 crown', [[1, 1], [1, 1]]), ('3x3 crown', [[1] * 3 for _ in range(3)]),
        ('inner elbow', [[1, 1, 1], [1, 0, 0], [1, 0, 0]]),
        ('fork', [[1, 1, 1], [0, 1, 0], [0, 1, 0]]),
        ('concave ring', [[1, 1, 1], [1, 0, 1], [1, 1, 1]])]
    cw, ch = 268, 198
    board = Image.new('RGB', (cw * 4, 56 + ch * 4), BG); draw = ImageDraw.Draw(board)
    G.label(draw, (7, 4), f'{snapshot["label"]}: actual alias SOURCE island/strip joins')
    G.label(draw, (7, 23), 'Literal source shapes and substrates, not generator or mGBA evidence. Native + exact2x.', DIM)
    proofs = []
    for kind in (1, 2):
        for n, (name, cells) in enumerate(patterns):
            xx, yy = n % 4 * cw, 56 + (n // 4 + (kind - 1) * 2) * ch
            cells = [[kind * x for x in row] for row in cells]
            cells = [[0] * (len(cells[0]) + 2)] + [[0] + row + [0] for row in cells] + [[0] * (len(cells[0]) + 2)]
            image, panels = map_assembly(snapshot, cells, floor='moss0' if kind == 1 else 'blight_floor')
            G.label(draw, (xx + 5, yy), ('Living ' if kind == 1 else 'Infected ') + name)
            board.paste(image, (xx + 5, yy + 26))
            G.paste(board, image, (xx + 95, yy + 26), 2)
            proofs.append({'kind': kind, 'name': name, 'cells': cells, 'native_rect': [xx + 5, yy + 26, *image.size],
                           'inspection_rect': [xx + 95, yy + 26, image.width * 2, image.height * 2],
                           'inspection_scale': 2, 'panels': panels})
    return board, proofs


def green_metrics(snapshot):
    measurements = {}
    def measure(entry):
        roles = set(snapshot['green_indices'].get(entry['palette'], []))
        opaque = sum(index != 0 for index in entry['indices'])
        green = sum(index in roles for index in entry['indices'])
        return {'declared_live_green_pixels': green, 'painted_pixels': opaque,
                'live_green_percent_of_painted': round(100 * green / opaque, 3) if opaque else None,
                'green_ink_indices': sorted(roles)}
    for name, entry in snapshot['macro'].items():
        measurements['macro-' + name] = measure(entry)
    for group in ('oak', 'sick-tree', 'dead-tree'):
        parts = [find(snapshot, name) for name in G.GROUPS[group][1]]
        values = [measure(e) for e in parts]
        painted = sum(v['painted_pixels'] for v in values)
        green = sum(v['declared_live_green_pixels'] for v in values)
        measurements['authored-' + group] = {
            'declared_live_green_pixels': green, 'painted_pixels': painted,
            'live_green_percent_of_painted': round(100 * green / painted, 3) if painted else None,
            'source_parts': [e['name'] for e in parts]}
    isolated = [e for e in snapshot['entries'] if e.get('topology') and e['topology']['family'] == 'canopy'
                and e['topology']['kind'] == 2 and e['topology']['mask'] == 15 and e['topology']['corners'] == 0]
    measurements['deep-isolated-parity-samples'] = [{**measure(e), 'name': e['name'],
                                                   'quadrant': e['topology']['quadrant']} for e in isolated]
    return {'method': 'Count explicitly authored live-green ink roles among nontransparent painted source pixels. '
                      'This is a compositional proxy, not a claim that every tile or every dark/purple pixel is biologically infected. '
                      'The approximate 80/20 brief applies to whole crowns; clipped parity samples are also disclosed.',
            'profile': snapshot['profile'], 'label': snapshot['label'], 'measurements': measurements}


def palette_board(snapshot):
    rows = [('foliage', 0)] + [('canopy3_blight', phase) for phase in range(4)]
    cw, ch, left = 44, 69, 145
    image = Image.new('RGB', (left + cw * 16, 58 + ch * len(rows)), BG); draw = ImageDraw.Draw(image)
    G.label(draw, (5, 3), snapshot['label'] + ': native RGB555 canopy inks')
    G.label(draw, (5, 22), 'Stored index0 RGB shown here; index0 is transparent in artwork. Palette inspection is SOURCE, not screenshot grading.', DIM)
    swatches = []
    for row, (bank, phase) in enumerate(rows):
        colors = snapshot['pulse_palettes'][bank][phase] if bank in snapshot['pulse_palettes'] else snapshot['bg_colors'][bank]
        yy = 58 + row * ch
        G.label(draw, (5, yy + 13), bank, DIM); G.label(draw, (5, yy + 29), 'phase ' + str(phase), DIM)
        for index, color in enumerate(colors):
            xx = left + index * cw
            G.label(draw, (xx + 3, yy), str(index), DIM)
            draw.rectangle((xx + 3, yy + 18, xx + 35, yy + 38), fill=color)
            G.label(draw, (xx + 1, yy + 43), color[1:], DIM)
            swatches.append({'bank': bank, 'phase': phase, 'index': index, 'rgb555_color': color,
                             'swatch_rect': [xx + 3, yy + 18, 33, 21]})
    return image, swatches


def branch_layers_board(snapshot):
    """Show literal floor and roof planes, without simulating the body guard."""
    cw, ch = 220, 244
    board = Image.new('RGB', (cw * 3, 58 + 2 * ch), BG); draw = ImageDraw.Draw(board)
    G.label(draw, (5, 3), snapshot['label'] + ': horizontal crown/fringe SOURCE planes')
    G.label(draw, (5, 22), 'BG2 floor + BG1 foreground. No synthetic Bloom visibility or engine-cutout simulation.', DIM)
    proof = []
    for row, kind in enumerate((1, 2)):
        floor_name = 'moss0' if kind == 1 else 'blight_floor'
        cells = [[kind] * 4, [kind] * 4, [0] * 4, [0] * 4]
        floor = tiled_floor(snapshot, (64, 64), floor_name)
        _, panels = map_assembly(snapshot, cells, floor=floor_name)
        roof = Image.new('RGBA', (64, 64))
        for panel in panels:
            entry = find(snapshot, panel['name'], panel['phase'])
            G.paste(roof, entry_image(snapshot, entry), tuple(panel['rect'][:2]))
        fringe = next(e for e in snapshot['entries'] if e.get('topology') and
                      e['topology']['family'] == 'fringe' and e['topology']['kind'] == kind and
                      e['topology']['mask'] == 1)
        for x in range(4):
            G.paste(roof, entry_image(snapshot, fringe), (x * 16, 32))
            panels.append(crop_record(fringe, (x * 16, 32, 16, 16)))
        composite = floor.copy(); G.paste(composite, roof, (0, 0))
        for col, (title, image) in enumerate((('BG2 actual floor', floor), ('BG1 transparent crown + branch', roof),
                                            ('Literal source composite', composite))):
            x, y = col * cw + 5, 58 + row * ch
            G.label(draw, (x, y), ('Living: ' if kind == 1 else 'Infected: ') + title)
            G.paste(board, image, (x, y + 27), 3)
        proof.append({'kind': kind, 'floor': floor_name, 'cells': cells, 'alias_panels': panels,
                      'floor_rgb_sha256': hashlib.sha256(floor.tobytes()).hexdigest(),
                      'roof_rgba_sha256': hashlib.sha256(roof.tobytes()).hexdigest(),
                      'composite_rgb_sha256': hashlib.sha256(composite.tobytes()).hexdigest()})
    return board, proof


def source_variant(snapshot, out, hold):
    out.mkdir(parents=True, exist_ok=True)
    canonical, sheets = export_entries(snapshot, out)
    status = snapshot.get('export_status', 'SOURCE')
    G.atlas(canonical, status + ' / ' + snapshot['label'] + ': canopy/tree SOURCE frames').save(out / 'canonical-canopy-catalog-source.png')
    proofs = {}
    for kind, name in ((1, 'healthy'), (2, 'infected')):
        image, panels = adjacency_board(snapshot, kind)
        image.save(out / f'all47-{name}-source.png'); proofs[name] = panels
    image, islands = islands_board(snapshot)
    image.save(out / 'adjacency-islands-source.png')
    image, branch_layers = branch_layers_board(snapshot)
    image.save(out / 'foreground-branch-layers-source.png')
    image, swatches = palette_board(snapshot); image.save(out / 'palette-inks-source.png')
    write(out / 'assembly-manifest.json', {'all47': proofs, 'islands': islands, 'branch_layers': branch_layers,
                                          'palette_swatches': swatches})
    metrics = green_metrics(snapshot); write(out / 'green-retention.json', metrics)
    frames = []
    for phase in range(4):
        image = Image.new('RGB', (3 * 212, 230), BG); draw = ImageDraw.Draw(image)
        G.label(draw, (5, 3), f'{status} / {snapshot["label"]}: BG phase{phase}, fixed{hold}ms SOURCE inspection')
        G.label(draw, (5, 21), 'No screenshot grade. Mixed is a declared healthy/infected material boundary; not a third engine palette.', DIM)
        for col, stage in enumerate(('healthy', 'mixed', 'deep')):
            field, _ = stage_assembly(snapshot, stage, phase)
            G.label(draw, (col * 212 + 5, 42), stage)
            G.paste(image, field, (col * 212 + 5, 62), 2)
        image.save(out / f'palette-phase-{phase}-source.png'); frames.append(image)
    gif = G.exact_gif(frames, hold, out / 'palette-pulse-source.gif')
    assert not gif.get('omitted'), gif
    write(out / 'source-gif.json', gif)
    markdown(out / 'README.md', [f'# {snapshot["local_variant"]}. {snapshot["label"]}: native source', '',
        '**SOURCE artwork and assemblies; these are not emulator captures.**', '',
        '[Back to all eight](../README.md)', '',
        '![Native canopy/tree source catalog](canonical-canopy-catalog-source.png)', '',
        '[47 healthy cases](all47-healthy-source.png) · [47 infected cases](all47-infected-source.png) · '
        '[Islands, strips and concave joins](adjacency-islands-source.png) · '
        '[Floor/branch foreground planes](foreground-branch-layers-source.png)', '',
        '[Exact fixed-clock palette inspection](palette-pulse-source.gif) · [Four PNG phases](palette-phase-0-source.png) · '
        '[Native ink swatches](palette-inks-source.png)', '',
        '[Canonical native frames and alias-sheet rectangles](native-manifest.json) · '
        '[Assembly definitions](assembly-manifest.json) · [Green-retention measurement](green-retention.json)', '',
        'Canonical frames have individual indexed/RGBA PNGs. Appended canopy/fringe aliases share literal native indexed sheets; '
        'every 16×16 rectangle and its nibble/RGBA hash is recorded. Logical collision is reported separately from image transparency. '
        'Source silhouettes cannot prove in-game visibility, cutout behavior or motion. The separately labelled actual recordings do.', '',
        'In forest play, semantic canopy cells select adjacency/parity aliases. The canonical pictures remain catalogued for full '
        'source review alongside the actual render-alias sheets.', '',
        'The approximate 80/20 retained-green target is measured over complete source crowns using declared live-green ink roles; '
        'it is not imposed on every quarter or counted by screenshot hue. Fixed inspection holds do not establish gameplay cadence.'])
    return {'profile': snapshot['profile'], 'local_variant': snapshot['local_variant'], 'label': snapshot['label'],
            'canonical_frame_instances': len(canonical), 'alias_instances': sum(len(s['entries']) for s in sheets),
            'source_gif': gif, 'green_retention': metrics}


def source_comparisons(snapshots, out):
    cw, ch = 212, 198
    board = Image.new('RGB', (cw * 3, 54 + ch * len(snapshots)), BG); draw = ImageDraw.Draw(board)
    status = snapshots[0].get('export_status', 'SOURCE')
    G.label(draw, (6, 3), status + ' / EIGHT CANOPY STUDIES / native SOURCE assemblies, not emulator screenshots')
    G.label(draw, (6, 22), 'Healthy / mixed materials / deep infection. Native pixels enlarged exactly2x; accepted grey soil is literal context.', DIM)
    panels = []
    for row, snap in enumerate(snapshots):
        yy = 54 + row * ch
        for col, stage in enumerate(('healthy', 'mixed', 'deep')):
            xx = col * cw
            G.label(draw, (xx + 5, yy), f'{snap["local_variant"]}. {snap["label"]}')
            G.label(draw, (xx + 5, yy + 17), stage, DIM)
            field, definitions = stage_assembly(snap, stage)
            G.paste(board, field, (xx + 5, yy + 38), 2)
            panels.append({'profile': snap['profile'], 'stage': stage,
                           'rect': [xx + 5, yy + 38, field.width * 2, field.height * 2],
                           'scale': 2, 'source_rgb_sha256': hashlib.sha256(field.tobytes()).hexdigest(),
                           'world_origin': [1, 1], 'alias_definitions': definitions})
    board.save(out / 'eight-canopy-directions-source.png')
    cw, ch = 228, 202
    trees = Image.new('RGB', (cw * 3, 54 + ch * len(snapshots)), BG); draw = ImageDraw.Draw(trees)
    G.label(draw, (6, 3), status + ' / HORIZONTAL TREE ANATOMY / literal authored source groups')
    G.label(draw, (6, 22), 'Living, infected and dead tree groups. These show source art, not player/foreground sorting.', DIM)
    for row, snap in enumerate(snapshots):
        yy = 54 + row * ch
        for col, (title, group) in enumerate((('living tree', 'oak'), ('infected tree', 'sick-tree'), ('dead tree', 'dead-tree'))):
            xx = col * cw
            G.label(draw, (xx + 5, yy), f'{snap["local_variant"]}. {snap["label"]}')
            G.label(draw, (xx + 5, yy + 18), title, DIM)
            image = group_image(snap, group)
            floor = tiled_floor(snap, (64, 64), 'moss0' if col == 0 else 'blight_floor')
            G.paste(floor, image, ((64 - image.width) // 2, 64 - image.height))
            G.paste(trees, floor, (xx + 5, yy + 42), 2)
            G.paste(trees, floor, (xx + 145, yy + 105))
    trees.save(out / 'horizontal-tree-forms-source.png')
    write(out / 'source-comparison-manifest.json', {'canopy_assemblies': panels})


def source_main(args):
    out, work = args.out.resolve(), args.work.resolve()
    out.mkdir(parents=True, exist_ok=True); work.mkdir(parents=True, exist_ok=True)
    sources = {p: freeze(work, p, args.final) for p in args.profiles}
    committed = {v['source_commit'] for v in sources.values()}
    assert len(committed) == 1, committed
    source_commit = next(iter(committed))
    snapshots = []
    def run(profile):
        path = work / 'source-snapshots' / f'v{profile}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, str(Path(__file__).resolve()), 'worker', '--profile', str(profile),
                        '--snapshot', str(path)], check=True, cwd=ROOT)
        return profile, json.loads(path.read_text())
    with ThreadPoolExecutor(max_workers=min(4, len(args.profiles))) as pool:
        fetched = dict(pool.map(run, args.profiles))
    reference_inputs = fetched[args.profiles[0]]['source_input_sha256']
    assert all(snapshot['source_input_sha256'] == reference_inputs for snapshot in fetched.values()), 'Mixed source snapshots'
    assert all(sha(ROOT / name) == digest for name, digest in reference_inputs.items()), 'Source changed during export'
    if args.final:
        for profile in args.profiles:
            assert freeze(work, profile, True) == sources[profile]
    summaries = []
    for profile in args.profiles:
        snapshot = fetched[profile]; snapshots.append(snapshot)
        snapshot['export_status'] = 'FROZEN' if args.final else 'DRAFT'
        base = out / f'variant-{profile - 10:02}'
        summary = source_variant(snapshot, base, args.hold)
        summary['freeze'] = sources[profile]
        write(base / 'snapshot.json', snapshot, compact=True); summaries.append(summary)
    source_comparisons(snapshots, out)
    markdown(out / 'README.md', ['# Eight native canopy directions', '',
        '**SOURCE review: native drawings, literal assemblies and fixed-clock palette inspection. Not mGBA screenshots.**', '',
        '![Eight canopy directions](eight-canopy-directions-source.png)', '',
        '[Healthy/infected/dead tree anatomy](horizontal-tree-forms-source.png)', '',
        *[f'- [{s["local_variant"]}. {s["label"]}](variant-{s["local_variant"]:02}/README.md)' for s in summaries], '',
        'The accepted grey diseased ground is retained as context. Every direction begins with recognizable tree/crown anatomy; '
        'the infection is attached to that structure. Green percentages use declared live-green ink roles among painted source pixels, '
        'not a biological claim or a quota for every small tile.', '',
        'Only the canopy/tree/fringe families are catalogued. The many adjacency aliases share indexed native sheets and exact crop/hash '
        'metadata instead of thousands of duplicate individual files. Existing prop, portrait, equipment and unrelated terrain catalogs '
        'are intentionally outside this focused pass.', '',
        '[Source inputs, outputs and summary](source-manifest.json) · [Comparison panel definitions](source-comparison-manifest.json)'])
    manifest = {'source_commit': source_commit, 'status': 'FINAL FROZEN SOURCE' if args.final else 'UNFROZEN SOURCE PILOT',
                'review_tool_sha256': LOADED_TOOL_SHA256, 'helper_sha256': {'forest_concept_gallery.py': sha(Path(G.__file__))},
                'current_source_input_sha256': reference_inputs,
                'profiles': summaries, 'files': {},
                'method': 'Authored native RGB555 palette/nibble data. Canonical individual PNGs and literal indexed alias-sheet crops '
                          'roundtrip exactly. Source assemblies/inspection GIFs do not stand in for real emulator evidence.'}
    for p in sorted(out.rglob('*')):
        if p.is_file() and p != out / 'source-manifest.json':
            manifest['files'][str(p.relative_to(out))] = {'sha256': sha(p), 'bytes': p.stat().st_size}
    assert sha(__file__) == LOADED_TOOL_SHA256, 'Gallery tool changed during export'
    write(out / 'source-manifest.json', manifest)
    print(json.dumps({'source_commit': source_commit, 'profiles': args.profiles,
                      'frames': sum(s['canonical_frame_instances'] + s['alias_instances'] for s in summaries),
                      'files': len(manifest['files'])}))


def exact_copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    assert sha(source) == sha(destination), (source, destination)


def safe_file(root, relative):
    path = (root / relative).resolve()
    assert path.is_relative_to(root.resolve()) and path.is_file(), path
    return path


def diagnostic(case):
    return 'diagnostic' in case.get('fixture_kind', '').lower() or case.get('group') == 'diagnostic'


def case_frames(case):
    frames = case.get('phase_keyframes', []) + case.get('action_keyframes', [])
    frames += [{**f, 'label': 'Glow phase ' + str(f['phase'])} for f in case.get('pulse_phase_keyframes', [])]
    worst = case.get('worst_visibility_keyframe')
    if worst and worst not in frames:
        frames.append(worst)
    displayed = case.get('displayed_character_keyframe')
    if displayed and displayed not in frames:
        frames.append(displayed)
    return frames


def capture_destination(out, profile):
    return out / 'actual' / (f'variant-{profile - 10:02}' if profile >= 11 else f'control-v{profile}')


def copy_capture(work, out, profile, final):
    root = work / f'runtime/v{profile}'
    report = json.loads((root / 'capture.json').read_text())
    frozen = freeze(work, profile, final)
    assert report.get('forest_variant', profile) == profile
    if final:
        assert report.get('complete') and report['passed'] == report['total'] and not report.get('failures')
        assert report['rom_sha256'] == frozen['rom_sha256'] and report['source_commit'] == frozen['source_commit']
        assert report['capture_tool_sha256'] == sha(ROOT / 'tools/forest_v3_review.py')
    destination = capture_destination(out, profile)
    destination.mkdir(parents=True, exist_ok=True)
    exact_copy(root / 'capture.json', destination / 'capture.json')
    files = set()
    for case in report['captures']:
        for key in ('image', 'after_image', 'filmstrip', 'video', 'gif'):
            if case.get(key):
                files.add(case[key])
        files.update(case.get('native_frames', []))
        for entry in case_frames(case):
            files.add(entry['path'])
            if entry.get('sha256'):
                assert sha(safe_file(root, entry['path'])) == entry['sha256']
    for relative in sorted(files):
        assert 'all-frames' not in Path(relative).parts, relative
        exact_copy(safe_file(root, relative), destination / relative)
    for is_diag in (False, True):
        cases = [c for c in report['captures'] if diagnostic(c) == is_diag]
        path = destination / ('diagnostic/README.md' if is_diag else 'README.md')
        prefix = '../' if is_diag else ''
        number = str(profile - 10) if profile >= 11 else 'Prior profile ' + str(profile)
        lines = [f'# {number}. {report.get("recipe", report.get("label", "Canopy study"))}: '
                 + ('diagnostic mGBA fixtures' if is_diag else 'actual generated mGBA contexts'), '',
                 ('**Explicit diagnostic rooms, not natural generation.**' if is_diag else
                  'Generated terrain with disclosed player/navigation/inventory fixtures. Source art is reviewed separately.'), '',
                 '[Complete capture report](' + prefix + 'capture.json)', '',
                 f'{len(cases)} contexts in this index; {report["passed"]}/{report["total"]} total capture checks.', '']
        for case in cases:
            lines += [f'## {case["name"]}', '',
                      f'Seed {case.get("seed")} · room {case.get("cell")} · {case.get("note", "")}', '',
                      f'![Actual native framebuffer]({prefix}{case["image"]})', '']
            links = []
            for key, title in (('after_image', 'After'), ('filmstrip', 'Native filmstrip'), ('video', 'Full-rate MP4'), ('gif', 'Exact-palette GIF')):
                if case.get(key): links.append(f'[{title}]({prefix}{case[key]})')
            for frame in case_frames(case):
                links.append(f'[{frame["label"]}]({prefix}{frame["path"]})')
            lines += [' · '.join(links), '']
        lines += ['Native PNGs retain actual 240×160 pixels. MP4s are lossy viewing copies. '
                  'Only exact-color GIFs are included. Raw all-frame recording archives remain local.']
        if any('cape' in case['name'] for case in cases):
            lines += ['', '“Least visible body” measures the body bitmap alone. The native cape may legitimately cover it. '
                      '“Least visible displayed character” instead measures the exact native Bloom/cape composite; these are '
                      'different frame selections and must not be confused with complete canopy occlusion. The capture report '
                      'records both measurements and the cape’s source/palette/anchor proof.']
        markdown(path, lines)
    return report, {'profile': profile, 'local_variant': profile - 10 if profile >= 11 else None,
                    'role': 'new study' if profile >= 11 else 'separate previous-forest control',
                    'contexts': len(report['captures']),
                    'natural_contexts': sum(not diagnostic(c) for c in report['captures']),
                    'diagnostic_contexts': sum(diagnostic(c) for c in report['captures']),
                    'movies': sum(bool(c.get('video')) for c in report['captures']),
                    'exact_gifs': sum(bool(c.get('gif')) for c in report['captures']),
                    'checks': {'passed': report['passed'], 'total': report['total']}, 'files': len(files),
                    'rom_sha256': report['rom_sha256']}


def actual_board(out, reports, selections, name, title):
    new_reports = [(p, r) for p, r in sorted(reports.items()) if p >= 11]
    width, height = 240 * len(selections), 54 + 190 * len(new_reports)
    board = Image.new('RGB', (width, height), BG); draw = ImageDraw.Draw(board)
    G.label(draw, (5, 3), title)
    G.label(draw, (5, 22), 'ACTUAL mGBA / literal240×160 panels. Captions are outside game pixels.', DIM)
    panels = []
    for row, (profile, report) in enumerate(new_reports):
        for col, selection in enumerate(selections):
            case_name, selector, label = selection[:3]
            source_profile = selection[3] if len(selection) > 3 else profile
            source_report = reports[source_profile]
            case = next(c for c in source_report['captures'] if c['name'] == case_name)
            if selector == 'image':
                relative = case['image']
            else:
                frames = case_frames(case)
                frame = next(f for f in frames if f['label'].lower() == selector.lower())
                relative = frame['path']
            source = capture_destination(out, source_profile) / relative
            image = Image.open(source).convert('RGB'); assert image.size == (240, 160)
            x, y = col * 240, 54 + row * 190
            caption = f'{profile - 10}. {report.get("recipe", report.get("label", "Canopy"))}'
            if source_profile < 11:
                caption = f'Previous forest study {source_profile}'
            G.label(draw, (x + 3, y), caption)
            G.label(draw, (x + 3, y + 14), label, DIM)
            board.paste(image, (x, y + 30))
            panels.append({'profile': source_profile, 'row_new_profile': profile, 'case': case_name, 'selector': selector,
                           'kind': 'diagnostic' if diagnostic(case) else 'generated',
                           'source': str(source.relative_to(out)), 'source_sha256': sha(source),
                           'rgb_sha256': hashlib.sha256(image.tobytes()).hexdigest(),
                           'rect': [x, y + 30, 240, 160]})
    path = out / name; board.save(path)
    check = Image.open(path).convert('RGB')
    for panel in panels:
        x, y, w, h = panel['rect']
        expected = Image.open(out / panel['source']).convert('RGB')
        assert check.crop((x, y, x + w, y + h)).tobytes() == expected.tobytes()
    return {'path': name, 'sha256': sha(path), 'panels': panels}


def grid_actual_board(out, reports, case_name, name, title):
    """Eight literal screens in4columns; no filtered or thumbnail reduction."""
    assert case_name in ('healthy-canopy', 'deep-blight')
    new_reports = [(p, r) for p, r in sorted(reports.items()) if p >= 11]
    cols, cw, ch = 4, 240, 190
    board = Image.new('RGB', (cols * cw, 54 + ch * math.ceil(len(new_reports) / cols)), BG)
    draw = ImageDraw.Draw(board)
    G.label(draw, (5, 3), title)
    G.label(draw, (5, 22), f'ACTUAL mGBA / {len(new_reports)} unchanged 240×160 framebuffers. Captions are outside game pixels.', DIM)
    panels = []
    for n, (profile, report) in enumerate(new_reports):
        case = next(c for c in report['captures'] if c['name'] == case_name)
        assert not diagnostic(case), 'Compact forest grids require naturally generated contexts'
        source = capture_destination(out, profile) / case['image']
        image = Image.open(source).convert('RGB'); assert image.size == (240, 160)
        x, y = n % cols * cw, 54 + n // cols * ch
        G.label(draw, (x + 3, y), f'{profile - 10}. {report.get("recipe", report.get("label", "Canopy"))}')
        G.label(draw, (x + 3, y + 14), 'Generated healthy forest' if case_name == 'healthy-canopy' else 'Generated deep forest', DIM)
        board.paste(image, (x, y + 30))
        panels.append({'profile': profile, 'case': case_name, 'selector': 'image', 'kind': 'generated',
                       'source': str(source.relative_to(out)), 'source_sha256': sha(source),
                       'rgb_sha256': hashlib.sha256(image.tobytes()).hexdigest(),
                       'rect': [x, y + 30, 240, 160]})
    path = out / name; board.save(path); check = Image.open(path).convert('RGB')
    for panel in panels:
        x, y, w, h = panel['rect']
        expected = Image.open(out / panel['source']).convert('RGB')
        assert check.crop((x, y, x + w, y + h)).tobytes() == expected.tobytes()
    return {'path': name, 'sha256': sha(path), 'layout': 'four-column native-frame grid', 'panels': panels}


def actual_main(args):
    out, work = args.out.resolve(), args.work.resolve()
    out.mkdir(parents=True, exist_ok=True)
    reports, summaries = {}, []
    for profile in args.profiles:
        report, summary = copy_capture(work, out, profile, args.final)
        reports[profile] = report; summaries.append(summary)
    common = set.intersection(*[{c['name'] for c in report['captures']} for report in reports.values()])
    control_summary = None
    if args.control_profile is not None:
        report, control_summary = copy_capture(work, out, args.control_profile, args.final)
        reports[args.control_profile] = report
    boards = []
    if args.board_plan:
        plans = json.loads(args.board_plan.read_text())
    else:
        plans = []
        landscape = ('healthy-canopy', 'mixed-forest', 'deep-blight')
        if set(landscape) <= common:
            plans.append({'name': 'healthy-mixed-deep-actual.png', 'title': 'Eight canopy studies: generated healthy/mixed/deep',
                          'selections': [[name, 'image', title] for name, title in zip(landscape, ('Healthy', 'Mixed', 'Deep'))]})
        for case, name, title in (
                ('deep-blight', 'eight-deep-canopies-actual.png', 'Eight infected canopy treatments / matched generated deep forest'),
                ('healthy-canopy', 'eight-healthy-canopies-actual.png', 'Eight leafy canopy studies / matched generated healthy forest')):
            if case in common:
                plans.append({'name': name, 'title': title, 'grid_case': case})
        for case in sorted(common):
            candidates = [next(c for c in report['captures'] if c['name'] == case) for p, report in reports.items() if p >= 11]
            labels = {f['label'].lower() for c in candidates for f in c.get('phase_keyframes', [])}
            if {'before', 'under', 'emerged'} <= labels:
                plans.append({'name': case + '-actual.png', 'title': case + ': real Before/Under/Emerged',
                              'selections': [[case, label, label] for label in ('Before', 'Under', 'Emerged')]})
        for kind in ('living', 'sick'):
            names = [kind + '-actions-' + facing for facing in ('n', 'e', 's', 'w')]
            if set(names) <= common:
                plans.append({'name': kind + '-least-visible-actions-actual.png',
                              'title': kind + ' canopy: actual least-visible body in four sword/shield views',
                              'selections': [[name, 'Least visible body', facing] for name, facing in zip(names, ('North', 'East', 'South', 'West'))]})
        diagnostic_names = ['diagnostic-' + kind + '-' + shape for kind in ('living-canopy', 'sick-canopy')
                            for shape in ('isolated-sizes', 'narrow-inner-corners')]
        if set(diagnostic_names) <= common:
            plans.append({'name': 'diagnostic-canopy-shapes-actual.png',
                          'title': 'DIAGNOSTIC mGBA canopy shapes / explicit fixtures, not natural generation',
                          'selections': [[name, 'image', name.removeprefix('diagnostic-')] for name in diagnostic_names]})
        if 'deep-blight' in common:
            plans.append({'name': 'four-glow-phases-actual.png', 'title': 'Four actual authored BG glow phases',
                          'selections': [['deep-blight', 'Glow phase ' + str(n), 'Phase ' + str(n)] for n in range(4)]})
        if 'sick-canopy-menu-resume' in common:
            plans.append({'name': 'menu-palette-resume-actual.png', 'title': 'Actual menu open/close and world-palette restoration',
                          'selections': [['sick-canopy-menu-resume', label, label] for label in ('Before menu', 'Menu open', 'After resume')]})
        if args.control_profile is not None:
            for stage, case in (('healthy', 'healthy-canopy'), ('deep', 'deep-blight')):
                if case in common:
                    plans.append({'name': 'prior-and-new-' + stage + '-actual.png',
                                  'title': 'Previous vs new canopy / matched real generated ' + stage + ' forest',
                                  'selections': [[case, 'image', 'Previous canopy', args.control_profile],
                                                 [case, 'image', 'New canopy']]})
            for kind in ('living', 'sick'):
                case = kind + '-cape-under-canopy'
                if case in common:
                    plans.append({'name': 'prior-and-new-' + kind + '-cape-visibility-actual.png',
                                  'title': kind + ' canopy: matched flight and least-visible native Bloom/cape composite',
                                  'selections': [[case, 'Cape flight', 'Previous flight', args.control_profile],
                                                 [case, 'Cape flight', 'New flight'],
                                                 [case, 'Least visible displayed character', 'Previous character minimum', args.control_profile],
                                                 [case, 'Least visible displayed character', 'New character minimum']]})
    for plan in plans:
        if plan.get('grid_case'):
            boards.append(grid_actual_board(out, reports, plan['grid_case'], plan['name'], plan['title']))
        else:
            boards.append(actual_board(out, reports, plan['selections'], plan['name'], plan['title']))
    assert boards, 'No actual comparison board was selected; pass --board-plan explicitly.'
    write(out / 'actual-panel-manifest.json', {'boards': boards,
          'method': 'Every comparison rectangle independently decoded and compared byte-for-byte with its linked native mGBA framebuffer.'})
    markdown(out / 'actual/README.md', ['# Actual mGBA canopy studies', '',
        'Generated contexts and deliberate diagnostic rooms have separate indexes. Native framebuffers are retained exactly. '
        'Source diagrams and historical frames do not inflate these counts.', '',
        *[f'- [Option {s["local_variant"]}](variant-{s["local_variant"]:02}/README.md): '
          f'{s["natural_contexts"]} generated contexts +{s["diagnostic_contexts"]} '
          f'[diagnostic fixtures](variant-{s["local_variant"]:02}/diagnostic/README.md).' for s in summaries], '',
        *([f'[Separate previous forest profile {args.control_profile}](control-v{args.control_profile}/README.md)']
          if args.control_profile is not None else [])])
    assert sha(__file__) == LOADED_TOOL_SHA256, 'Gallery tool changed during actual copy'
    all_summaries = summaries + ([control_summary] if control_summary else [])
    write(out / 'actual-publication-summary.json', {'styles': summaries, 'boards': len(boards),
          'panels': sum(len(b['panels']) for b in boards), 'separate_control': control_summary,
          'publication_tool_sha256': LOADED_TOOL_SHA256,
          'new_contexts': sum(s['contexts'] for s in summaries),
          'new_natural_contexts': sum(s['natural_contexts'] for s in summaries),
          'new_diagnostic_contexts': sum(s['diagnostic_contexts'] for s in summaries),
          'all_contexts': sum(s['contexts'] for s in all_summaries),
          'all_movies': sum(s['movies'] for s in all_summaries),
          'all_exact_gifs': sum(s['exact_gifs'] for s in all_summaries),
          'all_capture_checks': {'passed': sum(s['checks']['passed'] for s in all_summaries),
                                 'total': sum(s['checks']['total'] for s in all_summaries)},
          'source_commits': sorted({r['source_commit'] for r in reports.values()})})
    print(json.dumps({'styles': len(summaries), 'boards': len(boards), 'panels': sum(len(b['panels']) for b in boards)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('worker'); p.add_argument('--profile', type=int, required=True); p.add_argument('--snapshot', type=Path, required=True)
    p = sub.add_parser('source'); p.add_argument('--work', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--profiles', nargs='+', type=int, default=list(PROFILES)); p.add_argument('--hold', type=int, default=180); p.add_argument('--final', action='store_true')
    p = sub.add_parser('actual'); p.add_argument('--work', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--profiles', nargs='+', type=int, default=list(PROFILES)); p.add_argument('--board-plan', type=Path); p.add_argument('--final', action='store_true')
    p.add_argument('--control-profile', type=int, choices=[6])
    args = parser.parse_args()
    if args.mode == 'worker':
        worker(args)
    elif args.mode == 'source':
        assert set(args.profiles) <= set(PROFILES); source_main(args)
    else:
        assert set(args.profiles) <= set(PROFILES); actual_main(args)


if __name__ == '__main__':
    main()
