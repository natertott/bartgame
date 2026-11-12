#!/usr/bin/env python3
"""Qualify Cream's sixth art study with real mGBA pixels and real drops.

The matched room/climb suite delegates to cream_art_study_capture.py. Its
registered 512x384 mosaics are explicitly frozen camera crops, not a GBA
framebuffer. Ordinary clips use separate live cores and actual keys.

Isolated drop views disclose a normal room-load request and living hero
position/facing navigation. They do not grant tools or open gates. Optional
earned long-drop footage reuses the existing real-input trial/gate harness
with a read-only Python observer of the visual landing cache. No game art,
collision, health, inventory, enemy, progression, VRAM or pixels are assigned.
"""
import argparse
import ctypes as C
import json
from pathlib import Path
import runpy
import struct
import subprocess
import sys

from cream_art_study_capture import Capture, digest, raw, write_json
import probe as P
from regional_native_support import sha

TOOLS = Path(__file__).resolve().parent
PHYSICAL = ('ground_types_sha256', 'overlay_types_sha256', 'solid_sha256',
            'overlay_occupancy_sha256', 'climb_mask_sha256')


class Landing(C.Structure):
    _fields_ = [('x', C.c_int16), ('y', C.c_int16), ('from_node', C.c_uint8),
                ('edge', C.c_uint8), ('x0', C.c_uint8), ('y0', C.c_uint8),
                ('parts', C.c_uint8), ('flags', C.c_uint8)]


def landing_abi(bundle, folder, headers):
    """Compile cache layout from the exact ROM's archived ARM headers."""
    folder.mkdir(parents=True, exist_ok=True)
    fields = ('x', 'y', 'from', 'edge', 'x0', 'y0', 'parts', 'flags')
    expressions = ['sizeof(CreamVisualLanding)', 'CC_NODES*CC_EDGE_MAX']
    expressions += ['offsetof(CreamVisualLanding,%s)' % name for name in fields]
    expressions += ['offsetof(Room,ground)', 'offsetof(CreamRoomInfo,stage)']
    source = '#include <stddef.h>\n#include "cream_visuals.h"\n#include "cream_room.h"\n#include "room.h"\n'
    source += 'const unsigned values[] __attribute__((used,section(".landing_abi")))={'
    source += ','.join(expressions) + '};\n'
    unit, obj, binary = (folder / name for name in ('abi.c', 'abi.o', 'abi.bin'))
    unit.write_text(source)
    command = ['arm-none-eabi-gcc', '-mcpu=arm7tdmi', '-mthumb', '-std=c99',
               '-DBART_FOREST_VARIANT=32', '-I', str(headers), '-c', str(unit), '-o', str(obj)]
    built = subprocess.run(command, capture_output=True, text=True)
    (folder / 'compile.log').write_text(built.stdout + built.stderr)
    built.check_returncode()
    subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', '-j', '.landing_abi',
                    str(obj), str(binary)], check=True)
    values = struct.unpack('<' + 'I' * len(expressions), binary.read_bytes())
    assert values[0] == C.sizeof(Landing)
    for index, field in enumerate(fields):
        python_field = 'from_node' if field == 'from' else field
        assert values[index + 2] == getattr(Landing, python_field).offset
    result = dict(source_commit=(bundle / 'source-commit.txt').read_text().strip(),
                  source_sha256=sha(unit), command=command,
                  size=values[0], capacity=values[1], offsets=dict(zip(fields, values[2:10])),
                  room_ground=values[10], info_stage=values[11])
    write_json(folder / 'provenance.json', result)
    return result


def read_landings(core, abi):
    count = P.r16(core, P.sym('gCreamVisualLandingCount'))
    if count > abi['capacity']:
        raise AssertionError('landing cache count exceeds its real capacity')
    address = P.sym('gCreamVisualLandings')
    result = []
    for index in range(count):
        entry = Landing.from_buffer_copy(raw(core, address + index * abi['size'], abi['size']))
        stage = P.r8(core, P.sym('gCreamRoom') + abi['info_stage'])
        verified_parts, paintings = 0, []
        for part in range(6):
            if not (entry.parts & (1 << part)):
                continue
            xx, yy = entry.x0 + part % 3, entry.y0 + part // 3
            mt = P.r16(core, P.sym('gRoom') + abi['room_ground'] + (yy * 32 + xx) * 2)
            expected = [P.r16(core, P.sym('cream_visual_landing') + (stage * 6 + part) * 2)]
            expected += [P.r16(core, P.sym('cream_visual_landing_path') +
                              (stage * 24 + variant * 6 + part) * 2) for variant in range(4)]
            if mt in expected:
                verified_parts |= 1 << part
            paintings.append(dict(part=part, cell=[xx, yy], actual_metatile=mt,
                                  valid_shadow_metatiles=expected, actual_match=mt in expected))
        result.append(dict(x=entry.x, y=entry.y, from_node=entry.from_node,
                           edge=entry.edge, x0=entry.x0, y0=entry.y0,
                           parts=entry.parts, flags=entry.flags,
                           verified_parts=verified_parts, final_ground_parts=paintings))
    return result


