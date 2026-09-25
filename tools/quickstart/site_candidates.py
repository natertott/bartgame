"""Propose new ? room sites in rooms a region owns but does not use yet.

Minish Woods, Lake Hylia and Mount Crenel have far fewer content sites than
the regions they sit next to - four, five and eight against North Hyrule
Field's fourteen - and the rooms to fix that with already exist: every one
of them is a pocket the region owns (tools/quickstart/room_owner.py) that
simply has no row in sQuickStartRoomContentSites.

For each candidate this boots the ROM, lands the player on the room's real
ARRIVAL - the (endX, endY) of the transition row that points into it, which
is where the door actually puts you - floods the walkable grid from there,
and proposes the open tile in that component that is farthest from the
arrival without being off in a corner. Landing ON the content spot makes the
player collect the reward on the spawn frame, which is why distance from the
arrival is the thing being maximised.

It proposes; it does not decide. The invariant checker re-walks whatever
ends up in the table, and its rules (in the entrance component, not on a
solid tile, something actually spawns within 48px) are the real bar.

    python3 tools/quickstart/site_candidates.py [--region MW,LH,CREN]
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_tables as P
import exit_lists as X
from emu import boot, warp, here, room_dims, coll_at, poison_here, r16

ROM = os.path.join(P.ROOT, 'tmc.gba')
PLAYER = 0x03001160
RC = 0x03000bf0

# Rooms each region owns, from room_owner.py's own walk. Imported rather
# than copied so the two cannot drift.
def owned():
    import room_owner as RO
    return RO.walk() if hasattr(RO, 'walk') else None


def arrival_of(room_name):
    """Where the door that leads into this room puts the player.

    A WARP_TYPE_AREA row carries the trigger rectangle in the SOURCE room as
    (startX, startY) and the ARRIVAL in the destination as (endX, endY) -
    which is why Eastern Hills North's farm-house door reads (64,72) ->
    (120,136), the second pair being the spot inside the house. Several
    rooms have more than one door in; the first is as good as any, and the
    flood makes the choice moot as long as they share a component.
    """
    for src, rows in X.BY_ROOM.items():
        for w, sx, sy, ex, ey, shape, da, dr in rows:
            if dr == room_name and w == 'WARP_TYPE_AREA':
                return (ex, ey)
    return None


def flood(c, start_tx, start_ty, tw, th):
    seen = {(start_tx, start_ty)}
    q = collections.deque([(start_tx, start_ty)])
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


def propose(area_name, room_name):
    arr = arrival_of(room_name)
    if arr is None:
        return dict(room=room_name, why='no WARP_TYPE_AREA row points into it')
    c = boot(ROM)
    poison_here(c)
    warp(c, P.AREAS[area_name], P.ROOMS[room_name], arr[0], arr[1])
    if here(c) != (P.AREAS[area_name], P.ROOMS[room_name]):
        del c
        return dict(room=room_name, why='never landed (got %s)' % (here(c),))
    w, h = room_dims(c)
    tw, th = w // 16, h // 16
    px, py = r16(c, PLAYER + 0x2e) - r16(c, RC + 6), r16(c, PLAYER + 0x32) - r16(c, RC + 8)
    stx, sty = px // 16, py // 16
    if not (0 <= stx < tw and 0 <= sty < th) or coll_at(c, stx, sty) != 0:
        del c
        return dict(room=room_name, why='the arrival tile (%d,%d) is not open' % (stx, sty))
    comp = flood(c, stx, sty, tw, th)
    del c
    if len(comp) < 6:
        return dict(room=room_name, why='only %d open tiles from the arrival' % len(comp))
    # Farthest from the arrival, tie-broken toward the middle of the room so
    # a spot never ends up jammed against a wall.
    def score(t):
        d = abs(t[0] - stx) + abs(t[1] - sty)
        edge = min(t[0], tw - 1 - t[0], t[1], th - 1 - t[1])
        return (d, edge)
    best = max(comp, key=score)
    return dict(room=room_name, area=area_name, tiles=len(comp),
                arrival=(px, py), spot=(best[0] * 16 + 8, best[1] * 16 + 8),
                dist=abs(best[0] - stx) + abs(best[1] - sty))


def main():
    rooms = [a for a in sys.argv[1:] if a.startswith('ROOM_')]
    if not rooms:
        print(__doc__)
        return 2
    print('%-46s %6s %5s %12s %12s' % ('room', 'tiles', 'dist', 'arrival', 'spot'))
    for rn in rooms:
        an = X.OWNER.get(rn)
        if an is None:
            print('%-46s  (transitions.c does not own it)' % rn)
            continue
        r = propose(an, rn)
        if 'why' in r:
            print('%-46s  SKIP: %s' % (rn, r['why']))
            continue
        print('%-46s %6d %5d %12s %12s' % (rn, r['tiles'], r['dist'],
                                           r['arrival'], r['spot']))
        print('    { %s, %s, QUICKSTART_KINDS_ANY, %d, %d },'
              % (an, rn, r['spot'][0], r['spot'][1]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
