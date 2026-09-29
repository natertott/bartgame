"""Do the fuser faces and the hub wanderers actually vary, and do they render?

Three things this answers that reading the tables cannot:

  1. WHICH face each fuser room draws, and whether an NPC of that id is
     really standing on the spot - a cast entry whose CreateNPC fails, or
     whose Init deletes itself for want of a story flag, would leave the
     room's fusions unreachable and the table would still look right.
  2. Whether the wanderers move and turn between runs. Pinned seeds, so the
     same seed must give the same arrangement and different seeds must not.
  3. That a drawn face RENDERS. An entity that exists but draws nothing is
     the sprite-less-lever failure this project has hit before, so the check
     is the entity's own sprite index, not just its presence.

Usage: python3 tools/quickstart/hub_variety.py [seed ...]
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
SEEDS = [0x11111111, 0x243f6a88, 0x5a5a5a5a, 0xdeadbeef]
# Entity layout (include/entity.h): x is a Q16.16 SplitWord at 0x2c, so its
# integer half is 0x2e - NOT 0x30, which is y's LOW half. Getting that wrong
# writes to a different field entirely and reads back whatever you wrote, so
# it looks self-consistent and is silently meaningless.
ENT_SPRITE_INDEX = 0x12   # s16
ENT_ANIM_STATE = 0x14
HUB_ROOMS = [(48, 0, 'TOWER_ENTRANCE', 120, 264),
             (48, 2, 'TOWER_FLOOR_2', 120, 264),
             (8, 0, 'CLOUD_TOPS', 488, 424)]


def npc_names():
    out = {}
    for line in open(os.path.join(P.ROOT, 'include/npc.h')):
        m = re.match(r'\s*/\*0x([0-9a-f]+)\*/\s*(\w+),', line)
        if m:
            out[int(m.group(1), 16)] = m.group(2)
    return out


NAMES = npc_names()


def npcs(c):
    ox, oy = emu.r16(c, emu.ROOM_CONTROLS + 6), emu.r16(c, emu.ROOM_CONTROLS + 8)
    out = []
    for i in range(emu.MAX_ENT):
        b = emu.GENT + i * emu.STRIDE
        if c.memory.u8[b + emu.ENT_KIND] != emu.KIND_NPC:
            continue
        out.append(dict(id=c.memory.u8[b + emu.ENT_ID],
                        x=emu.r16(c, b + emu.ENT_X) - ox, y=emu.r16(c, b + emu.ENT_Y) - oy,
                        facing=c.memory.u8[b + ENT_ANIM_STATE],
                        sprite=emu.r16(c, b + ENT_SPRITE_INDEX)))
    return out


def main():
    seeds = [int(a, 0) for a in sys.argv[1:]] or SEEDS
    print('=== fuser faces, one room per boot ===')
    rooms = [(sp['areaName'], sp['roomName'], sp['area'], sp['room'])
             for sp in P.fuser_spots()]
    seen_ids, bad = collections.Counter(), []
    for seed in seeds[:1]:
        for an, rn, area, room in rooms:
            r = next((x for x in P.region_pool() if x['area'] == area and x['room'] == room), None)
            if r is None:
                continue
            c = emu.boot(ROM, seed=seed)
            emu.poison_here(c)
            emu.warp(c, area, room, r['entrance'][0], r['entrance'][1])
            if emu.here(c) != (area, room):
                print(f'  {rn[5:]:<38} did not land')
                del c
                continue
            for _ in range(120):
                c.run_frame()
            here = npcs(c)
            del c
            ids = collections.Counter(n['id'] for n in here)
            nosprite = [n for n in here if n['sprite'] == 0]
            for i in ids:
                seen_ids[i] += ids[i]
            if nosprite:
                bad.append((rn, [NAMES.get(n['id'], hex(n['id'])) for n in nosprite]))
            shown = ', '.join(f'{NAMES.get(i, hex(i))}x{n}' for i, n in ids.items()) or 'none'
            print(f'  {rn[5:]:<38} {shown}')
    print('\n  faces seen: ' +
          ', '.join(f'{NAMES.get(i, hex(i))}({n})' for i, n in sorted(seen_ids.items())))
    if bad:
        print('  NPCs WITH NO SPRITE: ' + '; '.join(f'{r}: {v}' for r, v in bad))
    else:
        print('  every NPC placed carries a sprite index')

    print('\n=== hub wanderers, per seed ===')
    face = {0: 'N', 2: 'E', 4: 'S', 6: 'W'}
    arrangements = {}
    for seed in seeds:
        rows = []
        for area, room, label, wx, wy in HUB_ROOMS:
            c = emu.boot(ROM, seed=seed)
            emu.poison_here(c)
            emu.warp(c, area, room, wx, wy)
            if emu.here(c) != (area, room):
                rows.append((label, 'did not land'))
                del c
                continue
            for _ in range(120):
                c.run_frame()
            here = sorted(npcs(c), key=lambda n: (n['x'], n['y']))
            del c
            rows.append((label, ' '.join(f"({n['x']},{n['y']}){face.get(n['facing'], n['facing'])}"
                                         for n in here)))
        arrangements[seed] = rows
        print(f'  seed {seed:#010x}')
        for label, txt in rows:
            print(f'    {label:<16} {txt}')
    distinct = len({tuple(t for _, t in rows) for rows in arrangements.values()})
    print(f'\n  {distinct} distinct arrangement(s) across {len(seeds)} seed(s)')
    return 0 if distinct > 1 and not bad else 1


if __name__ == '__main__':
    sys.exit(main())
