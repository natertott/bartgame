#!/usr/bin/env python3
"""Independently verify the adopted enemy mix and native broken Heart ROM.

The selected five bodies/weapon/seed must match the previously reviewed frozen
ROMs byte for byte. New Heart frames are decoded from actual 4bpp ROM nibbles
against the direct native painter, without importing the asset packer. Scope,
palette/VRAM budgets, frozen provenance and real gameplay traces are separate
checks. Historical assembler exports are checked only for preservation and are
not used as expected pixels for the selected/new native encoding audit.
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

from PIL import Image, ImageDraw, ImageFont
from sewer_concept_audit import NativeRom, decode_sprite
from enemy_study_audit import Audit, compare_trajectories

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = 'fef0334c27966a2e10700b5eacf8c90f8a067736'
SELECTED = {'beetle': 9, 'bat': 9, 'spitter': 5, 'slime': 9,
            'knight': 6, 'ksword': 6, 'proj': 5}
TITLES = {'beetle': 'Coin Toad', 'bat': 'Quill Moth',
          'spitter': 'Trumpet bellflower', 'slime': 'Pear bladder',
          'knight': 'Moth Confessor'}
HEART_FRAMES = ('pulse1', 'pulse2', 'hurt', 'charge1', 'charge2',
                'release1', 'release2', 'spawn1', 'spawn2',
                'lunge1', 'lunge2', 'dying1', 'dying2')
CHANGED = {*SELECTED, 'boss'}
SHA = lambda data: hashlib.sha256(data).hexdigest()


def expected_pixels():
    """Direct native authoring only: no production sprite assembler/packer."""
    sys.path.insert(0, str(ROOT / 'art'))
    import enemy_studies_small as small
    import enemy_studies_soft as soft
    import enemy_studies_heavy as heavy
    import enemy_studies_palette as palette
    import enemy_heart
    contract = {r['name']: r for r in json.loads(
        (ROOT / 'art/reboot_contracts.json').read_text())['sheets']}
    rows = {}
    for family, chosen in SELECTED.items():
        module = small if family in ('beetle', 'bat') else soft if family in ('spitter', 'slime', 'proj') else heavy
        names = ['seed'] if family == 'proj' else [*contract[family]['frames'],
                    *getattr(module, 'EXTRA_FRAMES', {}).get(family, ())]
        frames = {}
        for name in names:
            image = module.frame(family, chosen, name)
            assert image.mode == 'P' and set(image.tobytes()) <= set(range(16)), (family, name)
            frames[name] = {'size': list(image.size), 'pixels': image.tobytes().hex()}
        if family in TITLES:
            assert module.CONCEPTS[family][chosen-1] == TITLES[family], (family, chosen, module.CONCEPTS[family])
        colors = palette.colors() if family in ('beetle', 'bat', 'slime') else None
        rgb555 = [sum((int(c[i:i+2],16)//8) << (j*5)
                      for j, i in enumerate((1,3,5))) for c in colors] if colors else None
        rows[family] = {'frames': frames, 'enemy_palette': rgb555}
    frames = {}
    for name in HEART_FRAMES:
        image = enemy_heart.frame(name)
        assert image.mode == 'P' and image.size == (32,64)
        assert set(image.tobytes()) <= set(range(16)) and image.getbbox(), name
        frames[name] = {'size': [32,64], 'pixels': image.tobytes().hex()}
    rows['boss'] = {'frames': frames, 'enemy_palette': None}
    return rows


def historical_export():
    """Current pre-packing integration, used solely for old-profile retention."""
    sys.path.insert(0, str(ROOT / 'art'))
    import sprites
    import palettes
    result = {'sheets': {}, 'palettes': []}
    for sheet in sprites.SHEETS:
        frames = {name: bytes(int(v,16) if v != '.' else 0
                       for row in pixels for v in row).hex()
                  for name, pixels in sheet['frames'].items()}
        result['sheets'][sheet['name']] = {
            'canvas': [sheet['w'], sheet['h']], 'pal': sheet['pal'], 'frames': frames,
            'frame_pal': sheet.get('frame_pal')}
    for name, colors in palettes.OBJ_PALETTES:
        native = [sum((int(c[i:i+2],16)//8) << (j*5)
                      for j, i in enumerate((1,3,5))) for c in colors]
        result['palettes'].append([name, native])
    print(json.dumps(result, separators=(',', ':')))


class SelectedAudit(Audit):
    def __init__(self, args):
        args.work = str(Path(args.frozen).parent)
        args.baseline = str(Path(args.historical) / 'v1')
        args.reference = PREVIOUS
        super().__init__(args)
        self.directory = Path(args.frozen)
        self.rom = NativeRom(self.directory)
        self.freeze = json.loads((self.directory / 'freeze.json').read_text())
        self.source_cache[11] = expected_pixels()
        self.selected_frames = []

    def exact_choices(self):
        for name, chosen in SELECTED.items():
            old = NativeRom(Path(self.args.historical) / f'v{chosen}')
            meta, raw = self.rom.sheet(name)
            before, expected = old.sheet(name)
            self.check(11, 'selection', name + ' chosen variant ' + str(chosen) + ' metadata exact', meta == before)
            if name == 'proj':
                fid = self.rom.defs['F_PROJ_SEED']; stride = meta['frame_tiles']*32
                self.equal(11, 'selection', 'Bellflower seed5 exact',
                           expected[fid*stride:(fid+1)*stride], raw[fid*stride:(fid+1)*stride])
            else:
                self.equal(11, 'selection', name + ' complete selected sheet exact', expected, raw)
            palette = self.rom.array('pal_obj')[meta['pal']*32:(meta['pal']+1)*32]
            self.equal(11, 'selection', name + ' selected palette exact',
                       old.array('pal_obj')[before['pal']*32:(before['pal']+1)*32], palette)
            self.selected_frames.append({'sheet': name, 'selected_variant': chosen,
                'frame_count': len(self.source_cache[11][name]['frames']),
                'reference_rom_sha256': SHA(old.rom), 'palette_slot': meta['pal']})

    def complete_preservation(self):
        for name in self.base.sheet_ids:
            if name not in CHANGED:
                a, raw = self.base.sheet(name); b, current = self.rom.sheet(name)
                self.check(11, 'complete_preservation', name + ' complete metadata exact', a == b)
                self.equal(11, 'complete_preservation', name + ' complete bytes exact', raw, current)
        # These comparisons intentionally include every UI/palette array,
        # unlike the older broad redesign audit's permitted UI exceptions.
        self.equal(11, 'complete_preservation', 'all BG palette words exact', self.base.array('pal_bg'), self.rom.array('pal_bg'))
        self.equal(11, 'complete_preservation', 'all OBJ palette words exact', self.base.array('pal_obj'), self.rom.array('pal_obj'))
        skipped = {'tilesets', 'sheets', 'room_defs', 'pal_bg', 'pal_obj'}
        for name in self.base.sections:
            if name in skipped or name.startswith(('sheet_', 'tileset_', 'tile_anim')):
                continue
            self.check(11, 'complete_preservation', name + ' retained array exists', name in self.rom.sections)
            if name in self.rom.sections:
                self.equal(11, 'complete_preservation', name + ' retained bytes', self.base.array(name), self.rom.array(name))
        # Presentation and gameplay C are both preserved, not just selected
        # function tokens. New choices live entirely in native art integration.
        for path in sorted((ROOT/'src').glob('*')):
            if path.suffix not in ('.c', '.h', '.s', '.inc'):
                continue
            rel = str(path.relative_to(ROOT))
            before = subprocess.check_output(['git', 'show', PREVIOUS+':bartgame/'+rel], cwd=ROOT)
            self.equal('source', 'complete_preservation', rel + ' exact code', before, path.read_bytes())

    def historical(self):
        rows = []
        for variant in range(11):
            old = NativeRom(Path(self.args.historical) / f'v{variant}')
            frozen = json.loads((old.directory/'freeze.json').read_text())
            self.check(variant, 'historical', 'published historical ROM unchanged', SHA(old.rom) == frozen['rom_sha256'])
            code = 'import selected_enemy_audit as t; t.historical_export()'
            env = {**os.environ, 'BART_ENEMY': str(variant), 'BART_UI': '6',
                   'BART_MENU': '1', 'BART_SEWER': '9', 'BART_SWING': '3'}
            exported = json.loads(subprocess.check_output([sys.executable, '-c', code], cwd=ROOT/'tools', env=env, text=True))
            for name, sheet in exported['sheets'].items():
                meta, raw = old.sheet(name)
                self.check(variant, 'historical', name + ' canvas preserved', sheet['canvas'] == [meta['width'], meta['height']])
                self.check(variant, 'historical', name + ' frame count preserved', len(sheet['frames']) == meta['tile_count']//meta['frame_tiles'])
                self.check(variant, 'historical', name + ' palette preserved', old.defs['PAL_OBJ_'+sheet['pal'].upper()] == meta['pal'])
                # The linker removes unused generated palette arrays (for
                # example sword_frame_pal). Only linked runtime tables have
                # physical payloads; source-only metadata is not ROM data.
                if sheet['frame_pal'] is not None and name+'_frame_pal' in old.sections:
                    routes=bytes(old.defs['PAL_OBJ_'+sheet['frame_pal'][frame].upper()]
                                 for frame in sheet['frames'])
                    self.equal(variant, 'historical', name+' per-frame material routing preserved',
                               old.array(name+'_frame_pal'), routes)
                for i, (frame, pixels) in enumerate(sheet['frames'].items()):
                    self.check(variant, 'historical', name+'.'+frame+' ID preserved', old.defs['F_'+name.upper()+'_'+frame.upper()] == i)
                    stride = meta['frame_tiles']*32
                    self.equal(variant, 'historical', name+'.'+frame+' native pixels preserved',
                               decode_sprite(raw[i*stride:(i+1)*stride], meta['width'], meta['height']), bytes.fromhex(pixels))
            native = b''.join(struct.pack('<16H', *colors) for _, colors in exported['palettes'])
            self.equal(variant, 'historical', 'all historical OBJ palette exports preserved', old.array('pal_obj'), native)
            rows.append({'variant': variant, 'rom_sha256': SHA(old.rom), 'native_frames': sum(len(s['frames']) for s in exported['sheets'].values())})
        return rows

    def heart_atlas(self, out):
        meta, raw = self.rom.sheet('boss'); stride = meta['frame_tiles']*32
        palette = struct.unpack('<16H', self.rom.array('pal_obj')[meta['pal']*32:(meta['pal']+1)*32])
        colors = [tuple(((word >> shift)&31)*8 for shift in (0,5,10)) for word in palette]
        atlas = Image.new('RGB', (720,740), '#101820'); draw = ImageDraw.Draw(atlas)
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
        draw.fontmode = '1'; draw.text((5,5), 'All 13 Heart poses / ROM-decoded native art, not emulator output', font=font, fill='#e8d098')
        for i, name in enumerate(HEART_FRAMES):
            fid = self.rom.defs['F_BOSS_'+name.upper()]
            pixels = decode_sprite(raw[fid*stride:(fid+1)*stride], 32,64)
            image = Image.new('RGBA', (32,64)); image.putdata([(*colors[value],255) if value else (0,0,0,0) for value in pixels])
            x = i%5*144; y = 28+i//5*236
            big=image.resize((96,192), Image.Resampling.NEAREST); atlas.paste(big,(x+4,y),big)
            atlas.paste(image,(x+108,y+128),image)
            draw.text((x+4,y+199),name,font=font,fill='#e8d098')
        atlas.save(out)

    def visible_heart_poses(self, directory, capture):
        """Read actual captured RGB against frozen-ROM pose pixels and OAM.

        A stable repeated selection avoids the declared one-VBlank stream
        latency. Shadows/player/foreground may cover a few pixels; require a
        clearly visible body for every pose instead of trusting pose counters.
        """
        meta, raw = self.rom.sheet('boss'); stride=meta['frame_tiles']*32
        words=struct.unpack('<16H',self.rom.array('pal_obj')[meta['pal']*32:(meta['pal']+1)*32])
        colors=[tuple((((word>>shift)&31)<<3)|(((word>>shift)&31)>>2)
                      for shift in (0,5,10)) for word in words]
        by_id={self.rom.defs['F_BOSS_'+name.upper()]:name for name in HEART_FRAMES}
        pixels={fid:decode_sprite(raw[fid*stride:(fid+1)*stride],32,64) for fid in by_id}
        best={name:{'fraction':0.0} for name in HEART_FRAMES}
        for row in capture['captures']:
            if row['kind'] != 5:continue
            traces=row['trace']
            for tick,state in enumerate(traces):
                target=state.get('target'); previous=traces[tick-1].get('target') if tick else None
                if not target or not previous or target['presented_frame'] != previous['presented_frame']:
                    continue
                fid=target['presented_frame']
                if fid not in by_id or not state.get('target_hardware_oam'):continue
                obj=state['target_hardware_oam'][0]
                x0,y0=obj['x'],obj['y']
                if x0<0 or x0+32>240 or y0<12 or y0+64>160:continue
                p=Path(directory)/row['all_frames']/f'frame-{tick:03}.png'
                if not p.exists():continue
                image=Image.open(p).convert('RGB'); total=matches=0
                for y in range(64):
                    for x in range(32):
                        value=pixels[fid][y*32+(31-x if obj.get('flip') else x)]
                        if value:
                            total+=1;matches+=image.getpixel((x0+x,y0+y))==colors[value]
                fraction=matches/total if total else 0.0
                name=by_id[fid]
                if fraction>best[name]['fraction']:
                    best[name]={'fraction':fraction,'matches':matches,'opaque_pixels':total,
                                'capture':row['name'],'tick':tick,'image':str(p),'hardware_origin':[x0,y0]}
                if all(v['fraction']>=0.99 for v in best.values()):break
        for name,row in best.items():
            self.check(11,'runtime_pixels','Heart '+name+' has actual visible frozen-ROM body',
                       row['fraction']>=0.90,row)
        board=Image.new('RGB',(900,620),'#101820'); draw=ImageDraw.Draw(board)
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
        draw.fontmode='1';draw.text((5,5),'All 13 Heart poses / ACTUAL mGBA 80x80 crops at 2x nearest-neighbor',font=font,fill='#e8d098')
        rectangles=[]
        for i,name in enumerate(HEART_FRAMES):
            row=best[name]
            if not row.get('image'):continue
            image=Image.open(row['image']).convert('RGB');ox,oy=row['hardware_origin']
            left=max(0,min(160,ox-24));top=max(0,min(80,oy-8));bounds=[left,top,left+80,top+80]
            crop=image.crop(bounds).resize((160,160),Image.Resampling.NEAREST)
            x=i%5*180+5;y=28+i//5*196
            board.paste(crop,(x,y))
            draw.text((x,y+164),name+' / '+str(row['tick']),font=font,fill='#e8d098')
            rectangles.append({'pose':name,'source_image':row['image'],'source_sha256':SHA(Path(row['image']).read_bytes()),
                               'native_crop':bounds,'destination':[x,y,x+160,y+160]})
        board_path=Path(self.args.out).with_name('heart-actual-poses.png');board.save(board_path)
        return {'method':self.visible_heart_poses.__doc__.strip(),'poses':best,
                'minimum_required_opaque_pixel_match':0.90,
                'actual_pose_board':str(board_path),'unchanged_crop_rectangles':rectangles}

    def run(self):
        freeze = self.freeze; rom = self.rom
        self.check(11, 'provenance', 'native profile11 selected', rom.defs.get('BART_ENEMY_VARIANT') == 11)
        self.check(11, 'provenance', 'normal Makefile selects production11', bool(re.search(r'^BART_ENEMY\s*\?=\s*11\s*$', (ROOT/'Makefile').read_text(), re.M)))
        self.check(11, 'provenance', 'ROM frozen checksum', SHA(rom.rom) == freeze['rom_sha256'])
        for field in ('source_file_sha256', 'code_file_sha256'):
            self.check(11, 'provenance', field+' recorded', bool(freeze.get(field)))
            for name, digest in freeze.get(field, {}).items():
                self.check(11, 'provenance', name+' current hash', SHA((ROOT/name).read_bytes()) == digest)
                committed = subprocess.check_output(['git','show',freeze['source_commit']+':bartgame/'+name], cwd=ROOT)
                self.check(11, 'provenance', name+' committed hash', SHA(committed) == digest)
        self.code(); self.world(11,rom,11); self.native(11,rom,11); self.budget(11,rom,11)
        self.exact_choices(); self.complete_preservation()
        historical = self.historical() if not self.args.skip_historical else {'status': 'not_requested'}
        comparisons = {}
        if self.args.captures:
            path = Path(self.args.captures)/'capture.json'; capture = json.loads(path.read_text())
            self.check(11, 'runtime', 'capture frozen ROM hash', capture['rom_sha256'] == SHA(rom.rom))
            self.check(11, 'runtime', 'capture source commit', capture.get('source_commit') == freeze['source_commit'])
            self.check(11, 'runtime', 'all12 actual AI cases pass', capture.get('capture_count') == 12 and capture['passed'] == capture['total'] and not capture['failures'])
            comparisons['main'] = compare_trajectories(Path(self.args.historical)/'enemy-reviews/v1/capture.json', path)
            self.check(11, 'runtime', 'all12 positive gameplay trajectories exact', comparisons['main']['passed'] == comparisons['main']['total'] == 12, comparisons['main'])
            coverage = capture.get('pose_coverage', {})
            self.check(11, 'runtime', 'Heart pose coverage report recorded', bool(coverage))
            observed=set(coverage.get('boss',{}).get('actual_draw_selected_names',[]))
            self.check(11,'runtime','all13 Heart poses actually draw-selected',observed==set(HEART_FRAMES))
            comparisons['visible_heart_pixels']=self.visible_heart_poses(self.args.captures,capture)
        if self.args.clearing:
            path=Path(self.args.clearing)/'capture.json'; report=json.loads(path.read_text())
            self.check(11, 'runtime', 'clear-floor frozen ROM hash', report['rom_sha256'] == SHA(rom.rom))
            self.check(11, 'runtime', 'clear-floor checks pass', report['passed'] == report['total'] and not report['failures'])
            comparisons['clearing'] = compare_trajectories(Path(self.args.historical)/'pursuer-clearing/v1/capture.json', path)
            self.check(11, 'runtime', 'clear-floor gameplay trajectory exact', comparisons['clearing']['passed'] == comparisons['clearing']['total'] == 1, comparisons['clearing'])
        out=Path(self.args.out); out.parent.mkdir(parents=True,exist_ok=True)
        self.heart_atlas(out.with_name('heart-rom-native-atlas.png'))
        report={'method': __doc__, 'reference_commit': PREVIOUS, 'source_commit': freeze['source_commit'],
                'rom_sha256': SHA(rom.rom), 'auditor_sha256': SHA(Path(__file__).read_bytes()),
                'selected_assets': self.selected_frames, 'new_heart_frames': list(HEART_FRAMES),
                'native_selected_frame_count': sum(len(x['frames']) for x in self.source_cache[11].values()),
                'historical_profiles': historical, 'obj_budgets': self.budgets,
                'runtime_comparisons': comparisons, 'passed': sum(r['passed'] for r in self.rows),
                'total': len(self.rows), 'failures': [r for r in self.rows if not r['passed']], 'checks': self.rows,
                'limits': 'Native bytes, scope, budgets and gameplay contracts, not an aesthetic ranking. ROM-decoded art is separate from actual mGBA frames. Source pose completeness does not imply every pose was naturally observed.'}
        out.write_text(json.dumps(report,indent=2)+'\n')
        out.with_name(out.stem+'-summary.json').write_text(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2)+'\n')
        print('RESULT',report['passed'],'/',report['total'],flush=True)
        return int(bool(report['failures']))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen',required=True)
    parser.add_argument('--historical',default='/workspace/setup/appearance-enemy-studies')
    parser.add_argument('--captures')
    parser.add_argument('--clearing')
    parser.add_argument('--skip-historical',action='store_true')
    parser.add_argument('--out',default='/workspace/setup/selected-enemies-heart/audit.json')
    return SelectedAudit(parser.parse_args()).run()


if __name__=='__main__':raise SystemExit(main())
