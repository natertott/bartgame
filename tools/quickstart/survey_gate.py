"""Every DOOR the survey's places sit behind: does containment let it fire?

world_reach.py says what a place COSTS. This says whether the mode lets you
go there at all, which is a different question and the one that has bitten
three times now - Melari's Mine, Minish Village and most of Lake Hylia were
all fully wired in the transition data, priced in the survey, and cancelled
the frame their door fired, because the room they led into was not blessed
as a pocket.

Method is seam_gate.py's: stage the transition the way vanilla's door and
border code does (area_next, room_next, transitioningOut), run all three
containment functions, see whether the flag survives.

WHAT IT ASKS, AND WHY THAT TOOK TWO TRIES. The first version asked "from
this region's survey START, can I reach X" for every X the survey names.
That is the wrong question twice over: most of those places are two or three
doors deep, so there is no transition from the start room to them at all,
and a cancelled answer to an imaginary door is noise. It reported Melari's
Mine's side rooms as traps by asking whether they could return to a Mount
Crenel room they have never had a door to.

So this walks the EXIT TABLE instead. For every room the survey names, find
the rooms whose own exit lists lead into it and ask the gate from each of
those - the real door, from the real side. Then ask the reverse: from the
room itself, along each of ITS exits. A room is a TRAP only if every one of
its own exits is cancelled; one open way out is enough.

A transition is only POLICED when the room the player is standing in is a
named region room or a contained area (Castle Garden, Minish House
Interiors, Tree Interiors). Anywhere else every transition is allowed by
default, so those are reported as "unpoliced" rather than as passes - a
clean run must not be mistaken for coverage.

Usage: python3 tools/quickstart/survey_gate.py [SURVEY-KEY ...]
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, poison_here, here
from callrom import call_keep, game_sym
import parse_tables as P
import exit_lists as X
import world_reach as W

ROM = os.path.join(P.ROOT, 'tmc.gba')
ROOM_TRANSITION = 0x030010A0
TRANSITIONING_OUT = ROOM_TRANSITION + 0x08
AREA_NEXT = ROOM_TRANSITION + 0x0c
ROOM_NEXT = ROOM_TRANSITION + 0x0d

GATES = [game_sym(n) for n in ('QuickStartEnforceContainment',
                               'QuickStartEnforceLonLonContainment',
                               'QuickStartEnforceFieldRegionContainment')]

CONTAINED_AREAS = {'AREA_CASTLE_GARDEN', 'AREA_MINISH_HOUSE_INTERIORS', 'AREA_TREE_INTERIORS'}
POLICED_AREAS = {'AREA_HYRULE_FIELD', 'AREA_CASTOR_WILDS', 'AREA_RUINS',
                 'AREA_MINISH_WOODS', 'AREA_LAKE_HYLIA', 'AREA_MT_CRENEL'}


def ids(path):
    out = {}
    for line in open(os.path.join(P.ROOT, 'build/USA/enum_include/' + path)):
        m = re.match(r'\.set (\w+), (\d+)', line.strip())
        if m:
            out.setdefault(m.group(1), int(m.group(2)))
    return out


A, R = ids('area.inc'), ids('roomid.inc')
REGION_ROOMS = {r['roomName'] for r in P.region_pool()}

# room -> the AREA_* it belongs to, and room -> [(area, room)] leading in.
AREA_OF, INBOUND = {}, collections.defaultdict(set)
for src, rows in X.BY_ROOM.items():
    for w, sx, sy, ex, ey, shape, da, dr in rows:
        AREA_OF[dr] = da
        INBOUND[dr].add(src)
for src in X.BY_ROOM:
    if src in AREA_OF:
        continue
    for area in A:
        if src.startswith('ROOM_' + area[5:] + '_') and (
                src not in AREA_OF or len(area) > len(AREA_OF[src])):
            AREA_OF[src] = area

# An arrival coordinate for a room: the (endX, endY) of any door into it.
ARRIVAL = {}
for src, rows in X.BY_ROOM.items():
    for w, sx, sy, ex, ey, shape, da, dr in rows:
        ARRIVAL.setdefault(dr, (ex, ey))


def policed(room_name):
    area = AREA_OF.get(room_name)
    if area in CONTAINED_AREAS:
        return True
    return area in POLICED_AREAS and room_name in REGION_ROOMS


def ask(from_room, to_area, to_room):
    """Stand in from_room, stage a transition to to_room, run the gates."""
    fa = AREA_OF.get(from_room)
    if fa not in A or from_room not in R or to_area not in A or to_room not in R:
        return None
    x, y = ARRIVAL.get(from_room, (None, None))
    if x is None:
        return None
    c = boot(ROM)
    poison_here(c)
    warp(c, A[fa], R[from_room], x, y)
    if here(c) != (A[fa], R[from_room]):
        del c
        return None
    c.memory.u8[AREA_NEXT] = A[to_area]
    c.memory.u8[ROOM_NEXT] = R[to_room]
    c.memory.u8[TRANSITIONING_OUT] = 1
    for g in GATES:
        call_keep(c, g, ())
    out = c.memory.u8[TRANSITIONING_OUT] != 0
    del c
    return out


def main():
    keys = [a for a in sys.argv[1:] if not a.startswith('-')] or list(W.SURVEY)
    rooms = []
    for key in keys:
        for e in W.SURVEY[key]['dests']:
            name = 'ROOM_%s_%s' % (e['area'], e['room'])
            if name in R and (key, name) not in rooms:
                rooms.append((key, name))
    seen, doors_in, traps, asked = set(), [], [], 0
    for key, room in rooms:
        if room in seen:
            continue
        seen.add(room)
        ways_in, ways_out = [], []
        for src in sorted(INBOUND.get(room, ())):
            if not policed(src):
                continue
            ans = ask(src, AREA_OF.get(room), room)
            if ans is None:
                continue
            asked += 1
            ways_in.append((src, ans))
        if policed(room):
            for w, sx, sy, ex, ey, shape, da, dr in X.BY_ROOM.get(room, []):
                ans = ask(room, da, dr)
                if ans is None:
                    continue
                asked += 1
                ways_out.append((dr, ans))
        bits = []
        if not ways_in:
            bits.append('IN unpoliced' if room in AREA_OF else 'IN no door')
        else:
            bad = [s for s, ok in ways_in if not ok]
            bits.append('IN %d/%d doors open' % (len(ways_in) - len(bad), len(ways_in)))
            if len(bad) == len(ways_in):
                doors_in.append((key, room, bad))
        if not ways_out:
            bits.append('OUT unpoliced')
        else:
            good = [d for d, ok in ways_out if ok]
            bits.append('OUT %d/%d exits open' % (len(good), len(ways_out)))
            if not good:
                traps.append((key, room))
        print(f'  {room[5:]:<48} {", ".join(bits)}')
    print(f'\n{asked} policed transition(s) asked across {len(seen)} room(s)')
    if doors_in:
        print(f'\nNO WAY IN - every policed door into these is cancelled ({len(doors_in)}):')
        for key, room, bad in doors_in:
            print(f'  {key:<10} {room[5:]:<46} from {", ".join(s[5:] for s in bad)}')
    if traps:
        print(f'\nTRAPS - every exit cancelled ({len(traps)}):')
        for key, room in traps:
            print(f'  {key:<10} {room[5:]}')
    if not doors_in and not traps:
        print('nothing cancelled')
    return 1 if (doors_in or traps) else 0


if __name__ == '__main__':
    sys.exit(main())
