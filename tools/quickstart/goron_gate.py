"""Lon Lon Ranch's Goron cave mouth, before and after KINSTONE_29.

Vanilla's sub_StateChange_HyruleField_LonLonRanch paints two blocking tiles
over the cave mouth AND spawns the wall-punching Goron in front of them,
both only while KINSTONE_29 is unfused. They are one gate. We were deleting
the Goron but not the tiles, so the barrier stayed with nothing standing in
front of it.

Checks, on a fresh run and then with the fusion done:
  1. the two gate tiles at (8,54) and (8,55),
  2. whether the Goron NPC is present,
  3. whether Link can actually walk from the ranch into the cave.
"""
import sys
sys.path.insert(0, 'tools/quickstart')
from emu import (boot, warp, here, snap, entities, coll_at,
                 ROOM_CONTROLS, PLAYER, r16, w16)

FUSED = 0x02002a40 + 0x114 + 301
KINSTONE_29 = 0x29
RANCH = (3, 5)
STAIRS = (47, 0)
GORON_NPC = None  # resolved below from object/npc ids

import re
for line in open('build/USA/enum_include/npc.inc'):
    m = re.match(r'\.set GORON, (\d+)', line.strip())
    if m:
        GORON_NPC = int(m.group(1))
print('GORON npc id =', GORON_NPC)

# The gate tiles, straight out of roomInit.c.
GATE_TILES = [(8, 54), (8, 55)]


def stage(fuse):
    c = boot('tmc.gba')
    if fuse:
        c.memory.u8[FUSED + (KINSTONE_29 >> 3)] |= 1 << (KINSTONE_29 & 7)
    # Arrive south of the cave mouth, on open ground.
    warp(c, RANCH[0], RANCH[1], 136, 920, frames=360)
    return c


def hold(c, k, n, until):
    for _ in range(n):
        c.set_keys(k)
        c.run_frame()
        if here(c) != until:
            break
    c.clear_keys(k)


fails = []
for fuse in (False, True):
    label = 'AFTER  KINSTONE_29' if fuse else 'BEFORE KINSTONE_29'
    c = stage(fuse)
    if here(c) != RANCH:
        fails.append(f'{label}: could not stage Lon Lon Ranch ({here(c)})')
        continue
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    tiles = [coll_at(c, tx, ty) for tx, ty in GATE_TILES]
    gorons = [(e[4] - ox, e[5] - oy) for e in entities(c)
              if e[1] == 7 and e[2] == GORON_NPC]
    # Walk north into the cave mouth.
    w16(c, PLAYER + 0x2e, ox + 136)
    w16(c, PLAYER + 0x32, oy + 920)
    for _ in range(30):
        c.run_frame()
    hold(c, c.KEY_UP, 260, RANCH)
    got = here(c)
    px = r16(c, PLAYER + 0x2e) - ox
    py = r16(c, PLAYER + 0x32) - oy
    print(f'{label}:')
    print(f'   gate tiles (8,54)/(8,55) = ' + '/'.join(f'0x{t:02x}' for t in tiles))
    print(f'   Goron NPC present: {bool(gorons)} {gorons}')
    print(f'   walked north -> {got}, ended at ({px},{py})')
    snap(c, f'/tmp/claude-0/-home-user-bartgame/650f03f8-c7a6-58cd-957d-b2eef0cb4e82/'
            f'scratchpad/gate_{"after" if fuse else "before"}.png')
    if not fuse:
        if all(t == 0 for t in tiles):
            fails.append('before the fusion the gate tiles are already open')
        if not gorons:
            fails.append('before the fusion the wall-punching Goron is missing - '
                         'the barrier would have no visible cause')
        if got == STAIRS:
            fails.append('the cave opened without the fusion')
    else:
        if any(t != 0 for t in tiles):
            fails.append(f'after the fusion the gate tiles are still solid ({tiles})')
        if gorons:
            fails.append('after the fusion the Goron is still standing there')
        if got != STAIRS:
            fails.append(f'after the fusion Link still could not walk in (ended {got})')

print()
for f in fails:
    print('FAIL:', f)
print('RESULT:', 'PASS' if not fails else 'FAIL')
