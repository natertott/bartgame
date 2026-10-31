#!/usr/bin/env python3
"""Independent native enemy ROM, preserved-world and combat-contract audit.

Only source painter APIs provide expected native pixels. No asset builder,
4bpp packing helper, sprite dispatcher or deduplicator is imported. Frozen ROM
nibbles and relocated descriptors are decoded by the independent ROM reader.
The positive profiles share mechanics; source and runtime evidence are kept
separate from visual preference and from the older baseline's frame cost.
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

from sewer_concept_audit import NativeRom, decode_sprite

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()
FAMILIES = ('beetle', 'bat', 'spitter', 'slime', 'knight', 'boss')
CHANGED = set(FAMILIES) | {'ksword', 'proj'}
UI_SHEETS = {'huditems', 'uimarks', 'cursor'}
UI_ARRAYS = {'ui_tiles', 'hud_tiles', 'huditems_frame_pal'}
BG_SKINS = {'ui', 'menu', 'map', 'hud'}
OBJ_SKINS = {'ui', 'uikit'}
DEFAULT_REF = 'a9e09e5de3c185e6b7bc8293b2411e4bdc13e4fe'
SHAPES = {(8,8),(16,16),(32,32),(64,64),(16,8),(32,8),(32,16),(64,32),
          (8,16),(8,32),(16,32),(32,64)}


def source_export(variant):
    """Direct authoring functions, with no production sprite assembler."""
    sys.path.insert(0, str(ROOT / 'art'))
    import enemy_studies_small as small
    import enemy_studies_soft as soft
    import enemy_studies_heavy as heavy
    import enemy_studies_palette as palette
    result = {}
    contract = json.loads((ROOT / 'art/reboot_contracts.json').read_text())
    by_name = {r['name']: r for r in contract['sheets']}
    for family in (*FAMILIES, 'ksword', 'proj'):
        module = small if family in ('beetle','bat') else soft if family in ('spitter','slime','proj') else heavy
        base = ['seed'] if family == 'proj' else by_name[family]['frames']
        extra = list(getattr(module, 'EXTRA_FRAMES', {}).get(family, []))
        frames = {}
        for name in [*base, *extra]:
            image = module.frame(family, variant, name)
            assert image.mode == 'P' and all(0 <= x < 16 for x in image.tobytes()), (family, name)
            frames[name] = {'size': list(image.size), 'pixels': image.tobytes().hex()}
        colors = palette.colors() if family in ('beetle','bat','slime') else None
        native_colors = [sum((int(color[i:i+2],16)//8) << (j*5) for j,i in enumerate((1,3,5))) for color in colors] if colors else None
        result[family] = {'base': list(base), 'extra': extra, 'frames': frames, 'enemy_palette': native_colors}
    print(json.dumps(result, separators=(',', ':')))


def authoring(variant):
    code = f'import enemy_study_audit as e; e.source_export({variant})'
    env = {**os.environ, 'BART_ENEMY': str(variant), 'BART_SEWER': '9', 'BART_UI': '6'}
    return json.loads(subprocess.check_output([sys.executable, '-c', code], cwd=ROOT / 'tools', env=env, text=True))


def strip_comments(text):
    # String/character literals stay intact while comments disappear.
    pattern = r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|/\*.*?\*/|//[^\n]*'
    return re.sub(pattern, lambda m: m.group(1) or '', text, flags=re.S)


def tokens(text):
    return re.findall(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\w+|[^\w\s]', strip_comments(text))


def brace_part(text, start):
    clean = strip_comments(text)
    match = re.search(start, clean, re.S)
    if not match:
        raise ValueError('missing C declaration: ' + start)
    begin = clean.index('{', match.start())
    depth = 0
    for n in range(begin, len(clean)):
        depth += (clean[n] == '{') - (clean[n] == '}')
        if not depth:
            return clean[begin:n+1]
    raise ValueError('unclosed C declaration: ' + start)


def function(text, name):
    return brace_part(text, r'\b' + re.escape(name) + r'\s*\([^;{}]*\)\s*\{')


def git_source(ref, name):
    return subprocess.check_output(['git', 'show', ref + ':bartgame/' + name], cwd=ROOT, text=True)


def compare_trajectories(reference_path, candidate_path):
    """Independently compare canonical mechanics, excluding presentation clocks.

    No capture/harness module or mGBA binding is imported here. Global video
    phase, OAM, palette/tile residency and selected visual frame are excluded;
    position, AI state/timers, health, damage, projectiles and RNG are exact.
    """
    reference=json.loads(Path(reference_path).read_text())
    candidate=json.loads(Path(candidate_path).read_text())
    fields=('kind','type','state','timer','timer2','dir','facing','x_q16','y_q16',
            'z_q16','zvel_q16','speed','hp','iframes','knockback_timer','flags','damage','v')
    def actor(a):return {key:a[key] for key in fields} if a else None
    def canonical(t):
        return {'game_state':t['game_state'],'area':t['area'],'cell':t['cell'],
                'hero':actor(t['hero']),'hero_hp':t['hero_hp'],
                'target':actor(t['target']),'projectiles':t['projectiles'],
                'enemy_count':t['enemy_count'],'rng':t.get('rng')}
    old={row['name']:row for row in reference['captures']};rows=[]
    for row in candidate['captures']:
        before=old.get(row['name'])
        if before is None:
            rows.append({'name':row['name'],'passed':False,'reason':'reference capture missing'});continue
        a,b=[canonical(t) for t in before['trace']],[canonical(t) for t in row['trace']]
        bad=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),None)
        result={'name':row['name'],'passed':bad is None and len(a)==len(b),
                'reference_frames':len(a),'candidate_frames':len(b)}
        if bad is not None:result.update(first_divergence_tick=bad,reference=a[bad],candidate=b[bad])
        rows.append(result)
    return {'reference_rom_sha256':reference['rom_sha256'],
            'candidate_rom_sha256':candidate['rom_sha256'],
            'passed':sum(r['passed'] for r in rows),'total':len(rows),
            'method':compare_trajectories.__doc__.strip(),'captures':rows}


class Audit:
    def __init__(self, args):
        self.args = args
        self.work = Path(args.work)
        self.base = NativeRom(args.baseline)
        self.rows, self.variants, self.budgets = [], [], []
        self.source_cache = {}

    def check(self, variant, group, name, passed, detail=None):
        row = {'variant': variant, 'group': group, 'name': name, 'passed': bool(passed)}
        if detail is not None:
            row['detail'] = detail
        self.rows.append(row)
        if not passed:
            print('FAIL', variant, group, name, detail, flush=True)

    def equal(self, variant, group, name, expected, actual):
        self.check(variant, group, name, expected == actual, None if expected == actual else {
            'expected_sha256': SHA(expected), 'actual_sha256': SHA(actual),
            'expected_bytes': len(expected), 'actual_bytes': len(actual)})

    def world(self, v, rom, enemy):
        before = self.base
        self.check(v, 'identifiers', 'all metatile IDs unchanged', rom.tile_ids == before.tile_ids)
        self.check(v, 'identifiers', 'all sprite sheet IDs unchanged', rom.sheet_ids == before.sheet_ids)
        for area in ('forest', 'myst', 'sewer'):
            a, b = before.tileset(area), rom.tileset(area)
            for key in ('tile_count', 'palette_count'):
                self.check(v, 'world', area + '.' + key, a[key] == b[key], b[key])
            for key in ('tiles', 'map', 'palettes'):
                self.equal(v, 'world', area + '.' + key, a[key], b[key])
            self.check(v, 'world', area + ' animation data and clocks unchanged', a['animations'] == b['animations'])
            self.check(v, 'budget', area + ' <=1024 resident BG tiles', b['tile_count'] <= 1024, b['tile_count'])
        for name in before.sheet_ids:
            a, old = before.sheet(name)
            b, current = rom.sheet(name)
            self.check(v, 'sprite_contract', name + ' legal native hardware shape', (b['width'], b['height']) in SHAPES)
            expected = dict(a)
            if name in CHANGED and enemy:
                authored = self.source_cache[enemy][name]
                if name != 'proj':
                    expected['tile_count'] = b['frame_tiles'] * len(authored['frames'])
                if name in ('beetle','bat','slime'):
                    expected['pal'] = rom.defs['PAL_OBJ_ITEMS']
            self.check(v, 'sprite_contract', name + ' canvas/palette/shape and approved frame count', expected == b)
            for key, old_id in before.defs.items():
                if key.startswith('F_' + name.upper() + '_'):
                    self.check(v, 'frame_identity', key, rom.defs.get(key) == old_id)
            if name in UI_SHEETS:
                continue  # separately reviewed appearance options
            if not enemy or name not in CHANGED:
                self.equal(v, 'protected_sprite', name, old, current)
            elif name == 'proj':
                stride = a['frame_tiles'] * 32
                for frame in range(a['tile_count'] // a['frame_tiles']):
                    if frame != before.defs['F_PROJ_SEED']:
                        self.equal(v, 'protected_projectile', 'proj frame' + str(frame), old[frame*stride:(frame+1)*stride], current[frame*stride:(frame+1)*stride])
        skip = {'tilesets','sheets','room_defs','pal_bg','pal_obj'} | UI_ARRAYS
        for name in before.sections:
            if name in skip or name.startswith(('sheet_', 'tileset_', 'tile_anim')):
                continue
            self.check(v, 'protected_array', name + ' exists', name in rom.sections)
            if name in rom.sections:
                self.equal(v, 'protected_array', name, before.array(name), rom.array(name))
        # Relocated room pointers are compared through their resolved arrays.
        self.check(v, 'room', 'room count unchanged', before.defs['ROOM_COUNT'] == rom.defs['ROOM_COUNT'])
        contract = json.loads((ROOT / 'art/reboot_contracts.json').read_text())['rooms']
        for i, record in enumerate(contract):
            a = struct.unpack('<BB2xIIIB3x', before.array('room_defs')[i*20:(i+1)*20])
            b = struct.unpack('<BB2xIIIB3x', rom.array('room_defs')[i*20:(i+1)*20])
            self.check(v, 'room', record['name'] + ' physical dimensions/object count', (a[0],a[1],a[5]) == (b[0],b[1],b[5]))
            for index, field in ((2,'ground'),(3,'overlay'),(4,'objects')):
                symbol = 'room_' + record['name'] + '_' + field
                self.check(v, 'room', symbol + ' resolved target', b[index] == rom.symbols.get(symbol, 0))
        for array, prefix, allowed in [('pal_bg','PAL_BG_',BG_SKINS), ('pal_obj','PAL_OBJ_',OBJ_SKINS)]:
            count = before.defs['PAL_BG_COUNT' if array == 'pal_bg' else 'PAL_OBJ_COUNT']
            excluded = {before.defs[prefix + n.upper()] for n in allowed}
            if enemy and array == 'pal_obj':excluded.add(before.defs['PAL_OBJ_ITEMS'])
            for bank in range(count):
                if bank not in excluded:
                    self.equal(v, 'protected_palette', array + str(bank), before.array(array)[bank*32:(bank+1)*32], rom.array(array)[bank*32:(bank+1)*32])
        # Direct combat descriptors are outside generated assets.o.
        for symbol, length in (('gEnemyDefs', 6*8), ('gHitboxes', 12*4)):
            self.equal(v, 'combat_rom', symbol, before.read(before.symbols[symbol], length), rom.read(rom.symbols[symbol], length))

    def native(self, v, rom, enemy):
        if not enemy:
            return
        expected = self.source_cache[enemy]
        for family, data in expected.items():
            meta, raw = rom.sheet(family)
            stride = meta['frame_tiles'] * 32
            if family != 'proj':
                self.check(v, 'native_frame', family + ' exact original/appended frame ordering',
                           [rom.defs.get('F_' + family.upper() + '_' + n.upper()) for n in data['frames']] == list(range(len(data['frames']))))
            for name, image in data['frames'].items():
                fid = rom.defs['F_' + family.upper() + '_' + name.upper()]
                self.check(v, 'native_frame', family + '.' + name + ' authoring canvas', image['size'] == [meta['width'],meta['height']])
                actual = decode_sprite(raw[fid*stride:(fid+1)*stride], meta['width'], meta['height'])
                self.equal(v, 'native_frame', family + '.' + name, bytes.fromhex(image['pixels']), actual)
            colors = rom.array('pal_obj')[meta['pal']*32:(meta['pal']+1)*32]
            self.check(v, 'native_palette', family + ' RGB555 indices/bank', len(colors) == 32 and all(x < 0x8000 for x in struct.unpack('<16H', colors)))
            if data.get('enemy_palette'):
                self.equal(v,'native_palette',family+' isolated enemy palette',struct.pack('<16H',*data['enemy_palette']),colors)
        item_bank=rom.defs['PAL_OBJ_ITEMS']
        for name in rom.sheet_ids:
            meta,raw=rom.sheet(name)
            palette_array=name+'_frame_pal'
            if palette_array in rom.sections:
                routes=rom.array(palette_array)
                self.check(v,'palette_isolation',name+' no material frame routes into enemy-only bank',item_bank not in routes)
            if name not in ('beetle','bat','slime') and meta['pal']==item_bank:
                self.check(v,'palette_isolation',name+' default enemy bank overridden for every frame',palette_array in rom.sections and len(rom.array(palette_array))==meta['tile_count']//meta['frame_tiles'])

    def budget(self, v, rom, enemy):
        meta = {n: rom.sheet(n)[0] for n in rom.sheet_ids}
        even = lambda x: (x+1)&~1
        foundation = even(meta['hero']['frame_tiles'] + meta['sword']['tile_count'] + meta['shield']['frame_tiles'])
        all_types = ('beetle','bat','spitter','slime','knight','ksword')
        # A deliberately stronger union than a normal generated room: every
        # enemy type, boss, optional world-object sheet and seven-icon cache.
        allocations = {'hero/body+sword+streamed-shield foundation': foundation}
        for n in ('items','fx','proj','lift','pick32'):
            allocations[n + ' whole sheet'] = even(meta[n]['tile_count'])
        allocations['Bloom streamed action'] = 16
        allocations['Bloom ground shadow'] = even(meta['bloomshadow']['tile_count'])
        for n in all_types:
            allocations[n + ' whole sheet'] = even(meta[n]['tile_count'])
        # Legacy EN_BOSS also invokes ensure_sheet(SHEET_KNIGHT); already counted.
        allocations['boss streamed frame' if enemy else 'boss whole sheet'] = even(meta['boss']['frame_tiles'] if enemy else meta['boss']['tile_count'])
        allocations['chest streamed frame'] = even(meta['interactivechest']['frame_tiles'])
        allocations['entrance streamed frame'] = even(meta['interactiveentry']['frame_tiles'])
        allocations['ambient whole sheet'] = even(meta['glitter']['tile_count'])
        allocations['arrow whole sheet'] = even(meta['arrow']['tile_count'])
        allocations['seven menu icons'] = even(7 * meta['icon32']['frame_tiles'])
        allocations['trial mouth whole sheet'] = even(meta['mouth']['tile_count'])
        allocations['one forest/trial NPC frame'] = even(meta['npc']['frame_tiles'])
        if not rom.defs.get('BART_MENU_VARIANT',0):
            allocations['legacy map marker sheet'] = even(meta['marks']['tile_count'])
            allocations['legacy map dot sheet'] = even(meta['dots']['tile_count'])
        capacity = int(re.search(r'#define\s+OBJ_TILE_HUD_ICONS\s+(\d+)', (ROOT/'src/actor.h').read_text()).group(1))
        total = sum(allocations.values())
        self.check(v, 'obj_budget', 'conservative legal room-superset fits actor tile region', total <= capacity, {'used':total,'limit':capacity,'free':capacity-total,'allocations':allocations})
        self.budgets.append({'variant':v,'enemy':enemy,'used':total,'limit':capacity,'free':capacity-total,'allocations':allocations,
                             'limits':'Static allocation superset, not an OAM peak/CPU guarantee. Includes every enemy family although ordinary themed rooms use subsets. Portrait/HUD use their fixed higher reservations.'})
        if enemy:
            boss_source = (ROOT/'src/boss.c').read_text()
            ensure_source = function((ROOT/'src/enemy.c').read_text(), 'ensure_sheet')
            self.check(v, 'obj_budget', 'boss allocates one native frame, not complete thirteen-frame sheet', 'sprite_alloc(sheets[SHEET_BOSS].frame_tiles)' in boss_source)
            self.check(v, 'obj_budget', 'boss avoids unused knight residency', 'type == EN_BOSS' in ensure_source and 'return;' in ensure_source)

    def code(self):
        ref = self.args.reference
        functions = {
            'src/enemy.c':['enemy_pick_type','enemy_spawn','enemy_kill','enemy_hurt','beetle_update','bat_update','spitter_update','slime_update','knight_update','enemy_common','enemies_update'],
            'src/boss.c':['boss_is_dying','mood','spore_ring','spore_fan','clamp_in_room','boss_update','boss_defeated','boss_died'],
            'src/objects.c':['proj_spawn','proj_update','drop_roll'],
            'src/player.c':['player_hurt','player_sword_box'],
        }
        for filename, names in functions.items():
            before = git_source(ref, filename)
            current = (ROOT/filename).read_text()
            for name in names:
                a, b = tokens(function(before,name)), tokens(function(current,name))
                self.check('source', 'combat_source', filename + ':' + name + ' tokens unchanged', a == b)
        for filename, symbol in [('src/enemy.c','gEnemyDefs'),('src/actor.c','gHitboxes')]:
            before, current = git_source(ref, filename), (ROOT/filename).read_text()
            pattern = r'\b' + symbol + r'\s*\[[^]]*\]\s*=\s*\{'
            self.check('source','combat_source',symbol+' initializer unchanged',tokens(brace_part(before,pattern)) == tokens(brace_part(current,pattern)))
        # Boss allocation is the only spawn change; initialization after it stays exact.
        a = function(git_source(ref,'src/boss.c'),'boss_spawn')
        b = function((ROOT/'src/boss.c').read_text(),'boss_spawn')
        self.check('source','combat_source','boss initialization after allocation unchanged',tokens(a[a.index('sDying = 0'):]) == tokens(b[b.index('sDying = 0'):]))
        source='\n'.join(p.read_text() for p in (ROOT/'src').glob('*.c'))
        self.check('source','palette_isolation','no direct PAL_OBJ_ITEMS playfield consumer','PAL_OBJ_ITEMS' not in strip_comments(source))
        for name in ('bomb_place','bomb_update'):
            body=function((ROOT/'src/objects.c').read_text(),name)
            self.check('source','palette_isolation',name+' uses explicit material frame palette','a->pal = items_frame_pal[a->frame];' in body)
        for filename in ('src/menu.c','src/text.c'):
            source=(ROOT/filename).read_text()
            calls=re.findall(r'draw_sprite\([^;]*SHEET_ITEMS[^;]*;',strip_comments(source))
            self.check('source','palette_isolation',filename+' every material-item direct draw has frame palette',all('items_frame_pal[' in c for c in calls))

    def capture_comparison(self, builds):
        if not self.args.captures:
            return {'status':'not_requested','limits':'Actual mGBA behavior belongs to the separate enemy_study_review.py suite.'}
        captures = Path(self.args.captures)
        reports = []
        for build in builds:
            enemy = build.get('enemy', build.get('enemy_variant', build.get('variant',0)))
            if not enemy:
                continue
            v = build['variant']
            options = [captures/f'v{v}'/'capture.json', captures/f'enemy-{enemy}'/'capture.json', captures/f'v{enemy}'/'capture.json']
            path = next((p for p in options if p.exists()), None)
            self.check(v,'runtime_comparison','positive-profile capture report exists',path is not None)
            if path:
                report=json.loads(path.read_text())
                self.check(v,'runtime_comparison','capture ROM matches frozen build',report['rom_sha256']==build['rom_sha256'])
                self.check(v,'runtime_comparison','capture source matches frozen build',report.get('source_commit')==build.get('source_commit'))
                self.check(v,'runtime_comparison','all twelve intended flows complete',report.get('capture_count')==len(report['captures'])==12)
                self.check(v,'runtime_comparison','capture checks all pass',report['passed']==report['total'] and not report['failures'])
                reports.append((enemy,path))
        if len(reports) != 10:
            return {'status':'incomplete','profiles':len(reports)}
        reports.sort(key=lambda r:r[0]);reference=reports[0][1];results=[]
        expected_names={r['name'] for r in json.loads(reference.read_text())['captures']}
        for enemy,report in reports[1:]:
            self.check(enemy,'runtime_comparison','identical complete clip set',expected_names=={r['name'] for r in json.loads(report.read_text())['captures']})
            comparison=compare_trajectories(reference,report)
            passed=comparison['total']>0 and comparison['passed']==comparison['total']
            self.check(enemy,'runtime_comparison','same positive-profile gameplay trace',passed,comparison)
            results.append({'enemy':enemy,**comparison})
        return {'status':'complete','comparison_reference':1,'positive_profile_count':len(reports),'profile_pairs':len(results),'matched_flows':sum(x['passed'] for x in results),'total_flows':sum(x['total'] for x in results),'profiles':results,'limits':'Compares canonical AI/gameplay fields, not framebuffer pixels, global VBlank phase or older baseline performance.'}

    def run(self):
        builds = json.loads((self.work/'builds.json').read_text())
        if self.args.variants:
            builds = [b for b in builds if b['variant'] in self.args.variants]
        source_inputs = {str(p.relative_to(ROOT)):SHA(p.read_bytes()) for p in sorted((ROOT/'art').glob('*')) if p.suffix in ('.py','.json')}
        self.code()
        for build in builds:
            v = build['variant']
            directory = Path(build.get('directory',build.get('frozen',self.work/f'v{v}')))
            if not directory.is_absolute():directory=self.work/directory
            rom = NativeRom(directory)
            freeze = json.loads((directory/'freeze.json').read_text())
            enemy = freeze.get('enemy',freeze.get('enemy_variant',rom.defs.get('BART_ENEMY_VARIANT',0)))
            if enemy and enemy not in self.source_cache:self.source_cache[enemy]=authoring(enemy)
            self.check(v,'provenance','ROM matches frozen SHA256',SHA(rom.rom)==freeze['rom_sha256'])
            self.check(v,'profile','enemy profile matches header',rom.defs.get('BART_ENEMY_VARIANT',0)==enemy,enemy)
            self.check(v,'profile','final Drain selected',rom.defs['BART_SEWER_VARIANT']==9)
            for field in ('source_file_sha256','code_file_sha256'):
                recorded=freeze.get(field,{})
                self.check(v,'provenance',field+' populated',bool(recorded))
                for name,digest in recorded.items():
                    current=(ROOT/name).read_bytes()
                    self.check(v,'frozen_source',name+' current digest',SHA(current)==digest)
                    if freeze.get('source_commit'):
                        self.check(v,'frozen_source',name+' committed digest',SHA(subprocess.check_output(['git','show',freeze['source_commit']+':bartgame/'+name],cwd=ROOT))==digest)
            self.world(v,rom,enemy)
            self.native(v,rom,enemy)
            self.budget(v,rom,enemy)
            checks=[r for r in self.rows if r['variant']==v]
            self.variants.append({'variant':v,'enemy':enemy,'rom_sha256':SHA(rom.rom),'native_frames':sum(len(r['frames']) for r in self.source_cache.get(enemy,{}).values()),'passed':sum(r['passed'] for r in checks),'total':len(checks)})
            print('VARIANT',v,sum(r['passed'] for r in checks),'/',len(checks),flush=True)
        captures=self.capture_comparison(builds)
        self.check('source','provenance','native authoring inputs stayed unchanged during audit',source_inputs=={str(p.relative_to(ROOT)):SHA(p.read_bytes()) for p in sorted((ROOT/'art').glob('*')) if p.suffix in ('.py','.json')})
        report={'method':__doc__,'reference_commit':self.args.reference,'baseline_rom_sha256':SHA(self.base.rom),'auditor_sha256':SHA(Path(__file__).read_bytes()),'source_file_sha256':source_inputs,'variants':self.variants,'obj_budgets':self.budgets,'runtime_comparison':captures,'passed':sum(r['passed'] for r in self.rows),'total':len(self.rows),'failures':[r for r in self.rows if not r['passed']],'checks':self.rows,'limits':'Native encoding, scope and gameplay-contract evidence, not aesthetic ranking or human playtest. UI appearance/options/map geometry is separately reviewed. Every bonus frame can be correctly encoded without necessarily being observed in the actual sampled combat.'}
        out=Path(self.args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
        summary=out.with_name(out.stem+'-summary.json');summary.write_text(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2)+'\n')
        print('RESULT',report['passed'],'/',report['total'],flush=True)
        return int(bool(report['failures']))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',default='/workspace/setup/appearance-enemy-studies')
    p.add_argument('--baseline',default='/workspace/setup/ui-layout-studies/v0')
    p.add_argument('--reference',default=DEFAULT_REF)
    p.add_argument('--out',default='/workspace/setup/appearance-enemy-studies/enemy-audit.json')
    p.add_argument('--variants',type=int,nargs='*')
    p.add_argument('--captures',help='Optional completed positive-profile mGBA captures root.')
    return Audit(p.parse_args()).run()

if __name__=='__main__':raise SystemExit(main())
