"""Native integration checks for the frozen release, without rebuilding it.

Only explicit fixtures are the deterministic title seed, player navigation
(position/facing/safe standing point), pending normal room transitions, and a
full player inventory for negative trial tests. The probe never writes enemy
state/HP, terrain/collision, trial/completion flags, audio state or framebuffer.
Dry Sewer reachability is computed from the actual loaded Room and ROM tile
types; interaction/return and modal/audio behavior use real mGBA key inputs.
"""
import argparse
import hashlib
import json
import shutil
from collections import deque
from pathlib import Path

import probe as P
import critical_path as C


checks = []
trace = {}
OUT = None


def check(name, passed, observed):
    result = {'name': name, 'passed': bool(passed), 'observed': observed}
    checks.append(result)
    print(('PASS' if passed else 'FAIL'), name, json.dumps(observed), flush=True)


def static(name, obj=None):
    lines = Path(P.MAP).read_text().splitlines()
    for i, line in enumerate(lines):
        words = line.split()
        if words and words[0] in ('.bss.' + name, '.data.' + name,
                                  '.ewram_bss.' + name):
            if obj and obj not in line + lines[i + 1]:
                continue
            return int(words[1], 16) if len(words) > 1 else int(lines[i + 1].split()[0], 16)
    raise KeyError(name)


def section(name):
    lines = Path(P.MAP).read_text().splitlines()
    for i, line in enumerate(lines):
        words = line.split()
        if words and words[0] == name:
            return int(words[1], 16) if len(words) > 1 else int(lines[i + 1].split()[0], 16)
    raise KeyError(name)


def w32(c, address, value):
    P.w16(c, address, value & 65535)
    P.w16(c, address + 2, (value >> 16) & 65535)


def status(c):
    g = P.sym('gGame')
    return {'state': P.r8(c, g), 'area': P.r8(c, g + 1),
            'cell': P.r8(c, g + 2), 'player': P.actor(c, 0),
            'text': P.r8(c, P.sym('gTbActive')),
            'player_health': [P.r16(c, P.sym('gPl')), P.r16(c, P.sym('gPl') + 2)]}


def text_message(c):
    if not P.r8(c, P.sym('gTbActive')):
        return ''
    pointer = P.r32(c, static('sTbText', 'text.o'))
    chars = []
    for i in range(1024):
        value = P.r8(c, pointer + i)
        if not value:
            break
        chars.append(value)
    return bytes(chars).decode('ascii', errors='replace')


def gear_state(c):
    return {name: P.r8(c, static(name, 'gear_menu.o'))
            for name in ('sActive', 'sPage', 'sZoom')}


def nav(c, x, y, facing=0):
    """Navigation only: no state, health, collision, world or actor edits."""
    a = P.sym('gActors')
    w32(c, a + 8, x << 16)
    w32(c, a + 12, y << 16)
    P.w8(c, a + 7, facing)
    P.w8(c, a + 6, facing * 8)
    P.w16(c, P.sym('gPl') + 14, x)
    P.w16(c, P.sym('gPl') + 16, y)


def settle(c, area, cell=None, frames=1200):
    for _ in range(frames):
        if C.gstate(c) == 1 and C.area(c) == area and (cell is None or C.cell(c) == cell):
            return True
        P.run(c, 1)
    return False


def boot():
    c = P.boot(rom=P.ROM)
    C.dismiss(c)
    return c


def snap(c, name):
    P.snap(c, str(OUT / (name + '.png')))


