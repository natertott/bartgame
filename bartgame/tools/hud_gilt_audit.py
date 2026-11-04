#!/usr/bin/env python3
"""Independent scope, native-art fidelity and hardware-budget HUD review.

This compares decoded linked ROM assets with the native source and the previous
selected game. It does not claim that numerical checks establish attractive art;
actual HUD motion and scene readability are reviewed separately in mGBA.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from sewer_concept_audit import NativeRom, decode_sprite

GAME = Path(__file__).resolve().parents[1]
REPO = GAME.parent
BASELINE = 'e3e65be4d7ab98426e31a4bfab9dac02e17299f6'
BASELINE_ROM = '5fcf4cba1c6ab3a5af4575a5a05a49d9813457a02b4f5d16a7e3abc05e41566e'
ITEM_SHEETS = {'items', 'pick32', 'icon32', 'huditems'}
POINTER_TABLES = {'sheets', 'tilesets', 'room_defs', 'tile_anims_forest',
                  'tile_anims_myst', 'tile_anims_sewer'}
SHA = lambda data: hashlib.sha256(data).hexdigest()


def digest(value):
    return SHA(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def export_source():
    """Clean subprocess entry: no cached painters cross profile boundaries."""
    sys.path.insert(0, str(GAME/'art'))
    import palettes
    import rooms
    import sprites
    import tiles
    families = {}
    for sheet in sprites.SHEETS:
        name = sheet['name']
        families[name] = {
            'digest': digest(sheet), 'w': sheet['w'], 'h': sheet['h'],
            'pal': sheet['pal'], 'order': list(sheet['frames']),
            'frame_pal': sheet.get('frame_pal', {}),
        }
        if name in ITEM_SHEETS:
            families[name]['frames'] = {
                frame: bytes(int(pixel, 16) if pixel != '.' else 0
                             for row in rows for pixel in row).hex()
                for frame, rows in sheet['frames'].items()
            }
    print(json.dumps({
        'sheets': families,
        'bg_palettes': palettes.BG_PALETTES,
        'obj_palettes': palettes.OBJ_PALETTES,
        'metatiles': digest(tiles.METATILES),
        'rooms': digest(rooms.ROOMS),
    }, separators=(',', ':')))


def source_profile(profile):
    env = dict(os.environ, BART_SWING='3', BART_SEWER='9', BART_UI='6',
               BART_MENU='1', BART_ENEMY='11', BART_FOREST='32',
               BART_HUD=str(profile))
    result = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                             '--export-source'], cwd=GAME, env=env, check=True,
                            text=True, capture_output=True)
    return json.loads(result.stdout)


def bounds(pixels, w, h):
    points = [(i % w, i // w) for i, value in enumerate(pixels) if value]
    if not points:
        return None
    xs, ys = zip(*points)
    return [min(xs), min(ys), max(xs)+1, max(ys)+1]


def connected_components(pixels, w, h):
    pending = {i for i, value in enumerate(pixels) if value}
    components = 0
    while pending:
        components += 1
        frontier = [pending.pop()]
        while frontier:
            at = frontier.pop()
            x, y = at % w, at // w
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx, ny = x+dx, y+dy
                    other = ny*w+nx
                    if 0 <= nx < w and 0 <= ny < h and other in pending:
                        pending.remove(other)
                        frontier.append(other)
    return components


def section_size(linker, name):
    match = re.search(r'^\.'+re.escape(name)+r'\s+0x[0-9a-fA-F]+\s+0x([0-9a-fA-F]+)',
                      linker, re.M)
    return int(match.group(1), 16) if match else 0


class Audit:
    def __init__(self, args):
        self.args, self.checks = args, []
        self.before, self.after = NativeRom(args.before), NativeRom(args.after)

    def check(self, group, name, passed, detail=None):
        row = {'group': group, 'name': name, 'passed': bool(passed)}
        if detail is not None:
            row['detail'] = detail
        self.checks.append(row)
        if not passed:
            print('FAIL', group, name, detail, flush=True)

    def provenance(self):
        self.check('provenance', 'prior selected ROM is the delivered forest-cohesion baseline',
                   SHA(self.before.rom) == BASELINE_ROM)
        freeze_path = self.after.directory/'freeze.json'
        freeze = json.loads(freeze_path.read_text()) if freeze_path.exists() else {}
        if self.args.allow_pilot:
            self.freeze_metadata = {'unqualified_pilot': True, 'freeze': freeze}
        else:
            commit = freeze.get('source_commit', '')
            self.check('provenance', 'final freeze binds actual ROM bytes and a committed source revision',
                       SHA(self.after.rom) == freeze.get('rom_sha256') and
                       bool(re.fullmatch('[0-9a-f]{40}', commit)) and
                       'pilot' not in freeze.get('status', '').lower())
            inputs = freeze.get('inputs', {})
            self.check('provenance', 'final freeze records all game/art/build inputs',
                       len(inputs) >= 200 and 'src/text.c' in inputs and
                       'art/hud_gilt_items.py' in inputs and 'tools/build_assets.py' in inputs)
            for relative, expected in sorted(inputs.items()):
                current = (GAME/relative).read_bytes()
                linked_source = subprocess.check_output(
                    ['git', 'show', commit+':'+str((GAME/relative).relative_to(REPO))], cwd=REPO)
                self.check('provenance', relative+' matches current and committed frozen inputs',
                           SHA(current) == expected and SHA(linked_source) == expected)
            self.freeze_metadata = {'unqualified_pilot': False, 'source_commit': commit,
                                    'inputs_checked': len(inputs),
                                    'freeze_sha256': SHA(freeze_path.read_bytes()) if freeze_path.exists() else None}
        self.check('configuration', 'current HUD1/default forest32 and selected controls',
                   all(self.after.defs.get(name) == value for name, value in {
                       'BART_HUD_VARIANT': 1, 'BART_FOREST_VARIANT': 32,
                       'BART_SEWER_VARIANT': 9, 'BART_UI_VARIANT': 6,
                       'BART_MENU_VARIANT': 1, 'BART_ENEMY_VARIANT': 11,
                       'BLOOM_SWING_STUDY': 3, 'HUD_HEIGHT_PIXELS': 20,
                   }.items()))
        if self.args.legacy:
            legacy = NativeRom(self.args.legacy)
            self.check('configuration', 'legacy comparison is a current explicitHUD0 build',
                       legacy.defs.get('BART_HUD_VARIANT') == 0)
            self.check('configuration', 'HUD0 reproduces every byte of the prior released ROM',
                       legacy.rom == self.before.rom,
                       {'sha256': SHA(legacy.rom), 'bytes': len(legacy.rom)})
        else:
            self.check('configuration', 'HUD0 legacy preservation bundle supplied', False)
        changed = []
        for path in sorted((GAME/'src').glob('*')):
            if path.suffix not in ('.c', '.h', '.s'):
                continue
            relative = str(path.relative_to(REPO))
            old = subprocess.check_output(['git', 'show', BASELINE+':'+relative], cwd=REPO)
            if old != path.read_bytes():
                changed.append(str(path.relative_to(GAME)))
        self.check('scope', 'all gameplay/region/weapon/save source remains exact',
                   set(changed) <= {'src/text.c', 'src/text.h', 'src/actor.h'}, changed)
        return changed

    def native(self):
        before, after = source_profile(0), source_profile(1)
        records, changed = [], []
        for key in ('bg_palettes', 'obj_palettes', 'metatiles', 'rooms'):
            self.check('source scope', key+' remains exact', before[key] == after[key])
        self.check('source scope', 'all sprite identities remain registered in the same order',
                   list(before['sheets']) == list(after['sheets']))
        for name, old in before['sheets'].items():
            new = after['sheets'][name]
            for field in ('w', 'h', 'pal', 'order', 'frame_pal'):
                self.check('metadata', name+' '+field+' remains exact', old[field] == new[field])
            if name not in ITEM_SHEETS:
                self.check('source scope', name+' all source pixels retained', old['digest'] == new['digest'])
                continue
            meta, packed = self.after.sheet(name)
            w, h = new['w'], new['h']
            self.check('native', name+' linked canvas and frame allocation match native source',
                       (meta['width'], meta['height'], meta['frame_tiles']) == (w, h, w*h//64))
            for i, frame in enumerate(new['order']):
                source = bytes.fromhex(new['frames'][frame])
                previous = bytes.fromhex(old['frames'][frame])
                data = packed[i*meta['frame_tiles']*32:(i+1)*meta['frame_tiles']*32]
                decoded = decode_sprite(data, w, h)
                self.check('native', name+'/'+frame+' every packed pixel equals native source', source == decoded)
                self.check('native', name+'/'+frame+' has legal15 painted inks and alpha0',
                           len(source) == w*h and set(source) <= set(range(16)))
                parts = connected_components(source, w, h)
                self.check('silhouette', name+'/'+frame+' is one connected item without stray fragments',
                           parts == (0 if frame == 'none' else 1), {'components8': parts})
                box = bounds(source, w, h)
                old_box = bounds(previous, w, h)
                if source != previous:
                    changed.append(name+'/'+frame)
                records.append({'sheet': name, 'frame': frame, 'canvas': [w, h],
                                'bounds': box, 'painted_pixels': sum(bool(x) for x in source),
                                'previous_bounds': old_box,
                                'changed': source != previous, 'pixel_sha256': SHA(source)})
                if name in ('items', 'pick32'):
                    self.check('world scale', name+'/'+frame+' keeps a compact14px-or-smaller pickup body',
                               w == h == 16 and (box is None or max(box[2]-box[0], box[3]-box[1]) <= 14))
                if name == 'huditems' and frame in ('sword', 'shield', 'shield_upgraded',
                                                  'bombs', 'lamp', 'cloak', 'bow', 'hubcap'):
                    extent = max(box[2]-box[0], box[3]-box[1]) if box else 0
                    old_extent = max(old_box[2]-old_box[0], old_box[3]-old_box[1]) if old_box else 0
                    self.check('HUD scale', frame+' equipped icon has a larger native silhouette',
                               13 <= extent <= 16 and extent > old_extent,
                               {'before_extent': old_extent, 'after_extent': extent})
        for name, colors in after['bg_palettes'] + after['obj_palettes']:
            self.check('palette', name+' is one16-entry native RGB555 bank',
                       len(colors) == 16 and all(int(c[i:i+2], 16) % 8 == 0
                                                for c in colors for i in (1, 3, 5)))
        self.check('art scope', 'each item presentation family contains actual redrawn pixels',
                   all(any(item.startswith(name+'/') for item in changed) for name in ITEM_SHEETS))
        self.check('native', 'the real menu uses the same redrawn32px item pixels',
                   self.after.array('icon32_exact_tiles') == self.after.sheet('icon32')[1])
        return {'frames': records, 'changed_frames': changed,
                'source_comparison': 'Separate clean interpreters, HUD0/HUD1; exact native nibbles decoded independently from linked OBJ data.'}

    def protected(self):
        self.check('scope', 'all linked sheet IDs stay exact', self.before.sheet_ids == self.after.sheet_ids)
        self.check('scope', 'all linked metatile IDs stay exact', self.before.tile_ids == self.after.tile_ids)
        for name in self.before.sheet_ids:
            old, new = self.before.sheet(name), self.after.sheet(name)
            self.check('scope', name+' linked physical descriptor remains exact', old[0] == new[0])
            if name not in ITEM_SHEETS:
                self.check('scope', name+' entire linked sheet remains exact', old == new)
        allowed = {'sheet_'+name+'_tiles' for name in ITEM_SHEETS} | {'icon32_exact_tiles'}
        count = 0
        for name in sorted(self.before.sections):
            if name in allowed or name in POINTER_TABLES:
                continue
            self.check('scope', name+' linked scalar/material payload remains exact',
                       name in self.after.sections and self.before.array(name) == self.after.array(name))
            count += 1
        for name in ('forest', 'sewer', 'myst'):
            self.check('scope', name+' resolved terrain/map/animations/palettes remain exact',
                       self.before.tileset(name) == self.after.tileset(name))
        return {'protected_scalar_arrays': count,
                'excluded_pointer_tables': sorted(POINTER_TABLES),
                'allowed_changed_arrays': sorted(allowed)}

    def budgets(self):
        before, after = self.before, self.after
        memory = {}
        for region in ('iwram', 'bss', 'ewram', 'ewram_bss'):
            memory[region] = {'before_bytes': section_size(before.linker, region),
                              'after_bytes': section_size(after.linker, region)}
        iwram = memory['iwram']['after_bytes'] + memory['bss']['after_bytes']
        ewram = memory['ewram']['after_bytes'] + memory['ewram_bss']['after_bytes']
        self.check('budget', 'IWRAM preserves system/stack headroom', iwram <= 32*1024-256,
                   {'used': iwram, 'available': 32*1024-256})
        self.check('budget', 'EWRAM fits physical256KB memory', ewram <= 256*1024,
                   {'used': ewram, 'headroom': 256*1024-ewram})
        for name in ('forest', 'sewer', 'myst'):
            ts = after.tileset(name)
            self.check('budget', name+' retains legal BG tile and palette residency',
                       ts['tile_count'] <= (768 if name == 'forest' else 1024) and ts['palette_count'] <= 12,
                       {'tiles': ts['tile_count'], 'banks': ts['palette_count']})
        actor = (GAME/'src/actor.h').read_text()
        start = re.search(r'^#define OBJ_TILE_MINIMAP\s+(\d+)', actor, re.M)
        self.check('budget', '32px minimap occupies the reserved final16OBJ tiles',
                   start is not None and int(start.group(1)) == 1008 and int(start.group(1))+16 == 1024)
        purse_first = after.defs['HUD_TILE_BASE'] + after.defs['HUD_TILE_COUNT'] + after.defs['UI_TILE_COUNT']
        available = 384-purse_first-30*3
        self.check('budget', 'BG0 text pool remains positive below screenblocks22/23', available > 0,
                   {'first_tile': purse_first+90, 'end_tile': 384,
                    'available_text_tiles': available,
                    'note': 'Dialogue/shop allocation success is separately exercised in real mGBA.'})
        return memory

    def run(self):
        changed_source = self.provenance()
        source = self.native()
        scope = self.protected()
        memory = self.budgets()
        passed = sum(row['passed'] for row in self.checks)
        return {'method': __doc__.strip(), 'tool_sha256': SHA(Path(__file__).read_bytes()),
                'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
                'baseline_commit': BASELINE, 'baseline_rom_sha256': SHA(self.before.rom),
                'rom_sha256': SHA(self.after.rom), 'rom_bytes': len(self.after.rom),
                'changed_source_files': changed_source, 'native_art': source,
                'freeze_provenance': self.freeze_metadata,
                'protected_scope': scope, 'memory': memory,
                'passed': passed, 'total': len(self.checks), 'checks': self.checks}


def main():
    if '--export-source' in sys.argv:
        export_source()
        return 0
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before', default='/workspace/setup/hud-gilt/before/bundle')
    ap.add_argument('--after', required=True)
    ap.add_argument('--legacy')
    ap.add_argument('--allow-pilot', action='store_true',
                    help='Private iteration only: bypass committed final input qualification.')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    report = Audit(args).run()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2)+'\n')
    print('RESULT %s %d/%d' % ('PASS' if report['passed'] == report['total'] else 'FAIL',
                              report['passed'], report['total']), flush=True)
    return int(report['passed'] != report['total'])


if __name__ == '__main__':
    raise SystemExit(main())
