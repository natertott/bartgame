#!/usr/bin/env python3
"""Actual mGBA regression of first-pause inventory and borrowed graphics.

Seed1's real opening draft awards Mole Mitts, a Heart Container and Peril Beam.
No inventory, health, completion, actor results, palettes or video pixels are
assigned. Field review uses disclosed normal room loads and hero navigation.
The baseline mode records the original failures instead of repairing them.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from PIL import Image

import cream_art_study_capture as A
from cream_dynamic_capture import DynamicCapture, map_redraw
from regional_native_support import NativeRun, sha
from sewer_concept_audit import NativeRom
import probe as Q


def write(path, value):
    A.write_json(path, value)


def shot(run, out, name):
    im = run.c.bg_video.to_pil().convert('RGB').copy()
    im.save(out / (name + '.png'))
    im.resize((720, 480), Image.Resampling.NEAREST).save(out / (name + '-3x.png'))
    return dict(file=name + '.png', sha256=sha(out / (name + '.png')))


def ui_abi(run):
    folder = run.out / 'ui-abi'
    folder.mkdir(exist_ok=True)
    values = dict(def_size='sizeof(LegacyItemDef)', def_frame='offsetof(LegacyItemDef,frame)',
                  eq_mitts='EQ_MOLE_MITTS', ui_begin='UI_BG0*32', ui_bytes='UI_TILE_COUNT*32',
                  hud_begin='HUD_TILE_BASE*32', hud_bytes='HUD_TILE_COUNT*32',
                  hud_obj='OBJ_TILE_HUD_ICONS*32', hud_obj_bytes='60*32',
                  obj_limit='OBJ_TILE_SHEETS_END',
                  cream_progress_size='sizeof(CreamProgress)')
    source = '#include <stddef.h>\n#include "legacy_items.h"\n#include "ui.h"\n#include "cream_runtime.h"\n'
    source += 'const unsigned values[] __attribute__((used,section(".uiabi")))={' + ','.join(values.values()) + '};\n'
    unit, obj, binary = [folder / n for n in ('abi.c', 'abi.o', 'abi.bin')]
    unit.write_text(source)
    cmd = ['arm-none-eabi-gcc', '-mcpu=arm7tdmi', '-mthumb', '-std=c99', '-I', str(run.out / 'abi/headers'), '-c', str(unit), '-o', str(obj)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    (folder / 'compile.log').write_text(result.stdout + result.stderr)
    result.check_returncode()
    subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', '-j', '.uiabi', str(obj), str(binary)], check=True)
    answer = dict(zip(values, struct.unpack('<' + 'I' * len(values), binary.read_bytes())))
    write(folder / 'provenance.json', dict(source_commit=(run.bundle / 'source-commit.txt').read_text().strip(), values=answer, source_sha256=sha(unit), command=cmd))
    return answer


class Checks:
    def __init__(self):
        self.rows = []

    def check(self, name, passed, observed=None):
        self.rows.append(dict(name=name, passed=bool(passed), observed=observed))
        print(('PASS ' if passed else 'FAIL ') + name, flush=True)
        if not passed:
            raise AssertionError((name, observed))


def state_digest(run):
    a = run.abi
    return {name: A.digest(A.raw(run.c, Q.sym(name), size)) for name, size in (
        ('gRoom', 0), ('gActors', 96 * 64), ('gLegacyInventory', a['inventory_size']),
        ('gHandoffState', a['handoff_size'])) if size}


def source_item_frame(run, rom, abi, item):
    frame = rom.read(rom.symbols['gLegacyItemDefs'] + item * abi['def_size'] + abi['def_frame'], 1)[0]
    sh, data = rom.sheet('handoff_items')
    count = sh['frame_tiles'] * 32
    return data[frame * count:(frame + 1) * count], rom.array('pal_obj')[sh['pal'] * 32:(sh['pal'] + 1) * 32]


def displayed_item(run, rom, abi, item):
    """Read hardware OAM and actual OBJ tile/palette bytes, not menu claims."""
    expected, pal = source_item_frame(run, rom, abi, item)
    found = []
    for i in range(128):
        a0, a1, a2 = [Q.r16(run.c, 0x07000000 + i * 8 + off) & 65535 for off in (0, 2, 4)]
        if a0 & 0x300 == 0x200 or (a0 >> 14) != 0 or (a1 >> 14) != 1:
            continue
        x, y = a1 & 511, a0 & 255
        if x >= 240 or y >= 160:
            continue
        tile, bank = a2 & 1023, a2 >> 12
        data = A.raw(run.c, 0x06010000 + tile * 32, len(expected))
        actual_pal = A.raw(run.c, 0x05000200 + bank * 32, 32)
        if data == expected and actual_pal == pal:
            found.append(dict(oam=i, x=x, y=y, tile=tile, palette=bank, tile_sha256=A.digest(data)))
    return found


def resident(run, rom, abi):
    style = run.u8('gAppearanceStyle')
    expected = dict(blank=bytes(32), hud=rom.array('hud_tiles'),
                    kit=rom.array('appearance_ui_tiles')[style * abi['ui_bytes']:(style + 1) * abi['ui_bytes']])
    actual = dict(blank=A.raw(run.c, 0x06008000, 32),
                  hud=A.raw(run.c, 0x06008000 + abi['hud_begin'], abi['hud_bytes']),
                  kit=A.raw(run.c, 0x06008000 + abi['ui_begin'], abi['ui_bytes']))
    return {k: dict(exact=actual[k] == expected[k], expected_sha256=A.digest(expected[k]),
                    actual_sha256=A.digest(actual[k]), bytes=len(actual[k])) for k in expected}


def static_ground(run, rom):
    area = run.snapshot()['area']
    name = {0: 'sewer', 1: 'forest', 3: 'cream'}[area]
    ts = rom.tileset(name)
    data = bytearray(A.raw(run.c, 0x06000000, 32768))
    # Water and other native animations legitimately advance across a pause.
    # Compare every other byte, including all characters above the600tile UI.
    animated = []
    for anim in ts['animations']:
        a, b = anim['base'] * 32, (anim['base'] + 4) * 32
        data[a:b] = bytes(b - a)
        animated.append([a, b])
    return dict(area=area, sha256=A.digest(data), bytes=len(data), excluded_animated_ranges=animated)


def wait_area(live, area):
    live.advance([], 800, stop=lambda s: s['area'] == area and s['state'] == 1 and
                 s['actor']['state'] == 0 and not s['actor']['z'])
    live.run.dismiss()
    live.check('ordinary input reaches living area%d' % area,
               live.state()['area'] == area and live.state()['state'] == 1 and live.state()['health'][0] > 0)


def forest_round_trip(live, rom, abi, out, checks):
    out.mkdir(exist_ok=True)
    live.request(live.world.entry_node // 2)
    d = live.info().return_door
    live.nav((d.x + 1) * 16, (d.y + 1) * 16 + 14, 0)
    live.advance('A', 2)
    wait_area(live, 0)
    checks.check('Cream return preserves Sewer resident UI tiles', all(v['exact'] for v in resident(live.run, rom, abi).values()))
    candidates = [(x, y) for y in range(24) for x in range(32)
                  if live.tile_type(x * 16 + 8, y * 16 + 10) == rom.defs['TT_EXIT'] and
                  abs(x * 16 + 8 - live.run.abi['hub_ladder_x']) > 16]
    if not candidates:
        raise AssertionError('ordinary Forest ladder was not found')
    x, y = min(candidates, key=lambda p: (p[1], p[0]))
    live.nav(x * 16 + 8, (y + 2) * 16 + 14, 0)
    live.advance('UP', 500, stop=lambda s: s['area'] == 1 and s['state'] == 1)
    wait_area(live, 1)
    live.advance([], 8)
    before = static_ground(live.run, rom)
    shot(live.run, out, 'before')
    live.advance('START', 2)
    live.advance([], 60)
    for _ in range(2):
        live.advance('R', 2)
        live.advance([], 80)
    live.advance('A', 2)
    live.advance([], 120)
    shot(live.run, out, 'forest-map-zoom')
    live.advance('R', 2)
    live.advance([], 60)
    live.advance('START', 2)
    wait_area(live, 1)
    live.advance([], 8)
    after = static_ground(live.run, rom)
    shot(live.run, out, 'after')
    checks.check('Forest pause restores every static world character, including above600', before['sha256'] == after['sha256'], dict(before=before, after=after))
    checks.check('Forest map and inventory restore all resident HUD/UI pixels', all(v['exact'] for v in resident(live.run, rom, abi).values()))
    return dict(before=before, after=after)


def inventory_case(bundle, out, baseline):
    out.mkdir(parents=True, exist_ok=True)
    checks = Checks()
    run = NativeRun(bundle, out / 'private-core')
    rom = NativeRom(bundle)
    abi = ui_abi(run)
    run.start(1)
    gifts = run.finish_draft((1, 0, 0))
    run.settle(0)
    run.dismiss()
    checks.check('actual opening draft earned Mitts, Heart Container and Peril Beam', [x['item'] for x in gifts] == [19, 98, 79], gifts)
    checks.check('Mole Mitts are truly owned before first pause', bool(run.snapshot()['inventory']['owned'][0] & (1 << 19)))
    pictures = [shot(run, out, 'earned-before-first-pause')]
    run.tap('START', 60)
    pictures.append(shot(run, out, 'first-pause'))
    mitts = displayed_item(run, rom, abi, 19)
    if baseline:
        checks.check('baseline reproduces earned tool absent from first pause', not mitts)
    else:
        checks.check('first pause visibly renders the earned Mitts native pixels and palette', bool(mitts), mitts)
        checks.check('first pause selects the newly earned tool', run.u8('gMenuStudyItem') == 19, run.u8('gMenuStudyItem'))
        before = state_digest(run)
        run.keys([], 16)
        checks.check('idle first inventory frame preserves actors, ownership and progress', state_digest(run) == before)
        for slot, key in enumerate(('A', 'B', 'L')):
            run.tap(key, 16)
            eq = run.u8('gPl', run.abi['player_equip'] + slot)
            checks.check('real ' + key + ' equips the newly earned Mitts', eq == abi['eq_mitts'], eq)
        pictures.append(shot(run, out, 'equipped-mitts'))
    run.tap('R', 60)
    pictures.append(shot(run, out, 'new-passives'))
    passives = {str(item): displayed_item(run, rom, abi, item) for item in (79, 98)}
    if baseline:
        checks.check('baseline reproduces missing newly earned passives', not any(passives.values()), passives)
        # This is the user's workaround, using actual menu inputs.
        run.tap('R', 100)
        run.tap('R', 60)
        run.keys('SELECT', 4)
        run.keys([], 80)
        pictures.append(shot(run, out, 'later-satchel-workaround'))
        checks.check('baseline later Satchel visibly renders the same owned Mitts', bool(displayed_item(run, rom, abi, 19)))
    else:
        for item in (79, 98):
            checks.check('Keys page visibly renders earned item%d native pixels' % item, bool(passives[str(item)]), passives[str(item)])
        pictures.append(shot(run, out, 'keys-first-page'))
        run.tap('R', 120)
        run.tap('R', 60)
        checks.check('page cycle returns to Items with Mitts still present', run.u8('gMenuStudyPage') == 0 and bool(displayed_item(run, rom, abi, 19)))
        pictures.append(shot(run, out, 'items-after-page-cycle'))
        run.tap('START', 80)
        checks.check('primary pause closes into healthy Sewer play', run.snapshot()['state'] == 1 and run.snapshot()['area'] == 0 and run.snapshot()['health'][0] > 0)
        checks.check('Sewer resident HUD and UI pixels survive primary pages', all(v['exact'] for v in resident(run, rom, abi).values()), resident(run, rom, abi))
        run.tap('START', 60)
        checks.check('reopening primary inventory does not hide the earned tool', bool(displayed_item(run, rom, abi, 19)))
        pictures.append(shot(run, out, 'reopened-items'))
        run.tap('START', 80)
    write(out / 'input-trace.json', run.report_identity() | dict(inputs=run.inputs, draft=gifts))
    report = dict(rom_sha256=sha(Path(bundle) / 'bartgame.gba'), source_commit=(Path(bundle) / 'source-commit.txt').read_text().strip(),
                  seed=1, baseline=baseline, draft=gifts, native_mitts_stamps=mitts, passive_stamps=passives,
                  images=pictures, checks=checks.rows, complete=all(c['passed'] for c in checks.rows))
    write(out / 'report.json', report)
    return report


def graphics_case(bundle, out, baseline, survey=False):
    out.mkdir(parents=True, exist_ok=True)
    checks = Checks()
    live = DynamicCapture(bundle, out / 'private-core', 1)
    run, rom = live.run, NativeRom(bundle)
    abi = ui_abi(run)
    scans = []
    if survey:
        for cell in range(25):
            live.request(cell)
            live.advance([], 2)
            scans.append(dict(cell=cell, **run.resources()))
        selected = max(scans, key=lambda r: (r['next_tile'] or 0, len(r['world_oam'])))['cell']
        live.request(selected)
    live.safe_position()
    live.advance([], 8)
    before = resident(run, rom, abi)
    checks.check('resident blank, heart and UI tiles match ROM before pause', all(v['exact'] for v in before.values()), before)
    hud_before = A.raw(live.c, 0x06010000 + abi['hud_obj'], abi['hud_obj_bytes'])
    borrow_start = 0x06010000 + (abi['obj_limit'] - 7 * 16) * 32
    borrowed_before = A.raw(live.c, borrow_start, (7 * 16 + 60) * 32)
    palette_before = A.raw(live.c, Q.sym('gPalObj'), 512)
    resources_before = run.resources()
    ground_before = static_ground(run, rom)
    pictures = [shot(run, out, 'before-pause')]
    live.advance('START', 2)
    live.advance([], 60)
    pictures.append(shot(run, out, 'primary-items'))
    if not baseline:
        checks.check('pausing does not allocate world OBJ heap', run.resources()['next_tile'] == resources_before['next_tile'], dict(before=resources_before, after=run.resources()))
        checks.check('pausing adds no sprite allocation failure', run.resources()['alloc_failures'] == resources_before['alloc_failures'])
    live.advance('R', 2)
    live.advance([], 60)
    map_redraw(live, 'R', 0, 0)
    snapshot = live.readonly()
    map_redraw(live, 'A', 0, 1)
    pictures.append(shot(run, out, 'atlas-zoom'))
    checks.check('atlas zoom preserves physical game state', live.readonly() == snapshot)
    live.advance('R', 2)
    live.advance([], 80)
    pictures.append(shot(run, out, 'satchel-after-atlas'))
    after_satchel = resident(run, rom, abi)
    checks.check('atlas-to-Satchel preserves actors, inventory and progression', live.readonly() == snapshot)
    if baseline:
        checks.check('baseline reproduces corrupted BG0 resident tiles on Satchel return', not all(v['exact'] for v in after_satchel.values()), after_satchel)
    else:
        checks.check('atlas-to-Satchel restores every BG0 resident tile exactly', all(v['exact'] for v in after_satchel.values()), after_satchel)
    live.advance('START', 2)
    live.advance([], 600, stop=lambda s: s['state'] == 1 and s['actor']['state'] == 0 and s['actor']['z'] == 0)
    live.advance([], 6)
    pictures.append(shot(run, out, 'returned-to-world'))
    after = resident(run, rom, abi)
    checks.check('pause round trip returns to living Cream gameplay', live.state()['state'] == 1 and live.state()['health'][0] > 0)
    if baseline:
        checks.check('baseline reproduces persistent corrupted HUD/UI bytes after close', not all(v['exact'] for v in after.values()), after)
    else:
        checks.check('closed menu restores exact blank, HUD hearts and UI kit source bytes', all(v['exact'] for v in after.values()), after)
        hud_after = A.raw(live.c, 0x06010000 + abi['hud_obj'], abi['hud_obj_bytes'])
        checks.check('closed menu restores all60 reserved HUD OBJ characters', hud_after == hud_before,
                     dict(before_sha256=A.digest(hud_before), after_sha256=A.digest(hud_after)))
        borrowed_after = A.raw(live.c, borrow_start, len(borrowed_before))
        checks.check('closed menu restores every borrowed icon and HUD OBJ character', borrowed_after == borrowed_before,
                     dict(bytes=len(borrowed_before), before_sha256=A.digest(borrowed_before), after_sha256=A.digest(borrowed_after)))
        palette_after = A.raw(live.c, Q.sym('gPalObj'), 512)
        checks.check('closed menu restores all sixteen live OBJ palette banks', palette_after == palette_before,
                     dict(bytes=512, before_sha256=A.digest(palette_before), after_sha256=A.digest(palette_after)))
        live.advance([], 8)
        checks.check('no stale queued upload re-corrupts restored resident tiles', all(v['exact'] for v in resident(run, rom, abi).values()))
        live.composites(out / 'restored-native-BG2')
        ground_after = static_ground(run, rom)
        checks.check('Cream round trip restores every static ground character including above600', ground_before['sha256'] == ground_after['sha256'], dict(before=ground_before, after=ground_after))
        forest = forest_round_trip(live, rom, abi, out / 'forest', checks)
    write(out / 'input-trace.json', live.identity())
    report = dict(rom_sha256=sha(Path(bundle) / 'bartgame.gba'), source_commit=(Path(bundle) / 'source-commit.txt').read_text().strip(),
                  seed=1, baseline=baseline, images=pictures, residents_before=before, residents_on_satchel=after_satchel,
                  residents_after=after, room_survey=scans, resources_before=resources_before,
                  resources_after=run.resources(), ground_before=ground_before, forest=None if baseline else forest, checks=checks.rows, complete=all(c['passed'] for c in checks.rows))
    write(out / 'report.json', report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--baseline', action='store_true')
    p.add_argument('--survey', action='store_true')
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    sections = dict(inventory=inventory_case(a.bundle, a.out / 'inventory', a.baseline),
                    graphics=graphics_case(a.bundle, a.out / 'graphics', a.baseline, a.survey))
    report = dict(source_commit=(a.bundle / 'source-commit.txt').read_text().strip(), rom_sha256=sha(a.bundle / 'bartgame.gba'),
                  tool_sha256=sha(Path(__file__)), baseline=a.baseline, sections=sections,
                  complete=all(s['complete'] for s in sections.values()),
                  fixture_scope='Seeded real opening draft (choices1,0,0), actual menu/equipment inputs and disclosed ordinary loader/hero-position navigation. No health, inventory, completion, palette, terrain or video result writes.')
    write(a.out / 'report.json', report)
    return int(not report['complete'])


if __name__ == '__main__':
    raise SystemExit(main())
