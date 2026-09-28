"""Is every region's sky-drop landing spot safe to land on?

The pit in Cloud Tops rewrites player_status to sQuickStartRegionPool's
entranceX/entranceY (QuickStartProcessHubHoleLink), so that one coordinate
per region is where a run begins. Two ways it can be wrong, both reported:

  a) it is not hard ground - Castor Wilds dropped the player into the swamp;
  b) it is shared with something else, most often one of the region's own
     enemy spawn offsets, so the player lands in contact and takes a hit
     before they can move.

(b) is answered statically: the offsets are a table and so is the entrance.
(a) is answered from the ACT TILE under the coordinate, read out of the
running game and mapped through the ROM's own gMapActTileToSurfaceType.

Reading the act tile rather than gPlayerState.floor_type is not a detail.
floor_type looks like the same answer and is not: once the player is
standing in swamp it stops tracking, so teleporting around and reading it
back reports swamp everywhere. Measured in Castor Wilds - every one of the
1933 open tiles came back SURFACE_SWAMP, and every one of the 72 enemy
offsets with it, which would have meant the region had no dry ground at all.
The act tiles say 1039 of those tiles are ordinary ground. The sticky read
is a property of the player, not of the map.

  python3 tools/quickstart/drop_spots.py             audit all 18
  python3 tools/quickstart/drop_spots.py --propose   nearest safe replacement
"""
import collections
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import (boot, warp, press, poison_here, here, room_dims, coll_at, act_at, r16,
                 entities, KIND_ENEMY)
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
PLAYER_ENTITY = 0x03001160
HEALTH = PLAYER_ENTITY + 0x45
ROOM_CONTROLS = 0x03000BF0

# How close an enemy offset may sit to the drop spot. Three tiles: the player
# lands with no control for the drop animation, and a contact hitbox plus an
# enemy's own first step covers well over one. Must match
# QUICKSTART_DROP_CLEAR_PX in src/game.c.
CLEAR_PX = 48

# "Instant damage on landing" is the report, so the window is half a second,
# not the several seconds it takes a wave to walk over and earn a hit.
LAND_FRAMES = 30


def enums():
    """ACT_TILE_* -> value, SURFACE_* -> value, act tile -> surface."""
    act = {m.group(1): int(m.group(2), 0) for m in
           re.finditer(r'\b(ACT_TILE_\d+)\s*=\s*(0x[0-9a-fA-F]+|\d+)',
                       open(os.path.join(P.ROOT, 'include/tiles.h')).read())}
    ph = open(os.path.join(P.ROOT, 'include/player.h')).read()
    i = ph.find('typedef enum {\n    SURFACE_NORMAL,')
    surf, n = {}, 0
    for line in ph[i:ph.find('} SurfaceType;', i)].split('\n')[1:]:
        line = re.sub(r'//.*', '', line).strip().rstrip(',')
        if not line:
            continue
        if '=' in line:
            name, val = [t.strip() for t in line.split('=')]
            n = int(val, 0)
            surf[name] = n
        else:
            surf[line] = n
        n += 1
    pairs = re.findall(r'\{\s*(ACT_TILE_\d+)\s*,\s*(SURFACE_\w+)\s*\}',
                       open(os.path.join(P.ROOT, 'src/data/mapActTileToSurfaceType.c')).read())
    return surf, {act[a]: surf[s] for a, s in pairs if a in act and s in surf}


SURF, ACT2SURF = enums()
SURF_NAME = {v: k for k, v in SURF.items()}

# What a run may begin standing on. An act tile with no row in the ROM's
# table is SURFACE_NORMAL by construction, which is most of the overworld.
# The two LIGHT_GRADE slopes are in because Castle Garden's landing is on
# one and it costs nothing; buttons and the two ground-to-ground slopes are
# ordinary floor. Everything else is a finding - swamp and water need kit to
# cross, a pit or a hole is a fall, ice is not somewhere to arrive with no
# control.
SAFE = {SURF['SURFACE_NORMAL'], SURF['SURFACE_SLOPE_GNDGND_V'], SURF['SURFACE_SLOPE_GNDGND_H'],
        SURF['SURFACE_BUTTON'], SURF['SURFACE_LIGHT_GRADE'], SURF['SURFACE_29']}


def ids(path):
    out = {}
    for line in open(os.path.join(P.ROOT, 'build/USA/enum_include/' + path)):
        m = re.match(r'\.set (\w+), (\d+)', line.strip())
        if m:
            out.setdefault(m.group(1), int(m.group(2)))
    return out


