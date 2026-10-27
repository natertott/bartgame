"""Publish regular-forest artwork from matched, real mGBA captures.

python tools/healthy_gallery.py --before-root BEFORE --after-root AFTER --out OUT

Both roots contain ``captures`` (seed 0xB4A7) and ``seed-6`` from
healthy_review.py. Native PNGs, GIFs and reports are copied byte-for-byte.
Review sheets enlarge complete frames 2x with nearest-neighbour scaling;
all headings and captions are outside the game framebuffers.
"""
import argparse
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw

from blight_gallery import BACKGROUND, INK, MUTED, fonts, frame, native, sha


DATASETS = (('captures', 'seed-b4a7', 0xB4A7), ('seed-6', 'seed-6', 6))
COMPARISONS = (
    ('captures', 'great-tree.png', 'Living trees / canopy, trunks and roots'),
    ('seed-6', 'pond-bank.png', 'Pond and bridge / softer banks and water'),
    ('captures', 'path-canopy.png', 'Forest trail / grass, earth and foliage'),
    ('seed-6', 'room-03-stage2.png', 'The transition / living forest meets blight'),
)
LANDSCAPES = (
    ('captures', 'great-tree.png', 'Large living trees', 'Seed 0xB4A7 / tree feature view'),
    ('seed-6', 'pond-bank.png', 'Pond, banks and bridge', 'Seed 6 / pond feature view'),
    ('seed-6', 'birch.png', 'Birch and understory', 'Seed 6 / tree feature view'),
    ('seed-6', 'fir.png', 'Evergreens and forest floor', 'Seed 6 / tree feature view'),
    ('seed-6', 'room-21-stage0.png', 'Water through healthy woodland', 'Seed 6 / stage 0'),
    ('seed-6', 'room-03-stage2.png', 'The first spread of blight', 'Seed 6 / stage 2'),
)


def render_comparison(before, after, out):
    title, label, small = fonts()
    margin, gap, stride = 24, 24, 378
    sheet = Image.new('RGB', (1032, 112 + stride * len(COMPARISONS)), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, 16), 'Regular forest / actual mGBA before and after', font=title, fill=INK)
    draw.text((margin, 48), 'Identical seeds and camera positions; complete frames enlarged 2x.', font=label, fill=MUTED)
    for index, (dataset, filename, caption) in enumerate(COMPARISONS):
        top = 80 + stride * index
        draw.text((margin, top), caption, font=label, fill=INK)
        frame(sheet, before / dataset / filename, (margin, top + 27))
        frame(sheet, after / dataset / filename, (margin + 480 + gap, top + 27))
        draw.text((margin, top + 352), 'Previous regular forest', font=small, fill=MUTED)
        draw.text((margin + 480 + gap, top + 352), 'Unified forest materials', font=small, fill=MUTED)
    sheet.save(out / 'before-after.png')


def render_landscapes(after, out):
    title, label, small = fonts()
    margin, gap, stride = 24, 24, 386
    sheet = Image.new('RGB', (1032, 100 + stride * 3), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, 16), 'Regular forest / in the running game', font=title, fill=INK)
    draw.text((margin, 48), 'Actual 240x160 mGBA framebuffers, enlarged 2x without smoothing.', font=label, fill=MUTED)
    for index, (dataset, filename, caption, context) in enumerate(LANDSCAPES):
        x = margin + index % 2 * (480 + gap)
        top = 84 + index // 2 * stride
        frame(sheet, after / dataset / filename, (x, top))
        draw.text((x, top + 329), caption, font=label, fill=INK)
        draw.text((x, top + 351), context, font=small, fill=MUTED)
    sheet.save(out / 'landscapes.png')


def check_control(control):
    """A changed shared material stays disclosed, with its bounds proved."""
    if control['identical']:
        assert control['different_pixels'] == 0, control
        return
    assert control['file'] != 'drain-control.png', control
    assert control.get('retained_pixels_identical') is True, control
    assert control.get('changed_pixels_within_materials') is True, control
    materials = control.get('allowed_changed_materials')
    assert materials and all(isinstance(value, str) for value in materials), control
    bounds = control.get('allowed_changed_bounds')
    assert bounds, control
    for bound in bounds:
        assert bound['materials'] and set(bound['materials']) <= set(materials), bound
        x0, y0, x1, y1 = bound['framebuffer_rect']
        assert 0 <= x0 < x1 <= 240 and 0 <= y0 < y1 <= 160, bound


