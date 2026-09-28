"""Does a region pay its clear reward the moment the player walks in?

The report: "the player walks into a new region and receives the room clear
reward instantly, as soon as they arrive in the room ... quite often."

Warping in does not reproduce it, and that is the finding that matters:
QuickStartRegionMonitor's settled-room guard already covers the torn window
a warp lands in. So this WALKS - stand in a region with its wave up, hold a
direction across the real border or scroll seam, and watch what happens on
the other side.

The signal is gSave.reward_drop_x/y. QuickStartSpawnRegionRewardItem is the
only thing that writes it, so a change means the region paid out; counting
GROUND_ITEMs does not work, because several overworld rooms have vanilla
rupee clusters of their own sitting on the floor (South Hyrule Field alone
has six, which is what a first pass at this mistook for six prizes).

Usage: python3 tools/quickstart/region_arrival.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, here, poison_here, press, r16, entities, KIND_ENEMY
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
GSAVE = 0x02002A40
REWARD_DROP_X = GSAVE + 0x22
REWARD_DROP_Y = GSAVE + 0x24

# (label, from area/room/spawn, key to hold, expected destination room)
# Every leg is a crossing into a DIFFERENT region's room, or across a scroll
# seam inside a multi-room region - the two shapes a walk-in can take.
# (label, from area/room/spawn, key to hold)
#
# The coordinates are the ones region_walk.py MEASURED, not guesses. An
# overworld border is open only in bands and the rest of the edge is cliff,
# so "held a direction and nothing happened" is terrain, not a finding.
LEGS = [
    ('EH North  -> Minish Woods (border)', 'AREA_HYRULE_FIELD',
     'ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH', 440, 104, 'KEY_RIGHT'),
    ('EH South  -> Minish Woods (border)', 'AREA_HYRULE_FIELD',
     'ROOM_HYRULE_FIELD_EASTERN_HILLS_SOUTH', 440, 152, 'KEY_RIGHT'),
    ('Lon Lon   -> Lake Hylia   (border)', 'AREA_HYRULE_FIELD',
     'ROOM_HYRULE_FIELD_LON_LON_RANCH', 680, 440, 'KEY_RIGHT'),
    ('Trilby    -> Mount Crenel (border)', 'AREA_HYRULE_FIELD',
     'ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS', 40, 424, 'KEY_LEFT'),
    ('Minish W. -> EH North     (border)', 'AREA_MINISH_WOODS',
     'ROOM_MINISH_WOODS_MAIN', 24, 424, 'KEY_LEFT'),
    ('Lake Hylia-> Lon Lon      (border)', 'AREA_LAKE_HYLIA',
     'ROOM_LAKE_HYLIA_MAIN', 24, 440, 'KEY_LEFT'),
    # Scroll seams, the other shape a walk-in takes: two rooms of one area
    # sharing a pixel grid, with no Transition row anywhere. Worth testing
    # separately because a seam is not a room LOAD the way a border is, and
    # gRoomVars - which holds room flag 0, "a wave is up" - is wiped on a
    # load. Directions found by sweeping all four from each region's own
    # entrance; the ones not listed are cliff.
    ('EH South  -> EH Center    (seam)', 'AREA_HYRULE_FIELD',
     'ROOM_HYRULE_FIELD_EASTERN_HILLS_SOUTH', 328, 104, 'KEY_UP'),
    ('EH Center -> EH North     (seam)', 'AREA_HYRULE_FIELD',
     'ROOM_HYRULE_FIELD_EASTERN_HILLS_CENTER', 248, 104, 'KEY_UP'),
    ('WW Center -> WW North     (seam)', 'AREA_HYRULE_FIELD',
     'ROOM_HYRULE_FIELD_WESTERN_WOODS_CENTER', 264, 88, 'KEY_UP'),
    ('WW Center -> WW South     (seam)', 'AREA_HYRULE_FIELD',
     'ROOM_HYRULE_FIELD_WESTERN_WOODS_CENTER', 264, 88, 'KEY_DOWN'),
    ('Ruins ent.-> Below fort.  (seam)', 'AREA_RUINS',
     'ROOM_RUINS_ENTRANCE', 216, 456, 'KEY_RIGHT'),
]

SETTLE = 240  # frames to let the start room deal its wave before walking


def run(label, area, room, x, y, key):
    c = boot(ROM)
    poison_here(c)
    warp(c, P.AREAS[area], P.ROOMS[room], x, y)
    if here(c) != (P.AREAS[area], P.ROOMS[room]):
        print(f'{label}: never landed in the start room - INCONCLUSIVE')
        del c
        return None
    # Dismiss the region intro hint, then let the start room deal its wave.
    # Without the first part the player never takes a step: an Ezlo hint
    # holds PL_BUSY and the probe reports "never crossed".
    for _ in range(10):
        press(c, c.KEY_A, 5, 5)
    for _ in range(SETTLE):
        c.run_frame()
    before = (r16(c, REWARD_DROP_X), r16(c, REWARD_DROP_Y))
    started = here(c)
    armed = len(entities(c, KIND_ENEMY))
    k = getattr(c, key)
    crossed = -1
    for f in range(900):
        c.set_keys(k)
        c.run_frame()
        if here(c) != started:
            crossed = f
            break
    c.clear_keys(k)
    if crossed < 0:
        print(f'{label}: never crossed in 900 frames - INCONCLUSIVE '
              f'(still in {here(c)})')
        del c
        return None
    landed = here(c)
    paid = None
    for f in range(240):
        c.run_frame()
        now = (r16(c, REWARD_DROP_X), r16(c, REWARD_DROP_Y))
        if now != before and paid is None:
            paid = (f, now, len(entities(c, KIND_ENEMY)))
    del c
    ok = paid is None
    if ok:
        print(f'{label}: crossed into {landed} with {armed} enemies behind, '
              f'no payout in 240 frames  ok')
    else:
        f, now, live = paid
        print(f'{label}: crossed into {landed}, PAID OUT at arrival frame {f} '
              f'(reward_drop {before} -> {now}, {live} enemies alive)  FAIL')
    return ok


ROOM_VARS = 0x02034350
ROOM_FLAGS = ROOM_VARS + 0x14
QS_ROOM_FLAG_ORIGIN = 256


def qs_room_flag(c, n):
    b = QS_ROOM_FLAG_ORIGIN + n
    return (c.memory.u8[ROOM_FLAGS + (b >> 3)] >> (b & 7)) & 1


def pool_rows():
    i = P.GAME.find('static const QuickStartRegion sQuickStartRegionPool[] = {')
    body = re.sub(r'//[^\n]*', '', P.GAME[i:P.GAME.find('\n};', i)])
    num = r'(?:0x[0-9a-fA-F]+|\d+)'
    return [(a, r, int(x, 0), int(y, 0)) for a, r, x, y in re.findall(
        r'\{\s*(AREA_\w+),\s*(ROOM_\w+),\s*(' + num + r'),\s*(' + num + r')', body)]


def armed():
    """Is QuickStartRegionWaveCleared ever TRUE during an arrival?

    This is the condition the reward gate now rests on, for BOTH the first
    payout and the re-drop, so it is the thing worth measuring rather than
    the payout itself: reaching reward state 1 in a probe means clearing a
    region's wave with the sword, which takes longer than it is worth.

    Cleared = room flag 0 ("a wave is up") AND no ENEMY in the room. Flag 0
    lives in gRoomVars, which the room load wipes, so the expected answer is
    that it is never true on arrival - and the measurement also catches the
    other way it could go wrong, a deal that arms flag 0 having placed
    nothing (see QuickStartSpawnRegionWave).
    """
    rows = pool_rows()
    bad = 0
    for area, room, ex, ey in rows:
        c = boot(ROM)
        poison_here(c)
        warp(c, P.AREAS[area], P.ROOMS[room], ex, ey, frames=0)
        hit, frames = None, 0
        for f in range(400):
            c.run_frame()
            if here(c) != (P.AREAS[area], P.ROOMS[room]):
                continue
            frames += 1
            if qs_room_flag(c, 0) and not entities(c, KIND_ENEMY) and hit is None:
                hit = f
        del c
        if hit is not None:
            bad += 1
        print(f'  {room[5:]:<38} {frames:>3} frames in room, '
              f'{"CLEARED-ON-ARRIVAL at frame %d  FAIL" % hit if hit is not None else "never read as cleared  ok"}')
    print(f'\n{bad} of {len(rows)} regions read as a cleared wave during arrival')
    return 1 if bad else 0


def main():
    if '--armed' in sys.argv:
        return armed()
    res = [run(*leg) for leg in LEGS]
    real = [r for r in res if r is not None]
    print()
    if not real:
        print('INCONCLUSIVE: nothing crossed')
        return 2
    bad = real.count(False)
    print(f'PASS: {len(real)} walk-ins, none paid on arrival' if not bad
          else f'FAIL: {bad} of {len(real)} paid on arrival')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
