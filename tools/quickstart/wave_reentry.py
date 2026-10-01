"""Does leaving a 3-wave ? room and coming back advance the gauntlet?

The user's report (Oct 2026): "the player can just walk out of the room and
walk back in a few times and eventually the reward will drop without them
having to actually beat the challenge." Reproduced exactly before the fix -
wave 0, 1, 2, reward on the third re-entry, no kills - and the regression
test for it since.

Mechanism: the seam-gauntlet record (GF_SEAM_GAUNTLET_*, FLAG_BANK_11)
outlives the room on purpose, and a door exit deleted the wave, so the next
visit read a live record with no enemies as a cleared wave.
QuickStartSetupWaveRoomContent now reconciles once per visit: a record (or a
survive clock) with none of our enemies alive is a fight that was walked out
on, and is forgotten.

The exit is a warp to Castle Garden rather than a walk to the door - both
run the same area-change path (sub_08051DCC, RecycleEntities), and the
measurement before the fix matched the report through the warp.

    python3 tools/quickstart/wave_reentry.py [--rom tmc.gba]

PASS: four re-entries, the record's wave stays 0 and no ground item appears.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import (boot, warp, here, poison_here, entities, room_dims, KIND_ENEMY, KIND_OBJECT,
                 GROUND_ITEM_ID, SAVE_FLAGS)
import parse_tables as P
import callrom as C

SCRATCH = 0x0203F100
FLAG_BANK_11 = 0x9C0
SEAM_LIVE, SEAM_AREA, SEAM_ROOM, SEAM_WAVE, SEAM_SPAWNED = 43, 44, 51, 56, 58


def bank11(c, bit):
    b = FLAG_BANK_11 + bit
    return (c.memory.u8[SAVE_FLAGS + (b >> 3)] >> (b & 7)) & 1


def record(c):
    return dict(live=bank11(c, SEAM_LIVE), spawned=bank11(c, SEAM_SPAWNED),
                wave=bank11(c, SEAM_WAVE) | bank11(c, SEAM_WAVE + 1) << 1,
                area=sum(bank11(c, SEAM_AREA + b) << b for b in range(7)),
                room=sum(bank11(c, SEAM_ROOM + b) << b for b in range(5)))


def waves_kind():
    src = open(os.path.join(P.ROOT, 'src/game.c')).read()
    m = re.search(r'enum \{\s*QS_EVENT_ITEM_DROP[^}]*\}', src, re.S)
    kinds = list(dict.fromkeys(re.findall(r'(QS_EVENT_\w+)', m.group(0))))
    return kinds.index('QS_EVENT_WAVES')


def main():
    rom = os.path.join(P.ROOT, 'tmc.gba')
    if '--rom' in sys.argv:
        rom = sys.argv[sys.argv.index('--rom') + 1]
    WAVES = waves_kind()
    roll = C.game_sym('QuickStartContentSiteRoll')
    sites = P.content_sites_full()
    c = boot(rom)
    first = None
    for i, row in enumerate(sites):
        C.call_keep(c, roll, (i, SCRATCH, SCRATCH + 1))
        if c.memory.u8[SCRATCH] == WAVES:
            first = (i, row)
            break
    del c
    if first is None:
        print('no WAVES site in this run')
        return 2
    i, row = first
    a, r, cx, cy = row[2], row[3], row[4], row[5]
    print('WAVES site %d: %s / %s' % (i, row[0], row[1]))

    def enter(c):
        warp(c, a, r, cx, cy, frames=60)
        W, H = room_dims(c)
        px = 24 if cx > 80 else max(W - 24, cx + 80)
        py = 24 if cy > 80 else max(H - 24, cy + 80)
        warp(c, a, r, px, py, frames=400)

    def state(c, label):
        en = len(entities(c, KIND_ENEMY))
        it = len(entities(c, KIND_OBJECT, GROUND_ITEM_ID))
        rec = record(c)
        print('  %-22s here=%s enemies=%d ground_items=%d record=%s' % (label, here(c), en, it, rec))
        return rec, it

    c = boot(rom)
    poison_here(c)
    enter(c)
    state(c, 'first entry')
    bad = False
    for cyc in range(4):
        poison_here(c)
        warp(c, 7, 0, 504, 480, frames=200)
        poison_here(c)
        enter(c)
        rec, items = state(c, 're-entry %d' % (cyc + 1))
        if here(c) != (a, r):
            print('  never landed back in the room; inconclusive')
            return 2
        if rec['wave'] != 0 or items != 0:
            bad = True
    print('FAIL: a re-entry advanced the gauntlet or dropped the reward' if bad else 'PASS')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
