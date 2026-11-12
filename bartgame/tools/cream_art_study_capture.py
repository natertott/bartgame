#!/usr/bin/env python3
"""Capture pinned Cream art studies through the actual mGBA renderer.

Each registered panorama and ordinary live climb uses a separate fresh core.
Only the registered renderer core uses the existing HUD-free review camera and
clock hook. Nine raw native camera PNGs form each literal 512x384 crop mosaic.
Ordinary screenshots and clips advance actual simulation with real UP input,
without clock, camera, health, inventory, enemy, terrain or framebuffer writes.
Disclosed fixtures select the title seed, hero position/facing and the game's
ordinary room-load request. These isolated art views do not prove an earned
route through the area's progression gates.
"""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

from PIL import Image
import cream_graph_review as G
import probe as P
from regional_native_support import NativeRun, sha


class Spot(C.Structure):
    _fields_ = [('x', C.c_uint8), ('y', C.c_uint8)]


class Terrace(C.Structure):
    _fields_ = [('spawns', Spot * 6), ('spawn_count', C.c_uint8),
                ('content', C.c_uint8), ('chest', Spot), ('npc', Spot),
                ('heal', Spot), ('cache', Spot), ('mission', Spot)]


class Info(C.Structure):
    _fields_ = [('cell', C.c_uint8), ('stage', C.c_uint8), ('motif', C.c_uint8),
                ('climb_x', C.c_uint8), ('upper_bottom', C.c_uint8 * 32),
                ('lower_top', C.c_uint8 * 32), ('terrace', Terrace * 2),
                ('return_door', Spot)]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def raw(c, address, count):
    return bytes(P.r8(c, address + i) for i in range(count))


def w32(c, address, value):
    P.w16(c, address, value & 65535)
    P.w16(c, address + 2, value >> 16)


def extra_abi(run):
    """Check Python structures and observe fields using pinned ARM headers."""
    folder = run.out / 'art-abi'
    folder.mkdir(exist_ok=True)
    expressions = dict(room_size='sizeof(Room)', info_size='sizeof(CreamRoomInfo)',
                       world_size='sizeof(CreamWorld)', actor_size='sizeof(Actor)',
                       actor_x='offsetof(Actor,x)', actor_y='offsetof(Actor,y)',
                       actor_facing='offsetof(Actor,facing)',
                       enum_normal='PS_NORMAL', enum_climb='PS_CLIMB',
                       enum_dead='PS_DEAD', info_climb='offsetof(CreamRoomInfo,climb_x)',
                       info_upper='offsetof(CreamRoomInfo,upper_bottom)',
                       info_lower='offsetof(CreamRoomInfo,lower_top)',
                       info_terrace='offsetof(CreamRoomInfo,terrace)',
                       info_return='offsetof(CreamRoomInfo,return_door)')
    source = '#include <stddef.h>\n#include "room.h"\n#include "cream_room.h"\n#include "player.h"\n'
    source += '__attribute__((used,section(".art_abi"))) const unsigned values[]={'
    source += ','.join(expressions.values()) + '};\n'
    unit, obj, binary = folder / 'abi.c', folder / 'abi.o', folder / 'abi.bin'
    unit.write_text(source)
    command = ['arm-none-eabi-gcc', '-mcpu=arm7tdmi', '-mthumb', '-std=c99',
               '-DBART_FOREST_VARIANT=32', '-I', str(run.out / 'abi/headers'),
               '-c', str(unit), '-o', str(obj)]
    result = subprocess.run(command, capture_output=True, text=True)
    (folder / 'compile.log').write_text(result.stdout + result.stderr)
    result.check_returncode()
    subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', '-j', '.art_abi',
                    str(obj), str(binary)], check=True)
    answer = dict(zip(expressions, struct.unpack('<' + 'I' * len(expressions), binary.read_bytes())))
    assert answer['world_size'] == C.sizeof(G.World)
    assert answer['info_size'] == C.sizeof(Info)
    for key, field in [('info_climb', 'climb_x'), ('info_upper', 'upper_bottom'),
                       ('info_lower', 'lower_top'), ('info_terrace', 'terrace'),
                       ('info_return', 'return_door')]:
        assert answer[key] == getattr(Info, field).offset
    write_json(folder / 'provenance.json', dict(source_sha256=sha(unit), command=command, values=answer))
    return answer


