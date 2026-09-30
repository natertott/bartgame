"""Look at each fuser face. Not "does it exist" - does it DRAW correctly.

The user played the cast and reported that two of the faces they met have
"visual/GFX glitches", with Kid and Postman fine. A glitch of that kind is
invisible to hub_variety.py, which checks that a placed NPC carries a
sprite index: a broken face carries one too, it just draws garbage next to
itself. So this probe renders each face and saves a PNG to look at.

HOW A FACE IS FORCED. No patching. QuickStartFuserCastId is
  (((run_seed >> 3) + roomIndex * 5) & 0x7fff) % CAST_COUNT
so for a fixed room a seed can be searched that makes the room draw any
chosen cast slot, and the shipped path then runs unmodified. The player is
parked a few tiles from the fuser's own spot so the NPC is on screen and
near the middle of it.

Usage:
    python3 tools/quickstart/fuser_faces.py [outdir]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
ENT_SPRITE_INDEX = 0x12
ENT_ANIM_STATE = 0x14


def cast():
    """The cast table, read from game.c so this cannot drift from it."""
    src = open(os.path.join(P.ROOT, 'src/game.c')).read()
    i = src.index('static const u8 sQuickStartFuserCast[] = {')
    body = src[i:src.index('};', i)]
    body = body[body.index('{') + 1:]
    return [t.strip() for t in body.replace('\n', ' ').split(',') if t.strip()]


def npc_names():
    out = {}
    for line in open(os.path.join(P.ROOT, 'include/npc.h')):
        m = re.match(r'\s*/\*0x([0-9a-f]+)\*/\s*(\w+),', line)
        if m:
            out[int(m.group(1), 16)] = m.group(2)
    return out


NAMES = npc_names()


def seed_for(slot, room_index, n):
    """A run seed that makes `room_index` draw cast slot `slot`."""
    for s in range(0, 1 << 20):
        seed = 0x10000000 | (s * 8)
        if ((((seed >> 3) + room_index * 5) & 0x7fff) % n) == slot:
            return seed
    raise SystemExit('no seed found for slot %d' % slot)


def npcs(c):
    ox, oy = emu.r16(c, emu.ROOM_CONTROLS + 6), emu.r16(c, emu.ROOM_CONTROLS + 8)
    out = []
    for i in range(emu.MAX_ENT):
        b = emu.GENT + i * emu.STRIDE
        if c.memory.u8[b + emu.ENT_KIND] != emu.KIND_NPC:
            continue
        out.append(dict(id=c.memory.u8[b + emu.ENT_ID],
                        x=emu.r16(c, b + emu.ENT_X) - ox,
                        y=emu.r16(c, b + emu.ENT_Y) - oy,
                        sprite=emu.r16(c, b + ENT_SPRITE_INDEX)))
    return out


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/faces'
    os.makedirs(outdir, exist_ok=True)
    names = cast()
    spots = P.fuser_spots()
    # Eastern Hills North: nine fuser spots close together in a small room,
    # so whichever spot the run picks the NPC is near the player.
    want = ('AREA_HYRULE_FIELD', 'ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH')
    room_index = next(i for i, s in enumerate(spots)
                      if (s['areaName'], s['roomName']) == want)
    spot = spots[room_index]
    print('room %s (fuser row %d), %d spots'
          % (spot['roomName'][5:], room_index, len(spot['spots'])))
    for slot, nm in enumerate(names):
        seed = seed_for(slot, room_index, len(names))
        c = emu.boot(ROM, seed=seed)
        emu.poison_here(c)
        sx, sy = spot['spots'][0]
        emu.warp(c, spot['area'], spot['room'], sx, sy + 40)
        if emu.here(c) != (spot['area'], spot['room']):
            print('  %-14s did not land' % nm)
            del c
            continue
        # The region intro hint holds a textbox over the screen and a
        # snapshot taken through it shows the box, not the face. Ten A
        # presses clear it, the same way region_arrival.py does.
        for _ in range(10):
            emu.press(c, c.KEY_A, 5, 12)
        for _ in range(180):
            c.run_frame()
        # Walk the CAMERA to the face rather than hoping the run placed one
        # near the player: the spot a run picks varies with the seed, and a
        # seed is already spent forcing the cast slot. The player's integer
        # coordinates are moved directly (entity.h: x's integer half is
        # 0x2e and y's is 0x32 - 0x30 and 0x34 are the LOW halves, and
        # writing those moves nothing while reading back what you wrote).
        # Bring the FACE to the camera, not the camera to the face. Moving
        # the player instead clamps the view whenever the fuser's own spot
        # is near a room edge, and three of the eight spots are - which
        # left half the cast un-inspectable on the first pass.
        target_idx = None
        for i in range(emu.MAX_ENT):
            b = emu.GENT + i * emu.STRIDE
            if (c.memory.u8[b + emu.ENT_KIND] == emu.KIND_NPC
                    and NAMES.get(c.memory.u8[b + emu.ENT_ID]) == nm):
                target_idx = b
                break
        if target_idx is not None:
            px = emu.r16(c, emu.PLAYER + 0x2e)
            py = emu.r16(c, emu.PLAYER + 0x32)
            emu.w16(c, target_idx + 0x2e, px)
            emu.w16(c, target_idx + 0x32, py - 34)
            for _ in range(40):
                c.run_frame()

        # Screen position, so the crop lands on the FACE rather than on
        # whatever else happens to be near the player. gRoomControls
        # scroll_x/scroll_y (include/room.h 0x0A/0x0C) is the camera's
        # top-left in world pixels; an entity's world x/y minus that is
        # where it is drawn.
        sx_cam = emu.r16(c, emu.ROOM_CONTROLS + 0x0a)
        sy_cam = emu.r16(c, emu.ROOM_CONTROLS + 0x0c)
        ox = emu.r16(c, emu.ROOM_CONTROLS + 6)
        oy = emu.r16(c, emu.ROOM_CONTROLS + 8)
        here = [n for n in npcs(c) if NAMES.get(n['id']) == nm]
        on = [(n['x'] + ox - sx_cam, n['y'] + oy - sy_cam) for n in here]
        on = [(x, y) for x, y in on if -8 <= x <= 248 and -8 <= y <= 168]
        path = os.path.join(outdir, '%d_%s.png' % (slot, nm))
        emu.snap(c, path)
        del c
        with open(path + '.pos', 'w') as fh:
            fh.write(repr(on))
        if here:
            print('  %-14s seed=%#010x  %d placed, %d on screen at %s, sprite=%d'
                  % (nm, seed, len(here), len(on), on[:3], here[0]['sprite']))
        else:
            print('  %-14s seed=%#010x  NONE PLACED' % (nm, seed))
    return 0


if __name__ == '__main__':
    sys.exit(main())
