"""Capture the floor of every room a block puzzle might be built in.

Block puzzles (docs/QUICKSTART_BLOCK_PUZZLES.md) are generated offline per
room, so the generator needs each candidate room's floor as the game sees
it once the mode has set the room up: collision (0 = open) and act tiles
(water, pits, swamp, lava, ladders and the rest), plus where the player
arrives. Booting the emulator per room takes seconds; generating takes
many iterations, so the floors are captured once into build/block_rooms.json
and block_puzzles.py reads that file.

Candidates:
  * every ? room site alone in its room, kinstone-ungated, not a Great
    Fairy - landed through the testbed (scenario SITE, the FAIRY kind:
    nothing solid is placed), which puts the player where the site's own
    arrival puts them;
  * every region pool row, landed at its entrance (probe warps free).

    python3 tools/quickstart/block_rooms.py [--rom tmc-d3.gba] [--only SITE,...]
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import warp, here, press, r16, room_dims, coll_at, act_at, entities, KIND_NPC, PLAYER, ROOM_CONTROLS
import scenario as S
import parse_tables as P
import sim

args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else 'tmc-d3.gba'
OUT = os.path.join(P.ROOT, 'build', 'block_rooms.json')
MSG = 0x02000050


def dismiss(c, limit=600):
    quiet = 0
    for _ in range(limit):
        if c.memory.u8[MSG] == 0:
            c.run_frame(); quiet += 1
            if quiet >= 30:
                return
            continue
        press(c, c.KEY_A, 3, 17); quiet = 0


def capture(c, label, area, room, extra):
    w, h = room_dims(c)
    tw, th = min(w // 16, 64), min(h // 16, 64)
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    px, py = r16(c, PLAYER + 0x2e) - ox, r16(c, PLAYER + 0x32) - oy
    coll = [[coll_at(c, x, y) for x in range(tw)] for y in range(th)]
    act = [[act_at(c, x, y) for x in range(tw)] for y in range(th)]
    npcs = [((e[4] - ox) // 16, (e[5] - oy) // 16) for e in entities(c, KIND_NPC)]
    rec = dict(label=label, area=area, room=room, tw=tw, th=th, player=(px, py),
               coll=coll, act=act, npcs=npcs, landed=list(here(c)))
    rec.update(extra)
    return rec


def sites():
    cnt = collections.Counter((s['area'], s['room']) for s in sim.SITES)
    for i, s in enumerate(sim.SITES):
        if s['gate'] != 0 or cnt[(s['area'], s['room'])] != 1 or s['areaName'] == 'AREA_GREAT_FAIRIES':
            continue
        yield i, s


def main():
    only = set(args[args.index('--only') + 1].split(',')) if '--only' in args else None
    out = {}
    if os.path.exists(OUT):
        out = json.load(open(OUT))
    fairy = S.EVENTS.index('FAIRY')
    for i, s in sites():
        key = 'site:%d' % i
        if only and key not in only:
            continue
        c = S.boot(ROM, S.KINDS['SITE'], i, fairy, 0, kit=2, frames=300)
        dismiss(c)
        for _ in range(60):
            c.run_frame()
        if tuple(here(c)) != (s['area'], s['room']):
            print('%-10s %-46s NOT LANDED (%s)' % (key, s['roomName'], here(c)))
            del c
            continue
        out[key] = capture(c, key, s['areaName'], s['roomName'],
                           dict(site=i, spot=(s['cx'], s['cy']), kinds=s['kinds']))
        print('%-10s %-46s %dx%d' % (key, s['roomName'], out[key]['tw'], out[key]['th']))
        del c
    for row, p in enumerate(sim.POOL):
        key = 'row:%d' % row
        if only and key not in only:
            continue
        c = S.boot(ROM, 0, frames=60)
        c.memory.u8[0x02002a40 + 0x3C] = 0x51   # probe warps are free
        warp(c, p['area'], p['room'], p['entrance'][0], p['entrance'][1], frames=300)
        dismiss(c)
        for _ in range(60):
            c.run_frame()
        if tuple(here(c)) != (p['area'], p['room']):
            print('%-10s %-46s NOT LANDED (%s)' % (key, p['roomName'], here(c)))
            del c
            continue
        out[key] = capture(c, key, p['areaName'], p['roomName'],
                           dict(row=row, entrance=p['entrance'], reward=p['reward'],
                                region=sim.REGION_NAMES[sim.BY_POOL[row]]))
        print('%-10s %-46s %dx%d' % (key, p['roomName'], out[key]['tw'], out[key]['th']))
        del c
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump(out, f)
    print('%d rooms -> %s' % (len(out), OUT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
