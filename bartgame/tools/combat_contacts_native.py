#!/usr/bin/env python3
"""Check Bloom's live sword, body contacts, projectiles, walk and roll in mGBA.

The reviewed ROM runs in a private core. Disclosed fixtures set the title
seed, an unobstructed practice floor, Bloom's position/facing/loadout, and
stationary targets spawned through the game's normal enemy constructor.
Projectile fixtures use ordinary projectile records. Controller inputs and
the ROM's own update code produce all movement, attacks, misses and damage.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import bloom_probe as B
import critical_path as C
import lift_probe as L
import probe as P
import wood_probe as W


DIRECTIONS = ('UP', 'RIGHT', 'DOWN', 'LEFT')
FORWARD = ((0, -1), (1, 0), (0, 1), (-1, 0))
FOOT = (256, 230)
AK_ENEMY, AK_PROJ = 2, 3
PS_NORMAL, PS_ROLL, PS_ATTACK, PS_HURT = 0, 1, 2, 3


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Review:
    def __init__(self, bundle, out, seed):
        self.bundle, self.out, self.seed = bundle, out, seed
        self.out.mkdir(parents=True, exist_ok=True)
        self.checks, self.fixtures, self.media = [], [], []
        self.defs = B.configure(SimpleNamespace(map=bundle/'bartgame.map', assets_header=bundle/'assets.h'))
        rom = out/'review.gba'
        shutil.copyfile(bundle/'bartgame.gba', rom)
        for path in out.glob('review.gba.sav*'):
            path.unlink()
        P.ROM = str(rom)
        self.core = P.boot(rom=P.ROM, seed=seed)
        C.dismiss(self.core)
        entry = C.world(self.core)['entry']
        L.warp(self.core, entry, 2)
        B.clear_actors(self.core)
        B.floor_fixture(self.core, self.defs)
        self.hero, self.player = P.sym('gActors'), P.sym('gPl')
        self.base = self.core.save_raw_state()
        self.fixtures.append(dict(case='initial practice floor and private core', seed=seed, foot=FOOT,
                                  room=entry, room_request='normal Forest loader'))

    def check(self, label, passed, observed=None):
        self.checks.append(dict(name=label, passed=bool(passed), observed=observed))
        print(('PASS ' if passed else 'FAIL ')+label, flush=True)

    def shot(self, name):
        file = self.out/(name+'.png')
        P.snap(self.core, str(file))
        self.media.append(dict(file=file.name, sha256=sha(file)))

    def reset(self, facing=0, equipment=(0, 1, 5)):
        assert self.core.load_raw_state(self.base), 'mGBA practice state did not restore'
        B.reset_player(self.core, *FOOT, facing, equipment)

    def tick(self, *keys):
        P.hold(self.core, list(keys), 1)

    def w32(self, address, value):
        P.w16(self.core, address, value & 0xffff)
        P.w16(self.core, address + 2, (value >> 16) & 0xffff)

    def target(self, x, y, z=0, enemy=0, contact=False):
        index = W.spawn_enemy(self.core, enemy, 100, 100)
        at = self.hero + index * P.ACTOR_SIZE
        self.w32(at + 8, x << 16)
        self.w32(at + 12, y << 16)
        self.w32(at + 16, z << 16)
        self.w32(at + 20, 0)
        P.w8(self.core, at + 29, 180)  # ordinary recoil holds the isolated body
        P.w16(self.core, at + 32, 0)
        if not contact:
            flags = P.r8(self.core, at + 31)
            P.w8(self.core, at + 31, flags & ~(4 | 8))
        self.fixtures.append(dict(case='stationary native enemy', enemy=enemy, index=index,
                                  initial=P.actor(self.core, index), body_contact=contact,
                                  hitbox=P.r8(self.core, at + 34)))
        return index

    def attack(self, index=None, photo=None, projectile=None):
        start = P.actor(self.core, index)['hp'] if index is not None else 0
        records = []
        active_seen = 0
        self.tick('B')
        for _ in range(40):
            state = dict(B.live(self.core), hp=P.r16(self.core, self.player))
            if index is not None:
                actor = P.actor(self.core, index)
                state['target'] = actor
                state['hit'] = actor['kind'] != AK_ENEMY or actor['hp'] < start
            if projectile is not None:
                address = self.hero + projectile * P.ACTOR_SIZE
                state['projectile'] = dict(P.actor(self.core, projectile),
                                           reflected=bool(P.r8(self.core, address + 48)),
                                           direction=P.r8(self.core, address + 6))
            records.append(state)
            if state['active']:
                active_seen += 1
                if photo and active_seen == 4:
                    self.shot(photo)
            if state['state'] != PS_ATTACK:
                break
            self.tick()
        return records

    def angled_contact(self, facing, forward, z, expect_hit):
        self.reset(facing)
        dx, dy = FORWARD[facing]
        length = 24 if forward else -20
        # The native Beetle's hurtbox is five pixels higher relative to
        # Bloom's anchor. Adjust world y by z to hold projection constant.
        point = (FOOT[0] + length * dx, FOOT[1] - 5 + length * dy + z)
        index = self.target(*point, z=z)
        report = self.attack(index, f'attack-{DIRECTIONS[facing].lower()}' if forward and z == 0 else None)
        first = next((r for r in report if r['hit']), None)
        return bool(first) == expect_hit and (first is None or first['active']), report

    def sword(self):
        for facing, name in enumerate(DIRECTIONS):
            hit, report = self.angled_contact(facing, True, 0, True)
            self.check(f'{name} blade damages a same-plane enemy ahead', hit, report)
            self.check(f'{name} sword contact is live only during the committed cut',
                       [r['timer'] for r in report if r['active']] == list(range(2, 10))
                       and report[0]['state'] == PS_ATTACK and report[-1]['state'] == PS_NORMAL
                       and len(report) == 16, report)
            result, behind = self.angled_contact(facing, False, 0, False)
            self.check(f'{name} blade misses the enemy behind Bloom', result, behind)
            result, low = self.angled_contact(facing, True, 6, True)
            self.check(f'{name} blade still touches a low airborne target', result, low)
            result, high = self.angled_contact(facing, True, 24, False)
            self.check(f'{name} blade misses a higher enemy whose projection overlaps', result, high)
        for z, hit in ((12, True), (13, False)):
            result, report = self.angled_contact(0, True, z, hit)
            self.check(f'projected front contact observes the sword depth boundary at {z} px', result, report)

    def body_contacts(self):
        for type_, separation, z, hit, label in (
                (0, 9, 0, True, 'the edge of the small Beetle body'),
                (0, 10, 0, False, 'one pixel beyond the small Beetle body'),
                (3, 10, 0, True, 'the wider Slime body'),
                (0, 9, 24, False, 'a projected but vertically separated enemy')):
            self.reset(1)
            index = self.target(FOOT[0] + separation, FOOT[1] - 5 + z, z=z, enemy=type_, contact=True)
            before = P.r16(self.core, self.player)
            self.tick()
            after = P.r16(self.core, self.player)
            self.check(f'body overlap behaves independently at {label}', (before > after) == hit,
                       dict(before=before, after=after, target=P.actor(self.core, index)))

    def confessor(self):
        self.reset(3)
        index = W.spawn_enemy(self.core, 4, FOOT[0] - 20, FOOT[1], facing=1)
        foe = lambda: P.actor(self.core, index)
        self.fixtures.append(dict(case='native Confessor windup approach', enemy=foe(), hero=FOOT))
        for _ in range(260):
            if foe()['state'] == 6:
                break
            self.tick()
        assert foe()['state'] == 6 and foe()['facing'] == 1, 'Confessor never entered its natural tell'
        windup = self.core.save_raw_state()
        health = P.r16(self.core, self.player)
        rows = []
        for _ in range(40):
            self.tick()
            actor = foe()
            rows.append(dict(enemy=actor, hp=P.r16(self.core, self.player)))
            if actor['state'] == 8:
                break
        first = next((row for row in rows if row['hp'] != health), None)
        self.check('Confessor blade is harmless in its tell and first cuts at live age',
                   first is not None and first['enemy']['state'] == 7 and first['enemy']['timer'] == 10,
                   rows)
        assert self.core.load_raw_state(windup)
        self.w32(self.hero + 8, (foe()['x'] + 29) << 16)
        self.fixtures.append(dict(case='Confessor empty space and recovery approaches',
                                  outside=foe()['x'] + 29, inside=foe()['x'] + 20))
        for _ in range(40):
            actor = foe()
            if actor['state'] == 7 and actor['timer'] <= 2:
                break
            self.tick()
        self.check('Confessor live blade misses outside its steel', P.r16(self.core, self.player) == health
                   and foe()['state'] == 7 and foe()['timer'] <= 2, foe())
        self.w32(self.hero + 8, (foe()['x'] + 20) << 16)
        P.run(self.core, 6)
        self.check('Confessor recovery leaves an in-reach Bloom unharmed',
                   P.r16(self.core, self.player) == health and foe()['state'] == 8, foe())

    def projectile_reflections(self):
        for facing, direction in enumerate(DIRECTIONS):
            dx, dy = FORWARD[facing]
            for ahead in (True, False):
                self.reset(facing)
                delta = 23 if ahead else -23
                x, y = FOOT[0] + dx * delta, FOOT[1] - 4 + dy * delta
                W.put_actor(self.core, 1, AK_PROJ, 0, x, y, 6, flags=1,
                            dir_=(facing * 8 + 16) & 31, speed=0, damage=2, timer=1)
                self.fixtures.append(dict(case='stationary hostile seed', x=x, y=y, facing=facing, ahead=ahead))
                before = P.r16(self.core, self.player)
                records = self.attack(projectile=1)
                turned = next((row['projectile'] for row in records if row['projectile']['reflected']), None)
                self.check(f'{direction} blade turns the seed ahead only' if ahead else
                           f'{direction} blade leaves the seed behind neutral', bool(turned) == ahead
                           and (not turned or turned['direction'] == facing * 8)
                           and P.r16(self.core, self.player) == before,
                           records)

    def projectile_depth(self):
        for z, should_hurt in ((6, True), (24, False)):
            self.reset()
            W.put_actor(self.core, 1, AK_PROJ, 0, FOOT[0], FOOT[1] - 4 + z, 6,
                        flags=1, dir_=16, speed=0, damage=2, timer=1)
            self.w32(self.hero + P.ACTOR_SIZE + 16, z << 16)
            self.fixtures.append(dict(case='hostile seed at a fixed projected contact', z=z))
            before = P.r16(self.core, self.player)
            self.tick()
            after = P.r16(self.core, self.player)
            self.check(f'hostile seed at projected body contact resolves depth {z}',
                       (after < before) == should_hurt,
                       dict(before=before, after=after, seed=P.actor(self.core, 1)))

    def sword_reaches(self, facing, dx, dy):
        origins = P.sym('bloom_swing_origin')
        masks = P.sym('bloom_swing_masks')
        for phase in (2, 3, 4):
            pose = facing * 8 + phase
            ox, oy = (value if value < 128 else value - 256
                      for value in B.bytes_at(self.core, origins + pose * 2, 2))
            for y in range(max(0, dy - 11 - oy), min(31, dy - 2 - oy) + 1):
                row = P.r32(self.core, masks + pose * 128 + y * 4)
                if any(row & (1 << x) for x in range(max(0, dx - 5 - ox), min(31, dx + 4 - ox) + 1)):
                    return True
        return False

    def cream_support(self):
        self.reset()
        topology = P.sym('gCreamTopology')
        examples = {}
        for cell in range(25):
            requests = dict(sNextArea=3, sNextCell=cell, sNextSide=2, sTransPhase=0,
                            sCreamNextNode=cell * 2, sCreamNextFacing=0, sCreamDropRows=0)
            for name, value in requests.items():
                P.w8(self.core, L.ssym(name), value)
            for name in ('sCreamNextX', 'sCreamNextY'):
                P.w16(self.core, L.ssym(name), 65535)
            P.w8(self.core, P.sym('gGame'), 2)
            P.run(self.core, 80)
            C.dismiss(self.core)
            assert C.wait_play(self.core, 3)
            heights = list(B.bytes_at(self.core, topology + 7, 32 * 24))
            for key in (False, True):
                if key in examples:
                    continue
                for i, anchor in enumerate(heights):
                    if not anchor & 16 or anchor & 7 == 7:
                        continue
                    x, y = i % 32, i // 32
                    for facing, (dx, dy) in enumerate(FORWARD):
                        xx, yy = x + dx, y + dy
                        if not (1 <= xx < 31 and 1 <= yy < 23):
                            continue
                        target_height = heights[yy * 32 + xx]
                        if not target_height & 16 or target_height & 7 == 7:
                            continue
                        same = (anchor & 7) == (target_height & 7)
                        if same != key or not self.sword_reaches(facing, dx * 16, dy * 16):
                            continue
                        saved = self.core.save_raw_state()
                        B.reset_player(self.core, x * 16 + 8, y * 16 + 12, facing)
                        target = self.target(xx * 16 + 8, yy * 16 + 12)
                        report = self.attack(target)
                        self.check('Cream sword reaches a target on the same support level' if same else
                                   'Cream sword misses across different native support levels',
                                   any(row['hit'] for row in report) == same,
                                   dict(room=cell, heights=[anchor & 7, target_height & 7],
                                        actor_cells=[[x, y], [xx, yy]], facing=facing, frames=report))
                        self.fixtures.append(dict(case='ordinary Cream room-load and topology-based approach',
                                                  room=cell, same_support=same))
                        assert self.core.load_raw_state(saved)
                        examples[key] = True
                        break
                    if key in examples:
                        break
            if len(examples) == 2:
                return
        raise AssertionError('generated Cream rooms had no suitable supported melee approaches')

    def walk_and_roll(self):
        self.reset()
        P.hold(self.core, 'RIGHT', 16)
        x, y = P.player_pos(self.core)
        self.check('ordinary walk travels 20 px in 16 native updates', (x, y) == (FOOT[0] + 20, FOOT[1]))
        self.reset()
        P.hold(self.core, ['RIGHT', 'UP'], 16)
        x, y = P.player_pos(self.core)
        self.check('diagonal walking keeps comparable speed', 13 <= x - FOOT[0] <= 15 and 13 <= FOOT[1] - y <= 15,
                   dict(x=x, y=y, face=P.actor(self.core, 0)['facing']))
        self.reset(2)
        self.tick('RIGHT', 'UP')
        self.check('a fresh diagonal turns out of an incompatible old facing',
                   P.actor(self.core, 0)['facing'] in (0, 1), B.live(self.core))
        self.reset()
        P.hold(self.core, ['RIGHT', 'L'], 16)
        guarded = P.actor(self.core, 0)
        self.check('guarded walking holds facing and moves 12 px in 16 updates',
                   guarded['facing'] == 0 and guarded['x'] == FOOT[0] + 12, guarded)
        self.reset()
        self.tick('R')
        self.check('stationary R does not start a roll', P.actor(self.core, 0)['state'] == PS_NORMAL)
        self.reset(equipment=(6, 1, 5))
        self.tick('RIGHT', 'R')
        rows = []
        arrow_count = P.r8(self.core, self.player + 35)
        for i in range(45):
            actor = P.actor(self.core, 0)
            rows.append(actor)
            if actor['state'] != PS_ROLL:
                break
            if i == 6:
                self.tick('UP', 'A')
            else:
                self.tick('UP')
            if i == 8:
                self.shot('roll')
        self.check('R roll travels along committed facing through its recovery',
                   rows[0]['state'] == PS_ROLL and rows[-1]['state'] == PS_NORMAL
                   and rows[-1]['x'] == FOOT[0] + 59 and all(row['y'] == FOOT[1] for row in rows)
                   and len(rows) == 27, rows)
        self.check('ordinary bow input cannot replace a committed roll',
                   P.r8(self.core, self.player + 35) == arrow_count, rows)
        speeds = [row['speed'] for row in rows[1:]]
        expected = [768] + [512] * 15 + list(range(544, 833, 32))
        self.check('roll burst, committed travel and late speed ramp run on real updates', speeds == expected, speeds)

        self.reset()
        wall_cell = 36
        for y in range(26, 31):
            P.w8(self.core, P.sym('gRoom') + 4098 + y * 64 + wall_cell, 1)
        self.fixtures.append(dict(case='isolated practice-floor wall column', x=wall_cell * 8, subcell_rows=[26, 30]))
        self.tick('RIGHT', 'R')
        for _ in range(30):
            if P.actor(self.core, 0)['state'] != PS_ROLL:
                break
            self.tick()
        impact = P.actor(self.core, 0)
        rebound = bool(P.r8(self.core, self.hero + 29) and P.r32(self.core, self.hero + 16))
        P.run(self.core, 8)
        self.check('wall collision stops the roll and rebounds Bloom from the wall',
                   impact['state'] == PS_NORMAL and impact['coll'] & 2 and rebound
                   and P.actor(self.core, 0)['x'] < impact['x'], impact)

        self.reset()
        target = self.target(FOOT[0] + 85, FOOT[1] - 5, contact=True)
        self.tick('RIGHT', 'R')
        for _ in range(17):
            self.tick()
        assert P.actor(self.core, 0)['timer'] == 17
        location = P.player_pos(self.core)[0] + 4
        self.w32(self.hero + target * P.ACTOR_SIZE + 8, location << 16)
        self.fixtures.append(dict(case='body target moved into the live roll', x=location, timer=17))
        hp = P.r16(self.core, self.player)
        self.tick()
        self.check('early roll protection rejects a real enemy body contact',
                   P.r16(self.core, self.player) == hp and P.actor(self.core, 0)['state'] == PS_ROLL)
        self.tick()
        self.check('late roll becomes vulnerable to the same enemy body contact',
                   P.r16(self.core, self.player) < hp and P.actor(self.core, 0)['state'] == PS_HURT)

        self.reset()
        self.tick('RIGHT', 'R')
        P.run(self.core, 18)
        self.tick('B')
        self.check('late sword input waits for the normal roll recovery', P.actor(self.core, 0)['state'] == PS_ROLL)
        P.run(self.core, 8)
        self.check('late sword input comes out as the next ordinary attack', P.actor(self.core, 0)['state'] == PS_ATTACK)

    def learned_sword_actions(self):
        skills = P.sym('gLegacyInventory') + 32
        self.fixtures.append(dict(case='learned sword techniques', inventory_field='LegacyInventory.skills',
                                  roll_mask=2, spin_mask=1, fast_spin_mask=512))
        for label, learned, button, press_age, expects_damage in (
            ('learned roll requires the sword button', True, 'B', None, False),
            ('unlearned roll cannot thrust', False, 'B', 4, False),
            ('sword input before the roll window cannot thrust', True, 'B', 3, False),
            ('L-assigned sword thrusts in the learned roll window', True, 'L', 4, True),
        ):
            self.reset(1, (0, 0, 1) if button == 'L' else (0, 1, 0))
            P.w16(self.core, skills, 2 if learned else 0)
            target = self.target(FOOT[0] + 28, FOOT[1])
            start = P.actor(self.core, target)['hp']
            self.tick('RIGHT', 'R')
            hit = None
            for age in range(26):
                if age == press_age:
                    self.tick(button)
                else:
                    self.tick()
                if hit is None and P.actor(self.core, target)['hp'] < start:
                    hit = dict(age=age, state=P.actor(self.core, 0)['state'])
            self.check(label, hit == (dict(age=4, state=PS_ROLL) if expects_damage else None), hit)

        for skill_mask, threshold in ((1, 80), (513, 40)):
            for charge in (threshold - 1, threshold):
                self.reset(1)
                P.w16(self.core, skills, skill_mask)
                target = self.target(FOOT[0] - 22, FOOT[1])
                start = P.actor(self.core, target)['hp']
                self.tick('B')
                for _ in range(40):
                    if P.actor(self.core, 0)['state'] != PS_ATTACK:
                        break
                    self.tick('B')
                else:
                    raise AssertionError('ordinary cut did not complete before the spin charge')
                P.hold(self.core, 'B', charge - 1)
                before = P.actor(self.core, target)['hp']
                P.run(self.core, 6)
                after = P.actor(self.core, target)['hp']
                self.check(f'{charge} updates toward the {threshold}-update spin threshold',
                           before == start and (after < before) == (charge == threshold),
                           dict(start=start, before_release=before, after_release=after))

    def run(self):
        self.sword()
        self.body_contacts()
        self.confessor()
        self.projectile_reflections()
        self.projectile_depth()
        self.walk_and_roll()
        self.learned_sword_actions()
        self.cream_support()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seed', type=lambda value: int(value, 0), default=0xb4a7)
    args = parser.parse_args()
    review = Review(args.bundle.resolve(), args.out.resolve(), args.seed)
    error = None
    try:
        review.run()
    except Exception as exc:
        error = repr(exc)
        raise
    finally:
        passed = sum(row['passed'] for row in review.checks)
        report = dict(method=__doc__, emulator='mGBA 0.10.5', seed=args.seed,
                      source_commit=(review.bundle/'source-commit.txt').read_text().strip(),
                      rom_sha256=sha(review.bundle/'bartgame.gba'), tool_sha256=sha(Path(__file__)),
                      checks=review.checks, passed=passed, outputs=review.media, fixtures=review.fixtures,
                      complete=error is None and passed == len(review.checks), error=error)
        (review.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        print(f'RESULT {passed}/{len(review.checks)}', flush=True)
    return int(not report['complete'])


if __name__ == '__main__':
    raise SystemExit(main())
