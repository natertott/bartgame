"""Can a region host a boss? Engage one there, with the player kept inside.

boss_kill.py answers this for one room but its driver walks the player in a
straight line, and in a region whose arrival component touches a border -
Minish Woods, Lake Hylia - that walks straight out of the room before the
intro finishes. The room then unloads, the family goes with it, and the
result reads "never engaged" for a room that is perfectly capable.

So: same recipe (the intro's first stages wait on the player's action byte,
so the player must MOVE), but the player is put back whenever they drift
toward an edge. Castle Garden is the control - the arena everyone has
watched work in real play - and a region passes when it matches it:
the family composes, the intro finishes, the peel handler runs, and the
whole family dies.

    python3 tools/quickstart/boss_arena.py [ROOM_NAME ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, entities, here, KIND_ENEMY, GENT, STRIDE, r16
import parse_tables as P
import boss_region as B
import boss_kill as K

PLAYER = 0x03001160
RC = 0x03000bf0
ROM = os.path.join(P.ROOT, 'tmc.gba')
DEFAULT = ['ROOM_CASTLE_GARDEN_MAIN', 'ROOM_MINISH_WOODS_MAIN',
           'ROOM_LAKE_HYLIA_MAIN', 'ROOM_MT_CRENEL_ENTRANCE']


def pin(c, margin=72):
    """Keep the player at least `margin` inside the room's own rectangle."""
    ox, oy = r16(c, RC + 6), r16(c, RC + 8)
    w, h = r16(c, RC + 0x1e), r16(c, RC + 0x20)
    px, py = r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32)
    nx = min(max(px, ox + margin), ox + w - margin)
    ny = min(max(py, oy + margin), oy + h - margin)
    if (nx, ny) != (px, py):
        B.w16a(c, PLAYER + 0x2e, nx)
        B.w16a(c, PLAYER + 0x32, ny)


def run(room_name):
    region = next(r for r in P.region_pool() if r['roomName'] == room_name)
    rx, ry = region['reward']
    c = boot(ROM)
    B.enter(c, region)
    if here(c) != (region['area'], region['room']):
        return dict(room=room_name, landed=False)
    if B.spawn_family(c, rx, ry) is None:
        return dict(room=room_name, landed=True, composed=0)
    out = dict(room=room_name, landed=True, composed=len(K.bodies(c)),
               engaged=-1, peels=0, left=-1, stayed=False, pieces0=len(B.pieces(c)))
    start_room = here(c)
    for f in range(2400):
        k = c.KEY_RIGHT if (f // 30) % 2 == 0 else c.KEY_LEFT
        c.set_keys(k)
        B.heal(c)
        c.run_frame()
        c.clear_keys(k)
        pin(c)
        bs = K.bodies(c)
        if bs and c.memory.u8[bs[0] + K.OFF_SUBACTION] != 0:
            out['engaged'] = f
            break
        if not bs:
            out['vanished'] = f
            break
    if out['engaged'] >= 0:
        for _f in range(1200):
            for b in K.bodies(c):
                if c.memory.u8[b + K.OFF_IFRAMES] == 0:
                    c.memory.u8[b + K.OFF_CFLAGS] = K.CONTACT_NOW | K.CONTACT_SRC_SWORD
                if c.memory.u8[b + K.OFF_HITTYPE] == 0:
                    out['peels'] += 1
            B.heal(c)
            c.run_frame()
            pin(c)
        out['left'] = len(K.kill(c))
    out['stayed'] = here(c) == start_room
    del c
    return out


def main():
    rooms = [a for a in sys.argv[1:] if not a.startswith('--')] or DEFAULT
    rows = [run(r) for r in rooms]
    ctl = next((r for r in rows if r['room'] == 'ROOM_CASTLE_GARDEN_MAIN'), None)
    print('%-34s %8s %8s %7s %6s %7s' %
          ('room', 'composed', 'engaged', 'peels', 'left', 'stayed'))
    for r in rows:
        print('%-34s %8s %8s %7s %6s %7s%s' % (
            r['room'], r.get('composed', '-'),
            (r.get('engaged', -1) if r.get('engaged', -1) >= 0
             else 'NEVER' + (' (gone f%d)' % r['vanished'] if 'vanished' in r else '')),
            r.get('peels', '-'), r.get('left', '-'), r.get('stayed'),
            '   <- CONTROL' if r is ctl else ''))
    if ctl and ctl.get('engaged', -1) < 0:
        print('\nThe CONTROL did not engage, so nothing here is evidence about the '
              'other rooms - fix the harness first.')
        return 1
    bad = [r for r in rows if r is not ctl and
           (r.get('engaged', -1) < 0 or r.get('peels', 0) == 0 or r.get('left', 1) != 0)]
    print()
    if bad:
        print('NOT at parity with the control: %s' % ', '.join(r['room'] for r in bad))
    else:
        print('every room matched the control')
    return 0


if __name__ == '__main__':
    sys.exit(main())
