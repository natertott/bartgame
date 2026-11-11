#!/usr/bin/env python3
"""Native mGBA counterprobes for cross-system damage and modal boundaries.

Fixtures supply only player health, ownership, equipment, bottle contents,
Nayru ownership and navigation/facing. Real tap/release bombs supply damage;
real Sage interaction supplies the dialogue. No enemy HP/state, completion,
terrain, VRAM or framebuffer is changed. This is an isolated private SRAM core.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import probe as P

SHA = lambda b: hashlib.sha256(b).hexdigest()


def w32(c, address, value):
    P.w16(c, address, value & 65535)
    P.w16(c, address + 2, value >> 16)


class Review:
    def __init__(self, bundle, out):
        self.bundle = Path(bundle).resolve()
        self.out = Path(out).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        P.MAP = str(self.bundle / 'bartgame.map')
        P.ROM = str(self.bundle / 'bartgame.gba')
        P._syms = None
        self.rows = []

    def check(self, name, ok, observed):
        self.rows.append(dict(name=name, passed=bool(ok), observed=observed))
        print(('PASS ' if ok else 'FAIL ') + name, observed, flush=True)

    def fresh(self):
        return P.boot(rom=P.ROM)

    def fairy_mitigation(self):
        # PlayerState and the separate LegacyInventory remain layout-stable.
        # bottle[0] is42; HandoffState's first food word starts16 and charms20.
        for name, charm, initial_hp, expected_hp, expected_fairy in (
            ('unmitigated lethal damage invokes Fairy', 0, 4, 24, 0),
            ('Nayru nonlethal damage preserves Fairy', 1, 4, 3, 0x28),
            ('Nayru lethal remainder still invokes Fairy', 1, 1, 24, 0),
        ):
            c = self.fresh()
            pl, inv, hs = (P.sym(n) for n in ('gPl', 'gLegacyInventory', 'gHandoffState'))
            P.w16(c, pl, initial_hp)
            P.w8(c, pl + 8, P.r8(c, pl + 8) | 2)
            P.w8(c, pl + 7, 4)
            P.w8(c, pl + 9, 2)
            P.w8(c, inv + 42, 0x28)
            P.w8(c, hs + 20, charm)
            P.press(c, 'A', 2, 40)
            hp, fairy = P.r16(c, pl), P.r8(c, inv + 42)
            self.check(name, hp == expected_hp and fairy == expected_fairy,
                       dict(hp=hp, fairy=fairy, expected_hp=expected_hp,
                            expected_fairy=expected_fairy))
            P.snap(c, str(self.out / ('fairy-' + str(charm) + '-' + str(initial_hp) + '.png')))

    def dialogue_cancels_charge(self):
        c = self.fresh()
        base, pl = P.sym('gActors'), P.sym('gPl')
        sage = next(P.actor(c, i) for i in range(1, 96)
                    if P.r8(c, base + i * 64) == 5 and P.r8(c, base + i * 64 + 1) == 0)
        w32(c, base + 8, sage['x'] << 16)
        w32(c, base + 12, (sage['y'] + 22) << 16)
        P.w8(c, base + 7, 0)
        P.w8(c, base + 6, 0)
        P.w8(c, pl + 8, P.r8(c, pl + 8) | 2)
        P.w8(c, pl + 7, 4)
        P.w8(c, pl + 9, 0)
        P.w8(c, pl + 10, 2)
        P.run(c, 3)
        c.set_keys(c.KEY_B)
        P.run(c, 10)
        charged = P.r8(c, P.sym('gBombChargeTicks'))
        c.set_keys(c.KEY_B, c.KEY_A)
        P.run(c, 2)
        c.set_keys()
        P.run(c, 20)
        modal_charge = P.r8(c, P.sym('gBombChargeTicks'))
        modal = P.r8(c, P.sym('gTbActive'))
        P.snap(c, str(self.out / 'dialogue-interrupt.png'))
        for _ in range(15):
            P.press(c, 'A', 2, 25)
            if not P.r8(c, P.sym('gTbActive')):
                break
        P.run(c, 40)
        ammo = P.r8(c, pl + 7)
        self.check('real dialogue interrupts charge without a latent throw',
                   charged > 0 and modal and modal_charge == 0 and ammo == 4,
                   dict(charged=charged, dialogue_charge=modal_charge,
                        dialogue_open=modal, ammunition=ammo))
        P.snap(c, str(self.out / 'dialogue-return.png'))

    def health_overflow(self):
        c = self.fresh()
        pl = P.sym('gPl')
        P.w16(c, pl + 2, 160)
        P.w16(c, pl, 160)
        P.run(c, 4)
        # The left82px excludes the purse. The native20px height is already
        # occupied by selected item pods; both heart rows fit there.
        box = (0, 2, 82, 20)
        full = c.bg_video.to_pil().convert('RGB').crop(box).tobytes()
        P.snap(c, str(self.out / 'health-160.png'))
        P.w16(c, pl, 120)
        P.run(c, 4)
        reduced = c.bg_video.to_pil().convert('RGB').crop(box).tobytes()
        P.snap(c, str(self.out / 'health-120.png'))
        P.run(c, 4)
        steady = c.bg_video.to_pil().convert('RGB').crop(box).tobytes()
        self.check('health above ten hearts remains visible', full != reduced,
                   dict(native_crop=box, hp_max=160, first_hp=160, second_hp=120,
                        changed=full != reduced))
        self.check('unchanged health crop is stable positive control', reduced == steady,
                   dict(native_crop=box, identical=reduced == steady))

    def health_above_twenty(self):
        c = self.fresh()
        pl = P.sym('gPl')
        P.w16(c, pl + 2, 168)
        P.w16(c, pl, 168)
        P.run(c, 4)
        box = (84, 12, 146, 20)
        full = c.bg_video.to_pil().convert('RGB').crop(box).tobytes()
        P.snap(c, str(self.out / 'health-168.png'))
        P.w16(c, pl, 164)
        P.run(c, 4)
        reduced = c.bg_video.to_pil().convert('RGB').crop(box).tobytes()
        P.snap(c, str(self.out / 'health-164.png'))
        P.run(c, 4)
        steady = c.bg_video.to_pil().convert('RGB').crop(box).tobytes()
        self.check('health beyond twenty hearts has exact visible feedback',
                   full != reduced,
                   dict(native_crop=box, hp_max=168, first_hp=168, second_hp=164,
                        changed=full != reduced))
        self.check('unchanged exact-health panel is stable positive control',
                   reduced == steady, dict(native_crop=box, identical=reduced == steady))

    def run(self):
        self.fairy_mitigation()
        self.dialogue_cancels_charge()
        self.health_overflow()
        self.health_above_twenty()
        report = dict(method=__doc__, rom_sha256=SHA(Path(P.ROM).read_bytes()),
                      tool_sha256=SHA(Path(__file__).read_bytes()),
                      checks=self.rows, passed=sum(r['passed'] for r in self.rows),
                      total=len(self.rows))
        (self.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        return report['passed'] != report['total']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    return Review(args.bundle, args.out).run()


if __name__ == '__main__':
    sys.exit(main())
