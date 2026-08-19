"""Ask the ROM where each overworld key is allowed to drop.

The rule (the user's, and the reason the whole map exists): "the key must
not drop inside the region where it's needed... it could accidentally be
placed somewhere inaccessible, for example as part of a ? room that is
behind the door the key unlocks."

So this drives the real QuickStartKeyRegionAllowed, from inside real rooms,
including ? rooms - which are the case the rule was blind to until
sQuickStartRoomOwners existed. Every case carries its expected answer, and
each one also asks about an ungated item so a room that refuses everything
(a broken lookup) cannot pass as a room that correctly refuses keys.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_tables as P
from callrom import call, game_sym
from emu import boot, warp, here, poison_here

ROM = os.path.join(P.ROOT, 'tmc.gba')


ITEMS = P.ITEMS

# room, area, may the Lon Lon key drop here, may the Graveyard key
CASES = [
    # Ring rooms - the half that already worked, kept as the control.
    ('ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS', 'AREA_HYRULE_FIELD', True, True),
    ('ROOM_HYRULE_FIELD_LON_LON_RANCH', 'AREA_HYRULE_FIELD', False, False),
    ('ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH', 'AREA_HYRULE_FIELD', True, False),
    ('ROOM_ROYAL_VALLEY_MAIN', 'AREA_ROYAL_VALLEY', False, True),
    # ? rooms in an allowed region.
    ('ROOM_CAVES_TRILBY_RUPEE', 'AREA_CAVES', True, True),
    ('ROOM_CAVES_BOOMERANG', 'AREA_CAVES', True, True),
    ('ROOM_HOUSE_INTERIORS_4_FARM_HOUSE', 'AREA_HOUSE_INTERIORS_4', True, False),
    ('ROOM_GREAT_FAIRIES_GRAVEYARD', 'AREA_GREAT_FAIRIES', False, True),
    # ? rooms inside the region the key opens.
    ('ROOM_CAVES_LON_LON_RANCH', 'AREA_CAVES', False, False),
    ('ROOM_GORON_CAVE_MAIN', 'AREA_GORON_CAVE', False, False),
    # ? rooms behind the very door the key opens - the accident itself.
    ('ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_WEST', 'AREA_HOUSE_INTERIORS_4', False, False),
    ('ROOM_ROYAL_VALLEY_GRAVES_GINA', 'AREA_ROYAL_VALLEY_GRAVES', False, False),
    ('ROOM_ROYAL_VALLEY_GRAVES_HEART_PIECE', 'AREA_ROYAL_VALLEY_GRAVES', False, False),
    ('ROOM_HOUSE_INTERIORS_2_DAMPE', 'AREA_HOUSE_INTERIORS_2', False, False),
    # ? rooms in a region neither key may use.
    ('ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_BEDROOM', 'AREA_HOUSE_INTERIORS_2', False, False),
    ('ROOM_DOJOS_GRIMBLADE', 'AREA_DOJOS', False, False),
    # No region owns it: off the ring entirely, so nothing gated may go here.
    ('ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHWEST', 'AREA_MINISH_HOUSE_INTERIORS', False, False),
]


def ask(area, room, addr, item):
    """One boot, one question - the call clobbers the context it hijacks."""
    c = boot(ROM)
    poison_here(c)
    warp(c, area, room, 0x78, 0x78)
    if here(c) != (area, room):
        return None
    return call(c, addr, item)


def main():
    allowed = game_sym('QuickStartKeyRegionAllowed')
    mask = game_sym('QuickStartCurrentRegionMask')
    lonlon, grave = ITEMS['ITEM_QST_LONLON_KEY'], ITEMS['ITEM_QST_GRAVEYARD_KEY']
    ungated = ITEMS['ITEM_HEART_CONTAINER']
    ring = ['CG', 'NHF', 'SHF', 'EH', 'LLR', 'TRIL', 'WW', 'RV']
    bad = 0
    print('QuickStartKeyRegionAllowed @ %#x\n' % allowed)
    print('%-46s %-10s %-14s %-14s %s' % ('room', 'region', 'lon lon', 'graveyard', 'ungated'))
    for room, area_name, want_l, want_g in CASES:
        a, r = P.AREAS[area_name], P.ROOMS[room]
        m = ask(a, r, mask, 0)
        gl = ask(a, r, allowed, lonlon)
        gg = ask(a, r, allowed, grave)
        un = ask(a, r, allowed, ungated)
        if None in (m, gl, gg, un):
            print('%-46s did not land' % room[5:])
            bad += 1
            continue
        gl, gg, un = bool(gl), bool(gg), bool(un)
        names = '+'.join(n for i, n in enumerate(ring) if m & (1 << i)) or '-none-'
        ok = gl == want_l and gg == want_g and un
        bad += not ok
        print('%-46s %-10s %-14s %-14s %-6s%s' % (
            room[5:], names,
            '%s (want %s)' % (gl, want_l), '%s (want %s)' % (gg, want_g), un,
            '' if ok else '   <-- WRONG'))
    print('\n%d wrong out of %d' % (bad, len(CASES)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
