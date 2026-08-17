"""The dead doors, their approach sides, and whether the way back works.

door_audit.py says which ring doors never fire. This works out what to do
about each one: which side of the door the player can actually stand on
(that is where the position box goes), where the door's own Transition row
says to put them down on the other side (that is the spawn), and - the part
that decides whether a fix is safe at all - whether the room behind the
door can be left again on foot. A box into a room with a dead exit is a
trap, not a fix.

Emits the sQuickStartDoorBoxes rows for src/game.c.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import door_audit as D
from emu import boot, warp, here, poison_here, coll_at, r16, PLAYER, ROOM_CONTROLS

ROM = D.ROM
# Every dead door with a wired ? room behind it, as (roomName, doorX, doorY).
DEAD = [
    ('ROOM_CASTLE_GARDEN_MAIN', 776, 72),
    ('ROOM_CASTLE_GARDEN_MAIN', 232, 72),
    ('ROOM_HYRULE_FIELD_LON_LON_RANCH', 504, 520),
    ('ROOM_HYRULE_FIELD_LON_LON_RANCH', 136, 852),
    ('ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD', 928, 552),
    ('ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD', 280, 168),
    ('ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD', 88, 280),
    ('ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD', 376, 216),
    ('ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD', 72, 456),
    ('ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD', 432, 296),
    ('ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD', 576, 296),
    ('ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD', 432, 392),
    ('ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD', 576, 392),
    ('ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD', 752, 312),
    ('ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD', 504, 340),
    ('ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS', 136, 546),
    ('ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS', 56, 680),
    ('ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS', 408, 690),
    ('ROOM_HYRULE_FIELD_EASTERN_HILLS_SOUTH', 56, 40),
    ('ROOM_HYRULE_FIELD_EASTERN_HILLS_CENTER', 168, 152),
    ('ROOM_HYRULE_FIELD_WESTERN_WOODS_SOUTH', 184, 40),
    ('ROOM_HYRULE_FIELD_WESTERN_WOODS_NORTH', 160, 488),
]

SIDES = (('below', 0, 1, 'UP'), ('above', 0, -1, 'DOWN'),
         ('right', 1, 0, 'LEFT'), ('left', -1, 0, 'RIGHT'))


def region(room_name):
    import parse_tables as P
    return next(r for r in P.region_pool() if r['roomName'] == room_name)


def door_row(room_name, dx, dy):
    for f in D.BY_ROOM.get(room_name, []):
        if f[0] == 'WARP_TYPE_AREA' and D.num(f[1]) == dx and D.num(f[2]) == dy:
            return f
    return None


def main():
    boots = {}
    print('== approach sides and spawns ==')
    rows = []
    for room_name, dx, dy in DEAD:
        r = region(room_name)
        key = (r['area'], r['room'])
        if key not in boots:
            c = boot(ROM)
            poison_here(c)
            warp(c, r['area'], r['room'], dx, dy)
            boots[key] = c if here(c) == key else None
        c = boots[key]
        if c is None:
            print(f'{room_name} ({dx},{dy}): room would not load')
            continue
        f = door_row(room_name, dx, dy)
        tx, ty = dx // 16, dy // 16
        open_sides = []
        for label, ox, oy, key_name in SIDES:
            v = coll_at(c, tx + ox, ty + oy)
            v2 = coll_at(c, tx + ox * 2, ty + oy * 2)
            if v == 0 and v2 == 0:
                open_sides.append(label)
        print(f'{room_name[5:]:<38} ({dx:>3},{dy:>3}) door coll {coll_at(c, tx, ty):#04x} '
              f'open: {open_sides or "NONE"}  -> {f[6][5:]}/{f[7][5:]} spawn ({D.num(f[3])},{D.num(f[4])})')
        rows.append((room_name, dx, dy, open_sides, f))
    return rows


def returns(rows):
    """Can each room behind a dead door be left again on foot?

    This is the check that decides whether a position box is a fix or a
    trap. Nothing has ever walked into these rooms - their doors have been
    dead the whole time - so their exits are unexercised, and an interior
    whose own exit is as dead as the door in was would swallow the player.
    """
    import parse_tables as P
    print('\n== the way back out ==')
    seen = set()
    for room_name, dx, dy, sides, f in rows:
        dest_area_name, dest_room_name = f[6], f[7]
        if (dest_area_name, dest_room_name) in seen:
            continue
        seen.add((dest_area_name, dest_room_name))
        area, room = P.AREAS[dest_area_name], P.ROOMS[dest_room_name]
        spawn = (D.num(f[3]), D.num(f[4]))
        outs = [g for g in D.BY_ROOM.get(dest_room_name, []) if g[0] == 'WARP_TYPE_AREA']
        borders = [g for g in D.BY_ROOM.get(dest_room_name, []) if g[0] == 'WARP_TYPE_BORDER']
        if not outs and not borders:
            print(f'{dest_room_name[5:]:<48} NO EXIT ROWS AT ALL')
            continue
        verdicts = []
        for g in outs:
            ex, ey = D.num(g[1]), D.num(g[2])
            fired = None
            for label, ox, oy, key in SIDES:
                for tiles in (2, 3):
                    res = D.walk_in(area, room, ex, ey, key, ox, oy, tiles)
                    if res:
                        fired = f'{key}@{tiles}->{res}'
                        break
                if fired:
                    break
            verdicts.append(f'({ex},{ey})->{g[7][5:]}: ' + (fired or 'DEAD'))
        for g in borders:
            verdicts.append(f'border->{g[7][5:]}: (borders always fire)')
        print(f'{dest_room_name[5:]:<48} spawn {spawn}')
        for v in verdicts:
            print(f'    {v}')


if __name__ == '__main__':
    rows = main()
    if '--returns' in sys.argv:
        returns(rows)