def matched(before, after):
    assert before['seed'] == after['seed']
    assert before['fixture_version'] == after['fixture_version']
    assert len(before['rooms']) == len(after['rooms']) == 25
    assert sorted(view['cell'] for view in after['rooms']) == list(range(25))
    physics = after['physical_comparison']
    assert physics['checked_rooms'] == physics['unchanged_rooms'] == 25
    assert not physics['differences']
    for old, new in zip(before['rooms'], after['rooms']):
        for field in ('cell', 'stage', 'role', 'position', 'camera', 'image',
                      'logical_sha256', 'solid_sha256', 'spots_sha256'):
            assert old[field] == new[field], (new['cell'], field)
    assert len(before['features']) == len(after['features'])
    for old, new in zip(before['features'], after['features']):
        for field in ('feature', 'cell', 'position', 'image',
                      'logical_sha256', 'solid_sha256', 'spots_sha256'):
            assert old[field] == new[field], (new['feature'], field)
    controls = after['visual_controls']
    assert any(c['file'] == 'drain-control.png' and c['identical'] for c in controls)
    for control in controls:
        check_control(control)


def copy_native(root, out, phase):
    copied, reports = [], []
    for source_name, destination_name, seed in DATASETS:
        source = root / source_name
        destination = out / phase / destination_name
        report = json.loads((source / 'capture.json').read_text())
        assert int(report['seed'], 0) == seed, (source, report['seed'])
        destination.mkdir(parents=True, exist_ok=True)
        paths = [source / 'capture.json'] + sorted(source.glob('*.png')) + sorted(source.glob('*.gif'))
        for path in paths:
            if path.suffix == '.png':
                native(path)
            if path.suffix == '.gif':
                with Image.open(path) as gif:
                    assert gif.size == (480, 320), (path, gif.size)
            target = destination / path.name
            shutil.copyfile(path, target)
            assert sha(path) == sha(target), target
            copied.append({'file': str(target.relative_to(out)), 'sha256': sha(target)})
        reports.append({'folder': str(destination.relative_to(out)), 'seed': report['seed'],
                        'rom_sha256': report['rom_sha256'], 'fixture_version': report['fixture_version'],
                        'rooms': len(report['rooms']), 'features': len(report['features']),
                        'physical_comparison': report.get('physical_comparison'),
                        'visual_controls': report.get('visual_controls')})
    assert len({value['rom_sha256'] for value in reports}) == 1, reports
    return reports, copied


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before-root', type=Path, required=True)
    parser.add_argument('--after-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--source-preview', type=Path)
    args = parser.parse_args()
    # Validate both complete runs before publishing even the first image.
    for dataset, _, _ in DATASETS:
        before = json.loads((args.before_root / dataset / 'capture.json').read_text())
        after = json.loads((args.after_root / dataset / 'capture.json').read_text())
        matched(before, after)
    args.out.mkdir(parents=True, exist_ok=True)
    before_reports, before_files = copy_native(args.before_root, args.out, 'before')
    after_reports, after_files = copy_native(args.after_root, args.out, 'after')
    render_comparison(args.before_root, args.after_root, args.out)
    render_landscapes(args.after_root, args.out)
    report = {
        'emulator': 'mGBA 0.10.5',
        'method': 'Native PNG/GIF/report files copied byte-for-byte. Sheets enlarge complete 240x160 frames 2x with nearest-neighbour scaling and add captions outside the framebuffers. No source-art overlays or painted game pixels.',
        'before': before_reports, 'after': after_reports,
        'native_files': before_files + after_files,
        'comparison_views': [{'dataset': d, 'file': f, 'caption': c} for d, f, c in COMPARISONS],
        'landscape_views': [{'dataset': d, 'file': f, 'caption': c, 'context': x} for d, f, c, x in LANDSCAPES],
        'sheets': [{'file': name, 'sha256': sha(args.out / name)} for name in ('before-after.png', 'landscapes.png')],
    }
    if args.source_preview:
        target = args.out / 'source-preview.png'
        shutil.copyfile(args.source_preview, target)
        report['source_preview'] = {'file': target.name, 'sha256': sha(target),
                                    'method': 'Source-asset preview; separate from actual emulator captures.'}
    (args.out / 'gallery.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS:', len(report['native_files']), 'byte-exact native files; 50 matched rooms; two enlarged review sheets')


if __name__ == '__main__':
    main()
