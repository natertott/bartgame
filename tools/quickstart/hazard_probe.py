"""What each roster enemy does TO the player, for the hazard pool.

The torch and cleanup ? rooms (docs/QUICKSTART_LANTERN_GUST_EVENTS.md) want
enemies that slow the player, put a status on them (fire, ice, electricity),
or come after them. The roster's QS_T_FIRE / QS_T_ICE are colour themes, not
effects, so this measures the effect instead: every roster row, three of it
raw-spawned around a player standing still in the quiet Grimblade dojo (the
roster_soak setup), 600 frames, recording

  status   gPlayerState.flags seen: CAPTURED, BURNING, FROZEN, DRUGGED,
           MOLDWORM_CAPTURED; the PLAYER_FROZEN action; and HELD, a nonzero
           gPlayerState.mobility (set by a shock, sub_08017D28, and by a
           Beetle clinging on)
  slow     the lowest gPlayerState.speed_modifier (negative is slower)
  hits     how many times the player's health fell, and the hit types the
           player's contactFlags reported (the sender's hitType)

Health is topped up below a third so nothing dies. The player stands still,
or with --swing presses B and A in turn every 30 frames (a charged ChuChu
shocks only the sword that strikes it).

    python3 tools/quickstart/hazard_probe.py [--rom tmc-d3.gba] [--rows A-B] [--only NAME:form,...] [--frames 600] [--swing] [--json OUT]
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, press, poison_here, r16, w16, qs_site_set, entities, GENT, STRIDE, KIND_ENEMY, PLAYER
from callrom import call_keep, map_sym
import parse_tables as P
from roster_soak import roster_rows

args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else os.path.join(P.ROOT, 'tmc-d3.gba')
PSTATE = 0x03003f80
FLAGS = {0x10: 'CAPTURED', 0x400: 'BURNING', 0x800: 'FROZEN', 0x4000: 'DRUGGED', 0x80000: 'MOLDWORM_CAPTURED'}
PLAYER_FROZEN = 13
MAXHEALTH = 0x02002a40 + 0xAB   # gSave.stats.maxHealth
CREATE_ENEMY = map_sym('CreateEnemy')
UPDATE_SPRITE = map_sym('UpdateSpriteForCollisionLayer')
ENEMY_IDS = {}
for line in open(os.path.join(P.ROOT, 'build/USA/enum_include/enemy.inc')):
    m = re.match(r'\.set (\w+), (\d+)', line.strip())
    if m:
        ENEMY_IDS[m.group(1)] = int(m.group(2))


def u32(c, a):
    return c.memory.u8[a] | (c.memory.u8[a + 1] << 8) | (c.memory.u8[a + 2] << 16) | (c.memory.u8[a + 3] << 24)


def measure(level, name, form, frames=600):
    c = boot(ROM)
    qs_site_set(c, 16, 1)      # the dojo's own site done: nothing else spawns
    poison_here(c)
    warp(c, 37, 5, 0x78, 0xa0)
    for _ in range(10):
        press(c, c.KEY_A, 5, 5)
    ox, oy = r16(c, 0x03000bf0 + 6), r16(c, 0x03000bf0 + 8)
    w16(c, PLAYER + 0x2e, ox + 120); w16(c, PLAYER + 0x32, oy + 100)
    for dx, dy in ((-40, -24), (40, -24), (0, -48)):
        e = call_keep(c, CREATE_ENEMY, (ENEMY_IDS[name], form))
        if e:
            w16(c, e + 0x2e, ox + 120 + dx); w16(c, e + 0x32, oy + 100 + dy)
            c.memory.u8[e + 0x38] = 1
            call_keep(c, UPDATE_SPRITE, (e,))
    full = c.memory.u8[MAXHEALTH]
    seen, frozen_action, shocked, slowest, hits, hit_types = 0, False, False, 0, 0, set()
    last = c.memory.u8[PLAYER + 0x45]
    for f in range(frames):
        if c.memory.u8[0x02000050]:
            press(c, c.KEY_A, 2, 2)
        if '--swing' in args and f % 30 == 0:
            press(c, c.KEY_B if f % 60 else c.KEY_A, 2, 2)
        c.run_frame()
        shocked |= c.memory.u8[PSTATE + 0x1a] != 0
        flags = u32(c, PSTATE + 0x30)
        for bit in FLAGS:
            if flags & bit:
                seen |= bit
        frozen_action |= c.memory.u8[PLAYER + 0x0c] == PLAYER_FROZEN
        slowest = min(slowest, r16(c, PSTATE + 0x80))   # emu.r16 is signed
        h = c.memory.u8[PLAYER + 0x45]
        if h < last:
            hits += 1
            ct = c.memory.u8[PLAYER + 0x41]
            if ct & 0x80:
                hit_types.add(ct & 0x7f)
        if h < full // 3:
            c.memory.u8[PLAYER + 0x45] = full
            h = full
        last = h
    alive = len(entities(c, KIND_ENEMY, ENEMY_IDS[name]))
    del c
    return dict(level=level, name=name, form=form, status=[FLAGS[b] for b in FLAGS if seen & b] + (['FROZEN_ACTION'] if frozen_action else []) + (['HELD'] if shocked else []),
                slow=slowest, hits=hits, hit_types=sorted(hit_types), alive=alive)


def main():
    rows = roster_rows()
    frames = int(args[args.index('--frames') + 1]) if '--frames' in args else 600
    if '--only' in args:
        # NAME:form,... measured whether or not the roster holds them
        rows = [('extra', n.split(':')[0], int(n.split(':')[1])) for n in args[args.index('--only') + 1].split(',')]
    lo, hi = 0, len(rows) - 1
    if '--rows' in args:
        lo, hi = [int(x) for x in args[args.index('--rows') + 1].split('-')]
    out = []
    for i in range(lo, min(hi, len(rows) - 1) + 1):
        level, name, form = rows[i]
        r = measure(level, name, form, frames)
        r['row'] = i
        out.append(r)
        print('%3d %-18s %-18s f%d  status %-28s slow %5d  hits %2d types %-12s alive %d' % (
            i, level.replace('sQuickStart', ''), name, form, ','.join(r['status']) or '-', r['slow'], r['hits'],
            ','.join('%#x' % t for t in r['hit_types']) or '-', r['alive']), flush=True)
    if '--json' in args:
        json.dump(out, open(args[args.index('--json') + 1], 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
