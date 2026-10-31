#!/usr/bin/env python3
"""Record enemy alternatives from actual mGBA AI and ordinary combat.

The seed, room transition, safe player position/facing, inventory/healing and
removal of unrelated actors are disclosed fixtures. Boss HP fixtures select
the existing phase thresholds; they never assign an AI state/timer, body pose,
animation phase or height. Every enemy comes from the real generated room.
Source atlases separately establish complete authored-frame coverage.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageFont
import probe as P
import bloom_probe as B
import critical_path as C
import lift_probe as L
from sewer_concept_review import safe, gif_durations
from bloom_suite_gallery import write_gif

FPS = 16777216 / 280896
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
NAMES = ('pursuer', 'flyer', 'shooter', 'hopper', 'melee', 'boss')
MECHANIC_FIELDS = ('kind', 'type', 'state', 'timer', 'timer2', 'dir', 'facing',
                   'x_q16', 'y_q16', 'z_q16', 'zvel_q16', 'speed', 'hp',
                   'iframes', 'knockback_timer', 'flags', 'damage', 'v')

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def s32(value):
    return value - (1 << 32) if value >= (1 << 31) else value

class Review:
    def __init__(self, args):
        self.args = args
        self.frozen, self.out = Path(args.frozen), Path(args.out)
        self.out.mkdir(parents=True, exist_ok=True)
        P.ROM = str(self.frozen / 'bartgame.gba')
        self.defs = B.configure(SimpleNamespace(map=str(self.frozen / 'bartgame.map'),
                                               assets_header=str(self.frozen / 'assets.h')))
        C.mt = lambda name: self.defs['MT_' + name]
        self.variant = self.defs.get('BART_ENEMY_VARIANT', 0)
        self.rows, self.checks = [], []
        self.sheet_meta = {}
        self.target, self.kind, self.c = None, None, None
        self.context = {}
        try:
            self.presented = P.sym('gEnemyPresentedFrame')
        except KeyError:
            self.presented = None
        try:
            self.rng = B.static_symbol('sRand')
        except KeyError:
            self.rng = None

    def check(self, name, ok, detail=None):
        row = {'name': name, 'passed': bool(ok)}
        if detail is not None:
            row['detail'] = detail
        self.checks.append(row)
        if not ok:
            print('FAIL', name, detail, flush=True)

    def enemies(self):
        return [(i, P.actor(self.c, i)) for i in range(1, 96)
                if P.r8(self.c, P.sym('gActors') + i * 64) == 2]

    def target_live(self):
        if self.target is None:
            return False
        at = P.sym('gActors') + self.target * 64
        return P.r8(self.c, at) == 2 and P.r8(self.c, at + 1) == self.kind

    def actor_state(self, index):
        at = P.sym('gActors') + index * 64
        return {
            'kind': P.r8(self.c, at), 'type': P.r8(self.c, at + 1),
            'state': P.r8(self.c, at + 2), 'timer': P.r8(self.c, at + 4),
            'timer2': P.r8(self.c, at + 5), 'dir': P.r8(self.c, at + 6),
            'facing': P.r8(self.c, at + 7),
            'x_q16': s32(P.r32(self.c, at + 8)),
            'y_q16': s32(P.r32(self.c, at + 12)),
            'z_q16': s32(P.r32(self.c, at + 16)),
            'zvel_q16': s32(P.r32(self.c, at + 20)),
            'speed': P.r16(self.c, at + 24), 'hp': P.r16(self.c, at + 26),
            'iframes': P.r8(self.c, at + 28),
            'knockback_timer': P.r8(self.c, at + 29), 'flags': P.r8(self.c, at + 31),
            'ai_frame': P.r8(self.c, at + 37),
            'presented_frame': P.r8(self.c, self.presented + index) if self.presented else P.r8(self.c, at + 37),
            'sheet': P.r8(self.c, at + 36), 'damage': P.r8(self.c, at + 47),
            'tile': P.r16(self.c, at + 44) & 65535, 'palette': P.r8(self.c, at + 46),
            'v': list(B.bytes_at(self.c, at + 48, 6)),
        }

    def state(self):
        c = self.c
        projectiles = []
        for i in range(1, 96):
            at = P.sym('gActors') + i * 64
            if P.r8(c, at) == 3:
                a = self.actor_state(i)
                projectiles.append({k: a[k] for k in ('type', 'dir', 'x_q16', 'y_q16', 'speed', 'damage')}
                                   | {'friendly': a['v'][0]})
        target = self.actor_state(self.target) if self.target_live() else None
        body_oam = []
        if target:
            sheet_id = target['sheet']
            if sheet_id not in self.sheet_meta:
                self.sheet_meta[sheet_id] = B.sheet_metadata(c, sheet_id)
            sheet = self.sheet_meta[sheet_id]
            streamed = self.kind == 5 and self.variant
            end = target['tile'] + (sheet['frame_tiles'] if streamed else sheet['tiles'])
            body_oam = [o for o in B.oam(c) if target['tile'] <= o['tile'] < end
                        and o['shape'] == sheet['shape'] and o['size'] == sheet['size']
                        and o['pal'] == target['palette']]
        pl = P.sym('gPl')
        return {
            'frame': P.r32(c, P.sym('gFrame')),
            'updates': P.r32(c, P.sym('gGame') + 8),
            'game_state': C.gstate(c), 'area': C.area(c), 'cell': C.cell(c),
            'hero': self.actor_state(0), 'hero_hp': P.r16(c, pl),
            'target': target, 'projectiles': projectiles,
            'enemy_count': len(self.enemies()),
            'target_hardware_oam': body_oam,
            'rng': P.r32(c, self.rng) if self.rng else None,
            'camera': [P.r16(c, P.sym('gCamX')), P.r16(c, P.sym('gCamY'))],
            'oam_count': P.r8(c, P.sym('gOamCount')),
        }

    def heal(self):
        pl = P.sym('gPl')
        P.w16(self.c, pl + 2, 80)
        P.w16(self.c, pl, 80)

    def position(self, point, facing=None):
        assert safe(self.c, *point), ('unsafe player position', point)
        at, pl = P.sym('gActors'), P.sym('gPl')
        for off, value in ((8, point[0]), (12, point[1])):
            P.w16(self.c, at + off, 0)
            P.w16(self.c, at + off + 2, value)
        P.w16(self.c, pl + 14, point[0])
        P.w16(self.c, pl + 16, point[1])
        if facing is not None:
            P.w8(self.c, at + 7, facing)
            P.w8(self.c, at + 6, facing * 8)

    def enter(self, kind):
        self.kind = kind
        for seed in (0xB4A7, 6, 7, 11):
            self.c = P.boot(rom=P.ROM, seed=seed)
            C.dismiss(self.c)
            world = C.world(self.c)
            P.enter_forest(self.c)
            # Compare the same art/AI across coherent natural materials:
            # healthy pursuers/flyers, intermediate hopper, blighted shooter
            # and heavy. An unavailable stage falls back deterministically.
            preferred_stage = (0, 0, 2, 1, 3, 3)[kind]
            cells = [world['goal']] if kind == 5 else sorted(
                range(25), key=lambda cell: (abs(world['cells'][cell]['stage'] - preferred_stage), cell))
            for cell in cells:
                desc = world['cells'][cell]
                L.warp(self.c, cell, next(i for i, gate in enumerate(desc['gate']) if gate))
                C.dismiss(self.c)
                choices = [(i, a) for i, a in self.enemies() if a['type'] == kind]
                for index, actor in choices:
                    # A safe near target places its AI within its genuine
                    # detection/attack range, without changing enemy state.
                    offsets = ((56, 8), (-56, 8), (48, 16), (-48, 16)) if kind == 5 else ()
                    offsets += ((0, 40), (40, 0), (-40, 0), (0, -40),
                                             (32, 24), (-32, 24), (24, -32), (-24, -32),
                                             (0, 56), (56, 0), (-56, 0), (0, -56))
                    points = [(actor['x'] + dx, actor['y'] + dy) for dx, dy in offsets]
                    point = next((p for p in points if safe(self.c, *p)), None)
                    if point is None:
                        continue
                    self.target = index
                    # Remove unrelated actors, preserving the target and
                    # every naturally generated terrain/prop placement.
                    for other in range(1, 96):
                        if other != index:
                            P.w8(self.c, P.sym('gActors') + other * 64, 0)
                    self.position(point, 0)
                    self.heal()
                    pl = P.sym('gPl')
                    P.w8(self.c, pl + 8, P.r8(self.c, pl + 8) | 1)
                    P.w8(self.c, pl + 9, 0)
                    P.w8(self.c, pl + 10, 1)  # B holds the existing sword.
                    P.w8(self.c, pl + 11, 0)
                    # Follow the player's fixture through the ordinary eased
                    # camera; never assign camera/AI state to make a picture.
                    for _ in range(100):
                        self.heal()
                        self.c.run_frame()
                    self.context = {'seed': seed, 'cell': cell, 'stage': desc['stage'],
                                    'natural_spawn_index': index, 'kind': kind,
                                    'player_position_fixture': list(point),
                                    'player_health_fixture': 80,
                                    'ordinary_camera_settle_frames': 100,
                                    'unrelated_actors_cleared': True}
                    return
        raise AssertionError('no natural generated target with safe player position: ' + NAMES[kind])

    def wait(self, predicate, limit=1500):
        for tick in range(limit):
            if not self.target_live():
                return False
            if predicate(self.actor_state(self.target)):
                return True
            self.heal()
            self.c.run_frame()
        return False

    def record(self, name, total, controller=None, note=''):
        images, trace, events = [], [], []
        directory = self.out / name
        raw = self.out / 'all-frames' / name
        directory.mkdir(exist_ok=True)
        raw.mkdir(parents=True, exist_ok=True)
        for tick in range(total):
            self.c.clear_keys(*range(10))
            keys = controller(tick) if controller else []
            if keys:
                self.c.set_keys(*(P.key(self.c, key) for key in keys))
            self.heal()
            self.c.run_frame()
            im = self.c.bg_video.to_pil().convert('RGB').copy()
            images.append(im)
            im.save(raw / f'frame-{tick:03}.png')
            trace.append(self.state())
            if keys:
                events.append({'tick': tick, 'keys': keys})
        self.c.clear_keys(*range(10))
        selected = sorted({0, total // 4, total // 2, total * 3 // 4, total - 1})
        for tick in selected:
            images[tick].save(directory / f'frame-{tick:03}.png')
        # Prefer a visible target/action for the representative frame.
        def key_pose(t):
            a = t['target']
            if not a:
                return False
            if name == 'boss-real-defeat':
                return a['state'] == 6
            if name == 'melee-real-combat':
                return bool(a['iframes']) and a['hp'] > 0
            if self.kind == 0:
                return a['state'] == 2 and a['knockback_timer'] == 0
            if self.kind == 1:
                return a['state'] == 11 and a['ai_frame'] != self.defs['F_BAT_REST']
            if self.kind == 2:
                return a['state'] == 4 and 8 <= a['timer'] <= 12
            if self.kind == 3:
                return a['state'] == 5 and a['z_q16'] >= 6 << 16
            if self.kind == 4:
                return a['state'] == 7 and 5 <= a['timer'] <= 10
            return a['state'] in (2, 3, 4, 6)
        sheet = B.sheet_metadata(self.c, self.defs['SHEET_' + ('BEETLE', 'BAT', 'SPITTER', 'SLIME', 'KNIGHT', 'BOSS')[self.kind]])
        def visible(t):
            a = t['target']
            if not a or a['flags'] & 32 or not t['target_hardware_oam']:
                return False
            x = (a['x_q16'] >> 16) - t['camera'][0] - sheet['width'] // 2
            y = (a['y_q16'] >> 16) - (a['z_q16'] >> 16) - t['camera'][1] - sheet['height']
            return 0 <= x and x + sheet['width'] <= 240 and 12 <= y and y + sheet['height'] <= 160
        selected_tick = next((i for i, t in enumerate(trace) if key_pose(t) and visible(t)),
                             next((i for i, t in enumerate(trace) if visible(t)), total // 2))
        self.check(name + ' representative target is fully on screen below HUD', visible(trace[selected_tick]))
        images[selected_tick].save(self.out / (name + '.png'))
        film = Image.new('RGB', (960, 734), '#101820')
        d = ImageDraw.Draw(film)
        d.fontmode = '1'
        d.text((6, 4), name + ' / actual mGBA chronology', font=FONT, fill='#e8d098')
        for i in range(16):
            tick = round(i * (total - 1) / 15)
            x, y = i % 4 * 240, 22 + i // 4 * 178
            film.paste(images[tick], (x, y))
            target = trace[tick]['target']
            label = f'{tick:03} state {target["state"]} pose {target["presented_frame"]}' if target else f'{tick:03} target removed'
            d.text((x + 4, y + 162), label, font=FONT, fill='#e0dcc0')
        film.save(self.out / (name + '-filmstrip.png'))
        gif = name + '.gif'
        metadata = write_gif([im.resize((480, 320), Image.Resampling.NEAREST)
                              for im in images[::2]], gif_durations(total), self.out / gif)
        if not metadata['exact_palette']:
            (self.out / gif).unlink()
            gif = None
        video = None
        if not self.args.no_video:
            video = name + '.mp4'
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS),
                            '-i', str(raw / 'frame-%03d.png'), '-vf', 'scale=480:320:flags=neighbor',
                            '-an', '-c:v', 'libx264', '-threads', '1', '-crf', '17',
                            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(self.out / video)], check=True)
        play_pairs = [(a, b) for a, b in zip(trace, trace[1:])
                      if a['game_state'] == b['game_state'] == 1]
        self.check(name + ' game updates keep pace with video',
                   all(b['updates'] - a['updates'] == 1 for a, b in play_pairs))
        allowed = (1, 6) if name == 'boss-real-defeat' else (1,)
        self.check(name + ' remains actual play or real victory',
                   all(t['game_state'] in allowed for t in trace))
        self.check(name + ' OAM budget', max(t['oam_count'] for t in trace) <= 128)
        self.rows.append({'name': name, 'kind': self.kind, 'context': dict(self.context),
                          'frames': total, 'fps': FPS, 'image': name + '.png',
                          'filmstrip': name + '-filmstrip.png', 'gif': gif,
                          'gif_metadata': metadata, 'video': video,
                          'native_frames': [f'{name}/frame-{i:03}.png' for i in selected],
                          'all_frames': 'all-frames/' + name, 'events': events,
                          'note': note, 'representative_tick': selected_tick,
                          'mechanics_trace_sha256': hashlib.sha256(json.dumps(
                              [mechanics(t) for t in trace], sort_keys=True,
                              separators=(',', ':')).encode()).hexdigest(),
                          'trace': trace})
        self.save()
        print('CAPTURE', name, total, flush=True)
        return trace

    def fight_controller(self, tick):
        if not self.target_live():
            return []
        e = P.actor(self.c, self.target)
        px, py = P.player_pos(self.c)
        dx, dy = e['x'] - px, e['y'] + 10 - py
        keys = []
        if abs(dx) > 8:
            keys.append('RIGHT' if dx > 0 else 'LEFT')
        if abs(dy) > 8:
            keys.append('DOWN' if dy > 0 else 'UP')
        if abs(dx) < 30 and abs(dy) < 30 and tick % 24 < 2:
            keys.append('B')
        return keys

    def common(self, kind):
        self.enter(kind)
        if kind == 0:
            total = 160
        elif kind == 1:
            total = 280
        elif kind == 2:
            self.check('shooter naturally prepares a shot', self.wait(lambda e: e['state'] == 4))
            total = 160
        elif kind == 3:
            self.check('hopper naturally crouches before a hop', self.wait(lambda e: e['state'] == 3))
            total = 160
        else:
            # Let the real pursuer approach until it chooses its windup.
            self.check('melee naturally prepares a swing', self.wait(lambda e: e['state'] == 6))
            total = 144
        traces = self.record(NAMES[kind] + '-behavior', total,
                             note='Natural generated enemy; safe player position, inventory, healing and unrelated-actor clearing fixtures. AI state/timer/pose/height never assigned.')
        states = {t['target']['state'] for t in traces if t['target']}
        if kind == 0:
            self.check('pursuer chases', 2 in states)
            self.check('pursuer moves', len({(t['target']['x_q16'], t['target']['y_q16']) for t in traces if t['target']}) > 1)
        elif kind == 1:
            self.check('flyer rests and flies', {10, 11} <= states, sorted(states))
            self.check('flyer changes height', len({t['target']['z_q16'] for t in traces if t['target']}) > 1)
        elif kind == 2:
            self.check('shooter emits a real seed', any(p['type'] == 0 for t in traces for p in t['projectiles']))
            self.check('shooter returns from shot', 0 in states or 1 in states)
        elif kind == 3:
            self.check('hopper crouch and hop', {3, 5} <= states, sorted(states))
            self.check('hopper actually leaves ground', any(t['target'] and t['target']['z_q16'] > 0 for t in traces))
        else:
            self.check('melee windup swing recovery', {6, 7, 8} <= states, sorted(states))
            self.weapon_after_menu()
            self.enter(4)
            combat = self.record('melee-real-combat', 480, self.fight_controller,
                                 note='Natural 10HP heavy enemy, actual D-pad/B sword inputs. Player health/position/equipment and unrelated-actor clearing are fixtures; enemy HP/state/timer/pose are never assigned.')
            self.check('ordinary combat hurts the heavy enemy',
                       any(t['target'] and 0 < t['target']['hp'] < 10
                           and t['target']['iframes'] for t in combat))
            self.check('ordinary combat defeats the heavy enemy',
                       any(t['target'] is None for t in combat))
            hurt = {value for key, value in self.defs.items() if key.startswith('F_KNIGHT_HURT_')}
            if hurt and self.variant:
                self.check('new heavy hurt pose is actually presented',
                           any(t['target'] and t['target']['presented_frame'] in hurt for t in combat))

    def weapon_after_menu(self):
        """The large item menu must not overwrite the resident enemy weapon."""
        sheet = B.sheet_metadata(self.c, self.defs['SHEET_KSWORD'])
        tile = P.r16(self.c, B.static_symbol('sKswordTile')) & 65535
        expected = B.bytes_at(self.c, sheet['source'], sheet['tiles'] * 32)
        address = 0x06010000 + tile * 32
        palettes = {bank: B.bytes_at(self.c, P.sym('pal_obj') + bank * 32, 32)
                    for bank in (2, 10)}
        for bank, palette in palettes.items():
            self.check(f'OBJ bank{bank} matches native game palette before menu',
                       B.bytes_at(self.c, 0x05000200 + bank * 32, 32) == palette
                       and B.bytes_at(self.c, P.sym('gPalObj') + bank * 32, 32) == palette)
        self.check('heavy weapon native VRAM matches its ROM sheet before menu',
                   tile > 0 and B.bytes_at(self.c, address, len(expected)) == expected)
        P.press(self.c, 'START', 2, 20)
        self.check('ordinary Start opens the item menu during enemy encounter', C.gstate(self.c) == 4)
        paused = self.actor_state(self.target)
        P.run(self.c, 20)
        self.check('paused item menu preserves live heavy AI mechanics',
                   {key: paused[key] for key in MECHANIC_FIELDS}
                   == {key: self.actor_state(self.target)[key] for key in MECHANIC_FIELDS})
        P.press(self.c, 'START', 2, 20)
        self.check('ordinary Start resumes real enemy encounter', C.gstate(self.c) == 1)
        self.check('closing item menu preserves every native heavy weapon byte',
                   B.bytes_at(self.c, address, len(expected)) == expected)
        for bank, palette in palettes.items():
            self.check(f'closing menu restores native OBJ bank{bank} in buffer and hardware',
                       B.bytes_at(self.c, 0x05000200 + bank * 32, 32) == palette
                       and B.bytes_at(self.c, P.sym('gPalObj') + bank * 32, 32) == palette)
        self.record('melee-after-menu', 64,
                    note='Ordinary Start opened and closed the live item menu. Native enemy weapon VRAM and small-enemy/foliage OBJ palette banks are independently verified unchanged; real AI resumes.')

    def boss(self):
        self.enter(5)
        ring = self.record('boss-ring', 240, note='Natural 40HP generated boss: ordinary pulse, drift and eight-spore burst. Player healing/position fixtures only.')
        self.check('boss emits an eight-spore ring', max(len(t['projectiles']) for t in ring) >= 8)
        P.w16(self.c, P.sym('gActors') + self.target * 64 + 26, 26)
        self.context['boss_hp_fixture'] = 26
        middle = self.record('boss-fan-and-adds', 360, note='Disclosed boss HP26 fixture selects its existing middle phase; no AI state/timer/pose injected. Actual fans and add spawns follow.')
        self.check('boss middle phase summons adds', any(t['enemy_count'] > 1 for t in middle))
        self.check('boss middle phase emits spores', any(t['projectiles'] for t in middle))
        P.w16(self.c, P.sym('gActors') + self.target * 64 + 26, 12)
        self.context['boss_hp_fixture'] = 12
        lunge = self.record('boss-lunge', 200, note='Disclosed boss HP12 fixture selects existing low-health lunge phase; all motion and state transitions are real AI.')
        self.check('boss low phase lunges', any(t['target'] and t['target']['state'] == 4 for t in lunge))
        # A disclosed low-HP fixture accelerates the existing defeat event;
        # the ordinary sword and combat code must land the actual final blow.
        self.enter(5)
        P.w16(self.c, P.sym('gActors') + self.target * 64 + 26, 4)
        self.context['boss_hp_fixture'] = 4
        death = self.record('boss-real-defeat', 720, self.fight_controller,
                            note='Natural boss with disclosed HP4 fixture; real D-pad/B sword inputs cause a nonlethal hit, then existing 120-update death, blasts and Grail drop. No enemy animation/state assignments.')
        self.check('ordinary sword first hurts the boss without killing it',
                   any(t['target'] and 0 < t['target']['hp'] < 4
                       and t['target']['iframes'] for t in death))
        self.check('ordinary sword triggers boss death state', any(t['target'] and t['target']['state'] == 6 for t in death))
        self.check('boss removed after real death sequence', any(t['target'] is None for t in death))
        if self.variant:
            self.check('new boss hurt pose is actually presented',
                       any(t['target'] and t['target']['presented_frame'] == self.defs['F_BOSS_HURT']
                           and t['target']['iframes'] for t in death))

    def cave(self):
        """Additional actual interior contrast; preserve the natural group."""
        import art_reboot_review as AR
        for seed in (0xB4A7, 11, 6, 7):
            self.c = P.boot(rom=P.ROM, seed=seed)
            C.dismiss(self.c)
            world = C.world(self.c)
            P.enter_forest(self.c)
            for cell in range(25):
                packed = AR.actual_mystery(self.c, cell)
                if not packed or packed >> 6 or (packed & 15) not in (5, 6, 7):
                    continue
                if not AR.enter_natural(self.c, world, cell):
                    continue
                C.dismiss(self.c)
                self.heal()
                for _ in range(100):
                    if self.enemies():
                        break
                    self.c.run_frame()
                enemies = self.enemies()
                if not enemies:
                    continue
                self.target, actor = next(((i, a) for i, a in enemies if a['type'] == 4), enemies[0])
                self.kind = actor['type']
                self.context = {'seed': seed, 'cell': cell, 'natural_mystery': packed,
                                'style': 'cave', 'kind': self.kind,
                                'natural_spawn_index': self.target,
                                'player_health_fixture': 80,
                                'unrelated_actors_cleared': False}
                trace = self.record('cave-natural-group', 240,
                                    note='Actual generated cave combat trial entered through its real mouth. All naturally spawned enemies are retained; only player healing is a fixture. No Drain enemy spawns or invented enemy room are claimed.')
                self.check('actual cave enemy group stays in its natural interior',
                           all(t['area'] == 2 for t in trace))
                self.check('actual cave enemy group moves or attacks',
                           any(t['target'] and (t['target']['x_q16'], t['target']['y_q16'], t['target']['state'])
                               != (trace[0]['target']['x_q16'], trace[0]['target']['y_q16'], trace[0]['target']['state'])
                               for t in trace))
                return
        self.check('a naturally generated combat cave was found', False)

    def save(self):
        freeze = self.frozen / 'freeze.json'
        row = {'method': __doc__.strip(), 'emulator': 'mGBA 0.10.5',
               'rom_sha256': digest(P.ROM), 'enemy_variant': self.variant,
               'source_commit': json.loads(freeze.read_text()).get('source_commit') if freeze.exists() else None,
               'checks': self.checks, 'passed': sum(c['passed'] for c in self.checks),
               'total': len(self.checks), 'failures': [c for c in self.checks if not c['passed']],
               'capture_count': len(self.rows), 'captures': self.rows,
               'mechanic_comparison_fields': list(MECHANIC_FIELDS)}
        (self.out / 'capture.json').write_text(json.dumps(row, indent=2) + '\n')

    def run(self):
        for kind in (self.args.kinds if self.args.kinds is not None else range(6)):
            self.boss() if kind == 5 else self.common(kind)
        if self.args.include_cave:
            self.cave()
        self.save()
        print('RESULT', sum(c['passed'] for c in self.checks), '/', len(self.checks), 'captures', len(self.rows), flush=True)
        return int(any(not c['passed'] for c in self.checks))

def mechanics(t):
    """Exclude images, draw-only frames, OAM, global time and presentation IDs.

    Kept game fields expose any real AI/motion/health/projectile/RNG drift.
    Cold-loading/global-frame phase differences in a legacy baseline are not
    silently normalized away: callers inspect and explain any resulting drift.
    """
    def actor(a):
        return {key: a[key] for key in MECHANIC_FIELDS} if a else None
    return {'game_state': t['game_state'], 'area': t['area'], 'cell': t['cell'],
            'hero': actor(t['hero']), 'hero_hp': t['hero_hp'],
            'target': actor(t['target']), 'projectiles': t['projectiles'],
            'enemy_count': t['enemy_count'], 'rng': t.get('rng')}

def compare_reports(reference_path, candidate_path):
    """Independent trace comparison; reports concrete first divergence."""
    reference = json.loads(Path(reference_path).read_text())
    candidate = json.loads(Path(candidate_path).read_text())
    before = {r['name']: r for r in reference['captures']}
    rows = []
    for row in candidate['captures']:
        old = before.get(row['name'])
        if old is None:
            rows.append({'name': row['name'], 'passed': False, 'reason': 'reference capture missing'})
            continue
        a, b = [mechanics(t) for t in old['trace']], [mechanics(t) for t in row['trace']]
        bad = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None)
        item = {'name': row['name'], 'passed': bad is None and len(a) == len(b),
                'reference_frames': len(a), 'candidate_frames': len(b)}
        if bad is not None:
            item['first_divergence_tick'] = bad
            item['reference'] = a[bad]
            item['candidate'] = b[bad]
        rows.append(item)
    return {'reference_rom_sha256': reference['rom_sha256'],
            'candidate_rom_sha256': candidate['rom_sha256'],
            'passed': sum(r['passed'] for r in rows), 'total': len(rows),
            'method': mechanics.__doc__.strip(), 'captures': rows}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frozen', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--kinds', nargs='*', type=int, choices=range(6))
    p.add_argument('--no-video', action='store_true')
    p.add_argument('--include-cave', action='store_true',
                   help='Also enter a natural generated cave combat trial; no enemy/terrain injection.')
    return Review(p.parse_args()).run()

if __name__ == '__main__':
    raise SystemExit(main())
