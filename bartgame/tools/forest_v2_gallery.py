#!/usr/bin/env python3
"""Complete native SOURCE review of forest studies 6..10.

The catalogs and layer/adjacency diagrams are source constructions, not mGBA
captures. They disclose logical collision separately from visual aliases.
Palette-pulse previews use authored BG bank states with fixed inspection holds;
they never grade a screenshot or claim to reproduce the running game's clock.
"""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

import forest_concept_gallery as G

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art'
WORK = Path('/workspace/setup/forest-concepts-v2')
INVENTORY = Path('/workspace/setup/forest-concepts/inventory.json')
BG, FIELD, FG, DIM = G.BG, G.FIELD, G.FG, G.DIM
SHA = G.SHA
PAIRS = [(1, 6), (2, 7), (3, 8), (4, 9), (5, 10)]


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def frame_key(entry):
    return G.entry_key(entry)


def worker(args):
    """Snapshot the final integrated pipeline in one fresh profile process."""
    os.environ['BART_FOREST'] = str(args.profile)
    sys.path.insert(0, str(ART))
    import forest_concepts as FC
    import palettes
    import sprites
    import tiles

    assert FC.VARIANT == args.profile
    inv = json.loads(args.inventory.read_text())
    need_bg = set(inv['required']['bg_names'])
    need_obj = {(r['sheet'], r['frame']) for r in inv['required']['sprite_frames']
                + inv['required'].get('conditional_shared_lift_frames', [])}
    tile_meta, sprite_meta = G.metadata(inv)
    bg_colors, obj_colors = dict(palettes.BG_PALETTES), dict(palettes.OBJ_PALETTES)
    for colors in list(bg_colors.values()) + list(obj_colors.values()) + palettes.FACE_PALETTES:
        G.assert_palette(colors)
    tc = {r['name']: r for r in tiles.COVERAGE}
    sc = {(r['sheet'], r['frame']): r for r in sprites.COVERAGE}
    entries, context, context_frames = [], {}, {}
    topology = getattr(tiles, 'FOREST_V2_TOPOLOGY', None)
    specs = {r['name']: r for r in topology['specs']} if topology else {}
    tile_ids = {mt['name']: i for i, mt in enumerate(tiles.METATILES)}
    route_classes = None
    if FC.ROUND2:
        import forest_concepts_v2_topology as T2
        route_classes = T2.classes(tiles.METATILES)
    for tile_id, mt in enumerate(tiles.METATILES):
        name = mt['name']
        if name not in need_bg and name not in specs:
            continue
        meta, source = tile_meta.get(name, {}), specs.get(name)
        if meta:
            assert tile_id == meta['id']
        category = meta.get('category', 'terrain')
        if source:
            family = source['family']
            category = ('topology_canopy_healthy' if source.get('kind') == 1 else 'topology_canopy_blight') if family == 'canopy' else (
                'trees_and_canopy' if family == 'fringe' else 'water_crossings_and_elevation')
        for phase, rows in enumerate(mt.get('frames') or [mt['art']]):
            entry = {'kind': 'tile', 'name': name, 'id': tile_id, 'phase': phase,
                     'canvas': [16, 16], 'palette': mt['pal'], 'colors': bg_colors[mt['pal']],
                     'indices': G.indices(rows, (16, 16)), 'owner': tc[name]['owner'],
                     'category': category, 'family': source['family'] if source else meta.get('family'),
                     'type': mt['type'], 'coll': mt.get('coll', 0), 'prop': mt.get('prop', 0),
                     'glitter': bool(mt.get('glitter')), 'anim_speed': mt.get('anim_speed', 8),
                     'scope': 'appended_topology' if source else meta.get('scope')}
            if mt.get('qpals'):
                entry.update(quarter_palettes=mt['qpals'], quarter_colors=[bg_colors[n] for n in mt['qpals']])
            if source:
                entry['topology'] = source
                entry['semantic_parent'] = source['parent']
                entry['semantic_parent_id'] = tile_ids[source['parent']]
                entry['visual_only'] = bool(source['visual_only'])
            elif route_classes:
                canopy_kind, water_kind = route_classes[0][tile_id], route_classes[1][tile_id]
                if canopy_kind in (1, 2):
                    entry['forest_render_route'] = 'Semantic ID; forest renderer chooses an adjacency/parity canopy alias. Canonical source phases remain catalogued.'
                elif water_kind == 1:
                    entry['forest_render_route'] = 'Semantic water ID; forest renderer chooses an adjacency water alias with the allocated bitmap clock.'
                elif water_kind in (2, 3):
                    entry['forest_render_route'] = 'Original mixed-water picture except an isolated cell uses its dedicated alpha-edged alias.'
                elif name in ('mossy_stone', 'statue'):
                    entry['forest_render_route'] = 'At the active landmark coordinate the renderer shows local BG2 floor plus the taller OBJ marker; this canonical BG picture is retained elsewhere/afterward as appropriate.'
            entries.append(entry)
    for sheet_id, sh in enumerate(sprites.SHEETS):
        for frame_id, (name, rows) in enumerate(sh['frames'].items()):
            key = sh['name'], name
            authored = sc.get(key, {}).get('owner', '').startswith('forest_concepts_v2')
            is_context = (sh['name'] in ('hero', 'beetle', 'bat', 'spitter', 'knight', 'boss') and name in (
                'idle_s', 'walk_s1', 'fly1', 'pulse1')) or (sh['name'] == 'hero' and name.startswith('roll_'))
            if key not in need_obj and not authored and not is_context:
                continue
            bank = sh.get('frame_pal', {}).get(name, sh['pal'])
            colors = palettes.FACE_PALETTES[frame_id] if sh['name'] == 'face' else obj_colors[bank]
            palette_source = f'FACE_PALETTES[{frame_id}]' if sh['name'] == 'face' else 'OBJ_PALETTES'
            G.assert_palette(colors)
            entry = {'kind': 'sprite', 'sheet': sh['name'], 'name': name, 'id': frame_id,
                     'sheet_id': sheet_id, 'phase': 0, 'canvas': [sh['w'], sh['h']],
                     'palette': bank, 'palette_source': palette_source, 'colors': colors,
                     'indices': G.indices(rows, (sh['w'], sh['h'])), 'owner': sc[key]['owner'],
                     'category': 'obj-' + sh['name'], 'family': sh['name'],
                     'scope': sprite_meta.get(key, {}).get('scope', 'appended_environment')}
            assert tuple(entry['canvas']) in G.VALID_SIZES
            if key in need_obj or authored:
                if key in sprite_meta:
                    assert frame_id == sprite_meta[key]['id'], (key, frame_id)
                entries.append(entry)
            else:
                context.setdefault(sh['name'], entry)
                context_frames.setdefault(sh['name'], {})[name] = entry
    assert {e['name'] for e in entries if e['kind'] == 'tile' and e['name'] in need_bg} == need_bg
    assert need_obj <= {(e.get('sheet'), e['name']) for e in entries if e['kind'] == 'sprite'}
    pulse, pulse_indices, descriptions = {}, {}, {}
    if FC.ROUND2:
        import forest_concepts_v2_terrain as terrain
        import forest_concepts_v2_props as props
        import forest_concepts_v2_folk as folk
        assert topology is not None and len(specs) == 457
        pulse = terrain.pulse_palettes(FC.LOCAL_VARIANT)
        pulse_indices = {name: list(values) for name, values in terrain.PULSE_INDICES.items()}
        for name, phases in pulse.items():
            assert len(phases) == 4 and phases[0] == bg_colors[name]
            for colors in phases:
                G.assert_palette(colors)
                assert all(colors[i] == phases[0][i] for i in range(16) if i not in pulse_indices[name])
        descriptions = {'chests': list(props.CHEST_DESIGNS),
                        'folk': {role: forms[FC.LOCAL_VARIANT - 1] for role, forms in folk.CONCEPTS.items()}}
    context_entries = [entry for frames in context_frames.values() for entry in frames.values()]
    for entry in entries + context_entries:
        entry['index_sha256'] = hashlib.sha256(bytes(entry['indices'])).hexdigest()
        entry['rgba_sha256'] = hashlib.sha256(G.rgba(entry).tobytes()).hexdigest()
    assert len({frame_key(e) for e in entries}) == len(entries)
    write(args.snapshot, {'profile': args.profile, 'local_variant': FC.LOCAL_VARIANT,
                          'round2': FC.ROUND2, 'label': FC.NAMES[args.profile], 'entries': entries,
                          'context': context, 'context_frames': context_frames,
                          'bg_colors': bg_colors, 'topology': list(specs.values()),
                          'pulse_palettes': pulse, 'pulse_indices': pulse_indices, 'descriptions': descriptions})