A, R = ids('area.inc'), ids('roomid.inc')


def offset_tables():
    out = {}
    for m in re.finditer(r'static const s16 (sQuickStart\w*EnemyOffsets)\[\d*\]\[2\] = \{(.*?)\};',
                         P.GAME, re.S):
        body = re.sub(r'//[^\n]*', '', m.group(2))
        pairs = re.findall(r'\{\s*(0x[0-9a-fA-F]+|\d+)\s*,\s*(0x[0-9a-fA-F]+|\d+)\s*\}', body)
        out[m.group(1)] = [(int(a, 0), int(b, 0)) for a, b in pairs]
    return out


def pool_rows():
    i = P.GAME.find('static const QuickStartRegion sQuickStartRegionPool[] = {')
    body = re.sub(r'//[^\n]*', '', P.GAME[i:P.GAME.find('\n};', i)])
    num = r'(?:0x[0-9a-fA-F]+|\d+)'
    rows = re.findall(
        r'\{\s*(AREA_\w+),\s*(ROOM_\w+),\s*(' + num + r'),\s*(' + num + r'),'
        r'\s*' + num + r',\s*' + num + r',\s*' + num + r',\s*' + num + r','
        r'\s*(sQuickStart\w+),\s*ARRAY_COUNT\(\w+\),\s*\w+,\s*(' + num + r'),\s*(' + num + r')', body)
    return [(a, r, int(ex, 0), int(ey, 0), t, int(rx, 0), int(ry, 0))
            for a, r, ex, ey, t, rx, ry in rows]


