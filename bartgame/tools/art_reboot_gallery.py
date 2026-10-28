"""Publish frozen real-mGBA art-reboot evidence without painting gameplay.

Native PNGs, capture GIFs, chronological filmstrips and reports are copied
byte-for-byte. Review boards add captions outside complete 2x nearest-neighbour
framebuffers. The MP4 samples complete clips at their recorded timing; it is a
lossy convenience, not the primary pixel evidence. Compiled sprite atlases are
explicitly labelled source decoding, not emulator screenshots.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

from PIL import Image, ImageDraw, ImageFont

import bloom_suite_gallery as G
from blight_scope_probe import Rom

FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
TITLE = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 19)
GROUPS = ('drain', 'forest', 'blight', 'cave', 'special')
PAIRS = ('forest-wood-chest', 'blight-relic-chest', 'forest-cave-door',
         'forest-bomb-wall', 'blight-cobweb', 'blight-cape-hole')


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    assert G.digest(source) == G.digest(target)


def native(path):
    with Image.open(path) as im:
        assert im.size == (240, 160), (path, im.size)
        return im.convert('RGB')


def board(rows, target, heading, columns=3):
    """Each row is one complete real framebuffer; no crops or painted pixels."""
    width, height = columns * 480, ((len(rows) + columns - 1) // columns) * 350 + 44
    out = Image.new('RGB', (width, height), G.BG)
    draw = ImageDraw.Draw(out)
    draw.text((10, 10), heading, font=TITLE, fill=G.FG)
    for index, (path, caption) in enumerate(rows):
        x, y = index % columns * 480, index // columns * 350 + 44
        out.paste(native(path).resize((480, 320), Image.Resampling.NEAREST), (x, y))
        draw.text((x + 8, y + 326), caption, font=FONT, fill=G.FG)
    out.save(target)


def copy_captures(source, target, report_name, expected_sha):
    report = read(source / report_name)
    assert report['rom_sha256'] == expected_sha
    assert not report.get('missing') and not report.get('failures')
    copy(source / report_name, target / report_name)
    for row in report['captures']:
        assert row.get('passed', True), row['name']
        paths = [row['name'] + '.gif', row['filmstrip'], *row['native_frames']]
        if row.get('image'):
            paths.append(row['image'])
        for relative in paths:
            copy(source / relative, target / relative)
        for relative in row['native_frames']:
            native(target / relative)
    return report


def comparisons(args, out, final_report):
    before = read(args.before_interactive / 'capture.json')
    old = {row['name']: row for row in before['captures']}
    new = {row['name']: row for row in final_report['captures']}
    copy(args.before_interactive / 'capture.json', out / 'baseline-capture.json')
    rows, matches = [], []
    for name in PAIRS:
        a, b = old[name], new[name]
        same = {key: a[key] == b[key] for key in
                ('seed', 'cell', 'target', 'position', 'facing', 'physical_contract', 'inputs')}
        same['camera'] = a['initial']['camera'] == b['initial']['camera']
        assert all(same.values()), (name, same)
        copy(args.before_interactive / a['image'], out / 'baseline' / a['image'])
        rows.extend([(out / 'baseline' / a['image'], 'BEFORE | ' + name),
                     (args.out / 'actual/interactive' / b['image'], 'REBOOT | ' + name)])
        entry = {'name': name, 'same_fixture': same,
                 'before': 'baseline/' + a['image'],
                 'after': '../actual/interactive/' + b['image']}
        if name in ('forest-wood-chest', 'blight-cobweb'):
            copy(args.before_interactive / (name + '.gif'), out / 'baseline' / (name + '.gif'))
            entry['animated_comparison'] = G.compare(
                out / 'baseline' / (name + '.gif'),
                args.out / 'actual/interactive' / (name + '.gif'), out / (name + '.gif'), name)
        matches.append(entry)
    board(rows, out / 'before-after.png', 'Actual mGBA / matched seed, cell, target, position and camera', 2)
    result = {'before_rom_sha256': before['rom_sha256'],
              'after_rom_sha256': final_report['rom_sha256'], 'cases': matches,
              'note': 'Initial viewpoints and terrain fixtures match. Later gameplay frames can differ with compact Bloom feet and revised sword reach.'}
    if args.first_review and (args.first_review / 'screens/review.json').exists():
        first = read(args.first_review / 'screens/review.json')
        early = {row['name']: row for row in first['captures']}
        final = read(args.review / 'screens/review.json')
        later = {row['name']: row for row in final['captures']}
        rows, processes = [], []
        for name in ('forest-cell-20-stage3', 'interior-cave', 'interior-hollow'):
            if name not in early:
                continue
            a, b = early[name], later[name]
            same = a['seed'] == b['seed'] and all(a['initial'][k] == b['initial'][k]
                    for k in ('area', 'cell', 'position', 'camera'))
            assert same, name
            dest = out / 'initial-candidate' / a['image']
            copy(args.first_review / 'screens' / a['image'], dest)
            rows.extend([(dest, 'INITIAL CANDIDATE | ' + name),
                         (args.out / 'actual/screens' / b['image'], 'FINAL CANDIDATE | ' + name)])
            processes.append({'name': name, 'matched_seed_cell_position_camera': same})
        if rows:
            board(rows, out / 'candidate-refinement.png', 'Actual mGBA / initial candidate versus final polish', 2)
        result['candidate_refinement'] = {'initial_rom_sha256': first['rom_sha256'], 'cases': processes}
    write(out / 'comparison-manifest.json', result)
    return result


def atlases(frozen, out):
    """Decode all compiled OBJ frames, including exact bag/portrait palettes."""
    r = Rom(frozen / 'bartgame.gba', frozen / 'bartgame.map', frozen / 'assets.h')
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    for name, index in sorted(r.sheet_names.items(), key=lambda x: x[1]):
        meta, data = r.sheet(name)
        count, frame_tiles, shape, size, bank, width, height = meta
        frames = count // frame_tiles
        prefix = 'F_' + name.upper() + '_'
        names = {value: key[len(prefix):].lower() for key, value in r.defs.items() if key.startswith(prefix)}
        columns = min(frames, 8)
        cell_w, cell_h = max(140, width * 2 + 8), height * 2 + 27
        atlas = Image.new('RGB', (max(720, columns * cell_w), 60 + ((frames + columns - 1) // columns) * cell_h), G.BG)
        draw = ImageDraw.Draw(atlas)
        draw.text((10, 8), 'COMPILED SOURCE / ' + name + ' / NOT emulator gameplay', font=TITLE, fill=G.FG)
        draw.text((10, 34), f'{frames} native {width}x{height} canvases / 2x nearest-neighbour / frame labels below', font=FONT, fill=G.FG)
        for frame in range(frames):
            raw = data[frame * frame_tiles * 32:(frame + 1) * frame_tiles * 32]
            palette_bank = r.read(r.symbols[name + '_frame_pal'] + frame, 1)[0] if name + '_frame_pal' in r.symbols else bank
            palette = r.read(r.symbols['pal_obj'] + palette_bank * 32, 32)
            if name == 'face':
                palette = r.read(r.symbols['pal_face'] + frame * 32, 32)
            if name == 'icon32':
                raw = r.read(r.symbols['icon32_exact_tiles'] + frame * frame_tiles * 32, frame_tiles * 32)
                palette = r.read(r.symbols['icon32_exact_pal'] + frame * 32, 32)
            colours = struct.unpack('<16H', palette)
            image = Image.new('RGB', (width, height), (34, 39, 43))
            pixels = image.load()
            for y in range(height):
                for x in range(width):
                    tile = (y // 8) * (width // 8) + x // 8
                    byte = raw[tile * 32 + (y % 8) * 4 + (x % 8) // 2]
                    ink = (byte >> (4 * (x & 1))) & 15
                    if ink:
                        word = colours[ink]
                        pixels[x, y] = tuple((value << 3) | (value >> 2)
                                             for value in ((word >> shift) & 31 for shift in (0, 5, 10)))
            x, y = frame % columns * cell_w, 60 + frame // columns * cell_h
            atlas.paste(image.resize((width * 2, height * 2), Image.Resampling.NEAREST), (x + 4, y))
            draw.text((x + 4, y + height * 2 + 3), f'{frame} {names.get(frame, "")}', font=FONT, fill=G.FG)
        atlas.save(out / (name + '.png'))
        entries.append({'sheet': name, 'id': index, 'frames': frames, 'canvas': [width, height], 'path': name + '.png'})
    write(out / 'index.json', {'rom_sha256': G.digest(frozen / 'bartgame.gba'),
          'method': 'Static compiled-ROM source decoding, NOT an emulator capture. Transparent pixels use neutral grey. Exact menu and per-portrait palettes included.',
          'sheets': entries, 'frame_count': sum(e['frames'] for e in entries)})
    return len(entries)


def reel(actual, out):
    clips = []
    def gif(folder, name):
        clips.append((actual / folder / (name + '.gif'), name, None))
    def still(folder, name, seconds=1):
        clips.append((actual / folder / (name + '.png'), name, seconds))
    for name in ('title-screen', 'drain-ladder', 'forest-cell-21-stage0',
                 'forest-cell-14-stage1', 'forest-cell-20-stage3',
                 'interior-cave', 'interior-hollow', 'interior-thicket'):
        gif('screens', name)
    for action in ('sword', 'shield-wood', 'lamp', 'bow'):
        for facing in 'nesw':
            gif('actions/drain', f'drain-{action}-{facing}')
    for background in ('forest', 'blight', 'cave'):
        for action in ('sword-n', 'shield-wood-n', 'lamp-n', 'bow-n', 'cape-e'):
            gif('actions/' + background, background + '-' + action)
    for name in ('drain-roll-e',):
        gif('actions/drain', name)
    for name in ('lift-carry-throw-bush', 'forest-ledge-jump', 'forest-drowning',
                 'forest-item-get-bow', 'drain-forest-transition'):
        gif('actions/special', name)
    for name in ('forest-wood-chest', 'forest-brass-chest', 'blight-relic-chest',
                 'forest-cave-door', 'forest-hollow-door', 'blight-thicket-door',
                 'cave-floor-switch', 'blight-bomb-wall', 'blight-cobweb', 'blight-cape-hole'):
        gif('interactive', name)
    for name in ('pause_items', 'pause_keys', 'pause_map_full', 'shop', 'dialogue_peddler', 'dialogue_gardener'):
        still('interface/ui', name)
    for name in ('enemy-knight', 'enemy-spitter'):
        gif('screens', name)
    if (actual / 'supplement/heart-full-view.gif').exists():
        gif('supplement', 'heart-full-view')
    else:
        gif('screens', 'heart-boss')
    for name in ('bloom-death-and-return', 'victory-screen'):
        gif('screens', name)
    proc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
            '-s', '480x342', '-r', '30', '-i', '-', '-an', '-c:v', 'libx264', '-crf', '16',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(out)], stdin=subprocess.PIPE)
    total, entries = 0, []
    try:
        for path, caption, seconds in clips:
            if seconds is None:
                frames, durations = G.load_gif(path)
            else:
                frames = [native(path).resize((480, 320), Image.Resampling.NEAREST)]
                durations = [seconds * 1000]
            n = round(sum(durations) * 30 / 1000)
            start, pos, end = total / 30, 0, 0
            for tick in range(n):
                target = tick * 1000 / 30
                while pos < len(frames) - 1 and target >= end + durations[pos]:
                    end += durations[pos]
                    pos += 1
                proc.stdin.write(G.label(frames[pos], 'ACTUAL mGBA | ' + caption).tobytes())
            total += n
            entries.append({'capture': str(path.relative_to(actual)), 'start_seconds': start,
                            'seconds': n / 30, 'presentation': 'still' if seconds else 'complete recorded clip'})
        proc.stdin.close()
        assert proc.wait() == 0
    except BaseException:
        proc.kill()
        proc.wait()
        raise
    return {'path': out.name, 'fps': 30, 'frames': total, 'seconds': total / 30, 'clips': entries,
            'note': 'Lossy silent H.264 convenience. Complete clips retain recorded timing; PNG/GIF originals remain authoritative.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--review', type=Path, required=True)
    ap.add_argument('--interface', type=Path, required=True)
    ap.add_argument('--frozen', type=Path, required=True)
    ap.add_argument('--before-interactive', type=Path, required=True)
    ap.add_argument('--first-review', type=Path)
    ap.add_argument('--supplement', type=Path, help='Optional same-ROM screen-capture directory with review.json')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--no-video', action='store_true')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for family in ('actual', 'comparisons', 'source-atlases'):
        if (args.out / family).exists():
            shutil.rmtree(args.out / family)
    actual = args.out / 'actual'
    sha = G.digest(args.frozen / 'bartgame.gba')
    freeze = read(args.frozen / 'freeze.json') if (args.frozen / 'freeze.json').exists() else None
    if freeze:
        assert freeze['rom_sha256'] == sha
        copy(args.frozen / 'freeze.json', actual / 'frozen-rom.json')
    index = read(args.review / 'index.json')
    assert index['rom_sha256'] == sha and not index['failures']
    copy(args.review / 'index.json', actual / 'index.json')
    screens = copy_captures(args.review / 'screens', actual / 'screens', 'review.json', sha)
    actions = [copy_captures(args.review / 'actions' / group, actual / 'actions' / group, 'suite.json', sha)
               for group in GROUPS]
    copy(args.review / 'actions/index.json', actual / 'actions/index.json')
    interactive = copy_captures(args.review / 'interactive', actual / 'interactive', 'capture.json', sha)
    supplement = (copy_captures(args.supplement, actual / 'supplement', 'review.json', sha)
                  if args.supplement else {'captures': []})
    for path in sorted((args.review / 'screens/ending-steps').glob('*.png')):
        native(path)
        copy(path, actual / 'screens/ending-steps' / path.name)
    interface_counts = {}
    for group in ('ui', 'hud', 'title'):
        count = 0
        for path in sorted((args.interface / group).glob('*')):
            if path.suffix == '.png':
                if Image.open(path).size != (240, 160):
                    continue  # exclude overview sheets and HUD-band crops
                native(path)
                count += 1
            elif path.suffix != '.json':
                continue
            copy(path, actual / 'interface' / group / path.name)
        interface_counts[group] = count
    interface_report = read(args.interface / 'validation.json')
    assert interface_report['rom_sha256'] == sha
    copy(args.interface / 'validation.json', actual / 'interface/validation.json')
    forest = [(actual / 'screens' / row['image'], row['name'].replace('forest-', '') + ' | seed ' + row['seed'])
              for row in screens['captures'] if row['name'].startswith('forest-cell-')]
    board(forest, args.out / 'forest-stages.png', '25 actual forest views / one procedural seed / stages 0 through 3', 5)
    scenes = ('title-screen', 'drain-ladder', 'forest-cell-21-stage0', 'forest-cell-14-stage1',
              'forest-cell-03-stage2', 'forest-cell-20-stage3', 'interior-cave', 'interior-hollow',
              'interior-thicket', 'enemy-knight', 'heart-boss', 'victory-screen')
    overview = [(actual / 'screens' / (name + '.png'), name) for name in scenes]
    overview.extend([(actual / 'interactive/forest-wood-chest.png', 'Tile-scale chest / compact Bloom'),
                     (actual / 'actions/special/forest-item-get-bow/frame-032.png', 'Item-get / bow held above Bloom'),
                     (actual / 'interface/ui/pause_items.png', 'Inventory / 32px menu icon canvases'),
                     (actual / 'interface/ui/dialogue_gardener.png', 'Dialogue / portrait'),
                     (actual / 'actions/special/lift-carry-throw-bush-sword-drop/frame-062.png', 'Cut bush / small dropped object in motion'),
                     (actual / 'actions/special/forest-death/frame-016.png', 'Actual contact / death animation'),
                     (actual / 'screens/bloom-death-and-return/frame-160.png', 'Death returns Bloom to the Drain'),
                     (actual / 'interface/hud/hud_counts.png', 'HUD / counts and tile-sized equipped icons')])
    if (actual / 'supplement/heart-full-view.png').exists():
        overview = [(actual / 'supplement/heart-full-view.png', 'Heart / natural boss at fighting distance')
                    if path.name == 'heart-boss.png' else (path, caption) for path, caption in overview]
    board(overview, args.out / 'overview.png', 'NATIVE ART REBOOT / complete actual mGBA frames / 2x nearest-neighbour', 4)
    interface_views = ('pause_items', 'pause_keys', 'pause_map_full', 'pause_zoom_full', 'shop',
                       'dialogue_peddler', 'dialogue_gatekeeper', 'dialogue_hermit',
                       'dialogue_nun', 'dialogue_gardener', 'dialogue_bloom_return')
    board([(actual / 'interface/ui' / (name + '.png'), name) for name in interface_views],
          args.out / 'interfaces.png', 'Actual mGBA / menus, shop and all six character portraits', 3)
    enemy_views = [(actual / 'screens' / (name + '.png'), name) for name in
                   ('enemy-slime', 'enemy-bat', 'enemy-beetle', 'enemy-spitter', 'enemy-knight', 'heart-boss')]
    if (actual / 'supplement/heart-full-view.png').exists():
        enemy_views[-1] = (actual / 'supplement/heart-full-view.png', 'heart-full-view')
    board(enemy_views,
          args.out / 'enemies.png', 'Actual mGBA / naturally generated enemy actors and the Heart', 3)
    (args.out / 'comparisons').mkdir(exist_ok=True)
    compared = comparisons(args, args.out / 'comparisons', interactive)
    source_count = atlases(args.frozen, args.out / 'source-atlases')
    captures = screens['captures'] + interactive['captures'] + [row for report in actions for row in report['captures']]
    all_captures = captures + supplement['captures']
    manifest = {'source_rom_sha256': sha, 'source_rom_bytes': (args.frozen / 'bartgame.gba').stat().st_size,
          'source_commit': freeze.get('source_commit') if freeze else None,
          'emulator': screens['emulator'], 'method': __doc__.strip(),
          'counts': {'screen_clips': len(screens['captures']), 'action_clips': sum(len(r['captures']) for r in actions),
                     'interactive_clips': len(interactive['captures']), 'canonical_clips': len(captures),
                     'all_clips': len(all_captures),
                     'supplemental_clips': len(supplement['captures']),
                     'interface_native_views': interface_counts, 'source_atlases': source_count,
                     'exact_palette_capture_gifs': sum(c['gif']['exact_palette'] for c in all_captures)},
          'palette_note': 'Original native PNG framebuffers are unchanged. GIFs are 2x nearest-neighbour with their original per-capture exact_palette/colour_count metadata. Combined comparison GIFs record any 256-colour quantization separately.',
          'fixture_note': index['method'], 'comparison_rom_sha256': compared['before_rom_sha256'],
          'excluded': 'No ROM, linker map, generated C header, mockup or painted concept image is included as actual gameplay evidence.'}
    if not args.no_video:
        manifest['video'] = reel(actual, args.out / 'play-reel.mp4')
    roots = ('actual', 'comparisons', 'source-atlases')
    names = ('overview.png', 'forest-stages.png', 'interfaces.png', 'enemies.png', 'play-reel.mp4')
    manifest['files'] = [{'path': str(path.relative_to(args.out)), 'bytes': path.stat().st_size, 'sha256': G.digest(path)}
                         for path in sorted(args.out.rglob('*')) if path.is_file() and
                         (path.relative_to(args.out).parts[0] in roots or path.name in names)]
    write(args.out / 'gallery-manifest.json', manifest)
    print(json.dumps({key: manifest[key] for key in ('source_rom_sha256', 'counts')}, indent=2))
    print('FILES', len(manifest['files']), 'BYTES', sum(f['bytes'] for f in manifest['files']))
    if 'video' in manifest:
        print('VIDEO_SECONDS', manifest['video']['seconds'])


if __name__ == '__main__':
    main()
