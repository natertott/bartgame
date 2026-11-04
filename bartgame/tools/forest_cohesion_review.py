#!/usr/bin/env python3
"""Capture natural forest composition studies in the real GBA renderer.

The 512x384 room image is a registered mosaic of nine untouched 240x160
mGBA camera views. The native review camera changes camera/clock/HUD only.
No terrain, source art, pose or screenshot pixels are injected. Room-selection,
standing-position and enemy-isolation fixtures are recorded explicitly.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

from PIL import Image
import forest_trees_review as R
from sewer_concept_audit import NativeRom

P, B, C, T = R.P, R.B, R.C, R.T
read, words, write32, save_json, rgb_sha, sha = R.read, R.words, R.write32, R.save_json, R.rgb_sha, R.sha
LOADED_SHA = sha(Path(__file__).read_bytes())
DEFAULT_ROOMS = (
    {'name': 'healthy', 'seed': 0xB4A7, 'cell': 16},
    {'name': 'mixed', 'seed': 0xB4A7, 'cell': 0},
    {'name': 'deep', 'seed': 6, 'cell': 4},
)
MOTIFS = ('dry-glade', 'brook-crossing', 'pond', 'damp-root-hollow', 'ruined-edge', 'heart-arena')
INFO_NAMES = ('version', 'motif', 'water_cells', 'bridge_cells', 'wet_components',
              'ecology_clusters', 'solid_props_added', 'floor_accents_added', 'lantern_posts',
              'visible_trail_cells', 'ledge_cells', 'water_feature_attempts', 'feature_clue_posts',
              'arch', 'stage', 'cell')


def parse_number(value):
    return int(value, 0) if isinstance(value, str) else int(value)


def normalize_cases(values):
    cases = []
    for value in values:
        name = value['name']
        if not re.fullmatch(r'[A-Za-z0-9_-]+', name):
            raise ValueError('Case name must contain only letters, digits, underscore or hyphen')
        seed, cell = parse_number(value['seed']), int(value['cell'])
        if not 0 <= seed <= 0xFFFFFFFF or not 0 <= cell < 25:
            raise ValueError('Invalid native seed or cell')
        if any(row['name'] == name for row in cases):
            raise ValueError('Duplicate case name')
        cases.append({'name': name, 'seed': seed, 'cell': cell})
    return cases


class Review(R.Review):
    """Retain the old read-only PPU/body/map proof, with new composition cases."""

    def __init__(self, args):
        self.args = args
        self.base, self.out = Path(args.bundle).resolve(), Path(args.out).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.rom, self.rows, self.checks = NativeRom(self.base), [], []
        self.defs = self.rom.defs
        self.variant = self.defs['BART_FOREST_VARIANT']
        if self.variant not in (31, 32):
            raise ValueError('Requires integrated baseline31 or cohesion32')
        P.MAP = str(self.base/'bartgame.map')
        P._syms = None
        self.freeze = json.loads((self.base/'freeze.json').read_text()) if (self.base/'freeze.json').exists() else {'unfrozen_pilot': True}
        self.immutable = {name: sha((self.base/name).read_bytes()) for name in ('bartgame.gba', 'bartgame.map', 'assets.h')}
        self.deps = {}
        for module in tuple(sys.modules.values()):
            value = getattr(module, '__file__', None)
            if value:
                path = Path(value).resolve()
                if path.parent == Path(__file__).resolve().parent:
                    self.deps[path.name] = sha(path.read_bytes())
        self.c = self.pending = self.completed = None
        self.ts = self.rom.tileset('forest')
        self.rng = B.static_symbol('sRand')
        self.current_case = None
        self.census_rows = []
        self.finalized = False
        self.check('native forest atlas leaves BG3 map allocation free', 0 < self.ts['tile_count'] <= 768, self.ts['tile_count'])
        self.check('native world palette allocation respected', 0 < self.ts['palette_count'] <= 12, self.ts['palette_count'])

    def composition(self):
        if 'gForestCohesionInfo' not in self.rom.symbols:
            return {'available': False, 'reason': 'Historical31 has no composition telemetry.'}
        values = words(self.c, P.sym('gForestCohesionInfo'), 16)
        result = dict(zip(INFO_NAMES, values))
        result['available'] = True
        result['motif_name'] = MOTIFS[result['motif']] if result['motif'] < len(MOTIFS) else 'unknown'
        return result

    def snapshot(self):
        return {**super().snapshot(), 'composition': self.composition()}

    def grid(self):
        c = self.c
        at = P.sym('gRoom')
        width, height = P.r8(c, at), P.r8(c, at+1)
        ground = words(c, at+2, 1024)
        types = read(c, P.sym('metatile_type'), self.defs['METATILE_COUNT'])
        counts = {}
        wet, bridge = [], []
        bridge_ids = {self.defs.get('MT_BRIDGE'), self.defs.get('MT_BRIDGE_V')}
        for y in range(height):
            for x in range(width):
                mt = ground[y*32+x]
                if mt >= len(types):
                    continue
                kind = types[mt]
                counts[str(kind)] = counts.get(str(kind), 0)+1
                if kind == self.defs['TT_WATER']:
                    wet.append([x, y])
                if mt in bridge_ids:
                    bridge.append([x, y])
        return {'size_tiles': [width, height], 'type_counts': counts, 'water_cells': wet,
                'bridge_cells': bridge, 'ground_sha256': sha(struct.pack('<1024H', *ground)),
                'ground': ground[:width*height]}

    def native_transition(self, cell):
        c = self.c
        side = next(side for side, value in enumerate(self.world['cells'][cell]['gate']) if value)
        for name, value in (('sNextArea', 1), ('sNextCell', cell), ('sNextSide', side), ('sTransPhase', 0)):
            P.w8(c, self.static(name), value)
        P.w8(c, P.sym('gGame'), 2)
        for _ in range(1200):
            P.run(c, 1)
            if C.gstate(c) == 1 and C.area(c) == 1 and C.cell(c) == cell:
                break
        else:
            raise RuntimeError('Native area transition did not settle')
        C.dismiss(c)

    def census(self, seeds):
        """Inspect naturally generated ROM rooms without injecting their grids."""
        for seed in seeds:
            self.c = P.boot(rom=str(self.base/'bartgame.gba'), seed=seed)
            C.dismiss(self.c)
            self.world = C.world(self.c)
            P.enter_forest(self.c)
            for cell in range(25):
                self.native_transition(cell)
                record = {'seed': hex(seed), 'cell': cell, 'stage': self.world['cells'][cell]['stage'],
                          'role': self.world['cells'][cell]['role'], 'composition': self.composition(),
                          'grid': self.grid(), 'physical': self.physical()}
                self.census_rows.append(record)
            save_json(self.out/'census.json', self.census_report())
        suggestions = list(DEFAULT_ROOMS)
        for motif in (0, 1, 2, 3, 4, 5):
            options = [r for r in self.census_rows if r['composition'].get('motif') == motif]
            if not options:
                continue
            row = max(options, key=lambda r: (r['composition'].get('water_cells', 0), r['composition'].get('ecology_clusters', 0)))
            candidate = {'name': MOTIFS[motif], 'seed': parse_number(row['seed']), 'cell': row['cell']}
            if all((v['seed'], v['cell']) != (candidate['seed'], candidate['cell']) for v in suggestions):
                suggestions.append(candidate)
        save_json(self.out/'suggested-rooms.json', suggestions)
        save_json(self.out/'census.json', self.census_report())
        self.check('all requested native census room transitions completed', len(self.census_rows) == len(seeds)*25,
                   {'seeds': len(seeds), 'rooms': len(self.census_rows)})

    def census_report(self):
        return {'forest_variant': self.variant, 'bundle_sha256': self.immutable, 'source_freeze': self.freeze,
                'method': 'Actual seeded game and native selected-cell transitions. Grids and composition telemetry are read from RAM; no room or video pixels are injected.',
                'capture_tool_sha256': LOADED_SHA, 'rooms': self.census_rows}

    def walk(self, name, point):
        folder = self.out/name/'walk'
        folder.mkdir(exist_ok=True)
        self.normal()
        self.clear_enemies()
        self.settle(point)
        # Four ordinary directional phases; avoid known water/pit/exit cells
        # rather than accidentally recording an intentional drowning animation
        # as a foliage-visibility failure. The actual key at every tick is kept.
        frames, observations = [], []
        last = P.r32(self.c, P.sym('gGame')+8)
        for direction, hold in (('RIGHT', 48), ('DOWN', 36), ('LEFT', 48), ('UP', 36)):
            for _ in range(hold):
                tick = len(frames)
                actual = self.walk_direction(direction)
                if actual:
                    self.c.set_keys(P.key(self.c, actual))
                else:
                    self.c.clear_keys(*range(10))
                P.run(self.c, 1)
                image = self.c.bg_video.to_pil().convert('RGB').copy()
                image.save(folder/f'{tick:04d}.png')
                frames.append(image)
                now = P.r32(self.c, P.sym('gGame')+8)
                observations.append({'tick': tick, 'direction': actual, 'requested_direction': direction,
                                     'position': list(P.player_pos(self.c)),
                                     'logic_updates': (now-last)&0xFFFFFFFF, 'gFrame': P.r32(self.c, P.sym('gFrame')),
                                     'run_frames': now, 'body': self.completed})
                last = now
        self.c.clear_keys(*range(10))
        mp4 = folder.parent/'walk.mp4'
        self.encode(frames, folder, mp4)
        gif, gifmeta = self.gif(frames, folder.parent/'walk.gif')
        save_json(folder.parent/'walk-observations.json', observations)
        body = [o['body'] for o in observations if o['body'] and o['body'].get('body_found')]
        minimum = min((b['exact_visible_pixels'] for b in body), default=0)
        connected = min((b['largest_visible_component'] for b in body), default=0)
        self.check(name+' ordinary walk retains native Bloom visibility', minimum >= 37, minimum)
        self.check(name+' ordinary walk retains a recognizable connected body region', connected >= 12, connected)
        self.check(name+' ordinary walk guard consists only of exact current body pixels',
                   len(body) == len(observations) and all(b['guard_exact_native_subset'] for b in body))
        self.check(name+' ordinary walk retains every native frame and paired scanout',
                   len(frames) == 168 and all(b.get('scanline0') == 0 and b.get('scanline160') == 160 and
                                              b.get('video_frame') == b.get('end_video_frame') for b in body))
        missed = [{'tick': o['tick'], 'gFrame': o['gFrame'], 'position': o['position']} for o in observations if o['logic_updates'] == 0]
        return {'movie': str(mp4.relative_to(self.out)), 'gif': str(gif.relative_to(self.out)) if gif else None,
                'observations': str((folder.parent/'walk-observations.json').relative_to(self.out)),
                'frames': len(frames), 'raw_frames_local': str(folder), 'minimum_visible_Bloom_pixels': minimum,
                'minimum_connected_Bloom_pixels': connected,
                'missed_updates': len(missed), 'missed_update_frames': missed,
                'total_logic_updates': sum(o['logic_updates'] for o in observations),
                'frame_perfect_claim': False, 'timing_comparison': 'Literal recorded intervals; no allowance is imported from another profile or room.',
                'gif_metadata': gifmeta,
                'fixture': 'Enemy/projectile/FX isolation and initial safe standing position. Ordinary directional keys are selected from the actual room grid to avoid water/pits/ledges/exits. Every requested and actual key is recorded; terrain, pose and later position are never injected.'}

    def walk_direction(self, preferred):
        directions = ('UP', 'RIGHT', 'DOWN', 'LEFT')
        vectors = {'UP': (0, -2), 'RIGHT': (2, 0), 'DOWN': (0, 2), 'LEFT': (-2, 0)}
        i = directions.index(preferred)
        px, py = P.player_pos(self.c)
        forbidden = {self.defs['TT_'+name] for name in
                     ('PIT', 'WATER', 'HURT', 'LEDGE_N', 'LEDGE_E', 'LEDGE_S', 'LEDGE_W', 'EXIT', 'STAIRS', 'MYST')}
        base = P.sym('gRoom')
        width, height = P.r8(self.c, base), P.r8(self.c, base+1)
        types = P.sym('metatile_type')
        for direction in (preferred, directions[(i+1)%4], directions[(i-1)%4], directions[(i+2)%4]):
            dx, dy = vectors[direction]
            x, y = px+dx, py+dy
            valid = True
            for xx, yy in ((x-5, y-8), (x+4, y-8), (x-5, y-1), (x+4, y-1)):
                if not (0 <= xx < width*16 and 0 <= yy < height*16):
                    valid = False
                    break
                mt = P.r16(self.c, base+2+((yy//16)*32+xx//16)*2)&65535
                if mt >= self.defs['METATILE_COUNT'] or P.r8(self.c, types+mt) in forbidden:
                    valid = False
                    break
            if valid:
                return direction
        return None

    def encode(self, frames, folder, path):
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-framerate', '16777216/280896',
                        '-i', str(folder/'%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv444p', '-crf', '14', str(path)], check=True)

    def gif(self, frames, path):
        try:
            return path, T.sampled_gif(frames[::8], path, hold=130)
        except AssertionError:
            if path.exists():
                path.unlink()
            return None, {'omitted': True, 'reason': 'Exact sampled GIF roundtrip did not fit; native PNGs and full-rate video remain.'}

    def water_motion(self, name):
        wet = self.grid()['water_cells']
        if not wet:
            return None
        self.normal()
        self.clear_enemies()
        candidates = [(min(abs(x-wx*16-8)+abs(y-wy*16-8) for wx, wy in wet), x, y)
                      for y in range(64, 352, 8) for x in range(48, 472, 8) if self.safe(x, y)]
        if not candidates:
            return None
        _, px, py = min(candidates)
        self.settle((px, py))
        folder = self.out/name/'water'
        folder.mkdir(exist_ok=True)
        initial = self.physical()
        frames, observations = [], []
        for tick in range(96):
            P.run(self.c, 1)
            image = self.c.bg_video.to_pil().convert('RGB').copy()
            image.save(folder/f'{tick:04d}.png')
            frames.append(image)
            observations.append({'tick': tick, 'gFrame': P.r32(self.c, P.sym('gFrame')), 'hardware': self.snapshot(),
                                 'atlas': self.fidelity()})
        path = folder.parent/'water-motion.mp4'
        self.encode(frames, folder, path)
        gif, gifmeta = self.gif(frames, folder.parent/'water-motion.gif')
        save_json(folder.parent/'water-observations.json', observations)
        final = self.physical()
        self.check(name+' water motion uses authored animated atlas frames',
                   all(o['atlas']['animated_tiles_are_authored_ROM_frames'] and o['atlas']['static_resident_BG_tiles_equal_ROM'] for o in observations))
        self.check(name+' ordinary water animation leaves terrain and collision unchanged',
                   all(initial[k] == final[k] for k in ('ground_sha256', 'overlay_sha256', 'collision_sha256', 'underlay_sha256')))
        return {'movie': str(path.relative_to(self.out)), 'gif': str(gif.relative_to(self.out)) if gif else None,
                'observations': str((folder.parent/'water-observations.json').relative_to(self.out)),
                'frames': len(frames), 'raw_frames_local': str(folder), 'initial_position': [px, py],
                'gif_metadata': gifmeta, 'fixture': 'Dry-bank standing point and enemy isolation; ordinary world animation and native HUD, no held camera or animation clock.'}

    def room(self, name, seed, cell):
        requested_movies = self.args.movies
        self.args.movies = requested_movies and (not self.args.movie_cases or name in self.args.movie_cases.split(','))
        try:
            super().room(name, seed, cell)
        finally:
            self.args.movies = requested_movies
        row = self.rows[-1]
        row['composition'] = self.composition()
        row['grid'] = self.grid()
        water = self.args.water and (not self.args.water_cases or name in self.args.water_cases.split(','))
        row['water_motion'] = self.water_motion(name) if water else None
        self.save()

    def save(self):
        save_json(self.out/'capture.json', {'source_freeze': self.freeze, 'bundle': str(self.base),
            'bundle_sha256': self.immutable, 'forest_variant': self.variant, 'capture_tool_sha256': LOADED_SHA,
            'capture_dependency_sha256': self.deps, 'command': sys.argv, 'captures': self.rows,
            'timing_baseline': None, 'timing_note': 'Every native frame is retained. Missed logic intervals are reported per new room; no fixed old threshold is inherited.',
            'census_file': 'census.json' if self.census_rows else None,
            'checks': self.checks, 'complete': self.finalized,
            'pass': all(c['passed'] for c in self.checks)})

    def finish(self):
        if self.rows:
            used = sorted({p['frame'] for r in self.rows for p in r['panorama']['trees']['placements']})
            self.check('approved native tree frame indices remain valid', bool(used) and all(0 <= n < 12 for n in used), used)
        self.check('frozen ROM/header/map unchanged', all(sha((self.base/n).read_bytes()) == v for n, v in self.immutable.items()))
        self.check('capture tool unchanged during execution', sha(Path(__file__).read_bytes()) == LOADED_SHA)
        self.check('read-only capture dependencies unchanged during execution',
                   all(sha((Path(__file__).parent/n).read_bytes()) == v for n, v in self.deps.items()))
        self.finalized = True
        self.save()
        if not all(c['passed'] for c in self.checks):
            raise SystemExit('Native capture verification failed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--rooms', help='JSON case list: name, seed, cell')
    parser.add_argument('--only', help='Comma-separated names from the case list')
    parser.add_argument('--movies', action='store_true')
    parser.add_argument('--movie-cases', help='Optional comma-separated subset for --movies')
    parser.add_argument('--water', action='store_true', help='Record native96-frame surface-animation views when water exists')
    parser.add_argument('--water-cases', help='Optional comma-separated subset for --water')
    parser.add_argument('--census', help='Comma-separated seeds to inspect all25 naturally generated cells')
    parser.add_argument('--census-only', action='store_true')
    args = parser.parse_args()
    review = Review(args)
    if args.census:
        review.census([parse_number(s.strip()) for s in args.census.split(',')])
    cases = normalize_cases(json.loads(Path(args.rooms).read_text()) if args.rooms else DEFAULT_ROOMS)
    for selector in (args.movie_cases, args.water_cases):
        if selector and not set(selector.split(',')) <= {row['name'] for row in cases}:
            raise ValueError('A selected movie/water case is absent from the room list')
    if not args.census_only:
        for row in cases:
            if not args.only or row['name'] in args.only.split(','):
                review.room(row['name'], row['seed'], row['cell'])
    review.finish()


if __name__ == '__main__':
    main()
