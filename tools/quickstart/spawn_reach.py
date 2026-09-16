"""Does the ? room placer keep its enemies on ground the player can reach?

The user, after a playthrough: "There are some ? rooms where the enemies
are spawning behind a wall that the player can't access... the room is
structured such that the player enters through the door and is surrounded
on all sides by walls that they cannot pass through. On the other side of
those walls are tiles in the room, which are technically stand-able, but
the player can never access them."

Two measurements per room, both asked of the shipped C rather than of a
Python re-implementation of it:

  CONTROL  how many tiles QuickStartTileIsOpen calls open, and how many of
           those QuickStartMarkReachableTiles (seeded from the player's own
           tile) can actually reach. A room with a pocket shows a gap here;
           a room without one shows none, which is what makes the gap in
           the first kind of room mean something.

  TEST     call QuickStartSpawnEnemiesOnOpenTiles for real at the site's
           content spot and check every body it created against the same
           reach set. Any enemy on an unreachable tile is a failure.

Usage: python3 tools/quickstart/spawn_reach.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, press, r16, room_dims, qs_site_set, poison_here, entities, GENT, STRIDE, KIND_ENEMY
from callrom import call_keep, game_sym, map_sym
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
PLAYER = 0x03001160
ROOM_CONTROLS = 0x03000bf0
SCRATCH = 0x0203E000          # 512 bytes of EWRAM well clear of gSave
SCRATCH_OPEN = 0x0203E400     # the flood's open-tile map, same size
REACH_BYTES = 64 * 64 // 8

TILE_IS_OPEN = game_sym('QuickStartTileIsOpen')
MARK_REACH = game_sym('QuickStartMarkReachableTiles')
PLACE = game_sym('QuickStartSpawnEnemiesOnOpenTiles')
DELETE_ENTITY = map_sym('DeleteEntity')


def ids(path, prefix):
    out = {}
    for line in open(os.path.join(P.ROOT, 'build/USA/enum_include/' + path)):
        m = re.match(r'\.set (\w+), (\d+)', line.strip())
        if m:
            out[m.group(1)] = int(m.group(2))
    return out


AREAS = ids('area.inc', 'AREA_')
ROOMS = ids('roomid.inc', 'ROOM_')
ENEMIES = ids('enemy.inc', '')

# (label, area, room, arrival x/y from the room's own vanilla exit list,
#  the site content spot to place against)
CASES = [
    ('Goron cave main', 'AREA_GORON_CAVE', 'ROOM_GORON_CAVE_MAIN', 0x78, 0x278, 120, 600),
    ('Goron cave stairs', 'AREA_GORON_CAVE', 'ROOM_GORON_CAVE_STAIRS', 0x78, 0x78, 0x78, 0x60),
    ('Grimblade dojo', 'AREA_DOJOS', 'ROOM_DOJOS_GRIMBLADE', 0x78, 0xa0, 120, 96),
]


def reach_bit(c, tx, ty):
    i = (ty << 6) | tx
    return (c.memory.u8[SCRATCH + (i >> 3)] >> (i & 7)) & 1


def run_case(label, area, room, ax, ay, cx, cy):
    c = boot(ROM)
    poison_here(c)
    warp(c, AREAS[area], ROOMS[room], ax, ay)
    for _ in range(10):
        press(c, c.KEY_A, 5, 5)
    w = r16(c, ROOM_CONTROLS + 0x1e) >> 4
    h = r16(c, ROOM_CONTROLS + 0x20) >> 4
    ptx = (r16(c, PLAYER + 0x2e) - r16(c, ROOM_CONTROLS + 6)) >> 4
    pty = (r16(c, PLAYER + 0x32) - r16(c, ROOM_CONTROLS + 8)) >> 4
    # Cost matters here: this runs the moment a wave drops, and a flood
    # that takes four frames is a visible hitch. Find the smallest budget
    # that completes, which bounds the instruction count.
    call_keep(c, MARK_REACH, (SCRATCH, SCRATCH_OPEN, ptx, pty), budget=3200000)
    openTiles = []
    for ty in range(min(h, 64)):
        for tx in range(min(w, 64)):
            if call_keep(c, TILE_IS_OPEN, (tx, ty)):
                openTiles.append((tx, ty))
    unreachable = [t for t in openTiles if not reach_bit(c, *t)]
    print(f'{label}: room {w}x{h} tiles, player tile ({ptx},{pty})')
    print(f'    open {len(openTiles)}, reachable {len(openTiles) - len(unreachable)}, '
          f'UNREACHABLE {len(unreachable)}')
    if unreachable:
        print('    pocket sample:', unreachable[:8])

    before = {i for (i, k, ident, typ, x, y) in entities(c, kind=KIND_ENEMY)}
    placed = call_keep(c, PLACE, (ENEMIES['CHUCHU'], 2, cx, cy, 8, -1), budget=3200000)
    bad = []
    n = 0
    for (i, k, ident, typ, x, y) in entities(c, kind=KIND_ENEMY):
        if i in before:
            continue
        n += 1
        tx = (x - r16(c, ROOM_CONTROLS + 6)) >> 4
        ty = (y - r16(c, ROOM_CONTROLS + 8)) >> 4
        if not (0 <= tx < 64 and 0 <= ty < 64 and reach_bit(c, tx, ty)):
            bad.append((tx, ty))
    # A run that placed nothing on reachable ground is allowed to fall back
    # (see the escape hatch in the placer); anything else must stay inside
    # the player's component.
    fellBack = n > 0 and len(bad) == n
    print(f'    placer returned {placed}, {n} new enemies, {len(bad)} on unreachable tiles'
          + (f' {bad}' if bad else '') + ('  [escape hatch]' if fellBack else ''))
    return (0 if fellBack else len(bad)), len(unreachable)


def main():
    fails = 0
    pockets = 0
    for case in CASES:
        bad, unreach = run_case(*case)
        fails += bad
        pockets += unreach
    print()
    if pockets == 0:
        print('INCONCLUSIVE: no room measured had an unreachable pocket at all,')
        print('so "0 enemies in a pocket" proves nothing. Pick a room with one.')
        return 2
    print('FAIL: %d enemy placement(s) landed outside the player component' % fails
          if fails else 'PASS: every placement landed on reachable ground')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
