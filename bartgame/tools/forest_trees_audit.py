#!/usr/bin/env python3
"""Independent fidelity, room-geometry and capture audit of adopted trees.

The host corpus executes the actual room/forest-tree C code and native ROM
metadata. It is a logic test, not an emulator render. Raw mGBA evidence is
audited separately; passing numerical checks does not establish art quality.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

from sewer_concept_audit import NativeRom, decode_sprite
from forest_tree_study_audit import decode_map, rgb555

GAME = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
APPROVED_PAINTER = 'a8750327e4d015a31656ede2adbc21be6e8512eadca09c5aa8636c1599b3b54f'
TIMING_BASELINE_SHA = '1ef84e4fc5df0cc32c74ce7e46852bc88818a6122006a7410432b64600405ce3'


class Audit:
    def __init__(self, args):
        self.args = args
        self.out = Path(args.out)
        self.out.mkdir(parents=True, exist_ok=True)
        self.rom = NativeRom(args.bundle)
        self.base = NativeRom(args.base)
        self.rows = []
        self.tool_sha256 = SHA(Path(__file__).read_bytes())
        self.bundle_hashes = {name: SHA((self.rom.directory/name).read_bytes()) for name in ('bartgame.gba', 'bartgame.map', 'assets.h')}

    def check(self, group, name, passed, detail=None):
        row = dict(group=group, name=name, passed=bool(passed))
        if detail is not None:
            row['detail'] = detail
        self.rows.append(row)
        if not passed:
            print('FAIL', group, name, detail, flush=True)

    def provenance(self):
        path = self.rom.directory/'freeze.json'
        if not path.exists():
            self.check('provenance', 'frozen build metadata exists', self.args.allow_pilot,
                       'Explicit unfrozen pilot; not release evidence.' if self.args.allow_pilot else str(path))
            return {'unfrozen_pilot': True}
        freeze = json.loads(path.read_text())
        self.check('provenance', 'frozen ROM hash and profile match the loaded bytes',
                   freeze['rom_sha256'] == SHA(self.rom.rom) and freeze.get('variant', freeze.get('forest_variant')) == 31)
        for field in ('source_file_sha256', 'code_file_sha256'):
            for relative, expected in freeze[field].items():
                self.check('provenance', relative+' matches frozen input bytes', SHA((GAME/relative).read_bytes()) == expected)
        baseline = json.loads((self.base.directory/'freeze.json').read_text())
        for relative in ('src/world.c', 'src/world.h', 'src/roomgen.c', 'src/roomgen.h'):
            expected = baseline['code_file_sha256'][relative]
            self.check('scope', relative+' world/progression generation is unchanged from profile30',
                       freeze['code_file_sha256'][relative] == expected)
        return {'source_commit': freeze['source_commit'], 'unfrozen_pilot': False}

    def scope(self):
        """Compare resolved art bytes, never relocated pointer values."""
        for name in ('sewer', 'myst'):
            self.check('scope', name+' tiles/palettes/maps/animations stay exact',
                       self.rom.tileset(name) == self.base.tileset(name))
        for name in ('metatile_type', 'metatile_coll', 'metatile_prop'):
            self.check('scope', name+' semantic contracts stay exact', self.rom.array(name) == self.base.array(name))
        self.check('scope', 'existing blight pulse RGB555 colors stay exact',
                   self.rom.array('forest_v2_pulse_colors') == self.base.array('forest_v2_pulse_colors'))
        for name in sorted(self.base.sheet_ids):
            self.check('scope', name+' object sheet stays exact',
                       self.rom.sheet(name) == self.base.sheet(name))
        # Include all non-world character/UI/palette scalar arrays present in
        # both builds; the full forest atlas legitimately gets repacked.
        names = sorted(n for n in self.base.sections if n in self.rom.sections and
                       not n.startswith(('forest_', 'tree_study_', 'tileset_', 'ts_')) and
                       any(k in n for k in ('palette', 'title', 'font', 'hud', 'menu', 'dialogue')))
        for name in names:
            self.check('scope', name+' unchanged payload', self.rom.array(name) == self.base.array(name))
        forest_scope = self.forest_scope()
        return {'object_sheets': len(self.base.sheet_ids), 'extra_payloads': names, 'forest': forest_scope}

    def forest_scope(self):
        """Compare non-tree native pixels despite atlas/palette-bank relocation."""
        sys.path.insert(0, str(GAME/'art'))
        from forest_canopy_adaptive_terrain import owns
        path = self.rom.directory/'art-reboot-coverage.json'
        if not path.exists():
            path = self.rom.directory/'coverage.json'
        coverage = json.loads(path.read_text())
        descriptors = {row['name'].upper(): row for row in coverage['tiles']}
        retired, protected = [], []
        before, after = self.base.tileset('forest'), self.rom.tileset('forest')
        phases = max([a['frames'] for t in (before, after) for a in t['animations']]+[1])

        def phase_atlases(ts):
            result = []
            for phase in range(phases):
                pixels = bytearray(ts['tiles'])
                for anim in ts['animations']:
                    n = phase % anim['frames']
                    pixels[anim['base']*32:anim['base']*32+128] = anim['data'][n*128:(n+1)*128]
                result.append(pixels)
            return result

        atlases = (phase_atlases(before), phase_atlases(after))

        def resolved(ts, atlas, index):
            entries = struct.unpack_from('<4H', ts['map'], index*8)
            result = []
            for entry in entries:
                indices = decode_map(atlas, [entry], 8, 8)
                palette = struct.unpack_from('<16H', ts['palettes'], (entry >> 12)*32)
                result.extend(palette[p] if p else 0x8000 for p in indices)
            return struct.pack('<256H', *result)

        def animation_signature(ts, index):
            entries = struct.unpack_from('<4H', ts['map'], index*8)
            return tuple(next(((a['frames'], a['speed']) for a in ts['animations']
                               if a['base'] <= (entry & 1023) < a['base']+4), None) for entry in entries)

        for name, index in self.base.tile_ids.items():
            row = descriptors.get(name, {})
            is_tree = owns(name.lower()) or owns(row.get('parent', '').split('@')[0]) or row.get('family') == 'fringe'
            if is_tree:
                retired.append(name)
                continue
            new_index = self.rom.tile_ids[name]
            exact = all(resolved(before, atlases[0][phase], index) ==
                        resolved(after, atlases[1][phase], new_index) for phase in range(phases))
            exact = exact and animation_signature(before, index) == animation_signature(after, new_index)
            self.check('scope', 'forest '+name+' non-tree RGB555/alpha/animation stays exact', exact)
            protected.append(name)
        self.check('scope', 'forest protection has nonvacuous floor and interaction coverage',
                   all(n in protected for n in ('MOSS0', 'PATH', 'CRACK', 'WEB', 'DOOR_LOCKED', 'PIT')) and len(retired) > 100,
                   {'protected': len(protected), 'retired_tree_pictures': len(retired)})
        return {'protected_count': len(protected), 'retired_tree_pictures': retired,
                'comparison': 'Every native RGB555/transparent pixel at every frame, plus frame count/speed, after palette/map/flip resolution.'}

    def native(self):
        sys.path.insert(0, str(GAME/'art'))
        import forest_tree_study as art
        source_path = GAME/'art/forest_tree_study.py'
        self.check('native', 'approved painter bytes remain exact', SHA(source_path.read_bytes()) == APPROVED_PAINTER)
        self.check('native', 'profile31 is the integrated tree profile', self.rom.defs['BART_FOREST_VARIANT'] == 31)
        specs = art.specs()
        ts = self.rom.tileset('forest')
        self.check('budget', 'forest BG leaves map memory for the third world layer', ts['tile_count'] <= 768,
                   {'used': ts['tile_count'], 'limit': 768})
        self.check('budget', 'forest palette use stays within twelve world banks', ts['palette_count'] <= 12,
                   {'used': ts['palette_count'], 'limit': 12})
        records = []
        # Runtime map names are deliberately explicit, so a renamed ABI fails
        # loudly instead of silently auditing an unused diagnostic atlas.
        atlas_name = self.args.tree_tiles
        atlas = self.rom.array(atlas_name) if atlas_name else ts['tiles']
        slot = self.rom.defs[self.args.tree_slot]
        packed_palette = ts['palettes'][slot*32:(slot+1)*32]
        self.check('native', 'approved shared RGB555 bank survives packing',
                   packed_palette == struct.pack('<16H', *rgb555(art.palette())))
        pulse_count = self.rom.defs.get('FOREST_V2_PULSE_COUNT', 0)
        pulses = self.rom.array('forest_v2_pulse_slots')
        start = self.rom.defs['TS_FOREST']*pulse_count
        self.check('native', 'tree bank is not recolored by another material pulse', slot not in pulses[start:start+pulse_count])
        entry_blob = self.rom.array('forest_tree_entries')
        widths = self.rom.array('forest_tree_width')
        self.check('native', 'all twelve native widths survive descriptor packing',
                   widths == bytes(s['size_pixels'][0] for s in specs))
        for name, expected in (
                ('anchor_x', bytes(s['anchor'][0] for s in specs)),
                ('anchor_y', bytes(s['anchor'][1] for s in specs)),
                ('state', bytes(('healthy', 'sick', 'dead').index(s['state']) for s in specs)),
                ('variety', bytes(s['variety'] for s in specs))):
            self.check('native', 'native '+name+' descriptor is exact',
                       self.rom.array('forest_tree_'+name) == expected)
        for n, spec in enumerate(specs):
            image = art.tree(spec['size'], spec['variety'], spec['state'])
            count = image.width*image.height//64
            packed_entries = entry_blob[n*32:n*32+count*2]
            entries = struct.unpack('<%dH' % count, packed_entries)
            actual = decode_map(atlas, entries, image.width, image.height)
            self.check('native', spec['name']+' preserves every native pixel and hardware flip', actual == image.tobytes())
            self.check('native', spec['name']+' has exact canvas, ground anchor and bank',
                       image.size == tuple(spec['size_pixels']) and spec['anchor'] == [image.width//2, 30] and
                       all(e >> 12 == slot for e in entries))
            alpha_rows = [sum(1 << x for x in range(image.width) if image.getpixel((x, y))) for y in range(32)]
            opaque = self.rom.array('forest_tree_opaque_rows')[n*128:(n+1)*128]
            self.check('native', spec['name']+' fast depth-sorting row masks equal every source alpha bit',
                       opaque == struct.pack('<32I', *alpha_rows))
            records.append(dict(name=spec['name'], size=list(image.size), anchor=spec['anchor'],
                                index_sha256=SHA(actual), map_sha256=SHA(packed_entries)))
        return records

    def host(self):
        directory = self.out/'host'
        directory.mkdir(exist_ok=True)
        main = directory/'generator-check.c'
        main.write_text(HOST.replace('ROOMGEN_SOURCE', str(GAME/'src/roomgen.c')))
        wrapper = directory/'room-logic.c'
        wrapper.write_text('#define room_render qa_unused_hardware_room_render\n#include "'+str(GAME/'src/room.c')+'"\n#undef room_render\nvoid room_render(void) {}\n')
        arrays = ['#include "assets.h"']
        for kind, name, dims in re.findall(r'extern\s+const\s+(u8|u16|u32)\s+(\w+)\s*((?:\[[^\]]*\])+)[ \t]*;', self.rom.header):
            if name not in self.rom.sections or not name.startswith(('metatile_', 'forest_')):
                continue
            data = self.rom.array(name)
            values = (data if kind == 'u8' else struct.unpack('<%d%s' % (len(data)//(2 if kind == 'u16' else 4),
                                                                       'H' if kind == 'u16' else 'I'), data))
            arrays.append('const %s %s%s = {%s};' % (kind, name, dims, ','.join(map(str, values))))
        metadata = directory/'native-metadata.c'
        metadata.write_text('\n'.join(arrays)+'\n')
        binary = directory/'generator-check'
        command = ['gcc', '-O2', '-fno-builtin', '-w', '-ffunction-sections', '-fdata-sections',
                   '-I', str(GAME/'src'), '-I', str(self.rom.directory), str(main), str(wrapper),
                   *([str(GAME/'src/forest_trees.c')] if self.rom.defs['BART_FOREST_VARIANT'] >= 31 else []),
                   str(GAME/'src/world.c'), str(GAME/'src/util.c'), str(metadata),
                   '-Wl,--gc-sections', '-o', str(binary)]
        build = subprocess.run(command, text=True, capture_output=True, cwd=GAME)
        (directory/'compile.log').write_text(build.stdout+build.stderr)
        self.check('geometry', 'actual C room/tree host harness compiles', build.returncode == 0,
                   build.stderr[-4000:] if build.returncode else None)
        if build.returncode:
            return {'compile_failed': True}
        with (directory/'run.log').open('w') as stream:
            result = subprocess.run([str(binary), str(self.args.host_seeds)], stdout=stream, stderr=subprocess.STDOUT, cwd=GAME)
        output = (directory/'run.log').read_text()
        final = re.findall(r'^RESULT (\{[^\n]+\})$', output, re.M)
        stats = json.loads(final[-1]) if final else {}
        self.check('geometry', 'full requested seed ×25-room corpus completed',
                   stats.get('rooms') == self.args.host_seeds*25, stats)
        self.check('geometry', 'actual roots preserve approaches, gate cutsets and item pockets',
                   result.returncode == 0 and stats.get('failures') == 0, stats)
        if self.rom.defs['BART_FOREST_VARIANT'] >= 31:
            states = stats.get('stage_state_counts', [])
            green = [row[0]/sum(row) for row in states] if len(states) == 4 and all(sum(row) for row in states) else []
            self.check('geometry', 'all twelve native tree forms occur in ordinary generated rooms',
                       len(stats.get('frame_counts', [])) == 12 and all(stats['frame_counts']), stats.get('frame_counts'))
            self.check('geometry', 'depth retains living trees while structural sickness increases',
                       len(green) == 4 and green[0] > green[1] > max(green[2:]) > 0 and
                       states[0][2] == 0 and all(states[d][2] > 0 for d in (1, 2, 3)),
                       {'healthy_tree_proportions_by_stage': green, 'state_counts': states})
        record = dict(method='Actual C generation plus native ROM metadata; independent flood-fill and resulting-root checks. Hardware submission suppressed; no render claim.',
                      rom_sha256=SHA(self.rom.rom), statistics=stats, exit_code=result.returncode,
                      compiler=subprocess.check_output(['gcc', '--version'], text=True).splitlines()[0], command=command,
                      harness_sha256=SHA(main.read_bytes()), wrapper_sha256=SHA(wrapper.read_bytes()),
                      metadata_sha256=SHA(metadata.read_bytes()), binary_sha256=SHA(binary.read_bytes()),
                      source_sha256={str(p.relative_to(GAME)): SHA(p.read_bytes()) for p in
                                     (GAME/'src/roomgen.c', GAME/'src/room.c', GAME/'src/forest_trees.c', GAME/'src/world.c', GAME/'src/util.c') if p.exists()})
        (directory/'report.json').write_text(json.dumps(record, indent=2)+'\n')
        return record

    def captures(self):
        from PIL import Image
        path = Path(self.args.capture)
        manifest = json.loads(path.read_text())
        root = path.parent
        self.timing_baseline = None
        if manifest.get('timing_baseline'):
            timing_file = root/manifest['timing_baseline']['file']
            self.check('timing', 'historical control bytes match the pinned read-only comparison',
                       SHA(timing_file.read_bytes()) == manifest['timing_baseline']['sha256'] == TIMING_BASELINE_SHA)
            self.timing_baseline = json.loads(timing_file.read_text())
        self.check('capture', 'real mGBA capture binds the same frozen ROM',
                   manifest['source_freeze'].get('rom_sha256', manifest['bundle_sha256']['bartgame.gba']) == SHA(self.rom.rom))
        records = []
        for room in manifest['captures']:
            name = room['name']
            p = room['panorama']
            file = root/p['file']
            mosaic = Image.open(file).convert('RGB')
            self.check('capture', name+' full-room PNG has declared native dimensions/hash',
                       mosaic.size == (512, 384) and SHA(file.read_bytes()) == p['png_sha256'] and
                       SHA(mosaic.tobytes()) == p['RGB_sha256'])
            coverage = bytearray(512*384)
            views = p['views']
            for v in views:
                source_file = root/v['file']
                source = Image.open(source_file).convert('RGB')
                wc, sc, camera = v['world_crop'], v['source_crop'], v['camera']
                valid = (source.size == (240, 160) and 0 <= sc[0] < sc[2] <= 240 and
                         0 <= sc[1] < sc[3] <= 160 and 0 <= wc[0] < wc[2] <= 512 and
                         0 <= wc[1] < wc[3] <= 384 and
                         [sc[i]+camera[i%2] for i in range(4)] == wc)
                self.check('capture', name+' '+source_file.name+' is an untouched native camera PNG',
                           valid and SHA(source_file.read_bytes()) == v['png_sha256'] and
                           SHA(source.tobytes()) == v['RGB_sha256'])
                if not valid:
                    continue
                crop = source.crop(sc)
                self.check('capture', name+' '+source_file.name+' pixels copied literally into mosaic',
                           crop.tobytes() == mosaic.crop(wc).tobytes() and SHA(crop.tobytes()) == v['crop_RGB_sha256'])
                hw = v['hardware']
                self.check('capture', name+' '+source_file.name+' actual world planes share camera',
                           all(hw[k] == camera for k in ('camera', 'BG1_scroll', 'BG2_scroll', 'BG3_scroll')) and
                           not (hw['DISPCNT'] & 0x100))
                for y in range(wc[1], wc[3]):
                    for x in range(wc[0], wc[2]):
                        coverage[y*512+x] += 1
            self.check('capture', name+' full room uses exactly nine views and one source per pixel',
                       len(views) == 9 and set(coverage) == {1})
            self.check('capture', name+' actor coordinates/RNG are held through the camera fixture',
                       len({json.dumps(v['hardware']['world_actors'], sort_keys=True) for v in views}) == 1 and
                       len({v['hardware']['rng'] for v in views}) == 1)
            native_views = [room['native_arrival'], room['native_HUD'], *room['normal_facing_views']]
            for v in native_views:
                im = Image.open(root/v['file']).convert('RGB')
                self.check('capture', name+' '+Path(v['file']).name+' normal HUD evidence stays native',
                           im.size == (240, 160) and SHA(im.tobytes()) == v['RGB_sha256'] and
                           SHA((root/v['file']).read_bytes()) == v['png_sha256'] and bool(v['hardware']['DISPCNT'] & 0x100))
            walk = self.walk(root, room) if room.get('walk') else None
            records.append({'name': name, 'stage': room['stage'], 'views': len(views),
                            'different_overlap_pixels': sum(v['different_pixels'] for v in p['overlap_comparisons']),
                            'overlap_note': p['overlap_note'], 'walk': walk})
        self.check('capture', 'healthy, mixed and deep ordinary rooms all have native evidence',
                   {r['name'] for r in records} >= {'healthy', 'mixed', 'deep'})
        return {'manifest_sha256': SHA(path.read_bytes()), 'rooms': records,
                'provenance': 'Independent exact native PNG/crop/camera/hash verification; no source re-render or image repair.'}

    def walk(self, root, room):
        """Independently compare real walk PNGs with current native Bloom inks.

        The capture helper separately models BG1/BG3 occlusion. This check
        verifies its visible-pixel counts cannot exceed literal frame matches,
        all body/guard pixels come from ROM poses, and scanout is paired.
        It does not infer covered pixels from a source-room reconstruction.
        """
        from PIL import Image
        walk, name = room['walk'], room['name']
        observations = json.loads((root/walk['observations']).read_text())
        meta, hero = self.rom.sheet('hero')
        stride = meta['frame_tiles']*32
        poses = {SHA(hero[i:i+stride]) for i in range(0, len(hero), stride)}
        palette = self.rom.array('pal_obj')
        errors, minimum, guarded, behind = [], 999999, 0, 0
        for observation in observations:
            tick, model = observation['tick'], observation['body']
            if not model or not model.get('body_found'):
                errors.append([tick, 'no current native Bloom body'])
                continue
            raw = bytes.fromhex(model['body_vram_hex'])
            w, h = model['body_canvas']
            actor, colors = model['hero_OAM'], model['body_palette']
            good = SHA(raw) in poses and SHA(raw) == model['body_vram_sha256']
            good &= (w, h) == (meta['width'], meta['height'])
            good &= struct.pack('<16H', *colors) == palette[actor['pal']*32:(actor['pal']+1)*32]
            good &= model['scanline0'] == 0 and model['scanline160'] == 160 and model['video_frame'] == model['end_video_frame']
            body = decode_sprite(raw, w, h)
            guard = model.get('guard_OAM')
            if guard:
                guarded += 1
                mask = decode_sprite(bytes.fromhex(model['guard_vram_hex']), w, h)
                good &= all(guard[k] == actor[k] for k in ('x', 'y', 'pal', 'shape', 'size', 'flip')) and guard['priority'] == 1
                good &= all(not ink or ink == body[i] for i, ink in enumerate(mask))
            behind += bool(model.get('body_pixels_behind_BG1') or model.get('body_pixels_behind_BG3'))
            file = root/name/'walk'/f'{tick:04d}.png'
            image = Image.open(file).convert('RGB')
            hits = 0
            for y in range(h):
                for x in range(w):
                    i = body[y*w+(w-1-x if actor['flip'] else x)]
                    px, py = actor['x']+x, actor['y']+y
                    if not i or not (0 <= px < 240 and 12 <= py < 160):
                        continue
                    value = colors[i]
                    parts = (value & 31, (value >> 5) & 31, (value >> 10) & 31)
                    if max(parts) < 5 or sum(parts) < 10:
                        continue
                    rgb = tuple((v << 3) | (v >> 2) for v in parts)
                    hits += image.getpixel((px, py)) == rgb
            visible = model['exact_visible_pixels']
            good &= image.size == (240, 160) and 0 < visible <= hits and model['largest_visible_component'] >= 4
            if not good:
                errors.append([tick, 'native pose/guard/palette/scanout/actual pixel mismatch'])
            minimum = min(minimum, visible)
        self.check('walk', name+' real walk source/guard/palette/scanout and native PNG pixel proof', not errors, errors)
        self.check('walk', name+' visible body count agrees with complete captured sequence',
                   len(observations) == walk['frames'] and minimum == walk['minimum_visible_Bloom_pixels'] and minimum > 0,
                   {'minimum': minimum, 'frames': len(observations), 'guarded_frames': guarded, 'occluded_frames': behind})
        missed = sum(o['logic_updates'] == 0 for o in observations)
        baseline = next((r for r in (self.timing_baseline or {}).get('captures', [])
                         if r['build'] == 'base29' and r['room'] == name), None)
        qualified = baseline is not None and baseline['initial_position'] == room['initial_position'] and len(baseline['frames']) == len(observations) == 168
        self.check('timing', name+' literal missed native updates stay within the matched historical control',
                   qualified and missed == walk['missed_updates'] and missed <= baseline['missed_updates'] and
                   walk['historical_missed_update_limit'] == baseline['missed_updates'] and
                   walk['timing_comparison_sha256'] == TIMING_BASELINE_SHA,
                   {'actual_missed_updates': missed, 'historical_missed_updates': baseline['missed_updates'] if baseline else None,
                    'frame_perfect_claim': False})
        return {'frames': len(observations), 'minimum_visible_current_native_Bloom_pixels': minimum,
                'guarded_frames': guarded, 'occluded_frames': behind, 'missed_logic_updates': missed,
                'timing': 'Qualified only against the pinned matched historical control; not a frame-perfect claim.'}

    def run(self):
        report = dict(rom_sha256=SHA(self.rom.rom), base_rom_sha256=SHA(self.base.rom),
                      audit_tool_sha256=self.tool_sha256, command=sys.argv,
                      provenance=self.provenance(), approved_native_art=self.native(), protected_art=self.scope())
        if self.args.host_seeds:
            report['host'] = self.host()
        if self.args.capture:
            report['captures'] = self.captures()
        self.check('provenance', 'audit helper bytes were held through execution', SHA(Path(__file__).read_bytes()) == self.tool_sha256)
        self.check('provenance', 'frozen ROM/header/map bytes were held through execution',
                   all(SHA((self.rom.directory/name).read_bytes()) == expected for name, expected in self.bundle_hashes.items()))
        report.update(checks=self.rows, passed=sum(r['passed'] for r in self.rows), total=len(self.rows),
                      failures=[r for r in self.rows if not r['passed']])
        (self.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        print('RESULT', report['passed'], '/', report['total'], flush=True)
        return bool(report['failures'])


HOST = r'''
#include <stdio.h>
#include <stdlib.h>
#include "game.h"
#include "world.h"
#include "room.h"
#include "roomgen.h"
#if BART_FOREST_VARIANT >= 31
#include "forest_trees.h"
#endif
GameState gGame;
u32 gFrame;
#include "ROOMGEN_SOURCE"
/* Independent traversal reads the completed native collision grid, not a
   reconstruction of the generator's candidate/placement predicates. */
static unsigned char seen[4096];
static int queue[4096],failures,printed;
static unsigned long rooms,approaches,pockets,determinism,boundaries,feet_rooms;
static unsigned long trees,wood_cells,authored_cells,preview_checks,root_checks,opened_state_rooms,cache_checks,frame_seen[12],stage_state[4][3];
static const int land[4][2]={{15,2},{30,11},{15,22},{1,11}};
static void fail(unsigned seed,int cell,const char* why,int x,int y) {
    failures++;if(printed++<40)printf("FAIL seed=%u cell=%d %s (%d,%d)\n",seed,cell,why,x,y);
}
static int blocked(int qx,int qy,int items) {
    int x=qx/2,y=qy/2,t;
    if(qx<0||qy<0||qx>=gRoom.w*2||qy>=gRoom.h*2)return 1;
    t=room_type(x,y);
    if(t==TT_THORN||t==TT_LIFT1)return 0;
    if((items&1)&&t==TT_CRACK)return 0;
    if((items&2)&&t==TT_WEB)return 0;
    if((items&4)&&t==TT_PIT)return 0;
    if(t==TT_PIT||t==TT_WATER||t==TT_MYST||t==TT_EXIT)return 1;
    return gRoom.solid[qy*64+qx]!=0;
}
static void flood(int x,int y,int items) {
    static const int dx[4]={0,1,0,-1},dy[4]={-1,0,1,0};
    int a,b,head=0,tail=0,i;memset(seen,0,sizeof(seen));
    for(b=0;b<2;b++)for(a=0;a<2;a++) {
        int qx=x*2+a,qy=y*2+b,p=qy*64+qx;
        if(!blocked(qx,qy,items)){seen[p]=1;queue[tail++]=p;}
    }
    while(head<tail) {
        int p=queue[head++],x=p%64,y=p/64;
        for(i=0;i<4;i++) {
            int nx=x+dx[i],ny=y+dy[i],n=ny*64+nx;
            if(!blocked(nx,ny,items)&&!seen[n]){seen[n]=1;queue[tail++]=n;}
        }
    }
}
static int reaches(int x,int y) {
    if(x<0||y<0||x>=gRoom.w||y>=gRoom.h)return 0;
    return seen[y*128+x*2]||seen[y*128+x*2+1]||seen[(y*2+1)*64+x*2]||seen[(y*2+1)*64+x*2+1];
}
static void target(unsigned seed,int cell,const char* label,Spot p,int offset) {
    approaches++;if(!reaches(p.x,p.y+offset))fail(seed,cell,label,p.x,p.y+offset);
}
/* Bloom's implemented feet box is10×8, offset(0,-4), not a point on an
   8px collision quarter. A separate2px position lattice catches clear-looking
   8px slits that the earlier quarter flood can falsely call traversable.
   Every8px blocker remains wider than a lattice step. */
static unsigned char feet_seen[256*192];
static int feet_queue[256*192];
static int feet_free(int x,int y,int items) {
    int px=x*2,py=y*2,qx,qy;
    if(px<5||py<8||px+4>=gRoom.w*16||py>gRoom.h*16)return 0;
    for(qy=(py-8)/8;qy<=(py-1)/8;qy++)
        for(qx=(px-5)/8;qx<=(px+4)/8;qx++)if(blocked(qx,qy,items))return 0;
    return 1;
}
static void feet_flood(int sx,int sy,int items) {
    static const int dx[4]={0,1,0,-1},dy[4]={-1,0,1,0};
    int x,y,head=0,tail=0,i;memset(feet_seen,0,sizeof(feet_seen));
    for(y=sy*8;y<(sy+1)*8;y++)for(x=sx*8;x<(sx+1)*8;x++) {
        int p=y*256+x;
        if(feet_free(x,y,items)){feet_seen[p]=1;feet_queue[tail++]=p;}
    }
    while(head<tail) {
        int p=feet_queue[head++],x=p%256,y=p/256;
        for(i=0;i<4;i++) {
            int nx=x+dx[i],ny=y+dy[i],n=ny*256+nx;
            if(nx<0||ny<0||nx>=256||ny>=192||feet_seen[n]||!feet_free(nx,ny,items))continue;
            feet_seen[n]=1;feet_queue[tail++]=n;
        }
    }
}
static int feet_reaches(int x,int y) {
    int a,b;
    if(x<0||y<0||x>=gRoom.w||y>=gRoom.h)return 0;
    for(b=y*8;b<(y+1)*8;b++)for(a=x*8;a<(x+1)*8;a++)if(feet_seen[b*256+a])return 1;
    return 0;
}
static void feet_target(unsigned seed,int cell,const char* label,Spot p,int off) {
    if(!feet_reaches(p.x,p.y+off))fail(seed,cell,label,p.x,p.y+off);
}
static void feet_inspect(unsigned seed,int cell) {
    const Cell*c=&gWorld.cells[cell];int start=-1,s,i;
    for(s=0;s<4;s++)if(c->gate[s]){start=s;break;}
    if(start<0)return;
    feet_rooms++;feet_flood(land[start][0],land[start][1],0);
    for(s=0;s<4;s++)if(c->gate[s]&&!feet_reaches(land[s][0],land[s][1]))
        fail(seed,cell,"10x8feet cannot reach door landing",land[s][0],land[s][1]);
    if(gSpots.has_chest)feet_target(seed,cell,"10x8feet chest approach",gSpots.chest,1);
    if(gSpots.has_npc)feet_target(seed,cell,"10x8feet NPC approach",gSpots.npc,1);
    if(gSpots.has_relic)feet_target(seed,cell,"10x8feet relic approach",gSpots.relic,0);
    if(gSpots.has_boss)feet_target(seed,cell,"10x8feet boss approach",gSpots.boss,0);
    if(gSpots.has_shrine)feet_target(seed,cell,"10x8feet shrine approach",gSpots.shrine,1);
    if(gSpots.has_mouth)feet_target(seed,cell,"10x8feet mouth approach",gSpots.mouth,1);
    for(i=0;i<gSpots.torch_count;i++)feet_target(seed,cell,"10x8feet torch approach",gSpots.torches[i],1);
}
static int gate_allowed(const Cell* c,int side,int items) {
    int g=c->gate[side];
    if(g==GATE_WALL)return 0;
    if(g==GATE_CRACK)return (items&1)||world_gate_open(gGame.cell,side);
    if(g==GATE_WEB)return (items&2)||world_gate_open(gGame.cell,side);
    if(g==GATE_CHASM)return (items&4)!=0;
    if(g==GATE_LOCK)return world_gate_open(gGame.cell,side);
    return 1;
}
static void boundary(unsigned seed,int cell,int items) {
    const Cell*c=&gWorld.cells[cell];int x,y,side;
    boundaries++;
    for(y=0;y<gRoom.h*2;y++)for(x=0;x<gRoom.w*2;x++) {
        int at=y*64+x,x0,y0,x1,y1;
        if(x&&y&&x!=gRoom.w*2-1&&y!=gRoom.h*2-1)continue;
        if(!seen[at])continue;
        side=y==0?SIDE_N:x==gRoom.w*2-1?SIDE_E:y==gRoom.h*2-1?SIDE_S:SIDE_W;
        roomgen_gate_tiles(side,&x0,&y0,&x1,&y1);
        /* North has a gate on row1 and an open visual forecourt on row0. */
        if(side==SIDE_N)y0=y1=0;
        if(!gate_allowed(c,side,items)||x/2<x0||x/2>x1||y/2<y0||y/2>y1)
            fail(seed,cell,"escape outside the allowed gate cutset",x,y);
    }
}
static void inspect(unsigned seed,int cell) {
    const Cell*c=&gWorld.cells[cell];int s,start=-1,i,items;
    for(s=0;s<4;s++)if(c->gate[s]){start=s;break;}
    if(start<0){fail(seed,cell,"no arrival side",0,0);return;}
    flood(land[start][0],land[start][1],0);
    for(s=0;s<4;s++)if(c->gate[s]&&!reaches(land[s][0],land[s][1]))
        fail(seed,cell,"door inner landing unreachable",land[s][0],land[s][1]);
    if(gSpots.has_chest)target(seed,cell,"chest approach",gSpots.chest,1);
    if(gSpots.has_npc)target(seed,cell,"NPC approach",gSpots.npc,1);
    if(gSpots.has_relic)target(seed,cell,"relic approach",gSpots.relic,0);
    if(gSpots.has_boss)target(seed,cell,"boss approach",gSpots.boss,0);
    if(gSpots.has_shrine)target(seed,cell,"shrine approach",gSpots.shrine,1);
    if(gSpots.has_mouth)target(seed,cell,"mouth approach",gSpots.mouth,1);
    if(c->role==ROLE_KEYITEM&&!gSpots.has_mouth)fail(seed,cell,"mandatory task has no entrance",0,0);
    for(i=0;i<gSpots.spawn_count;i++)target(seed,cell,"spawn approach",gSpots.spawns[i],0);
    for(i=0;i<gSpots.torch_count;i++)target(seed,cell,"quest torch approach",gSpots.torches[i],1);
    if(c->role==ROLE_NPC_TORCH&&gSpots.torch_count!=4)fail(seed,cell,"quest lacks four censers",0,0);
    if(gSpots.has_treasure&&gSpots.pocket_kind>=1&&gSpots.pocket_kind<=3) {
        Spot p=gSpots.treasure;int item=1<<(gSpots.pocket_kind-1),open=c->opened&CELL_POCKET_OPEN;pockets++;
        if(!open&&reaches(p.x,p.y))fail(seed,cell,"pocket bypasses required item",p.x,p.y);
        flood(land[start][0],land[start][1],item);
        if(!reaches(p.x,p.y))fail(seed,cell,"pocket blocked with right item",p.x,p.y);
        flood(land[start][0],land[start][1],7^item);
        if(!open&&reaches(p.x,p.y))fail(seed,cell,"pocket accepts wrong items",p.x,p.y);
    }
    for(items=0;items<8;items++) {
        flood(land[start][0],land[start][1],items);boundary(seed,cell,items);
    }
}
static unsigned digest(const void* data,unsigned n) {
    const unsigned char*p=data;unsigned h=2166136261u;
    while(n--){h^=*p++;h*=16777619u;}return h;
}
#if BART_FOREST_VARIANT >= 31
/* This expected-set contract is independent of the planner's candidate and
   grouping code: forest metadata marks wood; the old native drawing canvases
   contribute only their actual nonzero collision bases. */
static int old_tree(u16 mt) {
    return (mt>=MT_TREE_TOP_NW&&mt<=MT_TREE_TRUNK_E)||
           (mt>=MT_TREE2_0&&mt<=MT_TREE2_5)||
           (mt>=MT_GTREE_0&&mt<=MT_GTREE_11)||
           (mt>=MT_GTREE2_0&&mt<=MT_GTREE2_11)||
           (mt>=MT_BTREE_0&&mt<=MT_BTREE_11)||
           (mt>=MT_BIRCH_0&&mt<=MT_BIRCH_5)||
           (mt>=MT_FIR_0&&mt<=MT_FIR_5)||
           (mt>=MT_SICKTREE_0&&mt<=MT_SICKTREE_5)||
           mt==MT_DEAD_TREE||mt==MT_FOREST_BLIGHT_DEAD_TREE;
}
static void tree_inspect(unsigned seed,int cell) {
    unsigned char owners[1024];int i,x,y,count=gForestTreeStats[1],owned=0,expected=0;
    memset(owners,0,sizeof(owners));
    if(gForestTreeStats[0]!=1||!forest_trees_active()||gForestTreeStats[10]||count<=0||count>FOREST_TREES_MAX)
        fail(seed,cell,"invalid/empty/overflowed live tree scene",count,gForestTreeStats[10]);
    for(i=0;i<count;i++) {
        ForestTree*t=&gForestTrees[i];int w,dx;
        if(t->frame>=12){fail(seed,cell,"invalid native frame",i,t->frame);continue;}
        w=forest_tree_width[t->frame]/16;x=t->x/16;y=(t->y+16)/16;
        if(t->x%16||t->y%16||x<0||y<0||x+w>gRoom.w||y>=gRoom.h||(w!=1&&w!=2)) {
            fail(seed,cell,"tree base outside logical room",x,y);continue;
        }
        trees++;frame_seen[t->frame]++;
        stage_state[gWorld.cells[cell].stage<4?gWorld.cells[cell].stage:3][forest_tree_state[t->frame]]++;
        for(dx=0;dx<w;dx++) {
            int at=y*32+x+dx,mt=room_get(x+dx,y);root_checks++;owned++;
            if(++owners[at]!=1||gForestTreeRoots[at]!=i+1)
                fail(seed,cell,"base cell lacks unique matching native tree owner",x+dx,y);
            if(!metatile_coll[mt]||(!forest_v2_canopy_kind[mt]&&!old_tree(mt)))
                fail(seed,cell,"tree invents a blocker over unrelated terrain",x+dx,y);
            if(t->root_mask[dx]!=metatile_coll[mt])
                fail(seed,cell,"native root record changes original collision mask",x+dx,y);
        }
    }
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int mt=room_get(x,y),at=y*32+x;
        int root=metatile_coll[mt]&&(forest_v2_canopy_kind[mt]||old_tree(mt));
        if(root){expected++;if(forest_v2_canopy_kind[mt])wood_cells++;else authored_cells++;}
        if(root!=(owners[at]!=0)||root!=(gForestTreeRoots[at]!=0))
            fail(seed,cell,"solid tree base and native picture ownership differ",x,y);
    }
    if(owned!=expected||expected!=gForestTreeStats[2]+gForestTreeStats[3])
        fail(seed,cell,"tree/base totals disagree",owned,expected);
}
static unsigned tree_digest(void) {
    return digest(gForestTrees,gForestTreeStats[1]*sizeof(ForestTree))^
           digest(gForestTreeRoots,sizeof(gForestTreeRoots))^digest(gForestTreeStats,sizeof(gForestTreeStats));
}
static void cache_check(unsigned seed,int cell) {
    Room held=gRoom;unsigned before=tree_digest();int x,y;
    /* Live redraw/menu return must not reroll trees after a clearable bush
       exposes floor. A fresh native room entry resets this cache separately. */
    for(y=2;y<gRoom.h-2;y++)for(x=1;x<gRoom.w-1;x++) {
        int mt=room_get(x,y);
        if(mt==MT_BUSH||mt==MT_THORN||mt==MT_TALL_GRASS) {
            room_set(x,y,MT_MOSS0);room_build_solid();forest_trees_plan();cache_checks++;
            if(before!=tree_digest())fail(seed,cell,"live bush-clear redraw rerolls resident trees",x,y);
            gRoom=held;return;
        }
    }
    forest_trees_plan();cache_checks++;
    if(before!=tree_digest())fail(seed,cell,"live same-room redraw rerolls resident trees",0,0);
}
#endif
static void build(int cell) {
    gGame.cell=cell;roomgen_build_internal(cell,FALSE);room_build_solid();
#if BART_FOREST_VARIANT >= 31
    /* The hardware-native entry pipeline calls tiles_load(), which clears
       the live scene cache. Suppress VRAM but preserve that lifecycle here. */
    forest_trees_reset();
    unsigned prior=digest(&gRoom,sizeof(gRoom));
    forest_trees_plan();
    if(prior!=digest(&gRoom,sizeof(gRoom)))fail(gWorld.seed,cell,"tree plan mutates semantic room/collision",0,0);
#endif
}
int main(int argc,char**argv) {
    unsigned n=argc>1?strtoul(argv[1],0,0):512,k;int cell;
    gGame.area=AREA_FOREST;gGame.state=GS_PLAY;
    for(k=1;k<=n;k++) {
        unsigned seed=k<=8?(unsigned[]){0,1,7,42,0xb4a7,0xdeadbeef,0xffffffff,0x80000000}[k-1]:hash32(0xd2170e5u,k);
        world_generate(seed);
        for(cell=0;cell<CELLS;cell++) {
            unsigned before;RoomSpots spots;
            build(cell);inspect(seed,cell);if(k<=32)feet_inspect(seed,cell);rooms++;
#if BART_FOREST_VARIANT >= 31
            unsigned tree_before=tree_digest();tree_inspect(seed,cell);
            if(k<=32) {
                u8 marks[MP_COUNT*2];
                unsigned room_before=digest(&gRoom,sizeof(gRoom));
                roomgen_preview_events((cell+7)%CELLS,marks);preview_checks++;
                if(tree_before!=tree_digest()||room_before!=digest(&gRoom,sizeof(gRoom)))
                    fail(seed,cell,"paused-map preview corrupts resident trees or Room",0,0);
                cache_check(seed,cell);
            }
#endif
            before=digest(&gRoom,sizeof(gRoom));spots=gSpots;
            build(cell);determinism++;
            if(before!=digest(&gRoom,sizeof(gRoom))||digest(&spots,sizeof(spots))!=digest(&gSpots,sizeof(gSpots)))
                fail(seed,cell,"return build is nondeterministic",0,0);
#if BART_FOREST_VARIANT >= 31
            if(tree_before!=tree_digest())fail(seed,cell,"return tree plan is nondeterministic",0,0);
#endif
            if(k<=32) {
                u8 old_open=gWorld.cells[cell].opened;
                gWorld.cells[cell].opened|=15|CELL_POCKET_OPEN;
                build(cell);inspect(seed,cell);feet_inspect(seed,cell);opened_state_rooms++;
#if BART_FOREST_VARIANT >= 31
                tree_inspect(seed,cell);
#endif
                gWorld.cells[cell].opened=old_open;
            }
        }
        if(k%64==0){printf("PROGRESS seeds=%u rooms=%lu failures=%d\n",k,rooms,failures);fflush(stdout);}
        if(failures>100)break;
    }
    printf("RESULT {\"requested_seeds\":%u,\"rooms\":%lu,\"opened_state_rooms\":%lu,\"approaches\":%lu,\"pockets\":%lu,\"determinism\":%lu,\"boundary_inventory_checks\":%lu,\"feet_box_rooms\":%lu,\"trees\":%lu,\"wood_cells\":%lu,\"authored_cells\":%lu,\"root_ownership_checks\":%lu,\"preview_preservation_checks\":%lu,\"live_scene_cache_checks\":%lu,\"frame_counts\":[",n,rooms,opened_state_rooms,approaches,pockets,determinism,boundaries,feet_rooms,trees,wood_cells,authored_cells,root_checks,preview_checks,cache_checks);
    for(cell=0;cell<12;cell++)printf("%s%lu",cell?",":"",frame_seen[cell]);
    printf("],\"stage_state_counts\":[");
    for(cell=0;cell<4;cell++)printf("%s[%lu,%lu,%lu]",cell?",":"",stage_state[cell][0],stage_state[cell][1],stage_state[cell][2]);
    printf("],\"failures\":%d}\n",failures);
    return failures?1:0;
}
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', required=True, help='Frozen profile31 ROM/map/assets.h directory')
    p.add_argument('--base', required=True, help='Frozen unchanged profile30 for resolved nonforest payload comparisons')
    p.add_argument('--out', required=True)
    p.add_argument('--host-seeds', type=int, default=512)
    p.add_argument('--allow-pilot', action='store_true', help='Explicitly allow a diagnostic bundle with no freeze.json')
    p.add_argument('--capture', help='Real mGBA capture.json to independently audit camera-mosaic provenance')
    p.add_argument('--tree-tiles', help='Explicit separate tree tile array; omit for shared forest atlas')
    p.add_argument('--tree-slot', default='FOREST_TREE_PALETTE_SLOT')
    return Audit(p.parse_args()).run()


if __name__ == '__main__':
    raise SystemExit(main())
