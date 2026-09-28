"""The Ezlo-hint door loop: does a room-entry hint still fire on a doorstep?

The user's report is a hard softlock, not an annoyance: walk out of the
Trilby Highlands tree, the "Something sleeps here" line plays the instant the
field loads, the door pulls the player straight back inside because they are
still standing on it, and it happens again, and again. Vanilla's "stand too
close and the door takes you" is fine alone; a hint that freezes the player
on that exact tile is what closes the loop.

The fix is QuickStartPlayerOnExitTrigger in game.c: no room-entry hint while
the player is on one of the room's own exits, and the latch is not set
either, so the line is postponed rather than lost.

TWO THINGS THIS PROBE HAD TO LEARN THE HARD WAY, both of which made an
earlier version report a working fix as broken:

  * emu.warp() runs 300 frames of its own. Warping to the reward spot and
    THEN moving the player to the door lets the hint fire during those 300
    frames, before the test has begun. The player has to arrive on the door.
  * the player has to be PINNED there. Left alone the engine takes them
    through the door, they come back out somewhere else, and the hint fires
    there - correctly - so the latch reads set either way.

    python3 tools/quickstart/door_hint_loop.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, here, r16, poison_here, SAVE_FLAGS, QS_BIT0
import parse_tables as P
import exit_lists as X

ROM = os.path.join(P.ROOT, 'tmc.gba')
PLAYER = 0x03001160
RC = 0x03000bf0
GF_REGION_INTRO_HINT_SHOWN = 207


def w16(c, a, v):
    c.memory.u8[a] = v & 0xFF
    c.memory.u8[a + 1] = (v >> 8) & 0xFF


def latch(c, n=GF_REGION_INTRO_HINT_SHOWN):
    b = QS_BIT0 + n
    return (c.memory.u8[SAVE_FLAGS + (b >> 3)] >> (b & 7)) & 1


def stand(region, x, y, frames=600):
    """Arrive at (x, y) and be held there. Returns (latch, room)."""
    c = boot(ROM)
    poison_here(c)
    warp(c, region['area'], region['room'], x, y)
    ox, oy = r16(c, RC + 6), r16(c, RC + 8)
    for _ in range(frames):
        w16(c, PLAYER + 0x2e, ox + x)
        w16(c, PLAYER + 0x32, oy + y)
        c.run_frame()
    out = (latch(c), here(c))
    del c
    return out


def doors(room_name):
    return [(sx, sy) for w, sx, sy, ex, ey, sh, da, dr in X.BY_ROOM.get(room_name, [])
            if w == 'WARP_TYPE_AREA']


def main():
    fails = []

    def check(ok, msg):
        print(('  ok   ' if ok else '  FAIL ') + msg)
        if not ok:
            fails.append(msg)

    # Castle Garden is skipped: it is the hub, where the item-selection phase
    # runs, so anything that happens there is probably not a room-entry hint.
    host = None
    for region in P.region_pool():
        if region['roomName'] == 'ROOM_CASTLE_GARDEN_MAIN' or not doors(region['roomName']):
            continue
        got, room = stand(region, *region['reward'])
        print('   %-42s in the open: latch=%d' % (region['roomName'], got))
        if got:
            host = region
            break
    check(host is not None, 'CONTROL: some region opens a room-entry hint at all')
    if host is None:
        print('\nThe control never fired, so nothing below would mean anything.')
        return 1

    dx, dy = doors(host['roomName'])[0]
    on, room = stand(host, dx, dy)
    print('   %-42s pinned on its door (%d,%d): latch=%d'
          % (host['roomName'], dx, dy, on))
    check(on == 0, 'pinned on a door, the room-entry hint does not fire')

    print()
    print('PASS' if not fails else 'FAILED: %d' % len(fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
