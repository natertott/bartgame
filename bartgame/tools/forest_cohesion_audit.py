#!/usr/bin/env python3
"""Independent native-art, geometry and real-capture review of forest profile32.

The host executes the actual room/forest-tree C against frozen native metadata.
It verifies route/interaction safety separately from the new ecological shape
checks. Passing numeric checks does not establish that a room looks natural.
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

import forest_trees_audit as PRIOR
from sewer_concept_audit import NativeRom, decode_sprite
from forest_tree_study_audit import decode_map, rgb555

GAME = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
APPROVED_PAINTER = PRIOR.APPROVED_PAINTER


def export_source():
    """Load authored profile32 pictures in a separate, clean interpreter."""
    os.environ['BART_FOREST'] = '32'
    sys.path.insert(0, str(GAME/'art'))
    import tiles
    import palettes
    rows = []
    for mt in tiles.METATILES:
        if mt['name'].startswith(('sw_', 'swh_', 'cave_', 'hollow_', 'thicket_', 'myst_')):
            continue
        frames = mt.get('frames') or [mt['art']]
        rows.append({'name': mt['name'], 'frames': frames,
                     'palettes': mt.get('qpals') or [mt['pal']]*4,
                     'owner': tiles.FOREST_OWNERS.get(mt['name'], 'topology or retained source')})
    print(json.dumps({'metatiles': rows, 'palettes': dict(palettes.BG_PALETTES)}))


class Audit(PRIOR.Audit):
    def __init__(self, args):
        super().__init__(args)
        self.tool_sha256 = SHA(Path(__file__).read_bytes())

    def provenance(self):
        path = self.rom.directory/'freeze.json'
        if not path.exists():
            self.check('provenance', 'frozen build metadata exists', self.args.allow_pilot,
                       'Explicit unfrozen pilot; not final release evidence.')
            return {'unfrozen_pilot': True}
        freeze = json.loads(path.read_text())
        self.check('provenance', 'frozen ROM hash/profile match the loaded bytes',
                   freeze['rom_sha256'] == SHA(self.rom.rom) and
                   freeze.get('variant', freeze.get('forest_variant')) == 32)
        for field in ('source_file_sha256', 'code_file_sha256'):
            for relative, expected in freeze[field].items():
                self.check('provenance', relative+' matches frozen input', SHA((GAME/relative).read_bytes()) == expected)
        baseline = json.loads((self.base.directory/'freeze.json').read_text())
        for relative in ('src/world.c', 'src/world.h'):
            self.check('scope', relative+' preserves the 5x5 progression engine',
                       freeze['code_file_sha256'][relative] == baseline['code_file_sha256'][relative])
        return {'source_commit': freeze['source_commit'], 'unfrozen_pilot': False,
                'baseline_source': baseline['source_commit']}

    def scope(self):
        self.check('scope', 'all existing metatile identifiers remain stable',
                   all(self.rom.tile_ids.get(n) == i for n, i in self.base.tile_ids.items()))
        for name in ('sewer', 'myst'):
            before, after = self.base.tileset(name), self.rom.tileset(name)
            for key in ('tiles', 'tile_count', 'palettes', 'palette_count', 'animations'):
                self.check('scope', name+' resolved '+key+' remains exact', before[key] == after[key])
            self.check('scope', name+' original map entries remain exact after new forest IDs append',
                       after['map'][:len(before['map'])] == before['map'] and
                       not any(after['map'][len(before['map']):]))
        for name in ('metatile_type', 'metatile_coll', 'metatile_prop', 'metatile_glitter'):
            old, new = self.base.array(name), self.rom.array(name)
            self.check('scope', name+' original physical/visual metadata prefix remains exact', new[:len(old)] == old)
        for name in sorted(self.base.sheet_ids):
            self.check('scope', name+' complete object sheet remains exact',
                       self.rom.sheet(name) == self.base.sheet(name))
        names = sorted(n for n in self.base.sections if n in self.rom.sections and
                       not n.startswith(('forest_', 'tree_study_', 'tileset_', 'ts_')) and
                       (any(k in n for k in ('palette', 'title', 'font', 'hud', 'menu', 'dialogue')) or
                        n.startswith(('pal_', 'appearance_', 'ui_')) or
                        n.endswith('_frame_pal') or n == 'icon32_exact_pal'))
        for name in names:
            self.check('scope', name+' protected scalar payload remains exact', self.rom.array(name) == self.base.array(name))
        self.check('scope', 'all global BG palette bytes remain exact outside area-local forest loading',
                   self.rom.array('pal_bg') == self.base.array('pal_bg'))
        changes = self.forest_changes()
        return {'protected_object_sheets': len(self.base.sheet_ids), 'protected_scalar_arrays': names,
                'forest_refinement': changes}

    def forest_changes(self):
        before, after = self.base.tileset('forest'), self.rom.tileset('forest')
        phases = max([a['frames'] for t in (before, after) for a in t['animations']]+[1])
        def atlases(ts):
            result = []
            for phase in range(phases):
                data = bytearray(ts['tiles'])
                for a in ts['animations']:
                    k = phase % a['frames']; data[a['base']*32:a['base']*32+128] = a['data'][k*128:(k+1)*128]
                result.append(data)
            return result
        old_atlas, new_atlas = atlases(before), atlases(after)
        def resolved(ts, atlas, index):
            result = []
            for entry in struct.unpack_from('<4H', ts['map'], index*8):
                palette = struct.unpack_from('<16H', ts['palettes'], (entry >> 12)*32)
                result.extend(palette[i] if i else 0x8000 for i in decode_map(atlas, [entry], 8, 8))
            return result
        changed, retained = [], []
        for name, index in self.base.tile_ids.items():
            same = all(resolved(before, old_atlas[p], index) ==
                       resolved(after, new_atlas[p], self.rom.tile_ids[name]) for p in range(phases))
            (retained if same else changed).append(name)
        self.check('art', 'forest refinement changes actual packed terrain rather than only a screenshot',
                   len(changed) >= 20 and any(n.startswith('WATER') for n in changed) and
                   any(n.startswith(('PATH','PEDGE')) for n in changed), {'changed': len(changed)})
        return {'changed_old_metatiles': changed, 'retained_old_metatiles': retained,
                'new_visual_metatiles': sorted(set(self.rom.tile_ids)-set(self.base.tile_ids)),
                'comparison': 'Resolved native RGB555/alpha pixels and all declared animation phases; retained families are not falsely claimed redrawn.'}

    def authored(self):
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--export-source'],
                                cwd=GAME, check=True, text=True, capture_output=True)
        source = json.loads(result.stdout)
        ts = self.rom.tileset('forest')
        colors = {name: [int(c[1:3],16)//8 | (int(c[3:5],16)//8 << 5) |
                          (int(c[5:7],16)//8 << 10) for c in values]
                  for name, values in source['palettes'].items()}
        count, pixels, failed = 0, 0, []
        for mt in source['metatiles']:
            name = mt['name'].upper()
            if name not in self.rom.tile_ids:
                failed.append([mt['name'], 'missing linked ID'])
                self.check('source', mt['name']+' authored picture has a linked metatile ID', False)
                continue
            index = self.rom.tile_ids[name]
            entries = struct.unpack_from('<4H', ts['map'], index*8)
            for phase, rows in enumerate(mt['frames']):
                assert len(rows) == 16 and all(len(row) == 16 for row in rows)
                expected = [0 if p in '. ' else int(p,16) for row in rows for p in row]
                atlas = bytearray(ts['tiles'])
                for a in ts['animations']:
                    k = phase % a['frames']
                    atlas[a['base']*32:a['base']*32+128] = a['data'][k*128:(k+1)*128]
                actual = decode_map(atlas, entries, 16, 16)
                valid = True
                for y in range(16):
                    for x in range(16):
                        p = y*16+x; q = (y//8)*2+x//8; ink = expected[p]
                        palette = struct.unpack_from('<16H', ts['palettes'], (entries[q] >> 12)*32)
                        want = colors[mt['palettes'][q]][ink] if ink else 0x8000
                        got = palette[actual[p]] if actual[p] else 0x8000
                        valid &= want == got
                count += 1; pixels += 256
                if not valid:
                    failed.append([mt['name'], phase])
            self.check('source', mt['name']+' preserves authored native RGB555/alpha in all source frames',
                       not any(row[0] == mt['name'] for row in failed), mt['owner'])
        return {'native_metatiles': len(source['metatiles']), 'native_frames': count,
                'compared_pixels': pixels, 'failures': failed,
                'source_export_sha256': SHA(result.stdout.encode()),
                'method': 'Clean profile32 source import; independent 4bpp/flip/palette decoding of actual linked forest atlas, no build_assets parser/deduplicator import.'}

    def native(self):
        sys.path.insert(0, str(GAME/'art'))
        import forest_tree_study as art
        source_path = GAME/'art/forest_tree_study.py'
        self.check('native', 'approved painter bytes remain exact', SHA(source_path.read_bytes()) == APPROVED_PAINTER)
        self.check('native', 'profile32 is the room-cohesion profile', self.rom.defs['BART_FOREST_VARIANT'] == 32)
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
                   *([str(GAME/'src/forest_paths.c')] if (GAME/'src/forest_paths.c').exists() and self.rom.defs['BART_FOREST_VARIANT'] == 32 else []),
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
        landscape = stats.get('landscape', {})
        quality_failures = landscape.get('failures', -1)
        self.check('geometry', 'actual roots preserve approaches, gate cutsets and item pockets',
                   result.returncode in (0, 1) and quality_failures >= 0 and
                   stats.get('failures', -1)-quality_failures-landscape.get('relic_layout_failures', 0) == 0, stats)
        self.check('landscape', 'completed rooms preserve coherent water, useful crossings and purposeful lights',
                   result.returncode in (0, 1) and quality_failures == 0, landscape)
        self.check('geometry', 'visible trail refinement changes no physical tile types or collision masks',
                   landscape.get('trail_refine_calls', 0) > 0 and landscape.get('trail_physics_failures', -1) == 0,
                   {k: landscape.get(k) for k in ('trail_refine_calls', 'trail_physics_failures')})
        self.check('lifecycle', 'permanent relic-dais paths and lamps survive collection and room re-entry',
                   landscape.get('relic_collection_cases', 0) > 0 and landscape.get('relic_layout_failures', -1) == 0,
                   {k: landscape.get(k) for k in ('relic_collection_cases', 'relic_layout_failures')})
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
                                     (GAME/'src/roomgen.c', GAME/'src/room.c', GAME/'src/forest_trees.c', GAME/'src/forest_paths.c', GAME/'src/world.c', GAME/'src/util.c') if p.exists()})
        (directory/'report.json').write_text(json.dumps(record, indent=2)+'\n')
        return record

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
        self.check('timing', name+' literal missed native updates are reported without historical threshold substitution',
                   missed == walk.get('missed_updates', missed),
                   {'actual_missed_updates': missed, 'frame_perfect_claim': False})
        return {'frames': len(observations), 'minimum_visible_current_native_Bloom_pixels': minimum,
                'guarded_frames': guarded, 'occluded_frames': behind, 'missed_logic_updates': missed,
                'timing': 'Literal intervals reported; performance comparison requires matched scenes and conditions, not old unrelated thresholds.'}


    captures = PRIOR.Audit.captures

    def run(self):
        report = dict(rom_sha256=SHA(self.rom.rom), base_rom_sha256=SHA(self.base.rom),
                      audit_tool_sha256=self.tool_sha256, command=sys.argv,
                      dependencies_sha256={'forest_trees_audit.py': SHA(Path(PRIOR.__file__).read_bytes())},
                      provenance=self.provenance(), approved_native_art=self.native(), protected_art=self.scope())
        if self.args.source_art:
            report['authored_native_art'] = self.authored()
        if self.args.host_seeds:
            report['host'] = self.host()
        if self.args.capture:
            report['captures'] = self.captures()
        self.check('provenance', 'audit helper was held through execution', SHA(Path(__file__).read_bytes()) == self.tool_sha256)
        self.check('provenance', 'frozen ROM/header/map remained unchanged',
                   all(SHA((self.rom.directory/n).read_bytes()) == v for n,v in self.bundle_hashes.items()))
        report.update(checks=self.rows, passed=sum(r['passed'] for r in self.rows), total=len(self.rows),
                      failures=[r for r in self.rows if not r['passed']])
        (self.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        print('RESULT', report['passed'], '/', report['total'], flush=True)
        return bool(report['failures'])


LANDSCAPE_HOST = r'''

/* Independent landscape checks use the completed semantic room, not the
   generator's proposed candidate/rejection predicates or decoration counters. */
static unsigned long qa_water_components,qa_water_cells,qa_bridge_runs,qa_bridge_landings;
static unsigned long qa_lights,qa_unanchored_lights,qa_detail_cells,qa_context_details,qa_ledge_cells;
static unsigned long qa_landscape_failures;
static unsigned long qa_motifs[6];
static int qa_deck(int x,int y) {
    if(x<0||y<0||x>=gRoom.w||y>=gRoom.h)return 0;
    int mt=room_get(x,y);return mt==MT_BRIDGE?1:mt==MT_BRIDGE_V?2:0;
}
static int qa_water(int x,int y) {
    if(x<0||y<0||x>=gRoom.w||y>=gRoom.h)return 0;
    int mt=room_get(x,y),kind=forest_v2_water_kind[mt];
    return (kind>=1&&kind<=3)||mt==MT_WATERFALL;
}
static int qa_wet(int x,int y) {return qa_water(x,y)||qa_deck(x,y);}
static int qa_dry_landing(int x,int y) {
    if(x<1||y<2||x>=gRoom.w-1||y>=gRoom.h-1||qa_wet(x,y))return 0;
    int t=room_type(x,y),dx,dy;
    if(t!=TT_FLOOR&&t!=TT_SLOW&&t!=TT_DOOR_OPEN&&t!=TT_STAIRS)return 0;
    for(dy=0;dy<2;dy++)for(dx=0;dx<2;dx++)
        if(gRoom.solid[(y*2+dy)*64+x*2+dx])return 0;
    return reaches(x,y);
}
static int qa_path(int x,int y) {
    if(x<0||y<0||x>=gRoom.w||y>=gRoom.h)return 0;
    int mt=room_get(x,y);
    return mt==MT_PATH||mt==MT_PATH_EDGE_N||mt==MT_BLIGHT_VEIN||
           (mt>=MT_PEDGE_1&&mt<=MT_PEDGE_F)||(mt>=MT_PEDGE_C1&&mt<=MT_PEDGE_CF);
}
static int qa_feature_near(int x,int y,int d) {
    int i;
    for(i=0;i<gSpots.torch_count;i++)
        if(ABS(x-gSpots.torches[i].x)+ABS(y-gSpots.torches[i].y)<=d)return 1;
    return (gSpots.has_chest&&ABS(x-gSpots.chest.x)+ABS(y-gSpots.chest.y)<=d)||
           (gSpots.has_npc&&ABS(x-gSpots.npc.x)+ABS(y-gSpots.npc.y)<=d)||
           ((gSpots.has_relic||gWorld.cells[gGame.cell].role==ROLE_RELIC)&&ABS(x-gSpots.relic.x)+ABS(y-gSpots.relic.y)<=d)||
           (gSpots.has_shrine&&ABS(x-gSpots.shrine.x)+ABS(y-gSpots.shrine.y)<=d)||
           (gSpots.has_mouth&&ABS(x-gSpots.mouth.x)+ABS(y-(gSpots.mouth.y+1))<=d)||
           (gSpots.has_treasure&&ABS(x-gSpots.treasure.x)+ABS(y-gSpots.treasure.y)<=d)||
           (gSpots.has_treasure&&ABS(x-gSpots.pocket_gate.x)+ABS(y-gSpots.pocket_gate.y)<=d)||
           (gSpots.has_boss&&ABS(x-gSpots.boss.x)+ABS(y-gSpots.boss.y)<=d);
}
static int qa_route_anchor(int x,int y) {
    int dx,dy;
    if(qa_feature_near(x,y,4))return 1;
    for(dy=-3;dy<=3;dy++)for(dx=-3;dx<=3;dx++)
        if(ABS(dx)+ABS(dy)<=3&&(qa_path(x+dx,y+dy)||qa_deck(x+dx,y+dy)))return 1;
    return 0;
}
static int qa_detail(int mt) {
    return mt==MT_BONES||mt==MT_STUMP||mt==MT_SICK_STUMP||mt==MT_SICK_ROCK||
           mt==MT_ROCK||mt==MT_ROCK2||mt==MT_ROCK3||mt==MT_LOG||
           mt==MT_HLOG_0||mt==MT_HLOG_1||mt==MT_ROCK_SMALL||mt==MT_BUSH;
}
static int qa_detail_context(int x,int y) {
    int dx,dy;
    if(qa_feature_near(x,y,4))return 1;
    for(dy=-3;dy<=3;dy++)for(dx=-3;dx<=3;dx++) {
        int nx=x+dx,ny=y+dy,mt;
        if(ABS(dx)+ABS(dy)>3||nx<0||ny<0||nx>=gRoom.w||ny>=gRoom.h)continue;
        mt=room_get(nx,ny);
        if(forest_v2_canopy_kind[mt]||qa_wet(nx,ny)||
           (mt==MT_MOSSY_STONE))return 1;
    }
    return 0;
}
static void qa_landscape(unsigned seed,int cell) {
    unsigned char wet_seen[768]={0};int q[768],x,y,i,component_count=0,water_count=0,deck_count=0;
    int lamp_x[128],lamp_y[128],lamp_count=0,lamp_seen[128]={0};
    int start=-1,s,failures_before=failures;
    for(s=0;s<4;s++)if(gWorld.cells[cell].gate[s]){start=s;break;}
    if(start>=0)flood(land[start][0],land[start][1],0);
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int mt=room_get(x,y),d=qa_deck(x,y),at=y*32+x;
        if(qa_water(x,y)){water_count++;qa_water_cells++;}
        if(d)deck_count++;
        if(qa_detail(mt)) {qa_detail_cells++;qa_context_details+=qa_detail_context(x,y);}
        if(mt==MT_LEDGE_N||mt==MT_LEDGE_S||mt==MT_LEDGE_S_W||mt==MT_LEDGE_S_E)qa_ledge_cells++;
        if(mt==MT_LANTERN_POST) {
            qa_lights++;
            if(lamp_count<128){lamp_x[lamp_count]=x;lamp_y[lamp_count]=y;lamp_seen[lamp_count]=qa_route_anchor(x,y);lamp_count++;}
            else fail(seed,cell,"too many lanterns for contextual audit",x,y);
        }
        if(qa_wet(x,y)&&!wet_seen[at]) {
            int head=0,tail=0,tiles=0;wet_seen[at]=1;q[tail++]=at;
            component_count++;qa_water_components++;
            while(head<tail) {
                int p=q[head++],cx=p%32,cy=p/32,j;tiles++;
                static const int dx[4]={0,1,0,-1},dy[4]={-1,0,1,0};
                for(j=0;j<4;j++) {
                    int nx=cx+dx[j],ny=cy+dy[j],next=ny*32+nx;
                    if(qa_wet(nx,ny)&&!wet_seen[next]){wet_seen[next]=1;q[tail++]=next;}
                }
            }
            if(tiles==1)fail(seed,cell,"isolated one-cell water/deck component",x,y);
        }
        if(d&&!(d==1?qa_deck(x-1,y)==1:qa_deck(x,y-1)==2)) {
            int ex=x,ey=y,wet_neighbor=0,j;
            while(d==1?qa_deck(ex+1,ey)==1:qa_deck(ex,ey+1)==2){if(d==1)ex++;else ey++;}
            qa_bridge_runs++;qa_bridge_landings+=2;
            int ax=d==1?x-1:x,ay=d==1?y:y-1,bx=d==1?ex+1:ex,by=d==1?ey:ey+1;
            if(!qa_dry_landing(ax,ay)||!qa_dry_landing(bx,by))fail(seed,cell,"bridge lacks two dry reachable full-footprint landings",x,y);
            for(j=0;j<=(d==1?ex-x:ey-y);j++) {
                int px=x+(d==1?j:0),py=y+(d==2?j:0);
                wet_neighbor|=d==1?(qa_water(px,py-1)||qa_water(px,py+1)):(qa_water(px-1,py)||qa_water(px+1,py));
            }
            if(!wet_neighbor)fail(seed,cell,"bridge deck does not cross visible water",x,y);
        }
    }
    for(s=0;s<lamp_count;s++)for(i=0;i<lamp_count;i++)if(lamp_seen[i]) {
        int j;for(j=0;j<lamp_count;j++)if(ABS(lamp_x[j]-lamp_x[i])+ABS(lamp_y[j]-lamp_y[i])<=4)lamp_seen[j]=1;
    }
    for(i=0;i<lamp_count;i++)if(!lamp_seen[i]){qa_unanchored_lights++;fail(seed,cell,"lantern lacks route/feature or connected clue chain",lamp_x[i],lamp_y[i]);}
#if BART_FOREST_VARIANT == 32
    int motif=gForestCohesionInfo[1];
    if(gForestCohesionInfo[0]!=1||motif>=6)fail(seed,cell,"invalid room motif ABI",motif,gForestCohesionInfo[0]);
    else qa_motifs[motif]++;
    if(motif==2&&(water_count<13||component_count!=1))fail(seed,cell,"pond motif lacks a coherent thirteen-cell water body",water_count,component_count);
#endif
    qa_landscape_failures+=failures-failures_before;
}

'''

HOST = PRIOR.HOST
HOST = HOST.replace('#include "ROOMGEN_SOURCE"', r'''
#include "forest_paths.h"
static unsigned long qa_trail_calls,qa_trail_physics_failures;
static void qa_trail_refine(int cell,u8* path);
#define forest_paths_refine qa_trail_refine
#include "ROOMGEN_SOURCE"
#undef forest_paths_refine
static void qa_trail_refine(int cell,u8* path) {
    u16 before[32*24],overlay[32*24];int x,y,changed=0;
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int q=y*32+x,mt=room_get(x,y);
        before[q]=metatile_coll[mt]|(metatile_type[mt]<<8);overlay[q]=room_get_overlay(x,y);
    }
    forest_paths_refine(cell,path);qa_trail_calls++;
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int q=y*32+x,mt=room_get(x,y);
        if(before[q]!=(metatile_coll[mt]|(metatile_type[mt]<<8))||overlay[q]!=room_get_overlay(x,y))changed=1;
    }
    if(changed){qa_trail_physics_failures++;printf("FAIL seed=%u cell=%d trail refinement changes physical type/collision or authored overlay\n",gWorld.seed,cell);}
}
''')
HOST = HOST.replace('static unsigned digest(', LANDSCAPE_HOST + '\nstatic unsigned digest(', 1)
HOST = HOST.replace('int main(int argc,char**argv) {', r'''
static unsigned long qa_relic_cases,qa_relic_layout_failures;
static void qa_relic_collection(unsigned seed,int cell) {
    u8 paths[32*24],lamps[32*24],flags=gWorld.cells[cell].flags;int x,y,mismatch=0,shown=0;
    if(gWorld.cells[cell].role!=ROLE_RELIC)return;
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int q=y*32+x;paths[q]=qa_path(x,y);lamps[q]=room_get(x,y)==MT_LANTERN_POST;
    }
    gWorld.cells[cell].flags|=CF_RELIC_TAKEN;build(cell);qa_relic_cases++;
    if(gSpots.has_relic)mismatch=1;
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int q=y*32+x;
        if(paths[q]!=qa_path(x,y)||lamps[q]!=(room_get(x,y)==MT_LANTERN_POST)) {
            if(shown++<4)printf("RELIC_DIFF seed=%u cell=%d pos=%d,%d road=%d->%d lamp=%d->%d\n",seed,cell,x,y,paths[q],qa_path(x,y),lamps[q],room_get(x,y)==MT_LANTERN_POST);
            mismatch=1;
        }
    }
    if(mismatch){qa_relic_layout_failures++;fail(seed,cell,"relic collection changes remembered trail/lantern layout",0,0);}
    gWorld.cells[cell].flags=flags;build(cell);
}
'''+'\nint main(int argc,char**argv) {', 1)
HOST = HOST.replace('            if(k<=32) {\n                u8 old_open=', '            qa_relic_collection(seed,cell);\n            if(k<=32) {\n                u8 old_open=', 1)
HOST = HOST.replace('build(cell);inspect(seed,cell);if(k<=32)feet_inspect(seed,cell);rooms++;',
                    'build(cell);inspect(seed,cell);qa_landscape(seed,cell);if(k<=32)feet_inspect(seed,cell);rooms++;')
HOST = HOST.replace('unsigned tree_before=tree_digest();tree_inspect(seed,cell);',
                    'unsigned tree_before=tree_digest();unsigned info_before=digest(gForestCohesionInfo,sizeof(gForestCohesionInfo));tree_inspect(seed,cell);')
HOST = HOST.replace('roomgen_preview_events((cell+7)%CELLS,marks);preview_checks++;',
                    'roomgen_preview_events((cell+7)%CELLS,marks);preview_checks++;if(info_before!=digest(gForestCohesionInfo,sizeof(gForestCohesionInfo)))fail(seed,cell,"paused-map preview corrupts live motif metadata",0,0);')
HOST = HOST.replace('if(tree_before!=tree_digest())fail(seed,cell,"return tree plan is nondeterministic",0,0);',
                    'if(tree_before!=tree_digest())fail(seed,cell,"return tree plan is nondeterministic",0,0);if(info_before!=digest(gForestCohesionInfo,sizeof(gForestCohesionInfo)))fail(seed,cell,"return room motif metadata is nondeterministic",0,0);')
HOST = HOST.replace('printf("],\\"failures\\":%d}\\n",failures);',
                    'printf("],\\"landscape\\":{\\"water_components\\":%lu,\\"water_cells\\":%lu,\\"bridge_runs\\":%lu,\\"bridge_landing_checks\\":%lu,\\"lantern_posts\\":%lu,\\"unanchored_lanterns\\":%lu,\\"detail_cells\\":%lu,\\"details_near_material_context\\":%lu,\\"ledge_cells\\":%lu,\\"failures\\":%lu,\\"trail_refine_calls\\":%lu,\\"trail_physics_failures\\":%lu,\\"relic_collection_cases\\":%lu,\\"relic_layout_failures\\":%lu,\\"motifs\\":[%lu,%lu,%lu,%lu,%lu,%lu]},\\"failures\\":%d}\\n",qa_water_components,qa_water_cells,qa_bridge_runs,qa_bridge_landings,qa_lights,qa_unanchored_lights,qa_detail_cells,qa_context_details,qa_ledge_cells,qa_landscape_failures,qa_trail_calls,qa_trail_physics_failures,qa_relic_cases,qa_relic_layout_failures,qa_motifs[0],qa_motifs[1],qa_motifs[2],qa_motifs[3],qa_motifs[4],qa_motifs[5],failures);')


def main():
    if '--export-source' in sys.argv:
        export_source()
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--base', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--host-seeds', type=int, default=32)
    parser.add_argument('--allow-pilot', action='store_true')
    parser.add_argument('--capture')
    parser.add_argument('--source-art', action='store_true', help='Compare clean authored profile32 pictures with the frozen native forest atlas')
    parser.add_argument('--tree-tiles')
    parser.add_argument('--tree-slot', default='FOREST_TREE_PALETTE_SLOT')
    return Audit(parser.parse_args()).run()


if __name__ == '__main__':
    raise SystemExit(main())
