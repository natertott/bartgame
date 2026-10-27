"""Publish native mGBA captures and clearly labelled, enlarged review sheets.

python tools/blight_gallery.py --before-root BEFORE --after-root AFTER --out OUT

Each root contains the ``captures`` (seed 0xB4A7) and ``seed-6`` directories
written by blight_review.py. Native PNGs and GIFs are copied byte-for-byte.
Sheets only enlarge whole frames 2x with nearest-neighbour scaling; captions
are outside the framebuffers. No source artwork is composited into a frame.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont


DATASETS = (('captures', 'seed-b4a7', 0xB4A7), ('seed-6', 'seed-6', 6))
COMPARISONS = (
    ('captures', 'mixed-blight.png', 'Mixed forest / encroaching blight'),
    ('seed-6', 'room-19-stage3.png', 'Deep forest / canopy and ruined stone'),
    ('captures', 'room-20-stage3.png', 'The Heart / final blight stage'),
)
LANDSCAPES = (
    ('captures', 'mixed-blight.png', 'Mixed forest', 'Seed 0xB4A7 / stage 2'),
    ('seed-6', 'room-19-stage3.png', 'Blue-violet canopy and ruins', 'Seed 6 / stage 3'),
    ('seed-6', 'room-04-stage3.png', 'Water and layered forest edges', 'Seed 6 / stage 3'),
    ('seed-6', 'deep-wall.png', 'Mossy masonry and glowing growths', 'Seed 6 / deep-forest feature view'),
    ('seed-6', 'deep-tree.png', 'Twisted tree at a clearing edge', 'Seed 6 / deep-forest feature view'),
    ('captures', 'room-20-stage3.png', 'The Heart', 'Seed 0xB4A7 / stage 3 arena'),
)
INK = '#eee9d7'
MUTED = '#b9b3c9'
BACKGROUND = '#10101b'
NATIVE = (240, 160)
ENLARGED = (480, 320)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fonts():
    family = '/usr/share/fonts/truetype/dejavu/DejaVuSans'
    return (ImageFont.truetype(family + '-Bold.ttf', 22),
            ImageFont.truetype(family + '.ttf', 16),
            ImageFont.truetype(family + '.ttf', 13))


def native(path):
    image = Image.open(path)
    assert image.size == NATIVE, (path, image.size)
    return image.convert('RGB')


def frame(sheet, path, xy):
    x, y = xy
    image = native(path).resize(ENLARGED, Image.Resampling.NEAREST)
    sheet.paste(image, (x, y))


def comparison(before, after, out):
    title, label, small = fonts()
    margin, gap, stride = 24, 24, 378
    sheet = Image.new('RGB', (1032, 112 + stride * len(COMPARISONS)), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, 16), 'Blighted Forest / actual mGBA before and after', font=title, fill=INK)
    draw.text((margin, 48), 'Identical seeds and camera positions; whole 240x160 frames enlarged 2x.', font=label, fill=MUTED)
    for i, (dataset, filename, caption) in enumerate(COMPARISONS):
        top = 80 + stride * i
        draw.text((margin, top), caption, font=label, fill=INK)
        frame(sheet, before / dataset / filename, (margin, top + 27))
        frame(sheet, after / dataset / filename, (margin + 480 + gap, top + 27))
        draw.text((margin, top + 352), 'Previous artwork', font=small, fill=MUTED)
        draw.text((margin + 480 + gap, top + 352), 'Supplied-atlas artwork', font=small, fill=MUTED)
    sheet.save(out / 'before-after.png')


def landscapes(after, out):
    title, label, small = fonts()
    margin, gap, stride = 24, 24, 386
    sheet = Image.new('RGB', (1032, 100 + stride * 3), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, 16), 'Blighted Forest / in the running game', font=title, fill=INK)
    draw.text((margin, 48), 'Actual mGBA framebuffers, enlarged 2x without smoothing.', font=label, fill=MUTED)
    for i, (dataset, filename, caption, context) in enumerate(LANDSCAPES):
        x = margin + (i % 2) * (480 + gap)
        top = 84 + (i // 2) * stride
        frame(sheet, after / dataset / filename, (x, top))
        draw.text((x, top + 329), caption, font=label, fill=INK)
        draw.text((x, top + 351), context, font=small, fill=MUTED)
    sheet.save(out / 'landscapes.png')


def copy_captures(root, out, phase):
    copied = []
    reports = []
    for source_name, destination_name, seed in DATASETS:
        source = root / source_name
        destination = out / phase / destination_name
        report = json.loads((source / 'capture.json').read_text())
        assert int(report['seed'], 0) == seed, (source, report['seed'])
        if phase == 'after':
            changes = report.get('physical_comparison', {}).get('differences', [])
            assert not changes, (source, changes)
            controls = report.get('visual_controls', [])
            assert all(c['identical'] for c in controls), (source, controls)
        destination.mkdir(parents=True, exist_ok=True)
        paths = [source / 'capture.json']
        paths += sorted(source.glob('*.png'))
        paths += sorted(source.glob('*.gif'))
        for path in paths:
            if path.suffix == '.png':
                native(path)  # Reject source previews or accidentally scaled captures.
            target = destination / path.name
            shutil.copyfile(path, target)
            assert sha(path) == sha(target)
            copied.append({'file':str(target.relative_to(out)), 'sha256':sha(target)})
        reports.append({'folder':str(destination.relative_to(out)),
                        'seed':report['seed'], 'rom_sha256':report['rom_sha256'],
                        'rooms':len(report['rooms']), 'features':len(report['features']),
                        'physical_comparison':report.get('physical_comparison'),
                        'visual_controls':report.get('visual_controls')})
    assert len({r['rom_sha256'] for r in reports}) == 1, reports
    return reports, copied


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before-root', type=Path, required=True)
    parser.add_argument('--after-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--source-preview', type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    before_reports, before_files = copy_captures(args.before_root, args.out, 'before')
    after_reports, after_files = copy_captures(args.after_root, args.out, 'after')
    comparison(args.before_root, args.after_root, args.out)
    landscapes(args.after_root, args.out)
    report = {
        'emulator':'mGBA 0.10.5',
        'method':'Native PNG/GIF files copied byte-for-byte. Review sheets enlarge complete native frames 2x using nearest-neighbour scaling and add captions outside them. No altered framebuffer pixels or source-art overlays.',
        'before':before_reports, 'after':after_reports,
        'native_files':before_files + after_files,
        'comparison_views':[{'dataset':d, 'file':f, 'caption':c} for d, f, c in COMPARISONS],
        'landscape_views':[{'dataset':d, 'file':f, 'caption':c, 'context':x} for d, f, c, x in LANDSCAPES],
        'sheets':[{ 'file':name, 'sha256':sha(args.out / name)}
                  for name in ('before-after.png', 'landscapes.png')],
    }
    if args.source_preview:
        target = args.out / 'source-preview.png'
        shutil.copyfile(args.source_preview, target)
        report['source_preview'] = {'file':target.name, 'sha256':sha(target),
                                    'method':'Source-asset preview; separate from emulator captures.'}
    (args.out / 'gallery.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS:', len(report['native_files']), 'byte-exact native files; two enlarged review sheets')


if __name__ == '__main__':
    main()