def in_shadow(entry, actor):
    # The engine's collision/standing probe is four pixels above the feet.
    tx, ty = actor['x'] // 16, (actor['y'] - 4) // 16
    xx, yy = tx - entry['x0'], ty - entry['y0']
    part = yy * 3 + xx
    return 0 <= xx < 3 and 0 <= yy < 2 and bool(entry.get('verified_parts', entry['parts']) & (1 << part))


class DepthCapture(Capture):
    def __init__(self, bundle, out, seed):
        super().__init__(bundle, out, seed)
        self.landing_layout = landing_abi(self.run.bundle, self.run.out / 'landing-abi',
                                          self.run.out / 'abi/headers')

    def request_node(self, node):
        """The same ordinary load fixture as the earlier art suite, with terrace."""
        before = self.state()
        if before['node'] == node:
            return
        for name, value in [('sNextArea', 3), ('sNextCell', node // 2), ('sNextSide', 2),
                            ('sTransPhase', 0), ('sCreamNextNode', node),
                            ('sCreamNextFacing', 0), ('sCreamDropRows', 0)]:
            address = next(self.run.sections[prefix + name] for prefix in
                           ('.bss.', '.data.', '.ewram_bss.') if prefix + name in self.run.sections)
            P.w8(self.c, address, value)
        for name in ('sCreamNextX', 'sCreamNextY'):
            address = next(self.run.sections[prefix + name] for prefix in
                           ('.bss.', '.data.', '.ewram_bss.') if prefix + name in self.run.sections)
            P.w16(self.c, address, 65535)
        P.w8(self.c, P.sym('gGame') + self.run.abi['game_state'], self.run.abi['enum_transition'])
        self.run.fixtures.append(dict(kind='ordinary room-load request for isolated drop visual',
                                      cell=node // 2, node=node, before=before))
        self.run.settle(3)
        self.run.dismiss()
        self.advance([], 30)
        self.check('ordinary room request selects source physical terrace', self.state()['node'] == node,
                   self.state())

    def shadows(self):
        return read_landings(self.c, self.landing_layout)

    def metrics(self):
        names = ('PanelCount', 'PanelCells', 'RimCount', 'DropCount', 'ToeCount')
        return {name: P.r16(self.c, P.sym('gCreamVisual' + name)) for name in names}

    def drop(self, folder, node, edge_index):
        folder.mkdir(parents=True, exist_ok=True)
        frames = folder / 'raw-frames'
        frames.mkdir(exist_ok=True)
        edge = self.world.edges[node][edge_index]
        self.check('isolated drop uses a real ungated DROP graph edge',
                   edge.kind == 3 and edge.require == 0,
                   dict(node=node, edge=edge_index, target=edge.target, require=edge.require))
        self.request_node(node)
        info = self.info()
        xx = 27 if edge.flags & 1 else 10 if node & 1 else info.climb_x
        yy = min(info.upper_bottom[xx], info.upper_bottom[xx + 1]) if node & 1 else 22
        self.nav(xx * 16 + 16, yy * 16 + 12, 2)
        self.advance([], 3)
        before = self.state()
        source_metrics = self.metrics()
        self.check('drop begins standing at an open dry physical sill',
                   self.feet_clear(before['actor']['x'], before['actor']['y'])
                   and before['actor']['state'] == self.extra['enum_normal']
                   and before['actor']['z'] == 0 and before['health'][0] > 0, before)
        self.c.bg_video.to_pil().convert('RGB').save(folder / 'before.png')
        pictures, trace = self.advance('DOWN', 650,
            stop=lambda state: state['state'] == 1 and state['node'] == edge.target
            and state['actor']['state'] == self.extra['enum_normal'] and state['actor']['z'] == 0,
            record=frames)
        after = self.state()
        shadows = self.shadows()
        own = [entry for entry in shadows if entry['from_node'] == node and entry['edge'] == edge_index]
        self.check('real DOWN enters a committed fall with positive height',
                   any(state['actor']['z'] > 0 for _, _, state, _ in pictures))
        self.check('actual fall lands upright on requested node with positive health',
                   after['node'] == edge.target and after['actor']['state'] == self.extra['enum_normal']
                   and after['actor']['z'] == 0 and trace['minimum_health'] > 0, after)
        self.check('real landing has exactly its authoritative incoming shadow record', len(own) == 1, own)
        if own:
            self.check('actual landing feet match recorded arrival exactly',
                       after['actor']['x'] == own[0]['x'] and after['actor']['y'] == own[0]['y'],
                       dict(actor=after['actor'], landing=own[0]))
            self.check('actual landing overlaps an actually painted shadow part',
                       in_shadow(own[0], after['actor']), own[0])
        self.c.bg_video.to_pil().convert('RGB').save(folder / 'landed.png')
        self.advance([], 24, record=None)
        images = [image for _, image, _, _ in pictures]
        images.extend([self.c.bg_video.to_pil().convert('RGB').copy()] * 8)
        images[0].save(folder / 'drop.gif', save_all=True, append_images=images[1:],
                       duration=67, loop=0, optimize=False)
        self.check('drop clip never enabled the frozen review camera', self.run.u8('gForestReviewEnabled') == 0)
        detail = dict(label='Ordinary native240x160 real DOWN fall; isolated navigation/load fixtures',
                      node=node, edge=edge_index, target=edge.target, before=before, after=after,
                      minimum_health=trace['minimum_health'], frames=trace['frames'],
                      source_metrics=source_metrics, landing_metrics=self.metrics(), landing_cache=shadows,
                      ordinary_review_camera=self.run.u8('gForestReviewEnabled'),
                      raw_frames=[dict(frame=i, file='raw-frames/' + file, state=state)
                                  for i, _, state, file in pictures])
        write_json(folder / 'provenance.json', detail)
        write_json(folder / 'input-trace.json', self.identity())
        return detail


def isolated_drops(bundle, out, seed):
    report = dict(seed=seed, rom_sha256=sha(bundle / 'bartgame.gba'), cases=[], complete=False)
    # Separate cores prevent the renderer fixture or a preceding fall from
    # changing the next test's physical state, enemies, health or clock.
    for kind in ('local', 'one-row'):
        capture = DepthCapture(bundle, out / ('private-cores/' + kind), seed)
        candidates = [(node, index, edge) for node in range(50)
                      for index, edge in enumerate(capture.world.edges[node][:capture.world.degree[node]])
                      if edge.kind == 3 and edge.require == 0 and
                      ((edge.target // 2 == node // 2) if kind == 'local' else
                       (edge.target // 10 == node // 10 + 1 and edge.target // 2 != node // 2))]
        if not candidates:
            raise AssertionError('no ungated ' + kind + ' drop for visual fixture')
        # Prefer the entry review room, then the other matched cases. The
        # destination is a secondary preference for incoming one-row falls.
        # This is graph selection, not an enemy/health/outcome modification.
        priority = {21: 0, 18: 1, 0: 2}
        candidates.sort(key=lambda row: (priority.get(row[0] // 2, 3),
                                         priority.get(row[2].target // 2, 3), row[0]))
        node, index, edge = candidates[0]
        detail = capture.drop(out / kind, node, index)
        report['cases'].append(dict(kind=kind, detail=detail, checks=capture.checks))
        write_json(out / 'report.json', report)
    report['complete'] = all(row['passed'] for case in report['cases'] for row in case['checks'])
    write_json(out / 'report.json', report)
    return report


def observe_runtime(bundle, out, seed):
    """Run the established earned-gate harness with an observation-only hook."""
    from regional_native_support import compile_abi
    compile_abi(bundle, out / 'observer-abi')
    abi = landing_abi(bundle, out / 'landing-abi', out / 'observer-abi/headers')
    script = TOOLS / 'cream_runtime_review.py'
    observations = []
    last = None

    def observe(frame, event, arg):
        nonlocal last
        if event != 'return' or frame.f_code.co_name != 'status' or Path(frame.f_code.co_filename) != script:
            return
        context = frame.f_globals
        if context.get('active_capture') is None or not isinstance(arg, dict):
            return
        core = context.get('c')
        if core is None or arg.get('area') != 3:
            return
        clock = P.r32(core, P.sym('gFrame'))
        if clock == last:
            return
        last = clock
        observations.append(dict(clock=clock, state=arg.copy(), landings=read_landings(core, abi)))

    sys.argv = [str(script), '--bundle', str(bundle), '--out', str(out / 'earned-runtime'),
                '--seed', str(seed), '--stop-after-long-drop']
    code = 0
    try:
        sys.setprofile(observe)
        runpy.run_path(str(script), run_name='__main__')
    except SystemExit as exit_code:
        code = exit_code.code or 0
    finally:
        sys.setprofile(None)
        write_json(out / 'read-only-cache-observations.json', observations)
    long_drop = out / 'earned-runtime/long-drop.json'
    checks = []
    if code == 0 and long_drop.exists():
        detail = json.loads(long_drop.read_text())
        target = detail['frames'][-1]['node']
        upright = [row for row in observations if row['state']['node'] == target
                   and row['state']['actor']['z'] == 0 and row['state']['actor']['state'] == 0]
        chosen = upright[0] if upright else None
        matching = [] if chosen is None else [entry for entry in chosen['landings']
                    if entry['flags'] & 1 and entry['x'] == chosen['state']['actor']['x']
                    and entry['y'] == chosen['state']['actor']['y']]
        checks += [dict(name='earned input harness finishes requested multiroom drop', passed=code == 0),
                   dict(name='actual long fall traverses at least three room rows', passed=detail['span'] >= 3,
                        observed=dict(span=detail['span'], cells=detail['cells'])),
                   dict(name='actual upright long landing has exact incoming visual anchor',
                        passed=bool(matching), observed=dict(landing=chosen, matching=matching)),
                   dict(name='actual long landing overlaps a painted landing shadow',
                        passed=bool(chosen and any(in_shadow(entry, chosen['state']['actor']) for entry in matching)))]
    else:
        checks.append(dict(name='earned input harness produced requested multiroom drop', passed=False,
                           observed=dict(exit_code=code, long_drop_exists=long_drop.exists())))
    report = dict(rom_sha256=sha(bundle / 'bartgame.gba'), seed=seed,
                  observer='Python return observer reads cache only while established harness captures a drop.',
                  observed_harness_sha256=sha(script), observer_sha256=sha(__file__),
                  observations=len(observations), checks=checks,
                  complete=all(row['passed'] for row in checks))
    write_json(out / 'report.json', report)
    return 0 if report['complete'] else 1


def run_logged(command, log):
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('w') as output:
        subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--seed', type=lambda text: int(text, 0), default=0xb4a7)
    parser.add_argument('--compare', action='append', default=[], metavar='LABEL=BUNDLE')
    parser.add_argument('--earned-long', action='store_true')
    parser.add_argument('--observe-runtime', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--existing-matched', help='reuse this exact bundle\'s completed matched capture')
    args = parser.parse_args()
    bundle, out = Path(args.bundle).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.observe_runtime:
        return observe_runtime(bundle, out, args.seed)
    selected = out / 'matched/style-6'
    if args.existing_matched:
        selected = Path(args.existing_matched).resolve()
    else:
        run_logged([sys.executable, str(TOOLS / 'cream_art_study_capture.py'), '--bundle', str(bundle),
                    '--out', str(selected), '--seed', str(args.seed)], out / 'logs/matched-style-6.log')
    candidate = json.loads((selected / 'report.json').read_text())
    assert candidate['complete'] and candidate['rom_sha256'] == sha(bundle / 'bartgame.gba')
    report = dict(rom_sha256=candidate['rom_sha256'], source_commit=candidate['source_commit'],
                  tool_sha256=sha(__file__), matched_capture=str(selected), checks=[], comparisons=[], complete=False)
    for specification in args.compare:
        label, source = specification.split('=', 1)
        baseline_bundle = Path(source).resolve()
        baseline_out = out / 'matched' / label
        run_logged([sys.executable, str(TOOLS / 'cream_art_study_capture.py'), '--bundle', str(baseline_bundle),
                    '--out', str(baseline_out), '--seed', str(args.seed)], out / ('logs/matched-' + label + '.log'))
        baseline = json.loads((baseline_out / 'report.json').read_text())
        checks = [dict(name='identical generated graph', passed=candidate['graph_sha256'] == baseline['graph_sha256'])]
        for new, old in zip(candidate['cases'], baseline['cases']):
            checks.append(dict(name=new['name'] + ': identical profile/features', passed=new['info'] == old['info']))
            for field in PHYSICAL:
                checks.append(dict(name=new['name'] + ': ' + field,
                                   passed=new['semantics'][field] == old['semantics'][field]))
        report['comparisons'].append(dict(label=label, rom_sha256=baseline['rom_sha256'],
                                           report=str(baseline_out / 'report.json'), checks=checks))
        report['checks'].extend(checks)
    drops = isolated_drops(bundle, out / 'isolated-drops', args.seed)
    report['checks'].append(dict(name='ordinary isolated drop clips pass', passed=drops['complete']))
    if args.earned_long:
        long_folder = out / 'earned-long'
        run_logged([sys.executable, str(Path(__file__).resolve()), '--observe-runtime', '--bundle', str(bundle),
                    '--out', str(long_folder), '--seed', '1432'], out / 'logs/earned-four-row.log')
        long_report = json.loads((long_folder / 'report.json').read_text())
        report['checks'].append(dict(name='earned four-row landing proof passes', passed=long_report['complete']))
    report['complete'] = all(row['passed'] for row in report['checks'])
    write_json(out / 'report.json', report)
    return 0 if report['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
