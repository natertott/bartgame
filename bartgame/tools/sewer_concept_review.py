"""Record opt-in Drain art from actual mGBA runs on unchanged room terrain.

Each view boots the same seeded game and moves only the player's position,
safe position and facing before an idle camera-settle period. NPCs stay alive,
and no terrain, action state, pose or animation frame is assigned. Dialogue and
shop clips use ordinary A presses. Native PNGs are exact 240x160 framebuffers;
GIFs sample every second video frame at nearest-neighbour2x, and MP4s retain
all video frames at the native GBA rate. Review captions sit outside gameplay.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageFont
import probe as P
import critical_path as C
import bloom_probe as B
from bloom_suite_gallery import write_gif

FPS = 16777216 / 280896
ROOT = Path(__file__).resolve().parent.parent
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
VIEWS = (
    ('market', (72, 115), 0, 288),
    ('ladder', (152, 80), 0, 128),
    ('wizard', (344, 118), 0, 288),
    ('bridge', (240, 174), 0, 128),
    ('left-channel', (120, 140), 0, 128),
    ('right-outfall', (424, 132), 0, 128),
    ('lower-left', (120, 254), 0, 128),
    ('lower-right', (360, 254), 0, 128),
)
HERO_SHEETS = ('HERO', 'SWORD', 'SHIELD', 'BLOOMFX', 'BLOOMSHADOW', 'GLITTER')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def configure(frozen):
    frozen = Path(frozen)
    P.ROM = str(frozen/'bartgame.gba')
    defs = B.configure(SimpleNamespace(map=str(frozen/'bartgame.map'),
                                     assets_header=str(frozen/'assets.h')))
    return defs


def boot(frozen):
    defs = configure(frozen)
    c = P.boot(rom=P.ROM, seed=0xB4A7)
    C.dismiss(c)
    assert C.area(c) == 0 and C.gstate(c) == 1
    return c, defs


def room_snapshot(c):
    room = P.sym('gRoom')
    desc = P.sym('room_defs')
    w, h = P.r8(c, room), P.r8(c, room+1)
    ground = P.r32(c, desc+4)
    overlay = P.r32(c, desc+8)
    objects = P.r32(c, desc+12)
    count = P.r8(c, desc+16)
    return {
        'size': [w, h],
        'ground': digest(B.bytes_at(c, ground, w*h*2)),
        'overlay': digest(B.bytes_at(c, overlay, w*h*2)),
        'objects': list(B.bytes_at(c, objects, count*4)),
        'loaded_ground': digest(B.bytes_at(c, room+2, 2048)),
        'loaded_overlay': digest(B.bytes_at(c, room+2050, 2048)),
        'solid': digest(B.bytes_at(c, room+4098, 4096)),
        'underlay': digest(B.bytes_at(c, room+8194, 2048)),
    }


def static_snapshot(c, defs):
    sheets = {}
    for name in HERO_SHEETS:
        index = defs['SHEET_'+name]
        meta = B.sheet_metadata(c, index)
        sheets[name.lower()] = {
            **{k: v for k, v in meta.items() if k != 'source'},
            'pixels_sha256': digest(B.bytes_at(c, meta['source'], meta['tiles']*32)),
            'palette_sha256': digest(B.bytes_at(c, P.sym('pal_obj')+meta['pal']*32, 32)),
        }
    physical = {}
    for name in ('type', 'coll', 'prop', 'glitter'):
        physical[name] = digest(B.bytes_at(c, P.sym('metatile_'+name), defs['METATILE_COUNT']))
    return {'room': room_snapshot(c), 'preserved_sheets': sheets,
            'physical_metadata': physical,
            'sword_study': defs.get('BLOOM_SWING_STUDY'),
            'sword_updates': defs.get('BLOOM_SWING_FRAMES')}


def tileset(c, defs):
    at = P.sym('tilesets') + defs['TS_SEWER']*28
    count = P.r16(c, at+4)&65535
    mapping = P.r32(c, at+8)
    anim_at = P.r32(c, at+12)
    animations = []
    for i in range(P.r8(c, at+16)):
        ta = anim_at+i*8
        tile, frames, speed, source = (P.r16(c, ta)&65535, P.r8(c, ta+2),
                                       P.r8(c, ta+3), P.r32(c, ta+4))
        animations.append({'tile': tile, 'frames': frames, 'speed': speed,
                           'frame_hashes': [digest(B.bytes_at(c, source+f*128, 128)) for f in range(frames)]})
    # Prefer the main channel's repeated liquid panels over incidental candles.
    selected = []
    for name in ('SWH_235', 'SWH_236', 'SWH_245', 'SWH_246', 'SWH_334', 'SWH_335'):
        mt = defs.get('MT_'+name)
        if mt is None:
            continue
        tile = (P.r16(c, mapping+mt*8)&65535)&1023
        match = next((a for a in animations if a['tile'] == tile), None)
        if match and len(set(match['frame_hashes'])) > 1:
            selected.append({'metatile': name.lower(), **match})
    if not selected:
        selected = [a for a in animations if len(set(a['frame_hashes'])) > 1][:1]
    return {'tile_count': count, 'palette_count': P.r8(c, at+24),
            'animations': animations, 'flow': selected}


def frame_catalog(c, defs):
    result = {}
    for name in ('PEDDLER_HEAD', 'PEDDLER_BODY', 'GATEKEEPER', 'WISP'):
        meta = B.sheet_metadata(c, defs['SHEET_'+name])
        n = defs['SHEET_'+name+'_FRAMES']
        names = {v: k[len('F_'+name+'_'):].lower() for k, v in defs.items() if k.startswith('F_'+name+'_')}
        blobs = {}
        for frame in range(n):
            value = digest(B.bytes_at(c, meta['source']+frame*meta['frame_tiles']*32, meta['frame_tiles']*32))
            blobs.setdefault(value, []).append(names.get(frame, str(frame)))
        result[name.lower()] = {'meta': meta, 'frames': blobs}
    return result


def npc_hardware(c, defs, catalog):
    entries = B.oam(c)
    result = {}
    positions = {}
    for name, desc in catalog.items():
        meta = desc['meta']
        entry = next((o for o in entries if o['pal'] == meta['pal'] and
                      o['shape'] == meta['shape'] and o['size'] == meta['size']), None)
        if entry is None:
            result[name] = []
            continue
        data = B.bytes_at(c, 0x06010000+entry['tile']*32, meta['frame_tiles']*32)
        result[name] = desc['frames'].get(digest(data), ['unmatched'])
        positions[name] = [entry['x'], entry['y']]
    anchor = None
    if 'gatekeeper' in positions and 'wisp' in positions:
        anchor = [positions['wisp'][i]-positions['gatekeeper'][i] for i in range(2)]
    peddler_anchor = None
    if 'peddler_head' in positions and 'peddler_body' in positions:
        # OAM positions wrap at512x256. Keep the small relative offset even
        # when the off-screen head and body straddle a wrapping boundary.
        delta = [positions['peddler_head'][i]-positions['peddler_body'][i] for i in range(2)]
        peddler_anchor = [(delta[0]+256)%512-256, (delta[1]+128)%256-128]
    return result, anchor, peddler_anchor, entries


def safe(c, px, py):
    room = P.sym('gRoom')
    if not (8 <= px < P.r8(c, room)*16-8 and 12 <= py < P.r8(c, room+1)*16):
        return False
    if any(P.r8(c, room+4098+(y//8)*64+x//8)
           for y in (py-8, py-4, py-1) for x in (px-5, px, px+4)):
        return False
    mt = P.r16(c, room+2+(((py-4)//16)*32+px//16)*2)&65535
    return P.r8(c, P.sym('metatile_type')+mt) == 0


def position(c, point, facing):
    assert safe(c, *point), ('unsafe fixture', point)
    actor, pl = P.sym('gActors'), P.sym('gPl')
    assert P.r8(c, actor+2) == 0, 'position fixture expects ordinary standing state'
    # Q16 positions and the game's fall return point; no animation/state writes.
    P.w16(c, actor+8, 0); P.w16(c, actor+10, point[0])
    P.w16(c, actor+12, 0); P.w16(c, actor+14, point[1])
    P.w16(c, pl+14, point[0]); P.w16(c, pl+16, point[1])
    P.w8(c, actor+7, facing); P.w8(c, actor+6, facing*8)
    P.run(c, 96)


def gif_durations(count, step=2):
    ticks = list(range(0, count, step))
    return [round(b/FPS*100)*10-round(a/FPS*100)*10
            for a, b in zip(ticks, ticks[1:]+[count])]


def mp4(directory, destination):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS),
                    '-i', str(directory/'frame-%03d.png'), '-vf', 'scale=720:480:flags=neighbor',
                    '-an', '-c:v', 'libx264', '-threads', '2', '-crf', '17', '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart', str(destination)], check=True)


class Review:
    def __init__(self, args):
        self.args = args
        self.frozen = Path(args.frozen)
        self.out = Path(args.out)
        self.out.mkdir(parents=True, exist_ok=True)
        self.sha = digest((self.frozen/'bartgame.gba').read_bytes())
        self.coverage = json.loads((self.frozen/'coverage.json').read_text())
        self.concept = self.coverage.get('sewer_concept')
        self.variant = self.concept['recipe']['id'] if self.concept else 0
        self.rows, self.checks = [], []
        c, defs = boot(args.baseline)
        self.baseline = static_snapshot(c, defs)
        c, self.defs = boot(self.frozen)
        self.snapshot = static_snapshot(c, self.defs)
        self.ts = tileset(c, self.defs)
        self.rail = None
        if 'SHEET_SEWERRAIL' in self.defs:
            meta = B.sheet_metadata(c, self.defs['SHEET_SEWERRAIL'])
            self.rail = {**meta, 'pixels_sha256': digest(B.bytes_at(c, meta['source'], meta['tiles']*32))}
        self.validate_static()

    def check(self, name, condition, detail=None):
        row = {'name': name, 'passed': bool(condition)}
        if detail is not None:
            row['detail'] = detail
        self.checks.append(row)
        if not condition:
            print('FAIL', name, detail, flush=True)
        return bool(condition)

    def validate_static(self):
        for name, value in self.baseline['room'].items():
            self.check('room '+name+' unchanged', self.snapshot['room'][name] == value)
        for name, value in self.baseline['preserved_sheets'].items():
            self.check(name+' source pixels/canvas/palette unchanged', self.snapshot['preserved_sheets'][name] == value)
        for name, value in self.baseline['physical_metadata'].items():
            self.check('all metatile '+name+' metadata unchanged', self.snapshot['physical_metadata'][name] == value)
        self.check('Step-and-cut remains selected', self.snapshot['sword_study'] == 3 and self.snapshot['sword_updates'] == 18)
        self.check('native sewer BG budget', self.ts['tile_count'] <= 1024, self.ts['tile_count'])
        self.check('native sewer palette budget', self.ts['palette_count'] <= 12, self.ts['palette_count'])
        self.check('flowing channel has distinct source animation frames', bool(self.ts['flow']), self.ts['flow'])
        if self.rail:
            self.check('foreground handrail is a legal two-tile16x8 sprite',
                       self.rail['width'] == 16 and self.rail['height'] == 8 and
                       self.rail['tiles'] == self.rail['frame_tiles'] == 2)

    def record(self, name, point, facing, total, dialogue=None):
        c, defs = boot(self.frozen)
        initial_room = room_snapshot(c)
        position(c, point, facing)
        catalog = frame_catalog(c, defs)
        images, trace = [], []
        rail_hardware = None
        raw = self.out/'all-frames'/name
        raw.mkdir(parents=True, exist_ok=True)
        directory = self.out/name
        directory.mkdir(exist_ok=True)
        gframe = P.r32(c, P.sym('gFrame'))
        updates = P.r32(c, P.sym('gGame')+8)
        shop_at = B.static_symbol('sShopActive')
        for tick in range(total):
            c.clear_keys(*range(10))
            if dialogue and 8 <= tick < 10:
                c.set_keys(P.key(c, 'A'))
            c.run_frame()
            image = c.bg_video.to_pil().convert('RGB').copy()
            image.save(raw/f'frame-{tick:03}.png')
            images.append(image)
            frames, anchor, peddler_anchor, entries = npc_hardware(c, defs, catalog)
            row = {'video_tick': tick, 'frame': P.r32(c, P.sym('gFrame')),
                   'game_updates': P.r32(c, P.sym('gGame')+8),
                   'state': C.gstate(c), 'area': C.area(c),
                   'hero_state': P.r8(c, P.sym('gActors')+2),
                   'position': list(P.player_pos(c)),
                   'camera': [P.r16(c, P.sym('gCamX')), P.r16(c, P.sym('gCamY'))],
                   'npc_frames': frames, 'flame_anchor': anchor,
                   'peddler_head_body_anchor': peddler_anchor,
                   'oam': P.r8(c, P.sym('gOamCount')),
                   'glitter_sites': P.r16(c, P.sym('gAmbientSiteCount')),
                   'glitter_potential': P.r8(c, P.sym('gAmbientPotential')),
                   'glitter_visible': P.r8(c, P.sym('gAmbientVisible')),
                   'textbox': P.r8(c, P.sym('gTbActive')),
                   'shop': P.r8(c, shop_at),
                   'flow_frames': [digest(B.bytes_at(c, 0x06000000+a['tile']*32, 128)) for a in self.ts['flow']]}
            if self.rail:
                candidates = [o for o in entries if o['pal'] == self.rail['pal'] and
                              o['shape'] == self.rail['shape'] and o['size'] == self.rail['size']]
                cx, cy = row['camera']
                positions = [[o['x']+cx, o['y']+cy] for o in candidates]
                row['rail_oam_count'] = len(candidates)
                row['rail_grid_and_bridge_opening_valid'] = all(
                    16 <= x < 464 and x%16 == 0 and not 224 <= x < 256 and y == 136
                    for x, y in positions)
                if candidates and rail_hardware is None:
                    o = candidates[0]
                    hardware_sha = digest(B.bytes_at(c, 0x06010000+o['tile']*32, 64))
                    rail_hardware = {'positions': positions, 'source_sha256': self.rail['pixels_sha256'],
                                     'hardware_sha256': hardware_sha, 'sample_video_tick': tick}
            trace.append(row)
        c.clear_keys(*range(10))
        selected = sorted({0, 8, total//4, total//2, total*3//4, total-1})
        for tick in selected:
            images[tick].save(directory/f'frame-{tick:03}.png')
        images[total//2].save(self.out/(name+'.png'))
        gif = write_gif([im.resize((480, 320), Image.Resampling.NEAREST) for im in images[::2]],
                        gif_durations(total), self.out/(name+'.gif'))
        if not self.args.no_video:
            mp4(raw, self.out/(name+'.mp4'))
        film = Image.new('RGB', (960, 4*178+22), '#101820')
        draw = ImageDraw.Draw(film)
        draw.text((6, 4), name+' / chronological actual mGBA frames', font=FONT, fill='#f0d898')
        for i in range(16):
            tick = round(i*(total-1)/15)
            x, y = (i%4)*240, 22+(i//4)*178
            film.paste(images[tick], (x, y))
            draw.text((x+4, y+162), 'video '+str(tick), font=FONT, fill='#e0dcc0')
        film.save(self.out/(name+'-filmstrip.png'))
        expected_anchor = [defs['WISP_X'], defs['WISP_Y']]
        anchors = [r['flame_anchor'] for r in trace if r['flame_anchor'] is not None]
        checks = {
            'native_room_remains_sewer': all(r['area'] == 0 for r in trace),
            'room_layout_and_collision_unchanged': room_snapshot(c) == initial_room,
            'both_original_npcs_retained': all(P.actor(c, i)['kind'] == 5 for i in (1, 2)),
            'hardware_oam_within_limit': max(r['oam'] for r in trace) <= 128,
            'glitter_budget_retained': all(r['glitter_potential'] <= 24 for r in trace),
            'wizard_flame_anchor_matches_authored_staff': bool(anchors) and all(a == expected_anchor for a in anchors),
            'npc_hardware_frames_match_rom': all('unmatched' not in fs for r in trace for fs in r['npc_frames'].values()),
        }
        if not dialogue:
            checks['standing_camera_fixture_stays_on_safe_ground'] = all(r['hero_state'] == 0 and r['position'] == list(point) for r in trace)
            checks['ordinary_idle_game_remains_playing'] = all(r['state'] == 1 for r in trace)
            checks['flowing_water_changes_in_hardware_vram'] = any(len({r['flow_frames'][i] for r in trace}) > 1 for i in range(len(self.ts['flow'])))
        elif dialogue == 'shop':
            checks['ordinary_A_opens_actual_shop'] = any(r['shop'] for r in trace)
        else:
            checks['ordinary_A_opens_actual_wizard_text'] = any(r['textbox'] for r in trace)
        # Off-screen NPCs have wrapped OAM coordinates; the relative anchor is
        # still valid when both are represented. At the far left/right one may
        # be entirely culled, so no-view clips mark this check inapplicable.
        if not anchors:
            checks['wizard_flame_anchor_matches_authored_staff'] = None
        if self.rail:
            checks['foreground_rail_leaves_physical_bridge_opening_clear'] = all(r['rail_grid_and_bridge_opening_valid'] for r in trace)
            if rail_hardware:
                checks['foreground_rail_uses_exact_two_tile_rom_art'] = rail_hardware['source_sha256'] == rail_hardware['hardware_sha256']
            if 0 <= 136-trace[0]['camera'][1] < 160:
                checks['visible_foreground_rail_is_present_in_hardware_oam'] = bool(rail_hardware)
        peddler_idle = None
        if self.variant and name == 'market' and not dialogue:
            # Identify the image actually uploaded into OBJ VRAM. The logic
            # clock may already be preparing the next upload, so it is not a
            # reliable source for this displayed head/body phase comparison.
            expected = {'rest': [8, 6], 'breathe': [8, 7]}
            named = {pose: [r for r in trace if pose in r['npc_frames']['peddler_body']]
                     for pose in expected}
            unique = {pose: [r for r in trace if r['npc_frames']['peddler_body'] == [pose]]
                      for pose in expected}
            checks['peddler_idle_displays_rest_and_breathe_in_hardware'] = all(named.values())
            checks['peddler_idle_has_unambiguous_hardware_samples_for_both_poses'] = all(unique.values())
            checks['peddler_head_and_body_breathing_phase_stays_connected'] = all(unique.values()) and all(
                r['peddler_head_body_anchor'] == expected[pose]
                for pose, rows in unique.items() for r in rows)
            peddler_idle = {
                'method': 'Exact ROM-body bytes identify displayed rest/breathe; only unique pose matches test the OAM head/body offset. No current-frame timer assumption.',
                'expected_head_body_anchors': expected,
                'matched_pose_samples': {pose: len(rows) for pose, rows in named.items()},
                'unambiguous_pose_samples': {pose: len(rows) for pose, rows in unique.items()},
                'observed_head_body_anchors': {pose: sorted({tuple(r['peddler_head_body_anchor'])
                    for r in rows if r['peddler_head_body_anchor'] is not None}) for pose, rows in unique.items()},
                'unambiguous_video_ticks': {pose: [r['video_tick'] for r in rows] for pose, rows in unique.items()},
            }
        for label, condition in checks.items():
            if condition is not None:
                self.check(name+': '+label, condition)
        row = {'name': name, 'variant': self.variant, 'seed': '0xb4a7',
               'position_fixture': list(point), 'facing_fixture': facing,
               'camera': trace[0]['camera'], 'video_frames': total, 'fps': FPS,
               'dialogue': dialogue, 'input': {'A_down': 8, 'A_up': 10} if dialogue else {},
               'native_frames': [name+f'/frame-{tick:03}.png' for tick in selected],
               'preview_png': name+'.png', 'gif': name+'.gif', 'gif_metadata': gif,
               'filmstrip': name+'-filmstrip.png', 'video': None if self.args.no_video else name+'.mp4',
               'full_frames': str(raw), 'checks': checks, 'trace': trace,
               'vblanks': P.r32(c, P.sym('gFrame'))-gframe,
               'game_updates': P.r32(c, P.sym('gGame')+8)-updates,
               'foreground_rail_hardware': rail_hardware,
               'peddler_idle_hardware': peddler_idle,
               'npc_frame_union': {who: sorted({f for r in trace for f in r['npc_frames'][who]}) for who in catalog}}
        self.rows.append(row)
        self.save()
        print('CAPTURE', self.variant, name, 'PASS' if all(v is True or v is None for v in checks.values()) else 'FAIL', flush=True)

    def save(self):
        failures = [r for r in self.checks if not r['passed']]
        report = {'variant': self.variant, 'concept': self.concept, 'rom_sha256': self.sha,
                  'emulator': 'mGBA 0.10.5', 'fps': FPS, 'method': __doc__.strip(),
                  'baseline_rom_sha256': digest((Path(self.args.baseline)/'bartgame.gba').read_bytes()),
                  'static_snapshot': self.snapshot, 'tileset': self.ts,
                  'foreground_rail': self.rail,
                  'captures': self.rows, 'capture_count': len(self.rows),
                  'passed': len(self.checks)-len(failures), 'total': len(self.checks),
                  'checks': self.checks, 'failures': failures}
        (self.out/'capture.json').write_text(json.dumps(report, indent=2)+'\n')

    def run(self):
        wanted = set(self.args.views.split(',')) if self.args.views else None
        for name, point, face, length in VIEWS:
            if wanted is None or name in wanted:
                self.record(name, point, face, length)
        if not self.args.no_dialogue:
            self.record('peddler-shop', (72, 112), 0, 128, 'shop')
            self.record('wizard-dialogue', (344, 118), 0, 128, 'wizard')
        self.check('frozen ROM unchanged during recording', digest((self.frozen/'bartgame.gba').read_bytes()) == self.sha)
        self.save()
        failures = [r for r in self.checks if not r['passed']]
        print('RESULT', 'FAIL' if failures else 'PASS', str(len(self.checks)-len(failures))+'/'+str(len(self.checks)), flush=True)
        return int(bool(failures))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--frozen', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--baseline', default='/workspace/setup/step-and-cut/frozen')
    ap.add_argument('--no-video', action='store_true')
    ap.add_argument('--no-dialogue', action='store_true')
    ap.add_argument('--views', help='Comma-separated subset of the eight authored viewpoints')
    return Review(ap.parse_args()).run()


if __name__ == '__main__':
    raise SystemExit(main())
