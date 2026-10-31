#!/usr/bin/env python3
"""Export complete native SOURCE catalogs for the five forest art studies.

These indexed assets, assembled material patches and fixed-hold source cycles
are not emulator captures. The separately frozen mGBA review establishes room
generation, layering, animation cadence and interactions in the running game.
"""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art'
BG, FIELD, FG, DIM = '#101820', '#283838', '#f0d898', '#b0c0a0'
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
VALID_SIZES = {(8, 8), (16, 16), (32, 32), (64, 64), (16, 8), (32, 8),
               (32, 16), (64, 32), (8, 16), (8, 32), (16, 32), (32, 64)}
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def label(draw, xy, value, color=FG):
    draw.fontmode = '1'
    draw.text(xy, str(value), fill=color, font=FONT)


def rgb(color):
    return tuple(int(color[n:n + 2], 16) for n in (1, 3, 5))


def paste(board, image, xy, scale=1):
    if scale != 1:
        image = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
    if image.mode == 'RGBA':
        board.paste(image, xy, image)
    else:
        board.paste(image, xy)


def silhouette(image):
    mask = image.getchannel('A')
    out = Image.new('RGBA', image.size, rgb(FG) + (0,))
    out.putalpha(mask)
    return out


def gray(image):
    out = image.convert('L').convert('RGBA')
    out.putalpha(image.getchannel('A'))
    return out


def indices(rows, size):
    w, h = size
    assert len(rows) == h and all(len(row) == w for row in rows), size
    values = [0 if value == '.' else int(value, 16) for row in rows for value in row]
    assert set(values) <= set(range(16))
    return values