class Capture:
    def __init__(self, bundle, out, seed):
        self.run = NativeRun(bundle, out)
        self.extra = extra_abi(self.run)
        self.seed = seed
        self.trace = []
        self.checks = []
        self.run.start(seed)
        self.draft = self.run.finish_draft((0, 1, 2))
        self.run.settle(0)
        self.run.dismiss()
        self.check('normal opening draft completed with positive health',
                   self.run.snapshot()['draft']['state'] == self.run.abi['enum_draft_done']
                   and self.run.snapshot()['health'][0] > 0)
        self.nav(self.run.abi['hub_ladder_x'], self.run.abi['hub_ladder_return'], 0)
        self.advance('UP', 600, stop=lambda st: st['state'] == 1 and st['area'] == 3)
        self.run.settle(3)
        self.run.dismiss()
        self.check('actual UP input enters Cream through Drain ladder', self.state()['area'] == 3)
        self.world = G.World.from_buffer_copy(raw(self.c, P.sym('gCreamWorld'), C.sizeof(G.World)))

    @property
    def c(self):
        return self.run.c

    def state(self):
        st = self.run.snapshot()
        return dict(frames=self.run.frames, clock=P.r32(self.c, P.sym('gFrame')),
                    run_frames=P.r32(self.c, P.sym('gGame') + 8), state=st['state'],
                    area=st['area'], cell=st['cell'], node=self.run.u8('gCreamNode'),
                    actor=st['actor'], health=st['health'], text=st['text'])

    def check(self, name, passed, observed=None):
        self.checks.append(dict(name=name, passed=bool(passed), observed=observed))
        print(('PASS ' if passed else 'FAIL ') + name, flush=True)
        if not passed:
            raise AssertionError(name + ': ' + str(observed))

    def advance(self, keys, count, stop=None, record=None):
        names = [keys] if isinstance(keys, str) else keys
        before = self.state()
        ks = [P.key(self.c, key) for key in names]
        self.c.clear_keys(*range(10))
        self.c.set_keys(*ks)
        changes = []
        images = []
        previous = None
        minimum_hp = before['health'][0]
        climb_frames = 0
        for index in range(count):
            self.c.run_frame()
            self.run.frames += 1
            st = self.state()
            if st['health'][0] <= 0 or st['actor']['state'] == self.extra['enum_dead']:
                raise RuntimeError('hero died; this capture never restores health or overrides action state')
            minimum_hp = min(minimum_hp, st['health'][0])
            climb_frames += st['actor']['state'] == self.extra['enum_climb']
            signature = (st['area'], st['cell'], st['node'], st['actor']['state'], st['health'][0])
            if signature != previous:
                changes.append(st)
                previous = signature
            if record is not None and index % 4 == 0:
                im = self.c.bg_video.to_pil().convert('RGB').copy()
                file = 'frame-%04d.png' % index
                im.save(record / file)
                images.append((index, im, st, file))
            if stop is not None and stop(st):
                break
        self.c.clear_keys(*ks)
        entry = dict(keys=names, frames=index + 1, before=before, after=self.state(),
                     state_changes=changes, minimum_health=minimum_hp, climb_frames=climb_frames)
        self.trace.append(entry)
        return images, entry

    def nav(self, x, y, facing=0):
        before = self.state()
        self.check('navigation begins in living ordinary ground state',
                   before['health'][0] > 0 and before['actor']['state'] == self.extra['enum_normal']
                   and before['actor']['z'] == 0, before)
        a = P.sym('gActors')
        w32(self.c, a + self.extra['actor_x'], x << 16)
        w32(self.c, a + self.extra['actor_y'], y << 16)
        P.w8(self.c, a + self.extra['actor_facing'], facing)
        self.run.fixtures.append(dict(kind='hero position/facing navigation', x=x, y=y,
                                      facing=facing, before=before))

    def request(self, cell):
        if self.state()['cell'] == cell:
            return
        before = self.state()
        values = [('sNextArea', 3), ('sNextCell', cell), ('sNextSide', 2),
                  ('sTransPhase', 0), ('sCreamNextNode', cell * 2),
                  ('sCreamNextFacing', 0), ('sCreamDropRows', 0)]
        for name, value in values:
            address = next((self.run.sections.get(prefix + name) for prefix in
                            ('.bss.', '.data.', '.ewram_bss.')
                            if prefix + name in self.run.sections), None)
            if address is None:
                raise KeyError(name)
            P.w8(self.c, address, value)
        for name in ('sCreamNextX', 'sCreamNextY'):
            address = next(self.run.sections[prefix + name] for prefix in
                           ('.bss.', '.data.', '.ewram_bss.') if prefix + name in self.run.sections)
            P.w16(self.c, address, 65535)
        P.w8(self.c, P.sym('gGame') + self.run.abi['game_state'], self.run.abi['enum_transition'])
        self.run.fixtures.append(dict(kind='ordinary Cream room-load request for isolated art case',
                                      cell=cell, node=cell * 2, before=before))
        self.run.settle(3)
        self.run.dismiss()
        self.check('ordinary load selected actual generated room', self.state()['cell'] == cell,
                   self.state())

    def info(self):
        return Info.from_buffer_copy(raw(self.c, P.sym('gCreamRoom'), C.sizeof(Info)))

    def tile_type(self, px, py):
        a = self.run.abi
        mt = P.r16(self.c, P.sym('gRoom') + a['room_ground'] + ((py // 16) * 32 + px // 16) * 2) & 65535
        return P.r8(self.c, P.sym('metatile_type') + mt)

    def feet_clear(self, px, py):
        offset = self.run.abi['room_solid']
        return all(not P.r8(self.c, P.sym('gRoom') + offset + y * 64 + x)
                   for y in range((py - 7) // 8, (py - 1) // 8 + 1)
                   for x in range((px - 4) // 8, (px + 3) // 8 + 1))

    def prepare(self, cell):
        self.request(cell)
        self.advance([], 24)
        info = self.info()
        px = (info.climb_x + 1) * 16 + 8
        defs = {n: int(v) for n, v in re.findall(r'^#define\s+(TT_\w+)\s+(\d+)\s*$',
                                               (self.run.bundle / 'assets.h').read_text(), re.M)}
        # The two profile columns can differ. The real route's dry approach
        # rectangle can replace the lower base painting, so find the actual
        # native floor/climb boundary instead of trusting a profile formula.
        feet = [y for y in range(23 * 16, 9 * 16, -1)
                if self.tile_type(px, y - 4) == defs['TT_FLOOR']
                and self.tile_type(px, y - 11) == defs['TT_CLIMB']
                and self.feet_clear(px, y)]
        if not feet:
            raise RuntimeError('no dry foot below actual local climb')
        py = feet[0]
        self.check('climb starts on dry physical floor below real shaft',
                   self.tile_type(px, py - 4) == defs['TT_FLOOR'] and self.feet_clear(px, py)
                   and self.tile_type(px, py - 11) == defs['TT_CLIMB'],
                   dict(x=px, y=py, climb_x=info.climb_x, ground=self.tile_type(px, py - 4)))
        self.nav(px, py, 0)
        self.advance([], 20)
        self.check('prepared hero remains alive below shaft', self.state()['health'][0] > 0
                   and self.state()['actor']['state'] == self.extra['enum_normal'], self.state())
        return dict(cell=info.cell, corruption=info.stage, motif=info.motif, climb_x=info.climb_x,
                    upper_bottom=list(info.upper_bottom), lower_top=list(info.lower_top),
                    terrace=[dict(content=t.content, chest=[t.chest.x, t.chest.y],
                                  npc=[t.npc.x, t.npc.y], mission=[t.mission.x, t.mission.y])
                             for t in info.terrace],
                    return_door=[info.return_door.x, info.return_door.y], dry_foot=[px, py])

    def semantics(self):
        a, address = self.run.abi, P.sym('gRoom')
        ground = raw(self.c, address + a['room_ground'], 2048)
        overlay = raw(self.c, address + a['room_overlay'], 2048)
        types = bytes(P.r8(self.c, P.sym('metatile_type') + mt) if mt != 65535 else 255
                      for mt in struct.unpack('<1024H', ground))
        overlay_types = bytes(P.r8(self.c, P.sym('metatile_type') + mt) if mt != 65535 else 255
                              for mt in struct.unpack('<1024H', overlay))
        solid = raw(self.c, address + a['room_solid'], 4096)
        occupancy = bytes(mt != 65535 for mt in struct.unpack('<1024H', overlay))
        return dict(room_raw_sha256=digest(raw(self.c, address, self.extra['room_size'])),
                    ground_types_sha256=digest(types), overlay_types_sha256=digest(overlay_types),
                    solid_sha256=digest(solid), overlay_occupancy_sha256=digest(occupancy),
                    climb_mask_sha256=digest(bytes(v == 26 for v in types)))

    def panorama(self, folder):
        folder.mkdir(exist_ok=True)
        clock = 256
        before_room = raw(self.c, P.sym('gRoom'), self.extra['room_size'])
        before_player = raw(self.c, P.sym('gPl'), self.run.abi['player_size'])
        before_world = raw(self.c, P.sym('gCreamWorld'), C.sizeof(G.World))
        before = self.state()
        before_semantics = self.semantics()
        xs, ys, xb, yb = (0, 136, 272), (0, 112, 224), (0, 188, 324, 512), (0, 136, 248, 384)
        mosaic, views, originals = Image.new('RGB', (512, 384)), [], []
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                P.w16(self.c, P.sym('gForestReviewCamera'), x)
                P.w16(self.c, P.sym('gForestReviewCamera') + 2, y)
                w32(self.c, P.sym('gForestReviewClock'), clock)
                P.w8(self.c, P.sym('gForestReviewEnabled'), 1)
                for _ in range(5):
                    w32(self.c, P.sym('gFrame'), clock - 1)
                    self.c.run_frame()
                    self.run.frames += 1
                im = self.c.bg_video.to_pil().convert('RGB').copy()
                file = 'camera-%d-%d.png' % (x, y)
                im.save(folder / file)
                world_crop = [xb[i], yb[j], xb[i + 1], yb[j + 1]]
                crop = [world_crop[0] - x, world_crop[1] - y,
                        world_crop[2] - x, world_crop[3] - y]
                mosaic.paste(im.crop(crop), world_crop[:2])
                originals.append(im)
                views.append(dict(camera=[x, y], file=file, world_crop=world_crop, source_crop=crop,
                                  png_sha256=sha(folder / file)))
        mosaic.save(folder / 'full-room.png')
        exact = all(mosaic.crop(v['world_crop']).tobytes() == im.crop(v['source_crop']).tobytes()
                    for v, im in zip(views, originals))
        unchanged = before_room == raw(self.c, P.sym('gRoom'), self.extra['room_size'])
        player_unchanged = before_player == raw(self.c, P.sym('gPl'), self.run.abi['player_size'])
        world_unchanged = before_world == raw(self.c, P.sym('gCreamWorld'), C.sizeof(G.World))
        self.check('registered panorama copies raw native pixels exactly', exact)
        self.check('frozen camera preserves room collision and all player fields', unchanged and player_unchanged)
        self.check('frozen camera preserves graph and player position/health', world_unchanged
                   and before['actor']['x'] == self.state()['actor']['x']
                   and before['actor']['y'] == self.state()['actor']['y']
                   and before['health'] == self.state()['health'])
        detail = dict(label='Registered renderer views and nine-camera crop mosaic; not ordinary gameplay frames',
                      method='Nine untouched 240x160 native mGBA PNGs; literal disjoint crops form 512x384.',
                      review_clock=clock, frame_assignment='gFrame=255 immediately before each frozen render only',
                      before=before, after=self.state(), room_unchanged=unchanged,
                      all_player_fields_unchanged=player_unchanged, graph_unchanged=world_unchanged,
                      crop_copy_exact=exact, semantics=before_semantics, views=views)
        write_json(folder / 'provenance.json', detail)
        self.run.fixtures.append(dict(kind='registered frozen HUD-free review camera', clock=clock,
                                      cameras=[v['camera'] for v in views]))
        # This private core is retired immediately; its forced renderer clock
        # never becomes the starting state of an ordinary live clip.
        P.w8(self.c, P.sym('gForestReviewEnabled'), 0)
        return detail

    def live(self, folder, cell):
        folder.mkdir(exist_ok=True)
        frames_folder = folder / 'raw-frames'
        frames_folder.mkdir(exist_ok=True)
        self.check('ordinary core never enables review camera', self.run.u8('gForestReviewEnabled') == 0)
        self.run.image('ordinary-start')
        self.c.bg_video.to_pil().convert('RGB').save(folder / 'start.png')
        before = self.state()
        pictures, trace = self.advance('UP', 260, stop=lambda st: st['node'] == cell * 2 + 1
                                      and st['actor']['state'] == self.extra['enum_normal'], record=frames_folder)
        after = self.state()
        self.check('real UP produces actual PS_CLIMB and upper-node arrival',
                   trace['climb_frames'] > 20 and before['node'] == cell * 2
                   and after['node'] == cell * 2 + 1 and after['actor']['state'] == self.extra['enum_normal'],
                   dict(before=before, after=after, climb_frames=trace['climb_frames']))
        self.check('live clip uses advancing simulation and positive health',
                   after['clock'] > before['clock'] and after['run_frames'] > before['run_frames']
                   and trace['minimum_health'] > 0 and self.run.u8('gForestReviewEnabled') == 0)
        self.c.bg_video.to_pil().convert('RGB').save(folder / 'landed.png')
        middle = next((row for row in pictures if row[2]['actor']['state'] == self.extra['enum_climb']
                       and row[0] >= trace['frames'] // 2), pictures[len(pictures) // 2])
        middle[1].save(folder / 'climbing.png')
        ims = [im for _, im, _, _ in pictures]
        ims[0].save(folder / 'climb.gif', save_all=True, append_images=ims[1:], duration=67, loop=0, optimize=False)
        detail = dict(label='Ordinary 240x160 live simulation with actual UP input',
                      before=before, after=after, frames=trace['frames'], sampled_every=4,
                      minimum_health=trace['minimum_health'], climb_frames=trace['climb_frames'],
                      assignments='No review camera/clock/frame assignments in this fresh ordinary core.',
                      raw_frames=[dict(frame=i, file='raw-frames/' + file, player=st['actor'],
                                       node=st['node'], health=st['health']) for i, _, st, file in pictures])
        write_json(folder / 'provenance.json', detail)
        return detail

    def identity(self):
        identity = self.run.report_identity()
        identity['input_method'] = 'Actual real keys plus individually disclosed seed, position/facing, room-load and registered-renderer fixtures.'
        # NativeRun retains detailed observations internally. Merge adjacent
        # identical key holds before publishing so a title/loading wait does
        # not produce hundreds of redundant per-frame snapshots.
        def compact(view):
            if view is None:
                return None
            return {key: view[key] for key in ('physical_frames', 'state', 'area',
                    'cell', 'actor', 'health', 'text', 'starting_draft', 'draft')
                    if key in view}
        inputs = []
        for row in self.run.inputs:
            initial, final = compact(row['initial']), compact(row['final'])
            if (inputs and inputs[-1]['keys'] == row['keys'] and
                    inputs[-1]['final']['physical_frames'] == initial['physical_frames']):
                inputs[-1]['frames'] += row['frames']
                inputs[-1]['final'] = final
            else:
                inputs.append(dict(keys=row['keys'], frames=row['frames'], initial=initial, final=final))
        identity['inputs'] = inputs
        identity['trace'] = self.trace
        identity['checks'] = self.checks
        identity['draft_choices'] = [{key: row[key] for key in ('round', 'index', 'item')} for row in self.draft]
        return identity


def select(world):
    """Choose the same semantic cases in every style using only graph data."""
    def local(cell):
        return any(e.kind == 2 and e.target == cell * 2 + 1 and e.require == 0
                   for e in world.edges[cell * 2][:world.degree[cell * 2]])
    def cave(cell):
        return any(e.kind == 4 for node in (cell * 2, cell * 2 + 1)
                   for e in world.edges[node][:world.degree[node]])
    def chest(cell):
        return bool((world.content[cell * 2] | world.content[cell * 2 + 1]) & 2)
    chosen = []
    for label, corruption in [('healthy', 0), ('sour', 1), ('deep', 2)]:
        candidates = [cell for cell in range(25) if world.corruption[cell] == corruption and local(cell)
                      and cell != world.goal_node // 2]
        if label == 'healthy' and world.entry_node // 2 in candidates:
            cell = world.entry_node // 2
        else:
            # Sour provides a cave, deep provides a chest, and unequal motifs
            # arise from the actual generated rooms rather than art fixtures.
            candidates.sort(key=lambda cell: (not (cave(cell) if label == 'sour' else chest(cell)), cell))
            if not candidates:
                raise RuntimeError('seed has no ungated local climb for ' + label)
            cell = candidates[0]
        edges = [dict(node=n, index=i, target=e.target, kind=e.kind, require=e.require, flags=e.flags)
                 for n in (cell * 2, cell * 2 + 1)
                 for i, e in enumerate(world.edges[n][:world.degree[n]])]
        chosen.append(dict(name=label, corruption=corruption, cell=cell, lower_node=cell * 2,
                           upper_node=cell * 2 + 1, cave=cave(cell), chest=chest(cell),
                           entry=cell == world.entry_node // 2, edges=edges))
    return chosen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--seed', type=lambda text: int(text, 0), default=0xb4a7)
    args = parser.parse_args()
    bundle, out = Path(args.bundle).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    initial = Capture(bundle, out / 'private-cores/healthy-renderer', args.seed)
    cases = select(initial.world)
    selection = dict(seed=args.seed, generated_seed=initial.world.seed, graph=G.plain(initial.world),
                     graph_sha256=digest(bytes(initial.world)), cases=cases)
    write_json(out / 'selection.json', selection)
    report = dict(source_commit=(bundle / 'source-commit.txt').read_text().strip(),
                  rom_sha256=sha(bundle / 'bartgame.gba'), tool_sha256=sha(__file__),
                  seed=args.seed, generated_seed=initial.world.seed, graph_sha256=selection['graph_sha256'],
                  cases=[], complete=False,
                  scope='Art comparison, not an earned progression route. Fresh private cores per registered renderer and ordinary live case.',
                  prohibited_writes='No player health/inventory/equipment, enemy, progression, gate, terrain, palette, VRAM or framebuffer assignments. No player action/z/standing override.')
    write_json(out / 'report.json', report)
    try:
        for case in cases:
            name, cell = case['name'], case['cell']
            folder = out / name
            folder.mkdir(exist_ok=True)
            renderer = initial if name == 'healthy' else Capture(bundle, out / ('private-cores/' + name + '-renderer'), args.seed)
            info = renderer.prepare(cell)
            panorama = renderer.panorama(folder / 'registered-renderer')
            write_json(folder / 'renderer-trace.json', renderer.identity())
            live = Capture(bundle, out / ('private-cores/' + name + '-live'), args.seed)
            live_info = live.prepare(cell)
            assert info == live_info
            semantics = live.semantics()
            live.check('fresh renderer and ordinary cores have identical room semantics',
                       semantics == panorama['semantics'])
            live_case = live.live(folder / 'ordinary-live', cell)
            write_json(folder / 'live-input-trace.json', live.identity())
            checks = renderer.checks + live.checks
            report['cases'].append(dict(**case, info=info, semantics=semantics,
                                        panorama=dict(file=name + '/registered-renderer/full-room.png',
                                                      room_unchanged=panorama['room_unchanged'],
                                                      all_player_fields_unchanged=panorama['all_player_fields_unchanged'],
                                                      crop_copy_exact=panorama['crop_copy_exact']),
                                        live=dict(file=name + '/ordinary-live/climb.gif',
                                                  frames=live_case['frames'], minimum_health=live_case['minimum_health'],
                                                  climb_frames=live_case['climb_frames']),
                                        checks=checks))
            write_json(out / 'report.json', report)
        report['complete'] = all(check['passed'] for case in report['cases'] for check in case['checks'])
    finally:
        write_json(out / 'report.json', report)
    return 0 if report['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
