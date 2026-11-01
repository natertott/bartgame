#!/usr/bin/env python3
"""Focused independent native/ROM audit for the repeated tree diagnostic grove.

The guide supplies design advice, not test thresholds. These checks establish
native dimensions, index/palette/map fidelity and scope; visual judgment stays
separate from numerical success. The compact grove is a deliberate review
fixture, not a naturally generated forest room.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from sewer_concept_audit import NativeRom, decode_8x8

GAME = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()


def rgb555(colors):
    result = []
    for color in colors:
        assert len(color) == 7 and color[0] == '#'
        rgb = [int(color[k:k+2], 16) for k in (1, 3, 5)]
        assert all(v % 8 == 0 for v in rgb), color
        result.append(sum((value // 8) << (axis * 5) for axis, value in enumerate(rgb)))
    assert len(result) == 16
    return result


def decode_map(tiles, entries, width, height):
    """Decode native 4bpp nibbles and independent per-subtile flips."""
    assert width % 8 == height % 8 == 0
    assert len(entries) == width * height // 64
    result = bytearray(width * height)
    for n, entry in enumerate(entries):
        tile = entry & 1023
        assert tile * 32 + 32 <= len(tiles)
        values = decode_8x8(tiles[tile*32:tile*32+32])
        ox, oy = (n % (width//8))*8, (n // (width//8))*8
        for y in range(8):
            for x in range(8):
                sx, sy = (7-x if entry & 0x400 else x), (7-y if entry & 0x800 else y)
                result[(oy+y)*width+ox+x] = values[sy*8+sx]
    return bytes(result)


def masks(pixels):
    return bytes(bool(value) for value in pixels)


class Audit:
    def __init__(self, args):
        self.args, self.checks = args, []
        self.root = Path(args.frozen)
        self.rom = NativeRom(self.root/'v30')
        self.base = NativeRom(self.root/'v29')
        self.source = self.load_source()

    def check(self, group, name, passed, detail=None):
        row = {'group': group, 'name': name, 'passed': bool(passed)}
        if detail is not None:
            row['detail'] = detail
        self.checks.append(row)
        if not passed:
            print('FAIL', group, name, detail, flush=True)

    def load_source(self):
        sys.path.insert(0, str(GAME/'art'))
        import forest_tree_study as art
        specs, images = art.specs(), []
        for spec in specs:
            image = art.tree(spec['size'], spec['variety'], spec['state'])
            assert image.mode == 'P' and image.size == tuple(spec['size_pixels'])
            images.append(image)
        return {'module': art, 'specs': specs, 'images': images,
                'palette': rgb555(art.palette())}

    def provenance(self):
        freeze = json.loads((self.root/'v30/freeze.json').read_text())
        self.check('provenance', 'profile30 ROM binds the frozen source',
                   freeze.get('variant', freeze.get('forest_variant')) == 30 and
                   freeze['rom_sha256'] == SHA(self.rom.rom) and not freeze.get('unfrozen_pilot', False))
        for field in ('source_file_sha256', 'code_file_sha256'):
            for name, digest in freeze[field].items():
                self.check('provenance', name+' current bytes match frozen inputs', SHA((GAME/name).read_bytes()) == digest)
        return freeze['source_commit']

    def native(self):
        rom, source = self.rom, self.source
        self.check('native', 'twelve source entries cover both sizes, varieties and structural states',
                   len(source['specs']) == 12 and {(s['size'], s['variety'], s['state']) for s in source['specs']} ==
                   {(size, variety, state) for size in ('broad', 'narrow') for variety in (0, 1) for state in ('healthy', 'sick', 'dead')})
        slot = rom.defs['TREE_STUDY_PALETTE_SLOT']
        tiles = rom.array('tree_study_tiles')
        self.check('budget', 'compact review atlas fits BG tile limit',
                   len(tiles) == rom.defs['TREE_STUDY_TILE_COUNT']*32 and len(tiles)//32 <= 1024,
                   {'tiles': len(tiles)//32, 'limit': 1024})
        self.check('palette', 'shared legal 16-ink RGB555 bank is packed exactly',
                   rom.array('tree_study_palette') == struct.pack('<16H', *source['palette']) and slot == 11)
        self.check('native', 'native transparent tile zero is all zero nibbles', tiles[:32] == bytes(32))
        records = []
        for i, (spec, image) in enumerate(zip(source['specs'], source['images'])):
            ptr, tw, th, size, variety, state = rom.unpack('<I5B', rom.symbols['tree_study_frames']+i*12)
            width, height = image.size
            wanted = (width//8, height//8, int(spec['size']=='narrow'), spec['variety'], ('healthy','sick','dead').index(spec['state']))
            self.check('descriptor', spec['name']+' native dimensions and state/order metadata',
                       (tw, th, size, variety, state) == wanted and ptr == rom.symbols[f'tree_study_map_{i}'])
            entries = list(rom.unpack('<%dH' % (tw*th), ptr))
            pixels = decode_map(tiles, entries, width, height)
            expected = image.tobytes()
            self.check('native', spec['name']+' source index range and fixed root anchor',
                       set(expected) <= set(range(16)) and spec['transparent_index'] == 0 and spec['anchor'] == [width//2, 30])
            self.check('native', spec['name']+' every packed nibble/flip equals direct native art', pixels == expected)
            self.check('palette', spec['name']+' every subtile uses the shared tree bank', all(e >> 12 == slot for e in entries))
            records.append({**spec, 'pixel_sha256': SHA(expected), 'painted_pixels': sum(bool(x) for x in expected),
                            'painted_bounds': image.getbbox(), 'map_entries': len(entries)})
        for size in ('broad','narrow'):
            for variety in (0,1):
                images = [source['images'][i].tobytes() for i, s in enumerate(source['specs']) if (s['size'],s['variety']) == (size,variety)]
                self.check('state', f'{size}{variety} healthy/sick/dead silhouettes differ beyond hue',
                           len({masks(x) for x in images}) == 3)
        ts = rom.tileset('forest')
        floor_maps = struct.unpack('<12H', rom.array('tree_study_floor'))
        floor_ids = (struct.unpack('<3H', rom.array('TREE_STUDY_FLOOR_MT'))
                     if 'TREE_STUDY_FLOOR_MT' in rom.sections else
                     tuple(rom.defs['MT_'+n] for n in ('MOSS0','PATH','BLIGHT_FLOOR')))
        # The engine uses its own fixed floor IDs; the duplicate exported ID
        # table may be legitimately discarded by --gc-sections. Pixel/bank
        # payload and actual runtime floor-ID checks remain independent.
        for n, name in enumerate(('MOSS0','PATH','BLIGHT_FLOOR')):
            expected_id = rom.defs['MT_'+name]
            native_entries = struct.unpack_from('<4H', ts['map'], expected_id*8)
            entries = floor_maps[n*4:n*4+4]
            native_pixels = decode_map(ts['tiles'], native_entries, 16, 16)
            packed_pixels = decode_map(tiles, entries, 16, 16)
            self.check('floor', name+' compact atlas retains original native floor pixels/banks',
                       floor_ids[n] == expected_id and native_pixels == packed_pixels and
                       [e>>12 for e in native_entries] == [e>>12 for e in entries])
        return records

    def protected(self):
        rom, base = self.rom, self.base
        self.check('scope', 'metatile and normal sprite identifiers unchanged', rom.tile_ids == base.tile_ids and rom.sheet_ids == base.sheet_ids)
        for area in ('forest','sewer','myst'):
            a, b = base.tileset(area), rom.tileset(area)
            self.check('scope', area+' complete normal tile/map/palette/animation payload unchanged', a == b)
        for name in base.sheet_ids:
            self.check('scope', name+' complete normal OBJ descriptor and pixel payload unchanged', rom.sheet(name) == base.sheet(name))
        excluded = {'tilesets','sheets','room_defs','canopy_prefabs','tile_anims_forest','tile_anims_sewer','tile_anims_myst'}
        checked, changed = 0, []
        for name in base.sections:
            if name in excluded:
                continue
            checked += 1
            if name not in rom.sections or base.array(name) != rom.array(name):
                changed.append(name)
        self.check('scope', 'all shared immutable artwork/UI/title/fonts/palettes/metadata arrays unchanged',
                   not changed, {'arrays': checked, 'changes': changed})
        for role in range(9):
            a = base.unpack('<I4B', base.symbols['canopy_prefabs']+role*8)
            b = rom.unpack('<I4B', rom.symbols['canopy_prefabs']+role*8)
            self.check('canopy', f'normal canopy descriptor{role} retains exact map and metadata',
                       a[1:] == b[1:] and a[0] == base.symbols[f'canopy_prefab_{role}_map'] and b[0] == rom.symbols[f'canopy_prefab_{role}_map'] and
                       base.read(a[0],a[1]*a[2]*8) == rom.read(b[0],b[1]*b[2]*8))
        return {'immutable_arrays': checked, 'changed_arrays': changed}

    def source_gallery(self):
        if not self.args.source_gallery:
            return {'status':'not_requested'}
        from PIL import Image
        root = Path(self.args.source_gallery)
        manifest = json.loads((root/'source-manifest.json').read_text())
        source = json.loads((root/'source-art.json').read_text())
        native = json.loads((root/'native-manifest.json').read_text())
        freeze = json.loads((self.root/'v30/freeze.json').read_text())
        self.check('source_provenance', 'native catalog binds profile30 frozen ROM/source/helper',
                   manifest['profile'] == 30 and manifest['source_commit'] == freeze['source_commit'] and
                   manifest['rom_sha256'] == SHA(self.rom.rom) and manifest['gallery_tool_sha256'] ==
                   SHA((GAME/'tools/forest_tree_gallery.py').read_bytes()))
        for name, digest in manifest['source_input_sha256'].items():
            self.check('source_provenance', name+' current source bytes', SHA((GAME/name).read_bytes()) == digest)
        for name, record in manifest['files'].items():
            path = root/name
            self.check('source_files', name+' literal file hash and size',
                       path.is_file() and path.stat().st_size == record['bytes'] and SHA(path.read_bytes()) == record['sha256'])
        self.check('source_coverage', 'twelve exact native source entries, one palette bank',
                   len(native['entries']) == manifest['native_images'] == len(source['entries']) == 12 and
                   manifest['palette_banks'] == 1 and rgb555(source['palette']) == self.source['palette'])
        images = {spec['name']: image for spec, image in zip(self.source['specs'], self.source['images'])}
        entries = {entry['name']:entry for entry in native['entries']}
        for entry in source['entries']:
            image = images[entry['name']]
            self.check('source_native', entry['name']+' exported source nibbles/anchor exactly direct art',
                       bytes(entry['indices']) == image.tobytes() and entry['anchor'] == [image.width//2,30])
        def rgba(image):
            out = Image.new('RGBA', image.size)
            palette = self.source['palette']
            out.putdata([((palette[v]&31)<<3, ((palette[v]>>5)&31)<<3, ((palette[v]>>10)&31)<<3,
                         255 if v else 0) for v in image.tobytes()])
            return out
        for name, image in images.items():
            entry = entries[name]
            indexed = Image.open(root/entry['native_indexed'])
            actual = Image.open(root/entry['native_rgba']).convert('RGBA')
            expected = rgba(image)
            self.check('source_native', name+' original P16 pixels and transparent index',
                       indexed.mode == 'P' and indexed.size == image.size and indexed.tobytes() == image.tobytes() and
                       indexed.info.get('transparency') == 0 and entry['index_sha256'] == SHA(image.tobytes()))
            self.check('source_native', name+' literal canonical RGB555 and binary-alpha PNG',
                       actual.size == image.size and actual.tobytes() == expected.tobytes())
        panels = 0
        for board in native['boards']:
            path = root/board['path']; picture = Image.open(path).convert('RGB')
            self.check('source_panels', board['path']+' declared file hash', SHA(path.read_bytes()) == board['sha256'])
            for panel in board['panels']:
                image = images[panel['name']]; expected = rgba(image)
                x,y,width,height = panel['native_rect']; crop = picture.crop((x,y,x+width,y+height))
                # Source preview transparency intentionally composites over floor.
                # Verify every opaque native pixel independently; those pixels
                # cannot be manufactured by the selected background.
                pairs = zip(image.tobytes(), expected.getdata(), crop.getdata())
                valid = (width,height) == image.size and all(
                    not ink or actual == ((224,216,176) if panel.get('kind') == 'silhouette diagnostic' else wanted[:3])
                    for ink,wanted,actual in pairs)
                self.check('source_panels', panel['name']+' '+board['path']+' native opaque pixels exact', valid)
                panels += 1
        return {'native_images':len(images),'hashed_files':len(manifest['files']), 'source_panels':panels,
                'manifest_sha256':SHA((root/'source-manifest.json').read_bytes()),
                'limits':'Source previews and silhouette/value diagnostics are not mGBA framebuffers.'}

    def runtime(self):
        if not self.args.runtime:
            return {'status':'not_requested'}
        from PIL import Image, ImageSequence
        from sewer_concept_audit import decode_sprite
        from fractions import Fraction
        import subprocess
        base = Path(self.args.runtime)
        path = base if base.is_file() else base/'capture.json'
        if not path.exists():
            path = base/'v30/capture.json'
        base = path.parent
        report = json.loads(path.read_text())
        freeze = json.loads((self.root/'v30/freeze.json').read_text())
        self.check('runtime_provenance', 'eight final source-bound diagnostic-grove cases',
                   report['complete'] and not report.get('unfrozen_pilot') and report['forest_variant'] == 30 and
                   report['source_commit'] == freeze['source_commit'] and report['rom_sha256'] == SHA(self.rom.rom) and
                   report['passed'] == report['total'] and not report['failures'] and len(report['captures']) == 8)
        self.check('runtime_provenance', 'held current capture helper',
                   report['capture_tool_sha256'] == SHA((GAME/'tools/forest_tree_review.py').read_bytes()))
        tiles = self.rom.array('tree_study_tiles')
        pal = self.source['palette']
        maps = []
        descriptors = []
        for i in range(12):
            p,w,h,size,variety,state = self.rom.unpack('<I5B', self.rom.symbols['tree_study_frames']+i*12)
            values = list(self.rom.unpack('<%dH'%(w*h),p));maps.append(values)
            descriptors.append({'map':values,'w8':w,'h8':h,'size':size,'variety':variety,'state':state})
        floors = struct.unpack('<12H',self.rom.array('tree_study_floor'))
        hero_info, hero_data = self.rom.sheet('hero')
        stride = hero_info['frame_tiles']*32
        poses = {SHA(hero_data[i:i+stride]) for i in range(0,len(hero_data),stride)}
        obj = self.rom.array('pal_obj')
        totals = {'contexts':0,'observed_frames':0,'movies':0,'exact_sampled_GIFs':0}
        minimum = minimum_component = 100000
        layout_sets = {}
        for row in report['captures']:
            name = row['name'];hw = row['initial_hardware'];info = hw['info'];placements = hw['placements']
            request = row['request'];floor = request%3;layout = request//3
            self.check('runtime_fixture', name+' explicit catalog/repeated diagnostic layout and native viewport',
                       info[:4] == [1,request,layout,floor] and info[4] == 12 and info[5] == len(tiles)//32 and info[6] == 11 and
                       info[7] == self.rom.defs['MT_'+('MOSS0','PATH','BLIGHT_FLOOR')[floor]] and info[10:12] == [1,12] and
                       hw['room_pixels'] == [240,160] and hw['camera'] == [0,0] and 'diagnostic' in row['fixture'].lower())
            self.check('runtime_maps', name+' live descriptor words equal frozen ROM maps', hw['frames'] == descriptors)
            expected1 = [0]*600;expected2 = [];roots = set();claimed = set();fits = True
            for placement in placements:
                frame = placement['frame'];f = descriptors[frame]
                x,y,w,h = (placement[k] for k in ('x','y','w','h'))
                fits &= x%8 == y%8 == 0 and w == f['w8']*8 and h == f['h8']*8 and 0 <= x <= 240-w and 0 <= y <= 160-h
                cells = {(x//8+xx,y//8+yy) for yy in range(f['h8']) for xx in range(f['w8'])}
                fits &= not bool(cells&claimed);claimed |= cells
                for yy in range(f['h8']):
                    for xx in range(f['w8']):expected1[(y//8+yy)*30+x//8+xx] = maps[frame][yy*f['w8']+xx]
                root = ((x+w//2-8)//8,(y+h-8)//8,2,1)
                fits &= tuple(placement[k] for k in ('root_x8','root_y8','root_w8','root_h8')) == root and placement['anchor_y'] == 30
                roots.update((root[0]+xx,root[1]+yy) for yy in range(root[3]) for xx in range(root[2]))
            floor_map = floors[floor*4:floor*4+4]
            expected2 = [floor_map[(y&1)*2+(x&1)] for y in range(20) for x in range(30)]
            self.check('runtime_geometry', name+' native placements fit, do not overlap and retain separate root footprints', fits)
            self.check('runtime_maps', name+' every raw BG1/BG2 entry independently matches native tree/floor maps',
                       hw['BG1_entries'] == expected1 and hw['BG2_entries'] == expected2)
            self.check('runtime_collision', name+' actual root grid exactly matches declared shallow footprints',
                       {tuple(p) for p in hw['actual_roots8']} == roots)
            self.check('runtime_palette', name+' actual tree bank and resident atlas equal packed native payloads',
                       hw['tree_palette'] == pal and hw['atlas_VRAM_sha256'] == SHA(tiles) and hw['gAnimTiles'] == 0)
            self.check('runtime_stability', name+' complete raw scene snapshot stays unchanged through ordinary play',
                       SHA(json.dumps(hw,sort_keys=True).encode()) == row['final_hardware_sha256'])
            key = tuple((p['frame'],p['x'],p['y'],p['w'],p['h']) for p in placements)
            if layout in layout_sets:
                self.check('runtime_fixture',name+' same diagnostic planting on different floor',key == layout_sets[layout])
            else:layout_sets[layout] = key
            if not layout:self.check('runtime_coverage',name+' all twelve native trees placed', {p['frame'] for p in placements} == set(range(12)))
            else:self.check('runtime_coverage',name+' repeated kit includes all three states',len({p['frame'] for p in placements})<12 and {descriptors[p['frame']]['state'] for p in placements} == {0,1,2})
            pngs = {p['tick']:base/p['path'] for p in row['native_frames']}
            # Literal first-frame art and alpha contact proof, independent of
            # the reader's expected arrays. Exclude only the current player
            # canvas/HUD/minimap; catalog trees remain fully inspectable.
            first = Image.open(base/row['image']).convert('RGB')
            body_oam = row['observations'][0]['hero_OAM']
            bw,bh = row['observations'][0]['body_canvas']
            floor_colors = struct.unpack('<%dH'%(len(self.rom.tileset('forest')['palettes'])//2),self.rom.tileset('forest')['palettes'])
            pixel_errors = [];opaque_checked = alpha_checked = 0
            def scene_floor_color(px,py):
                e = expected2[(py//8)*30+px//8];block = decode_8x8(tiles[(e&1023)*32:(e&1023)*32+32])
                xx,yy = px&7,py&7
                if e&0x400:xx=7-xx
                if e&0x800:yy=7-yy
                return floor_colors[(e>>12)*16+block[yy*8+xx]]
            for placement in placements:
                index = placement['frame'];src = self.source['images'][index];values = src.tobytes()
                for yy in range(src.height):
                    for xx in range(src.width):
                        px,py = placement['x']+xx,placement['y']+yy
                        if py<12 or (px>=220 and py>=140) or (body_oam['x']<=px<body_oam['x']+bw and body_oam['y']<=py<body_oam['y']+bh):continue
                        ink = values[yy*src.width+xx]
                        value = pal[ink] if ink else scene_floor_color(px,py)
                        rgb = tuple((q<<3)|(q>>2) for q in (value&31,(value>>5)&31,(value>>10)&31))
                        if first.getpixel((px,py)) != rgb:pixel_errors.append([px,py,ink])
                        if ink:opaque_checked+=1
                        else:alpha_checked+=1
            self.check('runtime_tree_pixels',name+' literal tree colors and alpha reveal exact native floor in framebuffer',
                       not pixel_errors and opaque_checked>0 and alpha_checked>0,
                       {'opaque_pixels':opaque_checked,'transparent_contact_pixels':alpha_checked,'mismatches':pixel_errors[:16]})
            observation_errors = [];png_errors = [];count = 0
            def tree_ink(px,py):
                e = expected1[(py//8)*30+px//8];data = decode_8x8(tiles[(e&1023)*32:(e&1023)*32+32])
                xx,yy = px&7,py&7
                if e&0x400:xx=7-xx
                if e&0x800:yy=7-yy
                return data[yy*8+xx]
            for tick,o in enumerate(row['observations']):
                valid = o.get('body_found') and o.get('scanline0') == 0 and o.get('scanline160') == 160 and o.get('video_frame') == o.get('end_video_frame') and o['irq_delta'] == o['update_delta'] == 1
                raw = bytes.fromhex(o['body_vram_hex']);w,h = o['body_canvas'];body = decode_sprite(raw,w,h);hero = o['hero_OAM'];colors = o['body_palette']
                valid &= SHA(raw) == o['body_vram_sha256'] and SHA(raw) in poses and (w,h) == (hero_info['width'],hero_info['height'])
                valid &= struct.pack('<16H',*colors) == obj[hero['pal']*32:(hero['pal']+1)*32]
                guard = o.get('guard_OAM');mask = decode_sprite(bytes.fromhex(o['guard_vram_hex']),w,h) if guard else None
                if guard:
                    valid &= all(guard[k] == hero[k] for k in ('x','y','pal','shape','size','flip')) and guard['priority'] == 1
                    valid &= all(not ink or ink == body[i] for i,ink in enumerate(mask))
                expected = [];covered = 0;bg_priority = o['BG1_control']&3
                for yy in range(h):
                    for xx in range(w):
                        sx = w-1-xx if hero['flip'] else xx;i = body[yy*w+sx]
                        if not i:continue
                        px,py = hero['x']+xx,hero['y']+yy
                        if not(0 <= px < 240 and 12 <= py < 160):continue
                        obscured = hero['priority'] > bg_priority and tree_ink(px,py) != 0
                        covered += int(obscured)
                        if obscured and not(mask and mask[yy*w+sx] == i):continue
                        color = colors[i];parts = (color&31,(color>>5)&31,(color>>10)&31)
                        if max(parts)<5 or sum(parts)<10:continue
                        expected.append((xx,yy,px,py,tuple((v<<3)|(v>>2) for v in parts)))
                valid &= covered == o['body_pixels_behind_tree'] and 0 < o['exact_visible_pixels'] <= len(expected) and o['largest_visible_component'] >= 4
                if not valid:observation_errors.append(tick)
                minimum = min(minimum,o['exact_visible_pixels']);minimum_component = min(minimum_component,o['largest_visible_component'])
                if tick in pngs:
                    image = Image.open(pngs[tick]).convert('RGB')
                    hits = {(xx,yy) for xx,yy,x,y,color in expected if image.getpixel((x,y)) == color}
                    left = set(hits);best = 0
                    while left:
                        todo = [left.pop()];n = 0
                        while todo:
                            x,y = todo.pop();n += 1
                            for near in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                                if near in left:left.remove(near);todo.append(near)
                        best = max(best,n)
                    if image.size != (240,160) or len(hits) != o['exact_visible_pixels'] or best != o['largest_visible_component']:png_errors.append(tick)
                count += 1
            self.check('runtime_body',name+' raw native body/guard/BG1/palette/scanout/cadence proof at every recorded frame',not observation_errors,observation_errors)
            self.check('runtime_pixels',name+' native PNG keyframes independently match exact body colors/components',not png_errors,png_errors)
            states = row['player_states']
            if row.get('video'):
                self.check('runtime_depth',name+' behind/front priorities and root push are exercised',
                           {o['priority'] for o in row['observations']} >= {1,2} and any(s['collision']&1 for s in states[72:]))
                data = json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_read_frames','-of','json',str(base/row['video'])],text=True))['streams'][0]
                self.check('runtime_media',name+' full native movie rate/frame count',
                           int(data['width']) == 240 and int(data['height']) == 160 and Fraction(data['r_frame_rate']) == Fraction(262144,4389) and int(data['nb_read_frames']) == row['frames'])
                with Image.open(base/row['gif']) as gif:
                    frames = [(f.convert('RGB').copy(),f.info['duration']) for f in ImageSequence.Iterator(gif)]
                gif_meta = row['gif_metadata']
                self.check('runtime_media',name+' exact sampled-color GIF timing declared and preserved',
                           len(frames) == gif_meta['encoded_frames'] and [ms for im,ms in frames] == gif_meta['encoded_holds_ms'] and
                           sum(ms for im,ms in frames) == gif_meta['sampled_frames']*gif_meta['sample_hold_ms'] and not gif_meta['engine_timing_claim'])
                # First GIF sample is the literal first native keyframe.
                self.check('runtime_media',name+' first sampled GIF is literal native RGB',frames[0][0].tobytes() == Image.open(pngs[0]).convert('RGB').tobytes())
                totals['movies'] += 1;totals['exact_sampled_GIFs'] += 1
            totals['contexts'] += 1;totals['observed_frames'] += count
        self.check('runtime_coverage','six floor/layout contexts plus two ordinary tree-depth clips',totals['contexts'] == 8 and totals['observed_frames'] == 352 and totals['movies'] == totals['exact_sampled_GIFs'] == 2)
        return {**totals,'minimum_visible_pixels':minimum,'minimum_connected_component':minimum_component,
                'report_sha256':SHA(path.read_bytes()),'limits':'Authored diagnostic grove; finite ordinary-input and native keyframe proof, not naturally generated forest adoption or universal playtesting.'}

    def historical(self):
        previous = Path(self.args.previous)
        rows = []
        for n in range(30):
            old, new = previous/f'v{n}/bartgame.gba', self.root/f'v{n}/bartgame.gba'
            same = old.is_file() and new.is_file() and old.read_bytes() == new.read_bytes()
            self.check('historical', f'complete old profile{n} ROM byte-identical', same)
            rows.append({'profile':n,'byte_identical':same,'current_sha256':SHA(new.read_bytes()) if new.exists() else None,
                         'previous_sha256':SHA(old.read_bytes()) if old.exists() else None})
        return rows

    def run(self):
        commit = self.provenance()
        native = self.native()
        scope = self.protected()
        historical = self.historical()
        gallery = self.source_gallery()
        runtime = self.runtime()
        result = {'method': __doc__.strip(), 'source_commit':commit,'auditor_sha256':SHA(Path(__file__).read_bytes()),
                  'native_trees':native,'protected_scope':scope,'historical_controls':historical,'source_gallery':gallery,'runtime':runtime,
                  'passed':sum(r['passed'] for r in self.checks),'total':len(self.checks),
                  'failures':[r for r in self.checks if not r['passed']],'checks':self.checks,
                  'limits':'Focused native/packed/source and explicitly diagnostic-grove proof, not an aesthetic verdict, natural forest adoption or universal gameplay guarantee.'}
        Path(self.args.out).parent.mkdir(parents=True,exist_ok=True)
        Path(self.args.out).write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ('source_commit','passed','total','failures')},indent=2))
        return int(bool(result['failures']))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frozen',required=True)
    p.add_argument('--previous',default='/workspace/setup/forest-canopy-emerald/frozen')
    p.add_argument('--runtime')
    p.add_argument('--source-gallery')
    p.add_argument('--out',required=True)
    return Audit(p.parse_args()).run()


if __name__=='__main__':
    raise SystemExit(main())
