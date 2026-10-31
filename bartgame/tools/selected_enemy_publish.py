#!/usr/bin/env python3
"""Publish the selected enemies and Broken Heart with exact mGBA evidence.

Native PNGs, existing full-rate MP4s and exact-palette GIFs are copied unchanged.
Source-art pose catalogs are kept separate from emulator output. Comparison
boards only concatenate/crop real frames, adding captions outside game pixels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from PIL import Image, ImageDraw

from appearance_enemy_publish import copy_capture_report, crop_bounds
from enemy_study_gallery import FONT, text

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
BG = '#101820'
NAMES = ('Coin Toad', 'Quill Moth', 'Trumpet Bellflower', 'Pear Bladder',
         'Moth Confessor', 'Broken Heart')
CLIPS = ('pursuer-behavior', 'flyer-behavior', 'shooter-behavior',
         'hopper-behavior', 'melee-behavior', 'boss-ring')


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def exact_copy(source, destination):
    source, destination = Path(source), Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    assert SHA(source) == SHA(destination), (source, destination)


def source_gallery(work, out, freeze):
    src = work / 'source-gallery'
    manifest = read(src / 'source-manifest.json')
    assert manifest['source_only'] and manifest['profile'] == 11
    assert manifest['frame_count'] == 64 and manifest['body_frame_count'] == 61
    for name, expected in manifest['source_sha256'].items():
        assert SHA(ROOT / name) == expected, ('source gallery stale', name)
        frozen = freeze.get('source_file_sha256', {}).get(name)
        if frozen is not None: assert expected == frozen, ('gallery differs from freeze', name)
    for name, expected in manifest['files'].items():
        assert SHA(src / name) == expected['sha256'], ('source output mismatch', name)
    for row in [*manifest['animations'].values(), manifest['combined_animation']]:
        assert row['exact_palette'] and row['decoded_rgb_verified']
    for p in src.rglob('*'):
        if p.is_file(): exact_copy(p, out / 'source' / p.relative_to(src))
    return {'frame_count': 64, 'body_frame_count': 61,
            'manifest': 'source/source-manifest.json',
            'overview': 'source/selected-overview-source.png',
            'combined_source_cycle': 'source/selected-all-poses-source.gif',
            'note': 'Native SOURCE pose catalogs; fixed review holds, not AI timing.'}


def browse(destination):
    destination = Path(destination)
    report = read(destination / 'capture.json')
    lines = ['# Selected enemies: actual mGBA recordings', '',
             '[Back to the full review](../README.md)' if destination.name == 'actual'
             else '[Back to the full review](../../README.md)', '',
             'These are real generated encounters and ordinary AI updates. The report records '
             'the disclosed seed, player position/health/inventory and boss-HP fixtures. '
             'Enemy state, position, timer, height, animation phase and pose are never assigned. '
             'Source pose catalogs are published separately.', '',
             '[Checks, native-frame links and complete traces](capture.json)', '']
    for row in report['captures']:
        title = row['name'].replace('-', ' ')
        lines += ['## ' + title, '', row.get('note', ''), '',
                  f'![Actual native framebuffer]({row["image"]})', '']
        links = []
        if row.get('gif'): links.append(f'[Exact-palette animation]({row["gif"]})')
        if row.get('video'): links.append(f'[Full-rate MP4]({row["video"]})')
        if row.get('filmstrip'): links.append(f'[Native chronology]({row["filmstrip"]})')
        if links: lines += [' · '.join(links), '']
    (destination / 'README.md').write_text('\n'.join(lines).rstrip() + '\n')


def actual_overview(work, out):
    report = read(work / 'captures/capture.json')
    by = {row['name']: row for row in report['captures']}
    rows = [(work / 'captures', by[clip]) for clip in CLIPS]
    if (work / 'clearing/capture.json').exists():
        clear = read(work / 'clearing/capture.json')
        row = next(r for r in clear['captures'] if r['name'] == 'pursuer-clearing')
        rows[0] = (work / 'clearing', row)
    result = {}
    for cropped in (False, True):
        board = Image.new('RGB', (720, 408), BG)
        draw = ImageDraw.Draw(board)
        caption = 'actual96x80 crops, 2x nearest-neighbour' if cropped else 'unchanged native240x160 frames'
        text(draw, (7, 5), 'SELECTED ENEMIES / ACTUAL mGBA / ' + caption)
        records = []
        for i, (source, row) in enumerate(rows):
            original = Image.open(source / row['image']).convert('RGB')
            assert original.size == (240, 160)
            tick = row['representative_tick']
            bounds = crop_bounds(row, tick) if cropped else None
            image = original.crop(bounds).resize((192, 160), Image.Resampling.NEAREST) if cropped else original
            x, y = (i % 3) * 240, 28 + (i // 3) * 190
            text(draw, (x + 5, y + 3), NAMES[i])
            dx, dy = x + (24 if cropped else 0), y + 22
            board.paste(image, (dx, dy))
            assert board.crop((dx, dy, dx + image.width, dy + image.height)).tobytes() == image.tobytes()
            records.append({'name': NAMES[i], 'case': row['name'],
                            'source_image': str((source / row['image']).relative_to(work)),
                            'source_sha256': SHA(source / row['image']), 'tick': tick,
                            'crop': bounds, 'destination': [dx, dy, dx + image.width, dy + image.height],
                            'note': 'Only actual framebuffer pixels; external captions and integer crop enlargement.'})
        name = 'selected-actual-context-2x.png' if cropped else 'selected-actual-native.png'
        board.save(out / name)
        result[name] = {'sha256': SHA(out / name), 'panels': records}
    write(out / 'selected-actual-manifest.json', result)
    return result


def release_rom(work, release, freeze, branch, gallery):
    release.mkdir(parents=True, exist_ok=True)
    stem = 'selected-enemies-' + freeze['source_commit'][:7]
    rom = stem + '.gba'; archive = stem + '.zip'
    source = work / 'frozen/bartgame.gba'
    assert SHA(source) == freeze['rom_sha256']
    exact_copy(source, release / rom)
    exact_copy(work / 'frozen/freeze.json', release / 'freeze.json')
    (release / 'ROM-SHA256.txt').write_text(f'{SHA(release / rom)}  {rom}\n')
    (release / 'README.txt').write_text(f'''BARTGAME - selected enemies and the Broken Heart

Coin Toad, Quill Moth, Trumpet Bellflower, Pear Bladder, Moth Confessor,
and a purplish heart broken down the middle. Complete native pose sets use
the existing AI rules, timings, damage and collision footprints.

Source: {freeze['source_commit']}
Default build: make -j4 (BART_ENEMY=11).

The Winebound HUD, title Options, Workbench inventory and event-labelled
regional/chamber maps remain. Title Options mixes three frame styles with
three palettes; Up/Down selects, Left/Right cycles, A/B/Start returns.
Preferences survive reset independently of the run save.

Start opens/closes inventory; R cycles pages; D-pad selects; A/B/L assign.
On the map A zooms, B returns and D-pad browses rooms. The corner minimap
and equipped-item ammunition remain visible during play.

Gallery: https://github.com/natertott/bartgame/blob/{branch}/{gallery}/README.md
Open the .gba in mGBA; no commercial ROM is required.
''')
    with zipfile.ZipFile(release / archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in (rom, 'README.txt', 'ROM-SHA256.txt', 'freeze.json'): z.write(release / name, name)
    with zipfile.ZipFile(release / archive) as z:
        assert z.testzip() is None
        assert len([n for n in z.namelist() if n.endswith('.gba')]) == 1
        for name in z.namelist():
            assert hashlib.sha256(z.read(name)).hexdigest() == SHA(release / name)
    (release / 'SHA256SUMS.txt').write_text(''.join(f'{SHA(release / name)}  {name}\n' for name in (rom, archive)))
    return rom, archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('work', 'out', 'release'): parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--branch', required=True)
    args = parser.parse_args()
    work, out, release = args.work.resolve(), args.out.resolve(), args.release.resolve()
    out.mkdir(parents=True, exist_ok=True)
    frozen = read(work / 'frozen/freeze.json')
    assert frozen.get('enemy', frozen.get('enemy_variant', 11)) == 11
    approved = {frozen['rom_sha256']: {**frozen, 'variant': frozen.get('variant', 11)}}
    audit = read(work / 'audit.json')
    assert audit['passed'] == audit['total'] and not audit.get('failures'), 'Final independent audit must pass before publication'
    validation = out / 'validation'; validation.mkdir(exist_ok=True)
    exact_copy(work / 'frozen/freeze.json', validation / 'freeze.json')
    for name in ('audit.json', 'audit-summary.json', 'audit.log', 'build.log', 'build-default.log',
                 'runtime-review.md', 'visual-review.md', 'selected-enemy-audit.json', 'selected-enemy-audit-summary.json',
                 'clearing-summary.json', 'final-runtime-verification.json',
                 'selection-contracts.json', 'historical-profile-preservation.json',
                 'capture.log', 'clearing.log'):
        if (work / name).is_file(): exact_copy(work / name, validation / name)
    if (work / 'frozen/coverage.json').is_file():
        exact_copy(work / 'frozen/coverage.json', validation / 'coverage.json')
    for name in ('native-validation.json', 'heart-native-validation.json'):
        if (work / 'source-heart' / name).is_file():
            exact_copy(work / 'source-heart' / name, validation / name)
    source = source_gallery(work, out, frozen)
    reviews = [copy_capture_report(work / 'captures', out / 'actual', 'capture.json', approved)]
    browse(out / 'actual')
    if (work / 'clearing/capture.json').exists():
        reviews.append(copy_capture_report(work / 'clearing', out / 'actual/clearing', 'capture.json', approved))
        browse(out / 'actual/clearing')
    overview = actual_overview(work, out)
    for name in ('heart-actual-poses.png', 'heart-actual-poses.json',
                 'heart-defeat-actual-timeline.png', 'heart-defeat-actual-timeline.json'):
        if (work / name).is_file(): exact_copy(work / name, out / 'actual' / name)
    if (work / 'heart-rom-native-atlas.png').is_file():
        exact_copy(work / 'heart-rom-native-atlas.png', validation / 'heart-rom-native-atlas.png')
    rom, archive = release_rom(work, release, frozen, args.branch, str(out.relative_to(REPO)))
    summary = {'source_commit': frozen['source_commit'], 'rom_sha256': frozen['rom_sha256'],
               'rom_file': rom, 'zip': archive, 'source_art': source,
               'actual_reviews': reviews, 'actual_overview': overview,
               'captures': sum(r['captures'] for r in reviews),
               'passed': sum(r['passed'] for r in reviews), 'total': sum(r['total'] for r in reviews),
               'omitted_gifs': sum((r['omitted_gifs'] for r in reviews), []),
               'format_policy': 'Native PNGs/filmstrips exact; existing full-rate MP4s lossy viewing copies; exact-only GIFs. Raw all-frame archives remain local. Source art is separate.'}
    write(validation / 'publication-summary.json', summary)
    manifest = {'source_commit': frozen['source_commit'], 'files': {},
                'note': 'Exact hashes excluding this manifest. Parent regenerates after main/release editorial README additions.'}
    for base in (out, release):
        for path in sorted(base.rglob('*')):
            if path.is_file() and path != validation / 'publication-manifest.json':
                manifest['files'][str(path.relative_to(REPO))] = {'sha256': SHA(path), 'bytes': path.stat().st_size}
    write(validation / 'publication-manifest.json', manifest)
    print(json.dumps({'source': frozen['source_commit'], 'captures': summary['captures'],
                      'checks': [summary['passed'], summary['total']], 'source_frames': 64,
                      'rom': rom, 'zip': archive, 'files': len(manifest['files'])}))


if __name__ == '__main__':
    main()
