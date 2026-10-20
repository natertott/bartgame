"""Hyrule Castle, the sixteenth region (Oct 2026): is it wired the way the
user asked - "incorporated the same as the overworld regions, with enemy
waves scattered throughout the rooms", "not ... ANY wave clear rewards",
and a few ? rooms?

  ROWS     the castle has its three pool rows (entrance hall, ring hall,
           lower hall), each in the castle's region (QS_REGION_HC, 15) by QuickStartRegionOfRoom.
  WAVES    per row, the REGION scenario deals enemies, killed ones are
           replaced, and the clear pays nothing: the reward state stays 0.
  SWEPT    no vanilla NPC stands in a wave room (the guards).
  WALKS    every crossing, walked with containment live (no probe bypass):
           the garden's north gate into the entrance hall and back, the
           seams entrance hall - ring hall - throne room, the entrance
           hall's and the ring hall's doors down into the lower hall (the
           flag doors the quirk hook opens), the lower hall up into the
           courtyard and back, the lower hall's west border into the cellar,
           the cellar's tunnel up the hedge ladder into the garden, and the
           ladder's way down (asked for directly: it is under bushes).
  REFUSED  the courtyard's north door into the Elemental Sanctuary is
           cancelled: the player stays in the courtyard.
  SITES    the three ? rooms are sites 119-121 (chain_audit.py --sites
           119:122 drives their kinds).

    python3 tools/quickstart/castle_probe.py [--rom tmc-d3.gba]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
from emu import r16, w16, here, entities, KIND_ENEMY, KIND_NPC, GENT, STRIDE, PLAYER, ROOM_CONTROLS
import scenario as S
import parse_tables as P
import callrom as C
from chain_audit import dismiss

ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else os.path.join(P.ROOT, 'tmc-d3.gba')
SAVE = 0x02002a40
HEALTH = SAVE + 0xA8 + 2
HC = P.AREAS['AREA_HYRULE_CASTLE']
CG = (P.AREAS['AREA_CASTLE_GARDEN'], P.ROOMS['ROOM_CASTLE_GARDEN_MAIN'])
SAN = (P.AREAS['AREA_SANCTUARY_ENTRANCE'], P.ROOMS['ROOM_SANCTUARY_ENTRANCE_MAIN'])
CEL = P.AREAS['AREA_HYRULE_CASTLE_CELLAR']
QS_REGION_HC = 15
res = []


def check(name, ok, detail=''):
    res.append(bool(ok))
    print('%s %-52s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)


def local(c):
    return (r16(c, PLAYER + 0x2e) - r16(c, ROOM_CONTROLS + 6), r16(c, PLAYER + 0x32) - r16(c, ROOM_CONTROLS + 8))


def settle(c, n=3):
    for _ in range(n):
        dismiss(c)
        for _ in range(40):
            c.run_frame()


def heal(c):
    c.memory.u8[HEALTH] = 24
    c.memory.u8[PLAYER + 0x45] = 24


def walk(c, key, frames=300):
    """Hold a direction until the room changes; settle; return here()."""
    start = here(c)
    k = getattr(c, 'KEY_' + key)
    c.set_keys(k)
    for _ in range(frames):
        heal(c)
        c.run_frame()
        if here(c) != start:
            break
    c.clear_keys(k)
    for _ in range(150):
        c.run_frame()
    return here(c)


def at(area, room, x, y):
    """A ROOM-scenario boot at a spot: containment is live."""
    c = S.boot(ROM, S.KINDS['ROOM'], a=area, b=room, c=x // 16, d=y // 16, kit=2, frames=300)
    settle(c)
    w16(c, PLAYER + 0x2e, r16(c, ROOM_CONTROLS + 6) + x)
    w16(c, PLAYER + 0x32, r16(c, ROOM_CONTROLS + 8) + y)
    for _ in range(10):
        c.run_frame()
    return c


def main():
    pool = P.region_pool()
    rows = [i for i, p in enumerate(pool) if p['areaName'] == 'AREA_HYRULE_CASTLE']
    check('ROWS: the castle has three pool rows', [pool[i]['roomName'] for i in rows] ==
          ['ROOM_HYRULE_CASTLE_0', 'ROOM_HYRULE_CASTLE_1', 'ROOM_HYRULE_CASTLE_3'], 'rows %s' % rows)
    for row in rows:
        name = pool[row]['roomName'][5:]
        c = S.boot(ROM, S.KINDS['REGION'], row, 0, kit=2, frames=400)
        settle(c)
        ring = C.call_keep(c, C.game_sym('QuickStartRegionOfRoom'), (pool[row]['area'], pool[row]['room']))
        check('ROWS: %s is the castle region (15)' % name, here(c) == (pool[row]['area'], pool[row]['room']) and ring == QS_REGION_HC,
              'here %s region %d' % (here(c), ring))
        npcs = [e for e in entities(c, KIND_NPC) if e[2] != 0x28]
        n0 = len(entities(c, KIND_ENEMY))
        killed = replaced = 0
        for _ in range(8):
            heal(c)
            for e in entities(c, KIND_ENEMY):
                c.memory.u8[GENT + e[0] * STRIDE + 0x45] = 0
                killed += 1
            for _ in range(150):
                c.run_frame()
            dismiss(c)
            replaced = max(replaced, len(entities(c, KIND_ENEMY)))
        reward = C.call_keep(c, C.game_sym('QuickStartGetRegionRewardState'), (row,))
        check('WAVES: %s deals and replaces enemies' % name, n0 > 0 and replaced > 0,
              'first %d, killed %d, next up to %d' % (n0, killed, replaced))
        check('WAVES: %s pays nothing for a clear' % name, reward == 0, 'reward state %d' % reward)
        check('SWEPT: no vanilla NPC in %s' % name, not npcs, 'npcs %s' % [(e[2], e[3]) for e in npcs][:6])

    walks = [
        ('garden gate -> entrance hall', CG, (504, 80), 'UP', (HC, 0)),
        ('entrance hall -> garden', (HC, 0), (216, 520), 'DOWN', CG),
        ('entrance hall -> ring hall (seam)', (HC, 0), (216, 24), 'UP', (HC, 1)),
        ('ring hall -> entrance hall (seam)', (HC, 1), (248, 504), 'DOWN', (HC, 0)),
        ('ring hall -> throne room (seam)', (HC, 1), (248, 24), 'UP', (HC, 2)),
        ('throne room -> ring hall (seam)', (HC, 2), (136, 330), 'DOWN', (HC, 1)),
        ('entrance hall west door -> lower hall', (HC, 0), (72, 232), 'UP', (HC, 3)),
        ('ring hall west door -> lower hall', (HC, 1), (88, 56), 'UP', (HC, 3)),
        ('ring hall east door -> lower hall', (HC, 1), (408, 56), 'UP', (HC, 3)),
        ('lower hall -> entrance hall', (HC, 3), (136, 616), 'DOWN', (HC, 0)),
        ('lower hall -> ring hall', (HC, 3), (104, 40), 'UP', (HC, 1)),
        ('lower hall -> courtyard', (HC, 3), (280, 472), 'UP', SAN),
        ('courtyard -> lower hall', SAN, (136, 400), 'DOWN', (HC, 3)),
        ('lower hall -> cellar button room', (HC, 3), (24, 668), 'LEFT', (CEL, 1)),
        ('cellar button room -> tunnel (seam)', (CEL, 1), (40, 88), 'LEFT', (CEL, 0)),
        ('tunnel ladder -> garden', (CEL, 0), (104, 432), 'UP', CG),
    ]
    for name, room, (x, y), key, want in walks:
        c = at(room[0], room[1], x, y)
        start = here(c)
        got = walk(c, key)
        check('WALKS: %s' % name, start == room and got == want, 'from %s to %s at %s' % (start, got, local(c)))

    # The garden's hedge ladder down is under a 3x3 bush patch in its alcove
    # (vanilla's own price, the sword), which the walk cannot cut its way to;
    # what the mode decides is containment, so the transition is asked for
    # directly, the way a door asks (emu.warp; well_probe's SHUT shows a warp
    # is refused like a door when containment refuses).
    c = at(CG[0], CG[1], 504, 480)
    emu.warp(c, CEL, P.ROOMS['ROOM_HYRULE_CASTLE_CELLAR_0'], 0x68, 0x1a8, frames=300)
    check('WALKS: garden -> cellar tunnel passes containment', here(c) == (CEL, 0), 'here %s at %s' % (here(c), local(c)))

    c = at(SAN[0], SAN[1], 136, 72)
    got = walk(c, 'UP')
    check('REFUSED: the courtyard door to the sanctuary', got == SAN and local(c)[1] < 120,
          'here %s at %s' % (got, local(c)))
    sites = [i for i, s in enumerate(P.content_sites()) if s[0] in ('AREA_HYRULE_CASTLE', 'AREA_SANCTUARY_ENTRANCE',
                                                                     'AREA_HYRULE_CASTLE_CELLAR')]
    check('SITES: the throne room, courtyard and tunnel are sites 119-121', sites == [119, 120, 121], 'sites %s' % sites)
    # The throne room as a ? room: its vanilla cast (the King, the minister,
    # the smith, six guards) is swept like every site's.
    c = S.boot(ROM, S.KINDS['SITE'], 119, S.EVENTS.index('ITEM_DROP'), kit=2, frames=400)
    settle(c)
    npcs = [e for e in entities(c, KIND_NPC) if e[2] != 0x28]
    check('SITES: the throne room is swept of its cast', here(c) == (HC, 2) and not npcs,
          'here %s npcs %s' % (here(c), [(e[2], e[3]) for e in npcs][:6]))
    print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
    return 0 if all(res) else 1


if __name__ == '__main__':
    sys.exit(main())
