"""Capture healthy woodland and matched controls from the actual ROM in mGBA.

python tools/healthy_review.py BEFORE --positions PREVIOUS/capture.json
python tools/healthy_review.py AFTER --match BEFORE/capture.json \
    --changed-materials changed-materials.json

The optional changed-materials file is an explicit list of exact metatile
names (or an object containing ``changed_names``). Deep-room controls retain
their visible differences; every changed pixel must lie in an actual rendered
cell containing one of those deliberately shared materials. Drain controls
must match exactly. Native PNG framebuffers are never modified.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

import blight_review as B
import critical_path as C
import lift_probe as L
import probe as P


FEATURES = {
    'great-tree': ('gtree_', 'gtree2_'),
    'oak': ('tree_top_', 'tree_mid_', 'tree_trunk_', 'tree2_'),
    'birch': ('birch_',),
    'fir': ('fir_',),
    'path-canopy': ('path', 'pedge_'),
    'pond-bank': ('water', 'shore_', 'bridge'),
    'ground-growths': ('fern_patch', 'leaf_litter', 'bush', 'moss_flowers'),
}
TREE_ANCHORS = {
    'great-tree': ('gtree_9', 'gtree2_9'),
    'oak': ('tree_trunk_w', 'tree2_4'),
    'birch': ('birch_4',),
    'fir': ('fir_4',),
}
FIXTURE_VERSION = 3


def camera_for(w, h, x, y):
    return max(0, min(w * 16 - 240, x * 16 + 8 - 120)), max(0, min(h * 16 - 160, y * 16 + 12 - 104))


def focus(c, names, feature):
    """Choose a real safe standing point which shows the complete material."""
    w, h, tiles, walk = B.grid(c, names)
    prefixes = FEATURES[feature]
    targets = [p for p, ns in tiles.items() if any(n.startswith(prefixes) for n in ns)]
    if feature in TREE_ANCHORS:
        targets = [p for p, ns in tiles.items() if any(n in TREE_ANCHORS[feature] for n in ns)]
    if not targets or not walk:
        return None

    def score(p):
        cx, cy = camera_for(w, h, *p)
        visible = []
        for tx, ty in targets:
            sx, sy = tx * 16 - cx, ty * 16 - cy
            if feature in TREE_ANCHORS:
                tw, th = (48, 64) if feature == 'great-tree' else (32, 48)
                top = sy + 16 - th
                if 8 <= sx and sx + tw <= 232 and 35 <= top and sy + 16 <= 148:
                    visible.append((sx + tw / 2, top + th / 2))
            elif 8 <= sx <= 216 and 36 <= sy <= 132:
                visible.append((sx + 8, sy + 8))
        if not visible:
            return -1000000, 0
        center = min(abs(x - 120) + abs(y - 80) for x, y in visible)
        viewed = []
        for (tx, ty), ns in tiles.items():
            sx, sy = tx * 16 - cx, ty * 16 - cy
            if -8 <= sx <= 240 and 28 <= sy <= 152:
                viewed.extend(ns)
        diversity = len(set(n for n in viewed if n != 'none'))
        canopy = sum(n.startswith(('forest_canopy', 'canopy', 'tree', 'gtree', 'birch', 'fir')) for n in viewed)
        water = sum(n.startswith(('water', 'shore_', 'bridge')) for n in viewed)
        paths = sum(n.startswith(('path', 'pedge_')) for n in viewed)
        value = 1000 + min(len(visible), 16) * 12 + diversity * 3 - center * 4
        if feature == 'path-canopy':
            value += min(canopy, 24) * 5 + min(paths, 24) * 5
        elif feature == 'pond-bank':
            value += min(water, 36) * 6 + min(paths, 12) * 3
        return value, len(visible)

    point = max(walk, key=lambda p: score(p)[0])
    value, visible = score(point)
    if value < 0:
        return None
    return {'position': [point[0] * 16 + 8, point[1] * 16 + 12],
            'focus_score': value, 'visible_feature_tiles': visible}


def allowed_names(path):
    if not path:
        return set()
    data = json.loads(Path(path).read_text())
    names = data['changed_names'] if isinstance(data, dict) else data
    assert isinstance(names, list) and all(isinstance(n, str) for n in names)
    return {n.removeprefix('MT_').lower() for n in names}


def visual_control(c, names, world, view, before, after, changed_materials):
    changed = [(i % 240, i // 240) for i, (a, b) in enumerate(zip(before.getdata(), after.getdata())) if a != b]
    result = {'file': view['image'], 'identical': not changed, 'different_pixels': len(changed)}
    if not changed:
        return result
    if 'cell' not in view or not changed_materials:
        return result
    cell = view['cell']
    desc = world['cells'][cell]
    L.warp(c, cell, next(i for i, g in enumerate(desc['gate']) if g))
    B.settle(c, view['position'])
    camera = [P.r16(c, P.sym('gCamX')), P.r16(c, P.sym('gCamY'))]
    assert camera == view['camera'], (cell, camera, view['camera'])
    room = P.sym('gRoom')
    w, h = P.r8(c, room), P.r8(c, room + 1)
    prop = P.sym('metatile_prop')
    bounds = []
    for ty in range(h):
        for tx in range(w):
            at = ty * 32 + tx
            mt = P.r16(c, room + 2 + at * 2) & 65535
            ov = P.r16(c, room + 2050 + at * 2) & 65535
            under = P.r16(c, room + 8194 + at * 2) & 65535
            # Match room.c::render_cell: the underlay is visible only under
            # a transparent prop, not merely because a stale field names it.
            rendered = {names.get(mt, 'none'), names.get(ov, 'none')}
            if mt != 65535 and P.r8(c, prop + mt) and under not in (65535, mt):
                rendered.add(names.get(under, 'none'))
            materials = sorted(rendered & changed_materials)
            if not materials:
                continue
            x0, y0 = max(0, tx * 16 - camera[0]), max(0, ty * 16 - camera[1])
            x1, y1 = min(240, (tx + 1) * 16 - camera[0]), min(160, (ty + 1) * 16 - camera[1])
            if x0 < x1 and y0 < y1:
                bounds.append({'metatile': [tx, ty], 'framebuffer_rect': [x0, y0, x1, y1], 'materials': materials})
    inside = bool(bounds) and all(any(b['framebuffer_rect'][0] <= x < b['framebuffer_rect'][2] and
                                     b['framebuffer_rect'][1] <= y < b['framebuffer_rect'][3]
                                     for b in bounds) for x, y in changed)
    result.update(allowed_changed_materials=sorted(changed_materials),
                  allowed_changed_bounds=bounds, changed_pixels_within_materials=inside,
                  retained_pixels_identical=inside)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('out')
    ap.add_argument('--rom', default=P.ROM)
    ap.add_argument('--map', default=P.MAP)
    ap.add_argument('--assets-header', default=str(Path(P.ROOT) / 'build/gen/assets.h'))
    ap.add_argument('--seed', default='0xB4A7')
    ap.add_argument('--positions', help='Reuse room standing points from a prior capture family')
    ap.add_argument('--match', help='Reuse healthy feature plan and compare physics/control images')
    ap.add_argument('--changed-materials', help='Explicit exact material-name JSON for deliberate shared changes')
    ap.add_argument('--no-gifs', action='store_true')
    args = ap.parse_args()
    assert not (args.positions and args.match), 'choose positions or match'
    P.MAP, P._syms = args.map, None
    names = B.definitions(args.assets_header)
    old = json.loads(Path(args.match).read_text()) if args.match else None
    positions = old or (json.loads(Path(args.positions).read_text()) if args.positions else None)
    seed = int(positions['seed'], 0) if positions else int(args.seed, 0)
    changed_materials = allowed_names(args.changed_materials)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    c = P.boot(rom=args.rom, seed=seed)
    C.dismiss(c)
    B.settle(c, [200, 270])
    P.snap(c, str(out / 'drain-control.png'))
    report = {'seed': hex(seed), 'rom_sha256': hashlib.sha256(Path(args.rom).read_bytes()).hexdigest(),
              'fixture_version': FIXTURE_VERSION, 'emulator': 'mGBA 0.10.5',
              'method': 'Native240x160 mGBA framebuffers. Real generated terrain and animation; debug room navigation, safe standing points, healing, cleared enemies/ambient firefly actors, settled camera, then animationclock0 and64 real frames. GIFs sample96 actual frames at everyother frame and enlarge2xNN.',
              'drain_image': 'drain-control.png', 'rooms': [], 'features': [], 'animations': [],
              'allowed_shared_materials': sorted(changed_materials)}
    world = C.world(c)
    P.enter_forest(c)
    for cell, desc in enumerate(world['cells']):
        L.warp(c, cell, next(i for i, g in enumerate(desc['gate']) if g))
        previous = next((r for r in positions['rooms'] if r['cell'] == cell), None) if positions else None
        position = previous['position'] if previous else B.focus(c, names)
        if desc['role'] == 2 and not previous:
            position = [256, 240]
        B.settle(c, position)
        filename = f'room-{cell:02d}-stage{desc["stage"]}.png'
        P.snap(c, str(out / filename))
        report['rooms'].append({'cell': cell, 'stage': desc['stage'], 'role': desc['role'],
                                'position': position, 'camera': [P.r16(c, P.sym('gCamX')), P.r16(c, P.sym('gCamY'))],
                                'image': filename, **B.contract(c)})
        print('CAPTURE', cell, 'stage', desc['stage'], position, flush=True)
    plan = list(old['features']) if old else []
    if not old:
        for feature in FEATURES:
            candidates = []
            for cell, desc in enumerate(world['cells']):
                if desc['stage'] > 1:
                    continue
                L.warp(c, cell, next(i for i, g in enumerate(desc['gate']) if g))
                view = focus(c, names, feature)
                if view:
                    candidates.append((view['focus_score'], desc['stage'] == 0, cell, view))
            if candidates:
                _, _, cell, view = max(candidates, key=lambda v: v[:3])
                plan.append({'feature': feature, 'cell': cell, 'stage': world['cells'][cell]['stage'],
                             'image': feature + '.png', **view})
    for view in plan:
        cell = view['cell']
        desc = world['cells'][cell]
        L.warp(c, cell, next(i for i, g in enumerate(desc['gate']) if g))
        B.settle(c, view['position'])
        P.snap(c, str(out / view['image']))
        report['features'].append(dict(view, **B.contract(c)))
        if not args.no_gifs and view['feature'] in ('great-tree', 'path-canopy', 'pond-bank'):
            report['animations'].append(B.gif(c, out / (view['feature'] + '.gif')))
        print('FEATURE', view['feature'], cell, view['position'], flush=True)
    reference = old or positions
    if reference:
        keys = ('logical_sha256', 'solid_sha256', 'spots_sha256')
        changes = [{'cell': a['cell'], 'field': k} for a, b in zip(report['rooms'], reference['rooms']) for k in keys if a[k] != b[k]]
        report['physical_comparison'] = {'checked_rooms': len(report['rooms']),
                                         'unchanged_rooms': len(report['rooms']) - len({v['cell'] for v in changes}),
                                         'differences': changes}
        assert not changes, changes
    if old:
        assert old.get('fixture_version') == FIXTURE_VERSION
        report['visual_controls'] = []
        controls = [{'image': 'drain-control.png'}] + [r for r in report['rooms'] if r['stage'] >= 3]
        for view in controls:
            filename = view['image']
            before = Image.open(Path(args.match).parent / filename).convert('RGB')
            after = Image.open(out / filename).convert('RGB')
            control = visual_control(c, names, world, view, before, after, changed_materials)
            report['visual_controls'].append(control)
            print('CONTROL', 'PASS' if control['identical'] else 'SHARED_MATERIALS_ONLY' if control.get('retained_pixels_identical') else 'DIFF', filename, control['different_pixels'], flush=True)
    (out / 'capture.json').write_text(json.dumps(report, indent=2) + '\n')
    assert all(v['identical'] or v.get('retained_pixels_identical') for v in report.get('visual_controls', [])), report.get('visual_controls')
    print('PASS:', len(report['rooms']), 'generated rooms,', len(report['features']), 'healthy feature views', flush=True)


if __name__ == '__main__':
    main()
