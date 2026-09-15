"""Reachable interior of the Trilby dig cave, from where the player lands.

AREA_DIG_CAVES shares one 480x960 map across four rooms, so a raw
collision dump spans rooms the player cannot reach. Flooding from the
arrival tile bounds the survey to the room actually being visited.
"""
import sys
sys.path.insert(0, '/home/user/bartgame/tools/quickstart')
from emu import warp, here, coll_at, room_dims, snap, w16, ROOM_CONTROLS as RC
from seed import boot_pinned
import parse_tables as P
HEALTH = 0x02002a40 + 0xA8 + 2
PLAYER = 0x03001160
OUT = '/tmp/claude-0/-home-user-bartgame/650f03f8-c7a6-58cd-957d-b2eef0cb4e82/scratchpad'
DIG = P.AREAS['AREA_DIG_CAVES']
ROOM = 3                              # ROOM_DIG_CAVES_TRILBY_HIGHLANDS
ARRIVE = (0x88, 0x68)                 # transitions.c, Trilby -> dig cave

c = boot_pinned('/home/user/bartgame/tmc.gba', 0x42)
warp(c, DIG, ROOM, ARRIVE[0], ARRIVE[1])
for _ in range(300):
    c.memory.u8[HEALTH] = 0x20
    c.run_frame()
print('landed at', here(c))
W, H = room_dims(c)
tw, th = W >> 4, H >> 4
ox = c.memory.u8[RC + 6] | (c.memory.u8[RC + 7] << 8)
oy = c.memory.u8[RC + 8] | (c.memory.u8[RC + 9] << 8)
px = c.memory.u8[PLAYER + 0x2e] | (c.memory.u8[PLAYER + 0x2f] << 8)
py = c.memory.u8[PLAYER + 0x32] | (c.memory.u8[PLAYER + 0x33] << 8)
start = ((px - ox) >> 4, (py - oy) >> 4)
print(f'room {W}x{H} ({tw}x{th}), origin ({ox},{oy}), player tile {start}')

open_t = lambda t: (0 <= t[0] < tw and 0 <= t[1] < th and coll_at(c, t[0], t[1]) == 0)
seen, stack = set(), [start]
while stack:
    t = stack.pop()
    if t in seen or not open_t(t):
        continue
    seen.add(t)
    stack += [(t[0]+1, t[1]), (t[0]-1, t[1]), (t[0], t[1]+1), (t[0], t[1]-1)]
print(f'reachable interior: {len(seen)} tiles')
if seen:
    xs = [t[0] for t in seen]; ys = [t[1] for t in seen]
    print(f'extent: tx {min(xs)}-{max(xs)}, ty {min(ys)}-{max(ys)}')
    for ty in range(min(ys) - 1, max(ys) + 2):
        print('   ' + ''.join('O' if (tx, ty) in seen else
                              ('.' if open_t((tx, ty)) else '#')
                              for tx in range(max(0, min(xs) - 1), min(tw, max(xs) + 2))))
    roomy = [t for t in seen
             if all((t[0]+dx, t[1]+dy) in seen for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
    print(f'{len(roomy)} tiles with full 3x3 elbow room')
    if roomy:
        far = max(roomy, key=lambda t: abs(t[0]-start[0]) + abs(t[1]-start[1]))
        print(f'furthest roomy tile from arrival: {far} -> content spot '
              f'({far[0]*16+8}, {far[1]*16+8})')
snap(c, f'{OUT}/digcave_trilby.png')