def dry_sewer(c):
    r = P.sym('gRoom')
    w, h = P.r8(c, r), P.r8(c, r + 1)
    ground = [P.r16(c, r + 2 + i * 2) & 65535 for i in range(1024)]
    solid = bytes(P.r8(c, r + 4098 + i) for i in range(4096))
    types = {mt: P.r8(c, P.sym('metatile_type') + mt) for mt in set(ground) if mt != 65535}
    cabinet = (P.r8(c, P.sym('gCabinetActive')),
               P.r16(c, P.sym('gCabinetX')), P.r16(c, P.sym('gCabinetY')))

    def dry(x, y):
        if x < 5 or x + 4 >= w * 16 or y < 8 or y >= h * 16:
            return False
        if types.get(ground[((y - 4) // 16) * 32 + x // 16]) in (2, 3, 16):
            return False
        for sy in range((y - 8) // 8, (y - 1) // 8 + 1):
            for sx in range((x - 5) // 8, (x + 4) // 8 + 1):
                if solid[sy * 64 + sx]:
                    return False
        active, cx, cy = cabinet
        if active and x - 5 <= cx + 11 and x + 4 >= cx - 12 and y - 8 <= cy and y - 1 >= cy - 13:
            return False
        return True

    start = P.player_pos(c)
    todo, seen, prev = deque([start]), {start}, {}
    while todo:
        x, y = todo.popleft()
        for nxt in ((x + 4, y), (x - 4, y), (x, y + 4), (x, y - 4)):
            if nxt not in seen and dry(*nxt):
                seen.add(nxt)
                prev[nxt] = (x, y)
                todo.append(nxt)
    result = {'room_metatiles': [w, h], 'spawn': start, 'dry_spawn': dry(*start),
              'reachable_4px_nodes': len(seen), 'cabinet': cabinet,
              'policy': 'Live Room 8px collision, player 10x8 feet box; feet hazard excludes PIT/WATER/HURT; cabinet collision included; moving NPCs excluded.'}
    for name, target in (('cream', (456, 130)), ('annex', (280, 130))):
        path = []
        p = target
        if target in seen:
            while p != start:
                path.append(p)
                p = prev[p]
            path.append(start)
            path.reverse()
        result[name] = {'approach': target, 'reachable': target in seen,
                        'path_length_px': max(0, len(path) - 1) * 4, 'path': path}
        check('dry ordinary-spawn route to ' + name + ' arch', target in seen and dry(*start),
              {k: v for k, v in result[name].items() if k != 'path'})
    trace['sewer_reachability'] = result


def entrances(c):
    nav(c, 456, 130)
    P.run(c, 2)
    snap(c, '01-sewer-cream-approach')
    P.press(c, 'A', 2, 2)
    ok = settle(c, 3)
    P.run(c, 2)
    arrival = status(c)
    snap(c, '02-cream-entry-stairs')
    check('real A enters Cream at its visible entry stairs', ok and abs(P.player_pos(c)[0] - 400) <= 2 and abs(P.player_pos(c)[1] - 350) <= 2, arrival)
    P.press(c, 'A', 2, 2)
    ok = settle(c, 0)
    P.run(c, 2)
    returned = status(c)
    snap(c, '03-cream-returns-matching-sewer-arch')
    check('real A on entry stairs returns to Cream Sewer arch', ok and P.player_pos(c) == (456, 130), returned)

    nav(c, 280, 130)
    P.run(c, 2)
    P.press(c, 'A', 2, 2)
    ok = settle(c, 4)
    P.run(c, 2)
    snap(c, '04-annex-entry')
    check('real A enters optional Annex', ok, status(c))
    return c


def music(c):
    result = {name: (P.r16(c, P.sym(name)) & 65535 if name in ('gOriginalMusicBgm', 'gOriginalMusicTrack') else P.r32(c, P.sym(name)))
              for name in ('gOriginalMusicBgm', 'gOriginalMusicTrack', 'gOriginalMusicSamples',
                           'gOriginalMusicLoops', 'gOriginalMusicDmaOffset', 'gVBlankHook')}
    result.update({'dma1_control': P.r32(c, 0x040000c4),
                   'dma1_source': P.r32(c, 0x040000bc),
                   'timer0_control': P.r16(c, 0x04000102) & 65535,
                   'timer1_control': P.r16(c, 0x04000106) & 65535})
    return result


def audio_span(c, label, frames=30):
    before = music(c)
    P.run(c, frames)
    after = music(c)
    same = before['gOriginalMusicTrack'] == after['gOriginalMusicTrack'] and before['gOriginalMusicBgm'] == after['gOriginalMusicBgm']
    advanced = after['gOriginalMusicSamples'] > before['gOriginalMusicSamples'] or after['gOriginalMusicLoops'] > before['gOriginalMusicLoops']
    pcm_running = all(s['dma1_control'] == 0xb6400000 and s['timer0_control'] == 0x80 and s['timer1_control'] == 0x84 for s in (before, after))
    # DMA offset is a block base and can remain unchanged during a short span.
    check('music advances during ' + label, same and advanced and pcm_running and before['gVBlankHook'] != 0 and after['gVBlankHook'] != 0,
          {'physical_frames': frames, 'before': before, 'after': after})


def annex_modal_and_exit(c):
    initial = music(c)['gVBlankHook']
    nav(c, 200, 158, 0)  # dry approach below the Inn desk; no purchase made.
    P.run(c, 2)
    P.press(c, 'A', 2, 8)
    modal = section('.ewram_bss.handoff_menu') + 14
    check('real A opens Annex Inn modal', P.r8(c, modal) != 0, {'mode': P.r8(c, modal), 'status': status(c)})
    snap(c, '05-annex-inn-modal')
    audio_span(c, 'Annex Inn modal')
    P.press(c, 'B', 2, 8)
    check('Annex modal closes and preserves original VBlank hook', P.r8(c, modal) == 0 and music(c)['gVBlankHook'] == initial,
          {'mode': P.r8(c, modal), 'hook_before': initial, 'hook_after': music(c)['gVBlankHook']})
    nav(c, 264, 350, 2)
    P.hold(c, 'DOWN', 12)
    ok = settle(c, 0)
    P.run(c, 2)
    snap(c, '06-annex-returns-matching-sewer-arch')
    check('real downward walk leaves Annex at matching Sewer arch', ok and P.player_pos(c) == (280, 130), status(c))


def menu_audio():
    c = boot()
    initial = music(c)['gVBlankHook']
    audio_span(c, 'ordinary Sewer play')
    P.press(c, 'START', 2, 10)
    check('old pause opens from real Start and chains original music hook',
          C.gstate(c) == 4 and P.r32(c, static('sStudyOldHook', 'menu.o')) == initial,
          {'status': status(c), 'saved_hook': P.r32(c, static('sStudyOldHook', 'menu.o'))})
    snap(c, '07-original-pause')
    audio_span(c, 'original pause')
    P.press(c, 'SELECT', 2, 10)
    check('real Select opens Satchel and chains original music hook',
          gear_state(c) == {'sActive': 1, 'sPage': 0, 'sZoom': 0} and P.r32(c, static('sOldHook', 'gear_menu.o')) == initial,
          {'gear': gear_state(c), 'saved_hook': P.r32(c, static('sOldHook', 'gear_menu.o'))})
    snap(c, '08-select-satchel')
    audio_span(c, 'Select Satchel')
    P.press(c, 'R', 2, 10)
    check('real R opens native atlas', gear_state(c) == {'sActive': 1, 'sPage': 1, 'sZoom': 0}, gear_state(c))
    snap(c, '09-satchel-atlas')
    audio_span(c, 'native atlas')
    P.press(c, 'A', 2, 10)
    check('real A opens atlas room zoom', gear_state(c) == {'sActive': 1, 'sPage': 1, 'sZoom': 1}, gear_state(c))
    snap(c, '10-native-atlas-zoom')
    audio_span(c, 'native atlas room zoom')
    P.press(c, 'START', 2, 10)
    check('Satchel atlas returns to play and restores music hook', C.gstate(c) == 1 and music(c)['gVBlankHook'] == initial,
          {'initial_hook': initial, 'after': music(c), 'status': status(c)})
    audio_span(c, 'play after nested pause/Satchel/atlas')


def world_flags(c):
    w = P.sym('gWorld')
    base = w + 4 + 25 * 13
    return {'flags': [P.r8(c, w + 4 + i * 13 + 11) for i in range(25)],
            'opened': [P.r8(c, w + 4 + i * 13 + 4) for i in range(25)],
            'myst_flags': [P.r8(c, base + 63 + i) for i in range(25)]}


def full_inventory(c):
    """Inventory-only negative control; leaves all quest/world/health alone."""
    pl = P.sym('gPl')
    P.w8(c, pl + 6, 9)  # keys
    P.w8(c, pl + 7, 99)
    P.w8(c, pl + 8, 0x7f)
    P.w8(c, pl + 35, 99)  # arrows
    P.w8(c, pl + 36, 0x1f)
    inv = P.sym('gLegacyInventory')
    for i in range(16):
        P.w8(c, inv + i, 255)  # all item owned bits, not seen/progression.
    P.w16(c, inv + 32, 255)  # all sword skills
    # bag/quiver capacities and passive upgrades; no world reward grants.
    for off, value in ((46, 4), (47, 2), (48, 2), (49, 1), (50, 1), (51, 1)):
        P.w8(c, inv + off, value)


def load_forest_cell(c, cell, side):
    for name, value in (('sNextArea', 1), ('sNextCell', cell),
                        ('sNextSide', side), ('sTransPhase', 0)):
        P.w8(c, static(name), value)
    P.w8(c, P.sym('gGame'), 2)
    return settle(c, 1, cell)


def gate_tiles(side):
    return (((15, 1), (16, 1)), ((31, 11), (31, 12)),
            ((15, 23), (16, 23)), ((0, 11), (0, 12)))[side]


def tile_states(c, side):
    r = P.sym('gRoom')
    result = []
    for x, y in gate_tiles(side):
        mt = P.r16(c, r + 2 + (y * 32 + x) * 2) & 65535
        result.append({'x': x, 'y': y, 'mt': mt, 'type': P.r8(c, P.sym('metatile_type') + mt)})
    return result


def trial_negative():
    for i, (name, equip) in enumerate((('bomb', 2), ('lamp', 3), ('cape', 4))):
        c = boot()
        before_flags = world_flags(c)
        full_inventory(c)
        w = C.world(c)
        cell, side = w['gate_cell'][i], w['gate_side'][i]
        loaded = load_forest_cell(c, cell, side)
        before = tile_states(c, side)
        check(name + ' test starts with full gear and no earned trial prizes',
              loaded and all(not (f & 8) for f in before_flags['flags']) and all(not (f & 4) for f in before_flags['myst_flags']),
              {'gate_cell': cell, 'gate_side': side, 'key_cells': w['key_cell'], 'tiles': before, 'inventory': {'items': P.r8(c, P.sym('gPl') + 8), 'items2': P.r8(c, P.sym('gPl') + 36)}})
        x, y, direction = C.door_inside(side)
        nav(c, x, y, side)
        P.w8(c, P.sym('gPl') + 9, equip)
        P.w8(c, P.sym('gPl') + 10, 1)
        P.w8(c, P.sym('gPl') + 11, 5)
        P.hold(c, direction, 24 if name != 'cape' else 10)
        P.run(c, 2)
        evidence = []
        c.set_keys(P.key(c, 'A'), *([P.key(c, direction)] if name == 'cape' else []))
        for _ in range(2 if name != 'bomb' else 30):
            P.run(c, 1)
            evidence.append({'pos': P.player_pos(c), 'state': P.actor(c, 0)['state'],
                             'charge': P.r8(c, P.sym('gBombChargeTicks')),
                             'lamp': P.r8(c, P.sym('gPl') + 23)})
        c.set_keys(*([P.key(c, direction)] if name == 'cape' else []))
        for f in range(100):
            P.run(c, 1)
            if f % 5 == 0:
                evidence.append({'pos': P.player_pos(c), 'state': P.actor(c, 0)['state'],
                                 'charge': P.r8(c, P.sym('gBombChargeTicks')),
                                 'lamp': P.r8(c, P.sym('gPl') + 23),
                                 'text': P.r8(c, P.sym('gTbActive'))})
        c.set_keys()
        after = tile_states(c, side)
        after_flags = world_flags(c)
        snap(c, 'trial-' + name + '-no-bypass')
        used = (any(e.get('charge') for e in evidence) and P.r8(c, P.sym('gPl') + 7) == 98 if name == 'bomb' else
                any(e.get('lamp') for e in evidence) if name == 'lamp' else
                any(e['state'] == 5 for e in evidence))
        prizes_unchanged = all((a & 8) == (b & 8) for a, b in zip(before_flags['flags'], after_flags['flags'])) and before_flags['myst_flags'] == after_flags['myst_flags']
        check(name + ' actual input activates its native tool', used, {'evidence': evidence[:5], 'bombs': P.r8(c, P.sym('gPl') + 7)})
        message = text_message(c)
        check(name + ' cannot bypass original mandatory trial gate',
              C.area(c) == 1 and C.cell(c) == cell and before == after and before_flags['opened'] == after_flags['opened'] and prizes_unchanged and 'trial seal' in message,
              {'before': before, 'after': after, 'opened_unchanged': before_flags['opened'] == after_flags['opened'],
               'trial_prizes_unchanged': prizes_unchanged, 'message': message, 'status': status(c)})
        trace['trial_' + name] = {'world': w, 'before_flags': before_flags, 'after_flags': after_flags, 'frames': evidence}


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    OUT = args.out.resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    # Separate path avoids loading or sharing another review's disk SRAM.
    private = OUT / 'private'
    private.mkdir(exist_ok=True)
    P.ROM = str(private / 'bartgame.gba')
    shutil.copyfile(args.bundle / 'bartgame.gba', P.ROM)
    for sav in private.glob('*.sav'):
        sav.unlink()
    P.MAP = str(args.bundle / 'bartgame.map')
    P._syms = None
    completed = False
    try:
        c = boot()
        dry_sewer(c)
        entrances(c)
        annex_modal_and_exit(c)
        menu_audio()
        trial_negative()
        completed = True
    finally:
        report = {'rom_sha256': hashlib.sha256(Path(P.ROM).read_bytes()).hexdigest(),
                  'source_commit': (args.bundle / 'source-commit.txt').read_text().strip(),
                  'tool_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'checks': checks, 'trace': trace,
                  'fixtures': __doc__, 'completed': completed,
                  'passed': completed and bool(checks) and all(c['passed'] for c in checks)}
        (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
