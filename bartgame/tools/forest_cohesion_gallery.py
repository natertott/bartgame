#!/usr/bin/env python3
"""Publish literal native forest room comparisons without retouching game pixels."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from PIL import Image, ImageDraw, ImageFont
import forest_trees_gallery as G

ROOT = Path(__file__).resolve().parents[1]
LOADED_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
BG, FG, DIM = '#101820', '#f0d898', '#b0c0a0'
FONT = ImageFont.load_default()
sha, rgb_sha, safe_path, exact_copy = G.sha, G.rgb_sha, G.safe_path, G.exact_copy
SOURCE_NAMES = (
    'moss0', 'moss1', 'moss2', 'moss_shade', 'moss_blight', 'moss_blight2',
    'blight_floor', 'blight_floor2', 'blight_vein', 'moss_flowers', 'moss_flowers2',
    'leaf_litter', 'tall_grass', 'fern_patch', 'meadow_4', 'clover_0', 'shroomring_0',
    'path', 'path_edge_n', 'pedge_1', 'pedge_3', 'pedge_c1', 'rot_10', 'rot_14',
    'water', 'water_1', 'water_3', 'water_f', 'water_c1', 'water_lily', 'water_foam',
    'waterfall', 'bridge', 'bridge_v', 'ledge_s', 'ledge_s_w', 'ledge_s_e', 'ledge_n',
    'pit', 'pit_inner', 'forest_blight_pit', 'blight_pool',
    'rock', 'rock2', 'rock3', 'mossy_stone', 'sick_rock', 'bones', 'sick_bones',
    'stump', 'sick_stump', 'hlog_0', 'hlog_1', 'fence', 'pillar', 'ruin_wall', 'statue',
    'thorn', 'crack', 'web', 'door_locked', 'door_open', 'myst_switch', 'myst_switch_down',
    'lantern_post', 'torch', 'torch_lit', 'shrine_plate', 'blight_crystal',
    'mouth_cave', 'mouth_hollow', 'mouth_thicket', 'stairs_down', 'chest', 'chest_open',
    'bush', 'rock_small', 'boulder', 'myst_pot',
)


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2)+'\n')


def source_snapshot(variant):
    """Read each art configuration in a separate process, never mixed globals."""
    code = ('import json,palettes,tiles; print(json.dumps({'
            '"palettes":dict(palettes.BG_PALETTES),'
            '"metatiles":{m["name"]:m for m in tiles.METATILES},'
            '"coverage":tiles.COVERAGE}))')
    return json.loads(subprocess.check_output([sys.executable, '-c', code],
        cwd=ROOT/'art', env=dict(os.environ, BART_FOREST=str(variant)), text=True))


def display_color(color):
    """Show stored RGB555 with the same integer channel expansion as GBA."""
    levels = [int(color[k:k+2], 16) >> 3 for k in (1, 3, 5)]
    return tuple((value << 3) | (value >> 2) for value in levels)


def source_image(snapshot, name, phase=0):
    mt = snapshot['metatiles'][name]
    frames = mt.get('frames') or [mt['art']]
    rows = frames[phase % len(frames)]
    indexed = Image.new('P', (16, 16), 0)
    indices = bytes(0 if ch in '. ' else int(ch, 16) for row in rows for ch in row)
    assert len(indices) == 256 and max(indices) < 16
    indexed.frombytes(indices)
    colors = snapshot['palettes'][mt['pal']]
    assert len(colors) == 16
    indexed.putpalette([c for color in colors for c in display_color(color)] + [0]*720)
    indexed.info['transparency'] = 0
    rgba = indexed.convert('RGBA')
    # A few legacy metatiles have different banks per8px quarter. Preserve
    # their real source color assignments in the display preview.
    if mt.get('qpals'):
        for y in range(16):
            for x in range(16):
                bank = mt['qpals'][(y//8)*2+x//8]
                ink = indices[y*16+x]
                rgba.putpixel((x, y), display_color(snapshot['palettes'][bank][ink]) + (255 if ink else 0,))
    return indexed, rgba, {'name': name, 'phase': phase, 'frames': len(frames),
        'bank': mt['pal'], 'quarter_banks': mt.get('qpals'),
        'index_sha256': hashlib.sha256(indices).hexdigest(),
        'RGBA_sha256': hashlib.sha256(rgba.tobytes()).hexdigest()}


def source_catalog(out, bundle, frozen):
    """Source-only native previews; never represented as emulator images."""
    freeze_path = bundle/'freeze.json'
    freeze = json.loads(freeze_path.read_text()) if freeze_path.exists() else {}
    if frozen:
        for name, expected in freeze['source_file_sha256'].items():
            assert sha(ROOT/name) == expected, ('Source art changed after freeze', name)
    before, after = source_snapshot(31), source_snapshot(32)
    names = [name for name in SOURCE_NAMES if name in before['metatiles'] and name in after['metatiles']]
    missing = sorted(set(SOURCE_NAMES)-set(names))
    folder = out/'source'
    folder.mkdir(parents=True, exist_ok=True)
    cards, records = [], []
    for name in names:
        old_indexed, old, old_record = source_image(before, name)
        new_indexed, new, new_record = source_image(after, name)
        for variant, indexed, rgba, record in ((31, old_indexed, old, old_record), (32, new_indexed, new, new_record)):
            path = folder/'native'/str(variant)/(name+'.png')
            path.parent.mkdir(parents=True, exist_ok=True)
            indexed.save(path, transparency=0)
            record['indexed_PNG'] = str(path.relative_to(out))
            record['PNG_sha256'] = sha(path)
        previews = []
        for snapshot, art, ground in ((before, old, 'moss0'), (after, new, 'moss0'),
                                      (after, new, 'path'), (after, new, 'blight_floor')):
            _, floor, _ = source_image(snapshot, ground)
            floor.alpha_composite(art)
            previews.append(floor.convert('RGB'))
        cards.append((name, previews))
        records.append({'name': name, 'before': old_record, 'after': new_record,
                        'display_pixels_changed': old.tobytes() != new.tobytes()})
    columns, cw, ch, header = 4, 176, 76, 55
    image = Image.new('RGB', (columns*cw+8, header+((len(cards)+columns-1)//columns)*ch), BG)
    draw = ImageDraw.Draw(image)
    caption(draw, (8, 6), 'SOURCE ART ONLY / native16px material and prop review')
    caption(draw, (8, 23), 'Each card: previous grass | new grass | new soil | new sick floor. Displayed2x nearest.', DIM)
    panels = []
    for i, (name, previews) in enumerate(cards):
        x, y = 8+(i%columns)*cw, header+(i//columns)*ch
        caption(draw, (x, y), name)
        for n, preview in enumerate(previews):
            rect = [x+n*40, y+20, x+n*40+32, y+52]
            image.paste(preview.resize((32, 32), Image.Resampling.NEAREST), rect[:2])
            panels.append({'name': name, 'context': n, 'rectangle': rect,
                           'native_RGB_sha256': rgb_sha(preview), 'scale': 2})
    path = folder/'materials-source.png'
    image.save(path)
    reopened = Image.open(path).convert('RGB')
    for panel, (_, previews) in zip(panels, (card for card in cards for _ in range(4))):
        expected = previews[panel['context']].resize((32, 32), Image.Resampling.NEAREST)
        assert reopened.crop(panel['rectangle']).tobytes() == expected.tobytes()
    palette_names = sorted({r['after']['bank'] for r in records})
    palette_records = []
    for name in palette_names:
        colors = after['palettes'][name]
        assert all(int(color[k:k+2], 16)%8 == 0 for color in colors for k in (1, 3, 5)), name
        palette_records.append({'bank': name, 'RGB555_author_colors': colors})
    groups = source_groups(folder, before, after)
    dump(folder/'source-manifest.json', {'kind': 'Native source drawings and local-floor previews; not emulator images.',
        'source_commit': freeze.get('source_commit'), 'gallery_tool_sha256': LOADED_SHA,
        'records': records, 'missing_names': missing, 'palette_banks': palette_records, 'complete_groups': groups,
        'board': {'file': str(path.relative_to(out)), 'sha256': sha(path), 'panels': panels},
        'phase_note': 'The board shows phase0; actual water-motion captures verify animated play. Indexed PNGs preserve original16-color indices and binary alpha.'})
    (folder/'README.md').write_text('# Native forest material source review\n\n'
        '![Source material and object comparison](materials-source.png)\n\n'
        'These are native16×16 source drawings, displayed at integer2× for inspection. '
        'Each card compares previous art on its original grass with the new drawing on new grass, soil and sick grass. '
        'The backgrounds are native source swatches, not captured room screens. Exterior index0 exposes the local source floor.\n\n'
        '![Complete native multi-cell source groups](groups-source.png)\n\n'
        'The second board assembles complete meadow, clover, fungi and log source pieces at their authored native dimensions. '
        'It is a source join/scale inspection, not a generated room or GBA framebuffer.\n\n'
        'The board shows phase0 of animated families. Current chests, entries, carry objects, Bloom and the approved tree kit may remain exact where already clear; '
        'the manifest records each representative asset and whether its effective source pixels changed.\n\n'
        '[Indexed native PNGs and palette contract](source-manifest.json) · [Actual mGBA rooms](../README.md)\n')
    return {'file': 'source/materials-source.png', 'assets': len(records),
        'changed_assets': sum(r['display_pixels_changed'] for r in records), 'missing_names': missing,
        'manifest_sha256': sha(folder/'source-manifest.json')}


def source_groups(folder, before, after):
    """Assemble authored multi-cell groups literally, with source-only labels."""
    specifications = [('Meadow', 'meadow_', 3, 3), ('Clover', 'clover_', 2, 2),
                      ('Mushrooms', 'shroomring_', 2, 2), ('Fallen log', 'hlog_', 2, 1)]
    image = Image.new('RGB', (440, 65+len(specifications)*150), BG)
    draw = ImageDraw.Draw(image)
    caption(draw, (8, 7), 'SOURCE GROUPS ONLY / previous31 and new32 native drawings')
    caption(draw, (8, 25), 'Complete multi-cell pieces.2x nearest inspection; not emulator screenshots.', DIM)
    panels = []
    for number, (name, prefix, cols, rows) in enumerate(specifications):
        y = 60+number*150
        caption(draw, (8, y), name+f' / {cols*16}x{rows*16}px')
        for variant, snapshot, x in ((31, before, 8), (32, after, 220)):
            group = Image.new('RGBA', (cols*16, rows*16), (0, 0, 0, 0))
            source_files = []
            for cy in range(rows):
                for cx in range(cols):
                    _, floor, _ = source_image(snapshot, 'moss0')
                    _, art, _ = source_image(snapshot, prefix+str(cy*cols+cx))
                    floor.alpha_composite(art)
                    group.alpha_composite(floor, (cx*16, cy*16))
                    source_files.append(prefix+str(cy*cols+cx))
            native = group.convert('RGB')
            native_path = folder/'groups'/f'{prefix.rstrip("_")}-{variant}.png'
            native_path.parent.mkdir(exist_ok=True)
            native.save(native_path)
            caption(draw, (x, y+17), 'Previous31' if variant == 31 else 'New32', DIM)
            rect = [x, y+35, x+native.width*2, y+35+native.height*2]
            image.paste(native.resize((native.width*2, native.height*2), Image.Resampling.NEAREST), rect[:2])
            panels.append({'name': name, 'variant': variant, 'source_tiles': source_files,
                'file': str(native_path.relative_to(folder.parent)), 'native_size': list(native.size),
                'native_RGB_sha256': rgb_sha(native), 'rectangle': rect, 'scale': 2})
    path = folder/'groups-source.png'
    image.save(path)
    reopened = Image.open(path).convert('RGB')
    for record in panels:
        native = Image.open(folder.parent/record['file']).convert('RGB')
        expected = native.resize((native.width*2, native.height*2), Image.Resampling.NEAREST)
        assert reopened.crop(record['rectangle']).tobytes() == expected.tobytes()
    return {'file': str(path.relative_to(folder.parent)), 'sha256': sha(path), 'panels': panels}


def caption(draw, point, value, color=FG):
    draw.fontmode = '1'
    draw.text(point, value, font=FONT, fill=color)


def tagged(row, tag):
    result = copy.deepcopy(row)
    for key in ('panorama', 'native_HUD', 'native_arrival'):
        if result.get(key):
            result[key]['file'] = tag+'/'+result[key]['file']
    for view in result.get('normal_facing_views', []):
        view['file'] = tag+'/'+view['file']
    return result


def copy_report(path, out, tag, final):
    path = path.resolve()
    base = path.parent
    data = json.loads(path.read_text())
    if final:
        assert data['pass'] and data.get('complete') is True and data['source_freeze'].get('source_commit')
        bundle = Path(data['bundle'])
        assert data['source_freeze']['rom_sha256'] == sha(bundle/'bartgame.gba')
        assert data['source_freeze'].get('variant', data['source_freeze'].get('forest_variant')) == data['forest_variant']
        assert all(sha(bundle/name) == value for name, value in data['bundle_sha256'].items())
        assert data['capture_tool_sha256'] == sha(ROOT/'tools/forest_cohesion_review.py')
        for name, expected in data['capture_dependency_sha256'].items():
            assert sha(ROOT/'tools'/name) == expected
    files = set()
    for row in data['captures']:
        G.verify_panorama(base, row['panorama'])
        for name in ('native_HUD', 'native_arrival'):
            if row.get(name):
                G.image_record(base, row[name], (240, 160))
        for record in row.get('normal_facing_views', []):
            G.image_record(base, record, (240, 160))
        files |= G.declared_paths(row, base)
        if row.get('water_motion'):
            files.update(row['water_motion'][key] for key in ('movie', 'gif', 'observations') if row['water_motion'].get(key))
    for relative in sorted(files):
        exact_copy(safe_path(base, relative), out/'actual'/tag/relative)
    exact_copy(path, out/'actual'/tag/'capture.json')
    if data.get('census_file'):
        exact_copy(safe_path(base, data['census_file']), out/'actual'/tag/data['census_file'])
    return data, [tagged(row, tag) for row in data['captures']], files


def make_board(out, filename, rows, columns=3, hud=False, scale=1, frozen=False):
    w, h = (240, 160) if hud else (512, 384)
    columns = min(columns, len(rows))
    gap, header, card = 8, 48, 36
    cw, ch = w*scale+gap, h*scale+card+gap
    image = Image.new('RGB', (columns*cw+gap, header+((len(rows)+columns-1)//columns)*ch), BG)
    draw = ImageDraw.Draw(image)
    caption(draw, (8, 7), ('FROZEN / ' if frozen else 'PILOT / ')+'FOREST / actual mGBA composition pass')
    caption(draw, (8, 24), 'Untouched native HUD views' if hud else '512x384 registered native-camera mosaics; held clock, HUD hidden', DIM)
    panels = []
    for index, row in enumerate(rows):
        x, y = gap+(index%columns)*cw, header+(index//columns)*ch
        rel = 'actual/'+row['native_HUD' if hud else 'panorama']['file']
        source = Image.open(out/rel).convert('RGB')
        assert source.size == (w, h)
        shown = source.resize((w*scale, h*scale), Image.Resampling.NEAREST)
        caption(draw, (x, y), row.get('caption', row['name'].replace('-', ' ')))
        caption(draw, (x, y+16), f'Seed {row["seed"]} / cell {row["cell"]} / stage {row["stage"]}', DIM)
        rect = [x, y+card, x+shown.width, y+card+shown.height]
        image.paste(shown, rect[:2])
        panels.append({'case': row['name'], 'source': rel, 'native_size': [w, h], 'scale': scale,
                       'source_sha256': sha(out/rel), 'rectangle': rect, 'source_RGB_sha256': rgb_sha(source)})
    path = out/filename
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    actual = Image.open(path).convert('RGB')
    for p in panels:
        source = Image.open(out/p['source']).convert('RGB')
        enlarged = source.resize((source.width*p['scale'], source.height*p['scale']), Image.Resampling.NEAREST)
        assert actual.crop(p['rectangle']).tobytes() == enlarged.tobytes()
    return {'file': filename, 'size': list(image.size), 'sha256': sha(path), 'panels': panels, 'frozen': frozen}


def release(bundle, folder, source, out):
    folder.mkdir(parents=True, exist_ok=True)
    stem = 'forest-room-cohesion-'+source[:7]
    rom, archive = stem+'.gba', stem+'.zip'
    exact_copy(bundle/'bartgame.gba', folder/rom)
    text = '\n'.join(['BARTGAME / Forest composition and native art refinement', '',
                     'Playable GBA ROM. Open the .gba file in mGBA.',
                     'Normal gameplay uses profile32 forest room generation and artwork.',
                     'The approved compact tree pictures remain unchanged.', '',
                     'Game/art source: '+source, 'ROM SHA256: '+sha(folder/rom), '',
                     'D-pad move; A/B/L equipped actions; R lift/roll; START menu.',
                     'Use the Drain ladder to enter the forest.',
                     'Review camera fixtures are inactive during ordinary gameplay.', ''])
    (folder/'README.txt').write_text(text)
    (folder/'SHA256SUMS.txt').write_text(''.join(sha(folder/name)+'  '+name+'\n' for name in (rom, 'README.txt')))
    with zipfile.ZipFile(folder/archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in (rom, 'README.txt', 'SHA256SUMS.txt'):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, (folder/name).read_bytes())
    with zipfile.ZipFile(folder/archive) as z:
        assert z.read(rom) == (bundle/'bartgame.gba').read_bytes() and z.testzip() is None
    review = Path(os.path.relpath(out, folder)).as_posix()+'/README.md'
    (folder/'README.md').write_text(f'# Forest room cohesion build\n\n[Playable ROM]({rom}) · [ZIP]({archive}) · [Checksums](SHA256SUMS.txt) · [Actual room review]({review})\n\nSource: `{source}`. ROM SHA256: `{sha(folder/rom)}`.\n')
    return {'folder': folder.name, 'rom': rom, 'zip': archive, 'rom_sha256': sha(folder/rom),
            'zip_sha256': sha(folder/archive), 'rom_bytes': (folder/rom).stat().st_size,
            'zip_bytes': (folder/archive).stat().st_size}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--baseline-report', '--before', dest='baseline_report', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--final', action='store_true')
    p.add_argument('--download-dir', type=Path)
    p.add_argument('--source-catalog', action='store_true', help='Publish separate native material/prop source comparisons')
    args = p.parse_args()
    if args.download_dir and not args.final:
        raise ValueError('Playable release requires a frozen final report')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report, rows, media = copy_report(args.report, out, 'after', args.final)
    assert report['forest_variant'] == 32 and rows
    if args.final:
        assert {'healthy', 'mixed', 'deep'} <= {row['name'] for row in rows}
    boards = [make_board(out, 'rooms-actual.png', rows, frozen=args.final),
              make_board(out, 'native-HUD-actual.png', rows, hud=True, frozen=args.final)]
    before, before_rows, before_media = (None, [], set())
    if args.baseline_report:
        before, before_rows, before_media = copy_report(args.baseline_report, out, 'before', args.final)
        assert before['forest_variant'] == 31
        matched = []
        for row in rows:
            prior = next((r for r in before_rows if int(r['seed'], 0) == int(row['seed'], 0) and r['cell'] == row['cell']), None)
            if prior:
                prior = copy.deepcopy(prior)
                current = copy.deepcopy(row)
                prior['caption'], current['caption'] = 'Previous31 / '+row['name'], 'New32 / '+row['name']
                matched.extend((prior, current))
            elif args.final:
                raise ValueError('Final comparison lacks a matched baseline cell: '+row['name'])
        if matched:
            boards.append(make_board(out, 'before-after.png', matched, columns=2, frozen=args.final))
    for row in rows:
        boards.append(make_board(out, 'inspection/'+row['name']+'-2x.png', [row], columns=1, scale=2, frozen=args.final))
    source = report['source_freeze'].get('source_commit')
    catalog = source_catalog(out, Path(report['bundle']), args.final) if args.source_catalog else None
    rel = release(Path(report['bundle']), args.download_dir.resolve(), source, out) if args.download_dir else None
    title = '# Forest room composition and art refinement\n\n'
    lines = [title.rstrip(), '', 'The forest is composed around natural room features, then dressed with contextual details. The approved tree silhouettes retain their native source pixels.', '',
             '![Actual generated forest rooms](rooms-actual.png)', '',
             'Each512×384 room is a registered mosaic of nine untouched240×160 mGBA camera views. The review camera holds time and hides the HUD; no terrain or screenshot pixels are injected.', '']
    if not args.final:
        lines[2:2] = ['**Unfrozen pilot:** implementation-review images; these do not qualify a playable release.', '']
    if before_rows:
        lines += ['![Matched previous and new forest rooms](before-after.png)', '',
                  'The comparison uses the same seeded cells in the old31 and new32 ROMs. Room geometry intentionally changes; both sides are real native-camera captures.', '']
    if catalog:
        lines += ['[Inspect native material and object source art](source/README.md) · '
                  '[Source/palette manifest](source/source-manifest.json)', '',
                  'Source-only contact studies are separate from emulator captures. They show native16px drawings on source grass, soil and sick grass, '
                  'including material transitions, vegetation, water, crossings, debris, stonework and interactions.', '']
    lines += ['![Native HUD views](native-HUD-actual.png)', '',
              '| Room | Native room mosaic | 2× inspection | Motion |', '| --- | --- | --- | --- |']
    for row in rows:
        name = row['name']
        motion = []
        for key, label in (('walk', 'Walk'), ('water_motion', 'Water')):
            if row.get(key):
                motion.append(f'[{label} MP4](actual/after/{row[key]["movie"]})')
        lines.append(f'| {name} / {row["seed"]} / cell{row["cell"]} | [PNG](actual/{row["panorama"]["file"]}) | [PNG](inspection/{name}-2x.png) | '+(' · '.join(motion) if motion else '—')+' |')
    if rel:
        target = Path(os.path.relpath(args.download_dir.resolve(), out)).as_posix()
        lines += ['', f'[Playable ROM]({target}/{rel["rom"]}) · [ZIP]({target}/{rel["zip"]}) · [Checksums]({target}/SHA256SUMS.txt)']
    lines += ['', 'Native HUD and arrival images remain untouched framebuffers. The review seeds the real game and uses native selected-cell transitions. '
              'Viewing fixtures isolate enemies/projectiles/effects, restore health and establish an initial safe standing point/facing. '
              'The natural-arrival image precedes that viewing setup. These are inspection fixtures, not an unassisted playthrough. '
              'During recorded movement, the harness sends ordinary directional buttons chosen from the actual traversable grid; it records each requested/actual key and does not teleport Bloom. '
              'Water clips use normal game simulation after the same setup, with no held camera or animation clock.', '',
              'Ambient glitter can differ in overlapping viewports because of native culling; literal crop seams remain unpainted. MP4s preserve every recorded native video frame at approximately59.73Hz. GIFs, when present, are sampled exact-color inspection copies.', '',
              f'Capture checks: {sum(c["passed"] for c in report["checks"])}/{len(report["checks"])}. Literal missed-update intervals are reported per room, with no frame-perfect claim.', '',
              '[Capture report](actual/after/capture.json) · [Literal panel proof](actual-panel-manifest.json) · [Publication summary](actual-publication-summary.json)', '']
    (out/'README.md').write_text('\n'.join(lines).rstrip()+'\n')
    summary = {'source_commit': source, 'forest_variant': 32, 'rom_sha256': report['source_freeze'].get('rom_sha256'),
               'gallery_tool_sha256': LOADED_SHA, 'gallery_dependency_sha256': {'forest_trees_gallery.py': sha(Path(G.__file__))},
               'capture_report_sha256': sha(args.report), 'baseline_report_sha256': sha(args.baseline_report) if args.baseline_report else None,
               'rooms': len(rows), 'native_camera_frames': sum(len(r['panorama']['views']) for r in rows),
               'copied_media': len(media)+len(before_media), 'boards': len(boards), 'release': rel,
               'source_catalog': catalog, 'frozen': args.final}
    dump(out/'actual-panel-manifest.json', {'source_commit': source, 'forest_variant': 32, 'boards': boards})
    dump(out/'actual-publication-summary.json', summary)
    assert sha(__file__) == LOADED_SHA, 'Gallery helper changed during publication'
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
