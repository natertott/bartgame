"""Select with nothing to fuse: does Ezlo name the next step, and only then?

The user, after a playthrough: pressing Select next to a fusion sprite must
keep opening the Kinstone screen, but pressing it with nobody there should
play a hint naming "what region and type of event they need to unlock
next".

Two halves, and the second is what makes the first mean anything:

  TEST     press Select in an empty room and read gRoomTransition.hint_idx.
           Three chain states, three predictable answers - nothing rolled,
           everything finished, and a live WAVE step whose line has to come
           out of the paired bank with the WAVE remainder.

  CONTROL  press Select with gPossibleInteraction dressed as "standing next
           to a fuser" - a current index, a real object, a kinstone id in
           range. The hint must NOT fire; that press belongs to the fusion
           screen. Without this the test only proves that Select does
           something, not that it does the right thing at the right time.

Usage: python3 tools/quickstart/select_hint.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, press, poison_here
from callrom import call_keep, game_sym
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
SAVE = 0x02002a40
CHAIN_KIND = SAVE + 0x026
CHAIN_WHERE = SAVE + 0x02B
CHAIN_PROGRESS = SAVE + 0x035
CHAIN_ROLLED = SAVE + 0x036
CHAIN_HINTED = SAVE + 0x037
ROOM_TRANSITION = 0x030010A0
HINT_IDX = ROOM_TRANSITION + 0x36
PI = 0x03003df0               # gPossibleInteraction
PI_CURRENT_INDEX = PI + 3
PI_CURRENT_OBJECT = PI + 4
PI_CANDIDATES = PI + 8
PLAYER = 0x03001160

FUSE_TARGET_NEARBY = game_sym('QuickStartFuseTargetNearby')
# Castle Garden's nine fuser spots, from sQuickStartFuserSpots. One of them
# is occupied on any given run.
GARDEN_SPOTS = ((776, 328), (248, 280), (328, 488), (424, 104), (584, 104),
                (664, 488), (488, 376), (408, 216), (600, 216))

PAIR_BASE, KIND_COUNT = 26, 5
QS_CHAIN_WAVE = 2
NO_STEP, CHAIN_DONE = 91, 92
AREA_DOJOS, ROOM_GRIMBLADE = None, None


def ids(path):
    import re
    out = {}
    for line in open(os.path.join(P.ROOT, 'build/USA/enum_include/' + path)):
        m = re.match(r'\.set (\w+), (\d+)', line.strip())
        if m:
            out.setdefault(m.group(1), int(m.group(2)))
    return out


def r16(c, a):
    return c.memory.u8[a] | (c.memory.u8[a + 1] << 8)


def w16(c, a, v):
    c.memory.u8[a] = v & 0xFF
    c.memory.u8[a + 1] = (v >> 8) & 0xFF


def w32(c, a, v):
    for i in range(4):
        c.memory.u8[a + i] = (v >> (8 * i)) & 0xFF


def real_fuser_control():
    """Stand next to an actual spawned fuser and press Select.

    The first version of this control dressed gPossibleInteraction by hand
    and failed - not because the code was wrong but because the engine
    rescans interactables every frame and puts currentIndex back to 0xFF
    before QuickStartRoomMonitor ever looks. A poked control measures the
    poke. So this finds a real one: walk the player onto each of Castle
    Garden's nine fuser spots and ask the ROM's own predicate which one has
    somebody standing on it.
    """
    A, R = ids('area.inc'), ids('roomid.inc')
    c = boot(ROM)
    poison_here(c)
    warp(c, A['AREA_CASTLE_GARDEN'], R['ROOM_CASTLE_GARDEN_MAIN'], 0x78, 0xa0)
    for _ in range(10):
        press(c, c.KEY_A, 5, 5)
    ox = r16(c, 0x03000bf0 + 6)
    oy = r16(c, 0x03000bf0 + 8)
    found = None
    for (sx, sy) in GARDEN_SPOTS:
        for (dx, dy) in ((0, 20), (0, -20), (20, 0), (-20, 0)):
            w16(c, PLAYER + 0x2e, ox + sx + dx)
            w16(c, PLAYER + 0x32, oy + sy + dy)
            for _ in range(6):
                press(c, c.KEY_A, 2, 2)
            if call_keep(c, FUSE_TARGET_NEARBY, ()):
                found = (sx, sy, dx, dy)
                break
        if found:
            break
    if found is None:
        print('CONTROL real fuser     : no fuser found on any Castle Garden spot - INCONCLUSIVE')
        del c
        return None
    c.memory.u8[HINT_IDX] = 0
    c.memory.u8[HINT_IDX + 1] = 0
    press(c, c.KEY_SELECT, 4, 12)
    got = r16(c, HINT_IDX)
    # "No hint at all" is the wrong bar. The press is SUPPOSED to reach the
    # fusion machinery, and with an empty Kinstone bag that machinery has
    # its own line to say (TEXT_EZLO 0x65, "you don't have any Kinstone
    # Pieces"). What must not happen is a line from bank 2 - that would be
    # this monitor stealing a press the fusion screen wanted.
    ok = (got >> 8) != 0xFF
    who = 'bank2 line %d' % (got & 0xFF) if (got >> 8) == 0xFF else ('the fusion path (0x%04x)' % got if got else 'nothing')
    print(f'CONTROL real fuser     : spot {found[:2]}, {who}  {"ok" if ok else "FAIL"}')
    del c
    return ok


def one(label, setup, fuser, expect):
    A, R = ids('area.inc'), ids('roomid.inc')
    c = boot(ROM)
    poison_here(c)
    warp(c, A['AREA_DOJOS'], R['ROOM_DOJOS_GRIMBLADE'], 0x78, 0xa0)
    for _ in range(10):
        press(c, c.KEY_A, 5, 5)
    setup(c)
    if fuser:
        # Dress the interaction state exactly the way the real fusion path
        # reads it: a current index, a candidate with a live kinstone id,
        # and an entity behind it.
        c.memory.u8[PI_CANDIDATES + 3] = 1          # kinstoneId
        w32(c, PI_CANDIDATES + 4, 0)                # customHitbox
        w32(c, PI_CANDIDATES + 8, PLAYER)           # entity - any non-NULL
        w32(c, PI_CURRENT_OBJECT, PI_CANDIDATES)
        c.memory.u8[PI_CURRENT_INDEX] = 0
    else:
        c.memory.u8[PI_CURRENT_INDEX] = 0xFF
        w32(c, PI_CURRENT_OBJECT, 0)
    c.memory.u8[HINT_IDX] = 0
    c.memory.u8[HINT_IDX + 1] = 0
    # Hand-rolled press rather than emu.press, because the fuser dressing
    # has to be re-applied EVERY frame: the engine rescans interactables
    # once a frame and puts currentIndex back to 0xFF, so a one-shot poke
    # before the press is gone by the time the button edge is read.
    def dress():
        if fuser:
            c.memory.u8[PI_CANDIDATES + 3] = 1
            w32(c, PI_CANDIDATES + 8, PLAYER)
            w32(c, PI_CURRENT_OBJECT, PI_CANDIDATES)
            c.memory.u8[PI_CURRENT_INDEX] = 0
    for _ in range(4):
        dress()
        c.set_keys(c.KEY_SELECT)
        c.run_frame()
    c.clear_keys(c.KEY_SELECT)
    for _ in range(12):
        dress()
        c.run_frame()
    got = r16(c, HINT_IDX)
    ok = expect(got)
    print(f'{label}: hint_idx = 0x{got:04x} ({"bank2 line %d" % (got & 0xFF) if (got >> 8) == 0xFF else "none"})'
          f'  {"ok" if ok else "FAIL"}')
    del c
    return ok


def main():
    def set_none(c):
        c.memory.u8[CHAIN_ROLLED] = 0
        c.memory.u8[CHAIN_PROGRESS] = 0

    def set_done(c):
        c.memory.u8[CHAIN_ROLLED] = 5
        c.memory.u8[CHAIN_PROGRESS] = 5

    def set_wave(c):
        c.memory.u8[CHAIN_ROLLED] = 1
        c.memory.u8[CHAIN_PROGRESS] = 0
        c.memory.u8[CHAIN_KIND] = QS_CHAIN_WAVE
        c.memory.u8[CHAIN_WHERE] = 0
        # Mark every step already hinted. Otherwise QuickStartChainHintOnce
        # fires its own once-per-step region line on the same frames and the
        # probe reads that instead - which is how the first run of this
        # measured line 4 ("Lon Lon Ranch") for both the test AND the
        # control, and would have read as the control failing.
        c.memory.u8[CHAIN_HINTED] = 0xFF

    def is_line(n):
        return lambda got: got == (0xFF << 8) | n

    def is_wave_pair(got):
        if (got >> 8) != 0xFF:
            return False
        n = got & 0xFF
        return PAIR_BASE <= n <= 90 and (n - PAIR_BASE) % KIND_COUNT == QS_CHAIN_WAVE

    results = [
        one('no step rolled      ', set_none, False, is_line(NO_STEP)),
        one('chain finished      ', set_done, False, is_line(CHAIN_DONE)),
        one('live WAVE step      ', set_wave, False, is_wave_pair),
    ]
    control = real_fuser_control()
    if control is not None:
        results.append(control)
    print()
    print('PASS' if all(results) else 'FAIL: %d of %d' % (results.count(False), len(results)))
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
