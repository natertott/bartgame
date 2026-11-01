#!/usr/bin/env python3
"""Publish literal mGBA room mosaics and their native source frames.

Only captions, borders, literal copies and integer nearest-neighbour inspection
enlargements are created here. Game pixels remain those in the capture report.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import zipfile

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 31
LOADED_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
BG, FG, DIM = '#101820', '#f0d898', '#b0c0a0'
FONT = ImageFont.load_default()
TITLES = {'healthy': 'Healthy forest', 'mixed': 'Sick woodland',
          'deep': 'Deep blight', 'boss': 'The Heart'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rgb_sha(image):
    return hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def markdown(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n')


def label(draw, xy, text, color=FG):
    draw.fontmode = '1'
    draw.text(xy, text, font=FONT, fill=color)


def safe_path(base, relative):
    result = (base / relative).resolve()
    if not result.is_relative_to(base):
        raise ValueError('Capture path escapes report folder: ' + str(relative))
    return result


def exact_copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != target.resolve():
        shutil.copyfile(source, target)
    assert sha(source) == sha(target), ('Copied bytes changed', source)


def image_record(base, record, expected_size=None):
    path = safe_path(base, record['file'])
    if record.get('png_sha256'):
        assert sha(path) == record['png_sha256'], ('Native PNG changed', path)
    image = Image.open(path).convert('RGB')
    if expected_size is not None:
        assert image.size == expected_size, (path, image.size)
    if record.get('RGB_sha256'):
        assert rgb_sha(image) == record['RGB_sha256'], ('Native pixels changed', path)
    return image


def verify_panorama(base, panorama):
    image = image_record(base, panorama, (512, 384))
    coverage = bytearray(image.width * image.height)
    assert len(panorama['views']) == 9
    for view in panorama['views']:
        native = image_record(base, view, (240, 160))
        crop = native.crop(view['source_crop'])
        assert rgb_sha(crop) == view['crop_RGB_sha256']
        assert image.crop(view['world_crop']).tobytes() == crop.tobytes()
        x0, y0, x1, y1 = view['world_crop']
        assert x1 - x0 == crop.width and y1 - y0 == crop.height
        for y in range(y0, y1):
            for x in range(x0, x1):
                coverage[y*image.width+x] += 1
    assert all(n == 1 for n in coverage), 'Mosaic does not cover room exactly once'
    return image


def declared_paths(row, base):
    paths = {row['panorama']['file'], row['native_HUD']['file']}
    if row.get('native_arrival'):
        paths.add(row['native_arrival']['file'])
    paths.update(v['file'] for v in row['panorama']['views'])
    paths.update(v['file'] for v in row.get('normal_facing_views', []))
    if row.get('walk'):
        paths.update(row['walk'][key] for key in ('movie', 'gif', 'observations')
                     if row['walk'].get(key))
    # Readbacks are evidence, never rendered substitutes for actual frames.
    folder = safe_path(base, row['panorama']['file']).parent
    paths.update(str(p.relative_to(base)) for p in folder.glob('*.bin'))
    return paths


def board(out, filename, rows, panels_per_row=3, scale=1, native_hud=False, frozen=False):
    width, height = ((240, 160) if native_hud else (512, 384))
    columns = min(panels_per_row, len(rows))
    gap, card_header, header = 8, 36, 56
    cellw, cellh = width*scale+gap, height*scale+card_header+gap
    count_rows = (len(rows)+columns-1)//columns
    image = Image.new('RGB', (columns*cellw+gap, header+count_rows*cellh), BG)
    d = ImageDraw.Draw(image)
    title = 'ACTUAL mGBA / native HUD-on views' if native_hud else 'ACTUAL mGBA / complete generated rooms'
    label(d, (8, 7), ('FROZEN / ' if frozen else 'PILOT / ') + title)
    subtitle = ('Untouched 240x160 frames; captions are outside the game pixels.' if native_hud
                else '512x384 camera mosaics of nine native views; held clock, HUD hidden.')
    label(d, (8, 25), subtitle, DIM)
    panels = []
    for index, row in enumerate(rows):
        col, line = index % columns, index // columns
        x, y = gap+col*cellw, header+line*cellh
        source = 'actual/' + (row['native_HUD']['file'] if native_hud else row['panorama']['file'])
        native = Image.open(out/source).convert('RGB')
        assert native.size == (width, height)
        shown = native.resize((width*scale, height*scale), Image.Resampling.NEAREST)
        title = TITLES.get(row['name'], row['name'].replace('-', ' ').title())
        label(d, (x, y), title)
        label(d, (x, y+16), f'Seed {row["seed"]} / room {row["cell"]} / stage {row["stage"]}', DIM)
        rect = [x, y+card_header, shown.width, shown.height]
        image.paste(shown, rect[:2])
        panels.append({'case': row['name'], 'source': source, 'source_sha256': sha(out/source),
                       'native_size': [width, height], 'inspection_scale': scale, 'rect': rect,
                       'native_RGB_sha256': rgb_sha(native),
                       'kind': 'native HUD-on framebuffer' if native_hud else 'registered native-camera mosaic'})
    path = out/filename
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    check = Image.open(path).convert('RGB')
    for panel in panels:
        x, y, w, h = panel['rect']
        native = Image.open(out/panel['source']).convert('RGB')
        expected = native.resize((w, h), Image.Resampling.NEAREST)
        assert check.crop((x, y, x+w, y+h)).tobytes() == expected.tobytes()
    return {'file': filename, 'sha256': sha(path), 'size': list(image.size), 'panels': panels}


def release(bundle, folder, source, out):
    folder.mkdir(parents=True, exist_ok=True)
    stem = 'forest-trees-integrated-' + source[:7]
    rom_name, zip_name = stem+'.gba', stem+'.zip'
    exact_copy(bundle/'bartgame.gba', folder/rom_name)
    readme = [
        'BARTGAME / integrated repeated forest trees', '',
        'Playable GBA ROM. Open the .gba file in mGBA.',
        'The approved healthy/sick/dead 32x32 and 16x32 trees are integrated',
        'in the procedural forest. Profile31 is the normal build.', '',
        'Source commit: '+source,
        'ROM SHA256: '+sha(folder/rom_name), '',
        'Controls: D-pad move; A/B/L equipped actions; R lift/roll; START menu.',
        'Use the Drain ladder to enter the forest. No review camera is active',
        'during ordinary play.', '',
        'Room pictures in the review are labelled camera mosaics; the GBA',
        'itself displays 240x160. Captures are not extra gameplay screens.',
    ]
    (folder/'README.txt').write_text('\n'.join(readme)+'\n')
    checksums = ''.join(sha(folder/name)+'  '+name+'\n' for name in (rom_name, 'README.txt'))
    (folder/'SHA256SUMS.txt').write_text(checksums)
    with zipfile.ZipFile(folder/zip_name, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in (rom_name, 'README.txt', 'SHA256SUMS.txt'):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (folder/name).read_bytes())
    with zipfile.ZipFile(folder/zip_name) as archive:
        assert archive.read(rom_name) == (bundle/'bartgame.gba').read_bytes()
        assert archive.testzip() is None
    relative = Path(os.path.relpath(out, folder)).as_posix()
    markdown(folder/'README.md', ['# Integrated forest-tree build', '',
        f'[Playable ROM]({rom_name}) · [ZIP]({zip_name}) · [SHA256 checksums](SHA256SUMS.txt) · '
        f'[Actual room review]({relative}/README.md)', '',
        'Open the `.gba` file in mGBA. This is the normal playable game with the selected compact tree kit integrated into the procedural forest.', '',
        f'Source: `{source}`. ROM SHA256: `{sha(folder/rom_name)}`.', '',
        'The ZIP contains the same ROM bytes, a short usage note and checksums. Captured room mosaics are review evidence and are separate from the playable ROM.'])
    return {'folder': folder.name, 'rom': rom_name, 'zip': zip_name,
            'rom_sha256': sha(folder/rom_name), 'zip_sha256': sha(folder/zip_name),
            'rom_bytes': (folder/rom_name).stat().st_size, 'zip_bytes': (folder/zip_name).stat().st_size}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--final', action='store_true')
    p.add_argument('--download-dir', type=Path)
    args = p.parse_args()
    report_path = args.report.resolve(); base = report_path.parent
    report = json.loads(report_path.read_text()); out = args.out.resolve()
    assert report['forest_variant'] == PROFILE
    rows = report['captures']; assert rows
    assert len({row['name'] for row in rows}) == len(rows)
    if args.download_dir and not args.final:
        raise ValueError('A playable release requires --final and a frozen capture report')
    freeze = report['source_freeze']; source = freeze.get('source_commit')
    bundle = Path(report['bundle']).resolve()
    if args.final:
        assert report.get('pass') and report.get('complete', True)
        assert {'healthy', 'mixed', 'deep'} <= {row['name'] for row in rows}
        assert source and len(source) == 40 and not freeze.get('unfrozen_pilot')
        assert freeze['rom_sha256'] == sha(bundle/'bartgame.gba')
        for key, expected in report['bundle_sha256'].items():
            assert sha(bundle/key) == expected, ('Frozen bundle changed', key)
        assert report['capture_tool_sha256'] == sha(ROOT/'tools/forest_trees_review.py')
        for key, expected in report.get('capture_dependency_sha256', {}).items():
            assert sha(ROOT/'tools'/key) == expected, ('Capture dependency changed', key)
    out.mkdir(parents=True, exist_ok=True)
    all_paths = set()
    timing = report.get('timing_baseline')
    if timing:
        path = safe_path(base, timing['file'])
        assert sha(path) == timing['sha256']
        all_paths.add(timing['file'])
    for row in rows:
        verify_panorama(base, row['panorama'])
        image_record(base, row['native_HUD'], (240, 160))
        if row.get('native_arrival'):
            image_record(base, row['native_arrival'], (240, 160))
        for record in row.get('normal_facing_views', []):
            image_record(base, record, (240, 160))
        all_paths |= declared_paths(row, base)
    actual = out/'actual'
    for relative in sorted(all_paths):
        exact_copy(safe_path(base, relative), actual/relative)
    exact_copy(report_path, actual/'capture.json')
    boards = [board(out, 'rooms-actual.png', rows, frozen=args.final),
              board(out, 'native-HUD-actual.png', rows, native_hud=True, frozen=args.final)]
    for row in rows:
        boards.append(board(out, f'inspection/{row["name"]}-2x.png', [row], panels_per_row=1, scale=2, frozen=args.final))
    release_summary = release(bundle, args.download_dir.resolve(), source, out) if args.download_dir else None
    paths_link = (Path(os.path.relpath(args.download_dir.resolve(), out)).as_posix()
                  if args.download_dir else None)
    lines = ['# Forest trees integrated into the game', '']
    if not args.final:
        lines += ['**Unfrozen pilot:** these captures are for implementation review. They do not qualify a playable release.', '']
    lines += [
        'The approved compact trees now replace the forest’s previous tree/canopy pictures in the procedural rooms. '
        'The twelve native drawings retain their original pixels and shared sixteen-entry RGB555 palette.', '',
        '![Complete generated rooms, assembled from actual mGBA camera views](rooms-actual.png)', '',
        '**Complete rooms:** each 512×384 image is a registered mosaic of nine actual 240×160 mGBA frames. '
        'The review camera holds the animation clock and hides the HUD; it changes no generated room geometry or art. '
        'These are camera mosaics, not single GBA framebuffers. Captions and borders sit outside captured game pixels.', '',
        '![Actual native HUD-on views](native-HUD-actual.png)', '',
        '**Native views:** each panel above is an unmodified 240×160 HUD-on framebuffer from the normal world renderer. '
        'Source pixels, full-room images and native views remain separate evidence.', '']
    if release_summary:
        lines += [f'[Download the playable ROM]({paths_link}/{release_summary["rom"]}) · '
                  f'[ZIP]({paths_link}/{release_summary["zip"]}) · [Build/checksums]({paths_link}/README.md)', '']
    lines += ['| Generated room | Complete room | Exact 2× inspection | Ordinary movement |',
              '| --- | --- | --- | --- |']
    for row in rows:
        movie = ('[MP4](actual/'+row['walk']['movie']+')') if row.get('walk') else '—'
        if row.get('walk') and row['walk'].get('gif'):
            movie += ' · [inspection GIF](actual/'+row['walk']['gif']+')'
        lines += [f'| {TITLES.get(row["name"], row["name"])} / seed `{row["seed"]}` / room {row["cell"]} '
                  f'| [Native mosaic](actual/{row["panorama"]["file"]}) '
                  f'| [2× PNG](inspection/{row["name"]}-2x.png) | {movie} |']
    lines += ['',
        'The review harness seeds the actual game and uses its native room transition to inspect selected generated cells. '
        'Enemies/projectiles are cleared and Bloom is placed at a disclosed safe standing point for inspection. '
        'Tree, terrain and pose pixels are never painted into the framebuffer. Walking clips use ordinary directional input after that fixture.', '',
        'Every mosaic pixel is copied from its declared native camera crop, with no blending or repainting. '
        'Ambient glitter has native viewport-edge culling and per-view budgets; differences between overlapping camera frames are recorded rather than hidden. '
        'The same frozen world actor coordinates are used in each view.', '',
        'Trees use transparent ground contact: BG2 carries the real local floor, BG1 the upper sixteen pixels, and BG3 the lower sixteen. '
        'Overlapping tree rows preserve the existing maze boundary. The visible canvas and collision remain separate: forest border bases retain their generated full-cell barriers, '
        'while free-standing trees retain their existing shallow root masks.', '',
        'MP4s are lossy viewing copies at the GBA’s full approximately 59.73Hz. Any GIFs use sampled exact-color frames with fixed inspection holds; they do not claim original playback timing.', '',
        '[Capture fixtures, native cameras and raw readbacks](actual/README.md) · '
        '[Literal panel proof](actual-panel-manifest.json) · [Publication summary](actual-publication-summary.json) · '
        '[Original approved source kit](../forest-tree-study/source/README.md) · '
        '[Guide application](../../bartgame/docs/art-reboot/references/TREE_GUIDE_APPLICATION.md)']
    if source:
        lines += ['', f'Frozen source `{source}`; ROM `{freeze.get("rom_sha256")}`.']
    checks = report.get('checks', [])
    lines += ['', f'Capture checks: {sum(bool(v["passed"]) for v in checks)}/{len(checks)}. '
              'These are finite technical checks and recorded rooms, not a claim of exhaustive gameplay or aesthetic acceptance.']
    markdown(out/'README.md', lines)
    actual_lines = ['# Actual mGBA room captures', '',
        '[Full capture report](capture.json) records the exact source bundle, camera crops, overlap differences, fixtures, room/collision hashes and native body scanout observations.', '',
        'Full-room images are camera mosaics. Native camera PNGs are unmodified 240×160 framebuffers. Raw `.bin` files are hardware/room readbacks used for independent verification; they are not rendered substitutes for the captures.', '']
    for row in rows:
        actual_lines += [f'## {TITLES.get(row["name"], row["name"])}', '',
                         f'![Actual camera mosaic]({row["panorama"]["file"]})', '',
                         f'[Native HUD view]({row["native_HUD"]["file"]}) · '
                         f'[First raw camera]({row["panorama"]["views"][0]["file"]})', '']
        if row.get('native_arrival'):
            actual_lines += [f'[Natural arrival with original actors]({row["native_arrival"]["file"]}) '
                             '(before enemy clearing or the standing-position fixture).', '']
    markdown(actual/'README.md', actual_lines)
    write(out/'actual-panel-manifest.json', {'source_commit': source, 'profile': PROFILE,
        'gallery_tool_sha256': LOADED_SHA, 'boards': boards,
        'method': 'Literal RGB native framebuffer/mosaic copies; inspection views use integer nearest-neighbour only. Captions are outside captured game pixels.'})
    summary = {'source_commit': source, 'profile': PROFILE, 'rom_sha256': freeze.get('rom_sha256'),
        'gallery_tool_sha256': LOADED_SHA, 'capture_report_sha256': sha(report_path),
        'rooms': len(rows), 'native_camera_frames': sum(len(r['panorama']['views']) for r in rows),
        'capture_checks_passed': sum(bool(v['passed']) for v in checks), 'capture_checks_total': len(checks),
        'copied_media_and_proof_files': len(all_paths), 'boards': len(boards),
        'panels': sum(len(b['panels']) for b in boards), 'release': release_summary,
        'frozen': args.final}
    write(out/'actual-publication-summary.json', summary)
    assert sha(__file__) == LOADED_SHA, 'Gallery helper changed during publication'
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
