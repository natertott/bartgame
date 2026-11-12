#!/usr/bin/env python3
"""Publish labelled, lossless review boards from cream_dynamic_capture output.

This utility does not run the game or manufacture gameplay pixels. It copies
native captures and assembles labelled boards using integer nearest-neighbour
scaling. Required: Pillow. Example:

    python tools/cream_heights_gallery.py --capture /path/to/native-r1 \
        --bundle /path/to/frozen/style-12 --out ../cream-heights-review

A draft may be assembled with --allow-partial. README.generated.md is a template;
an existing hand-written README.md is never overwritten. Re-run with only
--out PATH --refresh-manifest after editing that README or adding the ROM.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

MAP_NAMES = (
    'Contour Folio', 'Curdstone Diorama', 'Geological Section',
    'Exploded Shelves', 'Pilgrim Ribbon', 'Chamber Quilt',
    'Surveyor Blueprint', 'Stained Reliquary', 'Cairn Locator',
    'Plan & Escarpment',
)
ROOM_NAMES = (
    'Open Shelf', 'Folded Stair', 'Broken Mesa', 'Switchback',
    'High Grotto', 'Narrow Spurs', 'Double Ridge', 'Peak Arena',
)
SECTIONS = ('rooms', 'maps', 'local-actions', 'waterfalls', 'earned', 'performance')
SUPPLEMENTAL_SECTIONS = ('maps-fresh', 'forest-cache', 'earned-long')
BACKGROUND = '#10151d'
PANEL = '#1a222b'
GOLD = '#e8c670'
WHITE = '#f5efdb'
MUTED = '#b8c1c6'
NEAREST = Image.Resampling.NEAREST


def sha(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text()) if path.is_file() else None


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def font(size=16):
    for filename in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                     '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        if Path(filename).is_file():
            return ImageFont.truetype(filename, size)
    return ImageFont.load_default()


def label(draw, xy, value, size=16, fill=WHITE):
    draw.text(xy, value, font=font(size), fill=fill)


def open_native(path: Path, size):
    with Image.open(path) as original:
        if original.size != size:
            raise ValueError(f'{path}: expected native {size}, got {original.size}')
        return original.convert('RGB')


def public_file(relative: Path) -> bool:
    """Keep inspectable evidence, excluding private emulators and raw sequences."""
    if relative.suffix.lower() not in ('.png', '.gif', '.json'):
        return False
    for part in relative.parts[:-1]:
        lower = part.lower()
        if (lower.startswith('private') or 'abi' in lower or
                lower.startswith('survey-core') or
                lower in ('raw-frames', 'harness-source', '__pycache__')):
            return False
    return not re.fullmatch(r'frame-\d+\.png', relative.name, re.IGNORECASE)


def classify(path: str) -> str:
    if path.startswith('images/map-concepts-'):
        return 'labelled comparison board; native pause captures, nearest-neighbour scaling'
    if path.startswith('images/room-families'):
        return 'labelled comparison board; registered frozen renderer room mosaics'
    if path.startswith('images/maps/'):
        return 'ordinary native mGBA pause screenshot' + ('; nearest-neighbour enlargement' if '-2x.' in path or '-3x.' in path else '')
    if path.startswith('images/rooms/'):
        return 'registered frozen renderer stitched room survey' + ('; nearest-neighbour enlargement' if '-2x.' in path or '-3x.' in path else '')
    if path.startswith('validation/'):
        if path.endswith('.json'):
            return 'capture provenance or validation report'
        if '/registered-renderer/' in path or '/registered-panorama/' in path:
            return 'registered frozen renderer evidence; not an ordinary gameplay viewport'
        return 'mGBA capture evidence; fixture details are in adjacent JSON reports'
    if path.endswith('.gba'):
        return 'playable ROM; identity recorded independently in provenance'
    return 'review documentation or frozen-build metadata'


def manifest(out: Path, provenance=None):
    """Hash every public artifact, excluding the manifest itself (no recursion)."""
    if provenance is None:
        existing = load_json(out / 'manifest.json')
        if not existing:
            raise ValueError('Cannot refresh: manifest.json does not exist')
        provenance = existing['provenance']
    files = []
    for path in sorted(out.rglob('*')):
        if not path.is_file() or path == out / 'manifest.json':
            continue
        relative = path.relative_to(out).as_posix()
        item = dict(file=relative, bytes=path.stat().st_size,
                    sha256=sha(path), role=classify(relative))
        if path.suffix.lower() in ('.png', '.gif'):
            with Image.open(path) as image:
                item['size'] = list(image.size)
                item['frames'] = getattr(image, 'n_frames', 1)
        files.append(item)
    result = dict(schema=1, provenance=provenance, files=files,
                  self_hash_note='manifest.json is excluded from its own file list; all other public files are hashed.')
    write_json(out / 'manifest.json', result)
    return result


def copy_evidence(capture: Path, out: Path):
    copied = []
    for section in SECTIONS + SUPPLEMENTAL_SECTIONS:
        folder = capture / section
        if not folder.is_dir():
            continue
        for source in sorted(folder.rglob('*')):
            if not source.is_file():
                continue
            relative = source.relative_to(capture)
            if not public_file(relative):
                continue
            destination = out / 'validation' / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied.append(dict(file=destination.relative_to(out).as_posix(),
                               capture_file=relative.as_posix(), sha256=sha(source)))
    if (capture / 'report.json').is_file():
        target = out / 'validation' / 'capture-report.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(capture / 'report.json', target)
        copied.append(dict(file=target.relative_to(out).as_posix(),
                           capture_file='report.json', sha256=sha(capture / 'report.json')))
    return copied


def image_versions(source: Path, target: Path, native_size):
    image = open_native(source, native_size)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)  # Keep the exact original PNG bytes.
    for scale in (2, 3):
        image.resize((image.width * scale, image.height * scale), NEAREST).save(
            target.with_name(target.stem + f'-{scale}x.png'))
    return image


def map_boards(capture: Path, out: Path, allow_partial: bool):
    images = {}
    missing = []
    for index in range(1, 11):
        for view in ('overview', 'zoom'):
            filename = f'{index:02d}-{view}.png'
            source = capture / 'maps' / filename
            if source.is_file():
                images[index, view] = image_versions(
                    source, out / 'images/maps' / filename, (240, 160))
            else:
                missing.append('maps/' + filename)
    if missing and not allow_partial:
        raise ValueError('Incomplete map capture: ' + ', '.join(missing))
    if not images:
        return [], missing
    boards = []
    # Two 5-row boards. Screens remain exact 2x pixels; labels sit outside them.
    margin, gap, width, screen_h, row_h = 20, 20, 480, 320, 358
    for start, end in ((1, 5), (6, 10)):
        board = Image.new('RGB', (2 * width + gap + 2 * margin,
                                  82 + 5 * row_h + 20), BACKGROUND)
        draw = ImageDraw.Draw(board)
        label(draw, (margin, 10), f'CURDLED CREAM / MAP CONCEPTS {start:02d}-{end:02d}', 23, GOLD)
        label(draw, (margin, 42), 'Actual mGBA pause screens / 2x nearest-neighbour / ten unselected concepts', 15, MUTED)
        if missing:
            label(draw, (margin, 62), 'DRAFT - missing views are explicitly marked', 13, GOLD)
        for row, index in enumerate(range(start, end + 1)):
            top = 82 + row * row_h
            label(draw, (margin, top), f'{index:02d}  {MAP_NAMES[index - 1]}', 18, GOLD)
            for col, view in enumerate(('overview', 'zoom')):
                left = margin + col * (width + gap)
                label(draw, (left + width - 96, top + 2), view.upper(), 13, MUTED)
                pos = (left, top + 28)
                image = images.get((index, view))
                if image is None:
                    draw.rectangle((left, pos[1], left + width - 1, pos[1] + screen_h - 1), fill=PANEL)
                    label(draw, (left + 20, pos[1] + 140), 'Capture pending', 24, GOLD)
                else:
                    board.paste(image.resize((width, screen_h), NEAREST), pos)
        destination = out / 'images' / f'map-concepts-{start:02d}-{end:02d}.png'
        board.save(destination)
        boards.append(destination.relative_to(out).as_posix())
    return boards, missing


def room_boards(capture: Path, out: Path, allow_partial: bool):
    entries = []
    seen = set()
    for folder in sorted((capture / 'rooms').glob('archetype-*-cell-*')):
        match = re.fullmatch(r'archetype-(\d+)-cell-(\d+)', folder.name)
        if not match:
            continue
        archetype, cell = map(int, match.groups())
        if not 0 <= archetype < len(ROOM_NAMES):
            raise ValueError(f'Unknown room archetype in {folder}')
        source = folder / 'registered-renderer/full-room.png'
        if not source.is_file():
            continue
        image = image_versions(source, out / 'images/rooms' / (folder.name + '.png'), (512, 384))
        if archetype in seen:
            raise ValueError(f'Duplicate room family {archetype}; select one survey per family')
        seen.add(archetype)
        entries.append((archetype, cell, image))
    missing = [f'room family {i:02d} ({name})' for i, name in enumerate(ROOM_NAMES) if i not in seen]
    if missing and not allow_partial:
        raise ValueError('Incomplete room survey: ' + ', '.join(missing))
    if not entries:
        return None, missing
    margin, gap, card_w, row_h = 20, 20, 512, 422
    board = Image.new('RGB', (2 * card_w + 2 * margin + gap, 82 + 4 * row_h + 20), BACKGROUND)
    draw = ImageDraw.Draw(board)
    label(draw, (margin, 10), 'CURDLED CREAM / WEATHERED CURDSTONE / EIGHT ROOM FAMILIES', 22, GOLD)
    label(draw, (margin, 42), '512x384 native registered frozen renderer surveys / stitched cameras, not single GBA screens', 14, MUTED)
    if missing:
        label(draw, (margin, 62), 'DRAFT - missing families are explicitly marked', 13, GOLD)
    by_family = {archetype: (cell, image) for archetype, cell, image in entries}
    for archetype, name in enumerate(ROOM_NAMES):
        left = margin + (archetype % 2) * (card_w + gap)
        top = 82 + (archetype // 2) * row_h
        if archetype in by_family:
            cell, image = by_family[archetype]
            label(draw, (left, top), f'{archetype + 1:02d}  {name} / cell {cell:02d}', 18, GOLD)
            board.paste(image, (left, top + 28))
        else:
            label(draw, (left, top), f'{archetype + 1:02d}  {name}', 18, GOLD)
            draw.rectangle((left, top + 28, left + 511, top + 411), fill=PANEL)
            label(draw, (left + 20, top + 180), 'Survey pending', 24, GOLD)
    destination = out / 'images/room-families.png'
    board.save(destination)
    return destination.relative_to(out).as_posix(), missing


def reports(capture: Path, rom_sha: str, commit: str):
    summaries = []
    seeds = set()
    for section in SECTIONS + SUPPLEMENTAL_SECTIONS:
        if section in SUPPLEMENTAL_SECTIONS and not (capture / section).is_dir():
            continue
        report = load_json(capture / section / 'report.json')
        summary = dict(section=section, present=report is not None, complete=None)
        if report is not None:
            if report.get('rom_sha256') and report['rom_sha256'] != rom_sha:
                raise ValueError(f'{section}/report.json belongs to a different ROM')
            if report.get('source_commit') and report['source_commit'] != commit:
                raise ValueError(f'{section}/report.json belongs to a different source commit')
            if section in ('maps', 'maps-fresh'):
                for entry in report.get('images', []):
                    relative = Path(entry['file'])
                    if relative.is_absolute() or '..' in relative.parts:
                        raise ValueError(f'{section}/report.json contains an invalid screenshot path')
                    image = capture / section / relative
                    if image.is_file() and entry.get('sha256') and sha(image) != entry['sha256']:
                        raise ValueError(f'{image}: pixels no longer match the capture report hash')
            summary.update(complete=report.get('complete'), sha256=sha(capture / section / 'report.json'))
            if isinstance(report.get('seed'), int):
                seeds.add(report['seed'])
            for key in ('fixture', 'fixture_scope', 'limits', 'charted_fixture', 'long_only'):
                if key in report:
                    summary[key] = report[key]
        summaries.append(summary)
    return summaries, sorted(seeds)


def readme(out: Path, provenance):
    commit = provenance['source_commit']
    rom_sha = provenance['rom_sha256']
    seeds = ', '.join(f'0x{s:x} ({s})' for s in provenance['seeds']) or 'Not present in capture reports; check input traces.'
    map_count = 20 - len(provenance['missing_map_images'])
    room_count = 8 - len(provenance['missing_room_families'])
    status = 'All six capture sections report complete.' if provenance['all_sections_complete'] else 'Validation is pending or incomplete; see the section table below. This template does not imply the checks passed.'
    lines = [
        '# Curdled Cream: heights and map review', '',
        '**Generated review template. Review capture reports and replace this file with a final README before publication.**', '',
        'This pass uses the selected Weathered Curdstone direction with new room geometry, carved ascents, ledges and animated blue waterfalls. '
        'The ten pause-map presentations below are **unselected concepts**, not ten adopted regional art styles.', '',
        f'- Frozen source: `{commit}`',
        f'- ROM SHA-256: `{rom_sha}`',
        f'- Reported seed(s): {seeds}',
        f'- Present evidence: {map_count}/20 native pause screens; {room_count}/8 room families.', '',
        status, '',
        '## Room art and geometry', '',
        '[Eight room families](images/room-families.png). The board uses native 512×384 room surveys. '
        'Each panorama is a literal crop assembly of registered frozen mGBA renderer camera frames; '
        'it is **not** a single play viewport or an ordinary live gameplay frame. The separate review core fixes '
        'the renderer camera and clock. Adjacent `validation/rooms/*/registered-renderer/provenance.json` files '
        'identify every source camera, crop, fixture and equality check. Native singles and nearest 2×/3× inspection '
        'images are in [images/rooms](images/rooms).', '',
        '## Ten pause-map concepts', '',
        '[Concepts 01–05](images/map-concepts-01-05.png) · [Concepts 06–10](images/map-concepts-06-10.png)', '',
        f'The {map_count} available map images are ordinary 240×160 mGBA-rendered pause screens opened and navigated '
        'with real menu inputs. Comparison boards add external labels and use exact nearest-neighbour enlargement; '
        'the screenshot pixels are not repainted. Original PNG bytes plus 2× and 3× versions are in '
        '[images/maps](images/maps).', '',
        '| # | Concept | Overview | Room zoom |',
        '|---|---|---|---|',
    ]
    for i, name in enumerate(MAP_NAMES, 1):
        cells = []
        for view in ('overview', 'zoom'):
            file = f'images/maps/{i:02d}-{view}.png'
            cells.append(f'[native]({file})' if (out / file).is_file() else 'Pending')
        lines.append(f'| {i:02d} | {name} | {cells[0]} | {cells[1]} |')
    lines += [
        '', '**Controls:** D-pad selects a room; A opens its zoom; B returns to the overview/back; '
        'L or SELECT cycles the ten concepts; R opens the item menu; START resumes gameplay. '
        'The native title labels identify each concept. Icons and height information come from the selected actual room, '
        'with unknown rooms hidden.', '',
        'Fresh-discovery comparisons, when captured, are retained separately under '
        '`validation/maps-fresh/`; they are supplemental and are not counted among the twenty atlas comparison screens.', '',
        '## Capture scope and limitations', '',
        'The surveyed atlas fixture visits the 25 generated rooms through ordinary room-load requests to make the '
        'ten designs comparable. Separate clips use disclosed hero-navigation fixtures to put the player near the '
        'feature under review. This is not a claim of an unassisted playthrough. Normal captures do not write '
        'inventory, health, gate results, terrain, progression, palette, VRAM or framebuffer; the frozen registered '
        'survey helper is explicitly separate. Read the per-run input traces for seed/reset/navigation setup. '
        'Any earned-progression evidence and its fixture scope are reported independently.', '',
        'Native local-action and waterfall GIFs are retained under `validation/local-actions/` and '
        '`validation/waterfalls/`. Raw numbered animation frames, AVI recordings, private emulator cores, generated '
        'ABI helpers and intermediate binaries are intentionally omitted from this public gallery. Registered camera '
        'PNGs and JSON proof reports are retained. The manifest hashes all published artifacts.', '',
        '| Capture section | Report status | Evidence |',
        '|---|---|---|',
    ]
    for report in provenance['reports']:
        state = 'Complete' if report['complete'] is True else 'Failed/incomplete' if report['present'] else 'Pending / not captured'
        section = report['section']
        link = f'[report](validation/{section}/report.json)' if report['present'] else '—'
        lines.append(f'| {section} | {state} | {link} |')
    lines += ['', 'No additional performance or solvability guarantee is inferred by this publishing utility. '
              'The performance report, if present, describes its finite frame-count comparison and limits. '
              'The reports record the actual read-only map checks, renderer comparisons and traversal checks.', '',
              '## Reproduce this gallery', '', '```sh',
              'python tools/cream_heights_gallery.py --capture PATH/TO/native-r1 \\',
              '  --bundle PATH/TO/frozen/style-12 --out cream-heights-review',
              '# After adding the final README or ROM:',
              'python tools/cream_heights_gallery.py --out cream-heights-review --refresh-manifest',
              '```', '',
              '`manifest.json` records frozen build identity, capture report hashes, source-to-public copied evidence, '
              'image dimensions and the SHA-256 of every public file except itself. `README.generated.md` is never '
              'a substitute for inspecting actual results.', '']
    (out / 'README.generated.md').write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path)
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--allow-partial', action='store_true', help='Produce explicitly labelled draft boards when captures are missing')
    parser.add_argument('--refresh-manifest', action='store_true', help='Rehash an existing gallery after editorial changes; no capture/build required')
    args = parser.parse_args()
    out = args.out.resolve()
    if args.refresh_manifest:
        result = manifest(out)
        print(f'Refreshed {out}/manifest.json ({len(result["files"])} files)')
        return 0
    if args.capture is None or args.bundle is None:
        parser.error('--capture and --bundle are required unless --refresh-manifest is used')
    capture, bundle = args.capture.resolve(), args.bundle.resolve()
    if out == capture or out in capture.parents or capture in out.parents:
        parser.error('--out must be separate from --capture (neither may contain the other)')
    if out == bundle or out in bundle.parents or bundle in out.parents:
        parser.error('--out must be separate from --bundle (neither may contain the other)')
    if not capture.is_dir():
        parser.error(f'Capture directory does not exist: {capture}')
    rom = bundle / 'bartgame.gba'
    commit_file = bundle / 'source-commit.txt'
    if not rom.is_file() or not commit_file.is_file():
        parser.error('Frozen bundle must contain bartgame.gba and source-commit.txt')
    commit = commit_file.read_text().strip()
    if not re.fullmatch('[0-9a-fA-F]{40}', commit):
        parser.error('source-commit.txt must identify a full 40-character source commit')
    rom_sha = sha(rom)
    options = load_json(bundle / 'build-options.json')
    if options and options.get('rom_sha256') and options['rom_sha256'] != rom_sha:
        parser.error('Frozen build-options.json does not match bartgame.gba')
    report_summaries, seeds = reports(capture, rom_sha, commit)
    if not args.allow_partial:
        for required in ('rooms', 'maps'):
            if not (capture / required / 'report.json').is_file():
                parser.error(f'{required}/report.json is required; use --allow-partial for a labelled draft')
    existing = load_json(out / 'manifest.json')
    if existing and existing['provenance']['rom_sha256'] != rom_sha:
        parser.error('Output already contains a different ROM review; choose a new --out directory')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'images').mkdir(exist_ok=True)
    map_files, missing_maps = map_boards(capture, out, args.allow_partial)
    room_file, missing_rooms = room_boards(capture, out, args.allow_partial)
    copies = copy_evidence(capture, out)
    metadata = out / 'validation/frozen-build'
    metadata.mkdir(parents=True, exist_ok=True)
    for name in ('source-commit.txt', 'build-options.json'):
        if (bundle / name).is_file():
            shutil.copy2(bundle / name, metadata / name)
    provenance = dict(
        source_commit=commit, rom_sha256=rom_sha, build_options=options,
        gallery_tool_sha256=sha(Path(__file__)), seeds=seeds,
        reports=report_summaries, all_sections_complete=all(r['complete'] is True for r in report_summaries),
        draft=bool(missing_maps or missing_rooms), missing_map_images=missing_maps,
        missing_room_families=missing_rooms, map_boards=map_files, room_board=room_file,
        method='Lossless native mGBA captures and integer nearest-neighbour enlargements. Ordinary pause captures and frozen registered-renderer room mosaics are labelled separately.',
        copied_capture_files=copies,
    )
    readme(out, provenance)
    result = manifest(out, provenance)
    print(f'Wrote {out}: {20-len(missing_maps)}/20 maps, {8-len(missing_rooms)}/8 families, {len(result["files"])} public files')
    if not provenance['all_sections_complete']:
        print('Validation pending or incomplete: inspect README.generated.md and per-section reports.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, json.JSONDecodeError) as error:
        raise SystemExit(str(error))
