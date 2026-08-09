"""Overworld budget probe: entity slots and GFX slots per region, per
difficulty.

Answers "how much room is left for new content" with measured numbers
rather than estimates. MAX_ENTITIES is 72 and MAX_GFX_SLOTS is 44, both
game-wide; the GFX table is the one that actually runs out (see
docs/QUICKSTART_QUEST_RESEARCH.md). Run this after any change to the enemy
rosters, the density spawner, or anything that adds a sprite to a region.

Usage: python3 tools/quickstart/measure_budget.py
"""
import sys, gc
sys.path.insert(0, '/home/user/bartgame/tools/quickstart')
from emu import boot, warp, here, qs_set, GENT, STRIDE, MAX_ENT
import parse_tables as P

RC, GFX, MAX_GFX, DIFF0 = 0x03000bf0, 0x02024490, 44, 174
regions = {r['roomName'][17:]: r for r in P.region_pool()}
targets = [k for k in regions]  # all five region rows


def gfx_used(c):
    return sum(1 for i in range(MAX_GFX)
               if (c.memory.u8[GFX + 4 + i * 12] & 0x0F) not in (0, 1, 2))


def counts(c):
    tot = enemies = 0
    types = set()
    for i in range(MAX_ENT):
        b = GENT + i * STRIDE
        k = c.memory.u8[b + 8]
        if k == 0:
            continue
        tot += 1
        if k == 3:
            enemies += 1
            types.add((c.memory.u8[b + 9], c.memory.u8[b + 0xa]))
    return tot, enemies, len(types)


print(f'{"region":22s} {"diff":>4s} {"ents":>5s} {"enemies":>7s} {"types":>5s} {"gfx":>5s} {"gfxfree":>7s}')
for name in targets:
    r = regions[name]
    for diff in (0, 4, 8, 12):
        gc.collect()
        c = boot()
        for b in range(4):
            qs_set(c, DIFF0 + b, (diff >> b) & 1)
        c.memory.u8[RC + 4] = 0
        warp(c, r['area'], r['room'], r['entrance'][0], r['entrance'][1], 400)
        if here(c) != (r['area'], r['room']):
            print(f'{name} diff {diff}: no land')
            continue
        pe = pen = pty = pg = 0
        for _ in range(900):
            c.run_frame()
            t, e, ty = counts(c)
            pe, pen, pty = max(pe, t), max(pen, e), max(pty, ty)
            pg = max(pg, gfx_used(c))
        print(f'{name:22s} {diff:4d} {pe:5d} {pen:7d} {pty:5d} {pg:5d} {MAX_GFX-pg:7d}')
        del c
