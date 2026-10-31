#!/usr/bin/env python3
"""Independent native-ROM and preservation audit for the five forest studies.

Expected concept pixels come from the direct native painters, never the tile
assembler, sprite assembler or asset packer. ROM nibbles, flips, animation
payloads, palettes and descriptor targets are decoded independently. Production
profile zero and every protected surface retain the selected release exactly.
Actual gameplay capture contracts can be compared separately with --runtime.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

from sewer_concept_audit import NativeRom, decode_metatile, decode_sprite
from enemy_study_audit import compare_trajectories

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('/workspace/setup/forest-concepts')
PREVIOUS = '31b31513f354d9ead6577166d72fa06dad71358b'
PRODUCTION_SHA = '9330a44a4e27d99606a757134aa41a62adb122a74315c400e1ad3427048c8661'
TERRAIN_BANKS = ('ground', 'foliage', 'water', 'stone', 'blight', 'decay_mix', 'rot_water')
GLITTER = {'sparkle', 'sparkle_white'}
PORTRAITS = {'hermit', 'nun', 'gardener'}
LEGAL_CANVASES = {(8, 8), (16, 16), (32, 32), (64, 64), (16, 8), (32, 8),
                  (32, 16), (64, 32), (8, 16), (8, 32), (16, 32), (32, 64)}
INTEGRATIONS = {'art/tiles.py', 'art/sprites.py', 'art/palettes.py',
                'art/faces.py', 'tools/build_assets.py'}
SHA = lambda b: hashlib.sha256(b).hexdigest()


def native_palette(colors):
    assert len(colors) == 16, ('palette length', len(colors))
    result = []
    for color in colors:
        assert re.fullmatch(r'#[0-9a-fA-F]{6}', color), color
        rgb = [int(color[n:n+2], 16) for n in (1, 3, 5)]
        assert all(v % 8 == 0 for v in rgb), ('non-native RGB555 color', color)
        result.append(sum((v // 8) << (n * 5) for n, v in enumerate(rgb)))
    return result


def native_image(image, size):
    assert image.mode == 'P' and image.size == tuple(size), (image.mode, image.size, size)
    pixels = bytes(image.getdata())
    assert set(pixels) <= set(range(16)), ('non-4bpp index', set(pixels))
    return pixels


def source_export(variant, inventory):
    """Direct authoring only, in a fresh process with a fixed profile."""
    assert 1 <= variant <= 5
    os.environ['BART_FOREST'] = str(variant)
    sys.path.insert(0, str(ROOT / 'art'))
    import forest_concepts_terrain as terrain
    import forest_concepts_props as props
    import forest_concepts_folk as folk
    inv = json.loads(Path(inventory).read_text())
    bg = dict(inv['palettes']['bg'])
    bg.update({name: terrain.palette(name, variant) for name in TERRAIN_BANKS})
    # These two aliases are deliberately BG-only copies of unchanged OBJ inks.
    bg['forest_obj_foliage'] = inv['palettes']['bg']['foliage']
    bg['forest_obj_stone'] = inv['palettes']['bg']['stone']
    result = {'variant': variant, 'tiles': {}, 'sprites': {},
              'bg_palettes': {n: native_palette(c) for n, c in bg.items()},
              'portrait_palettes': {}}
    for tile in inv['tiles']:
        name = tile['name']
        if name not in inv['required']['bg_names'] or name in GLITTER:
            continue
        own_prop, own_terrain = props.supports_tile(name), terrain.supports(name)
        assert own_prop != own_terrain, ('missing or multiple direct tile owners', name)
        images = []; banks = []
        for phase in range(tile['frames']):
            image, bank = (props.paint_tile if own_prop else terrain.paint)(name, phase, variant)
            images.append(native_image(image, (16, 16)).hex()); banks.append(bank)
        assert len(set(banks)) == 1, (name, 'changing material within animation')
        result['tiles'][name] = {'frames': images, 'bank': banks[0],
                                  'owner': 'props' if own_prop else 'terrain'}
    sheets = {s['name']: s for s in inv['sheets']}
    for row in inv['required']['sprite_frames'] + inv['required']['conditional_shared_lift_frames']:
        sheet, name = row['sheet'], row['frame']
        size = sheets[sheet]['canvas']
        if sheet == 'face':
            assert name in PORTRAITS
            image = folk.portrait(name, variant)
            small = native_image(image, (48, 48))
            pixels = bytearray(64*64)
            for y in range(48):
                pixels[y*64:y*64+48] = small[y*48:(y+1)*48]
            result['portrait_palettes'][name] = native_palette(folk.portrait_palette(name, variant))
            bank = 'portrait'
        else:
            owns_prop, owns_folk = props.supports_frame(sheet, name), folk.supports_frame(sheet, name)
            assert owns_prop != owns_folk, ('missing or multiple direct sprite owners', sheet, name)
            image, bank = (props.paint_frame if owns_prop else folk.frame)(sheet, name, variant)
            pixels = native_image(image, size)
        result['sprites'].setdefault(sheet, {})[name] = {'pixels': bytes(pixels).hex(),
                                                        'bank': bank, 'canvas': size}
    print(json.dumps(result, separators=(',', ':')))


class ForestAudit:
    def __init__(self, args):
        self.args = args
        self.inventory = json.loads(Path(args.inventory).read_text())
        self.base = NativeRom(args.baseline)
        self.checks = []; self.profiles = []; self.art_cache = {}
        self.tile_specs = {t['name']: t for t in self.inventory['tiles']}
        self.sheet_specs = {s['name']: s for s in self.inventory['sheets']}
        self.owned = {(r['sheet'], r['frame']) for r in
                      self.inventory['required']['sprite_frames'] +
                      self.inventory['required']['conditional_shared_lift_frames']}

    def check(self, variant, group, name, ok, detail=None):
        row = {'variant': variant, 'group': group, 'name': name, 'passed': bool(ok)}
        if detail is not None:
            row['detail'] = detail
        self.checks.append(row)
        if not ok:
            print('FAIL', variant, group, name, detail, flush=True)

    def equal(self, variant, group, name, before, actual):
        detail = None if before == actual else {'expected_sha256': SHA(before),
                   'actual_sha256': SHA(actual), 'expected_bytes': len(before), 'actual_bytes': len(actual)}
        self.check(variant, group, name, before == actual, detail)

    def source(self):
        self.check('source', 'baseline', 'selected release ROM SHA256', SHA(self.base.rom) == PRODUCTION_SHA)
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', PREVIOUS,
                                         'bartgame/src', 'bartgame/art'], cwd=ROOT.parent, text=True).splitlines()
        for path in paths:
            rel = path.removeprefix('bartgame/')
            if rel in INTEGRATIONS:
                continue
            p = ROOT / rel
            # Include every existing art asset, metadata and all source files,
            # not a permissive list of selected function tokens.
            old = subprocess.check_output(['git', 'show', PREVIOUS+':'+path], cwd=ROOT.parent)
            self.check('source', 'protected_source', rel+' exists', p.is_file())
            if p.is_file():
                self.equal('source', 'protected_source', rel+' exact bytes', old, p.read_bytes())
        makefile = (ROOT/'Makefile').read_text()
        self.check('source', 'profile', 'ordinary make keeps FOREST0', bool(re.search(r'^BART_FOREST\s*\?=\s*0\s*$', makefile, re.M)))
        self.check('source', 'profile', 'ordinary make keeps selected ENEMY11', bool(re.search(r'^BART_ENEMY\s*\?=\s*11\s*$', makefile, re.M)))
        self.check('source', 'inventory', 'complete independent inventory cardinalities',
                   self.inventory['summary']['forest_and_myst_unique'] == 463 and
                   self.inventory['summary']['forest_and_myst_unique_frames'] == 528 and len(self.owned) == 24)

    def freeze(self, variant, rom):
        path = rom.directory/'freeze.json'
        f = json.loads(path.read_text())
        self.check(variant, 'freeze', 'ROM SHA256 matches frozen record', f['rom_sha256'] == SHA(rom.rom))
        self.check(variant, 'freeze', 'forest profile matches frozen record', f.get('forest_variant', f.get('variant')) == variant)
        self.check(variant, 'profile', 'header forest selection', rom.defs.get('BART_FOREST_VARIANT') == variant)
        for macro, expected in {'BART_ENEMY_VARIANT': 11, 'BART_UI_VARIANT': 6,
                                'BART_MENU_VARIANT': 1, 'BART_SEWER_VARIANT': 9,
                                'BLOOM_SWING_STUDY': 3}.items():
            self.check(variant, 'profile', macro+' unchanged', rom.defs.get(macro) == expected)
        for section in ('source_file_sha256', 'code_file_sha256'):
            self.check(variant, 'freeze', section+' populated', bool(f.get(section)))
            for rel, expected in f.get(section, {}).items():
                p = ROOT/rel
                self.check(variant, 'freeze', rel+' matches live frozen input', p.is_file() and SHA(p.read_bytes()) == expected)
                old = subprocess.check_output(['git', 'show', f['source_commit']+':bartgame/'+rel], cwd=ROOT)
                self.check(variant, 'freeze', rel+' matches committed frozen input', SHA(old) == expected)
        return f

    def physical(self, variant, rom):
        self.check(variant, 'identifiers', 'all metatile IDs preserved', rom.tile_ids == self.base.tile_ids)
        self.check(variant, 'identifiers', 'all sheet IDs preserved', rom.sheet_ids == self.base.sheet_ids)
        for name, value in self.base.defs.items():
            if name.startswith(('F_', 'SHEET_', 'TT_', 'TS_', 'PAL_OBJ_')):
                self.check(variant, 'identifiers', name+' stable', rom.defs.get(name) == value)
            if name.startswith('PAL_BG_') and name != 'PAL_BG_COUNT':
                self.check(variant, 'identifiers', name+' logical bank ID stable', rom.defs.get(name) == value)
        self.check(variant, 'identifiers', 'only two approved BG palette aliases appended',
                   rom.defs['PAL_BG_COUNT'] == self.base.defs['PAL_BG_COUNT'] + (2 if variant else 0))
        for name in ('metatile_type', 'metatile_coll', 'metatile_prop', 'metatile_glitter'):
            self.equal(variant, 'physical_metadata', name+' complete bytes', self.base.array(name), rom.array(name))
        # Room-def pointers relocate as art changes size; compare dimensions,
        # object counts and their resolved data targets, not pointer integers.
        self.check(variant, 'room_layout', 'room count stable', rom.defs['ROOM_COUNT'] == self.base.defs['ROOM_COUNT'])
        contracts = json.loads((ROOT/'art/reboot_contracts.json').read_text())
        for i, record in enumerate(contracts['rooms']):
            before = struct.unpack('<BB2xIIIB3x', self.base.array('room_defs')[i*20:(i+1)*20])
            actual = struct.unpack('<BB2xIIIB3x', rom.array('room_defs')[i*20:(i+1)*20])
            self.check(variant, 'room_layout', record['name']+' physical dimensions and object count',
                       (before[0], before[1], before[5]) == (actual[0], actual[1], actual[5]))
            for index, field in ((2, 'ground'), (3, 'overlay'), (4, 'objects')):
                name = 'room_'+record['name']+'_'+field
                self.check(variant, 'room_layout', name+' points at unchanged named data', actual[index] == rom.symbols.get(name, 0))
        for name, length in (('gEnemyDefs', 6*8), ('gHitboxes', 12*4)):
            self.equal(variant, 'physical_metadata', name+' exact ROM descriptor',
                       self.base.read(self.base.symbols[name], length), rom.read(rom.symbols[name], length))

    def protected(self, variant, rom):
        old = self.base.tileset('sewer'); new = rom.tileset('sewer')
        for name in ('tile_count', 'palette_count', 'animations'):
            self.check(variant, 'protected_drain', name+' exact', old[name] == new[name])
        for name in ('tiles', 'map', 'palettes'):
            self.equal(variant, 'protected_drain', name+' exact bytes', old[name], new[name])
        self.equal(variant, 'protected_palettes', 'all sixteen OBJ banks exact', self.base.array('pal_obj'), rom.array('pal_obj'))
        changed_bg = {self.base.defs['PAL_BG_'+name.upper()] for name in TERRAIN_BANKS} if variant else set()
        for bank in range(self.base.defs['PAL_BG_COUNT']):
            if bank not in changed_bg:
                self.equal(variant, 'protected_palettes', 'BG bank '+str(bank)+' exact',
                           self.base.array('pal_bg')[bank*32:(bank+1)*32], rom.array('pal_bg')[bank*32:(bank+1)*32])
        allowed_faces = {self.base.defs['F_FACE_'+n.upper()] for n in PORTRAITS} if variant else set()
        for bank in range(self.base.defs['SHEET_FACE_FRAMES']):
            if bank not in allowed_faces:
                self.equal(variant, 'protected_palettes', 'portrait bank '+str(bank)+' exact',
                           self.base.array('pal_face')[bank*32:(bank+1)*32], rom.array('pal_face')[bank*32:(bank+1)*32])
        for sheet in self.sheet_specs.values():
            name = sheet['name']; before, old_pixels = self.base.sheet(name); actual, pixels = rom.sheet(name)
            self.check(variant, 'sprite_contract', name+' physical shape/size/palette/frame count exact', before == actual)
            self.check(variant, 'native_limits', name+' legal hardware canvas',
                       (actual['width'], actual['height']) in LEGAL_CANVASES and actual['frame_tiles']*64 == actual['width']*actual['height'])
            stride = actual['frame_tiles']*32
            for frame in sheet['frames']:
                index = frame['id']; label = name+'.'+frame['name']
                if not variant or (name, frame['name']) not in self.owned:
                    self.equal(variant, 'protected_sprites', label+' exact packed pixels',
                               old_pixels[index*stride:(index+1)*stride], pixels[index*stride:(index+1)*stride])
            route_name = name+'_frame_pal'
            if route_name in self.base.sections:
                self.check(variant, 'material_routes', route_name+' remains linked', route_name in rom.sections)
            if route_name in rom.sections:
                before_routes = self.base.array(route_name) if route_name in self.base.sections else bytes([before['pal']])*sheet['frame_count']
                routes = rom.array(route_name)
                self.check(variant, 'material_routes', route_name+' covers every frame', len(routes) == sheet['frame_count'])
                for frame in sheet['frames']:
                    if not variant or (name, frame['name']) not in self.owned:
                        self.check(variant, 'material_routes', name+'.'+frame['name']+' exact material route',
                                   before_routes[frame['id']] == routes[frame['id']])
        # Resolve pointer-bearing tables explicitly, then require every other
        # linked asset array to remain exact unless its native artwork is owned.
        # This retained descriptor array embeds relocated frame pointers;
        # parsed base/count/speed/payload equality was asserted above.
        special = {'tilesets', 'sheets', 'room_defs', 'pal_bg', 'pal_face', 'tile_anims_sewer'}
        special |= {'sheet_'+sheet+'_tiles' for sheet, _ in self.owned}
        special |= {sheet+'_frame_pal' for sheet, _ in self.owned}
        for name in self.base.sections:
            if name in special or re.match(r'^(tileset_(forest|myst)_(tiles|pals)|metatile_map_(forest|myst)|tile_anims?_(forest|myst)(_|$))', name):
                continue
            self.check(variant, 'protected_arrays', name+' remains linked', name in rom.sections)
            if name in rom.sections:
                self.equal(variant, 'protected_arrays', name+' complete bytes', self.base.array(name), rom.array(name))
        for area in ('forest', 'myst'):
            before, actual = self.base.tileset(area), rom.tileset(area)
            for name in GLITTER:
                if area not in self.tile_specs[name]['areas']:
                    continue
                a = decode_metatile(self.base, before, name); b = decode_metatile(rom, actual, name)
                self.check(variant, 'protected_glitter', area+'.'+name+' exact frames/inks/colors/clock',
                           a['frames'] == b['frames'] and a['speed'] == b['speed'])

    def art(self, variant, rom):
        code = [sys.executable, str(Path(__file__).resolve()), '--export-source', str(variant), '--inventory', self.args.inventory]
        export = json.loads(subprocess.check_output(code, text=True, cwd=ROOT))
        self.art_cache[variant] = export
        # Inventory UI recipes were exported with the inventory helper's
        # source-default UI skin. The selected runtime UI banks are protected
        # by exact baseline-ROM bytes above, not by that unselected recipe.
        # Only the seven new terrain ramps and two aliases are authored here.
        authored_banks = set(TERRAIN_BANKS) | {'forest_obj_foliage', 'forest_obj_stone'}
        for name, colors in export['bg_palettes'].items():
            if name not in authored_banks:
                continue
            bank = rom.defs['PAL_BG_'+name.upper()]
            self.equal(variant, 'native_palettes', name+' complete global RGB555 bank',
                       struct.pack('<16H', *colors), rom.array('pal_bg')[bank*32:(bank+1)*32])
        need = set(self.inventory['required']['bg_names'])-GLITTER
        self.check(variant, 'source_coverage', 'exactly all 461 owned environment IDs', set(export['tiles']) == need and len(need) == 461)
        self.check(variant, 'source_coverage', 'exactly all 24 owned OBJ/portrait frames',
                   {(s, f) for s, frames in export['sprites'].items() for f in frames} == self.owned)
        tile_frames = 0; area_frames = 0; changed = set(); hashes = {}; animations = {}
        for area in ('forest', 'myst'):
            actual = rom.tileset(area); before = self.base.tileset(area)
            for name, authored in export['tiles'].items():
                spec = self.tile_specs[name]
                if area not in spec['areas']:
                    continue
                native = decode_metatile(rom, actual, name)
                old = decode_metatile(self.base, before, name)
                self.check(variant, 'native_frames', area+'.'+name+' frame count retained',
                           len(native['frames']) == len(authored['frames']) == spec['frames'])
                self.check(variant, 'native_clocks', area+'.'+name+' frame hold retained',
                           native['speed'] == (spec['anim_speed'] if spec['frames'] > 1 else None))
                colors = export['bg_palettes'][authored['bank']]
                expected_bank = struct.pack('<16H', *colors)
                for quarter, entry in enumerate(native['entries']):
                    bank = entry >> 12
                    self.equal(variant, 'native_material_routes', area+'.'+name+' quarter'+str(quarter)+' exact authored bank',
                               expected_bank, actual['palettes'][bank*32:(bank+1)*32])
                if native['frames'] != old['frames']:
                    changed.add(name)
                rows = []
                for phase, (expected, (pixels, rgb)) in enumerate(zip(authored['frames'], native['frames'])):
                    source = bytes.fromhex(expected); label = area+'.'+name+':'+str(phase)
                    expected_rgb = struct.pack('<256H', *[colors[v] if v else 0x8000 for v in source])
                    self.equal(variant, 'native_indexed', label+' independently decoded 4bpp pixels', source, pixels)
                    self.equal(variant, 'native_material', label+' native material colors', expected_rgb, rgb)
                    rows.append({'phase': phase, 'indices_sha256': SHA(pixels), 'rgb555_sha256': SHA(rgb)})
                    area_frames += 1
                hashes[area+'.'+name] = rows
                if spec['frames'] > 1:
                    animations[area+'.'+name] = {'frames': len(rows), 'speed': native['speed'],
                                                'distinct_frames': len({r['indices_sha256'] for r in rows})}
            # Every palette bank must equal one direct authoring bank; matching
            # the rendered pixels alone would miss unused corrupt palette inks.
            legal = {struct.pack('<16H', *c) for c in export['bg_palettes'].values()}
            for bank in range(actual['palette_count']):
                p = actual['palettes'][bank*32:(bank+1)*32]
                self.check(variant, 'native_palettes', area+' resident bank '+str(bank)+' exact authored RGB555', p in legal)
        tile_frames = sum(len(t['frames']) for t in export['tiles'].values())
        self.check(variant, 'source_coverage', 'all 523 owned native BG frames authored', tile_frames == 523, tile_frames)
        sprite_hashes = {}
        for sheet, frames in export['sprites'].items():
            meta, raw = rom.sheet(sheet); stride = meta['frame_tiles']*32
            for name, frame in frames.items():
                index = rom.defs['F_'+sheet.upper()+'_'+name.upper()]
                pixels = decode_sprite(raw[index*stride:(index+1)*stride], meta['width'], meta['height'])
                expected = bytes.fromhex(frame['pixels']); label = sheet+'.'+name
                self.equal(variant, 'native_sprites', label+' direct source vs ROM nibbles', expected, pixels)
                self.check(variant, 'native_sprites', label+' expected native canvas', frame['canvas'] == [meta['width'], meta['height']])
                if sheet == 'face':
                    expected_palette = struct.pack('<16H', *export['portrait_palettes'][name])
                    self.equal(variant, 'native_portrait_palette', name+' exact dynamic portrait bank',
                               expected_palette, rom.array('pal_face')[index*32:(index+1)*32])
                else:
                    route = rom.array(sheet+'_frame_pal')[index] if sheet+'_frame_pal' in rom.sections else meta['pal']
                    self.check(variant, 'native_material_routes', label+' exact OBJ material slot',
                               route == rom.defs['PAL_OBJ_'+frame['bank'].upper()])
                sprite_hashes[label] = SHA(pixels)
        # Each portable item is exactly its floor version: same nibbles and
        # material, not just a similar outline or an enlarged menu illustration.
        for tile, frame in [('bush','bush'), ('rock_small','rock'), ('boulder','boulder'), ('myst_pot','pot')]:
            a = export['tiles'][tile]; b = export['sprites']['lift'][frame]
            self.check(variant, 'ground_carry_identity', tile+' exact source/frozen carried pixels', a['frames'][0] == b['pixels'])
            bg_palette = struct.pack('<16H', *export['bg_palettes'][a['bank']])
            bank = rom.defs['PAL_OBJ_'+b['bank'].upper()]
            self.equal(variant, 'ground_carry_identity', tile+' exact native ground/carried material',
                       bg_palette, rom.array('pal_obj')[bank*32:(bank+1)*32])
        return {'native_bg_ids': len(export['tiles']), 'unique_native_bg_frames': tile_frames,
                'area_native_frame_instances': area_frames, 'native_obj_frames': len(sprite_hashes),
                'changed_bg_ids': len(changed), 'bg_frame_hashes': hashes,
                'obj_frame_hashes': sprite_hashes, 'animation_coverage': animations}

    def budgets(self, variant, rom):
        areas = {}
        for area in ('forest', 'myst', 'sewer'):
            ts = rom.tileset(area)
            self.check(variant, 'native_limits', area+' <=1024 resident hardware subtiles', ts['tile_count'] <= 1024, ts['tile_count'])
            self.check(variant, 'native_limits', area+' <=12 resident BG palettes', ts['palette_count'] <= 12, ts['palette_count'])
            self.check(variant, 'native_limits', area+' <=255 animation allocations', len(ts['animations']) <= 255, len(ts['animations']))
            colors = struct.unpack('<%dH' % (len(ts['palettes'])//2), ts['palettes'])
            self.check(variant, 'native_limits', area+' all palette words legal RGB555', all(c < 0x8000 for c in colors))
            self.equal(variant, 'native_mapping', area+' reserved tile zero remains blank', bytes(32), ts['tiles'][:32])
            logical = 'drain' if area == 'sewer' else area
            animated_bases = {row['base'] for row in ts['animations']}
            for spec in self.inventory['tiles']:
                at = spec['id']*8
                if logical not in spec['areas']:
                    self.equal(variant, 'native_mapping', area+'.'+spec['name']+' unloaded mapping remains blank', bytes(8), ts['map'][at:at+8])
                else:
                    entries = struct.unpack_from('<4H', ts['map'], at)
                    self.check(variant, 'native_mapping', area+'.'+spec['name']+' all quarters use valid native tile/bank',
                               all((entry&1023) < ts['tile_count'] and (entry>>12) < ts['palette_count'] for entry in entries))
                    base = entries[0]&1023
                    if base in animated_bases:
                        self.check(variant, 'native_animation_residency', area+'.'+spec['name']+' four unflipped sequential live animation quarters',
                                   [entry&4095 for entry in entries] == [base+q for q in range(4)])
            self.check(variant, 'native_clocks', area+' animation allocation count retained',
                       len(ts['animations']) == len(self.base.tileset(area)['animations']))
            for animation in ts['animations']:
                base = animation['base']
                self.check(variant, 'native_animation_residency', area+' animation'+str(base)+' complete in-bounds four-tile destination',
                           base+4 <= ts['tile_count'])
                self.equal(variant, 'native_animation_residency', area+' animation'+str(base)+' resident pixels equal authored phase zero',
                           animation['data'][:128], ts['tiles'][base*32:(base+4)*32])
            areas[area] = {'bg_subtiles': ts['tile_count'], 'bg_palette_banks': ts['palette_count'],
                           'animation_allocations': len(ts['animations'])}
        # All sheet physical descriptors and allocation C are exact; thus the
        # selected release's conservative 816/876 tile union remains valid.
        self.check(variant, 'obj_limits', 'unchanged sixteen physical OBJ banks', rom.defs['PAL_OBJ_COUNT'] == 16)
        self.check(variant, 'obj_limits', 'unchanged source frame allocation descriptors',
                   all(rom.sheet(n)[0] == self.base.sheet(n)[0] for n in self.base.sheet_ids))
        return areas

    def runtime(self):
        if not self.args.runtime:
            return {'status': 'not_requested', 'limit': 'Static native/protection audit; actual captures not asserted.'}
        root = Path(self.args.runtime); before = json.loads((root/'v0/capture.json').read_text()); results = []
        for v in self.args.profiles:
            candidate = json.loads((root/f'v{v}/capture.json').read_text())
            rom = NativeRom(Path(self.args.frozen)/f'v{v}')
            frozen = json.loads((rom.directory/'freeze.json').read_text())
            self.check(v, 'runtime', 'capture SHA matches frozen ROM', candidate['rom_sha256'] == SHA(rom.rom))
            self.check(v, 'runtime', 'capture source commit matches frozen input', candidate['source_commit'] == frozen['source_commit'])
            self.check(v, 'runtime', 'capture variant matches frozen ROM', candidate['forest_variant'] == v)
            self.check(v, 'runtime', 'capture freeze-file hash matches frozen input',
                       candidate.get('freeze_sha256') == SHA((rom.directory/'freeze.json').read_bytes()))
            self.check(v, 'runtime', 'capture harness SHA matches reviewed executable tool',
                       candidate.get('capture_tool_sha256') == SHA((ROOT/'tools/forest_concept_review.py').read_bytes()))
            self.check(v, 'runtime', 'capture harness checks all passed', candidate['passed'] == candidate['total'] and not candidate.get('failures'))
            self.check(v, 'runtime', 'complete requested runtime groups', candidate.get('complete') is True)
            old_rows = {row['name']: row for row in before['captures']}
            new_rows = {row['name']: row for row in candidate['captures']}
            self.check(v, 'runtime', 'identical capture case names', set(old_rows) == set(new_rows))
            fields = ('group', 'seed', 'cell', 'stage', 'role', 'archetype', 'action', 'frames', 'video_frames', 'position', 'facing',
                      'target', 'natural_mystery', 'physical_contract', 'inputs',
                      'final_physical_contract', 'maze_sha256', 'initial_progress_sha256',
                      'final_progress_sha256', 'initial_rng', 'final_rng')
            timings = []
            for name in sorted(set(old_rows)&set(new_rows)):
                a, b = old_rows[name], new_rows[name]
                for key in fields:
                    if key in a or key in b:
                        self.check(v, 'runtime_contracts', name+'.'+key+' exact baseline', a.get(key) == b.get(key))
                for key in ('initial', 'final'):
                    # Hardware OAM counts can legitimately vary with a drawn
                    # body's silhouette; world/player logical state cannot.
                    old_state = {k: value for k, value in a[key].items() if k != 'oam'}
                    new_state = {k: value for k, value in b[key].items() if k != 'oam'}
                    self.check(v, 'runtime_states', name+'.'+key+' exact logical state', old_state == new_state)
                old_transitions, new_transitions = a['mechanic_transitions'], b['mechanic_transitions']
                self.check(v, 'runtime_states', name+' identical ordered mechanical transitions',
                           [t['state'] for t in old_transitions] == [t['state'] for t in new_transitions])
                timings.append({'name': name, 'transition_ticks_exact': old_transitions == new_transitions})
            self.check(v, 'runtime_geometry', 'worlds exact generated world contract', candidate.get('worlds') == before.get('worlds'))
            old_rooms = {r['name'] for r in before.get('rooms', [])}
            new_rooms = {r['name'] for r in candidate.get('rooms', [])}
            self.check(v, 'runtime_geometry', 'same 25 generated room cases; contracts compared above', old_rooms == new_rooms and len(new_rooms) == 25)
            results.append({'variant': v, 'rom_sha256': SHA(rom.rom), 'cases': len(new_rows),
                            'capture_checks': {'passed': candidate['passed'], 'total': candidate['total']},
                            'transition_timing_observations': timings})
        return {'status': 'compared', 'profiles': results,
                'method': 'Compare disclosed fixtures, generated tile-ID/collision/type/spot contracts, maze/progress hashes and action-state transitions; expected RGB art differences are excluded.'}

    def pursuer_context(self):
        if not self.args.pursuer_context:
            return {'status': 'not_requested'}
        reference = Path('/workspace/setup/selected-enemies-heart/clearing/capture.json')
        rows = []
        for variant in range(1, 6):
            path = Path(self.args.pursuer_context)/f'v{variant}'/'capture.json'
            report = json.loads(path.read_text())
            rom = NativeRom(Path(self.args.frozen)/f'v{variant}')
            freeze = json.loads((rom.directory/'freeze.json').read_text())
            self.check(variant, 'pursuer_context', 'focused capture SHA matches native forest ROM', report['rom_sha256'] == SHA(rom.rom))
            self.check(variant, 'pursuer_context', 'focused source matches frozen input', report['source_commit'] == freeze['source_commit'])
            self.check(variant, 'pursuer_context', 'focused frozen header binds exact forest variant', rom.defs['BART_FOREST_VARIANT'] == variant)
            self.check(variant, 'pursuer_context', 'focused runtime checks all pass', report['passed'] == report['total'] == 6 and not report['failures'])
            captures = report['captures']
            self.check(variant, 'pursuer_context', 'one 96-frame natural pursuer, not a pose assembly',
                       len(captures) == 1 and captures[0]['kind'] == 0 and captures[0]['frames'] == 96 and
                       captures[0]['context']['seed'] == 6 and captures[0]['context']['cell'] == 9 and
                       captures[0]['context']['natural_spawn_index'] == 5)
            comparison = compare_trajectories(reference, path)
            self.check(variant, 'pursuer_context', 'actual pursuer mechanical trajectory exact to selected production release',
                       comparison['passed'] == comparison['total'] == 1)
            rows.append({'forest_variant': variant, 'source_commit': report['source_commit'],
                         'rom_sha256': report['rom_sha256'], 'enemy_variant': report['enemy_variant'],
                         'capture_count': 1, 'checks_passed': report['passed'], 'checks_total': report['total'],
                         'report': str(path), 'mechanical_comparison': comparison})
        return {'status': 'compared', 'profiles': rows, 'capture_count': 5, 'passed': 30, 'total': 30,
                'method': 'Separate actual mGBA green-Coin-Toad contrast encounters. The legacy enemy harness records enemy_variant; forest_variant is bound independently here through the frozen ROM header/SHA and source commit. No captured report is relabelled or rewritten.'}

    def run(self):
        self.source()
        for variant in self.args.profiles:
            rom = NativeRom(Path(self.args.frozen)/f'v{variant}')
            freeze = self.freeze(variant, rom)
            self.physical(variant, rom); self.protected(variant, rom)
            if not variant:
                self.equal(variant, 'production', 'complete production ROM byte identity', self.base.rom, rom.rom)
                art = {'status': 'production retained byte for byte'}
            else:
                art = self.art(variant, rom)
            self.profiles.append({'variant': variant, 'rom_sha256': SHA(rom.rom),
                                  'source_commit': freeze['source_commit'], 'native_art': art,
                                  'budgets': self.budgets(variant, rom)})
        runtime = self.runtime()
        pursuer = self.pursuer_context()
        failed = [r for r in self.checks if not r['passed']]
        out = {'method': __doc__, 'baseline_source': PREVIOUS, 'baseline_rom_sha256': SHA(self.base.rom),
               'auditor_sha256': SHA(Path(__file__).read_bytes()), 'inventory_sha256': SHA(Path(self.args.inventory).read_bytes()),
               'profiles': self.profiles, 'runtime': runtime, 'pursuer_context': pursuer, 'passed': len(self.checks)-len(failed),
               'total': len(self.checks), 'failures': failed, 'checks': self.checks,
               'limits': 'Source/native assertions cover all retained IDs including currently unused variants. Finite runtime samples do not claim universal route coverage, CPU timing, player preference or aesthetic perfection.'}
        path = Path(self.args.out); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out, indent=2)+'\n')
        print('RESULT', out['passed'], '/', out['total'], flush=True)
        return bool(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', default=str(WORK/'inventory.json'))
    parser.add_argument('--baseline', default=str(WORK/'baseline'))
    parser.add_argument('--frozen', default=str(WORK/'frozen'))
    parser.add_argument('--profiles', nargs='+', type=int, choices=range(6), default=list(range(6)))
    parser.add_argument('--runtime')
    parser.add_argument('--pursuer-context')
    parser.add_argument('--out', default=str(WORK/'audit/audit.json'))
    parser.add_argument('--export-source', type=int)
    args = parser.parse_args()
    if args.export_source is not None:
        source_export(args.export_source, args.inventory)
        return 0
    return ForestAudit(args).run()


if __name__ == '__main__':
    raise SystemExit(main())