def find(snapshot, name, phase=0, sheet=None):
    if sheet is None:
        candidates = [e for e in snapshot['entries'] if e['kind'] == 'tile' and e['name'] == name]
        assert candidates, (snapshot['profile'], name)
        return next(e for e in candidates if e['phase'] == phase % len(candidates))
    return next(e for e in snapshot['entries'] if e['kind'] == 'sprite' and (e['sheet'], e['name']) == (sheet, name))


def image(snapshot, name, phase=0, sheet=None, palette_phase=0):
    entry = find(snapshot, name, phase, sheet)
    if entry['kind'] == 'tile' and entry['palette'] in snapshot['pulse_palettes']:
        entry = {**entry, 'colors': snapshot['pulse_palettes'][entry['palette']][palette_phase % 4]}
    return G.rgba(entry)


def group(snapshot, key, phase=0, palette_phase=0):
    cols, names = G.GROUPS[key]
    out = Image.new('RGBA', (cols * 16, math.ceil(len(names) / cols) * 16))
    for n, name in enumerate(names):
        tile = image(snapshot, name, phase, palette_phase=palette_phase)
        G.paste(out, tile, (n % cols * 16, n // cols * 16))
    return out


def floor_field(snapshot, size, sick=False):
    out = Image.new('RGB', size, BG)
    tile = image(snapshot, 'blight_floor' if sick else 'moss0')
    for y in range(0, size[1], 16):
        for x in range(0, size[0], 16):
            G.paste(out, tile, (x, y))
    return out


def water_context_board(snapshots):
    """Literal isolated-puddle corners over three deliberately known floors."""
    cw, ch = 264, 160
    out = Image.new('RGB', (cw * 3, 65 + ch * len(snapshots)), BG); d = ImageDraw.Draw(out)
    G.label(d, (8, 5), 'ISOLATED WATER / literal SOURCE over healthy grass, sick grass and dirt')
    G.label(d, (8, 23), 'Native1x + exact2x. Known source fields, not a renderer capture; corner opacity is preserved, never recolored.', DIM)
    proofs = []
    for row, snapshot in enumerate(snapshots):
        y = 65 + row * ch
        G.label(d, (6, y + 3), f'#{snapshot["local_variant"]} {snapshot["label"]}')
        water_entry = find(snapshot, alias(snapshot, 'water', 15, 0))
        water = G.rgba(water_entry)
        for col, (title, floor_name) in enumerate((('Healthy grass', 'moss0'), ('Sick grass', 'blight_floor'), ('Dirt', 'path'))):
            x = col * cw; field = Image.new('RGB', (48, 48))
            floor = image(snapshot, floor_name)
            for yy in range(0, 48, 16):
                for xx in range(0, 48, 16):G.paste(field, floor, (xx, yy))
            G.paste(field, water, (16, 16))
            G.label(d, (x + 7, y + 22), title, DIM)
            out.paste(field.resize((96, 96), Image.Resampling.NEAREST), (x + 7, y + 44))
            out.paste(field, (x + 132, y + 92))
            proofs.append({'profile': snapshot['profile'], 'floor': floor_name, 'water_alias': water_entry['name'],
                           'water_corner_rgba': [list(water.getpixel(p)) for p in ((0, 0), (15, 0), (0, 15), (15, 15))],
                           'source_only': True})
    return out, proofs


def coords(mask, corners):
    """Canonical interior 3x3 neighborhood for one of the 47 legal cases."""
    cells = {(0, 0)}
    for bit, x, y in ((1, 0, -1), (2, 1, 0), (4, 0, 1), (8, -1, 0)):
        if not mask & bit:
            cells.add((x, y))
    for corner, touching, point in ((1, 9, (-1, -1)), (2, 3, (1, -1)),
                                     (4, 6, (1, 1)), (8, 12, (-1, 1))):
        if not mask & touching and not corners & corner:
            cells.add(point)
    return cells


def adjacency(cells, x, y):
    n, e, s, w = ((x + dx, y + dy) in cells for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)))
    mask = (0 if n else 1) | (0 if e else 2) | (0 if s else 4) | (0 if w else 8)
    corners = (1 if n and w and (x - 1, y - 1) not in cells else 0) | (
        2 if n and e and (x + 1, y - 1) not in cells else 0) | (
        4 if s and e and (x + 1, y + 1) not in cells else 0) | (
        8 if s and w and (x - 1, y + 1) not in cells else 0)
    return mask, corners


def cases(snapshot):
    pairs = sorted({(s['mask'], s['corners']) for s in snapshot['topology'] if s['family'] == 'water'})
    assert len(pairs) == 47
    assert all(adjacency(coords(mask, corners), 0, 0) == (mask, corners) for mask, corners in pairs)
    return pairs


def alias(snapshot, family, mask, corners=0, quadrant=0):
    specs = [s for s in snapshot['topology'] if s['family'] == ('canopy' if family != 'water' else 'water')
             and s['mask'] == mask and s.get('corners', 0) == corners
             and (family == 'water' or (s['kind'] == (2 if family == 'blight' else 1) and s['quadrant'] == quadrant))]
    assert len(specs) == 1, (family, mask, corners, quadrant)
    return specs[0]['name']


def shape(snapshot, family, occupied, palette_phase=0, origin=(2, 2)):
    width, height = max(x for x, _ in occupied) + 3, max(y for _, y in occupied) + 3
    sick = family == 'blight'
    out = floor_field(snapshot, (width * 16, height * 16), sick)
    records = []
    for x, y in sorted(occupied, key=lambda p: (p[1], p[0])):
        mask, corners = adjacency(occupied, x, y)
        q = ((origin[0] + x) & 1) | (((origin[1] + y) & 1) << 1)
        name = alias(snapshot, family, mask, corners, q)
        tile = image(snapshot, name, palette_phase=palette_phase)
        G.paste(out, tile, ((x + 1) * 16, (y + 1) * 16))
        records.append({'cell': [x, y], 'world_cell': [origin[0] + x, origin[1] + y],
                        'mask': mask, 'corners': corners, 'macro_quadrant': q, 'alias': name})
    return out, {'family': family, 'origin': list(origin), 'cells': records,
                 'substrate': 'Explicit source fixture: sick soil' if sick else 'Explicit source fixture: healthy grass',
                 'note': 'Interior island on a disclosed source substrate, not an actual generated room.'}