def rgba(entry):
    w, h = entry['canvas']
    colors = entry['colors']
    qs = entry.get('quarter_colors')
    out = Image.new('RGBA', (w, h))
    values = []
    for n, ink in enumerate(entry['indices']):
        palette = qs[(n // w // 8) * 2 + n % w // 8] if qs else colors
        values.append(rgb(palette[ink]) + (255 if ink else 0,))
    out.putdata(values)
    return out


def indexed(entry):
    """Single-bank 4bpp indices, or explicit bank+nibble for quarter palettes."""
    w, h = entry['canvas']
    qs = entry.get('quarter_colors')
    out = Image.new('P', (w, h))
    colors = sum(qs, []) if qs else entry['colors']
    palette = [channel for color in colors for channel in rgb(color)]
    out.putpalette(palette + [0] * (768 - len(palette)))
    if qs:
        out.putdata([ink + 16 * ((n // w // 8) * 2 + n % w // 8)
                     for n, ink in enumerate(entry['indices'])])
        out.info['transparency'] = bytes(0 if n % 16 == 0 else 255 for n in range(64))
    else:
        out.putdata(entry['indices'])
        out.info['transparency'] = 0
    return out


def assert_palette(colors):
    assert len(colors) == 16
    assert all(color.startswith('#') and len(color) == 7 and all(channel % 8 == 0 for channel in rgb(color))
               for color in colors), colors


def required(inventory):
    need = inventory['required']
    # The final task scope explicitly includes the shared ground/carry identity
    # of the four liftables. Their original anchors and held-item mechanics stay.
    frames = need['sprite_frames'] + need.get('conditional_shared_lift_frames', [])
    return set(need['bg_names']), {(row['sheet'], row['frame']) for row in frames}


def metadata(inventory):
    tiles = {row['name']: row for row in inventory['tiles']}
    frames = {(sh['name'], row['name']): {**row, 'sheet_scope': sh.get('scope')}
              for sh in inventory['sheets'] for row in sh['frames']}
    return tiles, frames


def worker(args):
    # Imports must occur after BART_FOREST is fixed in this isolated process.
    os.environ['BART_FOREST'] = str(args.profile)
    sys.path.insert(0, str(ART))
    import palettes
    import sprites
    import tiles

    inv = json.loads(args.inventory.read_text())
    need_tiles, need_sprites = required(inv)
    tile_meta, frame_meta = metadata(inv)
    bg_colors, obj_colors = dict(palettes.BG_PALETTES), dict(palettes.OBJ_PALETTES)
    for colors in list(bg_colors.values()) + list(obj_colors.values()):
        assert_palette(colors)
    entries = []
    coverage_tiles = {row['name']: row for row in tiles.COVERAGE}
    coverage_frames = {(row['sheet'], row['frame']): row for row in sprites.COVERAGE}
    for tile_id, mt in enumerate(tiles.METATILES):
        if mt['name'] not in need_tiles:
            continue
        meta = tile_meta[mt['name']]
        assert tile_id == meta['id'], (mt['name'], tile_id, meta['id'])
        frames = mt.get('frames') or [mt['art']]
        assert len(frames) == meta['frames'], mt['name']
        for phase, rows in enumerate(frames):
            entry = {'kind': 'tile', 'name': mt['name'], 'id': tile_id, 'phase': phase,
                     'family': meta.get('family', 'terrain'), 'scope': meta.get('scope'),
                     'category': meta.get('category', meta.get('family', 'terrain')),
                     'canvas': [16, 16], 'type': mt['type'], 'coll': mt.get('coll', 0),
                     'prop': mt.get('prop', 0), 'anim_speed': mt.get('anim_speed', 8),
                     'glitter': bool(mt.get('glitter')),
                     'palette': mt['pal'], 'colors': bg_colors[mt['pal']],
                     'indices': indices(rows, (16, 16)), 'owner': coverage_tiles[mt['name']]['owner']}
            if mt.get('qpals'):
                assert len(mt['qpals']) == 4
                entry['quarter_palettes'] = mt['qpals']
                entry['quarter_colors'] = [bg_colors[name] for name in mt['qpals']]
            entries.append(entry)
    contexts = {}
    for sheet_id, sh in enumerate(sprites.SHEETS):
        for frame_id, (name, rows) in enumerate(sh['frames'].items()):
            key = sh['name'], name
            if key not in need_sprites and not (sh['name'] in ('hero', 'beetle', 'bat', 'spitter', 'knight', 'boss')
                                               and name in ('idle_s', 'stand_s', 'walk_s1', 'fly1', 'pulse1')):
                continue
            colors = obj_colors[sh.get('frame_pal', {}).get(name, sh['pal'])]
            palette_source = 'OBJ_PALETTES'
            if sh['name'] == 'face':
                # Dialogue loads the selected portrait ramp into its resident
                # slot; the sheet's default OBJ alias is not the visible ramp.
                colors = palettes.FACE_PALETTES[frame_id]
                palette_source = f'FACE_PALETTES[{frame_id}]'
            exact = sh.get('exact_frames', {}).get(name)
            if exact:
                rows, colors = exact
            assert_palette(colors)
            entry = {'kind': 'sprite', 'sheet': sh['name'], 'name': name, 'id': frame_id,
                     'sheet_id': sheet_id, 'phase': 0, 'canvas': [sh['w'], sh['h']],
                     'palette': sh.get('frame_pal', {}).get(name, sh['pal']),
                     'palette_source': palette_source,
                     'colors': colors, 'indices': indices(rows, (sh['w'], sh['h'])),
                     'owner': coverage_frames[key]['owner']}
            assert tuple(entry['canvas']) in VALID_SIZES, key
            if key in need_sprites:
                meta = frame_meta[key]
                assert frame_id == meta['id'], (key, frame_id, meta['id'])
                entry.update(family=meta.get('family', sh['name']), category='obj-' + sh['name'],
                             scope=meta.get('scope'))
                entries.append(entry)
            else:
                contexts.setdefault(sh['name'], entry)
    assert {entry['name'] for entry in entries if entry['kind'] == 'tile'} == need_tiles
    assert {(entry['sheet'], entry['name']) for entry in entries if entry['kind'] == 'sprite'} == need_sprites
    for entry in entries:
        entry['index_sha256'] = hashlib.sha256(bytes(entry['indices'])).hexdigest()
        entry['rgba_sha256'] = hashlib.sha256(rgba(entry).tobytes()).hexdigest()
    title = 'Current forest reference' if args.profile == 0 else f'Forest concept {args.profile}'
    try:
        import forest_concepts as studies
        assert studies.VARIANT == args.profile, (studies.VARIANT, args.profile)
        title = studies.NAMES[args.profile]
    except ImportError:
        assert args.profile == 0, 'Positive source profiles require the integrated forest_concepts configuration.'
    write(args.snapshot, {'profile': args.profile, 'label': title, 'entries': entries,
                          'context': contexts, 'bg_colors': bg_colors})


def entry_key(entry):
    return (entry['kind'], entry.get('sheet', ''), entry['name'], entry['phase'])


def entry_name(entry):
    return ((entry['sheet'] + ' / ') if entry['kind'] == 'sprite' else '') + entry['name'] + (
        f' [{entry["phase"]}]' if entry['kind'] == 'tile' else '')


def slug(name):
    return ''.join(c if c.isalnum() or c in '-_' else '-' for c in name).strip('-')


def export_native(snapshot, out):
    exports = []
    for entry in snapshot['entries']:
        image = rgba(entry)
        category = 'bg' if entry['kind'] == 'tile' else 'obj/' + entry['sheet']
        stem = entry['name'] + (f'-phase{entry["phase"]:02}' if entry['kind'] == 'tile' else '')
        base = out / 'native' / category
        base.mkdir(parents=True, exist_ok=True)
        path_i, path_rgba = base / (stem + '-indexed.png'), base / (stem + '.png')
        indexed(entry).save(path_i)
        image.save(path_rgba)
        assert Image.open(path_i).convert('RGBA').tobytes() == image.tobytes(), path_i
        assert Image.open(path_rgba).convert('RGBA').tobytes() == image.tobytes(), path_rgba
        exports.append({**{key: value for key, value in entry.items() if key not in ('indices', 'colors', 'quarter_colors')},
                        'colors_rgb555': entry['colors'],
                        **({'quarter_colors_rgb555': entry['quarter_colors']} if entry.get('quarter_colors') else {}),
                        'native_indexed_png': str(path_i.relative_to(out)),
                        'native_rgba_png': str(path_rgba.relative_to(out)),
                        'indices_used': sorted(set(entry['indices'])),
                        'painted_bounds': image.getbbox(), 'png_roundtrip_verified': True})
    return exports


def atlas(entries, title):
    max_w, max_h = max(entry['canvas'][0] for entry in entries), max(entry['canvas'][1] for entry in entries)
    cw, ch, cols = max(188, max_w * 3 + max_w + 32), max_h * 3 + 58, 5
    board = Image.new('RGB', (cols * cw, 54 + math.ceil(len(entries) / cols) * ch), BG)
    d = ImageDraw.Draw(board)
    label(d, (8, 5), title)
    label(d, (8, 23), 'Complete SOURCE frames; native 1x + nearest-neighbour 3x. No emulator output.', DIM)
    for n, entry in enumerate(entries):
        x, y = n % cols * cw, 54 + n // cols * ch
        image = rgba(entry)
        # Labels are outside game pixels; long identifiers wrap to two rows.
        name = entry_name(entry)
        limit = max(16, int((cw - 10) / 6))
        label(d, (x + 5, y + 2), name[:limit])
        if len(name) > limit:
            label(d, (x + 5, y + 15), name[limit:limit * 2], DIM)
        base = y + ch - 23
        d.rectangle((x + 5, y + 31, x + 8 + image.width * 3, base + 1), fill=FIELD)
        paste(board, image, (x + 7, base - image.height * 3), 3)
        paste(board, image, (x + max_w * 3 + 22, base - image.height))
        label(d, (x + 5, base + 5), f'{entry.get("sheet", "BG")}:{entry["id"]} / {entry["palette"]}', DIM)
    return board


GROUPS = {
    'oak': (2, ['tree_top_nw', 'tree_top_ne', 'tree_mid_w', 'tree_mid_e', 'tree_trunk_w', 'tree_trunk_e']),
    'lantern-tree': (2, [f'tree2_{n}' for n in range(6)]),
    'birch': (2, [f'birch_{n}' for n in range(6)]),
    'fir': (2, [f'fir_{n}' for n in range(6)]),
    'sick-tree': (2, [f'sicktree_{n}' for n in range(6)]),
    'dead-tree': (2, [f'btree_{n}' for n in range(6)]),
    'reserved-rotten-extensions': (3, [f'btree_{n}' for n in range(6, 12)]),
    'wall-blight-tree': (2, [f'forest_blight_tree{n}' for n in range(6)]),
    'great-tree': (3, [f'gtree_{n}' for n in range(12)]),
    'great-lantern-tree': (3, [f'gtree2_{n}' for n in range(12)]),
    'meadow': (3, [f'meadow_{n}' for n in range(9)]),
    'clover': (2, [f'clover_{n}' for n in range(4)]),
    'mushroom-ring': (2, [f'shroomring_{n}' for n in range(4)]),
    'large-boulder': (2, [f'gboulder_{n}' for n in range(4)]),
    'tree-rock': (2, [f'treerock_{n}' for n in range(4)]),
    'fallen-log': (2, [f'hlog_{n}' for n in range(2)]),
    'raft': (2, [f'raft_{n}' for n in range(4)]),
}


def lookup(snapshot):
    return {(e['name'], e['phase']): e for e in snapshot['entries'] if e['kind'] == 'tile'}


def tile(snapshot, name, phase=0):
    found = lookup(snapshot)
    matches = [entry for (n, _), entry in found.items() if n == name]
    assert matches, (snapshot['profile'], name)
    entry = found[(name, phase % len(matches))]
    return rgba(entry)


def group(snapshot, key, phase=0):
    cols, names = GROUPS[key]
    out = Image.new('RGBA', (16 * cols, 16 * math.ceil(len(names) / cols)))
    for n, name in enumerate(names):
        image = tile(snapshot, name, phase)
        out.paste(image, (n % cols * 16, n // cols * 16), image)
    return out


def scene_patch(snapshot, stage, phase=0):
    """A disclosed 15x10 source material test, not a generated game room."""
    out = Image.new('RGBA', (240, 160))
    floor = 'moss0'
    for y in range(10):
        for x in range(15):
            image = tile(snapshot, floor, phase)
            out.paste(image, (x * 16, y * 16), image)
    # A small path forks toward the opening. Its western arm crosses one pond.
    path_cells = set([(7, y) for y in range(2, 10)] + [(x, 7) for x in range(8)]
                     + [(x, 4) for x in range(7, 12)] + [(x, 8) for x in range(7, 14)])
    available = {name for name, _ in lookup(snapshot)}
    for x, y in path_cells:
        mask = sum(bit for bit, dx, dy in ((1, 0, -1), (2, 1, 0), (4, 0, 1), (8, -1, 0))
                   if (x + dx, y + dy) not in path_cells)
        edge = f'pedge_{mask:x}'
        image = tile(snapshot, edge if mask and edge in available else 'path', phase)
        out.paste(image, (x * 16, y * 16), image)
    canopy = 'canopy_s' if stage == 0 else 'canopy_blight'
    for x in range(15):
        image = tile(snapshot, canopy, phase)
        out.paste(image, (x * 16, 0), image)
    for y in range(1, 7):
        for x in (0, 14):
            image = tile(snapshot, 'canopy' if stage == 0 else 'canopy_blight', phase)
            out.paste(image, (x * 16, y * 16), image)
    for x, y in ((12, 3), (13, 3), (13, 4)):
        image = tile(snapshot, 'canopy' if stage == 0 else 'canopy_blight', phase)
        out.paste(image, (x * 16, y * 16), image)
    for gx, key in [(16, 'oak' if stage == 0 else 'sick-tree'), (168, 'fir' if stage < 2 else 'dead-tree')]:
        image = group(snapshot, key, phase)
        out.paste(image, (gx, 20), image)
    if stage:
        for x, y in ((5, 2), (11, 8), (6, 5)):
            image = tile(snapshot, 'forest_rot3' if stage == 1 else 'blight_floor', phase)
            out.paste(image, (x * 16, y * 16), image)
    # Connected banks and usable land at both ends make the bridge legible.
    pond = [['water_9', 'water_1', 'water_3'], ['water_8', 'water', 'water_2'], ['water_c', 'water_4', 'water_6']]
    names = available
    for yy, row in enumerate(pond):
        for xx, name in enumerate(row):
            image = tile(snapshot, name if name in names else 'water', phase)
            out.paste(image, ((xx + 2) * 16, (yy + 6) * 16), image)
    for x in range(2, 5):
        image = tile(snapshot, 'bridge', phase)
        out.paste(image, (x * 16, 112), image)
    # Keep functional objects identical across stages: blight does not
    # automatically upgrade treasure, change a gate's verb or move an entry.
    image = tile(snapshot, 'crack', phase)
    out.paste(image, (112, 48), image)
    for name, xy in [('bush', (80, 80)), ('rock_small', (160, 128)), ('pit', (144, 96)),
                     ('moss_flowers', (96, 128))]:
        image = tile(snapshot, name, phase)
        out.paste(image, xy, image)
    source = {(entry.get('sheet'), entry['name']): entry for entry in snapshot['entries'] if entry['kind'] == 'sprite'}
    for key, xy in [(('interactivechest', 'brass_closed'), (160, 96)),
                    (('interactiveentry', 'hollow'), (192, 64))]:
        if key in source:
            image = rgba(source[key]); out.paste(image, xy, image)
    if 'hero' in snapshot['context']:
        image = rgba(snapshot['context']['hero']); out.paste(image, (104, 80), image)
    return out.convert('RGB')


def exact_gif(frames, hold, path):
    colors = sorted({color for frame in frames for _, color in frame.getcolors(frame.width * frame.height)})
    if len(colors) > 256:
        path.unlink(missing_ok=True)
        return {'omitted': True, 'reason': 'Exact RGB union exceeds GIF palette; PNG phases remain exact.',
                'colors': len(colors), 'frames': len(frames), 'hold_ms': hold}
    table = {color: n for n, color in enumerate(colors)}
    pal = [channel for color in colors for channel in color]
    converted = []
    for frame in frames:
        item = Image.new('P', frame.size)
        item.putpalette(pal + [0] * (768 - len(pal)))
        raw = frame.tobytes()
        item.putdata([table[color] for color in zip(raw[0::3], raw[1::3], raw[2::3])])
        converted.append(item)
    converted[0].save(path, save_all=True, append_images=converted[1:], duration=hold, loop=0,
                      optimize=False, disposal=2)
    with Image.open(path) as im:
        decoded = [(frame.convert('RGB').copy(), frame.info['duration']) for frame in ImageSequence.Iterator(im)]
    assert len(decoded) == len(frames), (path, len(decoded), len(frames))
    assert all(actual.tobytes() == expected.tobytes() and duration == hold
               for (actual, duration), expected in zip(decoded, frames)), path
    return {'exact_palette': True, 'colors': len(colors), 'frames': len(frames),
            'hold_ms': hold, 'decoded_rgb_verified': True}


def assembly_board(snapshot, phase=0):
    valid = set(name for name, _ in lookup(snapshot))
    groups = [name for name, (_, names) in GROUPS.items() if set(names) <= valid]
    cw, ch, cols = 176, 200, 5
    out = Image.new('RGB', (cols * cw, 54 + math.ceil(len(groups) / cols) * ch), BG)
    d = ImageDraw.Draw(out)
    label(d, (8, 5), f'{snapshot["label"]} / complete SOURCE groups')
    label(d, (8, 23), 'Adjacent 16x16 metatiles assembled at native 1x and exact 2x; not emulator output.', DIM)
    for n, name in enumerate(groups):
        x, y = n % cols * cw, 54 + n // cols * ch
        image = group(snapshot, name, phase)
        label(d, (x + 6, y + 4), name)
        paste(out, image, (x + 7, y + 27), 2)
        paste(out, image, (x + 111, y + 27 + image.height))
        label(d, (x + 6, y + 167), f'{image.width}x{image.height} native', DIM)
    return out


def diagnostics(snapshot):
    names = ['moss0', 'path', 'canopy_s', 'canopy_blight', 'blight_floor', 'water', 'pit', 'crack',
             'web', 'door_locked', 'myst_switch', 'myst_switch_down', 'bush', 'rock_small', 'boulder']
    found = lookup(snapshot)
    names = [name for name in names if (name, 0) in found]
    out = Image.new('RGB', (840, 54 + len(names) * 70), BG)
    d = ImageDraw.Draw(out)
    label(d, (8, 5), f'{snapshot["label"]} / SOURCE value and contour checks')
    label(d, (8, 23), 'Color, grayscale and silhouette are inspection views; captions sit outside all native images.', DIM)
    for n, name in enumerate(names):
        y = 54 + n * 70
        image = rgba(found[(name, 0)])
        label(d, (8, y + 20), name)
        for x, variant in [(220, image), (330, gray(image)), (440, silhouette(image))]:
            d.rectangle((x - 2, y + 7, x + 50, y + 60), fill=FIELD)
            paste(out, variant, (x, y + 8), 3)
        label(d, (550, y + 12), f'{found[(name, 0)]["type"]} / {found[(name, 0)]["palette"]}', DIM)
        paste(out, image, (550, y + 36))
    return out


COMPARISONS = {
    'floors-and-transitions': ['moss0', 'moss_flowers', 'tall_grass', 'path', 'pedge_3', 'verge_6',
                              'shore_6', 'moss_blight', 'forest_rot3', 'rot_38', 'blight_ground',
                              'blight_floor', 'blight_vein'],
    'water-crossings-and-depth': ['water', 'water_9', 'water_c1', 'water_lily', 'waterfall',
                                 'blight_pool', 'bridge', 'bridge_v', 'ledge_s', 'pit', 'forest_blight_pit'],
    'canopy-and-forest-structure': ['canopy', 'canopy_s', 'canopy_n', 'canopy_blight', 'canopy_blight_lit',
                                   'forest_blight_tree0', 'blight_wall', 'blight_wall2', 'blight_wall_lit'],
    'interactions-and-ground-objects': ['bush', 'rock_small', 'boulder', 'crack', 'web', 'door_locked',
                                       'door_open', 'myst_switch', 'myst_switch_down', 'torch', 'torch_lit',
                                       'myst_spring', 'relic', 'shrine_plate', 'stump', 'log', 'myst_pot'],
    'interior-materials': ['cave_floor0', 'cave_floor1', 'cave_wall', 'cave_face', 'cave_exit',
                           'hollow_floor0', 'hollow_wall', 'hollow_face', 'hollow_exit',
                           'thicket_floor0', 'thicket_wall', 'thicket_face', 'thicket_exit'],
}


def comparison_board(snapshots, title, samples):
    # Samples are either literal tile names, assembled group keys, or sheet/frame pairs.
    cw, left = 236, 192
    rows = []
    for sample in samples:
        images = []
        for snapshot in snapshots:
            if isinstance(sample, tuple):
                matches = [entry for entry in snapshot['entries'] if entry['kind'] == 'sprite'
                           and (entry['sheet'], entry['name']) == sample]
                image = rgba(matches[0])
            elif sample in GROUPS:
                image = group(snapshot, sample)
            else:
                image = tile(snapshot, sample)
            images.append(image)
        rows.append((sample, images, max(118, max(image.height for image in images) * 2 + 40)))
    out = Image.new('RGB', (left + cw * len(snapshots), 80 + sum(row[2] for row in rows)), BG)
    d = ImageDraw.Draw(out)
    label(d, (8, 5), f'FIVE FOREST STUDIES / SOURCE comparison / {title}')
    label(d, (8, 23), 'Native 1x + exact 2x on matching grass swatches (portraits neutral); not emulator output.', DIM)
    for n, snapshot in enumerate(snapshots):
        x = left + n * cw
        label(d, (x + 6, 48), f'#{snapshot["profile"]} {snapshot["label"]}'[:34])
    y = 80
    for sample, images, ch in rows:
        label(d, (6, y + 7), '/'.join(sample) if isinstance(sample, tuple) else sample)
        for n, image in enumerate(images):
            x = left + n * cw
            context = FIELD if isinstance(sample, tuple) and sample[0] == 'face' else tile(snapshots[n], 'moss0').getpixel((8, 8))[:3]
            d.rectangle((x + 2, y + 12, x + 14 + image.width * 2, y + 24 + image.height * 2), fill=context)
            d.rectangle((x + 146, y + 12 + image.height, x + 158 + image.width,
                         y + 24 + image.height * 2), fill=context)
            paste(out, image, (x + 8, y + 18), 2)
            paste(out, image, (x + 152, y + 18 + image.height))
        y += ch
    return out


def complete_native_matrix(snapshots):
    """Every required phase at 1x, in matching cells across the five columns."""
    categories = defaultdict(list)
    for entry in snapshots[0]['entries']:
        categories[entry['category']].append(entry_key(entry))
    maps = [{entry_key(e): e for e in snapshot['entries']} for snapshot in snapshots]
    left, cw, header = 198, 224, 80
    rows = []
    for category, keys in categories.items():
        width = max(maps[0][key]['canvas'][0] for key in keys)
        height = max(maps[0][key]['canvas'][1] for key in keys)
        cols = max(1, (cw - 16) // (width + 4))
        rows.append((category, keys, width + 4, height + 4, cols,
                     24 + math.ceil(len(keys) / cols) * (height + 4)))
    out = Image.new('RGB', (left + len(snapshots) * cw, header + sum(row[-1] for row in rows)), BG)
    d = ImageDraw.Draw(out)
    label(d, (8, 5), 'COMPLETE FOREST SOURCE / every required native frame, 1x / not emulator output')
    label(d, (8, 23), 'Same IDs/phases in every concept column; grass context under transparency, neutral portrait fields.', DIM)
    for n, snapshot in enumerate(snapshots):
        label(d, (left + n * cw + 6, 49), f'#{snapshot["profile"]} {snapshot["label"]}')
    y, panels = header, []
    for category, keys, cellw, cellh, cols, rowh in rows:
        words = category.replace('_', ' ').replace('-', ' ').split()
        line, lines = '', []
        for word in words:
            if line and FONT.getlength(line + ' ' + word) > left - 16:
                lines.append(line); line = word
            else:
                line = (line + ' ' + word).strip()
        lines.append(line)
        for i, line in enumerate(lines):
            label(d, (8, y + 4 + i * 14), line)
        label(d, (8, y + 8 + len(lines) * 14), f'{len(keys)} frame instances', DIM)
        for profile_index, snapshot in enumerate(snapshots):
            context = rgb(FIELD) if category == 'obj-face' else tile(snapshot, 'moss0').getpixel((8, 8))[:3]
            for n, key in enumerate(keys):
                entry = maps[profile_index][key]
                image = rgba(entry)
                x, yy = left + profile_index * cw + 8 + n % cols * cellw, y + 24 + n // cols * cellh
                expected = Image.new('RGB', image.size, context)
                paste(expected, image, (0, 0))
                out.paste(expected, (x, yy))
                assert out.crop((x, yy, x + image.width, yy + image.height)).tobytes() == expected.tobytes()
                panels.append({'profile': snapshot['profile'], 'key': list(key),
                               'rectangle': [x, yy, x + image.width, yy + image.height],
                               'native_index_sha256': entry['index_sha256'],
                               'native_rgba_sha256': entry['rgba_sha256'],
                               'context_rgb': context, 'copied_native_pixels_verified': True})
        y += rowh
    return out, {'source_only': True, 'scale': 1, 'panels': panels,
                 'note': 'Literal native source composites, not a generated room or emulator capture. Captions/gutters are external.'}


def motion_board(snapshot, names, phase, hold):
    out = Image.new('RGB', (max(720, 112 * len(names)), 166), BG)
    d = ImageDraw.Draw(out)
    label(d, (8, 5), f'{snapshot["label"]} / SOURCE cycle phase {phase}')
    label(d, (8, 23), f'Fixed {hold}ms inspection holds, not the game clock. Native animation timing is preserved in the ROM.', DIM)
    for n, name in enumerate(names):
        x = n * 112
        image = tile(snapshot, name, phase)
        label(d, (x + 4, 49), name[:17])
        paste(out, image, (x + 6, 74), 3)
        paste(out, image, (x + 72, 106))
    return out


STATE_PAIRS = [
    ('Bombable stone', 'crack', 'path'), ('Burnable web', 'web', 'moss0'),
    ('Key gate', 'door_locked', 'door_open'), ('Pressure plate', 'myst_switch', 'myst_switch_down'),
    ('Candle censer', 'torch', 'torch_lit'),
    ('Wooden chest', ('interactivechest', 'wooden_closed'), ('interactivechest', 'wooden_open')),
    ('Brass chest', ('interactivechest', 'brass_closed'), ('interactivechest', 'brass_open')),
    ('Relic chest', ('interactivechest', 'relic_closed'), ('interactivechest', 'relic_open')),
    ('Cave entrance', ('interactiveentry', 'cave_closed'), ('interactiveentry', 'cave')),
    ('Hollow entrance', ('interactiveentry', 'hollow_closed'), ('interactiveentry', 'hollow')),
    ('Thicket entrance', ('interactiveentry', 'thicket_closed'), ('interactiveentry', 'thicket')),
]


def state_board(snapshot, state, hold):
    cw, ch, cols = 208, 184, 4
    out = Image.new('RGB', (cw * cols, 54 + math.ceil(len(STATE_PAIRS) / cols) * ch), BG)
    d = ImageDraw.Draw(out)
    label(d, (8, 5), f'{snapshot["label"]} / SOURCE interaction state catalog / state {state + 1}')
    label(d, (8, 23), f'{hold}ms review hold; paired states, not a timed destruction or activation sequence.', DIM)
    sprites = {(e['sheet'], e['name']): e for e in snapshot['entries'] if e['kind'] == 'sprite'}
    for n, (title, first, second) in enumerate(STATE_PAIRS):
        x, y = n % cols * cw, 54 + n // cols * ch
        label(d, (x + 6, y + 4), title)
        item = (first, second)[state]
        image = rgba(sprites[item]) if isinstance(item, tuple) else tile(snapshot, item)
        base = y + ch - 22
        d.rectangle((x + 5, base - image.height * 2 - 2, x + 9 + image.width * 2, base + 1), fill=FIELD)
        paste(out, image, (x + 7, base - image.height * 2), 2)
        paste(out, image, (x + 122, base - image.height))
        label(d, (x + 6, base + 5), item[-1] if isinstance(item, tuple) else item, DIM)
    return out


def make_variant(snapshot, baseline, out, hold):
    out.mkdir(parents=True, exist_ok=True)
    exports = export_native(snapshot, out)
    families = defaultdict(list)
    for entry in snapshot['entries']:
        category = str(entry['category'])
        families[category].append(entry)
    atlas_paths = []
    (out / 'atlases').mkdir(exist_ok=True)
    for family, entries in sorted(families.items()):
        # Avoid one unreadably tall whole-game atlas; every family and phase remains covered.
        for part in range(math.ceil(len(entries) / 100)):
            suffix = f'-{part + 1:02}' if len(entries) > 100 else ''
            path = out / 'atlases' / (slug(family) + suffix + '-source.png')
            atlas(entries[part * 100:(part + 1) * 100], f'#{snapshot["profile"]} {snapshot["label"]} / {family.replace("_", " ")}').save(path)
            atlas_paths.append({'family': family, 'path': str(path.relative_to(out)),
                                'frame_keys': [list(entry_key(e)) for e in entries[part * 100:(part + 1) * 100]]})
    assembly_board(snapshot).save(out / 'assembled-groups-source.png')
    diagnostics(snapshot).save(out / 'value-contour-diagnostics-source.png')
    stages = []
    board = Image.new('RGB', (720, 206), BG)
    d = ImageDraw.Draw(board)
    label(d, (8, 5), f'#{snapshot["profile"]} {snapshot["label"]} / SOURCE material test patches, not generated rooms or mGBA')
    for n, title in enumerate(('Healthy', 'Mixed blight', 'Deep blight')):
        patch = scene_patch(snapshot, n)
        patch.save(out / f'material-patch-stage{n}-source.png')
        board.paste(patch, (n * 240, 46))
        label(d, (n * 240 + 6, 27), title)
        stages.append({'stage': title, 'path': f'material-patch-stage{n}-source.png',
                       'canvas': [240, 160], 'layout': 'Disclosed source-only 15x10 material/semantic test; not generated game geometry.'})
    board.save(out / 'healthy-mixed-deep-source.png')
    animations = []
    motion_groups = {
        'animated-materials': ('water', 'waterfall', 'water_lily', 'blight_pool', 'torch_lit', 'myst_spring'),
        'animated-blight-details': ('canopy_lantern', 'canopy_blight2', 'blight_ground2', 'blight_vein',
                                    'blight_floor2', 'blight_mist', 'blight_wall_lit', 'forest_blight_pit'),
    }
    for group_name, candidates in motion_groups.items():
        animated = [name for name in candidates if len([e for e in snapshot['entries']
                    if e['kind'] == 'tile' and e['name'] == name]) > 1]
        if not animated:
            continue
        count = math.lcm(*(len([e for e in snapshot['entries'] if e['kind'] == 'tile' and e['name'] == name]) for name in animated))
        count = min(24, count)
        frames = [motion_board(snapshot, animated, phase, hold) for phase in range(count)]
        for phase, frame in enumerate(frames):
            frame.save(out / f'{group_name}-phase{phase:02}-source.png')
        path = out / f'{group_name}-source.gif'
        animations.append({'path': path.name, 'tiles': animated, **exact_gif(frames, hold, path)})
    states = [state_board(snapshot, state, hold) for state in (0, 1)]
    for state, image in enumerate(states):
        image.save(out / f'interaction-states-phase{state:02}-source.png')
    path = out / 'interaction-states-source.gif'
    animations.append({'path': path.name, 'kind': 'Source state-pair catalog; not engine event timing.',
                       'pairs': STATE_PAIRS, **exact_gif(states, hold, path)})
    before = {entry_key(entry): entry for entry in baseline['entries']}
    changes = []
    for entry in snapshot['entries']:
        key = entry_key(entry)
        prior = before[key]
        changes.append({'key': list(key), 'indices_changed': entry['index_sha256'] != prior['index_sha256'],
                        'rgba_changed': entry['rgba_sha256'] != prior['rgba_sha256'],
                        'owner': entry['owner']})
    report = {'profile': snapshot['profile'], 'label': snapshot['label'], 'source_only': True,
              'frame_count': len(exports), 'bg_frame_count': sum(e['kind'] == 'tile' for e in exports),
              'bg_metatile_count': len({e['name'] for e in exports if e['kind'] == 'tile'}),
              'sprite_frame_count': sum(e['kind'] == 'sprite' for e in exports),
              'frames': exports, 'atlases': atlas_paths, 'stages': stages, 'animations': animations,
              'baseline_comparison': changes, 'baseline_profile': baseline['profile'],
              'shared_lift_frames_included': True,
              'note': 'This is complete catalog coverage, including protected context where the inventory requests it and the four explicitly selected ground/carry liftable identities. Catalog inclusion does not claim every source frame was redrawn.'}
    phases = defaultdict(list)
    for entry in snapshot['entries']:
        if entry['kind'] == 'tile':
            phases[entry['name']].append(entry)
    report['static_painted_phase_tiles'] = [name for name, entries in phases.items()
                                           if len(entries) > 1 and len({e['index_sha256'] for e in entries}) == 1]
    report['retained_compatibility_notes'] = [
        'Many former tree-species IDs share two crown arrangements and one bare skeleton per concept by design.',
        'Unplaced btree_6 through btree_11 root-extension contracts are intentionally retired to exact quiet grass.',
        'Retained Sister Mary Grace and Brother Mark body IDs alias the Nun and Hermit; they are not new spawned characters.',
        'Some allocated soil, root and pit-rim phases deliberately share static paintings; source phase catalogs do not imply blinking terrain.',
    ]
    lines = [f'# {snapshot["profile"]}. {snapshot["label"]}: native source catalog', '',
             '**SOURCE artwork and assembly tests; these are not emulator captures.**', '',
             '![Healthy, mixed and deep source material patches](healthy-mixed-deep-source.png)', '',
             'The 240×160 material patches use one disclosed source-only 15×10 layout to compare floor, forest mass, '
             'water crossing and interaction hierarchy. They do not reproduce a generated room. Actual room views and '
             'gameplay timing are published separately.', '',
             '[Assembled complete groups](assembled-groups-source.png) · '
             '[Value and contour diagnostics](value-contour-diagnostics-source.png) · '
             '[Native coverage and hashes](source-manifest.json)', '',
             'Tree groups include both raised transparent canopy cells and opaque grass-bearing ground cells. '
             'Their rectangular floor substrates are shown literally on the raw group sheet; the source material '
             'patches and separate actual-room views show how they meet surrounding ground.', '',
             f'Complete inventory: {report["bg_metatile_count"]} BG metatiles / {report["bg_frame_count"]} '
             f'BG frame instances, plus {report["sprite_frame_count"]} environment sprite/portrait frames. '
             'Every frame has exact native indexed and RGBA PNGs. Family atlases show all phases at 1× and integer 3×.', '',
             'Legacy tree IDs share a deliberately limited crown/skeleton vocabulary. The unplaced '
             '`btree_6`–`btree_11` extensions are intentionally retired to quiet grass. Retained Sister Mary Grace '
             'and Brother Mark bodies alias the Nun and Hermit; catalog coverage does not invent extra spawned people. '
             'Some allocated soil/root/pit phases have identical static paintings, keeping walkable ground quiet.', '',
             '| Category | Complete source atlas |', '| --- | --- |']
    lines += [f'| {entry["family"].replace("_", " ")} | [PNG]({entry["path"]}) |' for entry in atlas_paths]
    lines += ['', f'Animated material boards use a fixed {hold}ms inspection hold per phase, not engine cadence. '
              'Source animation frames and all gate/plate/chest states remain in the native catalog. '
              'No blended transition between separate interaction states is invented.']
    for animation in animations:
        if not animation.get('omitted'):
            title = 'interaction state catalog' if animation.get('kind') else 'material cycle'
            lines += ['', f'[Exact-palette {title}]({animation["path"]}).']
    (out / 'README.md').write_text('\n'.join(lines).rstrip() + '\n')
    report['files'] = {str(path.relative_to(out)): {'sha256': SHA(path), 'bytes': path.stat().st_size}
                       for path in sorted(out.rglob('*')) if path.is_file() and path.name != 'source-manifest.json'}
    write(out / 'source-manifest.json', report)
    return report


def source_hashes():
    paths = sorted(ART.glob('*.py')) + [ART / 'reboot_contracts.json', ROOT / 'Makefile',
                                      ROOT / 'tools/build_assets.py', Path(__file__).resolve()]
    return {str(path.relative_to(ROOT)): SHA(path) for path in paths}


def clean_previous_catalog(out):
    """Remove only unchanged, manifest-owned generated files before a rerun."""
    manifest = out / 'source-manifest.json'
    if not manifest.exists():
        return
    previous = json.loads(manifest.read_text())
    paths = []
    for name, record in previous['files'].items():
        path = (out / name).resolve()
        assert path.is_relative_to(out), ('unsafe previous output path', name)
        assert path.is_file() and SHA(path) == record['sha256'], ('previous generated output was changed', name)
        paths.append(path)
    for path in paths:
        path.unlink()
    manifest.unlink()
    for path in sorted(out.rglob('*'), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', required=True, type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--profiles', default='1,2,3,4,5')
    parser.add_argument('--baseline', type=int, default=0)
    parser.add_argument('--hold-ms', type=int, default=180)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--profile', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--snapshot', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(args)
        return
    assert args.out is not None
    assert args.hold_ms >= 50 and args.hold_ms % 10 == 0
    profiles = [int(value) for value in args.profiles.split(',')]
    assert profiles and len(profiles) == len(set(profiles)) and all(0 <= value <= 5 for value in profiles)
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    clean_previous_catalog(out)
    hashes = source_hashes()
    inventory_sha = SHA(args.inventory)
    with tempfile.TemporaryDirectory(prefix='forest-source-') as temp:
        temp = Path(temp)
        def capture(profile):
            path = temp / f'{profile}.json'
            command = [sys.executable, str(Path(__file__).resolve()), '--worker', '--profile', str(profile),
                       '--inventory', str(args.inventory.resolve()), '--snapshot', str(path)]
            result = subprocess.run(command, cwd=ROOT, env={**os.environ, 'BART_FOREST': str(profile)},
                                    capture_output=True, text=True)
            assert result.returncode == 0, result.stdout + result.stderr
            return profile, json.loads(path.read_text())
        with ThreadPoolExecutor(max_workers=3) as pool:
            snapshots = dict(pool.map(capture, sorted(set(profiles + [args.baseline]))))
    reports = []
    for profile in profiles:
        reports.append(make_variant(snapshots[profile], snapshots[args.baseline], out / f'variant-{profile:02}', args.hold_ms))
    comparison_dir = out / 'comparisons'; comparison_dir.mkdir(exist_ok=True)
    chosen = [snapshots[profile] for profile in profiles]
    matrix, matrix_report = complete_native_matrix(chosen)
    matrix.save(out / 'complete-native-source.png')
    write(out / 'complete-native-source.json', matrix_report)
    valid = set(name for name, _ in lookup(chosen[0]))
    comparisons = []
    for title, names in COMPARISONS.items():
        names = [name for name in names if name in valid]
        if names:
            path = comparison_dir / (title + '-source.png')
            comparison_board(chosen, title, names).save(path)
            comparisons.append({'family': title, 'path': str(path.relative_to(out)), 'samples': names})
    group_keys = [key for key, (_, names) in GROUPS.items() if set(names) <= valid]
    if group_keys:
        path = comparison_dir / 'assembled-trees-and-groups-source.png'
        comparison_board(chosen, 'assembled trees and groups', group_keys).save(path)
        comparisons.append({'family': 'assembled trees and groups', 'path': str(path.relative_to(out)), 'samples': group_keys})
    sprite_keys = [(entry['sheet'], entry['name']) for entry in chosen[0]['entries'] if entry['kind'] == 'sprite']
    for start in range(0, len(sprite_keys), 18):
        path = comparison_dir / f'environment-sprites-{1 + start // 18:02}-source.png'
        comparison_board(chosen, 'environment objects and forest folk', sprite_keys[start:start + 18]).save(path)
        comparisons.append({'family': 'environment sprites', 'path': str(path.relative_to(out)),
                            'samples': sprite_keys[start:start + 18]})
    # One native patch per stage and concept, with all external labels separate.
    overview = Image.new('RGB', (720, 38 + len(chosen) * 192), BG)
    d = ImageDraw.Draw(overview)
    label(d, (8, 5), 'FIVE FOREST CONCEPTS / SOURCE material test patches, not generated rooms or mGBA')
    for n, snapshot in enumerate(chosen):
        y = 38 + n * 192
        label(d, (6, y + 3), f'#{snapshot["profile"]} {snapshot["label"]}')
        for stage, stage_title in enumerate(('healthy', 'mixed', 'deep')):
            label(d, (stage * 240 + 6, y + 17), stage_title, DIM)
            overview.paste(scene_patch(snapshot, stage), (stage * 240, y + 32))
    overview.save(out / 'five-studies-healthy-mixed-deep-source.png')
    assert source_hashes() == hashes, 'Source files changed while exporting; freeze them and regenerate.'
    assert SHA(args.inventory) == inventory_sha, 'Inventory changed while exporting.'
    report = {'method': __doc__, 'source_only': True, 'profiles': profiles,
              'git_base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'source_sha256': hashes, 'inventory_sha256': inventory_sha,
              'hold_ms': args.hold_ms, 'variants': [{key: value for key, value in row.items()
                                                   if key not in ('frames', 'files', 'baseline_comparison')}
                                                  for row in reports],
              'comparisons': comparisons, 'total_frame_instances': sum(row['frame_count'] for row in reports)}
    lines = ['# Five forest directions: complete native source catalogs', '',
             '**SOURCE assets and inspection assemblies, not actual emulator screenshots.**', '',
             '![Five healthy, mixed and deep source material patches](five-studies-healthy-mixed-deep-source.png)', '',
             'All concepts retain quiet green grass and brown earth. Blight changes tree structure, canopy masses, '
             'parasites and local wet details while the same path/water/pit/gate meanings remain readable. '
             'The common 15×10 source test layout compares material hierarchy; actual generated room footage is separate.', '',
             '[Every required frame at native 1×, all five columns](complete-native-source.png) · '
             '[Native matrix provenance](complete-native-source.json)', '',
             '| Concept | Complete native catalog |', '| --- | --- |']
    lines += [f'| {row["profile"]}. {row["label"]} | [All frames and family atlases](variant-{row["profile"]:02}/README.md) |' for row in reports]
    lines += ['', '## Side-by-side family sheets', '']
    lines += [f'- [{row["family"]}]({row["path"]})' for row in comparisons]
    lines += ['', f'Total coverage: **{report["total_frame_instances"]} native frame instances** across {len(profiles)} profiles. '
              'This includes every inventory-required BG transition/frame and environment sprite/portrait, '
              'including unchanged context where explicitly requested. Native PNG roundtrips are checked exactly. '
              f'Source cycles use fixed {args.hold_ms}ms review holds, not gameplay timing. '
              'Baseline comparisons identify unchanged and redrawn frames rather than claiming all catalog entries changed.', '',
              '[Coverage, source hashes and output hashes](source-manifest.json).']
    (out / 'README.md').write_text('\n'.join(lines).rstrip() + '\n')
    report['files'] = {str(path.relative_to(out)): {'sha256': SHA(path), 'bytes': path.stat().st_size}
                       for path in sorted(out.rglob('*')) if path.is_file() and path != out / 'source-manifest.json'}
    write(out / 'source-manifest.json', report)
    print(json.dumps({'source_only': True, 'profiles': profiles,
                      'frame_instances': report['total_frame_instances'], 'files': len(report['files']), 'out': str(out)}))


if __name__ == '__main__':
    main()
