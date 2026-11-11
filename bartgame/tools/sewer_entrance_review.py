"""Walk from the real Drain spawn to its new doors in the actual ROM.

The only memory fixture is the title's deterministic seed. Movement, facing,
shield strafe, arch activation, return and the optional entitlement toggle use
real button inputs. Private copied ROM/SRAM isolates all saves. No hero position,
state, inventory, gate, meta, collision, camera, audio or pixels are assigned.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import probe as P
import critical_path as C
import release_boundary_review as B


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    bundle, out = args.bundle.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / 'private').mkdir(exist_ok=True)
    shutil.copy2(bundle / 'bartgame.gba', out / 'private/bartgame.gba')
    P.ROM = str(out / 'private/bartgame.gba')
    P.MAP = str(bundle / 'bartgame.map')
    P._syms = None
    checks, cases, inputs = [], {}, []
    movie, active = [], ''

    def status(c):
        return B.status(c)

    def check(name, ok, observed=None):
        checks.append(dict(name=name, passed=bool(ok), observed=observed))
        print(('PASS ' if ok else 'FAIL ') + name, flush=True)

    def snap(c, name):
        P.snap(c, str(out / (name + '.png')))

    def keyframe(c):
        return c.bg_video.to_pil().convert('RGB').copy()

    def frames(c, keys, count, record=False, until_area=None):
        if isinstance(keys, str):
            keys = [keys]
        inputs.append(dict(case=active, keys=keys, frames=count,
                           initial=status(c)))
        c.set_keys(*(P.key(c, k) for k in keys))
        for i in range(count):
            c.run_frame()
            if record and i % 4 == 0:
                movie.append(keyframe(c))
            if until_area is not None and C.area(c) == until_area and C.gstate(c) == 1:
                break
        c.clear_keys(*(P.key(c, k) for k in keys))
        inputs[-1]['final'] = status(c)

    def walk(c, x, y):
        for _ in range(600):
            px, py = P.player_pos(c)
            if abs(px-x) <= 1 and abs(py-y) <= 1:
                return True
            key = ('RIGHT' if x > px else 'LEFT') if abs(px-x) > 1 else ('DOWN' if y > py else 'UP')
            frames(c, key, 1)
        return False

    def boot_case(name, door):
        nonlocal active, movie
        active, movie = name, []
        c = P.boot(rom=P.ROM)
        C.dismiss(c)
        start = status(c)
        check(name + ': ordinary fresh Drain spawn', C.area(c) == 0 and P.player_pos(c) == (200, 270), start)
        route = [(248, 270), (248, 142), (door, 142), (door, 131)]
        ok = all(walk(c, x, y) for x, y in route)
        check(name + ': walk to arch approach using only D-pad', ok and C.area(c) == 0, status(c))
        cases[name] = dict(start=start, approach=status(c))
        snap(c, name + '-approach')
        return c

    def save_movie(name):
        if movie:
            movie[0].save(out / (name + '.gif'), save_all=True,
                          append_images=movie[1:], duration=67, loop=0)

    # The old release happened to pass this exact front-of-arch case.
    c = boot_case('cream-front-A', 456)
    frames(c, 'A', 2, True)
    frames(c, [], 100, True)
    check('Cream: A below arch enters', C.area(c) == 3 and C.gstate(c) == 1, status(c))
    cases[active]['arrival'] = status(c)
    snap(c, 'cream-front-A-arrival')
    if C.area(c) == 3:
        frames(c, 'A', 2)
        frames(c, [], 100)
        check('Cream: real stairs return to matching Drain arch', C.area(c) == 0 and P.player_pos(c) == (456, 130), status(c))
        frames(c, [], 180)
        check('Cream: return does not immediately re-enter', C.area(c) == 0 and P.player_pos(c) == (456, 130), status(c))
        snap(c, 'cream-return-no-bounce')
    save_movie('cream-front-A')

    c = boot_case('cream-walk', 456)
    frames(c, 'UP', 200, True, until_area=3)
    check('Cream: naturally walking into stairs enters', C.area(c) == 3 and C.gstate(c) == 1, status(c))
    cases[active]['arrival'] = status(c)
    snap(c, 'cream-walk-result')
    save_movie('cream-walk')

    # Shield holds a south-facing pose during northward movement. This reaches
    # the visible arch without satisfying its north-facing automatic trigger.
    c = boot_case('cream-visible-A', 456)
    frames(c, 'DOWN', 1)
    frames(c, ['L', 'UP'], 46, True)
    frames(c, [], 2)
    before = status(c)
    check('Cream: natural shield strafe reaches visible arch', C.area(c) == 0 and P.player_pos(c)[1] < 109 and P.actor(c, 0)['facing'] == 2, before)
    snap(c, 'cream-visible-A-before')
    frames(c, 'A', 2, True)
    frames(c, [], 100, True)
    check('Cream: A works inside visible arch, any facing', C.area(c) == 3 and C.gstate(c) == 1, status(c))
    cases[active]['before_A'], cases[active]['arrival'] = before, status(c)
    snap(c, 'cream-visible-A-result')
    save_movie('cream-visible-A')

    c = boot_case('annex-walk', 280)
    frames(c, 'UP', 200, True, until_area=4)
    check('Annex: naturally walking into arch enters', C.area(c) == 4 and C.gstate(c) == 1, status(c))
    cases[active]['arrival'] = status(c)
    snap(c, 'annex-walk-result')
    save_movie('annex-walk')

    # Open the actual Trophy desk and toggle the optional mode through its UI.
    # All six profile bytes remain untouched by the test.
    c = boot_case('entitlement', 280)
    frames(c, 'A', 2)
    frames(c, [], 100)
    if C.area(c) == 4:
        ok = walk(c, 120, 334) and walk(c, 120, 258)
        frames(c, 'A', 2)
        frames(c, [], 4)
        frames(c, 'DOWN', 2)
        frames(c, [], 4)
        frames(c, 'A', 2)
        frames(c, [], 4)
        # Observe each dismissal edge: the menu's own input-lock may consume
        # an immediate A press, and the message can span multiple text pages.
        for _ in range(40):
            if not P.r8(c, P.sym('gTbActive')):
                break
            frames(c, 'A', 2)
            frames(c, [], 12)
        mode = P.r8(c, P.sym('gHandoffState') + 12)
        check('Entitlement: actual Trophy UI enables optional mode', ok and mode == 1 and not P.r8(c, P.sym('gTbActive')), status(c))
        # Walk out through the existing southern threshold.
        ok = walk(c, 264, 258)
        frames(c, 'DOWN', 200, until_area=0)
        frames(c, [], 40)
        check('Annex: southern walk returns to matching arch without bounce', ok and C.area(c) == 0 and P.player_pos(c) == (280, 130), status(c))
        ok = walk(c, 280, 142) and walk(c, 456, 142) and walk(c, 456, 131)
        frames(c, 'UP', 100, True)
        first = B.text_message(c)
        check('Entitlement: locked ascent explains its requirement', ok and C.area(c) == 0 and '500' in first and 'Entitlement' in first, dict(status=status(c), message=first))
        # Continue holding UP while dismissing the mature text; the same hold
        # must not immediately reopen the box.
        c.set_keys(P.key(c, 'UP'))
        P.run(c, 120)
        for _ in range(5):
            if not P.r8(c, P.sym('gTbActive')):
                break
            c.set_keys(P.key(c, 'UP'), P.key(c, 'A'));P.run(c, 2)
            c.set_keys(P.key(c, 'UP'));P.run(c, 8)
        reopened = []
        for i in range(300):
            c.run_frame()
            if P.r8(c, P.sym('gTbActive')):
                reopened.append(i)
        c.clear_keys(P.key(c, 'UP'))
        check('Entitlement: one continuous UP hold does not spam denial', not reopened and C.area(c) == 0, dict(reopened_frames=reopened, final=status(c)))
        frames(c, [], 2)
        frames(c, 'A', 2)
        frames(c, [], 10)
        check('Entitlement: a new A request still explains the locked arch', P.r8(c, P.sym('gTbActive')) and '500' in B.text_message(c), status(c))
        snap(c, 'entitlement-locked-arch')
    else:
        check('Entitlement: Annex entry prerequisite', False, status(c))

    report = dict(method=__doc__, rom_sha256=hashlib.sha256(Path(P.ROM).read_bytes()).hexdigest(),
                  source_commit=(bundle/'source-commit.txt').read_text().strip(),
                  tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  checks=checks, cases=cases, inputs=inputs,
                  passed=sum(x['passed'] for x in checks), total=len(checks))
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('RESULT', report['passed'], '/', report['total'])
    raise SystemExit(report['passed'] != report['total'])


if __name__ == '__main__':
    main()