def collision_tile(entry, water=False, size=32):
    out = Image.new('RGB', (size, size), '#183848' if water else '#203828')
    d = ImageDraw.Draw(out); half = size // 2
    for n in range(4):
        x, y = n % 2 * half, n // 2 * half
        fill = '#304860' if water else '#803838' if entry['coll'] & (8, 4, 2, 1)[n] else '#385840'
        d.rectangle((x, y, x + half - 1, y + half - 1), fill=fill, outline='#c0b898')
    return out


def blob_board(snapshot, family):
    cw, ch, cols = 206, 136, 6
    combinations = cases(snapshot)
    out = Image.new('RGB', (cw * cols, 68 + math.ceil(47 / cols) * ch), BG)
    d = ImageDraw.Draw(out)
    G.label(d, (8, 5), f'#{snapshot["local_variant"]} {snapshot["label"]} / all47 {family} SOURCE adjacency cases')
    G.label(d, (8, 23), 'Four canopy parity swatches are separate samples, not one claimed island. N/E/S/W = exposed1/2/4/8.', DIM)
    G.label(d, (8, 41), 'Red = parent solid8px quarters. Blue = water hazard despite coll0. Rounding never erases the logical collider.', DIM)
    proofs = []
    for n, (mask, corners) in enumerate(combinations):
        x, y = n % cols * cw, 68 + n // cols * ch
        G.label(d, (x + 6, y + 2), f'M{mask:x} C{corners:x}')
        if family == 'water':
            name = alias(snapshot, family, mask, corners)
            for phase in (0, 1):
                pic = image(snapshot, name, phase)
                field = floor_field(snapshot, (24, 24)); G.paste(field, pic, (4, 4))
                out.paste(field, (x + 6 + phase * 30, y + 23))
        else:
            for q in range(4):
                name = alias(snapshot, family, mask, corners, q)
                field = floor_field(snapshot, (20, 20), family == 'blight')
                G.paste(field, image(snapshot, name), (2, 2))
                out.paste(field, (x + 6 + q % 2 * 24, y + 23 + q // 2 * 24))
        members = coords(mask, corners)
        for yy in range(-1, 2):
            for xx in range(-1, 2):
                fill = '#304860' if family == 'water' else '#284030'
                d.rectangle((x + 86 + (xx + 1) * 9, y + 25 + (yy + 1) * 9,
                             x + 93 + (xx + 1) * 9, y + 32 + (yy + 1) * 9),
                            fill=fill if (xx, yy) in members else '#806848', outline='#101820')
        parent = find(snapshot, 'water' if family == 'water' else 'canopy' if family == 'healthy' else 'blight_wall')
        out.paste(collision_tile(parent, family == 'water'), (x + 144, y + 25))
        G.label(d, (x + 6, y + 83), 'phase0/1' if family == 'water' else 'q0 q1 / q2 q3', DIM)
        G.label(d, (x + 6, y + 102), 'concave NW1 NE2 SE4 SW8', DIM)
        proofs.append({'mask': mask, 'corners': corners, 'canonical_neighbors': sorted(map(list, members)),
                       'parent_id': parent['id'], 'parent_type': parent['type'], 'parent_coll': parent['coll'],
                       'visual_only': True, 'source_only': True})
    return out, proofs


SHAPES = {'isolated1x1': {(0, 0)}, 'block2x2': {(x, y) for y in range(2) for x in range(2)},
          'block3x3': {(x, y) for y in range(3) for x in range(3)},
          'L-corner': {(0, 0), (0, 1), (1, 1)},
          'concave-ring': {(x, y) for y in range(3) for x in range(3)} - {(1, 1)}}


def shape_board(snapshot):
    cw, ch = 268, 204
    out = Image.new('RGB', (cw * 5, 64 + 3 * ch), BG); d = ImageDraw.Draw(out)
    G.label(d, (8, 5), f'#{snapshot["local_variant"]} {snapshot["label"]} / SOURCE adjacency assemblies at native1x +2x')
    G.label(d, (8, 23), 'Per-cell exposed sides/corners/parity follow the renderer. Explicit grass/soil substrate; no generated-room claim.', DIM)
    proofs = []
    for row, family in enumerate(('healthy', 'blight', 'water')):
        for col, (title, occupied) in enumerate(SHAPES.items()):
            x, y = col * cw, 64 + row * ch
            G.label(d, (x + 6, y + 2), family + ' / ' + title)
            picture, proof = shape(snapshot, family, occupied)
            out.paste(picture.resize((picture.width * 2, picture.height * 2), Image.Resampling.NEAREST), (x + 6, y + 22))
            out.paste(picture, (x + 182, y + 22 + picture.height))
            proof['shape'] = title; proofs.append(proof)
    return out, proofs


def gate(snapshot):
    out = floor_field(snapshot, (48, 48))
    G.paste(out, image(snapshot, 'door_locked'), (8, 16))
    G.paste(out, image(snapshot, 'door_locked'), (24, 16))
    G.paste(out, image(snapshot, 'keylock', sheet='forestlandmark'), (16, 0))
    return out


def landmark_assembly(snapshot, which, spent=False):
    if which == 'relic':
        out = floor_field(snapshot, (32, 48))
        # The live renderer hides the canonical mossy-stone picture while the
        # marker is active. Its pedestal is part of the OBJ; the logical
        # MOSSY_STONE FLOOR0 site still determines the interaction footprint.
        G.paste(out, image(snapshot, 'relic', sheet='forestlandmark'), (8, 0))
        return out
    out = floor_field(snapshot, (32, 64))
    G.paste(out, image(snapshot, 'shrine_plate'), (8, 32))
    G.paste(out, image(snapshot, 'shrine_spent' if spent else 'shrine_available', sheet='forestlandmark'), (8, 0))
    return out


def item_board(snapshots):
    rows = [('Whole lift boulder', 'boulder'), ('Bomb stone, chosen #4', 'crack'), ('Purple thorns', 'thorn'),
            ('Five silk constructions', 'web'), ('Simple button up', 'myst_switch'),
            ('Simple button down', 'myst_switch_down'), ('Bars BG + ONE lock OBJ', 'gate'),
            ('Gate bars BG layer only', 'door_locked'), ('Tall relic at live feature', 'relic-assembly'),
            ('Healing font + lower pad', 'shrine-assembly'), ('Spent font + lower pad', 'shrine-spent'),
            ('Two-cell solid fallen log', 'log-assembly'), ('Ledge near-side face', 'ledge_s')]
    left, cw, ch = 190, 220, 170
    out = Image.new('RGB', (left + cw * 5, 72 + len(rows) * ch), BG); d = ImageDraw.Draw(out)
    G.label(d, (8, 5), 'FOREST V2 / native SOURCE interactions and height assemblies')
    G.label(d, (8, 23), 'One complete two-cell key gate has ONE large lock. Height pictures do not enlarge physical footprints.', DIM)
    for n, snapshot in enumerate(snapshots):
        G.label(d, (left + n * cw + 6, 47), f'#{snapshot["local_variant"]} {snapshot["label"]}')
    for row, (title, name) in enumerate(rows):
        y = 72 + row * ch; G.label(d, (6, y + 8), title)
        for n, snapshot in enumerate(snapshots):
            if name == 'gate':pic = gate(snapshot)
            elif name == 'relic-assembly':pic = landmark_assembly(snapshot, 'relic')
            elif name.startswith('shrine'):pic = landmark_assembly(snapshot, 'shrine', name.endswith('spent'))
            elif name == 'log-assembly':pic = group(snapshot, 'fallen-log')
            else:pic = image(snapshot, name)
            x = left + n * cw
            field = floor_field(snapshot, (pic.width, pic.height), name == 'thorn')
            G.paste(field, pic, (0, 0))
            out.paste(field.resize((field.width * 2, field.height * 2), Image.Resampling.NEAREST), (x + 6, y + 25))
            out.paste(field, (x + 132, y + 25 + field.height))
    return out


def wooden_board(snapshots):
    left, cw, ch = 176, 220, 114
    names = ('wooden_closed', 'wooden_open', 'wooden_b_closed', 'wooden_b_open')
    out = Image.new('RGB', (left + 5 * cw, 72 + 4 * ch), BG); d = ImageDraw.Draw(out)
    G.label(d, (8, 5), 'TEN WOODEN CHEST FORMS / native SOURCE A+B closed/open states')
    G.label(d, (8, 23), 'Literal native32x32 canvases; 2x +1x. State pairs are inspection poses, not an engine-timing simulation.', DIM)
    for n, snapshot in enumerate(snapshots):
        G.label(d, (left + n * cw + 6, 47), f'#{snapshot["local_variant"]} {snapshot["label"]}')
    for row, name in enumerate(names):
        y = 72 + row * ch; G.label(d, (6, y + 9), name)
        for n, snapshot in enumerate(snapshots):
            field = floor_field(snapshot, (40, 40)); G.paste(field, image(snapshot, name, sheet='interactivechest'), (4, 4))
            x = left + n * cw
            out.paste(field.resize((80, 80), Image.Resampling.NEAREST), (x + 6, y + 23))
            out.paste(field, (x + 114, y + 63))
    return out


def folk_board(snapshots):
    cw, ch = 236, 166
    out = Image.new('RGB', (cw * 5, 72 + ch * 3), BG); d = ImageDraw.Draw(out)
    G.label(d, (8, 5), 'FIFTEEN FOREST FOLK / native static SOURCE bodies, matching48px busts and silhouettes')
    G.label(d, (8, 23), 'Body2x on sick soil +native1x on grass; portrait is the literal48x48 viewport crop. No idle animation is claimed.', DIM)
    for n, snapshot in enumerate(snapshots):
        G.label(d, (n * cw + 5, 47), f'#{snapshot["local_variant"]} {snapshot["label"]}')
    for row, role in enumerate(('hermit', 'nun', 'gardener')):
        for col, snapshot in enumerate(snapshots):
            x, y = col * cw, 72 + row * ch
            G.label(d, (x + 5, y + 4), snapshot['descriptions']['folk'][role])
            body = image(snapshot, role, sheet='npc')
            for xx, scale, sick in ((8, 2, True), (80, 1, False)):
                field = floor_field(snapshot, (32, 32), sick); G.paste(field, body, (0, 0))
                out.paste(field.resize((32 * scale, 32 * scale), Image.Resampling.NEAREST),
                          (x + xx, y + 100 - 32 * scale))
            portrait = image(snapshot, role, sheet='face').crop((0, 0, 48, 48))
            field = Image.new('RGB', (48, 48), FIELD); G.paste(field, portrait, (0, 0))
            out.paste(field, (x + 132, y + 52))
            G.paste(out, G.silhouette(body), (x + 190, y + 68))
            for xx, text in ((8, '2x soil'), (80, '1x grass'), (132, 'portrait1x'), (190, 'shape')):
                G.label(d, (x + xx, y + 111), text, DIM)
    return out


def footprint_board(snapshot):
    """Diagnostic wire overlays; these added colored grids are not game art."""
    cells = []
    canopy = image(snapshot, alias(snapshot, 'blight', 15, 0, 0))
    water = image(snapshot, alias(snapshot, 'water', 15, 0))
    arch = Image.new('RGBA', (32, 16)); G.paste(arch, image(snapshot, 'f2_arch_0'), (0, 0)); G.paste(arch, image(snapshot, 'f2_arch_1'), (16, 0))
    cells.extend([
        ('Rounded canopy', 'SOLID15; alpha corners still block', canopy, [(0, 0, 15, False)]),
        ('Water island', 'WATER0 is a hazard, not FLOOR0', water, [(0, 0, 0, True)]),
        ('Canopy fringe', 'Walkable FLOOR0 under foreground', image(snapshot, 'f2_fringe_1_1'), [(0, 0, 0, False)]),
        ('Raised root arch', 'Two FLOOR0 cells; no upper deck', arch, [(0, 0, 0, False), (16, 0, 0, False)]),
        ('Long fallen log', 'Two full SOLID15 cells, no passage', group(snapshot, 'fallen-log'), [(0, 0, 15, False), (16, 0, 15, False)]),
        ('Tall relic at live plinth', 'MOSSY_STONE footprint remains0', landmark_assembly(snapshot, 'relic'), [(8, 16, 0, False)]),
        ('Tall shrine plus lower pad', 'STATUE3 lower quarters; pad0', landmark_assembly(snapshot, 'shrine'), [(8, 16, 3, False), (8, 32, 0, False)]),
        ('Bars plus one large lock', 'Two DOOR15 cells; OBJ adds height', gate(snapshot), [(8, 16, 15, False), (24, 16, 15, False)]),
    ])
    cw, ch = 288, 230
    out = Image.new('RGB', (cw * 4, 65 + ch * 2), BG); d = ImageDraw.Draw(out)
    G.label(d, (8, 5), f'#{snapshot["local_variant"]} {snapshot["label"]} / SOURCE diagnostic collision overlays')
    G.label(d, (8, 23), 'Added wire colors are explanations: redblocked / greenpassable / bluewaterhazard. Literal native art is also shown without wires.', DIM)
    proofs = []
    for n, (title, subtitle, pic, footprints) in enumerate(cells):
        x, y = n % 4 * cw, 65 + n // 4 * ch
        G.label(d, (x + 5, y + 3), title); G.label(d, (x + 5, y + 19), subtitle, DIM)
        field = floor_field(snapshot, pic.size); G.paste(field, pic, (0, 0)); wired = field.copy(); grid = ImageDraw.Draw(wired)
        for xx, yy, mask, hazard in footprints:
            for q, bit in enumerate((8, 4, 2, 1)):
                a, b = xx + q % 2 * 8, yy + q // 2 * 8
                color = '#5888b0' if hazard else '#c05860' if mask & bit else '#80b078'
                grid.rectangle((a, b, a + 7, b + 7), outline=color)
        out.paste(wired.resize((wired.width * 2, wired.height * 2), Image.Resampling.NEAREST), (x + 7, y + 49))
        out.paste(field, (x + 158, y + 49 + field.height))
        proofs.append({'title': title, 'footprints': footprints, 'collision_quarter_bits': [8, 4, 2, 1],
                       'source_only': True, 'wire_overlay_is_diagnostic': True})
    return out, proofs


def state_board(snapshot, state, hold):
    objects = [('Wooden A', image(snapshot, 'wooden_open' if state else 'wooden_closed', sheet='interactivechest')),
               ('Wooden B', image(snapshot, 'wooden_b_open' if state else 'wooden_b_closed', sheet='interactivechest')),
               ('Pressure button', image(snapshot, 'myst_switch_down' if state else 'myst_switch')),
               ('Healing font', landmark_assembly(snapshot, 'shrine', bool(state))),
               ('Hollow entrance', image(snapshot, 'hollow' if state else 'hollow_closed', sheet='interactiveentry')),
               ('Thicket entrance', image(snapshot, 'thicket' if state else 'thicket_closed', sheet='interactiveentry'))]
    cw, ch = 220, 194
    out = Image.new('RGB', (cw * 3, 64 + ch * 2), BG); d = ImageDraw.Draw(out)
    G.label(d, (8, 5), f'#{snapshot["local_variant"]} {snapshot["label"]} / SOURCE interaction state{state}')
    G.label(d, (8, 23), f'Fixed{hold}ms inspection holds; discrete states, not engine event timing or a floor-restoration proof.', DIM)
    for n, (title, pic) in enumerate(objects):
        x, y = n % 3 * cw, 64 + n // 3 * ch; G.label(d, (x + 5, y + 3), title)
        field = floor_field(snapshot, pic.size); G.paste(field, pic, (0, 0))
        base = y + ch - 15
        out.paste(field.resize((field.width * 2, field.height * 2), Image.Resampling.NEAREST), (x + 6, base - field.height * 2))
        out.paste(field, (x + 128, base - field.height))
    return out


def motion_board(snapshot, phase, hold):
    names = ('water', 'waterfall', 'water_lily', 'water_foam', 'blight_pool', 'blight_mist')
    out = Image.new('RGB', (864, 186), BG); d = ImageDraw.Draw(out)
    G.label(d, (8, 5), f'#{snapshot["local_variant"]} {snapshot["label"]} / SOURCE bitmap phase{phase}')
    G.label(d, (8, 23), f'Fixed{hold}ms inspection holds; authored tile phases only. BG palette is held atphase0, separately from pulse preview.', DIM)
    for n, name in enumerate(names):
        x = n * 144; G.label(d, (x + 5, 55), name)
        field = floor_field(snapshot, (24, 24)); G.paste(field, image(snapshot, name, phase), (4, 4))
        out.paste(field.resize((72, 72), Image.Resampling.NEAREST), (x + 5, 81)); out.paste(field, (x + 96, 129))
    return out


def pulse_board(snapshot, phase):
    out = Image.new('RGB', (864, 254), BG); d = ImageDraw.Draw(out)
    G.label(d, (8, 5), f'#{snapshot["local_variant"]} {snapshot["label"]} / authored BG palette phase{phase}')
    G.label(d, (8, 23), 'SOURCE only: indices fixed; BG blight inks5/6/7/13/14 change. Fixed inspection holds, not game cadence.', DIM)
    pictures = [('Dead wood', group(snapshot, 'dead-tree', palette_phase=phase)),
                ('Sick tree', group(snapshot, 'sick-tree', palette_phase=phase)),
                ('Wall tree', group(snapshot, 'wall-blight-tree', palette_phase=phase)),
                ('Black canopy', image(snapshot, alias(snapshot, 'blight', 0, 0, 0), palette_phase=phase)),
                ('Thorns', image(snapshot, 'thorn', palette_phase=phase)),
                ('Growth', image(snapshot, 'blight_crystal', palette_phase=phase))]
    for n, (title, pic) in enumerate(pictures):
        x = n * 144
        G.label(d, (x + 7, 53), title)
        field = floor_field(snapshot, (max(40, pic.width), max(56, pic.height)), True)
        G.paste(field, pic, ((field.width - pic.width) // 2, field.height - pic.height))
        out.paste(field.resize((field.width * 2, field.height * 2), Image.Resampling.NEAREST), (x + 7, 77))
        G.paste(out, pic, (x + 104, 198 - pic.height))
    return out


def layer_board(snapshot):
    """Show source layer order plus the unchanged logical-footprint contract."""
    size = (112, 96); floor = floor_field(snapshot, size)
    foliage = Image.new('RGBA', size)
    # A connected top canopy with a true lower fringe above ordinary floor.
    occupied = {(x, 0) for x in range(7)}
    for x, y in occupied:
        m, c = adjacency(occupied, x, y); q = (x & 1) | ((y & 1) << 1)
        G.paste(foliage, image(snapshot, alias(snapshot, 'blight', m, c, q)), (x * 16, y * 16))
    for x in range(7):G.paste(foliage, image(snapshot, 'f2_fringe_1_1'), (x * 16, 16))
    actors = Image.new('RGBA', size)
    hero = G.rgba(snapshot['context']['hero']); G.paste(actors, hero, (40, 8))
    arch = Image.new('RGBA', size)
    G.paste(arch, image(snapshot, 'f2_arch_0'), (32, 48))
    G.paste(arch, image(snapshot, 'f2_arch_1'), (48, 48))
    # The second Bloom is a separate source inspection position, not a cloned
    # actor claim. A real run's traversal must establish the transition.
    under = Image.new('RGBA', size); G.paste(under, hero, (32, 32))
    combo = floor.copy(); G.paste(combo, actors, (0, 0)); G.paste(combo, foliage, (0, 0))
    arch_combo = floor.copy(); G.paste(arch_combo, under, (0, 0)); G.paste(arch_combo, arch, (0, 0))
    board = Image.new('RGB', (1220, 454), BG); d = ImageDraw.Draw(board)
    G.label(d, (8, 5), f'#{snapshot["local_variant"]} {snapshot["label"]} / SOURCE foreground and lower-route diagrams')
    G.label(d, (8, 23), 'Representative source order: BG2 floor -> OBJ Bloom -> BG1 projection. HUD BG0 is above and not drawn here.', DIM)
    for n, (title, pic) in enumerate((('BG2 ground only', floor), ('OBJ actor source layer', actors),
                                    ('BG1 canopy/fringe', foliage), ('Source combined fringe', combo), ('BG1 arch above lower route', arch_combo))):
        x = n * 244; G.label(d, (x + 5, 54), title)
        field = floor.copy(); G.paste(field, pic, (0, 0))
        board.paste(field.resize((224, 192), Image.Resampling.NEAREST), (x + 5, 79))
        board.paste(field, (x + 5, 291))
    G.label(d, (8, 403), 'Canopy logical cells: SOLID coll15. Adjacent fringe floor: coll0. Arch overlay: FLOOR coll0; no upper deck.', DIM)
    G.label(d, (8, 424), 'Logs: two SOLID15 cells. Relic: MOSSY_STONE FLOOR0. Shrine statue: lower two8px quarters; pad below stays walkable.', DIM)
    return board


def roll_clearance_board(snapshot):
    """Source alpha-composition test only, never an actual roll/collision run."""
    poses = ['idle_s'] + [name for name in snapshot['context_frames']['hero'] if name.startswith('roll_')]
    source_cases = []
    for spec in snapshot['topology']:
        if spec['family'] == 'fringe' and spec['mask'] & 1:
            entry = find(snapshot, spec['name'])
            clear = all(entry['indices'][y * 16 + x] == 0 for y in range(2, 16) for x in range(2, 14))
            assert clear, spec['name']
            source_cases.append({'alias': spec['name'], 'mask': spec['mask'], 'kind': spec['kind'],
                                 'clear_rectangle': [2, 2, 14, 16], 'transparent_pixels': 168})
    cols, cw, ch = 7, 184, 154
    panels = [(family, pose) for family in ('healthy', 'blight') for pose in poses]
    out = Image.new('RGB', (cols * cw, 72 + math.ceil(len(panels) / cols) * ch), BG); d = ImageDraw.Draw(out)
    G.label(d, (8, 5), f'#{snapshot["local_variant"]} {snapshot["label"]} / SOURCE-only standing and roll clearance diagrams')
    G.label(d, (8, 23), '2x composite vs native1x actor-only; fixed source feet(24,26), not input/movement, collision or runtime proof.', DIM)
    G.label(d, (8, 41), 'All north-touching fringe masks have the literal central12x14 transparent lane beneath their2px header.', DIM)
    proofs = []
    for n, (family, pose) in enumerate(panels):
        x, y = n % cols * cw, 72 + n // cols * ch
        G.label(d, (x + 5, y + 3), ('BL ' if family == 'blight' else 'HE ') + pose)
        field = floor_field(snapshot, (48, 48), family == 'blight')
        front = Image.new('RGBA', (48, 48)); occupied = {(0, 0), (1, 0), (2, 0)}
        for xx, yy in occupied:
            mask, corners = adjacency(occupied, xx, yy); q = xx & 1
            G.paste(front, image(snapshot, alias(snapshot, family, mask, corners, q)), (xx * 16, 0))
            G.paste(front, image(snapshot, f'f2_fringe_{1 if family == "blight" else 0}_1'), (xx * 16, 16))
        source = snapshot['context_frames']['hero'][pose]
        actor = Image.new('RGBA', (48, 48)); G.paste(actor, G.rgba(source), (8, -6))
        raw = field.copy(); G.paste(raw, actor, (0, 0)); combined = raw.copy(); G.paste(combined, front, (0, 0))
        a, b = actor.getchannel('A').tobytes(), front.getchannel('A').tobytes()
        opaque = sum(bool(value) for value in a); visible = sum(bool(v) and not bool(f) for v, f in zip(a, b))
        assert visible > 0, (snapshot['profile'], family, pose, 'source pose completely occluded')
        out.paste(combined.resize((96, 96), Image.Resampling.NEAREST), (x + 5, y + 27))
        out.paste(raw, (x + 120, y + 75))
        G.label(d, (x + 5, y + 132), f'source visible{visible}/{opaque}', DIM)
        proofs.append({'profile': snapshot['profile'], 'family': family, 'pose': pose,
                       'frame_id': source['id'], 'fixed_source_feet': [24, 26],
                       'protected_actor_index_sha256': source['index_sha256'],
                       'protected_actor_rgba_sha256': source['rgba_sha256'],
                       'actor_scene_opaque_pixels': opaque, 'visible_after_source_foreground': visible,
                       'source_only': True, 'not_runtime_or_physical_clearance_proof': True})
    return out, {'north_fringe_alpha_cases': source_cases, 'poses': proofs,
                 'method': 'Literal source alpha composition at disclosed fixed coordinates. Actual movement/clearance belongs to mGBA captures.'}


def before_after(old, current):
    cw, ch = 232, 216
    out = Image.new('RGB', (cw * 5, 66 + 5 * ch), BG); d = ImageDraw.Draw(out)
    G.label(d, (8, 5), 'BEFORE / AFTER FOREST SOURCE / previous options1..5 versus new options1..5')
    G.label(d, (8, 23), 'These are paired review options, not an assertion of one-to-one art ancestry. Native source1x +2x.', DIM)
    titles = ('Old sick tree', 'New sick tree', 'New dead tree', 'Old deep floor / new', 'New infected canopy')
    for col, title in enumerate(titles):G.label(d, (col * cw + 6, 46), title)
    for row, snapshot in enumerate(current):
        y = 66 + row * ch; baseline = old[row]
        G.label(d, (6, y + 5), f'#{snapshot["local_variant"]} {snapshot["label"]}')
        pictures = [group(baseline, 'sick-tree'), group(snapshot, 'sick-tree'), group(snapshot, 'dead-tree'),
                    image(baseline, 'blight_floor'), image(snapshot, 'blight_wall')]
        for col, pic in enumerate(pictures):
            source = baseline if col in (0, 3) else snapshot
            field = floor_field(source, (72, 72), True); G.paste(field, pic, (8, 72 - pic.height))
            if col == 3:G.paste(field, image(snapshot, 'blight_floor'), (40, 56))
            out.paste(field.resize((144, 144), Image.Resampling.NEAREST), (col * cw + 6, y + 29))
            G.paste(out, pic, (col * cw + 160, y + 173 - pic.height))
    return out


def source_hashes():
    paths = set(ART.glob('*.py')) | set((ROOT / 'src').glob('*.[chs]'))
    paths.update((ART / 'reboot_contracts.json', ROOT / 'Makefile', ROOT / 'gba.ld',
                  ROOT / 'tools/build_assets.py', ROOT / 'tools/forest_concept_gallery.py', Path(__file__).resolve()))
    return {str(path.relative_to(ROOT)): SHA(path) for path in sorted(paths)}


def native_palette_phase_groups(snapshot, out):
    """Literal indexed BG groups with four ramps, not four new packed frames."""
    groups = [('dead-tree', G.GROUPS['dead-tree'][0], G.GROUPS['dead-tree'][1]),
              ('canopy-interior-macro', 2, [alias(snapshot, 'blight', 0, 0, q) for q in range(4)])]
    folder = out / 'native-palette-phases'; folder.mkdir(exist_ok=True)
    records = []
    for title, cols, names in groups:
        width, height = cols * 16, math.ceil(len(names) / cols) * 16
        raw = bytearray(width * height); components = []
        for n, name in enumerate(names):
            entry = find(snapshot, name)
            assert entry['palette'] == 'blight'
            for y in range(16):
                start = (n // cols * 16 + y) * width + n % cols * 16
                raw[start:start + 16] = bytes(entry['indices'][y * 16:(y + 1) * 16])
            components.append({'name': name, 'id': entry['id'], 'index_sha256': entry['index_sha256']})
        index_sha = hashlib.sha256(raw).hexdigest(); phases = []
        for phase, colors in enumerate(snapshot['pulse_palettes']['blight']):
            entry = {'canvas': [width, height], 'indices': list(raw), 'colors': colors}
            p_path = folder / f'{title}-phase{phase:02}-indexed.png'
            a_path = folder / f'{title}-phase{phase:02}.png'
            G.indexed(entry).save(p_path); G.rgba(entry).save(a_path)
            with Image.open(p_path) as pic:
                assert hashlib.sha256(pic.tobytes()).hexdigest() == index_sha
                assert pic.convert('RGBA').tobytes() == Image.open(a_path).convert('RGBA').tobytes()
            phases.append({'phase': phase, 'colors_rgb555': colors, 'index_sha256': index_sha,
                           'native_indexed_png': str(p_path.relative_to(out)),
                           'native_rgba_png': str(a_path.relative_to(out)), 'rgba_roundtrip_verified': True})
        records.append({'name': title, 'canvas': [width, height], 'components': components,
                        'index_sha256': index_sha, 'phases': phases,
                        'hardware_role': 'Assembled native BG tiles; four palette states of one bitmap, not appended sprite frames.'})
    return records


def catalog(snapshot, baseline, out, hold):
    out.mkdir(parents=True, exist_ok=True)
    exports = G.export_native(snapshot, out)
    phase_groups = native_palette_phase_groups(snapshot, out)
    categories = defaultdict(list)
    for entry in snapshot['entries']:categories[entry['category']].append(entry)
    (out / 'atlases').mkdir(exist_ok=True); atlas_records = []
    for category, entries in sorted(categories.items()):
        for part in range(math.ceil(len(entries) / 200)):
            chunk = entries[part * 200:(part + 1) * 200]
            suffix = f'-{part + 1:02}' if len(entries) > 200 else ''
            path = out / 'atlases' / f'{G.slug(category)}{suffix}-source.png'
            G.atlas(chunk, f'#{snapshot["local_variant"]} {snapshot["label"]} / {category}').save(path)
            atlas_records.append({'category': category, 'path': str(path.relative_to(out)),
                                  'frame_keys': [list(frame_key(entry)) for entry in chunk]})
    shape_image, shape_records = shape_board(snapshot); shape_image.save(out / 'adjacency-islands-source.png')
    write(out / 'adjacency-islands-source.json', shape_records)
    topology_records = {}
    for family in ('healthy', 'blight', 'water'):
        board, records = blob_board(snapshot, family)
        board.save(out / f'all47-{family}-cases-source.png'); topology_records[family] = records
    write(out / 'all47-cases-source.json', topology_records)
    layer_board(snapshot).save(out / 'foreground-layer-diagrams-source.png')
    clearance_image, clearance_records = roll_clearance_board(snapshot)
    clearance_image.save(out / 'standing-roll-clearance-source.png')
    write(out / 'standing-roll-clearance-source.json', clearance_records)
    footprint_image, footprint_records = footprint_board(snapshot)
    footprint_image.save(out / 'physical-footprint-overlays-source.png')
    write(out / 'physical-footprint-overlays-source.json', footprint_records)
    G.assembly_board({**snapshot, 'profile': snapshot['local_variant']}).save(out / 'assembled-groups-source.png')
    G.diagnostics({**snapshot, 'profile': snapshot['local_variant']}).save(out / 'value-contour-diagnostics-source.png')
    animations = []
    pulse_frames = [pulse_board(snapshot, phase) for phase in range(4)]
    for phase, frame in enumerate(pulse_frames):frame.save(out / f'palette-pulse-phase{phase:02}-source.png')
    path = out / 'palette-pulse-source.gif'
    animations.append({'path': path.name, 'kind': 'Authored BG blight palette phases; all source indices held fixed.',
                       **G.exact_gif(pulse_frames, hold, path)})
    states = [state_board(snapshot, state, hold) for state in (0, 1)]
    for state, frame in enumerate(states):frame.save(out / f'interaction-states-phase{state:02}-source.png')
    path = out / 'interaction-states-source.gif'
    animations.append({'path': path.name, 'kind': 'Discrete interaction inspection states, not event timing.',
                       **G.exact_gif(states, hold, path)})
    motions = [motion_board(snapshot, phase, hold) for phase in range(6)]
    for phase, frame in enumerate(motions):frame.save(out / f'bitmap-motion-phase{phase:02}-source.png')
    path = out / 'bitmap-motion-source.gif'
    animations.append({'path': path.name, 'kind': 'Authored bitmap phases; palette held atphase0; not game cadence.',
                       **G.exact_gif(motions, hold, path)})
    before = {frame_key(e): e for e in baseline['entries']}
    changes = []
    for entry in snapshot['entries']:
        prior = before.get(frame_key(entry))
        changes.append({'key': list(frame_key(entry)), 'appended': prior is None,
                        'indices_changed': prior is None or entry['index_sha256'] != prior['index_sha256'],
                        'rgba_changed': prior is None or entry['rgba_sha256'] != prior['rgba_sha256']})
    report = {'profile': snapshot['profile'], 'local_variant': snapshot['local_variant'], 'label': snapshot['label'],
              'source_only': True, 'frames': exports, 'frame_count': len(exports),
              'bg_metatile_count': len({e['name'] for e in exports if e['kind'] == 'tile'}),
              'bg_frame_count': sum(e['kind'] == 'tile' for e in exports),
              'sprite_frame_count': sum(e['kind'] == 'sprite' for e in exports),
              'topology_alias_count': len(snapshot['topology']), 'topology': snapshot['topology'],
              'pulse_palettes': snapshot['pulse_palettes'], 'pulse_indices': snapshot['pulse_indices'],
              'pulse_affected_frame_keys': [list(frame_key(e)) for e in snapshot['entries']
                                            if e['kind'] == 'tile' and e['palette'] in snapshot['pulse_palettes']],
              'palette_pulse_indices_held_fixed': True,
              'native_palette_phase_groups': phase_groups,
              'baseline_profile': baseline['profile'], 'baseline_comparison': changes,
              'atlases': atlas_records, 'animations': animations,
              'hardware_layers': {'ground': 'BG2 (screenblock28)', 'foreground': 'BG1 (screenblock24)',
                                  'player': 'OBJ with existing depth priority', 'hud': 'BG0 reserved above world'},
              'layer_semantics': {'canopy': 'Semantic SOLID15; rounded aliases do not erase collision.',
                                  'water': 'Semantic WATER hazard despite coll0.', 'fringe': 'Render-only foreground over FLOOR0.',
                                  'arch': 'FLOOR0 overlay. Walkable lower route, no upper deck.',
                                  'log': 'Two full SOLID15 cells, not an underpass.',
                                  'relic': 'Tall marker at MOSSY_STONE FLOOR0; legacy RELIC tile is not live placement.',
                                  'shrine': 'Tall marker at statue; lower two8px quarters blocked; pad below stays walkable.'}}
    lines = [f'# {snapshot["local_variant"]}. {snapshot["label"]}: complete native source', '',
             f'Runtime selector: `BART_FOREST={snapshot["profile"]}`. **SOURCE art, not emulator screenshots.**', '',
             f'Coverage: {report["bg_metatile_count"]} BG IDs / {report["bg_frame_count"]} BG phases, '
             f'plus {report["sprite_frame_count"]} OBJ frames. This includes all {report["topology_alias_count"]} new '
             'render topology pictures and the new wooden-B/landmark frames; original/protected context is explicitly retained.', '',
             '[1×1/2×2/3×3 and concave assemblies](adjacency-islands-source.png) · '
             '[Layer explanations](foreground-layer-diagrams-source.png) · '
             '[Diagnostic physical-footprint overlays](physical-footprint-overlays-source.png) · '
             '[Standing/roll source-only clearance](standing-roll-clearance-source.png)', '',
             '[All47 healthy canopy cases](all47-healthy-cases-source.png) · '
             '[All47 infected canopy cases](all47-blight-cases-source.png) · '
             '[All47 water cases](all47-water-cases-source.png)', '',
             '[Authored palette-pulse source cycle](palette-pulse-source.gif). Only BG blight inks5/6/7/13/14 change; '
             f'indices are fixed and holds are {hold}ms for inspection. This is not the actual game clock. '
             'Shared OBJ/UI/glitter colors are not pulsed. Base PNGs show palette phase0; the four ramps are in the manifest.', '',
             '[Bitmap phase catalog](bitmap-motion-source.gif) · '
             '[Discrete interaction states](interaction-states-source.gif) · '
             '[All assembled groups](assembled-groups-source.png) · '
             '[Value/contour diagnostic](value-contour-diagnostics-source.png)', '',
             'The floor under source islands is explicitly chosen grass/soil. It is not evidence of an automatically '
             'inferred generated underlay. Transparent visual corners retain their semantic collider. '
             'Parity swatches are separate samples; a physical island uses a different adjacency mask for each cell. '
             'The engine world layers are BG2 ground and BG1 foreground around depth-sorted OBJ actors; HUD BG0 stays above.', '',
             'Canonical original canopy pictures and their allocated phases remain in this complete catalog. '
             'In the new forest renderer their semantic IDs select the new adjacency/parity aliases; '
             'the canonical bitmap alone is not a claim of the exact live picture at every position. '
             'Render routes are recorded per original ID. The pulse preview uses a live canopy alias and fixed source indices.', '',
             '| Complete category | Native1× + integer3× atlas |', '| --- | --- |']
    lines += [f'| {a["category"]} | [PNG]({a["path"]}) |' for a in atlas_records]
    lines += ['', '[All native files, IDs, banks, physical metadata and exact hashes](source-manifest.json). '
              'Retained legacy tree/root IDs and static allocated phases are kept honestly in the catalog; '
              'coverage does not imply every old ID is a unique species or every allocated phase visibly animates.']
    (out / 'README.md').write_text('\n'.join(lines).rstrip() + '\n')
    report['files'] = {str(p.relative_to(out)): {'sha256': SHA(p), 'bytes': p.stat().st_size}
                       for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'source-manifest.json'}
    write(out / 'source-manifest.json', report)
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inventory', type=Path, default=INVENTORY)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--profiles', default='6,7,8,9,10')
    ap.add_argument('--hold-ms', type=int, default=180)
    ap.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    ap.add_argument('--profile', type=int, help=argparse.SUPPRESS)
    ap.add_argument('--snapshot', type=Path, help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.worker:
        worker(args); return
    assert args.out and args.hold_ms >= 50 and args.hold_ms % 10 == 0
    profiles = [int(n) for n in args.profiles.split(',')]
    assert profiles == [6, 7, 8, 9, 10], 'Final five-way export requires6..10; use --worker for single-profile diagnostics.'
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True); G.clean_previous_catalog(out)
    hashes, inv_sha = source_hashes(), SHA(args.inventory)
    with tempfile.TemporaryDirectory(prefix='forest-v2-source-') as temp:
        def capture(profile):
            path = Path(temp) / f'{profile}.json'
            command = [sys.executable, str(Path(__file__).resolve()), '--worker', '--profile', str(profile),
                       '--inventory', str(args.inventory.resolve()), '--snapshot', str(path)]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            assert result.returncode == 0, (profile, result.stdout, result.stderr)
            return profile, json.loads(path.read_text())
        with ThreadPoolExecutor(max_workers=3) as pool:
            snapshots = dict(pool.map(capture, sorted(set(profiles + [p - 5 for p in profiles]))))
    chosen = [snapshots[p] for p in profiles]
    reports = [catalog(snapshots[p], snapshots[p - 5], out / f'variant-{p - 5:02}', args.hold_ms) for p in profiles]
    item_board(chosen).save(out / 'five-way-interactions-height-source.png')
    wooden_board(chosen).save(out / 'ten-wooden-chests-source.png')
    folk_board(chosen).save(out / 'fifteen-forest-folk-source.png')
    context_board, context_proof = water_context_board(chosen)
    context_board.save(out / 'isolated-water-three-floors-source.png')
    write(out / 'isolated-water-three-floors-source.json', context_proof)
    before_after([snapshots[p - 5] for p in profiles], chosen).save(out / 'before-after-infection-source.png')
    displayed = [{**s, 'profile': s['local_variant']} for s in chosen]
    matrix, proof = G.complete_native_matrix(displayed)
    for panel in proof['panels']:
        panel['local_variant'] = panel['profile']; panel['profile'] += 5
    matrix.save(out / 'complete-native-source.png'); write(out / 'complete-native-source.json', proof)
    for role in ('npc', 'face', 'interactiveentry', 'forestlandmark'):
        entries = [(e['sheet'], e['name']) for e in chosen[0]['entries'] if e['kind'] == 'sprite' and e['sheet'] == role]
        if entries:G.comparison_board(displayed, f'V2 {role} source', entries).save(out / f'five-way-{role}-source.png')
    assert source_hashes() == hashes, 'Inputs changed during source export; regenerate after source freeze.'
    assert SHA(args.inventory) == inv_sha, 'Inventory changed during source export.'
    report = {'method': __doc__, 'source_only': True, 'profiles': profiles,
              'profile_mapping': {str(p - 5): p for p in profiles}, 'hold_ms': args.hold_ms,
              'git_base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'source_sha256': hashes, 'inventory_sha256': inv_sha,
              'variants': [{k: v for k, v in r.items() if k not in ('frames', 'files', 'baseline_comparison', 'topology')}
                           for r in reports], 'total_frame_instances': sum(r['frame_count'] for r in reports)}
    lines = ['# Five infected-forest directions: complete native source review', '',
             '**SOURCE catalogs, palette-phase previews and layer diagrams; these are not mGBA captures.**', '',
             '![Old and new native infection](before-after-infection-source.png)', '',
             '[Ten wooden chest forms and states](ten-wooden-chests-source.png) · '
             '[Five-way interactions and height](five-way-interactions-height-source.png) · '
             '[Fifteen new folk with matching portraits](fifteen-forest-folk-source.png) · '
             '[Every required native frame](complete-native-source.png) · [Matrix provenance](complete-native-source.json)', '',
             '[Isolated water over three literal source floors](isolated-water-three-floors-source.png). '
             'The known-field test exposes corner opacity; it is not a renderer capture.', '',
             '| New local option | Runtime selector | Complete source catalog |', '| --- | --- | --- |']
    lines += [f'| {r["local_variant"]}. {r["label"]} | `BART_FOREST={r["profile"]}` | '
              f'[All frames,47-case diagrams and true bank-phase preview](variant-{r["local_variant"]:02}/README.md) |' for r in reports]
    lines += ['', 'The old0–5 studies remain separate. Source comparison pairs previous optionN and new optionN '
              'for review; their names are not a claim of direct asset ancestry. Original forest/mystery IDs, '
              'all appended topology aliases and all environment/landmark frames are present. Logical ground '
              'collision is documented separately from foreground transparency and render-only pictures. '
              'The assembled key gate combines two BG bar cells with one large lock OBJ. '
              'Root arches show only a walkable lower route; no accessible upper deck is promised.', '',
              f'Total source coverage: {report["total_frame_instances"]} frame instances. '
              f'Authored four-state BG palette pulse previews use fixed {args.hold_ms}ms inspection holds. '
              'They do not claim engine cadence, screenshot grading or OBJ recoloring. '
              '[Source inputs and exact output hashes](source-manifest.json).']
    (out / 'README.md').write_text('\n'.join(lines).rstrip() + '\n')
    report['files'] = {str(p.relative_to(out)): {'sha256': SHA(p), 'bytes': p.stat().st_size}
                       for p in sorted(out.rglob('*')) if p.is_file() and p != out / 'source-manifest.json'}
    write(out / 'source-manifest.json', report)
    print(json.dumps({'source_only': True, 'profiles': profiles, 'frame_instances': report['total_frame_instances'],
                      'files': len(report['files']), 'out': str(out)}))


if __name__ == '__main__':
    main()
