#!/usr/bin/env python3
"""Read-only native ROM audit of the five optional Cream environment studies.

No build is performed. Hardware BG flips, per-quarter palettes, animation
payloads and OBJ 1D nibbles are decoded independently of the asset builder.
Native/source fidelity and preservation are mechanical checks. Family pixel
and edge comparisons describe geometric differences; they do not rate art,
prove depth/readability, or establish collision/rendering agreement in play.
"""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

from sewer_concept_audit import NativeRom, SHAPES, decode_metatile, decode_sprite

ROOT = Path(__file__).resolve().parent.parent
BASELINE_SHA = '0dd8554384b53e618140f8c61590fc7e6a7ff0888f296ece034a95f357b34fdd'
STYLES = {0: 'original', 1: 'karst', 2: 'basilica', 3: 'moldglass', 4: 'quarry', 5: 'rind'}
sha = lambda data: hashlib.sha256(data).hexdigest()


def native_color(color):
    assert re.fullmatch(r'#[0-9a-fA-F]{6}', color), color
    values = [int(color[i:i+2], 16) for i in (1, 3, 5)]
    assert all(v % 8 == 0 for v in values), ('non-RGB555 source', color)
    return sum((v // 8) << (5 * i) for i, v in enumerate(values))


def source_export(variant, options):
    """A separate process avoids painter caches leaking across studies."""
    for key, value in options.items():
        if key.startswith('BART_'): os.environ[key] = str(value)
    os.environ['BART_CREAM'] = str(variant)
    sys.path.insert(0, str(ROOT / 'art'))
    import cream_terrain as terrain
    import cream_actors as actors
    palettes = {name: [native_color(c) for c in colors]
                for name, colors in terrain.PALETTES.items()}
    result = {'variant': variant, 'palettes': palettes, 'tiles': {}}
    for tile in terrain.METATILES:
        name = tile['name']
        assert name.startswith('cream_') and name not in result['tiles']
        frames = []
        for rows in tile.get('frames') or [tile['art']]:
            assert len(rows) == 16 and all(len(row) == 16 for row in rows), name
            assert all(c in '. 0123456789abcdefABCDEF' for row in rows for c in row), name
            pixels = bytes(0 if c in '. ' else int(c, 16) for row in rows for c in row)
            frames.append(pixels.hex())
        result['tiles'][name.upper()] = {
            'frames': frames, 'palettes': tile.get('qpals') or [tile['pal']] * 4,
            'type': tile['type'], 'coll': tile['coll'],
            'prop': int(bool(tile.get('prop'))), 'glitter': int(bool(tile.get('glitter'))),
            'speed': tile.get('anim_speed', 8) if len(frames) > 1 else None,
        }
    doors = next(sheet for sheet in actors.build_sheets() if sheet['name'] == 'creamdoors')
    raw_return = doors['frames']['return']
    assert doors['w'] == 32 and doors['h'] == 64 and len(raw_return) == 64
    assert all(len(row) == 32 for row in raw_return)
    result['cream_return'] = bytes(0 if c in '. ' else int(c, 16) for row in raw_return for c in row).hex()
    print(json.dumps(result, separators=(',', ':')))


def family(name):
    name = name.lower().removeprefix('cream_')
    for group, prefixes in (
        ('floor', ('floor_', 'path_')), ('cliff', ('cliff_',)),
        ('ledge', ('rim_', 'drop_', 'pit_')), ('climb', ('climb_',)),
        ('entrance', ('cave_s',)), ('barrier', ('cave_web', 'cave_crack', 'cave_ward', 'thorn_', 'web_', 'crack_', 'ward')),
        ('liquid', ('water_', 'fall_')), ('chest', ('chest_',)),
    ):
        if name.startswith(prefixes): return group
    return 'props'


def canonical(pixels):
    """Remove arbitrary ink numbering, preserving zero and colour boundaries."""
    labels = {0: 0}
    return bytes(labels.setdefault(value, len(labels)) for value in pixels)


def edges(pixels):
    return bytes(int(pixels[y*16+x] != pixels[y*16+x+1]) for y in range(16) for x in range(15)) + bytes(
        int(pixels[y*16+x] != pixels[(y+1)*16+x]) for y in range(15) for x in range(16))


def rodata(rom, name):
    match = re.search(r'^\s+\.rodata\.' + re.escape(name) + r'\s+0x([\da-fA-F]+)\s+0x([\da-fA-F]+)\s+\S+\s*$', rom.linker, re.M)
    assert match, ('linked section missing', name)
    return rom.read(int(match[1], 16), int(match[2], 16))


def songs(rom):
    table = rodata(rom, 'gOriginalSongs')
    result = []
    assert len(table) % 24 == 0
    for offset in range(0, len(table), 24):
        pcm, count, loop, total_frames, loop_frame, source_id, title = struct.unpack_from('<IIIHHH2xI', table, offset)
        name = bytearray()
        if title:
            while len(name) < 256:
                char = rom.read(title + len(name), 1)
                if char == b'\0': break
                name.extend(char)
            else: raise AssertionError('unterminated music title')
        result.append((bool(pcm), count, loop, total_frames, loop_frame, source_id, bytes(name)))
    return result


class Audit:
    def __init__(self, args):
        self.args = args
        self.base = NativeRom(args.baseline)
        self.checks = []
        self.results = []
        self.records = {}
        self.out = Path(args.out)
        self.out.parent.mkdir(parents=True, exist_ok=True)

    def check(self, label, group, name, passed, detail=None):
        row = dict(bundle=label, group=group, name=name, passed=bool(passed))
        if detail is not None: row['detail'] = detail
        self.checks.append(row)
        if not passed: print('FAIL', label, group, name, detail, flush=True)

    def equal(self, label, group, name, before, after):
        self.check(label, group, name, before == after,
                   None if before == after else {'before_sha256': sha(before), 'after_sha256': sha(after),
                                                 'before_bytes': len(before), 'after_bytes': len(after)})

    def scope(self, label, rom, variant):
        before = self.base
        self.check(label, 'identifiers', 'all metatile IDs/count unchanged', before.tile_ids == rom.tile_ids)
        self.check(label, 'identifiers', 'all sprite sheet IDs/count unchanged', before.sheet_ids == rom.sheet_ids)
        ids = {k: v for k, v in before.defs.items() if k.startswith(('F_', 'SHEET_', 'TS_', 'PAL_'))}
        self.check(label, 'identifiers', 'all frame/canvas/palette/tileset constants unchanged', all(rom.defs.get(k) == v for k, v in ids.items()))
        for name in ('metatile_type', 'metatile_coll', 'metatile_prop', 'metatile_glitter'):
            self.equal(label, 'physics_and_glitter', name, before.array(name), rom.array(name))
        for area in ('forest', 'sewer', 'myst', 'cream'):
            old, new = before.tileset(area), rom.tileset(area)
            self.check(label, 'native_limits', area + ' BG 4bpp tile budget', 0 < new['tile_count'] <= 1024, new['tile_count'])
            self.check(label, 'native_limits', area + ' BG palette budget', 0 < new['palette_count'] <= 12, new['palette_count'])
            self.check(label, 'native_limits', area + ' RGB555 palette words', all(v < 0x8000 for v in struct.unpack('<%dH' % (len(new['palettes'])//2), new['palettes'])))
            for entry in struct.unpack('<%dH' % (len(new['map'])//2), new['map']):
                assert (entry & 1023) < new['tile_count'] and entry >> 12 < new['palette_count'], (area, entry)
            for anim in new['animations']:
                assert anim['base'] + 3 < new['tile_count'] and anim['frames'] > 1 and anim['speed'] > 0
            if area != 'cream' or variant == 0:
                for field in ('tiles', 'map', 'palettes'):
                    self.equal(label, 'retained_' + area, field, old[field], new[field])
                self.check(label, 'retained_' + area, 'complete animation payload/timing', old['animations'] == new['animations'])
            else:
                # Cream also carries the unchanged handoff kit. Resolve it,
                # since tile deduplication/palette-bank order can relocate it.
                names = [n for n in before.tile_ids if not n.startswith('CREAM_')]
                def retained(name):
                    a, b = decode_metatile(before, old, name), decode_metatile(rom, new, name)
                    return a['frames'] == b['frames'] and a['speed'] == b['speed']
                unchanged = all(retained(n) for n in names)
                self.check(label, 'retained_cream_residents', 'all non-Cream native paintings and animations', unchanged, len(names))
        for name in before.sheet_ids:
            old, old_pixels = before.sheet(name)
            new, new_pixels = rom.sheet(name)
            self.check(label, 'sprite_contracts', name + ' exact descriptor', old == new)
            self.check(label, 'native_limits', name + ' legal OBJ canvas and 4bpp stride', (new['width'], new['height']) in SHAPES and new['frame_tiles']*64 == new['width']*new['height'] and new['tile_count'] % new['frame_tiles'] == 0)
            if variant and name == 'creamdoors' and self.args.allow_cream_return:
                stride = old['frame_tiles']*32
                return_frame = before.defs['F_CREAMDOORS_RETURN']
                for frame in range(old['tile_count']//old['frame_tiles']):
                    if frame != return_frame:
                        self.equal(label, 'retained_sprites', name + ' frame ' + str(frame), old_pixels[frame*stride:(frame+1)*stride], new_pixels[frame*stride:(frame+1)*stride])
                decoded = decode_sprite(new_pixels[return_frame*stride:(return_frame+1)*stride], new['width'], new['height'])
                self.check(label, 'cream_return', 'return frame retains16 transparent padding rows', not any(decoded[:new['width']*16]))
            else:
                self.equal(label, 'retained_sprites', name, old_pixels, new_pixels)
        # Pointer-bearing tables are resolved separately. All other linked
        # generated arrays include fonts, HUD, title, palette banks, timing,
        # room terrain and the physical/glitter metadata above.
        excluded = {'tilesets', 'sheets', 'room_defs'}
        prefixes = ('sheet_', 'tileset_', 'metatile_map_', 'tile_anim_', 'tile_anims_')
        protected = [name for name in before.sections if name not in excluded and not name.startswith(prefixes)]
        for name in protected:
            self.check(label, 'retained_assets', name + ' exists', name in rom.sections)
            if name in rom.sections: self.equal(label, 'retained_assets', name, before.array(name), rom.array(name))
        for index in range(before.defs['ROOM_COUNT']):
            a = before.unpack('<BB2xIIIB3x', before.symbols['room_defs'] + index*20)
            b = rom.unpack('<BB2xIIIB3x', rom.symbols['room_defs'] + index*20)
            self.check(label, 'retained_rooms', 'room descriptor ' + str(index), a[:2] + a[-1:] == b[:2] + b[-1:] and tuple(bool(v) for v in a[2:5]) == tuple(bool(v) for v in b[2:5]))
        self.equal(label, 'retained_music', 'entire original PCM section including loop continuations', rodata(before, 'original_music_pcm'), rodata(rom, 'original_music_pcm'))
        self.check(label, 'retained_music', 'resolved song descriptors and titles', songs(before) == songs(rom))
        return len(protected)

    def source(self, label, rom, variant, options):
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--export-source', str(variant), '--source-options', json.dumps(options)], env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), capture_output=True, text=True, check=True)
        source = json.loads(result.stdout)
        (self.out.parent / ('source-' + label + '.json')).write_text(json.dumps(source, indent=2) + '\n')
        ts = rom.tileset('cream')
        names = {name for name in rom.tile_ids if name.startswith('CREAM_')}
        self.check(label, 'source', 'all Cream source IDs cover native contract', names == set(source['tiles']), len(names))
        records = {}
        total_frames = 0
        for name, spec in source['tiles'].items():
            actual = decode_metatile(rom, ts, name)
            self.check(label, 'source', name + ' frame count/timing', len(actual['frames']) == len(spec['frames']) and actual['speed'] == spec['speed'])
            records[name] = actual['frames']
            for frame, (indices, colors) in enumerate(actual['frames']):
                expected = bytes.fromhex(spec['frames'][frame])
                self.equal(label, 'source_native_pixels', name + ' frame ' + str(frame), expected, indices)
                expected_colors = struct.pack('<256H', *[source['palettes'][spec['palettes'][(y//8)*2+x//8]][expected[y*16+x]] if expected[y*16+x] else 0x8000 for y in range(16) for x in range(16)])
                self.equal(label, 'source_native_colors', name + ' frame ' + str(frame), expected_colors, colors)
                total_frames += 1
        self.records[label] = records
        if self.args.allow_cream_return:
            meta, pixels = rom.sheet('creamdoors')
            frame = rom.defs['F_CREAMDOORS_RETURN']
            stride = meta['frame_tiles']*32
            decoded = decode_sprite(pixels[frame*stride:(frame+1)*stride], meta['width'], meta['height'])
            self.equal(label, 'source_native_sprites', 'Cream return doorway exact indexed pixels', bytes.fromhex(source['cream_return']), decoded)
        self.atlas(label, records)
        return total_frames

    def atlas(self, label, records):
        from PIL import Image
        ordered = sorted(records, key=lambda name: (family(name), name))
        canvas = Image.new('RGB', (16*16, ((len(ordered)+15)//16)*16), (24, 24, 32))
        manifest = []
        for i, name in enumerate(ordered):
            _, colors = records[name][0]
            pixels = []
            for value in struct.unpack('<256H', colors):
                pixels.append((24, 24, 32) if value == 0x8000 else tuple(((value >> (j*5)) & 31)*8 for j in range(3)))
            image = Image.new('RGB', (16, 16)); image.putdata(pixels)
            x, y = (i % 16)*16, (i // 16)*16
            canvas.paste(image, (x, y))
            manifest.append({'name': name, 'family': family(name), 'x': x, 'y': y, 'frame': 0})
        canvas.save(self.out.parent / ('native-atlas-' + label + '.png'))
        canvas.resize((canvas.width*4, canvas.height*4), Image.Resampling.NEAREST).save(self.out.parent / ('native-atlas-' + label + '-4x.png'))
        (self.out.parent / ('native-atlas-' + label + '.json')).write_text(json.dumps({'kind': 'ROM-decoded source assembly; not an emulator capture', 'tiles': manifest}, indent=2) + '\n')

    def comparisons(self):
        comparisons = []
        for left, right in itertools.combinations(self.records, 2):
            rows = defaultdict(lambda: {'metatiles': 0, 'changed_indexed': 0, 'changed_rgb555': 0, 'changed_canonical_geometry': 0, 'changed_internal_boundaries': 0, 'changed_transparent_footprint': 0})
            for name in self.records[left]:
                a, b = self.records[left][name], self.records[right][name]
                row = rows[family(name)]; row['metatiles'] += 1
                for field, fn in (
                    ('changed_indexed', lambda f: f[0]), ('changed_rgb555', lambda f: f[1]),
                    ('changed_canonical_geometry', lambda f: canonical(f[0])),
                    ('changed_internal_boundaries', lambda f: edges(f[0])),
                    ('changed_transparent_footprint', lambda f: bytes(int(p != 0) for p in f[0])),
                ):
                    row[field] += int([fn(f) for f in a] != [fn(f) for f in b])
            for group, row in rows.items():
                self.check(left + ':' + right, 'family_geometry', group + ' has structural changes after ink renumbering', row['changed_canonical_geometry'] > 0, row)
            comparisons.append({'left': left, 'right': right, 'families': dict(rows)})
        return comparisons

    def run(self):
        source_paths = [ROOT/'art'/name for name in ('cream_terrain.py', 'cream_actors.py', 'tiles.py', 'palettes.py')]
        if (ROOT/'art/cream_studies.py').exists(): source_paths.append(ROOT/'art/cream_studies.py')
        source_paths += sorted((ROOT/'art').glob('cream_style_*.py'))
        source_snapshot = {str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in source_paths}
        self.check('baseline', 'provenance', 'exact preserved production ROM', sha(self.base.rom) == BASELINE_SHA, sha(self.base.rom))
        pins = dict(value.split('=', 1) for value in self.args.pin)
        for item in self.args.bundle:
            label, path = item.split('=', 1) if '=' in item else (Path(item).name, item)
            assert re.fullmatch(r'[A-Za-z0-9_-]+', label) and label not in self.records, label
            rom = NativeRom(path)
            options_path = Path(path) / 'build-options.json'
            options = json.loads(options_path.read_text()) if options_path.exists() else {}
            if 'options' in options: options = options['options']
            variant = rom.defs.get('BART_CREAM_VARIANT', rom.defs.get('BART_CREAM_STUDY', 0))
            if 'BART_CREAM' in options:
                self.check(label, 'provenance', 'header agrees with frozen build option', variant == int(options['BART_CREAM']), variant)
            self.check(label, 'provenance', 'known optional Cream direction', variant in STYLES, variant)
            digest = sha(rom.rom)
            if 'rom_sha256' in options:
                self.check(label, 'provenance', 'ROM matches completed build-options SHA256 pin', digest == options['rom_sha256'], digest)
            if label in pins: self.check(label, 'provenance', 'ROM matches supplied exact SHA256 pin', digest == pins[label], digest)
            freeze = Path(path) / 'freeze.json'
            if freeze.exists():
                metadata = json.loads(freeze.read_text())
                if 'rom_sha256' in metadata: self.check(label, 'provenance', 'ROM matches freeze manifest', digest == metadata['rom_sha256'], digest)
            protected = self.scope(label, rom, variant)
            commit_path = Path(path)/'source-commit.txt'
            if commit_path.exists():
                commit = commit_path.read_text().strip()
                prefix = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', '--show-prefix'], text=True).strip()
                mismatches = []
                for source_path in source_paths:
                    relative = str(source_path.relative_to(ROOT))
                    result = subprocess.run(['git', '-C', str(ROOT), 'show', commit + ':' + prefix + relative], capture_output=True)
                    if result.returncode or sha(result.stdout) != source_snapshot[relative]: mismatches.append(relative)
                self.check(label, 'provenance', 'audited painters exactly match pinned source commit', not mismatches, mismatches or commit)
            frames = self.source(label, rom, variant, options) if not self.args.skip_source else 0
            self.check(label, 'provenance', 'frozen ROM unchanged throughout audit', sha((Path(path)/'bartgame.gba').read_bytes()) == digest)
            self.results.append({'label': label, 'path': str(Path(path).resolve()), 'variant': variant, 'style': STYLES.get(variant), 'rom_sha256': digest,
                                 'source_commit': (Path(path)/'source-commit.txt').read_text().strip() if (Path(path)/'source-commit.txt').exists() else None,
                                 'audited_bundle_file_sha256': {f: sha((Path(path)/f).read_bytes()) for f in ('bartgame.gba', 'bartgame.map', 'assets.h')},
                                 'budgets': {area: {k: rom.tileset(area)[k] for k in ('tile_count', 'palette_count')} for area in ('forest', 'sewer', 'myst', 'cream')},
                                 'source_native_frames': frames, 'protected_scalar_arrays': protected})
            print('BUNDLE', label, digest, flush=True)
        comparisons = self.comparisons()
        self.check('source', 'provenance', 'audited painter files unchanged throughout audit', source_snapshot == {str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in source_paths})
        self.check('baseline', 'provenance', 'baseline unchanged throughout audit', sha((Path(self.args.baseline)/'bartgame.gba').read_bytes()) == BASELINE_SHA)
        report = {'method': __doc__.strip(), 'baseline_rom_sha256': sha(self.base.rom), 'cream_return_frame_exception': self.args.allow_cream_return,
                  'bundles': self.results, 'source_file_sha256': source_snapshot, 'comparisons': comparisons, 'checks': self.checks,
                  'passed': sum(c['passed'] for c in self.checks), 'total': len(self.checks), 'failures': [c for c in self.checks if not c['passed']],
                  'limits': 'No alpha channel exists in GBA4bpp: index0 is binary transparency. Palette words areRGB555; source hex rows must be16x16 indexed data. Geometry comparisons remove ink numbering and report internal boundaries/footprints per whole family; no pixel-difference quota proves quality. Shared canvas/physical metadata are exact, so these studies add drawn depth rather than new elevation or collision. Real-room visibility, readability, motion, interaction approach and timing require the separate native mGBA review. Unlinked source arrays have no ROM payload to compare.'}
        self.out.write_text(json.dumps(report, indent=2) + '\n')
        print('RESULT', 'FAIL' if report['failures'] else 'PASS', str(report['passed']) + '/' + str(report['total']))
        return bool(report['failures'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', default='/workspace/setup/regional-integration/candidate4')
    parser.add_argument('--bundle', action='append', default=[], help='repeat PATH or LABEL=PATH')
    parser.add_argument('--out', default='/workspace/setup/cream-studies/audit/native-audit.json')
    parser.add_argument('--pin', action='append', default=[], help='optional repeat LABEL=exact-ROM-SHA256')
    parser.add_argument('--allow-cream-return', action='store_true', help='permit only Creamdoors return frame2; all other OBJ frames/banks exact')
    parser.add_argument('--skip-source', action='store_true', help='scope-only audit; no source fidelity or family comparisons')
    parser.add_argument('--export-source', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--source-options', default='{}', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.export_source is not None:
        source_export(args.export_source, json.loads(args.source_options)); return 0
    return Audit(args).run()


if __name__ == '__main__':
    raise SystemExit(main())