def surface_of(c, lx, ly):
    return ACT2SURF.get(act_at(c, lx // 16, ly // 16), SURF['SURFACE_NORMAL'])


def sname(s):
    return SURF_NAME.get(s, hex(s))[8:]


def flood(c, stx, sty, tw, th):
    seen = {(stx, sty)}
    q = collections.deque([(stx, sty)])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if (nx, ny) in seen or not (0 <= nx < tw and 0 <= ny < th):
                continue
            if coll_at(c, nx, ny) != 0:
                continue
            seen.add((nx, ny))
            q.append((nx, ny))
    return seen


def in_room(area, room, ex, ey):
    """Boot, drop the player on the coordinate, hand back the core."""
    c = boot(ROM)
    poison_here(c)
    warp(c, A[area], R[room], ex, ey)
    if here(c) != (A[area], R[room]):
        del c
        return None
    return c


def wave_placement(area, room, ex, ey, offs):
    """How many enemies were PLACED inside the landing square.

    Sampled on the frame the wave first appears, not after letting the room
    run: an enemy that walked into the square is ordinary gameplay, and only
    where the spawner put it says anything about the rule. Two regions read
    as occupied when this was measured 300 frames in, and neither had
    anything of ours placed there.
    """
    c = boot(ROM)
    poison_here(c)
    warp(c, A[area], R[room], ex, ey, frames=0)
    for _ in range(400):
        c.run_frame()
        if here(c) != (A[area], R[room]):
            continue
        live = entities(c, KIND_ENEMY)
        if live:
            ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
            # Only OUR placements count. A room's vanilla enemies stand
            # where the vanilla room put them and this mode neither places
            # nor moves them - the Wind Ruins' below-fortress room has one
            # about twenty pixels from the landing spot, and calling that a
            # failure of a rule about our own spawner would be wrong.
            n = sum(1 for e in live
                    if abs((e[4] - ox) - ex) < CLEAR_PX and abs((e[5] - oy) - ey) < CLEAR_PX
                    and (e[4] - ox, e[5] - oy) in offs)
            del c
            return n
    del c
    return 0


def audit():
    tables = offset_tables()
    rows = pool_rows()
    print(f'{len(rows)} region pool rows\n')
    bad = 0
    for area, room, ex, ey, tab, rx, ry in rows:
        offs = tables.get(tab, [])
        # The shipped rule is a square, so measure a square (see
        # QuickStartOnRegionDropSpot).
        box = [o for o in offs if abs(o[0] - ex) < CLEAR_PX and abs(o[1] - ey) < CLEAR_PX]
        exact = [o for o in offs if o == (ex, ey)]
        c = in_room(area, room, ex, ey)
        if c is None:
            print(f'{room[5:]:<38} never landed - INCONCLUSIVE')
            continue
        surf = surface_of(c, ex, ey)
        hp0 = c.memory.u8[HEALTH]
        for _ in range(LAND_FRAMES // 6):
            press(c, 0, 3, 3)
        hp1 = c.memory.u8[HEALTH]
        # What ACTUALLY spawned in the square, which is the question the
        # table rows only approximate. A row inside the square is inert now -
        # QuickStartOnRegionDropSpot refuses it at placement time - so the
        # rows are reported as suppressed and only a live body is a finding.
        del c
        live = wave_placement(area, room, ex, ey, set(offs))
        notes = []
        if surf not in SAFE:
            notes.append(f'SURFACE {sname(surf)}')
        if hp1 < hp0:
            notes.append(f'LOST {hp0 - hp1} HP in the first {LAND_FRAMES} frames')
        if live:
            notes.append(f'{live} enemy PLACED in the square')
        if notes:
            bad += 1
        suppressed = (f'{len(box)} row(s) suppressed' if box else 'clear')
        if exact:
            suppressed += f' ({len(exact)} of them exactly on it)'
        print(f'{room[5:]:<38} ({ex:>4},{ey:>4}) {sname(surf):<14} hp {hp0}->{hp1}  '
              f'{"; ".join(notes) if notes else "ok"}, {suppressed}')
    print(f'\n{bad} of {len(rows)} drop spot(s) with a finding')
    return 1 if bad else 0


def propose():
    """The nearest ground a run may begin on, for any spot that is not.

    A MINIMAL correction. Enemy-offset spacing is deliberately NOT a
    constraint: the shipped rule (QuickStartOnRegionDropSpot) keeps a clear
    square around whatever this coordinate ends up being, so a proposal does
    not have to dodge the table - it is only a tie-break, so a spot with room
    around it wins over one hemmed in by three offsets.
    """
    tables = offset_tables()
    for area, room, ex, ey, tab, rx, ry in pool_rows():
        offs = tables.get(tab, [])
        c = in_room(area, room, ex, ey)
        if c is None:
            print(f'{room[5:]:<38} never landed - SKIPPED')
            continue
        if surface_of(c, ex, ey) in SAFE:
            print(f'{room[5:]:<38} ({ex:>4},{ey:>4})  keep - {sname(surface_of(c, ex, ey))}')
            del c
            continue
        w, h = room_dims(c)
        tw, th = w // 16, h // 16
        stx, sty = ex // 16, ey // 16
        # Castle Garden's landing is on a LIGHT_GRADE slope, whose collision
        # byte is not 0 even though the player stands on it - so seeding the
        # flood on the landing tile itself fails there. Seed on the nearest
        # plain-open tile instead; it is the same component by construction,
        # since the player walks off the slope onto it.
        if coll_at(c, stx, sty) != 0:
            near = [(abs(tx - stx) + abs(ty - sty), tx, ty)
                    for ty in range(th) for tx in range(tw) if coll_at(c, tx, ty) == 0]
            if not near:
                print(f'{room[5:]:<38} no open tile anywhere - SKIPPED')
                del c
                continue
            _, stx, sty = min(near)
        comp = flood(c, stx, sty, tw, th)
        cands = []
        for (tx, ty) in comp:
            if not (1 <= tx < tw - 1 and 1 <= ty < th - 1):
                continue
            if any(coll_at(c, tx + dx, ty + dy) != 0
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                continue
            lx, ly = tx * 16 + 8, ty * 16 + 8
            if surface_of(c, lx, ly) not in SAFE:
                continue
            if any(surface_of(c, tx * 16 + 8 + dx * 16, ty * 16 + 8 + dy * 16) not in SAFE
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                continue
            crowd = sum(1 for o in offs if math.dist((lx, ly), o) < CLEAR_PX)
            cands.append((round(math.dist((lx, ly), (ex, ey))), crowd, lx, ly))
        cands.sort()
        if not cands:
            print(f'{room[5:]:<38} ({ex:>4},{ey:>4})  NO CANDIDATE '
                  f'({len(comp)} tiles in the component)')
            del c
            continue
        d, crowd, lx, ly = cands[0]
        surf = surface_of(c, lx, ly)
        del c
        print(f'{room[5:]:<38} ({ex:>4},{ey:>4}) -> ({lx:>4},{ly:>4})  {sname(surf):<14} '
              f'moved {d}px, {crowd} offset(s) near it, {len(cands)}/{len(comp)} tiles qualified')
    return 0


if __name__ == '__main__':
    sys.exit(propose() if '--propose' in sys.argv else audit())
